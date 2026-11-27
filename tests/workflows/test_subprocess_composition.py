"""Real workers, installed fixture packages, and durable parent execution trees."""
from copy import deepcopy
import errno
import json
import os
from pathlib import Path
import shutil
import sys

import pytest

from specify_cli.workflows import load_custom_steps, _unload_custom_steps
from specify_cli.workflows.base import RunStatus
from specify_cli.workflows.engine import WorkflowEngine, RunState
from specify_cli.workflows.function import load_workflow_functions
from specify_cli.workflows.function.loader import _unload_custom_functions
from tests.workflows.test_composition_execution import definition, install, call

FIXTURES = Path(__file__).parent / "fixtures/subprocess"


@pytest.fixture
def projects(tmp_path):
    source = tmp_path / "source"
    target = tmp_path / "project ü space"
    source.mkdir()
    target.mkdir()
    for kind, fixture, name in (("steps", "probe", "probe"), ("functions", "functions", "boundary-functions")):
        shutil.copytree(FIXTURES / fixture, source / ".specify/workflows" / kind / name)
    load_custom_steps(source)
    load_workflow_functions(source)
    yield source, target
    _unload_custom_steps()
    _unload_custom_functions()


def isolated(root, target="child", **fields):
    return call(target, execution={"mode": "subprocess", "project_root": str(root)}, **fields)


def symlink_or_skip(link, target, *, directory=False):
    try:
        link.symlink_to(target, target_is_directory=directory)
    except NotImplementedError as exc:
        pytest.skip(f"Host cannot create symlinks: {exc}")
    except OSError as exc:
        if exc.errno in {errno.EPERM, errno.ENOSYS, errno.ENOTSUP, errno.EOPNOTSUPP} or getattr(exc, "winerror", None) in {50, 1314}:
            pytest.skip(f"Host cannot create symlinks: {exc}")
        raise


def test_real_private_context_and_source_assets(projects, monkeypatch):
    source, target = projects
    child = definition("child", [{"id": "inspect", "type": "boundary-probe", "asset": True, "read_stdin": True,
                                   "value": "{{ inputs.value | boundary_suffix }}"}],
                       inputs={"value": {"type": "string", "default": "default"}},
                       outputs={"inspected": {"value": "{{ steps.inspect.output }}"}})
    child.data["workflow"]["model"] = "child-model"
    directory = install(source, child)
    (directory / "asset.txt").write_text("companion")
    # Lookup remains at the source even if the execution project has a conflict.
    install(target, definition("child", [{"id": "bad", "type": "no-such-step"}]))
    before = (os.getcwd(), sys.stdin, sys.stdout, sys.stderr, dict(os.environ))
    parent = definition("parent", [{"id": "private", "type": "boundary-probe"}, isolated(target, input={"value": "typed"})],
                        inputs={"secret": {"type": "string", "default": "caller-secret"}})
    parent.data["workflow"]["model"] = "parent-model"
    state = WorkflowEngine(source).execute(parent)
    assert state.status == RunStatus.COMPLETED
    inspected = state.step_results["call"]["output"]["inspected"]
    assert inspected["pid"] != os.getpid()
    assert inspected["root"] == inspected["cwd"] == str(target)
    assert inspected["value"] == "typed-fresh"
    assert inspected["model"] == "child-model"
    assert inspected["inputs"] == {"value": "typed"}
    assert inspected["steps"] == [] and inspected["item"] is None and inspected["stdin"] == ""
    assert inspected["asset"] == "companion"
    assert before == (os.getcwd(), sys.stdin, sys.stdout, sys.stderr, dict(os.environ))
    assert len(list((source / ".specify/workflows/runs").iterdir())) == 1
    assert not (target / ".specify/workflows/runs").exists()


def test_real_init_fan_out(projects, tmp_path):
    source, _ = projects
    roots = [tmp_path / name for name in ("alpha", "beta")]
    rendezvous = tmp_path / "rendezvous"
    rendezvous.mkdir()
    for root in roots:
        root.mkdir()
    child = definition("child", [
        {"id": "rendezvous", "type": "boundary-probe", "rendezvous": str(rendezvous)},
        {"id": "init", "type": "init", "here": True, "integration": "copilot", "script": "py", "no_git": True},
        {"id": "inspect", "type": "boundary-probe", "scaffold": True, "effect": "initialized"},
    ], outputs={"pid": {"value": "{{ steps.inspect.output.pid }}"},
                "root": {"value": "{{ steps.inspect.output.root }}"}})
    install(source, child)
    step = isolated("{{ item }}")
    parent = definition("parent", [{"id": "projects", "type": "fan-out", "items": [str(r) for r in roots],
                                    "max_concurrency": 2, "step": step}])
    before = (os.getcwd(), sys.stdin, sys.stdout, sys.stderr, dict(os.environ))
    state = WorkflowEngine(source).execute(parent)
    assert state.status == RunStatus.COMPLETED, state.error
    results = state.step_results["projects"]["output"]["results"]
    assert [r["root"] for r in results] == [str(r) for r in roots]
    assert len({r["pid"] for r in results}) == 2
    for root in roots:
        assert (root / "initialized").read_text() == "effect\n"
        assert (root / ".specify/memory/constitution.md").is_file()
    assert before == (os.getcwd(), sys.stdin, sys.stdout, sys.stderr, dict(os.environ))


def test_real_init_pause_resume_frozen_binding(projects):
    source, target = projects
    child = definition("child", [
        {"id": "init", "type": "init", "here": True, "integration": "copilot", "script": "py", "no_git": True},
        {"id": "effect", "type": "boundary-probe", "effect": "before"},
        {"id": "gate", "type": "gate", "message": "Review", "verdict_input": "verdict"},
        {"id": "after", "type": "boundary-probe", "effect": "after"},
    ], inputs={"verdict": {"type": "string", "default": ""}},
       outputs={"pid": {"value": "{{ steps.after.output.pid }}"}})
    directory = install(source, child)
    parent = definition("parent", [isolated("{{ inputs.root }}", input={"verdict": "{{ inputs.verdict }}"})],
                        inputs={"root": {"type": "string", "default": str(target)},
                                "verdict": {"type": "string", "default": ""}})
    paused = WorkflowEngine(source).execute(parent)
    assert paused.status == RunStatus.PAUSED, paused.error
    scaffold = target / ".specify/init-options.json"
    before = (scaffold.read_bytes(), scaffold.stat().st_mtime_ns)
    frozen = deepcopy(paused.execution["sequence"]["nodes"][0]["binding"])
    (directory / "workflow.yml").write_text("changed source no longer valid")
    resumed = WorkflowEngine(source).resume(paused.run_id, {"verdict": "approve", "root": "missing"})
    assert resumed.status == RunStatus.COMPLETED, resumed.error
    assert before == (scaffold.read_bytes(), scaffold.stat().st_mtime_ns)
    assert (target / "before").read_text() == "effect\n"
    assert (target / "after").read_text() == "effect\n"
    binding = resumed.execution["sequence"]["nodes"][0]["binding"]
    assert binding["execution"] == frozen["execution"] and binding["definition"] == frozen["definition"]
    assert RunState.load(resumed.run_id, source).execution == resumed.execution


@pytest.mark.parametrize("value", [None, True, [], {}, {"mode": "bogus"}, {"mode": "{{ inputs.mode }}"},
                                   {"mode": "in-process", "timeout": 1}, {"mode": "subprocess"},
                                   {"mode": "subprocess", "project_root": "x", "timeout": True},
                                   {"mode": "subprocess", "project_root": "x", "extra": 1}])
def test_invalid_execution_shape_rejected_before_launch(projects, monkeypatch, value):
    from specify_cli.workflows import _subprocess
    source, _ = projects
    monkeypatch.setattr(_subprocess.Supervisor, "launch", lambda *a: pytest.fail("must not launch"))
    parent = definition("parent", [call(execution=value)])
    assert WorkflowEngine(source).validate(parent)
    state = WorkflowEngine(source).execute(parent)
    assert state.status == RunStatus.FAILED


@pytest.mark.parametrize("mode", [None, {"mode": "in-process"}])
def test_default_process_identity(projects, mode):
    source, _ = projects
    install(source, definition("child", [{"id": "inspect", "type": "boundary-probe"}],
                               outputs={"pid": {"value": "{{ steps.inspect.output.pid }}"}}))
    config = call() if mode is None else call(execution=mode)
    # The installed fixture reads stdin; make this particular same-process call use DEVNULL.
    import unittest.mock
    with open(os.devnull) as stream, unittest.mock.patch("sys.stdin", stream):
        state = WorkflowEngine(source).execute(definition("parent", [config]))
    assert state.step_results["call"]["output"]["pid"] == os.getpid()


@pytest.mark.parametrize("root", [False, 12, [], "", "missing", "bad\x00root"])
def test_resolved_roots_rejected_before_launch(projects, monkeypatch, root):
    from specify_cli.workflows import _subprocess
    source, _ = projects
    install(source, definition("child", []))
    monkeypatch.setattr(_subprocess.Supervisor, "launch", lambda *a: pytest.fail("must not launch"))
    parent = definition("parent", [isolated("{{ inputs.root }}")],
                        inputs={"root": {"type": "string"}})
    # Direct context binding covers typed expression results without input coercion.
    from specify_cli.workflows.composition import bind_execution, CallError
    from specify_cli.workflows.base import StepContext
    with pytest.raises(CallError):
        bind_execution(parent.steps[0], StepContext(project_root=str(source), inputs={"root": root}), source)


def test_relative_root_uses_caller_project(projects, tmp_path, monkeypatch):
    from specify_cli.workflows.composition import checked_root
    source, target = projects
    launch = tmp_path / "unrelated"
    launch.mkdir()
    monkeypatch.chdir(launch)
    assert checked_root("../" + target.name, str(source)) == str(target)


def test_symlink_root_rejected(projects):
    from specify_cli.workflows.composition import checked_root, CallError
    source, target = projects
    link = source / "link"
    symlink_or_skip(link, target, directory=True)
    with pytest.raises(CallError, match="symlink"):
        checked_root("link/..", str(source))


@pytest.mark.parametrize("home_kind", ["relative", "absolute", "fallback"])
def test_home_origin_survives_fresh_nested_workers(projects, tmp_path, monkeypatch, home_kind):
    source, target = projects
    launch = tmp_path / "launch"
    home = launch / "home"
    home.mkdir(parents=True)
    nested = target / "nested"
    nested.mkdir()
    monkeypatch.chdir(launch)
    home_key = "USERPROFILE" if os.name == "nt" else "HOME"
    if home_kind == "fallback":
        monkeypatch.delenv(home_key, raising=False)
        if os.name == "nt":
            monkeypatch.setenv("HOMEDRIVE", home.drive)
            monkeypatch.setenv("HOMEPATH", str(home)[len(home.drive):])
        else:
            import pwd
            from types import SimpleNamespace
            # Only the parent uses this fallback. The fresh worker must receive
            # the pinned origin rather than consulting its own user database.
            monkeypatch.setattr(pwd, "getpwuid", lambda uid: SimpleNamespace(pw_dir=str(home)))
    else:
        monkeypatch.setenv(home_key, "home" if home_kind == "relative" else str(home))
    monkeypatch.setenv("BOUNDARY_ENV_SENTINEL", "ordinary inherited value")
    before = dict(os.environ)
    probe = {"id": "probe", "type": "boundary-probe", "home_origin": True}
    install(source, definition("inner", [probe],
                               outputs={"observed": {"value": "{{ steps.probe.output }}"}}))
    install(source, definition("child", [probe, isolated(nested, target="inner")],
                               outputs={"outer": {"value": "{{ steps.probe.output }}"},
                                        "inner": {"value": "{{ steps.call.output.observed }}"}}))
    state = WorkflowEngine(source).execute(definition("parent", [isolated(target)]))
    assert state.status == RunStatus.COMPLETED, state.error
    observed = state.step_results["call"]["output"]
    assert len({os.getpid(), observed["outer"]["pid"], observed["inner"]["pid"]}) == 3
    for result in (observed["outer"], observed["inner"]):
        assert result["home"] == str(home)
        assert result["trust"] == str(home / ".specify/integration-trust.json")
        assert result["inherited"] == "ordinary inherited value"
        assert not Path(result["trust"]).exists()
    assert dict(os.environ) == before


@pytest.mark.parametrize("mode,attributes,blocked", [("directory", 0x400, True),
                                                    ("file", 0x420, True),
                                                    ("symlink", 0, True),
                                                    ("directory", 0x10, False),
                                                    ("directory", 0, False)])
def test_root_nofollow_metadata_without_junction_api(monkeypatch, mode, attributes, blocked):
    import stat
    from types import SimpleNamespace
    from specify_cli import _file_policy as policy

    class LegacyPath:
        """Bounded Python 3.11 API model, not native Windows validation."""
        followed = False

        def __init__(self, value):
            self.value = str(value)

        anchor = "/"
        parts = ("/", "entry", "project")
        drive = "C:" if os.name == "nt" else ""
        root = "/"

        def __truediv__(self, part):
            return type(self)(self.value.rstrip("/") + "/" + part)

        def is_absolute(self):
            return True

        def is_symlink(self):
            return mode == "symlink"

        def lstat(self):
            return SimpleNamespace(st_mode={"symlink": stat.S_IFLNK, "directory": stat.S_IFDIR,
                                            "file": stat.S_IFREG}[mode],
                                   st_file_attributes=attributes)

        def resolve(self, strict=False):
            type(self).followed = True
            return self

        def is_dir(self):
            return True

        def __str__(self):
            return self.value

    assert not hasattr(LegacyPath, "is_junction")
    monkeypatch.setattr(policy, "Path", LegacyPath)
    if blocked:
        with pytest.raises(policy.ProjectPolicyError, match="symlink or reparse"):
            policy.resolve_nofollow_directory(LegacyPath("/entry/project"))
        assert not LegacyPath.followed
    else:
        assert str(policy.resolve_nofollow_directory(LegacyPath("/entry/project"))) == "/entry/project"
        assert LegacyPath.followed


@pytest.mark.parametrize("environment,expected", [
    ({"USERPROFILE": r"C:\safe\home", "HOMEDRIVE": "Z:", "HOMEPATH": r"\ignored"}, r"C:\safe\home"),
    ({"HOMEDRIVE": "C:", "HOMEPATH": r"\safe\home"}, r"C:\safe\home"),
    ({"USERPROFILE": r"\\server\share\home"}, r"\\server\share\home"),
    ({"USERPROFILE": "C:relative"}, None),
    ({"USERPROFILE": r"\relative"}, None),
    ({"HOMEDRIVE": "C:", "HOMEPATH": "relative"}, None),
])
def test_windows_home_selection_model(monkeypatch, environment, expected):
    """Use the Windows stdlib selection rules; not native Windows evidence."""
    import ntpath
    from specify_cli.workflows._subprocess import _home_origin, ProtocolError
    for key in ("USERPROFILE", "HOMEDRIVE", "HOMEPATH"):
        monkeypatch.delenv(key, raising=False)
    for key, value in environment.items():
        monkeypatch.setenv(key, value)
    selected = ntpath.expanduser("~")
    if expected is None:
        with pytest.raises(ProtocolError, match="Ambiguous"):
            _home_origin(selected, windows=True)
    else:
        assert _home_origin(selected, windows=True) == expected


@pytest.mark.parametrize("windows,value,cwd,expected", [
    (False, "/owned/link/../home", "/controller", "/owned/link/../home"),
    (False, "link/../home", "/controller", "/controller/link/../home"),
    (True, r"C:\owned\link\..\home", r"C:\controller", r"C:\owned\link\..\home"),
    (True, r"link\..\home", r"C:\controller", r"C:\controller\link\..\home"),
])
def test_home_origin_preserves_lexical_parents(monkeypatch, windows, value, cwd, expected):
    """Path models only; no filesystem or native Windows claim."""
    from specify_cli.workflows import _subprocess
    with monkeypatch.context() as patch:
        patch.setattr(os, "getcwd", lambda: cwd)
        actual = _subprocess._home_origin(value, windows=windows)
    assert actual == expected


def test_unknown_home_rejected_before_launch(projects, monkeypatch):
    from specify_cli.workflows import _subprocess
    source, target = projects
    install(source, definition("child", [{"id": "probe", "type": "boundary-probe"}]))
    if os.name == "nt":
        for key in ("USERPROFILE", "HOMEDRIVE", "HOMEPATH"):
            monkeypatch.delenv(key, raising=False)
    else:
        import pwd
        monkeypatch.delenv("HOME", raising=False)

        def unavailable(uid):
            raise KeyError(uid)

        monkeypatch.setattr(pwd, "getpwuid", unavailable)
    monkeypatch.setattr(_subprocess.Supervisor, "launch", lambda *a: pytest.fail("must not launch"))
    with pytest.raises(RuntimeError, match="home"):
        WorkflowEngine(source).execute(definition("parent", [isolated(target)]))


@pytest.mark.parametrize("kind,skip", [("privilege", True), ("unsupported", True),
                                     ("not-implemented", True), ("exists", False), ("io", False)])
def test_symlink_capability_guard_is_precise(tmp_path, monkeypatch, kind, skip):
    errors = {"privilege": OSError("privilege unavailable"),
              "unsupported": OSError(errno.ENOTSUP, "unsupported"),
              "not-implemented": NotImplementedError("unavailable"),
              "exists": FileExistsError(errno.EEXIST, "already exists"),
              "io": OSError(errno.EIO, "unrelated IO failure")}
    error = errors[kind]
    if kind == "privilege":
        error.winerror = 1314

    def fail(*args, **kwargs):
        raise error

    monkeypatch.setattr(Path, "symlink_to", fail)
    with pytest.raises(pytest.skip.Exception if skip else type(error)):
        symlink_or_skip(tmp_path / "link", tmp_path / "target")


@pytest.mark.parametrize("case", ["failed", "paused", "abort", "timeout", "exception", "exit", "interrupt", "object"])
def test_result_and_exception_semantics(projects, case):
    from specify_cli.workflows._subprocess import RemoteWorkflowError
    source, target = projects
    first = {"id": "probe", "type": "boundary-probe"}
    if case in {"failed", "paused"}:
        first["status"] = case
    if case in {"exception", "exit", "interrupt"}:
        first["exception"] = case
    if case == "timeout":
        first["sleep"] = 10
    if case == "object":
        first["value_object"] = True
    if case == "abort":
        first = {"id": "gate", "type": "gate", "message": "Reject", "verdict_input": "verdict"}
    install(source, definition("child", [first], inputs={"verdict": {"type": "string", "default": "reject"}}))
    config = isolated(target, continue_on_error=True)
    if case == "timeout":
        config["execution"]["timeout"] = .8
    parent = definition("parent", [config, {"id": "after", "type": "boundary-probe", "effect": "after"}])
    if case in {"exception", "object"}:
        with pytest.raises(RemoteWorkflowError):
            WorkflowEngine(source).execute(parent)
    elif case == "exit":
        with pytest.raises(SystemExit) as caught:
            WorkflowEngine(source).execute(parent)
        assert caught.value.code == 7
    else:
        state = WorkflowEngine(source).execute(parent)
        expected = RunStatus.ABORTED if case == "abort" else RunStatus.PAUSED if case in {"paused", "interrupt"} else RunStatus.COMPLETED
        assert state.status == expected
        assert (source / "after").exists() == (expected == RunStatus.COMPLETED)
    assert not (target / "after").exists()


def test_nested_isolated_and_inprocess_source_ownership(projects, tmp_path):
    source, target = projects
    inner = tmp_path / "inner"
    inner.mkdir()
    install(source, definition("leaf", [{"id": "inspect", "type": "boundary-probe", "read_subprocess": True}],
                               outputs={"root": {"value": "{{ steps.inspect.output.root }}"},
                                        "pid": {"value": "{{ steps.inspect.output.pid }}"}}))
    install(source, definition("middle", [call("leaf")], outputs={"root": {"value": "{{ steps.call.output.root }}"}}))
    install(source, definition("child", [call("middle"), {**isolated(inner, "leaf"), "id": "nested"}],
                               outputs={"same": {"value": "{{ steps.call.output.root }}"},
                                        "nested": {"value": "{{ steps.nested.output.root }}"}}))
    state = WorkflowEngine(source).execute(definition("parent", [isolated(target)]))
    assert state.status == RunStatus.COMPLETED
    assert state.step_results["call"]["output"] == {"workflow": "child", "status": "completed", "same": str(target), "nested": str(inner)}
    assert len(list((source / ".specify/workflows/runs").iterdir())) == 1


def test_checkpoint_failure_withholds_ack_and_poison_stops_effects(projects, monkeypatch):
    from specify_cli.workflows._execution import CheckpointError
    source, target = projects
    install(source, definition("child", [{"id": "first", "type": "boundary-probe", "effect": "first"},
                                         {"id": "next", "type": "boundary-probe", "effect": "next"}]))
    original = RunState._atomic_write_json
    failures = []

    def fail(path, data):
        tree = data.get("execution", {})
        nodes = tree.get("sequence", {}).get("nodes", [])
        if nodes and nodes[0].get("children") and nodes[0]["children"][0]["nodes"][0].get("phase") == "done":
            failures.append(path)
            raise OSError("fixture checkpoint unavailable")
        return original(path, data)

    monkeypatch.setattr(RunState, "_atomic_write_json", staticmethod(fail))
    with pytest.raises(CheckpointError):
        WorkflowEngine(source).execute(definition("parent", [isolated(target)]))
    assert len(failures) == 1
    assert (target / "first").read_text() == "effect\n"
    assert not (target / "next").exists()


def test_acknowledged_completion_survives_worker_loss(projects, monkeypatch, tmp_path):
    from specify_cli.workflows import _subprocess as transport
    source, target = projects
    release = tmp_path / "release"
    install(source, definition("child", [{"id": "first", "type": "boundary-probe", "effect": "first"},
                                         {"id": "next", "type": "boundary-probe", "wait_for": str(release), "effect": "next"}]))
    sent = transport.Channel.send
    saved = RunState.save
    first_done = False
    killed = False

    def observe(state):
        nonlocal first_done
        saved(state)
        node = (state.execution or {}).get("sequence", {}).get("nodes", [{}])[0]
        if node.get("children") and node["children"][0]["nodes"][0].get("phase") == "done":
            first_done = True

    def send(channel, message, *args):
        nonlocal killed
        sent(channel, message, *args)
        if first_done and message["kind"] == "ack" and not killed:
            killed = True
            with transport._active_lock:
                workers = [w for group in transport._active.values() for w in group]
            for worker in workers:
                worker.kill()

    monkeypatch.setattr(RunState, "save", observe)
    monkeypatch.setattr(transport.Channel, "send", send)
    with pytest.raises(transport.ProtocolError):
        WorkflowEngine(source).execute(definition("parent", [isolated(target)]))
    assert killed and not (target / "next").exists()
    run_id = next((source / ".specify/workflows/runs").iterdir()).name
    release.touch()
    state = WorkflowEngine(source).resume(run_id)
    assert state.status == RunStatus.COMPLETED
    assert (target / "first").read_text() == "effect\n"
    assert (target / "next").read_text() == "effect\n"


def test_native_diagnostics_cannot_forge_control(projects):
    source, target = projects
    install(source, definition("child", [{"id": "inspect", "type": "boundary-probe", "flood": True}],
                               outputs={"value": {"value": "declared"}}))
    state = WorkflowEngine(source).execute(definition("parent", [isolated(target)]))
    assert state.status == RunStatus.COMPLETED
    assert state.step_results["call"]["output"] == {"workflow": "child", "status": "completed", "value": "declared"}
    entries = [json.loads(line) for line in (state.runs_dir / "log.jsonl").read_text().splitlines()]
    diagnostic = next(entry for entry in entries if entry["event"] == "workflow_worker_diagnostics")
    assert len(diagnostic["diagnostics"].encode()) <= 65536
    assert diagnostic["truncated"] and "native-out" in diagnostic["diagnostics"]


def test_hostile_startup_does_not_execute(projects, monkeypatch, tmp_path):
    source, target = projects
    sentinel = tmp_path / "startup-sentinel"
    code = f"from pathlib import Path; Path({str(sentinel)!r}).touch(); raise RuntimeError('hostile startup')"
    for name in ("sitecustomize.py", "usercustomize.py", "specify_cli.py", "json.py"):
        (target / name).write_text(code)
    misleading = tmp_path / "bin"
    misleading.mkdir()
    (misleading / "specify").write_text(code)
    (misleading / "python").write_text(code)
    monkeypatch.setenv("PATH", str(misleading) + os.pathsep + os.environ["PATH"])
    for key in ("PYTHONPATH", "PYTHONHOME", "PYTHONUSERBASE"):
        monkeypatch.setenv(key, str(target))
    install(source, definition("child", [{"id": "probe", "type": "boundary-probe", "effect": "loaded"}]))
    state = WorkflowEngine(source).execute(definition("parent", [isolated(target)]))
    assert state.status == RunStatus.COMPLETED
    assert (target / "loaded").exists() and not sentinel.exists()


def test_cli_run_resume_status_single_parent_run(projects, monkeypatch):
    from typer.testing import CliRunner
    from specify_cli import app
    source, target = projects
    install(source, definition("child", [{"id": "before", "type": "boundary-probe", "effect": "before"},
                                         {"id": "gate", "type": "gate", "message": "Review", "verdict_input": "verdict"}],
                               inputs={"verdict": {"type": "string", "default": ""}}))
    directory = install(source, definition("parent", [isolated(target, input={"verdict": "{{ inputs.verdict }}"})],
                                           inputs={"verdict": {"type": "string", "default": ""}}))
    monkeypatch.chdir(source)
    runner = CliRunner()
    result = runner.invoke(app, ["workflow", "run", str(directory / "workflow.yml"), "--json"])
    assert result.exit_code == 0, result.output
    paused = json.loads(result.stdout)
    assert paused["status"] == "paused"
    assert paused["workflow_scopes"] == [{"scope_path": ["call"], "workflow_id": "child", "status": "paused"}]
    status = runner.invoke(app, ["workflow", "status", paused["run_id"], "--json"])
    assert status.exit_code == 0, status.output
    assert json.loads(status.stdout)["workflow_scopes"] == paused["workflow_scopes"]
    result = runner.invoke(app, ["workflow", "resume", paused["run_id"], "--input", "verdict=approve", "--json"])
    assert result.exit_code == 0, result.output
    assert json.loads(result.stdout)["status"] == "completed"
    assert (target / "before").read_text() == "effect\n"
    assert len(list((source / ".specify/workflows/runs").iterdir())) == 1
    assert not (target / ".specify/workflows/runs").exists()


def test_execution_root_auto_input_and_untrusted_adapter(projects, tmp_path):
    import hashlib
    from specify_cli.workflows._subprocess import RemoteWorkflowError
    source, target = projects
    (target / ".specify").mkdir()
    (target / ".specify/integration.json").write_text('{"version":1,"default_integration":"copilot"}')
    install(source, definition("child", [{"id": "probe", "type": "boundary-probe"}], inputs={"integration": {"type": "string", "default": "auto"}},
                               outputs={"integration-key": {"value": "{{ inputs.integration }}"}}))
    state = WorkflowEngine(source).execute(definition("parent", [isolated(target)]))
    assert state.step_results["call"]["output"]["integration-key"] == "copilot"
    package = target / ".specify/integrations/packages/untrusted"
    package.mkdir(parents=True)
    sentinel = tmp_path / "adapter-sentinel"
    code = f"from pathlib import Path; Path({str(sentinel)!r}).touch()"
    (package / "__init__.py").write_text(code)
    descriptor = "schema_version: '1.0'\nintegration:\n  id: untrusted\n  name: Fixture\n  version: 1.0.0\n"
    (package / "integration.yml").write_text(descriptor)
    record = {"id": "untrusted", "name": "Untrusted", "description": "fixture", "version": "1.0.0",
              "catalog": "fixture", "download_url": "https://example.invalid/unused", "requires": {},
              "files": {"__init__.py": hashlib.sha256(code.encode()).hexdigest(),
                        "integration.yml": hashlib.sha256(descriptor.encode()).hexdigest()}}
    (target / ".specify/integrations/packages.json").write_text(json.dumps({"schema_version": "1.0", "packages": {"untrusted": record}}))
    with pytest.raises(RemoteWorkflowError, match="no local trust decision"):
        WorkflowEngine(source).execute(definition("other", [isolated(target)]))
    assert not sentinel.exists()
    logs = [p.read_text() for p in (source / ".specify/workflows/runs").glob("*/log.jsonl")]
    assert any("no local trust decision" in log for log in logs)


@pytest.mark.parametrize("case", ["unknown", "missing", "invalid-type", "reserved-output"])
def test_child_contract_failures_are_failed_calls(projects, case):
    source, target = projects
    child = definition("child", [{"id": "probe", "type": "boundary-probe"}], inputs={"required": {"type": "boolean", "required": True}})
    mapping = {"required": True}
    if case == "unknown":
        mapping["unknown"] = "private"
    elif case == "missing":
        mapping = {}
    elif case == "invalid-type":
        mapping["required"] = []
    else:
        child.data["outputs"] = {"workflow": {"value": "reserved"}}
    install(source, child)
    state = WorkflowEngine(source).execute(definition("parent", [isolated(target, input=mapping)]))
    assert state.status == RunStatus.FAILED
    expected = {"unknown": "Undeclared inputs", "missing": "Required input", "invalid-type": "boolean", "reserved-output": "reserved"}
    assert expected[case] in state.error
    assert not list(target.iterdir())


def test_mixed_depth_limit_and_cycle(projects):
    source, target = projects
    install(source, definition("level16", [{"id": "probe", "type": "boundary-probe", "effect": "leaf"}]))
    for i in range(15, 0, -1):
        next_call = isolated(target, f"level{i+1}") if i in {1, 8} else call(f"level{i+1}")
        install(source, definition(f"level{i}", [next_call]))
    state = WorkflowEngine(source).execute(definition("parent", [isolated(target, "level1")]))
    assert state.status == RunStatus.COMPLETED
    assert (target / "leaf").read_text() == "effect\n"
    install(source, definition("level16", [call("level17")]))
    install(source, definition("level17", []))
    state = WorkflowEngine(source).execute(definition("parent", [isolated(target, "level1")]))
    assert state.status == RunStatus.FAILED and "maximum depth 16" in state.error
    install(source, definition("level16", [call("level1")]))
    state = WorkflowEngine(source).execute(definition("parent", [isolated(target, "level1")]))
    assert state.status == RunStatus.FAILED and "cycle" in state.error


def test_scoped_timeout_preserves_unrelated_invocation(projects, tmp_path):
    source, target = projects
    other = tmp_path / "other"
    other.mkdir()
    install(source, definition("slow", [{"id": "sleep", "type": "boundary-probe", "sleep": 10}]))
    install(source, definition("survivor", [{"id": "sleep", "type": "boundary-probe", "sleep": 2},
                                           {"id": "effect", "type": "boundary-probe", "effect": "survived"}]))
    timed = isolated(target, "slow", continue_on_error=True)
    timed["execution"]["timeout"] = 1.5
    parent = definition("parent", [{"id": "spread", "type": "fan-out", "items": [True, False], "max_concurrency": 2,
                                    "step": {"id": "route", "type": "if", "condition": "{{ item }}",
                                             "then": [timed], "else": [isolated(other, "survivor")]}}])
    state = WorkflowEngine(source).execute(parent)
    assert state.status == RunStatus.COMPLETED
    assert (other / "survived").read_text() == "effect\n"
    assert not (target / "survived").exists()


def test_boundary_changes_process_identity(projects):
    source, target = projects
    install(source, definition("child", [{"id": "probe", "type": "boundary-probe"}],
                               outputs={"pid": {"value": "{{ steps.probe.output.pid }}"}}))
    state = WorkflowEngine(source).execute(definition("parent", [isolated(target)]))
    assert state.status == RunStatus.COMPLETED
    assert state.step_results["call"]["output"]["pid"] != os.getpid(), "isolated call must use a different PID"


def test_unfinished_effect_may_repeat_on_resume(projects):
    from specify_cli.workflows._subprocess import RemoteWorkflowError
    source, target = projects
    install(source, definition("child", [{"id": "effect", "type": "boundary-probe", "effect": "count", "exception_input": "fail"}],
                               inputs={"fail": {"type": "boolean", "default": True}}))
    parent = definition("parent", [isolated(target, input={"fail": "{{ inputs.fail }}"})],
                        inputs={"fail": {"type": "boolean", "default": True}})
    with pytest.raises(RemoteWorkflowError, match="unfinished effect"):
        WorkflowEngine(source).execute(parent)
    run_id = next((source / ".specify/workflows/runs").iterdir()).name
    state = WorkflowEngine(source).resume(run_id, {"fail": False})
    assert state.status == RunStatus.COMPLETED
    assert (target / "count").read_text() == "effect\neffect\n"


def test_timeout_cancels_known_nested_worker_and_capture(projects, tmp_path):
    import time
    source, target = projects
    inner = tmp_path / "inner-capture"
    inner.mkdir()
    install(source, definition("leaf", [{"id": "capture", "type": "boundary-probe", "capture": True}]))
    install(source, definition("child", [isolated(inner, "leaf")]))
    config = isolated(target)
    config["execution"]["timeout"] = 20
    started = time.monotonic()
    state = WorkflowEngine(source).execute(definition("parent", [config]))
    elapsed = time.monotonic() - started
    assert state.status == RunStatus.FAILED and "timeout" in state.error
    assert elapsed < 27
    heartbeat = inner / "heartbeat"
    assert heartbeat.exists(), "Nested capture must actually run before timeout"
    value = heartbeat.read_bytes()
    time.sleep(.3)
    assert heartbeat.read_bytes() == value


@pytest.mark.skipif(os.name == "nt", reason="POSIX SIGINT injection; native Ctrl+C requires native validation")
def test_interrupt_cancels_known_nested_workers(projects, tmp_path, monkeypatch):
    import signal
    import threading
    import time
    source, target = projects
    inner = tmp_path / "inner-interrupt"
    inner.mkdir()
    heartbeat = inner / "heartbeat"
    install(source, definition("leaf", [{"id": "capture", "type": "boundary-probe", "capture": True}]))
    install(source, definition("child", [isolated(inner, "leaf")]))
    sent = threading.Event()

    def interrupt():
        deadline = time.monotonic() + 30
        while not heartbeat.exists() and time.monotonic() < deadline:
            time.sleep(.02)
        if heartbeat.exists():
            sent.set()
            os.kill(os.getpid(), signal.SIGINT)

    thread = threading.Thread(target=interrupt, daemon=True)
    thread.start()
    state = WorkflowEngine(source).execute(definition("parent", [isolated(target)]))
    thread.join(timeout=1)
    assert sent.is_set() and state.status == RunStatus.PAUSED
    value = heartbeat.read_bytes()
    time.sleep(.3)
    assert heartbeat.read_bytes() == value


def test_remote_base_exception_category(projects):
    from specify_cli.workflows._subprocess import RemoteWorkflowBaseError
    source, target = projects
    install(source, definition("child", [{"id": "base", "type": "boundary-probe", "exception": "base"}]))
    with pytest.raises(RemoteWorkflowBaseError, match="fixture base exception"):
        WorkflowEngine(source).execute(definition("parent", [isolated(target, continue_on_error=True)]))


def test_site_only_dependency_fails_explicitly(projects, tmp_path, monkeypatch):
    from specify_cli.workflows._subprocess import RemoteWorkflowError
    source, target = projects
    dependencies = tmp_path / "parent-only-dependencies"
    dependencies.mkdir()
    (dependencies / "boundary_parent_only.py").write_text("VALUE = 1")
    monkeypatch.syspath_prepend(str(dependencies))
    package = source / ".specify/workflows/steps/site-only"
    package.mkdir()
    (package / "step.yml").write_text("step:\n  type_key: site-only")
    (package / "__init__.py").write_text(
        "import boundary_parent_only\nfrom specify_cli.workflows.base import StepBase, StepResult\n"
        "class Only(StepBase):\n type_key = 'site-only'\n def execute(self, config, context): return StepResult()\n")
    load_custom_steps(source)
    install(source, definition("child", [{"id": "only", "type": "site-only"}]))
    with pytest.raises(RemoteWorkflowError, match="Invalid frozen worker workflow.*site-only"):
        WorkflowEngine(source).execute(definition("parent", [isolated(target)]))


def test_overlay_lookup_remains_source_owned(projects):
    import yaml
    from specify_cli.workflows.overlay import WorkflowResolver
    source, target = projects
    directory = install(source, definition('child', [{'id': 'probe', 'type': 'boundary-probe', 'value': 'original'}],
                                           outputs={'value': {'value': '{{ steps.probe.output.value }}'}}))
    # Use the actual resolver's installed source ownership. A target-root
    # overlay must not influence a source-root call.
    overlays = target / '.specify/workflows/overlays/child'
    overlays.mkdir(parents=True)
    (overlays / 'bad.yml').write_text('invalid target overlay must not be read')
    source_overlays = source / '.specify/workflows/overlays/child'
    source_overlays.mkdir(parents=True)
    (source_overlays / 'local.yml').write_text(yaml.safe_dump({
        'id': 'local', 'extends': 'child', 'priority': 10,
        'edits': [{'operation': 'replace', 'anchor': 'probe',
                   'step': {'id': 'probe', 'type': 'boundary-probe', 'value': 'source-overlay'}}]}))
    assert WorkflowResolver(source).resolve('child').source_path == directory / 'workflow.yml'
    state = WorkflowEngine(source).execute(definition('parent', [isolated(target)]))
    assert state.step_results['call']['output']['value'] == 'source-overlay'


@pytest.mark.skipif(os.name == 'nt', reason='POSIX escaped diagnostic holder; Windows job containment differs')
def test_inherited_diagnostic_pipe_does_not_hang_readers(projects):
    import signal
    import time
    source, target = projects
    install(source, definition('child', [{'id': 'helper', 'type': 'boundary-probe', 'detached_diagnostics': True}]))
    started = time.monotonic()
    try:
        state = WorkflowEngine(source).execute(definition('parent', [isolated(target)]))
        assert state.status == RunStatus.COMPLETED
        assert time.monotonic() - started < 12
    finally:
        pid_file = target / 'helper.pid'
        if pid_file.exists():
            try:
                os.kill(int(pid_file.read_text()), signal.SIGKILL)
            except ProcessLookupError:
                pass


@pytest.mark.parametrize('nested', [False, True])
def test_retry_gate_consumes_verdict_in_authoritative_binding(projects, nested):
    source, target = projects
    install(source, definition('leaf', [{'id': 'gate', 'type': 'gate', 'message': 'Review',
                                         'verdict_input': 'verdict', 'on_reject': 'retry'}],
                               inputs={'verdict': {'type': 'string', 'default': 'reject', 'enum': ['', 'reject', 'approve']}}))
    if nested:
        install(source, definition('child', [isolated(target, 'leaf', input={'verdict': '{{ inputs.verdict }}'})],
                                   inputs={'verdict': {'type': 'string', 'default': 'reject'}}))
    parent = definition('parent', [isolated(target, 'child' if nested else 'leaf', input={'verdict': '{{ inputs.verdict }}'})],
                        inputs={'verdict': {'type': 'string', 'default': 'reject'}})
    paused = WorkflowEngine(source).execute(parent)
    assert paused.status == RunStatus.PAUSED
    node = paused.execution['sequence']['nodes'][0]
    if nested:
        node = node['children'][0]['nodes'][0]
    assert node['binding']['inputs']['verdict'] == ''
    paused = WorkflowEngine(source).resume(paused.run_id)
    assert paused.status == RunStatus.PAUSED
    state = WorkflowEngine(source).resume(paused.run_id, {'verdict': 'approve'})
    assert state.status == RunStatus.COMPLETED


@pytest.mark.parametrize('code', [7, 'exit-message', None, True])
def test_validated_system_exit_codes(projects, code):
    from specify_cli.workflows._subprocess import RemoteWorkflowBaseError
    source, target = projects
    install(source, definition('child', [{'id': 'exit', 'type': 'boundary-probe', 'exception': 'exit', 'exit_code': code}]))
    if type(code) is bool:
        with pytest.raises(RemoteWorkflowBaseError, match='SystemExit code must'):
            WorkflowEngine(source).execute(definition('parent', [isolated(target)]))
    else:
        with pytest.raises(SystemExit) as caught:
            WorkflowEngine(source).execute(definition('parent', [isolated(target)]))
        assert caught.value.code == code


def test_launch_failure_is_returned_with_call_metadata(projects, monkeypatch):
    from specify_cli.workflows import _subprocess
    source, target = projects
    install(source, definition('child', [{'id': 'probe', 'type': 'boundary-probe'}]))

    def denied(*args):
        raise OSError('fixture launch denied')

    monkeypatch.setattr(_subprocess.Supervisor, 'launch', denied)
    state = WorkflowEngine(source).execute(definition('parent', [isolated(target, continue_on_error=True)]))
    assert state.status == RunStatus.COMPLETED
    output = state.step_results['call']['output']
    assert output == {'workflow': 'child', 'status': 'failed', 'error': 'Isolated workflow launch: fixture launch denied'}


@pytest.mark.parametrize('timeout', [None, False, 0, -1, '1', float('inf'), float('nan'), 10**400])
def test_invalid_timeout_rejected_at_validation_and_execution(projects, monkeypatch, timeout):
    from specify_cli.workflows import _subprocess
    source, target = projects
    config = isolated(target)
    config['execution']['timeout'] = timeout
    monkeypatch.setattr(_subprocess.Supervisor, 'launch', lambda *a: pytest.fail('must not launch'))
    parent = definition('parent', [config])
    assert WorkflowEngine(source).validate(parent)
    assert WorkflowEngine(source).execute(parent).status == RunStatus.FAILED


def test_root_expression_error_remains_exception(projects, monkeypatch):
    from specify_cli.workflows import _subprocess
    source, _ = projects
    monkeypatch.setattr(_subprocess.Supervisor, 'launch', lambda *a: pytest.fail('must not launch'))
    parent = definition('parent', [isolated('{{ inputs.root | from_json }}')],
                        inputs={'root': {'type': 'string', 'default': 'not-json'}})
    with pytest.raises(ValueError):
        WorkflowEngine(source).execute(parent)


def test_typed_inputs_round_trip(projects):
    source, target = projects
    install(source, definition('child', [{'id': 'inspect', 'type': 'boundary-probe'}],
                               inputs={'flag': {'type': 'boolean'}, 'count': {'type': 'number'}},
                               outputs={'values': {'value': '{{ steps.inspect.output.inputs }}'}}))
    values = {'flag': False, 'count': 2**60 + 1}
    state = WorkflowEngine(source).execute(definition('parent', [isolated(target, input=values)]))
    assert state.step_results['call']['output']['values'] == values
