"""
Guard CLI System - Category × Type Architecture

This module implements the guard system with Category × Type organization
for progressive disclosure teaching mechanisms.
"""

from .commands import guard_app
from .executor import GuardExecutor, GuardHistory
from .registry import GuardRegistry
from .scaffolder import BaseScaffolder, GuardScaffolder
from .types import (
    Category,
    Comment,
    CommentCategory,
    CommentNote,
    GuardInstance,
    GuardMetadata,
    GuardPolicy,
    GuardRun,
    GuardsManifest,
    GuardType,
    TaskGuards,
    Type,
)
from .utils import (
    generate_guard_id,
    generate_run_id,
    load_json,
    load_yaml,
    save_json,
    save_yaml,
)

__all__ = [
    # Data models
    "Category",
    "Type",
    "GuardType",
    "GuardInstance",
    "GuardRun",
    "Comment",
    "CommentCategory",
    "CommentNote",
    "GuardsManifest",
    "GuardMetadata",
    "TaskGuards",
    "GuardPolicy",
    # Core classes
    "GuardRegistry",
    "GuardScaffolder",
    "BaseScaffolder",
    "GuardExecutor",
    "GuardHistory",
    # CLI
    "guard_app",
    # Utilities
    "generate_guard_id",
    "generate_run_id",
    "load_yaml",
    "save_yaml",
    "load_json",
    "save_json",
]

__version__ = "0.1.0"
