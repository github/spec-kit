from __future__ import annotations

import unittest
import json
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError

from validators.speckit_implement_contract import (
    validate_behavior_contract_bundle,
    validate_behavior_draft_contract,
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
AGENTS_PATH = REPO_ROOT / "AGENTS.md"
EXTENSION_GOVERNANCE_PATH = REPO_ROOT / "docs" / "extension-governance.md"
SPECIFY_COMMAND_PATH = REPO_ROOT / "commands" / "speckit.specify.md"
CLARIFY_COMMAND_PATH = REPO_ROOT / "commands" / "speckit.clarify.md"
CHECKLIST_COMMAND_PATH = REPO_ROOT / "commands" / "speckit.checklist.md"
CONSTITUTION_COMMAND_PATH = REPO_ROOT / "commands" / "speckit.constitution.md"
ANALYZE_COMMAND_PATH = REPO_ROOT / "commands" / "speckit.analyze.md"
PLAN_COMMAND_PATH = REPO_ROOT / "commands" / "speckit.plan.md"
TASKS_COMMAND_PATH = REPO_ROOT / "commands" / "speckit.tasks.md"
IMPLEMENT_COMMAND_PATH = REPO_ROOT / "commands" / "speckit.implement.md"
CONSTITUTION_TEMPLATE_PATH = REPO_ROOT / "templates" / "constitution-template.md"
PLAN_TEMPLATE_PATH = REPO_ROOT / "templates" / "plan-template.md"
REQUIREMENTS_DEV_PATH = REPO_ROOT / "requirements-dev.txt"
MANIFEST_SCHEMA_PATH = REPO_ROOT / "schemas" / "speckit.implement.manifest.v1.schema.json"
HANDOFF_SCHEMA_PATH = REPO_ROOT / "schemas" / "speckit.implement.handoff.v2.schema.json"
RECEIPT_SCHEMA_PATH = REPO_ROOT / "schemas" / "speckit.implement.receipt.v1.schema.json"
BEHAVIOR_SCHEMA_PATHS = {
    "speckit.behavior.scenarios.draft.v1": REPO_ROOT
    / "schemas"
    / "speckit.behavior.scenarios.draft.v1.schema.json",
    "speckit.behavior.uif.intent.v1": REPO_ROOT
    / "schemas"
    / "speckit.behavior.uif.intent.v1.schema.json",
    "speckit.behavior.data_fixtures.intent.v1": REPO_ROOT
    / "schemas"
    / "speckit.behavior.data-fixtures.intent.v1.schema.json",
    "speckit.behavior.uif.expected.v1": REPO_ROOT
    / "schemas"
    / "speckit.behavior.uif.expected.v1.schema.json",
    "speckit.behavior.scenario_instances.v1": REPO_ROOT
    / "schemas"
    / "speckit.behavior.scenario-instances.v1.schema.json",
    "speckit.behavior.data_fixtures.v1": REPO_ROOT
    / "schemas"
    / "speckit.behavior.data-fixtures.v1.schema.json",
    "speckit.behavior.assertions.v1": REPO_ROOT
    / "schemas"
    / "speckit.behavior.assertions.v1.schema.json",
}
BEHAVIOR_TEMPLATE_PATHS = {
    "behavior-bdd-draft-template": REPO_ROOT / "templates" / "behavior" / "bdd-draft.feature",
    "behavior-scenarios-draft-template": REPO_ROOT
    / "templates"
    / "behavior"
    / "behavior-scenarios-draft.json",
    "behavior-uif-intent-template": REPO_ROOT / "templates" / "behavior" / "uif-intent.json",
    "behavior-data-fixtures-intent-template": REPO_ROOT
    / "templates"
    / "behavior"
    / "data-fixtures-intent.json",
    "behavior-testability-checklist-template": REPO_ROOT
    / "templates"
    / "behavior"
    / "behavior-testability-checklist.md",
    "behavior-bdd-contract-template": REPO_ROOT / "templates" / "behavior" / "bdd-contract.feature",
    "behavior-uif-expected-template": REPO_ROOT / "templates" / "behavior" / "uif-expected.json",
    "behavior-scenario-instances-template": REPO_ROOT
    / "templates"
    / "behavior"
    / "scenario-instances.json",
    "behavior-data-fixtures-template": REPO_ROOT / "templates" / "behavior" / "data-fixtures.json",
    "behavior-assertions-template": REPO_ROOT / "templates" / "behavior" / "assertions.json",
}
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
        "task_ids": ["T001"] if task_ids is None else task_ids,
        "vertical_capability": vertical_capability,
    }


def minimal_manifest(
    *,
    shards: list[dict] | None = None,
    dependencies: list[dict] | None = None,
    dispatch_order: list[list[str]] | None = None,
    vertical_capability: str = "service-flow",
    execution_mode: str = "isolated_subagent",
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
        "execution_mode": execution_mode,
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
    task_ids = ["T001"] if task_ids is None else task_ids
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


def minimal_behavior_scenarios_draft() -> dict:
    return {
        "contract_type": "speckit.behavior.scenarios.draft.v1",
        "feature": "refund-application",
        "scenarios": [
            {
                "id": "SCN-001",
                "title": "Submit refund",
                "type": "positive",
                "given": ["FIX-BUYER"],
                "when": ["click_refund", "submit_refund"],
                "then": ["show_refund_submitted"],
                "source": "plan-phase-0",
            }
        ],
    }


def minimal_uif_intent() -> dict:
    return {
        "contract_type": "speckit.behavior.uif.intent.v1",
        "feature": "refund-application",
        "intents": [
            {
                "id": "UIF-INTENT-001",
                "start_view": "OrderDetailPage",
                "events": [{"name": "submit_refund", "label": "Submit refund"}],
                "expected_feedback": ["Refund submitted"],
                "possible_transition_types": ["local_route", "api_call"],
            }
        ],
    }


def minimal_data_fixtures_intent() -> dict:
    return {
        "contract_type": "speckit.behavior.data_fixtures.intent.v1",
        "fixtures": [
            {
                "id": "FIX-BUYER",
                "description": "Buyer user",
                "required_for": ["SCN-001"],
                "required_states": {"user.role": "buyer"},
            }
        ],
    }


def minimal_uif_expected() -> dict:
    return {
        "contract_type": "speckit.behavior.uif.expected.v1",
        "id": "UIF-001",
        "source": "behavior/uif.intent.json",
        "type": "expected",
        "start_view": {"id": "VIEW-ORDER-DETAIL", "name": "Order detail"},
        "steps": [
            {"id": "EVT-SUBMIT-REFUND", "type": "user_event", "label": "Submit refund"},
            {"type": "api_call", "api": {"method": "POST", "path": "/orders/{orderId}/refund"}},
        ],
        "feedback_candidates": [
            {"id": "FB-SUCCESS", "type": "toast", "message": "Refund submitted"}
        ],
    }


def minimal_behavior_scenario_instances() -> dict:
    return {
        "contract_type": "speckit.behavior.scenario_instances.v1",
        "scenarios": [
            {
                "id": "SCN-001",
                "title": "Submit refund",
                "type": "positive",
                "uif_path_id": "UIF-001",
                "fixture_ids": ["FIX-BUYER"],
                "request_case": {"id": "REQ-001", "reason": "QUALITY_ISSUE"},
                "expected_response": {"business_code": "SUCCESS"},
                "expected_feedback": {"message": "Refund submitted"},
                "assertion_ids": ["AST-001"],
            }
        ],
    }


def minimal_behavior_data_fixtures() -> dict:
    return {
        "contract_type": "speckit.behavior.data_fixtures.v1",
        "fixtures": [
            {
                "id": "FIX-BUYER",
                "name": "Buyer user",
                "entities": ["user"],
                "required_states": {"user.role": "buyer"},
                "constraints": [],
                "setup_strategy": "factory",
            }
        ],
    }


def minimal_behavior_assertions() -> dict:
    return {
        "contract_type": "speckit.behavior.assertions.v1",
        "assertions": [
            {
                "id": "AST-001",
                "target": "refund.status",
                "operator": "equals",
                "expected": "PENDING",
            }
        ],
    }


class PresetContractTests(unittest.TestCase):
    def test_preset_manifest_contract(self) -> None:
        data = yaml.safe_load(PRESET_PATH.read_text(encoding="utf-8"))

        self.assertEqual("1.0", data["schema_version"])
        self.assertEqual("workflow-preset", data["preset"]["id"])
        self.assertEqual("Workflow Preset", data["preset"]["name"])
        self.assertEqual("1.3.1", data["preset"]["version"])
        self.assertEqual(
            "Behavior-first specification, design artifacts, and agent-native handoff orchestration",
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
            ["behavior", "bdd", "planning", "implementation", "handoff"],
            data["tags"],
        )

        provides = data["provides"]["templates"]
        self.assertEqual(30, len(provides))
        entries = {entry["name"]: entry for entry in provides}
        self.assertNotIn("behavior-open-questions-template", entries)
        self.assertNotIn("speckit-behavior-open-questions-v1-schema", entries)

        plan_template = entries["plan-template"]
        self.assertEqual("template", plan_template["type"])
        self.assertEqual("templates/plan-template.md", plan_template["file"])
        self.assertEqual("plan-template", plan_template["replaces"])
        self.assertEqual("wrap", plan_template["strategy"])

        constitution_template = entries["constitution-template"]
        self.assertEqual("template", constitution_template["type"])
        self.assertEqual("templates/constitution-template.md", constitution_template["file"])
        self.assertEqual("constitution-template", constitution_template["replaces"])
        self.assertEqual("wrap", constitution_template["strategy"])

        for command_name in ("speckit.plan", "speckit.tasks"):
            command = entries[command_name]
            self.assertEqual("command", command["type"])
            self.assertEqual(f"commands/{command_name}.md", command["file"])
            self.assertEqual(command_name, command["replaces"])
            self.assertEqual("wrap", command["strategy"])

        self.assertEqual(
            "Wrap core planning with Phase 0 behavior projection and optional design artifacts",
            entries["speckit.plan"]["description"],
        )
        self.assertEqual(
            "Wrap core specification with spec-only requirement ownership",
            entries["speckit.specify"]["description"],
        )
        self.assertEqual(
            "Wrap core clarification with spec-only ambiguity resolution",
            entries["speckit.clarify"]["description"],
        )
        self.assertEqual(
            "Wrap core checklist generation with BDD readiness gate",
            entries["speckit.checklist"]["description"],
        )

        for command_name in (
            "speckit.specify",
            "speckit.clarify",
            "speckit.checklist",
            "speckit.constitution",
            "speckit.analyze",
        ):
            command = entries[command_name]
            self.assertEqual("command", command["type"])
            self.assertEqual(f"commands/{command_name}.md", command["file"])
            self.assertEqual(command_name, command["replaces"])
            self.assertEqual("wrap", command["strategy"])

        self.assertEqual(
            "Wrap core constitution updates with change scope granularity governance",
            entries["speckit.constitution"]["description"],
        )
        self.assertEqual(
            "Add change scope granularity governance to the constitution template",
            entries["constitution-template"]["description"],
        )

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

        for template_name, template_path in BEHAVIOR_TEMPLATE_PATHS.items():
            template = entries[template_name]
            self.assertEqual("template", template["type"])
            self.assertEqual(
                str(template_path.relative_to(REPO_ROOT)),
                template["file"],
            )
            self.assertEqual(template_name, template["replaces"])
            self.assertEqual("replace", template["strategy"])

        for contract_type, schema_path in BEHAVIOR_SCHEMA_PATHS.items():
            schema_name = f"{contract_type}-schema".replace(".", "-").replace("_", "-")
            schema = entries[schema_name]
            self.assertEqual("template", schema["type"])
            self.assertEqual(str(schema_path.relative_to(REPO_ROOT)), schema["file"])
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
        self.assertNotIn("test-plan.md", command)
        self.assertIn("strategy: wrap", command)
        self.assertIn("Generate the two design artifacts only when useful", command)
        self.assertIn("Keep `plan.md` as summary/navigation", command)
        self.assertIn("validation decisions belong in `research.md`", command)
        self.assertIn("executable validation paths belong in `quickstart.md`", command)
        self.assertIn("final report must list generated artifacts", command)
        self.assertNotIn("speckit.tasks", command)
        self.assertNotIn("speckit.implement", command)

    def test_plan_template_navigation_contract(self) -> None:
        template = PLAN_TEMPLATE_PATH.read_text(encoding="utf-8")

        self.assertIn("{CORE_TEMPLATE}", template)
        self.assertIn("## Design Artifacts", template)
        self.assertIn("./class-diagram.md", template)
        self.assertIn("./contracts/sequences.md", template)
        self.assertNotIn("test-plan.md", template)
        self.assertIn("./data-model.md", template)
        self.assertIn("./contracts/", template)
        self.assertIn("./quickstart.md", template)

    def test_constitution_change_scope_granularity_contract(self) -> None:
        command = CONSTITUTION_COMMAND_PATH.read_text(encoding="utf-8")
        template = CONSTITUTION_TEMPLATE_PATH.read_text(encoding="utf-8")

        for document in (command, template):
            self.assertIn("{CORE_TEMPLATE}", document)
            self.assertIn("Change Scope Granularity", document)
            self.assertIn("R/M/U/O", document)
            self.assertIn("Planning locks M + U", document)

        self.assertIn("strategy: wrap", command)
        self.assertIn("Spec Kit planning and execution MUST use R/M/U/O scope granularity", template)
        self.assertIn("This principle applies from planning onward", template)
        self.assertIn("Requirement specification, clarification, and checklist readiness MUST NOT infer M/U/O boundaries", template)
        self.assertIn("preserve the Change Scope Granularity principle", command)
        self.assertIn("must not remove, weaken, or contradict", command)

    def test_change_scope_granularity_stage_references(self) -> None:
        plan = PLAN_COMMAND_PATH.read_text(encoding="utf-8")
        tasks = TASKS_COMMAND_PATH.read_text(encoding="utf-8")
        analyze = ANALYZE_COMMAND_PATH.read_text(encoding="utf-8")
        implement = IMPLEMENT_COMMAND_PATH.read_text(encoding="utf-8")

        self.assertIn("Apply the constitution's Change Scope Granularity principle.", plan)
        self.assertIn("During planning, lock the change scope to `M + U`", plan)
        self.assertIn("Do not lock operation-level implementation details or concrete write paths.", plan)

        self.assertIn("Preserve the planned `M + U` scope", tasks)
        self.assertIn("Do not generate handoff fields or `allowed_write_paths`.", tasks)

        self.assertIn("Check that tasks preserve the planned `M + U` scope.", analyze)
        self.assertIn("Report missing, widened, or ambiguous scope boundaries as blockers.", analyze)

        self.assertIn(
            "Map planned `U` design objects to concrete source, test, fixture, configuration, and receipt paths before worker execution.",
            implement,
        )
        self.assertIn("If the mapping is ambiguous, record `context_gaps`", implement)
        self.assertIn("do not widen to repository scope or broad module scope.", implement)

    def test_preplanning_commands_do_not_infer_scope_granularity(self) -> None:
        for path in (SPECIFY_COMMAND_PATH, CLARIFY_COMMAND_PATH, CHECKLIST_COMMAND_PATH):
            command = path.read_text(encoding="utf-8")
            for forbidden in (
                "Change Scope Granularity",
                "R/M/U/O",
                "M + U",
                "U -> concrete paths",
                "module/capability plus design object",
                "concrete write paths",
                "allowed_write_paths",
                "context_gaps",
            ):
                self.assertNotIn(forbidden, command, f"{path} contains {forbidden}")

    def test_tasks_command_wrapper_contract(self) -> None:
        tasks = TASKS_COMMAND_PATH.read_text(encoding="utf-8")

        self.assertIn("{CORE_TEMPLATE}", tasks)
        self.assertIn("class-diagram.md", tasks)
        self.assertIn("contracts/sequences.md", tasks)
        self.assertNotIn("test-plan.md", tasks)
        self.assertIn("strategy: wrap", tasks)
        self.assertIn("implementation, integration, orchestration", tasks)
        self.assertIn("existing checklist format and user-story organization", tasks)
        self.assertIn("Test Strategy Derivation", tasks)
        self.assertIn("derive the test level", tasks)
        self.assertIn("fixture/mock/sandbox/real-system strategy", tasks)
        self.assertIn("inline evidence requirement", tasks)

    def test_behavior_first_command_wrapper_contracts(self) -> None:
        specify = SPECIFY_COMMAND_PATH.read_text(encoding="utf-8")
        clarify = CLARIFY_COMMAND_PATH.read_text(encoding="utf-8")
        checklist = CHECKLIST_COMMAND_PATH.read_text(encoding="utf-8")

        for command in (specify, clarify, checklist):
            self.assertIn("{CORE_TEMPLATE}", command)
            self.assertIn("strategy: wrap", command)

        self.assertIn("Spec-Only Requirement Policy", specify)
        self.assertIn("produce or update `spec.md` only", specify)
        self.assertIn("This command writes only `spec.md`", specify)
        self.assertIn("Product requirements stay in `spec.md`", specify)
        self.assertIn("report the `spec.md` sections created or updated", specify)
        for forbidden in (
            "/speckit.plan",
            "/speckit.checklist",
            "behavior/bdd.draft.feature",
            "behavior/behavior-scenarios.draft.json",
            "behavior/uif.intent.json",
            "behavior/data-fixtures.intent.json",
            "behavior/open-questions.json",
            "formal behavior contracts",
            "interface schemas",
            "validation commands",
            "task plans",
            "design artifacts",
        ):
            self.assertNotIn(forbidden, specify)
        self.assertNotIn("contracts/bdd/", specify)
        self.assertNotIn("contracts/uif/", specify)

        self.assertIn("Spec-Only Clarification Policy", clarify)
        self.assertIn("Use `spec.md` as the clarification source", clarify)
        self.assertIn("Do not read or update behavior draft artifacts", clarify)
        self.assertIn("Product requirements stay in `spec.md`", clarify)
        self.assertIn("only after user-provided answers", clarify)
        for forbidden in (
            "behavior/bdd.draft.feature",
            "behavior/behavior-scenarios.draft.json",
            "behavior/uif.intent.json",
            "behavior/data-fixtures.intent.json",
            "behavior/open-questions.json",
        ):
            self.assertNotIn(forbidden, clarify)

        self.assertIn("BDD Readiness Gate", checklist)
        self.assertIn("checklists/behavior-testability.md", checklist)
        self.assertIn("directly from `spec.md`", checklist)
        self.assertIn("plan-entry quality gate", checklist)
        self.assertIn("Do not proceed to `/speckit.plan`", checklist)
        self.assertIn("Return to `/speckit.clarify` or `/speckit.specify`", checklist)
        self.assertIn("User Story Readiness", checklist)
        self.assertIn("Acceptance Criteria Quality", checklist)
        self.assertIn("Scenario Coverage", checklist)
        self.assertIn("Given Readiness", checklist)
        self.assertIn("When Readiness", checklist)
        self.assertIn("Then Readiness", checklist)
        self.assertIn("Gate Status", checklist)
        self.assertIn("PASS", checklist)
        self.assertIn("BLOCKED", checklist)
        self.assertIn("Blocking Items", checklist)
        self.assertIn("checklist artifacts only", checklist)

    def test_behavior_first_plan_and_tasks_awareness_contract(self) -> None:
        plan = PLAN_COMMAND_PATH.read_text(encoding="utf-8")
        tasks = TASKS_COMMAND_PATH.read_text(encoding="utf-8")
        template = PLAN_TEMPLATE_PATH.read_text(encoding="utf-8")
        implement = IMPLEMENT_COMMAND_PATH.read_text(encoding="utf-8")

        for term in (
            "behavior/bdd.draft.feature",
            "behavior/uif.intent.json",
            "behavior/data-fixtures.intent.json",
            "contracts/bdd/",
            "contracts/uif/",
            "contracts/behavior/",
            "formal behavior contracts",
            "must formalize",
            "N/A or blocker",
            "research.md",
            "test level",
            "fixture strategy",
            "mock/external-system strategy",
            "BehaviorScenarioInstance",
            "DataFixture",
            "UIFPath",
            "FeedbackView",
            "BehaviorAssertion",
        ):
            self.assertIn(term, plan)

        for term in (
            "Phase 0 Preflight",
            "Phase 0 Behavior Projection",
            "checklists/behavior-testability.md has passed",
            "before core research or design work",
            "behavior/behavior-scenarios.draft.json",
            "report-only/no-write failure",
            "must not create or update behavior artifacts",
            "Do not discover new requirement problems",
            "Do not ask clarification questions",
            "Do not modify `spec.md`",
            "upstream gate failure",
            "Return to `/speckit.checklist` or `/speckit.clarify`",
        ):
            self.assertIn(term, plan)

        self.assertNotIn("empty, or records only an upstream gate failure", plan)
        self.assertNotIn("behavior/open-questions.json", plan)
        self.assertNotIn("test-plan.md", plan)

        for term in (
            "contracts/bdd/",
            "contracts/uif/",
            "contracts/behavior/",
            "test-first",
            "existing checklist format and user-story organization",
            "For each BehaviorScenarioInstance",
            "fixture task",
            "BDD/E2E or contract test task",
            "implementation task",
            "verification evidence task",
            "For each UIF user_event",
            "For each UIF api_call",
            "For each quickstart validation path",
            "derive the test level",
            "fixture/mock/sandbox/real-system strategy",
            "inline evidence requirement",
        ):
            self.assertIn(term, tasks)

        self.assertNotIn("test-plan.md", tasks)

        self.assertIn("./behavior/bdd.draft.feature", template)
        self.assertIn("./contracts/bdd/", template)
        self.assertIn("./contracts/uif/", template)
        self.assertIn("./contracts/behavior/", template)

        self.assertIn("contracts/bdd/", implement)
        self.assertIn("contracts/uif/", implement)
        self.assertIn("contracts/behavior/", implement)
        self.assertIn("behavior contract constraints", implement)
        self.assertIn("validation_evidence must reference", implement)
        self.assertIn("BDD scenario", implement)
        self.assertIn("behavior assertion", implement)
        self.assertIn("API contract", implement)
        self.assertIn("quickstart path", implement)

    def test_bdd_formalization_strengthens_reasoning_without_traceability_system(self) -> None:
        plan = PLAN_COMMAND_PATH.read_text(encoding="utf-8")
        bdd_contract_template = BEHAVIOR_TEMPLATE_PATHS[
            "behavior-bdd-contract-template"
        ].read_text(encoding="utf-8")

        for term in (
            "When formalizing BDD Draft into `contracts/bdd/*.feature`",
            "Preserve scenario intent and business outcome from the draft.",
            "Convert ambiguous Given steps into formal fixture, actor, state, permission, or start-view conditions.",
            "Convert When steps into formal user events, request cases, or system triggers aligned with UIF/API contracts.",
            "Convert Then steps into formal feedback, response, business state, or assertion expectations.",
            "If a step cannot be formalized without inventing information, record `N/A or blocker` instead of guessing.",
            "Do not introduce independent traceability mechanisms for BDD formalization.",
        ):
            self.assertIn(term, plan)

        for forbidden in (
            "@SCN-",
            "trace table",
            "coverage matrix",
            "reverse index",
        ):
            self.assertNotIn(forbidden, plan)
            self.assertNotIn(forbidden, bdd_contract_template)

    def test_analyze_command_owns_vertical_consistency_contract(self) -> None:
        analyze = ANALYZE_COMMAND_PATH.read_text(encoding="utf-8")

        self.assertIn("{CORE_TEMPLATE}", analyze)
        self.assertIn("strategy: wrap", analyze)
        self.assertIn("vertical consistency", analyze)
        self.assertIn("spec -> BDD/UIF intent -> contracts -> tasks", analyze)
        self.assertIn("spec.md user stories have BDD coverage", analyze)
        self.assertIn("BDD Given steps map to fixtures", analyze)
        self.assertIn("BDD When steps map to UIF events or API requests", analyze)
        self.assertIn("BDD Then steps map to feedback or behavior assertions", analyze)
        self.assertIn("behavior/uif.intent.json is formalized into contracts/uif/*.expected.json", analyze)
        self.assertIn("behavior drafts exist but formal contracts are missing", analyze)
        self.assertIn("source draft and missing planning input", analyze)
        self.assertNotIn("behavior/open-questions.json", analyze)
        self.assertIn("N/A or blocker", analyze)
        self.assertIn("UIF API calls exist in contracts/api/", analyze)
        self.assertIn("behavior contracts cover scenarios, fixtures, and assertions", analyze)
        self.assertIn("tasks.md covers BDD, UIF, API, fixtures, and quickstart validation paths", analyze)
        self.assertNotIn("uif.actual.json", analyze)
        self.assertNotIn("uif.diff.json", analyze)
        self.assertNotIn("Actual UIF", analyze)

    def test_actual_uif_artifacts_are_not_part_of_preset_contract(self) -> None:
        paths = [
            README_PATH,
            SPECIFY_COMMAND_PATH,
            CLARIFY_COMMAND_PATH,
            CHECKLIST_COMMAND_PATH,
            ANALYZE_COMMAND_PATH,
            PLAN_COMMAND_PATH,
            TASKS_COMMAND_PATH,
            IMPLEMENT_COMMAND_PATH,
            PRESET_PATH,
        ]
        forbidden_terms = [
            "Expected UIF vs Actual UIF",
            "Actual UIF",
            "uif.actual.json",
            "uif.diff.json",
            "from implementation",
            "implementation-derived UIF",
            "static analysis tooling",
        ]
        for path in paths:
            document = path.read_text(encoding="utf-8")
            for term in forbidden_terms:
                self.assertNotIn(term, document, f"{path} contains {term}")

    def test_behavior_first_templates_exist_and_are_decoupled(self) -> None:
        for path in BEHAVIOR_TEMPLATE_PATHS.values():
            self.assertTrue(path.exists(), path)

        self.assertIn("Feature:", BEHAVIOR_TEMPLATE_PATHS["behavior-bdd-draft-template"].read_text())
        self.assertIn("Feature:", BEHAVIOR_TEMPLATE_PATHS["behavior-bdd-contract-template"].read_text())
        self.assertIn(
            "Behavior Testability Checklist",
            BEHAVIOR_TEMPLATE_PATHS["behavior-testability-checklist-template"].read_text(),
        )
        behavior_checklist_template = BEHAVIOR_TEMPLATE_PATHS[
            "behavior-testability-checklist-template"
        ].read_text(encoding="utf-8")
        self.assertIn("Gate Status: PASS|BLOCKED", behavior_checklist_template)
        self.assertIn("Blocking Items:", behavior_checklist_template)
        self.assertIn("none", behavior_checklist_template)
        self.assertNotIn(
            "No unchecked BDD readiness item blocks `/speckit.plan`",
            behavior_checklist_template,
        )
        self.assertFalse((REPO_ROOT / "templates" / "behavior" / "open-questions.json").exists())
        self.assertFalse(
            (
                REPO_ROOT
                / "schemas"
                / "speckit.behavior.open-questions.v1.schema.json"
            ).exists()
        )

        for template_name in (
            "behavior-scenarios-draft-template",
            "behavior-uif-intent-template",
            "behavior-data-fixtures-intent-template",
            "behavior-uif-expected-template",
            "behavior-scenario-instances-template",
            "behavior-data-fixtures-template",
            "behavior-assertions-template",
        ):
            self.assertIn(
                "contract_type",
                BEHAVIOR_TEMPLATE_PATHS[template_name].read_text(encoding="utf-8"),
            )

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
            "agent-runtime=<spec-kit-integration-key>",
            "Isolation Policy",
            "isolated_subagent",
            "manual_fresh_worker_session",
            "isolated subagent/subsession",
            "Core mode must not execute Worker handoffs inline in the same conversation context",
            "If isolated dispatch is unavailable or unknown, Core mode writes the manifest and handoffs, then stops with Worker-mode instructions.",
            "Worker runs receive only the Worker prompt and one handoff JSON path.",
            "Core consumes planner outputs and worker receipts, not worker conversation history.",
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

        self.assertIn("include relevant `research.md` validation decisions", command)
        self.assertIn("include relevant `quickstart.md` validation paths", command)
        self.assertNotIn("test-plan.md", command)

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

    def test_manifest_schema_declares_runtime_neutral_execution_mode(self) -> None:
        schema = json.loads(MANIFEST_SCHEMA_PATH.read_text(encoding="utf-8"))

        self.assertIn("execution_mode", schema["required"])
        self.assertEqual(
            {"isolated_subagent", "manual_fresh_worker_session"},
            set(schema["properties"]["execution_mode"]["enum"]),
        )

    def test_behavior_first_schema_contracts_accept_minimal_examples(self) -> None:
        examples = {
            "speckit.behavior.scenarios.draft.v1": minimal_behavior_scenarios_draft(),
            "speckit.behavior.uif.intent.v1": minimal_uif_intent(),
            "speckit.behavior.data_fixtures.intent.v1": minimal_data_fixtures_intent(),
            "speckit.behavior.uif.expected.v1": minimal_uif_expected(),
            "speckit.behavior.scenario_instances.v1": minimal_behavior_scenario_instances(),
            "speckit.behavior.data_fixtures.v1": minimal_behavior_data_fixtures(),
            "speckit.behavior.assertions.v1": minimal_behavior_assertions(),
        }

        for contract_type, path in BEHAVIOR_SCHEMA_PATHS.items():
            schema = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual("object", schema["type"])
            self.assertIn("required", schema)
            self.assertIn("properties", schema)
            self.assertEqual(contract_type, schema["properties"]["contract_type"]["const"])
            Draft202012Validator(schema).validate(examples[contract_type])

    def test_behavior_draft_schema_rejects_empty_given_when_then(self) -> None:
        schema = json.loads(
            BEHAVIOR_SCHEMA_PATHS["speckit.behavior.scenarios.draft.v1"].read_text(
                encoding="utf-8"
            )
        )

        for field in ("given", "when", "then"):
            with self.subTest(field=field):
                draft = minimal_behavior_scenarios_draft()
                draft["scenarios"][0][field] = []

                with self.assertRaises(ValidationError):
                    Draft202012Validator(schema).validate(draft)

    def test_behavior_scenario_instances_schema_rejects_empty_contract_refs(self) -> None:
        schema = json.loads(
            BEHAVIOR_SCHEMA_PATHS["speckit.behavior.scenario_instances.v1"].read_text(
                encoding="utf-8"
            )
        )

        for field in ("fixture_ids", "assertion_ids"):
            with self.subTest(field=field):
                instances = minimal_behavior_scenario_instances()
                instances["scenarios"][0][field] = []

                with self.assertRaises(ValidationError):
                    Draft202012Validator(schema).validate(instances)

    def test_expected_uif_schema_rejects_underspecified_typed_steps(self) -> None:
        schema = json.loads(
            BEHAVIOR_SCHEMA_PATHS["speckit.behavior.uif.expected.v1"].read_text(
                encoding="utf-8"
            )
        )

        underspecified_steps = [
            {"type": "api_call"},
            {"type": "local_route"},
            {"type": "user_event"},
        ]
        for step in underspecified_steps:
            with self.subTest(step_type=step["type"]):
                uif = minimal_uif_expected()
                uif["steps"] = [step]

                with self.assertRaises(ValidationError):
                    Draft202012Validator(schema).validate(uif)

    def test_behavior_draft_validator_rejects_fixture_for_unknown_scenario(self) -> None:
        fixtures = minimal_data_fixtures_intent()
        fixtures["fixtures"][0]["required_for"] = ["SCN-404"]

        with self.assertRaises(ValueError):
            validate_behavior_draft_contract(
                minimal_behavior_scenarios_draft(),
                fixtures,
            )

    def test_behavior_draft_validator_rejects_empty_given_when_then(self) -> None:
        for field in ("given", "when", "then"):
            with self.subTest(field=field):
                draft = minimal_behavior_scenarios_draft()
                draft["scenarios"][0][field] = []

                with self.assertRaisesRegex(ValueError, field):
                    validate_behavior_draft_contract(
                        draft,
                        minimal_data_fixtures_intent(),
                    )

    def test_behavior_draft_validator_accepts_valid_cross_fields(self) -> None:
        validate_behavior_draft_contract(
            minimal_behavior_scenarios_draft(),
            minimal_data_fixtures_intent(),
        )

    def test_behavior_contract_validator_rejects_missing_fixture_reference(self) -> None:
        instances = minimal_behavior_scenario_instances()
        instances["scenarios"][0]["fixture_ids"] = ["FIX-MISSING"]

        with self.assertRaises(ValueError):
            validate_behavior_contract_bundle(
                instances,
                minimal_behavior_data_fixtures(),
                minimal_behavior_assertions(),
                [minimal_uif_expected()],
            )

    def test_behavior_contract_validator_rejects_empty_contract_refs(self) -> None:
        for field in ("fixture_ids", "assertion_ids"):
            with self.subTest(field=field):
                instances = minimal_behavior_scenario_instances()
                instances["scenarios"][0][field] = []

                with self.assertRaisesRegex(ValueError, field):
                    validate_behavior_contract_bundle(
                        instances,
                        minimal_behavior_data_fixtures(),
                        minimal_behavior_assertions(),
                        [minimal_uif_expected()],
                    )

    def test_behavior_contract_validator_rejects_underspecified_uif_steps(self) -> None:
        for step in (
            {"type": "api_call"},
            {"type": "local_route"},
            {"type": "user_event"},
        ):
            with self.subTest(step_type=step["type"]):
                uif = minimal_uif_expected()
                uif["steps"] = [step]

                with self.assertRaises(ValueError):
                    validate_behavior_contract_bundle(
                        minimal_behavior_scenario_instances(),
                        minimal_behavior_data_fixtures(),
                        minimal_behavior_assertions(),
                        [uif],
                    )

    def test_behavior_contract_validator_accepts_valid_cross_fields(self) -> None:
        validate_behavior_contract_bundle(
            minimal_behavior_scenario_instances(),
            minimal_behavior_data_fixtures(),
            minimal_behavior_assertions(),
            [minimal_uif_expected()],
        )

    def test_manifest_schema_accepts_minimal_valid_manifest(self) -> None:
        schema = json.loads(MANIFEST_SCHEMA_PATH.read_text(encoding="utf-8"))
        manifest = minimal_manifest(shards=[], dispatch_order=[])
        Draft202012Validator(schema).validate(manifest)

    def test_manifest_schema_rejects_unknown_execution_mode(self) -> None:
        schema = json.loads(MANIFEST_SCHEMA_PATH.read_text(encoding="utf-8"))
        manifest = minimal_manifest(execution_mode="inline_same_session")

        with self.assertRaises(ValidationError):
            Draft202012Validator(schema).validate(manifest)

    def test_manifest_schema_rejects_empty_shard_task_ids(self) -> None:
        schema = json.loads(MANIFEST_SCHEMA_PATH.read_text(encoding="utf-8"))
        manifest = minimal_manifest(shards=[minimal_shard(task_ids=[])])

        with self.assertRaises(ValidationError):
            Draft202012Validator(schema).validate(manifest)

    def test_validate_manifest_contract_rejects_unknown_dispatch_order_shard(self) -> None:
        manifest = minimal_manifest(dispatch_order=[["S02-service-flow-01"]])
        with self.assertRaises(ValueError):
            validate_manifest_contract(manifest)

    def test_validate_manifest_contract_rejects_unknown_execution_mode(self) -> None:
        manifest = minimal_manifest(execution_mode="inline_same_session")
        with self.assertRaisesRegex(ValueError, "execution_mode"):
            validate_manifest_contract(manifest)

    def test_validate_manifest_contract_rejects_duplicate_shard_ids(self) -> None:
        manifest = minimal_manifest(
            shards=[
                minimal_shard(task_ids=["T001"]),
                minimal_shard(task_ids=["T002"]),
            ],
            dispatch_order=[[SHARD_ID]],
        )
        with self.assertRaisesRegex(ValueError, "duplicates shard_id"):
            validate_manifest_contract(manifest)

    def test_validate_manifest_contract_rejects_empty_shard_task_ids(self) -> None:
        manifest = minimal_manifest(shards=[minimal_shard(task_ids=[])])
        with self.assertRaisesRegex(ValueError, "task_ids"):
            validate_manifest_contract(manifest)

    def test_validate_manifest_contract_rejects_duplicate_shard_task_ids(self) -> None:
        manifest = minimal_manifest(shards=[minimal_shard(task_ids=["T001", "T001"])])
        with self.assertRaisesRegex(ValueError, "task_ids"):
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

    def test_validate_implement_contract_rejects_overlapping_allowed_write_paths(self) -> None:
        second_shard_id = "S02-service-flow-02"
        second_receipt_path = f"{HANDOFF_DIR}/results/{second_shard_id}.json"
        second_handoff_path = f"{HANDOFF_DIR}/{second_shard_id}.json"
        manifest = minimal_manifest(
            shards=[
                minimal_shard(),
                minimal_shard(shard_id=second_shard_id, task_ids=["T002"]),
            ],
            dispatch_order=[[SHARD_ID, second_shard_id]],
        )

        with self.assertRaisesRegex(ValueError, "allowed_write_paths"):
            validate_implement_contract(
                manifest,
                handoffs_by_path={
                    f"{HANDOFF_DIR}/{SHARD_ID}.json": minimal_handoff(),
                    second_handoff_path: minimal_handoff(
                        shard_id=second_shard_id,
                        task_ids=["T002"],
                        allowed_write_paths=[SERVICE_PATH, second_receipt_path],
                    ),
                },
                receipts_by_path={},
            )

    def test_validate_implement_contract_rejects_contained_allowed_write_paths(self) -> None:
        second_shard_id = "S02-service-flow-02"
        second_receipt_path = f"{HANDOFF_DIR}/results/{second_shard_id}.json"
        second_handoff_path = f"{HANDOFF_DIR}/{second_shard_id}.json"
        manifest = minimal_manifest(
            shards=[
                minimal_shard(),
                minimal_shard(shard_id=second_shard_id, task_ids=["T002"]),
            ],
            dispatch_order=[[SHARD_ID, second_shard_id]],
        )

        with self.assertRaisesRegex(ValueError, "allowed_write_paths"):
            validate_implement_contract(
                manifest,
                handoffs_by_path={
                    f"{HANDOFF_DIR}/{SHARD_ID}.json": minimal_handoff(),
                    second_handoff_path: minimal_handoff(
                        shard_id=second_shard_id,
                        task_ids=["T002"],
                        allowed_write_paths=[f"{FEATURE_PATH}/src", second_receipt_path],
                    ),
                },
                receipts_by_path={},
            )

    def test_validate_implement_contract_rejects_overlapping_capability_owns(self) -> None:
        second_shard_id = "S02-service-flow-02"
        second_receipt_path = f"{HANDOFF_DIR}/results/{second_shard_id}.json"
        second_handoff_path = f"{HANDOFF_DIR}/{second_shard_id}.json"
        first_handoff = minimal_handoff()
        first_handoff["capability_boundary"]["owns"] = [SERVICE_PATH]
        second_handoff = minimal_handoff(
            shard_id=second_shard_id,
            task_ids=["T002"],
            allowed_write_paths=[f"{FEATURE_PATH}/src/other.py", second_receipt_path],
        )
        second_handoff["capability_boundary"]["owns"] = [SERVICE_PATH]
        manifest = minimal_manifest(
            shards=[
                minimal_shard(),
                minimal_shard(shard_id=second_shard_id, task_ids=["T002"]),
            ],
            dispatch_order=[[SHARD_ID, second_shard_id]],
        )

        with self.assertRaisesRegex(ValueError, "capability_boundary.owns"):
            validate_implement_contract(
                manifest,
                handoffs_by_path={
                    f"{HANDOFF_DIR}/{SHARD_ID}.json": first_handoff,
                    second_handoff_path: second_handoff,
                },
                receipts_by_path={},
            )

    def test_validate_implement_contract_rejects_contained_capability_owns(self) -> None:
        second_shard_id = "S02-service-flow-02"
        second_receipt_path = f"{HANDOFF_DIR}/results/{second_shard_id}.json"
        second_handoff_path = f"{HANDOFF_DIR}/{second_shard_id}.json"
        first_handoff = minimal_handoff()
        first_handoff["capability_boundary"]["owns"] = [f"{FEATURE_PATH}/src"]
        second_handoff = minimal_handoff(
            shard_id=second_shard_id,
            task_ids=["T002"],
            allowed_write_paths=[f"{FEATURE_PATH}/tests/test_service.py", second_receipt_path],
        )
        second_handoff["capability_boundary"]["owns"] = [SERVICE_PATH]
        manifest = minimal_manifest(
            shards=[
                minimal_shard(),
                minimal_shard(shard_id=second_shard_id, task_ids=["T002"]),
            ],
            dispatch_order=[[SHARD_ID, second_shard_id]],
        )

        with self.assertRaisesRegex(ValueError, "capability_boundary.owns"):
            validate_implement_contract(
                manifest,
                handoffs_by_path={
                    f"{HANDOFF_DIR}/{SHARD_ID}.json": first_handoff,
                    second_handoff_path: second_handoff,
                },
                receipts_by_path={},
            )

    def test_handoff_schema_accepts_minimal_valid_handoff(self) -> None:
        schema = json.loads(HANDOFF_SCHEMA_PATH.read_text(encoding="utf-8"))
        Draft202012Validator(schema).validate(minimal_handoff())

    def test_handoff_schema_allows_context_gaps_for_blocked_handoff(self) -> None:
        schema = json.loads(HANDOFF_SCHEMA_PATH.read_text(encoding="utf-8"))
        handoff = minimal_handoff()
        handoff["context_gaps"] = ["Missing API contract context"]
        Draft202012Validator(schema).validate(handoff)

    def test_validate_handoff_contract_rejects_tasks_md_in_allowed_write_paths(self) -> None:
        handoff = minimal_handoff(allowed_write_paths=[SERVICE_PATH, TASKS_PATH, RECEIPT_PATH])
        with self.assertRaises(ValueError):
            validate_handoff_contract(handoff)

    def test_validate_handoff_contract_rejects_context_gaps(self) -> None:
        handoff = minimal_handoff()
        handoff["context_gaps"] = ["Missing API contract context"]
        with self.assertRaisesRegex(ValueError, "context_gaps"):
            validate_handoff_contract(handoff)

    def test_validate_handoff_contract_rejects_duplicate_task_ids(self) -> None:
        handoff = minimal_handoff(task_ids=["T001", "T001"])
        with self.assertRaisesRegex(ValueError, "task_ids"):
            validate_handoff_contract(handoff)

    def test_validate_handoff_contract_rejects_allowed_write_path_in_must_not_touch(self) -> None:
        handoff = minimal_handoff()
        handoff["capability_boundary"]["must_not_touch"] = [SERVICE_PATH]
        with self.assertRaisesRegex(ValueError, "must_not_touch"):
            validate_handoff_contract(handoff)

    def test_validate_handoff_contract_rejects_allowed_write_path_contained_in_must_not_touch(
        self,
    ) -> None:
        handoff = minimal_handoff()
        handoff["capability_boundary"]["must_not_touch"] = [f"{FEATURE_PATH}/src"]
        with self.assertRaisesRegex(ValueError, "must_not_touch"):
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

    def test_validate_receipt_contract_rejects_generic_behavior_evidence(self) -> None:
        handoff = minimal_handoff()
        handoff["allowed_read_paths"] = [
            TASKS_PATH,
            f"{FEATURE_PATH}/contracts/bdd/refund.feature",
            f"{FEATURE_PATH}/contracts/behavior/scenario-instances.json",
            f"{FEATURE_PATH}/contracts/api/refunds.openapi.yaml",
            f"{FEATURE_PATH}/quickstart.md",
        ]
        handoff["task_text"] = [
            "Implement SCN-001 and AST-001 from contracts/api/refunds.openapi.yaml"
        ]

        with self.assertRaisesRegex(ValueError, "validation_evidence"):
            validate_receipt_contract(
                handoff,
                minimal_receipt(validation_evidence=["unit tests passed"]),
                RECEIPT_PATH,
            )

    def test_validate_receipt_contract_accepts_behavior_evidence_references(self) -> None:
        handoff = minimal_handoff()
        handoff["allowed_read_paths"] = [
            TASKS_PATH,
            f"{FEATURE_PATH}/contracts/bdd/refund.feature",
            f"{FEATURE_PATH}/contracts/behavior/scenario-instances.json",
            f"{FEATURE_PATH}/contracts/api/refunds.openapi.yaml",
            f"{FEATURE_PATH}/quickstart.md",
        ]
        handoff["task_text"] = [
            "Implement SCN-001 and AST-001 from contracts/api/refunds.openapi.yaml"
        ]

        validate_receipt_contract(
            handoff,
            minimal_receipt(
                validation_evidence=[
                    "SCN-001 covered; AST-001 verified against contracts/api/refunds.openapi.yaml and quickstart.md"
                ]
            ),
            RECEIPT_PATH,
        )

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

    def test_handoff_schema_rejects_empty_task_ids(self) -> None:
        schema = json.loads(HANDOFF_SCHEMA_PATH.read_text(encoding="utf-8"))
        handoff = minimal_handoff(task_ids=[])
        with self.assertRaises(ValidationError):
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
        self.assertIn("/speckit.analyze", readme)
        self.assertIn("/speckit.implement", readme)
        self.assertIn("class-diagram.md", readme)
        self.assertIn("contracts/sequences.md", readme)
        self.assertNotIn("test-plan.md", readme)
        self.assertIn("test strategy derivation", readme)
        self.assertIn("validation decisions in `research.md`", readme)
        self.assertIn("validation paths in `quickstart.md`", readme)
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
        self.assertIn("must formalize", readme)
        self.assertIn("N/A or blocker", readme)
        self.assertIn("The preset has four goals:", readme)
        self.assertIn("BDD readiness gate", readme)
        self.assertIn("Phase 0 behavior projection", readme)
        self.assertIn("validation_evidence", readme)
        self.assertIn("Context-load controls", readme)
        self.assertIn("context-load controls", changelog)
        self.assertIn("Change Scope Granularity", changelog)
        self.assertIn("/speckit.constitution", changelog)
        self.assertIn("Moved behavior draft generation from `/speckit.specify` to `/speckit.plan` Phase 0", changelog)
        self.assertIn("BDD readiness gate", changelog)
        self.assertIn("Removed `behavior/open-questions.json`", changelog)
        self.assertIn("Hardened behavior contract quality gates", changelog)
        self.assertIn("formalization blockers", changelog)
        self.assertIn("behavior-linked validation evidence", changelog)
        self.assertNotIn("run-orchestrated-implement.py", readme)
        self.assertNotIn("speckit-implement-handoff.py", readme)
        self.assertNotIn("--dry-run true --run-id manual", readme)
        self.assertIn("Spec Kit CLI `>=0.8.10.dev0`", readme)
        self.assertIn("python3 -m pip install -r requirements-dev.txt", readme)
        self.assertIn("Preset CI Boundary", readme)
        self.assertIn("SPEC_KIT_FORK_DISPATCH_TOKEN", readme)
        self.assertIn("bigsmartben/spec-kit", readme)
        self.assertIn("workflow-preset-release", readme)
        self.assertIn("does not open pull requests to `github/spec-kit`", readme)
        self.assertIn("PyYAML", requirements)
        self.assertIn("jsonschema", requirements)
        self.assertIn("## 1.2.0", changelog)
        self.assertIn("## 1.1.0", changelog)
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
            "Runtime Isolation Mapping",
            "Isolated execution",
            "codex",
            "claude",
            "gemini",
            "opencode",
            "generic",
            "isolated subagent/subsession",
            "manual fresh Worker-mode sessions",
            "Dispatch Payloads",
            "Worker payload",
            "no full `spec.md`, `plan.md`, `research.md`, `contracts/`, `quickstart.md`",
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
            "validation_evidence references to relevant BDD scenario",
            "behavior assertion",
            "API contract",
            "quickstart path",
            "receipt 路径不等于 handoff 中声明的 `task_status_update.receipt_path`",
        ]
        for term in required_terms:
            self.assertIn(term, document)

        self.assertIn("research.md validation decisions", document)
        self.assertIn("quickstart.md validation paths", document)
        self.assertNotIn("test-plan.md", document)

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

    def test_extension_governance_document_contract(self) -> None:
        self.assertTrue(EXTENSION_GOVERNANCE_PATH.exists())
        document = EXTENSION_GOVERNANCE_PATH.read_text(encoding="utf-8")

        self.assertLessEqual(len(document.splitlines()), 140)
        required_terms = [
            "Preset Extension Governance",
            "templates own stable artifact shapes",
            "commands own stage-local generation instructions",
            "structured JSON artifacts require schemas",
            "validators/",
            "Do not put downstream prohibitions in upstream commands",
            "Behavior-first extension rule",
            "BDD and UIF artifacts need independent templates",
            "`/speckit.constitution`: constitution governance and project principles only",
            "`/speckit.checklist`: checklist artifacts and BDD readiness gates only",
            "`/speckit.plan`: Phase 0 behavior projection, planning artifacts, and formal contracts",
            "Handoff extensions must update schema, validator, command, and cross-agent documentation together",
            "Do not bump preset version or release archive URLs until release preparation",
            "Use extensions, not presets, for new tooling",
            "/speckit.analyze",
            "vertical consistency",
            "tests/test_preset_contract.py",
        ]
        for term in required_terms:
            self.assertIn(term, document)

        forbidden_terms = [
            "TBD",
            "TODO",
            "Do not create `contracts/bdd/`",
            "Do not create formal behavior contracts during specification",
        ]
        for term in forbidden_terms:
            self.assertNotIn(term, document)

    def test_agents_references_extension_governance(self) -> None:
        agents = AGENTS_PATH.read_text(encoding="utf-8")

        self.assertIn("docs/extension-governance.md", agents)
        self.assertIn("Extension Governance", agents)

if __name__ == "__main__":
    unittest.main()
