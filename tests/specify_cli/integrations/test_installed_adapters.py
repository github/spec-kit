"""Public-path regressions for neutral, catalog-installed adapter packages."""

from __future__ import annotations

import hashlib
import io
import json
import marshal
import os
import shutil
import stat
import struct
import subprocess
import sys
import tarfile
import threading
import zipfile
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml
from typer.testing import CliRunner

from specify_cli import AGENT_CONFIG, app
from specify_cli.agents import CommandRegistrar
from specify_cli.integrations import (
    INTEGRATION_REGISTRY,
    IntegrationDescriptor,
    IntegrationDescriptorError,
)
from specify_cli.integrations.installer import (
    IntegrationInstallError,
    load_installed_integrations,
    read_records,
    unload_installed_integrations,
)

KEY = "sample-agent"
runner = CliRunner()


def descriptor(version="1.0.0", key=KEY):
    return {
        "schema_version": "1.0",
        "integration": {
            "id": key, "name": "Sample Agent", "version": version,
            "description": "A neutral test adapter",
        },
        "requires": {"speckit_version": ">=0.6.0"},
    }


def implementation(key=KEY, *, flavor="skills", body="", folder=".sample-agent"):
    base = "SkillsIntegration" if flavor == "skills" else "MarkdownIntegration"
    subdir = "skills" if flavor == "skills" else "commands"
    extension = "/SKILL.md" if flavor == "skills" else ".md"
    return f'''from specify_cli.integrations.base import {base}

class SampleIntegration({base}):
    key = {key!r}
    config = {{
        "name": "Sample Agent", "folder": {folder!r},
        "commands_subdir": {subdir!r},
        "install_url": "https://example.com/sample-agent",
        "requires_cli": False,
    }}
    registrar_config = {{
        "dir": "{folder}/{subdir}", "format": "markdown",
        "args": "$ARGUMENTS", "extension": {extension!r},
    }}
    multi_install_safe = True
{body}
'''


@pytest.fixture(autouse=True)
def isolated_registry(monkeypatch, tmp_path):
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("USERPROFILE", str(home))
    monkeypatch.delenv("SPECIFY_INIT_DIR", raising=False)
    monkeypatch.delenv("SPECKIT_INTEGRATION_CATALOG_URL", raising=False)
    unload_installed_integrations()
    yield
    unload_installed_integrations()


@pytest.fixture
def server(tmp_path):
    downloads = tmp_path / "downloads"
    downloads.mkdir()
    requests = []

    class Handler(SimpleHTTPRequestHandler):
        def do_GET(self):
            requests.append(self.path)
            super().do_GET()

        def log_message(self, *args):
            pass

    http = ThreadingHTTPServer(("127.0.0.1", 0), partial(Handler, directory=str(downloads)))
    thread = threading.Thread(target=http.serve_forever, daemon=True)
    thread.start()
    result = SimpleNamespace(
        root=downloads, url=f"http://127.0.0.1:{http.server_port}", requests=requests,
    )
    try:
        yield result
    finally:
        http.shutdown()
        http.server_close()
        thread.join()


def publish(server, *, metadata=None, code=None, version="1.0.0", members=None, archive="zip"):
    data = descriptor(version) if metadata is None else metadata
    source = implementation() if code is None else code
    content = {
        "integration.yml": yaml.safe_dump(data).encode(),
        "__init__.py": source.encode(),
        **(members or {}),
    }
    path = server.root / f"sample-agent-{version}.{archive}"
    if archive == "zip":
        with zipfile.ZipFile(path, "w") as package:
            for name, value in content.items():
                package.writestr(name, value)
    else:
        with tarfile.open(path, "w:gz") as package:
            for name, value in content.items():
                entry = tarfile.TarInfo(name)
                entry.size = len(value)
                package.addfile(entry, io.BytesIO(value))
    info = {
        **data["integration"],
        "download_url": f"{server.url}/{path.name}",
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    }
    write_catalog(server, info)
    return info, path


def write_catalog(server, info):
    (server.root / "catalog.json").write_text(
        json.dumps({"schema_version": "1.0", "integrations": {KEY: info}})
    )


def run(project, arguments, *, input=None):
    previous = Path.cwd()
    os.chdir(project)
    try:
        return runner.invoke(app, arguments, input=input, catch_exceptions=False)
    finally:
        os.chdir(previous)


def catalog_project(tmp_path, server, *, install_allowed=True):
    project = tmp_path / "project"
    (project / ".specify").mkdir(parents=True)
    result = run(project, ["integration", "catalog", "add", f"{server.url}/catalog.json", "--name", "samples"])
    assert result.exit_code == 0, result.output
    if not install_allowed:
        path = project / ".specify" / "integration-catalogs.yml"
        data = yaml.safe_load(path.read_text())
        data["catalogs"][0]["install_allowed"] = False
        path.write_text(yaml.safe_dump(data))
    return project


def install(project):
    result = run(project, ["integration", "install", KEY, "--trust-integration", "--script", "py"])
    assert result.exit_code == 0, result.output
    return result


def snapshot(project):
    return {
        path.relative_to(project).as_posix(): path.read_bytes()
        for path in project.rglob("*")
        if path.is_file() and "__pycache__" not in path.parts
        and path.name != ".integration-install.lock"
    }


@pytest.mark.parametrize("existing", [False, True])
@pytest.mark.parametrize("change", ["unchanged", "partial", "concurrent", "deleted"])
def test_round9_pending_write_preserves_unattributed_changes(tmp_path, server, monkeypatch, existing, change):
    from specify_cli.integrations import _lifecycle

    body = f'''    def setup(self, project_root, manifest, **kwargs):
        from threading import Thread
        from specify_cli.integrations._file_changes import before_file_change
        target = project_root / ".sample-agent/skills/sample-pending.md"
        before_file_change(target)
        if {change!r} in ("partial", "concurrent"):
            target.write_text("partial write")
        if {change!r} == "concurrent":
            writer = Thread(target=lambda: target.write_text("concurrent edit"))
            writer.start()
            writer.join()
        if {change!r} == "deleted":
            target.unlink(missing_ok=True)
        raise OSError("sample write interrupted before completion")
'''
    publish(server, code=implementation(body=body))
    project = catalog_project(tmp_path, server)
    target = project / ".sample-agent/skills/sample-pending.md"
    target.parent.mkdir(parents=True)
    if existing:
        target.write_text("original bytes")
    before = snapshot(project)
    backups = []
    original_mkdtemp = _lifecycle.tempfile.mkdtemp

    def record_backup(*args, **kwargs):
        directory = original_mkdtemp(*args, **kwargs)
        if kwargs.get("prefix") == "speckit-integration-rollback-":
            backups.append(Path(directory))
        return directory

    monkeypatch.setattr(_lifecycle.tempfile, "mkdtemp", record_backup)
    conflict = change in {"partial", "concurrent"} or (change == "deleted" and existing)
    try:
        result = run(project, ["integration", "install", KEY, "--trust-integration", "--script", "py"])
        assert result.exit_code == 1, result.output
        assert "sample write interrupted" in " ".join(result.output.split())
        assert ("Preserved concurrent edits" in result.output) == conflict
        if change in {"partial", "concurrent"}:
            assert target.read_text() == ("partial write" if change == "partial" else "concurrent edit")
        elif change == "deleted":
            assert not target.exists()
        else:
            assert snapshot(project) == before
        assert len(backups) == 1
        assert backups[0].exists() == conflict
        if conflict and existing:
            assert any(path.read_bytes() == b"original bytes" for path in backups[0].rglob("*") if path.is_file())
        assert KEY not in read_records(project)
        assert KEY not in INTEGRATION_REGISTRY
    finally:
        for backup in backups:
            if backup.exists():
                shutil.rmtree(backup)


@pytest.mark.parametrize("field", ["author", "repository", "license"])
@pytest.mark.parametrize("value", [None, "", " \t", [], {"value": "sample"}, True, 12])
@pytest.mark.parametrize("source", ["descriptor", "catalog", "both"])
def test_round9_optional_metadata_rejects_invalid_values_before_import(tmp_path, server, field, value, source):
    marker = tmp_path / "unexpected-import"
    metadata = descriptor()
    if source in {"descriptor", "both"}:
        metadata["integration"][field] = value
    code = f"from pathlib import Path\nPath({str(marker)!r}).write_text('unexpected import')\n" + implementation()
    info, _ = publish(server, metadata=metadata, code=code)
    if source == "descriptor":
        info.pop(field)
    else:
        info[field] = value
    write_catalog(server, info)
    project = catalog_project(tmp_path, server)
    before = snapshot(project)
    result = run(project, ["integration", "install", KEY, "--trust-integration", "--script", "py"])
    assert result.exit_code == 1, result.output
    assert field in result.output
    assert "non-empty string" in " ".join(result.output.split())
    assert not marker.exists()
    assert snapshot(project) == before
    assert KEY not in INTEGRATION_REGISTRY


@pytest.mark.parametrize("optional", [False, True])
def test_round9_optional_metadata_preserves_valid_install_and_reload(tmp_path, server, optional):
    metadata = descriptor()
    fields = {"author": "Sample Publisher", "repository": "https://example.com/sample-agent", "license": "MIT"}
    if optional:
        metadata["integration"].update(fields)
    publish(server, metadata=metadata)
    project = catalog_project(tmp_path, server)
    install(project)
    unload_installed_integrations()
    load_installed_integrations(project)
    record = read_records(project)[KEY]
    for field, value in fields.items():
        assert (record[field] == value) if optional else field not in record
    assert INTEGRATION_REGISTRY[KEY].config["name"] == "Sample Agent"


@pytest.mark.parametrize("operation", ["run", "resume"])
@pytest.mark.parametrize("json_output", [False, True])
@pytest.mark.parametrize("failure", ["step", "save"])
@pytest.mark.parametrize("error_type", [OSError, FileNotFoundError])
def test_round9_workflow_runtime_io_keeps_run_context(
    tmp_path, monkeypatch, operation, json_output, failure, error_type,
):
    from specify_cli.workflows.base import RunStatus
    from specify_cli.workflows.engine import RunState, WorkflowEngine

    project = tmp_path / "project"
    (project / ".specify").mkdir(parents=True)
    source = project / "sample-workflow.yml"
    source.write_text(yaml.safe_dump({
        "schema_version": "1.0",
        "workflow": {"id": "sample-workflow", "name": "Sample Workflow", "version": "1.0.0"},
        "steps": [{"id": "sample-gate", "type": "gate", "message": "Sample review", "options": ["approve", "reject"]}],
    }))
    if operation == "resume":
        started = run(project, ["workflow", "run", str(source), "--json"])
        assert started.exit_code == 0, started.output
        run_id = json.loads(started.stdout)["run_id"]
    observed = []
    original_save = RunState.save

    def save_with_runtime_failure(state):
        observed.append(state.run_id)
        if failure == "save" and state.status == RunStatus.RUNNING and state.current_step_id:
            raise error_type("sample state save failed")
        return original_save(state)

    def failing_steps(engine, steps, context, state, registry, **kwargs):
        state.current_step_id = steps[0]["id"]
        state.save()
        raise error_type("sample step I/O failed")

    monkeypatch.setattr(RunState, "save", save_with_runtime_failure)
    if failure == "step":
        monkeypatch.setattr(WorkflowEngine, "_execute_steps", failing_steps)
    arguments = ["workflow", operation, str(source) if operation == "run" else run_id]
    if json_output:
        arguments.append("--json")
    result = run(project, arguments)
    assert result.exit_code == 1, result.output
    assert observed, result.output
    actual_run_id = observed[0]
    error = "sample state save failed" if failure == "save" else "sample step I/O failed"
    if json_output:
        payload = json.loads(result.stdout)
        assert payload["run_id"] == actual_run_id
        assert payload["workflow_id"] == "sample-workflow"
        assert payload["status"] == "failed"
        assert payload["error"] == error
        assert result.stderr == ""
    else:
        assert ("Workflow failed" if operation == "run" else "Resume failed") in result.output
        assert error in result.output
    persisted = RunState.load(actual_run_id, project)
    assert persisted.workflow_id == "sample-workflow"
    if failure == "step" or operation == "run":
        assert persisted.status == RunStatus.FAILED
        assert persisted.error == error
    else:
        assert persisted.status == RunStatus.PAUSED


def test_round9_execution_state_is_context_local_and_cleared_before_loading(tmp_path, monkeypatch):
    from concurrent.futures import ThreadPoolExecutor
    from specify_cli.workflows.engine import WorkflowDefinition, WorkflowEngine

    project = tmp_path / "project"
    (project / ".specify").mkdir(parents=True)
    engine = WorkflowEngine(project)
    definition = WorkflowDefinition.from_string(yaml.safe_dump({
        "schema_version": "1.0",
        "workflow": {"id": "sample-workflow", "name": "Sample Workflow", "version": "1.0.0"},
        "steps": [{"id": "sample-gate", "type": "gate", "message": "Sample review", "options": ["approve", "reject"]}],
    }))
    barrier = threading.Barrier(2)

    def fail_steps(self, steps, context, state, registry, **kwargs):
        barrier.wait(timeout=10)
        raise OSError("sample execution failure")

    def execute(run_id):
        with pytest.raises(OSError, match="sample execution failure"):
            engine.execute(definition, run_id=run_id)
        return engine._execution_state.get().run_id

    with monkeypatch.context() as patches:
        patches.setattr(WorkflowEngine, "_execute_steps", fail_steps)
        with ThreadPoolExecutor(max_workers=2) as pool:
            first = pool.submit(execute, "sample-first")
            second = pool.submit(execute, "sample-second")
            assert first.result(timeout=20) == "sample-first"
            assert second.result(timeout=20) == "sample-second"
    assert engine._execution_state.get() is None
    engine.execute(definition)
    assert engine._execution_state.get() is not None

    def fail_loading():
        raise IntegrationInstallError("sample adapter load failure")

    monkeypatch.setattr(engine, "_load_integrations", fail_loading)
    with pytest.raises(IntegrationInstallError, match="sample adapter load failure"):
        engine.execute(definition)
    assert engine._execution_state.get() is None


@pytest.mark.parametrize("force", [False, True])
@pytest.mark.parametrize("missing_manifest", [False, True])
def test_round8_upgrade_persists_only_after_regenerating_files(tmp_path, server, force, missing_manifest):
    from specify_cli.integrations import installer

    publish(server)
    project = catalog_project(tmp_path, server)
    install(project)
    manifest = project / f".specify/integrations/{KEY}.manifest.json"
    if missing_manifest:
        manifest.unlink()
    before = snapshot(project)
    trust_path = Path.home() / ".specify/integration-trust.json"
    ownership = json.loads(trust_path.read_text())["recovery"]
    publish(server, version="2.0.0", code=implementation(folder=".sample-next"))
    arguments = ["integration", "upgrade", KEY, "--trust-integration"]
    if force:
        arguments.append("--force")
    result = run(project, arguments)
    assert result.exit_code == 0, result.output
    assert installer._pending_root is None
    if missing_manifest:
        assert "Nothing to upgrade" in result.output
        assert snapshot(project) == before
        assert json.loads(trust_path.read_text())["recovery"] == ownership
        assert read_records(project)[KEY]["version"] == "1.0.0"
        assert INTEGRATION_REGISTRY[KEY].config["folder"] == ".sample-agent"
        assert CommandRegistrar(project).AGENT_CONFIGS[KEY]["dir"] == ".sample-agent/skills"
        assert not (project / ".sample-next").exists()
    else:
        assert "Nothing to upgrade" not in result.output
        assert read_records(project)[KEY]["version"] == "2.0.0"
        assert (project / ".sample-next/skills/speckit-plan/SKILL.md").is_file()
        assert not (project / ".sample-agent/skills/speckit-plan/SKILL.md").exists()
        assert INTEGRATION_REGISTRY[KEY].config["folder"] == ".sample-next"
        assert CommandRegistrar(project).AGENT_CONFIGS[KEY]["dir"] == ".sample-next/skills"


@pytest.mark.parametrize("class_separator,registrar_separator", [(".", "_"), ("_", "."), ("-", None)])
@pytest.mark.parametrize("class_no_symlink,registrar_no_symlink", [
    (False, False), (False, True), (True, False), (True, True), (False, None), (True, None),
])
def test_round8_recovery_retains_effective_registrar_settings(
    tmp_path, server, class_separator, registrar_separator, class_no_symlink, registrar_no_symlink,
):
    from specify_cli.integrations.installer import recovery_metadata

    overrides = {}
    if registrar_separator is not None:
        overrides["invoke_separator"] = registrar_separator
    if registrar_no_symlink is not None:
        overrides["dev_no_symlink"] = registrar_no_symlink
    body = (
        f"    invoke_separator = {class_separator!r}\n"
        f"    dev_no_symlink = {class_no_symlink!r}\n"
        f"    registrar_config = {{**registrar_config, **{overrides!r}}}\n"
    )
    publish(server, code=implementation(body=body))
    project = catalog_project(tmp_path, server)
    install(project)
    healthy = CommandRegistrar(project).AGENT_CONFIGS[KEY]
    expected_separator = registrar_separator or class_separator
    expected_no_symlink = class_no_symlink or bool(registrar_no_symlink)
    assert healthy["invoke_separator"] == expected_separator
    assert healthy.get("dev_no_symlink", False) == expected_no_symlink
    record = read_records(project)[KEY]
    expected = {**healthy, "dev_no_symlink": expected_no_symlink}
    assert record["registrar_config"] == expected
    binding = recovery_metadata(project, KEY, record)
    assert binding["registrar_config"] == expected
    (project / f".specify/integrations/packages/{KEY}/__init__.py").unlink()
    unload_installed_integrations()
    assert recovery_metadata(project, KEY, read_records(project)[KEY])["registrar_config"] == expected
    removed = run(project, ["integration", "uninstall", KEY, "--force"])
    assert removed.exit_code == 0, removed.output
    assert not (project / ".sample-agent/skills/speckit-plan/SKILL.md").exists()
    assert KEY not in read_records(project)
    assert KEY not in INTEGRATION_REGISTRY


@pytest.mark.parametrize("command", ["install", "use", "switch"])
def test_round7_noop_lifecycle_does_not_copy_output_roots_or_package_store(tmp_path, server, monkeypatch, command):
    from specify_cli.integrations import _lifecycle

    publish(server)
    project = catalog_project(tmp_path, server)
    install(project)
    unowned = project / ".sample-agent/unowned-data.bin"
    unowned.write_bytes(b"sample user data\n" * 100_000)
    before = snapshot(project)
    original_copytree = _lifecycle.shutil.copytree
    original_journal = _lifecycle._FileJournal

    def journal_without_eager_bytes(*args, **kwargs):
        journal = original_journal(*args, **kwargs)
        assert sum(path.stat().st_size for path in journal.backup.rglob("*") if path.is_file()) == 0
        return journal

    def refuse_eager_snapshot(source, destination, *args, **kwargs):
        assert Path(source) not in {
            project / ".sample-agent", project / ".specify/integrations",
        }, "an untouched output root must not be copied"
        return original_copytree(source, destination, *args, **kwargs)

    monkeypatch.setattr(_lifecycle.shutil, "copytree", refuse_eager_snapshot)
    monkeypatch.setattr(_lifecycle, "_FileJournal", journal_without_eager_bytes)
    result = run(project, ["integration", command, KEY])
    assert result.exit_code == 0, result.output
    assert snapshot(project) == before


@pytest.mark.parametrize("cache", ["agent", "registrar"])
def test_round7_failed_candidate_cache_refresh_cleans_pending_state(tmp_path, server, monkeypatch, cache):
    from specify_cli import _agent_config, agents
    from specify_cli.integrations import installer

    publish(server)
    project = catalog_project(tmp_path, server)
    before = snapshot(project)
    module = _agent_config if cache == "agent" else agents
    name = "_build_agent_config" if cache == "agent" else "_build_agent_configs"
    original = getattr(module, name)
    failed = False

    def fail_candidate_refresh():
        nonlocal failed
        if installer._pending_root is not None and not failed:
            failed = True
            raise RuntimeError("sample cache refresh failure")
        return original()

    monkeypatch.setattr(module, name, fail_candidate_refresh)
    try:
        result = run(project, ["integration", "install", KEY, "--trust-integration"])
        assert result.exit_code == 1, result.output
        assert "sample cache refresh failure" in " ".join(result.output.split())
        assert failed
        assert installer._pending_root is None
        assert KEY not in INTEGRATION_REGISTRY
        assert KEY not in AGENT_CONFIG
        assert KEY not in CommandRegistrar.AGENT_CONFIGS
        assert not installer._source_packages
        assert not any(name.startswith(installer._MODULE_PREFIX) for name in sys.modules)
        assert snapshot(project) == before
        other = catalog_project(tmp_path / "other", server)
        install(other)
        assert KEY in INTEGRATION_REGISTRY
    finally:
        installer._pending_root = None
        unload_installed_integrations()


@pytest.mark.parametrize("budget", ["bytes", "entries", "exact"])
def test_round7_snapshot_budget_is_checked_before_overwriting_existing_output(tmp_path, server, monkeypatch, budget):
    from specify_cli.integrations import _lifecycle

    body = '''    def setup(self, project_root, manifest, **kwargs):
        manifest.record_file(".sample-agent/skills/speckit-sample/SKILL.md", "new sample output")
        return []
'''
    publish(server, code=implementation(body=body))
    project = catalog_project(tmp_path, server)
    target = project / ".sample-agent/skills/speckit-sample/SKILL.md"
    target.parent.mkdir(parents=True)
    original = "original sample output"
    target.write_text(original)
    before = snapshot(project)
    monkeypatch.setattr(
        _lifecycle, "_MAX_BACKUP_BYTES", len(original.encode()) if budget == "exact" else 4,
        raising=False,
    )
    monkeypatch.setattr(_lifecycle, "_MAX_BACKUP_ENTRIES", 0 if budget == "entries" else 1, raising=False)
    result = run(project, ["integration", "install", KEY, "--trust-integration", "--script", "py"])
    if budget == "exact":
        assert result.exit_code == 0, result.output
        assert target.read_text() == "new sample output"
    else:
        assert result.exit_code == 1, result.output
        assert "snapshot budget" in " ".join(result.output.split())
        assert snapshot(project) == before
        assert KEY not in INTEGRATION_REGISTRY


def test_round7_recording_unchanged_existing_output_needs_no_content_snapshot(tmp_path, server, monkeypatch):
    from specify_cli.integrations import installer

    body = '''    def setup(self, project_root, manifest, **kwargs):
        manifest.record_existing(".sample-agent/skills/sample-existing.md", recovered=True)
        return []
'''
    publish(server, code=implementation(body=body))
    project = catalog_project(tmp_path, server)
    target = project / ".sample-agent/skills/sample-existing.md"
    target.parent.mkdir(parents=True)
    target.write_text("original sample output")
    before = snapshot(project)

    def fail_commit(*args, **kwargs):
        raise OSError("sample package commit failure")

    monkeypatch.setattr(installer, "write_records", fail_commit)
    result = run(project, ["integration", "install", KEY, "--trust-integration", "--script", "py"])
    assert result.exit_code == 1, result.output
    assert snapshot(project) == before


def test_round7_unobserved_overwrite_reports_unrecoverable_output_instead_of_deleting_it(tmp_path, server):
    body = '''    def setup(self, project_root, manifest, **kwargs):
        target = project_root / ".sample-agent/skills/sample-existing.md"
        target.write_text("unobserved sample write")
        manifest.record_existing(".sample-agent/skills/sample-existing.md")
        return []
'''
    publish(server, code=implementation(body=body))
    project = catalog_project(tmp_path, server)
    target = project / ".sample-agent/skills/sample-existing.md"
    target.parent.mkdir(parents=True)
    target.write_text("original sample output")
    result = run(project, ["integration", "install", KEY, "--trust-integration", "--script", "py"])
    assert result.exit_code == 1, result.output
    assert "before-write" in " ".join(result.output.split())
    assert "cannot restore" in " ".join(result.output.split())
    assert target.read_text() == "unobserved sample write"
    assert KEY not in read_records(project)
    assert KEY not in INTEGRATION_REGISTRY


@pytest.mark.parametrize("operation", ["install", "load"])
@pytest.mark.parametrize("alias", [False, True])
def test_round6_project_cannot_supply_its_local_trust_state(tmp_path, server, operation, alias):
    from specify_cli.integrations.installer import _trust_identity

    marker = tmp_path / "adapter-imported"
    publish(server, code=f"from pathlib import Path\nPath({str(marker)!r}).touch()\n" + implementation())
    project = Path.home() / ".specify"
    if operation == "load":
        original = catalog_project(tmp_path, server)
        install(original)
        shutil.copytree(original, project, dirs_exist_ok=True)
        trust = project / "integration-trust.json"
        data = json.loads(trust.read_text())
        data["grants"].append(_trust_identity(project, KEY, read_records(project)[KEY]["files"]))
        trust.write_text(json.dumps(data))
        marker.unlink()
    else:
        (project / ".specify").mkdir(parents=True)
        added = run(project, [
            "integration", "catalog", "add", f"{server.url}/catalog.json", "--name", "samples",
        ])
        assert added.exit_code == 0, added.output
    if alias:
        link = tmp_path / "project-alias"
        try:
            link.symlink_to(project, target_is_directory=True)
        except OSError as exc:
            pytest.skip(f"Symlinks unavailable: {exc}")
        project = link
    before = snapshot(project)
    arguments = (
        ["integration", "list"] if operation == "load"
        else ["integration", "install", KEY, "--trust-integration"]
    )
    result = run(project, arguments)
    assert result.exit_code == 1, result.output
    assert "outside the project" in " ".join(result.output.split())
    assert not marker.exists()
    assert snapshot(project) == before
    assert KEY not in INTEGRATION_REGISTRY


@pytest.mark.parametrize("directory", ["projects", ".specify/projects", ".specify-other"])
def test_round6_home_projects_outside_trust_path_remain_supported(server, directory):
    publish(server)
    project = catalog_project(Path.home() / directory, server)
    install(project)
    unload_installed_integrations()
    result = run(project, ["integration", "list"])
    assert result.exit_code == 0, result.output
    assert KEY in INTEGRATION_REGISTRY


@pytest.mark.parametrize("content", ["{", '{"schema_version":"1.0","grants":[false]}'])
def test_round6_invalid_local_trust_state_fails_before_candidate_import(tmp_path, server, content):
    marker = tmp_path / "adapter-imported"
    publish(server, code=f"from pathlib import Path\nPath({str(marker)!r}).touch()\n" + implementation())
    project = catalog_project(tmp_path, server)
    trust = Path.home() / ".specify/integration-trust.json"
    trust.parent.mkdir()
    trust.write_text(content)
    before = snapshot(project)
    result = run(project, ["integration", "install", KEY, "--trust-integration"])
    assert result.exit_code == 1, result.output
    assert "local trust state" in " ".join(result.output.split())
    assert not marker.exists()
    assert snapshot(project) == before
    assert trust.read_text() == content
    assert KEY not in INTEGRATION_REGISTRY


@pytest.mark.parametrize("multi_install_safe", [False, True])
@pytest.mark.parametrize("folder,legacy", [
    (".sample-agent", ".sample-agent"),
    (".sample-agent", ".sample-agent/skills"),
    (".sample-agent", ".sample-agent/skills/previous"),
    (".sample-agent", ".SAMPLE-AGENT"),
    (".sample-agent", ".SAMPLE-AGENT/previous"),
    (".sample-agent/current", ".sample-agent"),
    (".sample-agent/current", ".SAMPLE-AGENT"),
])
def test_round6_overlapping_own_output_roots_fail_before_setup(
    tmp_path, server, multi_install_safe, folder, legacy,
):
    body = f'''    multi_install_safe = {multi_install_safe!r}
    registrar_config = {{**registrar_config, "legacy_dir": {legacy!r}}}
    def setup(self, project_root, manifest, **kwargs):
        (project_root / "setup-ran").touch()
        return []
'''
    publish(server, code=implementation(folder=folder, body=body))
    project = catalog_project(tmp_path, server)
    before = snapshot(project)
    result = run(project, ["integration", "install", KEY, "--trust-integration"])
    assert result.exit_code == 1, result.output
    assert "overlap" in result.output.lower(), result.output
    assert not (project / "setup-ran").exists()
    assert snapshot(project) == before
    assert KEY not in INTEGRATION_REGISTRY


@pytest.mark.parametrize("multi_install_safe", [False, True])
def test_round6_distinct_own_output_roots_with_shared_name_prefix_are_supported(
    tmp_path, server, multi_install_safe,
):
    body = f'''    multi_install_safe = {multi_install_safe!r}
    registrar_config = {{**registrar_config, "legacy_dir": ".sample-agent-previous/skills"}}
'''
    publish(server, code=implementation(body=body))
    project = catalog_project(tmp_path, server)
    install(project)
    assert CommandRegistrar(project).AGENT_CONFIGS[KEY]["legacy_dir"] == ".sample-agent-previous/skills"


@pytest.mark.parametrize("recording", ["record_file", "record_existing"])
@pytest.mark.parametrize("preexisting", [
    None, ".sample-agent", ".sample-agent/skills", ".sample-agent/skills/speckit-sample",
])
def test_round6_failed_install_preserves_original_empty_output_directories(
    tmp_path, server, monkeypatch, recording, preexisting,
):
    from specify_cli.integrations import installer

    writing = (
        '            manifest.record_file(relative, "sample output")\n'
        if recording == "record_file" else
        '''            path = project_root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("sample output")
            manifest.record_existing(relative)
'''
    )
    body = '''    def setup(self, project_root, manifest, **kwargs):
        for name in ("SKILL.md", "extra.md"):
            relative = f".sample-agent/skills/speckit-sample/{name}"
''' + writing + '        return []\n'
    publish(server, code=implementation(body=body))
    project = catalog_project(tmp_path, server)
    if preexisting:
        (project / preexisting).mkdir(parents=True)
    original_directories = {path for path in project.rglob("*") if path.is_dir()}
    before = snapshot(project)

    def fail_commit(*args, **kwargs):
        assert (project / ".sample-agent/skills/speckit-sample/SKILL.md").is_file()
        assert (project / ".sample-agent/skills/speckit-sample/extra.md").is_file()
        raise OSError("sample package commit failure")

    monkeypatch.setattr(installer, "write_records", fail_commit)
    result = run(project, ["integration", "install", KEY, "--trust-integration", "--script", "py"])
    assert result.exit_code == 1, result.output
    assert "sample package commit failure" in result.output
    assert snapshot(project) == before
    assert all(path.is_dir() for path in original_directories)
    if preexisting:
        assert not any((project / preexisting).iterdir())
    else:
        assert not (project / ".sample-agent").exists()
    assert KEY not in INTEGRATION_REGISTRY


@pytest.mark.parametrize("integration,relative,home_scoped", [
    ("copilot", ".vscode", False),
    ("hermes", ".hermes/skills/speckit-plan", True),
])
@pytest.mark.parametrize("existing", [False, True])
def test_round6_failed_switch_preserves_directory_ownership_outside_adapter_root(
    tmp_path, server, monkeypatch, integration, relative, home_scoped, existing,
):
    from specify_cli.integrations import installer

    publish(server)
    project = catalog_project(tmp_path, server)
    install(project)
    directory = (Path.home() if home_scoped else project) / relative
    if existing:
        directory.mkdir(parents=True)
    before = snapshot(project)

    def fail_commit(*args, **kwargs):
        assert any(directory.iterdir())
        raise OSError("sample package commit failure")

    monkeypatch.setattr(installer, "write_records", fail_commit)
    result = run(project, [
        "integration", "switch", integration,
        *([] if home_scoped else ["--integration-options=--commands"]),
    ])
    assert result.exit_code == 1, result.output
    assert "sample package commit failure" in result.output
    assert snapshot(project) == before
    assert directory.is_dir() == existing
    if existing:
        assert not any(directory.iterdir())


@pytest.mark.parametrize("damaged", [False, True])
@pytest.mark.parametrize("command", ["status", "status-json", "status-run-json", "info"])
def test_round4_workflow_metadata_does_not_load_adapter(tmp_path, server, damaged, command, monkeypatch):
    from specify_cli.integrations import installer
    from specify_cli.workflows.engine import RunState

    publish(server)
    project = catalog_project(tmp_path, server)
    install(project)
    state = RunState(run_id="sample-run", workflow_id="sample-workflow", project_root=project)
    state.save()
    source = project / "sample-workflow.yml"
    source.write_text(yaml.safe_dump({
        "schema_version": "1.0",
        "workflow": {"id": "sample-workflow", "name": "Sample Workflow", "version": "1.0.0"},
        "steps": [{"id": "sample-shell", "type": "shell", "run": "echo sample"}],
    }))
    if damaged:
        (project / ".specify/integrations/packages/sample-agent/__init__.py").write_text("damaged")

    def forbidden_load(*args, **kwargs):
        raise AssertionError("metadata inspection must not execute installed adapters")

    monkeypatch.setattr(installer, "load_installed_integrations", forbidden_load)
    arguments = {
        "status": ["workflow", "status"],
        "status-json": ["workflow", "status", "--json"],
        "status-run-json": ["workflow", "status", "sample-run", "--json"],
        "info": ["workflow", "info", str(source)],
    }[command]
    result = run(project, arguments)
    assert result.exit_code == 0, result.output
    assert result.stderr == ""
    if command == "status-json":
        assert json.loads(result.stdout)["runs"][0]["run_id"] == "sample-run"
    elif command == "status-run-json":
        assert json.loads(result.stdout)["run_id"] == "sample-run"
    else:
        assert "sample-workflow" in result.stdout


@pytest.mark.parametrize("existing", [False, True])
def test_round4_failed_switch_restores_builtin_settings(tmp_path, server, monkeypatch, existing):
    from specify_cli.integrations import installer

    publish(server)
    project = catalog_project(tmp_path, server)
    install(project)
    settings = project / ".vscode/settings.json"
    if existing:
        settings.parent.mkdir()
        settings.write_text('{"user.setting": true}\n')
    before = snapshot(project)

    def fail_commit(*args, **kwargs):
        assert json.loads(settings.read_text())["chat.promptFilesRecommendations"]
        raise OSError("sample package commit failure")

    monkeypatch.setattr(installer, "write_records", fail_commit)
    result = run(project, [
        "integration", "switch", "copilot", "--integration-options=--commands",
    ])
    assert result.exit_code == 1, result.output
    assert "sample package commit failure" in result.output
    assert snapshot(project) == before


@pytest.mark.parametrize("install_allowed", [False, True])
def test_round4_search_advertises_only_allowed_external_installation(tmp_path, server, install_allowed):
    publish(server, code='raise RuntimeError("discovery must not import sample code")')
    project = catalog_project(tmp_path, server, install_allowed=install_allowed)
    result = run(project, ["integration", "search", KEY])
    assert result.exit_code == 0, result.output
    output = " ".join(result.output.split())
    assert (f"specify integration install {KEY}" in output) == install_allowed
    assert "Only built-in" not in output
    assert KEY not in INTEGRATION_REGISTRY


@pytest.mark.parametrize("target", ["hermes", "kimi"])
def test_round4_failed_switch_restores_builtin_global_and_legacy_outputs(tmp_path, server, monkeypatch, target):
    from specify_cli.integrations import installer

    publish(server)
    project = catalog_project(tmp_path, server)
    install(project)
    if target == "hermes":
        scope = Path.home() / ".hermes/skills"
        managed = scope / "speckit-plan/SKILL.md"
    else:
        scope = project / ".kimi/skills"
        managed = scope / "speckit.sample/SKILL.md"
    managed.parent.mkdir(parents=True)
    original = (
        "---\nmetadata:\n  author: github-spec-kit\n"
        "  source: templates/commands/sample.md\n---\nSample legacy skill\n"
    )
    managed.write_text(original)
    untouched = scope / "user-skill/SKILL.md"
    untouched.parent.mkdir()
    untouched.write_text("user-owned skill")
    before = snapshot(project)
    home_before = snapshot(scope)

    def fail_commit(*args, **kwargs):
        if target == "hermes":
            assert managed.read_text() != original
        else:
            assert not managed.exists()
            assert (project / ".kimi-code/skills/speckit-sample/SKILL.md").exists()
        raise OSError("sample package commit failure")

    monkeypatch.setattr(installer, "write_records", fail_commit)
    result = run(project, [
        "integration", "switch", target,
        *(["--integration-options=--migrate-legacy"] if target == "kimi" else []),
    ])
    assert result.exit_code == 1, result.output
    assert "sample package commit failure" in result.output
    assert snapshot(project) == before
    assert snapshot(scope) == home_before
    if target == "hermes":
        assert not (project / ".hermes").exists()


@pytest.mark.parametrize("events_format", ["json-nested", "copilot-json", "toml"])
def test_round4_failed_switch_restores_native_event_merges(tmp_path, server, monkeypatch, events_format):
    from specify_cli.integrations import installer

    extension = tmp_path / "sample-events"
    extension.mkdir()
    (extension / "extension.yml").write_text(yaml.safe_dump({
        "schema_version": "1.0",
        "extension": {
            "id": "sample-events", "name": "Sample Events", "version": "1.0.0",
            "description": "Sample event-only extension",
        },
        "requires": {"speckit_version": ">=0.1"},
        "provides": {"commands": []},
        "events": {"session_start": {"command": "speckit.sample.boot"}},
    }))
    suffix = "toml" if events_format == "toml" else "json"
    body = (
        '    CANONICAL_TO_NATIVE = {"session_start": "SampleStart"}\n'
        f'    events_config_file = ".sample-agent/events.{suffix}"\n'
        f'    events_format = {events_format!r}\n'
    )
    publish(server, code=implementation(body=body))
    project = catalog_project(tmp_path, server)
    install(project)
    assert run(project, ["extension", "add", "--dev", str(extension)]).exit_code == 0
    config = project / f".sample-agent/events.{suffix}"
    assert config.is_file()
    before = snapshot(project)

    def fail_commit(*args, **kwargs):
        assert not config.exists()
        raise OSError("sample package commit failure")

    monkeypatch.setattr(installer, "write_records", fail_commit)
    result = run(project, ["integration", "switch", "claude"])
    assert result.exit_code == 1, result.output
    assert "sample package commit failure" in result.output
    assert snapshot(project) == before


def test_round4_failed_switch_restores_preset_composition_cache(tmp_path, server, monkeypatch):
    from specify_cli.integrations import installer

    publish(server)
    project = catalog_project(tmp_path, server)
    install(project)
    preset = tmp_path / "sample-preset"
    (preset / "commands").mkdir(parents=True)
    (preset / "commands/sample.md").write_text(
        "---\ndescription: Sample wrapper\nstrategy: wrap\n---\n{CORE_TEMPLATE}\nSample wrapper\n"
    )
    (preset / "preset.yml").write_text(yaml.safe_dump({
        "schema_version": "1.0",
        "preset": {"id": "sample-preset", "name": "Sample Preset", "version": "1.0.0", "description": "Sample wrapper"},
        "requires": {"speckit_version": ">=0.1"},
        "provides": {"templates": [{
            "type": "command", "name": "speckit.plan", "file": "commands/sample.md",
            "strategy": "wrap",
        }]},
    }))
    added = run(project, ["preset", "add", "--dev", str(preset)])
    assert added.exit_code == 0, added.output
    cache = project / ".specify/presets/sample-preset/.composed/speckit.plan.md"
    cache.write_text("previous cache bytes")
    settings = project / ".vscode/settings.json"
    settings.parent.mkdir()
    settings.write_bytes(INTEGRATION_REGISTRY["copilot"]._vscode_settings_path().read_bytes())
    before = snapshot(project)

    def fail_commit(*args, **kwargs):
        assert cache.read_text() != "previous cache bytes"
        raise OSError("sample package commit failure")

    monkeypatch.setattr(installer, "write_records", fail_commit)
    result = run(project, ["integration", "switch", "copilot", "--integration-options=--commands"])
    assert result.exit_code == 1, result.output
    assert "sample package commit failure" in result.output
    assert snapshot(project) == before


@pytest.mark.parametrize("existing", [False, True])
def test_round4_successful_switch_retains_settings_ownership_rules(tmp_path, server, existing):
    publish(server)
    project = catalog_project(tmp_path, server)
    install(project)
    settings = project / ".vscode/settings.json"
    if existing:
        settings.parent.mkdir()
        settings.write_text('{"user.setting": true}')
    result = run(project, ["integration", "switch", "copilot", "--integration-options=--commands"])
    assert result.exit_code == 0, result.output
    assert json.loads(settings.read_text())["chat.promptFilesRecommendations"]
    manifest = json.loads((project / ".specify/integrations/copilot.manifest.json").read_text())
    assert (".vscode/settings.json" in manifest["files"]) != existing
    if existing:
        assert json.loads(settings.read_text())["user.setting"] is True


def test_round4_failed_settings_merge_preserves_concurrent_user_edit(tmp_path, server, monkeypatch):
    from specify_cli.integrations import _lifecycle, installer

    publish(server)
    project = catalog_project(tmp_path, server)
    install(project)
    settings = project / ".vscode/settings.json"
    settings.parent.mkdir()
    settings.write_text('{"user.setting": true}')
    original_mkdtemp = _lifecycle.tempfile.mkdtemp
    backups = []

    def record_backup(*args, **kwargs):
        path = original_mkdtemp(*args, **kwargs)
        if kwargs.get("prefix") == "speckit-integration-rollback-":
            backups.append(Path(path))
        return path

    def fail_commit(*args, **kwargs):
        settings.write_text('{"concurrent.user.edit": true}')
        raise OSError("sample package commit failure")

    monkeypatch.setattr(_lifecycle.tempfile, "mkdtemp", record_backup)
    monkeypatch.setattr(installer, "write_records", fail_commit)
    result = run(project, ["integration", "switch", "copilot", "--integration-options=--commands"])
    assert result.exit_code == 1, result.output
    assert json.loads(settings.read_text()) == {"concurrent.user.edit": True}
    assert "Preserved concurrent edits" in result.output
    assert len(backups) == 1
    shutil.rmtree(backups[0])


@pytest.mark.parametrize("field,value", [
    ("invoke_separator", None), ("invoke_separator", ""), ("invoke_separator", 1),
    ("invoke_separator", False), ("dev_no_symlink", "false"),
    ("dev_no_symlink", 1), ("dev_no_symlink", None),
])
def test_round5_invalid_public_adapter_attributes_are_rejected(tmp_path, server, field, value):
    publish(server, code=implementation(body=f"    {field} = {value!r}\n"))
    project = catalog_project(tmp_path, server)
    before = snapshot(project)
    result = run(project, ["integration", "install", KEY, "--trust-integration"])
    assert result.exit_code == 1, result.output
    assert field in result.output, result.output
    assert snapshot(project) == before
    assert KEY not in INTEGRATION_REGISTRY


@pytest.mark.parametrize("no_symlinks", [False, True])
def test_round5_valid_public_attributes_propagate_to_rendering_and_recovery(tmp_path, server, no_symlinks):
    from specify_cli.integrations.installer import recovery_metadata

    publish(server, code=implementation(
        body=f'    invoke_separator = "_"\n    dev_no_symlink = {no_symlinks!r}\n',
    ))
    project = catalog_project(tmp_path, server)
    install(project)
    registrar = CommandRegistrar(project)
    assert registrar.AGENT_CONFIGS[KEY]["invoke_separator"] == "_"
    assert bool(registrar.AGENT_CONFIGS[KEY].get("dev_no_symlink")) == no_symlinks
    record = read_records(project)[KEY]
    binding = recovery_metadata(project, KEY, record)
    assert binding["registrar_config"]["invoke_separator"] == "_"
    assert binding["registrar_config"]["dev_no_symlink"] is no_symlinks
    assert binding["files"] == record["files"]


@pytest.mark.parametrize("damage", ["package", "files", "project"])
def test_round5_recovery_checks_local_package_identity(tmp_path, server, damage):
    from specify_cli.integrations.installer import _recovery_identity

    publish(server)
    project = catalog_project(tmp_path, server)
    install(project)
    path = Path.home() / ".specify/integration-trust.json"
    data = json.loads(path.read_text())
    binding = data["recovery"][_recovery_identity(project, KEY)]
    if damage == "package":
        binding["package"] = "0" * 64
    elif damage == "files":
        binding["files"] = {"__init__.py": "0" * 64}
    else:
        other = catalog_project(tmp_path / "other", server)
        install(other)
        data = json.loads(path.read_text())
        data["recovery"][_recovery_identity(project, KEY)] = data["recovery"][_recovery_identity(other, KEY)]
    path.write_text(json.dumps(data))
    (project / f".specify/integrations/packages/{KEY}/__init__.py").unlink()
    before = snapshot(project)
    result = run(project, ["integration", "uninstall", KEY, "--force"])
    assert result.exit_code == 1, result.output
    assert "package identity" in " ".join(result.output.split()).lower(), result.output
    assert snapshot(project) == before


def test_round5_legacy_recovery_binding_remains_supported(tmp_path, server):
    from specify_cli.integrations.installer import _recovery_identity

    publish(server)
    project = catalog_project(tmp_path, server)
    install(project)
    path = Path.home() / ".specify/integration-trust.json"
    data = json.loads(path.read_text())
    data["recovery"][_recovery_identity(project, KEY)].pop("files", None)
    path.write_text(json.dumps(data))
    (project / f".specify/integrations/packages/{KEY}/__init__.py").unlink()
    result = run(project, ["integration", "uninstall", KEY, "--force"])
    assert result.exit_code == 0, result.output
    assert not (project / ".sample-agent/skills/speckit-plan/SKILL.md").exists()


def test_round5_revoked_package_grant_preserves_generated_files_on_forced_cleanup(tmp_path, server):
    publish(server)
    project = catalog_project(tmp_path, server)
    install(project)
    path = Path.home() / ".specify/integration-trust.json"
    data = json.loads(path.read_text())
    data["grants"] = []
    path.write_text(json.dumps(data))
    result = run(project, ["integration", "uninstall", KEY, "--force"])
    assert result.exit_code == 0, result.output
    assert "No local recovery ownership record" in " ".join(result.output.split())
    assert (project / ".sample-agent/skills/speckit-plan/SKILL.md").exists()
    assert not (project / f".specify/integrations/packages/{KEY}").exists()


@pytest.mark.parametrize("hashes", [None, [], {"__init__.py": None}])
def test_round5_invalid_local_recovery_hashes_fail_explicitly(tmp_path, server, hashes):
    from specify_cli.integrations.installer import _recovery_identity

    publish(server)
    project = catalog_project(tmp_path, server)
    install(project)
    path = Path.home() / ".specify/integration-trust.json"
    data = json.loads(path.read_text())
    data["recovery"][_recovery_identity(project, KEY)]["files"] = hashes
    path.write_text(json.dumps(data))
    before = snapshot(project)
    result = run(project, ["integration", "uninstall", KEY, "--force"])
    assert result.exit_code == 1, result.output
    assert "Invalid integration local recovery package hashes" in " ".join(result.output.split())
    assert snapshot(project) == before


def test_adapter_only_descriptor(tmp_path):
    path = tmp_path / "integration.yml"
    path.write_text(yaml.safe_dump(descriptor()))
    parsed = IntegrationDescriptor(path)
    assert parsed.id == KEY
    assert parsed.tools == []
    assert parsed.commands == parsed.scripts == []


@pytest.mark.parametrize("provides", [{}, {"commands": [], "scripts": []}, {"scripts": ["helper.py"]}])
def test_optional_legacy_provides_preserved(tmp_path, provides):
    path = tmp_path / "integration.yml"
    path.write_text(yaml.safe_dump({**descriptor(), "provides": provides}))
    parsed = IntegrationDescriptor(path)
    assert parsed.scripts == provides.get("scripts", [])


@pytest.mark.parametrize("requires", [
    {"speckit_version": "invalid"},
    {"speckit_version": ">=0.6", "tools": ["sample-agent"]},
    {"speckit_version": ">=0.6", "tools": [{"name": "sample-agent", "required": "yes"}]},
    {"speckit_version": ">=0.6", "tools": [{"name": "sample-agent", "version": "latest"}]},
])
def test_invalid_descriptor_requirements(tmp_path, requires):
    path = tmp_path / "integration.yml"
    path.write_text(yaml.safe_dump({**descriptor(), "requires": requires}))
    with pytest.raises(IntegrationDescriptorError):
        IntegrationDescriptor(path)


@pytest.mark.parametrize("archive", ["zip", "tar.gz"])
def test_catalog_install_renders_host_templates_and_fresh_process(tmp_path, server, archive):
    publish(server, archive=archive)
    project = catalog_project(tmp_path, server)
    install(project)
    records = read_records(project)
    assert records[KEY]["version"] == "1.0.0"
    package = project / ".specify/integrations/packages" / KEY
    assert set(records[KEY]["files"]) == {"integration.yml", "__init__.py"}
    assert not (package / "templates").exists()
    skill = project / ".sample-agent/skills/speckit-plan/SKILL.md"
    assert skill.is_file()
    rendered = skill.read_text(encoding="utf-8")
    assert ".specify/scripts/python/setup_plan.py" in rendered
    assert "{SCRIPT}" not in rendered and "__AGENT__" not in rendered
    assert "speckit-plan" in rendered
    manifest = json.loads((project / f".specify/integrations/{KEY}.manifest.json").read_text())
    assert not any("packages/" in name for name in manifest["files"])
    process = subprocess.run(
        [str(Path(sys.executable).parent / "specify"), "integration", "list"],
        cwd=project, capture_output=True, text=True, encoding="utf-8", check=False,
    )
    assert process.returncode == 0, process.stderr
    assert "Sample Agent" in process.stdout and KEY in process.stdout
    assert KEY in AGENT_CONFIG
    assert KEY in CommandRegistrar(project).AGENT_CONFIGS
    status = run(project, ["integration", "status", "--json"])
    assert status.exit_code == 0, status.output
    assert json.loads(status.output)["default_integration"] == KEY


def test_markdown_adapter_renders_host_commands(tmp_path, server):
    publish(server, code=implementation(flavor="markdown"))
    project = catalog_project(tmp_path, server)
    install(project)
    command = project / ".sample-agent/commands/speckit.plan.md"
    assert command.is_file()
    assert "{SCRIPT}" not in command.read_text(encoding="utf-8")
    assert not (project / ".sample-agent/skills").exists()


def test_catalog_discovery_does_not_import_and_denial_does_not_download(tmp_path, server):
    marker = tmp_path / "executed"
    publish(server, code=f"from pathlib import Path\nPath({str(marker)!r}).touch()\n" + implementation())
    project = catalog_project(tmp_path, server, install_allowed=False)
    for args in (["integration", "list", "--catalog"], ["integration", "info", KEY], ["integration", "search", KEY]):
        result = run(project, args)
        assert result.exit_code == 0, result.output
    denied = run(project, ["integration", "install", KEY, "--trust-integration"])
    assert denied.exit_code == 1 and "discovery-only" in denied.output
    assert not marker.exists()
    assert not any(".zip" in url for url in server.requests)


def test_trust_decline_does_not_download_or_import(tmp_path, server):
    marker = tmp_path / "executed"
    publish(server, code=f"from pathlib import Path\nPath({str(marker)!r}).touch()\n" + implementation())
    project = catalog_project(tmp_path, server)
    denied = run(project, ["integration", "install", KEY], input="n\n")
    assert denied.exit_code == 1 and "not trusted" in denied.output
    assert not marker.exists()
    assert not any(".zip" in url for url in server.requests)


@pytest.mark.parametrize(("change", "expected"), [
    ("id", "identity"), ("version", "version mismatch"), ("name", "name mismatch"),
    ("requires", "requirements mismatch"), ("checksum", "SHA-256 mismatch"),
    ("url", "HTTPS or loopback"), ("class-key", "class key mismatch"),
    ("class-name", "name mismatch"), ("class-version", "version mismatch"),
    ("import", "Failed to load"), ("multiple-classes", "exactly one"),
    ("side-effect", "import side effects"), ("paths", "Unsafe integration path"),
    ("registration-extension", "unsafe registration extension"),
    ("reserved-root", "reserved directory"), ("alternate-stream", "Unsafe integration path"),
    ("builtin", "already registered or built-in"),
    ("runtime-contract", "build_exec_args must accept"),
    ("runtime-model", "build_exec_args must accept model"),
    ("runtime-positional", "host execution signature"),
    ("missing-tool", "requires missing tool"), ("host-version", "requires Spec Kit"),
])
def test_invalid_packages_fail_explicitly_without_install(tmp_path, server, change, expected):
    data = descriptor()
    code = implementation()
    if change == "id":
        data["integration"]["id"] = "different-agent"
    elif change == "class-key":
        code = implementation(key="different-agent")
    elif change == "class-name":
        code = code.replace('"name": "Sample Agent"', '"name": "Different Name"')
    elif change == "class-version":
        code += '\n    version = "9.0.0"\n'
    elif change == "import":
        code = "raise RuntimeError('sample import failed')"
    elif change == "multiple-classes":
        code += "\nclass AnotherIntegration(SampleIntegration):\n    pass\n"
    elif change == "side-effect":
        code += "\nfrom specify_cli.integrations import _register\n_register(SampleIntegration())\n"
    elif change == "paths":
        code = implementation(folder="../outside")
    elif change == "registration-extension":
        code = code.replace("'/SKILL.md'", "'/../../outside'")
    elif change == "reserved-root":
        code = implementation(folder=".GIT")
    elif change == "alternate-stream":
        code = implementation(folder=".sample-agent:stream")
    elif change == "builtin":
        # A forged catalog key cannot turn a built-in class into an external adapter.
        code = implementation(key="copilot")
        expected = "class key mismatch"
    elif change == "runtime-contract":
        code += "\n    def build_exec_args(self, prompt):\n        return None\n"
    elif change == "runtime-model":
        code += "\n    def build_exec_args(self, prompt, *, integration_args=None, integration_options=None, project_root=None):\n        return None\n"
    elif change == "runtime-positional":
        code += "\n    def build_exec_args(self, prompt, model, output_json, integration_args, integration_options, project_root, /):\n        return None\n"
    elif change == "missing-tool":
        data["requires"]["tools"] = [{"name": "speckit-nonexistent-sample-tool", "required": True}]
    elif change == "host-version":
        data["requires"]["speckit_version"] = ">=999.0"
    info, _ = publish(server, metadata=data, code=code)
    if change == "version":
        info["version"] = "9.0.0"
    elif change == "name":
        info["name"] = "Different Name"
    elif change == "requires":
        info["requires"] = {"speckit_version": ">=0.9.0"}
    elif change == "checksum":
        info["sha256"] = "0" * 64
    elif change == "url":
        info["download_url"] = "http://example.com/sample-agent.zip"
    write_catalog(server, info)
    project = catalog_project(tmp_path, server)
    result = run(project, ["integration", "install", KEY, "--trust-integration"])
    assert result.exit_code == 1, result.output
    assert expected in " ".join(result.output.split()), result.output
    assert not (project / ".specify/integration.json").exists()
    assert not (project / ".sample-agent").exists()
    assert KEY not in INTEGRATION_REGISTRY


@pytest.mark.parametrize("member", ["../outside", "/absolute", r"..\outside"])
def test_malicious_archive_paths_rejected(tmp_path, server, member):
    publish(server, members={member: b"unsafe"})
    project = catalog_project(tmp_path, server)
    result = run(project, ["integration", "install", KEY, "--trust-integration"])
    assert result.exit_code == 1
    assert not (project / ".specify/integration.json").exists()


def test_archive_symlink_rejected(tmp_path, server):
    info, archive = publish(server)
    with zipfile.ZipFile(archive, "a") as package:
        entry = zipfile.ZipInfo("linked.py")
        entry.create_system = 3
        entry.external_attr = (stat.S_IFLNK | 0o777) << 16
        package.writestr(entry, "../outside")
    info["sha256"] = hashlib.sha256(archive.read_bytes()).hexdigest()
    write_catalog(server, info)
    project = catalog_project(tmp_path, server)
    result = run(project, ["integration", "install", KEY, "--trust-integration"])
    assert result.exit_code == 1 and "symlink" in result.output.lower()


def test_upgrade_and_uninstall_preserve_edits_and_remove_package(tmp_path, server):
    publish(server)
    project = catalog_project(tmp_path, server)
    install(project)
    skill = project / ".sample-agent/skills/speckit-plan/SKILL.md"
    skill.write_text(skill.read_text(encoding="utf-8") + "\nUser customization\n", encoding="utf-8")
    before = snapshot(project)
    publish(server, version="2.0.0")
    blocked = run(project, ["integration", "upgrade", KEY, "--trust-integration"])
    assert blocked.exit_code == 1 and "modified" in blocked.output
    assert snapshot(project) == before
    upgraded = run(project, ["integration", "upgrade", KEY, "--trust-integration", "--force"])
    assert upgraded.exit_code == 0, upgraded.output
    assert read_records(project)[KEY]["version"] == "2.0.0"
    skill.write_text("User customization\n")
    removed = run(project, ["integration", "uninstall", KEY])
    assert removed.exit_code == 0, removed.output
    assert skill.read_text() == "User customization\n"
    assert not (project / f".specify/integrations/packages/{KEY}").exists()
    assert not (project / ".specify/integrations/packages.json").exists()
    assert KEY not in INTEGRATION_REGISTRY and KEY not in AGENT_CONFIG
    assert KEY not in CommandRegistrar(project).AGENT_CONFIGS


@pytest.mark.parametrize("operation", ["install", "upgrade", "switch"])
def test_setup_failure_rolls_back_code_metadata_and_generated_files(tmp_path, server, operation):
    publish(server)
    project = catalog_project(tmp_path, server)
    if operation == "upgrade":
        install(project)
    elif operation == "switch":
        result = run(project, ["integration", "install", "claude"])
        assert result.exit_code == 0, result.output
    before = snapshot(project)
    body = '''
    def setup(self, project_root, manifest, **kwargs):
        super().setup(project_root, manifest, **kwargs)
        raise RuntimeError("sample setup failed")
'''
    publish(server, version="2.0.0", code=implementation(body=body))
    result = run(project, ["integration", operation, KEY, "--trust-integration"])
    assert result.exit_code == 1 and "sample setup failed" in " ".join(result.output.split()), result.output
    assert snapshot(project) == before
    if operation == "upgrade":
        assert read_records(project)[KEY]["version"] == "1.0.0"
        assert INTEGRATION_REGISTRY[KEY].config["name"] == "Sample Agent"
    else:
        assert KEY not in INTEGRATION_REGISTRY


def test_missing_or_modified_code_is_loud_and_json_status_is_parseable(tmp_path, server):
    publish(server)
    project = catalog_project(tmp_path, server)
    install(project)
    code = project / f".specify/integrations/packages/{KEY}/__init__.py"
    code.write_text(code.read_text() + "\nraise RuntimeError('do not execute')\n")
    status = run(project, ["integration", "status", "--json"])
    assert status.exit_code == 1
    report = json.loads(status.output)
    assert report["status"] == "error"
    assert report["findings"][0]["code"] == "integration-package-invalid"
    with pytest.raises(IntegrationInstallError, match="modified"):
        load_installed_integrations(project)
    code.unlink()
    with pytest.raises(IntegrationInstallError, match="root integration.yml"):
        load_installed_integrations(project)


def test_cross_project_registry_module_and_cache_isolation(tmp_path, server):
    publish(server, members={"helper.py": b"VALUE = 'sample'\n"}, code="from .helper import VALUE\n" + implementation())
    project = catalog_project(tmp_path, server)
    install(project)
    module = type(INTEGRATION_REGISTRY[KEY]).__module__
    assert module + ".helper" in sys.modules
    other = tmp_path / "other-project"
    (other / ".specify").mkdir(parents=True)
    registrar = CommandRegistrar(other)
    assert KEY not in registrar.AGENT_CONFIGS
    assert KEY not in CommandRegistrar.AGENT_CONFIGS
    assert KEY not in AGENT_CONFIG and KEY not in INTEGRATION_REGISTRY
    assert not any(name.startswith(module) for name in sys.modules)
    load_installed_integrations(project)
    assert KEY in CommandRegistrar(project).AGENT_CONFIGS and KEY in AGENT_CONFIG


def test_symlinked_storage_never_follows_target(tmp_path, server):
    publish(server)
    project = catalog_project(tmp_path, server)
    outside = tmp_path / "outside"
    outside.mkdir()
    (project / ".specify/integrations").mkdir()
    (project / ".specify/integrations/packages").symlink_to(outside, target_is_directory=True)
    result = run(project, ["integration", "install", KEY, "--trust-integration"])
    assert result.exit_code == 1 and "Symlinked" in result.output
    assert list(outside.iterdir()) == []


def test_init_external_adapter_from_registered_catalog(tmp_path, server):
    publish(server)
    project = catalog_project(tmp_path, server)
    result = run(project, [
        "init", "--here", "--force", "--non-interactive", "--ignore-agent-tools",
        "--integration", KEY, "--trust-integration", "--script", "py",
    ])
    assert result.exit_code == 0, result.output
    assert (project / ".sample-agent/skills/speckit-specify/SKILL.md").exists()
    assert KEY in read_records(project)


def test_new_project_init_from_catalog_environment(tmp_path, server, monkeypatch):
    publish(server)
    monkeypatch.setenv("SPECKIT_INTEGRATION_CATALOG_URL", f"{server.url}/catalog.json")
    project = tmp_path / "new-project"
    result = runner.invoke(app, [
        "init", str(project), "--non-interactive", "--ignore-agent-tools",
        "--integration", KEY, "--trust-integration",
    ], catch_exceptions=False)
    assert result.exit_code == 0, result.output
    assert (project / ".sample-agent/skills/speckit-plan/SKILL.md").is_file()
    assert KEY in read_records(project)


@pytest.mark.parametrize("damaged_uninstall", [False, True])
@pytest.mark.parametrize("failed_commit", [False, True])
def test_extension_and_preset_contributions_follow_active_external_adapter(
    tmp_path, server, monkeypatch, damaged_uninstall, failed_commit,
):
    publish(server)
    project = catalog_project(tmp_path, server)
    assert run(project, ["integration", "install", "claude"]).exit_code == 0
    install(project)
    extension = run(project, ["extension", "add", "git"])
    assert extension.exit_code == 0, extension.output
    assert not (project / ".sample-agent/skills/speckit-git-commit/SKILL.md").exists()

    preset = tmp_path / "sample-preset"
    (preset / "commands").mkdir(parents=True)
    (preset / "commands/speckit.specify.md").write_text(
        "---\ndescription: Sample preset command\n---\nSample preset guidance\n"
    )
    (preset / "preset.yml").write_text(yaml.safe_dump({
        "schema_version": "1.0",
        "preset": {"id": "sample-preset", "name": "Sample Preset", "version": "1.0.0", "description": "Sample guidance"},
        "requires": {"speckit_version": ">=0.1"},
        "provides": {"templates": [{"type": "command", "name": "speckit.specify", "file": "commands/speckit.specify.md"}]},
    }))
    added = run(project, ["preset", "add", "--dev", str(preset)])
    assert added.exit_code == 0, added.output
    assert "Sample preset guidance" not in (project / ".sample-agent/skills/speckit-specify/SKILL.md").read_text(encoding="utf-8")
    activated = run(project, ["integration", "use", KEY])
    assert activated.exit_code == 0, activated.output
    assert (project / ".sample-agent/skills/speckit-git-commit/SKILL.md").is_file()
    assert "Sample preset guidance" in (project / ".sample-agent/skills/speckit-specify/SKILL.md").read_text(encoding="utf-8")
    executable = Path(sys.executable).parent / ("specify.exe" if os.name == "nt" else "specify")
    fresh_removal = subprocess.run(
        [str(executable), "preset", "remove", "sample-preset"],
        cwd=project, capture_output=True, text=True, encoding="utf-8", timeout=30, check=False,
    )
    assert fresh_removal.returncode == 0, fresh_removal.stdout + fresh_removal.stderr
    assert "Sample preset guidance" not in (project / ".sample-agent/skills/speckit-specify/SKILL.md").read_text(encoding="utf-8")
    restored = run(project, ["preset", "add", "--dev", str(preset)])
    assert restored.exit_code == 0, restored.output
    assert "Sample preset guidance" in (project / ".sample-agent/skills/speckit-specify/SKILL.md").read_text(encoding="utf-8")
    assert "sample-agent" in json.loads((project / ".specify/init-options.json").read_text())["ai"]
    upgraded = run(project, ["integration", "upgrade", KEY, "--trust-integration", "--force"])
    assert upgraded.exit_code == 0, upgraded.output
    assert "Sample preset guidance" in (project / ".sample-agent/skills/speckit-specify/SKILL.md").read_text(encoding="utf-8")
    arguments = ["integration", "uninstall", KEY]
    if damaged_uninstall:
        (project / f".specify/integrations/packages/{KEY}/__init__.py").unlink()
        arguments.append("--force")
    if failed_commit:
        from specify_cli.integrations import installer

        def fail_commit(*args, **kwargs):
            raise OSError("sample commit failure")

        before = snapshot(project)
        monkeypatch.setattr(installer, "write_records", fail_commit)
        failed = run(project, arguments)
        assert failed.exit_code == 1, failed.output
        assert snapshot(project) == before
        return
    removed = run(project, arguments)
    assert removed.exit_code == 0, removed.output
    assert not (project / ".sample-agent/skills/speckit-git-commit/SKILL.md").exists()
    assert not (project / ".sample-agent/skills/speckit-specify/SKILL.md").exists()
    assert (project / ".claude/skills/speckit-git-commit/SKILL.md").is_file()
    assert "Sample preset guidance" in (project / ".claude/skills/speckit-specify/SKILL.md").read_text(encoding="utf-8")
    assert KEY not in read_records(project)
    assert json.loads((project / ".specify/integration.json").read_text())["integration"] == "claude"


def test_builtin_generic_can_coexist_with_external_adapter(tmp_path, server):
    publish(server)
    project = catalog_project(tmp_path, server)
    installed = run(project, [
        "integration", "install", "generic",
        "--integration-options=--commands-dir .sample-generic/commands",
    ])
    assert installed.exit_code == 0, installed.output
    blocked = run(project, ["integration", "install", KEY, "--trust-integration"])
    assert blocked.exit_code == 1 and "multi-install" in blocked.output
    forced = run(project, ["integration", "install", KEY, "--trust-integration", "--force"])
    assert forced.exit_code == 0, forced.output
    assert (project / ".sample-generic/commands/speckit.plan.md").is_file()
    assert (project / ".sample-agent/skills/speckit-plan/SKILL.md").is_file()
    assert run(project, ["integration", "use", KEY]).exit_code == 0


def test_switch_to_and_from_external_adapter_removes_durable_code(tmp_path, server):
    publish(server)
    project = catalog_project(tmp_path, server)
    assert run(project, ["integration", "install", "claude"]).exit_code == 0
    switched = run(project, ["integration", "switch", KEY, "--trust-integration"])
    assert switched.exit_code == 0, switched.output
    assert KEY in read_records(project)
    assert not (project / ".claude/skills/speckit-plan/SKILL.md").exists()
    switched_back = run(project, ["integration", "switch", "claude"])
    assert switched_back.exit_code == 0, switched_back.output
    assert not (project / f".specify/integrations/packages/{KEY}").exists()
    assert not (project / ".sample-agent/skills/speckit-plan/SKILL.md").exists()
    assert (project / ".claude/skills/speckit-plan/SKILL.md").is_file()


@pytest.mark.parametrize("step_type", ["command", "prompt"])
def test_public_workflow_dispatch_loads_adapter_and_uses_process_double(tmp_path, server, monkeypatch, step_type):
    body = '''
    def build_exec_args(self, prompt, *, model=None, output_json=True,
                        integration_args=None, integration_options=None,
                        project_root=None):
        return ["sample-agent-process", "-p", prompt]
'''
    publish(server, code=implementation(body=body))
    project = catalog_project(tmp_path, server)
    install(project)
    unload_installed_integrations()
    from specify_cli.workflows import engine

    calls = []

    def process_double(argv, **kwargs):
        calls.append((argv, kwargs))
        return SimpleNamespace(returncode=0, stdout="sample response", stderr="")

    original_which = shutil.which
    monkeypatch.setattr(
        shutil, "which",
        lambda name, *args, **kwargs: "/sample-agent-process"
        if name == "sample-agent-process" else original_which(name, *args, **kwargs),
    )
    monkeypatch.setattr(subprocess, "run", process_double)
    step = {"id": "sample-dispatch", "type": step_type, "integration": KEY}
    if step_type == "command":
        step["command"] = "speckit.plan"
    else:
        step["prompt"] = "Sample prompt"
    path = project / "sample-workflow.yml"
    path.write_text(yaml.safe_dump({
        "schema_version": "1.0",
        "workflow": {"id": "sample-workflow", "name": "Sample Workflow", "version": "1.0.0"},
        "steps": [step],
    }))
    executed = run(project, ["workflow", "run", str(path), "--json"])
    assert executed.exit_code == 0, executed.output
    report = json.loads(executed.stdout)
    assert report["status"] == "completed"
    assert calls[0][0][:2] == ["/sample-agent-process", "-p"]
    assert calls[0][0][2] == ("/speckit-plan" if step_type == "command" else "Sample prompt")
    assert calls[0][1]["cwd"] == str(project)
    state = engine.RunState.load(report["run_id"], project)
    assert state.step_results["sample-dispatch"]["output"]["dispatched"] is True


@pytest.mark.parametrize("failure", ["import", "download", "commit"])
def test_upgrade_candidate_failure_restores_old_adapter(tmp_path, server, monkeypatch, failure):
    publish(server)
    project = catalog_project(tmp_path, server)
    install(project)
    before = snapshot(project)
    _info, archive = publish(server, version="2.0.0", code="raise RuntimeError('sample import error')" if failure == "import" else None)
    if failure == "download":
        archive.unlink()
    elif failure == "commit":
        from specify_cli.integrations import installer

        def fail_commit(*args, **kwargs):
            raise OSError("sample commit error")

        monkeypatch.setattr(installer, "write_records", fail_commit)
    result = run(project, ["integration", "upgrade", KEY, "--trust-integration"])
    assert result.exit_code == 1, result.output
    assert "upgraded successfully" not in result.output
    assert snapshot(project) == before
    assert read_records(project)[KEY]["version"] == "1.0.0"
    assert KEY in INTEGRATION_REGISTRY


def test_repeated_install_is_noop_without_downloading_another_package(tmp_path, server):
    publish(server)
    project = catalog_project(tmp_path, server)
    install(project)
    before = snapshot(project)
    server.requests.clear()
    result = run(project, ["integration", "install", KEY])
    assert result.exit_code == 0 and "already installed" in result.output
    assert snapshot(project) == before
    assert server.requests == []


def test_uninstall_failure_restores_package_and_files(tmp_path, server):
    body = '''
    def teardown(self, project_root, manifest, *, force=False):
        super().teardown(project_root, manifest, force=force)
        raise RuntimeError("sample teardown failed")
'''
    publish(server, code=implementation(body=body))
    project = catalog_project(tmp_path, server)
    install(project)
    before = snapshot(project)
    result = run(project, ["integration", "uninstall", KEY])
    assert result.exit_code == 1, result.output
    assert snapshot(project) == before
    assert KEY in INTEGRATION_REGISTRY


def test_force_uninstall_removes_modified_generated_files(tmp_path, server):
    publish(server)
    project = catalog_project(tmp_path, server)
    install(project)
    skill = project / ".sample-agent/skills/speckit-plan/SKILL.md"
    skill.write_text("User customization")
    result = run(project, ["integration", "uninstall", KEY, "--force"])
    assert result.exit_code == 0, result.output
    assert not skill.exists()


def test_builtin_collision_rejected_before_import(tmp_path, server):
    marker = tmp_path / "executed"
    publish(server, code=f"from pathlib import Path\nPath({str(marker)!r}).touch()\n" + implementation())
    project = catalog_project(tmp_path, server)
    package = project / ".specify/integrations/packages/copilot"
    package.mkdir(parents=True)
    (project / ".specify/integrations/packages.json").write_text(json.dumps({
        "schema_version": "1.0", "packages": {"copilot": {"trusted": True, "files": {}}},
    }))
    original = INTEGRATION_REGISTRY["copilot"]
    result = run(project, ["integration", "list"])
    assert result.exit_code == 1 and "collides with built-in" in " ".join(result.output.split())
    assert INTEGRATION_REGISTRY["copilot"] is original
    assert not marker.exists()


def test_class_export_from_helper_module_is_supported(tmp_path, server):
    publish(server, code="from .adapter import SampleIntegration\n", members={"adapter.py": implementation().encode()})
    project = catalog_project(tmp_path, server)
    install(project)
    assert type(INTEGRATION_REGISTRY[KEY]).__module__.endswith(".adapter")


def test_oversized_archive_entry_inventory_rejected(tmp_path, server):
    publish(server, members={f"extras/{index}.txt": b"sample" for index in range(513)})
    project = catalog_project(tmp_path, server)
    result = run(project, ["integration", "install", KEY, "--trust-integration"])
    assert result.exit_code == 1
    assert "limit" in result.output.lower() or "too many" in result.output.lower()
    assert not (project / ".sample-agent").exists()


def test_project_registry_changes_cannot_reuse_stale_metadata_cache(tmp_path, server):
    publish(server)
    project = catalog_project(tmp_path, server)
    install(project)
    registry = project / ".specify/integrations/packages.json"
    data = json.loads(registry.read_text())
    data["packages"][KEY]["version"] = "99.0.0"
    registry.write_text(json.dumps(data))
    with pytest.raises(IntegrationInstallError, match="version mismatch"):
        load_installed_integrations(project)
    assert KEY not in INTEGRATION_REGISTRY and KEY not in AGENT_CONFIG


@pytest.mark.parametrize("relative", ["__init__.py", "adapter.py"])
def test_cached_bytecode_cannot_replace_verified_source(tmp_path, server, relative):
    import importlib.util

    publish(server, code="from .adapter import SampleIntegration\n", members={"adapter.py": implementation().encode()})
    project = catalog_project(tmp_path, server)
    install(project)
    package = project / f".specify/integrations/packages/{KEY}"
    source = package / relative
    marker = tmp_path / "unverified-bytecode-executed"
    poisoned_code = compile(
        f"from pathlib import Path\nPath({str(marker)!r}).touch()\n" + source.read_text(),
        str(source), "exec",
    )
    cached = Path(importlib.util.cache_from_source(str(source)))
    cached.parent.mkdir(exist_ok=True)
    cached.write_bytes(
        importlib.util.MAGIC_NUMBER
        + struct.pack("<III", 0, int(source.stat().st_mtime), source.stat().st_size)
        + marshal.dumps(poisoned_code)
    )
    unload_installed_integrations()
    assert load_installed_integrations(project) == [KEY]
    assert not marker.exists()


def test_lazy_relative_import_verifies_the_bytes_it_executes(tmp_path, server):
    body = '''
    def build_exec_args(self, prompt, **kwargs):
        from .helper import VALUE
        return [VALUE, prompt]
'''
    publish(server, code=implementation(body=body), members={"helper.py": b"VALUE = 'sample-agent-process'\n"})
    project = catalog_project(tmp_path, server)
    install(project)
    helper = project / f".specify/integrations/packages/{KEY}/helper.py"
    original = helper.read_bytes()
    marker = tmp_path / "modified-helper-executed"
    helper.write_text(f"from pathlib import Path\nPath({str(marker)!r}).touch()\nVALUE = 'changed'\n")
    with pytest.raises(IntegrationInstallError, match="source has been modified"):
        INTEGRATION_REGISTRY[KEY].build_exec_args("Sample prompt")
    assert not marker.exists()
    helper.write_bytes(original)
    assert INTEGRATION_REGISTRY[KEY].build_exec_args("Sample prompt") == ["sample-agent-process", "Sample prompt"]


@pytest.mark.parametrize("command", ["run", "resume"])
def test_workflow_adapter_load_errors_are_json_envelopes(tmp_path, server, command):
    publish(server)
    project = catalog_project(tmp_path, server)
    install(project)
    (project / f".specify/integrations/packages/{KEY}/__init__.py").write_text("raise RuntimeError('changed')")
    source = project / "sample-workflow.yml"
    source.write_text("schema_version: '1.0'\n")
    result = run(project, ["workflow", command, str(source) if command == "run" else "sample-run", "--json"])
    assert result.exit_code == 1
    report = json.loads(result.stdout)
    assert report["status"] == "failed" and "modified" in report["error"]
    assert report["run_id"] == (None if command == "run" else "sample-run")
    assert result.stderr == ""


@pytest.mark.parametrize("symlink_in_target", [False, True])
def test_output_paths_are_validated_against_selected_project(tmp_path, server, monkeypatch, symlink_in_target):
    publish(server)
    project = catalog_project(tmp_path, server)
    other = tmp_path / "other-project"
    other.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    root = project if symlink_in_target else other
    (root / ".sample-agent").mkdir()
    (root / ".sample-agent/skills").symlink_to(outside, target_is_directory=True)
    monkeypatch.setenv("SPECIFY_INIT_DIR", str(project))
    result = run(other, ["integration", "install", KEY, "--trust-integration"])
    assert result.exit_code == (1 if symlink_in_target else 0), result.output
    assert list(outside.iterdir()) == []
    assert (project / ".specify/integrations/packages.json").exists() is not symlink_in_target


def test_failed_filesystem_recovery_retains_and_reports_snapshots(tmp_path, server, monkeypatch):
    from specify_cli.integrations import _lifecycle, installer

    publish(server)
    project = catalog_project(tmp_path, server)
    install(project)
    publish(server, version="2.0.0")
    original_mkdtemp = _lifecycle.tempfile.mkdtemp
    backups = []

    def record_backup(*args, **kwargs):
        path = original_mkdtemp(*args, **kwargs)
        if kwargs.get("prefix") == "speckit-integration-rollback-":
            backups.append(Path(path))
        return path

    def fail_commit(*args, **kwargs):
        raise OSError("sample commit error")

    def fail_restore(*args, **kwargs):
        raise OSError("sample recovery error")

    monkeypatch.setattr(_lifecycle.tempfile, "mkdtemp", record_backup)
    monkeypatch.setattr(_lifecycle, "_restore_snapshots", fail_restore)
    monkeypatch.setattr(installer, "write_records", fail_commit)
    result = run(project, ["integration", "upgrade", KEY, "--trust-integration"])
    assert result.exit_code == 1
    assert "rollback failed" in result.output and "Recovery snapshots retained" in result.output
    assert len(backups) == 1 and backups[0].is_dir()
    try:
        descriptors = list(backups[0].rglob("integration.yml"))
        assert descriptors
        assert any(
            yaml.safe_load(path.read_text())["integration"]["version"] == "1.0.0"
            for path in descriptors
        )
    finally:
        shutil.rmtree(backups[0])


def test_successful_install_does_not_reimport_after_committing(tmp_path, server):
    counter = tmp_path / "sample-import-count"
    prefix = f'''from pathlib import Path
counter = Path({str(counter)!r})
count = int(counter.read_text()) if counter.exists() else 0
counter.write_text(str(count + 1))
if count >= 2:
    raise RuntimeError("sample adapter imported after commit")
'''
    publish(server, code=prefix + implementation())
    project = catalog_project(tmp_path, server)
    install(project)
    assert counter.read_text() == "2"
    assert KEY in INTEGRATION_REGISTRY


def test_relative_namespace_package_is_supported(tmp_path, server):
    publish(
        server, code="from .helpers.adapter import SampleIntegration\n",
        members={"helpers/adapter.py": implementation().encode()},
    )
    project = catalog_project(tmp_path, server)
    install(project)
    assert type(INTEGRATION_REGISTRY[KEY]).__module__.endswith(".helpers.adapter")


def test_abstract_exports_do_not_count_as_concrete_adapters(tmp_path, server):
    prefix = '''from abc import ABC, abstractmethod
from specify_cli.integrations.base import IntegrationBase

class AbstractAdapter(IntegrationBase, ABC):
    @abstractmethod
    def sample(self):
        pass

'''
    publish(server, code=prefix + implementation())
    project = catalog_project(tmp_path, server)
    install(project)
    assert type(INTEGRATION_REGISTRY[KEY]).__name__ == "SampleIntegration"


def test_same_adapter_key_in_different_projects_uses_its_own_paths(tmp_path, server):
    publish(server, code=implementation(folder=".sample-first"))
    first = catalog_project(tmp_path, server)
    install(first)
    publish(server, version="2.0.0", code=implementation(folder=".sample-second"))
    second = catalog_project(tmp_path / "second", server)
    install(second)
    outside = tmp_path / "outside"
    outside.mkdir()
    (first / ".sample-second").symlink_to(outside, target_is_directory=True)
    load_installed_integrations(first)
    assert AGENT_CONFIG[KEY]["folder"] == ".sample-first"
    assert CommandRegistrar(first).AGENT_CONFIGS[KEY]["dir"] == ".sample-first/skills"
    load_installed_integrations(second)
    assert AGENT_CONFIG[KEY]["folder"] == ".sample-second"
    assert CommandRegistrar(second).AGENT_CONFIGS[KEY]["dir"] == ".sample-second/skills"


@pytest.mark.parametrize("operation", ["execute", "resume"])
def test_reused_workflow_engine_reloads_its_own_project(tmp_path, server, monkeypatch, operation):
    from specify_cli.workflows.engine import WorkflowDefinition, WorkflowEngine

    body = '''
    def build_exec_args(self, prompt, **kwargs):
        return ["sample-agent-process", prompt]
'''
    publish(server, code=implementation(body=body))
    project = catalog_project(tmp_path, server)
    install(project)
    first = WorkflowEngine(project)
    calls = []

    def process_double(argv, **kwargs):
        calls.append(kwargs["cwd"])
        failed = operation == "resume" and len(calls) == 1
        return SimpleNamespace(returncode=int(failed), stdout="sample response", stderr="sample failure" if failed else "")

    original_which = shutil.which
    monkeypatch.setattr(
        shutil, "which",
        lambda name, *args, **kwargs: "/sample-agent-process"
        if name == "sample-agent-process" else original_which(name, *args, **kwargs),
    )
    monkeypatch.setattr(subprocess, "run", process_double)
    source = project / "sample-workflow.yml"
    source.write_text(yaml.safe_dump({
        "schema_version": "1.0",
        "workflow": {"id": "sample-workflow", "name": "Sample Workflow", "version": "1.0.0"},
        "steps": [{"id": "sample-prompt", "type": "prompt", "integration": KEY, "prompt": "Sample prompt"}],
    }))
    definition = WorkflowDefinition.from_yaml(source)
    if operation == "resume":
        state = first.execute(definition)
        assert state.status.value == "failed"
    other = tmp_path / "other-project"
    other.mkdir()
    WorkflowEngine(other)
    load_installed_integrations(other)
    assert KEY not in INTEGRATION_REGISTRY
    result = first.resume(state.run_id) if operation == "resume" else first.execute(definition)
    assert result.status.value == "completed"
    assert calls[-1] == str(project)


def test_concurrent_package_registry_changes_are_not_overwritten(tmp_path, server, monkeypatch):
    from contextlib import contextmanager

    from specify_cli import shared_infra

    publish(server)
    project = catalog_project(tmp_path, server)
    install(project)
    original_files = snapshot(project)
    publish(server, version="2.0.0")
    original_lock = shared_infra._exclusive_project_lock

    @contextmanager
    def concurrent_update(root, *args, **kwargs):
        with original_lock(root, *args, **kwargs):
            path = project / ".specify/integrations/packages.json"
            records = json.loads(path.read_text())
            records["packages"][KEY]["catalog"] = "updated-source"
            path.write_text(json.dumps(records))
            yield

    monkeypatch.setattr(shared_infra, "_exclusive_project_lock", concurrent_update)
    result = run(project, ["integration", "upgrade", KEY, "--trust-integration"])
    assert result.exit_code == 1 and "state changed" in result.output
    assert read_records(project)[KEY]["catalog"] == "updated-source"
    assert read_records(project)[KEY]["version"] == "1.0.0"
    current_files = snapshot(project)
    registry = ".specify/integrations/packages.json"
    assert {key: value for key, value in current_files.items() if key != registry} == {
        key: value for key, value in original_files.items() if key != registry
    }


@pytest.mark.parametrize("arguments", [["integration", "list"], ["check"]])
def test_package_load_diagnostics_cannot_inject_console_markup(tmp_path, server, arguments):
    publish(server)
    project = catalog_project(tmp_path, server)
    install(project)
    registry = project / ".specify/integrations/packages.json"
    data = json.loads(registry.read_text())
    data["packages"]["[/sample]"] = data["packages"].pop(KEY)
    registry.write_text(json.dumps(data))
    result = run(project, arguments)
    assert result.exit_code == 1
    assert "Invalid integration ID" in result.output and "[/sample]" in result.output


def test_rollback_never_follows_a_replaced_metadata_symlink(tmp_path, server, monkeypatch):
    from specify_cli.integrations import _lifecycle

    outside = tmp_path / "outside"
    outside.mkdir()
    marker = outside / "preserved.txt"
    marker.write_text("Outside data")
    body = f'''
    def setup(self, project_root, manifest, **kwargs):
        import shutil
        super().setup(project_root, manifest, **kwargs)
        metadata = project_root / ".specify"
        shutil.rmtree(metadata)
        metadata.symlink_to({str(outside)!r}, target_is_directory=True)
        raise RuntimeError("sample setup failed")
'''
    publish(server, code=implementation(body=body))
    project = catalog_project(tmp_path, server)
    original_mkdtemp = _lifecycle.tempfile.mkdtemp
    backups = []

    def record_backup(*args, **kwargs):
        path = original_mkdtemp(*args, **kwargs)
        if kwargs.get("prefix") == "speckit-integration-rollback-":
            backups.append(Path(path))
        return path

    monkeypatch.setattr(_lifecycle.tempfile, "mkdtemp", record_backup)
    result = run(project, ["integration", "install", KEY, "--trust-integration"])
    assert result.exit_code == 1
    assert marker.read_text() == "Outside data"
    assert list(outside.iterdir()) == [marker]
    assert "Recovery snapshots retained" in " ".join(result.output.split()), result.output
    assert len(backups) == 1 and backups[0].is_dir()
    shutil.rmtree(backups[0])


def test_cancelled_init_does_not_persist_a_prepared_adapter(tmp_path, server):
    publish(server)
    project = catalog_project(tmp_path, server)
    before = snapshot(project)
    result = run(project, [
        "init", "--here", "--ignore-agent-tools", "--integration", KEY,
        "--trust-integration", "--script", "py",
    ], input="n\n")
    assert result.exit_code == 0, result.output
    assert snapshot(project) == before
    assert read_records(project) == {}
    assert KEY not in INTEGRATION_REGISTRY
    assert "Project ready" not in result.output


@pytest.mark.parametrize("field", ["version", "download_url", "requires"])
def test_incomplete_package_metadata_is_an_explicit_cli_failure(tmp_path, server, field):
    publish(server)
    project = catalog_project(tmp_path, server)
    install(project)
    path = project / ".specify/integrations/packages.json"
    data = json.loads(path.read_text())
    del data["packages"][KEY][field]
    path.write_text(json.dumps(data))
    result = run(project, ["integration", "info", KEY])
    assert result.exit_code == 1
    assert "invalid package metadata" in result.output and field in result.output
    assert KEY not in INTEGRATION_REGISTRY


@pytest.mark.parametrize("arguments", [
    ["integration", "catalog", "list"],
    ["workflow", "step", "catalog", "list"],
    ["preset", "catalog", "list"],
    ["integration", "list", "--catalog"],
    ["integration", "info", KEY],
])
def test_metadata_commands_never_import_an_installed_adapter(tmp_path, server, arguments):
    marker = tmp_path / "imported"
    code = implementation() + f"\nfrom pathlib import Path\nPath({str(marker)!r}).write_text('imported')\n"
    publish(server, code=code)
    project = catalog_project(tmp_path, server)
    install(project)
    marker.unlink()
    executable = Path(sys.executable).parent / ("specify.exe" if os.name == "nt" else "specify")
    result = subprocess.run(
        [str(executable), *arguments], cwd=project,
        capture_output=True, text=True, encoding="utf-8", timeout=30, check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert not marker.exists()


@pytest.mark.parametrize("operation", ["upgrade", "uninstall"])
@pytest.mark.parametrize("damage", ["modified", "missing", "missing-directory", "incompatible", "import-failure"])
def test_force_recovery_does_not_require_a_loadable_old_adapter(tmp_path, server, operation, damage):
    publish(server)
    project = catalog_project(tmp_path, server)
    install(project)
    path = project / f".specify/integrations/packages/{KEY}/__init__.py"
    if damage == "missing-directory":
        shutil.rmtree(path.parent)
    elif damage == "missing":
        path.unlink()
    elif damage == "modified":
        path.write_text("raise RuntimeError('modified code must not execute')")
    else:
        registry = project / ".specify/integrations/packages.json"
        records = json.loads(registry.read_text())
        if damage == "import-failure":
            path.write_text(implementation() + "\nraise RuntimeError('sample import failure')\n")
            records["packages"][KEY]["files"]["__init__.py"] = hashlib.sha256(path.read_bytes()).hexdigest()
        else:
            descriptor_path = path.parent / "integration.yml"
            data = yaml.safe_load(descriptor_path.read_text())
            data["requires"]["speckit_version"] = ">=999"
            descriptor_path.write_text(yaml.safe_dump(data))
            records["packages"][KEY]["requires"] = data["requires"]
            records["packages"][KEY]["files"]["integration.yml"] = hashlib.sha256(descriptor_path.read_bytes()).hexdigest()
        registry.write_text(json.dumps(records))
    result = run(project, ["integration", "catalog", "list"])
    assert result.exit_code == 0, result.output
    strict = run(project, ["integration", operation, KEY])
    assert strict.exit_code == 1
    arguments = ["integration", operation, KEY, "--force"]
    if operation == "upgrade":
        publish(server, version="2.0.0")
        arguments.append("--trust-integration")
    result = run(project, arguments)
    assert result.exit_code == 0, result.output
    assert "without loading its failed implementation" in " ".join(result.output.split())
    if operation == "upgrade":
        assert read_records(project)[KEY]["version"] == "2.0.0"
        assert (project / ".sample-agent/skills/speckit-plan/SKILL.md").is_file()
    else:
        assert KEY not in read_records(project)
        assert not path.parent.exists()


@pytest.mark.parametrize("relative", [
    ".git.", ".specify ", ".. ", "con", "NUL.txt", "folder/LPT1.log",
    " leading", "trailing.", "bad*name", "bad?name", "bad|name",
    'bad"name', "bad<name", "bad>name", "bad\x1fname", "a" * 256,
])
def test_review_portable_paths_rejected_before_filesystem_access(tmp_path, relative):
    from specify_cli.integrations.installer import safe_project_path

    with pytest.raises(IntegrationInstallError):
        safe_project_path(tmp_path, relative)


@pytest.mark.parametrize("folder", [".git.", ".. ", "con", ".sample-agent/NUL.txt"])
def test_review_portable_output_paths_rejected_without_project_changes(tmp_path, server, folder):
    publish(server, code=implementation(folder=folder))
    project = catalog_project(tmp_path, server)
    before = snapshot(project)
    result = run(project, ["integration", "install", KEY, "--trust-integration"])
    assert result.exit_code == 1, result.output
    assert snapshot(project) == before
    assert folder not in {child.name for child in project.iterdir()}


def test_review_cloned_project_cannot_transfer_execution_consent(tmp_path, server):
    marker = tmp_path / "imported"
    publish(server, code=implementation() + f"\nfrom pathlib import Path\nPath({str(marker)!r}).touch()\n")
    project = catalog_project(tmp_path, server)
    install(project)
    marker.unlink()
    clone = tmp_path / "clone"
    shutil.copytree(project, clone)
    registry = clone / ".specify/integrations/packages.json"
    data = json.loads(registry.read_text())
    data["packages"][KEY]["trusted"] = True
    registry.write_text(json.dumps(data))
    result = run(clone, ["integration", "list"])
    assert result.exit_code == 1, result.output
    assert "local trust" in result.output.lower()
    assert not marker.exists()
    assert KEY not in INTEGRATION_REGISTRY
    recovered = run(clone, ["integration", "upgrade", KEY, "--force", "--trust-integration"])
    assert recovered.exit_code == 0, recovered.output
    assert marker.exists()


def test_review_local_consent_checked_before_cached_registration(tmp_path, server, monkeypatch):
    publish(server)
    project = catalog_project(tmp_path, server)
    install(project)
    assert load_installed_integrations(project) == [KEY]
    other_home = tmp_path / "other-home"
    other_home.mkdir()
    monkeypatch.setenv("HOME", str(other_home))
    monkeypatch.setenv("USERPROFILE", str(other_home))
    result = run(project, ["integration", "list"])
    assert result.exit_code == 1, result.output
    assert "local trust" in result.output.lower()
    assert KEY not in INTEGRATION_REGISTRY


def test_review_consent_is_bound_to_verified_package_digest(tmp_path, server):
    publish(server)
    project = catalog_project(tmp_path, server)
    install(project)
    marker = tmp_path / "changed-import"
    code = project / f".specify/integrations/packages/{KEY}/__init__.py"
    code.write_text(implementation() + f"\nfrom pathlib import Path\nPath({str(marker)!r}).touch()\n")
    registry = project / ".specify/integrations/packages.json"
    data = json.loads(registry.read_text())
    data["packages"][KEY]["files"]["__init__.py"] = hashlib.sha256(code.read_bytes()).hexdigest()
    registry.write_text(json.dumps(data))
    result = run(project, ["integration", "list"])
    assert result.exit_code == 1, result.output
    assert "local trust" in result.output.lower()
    assert not marker.exists()


@pytest.mark.parametrize("command", ["list", "info", "lookup"])
@pytest.mark.parametrize("contribution", ["extension", "preset"])
def test_review_artifact_fresh_process_loads_adapter_and_preserves_json_errors(
    tmp_path, server, command, contribution,
):
    from specify_cli.artifacts import ArtifactCatalog

    marker = tmp_path / "artifact-import"
    publish(server, code=implementation() + f"\nfrom pathlib import Path\nPath({str(marker)!r}).touch()\n")
    project = catalog_project(tmp_path, server)
    install(project)
    if contribution == "extension":
        added = run(project, ["extension", "add", "--dev", str(Path.cwd() / "extensions/git")])
        source = ".sample-agent/skills/speckit-git-commit/SKILL.md"
    else:
        preset = tmp_path / "sample-preset"
        (preset / "commands").mkdir(parents=True)
        (preset / "commands/speckit.specify.md").write_text(
            "---\ndescription: Sample preset command\n---\nSample preset guidance\n"
        )
        (preset / "preset.yml").write_text(yaml.safe_dump({
            "schema_version": "1.0",
            "preset": {
                "id": "sample-preset", "name": "Sample Preset",
                "version": "1.0.0", "description": "Sample guidance",
            },
            "requires": {"speckit_version": ">=0.1"},
            "provides": {"templates": [{
                "type": "command", "name": "speckit.specify", "file": "commands/speckit.specify.md",
            }]},
        }))
        added = run(project, ["preset", "add", "--dev", str(preset)])
        source = ".sample-agent/skills/speckit-specify/SKILL.md"
    assert added.exit_code == 0, added.output
    rows = ArtifactCatalog(project).list_artifacts_with_stack()
    row = next(row for row in rows if any(layer["sourcePath"] == source for layer in row["stack"]))
    layer = next(layer for layer in row["stack"] if layer["sourcePath"] == source)
    arguments = ["artifact", command]
    if command != "list":
        arguments.append(row["id"] if command == "info" else layer["lookupId"])
    arguments.append("--json")
    marker.unlink()
    executable = Path(sys.executable).parent / ("specify.exe" if os.name == "nt" else "specify")
    result = subprocess.run(
        [str(executable), *arguments], cwd=project,
        capture_output=True, text=True, encoding="utf-8", timeout=30, check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    assert marker.exists()
    if command in {"list", "info"}:
        payload_rows = payload if command == "list" else [payload]
        assert any(layer["sourcePath"] == source for row in payload_rows for layer in row["stack"])
    marker.unlink()
    package = project / f".specify/integrations/packages/{KEY}/__init__.py"
    package.write_text("raise RuntimeError('damaged adapter must not execute')")
    failed = subprocess.run(
        [str(executable), *arguments], cwd=project,
        capture_output=True, text=True, encoding="utf-8", timeout=30, check=False,
    )
    assert failed.returncode == 1
    assert failed.stdout == ""
    failure = json.loads(failed.stderr)
    assert set(failure) == {"error"}
    if command == "list":
        assert failure["error"] in {
            "artifact resolution failed",
            f"artifact resolution failed: Integration '{KEY}' installed package has been modified",
        }
    else:
        assert "modified" in failure["error"]
    assert not marker.exists()


@pytest.mark.parametrize("original", ["absent", "empty", "nonempty"])
def test_review_failed_init_removes_only_new_scaffolding(tmp_path, server, monkeypatch, original):
    publish(server, code=implementation(body="    def setup(self, *args, **kwargs):\n        raise RuntimeError('sample setup failure')\n"))
    monkeypatch.setenv("SPECKIT_INTEGRATION_CATALOG_URL", f"{server.url}/catalog.json")
    project = tmp_path / "target"
    if original != "absent":
        project.mkdir()
    if original == "nonempty":
        (project / "notes.txt").write_text("preserve")
    before = snapshot(project)
    result = run(tmp_path, [
        "init", str(project), "--force", "--ignore-agent-tools",
        "--integration", KEY, "--trust-integration", "--script", "py",
    ])
    assert result.exit_code == 1, result.output
    assert snapshot(project) == before
    assert project.exists() == (original != "absent")
    assert not (project / ".specify").exists()


def test_review_cancelled_init_leaves_existing_uninitialized_directory_unchanged(tmp_path, server, monkeypatch):
    publish(server)
    monkeypatch.setenv("SPECKIT_INTEGRATION_CATALOG_URL", f"{server.url}/catalog.json")
    project = tmp_path / "target"
    project.mkdir()
    notes = project / "notes.txt"
    notes.write_text("preserve")
    result = run(project, [
        "init", "--here", "--ignore-agent-tools", "--integration", KEY,
        "--trust-integration", "--script", "py",
    ], input="n\n")
    assert result.exit_code == 0, result.output
    assert list(project.iterdir()) == [notes]
    assert notes.read_text() == "preserve"


@pytest.mark.parametrize("change", ["revoked", "invalid", "inside-project", "symlink"])
def test_review_local_trust_store_cannot_be_bypassed(tmp_path, server, monkeypatch, change):
    publish(server)
    project = catalog_project(tmp_path, server)
    install(project)
    trust = Path.home() / ".specify/integration-trust.json"
    if os.name != "nt":
        assert stat.S_IMODE(trust.stat().st_mode) == 0o600
    if change == "revoked":
        trust.unlink()
    elif change == "invalid":
        trust.write_text('{"schema_version":"1.0","grants":[true]}')
    elif change == "inside-project":
        monkeypatch.setenv("HOME", str(project))
        monkeypatch.setenv("USERPROFILE", str(project))
    else:
        target = tmp_path / "copied-trust.json"
        shutil.copyfile(trust, target)
        trust.unlink()
        try:
            trust.symlink_to(target)
        except OSError as exc:
            pytest.skip(f"Symlinks unavailable: {exc}")
    result = run(project, ["integration", "list"])
    assert result.exit_code == 1, result.output
    assert "trust" in result.output.lower()
    assert KEY not in INTEGRATION_REGISTRY


def test_review_package_removal_does_not_suppress_permission_errors(tmp_path, server, monkeypatch):
    from specify_cli.integrations import installer

    publish(server)
    project = catalog_project(tmp_path, server)
    install(project)
    package = project / f".specify/integrations/packages/{KEY}"
    before = snapshot(project)
    original = installer.shutil.rmtree

    def deny_package_removal(path, *args, **kwargs):
        if Path(path) == package:
            raise PermissionError("sample package removal denied")
        return original(path, *args, **kwargs)

    monkeypatch.setattr(installer.shutil, "rmtree", deny_package_removal)
    result = run(project, ["integration", "uninstall", KEY, "--force"])
    assert result.exit_code == 1, result.output
    assert "sample package removal denied" in result.output
    assert snapshot(project) == before


def test_review_failed_init_preserves_new_unowned_scaffolding_content(tmp_path, server, monkeypatch):
    project = tmp_path / "target"
    notes = project / ".specify/user-notes.txt"
    body = f"""    def setup(self, *args, **kwargs):
        from pathlib import Path
        notes = Path({str(notes)!r})
        notes.parent.mkdir(parents=True, exist_ok=True)
        notes.write_text("independent progress")
        raise RuntimeError("sample setup failure")
"""
    publish(server, code=implementation(body=body))
    monkeypatch.setenv("SPECKIT_INTEGRATION_CATALOG_URL", f"{server.url}/catalog.json")
    result = run(tmp_path, [
        "init", str(project), "--ignore-agent-tools", "--integration", KEY,
        "--trust-integration", "--script", "py",
    ])
    assert result.exit_code == 1, result.output
    assert notes.read_text() == "independent progress"
    assert read_records(project) == {}


@pytest.mark.parametrize("writer", ["render", "copy", "script"])
def test_round2_leaf_symlink_never_redirects_transaction_writes(tmp_path, server, writer):
    outside = tmp_path / "outside.txt"
    outside.write_text("preserve outside data")
    if writer == "copy":
        source = tmp_path / "source.md"
        source.write_text("copied command")
        body = f"""    def setup(self, project_root, manifest, **kwargs):
        from pathlib import Path
        self.copy_command_to_directory(
            Path({str(source)!r}), project_root / ".sample-agent/skills", "SKILL.md"
        )
        return []
"""
        relative = ".sample-agent/skills/SKILL.md"
    elif writer == "script":
        body = """    def setup(self, project_root, manifest, **kwargs):
        return self.install_scripts(project_root, manifest)
"""
        relative = f".specify/integrations/{KEY}/scripts/sample.py"
    else:
        body = ""
        relative = ".sample-agent/skills/speckit-plan/SKILL.md"
    publish(
        server, code=implementation(body=body),
        members={"scripts/sample.py": b"print('sample')"} if writer == "script" else None,
    )
    project = catalog_project(tmp_path, server)
    leaf = project / relative
    leaf.parent.mkdir(parents=True)
    try:
        leaf.symlink_to(outside)
    except OSError as exc:
        pytest.skip(f"Symlinks unavailable: {exc}")
    before = snapshot(project)
    result = run(project, ["integration", "install", KEY, "--trust-integration", "--script", "py"])
    assert result.exit_code == 1, result.output
    assert "symlink" in result.output.lower(), result.output
    assert outside.read_text() == "preserve outside data"
    assert leaf.is_symlink()
    assert snapshot(project) == before


def test_round2_script_helper_installs_and_records_regular_files(tmp_path, server):
    body = """    def setup(self, project_root, manifest, **kwargs):
        return self.install_scripts(project_root, manifest)
"""
    publish(
        server, code=implementation(body=body),
        members={"scripts/sample.py": b"print('sample')"},
    )
    project = catalog_project(tmp_path, server)
    install(project)
    relative = f".specify/integrations/{KEY}/scripts/sample.py"
    assert (project / relative).read_bytes() == b"print('sample')"
    manifest = json.loads((project / f".specify/integrations/{KEY}.manifest.json").read_text())
    assert relative in manifest["files"]


def test_round2_forced_removal_unlinks_owned_leaf_without_following_it(tmp_path, server):
    publish(server)
    project = catalog_project(tmp_path, server)
    install(project)
    outside = tmp_path / "outside.txt"
    outside.write_text("preserve outside data")
    leaf = project / ".sample-agent/skills/speckit-plan/SKILL.md"
    leaf.unlink()
    try:
        leaf.symlink_to(outside)
    except OSError as exc:
        pytest.skip(f"Symlinks unavailable: {exc}")
    result = run(project, ["integration", "uninstall", KEY, "--force"])
    assert result.exit_code == 0, result.output
    assert not leaf.is_symlink()
    assert outside.read_text() == "preserve outside data"


def test_round2_snapshot_preserves_standalone_leaf_link_without_traversal(tmp_path, server, monkeypatch):
    body = """    def setup(self, project_root, manifest, **kwargs):
        self.write_file_and_record(
            "managed notes", project_root / "sample-notes.md", project_root, manifest
        )
        return []
"""
    publish(server, code=implementation(body=body))
    project = catalog_project(tmp_path, server)
    install(project)
    outside = tmp_path / "outside"
    outside.mkdir()
    marker = outside / "user-notes.md"
    marker.write_text("preserve outside directory")
    leaf = project / "sample-notes.md"
    leaf.unlink()
    try:
        leaf.symlink_to(outside, target_is_directory=True)
    except OSError as exc:
        pytest.skip(f"Symlinks unavailable: {exc}")
    original = shutil.copytree

    def reject_root_link_traversal(source, *args, **kwargs):
        assert not Path(source).is_symlink(), "snapshot followed a leaf link"
        return original(source, *args, **kwargs)

    monkeypatch.setattr(shutil, "copytree", reject_root_link_traversal)
    result = run(project, ["integration", "uninstall", KEY, "--force"])
    assert result.exit_code == 0, result.output
    assert not leaf.is_symlink()
    assert marker.read_text() == "preserve outside directory"


@pytest.mark.parametrize("metadata", ["other-root", "unrelated-root", "manifest-path"])
def test_round2_recovery_rejects_unverified_ownership_before_deleting_files(tmp_path, server, metadata):
    publish(server)
    project = catalog_project(tmp_path, server)
    assert run(project, ["integration", "install", "claude"]).exit_code == 0
    install(project)
    marker = project / ".claude/skills/user-notes.md"
    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.write_text("preserve another integration")
    (project / f".specify/integrations/packages/{KEY}/__init__.py").unlink()
    if metadata == "manifest-path":
        path = project / f".specify/integrations/{KEY}.manifest.json"
        data = json.loads(path.read_text())
        data["files"][marker.relative_to(project).as_posix()] = hashlib.sha256(marker.read_bytes()).hexdigest()
    else:
        path = project / ".specify/integrations/packages.json"
        data = json.loads(path.read_text())
        data["packages"][KEY]["registrar_config"]["dir"] = (
            ".claude/skills" if metadata == "other-root" else "user-files"
        )
    path.write_text(json.dumps(data))
    before = snapshot(project)
    result = run(project, ["integration", "uninstall", KEY, "--force"])
    assert result.exit_code == 1, result.output
    assert "ownership" in result.output.lower() or "overlap" in result.output.lower()
    assert snapshot(project) == before
    assert marker.read_text() == "preserve another integration"


@pytest.mark.parametrize("proof", ["copied-project", "legacy-grant"])
@pytest.mark.parametrize("operation", ["upgrade", "uninstall"])
def test_round2_recovery_without_local_ownership_preserves_old_outputs(tmp_path, server, proof, operation):
    publish(server)
    project = catalog_project(tmp_path, server)
    install(project)
    if proof == "copied-project":
        clone = tmp_path / "copied-project"
        shutil.copytree(project, clone)
        project = clone
    else:
        path = Path.home() / ".specify/integration-trust.json"
        data = json.loads(path.read_text())
        del data["recovery"]
        path.write_text(json.dumps(data))
    marker = project / ".claude/skills/user-notes.md"
    marker.parent.mkdir(parents=True)
    marker.write_text("preserve unrelated data")
    manifest_path = project / f".specify/integrations/{KEY}.manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["files"][marker.relative_to(project).as_posix()] = hashlib.sha256(marker.read_bytes()).hexdigest()
    manifest_path.write_text(json.dumps(manifest))
    skill = project / ".sample-agent/skills/speckit-plan/SKILL.md"
    skill.write_text("preserve previous layout customization")
    (project / f".specify/integrations/packages/{KEY}/__init__.py").unlink()
    arguments = ["integration", operation, KEY, "--force"]
    if operation == "upgrade":
        publish(server, version="2.0.0", code=implementation(folder=".sample-new"))
        arguments.append("--trust-integration")
    result = run(project, arguments)
    assert result.exit_code == 0, result.output
    assert "No local recovery ownership record" in result.output
    assert marker.read_text() == "preserve unrelated data"
    assert skill.read_text() == "preserve previous layout customization"
    if operation == "upgrade":
        assert (project / ".sample-new/skills/speckit-plan/SKILL.md").is_file()
        assert read_records(project)[KEY]["version"] == "2.0.0"
    else:
        assert not (project / f".specify/integrations/packages/{KEY}").exists()


@pytest.mark.parametrize("directory", ["primary", "legacy"])
def test_round2_recovery_rejects_even_locally_recorded_overlap(tmp_path, server, directory):
    body = "    multi_install_safe = False\n"
    if directory == "legacy":
        body += '    registrar_config = {**registrar_config, "legacy_dir": ".claude/skills"}\n'
    publish(
        server, code=implementation(
            folder=".claude" if directory == "primary" else ".sample-agent", body=body,
        ),
    )
    project = catalog_project(tmp_path, server)
    install(project)
    marker = project / ".claude/skills/user-notes.md"
    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.write_text("preserve another integration")
    (project / f".specify/integrations/packages/{KEY}/__init__.py").unlink()
    before = snapshot(project)
    result = run(project, ["integration", "uninstall", KEY, "--force"])
    assert result.exit_code == 1, result.output
    assert "ownership overlaps 'claude'" in result.output
    assert snapshot(project) == before
    assert marker.read_text() == "preserve another integration"


def test_round2_failed_durable_upgrade_retains_previous_recovery_ownership(tmp_path, server, monkeypatch):
    from specify_cli.integrations import installer

    publish(server)
    project = catalog_project(tmp_path, server)
    install(project)
    path = Path.home() / ".specify/integration-trust.json"
    ownership = json.loads(path.read_text())["recovery"]
    before = snapshot(project)
    publish(server, version="2.0.0", code=implementation(folder=".sample-new"))
    original = installer._import_package

    def fail_durable_update(package, metadata, hashes, root):
        if metadata.version == "2.0.0" and project in package.parents:
            raise IntegrationInstallError("sample durable import failed")
        return original(package, metadata, hashes, root)

    monkeypatch.setattr(installer, "_import_package", fail_durable_update)
    result = run(project, ["integration", "upgrade", KEY, "--force", "--trust-integration"])
    assert result.exit_code == 1, result.output
    assert "sample durable import failed" in result.output
    assert snapshot(project) == before
    assert json.loads(path.read_text())["recovery"] == ownership
    (project / f".specify/integrations/packages/{KEY}/__init__.py").unlink()
    removed = run(project, ["integration", "uninstall", KEY, "--force"])
    assert removed.exit_code == 0, removed.output


@pytest.mark.parametrize("operation", ["run", "resume"])
def test_round2_workflow_reload_oserror_uses_single_json_envelope(tmp_path, server, monkeypatch, operation):
    from specify_cli.integrations import installer
    from specify_cli.workflows.base import RunStatus
    from specify_cli.workflows.engine import RunState

    publish(server)
    project = catalog_project(tmp_path, server)
    install(project)
    source = project / "sample-workflow.yml"
    source.write_text(yaml.safe_dump({
        "schema_version": "1.0",
        "workflow": {"id": "sample-workflow", "name": "Sample Workflow", "version": "1.0.0"},
        "steps": [{"id": "sample-shell", "type": "shell", "run": "echo sample"}],
    }))
    state = RunState(
        run_id="sample-run", workflow_id="sample-workflow", project_root=project,
    )
    state.status = RunStatus.PAUSED
    state.save()
    (project / ".specify/workflows/runs/sample-run/workflow.yml").write_bytes(source.read_bytes())
    original = installer.package_hashes
    calls = 0

    def fail_second_load(package):
        nonlocal calls
        calls += 1
        if calls >= 2:
            raise PermissionError("sample package read denied")
        return original(package)

    monkeypatch.setattr(installer, "package_hashes", fail_second_load)
    result = run(project, [
        "workflow", operation, str(source) if operation == "run" else "sample-run", "--json",
    ])
    assert result.exit_code == 1, result.output
    payload = json.loads(result.stdout)
    assert payload["status"] == "failed"
    assert "sample package read denied" in payload["error"]
    assert result.stderr == ""


def test_round2_concurrent_load_waits_for_its_requested_project(tmp_path, server, monkeypatch):
    from concurrent.futures import ThreadPoolExecutor, TimeoutError

    from specify_cli.integrations import installer

    publish(server, code=implementation(folder=".sample-first"))
    first = catalog_project(tmp_path, server)
    install(first)
    publish(server, version="2.0.0", code=implementation(folder=".sample-second"))
    second = catalog_project(tmp_path / "second", server)
    install(second)
    unload_installed_integrations()
    entered = threading.Event()
    release = threading.Event()
    original = installer.package_hashes

    def slow_first_load(package):
        if first in package.parents:
            entered.set()
            assert release.wait(10)
        return original(package)

    monkeypatch.setattr(installer, "package_hashes", slow_first_load)
    with ThreadPoolExecutor(max_workers=2) as pool:
        a = pool.submit(load_installed_integrations, first)
        assert entered.wait(10)
        b = pool.submit(load_installed_integrations, second)
        try:
            with pytest.raises(TimeoutError):
                b.result(timeout=0.1)
        finally:
            release.set()
        assert a.result(timeout=10) == [KEY]
        assert b.result(timeout=10) == [KEY]
    assert INTEGRATION_REGISTRY[KEY].config["folder"] == ".sample-second"


@pytest.mark.parametrize("kind", ["prompt", "command"])
def test_round2_workflow_dispatch_keeps_project_adapter_after_registry_switch(tmp_path, server, monkeypatch, kind):
    from specify_cli.workflows.engine import WorkflowDefinition, WorkflowEngine

    body = '''
    def build_exec_args(self, prompt, **kwargs):
        return ["sample-agent-process", self.config["folder"], prompt]
'''
    publish(server, code=implementation(folder=".sample-first", body=body))
    first = catalog_project(tmp_path, server)
    install(first)
    publish(server, version="2.0.0", code=implementation(folder=".sample-second", body=body))
    second = catalog_project(tmp_path / "second", server)
    install(second)
    engine = WorkflowEngine(first)
    engine.on_step_start = lambda *args: load_installed_integrations(second)
    calls = []
    original_which = shutil.which
    monkeypatch.setattr(shutil, "which", lambda name: "/sample-agent-process" if name == "sample-agent-process" else original_which(name))

    def harmless_process(argv, **kwargs):
        calls.append(argv)
        return SimpleNamespace(returncode=0, stdout="sample response", stderr="")

    monkeypatch.setattr(subprocess, "run", harmless_process)
    step = {"id": "sample-dispatch", "type": kind, "integration": KEY}
    step["prompt" if kind == "prompt" else "command"] = "Sample prompt" if kind == "prompt" else "speckit.plan"
    source = first / "sample-workflow.yml"
    source.write_text(yaml.safe_dump({
        "schema_version": "1.0",
        "workflow": {"id": "sample-workflow", "name": "Sample Workflow", "version": "1.0.0"},
        "steps": [step],
    }))
    result = engine.execute(WorkflowDefinition.from_yaml(source))
    assert result.status.value == "completed", result.steps
    assert calls and all(argv[1] == ".sample-first" for argv in calls)


@pytest.mark.parametrize("kind", ["prompt", "command"])
@pytest.mark.parametrize("process_fails", [False, True])
def test_round2_overlapping_dispatch_pins_lazy_imports_and_project_lookup(
    tmp_path, server, monkeypatch, kind, process_fails,
):
    from concurrent.futures import ThreadPoolExecutor

    from specify_cli.integrations import installer
    from specify_cli.workflows.engine import WorkflowDefinition, WorkflowEngine

    body = '''
    def build_exec_args(self, prompt, **kwargs):
        from .helper import marker
        from specify_cli.integrations import get_integration
        assert get_integration(self.key) is self
        return ["sample-agent-process", marker, prompt]
'''
    publish(
        server, code=implementation(folder=".sample-first", body=body),
        members={"helper.py": b"marker = '.sample-first'"},
    )
    first = catalog_project(tmp_path, server)
    install(first)
    publish(
        server, version="2.0.0", code=implementation(folder=".sample-second", body=body),
        members={"helper.py": b"marker = '.sample-second'"},
    )
    second = catalog_project(tmp_path / "second", server)
    install(second)
    engines = [WorkflowEngine(root) for root in (first, second)]
    definitions = []
    for root in (first, second):
        step = {"id": "sample-dispatch", "type": kind, "integration": KEY}
        step["prompt" if kind == "prompt" else "command"] = (
            "Sample prompt" if kind == "prompt" else "speckit.plan"
        )
        source = root / "sample-workflow.yml"
        source.write_text(yaml.safe_dump({
            "schema_version": "1.0",
            "workflow": {"id": "sample-workflow", "name": "Sample Workflow", "version": "1.0.0"},
            "steps": [step],
        }))
        definitions.append(WorkflowDefinition.from_yaml(source))
    barrier = threading.Barrier(2)
    original = installer._VerifiedSourceLoader.get_code

    def overlap_lazy_import(loader, fullname):
        if fullname.endswith(".helper"):
            barrier.wait(timeout=10)
        return original(loader, fullname)

    monkeypatch.setattr(installer._VerifiedSourceLoader, "get_code", overlap_lazy_import)
    original_which = shutil.which
    monkeypatch.setattr(
        shutil, "which",
        lambda name: "/sample-agent-process" if name == "sample-agent-process" else original_which(name),
    )
    calls = []

    def harmless_process(argv, **kwargs):
        calls.append((argv[1], Path(kwargs["cwd"])))
        return SimpleNamespace(
            returncode=1 if process_fails else 0, stdout="sample response", stderr="sample failure",
        )

    monkeypatch.setattr(subprocess, "run", harmless_process)
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [
            pool.submit(engine.execute, definition)
            for engine, definition in zip(engines, definitions, strict=True)
        ]
        results = [future.result(timeout=20) for future in futures]
    assert all(result.status.value == ("failed" if process_fails else "completed") for result in results)
    assert set(calls) == {(".sample-first", first), (".sample-second", second)}
    assert not installer._pinned_names
    retained = {installer._namespace(value) for value in INTEGRATION_REGISTRY.values()}
    assert set(installer._source_packages) <= retained
    unload_installed_integrations()
    assert not installer._source_packages
    assert not any(name.startswith(installer._MODULE_PREFIX) for name in sys.modules)


@pytest.mark.parametrize("legacy", [
    "../outside", "/outside", ".sample/../outside", ".git/hooks", ".SPECIFY/scripts",
    "", None, 42, False, [],
])
def test_round3_invalid_legacy_destination_is_rejected_before_setup(tmp_path, server, legacy):
    marker = tmp_path / "setup-ran"
    body = f'''    registrar_config = {{**registrar_config, "legacy_dir": {legacy!r}}}
    def setup(self, project_root, manifest, **kwargs):
        from pathlib import Path
        Path({str(marker)!r}).touch()
        return []
'''
    publish(server, code=implementation(body=body))
    project = catalog_project(tmp_path, server)
    before = snapshot(project)
    result = run(project, ["integration", "install", KEY, "--trust-integration"])
    assert result.exit_code == 1, result.output
    assert not marker.exists()
    assert snapshot(project) == before


def test_round3_valid_legacy_destination_remains_supported(tmp_path, server):
    body = '    registrar_config = {**registrar_config, "legacy_dir": ".sample-previous/skills"}\n'
    publish(server, code=implementation(body=body))
    project = catalog_project(tmp_path, server)
    install(project)
    assert CommandRegistrar(project).AGENT_CONFIGS[KEY]["legacy_dir"] == ".sample-previous/skills"
    assert (project / ".sample-agent/skills/speckit-plan/SKILL.md").is_file()


@pytest.mark.parametrize("directory", ["primary", "legacy"])
def test_round3_home_relative_output_cannot_escape_project_contract(tmp_path, server, directory):
    body = (
        '    registrar_config = {**registrar_config, "legacy_dir": "~/.sample-previous/skills"}\n'
        if directory == "legacy" else ""
    )
    publish(server, code=implementation(
        folder="~/.sample-agent" if directory == "primary" else ".sample-agent", body=body,
    ))
    project = catalog_project(tmp_path, server)
    before = snapshot(project)
    result = run(project, ["integration", "install", KEY, "--trust-integration"])
    assert result.exit_code == 1, result.output
    assert "project-local" in result.output
    assert snapshot(project) == before


@pytest.mark.parametrize("directory", ["primary", "legacy"])
@pytest.mark.parametrize("alias", [".CLAUDE", ".CLAUDE/nested", ".KILOCODE"])
def test_round3_multi_install_overlap_uses_portable_casefolded_paths(tmp_path, server, directory, alias):
    body = (
        f'    registrar_config = {{**registrar_config, "legacy_dir": {alias!r}}}\n'
        if directory == "legacy" else ""
    )
    publish(server, code=implementation(
        folder=alias if directory == "primary" else ".sample-agent", body=body,
    ))
    project = catalog_project(tmp_path, server)
    before = snapshot(project)
    result = run(project, ["integration", "install", KEY, "--trust-integration"])
    assert result.exit_code == 1, result.output
    assert "overlap" in result.output.lower(), result.output
    assert snapshot(project) == before


@pytest.mark.parametrize("consumer", ["extension-candidates", "extension-remove", "preset"])
def test_round3_managers_snapshot_the_requested_project_atomically(tmp_path, server, monkeypatch, consumer):
    from specify_cli.extensions import ExtensionManager
    from specify_cli.presets import PresetManager

    publish(server, code=implementation(folder=".sample-first"))
    first = catalog_project(tmp_path, server)
    install(first)
    publish(server, version="2.0.0", code=implementation(folder=".sample-second"))
    second = catalog_project(tmp_path / "second", server)
    install(second)
    original = CommandRegistrar.__init__

    def switch_before_unscoped_snapshot(registrar, project_root=None, **kwargs):
        if project_root is None:
            load_installed_integrations(second)
        original(registrar, project_root, **kwargs)

    monkeypatch.setattr(CommandRegistrar, "__init__", switch_before_unscoped_snapshot)
    if consumer == "preset":
        registrar = PresetManager(first)._command_registrar()
        assert registrar.AGENT_CONFIGS[KEY]["dir"] == ".sample-first/skills"
    elif consumer == "extension-candidates":
        candidates = ExtensionManager(first)._extension_skill_candidate_dirs()
        assert first / ".sample-first/skills" in candidates
        assert first / ".sample-second/skills" not in candidates
    else:
        manager = ExtensionManager(first)
        manager.registry.add("sample-extension", {
            "version": "1.0.0", "registered_commands": {KEY: ["speckit.sample"]},
        })
        first_leaf = first / ".sample-first/skills/speckit-sample/SKILL.md"
        other_leaf = first / ".sample-second/skills/speckit-sample/SKILL.md"
        for leaf in (first_leaf, other_leaf):
            leaf.parent.mkdir(parents=True, exist_ok=True)
            leaf.write_text("preserve the correct project scope")
        assert manager.remove("sample-extension")
        assert not first_leaf.exists()
        assert other_leaf.read_text() == "preserve the correct project scope"


@pytest.mark.parametrize("operation", ["add", "remove", "enable", "disable"])
def test_round3_extension_event_refresh_loads_adapter_in_fresh_process(tmp_path, server, operation):
    from specify_cli.events import refresh_integration_events

    body = '''    CANONICAL_TO_NATIVE = {"session_start": "SampleStart"}
    events_config_file = ".sample-agent/events.json"
    events_format = "json-nested"
'''
    publish(server, code=implementation(body=body))
    project = catalog_project(tmp_path, server)
    install(project)
    extension = tmp_path / "sample-events"
    extension.mkdir()
    (extension / "extension.yml").write_text(yaml.safe_dump({
        "schema_version": "1.0",
        "extension": {
            "id": "sample-events", "name": "Sample Events", "version": "1.0.0",
            "description": "Sample event-only extension",
        },
        "requires": {"speckit_version": ">=0.1"},
        "provides": {"commands": []},
        "events": {"session_start": {"command": "speckit.sample.boot"}},
    }))
    config = project / ".sample-agent/events.json"
    if operation != "add":
        result = run(project, ["extension", "add", "--dev", str(extension)])
        assert result.exit_code == 0, result.output
        refresh_integration_events(project)
    if operation == "enable":
        result = run(project, ["extension", "disable", "sample-events"])
        assert result.exit_code == 0, result.output
        refresh_integration_events(project)
    arguments = (
        ["extension", "add", "--dev", str(extension)]
        if operation == "add" else ["extension", operation, "sample-events"]
    )
    if operation == "remove":
        arguments.append("--force")
    executable = Path(sys.executable).parent / ("specify.exe" if os.name == "nt" else "specify")
    result = subprocess.run(
        [str(executable), *arguments], cwd=project, capture_output=True,
        text=True, encoding="utf-8", timeout=30, check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    data = json.loads(config.read_text()) if config.exists() else {}
    hooks = data.get("hooks", {}).get("SampleStart", [])
    assert bool(hooks) == (operation in {"add", "enable"})


def test_round3_event_refresh_surfaces_failed_adapter_load(tmp_path, server):
    from specify_cli.events import EventRefreshError, refresh_integration_events

    publish(server)
    project = catalog_project(tmp_path, server)
    install(project)
    (project / f".specify/integrations/packages/{KEY}/__init__.py").write_text(
        "raise RuntimeError('sample adapter should not execute')"
    )
    with pytest.raises(EventRefreshError, match="sample-agent.*modified") as exc:
        refresh_integration_events(project)
    assert exc.value.failures[0][0] == "installed adapters"


@pytest.mark.parametrize("json_output", [False, True])
def test_round3_resume_disappearing_run_has_specific_missing_run_error(tmp_path, server, monkeypatch, json_output):
    from specify_cli.workflows.base import RunStatus
    from specify_cli.workflows.engine import RunState, WorkflowEngine

    publish(server)
    project = catalog_project(tmp_path, server)
    install(project)
    state = RunState(run_id="sample-run", workflow_id="sample-workflow", project_root=project)
    state.status = RunStatus.PAUSED
    state.installed_origin_tracked = True
    state.save()

    def disappear(engine, run_id, inputs):
        raise FileNotFoundError("sample state disappeared")

    monkeypatch.setattr(WorkflowEngine, "resume", disappear)
    result = run(project, ["workflow", "resume", "sample-run", *(["--json"] if json_output else [])])
    assert result.exit_code == 1, result.output
    if json_output:
        assert json.loads(result.stdout)["error"] == "Run not found: sample-run"
        assert result.stderr == ""
    else:
        assert "Run not found: sample-run" in result.stdout


def test_round3_resume_adapter_file_disappearance_is_not_a_missing_run(tmp_path, server, monkeypatch):
    from specify_cli.integrations import installer
    from specify_cli.workflows.base import RunStatus
    from specify_cli.workflows.engine import RunState

    publish(server)
    project = catalog_project(tmp_path, server)
    install(project)
    state = RunState(run_id="sample-run", workflow_id="sample-workflow", project_root=project)
    state.status = RunStatus.PAUSED
    state.installed_origin_tracked = True
    state.save()
    original = installer.package_hashes
    calls = 0

    def disappear_on_resume(package):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise FileNotFoundError("sample adapter source disappeared")
        return original(package)

    monkeypatch.setattr(installer, "package_hashes", disappear_on_resume)
    result = run(project, ["workflow", "resume", "sample-run", "--json"])
    assert result.exit_code == 1, result.output
    assert "sample adapter source disappeared" in json.loads(result.stdout)["error"]
    assert "Run not found" not in result.stdout
    assert result.stderr == ""


def test_failed_operation_preserves_independent_workflow_and_unowned_output_edits(tmp_path, server, monkeypatch):
    from specify_cli.integrations import installer
    from specify_cli.workflows.engine import RunState

    publish(server)
    project = catalog_project(tmp_path, server)
    install(project)
    user_file = project / ".sample-agent/skills/user-notes.md"
    user_file.write_text("before")
    workflow = RunState(run_id="sample-run", workflow_id="sample-workflow", project_root=project)
    workflow.save()
    publish(server, version="2.0.0")

    def fail_commit(*args, **kwargs):
        def independent_writer():
            user_file.write_text("independent user edit")
            workflow.current_step_index = 1
            workflow.save()
        thread = threading.Thread(target=independent_writer)
        thread.start()
        thread.join()
        raise OSError("sample commit failure")

    monkeypatch.setattr(installer, "write_records", fail_commit)
    result = run(project, ["integration", "upgrade", KEY, "--trust-integration"])
    assert result.exit_code == 1, result.output
    assert user_file.read_text() == "independent user edit"
    assert RunState.load("sample-run", project).current_step_index == 1
    assert read_records(project)[KEY]["version"] == "1.0.0"


def test_failed_operation_preserves_concurrent_edits_to_a_managed_file(tmp_path, server, monkeypatch):
    from specify_cli.integrations import _lifecycle, installer

    publish(server)
    project = catalog_project(tmp_path, server)
    install(project)
    path = project / ".sample-agent/skills/speckit-plan/SKILL.md"
    publish(server, version="2.0.0")
    original_mkdtemp = _lifecycle.tempfile.mkdtemp
    backups = []

    def record_backup(*args, **kwargs):
        directory = original_mkdtemp(*args, **kwargs)
        if kwargs.get("prefix") == "speckit-integration-rollback-":
            backups.append(Path(directory))
        return directory

    def fail_commit(*args, **kwargs):
        path.write_text("concurrent managed-file edit")
        raise OSError("sample commit failure")

    monkeypatch.setattr(_lifecycle.tempfile, "mkdtemp", record_backup)
    monkeypatch.setattr(installer, "write_records", fail_commit)
    result = run(project, ["integration", "upgrade", KEY, "--trust-integration"])
    assert result.exit_code == 1, result.output
    assert path.read_text() == "concurrent managed-file edit"
    assert "Preserved concurrent edits" in result.output
    assert len(backups) == 1
    shutil.rmtree(backups[0])


@pytest.mark.parametrize("script", ["sh", "ps", "py"])
def test_catalog_init_checks_required_tools_and_scaffolds_host_skills(tmp_path, server, monkeypatch, script):
    metadata = descriptor()
    metadata["requires"]["tools"] = [{"name": KEY, "required": True}]
    publish(server, metadata=metadata)
    project = catalog_project(tmp_path, server)
    before = snapshot(project)
    monkeypatch.setenv("PATH", str(tmp_path / "absent-tools"))
    arguments = [
        "init", "--here", "--force", "--ignore-agent-tools",
        "--integration", KEY, "--trust-integration", "--script", script,
    ]
    denied = run(project, arguments)
    assert denied.exit_code == 1 and "requires missing tool" in " ".join(denied.output.split())
    assert snapshot(project) == before
    tools = tmp_path / "tools"
    tools.mkdir()
    executable = tools / (KEY + ".exe" if os.name == "nt" else KEY)
    executable.write_text("scaffolding-only executable presence double")
    executable.chmod(0o755)
    monkeypatch.setenv("PATH", str(tools))
    result = run(project, arguments)
    assert result.exit_code == 0, result.output
    skill = project / ".sample-agent/skills/speckit-plan/SKILL.md"
    content = skill.read_text(encoding="utf-8")
    assert "{SCRIPT}" not in content and "__SPECKIT_COMMAND_" not in content
    assert yaml.safe_load(content.split("---", 2)[1])["name"] == "speckit-plan"
    assert (project / f".specify/scripts/{'python' if script == 'py' else 'bash' if script == 'sh' else 'powershell'}").is_dir()


@pytest.mark.parametrize("field,value", [
    ("dir", "../outside"), ("dir", ".specify/templates"),
    ("format", "unsupported"), ("args", None), ("extension", "/../outside"),
    ("invoke_separator", None), ("dev_no_symlink", "false"),
])
def test_force_recovery_validates_persisted_registration_metadata(tmp_path, server, field, value):
    publish(server)
    project = catalog_project(tmp_path, server)
    install(project)
    registry = project / ".specify/integrations/packages.json"
    data = json.loads(registry.read_text())
    data["packages"][KEY]["registrar_config"][field] = value
    registry.write_text(json.dumps(data))
    (project / f".specify/integrations/packages/{KEY}/__init__.py").write_text(
        "raise RuntimeError('modified code must not execute')"
    )
    before = snapshot(project)
    result = run(project, ["integration", "uninstall", KEY, "--force"])
    assert result.exit_code == 1, result.output
    assert snapshot(project) == before


def test_adapter_cannot_overwrite_a_concurrent_managed_edit_with_a_second_write(tmp_path, server, monkeypatch):
    from specify_cli.integrations import _lifecycle

    body = '''
    def setup(self, project_root, manifest, **kwargs):
        from threading import Thread
        created = super().setup(project_root, manifest, **kwargs)
        path = manifest.project_root / ".sample-agent/skills/speckit-plan/SKILL.md"
        thread = Thread(target=lambda: path.write_text("concurrent managed edit"))
        thread.start()
        thread.join()
        manifest.record_file(path.relative_to(manifest.project_root).as_posix(), "second adapter write")
        return created
'''
    publish(server, code=implementation(body=body))
    project = catalog_project(tmp_path, server)
    original = _lifecycle.tempfile.mkdtemp
    backups = []

    def record_backup(*args, **kwargs):
        directory = original(*args, **kwargs)
        if kwargs.get("prefix") == "speckit-integration-rollback-":
            backups.append(Path(directory))
        return directory

    monkeypatch.setattr(_lifecycle.tempfile, "mkdtemp", record_backup)
    try:
        result = run(project, ["integration", "install", KEY, "--trust-integration", "--script", "py"])
        assert result.exit_code == 1, result.output
        assert "refusing to overwrite" in " ".join(result.output.split())
        assert (project / ".sample-agent/skills/speckit-plan/SKILL.md").read_text() == "concurrent managed edit"
        assert KEY not in read_records(project)
    finally:
        for backup in backups:
            if backup.exists():
                shutil.rmtree(backup)


@pytest.mark.parametrize("operation", ["install", "switch"])
@pytest.mark.parametrize("existing", [False, True])
@pytest.mark.parametrize("change", ["concurrent", "deleted"])
def test_failed_setup_preserves_pending_tracked_changes(tmp_path, server, monkeypatch, operation, existing, change):
    from specify_cli.integrations import _lifecycle

    body = f'''    def setup(self, project_root, manifest, **kwargs):
        from threading import Thread
        from specify_cli.integrations._file_changes import changing_file
        path = manifest.record_file(".sample-agent/skills/sample-pending.md", "first completed write")
        with changing_file(path):
            writer = Thread(target=lambda: (
                path.write_text("concurrent edit") if {change!r} == "concurrent" else path.unlink()
            ))
            writer.start()
            writer.join()
            raise OSError("interrupted second write")
'''
    publish(server, code=implementation(body=body))
    project = catalog_project(tmp_path, server)
    if operation == "switch":
        assert run(project, ["integration", "install", "claude"]).exit_code == 0
    target = project / ".sample-agent/skills/sample-pending.md"
    target.parent.mkdir(parents=True)
    if existing:
        target.write_text("original bytes")
    backups = []
    original_mkdtemp = _lifecycle.tempfile.mkdtemp

    def record_backup(*args, **kwargs):
        directory = original_mkdtemp(*args, **kwargs)
        if kwargs.get("prefix") == "speckit-integration-rollback-":
            backups.append(Path(directory))
        return directory

    monkeypatch.setattr(_lifecycle.tempfile, "mkdtemp", record_backup)
    conflict = change == "concurrent" or existing
    try:
        result = run(project, ["integration", operation, KEY, "--trust-integration", "--script", "py"])
        assert result.exit_code == 1, result.output
        assert "interrupted second write" in " ".join(result.output.split())
        assert ("Preserved concurrent edits" in result.output) == conflict
        if change == "concurrent":
            assert target.read_text() == "concurrent edit"
        else:
            assert not target.exists()
        assert len(backups) == 1 and backups[0].exists() == conflict
        if existing:
            assert any(path.read_bytes() == b"original bytes" for path in backups[0].rglob("*") if path.is_file())
        assert KEY not in read_records(project)
        assert KEY not in INTEGRATION_REGISTRY
    finally:
        for backup in backups:
            if backup.exists():
                shutil.rmtree(backup)


@pytest.mark.parametrize("operation", ["install", "switch"])
@pytest.mark.parametrize("preexisting", [None, ".sample-agent", ".sample-agent/skills", ".sample-agent/skills/sample"])
def test_failed_setup_restores_completed_writes_and_original_directories(tmp_path, server, operation, preexisting):
    body = '''    def setup(self, project_root, manifest, **kwargs):
        manifest.record_file(".sample-agent/skills/sample/SKILL.md", "completed write")
        raise OSError("setup failure after completed write")
'''
    publish(server, code=implementation(body=body))
    project = catalog_project(tmp_path, server)
    if operation == "switch":
        assert run(project, ["integration", "install", "claude"]).exit_code == 0
    if preexisting:
        (project / preexisting).mkdir(parents=True)
    original_directories = {path for path in project.rglob("*") if path.is_dir()}
    before = snapshot(project)
    result = run(project, ["integration", operation, KEY, "--trust-integration", "--script", "py"])
    assert result.exit_code == 1, result.output
    assert "setup failure after completed write" in " ".join(result.output.split())
    assert "Preserved concurrent edits" not in result.output
    assert snapshot(project) == before
    assert all(path.is_dir() for path in original_directories)
    if preexisting:
        assert not any((project / preexisting).iterdir())
    else:
        assert not (project / ".sample-agent").exists()


@pytest.mark.parametrize("record_ownership", [False, True])
@pytest.mark.parametrize("limit_offset", [-1, 0, 1])
@pytest.mark.parametrize("windows_newlines", [False, True])
def test_trust_grant_respects_reader_limit_before_replacement(
    tmp_path, server, monkeypatch, record_ownership, limit_offset, windows_newlines,
):
    from specify_cli.integrations import installer
    from specify_cli.integrations.manifest import IntegrationManifest

    if windows_newlines:
        original_temporary_file = installer.tempfile.NamedTemporaryFile

        def windows_temporary_file(*args, **kwargs):
            if "b" not in kwargs.get("mode", "w+b") and "newline" not in kwargs:
                kwargs["newline"] = "\r\n"
            return original_temporary_file(*args, **kwargs)

        monkeypatch.setattr(installer.tempfile, "NamedTemporaryFile", windows_temporary_file)
    publish(server)
    first = catalog_project(tmp_path, server)
    install(first)
    second = catalog_project(tmp_path / "second", server)
    manifest = IntegrationManifest(KEY, second, version="1.0.0")
    manifest.record_file(".sample-agent/skills/sample.md", "sample output")
    manifest.save()
    record = read_records(first)[KEY]
    trust = installer._trust_store(first)
    original = trust.read_bytes()
    original_trust_paths = set(trust.parent.iterdir())
    expected = json.loads(original)
    identity = installer._trust_identity(second, KEY, record["files"])
    expected["grants"] = sorted(set(expected["grants"]) | {identity})
    if record_ownership:
        expected["recovery"][installer._recovery_identity(second, KEY)] = {
            "package": identity,
            "files": record["files"],
            "registrar_config": record["registrar_config"],
            "paths": sorted(manifest.files),
        }
    content = json.dumps(expected, indent=2) + "\n"
    monkeypatch.setattr(installer, "_MAX_TRUST_STATE_BYTES", len(content.encode("utf-8")) + limit_offset, raising=False)
    if limit_offset < 0:
        with pytest.raises(IntegrationInstallError, match="trust registry exceeds size limit"):
            installer._grant_trust(second, KEY, record, record_ownership=record_ownership)
        assert trust.read_bytes() == original
    else:
        installer._grant_trust(second, KEY, record, record_ownership=record_ownership)
        assert identity in installer._read_trust(trust)
        assert trust.read_bytes() == content.encode("utf-8")
    assert load_installed_integrations(first) == [KEY]
    assert set(trust.parent.iterdir()) == original_trust_paths


def test_install_trust_limit_failure_rolls_back_without_disabling_existing_adapter(tmp_path, server, monkeypatch):
    from specify_cli.integrations import installer
    from specify_cli.integrations.manifest import IntegrationManifest

    publish(server)
    first = catalog_project(tmp_path, server)
    install(first)
    second = catalog_project(tmp_path / "second", server)
    record = read_records(first)[KEY]
    trust = installer._trust_store(first)
    expected = json.loads(trust.read_text())
    identity = installer._trust_identity(second, KEY, record["files"])
    expected["grants"] = sorted(set(expected["grants"]) | {identity})
    expected["recovery"][installer._recovery_identity(second, KEY)] = {
        "package": identity,
        "files": record["files"],
        "registrar_config": record["registrar_config"],
        "paths": sorted(IntegrationManifest.load(KEY, first).files),
    }
    limit = len((json.dumps(expected, indent=2) + "\n").encode("utf-8")) - 1
    monkeypatch.setattr(installer, "_MAX_TRUST_STATE_BYTES", limit, raising=False)
    before = snapshot(second)
    result = run(second, ["integration", "install", KEY, "--trust-integration", "--script", "py"])
    assert result.exit_code == 1, result.output
    assert "trust registry exceeds size limit" in " ".join(result.output.split())
    assert snapshot(second) == before
    assert KEY not in read_records(second)
    assert load_installed_integrations(first) == [KEY]
    assert installer._recovery_identity(first, KEY) in installer._read_trust_state(trust)["recovery"]


@pytest.mark.parametrize("consumer", ["retained-registrar", "preset-registration"])
@pytest.mark.parametrize("interleaved", [False, True])
@pytest.mark.parametrize("lazy_import", [False, True])
def test_registration_keeps_requested_project_hooks(tmp_path, server, monkeypatch, consumer, interleaved, lazy_import):
    from specify_cli.presets import PresetManager

    def package(marker, folder):
        hook = (
            "        from .helper import MARKER\n"
            if lazy_import else f"        MARKER = {marker!r}\n"
        )
        code = implementation(
            flavor="markdown", folder=folder,
            body="    def post_process_command_content(self, content):\n" + hook + "        return content + '\\n' + MARKER + '\\n'\n",
        )
        publish(server, code=code, members={"helper.py": f"MARKER = {marker!r}\n".encode()})

    package("FIRST PROJECT ADAPTER", ".sample-agent")
    first = catalog_project(tmp_path, server)
    install(first)
    registrar = CommandRegistrar(first)
    package("SECOND PROJECT ADAPTER", ".other-agent")
    second = catalog_project(tmp_path / "second", server)
    install(second)
    source = tmp_path / "source"
    source.mkdir()
    (source / "command.md").write_text("---\ndescription: Sample command\n---\nBody\n")
    if consumer == "retained-registrar":
        if not interleaved:
            load_installed_integrations(first)
        registrar.register_commands(
            KEY, [{"name": "speckit.sample", "file": "command.md"}],
            "sample", source, first,
        )
    else:
        manager = PresetManager(first)
        original = manager._command_registrar

        def snapshot_then_interleave():
            scoped_registrar = original()
            if interleaved:
                load_installed_integrations(second)
            return scoped_registrar

        monkeypatch.setattr(manager, "_command_registrar", snapshot_then_interleave)
        manifest = SimpleNamespace(id="sample", templates=[{
            "type": "command", "name": "speckit.sample", "file": "command.md",
        }])
        manager._register_commands(manifest, source)
    output = (first / ".sample-agent/commands/speckit.sample.md").read_text()
    assert "FIRST PROJECT ADAPTER" in output
    assert "SECOND PROJECT ADAPTER" not in output
    assert not (first / ".other-agent").exists()


@pytest.mark.parametrize("consumer", ["extension", "preset"])
def test_skill_directory_uses_pinned_project_configuration(tmp_path, server, monkeypatch, consumer):
    import specify_cli
    from specify_cli.extensions import ExtensionManager
    from specify_cli.presets import PresetManager

    publish(server)
    first = catalog_project(tmp_path, server)
    install(first)
    publish(server, code=implementation(folder=".other-agent"))
    second = catalog_project(tmp_path / "second", server)
    install(second)
    original = specify_cli.resolve_active_skills_dir

    def interleave_before_directory_resolution(root):
        load_installed_integrations(second)
        return original(root)

    monkeypatch.setattr(specify_cli, "resolve_active_skills_dir", interleave_before_directory_resolution)
    manager = ExtensionManager(first) if consumer == "extension" else PresetManager(first)
    assert manager._get_skills_dir() == first / ".sample-agent/skills"
    assert not (first / ".other-agent").exists()


@pytest.mark.parametrize("consumer", ["retained-registrar", "preset-registration"])
def test_registration_pins_hooks_and_lazy_imports_during_another_thread_load(tmp_path, server, monkeypatch, consumer):
    from specify_cli.integrations import installer
    from specify_cli.presets import PresetManager

    body = '''    def post_process_command_content(self, content):
        from specify_cli.integrations import get_integration, installer
        callback = getattr(installer, "_review_registration_interleave", None)
        if callback is not None:
            callback()
        assert get_integration(self.key) is self, "wrong project registry"
        from .helper import MARKER
        return content + "\\n" + MARKER + "\\n"
'''
    publish(server, code=implementation(flavor="markdown", body=body), members={
        "helper.py": b"MARKER = 'FIRST PROJECT ADAPTER'\n",
    })
    first = catalog_project(tmp_path, server)
    install(first)
    publish(server, code=implementation(flavor="markdown", folder=".other-agent"))
    second = catalog_project(tmp_path / "second", server)
    install(second)
    source = tmp_path / "source"
    source.mkdir()
    (source / "command.md").write_text("---\ndescription: Sample command\n---\nBody\n")

    def interleave():
        errors = []

        def load_second():
            try:
                load_installed_integrations(second)
            except Exception as exc:
                errors.append(exc)

        thread = threading.Thread(target=load_second)
        thread.start()
        thread.join(timeout=10)
        assert not thread.is_alive()
        assert not errors

    monkeypatch.setattr(installer, "_review_registration_interleave", interleave, raising=False)
    if consumer == "retained-registrar":
        registrar = CommandRegistrar(first)
        registrar.register_commands(
            KEY, [{"name": "speckit.sample", "file": "command.md"}],
            "sample", source, first,
        )
    else:
        manager = PresetManager(first)
        manifest = SimpleNamespace(id="sample", templates=[{
            "type": "command", "name": "speckit.sample", "file": "command.md",
        }])
        manager._register_commands(manifest, source)
    output = (first / ".sample-agent/commands/speckit.sample.md").read_text()
    assert "FIRST PROJECT ADAPTER" in output
    assert not (first / ".other-agent").exists()


def test_retained_registrar_rechecks_revoked_local_consent_before_rendering(tmp_path, server):
    from specify_cli.integrations import installer

    publish(server, code=implementation(flavor="markdown"))
    project = catalog_project(tmp_path, server)
    install(project)
    registrar = CommandRegistrar(project)
    source = tmp_path / "source"
    source.mkdir()
    (source / "command.md").write_text("---\ndescription: Sample command\n---\nBody\n")
    trust = installer._trust_store(project)
    data = json.loads(trust.read_text())
    data["grants"] = []
    trust.write_text(json.dumps(data))
    before = snapshot(project)
    with pytest.raises(IntegrationInstallError, match="no local trust decision"):
        registrar.register_commands(
            KEY, [{"name": "speckit.sample", "file": "command.md"}],
            "sample", source, project,
        )
    assert snapshot(project) == before


@pytest.mark.parametrize("link_kind", ["leaf", "ancestor", "dangling-leaf"])
def test_manifest_setup_rejects_project_local_symlink_targets(tmp_path, server, link_kind):
    relative = (
        ".sample-agent/skills/linked-dir/target.txt"
        if link_kind == "ancestor" else ".sample-agent/skills/link.txt"
    )
    body = f'''    def setup(self, project_root, manifest, **kwargs):
        manifest.record_file({relative!r}, "replacement")
        return []
'''
    publish(server, code=implementation(body=body))
    project = catalog_project(tmp_path, server)
    target_dir = project / "user"
    target_dir.mkdir()
    target = target_dir / "target.txt"
    if link_kind != "dangling-leaf":
        target.write_text("user content")
    link = project / (
        ".sample-agent/skills/linked-dir" if link_kind == "ancestor"
        else ".sample-agent/skills/link.txt"
    )
    link.parent.mkdir(parents=True)
    link.symlink_to(target_dir if link_kind == "ancestor" else target, target_is_directory=link_kind == "ancestor")
    before = snapshot(project)
    result = run(project, ["integration", "install", KEY, "--trust-integration", "--script", "py"])
    assert result.exit_code == 1, result.output
    assert "symlinked" in result.output.lower()
    assert snapshot(project) == before
    assert link.is_symlink()
    assert KEY not in read_records(project)


@pytest.mark.parametrize("source", [
    "descriptor", "runtime", "override", "interactive", "optional-only", "ide-descriptor",
])
@pytest.mark.parametrize("available", [False, True])
def test_check_probes_external_adapter_tools_not_catalog_ids(tmp_path, server, monkeypatch, source, available):
    metadata = descriptor()
    if source in {"descriptor", "ide-descriptor"}:
        metadata["requires"]["tools"] = [
            {"name": "acme", "version": ">=1.0"},
            {"name": "optional-helper", "required": False},
        ]
    elif source == "optional-only":
        metadata["requires"]["tools"] = [{"name": "optional-helper", "required": False}]
    body = '''
    def build_exec_args(self, prompt, *, model=None, output_json=True,
                        integration_args=None, integration_options=None, project_root=None):
        return ["acme", "-p", prompt]
'''
    if source in {"descriptor", "ide-descriptor"}:
        body = '''
    def build_exec_args(self, prompt, *, model=None, output_json=True,
                        integration_args=None, integration_options=None, project_root=None):
        raise AssertionError("explicit tool requirements must not invoke the runtime builder")
'''
    if source == "override":
        body = ""
        monkeypatch.setenv("SPECKIT_INTEGRATION_SAMPLE_AGENT_EXECUTABLE", "acme")
    elif source == "interactive":
        body = '''
    def build_exec_args(self, prompt, *, model=None, output_json=True,
                        integration_args=None, integration_options=None, project_root=None):
        return None
'''
        monkeypatch.setenv("SPECKIT_INTEGRATION_SAMPLE_AGENT_EXECUTABLE", "acme")
    code = implementation(flavor="markdown", body=body)
    if source != "ide-descriptor":
        code = code.replace('"requires_cli": False', '"requires_cli": True')
    publish(server, metadata=metadata, code=code)
    monkeypatch.setattr(shutil, "which", lambda name, *args, **kwargs: "/sample/acme" if name == "acme" else None)
    project = catalog_project(tmp_path, server)
    install(project)
    probes = []

    def which(name, *args, **kwargs):
        probes.append(name)
        return "/sample/acme" if name == "acme" and available else None

    def no_process(*args, **kwargs):
        raise AssertionError("tool checks must not execute processes")

    monkeypatch.setattr(shutil, "which", which)
    monkeypatch.setattr(subprocess, "run", no_process)
    monkeypatch.setattr("specify_cli._utils.CLAUDE_LOCAL_PATH", tmp_path / "absent-claude")
    monkeypatch.setattr("specify_cli._utils.CLAUDE_NPM_LOCAL_PATH", tmp_path / "absent-npm-claude")
    result = run(project, ["check"])
    assert result.exit_code == 0, result.output
    assert "acme" in probes
    assert KEY not in probes
    assert "optional-helper" not in probes
    assert "acme" in result.output
    assert ("Tip: Install a coding agent" in result.output) == (not available)


@pytest.mark.parametrize("missing", ["acme", "required-helper"])
def test_check_reports_missing_external_auxiliary_requirements(tmp_path, server, monkeypatch, missing):
    metadata = descriptor()
    metadata["requires"]["tools"] = [
        {"name": "acme"},
        {"name": "required-helper", "required": True},
        {"name": "acme"},
        {"name": "optional-helper", "required": False},
    ]
    publish(server, metadata=metadata)
    monkeypatch.setattr(shutil, "which", lambda name, *args, **kwargs: "/sample/tool")
    project = catalog_project(tmp_path, server)
    install(project)
    probes = []

    def which(name, *args, **kwargs):
        probes.append(name)
        return "/sample/tool" if name in {"acme", "required-helper"} and name != missing else None

    monkeypatch.setattr(shutil, "which", which)
    result = run(project, ["check"])
    assert result.exit_code == 0, result.output
    assert probes.count("acme") == 1
    assert probes.count("required-helper") == 1
    assert "optional-helper" not in probes
    assert KEY not in probes
    assert f"not found: {missing}" in result.output


def test_check_skips_optional_tools_for_external_ide_adapter(tmp_path, server, monkeypatch):
    metadata = descriptor()
    metadata["requires"]["tools"] = [{"name": "optional-helper", "required": False}]
    publish(server, metadata=metadata)
    project = catalog_project(tmp_path, server)
    install(project)
    probes = []

    def which(name, *args, **kwargs):
        probes.append(name)
        return None

    monkeypatch.setattr(shutil, "which", which)
    result = run(project, ["check"])
    assert result.exit_code == 0, result.output
    assert KEY not in probes
    assert "optional-helper" not in probes
    assert "Sample Agent" in result.output
    assert "IDE-based, no CLI check" in result.output


@pytest.mark.parametrize("error_type", ["ValueError", "OSError", "NotImplementedError"])
def test_check_external_executable_resolution_errors_are_explicit(tmp_path, server, monkeypatch, error_type):
    body = f'''
    def build_exec_args(self, prompt, *, model=None, output_json=True,
                        integration_args=None, integration_options=None, project_root=None):
        raise {error_type}("sample executable lookup failure [red]")
'''
    code = implementation(flavor="markdown", body=body).replace('"requires_cli": False', '"requires_cli": True')
    publish(server, code=code)
    project = catalog_project(tmp_path, server)
    install(project)
    monkeypatch.setattr(shutil, "which", lambda *args, **kwargs: None)
    result = run(project, ["check"])
    assert result.exit_code == 1, result.output
    assert f"Cannot check integration '{KEY}'" in result.output
    assert "sample executable lookup failure [red]" in " ".join(result.output.split())
    assert "Specify CLI is ready to use" not in result.output


def test_check_rejects_missing_external_requirements_before_tool_probes(tmp_path, server, monkeypatch):
    publish(server)
    project = catalog_project(tmp_path, server)
    install(project)
    path = project / ".specify/integrations/packages.json"
    data = json.loads(path.read_text())
    data["packages"][KEY].pop("requires")
    path.write_text(json.dumps(data))

    def no_probe(*args, **kwargs):
        raise AssertionError("invalid metadata must fail before tool checks")

    monkeypatch.setattr(shutil, "which", no_probe)
    result = run(project, ["check"])
    assert result.exit_code == 1, result.output
    assert "invalid package metadata: requires" in result.output


def test_check_renders_external_adapter_names_as_literal_text(tmp_path, server, monkeypatch):
    name = "Sample Agent [red]Preview[/red]"
    metadata = descriptor()
    metadata["integration"]["name"] = name
    metadata["requires"]["tools"] = [{"name": "acme"}]
    code = implementation().replace('"name": "Sample Agent"', f'"name": "{name}"')
    publish(server, metadata=metadata, code=code)
    monkeypatch.setattr(shutil, "which", lambda tool, *args, **kwargs: "/sample/acme" if tool == "acme" else None)
    project = catalog_project(tmp_path, server)
    install(project)
    result = run(project, ["check"])
    assert result.exit_code == 0, result.output
    assert name in result.output


@pytest.mark.parametrize("operation", ["migrate", "uninstall"])
@pytest.mark.parametrize("contents", ["empty", "user", "generated"])
@pytest.mark.parametrize("fail", [False, True])
def test_kimi_legacy_parent_removal_obeys_lifecycle_rollback(tmp_path, server, monkeypatch, operation, contents, fail):
    from specify_cli.integrations import command_install, command_uninstall

    publish(server)
    project = catalog_project(tmp_path, server)
    install(project)
    if operation == "uninstall":
        result = run(project, ["integration", "install", "kimi", "--force", "--script", "py"])
        assert result.exit_code == 0, result.output
    legacy = project / ".kimi/skills"
    legacy.mkdir(parents=True)
    if contents == "user":
        (legacy / "notes.txt").write_text("preserve user notes")
    elif contents == "generated":
        skill = legacy / "speckit-legacy/SKILL.md"
        skill.parent.mkdir()
        skill.write_text(
            "---\nname: speckit-legacy\nmetadata:\n"
            "  author: github-spec-kit\n"
            "  source: templates/commands/legacy.md\n---\nLegacy skill\n"
        )
    original_directories = {path for path in project.rglob("*") if path.is_dir()}
    before = snapshot(project)
    if fail:
        def fail_after_cleanup(*args, **kwargs):
            assert legacy.exists() == (contents == "user")
            raise OSError("sample failure after legacy cleanup")

        module = command_install if operation == "migrate" else command_uninstall
        monkeypatch.setattr(module, "_write_integration_json", fail_after_cleanup)
    arguments = (
        ["integration", "install", "kimi", "--force", "--script", "py", "--integration-options=--migrate-legacy"]
        if operation == "migrate" else ["integration", "uninstall", "kimi"]
    )
    result = run(project, arguments)
    if fail:
        assert result.exit_code == 1, result.output
        assert "sample failure after legacy cleanup" in " ".join(result.output.split())
        assert snapshot(project) == before
        assert all(path.is_dir() for path in original_directories)
    else:
        assert result.exit_code == 0, result.output
        assert legacy.exists() == (contents == "user")
        if contents == "user":
            assert (legacy / "notes.txt").read_text() == "preserve user notes"
        elif contents == "generated" and operation == "migrate":
            assert (project / ".kimi-code/skills/speckit-legacy/SKILL.md").is_file()


@pytest.mark.parametrize("operation", ["run", "resume"])
@pytest.mark.parametrize("failure", ["dispatch-reload", "lazy-import", "none"])
@pytest.mark.parametrize("json_output", [False, True])
def test_workflow_dispatch_adapter_failures_keep_persisted_context(
    tmp_path, server, monkeypatch, operation, failure, json_output,
):
    from specify_cli.workflows import STEP_REGISTRY
    from specify_cli.workflows.base import RunStatus, StepResult, StepStatus
    from specify_cli.workflows.engine import RunState

    mutation = (
        '''        from pathlib import Path
        Path(__file__).with_name("helper.py").write_text("VALUE = 'changed'\\n")
'''
        if failure == "lazy-import" else ""
    )
    body = '''
    def build_exec_args(self, prompt, *, model=None, output_json=True,
                        integration_args=None, integration_options=None, project_root=None):
''' + mutation + '''        from .helper import VALUE
        return ["sample-agent-process", "-p", prompt]
'''
    publish(server, code=implementation(body=body), members={
        "helper.py": b"VALUE = 'original'\n",
    })
    project = catalog_project(tmp_path, server)
    install(project)
    helper = project / f".specify/integrations/packages/{KEY}/helper.py"
    source = project / "sample-dispatch-workflow.yml"
    source.write_text(yaml.safe_dump({
        "schema_version": "1.0",
        "workflow": {"id": "sample-workflow", "name": "Sample Workflow", "version": "1.0.0"},
        "steps": [
            {"id": "sample-preparation", "type": "gate", "message": "Sample preparation", "options": ["approve", "reject"]},
            {"id": "sample-dispatch", "type": "prompt", "integration": KEY, "prompt": "Sample prompt"},
        ],
    }))
    if operation == "resume":
        started = run(project, ["workflow", "run", str(source), "--json"])
        assert started.exit_code == 0, started.output
        initial = json.loads(started.stdout)
        assert initial["status"] == "paused"
        run_id = initial["run_id"]

    def approve_preparation(_step, config, context):
        if failure == "dispatch-reload":
            helper.write_text("VALUE = 'changed'\n")
        return StepResult(status=StepStatus.COMPLETED)

    monkeypatch.setattr(type(STEP_REGISTRY["gate"]), "execute", approve_preparation)
    original_which = shutil.which
    monkeypatch.setattr(
        shutil, "which",
        lambda name, *args, **kwargs: "/sample-agent-process"
        if name == "sample-agent-process" else original_which(name, *args, **kwargs),
    )
    processes = []

    def process_double(argv, **kwargs):
        assert failure == "none", "damaged adapters must fail before process execution"
        processes.append(argv)
        return SimpleNamespace(returncode=0, stdout="sample response", stderr="")

    monkeypatch.setattr(subprocess, "run", process_double)
    arguments = ["workflow", operation, str(source) if operation == "run" else run_id]
    if json_output:
        arguments.append("--json")
    result = run(project, arguments)
    failed = failure != "none"
    assert result.exit_code == (1 if failed else 0), result.output
    states = list((project / ".specify/workflows/runs").glob("*/state.json"))
    assert len(states) == 1
    persisted = RunState.load(states[0].parent.name, project)
    assert persisted.status == (RunStatus.FAILED if failed else RunStatus.COMPLETED)
    assert persisted.current_step_id == "sample-dispatch"
    assert persisted.current_step_index == 1
    assert persisted.step_results["sample-preparation"]["status"] == "completed"
    assert bool(processes) == (not failed)
    if json_output:
        payload = json.loads(result.stdout)
        assert payload["run_id"] == persisted.run_id
        assert payload["workflow_id"] == persisted.workflow_id == "sample-workflow"
        assert payload["current_step_id"] == persisted.current_step_id
        assert payload["current_step_index"] == persisted.current_step_index
        assert payload["status"] == persisted.status.value
        assert result.stderr == ""
        if failed:
            assert payload["error"] == persisted.error
        else:
            assert "error" not in payload
    elif failed:
        assert ("Workflow failed" if operation == "run" else "Resume failed") in result.output
    if failed:
        assert "modified" in persisted.error
