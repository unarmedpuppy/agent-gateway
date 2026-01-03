"""Tools endpoint for listing available tools."""

from typing import Any, Optional

from fastapi import APIRouter

from tools import list_tools, ToolCategory, ToolRole

router = APIRouter(tags=["tools"])


@router.get("/v1/tools")
async def get_tools(
    category: Optional[str] = None,
    role: Optional[str] = None,
) -> dict[str, Any]:
    """
    List available tools.
    
    Args:
        category: Filter by category (read_only, control, media, life_os)
        role: Filter by maximum required role (public, trusted, admin)
    """
    cat = None
    if category:
        try:
            cat = ToolCategory(category)
        except ValueError:
            pass
    
    r = None
    if role:
        try:
            r = ToolRole(role)
        except ValueError:
            pass
    
    tools = list_tools(category=cat, role=r)
    
    return {
        "tools": tools,
        "count": len(tools),
    }
