"""Tests for resume-private persisted state ownership."""

import os

import pytest


class TestWorkflowCliAlignment:
    @pytest.mark.skipif(not hasattr(os, "symlink"), reason="symlinks are unavailable")
    def test_resume_rejects_symlinked_cross_project_owner_root(
        self, project_dir, tmp_path
    ):
        from specify_cli.workflows._command_resume_state import (
            _resolve_run_owner_root,
        )

        real_owner = tmp_path / "real-owner"
        real_owner.mkdir()
        owner_link = tmp_path / "owner-link"
        owner_link.symlink_to(real_owner, target_is_directory=True)

        with pytest.raises(ValueError, match="unavailable"):
            _resolve_run_owner_root(str(owner_link), project_dir)

    @pytest.mark.skipif(not hasattr(os, "symlink"), reason="symlinks are unavailable")
    def test_resume_rejects_cross_project_owner_with_symlinked_ancestor(
        self, project_dir, tmp_path
    ):
        from specify_cli.workflows._command_resume_state import (
            _resolve_run_owner_root,
        )

        real_parent = tmp_path / "real-parent"
        owner = real_parent / "owner"
        owner.mkdir(parents=True)
        parent_link = tmp_path / "parent-link"
        parent_link.symlink_to(real_parent, target_is_directory=True)

        with pytest.raises(ValueError, match="unavailable"):
            _resolve_run_owner_root(str(parent_link / "owner"), project_dir)
