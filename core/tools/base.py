"""Tool base class and types."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any


class ToolCategory(str, Enum):
    READ_ONLY = "read_only"
    CONTROL = "control"
    MEDIA = "media"
    LIFE_OS = "life_os"


class ToolRole(str, Enum):
    PUBLIC = "public"
    TRUSTED = "trusted"
    ADMIN = "admin"


@dataclass
class ToolResult:
    success: bool
    data: Any = None
    error: str | None = None


class ToolBase(ABC):
    
    @property
    @abstractmethod
    def name(self) -> str:
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        pass
    
    @property
    @abstractmethod
    def category(self) -> ToolCategory:
        pass
    
    @property
    def required_role(self) -> ToolRole:
        return ToolRole.PUBLIC
    
    @property
    def parameters(self) -> dict[str, Any]:
        return {}
    
    @abstractmethod
    async def execute(self, **kwargs) -> ToolResult:
        pass
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "category": self.category.value,
            "required_role": self.required_role.value,
            "parameters": self.parameters,
        }
    
    def to_openai_function(self) -> dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": self.parameters,
                    "required": [k for k, v in self.parameters.items() if v.get("required", False)],
                },
            },
        }
