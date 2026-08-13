"""Parity tests for the Python check-prerequisites PoC."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from tests.conftest import requires_bash
from tests.parity_helpers import install_composition_stack

PROJECT_ROOT = Path(__file__).resolve().parent.parent
COMMON_SH = PROJECT_ROOT / "scripts" / "bash" / "common.sh"
CHECK_PREREQS_SH = PROJECT_ROOT / "scripts" / "bash" / "check-prerequisites.sh"
COMMON_PS = PROJECT_ROOT / "scripts" / "powershell" / "common.ps1"
CHECK_PREREQS_PS = PROJECT_ROOT / "scripts" / "powershell" / "check-prerequisites.ps1"
COMMON_PY = PROJECT_ROOT / "scripts" / "python" / "common.py"
CHECK_PREREQS_PY = PROJECT_ROOT / "scripts" / "python" / "check_prerequisites.py"

HAS_PWSH = shutil.which("pwsh") is not None
_WINDOWS_POWERSHELL = (
    shutil.which("powershell.exe") or shutil.which("powershell")
) if os.name == "nt" else None


def _install_scripts(repo: Path) -> None:
    bash_dir = repo / ".specify" / "scripts" / "bash"
    bash_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy(COMMON_SH, bash_dir / "common.sh")
    shutil.copy(CHECK_PREREQS_SH, bash_dir / "check-prerequisites.sh")

    ps_dir = repo / ".specify" / "scripts" / "powershell"
    ps_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy(COMMON_PS, ps_dir / "common.ps1")
    shutil.copy(CHECK_PREREQS_PS, ps_dir / "check-prerequisites.ps1")

    py_dir = repo / ".specify" / "scripts" / "python"
    py_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy(COMMON_PY, py_dir / "common.py")
    shutil.copy(CHECK_PREREQS_PY, py_dir / "check_prerequisites.py")


def _write_feature_json(
    repo: Path, feature_directory: str = "specs/001-my-feature"
) -> None:
    (repo / ".specify" / "feature.json").write_text(
        json.dumps({"feature_directory": feature_directory}, separators=(",", ":"))
        + "\n",
        encoding="utf-8",
    )


def _clean_env() -> dict[str, str]:
    env = os.environ.copy()
    for key in list(env):
        if key.startswith("SPECIFY_"):
            env.pop(key)
    return env


def _git_init(repo: Path) -> None:
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"], cwd=repo, check=True
    )
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo, check=True)
    subprocess.run(
        ["git", "commit", "--allow-empty", "-m", "init", "-q"], cwd=repo, check=True
    )


@pytest.fixture
def prereq_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "proj"
    repo.mkdir()
    _git_init(repo)
    (repo / ".specify").mkdir()
    _install_scripts(repo)
    return repo


def _py_cmd(repo: Path, *args: str) -> list[str]:
    script = repo / ".specify" / "scripts" / "python" / "check_prerequisites.py"
    return [sys.executable, str(script), *args]


def _repo_copy_py_cmd(repo: Path, *args: str) -> list[str]:
    script = repo / "scripts" / "python" / "check_prerequisites.py"
    return [sys.executable, str(script), *args]


def _bash_cmd(repo: Path, *args: str) -> list[str]:
    script = repo / ".specify" / "scripts" / "bash" / "check-prerequisites.sh"
    return ["bash", str(script), *args]


def _ps_cmd(repo: Path, *args: str) -> list[str]:
    script = repo / ".specify" / "scripts" / "powershell" / "check-prerequisites.ps1"
    exe = "pwsh" if HAS_PWSH else _WINDOWS_POWERSHELL
    return [exe, "-NoProfile", "-File", str(script), *args]


def _run(
    cmd: list[str], repo: Path, env: dict[str, str] | None = None
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
        env=env or _clean_env(),
    )


def _json_stdout(result: subprocess.CompletedProcess[str]) -> object:
    return json.loads(result.stdout)


def _normalize_status_text(text: str) -> str:
    return (
        text.replace("  ✓ ", "  [OK] ")
        .replace("  ✗ ", "  [FAIL] ")
        .replace("\r\n", "\n")
    )


def _normalize_help_text(text: str) -> str:
    normalized = text.replace("\r\n", "\n").replace(
        "check-prerequisites.sh", "check_prerequisites.py"
    )
    return "\n".join("" if not line.strip() else line for line in normalized.split("\n"))


@requires_bash
@pytest.mark.parametrize("missing", [False, True], ids=["composed", "missing"])
def test_all_variants_resolve_requested_template(
    prereq_repo: Path, missing: bool
) -> None:
    _write_feature_json(prereq_repo)
    feature = prereq_repo / "specs" / "001-my-feature"
    feature.mkdir(parents=True)
    (feature / "plan.md").write_text("# Plan\n", encoding="utf-8")
    template_name = "missing-template" if missing else "checklist-template"
    expected = install_composition_stack(
        prereq_repo, "checklist-template", "# Checklist\n"
    )

    results = [
        _run(
            _bash_cmd(prereq_repo, "--json", "--template", template_name),
            prereq_repo,
        ),
        _run(
            _py_cmd(prereq_repo, "--json", "--template", template_name),
            prereq_repo,
        ),
    ]
    if HAS_PWSH or _WINDOWS_POWERSHELL:
        results.append(
            _run(
                _ps_cmd(prereq_repo, "-Json", "-Template", template_name),
                prereq_repo,
            )
        )

    expected_status = 1 if missing else 0
    assert all(result.returncode == expected_status for result in results)
    if missing:
        assert all(result.stdout == "" for result in results)
    else:
        assert all(
            _json_stdout(result)["TEMPLATE_CONTENT"] == expected
            for result in results
        )


@requires_bash
@pytest.mark.parametrize("missing", [False, True], ids=["composed", "missing"])
def test_all_variants_validate_requested_template_in_text_mode(
    prereq_repo: Path, missing: bool
) -> None:
    _write_feature_json(prereq_repo)
    feature = prereq_repo / "specs" / "001-my-feature"
    feature.mkdir(parents=True)
    (feature / "plan.md").write_text("# Plan\n", encoding="utf-8")
    template_name = "missing-template" if missing else "checklist-template"
    install_composition_stack(
        prereq_repo, "checklist-template", "# Checklist\n"
    )

    results = [
        _run(
            _bash_cmd(prereq_repo, "--template", template_name),
            prereq_repo,
        ),
        _run(
            _py_cmd(prereq_repo, "--template", template_name),
            prereq_repo,
        ),
    ]
    if HAS_PWSH or _WINDOWS_POWERSHELL:
        results.append(
            _run(
                _ps_cmd(prereq_repo, "-Template", template_name),
                prereq_repo,
            )
        )

    expected_status = 1 if missing else 0
    assert all(result.returncode == expected_status for result in results)
    if missing:
        assert all(result.stdout == "" for result in results)


@requires_bash
@pytest.mark.parametrize(
    "args",
    [
        ("--json",),
        ("--json", "--include-tasks"),
        ("--json", "--require-tasks", "--include-tasks"),
        ("--json", "--paths-only"),
    ],
)
def test_python_json_output_matches_bash(prereq_repo: Path, args: tuple[str, ...]) -> None:
    feat = prereq_repo / "specs" / "001-my-feature"
    feat.mkdir(parents=True)
    (feat / "plan.md").write_text("# plan\n", encoding="utf-8")
    (feat / "tasks.md").write_text("# tasks\n", encoding="utf-8")
    (feat / "research.md").write_text("# research\n", encoding="utf-8")
    (feat / "data-model.md").write_text("# model\n", encoding="utf-8")
    (feat / "quickstart.md").write_text("# quickstart\n", encoding="utf-8")
    (feat / "contracts" / "v1").mkdir(parents=True)
    _write_feature_json(prereq_repo)

    bash = _run(_bash_cmd(prereq_repo, *args), prereq_repo)
    py = _run(_py_cmd(prereq_repo, *args), prereq_repo)

    assert py.returncode == bash.returncode == 0
    assert py.stderr == bash.stderr == ""
    assert _json_stdout(py) == _json_stdout(bash)


@requires_bash
def test_python_text_output_matches_bash(prereq_repo: Path) -> None:
    feat = prereq_repo / "specs" / "001-my-feature"
    feat.mkdir(parents=True)
    (feat / "plan.md").write_text("# plan\n", encoding="utf-8")
    (feat / "contracts").mkdir()
    _write_feature_json(prereq_repo)

    bash = _run(_bash_cmd(prereq_repo, "--include-tasks"), prereq_repo)
    py = _run(_py_cmd(prereq_repo, "--include-tasks"), prereq_repo)

    assert py.returncode == bash.returncode == 0
    assert py.stderr == bash.stderr == ""
    assert _normalize_status_text(py.stdout) == _normalize_status_text(bash.stdout)


def test_python_text_output_survives_a_legacy_stdout_code_page(
    prereq_repo: Path,
) -> None:
    """Text mode must not crash when stdout cannot encode the status glyphs.

    On Windows sys.stdout falls back to the ANSI code page whenever it is not a
    console — which is every time an agent or a workflow step captures the
    output. U+2713 is unencodable in cp1252, so printing it raised
    UnicodeEncodeError and truncated the report right after "AVAILABLE_DOCS:".
    The ASCII fallback is the rendering these markers already have in-tree
    (Test-FileExists in scripts/powershell/common.ps1, and
    normalize_status_text here).
    """
    feat = prereq_repo / "specs" / "001-my-feature"
    feat.mkdir(parents=True)
    (feat / "plan.md").write_text("# plan\n", encoding="utf-8")
    # research.md is present and the rest are not, so BOTH status markers are
    # produced in the same cp1252 subprocess: U+2713 for the available document
    # and U+2717 for the missing ones. Asserting only one of them would let a
    # fallback that always returned "[FAIL]" pass.
    (feat / "research.md").write_text("# research\n", encoding="utf-8")
    (feat / "contracts").mkdir()  # present but empty -> reported missing
    _write_feature_json(prereq_repo)

    env = _clean_env()
    env["PYTHONIOENCODING"] = "cp1252"
    result = _run(_py_cmd(prereq_repo, "--include-tasks"), prereq_repo, env=env)

    assert result.returncode == 0, result.stderr
    assert "UnicodeEncodeError" not in result.stderr
    assert "AVAILABLE_DOCS:" in result.stdout
    # Every per-document line must still be there, not truncated away by the
    # encode error.
    for doc in (
        "research.md",
        "data-model.md",
        "contracts/",
        "quickstart.md",
        "tasks.md",
    ):
        assert doc in result.stdout, (doc, result.stdout)
    # Both fallback markers, so neither branch of _status_marker can regress.
    assert "[OK] research.md" in result.stdout, result.stdout
    assert "[FAIL] quickstart.md" in result.stdout, result.stdout


@requires_bash
def test_python_help_output_matches_bash(prereq_repo: Path) -> None:
    bash = _run(_bash_cmd(prereq_repo, "--help"), prereq_repo)
    py = _run(_py_cmd(prereq_repo, "--help"), prereq_repo)

    assert py.returncode == bash.returncode == 0
    assert py.stderr == bash.stderr == ""
    assert _normalize_help_text(py.stdout) == _normalize_help_text(bash.stdout)


@requires_bash
def test_python_unknown_option_matches_bash_error_shape(prereq_repo: Path) -> None:
    bash = _run(_bash_cmd(prereq_repo, "--bogus"), prereq_repo)
    py = _run(_py_cmd(prereq_repo, "--bogus"), prereq_repo)

    assert py.returncode == bash.returncode == 1
    assert py.stdout == bash.stdout == ""
    assert py.stderr == bash.stderr


@pytest.mark.skipif(not (HAS_PWSH or _WINDOWS_POWERSHELL), reason="no PowerShell available")
@pytest.mark.parametrize(
    ("py_args", "ps_args"),
    [
        (("--json",), ("-Json",)),
        (("--json", "--include-tasks"), ("-Json", "-IncludeTasks")),
        (
            ("--json", "--require-tasks", "--include-tasks"),
            ("-Json", "-RequireTasks", "-IncludeTasks"),
        ),
        (("--json", "--paths-only"), ("-Json", "-PathsOnly")),
    ],
    ids=[
        "json",
        "json_include_tasks",
        "json_require_tasks_include_tasks",
        "json_paths_only",
    ],
)
def test_python_json_output_matches_powershell(
    prereq_repo: Path, py_args: tuple[str, ...], ps_args: tuple[str, ...]
) -> None:
    feat = prereq_repo / "specs" / "001-my-feature"
    feat.mkdir(parents=True)
    (feat / "plan.md").write_text("# plan\n", encoding="utf-8")
    (feat / "tasks.md").write_text("# tasks\n", encoding="utf-8")
    (feat / "research.md").write_text("# research\n", encoding="utf-8")
    (feat / "data-model.md").write_text("# model\n", encoding="utf-8")
    (feat / "quickstart.md").write_text("# quickstart\n", encoding="utf-8")
    (feat / "contracts" / "v1").mkdir(parents=True)
    _write_feature_json(prereq_repo)

    ps = _run(_ps_cmd(prereq_repo, *ps_args), prereq_repo)
    py = _run(_py_cmd(prereq_repo, *py_args), prereq_repo)

    assert py.returncode == ps.returncode == 0
    assert py.stderr == ps.stderr == ""
    assert _json_stdout(py) == _json_stdout(ps)


def test_python_repo_copy_script_file_fallback_finds_repo_root(tmp_path: Path) -> None:
    repo = tmp_path / "proj"
    outside = tmp_path / "outside"
    repo.mkdir()
    outside.mkdir()
    _git_init(repo)
    (repo / ".specify").mkdir()
    _write_feature_json(repo)
    (repo / "specs" / "001-my-feature").mkdir(parents=True)

    py_dir = repo / "scripts" / "python"
    py_dir.mkdir(parents=True)
    shutil.copy(COMMON_PY, py_dir / "common.py")
    shutil.copy(CHECK_PREREQS_PY, py_dir / "check_prerequisites.py")

    py = _run(_repo_copy_py_cmd(repo, "--json", "--paths-only"), outside)

    assert py.returncode == 0, py.stderr
    assert Path(_json_stdout(py)["REPO_ROOT"]) == repo


def test_python_paths_only_does_not_persist_feature_json(prereq_repo: Path) -> None:
    (prereq_repo / "specs" / "001-my-feature").mkdir(parents=True)
    (prereq_repo / "specs" / "002-other").mkdir(parents=True)
    _write_feature_json(prereq_repo, "specs/001-my-feature")
    feature_json = prereq_repo / ".specify" / "feature.json"
    before = feature_json.read_text(encoding="utf-8")
    env = _clean_env()
    env["SPECIFY_FEATURE_DIRECTORY"] = "specs/002-other"

    py = _run(_py_cmd(prereq_repo, "--json", "--paths-only"), prereq_repo, env=env)

    assert py.returncode == 0, py.stderr
    assert "002-other" in _json_stdout(py)["FEATURE_DIR"]
    assert feature_json.read_text(encoding="utf-8") == before


def test_python_normal_mode_persists_feature_json(prereq_repo: Path) -> None:
    (prereq_repo / "specs" / "001-my-feature").mkdir(parents=True)
    feat = prereq_repo / "specs" / "002-other"
    feat.mkdir(parents=True)
    (feat / "plan.md").write_text("# plan\n", encoding="utf-8")
    _write_feature_json(prereq_repo, "specs/001-my-feature")
    env = _clean_env()
    env["SPECIFY_FEATURE_DIRECTORY"] = "specs/002-other"

    py = _run(_py_cmd(prereq_repo, "--json"), prereq_repo, env=env)

    assert py.returncode == 0, py.stderr
    data = json.loads(
        (prereq_repo / ".specify" / "feature.json").read_text(encoding="utf-8")
    )
    assert data["feature_directory"] == "specs/002-other"


@requires_bash
def test_persisted_feature_json_is_lexical_when_specs_is_symlink(
    prereq_repo: Path, tmp_path: Path
) -> None:
    """A symlinked specs/ dir must persist "specs/NNN" like Bash does with its
    lexical prefix strip — resolve() would escape the repo and store a
    machine-specific absolute path."""
    real_specs = tmp_path / "real-specs"
    feat = real_specs / "002-other"
    feat.mkdir(parents=True)
    (feat / "plan.md").write_text("# plan\n", encoding="utf-8")
    repo = prereq_repo.resolve()
    try:
        (repo / "specs").symlink_to(real_specs, target_is_directory=True)
    except OSError:
        pytest.skip("symlinks not supported on this platform")
    env = _clean_env()
    env["SPECIFY_FEATURE_DIRECTORY"] = str(repo / "specs" / "002-other")
    feature_json = repo / ".specify" / "feature.json"

    bash = _run(_bash_cmd(prereq_repo, "--json"), prereq_repo, env=env)
    assert bash.returncode == 0, bash.stderr
    bash_persisted = json.loads(feature_json.read_text(encoding="utf-8"))
    feature_json.unlink()

    py = _run(_py_cmd(prereq_repo, "--json"), prereq_repo, env=env)
    assert py.returncode == 0, py.stderr
    py_persisted = json.loads(feature_json.read_text(encoding="utf-8"))

    assert py_persisted == bash_persisted
    assert py_persisted["feature_directory"] == "specs/002-other"


@pytest.mark.parametrize(
    ("args", "expected"),
    [
        (("--json",), "Feature directory not found"),
        (("--json",), "plan.md not found"),
        (("--json", "--require-tasks"), "tasks.md not found"),
    ],
    ids=["missing_feature_context", "missing_plan", "missing_tasks"],
)
def test_python_negative_errors_are_stderr_only(
    tmp_path: Path, args: tuple[str, ...], expected: str
) -> None:
    repo = tmp_path / "proj"
    repo.mkdir()
    _git_init(repo)
    (repo / ".specify").mkdir()
    _install_scripts(repo)

    if expected in {"plan.md not found", "tasks.md not found"}:
        feat = repo / "specs" / "001-my-feature"
        feat.mkdir(parents=True)
        _write_feature_json(repo)
        if expected == "tasks.md not found":
            (feat / "plan.md").write_text("# plan\n", encoding="utf-8")

    py = _run(_py_cmd(repo, *args), repo)

    assert py.returncode != 0
    assert expected in py.stderr
    assert expected not in py.stdout
    assert py.stdout.strip() == ""


def test_python_branch_falls_back_to_feature_dir_basename(prereq_repo: Path) -> None:
    (prereq_repo / "specs" / "001-my-feature").mkdir(parents=True)
    _write_feature_json(prereq_repo)

    py = _run(_py_cmd(prereq_repo, "--json", "--paths-only"), prereq_repo)

    assert py.returncode == 0, py.stderr
    assert _json_stdout(py)["BRANCH"] == "001-my-feature"


class TestGetInvokeSeparatorTolerance:
    """`get_invoke_separator` must fall back to "." for an unusable
    `integration.json`, matching its bash and PowerShell twins.

    The bash twin tries jq -> python3 -> awk and keeps its `separator="."`
    default on any parse failure; the PowerShell twin likewise returns ".".
    The Python twin instead indexed the parsed value directly, so two shapes
    escaped its `except (OSError, json.JSONDecodeError)`:

      * a non-mapping top level (`[]`, `"forge"`, `42`, `null`) is valid JSON,
        so JSONDecodeError never fires and `.get()` raised AttributeError;
      * a non-UTF-8 file raises UnicodeDecodeError -- a ValueError, not an
        OSError. Realistic on Windows, where PowerShell 5.1's `Out-File`/`>`
        default to UTF-16.

    The sibling `read_feature_json_feature_directory` in the same module
    already guards both.
    """

    @staticmethod
    def _load_common():
        import importlib.util

        spec = importlib.util.spec_from_file_location("_speckit_common_py", COMMON_PY)
        module = importlib.util.module_from_spec(spec)
        # Register before exec: the module defines @dataclass types, and
        # dataclasses resolves cls.__module__ through sys.modules.
        sys.modules[spec.name] = module
        try:
            spec.loader.exec_module(module)
        except Exception:  # pragma: no cover - defensive cleanup
            sys.modules.pop(spec.name, None)
            raise
        return module

    def _repo(self, tmp_path: Path, body: str | bytes) -> Path:
        (tmp_path / ".specify").mkdir(parents=True, exist_ok=True)
        target = tmp_path / ".specify" / "integration.json"
        if isinstance(body, bytes):
            target.write_bytes(body)
        else:
            target.write_text(body, encoding="utf-8")
        return tmp_path

    @pytest.mark.parametrize(
        "body", ["[]", '[{"a": 1}]', '"forge"', "42", "true", "null"]
    )
    def test_non_mapping_integration_json_falls_back(self, tmp_path: Path, body: str):
        common = self._load_common()
        assert common.get_invoke_separator(self._repo(tmp_path, body)) == "."

    def test_non_utf8_integration_json_falls_back(self, tmp_path: Path):
        common = self._load_common()
        raw = '{"default_integration": "forge"}'.encode("utf-16")
        assert common.get_invoke_separator(self._repo(tmp_path, raw)) == "."

    def test_hyphen_separator_is_still_honoured(self, tmp_path: Path):
        """Regression guard: the real feature must keep working."""
        common = self._load_common()
        body = json.dumps({
            "default_integration": "droid",
            "integration_settings": {"droid": {"invoke_separator": "-"}},
        })
        assert common.get_invoke_separator(self._repo(tmp_path, body)) == "-"


@pytest.mark.skipif(
    not (HAS_PWSH or _WINDOWS_POWERSHELL), reason="no PowerShell available"
)
def test_powershell_text_output_lists_available_docs(prereq_repo: Path) -> None:
    """Text mode must print a status line per document, like the twins.

    `Test-FileExists` / `Test-DirHasFiles` report their line with `Write-Output`
    and ALSO `return $true/$false`, both on the Success stream. The callers piped
    the whole call to `| Out-Null` to discard the boolean, which discarded the
    report line too — so `AVAILABLE_DOCS:` was emitted with nothing under it
    while the bash and Python twins list every document.
    """
    feat = prereq_repo / "specs" / "001-my-feature"
    feat.mkdir(parents=True)
    (feat / "plan.md").write_text("# plan\n", encoding="utf-8")
    (feat / "research.md").write_text("# research\n", encoding="utf-8")
    _write_feature_json(prereq_repo)

    ps = _run(_ps_cmd(prereq_repo, "-IncludeTasks"), prereq_repo)

    assert ps.returncode == 0, ps.stderr
    assert "AVAILABLE_DOCS:" in ps.stdout
    for doc in (
        "research.md",
        "data-model.md",
        "contracts/",
        "quickstart.md",
        "tasks.md",
    ):
        assert doc in ps.stdout, (doc, ps.stdout)
    # The existing file reports [OK], the missing ones [FAIL].
    assert "[OK] research.md" in _normalize_status_text(ps.stdout), ps.stdout
    assert "[FAIL] quickstart.md" in _normalize_status_text(ps.stdout), ps.stdout
