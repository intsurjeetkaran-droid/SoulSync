"""
SoulSync AI - Logging Configuration Module

This module provides centralized logging configuration for the entire application.
It sets up structured logging with appropriate formatters, handlers, and log levels.

Usage:
    from backend.utils.logging_config import setup_logging
    setup_logging()
    
    logger = logging.getLogger("soulsync.your_module")
    logger.info("Your log message")
"""

import logging
import logging.handlers
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional


class ColoredFormatter(logging.Formatter):
    """
    Custom formatter that adds colors to log levels for better readability
    in terminal output.
    
    Colors:
        - CRITICAL: Red background
        - ERROR: Red
        - WARNING: Yellow
        - INFO: Green
        - DEBUG: Cyan
    """
    
    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[41m',   # Red background
        'RESET': '\033[0m',       # Reset
    }
    
    def __init__(self, fmt: Optional[str] = None, datefmt: Optional[str] = None):
        super().__init__(fmt, datefmt)
    
    def format(self, record: logging.LogRecord) -> str:
        """Format the log record with colors."""
        log_color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        record.levelname = f"{log_color}{record.levelname}{self.COLORS['RESET']}"
        return super().format(record)


class JSONFormatter(logging.Formatter):
    """
    JSON formatter for production logging.
    Useful for log aggregation systems like ELK stack or CloudWatch.
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        import json
        
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        # Add extra fields
        if hasattr(record, 'user_id'):
            log_data['user_id'] = record.user_id
        if hasattr(record, 'request_id'):
            log_data['request_id'] = record.request_id
            
        return json.dumps(log_data)


def setup_logging(
    log_level: str = None,
    log_format: str = None,
    log_file: str = None,
    enable_file_logging: bool = False
) -> None:
    """
    Configure logging for the SoulSync application.
    
    This function sets up logging with:
    - Console handler with colored output (for development)
    - Optional file handler with rotation (for production)
    - Configurable log level and format
    
    Args:
        log_level: Log level string (DEBUG, INFO, WARNING, ERROR, CRITICAL).
                   Defaults to INFO.
        log_format: Format type ('text' or 'json'). Defaults to 'text'.
        log_file: Path to log file. If None, logs to console only.
        enable_file_logging: Whether to enable file logging. Defaults to False.
    
    Example:
        >>> setup_logging(log_level="DEBUG", log_format="text")
        >>> logger = logging.getLogger("soulsync.chat")
        >>> logger.info("Chat module initialized")
    """
    # Get configuration from environment if not provided
    if log_level is None:
        log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
    if log_format is None:
        log_format = os.getenv('LOG_FORMAT', 'text').lower()
    if log_file is None:
        log_file = os.getenv('LOG_FILE', 'logs/soulsync.log')
    
    # Convert string log level to logging constant
    numeric_level = getattr(logging, log_level, logging.INFO)
    
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    
    # Clear existing handlers
    if root_logger.hasHandlers():
        root_logger.handlers.clear()
    
    # Create formatters
    text_formatter = ColoredFormatter(
        fmt='%(asctime)s | %(levelname)s | %(name)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    detailed_formatter = logging.Formatter(
        fmt='%(asctime)s | %(levelname)-8s | %(name)-30s | %(funcName)-20s | %(lineno)-4d | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    json_formatter = JSONFormatter()
    
    # Select formatter based on format type
    if log_format == 'json':
        console_formatter = json_formatter
        file_formatter = json_formatter
    else:
        console_formatter = text_formatter
        file_formatter = detailed_formatter
    
    # Console Handler - Always enabled
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # File Handler - Optional
    if enable_file_logging or os.getenv('ENABLE_FILE_LOGGING', 'false').lower() == 'true':
        # Create logs directory
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Rotating file handler (10MB per file, keep 5 backup files)
        file_handler = logging.handlers.RotatingFileHandler(
            filename=log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)
        
        # Log startup message
        root_logger.info(f"File logging enabled: {log_file}")
    
    # Log startup information
    root_logger.info("=" * 60)
    root_logger.info("SoulSync AI - Logging Initialized")
    root_logger.info(f"Log Level: {log_level}")
    root_logger.info(f"Log Format: {log_format}")
    root_logger.info(f"Python Version: {sys.version}")
    root_logger.info("=" * 60)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the specified name.
    
    This is a convenience function that ensures all loggers follow
    the same naming convention and configuration.
    
    Args:
        name: Logger name, typically in format "soulsync.module_name"
    
    Returns:
        Configured logger instance
    
    Example:
        >>> logger = get_logger("soulsync.chat")
        >>> logger.info("Processing user message", extra={"user_id": "user123"})
    """
    # Ensure logger name starts with soulsync
    if not name.startswith('soulsync'):
        name = f"soulsync.{name}"
    
    return logging.getLogger(name)


# Module-level logger for this module
logger = get_logger("utils.logging_config")


def log_function_call(func_name: str, module_name: str, args: dict = None):
    """
    Decorator helper to log function calls with arguments.
    
    Args:
        func_name: Name of the function being called
        module_name: Name of the module containing the function
        args: Dictionary of function arguments (exclude sensitive data)
    
    Example:
        >>> log_function_call("generate_response", "ai_service", 
        ...                   {"user_input": "Hello", "lang": "en"})
    """
    logger = get_logger(module_name)
    args_str = ", ".join(f"{k}={v!r}" for k, v in (args or {}).items())
    logger.debug(f"Calling {func_name}({args_str})")


def log_api_request(
    method: str,
    path: str,
    user_id: str = None,
    status_code: int = None,
    duration_ms: float = None
):
    """
    Log an API request with relevant metadata.
    
    Args:
        method: HTTP method (GET, POST, etc.)
        path: Request path
        user_id: User identifier (if authenticated)
        status_code: HTTP response status code
        duration_ms: Request duration in milliseconds
    """
    logger = get_logger("api")
    
    log_msg = f"{method} {path}"
    extra = {}
    
    if user_id:
        log_msg += f" user={user_id}"
        extra['user_id'] = user_id
    if status_code:
        extra['status_code'] = status_code
    if duration_ms:
        log_msg += f" duration={duration_ms:.2f}ms"
        extra['duration_ms'] = duration_ms
    
    if status_code and status_code >= 400:
        logger.warning(log_msg, extra=extra)
    else:
        logger.info(log_msg, extra=extra)