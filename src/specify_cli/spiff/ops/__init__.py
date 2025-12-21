"""
specify_cli.spiff.ops - SPIFF Operations Layer

Business logic for BPMN workflow management and OTEL validation,
separated from CLI layer for testability and reusability.
"""

from .otel_validation import (
    OTELValidationResult,
    TestValidationStep,
    create_otel_validation_workflow,
    execute_otel_validation_workflow,
    run_8020_otel_validation,
)

__all__ = [
    "OTELValidationResult",
    "TestValidationStep",
    "create_otel_validation_workflow",
    "execute_otel_validation_workflow",
    "run_8020_otel_validation",
]
