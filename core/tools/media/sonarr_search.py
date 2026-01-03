"""Sonarr search tool - search and add TV shows."""

import logging
from typing import Any

import httpx

from ..base import ToolBase, ToolCategory, ToolRole, ToolResult
from config import get_settings

logger = logging.getLogger(__name__)


class SonarrSearchTool(ToolBase):
    
    @property
    def name(self) -> str:
        return "sonarr_search"
    
    @property
    def description(self) -> str:
        return "Search for TV shows in Sonarr"
    
    @property
    def category(self) -> ToolCategory:
        return ToolCategory.MEDIA
    
    @property
    def required_role(self) -> ToolRole:
        return ToolRole.TRUSTED
    
    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "query": {
                "type": "string",
                "description": "TV show name to search for",
                "required": True,
            },
        }
    
    async def execute(self, query: str = None, **kwargs) -> ToolResult:
        if not query:
            return ToolResult(success=False, error="query is required")
        
        settings = get_settings()
        
        if not settings.sonarr_api_key:
            return ToolResult(
                success=False,
                error="Sonarr API key not configured"
            )
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{settings.sonarr_url}/api/v3/series/lookup",
                    params={"term": query},
                    headers={"X-Api-Key": settings.sonarr_api_key},
                    timeout=10,
                )
                
                if response.status_code != 200:
                    return ToolResult(
                        success=False,
                        error=f"Sonarr API error: {response.status_code}"
                    )
                
                results = response.json()
                
                shows = []
                for show in results[:5]:
                    shows.append({
                        "title": show.get("title"),
                        "year": show.get("year"),
                        "tvdb_id": show.get("tvdbId"),
                        "overview": (show.get("overview", "")[:150] + "...") if show.get("overview") else "",
                        "status": show.get("status"),
                    })
                
                return ToolResult(
                    success=True,
                    data={
                        "query": query,
                        "count": len(shows),
                        "shows": shows,
                    },
                )
                
        except httpx.TimeoutException:
            return ToolResult(success=False, error="Sonarr request timed out")
        except Exception as e:
            logger.error(f"Error searching Sonarr: {e}")
            return ToolResult(success=False, error=str(e))
