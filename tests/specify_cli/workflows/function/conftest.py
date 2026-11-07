"""Fixtures for workflow function tests.

The custom-filter table and synthetic modules are process-global, so every
test starts and ends with only built-in filters registered.
"""

from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _reset_custom_functions():
    from specify_cli.workflows.function.loader import _unload_custom_functions

    _unload_custom_functions()
    yield
    _unload_custom_functions()
