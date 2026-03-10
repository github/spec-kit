"""
End-to-End Integration Tests (T084)

Tests complete workflows across all memory system components.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from specify_cli.memory.orchestrator import MemoryOrchestrator
from specify_cli.memory.headers_reader import HeadersFirstReader
from specify_cli.memory.project_detector import ProjectDetector
from specify_cli.memory.auto_save import AutoSaveTrigger
from specify_cli.memory.backup import MemoryBackup
from specify_cli.memory.smart_search import SmartSearchEngine


@pytest.fixture
def temp_project():
    """Create temporary project for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_path = Path(tmpdir) / "test-project"
        project_path.mkdir()

        # Initialize git repo
        import subprocess
        subprocess.run(["git", "init"], cwd=project_path, capture_output=True)
        subprocess.run(
            ["git", "config", "user.email", "test@example.com"],
            cwd=project_path,
            capture_output=True
        )
        subprocess.run(
            ["git", "config", "user.name", "Test User"],
            cwd=project_path,
            capture_output=True
        )

        # Create memory structure
        memory_path = Path(tmpdir) / "memory" / "projects" / "test-project"
        memory_path.mkdir(parents=True)

        yield {
            "project_path": project_path,
            "memory_path": memory_path,
            "temp_dir": tmpdir
        }


class TestMemoryOrchestratorE2E:
    """Test complete orchestrator workflows."""

    def test_full_lifecycle(self, temp_project):
        """Test complete memory lifecycle: add, search, retrieve."""
        orchestrator = MemoryOrchestrator(
            project_id="test-project",
            memory_root=Path(temp_project["temp_dir"]) / "memory"
        )

        # 1. Add entries
        orchestrator.add_lesson(
            title="Test Error",
            problem="Test failed",
            solution="Added missing import"
        )

        orchestrator.add_pattern(
            title="Test Pattern",
            description="Reusable test setup",
            code="def setup_test(): pass"
        )

        # 2. Search
        results = orchestrator.search("test")
        assert len(results) > 0

        # 3. Retrieve
        lessons = orchestrator.get_lessons()
        assert len(lessons) == 1
        assert "Test Error" in lessons[0]["title"]

        patterns = orchestrator.get_patterns()
        assert len(patterns) == 1
        assert "Test Pattern" in patterns[0]["title"]


class TestHeadersFirstReadingE2E:
    """Test headers-first reading workflows."""

    def test_headers_then_deep_read(self, temp_project):
        """Test reading headers first, then deep reading specific entry."""
        memory_path = temp_project["memory_path"]

        # Create test lessons file
        lessons_file = memory_path / "lessons.md"
        lessons_file.write_text("""
## Lesson One - Quick Fix
**Problem**: Bug in authentication
**Solution**: Added null check

## Lesson Two - Major Refactor
**Problem**: Code was unmaintainable
**Solution**: Refactored into modules
""")

        reader = HeadersFirstReader(
            project_id="test-project",
            memory_root=Path(temp_project["temp_dir"]) / "memory"
        )

        # 1. Read headers (lightweight)
        headers = reader.read_headers_first(file_types=["lessons"])
        assert len(headers) == 2
        assert headers[0]["title"] == "Lesson One"
        assert headers[1]["title"] == "Lesson Two"

        # 2. Deep read specific entry
        content = reader.read_section(
            file_type="lessons",
            header_match="Lesson One"
        )
        assert "Bug in authentication" in content


class TestAutoSaveE2E:
    """Test auto-save workflows."""

    def test_error_fix_capture(self, temp_project):
        """Test capturing error fix via auto-save."""
        memory_path = temp_project["memory_dir"] = Path(temp_project["temp_dir"]) / "memory" / "projects" / "test-project"
        memory_path.mkdir(parents=True, exist_ok=True)

        auto_save = AutoSaveTrigger(
            project_id="test-project",
            global_home=Path(temp_project["temp_dir"]) / "memory"
        )

        # Track error fix
        event_id = auto_save.error_fixed(
            error="Database connection timeout",
            solution="Increased connection timeout to 30s",
            context="Production environment"
        )

        assert event_id is not None

        # Verify it was saved
        lessons_file = memory_path / "lessons.md"
        content = lessons_file.read_text()
        assert "Database connection timeout" in content


class TestSmartSearchE2E:
    """Test smart search workflows."""

    def test_local_vs_global_search(self, temp_project):
        """Test automatic scope determination."""
        # This test requires multiple projects
        # For now, test local search
        memory_path = temp_project["memory_path"]

        # Create test patterns
        patterns_file = memory_path / "patterns.md"
        patterns_file.write_text("""
## Authentication Pattern
**Description**: JWT-based authentication
**When**: User login required
""")

        engine = SmartSearchEngine(
            global_home=Path(temp_project["temp_dir"]) / "memory"
        )

        # Local search
        results = engine.search(
            query="authentication",
            scope="local",
            current_project_id="test-project"
        )

        assert len(results) > 0
        assert results[0]["title"] == "Authentication Pattern"


class TestProjectDetectionE2E:
    """Test project detection workflows."""

    def test_git_project_detection(self, temp_project):
        """Test detecting project from git repository."""
        detector = ProjectDetector(
            global_home=Path(temp_project["temp_dir"]) / "memory"
        )

        project_info = detector.detect_current_project(
            cwd=temp_project["project_path"]
        )

        assert project_info["is_git"] is True
        assert "test-project" in project_info["project_id"]
        assert "memory_path" in project_info


class TestBackupE2E:
    """Test backup workflows."""

    def test_backup_and_restore(self, temp_project):
        """Test creating and restoring from backup."""
        memory_path = temp_project["memory_path"]

        # Create test data
        (memory_path / "lessons.md").write_text("# Test Lesson\n\nContent here")
        (memory_path / "patterns.md").write_text("# Test Pattern\n\nContent here")

        backup = MemoryBackup(
            global_home=Path(temp_project["temp_dir"]) / "memory"
        )

        # Create backup
        backup_path = backup.create_backup(
            project_id="test-project",
            file_types=["lessons", "patterns"]
        )

        assert backup_path is not None
        assert backup_path.exists()

        # Modify files
        (memory_path / "lessons.md").write_text("# Modified\n\nNew content")

        # Restore from backup
        success = backup.restore_backup(
            project_id="test-project",
            backup_timestamp=backup_path.name.split("_")[-1],
            file_types=["lessons"]
        )

        assert success is True
        content = (memory_path / "lessons.md").read_text()
        assert "Test Lesson" in content


@pytest.mark.integration
class TestCompleteWorkflowE2E:
    """Test complete end-to-end workflow."""

    def test_developer_day_workflow(self, temp_project):
        """Simulate a developer's day with memory system."""
        orchestrator = MemoryOrchestrator(
            project_id="test-project",
            memory_root=Path(temp_project["temp_dir"]) / "memory"
        )

        # Morning: Check relevant past work
        morning_results = orchestrator.search("authentication")
        assert isinstance(morning_results, list)

        # Mid-day: Encounter and fix bug
        orchestrator.add_lesson(
            title="Session Timeout Error",
            problem="Users logged out after 5 minutes",
            solution="Increased session timeout to 24 hours"
        )

        # Afternoon: Discover pattern
        orchestrator.add_pattern(
            title="Session Management Pattern",
            description="Handle user sessions with refresh tokens",
            code="class SessionManager: ..."
        )

        # Evening: Make architecture decision
        orchestrator.add_architecture(
            title="JWT for Authentication",
            context="Need stateless authentication",
            decision="JWT with refresh token rotation",
            rationale="Scalable, mobile-friendly, industry standard"
        )

        # Next day: Search and find all relevant info
        all_results = orchestrator.search("session authentication")
        assert len(all_results) >= 3  # lesson + pattern + architecture

        # Verify cross-project search would work
        detector = ProjectDetector(
            global_home=Path(temp_project["temp_dir"]) / "memory"
        )
        project_info = detector.detect_current_project(
            cwd=temp_project["project_path"]
        )
        assert project_info["project_id"] is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
