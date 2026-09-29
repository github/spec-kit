"""A persisted execution tree, traversed identically on first execution and resume.

An occurrence owns its result and descendants. Authored names are only aliases
in an expression context; tree positions distinguish repeated executions.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from dataclasses import replace
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
        "version": 1,
        "sequence": sequence(steps),
        "offset": max(0, offset),
        "initial": deepcopy(initial),
    }


def steps_of(seq: dict[str, Any]) -> Any:
    """Read the persisted YAML source for one execution sequence."""
    return yaml.safe_load(seq["source"])


LOOP_TYPES = frozenset({"while", "do-while"})


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
        template = node["result"]["output"]["step_template"]
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


def validate_execution(tree: Any) -> None:
    """Validate stored structure without importing a project's custom steps."""

    def check_sequence(seq, steps=None, *, shared=False):
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
            if not isinstance(node, dict) or node.get("phase") not in {
                "ready",
                "children",
                "outputs",
                "blocked",
                "done",
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
            if node.get("outcome", "completed") not in {"completed", *HALTING}:
                raise ValueError("Invalid execution outcome")
            if (
                node["phase"] == "done"
                and node.get("outcome", "completed") != "completed"
            ):
                raise ValueError("Completed execution has a blocking outcome")
            if node["phase"] == "blocked" and (
                result is None
                or result["status"] not in {"failed", "paused"}
                or node.get("outcome") not in HALTING
            ):
                raise ValueError("Blocked execution lacks a blocking result")
            children = node.get("children", [])
            if not isinstance(children, list):
                raise ValueError("Invalid execution children")
            kind = step.get("type")
            binding = node.get("binding")
            if binding is not None:
                if kind != "workflow" or not isinstance(binding, dict):
                    raise ValueError("Invalid workflow binding")
                source = binding.get("definition")
                if not isinstance(source, str):
                    raise ValueError("Invalid bound workflow definition or inputs")
                definition = yaml.safe_load(source)
                if (
                    not isinstance(definition, dict)
                    or not isinstance(definition.get("workflow"), dict)
                    or definition["workflow"].get("id") != binding.get("workflow")
                    or not isinstance(binding.get("inputs"), dict)
                    or "workflow_dir" not in binding
                    or not isinstance(binding["workflow_dir"], (str, type(None)))
                    or len(children) != 1
                    or not isinstance(definition.get("steps"), list)
                ):
                    raise ValueError("Invalid bound workflow definition or inputs")
            elif kind == "workflow" and children:
                raise ValueError("Workflow children require a binding")
            if kind == "fan-out" and children:
                template = (result or {}).get("output", {}).get("step_template")
                if not isinstance(template, dict):
                    raise ValueError("Invalid fan-out template")
            for index, child in enumerate(children):
                if shares_source(kind, index):
                    check_sequence(child, child_steps(step, node, index), shared=True)
                else:
                    check_sequence(child)
                handled_child_failure = (
                    kind == "workflow"
                    and step.get("continue_on_error") is True
                    and node.get("outcome") == "completed"
                    and result is not None
                    and result["status"] == "failed"
                )
                if (
                    node["phase"] == "done"
                    and any(nested["phase"] != "done" for nested in child["nodes"])
                    and not handled_child_failure
                ):
                    raise ValueError("Completed execution has unfinished children")
            if node["phase"] == "outputs" and binding is None:
                raise ValueError("Output finalization requires a workflow binding")
            if node["phase"] == "children" and (
                not children or (binding is None and result is None)
            ):
                raise ValueError("Expanded execution lacks its children or result")
            if node["phase"] == "ready" and (result is not None or children or binding):
                raise ValueError("Unstarted execution already has progress")
            if step.get("type") == "fan-out" and children:
                items = (result or {}).get("output", {}).get("items")
                if not isinstance(items, list) or len(items) != len(children):
                    raise ValueError("Fan-out items do not match execution children")

    try:
        if not isinstance(tree, dict) or tree.get("version") != 1:
            raise ValueError("Unsupported execution version")
        offset = tree.get("offset", 0)
        if (
            type(offset) is not int
            or offset < 0
            or not isinstance(tree.get("initial", {}), dict)
        ):
            raise ValueError("Invalid execution offset or initial aliases")
        check_sequence(tree["sequence"])
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


def scope_summaries(tree):
    """Report workflow boundaries without exposing private inputs or results."""
    summaries = []
    for _, node, path, _ in walk_execution(tree["sequence"]):
        binding = node.get("binding")
        if binding:
            output = node.get("result", {}).get("output", {})
            summaries.append(
                {
                    "scope_path": path,
                    "workflow_id": binding["workflow"],
                    "status": output.get("status", "running"),
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

    def commit(
        self,
        node=None,
        changes=None,
        *,
        context=None,
        name=None,
        public=False,
        qualified=None,
    ):
        """Mutate an occurrence and its compatibility views in one checkpoint."""
        with self.state._lock:
            if self.state._checkpoint_failed:
                raise CheckpointError("A previous checkpoint failed")
            if node is not None:
                node.update(changes or {})
                if context is not None and "result" in node:
                    self.project(
                        context,
                        name,
                        node["result"],
                        public=public,
                        qualified=qualified or name,
                    )
            self.state.save()

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
                    self.state.current_step_id = name
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
                context, name, node["result"], public=public, qualified=qualified
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
            return "aborted"

        if kind == "workflow":
            return self.workflow(
                config,
                node,
                context,
                ancestry,
                path,
                public,
                qualified,
            )

        if node["phase"] in {"ready", "blocked"}:
            with self.state._lock:
                self.state.current_step_id = qualified
            self.emit(
                "step_started",
                qualified,
                path,
                ancestry,
                type=kind,
                callback_label=config.get("command", "") or kind,
            )
            impl = self.registry.get(kind)
            if impl is None:
                # As on main: terminal, only step_failed, no projected result.
                # The node keeps its result so resume can retry after reinstalling.
                error = unknown_step_error(kind)
                result = StepResult(StepStatus.FAILED, error=error)
                self.commit(
                    node,
                    {
                        "phase": "blocked",
                        "result": self.record(config, result, context),
                        "outcome": "failed",
                        "error": error,
                    },
                )
                self.emit("step_failed", qualified, path, ancestry, error=error)
                return "failed"
            result = impl.execute(config, context)
            if result.status in {StepStatus.FAILED, StepStatus.PAUSED}:
                return self.finish(
                    config,
                    node,
                    result,
                    context,
                    ancestry,
                    path,
                    public,
                    qualified,
                )
            children = [sequence(result.next_steps)] if result.next_steps else []
            if kind == "fan-out":
                template = result.output.get("step_template", {})
                children = (
                    [occurrences([template]) for _ in result.output.get("items", [])]
                    if template
                    else []
                )
            data = self.record(config, result, context)
            if not children:
                if kind == "fan-out":
                    result.output = {**result.output, "results": []}
                return self.finish(
                    config,
                    node,
                    result,
                    context,
                    ancestry,
                    path,
                    public,
                    qualified,
                )
            self.commit(
                node,
                {"phase": "children", "result": data, "children": children},
                context=context,
                name=name,
                public=public,
                qualified=qualified,
            )
            self.emit(
                "step_completed",
                qualified,
                path,
                ancestry,
                status=result.status.value,
            )
        else:
            self.project(
                context, name, node["result"], public=public, qualified=qualified
            )

        if kind == "fan-out":
            outcome, error, outputs = self.fan_out(
                config, node, context, ancestry, path, public, qualified
            )
            data = {
                **node["result"],
                "output": {**node["result"]["output"], "results": outputs},
            }
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
                    self.commit(node, {"children": [*node["children"], child]})
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
        self.commit(
            node,
            {
                "phase": "done" if outcome == "completed" else "children",
                "outcome": outcome,
                "error": error,
                **({"result": data} if kind == "fan-out" else {}),
            },
            context=context if kind == "fan-out" else None,
            name=name if kind == "fan-out" else None,
            public=public,
            qualified=qualified,
        )
        return outcome

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

    def finish(
        self,
        config,
        node,
        result,
        context,
        ancestry,
        path,
        public,
        qualified,
    ):
        name = config.get("id", "step-0")
        outcome = "completed"
        if result.status == StepStatus.PAUSED:
            outcome = "paused"
        elif result.status == StepStatus.FAILED:
            outcome = "aborted" if result.output.get("aborted") else "failed"
            if outcome == "failed" and config.get("continue_on_error") is True:
                outcome = "completed"
        self.commit(
            node,
            {
                "phase": "done" if outcome == "completed" else "blocked",
                "result": self.record(config, result, context),
                "outcome": outcome,
                "error": result.error,
            },
            context=context,
            name=name,
            public=public,
            qualified=qualified,
        )
        self.emit(
            "step_completed",
            qualified,
            path,
            ancestry,
            status=result.status.value,
        )
        if result.status == StepStatus.FAILED:
            event = {
                "aborted": "workflow_aborted",
                "completed": "step_continue_on_error",
            }.get(outcome, "step_failed")
            self.emit(
                event,
                qualified,
                path,
                ancestry,
                error=result.error,
            )
        return outcome

    def workflow(
        self,
        config,
        node,
        context,
        ancestry,
        path,
        public,
        qualified,
    ):
        from .engine import WorkflowDefinition, workflow_dir_for

        self.emit(
            "step_started",
            qualified,
            path,
            ancestry,
            type="workflow",
            callback_label="workflow",
        )
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
                self.commit(
                    node,
                    {
                        "binding": binding,
                        "children": [occurrences(definition.steps)],
                        "phase": "children",
                    },
                )
            except CallError as exc:
                target = target if isinstance(target, str) else repr(target)
                result = StepResult(
                    StepStatus.FAILED,
                    output={"workflow": target, "status": "failed", "error": str(exc)},
                    error=str(exc),
                )
                return self.finish(
                    config,
                    node,
                    result,
                    context,
                    ancestry,
                    path,
                    public,
                    qualified,
                )
        else:
            definition = WorkflowDefinition(yaml.safe_load(binding["definition"]))
            if self.rebind:
                inputs = bind_inputs(
                    self.engine, definition, config, context, binding["inputs"]
                )
                binding = {**binding, "inputs": inputs}
                self.commit(node, {"binding": binding})
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
            self.commit(node, {"phase": "outputs"})
            try:
                output.update(evaluate_outputs(definition, child_context))
            except CallError as exc:
                output.update(status="failed", error=str(exc))
                result = StepResult(StepStatus.FAILED, output=output, error=str(exc))
                return self.finish(
                    config,
                    node,
                    result,
                    context,
                    ancestry,
                    path,
                    public,
                    qualified,
                )
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
        result = StepResult(status, output=output, error=error)
        return self.finish(
            config,
            node,
            result,
            context,
            ancestry,
            path,
            public,
            qualified,
        )

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
