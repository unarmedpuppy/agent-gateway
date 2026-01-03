import json
import logging
from typing import Any, Optional

import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from agents import get_agent, list_agents
from auth import resolve_user_role
from config import get_settings
from tools import get_tool, get_openai_tools, ToolRole

logger = logging.getLogger(__name__)
router = APIRouter(tags=["chat"])


class UserInfo(BaseModel):
    platform: str
    platform_user_id: str
    display_name: Optional[str] = None


class ChatContext(BaseModel):
    channel_name: Optional[str] = None
    history: Optional[list[dict]] = None


class ChatRequest(BaseModel):
    message: str
    user: UserInfo
    conversation_id: Optional[str] = None
    context: Optional[ChatContext] = None
    enable_tools: bool = True


class ChatResponse(BaseModel):
    response: str
    agent: str
    conversation_id: Optional[str] = None
    tools_used: list[str] = []


@router.get("/v1/agents")
async def get_agents() -> dict[str, Any]:
    return {"agents": list_agents()}


async def execute_tool(name: str, arguments: dict) -> dict:
    tool = get_tool(name)
    if not tool:
        return {"error": f"Tool '{name}' not found"}
    
    try:
        result = await tool.execute(**arguments)
        if result.success:
            return {"result": result.data}
        else:
            return {"error": result.error}
    except Exception as e:
        logger.error(f"Tool execution error: {e}")
        return {"error": str(e)}


async def call_llm_with_tools(
    settings,
    messages: list[dict],
    tools: list[dict],
    agent,
    conversation_id: str,
    user_id: str,
) -> tuple[str, list[str]]:
    """
    Call LLM with tool support. Handles tool calls iteratively.
    Returns (response_text, tools_used).
    """
    tools_used = []
    max_iterations = 3
    
    payload = {
        "model": agent.model,
        "messages": messages,
        "max_tokens": agent.max_tokens,
        "temperature": agent.temperature,
    }
    
    if tools:
        payload["tools"] = tools
        payload["tool_choice"] = "auto"
    
    headers = {
        "Content-Type": "application/json",
        "X-Enable-Memory": "true",
        "X-Conversation-ID": conversation_id,
        "X-Project": f"agent-core-{agent.agent_id}",
        "X-User-ID": user_id,
    }
    
    if settings.local_ai_api_key:
        headers["Authorization"] = f"Bearer {settings.local_ai_api_key}"
    
    for iteration in range(max_iterations):
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                f"{settings.local_ai_url}/v1/chat/completions",
                json=payload,
                headers=headers,
            )
            
            if response.status_code != 200:
                logger.error(f"LLM API returned {response.status_code}: {response.text}")
                raise Exception(f"LLM API error: {response.status_code}")
            
            data = response.json()
            choice = data["choices"][0]
            message = choice["message"]
            
            if message.get("tool_calls"):
                messages.append(message)
                
                for tool_call in message["tool_calls"]:
                    tool_name = tool_call["function"]["name"]
                    try:
                        tool_args = json.loads(tool_call["function"]["arguments"])
                    except json.JSONDecodeError:
                        tool_args = {}
                    
                    logger.info(f"Executing tool: {tool_name} with args: {tool_args}")
                    tool_result = await execute_tool(tool_name, tool_args)
                    tools_used.append(tool_name)
                    
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call["id"],
                        "name": tool_name,
                        "content": json.dumps(tool_result),
                    })
                
                payload["messages"] = messages
                continue
            
            return message["content"], tools_used
    
    return "I encountered an issue processing your request.", tools_used


@router.post("/v1/agent/{agent_id}/chat")
async def chat_with_agent(
    agent_id: str,
    request: ChatRequest,
) -> ChatResponse:
    agent = get_agent(agent_id)
    if not agent:
        raise HTTPException(
            status_code=404,
            detail=f"Agent '{agent_id}' not found. Available: {[a['id'] for a in list_agents()]}"
        )
    
    settings = get_settings()
    
    if not settings.local_ai_url:
        logger.error("LOCAL_AI_URL not configured")
        if hasattr(agent, 'get_api_down_message'):
            return ChatResponse(
                response=agent.get_api_down_message(),
                agent=agent_id,
                conversation_id=request.conversation_id,
            )
        raise HTTPException(status_code=503, detail="LLM backend not configured")
    
    conversation_id = request.conversation_id
    if not conversation_id:
        conversation_id = f"{request.user.platform}-{agent_id}-default"
    
    messages = [{"role": "system", "content": agent.system_prompt}]
    
    if request.context and request.context.history:
        messages.extend(request.context.history)
    
    user_prefix = request.user.display_name or request.user.platform_user_id
    messages.append({"role": "user", "content": f"{user_prefix}: {request.message}"})
    
    user_role, user_info = resolve_user_role(
        platform=request.user.platform,
        platform_user_id=request.user.platform_user_id,
        display_name=request.user.display_name or request.user.platform_user_id,
    )
    logger.info(f"User {user_info.display_name} ({request.user.platform}:{request.user.platform_user_id}) resolved to role: {user_role.value}")
    
    tools = []
    if request.enable_tools:
        tools = get_openai_tools(user_role)
    
    user_id = f"{request.user.platform}:{request.user.platform_user_id}"
    
    try:
        response_text, tools_used = await call_llm_with_tools(
            settings=settings,
            messages=messages,
            tools=tools,
            agent=agent,
            conversation_id=conversation_id,
            user_id=user_id,
        )
        
        if hasattr(agent, 'needs_fallback') and agent.needs_fallback(response_text):
            logger.info(f"Guardrail triggered for {agent_id}, using fallback")
            response_text = agent.get_fallback_response()
        
        return ChatResponse(
            response=response_text,
            agent=agent_id,
            conversation_id=conversation_id,
            tools_used=tools_used,
        )
        
    except httpx.TimeoutException:
        logger.error("LLM API request timed out")
        if hasattr(agent, 'get_api_down_message'):
            return ChatResponse(
                response=agent.get_api_down_message(),
                agent=agent_id,
                conversation_id=conversation_id,
            )
        raise HTTPException(status_code=504, detail="LLM backend timeout")
        
    except httpx.RequestError as e:
        logger.error(f"LLM API connection error: {e}")
        if hasattr(agent, 'get_api_down_message'):
            return ChatResponse(
                response=agent.get_api_down_message(),
                agent=agent_id,
                conversation_id=conversation_id,
            )
        raise HTTPException(status_code=503, detail="LLM backend unavailable")
        
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        if hasattr(agent, 'get_api_down_message'):
            return ChatResponse(
                response=agent.get_api_down_message(),
                agent=agent_id,
                conversation_id=conversation_id,
            )
        raise HTTPException(status_code=500, detail=str(e))
