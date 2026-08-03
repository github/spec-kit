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
    normalized = text[1:] if text[:1] in ("v", "V") else text
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


_SPECIFIER_CLAUSE = re.compile(r"^\s*(===|==|~=|!=|<=|>=|<|>)?\s*(.*?)\s*$")


def _normalize_constraint(value: str) -> str:
    """Normalize the version portion of each clause in a constraint string.

    ``packaging.SpecifierSet`` rejects SemVer prerelease spellings like
    ``>=1.2.3-rc1`` verbatim, even though :func:`parse_version` accepts the same
    spelling for installed versions. Normalize each comma-separated clause's
    version so prerelease handling is consistent across versions and constraints.
    """
    clauses = []
    for raw in str(value).split(","):
        if not raw.strip():
            continue
        match = _SPECIFIER_CLAUSE.match(raw)
        operator, version = match.groups()
        clauses.append(f"{operator or ''}{_normalize_semver(version)}")
    return ",".join(clauses)


def parse_constraint(value: str) -> SpecifierSet:
    """Parse a version constraint such as ``>=0.9.0`` into a :class:`SpecifierSet`."""
    try:
        return SpecifierSet(_normalize_constraint(value))
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


_SEMVER_RE = re.compile(
    r"^(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)"
    r"(?:-(?:(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)"
    r"(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?"
    r"(?:\+(?:[0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$"
)


def is_semver(value: str) -> bool:
    """Return True only for a full ``MAJOR.MINOR.PATCH`` SemVer string.

    Stricter than ``packaging.version.Version``, which also accepts partial
    versions like ``"1"`` or ``"1.0"``. An optional leading ``v`` or ``V`` is
    tolerated (mirrors ``_normalize_semver``).
    """
    text = str(value)
    core = text[1:] if text[:1] in ("v", "V") else text
    return bool(_SEMVER_RE.match(core))
