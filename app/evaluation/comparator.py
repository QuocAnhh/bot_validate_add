"""Compare responses with and without memory"""
import logging
import time
from typing import Dict, Any, Optional, Tuple

from app.evaluation.metrics import EvaluationMetrics

logger = logging.getLogger(__name__)


class ResponseComparator:
    """Compare agent responses with and without memory"""
    
    def __init__(self, metrics: Optional[EvaluationMetrics] = None):
        """
        Initialize comparator
        
        Args:
            metrics: Optional metrics tracker
        """
        self.metrics = metrics or EvaluationMetrics()
        logger.info("ResponseComparator initialized")
    
    async def compare_responses(
        self,
        agent_with_memory,
        agent_without_memory,
        query: str,
        conversation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Compare responses from agent with and without memory
        
        Args:
            agent_with_memory: Agent instance with memory enabled
            agent_without_memory: Agent instance with memory disabled
            query: User query
            conversation_id: Optional conversation ID
            
        Returns:
            Comparison results
        """
        results = {
            "query": query,
            "with_memory": None,
            "without_memory": None,
            "comparison": {}
        }
        
        # Get response with memory
        try:
            start_time = time.time()
            response_with_memory = ""
            memory_cases_used = 0
            
            async for chunk in agent_with_memory.process_message(query, conversation_id):
                chunk_data = chunk.get("data", "{}")
                import json
                try:
                    data = json.loads(chunk_data)
                    if "content" in data:
                        response_with_memory += data["content"]
                except:
                    pass
            
            time_with_memory = time.time() - start_time
            
            # Count memory cases used (if available)
            if hasattr(agent_with_memory, 'memory') and agent_with_memory.memory:
                # Try to get last retrieval count from logs or agent state
                memory_cases_used = agent_with_memory.memory.get_case_count()
            
            results["with_memory"] = {
                "response": response_with_memory,
                "response_time": round(time_with_memory, 3),
                "memory_cases_used": memory_cases_used
            }
            
        except Exception as e:
            logger.error(f"Error getting response with memory: {e}", exc_info=True)
            results["with_memory"] = {"error": str(e)}
        
        # Get response without memory
        try:
            start_time = time.time()
            response_without_memory = ""
            
            async for chunk in agent_without_memory.process_message(query, conversation_id):
                chunk_data = chunk.get("data", "{}")
                import json
                try:
                    data = json.loads(chunk_data)
                    if "content" in data:
                        response_without_memory += data["content"]
                except:
                    pass
            
            time_without_memory = time.time() - start_time
            
            results["without_memory"] = {
                "response": response_without_memory,
                "response_time": round(time_without_memory, 3)
            }
            
        except Exception as e:
            logger.error(f"Error getting response without memory: {e}", exc_info=True)
            results["without_memory"] = {"error": str(e)}
        
        # Calculate comparison metrics
        if results["with_memory"].get("response") and results["without_memory"].get("response"):
            results["comparison"] = {
                "response_length_diff": len(results["with_memory"]["response"]) - len(results["without_memory"]["response"]),
                "response_time_diff": results["with_memory"]["response_time"] - results["without_memory"]["response_time"],
                "responses_are_different": results["with_memory"]["response"] != results["without_memory"]["response"]
            }
            
            # Log comparison
            self.metrics.log_comparison(
                query=query,
                response_with_memory=results["with_memory"]["response"],
                response_without_memory=results["without_memory"]["response"],
                memory_cases_used=memory_cases_used,
                response_time_with_memory=results["with_memory"]["response_time"],
                response_time_without_memory=results["without_memory"]["response_time"]
            )
        
        return results

