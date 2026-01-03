"""
Mattermost API client wrapper.
"""
from __future__ import annotations

import logging
import time
from functools import lru_cache
from typing import Any, Optional

import httpx

from .config import BotConfig, get_mattermost_settings

logger = logging.getLogger(__name__)


class MattermostClientError(Exception):
    pass


class MattermostClient:

    def __init__(self, bot_config: BotConfig):
        self.bot_config = bot_config
        self._settings = get_mattermost_settings()
        self._channel_cache: dict[str, tuple[str, float]] = {}

    @property
    def base_url(self) -> str:
        scheme = self._settings.mattermost_scheme
        host = self._settings.mattermost_url
        port = self._settings.mattermost_port
        if (scheme == "https" and port == 443) or (scheme == "http" and port == 80):
            return f"{scheme}://{host}"
        return f"{scheme}://{host}:{port}"

    @property
    def headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.bot_config.token}",
            "Content-Type": "application/json",
        }

    def _get_channel_id(self, channel: str) -> str:
        if channel.startswith("channel:"):
            return channel[8:]

        now = time.time()
        if channel in self._channel_cache:
            cached_id, cached_time = self._channel_cache[channel]
            if now - cached_time < self._settings.channel_cache_ttl:
                return cached_id

        try:
            with httpx.Client(timeout=10) as client:
                resp = client.get(
                    f"{self.base_url}/api/v4/channels/name/team/{channel}",
                    headers=self.headers,
                )
                if resp.status_code == 200:
                    channel_id = resp.json()["id"]
                    self._channel_cache[channel] = (channel_id, now)
                    return channel_id
        except Exception as e:
            logger.warning(f"Could not resolve channel {channel}: {e}")

        return channel

    def post_message(
        self,
        channel: str,
        message: str,
        thread_id: Optional[str] = None,
    ) -> dict[str, Any]:
        channel_id = self._get_channel_id(channel)
        
        payload = {
            "channel_id": channel_id,
            "message": message,
        }
        if thread_id:
            payload["root_id"] = thread_id

        try:
            with httpx.Client(timeout=10) as client:
                resp = client.post(
                    f"{self.base_url}/api/v4/posts",
                    headers=self.headers,
                    json=payload,
                )
                if resp.status_code in (200, 201):
                    return resp.json()
                raise MattermostClientError(f"Failed to post: {resp.status_code}")
        except httpx.RequestError as e:
            raise MattermostClientError(f"Request error: {e}") from e

    def add_reaction(self, post_id: str, emoji: str, user_id: str) -> bool:
        payload = {
            "user_id": user_id,
            "post_id": post_id,
            "emoji_name": emoji,
        }

        try:
            with httpx.Client(timeout=10) as client:
                resp = client.post(
                    f"{self.base_url}/api/v4/reactions",
                    headers=self.headers,
                    json=payload,
                )
                return resp.status_code in (200, 201)
        except Exception as e:
            logger.error(f"Failed to add reaction: {e}")
            return False

    def get_me(self) -> dict[str, Any]:
        try:
            with httpx.Client(timeout=10) as client:
                resp = client.get(
                    f"{self.base_url}/api/v4/users/me",
                    headers=self.headers,
                )
                if resp.status_code == 200:
                    return resp.json()
                raise MattermostClientError(f"Failed to get user: {resp.status_code}")
        except httpx.RequestError as e:
            raise MattermostClientError(f"Request error: {e}") from e


_client_cache: dict[str, MattermostClient] = {}


def get_client(bot_config: BotConfig) -> MattermostClient:
    if bot_config.name not in _client_cache:
        _client_cache[bot_config.name] = MattermostClient(bot_config)
    return _client_cache[bot_config.name]
