import os
import logging

def get_logger(name: str = "app"):
    logger = logging.getLogger(name)
    
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        
        log_format = logging.Formatter(
            "[%(asctime)s] %(levelname)s in %(module)s: %(message)s"
        )
        
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(log_format)
        logger.addHandler(console_handler)
        current_dir = os.path.dirname(os.path.abspath(__file__))
        logs_dir = os.path.abspath(os.path.join(current_dir, "..", "..", "logs"))
        
        os.makedirs(logs_dir, exist_ok=True)
        
        log_file_path = os.path.join(logs_dir, "app.log")
        file_handler = logging.FileHandler(log_file_path)
        file_handler.setFormatter(log_format)
        logger.addHandler(file_handler)
        
    return logger

log = get_logger()
