"""
Tests for SPIFF OTEL Validation Operations

Tests for OTEL validation workflows and result tracking.
"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from specify_cli.spiff.ops import (
    OTELValidationResult,
    TestValidationStep,
    create_otel_validation_workflow,
    run_8020_otel_validation,
)


class TestValidationResultTypes:
    """Test validation result dataclasses."""

    def test_test_validation_step_creation(self):
        """Test creating a TestValidationStep."""
        step = TestValidationStep(
            key="test_key",
            name="Test Step",
            type="setup",
            success=True,
            duration_seconds=1.5,
            details="Test details",
        )

        assert step.key == "test_key"
        assert step.name == "Test Step"
        assert step.type == "setup"
        assert step.success is True
        assert step.duration_seconds == 1.5

    def test_test_validation_step_to_dict(self):
        """Test converting TestValidationStep to dict."""
        step = TestValidationStep(
            key="test",
            name="Test",
            type="execution",
            success=True,
            duration_seconds=2.0,
        )

        step_dict = step.to_dict()
        assert isinstance(step_dict, dict)
        assert step_dict["key"] == "test"
        assert step_dict["success"] is True

    def test_otel_validation_result_creation(self):
        """Test creating an OTELValidationResult."""
        result = OTELValidationResult(
            success=True,
            workflow_name="test_workflow",
            duration_seconds=10.0,
        )

        assert result.success is True
        assert result.workflow_name == "test_workflow"
        assert result.duration_seconds == 10.0

    def test_otel_validation_result_to_dict(self):
        """Test converting OTELValidationResult to dict."""
        result = OTELValidationResult(
            success=False,
            workflow_name="test",
            duration_seconds=5.0,
            errors=["Error 1", "Error 2"],
        )

        result_dict = result.to_dict()
        assert isinstance(result_dict, dict)
        assert result_dict["success"] is False
        assert result_dict["workflow_name"] == "test"
        assert len(result_dict["errors"]) == 2


class TestWorkflowCreation:
    """Test BPMN workflow creation for OTEL validation."""

    def test_create_validation_workflow(self, tmp_path):
        """Test creating a BPMN validation workflow."""
        output_path = tmp_path / "validation.bpmn"
        test_commands = ["echo 'test1'", "echo 'test2'"]

        workflow_path = create_otel_validation_workflow(output_path, test_commands)

        # Verify file created
        assert workflow_path.exists()
        assert workflow_path == output_path

        # Verify BPMN content
        content = workflow_path.read_text()
        assert "<?xml" in content
        assert "bpmn:definitions" in content
        assert "Process_otel_validation" in content

    def test_create_workflow_with_empty_tests(self, tmp_path):
        """Test creating workflow with no tests."""
        output_path = tmp_path / "empty.bpmn"

        workflow_path = create_otel_validation_workflow(output_path, [])

        assert workflow_path.exists()
        content = workflow_path.read_text()
        assert "bpmn:definitions" in content

    def test_create_workflow_creates_parent_dirs(self, tmp_path):
        """Test that parent directories are created."""
        output_path = tmp_path / "nested" / "deep" / "workflow.bpmn"

        workflow_path = create_otel_validation_workflow(output_path, [])

        assert workflow_path.exists()
        assert workflow_path.parent.exists()


class TestOTEL8020Validation:
    """Test 80/20 OTEL validation."""

    @patch("specify_cli.spiff.ops.otel_validation.execute_otel_validation_workflow")
    def test_run_8020_validation_minimal(self, mock_execute):
        """Test running 80/20 validation in minimal mode."""
        # Mock execution result
        mock_result = OTELValidationResult(
            success=True,
            workflow_name="otel_validation",
            duration_seconds=5.0,
        )
        mock_execute.return_value = mock_result

        # Run validation
        result = run_8020_otel_validation(test_scope="minimal")

        # Verify result
        assert result is not None
        assert isinstance(result, OTELValidationResult)

    @patch("specify_cli.spiff.ops.otel_validation.execute_otel_validation_workflow")
    def test_run_8020_validation_core(self, mock_execute):
        """Test running 80/20 validation in core mode."""
        mock_result = OTELValidationResult(
            success=True,
            workflow_name="otel_validation",
            duration_seconds=5.0,
        )
        mock_execute.return_value = mock_result

        result = run_8020_otel_validation(test_scope="core")

        assert result is not None
        assert result.success is True

    @patch("specify_cli.spiff.ops.otel_validation.execute_otel_validation_workflow")
    def test_run_8020_validation_full(self, mock_execute):
        """Test running 80/20 validation in full mode."""
        mock_result = OTELValidationResult(
            success=True,
            workflow_name="otel_validation",
            duration_seconds=8.0,
        )
        mock_execute.return_value = mock_result

        result = run_8020_otel_validation(test_scope="full")

        assert result is not None
        # Full scope should create more tests than minimal
        mock_execute.assert_called_once()
        call_args = mock_execute.call_args
        test_commands = call_args[0][1] if len(call_args[0]) > 1 else []
        assert len(test_commands) >= 5  # Full scope has at least 5 tests


class TestValidationSteps:
    """Test individual validation steps."""

    def test_validation_step_with_error(self):
        """Test creating a validation step with error."""
        step = TestValidationStep(
            key="failed_test",
            name="Failed Test",
            type="validation",
            success=False,
            duration_seconds=0.5,
            error="Test failed: module not found",
        )

        assert step.success is False
        assert step.error is not None
        assert "module not found" in step.error

    def test_validation_step_duration_tracking(self):
        """Test duration tracking in validation steps."""
        step1 = TestValidationStep(
            key="step1",
            name="Step 1",
            type="setup",
            success=True,
            duration_seconds=1.0,
        )
        step2 = TestValidationStep(
            key="step2",
            name="Step 2",
            type="execution",
            success=True,
            duration_seconds=2.5,
        )

        total_duration = step1.duration_seconds + step2.duration_seconds
        assert total_duration == 3.5
