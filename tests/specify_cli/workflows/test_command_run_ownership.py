"""Tests for run-private installed workflow ownership."""

import os
import shutil

import pytest
import typer


class TestWorkflowCliAlignment:
    WORKFLOW_YAML = """
schema_version: "1.0"
workflow:
  id: "align-wf"
  name: "Align Workflow"
  version: "{version}"
  description: "CLI alignment test workflow"
steps:
  - id: step-one
    type: shell
    run: "echo hello"
"""

    @pytest.mark.skipif(not hasattr(os, "symlink"), reason="symlinks are unavailable")
    def test_alias_rejects_symlinked_workflow_storage_before_resolve(
        self, project_dir, temp_dir
    ):
        from specify_cli.workflows import _command_run_ownership as run_ownership

        specify_dir = project_dir / ".specify"
        shutil.rmtree(specify_dir)
        redirected = temp_dir / "redirected-storage"
        workflow_file = redirected / "workflows" / "evil" / "workflow.yml"
        workflow_file.parent.mkdir(parents=True)
        workflow_file.write_text(
            self.WORKFLOW_YAML.format(version="1.0.0"), encoding="utf-8"
        )
        specify_dir.symlink_to(redirected, target_is_directory=True)
        alias = temp_dir / "workflow-alias.yml"
        alias.symlink_to(
            project_dir
            / ".specify"
            / "workflows"
            / "evil"
            / "workflow.yml"
        )

        with pytest.raises(typer.Exit):
            run_ownership._resolve_installed_workflow_ownership(
                alias, run_ownership.cli.err_console
            )
