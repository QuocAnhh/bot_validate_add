#!/usr/bin/env python3
"""Script to compare responses with and without memory"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.config import load_agent_config
from app.core.agent_factory import create_agent
from app.evaluation.comparator import ResponseComparator


async def main():
    """Compare responses with and without memory"""
    print("=" * 60)
    print("Memory Effectiveness Comparison")
    print("=" * 60)
    print()
    
    # Load config
    config = load_agent_config('configs/agent.yaml')
    
    # Create agent with memory
    print("Creating agent with memory...")
    config_with_memory = config.model_copy(deep=True)
    config_with_memory.memory.enabled = True
    agent_with_memory = create_agent(config_with_memory)
    
    # Create agent without memory
    print("Creating agent without memory...")
    config_without_memory = config.model_copy(deep=True)
    config_without_memory.memory.enabled = False
    agent_without_memory = create_agent(config_without_memory)
    
    # Test queries
    test_queries = [
        "Xin chào, bạn có thể giúp tôi không?",
        "Giải thích cho tôi về AI là gì?",
        "Hôm nay thời tiết như thế nào?",
    ]
    
    comparator = ResponseComparator()
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{'=' * 60}")
        print(f"Test {i}/{len(test_queries)}")
        print(f"Query: {query}")
        print(f"{'=' * 60}\n")
        
        results = await comparator.compare_responses(
            agent_with_memory=agent_with_memory,
            agent_without_memory=agent_without_memory,
            query=query
        )
        
        print("Response WITH memory:")
        print(f"  Time: {results['with_memory'].get('response_time', 'N/A')}s")
        print(f"  Cases used: {results['with_memory'].get('memory_cases_used', 0)}")
        print(f"  Response: {results['with_memory'].get('response', 'N/A')[:200]}...")
        print()
        
        print("Response WITHOUT memory:")
        print(f"  Time: {results['without_memory'].get('response_time', 'N/A')}s")
        print(f"  Response: {results['without_memory'].get('response', 'N/A')[:200]}...")
        print()
        
        if results.get('comparison'):
            comp = results['comparison']
            print("Comparison:")
            print(f"  Length difference: {comp.get('response_length_diff', 0)} chars")
            print(f"  Time difference: {comp.get('response_time_diff', 0):.3f}s")
            print(f"  Responses are different: {comp.get('responses_are_different', False)}")
        print()
    
    # Get statistics
    from app.evaluation.metrics import EvaluationMetrics
    metrics = EvaluationMetrics()
    stats = metrics.get_statistics()
    
    print("=" * 60)
    print("Overall Statistics")
    print("=" * 60)
    print(f"Total comparisons: {stats.get('total_comparisons', 0)}")
    if stats.get('comparison_stats'):
        cs = stats['comparison_stats']
        print(f"Average response time (with memory): {cs.get('avg_response_time_with_memory', 0):.3f}s")
        print(f"Average response time (without memory): {cs.get('avg_response_time_without_memory', 0):.3f}s")
        print(f"Time difference: {cs.get('time_difference', 0):.3f}s")
        print(f"Length difference: {cs.get('length_difference', 0):.1f} chars")
    print()


if __name__ == "__main__":
    asyncio.run(main())

