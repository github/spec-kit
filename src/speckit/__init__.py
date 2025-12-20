"""
speckit - A Python library for spec-driven development with universal LLM support.

This library provides tools for the complete specification workflow:
- Constitution: Project-level principles and standards
- Specify: Generate feature specifications from natural language
- Clarify: Identify ambiguities and generate clarification questions
- Plan: Generate technical implementation plans
- Tasks: Generate implementation task breakdowns
- Analyze: Check consistency across artifacts
"""

from speckit.speckit import SpecKit
from speckit.config import LLMConfig, StorageConfig, SpecKitConfig
from speckit.schemas import (
    # Enums
    Priority,
    TaskStatus,
    PhaseType,
    FeatureStatus,
    # Workflow artifacts
    Constitution,
    UserStory,
    FunctionalRequirement,
    Entity,
    Specification,
    TechStack,
    ArchitectureComponent,
    TechnicalPlan,
    Phase,
    Task,
    TaskBreakdown,
    ClarificationQuestion,
    AnalysisReport,
)
from speckit.llm import LiteLLMProvider, LLMResponse

__version__ = "0.2.1"
__all__ = [
    # Main class
    "SpecKit",
    # Config
    "LLMConfig",
    "StorageConfig",
    "SpecKitConfig",
    # Enums
    "Priority",
    "TaskStatus",
    "PhaseType",
    "FeatureStatus",
    # Workflow artifacts
    "Constitution",
    "UserStory",
    "FunctionalRequirement",
    "Entity",
    "Specification",
    "TechStack",
    "ArchitectureComponent",
    "TechnicalPlan",
    "Phase",
    "Task",
    "TaskBreakdown",
    "ClarificationQuestion",
    "AnalysisReport",
    # LLM
    "LiteLLMProvider",
    "LLMResponse",
]
