"""Regression tests for catalog trust/vetting guidance in docs (#4733).

These check for the specific inconsistencies reported in the issue:
workflow publishing docs claimed a security review of submitted workflow
code, and preset/bundle catalog docs lacked the vetting guidance that
extension catalog docs already had.
"""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_workflow_publishing_does_not_claim_security_review():
    text = (REPO_ROOT / "workflows" / "PUBLISHING.md").read_text(encoding="utf-8")
    assert "Security** — no malicious shell commands" not in text
    assert "workflows are reviewed at submission time" not in text
    assert "not a security review" in text


def test_preset_catalog_docs_warn_about_vetting_install_allowed():
    text = (REPO_ROOT / "docs" / "reference" / "presets.md").read_text(encoding="utf-8")
    assert "install_allowed" in text
    assert "vet" in text.lower()


def test_bundle_catalog_docs_cover_bundle_source_and_component_catalogs():
    text = (REPO_ROOT / "docs" / "reference" / "bundles.md").read_text(encoding="utf-8")
    assert "component catalogs" in text.lower()
    assert "vet" in text.lower()
