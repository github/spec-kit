"""Tests for INTEGRATION_REGISTRY — mechanics, completeness, and registrar alignment."""

import json
import os
from pathlib import PurePosixPath

import pytest
from typer.testing import CliRunner

from specify_cli import app
from specify_cli.integrations import (
    INTEGRATION_REGISTRY,
    _register,
    get_integration,
)
from specify_cli.integrations.base import MarkdownIntegration
from .conftest import StubIntegration


# Every integration key that must be registered (Stage 2 + Stage 3 + Stage 4 + Stage 5).
ALL_INTEGRATION_KEYS = [
    "copilot",
    # Stage 3 — standard markdown integrations
    "claude", "qwen", "opencode", "junie", "kilocode", "auggie",
    "roo", "codebuddy", "qodercli", "amp", "shai", "bob", "trae",
    "pi", "iflow", "kiro-cli", "windsurf", "vibe", "cursor-agent",
    # Stage 4 — TOML integrations
    "gemini", "tabnine",
    # Stage 5 — skills, generic & option-driven integrations
    "codex", "kimi", "agy", "generic",
]


def _multi_install_safe_keys() -> list[str]:
    return sorted(
        key
        for key, integration in INTEGRATION_REGISTRY.items()
        if integration.multi_install_safe
    )


def _multi_install_safe_pairs() -> list[tuple[str, str]]:
    safe_keys = _multi_install_safe_keys()
    return [
        (safe_keys[left], safe_keys[right])
        for left in range(len(safe_keys))
        for right in range(left + 1, len(safe_keys))
    ]


def _posix_path(value: str | None) -> str | None:
    if not value:
        return None
    return PurePosixPath(value).as_posix()


def _integration_root_dir(key: str) -> str | None:
    integration = INTEGRATION_REGISTRY[key]
    cfg = integration.config if isinstance(integration.config, dict) else {}
    return _posix_path(cfg.get("folder"))


def _integration_commands_dir(key: str) -> str | None:
    integration = INTEGRATION_REGISTRY[key]
    cfg = integration.config if isinstance(integration.config, dict) else {}
    folder = cfg.get("folder")
    if not folder:
        return None
    subdir = cfg.get("commands_subdir", "commands")
    return (PurePosixPath(folder) / subdir).as_posix()


def _paths_overlap(first: str | None, second: str | None) -> bool:
    if not first or not second:
        return False
    left = PurePosixPath(first)
    right = PurePosixPath(second)
    try:
        left.relative_to(right)
        return True
    except ValueError:
        pass
    try:
        right.relative_to(left)
        return True
    except ValueError:
        return False


def _path_is_inside(path: str | None, directory: str | None) -> bool:
    if not path or not directory:
        return False
    try:
        PurePosixPath(path).relative_to(PurePosixPath(directory))
        return True
    except ValueError:
        return False


class TestRegistry:
    def test_registry_is_dict(self):
        assert isinstance(INTEGRATION_REGISTRY, dict)

    def test_register_and_get(self):
        stub = StubIntegration()
        _register(stub)
        try:
            assert get_integration("stub") is stub
        finally:
            INTEGRATION_REGISTRY.pop("stub", None)

    def test_get_missing_returns_none(self):
        assert get_integration("nonexistent-xyz") is None

    def test_register_empty_key_raises(self):
        class EmptyKey(MarkdownIntegration):
            key = ""
        with pytest.raises(ValueError, match="empty key"):
            _register(EmptyKey())

    def test_register_duplicate_raises(self):
        stub = StubIntegration()
        _register(stub)
        try:
            with pytest.raises(KeyError, match="already registered"):
                _register(StubIntegration())
        finally:
            INTEGRATION_REGISTRY.pop("stub", None)


class TestRegistryCompleteness:
    """Every expected integration must be registered."""

    @pytest.mark.parametrize("key", ALL_INTEGRATION_KEYS)
    def test_key_registered(self, key):
        assert key in INTEGRATION_REGISTRY, f"{key} missing from registry"


class TestRegistrarKeyAlignment:
    """Every integration key must have a matching AGENT_CONFIGS entry.

    ``generic`` is excluded because it has no fixed directory — its
    output path comes from ``--commands-dir`` at runtime.
    """

    @pytest.mark.parametrize(
        "key",
        [k for k in ALL_INTEGRATION_KEYS if k != "generic"],
    )
    def test_integration_key_in_registrar(self, key):
        from specify_cli.agents import CommandRegistrar
        assert key in CommandRegistrar.AGENT_CONFIGS, (
            f"Integration '{key}' is registered but has no AGENT_CONFIGS entry"
        )

    def test_no_stale_cursor_shorthand(self):
        """The old 'cursor' shorthand must not appear in AGENT_CONFIGS."""
        from specify_cli.agents import CommandRegistrar
        assert "cursor" not in CommandRegistrar.AGENT_CONFIGS


class TestMultiInstallSafeContracts:
    """Declared safe integrations must stay isolated from each other."""

    @pytest.mark.parametrize("key", _multi_install_safe_keys())
    def test_safe_integrations_have_static_isolated_paths(self, key):
        integration = INTEGRATION_REGISTRY[key]

        assert _integration_root_dir(key), (
            f"{key} is declared multi-install safe but has no static root directory"
        )
        assert _integration_commands_dir(key), (
            f"{key} is declared multi-install safe but has no static commands directory"
        )
        assert integration.context_file, (
            f"{key} is declared multi-install safe but has no context file"
        )

    @pytest.mark.parametrize(("first", "second"), _multi_install_safe_pairs())
    def test_safe_integrations_have_distinct_agent_roots(self, first, second):
        assert not _paths_overlap(_integration_root_dir(first), _integration_root_dir(second)), (
            f"{first} and {second} are declared multi-install safe but have "
            f"overlapping agent roots {_integration_root_dir(first)!r} and "
            f"{_integration_root_dir(second)!r}"
        )

    @pytest.mark.parametrize(("first", "second"), _multi_install_safe_pairs())
    def test_safe_integrations_have_distinct_command_dirs(self, first, second):
        assert not _paths_overlap(_integration_commands_dir(first), _integration_commands_dir(second)), (
            f"{first} and {second} are declared multi-install safe but have "
            f"overlapping command directories {_integration_commands_dir(first)!r} and "
            f"{_integration_commands_dir(second)!r}"
        )

    @pytest.mark.parametrize(("first", "second"), _multi_install_safe_pairs())
    def test_safe_integrations_have_distinct_context_files(self, first, second):
        first_context = _posix_path(INTEGRATION_REGISTRY[first].context_file)
        second_context = _posix_path(INTEGRATION_REGISTRY[second].context_file)

        assert first_context != second_context, (
            f"{first} and {second} are declared multi-install safe but share "
            f"context file {first_context!r}"
        )

    @pytest.mark.parametrize(("first", "second"), _multi_install_safe_pairs())
    def test_safe_context_files_do_not_overlap_other_agent_roots(self, first, second):
        first_context = _posix_path(INTEGRATION_REGISTRY[first].context_file)
        second_context = _posix_path(INTEGRATION_REGISTRY[second].context_file)

        assert not _path_is_inside(first_context, _integration_root_dir(second)), (
            f"{first} context file {first_context!r} lives under {second} "
            f"agent root {_integration_root_dir(second)!r}"
        )
        assert not _path_is_inside(second_context, _integration_root_dir(first)), (
            f"{second} context file {second_context!r} lives under {first} "
            f"agent root {_integration_root_dir(first)!r}"
        )

    @pytest.mark.parametrize(("first", "second"), _multi_install_safe_pairs())
    def test_safe_context_files_do_not_overlap_other_command_dirs(self, first, second):
        first_context = _posix_path(INTEGRATION_REGISTRY[first].context_file)
        second_context = _posix_path(INTEGRATION_REGISTRY[second].context_file)

        assert not _path_is_inside(first_context, _integration_commands_dir(second)), (
            f"{first} context file {first_context!r} lives under {second} "
            f"commands directory {_integration_commands_dir(second)!r}"
        )
        assert not _path_is_inside(second_context, _integration_commands_dir(first)), (
            f"{second} context file {second_context!r} lives under {first} "
            f"commands directory {_integration_commands_dir(first)!r}"
        )

    @pytest.mark.parametrize(("first", "second"), _multi_install_safe_pairs())
    def test_safe_integrations_have_disjoint_manifests(
        self,
        tmp_path,
        first,
        second,
    ):
        for initial, additional in ((first, second), (second, first)):
            project_root = tmp_path / f"project-{initial}-{additional}"
            project_root.mkdir()
            runner = CliRunner()

            original_cwd = os.getcwd()
            try:
                os.chdir(project_root)
                init_result = runner.invoke(
                    app,
                    [
                        "init",
                        "--here",
                        "--integration",
                        initial,
                        "--script",
                        "sh",
                        "--no-git",
                        "--ignore-agent-tools",
                    ],
                    catch_exceptions=False,
                )
                assert init_result.exit_code == 0, init_result.output

                install_result = runner.invoke(
                    app,
                    ["integration", "install", additional, "--script", "sh"],
                    catch_exceptions=False,
                )
                assert install_result.exit_code == 0, install_result.output
            finally:
                os.chdir(original_cwd)

            initial_manifest = json.loads(
                (
                    project_root / ".specify" / "integrations" / f"{initial}.manifest.json"
                ).read_text(encoding="utf-8")
            )
            additional_manifest = json.loads(
                (
                    project_root / ".specify" / "integrations" / f"{additional}.manifest.json"
                ).read_text(encoding="utf-8")
            )

            initial_files = set(initial_manifest.get("files", {}))
            additional_files = set(additional_manifest.get("files", {}))

            assert initial_files.isdisjoint(additional_files), (
                f"{initial} and {additional} are declared multi-install safe but both manage "
                f"these files: {sorted(initial_files & additional_files)}"
            )
