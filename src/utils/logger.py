"""
Logging configuration and setup.

This module provides centralized logging configuration for the application,
including formatters, handlers, and log levels.
"""

import logging
import sys
from pathlib import Path
from typing import Optional

from src.utils.config import settings


def setup_logging(
    log_level: Optional[str] = None,
    log_file: Optional[str] = None
) -> logging.Logger:
    """
    Set up logging configuration for the application.
    
    Args:
        log_level: Override log level (uses settings.LOG_LEVEL if not provided)
        log_file: Optional log file path
        
    Returns:
        Root logger instance
    """
    # Use provided log level or fall back to settings
    level = log_level or settings.LOG_LEVEL
    
    # Create logs directory if log file is specified
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Define log format
    log_format = (
        "%(asctime)s - %(name)s - %(levelname)s - "
        "%(filename)s:%(lineno)d - %(message)s"
    )
    
    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format=log_format,
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[]
    )
    
    # Get root logger
    logger = logging.getLogger()
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Console handler with color support
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, level.upper()))
    
    # Add color formatter for console if in debug mode
    if settings.DEBUG:
        try:
            import colorlog
            color_formatter = colorlog.ColoredFormatter(
                "%(log_color)s" + log_format,
                datefmt="%Y-%m-%d %H:%M:%S",
                log_colors={
                    'DEBUG': 'cyan',
                    'INFO': 'green',
                    'WARNING': 'yellow',
                    'ERROR': 'red',
                    'CRITICAL': 'red,bg_white',
                }
            )
            console_handler.setFormatter(color_formatter)
        except ImportError:
            # Fall back to standard formatter
            console_handler.setFormatter(logging.Formatter(log_format))
    else:
        console_handler.setFormatter(logging.Formatter(log_format))
    
    logger.addHandler(console_handler)
    
    # File handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)  # Log everything to file
        file_handler.setFormatter(logging.Formatter(log_format))
        logger.addHandler(file_handler)
    
    # Set specific log levels for noisy libraries
    logging.getLogger("slack_bolt").setLevel(logging.INFO)
    logging.getLogger("slack_sdk").setLevel(logging.INFO)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    
    # Log initial setup
    logger.info(f"Logging configured with level: {level}")
    if log_file:
        logger.info(f"Logging to file: {log_file}")
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the specified name.
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)