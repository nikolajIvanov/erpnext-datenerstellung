import logging
from pathlib import Path
from typing import Optional

from src.core.base_transaction import BaseConfig


class ProcessLogger:
    """Centralized logging configuration for all processes."""

    def __init__(self, config: BaseConfig):
        """Initialize process logger."""
        self.file_logger = self._setup_logger(
            'file_logger',
            config.get_log_file_path(),
            propagate=False
        )

        self.console_logger = self._setup_logger(
            'console_logger',
            console_output=True,
            propagate=False
        )

    @staticmethod
    def _setup_logger(
            name: str,
            file_path: Optional[Path] = None,
            console_output: bool = False,
            propagate: bool = True
    ) -> logging.Logger:
        """Set up a logger with file and/or console output."""
        logger = logging.getLogger(name)
        logger.setLevel(logging.INFO)
        logger.propagate = propagate
        logger.handlers.clear()

        formatter = logging.Formatter('%(message)s')

        if file_path:
            file_handler = logging.FileHandler(str(file_path))
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

        if console_output:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)

        return logger

    def log_info(self, message: str, console: bool = True, file: bool = True):
        """Log info message."""
        if console:
            self.console_logger.info(message)
        if file:
            self.file_logger.info(message)

    def log_error(self, message: str, console: bool = True, file: bool = True):
        """Log error message."""
        if console:
            self.console_logger.error(message)
        if file:
            self.file_logger.error(message)

    def log_warning(self, message: str, console: bool = True, file: bool = True):
        """Log warning message."""
        if console:
            self.console_logger.warning(message)
        if file:
            self.file_logger.warning(message)

    def log_api_error(self, endpoint: str, error_msg: str, payload_path: Optional[Path] = None):
        """Log API error with consistent format to both console and file."""
        if payload_path:
            error_log = f"Failed to upload {endpoint}: {error_msg} (Payload saved to {payload_path.name})"
        else:
            error_log = f"Failed to upload {endpoint}: {error_msg}"

        self.log_info(error_log, console=True, file=True)