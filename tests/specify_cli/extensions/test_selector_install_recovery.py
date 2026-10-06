"""Install rollback restores new selector state without breaking config rescue."""

import shutil
from pathlib import Path

import pytest

from specify_cli.extensions import ExtensionManager, HookExecutor
from specify_cli.presets import PresetManager
from tests.specify_cli.presets.test_install_transaction import tree_state
from tests.specify_cli.presets.test_selector_provider_lifecycle import (
    COMMAND,
    extension,
    preset,
    project,
)


@pytest.mark.parametrize("kept_config", [False, True])
@pytest.mark.parametrize("cleanup_failure", [False, True])
def test_install_restores_selector_state_despite_cleanup_failure(
    tmp_path, monkeypatch, kept_config, cleanup_failure
):
    root = project(tmp_path, monkeypatch)
    manager = ExtensionManager(root)
    presets = PresetManager(root)
    presets.install_from_directory(
        preset(tmp_path, "fallback", COMMAND, "FALLBACK BODY", True),
        "0.1.5",
        priority=30,
    )
    presets.install_from_directory(
        preset(
            tmp_path, "selector", r"regex:speckit\.provider\..*", "SELECTOR BODY", True
        ),
        "0.1.5",
        priority=5,
    )
    dest = root / ".specify/extensions/provider"
    if kept_config:
        dest.mkdir(parents=True)
        (dest / ".keep-config").write_text("")
        (dest / "provider-config.yml").write_text("USER CONFIG: unchanged\n")
    target = root / f".gemini/commands/{COMMAND}.toml"
    before = tree_state(root)
    primary = OSError("original hook failure")
    hook_failed = False

    def fail_hooks(executor, manifest):
        nonlocal hook_failed
        assert "SELECTOR BODY" in target.read_text()
        assert manager.registry.is_installed("provider")
        hook_failed = True
        raise primary

    original_rmtree = shutil.rmtree
    attempted = []

    def rmtree(path, *args, **kwargs):
        if Path(path) == dest and cleanup_failure and hook_failed:
            attempted.append(path)
            raise OSError("real directory cleanup failure")
        return original_rmtree(path, *args, **kwargs)

    monkeypatch.setattr(HookExecutor, "register_hooks", fail_hooks)
    monkeypatch.setattr(shutil, "rmtree", rmtree)
    with pytest.raises(OSError, match="original hook failure") as error:
        manager.install_from_directory(extension(tmp_path), "0.1.5")
    assert error.value is primary
    assert not manager.registry.is_installed("provider")
    assert not ExtensionManager(root).registry.is_installed("provider")
    after = tree_state(root)

    # Generic unfinished install files are not part of this regression: compare
    # only winner artifacts, ownership, hooks, and caches outside that directory.
    def affected(state):
        return {
            key: value
            for key, value in state.items()
            if not key.startswith(".specify/extensions/provider")
            and not key.startswith(".specify/extensions/.backup")
            and not key.startswith(".specify/extensions/.rescue-staging-")
            and key != ".specify/extensions"
        }

    assert affected(after) == affected(before)
    if cleanup_failure and not kept_config:
        assert attempted
        assert any(
            "real directory cleanup failure" in note for note in primary.__notes__
        )
    if kept_config:
        assert (dest / "provider-config.yml").read_text() == "USER CONFIG: unchanged\n"
        # The established installer may retain completed rescue staging rather
        # than restoring the original keep-config marker. Keep both durable.
        staging = manager._rescue_staging_dir("provider")
        assert (dest / ".keep-config").exists() or (
            staging / ".rescue-complete"
        ).exists()
        if staging.exists():
            assert (
                staging / "provider-config.yml"
            ).read_text() == "USER CONFIG: unchanged\n"
