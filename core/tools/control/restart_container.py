"""Restart container tool - restart Docker containers."""

import asyncio
import logging
from typing import Any

from ..base import ToolBase, ToolCategory, ToolRole, ToolResult

logger = logging.getLogger(__name__)


class RestartContainerTool(ToolBase):
    
    @property
    def name(self) -> str:
        return "restart_container"
    
    @property
    def description(self) -> str:
        return "Restart a Docker container by name"
    
    @property
    def category(self) -> ToolCategory:
        return ToolCategory.CONTROL
    
    @property
    def required_role(self) -> ToolRole:
        return ToolRole.TRUSTED
    
    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "container_name": {
                "type": "string",
                "description": "Name of the container to restart (e.g., 'jellyfin', 'sonarr')",
                "required": True,
            },
        }
    
    async def execute(self, container_name: str = None, **kwargs) -> ToolResult:
        if not container_name:
            return ToolResult(success=False, error="container_name is required")
        
        container_name = container_name.strip().lower()
        if not container_name.replace("-", "").replace("_", "").isalnum():
            return ToolResult(
                success=False,
                error="Invalid container name - only alphanumeric, hyphens, underscores allowed"
            )
        
        try:
            proc = await asyncio.create_subprocess_exec(
                "docker", "restart", container_name,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()
            
            if proc.returncode != 0:
                error_msg = stderr.decode().strip()
                if "No such container" in error_msg:
                    return ToolResult(
                        success=False,
                        error=f"Container '{container_name}' not found"
                    )
                return ToolResult(success=False, error=f"Restart failed: {error_msg}")
            
            return ToolResult(
                success=True,
                data={
                    "container": container_name,
                    "action": "restarted",
                    "message": f"Container '{container_name}' restarted successfully",
                },
            )
            
        except Exception as e:
            logger.error(f"Error restarting container {container_name}: {e}")
            return ToolResult(success=False, error=str(e))
