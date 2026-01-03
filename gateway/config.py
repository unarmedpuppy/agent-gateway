"""
Gateway configuration.
"""
from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings


class GatewaySettings(BaseSettings):
    gateway_port: int = Field(default=8000)
    gateway_log_level: str = Field(default="INFO")

    agent_core_url: str = Field(default="http://agent-core:8000")
    local_ai_url: str = Field(default="http://llm-router:8000")
    local_ai_api_key: str = Field(default="")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


@lru_cache
def get_settings() -> GatewaySettings:
    return GatewaySettings()
