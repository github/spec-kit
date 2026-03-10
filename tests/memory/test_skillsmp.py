"""
Tests for Phase 6: SkillsMP Search functionality.

Tests for API client, GitHub fallback, skill comparison, and integration.
"""

import pytest
import tempfile
import json
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

from specify_cli.memory.skillsmp.api_client import SkillsMPAPIClient, SkillsMPError
from specify_cli.memory.skillsmp.api_key_storage import APIKeyStorage
from specify_cli.memory.skillsmp.github_fallback import GitHubSkillSearcher
from specify_cli.memory.skillsmp.skill_comparison import SkillComparator, ConflictResolver, SkillSelector
from specify_cli.memory.skillsmp.integration import SkillsMPIntegration


class TestSkillsMPAPIClient:
    """Test SkillsMP API client."""

    def test_client_initialization(self):
        """Test client initialization."""
        client = SkillsMPAPIClient()

        assert client.api_key is None
        assert client.daily_limit == 500

    def test_client_with_api_key(self):
        """Test client with API key."""
        client = SkillsMPAPIClient(api_key="test_key_123")

        assert client.api_key == "test_key_123"
        assert "Authorization" in client.session.headers

    def test_rate_limiting(self):
        """Test rate limiting."""
        client = SkillsMPAPIClient()
        client.daily_remaining = 1
        client.daily_limit = 5

        # Should allow request
        assert client._check_rate_limit() is True

        # Set to 0 (exhausted)
        client.daily_remaining = 0

        # Should block when exhausted
        assert client._check_rate_limit() is False


class TestAPIKeyStorage:
    """Test API key storage."""

    def test_store_and_retrieve_key(self):
        """Test storing and retrieving API key."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = APIKeyStorage()
            storage.storage_dir = Path(tmpdir)

            # Store key
            assert storage.store_api_key("test_api_key_12345") is True

            # Retrieve key
            key = storage.get_api_key()
            assert key == "test_api_key_12345"

    def test_has_api_key(self):
        """Test checking if API key exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = APIKeyStorage()
            storage.storage_dir = Path(tmpdir)

            # Clear any existing key from keyring (cleanup from previous tests)
            try:
                storage.delete_api_key()
            except:
                pass

            # Now check for non-existence
            assert storage.has_api_key() is False

            storage.store_api_key("test_key")
            assert storage.has_api_key() is True

    def test_delete_api_key(self):
        """Test deleting API key."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = APIKeyStorage()
            storage.storage_dir = Path(tmpdir)

            storage.store_api_key("test_key")
            assert storage.delete_api_key() is True
            assert storage.has_api_key() is False


class TestGitHubSkillSearcher:
    """Test GitHub fallback searcher."""

    def test_initialization(self):
        """Test initialization."""
        searcher = GitHubSkillSearcher()

        assert searcher.rate_limit == 60  # Unauthenticated

    def test_with_token(self):
        """Test with GitHub token."""
        searcher = GitHubSkillSearcher(token="ghp_test_token")

        assert searcher.rate_limit == 5000
        assert "Authorization" in searcher.session.headers

    def test_parse_github_result(self):
        """Test parsing GitHub result."""
        searcher = GitHubSkillSearcher()

        item = {
            "name": "test-agent",
            "path": "agents/test-agent.py",
            "repository": {
                "full_name": "user/test-repo",
                "description": "Test agent",
                "stargazers_count": 42,
                "language": "Python",
                "updated_at": "2025-01-01T00:00:00Z",
                "html_url": "https://github.com/user/test-repo"
            }
        }

        skill = searcher._parse_github_result(item)

        assert skill is not None
        assert skill["title"] == "test-agent"
        assert skill["github_stars"] == 42
        assert skill["source"] == "github"

    def test_parse_github_result_skip_non_skill(self):
        """Test skipping non-skill results."""
        searcher = GitHubSkillSearcher()

        item = {
            "name": "README.md",
            "path": "README.md",
            "repository": {
                "full_name": "user/repo",
                "description": "Project readme"
            }
        }

        skill = searcher._parse_github_result(item)

        assert skill is None


class TestSkillComparator:
    """Test skill comparison."""

    def test_calculate_similarity(self):
        """Test similarity calculation."""
        comparator = SkillComparator()

        skill = {
            "title": "Python Agent for File Operations",
            "description": "Agent that handles file operations",
            "tags": ["python", "agent", "files"],
            "github_stars": 50
        }

        score = comparator.calculate_similarity("python file agent", skill)

        assert 0.0 <= score <= 1.0
        assert score > 0.3  # Should have decent similarity

    def test_rank_skills(self):
        """Test skill ranking."""
        comparator = SkillComparator()

        skills = [
            {"title": "Python Agent", "github_stars": 10},
            {"title": "Python Agent", "github_stars": 100},  # Higher stars
            {"title": "Java Agent", "github_stars": 50}
        ]

        query = "python agent"
        ranked = comparator.rank_skills(query, skills)

        assert len(ranked) == 3
        assert ranked[0]["github_stars"] >= ranked[1]["github_stars"]
        assert "similarity" in ranked[0]

    def test_filter_duplicates(self):
        """Test duplicate filtering."""
        comparator = SkillComparator()

        skills = [
            {"title": "Agent", "github_repo": "user/repo1", "similarity": 0.8},
            {"title": "Agent", "github_repo": "user/repo1", "similarity": 0.9},
            {"title": "Agent Clone", "github_repo": "user/repo2", "similarity": 0.7}
        ]

        filtered = comparator.filter_duplicates(skills, threshold=0.8)

        # Should remove one duplicate
        assert len(filtered) <= len(skills)


class TestConflictResolver:
    """Test conflict resolution."""

    def test_resolve_selection_single(self):
        """Test resolving single match."""
        resolver = ConflictResolver()

        skills = [{"title": "Test Skill", "similarity": 0.9}]

        result = resolver.resolve_selection(skills, "test")

        assert result["action"] in ["selected", "auto_selected"]
        assert result["skill"]["title"] == "Test Skill"

    def test_resolve_selection_multiple(self):
        """Test resolving multiple matches."""
        resolver = ConflictResolver()

        skills = [
            {"title": "Skill A", "similarity": 0.9},
            {"title": "Skill B", "similarity": 0.7}
        ]

        result = resolver.resolve_selection(skills, "test")

        assert result["skill"]["title"] == "Skill A"  # Highest similarity
        assert len(result["alternatives"]) > 0

    def test_compare_with_github(self):
        """Test GitHub comparison."""
        resolver = ConflictResolver()

        sm_skill = {
            "github_stars": 50,
            "updated_at": "2025-01-01"
        }

        gh_skill = {
            "stargazers_count": 100,
            "updated_at": "2025-01-01"
        }

        result = resolver.compare_with_github(sm_skill, gh_skill)

        assert "preferred" in result
        assert "factors" in result


class TestSkillSelector:
    """Test skill selection."""

    def test_select_best_skills(self):
        """Test selecting best skills."""
        selector = SkillSelector()

        sm_skills = [
            {"title": "Python Agent", "similarity": 0.9},
            {"title": "Java Agent", "similarity": 0.7}
        ]

        gh_skills = [
            {"title": "Python Agent", "similarity": 0.85}
        ]

        selected = selector.select_best_skills(
            "python agent",
            sm_skills,
            gh_skills,
            limit=2
        )

        assert len(selected) > 0
        assert all("source" in s for s in selected)

    def test_detect_conflicts(self):
        """Test conflict detection."""
        selector = SkillSelector()

        skills = [
            {"title": "Python Agent", "github_repo": "user/repo1", "similarity": 0.8},
            {"title": "Python Agent", "github_repo": "user/repo2", "similarity": 0.75},
            {"title": "Different Agent", "similarity": 0.5}
        ]

        conflicts = selector.detect_conflicts(skills)

        # Should detect conflict between two "Python Agent" skills
        assert len(conflicts) >= 1


class TestSkillsMPIntegration:
    """Test unified SkillsMP integration."""

    def test_initialization(self):
        """Test integration initialization."""
        integration = SkillsMPIntegration()

        assert integration.skillsmp_client is None  # No API key
        assert integration.github_searcher is None  # No GitHub token

    def test_with_api_key(self):
        """Test with API key."""
        with tempfile.TemporaryDirectory() as tmpdir:
            integration = SkillsMPIntegration(
                api_key="test_key",
                global_home=Path(tmpdir)
            )

            assert integration.api_key == "test_key"
            assert integration.skillsmp_client is not None

    def test_search_skills_with_api(self):
        """Test searching with API."""
        with tempfile.TemporaryDirectory() as tmpdir:
            integration = SkillsMPIntegration(
                api_key="test_key",
                global_home=Path(tmpdir)
            )

            with patch.object(integration.skillsmp_client, 'search_skills') as mock_search:
                mock_search.return_value = [
                    {"title": "Test Skill", "github_stars": 10}
                ]

                results = integration.search_skills("test query")

                assert len(results) > 0
                assert results[0]["source"] == "skillsmp"

    def test_search_skills_github_fallback(self):
        """Test GitHub fallback when API unavailable."""
        with tempfile.TemporaryDirectory() as tmpdir:
            integration = SkillsMPIntegration(
                github_token="ghp_test",
                global_home=Path(tmpdir)
            )

            # SkillsMP not configured
            assert integration.skillsmp_client is None

            with patch.object(integration.github_searcher, 'search_skills') as mock_search:
                mock_search.return_value = [
                    {"title": "GitHub Skill"}
                ]

                results = integration.search_skills("test")

                assert len(results) > 0
                assert results[0]["source"] == "github"

    def test_setup_api_key(self):
        """Test setting up API key."""
        with tempfile.TemporaryDirectory() as tmpdir:
            integration = SkillsMPIntegration(global_home=Path(tmpdir))

            with patch.object(integration.key_storage, 'store_api_key') as mock_store:
                mock_store.return_value = True

                result = integration.setup_api_key("sk_test_key")

                assert result is True
                assert integration.api_key == "sk_test_key"

    def test_get_status(self):
        """Test getting status."""
        integration = SkillsMPIntegration()

        status = integration.get_status()

        assert "skillsmp" in status
        assert "github" in status


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
