"""Radarr search tool - search and add movies."""

import logging
from typing import Any

import httpx

from ..base import ToolBase, ToolCategory, ToolRole, ToolResult
from config import get_settings

logger = logging.getLogger(__name__)


class RadarrSearchTool(ToolBase):
    
    @property
    def name(self) -> str:
        return "radarr_search"
    
    @property
    def description(self) -> str:
        return "Search for movies in Radarr"
    
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
                "description": "Movie name to search for",
                "required": True,
            },
        }
    
    async def execute(self, query: str = None, **kwargs) -> ToolResult:
        if not query:
            return ToolResult(success=False, error="query is required")
        
        settings = get_settings()
        
        if not settings.radarr_api_key:
            return ToolResult(
                success=False,
                error="Radarr API key not configured"
            )
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{settings.radarr_url}/api/v3/movie/lookup",
                    params={"term": query},
                    headers={"X-Api-Key": settings.radarr_api_key},
                    timeout=10,
                )
                
                if response.status_code != 200:
                    return ToolResult(
                        success=False,
                        error=f"Radarr API error: {response.status_code}"
                    )
                
                results = response.json()
                
                movies = []
                for movie in results[:5]:
                    movies.append({
                        "title": movie.get("title"),
                        "year": movie.get("year"),
                        "tmdb_id": movie.get("tmdbId"),
                        "overview": (movie.get("overview", "")[:150] + "...") if movie.get("overview") else "",
                        "status": movie.get("status"),
                    })
                
                return ToolResult(
                    success=True,
                    data={
                        "query": query,
                        "count": len(movies),
                        "movies": movies,
                    },
                )
                
        except httpx.TimeoutException:
            return ToolResult(success=False, error="Radarr request timed out")
        except Exception as e:
            logger.error(f"Error searching Radarr: {e}")
            return ToolResult(success=False, error=str(e))
