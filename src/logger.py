import logging
import os
import sys
from datetime import datetime

LOG_FILE = f"{datetime.now().strftime('%m_%d_%Y_%H_%M_%S')}.log"
logs_path = os.path.join(os.getcwd(), "logs")
os.makedirs(logs_path, exist_ok=True)

LOG_FILE_PATH = os.path.join(logs_path, LOG_FILE)

# Configure logging to output to BOTH file and console (stdout)
# This is crucial for cloud platforms like Render to capture logs
logging.basicConfig(
    level=logging.INFO,
    format="[ %(asctime)s ] %(lineno)d %(name)s - %(levelname)s - %(message)s",
    handlers=[
        # File handler - saves to logs directory
        logging.FileHandler(LOG_FILE_PATH),
        # Stream handler - outputs to console (stdout) for Render
        logging.StreamHandler(sys.stdout)
    ]
)

# Export logging for imports
__all__ = ['logging']
