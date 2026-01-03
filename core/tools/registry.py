from typing import Optional

from .base import ToolBase, ToolCategory, ToolRole


_TOOLS: dict[str, ToolBase] = {}


def _register_tools():
    global _TOOLS
    
    from .read_only.service_status import ServiceStatusTool
    from .read_only.disk_usage import DiskUsageTool
    from .read_only.container_logs import ContainerLogsTool
    from .read_only.game_server_status import GameServerStatusTool
    
    from .control.restart_container import RestartContainerTool
    from .control.restart_game_server import RestartGameServerTool
    from .control.docker_compose import DockerComposeUpTool, DockerComposeDownTool
    from .control.trigger_backup import TriggerBackupTool
    
    from .media.sonarr_search import SonarrSearchTool
    from .media.radarr_search import RadarrSearchTool
    from .media.plex_control import PlexScanLibraryTool
    
    tools = [
        ServiceStatusTool(),
        DiskUsageTool(),
        ContainerLogsTool(),
        GameServerStatusTool(),
        RestartContainerTool(),
        RestartGameServerTool(),
        DockerComposeUpTool(),
        DockerComposeDownTool(),
        TriggerBackupTool(),
        SonarrSearchTool(),
        RadarrSearchTool(),
        PlexScanLibraryTool(),
    ]
    
    for tool in tools:
        _TOOLS[tool.name] = tool


def get_tool(name: str) -> Optional[ToolBase]:
    if not _TOOLS:
        _register_tools()
    return _TOOLS.get(name)


def list_tools(
    category: Optional[ToolCategory] = None,
    role: Optional[ToolRole] = None,
) -> list[dict]:
    if not _TOOLS:
        _register_tools()
    
    tools = list(_TOOLS.values())
    
    if category:
        tools = [t for t in tools if t.category == category]
    
    if role:
        role_hierarchy = {
            ToolRole.PUBLIC: [ToolRole.PUBLIC],
            ToolRole.TRUSTED: [ToolRole.PUBLIC, ToolRole.TRUSTED],
            ToolRole.ADMIN: [ToolRole.PUBLIC, ToolRole.TRUSTED, ToolRole.ADMIN],
        }
        allowed_roles = role_hierarchy.get(role, [ToolRole.PUBLIC])
        tools = [t for t in tools if t.required_role in allowed_roles]
    
    return [t.to_dict() for t in tools]


def get_tools_for_agent(agent_id: str, user_role: ToolRole = ToolRole.PUBLIC) -> list[ToolBase]:
    if not _TOOLS:
        _register_tools()
    
    role_hierarchy = {
        ToolRole.PUBLIC: [ToolRole.PUBLIC],
        ToolRole.TRUSTED: [ToolRole.PUBLIC, ToolRole.TRUSTED],
        ToolRole.ADMIN: [ToolRole.PUBLIC, ToolRole.TRUSTED, ToolRole.ADMIN],
    }
    allowed_roles = role_hierarchy.get(user_role, [ToolRole.PUBLIC])
    
    return [t for t in _TOOLS.values() if t.required_role in allowed_roles]


def get_openai_tools(user_role: ToolRole = ToolRole.PUBLIC) -> list[dict]:
    tools = get_tools_for_agent("any", user_role)
    return [t.to_openai_function() for t in tools]
