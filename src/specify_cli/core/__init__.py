"""
specify_cli.core - Core utilities and infrastructure

This module provides foundational utilities for the Specify CLI, including:
- Shell output and formatting utilities
- Process execution helpers
- Semantic conventions for OTEL instrumentation
- Error handling and exceptions
- Configuration management
"""

from .shell import (
    colour,
    colour_stderr,
    dump_json,
    markdown,
    timed,
    rich_table,
    progress_bar,
    install_rich,
)
from .process import (
    run_command,
    run_logged,
)
from .semconv import (
    WorkflowAttributes,
    WorkflowOperations,
    TestAttributes,
    SpecAttributes,
    get_common_attributes,
)

__all__ = [
    "colour",
    "colour_stderr",
    "dump_json",
    "markdown",
    "timed",
    "rich_table",
    "progress_bar",
    "install_rich",
    "run_command",
    "run_logged",
    "WorkflowAttributes",
    "WorkflowOperations",
    "TestAttributes",
    "SpecAttributes",
    "get_common_attributes",
]
