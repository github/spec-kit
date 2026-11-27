"""Tests for JunieIntegration."""

import os
import pytest

from specify_cli.integrations import get_integration
from specify_cli.integrations.junie import (
    _hyphenate_frontmatter_refs,
    format_junie_command_name,
    hyphenate_command_refs,
)
from .test_integration_base_markdown import MarkdownIntegrationTests

class TestJunieCommandNameFormatter:
    """Test the junie command name formatter."""

    def test_simple_name_without_prefix(self):
        """Test formatting a simple name without 'speckit.' prefix."""
        assert format_junie_command_name("plan") == "speckit-plan"
        assert format_junie_command_name("tasks") == "speckit-tasks"
        assert format_junie_command_name("specify") == "speckit-specify"

    def test_name_with_speckit_prefix(self):
        """Test formatting a name that already has 'speckit.' prefix."""
        assert format_junie_command_name("speckit.plan") == "speckit-plan"
        assert format_junie_command_name("speckit.tasks") == "speckit-tasks"

    def test_extension_command_name(self):
        """Test formatting extension command names with dots."""
        assert (
            format_junie_command_name("speckit.my-extension.example")
            == "speckit-my-extension-example"
        )
        assert (
            format_junie_command_name("my-extension.example")
            == "speckit-my-extension-example"
        )

    def test_idempotent_already_hyphenated(self):
        """Test that already-hyphenated names are returned unchanged (idempotent)."""
        assert format_junie_command_name("speckit-plan") == "speckit-plan"
        assert (
            format_junie_command_name("speckit-my-extension-example")
            == "speckit-my-extension-example"
        )




class TestJunieIntegration(MarkdownIntegrationTests):
    KEY = "junie"
    FOLDER = ".junie/"
    COMMANDS_SUBDIR = "commands"
    REGISTRAR_DIR = ".junie/commands"

    @pytest.mark.parametrize(
        "cmd_name, expected_filename",
        [
            ("plan", "speckit-plan.md"),
            ("speckit.plan", "speckit-plan.md"),
            ("speckit.git.commit", "speckit-git-commit.md"),
            ("speckit", "speckit-speckit.md"),
            ("speckitfoo", "speckit-speckitfoo.md"),
        ],
    )

    def test_junie_command_filename(self, cmd_name, expected_filename):
        """Verify junie uses hyphenated filenames."""
        junie = get_integration("junie")
        assert junie.command_filename(cmd_name) == expected_filename

    def test_junie_invoke_separator(self):
        """Verify junie uses hyphen as invoke separator."""
        junie = get_integration("junie")
        assert junie.invoke_separator == "-"
        assert junie.registrar_config["invoke_separator"] == "-"

    def test_junie_name_injection_and_formatting(self):
        """Verify junie has inject_name and format_name configured."""
        junie = get_integration("junie")
        assert junie.registrar_config["inject_name"] is True
        assert junie.registrar_config[
                   "format_name"] == format_junie_command_name

    def test_junie_handoff_rewrite(self):
        """Verify junie rewrites agent: speckit.foo to agent: speckit-foo."""
        junie = get_integration("junie")
        content = "---\nagent: speckit.plan\n---\n"
        rewritten = junie._rewrite_handoff_references(content)
        assert rewritten == "---\nagent: speckit-plan\n---\n"

    def test_junie_body_refs_keep_md_file_names(self):
        """Command references are hyphenated but ``speckit.*.md`` file names keep ``.md``."""
        body = (
            "Edit `.specify/extensions/git/commands/speckit.git.commit.md`, "
            "then run /speckit.git.commit."
        )
        assert hyphenate_command_refs(body) == (
            "Edit `.specify/extensions/git/commands/speckit.git.commit.md`, "
            "then run /speckit-git-commit."
        )

    def test_junie_refs_keep_md_file_names_at_a_windows_drive_root_and_env_paths(self):
        """Drive roots, ``(x86)``, ``[old]`` and ``%VAR%`` paths stay file names; commands hyphenate."""
        body = (
            "Open C:\\speckit.foo.md, C:\\Program Files (x86)\\speckit.git.commit.md, "
            "%TEMP%\\speckit.git.commit.md or ./commands[old]/speckit.git.commit.md, "
            "then run /speckit.foo.md and [/speckit.bar.md]."
        )
        assert hyphenate_command_refs(body) == (
            "Open C:\\speckit.foo.md, C:\\Program Files (x86)\\speckit.git.commit.md, "
            "%TEMP%\\speckit.git.commit.md or ./commands[old]/speckit.git.commit.md, "
            "then run /speckit-foo-md and [/speckit-bar-md]."
        )
        refs = _hyphenate_frontmatter_refs(
            {"file": "C:\\speckit.foo.md", "agent": "speckit.foo.md"}
        )
        assert refs == {"file": "C:\\speckit.foo.md", "agent": "speckit-foo-md"}

    def _register_junie_command(
        self, tmp_path, source_id, body, frontmatter="", *, extension_id=None
    ):
        from specify_cli.agents import CommandRegistrar

        source = tmp_path / "src"
        (source / "commands").mkdir(parents=True)
        (source / "commands" / "commit.md").write_text(
            f"---\ndescription: Commit\n{frontmatter}---\n\n{body}",
            encoding="utf-8",
        )
        project = tmp_path / "project"
        project.mkdir()
        CommandRegistrar().register_commands(
            "junie",
            [{"name": "speckit.git.commit", "file": "commands/commit.md"}],
            source_id,
            source,
            project,
            extension_id=extension_id,
        )
        out = project / ".junie" / "commands" / "speckit-git-commit.md"
        return out.read_text(encoding="utf-8")

    def test_registered_extension_command_keeps_md_file_names(self, tmp_path):
        """Registering an extension command for Junie hyphenates command
        references in the body and frontmatter but keeps ``.md`` file names."""
        text = self._register_junie_command(
            tmp_path,
            "git",
            "Edit `.specify/extensions/git/commands/speckit.git.commit.md`, "
            "then run /speckit.git.status.\n",
            frontmatter="handoff: speckit.git.status\nsource_file: commands/speckit.git.commit.md\n",
        )
        assert "`.specify/extensions/git/commands/speckit.git.commit.md`" in text
        assert "then run /speckit-git-status." in text
        assert "handoff: speckit-git-status" in text
        assert "source_file: commands/speckit.git.commit.md" in text
        assert "speckit-git-commit-md" not in text

    def test_registered_extension_command_keeps_bracketed_and_env_paths(self, tmp_path):
        """Registration keeps ``.md`` file names under ``(x86)``, ``[old]`` and
        ``%TEMP%`` directories in the body and frontmatter."""
        text = self._register_junie_command(
            tmp_path,
            "git",
            "Copy C:\\Program Files (x86)\\speckit.git.commit.md and "
            "./commands[old]/speckit.git.commit.md, then run /speckit.git.status.\n",
            frontmatter="source_file: '%TEMP%\\speckit.git.commit.md'\n",
        )
        assert "C:\\Program Files (x86)\\speckit.git.commit.md" in text
        assert "./commands[old]/speckit.git.commit.md" in text
        assert "%TEMP%\\speckit.git.commit.md" in text
        assert "then run /speckit-git-status." in text
        assert "speckit-git-commit-md" not in text

    def test_registered_core_command_is_not_rewritten(self, tmp_path):
        """The rewrite stays limited to extension and preset commands."""
        text = self._register_junie_command(
            tmp_path, "core", "Then run /speckit.git.status.\n"
        )
        assert "Then run /speckit.git.status." in text

    def test_process_registered_command_hook(self):
        junie = get_integration("junie")
        frontmatter = {"handoff": "speckit.plan", "file": "commands/speckit.plan.md"}
        body = "Run /speckit.plan; see commands/speckit.plan.md."
        assert junie.process_registered_command(
            frontmatter, body, source_id="core"
        ) == (frontmatter, body)
        assert junie.process_registered_command(
            frontmatter, body, source_id="my-preset"
        ) == (
            {"handoff": "speckit-plan", "file": "commands/speckit.plan.md"},
            "Run /speckit-plan; see commands/speckit.plan.md.",
        )

    def test_registered_extension_command_keeps_script_paths_and_dotted_directories(
        self, tmp_path
    ):
        """Non-.md path-qualified names, `{SCRIPT}`, and dotted directories keep dots."""
        text = self._register_junie_command(
            tmp_path,
            "git",
            "Invoke {SCRIPT}, read scripts/speckit.git.commit.sh, "
            "open /tmp/speckit.demo/commands/speckit.git.commit.md and "
            "speckit.demo/commands/speckit.git.commit.md, "
            "then run /speckit.git.status and /speckit.foo.sh.\n",
            frontmatter=(
                "scripts:\n"
                '  sh: \'scripts/speckit.git.commit.sh "{ARGS}"\'\n'
                "notes: /tmp/speckit.demo/commands/speckit.git.commit.md\n"
            ),
            extension_id="git",
        )
        assert '.specify/extensions/git/scripts/speckit.git.commit.sh "$ARGUMENTS"' in text
        assert "scripts/speckit.git.commit.sh" in text
        assert "/tmp/speckit.demo/commands/speckit.git.commit.md" in text
        assert "speckit.demo/commands/speckit.git.commit.md" in text
        assert "notes: /tmp/speckit.demo/commands/speckit.git.commit.md" in text
        assert "then run /speckit-git-status and /speckit-foo-sh." in text
        assert "speckit-demo" not in text
        assert "speckit-git-commit-sh" not in text

    def test_frontmatter_refs_memoize_shared_and_cyclic_yaml_aliases(self, tmp_path):
        """Shared YAML aliases keep identity and cyclic containers do not overflow."""
        import yaml
        from specify_cli.agents import CommandRegistrar

        shared_yaml = (
            "shared: &shared\n"
            "  next: /speckit.git.status\n"
            "  script: scripts/speckit.git.commit.sh\n"
            "first: *shared\n"
            "second: *shared\n"
        )
        loaded = yaml.safe_load(shared_yaml)
        out = _hyphenate_frontmatter_refs(loaded)
        assert out["first"] is out["second"]
        assert out["shared"] is out["first"]
        assert out["first"] == {
            "next": "/speckit-git-status",
            "script": "scripts/speckit.git.commit.sh",
        }
        assert loaded["shared"]["next"] == "/speckit.git.status"

        # End-to-end registration with YAML aliases in frontmatter.
        source = tmp_path / "src"
        (source / "commands").mkdir(parents=True)
        (source / "commands" / "commit.md").write_text(
            f"---\ndescription: Commit\n{shared_yaml}---\n\nRun /speckit.git.status.\n",
            encoding="utf-8",
        )
        project = tmp_path / "project"
        project.mkdir()
        CommandRegistrar().register_commands(
            "junie",
            [{"name": "speckit.git.commit", "file": "commands/commit.md"}],
            "git",
            source,
            project,
        )
        rendered = (
            project / ".junie" / "commands" / "speckit-git-commit.md"
        ).read_text(encoding="utf-8")
        assert "/speckit-git-status" in rendered
        assert "scripts/speckit.git.commit.sh" in rendered

        # Cyclic dict and cyclic list must not recurse infinitely or mutate inputs.
        cyclic_dict: dict[str, object] = {"cmd": "speckit.plan"}
        cyclic_dict["self"] = cyclic_dict
        transformed_dict = _hyphenate_frontmatter_refs(cyclic_dict)
        assert transformed_dict is not cyclic_dict
        assert transformed_dict["cmd"] == "speckit-plan"
        assert transformed_dict["self"] is transformed_dict
        assert cyclic_dict["cmd"] == "speckit.plan"

        cyclic_list: list[object] = ["speckit.plan"]
        cyclic_list.append(cyclic_list)
        transformed_list = _hyphenate_frontmatter_refs(cyclic_list)
        assert transformed_list is not cyclic_list
        assert transformed_list[0] == "speckit-plan"
        assert transformed_list[1] is transformed_list
        assert cyclic_list[0] == "speckit.plan"

    def test_registered_extension_command_keeps_prefixed_filenames_and_spaced_bracket_dirs(
        self, tmp_path
    ):
        """Prefixed filenames inside paths and spaced bracketed directories stay intact."""
        text = self._register_junie_command(
            tmp_path,
            "git",
            "Invoke {SCRIPT}, read commands/archived.speckit.git.commit.md, "
            "open C:\\Program Files (old versions)\\speckit.git.commit.md, "
            "C:/Program Files (old versions)/speckit.git.commit.md, "
            "./commands[old files]/speckit.git.commit.md, "
            "commands[old files]/speckit.git.commit.md, and "
            "/tmp/my-speckit.demo (old versions)/commands/archived.speckit.git.commit.md. "
            "Also check (see docs)/speckit.foo.md, [Run command]/speckit.foo.md, "
            "Edit C:\\foo\\bar.txt, then run (see docs)/speckit.foo.md, "
            "and /speckit.git.status.\n",
            frontmatter=(
                "scripts:\n"
                '  sh: \'scripts/run-speckit.git.commit.sh "{ARGS}"\'\n'
                "spaced_dir: 'C:\\Program Files (old versions)\\speckit.git.commit.md'\n"
                "archived: commands/archived.speckit.git.commit.md\n"
            ),
            extension_id="git",
        )
        assert '.specify/extensions/git/scripts/run-speckit.git.commit.sh "$ARGUMENTS"' in text
        assert "commands/archived.speckit.git.commit.md" in text
        assert "C:\\Program Files (old versions)\\speckit.git.commit.md" in text
        assert "C:/Program Files (old versions)/speckit.git.commit.md" in text
        assert "./commands[old files]/speckit.git.commit.md" in text
        assert "commands[old files]/speckit.git.commit.md" in text
        assert "/tmp/my-speckit.demo (old versions)/commands/archived.speckit.git.commit.md" in text
        assert "(see docs)/speckit-foo-md" in text
        assert "[Run command]/speckit-foo-md" in text
        assert "Edit C:\\foo\\bar.txt, then run (see docs)/speckit-foo-md" in text
        assert "and /speckit-git-status." in text
        assert "run-speckit-git-commit-sh" not in text
        assert "archived-speckit-git-commit-md" not in text
        assert "my-speckit-demo" not in text

    def test_registered_extension_command_keeps_plus_quoted_and_bracketed_paths(
        self, tmp_path
    ):
        """Plus-named dirs, quoted spaced paths, and bracketed segments stay intact."""
        text = self._register_junie_command(
            tmp_path,
            "git",
            "Invoke {SCRIPT}, read C:\\C++\\speckit.git.commit.md, "
            '"scripts/my speckit.git.commit.sh", '
            "'scripts/my speckit.git.commit.sh', "
            "`scripts/my speckit.git.commit.sh`, "
            '"C:\\Program Files\\my speckit.git.commit.sh", '
            '"/tmp/my dir/my speckit.git.commit.md", '
            "commands/[old]speckit.git.commit.md, "
            "speckit.demo[old]/commands/speckit.git.commit.md, and "
            "speckit.demo[old files]/commands/speckit.git.commit.md. "
            'Compare "Run /speckit.git.commit", "/speckit.foo.md", '
            '"ab:/speckit.foo.md", "Run speckit.plan and edit scripts/foo.sh", '
            '"don\'t run /speckit.git.status", [/speckit.foo.md], '
            "([/speckit.foo.md]), and [Run](/speckit.foo.md).\n",
            frontmatter=(
                "scripts:\n"
                '  sh: \'scripts/C++/speckit.git.commit.sh "{ARGS}"\'\n'
                'quoted: "scripts/my speckit.git.commit.sh"\n'
                "bracketed: commands/[old]speckit.git.commit.md\n"
            ),
            extension_id="git",
        )
        assert '.specify/extensions/git/scripts/C++/speckit.git.commit.sh "$ARGUMENTS"' in text
        assert "C:\\C++\\speckit.git.commit.md" in text
        assert '".specify/extensions/git/scripts/my speckit.git.commit.sh"' in text
        assert "'.specify/extensions/git/scripts/my speckit.git.commit.sh'" in text
        assert "`.specify/extensions/git/scripts/my speckit.git.commit.sh`" in text
        assert '"C:\\Program Files\\my speckit.git.commit.sh"' in text
        assert '"/tmp/my dir/my speckit.git.commit.md"' in text
        assert "commands/[old]speckit.git.commit.md" in text
        assert "speckit.demo[old]/commands/speckit.git.commit.md" in text
        assert "speckit.demo[old files]/commands/speckit.git.commit.md" in text
        assert "quoted: scripts/my speckit.git.commit.sh" in text
        assert "bracketed: commands/[old]speckit.git.commit.md" in text
        assert '"Run /speckit-git-commit"' in text
        assert '"/speckit-foo-md"' in text
        assert '"ab:/speckit-foo-md"' in text
        assert '"Run speckit-plan and edit .specify/extensions/git/scripts/foo.sh"' in text
        assert '"don\'t run /speckit-git-status"' in text
        assert "[/speckit-foo-md], ([/speckit-foo-md]), and [Run](/speckit-foo-md)." in text
        assert "my speckit-git-commit" not in text

    def test_hyphenate_command_refs_linear_scaling_in_long_segment(self):
        """Scanning many matches in one segment or unmatched brackets scales linearly."""
        import time

        t0 = time.monotonic()
        non_path = "a" + "-speckit.x" * 10_000
        assert hyphenate_command_refs(non_path) == "a" + "-speckit-x" * 10_000

        path_seg = "scripts/a" + "-speckit.x" * 10_000
        assert hyphenate_command_refs(path_seg) == path_seg

        unmatched = "]" * 20_000 + "/speckit.foo"
        assert hyphenate_command_refs(unmatched) == "]" * 20_000 + "/speckit-foo"

        contractions = "'" + "don't " * 10_000 + "/speckit.foo'"
        assert hyphenate_command_refs(contractions) == "'" + "don't " * 10_000 + "/speckit-foo'"
        elapsed = time.monotonic() - t0
        assert elapsed < 5.0, f"linear normalization took too long: {elapsed:.2f}s"

    def test_spaced_first_dir_quoted_path_leading_prose_and_bounded_memory(self, tmp_path):
        """Spaced initial directory paths stay intact, path-leading/multiline prose still hyphenates, and large inputs stay memory-bounded."""
        import tracemalloc

        # Spaced first directory component in quoted body & frontmatter.
        assert (
            hyphenate_command_refs('"my scripts/my speckit.git.commit.sh"')
            == '"my scripts/my speckit.git.commit.sh"'
        )
        assert _hyphenate_frontmatter_refs(
            {"spaced_first": "my scripts/my speckit.git.commit.sh"}
        ) == {"spaced_first": "my scripts/my speckit.git.commit.sh"}

        # Path-leading prose and multiline frontmatter values still hyphenate commands.
        assert (
            hyphenate_command_refs('"docs/setup.md then run speckit.plan"')
            == '"docs/setup.md then run speckit-plan"'
        )
        fm_prose = _hyphenate_frontmatter_refs(
            {
                "prose_path": "docs/setup.md then run speckit.plan",
                "multiline": "docs/usage.md\n/speckit.plan",
            }
        )
        assert fm_prose == {
            "prose_path": "docs/setup.md then run speckit-plan",
            "multiline": "docs/usage.md\n/speckit-plan",
        }

        text = self._register_junie_command(
            tmp_path,
            "git",
            '"my scripts/my speckit.git.commit.sh" vs "docs/setup.md then run speckit.plan".\n',
            frontmatter=(
                'spaced_first: "my scripts/my speckit.git.commit.sh"\n'
                'prose_path: "docs/setup.md then run speckit.plan"\n'
                'multiline: |\n'
                '  docs/usage.md\n'
                '  /speckit.plan\n'
            ),
        )
        assert '"my .specify/scripts/my speckit.git.commit.sh"' in text
        assert '"docs/setup.md then run speckit-plan"' in text
        assert "spaced_first: my scripts/my speckit.git.commit.sh" in text
        assert "prose_path: docs/setup.md then run speckit-plan" in text
        assert "/speckit-plan" in text

        # Bounded extra memory on ~1 MiB commands (both multi-line and single-line).
        big_line = "a/b[c]/d/e(f)/" * 8
        big_doc = (big_line + "\n") * 9_000 + "Run /speckit.git.status\n"
        single_line = big_line * 8_000 + " Run /speckit.git.status"
        for sample in (big_doc, single_line):
            tracemalloc.start()
            try:
                normalized = hyphenate_command_refs(sample)
                _, peak = tracemalloc.get_traced_memory()
            finally:
                tracemalloc.stop()
            assert normalized.rstrip("\n").endswith("Run /speckit-git-status")
            assert peak < 4 * len(sample), f"excessive peak memory: {peak} bytes"

    def test_round5_hash_dirs_spaced_dotted_dirs_arbitrary_suffixes_and_punct_prose(
        self, tmp_path
    ):
        """# dirs, spaced dotted dirs, arbitrary spaced suffixes, and punctuated prose."""
        assert (
            hyphenate_command_refs("Open C:\\C#\\speckit.git.commit.md")
            == "Open C:\\C#\\speckit.git.commit.md"
        )
        assert (
            hyphenate_command_refs('"speckit.demo files/commands/speckit.git.commit.md"')
            == '"speckit.demo files/commands/speckit.git.commit.md"'
        )
        assert (
            hyphenate_command_refs('"scripts/v1.0 speckit.git.commit.sh"')
            == '"scripts/v1.0 speckit.git.commit.sh"'
        )
        assert (
            hyphenate_command_refs('"migrations/my speckit.schema.sql"')
            == '"migrations/my speckit.schema.sql"'
        )
        assert (
            hyphenate_command_refs('"Run speckit.plan. Then read docs/usage.md"')
            == '"Run speckit-plan. Then read docs/usage.md"'
        )
        assert (
            hyphenate_command_refs('"Run `speckit.plan` then read docs/setup.md"')
            == '"Run `speckit-plan` then read docs/setup.md"'
        )

        fm_in = {
            "csharp": "C:\\C#\\speckit.git.commit.md",
            "dotted_dir": "speckit.demo files/commands/speckit.git.commit.md",
            "versioned": "scripts/v1.0 speckit.git.commit.sh",
            "migration": "migrations/my speckit.schema.sql",
            "sentence": "Run speckit.plan. Then read docs/usage.md",
            "backticked": "Run `speckit.plan` then read docs/setup.md",
        }
        assert _hyphenate_frontmatter_refs(fm_in) == {
            "csharp": "C:\\C#\\speckit.git.commit.md",
            "dotted_dir": "speckit.demo files/commands/speckit.git.commit.md",
            "versioned": "scripts/v1.0 speckit.git.commit.sh",
            "migration": "migrations/my speckit.schema.sql",
            "sentence": "Run speckit-plan. Then read docs/usage.md",
            "backticked": "Run `speckit-plan` then read docs/setup.md",
        }

        text = self._register_junie_command(
            tmp_path,
            "git",
            'Invoke {SCRIPT}, Open C:\\C#\\speckit.git.commit.md, '
            '"speckit.demo files/commands/speckit.git.commit.md", '
            '"migrations/my speckit.schema.sql", "Run speckit.plan. Then read docs/usage.md", '
            'and "Run `speckit.plan` then read docs/setup.md".\n',
            frontmatter=(
                "scripts:\n"
                '  sh: \'"scripts/v1.0 speckit.git.commit.sh" "{ARGS}"\'\n'
                "csharp: C:\\C#\\speckit.git.commit.md\n"
                "dotted_dir: speckit.demo files/commands/speckit.git.commit.md\n"
                "migration: migrations/my speckit.schema.sql\n"
                'sentence: "Run speckit.plan. Then read docs/usage.md"\n'
                'backticked: "Run `speckit.plan` then read docs/setup.md"\n'
            ),
            extension_id="git",
        )
        assert "Open C:\\C#\\speckit.git.commit.md" in text
        assert '"speckit.demo files/commands/speckit.git.commit.md"' in text
        assert '"migrations/my speckit.schema.sql"' in text
        assert '"Run speckit-plan. Then read docs/usage.md"' in text
        assert '"Run `speckit-plan` then read docs/setup.md"' in text
        assert "csharp: C:\\C#\\speckit.git.commit.md" in text
        assert "dotted_dir: speckit.demo files/commands/speckit.git.commit.md" in text
        assert "migration: migrations/my speckit.schema.sql" in text
        assert "sentence: Run speckit-plan. Then read docs/usage.md" in text
        assert "backticked: Run `speckit-plan` then read docs/setup.md" in text
        assert '".specify/extensions/git/scripts/v1.0 speckit.git.commit.sh" "$ARGUMENTS"' in text

    def test_junie_hook_instruction_injection(self):
        """Verify junie injects the dot-to-hyphen note for hooks."""
        junie = get_integration("junie")
        content = "- For each executable hook, output the following:\n"
        injected = junie._inject_hook_command_note(content)
        assert "replace dots (`.`) with hyphens (`-`)" in injected
        assert "- For each executable hook, output the following:" in injected

    def test_junie_hook_instruction_injection_no_trailing_newline(self):
        """Note must not collapse onto the instruction line when the
        instruction is the final line with no trailing newline.

        The injection regex matches the end-of-line via ``(\\r\\n|\\n|$)``, so
        the captured ``eol`` is empty on a file's last line that lacks a
        trailing newline. Without an ``or "\\n"`` fallback the note text and
        the instruction are emitted on the same line.
        """
        junie = get_integration("junie")
        content = "- For each executable hook, output the following:"  # no trailing \n
        injected = junie._inject_hook_command_note(content)
        assert "replace dots (`.`) with hyphens (`-`)" in injected
        # Instruction stays on its own line rather than being mashed onto the note.
        assert "\n- For each executable hook, output the following:" in injected

    def test_init_next_steps_show_hyphenated_commands(self, tmp_path):
        """Next Steps must list the `/speckit-<name>` commands Junie installs."""
        from typer.testing import CliRunner

        from specify_cli import app

        result = CliRunner().invoke(
            app,
            [
                "init",
                str(tmp_path / "junie-next-steps"),
                "--integration",
                self.KEY,
                "--script",
                "sh",
                "--ignore-agent-tools",
            ],
            catch_exceptions=False,
        )

        assert result.exit_code == 0, result.output
        assert "/speckit-plan" in result.output
        assert "/speckit.plan" not in result.output

    def test_build_exec_args_passes_prompt_as_task(self):
        """Junie's `-p` is `--project <path>`; the prompt goes to `--task`."""
        integration = get_integration(self.KEY)

        args = integration.build_exec_args(
            "/speckit-specify build a login page",
            output_json=False,
        )

        assert args == ["junie", "--task", "/speckit-specify build a login page"]
        assert "-p" not in args

    def test_build_exec_args_requests_json_output(self):
        integration = get_integration(self.KEY)

        args = integration.build_exec_args("/speckit-plan add OAuth", output_json=True)

        assert args == [
            "junie",
            "--task",
            "/speckit-plan add OAuth",
            "--output-format",
            "json",
        ]

    def test_build_exec_args_forwards_model(self):
        integration = get_integration(self.KEY)

        args = integration.build_exec_args(
            "/speckit-specify build a login page",
            model="sonnet",
            output_json=False,
        )

        assert args == [
            "junie",
            "--task",
            "/speckit-specify build a login page",
            "--model",
            "sonnet",
        ]

    def test_build_exec_args_applies_extra_args(self, monkeypatch):
        monkeypatch.setenv("SPECKIT_INTEGRATION_JUNIE_EXTRA_ARGS", "--skip-update-check")
        integration = get_integration(self.KEY)

        args = integration.build_exec_args(
            "check the build", model="sonnet", output_json=True
        )

        assert args == [
            "junie",
            "--task",
            "check the build",
            "--skip-update-check",
            "--model",
            "sonnet",
            "--output-format",
            "json",
        ]

    # -- Overrides for MarkdownIntegrationTests ---------------------------

    def test_setup_creates_files(self, tmp_path):
        from specify_cli.integrations.manifest import IntegrationManifest

        i = get_integration(self.KEY)
        m = IntegrationManifest(self.KEY, tmp_path)
        created = i.setup(tmp_path, m)
        assert len(created) > 0
        cmd_files = [
            f
            for f in created
            if "scripts" not in f.parts
               and f.suffix == ".md"
        ]
        for f in cmd_files:
            assert f.exists()
            assert f.name.startswith("speckit-")
            assert f.name.endswith(".md")

        specify_file = next(
            (f for f in cmd_files if f.name == "speckit-specify.md"), None
        )
        assert specify_file is not None
        specify_contents = specify_file.read_text(encoding="utf-8")
        assert "/speckit-plan" in specify_contents
        assert "/speckit.plan" not in specify_contents

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
        assert result.exit_code == 0
        i = get_integration(self.KEY)
        cmd_dir = i.commands_dest(project)
        assert cmd_dir.is_dir()
        commands = sorted(cmd_dir.glob("speckit-*"))
        assert len(commands) > 0

    def _expected_files(self, script_variant: str) -> list[str]:
        """Override to expect hyphenated speckit- prefix."""
        i = get_integration(self.KEY)
        cmd_dir = i.registrar_config["dir"]
        files = []

        # Command files
        for stem in (
            self.COMMANDS_SUBDIR_STEMS
            if hasattr(self, "COMMANDS_SUBDIR_STEMS")
            else self.COMMAND_STEMS
        ):
            files.append(f"{cmd_dir}/speckit-{stem.replace('.', '-')}.md")

        # Framework files
        files.append(".specify/integration.json")
        files.append(".specify/init-options.json")
        files.append(f".specify/integrations/{self.KEY}.manifest.json")
        files.append(".specify/integrations/speckit.manifest.json")
        files.append(".specify/.gitignore")

        if script_variant == "sh":
            for name in [
                "check-prerequisites.sh",
                "common.sh",
                "create-new-feature.sh",
                "markdown_sections.py",
                "resolve-template.sh",
                "setup-plan.sh",
                "setup-tasks.sh",
            ]:
                files.append(f".specify/scripts/bash/{name}")
        else:
            for name in [
                "check-prerequisites.ps1",
                "common.ps1",
                "create-new-feature.ps1",
                "markdown_sections.py",
                "resolve-template.ps1",
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

        files.append(".specify/memory/.constitution-template.json")
        files.append(".specify/memory/constitution.md")
        # Bundled workflow
        files.append(".specify/workflows/speckit/workflow.yml")
        files.append(".specify/workflows/workflow-registry.json")

        return sorted(files)
