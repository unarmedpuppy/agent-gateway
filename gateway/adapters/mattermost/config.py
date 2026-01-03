"""
Mattermost adapter configuration.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings


@dataclass
class BotConfig:
    name: str
    token_env: str
    default_channel: str = "town-square"

    @property
    def token(self) -> str | None:
        return os.getenv(self.token_env)

    def is_configured(self) -> bool:
        return self.token is not None


BOT_REGISTRY: dict[str, BotConfig] = {
    "tayne": BotConfig(
        name="tayne",
        token_env="MATTERMOST_BOT_TAYNE_TOKEN",
        default_channel="general",
    ),
    "server-monitor": BotConfig(
        name="server-monitor",
        token_env="MATTERMOST_BOT_MONITOR_TOKEN",
        default_channel="alerts",
    ),
    "trading-bot": BotConfig(
        name="trading-bot",
        token_env="MATTERMOST_BOT_TRADING_TOKEN",
        default_channel="trading",
    ),
}


class MattermostSettings(BaseSettings):
    mattermost_url: str = Field(default="mattermost.server.unarmedpuppy.com")
    mattermost_scheme: str = Field(default="https")
    mattermost_port: int = Field(default=443)

    agent_core_url: str = Field(default="http://agent-core:8000")
    local_ai_url: str = Field(default="http://llm-router:8000")
    local_ai_api_key: str = Field(default="")
    tayne_webhook_token: str = Field(default="")

    channel_cache_ttl: int = Field(default=300)

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


@lru_cache
def get_mattermost_settings() -> MattermostSettings:
    return MattermostSettings()


def get_bot(name: str) -> BotConfig | None:
    return BOT_REGISTRY.get(name)


def get_configured_bots() -> list[str]:
    return [name for name, bot in BOT_REGISTRY.items() if bot.is_configured()]
