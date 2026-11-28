"""Regression tests for mechanical [DATE] substitution and tasks-template front matter (#4335)."""

from __future__ import annotations

import datetime
import re
from pathlib import Path

import pytest
import yaml

from tests.conftest import requires_bash
from tests.parity_helpers import (
    HAS_POWERSHELL,
    PROJECT_ROOT,
    bash_cmd,
    install_scripts,
    json_stdout,
    make_repo,
    ps_cmd,
    py_cmd,
    run,
    write_feature_json,
)

SPEC_TEMPLATE = PROJECT_ROOT / "templates" / "spec-template.md"
PLAN_TEMPLATE = PROJECT_ROOT / "templates" / "plan-template.md"
TASKS_TEMPLATE = PROJECT_ROOT / "templates" / "tasks-template.md"

PORTS = [
    pytest.param("bash", marks=requires_bash),
    pytest.param(
        "powershell",
        marks=pytest.mark.skipif(not HAS_POWERSHELL, reason="no PowerShell available"),
    ),
    pytest.param("python"),
]

SPECIAL_CHARS_TEMPLATE = (
    "-n first line with [DATE] and second [DATE] on same line\n"
    "Case sensitive: [date] [Date] [dAtE]\n"
    "Other date tokens: [DATE_CREATED] [RATIFICATION_DATE] [LAST_AMENDED_DATE]\n"
    "Nested brackets: [[DATE]]\n"
    "Other placeholders: $ARGUMENTS [FEATURE NAME] [###-feature-name]\n"
    "Regex and shell chars: & \\& \\1 \\n \\t $env:USERNAME $(whoami) `id` %s %100%\n"
    "Quotes and backslashes: 'single' \"double\" C:\\Users\\test\\file\n"
    "Unicode: שלום עולם 添加用户 🎯 réservation\n"
    "Final date: [DATE]\n"
)


def _create_feature_cmd(
    repo: Path,
    port: str,
    *extra_args: str,
    json_mode: bool = False,
    dry_run: bool = False,
    allow_existing: bool = False,
    short_name: str | None = None,
) -> list[str]:
    if port == "powershell":
        args: list[str] = []
        if json_mode:
            args.append("-Json")
        if dry_run:
            args.append("-DryRun")
        if allow_existing:
            args.append("-AllowExistingBranch")
        if short_name is not None:
            args.extend(["-ShortName", short_name])
        args.extend(extra_args)
        return ps_cmd(repo, "create-new-feature", *args)

    args = []
    if json_mode:
        args.append("--json")
    if dry_run:
        args.append("--dry-run")
    if allow_existing:
        args.append("--allow-existing-branch")
    if short_name is not None:
        args.extend(["--short-name", short_name])
    args.extend(extra_args)
    command = bash_cmd if port == "bash" else py_cmd
    return command(repo, "create-new-feature", *args)


def _setup_plan_cmd(repo: Path, port: str, *, json_mode: bool = False) -> list[str]:
    if port == "powershell":
        return ps_cmd(repo, "setup-plan", *(("-Json",) if json_mode else ()))
    command = bash_cmd if port == "bash" else py_cmd
    return command(repo, "setup-plan", *(("--json",) if json_mode else ()))


def _setup_create_repo(tmp_path: Path, template_bytes: bytes | None) -> Path:
    repo = make_repo(tmp_path)
    install_scripts(repo, "create-new-feature")
    templates = repo / ".specify" / "templates"
    templates.mkdir(parents=True, exist_ok=True)
    if template_bytes is not None:
        (templates / "spec-template.md").write_bytes(template_bytes)
    return repo


def _setup_plan_repo(tmp_path: Path, template_bytes: bytes | None) -> tuple[Path, Path]:
    repo = make_repo(tmp_path)
    install_scripts(repo, "setup-plan")
    write_feature_json(repo, "specs/001-my-feature")
    feature_dir = repo / "specs" / "001-my-feature"
    feature_dir.mkdir(parents=True)
    templates = repo / ".specify" / "templates"
    templates.mkdir(parents=True, exist_ok=True)
    if template_bytes is not None:
        (templates / "plan-template.md").write_bytes(template_bytes)
    return repo, feature_dir


def _assert_substituted_bytes(
    actual_bytes: bytes, template_text: str, before: str, after: str
) -> None:
    assert not actual_bytes.startswith(b"\xef\xbb\xbf"), "Output must not have a UTF-8 BOM"
    expected_candidates = {
        template_text.replace("[DATE]", day).encode("utf-8")
        for day in (before, after)
    }
    assert actual_bytes in expected_candidates


# ── templates/tasks-template.md YAML front matter ────────────────────────────


def test_tasks_template_has_valid_yaml_frontmatter() -> None:
    raw = TASKS_TEMPLATE.read_bytes()
    assert not raw.startswith(b"\xef\xbb\xbf"), "tasks-template.md must not have a UTF-8 BOM"
    text = raw.decode("utf-8")
    lines = text.splitlines()

    assert lines[0] == "---"
    assert lines[1] == 'description: "Task list template for feature implementation"'
    assert lines[2] == "---"

    match = re.match(r"\A---\r?\n(.*?)\r?\n---\r?\n", text, flags=re.DOTALL)
    assert match is not None, "Expected valid YAML front matter at top of tasks-template.md"
    frontmatter = yaml.safe_load(match.group(1))
    assert frontmatter == {
        "description": "Task list template for feature implementation"
    }

    body = text[match.end() :]
    assert "# Tasks: [FEATURE NAME]" in body
    assert "**Input**: Design documents from `/specs/[###-feature-name]/`" in body


# ── create-new-feature [DATE] substitution ───────────────────────────────────


@pytest.mark.parametrize("port", PORTS)
def test_create_new_feature_substitutes_stock_spec_template_date(
    tmp_path: Path, port: str
) -> None:
    template_bytes = SPEC_TEMPLATE.read_bytes()
    template_text = template_bytes.decode("utf-8")
    assert "**Created**: [DATE]" in template_text

    repo = _setup_create_repo(tmp_path, template_bytes)
    before = datetime.date.today().isoformat()
    result = run(
        _create_feature_cmd(repo, port, "Add auth", json_mode=True, short_name="auth"),
        repo,
    )
    after = datetime.date.today().isoformat()

    assert result.returncode == 0, result.stderr
    payload = json_stdout(result)
    spec_file = repo / "specs" / payload["BRANCH_NAME"] / "spec.md"
    raw = spec_file.read_bytes()

    _assert_substituted_bytes(raw, template_text, before, after)
    rendered = raw.decode("utf-8")
    assert "[DATE]" not in rendered
    assert any(f"**Created**: {day}" in rendered for day in (before, after))
    assert "**Status**: Draft" in rendered
    assert '**Input**: User description: "$ARGUMENTS"' in rendered
    assert "[FEATURE NAME]" in rendered
    assert "`[###-feature-name]`" in rendered


@pytest.mark.parametrize("port", PORTS)
def test_create_new_feature_preserves_special_chars_and_other_tokens(
    tmp_path: Path, port: str
) -> None:
    repo = _setup_create_repo(tmp_path, SPECIAL_CHARS_TEMPLATE.encode("utf-8"))
    before = datetime.date.today().isoformat()
    result = run(
        _create_feature_cmd(repo, port, "Test chars", json_mode=True, short_name="chars"),
        repo,
    )
    after = datetime.date.today().isoformat()

    assert result.returncode == 0, result.stderr
    spec_file = repo / "specs" / "001-chars" / "spec.md"
    _assert_substituted_bytes(
        spec_file.read_bytes(), SPECIAL_CHARS_TEMPLATE, before, after
    )


@pytest.mark.parametrize("port", PORTS)
@pytest.mark.parametrize(
    "template_text",
    [
        "# No date placeholder here\nBody only.\n",
        "# No trailing newline\nDate: [DATE]",
        "# Multiple trailing newlines\n[DATE] and [DATE]\n\n\n",
    ],
    ids=["zero_occurrences", "no_trailing_newline", "multiple_trailing_newlines"],
)
def test_create_new_feature_handles_occurrence_counts_and_trailing_newlines(
    tmp_path: Path, port: str, template_text: str
) -> None:
    repo = _setup_create_repo(tmp_path, template_text.encode("utf-8"))
    before = datetime.date.today().isoformat()
    result = run(
        _create_feature_cmd(repo, port, "Test eol", json_mode=True, short_name="eol"),
        repo,
    )
    after = datetime.date.today().isoformat()

    assert result.returncode == 0, result.stderr
    spec_file = repo / "specs" / "001-eol" / "spec.md"
    _assert_substituted_bytes(spec_file.read_bytes(), template_text, before, after)


@pytest.mark.parametrize("port", PORTS)
def test_create_new_feature_preserves_dry_run_missing_template_and_existing_spec(
    tmp_path: Path, port: str
) -> None:
    # 1. --dry-run does not create directory or spec.md
    dry_repo = _setup_create_repo(tmp_path / "dry", b"Date: [DATE]\n")
    dry_result = run(
        _create_feature_cmd(
            dry_repo, port, "Dry run", json_mode=True, dry_run=True, short_name="dry"
        ),
        dry_repo,
    )
    assert dry_result.returncode == 0, dry_result.stderr
    assert json_stdout(dry_result)["DRY_RUN"] is True
    assert not (dry_repo / "specs" / "001-dry").exists()

    # 2. Missing spec template warns and creates empty spec.md
    missing_repo = _setup_create_repo(tmp_path / "missing", None)
    missing_result = run(
        _create_feature_cmd(
            missing_repo, port, "Missing", json_mode=True, short_name="missing"
        ),
        missing_repo,
    )
    assert missing_result.returncode == 0, missing_result.stderr
    assert "Spec template not found" in missing_result.stderr
    assert (missing_repo / "specs" / "001-missing" / "spec.md").read_bytes() == b""

    # 3. Existing spec.md with --allow-existing-branch is not overwritten or modified
    existing_repo = _setup_create_repo(tmp_path / "existing", b"New [DATE]\n")
    existing_dir = existing_repo / "specs" / "001-existing"
    existing_dir.mkdir(parents=True)
    existing_bytes = b"Existing literal [DATE] must stay untouched\n"
    (existing_dir / "spec.md").write_bytes(existing_bytes)
    existing_result = run(
        _create_feature_cmd(
            existing_repo,
            port,
            "Existing",
            json_mode=True,
            allow_existing=True,
            short_name="existing",
        ),
        existing_repo,
    )
    assert existing_result.returncode == 0, existing_result.stderr
    assert (existing_dir / "spec.md").read_bytes() == existing_bytes


# ── setup-plan [DATE] substitution ───────────────────────────────────────────


@pytest.mark.parametrize("port", PORTS)
def test_setup_plan_substitutes_stock_plan_template_date(
    tmp_path: Path, port: str
) -> None:
    template_bytes = PLAN_TEMPLATE.read_bytes()
    template_text = template_bytes.decode("utf-8")
    assert "**Date**: [DATE]" in template_text

    repo, feature_dir = _setup_plan_repo(tmp_path, template_bytes)
    before = datetime.date.today().isoformat()
    result = run(_setup_plan_cmd(repo, port, json_mode=True), repo)
    after = datetime.date.today().isoformat()

    assert result.returncode == 0, result.stderr
    payload = json_stdout(result)
    assert "IMPL_PLAN" in payload
    raw = (feature_dir / "plan.md").read_bytes()

    _assert_substituted_bytes(raw, template_text, before, after)
    rendered = raw.decode("utf-8")
    assert "[DATE]" not in rendered
    assert any(f"**Date**: {day}" in rendered for day in (before, after))
    assert "**Input**: Feature specification from `/specs/[###-feature-name]/spec.md`" in rendered


@pytest.mark.parametrize("port", PORTS)
def test_setup_plan_preserves_special_chars_and_other_tokens(
    tmp_path: Path, port: str
) -> None:
    repo, feature_dir = _setup_plan_repo(
        tmp_path, SPECIAL_CHARS_TEMPLATE.encode("utf-8")
    )
    before = datetime.date.today().isoformat()
    result = run(_setup_plan_cmd(repo, port, json_mode=True), repo)
    after = datetime.date.today().isoformat()

    assert result.returncode == 0, result.stderr
    _assert_substituted_bytes(
        (feature_dir / "plan.md").read_bytes(), SPECIAL_CHARS_TEMPLATE, before, after
    )


@pytest.mark.parametrize("port", PORTS)
@pytest.mark.parametrize(
    "template_text",
    [
        "# No date placeholder here\nBody only.\n",
        "# No trailing newline\nDate: [DATE]",
        "# Multiple trailing newlines\n[DATE] and [DATE]\n\n\n",
    ],
    ids=["zero_occurrences", "no_trailing_newline", "multiple_trailing_newlines"],
)
def test_setup_plan_handles_occurrence_counts_and_trailing_newlines(
    tmp_path: Path, port: str, template_text: str
) -> None:
    repo, feature_dir = _setup_plan_repo(tmp_path, template_text.encode("utf-8"))
    before = datetime.date.today().isoformat()
    result = run(_setup_plan_cmd(repo, port, json_mode=False), repo)
    after = datetime.date.today().isoformat()

    assert result.returncode == 0, result.stderr
    _assert_substituted_bytes(
        (feature_dir / "plan.md").read_bytes(), template_text, before, after
    )


@pytest.mark.parametrize("port", PORTS)
def test_setup_plan_preserves_existing_plan_and_error_paths(
    tmp_path: Path, port: str
) -> None:
    # 1. Existing plan.md with literal [DATE] is not overwritten or modified
    existing_repo, existing_feature = _setup_plan_repo(
        tmp_path / "existing", b"Template [DATE]\n"
    )
    existing_bytes = b"Existing plan [DATE] must remain untouched\n"
    (existing_feature / "plan.md").write_bytes(existing_bytes)
    existing_result = run(_setup_plan_cmd(existing_repo, port, json_mode=True), existing_repo)
    assert existing_result.returncode == 0, existing_result.stderr
    assert (existing_feature / "plan.md").read_bytes() == existing_bytes

    # 2. Missing plan template exits 1 without creating plan.md
    missing_repo, missing_feature = _setup_plan_repo(tmp_path / "missing", None)
    missing_result = run(_setup_plan_cmd(missing_repo, port, json_mode=True), missing_repo)
    assert missing_result.returncode == 1
    assert missing_result.stdout == ""
    assert "Plan template not found" in missing_result.stderr
    assert not (missing_feature / "plan.md").exists()

    # 3. Empty plan template exits 1 without creating plan.md
    empty_repo, empty_feature = _setup_plan_repo(tmp_path / "empty", b"")
    empty_result = run(_setup_plan_cmd(empty_repo, port, json_mode=True), empty_repo)
    assert empty_result.returncode == 1
    assert empty_result.stdout == ""
    assert "Plan template is empty" in empty_result.stderr
    assert not (empty_feature / "plan.md").exists()
