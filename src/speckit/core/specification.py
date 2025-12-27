"""
Specification generation for spec-kit.

This module provides tools to generate feature specifications from
natural language descriptions.
"""

import re
from datetime import datetime
from typing import Optional

from speckit.llm import LiteLLMProvider
from speckit.schemas import Constitution, Specification
from speckit.storage.base import StorageBase
from speckit.templates import render_template


class SpecificationBuilder:
    """
    Generates feature specifications from natural language descriptions.

    The specification includes user stories, functional requirements,
    entities, constraints, and success criteria.
    """

    def __init__(self, llm: LiteLLMProvider, storage: StorageBase):
        """
        Initialize specification builder.

        Args:
            llm: LLM provider for generation
            storage: Storage backend for persistence
        """
        self.llm = llm
        self.storage = storage

    def generate(
        self,
        feature_description: str,
        feature_id: Optional[str] = None,
        constitution: Optional[Constitution] = None,
        language: Optional[str] = None,
    ) -> Specification:
        """
        Generate a specification from natural language.

        Args:
            feature_description: Natural language description of the feature
            feature_id: Optional custom ID (auto-generated if not provided)
            constitution: Optional project constitution for context
            language: Optional output language (e.g., 'pt-br', 'es', 'en')

        Returns:
            Generated Specification model
        """
        # Auto-generate feature ID if not provided
        if feature_id is None:
            feature_id = self._generate_feature_id(feature_description)

        # Render prompt template
        prompt = render_template(
            "specification.jinja2",
            feature_description=feature_description,
            feature_id=feature_id,
            constitution=constitution,
            language=language,
        )

        # Generate specification using structured output
        spec = self.llm.complete_structured(
            prompt=prompt,
            response_model=Specification,
            system="You are a product manager creating detailed feature specifications.",
        )

        # Ensure IDs are set correctly
        spec.feature_id = feature_id
        spec.created_at = datetime.now()

        return spec

    async def generate_async(
        self,
        feature_description: str,
        feature_id: Optional[str] = None,
        constitution: Optional[Constitution] = None,
        language: Optional[str] = None,
    ) -> Specification:
        """Async version of generate()."""
        if feature_id is None:
            feature_id = self._generate_feature_id(feature_description)

        prompt = render_template(
            "specification.jinja2",
            feature_description=feature_description,
            feature_id=feature_id,
            constitution=constitution,
            language=language,
        )

        spec = await self.llm.complete_structured_async(
            prompt=prompt,
            response_model=Specification,
            system="You are a product manager creating detailed feature specifications.",
        )

        spec.feature_id = feature_id
        spec.created_at = datetime.now()

        return spec

    def _generate_feature_id(self, description: str) -> str:
        """Generate a feature ID from the description."""
        # Get existing features to determine next number
        existing = self.storage.list_features()
        next_num = len(existing) + 1

        # Extract key words for slug
        words = description.lower().split()[:3]
        slug = "-".join(re.sub(r"[^a-z0-9]", "", word) for word in words if word)

        return f"{next_num:03d}-{slug}"
