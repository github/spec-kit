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
            integration_args=["--no-session", "--verbose"],
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
            "--verbose",
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
            integration_args=["--per-step"],
            integration_options={"thinking": "low"},
        )

        assert args == [
            "omp",
            "--print",
            "--from-env",
            "--per-step",
            "--thinking",
            "low",
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
