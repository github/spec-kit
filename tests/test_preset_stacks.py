"""
Unit tests for reusable preset stacks (`.specify/preset-stacks.yml`).

Tests cover:
- Config file loading/validation
- Applying a stack (install/priority/source/failure semantics)
- Sync-on-reapply (uninstall of dropped entries, multi-stack overlap)
- `specify preset stack` CLI verbs (list/install/add/remove)
- `specify init --preset-stack` / implicit-default resolution
"""

import json
import os
import tempfile
import shutil
import zipfile
from pathlib import Path

import pytest

import yaml
from typer.testing import CliRunner

from specify_cli import app
from specify_cli.presets import PresetCatalog, PresetManager, PresetValidationError
from specify_cli.presets.stacks import (
    PresetStack,
    PresetStackEntry,
    PresetStacksConfig,
    apply_stack,
    load_stacks_config,
)

# ===== Fixtures =====


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    tmpdir = tempfile.mkdtemp()
    yield Path(tmpdir)
    shutil.rmtree(tmpdir)


@pytest.fixture
def project_dir(temp_dir):
    """Create a mock spec-kit project directory with .specify/ initialized."""
    proj_dir = temp_dir / "project"
    proj_dir.mkdir()

    specify_dir = proj_dir / ".specify"
    specify_dir.mkdir()

    templates_dir = specify_dir / "templates"
    templates_dir.mkdir()

    core_spec = templates_dir / "spec-template.md"
    core_spec.write_text("# Core Spec Template\n")

    core_plan = templates_dir / "plan-template.md"
    core_plan.write_text("# Core Plan Template\n")

    commands_dir = templates_dir / "commands"
    commands_dir.mkdir()

    return proj_dir


def _write_stacks_config(project_dir: Path, data: dict) -> Path:
    specify_dir = project_dir / ".specify"
    specify_dir.mkdir(exist_ok=True)
    config_path = specify_dir / "preset-stacks.yml"
    config_path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    return config_path


def _make_preset_dir(base_dir: Path, pack_id: str, version: str = "1.0.0") -> Path:
    """Build a minimal, valid, installable preset directory (mirrors test_presets.py's pack_dir)."""
    p_dir = base_dir / pack_id
    p_dir.mkdir()
    manifest = {
        "schema_version": "1.0",
        "preset": {
            "id": pack_id,
            "name": pack_id.title(),
            "version": version,
            "description": f"Test preset {pack_id}",
            "author": "Test Author",
            "repository": f"https://github.com/test/{pack_id}",
            "license": "MIT",
        },
        "requires": {"speckit_version": ">=0.1.0"},
        "provides": {
            "templates": [
                {
                    "type": "template",
                    "name": "spec-template",
                    "file": "templates/spec-template.md",
                    "description": "Custom spec template",
                    "replaces": "spec-template",
                }
            ]
        },
        "tags": ["testing"],
    }
    (p_dir / "preset.yml").write_text(yaml.safe_dump(manifest), encoding="utf-8")
    templates_dir = p_dir / "templates"
    templates_dir.mkdir()
    (templates_dir / "spec-template.md").write_text(f"# {pack_id} template\n")
    return p_dir


def _read_stack_state(project_dir: Path) -> dict:
    return json.loads(
        (project_dir / ".specify" / "presets" / ".stack-state.json").read_text(encoding="utf-8")
    )


def _zip_preset_dir(pack_dir: Path, zip_path: Path) -> Path:
    with zipfile.ZipFile(zip_path, "w") as zf:
        for file_path in pack_dir.rglob("*"):
            if file_path.is_file():
                zf.write(file_path, file_path.relative_to(pack_dir))
    return zip_path


# ===== load_stacks_config =====


class TestLoadStacksConfig:
    def test_absent_config_returns_empty_config(self, project_dir):
        config = load_stacks_config(project_dir)
        assert config == PresetStacksConfig(stacks=[])

    def test_valid_multi_stack_file_round_trips(self, project_dir):
        _write_stacks_config(project_dir, {
            "stacks": [
                {
                    "name": "default",
                    "entries": [
                        {"preset": "alpha", "priority": 5},
                        {"preset": "beta"},
                    ],
                },
                {
                    "name": "extra",
                    "entries": [
                        {"preset": "gamma", "priority": 20, "source": "/local/gamma"},
                    ],
                },
            ]
        })

        config = load_stacks_config(project_dir)

        assert config == PresetStacksConfig(stacks=[
            PresetStack(name="default", entries=[
                PresetStackEntry(preset="alpha", priority=5),
                PresetStackEntry(preset="beta", priority=10),
            ]),
            PresetStack(name="extra", entries=[
                PresetStackEntry(preset="gamma", priority=20, source="/local/gamma"),
            ]),
        ])

    def test_malformed_yaml_rejected_naming_file(self, project_dir):
        config_path = project_dir / ".specify" / "preset-stacks.yml"
        config_path.write_text("stacks: [this is: not valid yaml", encoding="utf-8")

        with pytest.raises(PresetValidationError, match=r"preset-stacks\.yml"):
            load_stacks_config(project_dir)

    def test_entry_missing_preset_rejected_naming_stack(self, project_dir):
        _write_stacks_config(project_dir, {
            "stacks": [
                {"name": "default", "entries": [{"priority": 5}]},
            ]
        })

        with pytest.raises(PresetValidationError, match="default"):
            load_stacks_config(project_dir)

    def test_stack_named_none_rejected(self, project_dir):
        _write_stacks_config(project_dir, {
            "stacks": [{"name": "none", "entries": [{"preset": "alpha"}]}]
        })

        with pytest.raises(PresetValidationError, match="none"):
            load_stacks_config(project_dir)

    def test_duplicate_preset_in_same_stack_rejected(self, project_dir):
        _write_stacks_config(project_dir, {
            "stacks": [{
                "name": "default",
                "entries": [
                    {"preset": "alpha", "priority": 5},
                    {"preset": "alpha", "priority": 10},
                ],
            }]
        })

        with pytest.raises(PresetValidationError, match="alpha"):
            load_stacks_config(project_dir)

    def test_omitted_priority_defaults_to_10(self, project_dir):
        _write_stacks_config(project_dir, {
            "stacks": [{"name": "default", "entries": [{"preset": "alpha"}]}]
        })

        config = load_stacks_config(project_dir)

        assert config.stacks[0].entries[0].priority == 10


# ===== apply_stack =====


class TestApplyStack:
    def test_applies_entries_at_listed_priority(self, project_dir, temp_dir):
        """AC1/FR-2030/FR-1010: matches individual `preset add --priority` calls."""
        alpha_dir = _make_preset_dir(temp_dir, "alpha")
        beta_dir = _make_preset_dir(temp_dir, "beta")
        stack = PresetStack(name="default", entries=[
            PresetStackEntry(preset="alpha", priority=5, source=str(alpha_dir)),
            PresetStackEntry(preset="beta", priority=20, source=str(beta_dir)),
        ])

        result = apply_stack(project_dir, stack, "0.1.5")

        assert result.success
        manager = PresetManager(project_dir)
        assert manager.registry.is_installed("alpha")
        assert manager.registry.is_installed("beta")
        assert manager.registry.get("alpha")["priority"] == 5
        assert manager.registry.get("beta")["priority"] == 20

    def test_reapply_updates_priority_without_duplicating(self, project_dir, temp_dir):
        """AC2: re-applying with a changed priority updates in place."""
        alpha_dir = _make_preset_dir(temp_dir, "alpha")
        stack = PresetStack(name="default", entries=[
            PresetStackEntry(preset="alpha", priority=5, source=str(alpha_dir)),
        ])
        apply_stack(project_dir, stack, "0.1.5")

        stack.entries[0].priority = 15
        result = apply_stack(project_dir, stack, "0.1.5")

        assert result.success
        manager = PresetManager(project_dir)
        assert manager.registry.is_installed("alpha")
        assert manager.registry.get("alpha")["priority"] == 15
        assert manager.list_installed().count(
            next(p for p in manager.list_installed() if p["id"] == "alpha")
        ) == 1

    def test_discovery_only_catalog_preset_installs_anyway(self, project_dir, temp_dir, monkeypatch):
        """AC3/FR-2025: a discovery-only catalog preset is installed via a stack."""
        gamma_dir = _make_preset_dir(temp_dir, "gamma")
        zip_path = _zip_preset_dir(gamma_dir, temp_dir / "gamma.zip")

        monkeypatch.setattr(
            PresetCatalog, "get_pack_info",
            lambda self, pack_id: {"id": pack_id, "_install_allowed": False, "download_url": "https://example.invalid/gamma.zip"},
        )

        def fake_download_pack(self, pack_id, target_dir=None, bypass_install_allowed=False):
            assert bypass_install_allowed is True
            return zip_path

        monkeypatch.setattr(PresetCatalog, "download_pack", fake_download_pack)
        monkeypatch.setattr("specify_cli._locate_bundled_preset", lambda pack_id: None)

        stack = PresetStack(name="default", entries=[PresetStackEntry(preset="gamma", priority=10)])
        result = apply_stack(project_dir, stack, "0.1.5")

        assert result.success
        assert PresetManager(project_dir).registry.is_installed("gamma")

    def test_explicit_local_source_makes_no_network_call(self, project_dir, temp_dir, monkeypatch):
        """FR-2032: an explicit local `source:` installs without any catalog/network lookup."""
        delta_dir = _make_preset_dir(temp_dir, "delta")

        def fail_if_called(*args, **kwargs):
            raise AssertionError("catalog should not be consulted for a local source entry")

        monkeypatch.setattr(PresetCatalog, "get_pack_info", fail_if_called)
        monkeypatch.setattr(PresetCatalog, "download_pack", fail_if_called)

        stack = PresetStack(name="default", entries=[
            PresetStackEntry(preset="delta", priority=10, source=str(delta_dir)),
        ])
        result = apply_stack(project_dir, stack, "0.1.5")

        assert result.success
        assert PresetManager(project_dir).registry.is_installed("delta")

    def test_explicit_source_url_installs_via_download(self, project_dir, temp_dir, monkeypatch):
        """FR-2032: an explicit archive-URL `source:` resolves via the download path."""
        scratch_dir = temp_dir / "download-scratch"
        scratch_dir.mkdir()
        epsilon_dir = _make_preset_dir(scratch_dir, "epsilon")
        zip_path = _zip_preset_dir(epsilon_dir, scratch_dir / "epsilon.zip")

        monkeypatch.setattr(
            "specify_cli.presets.stacks._download_archive",
            lambda url: zip_path,
        )

        stack = PresetStack(name="default", entries=[
            PresetStackEntry(preset="epsilon", priority=10, source="https://example.invalid/epsilon.zip"),
        ])
        result = apply_stack(project_dir, stack, "0.1.5")

        assert result.success
        assert PresetManager(project_dir).registry.is_installed("epsilon")

    def test_unresolvable_entry_fails_others_still_install(self, project_dir, temp_dir, monkeypatch):
        """AC4/FR-2040: an entry with no catalog match and no source fails by name; rest still installs."""
        zeta_dir = _make_preset_dir(temp_dir, "zeta")
        monkeypatch.setattr(PresetCatalog, "get_pack_info", lambda self, pack_id: None)
        monkeypatch.setattr("specify_cli._locate_bundled_preset", lambda pack_id: None)

        stack = PresetStack(name="default", entries=[
            PresetStackEntry(preset="missing-preset", priority=10),
            PresetStackEntry(preset="zeta", priority=10, source=str(zeta_dir)),
        ])
        result = apply_stack(project_dir, stack, "0.1.5")

        assert not result.success
        by_preset = {e.preset: e for e in result.entries}
        assert by_preset["missing-preset"].success is False
        assert "default" in by_preset["missing-preset"].error
        assert "missing-preset" in by_preset["missing-preset"].error
        assert by_preset["zeta"].success is True
        assert PresetManager(project_dir).registry.is_installed("zeta")

    def test_dropped_entry_is_uninstalled_on_reapply(self, project_dir, temp_dir):
        """AC5/FR-2035: dropping an entry and re-applying uninstalls it."""
        alpha_dir = _make_preset_dir(temp_dir, "alpha")
        beta_dir = _make_preset_dir(temp_dir, "beta")
        stack = PresetStack(name="default", entries=[
            PresetStackEntry(preset="alpha", priority=5, source=str(alpha_dir)),
            PresetStackEntry(preset="beta", priority=10, source=str(beta_dir)),
        ])
        apply_stack(project_dir, stack, "0.1.5")

        stack.entries = [PresetStackEntry(preset="alpha", priority=5, source=str(alpha_dir))]
        result = apply_stack(project_dir, stack, "0.1.5")

        assert result.success
        assert result.removed == ["beta"]
        manager = PresetManager(project_dir)
        assert manager.registry.is_installed("alpha")
        assert not manager.registry.is_installed("beta")

    def test_dropped_entry_stays_installed_if_another_stack_still_lists_it(self, project_dir, temp_dir):
        """AC5/FR-2035: a dropped entry survives if another applied stack's state still lists it."""
        alpha_dir = _make_preset_dir(temp_dir, "alpha")
        beta_dir = _make_preset_dir(temp_dir, "beta")

        stack_a = PresetStack(name="stack-a", entries=[
            PresetStackEntry(preset="alpha", priority=5, source=str(alpha_dir)),
            PresetStackEntry(preset="beta", priority=10, source=str(beta_dir)),
        ])
        apply_stack(project_dir, stack_a, "0.1.5")

        stack_b = PresetStack(name="stack-b", entries=[
            PresetStackEntry(preset="beta", priority=10, source=str(beta_dir)),
        ])
        apply_stack(project_dir, stack_b, "0.1.5")

        stack_a.entries = [PresetStackEntry(preset="alpha", priority=5, source=str(alpha_dir))]
        result = apply_stack(project_dir, stack_a, "0.1.5")

        assert result.success
        assert result.removed == []
        assert PresetManager(project_dir).registry.is_installed("beta")

    def test_failed_entry_is_not_treated_as_dropped(self, project_dir, temp_dir):
        """A transient failure must not make a still-listed preset look dropped."""
        alpha_dir = _make_preset_dir(temp_dir, "alpha")
        beta_dir = _make_preset_dir(temp_dir, "beta")
        stack = PresetStack(name="default", entries=[
            PresetStackEntry(preset="alpha", priority=5, source=str(alpha_dir)),
            PresetStackEntry(preset="beta", priority=10, source=str(beta_dir)),
        ])
        apply_stack(project_dir, stack, "0.1.5")

        # Same stack definition, but beta's source is momentarily unreachable.
        stack.entries[1].source = str(temp_dir / "gone")
        result = apply_stack(project_dir, stack, "0.1.5")

        assert not result.success
        assert result.removed == []
        assert PresetManager(project_dir).registry.is_installed("beta")
        assert set(_read_stack_state(project_dir)["default"]) == {"alpha", "beta"}

    def test_dropped_entry_removal_is_deferred_while_another_entry_fails(
        self, project_dir, temp_dir
    ):
        """A run with a failing entry defers uninstalls instead of guessing."""
        alpha_dir = _make_preset_dir(temp_dir, "alpha")
        beta_dir = _make_preset_dir(temp_dir, "beta")
        stack = PresetStack(name="default", entries=[
            PresetStackEntry(preset="alpha", priority=5, source=str(alpha_dir)),
            PresetStackEntry(preset="beta", priority=10, source=str(beta_dir)),
        ])
        apply_stack(project_dir, stack, "0.1.5")

        stack.entries = [PresetStackEntry(preset="alpha", priority=5, source=str(temp_dir / "gone"))]
        result = apply_stack(project_dir, stack, "0.1.5")

        assert result.removed == []
        assert result.deferred_removals == ["beta"]
        assert PresetManager(project_dir).registry.is_installed("beta")

        # Once the stack applies cleanly, the deferred removal happens.
        stack.entries = [PresetStackEntry(preset="alpha", priority=5, source=str(alpha_dir))]
        result = apply_stack(project_dir, stack, "0.1.5")

        assert result.success
        assert result.removed == ["beta"]
        assert not PresetManager(project_dir).registry.is_installed("beta")

    def test_manifest_id_differing_from_entry_is_tracked_and_removed(
        self, project_dir, temp_dir
    ):
        """A source whose manifest declares another ID is tracked under that ID."""
        real_dir = _make_preset_dir(temp_dir, "real-id")
        stack = PresetStack(name="default", entries=[
            PresetStackEntry(preset="requested-id", priority=10, source=str(real_dir)),
        ])

        result = apply_stack(project_dir, stack, "0.1.5")

        assert result.success
        assert result.entries[0].installed_id == "real-id"
        assert _read_stack_state(project_dir)["default"] == ["real-id"]
        assert PresetManager(project_dir).registry.is_installed("real-id")

        stack.entries = []
        result = apply_stack(project_dir, stack, "0.1.5")

        assert result.removed == ["real-id"]
        assert not PresetManager(project_dir).registry.is_installed("real-id")

    def test_independently_installed_preset_is_never_touched(self, project_dir, temp_dir):
        """AC5/FR-2035: a preset installed outside of any stack is left alone."""
        beta_dir = _make_preset_dir(temp_dir, "beta")
        PresetManager(project_dir).install_from_directory(beta_dir, "0.1.5", priority=10)

        alpha_dir = _make_preset_dir(temp_dir, "alpha")
        stack = PresetStack(name="default", entries=[
            PresetStackEntry(preset="alpha", priority=5, source=str(alpha_dir)),
        ])
        result = apply_stack(project_dir, stack, "0.1.5")

        assert result.success
        assert result.removed == []
        assert PresetManager(project_dir).registry.is_installed("beta")


# ===== `specify init` integration (US2) =====


_INIT_ARGS = [
    "--integration",
    "generic",
    "--integration-options",
    "--commands-dir .agent/commands",
    "--ignore-agent-tools",
    "--offline",
]


def _init_here(project_dir: Path, extra_args: list[str]):
    """Run `specify init --here --force` inside `project_dir` (merges into the
    `.specify/preset-stacks.yml` a test may have pre-created there)."""
    previous = os.getcwd()
    os.chdir(project_dir)
    try:
        return CliRunner().invoke(
            app,
            ["init", "--here", "--force", *_INIT_ARGS, *extra_args],
            catch_exceptions=True,
        )
    finally:
        os.chdir(previous)


class TestInitPresetStack:
    def test_default_stack_installs_automatically(self, temp_dir):
        """AC1: a defined `default` stack installs automatically when neither
        `--preset` nor `--preset-stack` is given."""
        project_dir = temp_dir / "project"
        project_dir.mkdir()
        gamma_dir = _make_preset_dir(temp_dir, "gamma")
        _write_stacks_config(project_dir, {
            "stacks": [
                {"name": "default", "entries": [{"preset": "gamma", "priority": 5, "source": str(gamma_dir)}]},
            ]
        })

        result = _init_here(project_dir, [])

        assert result.exit_code == 0, result.stdout
        assert PresetManager(project_dir).registry.is_installed("gamma")

    def test_no_default_stack_defined_is_noop(self, temp_dir):
        """AC2: no `default` stack defined -> no stack applied, identical to today."""
        project_dir = temp_dir / "project"
        project_dir.mkdir()
        delta_dir = _make_preset_dir(temp_dir, "delta")
        _write_stacks_config(project_dir, {
            "stacks": [
                {"name": "other", "entries": [{"preset": "delta", "priority": 5, "source": str(delta_dir)}]},
            ]
        })

        result = _init_here(project_dir, [])

        assert result.exit_code == 0, result.stdout
        assert not PresetManager(project_dir).registry.is_installed("delta")

    def test_preset_flag_skips_default_stack(self, temp_dir):
        """AC3: `--preset <id>` given -> `default` is skipped entirely."""
        project_dir = temp_dir / "project"
        project_dir.mkdir()
        gamma_dir = _make_preset_dir(temp_dir, "gamma")
        epsilon_dir = _make_preset_dir(temp_dir, "epsilon")
        _write_stacks_config(project_dir, {
            "stacks": [
                {"name": "default", "entries": [{"preset": "gamma", "priority": 5, "source": str(gamma_dir)}]},
            ]
        })

        result = _init_here(project_dir, ["--preset", str(epsilon_dir)])

        assert result.exit_code == 0, result.stdout
        manager = PresetManager(project_dir)
        assert manager.registry.is_installed("epsilon")
        assert not manager.registry.is_installed("gamma")

    def test_preset_stack_flag_skips_default_stack(self, temp_dir):
        """AC3: `--preset-stack <name>` given -> `default` is skipped entirely,
        and the named stack is applied instead."""
        project_dir = temp_dir / "project"
        project_dir.mkdir()
        gamma_dir = _make_preset_dir(temp_dir, "gamma")
        delta_dir = _make_preset_dir(temp_dir, "delta")
        _write_stacks_config(project_dir, {
            "stacks": [
                {"name": "default", "entries": [{"preset": "gamma", "priority": 5, "source": str(gamma_dir)}]},
                {"name": "other", "entries": [{"preset": "delta", "priority": 5, "source": str(delta_dir)}]},
            ]
        })

        result = _init_here(project_dir, ["--preset-stack", "other"])

        assert result.exit_code == 0, result.stdout
        manager = PresetManager(project_dir)
        assert manager.registry.is_installed("delta")
        assert not manager.registry.is_installed("gamma")

    def test_preset_stack_none_suppresses_default(self, temp_dir):
        """AC4: `--preset-stack none` suppresses `default` even though it exists."""
        project_dir = temp_dir / "project"
        project_dir.mkdir()
        gamma_dir = _make_preset_dir(temp_dir, "gamma")
        _write_stacks_config(project_dir, {
            "stacks": [
                {"name": "default", "entries": [{"preset": "gamma", "priority": 5, "source": str(gamma_dir)}]},
            ]
        })

        result = _init_here(project_dir, ["--preset-stack", "none"])

        assert result.exit_code == 0, result.stdout
        assert not PresetManager(project_dir).registry.is_installed("gamma")

    def test_preset_and_preset_stack_together_rejected(self, temp_dir):
        """AC5: both `--preset` and `--preset-stack` given -> rejected, neither installed."""
        project_name = "newproj"
        previous = os.getcwd()
        os.chdir(temp_dir)
        try:
            result = CliRunner().invoke(
                app,
                [
                    "init",
                    project_name,
                    *_INIT_ARGS,
                    "--preset",
                    "whatever",
                    "--preset-stack",
                    "default",
                ],
                catch_exceptions=True,
            )
        finally:
            os.chdir(previous)

        assert result.exit_code != 0
        assert "--preset" in result.stdout
        assert "--preset-stack" in result.stdout
        assert not (temp_dir / project_name).exists()

    def test_unknown_preset_stack_name_rejected(self, temp_dir):
        """FR-2022: an unknown `--preset-stack <name>` is rejected, naming the
        stack and listing what's defined."""
        project_dir = temp_dir / "project"
        project_dir.mkdir()
        gamma_dir = _make_preset_dir(temp_dir, "gamma")
        _write_stacks_config(project_dir, {
            "stacks": [
                {"name": "default", "entries": [{"preset": "gamma", "priority": 5, "source": str(gamma_dir)}]},
            ]
        })

        result = _init_here(project_dir, ["--preset-stack", "nope"])

        assert result.exit_code != 0
        assert "nope" in result.stdout
        assert "default" in result.stdout


# ===== `specify preset stack` CLI verbs (US3) =====


def _run_stack_cli(project_dir: Path, args: list[str]):
    previous = os.getcwd()
    os.chdir(project_dir)
    try:
        return CliRunner().invoke(app, ["preset", "stack", *args], catch_exceptions=True)
    finally:
        os.chdir(previous)


class TestPresetStackCli:
    def test_list_shows_stacks_with_priorities_and_default_marker(self, project_dir):
        """AC1: `list` shows every stack's name, entries with priorities, and default status."""
        _write_stacks_config(project_dir, {
            "stacks": [
                {"name": "default", "entries": [{"preset": "alpha", "priority": 5}]},
                {"name": "other", "entries": [{"preset": "beta", "priority": 20}]},
            ]
        })

        result = _run_stack_cli(project_dir, ["list"])

        assert result.exit_code == 0, result.stdout
        assert "default" in result.stdout
        assert "other" in result.stdout
        assert "alpha" in result.stdout
        assert "beta" in result.stdout
        assert "5" in result.stdout
        assert "20" in result.stdout

    def test_list_with_no_stacks_defined_exits_zero(self, project_dir):
        result = _run_stack_cli(project_dir, ["list"])
        assert result.exit_code == 0, result.stdout

    def test_install_by_name_only_touches_that_stacks_presets(self, project_dir, temp_dir):
        """AC2: applying a non-default stack by name leaves other installed presets untouched."""
        alpha_dir = _make_preset_dir(temp_dir, "alpha")
        beta_dir = _make_preset_dir(temp_dir, "beta")
        PresetManager(project_dir).install_from_directory(alpha_dir, "0.1.5", priority=10)

        _write_stacks_config(project_dir, {
            "stacks": [
                {"name": "other", "entries": [{"preset": "beta", "priority": 5, "source": str(beta_dir)}]},
            ]
        })

        result = _run_stack_cli(project_dir, ["install", "other"])

        assert result.exit_code == 0, result.stdout
        manager = PresetManager(project_dir)
        assert manager.registry.is_installed("alpha")
        assert manager.registry.is_installed("beta")

    def test_install_unknown_stack_name_rejected(self, project_dir):
        """FR-2022: on-demand `install <name>` CLI path names the requested stack and what's defined."""
        _write_stacks_config(project_dir, {
            "stacks": [{"name": "default", "entries": [{"preset": "alpha", "priority": 5}]}]
        })

        result = _run_stack_cli(project_dir, ["install", "nope"])

        assert result.exit_code != 0
        assert "nope" in result.stdout
        assert "default" in result.stdout

    def test_add_only_edits_config_and_never_installs(self, project_dir):
        result = _run_stack_cli(
            project_dir, ["add", "default", "--preset", "alpha", "--priority", "5"]
        )

        assert result.exit_code == 0, result.stdout
        config = load_stacks_config(project_dir)
        assert config.stacks == [
            PresetStack(name="default", entries=[PresetStackEntry(preset="alpha", priority=5)])
        ]
        assert not PresetManager(project_dir).registry.is_installed("alpha")

    def test_add_updates_existing_entry_in_place(self, project_dir):
        _write_stacks_config(project_dir, {
            "stacks": [{"name": "default", "entries": [{"preset": "alpha", "priority": 5}]}]
        })

        result = _run_stack_cli(
            project_dir, ["add", "default", "--preset", "alpha", "--priority", "20"]
        )

        assert result.exit_code == 0, result.stdout
        config = load_stacks_config(project_dir)
        assert config.stacks == [
            PresetStack(name="default", entries=[PresetStackEntry(preset="alpha", priority=20)])
        ]

    def test_remove_whole_stack(self, project_dir):
        _write_stacks_config(project_dir, {
            "stacks": [
                {"name": "default", "entries": [{"preset": "alpha", "priority": 5}]},
                {"name": "other", "entries": [{"preset": "beta", "priority": 10}]},
            ]
        })

        result = _run_stack_cli(project_dir, ["remove", "default"])

        assert result.exit_code == 0, result.stdout
        config = load_stacks_config(project_dir)
        assert [s.name for s in config.stacks] == ["other"]

    def test_remove_single_entry_only(self, project_dir):
        _write_stacks_config(project_dir, {
            "stacks": [
                {
                    "name": "default",
                    "entries": [
                        {"preset": "alpha", "priority": 5},
                        {"preset": "beta", "priority": 10},
                    ],
                },
            ]
        })

        result = _run_stack_cli(project_dir, ["remove", "default", "--preset", "alpha"])

        assert result.exit_code == 0, result.stdout
        config = load_stacks_config(project_dir)
        assert config.stacks == [
            PresetStack(name="default", entries=[PresetStackEntry(preset="beta", priority=10)])
        ]

    def test_remove_never_uninstalls(self, project_dir, temp_dir):
        """`remove` only edits the config file; it never calls `PresetManager.remove`."""
        alpha_dir = _make_preset_dir(temp_dir, "alpha")
        stack = PresetStack(name="default", entries=[
            PresetStackEntry(preset="alpha", priority=5, source=str(alpha_dir)),
        ])
        apply_stack(project_dir, stack, "0.1.5")
        assert PresetManager(project_dir).registry.is_installed("alpha")
        _write_stacks_config(project_dir, {
            "stacks": [{"name": "default", "entries": [{"preset": "alpha", "priority": 5, "source": str(alpha_dir)}]}],
        })

        result = _run_stack_cli(project_dir, ["remove", "default"])

        assert result.exit_code == 0, result.stdout
        assert PresetManager(project_dir).registry.is_installed("alpha")
