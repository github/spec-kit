"""
Integration tests: install a real extension into a temp project and verify
that generated SKILL.md files have correct .specify/extensions/<id>/… paths
instead of bare extension-relative references.

Set the SPECKIT_TEST_EXT_DIR environment variable to the path of a local
extension checkout before running. Tests are skipped automatically when
the variable is not set or the directory does not exist.

Example:
    SPECKIT_TEST_EXT_DIR=~/work/my-extension pytest tests/test_integration_foobar_extension.py
"""

import json
import os
import re
import shutil
import tempfile
from pathlib import Path

import pytest

_ext_dir_env = os.environ.get("SPECKIT_TEST_EXT_DIR", "")
EXT_DIR = Path(_ext_dir_env).expanduser().resolve() if _ext_dir_env else None

pytestmark = pytest.mark.skipif(
    EXT_DIR is None or not EXT_DIR.exists(),
    reason="Set SPECKIT_TEST_EXT_DIR to an extension checkout to run these tests",
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _ext_id() -> str:
    """Read the extension id from the manifest."""
    from specify_cli.extensions import ExtensionManifest
    return ExtensionManifest(EXT_DIR / "extension.yml").id


def _make_project(tmp: Path, ai: str = "codex") -> Path:
    """Create a minimal spec-kit project structure for *ai*."""
    project = tmp / "project"
    project.mkdir()
    specify = project / ".specify"
    specify.mkdir()

    (specify / "init-options.json").write_text(
        json.dumps({"ai": ai, "ai_skills": True, "script": "sh"})
    )

    if ai == "codex":
        (project / ".agents" / "skills").mkdir(parents=True)
    elif ai == "kimi":
        (project / ".kimi" / "skills").mkdir(parents=True)

    return project


def _install_ext(project: Path) -> None:
    from specify_cli.extensions import ExtensionManager
    try:
        from importlib.metadata import version
        speckit_version = version("specify-cli")
    except Exception:
        speckit_version = "999.0.0"
    ExtensionManager(project).install_from_directory(EXT_DIR, speckit_version, register_commands=True)


def _skill_files(project: Path, ext_id: str, ai: str = "codex") -> dict[str, Path]:
    """Return {skill_name: SKILL.md path} for all skills belonging to the extension."""
    if ai == "codex":
        skills_root = project / ".agents" / "skills"
    else:
        skills_root = project / ".kimi" / "skills"

    return {
        p.parent.name: p
        for p in skills_root.glob("*/SKILL.md")
        if ext_id in p.parent.name
    }


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def ext_id():
    return _ext_id()


@pytest.fixture
def tmp_dir():
    d = tempfile.mkdtemp()
    yield Path(d)
    shutil.rmtree(d)


@pytest.fixture
def codex_project(tmp_dir):
    project = _make_project(tmp_dir, ai="codex")
    _install_ext(project)
    return project


@pytest.fixture
def kimi_project(tmp_dir):
    project = _make_project(tmp_dir, ai="kimi")
    _install_ext(project)
    return project


# ---------------------------------------------------------------------------
# Extension installation sanity
# ---------------------------------------------------------------------------

class TestExtensionInstallation:

    def test_extension_files_copied_to_specify_dir(self, codex_project, ext_id):
        """Extension source should be copied under .specify/extensions/<id>/."""
        installed = codex_project / ".specify" / "extensions" / ext_id
        assert installed.is_dir(), f"Extension directory not created at {installed}"
        assert (installed / "extension.yml").exists()

    def test_agent_subdirectory_installed(self, codex_project, ext_id):
        """At least one subdirectory referenced by commands should be present."""
        installed = codex_project / ".specify" / "extensions" / ext_id
        subdirs = [d.name for d in installed.iterdir() if d.is_dir()]
        assert subdirs, f"No subdirectories found under installed extension at {installed}"

    def test_all_commands_produce_skill_files(self, codex_project, ext_id):
        """Every command declared in extension.yml should produce a SKILL.md."""
        from specify_cli.extensions import ExtensionManifest
        manifest = ExtensionManifest(
            codex_project / ".specify" / "extensions" / ext_id / "extension.yml"
        )
        skill_files = _skill_files(codex_project, ext_id, ai="codex")

        for cmd in manifest.commands:
            short = cmd["name"].removeprefix("speckit.")
            skill_name = f"speckit-{short}"
            assert skill_name in skill_files, (
                f"Expected SKILL.md for '{cmd['name']}' at '{skill_name}' — not found.\n"
                f"Available: {sorted(skill_files)}"
            )

    def test_registry_records_installed_extension(self, codex_project, ext_id):
        """Extension registry should record the extension as installed."""
        from specify_cli.extensions import ExtensionManager
        manager = ExtensionManager(codex_project)
        assert manager.registry.is_installed(ext_id), f"{ext_id} not recorded in registry"


# ---------------------------------------------------------------------------
# Path rewriting — core regression tests
# ---------------------------------------------------------------------------

class TestSkillPathRewriting:
    """Verify that .specify/extensions/<id>/… paths appear in generated SKILL.md files."""

    def _first_skill(self, codex_project: Path, ext_id: str) -> str:
        skill_files = _skill_files(codex_project, ext_id, ai="codex")
        assert skill_files, f"No skill files found for extension {ext_id}"
        # Prefer a 'run' command if present, otherwise take the first one
        key = next((k for k in skill_files if k.endswith(".run") or k.endswith("-run")), None)
        key = key or next(iter(skill_files))
        return skill_files[key].read_text()

    def test_skill_contains_extension_prefix_for_installed_subdirs(self, codex_project, ext_id):
        """Any subdirectory that exists in the installed extension should appear
        as .specify/extensions/<id>/<subdir>/ in at least one skill file."""
        installed = codex_project / ".specify" / "extensions" / ext_id
        skill_files = _skill_files(codex_project, ext_id, ai="codex")
        all_content = "\n".join(p.read_text() for p in skill_files.values())

        prefix = f".specify/extensions/{ext_id}/"
        installed_subdirs = [d.name for d in installed.iterdir() if d.is_dir() and d.name != "commands"]

        rewritten = [s for s in installed_subdirs if f"{prefix}{s}/" in all_content]
        assert rewritten, (
            f"Expected at least one installed subdirectory to appear as {prefix}<subdir>/ "
            f"in skill files.\nInstalled subdirs: {installed_subdirs}\n"
            f"Prefix searched: {prefix}"
        )

    def test_no_bare_subdir_paths_for_installed_subdirs(self, codex_project, ext_id):
        """For each installed subdirectory, no bare '<subdir>/…' references should
        remain after rewriting (only the prefixed form is acceptable)."""
        installed = codex_project / ".specify" / "extensions" / ext_id
        skill_files = _skill_files(codex_project, ext_id, ai="codex")
        prefix = f".specify/extensions/{ext_id}/"

        installed_subdirs = [d.name for d in installed.iterdir() if d.is_dir() and d.name != "commands"]
        failures = []

        for subdir in installed_subdirs:
            escaped = re.escape(subdir)
            for name, path in skill_files.items():
                content = path.read_text()
                # Strip all correctly-prefixed occurrences first
                stripped = content.replace(f"{prefix}{subdir}/", "__OK__")
                bare = re.findall(
                    r'(?:^|[\s`"\'(])(?:\.?/)?' + escaped + r'/',
                    stripped,
                    re.MULTILINE,
                )
                if bare:
                    failures.append(f"{name}: bare '{subdir}/' references: {bare}")

        assert not failures, "Bare subdirectory references found:\n" + "\n".join(failures)

    def test_all_skills_contain_no_bare_subdir_paths(self, codex_project, ext_id):
        """Comprehensive check across all skill files for all installed subdirs."""
        installed = codex_project / ".specify" / "extensions" / ext_id
        skill_files = _skill_files(codex_project, ext_id, ai="codex")
        prefix = f".specify/extensions/{ext_id}/"

        installed_subdirs = [d.name for d in installed.iterdir() if d.is_dir() and d.name != "commands"]
        failures = []

        for name, path in skill_files.items():
            content = path.read_text()
            for subdir in installed_subdirs:
                stripped = content.replace(f"{prefix}{subdir}/", "__OK__")
                bare = re.findall(
                    r'(?:^|[\s`"\'(])(?:\.?/)?' + re.escape(subdir) + r'/',
                    stripped,
                    re.MULTILINE,
                )
                if bare:
                    failures.append(f"{name}: bare '{subdir}/': {bare}")

        assert not failures, "Bare subdirectory references found:\n" + "\n".join(failures)


# ---------------------------------------------------------------------------
# Kimi agent
# ---------------------------------------------------------------------------

class TestSkillPathRewritingKimi:

    def test_kimi_skills_contain_extension_prefix(self, kimi_project, ext_id):
        """Kimi skills should also have extension-relative paths rewritten."""
        installed = kimi_project / ".specify" / "extensions" / ext_id
        skill_files = _skill_files(kimi_project, ext_id, ai="kimi")
        assert skill_files, f"No kimi skill files found for extension {ext_id}"

        prefix = f".specify/extensions/{ext_id}/"
        installed_subdirs = [d.name for d in installed.iterdir() if d.is_dir() and d.name != "commands"]
        all_content = "\n".join(p.read_text() for p in skill_files.values())

        rewritten = [s for s in installed_subdirs if f"{prefix}{s}/" in all_content]
        assert rewritten, (
            f"No installed subdirectory appeared as {prefix}<subdir>/ in kimi skill files.\n"
            f"Installed subdirs: {installed_subdirs}"
        )


# ---------------------------------------------------------------------------
# Script placeholder integration
# ---------------------------------------------------------------------------

class TestScriptPlaceholders:

    def test_no_unresolved_script_placeholders(self, codex_project, ext_id):
        """No {SCRIPT} / {AGENT_SCRIPT} / {ARGS} placeholders should survive."""
        skill_files = _skill_files(codex_project, ext_id, ai="codex")
        failures = []
        for name, path in skill_files.items():
            content = path.read_text()
            for placeholder in ("{SCRIPT}", "{AGENT_SCRIPT}", "{ARGS}"):
                if placeholder in content:
                    failures.append(f"{name}: contains {placeholder}")
        assert not failures, "Unresolved placeholders found:\n" + "\n".join(failures)
