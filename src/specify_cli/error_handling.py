#!/usr/bin/env python3
"""
Enhanced Error Handling for Domain Analysis Tool

Provides centralized error handling, logging, and user-friendly error messages
for the domain analysis workflow.
"""

import logging
import sys
import traceback
from pathlib import Path
from typing import Optional, Any, Dict, List
from dataclasses import dataclass
from enum import Enum


class ErrorSeverity(Enum):
    """Error severity levels for categorizing issues."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Categories of errors for better organization."""
    FILE_ACCESS = "file_access"
    DATA_PARSING = "data_parsing"
    CONFIGURATION = "configuration"
    VALIDATION = "validation"
    SYSTEM = "system"
    USER_INPUT = "user_input"


@dataclass
class DomainAnalysisError:
    """Structured error information for domain analysis operations."""
    category: ErrorCategory
    severity: ErrorSeverity
    message: str
    details: Optional[str] = None
    file_path: Optional[Path] = None
    suggestion: Optional[str] = None
    error_code: Optional[str] = None


class ErrorHandler:
    """Centralized error handling for domain analysis operations."""

    def __init__(self, log_level: str = "INFO", log_file: Optional[str] = None):
        self.errors: List[DomainAnalysisError] = []
        self.warnings: List[DomainAnalysisError] = []
        self.setup_logging(log_level, log_file)

    def setup_logging(self, log_level: str, log_file: Optional[str]):
        """Setup logging configuration."""
        level = getattr(logging, log_level.upper(), logging.INFO)

        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

        # Setup console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)

        # Setup logger
        self.logger = logging.getLogger('domain_analysis')
        self.logger.setLevel(level)
        self.logger.addHandler(console_handler)

        # Setup file handler if specified
        if log_file:
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)

    def handle_file_access_error(
        self,
        file_path: Path,
        operation: str,
        error: Exception
    ) -> DomainAnalysisError:
        """Handle file access related errors."""
        if isinstance(error, FileNotFoundError):
            error_info = DomainAnalysisError(
                category=ErrorCategory.FILE_ACCESS,
                severity=ErrorSeverity.ERROR,
                message=f"File not found: {file_path}",
                details=f"Could not {operation} file: {str(error)}",
                file_path=file_path,
                suggestion="Check that the file exists and the path is correct",
                error_code="FILE_NOT_FOUND"
            )
        elif isinstance(error, PermissionError):
            error_info = DomainAnalysisError(
                category=ErrorCategory.FILE_ACCESS,
                severity=ErrorSeverity.ERROR,
                message=f"Permission denied: {file_path}",
                details=f"Could not {operation} file: {str(error)}",
                file_path=file_path,
                suggestion="Check file permissions and ensure you have read/write access",
                error_code="PERMISSION_DENIED"
            )
        else:
            error_info = DomainAnalysisError(
                category=ErrorCategory.FILE_ACCESS,
                severity=ErrorSeverity.ERROR,
                message=f"File access error: {file_path}",
                details=f"Could not {operation} file: {str(error)}",
                file_path=file_path,
                suggestion="Check file path and permissions",
                error_code="FILE_ACCESS_ERROR"
            )

        self.errors.append(error_info)
        self.logger.error(self._format_error_message(error_info))
        return error_info

    def handle_data_parsing_error(
        self,
        file_path: Path,
        data_format: str,
        error: Exception
    ) -> DomainAnalysisError:
        """Handle data parsing related errors."""
        if "json" in data_format.lower():
            import json
            if isinstance(error, json.JSONDecodeError):
                error_info = DomainAnalysisError(
                    category=ErrorCategory.DATA_PARSING,
                    severity=ErrorSeverity.WARNING,
                    message=f"Invalid JSON format: {file_path.name}",
                    details=f"JSON parsing error at line {error.lineno}, column {error.colno}: {error.msg}",
                    file_path=file_path,
                    suggestion="Validate JSON syntax using an online JSON validator",
                    error_code="INVALID_JSON"
                )
            else:
                error_info = DomainAnalysisError(
                    category=ErrorCategory.DATA_PARSING,
                    severity=ErrorSeverity.WARNING,
                    message=f"JSON processing error: {file_path.name}",
                    details=str(error),
                    file_path=file_path,
                    suggestion="Check JSON file structure and content",
                    error_code="JSON_PROCESSING_ERROR"
                )
        elif "csv" in data_format.lower():
            error_info = DomainAnalysisError(
                category=ErrorCategory.DATA_PARSING,
                severity=ErrorSeverity.WARNING,
                message=f"CSV parsing error: {file_path.name}",
                details=str(error),
                file_path=file_path,
                suggestion="Check CSV file format, headers, and encoding",
                error_code="CSV_PARSING_ERROR"
            )
        else:
            error_info = DomainAnalysisError(
                category=ErrorCategory.DATA_PARSING,
                severity=ErrorSeverity.WARNING,
                message=f"Data parsing error: {file_path.name}",
                details=str(error),
                file_path=file_path,
                suggestion="Check file format and data structure",
                error_code="DATA_PARSING_ERROR"
            )

        self.warnings.append(error_info)
        self.logger.warning(self._format_error_message(error_info))
        return error_info

    def handle_configuration_error(
        self,
        config_path: Optional[Path],
        error: Exception
    ) -> DomainAnalysisError:
        """Handle configuration related errors."""
        import yaml
        if isinstance(error, yaml.YAMLError):
            error_info = DomainAnalysisError(
                category=ErrorCategory.CONFIGURATION,
                severity=ErrorSeverity.ERROR,
                message="Invalid YAML configuration",
                details=f"YAML parsing error: {str(error)}",
                file_path=config_path,
                suggestion="Validate YAML syntax and check configuration structure",
                error_code="INVALID_YAML"
            )
        else:
            error_info = DomainAnalysisError(
                category=ErrorCategory.CONFIGURATION,
                severity=ErrorSeverity.ERROR,
                message="Configuration error",
                details=str(error),
                file_path=config_path,
                suggestion="Check configuration file format and required fields",
                error_code="CONFIG_ERROR"
            )

        self.errors.append(error_info)
        self.logger.error(self._format_error_message(error_info))
        return error_info

    def handle_validation_error(
        self,
        validation_type: str,
        message: str,
        details: Optional[str] = None
    ) -> DomainAnalysisError:
        """Handle data validation errors."""
        error_info = DomainAnalysisError(
            category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.WARNING,
            message=f"Validation error: {validation_type}",
            details=details or message,
            suggestion="Review data quality and ensure required fields are present",
            error_code="VALIDATION_ERROR"
        )

        self.warnings.append(error_info)
        self.logger.warning(self._format_error_message(error_info))
        return error_info

    def handle_user_input_error(
        self,
        input_type: str,
        error: Exception
    ) -> DomainAnalysisError:
        """Handle user input related errors."""
        error_info = DomainAnalysisError(
            category=ErrorCategory.USER_INPUT,
            severity=ErrorSeverity.ERROR,
            message=f"Invalid user input: {input_type}",
            details=str(error),
            suggestion="Please check your input and try again",
            error_code="INVALID_INPUT"
        )

        self.errors.append(error_info)
        self.logger.error(self._format_error_message(error_info))
        return error_info

    def handle_system_error(self, operation: str, error: Exception) -> DomainAnalysisError:
        """Handle system-level errors."""
        error_info = DomainAnalysisError(
            category=ErrorCategory.SYSTEM,
            severity=ErrorSeverity.CRITICAL,
            message=f"System error during {operation}",
            details=str(error),
            suggestion="This may be a system issue. Try restarting the operation",
            error_code="SYSTEM_ERROR"
        )

        self.errors.append(error_info)
        self.logger.critical(self._format_error_message(error_info))
        return error_info

    def _format_error_message(self, error: DomainAnalysisError) -> str:
        """Format error message for logging."""
        message = f"[{error.category.value.upper()}] {error.message}"
        if error.file_path:
            message += f" (file: {error.file_path})"
        if error.details:
            message += f" - {error.details}"
        return message

    def print_error_summary(self):
        """Print a summary of all errors and warnings."""
        if not self.errors and not self.warnings:
            print("No errors or warnings to report.")
            return

        print("\n" + "="*60)
        print("ERROR AND WARNING SUMMARY")
        print("="*60)

        if self.errors:
            print(f"\nERRORS ({len(self.errors)}):")
            for i, error in enumerate(self.errors, 1):
                print(f"\n{i}. {error.message}")
                if error.details:
                    print(f"   Details: {error.details}")
                if error.file_path:
                    print(f"   File: {error.file_path}")
                if error.suggestion:
                    print(f"   Suggestion: {error.suggestion}")

        if self.warnings:
            print(f"\nWARNINGS ({len(self.warnings)}):")
            for i, warning in enumerate(self.warnings, 1):
                print(f"\n{i}. {warning.message}")
                if warning.details:
                    print(f"   Details: {warning.details}")
                if warning.file_path:
                    print(f"   File: {warning.file_path}")
                if warning.suggestion:
                    print(f"   Suggestion: {warning.suggestion}")

        print("\n" + "="*60)

    def has_critical_errors(self) -> bool:
        """Check if there are any critical errors that should stop execution."""
        return any(error.severity == ErrorSeverity.CRITICAL for error in self.errors)

    def has_errors(self) -> bool:
        """Check if there are any errors."""
        return len(self.errors) > 0

    def has_warnings(self) -> bool:
        """Check if there are any warnings."""
        return len(self.warnings) > 0

    def get_error_count(self) -> Dict[str, int]:
        """Get count of errors by category."""
        counts = {category.value: 0 for category in ErrorCategory}

        for error in self.errors + self.warnings:
            counts[error.category.value] += 1

        return counts

    def clear_errors(self):
        """Clear all stored errors and warnings."""
        self.errors.clear()
        self.warnings.clear()


# Global error handler instance
_global_error_handler: Optional[ErrorHandler] = None


def get_error_handler() -> ErrorHandler:
    """Get the global error handler instance."""
    global _global_error_handler
    if _global_error_handler is None:
        _global_error_handler = ErrorHandler()
    return _global_error_handler


def setup_error_handling(log_level: str = "INFO", log_file: Optional[str] = None):
    """Setup global error handling configuration."""
    global _global_error_handler
    _global_error_handler = ErrorHandler(log_level, log_file)


# Convenience functions for common error handling patterns
def safe_file_operation(operation_name: str, file_path: Path, operation_func, *args, **kwargs):
    """Safely execute a file operation with error handling."""
    error_handler = get_error_handler()
    try:
        return operation_func(*args, **kwargs)
    except (FileNotFoundError, PermissionError, OSError) as e:
        error_handler.handle_file_access_error(file_path, operation_name, e)
        return None
    except Exception as e:
        error_handler.handle_system_error(f"{operation_name} on {file_path}", e)
        return None


def safe_data_parsing(file_path: Path, data_format: str, parse_func, *args, **kwargs):
    """Safely parse data with error handling."""
    error_handler = get_error_handler()
    try:
        return parse_func(*args, **kwargs)
    except (ValueError, TypeError) as e:
        error_handler.handle_data_parsing_error(file_path, data_format, e)
        return None
    except Exception as e:
        error_handler.handle_system_error(f"parsing {data_format} file {file_path}", e)
        return None


def safe_user_input(input_type: str, input_func, validation_func=None, *args, **kwargs):
    """Safely handle user input with validation."""
    error_handler = get_error_handler()
    try:
        user_input = input_func(*args, **kwargs)
        if validation_func and not validation_func(user_input):
            raise ValueError(f"Invalid {input_type}: {user_input}")
        return user_input
    except (ValueError, TypeError) as e:
        error_handler.handle_user_input_error(input_type, e)
        return None
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        sys.exit(0)
    except Exception as e:
        error_handler.handle_system_error(f"processing user input for {input_type}", e)
        return None