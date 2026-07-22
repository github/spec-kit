"""Parity tests for the Python create-new-feature port."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from scripts.python import create_new_feature
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


def _normalized_error_text(stderr: str, repo: Path) -> str:
    stderr = re.sub(r"\x1b\[[0-9;]*m", "", stderr)
    stderr = re.sub(r"(?m)^\s*\|\s?", "", stderr)
    stderr = normalize_repo_paths(stderr, repo).replace("-Number", "--number")
    return " ".join(stderr.split())


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
def test_all_variants_timestamp_mode_match_shape(repo: Path) -> None:
    args = ("--json", "--dry-run", "--timestamp", "--short-name", "user-auth", "x")
    bash = run(bash_cmd(repo, SCRIPT, *args), repo)
    py = run(py_cmd(repo, SCRIPT, *args), repo)
    results = [bash, py]
    if HAS_POWERSHELL:
        results.append(
            run(
                ps_cmd(
                    repo,
                    SCRIPT,
                    "-Json",
                    "-DryRun",
                    "-Timestamp",
                    "-ShortName",
                    "user-auth",
                    "x",
                ),
                repo,
            )
        )

    assert all(result.returncode == 0 for result in results)
    # Timestamps may straddle a second boundary, so compare shape and suffix.
    for result in results:
        data = json_stdout(result)
        assert re.fullmatch(r"\d{8}-\d{6}-user-auth", data["BRANCH_NAME"])
        assert data["BRANCH_NAME"].startswith(data["FEATURE_NUM"])


@requires_bash
@pytest.mark.skipif(not HAS_POWERSHELL, reason="no PowerShell available")
def test_all_variants_timestamp_number_warning_matches(repo: Path) -> None:
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
    ps = run(
        ps_cmd(
            repo,
            SCRIPT,
            "-Json",
            "-DryRun",
            "-Timestamp",
            "-Number",
            "5",
            "-ShortName",
            "ua",
            "x",
        ),
        repo,
    )
    py = run(py_cmd(repo, SCRIPT, *args), repo)

    assert bash.returncode == ps.returncode == py.returncode == 0
    assert json_stdout(ps)
    assert (
        py.stderr
        == bash.stderr
        == ps.stderr.replace("-Number", "--number").replace(
            "-Timestamp", "--timestamp"
        )
        == "[specify] Warning: --number is ignored when --timestamp is used\n"
    )


@requires_bash
@pytest.mark.skipif(not HAS_POWERSHELL, reason="no PowerShell available")
def test_all_variants_invalid_number_fails_cleanly(repo: Path) -> None:
    args = ("--json", "--dry-run", "--number", "abc", "add rate limiting")
    bash = run(bash_cmd(repo, SCRIPT, *args), repo)
    ps = run(
        ps_cmd(
            repo,
            SCRIPT,
            "-Json",
            "-DryRun",
            "-Number",
            "abc",
            "add rate limiting",
        ),
        repo,
    )
    py = run(py_cmd(repo, SCRIPT, *args), repo)

    assert bash.returncode == ps.returncode == py.returncode == 1
    assert bash.stdout == ps.stdout == py.stdout == ""
    expected = "Error: --number must be an unsigned integer, got 'abc'"
    for result in (bash, ps, py):
        assert expected in _normalized_error_text(result.stderr, repo)


@requires_bash
@pytest.mark.skipif(not HAS_POWERSHELL, reason="no PowerShell available")
def test_all_variants_negative_number_fails_cleanly(repo: Path) -> None:
    args = ("--json", "--dry-run", "--number", "-1", "add rate limiting")
    bash = run(bash_cmd(repo, SCRIPT, *args), repo)
    ps = run(
        ps_cmd(
            repo,
            SCRIPT,
            "-Json",
            "-DryRun",
            "-Number",
            "-1",
            "add rate limiting",
        ),
        repo,
    )
    py = run(py_cmd(repo, SCRIPT, *args), repo)

    assert bash.returncode == ps.returncode == py.returncode == 1
    assert bash.stdout == ps.stdout == py.stdout == ""
    expected = "Error: --number must be an unsigned integer, got '-1'"
    for result in (bash, ps, py):
        assert expected in _normalized_error_text(result.stderr, repo)


@requires_bash
@pytest.mark.skipif(not HAS_POWERSHELL, reason="no PowerShell available")
@pytest.mark.parametrize("digit_count", [244, 5000])
def test_all_variants_oversized_number_fails_cleanly(
    repo: Path, digit_count: int
) -> None:
    number = "9" * digit_count
    bash = run(
        bash_cmd(
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
    ps = run(
        ps_cmd(
            repo,
            SCRIPT,
            "-Json",
            "-DryRun",
            "-Number",
            number,
            "add rate limiting",
        ),
        repo,
    )
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

    assert bash.returncode == ps.returncode == py.returncode == 1
    assert bash.stdout == ps.stdout == py.stdout == ""
    expected = (
        f"Error: --number must be between 0 and {2**63 - 1}, got '{number}'"
    )
    for result in (bash, ps, py):
        assert expected in _normalized_error_text(result.stderr, repo)


@requires_bash
@pytest.mark.skipif(not HAS_POWERSHELL, reason="no PowerShell available")
def test_all_variants_branch_truncation_match(repo: Path) -> None:
    args = ("--json", "--dry-run", "--short-name", "a" * 300, "x")
    bash = run(bash_cmd(repo, SCRIPT, *args), repo)
    ps = run(
        ps_cmd(
            repo,
            SCRIPT,
            "-Json",
            "-DryRun",
            "-ShortName",
            "a" * 300,
            "x",
        ),
        repo,
    )
    py = run(py_cmd(repo, SCRIPT, *args), repo)

    assert bash.returncode == ps.returncode == py.returncode == 0
    assert bash.stderr == ps.stderr == py.stderr
    assert json_stdout(bash) == json_stdout(ps) == json_stdout(py)
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


@requires_bash
@pytest.mark.skipif(not HAS_POWERSHELL, reason="no PowerShell available")
@pytest.mark.parametrize("number", ["-1", "+1"], ids=["negative", "positive_sign"])
def test_all_variants_reject_signed_number(repo: Path, number: str) -> None:
    bash = run(
        bash_cmd(repo, SCRIPT, "--json", "--dry-run", "--number", number, "x"),
        repo,
    )
    ps = run(
        ps_cmd(repo, SCRIPT, "-Json", "-DryRun", "-Number", number, "x"),
        repo,
    )
    py = run(
        py_cmd(repo, SCRIPT, "--json", "--dry-run", "--number", number, "x"),
        repo,
    )

    assert bash.returncode == ps.returncode == py.returncode == 1
    expected = f"Error: --number must be an unsigned integer, got '{number}'"
    for result in (bash, ps, py):
        assert expected in _normalized_error_text(result.stderr, repo)


@requires_bash
@pytest.mark.skipif(not HAS_POWERSHELL, reason="no PowerShell available")
@pytest.mark.parametrize("timestamp", [False, True], ids=["numbered", "timestamp"])
def test_all_variants_treat_empty_number_as_omitted(
    repo: Path, timestamp: bool
) -> None:
    bash_args = ["--json", "--dry-run", "--number", ""]
    ps_args = ["-Json", "-DryRun", "-Number", ""]
    py_args = ["--json", "--dry-run", "--number", ""]
    if timestamp:
        bash_args.append("--timestamp")
        ps_args.append("-Timestamp")
        py_args.append("--timestamp")
    bash_args.append("x")
    ps_args.append("x")
    py_args.append("x")

    bash = run(bash_cmd(repo, SCRIPT, *bash_args), repo)
    ps = run(ps_cmd(repo, SCRIPT, *ps_args), repo)
    py = run(py_cmd(repo, SCRIPT, *py_args), repo)

    assert bash.returncode == ps.returncode == py.returncode == 0
    assert bash.stderr == ps.stderr == py.stderr == ""
    if not timestamp:
        assert json_stdout(bash) == json_stdout(ps) == json_stdout(py)


@requires_bash
@pytest.mark.skipif(not HAS_POWERSHELL, reason="no PowerShell available")
@pytest.mark.parametrize(
    ("number", "returncode"),
    [
        (str(2**63 - 1), 0),
        (str(2**63), 1),
    ],
    ids=["int64_max", "int64_overflow"],
)
def test_all_variants_share_int64_number_range(
    repo: Path, number: str, returncode: int
) -> None:
    bash = run(
        bash_cmd(repo, SCRIPT, "--json", "--dry-run", "--number", number, "x"),
        repo,
    )
    ps = run(
        ps_cmd(repo, SCRIPT, "-Json", "-DryRun", "-Number", number, "x"),
        repo,
    )
    py = run(
        py_cmd(repo, SCRIPT, "--json", "--dry-run", "--number", number, "x"),
        repo,
    )

    assert bash.returncode == ps.returncode == py.returncode == returncode
    if returncode == 0:
        assert json_stdout(bash) == json_stdout(ps) == json_stdout(py)
    else:
        assert bash.stdout == ps.stdout == py.stdout == ""
        expected = f"Error: --number must be between 0 and {2**63 - 1}, got '{number}'"
        for result in (bash, ps, py):
            assert expected in _normalized_error_text(result.stderr, repo)


@requires_bash
@pytest.mark.skipif(not HAS_POWERSHELL, reason="no PowerShell available")
def test_all_variants_reject_exhausted_auto_number_range(repo: Path) -> None:
    (repo / "specs" / f"{2**63 - 1}-existing").mkdir(parents=True)

    bash = run(bash_cmd(repo, SCRIPT, "--json", "--dry-run", "x"), repo)
    ps = run(ps_cmd(repo, SCRIPT, "-Json", "-DryRun", "x"), repo)
    py = run(py_cmd(repo, SCRIPT, "--json", "--dry-run", "x"), repo)

    assert bash.returncode == ps.returncode == py.returncode == 1
    assert bash.stdout == ps.stdout == py.stdout == ""
    expected = f"Error: feature number must be between 0 and {2**63 - 1}, got '{2**63}'"
    for result in (bash, ps, py):
        assert expected in _normalized_error_text(result.stderr, repo)


@requires_bash
@pytest.mark.skipif(not HAS_POWERSHELL, reason="no PowerShell available")
@pytest.mark.parametrize("prefix", [2**63, 2**64 + 5])
def test_all_variants_ignore_out_of_range_existing_prefix(
    repo: Path, prefix: int
) -> None:
    (repo / "specs" / f"{prefix}-existing").mkdir(parents=True)

    bash = run(bash_cmd(repo, SCRIPT, "--json", "--dry-run", "x"), repo)
    ps = run(ps_cmd(repo, SCRIPT, "-Json", "-DryRun", "x"), repo)
    py = run(py_cmd(repo, SCRIPT, "--json", "--dry-run", "x"), repo)

    assert bash.returncode == ps.returncode == py.returncode == 0
    assert json_stdout(bash) == json_stdout(ps) == json_stdout(py)
    assert json_stdout(py)["FEATURE_NUM"] == "001"


def test_python_ignores_unconvertibly_large_existing_prefix() -> None:
    class Entry:
        name = f"{'9' * 5000}-existing"

        @staticmethod
        def is_dir() -> bool:
            return True

    class SpecsDir:
        @staticmethod
        def is_dir() -> bool:
            return True

        @staticmethod
        def iterdir() -> list[Entry]:
            return [Entry()]

    assert create_new_feature._get_highest_from_specs(SpecsDir()) == 0


@requires_bash
@pytest.mark.skipif(not HAS_POWERSHELL, reason="no PowerShell available")
def test_all_variants_text_mode_match(repo: Path) -> None:
    bash = run(bash_cmd(repo, SCRIPT, "--dry-run", "--number", "7", "x"), repo)
    ps = run(ps_cmd(repo, SCRIPT, "-DryRun", "-Number", "7", "x"), repo)
    py = run(py_cmd(repo, SCRIPT, "--dry-run", "--number", "7", "x"), repo)

    assert bash.returncode == ps.returncode == py.returncode == 0
    assert bash.stderr == ps.stderr == py.stderr == ""
    assert (
        normalize_repo_paths(bash.stdout, repo)
        == normalize_repo_paths(ps.stdout, repo)
        == normalize_repo_paths(py.stdout, repo)
    )


@requires_bash
@pytest.mark.skipif(not HAS_POWERSHELL, reason="no PowerShell available")
def test_all_variants_non_dry_text_mode_match(tmp_path: Path) -> None:
    bash_repo = _setup_repo(tmp_path, "bash")
    ps_repo = _setup_repo(tmp_path, "powershell")
    py_repo = _setup_repo(tmp_path, "python")

    bash = run(
        bash_cmd(bash_repo, SCRIPT, "--number", "7", "x"), bash_repo
    )
    ps = run(
        ps_cmd(ps_repo, SCRIPT, "-Number", "7", "x"), ps_repo
    )
    py = run(py_cmd(py_repo, SCRIPT, "--number", "7", "x"), py_repo)

    assert bash.returncode == ps.returncode == py.returncode == 0
    assert (
        normalize_repo_paths(bash.stdout, bash_repo)
        == normalize_repo_paths(py.stdout, py_repo)
    )
    assert (
        normalize_repo_paths(bash.stderr, bash_repo)
        == normalize_repo_paths(py.stderr, py_repo)
    )
    ps_stdout = normalize_repo_paths(ps.stdout, ps_repo)
    ps_stderr = normalize_repo_paths(ps.stderr, ps_repo)
    assert "$env:SPECIFY_FEATURE = '007-x'" in ps_stdout
    assert (
        "$env:SPECIFY_FEATURE_DIRECTORY = '<REPO>/specs/007-x'" in ps_stdout
    )
    assert "$env:SPECIFY_FEATURE = '007-x'" in ps_stderr
    assert (
        "$env:SPECIFY_FEATURE_DIRECTORY = '<REPO>/specs/007-x'" in ps_stderr
    )


@requires_bash
def test_python_persist_hints_match_bash_for_spaced_repo_path(
    tmp_path: Path,
) -> None:
    """Paths with spaces must be quoted identically (shlex.quote format) so
    the side-by-side text/stderr comparison holds."""
    bash_repo = _setup_repo(tmp_path, "my proj a")
    py_repo = _setup_repo(tmp_path, "my proj b")

    bash = run(bash_cmd(bash_repo, SCRIPT, "--number", "7", "x"), bash_repo)
    py = run(py_cmd(py_repo, SCRIPT, "--number", "7", "x"), py_repo)

    assert bash.returncode == py.returncode == 0, bash.stderr + py.stderr
    assert normalize_repo_paths(bash.stdout, bash_repo) == normalize_repo_paths(
        py.stdout, py_repo
    )
    assert normalize_repo_paths(bash.stderr, bash_repo) == normalize_repo_paths(
        py.stderr, py_repo
    )
    assert "export SPECIFY_FEATURE_DIRECTORY='<REPO>/specs/007-x'" in (
        normalize_repo_paths(py.stderr, py_repo)
    )


def test_python_powershell_persistence_assignments_escape_quotes() -> None:
    assert create_new_feature._persistence_assignments(
        "007-x", r"C:\repo\O'Brien", powershell=True
    ) == (
        "$env:SPECIFY_FEATURE = '007-x'",
        "$env:SPECIFY_FEATURE_DIRECTORY = 'C:\\repo\\O''Brien'",
    )


@requires_bash
@pytest.mark.skipif(not HAS_POWERSHELL, reason="no PowerShell available")
def test_all_variants_persist_symlinked_specs_path_lexically(
    tmp_path: Path,
) -> None:
    repos = [
        _setup_repo(tmp_path, "bash"),
        _setup_repo(tmp_path, "powershell"),
        _setup_repo(tmp_path, "python"),
    ]
    for current in repos:
        specs_target = tmp_path / f"{current.name}-specs"
        specs_target.mkdir()
        try:
            (current / "specs").symlink_to(
                specs_target, target_is_directory=True
            )
        except (OSError, NotImplementedError):
            pytest.skip("Symlinks are not available in this environment")

    bash = run(
        bash_cmd(repos[0], SCRIPT, "--json", "--number", "7", "x"),
        repos[0],
    )
    ps = run(
        ps_cmd(repos[1], SCRIPT, "-Json", "-Number", "7", "x"),
        repos[1],
    )
    py = run(
        py_cmd(repos[2], SCRIPT, "--json", "--number", "7", "x"),
        repos[2],
    )

    assert bash.returncode == ps.returncode == py.returncode == 0
    expected = '{"feature_directory":"specs/007-x"}'
    for current in repos:
        assert (
            current / ".specify" / "feature.json"
        ).read_text(encoding="utf-8").strip() == expected


@requires_bash
@pytest.mark.skipif(not HAS_POWERSHELL, reason="no PowerShell available")
def test_all_variants_allow_existing_branch(repo: Path) -> None:
    feature_dir = repo / "specs" / "001-x"
    feature_dir.mkdir(parents=True)
    spec_file = feature_dir / "spec.md"
    spec_file.write_text("existing\n", encoding="utf-8")

    bash = run(
        bash_cmd(
            repo,
            SCRIPT,
            "--json",
            "--number",
            "1",
            "--allow-existing-branch",
            "x",
        ),
        repo,
    )
    ps = run(
        ps_cmd(
            repo,
            SCRIPT,
            "-Json",
            "-Number",
            "1",
            "-AllowExistingBranch",
            "x",
        ),
        repo,
    )
    py = run(
        py_cmd(
            repo,
            SCRIPT,
            "--json",
            "--number",
            "1",
            "--allow-existing-branch",
            "x",
        ),
        repo,
    )

    assert bash.returncode == ps.returncode == py.returncode == 0
    assert json_stdout(bash) == json_stdout(ps) == json_stdout(py)
    assert spec_file.read_text(encoding="utf-8") == "existing\n"


@requires_bash
@pytest.mark.skipif(not HAS_POWERSHELL, reason="no PowerShell available")
def test_all_variants_existing_directory_failure_diagnostics(repo: Path) -> None:
    (repo / "specs" / "001-x").mkdir(parents=True)
    expected = (
        "Error: Feature directory '<REPO>/specs/001-x' already exists. "
        "Please use a different feature name or specify a different number "
        "with --number."
    )

    bash = run(bash_cmd(repo, SCRIPT, "--json", "--number", "1", "x"), repo)
    ps = run(ps_cmd(repo, SCRIPT, "-Json", "-Number", "1", "x"), repo)
    py = run(py_cmd(repo, SCRIPT, "--json", "--number", "1", "x"), repo)

    assert bash.returncode == ps.returncode == py.returncode == 1
    assert bash.stdout == ps.stdout == py.stdout == ""
    for result in (bash, ps, py):
        assert expected in _normalized_error_text(result.stderr, repo)
