"""Plugin step — a named, no-op workflow extension point.

An upstream workflow declares a slot at the position where a downstream
project may extend it. The step ``id`` is the overlay anchor; ``name`` is only
the human-readable slot label. A project overlay fills the slot with the
standard ``replace`` operation on the slot step's ``id``. Unfilled slots are
skipped when the workflow runs.

Example YAML::

    # Upstream workflow
    - id: post-implement
      type: plugin
      name: post-implement

    # .specify/workflows/overlays/my-workflow/fill-post-implement.yml
    id: fill-post-implement
    extends: my-workflow
    edits:
      - replace: post-implement
        step:
          id: post-implement
          type: shell
          run: echo "Run project-specific checks"
"""

from __future__ import annotations

from typing import Any

from specify_cli.workflows.base import StepBase, StepContext, StepResult, StepStatus


class PluginStep(StepBase):
    """Provide a named workflow extension point that skips when unfilled."""

    type_key = "plugin"

    def execute(self, config: dict[str, Any], context: StepContext) -> StepResult:
        return StepResult(
            status=StepStatus.SKIPPED,
            output={"slot": config.get("name")},
        )

    def validate(self, config: dict[str, Any]) -> list[str]:
        errors = super().validate(config)
        name = config.get("name")
        if name is None:
            errors.append(
                f"Plugin step {config.get('id', '?')!r} requires a 'name' field "
                "(the slot label)."
            )
        elif not isinstance(name, str) or not name.strip():
            errors.append(
                f"Plugin step {config.get('id', '?')!r}: 'name' must be a "
                "non-blank string."
            )
        return errors
