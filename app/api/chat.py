"""Chat API endpoints"""
import logging
from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Body
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse
from pydantic import BaseModel
import json

from app.schemas.chat import StreamChatRequest
from app.core.agent_factory import create_agent
from app.core.config import load_agent_config, list_available_agents
from app.core.agent_config import AgentConfig

logger = logging.getLogger("api")
agent_logger = logging.getLogger("agent")

router = APIRouter()

# Cache for agents (key: config_path, value: agent instance)
_agent_cache = {}


def get_agent(config_path: str, use_tools: bool = False):
    """
    Get or create agent from cache
    
    Args:
        config_path: Path to config file
        use_tools: Whether to use tools
        
    Returns:
        Agent instance
    """
    cache_key = f"{config_path}:{use_tools}"
    
    if cache_key not in _agent_cache:
        try:
            agent_logger.info(f"Creating agent from config: {config_path} (use_tools={use_tools})")
            agent = create_agent(config_path=config_path, use_tools=use_tools)
            _agent_cache[cache_key] = agent
            agent_logger.info(f"Created and cached agent: {config_path}")
        except Exception as e:
            agent_logger.error(f"Failed to create agent {config_path}: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Failed to create agent: {str(e)}")
    
    return _agent_cache[cache_key]


@router.post("/chat/stream")
async def stream_chat_handler(request: StreamChatRequest):
    """
    Endpoint to handle streaming chat requests.
    
    Supports:
    - agent_name: Ignored (single agent only)
    - config_path: Full path to config file (optional, overrides agent_name)
    - use_tools: Whether to use tools (default: False)
    """
    try:
        # Single agent - use default config
        # Multi-agent support commented out for simplicity
        # if request.config_path:
        #     config_path = request.config_path
        # elif request.agent_name:
        #     config_path = f"configs/{request.agent_name}.yaml"
        # else:
        #     config_path = "configs/agent.yaml"
        
        # Single agent configuration
        config_path = "configs/agent.yaml"
        
        logger.info(
            f"Chat request - Conversation: {request.conversation_id}, "
            f"Message length: {len(request.message)}"
        )
        
        # Get agent
        use_tools = request.use_tools if hasattr(request, 'use_tools') else False
        agent = get_agent(config_path, use_tools=use_tools)
        
        agent_logger.info(
            f"Processing message - Agent: {agent.agent_name}, "
            f"Conversation: {request.conversation_id}"
        )
        
        # Process message
        async def generate():
            try:
                chunk_count = 0
                async for chunk in agent.process_message(
                    user_message=request.message,
                    conversation_id=request.conversation_id
                ):
                    chunk_count += 1
                    yield chunk
                
                agent_logger.info(
                    f"Message processed - Agent: {agent.agent_name}, "
                    f"Conversation: {request.conversation_id}, "
                    f"Chunks: {chunk_count}"
                )
            except Exception as e:
                agent_logger.error(
                    f"Error in chat stream - Agent: {agent.agent_name}, "
                    f"Conversation: {request.conversation_id}, "
                    f"Error: {e}",
                    exc_info=True
                )
                yield {"data": json.dumps({"error": "Đã xảy ra lỗi khi xử lý yêu cầu."})}
        
        return EventSourceResponse(generate())
        
    except Exception as e:
        logger.error(f"Error in stream_chat_handler: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agents")
async def list_agents():
    """
    List all available agents
    
    Returns:
        List of available agent names
    """
    try:
        agents = list_available_agents()
        return {
            "agents": agents,
            "count": len(agents)
        }
    except Exception as e:
        logger.error(f"Error listing agents: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agents/{agent_name}")
async def get_agent_info(agent_name: str):
    """
    Get agent configuration info
    
    Args:
        agent_name: Name of agent config
        
    Returns:
        Agent configuration info
    """
    try:
        config_path = f"configs/{agent_name}.yaml"
        config = load_agent_config(config_path)
        
        return {
            "name": agent_name,
            "agent": config.agent,
            "has_tools": len(config.tools) > 0,
            "tools_count": len(config.tools),
            "memory_enabled": config.memory.enabled,
            "model": {
                "provider": config.model.provider,
                "model_name": config.model.model_name
            }
        }
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Agent not found: {agent_name}")
    except Exception as e:
        logger.error(f"Error getting agent info: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


class ResetRequest(BaseModel):
    """Request model for reset conversation"""
    conversation_id: Optional[str] = None


@router.post("/agents/{agent_name}/reset")
async def reset_agent_conversation(agent_name: str, request_data: ResetRequest = Body(...)):
    """
    Reset conversation (single agent)
    
    Args:
        agent_name: Ignored, uses default agent
        request_data: Request body with optional conversation_id
    """
    try:
        conversation_id = request_data.conversation_id if request_data else None
        
        # Always use default agent config
        config_path = "configs/agent.yaml"
        agent = get_agent(config_path, use_tools=False)
        
        # Reset conversation
        agent.reset_conversation(conversation_id=conversation_id)
        
        return {
            "status": "success",
            "message": "Conversation reset",
            "conversation_id": conversation_id or "all"
        }
    except Exception as e:
        logger.error(f"Error resetting conversation: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

