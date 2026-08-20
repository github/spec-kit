"""Unit and behavioral tests for ``specify_cli.core.build_core_inventory``.

Test targets:

- Path resolution across wheel and source layouts
- Frontmatter parsing with typed empty defaults
- Alphabetical ordering & determinism
- Stable id grammar
- Fail-fast failure modes
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from specify_cli import core as core_pkg
from specify_cli.core import CoreInventoryError, build_core_inventory


# ---------------------------------------------------------------------------
# Fixtures — build a minimal in-tmp layout that mirrors the source-checkout
# shape so we can exercise every branch without touching the real repo.
# ---------------------------------------------------------------------------


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


@pytest.fixture
def well_formed_layout(tmp_path: Path) -> Path:
    """A minimal source-shaped layout: 2 commands, 1 template, 1 script × 3 runtimes."""
    _write(
        tmp_path / "templates" / "commands" / "alpha.md",
        "---\ndescription: The alpha command.\n---\n\nbody",
    )
    _write(
        tmp_path / "templates" / "commands" / "beta.md",
        "---\ndescription: The beta command.\nhandoffs:\n  - agent: alpha\n  - agent: alpha\n---\n\nbody",
    )
    _write(
        tmp_path / "templates" / "spec-template.md",
        "---\ndescription: A test template.\n---\n\n# Spec Template\n",
    )
    _write(
        tmp_path / "scripts" / "bash" / "helper.sh",
        "#!/usr/bin/env bash\n# Helper script.\n# Second header line.\n\necho hi\n",
    )
    _write(tmp_path / "scripts" / "powershell" / "helper.ps1", "# ps helper\n")
    _write(tmp_path / "scripts" / "python" / "helper.py", "# py helper\n")
    return tmp_path


@pytest.fixture
def override_layout(monkeypatch: pytest.MonkeyPatch):
    """Patch ``_resolve_core_root`` to point at any given tmp source-layout root.

    Returns a callable ``use(root: Path)``.
    """

    def use(root: Path) -> None:
        layout = core_pkg._CoreLayout(
            commands_dir=root / "templates" / "commands",
            templates_dir=root / "templates",
            scripts_dir=root / "scripts",
        )
        monkeypatch.setattr(core_pkg, "_resolve_core_root", lambda: layout)

        # Discovery of the command name set must also point at the fixture,
        # else _build_command_entry looks for names the fixture doesn't have.
        names = frozenset(
            p.stem
            for p in (root / "templates" / "commands").glob("*.md")
            if p.is_file()
        )
        monkeypatch.setattr(
            "specify_cli.extensions.CORE_COMMAND_NAMES", names
        )

    return use


# ---------------------------------------------------------------------------
# Path resolution
# ---------------------------------------------------------------------------


def test_resolve_core_root_prefers_wheel_pack(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    fake_pack = tmp_path / "core_pack"
    (fake_pack / "commands").mkdir(parents=True)
    (fake_pack / "templates").mkdir()
    (fake_pack / "scripts").mkdir()
    monkeypatch.setattr(core_pkg, "_locate_core_pack", lambda: fake_pack)
    layout = core_pkg._resolve_core_root()
    assert layout.commands_dir == fake_pack / "commands"


def test_resolve_core_root_falls_back_to_repo(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(core_pkg, "_locate_core_pack", lambda: None)
    fake_repo = tmp_path / "repo"
    (fake_repo / "templates" / "commands").mkdir(parents=True)
    (fake_repo / "scripts").mkdir()
    monkeypatch.setattr(core_pkg, "_repo_root", lambda: fake_repo)
    layout = core_pkg._resolve_core_root()
    assert layout.commands_dir == fake_repo / "templates" / "commands"


def test_resolve_core_root_raises_when_nothing_shipped(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(core_pkg, "_locate_core_pack", lambda: None)
    monkeypatch.setattr(core_pkg, "_repo_root", lambda: tmp_path)
    with pytest.raises(CoreInventoryError) as excinfo:
        core_pkg._resolve_core_root()
    assert excinfo.value.error == "core_inventory.assets_missing"


def test_package_relative_rejects_backslash() -> None:
    with pytest.raises(CoreInventoryError) as excinfo:
        core_pkg._package_relative("templates\\commands\\foo.md")
    assert excinfo.value.error == "core_inventory.invalid_source_path"


def test_package_relative_rejects_absolute() -> None:
    with pytest.raises(CoreInventoryError):
        core_pkg._package_relative("/etc/passwd")


# ---------------------------------------------------------------------------
# Frontmatter parsing
# ---------------------------------------------------------------------------


def test_parse_command_frontmatter_success(tmp_path: Path) -> None:
    md = tmp_path / "cmd.md"
    md.write_text("---\ndescription: hi\nartifact: foo\n---\nbody\n", encoding="utf-8")
    parsed = core_pkg._read_leading_frontmatter(
        md, kind="command", name="cmd", source_path="commands/cmd.md"
    )
    assert parsed == {"description": "hi", "artifact": "foo"}


def test_parse_command_frontmatter_raises_on_unclosed_fence(tmp_path: Path) -> None:
    md = tmp_path / "cmd.md"
    md.write_text("---\ndescription: hi\n\nbody with no close\n", encoding="utf-8")
    with pytest.raises(CoreInventoryError) as excinfo:
        core_pkg._read_leading_frontmatter(
            md, kind="command", name="cmd", source_path="commands/cmd.md"
        )
    assert excinfo.value.error == "core_inventory.frontmatter_parse"
    assert excinfo.value.kind == "command"


def test_parse_command_frontmatter_returns_empty_when_absent(tmp_path: Path) -> None:
    md = tmp_path / "cmd.md"
    md.write_text("# just markdown, no frontmatter\n", encoding="utf-8")
    assert (
        core_pkg._read_leading_frontmatter(
            md, kind="command", name="cmd", source_path="commands/cmd.md"
        )
        == {}
    )


def test_parse_command_frontmatter_rejects_non_mapping(tmp_path: Path) -> None:
    md = tmp_path / "cmd.md"
    md.write_text("---\n- one\n- two\n---\nbody\n", encoding="utf-8")
    with pytest.raises(CoreInventoryError):
        core_pkg._read_leading_frontmatter(
            md, kind="command", name="cmd", source_path="commands/cmd.md"
        )


# ---------------------------------------------------------------------------
# Typed empty defaults & handoffs normalization
# ---------------------------------------------------------------------------


def test_build_command_entries_uses_typed_empty_defaults(well_formed_layout: Path, override_layout) -> None:
    override_layout(well_formed_layout)
    inv = build_core_inventory()
    alpha = next(c for c in inv["commands"] if c["name"] == "speckit.alpha")
    # alpha.md declares only `description:` — everything else must default.
    assert alpha["artifact"] is None
    assert alpha["optional"] is False
    assert alpha["handoffs"] == []


def test_build_command_handoffs_flatten_agent_field(well_formed_layout: Path, override_layout) -> None:
    override_layout(well_formed_layout)
    inv = build_core_inventory()
    beta = next(c for c in inv["commands"] if c["name"] == "speckit.beta")
    # beta.md's handoffs are mappings with `agent:` — we surface only agent ids.
    assert beta["handoffs"] == ["alpha", "alpha"]


def test_build_command_rejects_non_boolean_optional(tmp_path: Path, override_layout) -> None:
    _write(
        tmp_path / "templates" / "commands" / "gamma.md",
        "---\ndescription: hi\noptional: 123\n---\n",
    )
    (tmp_path / "templates" / "spec-template.md").parent.mkdir(exist_ok=True)
    _write(tmp_path / "templates" / "spec-template.md", "# Spec Template\n")
    _write(tmp_path / "scripts" / "bash" / "helper.sh", "#!/usr/bin/env bash\n# hi\n")
    override_layout(tmp_path)
    with pytest.raises(CoreInventoryError) as excinfo:
        build_core_inventory()
    assert excinfo.value.kind == "command"


# ---------------------------------------------------------------------------
# Scripts: partial runtimes, ordering
# ---------------------------------------------------------------------------


def test_build_script_entries_reports_partial_runtimes(tmp_path: Path, override_layout) -> None:
    _write(
        tmp_path / "templates" / "commands" / "alpha.md",
        "---\ndescription: hi\n---\n",
    )
    _write(tmp_path / "templates" / "spec-template.md", "# Spec\n")
    _write(tmp_path / "scripts" / "bash" / "solo.sh", "#!/usr/bin/env bash\n# solo\n")
    # No powershell variant. Only python.
    _write(tmp_path / "scripts" / "python" / "solo.py", "# py\n")
    override_layout(tmp_path)
    inv = build_core_inventory()
    solo = next(s for s in inv["scripts"] if s["name"] == "solo")
    assert solo["runtimes"] == ["bash", "python"]


def test_script_without_bash_fails_fast(tmp_path: Path, override_layout) -> None:
    _write(
        tmp_path / "templates" / "commands" / "alpha.md",
        "---\ndescription: hi\n---\n",
    )
    _write(tmp_path / "templates" / "spec-template.md", "# Spec\n")
    # Only powershell — no bash canonical.
    _write(tmp_path / "scripts" / "powershell" / "nobash.ps1", "# ps\n")
    override_layout(tmp_path)
    with pytest.raises(CoreInventoryError) as excinfo:
        build_core_inventory()
    assert excinfo.value.error == "core_inventory.missing_canonical"


def test_python_script_name_hyphenated(tmp_path: Path, override_layout) -> None:
    _write(
        tmp_path / "templates" / "commands" / "alpha.md",
        "---\ndescription: hi\n---\n",
    )
    _write(tmp_path / "templates" / "spec-template.md", "# Spec\n")
    _write(tmp_path / "scripts" / "bash" / "setup-plan.sh", "#!/usr/bin/env bash\n# setup\n")
    _write(tmp_path / "scripts" / "python" / "setup_plan.py", "# py\n")
    override_layout(tmp_path)
    inv = build_core_inventory()
    names = [s["name"] for s in inv["scripts"]]
    assert names == ["setup-plan"]  # underscore → hyphen normalization


# ---------------------------------------------------------------------------
# Determinism, ordering, and integration against the real shipped baseline
# ---------------------------------------------------------------------------


def test_build_core_inventory_deterministic_ordering() -> None:
    a = build_core_inventory()
    b = build_core_inventory()
    # Byte-identical serialization gate.
    assert json.dumps(a, sort_keys=False) == json.dumps(b, sort_keys=False)


def test_names_are_alphabetically_sorted() -> None:
    inv = build_core_inventory()
    for section in ("commands", "templates", "scripts"):
        names = [entry["name"] for entry in inv[section]]
        assert names == sorted(names), f"{section} not sorted"


def test_top_level_keys_have_fixed_order() -> None:
    inv = build_core_inventory()
    assert list(inv.keys()) == ["commands", "templates", "scripts"]


# ---------------------------------------------------------------------------
# Stable-id grammar
# ---------------------------------------------------------------------------


_STABLE_ID = re.compile(r"^core:_:(command|template|script):[A-Za-z0-9._-]+$")


def test_all_ids_match_stable_grammar() -> None:
    inv = build_core_inventory()
    seen: list[str] = []
    for section, kind in [("commands", "command"), ("templates", "template"), ("scripts", "script")]:
        for entry in inv[section]:
            eid: str = entry["id"]
            assert _STABLE_ID.match(eid), f"bad id: {eid}"
            assert eid == f"core:_:{kind}:{entry['name']}"
            seen.append(eid)
    # No dupes across sections.
    assert len(seen) == len(set(seen))


# ---------------------------------------------------------------------------
# Fail-fast behavior on packaging errors
# ---------------------------------------------------------------------------


def test_missing_command_file_exits_with_envelope(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # Layout exists but the requested command file is missing.
    _write(tmp_path / "templates" / "spec-template.md", "# Spec\n")
    _write(tmp_path / "scripts" / "bash" / "helper.sh", "#!/usr/bin/env bash\n# hi\n")
    (tmp_path / "templates" / "commands").mkdir(parents=True, exist_ok=True)
    layout = core_pkg._CoreLayout(
        commands_dir=tmp_path / "templates" / "commands",
        templates_dir=tmp_path / "templates",
        scripts_dir=tmp_path / "scripts",
    )
    monkeypatch.setattr(core_pkg, "_resolve_core_root", lambda: layout)
    monkeypatch.setattr(
        "specify_cli.extensions.CORE_COMMAND_NAMES",
        frozenset({"ghost"}),
    )
    with pytest.raises(CoreInventoryError) as excinfo:
        build_core_inventory()
    envelope = excinfo.value.to_envelope()
    assert envelope["error"] == "core_inventory.missing_file"
    assert envelope["artifact"]["kind"] == "command"
    assert envelope["artifact"]["name"] == "ghost"


def test_unparseable_command_frontmatter_produces_envelope(tmp_path: Path, override_layout) -> None:
    _write(
        tmp_path / "templates" / "commands" / "broken.md",
        "---\ndescription: hi\n[unclosed brace\n\nbody with no close\n",
    )
    _write(tmp_path / "templates" / "spec-template.md", "# Spec\n")
    _write(tmp_path / "scripts" / "bash" / "helper.sh", "#!/usr/bin/env bash\n# hi\n")
    override_layout(tmp_path)
    with pytest.raises(CoreInventoryError) as excinfo:
        build_core_inventory()
    envelope = excinfo.value.to_envelope()
    assert envelope["error"] == "core_inventory.frontmatter_parse"


# ---------------------------------------------------------------------------
# Template description fallback path (H1 heading when no frontmatter)
# ---------------------------------------------------------------------------


def test_template_description_falls_back_to_h1(tmp_path: Path, override_layout) -> None:
    _write(
        tmp_path / "templates" / "commands" / "alpha.md",
        "---\ndescription: hi\n---\n",
    )
    _write(
        tmp_path / "templates" / "noframe-template.md",
        "# The Fallback Heading\n\nBody.\n",
    )
    _write(tmp_path / "scripts" / "bash" / "helper.sh", "#!/usr/bin/env bash\n# helper\n")
    override_layout(tmp_path)
    inv = build_core_inventory()
    tmpl = next(t for t in inv["templates"] if t["name"] == "noframe-template")
    assert tmpl["description"] == "The Fallback Heading"


def test_template_without_any_description_fails_fast(tmp_path: Path, override_layout) -> None:
    _write(
        tmp_path / "templates" / "commands" / "alpha.md",
        "---\ndescription: hi\n---\n",
    )
    _write(
        tmp_path / "templates" / "nada-template.md",
        "just body, no heading, no frontmatter\n",
    )
    _write(tmp_path / "scripts" / "bash" / "helper.sh", "#!/usr/bin/env bash\n# helper\n")
    override_layout(tmp_path)
    with pytest.raises(CoreInventoryError) as excinfo:
        build_core_inventory()
    assert excinfo.value.kind == "template"


# ---------------------------------------------------------------------------
# Path-shape invariant
# ---------------------------------------------------------------------------


def test_all_source_paths_are_package_relative_posix() -> None:
    inv = build_core_inventory()
    for section in ("commands", "templates", "scripts"):
        for entry in inv[section]:
            sp = entry["sourcePath"]
            assert not sp.startswith("/"), sp
            assert "\\" not in sp, sp
