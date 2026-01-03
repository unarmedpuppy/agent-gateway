"""Service status tool - Docker container status."""

import asyncio
import logging
from typing import Any

from ..base import ToolBase, ToolCategory, ToolResult

logger = logging.getLogger(__name__)


class ServiceStatusTool(ToolBase):
    
    @property
    def name(self) -> str:
        return "service_status"
    
    @property
    def description(self) -> str:
        return "Get status of Docker containers running on the server"
    
    @property
    def category(self) -> ToolCategory:
        return ToolCategory.READ_ONLY
    
    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "filter": {
                "type": "string",
                "description": "Optional filter - container name prefix to filter by",
                "required": False,
            },
        }
    
    async def execute(self, filter: str = None, **kwargs) -> ToolResult:
        try:
            cmd = ["docker", "ps", "--format", "{{.Names}}\t{{.Status}}\t{{.Image}}"]
            
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
            containers = []
            
            for line in lines:
                if not line:
                    continue
                parts = line.split("\t")
                if len(parts) >= 3:
                    name, status, image = parts[0], parts[1], parts[2]
                    if filter and filter.lower() not in name.lower():
                        continue
                    containers.append({
                        "name": name,
                        "status": status,
                        "image": image.split("/")[-1],
                    })
            
            running = sum(1 for c in containers if "Up" in c["status"])
            total = len(containers)
            
            return ToolResult(
                success=True,
                data={
                    "running": running,
                    "total": total,
                    "containers": containers[:20],
                    "summary": f"{running}/{total} containers running",
                },
            )
            
        except Exception as e:
            logger.error(f"Error getting service status: {e}")
            return ToolResult(success=False, error=str(e))
