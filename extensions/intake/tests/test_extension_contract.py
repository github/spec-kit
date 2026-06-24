import os
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "scripts" / "python" / "validate_visual_design_intake.py"
PRD_VALIDATOR = ROOT / "scripts" / "python" / "validate_prd_intake.py"
TEST_CASE_VALIDATOR = ROOT / "scripts" / "python" / "validate_test_cases_intake.py"


def write_visual_intake_fixture(intake: Path, source_type: str, fidelity: str, file_name: str):
    intake.mkdir(parents=True, exist_ok=True)
    source_dir = intake / "source-files"
    source_dir.mkdir()
    source = source_dir / file_name
    source.write_bytes(f"{source_type}:{fidelity}:source".encode("utf-8"))

    import hashlib

    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    rel_source = f"source-files/{file_name}"
    if source_type == "image":
        source_details = [
            "source_details:",
            "  image_dimensions:",
            "    width_px: 100",
            "    height_px: 100",
            "  region_coverage: full",
            "  ocr_status: not_applicable",
        ]
    elif source_type == "pdf":
        source_details = [
            "source_details:",
            "  page_count: 1",
            "  processed_page_count: 1",
            "  rendered_page_refs:",
            f"    - {rel_source}#page=1",
            "  text_extraction_status: complete",
        ]
    elif source_type == "markdown":
        source_details = [
            "source_details:",
            "  heading_structure:",
            "    - Design brief",
            "  embedded_or_linked_asset_refs: []",
            "  design_note_parsing_status: complete",
        ]
    elif source_type == "figma":
        source_details = [
            "source_details:",
            "  file_url: https://www.figma.com/file/example",
            "  file_key: example",
            "  selected_node_ids:",
            "    - '1'",
        ]
    else:
        source_details = []

    (intake / "design-source-manifest.yaml").write_text(
        "\n".join(
            [
                f"source_type: {source_type}",
                f"required_fidelity: {fidelity}",
                "source_integrity_complete: true",
                "captured_at: '2026-06-23T00:00:00Z'",
                "capture_method: local_fixture",
                "page_or_frame_count: 1",
                "processed_count: 1",
                "extraction_scope: full",
                "source_files:",
                f"  - path: {rel_source}",
                "    mime_type: application/octet-stream",
                f"    byte_size: {source.stat().st_size}",
                f"    sha256: {digest}",
                "    role: original",
                *source_details,
                "",
            ]
        ),
        encoding="utf-8",
    )

    (intake / "visual-requirements.yaml").write_text(
        "\n".join(
            [
                "visual_requirements_complete: true",
                "visual_requirements_count: 1",
                "source_refs_complete: true",
                "fidelity_rules_applied: true",
                "visual_parity_plan_complete: true",
                "blocker_lint_errors: []",
                "parity_plan:",
                "  comparison_targets:",
                "    - primary_surface",
                f"  original_refs: ['{rel_source}#full']",
                "  comparison_method: manual_review",
                "  thresholds:",
                "    manual_review_checklist:",
                "      - compare primary hierarchy",
                "  accepted_exceptions: []",
                "  blocking_difference_categories:",
                "    - missing_required_visual_fact",
                "requirements:",
                "  - id: VR-001",
                "    category: layout",
                "    requirement: Preserve primary content hierarchy",
                f"    source_refs: ['{rel_source}#full']",
                "    evidence_type: observed",
                "    confidence: high",
                "    confidence_rationale: Source artifact directly shows the primary hierarchy.",
                "    engineering_action: Implement matching hierarchy",
                "    acceptance_check: Compare implementation screenshot with source",
                f"    fidelity_level: {fidelity}",
                "",
            ]
        ),
        encoding="utf-8",
    )

    (intake / "visual-evidence-packet.md").write_text(
        "---\n"
        "ready_gate: PASS\n"
        "blockers: []\n"
        "source_ref_count: 1\n"
        "extracted_item_count: 1\n"
        "generated_at: '2026-06-23T00:00:00Z'\n"
        "---\n"
        "# Visual Design Evidence Packet\n",
        encoding="utf-8",
    )


def write_prd_intake_fixture(intake: Path):
    intake.mkdir(parents=True, exist_ok=True)
    source_dir = intake / "source-files"
    source_dir.mkdir()
    source = source_dir / "feature-prd.md"
    source.write_text("# Feature PRD\n\nUsers can save draft content.\n", encoding="utf-8")

    import hashlib

    digest = hashlib.sha256(source.read_bytes()).hexdigest()

    (intake / "source-manifest.yaml").write_text(
        "\n".join(
            [
                "source_type: markdown",
                "source_integrity_complete: true",
                "captured_at: '2026-06-23T00:00:00Z'",
                "capture_method: local_fixture",
                "document_version: fixture-v1",
                "extraction_scope: full",
                "source_files:",
                "  - path: source-files/feature-prd.md",
                "    mime_type: text/markdown",
                f"    byte_size: {source.stat().st_size}",
                f"    sha256: {digest}",
                "    role: original",
                "source_details:",
                "  heading_coverage: full",
                "  parsed_section_coverage: full",
                "  linked_asset_refs: []",
                "",
            ]
        ),
        encoding="utf-8",
    )

    (intake / "prd-intake.yaml").write_text(
        "\n".join(
            [
                "prd_intake_complete: true",
                "source_refs_complete: true",
                "extracted_fact_count: 1",
                "acceptance_evidence_complete: true",
                "unresolved_ambiguity_marked: true",
                "acceptance_gaps: []",
                "open_questions:",
                "  - '[NEEDS CLARIFICATION] Pricing rules are outside this fixture.'",
                "blocker_lint_errors: []",
                "facts:",
                "  - id: PI-001",
                "    category: acceptance",
                "    statement: Users can save draft content.",
                "    source_refs: ['source-files/feature-prd.md#L3']",
                "    evidence_type: observed",
                "    confidence: high",
                "    confidence_rationale: Source statement directly describes the accepted behavior.",
                "    downstream_hint: candidate_acceptance_input",
                "    acceptance_or_validation_signal: Draft save behavior is explicitly stated.",
                "",
            ]
        ),
        encoding="utf-8",
    )

    (intake / "evidence-packet.md").write_text(
        "---\n"
        "ready_gate: PASS\n"
        "blockers: []\n"
        "source_ref_count: 1\n"
        "extracted_item_count: 1\n"
        "generated_at: '2026-06-23T00:00:00Z'\n"
        "---\n"
        "# PRD Evidence Packet\n",
        encoding="utf-8",
    )


def write_test_case_intake_fixture(intake: Path):
    intake.mkdir(parents=True, exist_ok=True)
    source_dir = intake / "source-files"
    source_dir.mkdir()
    source = source_dir / "test_feature.py"
    source.write_text("def test_save_draft():\n    assert True\n", encoding="utf-8")

    import hashlib

    digest = hashlib.sha256(source.read_bytes()).hexdigest()

    (intake / "source-manifest.yaml").write_text(
        "\n".join(
            [
                "source_type: code",
                "source_integrity_complete: true",
                "captured_at: '2026-06-23T00:00:00Z'",
                "capture_method: local_fixture",
                "framework_or_format: pytest",
                "execution_scope: unit",
                "source_files:",
                "  - path: source-files/test_feature.py",
                "    mime_type: text/x-python",
                f"    byte_size: {source.stat().st_size}",
                f"    sha256: {digest}",
                "    role: original",
                "source_details:",
                "  test_names:",
                "    - test_save_draft",
                "  execution_status: passed",
                "  skipped_markers: []",
                "  fixture_refs:",
                "    - local pytest fixture",
                "",
            ]
        ),
        encoding="utf-8",
    )

    (intake / "test-case-intake.yaml").write_text(
        "\n".join(
            [
                "test_case_intake_complete: true",
                "source_refs_complete: true",
                "scenario_count: 1",
                "assertions_complete: true",
                "fixture_evidence_complete: true",
                "coverage_gaps_recorded: true",
                "assertion_gaps: []",
                "fixture_or_test_data_gaps: []",
                "coverage_gaps:",
                "  - Error-state coverage is not present in the fixture.",
                "flaky_or_skipped_cases: []",
                "blocker_lint_errors: []",
                "scenarios:",
                "  - id: TC-001",
                "    category: unit",
                "    scenario: Saving draft content succeeds.",
                "    source_refs: ['source-files/test_feature.py#L1']",
                "    evidence_type: observed",
                "    confidence: high",
                "    confidence_rationale: Test source directly exercises the scenario.",
                "    actors: ['registered_user']",
                "    preconditions: ['draft content exists']",
                "    actions: ['save draft']",
                "    expected_outcomes: ['draft is persisted']",
                "    assertions: ['save path returns success']",
                "    fixtures_or_test_data: ['local pytest fixture']",
                "    coverage_signal: happy_path_present_error_path_missing",
                "",
            ]
        ),
        encoding="utf-8",
    )

    (intake / "evidence-packet.md").write_text(
        "---\n"
        "ready_gate: PASS\n"
        "blockers: []\n"
        "source_ref_count: 1\n"
        "extracted_item_count: 1\n"
        "generated_at: '2026-06-23T00:00:00Z'\n"
        "---\n"
        "# Test Case Evidence Packet\n",
        encoding="utf-8",
    )


def write_image_visual_intake_fixture(intake: Path):
    write_visual_intake_fixture(intake, "image", "low", "wireframe.png")


def test_manifest_loads_with_spec_kit_checkout():
    spec_kit_src = ROOT.parent / "spec-kit" / "src"
    if not spec_kit_src.exists():
        pytest.skip("spec-kit checkout not available next to extension")

    env = os.environ.copy()
    env["PYTHONPATH"] = str(spec_kit_src)

    code = (
        "from pathlib import Path; "
        "from specify_cli.extensions import ExtensionManifest; "
        "m=ExtensionManifest(Path('extension.yml')); "
        "assert m.id == 'intake'; "
        "assert len(m.commands) == 3; "
        "assert {c['name'] for c in m.commands} == {'speckit.intake.visual-design', 'speckit.intake.prd', 'speckit.intake.test-cases'}; "
        "assert m.hooks"
    )

    result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 0, result.stderr


def test_validator_blocks_missing_directory():
    result = subprocess.run(
        [sys.executable, str(VALIDATOR), "missing-dir"],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 1
    assert "VISUAL_SOURCE_MANIFEST_MISSING" in result.stdout
    assert "VISUAL_REQUIREMENTS_MISSING" in result.stdout
    assert "VISUAL_EVIDENCE_PACKET_MISSING" in result.stdout


def test_prd_validator_blocks_missing_directory():
    result = subprocess.run(
        [sys.executable, str(PRD_VALIDATOR), "missing-dir"],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 1
    assert "PRD_SOURCE_MANIFEST_MISSING" in result.stdout
    assert "PRD_INTAKE_MISSING" in result.stdout
    assert "PRD_EVIDENCE_PACKET_MISSING" in result.stdout


def test_test_case_validator_blocks_missing_directory():
    result = subprocess.run(
        [sys.executable, str(TEST_CASE_VALIDATOR), "missing-dir"],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 1
    assert "TEST_SOURCE_MANIFEST_MISSING" in result.stdout
    assert "TEST_CASE_INTAKE_MISSING" in result.stdout
    assert "TEST_EVIDENCE_PACKET_MISSING" in result.stdout


@pytest.mark.parametrize(
    ("source_type", "fidelity", "file_name"),
    [
        ("image", "low", "wireframe.png"),
        ("pdf", "medium", "design-pack.pdf"),
        ("markdown", "high", "design-brief.md"),
    ],
)
def test_validator_passes_visual_source_matrix(source_type, fidelity, file_name):
    work_dir = ROOT / ".tmp" / f"test-validator-{source_type}-{fidelity}"
    if work_dir.exists():
        shutil.rmtree(work_dir)
    intake = work_dir / "visual-design"
    write_visual_intake_fixture(intake, source_type, fidelity, file_name)

    result = subprocess.run(
        [sys.executable, str(VALIDATOR), str(intake)],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "Visual design intake readiness: PASS" in result.stdout

    shutil.rmtree(work_dir)


def test_prd_validator_passes_complete_minimal_intake():
    work_dir = ROOT / ".tmp" / "test-prd-validator-pass"
    if work_dir.exists():
        shutil.rmtree(work_dir)
    intake = work_dir / "prd"
    write_prd_intake_fixture(intake)

    result = subprocess.run(
        [sys.executable, str(PRD_VALIDATOR), str(intake)],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "PRD intake readiness: PASS" in result.stdout

    shutil.rmtree(work_dir)


def test_prd_validator_blocks_untraceable_facts():
    work_dir = ROOT / ".tmp" / "test-prd-validator-untraceable"
    if work_dir.exists():
        shutil.rmtree(work_dir)
    intake = work_dir / "prd"
    write_prd_intake_fixture(intake)

    text = (intake / "prd-intake.yaml").read_text(encoding="utf-8")
    text = text.replace("source_refs_complete: true", "source_refs_complete: false")
    text = text.replace("source_refs: ['source-files/feature-prd.md#L3']", "source_refs: []")
    (intake / "prd-intake.yaml").write_text(text, encoding="utf-8")

    result = subprocess.run(
        [sys.executable, str(PRD_VALIDATOR), "--json", str(intake)],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )

    payload = json.loads(result.stdout)
    assert result.returncode == 1
    assert "PRD_FACTS_UNTRACEABLE" in payload["blockers"]
    assert "PRD_READY_WITHOUT_EVIDENCE" in payload["blockers"]
    assert "PRD_SCHEMA_INVALID" in payload["blockers"]
    assert payload["details"]["schema_validation"]["prd_intake"]["valid"] is False

    shutil.rmtree(work_dir)


def test_prd_validator_blocks_invalid_confidence_enum():
    work_dir = ROOT / ".tmp" / "test-prd-validator-confidence"
    if work_dir.exists():
        shutil.rmtree(work_dir)
    intake = work_dir / "prd"
    write_prd_intake_fixture(intake)

    text = (intake / "prd-intake.yaml").read_text(encoding="utf-8")
    text = text.replace("    confidence: high", "    confidence: certain")
    (intake / "prd-intake.yaml").write_text(text, encoding="utf-8")

    result = subprocess.run(
        [sys.executable, str(PRD_VALIDATOR), "--json", str(intake)],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )

    payload = json.loads(result.stdout)
    assert result.returncode == 1
    assert "PRD_SCHEMA_INVALID" in payload["blockers"]
    assert payload["details"]["schema_validation"]["prd_intake"]["valid"] is False

    shutil.rmtree(work_dir)


@pytest.mark.parametrize(
    (
        "kind",
        "writer",
        "validator",
        "artifact",
        "rationale_line",
        "schema_blocker",
    ),
    [
        (
            "prd",
            write_prd_intake_fixture,
            PRD_VALIDATOR,
            "prd-intake.yaml",
            "    confidence_rationale: Source statement directly describes the accepted behavior.\n",
            "PRD_SCHEMA_INVALID",
        ),
        (
            "test-case",
            write_test_case_intake_fixture,
            TEST_CASE_VALIDATOR,
            "test-case-intake.yaml",
            "    confidence_rationale: Test source directly exercises the scenario.\n",
            "TEST_SCHEMA_INVALID",
        ),
        (
            "visual",
            write_image_visual_intake_fixture,
            VALIDATOR,
            "visual-requirements.yaml",
            "    confidence_rationale: Source artifact directly shows the primary hierarchy.\n",
            "VISUAL_SCHEMA_INVALID",
        ),
    ],
)
def test_validators_require_confidence_rationale(
    kind,
    writer,
    validator,
    artifact,
    rationale_line,
    schema_blocker,
):
    work_dir = ROOT / ".tmp" / f"test-{kind}-validator-missing-confidence-rationale"
    if work_dir.exists():
        shutil.rmtree(work_dir)
    intake = work_dir / kind
    writer(intake)

    path = intake / artifact
    text = path.read_text(encoding="utf-8")
    text = text.replace(rationale_line, "")
    path.write_text(text, encoding="utf-8")

    result = subprocess.run(
        [sys.executable, str(validator), "--json", str(intake)],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )

    payload = json.loads(result.stdout)
    assert result.returncode == 1
    assert schema_blocker in payload["blockers"]

    shutil.rmtree(work_dir)


@pytest.mark.parametrize(
    (
        "kind",
        "writer",
        "validator",
        "artifact",
        "count_line",
        "blocker",
        "detail_key",
        "match_key",
    ),
    [
        (
            "prd",
            write_prd_intake_fixture,
            PRD_VALIDATOR,
            "prd-intake.yaml",
            "extracted_fact_count: 1",
            "PRD_INTAKE_MISSING",
            "prd_intake",
            "count_matches_facts",
        ),
        (
            "test-case",
            write_test_case_intake_fixture,
            TEST_CASE_VALIDATOR,
            "test-case-intake.yaml",
            "scenario_count: 1",
            "TEST_CASE_INTAKE_MISSING",
            "test_case_intake",
            "count_matches_scenarios",
        ),
        (
            "visual",
            write_image_visual_intake_fixture,
            VALIDATOR,
            "visual-requirements.yaml",
            "visual_requirements_count: 1",
            "VISUAL_REQUIREMENTS_MISSING",
            "visual_requirements",
            "count_matches_requirements",
        ),
    ],
)
def test_validators_block_declared_count_mismatch(
    kind,
    writer,
    validator,
    artifact,
    count_line,
    blocker,
    detail_key,
    match_key,
):
    work_dir = ROOT / ".tmp" / f"test-{kind}-validator-count-mismatch"
    if work_dir.exists():
        shutil.rmtree(work_dir)
    intake = work_dir / kind
    writer(intake)

    path = intake / artifact
    text = path.read_text(encoding="utf-8")
    text = text.replace(count_line, count_line.replace(": 1", ": 2"))
    path.write_text(text, encoding="utf-8")

    result = subprocess.run(
        [sys.executable, str(validator), "--json", str(intake)],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )

    payload = json.loads(result.stdout)
    assert result.returncode == 1
    assert blocker in payload["blockers"]
    assert payload["details"][detail_key][match_key] is False

    shutil.rmtree(work_dir)


def test_prd_validator_blocks_incomplete_evidence_front_matter():
    work_dir = ROOT / ".tmp" / "test-prd-validator-front-matter"
    if work_dir.exists():
        shutil.rmtree(work_dir)
    intake = work_dir / "prd"
    write_prd_intake_fixture(intake)

    (intake / "evidence-packet.md").write_text(
        "---\nready_gate: PASS\n---\n# PRD Evidence Packet\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, str(PRD_VALIDATOR), "--json", str(intake)],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )

    payload = json.loads(result.stdout)
    assert result.returncode == 1
    assert "PRD_READY_WITHOUT_EVIDENCE" in payload["blockers"]

    shutil.rmtree(work_dir)


@pytest.mark.parametrize(
    ("kind", "writer", "validator", "packet_name", "ready_blocker"),
    [
        ("prd", write_prd_intake_fixture, PRD_VALIDATOR, "evidence-packet.md", "PRD_READY_WITHOUT_EVIDENCE"),
        (
            "test-case",
            write_test_case_intake_fixture,
            TEST_CASE_VALIDATOR,
            "evidence-packet.md",
            "TEST_READY_WITHOUT_EVIDENCE",
        ),
        (
            "visual",
            write_image_visual_intake_fixture,
            VALIDATOR,
            "visual-evidence-packet.md",
            "VISUAL_READY_WITHOUT_EVIDENCE",
        ),
    ],
)
def test_validators_block_blocked_evidence_packet(
    kind,
    writer,
    validator,
    packet_name,
    ready_blocker,
):
    work_dir = ROOT / ".tmp" / f"test-{kind}-validator-blocked-packet"
    if work_dir.exists():
        shutil.rmtree(work_dir)
    intake = work_dir / kind
    writer(intake)

    packet = intake / packet_name
    text = packet.read_text(encoding="utf-8")
    text = text.replace("ready_gate: PASS", "ready_gate: BLOCKED")
    packet.write_text(text, encoding="utf-8")

    result = subprocess.run(
        [sys.executable, str(validator), "--json", str(intake)],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )

    payload = json.loads(result.stdout)
    assert result.returncode == 1
    assert ready_blocker in payload["blockers"]

    shutil.rmtree(work_dir)


def test_test_case_validator_passes_complete_minimal_intake():
    work_dir = ROOT / ".tmp" / "test-case-validator-pass"
    if work_dir.exists():
        shutil.rmtree(work_dir)
    intake = work_dir / "test-cases"
    write_test_case_intake_fixture(intake)

    result = subprocess.run(
        [sys.executable, str(TEST_CASE_VALIDATOR), str(intake)],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "Test-case intake readiness: PASS" in result.stdout

    shutil.rmtree(work_dir)


def test_test_case_validator_blocks_missing_assertions_and_coverage():
    work_dir = ROOT / ".tmp" / "test-case-validator-missing-assertions"
    if work_dir.exists():
        shutil.rmtree(work_dir)
    intake = work_dir / "test-cases"
    write_test_case_intake_fixture(intake)

    text = (intake / "test-case-intake.yaml").read_text(encoding="utf-8")
    text = text.replace("assertions_complete: true", "assertions_complete: false")
    text = text.replace("coverage_gaps_recorded: true", "coverage_gaps_recorded: false")
    text = text.replace("    assertions: ['save path returns success']", "    assertions: []")
    text = text.replace("coverage_gaps:\n  - Error-state coverage is not present in the fixture.\n", "coverage_gaps: []\n")
    text = text.replace("    coverage_signal: happy_path_present_error_path_missing", "    coverage_signal: ''")
    (intake / "test-case-intake.yaml").write_text(text, encoding="utf-8")

    result = subprocess.run(
        [sys.executable, str(TEST_CASE_VALIDATOR), str(intake)],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 1
    assert "TEST_ASSERTIONS_MISSING" in result.stdout
    assert "TEST_COVERAGE_GAPS_MISSING" in result.stdout
    assert "TEST_READY_WITHOUT_EVIDENCE" in result.stdout

    shutil.rmtree(work_dir)


def test_test_case_validator_reports_schema_errors_in_json():
    work_dir = ROOT / ".tmp" / "test-case-validator-schema-error"
    if work_dir.exists():
        shutil.rmtree(work_dir)
    intake = work_dir / "test-cases"
    write_test_case_intake_fixture(intake)

    text = (intake / "test-case-intake.yaml").read_text(encoding="utf-8")
    text = text.replace("    category: unit", "    category: smoke")
    (intake / "test-case-intake.yaml").write_text(text, encoding="utf-8")

    result = subprocess.run(
        [sys.executable, str(TEST_CASE_VALIDATOR), "--json", str(intake)],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )

    payload = json.loads(result.stdout)
    assert result.returncode == 1
    assert "TEST_SCHEMA_INVALID" in payload["blockers"]
    assert "TEST_READY_WITHOUT_EVIDENCE" in payload["blockers"]
    assert payload["details"]["schema_validation"]["test_case_intake"]["valid"] is False

    shutil.rmtree(work_dir)


def test_visual_validator_blocks_missing_source_type_details():
    work_dir = ROOT / ".tmp" / "test-validator-missing-source-details"
    if work_dir.exists():
        shutil.rmtree(work_dir)
    intake = work_dir / "visual-design"
    write_visual_intake_fixture(intake, "image", "low", "wireframe.png")

    text = (intake / "design-source-manifest.yaml").read_text(encoding="utf-8")
    text = text.split("source_details:", 1)[0]
    (intake / "design-source-manifest.yaml").write_text(text, encoding="utf-8")

    result = subprocess.run(
        [sys.executable, str(VALIDATOR), "--json", str(intake)],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )

    payload = json.loads(result.stdout)
    assert result.returncode == 1
    assert "VISUAL_SCHEMA_INVALID" in payload["blockers"]
    assert payload["details"]["schema_validation"]["visual_source_manifest"]["valid"] is False

    shutil.rmtree(work_dir)


def test_validator_blocks_unsupported_visual_source_type():
    work_dir = ROOT / ".tmp" / "test-validator-unsupported-source"
    if work_dir.exists():
        shutil.rmtree(work_dir)
    intake = work_dir / "visual-design"
    write_visual_intake_fixture(intake, "sketch", "high", "design.sketch")

    result = subprocess.run(
        [sys.executable, str(VALIDATOR), str(intake)],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 1
    assert "VISUAL_SOURCE_TYPE_UNSUPPORTED" in result.stdout
    assert "VISUAL_SCHEMA_INVALID" in result.stdout
    assert "VISUAL_READY_WITHOUT_EVIDENCE" in result.stdout

    shutil.rmtree(work_dir)


def test_validator_passes_complete_minimal_figma_intake():
    work_dir = ROOT / ".tmp" / "test-validator-pass"
    if work_dir.exists():
        shutil.rmtree(work_dir)
    intake = work_dir / "visual-design"
    write_visual_intake_fixture(intake, "figma", "high", "figma-source.txt")

    metadata = intake / "figma-metadata.part-001.xml"
    metadata.write_text("<figma><node id=\"1\" name=\"Root\" /></figma>\n", encoding="utf-8")

    import hashlib

    digest = hashlib.sha256(metadata.read_bytes()).hexdigest()

    (intake / "figma-metadata.index.yaml").write_text(
        "\n".join(
            [
                "file_url: https://www.figma.com/file/example",
                "file_key: example",
                "page_id: page-1",
                "selected_node_ids:",
                "  - '1'",
                "captured_at: '2026-06-22T00:00:00Z'",
                "mcp_tool: get_metadata",
                "design_version_or_timestamp: '2026-06-22T00:00:00Z'",
                "selected_subtree_complete: true",
                "raw_metadata_complete: true",
                "expected_root_node_ids:",
                "  - '1'",
                "captured_root_node_ids:",
                "  - '1'",
                "missing_root_node_ids: []",
                "gap_count: 0",
                "gaps: []",
                "shards:",
                "  - path: figma-metadata.part-001.xml",
                f"    byte_size: {metadata.stat().st_size}",
                f"    sha256: {digest}",
                "    root_node_ids:",
                "      - '1'",
                "    node_count: 1",
                "    truncated: false",
                "",
            ]
        ),
        encoding="utf-8",
    )

    (intake / "figma-node-inventory.yaml").write_text(
        "\n".join(
            [
                "raw_node_count: 1",
                "inventory_node_count: 1",
                "excluded_node_count: 0",
                "missing_node_count: 0",
                "duplicate_node_count: 0",
                "truncated_raw_evidence: false",
                "node_inventory_coverage: 100%",
                "parity_passed: true",
                "",
            ]
        ),
        encoding="utf-8",
    )
    result = subprocess.run(
        [sys.executable, str(VALIDATOR), str(intake)],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "Visual design intake readiness: PASS" in result.stdout

    shutil.rmtree(work_dir)


def test_validator_blocks_legacy_figma_only_without_manifest():
    work_dir = ROOT / ".tmp" / "test-validator-legacy-figma"
    if work_dir.exists():
        shutil.rmtree(work_dir)
    intake = work_dir / "visual-design"
    intake.mkdir(parents=True)

    metadata = intake / "figma-metadata.part-001.xml"
    metadata.write_text("<figma><node id=\"1\" name=\"Root\" /></figma>\n", encoding="utf-8")

    import hashlib

    digest = hashlib.sha256(metadata.read_bytes()).hexdigest()

    (intake / "figma-metadata.index.yaml").write_text(
        "\n".join(
            [
                "file_url: https://www.figma.com/file/example",
                "file_key: example",
                "page_id: page-1",
                "selected_node_ids:",
                "  - '1'",
                "captured_at: '2026-06-22T00:00:00Z'",
                "mcp_tool: get_metadata",
                "design_version_or_timestamp: '2026-06-22T00:00:00Z'",
                "selected_subtree_complete: true",
                "raw_metadata_complete: true",
                "expected_root_node_ids:",
                "  - '1'",
                "captured_root_node_ids:",
                "  - '1'",
                "missing_root_node_ids: []",
                "gap_count: 0",
                "gaps: []",
                "shards:",
                "  - path: figma-metadata.part-001.xml",
                f"    byte_size: {metadata.stat().st_size}",
                f"    sha256: {digest}",
                "    root_node_ids:",
                "      - '1'",
                "    node_count: 1",
                "    truncated: false",
                "",
            ]
        ),
        encoding="utf-8",
    )

    (intake / "figma-node-inventory.yaml").write_text(
        "\n".join(
            [
                "raw_node_count: 1",
                "inventory_node_count: 1",
                "excluded_node_count: 0",
                "missing_node_count: 0",
                "duplicate_node_count: 0",
                "truncated_raw_evidence: false",
                "node_inventory_coverage: 100%",
                "parity_passed: true",
                "",
            ]
        ),
        encoding="utf-8",
    )

    (intake / "figma-evidence-packet.md").write_text(
        "# Figma Evidence Packet\n\n- ready_gate: PASS\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, str(VALIDATOR), str(intake)],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 1
    assert "VISUAL_SOURCE_MANIFEST_MISSING" in result.stdout
    assert "FIGMA_READY_WITHOUT_COMPLETENESS_PROOF" in result.stdout

    shutil.rmtree(work_dir)
