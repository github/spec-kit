"""
AI Importance Classifier - Multi-factor scoring for memory routing.

Calculates importance scores (0.0-1.0) to route content
to appropriate memory files (architecture.md, patterns.md, or projects-log.md).
"""

from typing import Dict, Optional
import re


class AIImportanceClassifier:
    """Classifies content importance for memory routing decisions."""

    def __init__(self):
        """Initialize AI importance classifier."""
        # Semantic importance keywords
        self.high_importance_keywords = [
            "architecture", "design", "infrastructure", "scalability",
            "security", "performance", "critical", "strategic",
            "архитектура", "дизайн", "инфраструктура", "масштабируемость",
            "безопасность", "производительность", "критический", "стратегический"
        ]

        self.medium_importance_keywords = [
            "pattern", "approach", "method", "implementation",
            "refactor", "optimization", "improvement",
            "паттерн", "подход", "метод", "реализация",
            "рефакторинг", "оптимизация", "улучшение"
        ]

        # Context complexity indicators
        self.complexity_indicators = [
            "alternatives", "options", "considered", "evaluated",
            "权衡", "варианты", "рассмотрели", "оценили"
        ]

    def calculate_importance(
        self,
        content: str,
        explicit_markers: Optional[list] = None
    ) -> Dict[str, any]:
        """Calculate importance score for content routing.

        Args:
            content: Content to analyze
            explicit_markers: Explicit user markers that override AI

        Returns:
            Dict with score, routing_target, confidence, and factors
        """
        # Check explicit user markers first (override AI)
        if explicit_markers:
            return self._apply_explicit_markers(explicit_markers)

        # Multi-factor scoring
        semantic_score = self._analyze_semantic_importance(content)
        complexity_score = self._analyze_context_complexity(content)
        impact_score = self._analyze_technical_impact(content)
        repeatability_score = self._analyze_repeatability(content)

        # Weighted average
        weights = {"semantic": 0.3, "complexity": 0.2, "impact": 0.3, "repeatability": 0.2}
        final_score = (
            semantic_score * weights["semantic"] +
            complexity_score * weights["complexity"] +
            impact_score * weights["impact"] +
            repeatability_score * weights["repeatability"]
        )

        # Determine routing target
        if final_score > 0.7:
            routing_target = "architecture.md"
        elif final_score > 0.4:
            routing_target = "patterns.md"
        else:
            routing_target = "projects-log.md"

        return {
            "score": round(final_score, 2),
            "routing_target": routing_target,
            "confidence": self._calculate_confidence(semantic_score, complexity_score, impact_score, repeatability_score),
            "factors": {
                "semantic": round(semantic_score, 2),
                "complexity": round(complexity_score, 2),
                "impact": round(impact_score, 2),
                "repeatability": round(repeatability_score, 2)
            }
        }

    def _apply_explicit_markers(self, markers: list) -> Dict[str, any]:
        """Apply explicit user markers (override AI scoring).

        Args:
            markers: List of explicit markers from user

        Returns:
            Dict with score=1.0 and appropriate routing
        """
        # Marker → target mapping
        marker_map = {
            "документируй это в architecture.md": "architecture.md",
            "architecture.md": "architecture.md",
            "запомни это как паттерн": "patterns.md",
            "patterns.md": "patterns.md",
            "ошибка важна": "lessons.md",
        }

        for marker in markers:
            marker_lower = marker.lower()
            for key, target in marker_map.items():
                if key in marker_lower:
                    return {
                        "score": 1.0,
                        "routing_target": target,
                        "confidence": 1.0,
                        "factors": {},
                        "explicit_marker": marker
                    }

        # Default if marker not recognized
        return {
            "score": 1.0,
            "routing_target": "projects-log.md",
            "confidence": 0.5,
            "factors": {},
            "explicit_marker": ", ".join(markers)
        }

    def _analyze_semantic_importance(self, content: str) -> float:
        """Analyze semantic importance (0.0-1.0).

        Args:
            content: Content to analyze

        Returns:
            Semantic score
        """
        content_lower = content.lower()
        score = 0.0

        # High importance keywords
        high_matches = sum(1 for kw in self.high_importance_keywords if kw in content_lower)
        score += min(high_matches * 0.15, 0.5)

        # Medium importance keywords
        medium_matches = sum(1 for kw in self.medium_importance_keywords if kw in content_lower)
        score += min(medium_matches * 0.05, 0.2)

        return min(score, 1.0)

    def _analyze_context_complexity(self, content: str) -> float:
        """Analyze context complexity (0.0-1.0).

        Args:
            content: Content to analyze

        Returns:
            Complexity score
        """
        content_lower = content.lower()

        # Discussion length (longer = more complex)
        word_count = len(content.split())
        if word_count > 500:
            score = 0.8
        elif word_count > 200:
            score = 0.5
        else:
            score = 0.2

        # Complexity indicators
        complexity_matches = sum(1 for kw in self.complexity_indicators if kw in content_lower)
        score += min(complexity_matches * 0.05, 0.2)

        return min(score, 1.0)

    def _analyze_technical_impact(self, content: str) -> float:
        """Analyze technical impact (0.0-1.0).

        Args:
            content: Content to analyze

        Returns:
            Impact score
        """
        content_lower = content.lower()

        # Core architecture keywords
        core_keywords = [
            "database schema", "api design", "authentication", "authorization",
            "data model", "migration", "integration", "infrastructure",
            "база данных", "api дизайн", "аутентификация", "авторизация",
            "модель данных", "миграция", "интеграция", "инфраструктура"
        ]

        matches = sum(1 for kw in core_keywords if kw in content_lower)
        return min(matches * 0.15, 1.0)

    def _analyze_repeatability(self, content: str) -> float:
        """Analyze repeatability (0.0-1.0).

        Novel content = higher score, common patterns = lower score.

        Args:
            content: Content to analyze

        Returns:
            Repeatability score
        """
        content_lower = content.lower()

        # Pattern keywords (indicates reusable)
        pattern_keywords = ["pattern", "template", "reusable", "common", "standard"]
        pattern_matches = sum(1 for kw in pattern_keywords if kw in content_lower)

        # Novelty keywords (indicates new/unique)
        novelty_keywords = ["new", "novel", "unique", "first time", "initial"]
        novelty_matches = sum(1 for kw in novelty_keywords if kw in content_lower)

        # More novel = higher importance for architecture
        score = 0.5 + (novel_matches * 0.2) - (pattern_matches * 0.1)
        return max(0.0, min(score, 1.0))

    def _calculate_confidence(
        self,
        semantic: float,
        complexity: float,
        impact: float,
        repeatability: float
    ) -> float:
        """Calculate confidence in the classification.

        Args:
            semantic: Semantic score
            complexity: Complexity score
            impact: Impact score
            repeatability: Repeatability score

        Returns:
            Confidence score (0.0-1.0)
        """
        # High variance = low confidence
        scores = [semantic, complexity, impact, repeatability]
        variance = max(scores) - min(scores)

        if variance < 0.3:
            return 0.9  # High confidence
        elif variance < 0.6:
            return 0.6  # Medium confidence
        else:
            return 0.3  # Low confidence

    def classify_explicit_markers(self, text: str) -> list:
        """Extract explicit user markers from text.

        Args:
            text: Text to search for markers

        Returns:
            List of found markers
        """
        markers = []

        # Common explicit marker patterns
        patterns = [
            r"(?:запиши|документируй|запомни).+?(?:architecture\.md|patterns?\.md)",
            r"(?:ошибка|lesson).+?важн",
            r"это\s+(?:важно|критично)",
            r"#autodoc",
            r"#documentation",
        ]

        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            markers.extend(matches)

        return list(set(markers))  # Deduplicate
