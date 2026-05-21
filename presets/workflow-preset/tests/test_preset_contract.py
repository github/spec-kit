from __future__ import annotations

import unittest
import json
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator

from validators.speckit_implement_contract import (
    validate_implement_contract,
    validate_handoff_contract,
    validate_manifest_contract,
    validate_receipt_contract,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
PRESET_PATH = REPO_ROOT / "preset.yml"
README_PATH = REPO_ROOT / "README.md"
CHANGELOG_PATH = REPO_ROOT / "CHANGELOG.md"
CROSS_AGENT_SUBAGENTS_PATH = REPO_ROOT / "speckit-cross-agent-subagents.md"
PLAN_COMMAND_PATH = REPO_ROOT / "commands" / "speckit.plan.md"
TASKS_COMMAND_PATH = REPO_ROOT / "commands" / "speckit.tasks.md"
IMPLEMENT_COMMAND_PATH = REPO_ROOT / "commands" / "speckit.implement.md"
PLAN_TEMPLATE_PATH = REPO_ROOT / "templates" / "plan-template.md"
REQUIREMENTS_DEV_PATH = REPO_ROOT / "requirements-dev.txt"
MANIFEST_SCHEMA_PATH = REPO_ROOT / "schemas" / "speckit.implement.manifest.v1.schema.json"
HANDOFF_SCHEMA_PATH = REPO_ROOT / "schemas" / "speckit.implement.handoff.v2.schema.json"
RECEIPT_SCHEMA_PATH = REPO_ROOT / "schemas" / "speckit.implement.receipt.v1.schema.json"
HANDOFF_CLI_PATH = REPO_ROOT / "scripts" / "speckit-implement-handoff.py"
BUILD_SCRIPT_PATH = REPO_ROOT / "scripts" / "build-task-shards.py"
RUN_SCRIPT_PATH = REPO_ROOT / "scripts" / "run-orchestrated-implement.py"
WORKFLOW_PATH = (
    REPO_ROOT
    / "workflows"
    / "speckit-orchestrated-implement"
    / "workflow.yml"
)

RUN_ID = "run-001"
FEATURE_PATH = "specs/001-demo"
HANDOFF_DIR = f"{FEATURE_PATH}/handoffs/implement/{RUN_ID}"
SHARD_ID = "S01-service-flow-01"
RECEIPT_PATH = f"{HANDOFF_DIR}/results/{SHARD_ID}.json"
SERVICE_PATH = f"{FEATURE_PATH}/src/service.py"
TASKS_PATH = f"{FEATURE_PATH}/tasks.md"


def minimal_shard(
    *,
    shard_id: str = SHARD_ID,
    vertical_capability: str = "service-flow",
    task_ids: list[str] | None = None,
) -> dict:
    return {
        "shard_id": shard_id,
        "handoff_path": f"{HANDOFF_DIR}/{shard_id}.json",
        "context_digest_path": f"{HANDOFF_DIR}/{shard_id}.context.md",
        "receipt_path": f"{HANDOFF_DIR}/results/{shard_id}.json",
        "task_ids": task_ids or ["T001"],
        "vertical_capability": vertical_capability,
    }


def minimal_manifest(
    *,
    shards: list[dict] | None = None,
    dependencies: list[dict] | None = None,
    dispatch_order: list[list[str]] | None = None,
    vertical_capability: str = "service-flow",
) -> dict:
    if shards is None:
        shards = [minimal_shard(vertical_capability=vertical_capability)]
    if dispatch_order is None:
        dispatch_order = [[shard["shard_id"] for shard in shards]]

    return {
        "contract_type": "speckit.implement.manifest.v1",
        "run_id": RUN_ID,
        "feature_path": FEATURE_PATH,
        "context_index_path": f"{HANDOFF_DIR}/context-index.json",
        "planner_outputs": [
            {
                "vertical_capability": vertical_capability,
                "planner_id": f"VP01-{vertical_capability}",
                "shard_plan_path": f"{HANDOFF_DIR}/planner-outputs/{vertical_capability}.plan.json",
                "handoff_draft_paths": [
                    f"{HANDOFF_DIR}/planner-outputs/{vertical_capability}.handoff.json"
                ],
                "context_digest_draft_paths": [
                    f"{HANDOFF_DIR}/planner-outputs/{vertical_capability}.context.md"
                ],
            }
        ],
        "shards": shards,
        "dependencies": dependencies or [],
        "dispatch_order": dispatch_order,
    }


def minimal_handoff(
    *,
    shard_id: str = SHARD_ID,
    vertical_capability: str = "service-flow",
    planner_vertical_capability: str | None = None,
    task_ids: list[str] | None = None,
    allowed_write_paths: list[str] | None = None,
) -> dict:
    task_ids = task_ids or ["T001"]
    planner_vertical_capability = planner_vertical_capability or vertical_capability
    receipt_path = f"{HANDOFF_DIR}/results/{shard_id}.json"
    if allowed_write_paths is None:
        allowed_write_paths = [SERVICE_PATH, receipt_path]

    return {
        "contract_type": "speckit.implement.handoff.v2",
        "shard_id": shard_id,
        "agent_topology": {
            "core_agent": {"role": "orchestrator"},
            "vertical_planner_agent": {
                "role": "planner",
                "vertical_planner_only": True,
                "may_execute_implementation": False,
                "may_write_manifest": False,
                "may_update_tasks_md": False,
            },
            "worker_agent": {
                "role": "executor",
                "single_handoff_only": True,
                "may_dispatch_workers": False,
                "may_update_tasks_md": False,
            },
        },
        "lifecycle_stage": "worker_execution",
        "vertical_capability": vertical_capability,
        "capability_boundary": {"owns": [], "depends_on": [], "must_not_touch": []},
        "planner_outputs": {
            "shard_plan_path": f"{HANDOFF_DIR}/planner-outputs/{vertical_capability}.plan.json",
            "handoff_draft_path": f"{HANDOFF_DIR}/planner-outputs/{vertical_capability}.handoff.json",
            "context_digest_draft_path": f"{HANDOFF_DIR}/planner-outputs/{vertical_capability}.context.md",
            "vertical_capability": planner_vertical_capability,
        },
        "draft_source": {
            "vertical_planner_id": f"VP01-{vertical_capability}",
            "handoff_draft_path": f"{HANDOFF_DIR}/planner-outputs/{vertical_capability}.handoff.json",
            "context_digest_draft_path": f"{HANDOFF_DIR}/planner-outputs/{vertical_capability}.context.md",
        },
        "task_ids": task_ids,
        "task_text": ["Implement service"],
        "context_digest_path": f"{HANDOFF_DIR}/{shard_id}.context.md",
        "context_index_path": f"{HANDOFF_DIR}/context-index.json",
        "allowed_read_paths": [TASKS_PATH],
        "allowed_write_paths": allowed_write_paths,
        "context_gaps": [],
        "validation_commands": [],
        "task_status_update": {
            "mode": "receipt",
            "receipt_path": receipt_path,
            "committer": "core_agent",
            "contract_type": "speckit.implement.receipt.v1",
            "required_fields": [
                "contract_type",
                "shard_id",
                "task_ids",
                "completed_task_ids",
                "validation_evidence",
            ],
        },
        "forbidden_actions": ["Do not edit `tasks.md`."],
    }


def minimal_receipt(
    *,
    shard_id: str = SHARD_ID,
    task_ids: list[str] | None = None,
    completed_task_ids: list[str] | None = None,
    changed_paths: list[str] | None = None,
    validation_evidence: list[str] | None = None,
) -> dict:
    task_ids = task_ids or ["T001"]
    return {
        "contract_type": "speckit.implement.receipt.v1",
        "shard_id": shard_id,
        "task_ids": task_ids,
        "completed_task_ids": completed_task_ids or task_ids,
        "changed_paths": changed_paths or [SERVICE_PATH],
        "validation_evidence": validation_evidence
        if validation_evidence is not None
        else ["unit tests passed"],
    }


class PresetContractTests(unittest.TestCase):
    def test_preset_manifest_contract(self) -> None:
        data = yaml.safe_load(PRESET_PATH.read_text(encoding="utf-8"))

        self.assertEqual("1.0", data["schema_version"])
        self.assertEqual("workflow-preset", data["preset"]["id"])
        self.assertEqual("Workflow Preset", data["preset"]["name"])
        self.assertEqual("1.0.3", data["preset"]["version"])
        self.assertEqual(
            "Plan design artifacts and agent-native handoff orchestration",
            data["preset"]["description"],
        )
        self.assertEqual("bigsmartben", data["preset"]["author"])
        self.assertEqual(
            "https://github.com/bigsmartben/spec-kit-workflow-preset",
            data["preset"]["repository"],
        )
        self.assertEqual("MIT", data["preset"]["license"])
        self.assertEqual(">=0.8.10.dev0", data["requires"]["speckit_version"])
        self.assertEqual(
            ["planning", "design", "implementation", "orchestration", "handoff"],
            data["tags"],
        )

        provides = data["provides"]["templates"]
        self.assertEqual(7, len(provides))
        entries = {entry["name"]: entry for entry in provides}

        plan_template = entries["plan-template"]
        self.assertEqual("template", plan_template["type"])
        self.assertEqual("templates/plan-template.md", plan_template["file"])
        self.assertEqual("plan-template", plan_template["replaces"])
        self.assertEqual("wrap", plan_template["strategy"])

        for command_name in ("speckit.plan", "speckit.tasks"):
            command = entries[command_name]
            self.assertEqual("command", command["type"])
            self.assertEqual(f"commands/{command_name}.md", command["file"])
            self.assertEqual(command_name, command["replaces"])
            self.assertEqual("wrap", command["strategy"])

        implement = entries["speckit.implement"]
        self.assertEqual("command", implement["type"])
        self.assertEqual("commands/speckit.implement.md", implement["file"])
        self.assertEqual("speckit.implement", implement["replaces"])
        self.assertEqual("replace", implement["strategy"])
        for schema_name, schema_file in (
            (
                "speckit-implement-manifest-v1-schema",
                "schemas/speckit.implement.manifest.v1.schema.json",
            ),
            (
                "speckit-implement-handoff-v2-schema",
                "schemas/speckit.implement.handoff.v2.schema.json",
            ),
            (
                "speckit-implement-receipt-v1-schema",
                "schemas/speckit.implement.receipt.v1.schema.json",
            ),
        ):
            schema = entries[schema_name]
            self.assertEqual("template", schema["type"])
            self.assertEqual(schema_file, schema["file"])
            self.assertEqual(schema_name, schema["replaces"])
            self.assertEqual("replace", schema["strategy"])

        self.assertNotIn("scripts", data["provides"])
        self.assertNotIn("files", data["provides"])
        self.assertNotIn("workflows", data["provides"])

    def test_cli_orchestration_files_are_not_packaged(self) -> None:
        self.assertFalse(HANDOFF_CLI_PATH.exists())
        self.assertFalse(BUILD_SCRIPT_PATH.exists())
        self.assertFalse(RUN_SCRIPT_PATH.exists())
        self.assertFalse(WORKFLOW_PATH.exists())

    def test_plan_command_wrapper_contract(self) -> None:
        command = PLAN_COMMAND_PATH.read_text(encoding="utf-8")

        self.assertIn("{CORE_TEMPLATE}", command)
        self.assertIn("class-diagram.md", command)
        self.assertIn("contracts/sequences.md", command)
        self.assertIn("test-plan.md", command)
        self.assertIn("strategy: wrap", command)
        self.assertIn("Generate the three design artifacts only when useful", command)
        self.assertIn("Keep `plan.md` as summary/navigation", command)
        self.assertIn("final report must list generated artifacts", command)
        self.assertNotIn("speckit.tasks", command)
        self.assertNotIn("speckit.implement", command)

    def test_plan_template_navigation_contract(self) -> None:
        template = PLAN_TEMPLATE_PATH.read_text(encoding="utf-8")

        self.assertIn("{CORE_TEMPLATE}", template)
        self.assertIn("## Design Artifacts", template)
        self.assertIn("./class-diagram.md", template)
        self.assertIn("./contracts/sequences.md", template)
        self.assertIn("./test-plan.md", template)
        self.assertIn("./data-model.md", template)
        self.assertIn("./contracts/", template)
        self.assertIn("./quickstart.md", template)

    def test_tasks_command_wrapper_contract(self) -> None:
        tasks = TASKS_COMMAND_PATH.read_text(encoding="utf-8")

        self.assertIn("{CORE_TEMPLATE}", tasks)
        self.assertIn("class-diagram.md", tasks)
        self.assertIn("contracts/sequences.md", tasks)
        self.assertIn("test-plan.md", tasks)
        self.assertIn("strategy: wrap", tasks)
        self.assertIn("implementation, integration, orchestration", tasks)
        self.assertIn("existing checklist format and user-story organization", tasks)

    def test_implement_command_is_agent_native_handoff_orchestrator(self) -> None:
        command = IMPLEMENT_COMMAND_PATH.read_text(encoding="utf-8")

        self.assertNotIn("{CORE_TEMPLATE}", command)
        self.assertNotIn("strategy: wrap", command)
        self.assertNotIn("uv run", command)
        self.assertNotIn("run-orchestrated-implement.py", command)
        self.assertNotIn("build-task-shards.py", command)
        self.assertNotIn("speckit-implement-handoff.py", command)
        self.assertNotIn("specify_cli.integrations", command)
        self.assertNotIn("subprocess", command.lower())
        self.assertNotIn("specify workflow run", command)
        self.assertNotIn('"contract_type": "speckit.implement.handoff.v2"', command)
        self.assertNotIn('"contract_type": "speckit.implement.manifest.v1"', command)
        self.assertNotIn('"contract_type": "speckit.implement.receipt.v1"', command)

        required_terms = [
            "Core mode",
            "Worker mode",
            "Core Agent",
            "Vertical Planner Agent",
            "Worker Agent",
            "vertical_capability",
            "planner_outputs",
            "draft_source",
            "speckit.implement.handoff.v2",
            "speckit.implement.receipt.v1",
            "context-index.json",
            "handoff-manifest.json",
            "speckit.implement.manifest.v1.schema.json",
            "speckit.implement.handoff.v2.schema.json",
            "speckit.implement.receipt.v1.schema.json",
            ".context.md",
            "handoffs/implement/<run-id>",
            "Use handoff JSON <path>",
            "allowed_read_paths",
            "allowed_write_paths",
            "context_gaps",
            "task_status_update",
            "receipt path does not equal `task_status_update.receipt_path`",
            "results/<shard-id>.json",
            "Do not edit `tasks.md`",
            "single handoff only",
            "vertical planner only",
            "intake",
            "context_indexing",
            "vertical_planning",
            "manifest_assembly",
            "worker_dispatch",
            "worker_execution",
            "receipt_review",
            "task_commit",
            "integration_verification",
            "closeout",
            "domain-model",
            "api-contract",
            "persistence",
            "service-flow",
            "ui",
            "test-validation",
            "documentation",
            "integration",
            "cleanup",
        ]
        for term in required_terms:
            self.assertIn(term, command)

    def test_implement_command_declares_deterministic_handoff_rules(self) -> None:
        command = IMPLEMENT_COMMAND_PATH.read_text(encoding="utf-8")

        required_terms = [
            "Shard Rules",
            "Only Vertical Planner Agents may produce shard plans and digest drafts.",
            "Only Core Agent may write final `handoff-manifest.json` and commit `tasks.md`.",
            "Only Worker Agents may execute implementation handoffs.",
            "one incomplete `tasks.md` checklist item maps to one candidate shard",
            "group candidates only when lifecycle dependencies, vertical_capability, and allowed_write_paths match",
            "shard IDs use `S<2-digit-sequence>-<vertical_capability>-<2-digit-sequence>`",
            "Files",
            "Schemas",
            "Context Digest Rules",
            "include task text for assigned `task_ids`",
            "include document headings from `context-index.json`",
            "include only sections referenced by assigned task paths or vertical_capability",
            "record unresolved required context as `context_gaps`",
            "Path Rules",
            "derive `allowed_write_paths` from paths referenced by assigned task text",
            "include receipt path in `allowed_write_paths`",
            "derive `allowed_read_paths` from allowed write parents, validation files, context digest, and context index",
            "Worker mode must reject non-existent handoff paths",
            "Worker mode must reject handoffs not listed in `handoff-manifest.json`",
        ]
        for term in required_terms:
            self.assertIn(term, command)

    def test_contract_schemas_are_decoupled_json_files(self) -> None:
        for path, contract_type in (
            (MANIFEST_SCHEMA_PATH, "speckit.implement.manifest.v1"),
            (HANDOFF_SCHEMA_PATH, "speckit.implement.handoff.v2"),
            (RECEIPT_SCHEMA_PATH, "speckit.implement.receipt.v1"),
        ):
            schema = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual("object", schema["type"])
            self.assertIn("required", schema)
            self.assertIn("properties", schema)
            self.assertEqual(contract_type, schema["properties"]["contract_type"]["const"])

        handoff = json.loads(HANDOFF_SCHEMA_PATH.read_text(encoding="utf-8"))
        self.assertIn("agent_topology", handoff["required"])
        self.assertIn("planner_outputs", handoff["required"])
        self.assertIn("draft_source", handoff["required"])
        self.assertIn("allowed_read_paths", handoff["required"])
        self.assertIn("allowed_write_paths", handoff["required"])
        self.assertIn("task_status_update", handoff["required"])

        agent_topology = handoff["properties"]["agent_topology"]
        self.assertIn("vertical_planner_agent", agent_topology["required"])
        self.assertIn(
            "may_execute_implementation",
            agent_topology["properties"]["vertical_planner_agent"]["required"],
        )

    def test_manifest_schema_accepts_minimal_valid_manifest(self) -> None:
        schema = json.loads(MANIFEST_SCHEMA_PATH.read_text(encoding="utf-8"))
        manifest = minimal_manifest(shards=[], dispatch_order=[])
        Draft202012Validator(schema).validate(manifest)

    def test_validate_manifest_contract_rejects_unknown_dispatch_order_shard(self) -> None:
        manifest = minimal_manifest(dispatch_order=[["S02-service-flow-01"]])
        with self.assertRaises(ValueError):
            validate_manifest_contract(manifest)

    def test_validate_manifest_contract_rejects_unknown_dependency_shard(self) -> None:
        manifest = minimal_manifest(
            dependencies=[{"shard_id": SHARD_ID, "depends_on": ["S02-service-flow-01"]}]
        )
        with self.assertRaises(ValueError):
            validate_manifest_contract(manifest)

    def test_validate_manifest_contract_rejects_self_dependency(self) -> None:
        manifest = minimal_manifest(
            dependencies=[{"shard_id": SHARD_ID, "depends_on": [SHARD_ID]}]
        )
        with self.assertRaises(ValueError):
            validate_manifest_contract(manifest)

    def test_validate_manifest_contract_rejects_dispatch_order_missing_shard(self) -> None:
        second_shard = minimal_shard(shard_id="S02-service-flow-02", task_ids=["T002"])
        manifest = minimal_manifest(
            shards=[minimal_shard(), second_shard],
            dispatch_order=[[SHARD_ID]],
        )
        with self.assertRaises(ValueError):
            validate_manifest_contract(manifest)

    def test_validate_manifest_contract_rejects_duplicate_dispatch_order_shard(self) -> None:
        manifest = minimal_manifest(dispatch_order=[[SHARD_ID], [SHARD_ID]])
        with self.assertRaises(ValueError):
            validate_manifest_contract(manifest)

    def test_validate_manifest_contract_rejects_dependency_after_dependent(self) -> None:
        second_shard = minimal_shard(shard_id="S02-service-flow-02", task_ids=["T002"])
        manifest = minimal_manifest(
            shards=[minimal_shard(), second_shard],
            dependencies=[{"shard_id": SHARD_ID, "depends_on": ["S02-service-flow-02"]}],
            dispatch_order=[[SHARD_ID], ["S02-service-flow-02"]],
        )
        with self.assertRaises(ValueError):
            validate_manifest_contract(manifest)

    def test_validate_manifest_contract_accepts_valid_cross_fields(self) -> None:
        validate_manifest_contract(minimal_manifest())

    def test_validate_implement_contract_rejects_missing_handoff(self) -> None:
        with self.assertRaises(ValueError):
            validate_implement_contract(
                minimal_manifest(),
                handoffs_by_path={},
                receipts_by_path={},
            )

    def test_validate_implement_contract_rejects_unlisted_handoff(self) -> None:
        with self.assertRaises(ValueError):
            validate_implement_contract(
                minimal_manifest(),
                handoffs_by_path={
                    f"{HANDOFF_DIR}/{SHARD_ID}.json": minimal_handoff(),
                    f"{HANDOFF_DIR}/S02-service-flow-02.json": minimal_handoff(
                        shard_id="S02-service-flow-02"
                    ),
                },
                receipts_by_path={},
            )

    def test_validate_implement_contract_rejects_unlisted_receipt(self) -> None:
        with self.assertRaises(ValueError):
            validate_implement_contract(
                minimal_manifest(),
                handoffs_by_path={f"{HANDOFF_DIR}/{SHARD_ID}.json": minimal_handoff()},
                receipts_by_path={
                    RECEIPT_PATH: minimal_receipt(),
                    f"{HANDOFF_DIR}/results/S02-service-flow-02.json": minimal_receipt(
                        shard_id="S02-service-flow-02"
                    ),
                },
            )

    def test_validate_implement_contract_accepts_valid_bundle(self) -> None:
        validate_implement_contract(
            minimal_manifest(),
            handoffs_by_path={f"{HANDOFF_DIR}/{SHARD_ID}.json": minimal_handoff()},
            receipts_by_path={RECEIPT_PATH: minimal_receipt()},
        )

    def test_handoff_schema_accepts_minimal_valid_handoff(self) -> None:
        schema = json.loads(HANDOFF_SCHEMA_PATH.read_text(encoding="utf-8"))
        Draft202012Validator(schema).validate(minimal_handoff())

    def test_validate_handoff_contract_rejects_tasks_md_in_allowed_write_paths(self) -> None:
        handoff = minimal_handoff(allowed_write_paths=[SERVICE_PATH, TASKS_PATH, RECEIPT_PATH])
        with self.assertRaises(ValueError):
            validate_handoff_contract(handoff)

    def test_validate_handoff_contract_accepts_valid_cross_fields(self) -> None:
        validate_handoff_contract(minimal_handoff())

    def test_validate_handoff_contract_rejects_planner_output_vertical_mismatch(self) -> None:
        handoff = minimal_handoff(planner_vertical_capability="ui")
        with self.assertRaises(ValueError):
            validate_handoff_contract(handoff)

    def test_receipt_schema_accepts_minimal_valid_receipt(self) -> None:
        schema = json.loads(RECEIPT_SCHEMA_PATH.read_text(encoding="utf-8"))
        Draft202012Validator(schema).validate(minimal_receipt())

    def test_validate_receipt_contract_rejects_path_mismatch(self) -> None:
        with self.assertRaises(ValueError):
            validate_receipt_contract(
                minimal_handoff(),
                minimal_receipt(),
                f"{HANDOFF_DIR}/results/wrong.json",
            )

    def test_validate_receipt_contract_rejects_shard_mismatch(self) -> None:
        with self.assertRaises(ValueError):
            validate_receipt_contract(
                minimal_handoff(),
                minimal_receipt(shard_id="S02-service-flow-01"),
                RECEIPT_PATH,
            )

    def test_validate_receipt_contract_accepts_valid_cross_fields(self) -> None:
        validate_receipt_contract(minimal_handoff(), minimal_receipt(), RECEIPT_PATH)

    def test_handoff_schema_rejects_worker_that_can_update_tasks_md(self) -> None:
        schema = json.loads(HANDOFF_SCHEMA_PATH.read_text(encoding="utf-8"))
        handoff = minimal_handoff()
        handoff["agent_topology"]["worker_agent"]["may_update_tasks_md"] = True
        with self.assertRaises(Exception):
            Draft202012Validator(schema).validate(handoff)

    def test_handoff_schema_rejects_planner_that_can_execute_implementation(self) -> None:
        schema = json.loads(HANDOFF_SCHEMA_PATH.read_text(encoding="utf-8"))
        handoff = minimal_handoff()
        handoff["agent_topology"]["vertical_planner_agent"]["may_execute_implementation"] = True
        with self.assertRaises(Exception):
            Draft202012Validator(schema).validate(handoff)

    def test_handoff_schema_rejects_unknown_vertical_capability(self) -> None:
        schema = json.loads(HANDOFF_SCHEMA_PATH.read_text(encoding="utf-8"))
        handoff = minimal_handoff(shard_id="S01-unknown-01", vertical_capability="unknown")
        with self.assertRaises(Exception):
            Draft202012Validator(schema).validate(handoff)

    def test_handoff_schema_rejects_tasks_md_in_allowed_write_paths(self) -> None:
        schema = json.loads(HANDOFF_SCHEMA_PATH.read_text(encoding="utf-8"))
        handoff = minimal_handoff(allowed_write_paths=[TASKS_PATH])
        with self.assertRaises(Exception):
            Draft202012Validator(schema).validate(handoff)

    def test_receipt_schema_rejects_empty_validation_evidence(self) -> None:
        schema = json.loads(RECEIPT_SCHEMA_PATH.read_text(encoding="utf-8"))
        receipt = minimal_receipt(validation_evidence=[])
        with self.assertRaises(Exception):
            Draft202012Validator(schema).validate(receipt)

    def test_implement_prompt_omits_narrative_filler(self) -> None:
        command = IMPLEMENT_COMMAND_PATH.read_text(encoding="utf-8")

        self.assertLessEqual(len(command.splitlines()), 130)
        forbidden_terms = [
            "This command is",
            "The current agent either acts",
            "The Core Agent is the only",
            "Worker Agent restrictions",
            "Use the narrowest",
            "A handoff should not",
            "unless the task itself",
            "When a task spans",
            "If any condition is unclear",
        ]
        for term in forbidden_terms:
            self.assertNotIn(term, command)

    def test_readme_contract(self) -> None:
        readme = README_PATH.read_text(encoding="utf-8")
        changelog = CHANGELOG_PATH.read_text(encoding="utf-8")
        requirements = REQUIREMENTS_DEV_PATH.read_text(encoding="utf-8")

        self.assertIn("specify preset add workflow-preset --from", readme)
        self.assertIn("specify preset add --dev /path/to/workflow-preset", readme)
        self.assertIn("/speckit.plan", readme)
        self.assertIn("/speckit.tasks", readme)
        self.assertIn("/speckit.implement", readme)
        self.assertIn("class-diagram.md", readme)
        self.assertIn("contracts/sequences.md", readme)
        self.assertIn("test-plan.md", readme)
        self.assertIn("handoffs/implement", readme)
        self.assertIn("agent-native handoff orchestration", readme)
        self.assertIn("Core Agent", readme)
        self.assertIn("Vertical Planner Agent", readme)
        self.assertIn("Worker Agent", readme)
        self.assertIn("lifecycle", readme)
        self.assertIn("vertical capability", readme)
        self.assertIn("speckit.implement.handoff.v2", readme)
        self.assertIn("speckit.implement.receipt.v1", readme)
        self.assertIn("speckit-cross-agent-subagents.md", readme)
        self.assertIn("Problem Addressed", readme)
        self.assertIn("reasoning quality", readme)
        self.assertIn("Context-load controls", readme)
        self.assertIn("context-load controls", changelog)
        self.assertNotIn("run-orchestrated-implement.py", readme)
        self.assertNotIn("speckit-implement-handoff.py", readme)
        self.assertNotIn("--dry-run true --run-id manual", readme)
        self.assertIn("Spec Kit CLI `>=0.8.10.dev0`", readme)
        self.assertIn("python3 -m pip install -r requirements-dev.txt", readme)
        self.assertIn("PyYAML", requirements)
        self.assertIn("jsonschema", requirements)
        self.assertIn("## 1.0.3", changelog)
        self.assertIn("agent-native handoff orchestration", changelog)
        self.assertIn("Removed Python dispatch tooling", changelog)

    def test_cross_agent_subagent_contract_document(self) -> None:
        self.assertTrue(CROSS_AGENT_SUBAGENTS_PATH.exists())
        document = CROSS_AGENT_SUBAGENTS_PATH.read_text(encoding="utf-8")

        self.assertLessEqual(len(document.splitlines()), 125)
        required_terms = [
            "Codex",
            "Claude Code",
            "Gemini CLI",
            "GitHub Copilot",
            "Reduce implementation-stage context load and reasoning drift",
            "Vertical Planner Agent",
            "Worker Prompt",
            "handoff-manifest.json",
            "speckit.implement.manifest.v1.schema.json",
            "speckit.implement.handoff.v2.schema.json",
            "speckit.implement.receipt.v1.schema.json",
            "Shard Rules",
            "Context Digest Rules",
            "Path Rules",
            "Only Vertical Planner Agents may produce shard plans and digest drafts.",
            "Only Core Agent may write final `handoff-manifest.json` and commit `tasks.md`.",
            "Only Worker Agents may execute implementation handoffs.",
            "Verify contract_type == speckit.implement.handoff.v2",
            "Load context_digest_path before editing",
            "Stop if context_gaps is not empty",
            "Execute only task_ids",
            "Read only allowed_read_paths",
            "Write only allowed_write_paths",
            "Do not edit tasks.md",
            "Do not dispatch workers",
            "Reject non-existent handoff paths",
            "Reject handoffs not listed in `handoff-manifest.json`",
            "receipt 路径不等于 handoff 中声明的 `task_status_update.receipt_path`",
        ]
        for term in required_terms:
            self.assertIn(term, document)

        forbidden_terms = [
            "核心思路",
            "也就是",
            "推荐架构",
            "不同平台的 subagent 启动方式不同",
            "跨平台稳定性的关键",
            "这样 Codex",
            "只做编排",
            "只做执行",
            "Scope",
            "```json",
        ]
        for term in forbidden_terms:
            self.assertNotIn(term, document)


if __name__ == "__main__":
    unittest.main()
