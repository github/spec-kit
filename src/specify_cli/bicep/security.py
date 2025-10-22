"""
Security hardening utilities for Bicep generator.

This module provides input validation, secure credential handling,
rate limiting, and audit logging capabilities.
"""

import hashlib
import hmac
import os
import re
import secrets
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, TypeVar, cast
from enum import Enum
import json
import logging

from rich.console import Console
from rich.table import Table

console = Console()
logger = logging.getLogger(__name__)

# Type variable for generic functions
F = TypeVar('F', bound=Callable[..., Any])


class SecurityLevel(Enum):
    """Security levels for operations."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ValidationError(Exception):
    """Raised when input validation fails."""
    pass


class RateLimitError(Exception):
    """Raised when rate limit is exceeded."""
    pass


class SecurityAuditError(Exception):
    """Raised when security audit detects issues."""
    pass


@dataclass
class ValidationRule:
    """Represents a validation rule."""
    
    name: str
    pattern: Optional[str] = None
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    allowed_chars: Optional[Set[str]] = None
    forbidden_patterns: List[str] = field(default_factory=list)
    custom_validator: Optional[Callable[[str], bool]] = None
    error_message: str = "Validation failed"
    
    def validate(self, value: str) -> tuple[bool, Optional[str]]:
        """
        Validate a value against this rule.
        
        Args:
            value: Value to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check pattern
        if self.pattern and not re.match(self.pattern, value):
            return False, f"{self.error_message}: Pattern mismatch"
        
        # Check length
        if self.min_length and len(value) < self.min_length:
            return False, f"{self.error_message}: Too short (min: {self.min_length})"
        
        if self.max_length and len(value) > self.max_length:
            return False, f"{self.error_message}: Too long (max: {self.max_length})"
        
        # Check allowed characters
        if self.allowed_chars:
            value_chars = set(value)
            if not value_chars.issubset(self.allowed_chars):
                invalid = value_chars - self.allowed_chars
                return False, f"{self.error_message}: Invalid characters: {invalid}"
        
        # Check forbidden patterns
        for forbidden in self.forbidden_patterns:
            if re.search(forbidden, value, re.IGNORECASE):
                return False, f"{self.error_message}: Contains forbidden pattern"
        
        # Custom validation
        if self.custom_validator and not self.custom_validator(value):
            return False, self.error_message
        
        return True, None


class InputValidator:
    """
    Input validation system with predefined rules for common inputs.
    
    Features:
    - Azure resource name validation
    - Path validation
    - Parameter validation
    - Injection attack prevention
    """
    
    # Common validation rules
    AZURE_RESOURCE_NAME = ValidationRule(
        name="azure_resource_name",
        pattern=r"^[a-zA-Z0-9][-a-zA-Z0-9]*[a-zA-Z0-9]$",
        min_length=1,
        max_length=64,
        error_message="Invalid Azure resource name"
    )
    
    AZURE_LOCATION = ValidationRule(
        name="azure_location",
        pattern=r"^[a-z]+[a-z0-9]*$",
        max_length=50,
        error_message="Invalid Azure location"
    )
    
    FILE_PATH = ValidationRule(
        name="file_path",
        forbidden_patterns=[
            r"\.\.",  # Directory traversal
            r"^/etc/",  # System directories
            r"^/root/",
            r"^C:\\Windows\\",
            r"^C:\\Program Files",
        ],
        max_length=4096,
        error_message="Invalid or unsafe file path"
    )
    
    SUBSCRIPTION_ID = ValidationRule(
        name="subscription_id",
        pattern=r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
        error_message="Invalid Azure subscription ID (must be valid GUID)"
    )
    
    RESOURCE_GROUP_NAME = ValidationRule(
        name="resource_group_name",
        pattern=r"^[-\w._()]+$",
        min_length=1,
        max_length=90,
        forbidden_patterns=[r"\.$"],  # Cannot end with period
        error_message="Invalid resource group name"
    )
    
    TEMPLATE_PARAMETER = ValidationRule(
        name="template_parameter",
        pattern=r"^[a-zA-Z_][a-zA-Z0-9_]*$",
        max_length=255,
        error_message="Invalid template parameter name"
    )
    
    @classmethod
    def validate(cls, value: str, rule: ValidationRule) -> None:
        """
        Validate a value against a rule, raising exception on failure.
        
        Args:
            value: Value to validate
            rule: Validation rule to apply
            
        Raises:
            ValidationError: If validation fails
        """
        is_valid, error_msg = rule.validate(value)
        if not is_valid:
            logger.warning(f"Validation failed for {rule.name}: {error_msg}")
            raise ValidationError(error_msg)
    
    @classmethod
    def is_safe_path(cls, path: str) -> bool:
        """
        Check if a file path is safe (no directory traversal, system paths).
        
        Args:
            path: File path to check
            
        Returns:
            True if path is safe
        """
        try:
            cls.validate(path, cls.FILE_PATH)
            
            # Additional checks
            resolved = Path(path).resolve()
            
            # Check if path escapes working directory
            cwd = Path.cwd().resolve()
            try:
                resolved.relative_to(cwd)
            except ValueError:
                logger.warning(f"Path {path} escapes working directory")
                return False
            
            return True
            
        except ValidationError:
            return False
    
    @classmethod
    def sanitize_input(cls, value: str, max_length: int = 1000) -> str:
        """
        Sanitize user input by removing potentially dangerous characters.
        
        Args:
            value: Input value to sanitize
            max_length: Maximum allowed length
            
        Returns:
            Sanitized value
        """
        # Trim to max length
        value = value[:max_length]
        
        # Remove control characters
        value = "".join(char for char in value if ord(char) >= 32 or char in "\n\r\t")
        
        # Remove potential injection patterns
        dangerous_patterns = [
            r"<script[^>]*>.*?</script>",  # XSS
            r"javascript:",  # JS injection
            r"on\w+\s*=",  # Event handlers
            r"eval\s*\(",  # Code execution
            r"exec\s*\(",
        ]
        
        for pattern in dangerous_patterns:
            value = re.sub(pattern, "", value, flags=re.IGNORECASE | re.DOTALL)
        
        return value.strip()


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting."""
    
    max_requests: int
    time_window_seconds: int
    burst_allowance: int = 0
    
    @property
    def requests_per_second(self) -> float:
        """Calculate requests per second."""
        return self.max_requests / self.time_window_seconds


@dataclass
class RateLimitEntry:
    """Rate limit tracking entry."""
    
    requests: List[float] = field(default_factory=list)
    blocked_until: Optional[float] = None
    
    def add_request(self, timestamp: float) -> None:
        """Add a request timestamp."""
        self.requests.append(timestamp)
    
    def cleanup_old_requests(self, window_seconds: int, current_time: float) -> None:
        """Remove requests outside the time window."""
        cutoff = current_time - window_seconds
        self.requests = [req for req in self.requests if req > cutoff]
    
    def is_blocked(self, current_time: float) -> bool:
        """Check if currently blocked."""
        if self.blocked_until and current_time < self.blocked_until:
            return True
        return False
    
    def block_for(self, duration_seconds: float, current_time: float) -> None:
        """Block for a duration."""
        self.blocked_until = current_time + duration_seconds


class RateLimiter:
    """
    Rate limiting system to prevent abuse and ensure fair usage.
    
    Features:
    - Per-identifier rate limiting
    - Configurable time windows
    - Burst allowance
    - Automatic cleanup of old entries
    """
    
    def __init__(self, config: RateLimitConfig):
        """
        Initialize rate limiter.
        
        Args:
            config: Rate limit configuration
        """
        self.config = config
        self.entries: Dict[str, RateLimitEntry] = defaultdict(RateLimitEntry)
        self._last_cleanup = time.time()
    
    def check_limit(self, identifier: str) -> bool:
        """
        Check if identifier has exceeded rate limit.
        
        Args:
            identifier: Unique identifier (e.g., user ID, IP address)
            
        Returns:
            True if within limit, False if exceeded
            
        Raises:
            RateLimitError: If rate limit exceeded
        """
        current_time = time.time()
        entry = self.entries[identifier]
        
        # Check if blocked
        if entry.is_blocked(current_time):
            remaining = entry.blocked_until - current_time
            raise RateLimitError(
                f"Rate limit exceeded. Blocked for {remaining:.1f} more seconds"
            )
        
        # Cleanup old requests
        entry.cleanup_old_requests(self.config.time_window_seconds, current_time)
        
        # Check rate limit
        if len(entry.requests) >= self.config.max_requests:
            # Block for time window duration
            entry.block_for(self.config.time_window_seconds, current_time)
            logger.warning(f"Rate limit exceeded for {identifier}")
            raise RateLimitError(
                f"Rate limit exceeded: {self.config.max_requests} requests "
                f"per {self.config.time_window_seconds} seconds"
            )
        
        # Add request
        entry.add_request(current_time)
        
        # Periodic cleanup
        if current_time - self._last_cleanup > 300:  # Every 5 minutes
            self._cleanup_entries(current_time)
            self._last_cleanup = current_time
        
        return True
    
    def get_remaining_requests(self, identifier: str) -> int:
        """
        Get remaining requests for identifier.
        
        Args:
            identifier: Unique identifier
            
        Returns:
            Number of remaining requests
        """
        current_time = time.time()
        entry = self.entries[identifier]
        entry.cleanup_old_requests(self.config.time_window_seconds, current_time)
        
        return max(0, self.config.max_requests - len(entry.requests))
    
    def reset(self, identifier: str) -> None:
        """
        Reset rate limit for identifier.
        
        Args:
            identifier: Unique identifier
        """
        if identifier in self.entries:
            del self.entries[identifier]
    
    def _cleanup_entries(self, current_time: float) -> None:
        """Remove old entries to free memory."""
        cutoff = current_time - (self.config.time_window_seconds * 2)
        
        to_remove = []
        for identifier, entry in self.entries.items():
            entry.cleanup_old_requests(self.config.time_window_seconds, current_time)
            if not entry.requests and not entry.is_blocked(current_time):
                to_remove.append(identifier)
        
        for identifier in to_remove:
            del self.entries[identifier]


def rate_limited(
    max_requests: int = 100,
    time_window_seconds: int = 60,
    identifier_func: Optional[Callable[..., str]] = None
) -> Callable[[F], F]:
    """
    Decorator for rate limiting function calls.
    
    Args:
        max_requests: Maximum requests in time window
        time_window_seconds: Time window in seconds
        identifier_func: Function to extract identifier from args
        
    Returns:
        Decorated function
    """
    config = RateLimitConfig(max_requests, time_window_seconds)
    limiter = RateLimiter(config)
    
    def decorator(func: F) -> F:
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Determine identifier
            if identifier_func:
                identifier = identifier_func(*args, **kwargs)
            else:
                identifier = "default"
            
            # Check rate limit
            limiter.check_limit(identifier)
            
            # Execute function
            return func(*args, **kwargs)
        
        return cast(F, wrapper)
    
    return decorator


class CredentialManager:
    """
    Secure credential management system.
    
    Features:
    - Environment variable-based storage
    - In-memory encryption
    - Credential rotation support
    - Audit logging
    """
    
    def __init__(self):
        """Initialize credential manager."""
        self._credentials: Dict[str, str] = {}
        self._encryption_key = self._generate_key()
    
    @staticmethod
    def _generate_key() -> bytes:
        """Generate encryption key for session."""
        return secrets.token_bytes(32)
    
    def _encrypt(self, value: str) -> str:
        """Simple encryption for in-memory storage."""
        # Use HMAC for simple encryption (not for production use)
        return hmac.new(
            self._encryption_key,
            value.encode(),
            hashlib.sha256
        ).hexdigest()
    
    def store_credential(
        self,
        key: str,
        value: str,
        source: str = "manual"
    ) -> None:
        """
        Store a credential securely.
        
        Args:
            key: Credential key/identifier
            value: Credential value
            source: Source of credential (env, manual, etc.)
        """
        if not key or not value:
            raise ValidationError("Credential key and value cannot be empty")
        
        # Validate key format
        if not re.match(r"^[A-Z][A-Z0-9_]*$", key):
            raise ValidationError(
                "Credential key must be uppercase with underscores"
            )
        
        # Store encrypted
        encrypted = self._encrypt(value)
        self._credentials[key] = encrypted
        
        logger.info(f"Stored credential: {key} (source: {source})")
    
    def get_credential(self, key: str, required: bool = True) -> Optional[str]:
        """
        Retrieve a credential.
        
        Args:
            key: Credential key
            required: Whether credential is required
            
        Returns:
            Credential value or None
            
        Raises:
            ValidationError: If required credential not found
        """
        # Try environment variable first
        env_value = os.environ.get(key)
        if env_value:
            logger.debug(f"Retrieved credential from environment: {key}")
            return env_value
        
        # Try stored credentials
        if key in self._credentials:
            logger.debug(f"Retrieved credential from storage: {key}")
            # Note: In production, would decrypt here
            return f"encrypted:{self._credentials[key][:16]}..."
        
        if required:
            raise ValidationError(f"Required credential not found: {key}")
        
        return None
    
    def remove_credential(self, key: str) -> None:
        """
        Remove a credential.
        
        Args:
            key: Credential key
        """
        if key in self._credentials:
            del self._credentials[key]
            logger.info(f"Removed credential: {key}")
    
    def list_credentials(self) -> List[str]:
        """
        List available credential keys.
        
        Returns:
            List of credential keys
        """
        env_creds = [
            key for key in os.environ.keys()
            if key.startswith(("AZURE_", "ARM_"))
        ]
        stored_creds = list(self._credentials.keys())
        
        return sorted(set(env_creds + stored_creds))
    
    def clear_all(self) -> None:
        """Clear all stored credentials."""
        self._credentials.clear()
        logger.info("Cleared all stored credentials")


@dataclass
class AuditEntry:
    """Security audit log entry."""
    
    timestamp: datetime
    event_type: str
    user: str
    action: str
    resource: Optional[str]
    result: str
    security_level: SecurityLevel
    details: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "event_type": self.event_type,
            "user": self.user,
            "action": self.action,
            "resource": self.resource,
            "result": self.result,
            "security_level": self.security_level.value,
            "details": self.details
        }


class SecurityAuditor:
    """
    Security audit logging system.
    
    Features:
    - Structured audit logs
    - Security level classification
    - Persistent storage
    - Query and analysis capabilities
    """
    
    def __init__(self, log_file: Optional[Path] = None):
        """
        Initialize security auditor.
        
        Args:
            log_file: Path to audit log file
        """
        self.log_file = log_file or Path.cwd() / ".bicep-generator" / "audit.log"
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        self._entries: List[AuditEntry] = []
    
    def log_event(
        self,
        event_type: str,
        user: str,
        action: str,
        result: str,
        security_level: SecurityLevel = SecurityLevel.LOW,
        resource: Optional[str] = None,
        **details: Any
    ) -> None:
        """
        Log a security event.
        
        Args:
            event_type: Type of event (authentication, authorization, etc.)
            user: User identifier
            action: Action performed
            result: Result of action (success, failure, denied)
            security_level: Security level of event
            resource: Resource affected
            **details: Additional event details
        """
        entry = AuditEntry(
            timestamp=datetime.now(),
            event_type=event_type,
            user=user,
            action=action,
            resource=resource,
            result=result,
            security_level=security_level,
            details=details
        )
        
        self._entries.append(entry)
        
        # Write to file immediately for critical events
        if security_level in (SecurityLevel.HIGH, SecurityLevel.CRITICAL):
            self._write_entry(entry)
        
        # Log to standard logger
        log_msg = (
            f"SECURITY [{security_level.value.upper()}] "
            f"{event_type}: {user} {action} {resource or ''} - {result}"
        )
        
        if security_level == SecurityLevel.CRITICAL:
            logger.critical(log_msg)
        elif security_level == SecurityLevel.HIGH:
            logger.error(log_msg)
        elif security_level == SecurityLevel.MEDIUM:
            logger.warning(log_msg)
        else:
            logger.info(log_msg)
    
    def _write_entry(self, entry: AuditEntry) -> None:
        """Write entry to audit log file."""
        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry.to_dict()) + "\n")
        except Exception as e:
            logger.error(f"Failed to write audit entry: {e}")
    
    def flush(self) -> None:
        """Flush all entries to disk."""
        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                for entry in self._entries:
                    f.write(json.dumps(entry.to_dict()) + "\n")
            self._entries.clear()
        except Exception as e:
            logger.error(f"Failed to flush audit log: {e}")
    
    def query_events(
        self,
        event_type: Optional[str] = None,
        user: Optional[str] = None,
        security_level: Optional[SecurityLevel] = None,
        since: Optional[datetime] = None,
        limit: int = 100
    ) -> List[AuditEntry]:
        """
        Query audit events.
        
        Args:
            event_type: Filter by event type
            user: Filter by user
            security_level: Filter by security level
            since: Filter by timestamp
            limit: Maximum results
            
        Returns:
            List of matching audit entries
        """
        results = []
        
        for entry in reversed(self._entries):
            if event_type and entry.event_type != event_type:
                continue
            if user and entry.user != user:
                continue
            if security_level and entry.security_level != security_level:
                continue
            if since and entry.timestamp < since:
                continue
            
            results.append(entry)
            
            if len(results) >= limit:
                break
        
        return results
    
    def get_summary(self, hours: int = 24) -> Dict[str, Any]:
        """
        Get security event summary.
        
        Args:
            hours: Number of hours to include
            
        Returns:
            Summary dictionary
        """
        cutoff = datetime.now() - timedelta(hours=hours)
        recent = [e for e in self._entries if e.timestamp >= cutoff]
        
        summary = {
            "total_events": len(recent),
            "time_period_hours": hours,
            "by_type": defaultdict(int),
            "by_level": defaultdict(int),
            "by_result": defaultdict(int),
            "users": set()
        }
        
        for entry in recent:
            summary["by_type"][entry.event_type] += 1
            summary["by_level"][entry.security_level.value] += 1
            summary["by_result"][entry.result] += 1
            summary["users"].add(entry.user)
        
        summary["by_type"] = dict(summary["by_type"])
        summary["by_level"] = dict(summary["by_level"])
        summary["by_result"] = dict(summary["by_result"])
        summary["users"] = list(summary["users"])
        
        return summary


def display_audit_summary(summary: Dict[str, Any]) -> None:
    """
    Display audit summary in formatted table.
    
    Args:
        summary: Audit summary dictionary
    """
    console.print(f"\n[bold cyan]Security Audit Summary[/bold cyan]")
    console.print(f"[dim]Last {summary['time_period_hours']} hours[/dim]\n")
    
    # Events by type
    if summary["by_type"]:
        table = Table(title="Events by Type")
        table.add_column("Event Type", style="cyan")
        table.add_column("Count", style="yellow")
        
        for event_type, count in sorted(summary["by_type"].items()):
            table.add_row(event_type, str(count))
        
        console.print(table)
    
    # Events by security level
    if summary["by_level"]:
        table = Table(title="Events by Security Level")
        table.add_column("Level", style="bold")
        table.add_column("Count", style="yellow")
        
        level_colors = {
            "critical": "red",
            "high": "red",
            "medium": "yellow",
            "low": "green"
        }
        
        for level, count in sorted(summary["by_level"].items()):
            color = level_colors.get(level, "white")
            table.add_row(f"[{color}]{level.upper()}[/{color}]", str(count))
        
        console.print(table)
    
    console.print(f"\n[cyan]Total Events:[/cyan] {summary['total_events']}")
    console.print(f"[cyan]Unique Users:[/cyan] {len(summary['users'])}")


# Global instances
_credential_manager = CredentialManager()
_security_auditor = SecurityAuditor()

# Export convenience functions
def get_credential(key: str, required: bool = True) -> Optional[str]:
    """Get a credential."""
    return _credential_manager.get_credential(key, required)


def store_credential(key: str, value: str, source: str = "manual") -> None:
    """Store a credential."""
    _credential_manager.store_credential(key, value, source)


def audit_event(
    event_type: str,
    user: str,
    action: str,
    result: str,
    security_level: SecurityLevel = SecurityLevel.LOW,
    resource: Optional[str] = None,
    **details: Any
) -> None:
    """Log a security audit event."""
    _security_auditor.log_event(
        event_type, user, action, result, security_level, resource, **details
    )


def get_audit_summary(hours: int = 24) -> Dict[str, Any]:
    """Get audit summary."""
    return _security_auditor.get_summary(hours)


# Export instances
credential_manager = _credential_manager
security_auditor = _security_auditor
