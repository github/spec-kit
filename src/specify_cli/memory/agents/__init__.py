"""
Agent Creation System - AgentForge patterns without OpenClaw.

Provides template generation, auto-improvement, handoff, and skill workflows.
"""

from .template_generator import AgentTemplateGenerator
from .auto_improvement import AutoImprovementSystem
from .auto_handoff import AutoHandoffSystem
from .skill_workflow import SkillCreationWorkflow
from .agent_templates import get_template, list_templates, get_all_templates

__all__ = [
    "AgentTemplateGenerator",
    "AutoImprovementSystem",
    "AutoHandoffSystem",
    "SkillCreationWorkflow",
    "get_template",
    "list_templates",
    "get_all_templates",
]
