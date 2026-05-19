"""Tests for CursorAgentIntegration."""

from pathlib import Path

from specify_cli.integrations import get_integration
from specify_cli.integrations.manifest import IntegrationManifest

from .test_integration_base_skills import SkillsIntegrationTests


class TestCursorAgentIntegration(SkillsIntegrationTests):
    KEY = "cursor-agent"
    FOLDER = ".cursor/"
    COMMANDS_SUBDIR = "skills"
    REGISTRAR_DIR = ".cursor/skills"
    CONTEXT_FILE = ".cursor/rules/specify-rules.mdc"


class TestCursorMdcFrontmatter:
    """Verify .mdc frontmatter handling in upsert/remove context section."""

    def _setup(self, tmp_path: Path):
        i = get_integration("cursor-agent")
        m = IntegrationManifest("cursor-agent", tmp_path)
        return i, m

    def test_new_mdc_gets_frontmatter(self, tmp_path):
        """A freshly created .mdc file includes alwaysApply: true."""
        i, m = self._setup(tmp_path)
        i.setup(tmp_path, m)
        ctx = (tmp_path / i.context_file).read_text(encoding="utf-8")
        assert ctx.startswith("---\n")
        assert "alwaysApply: true" in ctx

    def test_existing_mdc_without_frontmatter_gets_it(self, tmp_path):
        """An existing .mdc without frontmatter gets it added."""
        i, m = self._setup(tmp_path)
        ctx_path = tmp_path / i.context_file
        ctx_path.parent.mkdir(parents=True, exist_ok=True)
        ctx_path.write_text("# User rules\n", encoding="utf-8")
        i.upsert_context_section(tmp_path)
        content = ctx_path.read_text(encoding="utf-8")
        assert content.lstrip().startswith("---")
        assert "alwaysApply: true" in content
        assert "# User rules" in content

    def test_existing_mdc_with_frontmatter_preserves_it(self, tmp_path):
        """An existing .mdc with custom frontmatter is preserved."""
        i, m = self._setup(tmp_path)
        ctx_path = tmp_path / i.context_file
        ctx_path.parent.mkdir(parents=True, exist_ok=True)
        ctx_path.write_text(
            "---\nalwaysApply: true\ncustomKey: hello\n---\n\n# Rules\n",
            encoding="utf-8",
        )
        i.upsert_context_section(tmp_path)
        content = ctx_path.read_text(encoding="utf-8")
        assert "alwaysApply: true" in content
        assert "customKey: hello" in content
        assert "<!-- SPECKIT START -->" in content

    def test_existing_mdc_wrong_alwaysapply_fixed(self, tmp_path):
        """An .mdc with alwaysApply: false gets corrected."""
        i, m = self._setup(tmp_path)
        ctx_path = tmp_path / i.context_file
        ctx_path.parent.mkdir(parents=True, exist_ok=True)
        ctx_path.write_text(
            "---\nalwaysApply: false\n---\n\n# Rules\n",
            encoding="utf-8",
        )
        i.upsert_context_section(tmp_path)
        content = ctx_path.read_text(encoding="utf-8")
        assert "alwaysApply: true" in content
        assert "alwaysApply: false" not in content

    def test_upsert_idempotent_no_duplicate_frontmatter(self, tmp_path):
        """Repeated upserts don't duplicate frontmatter."""
        i, m = self._setup(tmp_path)
        i.upsert_context_section(tmp_path)
        i.upsert_context_section(tmp_path)
        content = (tmp_path / i.context_file).read_text(encoding="utf-8")
        assert content.count("alwaysApply") == 1

    def test_remove_deletes_mdc_with_only_frontmatter(self, tmp_path):
        """Removing the section from a Speckit-only .mdc deletes the file."""
        i, m = self._setup(tmp_path)
        i.upsert_context_section(tmp_path)
        ctx_path = tmp_path / i.context_file
        assert ctx_path.exists()
        i.remove_context_section(tmp_path)
        assert not ctx_path.exists()


class TestCursorAgentAutoPromote:
    """--ai cursor-agent auto-promotes to integration path."""

    def test_ai_cursor_agent_without_ai_skills_auto_promotes(self, tmp_path):
        """--ai cursor-agent should work the same as --integration cursor-agent."""
        from typer.testing import CliRunner
        from specify_cli import app

        runner = CliRunner()
        target = tmp_path / "test-proj"
        result = runner.invoke(app, ["init", str(target), "--ai", "cursor-agent", "--no-git", "--ignore-agent-tools", "--script", "sh"])

        assert result.exit_code == 0, f"init --ai cursor-agent failed: {result.output}"
        assert (target / ".cursor" / "skills" / "speckit-plan" / "SKILL.md").exists()


class TestCursorAgentCliDispatch:
    """Verify the CLI dispatch path for cursor-agent (issue #2629).

    The ``cursor-agent`` CLI supports headless execution via ``-p`` (with
    full tool access including write/shell) and requires ``--trust`` to
    bypass the Workspace Trust prompt.  These tests pin the exact argv
    shape that the workflow runner will use.
    """

    def test_requires_cli_is_true(self):
        i = get_integration("cursor-agent")
        assert i.config.get("requires_cli") is True

    def test_install_url_is_set(self):
        i = get_integration("cursor-agent")
        url = i.config.get("install_url")
        assert url is not None
        assert "cursor.com" in url

    def test_build_exec_args_default_includes_headless_flags_and_json(self):
        """Default argv emits the full headless flag set: -p --trust
        --approve-mcps --force, then prompt, then --output-format json.
        """
        i = get_integration("cursor-agent")
        args = i.build_exec_args("/speckit-specify some-feature")
        assert args == [
            "cursor-agent", "-p", "--trust", "--approve-mcps", "--force",
            "/speckit-specify some-feature",
            "--output-format", "json",
        ]

    def test_build_exec_args_text_output_omits_format(self):
        i = get_integration("cursor-agent")
        args = i.build_exec_args("/speckit-plan", output_json=False)
        assert args == [
            "cursor-agent", "-p", "--trust", "--approve-mcps", "--force",
            "/speckit-plan",
        ]

    def test_build_exec_args_with_model(self):
        i = get_integration("cursor-agent")
        args = i.build_exec_args(
            "/speckit-specify", model="sonnet-4-thinking", output_json=False
        )
        assert args == [
            "cursor-agent", "-p", "--trust", "--approve-mcps", "--force",
            "/speckit-specify",
            "--model", "sonnet-4-thinking",
        ]

    def test_build_exec_args_contains_mandatory_headless_flags(self):
        """The four headless flags must always appear together.

        ``--approve-mcps`` is required so MCP servers (e.g. dingtalk-doc)
        actually load in headless mode; ``--force`` is required so the
        agent doesn't block on tool-call approval prompts during the
        speckit workflow.  Together with ``-p`` and ``--trust`` they
        bring cursor-agent's headless behaviour in line with
        ``claude -p`` / ``codex --exec`` from spec-kit's perspective.
        """
        i = get_integration("cursor-agent")
        args = i.build_exec_args("/speckit-implement", output_json=False)
        for flag in ("-p", "--trust", "--approve-mcps", "--force"):
            assert flag in args, f"missing mandatory headless flag: {flag}"

    def test_build_command_invocation_uses_hyphenated_skill_name(self):
        """SkillsIntegration: /speckit-plan (not /speckit.plan)."""
        i = get_integration("cursor-agent")
        assert i.build_command_invocation("speckit.plan", "feature-x") == "/speckit-plan feature-x"
        assert i.build_command_invocation("plan") == "/speckit-plan"

    def test_dispatch_command_resolves_cmd_shim_for_subprocess(self):
        """``.cmd`` shims must be resolved to their full path before ``subprocess.run``.

        ``cursor-agent`` (and other npm-installed CLIs on Windows) ship as
        ``cursor-agent.cmd`` wrappers.  ``shutil.which`` honors ``PATHEXT``
        and finds them, but Python's ``subprocess.run`` calls
        ``CreateProcess`` which does **not** consult ``PATHEXT`` and fails
        with ``WinError 2`` on a bare ``["cursor-agent", ...]`` argv.  The
        fix in ``base.py::dispatch_command`` resolves ``exec_args[0]`` via
        ``shutil.which`` so the full ``.cmd`` path is what reaches
        ``CreateProcess``.
        """
        from unittest.mock import patch, MagicMock
        i = get_integration("cursor-agent")

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "ok"
        mock_result.stderr = ""

        fake_path = r"C:\Users\foo\AppData\Local\cursor-agent\cursor-agent.CMD"
        with patch(
            "specify_cli.integrations.base.shutil.which", return_value=fake_path
        ), patch("subprocess.run", return_value=mock_result) as mock_run:
            result = i.dispatch_command(
                "speckit.plan", args="feature-x", stream=False, timeout=5
            )

        assert result["exit_code"] == 0
        argv = mock_run.call_args[0][0]
        assert argv[0] == fake_path, f"expected resolved .CMD path, got: {argv[0]!r}"
        assert argv[1:6] == ["-p", "--trust", "--approve-mcps", "--force", "/speckit-plan feature-x"]

    def test_dispatch_command_passthrough_when_shutil_which_finds_nothing(self):
        """If ``shutil.which`` returns ``None``, leave argv unchanged so the
        existing ``FileNotFoundError`` path remains observable to callers."""
        from unittest.mock import patch, MagicMock
        i = get_integration("cursor-agent")

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        mock_result.stderr = ""

        with patch(
            "specify_cli.integrations.base.shutil.which", return_value=None
        ), patch("subprocess.run", return_value=mock_result) as mock_run:
            i.dispatch_command("speckit.plan", stream=False, timeout=5)

        argv = mock_run.call_args[0][0]
        assert argv[0] == "cursor-agent"

