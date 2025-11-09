"""Logging configuration"""
import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Optional

from app.core.config import LOG_LEVEL


def setup_logging(
    log_level: Optional[str] = None,
    log_dir: Path = Path("logs")
):
    """
    Setup logging configuration
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        log_dir: Directory for log files
    """
    # Create logs directory if it doesn't exist
    log_dir.mkdir(exist_ok=True)
    
    # Get log level
    level = getattr(logging, (log_level or LOG_LEVEL).upper(), logging.INFO)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Remove existing handlers
    root_logger.handlers.clear()
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    simple_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(simple_formatter)
    root_logger.addHandler(console_handler)
    
    # File handlers
    # Main application log
    app_log_file = log_dir / "app.log"
    app_handler = RotatingFileHandler(
        app_log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5
    )
    app_handler.setLevel(level)
    app_handler.setFormatter(detailed_formatter)
    root_logger.addHandler(app_handler)
    
    # API log
    api_log_file = log_dir / "api.log"
    api_handler = RotatingFileHandler(
        api_log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5
    )
    api_handler.setLevel(logging.INFO)
    api_handler.setFormatter(detailed_formatter)
    
    api_logger = logging.getLogger("api")
    api_logger.addHandler(api_handler)
    api_logger.setLevel(logging.INFO)
    
    # Agent log
    agent_log_file = log_dir / "agent.log"
    agent_handler = RotatingFileHandler(
        agent_log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5
    )
    agent_handler.setLevel(logging.INFO)
    agent_handler.setFormatter(detailed_formatter)
    
    agent_logger = logging.getLogger("agent")
    agent_logger.addHandler(agent_handler)
    agent_logger.setLevel(logging.INFO)
    
    # Error log (attached to root logger, not separate logger)
    error_log_file = log_dir / "error.log"
    error_handler = RotatingFileHandler(
        error_log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(detailed_formatter)
    root_logger.addHandler(error_handler)
    
    logging.info("Logging configured successfully")
    logging.info(f"Log directory: {log_dir.absolute()}")
    logging.info(f"Log level: {logging.getLevelName(level)}")


# Setup logging on import (but allow override)
# Don't auto-setup to avoid issues during testing
# setup_logging()

