"""Tests for the workflow overlay merge engine."""

from __future__ import annotations

import copy
from typing import Any

import pytest

from specify_cli.workflows.overlays.merge import (
    ComposedStep,
    OverlayLayer,
    find_step,
    merge_steps,
    validate_edits,
)
from specify_cli.workflows.overlays.schema import Overlay, OverlayEdit


def _step(id: str, **kwargs: Any) -> dict[str, Any]:  # noqa: A002
    """Build a minimal step dict with the given id."""
    return {"id": id, "type": "command", "command": "speckit.specify", **kwargs}


def _layer(overlay: Overlay, source: str) -> OverlayLayer:
    """Build an OverlayLayer for merge_steps."""
    return OverlayLayer(overlay, source)


class TestFindStep:
    """Recursive anchor lookup across nested step lists."""

    def test_find_step_flat(self):
        steps = [_step("a"), _step("b"), _step("c")]
        result = find_step(steps, "b")
        assert result is not None
        assert result[0] is steps
        assert result[1] == 1

    def test_find_step_missing(self):
        steps = [_step("a"), _step("b")]
        assert find_step(steps, "missing") is None

    def test_find_step_in_then(self):
        steps = [
            {
                "id": "if-1",
                "type": "if",
                "condition": "true",
                "then": [_step("then-a")],
                "else": [_step("else-b")],
            },
        ]
        result = find_step(steps, "then-a")
        assert result is not None
        assert result[0] is steps[0]["then"]
        assert result[1] == 0

    def test_find_step_in_else(self):
        steps = [
            {
                "id": "if-1",
                "type": "if",
                "condition": "true",
                "then": [_step("then-a")],
                "else": [_step("else-b")],
            },
        ]
        result = find_step(steps, "else-b")
        assert result is not None
        assert result[0] is steps[0]["else"]
        assert result[1] == 0

    def test_find_step_in_nested_steps(self):
        steps = [
            {
                "id": "while-1",
                "type": "while",
                "condition": "true",
                "steps": [_step("inner-a"), _step("inner-b")],
            },
        ]
        result = find_step(steps, "inner-b")
        assert result is not None
        assert result[0] is steps[0]["steps"]
        assert result[1] == 1

    def test_find_step_in_switch_cases(self):
        steps = [
            {
                "id": "switch-1",
                "type": "switch",
                "expression": "{{ inputs.x }}",
                "cases": {
                    "one": [_step("case-a")],
                    "two": [_step("case-b")],
                },
                "default": [_step("default-c")],
            },
        ]
        assert find_step(steps, "case-b")[1] == 0
        assert find_step(steps, "default-c")[1] == 0

    def test_find_step_not_in_fan_out_template(self):
        steps = [
            {
                "id": "fan-1",
                "type": "fan-out",
                "items": "{{ inputs.items }}",
                "step": {"id": "template-x", "type": "command", "command": "echo"},
            },
        ]
        assert find_step(steps, "template-x") is None


class TestMergeSteps:
    """Composition of multiple overlays in merge order."""

    def test_merge_steps_no_overlays(self):
        base = [_step("a"), _step("b")]
        steps, attribution = merge_steps(base, [])
        assert [s["id"] for s in steps] == ["a", "b"]
        assert attribution == [ComposedStep("a", "base"), ComposedStep("b", "base")]

    def test_merge_steps_single_overlay(self):
        base = [_step("a"), _step("b")]
        overlay = Overlay(
            id="ov1",
            extends="wf",
            priority=10,
            edits=[OverlayEdit("insert_after", "a", _step("new"))],
        )
        steps, attribution = merge_steps(base, [_layer(overlay, "project:ov1")])
        assert [s["id"] for s in steps] == ["a", "new", "b"]
        assert attribution == [
            ComposedStep("a", "base"),
            ComposedStep("new", "project:ov1"),
            ComposedStep("b", "base"),
        ]

    def test_merge_steps_higher_priority_wins(self):
        base = [_step("a")]
        low = Overlay(
            id="low",
            extends="wf",
            priority=5,
            edits=[OverlayEdit("insert_after", "a", _step("low-step"))],
        )
        high = Overlay(
            id="high",
            extends="wf",
            priority=10,
            edits=[OverlayEdit("insert_after", "a", _step("high-step"))],
        )
        steps, attribution = merge_steps(base, [_layer(low, "project:low"), _layer(high, "project:high")])
        # low applied first, then high; both insert after 'a', so high-step ends
        # closer to the anchor (higher priority wins the conflict).
        assert [s["id"] for s in steps] == ["a", "high-step", "low-step"]
        assert attribution == [
            ComposedStep("a", "base"),
            ComposedStep("high-step", "project:high"),
            ComposedStep("low-step", "project:low"),
        ]

    def test_merge_steps_replace_wins_over_insert(self):
        """Overlays apply to the original tree only; targeting an overlay-introduced step raises."""
        base = [_step("a")]
        insert = Overlay(
            id="insert",
            extends="wf",
            priority=5,
            edits=[OverlayEdit("insert_after", "a", _step("inserted"))],
        )
        replace = Overlay(
            id="replace",
            extends="wf",
            priority=10,
            edits=[OverlayEdit("replace", "inserted", _step("replaced"))],
        )
        # "inserted" is not a base step — overlays cannot target each other's steps.
        with pytest.raises(ValueError, match="Anchor 'inserted' not found"):
            merge_steps(base, [_layer(insert, "project:insert"), _layer(replace, "project:replace")])

    def test_merge_steps_does_not_mutate_base(self):
        base = [_step("a")]
        overlay = Overlay(
            id="ov1",
            extends="wf",
            priority=10,
            edits=[OverlayEdit("insert_after", "a", _step("new"))],
        )
        original = copy.deepcopy(base)
        merge_steps(base, [_layer(overlay, "project:ov1")])
        assert base == original

    def test_merge_steps_attribution_uses_source_not_overlay_id(self):
        base = [_step("a")]
        overlay = Overlay(
            id="same-id",
            extends="wf",
            priority=10,
            edits=[OverlayEdit("insert_after", "a", _step("new"))],
        )
        steps, attribution = merge_steps(base, [_layer(overlay, "installed:same-id")])
        assert [s["id"] for s in steps] == ["a", "new"]
        assert attribution == [
            ComposedStep("a", "base"),
            ComposedStep("new", "installed:same-id"),
        ]

    def test_merge_steps_nested_base_attribution(self):
        base = [
            {
                "id": "if-1",
                "type": "if",
                "condition": "true",
                "then": [_step("then-a")],
                "else": [_step("else-b")],
            },
        ]
        steps, attribution = merge_steps(base, [])
        assert attribution == [
            ComposedStep("if-1", "base"),
            ComposedStep("then-a", "base"),
            ComposedStep("else-b", "base"),
        ]

    def test_merge_steps_higher_replace_wins_lower_replace_same_anchor(self):
        base = [_step("implement")]
        low = Overlay(
            id="low",
            extends="wf",
            priority=5,
            edits=[OverlayEdit("replace", "implement", _step("low-implement"))],
        )
        high = Overlay(
            id="high",
            extends="wf",
            priority=10,
            edits=[OverlayEdit("replace", "implement", _step("high-implement"))],
        )
        steps, attribution = merge_steps(base, [_layer(low, "project:low"), _layer(high, "project:high")])
        assert [s["id"] for s in steps] == ["high-implement"]
        assert any(
            composed.step_id == "high-implement" and composed.source == "project:high"
            for composed in attribution
        )

    def test_merge_steps_higher_replace_wins_after_lower_remove_same_anchor(self):
        base = [_step("implement")]
        low = Overlay(
            id="low",
            extends="wf",
            priority=5,
            edits=[OverlayEdit("remove", "implement")],
        )
        high = Overlay(
            id="high",
            extends="wf",
            priority=10,
            edits=[OverlayEdit("replace", "implement", _step("high-implement"))],
        )
        steps, attribution = merge_steps(base, [_layer(low, "project:low"), _layer(high, "project:high")])
        assert [s["id"] for s in steps] == ["high-implement"]

    def test_merge_steps_higher_insert_wins_after_lower_remove_same_anchor(self):
        base = [_step("implement")]
        low = Overlay(
            id="low",
            extends="wf",
            priority=5,
            edits=[OverlayEdit("remove", "implement")],
        )
        high = Overlay(
            id="high",
            extends="wf",
            priority=10,
            edits=[OverlayEdit("insert_after", "implement", _step("high-after"))],
        )
        steps, attribution = merge_steps(base, [_layer(low, "project:low"), _layer(high, "project:high")])
        assert [s["id"] for s in steps] == ["implement", "high-after"]
        assert attribution == [
            ComposedStep("implement", "base"),
            ComposedStep("high-after", "project:high"),
        ]

    def test_merge_steps_later_overlay_wins_tie_same_anchor(self):
        """When two overlays have the same priority, the one applied later wins."""
        base = [_step("a")]
        first = Overlay(
            id="first",
            extends="wf",
            priority=10,
            edits=[OverlayEdit("replace", "a", _step("first-replace"))],
        )
        second = Overlay(
            id="second",
            extends="wf",
            priority=10,
            edits=[OverlayEdit("replace", "a", _step("second-replace"))],
        )
        # Merge order: first applied, then second wins tie.
        steps, attribution = merge_steps(
            base,
            [
                _layer(first, "overlay:first"),
                _layer(second, "overlay:second"),
            ],
        )
        assert [s["id"] for s in steps] == ["second-replace"]
        assert any(
            composed.step_id == "second-replace" and composed.source == "overlay:second"
            for composed in attribution
        )

    def test_merge_steps_insert_after_then_replace_same_anchor_id_change(self):
        """Inserts must be applied before the winning replace so the anchor still exists.

        Regression: when a replace changes the step ID, applying it before inserts
        causes ``find_step`` to fail on the now-gone original anchor.
        """
        base = [_step("build")]
        low = Overlay(
            id="low",
            extends="wf",
            priority=5,
            edits=[OverlayEdit("insert_after", "build", _step("test"))],
        )
        high = Overlay(
            id="high",
            extends="wf",
            priority=10,
            edits=[OverlayEdit("replace", "build", _step("compile"))],
        )
        steps, attribution = merge_steps(
            base, [_layer(low, "project:low"), _layer(high, "project:high")]
        )
        # The insert should land after the original anchor position, then the
        # anchor is replaced.  Final order: ["compile", "test"].
        assert [s["id"] for s in steps] == ["compile", "test"]
        assert attribution == [
            ComposedStep("compile", "project:high"),
            ComposedStep("test", "project:low"),
        ]

    def test_merge_steps_insert_before_then_replace_same_anchor_id_change(self):
        """Same as above but with insert_before — anchor must still be findable."""
        base = [_step("build")]
        low = Overlay(
            id="low",
            extends="wf",
            priority=5,
            edits=[OverlayEdit("insert_before", "build", _step("lint"))],
        )
        high = Overlay(
            id="high",
            extends="wf",
            priority=10,
            edits=[OverlayEdit("replace", "build", _step("compile"))],
        )
        steps, attribution = merge_steps(
            base, [_layer(low, "project:low"), _layer(high, "project:high")]
        )
        assert [s["id"] for s in steps] == ["lint", "compile"]
        assert attribution == [
            ComposedStep("lint", "project:low"),
            ComposedStep("compile", "project:high"),
        ]

    def test_merge_steps_unknown_anchor_still_raises(self):
        base = [_step("a")]
        overlay = Overlay(
            id="ov",
            extends="wf",
            priority=10,
            edits=[OverlayEdit("replace", "missing", _step("new"))],
        )
        with pytest.raises(ValueError, match="Anchor 'missing' not found"):
            merge_steps(base, [_layer(overlay, "project:ov")])

    # ── composite step attribution ───────────────────────────────────────

    def test_merge_insert_composite_if_attribution(self):
        """Nested then/else children of an inserted 'if' step get the overlay source."""
        base = [_step("a")]
        composite = {
            "id": "if-1",
            "type": "if",
            "condition": "true",
            "then": [_step("then-a")],
            "else": [_step("else-b")],
        }
        overlay = Overlay(
            id="ov", extends="wf", priority=10,
            edits=[OverlayEdit("insert_after", "a", composite)],
        )
        _steps, attribution = merge_steps(
            base, [_layer(overlay, "project:ov")]
        )
        assert attribution == [
            ComposedStep("a", "base"),
            ComposedStep("if-1", "project:ov"),
            ComposedStep("then-a", "project:ov"),
            ComposedStep("else-b", "project:ov"),
        ]

    def test_merge_insert_composite_switch_attribution(self):
        """Nested cases/default children of an inserted 'switch' step get the overlay source."""
        base = [_step("a")]
        composite = {
            "id": "switch-1",
            "type": "switch",
            "expression": "{{inputs.x}}",
            "cases": {"one": [_step("case-one")], "two": [_step("case-two")]},
            "default": [_step("default-z")],
        }
        overlay = Overlay(
            id="ov", extends="wf", priority=10,
            edits=[OverlayEdit("insert_before", "a", composite)],
        )
        _steps, attribution = merge_steps(
            base, [_layer(overlay, "project:ov")]
        )
        assert attribution == [
            ComposedStep("switch-1", "project:ov"),
            ComposedStep("default-z", "project:ov"),
            ComposedStep("case-one", "project:ov"),
            ComposedStep("case-two", "project:ov"),
            ComposedStep("a", "base"),
        ]

    def test_merge_replace_flat_with_composite_attribution(self):
        """Replacing a flat step with a composite step attributes all nested children."""
        base = [_step("a")]
        composite = {
            "id": "if-1",
            "type": "if",
            "condition": "true",
            "then": [_step("inner-x"), _step("inner-y")],
        }
        overlay = Overlay(
            id="ov", extends="wf", priority=10,
            edits=[OverlayEdit("replace", "a", composite)],
        )
        _steps, attribution = merge_steps(
            base, [_layer(overlay, "project:ov")]
        )
        assert attribution == [
            ComposedStep("if-1", "project:ov"),
            ComposedStep("inner-x", "project:ov"),
            ComposedStep("inner-y", "project:ov"),
        ]

    def test_merge_remove_composite_step_cleans_nested_sources(self):
        """Removing a composite step also cleans its nested children from sources."""
        base = [
            {
                "id": "if-1",
                "type": "if",
                "condition": "true",
                "then": [_step("then-a")],
                "else": [_step("else-b")],
            },
            _step("a"),
        ]
        overlay = Overlay(
            id="ov", extends="wf", priority=10,
            edits=[OverlayEdit("remove", "if-1")],
        )
        steps, attribution = merge_steps(
            base, [_layer(overlay, "project:ov")]
        )
        assert [s["id"] for s in steps] == ["a"]
        assert attribution == [ComposedStep("a", "base")]

    def test_merge_insert_deeply_nested_composite_attribution(self):
        """Deep nesting (if inside while) gets the overlay source at every level."""
        base = [_step("a")]
        inner_if = {
            "id": "inner-if",
            "type": "if",
            "condition": "true",
            "then": [_step("deep-x")],
        }
        composite = {
            "id": "while-1",
            "type": "while",
            "condition": "true",
            "steps": [inner_if],
        }
        overlay = Overlay(
            id="ov", extends="wf", priority=10,
            edits=[OverlayEdit("insert_after", "a", composite)],
        )
        _steps, attribution = merge_steps(
            base, [_layer(overlay, "project:ov")]
        )
        assert attribution == [
            ComposedStep("a", "base"),
            ComposedStep("while-1", "project:ov"),
            ComposedStep("inner-if", "project:ov"),
            ComposedStep("deep-x", "project:ov"),
        ]


class TestValidateEdits:
    """Edit validation against known base step IDs."""

    def test_valid_edits(self):
        edits = [
            OverlayEdit("insert_after", "a", _step("new")),
            OverlayEdit("remove", "b"),
        ]
        assert validate_edits(edits, {"a", "b"}) == []

    def test_invalid_anchor(self):
        edits = [OverlayEdit("insert_after", "missing", _step("new"))]
        errors = validate_edits(edits, {"a"})
        assert any("missing" in e for e in errors)

    def test_step_id_contains_colon(self):
        edits = [OverlayEdit("insert_after", "a", _step("bad:id"))]
        errors = validate_edits(edits, {"a"})
        assert any("':'" in e for e in errors)

    def test_remove_requires_no_step(self):
        edits = [OverlayEdit("remove", "a", _step("extra"))]
        errors = validate_edits(edits, {"a"})
        assert len(errors) > 0


class TestMergeStepsAncestorConflicts:
    """merge_steps raises when two targeted anchors are in a parent/descendant relationship."""

    def _if_step(self, parent_id: str, child_id: str) -> dict[str, Any]:
        return {
            "id": parent_id,
            "type": "if",
            "condition": "true",
            "then": [_step(child_id)],
        }

    def test_remove_parent_and_insert_after_child_raises(self):
        """Removing a parent while inserting after its nested child is an anchor conflict."""
        parent_id = "if-step"
        child_id = "then-child"
        base = [self._if_step(parent_id, child_id)]
        overlay = Overlay(
            id="ov",
            extends="wf",
            priority=10,
            edits=[
                OverlayEdit("remove", parent_id),
                OverlayEdit("insert_after", child_id, _step("new-step")),
            ],
        )
        with pytest.raises(ValueError, match="ancestor"):
            merge_steps(base, [_layer(overlay, "project:ov")])

    def test_replace_parent_and_remove_child_raises(self):
        """Replacing a parent while also removing a nested child is an anchor conflict."""
        parent_id = "if-step"
        child_id = "then-child"
        base = [self._if_step(parent_id, child_id)]
        overlay = Overlay(
            id="ov",
            extends="wf",
            priority=10,
            edits=[
                OverlayEdit("replace", parent_id, _step("new-parent")),
                OverlayEdit("remove", child_id),
            ],
        )
        with pytest.raises(ValueError, match="ancestor"):
            merge_steps(base, [_layer(overlay, "project:ov")])

    def test_conflict_across_multiple_overlays_raises(self):
        """Conflict is detected even when conflicting anchors come from different overlays."""
        parent_id = "if-step"
        child_id = "then-child"
        base = [self._if_step(parent_id, child_id)]
        overlay_a = Overlay(
            id="ov-a",
            extends="wf",
            priority=5,
            edits=[OverlayEdit("remove", parent_id)],
        )
        overlay_b = Overlay(
            id="ov-b",
            extends="wf",
            priority=10,
            edits=[OverlayEdit("insert_after", child_id, _step("new-step"))],
        )
        with pytest.raises(ValueError, match="ancestor"):
            merge_steps(
                base,
                [_layer(overlay_a, "project:ov-a"), _layer(overlay_b, "project:ov-b")],
            )

    def test_sibling_anchors_not_conflicting(self):
        """Anchors in sibling branches (not ancestor/descendant) are allowed."""
        base = [
            {
                "id": "if-step",
                "type": "if",
                "condition": "true",
                "then": [_step("then-child")],
                "else": [_step("else-child")],
            }
        ]
        overlay = Overlay(
            id="ov",
            extends="wf",
            priority=10,
            edits=[
                OverlayEdit("insert_after", "then-child", _step("after-then")),
                OverlayEdit("insert_after", "else-child", _step("after-else")),
            ],
        )
        # Should not raise — the two anchors are siblings, not ancestor/descendant.
        steps, _ = merge_steps(base, [_layer(overlay, "project:ov")])
        step_ids = [s.get("id") for s in steps[0]["then"]] + [s.get("id") for s in steps[0]["else"]]
        assert "after-then" in step_ids
        assert "after-else" in step_ids

    def test_single_anchor_not_conflicting(self):
        """A single anchor is never in conflict with itself."""
        parent_id = "if-step"
        child_id = "then-child"
        base = [self._if_step(parent_id, child_id)]
        overlay = Overlay(
            id="ov",
            extends="wf",
            priority=10,
            edits=[OverlayEdit("remove", parent_id)],
        )
        steps, _ = merge_steps(base, [_layer(overlay, "project:ov")])
        assert steps == []

    def test_child_not_targeted_no_conflict(self):
        """Targeting a parent alone (child not in any edit) is allowed."""
        parent_id = "if-step"
        child_id = "then-child"
        base = [self._if_step(parent_id, child_id), _step("other")]
        overlay = Overlay(
            id="ov",
            extends="wf",
            priority=10,
            edits=[
                OverlayEdit("remove", parent_id),
                OverlayEdit("insert_after", "other", _step("new-step")),
            ],
        )
        # "other" is not inside "if-step", so no ancestor conflict.
        steps, _ = merge_steps(base, [_layer(overlay, "project:ov")])
        assert [s["id"] for s in steps] == ["other", "new-step"]

    def test_insert_only_on_ancestor_and_descendant_not_conflicting(self):
        """insert_after on both a parent and its nested child is valid and order-independent."""
        parent_id = "if-step"
        child_id = "then-child"
        base = [self._if_step(parent_id, child_id)]
        overlay = Overlay(
            id="ov",
            extends="wf",
            priority=10,
            edits=[
                OverlayEdit("insert_after", parent_id, _step("after-parent")),
                OverlayEdit("insert_after", child_id, _step("after-child")),
            ],
        )
        # Should not raise — inserts leave the ancestor intact.
        steps, attribution = merge_steps(base, [_layer(overlay, "project:ov")])
        # "after-parent" is inserted at the top level after the if-step.
        assert [s["id"] for s in steps] == [parent_id, "after-parent"]
        # "after-child" is inserted inside the then list.
        then_ids = [s["id"] for s in steps[0]["then"]]
        assert then_ids == [child_id, "after-child"]


class TestMergeStepsIdCollision:
    """merge_steps is deterministic when a replacement reuses a base step ID."""

    def test_replace_with_reused_id_does_not_affect_original(self):
        """Replacing A with new_step(id=B) must not interfere with editing original B.

        Before the fix, the remove-B anchor group would find the replacement step
        (which now has id='b') instead of the original 'b' step, producing a
        different result depending on dict iteration order.
        """
        base = [_step("a"), _step("b"), _step("c")]
        overlay = Overlay(
            id="ov",
            extends="wf",
            priority=10,
            edits=[
                # Replace "a" with a new step that reuses id "b".
                OverlayEdit("replace", "a", {**_step("b"), "command": "speckit.replaced"}),
                # Remove the original "b".
                OverlayEdit("remove", "b"),
            ],
        )
        steps, attribution = merge_steps(base, [_layer(overlay, "project:ov")])
        # The original "b" is removed; the replacement (also id="b") survives.
        # "c" is untouched.
        assert len(steps) == 2
        remaining_ids = [s["id"] for s in steps]
        assert remaining_ids == ["b", "c"]
        # The surviving "b" step is the replacement (has the custom command).
        assert steps[0]["command"] == "speckit.replaced"
        # Attribution for the surviving replacement "b" must not be "unknown".
        # Previously, removing original "b" would pop sources["b"], erasing the
        # attribution recorded for the replacement step (regression guard for the
        # _remove_sources_recursively-in-remove-branch bug).
        sources = {cs.step_id: cs.source for cs in attribution}
        assert sources.get("b") == "project:ov", (
            f"expected 'project:ov' but got {sources.get('b')!r}"
        )
