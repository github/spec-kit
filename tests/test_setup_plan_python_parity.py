"""Parity tests for the Python setup-plan port."""

from __future__ import annotations

import os
import stat
from pathlib import Path

import pytest

from scripts.python import common as python_common
from tests.conftest import requires_bash
from tests.parity_helpers import (
    HAS_POWERSHELL,
    POWERSHELL_EXE,
    WINDOWS_POWERSHELL,
    _bash_posix_path,
    bash_cmd,
    break_wrap_layer,
    clean_env,
    install_composition_stack,
    install_scripts,
    json_stdout,
    make_repo,
    make_python3_path_shim,
    normalize_repo_paths,
    ps_cmd,
    py_cmd,
    run,
    write_feature_json,
)

SCRIPT = "setup-plan"
TEMPLATE_BODY = "# Plan Template\n\nBody.\n"
POWERSHELL_PORTS = [
    pytest.param(
        "powershell",
        marks=pytest.mark.skipif(not HAS_POWERSHELL, reason="no PowerShell available"),
    ),
    pytest.param(
        "windows-powershell",
        marks=pytest.mark.skipif(
            not WINDOWS_POWERSHELL, reason="Windows PowerShell 5.1 not available"
        ),
    ),
]
PORTS = [pytest.param("bash", marks=requires_bash), *POWERSHELL_PORTS, "python"]


def _command(repo: Path, port: str, json_mode: bool) -> list[str]:
    if port == "windows-powershell":
        assert WINDOWS_POWERSHELL
        return [
            WINDOWS_POWERSHELL, "-NoProfile", "-File",
            str(repo / ".specify" / "scripts" / "powershell" / f"{SCRIPT}.ps1"),
            *(("-Json",) if json_mode else ()),
        ]
    if port == "powershell":
        return ps_cmd(repo, SCRIPT, *(("-Json",) if json_mode else ()))
    command = bash_cmd if port == "bash" else py_cmd
    return command(repo, SCRIPT, *(("--json",) if json_mode else ()))


def _setup_repo(tmp_path: Path, name: str = "proj", template: bool = True) -> Path:
    repo = make_repo(tmp_path, name)
    install_scripts(repo, SCRIPT)
    write_feature_json(repo)
    (repo / "specs" / "001-my-feature").mkdir(parents=True)
    if template:
        templates = repo / ".specify" / "templates"
        templates.mkdir(parents=True)
        (templates / "plan-template.md").write_text(TEMPLATE_BODY, encoding="utf-8")
    return repo


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    return _setup_repo(tmp_path)


@pytest.mark.parametrize("port", PORTS)
@pytest.mark.parametrize(
    "kind",
    ["relative", "absolute", "prefix", "ancestor_link", "dangling_ancestor", "link_parent"],
)
def test_stored_feature_cannot_escape_project(
    repo: Path, port: str, kind: str
) -> None:
    outside = repo.parent / ("proj-other" if kind == "prefix" else "outside")
    if kind in {"ancestor_link", "dangling_ancestor", "link_parent"}:
        if kind != "dangling_ancestor":
            outside.mkdir()
        try:
            (repo / "linked").symlink_to(outside, target_is_directory=True)
        except OSError as exc:
            pytest.skip(f"Cannot create directory symlink: {exc}")
        value = "linked/new-feature"
        if kind == "link_parent":
            value = "linked/../outside/new-feature"
    elif kind == "relative":
        value = "../outside/new-feature"
    else:
        value = (
            _bash_posix_path(outside / "new-feature")
            if port == "bash" else str(outside / "new-feature")
        )
    write_feature_json(repo, value)
    before = (repo / ".specify" / "feature.json").read_bytes()

    result = run(_command(repo, port, True), repo)

    if kind == "link_parent" and os.name == "nt" and port == "python":
        # Windows normalizes parent components before resolving directory links.
        assert result.returncode == 0, result.stderr
        contained = repo / "outside" / "new-feature"
        assert Path(json_stdout(result)["FEATURE_DIR"]) == contained
        assert (contained / "plan.md").read_text(encoding="utf-8") == TEMPLATE_BODY
    else:
        assert result.returncode != 0
        assert result.stdout == ""
        assert "outside the project" in result.stderr
    assert not (outside / "new-feature").exists()
    assert (repo / ".specify" / "feature.json").read_bytes() == before


@pytest.mark.parametrize("port", POWERSHELL_PORTS)
@pytest.mark.parametrize("absolute", [False, True])
@pytest.mark.parametrize("escape", [False, True], ids=["contained", "outside"])
def test_powershell_mixed_separators_are_resolved_before_containment(
    repo: Path, port: str, absolute: bool, escape: bool
) -> None:
    value = r"..\outside/new-feature" if escape else r"specs\new-feature"
    if absolute:
        value = str(repo) + "/" + value
    write_feature_json(repo, value)
    before = (repo / ".specify" / "feature.json").read_bytes()

    result = run(_command(repo, port, True), repo)

    if escape:
        assert result.returncode != 0
        assert result.stdout == ""
        assert "outside the project" in result.stderr
        assert not (repo.parent / "outside" / "new-feature").exists()
    else:
        feature = repo / "specs" / "new-feature"
        assert result.returncode == 0, result.stderr
        assert Path(json_stdout(result)["FEATURE_DIR"]) == feature
        assert (feature / "plan.md").read_text(encoding="utf-8") == TEMPLATE_BODY
    assert (repo / ".specify" / "feature.json").read_bytes() == before


@requires_bash
@pytest.mark.skipif(os.name == "nt", reason="POSIX filenames containing newlines")
@pytest.mark.parametrize("parser", ["default", "python"])
@pytest.mark.parametrize(
    "kind", ["link-target", "parent-component", "terminal-link", "stored-path", "outside-link"]
)
def test_bash_feature_paths_preserve_trailing_newlines(
    repo: Path, kind: str, parser: str
) -> None:
    directory = (repo.parent if kind == "outside-link" else repo) / "feature\n\n"
    directory.mkdir()
    expected = directory / "new-feature"
    if kind == "parent-component":
        (directory / "child").mkdir()
        value = "feature\n\n/child/../new-feature"
    elif kind == "stored-path":
        value = "feature\n\n"
        expected = directory
    else:
        target = "../feature\n\n" if kind == "outside-link" else "feature\n\n"
        (repo / "linked").symlink_to(target, target_is_directory=True)
        value = "linked/new-feature"
        if kind == "terminal-link":
            value = "linked"
            expected = directory
    write_feature_json(repo, value)
    env = clean_env()
    if parser == "python":
        bin_dir = make_python3_path_shim(repo / "bin")
        jq = bin_dir / "jq"
        jq.write_text("#!/bin/sh\nexit 1\n", encoding="utf-8")
        jq.chmod(0o755)
        env["PATH"] = str(bin_dir) + os.pathsep + env["PATH"]

    result = run(_command(repo, "bash", parser == "default"), repo, env)

    if kind == "outside-link":
        assert result.returncode != 0
        assert result.stdout == ""
        assert "outside the project" in result.stderr
        assert not (directory / "new-feature").exists()
    else:
        assert result.returncode == 0, result.stderr
        if parser == "default":
            assert Path(json_stdout(result)["FEATURE_DIR"]) == expected
        else:
            assert f"FEATURE_DIR: {expected}\n" in result.stdout
        assert (expected / "plan.md").read_text(encoding="utf-8") == TEMPLATE_BODY
        assert not (repo / "feature").exists()
        if kind == "stored-path":
            feature_json = repo / ".specify" / "feature.json"
            before = feature_json.stat().st_mtime_ns
            env["SPECIFY_FEATURE_DIRECTORY"] = value
            retry = run(_command(repo, "bash", parser == "default"), repo, env)
            assert retry.returncode == 0, retry.stderr
            assert feature_json.stat().st_mtime_ns == before


@pytest.mark.parametrize("port", POWERSHELL_PORTS)
@pytest.mark.parametrize("existing", [False, True])
def test_powershell_plan_alias_uses_filesystem_casing(
    repo: Path, port: str, existing: bool
) -> None:
    feature = repo / "specs" / "001-my-feature"
    target = repo.parent / "target.md"
    if existing:
        target.write_bytes(b"keep")
    alias = feature / "PLAN.MD"
    try:
        alias.symlink_to(target)
    except OSError as exc:
        pytest.skip(f"Cannot create file symlink: {exc}")
    plan = feature / "plan.md"
    same_entry = plan.is_symlink()

    result = run(_command(repo, port, True), repo)

    if same_entry:
        assert result.returncode != 0
        assert result.stdout == ""
        assert "symbolic link" in result.stderr
    else:
        assert result.returncode == 0, result.stderr
        assert plan.read_text(encoding="utf-8") == TEMPLATE_BODY
    assert alias.is_symlink()
    assert target.exists() == existing
    if existing:
        assert target.read_bytes() == b"keep"


@pytest.mark.parametrize("port", POWERSHELL_PORTS)
def test_powershell_preserves_cloud_backed_plan(repo: Path, port: str) -> None:
    feature = repo / "specs" / "001-my-feature"
    plan = feature / "plan.md"
    plan.write_bytes(b"existing cloud plan")
    before = plan.stat().st_mtime_ns
    env = clean_env()
    env["SPECIFY_INIT_DIR"] = str(repo)
    env["TEST_FEATURE_DIR"] = str(feature)
    env["TEST_PLAN"] = str(plan)
    program = r"""
function Get-CloudPlan {
    [PSCustomObject]@{
        Name = 'plan.md'
        Attributes = [System.IO.FileAttributes]::ReparsePoint
        PSIsContainer = $false
        LinkType = $null
        Target = $null
    }
}
function Get-Item {
    [CmdletBinding()]
    param([string]$LiteralPath, [switch]$Force)
    if ($LiteralPath -ceq $env:TEST_PLAN) { return (Get-CloudPlan) }
    Microsoft.PowerShell.Management\Get-Item @PSBoundParameters
}
function Get-ChildItem {
    [CmdletBinding()]
    param([string]$LiteralPath, [switch]$Force)
    if ($LiteralPath -ceq $env:TEST_FEATURE_DIR) { return (Get-CloudPlan) }
    Microsoft.PowerShell.Management\Get-ChildItem @PSBoundParameters
}
& (Join-Path $env:SPECIFY_INIT_DIR '.specify/scripts/powershell/setup-plan.ps1') -Json
"""

    result = run(_command(repo, port, False)[:2] + ["-Command", program], repo, env)

    assert result.returncode == 0, result.stderr
    assert "already exists" in result.stderr
    assert plan.read_bytes() == b"existing cloud plan"
    assert plan.stat().st_mtime_ns == before


@pytest.mark.parametrize("port", [pytest.param("bash", marks=requires_bash), "python"])
@pytest.mark.skipif(not hasattr(os, "mkfifo"), reason="POSIX FIFO required")
def test_plan_fifo_is_rejected_without_writing(repo: Path, port: str) -> None:
    plan = repo / "specs" / "001-my-feature" / "plan.md"
    os.mkfifo(plan)
    # Keep a reader open so the unfixed Bash writer fails the assertion, not a hang.
    with os.fdopen(os.open(plan, os.O_RDONLY | os.O_NONBLOCK), "rb", buffering=0) as reader:
        result = run(_command(repo, port, True), repo, timeout=15)
        written = reader.read()

    assert result.returncode != 0
    assert result.stdout == ""
    assert written == b""
    assert stat.S_ISFIFO(plan.stat().st_mode)
    assert list(plan.parent.iterdir()) == [plan]


@pytest.mark.parametrize("port", PORTS)
def test_plan_directory_is_rejected_without_modification(repo: Path, port: str) -> None:
    plan = repo / "specs" / "001-my-feature" / "plan.md"
    plan.mkdir()
    sentinel = plan / "keep.md"
    sentinel.write_bytes(b"keep")

    result = run(_command(repo, port, True), repo, timeout=15)

    assert result.returncode != 0
    assert result.stdout == ""
    assert list(plan.iterdir()) == [sentinel]
    assert sentinel.read_bytes() == b"keep"
    assert list(plan.parent.iterdir()) == [plan]


@requires_bash
def test_bash_plan_publication_failure_is_reported(repo: Path) -> None:
    bin_dir = repo / "bin"
    bin_dir.mkdir()
    link = bin_dir / "link"
    link.write_text("#!/bin/sh\necho 'Hard links unavailable' >&2\nexit 1\n", encoding="utf-8")
    link.chmod(0o755)
    env = clean_env()
    env["PATH"] = str(bin_dir) + os.pathsep + env["PATH"]

    result = run(bash_cmd(repo, SCRIPT, "--json"), repo, env)

    assert result.returncode != 0
    assert result.stdout == ""
    assert "Cannot create plan" in result.stderr
    assert "Hard links unavailable" in result.stderr
    assert list((repo / "specs" / "001-my-feature").iterdir()) == []


@pytest.mark.parametrize("port", POWERSHELL_PORTS)
@pytest.mark.parametrize("count", [40, 41])
def test_powershell_link_traversal_limit(repo: Path, port: str, count: int) -> None:
    try:
        (repo / "link").symlink_to(".", target_is_directory=True)
    except OSError as exc:
        pytest.skip(f"Cannot create directory symlink: {exc}")
    write_feature_json(repo, "link/" * count + "new-feature")

    result = run(_command(repo, port, True), repo, timeout=15)

    if count == 40:
        assert result.returncode == 0, result.stderr
        assert (repo / "new-feature" / "plan.md").read_text(encoding="utf-8") == TEMPLATE_BODY
    else:
        assert result.returncode != 0
        assert result.stdout == ""
        assert "outside the project" in result.stderr
        assert not (repo / "new-feature").exists()


@pytest.mark.parametrize("port", POWERSHELL_PORTS)
@pytest.mark.parametrize("depth", [4, 5], ids=["within-budget", "over-budget"])
def test_powershell_counts_all_link_traversals(
    repo: Path, port: str, depth: int
) -> None:
    try:
        (repo / "l0").symlink_to(".", target_is_directory=True)
        for index in range(1, depth + 1):
            previous = f"l{index - 1}"
            (repo / f"l{index}").symlink_to(
                f"{previous}/{previous}", target_is_directory=True
            )
    except OSError as exc:
        pytest.skip(f"Cannot create directory symlink: {exc}")
    write_feature_json(repo, f"l{depth}/new-feature")

    result = run(_command(repo, port, True), repo, timeout=15)

    if depth == 4:
        assert result.returncode == 0, result.stderr
        assert (repo / "new-feature" / "plan.md").read_text(encoding="utf-8") == TEMPLATE_BODY
    else:
        assert result.returncode != 0
        assert result.stdout == ""
        assert "outside the project" in result.stderr
        assert not (repo / "new-feature").exists()


@pytest.mark.parametrize("port", POWERSHELL_PORTS)
@pytest.mark.parametrize(
    ("link_type", "target"),
    [
        ("", ""),
        ("SymbolicLink", ""),
        ("Junction", ""),
        ("SymbolicLink", "outside"),
        ("Junction", "outside"),
    ],
    ids=["cloud-placeholder", "unresolved-symlink", "unresolved-junction",
         "external-symlink", "external-junction"],
)
def test_powershell_reparse_directory_types(
    repo: Path, port: str, link_type: str, target: str
) -> None:
    feature = repo / "placeholder" / "new-feature"
    feature.parent.mkdir()
    write_feature_json(repo, "placeholder/new-feature")
    env = clean_env()
    env["SPECIFY_INIT_DIR"] = str(repo)
    env["TEST_REPARSE_ENTRY"] = str(feature.parent)
    env["TEST_LINK_TYPE"] = link_type
    env["TEST_LINK_TARGET"] = str(repo.parent / target) if target else ""
    program = r"""
function Get-Item {
    [CmdletBinding()]
    param([string]$LiteralPath, [switch]$Force)
    if ($LiteralPath -ceq $env:TEST_REPARSE_ENTRY) {
        return [PSCustomObject]@{
            Name = 'placeholder'
            Attributes = [System.IO.FileAttributes]::Directory -bor
                [System.IO.FileAttributes]::ReparsePoint
            PSIsContainer = $true
            LinkType = $env:TEST_LINK_TYPE
            Target = $env:TEST_LINK_TARGET
        }
    }
    Microsoft.PowerShell.Management\Get-Item @PSBoundParameters
}
& (Join-Path $env:SPECIFY_INIT_DIR '.specify/scripts/powershell/setup-plan.ps1') -Json
"""

    result = run(_command(repo, port, False)[:2] + ["-Command", program], repo, env)

    if not link_type:
        assert result.returncode == 0, result.stderr
        assert (feature / "plan.md").read_text(encoding="utf-8") == TEMPLATE_BODY
    else:
        assert result.returncode != 0
        assert result.stdout == ""
        assert "outside the project" in result.stderr
        assert not feature.exists()


@pytest.mark.parametrize("port", POWERSHELL_PORTS)
@pytest.mark.skipif(os.name == "nt", reason="Non-Windows case-sensitive name matching")
def test_powershell_missing_directory_does_not_match_case_sibling(
    repo: Path, port: str
) -> None:
    env = clean_env()
    env["SPECIFY_INIT_DIR"] = str(repo)
    env["TEST_MISSING_DIR"] = str(repo / "features")
    env["TEST_OUTSIDE"] = str(repo.parent / "outside")
    program = r"""
. (Join-Path $env:SPECIFY_INIT_DIR '.specify/scripts/powershell/common.ps1')
function Test-Path {
    [CmdletBinding()]
    param([string]$LiteralPath, [string]$PathType)
    if ($LiteralPath -ceq $env:TEST_MISSING_DIR) { return $false }
    Microsoft.PowerShell.Management\Test-Path @PSBoundParameters
}
function Get-ChildItem {
    [CmdletBinding()]
    param([string]$LiteralPath, [switch]$Force)
    Microsoft.PowerShell.Management\Get-ChildItem @PSBoundParameters
    if ($LiteralPath -ceq $env:SPECIFY_INIT_DIR) {
        [PSCustomObject]@{
            Name = 'Features'
            Attributes = [System.IO.FileAttributes]::Directory -bor
                [System.IO.FileAttributes]::ReparsePoint
            PSIsContainer = $true
            LinkType = 'SymbolicLink'
            Target = $env:TEST_OUTSIDE
        }
    }
}
Resolve-FeatureDirectoryPath -Path (Join-Path $env:TEST_MISSING_DIR 'new-feature')
"""

    result = run(_command(repo, port, False)[:2] + ["-Command", program], repo, env)

    assert result.returncode == 0, result.stderr
    assert Path(result.stdout.strip()) == repo / "features" / "new-feature"


@pytest.mark.parametrize("port", POWERSHELL_PORTS)
@pytest.mark.skipif(os.name == "nt", reason="Non-Windows case-sensitive name matching")
def test_powershell_plan_does_not_match_case_sibling(repo: Path, port: str) -> None:
    feature = repo / "specs" / "001-my-feature"
    env = clean_env()
    env["SPECIFY_INIT_DIR"] = str(repo)
    env["TEST_FEATURE_DIR"] = str(feature)
    program = r"""
function Get-ChildItem {
    [CmdletBinding()]
    param([string]$LiteralPath, [switch]$Force)
    Microsoft.PowerShell.Management\Get-ChildItem @PSBoundParameters
    if ($LiteralPath -ceq $env:TEST_FEATURE_DIR) {
        [PSCustomObject]@{
            Name = 'PLAN.MD'
            Attributes = [System.IO.FileAttributes]::ReparsePoint
            LinkType = 'SymbolicLink'
            Target = 'unrelated'
        }
    }
}
& (Join-Path $env:SPECIFY_INIT_DIR '.specify/scripts/powershell/setup-plan.ps1') -Json
"""

    result = run(_command(repo, port, False)[:2] + ["-Command", program], repo, env)

    assert result.returncode == 0, result.stderr
    assert (feature / "plan.md").read_text(encoding="utf-8") == TEMPLATE_BODY


@pytest.mark.parametrize("port", PORTS)
def test_stored_feature_link_loop_is_rejected(repo: Path, port: str) -> None:
    try:
        (repo / "loop").symlink_to("loop", target_is_directory=True)
    except OSError as exc:
        pytest.skip(f"Cannot create directory symlink: {exc}")
    write_feature_json(repo, "loop/new-feature")

    result = run(_command(repo, port, True), repo, timeout=15)

    assert result.returncode != 0
    assert result.stdout == ""
    assert "outside the project" in result.stderr


def test_python_strict_path_resolution_failure_is_reported(
    repo: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    feature = repo / "specs" / "001-my-feature"
    original_resolve = Path.resolve

    def resolve(path: Path, strict: bool = False) -> Path:
        if path == feature:
            if strict:
                raise OSError(1921, "The name cannot be resolved by the system")
            return path
        return original_resolve(path, strict=strict)

    monkeypatch.setenv("SPECIFY_INIT_DIR", str(repo))
    monkeypatch.delenv("SPECIFY_FEATURE_DIRECTORY", raising=False)
    monkeypatch.setattr(Path, "resolve", resolve)

    with pytest.raises(SystemExit, match="1"):
        python_common.get_feature_paths()

    assert "outside the project" in capsys.readouterr().err


@pytest.mark.parametrize("port", PORTS)
@pytest.mark.parametrize("absolute", [False, True])
def test_external_feature_requires_override_on_every_invocation(
    repo: Path, port: str, absolute: bool
) -> None:
    outside = repo.parent / "outside" / "new-feature"
    env = clean_env()
    absolute_value = _bash_posix_path(outside) if port == "bash" else str(outside)
    env["SPECIFY_FEATURE_DIRECTORY"] = absolute_value if absolute else "../outside/new-feature"

    result = run(_command(repo, port, True), repo, env)

    assert result.returncode == 0, result.stderr
    assert (outside / "plan.md").read_text(encoding="utf-8") == TEMPLATE_BODY
    retry = run(_command(repo, port, True), repo)
    assert retry.returncode != 0
    assert "outside the project" in retry.stderr


@pytest.mark.parametrize("port", PORTS)
@pytest.mark.parametrize("existing", [False, True])
@pytest.mark.parametrize("override", [False, True])
def test_plan_symlink_is_rejected(
    repo: Path, port: str, existing: bool, override: bool
) -> None:
    target = repo.parent / "target.md"
    if existing:
        target.write_bytes(b"preserve me")
    plan = repo / "specs" / "001-my-feature" / "plan.md"
    try:
        plan.symlink_to(target)
    except OSError as exc:
        pytest.skip(f"Cannot create file symlink: {exc}")
    env = clean_env()
    if override:
        env["SPECIFY_FEATURE_DIRECTORY"] = (
            _bash_posix_path(plan.parent) if port == "bash" else str(plan.parent)
        )

    result = run(_command(repo, port, True), repo, env)

    assert result.returncode != 0
    assert result.stdout == ""
    assert "symbolic link" in result.stderr
    assert plan.is_symlink()
    assert target.exists() == existing
    if existing:
        assert target.read_bytes() == b"preserve me"


@pytest.mark.parametrize("port", PORTS)
@pytest.mark.parametrize("kind", ["relative", "absolute", "normalized", "internal_link"])
def test_contained_stored_feature_is_supported(repo: Path, port: str, kind: str) -> None:
    feature = repo / "specs" / "new-feature"
    value = "specs/new-feature"
    if kind == "absolute":
        value = _bash_posix_path(feature) if port == "bash" else str(feature)
    elif kind == "normalized":
        value = "specs/unused/../new-feature"
    elif kind == "internal_link":
        try:
            (repo / "linked").symlink_to(repo / "specs", target_is_directory=True)
        except OSError as exc:
            pytest.skip(f"Cannot create directory symlink: {exc}")
        value = "linked/new-feature"
    write_feature_json(repo, value)

    result = run(_command(repo, port, True), repo)

    assert result.returncode == 0, result.stderr
    assert (feature / "plan.md").read_text(encoding="utf-8") == TEMPLATE_BODY
    assert not (repo / "specs" / "unused").exists()


def test_python_json_preserves_non_ascii_feature_on_legacy_stdout(repo: Path) -> None:
    feature = repo / "specs/001-功能"
    feature.mkdir()
    write_feature_json(repo, "specs/001-功能")
    env = clean_env()
    env["PYTHONIOENCODING"] = "cp1252"

    result = run(py_cmd(repo, SCRIPT, "--json"), repo, env)

    assert result.returncode == 0, result.stderr
    payload = json_stdout(result)
    assert payload["BRANCH"] == "001-功能"
    assert Path(payload["FEATURE_DIR"]) == feature
    assert Path(payload["FEATURE_SPEC"]) == feature / "spec.md"
    assert Path(payload["IMPL_PLAN"]) == feature / "plan.md"
    template = repo / ".specify" / "templates" / "plan-template.md"
    assert (feature / "plan.md").read_bytes() == template.read_bytes()


@pytest.mark.parametrize("port", PORTS)
@pytest.mark.parametrize("json_mode", [True, False], ids=["json", "text"])
@pytest.mark.parametrize("template_state", ["missing", "empty", "empty_override"])
def test_plan_template_failure_and_retry(
    tmp_path: Path, port: str, json_mode: bool, template_state: str
) -> None:
    repo = _setup_repo(tmp_path, template=False)
    template = repo / ".specify" / "templates" / "plan-template.md"
    if template_state != "missing":
        template.parent.mkdir(parents=True)
        template.write_bytes(b"")
        if template_state == "empty_override":
            template.write_bytes(TEMPLATE_BODY.encode("utf-8"))
            template = template.parent / "overrides" / template.name
            template.parent.mkdir()
            template.write_bytes(b"")
    plan = repo / "specs" / "001-my-feature" / "plan.md"

    result = run(_command(repo, port, json_mode), repo)

    diagnostic = "not found" if template_state == "missing" else "is empty"
    assert result.returncode == 1
    assert result.stdout == ""
    assert result.stderr == (
        f"ERROR: Plan template {diagnostic}; no new plan.md was created.\n"
        "Restore a valid plan template and rerun plan setup.\n"
    )
    assert not plan.exists()

    template.parent.mkdir(parents=True, exist_ok=True)
    template.write_bytes(TEMPLATE_BODY.encode("utf-8"))
    retry = run(_command(repo, port, json_mode), repo)

    assert retry.returncode == 0, retry.stderr
    assert plan.read_bytes() == TEMPLATE_BODY.encode("utf-8")
    if json_mode:
        assert sorted(json_stdout(retry)) == [
            "BRANCH", "FEATURE_DIR", "FEATURE_SPEC", "IMPL_PLAN"
        ]
    else:
        assert "IMPL_PLAN: " in retry.stdout


@pytest.mark.parametrize("port", PORTS)
@pytest.mark.parametrize("json_mode", [True, False], ids=["json", "text"])
@pytest.mark.parametrize("template_state", ["missing", "empty", "valid"])
@pytest.mark.parametrize("body", [b"", b"# Existing plan\n"], ids=["empty", "nonempty"])
def test_existing_plan_is_preserved(
    tmp_path: Path, port: str, json_mode: bool, template_state: str, body: bytes
) -> None:
    repo = _setup_repo(tmp_path, template=False)
    if template_state != "missing":
        template = repo / ".specify" / "templates" / "plan-template.md"
        template.parent.mkdir(parents=True)
        template.write_bytes(b"" if template_state == "empty" else TEMPLATE_BODY.encode())
    plan = repo / "specs" / "001-my-feature" / "plan.md"
    plan.write_bytes(body)
    before = plan.stat().st_mtime_ns

    result = run(_command(repo, port, json_mode), repo)

    assert result.returncode == 0, result.stderr
    assert plan.read_bytes() == body
    assert plan.stat().st_mtime_ns == before
    status = result.stderr if json_mode else result.stdout
    assert "already exists" in status
    assert "skipping template copy" in status
    if json_mode:
        assert "IMPL_PLAN" in json_stdout(result)


@pytest.mark.parametrize("port", PORTS)
@pytest.mark.parametrize("json_mode", [True, False], ids=["json", "text"])
def test_whitespace_plan_template_is_not_empty(
    repo: Path, port: str, json_mode: bool
) -> None:
    body = b" \t\n\n"
    (repo / ".specify" / "templates" / "plan-template.md").write_bytes(body)

    result = run(_command(repo, port, json_mode), repo)

    assert result.returncode == 0, result.stderr
    assert (repo / "specs" / "001-my-feature" / "plan.md").read_bytes() == body


@requires_bash
def test_python_fresh_copy_matches_bash(tmp_path: Path) -> None:
    repo_a = _setup_repo(tmp_path, "proj-a")
    repo_b = _setup_repo(tmp_path, "proj-b")

    bash = run(bash_cmd(repo_a, SCRIPT, "--json"), repo_a)
    py = run(py_cmd(repo_b, SCRIPT, "--json"), repo_b)

    assert py.returncode == bash.returncode == 0
    assert normalize_repo_paths(py.stdout, repo_b) == normalize_repo_paths(
        bash.stdout, repo_a
    )
    assert normalize_repo_paths(py.stderr, repo_b) == normalize_repo_paths(
        bash.stderr, repo_a
    )
    for repo in (repo_a, repo_b):
        plan = repo / "specs" / "001-my-feature" / "plan.md"
        assert plan.read_bytes() == TEMPLATE_BODY.encode("utf-8")


@requires_bash
def test_all_variants_materialize_composed_plan_template(tmp_path: Path) -> None:
    repos = [
        _setup_repo(tmp_path, "bash"),
        _setup_repo(tmp_path, "powershell"),
        _setup_repo(tmp_path, "python"),
    ]
    expected = ""
    for current in repos:
        expected = install_composition_stack(
            current, "plan-template", TEMPLATE_BODY
        )

    results = [
        run(bash_cmd(repos[0], SCRIPT, "--json"), repos[0]),
        run(py_cmd(repos[2], SCRIPT, "--json"), repos[2]),
    ]
    checked_repos = [repos[0], repos[2]]
    if HAS_POWERSHELL:
        results.insert(1, run(ps_cmd(repos[1], SCRIPT, "-Json"), repos[1]))
        checked_repos.insert(1, repos[1])

    assert all(result.returncode == 0 for result in results)
    for current in checked_repos:
        assert (
            current / "specs" / "001-my-feature" / "plan.md"
        ).read_text(encoding="utf-8") == expected


@requires_bash
def test_all_variants_fail_for_broken_plan_composition(tmp_path: Path) -> None:
    repos = [
        _setup_repo(tmp_path, "bash"),
        _setup_repo(tmp_path, "powershell"),
        _setup_repo(tmp_path, "python"),
    ]
    for current in repos:
        install_composition_stack(current, "plan-template", TEMPLATE_BODY)
        break_wrap_layer(current, "plan-template")

    results = [
        run(bash_cmd(repos[0], SCRIPT, "--json"), repos[0]),
        run(py_cmd(repos[2], SCRIPT, "--json"), repos[2]),
    ]
    if HAS_POWERSHELL:
        results.append(run(ps_cmd(repos[1], SCRIPT, "-Json"), repos[1]))

    assert all(result.returncode != 0 for result in results)


@requires_bash
@pytest.mark.parametrize("args", [("--json",), ()], ids=["json", "text"])
def test_python_existing_plan_matches_bash(repo: Path, args: tuple[str, ...]) -> None:
    plan = repo / "specs" / "001-my-feature" / "plan.md"
    plan.write_text("# existing\n", encoding="utf-8")

    bash = run(bash_cmd(repo, SCRIPT, *args), repo)
    py = run(py_cmd(repo, SCRIPT, *args), repo)

    assert py.returncode == bash.returncode == 0
    assert py.stdout == bash.stdout
    assert py.stderr == bash.stderr
    assert plan.read_text(encoding="utf-8") == "# existing\n"


@requires_bash
@pytest.mark.skipif(not HAS_POWERSHELL, reason="no PowerShell available")
def test_all_variants_reject_unknown_options(tmp_path: Path) -> None:
    repos = [
        _setup_repo(tmp_path, "bash"),
        _setup_repo(tmp_path, "powershell"),
        _setup_repo(tmp_path, "python"),
    ]

    bash = run(bash_cmd(repos[0], SCRIPT, "--json", "--bogus"), repos[0])
    ps = run(ps_cmd(repos[1], SCRIPT, "-Json", "--bogus"), repos[1])
    py = run(py_cmd(repos[2], SCRIPT, "--json", "--bogus"), repos[2])

    assert bash.returncode == ps.returncode == py.returncode == 1
    assert bash.stdout == ps.stdout == py.stdout == ""
    assert bash.stderr == ps.stderr == py.stderr == (
        "ERROR: Unknown option '--bogus'\n"
    )
    assert all(
        not (current / "specs" / "001-my-feature" / "plan.md").exists()
        for current in repos
    )


@requires_bash
def test_python_missing_template_matches_bash(tmp_path: Path) -> None:
    repo_a = _setup_repo(tmp_path, "proj-a", template=False)
    repo_b = _setup_repo(tmp_path, "proj-b", template=False)

    bash = run(bash_cmd(repo_a, SCRIPT, "--json"), repo_a)
    py = run(py_cmd(repo_b, SCRIPT, "--json"), repo_b)

    assert py.returncode == bash.returncode == 1
    assert py.stdout == bash.stdout == ""
    assert normalize_repo_paths(py.stderr, repo_b) == normalize_repo_paths(
        bash.stderr, repo_a
    )
    for repo in (repo_a, repo_b):
        plan = repo / "specs" / "001-my-feature" / "plan.md"
        assert not plan.exists()

    for repo in (repo_a, repo_b):
        templates = repo / ".specify" / "templates"
        templates.mkdir(parents=True)
        (templates / "plan-template.md").write_text(TEMPLATE_BODY, encoding="utf-8")

    bash_retry = run(bash_cmd(repo_a, SCRIPT, "--json"), repo_a)
    py_retry = run(py_cmd(repo_b, SCRIPT, "--json"), repo_b)
    assert py_retry.returncode == bash_retry.returncode == 0
    for repo in (repo_a, repo_b):
        assert (
            repo / "specs" / "001-my-feature" / "plan.md"
        ).read_text(encoding="utf-8") == TEMPLATE_BODY


@requires_bash
@pytest.mark.parametrize(
    ("registry", "expected"),
    [
        (
            '{"presets": {"alpha": {"priority": "high"}, "beta": {"priority": 1}}}',
            "# beta plan\n",
        ),
        (
            '{"presets": {"alpha": {"priority": 2}, "beta": {"priority": 1}, "gamma": {"priority": null}}}',
            "# beta plan\n",
        ),
        ("[]", "# alpha plan\n"),
        ('{"presets":[]}', "# alpha plan\n"),
        ('{"presets":null}', "# alpha plan\n"),
    ],
    ids=[
        "mixed_priorities",
        "null_priority",
        "list_root",
        "list_presets",
        "null_presets",
    ],
)
def test_all_variants_normalize_or_fallback_for_registry(
    tmp_path: Path, registry: str, expected: str
) -> None:
    """Priorities normalize canonically; malformed shapes fall back to directories."""
    repos = [
        _setup_repo(tmp_path, "bash", template=False),
        _setup_repo(tmp_path, "powershell", template=False),
        _setup_repo(tmp_path, "python", template=False),
    ]
    for repo in repos:
        presets = repo / ".specify" / "presets"
        for name, body in (
            (".hidden", "# hidden\n"),
            ("beta", "# beta plan\n"),
            ("alpha", "# alpha plan\n"),
        ):
            (presets / name / "templates").mkdir(parents=True)
            (presets / name / "templates" / "plan-template.md").write_text(
                body, encoding="utf-8"
            )
        (presets / ".registry").write_text(
            registry, encoding="utf-8"
        )

    bash = run(bash_cmd(repos[0], SCRIPT, "--json"), repos[0])
    py = run(py_cmd(repos[2], SCRIPT, "--json"), repos[2])
    results = [(bash, repos[0]), (py, repos[2])]
    if HAS_POWERSHELL:
        results.insert(
            1,
            (run(ps_cmd(repos[1], SCRIPT, "-Json"), repos[1]), repos[1]),
        )

    assert all(result.returncode == 0 for result, _ in results)
    assert len(
        {
            normalize_repo_paths(result.stdout, repo)
            for result, repo in results
        }
    ) == 1
    assert len(
        {
            normalize_repo_paths(result.stderr, repo)
            for result, repo in results
        }
    ) == 1
    for _, repo in results:
        plan = repo / "specs" / "001-my-feature" / "plan.md"
        assert plan.read_text(encoding="utf-8") == expected


@pytest.mark.skipif(not HAS_POWERSHELL, reason="no PowerShell available")
def test_powershell_broken_registry_fallback_sorts_directories(
    tmp_path: Path,
) -> None:
    repo = _setup_repo(tmp_path, "powershell", template=False)
    presets = repo / ".specify" / "presets"
    for name in ("alpha", "beta"):
        templates = presets / name / "templates"
        templates.mkdir(parents=True)
        (templates / "plan-template.md").write_text(
            f"# {name} plan\n", encoding="utf-8"
        )
    (presets / ".registry").write_text("{broken", encoding="utf-8")

    common = repo / ".specify" / "scripts" / "powershell" / "common.ps1"
    common_ps = str(common).replace("'", "''")
    alpha_ps = str(presets / "alpha").replace("'", "''")
    beta_ps = str(presets / "beta").replace("'", "''")
    repo_ps = str(repo).replace("'", "''")
    command = f"""
. '{common_ps}'
function Get-ChildItem {{
    @(
        [PSCustomObject]@{{ Name = 'beta'; FullName = '{beta_ps}' }}
        [PSCustomObject]@{{ Name = 'alpha'; FullName = '{alpha_ps}' }}
    )
}}
Resolve-Template -TemplateName 'plan-template' -RepoRoot '{repo_ps}'
"""
    result = run(
        [POWERSHELL_EXE, "-NoProfile", "-Command", command],
        repo,
    )

    assert result.returncode == 0
    assert result.stderr == ""
    assert Path(result.stdout.strip()).read_text(encoding="utf-8") == (
        "# alpha plan\n"
    )


@requires_bash
@pytest.mark.skipif(not HAS_POWERSHELL, reason="no PowerShell available")
@pytest.mark.parametrize(
    "context", ["missing", "invalid_json", "invalid_utf8", "invalid_init_dir"]
)
def test_all_variants_feature_context_error_matches(
    tmp_path: Path, context: str
) -> None:
    repo = make_repo(tmp_path)
    install_scripts(repo, SCRIPT)
    env = None
    if context == "invalid_json":
        (repo / ".specify" / "feature.json").write_text(
            "{not json", encoding="utf-8"
        )
    elif context == "invalid_utf8":
        (repo / ".specify" / "feature.json").write_bytes(b"\xff")
    elif context == "invalid_init_dir":
        env = clean_env()
        env["SPECIFY_INIT_DIR"] = str(tmp_path / "missing")

    bash = run(bash_cmd(repo, SCRIPT, "--json"), repo, env)
    ps = run(ps_cmd(repo, SCRIPT, "-Json"), repo, env)
    py = run(py_cmd(repo, SCRIPT, "--json"), repo, env)

    assert bash.returncode == ps.returncode == py.returncode == 1
    assert bash.stdout == ps.stdout == py.stdout == ""
    assert bash.stderr == ps.stderr == py.stderr


@requires_bash
@pytest.mark.skipif(not HAS_POWERSHELL, reason="no PowerShell available")
@pytest.mark.parametrize(
    "registry",
    [
        '{"presets":{"alpha":{"enabled":false,"priority":1}}}',
        '{"presets":{"alpha":"invalid"}}',
    ],
    ids=["disabled", "invalid_metadata"],
)
def test_all_variants_ignore_inactive_preset_template(
    tmp_path: Path, registry: str
) -> None:
    repos = [
        _setup_repo(tmp_path, "bash"),
        _setup_repo(tmp_path, "powershell"),
        _setup_repo(tmp_path, "python"),
    ]
    for current in repos:
        preset_templates = (
            current / ".specify" / "presets" / "alpha" / "templates"
        )
        preset_templates.mkdir(parents=True)
        (preset_templates / "plan-template.md").write_text(
            "# Disabled preset\n", encoding="utf-8"
        )
        (current / ".specify" / "presets" / ".registry").write_text(
            registry, encoding="utf-8"
        )

    bash = run(bash_cmd(repos[0], SCRIPT, "--json"), repos[0])
    ps = run(ps_cmd(repos[1], SCRIPT, "-Json"), repos[1])
    py = run(py_cmd(repos[2], SCRIPT, "--json"), repos[2])

    assert bash.returncode == ps.returncode == py.returncode == 0
    assert normalize_repo_paths(bash.stdout, repos[0]) == normalize_repo_paths(
        ps.stdout, repos[1]
    ) == normalize_repo_paths(py.stdout, repos[2])
    assert normalize_repo_paths(bash.stderr, repos[0]) == normalize_repo_paths(
        ps.stderr, repos[1]
    ) == normalize_repo_paths(py.stderr, repos[2])
    for current in repos:
        assert (
            current / "specs" / "001-my-feature" / "plan.md"
        ).read_text(encoding="utf-8") == TEMPLATE_BODY


@pytest.mark.skipif(not HAS_POWERSHELL, reason="no PowerShell available")
def test_python_json_output_matches_powershell(repo: Path) -> None:
    plan = repo / "specs" / "001-my-feature" / "plan.md"
    plan.write_text("# existing\n", encoding="utf-8")

    ps = run(ps_cmd(repo, SCRIPT, "-Json"), repo)
    py = run(py_cmd(repo, SCRIPT, "--json"), repo)

    assert py.returncode == ps.returncode == 0
    assert json_stdout(py) == json_stdout(ps)


@requires_bash
@pytest.mark.parametrize("args", [("--json",), ()], ids=["json", "text"])
def test_all_variants_emit_feature_dir_not_specs_dir(
    repo: Path, args: tuple[str, ...]
) -> None:
    r"""Pin the output key name, not just cross-port agreement.

    The other tests here compare the ports against each other, so all three
    could regress to ``SPECS_DIR`` together and still pass. This asserts the
    contract absolutely: the key is ``FEATURE_DIR``, it carries the feature
    directory rather than the specs root, and the old name is gone.
    ``SPECS_DIR`` means the specs root in ``create-new-feature.sh``, so
    re-emitting it here would reintroduce one name for two paths.

    The value is matched by suffix because the ports legitimately differ in
    path flavour -- under MSYS bash reports ``/tmp/...`` where the Python and
    PowerShell ports report ``C:\...``. The suffix still separates
    ``specs/001-my-feature`` from a bare ``specs``, which is the regression
    this guards.
    """
    json_mode = args == ("--json",)
    suffix = ("specs", "001-my-feature")

    commands = [bash_cmd(repo, SCRIPT, *args), py_cmd(repo, SCRIPT, *args)]
    if HAS_POWERSHELL:
        commands.append(ps_cmd(repo, SCRIPT, *(("-Json",) if json_mode else ())))

    for cmd in commands:
        result = run(cmd, repo)
        assert result.returncode == 0, result.stderr
        assert "SPECS_DIR" not in result.stdout

        if json_mode:
            payload = json_stdout(result)
            assert isinstance(payload, dict)
            assert sorted(payload) == [
                "BRANCH",
                "FEATURE_DIR",
                "FEATURE_SPEC",
                "IMPL_PLAN",
            ]
            value = payload["FEATURE_DIR"]
        else:
            lines = dict(
                line.split(": ", 1)
                for line in result.stdout.splitlines()
                if ": " in line
            )
            assert "FEATURE_DIR" in lines
            value = lines["FEATURE_DIR"]

        assert tuple(value.replace("\\", "/").rstrip("/").split("/")[-2:]) == suffix
