"""Restart game server tool - restart game server containers only."""

import asyncio
import logging
from typing import Any

from ..base import ToolBase, ToolCategory, ToolRole, ToolResult

logger = logging.getLogger(__name__)

# Whitelist of game server container name patterns
# These patterns match container names (case-insensitive substring match)
GAME_SERVER_PATTERNS = [
    "valheim",
    "rust",
    "minecraft",
    "7daystodie",
    "7dtd",
    "palworld",
    "satisfactory",
    "terraria",
    "ark",
]


def is_game_server(container_name: str) -> bool:
    """Check if a container name matches a game server pattern."""
    name_lower = container_name.lower()
    return any(pattern in name_lower for pattern in GAME_SERVER_PATTERNS)


class RestartGameServerTool(ToolBase):
    """Restart a game server container.
    
    This is a TRUSTED tool - only whitelisted Discord users can restart game servers.
    Only allows restarting containers that match known game server patterns.
    """
    
    @property
    def name(self) -> str:
        return "restart_game_server"
    
    @property
    def description(self) -> str:
        return "Restart a game server container (Valheim, Minecraft, Rust, 7DTD, etc.)"
    
    @property
    def category(self) -> ToolCategory:
        return ToolCategory.CONTROL
    
    @property
    def required_role(self) -> ToolRole:
        return ToolRole.TRUSTED
    
    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "server_name": {
                "type": "string",
                "description": "Name of the game server to restart (e.g., 'valheim', 'minecraft', 'rust')",
                "required": True,
            },
        }
    
    async def _find_container(self, server_name: str) -> tuple[str | None, str | None]:
        """Find a game server container matching the given name.
        
        Returns (container_name, error_message).
        """
        # Get all containers
        cmd = ["docker", "ps", "-a", "--format", "{{.Names}}"]
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        
        if proc.returncode != 0:
            return None, f"Docker command failed: {stderr.decode()}"
        
        containers = stdout.decode().strip().split("\n")
        server_name_lower = server_name.lower()
        
        # Find matching game server containers
        matches = []
        for container in containers:
            if not container:
                continue
            # Must be a game server AND match the search term
            if is_game_server(container) and server_name_lower in container.lower():
                matches.append(container)
        
        if not matches:
            # Check if it matches a non-game server (for better error message)
            non_game_matches = [c for c in containers if server_name_lower in c.lower()]
            if non_game_matches:
                return None, f"'{server_name}' is not a game server. Only game servers can be restarted with this tool."
            return None, f"No game server found matching '{server_name}'"
        
        if len(matches) > 1:
            return None, f"Multiple game servers match '{server_name}': {', '.join(matches)}. Please be more specific."
        
        return matches[0], None
    
    async def execute(self, server_name: str = None, **kwargs) -> ToolResult:
        if not server_name:
            return ToolResult(success=False, error="server_name is required")
        
        server_name = server_name.strip()
        
        # Find the container
        container_name, error = await self._find_container(server_name)
        if error:
            return ToolResult(success=False, error=error)
        
        try:
            # Restart the container
            proc = await asyncio.create_subprocess_exec(
                "docker", "restart", container_name,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()
            
            if proc.returncode != 0:
                error_msg = stderr.decode().strip()
                return ToolResult(success=False, error=f"Restart failed: {error_msg}")
            
            return ToolResult(
                success=True,
                data={
                    "server": container_name,
                    "action": "restarted",
                    "message": f"Game server '{container_name}' restarted successfully",
                },
            )
            
        except Exception as e:
            logger.error(f"Error restarting game server {container_name}: {e}")
            return ToolResult(success=False, error=str(e))
