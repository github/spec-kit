"""
Guard CLI Data Models - Category × Type Architecture

This module defines all data models for the guard system following
the Category × Type matrix organization.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional


@dataclass
class Category:
    """
    Technology/tooling for building guards (how you build the guard).
    
    Examples: pytest, docker, vitest, shell, mermaid
    """
    name: str
    description: str
    yaml_path: Path
    src_path: Optional[Path]
    invocation_pattern: str
    input_schema: dict
    output_schema: dict
    params_schema: dict
    teaching_content: str


@dataclass
class Type:
    """
    Functional validation purpose (what the guard validates).
    
    Examples: unit-testing, api-contracts, security, ux-flows
    """
    name: str
    description: str
    standard_definition: str
    success_criteria: list[str]
    common_failures: list[str]
    teaching_content: str


@dataclass
class GuardType:
    """
    Intersection of Category × Type (defines how to build/run guards).
    
    Example: pytest-unit-tests = pytest (category) × unit-testing (type)
    """
    id: str
    category: Category
    type: Type
    scaffolder_path: Path
    templates_dir: Path
    combined_teaching: str


@dataclass
class GuardInstance:
    """
    Instantiated guard in a codebase (parameterized microapp).
    
    Example: G007 - a specific pytest unit test guard for feature X
    """
    id: str
    guard_type: GuardType
    name: str
    created_at: datetime
    files: list[Path]
    command: str
    params: dict
    tags: list[str] = field(default_factory=list)
    tasks: list[str] = field(default_factory=list)


class CommentCategory(Enum):
    """Limited set of comment categories for structured diagnostics."""
    ROOT_CAUSE = "root-cause"
    FIX_APPLIED = "fix-applied"
    INVESTIGATION = "investigation"
    WORKAROUND = "workaround"
    FALSE_POSITIVE = "false-positive"


@dataclass
class CommentNote:
    """
    Structured note template for guard run comments.
    
    Creates diagnostic narrative: done → expected → todo
    """
    done: str  # What was done since last run
    expected: str  # What is expected next run
    todo: str  # What will be done before next run


@dataclass
class Comment:
    """
    Differential diagnosis comment for a guard run.
    
    Provides structured tracking of investigation and fixes.
    """
    timestamp: datetime
    category: CommentCategory
    note: CommentNote


@dataclass
class GuardRun:
    """
    Single execution of a guard with results and analysis.
    
    Stored in guard's history.json file.
    """
    run_id: str
    guard_id: str
    timestamp: datetime
    passed: bool  # Simplified: whether guard passed
    exit_code: int
    duration_ms: int  # Duration in milliseconds
    stdout: str
    stderr: str = ""
    analysis: str = ""  # Simplified: text analysis instead of dict
    comments: list[Comment] = field(default_factory=list)
    
    # Optional fields for future use
    git_commit: Optional[str] = None
    params: dict = field(default_factory=dict)
    guard_version: Optional[str] = None


class GuardPolicy(Enum):
    """Policy for task completion based on guard results."""
    ALL_PASS = "all_pass"  # All guards must pass
    ANY_PASS = "any_pass"  # At least one guard must pass
    MAJORITY_PASS = "majority_pass"  # >50% guards must pass


@dataclass
class GuardMetadata:
    """
    Guard metadata for manifest tracking.
    
    Stored in .specify/guards/list/ directory as individual guard files.
    """
    type: str
    category: str
    name: str
    created: datetime
    tags: list[str]
    tasks: list[str]


@dataclass
class TaskGuards:
    """
    Guards required for a specific task.
    
    Stored in guards-manifest.yaml tasks section.
    """
    name: str
    guards: list[str]
    guard_policy: GuardPolicy


@dataclass
class GuardsManifest:
    """
    Central manifest tracking guard-task-tag associations.
    
    Stored at .specify/guards-manifest.yaml.
    """
    guards: dict[str, GuardMetadata] = field(default_factory=dict)
    tasks: dict[str, TaskGuards] = field(default_factory=dict)
    tags: dict[str, list[str]] = field(default_factory=dict)
