"""
Discord adapter configuration.
"""
from __future__ import annotations

import os
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings


class DiscordSettings(BaseSettings):
    discord_token: str = Field(default="")
    agent_core_url: str = Field(default="http://agent-core:8000")
    local_ai_url: str = Field(default="http://llm-router:8000")
    local_ai_api_key: str = Field(default="")
    
    cooldown_seconds: float = Field(default=5.0)
    reaction_chance: float = Field(default=0.33)
    rapid_fire_threshold: int = Field(default=5)
    rapid_fire_window: int = Field(default=60)

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


@lru_cache
def get_discord_settings() -> DiscordSettings:
    return DiscordSettings()
