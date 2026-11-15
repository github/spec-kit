"""Shared per-step dispatch settings for the ``command`` and ``prompt`` steps.

``reasoning_effort`` and ``context_size`` resolve like ``model``: the step's
value, else the workflow default, evaluated as an expression. A result of
``None`` or ``""`` leaves the setting unset, so a step can opt out of an
inherited default. Set values are passed to the integration, which translates
them into its CLI's own arguments or rejects them; see
:func:`specify_cli.integrations.base.check_dispatch_settings`. This module
holds the parts of that contract the two steps must agree on: validation,
resolution, and naming where a rejected value came from.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from specify_cli.integrations.base import (
    DISPATCH_SETTINGS,
    DispatchSettingsError,
    dispatch_setting_value_error,
)
from specify_cli.workflows.base import StepContext
from specify_cli.workflows.expressions import evaluate_expression


@dataclass(frozen=True)
class ResolvedDispatchSettings:
    """Dispatch settings resolved for one step execution."""

    #: Set values only, in ``DISPATCH_SETTINGS`` order.
    settings: dict[str, str]

    #: Where each set value came from: ``"step"`` or ``"workflow.<name>"``.
    sources: dict[str, str]

    #: Every setting's value, or ``None`` when unset, for the step output.
    outputs: dict[str, str | None]


def _is_unset(value: Any) -> bool:
    return value is None or value == ""


def dispatch_setting_errors(config: dict[str, Any], label: str) -> list[str]:
    """Return validation errors for the step's literal dispatch settings.

    ``None`` and ``""`` inherit the workflow default, and an expression is
    checked once it is resolved. *label* names the step kind (``"Command"``).
    """
    errors: list[str] = []
    for name in DISPATCH_SETTINGS:
        value = config.get(name)
        if _is_unset(value) or (isinstance(value, str) and "{{" in value):
            continue
        problem = dispatch_setting_value_error(name, value)
        if problem is not None:
            errors.append(f"{label} step {config.get('id', '?')!r}: {problem}")
    return errors


def resolve_dispatch_settings(
    config: dict[str, Any], context: StepContext, label: str
) -> ResolvedDispatchSettings | str:
    """Resolve the step's dispatch settings, or return an error message.

    A missing, ``None``, or ``""`` step value inherits the workflow default,
    and a value containing ``{{`` is evaluated. A result of ``None`` or ``""``
    leaves the setting unset without a second fallback; any other result must
    be a valid setting value. An error names the value's source.
    """
    settings: dict[str, str] = {}
    sources: dict[str, str] = {}
    for name in DISPATCH_SETTINGS:
        value = config.get(name)
        source = "step"
        if _is_unset(value):
            value = getattr(context, f"default_{name}", None)
            source = f"workflow.{name}"
        from_expression = isinstance(value, str) and "{{" in value
        if from_expression:
            value = evaluate_expression(value, context)
        if _is_unset(value):
            continue
        problem = dispatch_setting_value_error(
            name, value, from_expression=from_expression
        )
        if problem is not None:
            return (
                f"{label} step {config.get('id', '?')!r}: {problem} "
                f"{dispatch_settings_attribution(name, {name: source})}"
            )
        settings[name] = value
        sources[name] = source
    return ResolvedDispatchSettings(
        settings=settings,
        sources=sources,
        outputs={name: settings.get(name) for name in DISPATCH_SETTINGS},
    )


def dispatch_settings_attribution(
    setting: str | None, sources: Mapping[str, str]
) -> str:
    """Return where a rejected dispatch setting came from, for an error message.

    Names the source of *setting* when it was set. Otherwise, for example for
    an integration's own error that names no setting, lists every set setting
    with its source. Returns ``""`` when no setting was set.
    """
    if setting in sources:
        return f"(set by {sources[setting]})"
    listed = "; ".join(
        f"{name} from {sources[name]}" for name in DISPATCH_SETTINGS if name in sources
    )
    return f"(settings: {listed})" if listed else ""


def dispatch_settings_failure(
    label: str,
    config: dict[str, Any],
    error: DispatchSettingsError,
    sources: Mapping[str, str],
) -> str:
    """Return the step error for a dispatch setting the integration rejected."""
    message = f"{label} step {config.get('id', '?')!r}: {error}"
    attribution = dispatch_settings_attribution(error.setting, sources)
    return f"{message} {attribution}" if attribution else message
