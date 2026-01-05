"""
Discord adapter implementation.

Connects to Discord using discord.py, handles message events,
routes to agent-core for AI responses.
"""
from __future__ import annotations

import asyncio
import logging
import random
from typing import Optional

import discord
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
from ...shared.persona import TAYNE_REACTIONS
from ...shared.guardrails import DEFAULT_REQUEST_TIMEOUT
from .config import get_discord_settings

logger = logging.getLogger(__name__)


class DiscordAdapter(BaseAdapter):

    def __init__(self):
        self._settings = get_discord_settings()
        self._client: Optional[discord.Client] = None
        self._connected = False
        self._rate_limiter = RateLimiter(
            config=RateLimitConfig(
                cooldown_seconds=self._settings.cooldown_seconds,
                rapid_fire_threshold=self._settings.rapid_fire_threshold,
                rapid_fire_window=self._settings.rapid_fire_window,
            )
        )

    @property
    def platform(self) -> str:
        return "discord"

    async def connect(self) -> None:
        if not self._settings.discord_token:
            logger.warning("Discord token not configured, adapter disabled")
            return

        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True
        intents.guild_messages = True
        self._client = discord.Client(intents=intents)

        @self._client.event
        async def on_ready():
            logger.info(f"Discord connected as {self._client.user}")
            self._connected = True

        @self._client.event
        async def on_message(message: discord.Message):
            await self._handle_message(message)

        asyncio.create_task(self._client.start(self._settings.discord_token))
        logger.info("Discord adapter starting...")

    async def disconnect(self) -> None:
        if self._client:
            await self._client.close()
            self._connected = False
            logger.info("Discord adapter disconnected")

    async def send_message(self, msg: OutboundMessage) -> bool:
        if not self._client or not self._connected:
            logger.error("Discord client not connected")
            return False

        try:
            channel = self._client.get_channel(int(msg.channel))
            if not channel:
                channel = await self._client.fetch_channel(int(msg.channel))

            if channel:
                await channel.send(msg.message)
                return True
            else:
                logger.error(f"Channel {msg.channel} not found")
                return False
        except Exception as e:
            logger.error(f"Error sending Discord message: {e}")
            return False

    async def add_reaction(self, channel: str, message_id: str, emoji: str) -> bool:
        if not self._client or not self._connected:
            return False

        try:
            ch = self._client.get_channel(int(channel))
            if not ch:
                ch = await self._client.fetch_channel(int(channel))
            
            msg = await ch.fetch_message(int(message_id))
            await msg.add_reaction(emoji)
            return True
        except Exception as e:
            logger.error(f"Error adding reaction: {e}")
            return False

    def is_healthy(self) -> bool:
        return self._connected

    def get_configured_bots(self) -> list[str]:
        if self._settings.discord_token:
            return ["tayne"]
        return []

    async def _handle_message(self, message: discord.Message) -> None:
        if message.author == self._client.user:
            return

        is_mentioned = self._client.user in message.mentions
        is_text_mention = "@tayne" in message.content.lower()

        if is_mentioned or is_text_mention:
            await self._handle_mention(message)
            return

        if random.random() < self._settings.reaction_chance:
            await self._add_random_reaction(message)

    async def _handle_mention(self, message: discord.Message) -> None:
        is_limited, is_rapid_fire = self._rate_limiter.check(str(message.author.id))

        if is_limited:
            response = random.choice(RATE_LIMITED_RESPONSES)
            if is_rapid_fire:
                response = random.choice(FALLBACK_QUOTES)
            try:
                await message.channel.send(response)
            except discord.errors.Forbidden:
                logger.warning(f"Cannot send to {message.channel}")
            return

        async with message.channel.typing():
            response = await self._query_tayne(message)

        if response:
            try:
                await message.channel.send(response)
            except discord.errors.Forbidden:
                logger.warning(f"Cannot send to {message.channel}")
        else:
            try:
                await message.channel.send(API_DOWN_MESSAGE)
            except discord.errors.Forbidden:
                pass

    async def _query_tayne(self, message: discord.Message) -> Optional[str]:
        user_message = self._clean_message(message.content, message.mentions)
        if not user_message:
            user_message = "Hello Tayne!"

        history = await self._fetch_history(message.channel)

        response = await self._query_agent_core(message, user_message, history)
        if response:
            logger.info("Response from agent-core")
            return response

        logger.info("Agent-core unavailable, falling back to direct LLM")
        return await self._query_llm_direct(message, user_message, history)

    async def _query_agent_core(
        self,
        message: discord.Message,
        user_message: str,
        history: list[dict],
    ) -> Optional[str]:
        payload = {
            "message": user_message,
            "user": {
                "platform": "discord",
                "platform_user_id": str(message.author.id),
                "display_name": message.author.display_name,
            },
            "conversation_id": f"discord-{message.channel.id}",
            "context": {
                "channel_name": getattr(message.channel, "name", "dm"),
                "history": history[:-1] if len(history) > 1 else [],
            },
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
        message: discord.Message,
        user_message: str,
        history: list[dict],
    ) -> Optional[str]:
        api_messages = [{"role": "system", "content": TAYNE_SYSTEM_PROMPT}]
        if len(history) > 1:
            api_messages.extend(history[:-1])
        api_messages.append({
            "role": "user",
            "content": f"{message.author.display_name}: {user_message}",
        })

        payload = {
            "model": "auto",
            "messages": api_messages,
            "max_tokens": 200,
            "temperature": 0.9,
        }

        headers = {
            "Content-Type": "application/json",
            "X-Enable-Memory": "true",
            "X-Conversation-ID": f"discord-{message.channel.id}",
            "X-Project": "tayne-discord",
            "X-User-ID": str(message.author.id),
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

    async def _fetch_history(self, channel, limit: int = 5) -> list[dict]:
        messages = []
        try:
            async for msg in channel.history(limit=limit):
                if not msg.content:
                    continue
                content = self._clean_message(msg.content, msg.mentions)
                if not content:
                    continue

                if msg.author == self._client.user:
                    role = "assistant"
                else:
                    role = "user"
                    content = f"{msg.author.display_name}: {content}"

                messages.append({"role": role, "content": content})
        except Exception as e:
            logger.warning(f"Error fetching history: {e}")

        messages.reverse()
        return messages

    def _clean_message(self, content: str, mentions: list) -> str:
        for mention in mentions:
            content = content.replace(f"<@{mention.id}>", "")
            content = content.replace(f"<@!{mention.id}>", "")
        return content.strip()

    async def _add_random_reaction(self, message: discord.Message) -> None:
        emoji = random.choice(TAYNE_REACTIONS)
        try:
            await message.add_reaction(emoji)
        except Exception as e:
            logger.debug(f"Could not add reaction: {e}")
