"""
Tests for SPIFF Runtime Engine

Tests for BPMN workflow execution, validation, and statistics.
"""

import pytest
import tempfile
from pathlib import Path

pytest.importorskip("spiff", minversion=None)

from specify_cli.spiff.runtime import (
    run_bpmn,
    validate_bpmn_file,
    get_workflow_stats,
)


class TestBPMNValidation:
    """Test BPMN file validation."""

    def test_validate_valid_bpmn(self, tmp_path):
        """Test validation of a valid BPMN file."""
        # Create a minimal valid BPMN file
        bpmn_content = """<?xml version="1.0" encoding="UTF-8"?>
<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"
                   id="Definitions_test"
                   name="test">
  <bpmn:process id="Process_test" name="test">
    <bpmn:startEvent id="Start" name="Start">
      <bpmn:outgoing>Flow</bpmn:outgoing>
    </bpmn:startEvent>
    <bpmn:endEvent id="End" name="End">
      <bpmn:incoming>Flow</bpmn:incoming>
    </bpmn:endEvent>
    <bpmn:sequenceFlow id="Flow" sourceRef="Start" targetRef="End"/>
  </bpmn:process>
</bpmn:definitions>"""

        workflow_path = tmp_path / "test.bpmn"
        workflow_path.write_text(bpmn_content)

        # Validate
        result = validate_bpmn_file(workflow_path)
        assert result is True

    def test_validate_invalid_bpmn(self, tmp_path):
        """Test validation of invalid BPMN file."""
        invalid_bpmn = "<invalid>not bpmn</invalid>"
        workflow_path = tmp_path / "invalid.bpmn"
        workflow_path.write_text(invalid_bpmn)

        # Validate
        result = validate_bpmn_file(workflow_path)
        assert result is False

    def test_validate_nonexistent_file(self):
        """Test validation of non-existent file."""
        workflow_path = Path("/nonexistent/workflow.bpmn")
        result = validate_bpmn_file(workflow_path)
        assert result is False


class TestBPMNExecution:
    """Test BPMN workflow execution."""

    def test_run_simple_workflow(self, tmp_path):
        """Test execution of a simple workflow."""
        bpmn_content = """<?xml version="1.0" encoding="UTF-8"?>
<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"
                   id="Definitions_simple"
                   name="simple">
  <bpmn:process id="Process_simple" name="simple">
    <bpmn:startEvent id="Start" name="Start">
      <bpmn:outgoing>Flow</bpmn:outgoing>
    </bpmn:startEvent>
    <bpmn:endEvent id="End" name="End">
      <bpmn:incoming>Flow</bpmn:incoming>
    </bpmn:endEvent>
    <bpmn:sequenceFlow id="Flow" sourceRef="Start" targetRef="End"/>
  </bpmn:process>
</bpmn:definitions>"""

        workflow_path = tmp_path / "simple.bpmn"
        workflow_path.write_text(bpmn_content)

        # Execute
        result = run_bpmn(workflow_path)

        # Verify result structure
        assert isinstance(result, dict)
        assert "status" in result
        assert "duration_seconds" in result
        assert "steps_executed" in result
        assert "workflow_name" in result

    def test_run_workflow_with_path_string(self, tmp_path):
        """Test execution with path as string."""
        bpmn_content = """<?xml version="1.0" encoding="UTF-8"?>
<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"
                   id="Definitions_stringpath"
                   name="stringpath">
  <bpmn:process id="Process_stringpath" name="stringpath">
    <bpmn:startEvent id="Start" name="Start">
      <bpmn:outgoing>Flow</bpmn:outgoing>
    </bpmn:startEvent>
    <bpmn:endEvent id="End" name="End">
      <bpmn:incoming>Flow</bpmn:incoming>
    </bpmn:endEvent>
    <bpmn:sequenceFlow id="Flow" sourceRef="Start" targetRef="End"/>
  </bpmn:process>
</bpmn:definitions>"""

        workflow_path = tmp_path / "stringpath.bpmn"
        workflow_path.write_text(bpmn_content)

        # Execute with string path
        result = run_bpmn(str(workflow_path))
        assert result is not None
        assert result["status"] == "completed"

    def test_run_nonexistent_workflow(self):
        """Test execution of non-existent workflow."""
        with pytest.raises(Exception):
            run_bpmn(Path("/nonexistent/workflow.bpmn"))


class TestWorkflowStats:
    """Test workflow statistics collection."""

    def test_get_stats_from_workflow(self, tmp_path):
        """Test getting statistics from a workflow."""
        bpmn_content = """<?xml version="1.0" encoding="UTF-8"?>
<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"
                   id="Definitions_stats"
                   name="stats">
  <bpmn:process id="Process_stats" name="stats">
    <bpmn:startEvent id="Start" name="Start">
      <bpmn:outgoing>Flow</bpmn:outgoing>
    </bpmn:startEvent>
    <bpmn:endEvent id="End" name="End">
      <bpmn:incoming>Flow</bpmn:incoming>
    </bpmn:endEvent>
    <bpmn:sequenceFlow id="Flow" sourceRef="Start" targetRef="End"/>
  </bpmn:process>
</bpmn:definitions>"""

        workflow_path = tmp_path / "stats.bpmn"
        workflow_path.write_text(bpmn_content)

        # Load and execute workflow
        from specify_cli.spiff.runtime import _load
        wf = _load(workflow_path)

        # Get stats
        stats = get_workflow_stats(wf)

        # Verify stats structure
        assert isinstance(stats, dict)
        assert "total_tasks" in stats
        assert "completed_tasks" in stats
        assert "is_completed" in stats
        assert "workflow_name" in stats
        assert stats["total_tasks"] >= 0
