"""A persisted execution tree, traversed identically on first execution and resume.

An occurrence owns its result and descendants. Authored names are only aliases
in an expression context; tree positions distinguish repeated executions.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from dataclasses import dataclass, replace
import threading
from typing import Any

import yaml

from .base import StepContext, StepResult, StepStatus
from .composition import (
    CallError,
    bind_inputs,
    evaluate_outputs,
    resolve_target,
    validate_runtime_call,
)
from .expressions import evaluate_condition, evaluate_expression

HALTING = {"paused", "failed", "aborted"}
EXECUTION_VERSION = 2

def unknown_step_error(kind):
    return f"Unknown step type: {kind!r}"


class CheckpointError(RuntimeError):
    """Persistence failed; reload the authoritative disk checkpoint before retrying."""


def sequence(steps: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "source": yaml.safe_dump(steps, sort_keys=False),
        "nodes": [{"phase": "ready"} for _ in steps],
    }


def occurrences(steps: list[dict[str, Any]]) -> dict[str, Any]:
    """Create occurrence storage that shares its parent's immutable source."""
    return {"nodes": [{"phase": "ready"} for _ in steps]}


def new_execution(
    steps: list[dict[str, Any]], offset: int, initial: dict[str, Any]
) -> dict[str, Any]:
    """Create the persisted root execution tree."""
    return {
        "version": EXECUTION_VERSION,
        "sequence": sequence(steps),
        "offset": max(0, offset),
        "initial": deepcopy(initial),
    }


def steps_of(seq: dict[str, Any]) -> Any:
    """Read the persisted YAML source for one execution sequence."""
    return yaml.safe_load(seq["source"])


LOOP_TYPES = frozenset({"while", "do-while"})
TRANSITIONS = {
    "begin": (frozenset({"ready", "blocked", "children", "outputs"}), frozenset()),
    "expand": (frozenset({"ready", "blocked"}), frozenset({"result", "children", "template"})),
    "bind": (frozenset({"ready", "blocked"}), frozenset({"binding", "children"})),
    "rebind": (frozenset({"children", "blocked", "outputs"}), frozenset({"binding"})),
    "iterate": (frozenset({"children"}), frozenset({"children"})),
    "outputs": (frozenset({"children", "blocked", "outputs"}), frozenset()),
    "finish": (frozenset({"ready", "blocked", "children", "outputs"}), frozenset({"result", "outcome", "error"})),
    "settle": (frozenset({"children"}), frozenset({"outcome", "error", "fan_results"})),
    "leave": (frozenset({"ready", "blocked", "children", "outputs", "done"}), frozenset()),
}


def shares_source(kind, index):
    """Whether child ``index`` reads its steps from the parent occurrence."""
    return kind in {"workflow", "fan-out"} or (kind in LOOP_TYPES and index > 0)


def child_steps(config, node, index):
    """Read a child sequence from its position in the parent occurrence."""
    kind = config.get("type")
    if not shares_source(kind, index):
        return steps_of(node["children"][index])
    if kind == "workflow":
        return yaml.safe_load(node["binding"]["definition"])["steps"]
    if kind == "fan-out":
        template = yaml.safe_load(node["template"])
        return [{"id": "item", **template}]
    return steps_of(node["children"][0])


def child_path(config, path, item):
    """Return a child's reporting path from its parent occurrence."""
    return (
        [*path, str(item)]
        if config.get("type") in {"fan-out"} | LOOP_TYPES
        else path
    )


def walk_execution(
    seq,
    path=(),
    *,
    children_first=False,
    skip_done=False,
    steps=None,
    loop_alias=None,
):
    """Yield execution occurrences with one shared path and ID rule.

    Each item is ``(config, node, path, step_id)``; ``step_id`` is the
    occurrence ID used by events, relative to the enclosing workflow scope.
    """
    steps = steps_of(seq) if steps is None else steps
    for index, (config, node) in enumerate(zip(steps, seq["nodes"])):
        if skip_done and node["phase"] == "done":
            continue
        name = config.get("id", f"step-{index}")
        here = [*path, name]
        qualified = qualified_id(name, loop_alias)
        kind = config.get("type", "command")
        if not children_first:
            yield config, node, here, qualified
        for item, child in enumerate(node.get("children", [])):
            yield from walk_execution(
                child,
                child_path(config, here, item),
                children_first=children_first,
                skip_done=skip_done,
                steps=child_steps(config, node, item),
                loop_alias=(
                    (qualified, item)
                    if kind == "fan-out"
                    else loop_alias_for(kind, qualified, item)
                ),
            )
        if children_first:
            yield config, node, here, qualified


def check_sequence(seq, steps=None, *, shared=False):
    """Walk a stored sequence, checking every occurrence and its descendants."""
    if not isinstance(seq, dict) or (shared and "source" in seq):
        raise ValueError("Invalid execution sequence")
    if shared:
        if not isinstance(steps, list):
            raise ValueError("Invalid shared execution source")
    else:
        if not isinstance(seq.get("source"), str):
            raise ValueError("Invalid execution sequence")
        steps = steps_of(seq)
    nodes = seq.get("nodes")
    if (
        not isinstance(steps, list)
        or not all(isinstance(s, dict) for s in steps)
        or not isinstance(nodes, list)
        or len(nodes) != len(steps)
    ):
        raise ValueError("Invalid execution sequence length or steps")
    for step, node in zip(steps, nodes):
        check_node(step, node)
        for index, child in enumerate(node.get("children", [])):
            if shares_source(step.get("type"), index):
                check_sequence(child, child_steps(step, node, index), shared=True)
            else:
                check_sequence(child)


def check_node(step, node, *, changed=None, new_children=()):
    """Validate one occurrence and its direct children without walking descendants.

    On a transition, unchanged YAML sources and existing child shapes were
    checked when they were created or loaded. Load checks everything.
    """
    if not isinstance(node, dict) or node.get("phase") not in {
        "ready", "children", "outputs", "blocked", "done",
    }:
        raise ValueError("Invalid execution phase")
    result = node.get("result")
    if result is not None and (
        not isinstance(result, dict)
        or result.get("status") not in {s.value for s in StepStatus}
        or not isinstance(result.get("output"), dict)
    ):
        raise ValueError("Invalid execution result")
    if node["phase"] == "done" and result is None:
        raise ValueError("Completed execution lacks a result")
    if "active" in node and type(node["active"]) is not bool:
        raise ValueError("Invalid execution activity")
    if node["phase"] == "done" and node.get("active"):
        raise ValueError("Completed execution is still active")
    if node.get("outcome", "completed") not in {"completed", *HALTING}:
        raise ValueError("Invalid execution outcome")
    if node["phase"] == "done" and node.get("outcome", "completed") != "completed":
        raise ValueError("Completed execution has a blocking outcome")
    if node["phase"] == "blocked" and (
        result is None or result["status"] not in {"failed", "paused"}
        or node.get("outcome") not in HALTING
    ):
        raise ValueError("Blocked execution lacks a blocking result")
    children = node.get("children", [])
    if not isinstance(children, list):
        raise ValueError("Invalid execution children")
    kind = step.get("type")
    if "fan_results" in node and (
        kind != "fan-out" or not isinstance(node["fan_results"], list)
    ):
        raise ValueError("Invalid fan-out aggregate results")
    if "template" in node and (kind != "fan-out" or not isinstance(node["template"], str)):
        raise ValueError("Invalid fan-out template")
    binding = node.get("binding")
    if binding is not None:
        if kind != "workflow" or not isinstance(binding, dict):
            raise ValueError("Invalid workflow binding")
        if changed is None or "binding" in changed:
            source = binding.get("definition")
            if not isinstance(source, str):
                raise ValueError("Invalid bound workflow definition or inputs")
            bound_definition = yaml.safe_load(source)
            if (
                not isinstance(bound_definition, dict)
                or not isinstance(bound_definition.get("workflow"), dict)
                or bound_definition["workflow"].get("id") != binding.get("workflow")
                or not isinstance(binding.get("inputs"), dict)
                or "workflow_dir" not in binding
                or not isinstance(binding["workflow_dir"], (str, type(None)))
                or len(children) != 1
                or not isinstance(bound_definition.get("steps"), list)
            ):
                raise ValueError("Invalid bound workflow definition or inputs")
    elif kind == "workflow" and children:
        raise ValueError("Workflow children require a binding")
    if kind == "fan-out" and children and (changed is None or "template" in changed):
        source = node.get("template")
        template = yaml.safe_load(source) if isinstance(source, str) else None
        if not isinstance(template, dict):
            raise ValueError("Invalid fan-out template")
    if changed is None or new_children:
        shared_steps = None
        for index, child in enumerate(children):
            if changed is not None and not any(child is fresh for fresh in new_children):
                continue
            if shares_source(kind, index):
                if shared_steps is None:
                    shared_steps = child_steps(step, node, index)
                check_sequence_shape(child, shared_steps, shared=True)
            else:
                check_sequence_shape(child)
    handled_child_failure = (
        kind == "workflow" and step.get("continue_on_error") is True
        and node.get("outcome") == "completed" and result is not None
        and result["status"] == "failed"
    )
    if node["phase"] == "done" and not handled_child_failure:
        for child in children:
            if any(nested["phase"] != "done" for nested in child["nodes"]):
                raise ValueError("Completed execution has unfinished children")
    if node["phase"] == "outputs" and binding is None:
        raise ValueError("Output finalization requires a workflow binding")
    if node["phase"] == "children" and (
        not children or (binding is None and result is None)
    ):
        raise ValueError("Expanded execution lacks its children or result")
    if node["phase"] == "ready" and (result is not None or children or binding):
        raise ValueError("Unstarted execution already has progress")
    if kind == "fan-out" and children:
        items = (result or {}).get("output", {}).get("items")
        if not isinstance(items, list) or len(items) != len(children):
            raise ValueError("Fan-out items do not match execution children")


def check_sequence_shape(seq, steps=None, *, shared=False):
    """Check a newly attached child sequence without visiting its nodes' descendants."""
    if not isinstance(seq, dict) or (shared and "source" in seq):
        raise ValueError("Invalid execution sequence")
    if shared:
        if not isinstance(steps, list):
            raise ValueError("Invalid shared execution source")
    else:
        if not isinstance(seq.get("source"), str):
            raise ValueError("Invalid execution sequence")
        steps = steps_of(seq)
    nodes = seq.get("nodes")
    if (
        not isinstance(steps, list) or not all(isinstance(s, dict) for s in steps)
        or not isinstance(nodes, list) or len(nodes) != len(steps)
    ):
        raise ValueError("Invalid execution sequence length or steps")


def validate_execution(tree: Any, *, workflow_steps=None, current_step_index=None) -> None:
    """Validate stored structure without importing a project's custom steps."""

    try:
        if not isinstance(tree, dict) or tree.get("version") != EXECUTION_VERSION:
            raise ValueError("Unsupported execution version")
        offset = tree.get("offset", 0)
        if (
            type(offset) is not int
            or offset < 0
            or not isinstance(tree.get("initial", {}), dict)
        ):
            raise ValueError("Invalid execution offset or initial aliases")
        check_sequence(tree["sequence"])
        if workflow_steps is not None:
            if offset >= len(workflow_steps) or offset > current_step_index:
                raise ValueError("Invalid execution offset for workflow position")
            if steps_of(tree["sequence"]) != workflow_steps[offset:]:
                raise ValueError("Invalid execution state: root sequence differs from workflow snapshot")
    except (KeyError, TypeError, yaml.YAMLError, RecursionError) as exc:
        raise ValueError(f"Invalid execution state: {exc}") from exc


def active_step(tree):
    """First unfinished leaf in execution order, including nested workflow scopes.

    Returns ``(path, node, step_id)``.
    """
    for _, node, path, step_id in walk_execution(
        tree["sequence"], children_first=True, skip_done=True
    ):
        return path, node, step_id
    return None


def bound_scopes(tree):
    """Yield (path, binding) for every bound workflow call, in execution order."""
    for _, node, path, _ in walk_execution(tree["sequence"]):
        if binding := node.get("binding"):
            yield path, binding


def scope_summaries(tree, run_status="running"):
    """Report workflow boundaries without exposing private inputs or results.

    Only an unfinished scope containing the active occurrence inherits a
    terminal run status; completed scopes retain their recorded result.
    """
    summaries = []
    active = active_step(tree)
    active_path = active[0] if active is not None else ()
    nodes_by_path = {
        tuple(path): node for _, node, path, _ in walk_execution(tree["sequence"])
    }
    for path, binding in bound_scopes(tree):
        output = nodes_by_path[tuple(path)].get("result", {}).get("output", {})
        status = output.get("status")
        if status is None:
            status = (
                run_status
                if run_status in HALTING and active_path[:len(path)] == path
                else "running"
            )
        summaries.append(
            {
                "scope_path": path,
                "workflow_id": binding["workflow"],
                "status": status,
            }
        )
    return summaries


def child_context_for_call(parent, binding, definition):
    """Create the private context for one bound workflow call."""
    return StepContext(
        inputs=binding["inputs"],
        project_root=parent.project_root,
        run_id=parent.run_id,
        is_resume=parent.is_resume,
        inside_fan_out=parent.inside_fan_out,
        workflow_dir=binding["workflow_dir"],
        default_integration=definition.default_integration,
        default_model=definition.default_model,
        default_options=definition.default_options,
    )


def qualified_id(name, loop_alias=None):
    """Return the public occurrence ID of a loop-iteration or fan-out-item step."""
    if loop_alias is None:
        return name
    return f"{loop_alias[0]}:{name}:{loop_alias[1]}"


def loop_alias_for(kind, qualified, iteration):
    """Qualify direct body steps of later loop iterations (4.6)."""
    return (qualified, iteration) if kind in LOOP_TYPES and iteration else None


def result_view(node):
    """Public result, distinct from the frozen result used to execute children."""
    result = node["result"]
    if "fan_results" in node:
        return {**result, "output": {**result["output"], "results": node["fan_results"]}}
    return result


@dataclass(frozen=True)
class Occurrence:
    """One invocation, never stored on a shared step implementation."""

    config: dict
    node: dict
    context: StepContext
    ancestry: tuple
    path: tuple
    public: bool
    qualified: str


@dataclass(frozen=True)
class SubtreeResult:
    outcome: str
    error: str | None
    outputs: list | None = None


@dataclass(frozen=True)
class MissingImplementation:
    error: str


class Execution:
    def __init__(self, engine, state, registry, *, rebind=False):
        self.engine, self.state, self.registry = engine, state, registry
        self.rebind = rebind

    def project(self, context, name, result, *, public, qualified):
        """Apply an occurrence result to its local and public views."""
        context.steps[name] = result
        if public:
            self.state.step_results[name] = result
            if qualified != name:
                context.steps[qualified] = result
                self.state.step_results[qualified] = result

    def project_alias(self, context, name, result):
        """Project a fan-out item result into its enclosing workflow scope."""
        context.steps[name] = result

    def transition(
        self,
        operation,
        occurrence,
        changes=None,
        *,
        publish=False,
        announce=True,
    ):
        """The only writer of occurrence progress and its checkpointed views.

        Phase is the continuation point; active marks entry into that continuation.
        Own-step results and subtree outcomes deliberately remain distinct.
        Validate the candidate before changing memory or writing anything.
        """
        node = occurrence.node
        with self.state._lock:
            if self.state._checkpoint_failed:
                raise CheckpointError("A previous checkpoint failed")
            phases, fields = TRANSITIONS[operation]
            if node["phase"] not in phases:
                raise ValueError(f"Invalid {operation} transition from {node['phase']}")
            if set(changes or {}) - fields:
                raise ValueError(f"Invalid fields for {operation} transition")
            candidate = {**node, **(changes or {})}
            if operation in {"expand", "bind"}:
                candidate["phase"] = "children"
            elif operation == "outputs":
                candidate["phase"] = "outputs"
            elif operation in {"finish", "settle"}:
                candidate["phase"] = (
                    "done" if candidate["outcome"] == "completed"
                    else "blocked" if operation == "finish" else "children"
                )
            if operation == "begin":
                candidate["active"] = True
                if (
                    node["phase"] == "blocked"
                    and occurrence.config.get("type") == "workflow"
                ):
                    # A call's recorded result summarizes its previous attempt
                    # and is stale once the call is re-entered, whether or not
                    # that attempt bound it: a bound call continues at its
                    # children, an unbound call binds again from ready. A leaf
                    # step's record describes that same step (for example a
                    # pending gate's prompt) and stays until finish replaces it.
                    for key in ("result", "outcome", "error"):
                        candidate.pop(key, None)
                    candidate["phase"] = (
                        "children" if candidate.get("binding") else "ready"
                    )
            elif operation in {"finish", "settle", "leave"}:
                candidate["active"] = False
            previous = node.get("children", [])
            new_children = ()
            if "children" in (changes or {}):
                existing = {id(child) for child in previous}
                new_children = tuple(
                    child for child in candidate["children"] if id(child) not in existing
                )
            # The same node rules are checked when a checkpoint is loaded.
            check_node(occurrence.config, candidate, changed=set(changes or ()),
                       new_children=new_children)
            node.clear()
            node.update(candidate)
            if operation == "begin":
                self.state.current_step_id = occurrence.qualified
            if publish and "result" in node:
                self.project(
                    occurrence.context,
                    occurrence.config["id"],
                    result_view(node),
                    public=occurrence.public,
                    qualified=occurrence.qualified,
                )
            # Leave is memory-only and best-effort; the run-level handler
            # checkpoints the unwound tree on an exception.
            # Do not insert a second checkpoint between completion and its event.
            if operation != "leave":
                self.state.save()
        if announce:
            self.notify(operation, occurrence, publish=publish)

    def notify(self, operation, occurrence, *, publish):
        """Post-checkpoint notifications; never responsible for persistence."""
        config, node = occurrence.config, occurrence.node
        kind = config.get("type", "command")
        args = occurrence.qualified, occurrence.path, occurrence.ancestry
        if operation == "begin":
            label = kind if kind == "workflow" else config.get("command", "") or kind
            self.emit("step_started", *args, type=kind, callback_label=label)
        elif operation in {"expand", "finish"}:
            result = node["result"]
            if publish:
                self.emit("step_completed", *args, status=result["status"])
            if result["status"] == "failed":
                event = {
                    "aborted": "workflow_aborted",
                    "completed": "step_continue_on_error",
                }.get(node.get("outcome"), "step_failed")
                self.emit(event, *args, error=result.get("error"))

    def emit(
        self,
        event,
        qualified,
        path,
        ancestry,
        *,
        callback_label=None,
        **fields,
    ):
        """Emit one step event and its optional start callback."""
        entry = {"event": event, "step_id": qualified, **fields}
        if len(ancestry) > 1:
            entry.update(execution_path=list(path), workflow_id=ancestry[-1])
        self.state.append_log(entry)
        if callback_label is not None and self.engine.on_step_start is not None:
            with self.engine._callback_lock:
                self.engine.on_step_start(qualified, callback_label)

    def run(
        self,
        seq,
        context,
        ancestry,
        *,
        path=(),
        public=True,
        root=False,
        loop_alias=None,
        steps=None,
    ):
        steps = steps_of(seq) if steps is None else steps
        for index, (config, node) in enumerate(zip(steps, seq["nodes"])):
            config = {"id": f"step-{index}", **config}
            name = config["id"]
            occurrence = (*path, index)
            qualified = qualified_id(name, loop_alias)
            if root and node["phase"] != "done":
                with self.state._lock:
                    self.state.current_step_index = index + self.state.execution.get(
                        "offset", 0
                    )
            outcome = self.step(
                config,
                node,
                context,
                ancestry,
                occurrence,
                public,
                qualified,
            )
            if outcome in HALTING:
                return outcome, node.get("error")
        return "completed", None

    def run_children(self, config, node, context, ancestry, path, public, qualified):
        """Run or replay persisted child sequences in order."""
        kind = config.get("type", "command")
        for iteration, child in enumerate(node.get("children", [])):
            outcome, error = self.run(
                child,
                context,
                ancestry,
                path=(*path, iteration),
                public=public,
                loop_alias=loop_alias_for(kind, qualified, iteration),
                steps=child_steps(config, node, iteration),
            )
            if outcome in HALTING:
                return outcome, error
        return "completed", None

    def step(self, config, node, context, ancestry, path, public, qualified):
        name = config.get("id", "step-0")
        kind = config.get("type", "command")
        if node["phase"] == "done":
            self.project(
                context, name, result_view(node), public=public, qualified=qualified
            )
            if kind == "fan-out" and node.get("children"):
                self.fan_out(
                    config,
                    node,
                    context,
                    ancestry,
                    path,
                    public,
                    qualified,
                    sequential=True,
                )
            elif kind not in {"workflow", "fan-out"}:
                self.run_children(
                    config, node, context, ancestry, path, public, qualified
                )
            return "completed"
        if node.get("outcome") == "aborted":
            # Replay the result the aborted occurrence projected when it ran, so
            # its fan-out item keeps its published output (see run_item).
            if node.get("result") is not None:
                self.project(
                    context, name, result_view(node), public=public, qualified=qualified
                )
            return "aborted"

        occurrence = Occurrence(config, node, context, ancestry, path, public, qualified)
        calls = kind == "workflow"
        try:
            # Workflow calls are announced on every entry, including resumed bound calls.
            self.transition(
                "begin", occurrence,
                announce=node["phase"] in {"ready", "blocked"} or calls,
            )
            result = self.workflow(occurrence) if calls else self.execute_step(occurrence)
            return self.finish(occurrence, result)
        except BaseException:
            if node.get("active"):
                try:
                    self.transition("leave", occurrence)
                except Exception:
                    pass  # A crash-shaped active node is valid on resume.
            raise

    def execute_step(self, occurrence):
        config, node, context = occurrence.config, occurrence.node, occurrence.context
        ancestry, path = occurrence.ancestry, occurrence.path
        public, qualified = occurrence.public, occurrence.qualified
        name, kind = config["id"], config.get("type", "command")

        if node["phase"] in {"ready", "blocked"}:
            impl = self.registry.get(kind)
            if impl is None:
                # Terminal: only step_failed, no projected result.
                # The node keeps its result so resume can retry after reinstalling.
                error = unknown_step_error(kind)
                return MissingImplementation(error)
            result = impl.execute(config, context)
            expansion = {}
            if kind == "fan-out":
                # Definitions belong to the tree, never to JSON result records.
                output = dict(result.output)
                template = output.pop("step_template", {})
                expansion["template"] = yaml.safe_dump(template, sort_keys=False)
                result = replace(result, output=output)
            if result.status in {StepStatus.FAILED, StepStatus.PAUSED}:
                return result
            children = [sequence(result.next_steps)] if result.next_steps else []
            if kind == "fan-out":
                children = (
                    [occurrences([template]) for _ in result.output.get("items", [])]
                    if template
                    else []
                )
            data = self.record(config, result, context)
            if not children:
                if kind == "fan-out":
                    result.output = {**result.output, "results": []}
                return result
            self.transition(
                "expand", occurrence,
                {"result": data, "children": children, **expansion},
                publish=True,
            )
        else:
            self.project(
                context, name, result_view(node), public=public, qualified=qualified
            )

        if kind == "fan-out":
            outcome, error, outputs = self.fan_out(
                config, node, context, ancestry, path, public, qualified
            )
        else:
            outcome, error = self.run_children(
                config, node, context, ancestry, path, public, qualified
            )
            if outcome == "completed" and kind in LOOP_TYPES:
                limit = config.get("max_iterations", 10)
                if isinstance(limit, bool) or not isinstance(limit, int) or limit < 1:
                    limit = 10
                while len(node["children"]) < limit and evaluate_condition(
                    config.get("condition", False), context
                ):
                    child = occurrences(steps_of(node["children"][0]))
                    self.transition("iterate", occurrence, {"children": [*node["children"], child]})
                    outcome, error = self.run(
                        child,
                        context,
                        ancestry,
                        path=(*path, len(node["children"]) - 1),
                        public=public,
                        loop_alias=loop_alias_for(
                            kind, qualified, len(node["children"]) - 1
                        ),
                        steps=child_steps(config, node, len(node["children"]) - 1),
                    )
                    if outcome in HALTING:
                        break
        return SubtreeResult(outcome, error, outputs if kind == "fan-out" else None)

    @staticmethod
    def record(config, result, context):
        output = result.output
        data = {
            "type": config.get("type", "command"),
            "integration": output.get("integration")
            or config.get("integration")
            or context.default_integration,
            "model": output.get("model")
            or config.get("model")
            or context.default_model,
            "options": output.get("options") or config.get("options", {}),
            "input": output.get("input") or config.get("input", {}),
            "output": output,
            "status": result.status.value,
            "error": result.error,
        }
        if config.get("type") == "workflow":
            # A call result exposes neither caller defaults nor private inputs (4.3).
            data.update(integration=None, model=None, options={}, input={})
        if data["type"] == "command" and "integration_args" in output:
            data.update(
                integration_args=output["integration_args"],
                integration_options=output["integration_options"],
            )
        return data

    def finish(self, occurrence, result):
        config, context = occurrence.config, occurrence.context
        if isinstance(result, SubtreeResult):
            self.transition(
                "settle", occurrence,
                {"outcome": result.outcome, "error": result.error,
                 **({"fan_results": result.outputs} if result.outputs is not None else {})},
                publish=result.outputs is not None,
            )
            return result.outcome
        missing = isinstance(result, MissingImplementation)
        if missing:
            result = StepResult(StepStatus.FAILED, error=result.error)
        outcome = "completed"
        if result.status == StepStatus.PAUSED:
            outcome = "paused"
        elif result.status == StepStatus.FAILED:
            outcome = "aborted" if result.output.get("aborted") else "failed"
            if not missing and outcome == "failed" and config.get("continue_on_error") is True:
                outcome = "completed"
        self.transition(
            "finish", occurrence,
            {
                "result": self.record(config, result, context),
                "outcome": outcome,
                "error": result.error,
            },
            publish=not missing,
        )
        return outcome

    def workflow(self, occurrence):
        from .engine import WorkflowDefinition, workflow_dir_for

        config, node, context = occurrence.config, occurrence.node, occurrence.context
        ancestry, path = occurrence.ancestry, occurrence.path
        binding = node.get("binding")
        target = binding["workflow"] if binding else config.get("workflow")
        if binding is None:
            try:
                validate_runtime_call(config)
                target = evaluate_expression(target, context)
                definition = resolve_target(self.state.project_root, target, ancestry)
                binding = {
                    "workflow": target,
                    "definition": yaml.safe_dump(definition.data, sort_keys=False),
                    "inputs": bind_inputs(self.engine, definition, config, context),
                    "workflow_dir": workflow_dir_for(definition),
                }
                self.transition(
                    "bind", occurrence,
                    {
                        "binding": binding,
                        "children": [occurrences(definition.steps)],
                    },
                )
            except CallError as exc:
                target = target if isinstance(target, str) else repr(target)
                return StepResult(
                    StepStatus.FAILED,
                    output={"workflow": target, "status": "failed", "error": str(exc)},
                    error=str(exc),
                )
        else:
            definition = WorkflowDefinition(yaml.safe_load(binding["definition"]))
            if self.rebind:
                inputs = bind_inputs(
                    self.engine, definition, config, context, binding["inputs"]
                )
                binding = {**binding, "inputs": inputs}
                self.transition("rebind", occurrence, {"binding": binding})
        child_context = child_context_for_call(context, binding, definition)
        outcome, error = self.run(
            node["children"][0],
            child_context,
            (*ancestry, target),
            path=(*path, "workflow"),
            public=False,
            steps=child_steps(config, node, 0),
        )
        output = {"workflow": target, "status": outcome}
        if outcome == "completed":
            self.transition("outputs", occurrence)
            try:
                output.update(evaluate_outputs(definition, child_context))
            except CallError as exc:
                output.update(status="failed", error=str(exc))
                return StepResult(StepStatus.FAILED, output=output, error=str(exc))
        elif outcome == "aborted":
            output["aborted"] = True
        if error is not None:
            output["error"] = error
        status = (
            StepStatus.COMPLETED
            if outcome == "completed"
            else StepStatus.PAUSED
            if outcome == "paused"
            else StepStatus.FAILED
        )
        return StepResult(status, output=output, error=error)

    def fan_out(
        self, config, node, context, ancestry, path, public, qualified, *, sequential=False
    ):
        output = node["result"]["output"]
        items = output.get("items", [])
        try:
            workers = max(1, int(output.get("max_concurrency", 1)))
        except (TypeError, ValueError, OverflowError):
            workers = 1
        if sequential:
            workers = 1
        workers = min(workers, len(items))
        initial = deepcopy(context.steps)
        # Children always consume the frozen expansion result. Aggregate outputs
        # belong to the reporting view, never to the item execution context.
        for key in {config.get("id", "step-0"), qualified}:
            if key in initial:
                initial[key] = deepcopy(node["result"])
        halted = threading.Event()
        template_name = child_steps(config, node, 0)[0]["id"]

        def run_item(index):
            local = replace(
                context, steps=deepcopy(initial), item=items[index], inside_fan_out=True
            )
            local_name = template_name
            inherited = local.steps.get(local_name)
            child = node["children"][index]
            outcome, error = self.run(
                child,
                local,
                ancestry,
                path=(*path, "item", index),
                public=False,
                loop_alias=(qualified, index),
                steps=child_steps(config, node, index),
            )
            if outcome in HALTING:
                halted.set()
            record = child["nodes"][0].get("result")
            if record is not None:
                record = result_view(child["nodes"][0])
            # Expose only results projected by the item traversal. Missing step
            # implementations keep an internal retry record but publish nothing.
            if local.steps.get(local_name) is inherited:
                record = None
            if record is not None:
                # Projection only (E2): persisted by the next commit, rebuilt on replay.
                with self.state._lock:
                    self.project_alias(
                        context,
                        f"{qualified}:{template_name}:{index}",
                        record,
                    )
                    if public:
                        self.state.step_results[
                            f"{qualified}:{template_name}:{index}"
                        ] = record
            return outcome, error, (record or {}).get("output", {})

        results = []
        if workers <= 1:
            for index in range(len(items)):
                outcome, error, value = run_item(index)
                results.append(value)
                if outcome in HALTING:
                    return outcome, error, results
            return "completed", None, results

        def run_item_guarded(index):
            try:
                return run_item(index)
            except BaseException:
                halted.set()
                raise

        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = {i: pool.submit(run_item_guarded, i) for i in range(workers)}
            for index in range(len(items)):
                try:
                    outcome, error, value = futures.pop(index).result()
                except BaseException:
                    for future in futures.values():
                        future.cancel()
                    raise
                results.append(value)
                if outcome in HALTING:
                    for future in futures.values():
                        future.cancel()
                    return outcome, error, results
                following = index + workers
                if following < len(items) and not halted.is_set():
                    futures[following] = pool.submit(run_item_guarded, following)
        return "completed", None, results
