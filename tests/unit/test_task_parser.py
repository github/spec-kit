import importlib.util
from pathlib import Path
import textwrap

import pytest


def load_task_parser():
    repo_root = Path(__file__).resolve().parents[2]
    module_path = repo_root / ".specify" / "lib" / "task_parser.py"
    spec = importlib.util.spec_from_file_location("task_parser", module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_phase_header_extraction():
    task_parser = load_task_parser()
    header = "## Phase 1: Setup (Shared Infrastructure)"
    assert task_parser.parse_phase_header(header) == "Setup (Shared Infrastructure)"


def test_task_line_parsing_and_dependencies(tmp_path):
    task_parser = load_task_parser()
    content = textwrap.dedent(
        """
        ## Phase 1: Setup (Shared Infrastructure)
        - [ ] T001 Create initial structure in src/main.py
        - [ ] T002 [P] [US1] Build parser in src/parser.py (depends on T001)
        """
    ).strip()
    tasks_path = tmp_path / "tasks.md"
    tasks_path.write_text(content, encoding="utf-8")

    tasks = task_parser.parse_tasks_file(tasks_path)
    assert len(tasks) == 2
    assert tasks[0].task_id == "T001"
    assert tasks[0].file_path == "src/main.py"
    assert tasks[1].task_id == "T002"
    assert tasks[1].user_story == "US1"
    assert tasks[1].dependencies == ["T001"]


def test_dependency_parsing_clean_description():
    task_parser = load_task_parser()
    deps, cleaned = task_parser.parse_dependencies(
        "Implement service (depends on T012, T013)"
    )
    assert deps == ["T012", "T013"]
    assert cleaned == "Implement service"


def test_malformed_task_line_warning(tmp_path, capsys):
    task_parser = load_task_parser()
    content = textwrap.dedent(
        """
        ## Phase 1: Setup (Shared Infrastructure)
        - [ ] T001 Valid task in src/main.py
        - [ ] Malformed task without ID
        """
    ).strip()
    tasks_path = tmp_path / "tasks.md"
    tasks_path.write_text(content, encoding="utf-8")

    tasks = task_parser.parse_tasks_file(tasks_path)
    assert len(tasks) == 1
    stderr = capsys.readouterr().err
    assert "Malformed task line" in stderr


def test_empty_tasks_file(tmp_path):
    task_parser = load_task_parser()
    tasks_path = tmp_path / "tasks.md"
    tasks_path.write_text("## Phase 1: Setup", encoding="utf-8")

    with pytest.raises(ValueError):
        task_parser.parse_tasks_file(tasks_path)


def test_circular_dependency_detection(tmp_path):
    task_parser = load_task_parser()
    content = textwrap.dedent(
        """
        ## Phase 1: Setup (Shared Infrastructure)
        - [ ] T001 Task one (depends on T002)
        - [ ] T002 Task two (depends on T001)
        """
    ).strip()
    tasks_path = tmp_path / "tasks.md"
    tasks_path.write_text(content, encoding="utf-8")

    tasks = task_parser.parse_tasks_file(tasks_path)
    cycle = task_parser.detect_circular_dependencies(tasks)
    assert cycle is not None


def test_validate_dependencies_missing_target(tmp_path):
    task_parser = load_task_parser()
    content = textwrap.dedent(
        """
        ## Phase 1: Setup (Shared Infrastructure)
        - [ ] T001 Task one (depends on T099)
        """
    ).strip()
    tasks_path = tmp_path / "tasks.md"
    tasks_path.write_text(content, encoding="utf-8")

    tasks = task_parser.parse_tasks_file(tasks_path)
    with pytest.raises(ValueError):
        task_parser.validate_dependencies(tasks)


def test_task_id_validation_errors(tmp_path):
    task_parser = load_task_parser()
    content = textwrap.dedent(
        """
        ## Phase 1: Setup (Shared Infrastructure)
        - [ ] T001 Valid task in src/main.py
        - [ ] T001 Duplicate task in src/dup.py
        """
    ).strip()
    tasks_path = tmp_path / "tasks.md"
    tasks_path.write_text(content, encoding="utf-8")

    tasks = task_parser.parse_tasks_file(tasks_path)
    with pytest.raises(ValueError):
        task_parser.validate_task_ids(tasks)
