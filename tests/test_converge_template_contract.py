"""Regression contract for auditable ``/speckit.converge`` outcomes (#3752)."""

from pathlib import Path


REPO_ROOT = Path(__file__).parent.parent
CONVERGE_TEMPLATE = REPO_ROOT / "templates" / "commands" / "converge.md"


def _template() -> str:
    return CONVERGE_TEMPLATE.read_text(encoding="utf-8")


def test_converge_counts_each_acceptance_scenario_independently():
    content = _template()

    assert "user-story acceptance scenario (e.g. `US1/AC2`)" in content
    assert "each `USn/ACn` key is counted independently" in content
    assert "A user story is **not** assessed on behalf" in content
    assert "derive `US<story-position>/AC<scenario-position>`" in content
    assert "derive a stable ordinal key from its" in content


def test_converge_reports_artifact_derived_coverage_denominators():
    content = _template()

    for metric in (
        "Buildable FRs checked: `<checked>/<total>`",
        "Buildable SCs checked: `<checked>/<total>`",
        "Acceptance scenarios checked: `<checked>/<total>`",
        "Plan decisions checked: `<checked>/<total>`",
        "Constitution MUST principles checked: `<checked>/<total>`",
    ):
        assert metric in content

    assert "does not block convergence. Do not derive" in content
    assert "denominator from model memory." in content


def test_converge_emits_a_stable_key_inventory_ledger():
    content = _template()

    assert "**Intent inventory ledger:** emit every applicable stable key" in content
    assert "US1/AC1 ✓, US1/AC2 F2, US3/AC4 unassessed" in content
    assert "do not replace acceptance-scenario keys with a user-story total" in content


def test_converged_is_blocked_by_incomplete_assessment():
    content = _template()

    incomplete = content.index("`incomplete_assessment` outcome")
    tasks_appended = content.index("`tasks_appended` outcome")
    converged = content.index("`converged` outcome")

    assert incomplete < tasks_appended < converged
    assert "any coverage numerator is below its denominator" in content
    assert "Do **not** modify `tasks.md` at all — no Convergence phase" in content
    assert "All applicable coverage metrics are `total/total`" in content


def test_converge_documents_all_outcomes_for_handoff_and_hooks():
    content = _template()

    assert "- On `incomplete_assessment`:" in content
    assert "(`incomplete_assessment`, `converged`, or `tasks_appended`)" in content
