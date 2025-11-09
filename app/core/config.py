"""Main configuration loader"""
import os
import yaml
from pathlib import Path
from typing import Optional, List
from dotenv import load_dotenv

from app.core.agent_config import AgentConfig

load_dotenv()

# Environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
PORT = int(os.getenv("PORT", "8000"))


def load_agent_config(config_path: str) -> AgentConfig:
    """
    Load agent configuration from YAML file
    
    Args:
        config_path: Path to YAML config file
        
    Returns:
        AgentConfig: Validated agent configuration
    """
    config_file = Path(config_path)
    
    if not config_file.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    
    with open(config_file, 'r', encoding='utf-8') as f:
        config_data = yaml.safe_load(f)
    
    # Override with environment variables if present
    if OPENAI_API_KEY:
        if 'model' not in config_data:
            config_data['model'] = {}
        if 'api_key' not in config_data['model']:
            config_data['model']['api_key'] = OPENAI_API_KEY
    
    # Validate and return
    return AgentConfig(**config_data)


def get_configs_directory() -> Path:
    """Get the configs directory path"""
    return Path(__file__).parent.parent.parent / "configs"


def list_available_agents() -> List[str]:
    """
    List all available agent configs
    
    Returns:
        List of agent names (config file names without .yaml)
    """
    configs_dir = get_configs_directory()
    agents = []
    
    if configs_dir.exists():
        for config_file in configs_dir.glob("*.yaml"):
            agents.append(config_file.stem)
    
    return agents
