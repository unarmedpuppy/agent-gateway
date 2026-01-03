"""
Mattermost adapter implementation.

Provides HTTP API for sending messages and handles webhooks from Mattermost.
"""
from __future__ import annotations

import logging
import random
from typing import Optional

import httpx

from ..base import BaseAdapter, OutboundMessage
from ...shared import (
    RateLimiter,
    RateLimitConfig,
    TAYNE_SYSTEM_PROMPT,
    FALLBACK_QUOTES,
    API_DOWN_MESSAGE,
    RATE_LIMITED_RESPONSES,
    needs_fallback,
)
from ...shared.guardrails import DEFAULT_REQUEST_TIMEOUT
from .config import get_mattermost_settings, get_bot, get_configured_bots, BotConfig
from .client import MattermostClient, MattermostClientError, get_client

logger = logging.getLogger(__name__)


class MattermostAdapter(BaseAdapter):

    def __init__(self):
        self._settings = get_mattermost_settings()
        self._healthy = False
        self._rate_limiter = RateLimiter(config=RateLimitConfig())

    @property
    def platform(self) -> str:
        return "mattermost"

    async def connect(self) -> None:
        configured = get_configured_bots()
        if not configured:
            logger.warning("No Mattermost bots configured")
            return

        for bot_name in configured:
            bot_config = get_bot(bot_name)
            if bot_config:
                try:
                    client = get_client(bot_config)
                    user = client.get_me()
                    logger.info(f"Mattermost bot '{bot_name}' connected as {user.get('username')}")
                except Exception as e:
                    logger.error(f"Failed to connect bot '{bot_name}': {e}")

        self._healthy = len(configured) > 0
        logger.info(f"Mattermost adapter ready with {len(configured)} bot(s)")

    async def disconnect(self) -> None:
        self._healthy = False
        logger.info("Mattermost adapter disconnected")

    async def send_message(self, msg: OutboundMessage) -> bool:
        bot_config = get_bot(msg.bot)
        if not bot_config or not bot_config.is_configured():
            logger.error(f"Bot '{msg.bot}' not configured")
            return False

        try:
            client = get_client(bot_config)
            client.post_message(
                channel=msg.channel,
                message=msg.message,
                thread_id=msg.thread_id,
            )
            return True
        except MattermostClientError as e:
            logger.error(f"Failed to send message: {e}")
            return False

    async def add_reaction(self, channel: str, message_id: str, emoji: str) -> bool:
        tayne_config = get_bot("tayne")
        if not tayne_config or not tayne_config.is_configured():
            return False

        try:
            client = get_client(tayne_config)
            user = client.get_me()
            return client.add_reaction(message_id, emoji, user["id"])
        except Exception as e:
            logger.error(f"Failed to add reaction: {e}")
            return False

    def is_healthy(self) -> bool:
        return self._healthy

    def get_configured_bots(self) -> list[str]:
        return get_configured_bots()

    async def handle_tayne_webhook(
        self,
        user_id: str,
        user_name: str,
        channel_id: str,
        text: str,
        post_id: str,
        trigger_word: str = "@tayne",
    ) -> Optional[str]:
        is_limited, is_rapid_fire = self._rate_limiter.check(user_id)

        if is_limited:
            response = random.choice(RATE_LIMITED_RESPONSES)
            if is_rapid_fire:
                response = random.choice(FALLBACK_QUOTES)
            return response

        cleaned_message = self._clean_message(text, trigger_word)

        response = await self._query_tayne(
            message=cleaned_message,
            user_name=user_name,
            channel_id=channel_id,
            user_id=user_id,
        )

        tayne_config = get_bot("tayne")
        if tayne_config and tayne_config.is_configured():
            try:
                client = get_client(tayne_config)
                response_text = response if response else API_DOWN_MESSAGE
                client.post_message(
                    channel=channel_id,
                    message=response_text,
                    thread_id=post_id,
                )
                return None
            except MattermostClientError as e:
                logger.error(f"Failed to post as Tayne: {e}")

        return response if response else API_DOWN_MESSAGE

    async def _query_tayne(
        self,
        message: str,
        user_name: str,
        channel_id: str,
        user_id: str,
    ) -> Optional[str]:
        response = await self._query_agent_core(message, user_name, channel_id, user_id)
        if response:
            logger.info("Response from agent-core")
            return response

        logger.info("Agent-core unavailable, falling back to direct LLM")
        return await self._query_llm_direct(message, user_name, channel_id, user_id)

    async def _query_agent_core(
        self,
        message: str,
        user_name: str,
        channel_id: str,
        user_id: str,
    ) -> Optional[str]:
        payload = {
            "message": message,
            "user": {
                "platform": "mattermost",
                "platform_user_id": user_id,
                "display_name": user_name,
            },
            "conversation_id": f"mattermost-{channel_id}",
            "context": {"channel_id": channel_id},
        }

        try:
            async with httpx.AsyncClient(timeout=DEFAULT_REQUEST_TIMEOUT) as client:
                resp = await client.post(
                    f"{self._settings.agent_core_url}/v1/agent/tayne/chat",
                    json=payload,
                )
                if resp.status_code == 200:
                    return resp.json().get("response")
                logger.warning(f"Agent-core returned {resp.status_code}")
                return None
        except Exception as e:
            logger.warning(f"Agent-core error: {e}")
            return None

    async def _query_llm_direct(
        self,
        message: str,
        user_name: str,
        channel_id: str,
        user_id: str,
    ) -> Optional[str]:
        api_messages = [
            {"role": "system", "content": TAYNE_SYSTEM_PROMPT},
            {"role": "user", "content": f"{user_name}: {message}"},
        ]

        payload = {
            "model": "auto",
            "messages": api_messages,
            "max_tokens": 200,
            "temperature": 0.9,
        }

        headers = {
            "Content-Type": "application/json",
            "X-Enable-Memory": "true",
            "X-Conversation-ID": f"mattermost-{channel_id}",
            "X-Project": "tayne-mattermost",
            "X-User-ID": user_id,
        }

        if self._settings.local_ai_api_key:
            headers["Authorization"] = f"Bearer {self._settings.local_ai_api_key}"

        try:
            async with httpx.AsyncClient(timeout=DEFAULT_REQUEST_TIMEOUT) as client:
                resp = await client.post(
                    f"{self._settings.local_ai_url}/v1/chat/completions",
                    json=payload,
                    headers=headers,
                )
                if resp.status_code == 200:
                    data = resp.json()
                    response_text = data["choices"][0]["message"]["content"]
                    if needs_fallback(response_text):
                        logger.info("Guardrail triggered, using fallback")
                        return random.choice(FALLBACK_QUOTES)
                    return response_text
                logger.error(f"LLM returned {resp.status_code}")
                return None
        except Exception as e:
            logger.error(f"LLM error: {e}")
            return None

    def _clean_message(self, text: str, trigger_word: str) -> str:
        import re
        cleaned = re.sub(re.escape(trigger_word), "", text, flags=re.IGNORECASE).strip()
        return cleaned if cleaned else "Hello Tayne!"
