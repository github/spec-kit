"""SemVer parsing and constraint evaluation, built on ``packaging`` (already a dependency)."""
from __future__ import annotations

from packaging.specifiers import InvalidSpecifier, SpecifierSet
from packaging.version import InvalidVersion, Version

from .. import BundlerError


def parse_version(value: str) -> Version:
    """Parse a version string into a comparable :class:`Version`."""
    try:
        return Version(str(value))
    except InvalidVersion as exc:
        raise BundlerError(f"Invalid version '{value}': {exc}") from exc


def parse_constraint(value: str) -> SpecifierSet:
    """Parse a version constraint such as ``>=0.9.0`` into a :class:`SpecifierSet`."""
    try:
        return SpecifierSet(str(value))
    except InvalidSpecifier as exc:
        raise BundlerError(
            f"Invalid version constraint '{value}': {exc}"
        ) from exc


def satisfies(installed: str, constraint: str) -> bool:
    """Return True if *installed* satisfies *constraint* (e.g. ``">=0.9.0"``).

    Pre-releases are allowed so a dev/pre build of Spec Kit still counts.
    """
    spec = parse_constraint(constraint)
    version = parse_version(installed)
    return spec.contains(version, prereleases=True)


def is_semver(value: str) -> bool:
    """Return True if *value* parses as a valid version."""
    try:
        Version(str(value))
        return True
    except (InvalidVersion, TypeError):
        return False
