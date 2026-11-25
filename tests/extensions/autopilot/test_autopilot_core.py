"""Unit tests for the autopilot's deterministic core (no git, no agents)."""

from __future__ import annotations

import json

import pytest
import yaml

from tests.extensions.autopilot.helpers import EXT_DIR, SPEC_TEMPLATE

from autopilot_core import config as config_mod
from autopilot_core import dag
from autopilot_core import spec as spec_mod


# ── config ───────────────────────────────────────────────────────────────────


def test_template_parses_identically_with_pyyaml_and_subset_reader():
    text = (EXT_DIR / "config-template.yml").read_text(encoding="utf-8")
    assert config_mod.parse_yaml_subset(text) == yaml.safe_load(text)


def test_template_covers_every_default_key():
    data = yaml.safe_load((EXT_DIR / "config-template.yml").read_text(encoding="utf-8"))

    def keys(mapping, prefix=""):
        out = set()
        for key, value in mapping.items():
            out.add(prefix + key)
            if isinstance(value, dict):
                out |= keys(value, prefix + key + ".")
        return out

    assert keys(data) == keys(config_mod.DEFAULTS)


def test_subset_reader_handles_lists_of_mappings_and_quotes():
    text = """
gate:
  checks:
    - name: test
      run: "pytest -q  # not a comment"
    - name: lint
      run: 'ruff check .'
  require_review: false
run:
  sync_paths: [".specify", '.claude']
  max_parallel: 3
"""
    assert config_mod.parse_yaml_subset(text) == {
        "gate": {
            "checks": [
                {"name": "test", "run": "pytest -q  # not a comment"},
                {"name": "lint", "run": "ruff check ."},
            ],
            "require_review": False,
        },
        "run": {"sync_paths": [".specify", ".claude"], "max_parallel": 3},
    }


def test_load_config_merges_over_defaults(tmp_path):
    path = tmp_path / "c.yml"
    path.write_text("pipe:\n  max_iterations: 9\n", encoding="utf-8")
    config = config_mod.load_config(tmp_path, path)
    assert config["pipe"]["max_iterations"] == 9
    assert config["pipe"]["stuck_after"] == config_mod.DEFAULTS["pipe"]["stuck_after"]
    assert config_mod.configured_checks(config) == []


@pytest.mark.parametrize(
    "text",
    [
        "pipe:\n  max_iterations: 0\n",
        "pipe:\n  max_iterations: true\n",
        "gate:\n  checks:\n    - run: pytest\n",
        "gate:\n  checks: pytest\n",
    ],
)
def test_load_config_rejects_bad_values(tmp_path, text):
    path = tmp_path / "c.yml"
    path.write_text(text, encoding="utf-8")
    with pytest.raises(config_mod.ConfigError):
        config_mod.load_config(tmp_path, path)


def test_configured_checks_skips_empty_commands():
    config = json.loads(json.dumps(config_mod.DEFAULTS))
    config["gate"]["checks"] = [{"name": "test", "run": "pytest"}, {"name": "lint", "run": "  "}]
    assert config_mod.configured_checks(config) == [{"name": "test", "run": "pytest"}]


# ── spec parsing ─────────────────────────────────────────────────────────────


def test_parse_scenarios_assigns_story_scoped_ids():
    scenarios = spec_mod.parse_scenarios(SPEC_TEMPLATE, "003")
    assert [s.tag for s in scenarios] == ["003-US1-AS1", "003-US1-AS2", "003-US2-AS1"]
    assert scenarios[1].text.endswith("the CSV has a header only")


@pytest.mark.parametrize(
    "text, matches",
    [
        ("def test_003_us1_as2_header_only():", True),
        ("// 003-US1-AS2 header only", True),
        ("it('003-us1-as2', ...)", True),
        ("003-US1-AS20", False),
        ("1003-US1-AS2", False),
        ("003-US1-AS1", False),
    ],
)
def test_scenario_pattern(text, matches):
    scenario = spec_mod.Scenario("003-US1-AS2", 1, 2, "")
    assert bool(scenario.pattern().search(text)) is matches


@pytest.mark.parametrize(
    "name, number",
    [("003-user-auth", "003"), ("20261124-101500-auth", "20261124-101500"), ("auth", "F")],
)
def test_feature_number(tmp_path, name, number):
    assert spec_mod.feature_number(tmp_path / name) == number


def test_resolve_feature_dir_prefers_env(tmp_path, monkeypatch):
    (tmp_path / ".specify").mkdir()
    (tmp_path / ".specify" / "feature.json").write_text('{"feature_directory": "specs/001-a"}', encoding="utf-8")
    monkeypatch.delenv("SPECIFY_FEATURE_DIRECTORY", raising=False)
    assert spec_mod.resolve_feature_dir(tmp_path) == tmp_path / "specs" / "001-a"
    monkeypatch.setenv("SPECIFY_FEATURE_DIRECTORY", "specs/002-b")
    assert spec_mod.resolve_feature_dir(tmp_path) == tmp_path / "specs" / "002-b"


def test_resolve_feature_dir_errors_without_any_source(tmp_path, monkeypatch):
    monkeypatch.delenv("SPECIFY_FEATURE_DIRECTORY", raising=False)
    with pytest.raises(spec_mod.FeatureError):
        spec_mod.resolve_feature_dir(tmp_path)


def test_append_task_phase_is_append_only_and_numbers_forward(tmp_path):
    tasks = tmp_path / "tasks.md"
    original = "# Tasks\n\n## Phase 1: Setup\n\n- [x] T001 Init\n- [ ] T002 Build\n\n## Phase 2: Convergence\n\n- [X] T010 Gap\n"
    tasks.write_text(original, encoding="utf-8")
    ids = spec_mod.append_task_phase(tasks, "Autopilot Remediation (iteration 1, gate)", ["Fix  lint\nerrors", "Add test"])
    text = tasks.read_text(encoding="utf-8")
    assert text.startswith(original)
    assert ids == ["T011", "T012"]
    assert "## Phase 3: Autopilot Remediation (iteration 1, gate)" in text
    assert "- [ ] T011 [AP] Fix lint errors" in text
    assert spec_mod.open_tasks(text) == ["T002 Build", "T011 [AP] Fix lint errors", "T012 [AP] Add test"]


def test_append_task_phase_writes_nothing_for_no_items(tmp_path):
    tasks = tmp_path / "tasks.md"
    tasks.write_text("- [x] T001 a\n", encoding="utf-8")
    assert spec_mod.append_task_phase(tasks, "x", []) == []
    assert tasks.read_text(encoding="utf-8") == "- [x] T001 a\n"


# ── DAG ──────────────────────────────────────────────────────────────────────


def _epic(epic_id, slug, depends_on=(), touches=("src/" + "x/**",)):
    return {
        "id": epic_id,
        "slug": slug,
        "title": slug.title(),
        "acceptance": ["works"],
        "depends_on": list(depends_on),
        "touches": list(touches),
    }


def test_parse_plan_accepts_valid_plan():
    epics = dag.parse_plan({"epics": [_epic("E1", "a", touches=["a/**"]), _epic("E2", "b", ["E1"], ["b/**"])]})
    assert [e.id for e in epics] == ["E1", "E2"]
    assert "Acceptance criteria" in epics[0].brief()


@pytest.mark.parametrize(
    "epics, problem",
    [
        ([], "no epics"),
        ([_epic("E1", "a"), _epic("E1", "b")], "duplicate id"),
        ([_epic("E1", "a"), _epic("E2", "a")], "duplicate slug"),
        ([_epic("E1", "Bad_Slug")], "kebab-case"),
        ([_epic("E1", "a", ["E9"])], "unknown dependency"),
        ([_epic("E1", "a", ["E1"])], "depends on itself"),
        ([{**_epic("E1", "a"), "acceptance": []}], "acceptance"),
        ([_epic("E1", "a", ["E2"]), _epic("E2", "b", ["E1"])], "cycle"),
    ],
)
def test_parse_plan_rejects_invalid_plans(epics, problem):
    with pytest.raises(dag.PlanError) as excinfo:
        dag.parse_plan({"epics": epics})
    assert problem in str(excinfo.value)


@pytest.mark.parametrize(
    "left, right, overlap",
    [
        ("src/auth/**", "src/billing/**", False),
        ("src/**", "src/auth/login.py", True),
        ("src/auth/a.py", "src/auth/b.py", False),
        ("src/auth", "src/auth/a.py", True),
        ("**/*.md", "src/x.py", True),
        ("tests/auth/**", "src/auth/**", False),
        ("src/a*/x.py", "src/b/x.py", True),
    ],
)
def test_globs_may_overlap(left, right, overlap):
    assert dag.globs_may_overlap(left, right) is overlap
    assert dag.globs_may_overlap(right, left) is overlap


def test_serialise_overlaps_adds_dependency_to_later_epic_only_when_independent():
    epics = dag.parse_plan(
        {
            "epics": [
                _epic("E1", "core", touches=["src/**"]),
                _epic("E2", "auth", touches=["src/auth/**"]),
                _epic("E3", "docs", touches=["docs/**"]),
                _epic("E4", "api", ["E1"], ["src/api/**"]),
            ]
        }
    )
    notes = dag.serialise_overlaps(epics)
    by_id = {e.id: e for e in epics}
    assert by_id["E2"].depends_on == ["E1"] and by_id["E2"].added_dependencies == ["E1"]
    assert by_id["E3"].depends_on == []
    assert by_id["E4"].depends_on == ["E1"] and by_id["E4"].added_dependencies == []
    assert len(notes) == 1 and "E2 now depends on E1" in notes[0]


def test_epic_without_touches_is_serialised():
    epics = dag.parse_plan({"epics": [_epic("E1", "a", touches=["a/**"]), _epic("E2", "b", touches=[])]})
    dag.serialise_overlaps(epics)
    assert epics[1].depends_on == ["E1"]


def test_waves_and_feature_numbers(tmp_path):
    (tmp_path / "specs" / "004-old").mkdir(parents=True)
    epics = dag.parse_plan(
        {
            "epics": [
                _epic("E3", "c", ["E1", "E2"], ["c/**"]),
                _epic("E1", "a", touches=["a/**"]),
                _epic("E2", "b", touches=["b/**"]),
            ]
        }
    )
    assert dag.waves(epics) == [["E1", "E2"], ["E3"]]
    assert dag.assign_feature_dirs(epics, tmp_path / "specs") == {
        "E1": "specs/005-a",
        "E2": "specs/006-b",
        "E3": "specs/007-c",
    }
