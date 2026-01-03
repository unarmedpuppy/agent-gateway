"""
Mattermost webhook handlers.

Receives outgoing webhooks from Mattermost when @tayne is mentioned.
"""
from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Form, HTTPException

from .config import get_mattermost_settings
from .adapter import MattermostAdapter

logger = logging.getLogger(__name__)
router = APIRouter(tags=["mattermost-webhooks"])

_adapter: MattermostAdapter | None = None


def set_adapter(adapter: MattermostAdapter) -> None:
    global _adapter
    _adapter = adapter


@router.post("/webhook/mattermost/tayne")
async def handle_tayne_mention(
    token: str = Form(default=""),
    team_id: str = Form(default=""),
    team_domain: str = Form(default=""),
    channel_id: str = Form(default=""),
    channel_name: str = Form(default=""),
    timestamp: str = Form(default=""),
    user_id: str = Form(default=""),
    user_name: str = Form(default=""),
    post_id: str = Form(default=""),
    text: str = Form(default=""),
    trigger_word: str = Form(default="@tayne"),
) -> dict[str, Any]:
    logger.info(f"Tayne mentioned by {user_name} in {channel_name}: {text[:50]}...")

    settings = get_mattermost_settings()
    if settings.tayne_webhook_token and token != settings.tayne_webhook_token:
        logger.warning(f"Invalid webhook token from {user_name}")
        raise HTTPException(status_code=401, detail="Invalid webhook token")

    if not _adapter:
        logger.error("Mattermost adapter not initialized")
        return {
            "text": "I seem to be having technical difficulties.",
            "response_type": "comment",
        }

    response = await _adapter.handle_tayne_webhook(
        user_id=user_id,
        user_name=user_name,
        channel_id=channel_id,
        text=text,
        post_id=post_id,
        trigger_word=trigger_word,
    )

    if response:
        return {
            "text": response,
            "response_type": "comment",
        }

    return {}


@router.get("/webhook/mattermost/health")
async def mattermost_health() -> dict[str, Any]:
    settings = get_mattermost_settings()

    agent_core_healthy = False
    if settings.agent_core_url:
        try:
            import httpx
            async with httpx.AsyncClient(timeout=5) as client:
                resp = await client.get(f"{settings.agent_core_url}/v1/health")
                agent_core_healthy = resp.status_code == 200
        except Exception:
            pass

    adapter_healthy = _adapter.is_healthy() if _adapter else False

    status = "healthy" if agent_core_healthy and adapter_healthy else "degraded"

    return {
        "status": status,
        "agent_core": "connected" if agent_core_healthy else "disconnected",
        "adapter": "healthy" if adapter_healthy else "unhealthy",
    }
