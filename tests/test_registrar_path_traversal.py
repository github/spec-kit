"""Tests for CommandRegistrar directory traversal guards around issue #2229."""

import errno
from pathlib import Path

import pytest

from specify_cli.agents import CommandRegistrar
from specify_cli._utils import relative_extension_path_violation


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


class TestCopilotPromptTraversal:
    """`write_copilot_prompt` is a public static method — guard it directly."""

    @pytest.mark.parametrize("bad_name", TRAVERSAL_PAYLOADS)
    def test_rejects_traversal_names(self, tmp_path, bad_name):
        project = tmp_path / "project"
        (project / ".github" / "prompts").mkdir(parents=True)

        with pytest.raises(ValueError, match="escapes|outside|Invalid"):
            CommandRegistrar.write_copilot_prompt(project, bad_name)

        _assert_no_stray_files(tmp_path, Path(bad_name).name.replace("/", ""))


ABS_OUTSIDE = "__ABS_OUTSIDE__"

FILE_FIELD_PAYLOADS = [
    "../outside.txt",
    "../../outside.txt",
    "commands/../../outside.txt",
    "C:outside.txt",
    ABS_OUTSIDE,
]


def _resolve_payload(bad_file: str, outside_file: Path) -> str:
    """Map the absolute-path sentinel to the real, existing outside file.

    Using the temp file's own absolute path (instead of ``/etc/passwd``)
    guarantees the file exists on every platform — so the test fails if the
    absolute-path guard regresses, rather than passing because the target
    happens not to exist (e.g. on Windows runners).
    """
    return str(outside_file) if bad_file == ABS_OUTSIDE else bad_file


def _assert_no_marker_leak(project: Path, marker: str) -> None:
    """Fail if ``marker`` content was written into any file under ``project``."""
    leaked = [
        p for p in project.rglob("*")
        if p.is_file() and marker in p.read_text(encoding="utf-8", errors="ignore")
    ]
    assert leaked == [], f"Outside file leaked into generated command: {leaked}"


class TestCommandFileTraversal:
    """The manifest ``file`` field must not read files outside source_dir.

    Regression for GHSA-w5fv-7w9x-7fc5: ``register_commands`` read
    ``source_dir / cmd_file`` with no containment check, so a manifest with
    a traversal (``file: ../../../outside.txt``) or an absolute path read an
    arbitrary host file verbatim into the generated agent command.
    """

    @pytest.mark.parametrize("bad_file", FILE_FIELD_PAYLOADS)
    def test_claude_skips_traversal_in_file_field(self, tmp_path, bad_file):
        project, ext_dir = _project_and_source(tmp_path)
        (project / ".claude" / "skills").mkdir(parents=True)

        outside_file = tmp_path / "outside.txt"
        outside_file.write_text("OUTSIDE-FILE-MARKER", encoding="utf-8")

        registrar = CommandRegistrar()
        registered = registrar.register_commands(
            "claude",
            [{"name": "speckit.myext.hello", "file": _resolve_payload(bad_file, outside_file), "aliases": []}],
            "myext",
            ext_dir,
            project,
        )

        assert registered == []
        _assert_no_marker_leak(project, "OUTSIDE-FILE-MARKER")

    @pytest.mark.parametrize("bad_file", FILE_FIELD_PAYLOADS)
    def test_gemini_skips_traversal_in_file_field(self, tmp_path, bad_file):
        project, ext_dir = _project_and_source(tmp_path)
        (project / ".gemini" / "commands").mkdir(parents=True)

        outside_file = tmp_path / "outside.txt"
        outside_file.write_text("OUTSIDE-FILE-MARKER", encoding="utf-8")

        registrar = CommandRegistrar()
        registered = registrar.register_commands(
            "gemini",
            [{"name": "speckit.myext.hello", "file": _resolve_payload(bad_file, outside_file), "aliases": []}],
            "myext",
            ext_dir,
            project,
        )

        assert registered == []
        _assert_no_marker_leak(project, "OUTSIDE-FILE-MARKER")

    @pytest.mark.parametrize("bad_value", [None, 123, "", ["x"]])
    def test_non_string_file_is_skipped(self, tmp_path, bad_value):
        """A non-string/empty ``file`` must be skipped, not raise TypeError."""
        project, ext_dir = _project_and_source(tmp_path)
        (project / ".gemini" / "commands").mkdir(parents=True)

        registrar = CommandRegistrar()
        registered = registrar.register_commands(
            "gemini",
            [{"name": "speckit.myext.hello", "file": bad_value, "aliases": []}],
            "myext",
            ext_dir,
            project,
        )

        assert registered == []

    def test_dotdot_rejected_even_when_target_is_in_bounds(self, tmp_path):
        """An in-bounds ``..`` payload is rejected by the ``..`` check itself.

        ``commands/../cmd.md`` resolves to ``ext_dir/cmd.md`` — inside
        source_dir — so the resolve()/relative_to() containment backstop would
        allow it. Creating that target file ensures the command is skipped
        because of the ``..`` rejection, not merely because the file is absent.
        """
        project, ext_dir = _project_and_source(tmp_path)
        (project / ".gemini" / "commands").mkdir(parents=True)
        (ext_dir / "cmd.md").write_text(
            "---\ndescription: test\n---\n\nbody\n", encoding="utf-8"
        )

        registrar = CommandRegistrar()
        registered = registrar.register_commands(
            "gemini",
            [{"name": "speckit.myext.hello", "file": "commands/../cmd.md", "aliases": []}],
            "myext",
            ext_dir,
            project,
        )

        assert registered == []


class TestRelativeExtensionPathPolicy:
    """Unit tests for the shared ``relative_extension_path_violation`` policy."""

    @pytest.mark.parametrize(
        "value",
        [
            "commands/hello.md",
            "hello.md",
            "a/b/c/hello.md",
        ],
    )
    def test_safe_relative_paths_have_no_violation(self, value):
        assert relative_extension_path_violation(value) is None

    @pytest.mark.parametrize(
        "value",
        [
            None,
            123,
            ["x"],
            "",
            "   ",
            " hello.md",
            "hello.md ",
            "/abs/outside.md",
            "/etc/passwd",
            "C:foo.md",
            "C:\\Windows\\system32",
            "\\\\server\\share\\x.md",
            "../escape.md",
            "commands/../../escape.md",
        ],
    )
    def test_unsafe_values_report_violation(self, value):
        assert relative_extension_path_violation(value) is not None


class TestReadSkipWarning:
    """Unregisterable but in-bounds files warn instead of failing silently."""

    def test_unreadable_target_warns_and_skips(self, tmp_path):
        project, ext_dir = _project_and_source(tmp_path)
        (project / ".gemini" / "commands").mkdir(parents=True)
        (ext_dir / "cmd.md").write_bytes(b"\xff\xfe\x00\x80bad")

        registrar = CommandRegistrar()
        with pytest.warns(UserWarning):
            registered = registrar.register_commands(
                "gemini",
                [{"name": "speckit.myext.hello", "file": "cmd.md", "aliases": []}],
                "myext",
                ext_dir,
                project,
            )

        assert registered == []

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
