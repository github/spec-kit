"""Reusable test mixin for standard TomlIntegration subclasses.

Each per-agent test file sets ``KEY``, ``FOLDER``, ``COMMANDS_SUBDIR``,
``REGISTRAR_DIR``, and ``CONTEXT_FILE``, then inherits all verification
logic from ``TomlIntegrationTests``.

Mirrors ``MarkdownIntegrationTests`` closely — same test structure,
adapted for TOML output format.
"""

import os
import tomllib

import pytest

from specify_cli.integrations import INTEGRATION_REGISTRY, get_integration
from specify_cli.integrations.base import TomlIntegration
from specify_cli.integrations.manifest import IntegrationManifest


class TomlIntegrationTests:
    """Mixin — set class-level constants and inherit these tests.

    Required class attrs on subclass::

        KEY: str              — integration registry key
        FOLDER: str           — e.g. ".gemini/"
        COMMANDS_SUBDIR: str  — e.g. "commands"
        REGISTRAR_DIR: str    — e.g. ".gemini/commands"
        CONTEXT_FILE: str     — e.g. "GEMINI.md"
    """

    KEY: str
    FOLDER: str
    COMMANDS_SUBDIR: str
    REGISTRAR_DIR: str
    CONTEXT_FILE: str

    # -- Registration -----------------------------------------------------

    def test_registered(self):
        assert self.KEY in INTEGRATION_REGISTRY
        assert get_integration(self.KEY) is not None

    def test_is_toml_integration(self):
        assert isinstance(get_integration(self.KEY), TomlIntegration)

    # -- Config -----------------------------------------------------------

    def test_config_folder(self):
        i = get_integration(self.KEY)
        assert i.config["folder"] == self.FOLDER

    def test_config_commands_subdir(self):
        i = get_integration(self.KEY)
        assert i.config["commands_subdir"] == self.COMMANDS_SUBDIR

    def test_registrar_config(self):
        i = get_integration(self.KEY)
        assert i.registrar_config["dir"] == self.REGISTRAR_DIR
        assert i.registrar_config["format"] == "toml"
        assert i.registrar_config["args"] == "{{args}}"
        assert i.registrar_config["extension"] == ".toml"

    def test_context_file(self):
        i = get_integration(self.KEY)
        assert i.context_file == self.CONTEXT_FILE

    # -- Setup / teardown -------------------------------------------------

    def test_setup_creates_files(self, tmp_path):
        i = get_integration(self.KEY)
        m = IntegrationManifest(self.KEY, tmp_path)
        created = i.setup(tmp_path, m)
        assert len(created) > 0
        cmd_files = [f for f in created if "scripts" not in f.parts]
        for f in cmd_files:
            assert f.exists()
            assert f.name.startswith("speckit.")
            assert f.name.endswith(".toml")

    def test_setup_writes_to_correct_directory(self, tmp_path):
        i = get_integration(self.KEY)
        m = IntegrationManifest(self.KEY, tmp_path)
        created = i.setup(tmp_path, m)
        expected_dir = i.commands_dest(tmp_path)
        assert expected_dir.exists(), (
            f"Expected directory {expected_dir} was not created"
        )
        cmd_files = [f for f in created if "scripts" not in f.parts]
        assert len(cmd_files) > 0, "No command files were created"
        for f in cmd_files:
            assert f.resolve().parent == expected_dir.resolve(), (
                f"{f} is not under {expected_dir}"
            )

    def test_templates_are_processed(self, tmp_path):
        """Command files must have placeholders replaced and be valid TOML."""
        i = get_integration(self.KEY)
        m = IntegrationManifest(self.KEY, tmp_path)
        created = i.setup(tmp_path, m)
        cmd_files = [f for f in created if "scripts" not in f.parts]
        assert len(cmd_files) > 0
        for f in cmd_files:
            content = f.read_text(encoding="utf-8")
            assert "{SCRIPT}" not in content, f"{f.name} has unprocessed {{SCRIPT}}"
            assert "__AGENT__" not in content, f"{f.name} has unprocessed __AGENT__"
            assert "{ARGS}" not in content, f"{f.name} has unprocessed {{ARGS}}"
            assert "__SPECKIT_COMMAND_" not in content, f"{f.name} has unprocessed __SPECKIT_COMMAND_*__"

    def test_toml_has_description(self, tmp_path):
        """Every TOML command file should have a description key."""
        i = get_integration(self.KEY)
        m = IntegrationManifest(self.KEY, tmp_path)
        created = i.setup(tmp_path, m)
        cmd_files = [f for f in created if "scripts" not in f.parts]
        for f in cmd_files:
            content = f.read_text(encoding="utf-8")
            assert 'description = "' in content, f"{f.name} missing description key"

    def test_toml_has_prompt(self, tmp_path):
        """Every TOML command file should have a prompt key."""
        i = get_integration(self.KEY)
        m = IntegrationManifest(self.KEY, tmp_path)
        created = i.setup(tmp_path, m)
        cmd_files = [f for f in created if "scripts" not in f.parts]
        for f in cmd_files:
            content = f.read_text(encoding="utf-8")
            assert "prompt = " in content, f"{f.name} missing prompt key"

    def test_toml_uses_correct_arg_placeholder(self, tmp_path):
        """TOML commands must use {{args}} (from {ARGS} replacement)."""
        i = get_integration(self.KEY)
        m = IntegrationManifest(self.KEY, tmp_path)
        created = i.setup(tmp_path, m)
        cmd_files = [f for f in created if "scripts" not in f.parts]
        # At least one file should contain {{args}} from the {ARGS} placeholder
        has_args = any("{{args}}" in f.read_text(encoding="utf-8") for f in cmd_files)
        assert has_args, "No TOML command file contains {{args}} placeholder"
        has_dollar_args = any(
            "$ARGUMENTS" in f.read_text(encoding="utf-8") for f in cmd_files
        )
        assert not has_dollar_args, (
            "TOML command still contains $ARGUMENTS instead of {{args}}"
        )

    @pytest.mark.parametrize(
        ("frontmatter", "expected"),
        [
            (
                "---\ndescription: |\n  First line\n  Second line\n---\nBody\n",
                "First line\nSecond line\n",
            ),
            (
                "---\ndescription: >\n  First line\n  Second line\n---\nBody\n",
                "First line Second line\n",
            ),
            (
                "---\ndescription: |-\n  First line\n  Second line\n---\nBody\n",
                "First line\nSecond line",
            ),
            (
                "---\ndescription: >-\n  First line\n  Second line\n---\nBody\n",
                "First line Second line",
            ),
        ],
    )
    def test_toml_extract_description_supports_block_scalars(
        self, frontmatter, expected
    ):
        assert TomlIntegration._extract_description(frontmatter) == expected

    def test_split_frontmatter_ignores_indented_delimiters(self):
        content = "---\ndescription: |\n  line one\n  ---\n  line two\n---\nBody\n"

        frontmatter, body = TomlIntegration._split_frontmatter(content)

        assert "line two" in frontmatter
        assert body == "Body\n"

    def test_toml_prompt_excludes_frontmatter(self, tmp_path, monkeypatch):
        i = get_integration(self.KEY)
        template = tmp_path / "sample.md"
        template.write_text(
            "---\n"
            "description: Summary line one\n"
            "scripts:\n"
            "  sh: scripts/bash/example.sh\n"
            "---\n"
            "Body line one\n"
            "Body line two\n",
            encoding="utf-8",
        )
        monkeypatch.setattr(i, "list_command_templates", lambda: [template])

        m = IntegrationManifest(self.KEY, tmp_path)
        created = i.setup(tmp_path, m)
        cmd_files = [f for f in created if "scripts" not in f.parts]
        assert len(cmd_files) == 1

        generated = cmd_files[0].read_text(encoding="utf-8")
        parsed = tomllib.loads(generated)

        assert parsed["description"] == "Summary line one"
        assert parsed["prompt"] == "Body line one\nBody line two"
        assert "description:" not in parsed["prompt"]
        assert "scripts:" not in parsed["prompt"]
        assert "---" not in parsed["prompt"]

    def test_toml_no_ambiguous_closing_quotes(self, tmp_path, monkeypatch):
        """Multiline body ending with a double quote must not produce an ambiguous TOML multiline-string closing delimiter (#2113)."""
        i = get_integration(self.KEY)
        template = tmp_path / "sample.md"
        template.write_text(
            "---\n"
            "description: Test\n"
            "scripts:\n"
            "  sh: echo ok\n"
            "---\n"
            "Check the following:\n"
            '- Correct: "Is X clearly specified?"\n',
            encoding="utf-8",
        )
        monkeypatch.setattr(i, "list_command_templates", lambda: [template])

        m = IntegrationManifest(self.KEY, tmp_path)
        created = i.setup(tmp_path, m)
        cmd_files = [f for f in created if "scripts" not in f.parts]
        assert len(cmd_files) == 1

        raw = cmd_files[0].read_text(encoding="utf-8")
        assert '""""' not in raw, "closing delimiter must not merge with body quote"
        assert '"""\n' in raw, "body must use multiline basic string"
        parsed = tomllib.loads(raw)
        assert parsed["prompt"].endswith('specified?"')
        assert not parsed["prompt"].endswith("\n"), (
            "parsed value must not gain a trailing newline"
        )

    def test_toml_triple_double_and_single_quote_ending(self, tmp_path, monkeypatch):
        """Body containing `\"\"\"` and ending with `'` falls back to escaped basic string."""
        i = get_integration(self.KEY)
        template = tmp_path / "sample.md"
        template.write_text(
            "---\n"
            "description: Test\n"
            "scripts:\n"
            "  sh: echo ok\n"
            "---\n"
            'Use """triple""" quotes\n'
            "and end with 'single'\n",
            encoding="utf-8",
        )
        monkeypatch.setattr(i, "list_command_templates", lambda: [template])

        m = IntegrationManifest(self.KEY, tmp_path)
        created = i.setup(tmp_path, m)
        cmd_files = [f for f in created if "scripts" not in f.parts]
        assert len(cmd_files) == 1

        raw = cmd_files[0].read_text(encoding="utf-8")
        assert "''''" not in raw, (
            "literal string must not produce ambiguous closing quotes"
        )
        parsed = tomllib.loads(raw)
        assert parsed["prompt"].endswith("'single'")
        assert '"""triple"""' in parsed["prompt"]
        assert not parsed["prompt"].endswith("\n"), (
            "parsed value must not gain a trailing newline"
        )

    def test_toml_closing_delimiter_inline_when_safe(self, tmp_path, monkeypatch):
        """Body NOT ending with `"` keeps closing `\"\"\"` inline (no extra newline)."""
        i = get_integration(self.KEY)
        template = tmp_path / "sample.md"
        template.write_text(
            "---\n"
            "description: Test\n"
            "scripts:\n"
            "  sh: echo ok\n"
            "---\n"
            "Line one\n"
            "Plain body content\n",
            encoding="utf-8",
        )
        monkeypatch.setattr(i, "list_command_templates", lambda: [template])

        m = IntegrationManifest(self.KEY, tmp_path)
        created = i.setup(tmp_path, m)
        cmd_files = [f for f in created if "scripts" not in f.parts]
        assert len(cmd_files) == 1

        raw = cmd_files[0].read_text(encoding="utf-8")
        parsed = tomllib.loads(raw)
        assert parsed["prompt"] == "Line one\nPlain body content"
        assert raw.rstrip().endswith('content"""'), (
            "closing delimiter should be inline when body does not end with a quote"
        )

    def test_toml_is_valid(self, tmp_path):
        """Every generated TOML file must parse without errors."""
        i = get_integration(self.KEY)
        m = IntegrationManifest(self.KEY, tmp_path)
        created = i.setup(tmp_path, m)
        cmd_files = [f for f in created if "scripts" not in f.parts]
        for f in cmd_files:
            raw = f.read_bytes()
            try:
                parsed = tomllib.loads(raw.decode("utf-8"))
            except Exception as exc:
                raise AssertionError(f"{f.name} is not valid TOML: {exc}") from exc
            assert "prompt" in parsed, f"{f.name} parsed TOML has no 'prompt' key"

    def test_plan_references_correct_context_file(self, tmp_path):
        """The generated plan command must reference this integration's context file."""
        i = get_integration(self.KEY)
        if not i.context_file:
            return
        m = IntegrationManifest(self.KEY, tmp_path)
        i.setup(tmp_path, m)
        plan_file = i.commands_dest(tmp_path) / i.command_filename("plan")
        assert plan_file.exists(), f"Plan file {plan_file} not created"
        content = plan_file.read_text(encoding="utf-8")
        assert i.context_file in content, (
            f"Plan command should reference {i.context_file!r} but it was not found in {plan_file.name}"
        )
        assert "__CONTEXT_FILE__" not in content, (
            f"Plan command has unprocessed __CONTEXT_FILE__ placeholder in {plan_file.name}"
        )

    def test_all_files_tracked_in_manifest(self, tmp_path):
        i = get_integration(self.KEY)
        m = IntegrationManifest(self.KEY, tmp_path)
        created = i.setup(tmp_path, m)
        for f in created:
            rel = f.resolve().relative_to(tmp_path.resolve()).as_posix()
            assert rel in m.files, f"{rel} not tracked in manifest"

    def test_install_uninstall_roundtrip(self, tmp_path):
        i = get_integration(self.KEY)
        m = IntegrationManifest(self.KEY, tmp_path)
        created = i.install(tmp_path, m)
        assert len(created) > 0
        m.save()
        for f in created:
            assert f.exists()
        removed, skipped = i.uninstall(tmp_path, m)
        assert len(removed) == len(created)
        assert skipped == []

    def test_modified_file_survives_uninstall(self, tmp_path):
        i = get_integration(self.KEY)
        m = IntegrationManifest(self.KEY, tmp_path)
        created = i.install(tmp_path, m)
        m.save()
        modified_file = created[0]
        modified_file.write_text("user modified this", encoding="utf-8")
        removed, skipped = i.uninstall(tmp_path, m)
        assert modified_file.exists()
        assert modified_file in skipped

    # -- Context section ---------------------------------------------------

    def test_setup_upserts_context_section(self, tmp_path):
        i = get_integration(self.KEY)
        m = IntegrationManifest(self.KEY, tmp_path)
        i.setup(tmp_path, m)
        if i.context_file:
            ctx_path = tmp_path / i.context_file
            assert ctx_path.exists(), f"Context file {i.context_file} not created for {self.KEY}"
            content = ctx_path.read_text(encoding="utf-8")
            assert "<!-- SPECKIT START -->" in content
            assert "<!-- SPECKIT END -->" in content
            assert "read the current plan" in content

    def test_teardown_removes_context_section(self, tmp_path):
        i = get_integration(self.KEY)
        m = IntegrationManifest(self.KEY, tmp_path)
        i.setup(tmp_path, m)
        m.save()
        if i.context_file:
            ctx_path = tmp_path / i.context_file
            content = ctx_path.read_text(encoding="utf-8")
            ctx_path.write_text("# My Rules\n\n" + content + "\n# Footer\n", encoding="utf-8")
            i.teardown(tmp_path, m)
            remaining = ctx_path.read_text(encoding="utf-8")
            assert "<!-- SPECKIT START -->" not in remaining
            assert "<!-- SPECKIT END -->" not in remaining
            assert "# My Rules" in remaining

    # -- CLI auto-promote -------------------------------------------------

    def test_ai_flag_auto_promotes(self, tmp_path):
        from typer.testing import CliRunner
        from specify_cli import app

        project = tmp_path / f"promote-{self.KEY}"
        project.mkdir()
        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            runner = CliRunner()
            result = runner.invoke(
                app,
                [
                    "init",
                    "--here",
                    "--ai",
                    self.KEY,
                    "--script",
                    "sh",
                    "--no-git",
                    "--ignore-agent-tools",
                ],
                catch_exceptions=False,
            )
        finally:
            os.chdir(old_cwd)
        assert result.exit_code == 0, f"init --ai {self.KEY} failed: {result.output}"
        i = get_integration(self.KEY)
        cmd_dir = i.commands_dest(project)
        assert cmd_dir.is_dir(), f"--ai {self.KEY} did not create commands directory"

    def test_integration_flag_creates_files(self, tmp_path):
        from typer.testing import CliRunner
        from specify_cli import app

        project = tmp_path / f"int-{self.KEY}"
        project.mkdir()
        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            runner = CliRunner()
            result = runner.invoke(
                app,
                [
                    "init",
                    "--here",
                    "--integration",
                    self.KEY,
                    "--script",
                    "sh",
                    "--no-git",
                    "--ignore-agent-tools",
                ],
                catch_exceptions=False,
            )
        finally:
            os.chdir(old_cwd)
        assert result.exit_code == 0, (
            f"init --integration {self.KEY} failed: {result.output}"
        )
        i = get_integration(self.KEY)
        cmd_dir = i.commands_dest(project)
        assert cmd_dir.is_dir(), f"Commands directory {cmd_dir} not created"
        commands = sorted(cmd_dir.glob("speckit.*.toml"))
        assert len(commands) > 0, f"No command files in {cmd_dir}"

    def test_init_options_includes_context_file(self, tmp_path):
        """init-options.json must include context_file for the active integration."""
        import json
        from typer.testing import CliRunner
        from specify_cli import app

        project = tmp_path / f"opts-{self.KEY}"
        project.mkdir()
        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            result = CliRunner().invoke(app, [
                "init", "--here", "--integration", self.KEY, "--script", "sh",
                "--no-git", "--ignore-agent-tools",
            ], catch_exceptions=False)
        finally:
            os.chdir(old_cwd)
        assert result.exit_code == 0
        opts = json.loads((project / ".specify" / "init-options.json").read_text())
        i = get_integration(self.KEY)
        assert opts.get("context_file") == i.context_file, (
            f"Expected context_file={i.context_file!r}, got {opts.get('context_file')!r}"
        )

    # -- Complete file inventory ------------------------------------------

    COMMAND_STEMS = [
        "governance",
        "analyze",
        "checklist",
        "clarify",
        "constitution",
        "implement",
        "plan",
        "specify",
        "tasks",
        "taskstoissues",
    ]

    def _expected_files(self, script_variant: str) -> list[str]:
        """Build the expected file list for this integration + script variant."""
        i = get_integration(self.KEY)
        cmd_dir = i.registrar_config["dir"]
        files = []

        # Command files (.toml)
        for stem in self.COMMAND_STEMS:
            files.append(f"{cmd_dir}/speckit.{stem}.toml")

        # Framework files
        files.append(".specify/integration.json")
        files.append(".specify/init-options.json")
        files.append(f".specify/integrations/{self.KEY}.manifest.json")
        files.append(".specify/integrations/speckit.manifest.json")

        if script_variant == "sh":
            for name in [
                "check-prerequisites.sh",
                "common.sh",
                "create-new-feature.sh",
                "setup-plan.sh",
                "setup-tasks.sh",
            ]:
                files.append(f".specify/scripts/bash/{name}")
        else:
            for name in [
                "check-prerequisites.ps1",
                "common.ps1",
                "create-new-feature.ps1",
                "setup-plan.ps1",
                "setup-tasks.ps1",
            ]:
                files.append(f".specify/scripts/powershell/{name}")

        for name in [
            "agent-governance-template.md",
            "checklist-template.md",
            "constitution-template.md",
            "plan-template.md",
            "spec-template.md",
            "tasks-template.md",
        ]:
            files.append(f".specify/templates/{name}")

        files.append("AGENTS.md")
        files.append(".specify/memory/agent-governance.md")
        files.append(".specify/memory/constitution.md")
        # Bundled workflow
        files.append(".specify/workflows/speckit/workflow.yml")
        files.append(".specify/workflows/workflow-registry.json")

        # Agent context file (if set)
        if i.context_file:
            files.append(i.context_file)

        return sorted(files)

    def test_complete_file_inventory_sh(self, tmp_path):
        """Every file produced by specify init --integration <key> --script sh."""
        from typer.testing import CliRunner
        from specify_cli import app

        project = tmp_path / f"inventory-sh-{self.KEY}"
        project.mkdir()
        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            result = CliRunner().invoke(
                app,
                [
                    "init",
                    "--here",
                    "--integration",
                    self.KEY,
                    "--script",
                    "sh",
                    "--no-git",
                    "--ignore-agent-tools",
                ],
                catch_exceptions=False,
            )
        finally:
            os.chdir(old_cwd)
        assert result.exit_code == 0, f"init failed: {result.output}"
        actual = sorted(
            p.relative_to(project).as_posix() for p in project.rglob("*") if p.is_file()
        )
        expected = self._expected_files("sh")
        assert actual == expected, (
            f"Missing: {sorted(set(expected) - set(actual))}\n"
            f"Extra: {sorted(set(actual) - set(expected))}"
        )

    def test_complete_file_inventory_ps(self, tmp_path):
        """Every file produced by specify init --integration <key> --script ps."""
        from typer.testing import CliRunner
        from specify_cli import app

        project = tmp_path / f"inventory-ps-{self.KEY}"
        project.mkdir()
        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            result = CliRunner().invoke(
                app,
                [
                    "init",
                    "--here",
                    "--integration",
                    self.KEY,
                    "--script",
                    "ps",
                    "--no-git",
                    "--ignore-agent-tools",
                ],
                catch_exceptions=False,
            )
        finally:
            os.chdir(old_cwd)
        assert result.exit_code == 0, f"init failed: {result.output}"
        actual = sorted(
            p.relative_to(project).as_posix() for p in project.rglob("*") if p.is_file()
        )
        expected = self._expected_files("ps")
        assert actual == expected, (
            f"Missing: {sorted(set(expected) - set(actual))}\n"
            f"Extra: {sorted(set(actual) - set(expected))}"
        )
