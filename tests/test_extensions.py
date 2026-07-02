"""
Unit tests for the extension system.

Tests cover:
- Extension manifest validation
- Extension registry operations
- Extension manager installation/removal
- Command registration
- Catalog stack (multi-catalog support)
"""

import pytest
import json
import os
import platform
import tempfile
import shutil
import tomllib
from contextlib import contextmanager
from pathlib import Path
from datetime import datetime, timezone
from unittest.mock import MagicMock

from tests.conftest import strip_ansi
from specify_cli.extensions import (
    CatalogEntry,
    CORE_COMMAND_NAMES,
    DEFAULT_HOOK_PRIORITY,
    VALID_EFFECTS,
    ExtensionManifest,
    ExtensionRegistry,
    ExtensionManager,
    CommandRegistrar,
    HookExecutor,
    ExtensionCatalog,
    ExtensionError,
    ValidationError,
    CompatibilityError,
    normalize_priority,
)
from specify_cli._utils import version_satisfies

# Minimal valid ZIP (empty end-of-central-directory record). Passes
# zipfile.is_zipfile() so --from download tests exercise the content guard.
_MINIMAL_ZIP_BYTES = b"PK\x05\x06" + b"\x00" * 18


def can_create_symlink(tmp_path: Path) -> bool:
    """Return True when the current platform/user can create file symlinks."""
    target = tmp_path / "symlink-target.txt"
    link = tmp_path / "symlink-link.txt"
    target.write_text("ok", encoding="utf-8")
    try:
        os.symlink(target, link)
    except OSError:
        return False
    return link.is_symlink()


# ===== Fixtures =====

@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    tmpdir = tempfile.mkdtemp()
    yield Path(tmpdir)
    shutil.rmtree(tmpdir)


@pytest.fixture
def valid_manifest_data():
    """Valid extension manifest data."""
    return {
        "schema_version": "1.0",
        "extension": {
            "id": "test-ext",
            "name": "Test Extension",
            "version": "1.0.0",
            "description": "A test extension",
            "author": "Test Author",
            "repository": "https://github.com/test/test-ext",
            "license": "MIT",
        },
        "requires": {
            "speckit_version": ">=0.1.0",
            "commands": ["speckit.tasks"],
        },
        "provides": {
            "commands": [
                {
                    "name": "speckit.test-ext.hello",
                    "file": "commands/hello.md",
                    "description": "Test command",
                }
            ]
        },
        "hooks": {
            "after_tasks": {
                "command": "speckit.test-ext.hello",
                "optional": True,
                "prompt": "Run test?",
            }
        },
        "tags": ["testing", "example"],
    }


@pytest.fixture
def extension_dir(temp_dir, valid_manifest_data):
    """Create a complete extension directory structure."""
    ext_dir = temp_dir / "test-ext"
    ext_dir.mkdir()

    # Write manifest
    import yaml
    manifest_path = ext_dir / "extension.yml"
    with open(manifest_path, 'w') as f:
        yaml.dump(valid_manifest_data, f)

    # Create commands directory
    commands_dir = ext_dir / "commands"
    commands_dir.mkdir()

    # Write command file
    cmd_file = commands_dir / "hello.md"
    cmd_file.write_text("""---
description: "Test hello command"
---

# Test Hello Command

$ARGUMENTS
""")

    return ext_dir


@pytest.fixture
def project_dir(temp_dir):
    """Create a mock spec-kit project directory."""
    proj_dir = temp_dir / "project"
    proj_dir.mkdir()

    # Create .specify directory
    specify_dir = proj_dir / ".specify"
    specify_dir.mkdir()

    return proj_dir


# ===== normalize_priority Tests =====

class TestNormalizePriority:
    """Test normalize_priority helper function."""

    def test_valid_integer(self):
        """Test with valid integer priority."""
        assert normalize_priority(5) == 5
        assert normalize_priority(1) == 1
        assert normalize_priority(100) == 100

    def test_valid_string_number(self):
        """Test with string that can be converted to int."""
        assert normalize_priority("5") == 5
        assert normalize_priority("10") == 10

    def test_zero_returns_default(self):
        """Test that zero priority returns default."""
        assert normalize_priority(0) == 10
        assert normalize_priority(0, default=5) == 5

    def test_negative_returns_default(self):
        """Test that negative priority returns default."""
        assert normalize_priority(-1) == 10
        assert normalize_priority(-100, default=5) == 5

    def test_none_returns_default(self):
        """Test that None returns default."""
        assert normalize_priority(None) == 10
        assert normalize_priority(None, default=5) == 5

    def test_invalid_string_returns_default(self):
        """Test that non-numeric string returns default."""
        assert normalize_priority("invalid") == 10
        assert normalize_priority("abc", default=5) == 5

    def test_float_truncates(self):
        """Test that float is truncated to int."""
        assert normalize_priority(5.9) == 5
        assert normalize_priority(3.1) == 3

    def test_empty_string_returns_default(self):
        """Test that empty string returns default."""
        assert normalize_priority("") == 10

    def test_custom_default(self):
        """Test custom default value."""
        assert normalize_priority(None, default=20) == 20
        assert normalize_priority("invalid", default=1) == 1

    def test_boolean_returns_default(self):
        """Booleans fall back to the default rather than acting as int 0/1."""
        assert normalize_priority(True) == 10
        assert normalize_priority(False) == 10
        assert normalize_priority(True, default=5) == 5


# ===== ExtensionManifest Tests =====

class TestExtensionManifest:
    """Test ExtensionManifest validation and parsing."""

    def test_valid_manifest(self, extension_dir):
        """Test loading a valid manifest."""
        manifest_path = extension_dir / "extension.yml"
        manifest = ExtensionManifest(manifest_path)

        assert manifest.id == "test-ext"
        assert manifest.name == "Test Extension"
        assert manifest.version == "1.0.0"
        assert manifest.description == "A test extension"
        assert len(manifest.commands) == 1
        assert manifest.commands[0]["name"] == "speckit.test-ext.hello"

    def test_core_command_names_match_bundled_templates(self):
        """Core command reservations should stay aligned with bundled templates."""
        commands_dir = Path(__file__).resolve().parent.parent / "templates" / "commands"
        expected = {
            command_file.stem
            for command_file in commands_dir.iterdir()
            if command_file.is_file() and command_file.suffix == ".md"
        }

        assert CORE_COMMAND_NAMES == expected

    def test_load_core_command_names_discovers_from_source_checkout(self, monkeypatch):
        """Discovery must actually read the repo-root templates, not silently
        fall back (#3274).

        The fallback set happens to equal the real command stems today, so an
        equality check against the live tree cannot tell a working loader apart
        from a dead one. Point ``_repo_root`` at a temp tree with *different*
        command names: the old off-by-one path math read nothing and returned
        the baked-in fallback; the fixed loader returns the temp stems.
        """
        from specify_cli.extensions import (
            _load_core_command_names,
            _FALLBACK_CORE_COMMAND_NAMES,
        )
        import specify_cli.extensions as ext

        with tempfile.TemporaryDirectory() as tmp:
            commands = Path(tmp) / "templates" / "commands"
            commands.mkdir(parents=True)
            (commands / "widget.md").write_text("# widget", encoding="utf-8")
            (commands / "gadget.md").write_text("# gadget", encoding="utf-8")
            (commands / "notacommand.txt").write_text("skip me", encoding="utf-8")

            # No wheel bundle in this scenario; force the source-checkout path.
            monkeypatch.setattr(ext, "_locate_core_pack", lambda: None)
            monkeypatch.setattr(ext, "_repo_root", lambda: Path(tmp))

            result = _load_core_command_names()

        assert result == {"widget", "gadget"}
        assert result != _FALLBACK_CORE_COMMAND_NAMES

    def test_load_core_command_names_prefers_wheel_core_pack(self, monkeypatch):
        """When a wheel ``core_pack`` bundle exists, discovery reads
        ``core_pack/commands`` (the force-include target) ahead of the source
        tree (#3274)."""
        from specify_cli.extensions import _load_core_command_names
        import specify_cli.extensions as ext

        with tempfile.TemporaryDirectory() as tmp:
            core_pack = Path(tmp) / "core_pack"
            (core_pack / "commands").mkdir(parents=True)
            (core_pack / "commands" / "sprocket.md").write_text("# sprocket", encoding="utf-8")

            monkeypatch.setattr(ext, "_locate_core_pack", lambda: core_pack)
            # Source fallback should be ignored while the bundle resolves.
            monkeypatch.setattr(ext, "_repo_root", lambda: Path(tmp) / "nonexistent")

            result = _load_core_command_names()

        assert result == {"sprocket"}

    def test_load_core_command_names_falls_back_when_nothing_found(self, monkeypatch):
        """With neither a bundle nor a source tree, discovery returns the
        baked-in fallback so validation still works (#3274)."""
        from specify_cli.extensions import (
            _load_core_command_names,
            _FALLBACK_CORE_COMMAND_NAMES,
        )
        import specify_cli.extensions as ext

        with tempfile.TemporaryDirectory() as tmp:
            monkeypatch.setattr(ext, "_locate_core_pack", lambda: None)
            monkeypatch.setattr(ext, "_repo_root", lambda: Path(tmp) / "nonexistent")

            assert _load_core_command_names() == _FALLBACK_CORE_COMMAND_NAMES

    def test_missing_required_field(self, temp_dir):
        """Test manifest missing required field."""
        import yaml

        manifest_path = temp_dir / "extension.yml"
        with open(manifest_path, 'w') as f:
            yaml.dump({"schema_version": "1.0"}, f)  # Missing 'extension'

        with pytest.raises(ValidationError, match="Missing required field"):
            ExtensionManifest(manifest_path)

    def test_non_mapping_yaml_raises_validation_error(self, temp_dir):
        """Manifest whose YAML root is a scalar or list raises ValidationError, not TypeError."""
        manifest_path = temp_dir / "extension.yml"
        for bad_content in ("42\n", "[]\n", "null\n"):
            manifest_path.write_text(bad_content)
            with pytest.raises(ValidationError, match="YAML mapping"):
                ExtensionManifest(manifest_path)

    def test_utf8_non_ascii_description_loads(self, temp_dir, valid_manifest_data):
        """Regression for #2325: non-ASCII (UTF-8) description loads on any platform.

        On Windows, Python's default text-mode encoding is the locale codepage
        (e.g. cp1252/GBK), which raises UnicodeDecodeError on UTF-8 bytes
        outside the ASCII range. The loader must open with encoding='utf-8'.
        """
        import yaml

        valid_manifest_data["extension"]["description"] = "中文测试 — émojis 🚀"
        manifest_path = temp_dir / "extension.yml"
        # Write UTF-8 bytes explicitly so the test exercises the read path,
        # not the (locale-dependent) write path.
        manifest_path.write_bytes(
            yaml.safe_dump(valid_manifest_data, allow_unicode=True).encode("utf-8")
        )

        manifest = ExtensionManifest(manifest_path)
        assert manifest.description == "中文测试 — émojis 🚀"

    def test_invalid_utf8_bytes_raises_validation_error(self, temp_dir):
        """Negative case: file containing invalid UTF-8 bytes raises ValidationError, not raw UnicodeDecodeError."""
        manifest_path = temp_dir / "extension.yml"
        # 0xFF/0xFE are not valid UTF-8 lead bytes.
        manifest_path.write_bytes(b"\xff\xfe not valid utf-8 \xff\n")

        with pytest.raises(ValidationError, match="not valid UTF-8"):
            ExtensionManifest(manifest_path)

    def test_invalid_extension_id(self, temp_dir, valid_manifest_data):
        """Test manifest with invalid extension ID format."""
        import yaml

        valid_manifest_data["extension"]["id"] = "Invalid_ID"  # Uppercase not allowed

        manifest_path = temp_dir / "extension.yml"
        with open(manifest_path, 'w') as f:
            yaml.dump(valid_manifest_data, f)

        with pytest.raises(ValidationError, match="Invalid extension ID"):
            ExtensionManifest(manifest_path)

    def test_invalid_version(self, temp_dir, valid_manifest_data):
        """Test manifest with invalid semantic version."""
        import yaml

        valid_manifest_data["extension"]["version"] = "invalid"

        manifest_path = temp_dir / "extension.yml"
        with open(manifest_path, 'w') as f:
            yaml.dump(valid_manifest_data, f)

        with pytest.raises(ValidationError, match="Invalid version"):
            ExtensionManifest(manifest_path)

    def test_valid_category(self, temp_dir, valid_manifest_data):
        """Test manifest with various category values (free-form string)."""
        import yaml

        for category in ("docs", "code", "process", "integration", "visibility", "custom-category"):
            valid_manifest_data["extension"]["category"] = category
            manifest_path = temp_dir / "extension.yml"
            with open(manifest_path, 'w') as f:
                yaml.dump(valid_manifest_data, f)
            manifest = ExtensionManifest(manifest_path)
            assert manifest.category == category

    def test_valid_effect(self, temp_dir, valid_manifest_data):
        """Test manifest with valid effect values."""
        import yaml

        for effect in sorted(VALID_EFFECTS):
            valid_manifest_data["extension"]["effect"] = effect
            manifest_path = temp_dir / "extension.yml"
            with open(manifest_path, 'w') as f:
                yaml.dump(valid_manifest_data, f)
            manifest = ExtensionManifest(manifest_path)
            assert manifest.effect == effect

    def test_invalid_category(self, temp_dir, valid_manifest_data):
        """Test manifest with empty category raises ValidationError."""
        import yaml

        valid_manifest_data["extension"]["category"] = ""
        manifest_path = temp_dir / "extension.yml"
        with open(manifest_path, 'w') as f:
            yaml.dump(valid_manifest_data, f)

        with pytest.raises(ValidationError, match="Invalid extension.category"):
            ExtensionManifest(manifest_path)

    def test_invalid_effect(self, temp_dir, valid_manifest_data):
        """Test manifest with invalid effect raises ValidationError."""
        import yaml

        valid_manifest_data["extension"]["effect"] = "write-only"
        manifest_path = temp_dir / "extension.yml"
        with open(manifest_path, 'w') as f:
            yaml.dump(valid_manifest_data, f)

        with pytest.raises(ValidationError, match="Invalid extension.effect"):
            ExtensionManifest(manifest_path)

    def test_category_and_effect_optional(self, temp_dir, valid_manifest_data):
        """Test that omitting category and effect still passes validation."""
        import yaml

        # Ensure no category/effect in data
        valid_manifest_data["extension"].pop("category", None)
        valid_manifest_data["extension"].pop("effect", None)
        manifest_path = temp_dir / "extension.yml"
        with open(manifest_path, 'w') as f:
            yaml.dump(valid_manifest_data, f)

        manifest = ExtensionManifest(manifest_path)
        assert manifest.category is None
        assert manifest.effect is None

    def test_invalid_command_name(self, temp_dir, valid_manifest_data):
        """Test manifest with command name that cannot be auto-corrected raises ValidationError."""
        import yaml

        valid_manifest_data["provides"]["commands"][0]["name"] = "invalid-name"

        manifest_path = temp_dir / "extension.yml"
        with open(manifest_path, 'w') as f:
            yaml.dump(valid_manifest_data, f)

        with pytest.raises(ValidationError, match="Invalid command name"):
            ExtensionManifest(manifest_path)

    @pytest.mark.parametrize(
        "bad_file",
        ["../../../outside.md", "../escape.md", "a/../../escape.md", "/abs/outside.md", "C:escape.md", "C:\\Windows\\x.md", "..\\..\\escape.md"],
    )
    def test_command_file_traversal_rejected(self, temp_dir, valid_manifest_data, bad_file):
        """Manifest 'file' field with traversal/absolute path raises ValidationError.

        Defense-in-depth for GHSA-w5fv-7w9x-7fc5.
        """
        import yaml

        valid_manifest_data["provides"]["commands"][0]["file"] = bad_file

        manifest_path = temp_dir / "extension.yml"
        with open(manifest_path, 'w', encoding='utf-8') as f:
            yaml.safe_dump(valid_manifest_data, f)

        with pytest.raises(ValidationError, match="Invalid command 'file'"):
            ExtensionManifest(manifest_path)

    @pytest.mark.parametrize("bad_file", [" commands/hello.md", "commands/hello.md ", "\tcommands/hello.md"])
    def test_command_file_whitespace_rejected(self, temp_dir, valid_manifest_data, bad_file):
        """Manifest 'file' with leading/trailing whitespace raises ValidationError."""
        import yaml

        valid_manifest_data["provides"]["commands"][0]["file"] = bad_file

        manifest_path = temp_dir / "extension.yml"
        with open(manifest_path, 'w', encoding='utf-8') as f:
            yaml.safe_dump(valid_manifest_data, f)

        with pytest.raises(ValidationError, match="leading or trailing whitespace"):
            ExtensionManifest(manifest_path)

    def test_command_name_autocorrect_speckit_prefix(self, temp_dir, valid_manifest_data):
        """Test that 'speckit.command' is auto-corrected to 'speckit.{ext_id}.command'."""
        import yaml

        valid_manifest_data["provides"]["commands"][0]["name"] = "speckit.hello"

        manifest_path = temp_dir / "extension.yml"
        with open(manifest_path, 'w') as f:
            yaml.dump(valid_manifest_data, f)

        manifest = ExtensionManifest(manifest_path)

        assert manifest.commands[0]["name"] == "speckit.test-ext.hello"
        assert len(manifest.warnings) == 1
        assert "speckit.hello" in manifest.warnings[0]
        assert "speckit.test-ext.hello" in manifest.warnings[0]

    def test_command_name_autocorrect_matching_ext_id_prefix(self, temp_dir, valid_manifest_data):
        """Test that '{ext_id}.command' is auto-corrected to 'speckit.{ext_id}.command'."""
        import yaml

        # Set ext_id to match the legacy namespace so correction is valid
        valid_manifest_data["extension"]["id"] = "docguard"
        valid_manifest_data["provides"]["commands"][0]["name"] = "docguard.guard"

        manifest_path = temp_dir / "extension.yml"
        with open(manifest_path, 'w') as f:
            yaml.dump(valid_manifest_data, f)

        manifest = ExtensionManifest(manifest_path)

        assert manifest.commands[0]["name"] == "speckit.docguard.guard"
        assert len(manifest.warnings) == 1
        assert "docguard.guard" in manifest.warnings[0]
        assert "speckit.docguard.guard" in manifest.warnings[0]

    def test_command_name_mismatched_namespace_not_corrected(self, temp_dir, valid_manifest_data):
        """Test that 'X.command' is NOT corrected when X doesn't match ext_id."""
        import yaml

        # ext_id is "test-ext" but command uses a different namespace
        valid_manifest_data["provides"]["commands"][0]["name"] = "docguard.guard"

        manifest_path = temp_dir / "extension.yml"
        with open(manifest_path, 'w') as f:
            yaml.dump(valid_manifest_data, f)

        with pytest.raises(ValidationError, match="Invalid command name"):
            ExtensionManifest(manifest_path)

    def test_alias_free_form_accepted(self, temp_dir, valid_manifest_data):
        """Aliases are free-form — a 'speckit.command' alias must be accepted unchanged."""
        import yaml

        valid_manifest_data["provides"]["commands"][0]["aliases"] = ["speckit.hello"]

        manifest_path = temp_dir / "extension.yml"
        with open(manifest_path, 'w') as f:
            yaml.dump(valid_manifest_data, f)

        manifest = ExtensionManifest(manifest_path)

        assert manifest.commands[0]["aliases"] == ["speckit.hello"]
        assert manifest.warnings == []

    def test_valid_command_name_has_no_warnings(self, temp_dir, valid_manifest_data):
        """Test that a correctly-named command produces no warnings."""
        import yaml

        manifest_path = temp_dir / "extension.yml"
        with open(manifest_path, 'w') as f:
            yaml.dump(valid_manifest_data, f)

        manifest = ExtensionManifest(manifest_path)

        assert manifest.warnings == []

    def test_no_commands_no_hooks(self, temp_dir, valid_manifest_data):
        """Test manifest with no commands and no hooks provided."""
        import yaml

        valid_manifest_data["provides"]["commands"] = []
        valid_manifest_data.pop("hooks", None)

        manifest_path = temp_dir / "extension.yml"
        with open(manifest_path, 'w') as f:
            yaml.dump(valid_manifest_data, f)

        with pytest.raises(ValidationError, match="must provide at least one command or hook"):
            ExtensionManifest(manifest_path)

    def test_hooks_only_extension(self, temp_dir, valid_manifest_data):
        """Test manifest with hooks but no commands is valid."""
        import yaml

        valid_manifest_data["provides"]["commands"] = []
        valid_manifest_data["hooks"] = {
            "after_specify": {
                "command": "speckit.test-ext.notify",
                "optional": True,
                "prompt": "Run notification?",
            }
        }

        manifest_path = temp_dir / "extension.yml"
        with open(manifest_path, 'w') as f:
            yaml.dump(valid_manifest_data, f)

        manifest = ExtensionManifest(manifest_path)
        assert manifest.id == valid_manifest_data["extension"]["id"]
        assert len(manifest.commands) == 0
        assert len(manifest.hooks) == 1

    def test_commands_null_rejected(self, temp_dir, valid_manifest_data):
        """Test manifest with commands: null is rejected."""
        import yaml

        valid_manifest_data["provides"]["commands"] = None

        manifest_path = temp_dir / "extension.yml"
        with open(manifest_path, 'w') as f:
            yaml.dump(valid_manifest_data, f)

        with pytest.raises(ValidationError, match="Invalid provides.commands"):
            ExtensionManifest(manifest_path)

    def test_hooks_not_dict_rejected(self, temp_dir, valid_manifest_data):
        """Test manifest with hooks as a list is rejected."""
        import yaml

        valid_manifest_data["hooks"] = ["not", "a", "dict"]

        manifest_path = temp_dir / "extension.yml"
        with open(manifest_path, 'w') as f:
            yaml.dump(valid_manifest_data, f)

        with pytest.raises(ValidationError, match="Invalid hooks"):
            ExtensionManifest(manifest_path)

    def test_non_dict_hook_entry_raises_validation_error(self, temp_dir, valid_manifest_data):
        """Non-mapping hook entries must raise ValidationError, not silently skip."""
        import yaml

        valid_manifest_data["hooks"]["after_tasks"] = "speckit.test-ext.hello"

        manifest_path = temp_dir / "extension.yml"
        with open(manifest_path, 'w') as f:
            yaml.dump(valid_manifest_data, f)

        with pytest.raises(ValidationError, match="Invalid hook 'after_tasks'"):
            ExtensionManifest(manifest_path)

    def test_hook_single_mapping_still_accepted(self, extension_dir):
        """Existing single-mapping hook manifests parse unchanged (regression)."""
        manifest_path = extension_dir / "extension.yml"
        manifest = ExtensionManifest(manifest_path)

        assert "after_tasks" in manifest.hooks
        assert isinstance(manifest.hooks["after_tasks"], dict)
        assert manifest.hooks["after_tasks"]["command"] == "speckit.test-ext.hello"

    def test_hook_list_of_mappings_accepted(self, temp_dir, valid_manifest_data):
        """A hook event may be configured as a list of mappings."""
        import yaml

        valid_manifest_data["provides"]["commands"].append({
            "name": "speckit.test-ext.bye",
            "file": "commands/bye.md",
            "description": "Second test command",
        })
        valid_manifest_data["hooks"]["after_tasks"] = [
            {"command": "speckit.test-ext.hello", "description": "first"},
            {"command": "speckit.test-ext.bye", "description": "second"},
        ]

        manifest_path = temp_dir / "extension.yml"
        with open(manifest_path, 'w', encoding="utf-8") as f:
            yaml.dump(valid_manifest_data, f)

        manifest = ExtensionManifest(manifest_path)

        entries = manifest.hooks["after_tasks"]
        assert isinstance(entries, list)
        assert [e["command"] for e in entries] == [
            "speckit.test-ext.hello",
            "speckit.test-ext.bye",
        ]

    def test_hook_list_with_non_mapping_entry_rejected(self, temp_dir, valid_manifest_data):
        """A list entry that is not a mapping must raise ValidationError."""
        import yaml

        valid_manifest_data["hooks"]["after_tasks"] = [
            {"command": "speckit.test-ext.hello"},
            "not-a-mapping",
        ]

        manifest_path = temp_dir / "extension.yml"
        with open(manifest_path, 'w', encoding="utf-8") as f:
            yaml.dump(valid_manifest_data, f)

        with pytest.raises(
            ValidationError,
            match="Invalid hook 'after_tasks': expected a mapping or list of mappings",
        ):
            ExtensionManifest(manifest_path)

    def test_hook_list_command_refs_normalized(self, temp_dir, valid_manifest_data):
        """Alias-form command refs are lifted to canonical form for every entry
        in a list hook, each emitting a warning."""
        import yaml

        valid_manifest_data["provides"]["commands"].append({
            "name": "speckit.test-ext.bye",
            "file": "commands/bye.md",
            "description": "Second test command",
        })
        valid_manifest_data["hooks"]["after_tasks"] = [
            {"command": "test-ext.hello"},
            {"command": "test-ext.bye"},
        ]

        manifest_path = temp_dir / "extension.yml"
        with open(manifest_path, 'w', encoding="utf-8") as f:
            yaml.dump(valid_manifest_data, f)

        manifest = ExtensionManifest(manifest_path)

        assert [e["command"] for e in manifest.hooks["after_tasks"]] == [
            "speckit.test-ext.hello",
            "speckit.test-ext.bye",
        ]
        lifted = [w for w in manifest.warnings if "updated to canonical form" in w]
        assert len(lifted) == 2

    def test_hook_empty_list_rejected(self, temp_dir, valid_manifest_data):
        """An empty list for a hook event is rejected rather than silently
        registering nothing."""
        import yaml

        valid_manifest_data["hooks"]["after_tasks"] = []

        manifest_path = temp_dir / "extension.yml"
        with open(manifest_path, 'w', encoding="utf-8") as f:
            yaml.dump(valid_manifest_data, f)

        with pytest.raises(ValidationError, match="must contain at least one entry"):
            ExtensionManifest(manifest_path)

    def test_hook_priority_field_validation(self, temp_dir, valid_manifest_data):
        """Hook entry ``priority`` must be a positive integer when provided."""
        import yaml

        manifest_path = temp_dir / "extension.yml"

        valid_manifest_data["hooks"]["after_tasks"] = {
            "command": "speckit.test-ext.hello",
            "priority": "high",
        }
        with open(manifest_path, 'w', encoding="utf-8") as f:
            yaml.dump(valid_manifest_data, f)
        with pytest.raises(ValidationError, match="invalid 'priority'.*integer"):
            ExtensionManifest(manifest_path)

        valid_manifest_data["hooks"]["after_tasks"]["priority"] = 0
        with open(manifest_path, 'w', encoding="utf-8") as f:
            yaml.dump(valid_manifest_data, f)
        with pytest.raises(ValidationError, match="invalid 'priority'.*>= 1"):
            ExtensionManifest(manifest_path)

        # bool is a subclass of int, so it must be rejected explicitly.
        valid_manifest_data["hooks"]["after_tasks"]["priority"] = True
        with open(manifest_path, 'w', encoding="utf-8") as f:
            yaml.dump(valid_manifest_data, f)
        with pytest.raises(ValidationError, match="invalid 'priority'.*integer"):
            ExtensionManifest(manifest_path)

        valid_manifest_data["hooks"]["after_tasks"]["priority"] = 5
        with open(manifest_path, 'w', encoding="utf-8") as f:
            yaml.dump(valid_manifest_data, f)
        manifest = ExtensionManifest(manifest_path)
        assert manifest.hooks["after_tasks"]["priority"] == 5

    def test_manifest_hash(self, extension_dir):
        """Test manifest hash calculation."""
        manifest_path = extension_dir / "extension.yml"
        manifest = ExtensionManifest(manifest_path)

        hash_value = manifest.get_hash()
        assert hash_value.startswith("sha256:")
        assert len(hash_value) > 10


# ===== ExtensionRegistry Tests =====

class TestExtensionRegistry:
    """Test ExtensionRegistry operations."""

    def test_empty_registry(self, temp_dir):
        """Test creating a new empty registry."""
        extensions_dir = temp_dir / "extensions"
        extensions_dir.mkdir()

        registry = ExtensionRegistry(extensions_dir)

        assert registry.data["schema_version"] == "1.0"
        assert registry.data["extensions"] == {}
        assert len(registry.list()) == 0

    def test_add_extension(self, temp_dir):
        """Test adding an extension to registry."""
        extensions_dir = temp_dir / "extensions"
        extensions_dir.mkdir()

        registry = ExtensionRegistry(extensions_dir)

        metadata = {
            "version": "1.0.0",
            "source": "local",
            "enabled": True,
        }
        registry.add("test-ext", metadata)

        assert registry.is_installed("test-ext")
        ext_data = registry.get("test-ext")
        assert ext_data["version"] == "1.0.0"
        assert "installed_at" in ext_data

    def test_remove_extension(self, temp_dir):
        """Test removing an extension from registry."""
        extensions_dir = temp_dir / "extensions"
        extensions_dir.mkdir()

        registry = ExtensionRegistry(extensions_dir)
        registry.add("test-ext", {"version": "1.0.0"})

        assert registry.is_installed("test-ext")

        registry.remove("test-ext")

        assert not registry.is_installed("test-ext")
        assert registry.get("test-ext") is None

    def test_registry_persistence(self, temp_dir):
        """Test that registry persists to disk."""
        extensions_dir = temp_dir / "extensions"
        extensions_dir.mkdir()

        # Create registry and add extension
        registry1 = ExtensionRegistry(extensions_dir)
        registry1.add("test-ext", {"version": "1.0.0"})

        # Load new registry instance
        registry2 = ExtensionRegistry(extensions_dir)

        # Should still have the extension
        assert registry2.is_installed("test-ext")
        assert registry2.get("test-ext")["version"] == "1.0.0"

    def test_update_preserves_installed_at(self, temp_dir):
        """Test that update() preserves the original installed_at timestamp."""
        extensions_dir = temp_dir / "extensions"
        extensions_dir.mkdir()

        registry = ExtensionRegistry(extensions_dir)
        registry.add("test-ext", {"version": "1.0.0", "enabled": True})

        # Get original installed_at
        original_data = registry.get("test-ext")
        original_installed_at = original_data["installed_at"]

        # Update with new metadata
        registry.update("test-ext", {"version": "2.0.0", "enabled": False})

        # Verify installed_at is preserved
        updated_data = registry.get("test-ext")
        assert updated_data["installed_at"] == original_installed_at
        assert updated_data["version"] == "2.0.0"
        assert updated_data["enabled"] is False

    def test_update_merges_with_existing(self, temp_dir):
        """Test that update() merges new metadata with existing fields."""
        extensions_dir = temp_dir / "extensions"
        extensions_dir.mkdir()

        registry = ExtensionRegistry(extensions_dir)
        registry.add("test-ext", {
            "version": "1.0.0",
            "enabled": True,
            "registered_commands": {"claude": ["cmd1", "cmd2"]},
        })

        # Update with partial metadata (only enabled field)
        registry.update("test-ext", {"enabled": False})

        # Verify existing fields are preserved
        updated_data = registry.get("test-ext")
        assert updated_data["enabled"] is False
        assert updated_data["version"] == "1.0.0"  # Preserved
        assert updated_data["registered_commands"] == {"claude": ["cmd1", "cmd2"]}  # Preserved

    def test_update_raises_for_missing_extension(self, temp_dir):
        """Test that update() raises KeyError for non-installed extension."""
        extensions_dir = temp_dir / "extensions"
        extensions_dir.mkdir()

        registry = ExtensionRegistry(extensions_dir)

        with pytest.raises(KeyError, match="not installed"):
            registry.update("nonexistent-ext", {"enabled": False})

    def test_restore_overwrites_completely(self, temp_dir):
        """Test that restore() overwrites the registry entry completely."""
        extensions_dir = temp_dir / "extensions"
        extensions_dir.mkdir()

        registry = ExtensionRegistry(extensions_dir)
        registry.add("test-ext", {"version": "2.0.0", "enabled": True})

        # Restore with complete backup data
        backup_data = {
            "version": "1.0.0",
            "enabled": False,
            "installed_at": "2024-01-01T00:00:00+00:00",
            "registered_commands": {"claude": ["old-cmd"]},
        }
        registry.restore("test-ext", backup_data)

        # Verify entry is exactly as restored
        restored_data = registry.get("test-ext")
        assert restored_data == backup_data

    def test_restore_can_recreate_removed_entry(self, temp_dir):
        """Test that restore() can recreate an entry after remove()."""
        extensions_dir = temp_dir / "extensions"
        extensions_dir.mkdir()

        registry = ExtensionRegistry(extensions_dir)
        registry.add("test-ext", {"version": "1.0.0"})

        # Save backup and remove
        backup = registry.get("test-ext").copy()
        registry.remove("test-ext")
        assert not registry.is_installed("test-ext")

        # Restore should recreate the entry
        registry.restore("test-ext", backup)
        assert registry.is_installed("test-ext")
        assert registry.get("test-ext")["version"] == "1.0.0"

    def test_restore_rejects_none_metadata(self, temp_dir):
        """Test restore() raises ValueError for None metadata."""
        extensions_dir = temp_dir / "extensions"
        extensions_dir.mkdir()
        registry = ExtensionRegistry(extensions_dir)

        with pytest.raises(ValueError, match="metadata must be a dict"):
            registry.restore("test-ext", None)

    def test_restore_rejects_non_dict_metadata(self, temp_dir):
        """Test restore() raises ValueError for non-dict metadata."""
        extensions_dir = temp_dir / "extensions"
        extensions_dir.mkdir()
        registry = ExtensionRegistry(extensions_dir)

        with pytest.raises(ValueError, match="metadata must be a dict"):
            registry.restore("test-ext", "not-a-dict")

        with pytest.raises(ValueError, match="metadata must be a dict"):
            registry.restore("test-ext", ["list", "not", "dict"])

    def test_restore_uses_deep_copy(self, temp_dir):
        """Test restore() deep copies metadata to prevent mutation."""
        extensions_dir = temp_dir / "extensions"
        extensions_dir.mkdir()
        registry = ExtensionRegistry(extensions_dir)

        original_metadata = {
            "version": "1.0.0",
            "nested": {"key": "original"},
        }
        registry.restore("test-ext", original_metadata)

        # Mutate the original metadata after restore
        original_metadata["version"] = "MUTATED"
        original_metadata["nested"]["key"] = "MUTATED"

        # Registry should have the original values
        stored = registry.get("test-ext")
        assert stored["version"] == "1.0.0"
        assert stored["nested"]["key"] == "original"

    def test_get_returns_deep_copy(self, temp_dir):
        """Test that get() returns deep copies for nested structures."""
        extensions_dir = temp_dir / "extensions"
        extensions_dir.mkdir()

        registry = ExtensionRegistry(extensions_dir)
        metadata = {
            "version": "1.0.0",
            "registered_commands": {"claude": ["cmd1"]},
        }
        registry.add("test-ext", metadata)

        fetched = registry.get("test-ext")
        fetched["registered_commands"]["claude"].append("cmd2")

        # Internal registry must remain unchanged.
        internal = registry.data["extensions"]["test-ext"]
        assert internal["registered_commands"] == {"claude": ["cmd1"]}

    def test_get_returns_none_for_corrupted_entry(self, temp_dir):
        """Test that get() returns None for corrupted (non-dict) entries."""
        extensions_dir = temp_dir / "extensions"
        extensions_dir.mkdir()

        registry = ExtensionRegistry(extensions_dir)

        # Directly corrupt the registry with non-dict entries
        registry.data["extensions"]["corrupted-string"] = "not a dict"
        registry.data["extensions"]["corrupted-list"] = ["not", "a", "dict"]
        registry.data["extensions"]["corrupted-int"] = 42
        registry._save()

        # All corrupted entries should return None
        assert registry.get("corrupted-string") is None
        assert registry.get("corrupted-list") is None
        assert registry.get("corrupted-int") is None
        # Non-existent should also return None
        assert registry.get("nonexistent") is None

    def test_list_returns_deep_copy(self, temp_dir):
        """Test that list() returns deep copies for nested structures."""
        extensions_dir = temp_dir / "extensions"
        extensions_dir.mkdir()

        registry = ExtensionRegistry(extensions_dir)
        metadata = {
            "version": "1.0.0",
            "registered_commands": {"claude": ["cmd1"]},
        }
        registry.add("test-ext", metadata)

        listed = registry.list()
        listed["test-ext"]["registered_commands"]["claude"].append("cmd2")

        # Internal registry must remain unchanged.
        internal = registry.data["extensions"]["test-ext"]
        assert internal["registered_commands"] == {"claude": ["cmd1"]}

    def test_list_returns_empty_dict_for_corrupted_registry(self, temp_dir):
        """Test that list() returns empty dict when extensions is not a dict."""
        extensions_dir = temp_dir / "extensions"
        extensions_dir.mkdir()
        registry = ExtensionRegistry(extensions_dir)

        # Corrupt the registry - extensions is a list instead of dict
        registry.data["extensions"] = ["not", "a", "dict"]
        registry._save()

        # list() should return empty dict, not crash
        result = registry.list()
        assert result == {}


# ===== ExtensionManager Tests =====

class TestExtensionManager:
    """Test ExtensionManager installation and removal."""

    def test_check_compatibility_valid(self, extension_dir, project_dir):
        """Test compatibility check with valid version."""
        manager = ExtensionManager(project_dir)
        manifest = ExtensionManifest(extension_dir / "extension.yml")

        # Should not raise
        result = manager.check_compatibility(manifest, "0.1.0")
        assert result is True

    def test_check_compatibility_invalid(self, extension_dir, project_dir):
        """Test compatibility check with invalid version."""
        manager = ExtensionManager(project_dir)
        manifest = ExtensionManifest(extension_dir / "extension.yml")

        # Requires >=0.1.0, but we have 0.0.1
        with pytest.raises(CompatibilityError, match="Extension requires spec-kit"):
            manager.check_compatibility(manifest, "0.0.1")

    def test_check_compatibility_allows_prerelease_builds(self, extension_dir, project_dir):
        """Prerelease spec-kit builds should satisfy compatible version ranges."""
        manager = ExtensionManager(project_dir)
        manifest = ExtensionManifest(extension_dir / "extension.yml")

        result = manager.check_compatibility(manifest, "0.8.8.dev0")
        assert result is True

    def test_install_from_directory(self, extension_dir, project_dir):
        """Test installing extension from directory."""
        manager = ExtensionManager(project_dir)

        manifest = manager.install_from_directory(
            extension_dir,
            "0.1.0",
            register_commands=False  # Skip command registration for now
        )

        assert manifest.id == "test-ext"
        assert manager.registry.is_installed("test-ext")

        # Check extension directory was copied
        ext_dir = project_dir / ".specify" / "extensions" / "test-ext"
        assert ext_dir.exists()
        assert (ext_dir / "extension.yml").exists()
        assert (ext_dir / "commands" / "hello.md").exists()

    def test_install_from_directory_explicitly_recovers_active_skills_dir(
        self, extension_dir, project_dir, monkeypatch
    ):
        """Extension install should explicitly request active skills-dir recovery."""
        captured = {}

        def fake_register_all(
            self,
            manifest,
            extension_dir,
            project_root,
            link_outputs=False,
            create_missing_active_skills_dir=False,
        ):
            captured["create_missing_active_skills_dir"] = (
                create_missing_active_skills_dir
            )
            return {}

        monkeypatch.setattr(
            CommandRegistrar,
            "register_commands_for_all_agents",
            fake_register_all,
        )

        manager = ExtensionManager(project_dir)
        manager.install_from_directory(extension_dir, "0.1.0", register_commands=True)

        assert captured["create_missing_active_skills_dir"] is True

    def test_command_registrar_default_does_not_recover_active_skills_dir(
        self, extension_dir, project_dir, monkeypatch
    ):
        """The extension wrapper should preserve the core registrar's conservative default."""
        from specify_cli.agents import CommandRegistrar as AgentCommandRegistrar

        captured = {}

        def fake_register_all(
            self,
            commands,
            source_id,
            source_dir,
            project_root,
            context_note=None,
            link_outputs=False,
            create_missing_active_skills_dir=False,
        ):
            captured["create_missing_active_skills_dir"] = (
                create_missing_active_skills_dir
            )
            return {}

        monkeypatch.setattr(
            AgentCommandRegistrar,
            "register_commands_for_all_agents",
            fake_register_all,
        )

        manifest = ExtensionManifest(extension_dir / "extension.yml")
        registrar = CommandRegistrar()
        registrar.register_commands_for_all_agents(manifest, extension_dir, project_dir)

        assert captured["create_missing_active_skills_dir"] is False

    def test_install_duplicate(self, extension_dir, project_dir):
        """Test installing already installed extension."""
        manager = ExtensionManager(project_dir)

        # Install once
        manager.install_from_directory(extension_dir, "0.1.0", register_commands=False)

        # Try to install again
        with pytest.raises(ExtensionError, match="already installed"):
            manager.install_from_directory(extension_dir, "0.1.0", register_commands=False)

    def test_install_force_reinstall(self, extension_dir, project_dir):
        """Test force-reinstalling an already-installed extension."""
        manager = ExtensionManager(project_dir)

        # Install once
        manager.install_from_directory(
            extension_dir, "0.1.0", register_commands=False
        )
        assert manager.registry.is_installed("test-ext")

        # Force-reinstall
        manifest2 = manager.install_from_directory(
            extension_dir, "0.1.0", register_commands=False, force=True
        )

        assert manifest2.id == "test-ext"
        assert manager.registry.is_installed("test-ext")
        # Check extension directory was recreated
        ext_dir = project_dir / ".specify" / "extensions" / "test-ext"
        assert ext_dir.exists()
        assert (ext_dir / "extension.yml").exists()
        assert (ext_dir / "commands" / "hello.md").exists()

    def test_install_force_config_preserved(self, extension_dir, project_dir):
        """Test that config files are preserved when force-reinstalling."""
        manager = ExtensionManager(project_dir)

        # Install once
        manager.install_from_directory(
            extension_dir, "0.1.0", register_commands=False
        )

        # Create a config file in the installed extension directory
        ext_dir = project_dir / ".specify" / "extensions" / "test-ext"
        config_file = ext_dir / "test-ext-config.yml"
        config_file.write_text("test: config")

        # Force-reinstall
        manager.install_from_directory(
            extension_dir, "0.1.0", register_commands=False, force=True
        )

        # Config file should still exist after reinstall
        new_config = ext_dir / "test-ext-config.yml"
        assert new_config.exists()
        assert new_config.read_text() == "test: config"

    def test_install_force_without_existing(self, extension_dir, project_dir):
        """Test force-install when extension is NOT already installed (works normally)."""
        manager = ExtensionManager(project_dir)

        manifest = manager.install_from_directory(
            extension_dir, "0.1.0", register_commands=False, force=True
        )

        assert manifest.id == "test-ext"
        assert manager.registry.is_installed("test-ext")

    def test_install_from_install_dir_is_rejected_without_data_loss(
        self, extension_dir, project_dir
    ):
        """Installing from an extension's own install dir must fail without
        deleting it (regression for issue #2990)."""
        manager = ExtensionManager(project_dir)

        # Install once so the extension lives at its install destination.
        manager.install_from_directory(extension_dir, "0.1.0", register_commands=False)
        install_dir = project_dir / ".specify" / "extensions" / "test-ext"
        assert install_dir.exists()

        # Re-installing from that same directory with --force must be rejected.
        with pytest.raises(ValidationError, match="install destination"):
            manager.install_from_directory(
                install_dir, "0.1.0", register_commands=False, force=True
            )

        # The directory and its contents must be left intact (no data loss).
        assert install_dir.exists()
        assert (install_dir / "extension.yml").exists()
        assert (install_dir / "commands" / "hello.md").exists()

    def test_install_from_install_dir_is_rejected_when_resolve_fails(
        self, extension_dir, project_dir, monkeypatch
    ):
        """Resolution failures must not bypass the self-install guard."""
        manager = ExtensionManager(project_dir)

        manager.install_from_directory(extension_dir, "0.1.0", register_commands=False)
        install_dir = project_dir / ".specify" / "extensions" / "test-ext"

        original_resolve = Path.resolve

        def fail_resolve(self, *args, **kwargs):
            if self in {install_dir, manager.extensions_dir / "test-ext"}:
                raise OSError("cannot resolve path")
            return original_resolve(self, *args, **kwargs)

        monkeypatch.setattr(Path, "resolve", fail_resolve)

        with pytest.raises(ValidationError, match="install destination"):
            manager.install_from_directory(
                install_dir, "0.1.0", register_commands=False, force=True
            )

        assert install_dir.exists()
        assert (install_dir / "extension.yml").exists()
        assert (install_dir / "commands" / "hello.md").exists()

    def test_install_zip_force_reinstall(self, extension_dir, project_dir):
        """Test force-reinstalling from ZIP when already installed."""
        import zipfile
        import tempfile

        manager = ExtensionManager(project_dir)

        # Install once from directory
        manager.install_from_directory(extension_dir, "0.1.0", register_commands=False)

        # Create a ZIP of the extension in a temp directory (not NamedTemporaryFile,
        # which can fail on Windows due to file locking).
        with tempfile.TemporaryDirectory() as tmpdir:
            zip_path = Path(tmpdir) / "test-ext.zip"
            with zipfile.ZipFile(zip_path, "w") as zf:
                for f in extension_dir.rglob("*"):
                    if f.is_file():
                        zf.write(f, f.relative_to(extension_dir))

            # Force-reinstall from ZIP
            manifest = manager.install_from_zip(
                zip_path, "0.1.0", force=True
            )

        assert manifest.id == "test-ext"
        assert manager.registry.is_installed("test-ext")
        ext_dir = project_dir / ".specify" / "extensions" / "test-ext"
        assert ext_dir.exists()

    def test_install_duplicate_error_mentions_force(self, extension_dir, project_dir):
        """Test that duplicate install error message suggests --force."""
        manager = ExtensionManager(project_dir)

        manager.install_from_directory(extension_dir, "0.1.0", register_commands=False)

        with pytest.raises(ExtensionError, match="--force"):
            manager.install_from_directory(extension_dir, "0.1.0", register_commands=False)

    def test_install_rejects_extension_id_in_core_namespace(self, temp_dir, project_dir):
        """Install should reject extension IDs that shadow core commands."""
        import yaml

        ext_dir = temp_dir / "analyze-ext"
        ext_dir.mkdir()
        (ext_dir / "commands").mkdir()

        manifest_data = {
            "schema_version": "1.0",
            "extension": {
                "id": "analyze",
                "name": "Analyze Extension",
                "version": "1.0.0",
                "description": "Test",
            },
            "requires": {"speckit_version": ">=0.1.0"},
            "provides": {
                "commands": [
                    {
                        "name": "speckit.analyze.extra",
                        "file": "commands/cmd.md",
                    }
                ]
            },
        }

        (ext_dir / "extension.yml").write_text(yaml.dump(manifest_data))
        (ext_dir / "commands" / "cmd.md").write_text("---\ndescription: Test\n---\n\nBody")

        manager = ExtensionManager(project_dir)
        with pytest.raises(ValidationError, match="conflicts with core command namespace"):
            manager.install_from_directory(ext_dir, "0.1.0", register_commands=False)

    def test_install_accepts_free_form_alias(self, temp_dir, project_dir):
        """Aliases are free-form — a short 'speckit.shortcut' alias must be preserved unchanged."""
        import yaml

        ext_dir = temp_dir / "alias-shortcut"
        ext_dir.mkdir()
        (ext_dir / "commands").mkdir()

        manifest_data = {
            "schema_version": "1.0",
            "extension": {
                "id": "alias-shortcut",
                "name": "Alias Shortcut",
                "version": "1.0.0",
                "description": "Test",
            },
            "requires": {"speckit_version": ">=0.1.0"},
            "provides": {
                "commands": [
                    {
                        "name": "speckit.alias-shortcut.cmd",
                        "file": "commands/cmd.md",
                        "aliases": ["speckit.shortcut"],
                    }
                ]
            },
        }

        (ext_dir / "extension.yml").write_text(yaml.dump(manifest_data))
        (ext_dir / "commands" / "cmd.md").write_text("---\ndescription: Test\n---\n\nBody")

        manager = ExtensionManager(project_dir)
        manifest = manager.install_from_directory(ext_dir, "0.1.0", register_commands=False)

        assert manifest.commands[0]["aliases"] == ["speckit.shortcut"]
        assert manifest.warnings == []

    def test_install_rejects_namespace_squatting(self, temp_dir, project_dir):
        """Install should reject commands and aliases outside the extension namespace."""
        import yaml

        ext_dir = temp_dir / "squat-ext"
        ext_dir.mkdir()
        (ext_dir / "commands").mkdir()

        manifest_data = {
            "schema_version": "1.0",
            "extension": {
                "id": "squat-ext",
                "name": "Squat Extension",
                "version": "1.0.0",
                "description": "Test",
            },
            "requires": {"speckit_version": ">=0.1.0"},
            "provides": {
                "commands": [
                    {
                        "name": "speckit.other-ext.cmd",
                        "file": "commands/cmd.md",
                        "aliases": ["speckit.squat-ext.ok"],
                    }
                ]
            },
        }

        (ext_dir / "extension.yml").write_text(yaml.dump(manifest_data))
        (ext_dir / "commands" / "cmd.md").write_text("---\ndescription: Test\n---\n\nBody")

        manager = ExtensionManager(project_dir)
        with pytest.raises(ValidationError, match="must use extension namespace 'squat-ext'"):
            manager.install_from_directory(ext_dir, "0.1.0", register_commands=False)

    def test_install_rejects_command_collision_with_installed_extension(self, temp_dir, project_dir):
        """Install should reject names already claimed by an installed legacy extension."""
        import yaml

        first_dir = temp_dir / "ext-one"
        first_dir.mkdir()
        (first_dir / "commands").mkdir()
        first_manifest = {
            "schema_version": "1.0",
            "extension": {
                "id": "ext-one",
                "name": "Extension One",
                "version": "1.0.0",
                "description": "Test",
            },
            "requires": {"speckit_version": ">=0.1.0"},
            "provides": {
                "commands": [
                    {
                        "name": "speckit.ext-one.sync",
                        "file": "commands/cmd.md",
                        "aliases": ["speckit.shared.sync"],
                    }
                ]
            },
        }
        (first_dir / "extension.yml").write_text(yaml.dump(first_manifest))
        (first_dir / "commands" / "cmd.md").write_text("---\ndescription: Test\n---\n\nBody")
        installed_ext_dir = project_dir / ".specify" / "extensions" / "ext-one"
        installed_ext_dir.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(first_dir, installed_ext_dir)

        second_dir = temp_dir / "ext-two"
        second_dir.mkdir()
        (second_dir / "commands").mkdir()
        second_manifest = {
            "schema_version": "1.0",
            "extension": {
                "id": "shared",
                "name": "Shared Extension",
                "version": "1.0.0",
                "description": "Test",
            },
            "requires": {"speckit_version": ">=0.1.0"},
            "provides": {
                "commands": [
                    {
                        "name": "speckit.shared.sync",
                        "file": "commands/cmd.md",
                    }
                ]
            },
        }
        (second_dir / "extension.yml").write_text(yaml.dump(second_manifest))
        (second_dir / "commands" / "cmd.md").write_text("---\ndescription: Test\n---\n\nBody")

        manager = ExtensionManager(project_dir)
        manager.registry.add("ext-one", {"version": "1.0.0", "source": "local"})

        with pytest.raises(ValidationError, match="already provided by extension 'ext-one'"):
            manager.install_from_directory(second_dir, "0.1.0", register_commands=False)

    def test_remove_extension(self, extension_dir, project_dir):
        """Test removing an installed extension."""
        manager = ExtensionManager(project_dir)

        # Install extension
        manager.install_from_directory(extension_dir, "0.1.0", register_commands=False)

        ext_dir = project_dir / ".specify" / "extensions" / "test-ext"
        assert ext_dir.exists()

        # Remove extension
        result = manager.remove("test-ext", keep_config=False)

        assert result is True
        assert not manager.registry.is_installed("test-ext")
        assert not ext_dir.exists()

    def test_remove_nonexistent(self, project_dir):
        """Test removing non-existent extension."""
        manager = ExtensionManager(project_dir)

        result = manager.remove("nonexistent")
        assert result is False

    def test_list_installed(self, extension_dir, project_dir):
        """Test listing installed extensions."""
        manager = ExtensionManager(project_dir)

        # Initially empty
        assert len(manager.list_installed()) == 0

        # Install extension
        manager.install_from_directory(extension_dir, "0.1.0", register_commands=False)

        # Should have one extension
        installed = manager.list_installed()
        assert len(installed) == 1
        assert installed[0]["id"] == "test-ext"
        assert installed[0]["name"] == "Test Extension"
        assert installed[0]["version"] == "1.0.0"
        assert installed[0]["command_count"] == 1
        assert installed[0]["hook_count"] == 1

    def test_config_backup_on_remove(self, extension_dir, project_dir):
        """Test that config files are backed up on removal."""
        manager = ExtensionManager(project_dir)

        # Install extension
        manager.install_from_directory(extension_dir, "0.1.0", register_commands=False)

        # Create a config file
        ext_dir = project_dir / ".specify" / "extensions" / "test-ext"
        config_file = ext_dir / "test-ext-config.yml"
        config_file.write_text("test: config")

        # Remove extension (without keep_config)
        manager.remove("test-ext", keep_config=False)

        # Check backup was created (now in subdirectory per extension)
        backup_dir = project_dir / ".specify" / "extensions" / ".backup" / "test-ext"
        backup_file = backup_dir / "test-ext-config.yml"
        assert backup_file.exists()
        assert backup_file.read_text() == "test: config"


# ===== CommandRegistrar Tests =====

class TestCommandRegistrar:
    """Test CommandRegistrar command registration."""

    def test_kiro_cli_agent_config_present(self):
        """Kiro CLI should be mapped to .kiro/prompts and legacy q removed."""
        assert "kiro-cli" in CommandRegistrar.AGENT_CONFIGS
        assert CommandRegistrar.AGENT_CONFIGS["kiro-cli"]["dir"] == ".kiro/prompts"
        assert "q" not in CommandRegistrar.AGENT_CONFIGS

    def test_codex_agent_config_present(self):
        """Codex should be mapped to .agents/skills."""
        assert "codex" in CommandRegistrar.AGENT_CONFIGS
        assert CommandRegistrar.AGENT_CONFIGS["codex"]["dir"] == ".agents/skills"
        assert CommandRegistrar.AGENT_CONFIGS["codex"]["extension"] == "/SKILL.md"

    def test_pi_agent_config_present(self):
        """Pi should be mapped to .pi/prompts."""
        assert "pi" in CommandRegistrar.AGENT_CONFIGS
        cfg = CommandRegistrar.AGENT_CONFIGS["pi"]
        assert cfg["dir"] == ".pi/prompts"
        assert cfg["format"] == "markdown"
        assert cfg["args"] == "$ARGUMENTS"
        assert cfg["extension"] == ".md"

    def test_qwen_agent_config_is_markdown(self):
        """Qwen should use Markdown format with $ARGUMENTS (not TOML)."""
        assert "qwen" in CommandRegistrar.AGENT_CONFIGS
        cfg = CommandRegistrar.AGENT_CONFIGS["qwen"]
        assert cfg["dir"] == ".qwen/commands"
        assert cfg["format"] == "markdown"
        assert cfg["args"] == "$ARGUMENTS"
        assert cfg["extension"] == ".md"

    def test_parse_frontmatter_valid(self):
        """Test parsing valid YAML frontmatter."""
        content = """---
description: "Test command"
tools:
  - tool1
  - tool2
---

# Command body
$ARGUMENTS
"""
        registrar = CommandRegistrar()
        frontmatter, body = registrar.parse_frontmatter(content)

        assert frontmatter["description"] == "Test command"
        assert frontmatter["tools"] == ["tool1", "tool2"]
        assert "Command body" in body
        assert "$ARGUMENTS" in body

    def test_parse_frontmatter_no_frontmatter(self):
        """Test parsing content without frontmatter."""
        content = "# Just a command\n$ARGUMENTS"

        registrar = CommandRegistrar()
        frontmatter, body = registrar.parse_frontmatter(content)

        assert frontmatter == {}
        assert body == content

    def test_parse_frontmatter_non_mapping_returns_empty_dict(self):
        """Non-mapping YAML frontmatter should not crash downstream renderers."""
        content = """---
- item1
- item2
---

# Command body
"""
        registrar = CommandRegistrar()
        frontmatter, body = registrar.parse_frontmatter(content)

        assert frontmatter == {}
        assert "Command body" in body

    def test_render_frontmatter(self):
        """Test rendering frontmatter to YAML."""
        frontmatter = {
            "description": "Test command",
            "tools": ["tool1", "tool2"]
        }

        registrar = CommandRegistrar()
        output = registrar.render_frontmatter(frontmatter)

        assert output.startswith("---\n")
        assert output.endswith("---\n")
        assert "description: Test command" in output

    def test_render_frontmatter_unicode(self):
        """Test rendering frontmatter preserves non-ASCII characters."""
        frontmatter = {
            "description": "Prüfe Konformität der Implementierung"
        }

        registrar = CommandRegistrar()
        output = registrar.render_frontmatter(frontmatter)

        assert "Prüfe Konformität" in output
        assert "\\u" not in output

    def test_adjust_script_paths_does_not_mutate_input(self):
        """Path adjustments should not mutate caller-owned frontmatter dicts."""
        from specify_cli.agents import CommandRegistrar as AgentCommandRegistrar
        registrar = AgentCommandRegistrar()
        original = {
            "scripts": {
                "sh": "../../scripts/bash/setup-plan.sh {ARGS}",
                "ps": "../../scripts/powershell/setup-plan.ps1 {ARGS}",
            }
        }
        before = json.loads(json.dumps(original))

        adjusted = registrar._adjust_script_paths(original)

        assert original == before
        assert adjusted["scripts"]["sh"] == ".specify/scripts/bash/setup-plan.sh {ARGS}"
        assert adjusted["scripts"]["ps"] == ".specify/scripts/powershell/setup-plan.ps1 {ARGS}"

    def test_adjust_script_paths_preserves_extension_local_paths(self):
        """Extension-local script paths should not be rewritten into .specify/.specify."""
        from specify_cli.agents import CommandRegistrar as AgentCommandRegistrar
        registrar = AgentCommandRegistrar()
        original = {
            "scripts": {
                "sh": ".specify/extensions/test-ext/scripts/setup.sh {ARGS}",
                "ps": "scripts/powershell/setup-plan.ps1 {ARGS}",
            }
        }

        adjusted = registrar._adjust_script_paths(original)

        assert adjusted["scripts"]["sh"] == ".specify/extensions/test-ext/scripts/setup.sh {ARGS}"
        assert adjusted["scripts"]["ps"] == ".specify/scripts/powershell/setup-plan.ps1 {ARGS}"

    def test_rewrite_project_relative_paths_preserves_extension_local_body_paths(self):
        """Body rewrites should preserve extension-local assets while fixing top-level refs."""
        from specify_cli.agents import CommandRegistrar as AgentCommandRegistrar

        body = (
            "Read `.specify/extensions/test-ext/templates/spec.md`\n"
            "Run scripts/bash/setup-plan.sh\n"
        )

        rewritten = AgentCommandRegistrar.rewrite_project_relative_paths(body)

        assert ".specify/extensions/test-ext/templates/spec.md" in rewritten
        assert ".specify/scripts/bash/setup-plan.sh" in rewritten

    def test_render_toml_command_handles_embedded_triple_double_quotes(self):
        """TOML renderer should stay valid when body includes triple double-quotes."""
        from specify_cli.agents import CommandRegistrar as AgentCommandRegistrar
        registrar = AgentCommandRegistrar()
        output = registrar.render_toml_command(
            {"description": "x"},
            'line1\n"""danger"""\nline2',
            "extension:test-ext",
        )

        assert "prompt = '''" in output
        assert '"""danger"""' in output

    def test_render_toml_command_escapes_when_both_triple_quote_styles_exist(self):
        """If body has both triple quote styles, fall back to escaped basic string."""
        from specify_cli.agents import CommandRegistrar as AgentCommandRegistrar
        registrar = AgentCommandRegistrar()
        output = registrar.render_toml_command(
            {"description": "x"},
            'a """ b\nc \'\'\' d',
            "extension:test-ext",
        )

        assert 'prompt = "' in output
        assert "\\n" in output
        assert "\\\"\\\"\\\"" in output

    def test_render_toml_command_preserves_multiline_description(self):
        """Multiline descriptions should render as parseable TOML with preserved semantics."""
        from specify_cli.agents import CommandRegistrar as AgentCommandRegistrar

        registrar = AgentCommandRegistrar()
        output = registrar.render_toml_command(
            {"description": "first line\nsecond line\n"},
            "body",
            "extension:test-ext",
        )

        parsed = tomllib.loads(output)

        assert parsed["description"] == "first line\nsecond line\n"

    def test_render_toml_command_preserves_backslashes_in_body(self):
        """A backslash in the body (e.g. a Windows path) must not break TOML.

        A multiline basic string ("\"\"\"") processes backslash escapes, so
        ``C:\\Users`` (``\\U``) would render as invalid TOML; the body must
        round-trip with backslashes intact.
        """
        from specify_cli.agents import CommandRegistrar as AgentCommandRegistrar

        registrar = AgentCommandRegistrar()
        output = registrar.render_toml_command(
            {"description": "x"},
            r"Run C:\Users\dev\tool.exe then report.",
            "extension:test-ext",
        )
        parsed = tomllib.loads(output)  # must not raise
        assert parsed["prompt"].strip() == r"Run C:\Users\dev\tool.exe then report."

    def test_render_toml_command_handles_trailing_backslash(self):
        """A body ending in a backslash must round-trip without corruption."""
        from specify_cli.agents import CommandRegistrar as AgentCommandRegistrar

        registrar = AgentCommandRegistrar()
        output = registrar.render_toml_command(
            {"description": "x"},
            "path ends with sep\\",
            "extension:test-ext",
        )
        parsed = tomllib.loads(output)
        assert parsed["prompt"].strip() == "path ends with sep\\"

    def test_render_toml_command_backslash_with_both_triple_quotes_escapes(self):
        """Body with a backslash and both triple-quote styles → escaped basic string."""
        from specify_cli.agents import CommandRegistrar as AgentCommandRegistrar

        registrar = AgentCommandRegistrar()
        body = "a \\ b\nc \"\"\" d\ne ''' f"
        output = registrar.render_toml_command({"description": "x"}, body, "extension:test-ext")
        parsed = tomllib.loads(output)
        assert parsed["prompt"] == body

    def test_register_commands_for_claude(self, extension_dir, project_dir):
        """Test registering commands for Claude agent."""
        # Create .claude directory
        claude_dir = project_dir / ".claude" / "skills"
        claude_dir.mkdir(parents=True)

        ExtensionManager(project_dir)  # Initialize manager (side effects only)
        manifest = ExtensionManifest(extension_dir / "extension.yml")

        registrar = CommandRegistrar()
        registered = registrar.register_commands_for_claude(
            manifest,
            extension_dir,
            project_dir
        )

        assert len(registered) == 1
        assert "speckit.test-ext.hello" in registered

        # Check command file was created
        cmd_file = claude_dir / "speckit-test-ext-hello" / "SKILL.md"
        assert cmd_file.exists()

        content = cmd_file.read_text()
        assert "description: Test hello command" in content
        assert "test-ext" in content

    def test_command_with_aliases(self, project_dir, temp_dir):
        """Test registering a command with aliases."""
        import yaml

        # Create extension with command alias
        ext_dir = temp_dir / "ext-alias"
        ext_dir.mkdir()

        manifest_data = {
            "schema_version": "1.0",
            "extension": {
                "id": "ext-alias",
                "name": "Extension with Alias",
                "version": "1.0.0",
                "description": "Test",
            },
            "requires": {
                "speckit_version": ">=0.1.0",
            },
            "provides": {
                "commands": [
                    {
                        "name": "speckit.ext-alias.cmd",
                        "file": "commands/cmd.md",
                        "aliases": ["speckit.ext-alias.shortcut"],
                    }
                ]
            },
        }

        with open(ext_dir / "extension.yml", 'w') as f:
            yaml.dump(manifest_data, f)

        (ext_dir / "commands").mkdir()
        (ext_dir / "commands" / "cmd.md").write_text("---\ndescription: Test\n---\n\nTest")

        claude_dir = project_dir / ".claude" / "skills"
        claude_dir.mkdir(parents=True)

        manifest = ExtensionManifest(ext_dir / "extension.yml")
        registrar = CommandRegistrar()
        registered = registrar.register_commands_for_claude(manifest, ext_dir, project_dir)

        assert len(registered) == 2
        assert "speckit.ext-alias.cmd" in registered
        assert "speckit.ext-alias.shortcut" in registered
        assert (claude_dir / "speckit-ext-alias-cmd" / "SKILL.md").exists()
        assert (claude_dir / "speckit-ext-alias-shortcut" / "SKILL.md").exists()

    def test_unregister_commands_for_codex_skills_uses_mapped_names(self, project_dir):
        """Codex skill cleanup should use the same mapped names as registration."""
        skills_dir = project_dir / ".agents" / "skills"
        (skills_dir / "speckit-specify").mkdir(parents=True)
        (skills_dir / "speckit-specify" / "SKILL.md").write_text("body")
        (skills_dir / "speckit-shortcut").mkdir(parents=True)
        (skills_dir / "speckit-shortcut" / "SKILL.md").write_text("body")

        registrar = CommandRegistrar()
        registrar.unregister_commands(
            {"codex": ["speckit.specify", "speckit.shortcut"]},
            project_dir,
        )

        assert not (skills_dir / "speckit-specify" / "SKILL.md").exists()
        assert not (skills_dir / "speckit-shortcut" / "SKILL.md").exists()

    def test_unregister_commands_handles_legacy_dot_notated_files(self, project_dir):
        """Unregister should clean up both legacy dot-notated and new hyphenated files."""
        # 1. Mock an agent that uses hyphenated/formatted names (e.g. Cline)
        from specify_cli.agents import CommandRegistrar as AgentCommandRegistrar
        registrar = AgentCommandRegistrar()

        # We'll use "cline" since it has format_name
        assert "cline" in registrar.AGENT_CONFIGS
        cline_config = registrar.AGENT_CONFIGS["cline"]
        cline_dir = project_dir / cline_config["dir"]
        cline_dir.mkdir(parents=True, exist_ok=True)

        # 2. Create both legacy and new files
        # Command name: speckit.git.commit
        # Formatted name: speckit-git-commit
        cmd_name = "speckit.git.commit"
        formatted_name = "speckit-git-commit"

        legacy_file = cline_dir / f"{cmd_name}.md"
        formatted_file = cline_dir / f"{formatted_name}.md"

        legacy_file.write_text("legacy body")
        formatted_file.write_text("formatted body")

        assert legacy_file.exists()
        assert formatted_file.exists()

        # 3. Call unregister
        registrar.unregister_commands({"cline": [cmd_name]}, project_dir)

        # 4. Verify both are gone
        assert not legacy_file.exists(), "Legacy dot-notated file should be removed"
        assert (
            not formatted_file.exists()
        ), "Formatted hyphenated file should be removed"

    def test_register_commands_for_all_agents_distinguishes_codex_from_amp(self, extension_dir, project_dir):
        """A Codex project under .agents/skills should not implicitly activate Amp."""
        skills_dir = project_dir / ".agents" / "skills"
        skills_dir.mkdir(parents=True)

        manifest = ExtensionManifest(extension_dir / "extension.yml")
        registrar = CommandRegistrar()
        registered = registrar.register_commands_for_all_agents(manifest, extension_dir, project_dir)

        assert "codex" in registered
        assert "amp" not in registered
        assert not (project_dir / ".agents" / "commands").exists()

    def test_codex_skill_registration_writes_skill_frontmatter(self, extension_dir, project_dir):
        """Codex SKILL.md output should use skills-oriented frontmatter."""
        skills_dir = project_dir / ".agents" / "skills"
        skills_dir.mkdir(parents=True)

        manifest = ExtensionManifest(extension_dir / "extension.yml")
        registrar = CommandRegistrar()
        registrar.register_commands_for_agent("codex", manifest, extension_dir, project_dir)

        skill_file = skills_dir / "speckit-test-ext-hello" / "SKILL.md"
        assert skill_file.exists()

        content = skill_file.read_text()
        assert "name: speckit-test-ext-hello" in content
        assert "description: Test hello command" in content
        assert "compatibility:" in content
        assert "metadata:" in content
        assert "source: test-ext:commands/hello.md" in content
        assert "<!-- Extension:" not in content

    def test_codex_skill_registration_resolves_script_placeholders(self, project_dir, temp_dir):
        """Codex SKILL.md overrides should resolve script placeholders."""
        import yaml

        ext_dir = temp_dir / "ext-scripted"
        ext_dir.mkdir()
        (ext_dir / "commands").mkdir()

        manifest_data = {
            "schema_version": "1.0",
            "extension": {
                "id": "ext-scripted",
                "name": "Scripted Extension",
                "version": "1.0.0",
                "description": "Test",
            },
            "requires": {"speckit_version": ">=0.1.0"},
            "provides": {
                "commands": [
                    {
                        "name": "speckit.ext-scripted.plan",
                        "file": "commands/plan.md",
                        "description": "Scripted command",
                    }
                ]
            },
        }
        with open(ext_dir / "extension.yml", "w") as f:
            yaml.dump(manifest_data, f)

        (ext_dir / "commands" / "plan.md").write_text(
            """---
description: "Scripted command"
scripts:
  sh: ../../scripts/bash/setup-plan.sh --json "{ARGS}"
  ps: ../../scripts/powershell/setup-plan.ps1 -Json
---

Run {SCRIPT}
Agent __AGENT__
"""
        )

        init_options = project_dir / ".specify" / "init-options.json"
        init_options.parent.mkdir(parents=True, exist_ok=True)
        init_options.write_text('{"ai":"codex","ai_skills":true,"script":"sh"}')

        skills_dir = project_dir / ".agents" / "skills"
        skills_dir.mkdir(parents=True)

        manifest = ExtensionManifest(ext_dir / "extension.yml")
        registrar = CommandRegistrar()
        registrar.register_commands_for_agent("codex", manifest, ext_dir, project_dir)

        skill_file = skills_dir / "speckit-ext-scripted-plan" / "SKILL.md"
        assert skill_file.exists()

        content = skill_file.read_text()
        assert "{SCRIPT}" not in content
        assert "__AGENT__" not in content
        assert "{ARGS}" not in content
        assert '.specify/scripts/bash/setup-plan.sh --json "$ARGUMENTS"' in content

    @pytest.mark.parametrize("agent_name,skills_path", [
        ("codex", ".agents/skills"),
        ("kimi", ".kimi-code/skills"),
        ("claude", ".claude/skills"),
        ("cursor-agent", ".cursor/skills"),
        ("trae", ".trae/skills"),
        ("agy", ".agents/skills"),
    ])
    def test_all_skill_agents_register_commands_with_resolved_placeholders(
        self, project_dir, temp_dir, agent_name, skills_path
    ):
        """All SKILL.md agents must produce fully resolved SKILL.md files when commands are registered."""
        import yaml

        ext_dir = temp_dir / f"ext-{agent_name}"
        ext_dir.mkdir()
        (ext_dir / "commands").mkdir()

        manifest_data = {
            "schema_version": "1.0",
            "extension": {
                "id": f"ext-{agent_name}",
                "name": "Scripted Extension",
                "version": "1.0.0",
                "description": "Test",
            },
            "requires": {"speckit_version": ">=0.1.0"},
            "provides": {
                "commands": [
                    {
                        "name": f"speckit.ext-{agent_name}.run",
                        "file": "commands/run.md",
                        "description": "Scripted command",
                    }
                ]
            },
        }
        with open(ext_dir / "extension.yml", "w") as f:
            yaml.dump(manifest_data, f)

        (ext_dir / "commands" / "run.md").write_text(
            "---\n"
            "description: Scripted command\n"
            "scripts:\n"
            '  sh: ../../scripts/bash/setup-plan.sh --json "{ARGS}"\n'
            "---\n\n"
            "Run {SCRIPT}\n"
            "Agent is __AGENT__.\n"
        )

        init_options = project_dir / ".specify" / "init-options.json"
        init_options.parent.mkdir(parents=True, exist_ok=True)
        init_options.write_text(f'{{"ai":"{agent_name}","script":"sh"}}')

        skills_dir = project_dir
        for part in skills_path.split("/"):
            skills_dir = skills_dir / part
        skills_dir.mkdir(parents=True)

        manifest = ExtensionManifest(ext_dir / "extension.yml")
        registrar = CommandRegistrar()
        registrar.register_commands_for_agent(agent_name, manifest, ext_dir, project_dir)

        skill_dir_name = f"speckit-ext-{agent_name}-run"
        skill_file = skills_dir / skill_dir_name / "SKILL.md"
        assert skill_file.exists(), f"SKILL.md not created for {agent_name}"

        content = skill_file.read_text()
        assert "{SCRIPT}" not in content, f"{{SCRIPT}} not resolved for {agent_name}"
        assert "__AGENT__" not in content, f"__AGENT__ not resolved for {agent_name}"
        assert "{ARGS}" not in content, f"{{ARGS}} not resolved for {agent_name}"
        assert '.specify/scripts/bash/setup-plan.sh' in content

    def test_codex_skill_alias_frontmatter_matches_alias_name(self, project_dir, temp_dir):
        """Codex alias skills should render their own matching `name:` frontmatter."""
        import yaml

        ext_dir = temp_dir / "ext-alias-skill"
        ext_dir.mkdir()
        (ext_dir / "commands").mkdir()

        manifest_data = {
            "schema_version": "1.0",
            "extension": {
                "id": "ext-alias-skill",
                "name": "Alias Skill Extension",
                "version": "1.0.0",
                "description": "Test",
            },
            "requires": {"speckit_version": ">=0.1.0"},
            "provides": {
                "commands": [
                    {
                        "name": "speckit.ext-alias-skill.cmd",
                        "file": "commands/cmd.md",
                        "aliases": ["speckit.ext-alias-skill.shortcut"],
                    }
                ]
            },
        }
        with open(ext_dir / "extension.yml", "w") as f:
            yaml.dump(manifest_data, f)

        (ext_dir / "commands" / "cmd.md").write_text("---\ndescription: Alias skill\n---\n\nBody\n")

        skills_dir = project_dir / ".agents" / "skills"
        skills_dir.mkdir(parents=True)

        manifest = ExtensionManifest(ext_dir / "extension.yml")
        registrar = CommandRegistrar()
        registrar.register_commands_for_agent("codex", manifest, ext_dir, project_dir)

        primary = skills_dir / "speckit-ext-alias-skill-cmd" / "SKILL.md"
        alias = skills_dir / "speckit-ext-alias-skill-shortcut" / "SKILL.md"

        assert primary.exists()
        assert alias.exists()
        assert "name: speckit-ext-alias-skill-cmd" in primary.read_text()
        assert "name: speckit-ext-alias-skill-shortcut" in alias.read_text()

    def test_codex_skill_registration_uses_fallback_script_variant_without_init_options(
        self, project_dir, temp_dir
    ):
        """Codex placeholder substitution should still work without init-options.json."""
        import yaml

        ext_dir = temp_dir / "ext-script-fallback"
        ext_dir.mkdir()
        (ext_dir / "commands").mkdir()

        manifest_data = {
            "schema_version": "1.0",
            "extension": {
                "id": "ext-script-fallback",
                "name": "Script fallback",
                "version": "1.0.0",
                "description": "Test",
            },
            "requires": {"speckit_version": ">=0.1.0"},
            "provides": {
                "commands": [
                    {
                        "name": "speckit.ext-script-fallback.plan",
                        "file": "commands/plan.md",
                    }
                ]
            },
        }
        with open(ext_dir / "extension.yml", "w") as f:
            yaml.dump(manifest_data, f)

        (ext_dir / "commands" / "plan.md").write_text(
            """---
description: "Fallback scripted command"
scripts:
  sh: ../../scripts/bash/setup-plan.sh --json "{ARGS}"
  ps: ../../scripts/powershell/setup-plan.ps1 -Json
---

Run {SCRIPT}
"""
        )

        # Intentionally do NOT create .specify/init-options.json
        skills_dir = project_dir / ".agents" / "skills"
        skills_dir.mkdir(parents=True)

        manifest = ExtensionManifest(ext_dir / "extension.yml")
        registrar = CommandRegistrar()
        registrar.register_commands_for_agent("codex", manifest, ext_dir, project_dir)

        skill_file = skills_dir / "speckit-ext-script-fallback-plan" / "SKILL.md"
        assert skill_file.exists()

        content = skill_file.read_text()
        assert "{SCRIPT}" not in content
        if platform.system().lower().startswith("win"):
            assert ".specify/scripts/powershell/setup-plan.ps1 -Json" in content
        else:
            assert '.specify/scripts/bash/setup-plan.sh --json "$ARGUMENTS"' in content

    def test_codex_skill_registration_handles_non_dict_init_options(
        self, project_dir, temp_dir
    ):
        """Non-dict init-options payloads should not crash skill placeholder resolution."""
        import yaml

        ext_dir = temp_dir / "ext-script-list-init"
        ext_dir.mkdir()
        (ext_dir / "commands").mkdir()

        manifest_data = {
            "schema_version": "1.0",
            "extension": {
                "id": "ext-script-list-init",
                "name": "List init options",
                "version": "1.0.0",
                "description": "Test",
            },
            "requires": {"speckit_version": ">=0.1.0"},
            "provides": {
                "commands": [
                    {
                        "name": "speckit.ext-script-list-init.plan",
                        "file": "commands/plan.md",
                    }
                ]
            },
        }
        with open(ext_dir / "extension.yml", "w") as f:
            yaml.dump(manifest_data, f)

        (ext_dir / "commands" / "plan.md").write_text(
            """---
description: "List init scripted command"
scripts:
  sh: ../../scripts/bash/setup-plan.sh --json "{ARGS}"
---

Run {SCRIPT}
"""
        )

        init_options = project_dir / ".specify" / "init-options.json"
        init_options.parent.mkdir(parents=True, exist_ok=True)
        init_options.write_text("[]")

        skills_dir = project_dir / ".agents" / "skills"
        skills_dir.mkdir(parents=True)

        manifest = ExtensionManifest(ext_dir / "extension.yml")
        registrar = CommandRegistrar()
        registrar.register_commands_for_agent("codex", manifest, ext_dir, project_dir)

        content = (skills_dir / "speckit-ext-script-list-init-plan" / "SKILL.md").read_text()
        assert '.specify/scripts/bash/setup-plan.sh --json "$ARGUMENTS"' in content

    def test_codex_skill_registration_fallback_prefers_powershell_on_windows(
        self, project_dir, temp_dir, monkeypatch
    ):
        """Without init metadata, Windows fallback should prefer ps scripts over sh."""
        import yaml

        monkeypatch.setattr("specify_cli.agents.platform.system", lambda: "Windows")

        ext_dir = temp_dir / "ext-script-windows-fallback"
        ext_dir.mkdir()
        (ext_dir / "commands").mkdir()

        manifest_data = {
            "schema_version": "1.0",
            "extension": {
                "id": "ext-script-windows-fallback",
                "name": "Script fallback windows",
                "version": "1.0.0",
                "description": "Test",
            },
            "requires": {"speckit_version": ">=0.1.0"},
            "provides": {
                "commands": [
                    {
                        "name": "speckit.ext-script-windows-fallback.plan",
                        "file": "commands/plan.md",
                    }
                ]
            },
        }
        with open(ext_dir / "extension.yml", "w") as f:
            yaml.dump(manifest_data, f)

        (ext_dir / "commands" / "plan.md").write_text(
            """---
description: "Windows fallback scripted command"
scripts:
  sh: ../../scripts/bash/setup-plan.sh --json "{ARGS}"
  ps: ../../scripts/powershell/setup-plan.ps1 -Json
---

Run {SCRIPT}
"""
        )

        skills_dir = project_dir / ".agents" / "skills"
        skills_dir.mkdir(parents=True)

        manifest = ExtensionManifest(ext_dir / "extension.yml")
        registrar = CommandRegistrar()
        registrar.register_commands_for_agent("codex", manifest, ext_dir, project_dir)

        skill_file = skills_dir / "speckit-ext-script-windows-fallback-plan" / "SKILL.md"
        assert skill_file.exists()

        content = skill_file.read_text()
        assert ".specify/scripts/powershell/setup-plan.ps1 -Json" in content
        assert ".specify/scripts/bash/setup-plan.sh" not in content

    def test_register_commands_for_copilot(self, extension_dir, project_dir):
        """Test registering commands for Copilot agent with .agent.md extension."""
        # Create .github/agents directory (Copilot project)
        agents_dir = project_dir / ".github" / "agents"
        agents_dir.mkdir(parents=True)

        manifest = ExtensionManifest(extension_dir / "extension.yml")

        registrar = CommandRegistrar()
        registered = registrar.register_commands_for_agent(
            "copilot", manifest, extension_dir, project_dir
        )

        assert len(registered) == 1
        assert "speckit.test-ext.hello" in registered

        # Verify command file uses .agent.md extension
        cmd_file = agents_dir / "speckit.test-ext.hello.agent.md"
        assert cmd_file.exists()

        # Verify NO plain .md file was created
        plain_md_file = agents_dir / "speckit.test-ext.hello.md"
        assert not plain_md_file.exists()

        content = cmd_file.read_text()
        assert "description: Test hello command" in content
        assert "test-ext" in content

    def test_dev_register_commands_symlinks_rendered_copilot_agent(
        self, extension_dir, project_dir, temp_dir
    ):
        """Dev-mode registration should symlink agent files to rendered outputs."""
        if not can_create_symlink(temp_dir):
            pytest.skip("Current platform/user cannot create symlinks")

        agents_dir = project_dir / ".github" / "agents"
        agents_dir.mkdir(parents=True)

        manifest = ExtensionManifest(extension_dir / "extension.yml")
        registrar = CommandRegistrar()
        registered = registrar.register_commands_for_agent(
            "copilot",
            manifest,
            extension_dir,
            project_dir,
            link_outputs=True,
        )

        assert registered == ["speckit.test-ext.hello"]

        cmd_file = agents_dir / "speckit.test-ext.hello.agent.md"
        assert cmd_file.is_symlink()

        target = cmd_file.resolve()
        assert ".specify-dev" in target.parts
        assert target.is_file()
        assert "Extension: test-ext" in cmd_file.read_text(encoding="utf-8")

    def test_dev_register_commands_replaces_codex_dev_symlink(
        self, extension_dir, project_dir, temp_dir
    ):
        """Codex dev registration should replace prior symlinks with real files."""
        if not can_create_symlink(temp_dir):
            pytest.skip("Current platform/user cannot create symlinks")

        skill_file = (
            project_dir
            / ".agents"
            / "skills"
            / "speckit-test-ext-hello"
            / "SKILL.md"
        )
        skill_file.parent.mkdir(parents=True)
        cache_file = (
            extension_dir
            / ".specify-dev"
            / "agent-commands"
            / "codex"
            / "speckit-test-ext-hello"
            / "SKILL.md"
        )
        cache_file.parent.mkdir(parents=True)
        cache_file.write_text("old linked content", encoding="utf-8")
        os.symlink(os.path.relpath(cache_file, skill_file.parent), skill_file)

        manifest = ExtensionManifest(extension_dir / "extension.yml")
        registrar = CommandRegistrar()
        registrar.register_commands_for_agent(
            "codex",
            manifest,
            extension_dir,
            project_dir,
            link_outputs=True,
        )

        assert skill_file.exists()
        assert not skill_file.is_symlink()
        assert "name: speckit-test-ext-hello" in skill_file.read_text(
            encoding="utf-8"
        )
        assert cache_file.read_text(encoding="utf-8") == "old linked content"

    def test_dev_register_commands_falls_back_to_copy_when_symlink_fails(
        self, extension_dir, project_dir, monkeypatch
    ):
        """Dev-mode registration stays functional when symlinks are unavailable."""
        agents_dir = project_dir / ".github" / "agents"
        agents_dir.mkdir(parents=True)

        def raise_symlink_error(target, link):
            raise OSError("symlink unavailable")

        monkeypatch.setattr("specify_cli.agents.os.symlink", raise_symlink_error)

        manifest = ExtensionManifest(extension_dir / "extension.yml")
        registrar = CommandRegistrar()
        registrar.register_commands_for_agent(
            "copilot",
            manifest,
            extension_dir,
            project_dir,
            link_outputs=True,
        )

        cmd_file = agents_dir / "speckit.test-ext.hello.agent.md"
        assert cmd_file.exists()
        assert not cmd_file.is_symlink()
        assert "Extension: test-ext" in cmd_file.read_text(encoding="utf-8")
        assert (
            extension_dir
            / ".specify-dev"
            / "agent-commands"
            / "copilot"
            / "speckit.test-ext.hello.agent.md"
        ).exists()

    def test_dev_register_commands_falls_back_to_copy_when_relpath_fails(
        self, extension_dir, project_dir, monkeypatch
    ):
        """Dev-mode registration stays functional across Windows drive roots."""
        agents_dir = project_dir / ".github" / "agents"
        agents_dir.mkdir(parents=True)

        def raise_relpath_error(path, start=None):
            raise ValueError("path is on mount 'D:', start on mount 'C:'")

        monkeypatch.setattr("specify_cli.agents.os.path.relpath", raise_relpath_error)

        manifest = ExtensionManifest(extension_dir / "extension.yml")
        registrar = CommandRegistrar()
        registrar.register_commands_for_agent(
            "copilot",
            manifest,
            extension_dir,
            project_dir,
            link_outputs=True,
        )

        cmd_file = agents_dir / "speckit.test-ext.hello.agent.md"
        assert cmd_file.exists()
        assert not cmd_file.is_symlink()
        assert "Extension: test-ext" in cmd_file.read_text(encoding="utf-8")
        assert (
            extension_dir
            / ".specify-dev"
            / "agent-commands"
            / "copilot"
            / "speckit.test-ext.hello.agent.md"
        ).exists()

    def test_dev_register_commands_falls_back_to_copy_when_cache_write_fails(
        self, extension_dir, project_dir, monkeypatch
    ):
        """Dev-mode registration stays functional when the dev cache is unwritable."""
        agents_dir = project_dir / ".github" / "agents"
        agents_dir.mkdir(parents=True)
        original_write_text = Path.write_text

        def raise_cache_write_error(path, *args, **kwargs):
            if ".specify-dev" in path.parts:
                raise OSError("cache is not writable")
            return original_write_text(path, *args, **kwargs)

        monkeypatch.setattr(Path, "write_text", raise_cache_write_error)

        manifest = ExtensionManifest(extension_dir / "extension.yml")
        registrar = CommandRegistrar()
        registrar.register_commands_for_agent(
            "copilot",
            manifest,
            extension_dir,
            project_dir,
            link_outputs=True,
        )

        cmd_file = agents_dir / "speckit.test-ext.hello.agent.md"
        assert cmd_file.exists()
        assert not cmd_file.is_symlink()
        assert "Extension: test-ext" in cmd_file.read_text(encoding="utf-8")
        assert not (
            extension_dir
            / ".specify-dev"
            / "agent-commands"
            / "copilot"
            / "speckit.test-ext.hello.agent.md"
        ).exists()

    def test_dev_register_commands_rejects_cache_path_traversal(self, temp_dir):
        """Dev-mode cache writes must stay inside the agent cache root."""
        from specify_cli.agents import CommandRegistrar as AgentCommandRegistrar

        source_dir = temp_dir / "extension"
        source_dir.mkdir()
        commands_dir = temp_dir / "commands"
        commands_dir.mkdir()

        with pytest.raises(ValueError, match="escapes directory"):
            AgentCommandRegistrar._write_registered_output(
                commands_dir / "safe.md",
                "content",
                source_dir,
                "copilot",
                "../escaped",
                ".md",
                True,
            )

        assert not (
            source_dir
            / ".specify-dev"
            / "agent-commands"
            / "escaped.md"
        ).exists()

    def test_copilot_companion_prompt_created(self, extension_dir, project_dir):
        """Test that companion .prompt.md files are created in .github/prompts/."""
        agents_dir = project_dir / ".github" / "agents"
        agents_dir.mkdir(parents=True)

        manifest = ExtensionManifest(extension_dir / "extension.yml")

        registrar = CommandRegistrar()
        registrar.register_commands_for_agent(
            "copilot", manifest, extension_dir, project_dir
        )

        # Verify companion .prompt.md file exists
        prompt_file = project_dir / ".github" / "prompts" / "speckit.test-ext.hello.prompt.md"
        assert prompt_file.exists()

        # Verify content has correct agent frontmatter
        content = prompt_file.read_text()
        assert content == "---\nagent: speckit.test-ext.hello\n---\n"

    def test_copilot_aliases_get_companion_prompts(self, project_dir, temp_dir):
        """Test that aliases also get companion .prompt.md files for Copilot."""
        import yaml

        ext_dir = temp_dir / "ext-alias-copilot"
        ext_dir.mkdir()

        manifest_data = {
            "schema_version": "1.0",
            "extension": {
                "id": "ext-alias-copilot",
                "name": "Extension with Alias",
                "version": "1.0.0",
                "description": "Test",
            },
            "requires": {"speckit_version": ">=0.1.0"},
            "provides": {
                "commands": [
                    {
                        "name": "speckit.ext-alias-copilot.cmd",
                        "file": "commands/cmd.md",
                        "aliases": ["speckit.ext-alias-copilot.shortcut"],
                    }
                ]
            },
        }

        with open(ext_dir / "extension.yml", "w") as f:
            yaml.dump(manifest_data, f)

        (ext_dir / "commands").mkdir()
        (ext_dir / "commands" / "cmd.md").write_text(
            "---\ndescription: Test\n---\n\nTest"
        )

        # Set up Copilot project
        (project_dir / ".github" / "agents").mkdir(parents=True)

        manifest = ExtensionManifest(ext_dir / "extension.yml")
        registrar = CommandRegistrar()
        registered = registrar.register_commands_for_agent(
            "copilot", manifest, ext_dir, project_dir
        )

        assert len(registered) == 2

        # Both primary and alias get companion .prompt.md
        prompts_dir = project_dir / ".github" / "prompts"
        assert (prompts_dir / "speckit.ext-alias-copilot.cmd.prompt.md").exists()
        assert (prompts_dir / "speckit.ext-alias-copilot.shortcut.prompt.md").exists()

    def test_non_copilot_agent_no_companion_file(self, extension_dir, project_dir):
        """Test that non-copilot agents do NOT create .prompt.md files."""
        claude_dir = project_dir / ".claude" / "skills"
        claude_dir.mkdir(parents=True)

        manifest = ExtensionManifest(extension_dir / "extension.yml")

        registrar = CommandRegistrar()
        registrar.register_commands_for_agent(
            "claude", manifest, extension_dir, project_dir
        )

        # No .github/prompts directory should exist
        prompts_dir = project_dir / ".github" / "prompts"
        assert not prompts_dir.exists()

    def test_unregister_skill_removes_parent_directory(self, project_dir, temp_dir):
        """Unregistering a SKILL.md command should remove the empty parent subdirectory."""
        import yaml

        ext_dir = temp_dir / "cleanup-ext"
        ext_dir.mkdir()
        (ext_dir / "commands").mkdir()

        manifest_data = {
            "schema_version": "1.0",
            "extension": {
                "id": "cleanup-ext",
                "name": "Cleanup Extension",
                "version": "1.0.0",
                "description": "Test",
            },
            "requires": {"speckit_version": ">=0.1.0"},
            "provides": {
                "commands": [
                    {
                        "name": "speckit.cleanup-ext.run",
                        "file": "commands/run.md",
                        "description": "Run",
                    }
                ]
            },
        }
        with open(ext_dir / "extension.yml", "w") as f:
            yaml.dump(manifest_data, f)
        (ext_dir / "commands" / "run.md").write_text("---\ndescription: Run\n---\n\nBody")

        skills_dir = project_dir / ".agents" / "skills"
        skills_dir.mkdir(parents=True)

        registrar = CommandRegistrar()
        from specify_cli.extensions import ExtensionManifest
        manifest = ExtensionManifest(ext_dir / "extension.yml")
        registrar.register_commands_for_agent("codex", manifest, ext_dir, project_dir)

        skill_subdir = skills_dir / "speckit-cleanup-ext-run"
        assert skill_subdir.exists(), "Skill subdirectory should exist after registration"
        assert (skill_subdir / "SKILL.md").exists()

        registrar.unregister_commands({"codex": ["speckit.cleanup-ext.run"]}, project_dir)

        assert not (skill_subdir / "SKILL.md").exists(), "SKILL.md should be removed"
        assert not skill_subdir.exists(), "Empty parent subdirectory should be removed"


# ===== Utility Function Tests =====

class TestVersionSatisfies:
    """Test version_satisfies utility function."""

    def test_version_satisfies_simple(self):
        """Test simple version comparison."""
        assert version_satisfies("1.0.0", ">=1.0.0")
        assert version_satisfies("1.0.1", ">=1.0.0")
        assert not version_satisfies("0.9.9", ">=1.0.0")

    def test_version_satisfies_range(self):
        """Test version range."""
        assert version_satisfies("1.5.0", ">=1.0.0,<2.0.0")
        assert not version_satisfies("2.0.0", ">=1.0.0,<2.0.0")
        assert not version_satisfies("0.9.0", ">=1.0.0,<2.0.0")

    def test_version_satisfies_complex(self):
        """Test complex version specifier."""
        assert version_satisfies("1.0.5", ">=1.0.0,!=1.0.3")
        assert not version_satisfies("1.0.3", ">=1.0.0,!=1.0.3")

    def test_version_satisfies_prerelease(self):
        """Prerelease builds should satisfy compatible lower bounds, but not higher bounds."""
        assert version_satisfies("0.8.8.dev0", ">=0.2.0")
        assert not version_satisfies("0.2.0.dev0", ">=0.2.0")
        assert not version_satisfies("0.8.7.dev1", ">=0.8.8")

    def test_version_satisfies_invalid(self):
        """Test invalid version strings."""
        assert not version_satisfies("invalid", ">=1.0.0")
        assert not version_satisfies("1.0.0", "invalid specifier")


# ===== Integration Tests =====

class TestIntegration:
    """Integration tests for complete workflows."""

    def test_full_install_and_remove_workflow(self, extension_dir, project_dir):
        """Test complete installation and removal workflow."""
        # Create Claude directory
        (project_dir / ".claude" / "skills").mkdir(parents=True)

        manager = ExtensionManager(project_dir)

        # Install
        manager.install_from_directory(
            extension_dir,
            "0.1.0",
            register_commands=True
        )

        # Verify installation
        assert manager.registry.is_installed("test-ext")
        installed = manager.list_installed()
        assert len(installed) == 1
        assert installed[0]["id"] == "test-ext"

        # Verify command registered
        cmd_file = project_dir / ".claude" / "skills" / "speckit-test-ext-hello" / "SKILL.md"
        assert cmd_file.exists()

        # Verify registry has registered commands (now a dict keyed by agent)
        metadata = manager.registry.get("test-ext")
        registered_commands = metadata["registered_commands"]
        # Check that the command is registered for at least one agent
        assert any(
            "speckit.test-ext.hello" in cmds
            for cmds in registered_commands.values()
        )

        # Remove
        result = manager.remove("test-ext")
        assert result is True

        # Verify removal
        assert not manager.registry.is_installed("test-ext")
        assert not cmd_file.exists()
        assert len(manager.list_installed()) == 0

    def test_copilot_cleanup_removes_prompt_files(self, extension_dir, project_dir):
        """Test that removing a Copilot extension also removes .prompt.md files."""
        agents_dir = project_dir / ".github" / "agents"
        agents_dir.mkdir(parents=True)

        manager = ExtensionManager(project_dir)
        manager.install_from_directory(extension_dir, "0.1.0", register_commands=True)

        # Verify copilot was detected and registered
        metadata = manager.registry.get("test-ext")
        assert "copilot" in metadata["registered_commands"]

        # Verify files exist before cleanup
        agent_file = agents_dir / "speckit.test-ext.hello.agent.md"
        prompt_file = project_dir / ".github" / "prompts" / "speckit.test-ext.hello.prompt.md"
        assert agent_file.exists()
        assert prompt_file.exists()

        # Use the extension manager to remove — exercises the copilot prompt cleanup code
        result = manager.remove("test-ext")
        assert result is True

        assert not agent_file.exists()
        assert not prompt_file.exists()

    def test_multiple_extensions(self, temp_dir, project_dir):
        """Test installing multiple extensions."""
        import yaml

        # Create two extensions
        for i in range(1, 3):
            ext_dir = temp_dir / f"ext{i}"
            ext_dir.mkdir()

            manifest_data = {
                "schema_version": "1.0",
                "extension": {
                    "id": f"ext{i}",
                    "name": f"Extension {i}",
                    "version": "1.0.0",
                    "description": f"Extension {i}",
                },
                "requires": {"speckit_version": ">=0.1.0"},
                "provides": {
                    "commands": [
                        {
                            "name": f"speckit.ext{i}.cmd",
                            "file": "commands/cmd.md",
                        }
                    ]
                },
            }

            with open(ext_dir / "extension.yml", 'w') as f:
                yaml.dump(manifest_data, f)

            (ext_dir / "commands").mkdir()
            (ext_dir / "commands" / "cmd.md").write_text("---\ndescription: Test\n---\nTest")

        manager = ExtensionManager(project_dir)

        # Install both
        manager.install_from_directory(temp_dir / "ext1", "0.1.0", register_commands=False)
        manager.install_from_directory(temp_dir / "ext2", "0.1.0", register_commands=False)

        # Verify both installed
        installed = manager.list_installed()
        assert len(installed) == 2
        assert {ext["id"] for ext in installed} == {"ext1", "ext2"}

        # Remove first
        manager.remove("ext1")

        # Verify only second remains
        installed = manager.list_installed()
        assert len(installed) == 1
        assert installed[0]["id"] == "ext2"


# ===== Extension Catalog Tests =====


class TestExtensionCatalog:
    """Test extension catalog functionality."""

    def test_catalog_initialization(self, temp_dir):
        """Test catalog initialization."""
        project_dir = temp_dir / "project"
        project_dir.mkdir()
        (project_dir / ".specify").mkdir()

        catalog = ExtensionCatalog(project_dir)

        assert catalog.project_root == project_dir
        assert catalog.cache_dir == project_dir / ".specify" / "extensions" / ".cache"

    def test_cache_directory_creation(self, temp_dir):
        """Test catalog cache directory is created when fetching."""
        project_dir = temp_dir / "project"
        project_dir.mkdir()
        (project_dir / ".specify").mkdir()

        catalog = ExtensionCatalog(project_dir)

        # Create mock catalog data
        catalog_data = {
            "schema_version": "1.0",
            "extensions": {
                "test-ext": {
                    "name": "Test Extension",
                    "id": "test-ext",
                    "version": "1.0.0",
                    "description": "Test",
                }
            },
        }

        # Manually save to cache to test cache reading
        catalog.cache_dir.mkdir(parents=True, exist_ok=True)
        catalog.cache_file.write_text(json.dumps(catalog_data))
        catalog.cache_metadata_file.write_text(
            json.dumps(
                {
                    "cached_at": datetime.now(timezone.utc).isoformat(),
                    "catalog_url": "http://test.com/catalog.json",
                }
            )
        )

        # Should use cache
        result = catalog.fetch_catalog()
        assert result == catalog_data

    def test_cache_expiration(self, temp_dir):
        """Test that expired cache is not used."""
        project_dir = temp_dir / "project"
        project_dir.mkdir()
        (project_dir / ".specify").mkdir()

        catalog = ExtensionCatalog(project_dir)

        # Create expired cache
        catalog.cache_dir.mkdir(parents=True, exist_ok=True)
        catalog_data = {"schema_version": "1.0", "extensions": {}}
        catalog.cache_file.write_text(json.dumps(catalog_data))

        # Set cache time to 2 hours ago (expired)
        expired_time = datetime.now(timezone.utc).timestamp() - 7200
        expired_datetime = datetime.fromtimestamp(expired_time, tz=timezone.utc)
        catalog.cache_metadata_file.write_text(
            json.dumps(
                {
                    "cached_at": expired_datetime.isoformat(),
                    "catalog_url": "http://test.com/catalog.json",
                }
            )
        )

        # Cache should be invalid
        assert not catalog.is_cache_valid()

    def test_search_all_extensions(self, temp_dir):
        """Test searching all extensions without filters."""
        import yaml as yaml_module

        project_dir = temp_dir / "project"
        project_dir.mkdir()
        (project_dir / ".specify").mkdir()

        # Use a single-catalog config so community extensions don't interfere
        config_path = project_dir / ".specify" / "extension-catalogs.yml"
        with open(config_path, "w") as f:
            yaml_module.dump(
                {
                    "catalogs": [
                        {
                            "name": "test-catalog",
                            "url": ExtensionCatalog.DEFAULT_CATALOG_URL,
                            "priority": 1,
                            "install_allowed": True,
                        }
                    ]
                },
                f,
            )

        catalog = ExtensionCatalog(project_dir)

        # Create mock catalog
        catalog_data = {
            "schema_version": "1.0",
            "extensions": {
                "jira": {
                    "name": "Jira Integration",
                    "id": "jira",
                    "version": "1.0.0",
                    "description": "Jira integration",
                    "author": "Stats Perform",
                    "tags": ["issue-tracking", "jira"],
                    "verified": True,
                },
                "linear": {
                    "name": "Linear Integration",
                    "id": "linear",
                    "version": "0.9.0",
                    "description": "Linear integration",
                    "author": "Community",
                    "tags": ["issue-tracking"],
                    "verified": False,
                },
            },
        }

        # Save to cache
        catalog.cache_dir.mkdir(parents=True, exist_ok=True)
        catalog.cache_file.write_text(json.dumps(catalog_data))
        catalog.cache_metadata_file.write_text(
            json.dumps(
                {
                    "cached_at": datetime.now(timezone.utc).isoformat(),
                    "catalog_url": "http://test.com",
                }
            )
        )

        # Search without filters
        results = catalog.search()
        assert len(results) == 2

    def test_search_by_query(self, temp_dir):
        """Test searching by query text."""
        import yaml as yaml_module

        project_dir = temp_dir / "project"
        project_dir.mkdir()
        (project_dir / ".specify").mkdir()

        # Use a single-catalog config so community extensions don't interfere
        config_path = project_dir / ".specify" / "extension-catalogs.yml"
        with open(config_path, "w") as f:
            yaml_module.dump(
                {
                    "catalogs": [
                        {
                            "name": "test-catalog",
                            "url": ExtensionCatalog.DEFAULT_CATALOG_URL,
                            "priority": 1,
                            "install_allowed": True,
                        }
                    ]
                },
                f,
            )

        catalog = ExtensionCatalog(project_dir)

        # Create mock catalog
        catalog_data = {
            "schema_version": "1.0",
            "extensions": {
                "jira": {
                    "name": "Jira Integration",
                    "id": "jira",
                    "version": "1.0.0",
                    "description": "Jira issue tracking",
                    "tags": ["jira"],
                },
                "linear": {
                    "name": "Linear Integration",
                    "id": "linear",
                    "version": "1.0.0",
                    "description": "Linear project management",
                    "tags": ["linear"],
                },
            },
        }

        catalog.cache_dir.mkdir(parents=True, exist_ok=True)
        catalog.cache_file.write_text(json.dumps(catalog_data))
        catalog.cache_metadata_file.write_text(
            json.dumps(
                {
                    "cached_at": datetime.now(timezone.utc).isoformat(),
                    "catalog_url": "http://test.com",
                }
            )
        )

        # Search for "jira"
        results = catalog.search(query="jira")
        assert len(results) == 1
        assert results[0]["id"] == "jira"

    def test_search_by_tag(self, temp_dir):
        """Test searching by tag."""
        import yaml as yaml_module

        project_dir = temp_dir / "project"
        project_dir.mkdir()
        (project_dir / ".specify").mkdir()

        # Use a single-catalog config so community extensions don't interfere
        config_path = project_dir / ".specify" / "extension-catalogs.yml"
        with open(config_path, "w") as f:
            yaml_module.dump(
                {
                    "catalogs": [
                        {
                            "name": "test-catalog",
                            "url": ExtensionCatalog.DEFAULT_CATALOG_URL,
                            "priority": 1,
                            "install_allowed": True,
                        }
                    ]
                },
                f,
            )

        catalog = ExtensionCatalog(project_dir)

        # Create mock catalog
        catalog_data = {
            "schema_version": "1.0",
            "extensions": {
                "jira": {
                    "name": "Jira",
                    "id": "jira",
                    "version": "1.0.0",
                    "description": "Jira",
                    "tags": ["issue-tracking", "jira"],
                },
                "linear": {
                    "name": "Linear",
                    "id": "linear",
                    "version": "1.0.0",
                    "description": "Linear",
                    "tags": ["issue-tracking", "linear"],
                },
                "github": {
                    "name": "GitHub",
                    "id": "github",
                    "version": "1.0.0",
                    "description": "GitHub",
                    "tags": ["vcs", "github"],
                },
            },
        }

        catalog.cache_dir.mkdir(parents=True, exist_ok=True)
        catalog.cache_file.write_text(json.dumps(catalog_data))
        catalog.cache_metadata_file.write_text(
            json.dumps(
                {
                    "cached_at": datetime.now(timezone.utc).isoformat(),
                    "catalog_url": "http://test.com",
                }
            )
        )

        # Search by tag "issue-tracking"
        results = catalog.search(tag="issue-tracking")
        assert len(results) == 2
        assert {r["id"] for r in results} == {"jira", "linear"}

    def test_search_verified_only(self, temp_dir):
        """Test searching verified extensions only."""
        import yaml as yaml_module

        project_dir = temp_dir / "project"
        project_dir.mkdir()
        (project_dir / ".specify").mkdir()

        # Use a single-catalog config so community extensions don't interfere
        config_path = project_dir / ".specify" / "extension-catalogs.yml"
        with open(config_path, "w") as f:
            yaml_module.dump(
                {
                    "catalogs": [
                        {
                            "name": "test-catalog",
                            "url": ExtensionCatalog.DEFAULT_CATALOG_URL,
                            "priority": 1,
                            "install_allowed": True,
                        }
                    ]
                },
                f,
            )

        catalog = ExtensionCatalog(project_dir)

        # Create mock catalog
        catalog_data = {
            "schema_version": "1.0",
            "extensions": {
                "jira": {
                    "name": "Jira",
                    "id": "jira",
                    "version": "1.0.0",
                    "description": "Jira",
                    "verified": True,
                },
                "linear": {
                    "name": "Linear",
                    "id": "linear",
                    "version": "1.0.0",
                    "description": "Linear",
                    "verified": False,
                },
            },
        }

        catalog.cache_dir.mkdir(parents=True, exist_ok=True)
        catalog.cache_file.write_text(json.dumps(catalog_data))
        catalog.cache_metadata_file.write_text(
            json.dumps(
                {
                    "cached_at": datetime.now(timezone.utc).isoformat(),
                    "catalog_url": "http://test.com",
                }
            )
        )

        # Search verified only
        results = catalog.search(verified_only=True)
        assert len(results) == 1
        assert results[0]["id"] == "jira"

    def test_get_extension_info(self, temp_dir):
        """Test getting specific extension info."""
        import yaml as yaml_module

        project_dir = temp_dir / "project"
        project_dir.mkdir()
        (project_dir / ".specify").mkdir()

        # Use a single-catalog config so community extensions don't interfere
        config_path = project_dir / ".specify" / "extension-catalogs.yml"
        with open(config_path, "w") as f:
            yaml_module.dump(
                {
                    "catalogs": [
                        {
                            "name": "test-catalog",
                            "url": ExtensionCatalog.DEFAULT_CATALOG_URL,
                            "priority": 1,
                            "install_allowed": True,
                        }
                    ]
                },
                f,
            )

        catalog = ExtensionCatalog(project_dir)

        # Create mock catalog
        catalog_data = {
            "schema_version": "1.0",
            "extensions": {
                "jira": {
                    "name": "Jira Integration",
                    "id": "jira",
                    "version": "1.0.0",
                    "description": "Jira integration",
                    "author": "Stats Perform",
                },
            },
        }

        catalog.cache_dir.mkdir(parents=True, exist_ok=True)
        catalog.cache_file.write_text(json.dumps(catalog_data))
        catalog.cache_metadata_file.write_text(
            json.dumps(
                {
                    "cached_at": datetime.now(timezone.utc).isoformat(),
                    "catalog_url": "http://test.com",
                }
            )
        )

        # Get extension info
        info = catalog.get_extension_info("jira")
        assert info is not None
        assert info["id"] == "jira"
        assert info["name"] == "Jira Integration"

        # Non-existent extension
        info = catalog.get_extension_info("nonexistent")
        assert info is None

    def test_clear_cache(self, temp_dir):
        """Test clearing catalog cache."""
        project_dir = temp_dir / "project"
        project_dir.mkdir()
        (project_dir / ".specify").mkdir()

        catalog = ExtensionCatalog(project_dir)

        # Create cache
        catalog.cache_dir.mkdir(parents=True, exist_ok=True)
        catalog.cache_file.write_text("{}")
        catalog.cache_metadata_file.write_text("{}")

        assert catalog.cache_file.exists()
        assert catalog.cache_metadata_file.exists()

        # Clear cache
        catalog.clear_cache()

        assert not catalog.cache_file.exists()
        assert not catalog.cache_metadata_file.exists()

    # --- _make_request / GitHub auth ---

    def _make_catalog(self, temp_dir):
        project_dir = temp_dir / "project"
        project_dir.mkdir()
        (project_dir / ".specify").mkdir()
        return ExtensionCatalog(project_dir)

    def _inject_github_config(self, monkeypatch, token_env="GH_TOKEN"):
        from tests.auth_helpers import inject_github_config
        inject_github_config(monkeypatch, token_env)

    def test_make_request_no_token_no_auth_header(self, temp_dir, monkeypatch):
        """Without a token, requests carry no Authorization header."""
        monkeypatch.delenv("GITHUB_TOKEN", raising=False)
        monkeypatch.delenv("GH_TOKEN", raising=False)
        catalog = self._make_catalog(temp_dir)
        req = catalog._make_request("https://raw.githubusercontent.com/org/repo/main/catalog.json")
        assert "Authorization" not in req.headers

    def test_make_request_whitespace_only_github_token_ignored(self, temp_dir, monkeypatch):
        """A whitespace-only GITHUB_TOKEN is treated as unset."""
        monkeypatch.setenv("GITHUB_TOKEN", "   ")
        monkeypatch.delenv("GH_TOKEN", raising=False)
        catalog = self._make_catalog(temp_dir)
        req = catalog._make_request("https://raw.githubusercontent.com/org/repo/main/catalog.json")
        assert "Authorization" not in req.headers

    def test_make_request_whitespace_github_token_falls_back_to_gh_token(self, temp_dir, monkeypatch):
        """When GITHUB_TOKEN is whitespace-only, GH_TOKEN is used as fallback."""
        monkeypatch.setenv("GITHUB_TOKEN", "   ")
        monkeypatch.setenv("GH_TOKEN", "ghp_fallback")
        self._inject_github_config(monkeypatch, token_env="GH_TOKEN")
        catalog = self._make_catalog(temp_dir)
        req = catalog._make_request("https://raw.githubusercontent.com/org/repo/main/catalog.json")
        assert req.get_header("Authorization") == "Bearer ghp_fallback"

    def test_make_request_github_token_added_for_raw_githubusercontent(self, temp_dir, monkeypatch):
        """GITHUB_TOKEN is attached for raw.githubusercontent.com URLs."""
        monkeypatch.setenv("GITHUB_TOKEN", "ghp_testtoken")
        monkeypatch.delenv("GH_TOKEN", raising=False)
        self._inject_github_config(monkeypatch, token_env="GITHUB_TOKEN")
        catalog = self._make_catalog(temp_dir)
        req = catalog._make_request("https://raw.githubusercontent.com/org/repo/main/catalog.json")
        assert req.get_header("Authorization") == "Bearer ghp_testtoken"

    def test_make_request_gh_token_fallback(self, temp_dir, monkeypatch):
        """GH_TOKEN is used when GITHUB_TOKEN is absent."""
        monkeypatch.delenv("GITHUB_TOKEN", raising=False)
        monkeypatch.setenv("GH_TOKEN", "ghp_ghtoken")
        self._inject_github_config(monkeypatch, token_env="GH_TOKEN")
        catalog = self._make_catalog(temp_dir)
        req = catalog._make_request("https://github.com/org/repo/releases/download/v1/ext.zip")
        assert req.get_header("Authorization") == "Bearer ghp_ghtoken"

    def test_make_request_gh_token_takes_precedence_over_github_token(self, temp_dir, monkeypatch):
        """When auth.json uses GH_TOKEN, that token is used regardless of GITHUB_TOKEN."""
        monkeypatch.setenv("GITHUB_TOKEN", "ghp_secondary")
        monkeypatch.setenv("GH_TOKEN", "ghp_primary")
        self._inject_github_config(monkeypatch, token_env="GH_TOKEN")
        catalog = self._make_catalog(temp_dir)
        req = catalog._make_request("https://api.github.com/repos/org/repo")
        assert req.get_header("Authorization") == "Bearer ghp_primary"

    def test_make_request_no_auth_for_non_matching_host(self, temp_dir, monkeypatch):
        """Auth is NOT attached to hosts not listed in auth.json."""
        monkeypatch.setenv("GITHUB_TOKEN", "ghp_testtoken")
        self._inject_github_config(monkeypatch, token_env="GITHUB_TOKEN")
        catalog = self._make_catalog(temp_dir)
        req = catalog._make_request("https://internal.example.com/catalog.json")
        assert "Authorization" not in req.headers

    def test_make_request_no_auth_when_no_config(self, temp_dir, monkeypatch):
        """No auth header when no auth.json config exists."""
        monkeypatch.delenv("GITHUB_TOKEN", raising=False)
        monkeypatch.delenv("GH_TOKEN", raising=False)
        catalog = self._make_catalog(temp_dir)
        req = catalog._make_request("https://github.com/org/repo/releases/download/v1/ext.zip")
        assert "Authorization" not in req.headers

    def test_make_request_token_added_for_api_github_com(self, temp_dir, monkeypatch):
        """GITHUB_TOKEN is attached for api.github.com URLs."""
        monkeypatch.setenv("GITHUB_TOKEN", "ghp_testtoken")
        self._inject_github_config(monkeypatch, token_env="GITHUB_TOKEN")
        catalog = self._make_catalog(temp_dir)
        req = catalog._make_request("https://api.github.com/repos/org/repo/releases/assets/1")
        assert req.get_header("Authorization") == "Bearer ghp_testtoken"

    def test_make_request_token_added_for_codeload_github_com(self, temp_dir, monkeypatch):
        """GITHUB_TOKEN is attached for codeload.github.com URLs (GitHub archive redirects)."""
        monkeypatch.setenv("GITHUB_TOKEN", "ghp_testtoken")
        self._inject_github_config(monkeypatch, token_env="GITHUB_TOKEN")
        catalog = self._make_catalog(temp_dir)
        req = catalog._make_request("https://codeload.github.com/org/repo/zip/refs/tags/v1.0.0")
        assert req.get_header("Authorization") == "Bearer ghp_testtoken"

    def test_fetch_single_catalog_sends_auth_header(self, temp_dir, monkeypatch):
        """_fetch_single_catalog passes Authorization header when a provider is configured."""
        from unittest.mock import patch, MagicMock

        monkeypatch.setenv("GITHUB_TOKEN", "ghp_testtoken")
        self._inject_github_config(monkeypatch, token_env="GITHUB_TOKEN")
        catalog = self._make_catalog(temp_dir)

        catalog_data = {"schema_version": "1.0", "extensions": {}}
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(catalog_data).encode()
        mock_response.__enter__ = lambda s: s
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_response.geturl.return_value = "https://raw.githubusercontent.com/org/repo/main/catalog.json"

        captured = {}
        mock_opener = MagicMock()

        def fake_open(req, timeout=None):
            captured["req"] = req
            return mock_response

        mock_opener.open.side_effect = fake_open

        entry = CatalogEntry(
            url="https://raw.githubusercontent.com/org/repo/main/catalog.json",
            name="private",
            priority=1,
            install_allowed=True,
        )

        with patch("specify_cli.authentication.http.urllib.request.build_opener", return_value=mock_opener):
            catalog._fetch_single_catalog(entry, force_refresh=True)

        assert captured["req"].get_header("Authorization") == "Bearer ghp_testtoken"

    @pytest.mark.parametrize(
        "payload",
        [
            # Root is not a JSON object.
            [],
            "oops",
            42,
            None,
            # Root is fine but ``extensions`` is the wrong type.
            {"schema_version": "1.0", "extensions": []},
            {"schema_version": "1.0", "extensions": "oops"},
            {"schema_version": "1.0", "extensions": None},
            {"schema_version": "1.0", "extensions": 42},
        ],
    )
    def test_fetch_single_catalog_rejects_malformed_payload(self, temp_dir, payload):
        """Malformed catalog payloads raise ExtensionError, not AttributeError.

        Without this guard, a payload like ``{"extensions": []}`` would pass the
        key-presence check and then crash with ``AttributeError: 'list' object
        has no attribute 'items'`` deep inside ``_get_merged_extensions``. The
        sibling integration catalog reader already validates both the root
        object and the nested mapping (see ``integrations/catalog.py``); the
        extension catalog must stay consistent.
        """
        from unittest.mock import patch, MagicMock

        catalog = self._make_catalog(temp_dir)

        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(payload).encode()
        mock_response.__enter__ = lambda s: s
        mock_response.__exit__ = MagicMock(return_value=False)

        entry = CatalogEntry(
            url="https://example.com/catalog.json",
            name="default",
            priority=1,
            install_allowed=True,
        )

        with patch.object(catalog, "_open_url", return_value=mock_response):
            with pytest.raises(ExtensionError, match="Invalid catalog format"):
                catalog._fetch_single_catalog(entry, force_refresh=True)

    @pytest.mark.parametrize(
        "cached_payload",
        [
            [],
            "oops",
            42,
            None,
            {"schema_version": "1.0", "extensions": []},
            {"schema_version": "1.0", "extensions": "oops"},
            {"schema_version": "1.0", "extensions": None},
        ],
    )
    def test_fetch_single_catalog_rejects_malformed_cached_payload(
        self, temp_dir, cached_payload
    ):
        """A poisoned cache silently falls back to the network instead of
        crashing — cached payloads pass through the same shape validation
        as freshly-fetched ones.

        Without this, a cache poisoned by an older spec-kit version (or a
        manual edit, or an upstream that briefly served a bad payload
        before the network guards landed) would re-crash every invocation
        of ``_get_merged_extensions`` despite the cache being "valid" by
        age. The recovery contract is: if the cached payload fails
        validation, drop it and refetch — never propagate
        ``AttributeError`` to the caller.
        """
        from unittest.mock import patch, MagicMock

        catalog = self._make_catalog(temp_dir)

        # Poison the default-URL cache. ``DEFAULT_CATALOG_URL`` is the
        # branch that goes through ``is_cache_valid()`` (the non-default
        # branch uses per-URL hashed cache files but the same code path
        # below).
        catalog.cache_dir.mkdir(parents=True, exist_ok=True)
        catalog.cache_file.write_text(json.dumps(cached_payload))
        catalog.cache_metadata_file.write_text(
            json.dumps(
                {
                    "cached_at": datetime.now(timezone.utc).isoformat(),
                    "catalog_url": ExtensionCatalog.DEFAULT_CATALOG_URL,
                }
            )
        )

        # Network refetch returns a valid payload so the recovery path
        # can complete.
        valid = {
            "schema_version": "1.0",
            "extensions": {"foo": {"name": "Foo", "version": "1.0.0"}},
        }
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(valid).encode()
        mock_response.__enter__ = lambda s: s
        mock_response.__exit__ = MagicMock(return_value=False)

        entry = CatalogEntry(
            url=ExtensionCatalog.DEFAULT_CATALOG_URL,
            name="default",
            priority=1,
            install_allowed=True,
        )

        with patch.object(catalog, "_open_url", return_value=mock_response):
            result = catalog._fetch_single_catalog(entry, force_refresh=False)

        # The poisoned cache was discarded and the network payload returned.
        assert result == valid

    @pytest.mark.parametrize(
        "payload",
        [
            # Root is not a JSON object.
            [],
            "oops",
            42,
            None,
            # Root is fine but ``extensions`` is the wrong type.
            {"schema_version": "1.0", "extensions": []},
            {"schema_version": "1.0", "extensions": "oops"},
            {"schema_version": "1.0", "extensions": None},
        ],
    )
    def test_fetch_catalog_rejects_malformed_payload(self, temp_dir, payload):
        """Legacy ``fetch_catalog`` reuses the same shape-validation helper.

        Before this change ``fetch_catalog`` only checked key presence — so
        a payload like ``42`` would crash with
        ``TypeError: argument of type 'int' is not iterable`` during the
        ``"schema_version" in catalog_data`` check, and an entry mapping
        of the wrong type would crash downstream. Reusing
        ``_validate_catalog_payload`` keeps the network-side behaviour of
        the legacy single-catalog method consistent with the multi-catalog
        ``_fetch_single_catalog`` path.
        """
        from unittest.mock import patch, MagicMock

        catalog = self._make_catalog(temp_dir)
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(payload).encode()
        mock_response.__enter__ = lambda s: s
        mock_response.__exit__ = MagicMock(return_value=False)

        with patch.object(catalog, "_open_url", return_value=mock_response):
            with pytest.raises(ExtensionError, match="Invalid catalog format"):
                catalog.fetch_catalog(force_refresh=True)

    def test_fetch_catalog_recovers_from_unreadable_cache(self, temp_dir):
        """An unreadable / wrong-encoded cache file silently refetches.

        The cache contract is best-effort: a JSON-decode failure, an OS
        read failure (permissions / disk / handle limit), or an invalid
        text encoding on a cache file written by an older client must
        all fall through to the network fetch rather than crash the
        caller. Covers Copilot's review point that the previous
        ``except (json.JSONDecodeError,)`` was too narrow.
        """
        from unittest.mock import patch, MagicMock

        catalog = self._make_catalog(temp_dir)
        # Write invalid UTF-8 bytes to the cache file so ``read_text``
        # raises ``UnicodeDecodeError`` (a subclass of ``UnicodeError``).
        catalog.cache_dir.mkdir(parents=True, exist_ok=True)
        catalog.cache_file.write_bytes(b"\xff\xfe\x00not-utf-8")
        catalog.cache_metadata_file.write_text(
            json.dumps(
                {
                    "cached_at": datetime.now(timezone.utc).isoformat(),
                    "catalog_url": ExtensionCatalog.DEFAULT_CATALOG_URL,
                }
            ),
            encoding="utf-8",
        )

        valid = {
            "schema_version": "1.0",
            "extensions": {"foo": {"name": "Foo", "version": "1.0.0"}},
        }
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(valid).encode()
        mock_response.__enter__ = lambda s: s
        mock_response.__exit__ = MagicMock(return_value=False)

        with patch.object(catalog, "_open_url", return_value=mock_response):
            result = catalog.fetch_catalog(force_refresh=False)

        # Recovered via network rather than crashing on the unreadable cache.
        assert result == valid

    def test_fetch_catalog_recovers_from_unreadable_metadata(self, temp_dir):
        """A wrongly-encoded metadata file degrades to a cache miss.

        ``is_cache_valid`` is consulted *before* the cache payload is
        read; if the metadata file itself can't be decoded (e.g. it was
        written on a Windows host whose default codec isn't UTF-8) the
        validity check must return ``False`` rather than propagate
        ``UnicodeDecodeError``. Without that guard, a corrupted metadata
        file would crash every invocation instead of falling through to
        a network refetch.
        """
        from unittest.mock import patch, MagicMock

        catalog = self._make_catalog(temp_dir)
        catalog.cache_dir.mkdir(parents=True, exist_ok=True)
        catalog.cache_file.write_text("{}", encoding="utf-8")
        # Bytes that are not valid UTF-8 — ``read_text(encoding="utf-8")``
        # will raise ``UnicodeDecodeError`` (subclass of ``UnicodeError``).
        catalog.cache_metadata_file.write_bytes(b"\xff\xfe\x00bad")

        # is_cache_valid must absorb the decode failure, not crash.
        assert catalog.is_cache_valid() is False

        valid = {
            "schema_version": "1.0",
            "extensions": {"foo": {"name": "Foo", "version": "1.0.0"}},
        }
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(valid).encode()
        mock_response.__enter__ = lambda s: s
        mock_response.__exit__ = MagicMock(return_value=False)

        with patch.object(catalog, "_open_url", return_value=mock_response):
            result = catalog.fetch_catalog(force_refresh=False)

        assert result == valid

    @pytest.mark.parametrize(
        "non_mapping_metadata",
        [
            "[]",       # JSON array
            '"oops"',   # JSON string
            "42",       # JSON number
            "true",     # JSON bool
            "null",     # JSON null
        ],
    )
    def test_is_cache_valid_handles_non_mapping_metadata(
        self, temp_dir, non_mapping_metadata
    ):
        """Metadata that parses to a non-mapping degrades to cache-invalid.

        The cache-validity check calls ``metadata.get("cached_at", "")``
        immediately after ``json.loads``. If the metadata file is valid
        JSON but parses to a non-mapping (``[]``, ``"oops"``, ``42``,
        ``true``, ``null``), ``.get`` raises ``AttributeError`` — which
        previously slipped past the except tuple and crashed the
        caller. The contract documented on ``is_cache_valid`` says any
        decode/shape failure should return ``False`` so ``fetch_catalog``
        falls through to a network refetch. This test pins that
        contract across every JSON non-mapping root type so a regression
        in the except clause can't silently re-introduce the crash.
        """
        catalog = self._make_catalog(temp_dir)
        catalog.cache_dir.mkdir(parents=True, exist_ok=True)
        catalog.cache_file.write_text("{}", encoding="utf-8")
        catalog.cache_metadata_file.write_text(
            non_mapping_metadata, encoding="utf-8"
        )

        # Must not raise — the contract is "any decode/shape failure → False".
        assert catalog.is_cache_valid() is False

    def test_fetch_catalog_writes_cache_as_utf8(self, temp_dir, monkeypatch):
        """Cache + metadata writes pass ``encoding="utf-8"``, observably.

        The earlier version of this test claimed to assert UTF-8 at the
        byte level but actually only round-tripped a non-ASCII string
        through ``json.dumps`` and ``read_text(encoding="utf-8")``.
        Because ``json.dumps`` defaults to ``ensure_ascii=True``, "café"
        was serialized as the all-ASCII escape ``caf\\u00e9`` before it
        ever reached ``write_text`` — the bytes on disk were identical
        regardless of the encoding kwarg, so a locale-encoded write
        would have round-tripped just fine. The drift Copilot's review
        flagged wasn't actually being caught.

        Fix: directly observe the ``encoding`` argument passed to every
        ``write_text`` call made against the cache directory. This is
        the production code's encoding choice, which is exactly what
        the regression guard cares about; non-ASCII payload tricks are
        unnecessary because the assertion is about the kwarg, not the
        bytes.
        """
        from unittest.mock import patch, MagicMock
        from pathlib import Path as _PathCls

        catalog = self._make_catalog(temp_dir)
        payload = {
            "schema_version": "1.0",
            "extensions": {"foo": {"name": "Foo", "version": "1.0.0"}},
        }
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(payload).encode("utf-8")
        mock_response.__enter__ = lambda s: s
        mock_response.__exit__ = MagicMock(return_value=False)

        # Record every ``write_text`` call's encoding kwarg so the
        # assertion observes the production writer's argument directly.
        recorded: list[dict] = []
        real_write_text = _PathCls.write_text

        def recording_write_text(self, data, *args, **kwargs):
            recorded.append(
                {"path": str(self), "encoding": kwargs.get("encoding")}
            )
            return real_write_text(self, data, *args, **kwargs)

        monkeypatch.setattr(_PathCls, "write_text", recording_write_text)

        with patch.object(catalog, "_open_url", return_value=mock_response):
            catalog.fetch_catalog(force_refresh=True)

        # Filter to writes inside the catalog's cache directory so
        # unrelated writes from other machinery don't pollute the
        # assertion.
        cache_writes = [
            r for r in recorded if str(catalog.cache_dir) in r["path"]
        ]
        assert cache_writes, "fetch_catalog made no writes to the cache dir"
        for record in cache_writes:
            assert record["encoding"] == "utf-8", (
                f"write_text on {record['path']} used encoding "
                f"{record['encoding']!r}; expected 'utf-8'"
            )

    def test_fetch_catalog_survives_unwritable_cache(self, temp_dir, monkeypatch):
        """An unwritable cache dir doesn't fail a successful fetch.

        Cache writes are best-effort, mirroring the read side and the
        ``integrations/catalog.py`` precedent: if ``mkdir``/``write_text``
        raises ``OSError`` (read-only checkout, permissions), the
        already-fetched-and-validated payload must still be returned
        rather than surfacing the cache failure to the caller.
        """
        from unittest.mock import patch, MagicMock
        from pathlib import Path as _PathCls

        catalog = self._make_catalog(temp_dir)
        valid = {
            "schema_version": "1.0",
            "extensions": {"foo": {"name": "Foo", "version": "1.0.0"}},
        }
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(valid).encode()
        mock_response.__enter__ = lambda s: s
        mock_response.__exit__ = MagicMock(return_value=False)

        # Simulate an unwritable cache dir: every write_text under the
        # cache directory raises PermissionError (an OSError subclass).
        real_write_text = _PathCls.write_text

        def failing_write_text(self, data, *args, **kwargs):
            if str(catalog.cache_dir) in str(self):
                raise PermissionError("cache dir is read-only")
            return real_write_text(self, data, *args, **kwargs)

        monkeypatch.setattr(_PathCls, "write_text", failing_write_text)

        with patch.object(catalog, "_open_url", return_value=mock_response):
            # Legacy single-catalog path.
            assert catalog.fetch_catalog(force_refresh=True) == valid

            # Multi-catalog path.
            entry = CatalogEntry(
                url="https://example.com/catalog.json",
                name="default",
                priority=1,
                install_allowed=True,
            )
            assert catalog._fetch_single_catalog(entry, force_refresh=True) == valid

    def test_get_merged_extensions_skips_non_mapping_entries(self, temp_dir):
        """Per-entry guard: one malformed entry shouldn't poison the merge.

        ``_fetch_single_catalog`` validates that ``extensions`` is a mapping,
        but it doesn't (and shouldn't) validate every entry inside it — a
        single bad entry in an otherwise-valid catalog should be skipped, not
        crash the whole resolve path. Mirrors the per-entry skip in
        ``integrations/catalog.py``: a malformed entry returns no error,
        valid entries continue to merge normally.
        """
        from unittest.mock import patch, MagicMock

        catalog = self._make_catalog(temp_dir)
        # Mix of valid entry, list-shaped entry, and string-shaped entry.
        payload = {
            "schema_version": "1.0",
            "extensions": {
                "good": {"name": "Good", "version": "1.0.0"},
                "bad-list": [],
                "bad-str": "oops",
            },
        }
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(payload).encode()
        mock_response.__enter__ = lambda s: s
        mock_response.__exit__ = MagicMock(return_value=False)

        entry = CatalogEntry(
            url="https://example.com/catalog.json",
            name="default",
            priority=1,
            install_allowed=True,
        )

        with patch.object(catalog, "_open_url", return_value=mock_response), \
             patch.object(catalog, "get_active_catalogs", return_value=[entry]):
            merged = catalog._get_merged_extensions(force_refresh=True)

        # Only the well-formed entry survives; the two malformed entries are
        # silently dropped rather than raising or crashing.
        assert [ext["id"] for ext in merged] == ["good"]

    def test_download_extension_sends_auth_header(self, temp_dir, monkeypatch):
        """download_extension passes Authorization header when a provider is configured."""
        from unittest.mock import patch, MagicMock
        import zipfile
        import io

        monkeypatch.setenv("GITHUB_TOKEN", "ghp_testtoken")
        self._inject_github_config(monkeypatch, token_env="GITHUB_TOKEN")
        catalog = self._make_catalog(temp_dir)

        # Build a minimal valid ZIP in memory
        zip_buf = io.BytesIO()
        with zipfile.ZipFile(zip_buf, "w") as zf:
            zf.writestr("extension.yml", "id: test-ext\nname: Test\nversion: 1.0.0\n")
        zip_bytes = zip_buf.getvalue()

        release_response = MagicMock()
        release_response.read.return_value = json.dumps(
            {
                "assets": [
                    {
                        "name": "test-ext.zip",
                        "url": "https://api.github.com/repos/org/repo/releases/assets/1",
                    }
                ]
            }
        ).encode()
        release_response.__enter__ = lambda s: s
        release_response.__exit__ = MagicMock(return_value=False)

        asset_response = MagicMock()
        asset_response.read.return_value = zip_bytes
        asset_response.__enter__ = lambda s: s
        asset_response.__exit__ = MagicMock(return_value=False)

        captured = []
        mock_opener = MagicMock()

        def fake_open(req, timeout=None):
            captured.append(req)
            if req.full_url.endswith("/releases/tags/v1"):
                return release_response
            return asset_response

        mock_opener.open.side_effect = fake_open

        ext_info = {
            "id": "test-ext",
            "name": "Test Extension",
            "version": "1.0.0",
            "download_url": "https://github.com/org/repo/releases/download/v1/test-ext.zip",
        }

        with patch.object(catalog, "get_extension_info", return_value=ext_info), \
             patch("specify_cli.authentication.http.urllib.request.build_opener", return_value=mock_opener):
            catalog.download_extension("test-ext", target_dir=temp_dir)

        assert captured[0].full_url == "https://api.github.com/repos/org/repo/releases/tags/v1"
        assert captured[0].get_header("Authorization") == "Bearer ghp_testtoken"
        assert captured[1].full_url == "https://api.github.com/repos/org/repo/releases/assets/1"
        assert captured[1].get_header("Authorization") == "Bearer ghp_testtoken"
        assert captured[1].get_header("Accept") == "application/octet-stream"

    def _make_zip_bytes(self):
        """Build a minimal valid extension ZIP in memory for download tests."""
        import zipfile
        import io

        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            zf.writestr("extension.yml", "id: test-ext\nname: Test\nversion: 1.0.0\n")
        return buf.getvalue()

    def _mock_response(self, data):
        """Build a context-manager mock HTTP response returning ``data``."""
        from unittest.mock import MagicMock

        resp = MagicMock()
        resp.read.return_value = data
        # Configure the context-manager protocol explicitly so `with resp`
        # yields `resp` itself, independent of how the protocol is invoked.
        resp.__enter__.return_value = resp
        resp.__exit__.return_value = False
        return resp

    def test_download_extension_accepts_matching_sha256(self, temp_dir):
        """A catalog ``sha256`` that matches the archive is accepted."""
        import hashlib
        from unittest.mock import patch

        catalog = self._make_catalog(temp_dir)
        zip_bytes = self._make_zip_bytes()
        ext_info = {
            "id": "test-ext",
            "name": "Test Extension",
            "version": "1.0.0",
            "download_url": "https://example.com/test-ext.zip",
            "sha256": hashlib.sha256(zip_bytes).hexdigest(),
        }

        with patch.object(catalog, "get_extension_info", return_value=ext_info), \
             patch.object(catalog, "_open_url", return_value=self._mock_response(zip_bytes)):
            zip_path = catalog.download_extension("test-ext", target_dir=temp_dir)

        assert zip_path.read_bytes() == zip_bytes

    def test_download_extension_rejects_sha256_mismatch(self, temp_dir):
        """A catalog ``sha256`` that does not match the downloaded archive
        aborts the install — a tampered or swapped archive is rejected.
        """
        from unittest.mock import patch

        catalog = self._make_catalog(temp_dir)
        zip_bytes = self._make_zip_bytes()
        ext_info = {
            "id": "test-ext",
            "name": "Test Extension",
            "version": "1.0.0",
            "download_url": "https://example.com/test-ext.zip",
            "sha256": "0" * 64,  # deliberately wrong
        }

        with patch.object(catalog, "get_extension_info", return_value=ext_info), \
             patch.object(catalog, "_open_url", return_value=self._mock_response(zip_bytes)):
            with pytest.raises(ExtensionError, match="[Ii]ntegrity"):
                catalog.download_extension("test-ext", target_dir=temp_dir)

    def test_download_extension_without_sha256_still_succeeds(self, temp_dir):
        """Entries without ``sha256`` keep working (backwards compatible)."""
        from unittest.mock import patch

        catalog = self._make_catalog(temp_dir)
        zip_bytes = self._make_zip_bytes()
        ext_info = {
            "id": "test-ext",
            "name": "Test Extension",
            "version": "1.0.0",
            "download_url": "https://example.com/test-ext.zip",
        }

        with patch.object(catalog, "get_extension_info", return_value=ext_info), \
             patch.object(catalog, "_open_url", return_value=self._mock_response(zip_bytes)):
            zip_path = catalog.download_extension("test-ext", target_dir=temp_dir)

        assert zip_path.read_bytes() == zip_bytes

    def test_download_extension_accepts_direct_github_rest_asset_url(self, temp_dir, monkeypatch):
        """download_extension can use a GitHub REST release asset URL directly."""
        from unittest.mock import patch, MagicMock
        import zipfile
        import io

        monkeypatch.setenv("GITHUB_TOKEN", "ghp_testtoken")
        self._inject_github_config(monkeypatch, token_env="GITHUB_TOKEN")
        catalog = self._make_catalog(temp_dir)

        zip_buf = io.BytesIO()
        with zipfile.ZipFile(zip_buf, "w") as zf:
            zf.writestr("extension.yml", "id: test-ext\nname: Test\nversion: 1.0.0\n")
        zip_bytes = zip_buf.getvalue()

        asset_response = MagicMock()
        asset_response.read.return_value = zip_bytes
        asset_response.__enter__ = lambda s: s
        asset_response.__exit__ = MagicMock(return_value=False)

        captured = []
        mock_opener = MagicMock()

        def fake_open(req, timeout=None):
            captured.append(req)
            return asset_response

        mock_opener.open.side_effect = fake_open

        ext_info = {
            "id": "test-ext",
            "name": "Test Extension",
            "version": "1.0.0",
            "download_url": "https://api.github.com/repos/org/repo/releases/assets/1",
        }

        with patch.object(catalog, "get_extension_info", return_value=ext_info), \
             patch("specify_cli.authentication.http.urllib.request.build_opener", return_value=mock_opener):
            catalog.download_extension("test-ext", target_dir=temp_dir)

        assert len(captured) == 1
        assert captured[0].full_url == "https://api.github.com/repos/org/repo/releases/assets/1"
        assert captured[0].get_header("Authorization") == "Bearer ghp_testtoken"
        assert captured[0].get_header("Accept") == "application/octet-stream"



# ===== CatalogEntry Tests =====

class TestCatalogEntry:
    """Test CatalogEntry dataclass."""

    def test_catalog_entry_creation(self):
        """Test creating a CatalogEntry."""
        entry = CatalogEntry(
            url="https://example.com/catalog.json",
            name="test",
            priority=1,
            install_allowed=True,
        )
        assert entry.url == "https://example.com/catalog.json"
        assert entry.name == "test"
        assert entry.priority == 1
        assert entry.install_allowed is True


# ===== Catalog Stack Tests =====

class TestCatalogStack:
    """Test multi-catalog stack support."""

    def _make_project(self, temp_dir: Path) -> Path:
        """Create a minimal spec-kit project directory."""
        project_dir = temp_dir / "project"
        project_dir.mkdir()
        (project_dir / ".specify").mkdir()
        return project_dir

    def _write_catalog_config(self, project_dir: Path, catalogs: list) -> None:
        """Write extension-catalogs.yml to project .specify dir."""
        import yaml as yaml_module

        config_path = project_dir / ".specify" / "extension-catalogs.yml"
        with open(config_path, "w") as f:
            yaml_module.dump({"catalogs": catalogs}, f)

    def _write_valid_cache(
        self, catalog: ExtensionCatalog, extensions: dict, url: str = "http://test.com"
    ) -> None:
        """Populate the primary cache file with mock extension data."""
        catalog_data = {"schema_version": "1.0", "extensions": extensions}
        catalog.cache_dir.mkdir(parents=True, exist_ok=True)
        catalog.cache_file.write_text(json.dumps(catalog_data))
        catalog.cache_metadata_file.write_text(
            json.dumps(
                {
                    "cached_at": datetime.now(timezone.utc).isoformat(),
                    "catalog_url": url,
                }
            )
        )

    # --- get_active_catalogs ---

    def test_default_stack(self, temp_dir):
        """Default stack includes default and community catalogs."""
        project_dir = self._make_project(temp_dir)
        catalog = ExtensionCatalog(project_dir)

        entries = catalog.get_active_catalogs()

        assert len(entries) == 2
        assert entries[0].url == ExtensionCatalog.DEFAULT_CATALOG_URL
        assert entries[0].name == "default"
        assert entries[0].priority == 1
        assert entries[0].install_allowed is True
        assert entries[1].url == ExtensionCatalog.COMMUNITY_CATALOG_URL
        assert entries[1].name == "community"
        assert entries[1].priority == 2
        assert entries[1].install_allowed is False

    def test_env_var_overrides_default_stack(self, temp_dir, monkeypatch):
        """SPECKIT_CATALOG_URL replaces the entire default stack."""
        project_dir = self._make_project(temp_dir)
        custom_url = "https://example.com/catalog.json"
        monkeypatch.setenv("SPECKIT_CATALOG_URL", custom_url)

        catalog = ExtensionCatalog(project_dir)
        entries = catalog.get_active_catalogs()

        assert len(entries) == 1
        assert entries[0].url == custom_url
        assert entries[0].install_allowed is True

    def test_env_var_invalid_url_raises(self, temp_dir, monkeypatch):
        """SPECKIT_CATALOG_URL with http:// (non-localhost) raises ValidationError."""
        project_dir = self._make_project(temp_dir)
        monkeypatch.setenv("SPECKIT_CATALOG_URL", "http://example.com/catalog.json")

        catalog = ExtensionCatalog(project_dir)
        with pytest.raises(ValidationError, match="HTTPS"):
            catalog.get_active_catalogs()

    def test_project_config_overrides_defaults(self, temp_dir):
        """Project-level extension-catalogs.yml overrides default stack."""
        project_dir = self._make_project(temp_dir)
        self._write_catalog_config(
            project_dir,
            [
                {
                    "name": "custom",
                    "url": "https://example.com/catalog.json",
                    "priority": 1,
                    "install_allowed": True,
                }
            ],
        )

        catalog = ExtensionCatalog(project_dir)
        entries = catalog.get_active_catalogs()

        assert len(entries) == 1
        assert entries[0].url == "https://example.com/catalog.json"
        assert entries[0].name == "custom"

    def test_project_config_sorted_by_priority(self, temp_dir):
        """Catalog entries are sorted by priority (ascending)."""
        project_dir = self._make_project(temp_dir)
        self._write_catalog_config(
            project_dir,
            [
                {
                    "name": "secondary",
                    "url": "https://example.com/secondary.json",
                    "priority": 5,
                    "install_allowed": False,
                },
                {
                    "name": "primary",
                    "url": "https://example.com/primary.json",
                    "priority": 1,
                    "install_allowed": True,
                },
            ],
        )

        catalog = ExtensionCatalog(project_dir)
        entries = catalog.get_active_catalogs()

        assert len(entries) == 2
        assert entries[0].name == "primary"
        assert entries[1].name == "secondary"

    def test_project_config_invalid_url_raises(self, temp_dir):
        """Project config with HTTP (non-localhost) URL raises ValidationError."""
        project_dir = self._make_project(temp_dir)
        self._write_catalog_config(
            project_dir,
            [
                {
                    "name": "bad",
                    "url": "http://example.com/catalog.json",
                    "priority": 1,
                    "install_allowed": True,
                }
            ],
        )

        catalog = ExtensionCatalog(project_dir)
        with pytest.raises(ValidationError, match="HTTPS"):
            catalog.get_active_catalogs()

    def test_empty_project_config_raises_error(self, temp_dir):
        """Empty catalogs list in config raises ValidationError (fail-closed for security)."""
        import yaml as yaml_module

        project_dir = self._make_project(temp_dir)
        config_path = project_dir / ".specify" / "extension-catalogs.yml"
        with open(config_path, "w") as f:
            yaml_module.dump({"catalogs": []}, f)

        catalog = ExtensionCatalog(project_dir)

        # Fail-closed: empty config should raise, not fall back to defaults
        with pytest.raises(ValidationError) as exc_info:
            catalog.get_active_catalogs()
        assert "contains no 'catalogs' entries" in str(exc_info.value)

    def test_catalog_entries_without_urls_raises_error(self, temp_dir):
        """Catalog entries without URLs raise ValidationError (fail-closed for security)."""
        import yaml as yaml_module

        project_dir = self._make_project(temp_dir)
        config_path = project_dir / ".specify" / "extension-catalogs.yml"
        with open(config_path, "w") as f:
            yaml_module.dump({
                "catalogs": [
                    {"name": "no-url-catalog", "priority": 1},
                    {"name": "another-no-url", "description": "Also missing URL"},
                ]
            }, f)

        catalog = ExtensionCatalog(project_dir)

        # Fail-closed: entries without URLs should raise, not fall back to defaults
        with pytest.raises(ValidationError) as exc_info:
            catalog.get_active_catalogs()
        assert "none have valid URLs" in str(exc_info.value)

    # --- _load_catalog_config ---

    def test_load_catalog_config_missing_file(self, temp_dir):
        """Returns None when config file doesn't exist."""
        project_dir = self._make_project(temp_dir)
        catalog = ExtensionCatalog(project_dir)

        result = catalog._load_catalog_config(project_dir / ".specify" / "nonexistent.yml")
        assert result is None

    def test_load_catalog_config_localhost_allowed(self, temp_dir):
        """Localhost HTTP URLs are allowed in config."""
        project_dir = self._make_project(temp_dir)
        self._write_catalog_config(
            project_dir,
            [
                {
                    "name": "local",
                    "url": "http://localhost:8000/catalog.json",
                    "priority": 1,
                    "install_allowed": True,
                }
            ],
        )

        catalog = ExtensionCatalog(project_dir)
        entries = catalog.get_active_catalogs()

        assert len(entries) == 1
        assert entries[0].url == "http://localhost:8000/catalog.json"

    @pytest.mark.parametrize(
        "config_content", ["[]\n", "false\n", "0\n", "''\n", "- item\n"]
    )
    def test_load_catalog_config_rejects_non_mapping_roots(
        self, temp_dir, config_content
    ):
        """Malformed roots raise ValidationError, not fallback or AttributeError."""
        project_dir = self._make_project(temp_dir)
        config_path = project_dir / ".specify" / "extension-catalogs.yml"
        config_path.write_text(config_content, encoding="utf-8")

        catalog = ExtensionCatalog(project_dir)

        with pytest.raises(
            ValidationError, match="expected a YAML mapping at the root"
        ) as exc_info:
            catalog.get_active_catalogs()
        assert str(config_path) in str(exc_info.value)

    def test_load_catalog_config_rejects_boolean_priority(self, temp_dir):
        """Boolean priorities are rejected instead of being coerced to 1 or 0."""
        import yaml as yaml_module

        project_dir = self._make_project(temp_dir)
        config_path = project_dir / ".specify" / "extension-catalogs.yml"
        config_path.write_text(
            yaml_module.dump(
                {
                    "catalogs": [
                        {
                            "name": "bad-priority",
                            "url": "https://example.com/catalog.json",
                            "priority": True,
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )

        catalog = ExtensionCatalog(project_dir)

        with pytest.raises(
            ValidationError, match="Invalid priority|expected integer"
        ) as exc_info:
            catalog.get_active_catalogs()
        assert str(config_path) in str(exc_info.value)

    def test_load_catalog_config_defaults_blank_names(self, temp_dir):
        """Blank and null names normalize by valid catalog order."""
        import yaml as yaml_module

        project_dir = self._make_project(temp_dir)
        config_path = project_dir / ".specify" / "extension-catalogs.yml"
        config_path.write_text(
            yaml_module.dump(
                {
                    "catalogs": [
                        {"name": "skipped", "url": "   "},
                        {"name": None, "url": "https://one.example.com/catalog.json"},
                        {"name": "   ", "url": "https://two.example.com/catalog.json"},
                    ]
                }
            ),
            encoding="utf-8",
        )

        catalog = ExtensionCatalog(project_dir)

        assert [entry.name for entry in catalog.get_active_catalogs()] == [
            "catalog-1",
            "catalog-2",
        ]

    @pytest.mark.parametrize(
        ("url", "expected_detail"),
        [
            ("relative/catalog.json", "HTTPS"),
            ("https:///no-host", "valid URL with a host"),
        ],
    )
    def test_load_catalog_config_invalid_url_includes_context(
        self, temp_dir, url, expected_detail
    ):
        """Invalid catalog URLs include the config path and entry index."""
        import yaml as yaml_module

        project_dir = self._make_project(temp_dir)
        config_path = project_dir / ".specify" / "extension-catalogs.yml"
        config_path.write_text(
            yaml_module.dump({"catalogs": [{"name": "bad", "url": url}]}),
            encoding="utf-8",
        )

        catalog = ExtensionCatalog(project_dir)

        with pytest.raises(ValidationError) as exc_info:
            catalog.get_active_catalogs()
        message = str(exc_info.value)
        assert "Invalid catalog URL" in message
        assert str(config_path) in message
        assert "index 0" in message
        assert expected_detail in message

    # --- Merge conflict resolution ---

    def test_merge_conflict_higher_priority_wins(self, temp_dir):
        """When same extension id is in two catalogs, higher priority wins."""
        project_dir = self._make_project(temp_dir)

        # Write project config with two catalogs
        self._write_catalog_config(
            project_dir,
            [
                {
                    "name": "primary",
                    "url": ExtensionCatalog.DEFAULT_CATALOG_URL,
                    "priority": 1,
                    "install_allowed": True,
                },
                {
                    "name": "secondary",
                    "url": ExtensionCatalog.COMMUNITY_CATALOG_URL,
                    "priority": 2,
                    "install_allowed": False,
                },
            ],
        )

        catalog = ExtensionCatalog(project_dir)

        # Write primary cache with jira v2.0.0
        primary_data = {
            "schema_version": "1.0",
            "extensions": {
                "jira": {
                    "name": "Jira Integration",
                    "id": "jira",
                    "version": "2.0.0",
                    "description": "Primary Jira",
                }
            },
        }
        catalog.cache_dir.mkdir(parents=True, exist_ok=True)
        catalog.cache_file.write_text(json.dumps(primary_data))
        catalog.cache_metadata_file.write_text(
            json.dumps({"cached_at": datetime.now(timezone.utc).isoformat(), "catalog_url": "http://test.com"})
        )

        # Write secondary cache (URL-hash-based) with jira v1.0.0 (should lose)
        import hashlib

        url_hash = hashlib.sha256(ExtensionCatalog.COMMUNITY_CATALOG_URL.encode()).hexdigest()[:16]
        secondary_cache = catalog.cache_dir / f"catalog-{url_hash}.json"
        secondary_meta = catalog.cache_dir / f"catalog-{url_hash}-metadata.json"
        secondary_data = {
            "schema_version": "1.0",
            "extensions": {
                "jira": {
                    "name": "Jira Integration Community",
                    "id": "jira",
                    "version": "1.0.0",
                    "description": "Community Jira",
                },
                "linear": {
                    "name": "Linear",
                    "id": "linear",
                    "version": "0.9.0",
                    "description": "Linear from secondary",
                },
            },
        }
        secondary_cache.write_text(json.dumps(secondary_data))
        secondary_meta.write_text(
            json.dumps({"cached_at": datetime.now(timezone.utc).isoformat(), "catalog_url": ExtensionCatalog.COMMUNITY_CATALOG_URL})
        )

        results = catalog.search()
        jira_results = [r for r in results if r["id"] == "jira"]
        assert len(jira_results) == 1
        # Primary catalog wins
        assert jira_results[0]["version"] == "2.0.0"
        assert jira_results[0]["_catalog_name"] == "primary"
        assert jira_results[0]["_install_allowed"] is True

        # linear comes from secondary
        linear_results = [r for r in results if r["id"] == "linear"]
        assert len(linear_results) == 1
        assert linear_results[0]["_catalog_name"] == "secondary"
        assert linear_results[0]["_install_allowed"] is False

    def test_install_allowed_false_from_get_extension_info(self, temp_dir):
        """get_extension_info includes _install_allowed from source catalog."""
        project_dir = self._make_project(temp_dir)

        # Single catalog that is install_allowed=False
        self._write_catalog_config(
            project_dir,
            [
                {
                    "name": "discovery",
                    "url": ExtensionCatalog.DEFAULT_CATALOG_URL,
                    "priority": 1,
                    "install_allowed": False,
                }
            ],
        )

        catalog = ExtensionCatalog(project_dir)
        self._write_valid_cache(
            catalog,
            {
                "jira": {
                    "name": "Jira Integration",
                    "id": "jira",
                    "version": "1.0.0",
                    "description": "Jira integration",
                }
            },
        )

        info = catalog.get_extension_info("jira")
        assert info is not None
        assert info["_install_allowed"] is False
        assert info["_catalog_name"] == "discovery"

    def test_search_results_include_catalog_metadata(self, temp_dir):
        """Search results include _catalog_name and _install_allowed."""
        project_dir = self._make_project(temp_dir)
        self._write_catalog_config(
            project_dir,
            [
                {
                    "name": "org",
                    "url": ExtensionCatalog.DEFAULT_CATALOG_URL,
                    "priority": 1,
                    "install_allowed": True,
                }
            ],
        )

        catalog = ExtensionCatalog(project_dir)
        self._write_valid_cache(
            catalog,
            {
                "jira": {
                    "name": "Jira Integration",
                    "id": "jira",
                    "version": "1.0.0",
                    "description": "Jira integration",
                }
            },
        )

        results = catalog.search()
        assert len(results) == 1
        assert results[0]["_catalog_name"] == "org"
        assert results[0]["_install_allowed"] is True


class TestExtensionIgnore:
    """Test .extensionignore support during extension installation."""

    def _make_extension(self, temp_dir, valid_manifest_data, extra_files=None, ignore_content=None):
        """Helper to create an extension directory with optional extra files and .extensionignore."""
        import yaml

        ext_dir = temp_dir / "ignored-ext"
        ext_dir.mkdir()

        # Write manifest
        with open(ext_dir / "extension.yml", "w") as f:
            yaml.dump(valid_manifest_data, f)

        # Create commands directory with a command file
        commands_dir = ext_dir / "commands"
        commands_dir.mkdir()
        (commands_dir / "hello.md").write_text(
            "---\ndescription: \"Test hello command\"\n---\n\n# Hello\n\n$ARGUMENTS\n"
        )

        # Create any extra files/dirs
        if extra_files:
            for rel_path, content in extra_files.items():
                p = ext_dir / rel_path
                p.parent.mkdir(parents=True, exist_ok=True)
                if content is None:
                    # Create directory
                    p.mkdir(parents=True, exist_ok=True)
                else:
                    p.write_text(content)

        # Write .extensionignore. Pinned to UTF-8 so non-ASCII patterns
        # in tests (see ``test_extensionignore_utf8_patterns``) survive
        # the round-trip on Windows runners with non-UTF-8 default locales.
        if ignore_content is not None:
            (ext_dir / ".extensionignore").write_text(
                ignore_content, encoding="utf-8"
            )

        return ext_dir

    def test_no_extensionignore(self, temp_dir, valid_manifest_data):
        """Without .extensionignore, all files are copied."""
        ext_dir = self._make_extension(
            temp_dir,
            valid_manifest_data,
            extra_files={"README.md": "# Hello", "tests/test_foo.py": "pass"},
        )

        proj_dir = temp_dir / "project"
        proj_dir.mkdir()
        (proj_dir / ".specify").mkdir()

        manager = ExtensionManager(proj_dir)
        manager.install_from_directory(ext_dir, "0.1.0", register_commands=False)

        dest = proj_dir / ".specify" / "extensions" / "test-ext"
        assert (dest / "README.md").exists()
        assert (dest / "tests" / "test_foo.py").exists()

    def test_extensionignore_excludes_files(self, temp_dir, valid_manifest_data):
        """Files matching .extensionignore patterns are excluded."""
        ext_dir = self._make_extension(
            temp_dir,
            valid_manifest_data,
            extra_files={
                "README.md": "# Hello",
                "tests/test_foo.py": "pass",
                "tests/test_bar.py": "pass",
                ".github/workflows/ci.yml": "on: push",
            },
            ignore_content="tests/\n.github/\n",
        )

        proj_dir = temp_dir / "project"
        proj_dir.mkdir()
        (proj_dir / ".specify").mkdir()

        manager = ExtensionManager(proj_dir)
        manager.install_from_directory(ext_dir, "0.1.0", register_commands=False)

        dest = proj_dir / ".specify" / "extensions" / "test-ext"
        # Included
        assert (dest / "README.md").exists()
        assert (dest / "extension.yml").exists()
        assert (dest / "commands" / "hello.md").exists()
        # Excluded
        assert not (dest / "tests").exists()
        assert not (dest / ".github").exists()

    def test_extensionignore_glob_patterns(self, temp_dir, valid_manifest_data):
        """Glob patterns like *.pyc are respected."""
        ext_dir = self._make_extension(
            temp_dir,
            valid_manifest_data,
            extra_files={
                "README.md": "# Hello",
                "helpers.pyc": b"\x00".decode("latin-1"),
                "commands/cache.pyc": b"\x00".decode("latin-1"),
            },
            ignore_content="*.pyc\n",
        )

        proj_dir = temp_dir / "project"
        proj_dir.mkdir()
        (proj_dir / ".specify").mkdir()

        manager = ExtensionManager(proj_dir)
        manager.install_from_directory(ext_dir, "0.1.0", register_commands=False)

        dest = proj_dir / ".specify" / "extensions" / "test-ext"
        assert (dest / "README.md").exists()
        assert not (dest / "helpers.pyc").exists()
        assert not (dest / "commands" / "cache.pyc").exists()

    def test_extensionignore_comments_and_blanks(self, temp_dir, valid_manifest_data):
        """Comments and blank lines in .extensionignore are ignored."""
        ext_dir = self._make_extension(
            temp_dir,
            valid_manifest_data,
            extra_files={"README.md": "# Hello", "notes.txt": "some notes"},
            ignore_content="# This is a comment\n\nnotes.txt\n\n# Another comment\n",
        )

        proj_dir = temp_dir / "project"
        proj_dir.mkdir()
        (proj_dir / ".specify").mkdir()

        manager = ExtensionManager(proj_dir)
        manager.install_from_directory(ext_dir, "0.1.0", register_commands=False)

        dest = proj_dir / ".specify" / "extensions" / "test-ext"
        assert (dest / "README.md").exists()
        assert not (dest / "notes.txt").exists()

    def test_extensionignore_itself_excluded(self, temp_dir, valid_manifest_data):
        """.extensionignore is never copied to the destination."""
        ext_dir = self._make_extension(
            temp_dir,
            valid_manifest_data,
            ignore_content="# nothing special here\n",
        )

        proj_dir = temp_dir / "project"
        proj_dir.mkdir()
        (proj_dir / ".specify").mkdir()

        manager = ExtensionManager(proj_dir)
        manager.install_from_directory(ext_dir, "0.1.0", register_commands=False)

        dest = proj_dir / ".specify" / "extensions" / "test-ext"
        assert (dest / "extension.yml").exists()
        assert not (dest / ".extensionignore").exists()

    def test_extensionignore_relative_path_match(self, temp_dir, valid_manifest_data):
        """Patterns matching relative paths work correctly."""
        ext_dir = self._make_extension(
            temp_dir,
            valid_manifest_data,
            extra_files={
                "docs/guide.md": "# Guide",
                "docs/internal/draft.md": "draft",
                "README.md": "# Hello",
            },
            ignore_content="docs/internal/draft.md\n",
        )

        proj_dir = temp_dir / "project"
        proj_dir.mkdir()
        (proj_dir / ".specify").mkdir()

        manager = ExtensionManager(proj_dir)
        manager.install_from_directory(ext_dir, "0.1.0", register_commands=False)

        dest = proj_dir / ".specify" / "extensions" / "test-ext"
        assert (dest / "docs" / "guide.md").exists()
        assert not (dest / "docs" / "internal" / "draft.md").exists()

    def test_extensionignore_dotdot_pattern_is_noop(self, temp_dir, valid_manifest_data):
        """Patterns with '..' should not escape the extension root."""
        ext_dir = self._make_extension(
            temp_dir,
            valid_manifest_data,
            extra_files={"README.md": "# Hello"},
            ignore_content="../sibling/\n",
        )

        proj_dir = temp_dir / "project"
        proj_dir.mkdir()
        (proj_dir / ".specify").mkdir()

        manager = ExtensionManager(proj_dir)
        manager.install_from_directory(ext_dir, "0.1.0", register_commands=False)

        dest = proj_dir / ".specify" / "extensions" / "test-ext"
        # Everything should still be copied — the '..' pattern matches nothing inside
        assert (dest / "README.md").exists()
        assert (dest / "extension.yml").exists()
        assert (dest / "commands" / "hello.md").exists()

    def test_extensionignore_absolute_path_pattern_is_noop(self, temp_dir, valid_manifest_data):
        """Absolute path patterns should not match anything."""
        ext_dir = self._make_extension(
            temp_dir,
            valid_manifest_data,
            extra_files={"README.md": "# Hello", "passwd": "sensitive"},
            ignore_content="/etc/passwd\n",
        )

        proj_dir = temp_dir / "project"
        proj_dir.mkdir()
        (proj_dir / ".specify").mkdir()

        manager = ExtensionManager(proj_dir)
        manager.install_from_directory(ext_dir, "0.1.0", register_commands=False)

        dest = proj_dir / ".specify" / "extensions" / "test-ext"
        # Nothing matches — /etc/passwd is anchored to root and there's no 'etc' dir
        assert (dest / "README.md").exists()
        assert (dest / "passwd").exists()

    def test_extensionignore_empty_file(self, temp_dir, valid_manifest_data):
        """An empty .extensionignore should exclude only itself."""
        ext_dir = self._make_extension(
            temp_dir,
            valid_manifest_data,
            extra_files={"README.md": "# Hello", "notes.txt": "notes"},
            ignore_content="",
        )

        proj_dir = temp_dir / "project"
        proj_dir.mkdir()
        (proj_dir / ".specify").mkdir()

        manager = ExtensionManager(proj_dir)
        manager.install_from_directory(ext_dir, "0.1.0", register_commands=False)

        dest = proj_dir / ".specify" / "extensions" / "test-ext"
        assert (dest / "README.md").exists()
        assert (dest / "notes.txt").exists()
        assert (dest / "extension.yml").exists()
        # .extensionignore itself is still excluded
        assert not (dest / ".extensionignore").exists()

    def test_extensionignore_windows_backslash_patterns(self, temp_dir, valid_manifest_data):
        """Backslash patterns (Windows-style) are normalised to forward slashes."""
        ext_dir = self._make_extension(
            temp_dir,
            valid_manifest_data,
            extra_files={
                "docs/internal/draft.md": "draft",
                "docs/guide.md": "# Guide",
            },
            ignore_content="docs\\internal\\draft.md\n",
        )

        proj_dir = temp_dir / "project"
        proj_dir.mkdir()
        (proj_dir / ".specify").mkdir()

        manager = ExtensionManager(proj_dir)
        manager.install_from_directory(ext_dir, "0.1.0", register_commands=False)

        dest = proj_dir / ".specify" / "extensions" / "test-ext"
        assert (dest / "docs" / "guide.md").exists()
        assert not (dest / "docs" / "internal" / "draft.md").exists()

    def test_extensionignore_utf8_patterns(self, temp_dir, valid_manifest_data):
        """Non-ASCII patterns in .extensionignore work on every locale.

        ``Path.read_text`` defaults to the system locale codec on Windows
        (cp1252 / gb2312 / cp932). Without an explicit ``encoding="utf-8"``,
        a pattern like ``ドキュメント/`` written by a UTF-8 host becomes
        mojibake on a cp1252 host and silently fails to match — leaking
        files the author intended to exclude. The existing
        ``test_extensionignore_windows_backslash_patterns`` already shows
        the codebase treats this as a Windows-author-friendly file; UTF-8
        is part of that same contract.
        """
        ext_dir = self._make_extension(
            temp_dir,
            valid_manifest_data,
            extra_files={
                "ドキュメント/private.md": "secret",
                "ドキュメント/public.md": "public",
                "docs/guide.md": "# Guide",
                "café/résumé.txt": "draft",
            },
            ignore_content="ドキュメント/\ncafé/\n",
        )

        proj_dir = temp_dir / "project"
        proj_dir.mkdir()
        (proj_dir / ".specify").mkdir()

        manager = ExtensionManager(proj_dir)
        manager.install_from_directory(ext_dir, "0.1.0", register_commands=False)

        dest = proj_dir / ".specify" / "extensions" / "test-ext"
        # Multibyte patterns excluded.
        assert not (dest / "ドキュメント").exists()
        assert not (dest / "café").exists()
        # ASCII path with no matching pattern is unaffected.
        assert (dest / "docs" / "guide.md").exists()

    def test_extensionignore_invalid_utf8_raises_validation_error(
        self, temp_dir, valid_manifest_data
    ):
        """A non-UTF-8 ``.extensionignore`` surfaces as ``ValidationError``.

        Pinning ``encoding="utf-8"`` on the reader means an
        ``.extensionignore`` written in some other codec (cp1252, etc.)
        now triggers ``UnicodeDecodeError`` instead of silently
        mojibake-ing patterns. Wrap that exception as ``ValidationError``
        with a pointer to the offending byte — the same pattern
        ``ExtensionManifest._load_yaml`` uses for ``extension.yml`` —
        so installation aborts with a user-friendly message instead of a
        raw Python traceback.
        """
        ext_dir = self._make_extension(temp_dir, valid_manifest_data)
        # Write an .extensionignore whose bytes are not valid UTF-8.
        # 0xE9 is 'é' in cp1252 but an invalid lead byte in UTF-8.
        (ext_dir / ".extensionignore").write_bytes(b"caf\xe9/\n")

        proj_dir = temp_dir / "project"
        proj_dir.mkdir()
        (proj_dir / ".specify").mkdir()

        manager = ExtensionManager(proj_dir)
        with pytest.raises(
            ValidationError, match=r"\.extensionignore is not valid UTF-8"
        ):
            manager.install_from_directory(ext_dir, "0.1.0", register_commands=False)

    def test_extensionignore_star_does_not_cross_directories(self, temp_dir, valid_manifest_data):
        """'*' should NOT match across directory boundaries (gitignore semantics)."""
        ext_dir = self._make_extension(
            temp_dir,
            valid_manifest_data,
            extra_files={
                "docs/api.draft.md": "draft",
                "docs/sub/api.draft.md": "nested draft",
            },
            ignore_content="docs/*.draft.md\n",
        )

        proj_dir = temp_dir / "project"
        proj_dir.mkdir()
        (proj_dir / ".specify").mkdir()

        manager = ExtensionManager(proj_dir)
        manager.install_from_directory(ext_dir, "0.1.0", register_commands=False)

        dest = proj_dir / ".specify" / "extensions" / "test-ext"
        # docs/*.draft.md should only match directly inside docs/, NOT subdirs
        assert not (dest / "docs" / "api.draft.md").exists()
        assert (dest / "docs" / "sub" / "api.draft.md").exists()

    def test_extensionignore_doublestar_crosses_directories(self, temp_dir, valid_manifest_data):
        """'**' should match across directory boundaries."""
        ext_dir = self._make_extension(
            temp_dir,
            valid_manifest_data,
            extra_files={
                "docs/api.draft.md": "draft",
                "docs/sub/api.draft.md": "nested draft",
                "docs/guide.md": "guide",
            },
            ignore_content="docs/**/*.draft.md\n",
        )

        proj_dir = temp_dir / "project"
        proj_dir.mkdir()
        (proj_dir / ".specify").mkdir()

        manager = ExtensionManager(proj_dir)
        manager.install_from_directory(ext_dir, "0.1.0", register_commands=False)

        dest = proj_dir / ".specify" / "extensions" / "test-ext"
        assert not (dest / "docs" / "api.draft.md").exists()
        assert not (dest / "docs" / "sub" / "api.draft.md").exists()
        assert (dest / "docs" / "guide.md").exists()

    def test_extensionignore_negation_pattern(self, temp_dir, valid_manifest_data):
        """'!' negation re-includes a previously excluded file."""
        ext_dir = self._make_extension(
            temp_dir,
            valid_manifest_data,
            extra_files={
                "docs/guide.md": "# Guide",
                "docs/internal.md": "internal",
                "docs/api.md": "api",
            },
            ignore_content="docs/*.md\n!docs/api.md\n",
        )

        proj_dir = temp_dir / "project"
        proj_dir.mkdir()
        (proj_dir / ".specify").mkdir()

        manager = ExtensionManager(proj_dir)
        manager.install_from_directory(ext_dir, "0.1.0", register_commands=False)

        dest = proj_dir / ".specify" / "extensions" / "test-ext"
        # docs/*.md excludes all .md in docs, but !docs/api.md re-includes it
        assert not (dest / "docs" / "guide.md").exists()
        assert not (dest / "docs" / "internal.md").exists()
        assert (dest / "docs" / "api.md").exists()


class TestExtensionAddCLI:
    """CLI integration tests for extension add command."""

    def test_catalog_add_escapes_url_markup(self, tmp_path):
        """Catalog add should render user-supplied URLs literally."""
        from typer.testing import CliRunner
        from unittest.mock import patch
        from specify_cli import app

        project_dir = tmp_path / "test-project"
        project_dir.mkdir()
        (project_dir / ".specify").mkdir()

        url = "https://example.com/[red]catalog[/red].json"

        runner = CliRunner()
        with patch.object(Path, "cwd", return_value=project_dir):
            result = runner.invoke(
                app,
                [
                    "extension",
                    "catalog",
                    "add",
                    url,
                    "--name",
                    "community",
                ],
                catch_exceptions=True,
            )

        assert result.exit_code == 0, result.output
        assert f"URL: {url}" in result.output

    def test_catalog_add_escapes_config_saved_path_markup(self, tmp_path):
        """Catalog add's saved-path label should render literally under Rich."""
        from typer.testing import CliRunner
        from unittest.mock import patch
        from specify_cli import app

        project_dir = tmp_path / "test-project"
        project_dir.mkdir()
        (project_dir / ".specify").mkdir()

        display_path = "project[red]/.specify/extension-catalogs.yml"

        runner = CliRunner()
        with patch.object(Path, "cwd", return_value=project_dir), \
             patch("specify_cli.extensions._commands._display_project_path", return_value=display_path):
            result = runner.invoke(
                app,
                [
                    "extension",
                    "catalog",
                    "add",
                    "https://example.com/catalog.json",
                    "--name",
                    "community",
                ],
                catch_exceptions=True,
            )

        assert result.exit_code == 0, result.output
        assert f"Config saved to {display_path}" in result.output

    def test_catalog_list_escapes_config_path_markup(self, tmp_path):
        """Catalog list's config-path label should render literally under Rich."""
        from typer.testing import CliRunner
        from unittest.mock import patch
        from specify_cli import app
        import yaml

        project_dir = tmp_path / "test-project"
        project_dir.mkdir()
        specify_dir = project_dir / ".specify"
        specify_dir.mkdir()
        (specify_dir / "extension-catalogs.yml").write_text(
            yaml.safe_dump(
                {
                    "catalogs": [
                        {
                            "name": "community",
                            "url": "https://example.com/catalog.json",
                            "priority": 10,
                            "install_allowed": False,
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )

        display_path = "project[red]/.specify/extension-catalogs.yml"

        runner = CliRunner()
        with patch.object(Path, "cwd", return_value=project_dir), \
             patch("specify_cli.extensions._commands._display_project_path", return_value=display_path):
            result = runner.invoke(
                app,
                ["extension", "catalog", "list"],
                catch_exceptions=True,
            )

        assert result.exit_code == 0, result.output
        assert f"Config: {display_path}" in result.output

    def test_catalog_add_escapes_config_read_exception_markup(self, tmp_path):
        """Catalog config parse errors can include user-controlled file content."""
        import yaml
        from typer.testing import CliRunner
        from unittest.mock import patch
        from specify_cli import app

        project_dir = tmp_path / "test-project"
        project_dir.mkdir()
        specify_dir = project_dir / ".specify"
        specify_dir.mkdir()
        (specify_dir / "extension-catalogs.yml").write_text("[red]bad[/red]", encoding="utf-8")

        runner = CliRunner()
        with patch.object(Path, "cwd", return_value=project_dir), \
             patch(
                 "specify_cli.extensions._commands.yaml.safe_load",
                 side_effect=yaml.YAMLError("bad [red]catalog[/red] yaml"),
             ):
            result = runner.invoke(
                app,
                [
                    "extension",
                    "catalog",
                    "add",
                    "https://example.com/catalog.json",
                    "--name",
                    "community",
                ],
                catch_exceptions=True,
            )

        assert result.exit_code == 1, result.output
        assert "bad [red]catalog[/red]" in result.output
        assert "yaml" in result.output

    def test_catalog_add_escapes_url_validation_exception_markup(self, tmp_path):
        """URL validation errors may include user-controlled URL text."""
        from typer.testing import CliRunner
        from unittest.mock import patch
        from specify_cli import app

        project_dir = tmp_path / "test-project"
        project_dir.mkdir()
        (project_dir / ".specify").mkdir()

        runner = CliRunner()
        with patch.object(Path, "cwd", return_value=project_dir), \
             patch.object(
                 ExtensionCatalog,
                 "_validate_catalog_url",
                 side_effect=ValidationError("bad [red]url[/red]"),
             ):
            result = runner.invoke(
                app,
                [
                    "extension",
                    "catalog",
                    "add",
                    "https://example.com/[red]catalog[/red].json",
                    "--name",
                    "community",
                ],
                catch_exceptions=True,
            )

        assert result.exit_code == 1, result.output
        assert "bad [red]url[/red]" in result.output

    def test_add_dev_links_copilot_agent_when_supported(
        self, extension_dir, project_dir, temp_dir
    ):
        """extension add --dev should link generated agent files when possible."""
        from typer.testing import CliRunner
        from unittest.mock import patch
        from specify_cli import app

        (project_dir / ".github" / "agents").mkdir(parents=True)

        runner = CliRunner()
        with patch.object(Path, "cwd", return_value=project_dir):
            result = runner.invoke(
                app,
                ["extension", "add", str(extension_dir), "--dev"],
                catch_exceptions=True,
            )

        assert result.exit_code == 0, result.output

        agent_file = (
            project_dir
            / ".github"
            / "agents"
            / "speckit.test-ext.hello.agent.md"
        )
        assert agent_file.exists()
        if can_create_symlink(temp_dir):
            assert agent_file.is_symlink()
            assert ".specify-dev" in agent_file.resolve().parts
        else:
            assert not agent_file.is_symlink()

    def test_add_dev_writes_codex_skills_as_files(self, extension_dir, project_dir):
        """Codex dev skills should be written as files so Codex can load them."""
        from typer.testing import CliRunner
        from unittest.mock import patch
        from specify_cli import app

        init_options = project_dir / ".specify" / "init-options.json"
        init_options.write_text(
            json.dumps({"ai": "codex", "ai_skills": True}), encoding="utf-8"
        )

        runner = CliRunner()
        with patch.object(Path, "cwd", return_value=project_dir):
            result = runner.invoke(
                app,
                ["extension", "add", str(extension_dir), "--dev"],
                catch_exceptions=True,
            )

        assert result.exit_code == 0, result.output

        skill_file = (
            project_dir
            / ".agents"
            / "skills"
            / "speckit-test-ext-hello"
            / "SKILL.md"
        )
        assert skill_file.exists()
        assert not skill_file.is_symlink()

        content = skill_file.read_text(encoding="utf-8")
        assert "name: speckit-test-ext-hello" in content
        assert "metadata:" in content
        assert "source: test-ext:commands/hello.md" in content

    def test_add_dev_replaces_existing_codex_skill_symlink(
        self, extension_dir, project_dir, temp_dir
    ):
        """Codex dev installs should migrate expected dev symlinks to files."""
        if not can_create_symlink(temp_dir):
            pytest.skip("Current platform/user cannot create symlinks")

        from typer.testing import CliRunner
        from unittest.mock import patch
        from specify_cli import app

        init_options = project_dir / ".specify" / "init-options.json"
        init_options.write_text(
            json.dumps({"ai": "codex", "ai_skills": True}), encoding="utf-8"
        )

        skill_file = (
            project_dir
            / ".agents"
            / "skills"
            / "speckit-test-ext-hello"
            / "SKILL.md"
        )
        skill_file.parent.mkdir(parents=True)
        cache_file = (
            extension_dir
            / ".specify-dev"
            / "extension-skills"
            / "speckit-test-ext-hello"
            / "SKILL.md"
        )
        cache_file.parent.mkdir(parents=True)
        cache_file.write_text("old linked content", encoding="utf-8")
        os.symlink(os.path.relpath(cache_file, skill_file.parent), skill_file)

        runner = CliRunner()
        with patch.object(Path, "cwd", return_value=project_dir):
            result = runner.invoke(
                app,
                ["extension", "add", str(extension_dir), "--dev"],
                catch_exceptions=True,
            )

        assert result.exit_code == 0, result.output
        assert skill_file.exists()
        assert not skill_file.is_symlink()
        content = skill_file.read_text(encoding="utf-8")
        assert "name: speckit-test-ext-hello" in content
        assert "source: test-ext:commands/hello.md" in content
        assert cache_file.read_text(encoding="utf-8") == "old linked content"

    def test_add_dev_falls_back_to_copy_when_windows_symlinks_unavailable(
        self, extension_dir, project_dir, monkeypatch
    ):
        """extension add --dev should work when Windows cannot create symlinks."""
        from typer.testing import CliRunner
        from unittest.mock import patch
        from specify_cli import app

        (project_dir / ".github" / "agents").mkdir(parents=True)

        def raise_windows_symlink_error(target, link):
            raise OSError("A required privilege is not held by the client")

        monkeypatch.setattr(
            "specify_cli.agents.os.symlink", raise_windows_symlink_error
        )

        runner = CliRunner()
        with patch.object(Path, "cwd", return_value=project_dir):
            result = runner.invoke(
                app,
                ["extension", "add", str(extension_dir), "--dev"],
                catch_exceptions=True,
            )

        assert result.exit_code == 0, result.output

        agent_file = (
            project_dir
            / ".github"
            / "agents"
            / "speckit.test-ext.hello.agent.md"
        )
        assert agent_file.exists()
        assert not agent_file.is_symlink()
        assert "Extension: test-ext" in agent_file.read_text(encoding="utf-8")
        assert (
            project_dir
            / ".specify"
            / "extensions"
            / "test-ext"
            / ".specify-dev"
            / "agent-commands"
            / "copilot"
            / "speckit.test-ext.hello.agent.md"
        ).exists()

    def test_add_by_display_name_uses_resolved_id_for_download(self, tmp_path):
        """extension add by display name should use resolved ID for download_extension()."""
        from typer.testing import CliRunner
        from unittest.mock import patch, MagicMock
        from specify_cli import app

        runner = CliRunner()

        # Create project structure
        project_dir = tmp_path / "test-project"
        project_dir.mkdir()
        (project_dir / ".specify").mkdir()
        (project_dir / ".specify" / "extensions").mkdir(parents=True)

        # Mock catalog that returns extension by display name
        mock_catalog = MagicMock()
        mock_catalog.get_extension_info.return_value = None  # ID lookup fails
        mock_catalog.search.return_value = [
            {
                "id": "acme-jira-integration",
                "name": "Jira Integration",
                "version": "1.0.0",
                "description": "Jira integration extension",
                "_install_allowed": True,
            }
        ]

        # Track what ID was passed to download_extension
        download_called_with = []
        def mock_download(extension_id):
            download_called_with.append(extension_id)
            # Return a path that will fail install (we just want to verify the ID)
            raise ExtensionError("Mock download - checking ID was resolved")

        mock_catalog.download_extension.side_effect = mock_download

        with patch("specify_cli.extensions.ExtensionCatalog", return_value=mock_catalog), \
             patch.object(Path, "cwd", return_value=project_dir):
            result = runner.invoke(
                app,
                ["extension", "add", "Jira Integration"],
                catch_exceptions=True,
            )

        assert result.exit_code != 0, (
            f"Expected non-zero exit code since mock download raises, got {result.exit_code}"
        )

        # Verify download_extension was called with the resolved ID, not the display name
        assert len(download_called_with) == 1
        assert download_called_with[0] == "acme-jira-integration", (
            f"Expected download_extension to be called with resolved ID 'acme-jira-integration', "
            f"but was called with '{download_called_with[0]}'"
        )

    def test_add_bundled_extension_not_found_gives_clear_error(self, tmp_path):
        """extension add should give a clear error when a bundled extension is not found locally."""
        from typer.testing import CliRunner
        from unittest.mock import patch, MagicMock
        from specify_cli import app

        runner = CliRunner()

        # Create project structure
        project_dir = tmp_path / "test-project"
        project_dir.mkdir()
        (project_dir / ".specify").mkdir()
        (project_dir / ".specify" / "extensions").mkdir(parents=True)

        # Mock catalog that returns a bundled extension without download_url
        mock_catalog = MagicMock()
        mock_catalog.get_extension_info.return_value = {
            "id": "git",
            "name": "Git Branching Workflow",
            "version": "1.0.0",
            "description": "Git branching extension",
            "bundled": True,
            "_install_allowed": True,
        }
        mock_catalog.search.return_value = []

        with patch("specify_cli.extensions.ExtensionCatalog", return_value=mock_catalog), \
             patch("specify_cli._locate_bundled_extension", return_value=None), \
             patch.object(Path, "cwd", return_value=project_dir):
            result = runner.invoke(
                app,
                ["extension", "add", "git"],
                catch_exceptions=True,
            )

        assert result.exit_code != 0
        assert "bundled with spec-kit" in result.output
        assert "reinstall" in result.output.lower()

    def test_add_from_url_prompts_before_spinner(self, tmp_path):
        """Confirm prompt for --from <url> must fire before the console.status spinner.

        Regression test for #2783: typer.confirm() inside console.status()
        was overwritten by the Rich spinner, making the command appear hung.
        """
        from typer.testing import CliRunner
        from unittest.mock import patch, MagicMock
        from specify_cli import app

        project_dir = tmp_path / "test-project"
        project_dir.mkdir()
        (project_dir / ".specify").mkdir()

        call_order: list[str] = []

        original_status = MagicMock()

        def record_status(*args, **kwargs):
            call_order.append("spinner")
            return original_status

        runner = CliRunner()
        with patch.object(Path, "cwd", return_value=project_dir), \
             patch("specify_cli.console.status", side_effect=record_status), \
             patch("typer.confirm", side_effect=lambda *a, **kw: (call_order.append("confirm"), False)[-1]):
            result = runner.invoke(
                app,
                ["extension", "add", "my-ext", "--from", "https://example.com/ext.zip"],
                catch_exceptions=True,
            )

        assert "confirm" in call_order, "confirm prompt was never called"
        # The confirm must fire BEFORE the spinner is entered
        if "spinner" in call_order:
            assert call_order.index("confirm") < call_order.index("spinner"), \
                f"confirm must precede spinner, got: {call_order}"
        assert result.exit_code == 0  # user declined → clean exit

    def test_add_status_escapes_extension_markup(self, tmp_path):
        """User-controlled extension names must not be parsed as Rich markup."""
        from rich.markup import escape as escape_markup
        from typer.testing import CliRunner
        from unittest.mock import MagicMock, patch
        from specify_cli import app

        project_dir = tmp_path / "test-project"
        project_dir.mkdir()
        (project_dir / ".specify").mkdir()

        status_messages: list[str] = []

        def record_status(message, *args, **kwargs):
            status_messages.append(message)
            return MagicMock()

        extension_name = "[red]bad[/red]"
        runner = CliRunner()
        with patch.object(Path, "cwd", return_value=project_dir), \
             patch("specify_cli.console.status", side_effect=record_status):
            result = runner.invoke(
                app,
                ["extension", "add", extension_name, "--dev"],
                catch_exceptions=True,
            )

        assert result.exit_code == 1
        assert status_messages == [
            f"[cyan]Installing extension: {escape_markup(extension_name)}[/cyan]"
        ]

    def test_add_post_install_hint_escapes_manifest_id_markup(self, tmp_path):
        """Extension IDs printed in Rich-rendered hints must stay literal."""
        import io
        from types import SimpleNamespace
        from typer.testing import CliRunner
        from unittest.mock import patch
        from specify_cli import app

        class FakeResponse(io.BytesIO):
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

        project_dir = tmp_path / "test-project"
        project_dir.mkdir()
        (project_dir / ".specify").mkdir()

        manifest_id = "[red]bad[/red]"

        def fake_install_from_zip(self_obj, zip_path, speckit_version, priority=10, force=False):
            return SimpleNamespace(
                id=manifest_id,
                name="Bad Extension",
                version="1.0.0",
                description="Test extension",
                warnings=[],
                commands=[],
                hooks=[],
            )

        runner = CliRunner()
        with patch.object(Path, "cwd", return_value=project_dir), \
             patch("typer.confirm", return_value=True), \
             patch("specify_cli.authentication.http.open_url", return_value=FakeResponse(_MINIMAL_ZIP_BYTES)), \
             patch.object(ExtensionManager, "install_from_zip", fake_install_from_zip), \
             patch.object(ExtensionRegistry, "get", return_value={}):
            result = runner.invoke(
                app,
                ["extension", "add", "bad", "--from", "https://example.com/ext.zip"],
                catch_exceptions=True,
            )

        assert result.exit_code == 0, result.output
        assert ".specify/extensions/[red]bad[/red]/" in result.output

    def test_add_from_url_cancel_exits_cleanly(self, tmp_path):
        """Declining the --from <url> confirmation should exit with code 0."""
        from typer.testing import CliRunner
        from unittest.mock import patch
        from specify_cli import app

        project_dir = tmp_path / "test-project"
        project_dir.mkdir()
        (project_dir / ".specify").mkdir()

        runner = CliRunner()
        with patch.object(Path, "cwd", return_value=project_dir), \
             patch("typer.confirm", return_value=False):
            result = runner.invoke(
                app,
                ["extension", "add", "my-ext", "--from", "https://example.com/ext.zip"],
                catch_exceptions=True,
            )

        assert result.exit_code == 0
        assert "Cancelled" in result.output

    def test_add_from_url_escapes_download_exception_markup(self, tmp_path):
        """Download errors can include user-controlled URL text."""
        import urllib.error
        from typer.testing import CliRunner
        from unittest.mock import patch
        from specify_cli import app

        project_dir = tmp_path / "test-project"
        project_dir.mkdir()
        (project_dir / ".specify").mkdir()

        runner = CliRunner()
        with patch.object(Path, "cwd", return_value=project_dir), \
             patch("typer.confirm", return_value=True), \
             patch(
                 "specify_cli.authentication.http.open_url",
                 side_effect=urllib.error.URLError("bad [red]download[/red]"),
             ):
            result = runner.invoke(
                app,
                [
                    "extension",
                    "add",
                    "my-ext",
                    "--from",
                    "https://example.com/[red]ext[/red].zip",
                ],
                catch_exceptions=True,
            )

        assert result.exit_code == 1, result.output
        assert "https://example.com/[red]ext[/red].zip" in result.output
        assert "bad [red]download[/red]" in result.output

    def test_add_from_url_rejects_non_zip_login_page(self, tmp_path):
        """An HTML login page (unauthenticated fetch) must fail clearly, not BadZipFile."""
        import io
        from typer.testing import CliRunner
        from unittest.mock import patch
        from specify_cli import app

        class FakeResponse(io.BytesIO):
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

        project_dir = tmp_path / "test-project"
        project_dir.mkdir()
        (project_dir / ".specify").mkdir()

        runner = CliRunner()
        with patch.object(Path, "cwd", return_value=project_dir), \
             patch("typer.confirm", return_value=True), \
             patch(
                 "specify_cli.authentication.http.open_url",
                 return_value=FakeResponse(b"<!DOCTYPE html><html>Sign in</html>"),
             ), \
             patch.object(ExtensionManager, "install_from_zip") as install:
            result = runner.invoke(
                app,
                ["extension", "add", "my-ext", "--from", "https://raw.ghe.example/o/r/ext.zip"],
                catch_exceptions=True,
            )

        assert result.exit_code == 1, result.output
        assert "did not return a ZIP archive" in result.output
        install.assert_not_called()

    def test_add_from_url_resolves_ghes_release_asset(self, tmp_path):
        """A GHES release-download URL resolves to /api/v3 with octet-stream Accept."""
        import io
        from types import SimpleNamespace
        from typer.testing import CliRunner
        from unittest.mock import patch
        from specify_cli import app
        import json

        class FakeResponse(io.BytesIO):
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

        project_dir = tmp_path / "test-project"
        project_dir.mkdir()
        (project_dir / ".specify").mkdir()
        seen = {}

        def fake_open_url(url, timeout=10, extra_headers=None, redirect_validator=None):
            if "/releases/tags/" in url:
                body = json.dumps({
                    "assets": [{
                        "name": "ext.zip",
                        "url": "https://ghes.example/api/v3/repos/org/repo/releases/assets/42",
                    }]
                }).encode()
                return FakeResponse(body)
            seen["url"] = url
            seen["headers"] = extra_headers
            return FakeResponse(_MINIMAL_ZIP_BYTES)

        def fake_install(self_obj, zip_path, speckit_version, priority=10, force=False):
            return SimpleNamespace(
                id="x", name="X", version="1.0.0", description="", warnings=[], commands=[], hooks=[]
            )

        runner = CliRunner()
        with patch.object(Path, "cwd", return_value=project_dir), \
             patch("typer.confirm", return_value=True), \
             patch("specify_cli.authentication.http.github_provider_hosts", return_value=("ghes.example",)), \
             patch("specify_cli.authentication.http.open_url", side_effect=fake_open_url), \
             patch.object(ExtensionManager, "install_from_zip", fake_install):
            result = runner.invoke(
                app,
                ["extension", "add", "x", "--from",
                 "https://ghes.example/org/repo/releases/download/v1.0/ext.zip"],
                catch_exceptions=True,
            )

        assert result.exit_code == 0, result.output
        assert "/api/v3/repos/org/repo/releases/assets/" in seen["url"]
        assert seen["headers"] == {"Accept": "application/octet-stream"}

    @pytest.mark.parametrize(
        ("exc_type", "label"),
        [
            (ValidationError, "Validation Error"),
            (CompatibilityError, "Compatibility Error"),
            (ExtensionError, "Error"),
        ],
    )
    def test_add_exception_handlers_escape_markup(self, tmp_path, exc_type, label):
        """Extension install exceptions can include manifest-controlled values."""
        from typer.testing import CliRunner
        from unittest.mock import patch
        from specify_cli import app

        project_dir = tmp_path / "test-project"
        project_dir.mkdir()
        (project_dir / ".specify").mkdir()

        ext_dir = tmp_path / "ext"
        ext_dir.mkdir()
        (ext_dir / "extension.yml").write_text("extension:\n  id: test\n", encoding="utf-8")

        runner = CliRunner()
        with patch.object(Path, "cwd", return_value=project_dir), \
             patch.object(
                 ExtensionManager,
                 "install_from_directory",
                 side_effect=exc_type("bad [red]extension[/red]"),
             ):
            result = runner.invoke(
                app,
                ["extension", "add", str(ext_dir), "--dev"],
                catch_exceptions=True,
            )

        assert result.exit_code == 1, result.output
        assert f"{label}:" in result.output
        assert "bad [red]extension[/red]" in result.output

    def test_add_from_url_uses_cache_tempfile_for_untrusted_extension_name(self, tmp_path):
        """The extension argument must not control the downloaded ZIP path."""
        import io
        from types import SimpleNamespace
        from typer.testing import CliRunner
        from unittest.mock import patch
        from specify_cli import app

        class FakeResponse(io.BytesIO):
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

        project_dir = tmp_path / "test-project"
        project_dir.mkdir()
        (project_dir / ".specify").mkdir()
        downloads_dir = project_dir / ".specify" / "extensions" / ".cache" / "downloads"
        installed = {}

        def fake_install_from_zip(self_obj, zip_path, speckit_version, priority=10, force=False):
            captured_path = Path(zip_path)
            installed["zip_path"] = captured_path
            installed["zip_bytes"] = captured_path.read_bytes()
            return SimpleNamespace(
                id="escape",
                name="Escape Test",
                version="1.0.0",
                description="Test extension",
                warnings=[],
                commands=[],
                hooks=[],
            )

        runner = CliRunner()
        with patch.object(Path, "cwd", return_value=project_dir), \
             patch("typer.confirm", return_value=True), \
             patch("specify_cli.authentication.http.open_url", return_value=FakeResponse(_MINIMAL_ZIP_BYTES)), \
             patch.object(ExtensionManager, "install_from_zip", fake_install_from_zip):
            result = runner.invoke(
                app,
                ["extension", "add", "../outside", "--from", "https://example.com/ext.zip"],
                catch_exceptions=True,
            )

        assert result.exit_code == 0
        assert installed["zip_bytes"] == _MINIMAL_ZIP_BYTES
        assert installed["zip_path"].resolve().is_relative_to(downloads_dir.resolve())
        assert installed["zip_path"].name.startswith("extension-url-download-")
        assert not installed["zip_path"].exists()


class TestDownloadExtensionBundled:
    """Tests for download_extension handling of bundled extensions."""

    def test_download_extension_raises_for_bundled(self, temp_dir):
        """download_extension should raise a clear error for bundled extensions without a URL."""
        from unittest.mock import patch

        project_dir = temp_dir / "project"
        project_dir.mkdir()
        (project_dir / ".specify").mkdir()

        catalog = ExtensionCatalog(project_dir)

        bundled_ext_info = {
            "name": "Git Branching Workflow",
            "id": "git",
            "version": "1.0.0",
            "description": "Git workflow",
            "bundled": True,
        }

        with patch.object(catalog, "get_extension_info", return_value=bundled_ext_info):
            with pytest.raises(ExtensionError, match="bundled with spec-kit"):
                catalog.download_extension("git")

    def test_download_extension_allows_bundled_with_url(self, temp_dir):
        """download_extension should allow bundled extensions that have a download_url (newer version)."""
        from unittest.mock import patch, MagicMock
        import urllib.request

        project_dir = temp_dir / "project"
        project_dir.mkdir()
        (project_dir / ".specify").mkdir()

        catalog = ExtensionCatalog(project_dir)

        bundled_with_url = {
            "name": "Git Branching Workflow",
            "id": "git",
            "version": "2.0.0",
            "description": "Git workflow",
            "bundled": True,
            "download_url": "https://example.com/git-2.0.0.zip",
        }

        mock_response = MagicMock()
        mock_response.read.return_value = b"fake zip data"
        mock_response.__enter__ = lambda s: s
        mock_response.__exit__ = MagicMock(return_value=False)

        with patch.object(catalog, "get_extension_info", return_value=bundled_with_url), \
             patch.object(urllib.request, "urlopen", return_value=mock_response):
            result = catalog.download_extension("git")
            assert result.name == "git-2.0.0.zip"

    def test_download_extension_raises_no_url_for_non_bundled(self, temp_dir):
        """download_extension should raise 'no download URL' for non-bundled extensions without URL."""
        from unittest.mock import patch

        project_dir = temp_dir / "project"
        project_dir.mkdir()
        (project_dir / ".specify").mkdir()

        catalog = ExtensionCatalog(project_dir)

        non_bundled_ext_info = {
            "name": "Some Extension",
            "id": "some-ext",
            "version": "1.0.0",
            "description": "Test",
        }

        with patch.object(catalog, "get_extension_info", return_value=non_bundled_ext_info):
            with pytest.raises(ExtensionError, match="has no download URL"):
                catalog.download_extension("some-ext")


class TestExtensionUpdateCLI:
    """CLI integration tests for extension update command."""

    @staticmethod
    def _create_extension_source(base_dir: Path, version: str, include_config: bool = False) -> Path:
        """Create a minimal extension source directory for install tests."""
        import yaml

        ext_dir = base_dir / f"test-ext-{version}"
        ext_dir.mkdir(parents=True, exist_ok=True)

        manifest = {
            "schema_version": "1.0",
            "extension": {
                "id": "test-ext",
                "name": "Test Extension",
                "version": version,
                "description": "A test extension",
            },
            "requires": {"speckit_version": ">=0.1.0"},
            "provides": {
                "commands": [
                    {
                        "name": "speckit.test-ext.hello",
                        "file": "commands/hello.md",
                        "description": "Test command",
                    }
                ]
            },
            "hooks": {
                "after_tasks": {
                    "command": "speckit.test-ext.hello",
                    "optional": True,
                }
            },
        }

        (ext_dir / "extension.yml").write_text(yaml.dump(manifest, sort_keys=False))
        commands_dir = ext_dir / "commands"
        commands_dir.mkdir(exist_ok=True)
        (commands_dir / "hello.md").write_text("---\ndescription: Test\n---\n\n$ARGUMENTS\n")
        if include_config:
            (ext_dir / "linear-config.yml").write_text("custom: true\nvalue: original\n")
        return ext_dir

    @staticmethod
    def _create_catalog_zip(zip_path: Path, version: str):
        """Create a minimal ZIP that passes extension_update ID validation."""
        import zipfile
        import yaml

        manifest = {
            "schema_version": "1.0",
            "extension": {
                "id": "test-ext",
                "name": "Test Extension",
                "version": version,
                "description": "A test extension",
            },
            "requires": {"speckit_version": ">=0.1.0"},
            "provides": {"commands": [{"name": "speckit.test-ext.hello", "file": "commands/hello.md"}]},
        }

        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("extension.yml", yaml.dump(manifest, sort_keys=False))

    def test_update_success_preserves_installed_at(self, tmp_path):
        """Successful update should keep original installed_at and apply new version."""
        from typer.testing import CliRunner
        from unittest.mock import patch
        from specify_cli import app

        runner = CliRunner()
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        (project_dir / ".specify").mkdir()
        (project_dir / ".claude" / "skills").mkdir(parents=True)

        manager = ExtensionManager(project_dir)
        v1_dir = self._create_extension_source(tmp_path, "1.0.0", include_config=True)
        manager.install_from_directory(v1_dir, "0.1.0")
        original_installed_at = manager.registry.get("test-ext")["installed_at"]
        original_config_content = (
            project_dir / ".specify" / "extensions" / "test-ext" / "linear-config.yml"
        ).read_text()

        zip_path = tmp_path / "test-ext-update.zip"
        self._create_catalog_zip(zip_path, "2.0.0")
        v2_dir = self._create_extension_source(tmp_path, "2.0.0")

        def fake_install_from_zip(self_obj, _zip_path, speckit_version):
            return self_obj.install_from_directory(v2_dir, speckit_version)

        with patch.object(Path, "cwd", return_value=project_dir), \
             patch.object(ExtensionCatalog, "get_extension_info", return_value={
                 "id": "test-ext",
                 "name": "Test Extension",
                 "version": "2.0.0",
                 "_install_allowed": True,
             }), \
             patch.object(ExtensionCatalog, "download_extension", return_value=zip_path), \
             patch.object(ExtensionManager, "install_from_zip", fake_install_from_zip):
            result = runner.invoke(app, ["extension", "update", "test-ext"], input="y\n", catch_exceptions=True)

        assert result.exit_code == 0, result.output

        updated = ExtensionManager(project_dir).registry.get("test-ext")
        assert updated["version"] == "2.0.0"
        assert updated["installed_at"] == original_installed_at
        restored_config_content = (
            project_dir / ".specify" / "extensions" / "test-ext" / "linear-config.yml"
        ).read_text()
        assert restored_config_content == original_config_content

    def test_update_failure_rolls_back_registry_hooks_and_commands(self, tmp_path, monkeypatch):
        """Failed update should restore original registry, hooks, and command files."""
        from typer.testing import CliRunner
        from unittest.mock import patch
        from specify_cli import app
        import yaml

        # Isolate home directory so Hermes' global ~/.hermes/skills/ doesn't
        # interfere — without a real skills dir, Hermes is skipped during
        # command registration, keeping the test focused on Claude/Codex/etc.
        fake_home = tmp_path / "home"
        fake_home.mkdir()
        monkeypatch.setattr(Path, "home", lambda: fake_home)

        runner = CliRunner()
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        (project_dir / ".specify").mkdir()
        (project_dir / ".claude" / "skills").mkdir(parents=True)

        manager = ExtensionManager(project_dir)
        v1_dir = self._create_extension_source(tmp_path, "1.0.0")
        manager.install_from_directory(v1_dir, "0.1.0")

        backup_registry_entry = manager.registry.get("test-ext")
        hooks_before = yaml.safe_load((project_dir / ".specify" / "extensions.yml").read_text())

        registered_commands = backup_registry_entry.get("registered_commands", {})
        command_files = []
        from specify_cli.agents import CommandRegistrar as AgentRegistrar
        agent_registrar = AgentRegistrar()
        for agent_name, cmd_names in registered_commands.items():
            if agent_name not in agent_registrar.AGENT_CONFIGS:
                continue
            agent_cfg = agent_registrar.AGENT_CONFIGS[agent_name]
            commands_dir = AgentRegistrar._resolve_agent_dir(
                agent_name, agent_cfg, project_dir
            )
            for cmd_name in cmd_names:
                output_name = AgentRegistrar._compute_output_name(agent_name, cmd_name, agent_cfg)
                cmd_path = commands_dir / f"{output_name}{agent_cfg['extension']}"
                command_files.append(cmd_path)

        assert command_files, "Expected at least one registered command file"
        for cmd_file in command_files:
            assert cmd_file.exists(), f"Expected command file to exist before update: {cmd_file}"

        zip_path = tmp_path / "test-ext-update.zip"
        self._create_catalog_zip(zip_path, "2.0.0")

        with patch.object(Path, "cwd", return_value=project_dir), \
             patch.object(ExtensionCatalog, "get_extension_info", return_value={
                 "id": "test-ext",
                 "name": "Test Extension",
                 "version": "2.0.0",
                 "_install_allowed": True,
             }), \
             patch.object(ExtensionCatalog, "download_extension", return_value=zip_path), \
             patch.object(ExtensionManager, "install_from_zip", side_effect=RuntimeError("install failed")):
            result = runner.invoke(app, ["extension", "update", "test-ext"], input="y\n", catch_exceptions=True)

        assert result.exit_code == 1, result.output

        restored_entry = ExtensionManager(project_dir).registry.get("test-ext")
        assert restored_entry == backup_registry_entry

        hooks_after = yaml.safe_load((project_dir / ".specify" / "extensions.yml").read_text())
        assert hooks_after == hooks_before

        for cmd_file in command_files:
            assert cmd_file.exists(), f"Expected command file to be restored after rollback: {cmd_file}"

    @pytest.mark.parametrize(
        ("manifest_text", "expected_detail"),
        [
            ("- not\n- a\n- mapping\n", "YAML mapping"),
            ("extension: []\n", "'extension' mapping"),
        ],
    )
    def test_update_rejects_malformed_zip_manifest(
        self, tmp_path, monkeypatch, manifest_text, expected_detail
    ):
        """Downloaded extension.yml shape must be valid before ID validation."""
        from typer.testing import CliRunner
        from unittest.mock import patch
        from specify_cli import app
        import zipfile

        fake_home = tmp_path / "home"
        fake_home.mkdir()
        monkeypatch.setattr(Path, "home", lambda: fake_home)

        runner = CliRunner()
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        (project_dir / ".specify").mkdir()
        (project_dir / ".claude" / "skills").mkdir(parents=True)

        manager = ExtensionManager(project_dir)
        v1_dir = self._create_extension_source(tmp_path, "1.0.0")
        manager.install_from_directory(v1_dir, "0.1.0")
        original_registry_entry = manager.registry.get("test-ext")

        zip_path = tmp_path / "bad-manifest.zip"
        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("extension.yml", manifest_text)

        with patch.object(Path, "cwd", return_value=project_dir), \
             patch.object(ExtensionCatalog, "get_extension_info", return_value={
                 "id": "test-ext",
                 "name": "Test Extension",
                 "version": "2.0.0",
                 "_install_allowed": True,
             }), \
             patch.object(ExtensionCatalog, "download_extension", return_value=zip_path):
            result = runner.invoke(
                app,
                ["extension", "update", "test-ext"],
                input="y\n",
                catch_exceptions=True,
            )

        assert result.exit_code == 1, result.output
        assert "Invalid extension manifest in downloaded archive" in result.output
        assert expected_detail in result.output
        assert "AttributeError" not in result.output
        assert ExtensionManager(project_dir).registry.get("test-ext") == original_registry_entry


class TestExtensionListCLI:
    """Test extension list CLI output format."""

    def test_list_shows_extension_id(self, extension_dir, project_dir):
        """extension list should display the extension ID."""
        from typer.testing import CliRunner
        from unittest.mock import patch
        from specify_cli import app

        runner = CliRunner()

        # Install the extension using the manager
        manager = ExtensionManager(project_dir)
        manager.install_from_directory(extension_dir, "0.1.0", register_commands=False)

        with patch.object(Path, "cwd", return_value=project_dir):
            result = runner.invoke(app, ["extension", "list"])

        assert result.exit_code == 0, result.output
        plain = strip_ansi(result.output)
        # Verify the extension ID is shown in the output
        assert "test-ext" in plain
        # Verify name and version are also shown
        assert "Test Extension" in plain
        assert "1.0.0" in plain


class TestExtensionPriority:
    """Test extension priority-based resolution."""

    def test_list_by_priority_empty(self, temp_dir):
        """Test list_by_priority on empty registry."""
        extensions_dir = temp_dir / "extensions"
        extensions_dir.mkdir()

        registry = ExtensionRegistry(extensions_dir)
        result = registry.list_by_priority()

        assert result == []

    def test_list_by_priority_single(self, temp_dir):
        """Test list_by_priority with single extension."""
        extensions_dir = temp_dir / "extensions"
        extensions_dir.mkdir()

        registry = ExtensionRegistry(extensions_dir)
        registry.add("test-ext", {"version": "1.0.0", "priority": 5})

        result = registry.list_by_priority()

        assert len(result) == 1
        assert result[0][0] == "test-ext"
        assert result[0][1]["priority"] == 5

    def test_list_by_priority_ordering(self, temp_dir):
        """Test list_by_priority returns extensions sorted by priority."""
        extensions_dir = temp_dir / "extensions"
        extensions_dir.mkdir()

        registry = ExtensionRegistry(extensions_dir)
        # Add in non-priority order
        registry.add("ext-low", {"version": "1.0.0", "priority": 20})
        registry.add("ext-high", {"version": "1.0.0", "priority": 1})
        registry.add("ext-mid", {"version": "1.0.0", "priority": 10})

        result = registry.list_by_priority()

        assert len(result) == 3
        # Lower priority number = higher precedence (first)
        assert result[0][0] == "ext-high"
        assert result[1][0] == "ext-mid"
        assert result[2][0] == "ext-low"

    def test_list_by_priority_default(self, temp_dir):
        """Test list_by_priority uses default priority of 10."""
        extensions_dir = temp_dir / "extensions"
        extensions_dir.mkdir()

        registry = ExtensionRegistry(extensions_dir)
        # Add without explicit priority
        registry.add("ext-default", {"version": "1.0.0"})
        registry.add("ext-high", {"version": "1.0.0", "priority": 1})
        registry.add("ext-low", {"version": "1.0.0", "priority": 20})

        result = registry.list_by_priority()

        assert len(result) == 3
        # ext-high (1), ext-default (10), ext-low (20)
        assert result[0][0] == "ext-high"
        assert result[1][0] == "ext-default"
        assert result[2][0] == "ext-low"

    def test_list_by_priority_invalid_priority_defaults(self, temp_dir):
        """Malformed priority values fall back to the default priority."""
        extensions_dir = temp_dir / "extensions"
        extensions_dir.mkdir()

        registry = ExtensionRegistry(extensions_dir)
        registry.add("ext-high", {"version": "1.0.0", "priority": 1})
        registry.data["extensions"]["ext-invalid"] = {
            "version": "1.0.0",
            "priority": "high",
        }
        registry._save()

        result = registry.list_by_priority()

        assert [item[0] for item in result] == ["ext-high", "ext-invalid"]
        assert result[1][1]["priority"] == 10

    def test_list_by_priority_excludes_disabled(self, temp_dir):
        """Test that list_by_priority excludes disabled extensions by default."""
        extensions_dir = temp_dir / "extensions"
        extensions_dir.mkdir()

        registry = ExtensionRegistry(extensions_dir)
        registry.add("ext-enabled", {"version": "1.0.0", "enabled": True, "priority": 5})
        registry.add("ext-disabled", {"version": "1.0.0", "enabled": False, "priority": 1})
        registry.add("ext-default", {"version": "1.0.0", "priority": 10})  # no enabled field = True

        # Default: exclude disabled
        by_priority = registry.list_by_priority()
        ext_ids = [p[0] for p in by_priority]
        assert "ext-enabled" in ext_ids
        assert "ext-default" in ext_ids
        assert "ext-disabled" not in ext_ids

    def test_list_by_priority_includes_disabled_when_requested(self, temp_dir):
        """Test that list_by_priority includes disabled extensions when requested."""
        extensions_dir = temp_dir / "extensions"
        extensions_dir.mkdir()

        registry = ExtensionRegistry(extensions_dir)
        registry.add("ext-enabled", {"version": "1.0.0", "enabled": True, "priority": 5})
        registry.add("ext-disabled", {"version": "1.0.0", "enabled": False, "priority": 1})

        # Include disabled
        by_priority = registry.list_by_priority(include_disabled=True)
        ext_ids = [p[0] for p in by_priority]
        assert "ext-enabled" in ext_ids
        assert "ext-disabled" in ext_ids
        # Disabled ext has lower priority number, so it comes first when included
        assert ext_ids[0] == "ext-disabled"

    def test_install_with_priority(self, extension_dir, project_dir):
        """Test that install_from_directory stores priority."""
        manager = ExtensionManager(project_dir)
        manager.install_from_directory(extension_dir, "0.1.0", register_commands=False, priority=5)

        metadata = manager.registry.get("test-ext")
        assert metadata["priority"] == 5

    def test_install_default_priority(self, extension_dir, project_dir):
        """Test that install_from_directory uses default priority of 10."""
        manager = ExtensionManager(project_dir)
        manager.install_from_directory(extension_dir, "0.1.0", register_commands=False)

        metadata = manager.registry.get("test-ext")
        assert metadata["priority"] == 10

    def test_list_installed_includes_priority(self, extension_dir, project_dir):
        """Test that list_installed includes priority in returned data."""
        manager = ExtensionManager(project_dir)
        manager.install_from_directory(extension_dir, "0.1.0", register_commands=False, priority=3)

        installed = manager.list_installed()

        assert len(installed) == 1
        assert installed[0]["priority"] == 3

    def test_priority_preserved_on_update(self, temp_dir):
        """Test that registry update preserves priority."""
        extensions_dir = temp_dir / "extensions"
        extensions_dir.mkdir()

        registry = ExtensionRegistry(extensions_dir)
        registry.add("test-ext", {"version": "1.0.0", "priority": 5, "enabled": True})

        # Update with new metadata (no priority specified)
        registry.update("test-ext", {"enabled": False})

        updated = registry.get("test-ext")
        assert updated["priority"] == 5  # Preserved
        assert updated["enabled"] is False  # Updated

    def test_corrupted_extension_entry_not_picked_up_as_unregistered(self, project_dir):
        """Corrupted registry entries are still tracked and NOT picked up as unregistered."""
        extensions_dir = project_dir / ".specify" / "extensions"

        valid_dir = extensions_dir / "valid-ext" / "templates"
        valid_dir.mkdir(parents=True)
        (valid_dir / "other-template.md").write_text("# Valid\n")

        broken_dir = extensions_dir / "broken-ext" / "templates"
        broken_dir.mkdir(parents=True)
        (broken_dir / "target-template.md").write_text("# Broken Target\n")

        registry = ExtensionRegistry(extensions_dir)
        registry.add("valid-ext", {"version": "1.0.0", "priority": 10})
        # Corrupt the entry - should still be tracked, not picked up as unregistered
        registry.data["extensions"]["broken-ext"] = "corrupted"
        registry._save()

        from specify_cli.presets import PresetResolver

        resolver = PresetResolver(project_dir)
        # Corrupted extension templates should NOT be resolved
        resolved = resolver.resolve("target-template")
        assert resolved is None

        # Valid extension template should still resolve
        valid_resolved = resolver.resolve("other-template")
        assert valid_resolved is not None
        assert "Valid" in valid_resolved.read_text()


class TestExtensionPriorityCLI:
    """Test extension priority CLI integration."""

    def test_add_with_priority_option(self, extension_dir, project_dir):
        """Test extension add command with --priority option."""
        from typer.testing import CliRunner
        from unittest.mock import patch
        from specify_cli import app

        runner = CliRunner()

        with patch.object(Path, "cwd", return_value=project_dir):
            result = runner.invoke(app, [
                "extension", "add", str(extension_dir), "--dev", "--priority", "3"
            ])

        assert result.exit_code == 0, result.output

        manager = ExtensionManager(project_dir)
        metadata = manager.registry.get("test-ext")
        assert metadata["priority"] == 3

    def test_list_shows_priority(self, extension_dir, project_dir):
        """Test extension list shows priority."""
        from typer.testing import CliRunner
        from unittest.mock import patch
        from specify_cli import app

        runner = CliRunner()

        # Install extension with priority
        manager = ExtensionManager(project_dir)
        manager.install_from_directory(extension_dir, "0.1.0", register_commands=False, priority=7)

        with patch.object(Path, "cwd", return_value=project_dir):
            result = runner.invoke(app, ["extension", "list"])

        assert result.exit_code == 0, result.output
        plain = strip_ansi(result.output)
        assert "Priority: 7" in plain

    def test_set_priority_changes_priority(self, extension_dir, project_dir):
        """Test set-priority command changes extension priority."""
        from typer.testing import CliRunner
        from unittest.mock import patch
        from specify_cli import app

        runner = CliRunner()

        # Install extension with default priority
        manager = ExtensionManager(project_dir)
        manager.install_from_directory(extension_dir, "0.1.0", register_commands=False)

        # Verify default priority
        assert manager.registry.get("test-ext")["priority"] == 10

        with patch.object(Path, "cwd", return_value=project_dir):
            result = runner.invoke(app, ["extension", "set-priority", "test-ext", "5"])

        assert result.exit_code == 0, result.output
        plain = strip_ansi(result.output)
        assert "priority changed: 10 → 5" in plain

        # Reload registry to see updated value
        manager2 = ExtensionManager(project_dir)
        assert manager2.registry.get("test-ext")["priority"] == 5

    def test_set_priority_same_value_no_change(self, extension_dir, project_dir):
        """Test set-priority with same value shows already set message."""
        from typer.testing import CliRunner
        from unittest.mock import patch
        from specify_cli import app

        runner = CliRunner()

        # Install extension with priority 5
        manager = ExtensionManager(project_dir)
        manager.install_from_directory(extension_dir, "0.1.0", register_commands=False, priority=5)

        with patch.object(Path, "cwd", return_value=project_dir):
            result = runner.invoke(app, ["extension", "set-priority", "test-ext", "5"])

        assert result.exit_code == 0, result.output
        plain = strip_ansi(result.output)
        assert "already has priority 5" in plain

    def test_set_priority_invalid_value(self, extension_dir, project_dir):
        """Test set-priority rejects invalid priority values."""
        from typer.testing import CliRunner
        from unittest.mock import patch
        from specify_cli import app

        runner = CliRunner()

        # Install extension
        manager = ExtensionManager(project_dir)
        manager.install_from_directory(extension_dir, "0.1.0", register_commands=False)

        with patch.object(Path, "cwd", return_value=project_dir):
            result = runner.invoke(app, ["extension", "set-priority", "test-ext", "0"])

        assert result.exit_code == 1, result.output
        assert "Priority must be a positive integer" in result.output

    def test_set_priority_not_installed(self, project_dir):
        """Test set-priority fails for non-installed extension."""
        from typer.testing import CliRunner
        from unittest.mock import patch
        from specify_cli import app

        runner = CliRunner()

        # Ensure .specify exists
        (project_dir / ".specify").mkdir(parents=True, exist_ok=True)

        with patch.object(Path, "cwd", return_value=project_dir):
            result = runner.invoke(app, ["extension", "set-priority", "nonexistent", "5"])

        assert result.exit_code == 1, result.output
        assert "not installed" in result.output.lower() or "no extensions installed" in result.output.lower()

    def test_set_priority_by_display_name(self, extension_dir, project_dir):
        """Test set-priority works with extension display name."""
        from typer.testing import CliRunner
        from unittest.mock import patch
        from specify_cli import app

        runner = CliRunner()

        # Install extension
        manager = ExtensionManager(project_dir)
        manager.install_from_directory(extension_dir, "0.1.0", register_commands=False)

        # Use display name "Test Extension" instead of ID "test-ext"
        with patch.object(Path, "cwd", return_value=project_dir):
            result = runner.invoke(app, ["extension", "set-priority", "Test Extension", "3"])

        assert result.exit_code == 0, result.output
        assert "priority changed" in result.output

        # Reload registry to see updated value
        manager2 = ExtensionManager(project_dir)
        assert manager2.registry.get("test-ext")["priority"] == 3


class TestExtensionPriorityBackwardsCompatibility:
    """Test backwards compatibility for extensions installed before priority feature."""

    def test_legacy_extension_without_priority_field(self, temp_dir):
        """Extensions installed before priority feature should default to 10."""
        extensions_dir = temp_dir / "extensions"
        extensions_dir.mkdir()

        # Simulate legacy registry entry without priority field
        registry = ExtensionRegistry(extensions_dir)
        registry.data["extensions"]["legacy-ext"] = {
            "version": "1.0.0",
            "source": "local",
            "enabled": True,
            "installed_at": "2025-01-01T00:00:00Z",
            # No "priority" field - simulates pre-feature extension
        }
        registry._save()

        # Reload registry
        registry2 = ExtensionRegistry(extensions_dir)

        # list_by_priority should use default of 10
        result = registry2.list_by_priority()
        assert len(result) == 1
        assert result[0][0] == "legacy-ext"
        # Priority defaults to 10 and is normalized in returned metadata
        assert result[0][1]["priority"] == 10

    def test_legacy_extension_in_list_installed(self, extension_dir, project_dir):
        """list_installed returns priority=10 for legacy extensions without priority field."""
        manager = ExtensionManager(project_dir)

        # Install extension normally
        manager.install_from_directory(extension_dir, "0.1.0", register_commands=False)

        # Manually remove priority to simulate legacy extension
        ext_data = manager.registry.data["extensions"]["test-ext"]
        del ext_data["priority"]
        manager.registry._save()

        # list_installed should still return priority=10
        installed = manager.list_installed()
        assert len(installed) == 1
        assert installed[0]["priority"] == 10

    def test_mixed_legacy_and_new_extensions_ordering(self, temp_dir):
        """Legacy extensions (no priority) sort with default=10 among prioritized extensions."""
        extensions_dir = temp_dir / "extensions"
        extensions_dir.mkdir()

        registry = ExtensionRegistry(extensions_dir)

        # Add extension with explicit priority=5
        registry.add("ext-with-priority", {"version": "1.0.0", "priority": 5})

        # Add legacy extension without priority (manually)
        registry.data["extensions"]["legacy-ext"] = {
            "version": "1.0.0",
            "source": "local",
            "enabled": True,
            # No priority field
        }
        registry._save()

        # Add extension with priority=15
        registry.add("ext-low-priority", {"version": "1.0.0", "priority": 15})

        # Reload and check ordering
        registry2 = ExtensionRegistry(extensions_dir)
        result = registry2.list_by_priority()

        assert len(result) == 3
        # Order: ext-with-priority (5), legacy-ext (defaults to 10), ext-low-priority (15)
        assert result[0][0] == "ext-with-priority"
        assert result[1][0] == "legacy-ext"
        assert result[2][0] == "ext-low-priority"


class _StubManifest(ExtensionManifest):
    """ExtensionManifest stub for HookExecutor tests.

    Subclasses the real manifest so it satisfies ``register_hooks``'s type
    while bypassing the file-based parsing/validation pipeline. The inherited
    ``id`` and ``hooks`` properties read from ``data``, so populating ``data``
    is enough.
    """

    def __init__(self, ext_id: str, hooks: dict):
        self.data = {"extension": {"id": ext_id}, "hooks": hooks}


class TestHookExecutorRegistration:
    """Tests for HookExecutor.register_hooks / get_hooks_for_event with
    multi-entry hook events and per-entry priority ordering."""

    def test_register_hooks_single_mapping_back_compat(self, project_dir):
        """Single-mapping form continues to register exactly one entry with
        default priority."""
        executor = HookExecutor(project_dir)
        executor.register_hooks(
            _StubManifest("ext-a", {"after_tasks": {"command": "speckit.ext-a.go"}})
        )

        config = executor.get_project_config()
        entries = config["hooks"]["after_tasks"]
        assert len(entries) == 1
        assert entries[0]["extension"] == "ext-a"
        assert entries[0]["command"] == "speckit.ext-a.go"
        assert entries[0]["priority"] == DEFAULT_HOOK_PRIORITY

    def test_register_hooks_multiple_entries_same_event(self, project_dir):
        """A list of mappings registers each entry under the same event."""
        executor = HookExecutor(project_dir)
        executor.register_hooks(
            _StubManifest(
                "ext-a",
                {
                    "after_tasks": [
                        {"command": "speckit.ext-a.first", "description": "1st"},
                        {"command": "speckit.ext-a.second", "description": "2nd"},
                    ]
                },
            )
        )

        entries = executor.get_project_config()["hooks"]["after_tasks"]
        assert len(entries) == 2
        assert [e["command"] for e in entries] == [
            "speckit.ext-a.first",
            "speckit.ext-a.second",
        ]
        assert all(e["extension"] == "ext-a" for e in entries)

    def test_register_hooks_dedup_on_extension_and_command(self, project_dir):
        """Re-registering the same (extension, command) updates in place
        rather than appending a duplicate entry."""
        executor = HookExecutor(project_dir)
        manifest = _StubManifest(
            "ext-a",
            {
                "after_tasks": [
                    {"command": "speckit.ext-a.first", "description": "v1"},
                    {"command": "speckit.ext-a.second", "description": "v1"},
                ]
            },
        )
        executor.register_hooks(manifest)

        manifest.hooks["after_tasks"][0]["description"] = "v2"
        executor.register_hooks(manifest)

        entries = executor.get_project_config()["hooks"]["after_tasks"]
        assert len(entries) == 2
        first = next(e for e in entries if e["command"] == "speckit.ext-a.first")
        assert first["description"] == "v2"

    def test_register_hooks_shape_change_removes_orphans(self, project_dir):
        """Reinstalling with a shorter hook shape (list → single mapping, or a
        shrunk list) purges the dropped commands instead of leaving orphans."""
        executor = HookExecutor(project_dir)
        executor.register_hooks(
            _StubManifest(
                "ext-a",
                {
                    "after_tasks": [
                        {"command": "speckit.ext-a.first"},
                        {"command": "speckit.ext-a.second"},
                    ]
                },
            )
        )

        executor.register_hooks(
            _StubManifest("ext-a", {"after_tasks": {"command": "speckit.ext-a.first"}})
        )

        entries = executor.get_project_config()["hooks"]["after_tasks"]
        assert [e["command"] for e in entries] == ["speckit.ext-a.first"]

    def test_register_hooks_single_to_list_reinstall_adds_entries(self, project_dir):
        """Reinstalling a single-mapping hook as a list adds the new entries."""
        executor = HookExecutor(project_dir)
        executor.register_hooks(
            _StubManifest("ext-a", {"after_tasks": {"command": "speckit.ext-a.first"}})
        )
        executor.register_hooks(
            _StubManifest(
                "ext-a",
                {
                    "after_tasks": [
                        {"command": "speckit.ext-a.first"},
                        {"command": "speckit.ext-a.second"},
                    ]
                },
            )
        )

        entries = executor.get_project_config()["hooks"]["after_tasks"]
        assert [e["command"] for e in entries] == [
            "speckit.ext-a.first",
            "speckit.ext-a.second",
        ]

    def test_register_hooks_skips_entry_without_command(self, project_dir):
        """An entry lacking a command is skipped (defensive; validated
        manifests never reach this state)."""
        executor = HookExecutor(project_dir)
        executor.register_hooks(
            _StubManifest(
                "ext-a",
                {
                    "after_tasks": [
                        {"command": "speckit.ext-a.go"},
                        {"optional": True},
                    ]
                },
            )
        )

        entries = executor.get_project_config()["hooks"]["after_tasks"]
        assert [e["command"] for e in entries] == ["speckit.ext-a.go"]

    def test_register_hooks_skips_non_dict_entry(self, project_dir):
        """A non-dict entry in a hook list is skipped rather than crashing
        (defensive; validated manifests never reach this state)."""
        executor = HookExecutor(project_dir)
        executor.register_hooks(
            _StubManifest(
                "ext-a",
                {"after_tasks": [{"command": "speckit.ext-a.go"}, "not-a-mapping"]},
            )
        )

        entries = executor.get_project_config()["hooks"]["after_tasks"]
        assert [e["command"] for e in entries] == ["speckit.ext-a.go"]

    def test_register_hooks_purges_dropped_event_orphans(self, project_dir):
        """Re-registering without an event it previously declared purges this
        extension's entries from that event, scoped to this extension."""
        executor = HookExecutor(project_dir)
        executor.register_hooks(
            _StubManifest(
                "ext-a",
                {
                    "after_tasks": {"command": "speckit.ext-a.tasks"},
                    "after_plan": {"command": "speckit.ext-a.plan"},
                    "after_implement": {"command": "speckit.ext-a.impl"},
                },
            )
        )
        executor.register_hooks(
            _StubManifest("ext-b", {"after_plan": {"command": "speckit.ext-b.plan"}})
        )

        executor.register_hooks(
            _StubManifest("ext-a", {"after_tasks": {"command": "speckit.ext-a.tasks"}})
        )

        hooks = executor.get_project_config()["hooks"]
        assert [e["command"] for e in hooks["after_tasks"]] == ["speckit.ext-a.tasks"]
        assert [e["command"] for e in hooks["after_plan"]] == ["speckit.ext-b.plan"]
        assert "after_implement" not in hooks

    def test_register_hooks_dropping_all_hooks_purges_orphans(self, project_dir):
        """Reinstalling with an empty hooks mapping still purges this
        extension's entries, scoped to this extension."""
        executor = HookExecutor(project_dir)
        executor.register_hooks(
            _StubManifest("ext-a", {"after_tasks": {"command": "speckit.ext-a.go"}})
        )
        executor.register_hooks(
            _StubManifest("ext-b", {"after_tasks": {"command": "speckit.ext-b.go"}})
        )

        executor.register_hooks(_StubManifest("ext-a", {}))

        hooks = executor.get_project_config()["hooks"]
        assert [e["command"] for e in hooks["after_tasks"]] == ["speckit.ext-b.go"]

    def test_register_hooks_empty_hooks_purge_survives_corrupt_entry(self, project_dir):
        """A corrupt non-dict entry already on disk does not break the
        empty-hooks orphan purge; it is dropped and valid entries survive."""
        executor = HookExecutor(project_dir)
        executor.register_hooks(
            _StubManifest("ext-a", {"after_tasks": {"command": "speckit.ext-a.go"}})
        )
        executor.register_hooks(
            _StubManifest("ext-b", {"after_tasks": {"command": "speckit.ext-b.go"}})
        )
        config = executor.get_project_config()
        config["hooks"]["after_tasks"].append("corrupt-non-dict-entry")
        executor.save_project_config(config)

        executor.register_hooks(_StubManifest("ext-a", {}))

        hooks = executor.get_project_config()["hooks"]
        assert [e["command"] for e in hooks["after_tasks"]] == ["speckit.ext-b.go"]

    def test_register_hooks_duplicate_command_moves_to_end(self, project_dir):
        """A command repeated in one manifest keeps the last value and the last
        insertion position, so equal-priority tie order is 'last wins'."""
        executor = HookExecutor(project_dir)
        executor.register_hooks(
            _StubManifest(
                "ext-a",
                {
                    "after_tasks": [
                        {"command": "speckit.ext-a.dup", "description": "first"},
                        {"command": "speckit.ext-a.other"},
                        {"command": "speckit.ext-a.dup", "description": "last"},
                    ]
                },
            )
        )

        entries = executor.get_project_config()["hooks"]["after_tasks"]
        assert [e["command"] for e in entries] == [
            "speckit.ext-a.other",
            "speckit.ext-a.dup",
        ]
        assert entries[-1]["description"] == "last"

    def test_register_hooks_preserves_other_extensions(self, project_dir):
        """Re-registering one extension must not disturb another extension's
        entries on the same event."""
        executor = HookExecutor(project_dir)
        executor.register_hooks(
            _StubManifest("ext-a", {"after_tasks": {"command": "speckit.ext-a.go"}})
        )
        executor.register_hooks(
            _StubManifest("ext-b", {"after_tasks": {"command": "speckit.ext-b.go"}})
        )

        executor.register_hooks(
            _StubManifest("ext-a", {"after_tasks": {"command": "speckit.ext-a.go"}})
        )

        entries = executor.get_project_config()["hooks"]["after_tasks"]
        assert sorted(e["extension"] for e in entries) == ["ext-a", "ext-b"]

    def test_get_hooks_for_event_sorts_by_priority(self, project_dir):
        """Returned entries are sorted by priority ascending; equal priorities
        preserve insertion order via stable sort."""
        executor = HookExecutor(project_dir)
        executor.register_hooks(
            _StubManifest(
                "ext-a",
                {
                    "after_tasks": [
                        {"command": "speckit.ext-a.mid", "priority": 10},
                        {"command": "speckit.ext-a.first", "priority": 1},
                        {"command": "speckit.ext-a.late", "priority": 20},
                        {"command": "speckit.ext-a.mid-tied", "priority": 10},
                    ]
                },
            )
        )

        ordered = executor.get_hooks_for_event("after_tasks")
        assert [e["command"] for e in ordered] == [
            "speckit.ext-a.first",
            "speckit.ext-a.mid",
            "speckit.ext-a.mid-tied",
            "speckit.ext-a.late",
        ]

    def test_get_hooks_for_event_orders_across_extensions(self, project_dir):
        """Priority controls execution order across extensions regardless of
        install order (Issue #2378 use case)."""
        executor = HookExecutor(project_dir)
        executor.register_hooks(
            _StubManifest(
                "ext-report",
                {"after_plan": {"command": "speckit.ext-report.run", "priority": 20}},
            )
        )
        executor.register_hooks(
            _StubManifest(
                "ext-verify",
                {"after_plan": {"command": "speckit.ext-verify.run", "priority": 5}},
            )
        )

        ordered = executor.get_hooks_for_event("after_plan")
        assert [e["command"] for e in ordered] == [
            "speckit.ext-verify.run",
            "speckit.ext-report.run",
        ]

    def test_get_hooks_for_event_treats_missing_priority_as_default(self, project_dir):
        """Entries persisted before priority was introduced should be sorted
        as if their priority equaled DEFAULT_HOOK_PRIORITY."""
        executor = HookExecutor(project_dir)
        # Legacy on-disk entry with no priority key.
        # register_hooks now always sets one, so write this state directly.
        executor.save_project_config({
            "installed": [],
            "settings": {"auto_execute_hooks": True},
            "hooks": {
                "after_tasks": [
                    {
                        "extension": "legacy",
                        "command": "speckit.legacy.go",
                        "enabled": True,
                    },
                    {
                        "extension": "newer",
                        "command": "speckit.newer.first",
                        "enabled": True,
                        "priority": 1,
                    },
                ]
            },
        })

        ordered = executor.get_hooks_for_event("after_tasks")
        assert [e["command"] for e in ordered] == [
            "speckit.newer.first",
            "speckit.legacy.go",
        ]

    def test_get_hooks_for_event_tolerates_corrupted_priority(self, project_dir):
        """A corrupted on-disk ``priority`` (non-numeric, None, or < 1) is
        normalized to the default instead of raising during sort."""
        executor = HookExecutor(project_dir)
        executor.save_project_config({
            "installed": [],
            "settings": {"auto_execute_hooks": True},
            "hooks": {
                "after_tasks": [
                    {
                        "extension": "corrupt",
                        "command": "speckit.corrupt.go",
                        "enabled": True,
                        "priority": "not-a-number",
                    },
                    {
                        "extension": "early",
                        "command": "speckit.early.go",
                        "enabled": True,
                        "priority": 1,
                    },
                ]
            },
        })

        ordered = executor.get_hooks_for_event("after_tasks")
        assert [e["command"] for e in ordered] == [
            "speckit.early.go",
            "speckit.corrupt.go",
        ]

    def test_unregister_hooks_removes_all_extension_entries(self, project_dir):
        """unregister_hooks removes every entry for the extension regardless
        of how many were registered to a given event."""
        executor = HookExecutor(project_dir)
        executor.register_hooks(
            _StubManifest(
                "ext-a",
                {
                    "after_tasks": [
                        {"command": "speckit.ext-a.first"},
                        {"command": "speckit.ext-a.second"},
                    ]
                },
            )
        )
        executor.register_hooks(
            _StubManifest("ext-b", {"after_tasks": {"command": "speckit.ext-b.solo"}})
        )

        executor.unregister_hooks("ext-a")

        entries = executor.get_project_config()["hooks"].get("after_tasks", [])
        assert [e["extension"] for e in entries] == ["ext-b"]


class TestHookInvocationRendering:
    """Test hook invocation formatting for different agent modes."""

    def test_kimi_hooks_render_skill_invocation(self, project_dir):
        """Kimi projects should render /skill:speckit-* invocations."""
        init_options = project_dir / ".specify" / "init-options.json"
        init_options.parent.mkdir(parents=True, exist_ok=True)
        init_options.write_text(json.dumps({"ai": "kimi", "ai_skills": False}))

        hook_executor = HookExecutor(project_dir)
        message = hook_executor.format_hook_message(
            "before_plan",
            [
                {
                    "extension": "test-ext",
                    "command": "speckit.plan",
                    "optional": False,
                }
            ],
        )

        assert "Executing: `/skill:speckit-plan`" in message
        assert "EXECUTE_COMMAND: speckit.plan" in message
        assert "EXECUTE_COMMAND_INVOCATION: /skill:speckit-plan" in message

    def test_codex_hooks_render_dollar_skill_invocation(self, project_dir):
        """Codex projects with skills mode should render $speckit-* invocations."""
        init_options = project_dir / ".specify" / "init-options.json"
        init_options.parent.mkdir(parents=True, exist_ok=True)
        init_options.write_text(json.dumps({"ai": "codex", "ai_skills": True}))

        hook_executor = HookExecutor(project_dir)
        execution = hook_executor.execute_hook(
            {
                "extension": "test-ext",
                "command": "speckit.tasks",
                "optional": False,
            }
        )

        assert execution["command"] == "speckit.tasks"
        assert execution["invocation"] == "$speckit-tasks"

    def test_zcode_hooks_render_dollar_skill_invocation(self, project_dir):
        """ZCode projects with skills mode should render $speckit-* invocations."""
        init_options = project_dir / ".specify" / "init-options.json"
        init_options.parent.mkdir(parents=True, exist_ok=True)
        init_options.write_text(json.dumps({"ai": "zcode", "ai_skills": True}))

        hook_executor = HookExecutor(project_dir)
        execution = hook_executor.execute_hook(
            {
                "extension": "test-ext",
                "command": "speckit.tasks",
                "optional": False,
            }
        )

        assert execution["command"] == "speckit.tasks"
        assert execution["invocation"] == "$speckit-tasks"

    def test_non_boolean_ai_skills_keeps_default_hook_invocation(self, project_dir):
        """Corrupted truthy ai_skills values should not enable skill invocation."""
        init_options = project_dir / ".specify" / "init-options.json"
        init_options.parent.mkdir(parents=True, exist_ok=True)
        init_options.write_text(
            json.dumps({"ai": "codex", "ai_skills": "false"}), encoding="utf-8"
        )

        hook_executor = HookExecutor(project_dir)
        execution = hook_executor.execute_hook(
            {
                "extension": "test-ext",
                "command": "speckit.tasks",
                "optional": False,
            }
        )

        assert execution["command"] == "speckit.tasks"
        assert execution["invocation"] == "/speckit.tasks"

    def test_cline_hooks_render_hyphenated_invocation(self, project_dir):
        """Cline projects should render /speckit-* invocations."""
        init_options = project_dir / ".specify" / "init-options.json"
        init_options.parent.mkdir(parents=True, exist_ok=True)
        init_options.write_text(json.dumps({"ai": "cline"}))

        hook_executor = HookExecutor(project_dir)
        execution = hook_executor.execute_hook(
            {
                "extension": "test-ext",
                "command": "speckit.tasks",
                "optional": False,
            }
        )

        assert execution["command"] == "speckit.tasks"
        assert execution["invocation"] == "/speckit-tasks"

    def test_cline_hooks_render_extension_command(self, project_dir):
        """Cline projects should render /speckit-my-ext-cmd for extension hooks."""
        init_options = project_dir / ".specify" / "init-options.json"
        init_options.parent.mkdir(parents=True, exist_ok=True)
        init_options.write_text(json.dumps({"ai": "cline"}))

        hook_executor = HookExecutor(project_dir)
        # Test with a non-speckit. command
        execution = hook_executor.execute_hook(
            {
                "extension": "test-ext",
                "command": "my-extension.do-something",
                "optional": False,
            }
        )

        assert execution["command"] == "my-extension.do-something"
        assert execution["invocation"] == "/speckit-my-extension-do-something"

    def test_non_skill_command_keeps_slash_invocation(self, project_dir):
        """Custom hook commands should keep slash invocation style."""
        init_options = project_dir / ".specify" / "init-options.json"
        init_options.parent.mkdir(parents=True, exist_ok=True)
        init_options.write_text(json.dumps({"ai": "kimi", "ai_skills": False}))

        hook_executor = HookExecutor(project_dir)
        message = hook_executor.format_hook_message(
            "before_tasks",
            [
                {
                    "extension": "test-ext",
                    "command": "pre_tasks_test",
                    "optional": False,
                }
            ],
        )

        assert "Executing: `/pre_tasks_test`" in message
        assert "EXECUTE_COMMAND: pre_tasks_test" in message
        assert "EXECUTE_COMMAND_INVOCATION: /pre_tasks_test" in message

    def test_extension_command_uses_hyphenated_skill_invocation(self, project_dir):
        """Multi-segment extension command ids should map to hyphenated skills."""
        init_options = project_dir / ".specify" / "init-options.json"
        init_options.parent.mkdir(parents=True, exist_ok=True)
        init_options.write_text(json.dumps({"ai": "kimi", "ai_skills": False}))

        hook_executor = HookExecutor(project_dir)
        message = hook_executor.format_hook_message(
            "after_tasks",
            [
                {
                    "extension": "test-ext",
                    "command": "speckit.test-ext.hello",
                    "optional": False,
                }
            ],
        )

        assert "Executing: `/skill:speckit-test-ext-hello`" in message
        assert "EXECUTE_COMMAND: speckit.test-ext.hello" in message
        assert "EXECUTE_COMMAND_INVOCATION: /skill:speckit-test-ext-hello" in message

    def test_hook_executor_caches_init_options_lookup(self, project_dir, monkeypatch):
        """Init options should be loaded once per executor instance."""
        calls = {"count": 0}

        def fake_load_init_options(_project_root):
            calls["count"] += 1
            return {"ai": "kimi", "ai_skills": False}

        monkeypatch.setattr("specify_cli.load_init_options", fake_load_init_options)

        hook_executor = HookExecutor(project_dir)
        assert hook_executor._render_hook_invocation("speckit.plan") == "/skill:speckit-plan"
        assert hook_executor._render_hook_invocation("speckit.tasks") == "/skill:speckit-tasks"
        assert calls["count"] == 1

    def test_hook_message_falls_back_when_invocation_is_empty(self, project_dir):
        """Hook messages should still render actionable command placeholders."""
        init_options = project_dir / ".specify" / "init-options.json"
        init_options.parent.mkdir(parents=True, exist_ok=True)
        init_options.write_text(json.dumps({"ai": "kimi", "ai_skills": False}))

        hook_executor = HookExecutor(project_dir)
        message = hook_executor.format_hook_message(
            "after_tasks",
            [
                {
                    "extension": "test-ext",
                    "command": None,
                    "optional": False,
                }
            ],
        )

        assert "Executing: `/<missing command>`" in message
        assert "EXECUTE_COMMAND: <missing command>" in message
        assert "EXECUTE_COMMAND_INVOCATION: /<missing command>" in message


class TestExtensionRemoveCLI:
    """CLI tests for `specify extension remove` confirmation prompt wording."""

    def _install_ext(self, project_dir, ext_dir):
        """Install extension and return the manager."""
        manager = ExtensionManager(project_dir)
        manager.install_from_directory(ext_dir, "0.1.0", register_commands=False)
        return manager

    def test_remove_confirmation_singular_command(self, tmp_path, extension_dir):
        """Confirmation prompt should say '1 command' (singular) when one command registered."""
        from typer.testing import CliRunner
        from unittest.mock import patch
        from specify_cli import app

        project_dir = tmp_path / "project"
        project_dir.mkdir()
        (project_dir / ".specify").mkdir()

        manager = self._install_ext(project_dir, extension_dir)
        # Inject registered_commands with 1 entry so cmd_count == 1
        manager.registry.update("test-ext", {"registered_commands": {"claude": ["speckit.test-ext.hello"]}})

        runner = CliRunner()
        with patch.object(Path, "cwd", return_value=project_dir):
            result = runner.invoke(
                app, ["extension", "remove", "test-ext"], input="n\n", catch_exceptions=False
            )

        assert "1 command" in result.output
        assert "1 commands" not in result.output

    def test_remove_confirmation_plural_commands(self, tmp_path, extension_dir):
        """Confirmation prompt should say '2 commands' (plural) when two commands registered."""
        from typer.testing import CliRunner
        from unittest.mock import patch
        from specify_cli import app

        project_dir = tmp_path / "project"
        project_dir.mkdir()
        (project_dir / ".specify").mkdir()

        manager = self._install_ext(project_dir, extension_dir)
        # Inject registered_commands with 2 entries so cmd_count == 2
        manager.registry.update("test-ext", {"registered_commands": {"claude": ["speckit.test-ext.hello", "speckit.test-ext.run"]}})

        runner = CliRunner()
        with patch.object(Path, "cwd", return_value=project_dir):
            result = runner.invoke(
                app, ["extension", "remove", "test-ext"], input="n\n", catch_exceptions=False
            )

        assert "2 commands" in result.output

    def test_remove_output_escapes_extension_id_markup(self, tmp_path):
        """Removal paths and reinstall hints must not parse extension IDs as markup."""
        from types import SimpleNamespace
        from typer.testing import CliRunner
        from unittest.mock import patch
        from specify_cli import app

        project_dir = tmp_path / "project"
        project_dir.mkdir()
        (project_dir / ".specify").mkdir()

        extension_id = "[red]bad[/red]"
        installed = [
            {
                "id": extension_id,
                "name": "Bad Extension",
                "version": "1.0.0",
                "description": "Test extension",
                "enabled": True,
            }
        ]

        runner = CliRunner()
        with patch.object(Path, "cwd", return_value=project_dir), \
             patch.object(ExtensionManager, "list_installed", return_value=installed), \
             patch.object(ExtensionManager, "get_extension", return_value=SimpleNamespace(commands=[])), \
             patch.object(ExtensionRegistry, "get", return_value={"registered_commands": {}, "registered_skills": []}), \
             patch.object(ExtensionManager, "remove", return_value=True):
            result = runner.invoke(
                app,
                ["extension", "remove", extension_id, "--force"],
                catch_exceptions=True,
            )

        assert result.exit_code == 0, result.output
        assert ".specify/extensions/.backup/[red]bad[/red]/" in result.output
        assert "specify extension add [red]bad[/red]" in result.output


class TestExtensionStateCLI:
    """CLI tests for installed extension state commands."""

    def test_enable_registry_error_escapes_extension_id_markup(self, tmp_path):
        """Registry-corruption errors should render extension IDs literally."""
        from typer.testing import CliRunner
        from unittest.mock import patch
        from specify_cli import app

        project_dir = tmp_path / "project"
        project_dir.mkdir()
        (project_dir / ".specify").mkdir()

        extension_id = "[red]bad[/red]"
        installed = [
            {
                "id": extension_id,
                "name": "Bad Extension",
                "version": "1.0.0",
                "description": "Test extension",
                "enabled": False,
            }
        ]

        runner = CliRunner()
        with patch.object(Path, "cwd", return_value=project_dir), \
             patch.object(ExtensionManager, "list_installed", return_value=installed), \
             patch.object(ExtensionRegistry, "get", return_value=None):
            result = runner.invoke(
                app,
                ["extension", "enable", extension_id],
                catch_exceptions=True,
            )

        assert result.exit_code == 1, result.output
        assert "Extension '[red]bad[/red]' not found in registry" in result.output

    def test_disable_reenable_hint_escapes_extension_id_markup(self, tmp_path):
        """Disable success hints should not parse extension IDs as markup."""
        from typer.testing import CliRunner
        from unittest.mock import patch
        from specify_cli import app

        project_dir = tmp_path / "project"
        project_dir.mkdir()
        (project_dir / ".specify").mkdir()

        extension_id = "[red]bad[/red]"
        installed = [
            {
                "id": extension_id,
                "name": "Bad Extension",
                "version": "1.0.0",
                "description": "Test extension",
                "enabled": True,
            }
        ]

        runner = CliRunner()
        with patch.object(Path, "cwd", return_value=project_dir), \
             patch.object(ExtensionManager, "list_installed", return_value=installed), \
             patch.object(ExtensionRegistry, "get", return_value={"enabled": True}), \
             patch.object(ExtensionRegistry, "update", return_value=None), \
             patch.object(HookExecutor, "get_project_config", return_value={}):
            result = runner.invoke(
                app,
                ["extension", "disable", extension_id],
                catch_exceptions=True,
            )

        assert result.exit_code == 0, result.output
        assert "specify extension enable [red]bad[/red]" in result.output


class TestClineExtensionHyphenation:
    """Test that Cline integration uses hyphenated commands and frontmatter references."""

    def _setup_mock_extension(self, tmp_path, ai_name):
        import yaml
        import json

        # 1. Setup mock project
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        (project_dir / ".specify").mkdir()

        init_options = project_dir / ".specify" / "init-options.json"
        init_options.write_text(json.dumps({"ai": ai_name}), encoding="utf-8")

        if ai_name == "cline":
            commands_dest_dir = project_dir / ".clinerules" / "workflows"
        else:
            commands_dest_dir = project_dir / ".agents" / "commands"
        commands_dest_dir.mkdir(parents=True, exist_ok=True)

        # 2. Setup mock extension directory
        ext_dir = tmp_path / "mock-ext"
        ext_dir.mkdir()

        manifest_data = {
            "schema_version": "1.0",
            "extension": {
                "id": "mock-ext",
                "name": "Mock Extension",
                "version": "1.0.0",
                "description": f"Mock extension for {ai_name} tests",
                "author": "Tester",
                "repository": "https://github.com/test/mock-ext",
                "license": "MIT",
            },
            "requires": {
                "speckit_version": ">=0.1.0",
            },
            "provides": {
                "commands": [
                    {
                        "name": "speckit.mock-ext.hello",
                        "file": "commands/hello.md",
                        "description": "Test hello command",
                        "aliases": ["speckit.mock-ext.greet"]
                    }
                ]
            }
        }

        with open(ext_dir / "extension.yml", "w", encoding="utf-8") as f:
            yaml.dump(manifest_data, f)

        commands_dir = ext_dir / "commands"
        commands_dir.mkdir()

        # Command file with dotted speckit references in frontmatter and body
        cmd_content = """---
description: "Test hello command"
agent: speckit.tasks
handoffs:
  - agent: speckit.iterate.start
    message: "Hand off to start"
---

# Test Hello Command

Please refer to speckit.mock-ext.greet for instructions.
$ARGUMENTS
"""
        (commands_dir / "hello.md").write_text(cmd_content, encoding="utf-8")

        return project_dir, ext_dir, commands_dest_dir

    def test_cline_extension_hyphenation(self, tmp_path):
        from typer.testing import CliRunner
        from unittest.mock import patch
        from specify_cli import app
        from specify_cli.agents import CommandRegistrar

        project_dir, ext_dir, cline_workflows_dir = self._setup_mock_extension(tmp_path, "cline")

        # 3. Run specify extension add
        runner = CliRunner()
        with patch.object(Path, "cwd", return_value=project_dir):
            result = runner.invoke(
                app, ["extension", "add", str(ext_dir), "--dev"], catch_exceptions=False
            )

        # Verify CLI printed hyphenated commands
        # Note: We assert that the primary command 'speckit-mock-ext-hello' is printed,
        # but we do not assert that the alias 'speckit-mock-ext-greet' is printed in the console
        # because manifest.commands only lists primary commands.
        assert "speckit-mock-ext-hello" in result.output
        assert "speckit.mock-ext.hello" not in result.output

        # Verify on-disk command names are hyphenated
        hello_file = cline_workflows_dir / "speckit-mock-ext-hello.md"
        greet_file = cline_workflows_dir / "speckit-mock-ext-greet.md"

        assert hello_file.exists()
        assert greet_file.exists()

        # Verify frontmatter in the generated files is recursively hyphenated
        hello_text = hello_file.read_text(encoding="utf-8")
        hello_fm, hello_body = CommandRegistrar.parse_frontmatter(hello_text)
        assert hello_fm["agent"] == "speckit-tasks"
        assert hello_fm["handoffs"][0]["agent"] == "speckit-iterate-start"

        # Verify body references are hyphenated for Cline
        assert "speckit-mock-ext-greet" in hello_body
        assert "speckit.mock-ext.greet" not in hello_body

    def test_non_cline_extension_no_hyphenation(self, tmp_path):
        from typer.testing import CliRunner
        from unittest.mock import patch
        from specify_cli import app
        from specify_cli.agents import CommandRegistrar

        project_dir, ext_dir, claude_commands_dir = self._setup_mock_extension(tmp_path, "claude")

        # 3. Run specify extension add
        runner = CliRunner()
        with patch.object(Path, "cwd", return_value=project_dir):
            result = runner.invoke(
                app, ["extension", "add", str(ext_dir), "--dev"], catch_exceptions=False
            )

        # Verify CLI printed dotted commands
        # Note: We assert that the primary command 'speckit.mock-ext.hello' is printed,
        # but we do not assert that the alias 'speckit.mock-ext.greet' is printed in the console
        # because manifest.commands only lists primary commands.
        assert "speckit.mock-ext.hello" in result.output
        assert "speckit-mock-ext-hello" not in result.output

        # Verify on-disk command names are dotted
        hello_file = claude_commands_dir / "speckit.mock-ext.hello.md"
        greet_file = claude_commands_dir / "speckit.mock-ext.greet.md"

        assert hello_file.exists()
        assert greet_file.exists()

        # Verify frontmatter references are still dotted
        hello_text = hello_file.read_text(encoding="utf-8")
        hello_fm, hello_body = CommandRegistrar.parse_frontmatter(hello_text)
        assert hello_fm["agent"] == "speckit.tasks"
        assert hello_fm["handoffs"][0]["agent"] == "speckit.iterate.start"

        # Verify body references are still dotted for non-Cline
        assert "speckit.mock-ext.greet" in hello_body
        assert "speckit-mock-ext-greet" not in hello_body


class TestExtensionForceCLI:
    """CLI tests for `specify extension add --dev --force`."""

    def _create_minimal_extension(self, base_dir: str | Path, ext_id: str = "test-ext") -> Path:
        """Create a minimal extension directory with manifest."""
        import yaml

        ext_dir = Path(base_dir) / ext_id
        ext_dir.mkdir(parents=True, exist_ok=True)
        (ext_dir / "commands").mkdir()

        manifest = {
            "schema_version": "1.0",
            "extension": {
                "id": ext_id,
                "name": "Test Extension",
                "version": "1.0.0",
                "description": "Test",
            },
            "requires": {"speckit_version": ">=0.1.0"},
            "provides": {
                "commands": [
                    {
                        "name": f"speckit.{ext_id}.hello",
                        "file": "commands/hello.md",
                        "description": "Test command",
                    }
                ]
            },
        }

        (ext_dir / "extension.yml").write_text(yaml.dump(manifest))
        (ext_dir / "commands" / "hello.md").write_text(
            "---\ndescription: Test\n---\n\nHello $ARGUMENTS\n"
        )
        return ext_dir

    def test_add_dev_force_reinstall(self, tmp_path):
        """extension add --dev --force should reinstall without error."""
        from typer.testing import CliRunner
        from unittest.mock import patch
        from specify_cli import app

        project_dir = tmp_path / "project"
        project_dir.mkdir()
        (project_dir / ".specify").mkdir()

        ext_src = self._create_minimal_extension(tmp_path)

        runner = CliRunner()
        with patch.object(Path, "cwd", return_value=project_dir):
            # First install
            result1 = runner.invoke(
                app, ["extension", "add", str(ext_src), "--dev"], catch_exceptions=False
            )
            assert result1.exit_code == 0, strip_ansi(result1.output)
            assert "installed" in strip_ansi(result1.output)

            # Force reinstall
            result2 = runner.invoke(
                app, ["extension", "add", str(ext_src), "--dev", "--force"], catch_exceptions=False
            )
            assert result2.exit_code == 0, strip_ansi(result2.output)
            assert "installed" in strip_ansi(result2.output)


def test_extension_wrapper_resolves_ghes_asset_when_host_configured(tmp_path, monkeypatch):
    """End-to-end wiring: auth.json github host → GHES asset resolution."""
    from specify_cli.authentication import http as _auth_http
    from specify_cli.authentication.config import AuthConfigEntry
    from specify_cli.extensions import ExtensionCatalog

    monkeypatch.setattr(_auth_http, "_config_override", [
        AuthConfigEntry(hosts=("ghes.example",), provider="github",
                        auth="bearer", token="t"),
    ])
    catalog = ExtensionCatalog(tmp_path)

    captured = []

    @contextmanager
    def fake_open(url, timeout=None, extra_headers=None):
        captured.append(url)
        resp = MagicMock()
        resp.read.return_value = json.dumps({
            "assets": [{"name": "ext.zip",
                        "url": "https://ghes.example/api/v3/repos/o/r/releases/assets/7"}]
        }).encode()
        yield resp

    monkeypatch.setattr(catalog, "_open_url", fake_open)

    resolved = catalog._resolve_github_release_asset_api_url(
        "https://ghes.example/o/r/releases/download/v1/ext.zip"
    )
    assert resolved == "https://ghes.example/api/v3/repos/o/r/releases/assets/7"
    assert captured == ["https://ghes.example/api/v3/repos/o/r/releases/tags/v1"]
