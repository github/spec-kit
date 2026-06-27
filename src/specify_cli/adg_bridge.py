"""Bridge to the external ``adg`` CLI (Agent Directory Group).

Spec Kit is the *producer* of skills; ``adg`` is the consumer/distributor.
When ``specify init --plugin`` is used, the core speckit skills are rendered
to a staging directory and handed to ``adg plugins import-skills`` so they
live in a single, versioned, global plugin (``~/.agents/plugins``) instead of
being copied into every project's ``.claude/skills``.

This module only talks to ``adg`` through its CLI surface — it never touches
adg's ``.agents/.plugin.json`` schema, keeping the two tools decoupled.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

PLUGIN_NAME = "speckit"
ADG_INSTALL_HINT = "npm install -g @rbbtsn0w/adg"


class AdgNotFoundError(RuntimeError):
    """Raised when the ``adg`` CLI cannot be located on the system."""

    def __init__(self) -> None:
        super().__init__(
            "The 'adg' CLI is required for --plugin mode but was not found.\n"
            f"Install it with: {ADG_INSTALL_HINT}"
        )


class AdgCommandError(RuntimeError):
    """Raised when an ``adg`` invocation exits non-zero."""

    def __init__(self, args: list[str], returncode: int, output: str) -> None:
        self.args = args
        self.returncode = returncode
        self.output = output
        super().__init__(
            f"adg command failed ({returncode}): {' '.join(args)}\n{output.strip()}"
        )


def find_adg() -> str | None:
    """Return the path to the ``adg`` executable, or ``None`` if absent.

    Looks on ``PATH`` first, then a few common locations (nvm, Homebrew)
    that may not be exported to a subprocess environment.
    """
    found = shutil.which("adg")
    if found:
        return found

    candidates = [
        Path.home() / ".nvm" / "current" / "bin" / "adg",
        Path("/opt/homebrew/bin/adg"),
        Path("/usr/local/bin/adg"),
    ]
    # nvm keeps versioned dirs; scan them as a best effort.
    nvm_versions = Path.home() / ".nvm" / "versions" / "node"
    if nvm_versions.is_dir():
        candidates.extend(sorted(nvm_versions.glob("*/bin/adg"), reverse=True))

    for cand in candidates:
        if cand.is_file():
            return str(cand)
    return None


def require_adg() -> str:
    """Return the ``adg`` path or raise :class:`AdgNotFoundError`."""
    adg = find_adg()
    if not adg:
        raise AdgNotFoundError()
    return adg


def _run(adg: str, args: list[str]) -> str:
    """Run ``adg <args>`` and return combined stdout, raising on failure."""
    proc = subprocess.run(
        [adg, *args],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        raise AdgCommandError(
            [adg, *args], proc.returncode, (proc.stdout or "") + (proc.stderr or "")
        )
    return proc.stdout or ""


def has_global_plugin(name: str = PLUGIN_NAME, *, adg: str | None = None) -> bool:
    """Return True when a plugin named *name* is installed in the global store.

    Prefers the stable ``adg plugins list --global --json`` contract; falls back
    to parsing the human text output for older adg versions without ``--json``
    (where each plugin line begins with ``<name>@<version>``).
    """
    adg = adg or require_adg()
    try:
        data = json.loads(_run(adg, ["plugins", "list", "--global", "--json"]))
        plugins = data.get("plugins", []) if isinstance(data, dict) else []
        if not isinstance(plugins, list):
            plugins = []
        return any(
            isinstance(p, dict) and p.get("name") == name for p in plugins
        )
    except (AdgCommandError, ValueError, TypeError):
        # Older adg: --json rejected (non-zero) or non-JSON output → text scrape.
        out = _run(adg, ["plugins", "list", "--global"])
        prefix = f"{name}@"
        return any(line.strip().startswith(prefix) for line in out.splitlines())


def add_plugin(
    plugin_dir: Path,
    *,
    as_global: bool = True,
    target: str = "all",
    adg: str | None = None,
) -> str:
    """Install a native ADG plugin source directory (skills + hooks + manifest).

    Calls ``adg plugins add <plugin_dir> --all [--global] --target <target>``;
    adg adapts it to the requested runtime(s).
    """
    adg = adg or require_adg()
    args = ["plugins", "add", str(plugin_dir), "--all", "--target", target]
    if as_global:
        args.append("--global")
    return _run(adg, args)


def link(
    names: list[str] | None = None,
    *,
    target: str = "all",
    as_global: bool = True,
    adg: str | None = None,
) -> str:
    """Project store plugins into a runtime (register + enable).

    Calls ``adg plugins link --target <target> [names...] [--global]``.
    ``adg plugins add`` populates the store and adapts manifests but does not
    always register a ``[local]`` plugin into every runtime (notably Claude),
    so this must run after :func:`add_plugin`. ``link`` is idempotent.
    """
    adg = adg or require_adg()
    args = ["plugins", "link", "--target", target]
    if as_global:
        args.append("--global")
    if names:
        args.extend(names)
    return _run(adg, args)
