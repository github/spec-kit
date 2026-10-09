"""Positive and negative coverage for pre/post extension hook resolution."""

import json
import shutil
import os
import subprocess
import sys
import hashlib
import threading
from contextlib import contextmanager
from functools import lru_cache
from pathlib import Path

import pytest
import yaml
from tests.conftest import _has_working_bash

ROOT = Path(__file__).parent.parent
PYTHON = ROOT / "scripts" / "python"


@lru_cache(maxsize=1)
def _bash_available():
    return _has_working_bash()


def bash_script(path):
    if os.name == "nt":
        if not _bash_available():
            pytest.skip("working Git Bash not available on Windows")
        return ["bash", str(path)]
    return [str(path)]


def run_hook(tmp_path, phase="pre", name="plan", variant="py", extra_env=None):
    scripts = {
        "py": [sys.executable, str(PYTHON / f"{phase}_hooks.py")],
        "sh": [str(ROOT / "scripts" / "bash" / f"{phase}-hooks.sh")],
        "ps": ["pwsh", "-NoProfile", "-File", str(ROOT / "scripts" / "powershell" / f"{phase}-hooks.ps1")],
    }
    if variant == "sh":
        scripts["sh"] = bash_script(ROOT / "scripts" / "bash" / f"{phase}-hooks.sh")
    env = os.environ.copy()
    env["SPECKIT_PYTHON_EXECUTABLE"] = sys.executable
    if extra_env:
        env.update(extra_env)
    result = subprocess.run(
        scripts[variant] + [name], cwd=tmp_path, env=env,
        capture_output=True, text=True, encoding="utf-8", check=False,
    )
    return result.returncode, json.loads(result.stdout)


def write_config(tmp_path, text):
    path = tmp_path / ".specify" / "extensions.yml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


@pytest.mark.parametrize("phase", ["pre", "post"])
@pytest.mark.parametrize("variant", ["py", "sh", "ps"])
def test_absent_config_returns_empty(tmp_path, phase, variant):
    if variant == "ps" and not shutil.which("pwsh"):
        pytest.skip("PowerShell not installed")
    code, data = run_hook(tmp_path, phase, variant=variant)
    assert code == 0
    assert data == {"event": f"{'before' if phase == 'pre' else 'after'}_plan", "hooks": []}


def test_hooks_sorted_and_filtered_with_stable_ties(tmp_path):
    write_config(tmp_path, yaml.safe_dump({"hooks": {"before_plan": [
        {"extension": "late", "command": "speckit.late.run", "priority": 20, "optional": False},
        {"extension": "first", "command": "speckit.first.run", "priority": 5, "optional": False},
        {"extension": "second", "command": "speckit.second.run", "priority": "5", "prompt": "Run second?"},
        {"extension": "disabled", "command": "speckit.disabled.run", "enabled": False},
        {"extension": "conditional", "command": "speckit.conditional.run", "condition": "env.CI is set"},
        {"extension": "default", "command": "speckit.default.run"},
    ]}}, sort_keys=False))
    code, data = run_hook(tmp_path)
    assert code == 0
    assert [h["extension"] for h in data["hooks"]] == ["first", "second", "default", "late"]
    assert [h["priority"] for h in data["hooks"]] == [5, 5, 10, 20]
    assert data["hooks"][0]["optional"] is False
    assert data["hooks"][1]["prompt"] == "Run second?"
    assert data["hooks"][2]["optional"] is True
    assert data["hooks"][2]["description"] == ""


def test_post_rereads_config_and_only_returns_matching_event(tmp_path):
    config = write_config(tmp_path, "hooks:\n  after_plan: []\n")
    assert run_hook(tmp_path, "post")[1]["hooks"] == []
    config.write_text("hooks:\n  after_plan:\n    - extension: git\n      command: speckit.git.commit\n", encoding="utf-8")
    assert run_hook(tmp_path, "post")[1]["hooks"][0]["command"] == "speckit.git.commit"
    assert run_hook(tmp_path, "pre")[1]["hooks"] == []


@pytest.mark.parametrize("text,part", [
    ("hooks: [wrong]", "hooks mapping"),
    ("[]", "hooks mapping"),
    ("hooks:\n  before_plan: wrong\n", "must be a list"),
    ("hooks:\n  before_plan:\n    - wrong\n", "must be a mapping"),
    ("hooks:\n  before_plan:\n    - extension: git\n", "needs extension and command"),
    ("hooks:\n  before_plan:\n    - extension: git\n      command: speckit.git.commit\n      enabled: 'false'\n", "enabled must be a boolean"),
    ("hooks:\n  before_plan:\n    - extension: git\n      command: speckit.git.commit\n      optional: 'false'\n", "optional must be a boolean"),
    ("hooks:\n  before_plan:\n    - extension: git\n      command: speckit.git.commit\n      prompt: [not, text]\n", "prompt must be a string"),
    ("hooks: [\n", "Could not read"),
])
@pytest.mark.parametrize("phase", ["pre", "post"])
def test_invalid_config_reports_error(tmp_path, text, part, phase):
    if phase == "post":
        text = text.replace("before_plan", "after_plan")
    write_config(tmp_path, text)
    code, data = run_hook(tmp_path, phase)
    assert code == 1
    assert part in data["error"]
    assert data["hooks"] == []


@pytest.mark.parametrize("variant", ["py", "sh", "ps"])
@pytest.mark.parametrize("phase", ["pre", "post"])
@pytest.mark.parametrize("invalid_event", ["invalid_event", "before_Bad"])
def test_legacy_rejects_invalid_event_even_when_other_hooks_are_valid(
    tmp_path, variant, phase, invalid_event
):
    if variant == "ps" and not shutil.which("pwsh"):
        pytest.skip("PowerShell not installed")
    requested = f"{'before' if phase == 'pre' else 'after'}_plan"
    write_config(tmp_path, yaml.safe_dump({"hooks": {
        requested: [{"extension": "git", "command": "speckit.git.commit"}],
        invalid_event: [],
    }}, sort_keys=False))

    code, data = run_hook(tmp_path, phase, variant=variant)
    assert code == 1
    assert data["hooks"] == []
    assert "hook event" in data["error"]


@pytest.mark.parametrize("priority,expected", [
    (False, 10), (0, 10), ("bad", 10), ("2", 2), (2.8, 2),
])
def test_legacy_priority_normalization(tmp_path, priority, expected):
    write_config(tmp_path, yaml.safe_dump({"hooks": {"before_plan": [
        {"extension": "git", "command": "speckit.git.commit", "priority": priority}
    ]}}))
    code, data = run_hook(tmp_path)
    assert code == 0
    assert data["hooks"][0]["priority"] == expected


@pytest.mark.parametrize("phase", ["pre", "post"])
def test_invalid_command_name_does_not_read_config(tmp_path, phase):
    write_config(tmp_path, "hooks: [\n")
    code, data = run_hook(tmp_path, phase, "../../bad")
    assert code == 1
    assert "Invalid hook event" in data["error"]
    assert data["event"] == f"{'before' if phase == 'pre' else 'after'}_../../bad"


@pytest.mark.parametrize("variant", ["sh", "ps", "py"])
@pytest.mark.parametrize("phase", ["pre", "post"])
def test_installed_mapping_metadata_does_not_hide_hooks(tmp_path, variant, phase):
    if variant == "ps" and not shutil.which("pwsh"):
        pytest.skip("PowerShell not installed")
    from specify_cli.extensions import HookExecutor

    event = f"{'before' if phase == 'pre' else 'after'}_plan"
    HookExecutor(tmp_path).save_project_config({
        "installed": [{"id": "git", "version": "1.0.0"}, "agent-context"],
        "hooks": {event: [{"extension": "git", "command": "speckit.git.commit"}]},
    })
    code, data = run_hook(tmp_path, phase, variant=variant)
    assert code == 0
    assert data == run_hook(tmp_path, phase)[1]
    assert data["hooks"][0]["command"] == "speckit.git.commit"


@pytest.mark.parametrize("variant", ["sh", "ps", "py"])
def test_documented_indented_installed_mapping(tmp_path, variant):
    if variant == "ps" and not shutil.which("pwsh"):
        pytest.skip("PowerShell not installed")
    write_config(tmp_path, (
        'installed:\n  - id: jira\n    version: "1.0.0"  # Pin to specific version\n'
        'hooks:\n  before_plan:\n    - extension: git\n      command: speckit.git.commit\n'
    ))
    code, data = run_hook(tmp_path, variant=variant)
    assert code == 0
    assert data["hooks"][0]["command"] == "speckit.git.commit"


@pytest.mark.parametrize("variant", ["sh", "ps", "py"])
def test_malformed_installed_mapping_rejected(tmp_path, variant):
    if variant == "ps" and not shutil.which("pwsh"):
        pytest.skip("PowerShell not installed")
    write_config(tmp_path, (
        "installed:\n- id: jira\n  version: [unfinished\n"
        "hooks:\n  before_plan: []\n"
    ))
    code, data = run_hook(tmp_path, variant=variant)
    assert code == 1
    assert data["hooks"] == []


@pytest.mark.parametrize("variant", ["sh", "ps", "py"])
@pytest.mark.parametrize("phase", ["pre", "post"])
@pytest.mark.parametrize("missing", ["extension", "command"])
def test_non_target_event_requires_identifiers(tmp_path, variant, phase, missing):
    if variant == "ps" and not shutil.which("pwsh"):
        pytest.skip("PowerShell not installed")
    field = "command: speckit.git.commit" if missing == "extension" else "extension: git"
    write_config(tmp_path, (
        "hooks:\n"
        f"  {'after' if phase == 'pre' else 'before'}_plan:\n"
        f"    - {field}\n"
    ))
    code, data = run_hook(tmp_path, phase, variant=variant)
    assert code == 1
    assert "needs extension and command" in data["error"]
    assert data["hooks"] == []


def test_empty_condition_and_enabled_default_still_execute(tmp_path):
    write_config(tmp_path, "hooks:\n  before_plan:\n    - extension: git\n      command: speckit.git.commit\n      condition: ''\n")
    assert len(run_hook(tmp_path)[1]["hooks"]) == 1


def test_missing_yaml_dependency_is_reported_not_silently_skipped(tmp_path):
    write_config(tmp_path, "hooks:\n  before_plan: []\n")
    result = subprocess.run(
        [sys.executable, "-I", "-S", str(PYTHON / "pre_hooks.py"), "plan"],
        cwd=tmp_path, capture_output=True, text=True,
    )
    assert result.returncode == 1
    assert json.loads(result.stdout) == {
        "event": "before_plan", "hooks": [],
        "error": "PyYAML is required to read .specify/extensions.yml",
    }


@pytest.mark.parametrize("variant", ["sh", "ps", "py"])
def test_materialized_projection_resolves_without_yaml_or_native_parsing(tmp_path, variant):
    if variant == "ps" and not shutil.which("pwsh"):
        pytest.skip("PowerShell not installed")
    from specify_cli.extensions import HookExecutor

    HookExecutor(tmp_path).save_project_config({"hooks": {"before_plan": [
        {"extension": "late", "command": "speckit.late.run", "priority": 20, "prompt": "😀"},
        {"extension": "first", "command": "speckit.first.run", "priority": 5},
    ]}})
    projected = tmp_path / ".specify/hook-dispatch/before_plan.json"
    assert projected.is_file()
    assert (tmp_path / ".specify/hook-dispatch/events.txt").read_bytes() == b"before_plan\n"
    assert b"\r" not in (tmp_path / ".specify/hook-dispatch/events.txt.sha256").read_bytes()
    assert b"\r" not in (tmp_path / ".specify/hook-dispatch/before_plan.sha256").read_bytes()
    assert [h["extension"] for h in json.loads(projected.read_text(encoding="utf-8"))["hooks"]] == [
        "first", "late",
    ]
    code, data = run_hook(tmp_path, variant=variant)
    assert code == 0
    assert data["hooks"][1]["prompt"] == "😀"
    assert data == run_hook(tmp_path)[1]
    if variant == "py":
        result = subprocess.run(
            [sys.executable, "-I", "-S", str(PYTHON / "pre_hooks.py"), "plan"],
            cwd=tmp_path, capture_output=True, text=True, encoding="utf-8", check=False,
        )
        assert result.returncode == 0, result.stderr
        assert json.loads(result.stdout) == data


@pytest.mark.parametrize("variant", ["sh", "ps", "py"])
def test_projection_rejects_stale_yaml_and_recovers_after_refresh(tmp_path, variant):
    if variant == "ps" and not shutil.which("pwsh"):
        pytest.skip("PowerShell not installed")
    from specify_cli.extensions import HookExecutor

    executor = HookExecutor(tmp_path)
    executor.save_project_config({"hooks": {"before_plan": [
        {"extension": "old", "command": "speckit.old.run"},
    ]}})
    config = tmp_path / ".specify/extensions.yml"
    config.write_text(
        "hooks:\n  before_plan:\n    - extension: new\n      command: speckit.new.run\n",
        encoding="utf-8",
    )
    code, data = run_hook(tmp_path, variant=variant)
    assert code == 1
    assert data["hooks"] == []
    assert "stale" in data["error"]
    executor.migrate_project_config()
    code, data = run_hook(tmp_path, variant=variant)
    assert code == 0
    assert [hook["extension"] for hook in data["hooks"]] == ["new"]


@pytest.mark.parametrize("variant", ["sh", "ps", "py"])
def test_projection_missing_entry_fails_instead_of_skipping_hook(tmp_path, variant):
    if variant == "ps" and not shutil.which("pwsh"):
        pytest.skip("PowerShell not installed")
    from specify_cli.extensions import HookExecutor

    HookExecutor(tmp_path).save_project_config({"hooks": {"before_plan": [
        {"extension": "git", "command": "speckit.git.commit"},
    ]}})
    (tmp_path / ".specify/hook-dispatch/before_plan.json").unlink()
    code, data = run_hook(tmp_path, variant=variant)
    assert code == 1
    assert data["hooks"] == []
    assert "incomplete" in data["error"]
    assert run_hook(tmp_path, name="tasks", variant=variant)[1]["hooks"] == []


@pytest.mark.parametrize("variant", ["sh", "ps", "py"])
def test_projection_missing_cache_fails_instead_of_using_legacy_yaml(tmp_path, variant):
    if variant == "ps" and not shutil.which("pwsh"):
        pytest.skip("PowerShell not installed")
    from specify_cli.extensions import HookExecutor

    HookExecutor(tmp_path).save_project_config({"hooks": {"before_plan": [
        {"extension": "git", "command": "speckit.git.commit"},
    ]}})
    (tmp_path / ".specify/hook-dispatch").rename(tmp_path / "removed-cache")
    code, data = run_hook(tmp_path, variant=variant)
    assert code == 1
    assert data["hooks"] == []
    assert "missing" in data["error"]


@pytest.mark.parametrize("variant", ["sh", "ps", "py"])
def test_projection_removes_old_event_after_config_save(tmp_path, variant):
    if variant == "ps" and not shutil.which("pwsh"):
        pytest.skip("PowerShell not installed")
    from specify_cli.extensions import HookExecutor

    executor = HookExecutor(tmp_path)
    executor.save_project_config({"hooks": {"before_plan": [
        {"extension": "git", "command": "speckit.git.commit"},
    ]}})
    executor.save_project_config({"hooks": {}})
    assert not (tmp_path / ".specify/hook-dispatch/before_plan.json").exists()
    code, data = run_hook(tmp_path, variant=variant)
    assert code == 0
    assert data["hooks"] == []


def test_invalid_projected_hook_cannot_replace_existing_projection(tmp_path):
    from specify_cli.extensions import HookExecutor

    executor = HookExecutor(tmp_path)
    executor.save_project_config({"hooks": {"before_plan": [
        {"extension": "git", "command": "speckit.git.commit"},
    ]}})
    before = (tmp_path / ".specify/extensions.yml").read_bytes()
    with pytest.raises(ValueError, match="condition must be a string or null"):
        executor.save_project_config({"hooks": {"after_plan": [
            {"extension": "other", "command": "speckit.other.run", "condition": False},
        ]}})
    assert (tmp_path / ".specify/extensions.yml").read_bytes() == before
    assert run_hook(tmp_path)[1]["hooks"][0]["extension"] == "git"


@pytest.mark.parametrize("variant", ["sh", "ps", "py"])
@pytest.mark.parametrize("replacement", [
    b'{"event":"before_plan","hooks":[\n',
    b'{"event":"before_tasks","hooks":[]}\n',
    b'{"event":"before_plan","hooks":{}}\n',
])
def test_corrupt_projection_reports_error(tmp_path, variant, replacement):
    if variant == "ps" and not shutil.which("pwsh"):
        pytest.skip("PowerShell not installed")
    from specify_cli.extensions import HookExecutor

    HookExecutor(tmp_path).save_project_config({"hooks": {"before_plan": [
        {"extension": "git", "command": "speckit.git.commit"},
    ]}})
    cache = tmp_path / ".specify/hook-dispatch"
    (cache / "before_plan.json").write_bytes(replacement)
    (cache / "before_plan.sha256").write_text(
        hashlib.sha256(replacement).hexdigest() + "\n", encoding="utf-8",
    )
    code, data = run_hook(tmp_path, variant=variant)
    assert code == 1
    assert data["hooks"] == []
    assert "projection" in data["error"]


@pytest.mark.parametrize("variant", ["sh", "ps", "py"])
def test_projection_modified_without_new_digest_is_rejected(tmp_path, variant):
    if variant == "ps" and not shutil.which("pwsh"):
        pytest.skip("PowerShell not installed")
    from specify_cli.extensions import HookExecutor

    HookExecutor(tmp_path).save_project_config({"hooks": {"before_plan": [
        {"extension": "git", "command": "speckit.git.commit"},
    ]}})
    (tmp_path / ".specify/hook-dispatch/before_plan.json").write_text(
        '{"event":"before_plan","hooks":[]}\n', encoding="utf-8",
    )
    code, data = run_hook(tmp_path, variant=variant)
    assert code == 1
    assert data["hooks"] == []
    assert "invalid" in data["error"]


@pytest.mark.parametrize("variant", ["sh", "ps", "py"])
def test_truncated_event_index_cannot_hide_mandatory_hooks(tmp_path, variant):
    if variant == "ps" and not shutil.which("pwsh"):
        pytest.skip("PowerShell not installed")
    from specify_cli.extensions import HookExecutor

    HookExecutor(tmp_path).save_project_config({"hooks": {"before_plan": [
        {"extension": "git", "command": "speckit.git.commit", "optional": False},
    ]}})
    cache = tmp_path / ".specify/hook-dispatch"
    (cache / "events.txt").write_bytes(b"")
    (cache / "before_plan.json").unlink()
    code, data = run_hook(tmp_path, variant=variant)
    assert code == 1
    assert data["hooks"] == []
    assert "index" in data["error"]


@pytest.mark.parametrize("variant", ["sh", "ps", "py"])
def test_semantically_invalid_projected_hook_is_rejected(tmp_path, variant):
    if variant == "ps" and not shutil.which("pwsh"):
        pytest.skip("PowerShell not installed")
    from specify_cli.extensions import HookExecutor

    HookExecutor(tmp_path).save_project_config({"hooks": {"before_plan": [
        {"extension": "git", "command": "speckit.git.commit"},
    ]}})
    cache = tmp_path / ".specify/hook-dispatch"
    payload = b'{"event":"before_plan","hooks":[{"extension":1}]}\n'
    (cache / "before_plan.json").write_bytes(payload)
    (cache / "before_plan.sha256").write_text(
        hashlib.sha256(payload).hexdigest() + "\n", encoding="utf-8",
    )
    code, data = run_hook(tmp_path, variant=variant)
    assert code == 1
    assert data["hooks"] == []
    assert "projection" in data["error"]


@pytest.mark.parametrize("variant", ["sh", "ps", "py"])
def test_read_during_projection_save_fails_then_recovers(tmp_path, monkeypatch, variant):
    if variant == "ps" and not shutil.which("pwsh"):
        pytest.skip("PowerShell not installed")
    from specify_cli.extensions import HookExecutor
    from specify_cli.integrations import _file_changes

    executor = HookExecutor(tmp_path)
    executor.save_project_config({"hooks": {"before_plan": [
        {"extension": "old", "command": "speckit.old.run"},
    ]}})
    writing = threading.Event()
    resume = threading.Event()
    failures = []
    original_write = _file_changes.write_bytes

    def paused_write(path, content):
        if path.name == "before_plan.json":
            writing.set()
            if not resume.wait(10):
                raise TimeoutError("Writer was not released")
        return original_write(path, content)

    monkeypatch.setattr(_file_changes, "write_bytes", paused_write)

    def save():
        try:
            executor.save_project_config({"hooks": {"before_plan": [
                {"extension": "new", "command": "speckit.new.run"},
            ]}})
        except (OSError, ValueError, RuntimeError) as exc:
            failures.append(exc)

    writer = threading.Thread(target=save)
    writer.start()
    try:
        assert writing.wait(10)
        code, data = run_hook(tmp_path, variant=variant)
        assert code == 1
        assert data["hooks"] == []
        assert "projection" in data["error"]
    finally:
        resume.set()
        writer.join(10)
    assert not writer.is_alive() and not failures
    code, data = run_hook(tmp_path, variant=variant)
    assert code == 0
    assert data["hooks"][0]["extension"] == "new"


def test_python_reader_rejects_save_after_reading_old_projection(tmp_path, monkeypatch):
    from scripts.python import pre_hooks
    from specify_cli.extensions import HookExecutor

    executor = HookExecutor(tmp_path)
    executor.save_project_config({"hooks": {"before_plan": [
        {"extension": "old", "command": "speckit.old.run"},
    ]}})
    original_read = Path.read_bytes
    replaced = False

    def read_and_replace(path):
        nonlocal replaced
        payload = original_read(path)
        if path.name == "before_plan.json" and not replaced:
            replaced = True
            executor.save_project_config({"hooks": {"before_plan": [
                {"extension": "new", "command": "speckit.new.run"},
            ]}})
        return payload

    monkeypatch.setattr(Path, "read_bytes", read_and_replace)
    with pytest.raises(ValueError, match="changed during resolution"):
        pre_hooks.resolve("before_plan", tmp_path)
    assert replaced


def test_concurrent_projection_saves_publish_matching_configuration(tmp_path, monkeypatch):
    from specify_cli.extensions import HookExecutor
    from specify_cli.integrations import _file_changes
    from specify_cli import shared_infra

    first_writing = threading.Event()
    resume_first = threading.Event()
    second_attempted = threading.Event()
    second_done = threading.Event()
    failures = []
    original_write = _file_changes.write_bytes
    original_lock = shared_infra._exclusive_project_lock

    def paused_write(path, content):
        if path.name == "before_plan.json" and threading.current_thread().name == "first":
            first_writing.set()
            if not resume_first.wait(10):
                raise TimeoutError("First writer was not released")
        return original_write(path, content)

    @contextmanager
    def observed_lock(*args, **kwargs):
        if threading.current_thread().name == "second":
            second_attempted.set()
        with original_lock(*args, **kwargs):
            yield

    monkeypatch.setattr(_file_changes, "write_bytes", paused_write)
    monkeypatch.setattr(shared_infra, "_exclusive_project_lock", observed_lock)

    def save(name):
        try:
            HookExecutor(tmp_path).save_project_config({"hooks": {"before_plan": [
                {"extension": name, "command": f"speckit.{name}.run"},
            ]}})
        except Exception as exc:
            failures.append(exc)
        finally:
            if name == "second":
                second_done.set()

    first = threading.Thread(target=save, args=("first",), name="first")
    second = threading.Thread(target=save, args=("second",), name="second")
    first.start()
    try:
        assert first_writing.wait(10)
        second.start()
        assert second_attempted.wait(10)
        assert not second_done.wait(0.2)
    finally:
        resume_first.set()
        first.join(10)
        if second.ident is not None:
            second.join(10)
    assert not first.is_alive() and not second.is_alive()
    assert not failures
    assert HookExecutor(tmp_path).get_project_config()["hooks"]["before_plan"][0]["extension"] == "second"
    assert run_hook(tmp_path)[1]["hooks"][0]["extension"] == "second"


def test_no_yaml_dependency_needed_for_absent_config(tmp_path):
    result = subprocess.run(
        [sys.executable, "-I", "-S", str(PYTHON / "pre_hooks.py"), "plan"],
        cwd=tmp_path, capture_output=True, text=True,
    )
    assert result.returncode == 0
    assert json.loads(result.stdout)["hooks"] == []


@pytest.mark.parametrize("priority", [float("inf"), float("-inf"), float("nan")])
def test_nonfinite_priority_does_not_crash(tmp_path, priority):
    write_config(tmp_path, yaml.safe_dump({"hooks": {"before_plan": [
        {"extension": "git", "command": "speckit.git.commit", "priority": priority}
    ]}}))
    code, data = run_hook(tmp_path)
    assert code == 0
    assert data["hooks"][0]["priority"] == 10


@pytest.mark.parametrize("variant", ["sh", "ps", "py"])
def test_initialized_project_installs_runnable_dispatchers(tmp_path, variant, monkeypatch):
    from typer.testing import CliRunner
    from specify_cli import app

    project = tmp_path / "project"
    project.mkdir()
    monkeypatch.chdir(project)
    result = CliRunner().invoke(app, [
        "init", "--here", "--integration", "copilot",
        "--integration-options", "--commands", "--script", variant,
    ], catch_exceptions=False)
    assert result.exit_code == 0, result.output
    if variant != "py":
        assert not (project / ".specify/scripts/python/pre_hooks.py").exists()
        assert not (project / ".specify/scripts/python/post_hooks.py").exists()
    write_config(project, "hooks:\n  before_plan:\n    - extension: git\n      command: speckit.git.commit\n")
    script_type = variant
    if variant == "ps" and not shutil.which("pwsh"):
        pytest.skip("PowerShell not installed")
    scripts = {
        "sh": [str(project / ".specify/scripts/bash/pre-hooks.sh")],
        "ps": ["pwsh", "-NoProfile", "-File", str(project / ".specify/scripts/powershell/pre-hooks.ps1")],
        "py": [sys.executable, str(project / ".specify/scripts/python/pre_hooks.py")],
    }
    if variant == "sh":
        scripts["sh"] = bash_script(project / ".specify/scripts/bash/pre-hooks.sh")
    env = os.environ.copy()
    env["SPECKIT_PYTHON_EXECUTABLE"] = sys.executable
    run = subprocess.run(scripts[script_type] + ["plan"], cwd=project, env=env, capture_output=True, text=True)
    assert run.returncode == 0, run.stderr
    assert json.loads(run.stdout)["hooks"][0]["command"] == "speckit.git.commit"


@pytest.mark.parametrize("variant", ["sh", "ps"])
@pytest.mark.parametrize("phase", ["pre", "post"])
def test_shell_variants_match_python(tmp_path, variant, phase):
    if variant == "ps" and not shutil.which("pwsh"):
        pytest.skip("PowerShell not installed")
    write_config(tmp_path, f"hooks:\n  {'before' if phase == 'pre' else 'after'}_plan:\n    - extension: git\n      command: speckit.git.commit\n")
    assert run_hook(tmp_path, phase, variant=variant) == run_hook(tmp_path, phase)


@pytest.mark.parametrize("variant", ["sh", "ps", "py"])
@pytest.mark.parametrize("phase", ["pre", "post"])
def test_canonical_cli_output_has_identical_order_and_metadata(tmp_path, variant, phase):
    if variant == "ps" and not shutil.which("pwsh"):
        pytest.skip("PowerShell not installed")
    from specify_cli.extensions import HookExecutor

    event = f"{'before' if phase == 'pre' else 'after'}_plan"
    HookExecutor(tmp_path).save_project_config({
        "installed": ["git", "agent-context"],
        "settings": {"auto_execute_hooks": True},
        "hooks": {
            "before_tasks": [{"extension": "elsewhere", "command": "speckit.elsewhere.run"}],
            event: [
                {"extension": "late", "command": "speckit.late.run", "priority": 20,
                 "prompt": "Don\'t commit: yet?", "description": 'Quote "tab\t' + "x" * 85},
                {"extension": "first", "command": "speckit.first.run", "priority": 5,
                 "optional": False, "condition": None},
                {"extension": "second", "command": "speckit.second.run", "priority": 5},
                {"extension": "disabled", "command": "speckit.disabled.run", "enabled": False},
                {"extension": "condition", "command": "speckit.condition.run",
                 "condition": "env.CI is set"},
            ],
        },
    })
    code, data = run_hook(tmp_path, phase, variant=variant)
    assert code == 0
    assert data == run_hook(tmp_path, phase)[1]
    assert [item["extension"] for item in data["hooks"]] == ["first", "second", "late"]
    assert data["hooks"][-1]["prompt"] == "Don't commit: yet?"
    assert data["hooks"][-1]["description"] == 'Quote "tab\t' + "x" * 85


@pytest.mark.parametrize("variant", ["sh", "ps", "py"])
def test_canonical_cli_writer_keeps_multiline_prompt_on_one_yaml_line(tmp_path, variant):
    if variant == "ps" and not shutil.which("pwsh"):
        pytest.skip("PowerShell not installed")
    from specify_cli.extensions import HookExecutor

    HookExecutor(tmp_path).save_project_config({"hooks": {"before_plan": [
        {"extension": "git", "command": "speckit.git.commit", "prompt": "first\nsecond"}
    ]}})
    config = (tmp_path / ".specify/extensions.yml").read_text(encoding="utf-8")
    assert 'prompt: "first\\nsecond"' in config
    code, data = run_hook(tmp_path, variant=variant)
    assert code == 0
    assert data["hooks"][0]["prompt"] == "first\nsecond"


@pytest.mark.parametrize("variant", ["sh", "ps", "py"])
@pytest.mark.parametrize("phase", ["pre", "post"])
def test_canonical_backslash_escape_matches_python(tmp_path, variant, phase):
    if variant == "ps" and not shutil.which("pwsh"):
        pytest.skip("PowerShell not installed")
    from specify_cli.extensions import HookExecutor

    event = f"{'before' if phase == 'pre' else 'after'}_plan"
    prompt = "Path C:\\workspace\nkeep \\ literal"
    HookExecutor(tmp_path).save_project_config({
        "hooks": {event: [
            {"extension": "git", "command": "speckit.git.commit", "prompt": prompt}
        ]}
    })
    code, data = run_hook(tmp_path, phase, variant=variant)
    assert code == 0
    assert data == run_hook(tmp_path, phase)[1]
    assert data["hooks"][0]["prompt"] == prompt


@pytest.mark.parametrize("variant", ["sh", "ps", "py"])
def test_legacy_yaml_escaped_slash_matches_python(tmp_path, variant):
    if variant == "ps" and not shutil.which("pwsh"):
        pytest.skip("PowerShell not installed")
    write_config(tmp_path, (
        'hooks:\n  before_plan:\n'
        '    - extension: git\n      command: speckit.git.commit\n'
        '      prompt: "a\\/b"\n'
    ))
    code, data = run_hook(tmp_path, variant=variant)
    assert code == 0
    assert data == run_hook(tmp_path)[1]
    assert data["hooks"][0]["prompt"] == "a/b"


@pytest.mark.parametrize("variant", ["sh", "ps", "py"])
@pytest.mark.parametrize("phase", ["pre", "post"])
@pytest.mark.parametrize("field,value", [
    ("extension", "false"), ("command", "123"), ("extension", "yes"),
    ("command", "0x10"), ("extension", "null"), ("command", "1.2"),
    ("extension", "2026-10-08"), ("command", ".nan"),
])
def test_native_identifiers_reject_implicitly_typed_yaml(tmp_path, variant, phase, field, value):
    if variant == "ps" and not shutil.which("pwsh"):
        pytest.skip("PowerShell not installed")
    event = f"{'before' if phase == 'pre' else 'after'}_plan"
    write_config(
        tmp_path,
        f"hooks:\n  {event}:\n    - extension: git\n"
        f"      command: speckit.git.commit\n      {field}: {value}\n",
    )
    code, data = run_hook(tmp_path, phase, variant=variant)
    assert code == 1
    assert "needs extension and command" in data["error"]
    assert data["hooks"] == []


@pytest.mark.parametrize("variant", ["sh", "ps", "py"])
@pytest.mark.parametrize("phase", ["pre", "post"])
def test_quoted_numeric_identifier_remains_string(tmp_path, variant, phase):
    if variant == "ps" and not shutil.which("pwsh"):
        pytest.skip("PowerShell not installed")
    event = f"{'before' if phase == 'pre' else 'after'}_plan"
    write_config(tmp_path, f"hooks:\n  {event}:\n    - extension: '123'\n      command: 'false'\n")
    code, data = run_hook(tmp_path, phase, variant=variant)
    assert code == 0
    assert data == run_hook(tmp_path, phase)[1]


@pytest.mark.parametrize("phase", ["pre", "post"])
def test_system_bash_resolves_unquoted_identifiers(tmp_path, phase):
    if os.name == "nt":
        pytest.skip("system /bin/bash is only available on POSIX")
    event = f"{'before' if phase == 'pre' else 'after'}_plan"
    write_config(tmp_path, f"hooks:\n  {event}:\n    - extension: git\n      command: speckit.git.commit\n")
    result = subprocess.run(
        ["/bin/bash", str(ROOT / "scripts/bash" / f"{phase}-hooks.sh"), "plan"],
        cwd=tmp_path, capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["hooks"][0]["command"] == "speckit.git.commit"


@pytest.mark.parametrize("variant", ["sh", "ps", "py"])
@pytest.mark.parametrize("phase", ["pre", "post"])
@pytest.mark.parametrize("value", ["false", "true", "0"])
def test_non_string_condition_fails_consistently(tmp_path, variant, phase, value):
    if variant == "ps" and not shutil.which("pwsh"):
        pytest.skip("PowerShell not installed")
    event = f"{'before' if phase == 'pre' else 'after'}_plan"
    write_config(tmp_path, f"hooks:\n  {event}:\n    - extension: git\n"
                           f"      command: speckit.git.commit\n      condition: {value}\n")
    code, data = run_hook(tmp_path, phase, variant=variant)
    assert code == 1
    assert "condition must be a string or null" in data["error"]
    assert data["hooks"] == []


@pytest.mark.parametrize("variant", ["sh", "ps", "py"])
def test_quoted_condition_remains_a_string(tmp_path, variant):
    if variant == "ps" and not shutil.which("pwsh"):
        pytest.skip("PowerShell not installed")
    write_config(tmp_path, "hooks:\n  before_plan:\n    - extension: git\n"
                           "      command: speckit.git.commit\n      condition: 'false'\n")
    code, data = run_hook(tmp_path, variant=variant)
    assert code == 0
    assert data["hooks"] == []


@pytest.mark.parametrize("variant", ["sh", "ps", "py"])
@pytest.mark.parametrize("value", ["null", "Null", "NULL", "~"])
def test_null_condition_allows_hook(tmp_path, variant, value):
    if variant == "ps" and not shutil.which("pwsh"):
        pytest.skip("PowerShell not installed")
    write_config(tmp_path, "hooks:\n  before_plan:\n    - extension: git\n"
                           f"      command: speckit.git.commit\n      condition: {value}\n")
    code, data = run_hook(tmp_path, variant=variant)
    assert code == 0
    assert data == run_hook(tmp_path)[1]
    assert len(data["hooks"]) == 1


@pytest.mark.parametrize("variant", ["sh", "ps", "py"])
def test_mixed_case_null_condition_remains_a_string(tmp_path, variant):
    if variant == "ps" and not shutil.which("pwsh"):
        pytest.skip("PowerShell not installed")
    write_config(tmp_path, "hooks:\n  before_plan:\n    - extension: git\n"
                           "      command: speckit.git.commit\n      condition: nUll\n")
    code, data = run_hook(tmp_path, variant=variant)
    assert code == 0
    assert data == run_hook(tmp_path)[1]
    assert data["hooks"] == []


@pytest.mark.parametrize("variant", ["sh", "ps"])
@pytest.mark.parametrize("phase", ["pre", "post"])
def test_native_resolvers_do_not_invoke_python(tmp_path, variant, phase):
    if variant == "ps" and not shutil.which("pwsh"):
        pytest.skip("PowerShell not installed")
    stub_dir = tmp_path / "stub-bin"
    stub_dir.mkdir()
    marker = tmp_path / "python-was-called"
    for name in ("python", "python3", "py"):
        stub = stub_dir / name
        stub.write_text(f'#!/bin/sh\nprintf called >> "{marker}"\nexit 97\n', encoding="utf-8")
        stub.chmod(0o755)
    write_config(tmp_path, f"hooks:\n  {'before' if phase == 'pre' else 'after'}_plan:\n  - extension: git\n    command: speckit.git.commit\n")
    code, data = run_hook(tmp_path, phase, variant=variant, extra_env={
        "PATH": f"{stub_dir}{os.pathsep}{os.environ['PATH']}",
        "SPECKIT_PYTHON_EXECUTABLE": "python3",
    })
    assert code == 0
    assert data["hooks"][0]["command"] == "speckit.git.commit"
    assert not marker.exists()


@pytest.mark.parametrize("variant", ["sh", "ps"])
@pytest.mark.parametrize("phase", ["pre", "post"])
@pytest.mark.parametrize("text", [
    "hooks:\n  before_plan: [wrong]\n",
    "hooks:\n  before_plan:\n  - extension: git\n    command: speckit.git.commit\n    prompt: |\n      multiline\n",
    "hooks:\n  before_plan:\n  - extension: git\n    command: speckit.git.commit\n    optional: 'false'\n",
    "hooks: [\n",
    "installed: [\nhooks: {}\n",
    "settings:\n  auto_execute_hooks: [\nhooks: {}\n",
    "installed:\n- 'unfinished\nhooks: {}\n",
    "hooks: {}\nhooks: {}\n",
    "hooks:\n  before_plan: []\n  before_plan: []\n",
    "settings:\n  auto_execute_hooks: true\n  bad indentation: nope\nhooks: {}\n",
])
def test_native_parsers_reject_unsupported_or_invalid_yaml(tmp_path, variant, phase, text):
    if variant == "ps" and not shutil.which("pwsh"):
        pytest.skip("PowerShell not installed")
    if phase == "post":
        text = text.replace("before_plan", "after_plan")
    write_config(tmp_path, text)
    code, data = run_hook(tmp_path, phase=phase, variant=variant)
    assert code == 1
    assert data["hooks"] == []
    assert data["error"]


@pytest.mark.parametrize("variant", ["sh", "ps", "py"])
@pytest.mark.parametrize("phase", ["pre", "post"])
@pytest.mark.parametrize("field", [
    "extension: 'unterminated", "extension: ''", 'command: ""',
    "optional: 'false'", "condition: false",
])
def test_non_target_event_fields_are_validated(tmp_path, variant, phase, field):
    if variant == "ps" and not shutil.which("pwsh"):
        pytest.skip("PowerShell not installed")
    event = f"{'before' if phase == 'pre' else 'after'}_tasks"
    write_config(tmp_path, f"hooks:\n  {event}:\n    - extension: git\n"
                           f"      command: speckit.git.commit\n      {field}\n")
    code, data = run_hook(tmp_path, phase, variant=variant)
    assert code == 1
    assert data["hooks"] == []
    assert data["error"]


@pytest.mark.parametrize("variant", ["sh", "ps"])
def test_native_invalid_event_is_valid_json(tmp_path, variant):
    if variant == "ps" and not shutil.which("pwsh"):
        pytest.skip("PowerShell not installed")
    code, data = run_hook(tmp_path, variant=variant, name='bad"name')
    assert code == 1
    assert "Invalid hook event" in data["error"]


@pytest.mark.parametrize("variant", ["sh", "ps", "py"])
@pytest.mark.parametrize("priority,expected", [
    ("5", 5), (False, 10), (0, 10), ("invalid", 10), (2.8, 2),
])
def test_priority_normalization_matches_across_runtimes(tmp_path, variant, priority, expected):
    if variant == "ps" and not shutil.which("pwsh"):
        pytest.skip("PowerShell not installed")
    write_config(tmp_path, yaml.safe_dump({"hooks": {"before_plan": [
        {"extension": "git", "command": "speckit.git.commit", "priority": priority}
    ]}}))
    code, data = run_hook(tmp_path, variant=variant)
    assert code == 0
    assert data["hooks"][0]["priority"] == expected


@pytest.mark.parametrize("variant", ["sh", "ps", "py"])
@pytest.mark.parametrize("priority,expected", [
    (2147483647, 2147483647),
    (2147483648, 10),
    (2147483647.9, 2147483647),
    (10**16, 10),
    ("00000000000000000005", 5),
    ("2.8", 10),
])
def test_priority_range_and_coercion_parity(tmp_path, variant, priority, expected):
    if variant == "ps" and not shutil.which("pwsh"):
        pytest.skip("PowerShell not installed")
    write_config(tmp_path, yaml.safe_dump({"hooks": {"before_plan": [
        {"extension": "high", "command": "speckit.high.run", "priority": priority},
        {"extension": "default", "command": "speckit.default.run"},
    ]}}, sort_keys=False))
    code, data = run_hook(tmp_path, variant=variant)
    assert code == 0
    assert data == run_hook(tmp_path)[1]
    assert [hook["extension"] for hook in data["hooks"]] == (
        ["default", "high"] if expected > 10 else ["high", "default"]
    )
    assert next(hook for hook in data["hooks"] if hook["extension"] == "high")["priority"] == expected


@pytest.mark.parametrize("variant", ["sh", "ps", "py"])
@pytest.mark.parametrize("raw,expected", [
    ("2_0", 20), ("0x14", 20), ("2.0e+1", 20),
    ("2.", 2), ("2.e+1", 20), ("+2.", 2),
    ("0b10100", 20), ("024", 20), ("1:02", 62),
    ("+0x14", 20), ("+024", 20), ("1:2", 62),
    ("+1:2", 62), ("01:02", 10), ("0:2", 10),
    ("0X14", 10), ("0B10100", 10),
    ("'0x14'", 10), ("'2_0'", 20),
    ("2.0e+99", 10), ("0xGG", 10),
])
def test_yaml_numeric_priority_parity(tmp_path, variant, raw, expected):
    if variant == "ps" and not shutil.which("pwsh"):
        pytest.skip("PowerShell not installed")
    write_config(tmp_path, (
        "hooks:\n  before_plan:\n"
        "    - extension: high\n      command: speckit.high.run\n"
        f"      priority: {raw}\n"
        "    - extension: default\n      command: speckit.default.run\n"
    ))
    code, data = run_hook(tmp_path, variant=variant)
    assert code == 0
    assert data == run_hook(tmp_path)[1]
    assert next(hook for hook in data["hooks"] if hook["extension"] == "high")["priority"] == expected


@pytest.mark.parametrize("variant", ["sh", "ps", "py"])
@pytest.mark.parametrize("value", [
    "\a", "\v", "\x01", "\x1b", "\x85", "\xa0", "\u2028", "\u2029",
    "\ufeff", "😀", "😀\nmore",
])
def test_canonical_writer_control_escape_parity(tmp_path, variant, value):
    if variant == "ps" and not shutil.which("pwsh"):
        pytest.skip("PowerShell not installed")
    from specify_cli.extensions import HookExecutor

    HookExecutor(tmp_path).save_project_config({"hooks": {"before_plan": [
        {"extension": "git", "command": "speckit.git.commit", "prompt": f"before{value}after"},
    ]}})
    code, data = run_hook(tmp_path, variant=variant)
    assert code == 0
    assert data == run_hook(tmp_path)[1]
    assert data["hooks"][0]["prompt"] == f"before{value}after"


@pytest.mark.parametrize("variant", ["sh", "ps", "py"])
def test_nul_in_existing_hook_configuration_is_rejected(tmp_path, variant):
    if variant == "ps" and not shutil.which("pwsh"):
        pytest.skip("PowerShell not installed")
    write_config(tmp_path, (
        'hooks:\n  before_plan:\n'
        '    - extension: git\n      command: speckit.git.commit\n'
        '      prompt: "before\\0after"\n'
    ))
    code, data = run_hook(tmp_path, variant=variant)
    assert code == 1
    assert data["hooks"] == []
    assert "NUL" in data["error"] or "Unsupported YAML escape" in data["error"]


def test_canonical_writer_rejects_nul_without_touching_config(tmp_path):
    from specify_cli.extensions import HookExecutor

    executor = HookExecutor(tmp_path)
    config = write_config(tmp_path, "hooks: {}\n")
    with pytest.raises(ValueError, match="NUL"):
        executor.save_project_config({"hooks": {"before_plan": [
            {"extension": "git", "command": "speckit.git.commit", "prompt": "before\0after"}
        ]}})
    assert config.read_text(encoding="utf-8") == "hooks: {}\n"


@pytest.mark.parametrize("variant", ["sh", "ps", "py"])
@pytest.mark.parametrize("value", [
    "JSvjEuqRsqs$tn]X", "N1Y'dombB*Afj9e;SO}^0^S'", "prefix{suffix",
])
def test_canonical_writer_quotes_native_reserved_scalar_chars(tmp_path, variant, value):
    if variant == "ps" and not shutil.which("pwsh"):
        pytest.skip("PowerShell not installed")
    from specify_cli.extensions import HookExecutor

    HookExecutor(tmp_path).save_project_config({"hooks": {"before_plan": [
        {"extension": "git", "command": "speckit.git.commit", "prompt": value},
    ]}})
    code, data = run_hook(tmp_path, variant=variant)
    assert code == 0
    assert data == run_hook(tmp_path)[1]
    assert data["hooks"][0]["prompt"] == value
