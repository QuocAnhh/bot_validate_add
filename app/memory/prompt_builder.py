"""Build prompts from retrieved cases"""
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


def build_prompt_from_cases(
    query: str,
    retrieved_cases: List[Dict[str, Any]],
    original_cases: Optional[List[Dict[str, Any]]] = None,
    max_positive: int = 4,
    max_negative: int = 2,
    include_negative: bool = False
) -> Optional[str]:
    """
    Build prompt with examples from retrieved cases
    
    Adapted from Memento's build_prompt_from_cases but simplified for single agent
    
    Args:
        query: Current user query
        retrieved_cases: Retrieved cases from memory
        original_cases: Original cases list (for reward info)
        max_positive: Max number of positive examples
        max_negative: Max number of negative examples
        include_negative: Whether to include negative examples
        
    Returns:
        Formatted prompt string or None if no cases
    """
    if not retrieved_cases:
        return None
    
    original_cases = original_cases or []
    
    # Separate positive and negative cases
    positive_cases: List[Dict[str, Any]] = []
    negative_cases: List[Dict[str, Any]] = []
    
    for case in retrieved_cases:
        line_index = case.get('line_index', -1)
        if 0 <= line_index < len(original_cases):
            reward = original_cases[line_index].get('reward', 1)  # Default to positive
            if reward == 1:
                positive_cases.append(case)
            elif include_negative:
                negative_cases.append(case)
        else:
            # If no reward info, assume positive
            positive_cases.append(case)
    
    # Build prompt parts
    prompt_parts: List[str] = []
    
    # Add positive examples
    if positive_cases:
        num_show = min(len(positive_cases), max_positive)
        prompt_parts.append(
            f"Similar previous conversations (showing {num_show} of {len(positive_cases)}):\n"
        )
        
        for i, case in enumerate(positive_cases[:max_positive], 1):
            user_msg = case.get('user_message', '')
            assistant_resp = case.get('assistant_response', '')
            prompt_parts.append(
                f"Example {i}:\n"
                f"User: {user_msg}\n"
                f"Assistant: {assistant_resp}\n"
            )
    
    # Add negative examples (optional)
    if include_negative and negative_cases:
        num_show = min(len(negative_cases), max_negative)
        prompt_parts.append(
            f"\nExamples to avoid (showing {num_show} of {len(negative_cases)}):\n"
        )
        
        for i, case in enumerate(negative_cases[:max_negative], 1):
            user_msg = case.get('user_message', '')
            assistant_resp = case.get('assistant_response', '')
            prompt_parts.append(
                f"Example {i}:\n"
                f"User: {user_msg}\n"
                f"Assistant: {assistant_resp}\n"
            )
    
    # Add instruction
    if positive_cases or negative_cases:
        if positive_cases and negative_cases:
            prompt_parts.append(
                "\nBased on the above examples, please respond to the current user message "
                "in a similar style and format as the positive examples, "
                "and avoid the patterns shown in the negative examples.\n\n"
            )
        elif positive_cases:
            prompt_parts.append(
                "\nBased on the above examples, please respond to the current user message "
                "in a similar style and format.\n\n"
            )
        elif negative_cases:
            prompt_parts.append(
                "\nPlease avoid the patterns shown in the above examples when responding "
                "to the current user message.\n\n"
            )
    
    return "\n".join(prompt_parts) if prompt_parts else None

