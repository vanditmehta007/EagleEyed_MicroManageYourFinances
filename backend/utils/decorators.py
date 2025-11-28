import time
import functools
import logging
import asyncio
from typing import Callable, Any, Type, Union, Tuple

# Use the centralized logger
from backend.utils.logger import logger

def time_execution(func: Callable) -> Callable:
    """
    Decorator to measure and log the execution time of a function.
    Supports both synchronous and asynchronous functions.
    """
    @functools.wraps(func)
    def sync_wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            return result
        finally:
            duration = (time.time() - start_time) * 1000
            logger.info(f"Function '{func.__name__}' executed in {duration:.2f} ms")

    @functools.wraps(func)
    async def async_wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            return result
        finally:
            duration = (time.time() - start_time) * 1000
            logger.info(f"Function '{func.__name__}' executed in {duration:.2f} ms")

    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    return sync_wrapper

def retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,)
) -> Callable:
    """
    Decorator to retry a function call upon failure.
    
    Args:
        max_attempts: Maximum number of attempts.
        delay: Initial delay between retries in seconds.
        backoff: Multiplier for delay after each failure.
        exceptions: Tuple of exception types to catch and retry.
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            current_delay = delay
            last_exception = None
            
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt == max_attempts:
                        logger.error(f"Function '{func.__name__}' failed after {max_attempts} attempts: {e}")
                        raise last_exception
                    
                    logger.warning(f"Attempt {attempt}/{max_attempts} for '{func.__name__}' failed: {e}. Retrying in {current_delay}s...")
                    time.sleep(current_delay)
                    current_delay *= backoff
            
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            current_delay = delay
            last_exception = None
            
            for attempt in range(1, max_attempts + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt == max_attempts:
                        logger.error(f"Function '{func.__name__}' failed after {max_attempts} attempts: {e}")
                        raise last_exception
                    
                    logger.warning(f"Attempt {attempt}/{max_attempts} for '{func.__name__}' failed: {e}. Retrying in {current_delay}s...")
                    await asyncio.sleep(current_delay)
                    current_delay *= backoff

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    return decorator

def log_call(func: Callable) -> Callable:
    """
    Decorator to log function entry and exit with arguments and return value.
    Use carefully with sensitive data.
    """
    @functools.wraps(func)
    def sync_wrapper(*args, **kwargs):
        logger.debug(f"Calling '{func.__name__}' with args={args} kwargs={kwargs}")
        try:
            result = func(*args, **kwargs)
            logger.debug(f"'{func.__name__}' returned: {result}")
            return result
        except Exception as e:
            logger.error(f"'{func.__name__}' raised exception: {e}")
            raise

    @functools.wraps(func)
    async def async_wrapper(*args, **kwargs):
        logger.debug(f"Calling '{func.__name__}' with args={args} kwargs={kwargs}")
        try:
            result = await func(*args, **kwargs)
            logger.debug(f"'{func.__name__}' returned: {result}")
            return result
        except Exception as e:
            logger.error(f"'{func.__name__}' raised exception: {e}")
            raise

    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    return sync_wrapper

def safe_execution(default_return: Any = None) -> Callable:
    """
    Decorator to wrap a function in a try-except block and return a default value on failure.
    Prevents the application from crashing due to unhandled exceptions in the wrapped function.
    
    Args:
        default_return: The value to return if an exception occurs.
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.error(f"Exception in '{func.__name__}': {e}", exc_info=True)
                return default_return

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                logger.error(f"Exception in '{func.__name__}': {e}", exc_info=True)
                return default_return

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    return decorator
