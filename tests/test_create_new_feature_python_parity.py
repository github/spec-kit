"""Parity tests for the Python create-new-feature port."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from scripts.python.common import persist_feature_json
from tests.conftest import requires_bash
from tests.parity_helpers import (
    HAS_POWERSHELL,
    bash_cmd,
    install_scripts,
    json_stdout,
    make_repo,
    normalize_repo_paths,
    normalize_script_names,
    ps_cmd,
    py_cmd,
    run,
)

SCRIPT = "create-new-feature"
TEMPLATE_BODY = "# Spec Template\n\nBody.\n"


def _setup_repo(tmp_path: Path, name: str = "proj") -> Path:
    repo = make_repo(tmp_path, name)
    install_scripts(repo, SCRIPT)
    templates = repo / ".specify" / "templates"
    templates.mkdir(parents=True)
    (templates / "spec-template.md").write_text(TEMPLATE_BODY, encoding="utf-8")
    return repo


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    return _setup_repo(tmp_path)


@pytest.fixture
def repo_pair(tmp_path: Path) -> tuple[Path, Path]:
    return _setup_repo(tmp_path, "proj-a"), _setup_repo(tmp_path, "proj-b")


@requires_bash
@pytest.mark.parametrize(
    "description",
    [
        "Add user authentication system",
        "I want to add the new API rate limiting feature for users",
        "Fix UI for DB sync",
        "a to the of",
    ],
    ids=["plain", "stop_words", "acronyms", "all_stop_words_fallback"],
)
def test_python_branch_name_generation_matches_bash(
    repo: Path, description: str
) -> None:
    bash = run(bash_cmd(repo, SCRIPT, "--json", "--dry-run", description), repo)
    py = run(py_cmd(repo, SCRIPT, "--json", "--dry-run", description), repo)

    assert py.returncode == bash.returncode == 0
    assert py.stderr == bash.stderr == ""
    assert json_stdout(py) == json_stdout(bash)


@requires_bash
@pytest.mark.parametrize(
    "args",
    [
        ("--json", "--dry-run", "--number", "7", "add rate limiting"),
        ("--json", "--dry-run", "--number", "010", "add rate limiting"),
    ],
    ids=["explicit_number", "leading_zero_number"],
)
def test_python_number_flag_matches_bash(repo: Path, args: tuple[str, ...]) -> None:
    bash = run(bash_cmd(repo, SCRIPT, *args), repo)
    py = run(py_cmd(repo, SCRIPT, *args), repo)

    assert py.returncode == bash.returncode == 0
    assert json_stdout(py) == json_stdout(bash)


@requires_bash
def test_python_sequential_numbering_matches_bash(repo: Path) -> None:
    for name in ("001-first", "0005-fourdigit", "20260101-120000-stamp", "12-short"):
        (repo / "specs" / name).mkdir(parents=True)

    bash = run(bash_cmd(repo, SCRIPT, "--json", "--dry-run", "add rate limiting"), repo)
    py = run(py_cmd(repo, SCRIPT, "--json", "--dry-run", "add rate limiting"), repo)

    assert py.returncode == bash.returncode == 0
    assert json_stdout(py) == json_stdout(bash)
    assert json_stdout(py)["FEATURE_NUM"] == "006"


@requires_bash
def test_python_timestamp_mode_matches_bash_shape(repo: Path) -> None:
    args = ("--json", "--dry-run", "--timestamp", "--short-name", "user-auth", "x")
    bash = run(bash_cmd(repo, SCRIPT, *args), repo)
    py = run(py_cmd(repo, SCRIPT, *args), repo)

    assert py.returncode == bash.returncode == 0
    # Timestamps may straddle a second boundary, so compare shape and suffix.
    for result in (bash, py):
        data = json_stdout(result)
        assert re.fullmatch(r"\d{8}-\d{6}-user-auth", data["BRANCH_NAME"])
        assert data["BRANCH_NAME"].startswith(data["FEATURE_NUM"])


@requires_bash
def test_python_timestamp_number_warning_matches_bash(repo: Path) -> None:
    args = (
        "--json",
        "--dry-run",
        "--timestamp",
        "--number",
        "5",
        "--short-name",
        "ua",
        "x",
    )
    bash = run(bash_cmd(repo, SCRIPT, *args), repo)
    py = run(py_cmd(repo, SCRIPT, *args), repo)

    assert py.returncode == bash.returncode == 0
    assert (
        py.stderr
        == bash.stderr
        == "[specify] Warning: --number is ignored when --timestamp is used\n"
    )


def test_python_invalid_number_fails_cleanly(repo: Path) -> None:
    # Deliberate deviation from bash: the bash twin dies with an arithmetic
    # expansion error for a non-integer --number, while the Python port
    # reports a clean error. Pin exit code and message so the intended
    # non-parity behavior can't regress silently.
    args = ("--json", "--dry-run", "--number", "abc", "add rate limiting")
    py = run(py_cmd(repo, SCRIPT, *args), repo)

    assert py.returncode == 1
    assert py.stdout == ""
    assert py.stderr == "Error: --number must be an integer, got 'abc'\n"


def test_python_negative_number_fails_cleanly(repo: Path) -> None:
    # Shell arithmetic differs across platforms for signed decimal strings;
    # the Python port deliberately rejects them consistently.
    args = ("--json", "--dry-run", "--number", "-1", "add rate limiting")
    py = run(py_cmd(repo, SCRIPT, *args), repo)

    assert py.returncode == 1
    assert py.stdout == ""
    assert py.stderr == "Error: --number must be an integer, got '-1'\n"


@pytest.mark.parametrize("digit_count", [244, 5000])
def test_python_oversized_number_fails_cleanly(repo: Path, digit_count: int) -> None:
    number = "9" * digit_count
    py = run(
        py_cmd(
            repo,
            SCRIPT,
            "--json",
            "--dry-run",
            "--number",
            number,
            "add rate limiting",
        ),
        repo,
    )

    assert py.returncode == 1
    assert py.stdout == ""
    assert py.stderr == "Error: feature number is too long for a branch name\n"


@requires_bash
def test_python_branch_truncation_matches_bash(repo: Path) -> None:
    args = ("--json", "--dry-run", "--short-name", "a" * 300, "x")
    bash = run(bash_cmd(repo, SCRIPT, *args), repo)
    py = run(py_cmd(repo, SCRIPT, *args), repo)

    assert py.returncode == bash.returncode == 0
    assert py.stderr == bash.stderr
    assert json_stdout(py) == json_stdout(bash)
    assert len(json_stdout(py)["BRANCH_NAME"]) == 244


@requires_bash
def test_python_full_run_matches_bash(repo_pair: tuple[Path, Path]) -> None:
    repo_a, repo_b = repo_pair
    description = "Add user authentication system"

    bash = run(bash_cmd(repo_a, SCRIPT, "--json", description), repo_a)
    py = run(py_cmd(repo_b, SCRIPT, "--json", description), repo_b)

    assert py.returncode == bash.returncode == 0
    assert normalize_repo_paths(py.stdout, repo_b) == normalize_repo_paths(
        bash.stdout, repo_a
    )
    assert normalize_repo_paths(py.stderr, repo_b) == normalize_repo_paths(
        bash.stderr, repo_a
    )

    branch = json_stdout(py)["BRANCH_NAME"]
    for repo in repo_pair:
        spec = repo / "specs" / branch / "spec.md"
        assert spec.read_text(encoding="utf-8") == TEMPLATE_BODY
    assert (repo_b / ".specify" / "feature.json").read_bytes() == (
        repo_a / ".specify" / "feature.json"
    ).read_bytes()


@requires_bash
def test_python_missing_template_warning_matches_bash(
    repo_pair: tuple[Path, Path],
) -> None:
    repo_a, repo_b = repo_pair
    for repo in repo_pair:
        (repo / ".specify" / "templates" / "spec-template.md").unlink()

    bash = run(bash_cmd(repo_a, SCRIPT, "--json", "add rate limiting"), repo_a)
    py = run(py_cmd(repo_b, SCRIPT, "--json", "add rate limiting"), repo_b)

    assert py.returncode == bash.returncode == 0
    assert normalize_repo_paths(py.stderr, repo_b) == normalize_repo_paths(
        bash.stderr, repo_a
    )
    branch = json_stdout(py)["BRANCH_NAME"]
    for repo in repo_pair:
        assert (repo / "specs" / branch / "spec.md").read_text(encoding="utf-8") == ""


@requires_bash
def test_python_existing_directory_error_matches_bash(
    repo_pair: tuple[Path, Path],
) -> None:
    repo_a, repo_b = repo_pair
    description = "add rate limiting"

    assert (
        run(
            bash_cmd(repo_a, SCRIPT, "--json", "--number", "1", description), repo_a
        ).returncode
        == 0
    )
    assert (
        run(
            py_cmd(repo_b, SCRIPT, "--json", "--number", "1", description), repo_b
        ).returncode
        == 0
    )

    bash = run(bash_cmd(repo_a, SCRIPT, "--json", "--number", "1", description), repo_a)
    py = run(py_cmd(repo_b, SCRIPT, "--json", "--number", "1", description), repo_b)

    assert py.returncode == bash.returncode == 1
    assert py.stdout == bash.stdout == ""
    assert normalize_repo_paths(py.stderr, repo_b) == normalize_repo_paths(
        bash.stderr, repo_a
    )

    bash_retry = run(
        bash_cmd(
            repo_a,
            SCRIPT,
            "--json",
            "--number",
            "1",
            "--allow-existing-branch",
            description,
        ),
        repo_a,
    )
    py_retry = run(
        py_cmd(
            repo_b,
            SCRIPT,
            "--json",
            "--number",
            "1",
            "--allow-existing-branch",
            description,
        ),
        repo_b,
    )
    assert py_retry.returncode == bash_retry.returncode == 0
    assert normalize_repo_paths(py_retry.stdout, repo_b) == normalize_repo_paths(
        bash_retry.stdout, repo_a
    )


@requires_bash
@pytest.mark.parametrize(
    "args",
    [
        (),
        ("   ",),
        ("--short-name",),
        ("--number",),
    ],
    ids=["missing_description", "whitespace_description", "short_name_no_value", "number_no_value"],
)
def test_python_argument_errors_match_bash(repo: Path, args: tuple[str, ...]) -> None:
    bash = run(bash_cmd(repo, SCRIPT, *args), repo)
    py = run(py_cmd(repo, SCRIPT, *args), repo)

    assert py.returncode == bash.returncode == 1
    assert py.stdout == bash.stdout == ""
    assert normalize_script_names(py.stderr, repo, SCRIPT) == normalize_script_names(
        bash.stderr, repo, SCRIPT
    )


@requires_bash
def test_python_help_matches_bash(repo: Path) -> None:
    bash = run(bash_cmd(repo, SCRIPT, "--help"), repo)
    py = run(py_cmd(repo, SCRIPT, "--help"), repo)

    assert py.returncode == bash.returncode == 0
    assert py.stderr == bash.stderr == ""
    assert normalize_script_names(py.stdout, repo, SCRIPT) == normalize_script_names(
        bash.stdout, repo, SCRIPT
    )


@requires_bash
def test_python_persists_relative_feature_json(repo: Path) -> None:
    py = run(py_cmd(repo, SCRIPT, "--json", "add rate limiting"), repo)

    assert py.returncode == 0, py.stderr
    branch = json_stdout(py)["BRANCH_NAME"]
    feature_json = (repo / ".specify" / "feature.json").read_text(encoding="utf-8")
    assert feature_json == f'{{"feature_directory":"specs/{branch}"}}\n'


def test_persist_feature_json_avoids_platform_newline_translation(
    tmp_path: Path, monkeypatch
) -> None:
    def windows_write_text(path: Path, data: str, **kwargs) -> int:
        encoding = kwargs.get("encoding") or "utf-8"
        return path.write_bytes(data.replace("\n", "\r\n").encode(encoding))

    monkeypatch.setattr(Path, "write_text", windows_write_text)

    persist_feature_json(tmp_path, "specs/001-test")

    assert (tmp_path / ".specify" / "feature.json").read_bytes() == (
        b'{"feature_directory":"specs/001-test"}\n'
    )


@pytest.mark.skipif(not HAS_POWERSHELL, reason="no PowerShell available")
@pytest.mark.parametrize(
    ("py_args", "ps_args"),
    [
        (
            ("--json", "--dry-run", "Add user authentication system"),
            ("-Json", "-DryRun", "Add user authentication system"),
        ),
        (
            ("--json", "--dry-run", "--short-name", "My Fancy Name", "x"),
            ("-Json", "-DryRun", "-ShortName", "My Fancy Name", "x"),
        ),
        (
            ("--json", "--dry-run", "--number", "7", "add rate limiting"),
            ("-Json", "-DryRun", "-Number", "7", "add rate limiting"),
        ),
    ],
    ids=["plain", "short_name", "number"],
)
def test_python_json_output_matches_powershell(
    repo: Path, py_args: tuple[str, ...], ps_args: tuple[str, ...]
) -> None:
    ps = run(ps_cmd(repo, SCRIPT, *ps_args), repo)
    py = run(py_cmd(repo, SCRIPT, *py_args), repo)

    assert py.returncode == ps.returncode == 0
    assert json_stdout(py) == json_stdout(ps)
