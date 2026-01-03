"""Auth module for role-based access control."""

from .users import get_user_role, UserInfo
from .middleware import resolve_user_role

__all__ = ["get_user_role", "UserInfo", "resolve_user_role"]
