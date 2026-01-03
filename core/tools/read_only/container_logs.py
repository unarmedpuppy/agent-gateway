"""Container logs tool - Tail container logs."""

import asyncio
import logging
from typing import Any

from ..base import ToolBase, ToolCategory, ToolResult

logger = logging.getLogger(__name__)


class ContainerLogsTool(ToolBase):
    
    @property
    def name(self) -> str:
        return "container_logs"
    
    @property
    def description(self) -> str:
        return "Get recent logs from a Docker container"
    
    @property
    def category(self) -> ToolCategory:
        return ToolCategory.READ_ONLY
    
    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "container": {
                "type": "string",
                "description": "Container name to get logs from",
                "required": True,
            },
            "lines": {
                "type": "integer",
                "description": "Number of lines to return (default: 20, max: 100)",
                "required": False,
            },
        }
    
    async def execute(self, container: str = None, lines: int = 20, **kwargs) -> ToolResult:
        if not container:
            return ToolResult(success=False, error="container parameter is required")
        
        lines = min(max(1, lines), 100)
        
        try:
            cmd = ["docker", "logs", "--tail", str(lines), container]
            
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()
            
            if proc.returncode != 0:
                error_msg = stderr.decode()
                if "No such container" in error_msg:
                    return ToolResult(
                        success=False,
                        error=f"Container '{container}' not found"
                    )
                return ToolResult(
                    success=False,
                    error=f"Docker logs failed: {error_msg}"
                )
            
            output = stdout.decode() or stderr.decode()
            log_lines = output.strip().split("\n") if output.strip() else []
            
            return ToolResult(
                success=True,
                data={
                    "container": container,
                    "lines_returned": len(log_lines),
                    "logs": log_lines,
                },
            )
            
        except Exception as e:
            logger.error(f"Error getting container logs: {e}")
            return ToolResult(success=False, error=str(e))
