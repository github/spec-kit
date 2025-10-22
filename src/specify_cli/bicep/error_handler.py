"""
Comprehensive error handling and logging system for Bicep generation.

This module provides structured error handling, recovery mechanisms,
user-friendly error messages, and detailed logging capabilities.
"""

import asyncio
import logging
import traceback
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any, Type, Union, Callable
import json
from dataclasses import dataclass, field
from enum import Enum
import functools
import os

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.logging import RichHandler


class ErrorSeverity(str, Enum):
    """Error severity levels."""
    
    CRITICAL = "critical"      # System cannot continue
    ERROR = "error"           # Operation failed but system can continue
    WARNING = "warning"       # Potential problem, operation succeeded
    INFO = "info"            # Informational message
    DEBUG = "debug"          # Debug information


class ErrorCategory(str, Enum):
    """Error categories for classification."""
    
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    NETWORK = "network"
    VALIDATION = "validation"
    CONFIGURATION = "configuration"
    RESOURCE_NOT_FOUND = "resource_not_found"
    RATE_LIMIT = "rate_limit"
    QUOTA_EXCEEDED = "quota_exceeded"
    TEMPLATE_PARSING = "template_parsing"
    AZURE_API = "azure_api"
    FILE_SYSTEM = "file_system"
    USER_INPUT = "user_input"
    INTERNAL = "internal"


@dataclass
class ErrorContext:
    """Context information for error tracking."""
    
    operation: str
    component: str
    resource_name: Optional[str] = None
    template_path: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    correlation_id: Optional[str] = None
    
    # Additional context data
    parameters: Dict[str, Any] = field(default_factory=dict)
    state: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BicepError:
    """Structured error information."""
    
    id: str
    message: str
    severity: ErrorSeverity
    category: ErrorCategory
    
    # Context
    context: ErrorContext
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Technical details
    exception_type: Optional[str] = None
    stack_trace: Optional[str] = None
    inner_error: Optional['BicepError'] = None
    
    # User guidance
    user_message: str = ""
    suggested_actions: List[str] = field(default_factory=list)
    documentation_links: List[str] = field(default_factory=list)
    
    # Recovery information
    is_recoverable: bool = False
    retry_after_seconds: Optional[int] = None
    recovery_actions: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary for logging/serialization."""
        
        error_dict = {
            'id': self.id,
            'message': self.message,
            'severity': self.severity.value,
            'category': self.category.value,
            'timestamp': self.timestamp.isoformat(),
            'user_message': self.user_message,
            'is_recoverable': self.is_recoverable,
            'context': {
                'operation': self.context.operation,
                'component': self.context.component,
                'resource_name': self.context.resource_name,
                'template_path': self.context.template_path,
                'parameters': self.context.parameters,
                'state': self.context.state
            }
        }
        
        if self.exception_type:
            error_dict['exception_type'] = self.exception_type
        
        if self.suggested_actions:
            error_dict['suggested_actions'] = self.suggested_actions
        
        if self.recovery_actions:
            error_dict['recovery_actions'] = self.recovery_actions
        
        if self.inner_error:
            error_dict['inner_error'] = self.inner_error.to_dict()
        
        return error_dict


class BicepErrorHandler:
    """
    Centralized error handling for Bicep generation system.
    
    Provides structured error handling, recovery mechanisms, and
    user-friendly error reporting with detailed logging.
    """
    
    def __init__(self, log_level: str = "INFO", log_file: Optional[Path] = None):
        self.console = Console(stderr=True)
        
        # Initialize logging
        self._setup_logging(log_level, log_file)
        
        # Error tracking
        self.errors: List[BicepError] = []
        self.error_counts: Dict[str, int] = {}
        
        # Recovery handlers
        self.recovery_handlers: Dict[ErrorCategory, List[Callable]] = {}
        
        # User message templates
        self.user_message_templates = self._initialize_user_messages()
        
        # Documentation links
        self.documentation_links = self._initialize_documentation_links()
        
        # Initialize recovery handlers
        self._initialize_recovery_handlers()
    
    def _setup_logging(self, log_level: str, log_file: Optional[Path]):
        """Set up comprehensive logging system."""
        
        # Create logger
        self.logger = logging.getLogger('bicep_generator')
        self.logger.setLevel(getattr(logging, log_level.upper()))
        
        # Remove existing handlers to avoid duplicates
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        # Rich console handler for user-friendly output
        console_handler = RichHandler(
            console=Console(stderr=True),
            show_time=True,
            show_path=False,
            markup=True,
            rich_tracebacks=True,
            tracebacks_show_locals=False
        )
        console_handler.setLevel(logging.INFO)
        
        console_formatter = logging.Formatter(
            fmt="%(message)s",
            datefmt="[%X]"
        )
        console_handler.setFormatter(console_formatter)
        
        self.logger.addHandler(console_handler)
        
        # File handler for detailed logging
        if log_file:
            log_file.parent.mkdir(parents=True, exist_ok=True)
            
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(logging.DEBUG)
            
            file_formatter = logging.Formatter(
                fmt='%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            file_handler.setFormatter(file_formatter)
            
            self.logger.addHandler(file_handler)
        
        # Also create a structured JSON logger for error analysis
        if log_file:
            json_log_file = log_file.with_suffix('.json')
            json_handler = logging.FileHandler(json_log_file, encoding='utf-8')
            json_handler.setLevel(logging.ERROR)
            json_handler.setFormatter(JsonFormatter())
            
            self.logger.addHandler(json_handler)
    
    def handle_error(
        self,
        exception: Exception,
        context: ErrorContext,
        user_message: Optional[str] = None,
        suggested_actions: Optional[List[str]] = None,
        is_recoverable: bool = False
    ) -> BicepError:
        """
        Handle an error with full context and recovery options.
        
        Args:
            exception: The exception that occurred
            context: Context information for the error
            user_message: User-friendly error message
            suggested_actions: List of suggested actions for the user
            is_recoverable: Whether the error is recoverable
            
        Returns:
            Structured error information
        """
        
        # Classify the error
        category = self._classify_error(exception)
        severity = self._determine_severity(exception, category)
        
        # Generate error ID
        error_id = self._generate_error_id(category, context)
        
        # Create structured error
        error = BicepError(
            id=error_id,
            message=str(exception),
            severity=severity,
            category=category,
            context=context,
            exception_type=exception.__class__.__name__,
            stack_trace=traceback.format_exc(),
            user_message=user_message or self._generate_user_message(exception, category),
            suggested_actions=suggested_actions or self._get_suggested_actions(category),
            documentation_links=self._get_documentation_links(category),
            is_recoverable=is_recoverable or self._is_error_recoverable(category),
            recovery_actions=self._get_recovery_actions(category)
        )
        
        # Store error
        self.errors.append(error)
        self.error_counts[category.value] = self.error_counts.get(category.value, 0) + 1
        
        # Log error
        self._log_error(error)
        
        # Attempt recovery if possible
        if error.is_recoverable:
            self._attempt_recovery(error)
        
        return error
    
    def display_error(self, error: BicepError, show_technical_details: bool = False):
        """Display user-friendly error information."""
        
        # Determine color based on severity
        severity_colors = {
            ErrorSeverity.CRITICAL: "red",
            ErrorSeverity.ERROR: "red",
            ErrorSeverity.WARNING: "yellow",
            ErrorSeverity.INFO: "blue",
            ErrorSeverity.DEBUG: "dim"
        }
        
        color = severity_colors.get(error.severity, "red")
        
        # Create error panel content
        panel_content = f"[bold {color}]{error.severity.value.upper()}:[/bold {color}] {error.user_message}\n"
        
        if error.suggested_actions:
            panel_content += f"\n[bold]Suggested Actions:[/bold]\n"
            for action in error.suggested_actions:
                panel_content += f"  • {action}\n"
        
        if error.is_recoverable and error.recovery_actions:
            panel_content += f"\n[bold green]Recovery Options:[/bold green]\n"
            for action in error.recovery_actions:
                panel_content += f"  ↻ {action}\n"
        
        if error.documentation_links:
            panel_content += f"\n[bold blue]Documentation:[/bold blue]\n"
            for link in error.documentation_links:
                panel_content += f"  🔗 {link}\n"
        
        # Show technical details if requested
        if show_technical_details:
            panel_content += f"\n[dim]Error ID: {error.id}[/dim]\n"
            panel_content += f"[dim]Category: {error.category.value}[/dim]\n"
            panel_content += f"[dim]Component: {error.context.component}[/dim]\n"
            panel_content += f"[dim]Operation: {error.context.operation}[/dim]\n"
            
            if error.exception_type:
                panel_content += f"[dim]Exception: {error.exception_type}[/dim]\n"
        
        self.console.print(Panel(
            panel_content.rstrip(),
            title=f"Error: {error.context.operation}",
            border_style=color
        ))
    
    def _classify_error(self, exception: Exception) -> ErrorCategory:
        """Classify error into appropriate category."""
        
        exception_name = exception.__class__.__name__
        message = str(exception).lower()
        
        # Authentication/Authorization errors
        if any(term in message for term in ['authentication', 'unauthorized', 'forbidden', 'access denied']):
            return ErrorCategory.AUTHORIZATION if 'forbidden' in message else ErrorCategory.AUTHENTICATION
        
        # Network errors
        if any(term in message for term in ['connection', 'timeout', 'network', 'dns', 'ssl']):
            return ErrorCategory.NETWORK
        
        # Rate limiting
        if any(term in message for term in ['rate limit', 'throttled', 'too many requests']):
            return ErrorCategory.RATE_LIMIT
        
        # Quota errors
        if any(term in message for term in ['quota', 'limit exceeded', 'insufficient']):
            return ErrorCategory.QUOTA_EXCEEDED
        
        # Validation errors
        if any(term in message for term in ['validation', 'invalid', 'malformed', 'schema']):
            return ErrorCategory.VALIDATION
        
        # File system errors
        if exception_name in ['FileNotFoundError', 'PermissionError', 'OSError']:
            return ErrorCategory.FILE_SYSTEM
        
        # Resource not found
        if any(term in message for term in ['not found', 'does not exist', '404']):
            return ErrorCategory.RESOURCE_NOT_FOUND
        
        # Template parsing errors
        if any(term in message for term in ['json', 'yaml', 'bicep', 'parse', 'syntax']):
            return ErrorCategory.TEMPLATE_PARSING
        
        # Azure API errors
        if any(term in message for term in ['azure', 'resource provider', 'subscription']):
            return ErrorCategory.AZURE_API
        
        # Configuration errors
        if any(term in message for term in ['configuration', 'config', 'setting']):
            return ErrorCategory.CONFIGURATION
        
        # User input errors
        if exception_name in ['ValueError', 'TypeError'] and 'input' in message:
            return ErrorCategory.USER_INPUT
        
        # Default to internal error
        return ErrorCategory.INTERNAL
    
    def _determine_severity(self, exception: Exception, category: ErrorCategory) -> ErrorSeverity:
        """Determine error severity based on exception and category."""
        
        # Critical errors that stop the system
        if category in [ErrorCategory.AUTHENTICATION, ErrorCategory.AUTHORIZATION]:
            return ErrorSeverity.CRITICAL
        
        if isinstance(exception, (SystemExit, KeyboardInterrupt)):
            return ErrorSeverity.CRITICAL
        
        # High severity errors
        if category in [ErrorCategory.AZURE_API, ErrorCategory.TEMPLATE_PARSING]:
            return ErrorSeverity.ERROR
        
        # Medium severity
        if category in [ErrorCategory.NETWORK, ErrorCategory.VALIDATION, ErrorCategory.FILE_SYSTEM]:
            return ErrorSeverity.ERROR
        
        # Lower severity
        if category in [ErrorCategory.RATE_LIMIT, ErrorCategory.QUOTA_EXCEEDED]:
            return ErrorSeverity.WARNING
        
        # Configuration issues
        if category == ErrorCategory.CONFIGURATION:
            return ErrorSeverity.WARNING
        
        # Default
        return ErrorSeverity.ERROR
    
    def _generate_error_id(self, category: ErrorCategory, context: ErrorContext) -> str:
        """Generate unique error identifier."""
        
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        component = context.component.replace(' ', '_').lower()
        operation = context.operation.replace(' ', '_').lower()
        
        return f"BGE_{category.value.upper()}_{component}_{operation}_{timestamp}"
    
    def _generate_user_message(self, exception: Exception, category: ErrorCategory) -> str:
        """Generate user-friendly error message."""
        
        templates = self.user_message_templates.get(category, {})
        
        # Try to find specific message template
        exception_name = exception.__class__.__name__
        if exception_name in templates:
            return templates[exception_name].format(error=str(exception))
        
        # Use category default
        if 'default' in templates:
            return templates['default'].format(error=str(exception))
        
        # Fallback to generic message
        return f"An error occurred during the operation: {str(exception)}"
    
    def _get_suggested_actions(self, category: ErrorCategory) -> List[str]:
        """Get suggested actions for error category."""
        
        action_map = {
            ErrorCategory.AUTHENTICATION: [
                "Check Azure credentials and authentication",
                "Run 'az login' to authenticate with Azure",
                "Verify Azure subscription access"
            ],
            ErrorCategory.AUTHORIZATION: [
                "Verify Azure role assignments and permissions",
                "Check subscription and resource group access",
                "Contact your Azure administrator for access"
            ],
            ErrorCategory.NETWORK: [
                "Check internet connectivity",
                "Verify firewall and proxy settings",
                "Try again in a few minutes"
            ],
            ErrorCategory.RATE_LIMIT: [
                "Wait a few minutes and try again",
                "Reduce the frequency of requests",
                "Consider using batch operations"
            ],
            ErrorCategory.VALIDATION: [
                "Review template syntax and structure",
                "Check parameter values and types",
                "Validate against Azure resource schemas"
            ],
            ErrorCategory.FILE_SYSTEM: [
                "Check file and directory permissions",
                "Verify file paths exist and are accessible",
                "Ensure sufficient disk space"
            ],
            ErrorCategory.RESOURCE_NOT_FOUND: [
                "Verify resource names and identifiers",
                "Check Azure subscription and resource group",
                "Ensure resources exist in the specified region"
            ]
        }
        
        return action_map.get(category, [
            "Review the error details above",
            "Check the operation logs for more information",
            "Contact support if the issue persists"
        ])
    
    def _get_documentation_links(self, category: ErrorCategory) -> List[str]:
        """Get relevant documentation links for error category."""
        
        return self.documentation_links.get(category, [])
    
    def _is_error_recoverable(self, category: ErrorCategory) -> bool:
        """Determine if error category is typically recoverable."""
        
        recoverable_categories = {
            ErrorCategory.NETWORK,
            ErrorCategory.RATE_LIMIT,
            ErrorCategory.QUOTA_EXCEEDED,
            ErrorCategory.VALIDATION,
            ErrorCategory.CONFIGURATION
        }
        
        return category in recoverable_categories
    
    def _get_recovery_actions(self, category: ErrorCategory) -> List[str]:
        """Get recovery actions for error category."""
        
        recovery_map = {
            ErrorCategory.NETWORK: [
                "Retry with exponential backoff",
                "Switch to alternative endpoint if available"
            ],
            ErrorCategory.RATE_LIMIT: [
                "Wait for rate limit reset",
                "Implement request throttling"
            ],
            ErrorCategory.VALIDATION: [
                "Fix validation errors and retry",
                "Use template validation tools"
            ]
        }
        
        return recovery_map.get(category, [])
    
    def _log_error(self, error: BicepError):
        """Log error with appropriate level and format."""
        
        # Map severity to logging level
        log_level_map = {
            ErrorSeverity.CRITICAL: logging.CRITICAL,
            ErrorSeverity.ERROR: logging.ERROR,
            ErrorSeverity.WARNING: logging.WARNING,
            ErrorSeverity.INFO: logging.INFO,
            ErrorSeverity.DEBUG: logging.DEBUG
        }
        
        log_level = log_level_map.get(error.severity, logging.ERROR)
        
        # Create structured log message
        log_message = {
            'error_id': error.id,
            'category': error.category.value,
            'severity': error.severity.value,
            'message': error.message,
            'operation': error.context.operation,
            'component': error.context.component,
            'timestamp': error.timestamp.isoformat()
        }
        
        # Add optional context
        if error.context.resource_name:
            log_message['resource_name'] = error.context.resource_name
        
        if error.context.template_path:
            log_message['template_path'] = error.context.template_path
        
        # Log the structured message
        self.logger.log(log_level, json.dumps(log_message))
        
        # Also log stack trace at debug level
        if error.stack_trace:
            self.logger.debug(f"Stack trace for {error.id}:\\n{error.stack_trace}")
    
    def _attempt_recovery(self, error: BicepError):
        """Attempt automatic error recovery."""
        
        recovery_handlers = self.recovery_handlers.get(error.category, [])
        
        for handler in recovery_handlers:
            try:
                success = handler(error)
                if success:
                    self.logger.info(f"Successfully recovered from error {error.id}")
                    break
            except Exception as e:
                self.logger.warning(f"Recovery handler failed for {error.id}: {e}")
    
    def _initialize_user_messages(self) -> Dict[ErrorCategory, Dict[str, str]]:
        """Initialize user-friendly error message templates."""
        
        return {
            ErrorCategory.AUTHENTICATION: {
                'default': "Authentication failed. Please check your Azure credentials and try logging in again.",
                'AuthenticationError': "Unable to authenticate with Azure. Please run 'az login' to sign in."
            },
            ErrorCategory.AUTHORIZATION: {
                'default': "Access denied. You don't have sufficient permissions for this operation.",
                'ForbiddenError': "Access forbidden. Please check your Azure role assignments."
            },
            ErrorCategory.NETWORK: {
                'default': "Network connection failed. Please check your internet connection and try again.",
                'ConnectionError': "Unable to connect to Azure services. Please check your network connection.",
                'TimeoutError': "The operation timed out. Please try again or check your network connection."
            },
            ErrorCategory.VALIDATION: {
                'default': "Template validation failed. Please check your Bicep template for errors.",
                'ValidationError': "The template contains validation errors: {error}"
            },
            ErrorCategory.FILE_SYSTEM: {
                'default': "File system error occurred. Please check file permissions and paths.",
                'FileNotFoundError': "The specified file was not found: {error}",
                'PermissionError': "Permission denied accessing file: {error}"
            },
            ErrorCategory.RATE_LIMIT: {
                'default': "Rate limit exceeded. Please wait a moment and try again.",
                'RateLimitError': "Too many requests. Please wait {retry_after} seconds before retrying."
            }
        }
    
    def _initialize_documentation_links(self) -> Dict[ErrorCategory, List[str]]:
        """Initialize documentation links for each error category."""
        
        return {
            ErrorCategory.AUTHENTICATION: [
                "https://docs.microsoft.com/en-us/cli/azure/authenticate-azure-cli",
                "https://docs.microsoft.com/en-us/azure/active-directory/managed-identities-azure-resources/"
            ],
            ErrorCategory.AUTHORIZATION: [
                "https://docs.microsoft.com/en-us/azure/role-based-access-control/",
                "https://docs.microsoft.com/en-us/azure/azure-resource-manager/management/resource-providers-and-types"
            ],
            ErrorCategory.VALIDATION: [
                "https://docs.microsoft.com/en-us/azure/azure-resource-manager/bicep/",
                "https://docs.microsoft.com/en-us/azure/azure-resource-manager/templates/template-syntax"
            ],
            ErrorCategory.AZURE_API: [
                "https://docs.microsoft.com/en-us/rest/api/azure/",
                "https://docs.microsoft.com/en-us/azure/azure-resource-manager/management/azure-services-resource-providers"
            ]
        }
    
    def _initialize_recovery_handlers(self):
        """Initialize automatic recovery handlers."""
        
        def retry_with_backoff(error: BicepError) -> bool:
            """Generic retry handler with exponential backoff."""
            # This would implement actual retry logic
            return False
        
        def refresh_credentials(error: BicepError) -> bool:
            """Attempt to refresh Azure credentials."""
            # This would implement credential refresh logic
            return False
        
        # Register recovery handlers
        self.recovery_handlers[ErrorCategory.NETWORK] = [retry_with_backoff]
        self.recovery_handlers[ErrorCategory.RATE_LIMIT] = [retry_with_backoff]
        self.recovery_handlers[ErrorCategory.AUTHENTICATION] = [refresh_credentials]
    
    def get_error_summary(self) -> Dict[str, Any]:
        """Get summary of all errors encountered."""
        
        summary = {
            'total_errors': len(self.errors),
            'error_counts_by_category': self.error_counts.copy(),
            'error_counts_by_severity': {},
            'recent_errors': []
        }
        
        # Count by severity
        for error in self.errors:
            severity = error.severity.value
            summary['error_counts_by_severity'][severity] = summary['error_counts_by_severity'].get(severity, 0) + 1
        
        # Get recent errors (last 10)
        recent_errors = self.errors[-10:] if self.errors else []
        summary['recent_errors'] = [
            {
                'id': error.id,
                'severity': error.severity.value,
                'category': error.category.value,
                'message': error.user_message,
                'timestamp': error.timestamp.isoformat()
            }
            for error in recent_errors
        ]
        
        return summary
    
    def clear_errors(self):
        """Clear error history."""
        self.errors.clear()
        self.error_counts.clear()


class JsonFormatter(logging.Formatter):
    """JSON formatter for structured logging."""
    
    def format(self, record):
        log_entry = {
            'timestamp': self.formatTime(record),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
        
        return json.dumps(log_entry)


def error_handler(
    category: Optional[ErrorCategory] = None,
    user_message: Optional[str] = None,
    is_recoverable: bool = False,
    suggested_actions: Optional[List[str]] = None
):
    """
    Decorator for automatic error handling.
    
    Usage:
        @error_handler(category=ErrorCategory.VALIDATION, user_message="Template validation failed")
        def validate_template(template):
            # Function implementation
            pass
    """
    
    def decorator(func):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                # Get error handler instance (assuming it's available globally or via DI)
                handler = getattr(func, '_error_handler', None) or BicepErrorHandler()
                
                context = ErrorContext(
                    operation=func.__name__,
                    component=func.__module__,
                    parameters={'args': str(args), 'kwargs': str(kwargs)}
                )
                
                error = handler.handle_error(
                    exception=e,
                    context=context,
                    user_message=user_message,
                    suggested_actions=suggested_actions,
                    is_recoverable=is_recoverable
                )
                
                # Re-raise if critical
                if error.severity == ErrorSeverity.CRITICAL:
                    raise
                
                return None
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # Same logic as async wrapper
                handler = getattr(func, '_error_handler', None) or BicepErrorHandler()
                
                context = ErrorContext(
                    operation=func.__name__,
                    component=func.__module__,
                    parameters={'args': str(args), 'kwargs': str(kwargs)}
                )
                
                error = handler.handle_error(
                    exception=e,
                    context=context,
                    user_message=user_message,
                    suggested_actions=suggested_actions,
                    is_recoverable=is_recoverable
                )
                
                if error.severity == ErrorSeverity.CRITICAL:
                    raise
                
                return None
        
        # Return appropriate wrapper based on function type
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    
    return decorator


# Global error handler instance
_global_error_handler: Optional[BicepErrorHandler] = None


def get_error_handler() -> BicepErrorHandler:
    """Get global error handler instance."""
    global _global_error_handler
    
    if _global_error_handler is None:
        # Initialize with default configuration
        log_dir = Path.home() / '.specify_cli' / 'logs'
        log_file = log_dir / f'bicep_generator_{datetime.now().strftime("%Y%m%d")}.log'
        _global_error_handler = BicepErrorHandler(log_file=log_file)
    
    return _global_error_handler


def set_error_handler(handler: BicepErrorHandler):
    """Set global error handler instance."""
    global _global_error_handler
    _global_error_handler = handler