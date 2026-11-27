"""Transport parsing, durable scope validation and real hostile worker peers."""
from copy import deepcopy
import json
import os
from pathlib import Path
import struct
import sys

import pytest

from specify_cli.workflows._subprocess import Channel, ProtocolError, decode, encode, envelope
from specify_cli.workflows._execution import check_sequence, validate_execution
from tests.workflows.test_composition_execution import definition, install
from tests.workflows.test_subprocess_composition import isolated
from tests.workflows import test_subprocess_composition as composition_tests
from specify_cli.workflows.engine import WorkflowEngine, RunState

IDENTITY = {"run_id": "parent-run", "position": [1, 0, 2], "nonce": "attempt"}
projects = composition_tests.projects


def test_large_unicode_lossless_frame():
    message = envelope("start", IDENTITY, value=["中文 ü" * 100000, False, None, 12, {"number": 1.25}])
    framed = encode(message)
    assert struct.unpack('!I', framed[:4])[0] == len(framed) - 4
    assert decode(framed[4:]) == message


@pytest.mark.parametrize("raw", [b'{}', b'[]', b'null', b'\xff', b'{"version":1,"version":1}',
                                  b'{"a":NaN}', b'{"a":Infinity}', b'{"a":1e999}', b'{} {}'])
def test_bad_json_and_envelopes(raw):
    with pytest.raises(ProtocolError):
        decode(raw)


@pytest.mark.parametrize("field,value", [("version", True), ("version", 2), ("kind", "unknown"),
                                         ("kind", []), ("revision", True), ("revision", -1),
                                         ("payload", []), ("identity", {}),
                                         ("identity", {**IDENTITY, "position": [True]})])
def test_strict_envelope_types(field, value):
    message = envelope("ready", IDENTITY)
    message[field] = value
    with pytest.raises(ProtocolError):
        decode(json.dumps(message).encode())


@pytest.mark.parametrize("data", [struct.pack('!I', 0), struct.pack('!I', 16 * 1024 * 1024 + 1),
                                   b'\x00\x00', struct.pack('!I', 10) + b'{}'])
def test_pipe_truncation_and_lengths(data):
    read_fd, write_fd = os.pipe()
    unused_read, outgoing_fd = os.pipe()
    with os.fdopen(write_fd, 'wb', buffering=0) as writer:
        writer.write(data)
    channel = Channel(os.fdopen(read_fd, 'rb', buffering=0), os.fdopen(outgoing_fd, 'wb', buffering=0))
    try:
        with pytest.raises(ProtocolError):
            channel.receive()
    finally:
        assert channel.close()
        os.close(unused_read)


def test_encode_refuses_loss_and_oversize():
    for value in (object(), (1, 2), float('nan')):
        with pytest.raises(ValueError):
            encode(envelope('start', IDENTITY, value=value))
    with pytest.raises(ProtocolError, match='length'):
        encode(envelope('start', IDENTITY, value='x' * (16 * 1024 * 1024)))


@pytest.mark.parametrize("mode", ['escape', 'outer-finish', 'stale', 'nonce', 'unknown-envelope',
                                  'invalid-fields', 'forged-progress', 'final-only', 'early-outputs'])
def test_real_controller_rejects_invalid_peer_without_child_effect(projects, monkeypatch, mode):
    from specify_cli.workflows import _subprocess
    source, target = projects
    install(source, definition('child', [{'id': 'effect', 'type': 'boundary-probe', 'effect': 'effect'}]))
    script = Path(__file__).parent / 'fixtures/subprocess/adversary.py'
    monkeypatch.setattr(_subprocess, 'startup_args', lambda: [sys.executable, '-I', '-S', '-B', str(script), mode])
    with pytest.raises((ProtocolError, ValueError)):
        WorkflowEngine(source).execute(definition('parent', [isolated(target)]))
    run_id = next((source / '.specify/workflows/runs').iterdir()).name
    saved = RunState.load(run_id, source)
    assert saved.execution['sequence']['nodes'][0]['children'][0]['nodes'] == [{'phase': 'ready'}]
    assert not (target / 'effect').exists()


def test_strict_shared_shapes():
    for value in ({'nodes': [], 'extra': 1}, {'nodes': [], 'source': ''}, {'nodes': [], 'binding': {}}):
        with pytest.raises(ValueError):
            check_sequence(value, [], shared=True)


def test_persisted_metadata_rejected_before_launch(projects, monkeypatch):
    from specify_cli.workflows import _subprocess
    source, target = projects
    install(source, definition('child', [{'id': 'wait', 'type': 'gate', 'message': 'Review'}]))
    state = WorkflowEngine(source).execute(definition('parent', [isolated(target)]))
    tree = deepcopy(state.execution)
    metadata = tree['sequence']['nodes'][0]['binding']['execution']
    for field, value in [('mode', 'in-process'), ('project_root', 'relative'), ('timeout', True), ('extra', 1)]:
        bad = deepcopy(tree)
        bad['sequence']['nodes'][0]['binding']['execution'][field] = value
        with pytest.raises(ValueError):
            validate_execution(bad)
    assert metadata['project_root'] == str(target)
    monkeypatch.setattr(_subprocess.Supervisor, 'launch', lambda *a: pytest.fail('must not launch'))
    # A frozen root that disappears must fail rather than silently use cwd.
    moved = target.with_name('moved')
    target.rename(moved)
    with pytest.raises(ValueError, match='bound execution root'):
        WorkflowEngine(source).resume(state.run_id)


def test_cancellation_registration_covers_launch(monkeypatch, tmp_path):
    from specify_cli.workflows._subprocess import Supervisor, cancel_workers
    scope = object()
    supervisor = Supervisor(scope)
    with cancel_workers(scope):
        pass
    monkeypatch.setattr('subprocess.Popen', lambda *a, **k: pytest.fail('cancelled launch must not spawn'))
    try:
        with pytest.raises(KeyboardInterrupt):
            supervisor.launch([], str(tmp_path), {})
    finally:
        assert supervisor.close()


def test_remote_iteration_cannot_replace_completed_nodes():
    from specify_cli.workflows._execution import Occurrence
    from specify_cli.workflows.base import StepContext
    from specify_cli.workflows._subprocess import validate_remote_transition
    child = {'nodes': [{'phase': 'done', 'result': {'status': 'completed', 'output': {}}}], 'source': '- id: old'}
    node = {'phase': 'children', 'children': [child]}
    local = Occurrence({'id': 'loop', 'type': 'while'}, node, StepContext(), ('root',), (), False, 'loop')
    rewritten = deepcopy(child)
    rewritten['nodes'][0]['result']['output'] = {'changed': True}
    with pytest.raises(ProtocolError, match='rewrites'):
        validate_remote_transition(local, 'iterate', {'children': [rewritten, {'nodes': [{'phase': 'ready'}]}]})


def test_cancellation_during_actual_launch_is_rechecked(monkeypatch, tmp_path):
    from specify_cli.workflows._subprocess import Supervisor
    import subprocess
    supervisor = Supervisor(object())
    original = subprocess.Popen

    def spawn(*args, **kwargs):
        process = original(*args, **kwargs)
        supervisor.cancel()  # Registration exists, but proc assignment has not happened.
        return process

    monkeypatch.setattr(subprocess, 'Popen', spawn)
    try:
        with pytest.raises(KeyboardInterrupt):
            supervisor.launch([sys.executable, '-I', '-S', '-B', '-c', 'import sys; sys.stdin.read()'], str(tmp_path), os.environ.copy())
    finally:
        assert supervisor.close(cancel=True)
    assert supervisor.proc.poll() is not None


def test_package_identity_uses_directories_even_with_shared_initializer(tmp_path, monkeypatch):
    import importlib.machinery
    from types import ModuleType
    from specify_cli.workflows._subprocess_bootstrap import verify_packages
    import specify_cli
    package = Path(specify_cli.__file__).parent
    other = tmp_path / 'other-package'
    other.mkdir()
    initializer = other / '__init__.py'
    composition_tests.symlink_or_skip(initializer, package / '__init__.py')
    module = ModuleType('specify_cli.forged')
    module.__file__ = str(initializer)
    module.__path__ = [str(other)]
    module.__spec__ = importlib.machinery.ModuleSpec('specify_cli.forged', loader=None, origin=str(initializer), is_package=True)
    module.__spec__.has_location = True
    module.__spec__.submodule_search_locations = [str(other)]
    monkeypatch.setitem(sys.modules, 'specify_cli.forged', module)
    with pytest.raises((RuntimeError, OSError)):
        verify_packages(package)


@pytest.mark.parametrize("failure", [False, True])
def test_real_bootstrap_isolates_noisy_package_import_before_application(tmp_path, failure):
    import subprocess
    import specify_cli
    bootstrap = Path(specify_cli.__file__).parent / 'workflows/_subprocess_bootstrap.py'
    source = tmp_path / 'source'
    package = source / 'specify_cli'
    workflows = package / 'workflows'
    workflows.mkdir(parents=True)
    (package / '__init__.py').write_text(
        "import os, sys\n"
        "assert sys.stdin.read() == ''\n"
        "assert 'specify_cli._file_handles' not in sys.modules\n"
        "print('python-startup-noise')\n"
        "os.write(1, b'native-startup-noise\\n')\n"
        + ("raise RuntimeError('startup sentinel')\n" if failure else ""))
    (workflows / '__init__.py').write_text('')
    (workflows / '_subprocess.py').write_text('')
    (workflows / '_subprocess_worker.py').write_text(
        "import os, sys\n"
        "def run(incoming, outgoing, verify):\n"
        "    verify()\n"
        "    assert incoming.read() == b'controller'\n"
        "    assert sys.stdin.read() == ''\n"
        "    assert not os.get_inheritable(incoming.fileno())\n"
        "    assert not os.get_inheritable(outgoing.fileno())\n"
        "    outgoing.write(b'CONTROL')\n")
    # Neither the supplied application tree nor cwd may supply the native helper.
    for parent in (package, tmp_path):
        (parent / '_file_handles.py').write_text("raise AssertionError('untrusted helper')\n")
    env = {**os.environ, 'PYTHONPATH': str(tmp_path)}
    result = subprocess.run([sys.executable, '-I', '-S', '-B', str(bootstrap), str(source), '[]'],
                            cwd=tmp_path, env=env, input=b'controller', capture_output=True, timeout=15)
    assert result.returncode == (1 if failure else 0), result.stderr.decode(errors='replace')
    assert result.stdout == (b'' if failure else b'CONTROL')
    assert b'python-startup-noise' in result.stderr and b'native-startup-noise' in result.stderr
    assert b'untrusted helper' not in result.stderr
    if failure:
        assert b'startup sentinel' in result.stderr


def test_bootstrap_adjacent_helper_requires_absolute_location_and_cleans_failed_import(tmp_path, monkeypatch):
    from specify_cli.workflows import _subprocess_bootstrap as bootstrap
    monkeypatch.setattr(bootstrap, '__file__', 'relative.py')
    with pytest.raises(RuntimeError, match='absolute'):
        bootstrap._load_handles()
    selected = tmp_path / 'selected'
    (selected / 'workflows').mkdir(parents=True)
    (selected / '_file_handles.py').write_text("raise RuntimeError('helper setup failure')\n")
    monkeypatch.setattr(bootstrap, '__file__', str(selected / 'workflows/_subprocess_bootstrap.py'))
    with pytest.raises(RuntimeError, match='helper setup failure'):
        bootstrap._load_handles()
    assert '_specify_workflow_file_handles' not in sys.modules


def test_package_identity_accepts_os_directory_alias_and_preserves_errors(tmp_path, monkeypatch):
    from specify_cli.workflows._subprocess_bootstrap import verify_packages
    from specify_cli import _file_handles
    import specify_cli
    alias = tmp_path / 'package-alias'
    composition_tests.symlink_or_skip(alias, Path(specify_cli.__file__).parent, directory=True)
    verify_packages(alias)

    def denied(*args):
        raise PermissionError('identity probe denied')

    monkeypatch.setattr(_file_handles, 'same_installation_directory', denied)
    with pytest.raises(PermissionError, match='identity probe denied'):
        verify_packages(alias)
