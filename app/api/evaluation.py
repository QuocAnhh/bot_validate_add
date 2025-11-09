"""API endpoints for evaluation and comparison"""
import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel

from app.core.config import load_agent_config
from app.core.agent_factory import create_agent
from app.evaluation.comparator import ResponseComparator
from app.evaluation.metrics import EvaluationMetrics

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/evaluation", tags=["evaluation"])


class CompareRequest(BaseModel):
    """Request model for comparison"""
    message: str
    conversation_id: Optional[str] = None


@router.post("/compare")
async def compare_with_without_memory(request: CompareRequest = Body(...)):
    """
    Compare agent responses with and without memory
    
    This endpoint creates two agent instances:
    - One with memory enabled
    - One with memory disabled
    
    Then compares their responses to the same query.
    """
    try:
        # Load config
        config = load_agent_config('configs/agent.yaml')
        
        # Create agent with memory
        config_with_memory = config.model_copy(deep=True)
        config_with_memory.memory.enabled = True
        agent_with_memory = create_agent(config=config_with_memory)
        
        # Create agent without memory
        config_without_memory = config.model_copy(deep=True)
        config_without_memory.memory.enabled = False
        agent_without_memory = create_agent(config=config_without_memory)
        
        # Compare responses
        comparator = ResponseComparator()
        results = await comparator.compare_responses(
            agent_with_memory=agent_with_memory,
            agent_without_memory=agent_without_memory,
            query=request.message,
            conversation_id=request.conversation_id
        )
        
        return {
            "success": True,
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Error in comparison: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/statistics")
async def get_evaluation_statistics():
    """
    Get evaluation statistics from logged metrics
    """
    try:
        metrics = EvaluationMetrics()
        stats = metrics.get_statistics()
        return {
            "success": True,
            "statistics": stats
        }
    except Exception as e:
        logger.error(f"Error getting statistics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/log-response")
async def log_response(
    has_memory: bool = Body(...),
    query: str = Body(...),
    response: str = Body(...),
    memory_cases_used: int = Body(0),
    response_time: Optional[float] = Body(None)
):
    """
    Manually log a response for evaluation
    """
    try:
        metrics = EvaluationMetrics()
        metrics.log_response(
            query=query,
            response=response,
            has_memory=has_memory,
            memory_cases_used=memory_cases_used,
            response_time=response_time
        )
        return {"success": True, "message": "Response logged"}
    except Exception as e:
        logger.error(f"Error logging response: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

