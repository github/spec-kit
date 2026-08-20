"""Qoder CLI integration.

Qoder IDE 1.24+ dropped ``.qoder/commands/`` scanning in favour of the
skills layout: ``.qoder/skills/{skill-name}/SKILL.md`` with a ``name``
field in frontmatter.  Migrated to ``SkillsIntegration`` to match.
"""

from ..base import SkillsIntegration


class QodercliIntegration(SkillsIntegration):
    key = "qodercli"
    config = {
        "name": "Qoder CLI",
        "folder": ".qoder/",
        "commands_subdir": "skills",
        "install_url": "https://qoder.com/cli",
        "requires_cli": True,
    }
    registrar_config = {
        "dir": ".qoder/skills",
        "format": "markdown",
        "args": "$ARGUMENTS",
        "extension": "/SKILL.md",
    }
    legacy_flat_command_dir = ".qoder/commands"
    legacy_flat_command_extension = ".md"
    multi_install_safe = True
