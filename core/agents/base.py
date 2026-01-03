"""Base class for all agents."""

from abc import ABC, abstractmethod


class AgentBase(ABC):
    """Base class for all agents."""
    
    @property
    @abstractmethod
    def agent_id(self) -> str:
        """Unique identifier for this agent."""
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable name."""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Short description of this agent."""
        pass
    
    @property
    @abstractmethod
    def system_prompt(self) -> str:
        """System prompt defining agent personality."""
        pass
    
    @property
    def model(self) -> str:
        """Default model to use. 'auto' lets router choose."""
        return "auto"
    
    @property
    def max_tokens(self) -> int:
        """Default max tokens for responses."""
        return 200
    
    @property
    def temperature(self) -> float:
        """Default temperature for responses."""
        return 0.9
