import logging
import time
from functools import wraps
from typing import Any, Callable

from backend import settings

logger = logging.getLogger(__name__)


def log_execution_time(func: Callable) -> Callable:
    """
    Decorator that logs the execution time of a function.
    
    Args:
        func: The function to decorate
        
    Returns:
        Decorated function that logs execution time
    """
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        start_time: float = time.perf_counter()
        try:
            result = func(*args, **kwargs)
            return result
        finally:
            end_time: float = time.perf_counter()
            duration = end_time - start_time
            logger.info(f"{func.__name__} execution time: {duration:.2f} seconds")
    
    return wrapper


def debugpy_django_q(func: Callable) -> Callable:
    """
    Decorator that enables debugpy debugging for django_q background tasks.
    
    Allows easy debugging of background tasks by setting environment variables:
    - DEBUGPY_ENABLE: Set to 'true' to enable debugging (default: false)
    - DEBUG_DJANGO_Q_PORT: Port for debugpy to listen on (required to enable django_q debugging)
    - DEBUGPY_DJANGO_Q_TIMEOUT: Timeout in seconds to wait for debugger attachment (default: 30)
    
    When enabled, the decorator will:
    1. Initialize debugpy on the configured port
    2. Wait up to the specified timeout for a debugger to attach
    3. Continue execution with or without a debugger after the timeout
    
    Usage:
        @debugpy_django_q
        def my_background_task(task_data):
            # Your task code here
            pass
    
    Args:
        func: The background task function to decorate
        
    Returns:
        Decorated function with debugpy debugging support
    """
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        # Check if debugging is enabled and django_q debug port is configured
        if settings.DEBUGPY_ENABLE and settings.DEBUG_DJANGO_Q_PORT:
            try:
                import debugpy
                
                logger.info(f"Enabling debugpy for task '{func.__name__}' on port {settings.DEBUG_DJANGO_Q_PORT}")
                
                # Listen for debugger connection
                debugpy.listen(('0.0.0.0', settings.DEBUG_DJANGO_Q_PORT))
                logger.info(f"debugpy listening on port {settings.DEBUG_DJANGO_Q_PORT}, waiting up to {settings.DEBUGPY_DJANGO_Q_TIMEOUT}s for debugger to attach...")
                
                # Wait for debugger to attach with timeout
                debugpy.wait_for_client(timeout=settings.DEBUGPY_DJANGO_Q_TIMEOUT)
                logger.info("Debugger attached, continuing task execution")
                
            except ImportError:
                logger.warning("debugpy not installed, skipping debug mode for django_q task")
            except Exception as e:
                logger.warning(f"Failed to initialize debugpy for django_q task '{func.__name__}': {e}")
                logger.info("Continuing task execution without debugger")
        
        # Execute the task
        return func(*args, **kwargs)
    
    return wrapper
