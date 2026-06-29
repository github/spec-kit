from __future__ import annotations

import unittest
import json
import re
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError

from validators.speckit_implement_contract import (
    validate_behavior_case_coverage,
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
CROSS_AGENT_SUBAGENTS_PATH = REPO_ROOT / "tests" / "contracts" / "speckit-cross-agent-subagents.md"
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
CANONICAL_RESPONSIVE_VISUAL_RULE = (
    "Responsive visual requirements block PASS only when they are complex, "
    "multi-state, or declare L2 or L3 visual proof"
)
FORBIDDEN_VISUAL_COMPAT_TERMS = (
    "legacy visual",
    "previous-version",
    "previous version",
    "backward-compatible",
    "backward compatible",
    "fallback visual",
    "fallback visual rule",
    "compatibility mode",
    "历史版本",
    "旧版兼容",
    "兼容旧版",
    "回退视觉规则",
)
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
API_CONTRACT_PATH = f"{FEATURE_PATH}/contracts/api/refunds.openapi.yaml"
SEQUENCES_PATH = f"{FEATURE_PATH}/contracts/sequences.md"
QUICKSTART_PATH = f"{FEATURE_PATH}/quickstart.md"


def no_data_side_effects_review(*, paths: list[str] | None = None) -> dict:
    return {
        "reviewed_diff_paths": paths or [SERVICE_PATH],
        "runtime_data_writes_found": False,
        "mutation_findings": [],
    }


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
    task_type: str = "implementation",
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
        "task_type": task_type,
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
    review_conclusion: dict | None = None,
    data_side_effect_review: dict | None = None,
    consistency_repairs: list[dict] | None = None,
    deferred_validation_todos: list[dict] | None = None,
    task_type: str = "implementation",
) -> dict:
    task_ids = task_ids or ["T001"]
    receipt = {
        "contract_type": "speckit.implement.receipt.v1",
        "shard_id": shard_id,
        "task_type": task_type,
        "task_ids": task_ids,
        "completed_task_ids": task_ids if completed_task_ids is None else completed_task_ids,
        "changed_paths": changed_paths or [SERVICE_PATH],
        "validation_evidence": validation_evidence
        if validation_evidence is not None
        else ["unit tests passed"],
    }
    if review_conclusion is not None:
        receipt["review_conclusion"] = review_conclusion
    if data_side_effect_review is not None:
        receipt["data_side_effect_review"] = data_side_effect_review
    if consistency_repairs is not None:
        receipt["consistency_repairs"] = consistency_repairs
    if deferred_validation_todos is not None:
        receipt["deferred_validation_todos"] = deferred_validation_todos
    return receipt


def minimal_behavior_scenarios_draft(
    *,
    scenario_id: str = "SCN-001",
    scenario_type: str = "positive",
) -> dict:
    return {
        "contract_type": "speckit.behavior.scenarios.draft.v1",
        "feature": "refund-application",
        "scenarios": [
            {
                "id": scenario_id,
                "title": "Submit refund",
                "type": scenario_type,
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


def minimal_exception_behavior_scenario_instances(*, scenario_type: str = "permission") -> dict:
    instances = minimal_behavior_scenario_instances()
    scenario = instances["scenarios"][0]
    scenario["id"] = "SCN-ERR-001"
    scenario["title"] = "Reject refund request"
    scenario["type"] = scenario_type
    scenario["request_case"] = {
        "id": "REQ-ERR-001",
        "case_kind": scenario_type,
        "outcome": "failure",
        "trigger": "submit_refund_without_required_permission",
    }
    scenario["expected_response"] = {
        "business_code": "REJECTED",
        "status": 403,
        "error_code": "ERR_PERMISSION_DENIED",
    }
    scenario["expected_feedback"] = {
        "type": "inline_error",
        "message": "Permission denied",
    }
    scenario["assertion_ids"] = ["AST-001"]
    return instances


def minimal_case_coverage() -> dict:
    return {
        "case_coverage": [
            {
                "story": "Refund request",
                "case_id": "CASE-001",
                "case_type": "permission",
                "status": "Required",
                "source": "spec.md#user-story-1",
                "scenario_id": "SCN-ERR-001",
            }
        ]
    }


def minimal_case_coverage_with_blocker() -> dict:
    return {
        "case_coverage": [
            {
                "story": "Refund request",
                "case_id": "CASE-002",
                "case_type": "validation",
                "status": "Required",
                "source": "spec.md#user-story-1",
                "blocker_id": "BLK-001",
            }
        ]
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


def minimal_exception_behavior_assertions() -> dict:
    return minimal_exception_behavior_assertions_with_intent("state_invariant")


def minimal_exception_behavior_assertions_with_intent(intent: str) -> dict:
    assertions = minimal_behavior_assertions()
    assertions["assertions"][0]["intent"] = intent
    return assertions


class PresetContractTests(unittest.TestCase):
    def test_preset_manifest_contract(self) -> None:
        data = yaml.safe_load(PRESET_PATH.read_text(encoding="utf-8"))

        self.assertEqual("1.0", data["schema_version"])
        self.assertEqual("workflow-preset", data["preset"]["id"])
        self.assertEqual("Workflow Preset", data["preset"]["name"])
        self.assertEqual("1.3.10", data["preset"]["version"])
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
        for migrated_entry in (
            "provider-evidence-packet-template",
            "provider-intake-contract-template",
            "design-requirement" + "-intake-template",
            "requirement-merge" + "-report-template",
            "speckit-design-visual" + "-item-matrix-v1-schema",
        ):
            self.assertNotIn(migrated_entry, entries)

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
            "Wrap core checklist generation with BDD, NFR, and Visual Fidelity readiness gate",
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
            "Wrap core constitution updates with change scope granularity and architecture SSOT governance",
            entries["speckit.constitution"]["description"],
        )
        self.assertEqual(
            "Add change scope granularity and architecture SSOT governance to the constitution template",
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
                template_path.relative_to(REPO_ROOT).as_posix(),
                template["file"],
            )
            self.assertEqual(template_name, template["replaces"])
            self.assertEqual("replace", template["strategy"])

        for contract_type, schema_path in BEHAVIOR_SCHEMA_PATHS.items():
            schema_name = f"{contract_type}-schema".replace(".", "-").replace("_", "-")
            schema = entries[schema_name]
            self.assertEqual("template", schema["type"])
            self.assertEqual(schema_path.relative_to(REPO_ROOT).as_posix(), schema["file"])
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
        self.assertIn("Generate design artifacts only when the feature requires internal object design or cross-boundary sequence constraints", command)
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

    def test_plan_visual_substage_enhancement_contract(self) -> None:
        command = PLAN_COMMAND_PATH.read_text(encoding="utf-8")
        template = PLAN_TEMPLATE_PATH.read_text(encoding="utf-8")
        readme = README_PATH.read_text(encoding="utf-8")
        governance = EXTENSION_GOVERNANCE_PATH.read_text(encoding="utf-8")

        for term in (
            "Visual Planning Responsibilities",
            "Visual validation decisions",
            "Visual Item ID",
            "viewport/state coverage strategy",
            "visual regression or baseline proof strategy",
            "Do not copy the Visual Fidelity Evidence Matrix into `research.md`",
            "do not rebuild provider evidence matrices",
            "visual_item_refs",
            "viewport_matrix_refs",
            "state_matrix_refs",
            "visual_proof_refs",
            "accepted_exception_refs",
            "UI interaction sequence",
            "visual state handoff points",
            "responsive branch trigger refs",
        ):
            self.assertIn(term, command)

        for term in (
            "Visual fidelity navigation",
            "Visual validation decisions: `./research.md`",
            "Visual interaction contracts: `./contracts/uif/` and `./contracts/behavior/`",
            "Visual flow sequences: `./contracts/sequences.md`",
        ):
            self.assertIn(term, template)

        for document in (readme, governance):
            self.assertIn("research.md records visual validation decisions", document)
            self.assertIn("contracts formalize visual interaction and state constraints", document)
            self.assertIn("contracts/sequences.md records visual state flow only when it affects cross-boundary sequencing", document)

        self.assertIn(
            "fixed R/M/U/O model: R is Repository / Workspace, M is Module / Capability, U is Unit / Design Object, and O is Operation / Detail",
            readme,
        )
        self.assertIn(
            "Blocks constitution writes when a generated draft changes the fixed R/M/U/O mapping",
            readme,
        )
        self.assertIn(
            "Routes architecture decisions, domain facts, object design, flows, and interface contracts to architecture SSOT artifacts instead of embedding concrete implementation content in ratified constitution principles",
            readme,
        )

    def test_constitution_change_scope_granularity_contract(self) -> None:
        command = CONSTITUTION_COMMAND_PATH.read_text(encoding="utf-8")
        template = CONSTITUTION_TEMPLATE_PATH.read_text(encoding="utf-8")

        exact_mapping = [
            "R: Repository / Workspace. Environment only; too broad for scoped changes.",
            "M: Module / Capability. Hard outer boundary.",
            "U: Unit / Design Object. Primary planning boundary.",
            "O: Operation / Detail. Execution detail.",
        ]
        forbidden_mapping_drift = [
            "R, Requirement",
            "R: Requirement",
            "M, Model",
            "M: Model",
            "U, User/API Interface",
            "U: User/API Interface",
            "O, Operations",
            "O: Operations",
        ]

        for document in (command, template):
            self.assertIn("{CORE_TEMPLATE}", document)
            self.assertIn("Change Scope Granularity", document)
            self.assertIn("R/M/U/O", document)
            self.assertIn("Planning locks M + U", document)
            for mapping in exact_mapping:
                self.assertIn(mapping, document)
            for forbidden in forbidden_mapping_drift:
                self.assertNotIn(forbidden, document)

        self.assertIn("strategy: wrap", command)
        self.assertIn("Spec Kit planning and execution MUST use R/M/U/O scope granularity", template)
        self.assertIn("This principle applies from planning onward", template)
        self.assertIn("Requirement specification, clarification, and checklist readiness MUST NOT infer M/U/O boundaries", template)
        self.assertIn("preserve the Change Scope Granularity principle", command)
        self.assertIn("must not remove, weaken, or contradict", command)
        self.assertIn("The R/M/U/O letter mapping is fixed and MUST remain exact", command)
        self.assertIn("preserves the exact R/M/U/O letter mapping", command)
        self.assertIn("CONSTITUTION_RMUO_MAPPING_DRIFT", command)
        self.assertIn("CONSTITUTION_TEMPLATE_STATUS_UNCHECKED", command)
        self.assertIn("do not report it as missing", command)
        self.assertIn("do not treat that as the workflow-preset template being absent", command)
        self.assertIn("Architecture SSOT Boundary", command)
        self.assertIn("Architecture SSOT Compliance", command)
        self.assertIn("Ratified constitution principles must be durable governance rules, not architecture fact storage", command)
        self.assertIn(
            "Architecture decisions, domain facts, object design, flows, and interface contracts belong in their architecture SSOT artifacts",
            command,
        )
        self.assertIn("specs/<feature>/data-model.md", command)
        self.assertIn("specs/<feature>/class-diagram.md", command)
        self.assertIn("specs/<feature>/contracts/sequences.md", command)
        self.assertIn("specs/<feature>/contracts/", command)
        self.assertIn("specs/<feature>/research.md", command)
        self.assertIn(
            "MUST NOT capture, discover, extract, migrate, store, validate, or repair architecture facts",
            command,
        )
        self.assertIn("do not embed them in ratified principles", command)
        self.assertIn("name the responsible workflow-preset SSOT artifact type", command)
        self.assertIn("Do not write concrete `specs/<feature>/...` paths", command)
        self.assertIn("check those paths", command)
        self.assertIn("create or update those artifacts", command)
        self.assertIn("CONSTITUTION_ARCH_SSOT_GAP", command)
        self.assertIn("copy concrete implementation facts", command)
        self.assertIn("Planning outputs MUST comply with existing Architecture SSOT artifacts", command)
        self.assertIn("MUST NOT contradict, relocate, weaken, or silently replace architecture SSOT content", command)
        self.assertIn("requires planning outputs to comply with existing Architecture SSOT artifacts", command)
        self.assertIn(
            "routes architecture decisions, domain facts, object design, flows, and interface contracts to workflow-preset SSOT artifact types",
            command,
        )
        self.assertNotIn("unless the current Spec Kit context already provides an existing feature path", command)
        self.assertNotIn("required existing SSOT path is absent", command)
        self.assertIn("The R/M/U/O letter mapping is fixed", template)
        self.assertIn("Architecture SSOT Boundary", template)
        self.assertIn("Architecture SSOT Compliance", template)
        self.assertIn("Ratified constitution principles are durable governance rules, not architecture fact storage", template)
        self.assertIn(
            "Architecture decisions, domain facts, object design, flows, and interface contracts belong in their architecture SSOT artifacts",
            template,
        )
        self.assertIn("specs/<feature>/data-model.md", template)
        self.assertIn("specs/<feature>/class-diagram.md", template)
        self.assertIn("specs/<feature>/contracts/sequences.md", template)
        self.assertIn("specs/<feature>/contracts/", template)
        self.assertIn("specs/<feature>/research.md", template)
        self.assertIn("may reference these SSOT artifact types", template)
        self.assertIn(
            "must not copy concrete implementation facts, temporary repository observations, or module responsibility inventories",
            template,
        )
        self.assertIn("Planning outputs MUST comply with existing Architecture SSOT artifacts", template)
        self.assertIn("Planning MUST NOT contradict, relocate, weaken, or silently replace architecture SSOT content", template)

    def test_change_scope_granularity_stage_references(self) -> None:
        plan = PLAN_COMMAND_PATH.read_text(encoding="utf-8")
        tasks = TASKS_COMMAND_PATH.read_text(encoding="utf-8")
        analyze = ANALYZE_COMMAND_PATH.read_text(encoding="utf-8")
        implement = IMPLEMENT_COMMAND_PATH.read_text(encoding="utf-8")

        self.assertIn("Apply the constitution's Change Scope Granularity principle.", plan)
        self.assertIn("During planning, lock the change scope to `M + U`", plan)
        self.assertIn("Do not lock operation-level implementation details or concrete write paths.", plan)
        self.assertNotIn("Architecture SSOT Compliance", plan)
        self.assertNotIn("PLANNING_ARCH_SSOT_CONFLICT", plan)

        self.assertIn("Preserve the planned `M + U` scope", tasks)
        self.assertIn("Do not generate execution metadata or write-path fields.", tasks)

        self.assertIn("Check that tasks preserve the planned `M + U` scope.", analyze)
        self.assertIn("Report missing, widened, or ambiguous scope boundaries as blockers.", analyze)

        cross_agent = CROSS_AGENT_SUBAGENTS_PATH.read_text(encoding="utf-8")
        self.assertIn("Map planned `U` design objects to concrete source", implement)
        self.assertIn("planned `U` design object", cross_agent)
        self.assertIn("specific source, test, fixture, configuration, or receipt paths", cross_agent)
        self.assertIn("context_gaps", cross_agent)

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
        self.assertIn("`/speckit.tasks` owns implementation, validation, and review task definition in `tasks.md`", tasks)
        self.assertIn("must not invent validation strategy", tasks)
        self.assertIn("change requirements, update contracts, or widen scope", tasks)
        self.assertIn("Planning Input Taxonomy", tasks)
        self.assertIn("validation level taxonomy", tasks)
        self.assertIn("fixture strategy and external-system execution mode taxonomy", tasks)
        self.assertIn("Evidence binding", tasks)
        self.assertIn("Validation Task Derivation", tasks)
        self.assertIn("derive the validation level", tasks)
        self.assertIn("fixture strategy, external-system execution mode", tasks)
        self.assertIn("inline evidence requirement", tasks)
        self.assertIn("validation task taxonomy", tasks)
        for validation_scope in (
            "`contract_validation`",
            "`visual_verification` or `ui_acceptance`",
            "`data_side_effect_validation`",
            "`integration_e2e_validation`",
        ):
            self.assertIn(validation_scope, tasks)
        self.assertIn("Final Code Review", tasks)
        self.assertIn("append the final phase after user-story tasks", tasks)
        self.assertIn("final review scope taxonomy", tasks)
        self.assertIn("`boundary`, `interface_contract`, `visual`, `data_side_effect`, `behavior_contract`, `sequence_consistency`, and `asset_binding`", tasks)
        self.assertIn("Checked sources include", tasks)
        self.assertIn("`contracts/uif/`", tasks)
        self.assertIn("`spec.md` Client Asset Contract entries", tasks)
        self.assertIn("Visual Fidelity Readiness", tasks)
        self.assertIn("data side-effect review", tasks)
        self.assertIn("field-level update/delete", tasks)
        self.assertIn("runtime database writes", tasks)
        self.assertIn("boundary review", tasks)
        self.assertIn("task scope stays within planned `M + U`", tasks)
        self.assertIn("no implementation task changed `spec.md`, `contracts/`, readiness checklists, or Visual Fidelity Readiness", tasks)
        self.assertIn("visual consistency review", tasks)
        self.assertIn("implemented UI states and viewport behavior", tasks)
        self.assertIn("screenshot refs, visual proof refs", tasks)
        self.assertIn("visual task taxonomy", tasks)
        self.assertIn("story-local task granularity", tasks)
        self.assertIn("`visual_setup` -> `visual_validation` -> `visual_implementation` -> `visual_evidence`", tasks)
        self.assertIn("Do not create a separate visual lifecycle phase", tasks)
        self.assertIn("Visual tasks must name concrete source, test, fixture, configuration, or asset paths", tasks)
        self.assertIn("report a readiness blocker instead of generating an ambiguous visual task", tasks)
        self.assertIn("Client Asset Contract bindings, variants, and fallback policy", tasks)
        self.assertIn("real-system e2e environment readiness", tasks)
        self.assertIn("Review evidence binding", tasks)
        self.assertIn("concrete review scope, source artifacts, implementation surfaces, and evidence refs", tasks)
        self.assertIn("bounded repair permission", tasks)
        self.assertIn("review evidence, bounded repair permission, or a blocker", tasks)
        self.assertIn("record a blocker instead of treating the change as implementation work", tasks)
        self.assertNotIn("handoff", tasks)
        self.assertNotIn("allowed_write_paths", tasks)
        self.assertNotIn("receipt", tasks)
        self.assertNotIn("speckit.implement.receipt.v1", tasks)
        self.assertNotIn("task_type: code_review", tasks)
        self.assertNotIn("data_side_effect_review", tasks)
        self.assertNotIn("review_conclusion", tasks)
        self.assertNotIn("checked_sources", tasks)
        self.assertNotIn("consistency_repairs", tasks)
        self.assertNotIn("deferred_validation_todos", tasks)
        self.assertNotIn("empty arrays or objects indicate no entries", tasks)
        self.assertNotIn("task_type: visual_verification", tasks)
        self.assertNotIn("task_type: interface_validation", tasks)
        self.assertNotIn("task_type: data_side_effect_validation", tasks)

    def test_behavior_first_command_wrapper_contracts(self) -> None:
        specify = SPECIFY_COMMAND_PATH.read_text(encoding="utf-8")
        clarify = CLARIFY_COMMAND_PATH.read_text(encoding="utf-8")
        checklist = CHECKLIST_COMMAND_PATH.read_text(encoding="utf-8")

        for command in (specify, clarify, checklist):
            self.assertIn("{CORE_TEMPLATE}", command)
            self.assertIn("strategy: wrap", command)
            self.assertIn(
                "This wrapper must not redefine core-owned User Input, Pre-Execution Checks, extension hooks, base path resolution, or core file handling.",
                command,
            )

        self.assertIn("Spec-Only Requirement Policy", specify)
        self.assertIn("Wrapper Input Additions", specify)
        self.assertIn("Wrapper Preflight Additions", specify)
        self.assertIn("Wrapper Outline Additions", specify)
        self.assertNotIn("## User Input", specify)
        self.assertNotIn("## Pre-Execution Checks", specify)
        self.assertIn("Preset-added requirement output writes only `spec.md`", specify)
        self.assertIn("Product requirements stay in `spec.md`", specify)
        self.assertIn("non-functional requirements", specify)
        self.assertIn("visual and UI requirements", specify)
        self.assertIn("report the `spec.md` sections created or updated", specify)
        for term in (
            "Official Style Alignment",
            "Focus on WHAT users need and WHY",
            "Avoid HOW to implement",
            "Limit [NEEDS CLARIFICATION] markers to the highest-impact unresolved product decisions",
            "Specification Quality Validation",
            "Done When",
        ):
            self.assertIn(term, specify)
        for term in (
            "confirmed external intake facts",
            "visual SSOT refs",
            "evidence refs",
            "does not perform intake",
            "call provider tools",
            "parse HTML bundles",
            "decide provider source readiness",
            "generate provider artifact instances",
            "Specification Projection Policy",
            "source-backed external intake facts",
            "Visual Asset Registry",
            "external source artifact inputs",
            "visual media inventory",
            "license status",
            "Visual & UI Specification",
            "observable visual and UI requirements",
            "write a `Visual & UI Specification` section",
            "Not Applicable rationale",
            "Every identified visual or UI requirement must be recorded",
            "`Required`, `Not Applicable`, `Unknown`, or `[BLOCKED: PROVIDER_EVIDENCE]`",
            "do not silently omit low-evidence visual or UI requirements",
            "source refs",
            "state and viewport refs",
            "Client Asset Contract facts",
            "asset source strategy",
            "required variants",
            "fallback policy",
            "blocker status",
            "Promote only source-backed visual, layout, state, interaction, responsive, accessibility, and acceptance facts",
            "Component State Matrix content as Visual & UI Specification requirements, not visual assets",
            "observable states, visual feedback, and interaction outcomes",
            "Product semantics implied only by provider evidence stay `[NEEDS CLARIFICATION]`",
            "DOM structure",
            "CSS selectors",
            "component props",
            "provider blockers",
            "[BLOCKED: PROVIDER_EVIDENCE]",
            "keep explicit visual or UI requirement coverage in `spec.md`",
            "Functional, non-functional, and visual/UI requirement coverage",
            "must not become product `[NEEDS CLARIFICATION]` items",
            "[NEEDS CLARIFICATION]",
            "visual SSOT refs preserved",
        ):
            self.assertIn(term, specify)
        self.assertLessEqual(len(specify.splitlines()), 70)
        for forbidden in (
            "/speckit.plan",
            "/speckit.checklist",
            "Visual Fidelity Evidence Matrix",
            "`[NEEDS CLARIFICATION]` item requesting a filled Provider Evidence Packet",
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
            "local asset path",
            "asset hash",
            "allowed_write_paths",
            "Design intake input",
            "Provider Evidence Packet readiness",
            "Requirement Merge Report",
            "raw get_metadata",
            "Stage 0:",
            "Stage 1:",
            "Stage 2:",
            "Stage 3:",
            "Observed from provider design",
        ):
            self.assertNotIn(forbidden, specify)
        self.assertNotIn("contracts/bdd/", specify)
        self.assertNotIn("contracts/uif/", specify)

        self.assertIn("Spec-Only Clarification Policy", clarify)
        self.assertIn("Wrapper Input Additions", clarify)
        self.assertIn("Wrapper Preflight Additions", clarify)
        self.assertIn("Wrapper Outline Additions", clarify)
        self.assertNotIn("## User Input", clarify)
        self.assertNotIn("## Pre-Execution Checks", clarify)
        self.assertIn("Use `spec.md` as the clarification source", clarify)
        self.assertIn("Do not read or update behavior draft artifacts", clarify)
        self.assertIn("Product requirements stay in `spec.md`", clarify)
        self.assertIn("non-functional requirement assumptions", clarify)
        self.assertIn("visual/UI requirement coverage status", clarify)
        self.assertIn("only after user-provided answers", clarify)
        self.assertIn("Design Requirement Clarification Strategy", clarify)
        self.assertIn("external intake evidence", clarify)
        self.assertIn("visual SSOT refs", clarify)
        self.assertIn("evidence-derived gaps", clarify)
        self.assertIn("visual/UI coverage status `Unknown`", clarify)
        self.assertIn("[NEEDS CLARIFICATION]", clarify)
        self.assertIn("Do not call provider tools", clarify)
        self.assertIn("Do not re-extract design facts", clarify)
        self.assertIn("re-parse provider design links", clarify)
        self.assertIn("parse HTML SSOT bundles", clarify)
        self.assertIn("External intake owns source capture and provider readiness", clarify)
        self.assertIn("confirmed evidence-backed requirements and trace refs", clarify)
        self.assertIn("Do not ask the user to fix provider extraction artifacts", clarify)
        self.assertIn("Ask at most 5 high-impact questions", clarify)
        self.assertIn("Present EXACTLY ONE question at a time", clarify)
        self.assertIn("Do NOT output them all at once", clarify)
        self.assertIn("Never reveal future queued questions", clarify)
        self.assertIn("Maximum of 5 total questions", clarify)
        self.assertIn("Format recommendations as `**Recommended:** Option [X] - <brief rationale>`", clarify)
        self.assertIn("Keep the rationale short and decision-focused", clarify)
        self.assertNotIn("<reasoning>", clarify)
        self.assertIn("Suggested", clarify)
        self.assertIn("2-5", clarify)
        self.assertIn("<=5 words", clarify)
        self.assertIn("yes", clarify)
        self.assertIn("recommended", clarify)
        self.assertIn("suggested", clarify)
        self.assertIn("Save `spec.md` after each accepted answer", clarify)
        self.assertIn("## Clarifications", clarify)
        self.assertIn("### Session YYYY-MM-DD", clarify)
        self.assertIn("Q:", clarify)
        self.assertIn("A:", clarify)
        self.assertIn("provider-specific clarification document", clarify)
        self.assertIn("Validation after each write", clarify)
        self.assertIn("after EACH write plus final pass", clarify)
        self.assertIn("Total asked", clarify)
        self.assertIn("no contradictory earlier statement remains", clarify)
        self.assertIn("Do not update checklist artifacts", clarify)
        self.assertIn("report checklist impact as unresolved readiness context", clarify)
        self.assertNotIn("FEATURE_DIR/checklists/requirements.md", clarify)
        self.assertNotIn("Only toggle the `[ ]`/`[x]` marker", clarify)
        self.assertIn("hooks.before_clarify", clarify)
        self.assertIn("hooks.after_clarify", clarify)
        self.assertIn("EXECUTE_COMMAND", clarify)
        self.assertIn("Completion Report", clarify)
        self.assertIn("Visual/UI coverage status: Required, Not Applicable, Unknown, or `[BLOCKED: PROVIDER_EVIDENCE]`", clarify)
        self.assertIn("visual fidelity scope", clarify)
        self.assertIn("missing UI states", clarify)
        self.assertIn("responsive behavior", clarify)
        self.assertIn("component reuse constraints", clarify)
        self.assertIn("data semantics", clarify)
        self.assertIn("acceptance evidence", clarify)
        self.assertIn("write confirmed answers back into `spec.md`", clarify)
        self.assertIn("Update affected visual/UI coverage status", clarify)
        self.assertIn("Any answered visual/UI coverage status was updated in `spec.md`", clarify)
        self.assertIn("Do not generate visual restoration checklists", clarify)
        for forbidden in (
            "behavior/bdd.draft.feature",
            "behavior/behavior-scenarios.draft.json",
            "behavior/uif.intent.json",
            "behavior/data-fixtures.intent.json",
            "behavior/open-questions.json",
            "use_provider_tool",
            "get_design_context",
            "fetch provider design URL",
            "read provider design URL",
            "Provider Evidence Packet",
            "Design Requirement" + " Intake",
            "Inferred from Structure",
            "update checklists/behavior-testability.md",
        ):
            self.assertNotIn(forbidden, clarify)

        self.assertIn('Checklist Purpose: "Unit Tests for English"', checklist)
        self.assertIn("NOT for verification/testing", checklist)
        self.assertIn("CORE PRINCIPLE - Test the Requirements, Not the Implementation", checklist)
        self.assertIn("Checklist questions must use requirement-quality forms", checklist)
        self.assertIn("$ARGUMENTS", checklist)
        self.assertIn("dynamic clarifying questions", checklist)
        self.assertIn("no pre-baked catalog", checklist)
        self.assertIn("Q1/Q2/Q3", checklist)
        self.assertIn("Q4/Q5", checklist)
        self.assertIn("create the file when absent", checklist)
        self.assertIn("append or update without deleting existing checklist content", checklist)
        self.assertIn("update mode", checklist)
        self.assertIn("full path", checklist)
        self.assertIn("item count", checklist)
        self.assertIn("focus areas", checklist)
        self.assertIn("depth level", checklist)
        self.assertIn("actor/timing", checklist)
        self.assertIn("must-have items", checklist)
        self.assertIn("BDD Readiness Gate", checklist)
        self.assertIn("checklists/behavior-testability.md", checklist)
        self.assertIn("directly from `spec.md`", checklist)
        self.assertIn("plan-entry quality gate", checklist)
        self.assertIn("Do not proceed to `/speckit.plan`", checklist)
        self.assertIn("Requirement ambiguity returns to `/speckit.clarify` or `/speckit.specify`", checklist)
        self.assertIn("User Story Readiness", checklist)
        self.assertIn("Acceptance Criteria Quality", checklist)
        self.assertIn("Scenario Coverage", checklist)
        self.assertIn("Case Coverage Matrix", checklist)
        self.assertIn("one row per story or capability case type", checklist)
        self.assertIn("case status: Required|Not Applicable|Unknown", checklist)
        self.assertIn("Each row must have a stable Case ID", checklist)
        self.assertIn("Required rows must cite the source `spec.md` section", checklist)
        self.assertIn("Scenario IDs and `case_coverage_blockers` are assigned during `/speckit.plan`", checklist)
        self.assertIn("Not Applicable requires rationale", checklist)
        self.assertIn("Unknown must appear in Blocking Items", checklist)
        self.assertIn("Required case type without observable acceptance behavior blocks PASS", checklist)
        self.assertIn("Given Readiness", checklist)
        self.assertIn("When Readiness", checklist)
        self.assertIn("Then Readiness", checklist)
        self.assertIn("Non-Functional Requirement Readiness", checklist)
        self.assertIn("Required", checklist)
        self.assertIn("Not Applicable", checklist)
        self.assertIn("Unknown", checklist)
        self.assertIn("performance, security and privacy, reliability and recovery", checklist)
        self.assertIn("accessibility, compliance and auditability, observability", checklist)
        self.assertIn("compatibility, data lifecycle, and cost or operational constraints", checklist)
        self.assertIn("explicitly declared in `spec.md`", checklist)
        self.assertIn("verifiable product-level criteria", checklist)
        self.assertIn("Do not require technical designs", checklist)
        self.assertIn("Required but missing", checklist)
        self.assertIn("Required but not verifiable", checklist)
        self.assertIn("Unknown and affects downstream design", checklist)
        for term in (
            "Visual Fidelity Readiness",
            "Visual & UI Specification",
            "Check Visual/UI Coverage from `spec.md`",
            "Every identified visual/UI requirement must use status",
            "`Required`, `Not Applicable`, `Unknown`, or `[BLOCKED: PROVIDER_EVIDENCE]`",
            "requirement status",
            "Unknown visual/UI coverage status must appear in Blocking Items",
            "Required visual/UI requirements without observable requirement text block PASS",
            "`[BLOCKED: PROVIDER_EVIDENCE]` items remain provider evidence blockers",
            "visual SSOT refs",
            "external intake refs",
            "provider evidence blockers",
            "product-side visual requirements such as pixel-perfect, brand-critical, responsive visual, or UI visual acceptance requirements",
            "Visual Fidelity Evidence Matrix",
            "Use the behavior-testability checklist template as the visual gate authority",
            "external intake readiness status when cited",
            "visual SSOT refs, evidence refs",
            "source traceability",
            "Screenshot evidence level",
            "BDD, NFR, and Visual Fidelity readiness gate",
            "declared visual proof required",
            "Gate Status: BLOCKED",
            "state, responsive, accessibility, component mapping, and accepted exception",
            "Responsive visual requirements block PASS only when they are complex, multi-state, or declare L2 or L3 visual proof",
            "Use one Visual Fidelity Evidence Matrix as the single visual readiness record",
            "Do not add historical visual rules or alternate visual decision paths",
        ):
            self.assertIn(term, checklist)
        for term in (
            "| Visual Item ID | Source `spec.md` section | Requirement Status | Fidelity Scope | Screenshot Level | Evidence Refs | Visual Proof Required | Blocking Item ID | Exception Rule |",
            "raw metadata completeness",
            "metadata index completeness proof",
            "node inventory parity",
            "blocker lint errors",
            "Responsive visual readiness must record viewport-specific evidence or set Gate Status: BLOCKED",
        ):
            self.assertNotIn(term, checklist)
        self.assertIn("Gate Status", checklist)
        self.assertIn("PASS", checklist)
        self.assertIn("BLOCKED", checklist)
        self.assertIn("Blocking Items", checklist)
        self.assertIn("checklist artifacts only", checklist)
        self.assertIn("BDD, NFR, and Visual Fidelity readiness status", checklist)
        self.assertIn(
            "Provider evidence readiness blockers return to the external intake extension, not `/speckit.clarify`",
            checklist,
        )

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
            "Required case types from `checklists/behavior-testability.md`",
            "must project into `behavior/behavior-scenarios.draft.json`",
            "must formalize into `contracts/behavior/scenario-instances.json`",
            "Do not continue with only positive scenarios when Required case types exist",
            "Map each Required Case ID to a Scenario ID or `case_coverage_blockers` entry",
            "write `case_coverage_blockers`",
            "record `N/A or blocker` with the Case ID",
        ):
            self.assertIn(term, plan)

        for term in (
            "Phase 0 Preflight",
            "Phase 0 Behavior Projection",
            "checklists/behavior-testability.md has passed",
            "Blocking Items: none` or a `Blocking Items` section containing only `- none`",
            "before core research or design work",
            "visual fidelity scope",
            "screenshot refs",
            "visual proof refs",
            "external visual SSOT refs",
            "Visual Fidelity Evidence Matrix `Requirement Status`",
            "Carry forward only visual rows with status `Required` or an accepted exception rule",
            "Rows with status `Unknown` or `[BLOCKED: PROVIDER_EVIDENCE]` must already have blocked checklist PASS",
            "report-only/no-write upstream gate failure",
            "Do not project `Not Applicable` rows into visual planning outputs",
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
            "`spec.md` visual acceptance requirements",
            "`checklists/behavior-testability.md` Visual Fidelity Readiness",
            "screenshot refs",
            "visual proof refs",
            "visual SSOT refs",
            "external evidence refs",
            "visual fidelity requirements",
            "test-first",
            "existing checklist format and user-story organization",
            "For each BehaviorScenarioInstance",
            "fixture task",
            "BDD/E2E or contract test task",
            "implementation task",
            "verification evidence task",
            "Expected UIF contract step with type `user_event`",
            "Expected UIF contract step with type `api_call`",
            "visual task taxonomy",
            "`visual_verification` or `ui_acceptance`",
            "UI acceptance task",
            "state coverage",
            "viewport coverage",
            "visual proof ref",
            "For each quickstart validation path",
            "derive the validation level",
            "fixture strategy, external-system execution mode",
            "inline evidence requirement",
            "Planning Input Taxonomy",
            "`/speckit.tasks` owns implementation, validation, and review task definition in `tasks.md`",
            "must not invent validation strategy",
            "validation level taxonomy",
            "fixture strategy and external-system execution mode taxonomy",
            "Evidence binding",
            "validation task taxonomy",
            "`contract_validation`",
            "`visual_verification` or `ui_acceptance`",
            "`data_side_effect_validation`",
            "`integration_e2e_validation`",
            "Client Asset Contract",
            "derive asset preparation, binding, implementation, and validation tasks",
            "Missing required client visual assets are readiness blockers",
            "Use Visual Fidelity Readiness as the only visual planning readiness source",
            "`Requirement Status` as the visual task input filter",
            "Generate visual tasks only for rows with status `Required` or `Required` plus an accepted exception",
            "tasks for accepted exceptions must cite the exception rule",
            "Do not generate implementation, validation, verification, evidence, asset binding, UI acceptance, or review tasks for `Not Applicable`, `Unknown`, or `[BLOCKED: PROVIDER_EVIDENCE]` rows",
            "Route `Unknown` rows back to `/speckit.clarify`",
            "route `[BLOCKED: PROVIDER_EVIDENCE]` rows to the external intake extension",
            "`/speckit.tasks` must not discover visual requirements or repair evidence",
            "only decomposes visual specifications that already passed the readiness gate",
            "Do not create a second readiness rule",
            "HTML SSOT bundles",
            "external intake artifacts",
            "Do not generate execution metadata or write-path fields.",
            "Missing Required case coverage is a coverage blocker, not silently skipped work",
            "`negative`, `boundary`, `permission`, `validation`, or `state_conflict`",
            "For each BehaviorScenarioInstance with type",
            "derive fixture, contract or BDD test, implementation, and verification evidence tasks",
            "visual consistency review",
            "implemented UI states and viewport behavior",
            "visual task taxonomy",
            "story-local task granularity",
            "`visual_setup` -> `visual_validation` -> `visual_implementation` -> `visual_evidence`",
            "`visual_setup` -> `visual_validation` -> `visual_implementation` -> `visual_evidence` -> `final_visual_review`",
            "`asset_binding`",
            "`final_visual_review`",
            "`visual_setup`, `visual_validation`, `visual_implementation`, `visual_evidence`, `ui_acceptance`, `visual_verification`, `asset_binding`, and `final_visual_review` are the only visual task types",
            "visual regression tests",
            "screenshot comparison",
            "accessibility check entrypoints",
            "empty/error/loading/disabled/hover/focus states",
            "license or authorization refs",
            "Do not create a separate visual lifecycle phase",
            "Visual tasks must name concrete source, test, fixture, configuration, or asset paths",
            "report a readiness blocker instead of generating an ambiguous visual task",
            "Do not generate visual tasks for rows with `Requirement Status` `Not Applicable`, `Unknown`, or `[BLOCKED: PROVIDER_EVIDENCE]`",
            "Client Asset Contract bindings, variants, and fallback policy",
            "Review evidence binding",
            "bounded repair permission",
            "final review scope taxonomy",
            "`boundary`, `interface_contract`, `visual`, `data_side_effect`, `behavior_contract`, `sequence_consistency`, and `asset_binding`",
            "boundary review",
            "no implementation task changed `spec.md`, `contracts/`, readiness checklists, or Visual Fidelity Readiness",
        ):
            self.assertIn(term, tasks)

        self.assertNotIn("task_type: visual_verification", tasks)
        self.assertNotIn("task_type: interface_validation", tasks)
        self.assertNotIn("task_type: data_side_effect_validation", tasks)
        self.assertNotIn("test-plan.md", tasks)

        self.assertIn("./behavior/bdd.draft.feature", template)
        self.assertIn("./contracts/bdd/", template)
        self.assertIn("./contracts/uif/", template)
        self.assertIn("./contracts/behavior/", template)

        cross_agent = CROSS_AGENT_SUBAGENTS_PATH.read_text(encoding="utf-8")
        self.assertIn("tests/contracts/speckit-cross-agent-subagents.md", implement)
        self.assertIn("contracts/bdd/", cross_agent)
        self.assertIn("contracts/uif/", cross_agent)
        self.assertIn("contracts/behavior/", cross_agent)
        self.assertIn("behavior contract constraints", cross_agent)
        self.assertIn("validation_evidence references", cross_agent)
        self.assertIn("BDD scenario", cross_agent)
        self.assertIn("behavior assertion", cross_agent)
        self.assertIn("API contract", cross_agent)
        self.assertIn("quickstart path", cross_agent)
        self.assertIn("visual fidelity requirements", cross_agent)
        self.assertIn("screenshot refs", cross_agent)
        self.assertIn("visual proof refs", cross_agent)
        self.assertIn("visual SSOT refs", cross_agent)
        self.assertIn("Client Asset Contract", cross_agent)
        self.assertIn("asset binding", cross_agent)
        self.assertIn("local asset paths or code asset mappings", cross_agent)
        self.assertIn("missing required client visual assets", cross_agent)
        self.assertIn("Visual Item ID", cross_agent)
        self.assertIn("Requirement Status", cross_agent)
        self.assertIn("visual shard candidates must come only from `tasks.md` visual task types", cross_agent)
        self.assertIn("only `Required` or `Required` plus an accepted exception is executable", cross_agent)
        self.assertIn("do not create visual shards for `Not Applicable`, `Unknown`, or `[BLOCKED: PROVIDER_EVIDENCE]`", cross_agent)
        self.assertIn("route `Unknown` back to `/speckit.clarify`", cross_agent)
        self.assertIn("`[BLOCKED: PROVIDER_EVIDENCE]` to the external intake extension", cross_agent)
        self.assertIn("missing visual proof refs", cross_agent)
        self.assertIn("missing screenshot refs", cross_agent)
        self.assertIn("final_visual_review tasks", cross_agent)
        self.assertIn("must not discover visual requirements, repair Visual Fidelity Readiness evidence", cross_agent)
        self.assertIn("planned `U` design object", cross_agent)
        self.assertIn("specific source, test, fixture, configuration, or receipt paths", cross_agent)

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
        self.assertIn("case coverage", analyze)
        self.assertIn("Required case types in `checklists/behavior-testability.md`", analyze)
        self.assertIn("case types are either covered or have `N/A or blocker` evidence", analyze)
        self.assertIn(
            "failure scenarios declare error code, failure feedback, and state invariant, rollback, or compensation assertion",
            analyze,
        )
        self.assertIn("quickstart validation paths cover Required failure scenarios", analyze)
        self.assertIn("Build a one-pass artifact inventory before deep reading", analyze)
        self.assertIn("Use stable IDs as the primary consistency surface", analyze)
        self.assertIn("CASE-", analyze)
        self.assertIn("SCN-", analyze)
        self.assertIn("UIF-", analyze)
        self.assertIn("FIX-", analyze)
        self.assertIn("AST-", analyze)
        self.assertIn("BLK-", analyze)
        self.assertIn("Read surrounding prose only when a required ID, source section, or blocker explanation is missing or ambiguous", analyze)
        self.assertIn("Stop expanding a branch after the first blocker that proves the downstream link cannot be closed", analyze)
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
        self.assertIn("Case Coverage Matrix", behavior_checklist_template)
        self.assertIn("one row per story or capability case type", behavior_checklist_template)
        self.assertIn("Status: Required|Not Applicable|Unknown", behavior_checklist_template)
        self.assertIn("| Case ID | Story/Capability | Case Type | Status | Source `spec.md` section | Blocking Item ID | Rationale |", behavior_checklist_template)
        self.assertIn(
            "Required case type must cite the source `spec.md` section",
            behavior_checklist_template,
        )
        self.assertIn(
            "Each row must have a stable Case ID",
            behavior_checklist_template,
        )
        self.assertIn(
            "Scenario IDs and `case_coverage_blockers` are assigned during `/speckit.plan`",
            behavior_checklist_template,
        )
        self.assertIn("Not Applicable requires rationale", behavior_checklist_template)
        self.assertIn("Unknown must appear in Blocking Items", behavior_checklist_template)
        self.assertIn("Non-Functional Requirement Readiness", behavior_checklist_template)
        self.assertIn("Status: Required|Not Applicable|Unknown", behavior_checklist_template)
        self.assertIn("Performance", behavior_checklist_template)
        self.assertIn("Security and Privacy", behavior_checklist_template)
        self.assertIn("Reliability and Recovery", behavior_checklist_template)
        self.assertIn("Accessibility", behavior_checklist_template)
        self.assertIn("Compliance and Auditability", behavior_checklist_template)
        self.assertIn("Observability", behavior_checklist_template)
        self.assertIn("Compatibility", behavior_checklist_template)
        self.assertIn("Data Lifecycle", behavior_checklist_template)
        self.assertIn("Cost and Operational Constraints", behavior_checklist_template)
        self.assertIn("explicitly declared in `spec.md`", behavior_checklist_template)
        self.assertIn("without prescribing architecture", behavior_checklist_template)
        self.assertIn("Visual Fidelity Readiness", behavior_checklist_template)
        self.assertIn("Visual & UI Specification", behavior_checklist_template)
        self.assertIn("Every identified visual/UI requirement uses status", behavior_checklist_template)
        self.assertIn("Unknown visual/UI coverage status appears in Blocking Items", behavior_checklist_template)
        self.assertIn("Required visual/UI requirements have observable requirement text", behavior_checklist_template)
        self.assertIn("Design-derived requirements", behavior_checklist_template)
        self.assertIn(
            "external intake readiness status when cited, evidence refs, visual SSOT refs, and blockers",
            behavior_checklist_template,
        )
        self.assertNotIn("raw metadata completeness", behavior_checklist_template)
        self.assertNotIn("metadata index completeness proof", behavior_checklist_template)
        self.assertNotIn("node inventory parity", behavior_checklist_template)
        self.assertNotIn("blocker lint errors", behavior_checklist_template)
        self.assertIn("component mappings and variant coverage", behavior_checklist_template)
        self.assertIn("responsive behavior is explicit", behavior_checklist_template)
        self.assertIn("accessibility requirements are explicit", behavior_checklist_template)
        self.assertIn("Requirement Status", behavior_checklist_template)
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

        scenario_instances_template = BEHAVIOR_TEMPLATE_PATHS[
            "behavior-scenario-instances-template"
        ].read_text(encoding="utf-8")
        self.assertIn('"case_coverage_blockers"', scenario_instances_template)
        self.assertIn('"type": "permission"', scenario_instances_template)
        self.assertIn('"case_kind": "permission"', scenario_instances_template)
        self.assertIn('"error_code"', scenario_instances_template)
        self.assertIn('"expected_feedback"', scenario_instances_template)

        assertions_template = BEHAVIOR_TEMPLATE_PATHS["behavior-assertions-template"].read_text(
            encoding="utf-8"
        )
        self.assertIn('"intent": "state_invariant"', assertions_template)

    def test_visual_fidelity_screenshot_evidence_gate_contract(self) -> None:
        command = CHECKLIST_COMMAND_PATH.read_text(encoding="utf-8")
        template = BEHAVIOR_TEMPLATE_PATHS[
            "behavior-testability-checklist-template"
        ].read_text(encoding="utf-8")

        for term in (
            "Use the behavior-testability checklist template as the visual gate authority",
            "external intake readiness status when cited",
            "Visual Fidelity Evidence Matrix alone decides visual planning readiness",
            "proof level sufficiency",
            "screenshot sufficiency",
            "accepted exception rules",
            "Read visual facts from `spec.md` and evidence refs",
            "do not call provider tools",
            "re-extract external intake evidence",
            "parse HTML SSOT bundles",
            "rebuild provider matrices",
            "another visual readiness path",
            CANONICAL_RESPONSIVE_VISUAL_RULE,
            "Use one Visual Fidelity Evidence Matrix as the single visual readiness record",
            "Do not add historical visual rules or alternate visual decision paths",
            "Blocking Items",
        ):
            self.assertIn(term, command)
        for term in (
            "| Visual Item ID | Source `spec.md` section | Requirement Status | Fidelity Scope | Screenshot Level | Evidence Refs | Visual Proof Required | Blocking Item ID | Exception Rule |",
            "raw metadata completeness",
            "metadata index completeness proof",
            "node inventory parity",
            "blocker lint errors",
            "Responsive visual readiness must record viewport-specific evidence or set Gate Status: BLOCKED",
        ):
            self.assertNotIn(term, command)

        for term in (
            "Screenshot evidence level",
            "visual proof refs",
            "L0|L1|L2|L3",
            "declared visual proof required",
            "only artifact that decides visual planning readiness",
            "proof level sufficiency",
            "screenshot sufficiency",
            "accepted exception rules",
            "does not call provider tools",
            "re-extract external intake evidence",
            "parse HTML SSOT bundles",
            "rebuild provider matrices",
            "another visual readiness path",
            "Missing screenshot evidence sets Gate Status: BLOCKED",
            "High-fidelity requirements without L3 screenshot evidence set Gate Status: BLOCKED",
            "Pixel-perfect requirements without L3 screenshot evidence set Gate Status: BLOCKED",
            CANONICAL_RESPONSIVE_VISUAL_RULE,
            "Visual Fidelity Evidence Matrix",
            "Source `spec.md` section",
            "Requirement Status",
            "Requirement Status is declared for each visual requirement or visual proof obligation",
            "Evidence Refs",
            "Exception Rule",
            "lists the item in Blocking Items",
            "Pixel-perfect",
            "Blocking Items",
            "external intake readiness status when cited",
            "Use one Visual Fidelity Evidence Matrix as the single visual readiness record",
            "Do not add historical visual rules or alternate visual decision paths",
        ):
            self.assertIn(term, template)
        self.assertIn(
            "Required client visual assets have source refs, asset source strategy, required variants, fallback policy, and blocker status.",
            template,
        )
        self.assertEqual(
            len(
                re.findall(
                    r"^## Visual Fidelity Evidence Matrix$",
                    template,
                    flags=re.MULTILINE,
                )
            ),
            1,
        )
        self.assertEqual(
            template.count(
                "| Visual Item ID | Source `spec.md` section | Requirement Status | Fidelity Scope | Screenshot Level | Evidence Refs | Visual Proof Required | Blocking Item ID | Exception Rule |"
            ),
            1,
        )
        self.assertEqual(
            template.count(
                "Use one Visual Fidelity Evidence Matrix as the single visual readiness record"
            ),
            1,
        )
        self.assertEqual(template.count(CANONICAL_RESPONSIVE_VISUAL_RULE), 1)
        for forbidden in (
            "Responsive visual readiness must record viewport-specific evidence or set Gate Status: BLOCKED",
            "Responsive visual readiness records viewport-specific evidence or sets Gate Status: BLOCKED",
            "Screenshot Coverage Matrix",
            "Visual Proof Matrix",
            "Visual Restoration Checklist",
        ):
            self.assertNotIn(forbidden, template)

        for document in (command, template):
            lowered = document.lower()
            for forbidden in FORBIDDEN_VISUAL_COMPAT_TERMS:
                self.assertNotIn(forbidden, lowered)

    def test_implement_command_is_agent_native_handoff_orchestrator(self) -> None:
        command = IMPLEMENT_COMMAND_PATH.read_text(encoding="utf-8")
        cross_agent = CROSS_AGENT_SUBAGENTS_PATH.read_text(encoding="utf-8")

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

        command_terms = [
            "Core mode",
            "Worker mode",
            "Core Agent",
            "Vertical Planner Agent",
            "Worker Agent",
            "vertical_capability",
            "speckit.implement.handoff.v2",
            "speckit.implement.receipt.v1",
            "handoff-manifest.json",
            "speckit.implement.manifest.v1.schema.json",
            "speckit.implement.handoff.v2.schema.json",
            "speckit.implement.receipt.v1.schema.json",
            "validators/speckit_implement_contract.py",
            "tests/contracts/speckit-cross-agent-subagents.md",
            "Use handoff JSON <path>",
            "allowed_read_paths",
            "allowed_write_paths",
            "context_gaps",
            "task_status_update",
            "Do not edit `tasks.md`",
            "Visual Implementation Boundary",
            "visual task input filter",
            "Visual Fidelity Readiness `Requirement Status` is `Required` or `Required` plus an accepted exception",
            "Do not create handoffs or worker instructions for visual rows",
            "`Unknown`, or `[BLOCKED: PROVIDER_EVIDENCE]`",
            "Route `Unknown` visual rows back to `/speckit.clarify`",
            "route `[BLOCKED: PROVIDER_EVIDENCE]` visual rows to the external intake extension",
            "`/speckit.implement` must not discover visual requirements, repair Visual Fidelity Readiness evidence",
            "Visual worker receipts must reference the relevant Visual Item ID",
        ]
        for term in command_terms:
            self.assertIn(term, command)

        contract_terms = [
            "planner_outputs",
            "draft_source",
            "context-index.json",
            ".context.md",
            "handoffs/implement/<run-id>",
            "results/<shard>.json",
            "exactly one handoff",
            "intake",
            "context_indexing",
            "vertical_planning",
            "manifest_assembly",
            "worker_dispatch",
            "worker_execution",
            "receipt_review",
            "code_review",
            "task_commit",
            "integration_verification",
            "closeout",
        ]
        for term in contract_terms:
            self.assertIn(term, cross_agent)

    def test_implement_command_declares_deterministic_handoff_rules(self) -> None:
        command = IMPLEMENT_COMMAND_PATH.read_text(encoding="utf-8")
        cross_agent = CROSS_AGENT_SUBAGENTS_PATH.read_text(encoding="utf-8")

        command_terms = [
            "agent-runtime=<spec-kit-integration-key>",
            "isolated_subagent",
            "manual_fresh_worker_session",
            "isolated subagent/subsession",
            "write the manifest and handoffs, then stop with Worker-mode instructions",
            "Consume planner outputs and worker receipts, not worker conversation history",
            "Reject non-existent handoff paths",
            "Reject handoffs not listed in `handoff-manifest.json`",
        ]
        for term in command_terms:
            self.assertIn(term, command)

        contract_terms = [
            "Runtime Isolation Mapping",
            "Worker payload",
            "no full `spec.md`, `plan.md`, `research.md`, `contracts/`, `quickstart.md`",
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
            "Reject non-existent handoff paths",
            "Reject handoffs not listed in `handoff-manifest.json`",
        ]
        for term in contract_terms:
            self.assertIn(term, cross_agent)

        self.assertIn("research.md validation decisions", cross_agent)
        self.assertIn("quickstart.md validation paths", cross_agent)
        self.assertIn("Code Review Receipts", cross_agent)
        self.assertIn("task_type: code_review", cross_agent)
        self.assertIn("review_conclusion", cross_agent)
        self.assertIn("checked_sources", cross_agent)
        self.assertIn("data_side_effect_review", cross_agent)
        self.assertIn("data side effects", cross_agent)
        self.assertIn("field-level update/delete", cross_agent)
        self.assertIn("runtime database writes", cross_agent)
        self.assertIn("actual implementation diff", cross_agent)
        self.assertIn("consistency_repairs", cross_agent)
        self.assertIn("deferred_validation_todos", cross_agent)
        self.assertIn("quickstart/contract validation command", cross_agent)
        self.assertIn("repair implementation drift against existing design, sequence, or contract constraints", cross_agent)
        self.assertIn("real e2e gaps become todos", cross_agent)
        self.assertNotIn("## Shard Rules", command)
        self.assertNotIn("## Context Digest Rules", command)
        self.assertNotIn("## Path Rules", command)
        self.assertNotIn("## Code Review Receipts", command)
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
        self.assertIn("task_type", handoff["required"])
        self.assertIn("allowed_read_paths", handoff["required"])
        self.assertIn("allowed_write_paths", handoff["required"])
        self.assertIn("task_status_update", handoff["required"])

        agent_topology = handoff["properties"]["agent_topology"]
        self.assertIn("vertical_planner_agent", agent_topology["required"])
        self.assertIn(
            "may_execute_implementation",
            agent_topology["properties"]["vertical_planner_agent"]["required"],
        )

        receipt = json.loads(RECEIPT_SCHEMA_PATH.read_text(encoding="utf-8"))
        self.assertIn("task_type", receipt["required"])
        review_conclusion = receipt["properties"]["review_conclusion"]
        self.assertIn("checked_sources", review_conclusion["required"])
        data_side_effect_review = receipt["properties"]["data_side_effect_review"]
        self.assertIn("reviewed_diff_paths", data_side_effect_review["required"])
        self.assertIn("mutation_findings", data_side_effect_review["required"])
        self.assertIn("pattern", handoff["properties"]["shard_id"])
        self.assertIn("pattern", receipt["properties"]["shard_id"])

        manifest = json.loads(MANIFEST_SCHEMA_PATH.read_text(encoding="utf-8"))
        manifest_shard = manifest["properties"]["shards"]["items"]["properties"]["shard_id"]
        self.assertIn("pattern", manifest_shard)

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

    def test_behavior_scenario_instances_schema_accepts_structured_exception_cases(self) -> None:
        schema = json.loads(
            BEHAVIOR_SCHEMA_PATHS["speckit.behavior.scenario_instances.v1"].read_text(
                encoding="utf-8"
            )
        )

        for scenario_type in ("negative", "boundary", "permission", "validation", "state_conflict"):
            with self.subTest(scenario_type=scenario_type):
                Draft202012Validator(schema).validate(
                    minimal_exception_behavior_scenario_instances(
                        scenario_type=scenario_type,
                    )
                )

    def test_behavior_scenario_instances_schema_rejects_exception_case_shells(self) -> None:
        schema = json.loads(
            BEHAVIOR_SCHEMA_PATHS["speckit.behavior.scenario_instances.v1"].read_text(
                encoding="utf-8"
            )
        )
        invalid_mutations = [
            ("case_kind", lambda scenario: scenario["request_case"].pop("case_kind")),
            ("trigger", lambda scenario: scenario["request_case"].pop("trigger")),
            ("expected_response", lambda scenario: scenario.update({"expected_response": {}})),
            ("error_code", lambda scenario: scenario["expected_response"].pop("error_code")),
            ("expected_feedback", lambda scenario: scenario.update({"expected_feedback": {}})),
            ("feedback_type", lambda scenario: scenario["expected_feedback"].pop("type")),
            ("feedback_message", lambda scenario: scenario["expected_feedback"].pop("message")),
        ]

        for label, mutate in invalid_mutations:
            with self.subTest(label=label):
                instances = minimal_exception_behavior_scenario_instances()
                mutate(instances["scenarios"][0])

                with self.assertRaises(ValidationError):
                    Draft202012Validator(schema).validate(instances)

    def test_behavior_scenario_instances_schema_rejects_mismatched_exception_case_kind(self) -> None:
        schema = json.loads(
            BEHAVIOR_SCHEMA_PATHS["speckit.behavior.scenario_instances.v1"].read_text(
                encoding="utf-8"
            )
        )
        instances = minimal_exception_behavior_scenario_instances(scenario_type="permission")
        instances["scenarios"][0]["request_case"]["case_kind"] = "validation"

        with self.assertRaises(ValidationError):
            Draft202012Validator(schema).validate(instances)

    def test_behavior_scenario_instances_schema_accepts_case_coverage_blockers(self) -> None:
        schema = json.loads(
            BEHAVIOR_SCHEMA_PATHS["speckit.behavior.scenario_instances.v1"].read_text(
                encoding="utf-8"
            )
        )
        instances = minimal_behavior_scenario_instances()
        instances["case_coverage_blockers"] = [
            {
                "id": "BLK-001",
                "case_id": "CASE-002",
                "case_type": "validation",
                "source": "spec.md#user-story-1",
                "reason": "Validation rule is marked Unknown in checklist.",
                "downstream_contract_path": "contracts/behavior/scenario-instances.json",
            }
        ]

        Draft202012Validator(schema).validate(instances)

    def test_behavior_scenario_instances_schema_rejects_incomplete_case_coverage_blockers(self) -> None:
        schema = json.loads(
            BEHAVIOR_SCHEMA_PATHS["speckit.behavior.scenario_instances.v1"].read_text(
                encoding="utf-8"
            )
        )
        required_fields = (
            "id",
            "case_id",
            "case_type",
            "source",
            "reason",
            "downstream_contract_path",
        )

        for field in required_fields:
            with self.subTest(field=field):
                instances = minimal_behavior_scenario_instances()
                blocker = {
                    "id": "BLK-001",
                    "case_id": "CASE-002",
                    "case_type": "validation",
                    "source": "spec.md#user-story-1",
                    "reason": "Validation rule is marked Unknown in checklist.",
                    "downstream_contract_path": "contracts/behavior/scenario-instances.json",
                }
                blocker.pop(field)
                instances["case_coverage_blockers"] = [blocker]

                with self.assertRaises(ValidationError):
                    Draft202012Validator(schema).validate(instances)

    def test_behavior_scenario_instances_schema_accepts_success_boundary_case(self) -> None:
        schema = json.loads(
            BEHAVIOR_SCHEMA_PATHS["speckit.behavior.scenario_instances.v1"].read_text(
                encoding="utf-8"
            )
        )
        instances = minimal_exception_behavior_scenario_instances(scenario_type="boundary")
        scenario = instances["scenarios"][0]
        scenario["request_case"]["outcome"] = "success"
        scenario["expected_response"] = {"business_code": "ACCEPTED_AT_LIMIT"}
        scenario["expected_feedback"] = {"message": "Limit accepted"}

        Draft202012Validator(schema).validate(instances)

    def test_behavior_scenario_instances_schema_rejects_boundary_failure_without_error(self) -> None:
        schema = json.loads(
            BEHAVIOR_SCHEMA_PATHS["speckit.behavior.scenario_instances.v1"].read_text(
                encoding="utf-8"
            )
        )
        instances = minimal_exception_behavior_scenario_instances(scenario_type="boundary")
        scenario = instances["scenarios"][0]
        scenario["request_case"]["outcome"] = "failure"
        scenario["expected_response"] = {"status": 422}
        scenario["expected_feedback"] = {"message": "Limit exceeded"}

        with self.assertRaises(ValidationError):
            Draft202012Validator(schema).validate(instances)

    def test_behavior_assertions_schema_accepts_exception_assertion_intent(self) -> None:
        schema = json.loads(
            BEHAVIOR_SCHEMA_PATHS["speckit.behavior.assertions.v1"].read_text(
                encoding="utf-8"
            )
        )

        Draft202012Validator(schema).validate(minimal_exception_behavior_assertions())

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

    def test_behavior_contract_validator_rejects_exception_case_shells(self) -> None:
        invalid_mutations = [
            ("case_kind", lambda scenario: scenario["request_case"].pop("case_kind")),
            ("trigger", lambda scenario: scenario["request_case"].pop("trigger")),
            ("expected_response", lambda scenario: scenario.update({"expected_response": {}})),
            ("error_code", lambda scenario: scenario["expected_response"].pop("error_code")),
            ("expected_feedback", lambda scenario: scenario.update({"expected_feedback": {}})),
            ("feedback_type", lambda scenario: scenario["expected_feedback"].pop("type")),
            ("feedback_message", lambda scenario: scenario["expected_feedback"].pop("message")),
        ]

        for label, mutate in invalid_mutations:
            with self.subTest(label=label):
                instances = minimal_exception_behavior_scenario_instances()
                mutate(instances["scenarios"][0])

                with self.assertRaisesRegex(ValueError, label):
                    validate_behavior_contract_bundle(
                        instances,
                        minimal_behavior_data_fixtures(),
                        minimal_exception_behavior_assertions(),
                        [minimal_uif_expected()],
                    )

    def test_behavior_contract_validator_rejects_exception_without_state_or_rollback_assertion(self) -> None:
        with self.assertRaisesRegex(
            ValueError,
            "state_invariant_rollback_or_compensation_assertion",
        ):
            validate_behavior_contract_bundle(
                minimal_exception_behavior_scenario_instances(),
                minimal_behavior_data_fixtures(),
                minimal_behavior_assertions(),
                [minimal_uif_expected()],
            )

    def test_behavior_contract_validator_rejects_mismatched_exception_case_kind(self) -> None:
        instances = minimal_exception_behavior_scenario_instances(scenario_type="permission")
        instances["scenarios"][0]["request_case"]["case_kind"] = "validation"

        with self.assertRaisesRegex(ValueError, "case_kind"):
            validate_behavior_contract_bundle(
                instances,
                minimal_behavior_data_fixtures(),
                minimal_exception_behavior_assertions(),
                [minimal_uif_expected()],
            )

    def test_behavior_contract_validator_accepts_structured_exception_cases(self) -> None:
        for scenario_type in ("negative", "boundary", "permission", "validation", "state_conflict"):
            with self.subTest(scenario_type=scenario_type):
                validate_behavior_contract_bundle(
                    minimal_exception_behavior_scenario_instances(
                        scenario_type=scenario_type,
                    ),
                    minimal_behavior_data_fixtures(),
                    minimal_exception_behavior_assertions(),
                    [minimal_uif_expected()],
                )

    def test_behavior_contract_validator_accepts_rollback_and_compensation_assertions(self) -> None:
        for intent in ("rollback", "compensation"):
            with self.subTest(intent=intent):
                validate_behavior_contract_bundle(
                    minimal_exception_behavior_scenario_instances(),
                    minimal_behavior_data_fixtures(),
                    minimal_exception_behavior_assertions_with_intent(intent),
                    [minimal_uif_expected()],
                )

    def test_behavior_contract_validator_accepts_success_boundary_case(self) -> None:
        instances = minimal_exception_behavior_scenario_instances(scenario_type="boundary")
        scenario = instances["scenarios"][0]
        scenario["request_case"]["outcome"] = "success"
        scenario["expected_response"] = {"business_code": "ACCEPTED_AT_LIMIT"}
        scenario["expected_feedback"] = {"message": "Limit accepted"}

        validate_behavior_contract_bundle(
            instances,
            minimal_behavior_data_fixtures(),
            minimal_behavior_assertions(),
            [minimal_uif_expected()],
        )

    def test_behavior_contract_validator_rejects_boundary_failure_without_error(self) -> None:
        instances = minimal_exception_behavior_scenario_instances(scenario_type="boundary")
        scenario = instances["scenarios"][0]
        scenario["request_case"]["outcome"] = "failure"
        scenario["expected_response"] = {"status": 422}
        scenario["expected_feedback"] = {"message": "Limit exceeded"}

        with self.assertRaisesRegex(ValueError, "error_code"):
            validate_behavior_contract_bundle(
                instances,
                minimal_behavior_data_fixtures(),
                minimal_exception_behavior_assertions(),
                [minimal_uif_expected()],
            )

    def test_behavior_case_coverage_validator_rejects_missing_required_case(self) -> None:
        with self.assertRaisesRegex(ValueError, "Required case"):
            validate_behavior_case_coverage(
                minimal_case_coverage(),
                minimal_behavior_scenarios_draft(),
                minimal_behavior_scenario_instances(),
                "T001 implement SCN-001",
                "Validate SCN-001",
            )

    def test_behavior_case_coverage_validator_rejects_empty_matrix(self) -> None:
        with self.assertRaisesRegex(ValueError, "case_coverage"):
            validate_behavior_case_coverage(
                {},
                minimal_behavior_scenarios_draft(),
                minimal_behavior_scenario_instances(),
                "T001 implement SCN-001",
                "Validate SCN-001",
            )

    def test_behavior_case_coverage_validator_requires_tasks_and_quickstart_evidence(self) -> None:
        with self.assertRaisesRegex(ValueError, "tasks.md"):
            validate_behavior_case_coverage(
                minimal_case_coverage(),
                minimal_behavior_scenarios_draft(
                    scenario_type="permission",
                    scenario_id="SCN-ERR-001",
                ),
                minimal_exception_behavior_scenario_instances(),
                "T001 implement SCN-001",
                "Validate SCN-ERR-001",
            )

        with self.assertRaisesRegex(ValueError, "quickstart.md"):
            validate_behavior_case_coverage(
                minimal_case_coverage(),
                minimal_behavior_scenarios_draft(
                    scenario_type="permission",
                    scenario_id="SCN-ERR-001",
                ),
                minimal_exception_behavior_scenario_instances(),
                "T001 implement SCN-ERR-001",
                "Validate SCN-001",
            )

    def test_behavior_case_coverage_validator_accepts_closed_required_case(self) -> None:
        validate_behavior_case_coverage(
            minimal_case_coverage(),
            minimal_behavior_scenarios_draft(
                scenario_type="permission",
                scenario_id="SCN-ERR-001",
            ),
            minimal_exception_behavior_scenario_instances(),
            "T001 implement SCN-ERR-001 and AST-001",
            "Validate SCN-ERR-001 through quickstart path",
        )

    def test_behavior_case_coverage_validator_accepts_formal_blocker_for_required_case(self) -> None:
        instances = minimal_behavior_scenario_instances()
        instances["case_coverage_blockers"] = [
            {
                "id": "BLK-001",
                "case_id": "CASE-002",
                "case_type": "validation",
                "source": "spec.md#user-story-1",
                "reason": "Validation rule is still Unknown in checklist.",
                "downstream_contract_path": "contracts/behavior/scenario-instances.json",
            }
        ]

        validate_behavior_case_coverage(
            minimal_case_coverage_with_blocker(),
            minimal_behavior_scenarios_draft(),
            instances,
            "T001 blocked by BLK-001",
            "BLK-001 blocks quickstart validation",
        )

    def test_behavior_case_coverage_validator_requires_blocker_downstream_evidence(self) -> None:
        instances = minimal_behavior_scenario_instances()
        instances["case_coverage_blockers"] = [
            {
                "id": "BLK-001",
                "case_id": "CASE-002",
                "case_type": "validation",
                "source": "spec.md#user-story-1",
                "reason": "Validation rule is still Unknown in checklist.",
                "downstream_contract_path": "contracts/behavior/scenario-instances.json",
            }
        ]

        with self.assertRaisesRegex(ValueError, "tasks.md"):
            validate_behavior_case_coverage(
                minimal_case_coverage_with_blocker(),
                minimal_behavior_scenarios_draft(),
                instances,
                "T001 implement SCN-001",
                "BLK-001 blocks quickstart validation",
            )

        with self.assertRaisesRegex(ValueError, "quickstart.md"):
            validate_behavior_case_coverage(
                minimal_case_coverage_with_blocker(),
                minimal_behavior_scenarios_draft(),
                instances,
                "T001 blocked by BLK-001",
                "Validate SCN-001",
            )

    def test_behavior_case_coverage_validator_rejects_blocker_source_mismatch(self) -> None:
        instances = minimal_behavior_scenario_instances()
        instances["case_coverage_blockers"] = [
            {
                "id": "BLK-001",
                "case_id": "CASE-002",
                "case_type": "validation",
                "source": "spec.md#different-story",
                "reason": "Validation rule is still Unknown in checklist.",
                "downstream_contract_path": "contracts/behavior/scenario-instances.json",
            }
        ]

        with self.assertRaisesRegex(ValueError, "source"):
            validate_behavior_case_coverage(
                minimal_case_coverage_with_blocker(),
                minimal_behavior_scenarios_draft(),
                instances,
                "T001 blocked by BLK-001",
                "BLK-001 blocks quickstart validation",
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

    def test_validate_manifest_contract_rejects_shard_id_vertical_capability_mismatch(
        self,
    ) -> None:
        manifest = minimal_manifest(
            shards=[
                minimal_shard(shard_id="S01-ui-01", vertical_capability="service-flow")
            ],
            dispatch_order=[["S01-ui-01"]],
            vertical_capability="service-flow",
        )

        with self.assertRaisesRegex(ValueError, "shard_id vertical_capability mismatch"):
            validate_manifest_contract(manifest)

    def test_validate_manifest_contract_rejects_invalid_shard_id_pattern(self) -> None:
        manifest = minimal_manifest(
            shards=[minimal_shard(shard_id="S1-service-flow-01")],
            dispatch_order=[["S1-service-flow-01"]],
        )

        with self.assertRaisesRegex(ValueError, "invalid shard_id"):
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

    def test_validate_implement_contract_rejects_code_review_that_misses_implementation_diff(
        self,
    ) -> None:
        review_shard_id = "S02-service-flow-02"
        review_receipt_path = f"{HANDOFF_DIR}/results/{review_shard_id}.json"
        review_handoff_path = f"{HANDOFF_DIR}/{review_shard_id}.json"
        manifest = minimal_manifest(
            shards=[
                minimal_shard(),
                minimal_shard(
                    shard_id=review_shard_id,
                    task_ids=["T099"],
                ),
            ],
            dependencies=[
                {"shard_id": review_shard_id, "depends_on": [SHARD_ID]},
            ],
            dispatch_order=[[SHARD_ID], [review_shard_id]],
        )
        review_handoff = minimal_handoff(
            shard_id=review_shard_id,
            task_ids=["T099"],
            allowed_write_paths=[review_receipt_path],
            task_type="code_review",
        )
        review_handoff["allowed_read_paths"] = [TASKS_PATH, QUICKSTART_PATH, SERVICE_PATH]

        with self.assertRaisesRegex(ValueError, "implementation changed_paths"):
            validate_implement_contract(
                manifest,
                handoffs_by_path={
                    f"{HANDOFF_DIR}/{SHARD_ID}.json": minimal_handoff(),
                    review_handoff_path: review_handoff,
                },
                receipts_by_path={
                    RECEIPT_PATH: minimal_receipt(changed_paths=[SERVICE_PATH]),
                    review_receipt_path: minimal_receipt(
                        shard_id=review_shard_id,
                        task_ids=["T099"],
                        task_type="code_review",
                        changed_paths=[review_receipt_path],
                        validation_evidence=["Code review checked implementation diff."],
                        review_conclusion={
                            "status": "approved",
                            "summary": "Review complete.",
                            "checked_sources": [QUICKSTART_PATH],
                            "findings": [],
                        },
                        data_side_effect_review=no_data_side_effects_review(
                            paths=[QUICKSTART_PATH]
                        ),
                    ),
                },
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

    def test_validate_handoff_contract_rejects_shard_id_vertical_capability_mismatch(
        self,
    ) -> None:
        handoff = minimal_handoff(shard_id="S01-ui-01", vertical_capability="service-flow")
        with self.assertRaisesRegex(ValueError, "shard_id vertical_capability mismatch"):
            validate_handoff_contract(handoff)

    def test_validate_handoff_contract_rejects_invalid_shard_id_pattern(self) -> None:
        handoff = minimal_handoff(shard_id="S01_service_flow_01")
        with self.assertRaisesRegex(ValueError, "invalid shard_id"):
            validate_handoff_contract(handoff)

    def test_receipt_schema_accepts_minimal_valid_receipt(self) -> None:
        schema = json.loads(RECEIPT_SCHEMA_PATH.read_text(encoding="utf-8"))
        Draft202012Validator(schema).validate(minimal_receipt())

    def test_receipt_schema_accepts_code_review_receipt_fields(self) -> None:
        schema = json.loads(RECEIPT_SCHEMA_PATH.read_text(encoding="utf-8"))
        Draft202012Validator(schema).validate(
            minimal_receipt(
                task_type="code_review",
                changed_paths=[SERVICE_PATH, RECEIPT_PATH],
                review_conclusion={
                    "status": "changes_requested",
                    "summary": "Implementation drift repaired; e2e environment pending.",
                    "checked_sources": [
                        API_CONTRACT_PATH,
                        SEQUENCES_PATH,
                        QUICKSTART_PATH,
                    ],
                    "findings": [
                        {
                            "id": "CR-001",
                            "severity": "high",
                            "category": "sequence_drift",
                            "summary": "Retry order differed from contracts/sequences.md.",
                            "paths": [SERVICE_PATH],
                            "resolution": "repaired",
                        }
                    ],
                },
                data_side_effect_review={
                    "reviewed_diff_paths": [SERVICE_PATH],
                    "runtime_data_writes_found": True,
                    "mutation_findings": [
                        {
                            "id": "DSE-001",
                            "severity": "high",
                            "category": "field_level_update",
                            "summary": "Order status update may affect shared fulfillment flow.",
                            "paths": [SERVICE_PATH],
                            "operation": "update",
                            "tables_or_entities": ["orders"],
                            "fields": ["status"],
                            "resolution": "blocked",
                        }
                    ],
                },
                consistency_repairs=[
                    {
                        "finding_id": "CR-001",
                        "reason": "Restore planned retry ordering.",
                        "changed_paths": [SERVICE_PATH],
                        "evidence": ["contracts/sequences.md retry flow"],
                    }
                ],
                deferred_validation_todos=[
                    {
                        "id": "E2E-001",
                        "reason": "Real payment sandbox unavailable.",
                        "missing_environment": ["PAYMENT_SANDBOX_TOKEN"],
                        "validation_path": "quickstart.md#real-e2e",
                        "commands": ["npm run e2e:payment"],
                        "blocking": False,
                    }
                ],
            )
        )

    def test_receipt_schema_rejects_review_conclusion_without_checked_sources(self) -> None:
        schema = json.loads(RECEIPT_SCHEMA_PATH.read_text(encoding="utf-8"))
        receipt = minimal_receipt(
            task_type="code_review",
            review_conclusion={
                "status": "approved",
                "summary": "Review complete.",
                "findings": [],
            },
        )

        with self.assertRaises(ValidationError):
            Draft202012Validator(schema).validate(receipt)

    def test_receipt_schema_requires_data_side_effect_review_for_code_review_receipt(
        self,
    ) -> None:
        schema = json.loads(RECEIPT_SCHEMA_PATH.read_text(encoding="utf-8"))
        receipt = minimal_receipt(
            task_type="code_review",
            review_conclusion={
                "status": "approved",
                "summary": "Review complete.",
                "checked_sources": [SERVICE_PATH],
                "findings": [],
            },
        )

        with self.assertRaises(ValidationError):
            Draft202012Validator(schema).validate(receipt)

    def test_receipt_schema_rejects_data_side_effect_review_without_reviewed_diff_paths(
        self,
    ) -> None:
        schema = json.loads(RECEIPT_SCHEMA_PATH.read_text(encoding="utf-8"))
        receipt = minimal_receipt(
            task_type="code_review",
            review_conclusion={
                "status": "approved",
                "summary": "Review complete.",
                "checked_sources": [SERVICE_PATH],
                "findings": [],
            },
            data_side_effect_review={
                "runtime_data_writes_found": False,
                "mutation_findings": [],
            },
        )

        with self.assertRaises(ValidationError):
            Draft202012Validator(schema).validate(receipt)

    def test_receipt_schema_rejects_empty_deferred_validation_environment(self) -> None:
        schema = json.loads(RECEIPT_SCHEMA_PATH.read_text(encoding="utf-8"))
        receipt = minimal_receipt(
            task_type="code_review",
            review_conclusion={
                "status": "blocked",
                "summary": "Real e2e environment unavailable.",
                "checked_sources": [QUICKSTART_PATH],
                "findings": [],
            },
            deferred_validation_todos=[
                {
                    "id": "E2E-001",
                    "reason": "Real e2e environment missing.",
                    "missing_environment": [],
                    "validation_path": "quickstart.md#payment-e2e",
                    "commands": ["npm run e2e:payment"],
                    "blocking": False,
                }
            ],
        )

        with self.assertRaises(ValidationError):
            Draft202012Validator(schema).validate(receipt)

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

    def test_validate_receipt_contract_rejects_completed_tasks_with_deferred_validation(
        self,
    ) -> None:
        with self.assertRaisesRegex(ValueError, "completed_task_ids"):
            validate_receipt_contract(
                minimal_handoff(),
                minimal_receipt(
                    deferred_validation_todos=[
                        {
                            "id": "VAL-001",
                            "reason": "Sandbox credentials unavailable.",
                            "missing_environment": ["PAYMENT_SANDBOX_TOKEN"],
                            "validation_path": "quickstart.md#payment",
                            "commands": ["npm run e2e:payment"],
                            "blocking": False,
                        }
                    ],
                ),
                RECEIPT_PATH,
            )

    def test_validate_receipt_contract_rejects_completed_code_review_without_approval(
        self,
    ) -> None:
        handoff = minimal_handoff(task_ids=["T099"], task_type="code_review")
        handoff["allowed_read_paths"] = [TASKS_PATH, SERVICE_PATH]

        with self.assertRaisesRegex(ValueError, "approved"):
            validate_receipt_contract(
                handoff,
                minimal_receipt(
                    task_ids=["T099"],
                    task_type="code_review",
                    review_conclusion={
                        "status": "changes_requested",
                        "summary": "Review found pending repairs.",
                        "checked_sources": [SERVICE_PATH],
                        "findings": [],
                    },
                    data_side_effect_review=no_data_side_effects_review(),
                ),
                RECEIPT_PATH,
            )

    def test_validate_receipt_contract_requires_review_conclusion_for_code_review_task(
        self,
    ) -> None:
        handoff = minimal_handoff(task_ids=["T099"], task_type="code_review")
        handoff["task_text"] = ["T099 Review final implementation readiness"]

        with self.assertRaisesRegex(ValueError, "review_conclusion"):
            validate_receipt_contract(
                handoff,
                minimal_receipt(task_ids=["T099"], task_type="code_review"),
                RECEIPT_PATH,
            )

    def test_validate_receipt_contract_rejects_code_review_receipt_without_task_type(
        self,
    ) -> None:
        handoff = minimal_handoff(task_ids=["T099"], task_type="code_review")

        with self.assertRaisesRegex(ValueError, "task_type"):
            validate_receipt_contract(
                handoff,
                minimal_receipt(task_ids=["T099"], task_type="implementation"),
                RECEIPT_PATH,
            )

    def test_validate_receipt_contract_requires_checked_sources_for_code_review_task(
        self,
    ) -> None:
        handoff = minimal_handoff(task_ids=["T099"], task_type="code_review")

        with self.assertRaisesRegex(ValueError, "checked_sources"):
            validate_receipt_contract(
                handoff,
                minimal_receipt(
                    task_ids=["T099"],
                    task_type="code_review",
                    review_conclusion={
                        "status": "approved",
                        "summary": "Review complete.",
                        "findings": [],
                    },
                ),
                RECEIPT_PATH,
            )

    def test_validate_receipt_contract_requires_data_side_effect_review_for_code_review_task(
        self,
    ) -> None:
        handoff = minimal_handoff(task_ids=["T099"], task_type="code_review")
        handoff["allowed_read_paths"] = [TASKS_PATH, SERVICE_PATH]

        with self.assertRaisesRegex(ValueError, "data_side_effect_review"):
            validate_receipt_contract(
                handoff,
                minimal_receipt(
                    task_ids=["T099"],
                    task_type="code_review",
                    review_conclusion={
                        "status": "approved",
                        "summary": "Review complete.",
                        "checked_sources": [SERVICE_PATH],
                        "findings": [],
                    },
                ),
                RECEIPT_PATH,
            )

    def test_validate_receipt_contract_requires_complete_data_side_effect_review(
        self,
    ) -> None:
        handoff = minimal_handoff(task_ids=["T099"], task_type="code_review")
        handoff["allowed_read_paths"] = [TASKS_PATH, SERVICE_PATH]

        for field in (
            "reviewed_diff_paths",
            "runtime_data_writes_found",
            "mutation_findings",
        ):
            data_side_effect_review = no_data_side_effects_review()
            data_side_effect_review.pop(field)

            with self.subTest(field=field):
                with self.assertRaisesRegex(ValueError, field):
                    validate_receipt_contract(
                        handoff,
                        minimal_receipt(
                            task_ids=["T099"],
                            task_type="code_review",
                            review_conclusion={
                                "status": "approved",
                                "summary": "Review complete.",
                                "checked_sources": [SERVICE_PATH],
                                "findings": [],
                            },
                            data_side_effect_review=data_side_effect_review,
                        ),
                        RECEIPT_PATH,
                    )

    def test_validate_receipt_contract_rejects_unreviewed_diff_path_for_data_side_effect_review(
        self,
    ) -> None:
        handoff = minimal_handoff(task_ids=["T099"], task_type="code_review")
        handoff["allowed_read_paths"] = [TASKS_PATH, SERVICE_PATH]

        with self.assertRaisesRegex(ValueError, "reviewed_diff_paths"):
            validate_receipt_contract(
                handoff,
                minimal_receipt(
                    task_ids=["T099"],
                    task_type="code_review",
                    review_conclusion={
                        "status": "approved",
                        "summary": "Review complete.",
                        "checked_sources": [SERVICE_PATH],
                        "findings": [],
                    },
                    data_side_effect_review={
                        "reviewed_diff_paths": [f"{FEATURE_PATH}/src/unread.py"],
                        "runtime_data_writes_found": False,
                        "mutation_findings": [],
                    },
                ),
                RECEIPT_PATH,
            )

    def test_validate_receipt_contract_rejects_approved_with_unresolved_high_data_side_effect(
        self,
    ) -> None:
        handoff = minimal_handoff(task_ids=["T099"], task_type="code_review")
        handoff["allowed_read_paths"] = [TASKS_PATH, SERVICE_PATH]

        with self.assertRaisesRegex(ValueError, "data side-effect"):
            validate_receipt_contract(
                handoff,
                minimal_receipt(
                    task_ids=["T099"],
                    task_type="code_review",
                    review_conclusion={
                        "status": "approved",
                        "summary": "Review complete.",
                        "checked_sources": [SERVICE_PATH],
                        "findings": [],
                    },
                    data_side_effect_review={
                        "reviewed_diff_paths": [SERVICE_PATH],
                        "runtime_data_writes_found": True,
                        "mutation_findings": [
                            {
                                "id": "DSE-001",
                                "severity": "high",
                                "category": "field_level_update",
                                "summary": "Shared status field update may disable other flows.",
                                "paths": [SERVICE_PATH],
                                "operation": "update",
                                "tables_or_entities": ["orders"],
                                "fields": ["status"],
                                "resolution": "todo",
                            }
                        ],
                    },
                ),
                RECEIPT_PATH,
            )

    def test_validate_receipt_contract_rejects_checked_source_outside_allowed_reads(
        self,
    ) -> None:
        handoff = minimal_handoff(task_ids=["T099"], task_type="code_review")

        with self.assertRaisesRegex(ValueError, "checked_sources"):
            validate_receipt_contract(
                handoff,
                minimal_receipt(
                    task_ids=["T099"],
                    task_type="code_review",
                    review_conclusion={
                        "status": "approved",
                        "summary": "Review complete.",
                        "checked_sources": [API_CONTRACT_PATH],
                        "findings": [],
                    },
                ),
                RECEIPT_PATH,
            )

    def test_validate_receipt_contract_rejects_repair_path_outside_allowed_writes(
        self,
    ) -> None:
        handoff = minimal_handoff(task_ids=["T099"], task_type="code_review")
        handoff["allowed_read_paths"] = [TASKS_PATH, SEQUENCES_PATH]

        with self.assertRaisesRegex(ValueError, "consistency repair changed path"):
            validate_receipt_contract(
                handoff,
                minimal_receipt(
                    task_ids=["T099"],
                    task_type="code_review",
                    completed_task_ids=[],
                    review_conclusion={
                        "status": "changes_requested",
                        "summary": "Contract drift repaired.",
                        "checked_sources": [SEQUENCES_PATH],
                        "findings": [],
                    },
                    data_side_effect_review=no_data_side_effects_review(
                        paths=[SEQUENCES_PATH]
                    ),
                    consistency_repairs=[
                        {
                            "finding_id": "CR-001",
                            "reason": "Align API contract.",
                            "changed_paths": [f"{FEATURE_PATH}/contracts/api/refunds.yaml"],
                            "evidence": ["plan.md API contract"],
                        }
                    ],
                ),
                RECEIPT_PATH,
            )

    def test_validate_receipt_contract_requires_todo_for_deferred_real_e2e(self) -> None:
        handoff = minimal_handoff(task_ids=["T099"], task_type="code_review")
        handoff["allowed_read_paths"] = [TASKS_PATH, QUICKSTART_PATH]
        handoff["validation_commands"] = ["npm run e2e:payment"]
        handoff["task_text"] = ["T099 Review real e2e readiness"]

        with self.assertRaisesRegex(ValueError, "deferred_validation_todos"):
            validate_receipt_contract(
                handoff,
                minimal_receipt(
                    task_ids=["T099"],
                    task_type="code_review",
                    completed_task_ids=[],
                    validation_evidence=[
                        "quickstart.md command npm run e2e:payment: real e2e cannot run, missing PAYMENT_SANDBOX_TOKEN"
                    ],
                    review_conclusion={
                        "status": "blocked",
                        "summary": "Real e2e environment unavailable.",
                        "checked_sources": [QUICKSTART_PATH],
                        "findings": [],
                    },
                    data_side_effect_review=no_data_side_effects_review(
                        paths=[QUICKSTART_PATH]
                    ),
                ),
                RECEIPT_PATH,
            )

    def test_validate_receipt_contract_rejects_approved_with_unresolved_high_finding(
        self,
    ) -> None:
        handoff = minimal_handoff(task_ids=["T099"], task_type="code_review")
        handoff["allowed_read_paths"] = [TASKS_PATH, API_CONTRACT_PATH]

        with self.assertRaisesRegex(ValueError, "unresolved"):
            validate_receipt_contract(
                handoff,
                minimal_receipt(
                    task_ids=["T099"],
                    task_type="code_review",
                    review_conclusion={
                        "status": "approved",
                        "summary": "Approved despite known API drift.",
                        "checked_sources": [API_CONTRACT_PATH],
                        "findings": [
                            {
                                "id": "CR-001",
                                "severity": "high",
                                "category": "api_contract_drift",
                                "summary": "Response schema still differs from API contract.",
                                "paths": [SERVICE_PATH],
                                "resolution": "todo",
                            }
                        ],
                    },
                    data_side_effect_review=no_data_side_effects_review(
                        paths=[API_CONTRACT_PATH]
                    ),
                ),
                RECEIPT_PATH,
            )

    def test_validate_receipt_contract_rejects_approved_when_real_e2e_deferred(
        self,
    ) -> None:
        handoff = minimal_handoff(task_ids=["T099"], task_type="code_review")
        handoff["allowed_read_paths"] = [TASKS_PATH, QUICKSTART_PATH]
        handoff["validation_commands"] = ["npm run e2e:payment"]

        with self.assertRaisesRegex(ValueError, "approved"):
            validate_receipt_contract(
                handoff,
                minimal_receipt(
                    task_ids=["T099"],
                    task_type="code_review",
                    completed_task_ids=[],
                    validation_evidence=[
                        "quickstart.md command npm run e2e:payment: real e2e cannot run, missing PAYMENT_SANDBOX_TOKEN"
                    ],
                    review_conclusion={
                        "status": "approved",
                        "summary": "Approved although real e2e is missing.",
                        "checked_sources": [QUICKSTART_PATH],
                        "findings": [],
                    },
                    data_side_effect_review=no_data_side_effects_review(
                        paths=[QUICKSTART_PATH]
                    ),
                    deferred_validation_todos=[
                        {
                            "id": "E2E-001",
                            "reason": "Real e2e environment missing.",
                            "missing_environment": ["PAYMENT_SANDBOX_TOKEN"],
                            "validation_path": "quickstart.md#payment-e2e",
                            "commands": ["npm run e2e:payment"],
                            "blocking": False,
                        }
                    ],
                ),
                RECEIPT_PATH,
            )

    def test_validate_receipt_contract_requires_code_review_command_evidence(
        self,
    ) -> None:
        handoff = minimal_handoff(task_ids=["T099"], task_type="code_review")
        handoff["allowed_read_paths"] = [TASKS_PATH, API_CONTRACT_PATH, QUICKSTART_PATH]
        handoff["validation_commands"] = ["npm run test:contract", "npm run e2e:payment"]

        with self.assertRaisesRegex(ValueError, "validation_evidence"):
            validate_receipt_contract(
                handoff,
                minimal_receipt(
                    task_ids=["T099"],
                    task_type="code_review",
                    completed_task_ids=[],
                    validation_evidence=["Code review completed."],
                    review_conclusion={
                        "status": "changes_requested",
                        "summary": "Review complete; validation still pending.",
                        "checked_sources": [API_CONTRACT_PATH, QUICKSTART_PATH],
                        "findings": [],
                    },
                    data_side_effect_review=no_data_side_effects_review(
                        paths=[API_CONTRACT_PATH]
                    ),
                ),
                RECEIPT_PATH,
            )

    def test_validate_receipt_contract_accepts_code_review_with_repair_and_e2e_todo(
        self,
    ) -> None:
        handoff = minimal_handoff(task_ids=["T099"], task_type="code_review")
        handoff["allowed_read_paths"] = [
            TASKS_PATH,
            SEQUENCES_PATH,
            QUICKSTART_PATH,
            SERVICE_PATH,
        ]
        handoff["validation_commands"] = ["npm run e2e:payment"]
        handoff["task_text"] = ["T099 Review design drift and real e2e readiness"]

        validate_receipt_contract(
            handoff,
            minimal_receipt(
                task_ids=["T099"],
                task_type="code_review",
                completed_task_ids=[],
                changed_paths=[SERVICE_PATH],
                validation_evidence=[
                    "checked contracts/sequences.md; quickstart.md command npm run e2e:payment deferred because PAYMENT_SANDBOX_TOKEN is unavailable; real e2e deferred"
                ],
                review_conclusion={
                    "status": "changes_requested",
                    "summary": "Sequence drift repaired; real e2e pending.",
                    "checked_sources": [SEQUENCES_PATH, QUICKSTART_PATH],
                    "findings": [
                        {
                            "id": "CR-001",
                            "severity": "high",
                            "category": "sequence_drift",
                            "summary": "Retry sequence drifted from planned flow.",
                            "paths": [SERVICE_PATH],
                            "resolution": "repaired",
                        }
                    ],
                },
                data_side_effect_review=no_data_side_effects_review(),
                consistency_repairs=[
                    {
                        "finding_id": "CR-001",
                        "reason": "Align implementation with planned sequence.",
                        "changed_paths": [SERVICE_PATH],
                        "evidence": ["contracts/sequences.md"],
                    }
                ],
                deferred_validation_todos=[
                    {
                        "id": "E2E-001",
                        "reason": "Real e2e environment missing.",
                        "missing_environment": ["PAYMENT_SANDBOX_TOKEN"],
                        "validation_path": "quickstart.md#payment-e2e",
                        "commands": ["npm run e2e:payment"],
                        "blocking": False,
                    }
                ],
            ),
            RECEIPT_PATH,
        )

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

    def test_validate_receipt_contract_rejects_generic_visual_evidence(self) -> None:
        handoff = minimal_handoff(
            shard_id="S01-ui-01",
            vertical_capability="ui",
            allowed_write_paths=[f"{FEATURE_PATH}/src/ui/refund.tsx", f"{HANDOFF_DIR}/results/S01-ui-01.json"],
        )
        handoff["allowed_read_paths"] = [
            TASKS_PATH,
            f"{FEATURE_PATH}/checklists/behavior-testability.md",
            f"{FEATURE_PATH}/contracts/uif/refund.json",
            f"{FEATURE_PATH}/quickstart.md",
        ]
        handoff["task_text"] = [
            "T010 visual_verification for Visual Item ID VUI-001 with Requirement Status Required"
        ]
        receipt_path = f"{HANDOFF_DIR}/results/S01-ui-01.json"
        handoff["task_status_update"]["receipt_path"] = receipt_path

        with self.assertRaisesRegex(ValueError, "Visual Item ID"):
            validate_receipt_contract(
                handoff,
                minimal_receipt(
                    shard_id="S01-ui-01",
                    changed_paths=[f"{FEATURE_PATH}/src/ui/refund.tsx"],
                    validation_evidence=["unit tests passed"],
                ),
                receipt_path,
            )

    def test_validate_receipt_contract_accepts_visual_evidence_references(self) -> None:
        handoff = minimal_handoff(
            shard_id="S01-ui-01",
            vertical_capability="ui",
            allowed_write_paths=[f"{FEATURE_PATH}/src/ui/refund.tsx", f"{HANDOFF_DIR}/results/S01-ui-01.json"],
        )
        handoff["allowed_read_paths"] = [
            TASKS_PATH,
            f"{FEATURE_PATH}/checklists/behavior-testability.md",
            f"{FEATURE_PATH}/contracts/uif/refund.json",
            f"{FEATURE_PATH}/quickstart.md",
        ]
        handoff["task_text"] = [
            "T010 visual_verification for Visual Item ID VUI-001 with Requirement Status Required"
        ]
        receipt_path = f"{HANDOFF_DIR}/results/S01-ui-01.json"
        handoff["task_status_update"]["receipt_path"] = receipt_path

        validate_receipt_contract(
            handoff,
            minimal_receipt(
                shard_id="S01-ui-01",
                changed_paths=[f"{FEATURE_PATH}/src/ui/refund.tsx"],
                validation_evidence=[
                    "Visual Item ID VUI-001 Requirement Status Required verified with screenshot ref quickstart.md#visual-refund"
                ],
            ),
            receipt_path,
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

    def test_manifest_schema_rejects_invalid_shard_id_pattern(self) -> None:
        schema = json.loads(MANIFEST_SCHEMA_PATH.read_text(encoding="utf-8"))
        manifest = minimal_manifest(
            shards=[minimal_shard(shard_id="S1-service-flow-01")],
            dispatch_order=[["S1-service-flow-01"]],
        )
        with self.assertRaises(ValidationError):
            Draft202012Validator(schema).validate(manifest)

    def test_handoff_schema_rejects_invalid_shard_id_pattern(self) -> None:
        schema = json.loads(HANDOFF_SCHEMA_PATH.read_text(encoding="utf-8"))
        handoff = minimal_handoff(shard_id="S01_service_flow_01")
        with self.assertRaises(ValidationError):
            Draft202012Validator(schema).validate(handoff)

    def test_receipt_schema_rejects_invalid_shard_id_pattern(self) -> None:
        schema = json.loads(RECEIPT_SCHEMA_PATH.read_text(encoding="utf-8"))
        receipt = minimal_receipt(shard_id="S01-service-flow-1")
        with self.assertRaises(ValidationError):
            Draft202012Validator(schema).validate(receipt)

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

        lines = command.splitlines()
        self.assertLessEqual(len(lines), 80)
        self.assertLessEqual(len(command), 4000)
        self.assertLessEqual(max(len(line) for line in lines), 120)
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
        self.assertIn("tests/contracts/speckit-cross-agent-subagents.md", readme)
        self.assertIn("Problem Addressed", readme)
        self.assertIn("reasoning quality", readme)
        self.assertNotIn("compatible with the core workflow", readme)
        self.assertNotIn("core compatibility fixes", readme)
        self.assertIn("must formalize", readme)
        self.assertIn("N/A or blocker", readme)
        self.assertIn("The preset has four goals:", readme)
        self.assertIn("BDD readiness gate", readme)
        self.assertIn("NFR readiness", readme)
        self.assertIn("BDD/NFR/applicable Visual Fidelity", readme)
        self.assertIn("External Intake And Visual SSOT", readme)
        self.assertIn("spec-kit-intake", readme)
        self.assertIn("external intake evidence + visual SSOT refs -> /speckit.specify -> baseline spec.md", readme)
        self.assertIn("does not perform intake", readme)
        self.assertIn("parse HTML SSOT bundles", readme)
        self.assertIn("decide provider source readiness", readme)
        self.assertIn("visual SSOT refs", readme)
        self.assertIn("external evidence refs", readme)
        self.assertIn("source-backed facts", readme)
        self.assertIn("Product semantics implied only by provider evidence remain `[NEEDS CLARIFICATION]`", readme)
        self.assertIn("speckit.intake.visual-design", readme)
        self.assertIn("speckit.intake.html-ssot", readme)
        self.assertIn("Visual Fidelity readiness gate", readme)
        self.assertIn("Screenshot is evidence, not intake", readme)
        self.assertIn("optional but strongly recommended visual evidence", readme)
        self.assertIn("L0 No Screenshot", readme)
        self.assertIn("L1 Key Screenshots", readme)
        self.assertIn("L2 State + Viewport Matrix", readme)
        self.assertIn("L3 Visual Baseline", readme)
        self.assertIn("pixel-perfect", readme)
        self.assertIn("Screenshots cannot upgrade product semantics", readme)
        self.assertIn(
            CANONICAL_RESPONSIVE_VISUAL_RULE,
            readme,
        )
        self.assertIn(
            "product-side visual requirements such as pixel-perfect, brand-critical, responsive visual, or UI visual acceptance requirements",
            readme,
        )
        self.assertIn("Visual Fidelity Evidence Matrix", readme)
        self.assertIn("visual requirement or visual proof obligation", readme)
        self.assertIn("single visual readiness record", readme)
        self.assertIn("only the Visual Fidelity Evidence Matrix decides visual planning readiness", readme)
        self.assertIn("proof sufficiency", readme)
        self.assertIn("accepted exception rules", readme)
        self.assertIn("The intake extension owns source capture", readme)
        self.assertIn("HTML SSOT bundle contracts", readme)
        self.assertIn("source-side validators live in the `spec-kit-intake` extension", readme)
        self.assertIn("[BLOCKED: PROVIDER_EVIDENCE]", readme)
        self.assertNotIn(
            "writes or marks it as `[NEEDS CLARIFICATION]`",
            readme,
        )
        self.assertIn("source-side readiness", readme)
        self.assertIn("The Visual Fidelity Evidence Matrix remains the only planning readiness gate", readme)
        self.assertIn("clarifies evidence-derived gaps already written in `spec.md`", readme)
        self.assertIn("does not call provider tools", readme)
        self.assertIn("explicit non-functional requirement declarations", readme)
        self.assertIn("Required, Not Applicable, or Unknown", readme)
        self.assertIn("missing or unverifiable NFR assumptions", readme)
        self.assertIn("Phase 0 behavior projection", readme)
        self.assertIn("Case Coverage Matrix", readme)
        self.assertIn("case coverage", readme)
        self.assertIn("Required, Not Applicable, or Unknown", readme)
        lowered = readme.lower()
        for forbidden in FORBIDDEN_VISUAL_COMPAT_TERMS:
            self.assertNotIn(forbidden, lowered)
        self.assertNotIn(
            "Responsive visual readiness must record viewport-specific evidence or set Gate Status: BLOCKED",
            readme,
        )
        self.assertNotIn(
            "Responsive visual readiness records viewport-specific evidence or sets Gate Status: BLOCKED",
            readme,
        )
        self.assertIn("failure scenarios", readme)
        self.assertIn(
            "error code, failure feedback, and state invariant, rollback, or compensation assertion",
            readme,
        )
        self.assertIn("visual verification, contract validation, data-side-effect validation, integration/e2e validation, and scope-aware code review tasks", readme)
        self.assertIn("without inventing validation strategy, changing requirements, updating contracts, or widening scope", readme)
        self.assertIn("validation_evidence", readme)
        self.assertIn("Context-load controls", readme)
        self.assertIn("context-load controls", changelog)
        self.assertIn("Case Coverage Matrix", changelog)
        self.assertIn("failure behavior scenarios", changelog)
        self.assertIn("Change Scope Granularity", changelog)
        self.assertIn("/speckit.constitution", changelog)
        self.assertIn("Moved behavior draft generation from `/speckit.specify` to `/speckit.plan` Phase 0", changelog)
        self.assertIn("BDD readiness gate", changelog)
        self.assertIn("NFR readiness", changelog)
        self.assertIn("explicitly declare applicable non-functional requirements", changelog)
        self.assertIn("Removed `behavior/open-questions.json`", changelog)
        self.assertIn("Hardened behavior contract quality gates", changelog)
        self.assertIn("formalization blockers", changelog)
        self.assertIn("behavior-linked validation evidence", changelog)
        self.assertIn("only the checklist Visual Fidelity Evidence Matrix decides visual planning readiness", changelog)
        self.assertNotIn("run-orchestrated-implement.py", readme)
        self.assertNotIn("speckit-implement-handoff.py", readme)
        self.assertNotIn("--dry-run true --run-id manual", readme)
        self.assertIn("Spec Kit CLI `>=0.8.10.dev0`", readme)
        self.assertIn("python3 -m pip install -r requirements-dev.txt", readme)
        self.assertIn("Preset CI Boundary", readme)
        self.assertIn("SPEC_KIT_FORK_PR_TOKEN", readme)
        self.assertIn("bigsmartben/spec-kit", readme)
        self.assertIn("workflow-preset-release-v<version>", readme)
        self.assertIn("integration PR", readme)
        self.assertIn("next patch version", readme)
        self.assertIn("does not open pull requests to `github/spec-kit`", readme)
        self.assertNotIn("repository_dispatch", readme)
        self.assertIn("PyYAML", requirements)
        self.assertIn("jsonschema", requirements)
        self.assertIn("## 1.2.0", changelog)
        self.assertIn("## 1.1.0", changelog)
        self.assertIn("## 1.0.3", changelog)
        self.assertIn("Final Code Review", changelog)
        self.assertIn("structured code review receipts", changelog)
        self.assertIn("Migrated product, design, provider, and HTML intake ownership out of the workflow preset", changelog)
        self.assertIn("external intake refs and visual SSOT refs", changelog)
        self.assertIn("/speckit.tasks` defines validation, visual verification, contract validation, data-side-effect validation, integration/e2e validation", changelog)
        self.assertIn("/speckit.implement` only executes those tasks and records receipt evidence", changelog)
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
            "Code Review Receipts",
            "task_type: code_review",
            "review_conclusion",
            "checked_sources",
            "consistency_repairs",
            "deferred_validation_todos",
            "quickstart/contract validation command",
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
            "Source intake artifacts belong in an extension, not this preset",
            "External intake owns source capture",
            "rendered HTML SSOT bundles",
            "Behavior-first extension rule",
            "BDD and UIF artifacts need independent templates",
            "`/speckit.constitution`: constitution governance and project principles only",
            "`/speckit.checklist`: checklist artifacts and BDD/NFR/Visual Fidelity readiness gates only",
            "external intake refs",
            "visual SSOT refs",
            "External evidence refs must not",
            "decide visual planning readiness",
            "proof sufficiency",
            "Visual Fidelity Evidence Matrix",
            "one row per visual requirement or visual proof obligation",
            "Source `spec.md` section",
            "Fidelity Scope",
            "Screenshot Level",
            "Evidence Refs",
            "Visual Proof Required",
            "Blocking Item ID",
            "Exception Rule",
            CANONICAL_RESPONSIVE_VISUAL_RULE,
            "single visual readiness record",
            "only artifact that decides visual planning readiness",
            "visual proof level sufficiency",
            "screenshot sufficiency",
            "accepted exception rules",
            "checklist Gate Status",
            "checklist Blocking Items",
            "Source-side intake readiness remains separate",
            "Provider tools, provider execution, hooks, adapter scripts",
            "External design extraction is not a clarification responsibility",
            "NFR readiness belongs in `spec.md` product requirements",
            "`/speckit.plan`: Phase 0 behavior projection, planning artifacts, and formal contracts",
            "`/speckit.tasks` owns implementation, validation, visual verification, contract validation, data-side-effect validation, integration/e2e validation, and code review task definition in `tasks.md`",
            "`/speckit.implement` may execute those tasks and record receipt evidence",
            "must not invent validation strategy, add lifecycle roles, change requirements, update contracts, or widen scope during execution",
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
        lowered = document.lower()
        for forbidden in FORBIDDEN_VISUAL_COMPAT_TERMS:
            self.assertNotIn(forbidden, lowered)
        self.assertNotIn(
            "Responsive visual readiness must record viewport-specific evidence or set Gate Status: BLOCKED",
            document,
        )
        self.assertNotIn(
            "Responsive visual readiness records viewport-specific evidence or sets Gate Status: BLOCKED",
            document,
        )

    def test_agents_references_extension_governance(self) -> None:
        agents = AGENTS_PATH.read_text(encoding="utf-8")

        self.assertIn("docs/extension-governance.md", agents)
        self.assertIn("Extension Governance", agents)

    def _workflow_on(self, workflow: dict) -> dict:
        return workflow.get("on") or workflow.get(True) or {}

    def test_github_actions_contract_workflow(self) -> None:
        workflow_path = REPO_ROOT / ".github" / "workflows" / "ci.yml"
        if not workflow_path.exists():
            self.skipTest("source repository workflow file is not packaged in the preset")
        workflow = yaml.safe_load(workflow_path.read_text(encoding="utf-8"))

        self.assertEqual("Preset Contract", workflow["name"])
        self.assertEqual({"contents": "read"}, workflow["permissions"])
        triggers = self._workflow_on(workflow)
        self.assertIn("pull_request", triggers)
        self.assertEqual(["main"], triggers["push"]["branches"])
        self.assertIn("workflow_dispatch", triggers)

        contract_job = workflow["jobs"]["contract"]
        self.assertEqual("ubuntu-latest", contract_job["runs-on"])
        self.assertEqual(
            ["3.10", "3.13"],
            contract_job["strategy"]["matrix"]["python-version"],
        )
        workflow_text = workflow_path.read_text(encoding="utf-8")
        self.assertIn("python3 -m pip install -r requirements-dev.txt", workflow_text)
        self.assertIn("python3 -m unittest tests/test_preset_contract.py", workflow_text)

    def test_github_actions_artifact_release_and_integration_pr_workflow(self) -> None:
        workflow_path = REPO_ROOT / ".github" / "workflows" / "preset-artifact.yml"
        if not workflow_path.exists():
            self.skipTest("source repository workflow file is not packaged in the preset")
        workflow = yaml.safe_load(workflow_path.read_text(encoding="utf-8"))

        self.assertEqual("Preset Artifact", workflow["name"])
        self.assertEqual({"contents": "write"}, workflow["permissions"])
        triggers = self._workflow_on(workflow)
        self.assertEqual(["v*"], triggers["push"]["tags"])
        self.assertIn("workflow_dispatch", triggers)
        inputs = triggers["workflow_dispatch"]["inputs"]
        self.assertIn("version", inputs)
        self.assertIn("spec_kit_ref", inputs)
        self.assertIn("create_integration_pr", inputs)

        workflow_text = workflow_path.read_text(encoding="utf-8")
        required_terms = [
            "spec-kit-workflow-preset-v${VERSION}.zip",
            "NEXT_PATCH_VERSION",
            "python3 -m unittest tests/test_preset_contract.py",
            "python3 -m venv \"${GITHUB_WORKSPACE}/.venv-specify-smoke\"",
            "echo \"${GITHUB_WORKSPACE}/.venv-specify-smoke/bin\" >> \"${GITHUB_PATH}\"",
            'PATH="${GITHUB_WORKSPACE}/.venv-specify-smoke/bin:${PATH}"',
            'project_dir="$(mktemp -d "${RUNNER_TEMP}/workflow-preset-smoke.XXXXXX")"',
            'resolve_out="${RUNNER_TEMP}/plan-template-resolve.txt"',
            'constitution_resolve_out="${RUNNER_TEMP}/constitution-template-resolve.txt"',
            "PIP_CONFIG_FILE: /dev/null",
            'PYTEST_ADDOPTS: ""',
            'export TMPDIR="${RUNNER_TEMP}"',
            'export TEMP="${RUNNER_TEMP}"',
            'export TMP="${RUNNER_TEMP}"',
            'specify init --here --integration claude --script sh --ignore-agent-tools',
            "specify preset remove workflow-preset",
            "specify preset add --dev",
            "specify preset resolve plan-template",
            "specify preset resolve constitution-template",
            "R: Repository / Workspace",
            "M: Module / Capability",
            "U: Unit / Design Object",
            "O: Operation / Detail",
            ".claude/skills/speckit-implement/SKILL.md",
            "SPEC_KIT_FORK_PR_TOKEN",
            "bigsmartben/spec-kit",
            "workflow-preset-release-v${VERSION}",
            "gh pr create",
            "gh pr edit",
            "WORKFLOW_PRESET_DOWNLOAD_URL",
            "presets/catalog.community.json",
            "community_catalog_path",
            "community_catalog",
            "download_url",
            'assert entry\\["version"\\] == "[0-9]+\\.[0-9]+\\.[0-9]+"',
            "tests/test_presets.py",
            "tests/contracts/speckit-cross-agent-subagents.md",
            "ZipInfo",
            "1980, 1, 1",
            "github.ref_type == 'tag' || (github.event_name == 'workflow_dispatch' && env.CREATE_INTEGRATION_PR == 'true')",
            "env.CREATE_INTEGRATION_PR == 'true'",
            "refs/tags/v${VERSION}",
            "^[0-9]+\\.[0-9]+\\.[0-9]+$",
            "persist-credentials: false",
            "git rev-parse HEAD",
            "refs/tags/v${VERSION}^{}",
            "SPEC_KIT_FORK_PR_TOKEN is required when integration PR creation is requested.",
            "exit 1",
        ]
        for term in required_terms:
            self.assertIn(term, workflow_text)
        forbidden_terms = [
            "specify preset resolve workflow-preset plan-template",
            "specify preset resolve workflow-preset speckit.implement",
            "client_payload[version]",
            "client_payload[download_url]",
            "repository_dispatch",
            "repos/bigsmartben/spec-kit/dispatches",
            "::warning::SPEC_KIT_FORK_DISPATCH_TOKEN",
            "skipping integration PR",
        ]
        for term in forbidden_terms:
            self.assertNotIn(term, workflow_text)
        self.assertNotIn("github/spec-kit", workflow_text)


if __name__ == "__main__":
    unittest.main()
