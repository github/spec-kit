"""Unit tests for version parsing and constraint satisfaction (FR-016 gate)."""
from __future__ import annotations

import pytest

from specify_cli.bundler import BundlerError
from specify_cli.bundler.lib.versioning import is_semver, satisfies


@pytest.mark.parametrize("value,expected", [
    ("1.0.0", True),
    ("0.11.2", True),
    ("1.2.3-rc1", True),
    ("1.2.3-alpha1", True),
    ("1.2.3-beta2", True),
    ("v1.2.3", True),
    ("not-a-version", False),
    ("", False),
    # packaging.version.Version accepts these partial versions; SemVer must not.
    ("1", False),
    ("1.0", False),
    ("1.2.3.4", False),
])
def test_is_semver(value, expected):
    assert is_semver(value) is expected


@pytest.mark.parametrize("installed,constraint,ok", [
    ("0.11.2", ">=0.1.0", True),
    ("0.11.2", ">=1.0.0", False),
    ("1.0.0", ">=1.0.0,<2.0.0", True),
    ("2.0.0", ">=1.0.0,<2.0.0", False),
    ("1.5.0", "", True),  # empty constraint is permissive
    # Prerelease spellings normalize consistently for constraint checks.
    ("1.2.3-rc1", ">=1.2.0", True),
    ("1.2.3-alpha1", ">=2.0.0", False),
])
def test_satisfies(installed, constraint, ok):
    assert satisfies(installed, constraint) is ok


def test_invalid_constraint_raises():
    with pytest.raises(BundlerError):
        satisfies("1.0.0", ">>bad")


def test_uppercase_v_prefix_tolerated():
    # Mirrors specify_cli._version tag normalization (V -> v).
    assert is_semver("V1.2.3") is True
    assert satisfies("V1.2.3", ">=1.2.0") is True


@pytest.mark.parametrize("installed,constraint,ok", [
    # Prerelease spellings are now normalized inside constraints too, so a
    # constraint like ">=1.2.3-rc1" parses (previously raised InvalidSpecifier).
    ("1.2.3-rc2", ">=1.2.3-rc1", True),
    ("1.2.2", ">=1.2.3-rc1", False),
    ("1.5.0", ">=1.2.3-rc1,<2.0.0", True),
    ("1.2.3-beta.1", ">=1.2.3-alpha1", True),
])
def test_satisfies_prerelease_in_constraint(installed, constraint, ok):
    assert satisfies(installed, constraint) is ok


def test_parse_constraint_empty_is_permissive():
    from specify_cli.bundler.lib.versioning import parse_constraint

    assert str(parse_constraint("")) == ""


@pytest.mark.parametrize(
    "constraint",
    [
        ">=1.0.0\n<2.0.0\n",   # a YAML block literal, as loaded
        ">=1.0\n.0",
        "a\nb",
    ],
    ids=["yaml_block_literal", "split_version", "garbage"],
)
def test_constraint_with_an_embedded_newline_reports_a_bundler_error(constraint):
    """A clause containing a newline must be reported, not crash.

    `_SPECIFIER_CLAUSE` is anchored with `^`/`$` and `.` does not cross
    newlines, so such a clause does not match at all and `match.groups()`
    raised a raw `AttributeError` — escaping `parse_constraint`'s contract to
    surface bad input as a `BundlerError`. A YAML block literal reaches this
    with no exotic input at all:

        requires:
          speckit_version: |
            >=1.0.0
            <2.0.0
    """
    from specify_cli.bundler.lib.versioning import parse_constraint

    with pytest.raises(BundlerError, match="Invalid version constraint"):
        parse_constraint(constraint)


@pytest.mark.parametrize(
    "constraint,expected",
    [
        (">=1.0.0", ">=1.0.0"),
        (">=v1.0.0", ">=1.0.0"),
        ("~=1.2", "~=1.2"),
        (">=1.0.0\n", ">=1.0.0"),   # trailing newline is still stripped
        ("\n>=1.0.0", ">=1.0.0"),   # leading newline too
    ],
)
def test_valid_constraints_are_unaffected(constraint, expected):
    """Only clauses that genuinely fail to match change behaviour."""
    from specify_cli.bundler.lib.versioning import parse_constraint

    assert str(parse_constraint(constraint)) == expected
