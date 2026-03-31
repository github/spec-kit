"""
Validation tests for offline/air-gapped scaffolding (PR #1803).

For every supported AI agent (except "generic") the scaffold output is verified
against invariants and compared byte-for-byte with the canonical output produced
by create-release-packages.sh.

Since scaffold_from_core_pack() now invokes the release script at runtime, the
parity test (section 9) runs the script independently and compares the results
to ensure the integration is correct.

Per-agent invariants verified
──────────────────────────────
  • Command files are written to the directory declared in AGENT_CONFIG
  • File count matches the number of source templates
  • Extension is correct: .toml (TOML agents), .agent.md (copilot), .md (rest)
  • No unresolved placeholders remain ({SCRIPT}, {ARGS}, __AGENT__)
  • Argument token is correct: {{args}} for TOML agents, $ARGUMENTS for others
  • Path rewrites applied: scripts/ → .specify/scripts/ etc.
  • TOML files have "description" and "prompt" fields
  • Markdown files have parseable YAML frontmatter
  • Copilot: companion speckit.*.prompt.md files are generated in prompts/
  • .specify/scripts/ contains at least one script file
  • .specify/templates/ contains at least one template file

Parity invariant
────────────────
  Every file produced by scaffold_from_core_pack() must be byte-for-byte
  identical to the same file in the ZIP produced by the release script.
"""

import os
import re
import shutil
import subprocess
import tomllib
import zipfile
from pathlib import Path

import pytest
import yaml

from specify_cli import (
    AGENT_CONFIG,
    _TOML_AGENTS,
    _locate_core_pack,
    scaffold_from_core_pack,
)

_REPO_ROOT = Path(__file__).parent.parent
_RELEASE_SCRIPT = _REPO_ROOT / ".github" / "workflows" / "scripts" / "create-release-packages.sh"


def _find_bash() -> str | None:
    """Return the path to a usable bash on this machine, or None."""
    # Prefer PATH lookup so non-standard install locations (Nix, CI) are found.
    on_path = shutil.which("bash")
    if on_path:
        return on_path
    candidates = [
        "/opt/homebrew/bin/bash",
        "/usr/local/bin/bash",
        "/bin/bash",
        "/usr/bin/bash",
    ]
    for candidate in candidates:
        try:
            result = subprocess.run(
                [candidate, "--version"],
                capture_output=True, text=True, timeout=5,
            )
            if result.returncode == 0:
                return candidate
        except (FileNotFoundError, subprocess.TimeoutExpired):
            continue
    return None


def _run_release_script(agent: str, script_type: str, bash: str, output_dir: Path) -> Path:
    """Run create-release-packages.sh for *agent*/*script_type* and return the
    path to the generated ZIP.  *output_dir* receives the build artifacts so
    the repo working tree stays clean."""
    env = os.environ.copy()
    env["AGENTS"] = agent
    env["SCRIPTS"] = script_type
    env["GENRELEASES_DIR"] = str(output_dir)

    result = subprocess.run(
        [bash, str(_RELEASE_SCRIPT), "v0.0.0"],
        capture_output=True, text=True,
        cwd=str(_REPO_ROOT),
        env=env,
        timeout=300,
    )

    if result.returncode != 0:
        pytest.fail(
            f"Release script failed with exit code {result.returncode}\n"
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )

    zip_pattern = f"spec-kit-template-{agent}-{script_type}-v0.0.0.zip"
    zip_path = output_dir / zip_pattern
    if not zip_path.exists():
        pytest.fail(
            f"Release script did not produce expected ZIP: {zip_path}\n"
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )
    return zip_path

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

# Number of source command templates (one per .md file in templates/commands/)


def _commands_dir() -> Path:
    """Return the command templates directory (source-checkout or core_pack)."""
    core = _locate_core_pack()
    if core and (core / "commands").is_dir():
        return core / "commands"
    # Source-checkout fallback
    repo_root = Path(__file__).parent.parent
    return repo_root / "templates" / "commands"


def _get_source_template_stems() -> list[str]:
    """Return the stems of source command template files (e.g. ['specify', 'plan', ...])."""
    return sorted(p.stem for p in _commands_dir().glob("*.md"))


def _expected_cmd_dir(project_path: Path, agent: str) -> Path:
    """Return the expected command-files directory for a given agent."""
    cfg = AGENT_CONFIG[agent]
    folder = (cfg.get("folder") or "").rstrip("/")
    subdir = cfg.get("commands_subdir", "commands")
    if folder:
        return project_path / folder / subdir
    return project_path / ".speckit" / subdir


# Agents whose commands are laid out as <skills_dir>/<name>/SKILL.md.
# Maps agent -> separator used in skill directory names.
_SKILL_AGENTS: dict[str, str] = {"codex": "-", "kimi": "-"}


def _expected_ext(agent: str) -> str:
    if agent in _TOML_AGENTS:
        return "toml"
    if agent == "copilot":
        return "agent.md"
    if agent in _SKILL_AGENTS:
        return "SKILL.md"
    return "md"


def _list_command_files(cmd_dir: Path, agent: str) -> list[Path]:
    """List generated command files, handling skills-based directory layouts."""
    if agent in _SKILL_AGENTS:
        sep = _SKILL_AGENTS[agent]
        return sorted(cmd_dir.glob(f"speckit{sep}*/SKILL.md"))
    ext = _expected_ext(agent)
    return sorted(cmd_dir.glob(f"speckit.*.{ext}"))


def _collect_relative_files(root: Path) -> dict[str, bytes]:
    """Walk *root* and return {relative_posix_path: file_bytes}."""
    result: dict[str, bytes] = {}
    for p in root.rglob("*"):
        if p.is_file():
            result[p.relative_to(root).as_posix()] = p.read_bytes()
    return result


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def source_template_stems() -> list[str]:
    return _get_source_template_stems()


@pytest.fixture(scope="session")
def scaffolded_sh(tmp_path_factory):
    """Session-scoped cache: scaffold once per agent with script_type='sh'."""
    cache = {}
    def _get(agent: str) -> Path:
        if agent not in cache:
            project = tmp_path_factory.mktemp(f"scaffold_sh_{agent}")
            ok = scaffold_from_core_pack(project, agent, "sh")
            assert ok, f"scaffold_from_core_pack returned False for agent '{agent}'"
            cache[agent] = project
        return cache[agent]
    return _get


@pytest.fixture(scope="session")
def scaffolded_ps(tmp_path_factory):
    """Session-scoped cache: scaffold once per agent with script_type='ps'."""
    cache = {}
    def _get(agent: str) -> Path:
        if agent not in cache:
            project = tmp_path_factory.mktemp(f"scaffold_ps_{agent}")
            ok = scaffold_from_core_pack(project, agent, "ps")
            assert ok, f"scaffold_from_core_pack returned False for agent '{agent}'"
            cache[agent] = project
        return cache[agent]
    return _get


# ---------------------------------------------------------------------------
# Parametrize over all agents except "generic"
# ---------------------------------------------------------------------------

_TESTABLE_AGENTS = [a for a in AGENT_CONFIG if a != "generic"]


# ---------------------------------------------------------------------------
# 1. Bundled scaffold — directory structure
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("agent", _TESTABLE_AGENTS)
def test_scaffold_creates_specify_scripts(agent, scaffolded_sh):
    """scaffold_from_core_pack copies at least one script into .specify/scripts/."""
    project = scaffolded_sh(agent)

    scripts_dir = project / ".specify" / "scripts" / "bash"
    assert scripts_dir.is_dir(), f".specify/scripts/bash/ missing for agent '{agent}'"
    assert any(scripts_dir.iterdir()), f".specify/scripts/bash/ is empty for agent '{agent}'"


@pytest.mark.parametrize("agent", _TESTABLE_AGENTS)
def test_scaffold_creates_specify_templates(agent, scaffolded_sh):
    """scaffold_from_core_pack copies at least one page template into .specify/templates/."""
    project = scaffolded_sh(agent)

    tpl_dir = project / ".specify" / "templates"
    assert tpl_dir.is_dir(), f".specify/templates/ missing for agent '{agent}'"
    assert any(tpl_dir.iterdir()), ".specify/templates/ is empty"


@pytest.mark.parametrize("agent", _TESTABLE_AGENTS)
def test_scaffold_command_dir_location(agent, scaffolded_sh):
    """Command files land in the directory declared by AGENT_CONFIG."""
    project = scaffolded_sh(agent)

    cmd_dir = _expected_cmd_dir(project, agent)
    assert cmd_dir.is_dir(), (
        f"Command dir '{cmd_dir.relative_to(project)}' not created for agent '{agent}'"
    )


# ---------------------------------------------------------------------------
# 2. Bundled scaffold — file count
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("agent", _TESTABLE_AGENTS)
def test_scaffold_command_file_count(agent, scaffolded_sh, source_template_stems):
    """One command file is generated per source template for every agent."""
    project = scaffolded_sh(agent)

    cmd_dir = _expected_cmd_dir(project, agent)
    generated = _list_command_files(cmd_dir, agent)

    if cmd_dir.is_dir():
        dir_listing = list(cmd_dir.iterdir())
    else:
        dir_listing = f"<command dir missing: {cmd_dir}>"

    assert len(generated) == len(source_template_stems), (
        f"Agent '{agent}': expected {len(source_template_stems)} command files "
        f"({_expected_ext(agent)}), found {len(generated)}. Dir: {dir_listing}"
    )


@pytest.mark.parametrize("agent", _TESTABLE_AGENTS)
def test_scaffold_command_file_names(agent, scaffolded_sh, source_template_stems):
    """Each source template stem maps to a corresponding speckit.<stem>.<ext> file."""
    project = scaffolded_sh(agent)

    cmd_dir = _expected_cmd_dir(project, agent)
    for stem in source_template_stems:
        if agent in _SKILL_AGENTS:
            sep = _SKILL_AGENTS[agent]
            expected = cmd_dir / f"speckit{sep}{stem}" / "SKILL.md"
        else:
            ext = _expected_ext(agent)
            expected = cmd_dir / f"speckit.{stem}.{ext}"
        assert expected.is_file(), (
            f"Agent '{agent}': expected file '{expected.name}' not found in '{cmd_dir}'"
        )


# ---------------------------------------------------------------------------
# 3. Bundled scaffold — content invariants
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("agent", _TESTABLE_AGENTS)
def test_no_unresolved_script_placeholder(agent, scaffolded_sh):
    """{SCRIPT} must not appear in any generated command file."""
    project = scaffolded_sh(agent)

    cmd_dir = _expected_cmd_dir(project, agent)
    for f in cmd_dir.rglob("*"):
        if f.is_file():
            content = f.read_text(encoding="utf-8")
            assert "{SCRIPT}" not in content, (
                f"Unresolved {{SCRIPT}} in '{f.relative_to(project)}' for agent '{agent}'"
            )


@pytest.mark.parametrize("agent", _TESTABLE_AGENTS)
def test_no_unresolved_agent_placeholder(agent, scaffolded_sh):
    """__AGENT__ must not appear in any generated command file."""
    project = scaffolded_sh(agent)

    cmd_dir = _expected_cmd_dir(project, agent)
    for f in cmd_dir.rglob("*"):
        if f.is_file():
            content = f.read_text(encoding="utf-8")
            assert "__AGENT__" not in content, (
                f"Unresolved __AGENT__ in '{f.relative_to(project)}' for agent '{agent}'"
            )


@pytest.mark.parametrize("agent", _TESTABLE_AGENTS)
def test_no_unresolved_args_placeholder(agent, scaffolded_sh):
    """{ARGS} must not appear in any generated command file (replaced with agent-specific token)."""
    project = scaffolded_sh(agent)

    cmd_dir = _expected_cmd_dir(project, agent)
    for f in cmd_dir.rglob("*"):
        if f.is_file():
            content = f.read_text(encoding="utf-8")
            assert "{ARGS}" not in content, (
                f"Unresolved {{ARGS}} in '{f.relative_to(project)}' for agent '{agent}'"
            )


# Build a set of template stems that actually contain {ARGS} in their source.
_TEMPLATES_WITH_ARGS: frozenset[str] = frozenset(
    p.stem
    for p in _commands_dir().glob("*.md")
    if "{ARGS}" in p.read_text(encoding="utf-8")
)


@pytest.mark.parametrize("agent", _TESTABLE_AGENTS)
def test_argument_token_format(agent, scaffolded_sh):
    """For templates that carry an {ARGS} token:
    - TOML agents must emit {{args}}
    - Forge must emit {{parameters}}
    - Other Markdown agents must emit $ARGUMENTS
    Templates without {ARGS} (e.g. implement, plan) are skipped.
    """
    project = scaffolded_sh(agent)

    cmd_dir = _expected_cmd_dir(project, agent)

    for f in _list_command_files(cmd_dir, agent):
        # Recover the stem from the file path
        if agent in _SKILL_AGENTS:
            sep = _SKILL_AGENTS[agent]
            stem = f.parent.name.removeprefix(f"speckit{sep}")
        else:
            ext = _expected_ext(agent)
            stem = f.name.removeprefix("speckit.").removesuffix(f".{ext}")
        if stem not in _TEMPLATES_WITH_ARGS:
            continue  # this template has no argument token

        content = f.read_text(encoding="utf-8")
        if agent in _TOML_AGENTS:
            assert "{{args}}" in content, (
                f"TOML agent '{agent}': expected '{{{{args}}}}' in '{f.name}'"
            )
        elif agent == "forge":
            # Forge uses {{parameters}} instead of $ARGUMENTS
            assert "{{parameters}}" in content, (
                f"Forge agent: expected '{{{{parameters}}}}' in '{f.name}'"
            )
        else:
            assert "$ARGUMENTS" in content, (
                f"Markdown agent '{agent}': expected '$ARGUMENTS' in '{f.name}'"
            )


@pytest.mark.parametrize("agent", _TESTABLE_AGENTS)
def test_path_rewrites_applied(agent, scaffolded_sh):
    """Bare scripts/ and templates/ paths must be rewritten to .specify/ variants.

    YAML frontmatter 'source:' metadata fields are excluded — they reference
    the original template path for provenance, not a runtime path.
    """
    project = scaffolded_sh(agent)

    cmd_dir = _expected_cmd_dir(project, agent)
    for f in cmd_dir.rglob("*"):
        if not f.is_file():
            continue
        content = f.read_text(encoding="utf-8")

        # Strip YAML frontmatter before checking — source: metadata is not a runtime path
        body = content
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                body = parts[2]

        # Should not contain bare (non-.specify/) script paths
        assert not re.search(r'(?<!\.specify/)scripts/', body), (
            f"Bare scripts/ path found in '{f.relative_to(project)}' for agent '{agent}'"
        )
        assert not re.search(r'(?<!\.specify/)templates/', body), (
            f"Bare templates/ path found in '{f.relative_to(project)}' for agent '{agent}'"
        )


# ---------------------------------------------------------------------------
# 4. TOML format checks
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("agent", sorted(_TOML_AGENTS))
def test_toml_format_valid(agent, scaffolded_sh):
    """TOML agents: every command file must have description and prompt fields."""
    project = scaffolded_sh(agent)

    cmd_dir = _expected_cmd_dir(project, agent)
    for f in cmd_dir.glob("speckit.*.toml"):
        content = f.read_text(encoding="utf-8")
        assert 'description = "' in content, (
            f"Missing 'description' in '{f.name}' for agent '{agent}'"
        )
        assert 'prompt = """' in content, (
            f"Missing 'prompt' block in '{f.name}' for agent '{agent}'"
        )


# ---------------------------------------------------------------------------
# 5. Markdown frontmatter checks
# ---------------------------------------------------------------------------

_MARKDOWN_AGENTS = [a for a in _TESTABLE_AGENTS if a not in _TOML_AGENTS]


@pytest.mark.parametrize("agent", _MARKDOWN_AGENTS)
def test_markdown_has_frontmatter(agent, scaffolded_sh):
    """Markdown agents: every command file must start with valid YAML frontmatter."""
    project = scaffolded_sh(agent)

    cmd_dir = _expected_cmd_dir(project, agent)
    for f in _list_command_files(cmd_dir, agent):
        content = f.read_text(encoding="utf-8")
        assert content.startswith("---"), (
            f"No YAML frontmatter in '{f.name}' for agent '{agent}'"
        )
        parts = content.split("---", 2)
        assert len(parts) >= 3, f"Incomplete frontmatter in '{f.name}'"
        fm = yaml.safe_load(parts[1])
        assert fm is not None, f"Empty frontmatter in '{f.name}'"
        assert "description" in fm, (
            f"'description' key missing from frontmatter in '{f.name}' for agent '{agent}'"
        )


def test_forge_name_field_in_frontmatter(scaffolded_sh):
    """Forge: every command file must have a 'name' field in frontmatter that matches the filename.
    
    Forge requires both 'name' and 'description' fields in command frontmatter.
    This test ensures the release script's name injection is working correctly.
    """
    project = scaffolded_sh("forge")
    
    cmd_dir = _expected_cmd_dir(project, "forge")
    for f in _list_command_files(cmd_dir, "forge"):
        content = f.read_text(encoding="utf-8")
        assert content.startswith("---"), (
            f"No YAML frontmatter in '{f.name}'"
        )
        parts = content.split("---", 2)
        assert len(parts) >= 3, f"Incomplete frontmatter in '{f.name}'"
        fm = yaml.safe_load(parts[1])
        assert fm is not None, f"Empty frontmatter in '{f.name}'"
        
        # Check that 'name' field exists
        assert "name" in fm, (
            f"'name' key missing from frontmatter in '{f.name}' - "
            f"Forge requires both 'name' and 'description' fields"
        )
        
        # Check that name matches the filename (without extension)
        expected_name = f.name.removesuffix(".md")
        actual_name = fm["name"]
        assert actual_name == expected_name, (
            f"Frontmatter 'name' field ({actual_name}) does not match "
            f"filename ({expected_name}) in '{f.name}'"
        )


# ---------------------------------------------------------------------------
# 6. Copilot-specific: companion .prompt.md files
# ---------------------------------------------------------------------------

def test_copilot_companion_prompt_files(scaffolded_sh, source_template_stems):
    """Copilot: a speckit.<stem>.prompt.md companion is created for every .agent.md file."""
    project = scaffolded_sh("copilot")

    prompts_dir = project / ".github" / "prompts"
    assert prompts_dir.is_dir(), ".github/prompts/ not created for copilot"

    for stem in source_template_stems:
        prompt_file = prompts_dir / f"speckit.{stem}.prompt.md"
        assert prompt_file.is_file(), (
            f"Companion prompt file '{prompt_file.name}' missing for copilot"
        )


def test_copilot_prompt_file_content(scaffolded_sh, source_template_stems):
    """Copilot companion .prompt.md files must reference their parent .agent.md."""
    project = scaffolded_sh("copilot")

    prompts_dir = project / ".github" / "prompts"
    for stem in source_template_stems:
        f = prompts_dir / f"speckit.{stem}.prompt.md"
        content = f.read_text(encoding="utf-8")
        assert f"agent: speckit.{stem}" in content, (
            f"Companion '{f.name}' does not reference 'speckit.{stem}'"
        )


# ---------------------------------------------------------------------------
# 7. PowerShell script variant
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("agent", _TESTABLE_AGENTS)
def test_scaffold_powershell_variant(agent, scaffolded_ps, source_template_stems):
    """scaffold_from_core_pack with script_type='ps' creates correct files."""
    project = scaffolded_ps(agent)

    scripts_dir = project / ".specify" / "scripts" / "powershell"
    assert scripts_dir.is_dir(), f".specify/scripts/powershell/ missing for '{agent}'"
    assert any(scripts_dir.iterdir()), ".specify/scripts/powershell/ is empty"

    cmd_dir = _expected_cmd_dir(project, agent)
    generated = _list_command_files(cmd_dir, agent)
    assert len(generated) == len(source_template_stems)


# ---------------------------------------------------------------------------
# 8. Parity: bundled vs. real create-release-packages.sh ZIP
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def release_script_trees(tmp_path_factory):
    """Session-scoped cache: run release script once per (agent, script_type)."""
    cache: dict[tuple[str, str], dict[str, bytes]] = {}
    bash = _find_bash()

    def _get(agent: str, script_type: str) -> dict[str, bytes] | None:
        if bash is None:
            return None
        key = (agent, script_type)
        if key not in cache:
            tmp = tmp_path_factory.mktemp(f"release_{agent}_{script_type}")
            gen_dir = tmp / "genreleases"
            gen_dir.mkdir()
            zip_path = _run_release_script(agent, script_type, bash, gen_dir)
            extracted = tmp / "extracted"
            extracted.mkdir()
            with zipfile.ZipFile(zip_path) as zf:
                zf.extractall(extracted)
            cache[key] = _collect_relative_files(extracted)
        return cache[key]
    return _get


@pytest.mark.parametrize("script_type", ["sh", "ps"])
@pytest.mark.parametrize("agent", _TESTABLE_AGENTS)
def test_parity_bundled_vs_release_script(agent, script_type, scaffolded_sh, scaffolded_ps, release_script_trees):
    """scaffold_from_core_pack() file tree is identical to the ZIP produced by
    create-release-packages.sh for every agent and script type.

    This is the true end-to-end parity check: the Python offline path must
    produce exactly the same artifacts as the canonical shell release script.

    Both sides are session-cached: each agent/script_type combination is
    scaffolded and release-scripted only once across all tests.
    """
    script_tree = release_script_trees(agent, script_type)
    if script_tree is None:
        pytest.skip("bash required to run create-release-packages.sh")

    # Reuse session-cached scaffold output
    if script_type == "sh":
        bundled_dir = scaffolded_sh(agent)
    else:
        bundled_dir = scaffolded_ps(agent)

    bundled_tree = _collect_relative_files(bundled_dir)

    only_bundled = set(bundled_tree) - set(script_tree)
    only_script = set(script_tree) - set(bundled_tree)

    assert not only_bundled, (
        f"Agent '{agent}' ({script_type}): files only in bundled output (not in release ZIP):\n  "
        + "\n  ".join(sorted(only_bundled))
    )
    assert not only_script, (
        f"Agent '{agent}' ({script_type}): files only in release ZIP (not in bundled output):\n  "
        + "\n  ".join(sorted(only_script))
    )

    for name in bundled_tree:
        assert bundled_tree[name] == script_tree[name], (
            f"Agent '{agent}' ({script_type}): file '{name}' content differs between "
            f"bundled output and release script ZIP"
        )


# ---------------------------------------------------------------------------
# Section 10 – pyproject.toml force-include covers all template files
# ---------------------------------------------------------------------------

def test_pyproject_force_include_covers_all_templates():
    """Every file in templates/ (excluding commands/) must be listed in
    pyproject.toml's [tool.hatch.build.targets.wheel.force-include] section.

    This prevents new template files from being silently omitted from the
    wheel, which would break ``specify init --offline``.
    """
    templates_dir = _REPO_ROOT / "templates"
    # Collect all files directly in templates/ (not in subdirectories like commands/)
    repo_template_files = sorted(
        f.name for f in templates_dir.iterdir()
        if f.is_file()
    )
    assert repo_template_files, "Expected at least one template file in templates/"

    pyproject_path = _REPO_ROOT / "pyproject.toml"
    with open(pyproject_path, "rb") as f:
        pyproject = tomllib.load(f)
    force_include = pyproject.get("tool", {}).get("hatch", {}).get("build", {}).get("targets", {}).get("wheel", {}).get("force-include", {})

    missing = [
        name for name in repo_template_files
        if f"templates/{name}" not in force_include
    ]
    assert not missing, (
        "Template files not listed in pyproject.toml force-include "
        "(offline scaffolding will miss them):\n  "
        + "\n  ".join(missing)
    )
