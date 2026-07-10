"""Reusable test mixin for standard YamlIntegration subclasses.

Each per-agent test file sets ``KEY``, ``FOLDER``, ``COMMANDS_SUBDIR``,
and ``REGISTRAR_DIR``, then inherits all verification logic from
``YamlIntegrationTests``.

Mirrors ``TomlIntegrationTests`` closely — same test structure,
adapted for YAML recipe output format.
"""

import os

import yaml

from specify_cli.integrations import INTEGRATION_REGISTRY, get_integration
from specify_cli.integrations.base import YamlIntegration
from specify_cli.integrations.manifest import IntegrationManifest


class YamlIntegrationTests:
    """Mixin — set class-level constants and inherit these tests.

    Required class attrs on subclass::

        KEY: str              — integration registry key
        FOLDER: str           — e.g. ".goose/"
        COMMANDS_SUBDIR: str  — e.g. "recipes"
        REGISTRAR_DIR: str    — e.g. ".goose/recipes"
    """

    KEY: str
    FOLDER: str
    COMMANDS_SUBDIR: str
    REGISTRAR_DIR: str

    # -- Registration -----------------------------------------------------

    def test_registered(self):
        assert self.KEY in INTEGRATION_REGISTRY
        assert get_integration(self.KEY) is not None

    def test_is_yaml_integration(self):
        assert isinstance(get_integration(self.KEY), YamlIntegration)

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
        assert i.registrar_config["format"] == "yaml"
        assert i.registrar_config["args"] == "{{args}}"
        assert i.registrar_config["extension"] == ".yaml"

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
            assert f.name.endswith(".yaml")

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
        """Command files must have placeholders replaced."""
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

    def test_yaml_has_title(self, tmp_path):
        """Every YAML recipe should have a title field."""
        i = get_integration(self.KEY)
        m = IntegrationManifest(self.KEY, tmp_path)
        created = i.setup(tmp_path, m)
        cmd_files = [f for f in created if "scripts" not in f.parts]
        for f in cmd_files:
            content = f.read_text(encoding="utf-8")
            assert "title:" in content, f"{f.name} missing title field"

    def test_yaml_has_prompt(self, tmp_path):
        """Every YAML recipe should have a prompt block scalar."""
        i = get_integration(self.KEY)
        m = IntegrationManifest(self.KEY, tmp_path)
        created = i.setup(tmp_path, m)
        cmd_files = [f for f in created if "scripts" not in f.parts]
        for f in cmd_files:
            content = f.read_text(encoding="utf-8")
            assert "prompt: |" in content, f"{f.name} missing prompt block scalar"

    def test_yaml_uses_correct_arg_placeholder(self, tmp_path):
        """YAML recipes must use {{args}} placeholder."""
        i = get_integration(self.KEY)
        m = IntegrationManifest(self.KEY, tmp_path)
        created = i.setup(tmp_path, m)
        cmd_files = [f for f in created if "scripts" not in f.parts]
        has_args = any("{{args}}" in f.read_text(encoding="utf-8") for f in cmd_files)
        assert has_args, "No YAML recipe contains {{args}} placeholder"
        has_dollar_args = any(
            "$ARGUMENTS" in f.read_text(encoding="utf-8") for f in cmd_files
        )
        assert not has_dollar_args, (
            "YAML recipe still contains $ARGUMENTS instead of {{args}}"
        )

    def test_yaml_is_valid(self, tmp_path):
        """Every generated YAML file must parse without errors."""
        i = get_integration(self.KEY)
        m = IntegrationManifest(self.KEY, tmp_path)
        created = i.setup(tmp_path, m)
        cmd_files = [f for f in created if "scripts" not in f.parts]
        for f in cmd_files:
            content = f.read_text(encoding="utf-8")
            # Strip trailing source comment before parsing
            lines = content.split("\n")
            yaml_lines = [ln for ln in lines if not ln.startswith("# Source:")]
            try:
                parsed = yaml.safe_load("\n".join(yaml_lines))
            except Exception as exc:
                raise AssertionError(f"{f.name} is not valid YAML: {exc}") from exc
            assert "prompt" in parsed, f"{f.name} parsed YAML has no 'prompt' key"
            assert "title" in parsed, f"{f.name} parsed YAML has no 'title' key"

    def test_yaml_prompt_excludes_frontmatter(self, tmp_path, monkeypatch):
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

        content = cmd_files[0].read_text(encoding="utf-8")
        # Strip source comment for parsing
        lines = content.split("\n")
        yaml_lines = [ln for ln in lines if not ln.startswith("# Source:")]
        parsed = yaml.safe_load("\n".join(yaml_lines))

        assert "description:" not in parsed["prompt"]
        assert "scripts:" not in parsed["prompt"]
        assert "---" not in parsed["prompt"]

    def test_yaml_prompt_with_indented_first_line_stays_valid(self):
        """A body whose first line is indented must still parse.

        A bare ``|`` block scalar infers its indentation from the first
        non-empty line, so a body starting with an indented line (e.g. a
        markdown code block or nested list item) made the parser expect that
        deeper indent for the whole block and reject the later, shallower
        lines. The explicit ``|2`` indicator pins the indent so it parses."""
        body = "    indented first line\nback to normal\n    indented again"
        rendered = YamlIntegration._render_yaml("Title", "Desc", body, "src")

        yaml_lines = [
            ln for ln in rendered.split("\n") if not ln.startswith("# Source:")
        ]
        parsed = yaml.safe_load("\n".join(yaml_lines))
        assert parsed["prompt"].rstrip("\n") == body

    def test_yaml_prompt_with_control_characters_stays_valid(self):
        """A body containing control characters must still produce parseable YAML.

        YAML forbids C0 control characters (except tab and newline), DEL,
        C1 controls, lone surrogates and U+FFFE/U+FFFF in every scalar form,
        and YAML 1.1 treats NEL (U+0085), LS (U+2028) and PS (U+2029) as
        line breaks that corrupt a literal block scalar's structure. The
        renderer falls back to an escaped double-quoted scalar for such
        bodies."""
        for ch in (
            "\x08", "\x0c", "\x1b", "\x7f",
            "\x80", "\x84", "\x85", "\x86", "\x9f",
            "\u2028", "\u2029",
            "\ud800", "\udfff", "\ufffe", "\uffff",
        ):
            body = f"before{ch}after\nsecond line"
            rendered = YamlIntegration._render_yaml("Title", "Desc", body, "src")
            parsed = yaml.safe_load(rendered)
            assert parsed["prompt"].rstrip("\n") == body, f"char {ch!r} round-trip"

    def test_yaml_prompt_with_bare_carriage_return_stays_valid(self):
        """A bare CR (not part of CRLF) must not break the generated YAML.

        Inside a block scalar a lone \r acts as a line break, corrupting
        the document structure."""
        body = "line1\rstill line1\nline2"
        rendered = YamlIntegration._render_yaml("Title", "Desc", body, "src")
        parsed = yaml.safe_load(rendered)
        assert parsed["prompt"].rstrip("\n") == body

    def test_plan_command_has_no_context_placeholder(self, tmp_path):
        """The generated plan command must not carry a context-file placeholder.

        Agent context files are owned entirely by the opt-in agent-context
        extension, so the core plan command must not reference one.
        """
        i = get_integration(self.KEY)
        m = IntegrationManifest(self.KEY, tmp_path)
        i.setup(tmp_path, m)
        plan_file = i.commands_dest(tmp_path) / i.command_filename("plan")
        assert plan_file.exists(), f"Plan file {plan_file} not created"
        content = plan_file.read_text(encoding="utf-8")
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

    # -- Context file ownership (extension-owned, opt-in) -----------------

    def test_setup_does_not_write_context_section(self, tmp_path):
        """Setup must not create or manage any agent context file — that is
        owned entirely by the opt-in agent-context extension."""
        i = get_integration(self.KEY)
        m = IntegrationManifest(self.KEY, tmp_path)
        i.setup(tmp_path, m)
        for path in tmp_path.rglob("*"):
            if path.is_file():
                text = path.read_text(encoding="utf-8", errors="ignore")
                assert "<!-- SPECKIT START -->" not in text, (
                    f"Setup wrote a managed context section into {path} for {self.KEY}"
                )

    def test_teardown_leaves_existing_context_file_intact(self, tmp_path):
        """A user-authored context file must survive setup + teardown untouched."""
        i = get_integration(self.KEY)
        m = IntegrationManifest(self.KEY, tmp_path)
        ctx_path = tmp_path / "AGENTS.md"
        original = "# My Rules\n\nUser content.\n"
        ctx_path.write_text(original, encoding="utf-8")
        i.setup(tmp_path, m)
        m.save()
        i.teardown(tmp_path, m)
        assert ctx_path.read_text(encoding="utf-8") == original

    # -- CLI integration flag -------------------------------------------------

    def test_integration_flag_auto_promotes(self, tmp_path):
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
                    "--integration",
                    self.KEY,
                    "--script",
                    "sh",
                    "--ignore-agent-tools",
                ],
                catch_exceptions=False,
            )
        finally:
            os.chdir(old_cwd)
        assert result.exit_code == 0, f"init --integration {self.KEY} failed: {result.output}"
        i = get_integration(self.KEY)
        cmd_dir = i.commands_dest(project)
        assert cmd_dir.is_dir(), f"--integration {self.KEY} did not create commands directory"

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
        commands = sorted(cmd_dir.glob("speckit.*.yaml"))
        assert len(commands) > 0, f"No command files in {cmd_dir}"


    # -- Complete file inventory ------------------------------------------

    COMMAND_STEMS = [
        "analyze",
        "clarify",
        "constitution",
        "converge",
        "implement",
        "plan",
        "checklist",
        "specify",
        "tasks",
        "taskstoissues",
    ]

    def _expected_files(self, script_variant: str) -> list[str]:
        """Build the expected file list for this integration + script variant."""
        i = get_integration(self.KEY)
        cmd_dir = i.registrar_config["dir"]
        files = []

        # Command files (.yaml)
        for stem in self.COMMAND_STEMS:
            files.append(f"{cmd_dir}/speckit.{stem}.yaml")

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
            "checklist-template.md",
            "constitution-template.md",
            "plan-template.md",
            "spec-template.md",
            "tasks-template.md",
        ]:
            files.append(f".specify/templates/{name}")

        files.append(".specify/memory/constitution.md")
        # Bundled workflow
        files.append(".specify/workflows/speckit/workflow.yml")
        files.append(".specify/workflows/workflow-registry.json")



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
                    "--ignore-agent-tools",
                ],
                catch_exceptions=False,
            )
        finally:
            os.chdir(old_cwd)
        assert result.exit_code == 0, f"init failed: {result.output}"
        actual = sorted(
            p.relative_to(project).as_posix() for p in project.rglob("*") if p.is_file() and ".git" not in p.parts
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
                    "--ignore-agent-tools",
                ],
                catch_exceptions=False,
            )
        finally:
            os.chdir(old_cwd)
        assert result.exit_code == 0, f"init failed: {result.output}"
        actual = sorted(
            p.relative_to(project).as_posix() for p in project.rglob("*") if p.is_file() and ".git" not in p.parts
        )
        expected = self._expected_files("ps")
        assert actual == expected, (
            f"Missing: {sorted(set(expected) - set(actual))}\n"
            f"Extra: {sorted(set(actual) - set(expected))}"
        )
