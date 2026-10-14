"""Tests for preset layer resolution and composition in specify_cli.presets._resolver."""

import json
import re
import warnings
from pathlib import Path

import pytest
import yaml

from specify_cli.extensions import ExtensionRegistry
from specify_cli.presets import (
    PresetManager,
    PresetManifest,
    PresetRegistry,
    PresetResolver,
    PresetValidationError,
)
from tests.specify_cli.presets._helpers import (
    CORE_TEMPLATE_NAMES,
    install_selector_fixture,
    install_self_test_preset,
    write_command_declarations,
    write_selector_contract_preset,
    write_selector_preset,
)


class TestPresetResolver:
    """Test PresetResolver priority stack."""

    def test_resolve_core_template(self, project_dir):
        """Test resolving a core template."""
        resolver = PresetResolver(project_dir)
        result = resolver.resolve("spec-template")
        assert result is not None
        assert result.name == "spec-template.md"
        assert "Core Spec Template" in result.read_text()

    def test_resolve_nonexistent(self, project_dir):
        """Test resolving a nonexistent template returns None."""
        resolver = PresetResolver(project_dir)
        result = resolver.resolve("nonexistent-template")
        assert result is None

    def test_resolver_ignores_traversing_registry_ids(self, project_dir):
        """Registry IDs cannot escape preset or extension install roots."""
        for registry_dir, registry_key, outside_name in (
            ("presets", "presets", "outside-preset"),
            ("extensions", "extensions", "outside-extension"),
        ):
            outside = project_dir.parent / outside_name
            (outside / "templates").mkdir(parents=True)
            (outside / "templates" / "spec-template.md").write_text(
                f"# Sensitive {registry_key}\n",
                encoding="utf-8",
            )
            installed = project_dir / ".specify" / registry_dir
            installed.mkdir(parents=True, exist_ok=True)
            (installed / ".registry").write_text(
                json.dumps(
                    {
                        registry_key: {
                            f"../../../{outside_name}": {
                                "enabled": True,
                                "priority": 1,
                            }
                        }
                    }
                ),
                encoding="utf-8",
            )

        content = PresetResolver(project_dir).resolve_content("spec-template")

        assert content is not None
        assert "Core Spec Template" in content
        assert "Sensitive" not in content

    def test_resolve_higher_priority_pack_wins(self, project_dir, temp_dir, valid_pack_data):
        """Test that a pack with lower priority number wins over higher number."""
        manager = PresetManager(project_dir)

        # Create pack A (priority 10 — lower precedence)
        pack_a_dir = temp_dir / "pack-a"
        pack_a_dir.mkdir()
        data_a = {**valid_pack_data}
        data_a["preset"] = {**valid_pack_data["preset"], "id": "pack-a", "name": "Pack A"}
        with open(pack_a_dir / "preset.yml", 'w') as f:
            yaml.dump(data_a, f)
        (pack_a_dir / "templates").mkdir()
        (pack_a_dir / "templates" / "spec-template.md").write_text("# From Pack A\n")

        # Create pack B (priority 1 — higher precedence)
        pack_b_dir = temp_dir / "pack-b"
        pack_b_dir.mkdir()
        data_b = {**valid_pack_data}
        data_b["preset"] = {**valid_pack_data["preset"], "id": "pack-b", "name": "Pack B"}
        with open(pack_b_dir / "preset.yml", 'w') as f:
            yaml.dump(data_b, f)
        (pack_b_dir / "templates").mkdir()
        (pack_b_dir / "templates" / "spec-template.md").write_text("# From Pack B\n")

        # Install A first (priority 10), B second (priority 1)
        manager.install_from_directory(pack_a_dir, "0.1.5", priority=10)
        manager.install_from_directory(pack_b_dir, "0.1.5", priority=1)

        # Pack B should win because lower priority number
        resolver = PresetResolver(project_dir)
        result = resolver.resolve("spec-template")
        assert result is not None
        assert "From Pack B" in result.read_text()

    def test_resolve_override_takes_priority(self, project_dir):
        """Test that project overrides take priority over core."""
        # Create override
        overrides_dir = project_dir / ".specify" / "templates" / "overrides"
        overrides_dir.mkdir(parents=True)
        override = overrides_dir / "spec-template.md"
        override.write_text("# Override Spec Template\n")

        resolver = PresetResolver(project_dir)
        result = resolver.resolve("spec-template")
        assert result is not None
        assert "Override Spec Template" in result.read_text()

    def test_resolve_pack_takes_priority_over_core(self, project_dir, pack_dir):
        """Test that installed packs take priority over core templates."""
        # Install the pack
        manager = PresetManager(project_dir)
        manager.install_from_directory(pack_dir, "0.1.5")

        resolver = PresetResolver(project_dir)
        result = resolver.resolve("spec-template")
        assert result is not None
        assert "Custom Spec Template" in result.read_text()

    def _install_pack_with_manifest_file(self, project_dir, *, extra_file=False):
        """Create a pack whose manifest declares a NON-convention file: path.

        Returns the pack dir under the project. The declared file lives at
        custom/spec.md (not the convention templates/spec-template.md).
        """
        presets_dir = project_dir / ".specify" / "presets"
        pack_dir = presets_dir / "mypack"
        (pack_dir / "custom").mkdir(parents=True)
        (pack_dir / "custom" / "spec.md").write_text(
            "# Manifest-declared Spec\n", encoding="utf-8"
        )
        if extra_file:
            # An undeclared convention-path file the manifest points away from.
            (pack_dir / "templates").mkdir()
            (pack_dir / "templates" / "spec-template.md").write_text(
                "# Stray Convention Spec\n", encoding="utf-8"
            )
        manifest = {
            "schema_version": "1.0",
            "preset": {
                "id": "mypack",
                "name": "My Pack",
                "version": "1.0.0",
                "description": "declares a non-convention file path",
            },
            "requires": {"speckit_version": ">=0.1.0"},
            "provides": {
                "templates": [
                    {
                        "type": "template",
                        "name": "spec-template",
                        "file": "custom/spec.md",
                        "strategy": "replace",
                    }
                ]
            },
        }
        with open(pack_dir / "preset.yml", "w") as f:
            yaml.dump(manifest, f)
        PresetRegistry(presets_dir).add(
            "mypack", {"version": "1.0.0", "priority": 10}
        )
        return pack_dir

    def test_resolve_uses_manifest_declared_file_path(self, project_dir):
        """resolve() must honor a manifest-declared non-convention file: path.

        Previously the tier-2 loop was convention-only, so it returned the
        core template and resolve_with_source() misattributed source='core',
        diverging from collect_all_layers()/resolve_content().
        """
        pack_dir = self._install_pack_with_manifest_file(project_dir)
        resolver = PresetResolver(project_dir)

        result = resolver.resolve("spec-template")
        assert result == pack_dir / "custom" / "spec.md"
        assert "Manifest-declared Spec" in result.read_text()

        sourced = resolver.resolve_with_source("spec-template")
        assert sourced is not None
        assert "mypack" in sourced["source"]
        # resolve() must agree with collect_all_layers()'s top layer.
        layers = resolver.collect_all_layers("spec-template")
        assert Path(layers[0]["path"]) == pack_dir / "custom" / "spec.md"

    def test_resolve_manifest_file_wins_over_undeclared_convention_file(
        self, project_dir
    ):
        """A stray convention-path file must not shadow the manifest's file:."""
        pack_dir = self._install_pack_with_manifest_file(
            project_dir, extra_file=True
        )
        resolver = PresetResolver(project_dir)
        result = resolver.resolve("spec-template")
        assert result == pack_dir / "custom" / "spec.md"
        assert "Manifest-declared Spec" in result.read_text()

    def test_resolve_skips_convention_when_manifest_file_missing(self, project_dir):
        """When the manifest declares a file: that does not exist, resolve()
        must NOT fall back to a convention file in the same pack (that would
        mask a typo) — it skips the pack and resolves core instead."""
        presets_dir = project_dir / ".specify" / "presets"
        pack_dir = presets_dir / "mypack"
        # Manifest declares custom/spec.md (MISSING); a convention file exists
        # in the pack and must NOT be used.
        (pack_dir / "templates").mkdir(parents=True)
        (pack_dir / "templates" / "spec-template.md").write_text(
            "# Stray Convention Spec\n", encoding="utf-8"
        )
        manifest = {
            "schema_version": "1.0",
            "preset": {
                "id": "mypack",
                "name": "My Pack",
                "version": "1.0.0",
                "description": "declares a missing file path",
            },
            "requires": {"speckit_version": ">=0.1.0"},
            "provides": {
                "templates": [
                    {
                        "type": "template",
                        "name": "spec-template",
                        "file": "custom/spec.md",
                        "strategy": "replace",
                    }
                ]
            },
        }
        with open(pack_dir / "preset.yml", "w") as f:
            yaml.dump(manifest, f)
        PresetRegistry(presets_dir).add(
            "mypack", {"version": "1.0.0", "priority": 10}
        )

        resolver = PresetResolver(project_dir)
        result = resolver.resolve("spec-template")
        assert result is not None
        content = result.read_text()
        assert "Stray Convention Spec" not in content  # pack convention skipped
        assert "Core Spec Template" in content  # fell through to core

    def test_resolve_skips_convention_when_manifest_file_is_directory(
        self, project_dir
    ):
        """When the manifest's file: path resolves to a DIRECTORY (not a regular
        file), resolve()/collect_all_layers() must treat it as missing — exists()
        would accept it and downstream read_text() on a directory would crash.
        The pack is skipped (no convention fallback), so core wins."""
        presets_dir = project_dir / ".specify" / "presets"
        pack_dir = presets_dir / "mypack"
        # Declared file: custom/spec.md is created as a DIRECTORY.
        (pack_dir / "custom" / "spec.md").mkdir(parents=True)
        # A convention file also exists and must NOT be used.
        (pack_dir / "templates").mkdir(parents=True)
        (pack_dir / "templates" / "spec-template.md").write_text(
            "# Stray Convention Spec\n", encoding="utf-8"
        )
        manifest = {
            "schema_version": "1.0",
            "preset": {
                "id": "mypack",
                "name": "My Pack",
                "version": "1.0.0",
                "description": "declares a file: that is actually a directory",
            },
            "requires": {"speckit_version": ">=0.1.0"},
            "provides": {
                "templates": [
                    {
                        "type": "template",
                        "name": "spec-template",
                        "file": "custom/spec.md",
                        "strategy": "replace",
                    }
                ]
            },
        }
        with open(pack_dir / "preset.yml", "w") as f:
            yaml.dump(manifest, f)
        PresetRegistry(presets_dir).add(
            "mypack", {"version": "1.0.0", "priority": 10}
        )

        resolver = PresetResolver(project_dir)
        result = resolver.resolve("spec-template")
        assert result is not None
        assert result.is_file()  # never a directory
        content = result.read_text()
        assert "Stray Convention Spec" not in content  # pack convention skipped
        assert "Core Spec Template" in content  # fell through to core
        # collect_all_layers() must agree: the directory is not a layer.
        layers = resolver.collect_all_layers("spec-template")
        assert all(Path(layer["path"]).is_file() for layer in layers)
        assert all(
            Path(layer["path"]) != pack_dir / "custom" / "spec.md"
            for layer in layers
        )

    def test_resolve_override_takes_priority_over_pack(self, project_dir, pack_dir):
        """Test that overrides take priority over installed packs."""
        # Install the pack
        manager = PresetManager(project_dir)
        manager.install_from_directory(pack_dir, "0.1.5")

        # Create override
        overrides_dir = project_dir / ".specify" / "templates" / "overrides"
        overrides_dir.mkdir(parents=True)
        override = overrides_dir / "spec-template.md"
        override.write_text("# Override Spec Template\n")

        resolver = PresetResolver(project_dir)
        result = resolver.resolve("spec-template")
        assert result is not None
        assert "Override Spec Template" in result.read_text()

    def test_resolve_extension_provided_templates(self, project_dir):
        """Test resolving templates provided by extensions."""
        # Create extension with templates
        ext_dir = project_dir / ".specify" / "extensions" / "my-ext"
        ext_templates_dir = ext_dir / "templates"
        ext_templates_dir.mkdir(parents=True)
        ext_template = ext_templates_dir / "custom-template.md"
        ext_template.write_text("# Extension Custom Template\n")

        # Register extension in registry
        extensions_dir = project_dir / ".specify" / "extensions"
        ext_registry = ExtensionRegistry(extensions_dir)
        ext_registry.add("my-ext", {"version": "1.0.0", "priority": 10})

        resolver = PresetResolver(project_dir)
        result = resolver.resolve("custom-template")
        assert result is not None
        assert "Extension Custom Template" in result.read_text()

    def test_resolve_disabled_extension_templates_skipped(self, project_dir):
        """Test that disabled extension templates are not resolved."""
        # Create extension with templates
        ext_dir = project_dir / ".specify" / "extensions" / "disabled-ext"
        ext_templates_dir = ext_dir / "templates"
        ext_templates_dir.mkdir(parents=True)
        ext_template = ext_templates_dir / "disabled-template.md"
        ext_template.write_text("# Disabled Extension Template\n")

        # Register extension as disabled
        extensions_dir = project_dir / ".specify" / "extensions"
        ext_registry = ExtensionRegistry(extensions_dir)
        ext_registry.add("disabled-ext", {"version": "1.0.0", "priority": 1, "enabled": False})

        # Template should NOT be resolved because extension is disabled
        resolver = PresetResolver(project_dir)
        result = resolver.resolve("disabled-template")
        assert result is None, "Disabled extension template should not be resolved"

    def test_resolve_disabled_extension_not_picked_up_as_unregistered(self, project_dir):
        """Test that disabled extensions are not picked up via unregistered dir scan."""
        # Create extension directory with templates
        ext_dir = project_dir / ".specify" / "extensions" / "test-disabled-ext"
        ext_templates_dir = ext_dir / "templates"
        ext_templates_dir.mkdir(parents=True)
        ext_template = ext_templates_dir / "unique-disabled-template.md"
        ext_template.write_text("# Should Not Resolve\n")

        # Register the extension but disable it
        extensions_dir = project_dir / ".specify" / "extensions"
        ext_registry = ExtensionRegistry(extensions_dir)
        ext_registry.add("test-disabled-ext", {"version": "1.0.0", "enabled": False})

        # Verify the template is NOT resolved (even though the directory exists)
        resolver = PresetResolver(project_dir)
        result = resolver.resolve("unique-disabled-template")
        assert result is None, "Disabled extension should not be picked up as unregistered"

    @pytest.mark.parametrize(
        "registry_bytes",
        [b"{ not valid json", b'{"extensions": []}', b"[]"],
        ids=["invalid_json", "non_mapping_extensions", "non_mapping_root"],
    )
    def test_resolve_fails_closed_on_corrupt_extension_registry(
        self, project_dir, registry_bytes
    ):
        """A corrupt extension registry must fail closed rather than let the
        directory scan admit every on-disk extension as enabled."""
        extensions_dir = project_dir / ".specify" / "extensions"
        ext_templates_dir = extensions_dir / "sneaky-ext" / "templates"
        ext_templates_dir.mkdir(parents=True)
        (ext_templates_dir / "custom-template.md").write_text(
            "# Should not be served\n"
        )
        (extensions_dir / ".registry").write_bytes(registry_bytes)

        resolver = PresetResolver(project_dir)
        with pytest.raises(PresetValidationError, match="Invalid extension registry"):
            resolver._get_all_extensions_by_priority()
        with pytest.raises(PresetValidationError, match="Invalid extension registry"):
            resolver.resolve("custom-template")

    def test_resolve_fails_closed_when_registry_is_directory(self, project_dir):
        """A directory at the registry path must fail closed, not be treated as
        an absent registry that enables every on-disk extension."""
        extensions_dir = project_dir / ".specify" / "extensions"
        ext_templates_dir = extensions_dir / "sneaky-ext" / "templates"
        ext_templates_dir.mkdir(parents=True)
        (ext_templates_dir / "custom-template.md").write_text(
            "# Should not be served\n"
        )
        (extensions_dir / ".registry").mkdir()

        resolver = PresetResolver(project_dir)
        with pytest.raises(PresetValidationError, match="Invalid extension registry"):
            resolver.resolve("custom-template")

    def test_resolve_fails_closed_when_registry_is_broken_symlink(self, project_dir):
        """A dangling ``.registry`` symlink must fail closed. ``Path.exists()``
        follows symlinks and would mistake it for an absent registry, reopening
        the fail-open directory scan."""
        extensions_dir = project_dir / ".specify" / "extensions"
        ext_templates_dir = extensions_dir / "sneaky-ext" / "templates"
        ext_templates_dir.mkdir(parents=True)
        (ext_templates_dir / "custom-template.md").write_text(
            "# Should not be served\n"
        )
        (extensions_dir / ".registry").symlink_to(
            extensions_dir / "does-not-exist"
        )

        registry = ExtensionRegistry(extensions_dir)
        assert registry.is_corrupt()
        resolver = PresetResolver(project_dir)
        with pytest.raises(PresetValidationError, match="Invalid extension registry"):
            resolver.resolve("custom-template")

    def test_resolve_pack_over_extension(self, project_dir, pack_dir, temp_dir, valid_pack_data):
        """Test that pack templates take priority over extension templates."""
        # Create extension with templates
        ext_dir = project_dir / ".specify" / "extensions" / "my-ext"
        ext_templates_dir = ext_dir / "templates"
        ext_templates_dir.mkdir(parents=True)
        ext_template = ext_templates_dir / "spec-template.md"
        ext_template.write_text("# Extension Spec Template\n")

        # Install a pack with the same template
        manager = PresetManager(project_dir)
        manager.install_from_directory(pack_dir, "0.1.5")

        resolver = PresetResolver(project_dir)
        result = resolver.resolve("spec-template")
        assert result is not None
        # Pack should win over extension
        assert "Custom Spec Template" in result.read_text()

    def test_resolve_with_source_core(self, project_dir):
        """Test resolve_with_source for core template."""
        resolver = PresetResolver(project_dir)
        result = resolver.resolve_with_source("spec-template")
        assert result is not None
        assert result["source"] == "core"
        assert "spec-template.md" in result["path"]

    def test_resolve_with_source_override(self, project_dir):
        """Test resolve_with_source for override template."""
        overrides_dir = project_dir / ".specify" / "templates" / "overrides"
        overrides_dir.mkdir(parents=True)
        override = overrides_dir / "spec-template.md"
        override.write_text("# Override\n")

        resolver = PresetResolver(project_dir)
        result = resolver.resolve_with_source("spec-template")
        assert result is not None
        assert result["source"] == "project override"

    def test_resolve_with_source_pack(self, project_dir, pack_dir):
        """Test resolve_with_source for pack template."""
        manager = PresetManager(project_dir)
        manager.install_from_directory(pack_dir, "0.1.5")

        resolver = PresetResolver(project_dir)
        result = resolver.resolve_with_source("spec-template")
        assert result is not None
        assert "test-pack" in result["source"]
        assert "v1.0.0" in result["source"]

    def test_resolve_with_source_extension(self, project_dir):
        """Test resolve_with_source for extension-provided template."""
        ext_dir = project_dir / ".specify" / "extensions" / "my-ext"
        ext_templates_dir = ext_dir / "templates"
        ext_templates_dir.mkdir(parents=True)
        ext_template = ext_templates_dir / "unique-template.md"
        ext_template.write_text("# Unique\n")

        # Register extension in registry
        extensions_dir = project_dir / ".specify" / "extensions"
        ext_registry = ExtensionRegistry(extensions_dir)
        ext_registry.add("my-ext", {"version": "1.0.0", "priority": 10})

        resolver = PresetResolver(project_dir)
        result = resolver.resolve_with_source("unique-template")
        assert result is not None
        assert result["source"] == "extension:my-ext v1.0.0"

    def test_resolve_with_source_not_found(self, project_dir):
        """Test resolve_with_source for nonexistent template."""
        resolver = PresetResolver(project_dir)
        result = resolver.resolve_with_source("nonexistent")
        assert result is None

    def test_resolve_skips_hidden_extension_dirs(self, project_dir):
        """Test that hidden directories in extensions are skipped."""
        ext_dir = project_dir / ".specify" / "extensions" / ".backup"
        ext_templates_dir = ext_dir / "templates"
        ext_templates_dir.mkdir(parents=True)
        ext_template = ext_templates_dir / "hidden-template.md"
        ext_template.write_text("# Hidden\n")

        resolver = PresetResolver(project_dir)
        result = resolver.resolve("hidden-template")
        assert result is None

    def test_collect_all_layers_finds_bundled_core_without_specify_commands(
        self, project_dir
    ):
        """Tier-5 fallback locates the bundled core command when
        .specify/templates/commands/ has no matching file.

        Regression test for #3086: a stale ``.parent`` chain made the
        source-checkout fallback resolve to ``src/templates/...`` (which does
        not exist), so ``wrap`` presets found no base layer. The fallback must
        resolve against the real repo-root ``templates/commands`` tree.
        """
        # project_dir's commands dir is empty, so tier-4 cannot satisfy this.
        resolver = PresetResolver(project_dir)
        layers = resolver.collect_all_layers("speckit.implement", "command")
        assert layers, "expected a bundled core base layer to be found"
        assert layers[-1]["source"] == "core (bundled)"
        assert layers[-1]["path"].parts[-2:] == ("commands", "implement.md")

    def test_resolve_command_falls_back_to_bundled_core(self, project_dir):
        """resolve() tier-5 returns the bundled core command when
        .specify/templates/commands/ lacks it (regression for #3086)."""
        resolver = PresetResolver(project_dir)
        result = resolver.resolve("speckit.implement", "command")
        assert result is not None
        assert result.parts[-2:] == ("commands", "implement.md")


class TestResolveCore:
    """Test PresetResolver.resolve_core() skips the installed-presets tier."""

    def test_resolve_core_does_not_return_preset_files(self, project_dir):
        """resolve_core must not return files from .specify/presets/."""
        preset_cmd_dir = project_dir / ".specify" / "presets" / "my-preset" / "commands"
        preset_cmd_dir.mkdir(parents=True)
        (preset_cmd_dir / "specify.md").write_text("---\ndescription: preset wrap\n---\n\nwrap body\n")

        resolver = PresetResolver(project_dir)
        result = resolver.resolve_core("specify", "command")
        # The preset file must never be returned — but the bundled core may be.
        if result is not None:
            assert "presets" not in result.parts

    def test_resolve_core_returns_core_template(self, project_dir):
        """resolve_core falls through to core templates (tier 4)."""
        core_cmd_dir = project_dir / ".specify" / "templates" / "commands"
        core_cmd_dir.mkdir(parents=True, exist_ok=True)
        (core_cmd_dir / "specify.md").write_text("---\ndescription: core\n---\n\ncore body\n")

        # Also place a preset file — resolve_core must still return the core
        preset_cmd_dir = project_dir / ".specify" / "presets" / "my-preset" / "commands"
        preset_cmd_dir.mkdir(parents=True)
        (preset_cmd_dir / "specify.md").write_text("---\ndescription: preset wrap\n---\n\nwrap body\n")

        resolver = PresetResolver(project_dir)
        result = resolver.resolve_core("specify", "command")
        assert result is not None
        assert "presets" not in result.parts
        assert result.parts[-3:] == ("templates", "commands", "specify.md")

    def test_resolve_core_returns_override(self, project_dir):
        """resolve_core returns tier-1 override if present."""
        override_dir = project_dir / ".specify" / "templates" / "overrides"
        override_dir.mkdir(parents=True)
        (override_dir / "specify.md").write_text("---\ndescription: override\n---\n\noverride body\n")

        resolver = PresetResolver(project_dir)
        result = resolver.resolve_core("specify", "command")
        assert result is not None
        assert result.parts[-2:] == ("overrides", "specify.md")

    def test_resolve_core_returns_extension_template(self, project_dir):
        """resolve_core returns extension templates (tier 3)."""
        ext_cmd_dir = project_dir / ".specify" / "extensions" / "myext" / "commands"
        ext_cmd_dir.mkdir(parents=True)
        (ext_cmd_dir / "myext-cmd.md").write_text("---\ndescription: ext\n---\n\next body\n")

        resolver = PresetResolver(project_dir)
        result = resolver.resolve_core("myext-cmd", "command")
        assert result is not None
        assert result.parts[-4:-1] == ("extensions", "myext", "commands")

    def test_resolve_core_returns_none_when_nothing_found(self, project_dir):
        """resolve_core returns None when no file found in tiers 1/3/4."""
        resolver = PresetResolver(project_dir)
        result = resolver.resolve_core("nonexistent", "command")
        assert result is None

    def test_resolve_extension_command_via_manifest_skips_oserror_manifests(self, project_dir):
        """resolve_extension_command_via_manifest skips extensions whose manifest raises OSError."""
        import unittest.mock as mock

        ext_dir = project_dir / ".specify" / "extensions" / "bad-ext"
        cmd_dir = ext_dir / "commands"
        cmd_dir.mkdir(parents=True)
        (cmd_dir / "mycmd.md").write_text("---\ndescription: d\n---\n\nbody\n")
        (ext_dir / "extension.yml").write_text(
            "schema_version: '1.0'\n"
            "extension:\n  id: bad-ext\n  name: Bad\n  version: 1.0.0\n"
            "  description: d\n  author: a\n  repository: https://example.com\n"
            "  license: MIT\n"
            "requires:\n  speckit_version: '>=0.2.0'\n"
            "provides:\n  commands:\n"
            "    - name: speckit.bad-ext.mycmd\n"
            "      file: commands/mycmd.md\n"
            "      description: My command\n"
        )

        resolver = PresetResolver(project_dir)
        # Simulate a permission error when opening the manifest file.
        with mock.patch("builtins.open", side_effect=PermissionError("denied")):
            result = resolver.resolve_extension_command_via_manifest("speckit.bad-ext.mycmd")

        assert result is None, "OSError during manifest load must be silently skipped"


class TestExtensionPriorityResolution:
    """Test extension priority resolution with registered and unregistered extensions."""

    def test_unregistered_beats_registered_with_lower_precedence(self, project_dir):
        """Unregistered extension (implicit priority 10) beats registered with priority 20."""
        extensions_dir = project_dir / ".specify" / "extensions"
        extensions_dir.mkdir(parents=True, exist_ok=True)

        # Create registered extension with priority 20 (lower precedence than 10)
        registered_dir = extensions_dir / "registered-ext"
        (registered_dir / "templates").mkdir(parents=True)
        (registered_dir / "templates" / "test-template.md").write_text("# From Registered\n")

        ext_registry = ExtensionRegistry(extensions_dir)
        ext_registry.add("registered-ext", {"version": "1.0.0", "priority": 20})

        # Create unregistered extension directory (implicit priority 10)
        unregistered_dir = extensions_dir / "unregistered-ext"
        (unregistered_dir / "templates").mkdir(parents=True)
        (unregistered_dir / "templates" / "test-template.md").write_text("# From Unregistered\n")

        # Unregistered (priority 10) should beat registered (priority 20)
        resolver = PresetResolver(project_dir)
        result = resolver.resolve("test-template")
        assert result is not None
        assert "From Unregistered" in result.read_text()

    def test_registered_with_higher_precedence_beats_unregistered(self, project_dir):
        """Registered extension with priority 5 beats unregistered (implicit priority 10)."""
        extensions_dir = project_dir / ".specify" / "extensions"
        extensions_dir.mkdir(parents=True, exist_ok=True)

        # Create registered extension with priority 5 (higher precedence than 10)
        registered_dir = extensions_dir / "registered-ext"
        (registered_dir / "templates").mkdir(parents=True)
        (registered_dir / "templates" / "test-template.md").write_text("# From Registered\n")

        ext_registry = ExtensionRegistry(extensions_dir)
        ext_registry.add("registered-ext", {"version": "1.0.0", "priority": 5})

        # Create unregistered extension directory (implicit priority 10)
        unregistered_dir = extensions_dir / "unregistered-ext"
        (unregistered_dir / "templates").mkdir(parents=True)
        (unregistered_dir / "templates" / "test-template.md").write_text("# From Unregistered\n")

        # Registered (priority 5) should beat unregistered (priority 10)
        resolver = PresetResolver(project_dir)
        result = resolver.resolve("test-template")
        assert result is not None
        assert "From Registered" in result.read_text()

    def test_unregistered_attribution_with_priority_ordering(self, project_dir):
        """Test resolve_with_source correctly attributes unregistered extension."""
        extensions_dir = project_dir / ".specify" / "extensions"
        extensions_dir.mkdir(parents=True, exist_ok=True)

        # Create registered extension with priority 20
        registered_dir = extensions_dir / "registered-ext"
        (registered_dir / "templates").mkdir(parents=True)
        (registered_dir / "templates" / "test-template.md").write_text("# From Registered\n")

        ext_registry = ExtensionRegistry(extensions_dir)
        ext_registry.add("registered-ext", {"version": "1.0.0", "priority": 20})

        # Create unregistered extension (implicit priority 10)
        unregistered_dir = extensions_dir / "unregistered-ext"
        (unregistered_dir / "templates").mkdir(parents=True)
        (unregistered_dir / "templates" / "test-template.md").write_text("# From Unregistered\n")

        # Attribution should show unregistered extension
        resolver = PresetResolver(project_dir)
        result = resolver.resolve_with_source("test-template")
        assert result is not None
        assert "unregistered-ext" in result["source"]
        assert "(unregistered)" in result["source"]

    def test_same_priority_sorted_alphabetically(self, project_dir):
        """Extensions with same priority are sorted alphabetically by ID."""
        extensions_dir = project_dir / ".specify" / "extensions"
        extensions_dir.mkdir(parents=True, exist_ok=True)

        # Create two unregistered extensions (both implicit priority 10)
        # "aaa-ext" should come before "zzz-ext" alphabetically
        zzz_dir = extensions_dir / "zzz-ext"
        (zzz_dir / "templates").mkdir(parents=True)
        (zzz_dir / "templates" / "test-template.md").write_text("# From ZZZ\n")

        aaa_dir = extensions_dir / "aaa-ext"
        (aaa_dir / "templates").mkdir(parents=True)
        (aaa_dir / "templates" / "test-template.md").write_text("# From AAA\n")

        # AAA should win due to alphabetical ordering at same priority
        resolver = PresetResolver(project_dir)
        result = resolver.resolve("test-template")
        assert result is not None
        assert "From AAA" in result.read_text()


class TestSelfTestPreset:
    """Template resolution using the bundled self-test preset."""

    def test_self_test_overrides_all_core_templates(self, project_dir):
        """Test that installing self-test overrides every core template."""
        # Set up core templates in the project
        templates_dir = project_dir / ".specify" / "templates"
        for name in CORE_TEMPLATE_NAMES:
            (templates_dir / f"{name}.md").write_text(f"# Core {name}\n")

        # Install self-test preset
        manager = PresetManager(project_dir)
        install_self_test_preset(manager)

        # Every core template should now resolve from the preset
        resolver = PresetResolver(project_dir)
        for name in CORE_TEMPLATE_NAMES:
            result = resolver.resolve(name)
            assert result is not None, f"{name} did not resolve"
            content = result.read_text()
            assert "preset:self-test" in content, (
                f"{name} resolved but not from self-test preset"
            )

    def test_self_test_resolve_with_source(self, project_dir):
        """Test that resolve_with_source attributes templates to self-test."""
        templates_dir = project_dir / ".specify" / "templates"
        for name in CORE_TEMPLATE_NAMES:
            (templates_dir / f"{name}.md").write_text(f"# Core {name}\n")

        manager = PresetManager(project_dir)
        install_self_test_preset(manager)

        resolver = PresetResolver(project_dir)
        for name in CORE_TEMPLATE_NAMES:
            result = resolver.resolve_with_source(name)
            assert result is not None, f"{name} did not resolve"
            assert "self-test" in result["source"], (
                f"{name} source is '{result['source']}', expected self-test"
            )

    def test_self_test_override_resolves_constitution_template(self, project_dir):
        """The preset override of constitution-template resolves to the preset file."""
        templates_dir = project_dir / ".specify" / "templates"
        (templates_dir / "constitution-template.md").write_text("# Core constitution\n")

        manager = PresetManager(project_dir)
        install_self_test_preset(manager)

        resolver = PresetResolver(project_dir)
        result = resolver.resolve("constitution-template", "template")
        assert result is not None
        assert "preset:self-test" in result.read_text()


class TestPresetEnableDisable:
    """Disabled presets are excluded from template resolution."""









    def test_disabled_preset_excluded_from_resolution(self, project_dir, pack_dir):
        """Test that disabled presets are excluded from template resolution."""
        # Install preset with a template
        manager = PresetManager(project_dir)
        manager.install_from_directory(pack_dir, "0.1.5")

        # Create a template in the preset directory
        preset_template = project_dir / ".specify" / "presets" / "test-pack" / "templates" / "test-template.md"
        preset_template.parent.mkdir(parents=True, exist_ok=True)
        preset_template.write_text("# Template from test-pack")

        resolver = PresetResolver(project_dir)

        # Template should be found when enabled
        result = resolver.resolve("test-template", "template")
        assert result is not None
        assert "test-pack" in str(result)

        # Disable the preset
        manager.registry.update("test-pack", {"enabled": False})

        # Template should NOT be found when disabled
        resolver2 = PresetResolver(project_dir)
        result2 = resolver2.resolve("test-template", "template")
        assert result2 is None


class TestWrapStrategy:
    """Resolution of extension command, template, and script layers."""

    def test_extension_command_resolves_via_extension_directory(self, project_dir):
        """Extension commands (e.g. speckit.git.feature) resolve from the extension directory.

        Both _register_skills and register_commands pass the full cmd_name to
        _substitute_core_template, which tries the full name first via PresetResolver
        and finds speckit.git.feature.md in the extension commands directory.
        """
        from specify_cli.presets import _substitute_core_template
        from specify_cli.agents import CommandRegistrar

        # Place the template where a real extension would install it
        ext_cmd_dir = project_dir / ".specify" / "extensions" / "git" / "commands"
        ext_cmd_dir.mkdir(parents=True, exist_ok=True)
        (ext_cmd_dir / "speckit.git.feature.md").write_text(
            "---\ndescription: git feature core\n---\n\n# Git Feature Core\n"
        )
        # Ensure a hyphenated or dot-separated fallback does NOT exist
        assert not (project_dir / ".specify" / "templates" / "commands" / "git.feature.md").exists()
        assert not (project_dir / ".specify" / "templates" / "commands" / "git-feature.md").exists()

        registrar = CommandRegistrar()
        body = "## Wrapper\n\n{CORE_TEMPLATE}\n"

        # Both call sites now pass the full cmd_name
        result, _ = _substitute_core_template(body, "speckit.git.feature", project_dir, registrar)

        assert "# Git Feature Core" in result
        assert "{CORE_TEMPLATE}" not in result

    def test_extension_command_resolves_via_manifest_when_filename_differs(self, project_dir):
        """Extension commands whose filename differs from the command name resolve via extension.yml.

        The selftest extension maps speckit.selftest.extension → commands/selftest.md.
        Name-based lookup would look for commands/speckit.selftest.extension.md and fail;
        manifest-based lookup must find the actual file declared in the manifest.
        """
        from specify_cli.presets import _substitute_core_template
        from specify_cli.agents import CommandRegistrar

        ext_dir = project_dir / ".specify" / "extensions" / "selftest"
        cmd_dir = ext_dir / "commands"
        cmd_dir.mkdir(parents=True, exist_ok=True)

        # File is named selftest.md, NOT speckit.selftest.extension.md
        (cmd_dir / "selftest.md").write_text(
            "---\ndescription: selftest core\n---\n\n# Selftest Core\n"
        )
        # Manifest maps the command name to the actual file
        (ext_dir / "extension.yml").write_text(
            "schema_version: '1.0'\n"
            "extension:\n  id: selftest\n  name: Self-Test\n  version: 1.0.0\n"
            "  description: test\n  author: test\n  repository: https://example.com\n"
            "  license: MIT\n"
            "requires:\n  speckit_version: '>=0.2.0'\n"
            "provides:\n"
            "  commands:\n"
            "    - name: speckit.selftest.extension\n"
            "      file: commands/selftest.md\n"
            "      description: Selftest command\n"
        )

        registrar = CommandRegistrar()
        body = "## Wrapper\n\n{CORE_TEMPLATE}\n"
        result, _ = _substitute_core_template(body, "speckit.selftest.extension", project_dir, registrar)

        assert "# Selftest Core" in result
        assert "{CORE_TEMPLATE}" not in result

    def test_extension_template_resolves_via_manifest_when_filename_differs(self, project_dir):
        """provides.templates entries resolve via extension.yml when the file
        doesn't sit at the conventional path.

        Regression coverage for #4010: manifest-declared templates/scripts
        must actually be consulted by the resolver, not just accepted by
        manifest validation.
        """
        ext_dir = project_dir / ".specify" / "extensions" / "reportext"
        tmpl_dir = ext_dir / "templates" / "nested"
        tmpl_dir.mkdir(parents=True, exist_ok=True)

        # File lives at a path convention-based lookup (templates/<name>.md)
        # would never find.
        (tmpl_dir / "actual.md").write_text("# Report Scaffold\n")
        (ext_dir / "extension.yml").write_text(
            "schema_version: '1.0'\n"
            "extension:\n  id: reportext\n  name: Report Ext\n  version: 1.0.0\n"
            "  description: test\n  author: test\n  repository: https://example.com\n"
            "  license: MIT\n"
            "requires:\n  speckit_version: '>=0.2.0'\n"
            "provides:\n"
            "  templates:\n"
            "    - name: report-scaffold\n"
            "      file: templates/nested/actual.md\n"
            "      description: Report scaffold\n"
        )

        resolver = PresetResolver(project_dir)
        layers = resolver.collect_all_layers("report-scaffold", "template")
        assert layers, "expected the manifest-declared template to resolve"
        assert layers[0]["path"] == tmpl_dir / "actual.md"
        assert layers[0]["strategy"] == "replace"

    def test_extension_script_resolves_via_manifest_when_filename_differs(self, project_dir):
        """provides.scripts entries resolve via extension.yml when the file
        doesn't sit at the conventional path."""
        ext_dir = project_dir / ".specify" / "extensions" / "collectext"
        script_dir = ext_dir / "scripts" / "bash"
        script_dir.mkdir(parents=True, exist_ok=True)

        # File is under scripts/bash/, not directly under scripts/, so
        # convention-based lookup (scripts/<name>.sh) would never find it.
        (script_dir / "collect.sh").write_text("#!/usr/bin/env bash\necho collect\n")
        (ext_dir / "extension.yml").write_text(
            "schema_version: '1.0'\n"
            "extension:\n  id: collectext\n  name: Collect Ext\n  version: 1.0.0\n"
            "  description: test\n  author: test\n  repository: https://example.com\n"
            "  license: MIT\n"
            "requires:\n  speckit_version: '>=0.2.0'\n"
            "provides:\n"
            "  scripts:\n"
            "    - name: myext-collect\n"
            "      file: scripts/bash/collect.sh\n"
            "      description: Data-collection helper\n"
            "      runtimes: [bash]\n"
        )

        resolver = PresetResolver(project_dir)
        layers = resolver.collect_all_layers("myext-collect", "script")
        assert layers, "expected the manifest-declared script to resolve"
        assert layers[0]["path"] == script_dir / "collect.sh"
        assert layers[0]["strategy"] == "replace"

    def test_extension_template_convention_lookup_unaffected_when_undeclared(self, project_dir):
        """An extension template with no manifest entry still resolves via
        the pre-existing filename convention (no regression)."""
        ext_dir = project_dir / ".specify" / "extensions" / "conventionext"
        tmpl_dir = ext_dir / "templates"
        tmpl_dir.mkdir(parents=True, exist_ok=True)
        (tmpl_dir / "legacy-template.md").write_text("# Legacy Template\n")
        # No extension.yml at all -- purely convention-based, unregistered extension.

        resolver = PresetResolver(project_dir)
        layers = resolver.collect_all_layers("legacy-template", "template")
        assert layers, "expected convention-based lookup to still find the template"
        assert layers[0]["path"] == tmpl_dir / "legacy-template.md"

    def test_extension_manifest_wins_over_stale_conventional_file(self, project_dir):
        """A declared entry is authoritative even when a stale file also sits at
        the conventional path (templates/<name>.md) — the manifest must win,
        not the convention lookup, per #4010's acceptance criteria."""
        ext_dir = project_dir / ".specify" / "extensions" / "bothpathsext"
        (ext_dir / "templates").mkdir(parents=True, exist_ok=True)
        (ext_dir / "custom").mkdir(parents=True, exist_ok=True)

        # Stale file at the conventional path -- must NOT win.
        (ext_dir / "templates" / "report-scaffold.md").write_text("# Stale\n")
        # Declared file at a non-conventional path -- must win.
        (ext_dir / "custom" / "bar.md").write_text("# Actual\n")
        (ext_dir / "extension.yml").write_text(
            "schema_version: '1.0'\n"
            "extension:\n  id: bothpathsext\n  name: Both Paths Ext\n  version: 1.0.0\n"
            "  description: test\n  author: test\n  repository: https://example.com\n"
            "  license: MIT\n"
            "requires:\n  speckit_version: '>=0.2.0'\n"
            "provides:\n"
            "  templates:\n"
            "    - name: report-scaffold\n"
            "      file: custom/bar.md\n"
            "      description: Report scaffold\n"
        )

        resolver = PresetResolver(project_dir)

        layers = resolver.collect_all_layers("report-scaffold", "template")
        assert layers, "expected the manifest-declared template to resolve"
        assert layers[0]["path"] == ext_dir / "custom" / "bar.md"

        resolved = resolver.resolve("report-scaffold", "template")
        assert resolved == ext_dir / "custom" / "bar.md"

        with_source = resolver.resolve_with_source("report-scaffold", "template")
        assert with_source["path"] == str(ext_dir / "custom" / "bar.md")

    def test_extension_manifest_declared_but_missing_file_does_not_fall_back(self, project_dir):
        """A declared entry whose file is missing is authoritative -- the
        resolver must not silently mask the typo by falling back to a
        conventional file that happens to also exist."""
        ext_dir = project_dir / ".specify" / "extensions" / "missingfileext"
        (ext_dir / "scripts").mkdir(parents=True, exist_ok=True)

        # A conventional file exists, but the manifest declares a different,
        # non-existent file for the same name.
        (ext_dir / "scripts" / "myext-collect.sh").write_text("#!/usr/bin/env bash\necho legacy\n")
        (ext_dir / "extension.yml").write_text(
            "schema_version: '1.0'\n"
            "extension:\n  id: missingfileext\n  name: Missing File Ext\n  version: 1.0.0\n"
            "  description: test\n  author: test\n  repository: https://example.com\n"
            "  license: MIT\n"
            "requires:\n  speckit_version: '>=0.2.0'\n"
            "provides:\n"
            "  scripts:\n"
            "    - name: myext-collect\n"
            "      file: scripts/does-not-exist.sh\n"
            "      description: Data-collection helper\n"
        )

        resolver = PresetResolver(project_dir)

        assert resolver.collect_all_layers("myext-collect", "script") == []
        assert resolver.resolve("myext-collect", "script") is None

    def test_extension_script_resolve_and_resolve_with_source_parity(self, project_dir):
        """resolve() and resolve_with_source() must find a manifest-declared
        script at a non-conventional path, matching collect_all_layers()."""
        ext_dir = project_dir / ".specify" / "extensions" / "collectext2"
        script_dir = ext_dir / "scripts" / "bash"
        script_dir.mkdir(parents=True, exist_ok=True)

        (script_dir / "collect.sh").write_text("#!/usr/bin/env bash\necho collect\n")
        (ext_dir / "extension.yml").write_text(
            "schema_version: '1.0'\n"
            "extension:\n  id: collectext2\n  name: Collect Ext 2\n  version: 1.0.0\n"
            "  description: test\n  author: test\n  repository: https://example.com\n"
            "  license: MIT\n"
            "requires:\n  speckit_version: '>=0.2.0'\n"
            "provides:\n"
            "  scripts:\n"
            "    - name: myext-collect2\n"
            "      file: scripts/bash/collect.sh\n"
            "      description: Data-collection helper\n"
            "      runtimes: [bash]\n"
        )

        resolver = PresetResolver(project_dir)

        resolved = resolver.resolve("myext-collect2", "script")
        assert resolved == script_dir / "collect.sh"

        with_source = resolver.resolve_with_source("myext-collect2", "script")
        assert with_source is not None
        assert with_source["path"] == str(script_dir / "collect.sh")
        assert with_source["source"] == "extension:collectext2 (unregistered)"


class TestResolveContent:
    """Test PresetResolver.resolve_content() composition."""

    def test_resolve_content_core_template(self, project_dir):
        """Test resolve_content returns core template when no composition."""
        resolver = PresetResolver(project_dir)
        content = resolver.resolve_content("spec-template")
        assert content is not None
        assert "Core Spec Template" in content

    def test_resolve_content_nonexistent(self, project_dir):
        """Test resolve_content returns None for nonexistent template."""
        resolver = PresetResolver(project_dir)
        content = resolver.resolve_content("nonexistent")
        assert content is None

    def test_resolve_content_unreadable_winning_layer_returns_none(self, project_dir):
        """An undecodable winning layer must yield None, not a raw traceback.

        ``collect_all_layers`` deliberately keeps a non-UTF-8 legacy command
        layer (with its ``replace`` default) so unrelated commands still
        resolve. ``resolve_content`` then read that same file without a
        boundary, so the tolerated layer crashed with ``UnicodeDecodeError``
        at composition time — reachable from ``specify preset add`` via
        ``_register_commands``. The documented contract is "Composed content
        string, or None if not found".
        """
        presets_dir = project_dir / ".specify" / "presets"
        command_path = (
            presets_dir / "legacy-pack" / "commands" / "speckit.legacy.md"
        )
        command_path.parent.mkdir(parents=True)
        command_path.write_bytes(b"\xff\xfe")
        PresetRegistry(presets_dir).add(
            "legacy-pack", {"version": "1.0.0", "priority": 10}
        )

        resolver = PresetResolver(project_dir)
        content = resolver.resolve_content("speckit.legacy", "command")
        assert content is None

    def test_resolve_content_unreadable_base_under_composing_layer(
        self, project_dir, temp_dir, valid_pack_data
    ):
        """An undecodable base beneath a valid composing layer yields None.

        Covers the base-read guard: the winning layer composes (append), so
        resolution reads the base layer beneath it — here the core template,
        corrupted to non-UTF-8 — and must return None instead of crashing.
        """
        pack_data = {**valid_pack_data}
        pack_data["preset"] = {**valid_pack_data["preset"], "id": "append-pack", "name": "Append"}
        pack_data["provides"] = {
            "templates": [{
                "type": "template",
                "name": "spec-template",
                "file": "templates/spec-template.md",
                "strategy": "append",
            }]
        }
        pack_dir = temp_dir / "append-pack"
        pack_dir.mkdir()
        with open(pack_dir / "preset.yml", 'w') as f:
            yaml.dump(pack_data, f)
        (pack_dir / "templates").mkdir()
        (pack_dir / "templates" / "spec-template.md").write_text("## Appended Section\n")

        manager = PresetManager(project_dir)
        manager.install_from_directory(pack_dir, "0.1.5")

        core_spec = project_dir / ".specify" / "templates" / "spec-template.md"
        core_spec.write_bytes(b"\xff\xfe")

        resolver = PresetResolver(project_dir)
        assert resolver.resolve_content("spec-template") is None

    def test_resolve_content_unreadable_composing_layer(
        self, project_dir, temp_dir, valid_pack_data, monkeypatch
    ):
        """An unreadable composing layer over a valid base yields None.

        Covers the composition-loop read and the ``OSError`` half of the
        boundary: the base (core template) reads fine, but the append layer
        raises a mocked ``PermissionError`` — mocked so the case also holds
        under privileged CI where permission bits are not enforced.
        """
        pack_data = {**valid_pack_data}
        pack_data["preset"] = {**valid_pack_data["preset"], "id": "append-pack", "name": "Append"}
        pack_data["provides"] = {
            "templates": [{
                "type": "template",
                "name": "spec-template",
                "file": "templates/spec-template.md",
                "strategy": "append",
            }]
        }
        pack_dir = temp_dir / "append-pack"
        pack_dir.mkdir()
        with open(pack_dir / "preset.yml", 'w') as f:
            yaml.dump(pack_data, f)
        (pack_dir / "templates").mkdir()
        (pack_dir / "templates" / "spec-template.md").write_text("## Appended Section\n")

        manager = PresetManager(project_dir)
        manager.install_from_directory(pack_dir, "0.1.5")

        layer_path = (
            project_dir / ".specify" / "presets" / "append-pack"
            / "templates" / "spec-template.md"
        )
        assert layer_path.is_file()
        original_read_text = Path.read_text

        def failing_read_text(self_path, *args, **kwargs):
            if self_path == layer_path:
                raise PermissionError(13, "Permission denied")
            return original_read_text(self_path, *args, **kwargs)

        monkeypatch.setattr(Path, "read_text", failing_read_text)

        resolver = PresetResolver(project_dir)
        assert resolver.resolve_content("spec-template") is None

    def test_resolve_content_replace_strategy(self, project_dir, temp_dir, valid_pack_data):
        """Test resolve_content with default replace strategy."""
        manager = PresetManager(project_dir)
        manager.install_from_directory(
            _create_pack(temp_dir, valid_pack_data, "replace-pack",
                         "# Replaced Content\n"),
            "0.1.5"
        )

        resolver = PresetResolver(project_dir)
        content = resolver.resolve_content("spec-template")
        assert content is not None
        assert "Replaced Content" in content
        assert "Core Spec Template" not in content

    def test_resolve_content_append_strategy(self, project_dir, temp_dir, valid_pack_data):
        """Test resolve_content with append strategy."""
        pack_data = {**valid_pack_data}
        pack_data["preset"] = {**valid_pack_data["preset"], "id": "append-pack", "name": "Append"}
        pack_data["provides"] = {
            "templates": [{
                "type": "template",
                "name": "spec-template",
                "file": "templates/spec-template.md",
                "strategy": "append",
            }]
        }
        pack_dir = temp_dir / "append-pack"
        pack_dir.mkdir()
        with open(pack_dir / "preset.yml", 'w') as f:
            yaml.dump(pack_data, f)
        (pack_dir / "templates").mkdir()
        (pack_dir / "templates" / "spec-template.md").write_text("## Appended Section\n")

        manager = PresetManager(project_dir)
        manager.install_from_directory(pack_dir, "0.1.5")

        resolver = PresetResolver(project_dir)
        content = resolver.resolve_content("spec-template")
        assert content is not None
        assert "Core Spec Template" in content
        assert "Appended Section" in content
        # Core should come first, appended after
        assert content.index("Core Spec Template") < content.index("Appended Section")

    def test_resolve_content_prepend_strategy(self, project_dir, temp_dir, valid_pack_data):
        """Test resolve_content with prepend strategy."""
        pack_data = {**valid_pack_data}
        pack_data["preset"] = {**valid_pack_data["preset"], "id": "prepend-pack", "name": "Prepend"}
        pack_data["provides"] = {
            "templates": [{
                "type": "template",
                "name": "spec-template",
                "file": "templates/spec-template.md",
                "strategy": "prepend",
            }]
        }
        pack_dir = temp_dir / "prepend-pack"
        pack_dir.mkdir()
        with open(pack_dir / "preset.yml", 'w') as f:
            yaml.dump(pack_data, f)
        (pack_dir / "templates").mkdir()
        (pack_dir / "templates" / "spec-template.md").write_text("## Security Header\n")

        manager = PresetManager(project_dir)
        manager.install_from_directory(pack_dir, "0.1.5")

        resolver = PresetResolver(project_dir)
        content = resolver.resolve_content("spec-template")
        assert content is not None
        assert "Security Header" in content
        assert "Core Spec Template" in content
        # Prepended content should come first
        assert content.index("Security Header") < content.index("Core Spec Template")

    def test_resolve_content_wrap_strategy(self, project_dir, temp_dir, valid_pack_data):
        """Test resolve_content with wrap strategy for templates."""
        pack_data = {**valid_pack_data}
        pack_data["preset"] = {**valid_pack_data["preset"], "id": "wrap-pack", "name": "Wrap"}
        pack_data["provides"] = {
            "templates": [{
                "type": "template",
                "name": "spec-template",
                "file": "templates/spec-template.md",
                "strategy": "wrap",
            }]
        }
        pack_dir = temp_dir / "wrap-pack"
        pack_dir.mkdir()
        with open(pack_dir / "preset.yml", 'w') as f:
            yaml.dump(pack_data, f)
        (pack_dir / "templates").mkdir()
        (pack_dir / "templates" / "spec-template.md").write_text(
            "# Wrapper Start\n\n{CORE_TEMPLATE}\n\n# Wrapper End\n"
        )

        manager = PresetManager(project_dir)
        manager.install_from_directory(pack_dir, "0.1.5")

        resolver = PresetResolver(project_dir)
        content = resolver.resolve_content("spec-template")
        assert content is not None
        assert "Wrapper Start" in content
        assert "Core Spec Template" in content
        assert "Wrapper End" in content
        # Wrapper should surround core
        assert content.index("Wrapper Start") < content.index("Core Spec Template")
        assert content.index("Core Spec Template") < content.index("Wrapper End")

    def test_resolve_content_wrap_strategy_script(self, project_dir, temp_dir, valid_pack_data):
        """Test resolve_content with wrap strategy for scripts uses $CORE_SCRIPT."""
        # Create core script
        scripts_dir = project_dir / ".specify" / "templates" / "scripts"
        scripts_dir.mkdir(parents=True, exist_ok=True)
        (scripts_dir / "test-script.sh").write_text("echo 'core script'\n")

        pack_data = {**valid_pack_data}
        pack_data["preset"] = {**valid_pack_data["preset"], "id": "script-wrap", "name": "Script Wrap"}
        pack_data["provides"] = {
            "templates": [{
                "type": "script",
                "name": "test-script",
                "file": "scripts/test-script.sh",
                "strategy": "wrap",
            }]
        }
        pack_dir = temp_dir / "script-wrap"
        pack_dir.mkdir()
        with open(pack_dir / "preset.yml", 'w') as f:
            yaml.dump(pack_data, f)
        (pack_dir / "scripts").mkdir()
        (pack_dir / "scripts" / "test-script.sh").write_text(
            "#!/bin/bash\necho 'before'\n$CORE_SCRIPT\necho 'after'\n"
        )

        manager = PresetManager(project_dir)
        manager.install_from_directory(pack_dir, "0.1.5")

        resolver = PresetResolver(project_dir)
        content = resolver.resolve_content("test-script", "script")
        assert content is not None
        assert "echo 'before'" in content
        assert "echo 'core script'" in content
        assert "echo 'after'" in content

    def test_resolve_content_multi_preset_chain(self, project_dir, temp_dir, valid_pack_data):
        """Test multi-preset composition chain: prepend + append stacking."""
        # Create preset A (priority 1): prepend security header
        pack_a_data = {**valid_pack_data}
        pack_a_data["preset"] = {**valid_pack_data["preset"], "id": "preset-a", "name": "A"}
        pack_a_data["provides"] = {
            "templates": [{
                "type": "template",
                "name": "spec-template",
                "file": "templates/spec-template.md",
                "strategy": "prepend",
            }]
        }
        pack_a_dir = temp_dir / "preset-a"
        pack_a_dir.mkdir()
        with open(pack_a_dir / "preset.yml", 'w') as f:
            yaml.dump(pack_a_data, f)
        (pack_a_dir / "templates").mkdir()
        (pack_a_dir / "templates" / "spec-template.md").write_text("## Security Header\n")

        # Create preset B (priority 2): append compliance footer
        pack_b_data = {**valid_pack_data}
        pack_b_data["preset"] = {**valid_pack_data["preset"], "id": "preset-b", "name": "B"}
        pack_b_data["provides"] = {
            "templates": [{
                "type": "template",
                "name": "spec-template",
                "file": "templates/spec-template.md",
                "strategy": "append",
            }]
        }
        pack_b_dir = temp_dir / "preset-b"
        pack_b_dir.mkdir()
        with open(pack_b_dir / "preset.yml", 'w') as f:
            yaml.dump(pack_b_data, f)
        (pack_b_dir / "templates").mkdir()
        (pack_b_dir / "templates" / "spec-template.md").write_text("## Compliance Footer\n")

        manager = PresetManager(project_dir)
        manager.install_from_directory(pack_a_dir, "0.1.5", priority=1)
        manager.install_from_directory(pack_b_dir, "0.1.5", priority=2)

        resolver = PresetResolver(project_dir)
        content = resolver.resolve_content("spec-template")
        assert content is not None
        # Result: <security header> + <core> + <compliance footer>
        assert "Security Header" in content
        assert "Core Spec Template" in content
        assert "Compliance Footer" in content
        assert content.index("Security Header") < content.index("Core Spec Template")
        assert content.index("Core Spec Template") < content.index("Compliance Footer")

    def test_resolve_content_override_trumps_composition(self, project_dir, temp_dir, valid_pack_data):
        """Test that project overrides trump composition (replace at top priority)."""
        # Install a composing preset
        pack_data = {**valid_pack_data}
        pack_data["preset"] = {**valid_pack_data["preset"], "id": "append-pack", "name": "Append"}
        pack_data["provides"] = {
            "templates": [{
                "type": "template",
                "name": "spec-template",
                "file": "templates/spec-template.md",
                "strategy": "append",
            }]
        }
        pack_dir = temp_dir / "append-pack"
        pack_dir.mkdir()
        with open(pack_dir / "preset.yml", 'w') as f:
            yaml.dump(pack_data, f)
        (pack_dir / "templates").mkdir()
        (pack_dir / "templates" / "spec-template.md").write_text("## Appended\n")

        manager = PresetManager(project_dir)
        manager.install_from_directory(pack_dir, "0.1.5")

        # Create project override (replaces everything)
        overrides_dir = project_dir / ".specify" / "templates" / "overrides"
        overrides_dir.mkdir(parents=True)
        (overrides_dir / "spec-template.md").write_text("# Override Only\n")

        resolver = PresetResolver(project_dir)
        content = resolver.resolve_content("spec-template")
        assert content is not None
        assert "Override Only" in content
        # Override replaces, so appended content should not be visible
        assert "Core Spec Template" not in content

    def test_resolve_content_command_type(self, project_dir, temp_dir, valid_pack_data):
        """Test resolve_content with command template type."""
        # Create core command using stem naming (matches real layout: plan.md, not speckit.plan.md)
        commands_dir = project_dir / ".specify" / "templates" / "commands"
        commands_dir.mkdir(parents=True, exist_ok=True)
        (commands_dir / "plan.md").write_text("# Core Plan Command\n")

        pack_data = {**valid_pack_data}
        pack_data["preset"] = {**valid_pack_data["preset"], "id": "cmd-append", "name": "CmdAppend"}
        pack_data["provides"] = {
            "templates": [{
                "type": "command",
                "name": "speckit.plan",
                "file": "commands/speckit.plan.md",
                "strategy": "append",
            }]
        }
        pack_dir = temp_dir / "cmd-append"
        pack_dir.mkdir()
        with open(pack_dir / "preset.yml", 'w') as f:
            yaml.dump(pack_data, f)
        (pack_dir / "commands").mkdir()
        (pack_dir / "commands" / "speckit.plan.md").write_text("## Additional Instructions\n")

        manager = PresetManager(project_dir)
        manager.install_from_directory(pack_dir, "0.1.5")

        resolver = PresetResolver(project_dir)
        content = resolver.resolve_content("speckit.plan", "command")
        assert content is not None
        assert "Core Plan Command" in content
        assert "Additional Instructions" in content

    def test_resolve_content_command_frontmatter_stripping(self, project_dir, temp_dir, valid_pack_data):
        """Test that command composition strips frontmatter from lower layers
        and reattaches only the highest-priority frontmatter."""
        # Create core command with frontmatter
        commands_dir = project_dir / ".specify" / "templates" / "commands"
        commands_dir.mkdir(parents=True, exist_ok=True)
        (commands_dir / "check.md").write_text(
            "---\ndescription: Core check command\n---\nCore body content\n"
        )

        pack_data = {**valid_pack_data}
        pack_data["preset"] = {**valid_pack_data["preset"], "id": "fm-test", "name": "FmTest"}
        pack_data["provides"] = {
            "templates": [{
                "type": "command",
                "name": "speckit.check",
                "file": "commands/speckit.check.md",
                "strategy": "append",
            }]
        }
        pack_dir = temp_dir / "fm-test"
        pack_dir.mkdir()
        with open(pack_dir / "preset.yml", 'w') as f:
            yaml.dump(pack_data, f)
        (pack_dir / "commands").mkdir()
        (pack_dir / "commands" / "speckit.check.md").write_text(
            "---\ndescription: Preset check override\n---\nPreset body content\n"
        )

        manager = PresetManager(project_dir)
        manager.install_from_directory(pack_dir, "0.1.5")

        resolver = PresetResolver(project_dir)
        content = resolver.resolve_content("speckit.check", "command")
        assert content is not None
        # Should have the preset (highest-priority) frontmatter
        assert "Preset check override" in content
        # Should have both bodies
        assert "Core body content" in content
        assert "Preset body content" in content
        # Core frontmatter should NOT appear in the body
        assert content.count("---") == 2  # only one frontmatter block (opening + closing)

    def test_resolve_content_blank_line_separator(self, project_dir, temp_dir, valid_pack_data):
        """Test that prepend/append use blank line separator."""
        pack_data = {**valid_pack_data}
        pack_data["preset"] = {**valid_pack_data["preset"], "id": "sep-test", "name": "SepTest"}
        pack_data["provides"] = {
            "templates": [{
                "type": "template",
                "name": "spec-template",
                "file": "templates/spec-template.md",
                "strategy": "append",
            }]
        }
        pack_dir = temp_dir / "sep-test"
        pack_dir.mkdir()
        with open(pack_dir / "preset.yml", 'w') as f:
            yaml.dump(pack_data, f)
        (pack_dir / "templates").mkdir()
        (pack_dir / "templates" / "spec-template.md").write_text("appended")

        manager = PresetManager(project_dir)
        manager.install_from_directory(pack_dir, "0.1.5")

        resolver = PresetResolver(project_dir)
        content = resolver.resolve_content("spec-template")
        # Should have blank line separator
        assert "\n\n" in content

    def test_resolve_content_replace_over_wrap(self, project_dir, temp_dir, valid_pack_data):
        """Top-priority replace layer should win even if a lower layer uses wrap."""
        # Install a low-priority wrap preset (with no placeholder — would fail if evaluated)
        wrap_data = {**valid_pack_data}
        wrap_data["preset"] = {**valid_pack_data["preset"], "id": "wrap-lo", "name": "WrapLo"}
        wrap_data["provides"] = {
            "templates": [{
                "type": "template",
                "name": "spec-template",
                "file": "templates/spec-template.md",
                "strategy": "wrap",
            }]
        }
        wrap_dir = temp_dir / "wrap-lo"
        wrap_dir.mkdir()
        with open(wrap_dir / "preset.yml", "w") as f:
            yaml.dump(wrap_data, f)
        (wrap_dir / "templates").mkdir()
        # Intentionally missing {CORE_TEMPLATE} — would error if composition ran
        (wrap_dir / "templates" / "spec-template.md").write_text("wrapper without placeholder")

        manager = PresetManager(project_dir)
        manager.install_from_directory(wrap_dir, "0.1.5", priority=10)

        # Install a high-priority replace preset
        rep_data = {**valid_pack_data}
        rep_data["preset"] = {**valid_pack_data["preset"], "id": "rep-hi", "name": "RepHi"}
        rep_data["provides"] = {
            "templates": [{
                "type": "template",
                "name": "spec-template",
                "file": "templates/spec-template.md",
            }]
        }
        rep_dir = temp_dir / "rep-hi"
        rep_dir.mkdir()
        with open(rep_dir / "preset.yml", "w") as f:
            yaml.dump(rep_data, f)
        (rep_dir / "templates").mkdir()
        (rep_dir / "templates" / "spec-template.md").write_text("# Replaced content\n")

        manager.install_from_directory(rep_dir, "0.1.5", priority=1)

        resolver = PresetResolver(project_dir)
        content = resolver.resolve_content("spec-template")
        assert content == "# Replaced content\n"

    @pytest.mark.parametrize("strategy", ["append", "prepend", "wrap"])
    def test_resolve_content_rewrites_extension_base_subdir_paths(
        self, project_dir, temp_dir, strategy
    ):
        """Composing over an extension-provided base command must resolve the
        extension's own subdir references (agents/, knowledge-base/) to their
        installed location (#2101), not just when the extension wins outright.
        """
        extension_dir = project_dir / ".specify" / "extensions" / "fakeext"
        (extension_dir / "commands").mkdir(parents=True, exist_ok=True)
        (extension_dir / "agents" / "control").mkdir(parents=True, exist_ok=True)
        (extension_dir / "agents" / "control" / "commander.md").write_text("# Commander\n")
        (extension_dir / "commands" / "cmd.md").write_text(
            "---\ndescription: Extension fakeext cmd\n---\n\n"
            "Read agents/control/commander.md for context.\n"
        )
        extension_manifest = {
            "schema_version": "1.0",
            "extension": {
                "id": "fakeext",
                "name": "Fake Extension",
                "version": "1.0.0",
                "description": "Test",
            },
            "requires": {"speckit_version": ">=0.1.0"},
            "provides": {
                "commands": [
                    {
                        "name": "speckit.fakeext.cmd",
                        "file": "commands/cmd.md",
                        "description": "Fake extension command",
                    }
                ]
            },
        }
        with open(extension_dir / "extension.yml", "w") as f:
            yaml.dump(extension_manifest, f)

        preset_dir = temp_dir / f"ext-base-{strategy}"
        preset_dir.mkdir()
        (preset_dir / "commands").mkdir()
        overlay_body = (
            "{CORE_TEMPLATE}\n## Extra\n" if strategy == "wrap" else "## Extra\n"
        )
        (preset_dir / "commands" / "speckit.fakeext.cmd.md").write_text(
            f"---\ndescription: Preset overlay\n---\n\n{overlay_body}"
        )
        preset_manifest = {
            "schema_version": "1.0",
            "preset": {
                "id": f"ext-base-{strategy}",
                "name": "Ext Base",
                "version": "1.0.0",
                "description": "Test",
            },
            "requires": {"speckit_version": ">=0.1.0"},
            "provides": {
                "templates": [
                    {
                        "type": "command",
                        "name": "speckit.fakeext.cmd",
                        "file": "commands/speckit.fakeext.cmd.md",
                        "strategy": strategy,
                    }
                ]
            },
        }
        with open(preset_dir / "preset.yml", "w") as f:
            yaml.dump(preset_manifest, f)

        manager = PresetManager(project_dir)
        manager.install_from_directory(preset_dir, "0.1.5")

        resolver = PresetResolver(project_dir)
        content = resolver.resolve_content("speckit.fakeext.cmd", "command")
        assert content is not None
        assert ".specify/extensions/fakeext/agents/control/commander.md" in content
        assert "Read agents/control" not in content
        assert "## Extra" in content


class TestCollectAllLayers:
    """Test PresetResolver.collect_all_layers() method."""

    def test_non_utf8_legacy_command_keeps_replace_strategy(self, project_dir):
        presets_dir = project_dir / ".specify" / "presets"
        command_path = (
            presets_dir / "legacy-pack" / "commands" / "speckit.legacy.md"
        )
        command_path.parent.mkdir(parents=True)
        command_path.write_bytes(b"\xff\xfe")
        PresetRegistry(presets_dir).add(
            "legacy-pack", {"version": "1.0.0", "priority": 10}
        )

        layers = PresetResolver(project_dir).collect_all_layers(
            "speckit.legacy", "command"
        )

        assert layers[0]["path"] == command_path
        assert layers[0]["strategy"] == "replace"

    def test_single_core_layer(self, project_dir):
        """Test collecting layers with only core template."""
        resolver = PresetResolver(project_dir)
        layers = resolver.collect_all_layers("spec-template")
        assert len(layers) == 1
        assert layers[0]["source"] == "core"
        assert layers[0]["strategy"] == "replace"

    def test_layers_include_presets(self, project_dir, temp_dir, valid_pack_data):
        """Test that layers include installed preset."""
        manager = PresetManager(project_dir)
        pack_dir = _create_pack(temp_dir, valid_pack_data, "test-pack",
                                "# From Pack\n")
        manager.install_from_directory(pack_dir, "0.1.5")

        resolver = PresetResolver(project_dir)
        layers = resolver.collect_all_layers("spec-template")
        assert len(layers) == 2
        # Highest priority first
        assert "test-pack" in layers[0]["source"]
        assert layers[1]["source"] == "core"

    def test_layers_order_matches_priority(self, project_dir, temp_dir, valid_pack_data):
        """Test that layers are ordered by priority (highest first)."""
        manager = PresetManager(project_dir)
        for pid, prio in [("pack-lo", 10), ("pack-hi", 1)]:
            d = {**valid_pack_data}
            d["preset"] = {**valid_pack_data["preset"], "id": pid, "name": pid}
            p = temp_dir / pid
            p.mkdir()
            with open(p / "preset.yml", 'w') as f:
                yaml.dump(d, f)
            (p / "templates").mkdir()
            (p / "templates" / "spec-template.md").write_text(f"# {pid}\n")
            manager.install_from_directory(p, "0.1.5", priority=prio)

        resolver = PresetResolver(project_dir)
        layers = resolver.collect_all_layers("spec-template")
        assert len(layers) == 3  # pack-hi, pack-lo, core
        assert "pack-hi" in layers[0]["source"]
        assert "pack-lo" in layers[1]["source"]
        assert layers[2]["source"] == "core"

    def test_layers_read_strategy_from_manifest(self, project_dir, temp_dir, valid_pack_data):
        """Test that layers read strategy from preset manifest."""
        pack_data = {**valid_pack_data}
        pack_data["preset"] = {**valid_pack_data["preset"], "id": "strat-pack", "name": "Strat"}
        pack_data["provides"] = {
            "templates": [{
                "type": "template",
                "name": "spec-template",
                "file": "templates/spec-template.md",
                "strategy": "append",
            }]
        }
        pack_dir = temp_dir / "strat-pack"
        pack_dir.mkdir()
        with open(pack_dir / "preset.yml", 'w') as f:
            yaml.dump(pack_data, f)
        (pack_dir / "templates").mkdir()
        (pack_dir / "templates" / "spec-template.md").write_text("## Footer\n")

        manager = PresetManager(project_dir)
        manager.install_from_directory(pack_dir, "0.1.5")

        resolver = PresetResolver(project_dir)
        layers = resolver.collect_all_layers("spec-template")
        # Preset layer should have strategy=append
        assert layers[0]["strategy"] == "append"
        # Core layer should be replace
        assert layers[1]["strategy"] == "replace"


def _create_pack(temp_dir, valid_pack_data, pack_id, content,
                 strategy="replace", template_type="template",
                 template_name="spec-template"):
    """Helper to create a preset pack directory."""
    pack_data = {**valid_pack_data}
    pack_data["preset"] = {**valid_pack_data["preset"], "id": pack_id, "name": pack_id}

    tmpl_entry = {
        "type": template_type,
        "name": template_name,
    }
    if template_type == "script":
        tmpl_entry["file"] = f"scripts/{template_name}.sh"
    elif template_type == "command":
        tmpl_entry["file"] = f"commands/{template_name}.md"
    else:
        tmpl_entry["file"] = f"templates/{template_name}.md"
    if strategy != "replace":
        tmpl_entry["strategy"] = strategy
    pack_data["provides"] = {"templates": [tmpl_entry]}

    pack_dir = temp_dir / pack_id
    pack_dir.mkdir(exist_ok=True)
    with open(pack_dir / "preset.yml", 'w') as f:
        yaml.dump(pack_data, f)

    if template_type == "script":
        subdir = pack_dir / "scripts"
        subdir.mkdir(exist_ok=True)
        (subdir / f"{template_name}.sh").write_text(content)
    elif template_type == "command":
        subdir = pack_dir / "commands"
        subdir.mkdir(exist_ok=True)
        (subdir / f"{template_name}.md").write_text(content)
    else:
        subdir = pack_dir / "templates"
        subdir.mkdir(exist_ok=True)
        (subdir / f"{template_name}.md").write_text(content)

    return pack_dir


def test_command_regex_matches_core_resource_only(project_dir):
    write_selector_preset(
        project_dir,
        "regex-pack",
        "regex:^speckit\.plan$",
        priority=10,
        strategy="append",
    )
    layers = PresetResolver(project_dir).collect_all_layers("speckit.plan", "command")
    assert any(layer["source"].startswith("regex-pack") for layer in layers)
    assert (
        PresetResolver(project_dir).collect_all_layers("does-not-exist", "command")
        == []
    )


def test_command_regex_matches_extension_resource(project_dir):
    ext = project_dir / ".specify" / "extensions" / "demo"
    (ext / "templates" / "commands").mkdir(parents=True)
    (ext / "templates" / "commands" / "speckit.plan.md").write_text(
        "extension base\n", encoding="utf-8"
    )
    write_selector_preset(
        project_dir,
        "regex-pack",
        "regex:^speckit\.plan$",
        priority=10,
        strategy="append",
    )
    layers = PresetResolver(project_dir).collect_all_layers("speckit.plan", "command")
    assert any(layer["source"].startswith("regex-pack") for layer in layers)


def test_command_regex_matches_lower_priority_preset(project_dir):
    write_selector_preset(
        project_dir, "high", "regex:^speckit\.plan$", priority=1, strategy="append"
    )
    write_selector_preset(project_dir, "low", "speckit.plan", priority=10)
    layers = PresetResolver(project_dir).collect_all_layers("speckit.plan", "command")
    assert any(layer["source"].startswith("high") for layer in layers)
    assert any(layer["source"].startswith("low") for layer in layers)


def test_regex_does_not_match_higher_preset_or_create_resource(project_dir):
    write_selector_preset(project_dir, "higher", "only-higher", priority=1)
    write_selector_preset(project_dir, "lower", "regex:^only-higher$", priority=10)
    resolver = PresetResolver(project_dir)
    layers = resolver.collect_all_layers("only-higher", "command")
    assert any(layer["source"].startswith("higher") for layer in layers)
    assert not any(layer["source"].startswith("lower") for layer in layers)
    assert resolver.collect_all_layers("does-not-exist", "command") == []
    assert resolver.collect_all_layers("regex:^only-higher$", "command") == []


def test_same_priority_regex_layers_follow_preset_id_order(project_dir):
    # Registry tie-break is alphabetical ID; both selectors match the same core command.
    write_selector_preset(
        project_dir,
        "zeta-regex",
        "regex:^speckit.plan$",
        priority=10,
        strategy="append",
        body="zeta\n",
    )
    write_selector_preset(
        project_dir,
        "alpha-regex",
        "regex:^speckit.plan$",
        priority=10,
        strategy="append",
        body="alpha\n",
    )
    layers = PresetResolver(project_dir).collect_all_layers("speckit.plan", "command")
    regex_sources = [
        layer["source"].split()[0] for layer in layers if "-regex" in layer["source"]
    ]
    assert regex_sources == ["alpha-regex", "zeta-regex"]


def test_project_override_is_not_regex_lower_layer_proof(project_dir):
    overrides = project_dir / ".specify" / "templates" / "overrides"
    overrides.mkdir(parents=True)
    (overrides / "speckit.foo.md").write_text("override\n", encoding="utf-8")
    write_selector_preset(
        project_dir,
        "regex-pack",
        "regex:^speckit.foo$",
        priority=10,
        strategy="append",
    )
    resolver = PresetResolver(project_dir)
    layers = resolver.collect_all_layers("speckit.foo", "command")
    assert [layer["source"] for layer in layers] == ["project override"]


def test_project_override_does_not_hide_real_regex_lower_layer(project_dir):
    overrides = project_dir / ".specify" / "templates" / "overrides"
    overrides.mkdir(parents=True)
    (overrides / "speckit.foo.md").write_text("override\n", encoding="utf-8")
    write_selector_preset(
        project_dir,
        "regex-pack",
        "regex:^speckit.foo$",
        priority=10,
        strategy="append",
    )
    core = project_dir / ".specify" / "templates" / "commands" / "speckit.foo.md"
    core.parent.mkdir(parents=True, exist_ok=True)
    core.write_text("core\n", encoding="utf-8")
    layers = PresetResolver(project_dir).collect_all_layers("speckit.foo", "command")
    assert [layer["source"] for layer in layers] == [
        "project override",
        "regex-pack v1.0.0",
        "core",
    ]


def test_exact_and_regex_layers_keep_existing_priority_composition(project_dir):
    write_selector_preset(
        project_dir,
        "higher-regex",
        "regex:^speckit.plan$",
        priority=1,
        strategy="append",
        body="A\n",
    )
    write_selector_preset(
        project_dir,
        "higher-exact",
        "speckit.plan",
        priority=2,
        strategy="prepend",
        body="B\n",
    )
    resolver = PresetResolver(project_dir)
    layers = resolver.collect_all_layers("speckit.plan", "command")
    assert [layer["source"].split(" ")[0] for layer in layers[:2]] == [
        "higher-regex",
        "higher-exact",
    ]
    result = resolver.resolve_content("speckit.plan", "command")
    assert result is not None and "A" in result and "B" in result


def test_zero_match_is_non_fatal_and_has_no_layer(project_dir):
    write_selector_preset(project_dir, "no-match", "regex:^missing-resource$", priority=10)
    assert (
        PresetResolver(project_dir).collect_all_layers("missing-resource", "command")
        == []
    )


def _name(resource_type):
    return (
        "speckit.selector-contract"
        if resource_type == "command"
        else "selector-contract"
    )


def _assert_parity(
    resolver, name, resource_type, expected_paths, expected_sources, content
):
    layers = resolver.collect_all_layers(name, resource_type)
    assert [layer["path"] for layer in layers] == expected_paths
    assert [layer["source"] for layer in layers] == expected_sources
    assert resolver.resolve(name, resource_type) == expected_paths[0]
    assert resolver.resolve_with_source(name, resource_type) == {
        "path": str(expected_paths[0]),
        "source": expected_sources[0],
    }
    assert resolver.resolve_content(name, resource_type) == content


@pytest.mark.parametrize("resource_type", ["command"])
@pytest.mark.parametrize("order", ["regex-exact", "exact-regex", "regex-regex"])
def test_overlapping_declarations_share_manifest_order(tmp_path, resource_type, order):
    name = _name(resource_type)
    regex = f"regex:{re.escape(name)}"
    names = {
        "regex-exact": [regex, name],
        "exact-regex": [name, regex],
        "regex-regex": [regex, f"regex:^{re.escape(name)}$"],
    }[order]
    pack = write_selector_contract_preset(
        tmp_path,
        "selector",
        [
            (entry, resource_type, "replace", f"body-{index}")
            for index, entry in enumerate(names)
        ],
    )
    lower = write_selector_contract_preset(
        tmp_path, "lower", [(name, resource_type, "replace", "base")], 10
    )
    suffix = "sh" if resource_type == "script" else "md"
    _assert_parity(
        PresetResolver(tmp_path),
        name,
        resource_type,
        [
            pack / f"payload-0.{suffix}",
            pack / f"payload-1.{suffix}",
            lower / f"payload-0.{suffix}",
        ],
        ["selector v1.0.0", "selector v1.0.0", "lower v1.0.0"],
        "body-0",
    )


@pytest.mark.parametrize("resource_type", ["command"])
@pytest.mark.parametrize("regex_first", [True, False])
def test_exact_and_regex_compose_over_lower_without_deduplication(
    tmp_path, resource_type, regex_first
):
    name = _name(resource_type)
    names = [f"regex:{re.escape(name)}", name]
    if not regex_first:
        names.reverse()
    placeholder = "$CORE_SCRIPT" if resource_type == "script" else "{CORE_TEMPLATE}"
    pack = write_selector_contract_preset(
        tmp_path,
        "selector",
        [
            (entry, resource_type, "wrap", f"layer-{index}[{placeholder}]")
            for index, entry in enumerate(names)
        ],
    )
    lower = write_selector_contract_preset(
        tmp_path, "lower", [(name, resource_type, "replace", "base")], 10
    )
    suffix = "sh" if resource_type == "script" else "md"
    _assert_parity(
        PresetResolver(tmp_path),
        name,
        resource_type,
        [
            pack / f"payload-0.{suffix}",
            pack / f"payload-1.{suffix}",
            lower / f"payload-0.{suffix}",
        ],
        ["selector v1.0.0", "selector v1.0.0", "lower v1.0.0"],
        "layer-0[layer-1[base]]",
    )


@pytest.mark.parametrize("overlap", ["regex-exact", "regex-regex"])
def test_overlaps_using_the_same_file_are_not_deduplicated(tmp_path, overlap):
    name = _name("command")
    pack = write_selector_contract_preset(
        tmp_path,
        "selector",
        [
            (f"regex:{name}", "command", "wrap", "overlay[{CORE_TEMPLATE}]"),
            (
                name if overlap == "regex-exact" else f"regex:^{name}$",
                "command",
                "wrap",
                "unused",
            ),
        ],
    )
    manifest_path = pack / "preset.yml"
    data = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    data["provides"]["templates"][1]["file"] = "payload-0.md"
    manifest_path.write_text(yaml.safe_dump(data), encoding="utf-8")
    lower = write_selector_contract_preset(tmp_path, "lower", [(name, "command", "replace", "base")], 10)
    _assert_parity(
        PresetResolver(tmp_path),
        name,
        "command",
        [pack / "payload-0.md", pack / "payload-0.md", lower / "payload-0.md"],
        ["selector v1.0.0", "selector v1.0.0", "lower v1.0.0"],
        "overlay[overlay[base]]",
    )


@pytest.mark.parametrize("missing", ["exact", "regex", "both"])
def test_unusable_declarations_skip_to_the_first_usable_layer(tmp_path, missing):
    name = _name("command")
    pack = write_selector_contract_preset(
        tmp_path,
        "selector",
        [
            (
                name,
                "command",
                "replace",
                None if missing in {"exact", "both"} else "exact",
            ),
            (
                f"regex:{name}",
                "command",
                "replace",
                None if missing in {"regex", "both"} else "regex",
            ),
        ],
    )
    # A matching declaration still prevents a stray conventional file winning.
    (pack / f"{name}.md").write_text("stray", encoding="utf-8")
    lower = write_selector_contract_preset(tmp_path, "lower", [(name, "command", "replace", "base")], 10)
    paths, sources = [], []
    if missing not in {"exact", "both"}:
        paths.append(pack / "payload-0.md")
        sources.append("selector v1.0.0")
    if missing not in {"regex", "both"}:
        paths.append(pack / "payload-1.md")
        sources.append("selector v1.0.0")
    paths.append(lower / "payload-0.md")
    sources.append("lower v1.0.0")
    content = {"exact": "regex", "regex": "exact", "both": "base"}[missing]
    _assert_parity(PresetResolver(tmp_path), name, "command", paths, sources, content)


def test_own_exact_declaration_does_not_make_regex_eligible(tmp_path):
    name = _name("command")
    pack = write_selector_contract_preset(
        tmp_path,
        "selector",
        [
            (f"regex:{name}", "command", "replace", "ineligible"),
            (name, "command", "replace", "exact"),
        ],
    )
    _assert_parity(
        PresetResolver(tmp_path),
        name,
        "command",
        [pack / "payload-1.md"],
        ["selector v1.0.0"],
        "exact",
    )


INVALID_PATTERNS = [
    pytest.param("[unterminated", re.error, id="grammar"),
    pytest.param("a{999999999999999999999}", OverflowError, id="huge-repetition"),
    pytest.param("(" * 2000 + "a" + ")" * 2000, RecursionError, id="deep-nesting"),
]


@pytest.mark.parametrize("pattern,compile_error", INVALID_PATTERNS)
def test_malformed_selector_manifest_warns_once_but_unrelated_invalid_manifest_is_silent(
    tmp_path, monkeypatch, pattern, compile_error
):
    from specify_cli.presets import _resolver

    malformed = write_selector_contract_preset(
        tmp_path, "malformed", [(f"regex:{pattern}", "command", "replace", "bad")]
    )
    errors = {}

    def capture_validation_error(path):
        try:
            return PresetManifest(path)
        except PresetValidationError as exc:
            errors[path] = exc
            raise

    monkeypatch.setattr(_resolver, "PresetManifest", capture_validation_error)
    invalid = write_selector_contract_preset(tmp_path, "invalid", [])
    (invalid / "preset.yml").write_text("schema_version: invalid\n", encoding="utf-8")
    resolver = PresetResolver(tmp_path)

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        assert resolver._get_manifest(malformed) is None
        assert resolver._get_manifest(malformed) is None
        assert resolver._get_manifest(invalid) is None

    assert len(caught) == 1
    error = errors[malformed / "preset.yml"]
    assert isinstance(error.__cause__, compile_error)
    assert str(malformed / "preset.yml") in str(caught[0].message)
    assert str(error) in str(caught[0].message)


def test_exact_command_resolves_without_consulting_corrupt_extension_registry(tmp_path, monkeypatch):
    name = "speckit.exact"
    pack = write_selector_contract_preset(
        tmp_path, "exact", [(name, "command", "replace", "EXACT BODY")]
    )
    extensions = tmp_path / ".specify" / "extensions"
    extensions.mkdir()
    (extensions / ".registry").write_text("{broken", encoding="utf-8")
    resolver = PresetResolver(tmp_path)
    assert resolver.resolve(name, "command") == pack / "payload-0.md"

    def unexpected_scan():
        pytest.fail("Exact declarations must not scan extensions")

    monkeypatch.setattr(resolver, "_get_all_extensions_by_priority", unexpected_scan)
    assert resolver.resolve(name, "command") == pack / "payload-0.md"


@pytest.mark.parametrize(
    "location,eligible",
    [("commands", True), ("templates/commands", True), ("templates/templates/commands", False)],
)
def test_extension_conventional_command_locations_agree_with_selector_candidates(
    tmp_path, location, eligible
):
    from specify_cli.presets._resolver import _conventional_command_names

    name = "speckit.target.collect"
    body = _extension(tmp_path, "target", f"{location}/{name}.md")
    resolver = PresetResolver(tmp_path)
    extension = resolver.extensions_dir / "target"

    assert (name in _conventional_command_names(extension)) is eligible
    assert resolver.resolve(name, "command") == (body if eligible else None)
    assert resolver._extension_has_concrete_resource(extension, name, "command") is eligible


@pytest.mark.parametrize("pattern,compile_error", INVALID_PATTERNS)
def test_installed_malformed_selector_is_isolated_from_healthy_presets(
    tmp_path, pattern, compile_error
):
    name = _name("command")
    write_selector_contract_preset(
        tmp_path, "malformed", [(f"regex:{pattern}", "command", "replace", "bad")]
    )
    healthy = write_selector_contract_preset(
        tmp_path, "healthy", [(name, "command", "replace", "healthy")], 10
    )
    installed = {
        entry["id"]: entry for entry in PresetManager(tmp_path).list_installed()
    }
    assert set(installed) == {"malformed", "healthy"}
    assert installed["malformed"]["description"] == "⚠️ Corrupted preset"
    assert installed["malformed"]["enabled"] is False
    assert installed["healthy"]["enabled"] is True
    _assert_parity(
        PresetResolver(tmp_path),
        name,
        "command",
        [healthy / "payload-0.md"],
        ["healthy v1.0.0"],
        "healthy",
    )


def _extension(project_dir, extension_id, filename, *, declared=False):
    root = project_dir / ".specify" / "extensions" / extension_id
    candidate = root / filename
    candidate.parent.mkdir(parents=True, exist_ok=True)
    candidate.write_text(f"# {extension_id} base\n", encoding="utf-8")
    if declared:
        (root / "extension.yml").write_text(
            yaml.safe_dump(
                {
                    "schema_version": "1.0",
                    "extension": {
                        "id": extension_id,
                        "name": extension_id,
                        "version": "1.0.0",
                        "description": "resolver fixture",
                    },
                    "requires": {"speckit_version": ">=0.1.0"},
                    "provides": {
                        "commands": [
                            {
                                "name": "speckit.target.collect",
                                "file": filename,
                                "description": "collect",
                            }
                        ]
                    },
                }
            ),
            encoding="utf-8",
        )
    return candidate


def _preset(project_dir, preset_id, declarations, *, priority=1):
    root = project_dir / ".specify" / "presets" / preset_id
    root.mkdir(parents=True, exist_ok=True)
    (root / "payload.md").write_text("overlay\n", encoding="utf-8")
    (root / "preset.yml").write_text(
        yaml.safe_dump(
            {
                "schema_version": "1.0",
                "preset": {
                    "id": preset_id,
                    "name": preset_id,
                    "version": "1.0.0",
                    "description": "resolver fixture",
                },
                "requires": {"speckit_version": ">=0.1.0"},
                "provides": {"templates": declarations},
            }
        ),
        encoding="utf-8",
    )
    PresetRegistry(root.parent).add(
        preset_id, {"version": "1.0.0", "priority": priority, "enabled": True}
    )
    return root / "payload.md"


@pytest.mark.parametrize("registered", [False, True])
@pytest.mark.parametrize(
    "filename,declared",
    [
        ("commands/target.collect.md", False),
        ("templates/commands/target.collect.md", False),
        ("commands/actual.md", True),
        ("commands/speckit.target.collect.md", False),
    ],
)
def test_each_extension_candidate_is_emitted_once_with_own_attribution(
    project_dir, registered, filename, declared
):
    candidate = _extension(project_dir, "target", filename, declared=declared)
    # An earlier unrelated orphan must not discover target's namespace fallback.
    unrelated = project_dir / ".specify" / "extensions" / "aaa-orphan"
    unrelated.mkdir()
    if registered:
        ExtensionRegistry(project_dir / ".specify" / "extensions").add(
            "target", {"enabled": True, "version": "1.0.0", "priority": 20}
        )
    resolver = PresetResolver(project_dir)
    layers = resolver.collect_all_layers("speckit.target.collect", "command")
    assert len(layers) == 1
    assert layers[0]["path"] == candidate
    assert layers[0]["extension_id"] == "target"
    assert layers[0]["extension_dir"] == (
        project_dir / ".specify" / "extensions" / "target"
    )
    assert layers[0]["source"] == (
        "extension:target v1.0.0" if registered else "extension:target (unregistered)"
    )
    assert resolver.resolve("speckit.target.collect", "command") == candidate
    assert (
        resolver.resolve_content("speckit.target.collect", "command")
        == "# target base\n"
    )


@pytest.mark.parametrize("declared", [False, True])
def test_disabled_namespace_is_never_revived_by_unrelated_extension(
    project_dir, declared
):
    _extension(project_dir, "target", "commands/target.collect.md", declared=declared)
    (project_dir / ".specify" / "extensions" / "aaa-orphan").mkdir()
    registry = ExtensionRegistry(project_dir / ".specify" / "extensions")
    registry.add("target", {"enabled": False, "version": "1.0.0"})
    resolver = PresetResolver(project_dir)
    assert resolver.collect_all_layers("speckit.target.collect", "command") == []
    assert resolver.resolve("speckit.target.collect", "command") is None
    assert resolver.resolve_content("speckit.target.collect", "command") is None


@pytest.mark.parametrize("template_type", ["command", "template", "script"])
def test_missing_manifest_command_never_falls_back_to_legacy_file(
    project_dir, template_type
):
    candidate = _extension(
        project_dir, "target", "commands/target.collect.md", declared=True
    )
    manifest_path = candidate.parents[1] / "extension.yml"
    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    manifest["provides"]["commands"][0]["file"] = "commands/missing.md"
    manifest_path.write_text(yaml.safe_dump(manifest), encoding="utf-8")
    resolver = PresetResolver(project_dir)
    assert resolver.collect_all_layers("speckit.target.collect", template_type) == []
    assert resolver.resolve("speckit.target.collect", template_type) is None


@pytest.mark.parametrize("template_type", ["template", "script"])
def test_legacy_command_is_not_a_template_or_script_layer(project_dir, template_type):
    _extension(project_dir, "target", "commands/target.collect.md")
    resolver = PresetResolver(project_dir)
    assert resolver.collect_all_layers("speckit.target.collect", template_type) == []
    assert resolver.resolve("speckit.target.collect", template_type) is None
    assert resolver.resolve_content("speckit.target.collect", template_type) is None


@pytest.mark.parametrize("enabled", [False, True])
def test_regex_eligibility_uses_enabled_legacy_namespace_base(project_dir, enabled):
    candidate = _extension(project_dir, "target", "commands/target.collect.md")
    ExtensionRegistry(project_dir / ".specify" / "extensions").add(
        "target", {"enabled": enabled, "version": "1.0.0"}
    )
    overlay = _preset(
        project_dir,
        "selector",
        [
            {
                "type": "command",
                "name": r"regex:^speckit\.target\.collect$",
                "file": "payload.md",
                "strategy": "append",
            }
        ],
    )
    resolver = PresetResolver(project_dir)
    layers = resolver.collect_all_layers("speckit.target.collect", "command")
    if enabled:
        assert [layer["path"] for layer in layers] == [overlay, candidate]
        assert resolver.resolve("speckit.target.collect", "command") == overlay
        assert resolver.resolve_content("speckit.target.collect", "command") == (
            "# target base\n\n\noverlay\n"
        )
    else:
        assert layers == []
        assert resolver.resolve("speckit.target.collect", "command") is None
        assert resolver.resolve_content("speckit.target.collect", "command") is None


def test_distinct_providers_and_exact_regex_declarations_are_not_deduplicated(
    project_dir,
):
    base = _extension(project_dir, "target", "commands/actual.md", declared=True)
    other = _extension(project_dir, "other", "commands/actual.md", declared=True)
    ExtensionRegistry(project_dir / ".specify" / "extensions").add(
        "target", {"enabled": True, "priority": 1, "version": "1.0.0"}
    )
    declarations = [
        {
            "type": "command",
            "name": name,
            "file": "payload.md",
            "strategy": "append",
        }
        for name in ("speckit.target.collect", r"regex:^speckit\.target\.collect$")
    ]
    overlay = _preset(project_dir, "selector", declarations)
    lower = _preset(project_dir, "lower", [declarations[0]], priority=2)
    resolver = PresetResolver(project_dir)
    layers = resolver.collect_all_layers("speckit.target.collect", "command")
    assert [layer["path"] for layer in layers] == [overlay, overlay, lower, base, other]
    assert resolver.resolve_content("speckit.target.collect", "command") == (
        "# target base\n\n\noverlay\n\n\noverlay\n\n\noverlay\n"
    )


def test_lower_preset_conventional_templates_command_is_a_candidate(tmp_path):
    """A lower preset's templates/commands/<name>.md must be discoverable.

    _conventional_command_names and _expand_command_selectors both enumerate that
    location, for lower presets as much as for extensions, so the shared
    conventional lookup the eligibility check relies on has to agree with them.
    Before the fix the file was enumerated as a candidate name but resolved to no
    layer, so a selector that matched it materialized nothing.
    """
    from specify_cli.presets._resolver import PresetResolver

    pack = tmp_path / ".specify" / "presets" / "lower"
    (pack / "templates" / "commands").mkdir(parents=True)
    body = pack / "templates" / "commands" / "speckit.lower.extra.md"
    body.write_text("---\ndescription: lower\n---\nLOWER BODY\n", encoding="utf-8")

    resolver = PresetResolver(tmp_path)

    # The shared lookup resolves it, and the eligibility check agrees.
    assert (
        resolver._conventional_resource(pack, "speckit.lower.extra", "command") == body
    )
    assert resolver._has_concrete_resource(pack, "speckit.lower.extra", "command")

    # The neighbouring conventional location keeps working.
    (pack / "commands").mkdir()
    flat = pack / "commands" / "speckit.lower.flat.md"
    flat.write_text("---\ndescription: flat\n---\nFLAT BODY\n", encoding="utf-8")
    assert (
        resolver._conventional_resource(pack, "speckit.lower.flat", "command") == flat
    )

    # A missing resource stays missing.
    assert (
        resolver._conventional_resource(pack, "speckit.lower.absent", "command") is None
    )


@pytest.mark.parametrize(
    ("strategy", "overlay", "expected"),
    [
        ("replace", "# Preset replacement\n", "# Preset replacement"),
        ("prepend", "# Preset prefix\n", "# Preset prefix\n\n\n# Core command"),
        ("append", "# Preset suffix\n", "# Core command\n\n\n# Preset suffix"),
        (
            "wrap",
            "# Wrapper start\n{CORE_TEMPLATE}\n# Wrapper end\n",
            "# Wrapper start\n# Core command\n\n# Wrapper end",
        ),
    ],
)
def test_command_regex_composes_over_core_for_each_strategy(
    project_dir, tmp_path, strategy, overlay, expected
):
    core_commands = project_dir / ".specify" / "templates" / "commands"
    core_commands.mkdir(parents=True, exist_ok=True)
    (core_commands / "plan.md").write_text("# Core command\n", encoding="utf-8")
    pack_dir = tmp_path / "selector"
    declaration = {
        "type": "command",
        "name": r"regex:^speckit\.plan$",
        "strategy": strategy,
        "body": overlay,
    }
    write_command_declarations(pack_dir, "selector", [declaration])
    installed = install_selector_fixture(project_dir, "selector", pack_dir, 1)

    content = PresetResolver(project_dir).resolve_content("speckit.plan", "command")

    assert content is not None
    assert content.strip() == expected.strip()
    layers = PresetResolver(project_dir).collect_all_layers("speckit.plan", "command")
    assert [layer["source"] for layer in layers] == ["selector v1.0.0", "core"]
    assert layers[0]["path"] == installed / "command-0.md"


def test_command_regex_expands_and_composes_over_extension_layer(project_dir, tmp_path):
    extension = project_dir / ".specify" / "extensions" / "demo"
    (extension / "commands").mkdir(parents=True)
    (extension / "commands" / "speckit.demo.md").write_text(
        "# Extension command\n", encoding="utf-8"
    )
    ExtensionRegistry(project_dir / ".specify" / "extensions").add(
        "demo", {"enabled": True, "priority": 10, "version": "1.0"}
    )
    pack_dir = tmp_path / "selector"
    write_command_declarations(
        pack_dir,
        "selector",
        [
            {
                "type": "command",
                "name": r"regex:^speckit\.demo$",
                "strategy": "append",
                "body": "# Preset addition\n",
            }
        ],
    )
    install_selector_fixture(project_dir, "selector", pack_dir, 1)

    content = PresetResolver(project_dir).resolve_content("speckit.demo", "command")

    assert content == "# Extension command\n\n\n# Preset addition\n"
    layers = PresetResolver(project_dir).collect_all_layers("speckit.demo", "command")
    assert [layer["source"] for layer in layers] == [
        "selector v1.0.0",
        "extension:demo v1.0",
    ]


def test_command_regex_expands_and_composes_over_lower_preset(project_dir, tmp_path):
    lower_pack = tmp_path / "lower"
    write_command_declarations(
        lower_pack,
        "lower",
        [
            {
                "type": "command",
                "name": "speckit.lower",
                "strategy": "replace",
                "body": "# Lower preset command\n",
            }
        ],
    )
    install_selector_fixture(project_dir, "lower", lower_pack, 10)
    selector_pack = tmp_path / "selector"
    write_command_declarations(
        selector_pack,
        "selector",
        [
            {
                "type": "command",
                "name": r"regex:^speckit\.lower$",
                "strategy": "prepend",
                "body": "# Selector prefix\n",
            }
        ],
    )
    install_selector_fixture(project_dir, "selector", selector_pack, 1)

    content = PresetResolver(project_dir).resolve_content("speckit.lower", "command")

    assert content == "# Selector prefix\n\n\n# Lower preset command\n"
    layers = PresetResolver(project_dir).collect_all_layers("speckit.lower", "command")
    assert [layer["source"] for layer in layers] == [
        "selector v1.0.0",
        "lower v1.0.0",
    ]


def test_three_overlapping_command_regexes_keep_declaration_order_and_compose(
    project_dir, tmp_path
):
    core_commands = project_dir / ".specify" / "templates" / "commands"
    core_commands.mkdir(parents=True, exist_ok=True)
    (core_commands / "plan.md").write_text("# Core command\n", encoding="utf-8")
    pack_dir = tmp_path / "selector"
    declarations = [
        {
            "type": "command",
            "name": r"regex:^speckit\.plan$",
            "strategy": "prepend",
            "body": "# Declared first\n",
        },
        {
            "type": "command",
            "name": r"regex:^speckit\.p.*$",
            "strategy": "append",
            "body": "# Declared second\n",
        },
        {
            "type": "command",
            "name": r"regex:^speckit\.pla.*n$",
            "strategy": "wrap",
            "body": "# Declared third start\n{CORE_TEMPLATE}\n# Declared third end\n",
        },
    ]
    write_command_declarations(pack_dir, "selector", declarations)
    install_selector_fixture(project_dir, "selector", pack_dir, 1)
    manager = PresetManager(project_dir)
    manifest = PresetManifest(
        project_dir / ".specify" / "presets" / "selector" / "preset.yml"
    )

    expanded = manager._expand_command_selectors(
        PresetResolver(project_dir),
        project_dir / ".specify" / "presets" / "selector",
        manifest.templates,
    )
    layers = PresetResolver(project_dir).collect_all_layers("speckit.plan", "command")
    content = PresetResolver(project_dir).resolve_content("speckit.plan", "command")

    assert [entry["name"] for entry in expanded] == [
        "speckit.plan",
        "speckit.plan",
        "speckit.plan",
    ]
    assert [layer["path"].name for layer in layers] == [
        "command-0.md",
        "command-1.md",
        "command-2.md",
        "plan.md",
    ]
    assert content is not None
    assert content.index("Declared first") < content.index("Declared third start")
    assert content.index("Declared third start") < content.index("Core command")
    assert content.index("Core command") < content.index("Declared third end")
    assert content.index("Declared third end") < content.index("Declared second")


def test_ineligible_selector_declaration_does_not_create_its_conventional_payload(
    project_dir,
):
    """A selector that matches no lower provider must not fabricate the resource.

    Copilot's previously-missed finding: an ineligible matching selector was
    collapsed to nothing, which callers read as "undeclared" and then satisfied
    through the convention lookup. A declaration whose payload sits at the
    conventional location ``commands/foo.md`` therefore resolved that file even
    though no lower ``foo`` command exists, so the selector created the very
    resource it was only meant to augment.
    """
    from specify_cli.presets import PresetResolver
    from tests.specify_cli.presets._helpers import write_diagnostic_selector_preset

    write_diagnostic_selector_preset(
        project_dir,
        "selector-no-lower",
        [{"type": "command", "name": r"regex:^foo$", "file": "commands/foo.md"}],
    )
    resolver = PresetResolver(project_dir)
    pack = project_dir / ".specify" / "presets" / "selector-no-lower"

    declarations = resolver._preset_declarations_for_resource(pack, "foo", "command")
    assert declarations, "the matching declaration must be preserved, not dropped"
    assert [candidate for _declaration, candidate in declarations] == [None]
    assert resolver.resolve("foo", "command") is None
    assert resolver.collect_all_layers("foo", "command") == []


def test_unmatched_selector_payload_is_not_evidence_for_a_higher_selector(project_dir):
    """Selector declarations must not chain through their own conventional payload.

    A lower preset declaring ``regex:^foo$`` with its payload at ``commands/foo.md``
    was discovered by the convention lookup, so it counted as a concrete lower
    resource and made a higher ``regex:^foo$`` eligible - even though the contract
    forbids using another selector declaration as evidence of existence.
    """
    from specify_cli.presets import PresetRegistry, PresetResolver
    from tests.specify_cli.presets._helpers import write_diagnostic_selector_preset

    for preset_id in ("selector-lower", "selector-higher"):
        write_diagnostic_selector_preset(
            project_dir,
            preset_id,
            [{"type": "command", "name": r"regex:^foo$", "file": "commands/foo.md"}],
        )
    registry = PresetRegistry(project_dir / ".specify" / "presets")
    registry.add("selector-lower", {"enabled": True, "priority": 20, "version": "1.0.0"})
    registry.add("selector-higher", {"enabled": True, "priority": 10, "version": "1.0.0"})

    resolver = PresetResolver(project_dir)
    presets_dir = project_dir / ".specify" / "presets"
    assert (
        resolver._has_concrete_resource(presets_dir / "selector-lower", "foo", "command")
        is False
    )
    higher = resolver._preset_declarations_for_resource(
        presets_dir / "selector-higher", "foo", "command"
    )
    assert [candidate for _declaration, candidate in higher] == [None]
    assert resolver.resolve("foo", "command") is None
