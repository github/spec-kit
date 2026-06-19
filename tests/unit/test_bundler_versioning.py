"""Unit tests for version parsing and constraint satisfaction (FR-016 gate)."""
from __future__ import annotations

import pytest

from specify_cli.bundler import BundlerError
from specify_cli.bundler.lib.versioning import is_semver, satisfies


@pytest.mark.parametrize("value,expected", [
    ("1.0.0", True),
    ("0.11.2", True),
    ("1.2.3-rc1", True),
    ("not-a-version", False),
    ("", False),
])
def test_is_semver(value, expected):
    assert is_semver(value) is expected


@pytest.mark.parametrize("installed,constraint,ok", [
    ("0.11.2", ">=0.1.0", True),
    ("0.11.2", ">=1.0.0", False),
    ("1.0.0", ">=1.0.0,<2.0.0", True),
    ("2.0.0", ">=1.0.0,<2.0.0", False),
    ("1.5.0", "", True),  # empty constraint is permissive
])
def test_satisfies(installed, constraint, ok):
    assert satisfies(installed, constraint) is ok


def test_invalid_constraint_raises():
    with pytest.raises(BundlerError):
        satisfies("1.0.0", ">>bad")
