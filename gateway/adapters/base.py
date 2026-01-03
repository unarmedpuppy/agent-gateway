"""
Base adapter interface for platform adapters.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from pydantic import BaseModel


class InboundMessage(BaseModel):
    platform: str
    user_id: str
    user_display_name: str
    channel_id: str
    channel_name: Optional[str] = None
    message: str
    thread_id: Optional[str] = None
    raw: dict = {}


class OutboundMessage(BaseModel):
    platform: str
    bot: str
    channel: str
    message: str
    thread_id: Optional[str] = None
    metadata: dict = {}


class BaseAdapter(ABC):

    @property
    @abstractmethod
    def platform(self) -> str:
        pass

    @abstractmethod
    async def connect(self) -> None:
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        pass

    @abstractmethod
    async def send_message(self, msg: OutboundMessage) -> bool:
        pass

    @abstractmethod
    async def add_reaction(self, channel: str, message_id: str, emoji: str) -> bool:
        pass

    @abstractmethod
    def is_healthy(self) -> bool:
        pass

    @abstractmethod
    def get_configured_bots(self) -> list[str]:
        pass


class AdapterRegistry:
    _adapters: dict[str, BaseAdapter] = {}

    @classmethod
    def register(cls, adapter: BaseAdapter) -> None:
        cls._adapters[adapter.platform] = adapter

    @classmethod
    def get(cls, platform: str) -> Optional[BaseAdapter]:
        return cls._adapters.get(platform)

    @classmethod
    def all(cls) -> dict[str, BaseAdapter]:
        return cls._adapters.copy()

    @classmethod
    async def connect_all(cls) -> None:
        for adapter in cls._adapters.values():
            await adapter.connect()

    @classmethod
    async def disconnect_all(cls) -> None:
        for adapter in cls._adapters.values():
            await adapter.disconnect()
