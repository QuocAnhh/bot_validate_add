"""Prompt loader utility"""
from typing import Dict, Any, Optional
from pathlib import Path

from app.prompts.framework import PromptFramework


def load_prompt_template(
    template_name: str,
    variables: Optional[Dict[str, Any]] = None
) -> str:
    """
    Load prompt template by name and replace variables
    
    Args:
        template_name: Name of template file (without .txt extension)
        variables: Dictionary of variables to replace
        
    Returns:
        Final prompt with variables replaced
    """
    templates_dir = Path(__file__).parent / "templates"
    template_path = templates_dir / f"{template_name}.txt"
    
    if not template_path.exists():
        raise FileNotFoundError(f"Template not found: {template_name}")
    
    return PromptFramework.build_prompt(
        template_path=str(template_path),
        variables=variables or {}
    )


def build_prompt_from_config(agent_config: Dict[str, Any]) -> str:
    """
    Build prompt from agent configuration
    
    Args:
        agent_config: Agent configuration dictionary
        
    Returns:
        Final prompt string
    """
    # Extract variables from config
    agent_info = agent_config.get('agent', {})
    tools = agent_config.get('tools', [])
    memory_config = agent_config.get('memory', {})
    
    # Get template name (default to agent)
    template_name = agent_config.get('prompt_template', 'agent')
    
    # Build variables
    variables = {
        'AGENT': {
            'NAME': agent_info.get('name', 'Assistant'),
            'DESCRIPTION': agent_info.get('description', 'Trợ lý ảo'),
            'START_MESSAGE': agent_info.get('start_message', 'Xin chào!'),
            'END_MESSAGE': agent_info.get('end_message', 'Cảm ơn bạn!')
        },
        'tools_description': PromptFramework.format_tools_description(tools),
        'memory_instructions': PromptFramework.format_memory_instructions(memory_config)
    }
    
    # Load and build prompt
    return load_prompt_template(template_name, variables)


def get_template_path(template_name: str) -> Path:
    """
    Get path to template file
    
    Args:
        template_name: Name of template (without .txt)
        
    Returns:
        Path to template file
    """
    templates_dir = Path(__file__).parent / "templates"
    return templates_dir / f"{template_name}.txt"


def list_available_templates() -> list:
    """
    List all available prompt templates
    
    Returns:
        List of template names (without .txt extension)
    """
    templates_dir = Path(__file__).parent / "templates"
    
    if not templates_dir.exists():
        return []
    
    templates = []
    for template_file in templates_dir.glob("*.txt"):
        templates.append(template_file.stem)
    
    return templates

