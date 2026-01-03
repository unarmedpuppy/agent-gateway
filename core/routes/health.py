"""Health check endpoints."""

import httpx
from fastapi import APIRouter

from config import get_settings
from agents import list_agents

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check() -> dict:
    """Basic health check."""
    return {"status": "healthy"}


@router.get("/v1/health")
async def health_check_v1() -> dict:
    """
    Detailed health check including dependencies.
    
    Checks:
    - Service status
    - Local AI Router connectivity
    - Available agents
    """
    settings = get_settings()
    
    # Check local-ai-router
    local_ai_healthy = False
    local_ai_error = None
    
    if settings.local_ai_url:
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(f"{settings.local_ai_url}/health")
                local_ai_healthy = response.status_code == 200
        except httpx.TimeoutException:
            local_ai_error = "timeout"
        except httpx.RequestError as e:
            local_ai_error = str(e)
        except Exception as e:
            local_ai_error = str(e)
    else:
        local_ai_error = "not configured"
    
    # Get available agents
    agents = list_agents()
    
    # Determine overall status
    if local_ai_healthy:
        status = "healthy"
    else:
        status = "degraded"
    
    return {
        "status": status,
        "local_ai_router": {
            "connected": local_ai_healthy,
            "url": settings.local_ai_url or "not configured",
            "error": local_ai_error,
        },
        "agents": agents,
        "version": "1.0.0",
    }
