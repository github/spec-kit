"""Unit tests for FileStorage."""

import tempfile
from pathlib import Path

import pytest

from speckit.schemas import (
    Constitution,
    Specification,
    TechnicalPlan,
    TaskBreakdown,
    Task,
    TechStack,
    Priority,
    TaskStatus,
    PhaseType,
)
from speckit.storage.file_storage import FileStorage


@pytest.fixture
def temp_project():
    """Create a temporary project directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def storage(temp_project):
    """Create FileStorage instance."""
    return FileStorage(temp_project)


class TestFileStorageInit:
    """Tests for FileStorage initialization."""

    def test_creates_directories(self, temp_project):
        """Test that storage creates necessary directories."""
        storage = FileStorage(temp_project)

        assert (temp_project / ".speckit").exists()
        assert (temp_project / "specs").exists()

    def test_custom_directories(self, temp_project):
        """Test custom directory names."""
        storage = FileStorage(
            temp_project,
            specs_dir="features",
            base_dir=".config",
        )

        assert (temp_project / ".config").exists()
        assert (temp_project / "features").exists()


class TestConstitutionStorage:
    """Tests for Constitution storage."""

    @pytest.fixture
    def constitution(self):
        """Create test constitution."""
        return Constitution(
            project_name="Test Project",
            core_principles=["Principle 1", "Principle 2"],
            quality_standards=["Standard 1"],
            testing_standards=["Test standard"],
            tech_constraints=["Constraint 1"],
            ux_guidelines=["UX rule"],
            governance_rules=["Rule 1"],
        )

    def test_save_constitution(self, storage, constitution):
        """Test saving constitution."""
        path = storage.save_constitution(constitution)

        assert path.exists()
        assert path.name == "constitution.md"
        assert "Test Project" in path.read_text()

    def test_load_constitution(self, storage, constitution):
        """Test loading constitution."""
        storage.save_constitution(constitution)
        loaded = storage.load_constitution()

        assert loaded is not None
        assert loaded.project_name == "Test Project"
        assert "Principle 1" in loaded.core_principles
        assert "Principle 2" in loaded.core_principles

    def test_load_nonexistent_constitution(self, storage):
        """Test loading when no constitution exists."""
        loaded = storage.load_constitution()
        assert loaded is None

    def test_backup_on_overwrite(self, storage, constitution):
        """Test that backup is created on overwrite."""
        storage.save_constitution(constitution)
        constitution.project_name = "Updated Project"
        storage.save_constitution(constitution)

        # Check for backup file
        backup_files = list(storage.config_path.glob("*.bak"))
        assert len(backup_files) == 1


class TestSpecificationStorage:
    """Tests for Specification storage."""

    @pytest.fixture
    def specification(self):
        """Create test specification."""
        return Specification(
            feature_name="Test Feature",
            feature_id="001-test",
            overview="A test feature",
            problem_statement="Solving test problems",
            target_users=["developers"],
            assumptions=["Users can code"],
            constraints=["Python only"],
            out_of_scope=["GUI"],
            success_criteria=["Tests pass"],
        )

    def test_save_specification(self, storage, specification):
        """Test saving specification."""
        path = storage.save_specification(specification, "001-test")

        assert path.exists()
        assert "Test Feature" in path.read_text()

    def test_load_specification(self, storage, specification):
        """Test loading specification."""
        storage.save_specification(specification, "001-test")
        loaded = storage.load_specification("001-test")

        assert loaded is not None
        assert loaded.feature_name == "Test Feature"
        assert loaded.feature_id == "001-test"

    def test_load_nonexistent_specification(self, storage):
        """Test loading when no specification exists."""
        loaded = storage.load_specification("999-nonexistent")
        assert loaded is None


class TestPlanStorage:
    """Tests for TechnicalPlan storage."""

    @pytest.fixture
    def plan(self):
        """Create test plan."""
        return TechnicalPlan(
            feature_id="001-test",
            tech_stack=TechStack(
                language="Python 3.11",
                framework="FastAPI",
                testing="pytest",
            ),
            architecture_overview="A microservice architecture",
            technical_risks=["Risk 1"],
            mitigation_strategies=["Strategy 1"],
        )

    def test_save_plan(self, storage, plan):
        """Test saving plan."""
        path = storage.save_plan(plan, "001-test")

        assert path.exists()
        assert "Python 3.11" in path.read_text()

    def test_load_plan(self, storage, plan):
        """Test loading plan."""
        storage.save_plan(plan, "001-test")
        loaded = storage.load_plan("001-test")

        assert loaded is not None
        assert loaded.feature_id == "001-test"

    def test_load_nonexistent_plan(self, storage):
        """Test loading when no plan exists."""
        loaded = storage.load_plan("999-nonexistent")
        assert loaded is None


class TestTasksStorage:
    """Tests for TaskBreakdown storage."""

    @pytest.fixture
    def tasks(self):
        """Create test task breakdown."""
        from speckit.schemas import Phase

        return TaskBreakdown(
            feature_id="001-test",
            feature_name="Test Feature",
            phases=[
                Phase(
                    id="setup",
                    number=1,
                    name="Setup",
                    purpose="Project initialization",
                    checkpoint="Setup complete",
                ),
                Phase(
                    id="core",
                    number=2,
                    name="Core Implementation",
                    purpose="Main functionality",
                    checkpoint="Core complete",
                ),
            ],
            tasks=[
                Task(
                    id="T001",
                    title="Setup project",
                    phase="setup",
                    priority="P1",
                    status=TaskStatus.COMPLETED,
                    description="Initialize the project structure",
                    file_paths=["pyproject.toml"],
                ),
                Task(
                    id="T002",
                    title="Implement feature",
                    phase="core",
                    priority="P1",
                    status=TaskStatus.PENDING,
                    user_story_id="US1",
                    is_parallel=True,
                    description="Implement the main feature",
                    file_paths=["src/main.py"],
                ),
            ],
        )

    def test_save_tasks(self, storage, tasks):
        """Test saving tasks."""
        path = storage.save_tasks(tasks, "001-test")

        assert path.exists()
        content = path.read_text()
        assert "T001" in content
        assert "T002" in content

    def test_load_tasks(self, storage, tasks):
        """Test loading tasks."""
        storage.save_tasks(tasks, "001-test")
        loaded = storage.load_tasks("001-test")

        assert loaded is not None
        assert loaded.feature_id == "001-test"
        assert len(loaded.tasks) >= 2

    def test_load_nonexistent_tasks(self, storage):
        """Test loading when no tasks exist."""
        loaded = storage.load_tasks("999-nonexistent")
        assert loaded is None


class TestFeatureManagement:
    """Tests for feature management."""

    def test_list_features_empty(self, storage):
        """Test listing features when none exist."""
        features = storage.list_features()
        assert features == []

    def test_list_features(self, storage):
        """Test listing features."""
        # Create some feature directories
        storage.create_feature("001-auth")
        storage.create_feature("002-payments")

        features = storage.list_features()

        assert "001-auth" in features
        assert "002-payments" in features
        assert len(features) == 2

    def test_feature_exists(self, storage):
        """Test checking feature existence."""
        storage.create_feature("001-test")

        assert storage.feature_exists("001-test")
        assert not storage.feature_exists("999-nonexistent")

    def test_get_feature_path(self, storage, temp_project):
        """Test getting feature path."""
        path = storage.get_feature_path("001-test")

        assert path == temp_project / "specs" / "001-test"

    def test_create_feature(self, storage):
        """Test creating feature directory."""
        path = storage.create_feature("001-new")

        assert path.exists()
        assert path.is_dir()

    def test_get_artifact_path(self, storage, temp_project):
        """Test getting artifact paths."""
        spec_path = storage.get_artifact_path("001-test", "spec")
        plan_path = storage.get_artifact_path("001-test", "plan")
        tasks_path = storage.get_artifact_path("001-test", "tasks")

        assert spec_path.name == "spec.md"
        assert plan_path.name == "plan.md"
        assert tasks_path.name == "tasks.md"

    def test_get_artifact_path_invalid(self, storage):
        """Test getting path for invalid artifact type."""
        with pytest.raises(ValueError):
            storage.get_artifact_path("001-test", "invalid")

    def test_artifact_exists(self, storage):
        """Test checking artifact existence."""
        spec = Specification(
            feature_name="Test",
            feature_id="001-test",
        )
        storage.save_specification(spec, "001-test")

        assert storage.artifact_exists("001-test", "spec")
        assert not storage.artifact_exists("001-test", "plan")
