"""Cross-domain preset workflows and bundled-content contracts.

Domain unit tests mirror src/specify_cli/presets/_*.py under
tests/specify_cli/presets/test_*.py; command tests live alongside them.
"""

import json
import zipfile
from pathlib import Path

import pytest
import yaml

from specify_cli.extensions import ExtensionRegistry
from specify_cli.presets import (
    PresetManager,
    PresetManifest,
    PresetResolver,
)
from tests.specify_cli.presets import _fixtures
from tests.specify_cli.presets._helpers import (
    CORE_TEMPLATE_NAMES,
    SELF_TEST_PRESET_DIR,
    install_self_test_preset,
)

temp_dir = _fixtures.temp_dir
valid_pack_data = _fixtures.valid_pack_data
pack_dir = _fixtures.pack_dir
project_dir = _fixtures.project_dir


class TestIntegration:
    """Integration tests for complete preset workflows."""

    def test_full_install_resolve_remove_cycle(self, project_dir, pack_dir):
        """Test complete lifecycle: install → resolve → remove."""
        # Install
        manager = PresetManager(project_dir)
        manifest = manager.install_from_directory(pack_dir, "0.1.5")
        assert manifest.id == "test-pack"

        # Resolve — pack template should win over core
        resolver = PresetResolver(project_dir)
        result = resolver.resolve("spec-template")
        assert result is not None
        assert "Custom Spec Template" in result.read_text()

        # Remove
        manager.remove("test-pack")

        # Resolve — should fall back to core
        result = resolver.resolve("spec-template")
        assert result is not None
        assert "Core Spec Template" in result.read_text()

    def test_override_beats_pack_beats_extension_beats_core(self, project_dir, pack_dir):
        """Test the full priority stack: override > pack > extension > core."""
        resolver = PresetResolver(project_dir)

        # Core should resolve
        result = resolver.resolve_with_source("spec-template")
        assert result["source"] == "core"

        # Add extension template
        ext_dir = project_dir / ".specify" / "extensions" / "my-ext"
        ext_templates_dir = ext_dir / "templates"
        ext_templates_dir.mkdir(parents=True)
        (ext_templates_dir / "spec-template.md").write_text("# Extension\n")

        # Register extension in registry
        extensions_dir = project_dir / ".specify" / "extensions"
        ext_registry = ExtensionRegistry(extensions_dir)
        ext_registry.add("my-ext", {"version": "1.0.0", "priority": 10})

        result = resolver.resolve_with_source("spec-template")
        assert result["source"] == "extension:my-ext v1.0.0"

        # Install pack — should win over extension
        manager = PresetManager(project_dir)
        manager.install_from_directory(pack_dir, "0.1.5")

        result = resolver.resolve_with_source("spec-template")
        assert "test-pack" in result["source"]

        # Add override — should win over pack
        overrides_dir = project_dir / ".specify" / "templates" / "overrides"
        overrides_dir.mkdir(parents=True)
        (overrides_dir / "spec-template.md").write_text("# Override\n")

        result = resolver.resolve_with_source("spec-template")
        assert result["source"] == "project override"

    def test_install_from_zip_then_resolve(self, project_dir, pack_dir, temp_dir):
        """Test installing from ZIP and then resolving."""
        # Create ZIP
        zip_path = temp_dir / "test-pack.zip"
        with zipfile.ZipFile(zip_path, 'w') as zf:
            for file_path in pack_dir.rglob('*'):
                if file_path.is_file():
                    arcname = file_path.relative_to(pack_dir)
                    zf.write(file_path, arcname)

        # Install
        manager = PresetManager(project_dir)
        manager.install_from_zip(zip_path, "0.1.5")

        # Resolve
        resolver = PresetResolver(project_dir)
        result = resolver.resolve("spec-template")
        assert result is not None
        assert "Custom Spec Template" in result.read_text()


class TestSelfTestPreset:
    """Bundled self-test preset contents and catalog visibility."""

    def test_self_test_preset_exists(self):
        """Verify the self-test preset directory and manifest exist."""
        assert SELF_TEST_PRESET_DIR.exists()
        assert (SELF_TEST_PRESET_DIR / "preset.yml").exists()

    def test_self_test_manifest_valid(self):
        """Verify the self-test preset manifest is valid."""
        manifest = PresetManifest(SELF_TEST_PRESET_DIR / "preset.yml")
        assert manifest.id == "self-test"
        assert manifest.name == "Self-Test Preset"
        assert manifest.version == "1.0.0"
        assert len(manifest.templates) == 7  # 5 templates + 2 commands

    def test_self_test_provides_all_core_templates(self):
        """Verify the self-test preset provides an override for every core template."""
        manifest = PresetManifest(SELF_TEST_PRESET_DIR / "preset.yml")
        provided_names = {t["name"] for t in manifest.templates}
        for name in CORE_TEMPLATE_NAMES:
            assert name in provided_names, f"Self-test preset missing template: {name}"

    def test_self_test_template_files_exist(self):
        """Verify that all declared template files actually exist on disk."""
        manifest = PresetManifest(SELF_TEST_PRESET_DIR / "preset.yml")
        for tmpl in manifest.templates:
            tmpl_path = SELF_TEST_PRESET_DIR / tmpl["file"]
            assert tmpl_path.exists(), f"Missing template file: {tmpl['file']}"

    def test_self_test_templates_have_marker(self):
        """Verify each template contains the preset:self-test marker."""
        for name in CORE_TEMPLATE_NAMES:
            tmpl_path = SELF_TEST_PRESET_DIR / "templates" / f"{name}.md"
            content = tmpl_path.read_text()
            assert "preset:self-test" in content, f"{name}.md missing preset:self-test marker"

    def test_self_test_not_in_catalog(self):
        """Verify the self-test preset is NOT in the catalog (it's local-only)."""
        catalog_path = Path(__file__).parent.parent / "presets" / "catalog.json"
        catalog_data = json.loads(catalog_path.read_text())
        assert "self-test" not in catalog_data["presets"]

    def test_self_test_has_command(self):
        """Verify the self-test preset includes a command override."""
        manifest = PresetManifest(SELF_TEST_PRESET_DIR / "preset.yml")
        commands = [t for t in manifest.templates if t["type"] == "command"]
        assert len(commands) >= 1
        assert commands[0]["name"] == "speckit.specify"

    def test_self_test_command_file_exists(self):
        """Verify the self-test command file exists on disk."""
        cmd_path = SELF_TEST_PRESET_DIR / "commands" / "speckit.specify.md"
        assert cmd_path.exists()
        content = cmd_path.read_text()
        assert "preset:self-test" in content


class TestInitOptions:
    """Tests for save_init_options / load_init_options helpers."""

    def test_save_and_load_round_trip(self, project_dir):
        from specify_cli import save_init_options, load_init_options

        opts = {"ai": "claude", "ai_skills": True, "here": False}
        save_init_options(project_dir, opts)

        loaded = load_init_options(project_dir)
        assert loaded["ai"] == "claude"
        assert loaded["ai_skills"] is True

    def test_save_and_load_available_from_init_options_module(self, project_dir):
        from specify_cli._init_options import load_init_options, save_init_options

        opts = {"ai": "codex", "ai_skills": True, "script": "sh"}
        save_init_options(project_dir, opts)

        assert load_init_options(project_dir) == opts

    def test_save_uses_utf8_encoding(self, project_dir, monkeypatch):
        from specify_cli import save_init_options

        original_write_text = Path.write_text
        seen: dict[str, str | None] = {}

        def spy_write_text(path, data, *args, **kwargs):
            if path == project_dir / ".specify" / "init-options.json":
                seen["encoding"] = kwargs.get("encoding")
            return original_write_text(path, data, *args, **kwargs)

        monkeypatch.setattr(Path, "write_text", spy_write_text)

        save_init_options(project_dir, {"label": "中文测试"})

        assert seen["encoding"] == "utf-8"

    def test_load_uses_utf8_encoding(self, project_dir, monkeypatch):
        from specify_cli import load_init_options

        opts_file = project_dir / ".specify" / "init-options.json"
        opts_file.parent.mkdir(parents=True, exist_ok=True)
        opts_file.write_text('{"ai": "codex"}', encoding="utf-8")

        original_read_text = Path.read_text
        seen: dict[str, str | None] = {}

        def spy_read_text(path, *args, **kwargs):
            if path == opts_file:
                seen["encoding"] = kwargs.get("encoding")
            return original_read_text(path, *args, **kwargs)

        monkeypatch.setattr(Path, "read_text", spy_read_text)

        assert load_init_options(project_dir) == {"ai": "codex"}
        assert seen["encoding"] == "utf-8"

    def test_load_returns_empty_when_missing(self, project_dir):
        from specify_cli import load_init_options

        assert load_init_options(project_dir) == {}

    def test_load_returns_empty_on_invalid_json(self, project_dir):
        from specify_cli import load_init_options

        opts_file = project_dir / ".specify" / "init-options.json"
        opts_file.parent.mkdir(parents=True, exist_ok=True)
        opts_file.write_text("{bad json")

        assert load_init_options(project_dir) == {}

    @pytest.mark.parametrize(
        "value",
        ["名前-プロジェクト", "café-résumé", "Ωmega-Δelta", "🚀-launch"],
    )
    def test_save_load_round_trip_preserves_non_ascii(self, project_dir, value):
        """Non-ASCII values round-trip via explicit UTF-8 encoding.

        ``Path.write_text`` / ``Path.read_text`` default to the system
        locale codec on Windows (cp1252 / gb2312 / cp932). Without
        ``encoding="utf-8"`` pinned on both ends, a project name like
        ``café`` written on a UTF-8 host becomes garbled or unreadable on
        a cp1252 host (and vice versa). Pin UTF-8 explicitly so init
        options round-trip across machines and CI.

        Note: this test only meaningfully exercises the encoding pin
        because ``save_init_options`` now writes JSON with
        ``ensure_ascii=False`` — otherwise ``json.dumps`` would output
        ASCII-only ``\\uXXXX`` escapes and the encoding pin would be a
        no-op for any value here. ``test_save_writes_real_utf8_bytes``
        below asserts that contract directly.
        """
        from specify_cli import save_init_options, load_init_options

        save_init_options(project_dir, {"ai": "claude", "project_name": value})

        loaded = load_init_options(project_dir)
        assert loaded["project_name"] == value

    def test_save_writes_real_utf8_bytes(self, project_dir):
        """The on-disk file contains real UTF-8 bytes, not ``\\uXXXX`` escapes.

        Pinning ``encoding="utf-8"`` on ``write_text`` only makes a
        difference when the serialiser actually emits non-ASCII
        characters. With ``ensure_ascii=False`` on ``json.dumps`` the
        non-ASCII bytes hit the file, so the encoding pin is the thing
        that decides between cp1252 garbage and clean UTF-8 on Windows.

        This test pins that behaviour: the on-disk bytes are valid UTF-8
        and contain the multi-byte encoding of ``café``, not its
        ``\\u00e9`` escape form. Reviewers can verify that removing
        ``ensure_ascii=False`` or ``encoding="utf-8"`` from the writer
        breaks this test, which is what Copilot's review pointed out the
        original round-trip test failed to do.
        """
        from specify_cli import save_init_options

        save_init_options(project_dir, {"project_name": "café"})

        opts_file = project_dir / ".specify" / "init-options.json"
        raw = opts_file.read_bytes()
        # 'café' in UTF-8 ends with bytes 0xC3 0xA9 ('é'). The cp1252
        # encoding of 'é' is the single byte 0xE9. The JSON-escape form
        # would be the 6-byte literal '\\u00e9'. We assert the UTF-8 form
        # is present so the test pins the actual contract.
        assert b"caf\xc3\xa9" in raw, (
            "Expected UTF-8 bytes for 'café' in the on-disk file, "
            f"got: {raw!r}"
        )
        # And the whole file decodes cleanly as UTF-8.
        raw.decode("utf-8")

    def test_load_returns_empty_on_locale_corrupted_file(self, project_dir):
        """A file written in a non-UTF-8 codec falls back to {}, not crash.

        Simulates a file produced by an old client (or by a peer machine
        with a different default locale) that contains bytes invalid as
        UTF-8. ``load_init_options`` should fall back to ``{}`` per the
        existing contract — never propagate a raw ``UnicodeDecodeError``
        to the CLI surface.
        """
        from specify_cli import load_init_options

        opts_file = project_dir / ".specify" / "init-options.json"
        opts_file.parent.mkdir(parents=True, exist_ok=True)
        # 0xE9 is 'é' in cp1252 but an invalid lead byte in UTF-8.
        opts_file.write_bytes(b'{"project_name": "caf\xe9"}')

        assert load_init_options(project_dir) == {}

    @pytest.mark.parametrize("payload", ["[]", '"value"', "42", "true", "null"])
    def test_load_returns_empty_on_non_object_json(self, project_dir, payload):
        from specify_cli import load_init_options

        opts_file = project_dir / ".specify" / "init-options.json"
        opts_file.parent.mkdir(parents=True, exist_ok=True)
        opts_file.write_text(payload, encoding="utf-8")

        assert load_init_options(project_dir) == {}

    def test_load_returns_empty_on_unicode_decode_error(self, project_dir, monkeypatch):
        from specify_cli import load_init_options

        opts_file = project_dir / ".specify" / "init-options.json"
        opts_file.parent.mkdir(parents=True, exist_ok=True)
        opts_file.write_bytes(b"{}")

        original_read_text = Path.read_text

        def raise_decode_error(path, *args, **kwargs):
            if path == opts_file:
                raise UnicodeDecodeError("utf-8", b"\xff", 0, 1, "invalid start byte")
            return original_read_text(path, *args, **kwargs)

        monkeypatch.setattr(Path, "read_text", raise_decode_error)

        assert load_init_options(project_dir) == {}

    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            (True, True),
            (False, False),
            ("true", False),
            ("false", False),
            (1, False),
            (0, False),
            (None, False),
        ],
    )
    def test_is_ai_skills_enabled_requires_boolean_true(self, value, expected):
        from specify_cli._init_options import is_ai_skills_enabled

        assert is_ai_skills_enabled({"ai_skills": value}) is expected


class TestResolveActiveAgentForRegistration:
    """Tests for the shared #2948 active-agent resolution helper.

    ``load_init_options`` collapses "no file", "corrupted file", and
    "valid file with no active agent" into the same ``{}``. Extensions and
    presets both need to tell those apart: no file means "legacy project,
    fall back to all detected agents"; a corrupted or malformed file means
    "fail closed, register nothing" so a corrupted init-options.json can't
    silently reintroduce all-agent registration.
    """

    def test_missing_file_returns_sentinel(self, project_dir):
        from specify_cli._init_options import (
            MISSING_INIT_OPTIONS_FILE,
            resolve_active_agent_for_registration,
        )

        assert (
            resolve_active_agent_for_registration(project_dir)
            is MISSING_INIT_OPTIONS_FILE
        )

    def test_valid_active_agent_returns_string(self, project_dir):
        from specify_cli import save_init_options
        from specify_cli._init_options import resolve_active_agent_for_registration

        save_init_options(project_dir, {"ai": "claude"})

        assert resolve_active_agent_for_registration(project_dir) == "claude"

    def test_corrupted_json_fails_closed(self, project_dir):
        """A present-but-unparseable file must not behave like "no file"."""
        from specify_cli._init_options import resolve_active_agent_for_registration

        opts_file = project_dir / ".specify" / "init-options.json"
        opts_file.parent.mkdir(parents=True, exist_ok=True)
        opts_file.write_text("{bad json", encoding="utf-8")

        assert resolve_active_agent_for_registration(project_dir) is None

    @pytest.mark.parametrize("value", [[], {}, "", 0, None, ["claude"]])
    def test_malformed_ai_value_fails_closed(self, project_dir, value):
        """A recorded but non-string/empty ``ai`` value fails closed too."""
        from specify_cli import save_init_options
        from specify_cli._init_options import resolve_active_agent_for_registration

        save_init_options(project_dir, {"ai": value})

        assert resolve_active_agent_for_registration(project_dir) is None

    def test_dangling_symlink_fails_closed(self, project_dir):
        """A dangling init-options.json symlink must fail closed, not fall
        back to "no file" (#2948).

        ``Path.exists()`` follows symlinks and returns False for a broken
        symlink whose target is missing, so a naive presence check treats a
        dangling symlink the same as "no file at all" and falls back to
        legacy all-agent registration. The path is present (just broken),
        so it must be treated as a corrupted file and fail closed instead.
        """
        from specify_cli._init_options import resolve_active_agent_for_registration

        opts_file = project_dir / ".specify" / "init-options.json"
        opts_file.parent.mkdir(parents=True, exist_ok=True)
        opts_file.symlink_to(project_dir / ".specify" / "does-not-exist.json")

        assert not opts_file.exists()  # sanity: this is what makes it dangling
        assert opts_file.is_symlink()
        assert resolve_active_agent_for_registration(project_dir) is None


LEAN_PRESET_DIR = Path(__file__).parent.parent / "presets" / "lean"


CORE_CONSTITUTION_COMMAND = (
    Path(__file__).parent.parent / "templates" / "commands" / "constitution.md"
)


LEAN_COMMAND_NAMES = [
    "speckit.specify",
    "speckit.plan",
    "speckit.tasks",
    "speckit.implement",
    "speckit.constitution",
]


@pytest.mark.parametrize(
    "command_path",
    [
        CORE_CONSTITUTION_COMMAND,
        LEAN_PRESET_DIR / "commands" / "speckit.constitution.md",
    ],
    ids=["core", "lean"],
)
def test_constitution_commands_guard_against_non_governance_work(command_path):
    """Constitution commands defer non-governance work instead of executing it."""
    content = command_path.read_text()
    lower_content = content.lower()
    normalized_content = " ".join(lower_content.split())

    assert "## Scope Guard" in content
    assert "**MUST NOT**" in content
    assert "Classify every part" in content
    assert "application source files" in content
    assert "non-governance intent" in content
    assert "`Next Actions`" in content
    assert "__SPECKIT_COMMAND_SPECIFY__" in content
    assert "omit" in lower_content
    assert "do not invoke it" in normalized_content or "without invoking it" in normalized_content


def test_core_constitution_command_resolves_template_at_runtime():
    """The core command must consume the composed scaffold on every invocation."""
    content = CORE_CONSTITUTION_COMMAND.read_text()

    assert "resolve-template.sh constitution-template --json" in content
    assert "resolve-template.ps1 constitution-template -Json" in content
    assert "resolve_template.py constitution-template --json" in content
    assert "parse `TEMPLATE_CONTENT` as the active template" in content
    assert "do not continue with only one contributing" in content
    assert "Do not write back to any versioned template layer" in content


def test_core_checklist_command_resolves_template_at_runtime():
    """The checklist command must consume the composed scaffold."""
    content = (CORE_CONSTITUTION_COMMAND.parent / "checklist.md").read_text(
        encoding="utf-8"
    )

    assert "--template checklist-template" in content
    assert "TEMPLATE_CONTENT" in content
    assert "Use TEMPLATE_CONTENT as the structural template" in content


class TestLeanPreset:
    """Tests for the lean preset that ships with the repo."""

    def test_lean_preset_exists(self):
        """Verify the lean preset directory and manifest exist."""
        assert LEAN_PRESET_DIR.exists()
        assert (LEAN_PRESET_DIR / "preset.yml").exists()

    def test_lean_manifest_valid(self):
        """Verify the lean preset manifest is valid."""
        manifest = PresetManifest(LEAN_PRESET_DIR / "preset.yml")
        assert manifest.id == "lean"
        assert manifest.name == "Lean Workflow"
        assert manifest.version == "1.0.0"
        assert len(manifest.templates) == 5  # 5 commands

    def test_lean_provides_core_workflow_commands(self):
        """Verify the lean preset provides overrides for core workflow commands."""
        manifest = PresetManifest(LEAN_PRESET_DIR / "preset.yml")
        provided_names = {t["name"] for t in manifest.templates}
        for name in LEAN_COMMAND_NAMES:
            assert name in provided_names, f"Lean preset missing command: {name}"

    def test_lean_command_files_exist(self):
        """Verify that all declared command files actually exist on disk."""
        manifest = PresetManifest(LEAN_PRESET_DIR / "preset.yml")
        for tmpl in manifest.templates:
            tmpl_path = LEAN_PRESET_DIR / tmpl["file"]
            assert tmpl_path.exists(), f"Missing command file: {tmpl['file']}"

    def test_lean_commands_have_no_scripts(self):
        """Verify lean commands have no scripts in frontmatter."""
        from specify_cli.agents import CommandRegistrar

        for name in LEAN_COMMAND_NAMES:
            cmd_path = LEAN_PRESET_DIR / "commands" / f"speckit.{name.split('.')[-1]}.md"
            content = cmd_path.read_text()
            frontmatter, _ = CommandRegistrar.parse_frontmatter(content)
            assert "scripts" not in frontmatter, f"{name} should not have scripts in frontmatter"

    def test_lean_commands_have_no_hooks(self):
        """Verify lean commands do not contain extension hook boilerplate."""
        for name in LEAN_COMMAND_NAMES:
            cmd_path = LEAN_PRESET_DIR / "commands" / f"speckit.{name.split('.')[-1]}.md"
            content = cmd_path.read_text()
            assert "hooks." not in content, f"{name} should not reference extension hooks"
            assert "extensions.yml" not in content, f"{name} should not reference extensions.yml"

    def test_install_lean_preset(self, project_dir):
        """Test installing the lean preset from its directory."""
        manager = PresetManager(project_dir)
        manifest = manager.install_from_directory(LEAN_PRESET_DIR, "0.6.0")
        assert manifest.id == "lean"
        assert manager.registry.is_installed("lean")

    def test_lean_overrides_commands(self, project_dir):
        """Test that lean preset overrides are resolved correctly."""
        manager = PresetManager(project_dir)
        manager.install_from_directory(LEAN_PRESET_DIR, "0.6.0")

        resolver = PresetResolver(project_dir)
        for name in LEAN_COMMAND_NAMES:
            result = resolver.resolve(name, template_type="command")
            assert result is not None, f"Lean override for {name} not resolved"


class TestBundledPresetLocator:
    """Tests for _locate_bundled_preset discovery function."""

    def test_locate_bundled_lean_preset(self):
        """_locate_bundled_preset finds the lean preset."""
        from specify_cli import _locate_bundled_preset

        path = _locate_bundled_preset("lean")
        assert path is not None
        assert (path / "preset.yml").is_file()

    def test_locate_bundled_preset_not_found(self):
        """_locate_bundled_preset returns None for nonexistent preset."""
        from specify_cli import _locate_bundled_preset

        path = _locate_bundled_preset("nonexistent-preset")
        assert path is None

    def test_locate_bundled_preset_rejects_invalid_id(self):
        """_locate_bundled_preset rejects IDs with invalid characters."""
        from specify_cli import _locate_bundled_preset

        assert _locate_bundled_preset("../escape") is None
        assert _locate_bundled_preset("UPPERCASE") is None
        assert _locate_bundled_preset("has spaces") is None

    def test_bundled_preset_in_catalog(self):
        """Verify the lean preset is listed in catalog.json with bundled marker."""
        catalog_path = Path(__file__).parent.parent / "presets" / "catalog.json"
        catalog = json.loads(catalog_path.read_text())
        assert "lean" in catalog["presets"]
        assert catalog["presets"]["lean"]["bundled"] is True
        assert "download_url" not in catalog["presets"]["lean"]


class TestEnsureConstitutionResolverAware:
    """`ensure_constitution_from_template` must resolve through PresetResolver.

    Init materializes the live constitution once, while later /constitution
    runs resolve on demand. These tests pin the regression from issue #3272:
    a preset-provided ``constitution-template`` must win during the init seed,
    while the core template is used when no preset overrides it.
    """

    def _core_constitution(self, project_dir):
        templates_dir = project_dir / ".specify" / "templates"
        templates_dir.mkdir(parents=True, exist_ok=True)
        (templates_dir / "constitution-template.md").write_text(
            "# [PROJECT_NAME] Constitution\n\n### [PRINCIPLE_1_NAME]\n"
        )

    def _wrap_constitution_preset(self, temp_dir):
        preset_dir = temp_dir / "ensure-wrap-preset"
        (preset_dir / "templates").mkdir(parents=True)
        (preset_dir / "templates" / "constitution-template.md").write_text(
            "# Ensure Wrapper\n\n{CORE_TEMPLATE}\n\n## Tail\n"
        )
        (preset_dir / "preset.yml").write_text(
            yaml.dump(
                {
                    "schema_version": "1.0",
                    "preset": {
                        "id": "ensure-wrap",
                        "name": "Ensure Wrap",
                        "version": "1.0.0",
                        "description": "Wrap strategy for ensure() coverage",
                    },
                    "requires": {"speckit_version": ">=0.1.0"},
                    "provides": {
                        "templates": [
                            {
                                "type": "template",
                                "name": "constitution-template",
                                "file": "templates/constitution-template.md",
                                "strategy": "wrap",
                                "description": "Wrapped constitution",
                            }
                        ]
                    },
                }
            )
        )
        return preset_dir

    def test_seeds_from_core_when_no_preset(self, project_dir):
        from specify_cli.command_init import ensure_constitution_from_template

        self._core_constitution(project_dir)
        ensure_constitution_from_template(project_dir)

        memory = project_dir / ".specify" / "memory" / "constitution.md"
        assert memory.exists()
        assert "[PROJECT_NAME]" in memory.read_text()
        assert (memory.parent / ".constitution-template.json").exists()

    def test_seeds_from_preset_when_installed(self, project_dir):
        from specify_cli.command_init import ensure_constitution_from_template

        self._core_constitution(project_dir)
        manager = PresetManager(project_dir)
        install_self_test_preset(manager)

        memory = project_dir / ".specify" / "memory" / "constitution.md"
        assert not memory.exists()

        ensure_constitution_from_template(project_dir)

        assert memory.exists()
        content = memory.read_text()
        assert "preset:self-test" in content
        assert "[PROJECT_NAME]" not in content

    def test_preserves_existing_memory(self, project_dir):
        from specify_cli.command_init import ensure_constitution_from_template

        self._core_constitution(project_dir)
        memory = project_dir / ".specify" / "memory" / "constitution.md"
        memory.parent.mkdir(parents=True, exist_ok=True)
        authored = "# Acme Constitution\nAuthored.\n"
        memory.write_text(authored)

        ensure_constitution_from_template(project_dir)

        assert memory.read_text() == authored

    def test_preserves_edited_generated_memory(self, project_dir):
        from specify_cli.command_init import ensure_constitution_from_template

        self._core_constitution(project_dir)
        ensure_constitution_from_template(project_dir)
        memory = project_dir / ".specify" / "memory" / "constitution.md"
        authored = memory.read_text() + "\nAuthored amendment.\n"
        memory.write_text(authored)

        manager = PresetManager(project_dir)
        install_self_test_preset(manager)

        assert memory.read_text() == authored

    def test_composes_wrap_strategy_when_ensuring(self, project_dir, temp_dir):
        from specify_cli.command_init import ensure_constitution_from_template

        self._core_constitution(project_dir)
        manager = PresetManager(project_dir)
        manager.install_from_directory(self._wrap_constitution_preset(temp_dir), "0.1.5")

        memory = project_dir / ".specify" / "memory" / "constitution.md"
        assert not memory.exists()
        ensure_constitution_from_template(project_dir)

        content = memory.read_text()
        assert "{CORE_TEMPLATE}" not in content
        assert "# Ensure Wrapper" in content
        assert "[PROJECT_NAME]" in content


class TestConstitutionSyncPreset:
    """The bundled opt-in ``constitution-sync`` preset re-adds materialization.

    Follow-up to #3790: core ``/constitution`` no longer propagates guidance
    into templates. Issue #3950 also gates install-time constitution seeding on
    this preset. Its command override remains a ``wrap`` of core so it stays
    forward-compatible with core changes.
    """

    PRESET_DIR = Path(__file__).parent.parent / "presets" / "constitution-sync"

    def test_manifest_provides_wrap_of_constitution(self):
        manifest = yaml.safe_load((self.PRESET_DIR / "preset.yml").read_text())
        assert manifest["preset"]["id"] == "constitution-sync"
        entries = manifest["provides"]["templates"]
        assert len(entries) == 1
        entry = entries[0]
        assert entry["type"] == "command"
        assert entry["name"] == "speckit.constitution"
        assert entry["strategy"] == "wrap"
        # Must target the post-#3790 baseline so propagation is not double-applied.
        assert manifest["requires"]["speckit_version"] == ">=0.14.4"

    def test_wrapper_uses_core_template_and_propagates(self):
        text = (self.PRESET_DIR / "commands" / "speckit.constitution.md").read_text()

        # Parse the Markdown frontmatter as YAML rather than substring-matching,
        # so `strategy: wrap` is asserted structurally (not as text that could
        # appear in the body) and {CORE_TEMPLATE} is asserted in the body only.
        assert text.startswith("---\n")
        _, frontmatter_block, body = text.split("---", 2)
        frontmatter = yaml.safe_load(frontmatter_block)
        assert frontmatter["strategy"] == "wrap"

        assert "{CORE_TEMPLATE}" in body
        assert "strategy: wrap" not in body  # only in frontmatter
        # The three governed scaffolds the old checklist propagated into.
        assert "plan-template.md" in body
        assert "spec-template.md" in body
        assert "tasks-template.md" in body
        # Must not mutate versioned preset/extension artifacts.
        assert "Do not edit versioned preset- or extension-provided template or command files" in body

    def test_catalog_lists_bundled_preset(self):
        manifest = yaml.safe_load((self.PRESET_DIR / "preset.yml").read_text())
        catalog = json.loads((self.PRESET_DIR.parent / "catalog.json").read_text())
        entry = catalog["presets"]["constitution-sync"]
        assert entry["bundled"] is True
        assert entry["version"] == manifest["preset"]["version"]
        assert entry["provides"]["commands"] == 1
        assert entry["provides"]["templates"] == 0

    def test_wrap_composes_over_core_constitution(self, project_dir):
        """Installing the preset yields a wrap layer atop the bundled core."""
        manager = PresetManager(project_dir)
        manager.install_from_directory(self.PRESET_DIR, "0.15.0")

        resolver = PresetResolver(project_dir)
        layers = resolver.collect_all_layers("speckit.constitution", "command")
        assert len(layers) >= 2, "expected preset wrap layer plus a core base"
        assert layers[0]["strategy"] == "wrap"
        assert any("constitution-sync" in str(layer["path"]) for layer in layers)
        assert layers[-1]["source"] == "core (bundled)"

    def test_resolved_content_embeds_core_and_sync_pass(self, project_dir):
        """resolve_content substitutes {CORE_TEMPLATE} so the effective command
        contains both the bundled core body and the propagation pass."""
        manager = PresetManager(project_dir)
        manager.install_from_directory(self.PRESET_DIR, "0.15.0")

        resolver = PresetResolver(project_dir)
        content = resolver.resolve_content("speckit.constitution", "command")
        assert content is not None
        # {CORE_TEMPLATE} must be replaced, not left literal.
        assert "{CORE_TEMPLATE}" not in content
        # Core body is present (distinctive core-only heading).
        assert "## Scope Guard" in content
        # The wrapper's propagation pass is present and supersedes the guard.
        assert "## Constitution Template Sync" in content
        assert "supersedes the \"Scope Guard\" above" in content
        assert "plan-template.md" in content
