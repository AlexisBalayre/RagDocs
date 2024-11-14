"""
Logger Configuration Utility

This module provides a utility function to set up a logger with both file and console
handlers. The logger is designed for use in applications requiring detailed debugging
and runtime monitoring. It supports creating log files in a dedicated directory and
formats log messages for clarity.
"""

import logging
from pathlib import Path


def setup_logger(
    name: str = "rag_system", log_file: str = "rag_system.log"
) -> logging.Logger:
    """
    Configure a logger with both file and console handlers.

    Args:
        name (str): The name of the logger. Defaults to "rag_system".
        log_file (str): The name of the log file. Defaults to "rag_system.log".

    Returns:
        logging.Logger: Configured logger instance.
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    log_path = log_dir / log_file

    # File handler
    file_handler = logging.FileHandler(log_path)
    file_handler.setLevel(logging.DEBUG)
    file_format = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    file_handler.setFormatter(file_format)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_format = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    console_handler.setFormatter(console_format)

    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger
