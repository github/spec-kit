"""
Skill comparison and conflict resolution for SkillsMP integration.

Compares similar skills and helps resolve conflicts when multiple options exist.
"""

from typing import List, Dict, Any, Optional, Tuple
from difflib import SequenceMatcher
from datetime import datetime

from ..logging import get_logger


class SkillComparator:
    """Compares and ranks skills based on relevance."""

    def __init__(self):
        """Initialize skill comparator."""
        self.logger = get_logger()

    def calculate_similarity(
        self,
        query: str,
        skill: Dict[str, Any]
    ) -> float:
        """Calculate similarity between query and skill.

        Args:
            query: Search query
            skill: Skill data

        Returns:
            Similarity score (0.0 to 1.0)
        """
        query_lower = query.lower()

        # Factors:
        # 1. Title match (40%)
        # 2. Description match (30%)
        # 3. Tags match (20%)
        # 4. Stars/reputation (10%)

        score = 0.0

        # Title similarity
        title = skill.get("title", "").lower()
        title_sim = SequenceMatcher(None, query_lower, title).ratio()
        score += title_sim * 0.4

        # Description similarity
        description = skill.get("description", "").lower()
        desc_sim = SequenceMatcher(None, query_lower, description).ratio()
        score += desc_sim * 0.3

        # Tags match
        tags = skill.get("tags", [])
        if tags:
            query_words = set(query_lower.split())
            tag_words = set(" ".join(tags).lower().split())
            tag_overlap = len(query_words & tag_words)
            score += min(tag_overlap / len(query_words), 1.0) * 0.2

        # Reputation (stars)
        stars = skill.get("github_stars", 0)
        normalized_stars = min(stars / 100, 1.0)  # Cap at 100 stars
        score += normalized_stars * 0.1

        return min(score, 1.0)

    def rank_skills(
        self,
        query: str,
        skills: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Rank skills by relevance.

        Args:
            query: Search query
            skills: List of skills

        Returns:
            Ranked list with similarity scores
        """
        scored = []

        for skill in skills:
            similarity = self.calculate_similarity(query, skill)
            skill_with_score = {**skill, "similarity": similarity}
            scored.append(skill_with_score)

        # Sort by similarity
        scored.sort(key=lambda x: x["similarity"], reverse=True)

        return scored

    def filter_duplicates(
        self,
        skills: List[Dict[str, Any]],
        threshold: float = 0.9
    ) -> List[Dict[str, Any]]:
        """Filter out duplicate skills.

        Args:
            skills: List of skills
            threshold: Similarity threshold for duplicates

        Returns:
            Filtered list
        """
        unique = []

        for skill in skills:
            is_duplicate = False

            for existing in unique:
                # Check title similarity
                title_sim = SequenceMatcher(
                    None,
                    skill.get("title", ""),
                    existing.get("title", "")
                ).ratio()

                # Check repository similarity
                repo_a = skill.get("github_repo", "")
                repo_b = existing.get("github_repo", "")

                if repo_a and repo_b and repo_a == repo_b:
                    is_duplicate = True
                    break

                if title_sim > threshold:
                    # Keep the one with higher similarity
                    if skill.get("similarity", 0) > existing.get("similarity", 0):
                        # Replace existing
                        unique[unique.index(existing)] = skill
                    is_duplicate = True
                    break

            if not is_duplicate:
                unique.append(skill)

        return unique


class ConflictResolver:
    """Resolves conflicts when multiple similar skills exist."""

    def __init__(self):
        """Initialize conflict resolver."""
        self.logger = get_logger()

    def resolve_selection(
        self,
        skills: List[Dict[str, Any]],
        query: str
    ) -> Dict[str, Any]:
        """Resolve which skill to select from multiple options.

        Args:
            skills: List of similar skills
            query: Original search query

        Returns:
            Selected skill with rationale
        """
        if len(skills) == 1:
            return {
                "skill": skills[0],
                "action": "selected",
                "rationale": "Only match"
            }

        # Multiple options - rank and select
        comparator = SkillComparator()
        ranked = comparator.rank_skills(query, skills)

        best = ranked[0]

        # Determine action
        if best["similarity"] > 0.8:
            action = "auto_selected"
            rationale = f"High similarity ({best['similarity']:.2f})"
        elif len(ranked) > 3:
            action = "top_candidate"
            rationale = f"{len(ranked)} options found, selected best match"
        else:
            action = "needs_review"
            rationale = f"{len(ranked)} similar options, manual review recommended"

        return {
            "skill": best,
            "action": action,
            "rationale": rationale,
            "alternatives": ranked[1:3] if len(ranked) > 1 else []
        }

    def compare_with_github(
        self,
        skillsmp_skill: Dict[str, Any],
        github_skill: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Compare SkillsMP skill with GitHub skill.

        Args:
            skillsmp_skill: Skill from SkillsMP
            github_skill: Skill from GitHub search

        Returns:
            Comparison result
        """
        factors = {
            "stars_sm": skillsmp_skill.get("github_stars", 0),
            "stars_gh": github_skill.get("stargazers_count", 0),
            "updated_sm": skillsmp_skill.get("updated_at", ""),
            "updated_gh": github_skill.get("updated_at", ""),
            "description_match": SequenceMatcher(
                None,
                skillsmp_skill.get("description", ""),
                github_skill.get("description", "")
            ).ratio()
        }

        # Determine preferred source
        preferred = "skillsmp"

        if factors["stars_gh"] > factors["stars_sm"] * 1.5:
            preferred = "github"
        elif factors["description_match"] < 0.5:
            # Descriptions don't match, might be different skills
            preferred = "both"

        return {
            "preferred": preferred,
            "factors": factors,
            "recommendation": self._get_recommendation(preferred, factors)
        }

    def _get_recommendation(
        self,
        preferred: str,
        factors: Dict[str, Any]
    ) -> str:
        """Get recommendation text.

        Args:
            preferred: Preferred source
            factors: Comparison factors

        Returns:
            Recommendation text
        """
        if preferred == "skillsmp":
            return f"SkillsMP version recommended (verified, {factors['stars_sm']} stars)"
        elif preferred == "github":
            return f"GitHub version recommended (more popular: {factors['stars_gh']} vs {factors['stars_sm']} stars)"
        else:
            return "Both versions relevant - review manually"


class SkillSelector:
    """High-level skill selection with conflict resolution."""

    def __init__(self):
        """Initialize skill selector."""
        self.logger = get_logger()
        self.comparator = SkillComparator()
        self.resolver = ConflictResolver()

    def select_best_skills(
        self,
        query: str,
        skillsmp_skills: List[Dict[str, Any]],
        github_skills: Optional[List[Dict[str, Any]]] = None,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Select best skills from multiple sources.

        Args:
            query: Search query
            skillsmp_skills: Skills from SkillsMP API
            github_skills: Skills from GitHub (optional)
            limit: Max results

        Returns:
            Selected skills with metadata
        """
        # Rank SkillsMP skills
        ranked_sm = self.comparator.rank_skills(query, skillsmp_skills)

        # Combine with GitHub if provided
        if github_skills:
            ranked_gh = self.comparator.rank_skills(query, github_skills)

            # Interleave based on ranking
            combined = []
            i = j = 0
            while len(combined) < limit and (i < len(ranked_sm) or j < len(ranked_gh)):
                if i < len(ranked_sm) and (j >= len(ranked_gh) or ranked_sm[i]["similarity"] >= ranked_gh[j]["similarity"]):
                    combined.append({**ranked_sm[i], "source": "skillsmp"})
                    i += 1
                else:
                    combined.append({**ranked_gh[j], "source": "github"})
                    j += 1

            return combined[:limit]

        # Return only SkillsMP
        return [{**s, "source": "skillsmp"} for s in ranked_sm[:limit]]

    def detect_conflicts(
        self,
        skills: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Detect potential conflicts in skill list.

        Args:
            skills: List of skills

        Returns:
            List of conflict groups
        """
        conflicts = []
        processed = set()

        for i, skill1 in enumerate(skills):
            if i in processed:
                continue

            group = [i]

            for j, skill2 in enumerate(skills[i+1:], start=i+1):
                # Check for similarity
                title_sim = SequenceMatcher(
                    None,
                    skill1.get("title", ""),
                    skill2.get("title", "")
                ).ratio()

                if title_sim > 0.7:
                    group.append(j)
                    processed.add(j)

            if len(group) > 1:
                conflicts.append({
                    "indices": group,
                    "skills": [skills[k] for k in group],
                    "similarity_range": (
                        min(s.get("similarity", 0) for s in [skills[k] for k in group]),
                        max(s.get("similarity", 0) for s in [skills[k] for k in group])
                    )
                })

        return conflicts
