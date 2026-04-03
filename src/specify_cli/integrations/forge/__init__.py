"""Forge integration — forgecode.dev AI coding agent.

Forge has several unique behaviors compared to standard markdown agents:
- Uses `{{parameters}}` instead of `$ARGUMENTS` for argument passing
- Strips `handoffs` frontmatter key (Claude Code feature that causes Forge to hang)
- Injects `name` field into frontmatter when missing
- Requires hyphenated command names (speckit-foo-bar) instead of dot notation (speckit.foo.bar)
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ..base import MarkdownIntegration
from ..manifest import IntegrationManifest


def format_forge_command_name(cmd_name: str) -> str:
    """Convert command name to Forge-compatible hyphenated format.
    
    Forge requires command names to use hyphens instead of dots for
    compatibility with ZSH and other shells. This function converts
    dot-notation command names to hyphenated format.
    
    Examples:
        >>> format_forge_command_name("plan")
        'speckit-plan'
        >>> format_forge_command_name("speckit.plan")
        'speckit-plan'
        >>> format_forge_command_name("speckit.my-extension.example")
        'speckit-my-extension-example'
        >>> format_forge_command_name("speckit.jira.sync-status")
        'speckit-jira-sync-status'
    
    Args:
        cmd_name: Command name in any format (with or without 'speckit.' prefix)
    
    Returns:
        Hyphenated command name with 'speckit-' prefix
    """
    # Strip 'speckit.' prefix if present
    short_name = cmd_name
    if short_name.startswith("speckit."):
        short_name = short_name[len("speckit."):]
    
    # Replace all dots with hyphens
    short_name = short_name.replace(".", "-")
    
    # Return with 'speckit-' prefix
    return f"speckit-{short_name}"


class ForgeIntegration(MarkdownIntegration):
    """Integration for Forge (forgecode.dev).

    Extends MarkdownIntegration to add Forge-specific processing:
    - Replaces $ARGUMENTS with {{parameters}}
    - Strips 'handoffs' frontmatter key (incompatible with Forge)
    - Injects 'name' field into frontmatter when missing
    """

    key = "forge"
    config = {
        "name": "Forge",
        "folder": ".forge/",
        "commands_subdir": "commands",
        "install_url": "https://forgecode.dev/docs/",
        "requires_cli": True,
    }
    registrar_config = {
        "dir": ".forge/commands",
        "format": "markdown",
        "args": "{{parameters}}",
        "extension": ".md",
        "strip_frontmatter_keys": ["handoffs"],
        "inject_name": True,
        "format_name": format_forge_command_name,  # Custom name formatter
    }
    context_file = "AGENTS.md"

    def setup(
        self,
        project_root: Path,
        manifest: IntegrationManifest,
        parsed_options: dict[str, Any] | None = None,
        **opts: Any,
    ) -> list[Path]:
        """Install Forge commands with custom processing.

        Extends MarkdownIntegration.setup() to inject Forge-specific transformations
        after standard template processing.
        """
        templates = self.list_command_templates()
        if not templates:
            return []

        project_root_resolved = project_root.resolve()
        if manifest.project_root != project_root_resolved:
            raise ValueError(
                f"manifest.project_root ({manifest.project_root}) does not match "
                f"project_root ({project_root_resolved})"
            )

        dest = self.commands_dest(project_root).resolve()
        try:
            dest.relative_to(project_root_resolved)
        except ValueError as exc:
            raise ValueError(
                f"Integration destination {dest} escapes "
                f"project root {project_root_resolved}"
            ) from exc
        dest.mkdir(parents=True, exist_ok=True)

        script_type = opts.get("script_type", "sh")
        arg_placeholder = self.registrar_config.get("args", "{{parameters}}")
        created: list[Path] = []

        for src_file in templates:
            raw = src_file.read_text(encoding="utf-8")
            # Process template with standard MarkdownIntegration logic
            processed = self.process_template(raw, self.key, script_type, arg_placeholder)

            # FORGE-SPECIFIC: Ensure any remaining $ARGUMENTS placeholders are
            # converted to {{parameters}}
            processed = processed.replace("$ARGUMENTS", arg_placeholder)

            # FORGE-SPECIFIC: Apply frontmatter transformations
            processed = self._apply_forge_transformations(processed, src_file.stem)

            dst_name = self.command_filename(src_file.stem)
            dst_file = self.write_file_and_record(
                processed, dest / dst_name, project_root, manifest
            )
            created.append(dst_file)

        # Install integration-specific update-context scripts
        created.extend(self.install_scripts(project_root, manifest))

        return created

    def _apply_forge_transformations(self, content: str, template_name: str) -> str:
        """Apply Forge-specific transformations to processed content.

        1. Strip 'handoffs' frontmatter key (from Claude Code templates; incompatible with Forge)
        2. Inject 'name' field if missing (using hyphenated format)
        """
        # Parse frontmatter
        lines = content.split('\n')
        if not lines or lines[0].strip() != '---':
            return content

        # Find end of frontmatter
        frontmatter_end = -1
        for i in range(1, len(lines)):
            if lines[i].strip() == '---':
                frontmatter_end = i
                break

        if frontmatter_end == -1:
            return content

        frontmatter_lines = lines[1:frontmatter_end]
        body_lines = lines[frontmatter_end + 1:]

        # 1. Strip 'handoffs' key
        filtered_frontmatter = []
        skip_until_outdent = False
        for line in frontmatter_lines:
            if skip_until_outdent:
                # Skip indented lines under handoffs:
                if line and (line[0] == ' ' or line[0] == '\t'):
                    continue
                else:
                    skip_until_outdent = False

            if line.strip().startswith('handoffs:'):
                skip_until_outdent = True
                continue

            filtered_frontmatter.append(line)

        # 2. Inject 'name' field if missing (using centralized formatter)
        has_name = any(line.strip().startswith('name:') for line in filtered_frontmatter)
        if not has_name:
            # Use centralized formatter to ensure consistent hyphenated format
            cmd_name = format_forge_command_name(template_name)
            filtered_frontmatter.insert(0, f'name: {cmd_name}')

        # Reconstruct content
        result = ['---'] + filtered_frontmatter + ['---'] + body_lines
        return '\n'.join(result)
