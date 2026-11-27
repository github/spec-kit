"""Private workflow worker protocol and invocation-scoped process supervision.

Only the controller's Execution writes durable progress. A worker transition
blocks until that writer has validated and checkpointed it.
"""
from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from copy import deepcopy
import json
import ntpath
import os
from pathlib import Path, PureWindowsPath
import posixpath
import queue
import signal
import struct
import subprocess
import sys
import sysconfig
import threading
import time
import uuid

from specify_cli.integrations import _capture

MAX_FRAME = 16 * 1024 * 1024
KINDS = frozenset({
    "start", "ready", "transition", "ack", "finalize", "result", "exception",
    "interrupt", "system_exit", "cancel",
})
_scope = ContextVar("isolated_workflow_scope", default=None)
_active_lock = threading.RLock()
_active = {}
_cancelling = {}
_dependency_paths = None  # Set by stdlib bootstrap inside workers, carried into nested workers.


class ProtocolError(RuntimeError):
    """The isolated workflow did not obey its controller contract."""


class RemoteWorkflowError(RuntimeError):
    """An ordinary exception raised beyond the process boundary."""


class RemoteWorkflowBaseError(BaseException):
    """A non-interrupt, non-SystemExit BaseException from the worker."""


@contextmanager
def execution_scope(scope):
    token = _scope.set(scope)
    try:
        yield
    finally:
        _scope.reset(token)


@contextmanager
def cancel_captures():
    """Preserve capture cancellation and include this Execution's workers."""
    with cancel_workers(_scope.get()), _capture.cancel_captures():
        yield


@contextmanager
def cancel_workers(scope):
    with _active_lock:
        _cancelling[scope] = _cancelling.get(scope, 0) + 1
        workers = list(_active.get(scope, ()))
    try:
        for worker in workers:
            worker.cancel()
        yield
    finally:
        deadline = time.monotonic() + 2
        for worker in workers:
            if worker.proc is not None:
                try:
                    worker.proc.wait(timeout=max(0, deadline - time.monotonic()))
                except subprocess.TimeoutExpired:
                    pass
            worker.kill()
        with _active_lock:
            _cancelling[scope] -= 1
            if not _cancelling[scope]:
                del _cancelling[scope]


def _pairs(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise ProtocolError("Duplicate JSON key")
        value[key] = item
    return value


def _constant(value):
    raise ProtocolError("Non-finite JSON number")


def encode(message):
    from .composition import require_json
    require_json(message)
    data = json.dumps(message, ensure_ascii=True, allow_nan=False, separators=(",", ":")).encode("utf-8")
    if not 0 < len(data) <= MAX_FRAME:
        raise ProtocolError("Invalid frame length (maximum 16 MiB)")
    return struct.pack("!I", len(data)) + data


def decode(data):
    from .composition import require_json
    try:
        value = json.loads(data.decode("utf-8"), object_pairs_hook=_pairs, parse_constant=_constant)
        require_json(value)
    except (UnicodeError, ValueError, RecursionError) as exc:
        raise ProtocolError(f"Invalid protocol JSON: {exc}") from exc
    if (not isinstance(value, dict)
            or set(value) != {"version", "kind", "identity", "revision", "payload"}
            or type(value["version"]) is not int or value["version"] != 1
            or not isinstance(value["kind"], str) or value["kind"] not in KINDS
            or type(value["revision"]) is not int or value["revision"] < 0
            or not isinstance(value["payload"], dict)):
        raise ProtocolError("Invalid protocol envelope")
    identity = value["identity"]
    if (not isinstance(identity, dict) or set(identity) != {"run_id", "position", "nonce"}
            or not all(isinstance(identity[k], str) and identity[k] for k in ("run_id", "nonce"))
            or not isinstance(identity["position"], list)
            or any(type(i) is not int or i < 0 for i in identity["position"])):
        raise ProtocolError("Invalid invocation identity")
    return value


def envelope(kind, identity, revision=0, **payload):
    return {"version": 1, "kind": kind, "identity": identity, "revision": revision, "payload": payload}


def _available(pipe):
    if os.name != "nt":
        import select
        poller = select.poll()
        poller.register(pipe, select.POLLIN)
        return bool(poller.poll(50))
    import ctypes
    import msvcrt
    from ctypes import wintypes
    count = wintypes.DWORD()
    peek = ctypes.WinDLL("kernel32", use_last_error=True).PeekNamedPipe
    peek.argtypes = (wintypes.HANDLE, wintypes.LPVOID, wintypes.DWORD,
                     wintypes.LPVOID, ctypes.POINTER(wintypes.DWORD), wintypes.LPVOID)
    peek.restype = wintypes.BOOL
    if not peek(msvcrt.get_osfhandle(pipe.fileno()), None, 0, None, ctypes.byref(count), None):
        return True  # Broken pipe: read observes EOF.
    return count.value > 0


class Channel:
    """Polled reader and bounded asynchronous writes; no unbounded teardown join."""
    def __init__(self, incoming, outgoing, *, on_eof=None):
        self.incoming, self.outgoing = incoming, outgoing
        self.stop = threading.Event()
        self.messages = queue.Queue(maxsize=2)
        self.writes = queue.Queue(maxsize=1)
        self.on_eof = on_eof
        self.read_thread = threading.Thread(target=self._read, daemon=True)
        self.write_thread = threading.Thread(target=self._write, daemon=True)
        self.read_thread.start()
        self.write_thread.start()

    def _exact(self, size, *, header=False):
        result = bytearray()
        while len(result) < size:
            if self.stop.is_set():
                raise EOFError("Control closed")
            if not _available(self.incoming):
                self.stop.wait(.05)
                continue
            chunk = os.read(self.incoming.fileno(), min(size - len(result), 65536))
            if not chunk:
                if header and not result:
                    raise EOFError("Control EOF")
                raise ProtocolError("Truncated control frame")
            result.extend(chunk)
        return bytes(result)

    def _put(self, value):
        while not self.stop.is_set():
            try:
                self.messages.put(value, timeout=.05)
                return
            except queue.Full:
                pass

    def _read(self):
        try:
            while not self.stop.is_set():
                length, = struct.unpack("!I", self._exact(4, header=True))
                if not 0 < length <= MAX_FRAME:
                    raise ProtocolError("Invalid frame length (maximum 16 MiB)")
                self._put(decode(self._exact(length)))
        except BaseException as exc:
            self._put(exc)
            if self.on_eof is not None and not self.stop.is_set():
                self.on_eof()

    def _write(self):
        while not self.stop.is_set():
            try:
                data, done, outcome = self.writes.get(timeout=.05)
            except queue.Empty:
                continue
            try:
                while data:
                    count = os.write(self.outgoing.fileno(), data)
                    if count <= 0:
                        raise ProtocolError("Control write made no progress")
                    data = data[count:]
            except BaseException as exc:
                outcome.append(exc)
            finally:
                done.set()

    def send(self, message, check=lambda: None):
        data, done, outcome = encode(message), threading.Event(), []
        while True:
            check()
            if self.stop.is_set():
                raise EOFError("Control closed")
            try:
                self.writes.put((data, done, outcome), timeout=.05)
                break
            except queue.Full:
                pass
        while not done.wait(.05):
            check()
            if self.stop.is_set():
                raise EOFError("Control closed")
        if outcome:
            raise ProtocolError(f"Control write failed: {outcome[0]}") from outcome[0]

    def receive(self, check=lambda: None):
        while True:
            check()
            try:
                value = self.messages.get(timeout=.05)
            except queue.Empty:
                if self.stop.is_set():
                    raise EOFError("Control closed")
                continue
            if isinstance(value, BaseException):
                raise value
            return value

    def close(self, *, deadline=None):
        self.stop.set()
        deadline = time.monotonic() + 1 if deadline is None else deadline
        for reader in (self.read_thread, self.write_thread):
            reader.join(max(0, deadline - time.monotonic()))
        # Never close a file object whose reader holds a buffered I/O lock.
        for pipe, thread in ((self.incoming, self.read_thread), (self.outgoing, self.write_thread)):
            if not thread.is_alive():
                pipe.close()
        return not self.read_thread.is_alive() and not self.write_thread.is_alive()


class Supervisor:
    """Own one new group/job, including cancellation concurrent with launch."""
    def __init__(self, scope):
        self.scope, self.proc, self.job, self.channel = scope, None, None, None
        self.closed = False
        self.cancelled = threading.Event()
        self.lock = threading.RLock()
        self.diagnostics = bytearray()
        self.truncated = False
        self.reader_stop = threading.Event()
        self.reader = None
        with _active_lock:
            _active.setdefault(scope, set()).add(self)
            if scope in _cancelling:
                self.cancelled.set()

    def launch(self, args, root, env):
        with _capture._deferred_interrupt() as interrupted:
            with self.lock:
                if self.cancelled.is_set():
                    raise KeyboardInterrupt
                options = ({"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP | _capture._CREATE_SUSPENDED}
                           if os.name == "nt" else {"start_new_session": True})
                self.proc = subprocess.Popen(args, cwd=root, env=env, stdin=subprocess.PIPE,
                                             stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                             bufsize=0, **options)
                if os.name == "nt":
                    try:
                        self.job = _capture._start_in_job(self.proc)
                    except BaseException:
                        self.kill()
                        raise
                self.channel = Channel(self.proc.stdout, self.proc.stdin)
                self.reader = threading.Thread(target=self._drain, daemon=True)
                self.reader.start()
            if interrupted:
                self.cancel()
                raise KeyboardInterrupt
        if self.cancelled.is_set():
            self.cancel()
            raise KeyboardInterrupt

    def _drain(self):
        try:
            while not self.reader_stop.is_set():
                if not _available(self.proc.stderr):
                    self.reader_stop.wait(.05)
                    continue
                chunk = os.read(self.proc.stderr.fileno(), 65536)
                if not chunk:
                    return
                room = 65536 - len(self.diagnostics)
                self.diagnostics.extend(chunk[:room])
                self.truncated |= len(chunk) > room
        except (OSError, ValueError):
            return

    def cancel(self):
        self.cancelled.set()
        # Closing the controller's write channel lets the worker's independent
        # EOF monitor cancel nested sessions and captures before group kill.
        with self.lock:
            if self.closed:
                return
            if self.proc is not None and self.proc.stdin is not None:
                try:
                    self.proc.stdin.close()
                except OSError:
                    pass

    def kill(self):
        with self.lock:
            if self.proc is None or self.closed:
                return
            if self.job is not None:
                _capture._windows().TerminateJobObject(self.job, 1)
            elif os.name != "nt":
                try:
                    os.killpg(self.proc.pid, signal.SIGKILL)
                except OSError:
                    pass
            try:
                self.proc.kill()
            except OSError:
                pass

    def close(self, *, cancel=False):
        complete = True
        if self.proc is not None:
            if cancel:
                self.cancel()
                try:
                    self.proc.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    pass
                self.kill()  # Also kill still-owned descendants after direct exit.
            try:
                self.proc.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self.kill()
                complete = False
            drain_deadline = time.monotonic() + 1
            if self.channel is not None:
                complete &= self.channel.close(deadline=drain_deadline)
            if self.reader is not None:
                self.reader.join(timeout=max(0, drain_deadline - time.monotonic() - .1))
                self.reader_stop.set()
                self.reader.join(timeout=max(0, drain_deadline - time.monotonic()))
                complete &= not self.reader.is_alive()
                if not self.reader.is_alive():
                    self.proc.stderr.close()
            if self.job is not None:
                _capture._windows().CloseHandle(self.job)
                self.job = None
        with self.lock:
            self.closed = True
        with _active_lock:
            group = _active.get(self.scope)
            if group is not None:
                group.discard(self)
                if not group:
                    del _active[self.scope]
        return complete


def structural_occurrences(boundary):
    """Derive all transport/reporting identities from the local frozen tree."""
    from ._execution import Occurrence, child_steps, loop_alias_for, qualified_id
    from .base import StepContext
    yield (), boundary

    def walk(seq, steps, position, path, ancestry, loop_alias=None):
        for index, (raw, node) in enumerate(zip(steps, seq["nodes"])):
            config = {"id": f"step-{index}", **raw}
            name = config["id"]
            qualified = qualified_id(name, loop_alias)
            here = (*position, index)
            occurrence = Occurrence(config, node, StepContext(), ancestry, (*path, index), False, qualified)
            yield here, occurrence
            kind = config.get("type")
            for item, child in enumerate(node.get("children", [])):
                child_ancestry = (*ancestry, node["binding"]["workflow"]) if kind == "workflow" else ancestry
                child_report = ((*occurrence.path, "workflow") if kind == "workflow"
                                else (*occurrence.path, "item", item) if kind == "fan-out"
                                else (*occurrence.path, item))
                alias = (qualified, item) if kind == "fan-out" else loop_alias_for(kind, qualified, item)
                yield from walk(child, child_steps(config, node, item), (*here, item),
                                child_report, child_ancestry, alias)

    binding = boundary.node["binding"]
    yield from walk(boundary.node["children"][0], child_steps(boundary.config, boundary.node, 0),
                    (0,), (*boundary.path, "workflow"), (*boundary.ancestry, binding["workflow"]))


def startup_args():
    import specify_cli
    from specify_cli._file_handles import installation_directory_exists
    from ._subprocess_bootstrap import verify_packages
    filename = getattr(specify_cli, "__file__", None)
    if not isinstance(filename, str) or not Path(filename).is_absolute():
        raise ProtocolError("Startup requires absolute Specify package metadata")
    package = Path(filename).parent
    verify_packages(package)
    if not installation_directory_exists(package) or not Path(sys.executable).is_absolute():
        raise ProtocolError("Startup requires a directory-backed Specify and absolute interpreter")
    dependencies = (list(_dependency_paths) if _dependency_paths is not None else
                    list(dict.fromkeys(sysconfig.get_path(key) for key in ("purelib", "platlib"))))
    if any(not path or not Path(path).is_absolute() for path in dependencies):
        raise ProtocolError("Startup requires absolute interpreter dependency directories")
    return [sys.executable, "-I", "-S", "-B", str(package / "workflows/_subprocess_bootstrap.py"),
            str(package.parent), json.dumps(dependencies)]


def input_owner(boundary, position):
    """The enclosing private input mapping, distinct from a call's own inputs."""
    owners = [(pos, local.node["binding"]) for pos, local in structural_occurrences(boundary)
              if "binding" in local.node and len(position) > len(pos)
              and tuple(position[:len(pos) + 1]) == (*pos, 0)]
    return max(owners, key=lambda item: len(item[0]))[1] if owners else None


def checked_input_update(boundary, position, inputs):
    from .composition import require_json
    owner = input_owner(boundary, position)
    if owner is None:
        if inputs is not None:
            raise ProtocolError("Input update is outside a child scope")
        return None
    if not isinstance(inputs, dict):
        raise ProtocolError("Invalid private input update")
    require_json(inputs)
    # Steps already receive mutable private inputs in-process (retry gates
    # consume verdicts). Mirror that checkpointed mapping without rebinding or
    # re-resolving defaults/auto after a completed init.
    return owner, inputs


def validate_remote_transition(local, operation, changes):
    """A snapshot in a transition cannot rewrite acknowledged descendants."""
    from ._execution import check_sequence, child_steps
    node = local.node
    if operation == "rebind":
        previous, proposed = node.get("binding", {}), changes.get("binding", {})
        if ({k: v for k, v in previous.items() if k != "inputs"}
                != {k: v for k, v in proposed.items() if k != "inputs"}):
            raise ProtocolError("Rebind changes frozen workflow metadata")
    if "children" not in changes:
        return
    children = changes["children"]
    if not isinstance(children, list):
        raise ProtocolError("Invalid transition children")
    old = node.get("children", [])
    if operation == "iterate":
        if len(children) != len(old) + 1 or children[:-1] != old:
            raise ProtocolError("Iteration rewrites acknowledged children")
        fresh = children[-1:]
    elif operation in {"expand", "bind"} and not old:
        fresh = children
    else:
        raise ProtocolError("Transition rewrites existing children")
    candidate = {**node, **changes}
    for child in fresh:
        if (not isinstance(child, dict) or not isinstance(child.get("nodes"), list)
                or any(n != {"phase": "ready"} for n in child["nodes"])):
            raise ProtocolError("New children already contain progress")
    for index, child in enumerate(children):
        from ._execution import shares_source
        if shares_source(local.config.get("type"), index):
            check_sequence(child, child_steps(local.config, candidate, index), shared=True)
        else:
            check_sequence(child)


def raise_remote(message):
    kind, payload = message["kind"], message["payload"]
    if kind == "interrupt" and not payload:
        raise KeyboardInterrupt
    if kind == "system_exit" and set(payload) == {"code"} and type(payload["code"]) in {int, str, type(None)}:
        raise SystemExit(payload["code"])
    if (kind == "exception" and set(payload) == {"category", "type", "text"}
            and isinstance(payload["category"], str) and payload["category"] in {"exception", "base"}
            and isinstance(payload["type"], str) and len(payload["type"]) <= 256
            and isinstance(payload["text"], str) and len(payload["text"]) <= 4096):
        error_class = RemoteWorkflowError if payload["category"] == "exception" else RemoteWorkflowBaseError
        raise error_class(f"{payload['type']}: {payload['text']}")
    raise ProtocolError("Invalid remote exception")


def _home_origin(value, *, windows=None):
    """Anchor the effective home before cwd changes, including nested launches."""
    windows = os.name == "nt" if windows is None else windows
    if windows:
        path = PureWindowsPath(value)
        if bool(path.drive) != bool(path.root):
            raise ProtocolError("Ambiguous drive-relative or root-relative Windows home")
    pathmod = ntpath if windows else posixpath
    # Keep lexical parents: normalizing '..' could erase a symlink component
    # that the existing home/trust checks must inspect.
    return value if pathmod.isabs(value) else pathmod.join(os.getcwd(), value)


def isolated_call(execution, occurrence):
    from .base import StepResult, StepStatus
    from .composition import check_bound_execution
    binding = occurrence.node["binding"]
    metadata = binding["execution"]
    check_bound_execution(metadata, paths=True)
    env = os.environ.copy()
    # Trust, auth and user catalog/config paths use Path.home(). Resolve its
    # platform fallback now; the execution project must not select their origin.
    # USERPROFILE takes precedence over HOMEDRIVE/HOMEPATH on Windows.
    env["USERPROFILE" if os.name == "nt" else "HOME"] = _home_origin(os.fspath(Path.home()))
    # Structural position within the durable root is distinct from reporting aliases.
    def find(seq, target, position=()):
        for i, node in enumerate(seq["nodes"]):
            if node is target:
                return (*position, i)
            for j, child in enumerate(node.get("children", [])):
                found = find(child, target, (*position, i, j))
                if found is not None:
                    return found
        return None
    position = find(execution.state.execution["sequence"], occurrence.node)
    if position is None:
        # Worker state includes its enclosing call as a one-node sequence too.
        raise ProtocolError("Call is outside the execution tree")
    identity = {"run_id": execution.state.run_id, "position": list(position), "nonce": uuid.uuid4().hex}
    supervisor = Supervisor(execution)
    timeout = metadata["timeout"]
    deadline = None if timeout is None else time.monotonic() + timeout
    normal = False
    revision = 0
    finalized = False

    def check():
        if supervisor.cancelled.is_set():
            raise KeyboardInterrupt
        if deadline is not None and time.monotonic() >= deadline:
            raise TimeoutError("Isolated workflow timeout")

    for key in tuple(env):
        if key.startswith("PYTHON") or key.startswith("SPECKIT_WORKFLOW_") or key in {"SPECKIT_PROJECT_ROOT", "SPECIFY_INIT_DIR"}:
            env.pop(key)
    env["SPECKIT_WORKFLOW_RUN_ID"] = execution.state.run_id
    if sys.dont_write_bytecode:
        # Keep the controller's no-bytecode preference for workload Python
        # subprocesses too; worker import selection remains owned by -I -S.
        env["PYTHONDONTWRITEBYTECODE"] = "1"
    if binding["workflow_dir"] is not None:
        env["SPECKIT_WORKFLOW_DIR"] = binding["workflow_dir"]
    try:
        try:
            supervisor.launch(startup_args(), metadata["project_root"], env)
        except OSError as exc:
            error = f"Isolated workflow launch: {exc}"
            return StepResult(StepStatus.FAILED,
                              output={"workflow": binding["workflow"], "status": "failed", "error": error}, error=error)
        channel = supervisor.channel
        channel.send(envelope("start", identity, node=deepcopy(occurrence.node),
                              config=occurrence.config, ancestry=list(occurrence.ancestry),
                              path=list(occurrence.path), qualified=occurrence.qualified,
                              is_resume=occurrence.context.is_resume,
                              inside_fan_out=occurrence.context.inside_fan_out, rebind=execution.rebind), check)
        message = channel.receive(check)
        if message != envelope("ready", identity):
            if message["identity"] == identity and message["revision"] == 0 and message["kind"] in {"exception", "interrupt", "system_exit"}:
                raise_remote(message)
            raise ProtocolError("Invalid worker startup handshake")
        while True:
            message = channel.receive(check)
            if message["identity"] != identity:
                raise ProtocolError("Incorrect invocation identity")
            kind, payload = message["kind"], message["payload"]
            expected = revision + 1 if kind == "transition" else revision
            if message["revision"] != expected:
                raise ProtocolError("Stale or invalid transition revision")
            if kind == "transition" and not finalized:
                if (set(payload) != {"position", "operation", "changes", "publish", "announce", "inputs"}
                        or not isinstance(payload["position"], list)
                        or any(type(i) is not int or i < 0 for i in payload["position"])
                        or not isinstance(payload["changes"], dict)
                        or type(payload["publish"]) is not bool or type(payload["announce"]) is not bool):
                    raise ProtocolError("Invalid transition fields")
                with execution.state._lock:
                    local = dict(structural_occurrences(occurrence)).get(tuple(payload["position"]))
                    if local is None or (not payload["position"] and payload["operation"] not in {"outputs", "leave"}):
                        raise ProtocolError("Transition is outside the child subtree")
                    if not isinstance(payload["operation"], str) or payload["operation"] not in {"begin", "expand", "bind", "rebind", "iterate", "outputs", "finish", "settle", "leave"}:
                        raise ProtocolError("Unknown transition operation")
                    validate_remote_transition(local, payload["operation"], payload["changes"])
                    input_update = checked_input_update(occurrence, payload["position"], payload["inputs"])
                    execution.transition(payload["operation"], local, payload["changes"],
                                         publish=payload["publish"], announce=payload["announce"],
                                         input_update=input_update)
                revision += 1
                channel.send(envelope("ack", identity, revision), check)
            elif kind == "finalize" and not finalized and not payload:
                finalized = True
                channel.send(envelope("ack", identity, revision), check)
            elif kind == "result" and finalized:
                if (set(payload) != {"status", "output", "error"}
                        or not isinstance(payload["status"], str) or payload["status"] not in {"completed", "failed", "paused"}
                        or not isinstance(payload["output"], dict)
                        or not isinstance(payload["error"], (str, type(None)))):
                    raise ProtocolError("Invalid worker result")
                output = payload["output"]
                definition = __import__("yaml").safe_load(binding["definition"])
                allowed = {"workflow", "status", "error", "aborted", *definition.get("outputs", {})}
                if (output.keys() - allowed or output.get("workflow") != binding["workflow"]
                        or not isinstance(output.get("status"), str)
                        or output["status"] not in {"completed", "failed", "paused", "aborted"}
                        or payload["status"] != {"aborted": "failed"}.get(output["status"], output["status"])
                        or output.get("error") != payload["error"]
                        or ("aborted" in output and (output["status"] != "aborted" or output["aborted"] is not True))
                        or (output["status"] == "aborted" and output.get("aborted") is not True)
                        or (payload["status"] == "completed" and set(output) != {"workflow", "status", *definition.get("outputs", {})})
                        or (payload["status"] == "completed" and occurrence.node["phase"] != "outputs")):
                    raise ProtocolError("Invalid workflow result contract")
                # Require EOF, no additional frame, and successful direct worker exit.
                try:
                    extra = channel.receive(check)
                except EOFError:
                    pass
                else:
                    raise ProtocolError(f"Trailing worker message: {extra['kind']}")
                exit_deadline = time.monotonic() + 2
                while supervisor.proc.poll() is None and time.monotonic() < exit_deadline:
                    check()
                    time.sleep(.02)
                if supervisor.proc.poll() != 0:
                    raise ProtocolError("Worker exit was not successful")
                normal = True
                return StepResult(StepStatus(payload["status"]), output=output, error=payload["error"])
            elif kind in {"exception", "interrupt", "system_exit"} and not finalized:
                raise_remote(message)
            else:
                raise ProtocolError("Unexpected worker message")
    except TimeoutError:
        return StepResult(StepStatus.FAILED, output={"workflow": binding["workflow"], "status": "failed", "error": "Isolated workflow timeout"},
                          error="Isolated workflow timeout")
    except EOFError as exc:
        raise ProtocolError("Worker startup/control EOF before a complete result") from exc
    finally:
        pending_error = sys.exception()
        complete = supervisor.close(cancel=not normal)
        # Retained diagnostics are scoped evidence, never part of call outputs.
        if supervisor.diagnostics and not execution.state._checkpoint_failed:
            execution.state.append_log({"event": "workflow_worker_diagnostics", "step_id": occurrence.qualified,
                                        "execution_path": list(occurrence.path),
                                        "workflow_id": binding["workflow"],
                                        "diagnostics": supervisor.diagnostics.decode("utf-8", errors="replace"),
                                        "truncated": supervisor.truncated})
        if not complete:
            if pending_error is not None:
                pending_error.add_note("Isolated workflow teardown unfinished within bounds")
            else:
                raise ProtocolError("Isolated workflow teardown unfinished within bounds")
