"""
specify_cli.spiff - BPMN Workflow Engine Integration

This module provides BPMN workflow execution with OpenTelemetry instrumentation,
adapted from uvmgr's SpiffWorkflow integration.

Key Components:
  - runtime: Low-level BPMN execution engine
  - ops: Business logic for workflow operations
  - semconv: Semantic conventions for workflow instrumentation

The SpiffWorkflow library is an optional dependency. Install with:
    pip install specify-cli[spiff]

Examples:
    >>> from specify_cli.spiff.runtime import run_bpmn
    >>> result = run_bpmn("workflow.bpmn")
    >>> print(f"Status: {result['status']}, Steps: {result['steps_executed']}")
"""

__all__ = [
    "run_bpmn",
    "validate_bpmn_file",
    "get_workflow_stats",
]

# Lazy imports - SpiffWorkflow is optional
_spiff_available = False
try:
    import spiff
    _spiff_available = True
except ImportError:
    pass


def run_bpmn(*args, **kwargs):
    """Execute a BPMN workflow (lazy loaded)."""
    if not _spiff_available:
        raise ImportError(
            "SpiffWorkflow is not installed. "
            "Install with: pip install specify-cli[spiff]"
        )
    from .runtime import run_bpmn as _run_bpmn
    return _run_bpmn(*args, **kwargs)


def validate_bpmn_file(*args, **kwargs):
    """Validate a BPMN file (lazy loaded)."""
    if not _spiff_available:
        raise ImportError(
            "SpiffWorkflow is not installed. "
            "Install with: pip install specify-cli[spiff]"
        )
    from .runtime import validate_bpmn_file as _validate_bpmn_file
    return _validate_bpmn_file(*args, **kwargs)


def get_workflow_stats(*args, **kwargs):
    """Get workflow execution statistics (lazy loaded)."""
    if not _spiff_available:
        raise ImportError(
            "SpiffWorkflow is not installed. "
            "Install with: pip install specify-cli[spiff]"
        )
    from .runtime import get_workflow_stats as _get_workflow_stats
    return _get_workflow_stats(*args, **kwargs)
