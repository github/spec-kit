"""opencode integration."""

from __future__ import annotations

import filecmp
import shutil
from pathlib import Path
from typing import Any

from ..base import MarkdownIntegration
from ..manifest import IntegrationManifest


def _migrate_legacy_command_dir(project_root: Path) -> int:
    """Migrate the legacy `.opencode/command` directory to `.opencode/commands`.

    Called after setup() has written canonical files to `.opencode/commands/`.
    For each legacy file:
    - If a same-named file exists in the new dir and is byte-identical, delete legacy.
    - If a same-named file exists but content differs (user-customized), preserve legacy.
    - If no counterpart exists, move legacy to the new dir.
    Symlinks are unlinked rather than traversed, and filesystem errors are silenced.

    Returns the number of entries removed or moved from the legacy directory.
    """
    legacy = project_root / ".opencode" / "command"

    if legacy.is_symlink():
        try:
            legacy.unlink()
            return 1
        except OSError:
            return 0

    if not legacy.is_dir():
        return 0

    new_dir = project_root / ".opencode" / "commands"
    count = 0

    for item in legacy.iterdir():
        counterpart = new_dir / item.name
        try:
            if counterpart.exists():
                # Only delete when byte-identical; preserve user customizations.
                if item.is_file() and counterpart.is_file() and filecmp.cmp(item, counterpart, shallow=False):
                    _remove_item(item)
                    count += 1
                # else: user-customized or non-file; leave in place
            else:
                new_dir.mkdir(parents=True, exist_ok=True)
                item.rename(counterpart)
                count += 1
        except OSError:
            pass

    try:
        legacy.rmdir()
    except OSError:
        pass

    return count


def _remove_item(item: Path) -> None:
    """Remove a file or directory, handling symlinks specially."""
    if item.is_symlink() or item.is_file():
        item.unlink()
    else:
        shutil.rmtree(item)


class OpencodeIntegration(MarkdownIntegration):
    key = "opencode"
    config = {
        "name": "opencode",
        "folder": ".opencode/",
        "commands_subdir": "commands",
        "install_url": "https://opencode.ai",
        "requires_cli": True,
    }
    registrar_config = {
        "dir": ".opencode/commands",
        "format": "markdown",
        "args": "$ARGUMENTS",
        "extension": ".md",
    }
    context_file = "AGENTS.md"

    def setup(
        self,
        project_root: Path,
        manifest: IntegrationManifest,
        parsed_options: dict[str, Any] | None = None,
        **opts: Any,
    ) -> list[Path]:
        """Install commands and remove any legacy `.opencode/command` directory."""
        created = super().setup(project_root, manifest, parsed_options=parsed_options, **opts)
        _migrate_legacy_command_dir(project_root)
        return created

    def build_exec_args(
        self,
        prompt: str,
        *,
        model: str | None = None,
        output_json: bool = True,
    ) -> list[str] | None:
        args = [self.key, "run"]

        message = prompt
        if prompt.startswith("/"):
            command, _, remainder = prompt[1:].partition(" ")
            if command:
                args.extend(["--command", command])
                message = remainder

        if model:
            args.extend(["-m", model])
        if output_json:
            args.extend(["--format", "json"])
        if message:
            args.append(message)
        return args
