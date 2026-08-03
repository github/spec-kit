"""Parity tests for the Python setup-plan port."""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.conftest import requires_bash
from tests.parity_helpers import (
    HAS_POWERSHELL,
    POWERSHELL_EXE,
    bash_cmd,
    clean_env,
    install_scripts,
    json_stdout,
    make_repo,
    normalize_repo_paths,
    ps_cmd,
    py_cmd,
    run,
    write_feature_json,
)

SCRIPT = "setup-plan"
TEMPLATE_BODY = "# Plan Template\n\nBody.\n"


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
        assert plan.read_text(encoding="utf-8") == TEMPLATE_BODY


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
def test_all_variants_ignore_extra_arguments(tmp_path: Path) -> None:
    repos = [
        _setup_repo(tmp_path, "bash"),
        _setup_repo(tmp_path, "powershell"),
        _setup_repo(tmp_path, "python"),
    ]

    bash = run(bash_cmd(repos[0], SCRIPT, "--json", "--bogus"), repos[0])
    ps = run(ps_cmd(repos[1], SCRIPT, "-Json", "--bogus"), repos[1])
    py = run(py_cmd(repos[2], SCRIPT, "--json", "--bogus"), repos[2])

    assert bash.returncode == ps.returncode == py.returncode == 0
    assert normalize_repo_paths(bash.stdout, repos[0]) == normalize_repo_paths(
        ps.stdout, repos[1]
    ) == normalize_repo_paths(py.stdout, repos[2])
    assert normalize_repo_paths(bash.stderr, repos[0]) == normalize_repo_paths(
        ps.stderr, repos[1]
    ) == normalize_repo_paths(py.stderr, repos[2])


@requires_bash
def test_python_missing_template_matches_bash(tmp_path: Path) -> None:
    repo_a = _setup_repo(tmp_path, "proj-a", template=False)
    repo_b = _setup_repo(tmp_path, "proj-b", template=False)

    bash = run(bash_cmd(repo_a, SCRIPT, "--json"), repo_a)
    py = run(py_cmd(repo_b, SCRIPT, "--json"), repo_b)

    assert py.returncode == bash.returncode == 0
    assert normalize_repo_paths(py.stderr, repo_b) == normalize_repo_paths(
        bash.stderr, repo_a
    )
    for repo in (repo_a, repo_b):
        plan = repo / "specs" / "001-my-feature" / "plan.md"
        assert plan.read_text(encoding="utf-8") == ""


@requires_bash
@pytest.mark.parametrize(
    "registry",
    [
        '{"presets": {"alpha": {"priority": "high"}, "beta": {"priority": 1}}}',
        '{"presets": {"alpha": {"priority": 2}, "beta": {"priority": 1}, "gamma": {"priority": null}}}',
        "[]",
        '{"presets":[]}',
        '{"presets":null}',
    ],
    ids=[
        "mixed_priorities",
        "null_priority",
        "list_root",
        "list_presets",
        "null_presets",
    ],
)
def test_all_variants_broken_registry_falls_back_to_dir_scan(
    tmp_path: Path, registry: str
) -> None:
    """Malformed registries fall back to the alphabetical directory scan."""
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
        assert plan.read_text(encoding="utf-8") == "# alpha plan\n"


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
