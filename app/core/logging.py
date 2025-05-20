import logging
import sys
from types import FrameType
from typing import cast

from loguru import logger

from app.core.config import get_settings


# Intercept standard logging messages toward loguru
class InterceptHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:  
        # Get corresponding Loguru level if it exists
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = str(record.levelno)

        # Find caller from where the logged message originated
        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:  
            frame = cast(FrameType, frame.f_back)
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level,
            record.getMessage(),
        )


def setup_logging() -> None:
    """Configure logging with loguru"""
    settings = get_settings()
    
    # Remove default handlers
    logging.root.handlers = [InterceptHandler()]
    logging.root.setLevel(settings.LOG_LEVEL)
    
    # Remove loguru default handler
    logger.remove()
    
    # Configure loguru with custom formatting
    log_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
        "<level>{message}</level>"
    )
    
    # Add stderr handler for interactive use
    logger.add(
        sys.stderr, 
        format=log_format, 
        level=settings.LOG_LEVEL,
        colorize=True,
    )
    
    # Add file handler for persistent logs
    logger.add(
        "logs/dependency_scanner.log",
        rotation="10 MB",
        retention="1 week",
        format=log_format,
        level=settings.LOG_LEVEL,
        colorize=False,
        backtrace=True,
        diagnose=True,
    )
    
    # Intercept standard lib events like uvicorn logs
    for _log in ["uvicorn", "uvicorn.access", "uvicorn.error", "fastapi"]:
        _logger = logging.getLogger(_log)
        _logger.handlers = [InterceptHandler()]
        _logger.propagate = False
        
    logger.info("Logging setup complete")