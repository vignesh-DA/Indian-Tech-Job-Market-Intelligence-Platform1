import logging
import os
import sys
from datetime import datetime


class SafeStreamHandler(logging.StreamHandler):
    """Stream handler that avoids crashing on Unicode output in legacy consoles."""

    def emit(self, record):
        try:
            super().emit(record)
        except UnicodeEncodeError:
            try:
                msg = self.format(record)
                encoding = getattr(self.stream, 'encoding', None) or 'utf-8'
                safe_msg = msg.encode(encoding, errors='replace').decode(encoding, errors='replace')
                self.stream.write(safe_msg + self.terminator)
                self.flush()
            except Exception:
                self.handleError(record)

is_vercel = os.environ.get('VERCEL') == '1'
LOG_FILE = f"{datetime.now().strftime('%m_%d_%Y_%H_%M_%S')}.log"
logs_path = os.path.join("/tmp" if is_vercel else os.getcwd(), "logs")

try:
    os.makedirs(logs_path, exist_ok=True)
except OSError:
    pass

LOG_FILE_PATH = os.path.join(logs_path, LOG_FILE)

# Configure logging to output to BOTH file and console (stdout)
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

if hasattr(sys.stderr, 'reconfigure'):
    try:
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

handlers = [SafeStreamHandler(sys.stdout)]
if os.access(logs_path, os.W_OK):
    handlers.append(logging.FileHandler(LOG_FILE_PATH, encoding='utf-8'))

logging.basicConfig(
    level=logging.INFO,
    format="[ %(asctime)s ] %(lineno)d %(name)s - %(levelname)s - %(message)s",
    handlers=handlers
)

# Export logging for imports
__all__ = ['logging']
