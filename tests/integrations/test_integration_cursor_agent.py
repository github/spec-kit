"""Tests for CursorAgentIntegration."""

from urllib.parse import urlparse

from specify_cli.integrations import get_integration

from .test_integration_base_skills import SkillsIntegrationTests


class TestCursorAgentIntegration(SkillsIntegrationTests):
    KEY = "cursor-agent"
    FOLDER = ".cursor/"
    COMMANDS_SUBDIR = "skills"
    REGISTRAR_DIR = ".cursor/skills"


class TestCursorAgentInitFlow:
    """--integration cursor-agent creates expected files."""

    def test_integration_cursor_agent_creates_skills(self, tmp_path):
        """--integration cursor-agent should create skills in .cursor/skills."""
        from typer.testing import CliRunner
        from specify_cli import app

        runner = CliRunner()
        target = tmp_path / "test-proj"
        result = runner.invoke(app, ["init", str(target), "--integration", "cursor-agent", "--ignore-agent-tools", "--script", "sh"])

        assert result.exit_code == 0, f"init --integration cursor-agent failed: {result.output}"
        assert (target / ".cursor" / "skills" / "speckit-plan" / "SKILL.md").exists()


class TestCursorAgentCliDispatch:
    """Verify the CLI dispatch path for cursor-agent (issue #2629).

    The ``cursor-agent`` CLI supports headless execution via ``-p`` (with
    full tool access including write/shell) and requires ``--trust`` to
    bypass the Workspace Trust prompt.  These tests pin the exact argv
    shape that the workflow runner will use.
    """

    def test_requires_cli_is_false_for_ide_first_flow(self):
        """``requires_cli`` must stay False so the IDE-only flow keeps working.

        ``specify init --integration cursor-agent`` (without ``--ignore-agent-tools``)
        treats ``requires_cli=True`` as a hard precheck and fails when the
        ``cursor-agent`` CLI isn't on PATH — even though the Cursor IDE
        / skills flow can run without it.  Workflow dispatch support is
        signalled by overriding ``build_exec_args()`` instead, mirroring
        ``CopilotIntegration``.
        """
        i = get_integration("cursor-agent")
        assert i.config.get("requires_cli") is False

    def test_install_url_is_set(self):
        i = get_integration("cursor-agent")
        url = i.config.get("install_url")
        assert url is not None
        # CodeQL: use a hostname comparison instead of a substring check
        # to avoid the "Incomplete URL substring sanitization" warning
        # (substring "cursor.com" can also appear in attacker-controlled
        # positions of an arbitrary URL).
        host = (urlparse(url).hostname or "").lower()
        assert host == "cursor.com" or host.endswith(".cursor.com")

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

    def test_build_exec_args_supports_dispatch_without_requires_cli(self):
        """``build_exec_args`` must return argv even though ``requires_cli``
        is ``False``.

        ``CursorAgentIntegration`` opts out of the ``requires_cli`` hard
        precheck (so ``specify init`` doesn't fail when the CLI isn't on
        PATH) but still supports workflow dispatch.  The presence of a
        non-``None`` argv from ``build_exec_args()`` is what the engine
        keys off — pin that invariant.
        """
        i = get_integration("cursor-agent")
        assert i.config.get("requires_cli") is False
        argv = i.build_exec_args("/speckit-plan", output_json=False)
        assert argv is not None
        assert argv[0] == "cursor-agent"

    def test_build_exec_args_honors_executable_override(self, monkeypatch):
        """``SPECKIT_INTEGRATION_CURSOR_AGENT_EXECUTABLE`` overrides argv[0].

        Every other CLI-dispatch integration (codex, devin, ...) routes
        argv[0] through ``_resolve_executable()`` so operators can pin a
        binary path (issue #2596). cursor-agent hardcoded ``self.key`` and
        silently ignored the documented override.
        """
        monkeypatch.setenv(
            "SPECKIT_INTEGRATION_CURSOR_AGENT_EXECUTABLE", "/custom/cursor"
        )
        i = get_integration("cursor-agent")
        args = i.build_exec_args("/speckit-plan", output_json=False)
        assert args[0] == "/custom/cursor"
        # The mandatory headless flags must still be present.
        for flag in ("-p", "--trust", "--approve-mcps", "--force"):
            assert flag in args

    def test_build_exec_args_honors_extra_args_override(self, monkeypatch):
        """``SPECKIT_INTEGRATION_CURSOR_AGENT_EXTRA_ARGS`` flags are injected
        *before* Spec Kit's canonical ``--model`` / ``--output-format`` flags.

        The ``_apply_extra_args_env_var()`` hook (issue #2595) was never
        invoked by cursor-agent, so operator-supplied flags were dropped.
        Insertion order is the real contract: extra args must land after the
        mandatory headless flags but before ``--model`` / ``--output-format``,
        so they cannot clobber, displace, or reorder Spec Kit's canonical
        trailing flags. Exercise with both a model and JSON output so both
        canonical flags are present to pin against.
        """
        monkeypatch.setenv(
            "SPECKIT_INTEGRATION_CURSOR_AGENT_EXTRA_ARGS", "--foo bar"
        )
        i = get_integration("cursor-agent")
        args = i.build_exec_args(
            "/speckit-plan", model="sonnet-4-thinking", output_json=True
        )
        assert "--foo" in args
        assert "bar" in args
        # "bar" is the value of "--foo": the tokens stay adjacent and in order.
        assert args.index("bar") == args.index("--foo") + 1
        # Extra args are inserted before the canonical flags, so they cannot
        # clobber or reorder them (the behavioral contract this test guards).
        assert args.index("--foo") < args.index("--model")
        assert args.index("--foo") < args.index("--output-format")
        # The canonical flags themselves remain intact and correctly paired.
        assert args[args.index("--model") + 1] == "sonnet-4-thinking"
        assert args[args.index("--output-format") + 1] == "json"

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

