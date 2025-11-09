"""Metrics for evaluating memory effectiveness"""
import logging
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class EvaluationMetrics:
    """Track and compare metrics for memory effectiveness"""
    
    def __init__(self, metrics_path: str = "evaluation/metrics.jsonl"):
        """
        Initialize metrics tracker
        
        Args:
            metrics_path: Path to JSONL file for storing metrics
        """
        self.metrics_path = Path(metrics_path)
        self.metrics_path.parent.mkdir(parents=True, exist_ok=True)
        logger.info(f"Evaluation metrics initialized: {self.metrics_path}")
    
    def log_comparison(
        self,
        query: str,
        response_with_memory: str,
        response_without_memory: str,
        memory_cases_used: int = 0,
        response_time_with_memory: Optional[float] = None,
        response_time_without_memory: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Log comparison between responses with and without memory
        
        Args:
            query: User query
            response_with_memory: Response when memory is enabled
            response_without_memory: Response when memory is disabled
            memory_cases_used: Number of memory cases used
            response_time_with_memory: Time taken with memory (seconds)
            response_time_without_memory: Time taken without memory (seconds)
            metadata: Additional metadata
        """
        metric = {
            "timestamp": datetime.now().isoformat(),
            "query": query,
            "response_with_memory": response_with_memory,
            "response_without_memory": response_without_memory,
            "memory_cases_used": memory_cases_used,
            "response_time_with_memory": response_time_with_memory,
            "response_time_without_memory": response_time_without_memory,
            "response_length_with_memory": len(response_with_memory),
            "response_length_without_memory": len(response_without_memory),
        }
        
        if metadata:
            metric.update(metadata)
        
        try:
            with open(self.metrics_path, 'a', encoding='utf-8') as f:
                json_line = json.dumps(metric, ensure_ascii=False)
                f.write(json_line + '\n')
            logger.info(f"Logged comparison metric: {self.metrics_path}")
        except Exception as e:
            logger.error(f"Error logging metric: {e}", exc_info=True)
    
    def log_response(
        self,
        query: str,
        response: str,
        has_memory: bool,
        memory_cases_used: int = 0,
        response_time: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Log single response (with or without memory)
        
        Args:
            query: User query
            response: Agent response
            has_memory: Whether memory was enabled
            memory_cases_used: Number of memory cases used
            response_time: Time taken (seconds)
            metadata: Additional metadata
        """
        metric = {
            "timestamp": datetime.now().isoformat(),
            "query": query,
            "response": response,
            "has_memory": has_memory,
            "memory_cases_used": memory_cases_used,
            "response_time": response_time,
            "response_length": len(response),
        }
        
        if metadata:
            metric.update(metadata)
        
        try:
            with open(self.metrics_path, 'a', encoding='utf-8') as f:
                json_line = json.dumps(metric, ensure_ascii=False)
                f.write(json_line + '\n')
            logger.debug(f"Logged response metric: has_memory={has_memory}")
        except Exception as e:
            logger.error(f"Error logging metric: {e}", exc_info=True)
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics from logged metrics
        
        Returns:
            Dictionary with statistics
        """
        if not self.metrics_path.exists():
            return {"error": "No metrics file found"}
        
        comparisons = []
        with_memory = []
        without_memory = []
        
        try:
            with open(self.metrics_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        metric = json.loads(line)
                        
                        # Check if it's a comparison
                        if "response_with_memory" in metric:
                            comparisons.append(metric)
                        elif metric.get("has_memory"):
                            with_memory.append(metric)
                        else:
                            without_memory.append(metric)
                    except json.JSONDecodeError:
                        continue
            
            stats = {
                "total_comparisons": len(comparisons),
                "total_with_memory": len(with_memory),
                "total_without_memory": len(without_memory),
                "total_metrics": len(comparisons) + len(with_memory) + len(without_memory)
            }
            
            if comparisons:
                # Calculate averages for comparisons
                avg_time_with = sum(
                    m.get("response_time_with_memory", 0) or 0 
                    for m in comparisons
                ) / len(comparisons)
                avg_time_without = sum(
                    m.get("response_time_without_memory", 0) or 0 
                    for m in comparisons
                ) / len(comparisons)
                
                avg_length_with = sum(
                    m.get("response_length_with_memory", 0) 
                    for m in comparisons
                ) / len(comparisons)
                avg_length_without = sum(
                    m.get("response_length_without_memory", 0) 
                    for m in comparisons
                ) / len(comparisons)
                
                stats["comparison_stats"] = {
                    "avg_response_time_with_memory": round(avg_time_with, 3),
                    "avg_response_time_without_memory": round(avg_time_without, 3),
                    "avg_response_length_with_memory": round(avg_length_with, 1),
                    "avg_response_length_without_memory": round(avg_length_without, 1),
                    "time_difference": round(avg_time_with - avg_time_without, 3),
                    "length_difference": round(avg_length_with - avg_length_without, 1),
                }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting statistics: {e}", exc_info=True)
            return {"error": str(e)}

