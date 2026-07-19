"""Tests for overlay YAML schema normalization, especially shorthand edits."""

from __future__ import annotations

import pytest

from specify_cli.workflows.overlays.schema import (
    OverlayEdit,
    validate_overlay_yaml,
)


class TestShorthandEdits:
    """Requirements-compliant shorthand edit format."""

    def test_shorthand_insert_after(self):
        overlay, errors = validate_overlay_yaml(
            {
                "id": "lint",
                "extends": "wf",
                "priority": 10,
                "edits": [
                    {
                        "insert_after": "implement",
                        "step": {"id": "lint", "type": "shell", "command": "npm run lint"},
                    }
                ],
            }
        )
        assert not errors, errors
        assert overlay is not None
        assert overlay.edits == [
            OverlayEdit("insert_after", "implement", {"id": "lint", "type": "shell", "command": "npm run lint"})
        ]

    def test_shorthand_insert_before(self):
        overlay, errors = validate_overlay_yaml(
            {
                "id": "ov",
                "extends": "wf",
                "priority": 10,
                "edits": [
                    {
                        "insert_before": "a",
                        "step": {"id": "b", "type": "command", "command": "echo"},
                    }
                ],
            }
        )
        assert not errors, errors
        assert overlay is not None
        assert overlay.edits == [
            OverlayEdit("insert_before", "a", {"id": "b", "type": "command", "command": "echo"})
        ]

    def test_shorthand_replace(self):
        overlay, errors = validate_overlay_yaml(
            {
                "id": "ov",
                "extends": "wf",
                "priority": 10,
                "edits": [
                    {
                        "replace": "a",
                        "step": {"id": "a", "type": "command", "command": "echo"},
                    }
                ],
            }
        )
        assert not errors, errors
        assert overlay is not None
        assert overlay.edits == [
            OverlayEdit("replace", "a", {"id": "a", "type": "command", "command": "echo"})
        ]

    def test_shorthand_remove(self):
        overlay, errors = validate_overlay_yaml(
            {
                "id": "ov",
                "extends": "wf",
                "priority": 10,
                "edits": [{"remove": "a"}],
            }
        )
        assert not errors, errors
        assert overlay is not None
        assert overlay.edits == [OverlayEdit("remove", "a")]

    def test_explicit_operation_format_still_valid(self):
        overlay, errors = validate_overlay_yaml(
            {
                "id": "ov",
                "extends": "wf",
                "priority": 10,
                "edits": [
                    {
                        "operation": "insert_after",
                        "anchor": "a",
                        "step": {"id": "b", "type": "command", "command": "echo"},
                    }
                ],
            }
        )
        assert not errors, errors
        assert overlay is not None
        assert overlay.edits == [
            OverlayEdit("insert_after", "a", {"id": "b", "type": "command", "command": "echo"})
        ]

    def test_multiple_operation_fields_rejected(self):
        overlay, errors = validate_overlay_yaml(
            {
                "id": "ov",
                "extends": "wf",
                "priority": 10,
                "edits": [
                    {
                        "insert_after": "a",
                        "remove": "a",
                    }
                ],
            }
        )
        assert overlay is None
        assert any("multiple" in e.lower() for e in errors), errors

    def test_invalid_operation_field_rejected(self):
        overlay, errors = validate_overlay_yaml(
            {
                "id": "ov",
                "extends": "wf",
                "priority": 10,
                "edits": [{"destroy": "a"}],
            }
        )
        assert overlay is None
        assert any("operation" in e.lower() for e in errors), errors

    def test_shorthand_and_explicit_mixed_list(self):
        overlay, errors = validate_overlay_yaml(
            {
                "id": "ov",
                "extends": "wf",
                "priority": 10,
                "edits": [
                    {"insert_after": "a", "step": {"id": "b", "type": "command", "command": "echo"}},
                    {
                        "operation": "remove",
                        "anchor": "c",
                    },
                ],
            }
        )
        assert not errors, errors
        assert overlay is not None
        assert overlay.edits == [
            OverlayEdit("insert_after", "a", {"id": "b", "type": "command", "command": "echo"}),
            OverlayEdit("remove", "c"),
        ]

    def test_shorthand_remove_must_not_include_step(self):
        overlay, errors = validate_overlay_yaml(
            {
                "id": "ov",
                "extends": "wf",
                "priority": 10,
                "edits": [
                    {
                        "remove": "a",
                        "step": {"id": "b", "type": "command", "command": "echo"},
                    }
                ],
            }
        )
        assert overlay is None
        assert any("remove" in e.lower() and "step" in e.lower() for e in errors), errors


class TestOverlayIdValidation:
    """Overlay and workflow IDs must be safe path segments."""

    @pytest.mark.parametrize("overlay_id", ["../ov", "a/b", "a\\\\b", ".", "..", ""])
    def test_invalid_overlay_id_rejected(self, overlay_id):
        overlay, errors = validate_overlay_yaml(
            {
                "id": overlay_id,
                "extends": "wf",
                "priority": 10,
                "edits": [{"remove": "a"}],
            }
        )
        assert overlay is None
        assert any("id" in e.lower() for e in errors), errors


class TestOverlayPriorityNormalization:
    """Stored overlay priorities match preset normalization semantics."""

    @pytest.mark.parametrize("priority", [None, True, "invalid", 0])
    def test_invalid_or_missing_priority_defaults_to_ten(self, priority):
        data = {
            "id": "ov",
            "extends": "wf",
            "edits": [{"remove": "a"}],
        }
        if priority is not None:
            data["priority"] = priority

        overlay, errors = validate_overlay_yaml(data)

        assert errors == []
        assert overlay is not None
        assert overlay.priority == 10

    @pytest.mark.parametrize("extends", ["../wf", "a/b", "a\\\\b", ".", "..", ""])
    def test_invalid_extends_rejected(self, extends):
        overlay, errors = validate_overlay_yaml(
            {
                "id": "ov",
                "extends": extends,
                "priority": 10,
                "edits": [{"remove": "a"}],
            }
        )
        assert overlay is None
        assert any("extends" in e.lower() for e in errors), errors

    @pytest.mark.parametrize("extends", ["overlays", "runs", "steps"])
    def test_reserved_workflow_id_rejected(self, extends):
        overlay, errors = validate_overlay_yaml(
            {
                "id": "ov",
                "extends": extends,
                "priority": 10,
                "edits": [{"remove": "a"}],
            }
        )
        assert overlay is None
        assert any("reserved" in error.lower() for error in errors), errors

    def test_valid_dashed_id_accepted(self):
        overlay, errors = validate_overlay_yaml(
            {
                "id": "my-overlay",
                "extends": "my-workflow",
                "priority": 10,
                "edits": [{"remove": "a"}],
            }
        )
        assert not errors, errors
        assert overlay is not None

    def test_validate_safe_id_rejects_trailing_newline(self):
        """A trailing newline must not pass ID validation (fullmatch guard)."""
        overlay, errors = validate_overlay_yaml(
            {
                "id": "overlay\n",
                "extends": "wf",
                "priority": 10,
                "edits": [{"remove": "a"}],
            }
        )
        assert overlay is None
        assert any("id" in e.lower() for e in errors), errors

    def test_validate_safe_id_rejects_embedded_newline(self):
        """An embedded newline must not pass ID validation."""
        overlay, errors = validate_overlay_yaml(
            {
                "id": "ov\nerlay",
                "extends": "wf",
                "priority": 10,
                "edits": [{"remove": "a"}],
            }
        )
        assert overlay is None
        assert any("id" in e.lower() for e in errors), errors
