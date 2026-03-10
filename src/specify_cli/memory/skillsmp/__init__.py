"""
SkillsMP skill search integration.

Package initialization.
"""

from .api_client import SkillsMPAPIClient, SkillsMPError
from .api_key_storage import APIKeyStorage
from .github_fallback import GitHubSkillSearcher
from .skill_comparison import SkillComparator, ConflictResolver, SkillSelector
from .integration import SkillsMPIntegration

__all__ = [
    "SkillsMPAPIClient",
    "SkillsMPError",
    "APIKeyStorage",
    "GitHubSkillSearcher",
    "SkillComparator",
    "ConflictResolver",
    "SkillSelector",
    "SkillsMPIntegration"
]
