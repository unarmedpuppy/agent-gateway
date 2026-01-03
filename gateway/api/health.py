"""
Health check endpoints for the gateway.
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from ..adapters import AdapterRegistry

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check() -> dict[str, Any]:
    adapters_status = {}
    all_healthy = True

    for platform, adapter in AdapterRegistry.all().items():
        healthy = adapter.is_healthy()
        adapters_status[platform] = {
            "healthy": healthy,
            "bots": adapter.get_configured_bots(),
        }
        if not healthy:
            all_healthy = False

    return {
        "status": "healthy" if all_healthy else "degraded",
        "adapters": adapters_status,
    }


@router.get("/adapters")
async def list_adapters() -> dict[str, Any]:
    adapters = []
    for platform, adapter in AdapterRegistry.all().items():
        adapters.append({
            "platform": platform,
            "healthy": adapter.is_healthy(),
            "bots": adapter.get_configured_bots(),
        })
    return {"adapters": adapters}
