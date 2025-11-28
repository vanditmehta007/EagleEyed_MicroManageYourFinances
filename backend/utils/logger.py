import logging
import sys
import json
import os
from typing import Optional, Dict, Any
from datetime import datetime

class StructuredFormatter(logging.Formatter):
    """
    Formatter to output logs in JSON format for structured logging.
    """
    def format(self, record: logging.LogRecord) -> str:
        log_record = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)
            
        # Add extra fields if passed in 'extra' dict
        if hasattr(record, "extra_data"):
            log_record.update(record.extra_data)
            
        return json.dumps(log_record)

def setup_logger(name: str = "eagle_eyed", log_level: str = "INFO", log_file: Optional[str] = None) -> logging.Logger:
    """
    Configures and returns a logger with structured JSON formatting.
    
    Args:
        name: Name of the logger.
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        log_file: Optional path to a log file.
        
    Returns:
        Configured Logger instance.
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    
    # Avoid adding duplicate handlers
    if logger.handlers:
        return logger

    # Create formatter
    formatter = StructuredFormatter()

    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File Handler (Optional)
    if log_file:
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(log_file), exist_ok=True)
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except Exception as e:
            print(f"Failed to setup file logging: {e}")

    return logger

# Initialize default logger
# Can be configured via environment variables
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = os.getenv("LOG_FILE", "logs/app.log")

logger = setup_logger("eagle_eyed", LOG_LEVEL, LOG_FILE)

def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get a child logger with the specified name.
    
    Args:
        name: Suffix for the logger name (e.g., 'worker', 'api').
        
    Returns:
        Logger instance.
    """
    if name:
        return setup_logger(f"eagle_eyed.{name}", LOG_LEVEL, LOG_FILE)
    return logger

def log_request(method: str, path: str, status_code: int, duration_ms: float, **kwargs):
    """
    Helper to log API requests structurally.
    """
    extra = {
        "type": "request",
        "method": method,
        "path": path,
        "status_code": status_code,
        "duration_ms": duration_ms
    }
    extra.update(kwargs)
    logger.info(f"API Request: {method} {path} {status_code}", extra={"extra_data": extra})

def log_task(task_name: str, status: str, **kwargs):
    """
    Helper to log background task execution.
    """
    extra = {
        "type": "task",
        "task": task_name,
        "status": status
    }
    extra.update(kwargs)
    logger.info(f"Task {task_name}: {status}", extra={"extra_data": extra})

def log_error(error: Exception, context: str = "", **kwargs):
    """
    Helper to log errors with context.
    """
    extra = {
        "type": "error",
        "context": context,
        "error_type": type(error).__name__
    }
    extra.update(kwargs)
    logger.error(f"Error in {context}: {str(error)}", exc_info=True, extra={"extra_data": extra})
