"""Shared test fixtures for speckit tests."""

import tempfile
from pathlib import Path
from typing import Generator
from unittest.mock import MagicMock, AsyncMock

import pytest

from speckit.config import LLMConfig, StorageConfig, SpecKitConfig


@pytest.fixture
def temp_project_dir() -> Generator[Path, None, None]:
    """Create a temporary project directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_path = Path(tmpdir)
        # Create .speckit directory
        speckit_dir = project_path / ".speckit"
        speckit_dir.mkdir()
        # Create specs directory
        specs_dir = project_path / "specs"
        specs_dir.mkdir()
        yield project_path


@pytest.fixture
def llm_config() -> LLMConfig:
    """Create a test LLM configuration."""
    return LLMConfig(
        model="gpt-4o-mini",
        temperature=0.7,
        max_tokens=4096,
        timeout=120,
        max_retries=3,
        fallback_models=["gpt-4o-mini", "claude-3-haiku-20240307"],
    )


@pytest.fixture
def storage_config() -> StorageConfig:
    """Create a test storage configuration."""
    return StorageConfig(
        backend="file",
        base_dir=".speckit",
        specs_dir="specs",
    )


@pytest.fixture
def speckit_config(temp_project_dir: Path, llm_config: LLMConfig, storage_config: StorageConfig) -> SpecKitConfig:
    """Create a test SpecKit configuration."""
    return SpecKitConfig(
        llm=llm_config,
        storage=storage_config,
        project_path=temp_project_dir,
        language="en",
        verbose=False,
        debug=False,
    )


@pytest.fixture
def mock_llm_provider() -> MagicMock:
    """Create a mock LLM provider for testing."""
    mock = MagicMock()
    mock.complete.return_value = MagicMock(
        content="Mock LLM response",
        model="gpt-4o-mini",
        usage={"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150},
    )
    mock.complete_async = AsyncMock(return_value=MagicMock(
        content="Mock async LLM response",
        model="gpt-4o-mini",
        usage={"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150},
    ))
    return mock


@pytest.fixture
def sample_feature_description() -> str:
    """Sample feature description for testing."""
    return """
    Add user authentication with:
    - Email/password login
    - Password reset via email
    - Session management with JWT
    """


@pytest.fixture
def sample_specification_dict() -> dict:
    """Sample specification data for testing."""
    return {
        "feature_name": "User Authentication",
        "feature_id": "001-auth",
        "created_at": "2025-01-01T00:00:00",
        "version": "1.0.0",
        "overview": "Add user authentication to the application.",
        "problem_statement": "Users need to securely log in to access features.",
        "target_users": ["end users", "administrators"],
        "user_stories": [
            {
                "id": "US-001",
                "as_a": "end user",
                "i_want": "to log in with email and password",
                "so_that": "I can access my account",
                "priority": "must",
                "acceptance_criteria": [
                    "User can enter email and password",
                    "System validates credentials",
                    "User is redirected to dashboard on success",
                ],
            }
        ],
        "functional_requirements": [],
        "entities": [],
        "assumptions": [],
        "constraints": [],
        "out_of_scope": [],
        "success_criteria": [],
        "clarifications_needed": [],
        "clarifications_resolved": [],
    }
