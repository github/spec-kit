"""Bundle manifest model (``bundle.yml``) — parsing and structural normalization.

Mirrors ``contracts/bundle-manifest.schema.md``. Structural validation (shape,
required fields, enum/semver checks) lives here; *reference* resolution against a
catalog stack lives in the validator/resolver services.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .. import BundlerError
from ..lib.versioning import is_semver
from ..lib.yamlio import load_yaml

SUPPORTED_SCHEMA_VERSIONS = {"1.0"}
PRESET_STRATEGIES = {"replace", "prepend", "append", "wrap"}

COMPONENT_KINDS = ("extensions", "presets", "steps", "workflows")

# A bundle id must be a filesystem-safe slug: it is interpolated into artifact
# filenames (e.g. ``<id>-<version>.zip``), so path separators or traversal
# segments must never appear.
_SAFE_BUNDLE_ID = re.compile(r"^[a-z0-9](?:[a-z0-9._-]*[a-z0-9])?$")


@dataclass(frozen=True)
class ComponentRef:
    """A pointer to an existing Spec Kit primitive a bundle installs."""

    kind: str  # one of COMPONENT_KINDS (singularized concept), stored plural-of-origin
    id: str
    version: str | None = None
    source: str | None = None
    priority: int | None = None  # presets only
    strategy: str | None = None  # presets only

    def label(self) -> str:
        return f"{self.kind[:-1]}:{self.id}@{self.version or 'unpinned'}"


@dataclass(frozen=True)
class IntegrationRef:
    id: str


@dataclass(frozen=True)
class Requires:
    speckit_version: str
    tools: tuple[str, ...] = ()
    mcp: tuple[str, ...] = ()


@dataclass(frozen=True)
class BundleMeta:
    id: str
    name: str
    version: str
    role: str
    description: str
    author: str
    license: str


@dataclass
class BundleManifest:
    schema_version: str
    bundle: BundleMeta
    requires: Requires
    integration: IntegrationRef | None = None
    extensions: list[ComponentRef] = field(default_factory=list)
    presets: list[ComponentRef] = field(default_factory=list)
    steps: list[ComponentRef] = field(default_factory=list)
    workflows: list[ComponentRef] = field(default_factory=list)
    tags: tuple[str, ...] = ()
    source_path: Path | None = None

    @property
    def components(self) -> list[ComponentRef]:
        """All installable component references in deterministic order."""
        return [*self.extensions, *self.presets, *self.steps, *self.workflows]

    # -- construction ---------------------------------------------------------

    @classmethod
    def from_file(cls, path: Path) -> "BundleManifest":
        data = load_yaml(path)
        manifest = cls.from_dict(data)
        manifest.source_path = Path(path)
        return manifest

    @classmethod
    def from_dict(cls, data: Any) -> "BundleManifest":
        if not isinstance(data, dict):
            raise BundlerError("Manifest must be a YAML mapping at the top level.")

        schema_version = str(data.get("schema_version", "")).strip()

        bundle_raw = data.get("bundle")
        if not isinstance(bundle_raw, dict):
            raise BundlerError("Manifest is missing the required 'bundle' mapping.")
        meta = BundleMeta(
            id=str(bundle_raw.get("id", "")).strip(),
            name=str(bundle_raw.get("name", "")).strip(),
            version=str(bundle_raw.get("version", "")).strip(),
            role=str(bundle_raw.get("role", "")).strip(),
            description=str(bundle_raw.get("description", "")).strip(),
            author=str(bundle_raw.get("author", "")).strip(),
            license=str(bundle_raw.get("license", "")).strip(),
        )

        requires_raw = data.get("requires")
        if requires_raw is None:
            requires_raw = {}
        elif not isinstance(requires_raw, dict):
            raise BundlerError("'requires' must be a mapping when present.")
        requires = Requires(
            speckit_version=str(requires_raw.get("speckit_version", "")).strip(),
            tools=_parse_str_list(requires_raw.get("tools"), "requires.tools"),
            mcp=_parse_str_list(requires_raw.get("mcp"), "requires.mcp"),
        )

        integration = None
        integration_raw = data.get("integration")
        # Mirror the requires/provides guards above: a present-but-non-mapping
        # 'integration' (e.g. a bare string "copilot") was silently dropped,
        # leaving the bundle wrongly integration-agnostic. Reject it instead.
        if integration_raw is not None and not isinstance(integration_raw, dict):
            raise BundlerError("'integration' must be a mapping when present.")
        if isinstance(integration_raw, dict) and integration_raw.get("id"):
            integration = IntegrationRef(id=str(integration_raw["id"]).strip())

        provides = data.get("provides")
        if provides is None:
            provides = {}
        elif not isinstance(provides, dict):
            raise BundlerError("'provides' must be a mapping when present.")

        tags_raw = data.get("tags")
        if tags_raw is None:
            tags_raw = []
        else:
            tags_raw = _parse_str_list(tags_raw, "tags")

        manifest = cls(
            schema_version=schema_version,
            bundle=meta,
            requires=requires,
            integration=integration,
            extensions=_parse_refs("extensions", provides.get("extensions")),
            presets=_parse_refs("presets", provides.get("presets")),
            steps=_parse_refs("steps", provides.get("steps")),
            workflows=_parse_refs("workflows", provides.get("workflows")),
            tags=tuple(str(t) for t in tags_raw),
        )
        return manifest

    # -- structural validation ------------------------------------------------

    def structural_errors(self) -> list[str]:
        """Return a list of human-readable structural problems (empty == valid)."""
        errors: list[str] = []

        if self.schema_version not in SUPPORTED_SCHEMA_VERSIONS:
            errors.append(
                f"schema_version '{self.schema_version or '<missing>'}' is not supported "
                f"(supported: {sorted(SUPPORTED_SCHEMA_VERSIONS)})."
            )

        required = {
            "bundle.id": self.bundle.id,
            "bundle.name": self.bundle.name,
            "bundle.version": self.bundle.version,
            "bundle.role": self.bundle.role,
            "bundle.description": self.bundle.description,
            "bundle.author": self.bundle.author,
            "bundle.license": self.bundle.license,
            "requires.speckit_version": self.requires.speckit_version,
        }
        for field_path, value in required.items():
            if not value:
                errors.append(f"Missing required field: {field_path}.")

        if self.bundle.version and not is_semver(self.bundle.version):
            errors.append(f"bundle.version '{self.bundle.version}' is not valid semver.")

        if self.bundle.id and not _SAFE_BUNDLE_ID.match(self.bundle.id):
            errors.append(
                f"bundle.id '{self.bundle.id}' must be a slug "
                "(lowercase letters, digits, '.', '_', '-'; no path separators)."
            )

        for ref in self.components:
            if not ref.id:
                errors.append(f"A {ref.kind[:-1]} entry is missing its 'id'.")
            if ref.kind != "steps" and not ref.version:
                errors.append(
                    f"{ref.kind[:-1]} '{ref.id or '<unknown>'}' must be pinned to a 'version'."
                )
            if ref.version and not is_semver(ref.version):
                errors.append(
                    f"{ref.kind[:-1]} '{ref.id}' has invalid version '{ref.version}'."
                )

        for ref in self.presets:
            if ref.priority is None:
                errors.append(f"preset '{ref.id}' must declare an integer 'priority'.")
            if ref.strategy is None or ref.strategy not in PRESET_STRATEGIES:
                errors.append(
                    f"preset '{ref.id}' has invalid strategy '{ref.strategy}' "
                    f"(must be one of {sorted(PRESET_STRATEGIES)})."
                )

        return errors

    def is_agnostic(self) -> bool:
        """True when the bundle declares no integration (inherits the active one)."""
        return self.integration is None


def _parse_str_list(raw: Any, field_name: str) -> tuple[str, ...]:
    """Coerce a manifest list-of-strings field into a tuple of strings.

    Rejects a bare string/bytes (which would otherwise be iterated
    character-by-character) and any non-list/tuple, matching the manifest
    contract (``string[]``).
    """
    if raw is None:
        return ()
    if isinstance(raw, (str, bytes)) or not isinstance(raw, (list, tuple)):
        raise BundlerError(f"'{field_name}' must be a list of strings when present.")
    return tuple(str(item) for item in raw)


def _parse_refs(kind: str, raw: Any) -> list[ComponentRef]:
    if raw is None:
        return []
    if not isinstance(raw, list):
        raise BundlerError(f"provides.{kind} must be a list when present.")
    refs: list[ComponentRef] = []
    for item in raw:
        if not isinstance(item, dict):
            raise BundlerError(f"Each provides.{kind} entry must be a mapping.")
        priority = _parse_priority(kind, item.get("priority"))
        refs.append(
            ComponentRef(
                kind=kind,
                id=str(item.get("id", "")).strip(),
                version=(str(item["version"]).strip() if item.get("version") else None),
                source=(str(item["source"]).strip() if item.get("source") else None),
                priority=priority,
                strategy=(str(item["strategy"]).strip() if item.get("strategy") else None),
            )
        )
    return refs


def _parse_priority(kind: str, raw: Any) -> int | None:
    if raw is None:
        return None
    if isinstance(raw, bool) or not isinstance(raw, (int, str)):
        raise BundlerError(
            f"provides.{kind} priority must be an integer, got {raw!r}."
        )
    try:
        return int(raw)
    except (TypeError, ValueError):
        raise BundlerError(
            f"provides.{kind} priority must be an integer, got {raw!r}."
        ) from None
