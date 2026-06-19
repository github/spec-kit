"""SemVer parsing and constraint evaluation, built on ``packaging`` (already a dependency)."""
from __future__ import annotations

import re

from packaging.specifiers import InvalidSpecifier, SpecifierSet
from packaging.version import InvalidVersion, Version

from .. import BundlerError

# Common SemVer prerelease spellings (``1.2.3-rc1``, ``1.2.3-alpha.1``) that
# PEP 440 / ``packaging`` rejects verbatim. Normalized to PEP 440 before
# parsing so prerelease versions validate consistently (mirrors
# ``specify_cli._version._normalize_tag``).
_PRERELEASE_PATTERN = re.compile(
    r"^([0-9]+\.[0-9]+\.[0-9]+)[-.]?(alpha|beta|a|b|rc)[-.]?([0-9]+)(.*)$",
    flags=re.IGNORECASE,
)


def _normalize_semver(value: str) -> str:
    """Normalize common SemVer prerelease spellings into PEP 440 text."""
    text = str(value)
    normalized = text[1:] if text.startswith("v") else text
    match = _PRERELEASE_PATTERN.match(normalized)
    if match is None:
        return normalized
    base, label, number, rest = match.groups()
    pep440_label = {"alpha": "a", "beta": "b"}.get(label.lower(), label.lower())
    return f"{base}{pep440_label}{number}{rest}"


def parse_version(value: str) -> Version:
    """Parse a version string into a comparable :class:`Version`."""
    try:
        return Version(_normalize_semver(value))
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
        Version(_normalize_semver(value))
        return True
    except (InvalidVersion, TypeError):
        return False
