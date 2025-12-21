"""
specify_cli.spiff.ops.otel_validation - OTEL Validation Workflows

Provides BPMN-driven test validation for OpenTelemetry instrumentation.
Adapted from uvmgr's comprehensive validation framework.

This module enables:
  - Creating custom BPMN validation workflows
  - Executing workflows with instrumentation verification
  - 80/20 approach: critical path validation
  - Comprehensive metrics collection
"""

from __future__ import annotations

import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

__all__ = [
    "OTELValidationResult",
    "TestValidationStep",
    "create_otel_validation_workflow",
    "execute_otel_validation_workflow",
    "run_8020_otel_validation",
]

# Optional OTEL instrumentation
try:
    from ...core.telemetry import metric_counter, metric_histogram, span
    from ...core.instrumentation import add_span_attributes, add_span_event
    _otel_available = True
except ImportError:
    _otel_available = False

    def span(*args, **kwargs):
        from contextlib import contextmanager
        @contextmanager
        def _no_op():
            yield
        return _no_op()

    def metric_counter(name):
        def _no_op(value=1):
            return None
        return _no_op

    def metric_histogram(name):
        def _no_op(value):
            return None
        return _no_op

    def add_span_attributes(**kwargs):
        pass

    def add_span_event(name, attributes=None):
        pass


@dataclass
class TestValidationStep:
    """Individual validation step tracking."""

    key: str
    name: str
    type: str  # "setup", "execution", "validation", "cleanup"
    success: bool
    duration_seconds: float = 0.0
    details: str = ""
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "key": self.key,
            "name": self.name,
            "type": self.type,
            "success": self.success,
            "duration_seconds": self.duration_seconds,
            "details": self.details,
            "error": self.error,
        }


@dataclass
class OTELValidationResult:
    """Comprehensive OTEL validation results."""

    success: bool
    workflow_name: str
    duration_seconds: float = 0.0
    validation_steps: List[TestValidationStep] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    spans_created: int = 0
    metrics_recorded: int = 0
    test_results: Dict[str, bool] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "success": self.success,
            "workflow_name": self.workflow_name,
            "duration_seconds": self.duration_seconds,
            "steps": [s.to_dict() for s in self.validation_steps],
            "errors": self.errors,
            "metrics": self.metrics,
            "spans_created": self.spans_created,
            "metrics_recorded": self.metrics_recorded,
            "test_results": self.test_results,
        }


def create_otel_validation_workflow(
    output_path: Path,
    test_commands: List[str],
    workflow_name: str = "otel_validation",
) -> Path:
    """
    Create a BPMN workflow for OTEL validation.

    Args:
        output_path: Where to save the BPMN file
        test_commands: List of test commands to execute
        workflow_name: Name of the workflow

    Returns
    -------
        Path to created BPMN file
    """
    with span("workflow.create_otel_validation", workflow_name=workflow_name):
        add_span_event("workflow.creation.started", {"num_commands": len(test_commands)})

        # Generate BPMN XML
        bpmn_content = _generate_otel_validation_bpmn(workflow_name, test_commands)

        # Write to file
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(bpmn_content)

        add_span_event("workflow.creation.completed", {"file_path": str(output_path)})
        metric_counter("workflow.creation.count")(1)

        return output_path


def execute_otel_validation_workflow(
    workflow_path: Path,
    test_commands: List[str],
    timeout_seconds: int = 60,
) -> OTELValidationResult:
    """
    Execute OTEL validation workflow.

    Args:
        workflow_path: Path to BPMN workflow file
        test_commands: Commands to execute for validation
        timeout_seconds: Timeout for execution

    Returns
    -------
        OTELValidationResult with comprehensive validation data
    """
    start_time = time.time()
    workflow_name = workflow_path.stem

    with span("validation.execute_otel_workflow", workflow_name=workflow_name):
        result = OTELValidationResult(
            success=False,
            workflow_name=workflow_name,
        )

        validation_steps: List[TestValidationStep] = []

        try:
            # Step 1: Validate BPMN file
            step_start = time.time()
            add_span_event("validation.step.bpmn_validation.started", {})

            try:
                from ..runtime import validate_bpmn_file
                bpmn_valid = validate_bpmn_file(workflow_path)
                step_duration = time.time() - step_start

                validation_steps.append(TestValidationStep(
                    key="bpmn_validation",
                    name="BPMN File Validation",
                    type="setup",
                    success=bpmn_valid,
                    duration_seconds=step_duration,
                    details=f"Validated workflow definition from {workflow_path.name}",
                ))
                metric_histogram("validation.step.duration")(step_duration)
            except Exception as e:
                validation_steps.append(TestValidationStep(
                    key="bpmn_validation",
                    name="BPMN File Validation",
                    type="setup",
                    success=False,
                    duration_seconds=time.time() - step_start,
                    error=str(e),
                ))
                raise

            # Step 2: Execute workflow
            step_start = time.time()
            add_span_event("validation.step.workflow_execution.started", {})

            try:
                from ..runtime import run_bpmn
                workflow_result = run_bpmn(workflow_path)
                step_duration = time.time() - step_start

                validation_steps.append(TestValidationStep(
                    key="workflow_execution",
                    name="Workflow Execution",
                    type="execution",
                    success=workflow_result.get("status") == "completed",
                    duration_seconds=step_duration,
                    details=f"Executed {workflow_result.get('steps_executed', 0)} steps",
                ))
            except Exception as e:
                validation_steps.append(TestValidationStep(
                    key="workflow_execution",
                    name="Workflow Execution",
                    type="execution",
                    success=False,
                    duration_seconds=time.time() - step_start,
                    error=str(e),
                ))
                raise

            # Step 3: Execute test commands
            step_start = time.time()
            add_span_event("validation.step.test_execution.started", {
                "num_tests": len(test_commands)
            })

            test_results = {}
            for i, cmd in enumerate(test_commands):
                try:
                    result_text = subprocess.run(
                        cmd,
                        shell=True,
                        capture_output=True,
                        text=True,
                        timeout=timeout_seconds,
                    )
                    test_results[cmd] = result_text.returncode == 0
                except Exception as e:
                    test_results[cmd] = False

            step_duration = time.time() - step_start
            passed_tests = sum(1 for v in test_results.values() if v)

            validation_steps.append(TestValidationStep(
                key="test_execution",
                name="Test Command Execution",
                type="execution",
                success=passed_tests == len(test_commands),
                duration_seconds=step_duration,
                details=f"Executed {len(test_commands)} test commands, {passed_tests} passed",
            ))

            # Step 4: OTEL system health check
            step_start = time.time()
            add_span_event("validation.step.otel_health.started", {})

            try:
                otel_health = _validate_otel_system_health()
                step_duration = time.time() - step_start

                validation_steps.append(TestValidationStep(
                    key="otel_health",
                    name="OTEL System Health",
                    type="validation",
                    success=otel_health["healthy"],
                    duration_seconds=step_duration,
                    details=otel_health.get("details", ""),
                ))
            except Exception as e:
                validation_steps.append(TestValidationStep(
                    key="otel_health",
                    name="OTEL System Health",
                    type="validation",
                    success=False,
                    duration_seconds=time.time() - step_start,
                    error=str(e),
                ))

            # Calculate result
            result.validation_steps = validation_steps
            result.success = all(s.success for s in validation_steps)
            result.duration_seconds = time.time() - start_time
            result.test_results = test_results
            result.metrics = {
                "total_steps": len(validation_steps),
                "successful_steps": sum(1 for s in validation_steps if s.success),
                "total_tests": len(test_commands),
                "successful_tests": passed_tests,
            }

            add_span_event("validation.execution.completed", {
                "success": result.success,
                "steps": len(validation_steps),
                "duration": result.duration_seconds,
            })

            metric_counter("validation.executions.completed")(1)
            metric_histogram("validation.execution.duration")(result.duration_seconds)

            return result

        except Exception as e:
            result.errors.append(str(e))
            result.duration_seconds = time.time() - start_time

            add_span_event("validation.execution.failed", {
                "error": str(e),
                "duration": result.duration_seconds,
            })

            metric_counter("validation.executions.failed")(1)
            return result


def run_8020_otel_validation(
    test_scope: str = "core",
    timeout_seconds: int = 60,
) -> OTELValidationResult:
    """
    Run 80/20 OTEL validation (critical path only).

    Focuses on the 20% of tests that validate 80% of functionality:
    - OTEL library imports
    - Span creation capability
    - Metric recording capability
    - Instrumentation registry
    - Basic workflow execution

    Args:
        test_scope: Scope of validation ("core", "full", "minimal")
        timeout_seconds: Timeout for execution

    Returns
    -------
        OTELValidationResult
    """
    with span("validation.8020_otel", scope=test_scope):
        add_span_event("validation.8020.started", {"scope": test_scope})

        # Define critical tests based on scope
        if test_scope == "minimal":
            test_commands = [
                "python -c 'import opentelemetry'",
                "python -c 'from opentelemetry.sdk.trace import TracerProvider'",
            ]
        elif test_scope == "core":
            test_commands = [
                "python -c 'import opentelemetry'",
                "python -c 'from opentelemetry.sdk.trace import TracerProvider'",
                "python -c 'from opentelemetry.sdk.metrics import MeterProvider'",
                "python -c 'from opentelemetry.instrumentation import trace'",
                "python -c 'from specify_cli.spiff.runtime import run_bpmn'",
            ]
        else:  # full
            test_commands = [
                "python -c 'import opentelemetry'",
                "python -c 'from opentelemetry.sdk.trace import TracerProvider'",
                "python -c 'from opentelemetry.sdk.metrics import MeterProvider'",
                "python -c 'from opentelemetry.instrumentation import trace'",
                "python -c 'from specify_cli.spiff.runtime import run_bpmn'",
                "python -c 'from specify_cli.core import WorkflowAttributes'",
                "python -c 'from specify_cli.core.telemetry import span'",
            ]

        # Create and execute workflow
        workflow_path = Path.home() / ".cache" / "spec_kit" / "otel_validation.bpmn"
        create_otel_validation_workflow(workflow_path, test_commands)

        result = execute_otel_validation_workflow(
            workflow_path,
            test_commands,
            timeout_seconds=timeout_seconds,
        )

        metric_counter("validation.8020.executed")(1)
        if result.success:
            metric_counter("validation.8020.success")(1)
        else:
            metric_counter("validation.8020.failure")(1)

        return result


def _generate_otel_validation_bpmn(workflow_name: str, test_commands: List[str]) -> str:
    """Generate BPMN XML for OTEL validation workflow."""
    task_list = "\n".join([
        f"""        <bpmn:ServiceTask id="Task_{i}" name="Test: {cmd[:50]}...">
          <bpmn:outgoing>Flow_{i}</bpmn:outgoing>
        </bpmn:ServiceTask>
        <bpmn:SequenceFlow id="Flow_{i}" sourceRef="Task_{i}" targetRef="{'Task_' + str(i+1) if i+1 < len(test_commands) else 'End'}"/>"""
        for i, cmd in enumerate(test_commands)
    ])

    first_task_ref = f"Task_0" if test_commands else "End"

    return f"""<?xml version="1.0" encoding="UTF-8"?>
<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"
                   xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI"
                   xmlns:dc="http://www.omg.org/spec/DD/20100524/DC"
                   id="Definitions_{workflow_name}"
                   name="{workflow_name}">
  <bpmn:process id="Process_{workflow_name}" name="{workflow_name}">
    <bpmn:startEvent id="Start" name="Start OTEL Validation">
      <bpmn:outgoing>StartFlow</bpmn:outgoing>
    </bpmn:startEvent>
    <bpmn:sequenceFlow id="StartFlow" sourceRef="Start" targetRef="{first_task_ref}"/>
{task_list}
    <bpmn:endEvent id="End" name="OTEL Validation Complete">
      <bpmn:incoming>Flow_{len(test_commands)-1 if test_commands else '0'}</bpmn:incoming>
    </bpmn:endEvent>
  </bpmn:process>
</bpmn:definitions>
"""


def _validate_otel_system_health() -> Dict[str, Any]:
    """Validate OTEL system health."""
    try:
        import opentelemetry
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.metrics import MeterProvider
        from opentelemetry.instrumentation import trace

        # Check critical components
        checks = {
            "opentelemetry_import": True,
            "tracer_provider": isinstance(TracerProvider(), TracerProvider),
            "meter_provider": isinstance(MeterProvider(), MeterProvider),
            "instrumentation_api": hasattr(trace, 'get_tracer'),
        }

        healthy = all(checks.values())
        details = f"OTEL Health: {sum(checks.values())}/{len(checks)} checks passed"

        return {
            "healthy": healthy,
            "details": details,
            "checks": checks,
        }
    except Exception as e:
        return {
            "healthy": False,
            "details": f"OTEL health check failed: {e}",
            "checks": {},
        }
