"""Core functionality for Specify CLI."""

from .git import is_git_repo, init_git_repo
from .github import (
    _format_rate_limit_error,
    _github_auth_headers,
    _github_token,
    _parse_rate_limit_headers,
    download_template_from_github,
)

__all__ = [
    # GitHub functions
    "_github_token",
    "_github_auth_headers",
    "_parse_rate_limit_headers",
    "_format_rate_limit_error",
    "download_template_from_github",
    # Git functions
    "is_git_repo",
    "init_git_repo",
]
