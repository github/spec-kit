#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "typer",
#     "rich",
# ]
# ///
"""Story Kit CLI - bootstrap narrative-focused projects using Story-Driven Development."""

from __future__ import annotations

import json
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict

import subprocess

import typer
from rich.align import Align
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

console = Console()

BANNER = """
███████╗████████╗ ██████╗ ██████╗ ██╗   ██╗██╗  ██╗██╗████████╗
██╔════╝╚══██╔══╝██╔═══██╗██╔══██╗██║   ██║██║ ██╔╝██║╚══██╔══╝
███████╗   ██║   ██║   ██║██████╔╝██║   ██║█████╔╝ ██║   ██║   
╚════██║   ██║   ██║   ██║██╔═══╝ ██║   ██║██╔═██╗ ██║   ██║   
███████║   ██║   ╚██████╔╝██║     ╚██████╔╝██║  ██╗██║   ██║   
╚══════╝   ╚═╝    ╚═════╝ ╚═╝      ╚═════╝ ╚═╝  ╚═╝╚═╝   ╚═╝   
"""
TAGLINE = "Story Kit — Structured storytelling with creative autonomy"

AI_CHOICES: Dict[str, str] = {
    "claude": "Claude Code",
    "gemini": "Gemini CLI",
    "copilot": "GitHub Copilot",
    "cursor": "Cursor",
    "qwen": "Qwen Code",
    "opencode": "opencode",
    "windsurf": "Windsurf",
    "kilocode": "Kilo Code",
    "auggie": "Auggie CLI",
    "roo": "Roo Code",
    "codex": "Codex CLI",
}

INTERACTION_CHOICES = {
    "guided": "Stage-gate (ask for approval before each big step)",
    "auto": "Autopilot (run through tasks without stopping)",
    "hybrid": "Hybrid (autopilot drafting, pause for reviews)",
    "sandbox": "Experiment (branching explorations, no canon updates)",
}

BASE_TEMPLATE_DIR = Path(__file__).resolve().parent / "template_root"
CONFIG_DIR_NAME = ".storykit"
CONFIG_FILENAME = "storykit.config.json"

app = typer.Typer(
    name="storyfy",
    help="Bootstrap Story Kit projects",
    add_completion=False,
    invoke_without_command=True,
)


def show_banner() -> None:
    banner_lines = BANNER.strip("\n").splitlines()
    colors = ["magenta", "purple", "violet", "bright_magenta", "white"]
    styled = Text()
    for idx, line in enumerate(banner_lines):
        styled.append(line + "\n", style=colors[idx % len(colors)])
    console.print(Align.center(styled))
    console.print(Align.center(Text(TAGLINE, style="italic bright_yellow")))
    console.print()


@app.callback()
def callback(ctx: typer.Context):
    if ctx.invoked_subcommand is None and "--help" not in sys.argv and "-h" not in sys.argv:
        show_banner()
        console.print(Align.center("[dim]运行 'storyfy --help' 查看命令说明[/dim]"))
        console.print()


def humanize(name: str) -> str:
    if not name:
        return "Unnamed Saga"
    cleaned = name.replace("-", " ").replace("_", " ")
    words = [w.capitalize() for w in cleaned.split() if w]
    return " ".join(words) if words else "Unnamed Saga"


def slugify(value: str) -> str:
    slug = "".join(ch.lower() if ch.isalnum() else "-" for ch in value)
    slug = slug.strip("-")
    while "--" in slug:
        slug = slug.replace("--", "-")
    return slug or "story"


def copy_template(project_path: Path) -> None:
    if not BASE_TEMPLATE_DIR.exists():
        raise RuntimeError(f"缺少模板目录: {BASE_TEMPLATE_DIR}")

    for item in BASE_TEMPLATE_DIR.iterdir():
        dest = project_path / item.name
        if item.is_dir():
            shutil.copytree(item, dest, dirs_exist_ok=True)
        else:
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(item, dest)


def apply_placeholders(project_path: Path, replacements: Dict[str, str]) -> None:
    for path in project_path.rglob("*"):
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        new_text = text
        for key, value in replacements.items():
            new_text = new_text.replace(key, value)
        if new_text != text:
            path.write_text(new_text, encoding="utf-8")


def ensure_executable_scripts(project_path: Path) -> None:
    if os.name == "nt":
        return
    scripts_root = project_path / ".specify" / "scripts"
    if not scripts_root.is_dir():
        return
    for script in scripts_root.rglob("*.sh"):
        if not script.is_file():
            continue
        mode = script.stat().st_mode
        if mode & 0o111:
            continue
        new_mode = mode
        if mode & 0o400:
            new_mode |= 0o100
        if mode & 0o040:
            new_mode |= 0o010
        if mode & 0o004:
            new_mode |= 0o001
        if not (new_mode & 0o100):
            new_mode |= 0o100
        os.chmod(script, new_mode)


def write_config(project_path: Path, data: Dict[str, str]) -> None:
    config_dir = project_path / CONFIG_DIR_NAME
    config_dir.mkdir(parents=True, exist_ok=True)
    config_path = config_dir / CONFIG_FILENAME
    config_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def init_git_repo(project_path: Path) -> bool:
    if shutil.which("git") is None:
        return False
    if (project_path / ".git").exists():
        return False
    try:
        subprocess.run(["git", "init"], cwd=project_path, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except subprocess.CalledProcessError:
        return False


@app.command()
def init(
    project_name: str = typer.Argument(None, help="新项目目录名"),
    story_title: str = typer.Option(None, "--story-title", "-t", help="故事标题 (默认根据目录名生成)"),
    ai_assistant: str = typer.Option(None, "--ai", help="首选 AI 助手"),
    interaction_mode: str = typer.Option("guided", "--interaction", "-i", help="协作模式: guided|auto|hybrid|sandbox"),
    timeline_span: int = typer.Option(50, "--timeline-span", help="每份主时间线概览覆盖的章节数，默认 50"),
    here: bool = typer.Option(False, "--here", help="在当前目录初始化 Story Kit"),
    no_git: bool = typer.Option(False, "--no-git", help="跳过 git 初始化"),
):
    """创建新的 Story Kit 项目。"""
    show_banner()

    if timeline_span <= 0:
        console.print("[red]时间线分段必须为正整数[/red]")
        raise typer.Exit(1)

    if here and project_name:
        console.print("[red]不能同时指定项目名和 --here[/red]")
        raise typer.Exit(1)
    if not here and not project_name:
        console.print("[red]请提供项目名，或使用 --here[/red]")
        raise typer.Exit(1)

    interaction_mode = interaction_mode.lower()
    if interaction_mode not in INTERACTION_CHOICES:
        console.print("[red]无效的协作模式：[/red]" + interaction_mode)
        console.print("可选项: " + ", ".join(INTERACTION_CHOICES))
        raise typer.Exit(1)

    if ai_assistant:
        ai_key = ai_assistant.lower()
        if ai_key not in AI_CHOICES:
            console.print("[red]未知的 AI 助手：[/red]" + ai_assistant)
            console.print("支持: " + ", ".join(AI_CHOICES))
            raise typer.Exit(1)
        ai_assistant = ai_key
    else:
        ai_assistant = "unspecified"
    ai_label = AI_CHOICES.get(ai_assistant, "未指定") if ai_assistant != "unspecified" else "未指定"

    if here:
        project_path = Path.cwd()
        project_name = project_path.name
        if any(project_path.iterdir()):
            console.print("[yellow]提醒：当前目录非空，Story Kit 文件会与现有内容合并。[/yellow]")
    else:
        project_path = (Path.cwd() / project_name).resolve()
        if project_path.exists() and any(project_path.iterdir()):
            console.print("[red]目标目录已存在且非空：[/red]" + str(project_path))
            raise typer.Exit(1)
        project_path.mkdir(parents=True, exist_ok=True)

    story_title = story_title or humanize(project_name)
    story_slug = slugify(story_title)

    console.print(Panel.fit(
        f"项目路径: [cyan]{project_path}[/cyan]\n"
        f"故事标题: [green]{story_title}[/green]\n"
        f"协作模式: [magenta]{interaction_mode}[/magenta]\n"
        f"首选助手: [blue]{ai_label}[/blue]\n"
        f"时间线分段: [yellow]{timeline_span} 章/文件[/yellow]",
        title="Story Kit 设置",
        border_style="cyan",
    ))

    copy_template(project_path)
    timeline_segment_pad = str(timeline_span).zfill(3)

    apply_placeholders(
        project_path,
        {
            "{{STORY_TITLE}}": story_title,
            "{{STORY_SLUG}}": story_slug,
            "{{DEFAULT_INTERACTION_MODE}}": interaction_mode,
            "{{PREFERRED_AI}}": ai_label,
            "{{AI_KEY}}": ai_assistant,
            "{{INITIALIZED_AT}}": datetime.now().strftime("%Y-%m-%d"),
            "{{STRUCTURE_HINT}}": "待定结构",
            "{{TIMELINE_SEGMENT}}": str(timeline_span),
            "{{TIMELINE_SEGMENT_PAD}}": timeline_segment_pad,
        },
    )
    ensure_executable_scripts(project_path)

    config_payload = {
        "story_title": story_title,
        "story_slug": story_slug,
        "preferred_ai": ai_assistant,
        "preferred_ai_label": ai_label,
        "interaction_mode": interaction_mode,
        "initialized_at": datetime.now().isoformat(),
        "timeline_span": timeline_span,
        "timeline_span_pad": timeline_segment_pad,
        "cli_version": "0.1.0",
    }
    write_config(project_path, config_payload)

    git_initialized = False
    if not no_git:
        git_initialized = init_git_repo(project_path)

    console.print()
    steps = Table(grid_style="dim", show_header=False, box=None)
    steps.add_row("1.", "进入目录: [cyan]cd {}[/cyan]".format(project_path))
    steps.add_row("2.", "查看故事宪章: [cyan]memory/constitution.md[/cyan]")
    steps.add_row("3.", "在你的 AI 助手中加载 Story Kit Slash Commands")
    steps.add_row("4.", "从 [cyan]/constitution[/cyan] 开始定义创作原则")
    steps.add_row("5.", "使用 [cyan]/specify[/cyan] 细化故事设定")
    console.print(Panel(steps, title="下一步", border_style="magenta"))

    if git_initialized:
        console.print("[green]已初始化 Git 仓库。[/green]")
    elif not no_git:
        console.print("[yellow]未检测到 git 或初始化失败，可手动运行 git init。[/yellow]")

    console.print("\n祝写作顺利！🌌")


@app.command()
def info():
    """显示可选 AI 助手和协作模式。"""
    show_banner()
    ai_table = Table(title="支持的 AI 助手", show_header=False, box=None)
    for key, label in AI_CHOICES.items():
        ai_table.add_row(f"[cyan]{key}[/cyan]", label)

    mode_table = Table(title="协作模式", show_header=False, box=None)
    for key, desc in INTERACTION_CHOICES.items():
        mode_table.add_row(f"[magenta]{key}[/magenta]", desc)

    console.print(ai_table)
    console.print()
    console.print(mode_table)
    console.print()
    console.print("[dim]默认时间线分段: 50 章，可在 storyfy init 时通过 --timeline-span 调整[/dim]")


def main():
    app()


if __name__ == "__main__":
    main()
