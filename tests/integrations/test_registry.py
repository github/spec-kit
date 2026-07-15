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
    "rovodev", "codebuddy", "qodercli", "amp", "shai", "bob", "trae",
    "pi", "kiro-cli", "vibe", "cursor-agent", "firebender",
    # Stage 4 — TOML integrations
    "gemini", "tabnine",
    # Stage 5 — skills, generic & option-driven integrations
    "codex", "kimi", "agy", "zed", "generic",
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


def _multi_install_safe_orders() -> list[list[str]]:
    safe_keys = _multi_install_safe_keys()
    if len(safe_keys) < 2:
        return [safe_keys]
    return [safe_keys[index:] + safe_keys[:index] for index in range(len(safe_keys))]


def _multi_install_safe_order_id(ordered_keys: list[str]) -> str:
    if not ordered_keys:
        return "no-safe-integrations"
    return f"init-{ordered_keys[0]}"


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

    def test_safe_install_orders_rotate_each_integration_through_init(self):
        safe_keys = _multi_install_safe_keys()
        orders = _multi_install_safe_orders()

        assert len(safe_keys) >= 2
        assert [order[0] for order in orders] == safe_keys
        assert len({tuple(order) for order in orders}) == len(safe_keys)
        assert all(sorted(order) == safe_keys for order in orders)

    @pytest.mark.parametrize("key", _multi_install_safe_keys())
    def test_safe_integrations_have_static_isolated_paths(self, key):
        assert _integration_root_dir(key), (
            f"{key} is declared multi-install safe but has no static root directory"
        )
        assert _integration_commands_dir(key), (
            f"{key} is declared multi-install safe but has no static commands directory"
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

    @pytest.mark.parametrize(
        "ordered_keys",
        _multi_install_safe_orders(),
        ids=_multi_install_safe_order_id,
    )
    def test_safe_integrations_have_disjoint_manifests(
        self,
        tmp_path,
        ordered_keys,
    ):
        # The pairwise disjointness contract is only meaningful with at least
        # two safe integrations. Guard so a shrunken registry fails loudly here
        # rather than passing vacuously (or tripping over ordered_keys[0] below).
        assert len(ordered_keys) >= 2, (
            f"expected at least two multi-install-safe integrations, got {ordered_keys}"
        )

        project_root = tmp_path / "project"
        project_root.mkdir()
        runner = CliRunner()

        # Install every safe integration once into a single project, then assert
        # pairwise manifest isolation. Each safe integration writes only to its
        # own (disjoint) directories and always records what it writes, so a
        # manifest's contents are independent of install order and of which other
        # integrations are co-installed. The parametrized rotations keep the
        # aggregate setup while placing each safe integration first once, so each
        # one still exercises the `specify init --integration ...` path.
        original_cwd = os.getcwd()
        try:
            os.chdir(project_root)
            init_result = runner.invoke(
                app,
                [
                    "init",
                    "--here",
                    "--integration",
                    ordered_keys[0],
                    "--script",
                    "sh",
                    "--ignore-agent-tools",
                ],
                catch_exceptions=False,
            )
            assert init_result.exit_code == 0, init_result.output

            for key in ordered_keys[1:]:
                install_result = runner.invoke(
                    app,
                    ["integration", "install", key, "--script", "sh"],
                    catch_exceptions=False,
                )
                assert install_result.exit_code == 0, install_result.output
        finally:
            os.chdir(original_cwd)

        integrations_dir = project_root / ".specify" / "integrations"
        manifests = {}
        for key in ordered_keys:
            manifest = json.loads(
                (integrations_dir / f"{key}.manifest.json").read_text(encoding="utf-8")
            )
            files = manifest.get("files", {})
            assert isinstance(files, dict), f"{key} manifest files must be an object"
            manifests[key] = set(files.keys())

        for first, second in _multi_install_safe_pairs():
            overlap = manifests[first] & manifests[second]
            assert not overlap, (
                f"{first} and {second} are declared multi-install safe but both manage "
                f"these files: {sorted(overlap)}"
            )

    def test_kiro_cli_is_declared_multi_install_safe(self):
        """kiro-cli confines itself to an isolated ``.kiro/`` root that no
        other integration touches, so it must be declared multi-install safe
        (issue #3471).

        Before the fix, co-installing kiro-cli alongside another integration
        left ``specify integration status`` permanently in ERROR
        (``unsafe-multi-install``) with no way to acknowledge it. The
        parametrized isolation/manifest contracts above already exercise
        kiro-cli once the flag is set; this pins the declaration itself so a
        future edit cannot silently drop it and reintroduce the error.
        """
        assert INTEGRATION_REGISTRY["kiro-cli"].multi_install_safe is True


class TestCatalogParity:
    """The discovery catalog must list every registered integration."""

    def test_every_registered_integration_is_in_catalog(self):
        """``integrations/catalog.json`` must cover every registry key.

        The catalog is the discovery manifest; an integration that is
        registered, registrar-aligned and registry-tested but missing from
        the catalog is undiscoverable through it. ``generic`` is exempt —
        it is the no-fixed-directory fallback, not a catalogued agent.
        """
        from pathlib import Path

        repo_root = Path(__file__).resolve().parents[2]
        catalog = json.loads(
            (repo_root / "integrations" / "catalog.json").read_text(encoding="utf-8")
        )
        catalogued = set(catalog["integrations"])
        registered = set(INTEGRATION_REGISTRY) - {"generic"}
        missing = sorted(registered - catalogued)
        assert not missing, f"integrations missing from catalog.json: {missing}"
