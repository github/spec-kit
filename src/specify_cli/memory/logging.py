"""
Memory system logging with graceful degradation support.

Provides structured logging that works even when external dependencies fail.
"""

import logging
import sys
from pathlib import Path
from typing import Optional


class MemoryLogger:
    """Logger for memory system operations with graceful degradation."""

    def __init__(self, name: str = "specify.memory", log_file: Optional[Path] = None):
        """Initialize memory logger.

        Args:
            name: Logger name
            log_file: Optional log file path
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)

        # Console handler (always works)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)

        # File handler (optional, may fail gracefully)
        if log_file:
            try:
                log_file.parent.mkdir(parents=True, exist_ok=True)
                file_handler = logging.FileHandler(log_file)
                file_handler.setLevel(logging.DEBUG)
                file_formatter = logging.Formatter(
                    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
                )
                file_handler.setFormatter(file_formatter)
                self.logger.addHandler(file_handler)
            except (IOError, OSError) as e:
                self.logger.warning(f"Could not create file logger: {e}")

    def warning_once(self, message: str, warning_key: str = "_shown_warnings") -> None:
        """Log a warning only once per session.

        Args:
            message: Warning message
            warning_key: Key for tracking shown warnings
        """
        if not hasattr(self, warning_key):
            setattr(self, warning_key, set())

        shown_warnings = getattr(self, warning_key)
        if warning_key not in shown_warnings:
            self.logger.warning(message)
            shown_warnings.add(warning_key)


# Global logger instance
_logger: Optional[MemoryLogger] = None


def get_logger(log_file: Optional[Path] = None) -> MemoryLogger:
    """Get or create global memory logger.

    Args:
        log_file: Optional log file path

    Returns:
        MemoryLogger instance
    """
    global _logger
    if _logger is None:
        _logger = MemoryLogger(log_file=log_file)
    return _logger
