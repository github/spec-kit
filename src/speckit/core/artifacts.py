"""
Extended artifacts generation for spec-kit.

This module provides tools to generate additional artifacts beyond
the core workflow: data models, research findings, API contracts,
quality checklists, and quickstart guides.
"""

from datetime import datetime
from typing import Optional

from speckit.llm import LiteLLMProvider
from speckit.schemas import (
    APIContract,
    DataModel,
    QualityChecklist,
    QuickstartGuide,
    ResearchFindings,
    Specification,
    TechnicalPlan,
)
from speckit.storage.base import StorageBase
from speckit.templates import render_template


class ArtifactGenerator:
    """
    Generates extended artifacts for feature development.

    Provides LLM-powered generation for:
    - Data models (database schemas)
    - Research findings (technology decisions)
    - API contracts (endpoint specifications)
    - Quality checklists (specification validation)
    - Quickstart guides (developer onboarding)
    """

    def __init__(self, llm: LiteLLMProvider, storage: StorageBase):
        """
        Initialize artifact generator.

        Args:
            llm: LLM provider for generation
            storage: Storage backend for persistence
        """
        self.llm = llm
        self.storage = storage

    # =========================================================================
    # Data Model Generation
    # =========================================================================

    def generate_data_model(
        self,
        specification: Specification,
        plan: TechnicalPlan,
        language: Optional[str] = None,
    ) -> DataModel:
        """
        Generate database schema and data model.

        Args:
            specification: Feature specification
            plan: Technical implementation plan
            language: Optional output language (e.g., 'pt-br', 'es', 'en')

        Returns:
            Generated DataModel with entities and fields
        """
        prompt = render_template(
            "data_model.jinja2",
            specification=specification.model_dump(mode="json"),
            plan=plan.model_dump(mode="json"),
            language=language,
        )

        data_model = self.llm.complete_structured(
            prompt=prompt,
            response_model=DataModel,
            system="You are a database architect creating data model specifications.",
        )

        # Ensure IDs are set correctly
        data_model.feature_id = specification.feature_id
        data_model.feature_name = specification.feature_name
        data_model.created_at = datetime.now()

        return data_model

    async def generate_data_model_async(
        self,
        specification: Specification,
        plan: TechnicalPlan,
        language: Optional[str] = None,
    ) -> DataModel:
        """Async version of generate_data_model()."""
        prompt = render_template(
            "data_model.jinja2",
            specification=specification.model_dump(mode="json"),
            plan=plan.model_dump(mode="json"),
            language=language,
        )

        data_model = await self.llm.complete_structured_async(
            prompt=prompt,
            response_model=DataModel,
            system="You are a database architect creating data model specifications.",
        )

        data_model.feature_id = specification.feature_id
        data_model.feature_name = specification.feature_name
        data_model.created_at = datetime.now()

        return data_model

    # =========================================================================
    # Research Findings Generation
    # =========================================================================

    def generate_research(
        self,
        plan: TechnicalPlan,
        language: Optional[str] = None,
    ) -> ResearchFindings:
        """
        Generate technology research and decision documentation.

        Args:
            plan: Technical implementation plan
            language: Optional output language (e.g., 'pt-br', 'es', 'en')

        Returns:
            Generated ResearchFindings with technology decisions
        """
        prompt = render_template(
            "research.jinja2",
            plan=plan.model_dump(mode="json"),
            language=language,
        )

        research = self.llm.complete_structured(
            prompt=prompt,
            response_model=ResearchFindings,
            system="You are a technology researcher documenting architectural decisions.",
        )

        # Ensure IDs are set correctly
        research.feature_id = plan.feature_id
        research.created_at = datetime.now()

        return research

    async def generate_research_async(
        self,
        plan: TechnicalPlan,
        language: Optional[str] = None,
    ) -> ResearchFindings:
        """Async version of generate_research()."""
        prompt = render_template(
            "research.jinja2",
            plan=plan.model_dump(mode="json"),
            language=language,
        )

        research = await self.llm.complete_structured_async(
            prompt=prompt,
            response_model=ResearchFindings,
            system="You are a technology researcher documenting architectural decisions.",
        )

        research.feature_id = plan.feature_id
        research.created_at = datetime.now()

        return research

    # =========================================================================
    # API Contract Generation
    # =========================================================================

    def generate_api_contract(
        self,
        specification: Specification,
        plan: TechnicalPlan,
        language: Optional[str] = None,
    ) -> APIContract:
        """
        Generate API specification with endpoints and schemas.

        Args:
            specification: Feature specification
            plan: Technical implementation plan
            language: Optional output language (e.g., 'pt-br', 'es', 'en')

        Returns:
            Generated APIContract with endpoint definitions
        """
        prompt = render_template(
            "api_contract.jinja2",
            specification=specification.model_dump(mode="json"),
            plan=plan.model_dump(mode="json"),
            language=language,
        )

        contract = self.llm.complete_structured(
            prompt=prompt,
            response_model=APIContract,
            system="You are an API architect creating formal API specifications.",
        )

        # Ensure IDs are set correctly
        contract.feature_id = specification.feature_id
        contract.feature_name = specification.feature_name
        contract.created_at = datetime.now()

        return contract

    async def generate_api_contract_async(
        self,
        specification: Specification,
        plan: TechnicalPlan,
        language: Optional[str] = None,
    ) -> APIContract:
        """Async version of generate_api_contract()."""
        prompt = render_template(
            "api_contract.jinja2",
            specification=specification.model_dump(mode="json"),
            plan=plan.model_dump(mode="json"),
            language=language,
        )

        contract = await self.llm.complete_structured_async(
            prompt=prompt,
            response_model=APIContract,
            system="You are an API architect creating formal API specifications.",
        )

        contract.feature_id = specification.feature_id
        contract.feature_name = specification.feature_name
        contract.created_at = datetime.now()

        return contract

    # =========================================================================
    # Quality Checklist Generation
    # =========================================================================

    def generate_checklist(
        self,
        specification: Specification,
        language: Optional[str] = None,
    ) -> QualityChecklist:
        """
        Generate quality validation checklist for specification.

        Args:
            specification: Feature specification to validate
            language: Optional output language (e.g., 'pt-br', 'es', 'en')

        Returns:
            Generated QualityChecklist with validation items
        """
        prompt = render_template(
            "checklist.jinja2",
            specification=specification.model_dump(mode="json"),
            language=language,
        )

        checklist = self.llm.complete_structured(
            prompt=prompt,
            response_model=QualityChecklist,
            system="You are a quality assurance specialist validating specification quality.",
        )

        # Ensure IDs are set correctly
        checklist.feature_id = specification.feature_id
        checklist.feature_name = specification.feature_name
        checklist.created_at = datetime.now()

        return checklist

    async def generate_checklist_async(
        self,
        specification: Specification,
        language: Optional[str] = None,
    ) -> QualityChecklist:
        """Async version of generate_checklist()."""
        prompt = render_template(
            "checklist.jinja2",
            specification=specification.model_dump(mode="json"),
            language=language,
        )

        checklist = await self.llm.complete_structured_async(
            prompt=prompt,
            response_model=QualityChecklist,
            system="You are a quality assurance specialist validating specification quality.",
        )

        checklist.feature_id = specification.feature_id
        checklist.feature_name = specification.feature_name
        checklist.created_at = datetime.now()

        return checklist

    # =========================================================================
    # Quickstart Guide Generation
    # =========================================================================

    def generate_quickstart(
        self,
        specification: Specification,
        plan: TechnicalPlan,
        language: Optional[str] = None,
    ) -> QuickstartGuide:
        """
        Generate quickstart guide for developers.

        Args:
            specification: Feature specification
            plan: Technical implementation plan
            language: Optional output language (e.g., 'pt-br', 'es', 'en')

        Returns:
            Generated QuickstartGuide with setup instructions
        """
        prompt = render_template(
            "quickstart.jinja2",
            specification=specification.model_dump(mode="json"),
            plan=plan.model_dump(mode="json"),
            language=language,
        )

        quickstart = self.llm.complete_structured(
            prompt=prompt,
            response_model=QuickstartGuide,
            system="You are a technical writer creating developer onboarding documentation.",
        )

        # Ensure IDs are set correctly
        quickstart.feature_id = specification.feature_id
        quickstart.feature_name = specification.feature_name
        quickstart.created_at = datetime.now()

        return quickstart

    async def generate_quickstart_async(
        self,
        specification: Specification,
        plan: TechnicalPlan,
        language: Optional[str] = None,
    ) -> QuickstartGuide:
        """Async version of generate_quickstart()."""
        prompt = render_template(
            "quickstart.jinja2",
            specification=specification.model_dump(mode="json"),
            plan=plan.model_dump(mode="json"),
            language=language,
        )

        quickstart = await self.llm.complete_structured_async(
            prompt=prompt,
            response_model=QuickstartGuide,
            system="You are a technical writer creating developer onboarding documentation.",
        )

        quickstart.feature_id = specification.feature_id
        quickstart.feature_name = specification.feature_name
        quickstart.created_at = datetime.now()

        return quickstart
