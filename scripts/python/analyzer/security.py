"""
Security utilities for safe project analysis.

Provides path validation and sanitization to prevent security vulnerabilities.
"""

import logging
from pathlib import Path
from typing import Optional

# Handle both relative and absolute imports
try:
    from .config import DEFAULT_CONFIG
except ImportError:
    from config import DEFAULT_CONFIG

logger = logging.getLogger(__name__)


class SecurityError(Exception):
    """Raised when security validation fails."""
    pass


def validate_project_path(path: Path) -> Path:
    """
    Validate that a project path is safe to analyze.

    Args:
        path: Path to validate

    Returns:
        Resolved absolute path

    Raises:
        SecurityError: If path is unsafe
        FileNotFoundError: If path doesn't exist
        PermissionError: If path is not readable
    """
    # Convert to Path object
    path = Path(path)

    # Check if path exists
    if not path.exists():
        raise FileNotFoundError(f"Path does not exist: {path}")

    # Resolve to absolute path
    try:
        resolved_path = path.resolve(strict=True)
    except (OSError, RuntimeError) as e:
        raise SecurityError(f"Cannot resolve path: {e}")

    # Check if it's a directory
    if not resolved_path.is_dir():
        raise SecurityError(f"Path is not a directory: {resolved_path}")

    # Check for forbidden system paths
    path_str = str(resolved_path)
    forbidden = DEFAULT_CONFIG.security.forbidden_paths

    for forbidden_path in forbidden:
        if path_str.startswith(forbidden_path):
            raise SecurityError(
                f"Cannot analyze system directory: {resolved_path} "
                f"(starts with {forbidden_path})"
            )

    # Check read permission
    if not resolved_path.is_dir() or not resolved_path.exists():
        raise PermissionError(f"Cannot read directory: {resolved_path}")

    # Additional checks for symlinks to system directories
    try:
        # Check if any parent is a symlink to a forbidden path
        for parent in resolved_path.parents:
            if parent.is_symlink():
                target = parent.readlink()
                target_str = str(target)
                for forbidden_path in forbidden:
                    if target_str.startswith(forbidden_path):
                        raise SecurityError(
                            f"Symlink to forbidden path detected: {parent} -> {target}"
                        )
    except Exception as e:
        logger.warning(f"Could not check symlinks: {e}")

    return resolved_path


def validate_file_path(file_path: Path, project_root: Path) -> Path:
    """
    Validate that a file path is within project scope.

    Args:
        file_path: File path to validate
        project_root: Project root directory

    Returns:
        Resolved file path

    Raises:
        SecurityError: If file is outside project scope
    """
    file_path = Path(file_path).resolve()
    project_root = Path(project_root).resolve()

    # Ensure file is within project root
    try:
        file_path.relative_to(project_root)
    except ValueError:
        raise SecurityError(
            f"File path {file_path} is outside project root {project_root}"
        )

    return file_path


def sanitize_path_for_display(path: Path, max_length: int = 100) -> str:
    """
    Sanitize path for safe display in logs/reports.

    Args:
        path: Path to sanitize
        max_length: Maximum length of output string

    Returns:
        Safe string representation
    """
    path_str = str(path)

    # Truncate if too long
    if len(path_str) > max_length:
        path_str = "..." + path_str[-(max_length-3):]

    # Remove any control characters
    path_str = "".join(char for char in path_str if ord(char) >= 32 or char in '\n\t')

    return path_str
