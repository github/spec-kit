"""Tests for specify_cli._utils.run_command."""

from __future__ import annotations

import inspect

import pytest

from specify_cli import run_command


def test_run_command_has_no_shell_parameter():
    """The shell-injection surface is removed at the API level.

    ``run_command`` must never accept a ``shell`` parameter: the argv-list
    contract makes shell interpolation impossible by construction, and there is
    no runtime mode to re-enable it. Passing ``shell=`` is a hard ``TypeError``.
    """
    assert "shell" not in inspect.signature(run_command).parameters
    with pytest.raises(TypeError):
        run_command(["echo", "blocked"], shell=True)  # type: ignore[call-arg]  # noqa: S604
