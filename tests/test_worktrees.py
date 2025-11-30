"""
Tests for spectrena.worktrees (sw command).
"""

import pytest
from pathlib import Path
import os
from git import Repo
from spectrena.worktrees import (
    get_spec_branches,
    extract_spec_id,
    load_dependencies,
    get_completed_specs,
)


class TestWorktreesHelpers:
    """Test worktree helper functions."""

    def test_extract_spec_id_simple(self):
        """Test extracting spec ID from branch name."""
        # extract_spec_id now returns full spec ID (without spec/ prefix)
        assert extract_spec_id("spec/001-user-auth") == "001-user-auth"
        assert extract_spec_id("spec/042-api-integration") == "042-api-integration"

    def test_extract_spec_id_component(self):
        """Test extracting spec ID with component."""
        # Returns full spec ID including component and slug
        assert extract_spec_id("spec/CORE-001-user-auth") == "CORE-001-user-auth"
        assert extract_spec_id("spec/API-042-rest-endpoints") == "API-042-rest-endpoints"

    def test_get_spec_branches(self, git_repo, temp_dir):
        """Test getting all spec branches."""
        # Create some spec branches
        git_repo.create_head("spec/001-feature-a")
        git_repo.create_head("spec/002-feature-b")
        git_repo.create_head("feature/not-a-spec")
        git_repo.create_head("spec/CORE-003-feature-c")

        branches = get_spec_branches(git_repo)

        assert "spec/001-feature-a" in branches
        assert "spec/002-feature-b" in branches
        assert "spec/CORE-003-feature-c" in branches
        assert "feature/not-a-spec" not in branches

    def test_load_dependencies_empty(self, temp_dir):
        """Test loading dependencies when file doesn't exist."""
        os.chdir(temp_dir)
        deps = load_dependencies()
        assert deps == {}

    def test_load_dependencies_valid(self, temp_dir):
        """Test loading valid dependencies file (Mermaid format)."""
        # Create deps.mermaid file
        deps_file = temp_dir / "deps.mermaid"
        deps_file.write_text("""graph TD
    CORE-001
    CORE-002 --> CORE-001
    API-001 --> CORE-001
    API-001 --> CORE-002
    UI-001 --> API-001
""")

        os.chdir(temp_dir)
        deps = load_dependencies()

        assert deps["CORE-001"] == []
        assert deps["CORE-002"] == ["CORE-001"]
        assert "CORE-001" in deps["API-001"]
        assert "CORE-002" in deps["API-001"]
        assert deps["UI-001"] == ["API-001"]

    @pytest.mark.skip(reason="Git signing issues in test environment")
    def test_get_completed_specs(self, git_repo, temp_dir):
        """Test getting completed (merged) specs."""
        os.chdir(temp_dir)

        # Create spec branches
        spec1 = git_repo.create_head("spec/001-completed")
        spec2 = git_repo.create_head("spec/002-in-progress")

        # Merge spec1 to master (default branch)
        git_repo.head.reference = git_repo.heads.master
        git_repo.head.reset(index=True, working_tree=True)

        # Create a commit on spec1
        spec1.checkout()
        (temp_dir / "feature1.txt").write_text("Feature 1")
        git_repo.index.add(["feature1.txt"])
        git_repo.index.commit("Add feature 1")

        # Merge spec1 to master
        git_repo.heads.master.checkout()
        git_repo.git.merge("spec/001-completed", no_ff=True, m="Merge spec/001-completed")

        # Check completed specs (returns first two parts of spec ID)
        completed = get_completed_specs(git_repo)
        assert "001-completed" in completed
        assert "002-in" not in completed


class TestDependencyGraph:
    """Test dependency graph operations."""

    def test_simple_dependency_chain(self, temp_dir):
        """Test simple linear dependency chain."""
        deps_file = temp_dir / "deps.mermaid"
        deps_file.write_text("""graph TD
    SPEC-001
    SPEC-002 --> SPEC-001
    SPEC-003 --> SPEC-002
""")

        os.chdir(temp_dir)
        deps = load_dependencies()

        # SPEC-003 depends on SPEC-002
        assert "SPEC-002" in deps["SPEC-003"]
        # SPEC-002 depends on SPEC-001
        assert "SPEC-001" in deps["SPEC-002"]
        # SPEC-001 has no dependencies
        assert deps["SPEC-001"] == []

    def test_multi_dependency(self, temp_dir):
        """Test spec with multiple dependencies."""
        deps_file = temp_dir / "deps.mermaid"
        deps_file.write_text("""graph TD
    SPEC-001
    SPEC-002
    SPEC-003 --> SPEC-001
    SPEC-003 --> SPEC-002
""")

        os.chdir(temp_dir)
        deps = load_dependencies()

        assert len(deps["SPEC-003"]) == 2
        assert "SPEC-001" in deps["SPEC-003"]
        assert "SPEC-002" in deps["SPEC-003"]

    def test_no_dependencies(self, temp_dir):
        """Test spec with no dependencies (root)."""
        deps_file = temp_dir / "deps.mermaid"
        deps_file.write_text("""graph TD
    SPEC-001
    SPEC-002 --> SPEC-001
""")

        os.chdir(temp_dir)
        deps = load_dependencies()

        # SPEC-001 has no dependencies (is a root)
        assert "SPEC-001" in deps
        assert deps["SPEC-001"] == []
        # SPEC-002 depends on SPEC-001
        assert "SPEC-002" in deps
        assert deps["SPEC-002"] == ["SPEC-001"]


class TestWorktreeOperations:
    """Test worktree operations (requires git repo)."""

    def test_worktree_directory_structure(self, git_repo, temp_dir):
        """Test expected worktree directory structure."""
        # Create a spec branch
        spec_branch = git_repo.create_head("spec/001-test-feature")

        # Create worktree
        worktree_dir = temp_dir.parent / "worktrees" / "001-test-feature"
        worktree_dir.parent.mkdir(parents=True, exist_ok=True)

        git_repo.git.worktree("add", str(worktree_dir), "spec/001-test-feature")

        # Verify worktree exists
        assert worktree_dir.exists()
        assert (worktree_dir / ".git").exists()

        # Cleanup
        git_repo.git.worktree("remove", str(worktree_dir))

    def test_worktree_list(self, git_repo, temp_dir):
        """Test listing worktrees."""
        from spectrena.worktrees import get_worktrees

        # Create a worktree
        spec_branch = git_repo.create_head("spec/test-worktree")
        worktree_dir = temp_dir.parent / "worktrees" / "test"
        worktree_dir.parent.mkdir(parents=True, exist_ok=True)

        git_repo.git.worktree("add", str(worktree_dir), "spec/test-worktree")

        # Get worktrees
        os.chdir(temp_dir)
        worktrees = get_worktrees(git_repo)

        # Should have at least 2: main repo + our worktree
        assert len(worktrees) >= 2

        # Find our worktree
        our_wt = next((wt for wt in worktrees if wt.get("branch") == "spec/test-worktree"), None)
        assert our_wt is not None
        assert "test" in our_wt["path"]

        # Cleanup
        git_repo.git.worktree("remove", str(worktree_dir))
