"""Trigger backup tool - run B2 backup script."""

import asyncio
import logging
from typing import Any

from ..base import ToolBase, ToolCategory, ToolRole, ToolResult

logger = logging.getLogger(__name__)

BACKUP_SCRIPT = "/server/scripts/backup-to-b2.sh"


class TriggerBackupTool(ToolBase):
    
    @property
    def name(self) -> str:
        return "trigger_backup"
    
    @property
    def description(self) -> str:
        return "Trigger a backup to Backblaze B2 cloud storage"
    
    @property
    def category(self) -> ToolCategory:
        return ToolCategory.CONTROL
    
    @property
    def required_role(self) -> ToolRole:
        return ToolRole.ADMIN
    
    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "dry_run": {
                "type": "boolean",
                "description": "If true, only show what would be backed up without actually doing it",
                "required": False,
            },
        }
    
    async def execute(self, dry_run: bool = False, **kwargs) -> ToolResult:
        try:
            cmd = ["bash", BACKUP_SCRIPT]
            if dry_run:
                cmd.append("--dry-run")
            
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(),
                timeout=300,
            )
            
            if proc.returncode != 0:
                return ToolResult(
                    success=False,
                    error=f"Backup failed: {stderr.decode()}"
                )
            
            output = stdout.decode()
            
            transferred = "unknown"
            for line in output.split("\n"):
                if "Transferred:" in line:
                    transferred = line.strip()
                    break
            
            return ToolResult(
                success=True,
                data={
                    "action": "dry_run" if dry_run else "backup_started",
                    "transferred": transferred,
                    "message": f"Backup {'dry run' if dry_run else 'completed'} successfully",
                },
            )
            
        except asyncio.TimeoutError:
            return ToolResult(
                success=False,
                error="Backup timed out after 5 minutes"
            )
        except Exception as e:
            logger.error(f"Error triggering backup: {e}")
            return ToolResult(success=False, error=str(e))
