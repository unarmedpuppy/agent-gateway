"""Docker compose tools - bring stacks up/down."""

import asyncio
import logging
import os
from typing import Any

from ..base import ToolBase, ToolCategory, ToolRole, ToolResult

logger = logging.getLogger(__name__)

APPS_DIR = "/server/apps"

ALLOWED_APPS = {
    "jellyfin",
    "sonarr",
    "radarr",
    "prowlarr",
    "qbittorrent",
    "plex",
    "immich",
    "homepage",
    "traefik",
    "grafana",
    "adguard-home",
    "ghost",
    "wiki",
    "monica",
    "mealie",
    "frigate",
    "mattermost",
    "discord-reaction-bot",
    "agent-core",
    "local-ai-router",
    "bird",
    "bird-viewer",
    "polymarket-bot",
}


class DockerComposeUpTool(ToolBase):
    
    @property
    def name(self) -> str:
        return "docker_compose_up"
    
    @property
    def description(self) -> str:
        return "Start a Docker Compose stack"
    
    @property
    def category(self) -> ToolCategory:
        return ToolCategory.CONTROL
    
    @property
    def required_role(self) -> ToolRole:
        return ToolRole.ADMIN
    
    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "app_name": {
                "type": "string",
                "description": f"Name of the app to start. Allowed: {', '.join(sorted(ALLOWED_APPS))}",
                "required": True,
            },
        }
    
    async def execute(self, app_name: str = None, **kwargs) -> ToolResult:
        if not app_name:
            return ToolResult(success=False, error="app_name is required")
        
        app_name = app_name.strip().lower()
        
        if app_name not in ALLOWED_APPS:
            return ToolResult(
                success=False,
                error=f"App '{app_name}' not in allowed list. Allowed: {', '.join(sorted(ALLOWED_APPS))}"
            )
        
        compose_path = os.path.join(APPS_DIR, app_name, "docker-compose.yml")
        if not os.path.exists(compose_path):
            return ToolResult(
                success=False,
                error=f"docker-compose.yml not found for '{app_name}'"
            )
        
        try:
            proc = await asyncio.create_subprocess_exec(
                "docker", "compose", "-f", compose_path, "up", "-d",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=os.path.join(APPS_DIR, app_name),
            )
            stdout, stderr = await proc.communicate()
            
            if proc.returncode != 0:
                return ToolResult(
                    success=False,
                    error=f"docker compose up failed: {stderr.decode()}"
                )
            
            return ToolResult(
                success=True,
                data={
                    "app": app_name,
                    "action": "started",
                    "message": f"App '{app_name}' started successfully",
                },
            )
            
        except Exception as e:
            logger.error(f"Error starting app {app_name}: {e}")
            return ToolResult(success=False, error=str(e))


class DockerComposeDownTool(ToolBase):
    
    @property
    def name(self) -> str:
        return "docker_compose_down"
    
    @property
    def description(self) -> str:
        return "Stop a Docker Compose stack"
    
    @property
    def category(self) -> ToolCategory:
        return ToolCategory.CONTROL
    
    @property
    def required_role(self) -> ToolRole:
        return ToolRole.ADMIN
    
    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "app_name": {
                "type": "string",
                "description": f"Name of the app to stop. Allowed: {', '.join(sorted(ALLOWED_APPS))}",
                "required": True,
            },
        }
    
    async def execute(self, app_name: str = None, **kwargs) -> ToolResult:
        if not app_name:
            return ToolResult(success=False, error="app_name is required")
        
        app_name = app_name.strip().lower()
        
        if app_name not in ALLOWED_APPS:
            return ToolResult(
                success=False,
                error=f"App '{app_name}' not in allowed list. Allowed: {', '.join(sorted(ALLOWED_APPS))}"
            )
        
        compose_path = os.path.join(APPS_DIR, app_name, "docker-compose.yml")
        if not os.path.exists(compose_path):
            return ToolResult(
                success=False,
                error=f"docker-compose.yml not found for '{app_name}'"
            )
        
        try:
            proc = await asyncio.create_subprocess_exec(
                "docker", "compose", "-f", compose_path, "down",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=os.path.join(APPS_DIR, app_name),
            )
            stdout, stderr = await proc.communicate()
            
            if proc.returncode != 0:
                return ToolResult(
                    success=False,
                    error=f"docker compose down failed: {stderr.decode()}"
                )
            
            return ToolResult(
                success=True,
                data={
                    "app": app_name,
                    "action": "stopped",
                    "message": f"App '{app_name}' stopped successfully",
                },
            )
            
        except Exception as e:
            logger.error(f"Error stopping app {app_name}: {e}")
            return ToolResult(success=False, error=str(e))
