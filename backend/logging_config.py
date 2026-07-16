"""Logging configuration for the application."""
import logging
import logging.handlers
import sys
from pathlib import Path

# Create logs directory if it doesn't exist
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

LOG_FILE = LOG_DIR / "app.log"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


def setup_logging():
    """Configure logging to output to both console and file."""
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    # Remove existing handlers to avoid duplicates
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Console handler (INFO level).
    # A Windows console is cp1252, and model output routinely contains characters
    # it cannot encode (narrow no-break spaces, em dashes). Without this, logging
    # such a line raises UnicodeEncodeError instead of printing it.
    stream = sys.stderr
    if hasattr(stream, "reconfigure"):
        stream.reconfigure(errors="backslashreplace")
    console_handler = logging.StreamHandler(stream)
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter(LOG_FORMAT)
    console_handler.setFormatter(console_formatter)

    # File handler (DEBUG level - more detailed). utf-8 for the same reason:
    # the default here is the locale encoding, which is also cp1252 on Windows.
    file_handler = logging.handlers.RotatingFileHandler(
        LOG_FILE,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,  # Keep 5 backup files
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(LOG_FORMAT)
    file_handler.setFormatter(file_formatter)

    # Add handlers to root logger
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

    logging.info(f"Logging configured. File: {LOG_FILE}")
