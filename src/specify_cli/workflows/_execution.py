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
from .composition import bind_inputs, evaluate_outputs, resolve_target, validate_call
from .expressions import evaluate_condition, evaluate_expression

HALTING = {"paused", "failed", "aborted"}


class CheckpointError(RuntimeError):
    """Persistence failed; reload the authoritative disk checkpoint before retrying."""


def sequence(steps: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "source": yaml.safe_dump(steps, sort_keys=False),
        "nodes": [{"phase": "ready"} for _ in steps],
    }


def validate_execution(tree: Any) -> None:
    """Validate stored structure without importing a project's custom steps."""

    def check_sequence(seq):
        if not isinstance(seq, dict) or not isinstance(seq.get("source"), str):
            raise ValueError("Invalid execution sequence")
        steps = yaml.safe_load(seq["source"])
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
            for child in children:
                check_sequence(child)
            binding = node.get("binding")
            if binding is not None:
                if step.get("type") != "workflow" or not isinstance(binding, dict):
                    raise ValueError("Invalid workflow binding")
                definition = yaml.safe_load(binding.get("definition", ""))
                if (
                    not isinstance(definition, dict)
                    or not isinstance(definition.get("workflow"), dict)
                    or definition["workflow"].get("id") != binding.get("workflow")
                    or not isinstance(binding.get("inputs"), dict)
                    or len(children) != 1
                    or not isinstance(definition.get("steps"), list)
                    or definition["steps"] != yaml.safe_load(children[0]["source"])
                ):
                    raise ValueError("Invalid bound workflow definition or inputs")
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
    """First unfinished leaf in execution order, including nested workflow scopes."""

    def walk(seq, path):
        for index, (config, node) in enumerate(
            zip(yaml.safe_load(seq["source"]), seq["nodes"])
        ):
            if node["phase"] == "done":
                continue
            here = [*path, config.get("id", f"step-{index}")]
            for item, child in enumerate(node.get("children", [])):
                child_path = (
                    [*here, str(item)]
                    if config.get("type") in {"fan-out", "while", "do-while"}
                    else here
                )
                found = walk(child, child_path)
                if found:
                    return found
            return here, node
        return None

    return walk(tree["sequence"], [])


def scope_summaries(tree):
    """Report workflow boundaries without exposing private inputs or results."""
    summaries = []

    def walk(seq, path):
        for index, (config, node) in enumerate(
            zip(yaml.safe_load(seq["source"]), seq["nodes"])
        ):
            here = [*path, config.get("id", f"step-{index}")]
            binding = node.get("binding")
            if binding:
                output = node.get("result", {}).get("output", {})
                summaries.append(
                    {
                        "scope_path": here,
                        "workflow_id": binding["workflow"],
                        "status": output.get("status", "running"),
                    }
                )
            for item, child in enumerate(node.get("children", [])):
                child_path = (
                    [*here, str(item)]
                    if config.get("type") in {"fan-out", "while", "do-while"}
                    else here
                )
                walk(child, child_path)

    walk(tree["sequence"], [])
    return summaries


class Execution:
    def __init__(self, engine, state, registry, *, rebind=False):
        self.engine, self.state, self.registry = engine, state, registry
        self.rebind = rebind

    def commit(self, node=None, changes=None, *, context=None, name=None, public=None):
        """Mutate an occurrence and its compatibility views in one checkpoint."""
        with self.state._lock:
            if self.state._checkpoint_failed:
                raise CheckpointError("A previous checkpoint failed")
            if node is not None:
                node.update(changes or {})
                if context is not None and "result" in node:
                    context.steps[name] = node["result"]
                    if public is not None:
                        self.state.step_results[public] = node["result"]
            self.state.save()

    def log(self, event, name, path, workflow, **fields):
        entry = {"event": event, "step_id": name, **fields}
        if path:
            entry.update(execution_path=list(path), workflow_id=workflow)
        self.state.append_log(entry)

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
    ):
        steps = yaml.safe_load(seq["source"])
        for index, (config, node) in enumerate(zip(steps, seq["nodes"])):
            config = {"id": f"step-{index}", **config}
            name = config["id"]
            occurrence = (*path, index)
            public_name = name if public else None
            if root and node["phase"] != "done":
                with self.state._lock:
                    self.state.current_step_index = index + self.state.execution.get(
                        "offset", 0
                    )
                    self.state.current_step_id = name
            outcome = self.step(
                config, node, context, ancestry, occurrence, public_name
            )
            if loop_alias is not None and "result" in node:
                with self.state._lock:
                    key = f"{loop_alias[0]}:{name}:{loop_alias[1]}"
                    self.state.step_results[key] = node["result"]
                    context.steps[key] = node["result"]
                    self.state.save()
            if outcome in HALTING:
                return outcome, node.get("error")
        return "completed", None

    def restore(self, node, context):
        """Rebuild aliases for completed expansions without re-executing them."""
        for child in node.get("children", []) if "binding" not in node else []:
            for index, (config, nested) in enumerate(
                zip(yaml.safe_load(child["source"]), child["nodes"])
            ):
                if "result" in nested:
                    context.steps[config.get("id", f"step-{index}")] = nested["result"]
                if config.get("type") != "fan-out":
                    self.restore(nested, context)

    def step(self, config, node, context, ancestry, path, public_name):
        name = config.get("id", "step-0")
        kind = config.get("type", "command")
        if node["phase"] == "done":
            context.steps[name] = node["result"]
            if kind == "fan-out":
                template = node["result"]["output"].get("step_template", {})
                for index, child in enumerate(node.get("children", [])):
                    result = child["nodes"][0].get("result")
                    if result is not None:
                        context.steps[
                            f"{name}:{template.get('id', 'item')}:{index}"
                        ] = result
            else:
                self.restore(node, context)
            return node.get("outcome", "completed")
        if node.get("outcome") == "aborted":
            return "aborted"

        if kind == "workflow":
            return self.workflow(config, node, context, ancestry, path, public_name)

        if node["phase"] in {"ready", "blocked"}:
            with self.state._lock:
                self.state.current_step_id = name
            self.log("step_started", name, path, ancestry[-1], type=kind)
            if self.engine.on_step_start is not None:
                with self.engine._callback_lock:
                    self.engine.on_step_start(name, config.get("command", "") or kind)
            impl = self.registry.get(kind)
            result = (
                impl.execute(config, context)
                if impl
                else StepResult(StepStatus.FAILED, error=f"Unknown step type: {kind!r}")
            )
            if result.status in {StepStatus.FAILED, StepStatus.PAUSED}:
                return self.finish(
                    config, node, result, context, ancestry, path, public_name
                )
            children = [sequence(result.next_steps)] if result.next_steps else []
            if kind == "fan-out":
                template = result.output.get("step_template", {})
                children = (
                    [sequence([template]) for _ in result.output.get("items", [])]
                    if template
                    else []
                )
            data = self.record(config, result, context)
            if not children:
                if kind == "fan-out":
                    result.output = {**result.output, "results": []}
                return self.finish(
                    config, node, result, context, ancestry, path, public_name
                )
            self.commit(
                node,
                {"phase": "children", "result": data, "children": children},
                context=context,
                name=name,
                public=public_name,
            )
        else:
            context.steps[name] = node["result"]

        if kind == "fan-out":
            outcome, error, outputs = self.fan_out(
                config, node, context, ancestry, path, public_name
            )
            data = {
                **node["result"],
                "output": {**node["result"]["output"], "results": outputs},
            }
            self.commit(
                node, {"result": data}, context=context, name=name, public=public_name
            )
        else:
            outcome, error = "completed", None
            for iteration, child in enumerate(node["children"]):
                outcome, error = self.run(
                    child,
                    context,
                    ancestry,
                    path=(*path, iteration),
                    public=public_name is not None,
                    loop_alias=(name, iteration)
                    if kind in {"while", "do-while"}
                    and iteration
                    and public_name is not None
                    else None,
                )
                if outcome in HALTING:
                    break
            if outcome == "completed" and kind in {"while", "do-while"}:
                limit = config.get("max_iterations", 10)
                if isinstance(limit, bool) or not isinstance(limit, int) or limit < 1:
                    limit = 10
                while len(node["children"]) < limit and evaluate_condition(
                    config.get("condition", False), context
                ):
                    child = sequence(yaml.safe_load(node["children"][0]["source"]))
                    self.commit(node, {"children": [*node["children"], child]})
                    outcome, error = self.run(
                        child,
                        context,
                        ancestry,
                        path=(*path, len(node["children"]) - 1),
                        public=public_name is not None,
                        loop_alias=(name, len(node["children"]) - 1)
                        if public_name is not None
                        else None,
                    )
                    if outcome in HALTING:
                        break
        self.commit(
            node,
            {
                "phase": "done" if outcome == "completed" else "children",
                "outcome": outcome,
                "error": error,
            },
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
            "input": {}
            if config.get("type") == "workflow"
            else output.get("input") or config.get("input", {}),
            "output": output,
            "status": result.status.value,
            "error": result.error,
        }
        if data["type"] == "command" and "integration_args" in output:
            data.update(
                integration_args=output["integration_args"],
                integration_options=output["integration_options"],
            )
        return data

    def finish(self, config, node, result, context, ancestry, path, public_name):
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
            public=public_name,
        )
        self.log("step_completed", name, path, ancestry[-1], status=result.status.value)
        if result.status == StepStatus.FAILED:
            event = {
                "aborted": "workflow_aborted",
                "completed": "step_continue_on_error",
            }.get(outcome, "step_failed")
            self.log(event, name, path, ancestry[-1], error=result.error)
        return outcome

    def workflow(self, config, node, context, ancestry, path, public_name):
        from .engine import WorkflowDefinition

        name = config.get("id", "step-0")
        self.log("step_started", name, path, ancestry[-1], type="workflow")
        if self.engine.on_step_start is not None:
            with self.engine._callback_lock:
                self.engine.on_step_start(name, "workflow")
        binding = node.get("binding")
        target = binding["workflow"] if binding else config.get("workflow")
        try:
            if binding is None:
                errors = validate_call(config)
                if errors:
                    raise ValueError("; ".join(errors))
                target = evaluate_expression(target, context)
                definition = resolve_target(self.state.project_root, target, ancestry)
                binding = {
                    "workflow": target,
                    "definition": yaml.safe_dump(definition.data, sort_keys=False),
                    "inputs": bind_inputs(self.engine, definition, config, context),
                    "workflow_dir": str(definition.source_path.parent)
                    if definition.source_path
                    else None,
                }
                self.commit(
                    node,
                    {
                        "binding": binding,
                        "children": [sequence(definition.steps)],
                        "phase": "children",
                    },
                )
            else:
                definition = WorkflowDefinition(yaml.safe_load(binding["definition"]))
                if self.rebind:
                    binding = {
                        **binding,
                        "inputs": bind_inputs(self.engine, definition, config, context),
                    }
                    self.commit(node, {"binding": binding})
            child_context = StepContext(
                inputs=binding["inputs"],
                project_root=context.project_root,
                run_id=context.run_id,
                is_resume=context.is_resume,
                workflow_dir=binding["workflow_dir"],
                default_integration=definition.default_integration,
                default_model=definition.default_model,
                default_options=definition.default_options,
            )
            outcome, error = self.run(
                node["children"][0],
                child_context,
                (*ancestry, target),
                path=(*path, "workflow"),
                public=False,
            )
            output = {"workflow": target, "status": outcome}
            if outcome == "completed":
                self.commit(node, {"phase": "outputs"})
                output.update(evaluate_outputs(definition, child_context))
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
        except CheckpointError:
            raise
        except Exception as exc:
            target = target if isinstance(target, str) else repr(target)
            result = StepResult(
                StepStatus.FAILED,
                output={"workflow": target, "status": "failed", "error": str(exc)},
                error=str(exc),
            )
        return self.finish(config, node, result, context, ancestry, path, public_name)

    def fan_out(self, config, node, context, ancestry, path, public_name):
        output = node["result"]["output"]
        items = output.get("items", [])
        try:
            workers = max(1, int(output.get("max_concurrency", 1)))
        except (TypeError, ValueError, OverflowError):
            workers = 1
        workers = min(workers, len(items))
        initial = deepcopy(context.steps)
        halted = threading.Event()

        def run_item(index):
            local = replace(
                context, steps=deepcopy(initial), item=items[index], inside_fan_out=True
            )
            child = node["children"][index]
            outcome, error = self.run(
                child, local, ancestry, path=(*path, "item", index), public=False
            )
            if outcome in HALTING:
                halted.set()
            record = child["nodes"][0].get("result", {})
            template_name = output.get("step_template", {}).get("id", "item")
            with self.state._lock:
                key = f"{config['id']}:{template_name}:{index}"
                context.steps[key] = record
                if public_name is not None:
                    self.state.step_results[key] = record
                    self.state.save()
            return outcome, error, record.get("output", {})

        results = []
        if workers <= 1:
            for index in range(len(items)):
                outcome, error, value = run_item(index)
                results.append(value)
                if outcome in HALTING:
                    return outcome, error, results
            return "completed", None, results
        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = {i: pool.submit(run_item, i) for i in range(workers)}
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
                    futures[following] = pool.submit(run_item, following)
        return "completed", None, results
