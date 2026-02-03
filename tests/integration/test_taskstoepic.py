import importlib.util
import os
from pathlib import Path
import textwrap


def load_task_parser():
    repo_root = Path(__file__).resolve().parents[2]
    module_path = repo_root / ".specify" / "lib" / "task_parser.py"
    spec = importlib.util.spec_from_file_location("task_parser", module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_fake_cli(bin_dir: Path, name: str, script: str) -> Path:
    path = bin_dir / name
    path.write_text(script, encoding="utf-8")
    path.chmod(0o755)
    return path


def setup_repo(tmp_path: Path):
    repo_root = tmp_path
    (repo_root / ".beads").mkdir()
    feature_dir = repo_root / "specs" / "001-feature"
    feature_dir.mkdir(parents=True)
    (feature_dir / "spec.md").write_text("# Feature One", encoding="utf-8")
    (feature_dir / "plan.md").write_text("Plan", encoding="utf-8")
    tasks_content = textwrap.dedent(
        """
        ## Phase 1: Setup (Shared Infrastructure)
        - [ ] T001 Initial setup in src/main.py
        ## Phase 3: User Story 1 - Parser (Priority: P1)
        - [ ] T002 [US1] Implement parser in src/parser.py (depends on T001)
        """
    ).strip()
    tasks_path = feature_dir / "tasks.md"
    tasks_path.write_text(tasks_content, encoding="utf-8")
    return repo_root, feature_dir, tasks_path


def test_end_to_end_with_mocked_clis(tmp_path, monkeypatch):
    task_parser = load_task_parser()
    repo_root, feature_dir, tasks_path = setup_repo(tmp_path)

    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    bd_log = tmp_path / "bd.log"
    bd_count = tmp_path / "bd.count"

    bd_script = textwrap.dedent(
        """
        #!/usr/bin/env bash
        set -e
        LOG="$BD_LOG"
        COUNT_FILE="$BD_COUNT"
        cmd="$1"
        shift
        if [[ "$cmd" == "create" ]]; then
            count=0
            if [[ -f "$COUNT_FILE" ]]; then
                count=$(cat "$COUNT_FILE")
            fi
            count=$((count + 1))
            echo "$count" > "$COUNT_FILE"
            echo "bd-test${count}"
        elif [[ "$cmd" == "dep" ]]; then
            echo "dep $*" >> "$LOG"
        fi
        """
    ).strip()

    gt_script = textwrap.dedent(
        """
        #!/usr/bin/env bash
        set -e
        if [[ "$1" == "convoy" && "$2" == "create" ]]; then
            echo "gt-abc123"
        fi
        """
    ).strip()

    write_fake_cli(bin_dir, "bd", bd_script)
    write_fake_cli(bin_dir, "gt", gt_script)

    monkeypatch.setenv("PATH", f"{bin_dir}:{os.environ.get('PATH', '')}")
    monkeypatch.setenv("BD_LOG", str(bd_log))
    monkeypatch.setenv("BD_COUNT", str(bd_count))

    exit_code, result = task_parser.run_taskstoepic(
        tasks_path=tasks_path,
        feature_dir=feature_dir,
        repo_root=repo_root,
        user_input="",
    )

    assert exit_code == 0
    assert len(result["created"]) == 2
    assert result["convoy"]["convoy_id"] == "gt-abc123"


def test_idempotency_run_twice(tmp_path, monkeypatch):
    task_parser = load_task_parser()
    repo_root, feature_dir, tasks_path = setup_repo(tmp_path)

    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    bd_log = tmp_path / "bd.log"
    bd_count = tmp_path / "bd.count"

    bd_script = textwrap.dedent(
        """
        #!/usr/bin/env bash
        set -e
        COUNT_FILE="$BD_COUNT"
        cmd="$1"
        shift
        if [[ "$cmd" == "create" ]]; then
            count=0
            if [[ -f "$COUNT_FILE" ]]; then
                count=$(cat "$COUNT_FILE")
            fi
            count=$((count + 1))
            echo "$count" > "$COUNT_FILE"
            echo "bd-test${count}"
        fi
        """
    ).strip()

    write_fake_cli(bin_dir, "bd", bd_script)
    monkeypatch.setenv("PATH", f"{bin_dir}:{os.environ.get('PATH', '')}")
    monkeypatch.setenv("BD_COUNT", str(bd_count))

    exit_code1, result1 = task_parser.run_taskstoepic(
        tasks_path=tasks_path,
        feature_dir=feature_dir,
        repo_root=repo_root,
        user_input="",
    )
    exit_code2, result2 = task_parser.run_taskstoepic(
        tasks_path=tasks_path,
        feature_dir=feature_dir,
        repo_root=repo_root,
        user_input="",
    )

    assert exit_code1 == 0
    assert exit_code2 == 0
    assert len(result2["created"]) == 0
    assert len(result2["skipped"]) == 2


def test_dependency_linking(tmp_path, monkeypatch):
    task_parser = load_task_parser()
    repo_root, feature_dir, tasks_path = setup_repo(tmp_path)

    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    bd_log = tmp_path / "bd.log"
    bd_count = tmp_path / "bd.count"

    bd_script = textwrap.dedent(
        """
        #!/usr/bin/env bash
        set -e
        LOG="$BD_LOG"
        COUNT_FILE="$BD_COUNT"
        cmd="$1"
        shift
        if [[ "$cmd" == "create" ]]; then
            count=0
            if [[ -f "$COUNT_FILE" ]]; then
                count=$(cat "$COUNT_FILE")
            fi
            count=$((count + 1))
            echo "$count" > "$COUNT_FILE"
            echo "bd-test${count}"
        elif [[ "$cmd" == "dep" ]]; then
            echo "dep $*" >> "$LOG"
        fi
        """
    ).strip()

    write_fake_cli(bin_dir, "bd", bd_script)
    monkeypatch.setenv("PATH", f"{bin_dir}:{os.environ.get('PATH', '')}")
    monkeypatch.setenv("BD_LOG", str(bd_log))
    monkeypatch.setenv("BD_COUNT", str(bd_count))

    task_parser.run_taskstoepic(
        tasks_path=tasks_path,
        feature_dir=feature_dir,
        repo_root=repo_root,
        user_input="",
    )

    log_content = bd_log.read_text(encoding="utf-8")
    assert "dep add" in log_content


def test_graceful_degradation_missing_gt(tmp_path, monkeypatch):
    task_parser = load_task_parser()
    repo_root, feature_dir, tasks_path = setup_repo(tmp_path)

    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    bd_count = tmp_path / "bd.count"

    bd_script = textwrap.dedent(
        """
        #!/usr/bin/env bash
        set -e
        COUNT_FILE="$BD_COUNT"
        cmd="$1"
        shift
        if [[ "$cmd" == "create" ]]; then
            count=0
            if [[ -f "$COUNT_FILE" ]]; then
                count=$(cat "$COUNT_FILE")
            fi
            count=$((count + 1))
            echo "$count" > "$COUNT_FILE"
            echo "bd-test${count}"
        fi
        """
    ).strip()

    write_fake_cli(bin_dir, "bd", bd_script)
    monkeypatch.setenv("PATH", f"{bin_dir}:{os.environ.get('PATH', '')}")
    monkeypatch.setenv("BD_COUNT", str(bd_count))

    exit_code, result = task_parser.run_taskstoepic(
        tasks_path=tasks_path,
        feature_dir=feature_dir,
        repo_root=repo_root,
        user_input="",
    )

    assert exit_code == 0
    assert result["convoy"] is None
    assert "Gastown CLI not found" in result["convoy_warning"]


def test_missing_tasks_file_error(tmp_path):
    task_parser = load_task_parser()
    repo_root = tmp_path
    feature_dir = tmp_path / "specs" / "001-feature"
    feature_dir.mkdir(parents=True)
    tasks_path = feature_dir / "tasks.md"

    exit_code, result = task_parser.run_taskstoepic(
        tasks_path=tasks_path,
        feature_dir=feature_dir,
        repo_root=repo_root,
        user_input="",
    )

    assert exit_code == 1
    assert "tasks.md not found" in result["error"]


def test_partial_failure_on_bd_create(tmp_path, monkeypatch):
    task_parser = load_task_parser()
    repo_root, feature_dir, tasks_path = setup_repo(tmp_path)

    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    bd_count = tmp_path / "bd.count"

    bd_script = textwrap.dedent(
        """
        #!/usr/bin/env bash
        set -e
        COUNT_FILE="$BD_COUNT"
        cmd="$1"
        shift
        if [[ "$cmd" == "create" ]]; then
            count=0
            if [[ -f "$COUNT_FILE" ]]; then
                count=$(cat "$COUNT_FILE")
            fi
            count=$((count + 1))
            echo "$count" > "$COUNT_FILE"
            if [[ "$count" -eq 3 ]]; then
                echo "forced failure" >&2
                exit 1
            fi
            echo "bd-test${count}"
        fi
        """
    ).strip()

    write_fake_cli(bin_dir, "bd", bd_script)
    monkeypatch.setenv("PATH", f"{bin_dir}:{os.environ.get('PATH', '')}")
    monkeypatch.setenv("BD_COUNT", str(bd_count))

    exit_code, result = task_parser.run_taskstoepic(
        tasks_path=tasks_path,
        feature_dir=feature_dir,
        repo_root=repo_root,
        user_input="",
    )

    assert exit_code == 6
    assert result["failed"]
