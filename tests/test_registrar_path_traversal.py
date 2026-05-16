"""Tests for CommandRegistrar directory traversal guards around issue #2229."""

import errno
from pathlib import Path

import pytest

from specify_cli.agents import CommandRegistrar


TRAVERSAL_PAYLOADS = [
    "../pwned",
    "../../etc/passwd",
    "subdir/../../escape",
    "/absolute/evil",
]


def _write_source(ext_dir: Path) -> Path:
    ext_dir.mkdir(parents=True, exist_ok=True)
    (ext_dir / "commands").mkdir(exist_ok=True)
    (ext_dir / "commands" / "cmd.md").write_text(
        "---\ndescription: test\n---\n\nbody\n", encoding="utf-8"
    )
    return ext_dir


def _cmd(name: str, aliases: list[str] | None = None) -> dict[str, object]:
    return {
        "name": name,
        "file": "commands/cmd.md",
        "aliases": list(aliases or []),
    }


def _project_and_source(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    ext_dir = _write_source(tmp_path / "ext-src")
    return project, ext_dir


def _assert_no_stray_files(tmp_root: Path, marker: str) -> None:
    """Fail if a file matching ``marker`` exists outside the project tree."""
    stray = [
        p for p in tmp_root.rglob("*")
        if p.is_file() and marker in p.name and "project" not in p.parts
    ]
    assert stray == [], (
        f"Traversal payload leaked files outside the project tree: {stray}"
    )


class TestPrimaryCommandTraversal:
    """Primary command names must not escape the agent's commands directory."""

    @pytest.mark.parametrize("bad_name", TRAVERSAL_PAYLOADS)
    def test_gemini_rejects_traversal_in_primary_name(self, tmp_path, bad_name):
        project, ext_dir = _project_and_source(tmp_path)
        (project / ".gemini" / "commands").mkdir(parents=True)

        registrar = CommandRegistrar()
        with pytest.raises(ValueError, match="escapes|outside|Invalid"):
            registrar.register_commands(
                "gemini", [_cmd(bad_name)], "myext", ext_dir, project
            )

        _assert_no_stray_files(tmp_path, Path(bad_name).name.replace("/", ""))

    @pytest.mark.parametrize("bad_name", TRAVERSAL_PAYLOADS)
    def test_copilot_rejects_traversal_in_primary_name(self, tmp_path, bad_name):
        project, ext_dir = _project_and_source(tmp_path)
        (project / ".github" / "agents").mkdir(parents=True)
        (project / ".github" / "prompts").mkdir(parents=True)

        registrar = CommandRegistrar()
        with pytest.raises(ValueError, match="escapes|outside|Invalid"):
            registrar.register_commands(
                "copilot", [_cmd(bad_name)], "myext", ext_dir, project
            )

        _assert_no_stray_files(tmp_path, Path(bad_name).name.replace("/", ""))


class TestAliasTraversal:
    """Free-form aliases must not escape commands_dir (regression for b67b285)."""

    @pytest.mark.parametrize("bad_alias", TRAVERSAL_PAYLOADS)
    def test_gemini_rejects_traversal_in_alias(self, tmp_path, bad_alias):
        project, ext_dir = _project_and_source(tmp_path)
        (project / ".gemini" / "commands").mkdir(parents=True)

        registrar = CommandRegistrar()
        with pytest.raises(ValueError, match="escapes|outside|Invalid"):
            registrar.register_commands(
                "gemini",
                [_cmd("speckit.myext.ok", [bad_alias])],
                "myext",
                ext_dir,
                project,
            )

        _assert_no_stray_files(tmp_path, Path(bad_alias).name.replace("/", ""))

    @pytest.mark.parametrize("bad_alias", TRAVERSAL_PAYLOADS)
    def test_copilot_rejects_traversal_in_alias(self, tmp_path, bad_alias):
        project, ext_dir = _project_and_source(tmp_path)
        (project / ".github" / "agents").mkdir(parents=True)
        (project / ".github" / "prompts").mkdir(parents=True)

        registrar = CommandRegistrar()
        with pytest.raises(ValueError, match="escapes|outside|Invalid"):
            registrar.register_commands(
                "copilot",
                [_cmd("speckit.myext.ok", [bad_alias])],
                "myext",
                ext_dir,
                project,
            )

        _assert_no_stray_files(tmp_path, Path(bad_alias).name.replace("/", ""))


class TestSourceFileTraversal:
    """Command source files must stay inside the declared source directory."""

    @pytest.mark.parametrize("bad_file", TRAVERSAL_PAYLOADS)
    def test_rejects_traversal_in_command_source_file(self, tmp_path, bad_file):
        project, ext_dir = _project_and_source(tmp_path)
        (project / ".gemini" / "commands").mkdir(parents=True)

        registrar = CommandRegistrar()
        with pytest.raises(ValueError, match="escapes directory"):
            registrar.register_commands(
                "gemini",
                [
                    {
                        "name": "speckit.myext.ok",
                        "file": bad_file,
                        "aliases": [],
                    }
                ],
                "myext",
                ext_dir,
                project,
            )


class TestCopilotPromptTraversal:
    """`write_copilot_prompt` is a public static method — guard it directly."""

    @pytest.mark.parametrize("bad_name", TRAVERSAL_PAYLOADS)
    def test_rejects_traversal_names(self, tmp_path, bad_name):
        project = tmp_path / "project"
        (project / ".github" / "prompts").mkdir(parents=True)

        with pytest.raises(ValueError, match="escapes|outside|Invalid"):
            CommandRegistrar.write_copilot_prompt(project, bad_name)

        _assert_no_stray_files(tmp_path, Path(bad_name).name.replace("/", ""))


class TestSafeRegistration:
    """Positive regression — well-formed names continue to register."""

    def test_symlinked_subdir_under_commands_dir_is_preserved(self, tmp_path):
        """Lexical check must not block legitimately symlinked sub-directories.

        Teams sometimes symlink shared skills into their agent commands dir
        (e.g. ``.gemini/commands/shared -> /team/shared-commands``). The
        guard is purely lexical, so such a setup continues to work even though
        the resolved target lives outside commands_dir on disk.
        """
        project, ext_dir = _project_and_source(tmp_path)
        commands_dir = project / ".gemini" / "commands"
        commands_dir.mkdir(parents=True)

        external_shared = tmp_path / "external-shared"
        external_shared.mkdir()
        try:
            (commands_dir / "shared").symlink_to(
                external_shared, target_is_directory=True
            )
        except OSError as exc:
            if exc.errno in {errno.EPERM, errno.EACCES}:
                pytest.skip("symlink creation is not permitted in this environment")
            raise

        registrar = CommandRegistrar()
        registered = registrar.register_commands(
            "gemini",
            [_cmd("shared/hello")],
            "myext",
            ext_dir,
            project,
        )

        assert registered == ["shared/hello"]
        assert (external_shared / "hello.toml").exists()

    def test_safe_command_and_alias_still_register(self, tmp_path):
        project, ext_dir = _project_and_source(tmp_path)
        (project / ".claude" / "skills").mkdir(parents=True)

        registrar = CommandRegistrar()
        registered = registrar.register_commands(
            "claude",
            [_cmd("speckit.myext.hello", ["speckit.myext.hi"])],
            "myext",
            ext_dir,
            project,
        )

        assert "speckit.myext.hello" in registered
        assert "speckit.myext.hi" in registered
        assert (
            project
            / ".claude"
            / "skills"
            / "speckit-myext-hello"
            / "SKILL.md"
        ).exists()
        assert (
            project
            / ".claude"
            / "skills"
            / "speckit-myext-hi"
            / "SKILL.md"
        ).exists()
