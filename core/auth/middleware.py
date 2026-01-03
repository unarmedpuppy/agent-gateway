"""
Auth middleware for role-based access control.

Resolves user roles and filters tools based on permissions.
"""

from typing import Optional

from tools.base import ToolRole
from .users import get_user_role, get_user_info, UserInfo


def resolve_user_role(
    platform: Optional[str],
    platform_user_id: Optional[str],
    display_name: str = "Unknown",
) -> tuple[ToolRole, UserInfo]:
    """Resolve user's role from platform and user ID.
    
    Args:
        platform: Platform name (discord, mattermost, etc.)
        platform_user_id: User ID on that platform
        display_name: Display name for user
        
    Returns:
        Tuple of (role, user_info)
    """
    if not platform or not platform_user_id:
        # Unknown user - public access only
        return ToolRole.PUBLIC, UserInfo(
            platform=platform or "unknown",
            platform_user_id=platform_user_id or "unknown",
            display_name=display_name,
            role=ToolRole.PUBLIC,
        )
    
    user_info = get_user_info(platform, platform_user_id, display_name)
    return user_info.role, user_info


def can_use_tool(user_role: ToolRole, tool_required_role: ToolRole) -> bool:
    """Check if user with given role can use a tool.
    
    Role hierarchy:
    - ADMIN can use all tools
    - TRUSTED can use PUBLIC and TRUSTED tools
    - PUBLIC can only use PUBLIC tools
    
    Args:
        user_role: User's role
        tool_required_role: Role required by the tool
        
    Returns:
        True if user can use the tool
    """
    role_hierarchy = {
        ToolRole.PUBLIC: [ToolRole.PUBLIC],
        ToolRole.TRUSTED: [ToolRole.PUBLIC, ToolRole.TRUSTED],
        ToolRole.ADMIN: [ToolRole.PUBLIC, ToolRole.TRUSTED, ToolRole.ADMIN],
    }
    
    allowed_roles = role_hierarchy.get(user_role, [ToolRole.PUBLIC])
    return tool_required_role in allowed_roles
