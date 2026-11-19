"""Scaffold regressions for citation-first constrained-field guidance.

These checks inspect the shipped prompts, not LLM behavior. Exercise the
positive and negative artifact scenarios in fixtures/constrained-fields.md
through a coding agent for generation and analysis outcome evidence.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
TASKS_TEMPLATE = REPO_ROOT / "templates" / "commands" / "tasks.md"
ANALYZE_TEMPLATE = REPO_ROOT / "templates" / "commands" / "analyze.md"


def _section(path: Path, start: str, end: str) -> str:
    text = path.read_text(encoding="utf-8")
    return " ".join(text.split(start, 1)[1].split(end, 1)[0].split())


def test_task_generation_requires_canonical_field_citations_not_verbatim_copies():
    section = _section(
        TASKS_TEMPLATE, "**From Data Model**", "**From Setup/Infrastructure**"
    )
    for clause in (
        "data-model.md is the canonical source",
        "each constrained field",
        "`Entity.field`",
        "implementing task",
        "Do not require verbatim copies",
        "Do not restate unchanged constraints",
        "only when the task adds to or narrows the canonical rule",
        "Task-specific constraints MUST NOT contradict",
        "A field mention elsewhere in the task is not a citation",
        "constraints encoded in field types",
        "max/min length, nullable/required, enum values, validation rules",
    ):
        assert clause in section, f"Missing task-generation guidance: {clause}"
    assert "quote the constraint verbatim in the task description" not in section


def test_task_generation_checks_field_citation_completeness():
    section = _section(
        TASKS_TEMPLATE, "3. **Execute task generation workflow**", "4. **Generate tasks.md**"
    )
    assert "every constrained field has an explicit, resolving citation" in section
    assert "at least one implementing task" in section


def test_task_generation_context_includes_the_feature_design_documents():
    section = _section(
        TASKS_TEMPLATE, "Context for task generation:", "## Task Generation Rules"
    )
    assert "without context beyond the feature's design documents" in section
    assert "does not require copying those documents into task descriptions" in section


def test_analysis_loads_optional_model_and_builds_field_inventory():
    loading = _section(
        ANALYZE_TEMPLATE, "### 2. Load Artifacts", "### 4. Detection Passes"
    )
    for clause in (
        "**From data-model.md (if present):**",
        "constraints encoded in field types",
        "If absent or no constrained fields exist",
        "do not invent fields or constraints",
        "**Constrained-field inventory**",
        "**Field citation mapping**",
        "implementing task IDs",
        "exact `Entity.field`",
    ):
        assert clause in loading, f"Missing analysis inventory guidance: {clause}"


def test_analysis_distinguishes_implementation_citations_from_mentions():
    coverage = _section(
        ANALYZE_TEMPLATE, "#### E. Coverage Gaps", "#### F. Inconsistency"
    )
    for clause in (
        "explicit `data-model.md` + `Entity.field` citation",
        "Generic document/entity references, bare field names, and test-only references do not count",
        "unresolved field citations",
        "must not be guessed as aliases",
        "shared implementing task may cite multiple fields",
        "Mere co-occurrence of a document reference and a field mention is not a citation",
    ):
        assert clause in coverage, f"Missing citation coverage guidance: {clause}"


def test_analysis_compares_stated_constraints_without_requiring_copies():
    inconsistency = _section(
        ANALYZE_TEMPLATE, "#### F. Inconsistency", "### 5. Severity Assignment"
    )
    for clause in (
        "even when a valid citation is present",
        "even when its citation is missing",
        "length, nullable/required status, enum values, and validation rules",
        "canonical and task-stated restrictions",
        "Do not flag citation-only tasks or semantically matching paraphrases",
        "Do not invent canonical values",
    ):
        assert clause in inconsistency, f"Missing constraint comparison guidance: {clause}"


def test_analysis_preserves_existing_report_and_read_only_guards():
    text = " ".join(ANALYZE_TEMPLATE.read_text(encoding="utf-8").split())
    report = _section(
        ANALYZE_TEMPLATE, "### 5. Severity Assignment", "### 7. Provide Next Actions"
    )
    assert "**STRICTLY READ-ONLY**" in text
    assert "Limit to 50 findings total" in text
    for clause in (
        "missing/unresolved constrained-field citations",
        "contradictory task constraints",
        "**Constrained-Field Coverage (when applicable):**",
        "Field (`Entity.field`)",
        "Canonical Location",
        "Implementing Task IDs",
        "do not change the existing requirement coverage denominator",
        "source locations",
    ):
        assert clause in report, f"Missing field reporting guidance: {clause}"
