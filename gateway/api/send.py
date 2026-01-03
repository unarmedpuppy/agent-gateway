"""
Unified outbound message API.

Any internal service can send messages to any platform via this endpoint.
"""
from __future__ import annotations

import logging
from typing import Any, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..adapters import AdapterRegistry, OutboundMessage

logger = logging.getLogger(__name__)
router = APIRouter(tags=["send"])


class SendRequest(BaseModel):
    platform: str
    bot: str
    channel: str
    message: str
    thread_id: Optional[str] = None
    metadata: dict = {}


class SendResponse(BaseModel):
    success: bool
    platform: str
    channel: str
    error: Optional[str] = None


@router.post("/send", response_model=SendResponse)
async def send_message(request: SendRequest) -> SendResponse:
    adapter = AdapterRegistry.get(request.platform)

    if not adapter:
        available = list(AdapterRegistry.all().keys())
        raise HTTPException(
            status_code=400,
            detail=f"Unknown platform: {request.platform}. Available: {available}",
        )

    if not adapter.is_healthy():
        raise HTTPException(
            status_code=503,
            detail=f"Adapter for {request.platform} is not healthy",
        )

    msg = OutboundMessage(
        platform=request.platform,
        bot=request.bot,
        channel=request.channel,
        message=request.message,
        thread_id=request.thread_id,
        metadata=request.metadata,
    )

    try:
        success = await adapter.send_message(msg)
        if success:
            logger.info(f"Sent message to {request.platform}/{request.channel}")
            return SendResponse(
                success=True,
                platform=request.platform,
                channel=request.channel,
            )
        else:
            return SendResponse(
                success=False,
                platform=request.platform,
                channel=request.channel,
                error="Failed to send message",
            )
    except Exception as e:
        logger.error(f"Error sending message: {e}")
        return SendResponse(
            success=False,
            platform=request.platform,
            channel=request.channel,
            error=str(e),
        )


class ReactRequest(BaseModel):
    platform: str
    channel: str
    message_id: str
    emoji: str


@router.post("/react")
async def add_reaction(request: ReactRequest) -> dict[str, Any]:
    adapter = AdapterRegistry.get(request.platform)

    if not adapter:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown platform: {request.platform}",
        )

    try:
        success = await adapter.add_reaction(
            request.channel,
            request.message_id,
            request.emoji,
        )
        return {"success": success}
    except Exception as e:
        logger.error(f"Error adding reaction: {e}")
        return {"success": False, "error": str(e)}
