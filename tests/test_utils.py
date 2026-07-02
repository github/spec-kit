"""Tests for specify_cli._utils.run_command."""

from __future__ import annotations

import inspect

import pytest

from specify_cli import run_command


def test_run_command_rejects_shell_execution_compatibly():
    assert inspect.signature(run_command).parameters["shell"].default is False
    with pytest.raises(ValueError, match="does not support shell=True"):
        run_command(["echo", "blocked"], shell=True)  # noqa: S604
