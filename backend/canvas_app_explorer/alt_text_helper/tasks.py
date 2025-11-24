import logging
import time

logger = logging.getLogger(__name__)

def simple_math_task():
    logger.info("Starting simple_math_task...")
    time.sleep(5) 
    
    a = 15
    b = 7
    result = a + b
    logger.info(f"Task complete. Result: {result}")

    # The return value is stored in the database by django-q2 upon completion.
    return {
        "status": "COMPLETED",
        "result": result,
        "details": "Hardcoded math task executed successfully.",
        "timestamp": time.time()
    }
