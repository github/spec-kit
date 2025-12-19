"""
Exception hierarchy for spec-kit.

This module defines all custom exceptions used throughout the library.
"""

from typing import Optional


class SpecKitError(Exception):
    """Base exception for all spec-kit errors."""

    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


# =============================================================================
# Configuration Errors
# =============================================================================


class ConfigurationError(SpecKitError):
    """Error in configuration."""

    pass


class InvalidConfigError(ConfigurationError):
    """Invalid configuration value."""

    def __init__(self, key: str, value: str, reason: str):
        super().__init__(
            f"Invalid configuration for '{key}': {reason}",
            {"key": key, "value": value, "reason": reason},
        )
        self.key = key
        self.value = value
        self.reason = reason


class MissingConfigError(ConfigurationError):
    """Required configuration is missing."""

    def __init__(self, key: str):
        super().__init__(
            f"Missing required configuration: {key}",
            {"key": key},
        )
        self.key = key


# =============================================================================
# LLM Errors
# =============================================================================


class LLMError(SpecKitError):
    """Error from LLM provider."""

    def __init__(
        self,
        message: str,
        model: Optional[str] = None,
        provider: Optional[str] = None,
        original_error: Optional[Exception] = None,
    ):
        super().__init__(
            message,
            {"model": model, "provider": provider},
        )
        self.model = model
        self.provider = provider
        self.original_error = original_error


class LLMRateLimitError(LLMError):
    """Rate limit exceeded."""

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: Optional[int] = None,
        **kwargs,
    ):
        super().__init__(message, **kwargs)
        self.retry_after = retry_after


class LLMTimeoutError(LLMError):
    """Request timed out."""

    def __init__(
        self,
        message: str = "Request timed out",
        timeout: Optional[int] = None,
        **kwargs,
    ):
        super().__init__(message, **kwargs)
        self.timeout = timeout


class LLMAuthenticationError(LLMError):
    """Authentication failed."""

    def __init__(self, message: str = "Authentication failed", **kwargs):
        super().__init__(message, **kwargs)


class LLMModelNotFoundError(LLMError):
    """Model not found."""

    def __init__(self, model: str, **kwargs):
        super().__init__(
            f"Model not found: {model}",
            model=model,
            **kwargs,
        )


# =============================================================================
# Validation Errors
# =============================================================================


class ValidationError(SpecKitError):
    """Validation error for schemas or data."""

    def __init__(
        self,
        message: str,
        errors: Optional[list[dict]] = None,
    ):
        super().__init__(message, {"errors": errors or []})
        self.errors = errors or []


class SchemaValidationError(ValidationError):
    """Schema validation failed."""

    def __init__(self, model_name: str, errors: list[dict]):
        super().__init__(
            f"Schema validation failed for {model_name}",
            errors=errors,
        )
        self.model_name = model_name


# =============================================================================
# Storage Errors
# =============================================================================


class StorageError(SpecKitError):
    """Error in storage operations."""

    pass


class ArtifactNotFoundError(StorageError):
    """Artifact not found."""

    def __init__(self, artifact_type: str, feature_id: str):
        super().__init__(
            f"{artifact_type.title()} not found for feature: {feature_id}",
            {"artifact_type": artifact_type, "feature_id": feature_id},
        )
        self.artifact_type = artifact_type
        self.feature_id = feature_id


class FeatureNotFoundError(StorageError):
    """Feature not found."""

    def __init__(self, feature_id: str):
        super().__init__(
            f"Feature not found: {feature_id}",
            {"feature_id": feature_id},
        )
        self.feature_id = feature_id


class StorageIOError(StorageError):
    """I/O error in storage operations."""

    def __init__(self, path: str, operation: str, original_error: Optional[Exception] = None):
        super().__init__(
            f"Storage I/O error during {operation}: {path}",
            {"path": path, "operation": operation},
        )
        self.path = path
        self.operation = operation
        self.original_error = original_error


# =============================================================================
# Workflow Errors
# =============================================================================


class WorkflowError(SpecKitError):
    """Error in workflow execution."""

    pass


class WorkflowStateError(WorkflowError):
    """Invalid workflow state."""

    def __init__(self, message: str, current_state: str, expected_state: str):
        super().__init__(
            message,
            {"current_state": current_state, "expected_state": expected_state},
        )
        self.current_state = current_state
        self.expected_state = expected_state


class DependencyError(WorkflowError):
    """Dependency not satisfied."""

    def __init__(self, task_id: str, missing_deps: list[str]):
        super().__init__(
            f"Task {task_id} has unmet dependencies: {', '.join(missing_deps)}",
            {"task_id": task_id, "missing_deps": missing_deps},
        )
        self.task_id = task_id
        self.missing_deps = missing_deps


class CircularDependencyError(WorkflowError):
    """Circular dependency detected."""

    def __init__(self, cycle: list[str]):
        super().__init__(
            f"Circular dependency detected: {' -> '.join(cycle)}",
            {"cycle": cycle},
        )
        self.cycle = cycle
