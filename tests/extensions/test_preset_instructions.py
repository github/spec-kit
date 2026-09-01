"""Tests for preset-contributed always-on instructions (github/spec-kit#4200).

Two layers are covered:

1. Preset manifest validation (``src/specify_cli/presets``): a preset may declare
   a ``provides.instructions`` capability, an instructions-only preset (no
   templates) is valid, and entries are path-safe and well typed.
2. The ``agent-context`` composition: on update, each installed + enabled
   preset's instruction block is merged into the managed section of the agent
   context file inside a per-preset namespaced marker block; disabled/removed
   presets drop out; multiple presets coexist deterministically; path-unsafe,
   non-UTF-8, and marker-colliding entries are skipped.

This is the "explicit preset over agent-context" delivery discussed in #4200:
core validates metadata only; the opt-in agent-context extension owns the writes.
"""

from __future__ import annotations

import json
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

from specify_cli.presets import PresetManifest, PresetValidationError

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


# ── Preset manifest validation ──────────────────────────────────────────────


def _manifest(tmp_path: Path, provides_block: str) -> Path:
    text = (
        'schema_version: "1.0"\n'
        "preset:\n"
        "  id: demo\n"
        "  name: Demo\n"
        '  version: "0.1.0"\n'
        "  description: d\n"
        "requires:\n"
        '  speckit_version: ">=0.6.0"\n'
        "provides:\n"
    ) + textwrap.indent(provides_block, "  ")
    p = tmp_path / "preset.yml"
    p.write_text(text, encoding="utf-8")
    return p


def test_instructions_capability_is_accepted(tmp_path):
    m = PresetManifest(
        _manifest(
            tmp_path,
            "instructions:\n  - file: instructions/best-practices.md\n    description: rules\n",
        )
    )
    assert m.instructions == [
        {"file": "instructions/best-practices.md", "description": "rules"}
    ]


def test_instructions_only_preset_is_valid(tmp_path):
    # A preset that provides ONLY instructions (no templates) is valid.
    m = PresetManifest(
        _manifest(tmp_path, "instructions:\n  - file: instructions/rules.md\n")
    )
    assert m.instructions and not m.templates


def test_preset_with_neither_templates_nor_instructions_rejected(tmp_path):
    with pytest.raises(PresetValidationError, match="at least one template"):
        # provides present but empty
        p = tmp_path / "preset.yml"
        p.write_text(
            'schema_version: "1.0"\n'
            "preset:\n  id: demo\n  name: Demo\n  version: \"0.1.0\"\n  description: d\n"
            "requires:\n  speckit_version: \">=0.6.0\"\n"
            "provides: {}\n",
            encoding="utf-8",
        )
        PresetManifest(p)


def test_instructions_must_be_a_list(tmp_path):
    with pytest.raises(PresetValidationError, match="provides.instructions: expected a list"):
        PresetManifest(_manifest(tmp_path, "instructions:\n  file: rules.md\n"))


def test_instruction_entry_requires_file(tmp_path):
    with pytest.raises(PresetValidationError, match="missing 'file'"):
        PresetManifest(_manifest(tmp_path, "instructions:\n  - description: no file\n"))


def test_instruction_description_must_be_a_string(tmp_path):
    with pytest.raises(PresetValidationError, match="'description' must be a string"):
        PresetManifest(
            _manifest(
                tmp_path,
                "instructions:\n  - file: rules.md\n    description: [not, a, string]\n",
            )
        )


@pytest.mark.parametrize("bad_path", ["/abs/rules.md", "../escape.md", "sub/../../escape.md"])
def test_instruction_path_traversal_rejected(tmp_path, bad_path):
    with pytest.raises(PresetValidationError, match="Invalid instruction file"):
        PresetManifest(_manifest(tmp_path, f"instructions:\n  - file: {bad_path}\n"))


def test_empty_instructions_list_rejected(tmp_path):
    # An empty instructions list provides nothing; reject like empty templates.
    with pytest.raises(PresetValidationError, match="must not be empty"):
        PresetManifest(_manifest(tmp_path, "instructions: []\n"))


@pytest.mark.parametrize(
    "bad_path",
    ["", "  ", " rules.md ", ".", "sub/", "C:rules.md", "rules\\win.md"],
    ids=["empty", "whitespace", "surrounding-ws", "dot", "dir-only", "drive-relative", "backslash"],
)
def test_instruction_path_non_portable_rejected(tmp_path, bad_path):
    with pytest.raises(PresetValidationError, match="Invalid instruction file"):
        PresetManifest(_manifest(tmp_path, f"instructions:\n  - file: '{bad_path}'\n"))


# ── agent-context composition ───────────────────────────────────────────────


def _configure_agent_context(project: Path, context_file: str = "AGENTS.md") -> None:
    cfg = project / ".specify" / "extensions" / "agent-context" / "agent-context-config.yml"
    cfg.parent.mkdir(parents=True, exist_ok=True)
    cfg.write_text(f"context_file: {context_file}\ncontext_files: []\n", encoding="utf-8")


def _install_preset(
    project: Path,
    preset_id: str,
    rules: str,
    *,
    enabled: bool = True,
    file_rel: str = "instructions/rules.md",
) -> None:
    """Materialize an installed preset on disk + register it (no CLI needed)."""
    presets = project / ".specify" / "presets"
    preset_dir = presets / preset_id
    target = preset_dir / file_rel
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(rules, encoding="utf-8")
    (preset_dir / "preset.yml").write_text(
        textwrap.dedent(
            f"""\
            schema_version: "1.0"
            preset:
              id: {preset_id}
              name: {preset_id}
              version: "1.0.0"
              description: d
            requires:
              speckit_version: ">=0.6.0"
            provides:
              instructions:
                - file: {file_rel}
            """
        ),
        encoding="utf-8",
    )
    registry_path = presets / ".registry"
    if registry_path.is_file():
        registry = json.loads(registry_path.read_text(encoding="utf-8"))
    else:
        registry = {"schema_version": "1.0", "presets": {}}
    registry["presets"][preset_id] = {"version": "1.0.0", "enabled": enabled}
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    registry_path.write_text(json.dumps(registry, indent=2), encoding="utf-8")


def _run_update(project: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(PY_TWIN)],
        cwd=str(project),
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


def _managed(project: Path, context_file: str = "AGENTS.md") -> str:
    p = project / context_file
    return p.read_text(encoding="utf-8") if p.is_file() else ""


def test_enabled_preset_block_composed(tmp_path):
    _configure_agent_context(tmp_path)
    _install_preset(tmp_path, "cosmos-rules", RULES_A)

    _run_update(tmp_path)
    section = _managed(tmp_path)

    assert "<!-- SPECKIT PRESET:cosmos-rules START -->" in section
    assert "<!-- SPECKIT PRESET:cosmos-rules END -->" in section
    # Payload preserved byte-for-byte (including the em-dash).
    assert RULES_A.strip() in section


def test_disabled_preset_block_removed_on_update(tmp_path):
    _configure_agent_context(tmp_path)
    _install_preset(tmp_path, "cosmos-rules", RULES_A)
    _run_update(tmp_path)
    assert "PRESET:cosmos-rules" in _managed(tmp_path)

    _install_preset(tmp_path, "cosmos-rules", RULES_A, enabled=False)
    _run_update(tmp_path)
    section = _managed(tmp_path)
    assert "PRESET:cosmos-rules" not in section
    # Base managed section survives.
    assert "<!-- SPECKIT START -->" in section and "<!-- SPECKIT END -->" in section


def test_multiple_presets_in_id_order(tmp_path):
    _configure_agent_context(tmp_path)
    _install_preset(tmp_path, "zeta", RULES_B)
    _install_preset(tmp_path, "alpha", RULES_A)
    _run_update(tmp_path)
    section = _managed(tmp_path)

    assert "PRESET:alpha" in section and "PRESET:zeta" in section
    assert section.index("PRESET:alpha START") < section.index("PRESET:zeta START")


def test_path_unsafe_instruction_entry_skipped(tmp_path):
    _configure_agent_context(tmp_path)
    _install_preset(tmp_path, "evil", RULES_A, file_rel="rules.md")
    manifest = tmp_path / ".specify" / "presets" / "evil" / "preset.yml"
    manifest.write_text(
        manifest.read_text(encoding="utf-8").replace(
            "- file: rules.md", "- file: ../../../../etc/passwd"
        ),
        encoding="utf-8",
    )
    _run_update(tmp_path)
    assert "PRESET:evil" not in _managed(tmp_path)


def test_marker_colliding_payload_skipped(tmp_path):
    _configure_agent_context(tmp_path)
    _install_preset(tmp_path, "bad", "# Bad\n\n<!-- SPECKIT END -->\n\nstranded\n")
    result = _run_update(tmp_path)
    assert result.returncode == 0
    section = _managed(tmp_path)
    assert "PRESET:bad" not in section
    assert "stranded" not in section
    assert section.count("<!-- SPECKIT START -->") == 1
    assert section.count("<!-- SPECKIT END -->") == 1


def test_non_utf8_instruction_file_skipped(tmp_path):
    _configure_agent_context(tmp_path)
    _install_preset(tmp_path, "good", RULES_A)
    _install_preset(tmp_path, "broken", RULES_B)
    broken = tmp_path / ".specify" / "presets" / "broken" / "instructions" / "rules.md"
    broken.write_bytes(b"\xff\xfe bad bytes \x80\x81")
    result = _run_update(tmp_path)
    assert result.returncode == 0
    section = _managed(tmp_path)
    assert "PRESET:good" in section
    assert "PRESET:broken" not in section


def test_no_preset_registry_just_base_section(tmp_path):
    _configure_agent_context(tmp_path)
    result = _run_update(tmp_path)
    assert result.returncode == 0
    section = _managed(tmp_path)
    assert "<!-- SPECKIT START -->" in section and "<!-- SPECKIT END -->" in section
    assert "PRESET:" not in section


def test_unsafe_registry_preset_id_skipped(tmp_path):
    # The registry is on disk and untrusted: an id with separators/traversal or
    # an absolute/drive form must be skipped, not resolved and read.
    _configure_agent_context(tmp_path)
    _install_preset(tmp_path, "good", RULES_A)
    reg_path = tmp_path / ".specify" / "presets" / ".registry"
    reg = json.loads(reg_path.read_text(encoding="utf-8"))
    reg["presets"]["../../evil"] = {"version": "1.0.0", "enabled": True}
    reg["presets"]["/abs-evil"] = {"version": "1.0.0", "enabled": True}
    reg_path.write_text(json.dumps(reg, indent=2), encoding="utf-8")
    result = _run_update(tmp_path)
    assert result.returncode == 0
    section = _managed(tmp_path)
    assert "PRESET:good" in section
    assert "evil" not in section
