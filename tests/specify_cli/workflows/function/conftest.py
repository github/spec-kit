"""Fixtures for workflow function tests.

The custom-filter table is process-global, so every test starts and ends with
only built-in filters registered.
"""

from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _reset_custom_filters():
    from specify_cli.workflows.expressions import unregister_custom_filters

    unregister_custom_filters()
    yield
    unregister_custom_filters()
