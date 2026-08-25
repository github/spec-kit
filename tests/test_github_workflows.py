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
COMMUNITY_SUBMISSION_WORKFLOWS = (
    (
        "bundle",
        "bundle-submission",
        "bundles/catalog.community.json",
        "docs/community/bundles.md",
        "Modify only `bundles/catalog.community.json`",
    ),
    (
        "extension",
        "extension-submission",
        "extensions/catalog.community.json",
        "docs/community/extensions.md",
        "Do not modify any other files",
    ),
    (
        "preset",
        "preset-submission",
        "presets/catalog.community.json",
        "docs/community/presets.md",
        "Do not modify any other files",
    ),
)


def _create_pull_request_allowed_files(source_text: str) -> list[str]:
    create_pr_match = re.search(
        r"(?m)^  create-pull-request:\n(?P<body>(?:^    [^\n]*\n?)+)",
        source_text,
    )
    assert create_pr_match is not None

    allowed_files_match = re.search(
        r"(?m)^    allowed-files:\n(?P<files>(?:^      - [^\n]+\n?)+)",
        create_pr_match.group("body"),
    )
    assert allowed_files_match is not None

    return [
        line.strip().removeprefix("- ")
        for line in allowed_files_match.group("files").splitlines()
        if line.strip()
    ]


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


def test_community_submission_automation_is_wired_to_allowed_files():
    assignment = WORKFLOWS_DIR / "catalog-assign.yml"
    assignment_text = assignment.read_text(encoding="utf-8")

    for workflow, label, catalog_file, docs_file, instruction in (
        COMMUNITY_SUBMISSION_WORKFLOWS
    ):
        source = WORKFLOWS_DIR / f"add-community-{workflow}.md"
        compiled = WORKFLOWS_DIR / f"add-community-{workflow}.lock.yml"

        assert source.is_file()
        assert compiled.is_file()
        source_text = source.read_text(encoding="utf-8")
        compiled_text = compiled.read_text(encoding="utf-8")

        assert f"names: [{label}]" in source_text
        assert catalog_file in source_text
        assert docs_file in source_text
        assert instruction in source_text
        assert _create_pull_request_allowed_files(source_text) == [
            catalog_file,
            docs_file,
        ]
        assert f'"allowed_files":["{catalog_file}","{docs_file}"]' in compiled_text
        assert label in assignment_text


def test_community_submission_allowed_files_do_not_include_other_catalogs_or_docs():
    allowed_by_workflow = {
        workflow: set(
            _create_pull_request_allowed_files(
                (WORKFLOWS_DIR / f"add-community-{workflow}.md").read_text(
                    encoding="utf-8"
                )
            )
        )
        for workflow, *_ in COMMUNITY_SUBMISSION_WORKFLOWS
    }

    workflow_allowed_files = list(allowed_by_workflow.items())

    for index, (workflow, allowed_files) in enumerate(workflow_allowed_files):
        for other_workflow, other_allowed_files in workflow_allowed_files[index + 1 :]:
            overlapping_files = allowed_files & other_allowed_files
            assert overlapping_files == set(), (
                f"{workflow} and {other_workflow} share allowed files: "
                f"{sorted(overlapping_files)}"
            )


def test_bug_test_workflow_provisions_python_dependencies():
    source = WORKFLOWS_DIR / "bug-test.md"
    compiled = WORKFLOWS_DIR / "bug-test.lock.yml"

    assert source.is_file()
    assert compiled.is_file()
    source_text = source.read_text(encoding="utf-8")
    compiled_text = compiled.read_text(encoding="utf-8")

    setup_uv = (
        "astral-sh/setup-uv@20cfd1bf945f4377ade1205e4dbc17946fc9a30d # v10.0.1"
    )
    setup_python = (
        "actions/setup-python@5fda3b95a4ea91299a34e894583c3862153e4b97 # v7.0.0"
    )

    assert "    - pypi.org" in source_text
    assert "    - files.pythonhosted.org" in source_text
    assert setup_uv in source_text
    assert setup_python in source_text
    assert 'run: uv pip install --system -e ".[test]"' in source_text

    assert '"pypi.org"' in compiled_text
    assert '"files.pythonhosted.org"' in compiled_text
    checkout_index = compiled_text.index("- name: Checkout repository")
    uv_index = compiled_text.index("- name: Setup uv")
    python_index = compiled_text.index("- name: Set up Python")
    sync_index = compiled_text.index("- name: Install Python test dependencies")
    agent_index = compiled_text.index("- name: Execute GitHub Copilot CLI")
    assert checkout_index < uv_index < python_index < sync_index < agent_index
    assert setup_uv in compiled_text
    assert setup_python in compiled_text
    assert 'run: uv pip install --system -e ".[test]"' in compiled_text
