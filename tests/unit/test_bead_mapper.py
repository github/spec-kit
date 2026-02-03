import importlib.util
from pathlib import Path


def load_task_parser():
    repo_root = Path(__file__).resolve().parents[2]
    module_path = repo_root / ".specify" / "lib" / "task_parser.py"
    spec = importlib.util.spec_from_file_location("task_parser", module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_mapping_serialization_roundtrip(tmp_path):
    task_parser = load_task_parser()
    mapping = task_parser.TaskBeadMapping(
        version=task_parser.CURRENT_MAPPING_VERSION,
        feature_dir=str(tmp_path),
        branch_name="001-feature",
        created_at="2026-02-03T00:00:00Z",
        last_updated="2026-02-03T00:00:00Z",
        mappings={
            "T001": task_parser.BeadMappingEntry(
                bead_id="bd-test1",
                created_at="2026-02-03T00:00:01Z",
                title="Test task",
                parent_bead_id="bd-parent",
            )
        },
        convoy=None,
        stats={"total_beads_created": 1},
    )
    task_parser.save_mapping(mapping, tmp_path)
    loaded = task_parser.load_mapping(tmp_path)
    assert loaded is not None
    assert loaded.mappings["T001"].bead_id == "bd-test1"


def test_duplicate_detection():
    task_parser = load_task_parser()
    mapping = task_parser.TaskBeadMapping(
        version=task_parser.CURRENT_MAPPING_VERSION,
        feature_dir="/tmp/feature",
        branch_name="branch",
        created_at="",
        last_updated="",
        mappings={"T001": task_parser.BeadMappingEntry("bd-1", "", "Task")},
        convoy=None,
        stats={},
    )
    assert task_parser.is_duplicate("T001", mapping) is True
    assert task_parser.is_duplicate("T002", mapping) is False


def test_parent_bead_determination():
    task_parser = load_task_parser()
    task = task_parser.Task(
        task_id="T001",
        is_parallel=False,
        user_story="US1",
        description="Test",
        file_path=None,
        dependencies=[],
        phase_name="User Story 1 - Example",
        phase_priority=2,
        line_number=1,
    )
    key, title = task_parser.determine_parent_bead(task)
    assert key == "us:US1"
    assert "User Story 1" in title


def test_convoy_name_fallback(tmp_path, monkeypatch):
    task_parser = load_task_parser()
    feature_dir = tmp_path / "specs" / "001-feature"
    feature_dir.mkdir(parents=True)
    (feature_dir / "spec.md").write_text("# My Feature", encoding="utf-8")

    repo_root = tmp_path
    monkeypatch.setenv("PATH", "")

    name = task_parser.get_convoy_name(repo_root, feature_dir)
    assert name == "My Feature"


def test_phase_priority_mapping(tmp_path):
    task_parser = load_task_parser()
    content = "\n".join(
        [
            "## Phase 1: Setup (Shared Infrastructure)",
            "- [ ] T001 Setup task in src/setup.py",
            "## Phase 2: Foundational (Blocking)",
            "- [ ] T002 Foundational task in src/base.py",
            "## Phase 3: User Story 1 - Example (Priority: P1)",
            "- [ ] T003 [US1] Story task in src/story.py",
        ]
    )
    tasks_path = tmp_path / "tasks.md"
    tasks_path.write_text(content, encoding="utf-8")

    tasks = task_parser.parse_tasks_file(tasks_path)
    assert tasks[0].phase_priority == 0
    assert tasks[1].phase_priority == 1
    assert tasks[2].phase_priority == 2
