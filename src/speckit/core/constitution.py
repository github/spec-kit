"""
Constitution management for spec-kit.

This module provides tools to create and manage project constitutions
that define guiding principles for development.
"""

from typing import Optional

from speckit.llm import LiteLLMProvider
from speckit.schemas import Constitution
from speckit.storage.base import StorageBase
from speckit.templates import render_template


class ConstitutionManager:
    """
    Manages project constitution creation and updates.

    The constitution defines project-level principles, standards, and
    constraints that guide all development decisions.
    """

    def __init__(self, llm: LiteLLMProvider, storage: StorageBase):
        """
        Initialize constitution manager.

        Args:
            llm: LLM provider for generation
            storage: Storage backend for persistence
        """
        self.llm = llm
        self.storage = storage

    def create(
        self,
        project_name: str,
        seed_principles: Optional[list[str]] = None,
        interactive: bool = False,
    ) -> Constitution:
        """
        Create a new project constitution.

        Args:
            project_name: Name of the project
            seed_principles: Optional initial principles to build on
            interactive: Whether to prompt for refinement

        Returns:
            Generated Constitution model
        """
        # Render prompt template
        prompt = render_template(
            "constitution.jinja2",
            project_name=project_name,
            seed_principles=seed_principles or [],
        )

        # Generate constitution using structured output
        constitution = self.llm.complete_structured(
            prompt=prompt,
            response_model=Constitution,
            system="You are a software architect helping establish project principles.",
        )

        # Ensure project name is set correctly
        constitution.project_name = project_name

        return constitution

    async def create_async(
        self,
        project_name: str,
        seed_principles: Optional[list[str]] = None,
        interactive: bool = False,
    ) -> Constitution:
        """Async version of create()."""
        prompt = render_template(
            "constitution.jinja2",
            project_name=project_name,
            seed_principles=seed_principles or [],
        )

        constitution = await self.llm.complete_structured_async(
            prompt=prompt,
            response_model=Constitution,
            system="You are a software architect helping establish project principles.",
        )

        constitution.project_name = project_name
        return constitution

    def load(self) -> Optional[Constitution]:
        """Load existing constitution from storage."""
        return self.storage.load_constitution()

    def save(self, constitution: Constitution) -> None:
        """Save constitution to storage."""
        self.storage.save_constitution(constitution)
