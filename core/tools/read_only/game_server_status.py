"""Game server status tool - Docker container status for game servers only."""

import asyncio
import logging
import re
from typing import Any

from ..base import ToolBase, ToolCategory, ToolResult

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


class GameServerStatusTool(ToolBase):
    """Get status of game server containers only.
    
    This is a PUBLIC tool - any Discord user can check game server status.
    Only shows containers that match known game server patterns.
    """
    
    @property
    def name(self) -> str:
        return "game_server_status"
    
    @property
    def description(self) -> str:
        return "Get status of game server containers (Valheim, Minecraft, Rust, 7DTD, etc.)"
    
    @property
    def category(self) -> ToolCategory:
        return ToolCategory.READ_ONLY
    
    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "filter": {
                "type": "string",
                "description": "Optional filter - game server name to filter by (e.g., 'valheim', 'minecraft')",
                "required": False,
            },
        }
    
    async def execute(self, filter: str = None, **kwargs) -> ToolResult:
        try:
            # Get all containers (running and stopped)
            cmd = ["docker", "ps", "-a", "--format", "{{.Names}}\t{{.Status}}\t{{.Image}}"]
            
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()
            
            if proc.returncode != 0:
                return ToolResult(
                    success=False,
                    error=f"Docker command failed: {stderr.decode()}"
                )
            
            lines = stdout.decode().strip().split("\n")
            game_servers = []
            
            for line in lines:
                if not line:
                    continue
                parts = line.split("\t")
                if len(parts) >= 3:
                    name, status, image = parts[0], parts[1], parts[2]
                    
                    # Only include game servers
                    if not is_game_server(name):
                        continue
                    
                    # Apply optional user filter
                    if filter and filter.lower() not in name.lower():
                        continue
                    
                    # Determine friendly status
                    is_running = "Up" in status
                    friendly_status = "online" if is_running else "offline"
                    
                    game_servers.append({
                        "name": name,
                        "status": friendly_status,
                        "details": status,
                        "image": image.split("/")[-1].split(":")[0],
                    })
            
            online = sum(1 for s in game_servers if s["status"] == "online")
            total = len(game_servers)
            
            if total == 0:
                return ToolResult(
                    success=True,
                    data={
                        "online": 0,
                        "total": 0,
                        "servers": [],
                        "summary": "No game servers found" + (f" matching '{filter}'" if filter else ""),
                    },
                )
            
            return ToolResult(
                success=True,
                data={
                    "online": online,
                    "total": total,
                    "servers": game_servers,
                    "summary": f"{online}/{total} game servers online",
                },
            )
            
        except Exception as e:
            logger.error(f"Error getting game server status: {e}")
            return ToolResult(success=False, error=str(e))
