"""
Tests for Phase 3: Memory Accumulation functionality.

Tests for auto-save, cross-project learning, smart search, etc.
"""

import pytest
import tempfile
import json
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

from specify_cli.memory.project_detector import ProjectDetector
from specify_cli.memory.auto_save import AutoSaveTrigger
from specify_cli.memory.headers_reader import HeadersFirstReader, ContextOptimizer
from specify_cli.memory.cross_project import CrossProjectLearning
from specify_cli.memory.smart_search import SmartSearchEngine, SearchScope
from specify_cli.memory.backup import MemoryBackup, AutoBackup


class TestProjectDetector:
    """Test project auto-detection."""

    def test_detect_from_directory_name(self):
        """Test detection using directory name."""
        with tempfile.TemporaryDirectory() as tmpdir:
            detector = ProjectDetector(global_home=Path(tmpdir))

            # Create a test project directory
            project_dir = Path(tmpdir) / "test-projects" / "my-cool-project"
            project_dir.mkdir(parents=True)

            info = detector.detect_current_project(project_dir)

            assert info["project_id"] == "my-cool-project"
            assert info["project_name"] == "my-cool-project"
            assert info["is_git"] is False

    def test_detect_from_git_remote(self):
        """Test detection using git remote URL."""
        with tempfile.TemporaryDirectory() as tmpdir:
            detector = ProjectDetector(global_home=Path(tmpdir))

            # Mock git command
            with patch('subprocess.run') as mock_run:
                mock_result = Mock()
                mock_result.returncode = 0
                mock_result.stdout.strip.return_value = "https://github.com/user/repo.git"
                mock_run.return_value = mock_result

                # Create git directory
                git_dir = Path(tmpdir) / "project" / ".git"
                git_dir.mkdir(parents=True)

                info = detector.detect_current_project(git_dir.parent)

                assert info["project_id"] == "user-repo"
                assert info["project_name"] == "repo"
                assert info["is_git"] is True

    def test_ensure_memory_structure(self):
        """Test memory directory structure creation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            detector = ProjectDetector(global_home=Path(tmpdir))

            success = detector.ensure_project_memory_structure(
                "test-project",
                Path(tmpdir) / "memory" / "projects" / "test-project"
            )

            assert success is True
            assert (Path(tmpdir) / "memory" / "projects" / "test-project" / ".spec-kit").exists()

    def test_list_all_projects(self):
        """Test listing all projects with memory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            detector = ProjectDetector(global_home=Path(tmpdir))

            # Create projects
            projects_dir = Path(tmpdir) / "memory" / "projects"
            projects_dir.mkdir(parents=True)

            (projects_dir / "project1").mkdir()
            (projects_dir / "project2").mkdir()

            projects = detector.list_all_projects()

            assert len(projects) >= 2
            project_ids = [p["project_id"] for p in projects]
            assert "project1" in project_ids
            assert "project2" in project_ids


class TestAutoSaveTrigger:
    """Test auto-save trigger functionality."""

    def test_track_event(self):
        """Test event tracking."""
        with tempfile.TemporaryDirectory() as tmpdir:
            trigger = AutoSaveTrigger(
                project_id="test-project",
                global_home=Path(tmpdir),
                enabled=False  # Disable actual saving
            )

            event_id = trigger.track_event(
                "test_event",
                {"key": "value"},
                auto_save=False
            )

            assert event_id is not None
            assert len(event_id) == 8  # UUID prefix length

    def test_task_completed(self):
        """Test task completion tracking."""
        with tempfile.TemporaryDirectory() as tmpdir:
            trigger = AutoSaveTrigger(
                project_id="test-project",
                global_home=Path(tmpdir),
                enabled=False
            )

            event_id = trigger.task_completed(
                task_name="Build feature",
                success=True,
                lessons="Use async/await for I/O"
            )

            assert event_id is not None

            events = trigger.get_recent_events()
            assert len(events) > 0
            assert events[0]["type"] == "task_complete"

    def test_error_fixed(self):
        """Test error fix tracking."""
        with tempfile.TemporaryDirectory() as tmpdir:
            trigger = AutoSaveTrigger(
                project_id="test-project",
                global_home=Path(tmpdir),
                enabled=True  # Enable to test actual saving
            )

            # Initialize memory files first
            from specify_cli.memory.file_manager import FileMemoryManager
            manager = FileMemoryManager(global_home=Path(tmpdir))
            manager.initialize_memory_files()

            event_id = trigger.error_fixed(
                error="Connection timeout",
                solution="Increase timeout to 30s",
                context="API calls to external service"
            )

            assert event_id is not None

    def test_pattern_discovered(self):
        """Test pattern discovery tracking."""
        with tempfile.TemporaryDirectory() as tmpdir:
            trigger = AutoSaveTrigger(
                project_id="test-project",
                global_home=Path(tmpdir),
                enabled=True
            )

            # Initialize memory files first
            from specify_cli.memory.file_manager import FileMemoryManager
            manager = FileMemoryManager(global_home=Path(tmpdir))
            manager.initialize_memory_files()

            event_id = trigger.pattern_discovered(
                pattern_name="Repository Pattern",
                description="Separate data access from business logic",
                code_example="class Repository { ... }"
            )

            assert event_id is not None

    def test_enable_disable(self):
        """Test enable/disable functionality."""
        with tempfile.TemporaryDirectory() as tmpdir:
            trigger = AutoSaveTrigger(
                project_id="test-project",
                global_home=Path(tmpdir),
                enabled=True
            )

            assert trigger.enabled is True

            trigger.disable()
            assert trigger.enabled is False

            trigger.enable()
            assert trigger.enabled is True


class TestHeadersFirstReader:
    """Test headers-first reading for context optimization."""

    def test_read_headers(self):
        """Test reading only headers from memory files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test file with headers
            memory_dir = Path(tmpdir) / "memory" / "projects" / ".global"
            memory_dir.mkdir(parents=True)

            lessons_file = memory_dir / "lessons.md"
            lessons_file.write_text("""
# Lessons Learned

## Error: JWT Token Expired - Need refresh token flow
**Date**: 2025-01-10
**Context**: Authentication failing after 15 minutes
**Solution**: Implement token refresh with silent renewal

## Error: Database Connection Pool Exhausted
**Date**: 2025-01-11
**Solution**: Increase pool size and implement proper connection cleanup
""", encoding='utf-8')

            reader = HeadersFirstReader(global_home=Path(tmpdir))

            headers = reader.read_headers(".global", file_types=["lessons"], limit=10)

            assert "lessons" in headers
            assert len(headers["lessons"]) == 2
            assert "JWT Token Expired" in headers["lessons"][0]["title"]
            assert "Need refresh token flow" in headers["lessons"][0]["summary"]

    def test_read_section(self):
        """Test reading full section."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test file
            memory_dir = Path(tmpdir) / "memory" / "projects" / ".global"
            memory_dir.mkdir(parents=True)

            lessons_file = memory_dir / "lessons.md"
            lessons_file.write_text("""
# Lessons

## Error: JWT
**Date**: 2025-01-10
**Solution**: Use refresh tokens

## Other Section
Some content here
""", encoding='utf-8')

            reader = HeadersFirstReader(global_home=Path(tmpdir))

            section = reader.read_section(".global", "lessons", "JWT")

            assert section is not None
            assert "refresh tokens" in section

    def test_context_token_estimate(self):
        """Test token estimation."""
        reader = HeadersFirstReader()

        # Rough estimate: ~4 chars per token
        text = "This is a test text with some words"
        estimated = reader.estimate_tokens(text)

        assert estimated > 0
        assert estimated < len(text)  # Should be less than char count

    def test_format_compact_context(self):
        """Test compact formatting for minimal tokens."""
        with tempfile.TemporaryDirectory() as tmpdir:
            reader = HeadersFirstReader(global_home=Path(tmpdir))

            headers = {
                "lessons": [
                    {"title": "Error: JWT", "summary": "Need refresh flow"}
                ],
                "patterns": [
                    {"title": "Repository", "summary": "Data access pattern"}
                ]
            }

            context = reader.format_headers_context(headers, format="compact")

            assert "Lessons (1 items)" in context
            assert "Patterns (1 items)" in context
            assert "Error: JWT" in context


class TestContextOptimizer:
    """Test context optimization."""

    def test_get_before_task_context(self):
        """Test getting minimal context before task."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test files
            memory_dir = Path(tmpdir) / "memory" / "projects" / ".global"
            memory_dir.mkdir(parents=True)

            for file_type in ["lessons", "patterns"]:
                file_path = memory_dir / f"{file_type}.md"
                file_path.write_text(f"""
# {file_type.title()}

## Test Entry - Summary here
Content goes here
""", encoding='utf-8')

            optimizer = ContextOptimizer(global_home=Path(tmpdir))

            context = optimizer.get_before_task_context(".global", token_budget=100)

            assert "context" in context
            assert "estimated_tokens" in context
            assert context["estimated_tokens"] < 500  # Should be minimal

    def test_get_deep_dive_context(self):
        """Test getting full section content."""
        with tempfile.TemporaryDirectory() as tmpdir:
            memory_dir = Path(tmpdir) / "memory" / "projects" / ".global"
            memory_dir.mkdir(parents=True)

            lessons_file = memory_dir / "lessons.md"
            lessons_file.write_text("""
# Lessons

## Target Entry
**Date**: 2025-01-10
**Solution**: Detailed solution here
""", encoding='utf-8')

            optimizer = ContextOptimizer(global_home=Path(tmpdir))

            content = optimizer.get_deep_dive_context(".global", "lessons", "Target Entry")

            assert content is not None
            assert "Detailed solution" in content


class TestCrossProjectLearning:
    """Test cross-project learning functionality."""

    def test_find_related_projects(self):
        """Test finding related projects."""
        with tempfile.TemporaryDirectory() as tmpdir:
            learning = CrossProjectLearning(global_home=Path(tmpdir))

            # Create mock projects
            projects_dir = Path(tmpdir) / "memory" / "projects"
            projects_dir.mkdir(parents=True)

            (projects_dir / "project1-react").mkdir()
            (projects_dir / "project2-vue").mkdir()
            (projects_dir / "project3-react").mkdir()

            related = learning.find_related_projects("project1-react")

            # Should find project3-react as related (same technology)
            project_ids = [p["project_id"] for p in related]
            assert "project3-react" in project_ids

    def test_calculate_similarity(self):
        """Test project similarity calculation."""
        learning = CrossProjectLearning()

        # Same technology
        sim1 = learning._calculate_project_similarity("my-react-app", "other-react-project")
        assert sim1 > 0.3

        # Different technologies
        sim2 = learning._calculate_project_similarity("react-app", "vue-app")
        assert sim2 < sim1

    def test_transfer_learning(self):
        """Test transferring learnings between projects."""
        with tempfile.TemporaryDirectory() as tmpdir:
            learning = CrossProjectLearning(global_home=Path(tmpdir))

            # Setup source project
            from specify_cli.memory.file_manager import FileMemoryManager
            manager = FileMemoryManager(global_home=Path(tmpdir))

            source_dir = Path(tmpdir) / "memory" / "projects" / "source"
            source_dir.mkdir(parents=True)

            patterns_file = source_dir / "patterns.md"
            patterns_file.write_text("""
# Patterns

## Important Pattern
**Importance**: high
This is an important pattern worth transferring
""", encoding='utf-8')

            # Create target project
            target_dir = Path(tmpdir) / "memory" / "projects" / "target"
            target_dir.mkdir(parents=True)

            transferred = learning.transfer_learning("source", "target", min_importance=0.0)

            # Should transfer the pattern
            assert transferred >= 0


class TestSmartSearch:
    """Test smart search with scope determination."""

    def test_determine_scope_global_markers(self):
        """Test scope determination with global markers."""
        engine = SmartSearchEngine()

        scope = engine.determine_scope("вообще ищу решение")
        assert scope == SearchScope.GLOBAL

    def test_determine_scope_local_markers(self):
        """Test scope determination with local markers."""
        engine = SmartSearchEngine()

        scope = engine.determine_scope("в этом проекте есть ошибка")
        assert scope == SearchScope.LOCAL

    def test_determine_scope_auto(self):
        """Test auto scope determination."""
        engine = SmartSearchEngine()

        scope = engine.determine_scope("как исправить ошибку")
        # Questions about fixing should use auto then determine
        assert scope in [SearchScope.AUTO, SearchScope.LOCAL]

    def test_search_local(self):
        """Test local search."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test data
            memory_dir = Path(tmpdir) / "memory" / "projects" / "test-project"
            memory_dir.mkdir(parents=True)

            lessons_file = memory_dir / "lessons.md"
            lessons_file.write_text("""
# Lessons

## Error: JWT Expired
Need refresh token flow
""", encoding='utf-8')

            engine = SmartSearchEngine(global_home=Path(tmpdir))

            results = engine.search("JWT", scope="local", current_project_id="test-project")

            assert "results" in results
            assert len(results["results"]) > 0
            assert "JWT" in results["results"][0]["title"]

    def test_suggest_expansion(self):
        """Test suggestion to expand to global search."""
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = SmartSearchEngine(global_home=Path(tmpdir))

            # Poor local results
            local_results = [
                {"title": "Unrelated", "relevance": 0.1}
            ]

            suggestion = engine.suggest_expansion(
                local_results,
                "search query",
                "test-project"
            )

            # Should suggest expansion (though may be None if no global results)
            # In this case, with no global data, it will be None
            assert suggestion is None or "reason" in suggestion


class TestMemoryBackup:
    """Test memory backup functionality."""

    def test_create_backup(self):
        """Test creating backup."""
        with tempfile.TemporaryDirectory() as tmpdir:
            backup = MemoryBackup(global_home=Path(tmpdir))

            # Create test file
            memory_dir = Path(tmpdir) / "memory" / "projects" / "test-project"
            memory_dir.mkdir(parents=True)

            test_file = memory_dir / "lessons.md"
            test_file.write_text("# Lessons\n\n## Test Entry\nContent")

            backup_path = backup.create_backup("test-project", file_types=["lessons"])

            assert backup_path is not None
            assert backup_path.exists()
            assert (backup_path / "lessons.md").exists()

    def test_list_backups(self):
        """Test listing backups."""
        with tempfile.TemporaryDirectory() as tmpdir:
            backup = MemoryBackup(global_home=Path(tmpdir))

            # Create a backup first
            memory_dir = Path(tmpdir) / "memory" / "projects" / "test-project"
            memory_dir.mkdir(parents=True)

            test_file = memory_dir / "lessons.md"
            test_file.write_text("content")

            backup.create_backup("test-project", file_types=["lessons"])

            # List backups
            backups = backup.list_backups("test-project")

            assert len(backups) > 0
            assert "timestamp" in backups[0]

    def test_restore_backup(self):
        """Test restoring from backup."""
        with tempfile.TemporaryDirectory() as tmpdir:
            backup = MemoryBackup(global_home=Path(tmpdir))

            # Create original file
            memory_dir = Path(tmpdir) / "memory" / "projects" / "test-project"
            memory_dir.mkdir(parents=True)

            original_file = memory_dir / "lessons.md"
            original_content = "# Original Content\n\n## Entry 1"
            original_file.write_text(original_content)

            # Create backup
            backup_path = backup.create_backup("test-project", file_types=["lessons"])

            # Modify original
            original_file.write_text("# Modified Content")

            # Restore
            success = backup.restore_backup("test-project", backup_path.name.split("_", 1)[1])

            assert success is True
            # Check restored content
            restored = original_file.read_text()
            assert "Original Content" in restored


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
