"""
Agent Gateway - Unified platform adapter service.

Connects to Discord, Mattermost, and other platforms, routing messages
to agent-core for AI-powered responses.
"""
from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .adapters import AdapterRegistry
from .adapters.discord import DiscordAdapter
from .adapters.mattermost import MattermostAdapter
from .adapters.mattermost.webhooks import router as mm_webhook_router, set_adapter as set_mm_adapter
from .api import health_router, send_router

settings = get_settings()

logging.basicConfig(
    level=getattr(logging, settings.gateway_log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    discord_adapter = DiscordAdapter()
    mattermost_adapter = MattermostAdapter()

    AdapterRegistry.register(discord_adapter)
    AdapterRegistry.register(mattermost_adapter)

    set_mm_adapter(mattermost_adapter)

    await AdapterRegistry.connect_all()
    logger.info("All adapters connected")

    yield

    await AdapterRegistry.disconnect_all()
    logger.info("All adapters disconnected")


app = FastAPI(
    title="Agent Gateway",
    description="Unified platform adapter for Discord, Mattermost, and more",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(send_router)
app.include_router(mm_webhook_router)


@app.get("/")
async def root():
    return {
        "service": "agent-gateway",
        "status": "running",
        "adapters": list(AdapterRegistry.all().keys()),
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=settings.gateway_port)
