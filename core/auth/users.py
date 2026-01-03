"""
User whitelist configuration.

Maps platform:user_id to roles for access control.
"""

from dataclasses import dataclass
from typing import Optional

from tools.base import ToolRole


@dataclass
class UserInfo:
    """User information with role."""
    platform: str
    platform_user_id: str
    display_name: str
    role: ToolRole


# Whitelisted users - add platform:user_id mappings here
# Format: "platform:user_id" -> {"role": ToolRole, "name": "Display Name"}
#
# ROLE CAPABILITIES:
#   PUBLIC  - Can use read-only tools (service_status, game_server_status, disk_usage)
#   TRUSTED - PUBLIC + can use control tools (restart_game_server, restart_container)
#   ADMIN   - TRUSTED + admin tools (docker_compose_up/down, trigger_backup)
#
# To get Discord user IDs:
#   Enable Developer Mode in Discord (Settings > App Settings > Advanced)
#   Right-click user > Copy User ID
#
WHITELISTED_USERS: dict[str, dict] = {
    # ===== ADMINS (full access) =====
    # Discord - Josh
    "discord:244649852473049088": {
        "role": ToolRole.ADMIN,
        "name": "Josh",
    },
    # Mattermost - Josh (get ID from Mattermost profile or logs)
    # "mattermost:USER_ID_HERE": {
    #     "role": ToolRole.ADMIN,
    #     "name": "Josh",
    # },
    
    # ===== TRUSTED (can restart game servers) =====
    # Add Discord users who should be able to restart game servers
    # "discord:USER_ID_HERE": {
    #     "role": ToolRole.TRUSTED,
    #     "name": "Friend Name",
    # },
}

# Default role for unknown users
DEFAULT_ROLE = ToolRole.PUBLIC


def get_user_role(platform: str, platform_user_id: str) -> ToolRole:
    """Get role for a user by platform and ID.
    
    Args:
        platform: Platform name (discord, mattermost, telegram, etc.)
        platform_user_id: User ID on that platform
        
    Returns:
        User's role, or DEFAULT_ROLE if not whitelisted
    """
    key = f"{platform}:{platform_user_id}"
    user_config = WHITELISTED_USERS.get(key)
    
    if user_config:
        return user_config["role"]
    
    return DEFAULT_ROLE


def get_user_info(platform: str, platform_user_id: str, display_name: str = "Unknown") -> UserInfo:
    """Get full user info including role.
    
    Args:
        platform: Platform name
        platform_user_id: User ID on that platform
        display_name: Display name (fallback if not in whitelist)
        
    Returns:
        UserInfo with resolved role
    """
    key = f"{platform}:{platform_user_id}"
    user_config = WHITELISTED_USERS.get(key)
    
    if user_config:
        return UserInfo(
            platform=platform,
            platform_user_id=platform_user_id,
            display_name=user_config.get("name", display_name),
            role=user_config["role"],
        )
    
    return UserInfo(
        platform=platform,
        platform_user_id=platform_user_id,
        display_name=display_name,
        role=DEFAULT_ROLE,
    )
