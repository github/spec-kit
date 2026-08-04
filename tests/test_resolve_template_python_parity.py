"""Parity tests for composed runtime template resolution."""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.conftest import requires_bash
from tests.parity_helpers import (
    HAS_POWERSHELL,
    bash_cmd,
    clean_env,
    install_composition_stack,
    install_scripts,
    json_stdout,
    make_repo,
    ps_cmd,
    py_cmd,
    run,
)

SCRIPT = "resolve-template"
TEMPLATE = "constitution-template"


def _setup_repo(tmp_path: Path) -> tuple[Path, str]:
    repo = make_repo(tmp_path)
    install_scripts(repo, SCRIPT)
    expected = install_composition_stack(repo, TEMPLATE, "# Core\n")
    return repo, expected


@requires_bash
def test_all_variants_emit_composed_template_content(tmp_path: Path) -> None:
    repo, expected = _setup_repo(tmp_path)
    results = [
        run(bash_cmd(repo, SCRIPT, TEMPLATE, "--json"), repo),
        run(py_cmd(repo, SCRIPT, TEMPLATE, "--json"), repo),
    ]
    if HAS_POWERSHELL:
        results.append(run(ps_cmd(repo, SCRIPT, TEMPLATE, "-Json"), repo))

    assert all(result.returncode == 0 for result in results)
    assert all(result.stderr == "" for result in results)
    assert all(
        json_stdout(result)
        == {"TEMPLATE_NAME": TEMPLATE, "TEMPLATE_CONTENT": expected}
        for result in results
    )


@requires_bash
@pytest.mark.parametrize(
    "without_registry,core_content",
    [
        (True, "# Core\n"),
        (False, "# Café ✓\n"),
    ],
    ids=["directory_fallback", "unicode"],
)
def test_all_variants_preserve_composition_parity(
    tmp_path: Path, without_registry: bool, core_content: str
) -> None:
    repo = make_repo(tmp_path)
    install_scripts(repo, SCRIPT)
    expected = install_composition_stack(repo, TEMPLATE, core_content)
    if without_registry:
        (repo / ".specify" / "presets" / ".registry").unlink()
        expected = (
            "# Prepended\n\n\n"
            "## Wrapper\n"
            f"{core_content}\n"
            "## End\n\n\n"
            "# Appended\n"
        )

    results = [
        run(bash_cmd(repo, SCRIPT, TEMPLATE, "--json"), repo),
        run(py_cmd(repo, SCRIPT, TEMPLATE, "--json"), repo),
    ]
    if HAS_POWERSHELL:
        results.append(run(ps_cmd(repo, SCRIPT, TEMPLATE, "-Json"), repo))

    assert all(result.returncode == 0 for result in results)
    assert all(
        json_stdout(result)["TEMPLATE_CONTENT"] == expected
        for result in results
    )


@requires_bash
@pytest.mark.parametrize(
    "template_name",
    ["missing-template", "../../../outside"],
    ids=["missing", "path_traversal"],
)
def test_all_variants_reject_unresolvable_template(
    tmp_path: Path, template_name: str
) -> None:
    repo = make_repo(tmp_path)
    install_scripts(repo, SCRIPT)
    (repo / "outside.md").write_text("sensitive content\n", encoding="utf-8")

    results = [
        run(bash_cmd(repo, SCRIPT, template_name, "--json"), repo),
        run(py_cmd(repo, SCRIPT, template_name, "--json"), repo),
    ]
    if HAS_POWERSHELL:
        results.append(run(ps_cmd(repo, SCRIPT, template_name, "-Json"), repo))

    assert all(result.returncode == 1 for result in results)
    assert all(result.stdout == "" for result in results)
    assert all("sensitive content" not in result.stderr for result in results)


@requires_bash
def test_all_variants_fail_when_wrap_placeholder_is_missing(
    tmp_path: Path,
) -> None:
    repo = make_repo(tmp_path)
    install_scripts(repo, SCRIPT)
    templates = repo / ".specify" / "templates"
    templates.mkdir(parents=True)
    (templates / f"{TEMPLATE}.md").write_text("# Core\n", encoding="utf-8")
    preset = repo / ".specify" / "presets" / "wrap-pack"
    (preset / "templates").mkdir(parents=True)
    (preset / "templates" / f"{TEMPLATE}.md").write_text(
        "# Broken wrapper\n", encoding="utf-8"
    )
    (preset / "preset.yml").write_text(
        "provides:\n"
        "  templates:\n"
        "    - type: template\n"
        f"      name: {TEMPLATE}\n"
        f"      file: templates/{TEMPLATE}.md\n"
        "      strategy: wrap\n",
        encoding="utf-8",
    )
    (repo / ".specify" / "presets" / ".registry").write_text(
        '{"presets":{"wrap-pack":{"enabled":true,"priority":1}}}\n',
        encoding="utf-8",
    )

    results = [
        run(bash_cmd(repo, SCRIPT, TEMPLATE, "--json"), repo),
        run(py_cmd(repo, SCRIPT, TEMPLATE, "--json"), repo),
    ]
    if HAS_POWERSHELL:
        results.append(run(ps_cmd(repo, SCRIPT, TEMPLATE, "-Json"), repo))

    assert all(result.returncode != 0 for result in results)
    assert all(result.stdout == "" for result in results)


@requires_bash
def test_all_variants_fail_when_yaml_parser_is_unavailable(
    tmp_path: Path,
) -> None:
    repo, _ = _setup_repo(tmp_path)
    blocker = tmp_path / "blocker"
    blocker.mkdir()
    (blocker / "yaml.py").write_text(
        "raise ImportError('simulated missing PyYAML')\n",
        encoding="utf-8",
    )
    env = clean_env()
    env["PYTHONPATH"] = str(blocker)

    results = [
        run(bash_cmd(repo, SCRIPT, TEMPLATE, "--json"), repo, env),
        run(py_cmd(repo, SCRIPT, TEMPLATE, "--json"), repo, env),
    ]
    if HAS_POWERSHELL:
        results.append(
            run(ps_cmd(repo, SCRIPT, TEMPLATE, "-Json"), repo, env)
        )

    assert all(result.returncode != 0 for result in results)
    assert all(result.stdout == "" for result in results)


@requires_bash
def test_all_variants_fail_for_malformed_preset_manifest(
    tmp_path: Path,
) -> None:
    repo, _ = _setup_repo(tmp_path)
    (
        repo / ".specify" / "presets" / "wrap-pack" / "preset.yml"
    ).write_text("provides: [\n", encoding="utf-8")

    results = [
        run(bash_cmd(repo, SCRIPT, TEMPLATE, "--json"), repo),
        run(py_cmd(repo, SCRIPT, TEMPLATE, "--json"), repo),
    ]
    if HAS_POWERSHELL:
        results.append(run(ps_cmd(repo, SCRIPT, TEMPLATE, "-Json"), repo))

    assert all(result.returncode != 0 for result in results)
    assert all(result.stdout == "" for result in results)
