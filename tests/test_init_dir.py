"""Tests for the SPECIFY_INIT_DIR project-root override.

SPECIFY_INIT_DIR lets a non-interactive / CI caller target a member project from
outside its directory (e.g. a monorepo root) without `cd`. It names the project
root — the directory *containing* `.specify/` — and is strict: it must exist and
contain `.specify/`, otherwise the resolver hard-errors with no silent fallback to
cwd or the git toplevel.

See proposals/monorepo-support and github/spec-kit discussion #2834.
"""

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

from tests.conftest import requires_bash

PROJECT_ROOT = Path(__file__).resolve().parent.parent
COMMON_SH = PROJECT_ROOT / "scripts" / "bash" / "common.sh"
COMMON_PS = PROJECT_ROOT / "scripts" / "powershell" / "common.ps1"
GIT_CREATE_FEATURE_SH = (
    PROJECT_ROOT / "extensions" / "git" / "scripts" / "bash" / "create-new-feature-branch.sh"
)

HAS_PWSH = shutil.which("pwsh") is not None
_POWERSHELL = shutil.which("powershell.exe") or shutil.which("powershell")
_PS_EXE = "pwsh" if HAS_PWSH else _POWERSHELL


def _clean_env() -> dict[str, str]:
    """Inherited env minus all SPECIFY_* vars, so a developer/CI override
    (SPECIFY_FEATURE, SPECIFY_FEATURE_DIRECTORY, …) cannot leak into the
    subprocess and make these resolution tests flaky."""
    env = os.environ.copy()
    for key in list(env):
        if key.startswith("SPECIFY_"):
            env.pop(key)
    return env


def _make_project(root: Path, name: str) -> Path:
    """Create <root>/<name>/.specify (the minimal Spec Kit project marker)."""
    proj = root / name
    (proj / ".specify").mkdir(parents=True)
    return proj


def _bash(func_call: str, cwd: Path, env: dict[str, str]) -> subprocess.CompletedProcess:
    """Source the real common.sh and run a function, from a given cwd/env."""
    return subprocess.run(
        ["bash", "-c", f'source "{COMMON_SH}" && {func_call}'],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )


def _ps(script: str, cwd: Path, env: dict[str, str]) -> subprocess.CompletedProcess:
    """Dot-source the real common.ps1 and run PowerShell, from a given cwd/env."""
    return subprocess.run(
        [_PS_EXE, "-NoProfile", "-Command", f'. "{COMMON_PS}"; {script}'],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )


def _feature_dir_line(stdout: str) -> str | None:
    for line in stdout.splitlines():
        if line.startswith("FEATURE_DIR="):
            return line.split("=", 1)[1].strip("'\"")
    return None


def _bash_path(path: Path) -> str:
    """Return the path format emitted by Bash `pwd`.

    Git-for-Windows Bash reports absolute paths as /c/... while pathlib reports
    them as C:\\..., so Bash stdout comparisons need an expected value in Bash's
    own path shape.
    """
    if os.name != "nt":
        return str(path)

    resolved = path.resolve()
    path_str = str(resolved).replace("\\", "/")
    if resolved.drive.endswith(":"):
        return f"/{resolved.drive[0].lower()}{path_str[len(resolved.drive):]}"
    return path_str


requires_pwsh = pytest.mark.skipif(
    not (HAS_PWSH or _POWERSHELL), reason="no PowerShell available"
)


# ── Bash: positive cases ────────────────────────────────────────────────────


@requires_bash
def test_valid_path_resolves_from_outside(tmp_path: Path) -> None:
    """P1: a valid project path resolves correctly when run from elsewhere."""
    web = _make_project(tmp_path, "web")
    env = {**_clean_env(), "SPECIFY_INIT_DIR": str(web)}
    result = _bash("get_repo_root", cwd=tmp_path, env=env)
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == _bash_path(web)


@requires_bash
def test_relative_path_normalized_against_cwd(tmp_path: Path) -> None:
    """P2: a relative SPECIFY_INIT_DIR is resolved against the current directory."""
    web = _make_project(tmp_path, "web")
    env = {**_clean_env(), "SPECIFY_INIT_DIR": "web"}
    result = _bash("get_repo_root", cwd=tmp_path, env=env)
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == _bash_path(web)


@requires_bash
def test_trailing_slash_tolerated(tmp_path: Path) -> None:
    """P3: a trailing slash is collapsed by normalization."""
    web = _make_project(tmp_path, "web")
    env = {**_clean_env(), "SPECIFY_INIT_DIR": f"{web}/"}
    result = _bash("get_repo_root", cwd=tmp_path, env=env)
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == _bash_path(web)


@requires_bash
def test_precedence_over_cwd_project(tmp_path: Path) -> None:
    """P4: feature resolution happens inside the *target* project, not cwd.

    cwd is itself a valid Spec Kit project; SPECIFY_INIT_DIR must redirect
    resolution to the target project, so a relative SPECIFY_FEATURE_DIRECTORY
    normalizes under the target root, not cwd.
    """
    cwd_proj = _make_project(tmp_path, "cwd_proj")
    (cwd_proj / "specs" / "001-cwd").mkdir(parents=True)
    web = _make_project(tmp_path, "web")

    env = {
        **_clean_env(),
        "SPECIFY_INIT_DIR": str(web),
        "SPECIFY_FEATURE_DIRECTORY": "specs/001-demo",
    }
    result = _bash("get_feature_paths", cwd=cwd_proj, env=env)
    assert result.returncode == 0, result.stderr
    assert _feature_dir_line(result.stdout) == _bash_path(web / "specs" / "001-demo")
    assert _bash_path(cwd_proj) not in result.stdout


@requires_bash
def test_composes_with_feature_directory_override(tmp_path: Path) -> None:
    """P5: SPECIFY_INIT_DIR (project axis) composes with SPECIFY_FEATURE_DIRECTORY
    (feature axis); a relative feature dir normalizes under the *target* root."""
    web = _make_project(tmp_path, "web")
    env = {
        **_clean_env(),
        "SPECIFY_INIT_DIR": str(web),
        "SPECIFY_FEATURE_DIRECTORY": "specs/003-x",
    }
    result = _bash("get_feature_paths", cwd=tmp_path, env=env)
    assert result.returncode == 0, result.stderr
    assert _feature_dir_line(result.stdout) == _bash_path(web / "specs" / "003-x")


@requires_bash
def test_composes_with_target_feature_json(tmp_path: Path) -> None:
    """P6: the target project's .specify/feature.json is honored."""
    web = _make_project(tmp_path, "web")
    (web / ".specify" / "feature.json").write_text(
        '{"feature_directory": "specs/004-fj"}'
    )
    env = {**_clean_env(), "SPECIFY_INIT_DIR": str(web)}
    result = _bash("get_feature_paths", cwd=tmp_path, env=env)
    assert result.returncode == 0, result.stderr
    assert _feature_dir_line(result.stdout) == _bash_path(web / "specs" / "004-fj")


# ── Bash: negative / contract cases ─────────────────────────────────────────


@requires_bash
def test_unset_preserves_cwd_walk(tmp_path: Path) -> None:
    """N1: with SPECIFY_INIT_DIR unset, resolution walks up from cwd as before."""
    web = _make_project(tmp_path, "web")
    sub = web / "src" / "deep"
    sub.mkdir(parents=True)
    result = _bash("get_repo_root", cwd=sub, env=_clean_env())
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == _bash_path(web)


@requires_bash
def test_empty_string_treated_as_unset(tmp_path: Path) -> None:
    """N2: an empty SPECIFY_INIT_DIR behaves as unset (not as ".").

    Run from a deep subdirectory so the two interpretations diverge:
    empty-as-unset walks up to the project root; empty-as-"." would resolve to
    the cwd (which has no .specify/) and error. Asserting the walk-up result
    genuinely guards against a regression to "." semantics.
    """
    web = _make_project(tmp_path, "web")
    sub = web / "src" / "deep"
    sub.mkdir(parents=True)
    env = {**_clean_env(), "SPECIFY_INIT_DIR": ""}
    result = _bash("get_repo_root", cwd=sub, env=env)
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == _bash_path(web)


@requires_bash
def test_invalid_init_dir_fails_feature_paths_chain(tmp_path: Path) -> None:
    """N5: an invalid SPECIFY_INIT_DIR hard-fails the load-bearing call site
    (get_feature_paths), not just get_repo_root — this is what the decl/assign
    split guards against (a `local x=$(get_repo_root)` would mask the failure
    and emit a FEATURE_DIR under the wrong root). SPECIFY_FEATURE_DIRECTORY is
    set so a feature dir *is* resolvable — only the propagation stops a
    wrong-root FEATURE_DIR, so a revert to the masked form fails this test."""
    web = _make_project(tmp_path, "web")  # valid project at cwd
    missing = tmp_path / "does_not_exist"
    env = {
        **_clean_env(),
        "SPECIFY_INIT_DIR": str(missing),
        "SPECIFY_FEATURE_DIRECTORY": "specs/001-x",
    }
    result = _bash("get_feature_paths", cwd=web, env=env)
    assert result.returncode != 0
    assert "does not point to an existing directory" in result.stderr
    assert "FEATURE_DIR=" not in result.stdout


@requires_bash
def test_nonexistent_path_errors_no_fallback(tmp_path: Path) -> None:
    """N3: a non-existent path hard-errors — even from inside a valid project,
    proving there is no silent fallback to the cwd walk-up or git root."""
    web = _make_project(tmp_path, "web")  # valid project at cwd
    missing = tmp_path / "does_not_exist"
    env = {**_clean_env(), "SPECIFY_INIT_DIR": str(missing)}
    result = _bash("get_repo_root", cwd=web, env=env)
    assert result.returncode != 0
    assert "does not point to an existing directory" in result.stderr
    assert _bash_path(web) not in result.stdout


@requires_bash
def test_path_without_specify_errors_no_fallback(tmp_path: Path) -> None:
    """N4: a path that exists but lacks .specify/ hard-errors, no fallback."""
    web = _make_project(tmp_path, "web")  # valid project at cwd
    nodot = tmp_path / "nodot"
    nodot.mkdir()
    env = {**_clean_env(), "SPECIFY_INIT_DIR": str(nodot)}
    result = _bash("get_repo_root", cwd=web, env=env)
    assert result.returncode != 0
    assert "not a Spec Kit project" in result.stderr
    assert _bash_path(web) not in result.stdout


@requires_bash
def test_file_path_errors_no_fallback(tmp_path: Path) -> None:
    """N4b: a path that exists but is a file (not a directory) hard-errors with
    the existing-directory message, with no fallback."""
    web = _make_project(tmp_path, "web")  # valid project at cwd
    a_file = tmp_path / "afile"
    a_file.write_text("x")
    env = {**_clean_env(), "SPECIFY_INIT_DIR": str(a_file)}
    result = _bash("get_repo_root", cwd=web, env=env)
    assert result.returncode != 0
    assert "does not point to an existing directory" in result.stderr
    assert _bash_path(web) not in result.stdout


# ── Bash: bundled Git extension entrypoint ──────────────────────────────────


def _bash_git_create(
    args: list[str], cwd: Path, env: dict[str, str]
) -> subprocess.CompletedProcess:
    """Run the bundled git extension's create-new-feature-branch.sh (the real
    /speckit.specify before_specify entrypoint)."""
    return subprocess.run(
        ["bash", str(GIT_CREATE_FEATURE_SH), *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )


def _json_line(stdout: str) -> dict | None:
    for line in stdout.splitlines():
        line = line.strip()
        if line.startswith("{"):
            return json.loads(line)
    return None


@requires_bash
def test_git_ext_create_feature_numbers_from_target(tmp_path: Path) -> None:
    """P8: the git extension's feature creation numbers from the SPECIFY_INIT_DIR
    project, not the cwd project."""
    (tmp_path / "specs" / "008-cwd").mkdir(parents=True)  # cwd project's specs
    web = _make_project(tmp_path, "web")
    (web / ".specify" / "templates").mkdir(parents=True, exist_ok=True)
    (web / ".specify" / "templates" / "spec-template.md").write_text("# Spec: [FEATURE]\n")
    (web / "specs" / "005-existing").mkdir(parents=True)

    env = {**_clean_env(), "SPECIFY_INIT_DIR": str(web)}
    result = _bash_git_create(["--json", "next thing"], cwd=tmp_path, env=env)
    assert result.returncode == 0, result.stderr
    data = _json_line(result.stdout)
    assert data is not None and data["FEATURE_NUM"] == "006"  # 005 in web → 006, not 009


@requires_bash
def test_git_ext_create_feature_invalid_init_dir_errors(tmp_path: Path) -> None:
    """N7: the git extension hard-errors on an invalid SPECIFY_INIT_DIR with no
    fallback to the cwd/git-toplevel project."""
    web = _make_project(tmp_path, "web")  # valid project at cwd
    (web / "specs" / "001-cwd").mkdir(parents=True)
    missing = tmp_path / "does_not_exist"
    env = {**_clean_env(), "SPECIFY_INIT_DIR": str(missing)}
    result = _bash_git_create(["--json", "x"], cwd=web, env=env)
    assert result.returncode != 0
    assert "does not point to an existing directory" in result.stderr
    assert _json_line(result.stdout) is None


# ── PowerShell mirror (skipped only when no PowerShell is installed; the CI
#    ubuntu/windows runners ship pwsh, so these DO run there) ─────────────────


@requires_pwsh
def test_ps_valid_path_resolves_from_outside(tmp_path: Path) -> None:
    web = _make_project(tmp_path, "web")
    env = {**_clean_env(), "SPECIFY_INIT_DIR": str(web)}
    result = _ps("Get-RepoRoot", cwd=tmp_path, env=env)
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == str(web)


@requires_pwsh
def test_ps_relative_path_normalized_against_cwd(tmp_path: Path) -> None:
    web = _make_project(tmp_path, "web")
    env = {**_clean_env(), "SPECIFY_INIT_DIR": "web"}
    result = _ps("Get-RepoRoot", cwd=tmp_path, env=env)
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == str(web)


@requires_pwsh
def test_ps_trailing_slash_tolerated(tmp_path: Path) -> None:
    web = _make_project(tmp_path, "web")
    env = {**_clean_env(), "SPECIFY_INIT_DIR": f"{web}/"}
    result = _ps("Get-RepoRoot", cwd=tmp_path, env=env)
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == str(web)


@requires_pwsh
def test_ps_unset_preserves_cwd_walk(tmp_path: Path) -> None:
    web = _make_project(tmp_path, "web")
    sub = web / "src" / "deep"
    sub.mkdir(parents=True)
    result = _ps("Get-RepoRoot", cwd=sub, env=_clean_env())
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == str(web)


@requires_pwsh
def test_ps_precedence_over_cwd_project(tmp_path: Path) -> None:
    cwd_proj = _make_project(tmp_path, "cwd_proj")
    (cwd_proj / "specs" / "001-cwd").mkdir(parents=True)
    web = _make_project(tmp_path, "web")
    env = {
        **_clean_env(),
        "SPECIFY_INIT_DIR": str(web),
        "SPECIFY_FEATURE_DIRECTORY": "specs/001-demo",
    }
    result = _ps(
        '$r = Get-FeaturePathsEnv; Write-Output "FEATURE_DIR=$($r.FEATURE_DIR)"',
        cwd=cwd_proj,
        env=env,
    )
    assert result.returncode == 0, result.stderr
    # PowerShell Join-Path keeps the embedded "/" of the relative feature dir
    # while pathlib uses the platform separator; compare separator-insensitively
    # so the Windows CI runner (where pwsh runs) matches.
    feature_dir = _feature_dir_line(result.stdout)
    assert feature_dir is not None, result.stdout
    assert feature_dir.replace("\\", "/") == (web / "specs" / "001-demo").as_posix()
    assert str(cwd_proj) not in result.stdout


@requires_pwsh
def test_ps_composes_with_feature_directory_override(tmp_path: Path) -> None:
    web = _make_project(tmp_path, "web")
    env = {
        **_clean_env(),
        "SPECIFY_INIT_DIR": str(web),
        "SPECIFY_FEATURE_DIRECTORY": "specs/003-x",
    }
    result = _ps(
        '$r = Get-FeaturePathsEnv; Write-Output "FEATURE_DIR=$($r.FEATURE_DIR)"',
        cwd=tmp_path,
        env=env,
    )
    assert result.returncode == 0, result.stderr
    # Separator-insensitive: PowerShell Join-Path keeps the embedded "/".
    feature_dir = _feature_dir_line(result.stdout)
    assert feature_dir is not None, result.stdout
    assert feature_dir.replace("\\", "/") == (web / "specs" / "003-x").as_posix()


@requires_pwsh
def test_ps_empty_string_treated_as_unset(tmp_path: Path) -> None:
    web = _make_project(tmp_path, "web")
    sub = web / "src" / "deep"
    sub.mkdir(parents=True)
    env = {**_clean_env(), "SPECIFY_INIT_DIR": ""}
    result = _ps("Get-RepoRoot", cwd=sub, env=env)
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == str(web)


@requires_pwsh
def test_ps_nonexistent_path_errors_no_fallback(tmp_path: Path) -> None:
    web = _make_project(tmp_path, "web")
    missing = tmp_path / "does_not_exist"
    env = {**_clean_env(), "SPECIFY_INIT_DIR": str(missing)}
    result = _ps("Get-RepoRoot", cwd=web, env=env)
    assert result.returncode != 0
    assert "does not point to an existing directory" in result.stderr


@requires_pwsh
def test_ps_path_without_specify_errors_no_fallback(tmp_path: Path) -> None:
    web = _make_project(tmp_path, "web")
    nodot = tmp_path / "nodot"
    nodot.mkdir()
    env = {**_clean_env(), "SPECIFY_INIT_DIR": str(nodot)}
    result = _ps("Get-RepoRoot", cwd=web, env=env)
    assert result.returncode != 0
    assert "not a Spec Kit project" in result.stderr


@requires_pwsh
def test_ps_file_path_errors_no_fallback(tmp_path: Path) -> None:
    """A file path resolves via Resolve-Path but is not a directory; the resolver
    must reject it with the existing-directory message, not not-a-project."""
    web = _make_project(tmp_path, "web")
    a_file = tmp_path / "afile"
    a_file.write_text("x")
    env = {**_clean_env(), "SPECIFY_INIT_DIR": str(a_file)}
    result = _ps("Get-RepoRoot", cwd=web, env=env)
    assert result.returncode != 0
    assert "does not point to an existing directory" in result.stderr
