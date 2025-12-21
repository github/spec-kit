"""
specify_cli.spiff.ops - SPIFF Operations Layer

Business logic for BPMN workflow management, OTEL validation, and external
project validation, separated from CLI layer for testability and reusability.
"""

from .otel_validation import (
    OTELValidationResult,
    TestValidationStep,
    create_otel_validation_workflow,
    execute_otel_validation_workflow,
    run_8020_otel_validation,
)
from .external_projects import (
    ExternalProjectInfo,
    ExternalValidationResult,
    discover_external_projects,
    validate_external_project_with_spiff,
    batch_validate_external_projects,
    run_8020_external_project_validation,
)

__all__ = [
    # OTEL validation
    "OTELValidationResult",
    "TestValidationStep",
    "create_otel_validation_workflow",
    "execute_otel_validation_workflow",
    "run_8020_otel_validation",
    # External projects
    "ExternalProjectInfo",
    "ExternalValidationResult",
    "discover_external_projects",
    "validate_external_project_with_spiff",
    "batch_validate_external_projects",
    "run_8020_external_project_validation",
]
