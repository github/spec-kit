from __future__ import annotations

import re
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

AGENT_OUTPUT = {
    "claude": (".claude/commands", "md", "$ARGUMENTS"),
    "gemini": (".gemini/commands", "toml", "{{args}}"),
    "copilot": (".github/agents", "agent.md", "$ARGUMENTS"),
    "cursor-agent": (".cursor/commands", "md", "$ARGUMENTS"),
    "qwen": (".qwen/commands", "toml", "{{args}}"),
    "opencode": (".opencode/command", "md", "$ARGUMENTS"),
    "windsurf": (".windsurf/workflows", "md", "$ARGUMENTS"),
    "codex": (".codex/prompts", "md", "$ARGUMENTS"),
    "kilocode": (".kilocode/workflows", "md", "$ARGUMENTS"),
    "auggie": (".augment/commands", "md", "$ARGUMENTS"),
    "roo": (".roo/commands", "md", "$ARGUMENTS"),
    "codebuddy": (".codebuddy/commands", "md", "$ARGUMENTS"),
    "qoder": (".qoder/commands", "md", "$ARGUMENTS"),
    "amp": (".agents/commands", "md", "$ARGUMENTS"),
    "shai": (".shai/commands", "md", "$ARGUMENTS"),
    "q": (".amazonq/prompts", "md", "$ARGUMENTS"),
    "bob": (".bob/commands", "md", "$ARGUMENTS"),
}


@dataclass
class TemplateParseResult:
    description: str
    script_command: str | None
    agent_script_command: str | None
    content: str


class TemplatePackagerError(RuntimeError):
    pass


def _normalize_newlines(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n")


def _split_frontmatter(content: str) -> tuple[str | None, str]:
    if not content.startswith("---\n"):
        return None, content
    parts = content.split("---\n", 2)
    if len(parts) < 3:
        return None, content
    _, frontmatter, rest = parts
    return frontmatter, rest


def _extract_description(frontmatter_lines: Iterable[str]) -> str:
    for line in frontmatter_lines:
        match = re.match(r"^description:\s*(.*)$", line.strip())
        if match:
            return match.group(1).strip().strip('"')
    return ""


def _extract_script(frontmatter_lines: list[str], script_variant: str, *, block_name: str) -> str | None:
    in_block = False
    for line in frontmatter_lines:
        stripped = line.strip()
        if stripped == f"{block_name}:":
            in_block = True
            continue
        if in_block and re.match(r"^[A-Za-z_].*:\s*$", stripped):
            in_block = False
        if in_block:
            if stripped.startswith(f"{script_variant}:"):
                return stripped.split(":", 1)[1].strip()
    return None


def _strip_script_blocks(frontmatter_lines: list[str]) -> list[str]:
    filtered: list[str] = []
    skipping = False

    for line in frontmatter_lines:
        stripped = line.strip()
        if stripped in {"scripts:", "agent_scripts:"}:
            skipping = True
            continue

        if skipping:
            if re.match(r"^[A-Za-z_].*:\s*$", stripped):
                skipping = False
                filtered.append(line)
            continue

        filtered.append(line)

    return filtered


def _rewrite_paths(content: str) -> str:
    for name in ("memory", "scripts", "templates"):
        content = re.sub(rf"/?{name}/", f".specify/{name}/", content)
    return content


def parse_template(path: Path, *, script_variant: str) -> TemplateParseResult:
    raw = _normalize_newlines(path.read_text(encoding="utf-8"))
    frontmatter, body = _split_frontmatter(raw)
    if frontmatter is None:
        raise TemplatePackagerError(f"Missing YAML frontmatter in {path}")

    frontmatter_lines = frontmatter.split("\n")
    description = _extract_description(frontmatter_lines)
    script_command = _extract_script(frontmatter_lines, script_variant, block_name="scripts")
    agent_script_command = _extract_script(frontmatter_lines, script_variant, block_name="agent_scripts")

    frontmatter_filtered = "\n".join(_strip_script_blocks(frontmatter_lines)).strip("\n")
    rebuilt = f"---\n{frontmatter_filtered}\n---\n{body.lstrip()}"

    if script_command:
        rebuilt = rebuilt.replace("{SCRIPT}", script_command)
    if agent_script_command:
        rebuilt = rebuilt.replace("{AGENT_SCRIPT}", agent_script_command)

    return TemplateParseResult(
        description=description,
        script_command=script_command,
        agent_script_command=agent_script_command,
        content=rebuilt,
    )


def render_template(
    template: TemplateParseResult,
    *,
    agent: str,
    arg_format: str,
) -> str:
    content = template.content.replace("{ARGS}", arg_format)
    content = content.replace("__AGENT__", agent)
    content = _rewrite_paths(content)
    return content


def write_command_file(
    *,
    output_path: Path,
    extension: str,
    description: str,
    content: str,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if extension == "toml":
        body = content.replace("\\", "\\\\")
        output_path.write_text(
            "\n".join(
                [
                    f"description = \"{description}\"",
                    "",
                    "prompt = \"\"\"",
                    body,
                    "\"\"\"",
                ]
            ),
            encoding="utf-8",
        )
        return

    output_path.write_text(content, encoding="utf-8")


def write_copilot_prompts(agents_dir: Path, prompts_dir: Path) -> None:
    prompts_dir.mkdir(parents=True, exist_ok=True)
    for agent_file in agents_dir.glob("speckit.*.agent.md"):
        basename = agent_file.stem.replace(".agent", "")
        prompt_file = prompts_dir / f"{basename}.prompt.md"
        prompt_file.write_text(
            "\n".join([
                "---",
                f"agent: {basename}",
                "---",
                "",
            ]),
            encoding="utf-8",
        )


def build_commands(
    *,
    templates_dir: Path,
    output_dir: Path,
    agent: str,
    script_variant: str,
    include_vscode_settings: bool = False,
) -> list[Path]:
    if agent not in AGENT_OUTPUT:
        raise TemplatePackagerError(f"Unsupported agent: {agent}")

    commands_dir, extension, arg_format = AGENT_OUTPUT[agent]
    output_commands_dir = output_dir / commands_dir
    templates = sorted(templates_dir.glob("*.md"))
    if not templates:
        raise TemplatePackagerError(f"No command templates found in {templates_dir}")

    written: list[Path] = []

    for template_path in templates:
        result = parse_template(template_path, script_variant=script_variant)
        rendered = render_template(result, agent=agent, arg_format=arg_format)

        if extension == "toml":
            output_name = f"speckit.{template_path.stem}.toml"
        elif extension == "agent.md":
            output_name = f"speckit.{template_path.stem}.agent.md"
        else:
            output_name = f"speckit.{template_path.stem}.md"

        output_path = output_commands_dir / output_name
        write_command_file(
            output_path=output_path,
            extension="toml" if extension == "toml" else "md",
            description=result.description,
            content=rendered,
        )
        written.append(output_path)

    if agent == "copilot":
        write_copilot_prompts(output_commands_dir, output_dir / ".github" / "prompts")
        if include_vscode_settings:
            vscode_settings = Path("templates/vscode-settings.json")
            if vscode_settings.exists():
                dest = output_dir / ".vscode" / "settings.json"
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(vscode_settings, dest)
                written.append(dest)

    return written


def build_commands_for_agents(
    *,
    templates_dir: Path,
    output_dir: Path,
    agents: Iterable[str],
    script_variant: str,
    include_vscode_settings: bool = False,
) -> dict[str, list[Path]]:
    results: dict[str, list[Path]] = {}
    for agent in agents:
        results[agent] = build_commands(
            templates_dir=templates_dir,
            output_dir=output_dir,
            agent=agent,
            script_variant=script_variant,
            include_vscode_settings=include_vscode_settings,
        )
    return results
