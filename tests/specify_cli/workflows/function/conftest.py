"""Fixtures for workflow function tests."""

from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _reset_custom_functions(reset_custom_functions):
    """Every function test starts and ends with only built-in filters."""
