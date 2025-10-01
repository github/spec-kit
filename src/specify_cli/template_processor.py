"""
Template processing for language localization.
Handles post-processing of downloaded templates to inject language instructions.
"""

from pathlib import Path
from typing import Optional

from .locale import inject_language_instructions, get_locale_manager


def process_command_templates(project_path: Path, locale: str = None) -> None:
    """
    Process all command templates in the project to inject language instructions.

    Args:
        project_path: Path to the project directory
        locale: Target locale (defaults to current locale)
    """
    if locale is None:
        locale = get_locale_manager().current_locale

    # Skip processing for English (default language)
    if locale == "en":
        return

    # Try different possible locations for command templates
    possible_locations = [
        project_path / ".specify" / "templates" / "commands",
        project_path / ".claude" / "commands",
        project_path / ".gemini" / "commands",
        project_path / ".cursor" / "commands",
        project_path / ".github" / "prompts",  # GitHub Copilot
    ]

    commands_dir = None
    for location in possible_locations:
        if location.exists():
            commands_dir = location
            break

    if commands_dir is None:
        return

    # Define which commands to process and their corresponding command names
    # Support: .md (Claude/Cursor), .prompt.md (GitHub Copilot), .toml (Gemini)
    command_mappings = {
        "specify.md": "specify",
        "specify.prompt.md": "specify",
        "specify.toml": "specify",
        "plan.md": "plan",
        "plan.prompt.md": "plan",
        "plan.toml": "plan",
        "tasks.md": "tasks",
        "tasks.prompt.md": "tasks",
        "tasks.toml": "tasks",
        "constitution.md": "constitution",
        "constitution.prompt.md": "constitution",
        "constitution.toml": "constitution",
        "clarify.md": "clarify",
        "clarify.prompt.md": "clarify",
        "clarify.toml": "clarify",
        "analyze.md": "analyze",
        "analyze.prompt.md": "analyze",
        "analyze.toml": "analyze",
        "implement.md": "implement",
        "implement.prompt.md": "implement",
        "implement.toml": "implement"
    }

    for filename, command_name in command_mappings.items():
        template_file = commands_dir / filename
        if template_file.exists():
            _process_single_template(template_file, command_name, locale)


def _process_single_template(template_file: Path, command_name: str, locale: str) -> None:
    """
    Process a single command template file.

    Args:
        template_file: Path to the template file
        command_name: Name of the command (e.g., 'specify', 'plan')
        locale: Target locale
    """
    try:
        # Read current content
        with open(template_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Handle TOML files differently (Gemini CLI uses TOML format)
        if template_file.suffix == '.toml':
            processed_content = _process_toml_template(content, command_name, locale)
        # Check if already processed (avoid double processing)
        elif "{{LANGUAGE_INSTRUCTION}}" in content:
            # Template already has placeholders, just inject
            processed_content = inject_language_instructions(content, command_name, locale)
        else:
            # Add language instruction placeholder after the frontmatter
            processed_content = _add_language_placeholder(content, command_name, locale)

        # Write back the processed content
        with open(template_file, 'w', encoding='utf-8') as f:
            f.write(processed_content)

    except (IOError, UnicodeDecodeError, ValueError) as e:
        # Skip files that can't be read or processed, but log the issue
        try:
            from rich.console import Console
            console = Console()
            console.print(f"[yellow]Warning: Could not process template {template_file}: {e}[/yellow]")
        except ImportError:
            pass  # Silently skip if rich is not available


def _process_toml_template(content: str, command_name: str, locale: str) -> str:
    """
    Process TOML template files (used by Gemini CLI).
    TOML format: prompt = triple-quoted string

    Args:
        content: TOML file content
        command_name: Name of the command
        locale: Target locale

    Returns:
        Processed TOML content with language instructions
    """
    import re
    from .locale import get_locale_manager

    # Get language instructions
    lm = get_locale_manager()
    lm.set_locale(locale)

    general_instruction = lm.get_text("ai_instructions.general")
    command_instruction = lm.get_text(f"ai_instructions.commands.{command_name}")
    footer_reminder = lm.get_text("ai_instructions.footer_reminder")

    # Build header instruction
    header_parts = []
    if general_instruction:
        header_parts.append(general_instruction)
    if command_instruction:
        header_parts.append(command_instruction)

    header_instruction = "\n\n".join(header_parts) if header_parts else ""

    # Find prompt = """...""" pattern
    prompt_pattern = r'(prompt\s*=\s*""")(.*?)(""")'

    def replace_prompt(match):
        prefix = match.group(1)
        prompt_content = match.group(2)
        suffix = match.group(3)

        # Add header after opening """
        new_content = prompt_content
        if header_instruction:
            # Insert after frontmatter if exists, otherwise at beginning
            lines = prompt_content.split('\n')
            frontmatter_end = -1
            frontmatter_count = 0

            for i, line in enumerate(lines):
                if line.strip() == '---':
                    frontmatter_count += 1
                    if frontmatter_count == 2:
                        frontmatter_end = i
                        break

            if frontmatter_end >= 0:
                # Insert after frontmatter
                before = '\n'.join(lines[:frontmatter_end + 1])
                after = '\n'.join(lines[frontmatter_end + 1:])
                new_content = f"{before}\n\n{header_instruction}\n{after}"
            else:
                # Insert at beginning
                new_content = f"\n{header_instruction}\n{prompt_content}"

        # Add footer before closing """
        if footer_reminder:
            new_content = new_content.rstrip() + "\n" + footer_reminder + "\n"

        return prefix + new_content + suffix

    # Apply replacement
    result = re.sub(prompt_pattern, replace_prompt, content, flags=re.DOTALL)
    return result


def _add_language_placeholder(content: str, command_name: str, locale: str) -> str:
    """
    Add language instruction placeholder to template content.

    Args:
        content: Original template content
        command_name: Name of the command
        locale: Target locale

    Returns:
        Content with language placeholder added
    """
    lines = content.split('\n')

    # Find the end of frontmatter (marked by second ---)
    frontmatter_end = -1
    frontmatter_count = 0

    for i, line in enumerate(lines):
        if line.strip() == '---':
            frontmatter_count += 1
            if frontmatter_count == 2:
                frontmatter_end = i
                break

    if frontmatter_end == -1:
        # No frontmatter found, add at the beginning
        instruction_content = inject_language_instructions("{{LANGUAGE_INSTRUCTION}}", command_name, locale)
        if instruction_content.strip():
            return f"{instruction_content}\n\n{content}"
        return content

    # Insert language instruction after frontmatter
    instruction_content = inject_language_instructions("{{LANGUAGE_INSTRUCTION}}", command_name, locale)

    if instruction_content.strip():
        before_frontmatter = lines[:frontmatter_end + 1]
        after_frontmatter = lines[frontmatter_end + 1:]

        # Add instruction after frontmatter and footer at the end
        result_lines = before_frontmatter + ['', instruction_content, ''] + after_frontmatter
        result = '\n'.join(result_lines)

        # Add footer reminder at the end
        from .locale import get_locale_manager
        lm = get_locale_manager()
        lm.set_locale(locale)
        footer_reminder = lm.get_text("ai_instructions.footer_reminder")
        if footer_reminder and footer_reminder.strip():
            result = result + "\n" + footer_reminder

        return result

    return content


def create_claude_language_guide(project_path: Path, locale: str) -> None:
    """
    Create or update .claude/CLAUDE.md with language-specific instructions.
    This ensures Claude Code uses the correct language in all conversations.

    Args:
        project_path: Path to the project directory
        locale: Target locale
    """
    if locale == "en":
        return  # No need for English (default)

    claude_dir = project_path / ".claude"
    claude_md = claude_dir / "CLAUDE.md"

    # Get language instructions
    lm = get_locale_manager()
    lm.set_locale(locale)

    general_instruction = lm.get_text("ai_instructions.general")
    guidelines_header = lm.get_text("ai_instructions.guidelines_header")

    # Get guidelines as list (get_text converts to string, so we need to access directly)
    locale_data = lm._load_locale(locale)
    guidelines = locale_data.get("ai_instructions", {}).get("guidelines", [])

    # Build the CLAUDE.md content
    content_parts = []

    # Add header
    language_name = {
        "ko": "한국어 (Korean)",
        "ja": "日本語 (Japanese)",
        "zh": "中文 (Chinese)",
        "es": "Español (Spanish)",
        "fr": "Français (French)",
        "de": "Deutsch (German)",
    }.get(locale, locale.upper())

    content_parts.append(f"# Project Language: {language_name}\n")

    # Add general instruction
    if general_instruction:
        content_parts.append(general_instruction)

    # Add guidelines
    if guidelines and isinstance(guidelines, list) and guidelines_header:
        content_parts.append(f"\n{guidelines_header}")
        for guideline in guidelines:
            content_parts.append(f"- {guideline}")

    # Combine all parts
    content = "\n".join(content_parts)

    # Create .claude directory if it doesn't exist
    claude_dir.mkdir(parents=True, exist_ok=True)

    # Write the CLAUDE.md file
    try:
        with open(claude_md, 'w', encoding='utf-8') as f:
            f.write(content)
    except (IOError, PermissionError) as e:
        try:
            from rich.console import Console
            console = Console()
            console.print(f"[yellow]Warning: Could not create {claude_md}: {e}[/yellow]")
        except ImportError:
            pass


def apply_language_to_commands(project_path: Path, locale: str) -> None:
    """
    Apply language settings to all command templates in the project.
    Main entry point for template processing.

    Args:
        project_path: Path to the project directory
        locale: Target locale
    """
    # Process command templates
    process_command_templates(project_path, locale)

    # Create Claude language guide for Claude Code
    create_claude_language_guide(project_path, locale)