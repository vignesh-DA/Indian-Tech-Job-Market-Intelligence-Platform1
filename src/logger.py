import logging
import os
import sys
from datetime import datetime

is_vercel = os.environ.get('VERCEL') == '1'
LOG_FILE = f"{datetime.now().strftime('%m_%d_%Y_%H_%M_%S')}.log"
logs_path = os.path.join("/tmp" if is_vercel else os.getcwd(), "logs")

try:
    os.makedirs(logs_path, exist_ok=True)
except OSError:
    pass

LOG_FILE_PATH = os.path.join(logs_path, LOG_FILE)

# Configure logging to output to BOTH file and console (stdout)
handlers = [logging.StreamHandler(sys.stdout)]
if os.access(logs_path, os.W_OK):
    handlers.append(logging.FileHandler(LOG_FILE_PATH))

logging.basicConfig(
    level=logging.INFO,
    format="[ %(asctime)s ] %(lineno)d %(name)s - %(levelname)s - %(message)s",
    handlers=handlers
)

# Export logging for imports
__all__ = ['logging']
