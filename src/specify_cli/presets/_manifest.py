"""Preset manifest validation and domain errors (private implementation)."""

import hashlib
import os
import re
from pathlib import Path
from typing import Any, Dict, List

import yaml
from packaging import version as pkg_version
from packaging.specifiers import InvalidSpecifier, SpecifierSet


class PresetError(Exception):
    """Base exception for preset-related errors."""
    pass


class PresetValidationError(PresetError):
    """Raised when preset manifest validation fails."""
    pass


class PresetCompatibilityError(PresetError):
    """Raised when preset is incompatible with current environment."""
    pass


VALID_PRESET_TEMPLATE_TYPES = {"template", "command", "script"}
VALID_PRESET_STRATEGIES = {"replace", "prepend", "append", "wrap"}
# Scripts only support replace and wrap (prepend/append don't make semantic sense for executable code)
VALID_SCRIPT_STRATEGIES = {"replace", "wrap"}


class PresetManifest:
    """Represents and validates a preset manifest (preset.yml)."""

    SCHEMA_VERSION = "1.0"
    REQUIRED_FIELDS = ["schema_version", "preset", "requires", "provides"]

    def __init__(self, manifest_path: Path):
        """Load and validate preset manifest.

        Args:
            manifest_path: Path to preset.yml file

        Raises:
            PresetValidationError: If manifest is invalid
        """
        self.path = manifest_path
        self.data = self._load_yaml(manifest_path)
        self._validate()

    def _load_yaml(self, path: Path) -> dict:
        """Load YAML file safely."""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise PresetValidationError(f"Invalid YAML in {path}: {e}")
        except FileNotFoundError:
            raise PresetValidationError(f"Manifest not found: {path}")
        except UnicodeDecodeError as e:
            raise PresetValidationError(
                f"Manifest is not valid UTF-8: {path} ({e.reason} at byte {e.start})"
            )
        except OSError as e:
            raise PresetValidationError(f"Could not read manifest {path}: {e}")
        if data is None:
            return {}
        if not isinstance(data, dict):
            raise PresetValidationError(
                f"Manifest must be a YAML mapping, got {type(data).__name__}: {path}"
            )
        return data

    def _validate(self):
        """Validate manifest structure and required fields."""
        # Check required top-level fields
        for field in self.REQUIRED_FIELDS:
            if field not in self.data:
                raise PresetValidationError(f"Missing required field: {field}")

        # Validate schema version
        if self.data["schema_version"] != self.SCHEMA_VERSION:
            raise PresetValidationError(
                f"Unsupported schema version: {self.data['schema_version']} "
                f"(expected {self.SCHEMA_VERSION})"
            )

        for section in ("preset", "requires", "provides"):
            if not isinstance(self.data[section], dict):
                raise PresetValidationError(
                    f"Invalid {section}: expected a mapping"
                )

        # Validate preset metadata
        pack = self.data["preset"]
        # Check presence AND type: the format/version checks below feed these
        # values straight to ``re.match`` and ``packaging.Version``, both of
        # which raise a bare TypeError on a non-string. YAML makes that an easy
        # authoring slip -- unquoted ``version: 1.0`` parses as a float and
        # ``id: 2`` as an int -- and TypeError is not a PresetValidationError,
        # so it escapes every caller that already handles a malformed manifest
        # (see list_installed()'s "Corrupted preset" fallback, which catches
        # PresetValidationError only, making one bad preset exit ``specify
        # preset list`` with a raw traceback and hide the healthy ones).
        # Mirrors the sibling IntegrationDescriptor, which already type-checks
        # the same four fields.
        for field in ["id", "name", "version", "description"]:
            if field not in pack:
                raise PresetValidationError(f"Missing preset.{field}")
            if not isinstance(pack[field], str):
                raise PresetValidationError(
                    f"Invalid preset.{field}: expected a string, "
                    f"got {type(pack[field]).__name__}"
                )

        # Validate pack ID format
        if not re.match(r'^[a-z0-9-]+$', pack["id"]):
            raise PresetValidationError(
                f"Invalid preset ID '{pack['id']}': "
                "must be lowercase alphanumeric with hyphens only"
            )

        # Validate semantic version
        try:
            pkg_version.Version(pack["version"])
        except pkg_version.InvalidVersion:
            raise PresetValidationError(f"Invalid version: {pack['version']}")

        # Validate requires section
        requires = self.data["requires"]
        if "speckit_version" not in requires:
            raise PresetValidationError("Missing requires.speckit_version")
        # Presence alone is not enough: check_compatibility() feeds this value to
        # ``SpecifierSet(required)``, guarded only by ``except InvalidSpecifier``,
        # which a non-string escapes two different ways. A float/int/bool/None
        # raises TypeError from the constructor, while a list or dict is an
        # *iterable*, so SpecifierSet accepts it and the failure surfaces much
        # later as ``AttributeError: 'str' object has no attribute 'filter'`` from
        # inside .contains(). Neither is a PresetCompatibilityError, so both
        # bypass the CLI's "Compatibility Error" handler and exit 1 with a raw
        # traceback naming no field. An unquoted ``speckit_version: 1.0`` is an
        # easy YAML slip. Mirrors the sibling IntegrationDescriptor, which already
        # requires a non-empty string here.
        if (
            not isinstance(requires["speckit_version"], str)
            or not requires["speckit_version"].strip()
        ):
            raise PresetValidationError(
                "Invalid requires.speckit_version: expected a non-empty string, "
                f"got {type(requires['speckit_version']).__name__}"
            )

        # Validate the optional extension dependency list. A preset that
        # overrides commands calling into an extension is inert without it, and
        # until now the only place that could be said was the README -- see
        # issue #4231. Absent means "no dependencies", so every existing preset
        # stays valid.
        if "extensions" in requires:
            self._validate_requires_extensions(requires["extensions"])

        # Validate provides section
        provides = self.data["provides"]
        if "templates" not in provides:
            raise PresetValidationError(
                "Preset must provide at least one template"
            )

        # Validate templates. Guard the container and each entry's shape so a
        # malformed third-party preset.yml (e.g. ``templates: 5`` or
        # ``templates: [null]``) raises a clean PresetValidationError the
        # install handler already catches, instead of a raw TypeError
        # ('int'/'NoneType' object is not iterable) that escapes to an
        # unhandled traceback. Mirrors the sibling ExtensionManifest guards.
        #
        # Order matters: the container's TYPE is checked before its emptiness,
        # so a FALSY non-list (``templates: 0``/``false``/``null``/``''``/``{}``)
        # reports the accurate type error rather than the misleading "must
        # provide at least one template". An empty list still reports the
        # latter, since that genuinely is a list with no templates.
        templates = provides["templates"]
        if not isinstance(templates, list):
            raise PresetValidationError(
                "Invalid provides.templates: expected a list"
            )
        if not templates:
            raise PresetValidationError(
                "Preset must provide at least one template"
            )
        seen_name_types: set[tuple[str, str]] = set()
        for tmpl in templates:
            if not isinstance(tmpl, dict):
                raise PresetValidationError(
                    "Each template entry in 'provides.templates' must be a mapping"
                )
            if "type" not in tmpl or "name" not in tmpl or "file" not in tmpl:
                raise PresetValidationError(
                    "Template missing 'type', 'name', or 'file'"
                )

            # 'name' feeds re.match and 'file' feeds os.path.normpath below;
            # both raise a bare TypeError on a non-string, which is not a
            # PresetValidationError and so escapes the callers that handle a
            # malformed manifest. The sibling extension manifest already
            # rejects a non-string command 'file' via
            # relative_extension_path_violation().
            for field in ("type", "name", "file"):
                if not isinstance(tmpl[field], str):
                    raise PresetValidationError(
                        f"Invalid template {field}: expected a string, "
                        f"got {type(tmpl[field]).__name__}"
                    )

            if tmpl["type"] not in VALID_PRESET_TEMPLATE_TYPES:
                raise PresetValidationError(
                    f"Invalid template type '{tmpl['type']}': "
                    f"must be one of {sorted(VALID_PRESET_TEMPLATE_TYPES)}"
                )

            # PresetResolver._manifest_declared_template returns the first
            # 'provides.templates' entry matching a given (name, type) pair, so
            # a later duplicate would be silently unreachable while still being
            # counted by PresetManifest.templates. Reject at validation time
            # instead, mirroring the sibling fix for ExtensionManifest's
            # provides.templates/scripts (#4016).
            name_type = (tmpl["name"], tmpl["type"])
            if name_type in seen_name_types:
                raise PresetValidationError(
                    f"Duplicate template name '{tmpl['name']}' of type "
                    f"'{tmpl['type']}' in 'provides.templates'"
                )
            seen_name_types.add(name_type)

            # Validate file path safety: must be relative, no parent traversal
            file_path = tmpl["file"]
            normalized = os.path.normpath(file_path)
            if os.path.isabs(normalized) or normalized.startswith(".."):
                raise PresetValidationError(
                    f"Invalid template file path '{file_path}': "
                    "must be a relative path within the preset directory"
                )

            # Validate strategy field (optional, defaults to "replace")
            strategy = tmpl.get("strategy", "replace")
            if not isinstance(strategy, str):
                raise PresetValidationError(
                    f"Invalid strategy value: must be a string, "
                    f"got {type(strategy).__name__}"
                )
            strategy = strategy.lower()
            # Persist normalized value so downstream code sees lowercase
            if "strategy" in tmpl:
                tmpl["strategy"] = strategy
            if strategy not in VALID_PRESET_STRATEGIES:
                raise PresetValidationError(
                    f"Invalid strategy '{strategy}': "
                    f"must be one of {sorted(VALID_PRESET_STRATEGIES)}"
                )
            if tmpl["type"] == "script" and strategy not in VALID_SCRIPT_STRATEGIES:
                raise PresetValidationError(
                    f"Invalid strategy '{strategy}' for script: "
                    f"scripts only support {sorted(VALID_SCRIPT_STRATEGIES)}"
                )

            # Validate template name format
            if tmpl["type"] == "command":
                # Commands use dot notation (e.g. speckit.specify)
                if not re.match(r'^[a-z0-9.-]+$', tmpl["name"]):
                    raise PresetValidationError(
                        f"Invalid command name '{tmpl['name']}': "
                        "must be lowercase alphanumeric with hyphens and dots only"
                    )
            else:
                if not re.match(r'^[a-z0-9-]+$', tmpl["name"]):
                    raise PresetValidationError(
                        f"Invalid template name '{tmpl['name']}': "
                        "must be lowercase alphanumeric with hyphens only"
                    )

    @property
    def id(self) -> str:
        """Get preset ID."""
        return self.data["preset"]["id"]

    @property
    def name(self) -> str:
        """Get preset name."""
        return self.data["preset"]["name"]

    @property
    def version(self) -> str:
        """Get preset version."""
        return self.data["preset"]["version"]

    @property
    def description(self) -> str:
        """Get preset description."""
        return self.data["preset"]["description"]

    @property
    def author(self) -> str:
        """Get preset author."""
        return self.data["preset"].get("author", "")

    @staticmethod
    def _validate_requires_extensions(declared: Any) -> None:
        """Validate the optional ``requires.extensions`` list.

        Accepts either a bare extension id or a mapping carrying an optional
        version specifier and an optional ``required`` flag:

        .. code-block:: yaml

            requires:
              extensions:
                - speckit-inventory
                - id: other-ext
                  version: ">=1.2.0"
                  required: false

        Raises:
            PresetValidationError: If the list or any entry is malformed.
        """
        if not isinstance(declared, list):
            raise PresetValidationError(
                "Invalid requires.extensions: expected a list, "
                f"got {type(declared).__name__}"
            )

        for index, entry in enumerate(declared):
            label = f"requires.extensions[{index}]"

            if isinstance(entry, str):
                entry = {"id": entry}
            elif not isinstance(entry, dict):
                raise PresetValidationError(
                    f"Invalid {label}: expected a string or a mapping, "
                    f"got {type(entry).__name__}"
                )

            if "id" not in entry:
                raise PresetValidationError(f"Missing {label}.id")
            extension_id = entry["id"]
            if not isinstance(extension_id, str):
                raise PresetValidationError(
                    f"Invalid {label}.id: expected a string, "
                    f"got {type(extension_id).__name__}"
                )
            # Same id shape the extension loader enforces, so a dependency can
            # never name something that could not be installed in the first
            # place. fullmatch rather than match with an anchored pattern: `$`
            # also matches before a trailing newline, so "demo-ext\n" would
            # otherwise validate here while PresetResolver._is_safe_registry_id
            # (which uses fullmatch) rejects it, and the newline would land in
            # a suggested command.
            if not re.fullmatch(r'[a-z0-9-]+', extension_id):
                raise PresetValidationError(
                    f"Invalid {label}.id {extension_id!r}: "
                    "must be lowercase alphanumeric with hyphens only"
                )

            if "version" in entry:
                constraint = entry["version"]
                # Mirrors the requires.speckit_version reasoning: a non-string
                # escapes InvalidSpecifier two ways -- scalars raise TypeError
                # from the constructor, and a list/dict is iterable so it
                # constructs and only fails later inside .contains().
                if not isinstance(constraint, str) or not constraint.strip():
                    raise PresetValidationError(
                        f"Invalid {label}.version: expected a non-empty string, "
                        f"got {type(constraint).__name__}"
                    )
                try:
                    SpecifierSet(constraint)
                except InvalidSpecifier:
                    raise PresetValidationError(
                        f"Invalid {label}.version '{constraint}': "
                        "not a valid version specifier"
                    )

            if "required" in entry and not isinstance(entry["required"], bool):
                raise PresetValidationError(
                    f"Invalid {label}.required: expected a boolean, "
                    f"got {type(entry['required']).__name__}"
                )

    @property
    def requires_speckit_version(self) -> str:
        """Get required spec-kit version range."""
        return self.data["requires"]["speckit_version"]

    @property
    def requires_extensions(self) -> List[Dict[str, Any]]:
        """Get declared extension dependencies, normalized to mappings.

        Returns:
            One entry per dependency with ``id``, ``version`` (``None`` when
            unconstrained), and ``required`` (defaulting to ``True``). Empty
            when the manifest declares no dependencies.
        """
        declared = self.data["requires"].get("extensions")
        if not isinstance(declared, list):
            return []

        normalized: List[Dict[str, Any]] = []
        for entry in declared:
            if isinstance(entry, str):
                entry = {"id": entry}
            if not isinstance(entry, dict) or not isinstance(entry.get("id"), str):
                continue
            normalized.append(
                {
                    "id": entry["id"],
                    "version": entry.get("version"),
                    "required": entry.get("required", True),
                }
            )
        return normalized

    @property
    def templates(self) -> List[Dict[str, Any]]:
        """Get list of provided templates."""
        return self.data["provides"]["templates"]

    @property
    def tags(self) -> List[str]:
        """Get preset tags."""
        return self.data.get("tags", [])

    def get_hash(self) -> str:
        """Calculate SHA256 hash of manifest file."""
        h = hashlib.sha256()
        with open(self.path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        return f"sha256:{h.hexdigest()}"
