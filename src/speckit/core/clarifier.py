"""
Clarification engine for spec-kit.

This module provides tools to identify ambiguities in specifications
and generate clarification questions.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from speckit.llm import LiteLLMProvider
from speckit.schemas import ClarificationQuestion, Specification
from speckit.templates import render_template


class ClarificationQuestionList(BaseModel):
    """Response model for clarification questions."""

    questions: list[ClarificationQuestion]


class ClarificationEngine:
    """
    Identifies ambiguities and generates clarification questions.

    Analyzes specifications to find areas that need more detail
    or could be interpreted multiple ways.
    """

    def __init__(self, llm: LiteLLMProvider):
        """
        Initialize clarification engine.

        Args:
            llm: LLM provider for analysis
        """
        self.llm = llm

    def clarify(
        self,
        specification: Specification,
        max_questions: int = 5,
    ) -> tuple[Specification, list[ClarificationQuestion]]:
        """
        Identify clarification questions for a specification.

        Args:
            specification: Specification to analyze
            max_questions: Maximum questions to generate

        Returns:
            Tuple of (updated spec with clarifications_needed, questions list)
        """
        # Render prompt template (use mode='json' for datetime serialization)
        prompt = render_template(
            "clarify.jinja2",
            specification=specification.model_dump(mode="json"),
            max_questions=max_questions,
        )

        # Generate questions using structured output
        result = self.llm.complete_structured(
            prompt=prompt,
            response_model=ClarificationQuestionList,
            system="You are a senior analyst reviewing specifications for ambiguities.",
        )

        questions = result.questions

        # Update specification with clarifications needed
        if questions:
            specification.clarifications_needed = [q.question for q in questions]

        return specification, questions

    async def clarify_async(
        self,
        specification: Specification,
        max_questions: int = 5,
    ) -> tuple[Specification, list[ClarificationQuestion]]:
        """Async version of clarify()."""
        prompt = render_template(
            "clarify.jinja2",
            specification=specification.model_dump(mode="json"),
            max_questions=max_questions,
        )

        result = await self.llm.complete_structured_async(
            prompt=prompt,
            response_model=ClarificationQuestionList,
            system="You are a senior analyst reviewing specifications for ambiguities.",
        )

        questions = result.questions

        if questions:
            specification.clarifications_needed = [q.question for q in questions]

        return specification, questions

    def apply_answer(
        self,
        specification: Specification,
        question_id: str,
        answer: str,
    ) -> Specification:
        """
        Apply an answer to a clarification question.

        Args:
            specification: Specification to update
            question_id: ID of the question being answered
            answer: The answer to apply

        Returns:
            Updated specification with the clarification resolved
        """
        # Add to resolved clarifications
        specification.clarifications_resolved.append(
            {
                "question_id": question_id,
                "answer": answer,
                "answered_at": datetime.now().isoformat(),
            }
        )

        # Remove from needed clarifications (if present)
        # Note: This is a simplified implementation - in practice,
        # you might want to match question text or use IDs
        specification.clarifications_needed = [
            q for q in specification.clarifications_needed if question_id not in q
        ]

        return specification
