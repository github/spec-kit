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
    ]

    commands_dir = None
    for location in possible_locations:
        if location.exists():
            commands_dir = location
            break

    if commands_dir is None:
        return

    # Define which commands to process and their corresponding command names
    command_mappings = {
        "specify.md": "specify",
        "plan.md": "plan",
        "tasks.md": "tasks",
        "constitution.md": "constitution",
        "clarify.md": "clarify",
        "analyze.md": "analyze",
        "implement.md": "implement"
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

        # Check if already processed (avoid double processing)
        if "{{LANGUAGE_INSTRUCTION}}" in content:
            # Template already has placeholders, just inject
            processed_content = inject_language_instructions(content, command_name, locale)
        else:
            # Add language instruction placeholder after the frontmatter
            processed_content = _add_language_placeholder(content, command_name, locale)

        # Write back the processed content
        with open(template_file, 'w', encoding='utf-8') as f:
            f.write(processed_content)

    except Exception as e:
        # Silently skip files that can't be processed
        pass


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

        # Add instruction after frontmatter
        result_lines = before_frontmatter + ['', instruction_content, ''] + after_frontmatter
        return '\n'.join(result_lines)

    return content


def apply_language_to_commands(project_path: Path, locale: str) -> None:
    """
    Apply language settings to all command templates in the project.
    Main entry point for template processing.

    Args:
        project_path: Path to the project directory
        locale: Target locale
    """
    process_command_templates(project_path, locale)