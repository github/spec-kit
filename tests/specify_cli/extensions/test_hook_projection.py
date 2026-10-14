"""Projection contract and publication failures without changing hook reads."""

import hashlib
import json
from contextlib import contextmanager
from pathlib import Path

import pytest
import yaml

from specify_cli import save_init_options
from specify_cli.extensions import HookExecutor
from specify_cli.extensions._hook_projection import project_hooks


def _config() -> dict:
    return {
        "installed": ["example"],
        "settings": {"auto_execute_hooks": True},
        "hooks": {
            "before_plan": [
                {"extension": "example", "command": "speckit.example.first", "priority": 90, "optional": False},
                {"extension": "example", "command": "speckit.example.skipped", "enabled": False},
                {"extension": "example", "command": "speckit.example.dynamic", "condition": "env.RUN is set"},
                {"extension": "example", "command": "speckit.example.last", "priority": 1, "prompt": "Proceed?"},
            ],
            "after_plan": [],
        },
    }


def _enabled_executor(root: Path) -> HookExecutor:
    save_init_options(root, {"native_extension_hooks": True})
    return HookExecutor(root)


def _assert_snapshot(root: Path, event: str = "before_plan") -> dict:
    cache = root / ".specify" / "hook-dispatch"
    source = (root / ".specify" / "extensions.yml").read_bytes()
    assert (cache / "source.yml").read_bytes() == source
    index = (cache / "events.txt").read_bytes()
    assert index == b"before_plan\nafter_plan\n"
    assert (cache / "events.txt.sha256").read_text().strip() == hashlib.sha256(index).hexdigest()
    payload = (cache / f"{event}.json").read_bytes()
    assert (cache / f"{event}.json.sha256").read_text().strip() == hashlib.sha256(payload).hexdigest()
    return json.loads(payload)


def test_default_save_and_refresh_preserve_legacy_hooks_without_projection(tmp_path):
    executor = HookExecutor(tmp_path)
    config = {"installed": ["example"], "hooks": {"custom:after": [
        {"extension": "example", "command": "speckit.example.legacy"}
    ]}}
    executor.save_project_config(config)
    source = executor.config_file.read_bytes()
    executor.migrate_project_config()
    assert executor.config_file.read_bytes() == source
    assert executor.get_hooks_for_event("custom:after")[0]["command"] == (
        "speckit.example.legacy"
    )
    assert not (tmp_path / ".specify/hook-dispatch").exists()


def test_default_hook_lifecycle_keeps_legacy_event_without_projection(tmp_path):
    executor = HookExecutor(tmp_path)
    config = {"installed": ["example"], "hooks": {"custom:after": [
        {"extension": "example", "command": "speckit.example.legacy"}
    ]}}
    executor.save_project_config(config)
    executor.disable_hooks("example")
    assert not executor.get_hooks_for_event("custom:after")
    executor.enable_hooks("example")
    assert executor.get_hooks_for_event("custom:after")
    executor.unregister_hooks("example")
    assert not executor.get_hooks_for_event("custom:after")
    assert not (tmp_path / ".specify/hook-dispatch").exists()


@pytest.mark.parametrize("invalid", ["true", 1, None, []])
def test_non_boolean_opt_in_is_rejected_without_writing_projection(tmp_path, invalid):
    save_init_options(tmp_path, {"native_extension_hooks": invalid})
    executor = HookExecutor(tmp_path)
    with pytest.raises(ValueError, match="native_extension_hooks.*expected true or false"):
        executor.save_project_config(_config())
    assert not executor.config_file.exists()
    assert not (tmp_path / ".specify/hook-dispatch").exists()


def test_opt_out_retires_prior_projection_and_restores_legacy_writes(tmp_path):
    executor = _enabled_executor(tmp_path)
    executor.save_project_config(_config())
    cache = tmp_path / ".specify/hook-dispatch"
    assert cache.exists()
    save_init_options(tmp_path, {"native_extension_hooks": False})
    legacy = {"hooks": {"custom:after": [
        {"extension": "example", "command": "speckit.example.legacy"}
    ]}}
    executor.save_project_config(legacy)
    executor.migrate_project_config()
    assert not cache.exists()
    assert executor.get_hooks_for_event("custom:after")[0]["command"] == (
        "speckit.example.legacy"
    )
    save_init_options(tmp_path, {"native_extension_hooks": True})
    with pytest.raises(ValueError, match="Rename legacy events"):
        executor.migrate_project_config()
    assert not cache.exists()


def test_save_projects_only_unconditional_enabled_hooks_in_yaml_order(tmp_path):
    executor = _enabled_executor(tmp_path)
    executor.save_project_config(_config())
    result = _assert_snapshot(tmp_path)
    assert result == {
        "event": "before_plan",
        "hooks": [
            {"extension": "example", "command": "speckit.example.first", "optional": False,
             "description": "", "prompt": "", "priority": 90},
            {"extension": "example", "command": "speckit.example.last", "optional": True,
             "description": "", "prompt": "Proceed?", "priority": 1},
        ],
    }
    assert json.loads((tmp_path / ".specify/hook-dispatch/after_plan.json").read_text()) == {
        "event": "after_plan", "hooks": []
    }
    assert [hook["command"] for hook in executor.get_hooks_for_event("before_plan")] == [
        "speckit.example.last", "speckit.example.dynamic",
        "speckit.example.first",
    ]


@pytest.mark.parametrize("bad", [
    {"hooks": {42: []}},
    {"hooks": {"custom:after": []}},
    {"hooks": {"../before_plan": []}},
    {"hooks": {"before_speckit.bug.assess": []}},
    {"hooks": {"before_": []}},
    {"hooks": {"after_Bug": []}},
    {"hooks": {"before_" + "a" * 250: []}},
    {"hooks": {"before_plan": [None]}},
    {"hooks": {"before_plan": [{"extension": "a", "command": "b", "optional": "yes"}]}},
    {"hooks": {"before_plan": [{"extension": "a", "command": "b", "condition": 7}]}},
    {"hooks": {"before_plan": [{"extension": "a", "command": "b\0"}]}},
])
def test_invalid_inputs_leave_existing_config_and_projection_unchanged(tmp_path, bad):
    executor = _enabled_executor(tmp_path)
    executor.save_project_config(_config())
    old_source = executor.config_file.read_bytes()
    old_projection = (tmp_path / ".specify/hook-dispatch/before_plan.json").read_bytes()
    with pytest.raises(ValueError):
        executor.save_project_config(bad)
    assert executor.config_file.read_bytes() == old_source
    assert (tmp_path / ".specify/hook-dispatch/before_plan.json").read_bytes() == old_projection


def test_update_and_refresh_retire_stale_events_and_preserve_crlf(tmp_path):
    executor = _enabled_executor(tmp_path)
    executor.save_project_config(_config())
    updated = _config()
    updated["hooks"] = {"after_tasks": []}
    executor.save_project_config(updated)
    assert not (tmp_path / ".specify/hook-dispatch/before_plan.json").exists()
    assert (tmp_path / ".specify/hook-dispatch/events.txt").read_bytes() == b"after_tasks\n"
    executor.config_file.write_bytes(executor.config_file.read_bytes().replace(b"\n", b"\r\n"))
    executor.migrate_project_config()
    assert (tmp_path / ".specify/hook-dispatch/source.yml").read_bytes() == executor.config_file.read_bytes()
    assert b"\r\n" in executor.config_file.read_bytes()


def test_refresh_projects_exact_source_read_under_lock(tmp_path, monkeypatch):
    import specify_cli.extensions._hook_projection as projection

    executor = _enabled_executor(tmp_path)
    executor.save_project_config(_config())
    updated = {"installed": ["example"], "hooks": {"after_tasks": []}}
    original_lock = projection._exclusive_project_lock

    @contextmanager
    def concurrent_save(*args, **kwargs):
        with original_lock(*args, **kwargs):
            executor.config_file.write_text(
                yaml.safe_dump(updated, sort_keys=False), encoding="utf-8"
            )
            yield

    monkeypatch.setattr(projection, "_exclusive_project_lock", concurrent_save)
    executor.migrate_project_config()
    cache = tmp_path / ".specify/hook-dispatch"
    assert (cache / "source.yml").read_bytes() == executor.config_file.read_bytes()
    assert (cache / "events.txt").read_bytes() == b"after_tasks\n"
    assert json.loads((cache / "after_tasks.json").read_text())["hooks"] == []
    assert not (cache / "before_plan.json").exists()


def test_refuse_unsafe_cache_and_invalid_existing_config(tmp_path):
    executor = _enabled_executor(tmp_path)
    executor.save_project_config(_config())
    cache = tmp_path / ".specify/hook-dispatch"
    (cache / "unexpected").mkdir()
    original = executor.config_file.read_bytes()
    with pytest.raises(ValueError, match="non-file"):
        executor.load_project_config_for_update()
    with pytest.raises(ValueError, match="non-file"):
        executor.save_project_config(_config())
    assert executor.config_file.read_bytes() == original
    (cache / "unexpected").rmdir()
    executor.config_file.write_text("hooks:\n  before_plan: invalid\n")
    with pytest.raises(ValueError, match="expected a list"):
        executor.load_project_config_for_update()


def test_refuse_symlinked_config_and_cache_before_mutation(tmp_path):
    executor = _enabled_executor(tmp_path)
    executor.config_file.parent.mkdir(exist_ok=True)
    external = tmp_path / "external.yml"
    external.write_text("hooks: {}\n", encoding="utf-8")
    try:
        executor.config_file.symlink_to(external)
    except (OSError, NotImplementedError):
        pytest.skip("symlinks unavailable")
    with pytest.raises(ValueError, match="symlinked"):
        executor.save_project_config(_config())
    assert external.read_text() == "hooks: {}\n"
    executor.config_file.unlink()
    executor.config_file.write_text("hooks: {}\n")
    (tmp_path / ".specify/hook-dispatch").symlink_to(tmp_path, target_is_directory=True)
    with pytest.raises(ValueError, match="symlinked"):
        executor.load_project_config_for_update()
    assert executor.config_file.read_text() == "hooks: {}\n"


def test_publication_failure_restores_prior_pair(tmp_path, monkeypatch):
    import specify_cli.extensions._hook_projection as projection

    executor = _enabled_executor(tmp_path)
    executor.save_project_config(_config())
    source = executor.config_file.read_bytes()
    payload = (tmp_path / ".specify/hook-dispatch/before_plan.json").read_bytes()
    real_replace = projection.os.replace

    def fail_config_write(src, dst):
        if Path(dst) == executor.config_file:
            raise OSError("simulated config write failure")
        return real_replace(src, dst)

    monkeypatch.setattr(projection.os, "replace", fail_config_write)
    with pytest.raises(OSError, match="simulated config"):
        executor.save_project_config({"installed": [], "hooks": {}})
    assert executor.config_file.read_bytes() == source
    assert (tmp_path / ".specify/hook-dispatch/before_plan.json").read_bytes() == payload
    _assert_snapshot(tmp_path)
    assert not list((tmp_path / ".specify").glob(".hook-stage-*"))


def test_unreadable_existing_config_does_not_allocate_stage(tmp_path):
    executor = _enabled_executor(tmp_path)
    executor.config_file.parent.mkdir(exist_ok=True)
    executor.config_file.mkdir()
    with pytest.raises(OSError):
        executor.save_project_config(_config())
    assert not list(executor.config_file.parent.glob(".hook-stage-*"))
    assert not (tmp_path / ".specify/hook-dispatch").exists()


def test_backup_cleanup_failure_warns_after_successful_publication(tmp_path, monkeypatch, caplog):
    import specify_cli.extensions._hook_projection as projection

    executor = _enabled_executor(tmp_path)
    executor.save_project_config(_config())
    real_rmtree = projection.shutil.rmtree

    def fail_backup_cleanup(path, *args, **kwargs):
        if str(path).endswith(".backup"):
            raise OSError("backup cleanup failed")
        return real_rmtree(path, *args, **kwargs)

    monkeypatch.setattr(projection.shutil, "rmtree", fail_backup_cleanup)
    updated = {"installed": ["example"], "hooks": {"after_plan": []}}
    executor.save_project_config(updated)
    assert "backup cleanup failed" in caplog.text
    assert yaml.safe_load(executor.config_file.read_text(encoding="utf-8")) == updated
    assert (tmp_path / ".specify/hook-dispatch/source.yml").read_bytes() == executor.config_file.read_bytes()
    assert (tmp_path / ".specify/hook-dispatch/events.txt").read_bytes() == b"after_plan\n"
    assert not (tmp_path / ".specify/hook-dispatch/before_plan.json").exists()


def test_existing_yaml_refresh_keeps_legacy_read_semantics(tmp_path):
    executor = _enabled_executor(tmp_path)
    executor.config_file.parent.mkdir(exist_ok=True)
    existing = _config()
    executor.config_file.write_text(yaml.safe_dump(existing, sort_keys=False))
    old = executor.check_hooks_for_event("before_plan")
    executor.migrate_project_config()
    assert executor.check_hooks_for_event("before_plan") == old
    _assert_snapshot(tmp_path)


def test_enable_disable_remove_republish_without_stale_hooks(tmp_path):
    executor = _enabled_executor(tmp_path)
    executor.save_project_config(_config())
    executor.disable_hooks("example")
    assert _assert_snapshot(tmp_path)["hooks"] == []
    executor.enable_hooks("example")
    assert [hook["command"] for hook in _assert_snapshot(tmp_path)["hooks"]] == [
        "speckit.example.first", "speckit.example.skipped", "speckit.example.last"
    ]
    executor.unregister_hooks("example")
    assert not (tmp_path / ".specify/hook-dispatch/before_plan.json").exists()
    assert (tmp_path / ".specify/hook-dispatch/events.txt").read_bytes() == b""


def test_shared_infrastructure_refresh_projects_existing_config(tmp_path, monkeypatch):
    import specify_cli

    executor = _enabled_executor(tmp_path)
    executor.config_file.parent.mkdir(exist_ok=True)
    executor.config_file.write_text(yaml.safe_dump(_config(), sort_keys=False), encoding="utf-8")
    monkeypatch.setattr(specify_cli, "_install_shared_infra_impl", lambda *args, **kwargs: True)
    assert specify_cli._install_shared_infra(tmp_path, "sh", refresh_managed=True)
    _assert_snapshot(tmp_path)


def test_project_hooks_is_pure():
    config = _config()
    original = yaml.safe_dump(config)
    project_hooks(config)
    assert yaml.safe_dump(config) == original


def test_arbitrary_command_event_refresh_preserves_hook_reader_behavior(tmp_path):
    executor = _enabled_executor(tmp_path)
    executor.config_file.parent.mkdir(exist_ok=True)
    existing = {"hooks": {
        "before_my_command": [
            {"extension": "example", "command": "speckit.example.one", "priority": 30},
            {"extension": "example", "command": "speckit.example.two", "priority": 2},
        ],
        "after_bug_assess": [
            {"extension": "example", "command": "speckit.example.extension"}
        ],
        "before_2fa_assess": [],
    }}
    executor.config_file.write_text(yaml.safe_dump(existing, sort_keys=False))
    before = {
        event: executor.get_hooks_for_event(event)
        for event in existing["hooks"]
    }
    executor.migrate_project_config()
    assert {
        event: executor.get_hooks_for_event(event)
        for event in existing["hooks"]
    } == before
    cache = tmp_path / ".specify/hook-dispatch"
    assert json.loads((cache / "before_my_command.json").read_text())["event"] == "before_my_command"
    assert (cache / "events.txt").read_bytes() == (
        b"before_my_command\nafter_bug_assess\nbefore_2fa_assess\n"
    )
    assert json.loads((cache / "after_bug_assess.json").read_text())["event"] == "after_bug_assess"


def test_refresh_rejects_legacy_event_with_actionable_error(tmp_path):
    executor = _enabled_executor(tmp_path)
    executor.save_project_config(_config())
    cache = tmp_path / ".specify/hook-dispatch"
    old_index = (cache / "events.txt").read_bytes()
    executor.config_file.write_text("hooks:\n  custom:after: []\n", encoding="utf-8")
    with pytest.raises(ValueError, match="Rename legacy events"):
        executor.migrate_project_config()
    assert executor.config_file.read_text() == "hooks:\n  custom:after: []\n"
    assert (cache / "events.txt").read_bytes() == old_index


@pytest.mark.parametrize("value,expected", [
    ("7", 7), (False, 10), ("invalid", 10), (-1, 10),
    (2147483648, 10), (float("inf"), 10),
])
def test_project_hooks_normalizes_legacy_priorities(value, expected):
    config = {"hooks": {"after_plan": [
        {"extension": "example", "command": "speckit.example.run", "priority": value}
    ]}}
    assert json.loads(project_hooks(config)["after_plan"])["hooks"][0]["priority"] == expected
