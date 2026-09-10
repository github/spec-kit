"""specify init must copy core command templates (#3086).

``install_shared_infra`` used to iterate only top-level files under
``templates/``, so ``templates/commands/`` never landed in
``.specify/templates/commands/``. Wrap presets then had no core base layer.
"""

from __future__ import annotations

from pathlib import Path

from rich.console import Console

from specify_cli.shared_infra import (
    install_shared_infra,
    refresh_shared_templates,
    shared_commands_source,
)


def _console() -> Console:
    return Console(quiet=True)


def test_shared_commands_source_prefers_wheel_core_pack(tmp_path: Path) -> None:
    core_pack = tmp_path / "core_pack"
    (core_pack / "commands").mkdir(parents=True)
    (core_pack / "commands" / "implement.md").write_text("# impl\n", encoding="utf-8")
    repo_root = tmp_path / "repo"
    (repo_root / "templates" / "commands").mkdir(parents=True)

    source = shared_commands_source(core_pack=core_pack, repo_root=repo_root)
    assert source == core_pack / "commands"


def test_shared_commands_source_falls_back_to_repo_templates(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    commands = repo_root / "templates" / "commands"
    commands.mkdir(parents=True)
    (commands / "specify.md").write_text("# spec\n", encoding="utf-8")

    source = shared_commands_source(core_pack=None, repo_root=repo_root)
    assert source == commands


def test_install_shared_infra_copies_command_templates(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    commands_src = repo_root / "templates" / "commands"
    commands_src.mkdir(parents=True)
    (commands_src / "implement.md").write_text("# implement\n", encoding="utf-8")
    (commands_src / "specify.md").write_text("# specify\n", encoding="utf-8")
    (repo_root / "templates").mkdir(parents=True, exist_ok=True)
    (repo_root / "templates" / "plan-template.md").write_text("# plan\n", encoding="utf-8")
    scripts = repo_root / "scripts" / "bash"
    scripts.mkdir(parents=True)
    (scripts / "check-prerequisites.sh").write_text("#!/bin/sh\n", encoding="utf-8")

    project = tmp_path / "proj"
    project.mkdir()
    install_shared_infra(
        project,
        "sh",
        version="test",
        core_pack=None,
        repo_root=repo_root,
        console=_console(),
        force=True,
    )

    dest = project / ".specify" / "templates" / "commands"
    assert (dest / "implement.md").is_file()
    assert (dest / "specify.md").is_file()
    assert (dest / "implement.md").read_text(encoding="utf-8") == "# implement\n"


def test_install_shared_infra_copies_wheel_core_pack_commands(tmp_path: Path) -> None:
    core_pack = tmp_path / "core_pack"
    (core_pack / "commands").mkdir(parents=True)
    (core_pack / "commands" / "plan.md").write_text("# plan cmd\n", encoding="utf-8")
    (core_pack / "templates").mkdir(parents=True)
    (core_pack / "templates" / "spec-template.md").write_text("# spec tmpl\n", encoding="utf-8")
    (core_pack / "scripts" / "bash").mkdir(parents=True)
    (core_pack / "scripts" / "bash" / "check-prerequisites.sh").write_text(
        "#!/bin/sh\n", encoding="utf-8"
    )

    project = tmp_path / "proj"
    project.mkdir()
    install_shared_infra(
        project,
        "sh",
        version="test",
        core_pack=core_pack,
        repo_root=tmp_path / "unused",
        console=_console(),
        force=True,
    )

    dest = project / ".specify" / "templates" / "commands" / "plan.md"
    assert dest.is_file()
    assert dest.read_text(encoding="utf-8") == "# plan cmd\n"


def test_refresh_shared_templates_updates_commands(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    commands_src = repo_root / "templates" / "commands"
    commands_src.mkdir(parents=True)
    (commands_src / "clarify.md").write_text("# old\n", encoding="utf-8")
    (repo_root / "templates" / "plan-template.md").write_text("# plan\n", encoding="utf-8")
    scripts = repo_root / "scripts" / "bash"
    scripts.mkdir(parents=True)
    (scripts / "check-prerequisites.sh").write_text("#!/bin/sh\n", encoding="utf-8")

    project = tmp_path / "proj"
    project.mkdir()
    install_shared_infra(
        project,
        "sh",
        version="test",
        core_pack=None,
        repo_root=repo_root,
        console=_console(),
        force=True,
    )
    (commands_src / "clarify.md").write_text("# new\n", encoding="utf-8")

    refresh_shared_templates(
        project,
        version="test",
        core_pack=None,
        repo_root=repo_root,
        console=_console(),
        invoke_separator=".",
        force=True,
    )

    dest = project / ".specify" / "templates" / "commands" / "clarify.md"
    assert dest.read_text(encoding="utf-8") == "# new\n"
