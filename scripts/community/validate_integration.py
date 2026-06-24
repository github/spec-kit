#!/usr/bin/env python3
"""Validate local community integration workflow invariants.

This script is intentionally dependency-free so it can run from PowerShell,
GitHub Actions, or a fresh checkout before project dependencies are installed.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


ID_RE = re.compile(r"^[a-z][a-z0-9-]*$")
SEMVER_RE = re.compile(r"^v?\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?$")
ISO_DAY_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T00:00:00Z$")
SHA_RE = re.compile(r"\b[0-9a-fA-F]{40}\b")
URL_RE = re.compile(r"^https://")
COMMUNITY_BRANCH_RE = re.compile(r"^community/(?:\d+-)?[a-z0-9][a-z0-9._-]*$")


class Validation:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def error(self, message: str) -> None:
        self.errors.append(message)

    def warn(self, message: str) -> None:
        self.warnings.append(message)

    def require(self, condition: bool, message: str) -> None:
        if not condition:
            self.error(message)


def load_json(path: Path, validation: Validation) -> dict:
    try:
        with path.open(encoding="utf-8") as handle:
            data = json.load(handle)
    except FileNotFoundError:
        validation.error(f"{path}: file not found")
        return {}
    except json.JSONDecodeError as exc:
        validation.error(f"{path}: invalid JSON at line {exc.lineno}, column {exc.colno}: {exc.msg}")
        return {}

    if not isinstance(data, dict):
        validation.error(f"{path}: root value must be a JSON object")
        return {}
    return data


def validate_catalog(
    path: Path,
    collection_key: str,
    validation: Validation,
) -> None:
    data = load_json(path, validation)
    if not data:
        return

    validation.require(data.get("schema_version") == "1.0", f"{path}: schema_version must be 1.0")
    updated_at = data.get("updated_at")
    validation.require(
        isinstance(updated_at, str) and ISO_DAY_RE.match(updated_at) is not None,
        f"{path}: updated_at must use YYYY-MM-DDT00:00:00Z",
    )

    entries = data.get(collection_key)
    if not isinstance(entries, dict):
        validation.error(f"{path}: missing object field {collection_key!r}")
        return

    ids = list(entries)
    validation.require(ids == sorted(ids), f"{path}: {collection_key} keys must be sorted alphabetically")

    for entry_id, entry in entries.items():
        prefix = f"{path}: {collection_key}.{entry_id}"
        if not isinstance(entry, dict):
            validation.error(f"{prefix}: entry must be an object")
            continue

        validation.require(ID_RE.match(entry_id) is not None, f"{prefix}: key must match {ID_RE.pattern}")
        if "id" in entry:
            validation.require(entry["id"] == entry_id, f"{prefix}: id field must match catalog key")

        for field in ("name", "version", "description", "author", "repository", "license"):
            validation.require(
                isinstance(entry.get(field), str) and entry[field].strip() != "",
                f"{prefix}: missing non-empty string field {field!r}",
            )

        version = entry.get("version")
        validation.require(
            isinstance(version, str) and SEMVER_RE.match(version) is not None,
            f"{prefix}: version must be semver, with optional v prefix",
        )

        repository = entry.get("repository")
        validation.require(
            isinstance(repository, str) and URL_RE.match(repository) is not None,
            f"{prefix}: repository must be an https URL",
        )

        download_url = entry.get("download_url")
        if not (isinstance(download_url, str) and URL_RE.match(download_url)):
            validation.warn(f"{prefix}: download_url should be a non-empty https URL")

        requires = entry.get("requires")
        validation.require(isinstance(requires, dict), f"{prefix}: requires must be an object")
        if isinstance(requires, dict):
            validation.require(
                isinstance(requires.get("speckit_version"), str) and requires["speckit_version"].strip() != "",
                f"{prefix}: requires.speckit_version is required",
            )

        validation.require(isinstance(entry.get("provides"), dict), f"{prefix}: provides must be an object")
        validation.require(isinstance(entry.get("tags"), list) and len(entry["tags"]) >= 1, f"{prefix}: tags must be a non-empty array")

        for date_field in ("created_at", "updated_at"):
            value = entry.get(date_field)
            if not (isinstance(value, str) and ISO_DAY_RE.match(value)):
                validation.warn(f"{prefix}: {date_field} should use YYYY-MM-DDT00:00:00Z")


def field_value(body: str, label: str) -> str | None:
    pattern = re.compile(rf"(?im)^\s*[-*]?\s*{re.escape(label)}\s*:\s*(.+?)\s*$")
    match = pattern.search(body)
    if not match:
        return None
    value = match.group(1).strip()
    if value.startswith("<!--"):
        return None
    return value


def validate_branch(branch: str | None, validation: Validation) -> None:
    if not branch:
        return
    if branch.startswith("community/"):
        validation.require(
            COMMUNITY_BRANCH_RE.match(branch) is not None,
            f"branch {branch!r}: community branches must match community/(<issue>-)?<kebab-slug>",
        )


def validate_pr_body(body_path: Path | None, branch: str | None, validation: Validation) -> None:
    if body_path is None:
        return
    try:
        body = body_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        validation.error(f"{body_path}: PR body file not found")
        return

    if not branch or not branch.startswith("community/"):
        return

    route = field_value(body, "Submission route")
    validation.require(
        route in {"pr-template", "issue-template"},
        "community PR body must set 'Submission route: pr-template' or 'Submission route: issue-template'",
    )

    catalog_type = field_value(body, "Catalog type")
    validation.require(
        catalog_type in {"extension", "preset"},
        "community PR body must set 'Catalog type: extension' or 'Catalog type: preset'",
    )

    if route == "issue-template":
        validation.require(
            re.search(r"(?i)\bCloses\s+#\d+\b", body) is not None,
            "issue-template community PRs must include 'Closes #<issue-number>'",
        )
        return

    if route == "pr-template":
        source_repository = field_value(body, "Source repository")
        source_version = field_value(body, "Source version")
        source_commit = field_value(body, "Source commit")
        download_url = field_value(body, "Download URL")

        validation.require(
            source_repository is not None and URL_RE.match(source_repository) is not None,
            "pr-template community PRs must include an https Source repository",
        )
        validation.require(
            source_version is not None and SEMVER_RE.match(source_version) is not None,
            "pr-template community PRs must include a semver Source version",
        )
        validation.require(
            source_commit is not None and SHA_RE.search(source_commit) is not None,
            "pr-template community PRs must include a 40-character Source commit SHA",
        )
        validation.require(
            download_url is not None and URL_RE.match(download_url) is not None,
            "pr-template community PRs must include an https Download URL",
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--branch", default=None, help="Current branch name, usually github.head_ref in CI")
    parser.add_argument("--pr-body-file", type=Path, default=None)
    parser.add_argument("--show-warnings", action="store_true", help="Print non-blocking historical catalog style warnings")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    validation = Validation()

    validate_branch(args.branch, validation)
    validate_pr_body(args.pr_body_file, args.branch, validation)
    validate_catalog(repo_root / "extensions" / "catalog.community.json", "extensions", validation)
    validate_catalog(repo_root / "presets" / "catalog.community.json", "presets", validation)

    if args.show_warnings:
        for warning in validation.warnings:
            print(f"warning: {warning}")
    if validation.errors:
        for error in validation.errors:
            print(f"error: {error}", file=sys.stderr)
        return 1

    print("Community integration validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
