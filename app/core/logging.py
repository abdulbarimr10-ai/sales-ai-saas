import logging
import sys

def setup_logging():
    """Configure structured logging for the application."""
    logger = logging.getLogger("sales_ai")
    
    # If handlers exist, avoid adding them again (prevents duplicate logs in reloads)
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)

    formatter = logging.Formatter(
        '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
    )

    # Console Handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    ch.setFormatter(formatter)
    
    logger.addHandler(ch)
    
    return logger

logger = setup_logging()
