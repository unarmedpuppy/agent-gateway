"""
Agent Core Service

Central service hosting AI agents with platform-agnostic interfaces.
Agents can be accessed by Discord, Mattermost, Telegram, or any HTTP client.

Usage:
    uvicorn main:app --host 0.0.0.0 --port 8000
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import get_settings
from routes import chat_router, health_router, tools_router


# Configure logging
settings = get_settings()
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    logger.info("Agent Core starting up...")
    logger.info(f"Local AI Router URL: {settings.local_ai_url}")
    yield
    logger.info("Agent Core shutting down...")


app = FastAPI(
    title="Agent Core",
    description="Platform-agnostic AI agent service",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware for potential web clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes
app.include_router(health_router)
app.include_router(chat_router)
app.include_router(tools_router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "Agent Core",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/v1/health",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=True,
    )
