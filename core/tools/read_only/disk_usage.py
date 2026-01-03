"""Disk usage tool - System disk usage."""

import asyncio
import logging
from typing import Any

from ..base import ToolBase, ToolCategory, ToolResult

logger = logging.getLogger(__name__)


class DiskUsageTool(ToolBase):
    
    @property
    def name(self) -> str:
        return "disk_usage"
    
    @property
    def description(self) -> str:
        return "Get disk usage information for the server"
    
    @property
    def category(self) -> ToolCategory:
        return ToolCategory.READ_ONLY
    
    async def execute(self, **kwargs) -> ToolResult:
        try:
            cmd = ["df", "-h", "--output=target,size,used,avail,pcent"]
            
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()
            
            if proc.returncode != 0:
                return ToolResult(
                    success=False,
                    error=f"df command failed: {stderr.decode()}"
                )
            
            lines = stdout.decode().strip().split("\n")
            disks = []
            
            important_mounts = ["/", "/mnt", "/jenquist-cloud", "/home"]
            
            for line in lines[1:]:
                parts = line.split()
                if len(parts) >= 5:
                    mount = parts[0]
                    if not any(mount.startswith(m) for m in important_mounts):
                        if mount not in ["/", "/home"]:
                            continue
                    
                    size, used, avail, percent = parts[1], parts[2], parts[3], parts[4]
                    disks.append({
                        "mount": mount,
                        "size": size,
                        "used": used,
                        "available": avail,
                        "percent": percent,
                    })
            
            critical = [d for d in disks if int(d["percent"].rstrip("%")) > 90]
            warning = [d for d in disks if 80 <= int(d["percent"].rstrip("%")) <= 90]
            
            status = "OK"
            if critical:
                status = "CRITICAL"
            elif warning:
                status = "WARNING"
            
            return ToolResult(
                success=True,
                data={
                    "status": status,
                    "disks": disks,
                    "critical": [d["mount"] for d in critical],
                    "warning": [d["mount"] for d in warning],
                },
            )
            
        except Exception as e:
            logger.error(f"Error getting disk usage: {e}")
            return ToolResult(success=False, error=str(e))
