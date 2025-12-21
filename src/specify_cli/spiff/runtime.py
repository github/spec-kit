"""
specify_cli.spiff.runtime - BPMN Workflow Execution Engine

Low-level SpiffWorkflow integration with comprehensive OTEL instrumentation.
Adapted from uvmgr's runtime/agent/spiff.py.

Features:
  - BPMN workflow execution with safety mechanisms
  - Infinite loop detection
  - Task-level performance tracking
  - Full OTEL instrumentation with spans, events, and metrics
  - Semantic conventions for workflow domain

Note: Requires SpiffWorkflow library. Install with:
    pip install spiffworkflow
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any, Dict, Optional

try:
    from SpiffWorkflow.bpmn.parser import BpmnParser
    from SpiffWorkflow.bpmn.workflow import BpmnWorkflow
    from SpiffWorkflow.task import Task, TaskState
except ImportError:
    raise ImportError(
        "SpiffWorkflow is required for SPIFF support. "
        "Install with: pip install specify-cli[spiff]"
    )

from ..core.shell import colour

__all__ = [
    "run_bpmn",
    "validate_bpmn_file",
    "get_workflow_stats",
]

# Optional OTEL instrumentation (graceful degradation if not available)
try:
    from ..core.telemetry import metric_counter, metric_histogram, span
    from ..core.instrumentation import add_span_attributes, add_span_event
    _otel_available = True
except ImportError:
    _otel_available = False

    # Mock OTEL functions if not available
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


def _load(path: Path) -> BpmnWorkflow:
    """Load BPMN workflow from file with instrumentation."""
    with span("workflow.load", definition_path=str(path)):
        add_span_event("workflow.parsing.started", {"file_path": str(path)})

        parser = BpmnParser()
        parser.add_bpmn_file(str(path))

        # Get the workflow specification name from the file
        # Try to get the first available process spec
        process_parsers = parser.process_parsers
        if process_parsers:
            process_id = list(process_parsers.keys())[0]
            wf_spec = parser.get_spec(process_id)
        else:
            # Fallback to empty string for legacy compatibility
            wf_spec = parser.get_spec("")

        workflow = BpmnWorkflow(wf_spec)

        # Add workflow metadata to current span
        add_span_attributes(
            workflow_engine="SpiffWorkflow",
            workflow_definition_name=wf_spec.name or path.stem,
            workflow_instance_id=str(id(workflow)),
        )

        add_span_event("workflow.parsing.completed", {
            "workflow_name": wf_spec.name or path.stem,
            "task_count": len(list(wf_spec.task_specs)),
        })

        metric_counter("workflow.instances.created")(1)

        return workflow


def _step(wf: BpmnWorkflow) -> None:
    """Execute one step of workflow with detailed instrumentation."""
    with span("workflow.step"):
        step_start = time.time()
        tasks_processed = 0

        # Get next ready task and execute it
        next_task = wf.get_next_task()
        if next_task:
            task_type = "script" if hasattr(next_task.task_spec, "script") else "service"
            _process_task(wf, next_task, task_type)
            tasks_processed = 1

            add_span_event("workflow.task.executed", {
                "task_name": getattr(next_task.task_spec, "name", str(next_task)),
                "task_type": task_type,
            })
        else:
            # No tasks ready, workflow might be waiting or complete
            add_span_event("workflow.step.no_tasks", {"workflow_completed": wf.is_completed()})

        step_duration = time.time() - step_start

        add_span_attributes(
            tasks_processed=tasks_processed,
            step_duration_ms=int(step_duration * 1000),
        )

        # Record step metrics
        metric_histogram("workflow.step.duration")(step_duration)
        metric_counter("workflow.tasks.processed")(tasks_processed)


def _process_task(wf: BpmnWorkflow, task: Task, task_type: str) -> None:
    """Process a single workflow task with instrumentation."""
    task_name = getattr(task.task_spec, "name", str(task))

    with span(
        f"workflow.task.{task_type}",
        task_name=task_name,
        task_type=task_type,
        task_id=str(task.id),
    ):
        task_start = time.time()

        add_span_event("task.started", {
            "task_name": task_name,
            "task_type": task_type,
            "task_state": str(task.state),
        })

        try:
            # Execute the task based on its type
            if task_type == "script":
                colour(f"🔄 executing script task: {task_name}", "cyan")
                # For script tasks, just complete them (SpiffWorkflow handles execution)
                task.complete()
            else:
                colour(f"↻ auto-completing service task: {task_name}", "cyan")
                # For other tasks, complete directly
                task.complete()

            task_duration = time.time() - task_start

            add_span_event("task.completed", {
                "task_name": task_name,
                "duration_ms": int(task_duration * 1000),
            })

            # Record task metrics
            metric_histogram(f"workflow.task.{task_type}.duration")(task_duration)
            metric_counter(f"workflow.task.{task_type}.completed")(1)

        except Exception as e:
            add_span_event("task.failed", {
                "task_name": task_name,
                "error": str(e),
            })
            metric_counter(f"workflow.task.{task_type}.failed")(1)
            raise


def run_bpmn(path: Path | str) -> dict[str, Any]:
    """
    Execute a BPMN workflow with comprehensive instrumentation.

    Args:
        path: Path to the BPMN file

    Returns
    -------
        Dict containing workflow execution statistics:
            - status: "completed" or "failed"
            - duration_seconds: Total execution time
            - steps_executed: Number of workflow steps
            - total_tasks: Total number of tasks
            - completed_tasks: Number of completed tasks
            - failed_tasks: Number of failed/cancelled tasks
            - workflow_name: Name of the workflow
    """
    path = Path(path)
    execution_start = time.time()

    with span(
        "workflow.execute",
        definition_path=str(path),
        definition_name=path.stem,
        engine="SpiffWorkflow",
    ):
        add_span_event("workflow.execution.started", {"file_path": str(path)})

        # Load workflow
        wf = _load(path)

        steps = 0
        total_tasks = 0

        try:
            # Execute workflow steps with safety mechanisms
            max_iterations = 100  # Prevent infinite loops
            last_task_id = None
            iterations = 0

            while not wf.is_completed() and iterations < max_iterations:
                iterations += 1

                # Get next task for safety checking
                next_task = wf.get_next_task()
                if not next_task:
                    add_span_event("workflow.no_ready_tasks", {"iteration": iterations})
                    break

                # Check for infinite loop (same task repeating)
                current_task_id = next_task.id
                if current_task_id == last_task_id:
                    add_span_event("workflow.infinite_loop_detected", {
                        "task_id": str(current_task_id),
                        "task_name": getattr(next_task.task_spec, "name", "unknown"),
                        "iteration": iterations
                    })
                    break

                last_task_id = current_task_id
                all_tasks_before = len(list(wf.get_tasks()))

                # Execute step
                _step(wf)

                all_tasks_after = len(list(wf.get_tasks()))
                steps += 1
                total_tasks += all_tasks_after

                # Add progress update
                add_span_event("workflow.step.completed", {
                    "step_number": steps,
                    "iteration": iterations,
                    "total_tasks": all_tasks_after,
                })

                # Safety: Add small delay to prevent CPU spinning
                time.sleep(0.001)

            if iterations >= max_iterations:
                add_span_event("workflow.max_iterations_reached", {
                    "max_iterations": max_iterations,
                    "steps": steps
                })

            execution_duration = time.time() - execution_start

            # Final workflow state
            final_tasks = list(wf.get_tasks())
            # Count tasks by state using SpiffWorkflow states
            completed_tasks = [t for t in final_tasks if t.state == TaskState.COMPLETED]
            failed_tasks = [t for t in final_tasks if t.state == TaskState.CANCELLED]

            stats = {
                "status": "completed",
                "duration_seconds": execution_duration,
                "steps_executed": steps,
                "total_tasks": len(final_tasks),
                "completed_tasks": len(completed_tasks),
                "failed_tasks": len(failed_tasks),
                "workflow_name": path.stem,
            }

            add_span_attributes(**{
                f"workflow.{k}": v for k, v in stats.items()
                if isinstance(v, (str, int, float, bool))
            })

            add_span_event("workflow.execution.completed", stats)

            # Record final metrics
            metric_histogram("workflow.execution.duration")(execution_duration)
            metric_counter("workflow.executions.completed")(1)

            colour("✔ BPMN workflow completed", "green")
            colour(f"  Duration: {execution_duration:.2f}s, Steps: {steps}, Tasks: {len(completed_tasks)}", "blue")

            return stats

        except Exception as e:
            execution_duration = time.time() - execution_start

            error_stats = {
                "status": "failed",
                "duration_seconds": execution_duration,
                "steps_executed": steps,
                "error": str(e),
                "workflow_name": path.stem,
            }

            add_span_event("workflow.execution.failed", error_stats)
            metric_counter("workflow.executions.failed")(1)

            colour(f"✗ BPMN workflow failed: {e}", "red")
            raise


def get_workflow_stats(wf: BpmnWorkflow) -> dict[str, Any]:
    """
    Get comprehensive statistics about a workflow instance with telemetry.

    Args:
        wf: BpmnWorkflow instance

    Returns
    -------
        Dict containing workflow statistics:
            - total_tasks: Total number of tasks
            - completed_tasks: Number of completed tasks
            - ready_tasks: Number of ready-to-execute tasks
            - waiting_tasks: Number of waiting tasks
            - cancelled_tasks: Number of cancelled tasks
            - is_completed: Whether workflow is complete
            - workflow_name: Name of the workflow
    """
    with span("workflow.get_stats", workflow_id=str(id(wf))):
        add_span_event("workflow.stats.collecting", {"workflow_id": str(id(wf))})

        start_time = time.time()
        all_tasks = list(wf.get_tasks())

        # Calculate stats with detailed breakdown
        completed_tasks = [t for t in all_tasks if t.state == TaskState.COMPLETED]
        ready_tasks = [t for t in all_tasks if t.state == TaskState.READY]
        waiting_tasks = [t for t in all_tasks if t.state == TaskState.WAITING]
        cancelled_tasks = [t for t in all_tasks if t.state == TaskState.CANCELLED]

        stats = {
            "total_tasks": len(all_tasks),
            "completed_tasks": len(completed_tasks),
            "ready_tasks": len(ready_tasks),
            "waiting_tasks": len(waiting_tasks),
            "cancelled_tasks": len(cancelled_tasks),
            "is_completed": wf.is_completed(),
            "workflow_name": getattr(wf.spec, "name", "unknown"),
        }

        duration = time.time() - start_time

        # Record metrics
        metric_counter("workflow.stats.requests")(1)
        metric_histogram("workflow.stats.collection_duration")(duration)

        add_span_attributes(**{
            "workflow.name": stats["workflow_name"],
            "workflow.total_tasks": stats["total_tasks"],
            "workflow.completed_tasks": stats["completed_tasks"],
            "workflow.is_completed": stats["is_completed"],
            "workflow.stats_duration": duration,
        })

        add_span_event("workflow.stats.collected", {
            **stats,
            "collection_duration": duration,
        })

        return stats


def validate_bpmn_file(path: Path | str) -> bool:
    """
    Validate a BPMN file can be loaded successfully.

    Args:
        path: Path to the BPMN file

    Returns
    -------
        True if file is valid, False otherwise
    """
    path = Path(path)
    with span("workflow.validate", definition_path=str(path)):
        try:
            parser = BpmnParser()
            parser.add_bpmn_file(str(path))

            # Try to get the first available process spec
            process_parsers = parser.process_parsers
            if process_parsers:
                process_id = list(process_parsers.keys())[0]
                spec = parser.get_spec(process_id)
            else:
                # Fallback to empty string for legacy compatibility
                spec = parser.get_spec("")

            add_span_event("workflow.validation.success", {
                "workflow_name": spec.name or path.stem,
                "task_specs": len(list(spec.task_specs)),
            })

            metric_counter("workflow.validations.passed")(1)
            return True

        except Exception as e:
            add_span_event("workflow.validation.failed", {
                "error": str(e),
                "file_path": str(path),
            })

            metric_counter("workflow.validations.failed")(1)
            return False
