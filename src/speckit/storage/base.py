"""
Abstract base class for artifact storage.

This module defines the storage interface that all storage backends must implement.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

from speckit.schemas import (
    Constitution,
    Specification,
    TechnicalPlan,
    TaskBreakdown,
)


class StorageBase(ABC):
    """Abstract base class for artifact storage backends."""

    def __init__(self, project_path: Path, specs_dir: str = "specs", base_dir: str = ".speckit"):
        """
        Initialize storage backend.

        Args:
            project_path: Root directory of the project
            specs_dir: Directory name for feature specifications
            base_dir: Directory name for spec-kit configuration
        """
        self.project_path = Path(project_path).resolve()
        self.specs_dir = specs_dir
        self.base_dir = base_dir

    @property
    def specs_path(self) -> Path:
        """Get the full path to the specs directory."""
        return self.project_path / self.specs_dir

    @property
    def config_path(self) -> Path:
        """Get the full path to the config directory."""
        return self.project_path / self.base_dir

    # =========================================================================
    # Constitution
    # =========================================================================

    @abstractmethod
    def save_constitution(self, constitution: Constitution) -> Path:
        """
        Save project constitution.

        Args:
            constitution: Constitution model to save

        Returns:
            Path to the saved file
        """
        pass

    @abstractmethod
    def load_constitution(self) -> Optional[Constitution]:
        """
        Load project constitution.

        Returns:
            Constitution model if found, None otherwise
        """
        pass

    # =========================================================================
    # Specification
    # =========================================================================

    @abstractmethod
    def save_specification(self, specification: Specification, feature_id: str) -> Path:
        """
        Save feature specification.

        Args:
            specification: Specification model to save
            feature_id: Feature identifier (e.g., "001-auth")

        Returns:
            Path to the saved file
        """
        pass

    @abstractmethod
    def load_specification(self, feature_id: str) -> Optional[Specification]:
        """
        Load feature specification.

        Args:
            feature_id: Feature identifier

        Returns:
            Specification model if found, None otherwise
        """
        pass

    # =========================================================================
    # Technical Plan
    # =========================================================================

    @abstractmethod
    def save_plan(self, plan: TechnicalPlan, feature_id: str) -> Path:
        """
        Save technical implementation plan.

        Args:
            plan: TechnicalPlan model to save
            feature_id: Feature identifier

        Returns:
            Path to the saved file
        """
        pass

    @abstractmethod
    def load_plan(self, feature_id: str) -> Optional[TechnicalPlan]:
        """
        Load technical implementation plan.

        Args:
            feature_id: Feature identifier

        Returns:
            TechnicalPlan model if found, None otherwise
        """
        pass

    # =========================================================================
    # Task Breakdown
    # =========================================================================

    @abstractmethod
    def save_tasks(self, tasks: TaskBreakdown, feature_id: str) -> Path:
        """
        Save task breakdown.

        Args:
            tasks: TaskBreakdown model to save
            feature_id: Feature identifier

        Returns:
            Path to the saved file
        """
        pass

    @abstractmethod
    def load_tasks(self, feature_id: str) -> Optional[TaskBreakdown]:
        """
        Load task breakdown.

        Args:
            feature_id: Feature identifier

        Returns:
            TaskBreakdown model if found, None otherwise
        """
        pass

    # =========================================================================
    # Feature Management
    # =========================================================================

    @abstractmethod
    def list_features(self) -> list[str]:
        """
        List all feature identifiers in the project.

        Returns:
            List of feature IDs (e.g., ["001-auth", "002-payments"])
        """
        pass

    @abstractmethod
    def feature_exists(self, feature_id: str) -> bool:
        """
        Check if a feature exists.

        Args:
            feature_id: Feature identifier

        Returns:
            True if feature exists, False otherwise
        """
        pass

    @abstractmethod
    def get_feature_path(self, feature_id: str) -> Path:
        """
        Get the directory path for a feature.

        Args:
            feature_id: Feature identifier

        Returns:
            Path to the feature directory
        """
        pass

    @abstractmethod
    def create_feature(self, feature_id: str) -> Path:
        """
        Create a new feature directory.

        Args:
            feature_id: Feature identifier

        Returns:
            Path to the created directory
        """
        pass
