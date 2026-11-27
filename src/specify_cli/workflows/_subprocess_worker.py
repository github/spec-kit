"""Production worker: common Execution traversal with a synchronous transition sink."""
from __future__ import annotations

from copy import deepcopy
import os
import json
from pathlib import Path
import sys
import threading
from types import SimpleNamespace

import yaml

from ._subprocess import (
    Channel, ProtocolError, cancel_captures, encode, envelope, execution_scope,
    structural_occurrences, input_owner,
)


def run(incoming, outgoing, verify_packages):
    from . import STEP_REGISTRY, load_custom_steps
    from ._execution import Execution, Occurrence, check_node, check_sequence
    from .base import StepContext
    from .composition import check_bound_execution
    from .engine import WorkflowDefinition, WorkflowEngine, validate_workflow
    from .function import load_workflow_functions

    executor = None
    finished = threading.Event()

    def lost_controller():
        # Independent of the workload thread, which may be blocked in a step.
        # Nested workers own separate groups; close their control first.
        if finished.is_set():
            return
        with execution_scope(executor), cancel_captures():
            pass
        os._exit(1)

    channel = Channel(incoming, outgoing, on_eof=lost_controller)
    identity = None
    revision = 0
    lock = threading.RLock()
    try:
        start = channel.receive()
        if start["kind"] != "start" or start["revision"] != 0:
            raise ProtocolError("Expected initial start frame")
        identity, payload = start["identity"], start["payload"]
        if (set(payload) != {"node", "config", "ancestry", "path", "qualified", "is_resume", "inside_fan_out", "rebind"}
                or not isinstance(payload["config"], dict)
                or payload["config"].get("type") != "workflow"
                or not isinstance(payload["ancestry"], list)
                or not payload["ancestry"] or any(not isinstance(p, str) for p in payload["ancestry"])
                or not isinstance(payload["path"], list)
                or any(type(p) not in {int, str} for p in payload["path"])
                or not isinstance(payload["qualified"], str)
                or any(type(payload[k]) is not bool for k in ("is_resume", "inside_fan_out", "rebind"))):
            raise ProtocolError("Invalid start payload")
        node = payload["node"]
        check_node(payload["config"], node)
        binding = node["binding"]
        metadata = binding["execution"]
        check_bound_execution(metadata, paths=True)
        root, source = Path(metadata["project_root"]), Path(metadata["source_root"])
        definition = WorkflowDefinition(yaml.safe_load(binding["definition"]))
        check_sequence(node["children"][0], definition.steps, shared=True)
        load_custom_steps(source)
        load_workflow_functions(source)
        engine = WorkflowEngine(root)
        engine._load_integrations()
        errors = validate_workflow(definition)
        if errors:
            raise ProtocolError("Invalid frozen worker workflow: " + "; ".join(errors))
        verify_packages()
        def diagnostic_log(entry):
            if entry.get("event") == "workflow_worker_diagnostics":
                print(json.dumps(entry, ensure_ascii=False), file=sys.stderr)

        state = SimpleNamespace(
            project_root=root, run_id=identity["run_id"],
            _lock=threading.RLock(), _checkpoint_failed=False,
            current_step_id=None, current_step_index=0, step_results={},
            execution={"sequence": {"nodes": [node]}},
            save=lambda: None, append_log=diagnostic_log,
        )
        context = StepContext(project_root=str(root), run_id=identity["run_id"],
                              is_resume=payload["is_resume"], inside_fan_out=payload["inside_fan_out"])
        boundary = Occurrence(payload["config"], node, context, tuple(payload["ancestry"]),
                              tuple(payload["path"]), False, payload["qualified"])

        def ack():
            message = channel.receive()
            if message != envelope("ack", identity, revision):
                raise ProtocolError("Invalid checkpoint ACK")

        def transition(operation, occurrence, changes, publish, announce, input_update):
            nonlocal revision
            with lock:
                position = next((pos for pos, local in structural_occurrences(boundary)
                                 if local.node is occurrence.node), None)
                if position is None:
                    raise ProtocolError("Worker transition outside child subtree")
                owner = input_owner(boundary, position)
                inputs = input_update[1] if input_update is not None else owner["inputs"] if owner is not None else None
                message = envelope("transition", identity, revision + 1,
                                   position=list(position), operation=operation, changes=deepcopy(changes),
                                   publish=publish, announce=announce, inputs=deepcopy(inputs))
                encode(message)  # A rejected value has not consumed a revision.
                revision += 1
                channel.send(message)
                ack()

        executor = Execution(engine, state, STEP_REGISTRY, rebind=payload["rebind"],
                             transition_sink=transition, source_root=source)
        channel.send(envelope("ready", identity))
        with execution_scope(executor):
            result = executor.bound_workflow(boundary, definition)
        with lock:
            channel.send(envelope("finalize", identity, revision))
            ack()
            channel.send(envelope("result", identity, revision, status=result.status.value,
                                  output=result.output, error=result.error))
        finished.set()
    except BaseException as exc:
        if identity is not None:
            with lock:
                if isinstance(exc, KeyboardInterrupt):
                    message = envelope("interrupt", identity, revision)
                elif isinstance(exc, SystemExit):
                    code = exc.code
                    if type(code) not in {str, int, type(None)}:
                        message = envelope("exception", identity, revision, category="base", type="SystemExit",
                                           text="Remote SystemExit code must be an int, string or null")
                    else:
                        message = envelope("system_exit", identity, revision, code=code)
                else:
                    message = envelope("exception", identity, revision,
                                       category="exception" if isinstance(exc, Exception) else "base",
                                       type=type(exc).__name__[:256], text=str(exc)[:4096])
                try:
                    channel.send(message)
                except (OSError, EOFError, ProtocolError):
                    pass
        else:
            raise
        finished.set()
    finally:
        finished.set()
        with execution_scope(executor), cancel_captures():
            pass
        channel.close()
