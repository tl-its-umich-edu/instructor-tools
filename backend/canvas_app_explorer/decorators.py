import asyncio
import logging
import time
from functools import wraps
from typing import Any, Callable

logger = logging.getLogger(__name__)


def log_execution_time(func: Callable) -> Callable:
    """
    Decorator that logs the execution time of both sync and async functions.
    Automatically detects the function type and handles accordingly.
    
    Args:
        func: The function to decorate (sync or async)
        
    Returns:
        Decorated function that logs execution time
    """
    if asyncio.iscoroutinefunction(func):
        @wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            start_time: float = time.perf_counter()
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                end_time: float = time.perf_counter()
                duration = end_time - start_time
                logger.info(f"{func.__name__} execution time: {duration:.2f} seconds")
        return async_wrapper
    else:
        @wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            start_time: float = time.perf_counter()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                end_time: float = time.perf_counter()
                duration = end_time - start_time
                logger.info(f"{func.__name__} execution time: {duration:.2f} seconds")
        return sync_wrapper
