"""
Logging configuration for the sales analytics project.
"""
import logging
import sys
from pathlib import Path
from loguru import logger
import yaml

class InterceptHandler(logging.Handler):
    """Intercept standard logging messages toward Loguru."""
    
    def emit(self, record):
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno
            
        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1
            
        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())

def setup_logger(config_path: str = "config.yaml"):
    """
    Setup logger with configuration from config file.
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        Configured logger instance
    """
    # Load config
    config_file = Path(config_path)
    if not config_file.exists() and not config_file.is_absolute():
        # Fallback to project root if not found in current directory
        config_file = Path(__file__).resolve().parents[2] / config_path
        
    with open(config_file, 'r') as f:
        config = yaml.safe_load(f)
    
    log_config = config.get('logging', {})
    log_level = log_config.get('level', 'INFO')
    log_format = log_config.get('format', "{time:YYYY-MM-DD HH:mm:ss} - {name} - {level} - {message}")
    log_file = log_config.get('file', 'logs/sales_analytics.log')
    
    # Create logs directory if it doesn't exist
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Remove default handler
    logger.remove()
    
    # Add console handler
    logger.add(
        sys.stdout,
        format=log_format,
        level=log_level,
        colorize=True
    )
    
    # Add file handler with rotation
    logger.add(
        log_file,
        format=log_format,
        level=log_level,
        rotation="10 MB",
        retention="30 days",
        compression="zip"
    )
    
    # Intercept standard logging
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)
    
    return logger

# Create global logger instance
logger = setup_logger()