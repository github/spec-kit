"""Assemble the speckit skills (and lifecycle hook) into an ADG plugin source.

The producer reuses the existing ``ClaudeIntegration`` skill-rendering pipeline
(``SkillsIntegration.setup``) against a throwaway staging root, so the emitted
``SKILL.md`` files are byte-for-byte identical to what ``specify init`` would
write into a project's ``.claude/skills``. The skills (plus an optional
``hooks/`` dir and a minimal ``.agents/.plugin.json`` manifest) are laid out as
a native ADG plugin so ``adg plugins add <dir> --global`` ingests it directly
and fans it out to claude/codex/antigravity.

Only the core command templates are produced (``list_command_templates``);
extensions and presets stay project-local — see the project plan.
"""

from __future__ import annotations

import json
import re
import shutil
import tempfile
from pathlib import Path

from ._assets import get_speckit_version

PLUGIN_NAME = "speckit"
PLUGIN_DESCRIPTION = (
    "Spec-Driven Development workflow: specify, clarify, plan, tasks, analyze, "
    "and implement slash commands backed by deterministic scripts."
)
SCHEMA_VERSION = "adg.plugin/v1"


def to_semver(version: str) -> str:
    """Coerce a PEP 440-ish version into the strict semver adg requires.

    adg's schema enforces ``MAJOR.MINOR.PATCH(-prerelease)?(+build)?``.
    Dev/post/pre suffixes like ``0.11.4.dev0`` become ``0.11.4-dev0``.
    Falls back to ``0.0.0`` when no MAJOR.MINOR.PATCH core is present.
    """
    m = re.match(r"^(\d+\.\d+\.\d+)(.*)$", version.strip())
    if not m:
        return "0.0.0"
    core, rest = m.group(1), m.group(2)
    if not rest:
        return core
    # Strip a leading separator (".", "-", "+") then sanitize the remainder
    # into a valid semver prerelease segment ([0-9A-Za-z-.]).
    pre = re.sub(r"[^0-9A-Za-z.-]", "-", rest.lstrip(".-+"))
    return f"{core}-{pre}" if pre else core


def produce_core_skills(skills_parent: Path, script_type: str = "sh") -> Path:
    """Render core speckit skills into ``<skills_parent>/skills`` and return it.

    Reuses ``ClaudeIntegration.setup`` on a temporary root (which emits
    ``.claude/skills/speckit-*/SKILL.md``), then relocates the ``speckit-*``
    directories under ``<skills_parent>/skills`` — the layout an ADG plugin
    manifest's ``"skills": "./skills/"`` pointer expects.
    """
    from .integrations import get_integration
    from .integrations.manifest import IntegrationManifest

    claude = get_integration("claude")
    if claude is None:  # pragma: no cover - claude is always registered
        raise RuntimeError("claude integration is not available")

    skills_dir = (skills_parent / "skills").resolve()
    skills_dir.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as tmp:
        staging = Path(tmp).resolve()
        manifest = IntegrationManifest("claude", staging, version=get_speckit_version())
        claude.setup(staging, manifest, script_type=script_type)
        rendered = claude.skills_dest(staging)
        # Pass the upstream-rendered skills through unchanged: their name and
        # content (handoff cross-references to other speckit skills) are a
        # matched set owned by spec-kit's own command-ref resolution. Any
        # runtime namespace adaptation is adg's concern, not the producer's.
        for child in sorted(rendered.iterdir()):
            if child.is_dir():
                shutil.copytree(child, skills_dir / child.name, dirs_exist_ok=True)

    return skills_dir


def build_plugin(
    out_dir: Path,
    script_type: str = "sh",
    *,
    include_hook: bool = True,
    hook_src: Path | None = None,
) -> Path:
    """Assemble a native ADG plugin source tree under *out_dir*.

    Produces::

        out_dir/
          .agents/.plugin.json    # plugin manifest
          skills/speckit-*/SKILL.md
          hooks/hooks.json        # Claude-native hook format (adg's de-facto std)
          hooks/ensure-specify.sh # script referenced by the hook

    Hooks are authored in Claude's native format (adg 0.4.0-beta.5+ adopted it
    as the standard: Claude auto-loads ``hooks/hooks.json``, adg routes the same
    file to Codex/Antigravity). When *include_hook* is true (default) the
    bundled hooks dir is located via :func:`_locate_plugin_hooks` unless
    *hook_src* overrides it. Returns *out_dir*; suitable for ``adg plugins add``.
    """
    from ._assets import _locate_plugin_hooks

    out_dir = out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    produce_core_skills(out_dir, script_type)

    if include_hook and hook_src is None:
        hook_src = _locate_plugin_hooks()

    manifest: dict[str, object] = {
        "schemaVersion": SCHEMA_VERSION,
        "name": PLUGIN_NAME,
        "version": to_semver(get_speckit_version()),
        "description": PLUGIN_DESCRIPTION,
        "skills": "./skills/",
    }

    if hook_src is not None and hook_src.is_dir():
        shutil.copytree(hook_src, out_dir / "hooks", dirs_exist_ok=True)
        manifest["hooks"] = "./hooks/"

    agents_dir = out_dir / ".agents"
    agents_dir.mkdir(parents=True, exist_ok=True)
    (agents_dir / ".plugin.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )

    return out_dir
