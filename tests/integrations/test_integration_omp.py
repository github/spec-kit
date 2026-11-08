"""Tests for OmpIntegration."""

import pytest

from specify_cli.integrations import get_integration

from .test_integration_base_markdown import MarkdownIntegrationTests


class TestOmpIntegration(MarkdownIntegrationTests):
    KEY = "omp"
    FOLDER = ".omp/"
    COMMANDS_SUBDIR = "commands"
    REGISTRAR_DIR = ".omp/commands"

    def test_multi_install_safe(self):
        # Omp writes only to its isolated, static root .omp/commands, disjoint
        # from every other integration, so it must be co-install safe (mirrors
        # qwen/shai/qodercli and the kiro-cli #3471 precedent).
        assert get_integration(self.KEY).multi_install_safe is True

    def test_build_exec_args_uses_omp_json_mode(self):
        i = get_integration(self.KEY)

        args = i.build_exec_args(
            "/speckit.specify Build auth",
            model="gpt-5",
        )

        assert args == [
            "omp",
            "--print",
            "--model",
            "gpt-5",
            "--mode",
            "json",
            "/speckit.specify Build auth",
        ]

    def test_build_exec_args_passes_integration_args_and_options(self, monkeypatch):
        monkeypatch.delenv("SPECKIT_INTEGRATION_OMP_EXECUTABLE", raising=False)
        monkeypatch.delenv("SPECKIT_INTEGRATION_OMP_EXTRA_ARGS", raising=False)

        args = get_integration(self.KEY).build_exec_args(
            "/speckit.plan",
            model="gpt-5",
            integration_args=["--no-session", "--yolo"],
            integration_options={
                "profile": "work",
                "thinking": "high",
                "tools": "read,bash",
            },
        )

        assert args == [
            "omp",
            "--print",
            "--no-session",
            "--yolo",
            "--profile",
            "work",
            "--thinking",
            "high",
            "--tools",
            "read,bash",
            "--model",
            "gpt-5",
            "--mode",
            "json",
            "/speckit.plan",
        ]

    def test_build_exec_args_places_integration_args_after_env_extra_args(
        self, monkeypatch
    ):
        monkeypatch.delenv("SPECKIT_INTEGRATION_OMP_EXECUTABLE", raising=False)
        monkeypatch.setenv("SPECKIT_INTEGRATION_OMP_EXTRA_ARGS", "--from-env")

        args = get_integration(self.KEY).build_exec_args(
            "prompt",
            output_json=False,
            integration_args=["--no-title"],
            integration_options={"thinking": "low"},
        )

        assert args == [
            "omp",
            "--print",
            "--from-env",
            "--no-title",
            "--thinking",
            "low",
            "--mode",
            "text",
            "prompt",
        ]

    @pytest.mark.parametrize(
        "thinking",
        ["off", "minimal", "low", "medium", "high", "xhigh", "max", "auto"],
    )
    def test_validate_runtime_config_accepts_thinking_levels(self, thinking):
        get_integration(self.KEY).validate_runtime_config(
            None, {"thinking": thinking}
        )

    @pytest.mark.parametrize(
        ("integration_args", "integration_options"),
        [(None, None), ([], {}), (["--no-session"], {"profile": "work"})],
    )
    def test_validate_runtime_config_accepts_valid_config(
        self, integration_args, integration_options
    ):
        get_integration(self.KEY).validate_runtime_config(
            integration_args, integration_options
        )

    @pytest.mark.parametrize("integration_args", [[""], ["   "], [42], ["--ok", None]])
    def test_integration_args_reject_malformed_values(self, integration_args):
        with pytest.raises(ValueError, match="non-empty strings"):
            get_integration(self.KEY).build_exec_args(
                "prompt",
                integration_args=integration_args,
            )

    @pytest.mark.parametrize(
        "integration_args",
        [["--model", "gpt-5"], ["--model=gpt-5"], ["--no-session", "--model", "gpt-5"]],
    )
    def test_integration_args_model_flag_is_rejected(self, integration_args):
        with pytest.raises(ValueError, match="command-step 'model' field"):
            get_integration(self.KEY).build_exec_args(
                "prompt",
                integration_args=integration_args,
            )

    @pytest.mark.parametrize(
        "integration_args", [["--"], ["--no-session", "--"], ["--", "extra"]]
    )
    def test_integration_args_option_terminator_is_rejected(self, integration_args):
        with pytest.raises(ValueError, match="option terminator"):
            get_integration(self.KEY).build_exec_args(
                "prompt",
                integration_args=integration_args,
            )

    @pytest.mark.parametrize(
        "integration_args",
        [
            ["--="],
            ["--=x"],
            ["--system-prompt"],
            ["--resume"],
            ["--models", "a,b"],
            ["positional"],
            ["@file.md"],
            ["-"],
            ["-r"],
            ["--help"],
            ["--print"],
            ["--help=false"],
            ["--version=false"],
            ["--print=false"],
            ["--help="],
            ["--export=session.jsonl"],
            ["--alias=omp-work"],
            ["--mode=rpc"],
        ],
    )
    def test_integration_args_unsafe_tokens_are_rejected(self, integration_args):
        with pytest.raises(ValueError, match="not allowed"):
            get_integration(self.KEY).build_exec_args(
                "prompt", integration_args=integration_args
            )

    @pytest.mark.parametrize(
        "integration_args",
        [
            ["--yolo=false"],
            ["--auto-approve=false"],
            ["--auto-approve=0"],
            ["--yolo="],
            ["--plan-yolo=false"],
            ["--no-session=false"],
        ],
    )
    def test_integration_args_valueless_flag_with_inline_value_is_rejected(
        self, integration_args
    ):
        """OMP enables a boolean flag regardless of an inline ``=value``.

        ``--yolo=false`` would silently turn on auto-approval, so every
        equals-form of a known valueless flag is rejected.
        """
        with pytest.raises(ValueError, match="does not take a value"):
            get_integration(self.KEY).build_exec_args(
                "prompt", integration_args=integration_args
            )

    @pytest.mark.parametrize(
        "integration_args", [["--yolo"], ["--auto-approve"], ["--plan-yolo"]]
    )
    def test_integration_args_bare_approval_flags_are_accepted(
        self, integration_args
    ):
        args = get_integration(self.KEY).build_exec_args(
            "prompt", integration_args=integration_args
        )
        assert integration_args[0] in args

    @pytest.mark.parametrize(
        "integration_args",
        [
            ["--no-session", "--yolo"],
            ["--system-prompt=be brief"],
            ["--resume=abc123"],
            ["--models=a,b", "--no-title"],
        ],
    )
    @pytest.mark.parametrize("output_json", [True, False])
    def test_integration_args_preserve_omp_parsing(
        self, monkeypatch, integration_args, output_json
    ):
        """Replay OMP's parseArgs semantics over the generated argv.

        Mirrors args.ts/flag-tables.ts (can1357/oh-my-pi): ``--x=v`` is split
        into ``--x v``, string flags consume the next token even if
        flag-looking, optional-value flags consume the next non-dash token,
        and ``--`` ends option parsing.
        """
        monkeypatch.delenv("SPECKIT_INTEGRATION_OMP_EXECUTABLE", raising=False)
        monkeypatch.delenv("SPECKIT_INTEGRATION_OMP_EXTRA_ARGS", raising=False)
        argv = get_integration(self.KEY).build_exec_args(
            "the prompt",
            model="gpt-5",
            output_json=output_json,
            integration_args=integration_args,
            integration_options={"thinking": "high"},
        )
        parsed = _parse_omp_args(argv[1:])
        assert parsed["messages"] == ["the prompt"]
        assert parsed["model"] == "gpt-5"
        assert parsed["thinking"] == "high"
        assert parsed["print"] is True
        assert parsed.get("mode") == ("json" if output_json else "text")

    def test_replayed_parser_shows_why_bare_flags_are_unsafe(self):
        # Sanity-check the model against the cases from the PR review.
        assert _parse_omp_args(["--print", "--=", "--model", "m", "p"])[
            "messages"
        ] == ["--model", "m", "p"]
        assert _parse_omp_args(["--system-prompt", "--mode", "json", "p"])[
            "system-prompt"
        ] == "--mode"
        assert _parse_omp_args(["--resume", "p"])["messages"] == []

    def test_integration_args_allow_models_cycling_flag(self):
        # `--models` only scopes Ctrl+P cycling; it does not select the model.
        get_integration(self.KEY).validate_runtime_config(
            ["--models=claude-sonnet,gpt-5"], None
        )

    def test_integration_options_model_is_rejected(self):
        with pytest.raises(ValueError, match="command-step 'model' field"):
            get_integration(self.KEY).build_exec_args(
                "prompt",
                integration_options={"model": "gpt-5"},
            )

    @pytest.mark.parametrize(
        ("options", "message"),
        [
            ({1: "value"}, "keys must be strings"),
            ({"unknown": "value"}, r"unknown integration option\(s\): 'unknown'"),
            ({"profile": ""}, "'profile' must be a non-empty string"),
            ({"tools": "   "}, "'tools' must be a non-empty string"),
            ({"profile": 42}, "'profile' must be a non-empty string"),
            ({"thinking": "extreme"}, "'thinking' must be one of"),
        ],
    )
    def test_integration_options_are_validated(self, options, message):
        with pytest.raises(ValueError, match=message):
            get_integration(self.KEY).build_exec_args(
                "prompt",
                integration_options=options,
            )


_STRING_FLAGS = {
    "--system-prompt", "--model", "--mode", "--thinking", "--tools",
    "--models", "--profile", "--alias", "--append-system-prompt", "--cwd",
}
_OPTIONAL_FLAGS = {"--resume", "-r", "--restore", "--session"}


def _parse_omp_args(argv):
    """Minimal replay of OMP's ``parseArgs`` for the flags this adapter emits."""
    args = list(argv)
    result = {"messages": [], "print": False}
    separator = False
    i = 0
    while i < len(args):
        arg = args[i]
        if separator:
            result["messages"].append(arg)
            i += 1
            continue
        eq_index = -1
        if arg.startswith("--") and "=" in arg:
            name, _, value = arg.partition("=")
            arg = name
            args.insert(i + 1, value)
            eq_index = i + 1
        start = i
        if arg in _STRING_FLAGS:
            if i + 1 < len(args):
                i += 1
                result[arg[2:]] = args[i]
        elif arg in _OPTIONAL_FLAGS:
            nxt = args[i + 1] if i + 1 < len(args) else None
            if nxt is not None and not nxt.startswith("-") and nxt != "":
                i += 1
                result[arg.lstrip("-")] = args[i]
        elif arg in ("--print", "-p"):
            result["print"] = True
        elif arg == "--":
            separator = True
        elif arg.startswith("@") or not arg.startswith("-") or arg == "-":
            if not arg.startswith("@"):
                result["messages"].append(arg)
        if eq_index != -1 and i == start:
            del args[eq_index]
        i += 1
    return result
