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
def isolated_registry(monkeypatch):
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
    rendered = skill.read_text()
    assert ".specify/scripts/python/setup_plan.py" in rendered
    assert "{SCRIPT}" not in rendered and "__AGENT__" not in rendered
    assert "speckit-plan" in rendered
    manifest = json.loads((project / f".specify/integrations/{KEY}.manifest.json").read_text())
    assert not any("packages/" in name for name in manifest["files"])
    process = subprocess.run(
        [str(Path(sys.executable).parent / "specify"), "integration", "list"],
        cwd=project, capture_output=True, text=True, check=False,
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
    assert "{SCRIPT}" not in command.read_text()
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
    skill.write_text(skill.read_text() + "\nUser customization\n")
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


def test_extension_and_preset_contributions_follow_active_external_adapter(tmp_path, server):
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
    assert "Sample preset guidance" not in (project / ".sample-agent/skills/speckit-specify/SKILL.md").read_text()
    activated = run(project, ["integration", "use", KEY])
    assert activated.exit_code == 0, activated.output
    assert (project / ".sample-agent/skills/speckit-git-commit/SKILL.md").is_file()
    assert "Sample preset guidance" in (project / ".sample-agent/skills/speckit-specify/SKILL.md").read_text()
    assert "sample-agent" in json.loads((project / ".specify/init-options.json").read_text())["ai"]
    upgraded = run(project, ["integration", "upgrade", KEY, "--trust-integration", "--force"])
    assert upgraded.exit_code == 0, upgraded.output
    assert "Sample preset guidance" in (project / ".sample-agent/skills/speckit-specify/SKILL.md").read_text()
    removed = run(project, ["integration", "uninstall", KEY])
    assert removed.exit_code == 0, removed.output
    assert not (project / ".sample-agent/skills/speckit-git-commit/SKILL.md").exists()
    assert not (project / ".sample-agent/skills/speckit-specify/SKILL.md").exists()
    assert (project / ".claude/skills/speckit-git-commit/SKILL.md").is_file()
    assert "Sample preset guidance" in (project / ".claude/skills/speckit-specify/SKILL.md").read_text()
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
    assert any((backups[0] / "1").rglob("packages.json")) or any((backups[0] / "0").rglob("packages.json"))
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
            path = root / ".specify/integrations/packages.json"
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
