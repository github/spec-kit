import json
from pathlib import Path
from specify_cli.guards.registry import GuardRegistry


def test_registry_initialization(temp_project_dir):
    guards_base = temp_project_dir / ".specify" / "guards"
    registry = GuardRegistry(guards_base)
    
    assert (guards_base / "list").exists()
    assert (guards_base / "history").exists()
    assert (guards_base / "index.json").exists()


def test_generate_sequential_ids(temp_project_dir):
    guards_base = temp_project_dir / ".specify" / "guards"
    registry = GuardRegistry(guards_base)
    
    id1 = registry.generate_id()
    id2 = registry.generate_id()
    id3 = registry.generate_id()
    
    assert id1 == "G001"
    assert id2 == "G002"
    assert id3 == "G003"


def test_add_and_get_guard(temp_project_dir):
    guards_base = temp_project_dir / ".specify" / "guards"
    registry = GuardRegistry(guards_base)
    
    registry.add_guard(
        guard_id="G001",
        guard_type="unit-pytest",
        name="test-commands",
        command="make test-guard-G001",
        files=["tests/unit/guards/G001_test_commands.py"]
    )
    
    guard = registry.get_guard("G001")
    assert guard is not None
    assert guard["id"] == "G001"
    assert guard["type"] == "unit-pytest"
    assert guard["name"] == "test-commands"
    assert guard["command"] == "make test-guard-G001"
    assert guard["files"] == ["tests/unit/guards/G001_test_commands.py"]


def test_list_guards(temp_project_dir):
    guards_base = temp_project_dir / ".specify" / "guards"
    registry = GuardRegistry(guards_base)
    
    registry.add_guard("G001", "unit-pytest", "guard1", "make test1", ["test1.py"])
    registry.add_guard("G002", "api", "guard2", "make test2", ["test2.py"])
    
    guards = registry.list_guards()
    assert len(guards) == 2
    assert guards[0]["id"] == "G001"
    assert guards[1]["id"] == "G002"


def test_update_guard_status(temp_project_dir):
    guards_base = temp_project_dir / ".specify" / "guards"
    registry = GuardRegistry(guards_base)
    
    registry.add_guard("G001", "unit-pytest", "test", "make test", ["test.py"])
    
    registry.update_guard_status("G001", "disabled")
    
    guard = registry.get_guard("G001")
    assert guard is not None
    assert guard["status"] == "disabled"


def test_get_nonexistent_guard(temp_project_dir):
    guards_base = temp_project_dir / ".specify" / "guards"
    registry = GuardRegistry(guards_base)
    
    guard = registry.get_guard("G999")
    assert guard is None


def test_record_execution(temp_project_dir):
    guards_base = temp_project_dir / ".specify" / "guards"
    registry = GuardRegistry(guards_base)
    
    registry.add_guard("G001", "unit-pytest", "test", "make test", ["test.py"])
    
    registry.record_execution(
        guard_id="G001",
        result="pass",
        exit_code=0,
        duration_ms=1234,
        output="All tests passed"
    )
    
    guard = registry.get_guard("G001")
    assert guard is not None
    assert guard["last_result"] == "pass"
    assert guard["execution_count"] == 1
    assert guard["last_executed"] is not None
    
    history = registry.get_guard_history("G001")
    assert len(history) >= 1
    if history and history[0]:
        assert history[0]["result"] == "pass"
        assert history[0]["exit_code"] == 0
        assert history[0]["duration_ms"] == 1234
