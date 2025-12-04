import logging
import logging.handlers
import os
from datetime import datetime

def setup_logging():
    """
    Set up logging configuration for the BallSpinner Controller application.
    Creates separate log files for info and debug levels.
    """
    
    # Create logs directory if it doesn't exist
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Get current timestamp for log file naming
    timestamp = datetime.now().strftime("%Y%m%d")
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)  # Set to lowest level to capture everything
    
    # Clear any existing handlers
    root_logger.handlers.clear()
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
    )
    simple_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # INFO Logger - for general application flow
    info_handler = logging.handlers.RotatingFileHandler(
        filename=os.path.join(log_dir, f'ballspinner_info_{timestamp}.log'),
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    info_handler.setLevel(logging.INFO)
    info_handler.setFormatter(simple_formatter)
    
    # DEBUG Logger - for detailed debugging information
    debug_handler = logging.handlers.RotatingFileHandler(
        filename=os.path.join(log_dir, f'ballspinner_debug_{timestamp}.log'),
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    debug_handler.setLevel(logging.DEBUG)
    debug_handler.setFormatter(detailed_formatter)
    
    # Console handler for immediate feedback
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(simple_formatter)
    
    # Add handlers to root logger
    root_logger.addHandler(info_handler)
    root_logger.addHandler(debug_handler)
    # root_logger.addHandler(console_handler)
    
    return root_logger

def get_logger(name):
    """
    Get a logger instance for a specific module.
    
    Args:
        name (str): Usually __name__ from the calling module
        
    Returns:
        logging.Logger: Configured logger instance
    """
    return logging.getLogger(name)
