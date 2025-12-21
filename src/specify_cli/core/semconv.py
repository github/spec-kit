"""
specify_cli.core.semconv - Semantic Conventions

Standard attribute names for OpenTelemetry instrumentation in spec-kit.
Follows OpenTelemetry semantic conventions while adding spec-kit specific domains.

Reference: https://opentelemetry.io/docs/specs/otel/protocol/exporter/
"""

from typing import Dict, Any

__all__ = [
    "WorkflowAttributes",
    "WorkflowOperations",
    "TestAttributes",
    "SpecAttributes",
]


class WorkflowAttributes:
    """Semantic conventions for BPMN workflow execution."""

    WORKFLOW_ID = "workflow.id"
    WORKFLOW_NAME = "workflow.name"
    WORKFLOW_VERSION = "workflow.version"
    WORKFLOW_FILE = "workflow.file"
    WORKFLOW_FORMAT = "workflow.format"  # "bpmn", "dmn", etc.
    WORKFLOW_STATUS = "workflow.status"  # "created", "executing", "completed", "failed"

    TASK_ID = "task.id"
    TASK_NAME = "task.name"
    TASK_TYPE = "task.type"  # "script_task", "service_task", "user_task", etc.
    TASK_STATE = "task.state"  # "COMPLETED", "READY", "WAITING", "CANCELLED"
    TASK_ATTEMPTS = "task.attempts"
    TASK_DURATION_MS = "task.duration_ms"

    STEP_INDEX = "step.index"
    STEP_COUNT = "step.count"
    STEP_DURATION_MS = "step.duration_ms"

    LOOP_DETECTED = "workflow.loop_detected"
    LOOP_COUNT = "workflow.loop_count"
    MAX_ITERATIONS = "workflow.max_iterations"
    CURRENT_ITERATION = "workflow.current_iteration"


class WorkflowOperations:
    """Operation names for workflow instrumentation."""

    CREATE = "workflow.create"
    LOAD = "workflow.load"
    VALIDATE = "workflow.validate"
    EXECUTE = "workflow.execute"
    STEP = "workflow.step"
    TASK_EXECUTE = "task.execute"
    TASK_PROCESS = "task.process"
    PARSE = "bpmn.parse"


class TestAttributes:
    """Semantic conventions for test execution and validation."""

    TEST_ID = "test.id"
    TEST_NAME = "test.name"
    TEST_TYPE = "test.type"  # "unit", "integration", "e2e", "validation"
    TEST_COMMAND = "test.command"
    TEST_STATUS = "test.status"  # "passed", "failed", "skipped"
    TEST_DURATION_MS = "test.duration_ms"
    TEST_ERROR = "test.error"

    VALIDATION_ID = "validation.id"
    VALIDATION_TYPE = "validation.type"  # "otel", "integration", "conformance"
    VALIDATION_SCOPE = "validation.scope"  # "project", "module", "function"
    VALIDATION_RESULT = "validation.result"  # "success", "failure", "warning"

    # OTEL-specific validation
    OTEL_SPANS_CREATED = "otel.spans_created"
    OTEL_METRICS_CREATED = "otel.metrics_created"
    OTEL_SPAN_EVENTS = "otel.span_events"
    OTEL_HEALTH_STATUS = "otel.health_status"


class SpecAttributes:
    """Semantic conventions for Spec-Kit specific operations."""

    SPEC_ID = "spec.id"
    SPEC_NAME = "spec.name"
    SPEC_FILE = "spec.file"
    SPEC_FORMAT = "spec.format"  # "rdf", "bpmn", "yaml", etc.
    SPEC_STATUS = "spec.status"  # "draft", "active", "archived"

    PROJECT_ID = "project.id"
    PROJECT_NAME = "project.name"
    PROJECT_PATH = "project.path"
    PROJECT_TYPE = "project.type"  # "web", "cli", "library", "data", "ml"
    PROJECT_MANAGER = "project.manager"  # "uv", "pip", "poetry", "pipenv"

    PM_OPERATION = "pm.operation"  # "discover", "conform", "filter", "sample"
    PM_ALGORITHM = "pm.algorithm"  # "alpha", "inductive", etc.
    PM_CASES = "pm.cases"
    PM_EVENTS = "pm.events"
    PM_ACTIVITIES = "pm.activities"
    PM_VARIANTS = "pm.variants"

    CODEGEN_FILE = "codegen.file"
    CODEGEN_LINES = "codegen.lines"
    CODEGEN_TIME_MS = "codegen.time_ms"


def get_common_attributes(name: str, status: str = None) -> Dict[str, Any]:
    """
    Create a common attribute set for any operation.

    Args:
        name: Operation name
        status: Operation status (optional)

    Returns:
        Dictionary of standard attributes
    """
    attrs = {"operation.name": name}
    if status:
        attrs["operation.status"] = status
    return attrs
