"""
Agent Registry

Discovers and manages agent instances. Each agent has a unique ID,
persona configuration, and default settings.
"""

from typing import Optional

from .base import AgentBase
from .tayne import TayneAgent


# Registry of available agents
_AGENTS: dict[str, AgentBase] = {}


def _register_agents():
    """Register all available agents."""
    global _AGENTS
    
    agents = [
        TayneAgent(),
    ]
    
    for agent in agents:
        _AGENTS[agent.agent_id] = agent


def get_agent(agent_id: str) -> Optional[AgentBase]:
    """Get an agent by ID."""
    if not _AGENTS:
        _register_agents()
    return _AGENTS.get(agent_id)


def list_agents() -> list[dict]:
    """List all available agents."""
    if not _AGENTS:
        _register_agents()
    
    return [
        {
            "id": agent.agent_id,
            "name": agent.name,
            "description": agent.description,
        }
        for agent in _AGENTS.values()
    ]
