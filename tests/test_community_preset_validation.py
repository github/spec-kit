"""Regression coverage for the repository-owned preset submission verifier."""

import hashlib
import json
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parent.parent
VERIFIER = ROOT / ".github" / "scripts" / "validate_community_preset.py"
WORKFLOW = ROOT / ".github" / "workflows" / "add-community-preset.md"


@pytest.fixture
def submission(tmp_path):
    issue = {
        "preset_id": "sample",
        "preset_name": "Sample Preset",
        "version": "1.2.3",
        "description": "Sample usage",
        "author": "Contributor",
        "repository": "https://github.com/example/presets",
        "download_url": "https://github.com/example/presets/releases/download/sample-v1.2.3/sample.zip",
        "documentation": "https://github.com/example/presets/blob/main/sample/README.md",
        "license": "MIT",
        "speckit_version": ">=1.0.0",
        "required_extensions": "aide, canon",
        "templates_provided": "- spec-template.md",
        "commands_provided": "- speckit.plan.md",
        "scripts_count": "0",
        "tags": "sample, example",
    }
    paths = {name: tmp_path / name for name in (
        "issue.json", "archive.zip", "README.md", "catalog.json", "presets.md",
        "snapshot.json",
    )}
    paths["README.md"].write_text(
        f"specify preset add --from {issue['download_url']}\n", encoding="utf-8"
    )
    manifest = {
        "preset": {"id": "sample", "version": "1.2.3"},
        "requires": {"speckit_version": ">=1.0.0", "extensions": ["aide", "canon"]},
    }
    with zipfile.ZipFile(paths["archive.zip"], "w") as archive:
        archive.writestr("presets-release/sample/preset.yml", yaml.safe_dump(manifest))
        archive.writestr("presets-release/other/preset.yml", yaml.safe_dump({
            "preset": {"id": "other", "version": "9.9.9"},
            "requires": {"speckit_version": ">=0.1.0"},
        }))
    issue["actual_sha256"] = hashlib.sha256(paths["archive.zip"].read_bytes()).hexdigest()
    paths["issue.json"].write_text(json.dumps(issue), encoding="utf-8")
    paths["catalog.json"].write_text(
        json.dumps({"presets": {}}), encoding="utf-8"
    )
    paths["presets.md"].write_text(
        "| Preset | Purpose | Provides | Requires | URL |\n"
        "|--------|---------|----------|----------|-----|\n",
        encoding="utf-8",
    )
    return issue, manifest, paths


def run_verifier(paths, phase="submission"):
    return subprocess.run(
        [
            sys.executable, str(VERIFIER), phase,
            "--issue", str(paths["issue.json"]),
            "--archive", str(paths["archive.zip"]),
            "--readme", str(paths["README.md"]),
            "--catalog", str(paths["catalog.json"]),
            "--docs", str(paths["presets.md"]),
            "--snapshot", str(paths["snapshot.json"]),
        ],
        capture_output=True, text=True, check=False,
    )


def write_archive(paths, manifest):
    with zipfile.ZipFile(paths["archive.zip"], "w") as archive:
        archive.writestr("release/sample/preset.yml", yaml.safe_dump(manifest))


def write_generated(issue, paths, *, created_at="2025-01-01T00:00:00Z"):
    entry = {
        "id": issue["preset_id"], "name": issue["preset_name"],
        "version": issue["version"], "description": issue["description"],
        "author": issue["author"], "repository": issue["repository"],
        "download_url": issue["download_url"], "sha256": issue["actual_sha256"],
        "homepage": issue["repository"], "documentation": issue["documentation"],
        "license": issue["license"],
        "requires": {"speckit_version": issue["speckit_version"],
                     "extensions": ["aide", "canon"]},
        "provides": {"templates": 1, "commands": 1},
        "tags": ["sample", "example"],
        "created_at": created_at, "updated_at": "2026-01-01T00:00:00Z",
    }
    paths["catalog.json"].write_text(json.dumps({
        "updated_at": entry["updated_at"], "presets": {"sample": entry},
    }), encoding="utf-8")
    paths["presets.md"].write_text(
        "| Preset | Purpose | Provides | Requires | URL |\n"
        "|--------|---------|----------|----------|-----|\n"
        "| Sample Preset | Sample usage | 1 template, 1 command | "
        "aide extension, canon extension | "
        "[presets](https://github.com/example/presets) |\n",
        encoding="utf-8",
    )
    return entry


def test_matching_monorepo_submission_and_generated_files_pass(submission):
    issue, _, paths = submission
    first = run_verifier(paths)
    assert first.returncode == 0, first.stdout + first.stderr
    write_generated(issue, paths)
    second = run_verifier(paths, "generated")
    assert second.returncode == 0, second.stdout + second.stderr


def test_update_preserving_created_at_passes(submission):
    issue, _, paths = submission
    original = write_generated(issue, paths, created_at="2024-12-01T00:00:00Z")
    paths["catalog.json"].write_text(json.dumps({
        "updated_at": original["updated_at"], "presets": {"sample": original},
    }), encoding="utf-8")
    assert run_verifier(paths).returncode == 0
    write_generated(issue, paths, created_at="2024-12-01T00:00:00Z")
    assert run_verifier(paths, "generated").returncode == 0


@pytest.mark.parametrize(("change", "message"), [
    ({"preset": {"id": "sample", "version": "1.2.4"}}, "version"),
    ({"requires": {"speckit_version": ">=2.0.0",
                   "extensions": ["aide", "canon"]}}, "speckit_version"),
    ({"requires": {"speckit_version": ">=1.0.0",
                   "extensions": ["aide"]}}, "extensions"),
])
def test_published_manifest_mismatch_is_submission_failure(submission, change, message):
    _, manifest, paths = submission
    manifest.update(change)
    write_archive(paths, manifest)
    result = run_verifier(paths)
    assert result.returncode == 1
    assert message in result.stdout
    assert not paths["snapshot.json"].exists()


def test_release_tag_mismatch_is_submission_failure(submission):
    issue, _, paths = submission
    issue["download_url"] = issue["download_url"].replace("v1.2.3", "v1.2.4")
    paths["issue.json"].write_text(json.dumps(issue), encoding="utf-8")
    assert run_verifier(paths).returncode == 1


def test_stale_from_url_fails_even_with_valid_dev_command(submission):
    issue, _, paths = submission
    paths["README.md"].write_text(
        "specify preset add --dev ./sample\n"
        f"specify preset add --from {issue['download_url'].replace('v1.2.3', 'v1.2.2')}\n",
        encoding="utf-8",
    )
    result = run_verifier(paths)
    assert result.returncode == 1
    assert "README" in result.stdout


def test_dev_only_readme_is_accepted(submission):
    _, _, paths = submission
    paths["README.md"].write_text(
        "specify preset add --dev ./sample\n", encoding="utf-8"
    )
    assert run_verifier(paths).returncode == 0


def test_quoted_from_url_with_sentence_punctuation_is_accepted(submission):
    issue, _, paths = submission
    paths["README.md"].write_text(
        f'Spec Kit install: `specify preset add --from "{issue["download_url"]}".`\n',
        encoding="utf-8",
    )
    assert run_verifier(paths).returncode == 0


def test_id_install_and_unrelated_monorepo_release_are_accepted(submission):
    _, _, paths = submission
    paths["README.md"].write_text(
        "specify preset add sample\n"
        "specify preset add --from "
        "https://github.com/example/presets/releases/download/other-v2.0.0/other.zip\n",
        encoding="utf-8",
    )
    assert run_verifier(paths).returncode == 0


def test_stale_scoped_release_in_another_repository_fails(submission):
    _, _, paths = submission
    paths["README.md"].write_text(
        "specify preset add --dev ./sample\n"
        "specify preset add --from "
        "https://github.com/elsewhere/presets/releases/download/sample-v1.2.2/sample.zip\n",
        encoding="utf-8",
    )
    assert run_verifier(paths).returncode == 1


def test_optional_manifest_extension_is_not_required(submission):
    issue, manifest, paths = submission
    manifest["requires"]["extensions"].append({
        "id": "optional", "version": ">=1.0.0", "required": False,
    })
    write_archive(paths, manifest)
    issue["actual_sha256"] = hashlib.sha256(paths["archive.zip"].read_bytes()).hexdigest()
    paths["issue.json"].write_text(json.dumps(issue), encoding="utf-8")
    assert run_verifier(paths).returncode == 0


def test_invalid_unrelated_monorepo_manifest_does_not_mask_match(submission):
    _, manifest, paths = submission
    with zipfile.ZipFile(paths["archive.zip"], "w") as archive:
        archive.writestr("release/sample/preset.yml", yaml.safe_dump(manifest))
        archive.writestr("release/other/preset.yml", "preset: [invalid\n")
    assert run_verifier(paths).returncode == 0


def test_missing_archive_is_blocked_not_failed(submission):
    _, _, paths = submission
    paths["archive.zip"].unlink()
    result = run_verifier(paths)
    assert result.returncode == 2
    assert "BLOCKED" in result.stdout


def test_missing_generated_documentation_is_repairable(submission):
    issue, _, paths = submission
    assert run_verifier(paths).returncode == 0
    write_generated(issue, paths)
    paths["presets.md"].unlink()
    result = run_verifier(paths, "generated")
    assert result.returncode == 3
    assert "REPAIR" in result.stdout


def test_existing_entry_without_creation_date_blocks_update(submission):
    issue, _, paths = submission
    entry = write_generated(issue, paths)
    del entry["created_at"]
    paths["catalog.json"].write_text(
        json.dumps({"presets": {"sample": entry}}), encoding="utf-8"
    )
    result = run_verifier(paths)
    assert result.returncode == 2
    assert "created_at" in result.stdout


@pytest.mark.parametrize(("damage", "message"), [
    ("catalog-json", "catalog"),
    ("catalog-order", "alphabetical"),
    ("catalog-metadata", "version"),
    ("catalog-timestamp", "top-level updated_at"),
    ("docs-order", "alphabetical"),
    ("docs-row", "documentation row"),
    ("created-at", "created_at"),
])
def test_generated_defects_are_fixable_not_submission_failures(submission, damage, message):
    issue, _, paths = submission
    if damage == "created-at":
        original = write_generated(issue, paths)
        paths["catalog.json"].write_text(
            json.dumps({"updated_at": original["updated_at"], "presets": {
                "sample": original,
            }}), encoding="utf-8"
        )
    assert run_verifier(paths).returncode == 0
    entry = write_generated(issue, paths)
    if damage == "catalog-json":
        paths["catalog.json"].write_text("{", encoding="utf-8")
    elif damage == "catalog-order":
        paths["catalog.json"].write_text(json.dumps({
            "updated_at": entry["updated_at"],
            "presets": {"sample": entry, "aaa": {"name": "AAA"}},
        }), encoding="utf-8")
    elif damage == "catalog-metadata":
        entry["version"] = "1.2.4"
        paths["catalog.json"].write_text(
            json.dumps({"updated_at": entry["updated_at"], "presets": {
                "sample": entry,
            }}), encoding="utf-8"
        )
    elif damage == "catalog-timestamp":
        paths["catalog.json"].write_text(
            json.dumps({"updated_at": "2020-01-01T00:00:00Z", "presets": {
                "sample": entry,
            }}), encoding="utf-8"
        )
    elif damage == "docs-order":
        paths["presets.md"].write_text(
            paths["presets.md"].read_text(encoding="utf-8")
            + "| AAA | x | 1 command | — | [aaa](https://github.com/aaa/aaa) |\n",
            encoding="utf-8",
        )
    elif damage == "docs-row":
        paths["presets.md"].write_text(
            paths["presets.md"].read_text(encoding="utf-8").replace(
                "Sample usage", "Wrong purpose"
            ), encoding="utf-8",
        )
    elif damage == "created-at":
        entry["created_at"] = "2026-01-01T00:00:00Z"
        paths["catalog.json"].write_text(
            json.dumps({"updated_at": entry["updated_at"], "presets": {
                "sample": entry,
            }}), encoding="utf-8"
        )
    result = run_verifier(paths, "generated")
    assert result.returncode == 3, result.stdout + result.stderr
    assert message in result.stdout


def test_workflow_gates_success_on_both_verifier_phases():
    source = WORKFLOW.read_text(encoding="utf-8")
    assert "python3 .github/scripts/validate_community_preset.py submission" in source
    assert "python3 .github/scripts/validate_community_preset.py generated" in source
    assert (source.index("validate_community_preset.py generated")
            < source.index("## Step 6")
            < source.index("add the `validation-passed`", source.index("## Step 6")))
    frontmatter = yaml.safe_load(source.split("---", 2)[1])
    assert [step["name"] for step in frontmatter["steps"]] == [
        "Set up Python for preset verification",
        "Install preset verifier dependency",
    ]
    compiled = yaml.safe_load(
        (ROOT / ".github/workflows/add-community-preset.lock.yml").read_text(
            encoding="utf-8"
        )
    )
    steps = compiled["jobs"]["agent"]["steps"]
    for setup in frontmatter["steps"]:
        assert setup in steps
