"""Plex control tool - scan libraries and control Plex."""

import logging
from typing import Any

import httpx

from ..base import ToolBase, ToolCategory, ToolRole, ToolResult
from config import get_settings

logger = logging.getLogger(__name__)


class PlexScanLibraryTool(ToolBase):
    
    @property
    def name(self) -> str:
        return "plex_scan_library"
    
    @property
    def description(self) -> str:
        return "Trigger a Plex library scan"
    
    @property
    def category(self) -> ToolCategory:
        return ToolCategory.MEDIA
    
    @property
    def required_role(self) -> ToolRole:
        return ToolRole.TRUSTED
    
    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "library_name": {
                "type": "string",
                "description": "Name of the library to scan (e.g., 'Movies', 'TV Shows'). Leave empty to scan all.",
                "required": False,
            },
        }
    
    async def execute(self, library_name: str = None, **kwargs) -> ToolResult:
        settings = get_settings()
        
        if not settings.plex_token:
            return ToolResult(
                success=False,
                error="Plex token not configured"
            )
        
        try:
            async with httpx.AsyncClient() as client:
                libraries_response = await client.get(
                    f"{settings.plex_url}/library/sections",
                    params={"X-Plex-Token": settings.plex_token},
                    headers={"Accept": "application/json"},
                    timeout=10,
                )
                
                if libraries_response.status_code != 200:
                    return ToolResult(
                        success=False,
                        error=f"Plex API error: {libraries_response.status_code}"
                    )
                
                data = libraries_response.json()
                directories = data.get("MediaContainer", {}).get("Directory", [])
                
                if library_name:
                    target_libs = [
                        lib for lib in directories 
                        if lib.get("title", "").lower() == library_name.lower()
                    ]
                    if not target_libs:
                        available = [lib.get("title") for lib in directories]
                        return ToolResult(
                            success=False,
                            error=f"Library '{library_name}' not found. Available: {', '.join(available)}"
                        )
                else:
                    target_libs = directories
                
                scanned = []
                for lib in target_libs:
                    lib_key = lib.get("key")
                    lib_title = lib.get("title")
                    
                    scan_response = await client.get(
                        f"{settings.plex_url}/library/sections/{lib_key}/refresh",
                        params={"X-Plex-Token": settings.plex_token},
                        timeout=10,
                    )
                    
                    if scan_response.status_code == 200:
                        scanned.append(lib_title)
                
                return ToolResult(
                    success=True,
                    data={
                        "action": "scan_triggered",
                        "libraries": scanned,
                        "message": f"Scan triggered for: {', '.join(scanned)}",
                    },
                )
                
        except httpx.TimeoutException:
            return ToolResult(success=False, error="Plex request timed out")
        except Exception as e:
            logger.error(f"Error controlling Plex: {e}")
            return ToolResult(success=False, error=str(e))
