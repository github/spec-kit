"""Parity tests: update_agent_context.py vs update-agent-context.sh/.ps1.

Each test prepares two identical project trees, runs the bash script in one
and the Python port in the other, then compares exit codes, output (with
project roots normalized) and the resulting context-file bytes. PowerShell
tests compare the resulting file content only and are skipped when ``pwsh``
is unavailable.
"""

from __future__ import annotations

import errno
import io
import json
import os
import re
import runpy
import shutil
import subprocess
import sys
import time
from contextlib import redirect_stdout
from pathlib import Path

import pytest

from tests.conftest import requires_bash
from tests.extensions.test_extension_agent_context import (
    BASH,
    EXT_DIR,
    POWERSHELL,
    _bash_posix_path,
    _bundled_script_env,
)

PY_SCRIPT = EXT_DIR / "scripts" / "python" / "update_agent_context.py"
BASH_SCRIPT = EXT_DIR / "scripts" / "bash" / "update-agent-context.sh"
PS_SCRIPT = EXT_DIR / "scripts" / "powershell" / "update-agent-context.ps1"

requires_posix_bash = pytest.mark.skipif(
    not BASH or os.name == "nt",
    reason="POSIX bash required for side-by-side parity runs",
)


def run_bash(project_root: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [BASH, _bash_posix_path(BASH_SCRIPT), *args],
        cwd=project_root,
        env=_bundled_script_env(project_root, for_bash=True),
        capture_output=True,
        text=True,
        timeout=30,
    )


def run_python(project_root: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(PY_SCRIPT), *args],
        cwd=project_root,
        env=_bundled_script_env(project_root),
        capture_output=True,
        text=True,
        timeout=30,
    )


def run_powershell(project_root: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [
            POWERSHELL,
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(PS_SCRIPT),
            *args,
        ],
        cwd=project_root,
        env=_bundled_script_env(project_root),
        capture_output=True,
        text=True,
        timeout=30,
    )


def normalize(text: str, project_root: Path) -> str:
    return text.replace(str(project_root.resolve()), "__ROOT__").replace(
        str(project_root), "__ROOT__"
    )


def write_config(project_root: Path, **overrides: object) -> None:
    """Write the extension config as JSON (valid YAML, PS-parseable too)."""
    cfg: dict = {
        "context_file": overrides.get("context_file", ""),
        "context_files": overrides.get("context_files", []),
        "context_markers": overrides.get(
            "context_markers",
            {"start": "<!-- SPECKIT START -->", "end": "<!-- SPECKIT END -->"},
        ),
    }
    cfg_dir = project_root / ".specify" / "extensions" / "agent-context"
    cfg_dir.mkdir(parents=True, exist_ok=True)
    (cfg_dir / "agent-context-config.yml").write_text(
        json.dumps(cfg), encoding="utf-8"
    )


def make_project(root: Path, **config: object) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    write_config(root, **config)
    return root


def add_plan(project_root: Path, feature_dir: str = "specs/001-demo") -> None:
    plan = project_root / feature_dir / "plan.md"
    plan.parent.mkdir(parents=True, exist_ok=True)
    plan.write_text("# plan\n", encoding="utf-8")
    (project_root / ".specify").mkdir(parents=True, exist_ok=True)
    (project_root / ".specify" / "feature.json").write_text(
        json.dumps({"feature_directory": feature_dir}), encoding="utf-8"
    )


def twin_projects(tmp_path: Path, **config: object) -> tuple[Path, Path]:
    return (
        make_project(tmp_path / "proj-a", **config),
        make_project(tmp_path / "proj-b", **config),
    )


def assert_parity(
    bash: subprocess.CompletedProcess,
    py: subprocess.CompletedProcess,
    repo_a: Path,
    repo_b: Path,
) -> None:
    assert py.returncode == bash.returncode, py.stderr + bash.stderr
    assert normalize(py.stdout, repo_b) == normalize(bash.stdout, repo_a)
    assert normalize(py.stderr, repo_b) == normalize(bash.stderr, repo_a)


# ── Fresh file and upsert behavior ───────────────────────────────────────────


@requires_posix_bash
def test_python_creates_fresh_context_file_matching_bash(tmp_path: Path) -> None:
    repo_a, repo_b = twin_projects(tmp_path, context_file="AGENTS.md")
    add_plan(repo_a)
    add_plan(repo_b)

    bash = run_bash(repo_a)
    py = run_python(repo_b)

    assert_parity(bash, py, repo_a, repo_b)
    content_a = (repo_a / "AGENTS.md").read_bytes()
    content_b = (repo_b / "AGENTS.md").read_bytes()
    assert content_a == content_b
    assert b"at specs/001-demo/plan.md" in content_b


@requires_posix_bash
def test_python_replaces_existing_section_matching_bash(tmp_path: Path) -> None:
    repo_a, repo_b = twin_projects(tmp_path, context_file="AGENTS.md")
    existing = (
        "# My project\n\n"
        "<!-- SPECKIT START -->\nstale section\n<!-- SPECKIT END -->\n"
        "\nTrailing prose stays.\n"
    )
    for repo in (repo_a, repo_b):
        add_plan(repo)
        (repo / "AGENTS.md").write_text(existing, encoding="utf-8")

    bash = run_bash(repo_a)
    py = run_python(repo_b)

    assert_parity(bash, py, repo_a, repo_b)
    content = (repo_b / "AGENTS.md").read_text(encoding="utf-8")
    assert content == (repo_a / "AGENTS.md").read_text(encoding="utf-8")
    assert "stale section" not in content
    assert content.startswith("# My project\n")
    assert "Trailing prose stays." in content


@requires_posix_bash
@pytest.mark.parametrize(
    "existing",
    [
        "# Doc\n<!-- SPECKIT START -->\ndangling start\n",
        "dangling end\n<!-- SPECKIT END -->\nrest\n",
        "no markers at all",
    ],
    ids=["start-only", "end-only", "no-markers-no-newline"],
)
def test_python_handles_partial_markers_matching_bash(
    tmp_path: Path, existing: str
) -> None:
    repo_a, repo_b = twin_projects(tmp_path, context_file="AGENTS.md")
    for repo in (repo_a, repo_b):
        add_plan(repo)
        (repo / "AGENTS.md").write_text(existing, encoding="utf-8")

    bash = run_bash(repo_a)
    py = run_python(repo_b)

    assert_parity(bash, py, repo_a, repo_b)
    assert (repo_a / "AGENTS.md").read_bytes() == (repo_b / "AGENTS.md").read_bytes()


@requires_posix_bash
def test_python_custom_markers_matching_bash(tmp_path: Path) -> None:
    markers = {"start": "<!-- CTX BEGIN -->", "end": "<!-- CTX FINISH -->"}
    repo_a, repo_b = twin_projects(
        tmp_path, context_file="AGENTS.md", context_markers=markers
    )
    existing = "intro\n<!-- CTX BEGIN -->\nold\n<!-- CTX FINISH -->\noutro\n"
    for repo in (repo_a, repo_b):
        add_plan(repo)
        (repo / "AGENTS.md").write_text(existing, encoding="utf-8")

    bash = run_bash(repo_a)
    py = run_python(repo_b)

    assert_parity(bash, py, repo_a, repo_b)
    content = (repo_b / "AGENTS.md").read_text(encoding="utf-8")
    assert content == (repo_a / "AGENTS.md").read_text(encoding="utf-8")
    assert "<!-- CTX BEGIN -->" in content
    assert "old" not in content


@requires_posix_bash
def test_python_multiple_context_files_dedup_matching_bash(tmp_path: Path) -> None:
    files = ["AGENTS.md", "docs/CONTEXT.md", "AGENTS.md"]
    repo_a, repo_b = twin_projects(tmp_path, context_files=files)
    add_plan(repo_a)
    add_plan(repo_b)

    bash = run_bash(repo_a)
    py = run_python(repo_b)

    assert_parity(bash, py, repo_a, repo_b)
    assert bash.stdout.count("agent-context: updated") == 2
    for name in ("AGENTS.md", "docs/CONTEXT.md"):
        assert (repo_a / name).read_bytes() == (repo_b / name).read_bytes()


@requires_posix_bash
def test_python_normalizes_crlf_matching_bash(tmp_path: Path) -> None:
    repo_a, repo_b = twin_projects(tmp_path, context_file="AGENTS.md")
    existing = b"# Doc\r\n\r\n<!-- SPECKIT START -->\r\nold\r\n<!-- SPECKIT END -->\r\ntail\r\n"
    for repo in (repo_a, repo_b):
        add_plan(repo)
        (repo / "AGENTS.md").write_bytes(existing)

    bash = run_bash(repo_a)
    py = run_python(repo_b)

    assert_parity(bash, py, repo_a, repo_b)
    content = (repo_b / "AGENTS.md").read_bytes()
    assert content == (repo_a / "AGENTS.md").read_bytes()
    assert b"\r" not in content


@requires_posix_bash
def test_python_mdc_frontmatter_repair_matching_bash(tmp_path: Path) -> None:
    mdc = ".cursor/rules/specify-rules.mdc"
    cases = {
        "missing": "# Rules\n",
        "false-value": "---\ndescription: rules\nalwaysApply: false\n---\n\n# Rules\n",
        "no-key": "---\ndescription: rules\n---\n\n# Rules\n",
    }
    for name, existing in cases.items():
        repo_a = make_project(tmp_path / f"a-{name}", context_file=mdc)
        repo_b = make_project(tmp_path / f"b-{name}", context_file=mdc)
        for repo in (repo_a, repo_b):
            add_plan(repo)
            target = repo / mdc
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(existing, encoding="utf-8")

        bash = run_bash(repo_a)
        py = run_python(repo_b)

        assert_parity(bash, py, repo_a, repo_b)
        content = (repo_b / mdc).read_text(encoding="utf-8")
        assert content == (repo_a / mdc).read_text(encoding="utf-8"), name
        assert "alwaysApply: true" in content, name


# ── Plan-path resolution ─────────────────────────────────────────────────────


@requires_posix_bash
def test_python_explicit_plan_argument_matching_bash(tmp_path: Path) -> None:
    repo_a, repo_b = twin_projects(tmp_path, context_file="AGENTS.md")

    bash = run_bash(repo_a, "specs/009-explicit/plan.md")
    py = run_python(repo_b, "specs/009-explicit/plan.md")

    assert_parity(bash, py, repo_a, repo_b)
    content = (repo_b / "AGENTS.md").read_bytes()
    assert content == (repo_a / "AGENTS.md").read_bytes()
    assert b"at specs/009-explicit/plan.md" in content


@requires_posix_bash
def test_python_mtime_fallback_matching_bash(tmp_path: Path) -> None:
    repo_a, repo_b = twin_projects(tmp_path, context_file="AGENTS.md")
    now = time.time()
    for repo in (repo_a, repo_b):
        for feature, age in (("specs/000-old", 10), ("specs/001-new", 0)):
            plan = repo / feature / "plan.md"
            plan.parent.mkdir(parents=True, exist_ok=True)
            plan.write_text("# plan\n", encoding="utf-8")
            os.utime(plan, (now - age, now - age))

    bash = run_bash(repo_a)
    py = run_python(repo_b)

    assert_parity(bash, py, repo_a, repo_b)
    content = (repo_b / "AGENTS.md").read_bytes()
    assert content == (repo_a / "AGENTS.md").read_bytes()
    assert b"at specs/001-new/plan.md" in content


@requires_posix_bash
def test_python_mtime_fallback_finds_nested_plan_matching_bash(
    tmp_path: Path,
) -> None:
    """The mtime fallback must recurse into scoped layouts.

    A plan created under specs/<scope>/<feature>/plan.md (as produced via
    SPECIFY_FEATURE_DIRECTORY) is more than one level below specs/. The old
    Python port used a one-level specs/*/plan.md glob and missed it, while the
    bash/PowerShell twins recurse (#3024). This locks in the parity.
    """
    repo_a, repo_b = twin_projects(tmp_path, context_file="AGENTS.md")
    for repo in (repo_a, repo_b):
        plan = repo / "specs" / "backend" / "001-nested" / "plan.md"
        plan.parent.mkdir(parents=True, exist_ok=True)
        plan.write_text("# plan\n", encoding="utf-8")

    bash = run_bash(repo_a)
    py = run_python(repo_b)

    assert_parity(bash, py, repo_a, repo_b)
    content = (repo_b / "AGENTS.md").read_bytes()
    assert content == (repo_a / "AGENTS.md").read_bytes()
    assert b"at specs/backend/001-nested/plan.md" in content


@pytest.mark.parametrize(
    "run_script",
    [
        pytest.param(run_python, id="python"),
        pytest.param(run_bash, id="bash", marks=requires_bash),
    ],
)
@pytest.mark.parametrize("has_regular_plan", [False, True], ids=["alone", "with-plan"])
@pytest.mark.parametrize(
    "candidate_kind",
    [
        "regular-file",
        "directory",
        "dangling-link",
        "non-directory-link",
        "directory-link",
        "file-link",
        "escaping-link",
    ],
)
def test_mtime_fallback_selects_only_in_project_files(
    tmp_path: Path, run_script, has_regular_plan: bool, candidate_kind: str
) -> None:
    repo = make_project(tmp_path / "project", context_file="AGENTS.md")
    expected_plan = ""
    if has_regular_plan:
        expected_plan = "specs/backend/001-valid/plan.md"
        plan = repo / expected_plan
        plan.parent.mkdir(parents=True)
        plan.write_text("# older plan\n", encoding="utf-8")
        os.utime(plan, (1_600_000_000, 1_600_000_000))

    candidate = repo / "specs/999-candidate/plan.md"
    candidate.parent.mkdir(parents=True)
    if candidate_kind == "regular-file":
        candidate.write_text("# newer plan\n", encoding="utf-8")
        os.utime(candidate, (1_700_000_000, 1_700_000_000))
        expected_plan = "specs/999-candidate/plan.md"
    elif candidate_kind == "directory":
        candidate.mkdir()
        os.utime(candidate, (1_700_000_000, 1_700_000_000))
    else:
        target = repo / "plans/current.md"
        if candidate_kind == "escaping-link":
            target = tmp_path / "outside.md"
        if candidate_kind == "non-directory-link":
            target.parent.parent.mkdir(parents=True, exist_ok=True)
            target.parent.write_text("not a directory\n", encoding="utf-8")
        elif candidate_kind == "directory-link":
            target.mkdir(parents=True)
        elif candidate_kind != "dangling-link":
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text("# linked plan\n", encoding="utf-8")
        try:
            candidate.symlink_to(
                target, target_is_directory=candidate_kind == "directory-link"
            )
        except (OSError, NotImplementedError) as exc:
            pytest.skip(f"symlinks unavailable: {exc}")
        if candidate_kind not in ("dangling-link", "non-directory-link"):
            os.utime(target, (1_700_000_000, 1_700_000_000))
        if candidate_kind == "file-link":
            # Valid file links retain target mtime ordering and resolved paths,
            # including targets outside specs/ that are still in the project.
            expected_plan = "plans/current.md"

    result = run_script(repo)

    assert result.returncode == 0, result.stderr
    assert result.stderr == ""
    assert result.stdout == "agent-context: updated AGENTS.md\n"
    expected = (
        "<!-- SPECKIT START -->\n"
        "For additional context about technologies to be used, project structure,\n"
        "shell commands, and other important information, read the current plan\n"
    )
    if expected_plan:
        expected += f"at {expected_plan}\n"
    expected += "<!-- SPECKIT END -->\n"
    assert (repo / "AGENTS.md").read_bytes() == expected.encode("utf-8")


@pytest.fixture(params=["python", "bash-python"])
def mtime_resolver(request, monkeypatch):
    """Run actual resolver code; the Bash heredoc needs no shell for IO injection."""
    if request.param == "python":
        return runpy.run_path(str(PY_SCRIPT))["_resolve_plan_path"]

    matches = re.findall(
        r"_plan_rel=\"\$\(\"\$_python\" - \"\$PROJECT_ROOT\" <<'PY'\n(.*?)\nPY\n\)\"",
        BASH_SCRIPT.read_text(encoding="utf-8"),
        re.DOTALL,
    )
    assert len(matches) == 1, "expected exactly one mtime fallback heredoc"
    code = compile(matches[0], str(BASH_SCRIPT), "exec")

    def resolve(project_root):
        output = io.StringIO()
        with monkeypatch.context() as patch, redirect_stdout(output):
            patch.setattr(sys, "argv", ["-", str(project_root)])
            exec(code, {})
        return output.getvalue().strip()

    return resolve


@pytest.fixture(params=[False, True], ids=["alone", "with-plan"])
def mtime_candidate(tmp_path, request):
    repo = make_project(tmp_path.resolve() / "project", context_file="AGENTS.md")
    expected_plan = ""
    if request.param:
        expected_plan = "specs/backend/001-valid/plan.md"
        plan = repo / expected_plan
        plan.parent.mkdir(parents=True)
        plan.write_text("# older plan\n", encoding="utf-8")
        os.utime(plan, (1_600_000_000, 1_600_000_000))
    candidate = repo / "specs/999-candidate/plan.md"
    candidate.parent.mkdir(parents=True)
    candidate.write_text("# candidate\n", encoding="utf-8")
    return repo, candidate, expected_plan


def _patch_candidate_io(
    monkeypatch, specs_root, candidate, stat_errors, *, resolved=None, resolve_error=None
):
    """Inject at os.stat so Python 3.14's os.path.isfile path is covered too.

    Resolve is controlled separately: these tests distinguish excluded paths
    from stat failures after successful in-project containment, on every OS.
    """
    original_rglob = Path.rglob
    original_stat = os.stat
    original_resolve = Path.resolve
    # Literal-name globbing can stat candidates before yielding them. Capture
    # real enumeration first so injected errors reach only resolver operations.
    candidates = tuple(original_rglob(specs_root, "plan.md"))
    assert candidate in candidates, "expected the candidate in real specs enumeration"
    calls = []

    def rglob(path, pattern, *args, **kwargs):
        if path == specs_root and pattern == "plan.md":
            return iter(candidates)
        return original_rglob(path, pattern, *args, **kwargs)

    def stat(path, *args, **kwargs):
        if isinstance(path, (str, os.PathLike)) and Path(path) == candidate:
            calls.append(path)
            error = stat_errors.get(len(calls))
            if error is not None:
                raise OSError(error, "injected candidate stat error", str(path))
        return original_stat(path, *args, **kwargs)

    def resolve(path, *args, **kwargs):
        if path == candidate:
            if resolve_error is not None:
                raise OSError(resolve_error, "injected resolve error", str(path))
            return candidate if resolved is None else resolved
        return original_resolve(path, *args, **kwargs)

    monkeypatch.setattr(Path, "rglob", rglob)
    monkeypatch.setattr(os, "stat", stat)
    monkeypatch.setattr(Path, "resolve", resolve)
    return calls


@pytest.mark.parametrize("resolve_fails", [False, True], ids=["external", "resolve-error"])
def test_mtime_fallback_ignores_excluded_candidate_errors(
    monkeypatch, mtime_resolver, mtime_candidate, resolve_fails
):
    repo, candidate, expected_plan = mtime_candidate
    calls = _patch_candidate_io(
        monkeypatch,
        repo / "specs",
        candidate,
        {1: errno.EACCES},
        resolved=repo.parent / "private/plan.md",
        resolve_error=errno.EACCES if resolve_fails else None,
    )
    assert mtime_resolver(str(repo)) == expected_plan
    assert calls == [], "excluded candidates must not reach the stat precheck"


@pytest.mark.parametrize("error", [errno.EACCES, errno.EPERM, errno.EIO])
def test_mtime_fallback_preserves_contained_stat_errors(
    monkeypatch, mtime_resolver, mtime_candidate, error
):
    repo, candidate, _ = mtime_candidate
    calls = _patch_candidate_io(monkeypatch, repo / "specs", candidate, {1: error})
    with pytest.raises(OSError) as exc:
        mtime_resolver(str(repo))
    assert type(exc.value) is type(OSError(error, ""))
    assert exc.value.errno == error
    assert len(calls) == 1


@pytest.mark.parametrize("error", [errno.ENOENT, errno.ENOTDIR])
def test_mtime_fallback_skips_missing_candidate_at_precheck(
    monkeypatch, mtime_resolver, mtime_candidate, error
):
    repo, candidate, expected_plan = mtime_candidate
    calls = _patch_candidate_io(monkeypatch, repo / "specs", candidate, {1: error})
    assert mtime_resolver(str(repo)) == expected_plan
    assert len(calls) == 1


@pytest.mark.parametrize("error", [errno.EACCES, errno.ENOENT, errno.ENOTDIR])
def test_mtime_fallback_propagates_sort_stat_errors(
    monkeypatch, mtime_resolver, mtime_candidate, error
):
    repo, candidate, _ = mtime_candidate
    calls = _patch_candidate_io(monkeypatch, repo / "specs", candidate, {2: error})
    with pytest.raises(OSError) as exc:
        mtime_resolver(str(repo))
    assert type(exc.value) is type(OSError(error, ""))
    assert exc.value.errno == error
    assert len(calls) == 2


@pytest.mark.parametrize(
    "run_script",
    [
        pytest.param(run_python, id="python"),
        pytest.param(run_bash, id="bash", marks=requires_bash),
    ],
)
@pytest.mark.parametrize("has_regular_plan", [False, True], ids=["alone", "with-plan"])
def test_mtime_fallback_skips_inaccessible_external_symlink(
    tmp_path, run_script, has_regular_plan
):
    repo = make_project(tmp_path / "project", context_file="AGENTS.md")
    expected_plan = ""
    if has_regular_plan:
        expected_plan = "specs/001-valid/plan.md"
        plan = repo / expected_plan
        plan.parent.mkdir(parents=True)
        plan.write_text("# plan\n", encoding="utf-8")
    private = tmp_path / "private"
    private.mkdir()
    target = private / "plan.md"
    target.write_text("# external plan\n", encoding="utf-8")
    candidate = repo / "specs/999-candidate/plan.md"
    candidate.parent.mkdir(parents=True)
    try:
        candidate.symlink_to(target)
    except (OSError, NotImplementedError) as exc:
        pytest.skip(f"symlinks unavailable: {exc}")
    original_mode = private.stat().st_mode
    try:
        private.chmod(0)
        try:
            candidate.stat()
        except PermissionError as exc:
            assert exc.errno == errno.EACCES
        else:
            pytest.skip("directory permissions do not cause EACCES for this user/filesystem")
        result = run_script(repo)
    finally:
        private.chmod(original_mode)

    assert result.returncode == 0, result.stderr
    assert result.stdout == "agent-context: updated AGENTS.md\n"
    assert result.stderr == ""
    expected = (
        "<!-- SPECKIT START -->\n"
        "For additional context about technologies to be used, project structure,\n"
        "shell commands, and other important information, read the current plan\n"
    )
    if expected_plan:
        expected += f"at {expected_plan}\n"
    expected += "<!-- SPECKIT END -->\n"
    assert (repo / "AGENTS.md").read_bytes() == expected.encode("utf-8")


@requires_posix_bash
def test_python_mtime_fallback_skips_plan_reached_through_escaping_symlink(
    tmp_path: Path,
) -> None:
    """A plan reached via a specs/ symlink out of the project is not selected.

    ``relative_to()`` is lexical, so ``specs/linked/001-x/plan.md`` looks
    in-project even when ``specs/linked`` points outside the tree. Resolving
    before the containment check rejects it, so the fallback finds nothing and
    the ``at <plan>`` line is omitted rather than naming an out-of-project file
    with an in-project-looking path. Mirrors the bash twin's ``_resolved_rel``.
    """
    repo_a, repo_b = twin_projects(tmp_path, context_file="AGENTS.md")
    for repo in (repo_a, repo_b):
        outside = repo.parent / f"outside-{repo.name}" / "001-x"
        outside.mkdir(parents=True, exist_ok=True)
        (outside / "plan.md").write_text("# plan\n", encoding="utf-8")
        specs = repo / "specs"
        specs.mkdir(parents=True, exist_ok=True)
        (specs / "linked").symlink_to(outside.parent, target_is_directory=True)
        # Sanity: the plan really is reachable through the symlink.
        assert (specs / "linked" / "001-x" / "plan.md").is_file()

    bash = run_bash(repo_a)
    py = run_python(repo_b)

    assert_parity(bash, py, repo_a, repo_b)
    content = (repo_b / "AGENTS.md").read_bytes()
    assert content == (repo_a / "AGENTS.md").read_bytes()
    assert b"\nat " not in content


@requires_posix_bash
def test_python_prefers_feature_json_over_mtime_matching_bash(tmp_path: Path) -> None:
    repo_a, repo_b = twin_projects(tmp_path, context_file="AGENTS.md")
    now = time.time()
    for repo in (repo_a, repo_b):
        add_plan(repo, "specs/001-active")
        stale = repo / "specs" / "000-stale" / "plan.md"
        stale.parent.mkdir(parents=True, exist_ok=True)
        stale.write_text("# plan\n", encoding="utf-8")
        os.utime(repo / "specs" / "001-active" / "plan.md", (now - 10, now - 10))
        os.utime(stale, (now, now))

    bash = run_bash(repo_a)
    py = run_python(repo_b)

    assert_parity(bash, py, repo_a, repo_b)
    content = (repo_b / "AGENTS.md").read_bytes()
    assert content == (repo_a / "AGENTS.md").read_bytes()
    assert b"at specs/001-active/plan.md" in content


@requires_posix_bash
def test_python_no_plan_omits_at_line_matching_bash(tmp_path: Path) -> None:
    repo_a, repo_b = twin_projects(tmp_path, context_file="AGENTS.md")

    bash = run_bash(repo_a)
    py = run_python(repo_b)

    assert_parity(bash, py, repo_a, repo_b)
    content = (repo_b / "AGENTS.md").read_bytes()
    assert content == (repo_a / "AGENTS.md").read_bytes()
    assert b"\nat " not in content


# ── Config gates and path validation ─────────────────────────────────────────


@requires_posix_bash
def test_python_missing_config_matching_bash(tmp_path: Path) -> None:
    repo_a = tmp_path / "proj-a"
    repo_b = tmp_path / "proj-b"
    repo_a.mkdir()
    repo_b.mkdir()

    bash = run_bash(repo_a)
    py = run_python(repo_b)

    assert_parity(bash, py, repo_a, repo_b)
    assert py.returncode == 0
    assert "not found; nothing to do." in py.stderr


@requires_posix_bash
def test_python_unparseable_config_matching_bash(tmp_path: Path) -> None:
    repo_a = tmp_path / "proj-a"
    repo_b = tmp_path / "proj-b"
    for repo in (repo_a, repo_b):
        cfg_dir = repo / ".specify" / "extensions" / "agent-context"
        cfg_dir.mkdir(parents=True)
        (cfg_dir / "agent-context-config.yml").write_text(
            "context_file: [unclosed\n", encoding="utf-8"
        )

    bash = run_bash(repo_a)
    py = run_python(repo_b)

    assert_parity(bash, py, repo_a, repo_b)
    assert py.returncode == 0
    assert "cannot update context." in py.stderr
    assert "agent-context: skipping update (see above for details)." in py.stderr


@requires_posix_bash
def test_python_empty_config_matching_bash(tmp_path: Path) -> None:
    repo_a, repo_b = twin_projects(tmp_path)

    bash = run_bash(repo_a)
    py = run_python(repo_b)

    assert_parity(bash, py, repo_a, repo_b)
    assert py.returncode == 0
    assert "context_files/context_file not set" in py.stderr


@pytest.mark.parametrize(
    "run_shell",
    [
        pytest.param(run_bash, id="bash", marks=requires_posix_bash),
        pytest.param(
            run_powershell,
            id="powershell",
            marks=pytest.mark.skipif(not POWERSHELL, reason="no PowerShell available"),
        ),
    ],
)
@pytest.mark.parametrize(
    ("integration", "context_file"),
    [("claude", "CLAUDE.md"), ("mcode", "AGENTS.md")],
)
def test_python_self_seed_from_init_options_matching_shell(
    tmp_path: Path, run_shell, integration: str, context_file: str
) -> None:
    repo_a, repo_b = twin_projects(tmp_path)
    for repo in (repo_a, repo_b):
        add_plan(repo)
        (repo / ".specify" / "init-options.json").write_text(
            json.dumps({"integration": integration}), encoding="utf-8"
        )
        shutil.copy(
            EXT_DIR / "agent-context-defaults.json",
            repo
            / ".specify"
            / "extensions"
            / "agent-context"
            / "agent-context-defaults.json",
        )

    shell = run_shell(repo_a)
    py = run_python(repo_b)

    assert shell.returncode == py.returncode == 0, shell.stderr + py.stderr
    if run_shell is run_bash:
        assert_parity(shell, py, repo_a, repo_b)
    content = (repo_b / context_file).read_bytes()
    assert (repo_a / context_file).read_bytes() == content
    assert b"<!-- SPECKIT START -->" in content
    assert b"specs/001-demo/plan.md" in content


@requires_posix_bash
@pytest.mark.parametrize(
    "bad_path",
    ["/etc/AGENTS.md", "docs\\AGENTS.md", "../outside.md", "nested/../../escape.md"],
    ids=["absolute", "backslash", "dotdot", "nested-dotdot"],
)
def test_python_rejects_escaping_paths_matching_bash(
    tmp_path: Path, bad_path: str
) -> None:
    repo_a, repo_b = twin_projects(tmp_path, context_file=bad_path)

    bash = run_bash(repo_a)
    py = run_python(repo_b)

    assert_parity(bash, py, repo_a, repo_b)
    assert py.returncode == 1
    assert not (repo_b / "AGENTS.md").exists()


# ── PowerShell parity (content only) ─────────────────────────────────────────


@pytest.mark.skipif(not POWERSHELL, reason="no PowerShell available")
def test_python_fresh_context_file_matches_powershell(tmp_path: Path) -> None:
    repo_a = make_project(tmp_path / "proj-ps", context_file="AGENTS.md")
    repo_b = make_project(tmp_path / "proj-py", context_file="AGENTS.md")
    add_plan(repo_a)
    add_plan(repo_b)

    ps = run_powershell(repo_a)
    py = run_python(repo_b)

    assert ps.returncode == py.returncode == 0, ps.stderr + py.stderr
    assert (repo_a / "AGENTS.md").read_bytes() == (repo_b / "AGENTS.md").read_bytes()


@pytest.mark.skipif(not POWERSHELL, reason="no PowerShell available")
def test_python_mtime_fallback_finds_nested_plan_matches_powershell(
    tmp_path: Path,
) -> None:
    """Python's mtime fallback must recurse like the PowerShell twin.

    With no feature.json, discovery falls back to scanning under specs/. A plan
    at specs/<scope>/<feature>/plan.md sits more than one level deep; the old
    Python one-level glob missed it while PowerShell already recurses (#3024).
    """
    repo_a = make_project(tmp_path / "proj-ps", context_file="AGENTS.md")
    repo_b = make_project(tmp_path / "proj-py", context_file="AGENTS.md")
    for repo in (repo_a, repo_b):
        plan = repo / "specs" / "backend" / "001-nested" / "plan.md"
        plan.parent.mkdir(parents=True, exist_ok=True)
        plan.write_text("# plan\n", encoding="utf-8")

    ps = run_powershell(repo_a)
    py = run_python(repo_b)

    assert ps.returncode == py.returncode == 0, ps.stderr + py.stderr
    assert (repo_a / "AGENTS.md").read_bytes() == (repo_b / "AGENTS.md").read_bytes()
    assert b"at specs/backend/001-nested/plan.md" in (repo_b / "AGENTS.md").read_bytes()


@pytest.mark.skipif(not POWERSHELL, reason="no PowerShell available")
def test_python_upsert_matches_powershell(tmp_path: Path) -> None:
    repo_a = make_project(tmp_path / "proj-ps", context_file="AGENTS.md")
    repo_b = make_project(tmp_path / "proj-py", context_file="AGENTS.md")
    existing = (
        "# My project\n\n"
        "<!-- SPECKIT START -->\nstale\n<!-- SPECKIT END -->\n"
        "\ntail\n"
    )
    for repo in (repo_a, repo_b):
        add_plan(repo)
        (repo / "AGENTS.md").write_text(existing, encoding="utf-8")

    ps = run_powershell(repo_a)
    py = run_python(repo_b)

    assert ps.returncode == py.returncode == 0, ps.stderr + py.stderr
    assert (repo_a / "AGENTS.md").read_bytes() == (repo_b / "AGENTS.md").read_bytes()
