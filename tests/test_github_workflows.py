"""Static checks for repository GitHub Actions workflows."""

from __future__ import annotations

import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
WORKFLOWS_DIR = REPO_ROOT / ".github" / "workflows"
# Match both the dedicated-step form (`        uses: x@sha`) and the
# inline shorthand (`      - uses: x@sha`) used in catalog-assign.yml.
USES_RE = re.compile(r"^\s*(?:-\s*)?uses:\s*(?P<ref>\S+)", re.MULTILINE)
PINNED_SHA_RE = re.compile(r"@[0-9a-f]{40}$", re.IGNORECASE)


def test_github_actions_are_pinned_to_full_commit_shas():
    unpinned_refs = []

    workflows = sorted(
        list(WORKFLOWS_DIR.glob("*.yml")) + list(WORKFLOWS_DIR.glob("*.yaml"))
    )
    assert workflows

    for workflow in workflows:
        workflow_text = workflow.read_text(encoding="utf-8")
        for match in USES_RE.finditer(workflow_text):
            uses_ref = match.group("ref")
            if uses_ref.startswith(("./", "../")):
                continue
            if PINNED_SHA_RE.search(uses_ref):
                continue
            unpinned_refs.append(f"{workflow.relative_to(REPO_ROOT)}: {uses_ref}")

    assert unpinned_refs == []


def test_pinned_action_ref_accepts_uppercase_hex_sha():
    assert PINNED_SHA_RE.search(
        "actions/example@0123456789ABCDEF0123456789ABCDEF01234567"
    )


def test_community_bundle_submission_automation_is_wired():
    source = WORKFLOWS_DIR / "add-community-bundle.md"
    compiled = WORKFLOWS_DIR / "add-community-bundle.lock.yml"
    assignment = WORKFLOWS_DIR / "catalog-assign.yml"

    assert source.is_file()
    assert compiled.is_file()
    source_text = source.read_text(encoding="utf-8")
    assignment_text = assignment.read_text(encoding="utf-8")

    assert "names: [bundle-submission]" in source_text
    assert "bundles/catalog.community.json" in source_text
    assert "docs/community/bundles.md" in source_text
    assert "verified: false" in source_text
    assert "allowed-files:" in source_text
    assert "bundle-submission" in assignment_text
