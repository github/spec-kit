"""
Technical planning for spec-kit.

This module provides tools to generate technical implementation plans
from feature specifications.
"""

from datetime import datetime
from typing import Optional

from speckit.llm import LiteLLMProvider
from speckit.schemas import Constitution, Specification, TechStack, TechnicalPlan
from speckit.storage.base import StorageBase
from speckit.templates import render_template


class TechnicalPlanner:
    """
    Generates technical implementation plans from specifications.

    The plan includes technology stack, architecture, components,
    file structure, and risk assessment.
    """

    def __init__(self, llm: LiteLLMProvider, storage: StorageBase):
        """
        Initialize technical planner.

        Args:
            llm: LLM provider for generation
            storage: Storage backend for persistence
        """
        self.llm = llm
        self.storage = storage

    def plan(
        self,
        specification: Specification,
        constitution: Optional[Constitution] = None,
        tech_stack: Optional[TechStack] = None,
        language: Optional[str] = None,
    ) -> TechnicalPlan:
        """
        Generate a technical plan from a specification.

        Args:
            specification: Specification to plan for
            constitution: Optional project constitution for constraints
            tech_stack: Optional technology constraints
            language: Optional output language (e.g., 'pt-br', 'es', 'en')

        Returns:
            Generated TechnicalPlan model
        """
        # Render prompt template (use mode='json' for datetime serialization)
        prompt = render_template(
            "plan.jinja2",
            specification=specification.model_dump(mode="json"),
            constitution=constitution.model_dump(mode="json") if constitution else None,
            tech_stack=tech_stack.model_dump(mode="json") if tech_stack else None,
            language=language,
        )

        # Generate plan using structured output
        plan = self.llm.complete_structured(
            prompt=prompt,
            response_model=TechnicalPlan,
            system="You are a software architect creating technical implementation plans.",
        )

        # Ensure feature_id is set correctly
        plan.feature_id = specification.feature_id
        plan.created_at = datetime.now()

        return plan

    async def plan_async(
        self,
        specification: Specification,
        constitution: Optional[Constitution] = None,
        tech_stack: Optional[TechStack] = None,
        language: Optional[str] = None,
    ) -> TechnicalPlan:
        """Async version of plan()."""
        prompt = render_template(
            "plan.jinja2",
            specification=specification.model_dump(mode="json"),
            constitution=constitution.model_dump(mode="json") if constitution else None,
            tech_stack=tech_stack.model_dump(mode="json") if tech_stack else None,
            language=language,
        )

        plan = await self.llm.complete_structured_async(
            prompt=prompt,
            response_model=TechnicalPlan,
            system="You are a software architect creating technical implementation plans.",
        )

        plan.feature_id = specification.feature_id
        plan.created_at = datetime.now()

        return plan
