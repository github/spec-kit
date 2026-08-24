"""Tests for extension-contributed always-on instructions (github/spec-kit#4200).

Two layers are covered:

1. Core manifest validation (``src/specify_cli/extensions``): the ``provides.instructions``
   capability is accepted, validated, and path-safe, and an instructions-only
   extension is a valid extension.
2. The ``agent-context`` composition: on update, each installed + enabled extension's
   instruction block is merged into the routed agent context file inside a
   per-extension namespaced marker block, disabled/removed extensions drop out,
   multiple extensions coexist deterministically, path-unsafe entries are skipped,
   and nothing is written when agent-context is not configured.
"""

from __future__ import annotations

import json
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

from specify_cli.extensions import ExtensionManifest, ValidationError

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PY_TWIN = (
    PROJECT_ROOT
    / "extensions"
    / "agent-context"
    / "scripts"
    / "python"
    / "update_agent_context.py"
)

RULES_A = "# Rules A\n\n- Rule a1\n- Rule a2 with an em-dash \u2014 keep it\n"
RULES_B = "# Rules B\n\n- Rule b1\n"


# ── Core manifest validation ────────────────────────────────────────────────


def _manifest(tmp_path: Path, provides_block: str) -> Path:
    text = (
        'schema_version: "1.0"\n'
        "extension:\n"
        "  id: demo\n"
        "  name: Demo\n"
        "  version: \"0.1.0\"\n"
        "  description: d\n"
        "  author: a\n"
        "requires:\n"
        '  speckit_version: ">=0.6.0"\n'
        "provides:\n"
    ) + textwrap.indent(provides_block, "  ")
    p = tmp_path / "extension.yml"
    p.write_text(text, encoding="utf-8")
    return p


def test_instructions_capability_is_accepted(tmp_path):
    m = ExtensionManifest(
        _manifest(
            tmp_path,
            "instructions:\n  - file: instructions/best-practices.md\n    description: rules\n",
        )
    )
    assert m.instructions == [
        {"file": "instructions/best-practices.md", "description": "rules"}
    ]


def test_instructions_only_extension_is_valid(tmp_path):
    # An extension that provides ONLY instructions (no command/hook) is valid.
    m = ExtensionManifest(
        _manifest(tmp_path, "instructions:\n  - file: instructions/rules.md\n")
    )
    assert m.instructions and not m.commands


def test_instructions_must_be_a_list(tmp_path):
    with pytest.raises(ValidationError, match="provides.instructions: expected a list"):
        ExtensionManifest(_manifest(tmp_path, "instructions:\n  file: rules.md\n"))


def test_instruction_entry_requires_file(tmp_path):
    with pytest.raises(ValidationError, match="missing 'file'"):
        ExtensionManifest(
            _manifest(tmp_path, "instructions:\n  - description: no file here\n")
        )


def test_instruction_description_must_be_a_string(tmp_path):
    with pytest.raises(ValidationError, match="'description' must be a string"):
        ExtensionManifest(
            _manifest(
                tmp_path,
                "instructions:\n  - file: rules.md\n    description: [not, a, string]\n",
            )
        )


@pytest.mark.parametrize(
    "bad_path",
    ["/abs/rules.md", "../escape.md", "sub/../../escape.md"],
)
def test_instruction_path_traversal_rejected(tmp_path, bad_path):
    with pytest.raises(ValidationError, match="Invalid instruction file"):
        ExtensionManifest(
            _manifest(tmp_path, f"instructions:\n  - file: {bad_path}\n")
        )


# ── agent-context composition ───────────────────────────────────────────────


def _install_extension(
    project: Path,
    ext_id: str,
    rules: str,
    *,
    enabled: bool = True,
    file_rel: str = "instructions/rules.md",
    declare_instructions: bool = True,
) -> None:
    """Materialize an installed extension on disk + register it (no CLI needed)."""
    exts = project / ".specify" / "extensions"
    ext_dir = exts / ext_id
    target = ext_dir / file_rel
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(rules, encoding="utf-8")

    provides = (
        f"provides:\n  instructions:\n    - file: {file_rel}\n"
        if declare_instructions
        else "provides:\n  commands:\n    - name: demo.noop\n      file: cmd.md\n"
    )
    (ext_dir / "extension.yml").write_text(
        textwrap.dedent(
            f"""\
            schema_version: "1.0"
            extension:
              id: {ext_id}
              name: {ext_id}
              version: "0.1.0"
              description: d
              author: a
            requires:
              speckit_version: ">=0.2.0"
            """
        )
        + provides,
        encoding="utf-8",
    )

    registry_path = exts / ".registry"
    if registry_path.is_file():
        registry = json.loads(registry_path.read_text(encoding="utf-8"))
    else:
        registry = {"schema_version": "1.0", "extensions": {}}
    registry["extensions"][ext_id] = {"version": "0.1.0", "enabled": enabled}
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    registry_path.write_text(json.dumps(registry, indent=2), encoding="utf-8")


def _configure_agent_context(project: Path, context_file: str = "AGENTS.md") -> None:
    cfg = project / ".specify" / "extensions" / "agent-context" / "agent-context-config.yml"
    cfg.parent.mkdir(parents=True, exist_ok=True)
    cfg.write_text(
        "context_file: {}\ncontext_files: []\n".format(context_file),
        encoding="utf-8",
    )


def _run_update(project: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(PY_TWIN)],
        cwd=str(project),
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


def _managed_section(project: Path, context_file: str = "AGENTS.md") -> str:
    p = project / context_file
    return p.read_text(encoding="utf-8") if p.is_file() else ""


def test_enabled_extension_block_composed_into_context_file(tmp_path):
    _configure_agent_context(tmp_path)
    _install_extension(tmp_path, "cosmosdb", RULES_A)

    _run_update(tmp_path)
    section = _managed_section(tmp_path)

    assert "<!-- SPECKIT EXT:cosmosdb START -->" in section
    assert "<!-- SPECKIT EXT:cosmosdb END -->" in section
    # Payload preserved byte-for-byte (including the em-dash).
    assert RULES_A.strip() in section


def test_disabled_extension_block_is_removed_on_update(tmp_path):
    _configure_agent_context(tmp_path)
    _install_extension(tmp_path, "cosmosdb", RULES_A)
    _run_update(tmp_path)
    assert "EXT:cosmosdb" in _managed_section(tmp_path)

    # Flip enabled -> false and re-run: the block must disappear cleanly.
    _install_extension(tmp_path, "cosmosdb", RULES_A, enabled=False)
    _run_update(tmp_path)
    section = _managed_section(tmp_path)
    assert "EXT:cosmosdb" not in section
    # Base managed section survives.
    assert "<!-- SPECKIT START -->" in section and "<!-- SPECKIT END -->" in section


def test_multiple_extensions_coexist_in_id_order(tmp_path):
    _configure_agent_context(tmp_path)
    _install_extension(tmp_path, "zeta", RULES_B)
    _install_extension(tmp_path, "alpha", RULES_A)
    _run_update(tmp_path)
    section = _managed_section(tmp_path)

    assert "EXT:alpha" in section and "EXT:zeta" in section
    # Deterministic id ordering: alpha before zeta.
    assert section.index("EXT:alpha START") < section.index("EXT:zeta START")


def test_path_unsafe_instruction_entry_is_skipped(tmp_path):
    _configure_agent_context(tmp_path)
    # Register an extension whose manifest points outside its dir; the composer
    # must skip it rather than read an arbitrary file.
    _install_extension(tmp_path, "evil", RULES_A, file_rel="rules.md")
    manifest = tmp_path / ".specify" / "extensions" / "evil" / "extension.yml"
    manifest.write_text(
        manifest.read_text(encoding="utf-8").replace(
            "- file: rules.md", "- file: ../../../../etc/passwd"
        ),
        encoding="utf-8",
    )
    _run_update(tmp_path)
    assert "EXT:evil" not in _managed_section(tmp_path)


def test_marker_colliding_instruction_payload_is_skipped(tmp_path):
    # A payload that embeds a managed-section marker would corrupt the
    # find/replace in _upsert_section and strand content on disable/remove, so it
    # is skipped (fail closed) while the base section stays well-formed.
    _configure_agent_context(tmp_path)
    colliding = "# Bad\n\n<!-- SPECKIT END -->\n\nstranded text\n"
    _install_extension(tmp_path, "cosmosdb", colliding)
    result = _run_update(tmp_path)
    assert result.returncode == 0
    section = _managed_section(tmp_path)
    assert "EXT:cosmosdb" not in section
    assert "stranded text" not in section
    # Exactly one base marker pair remains (no duplication/corruption).
    assert section.count("<!-- SPECKIT START -->") == 1
    assert section.count("<!-- SPECKIT END -->") == 1


def test_non_utf8_instruction_file_is_skipped(tmp_path):
    # A declared instruction file that is not valid UTF-8 must be skipped like an
    # unreadable file (fail closed), never crashing the whole context refresh.
    _configure_agent_context(tmp_path)
    _install_extension(tmp_path, "good", RULES_A)
    _install_extension(tmp_path, "broken", RULES_B)
    broken_file = (
        tmp_path / ".specify" / "extensions" / "broken" / "instructions" / "rules.md"
    )
    broken_file.write_bytes(b"\xff\xfe bad bytes \x80\x81")
    result = _run_update(tmp_path)
    assert result.returncode == 0
    section = _managed_section(tmp_path)
    assert "EXT:good" in section
    assert "EXT:broken" not in section


def test_noop_when_agent_context_not_configured(tmp_path):
    # No agent-context config present: the update must not write any agent file.
    _install_extension(tmp_path, "cosmosdb", RULES_A)
    result = _run_update(tmp_path)
    assert result.returncode == 0
    assert not (tmp_path / "AGENTS.md").exists()


def test_emit_extension_blocks_mode(tmp_path):
    # The --emit-extension-blocks mode is the single source of truth shared by the
    # bash/PowerShell twins; it prints the namespaced block for enabled extensions.
    _install_extension(tmp_path, "cosmosdb", RULES_A)
    result = subprocess.run(
        [sys.executable, str(PY_TWIN), "--emit-extension-blocks"],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert result.returncode == 0
    assert "<!-- SPECKIT EXT:cosmosdb START -->" in result.stdout
    assert RULES_A.strip() in result.stdout
