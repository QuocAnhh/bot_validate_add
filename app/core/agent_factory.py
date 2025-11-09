"""Agent factory for creating agents from config"""
import logging
from typing import Optional
from pathlib import Path

from app.core.config import load_agent_config
from app.core.agent_config import AgentConfig
from app.use_cases.base.simple_agent import SimpleAgent
from app.use_cases.base.base_agent import BaseAgent
from typing import Union

logger = logging.getLogger(__name__)


def create_agent(
    config_path: Optional[str] = None,
    config: Optional[AgentConfig] = None,
    use_tools: bool = False
) -> Union[SimpleAgent, BaseAgent]:
    """
    Create agent from config
    
    Args:
        config_path: Path to config file
        config: AgentConfig object (if already loaded)
        use_tools: Whether to use tools (if True, uses BaseAgent, else SimpleAgent)
        
    Returns:
        Agent instance (SimpleAgent or BaseAgent)
    """
    # Load config if not provided
    if not config:
        if not config_path:
            raise ValueError("Either config_path or config must be provided")
        
        config = load_agent_config(config_path)
    
    # Check if tools are configured
    has_tools = len(config.tools) > 0
    
    # If use_tools is False or no tools configured, use SimpleAgent
    if not use_tools or not has_tools:
        logger.info(f"Creating SimpleAgent for {config.agent.get('name', 'Unknown')}")
        return SimpleAgent(config)
    
    # Otherwise, use BaseAgent (requires implementation in use_cases)
    logger.info(f"Creating BaseAgent with tools for {config.agent.get('name', 'Unknown')}")
    
    # Try to import and create specific agent type
    # For now, fallback to SimpleAgent if specific agent not found
    try:
        # Try to find agent in use_cases
        agent_name = config.agent.get('name', '').lower().replace(' ', '_')
        agent_module_path = f"app.use_cases.{agent_name}.{agent_name}_agent"
        
        try:
            module = __import__(agent_module_path, fromlist=[f"{agent_name.title()}Agent"])
            agent_class = getattr(module, f"{agent_name.title()}Agent")
            return agent_class(config)
        except (ImportError, AttributeError):
            logger.warning(f"Specific agent not found, using BaseAgent")
            # For now, return SimpleAgent as BaseAgent requires more setup
            return SimpleAgent(config)
    except Exception as e:
        logger.warning(f"Error creating agent with tools: {e}, falling back to SimpleAgent")
        return SimpleAgent(config)

