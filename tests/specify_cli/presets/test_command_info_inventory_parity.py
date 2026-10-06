"""Real inventory regressions for selector diagnostics (no mocked catalog)."""

from pathlib import Path

import pytest
from typer.testing import CliRunner

from specify_cli import app
from specify_cli.artifacts import ArtifactCatalog
from specify_cli.presets import PresetRegistry, PresetResolver
from specify_cli.presets.command_info import _diagnostic_selector_matches
from tests.conftest import install_preset, strip_ansi


def _payload(pack, relative):
    path = pack / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("# inventory fixture\n", encoding="utf-8")
    return path


def _selector(project, kind):
    pack = install_preset(
        project,
        "selector",
        {
            "templates": [
                {
                    "type": kind,
                    "name": "regex:^parity-.*$",
                    "file": "overlay/payload.md",
                    "strategy": "wrap" if kind == "script" else "append",
                }
            ]
        },
        priority=5,
    )
    _payload(pack, "overlay/payload.md")
    return pack


@pytest.mark.parametrize("kind,suffix", [("template", ".md"), ("script", ".sh")])
def test_diagnostics_include_enabled_extension_manifest_and_conventions(
    tmp_path, kind, suffix
):
    project = tmp_path / "project"
    (project / ".specify").mkdir(parents=True)
    pack = _selector(project, kind)
    extensions = project / ".specify" / "extensions"
    # A manifest-free extension uses the resolver's conventional resource path.
    conventional = extensions / "conventional"
    _payload(conventional, f"{kind}s/parity-conventional{suffix}")
    # Valid manifest declarations can point outside the conventional directory.
    import yaml
    from specify_cli.extensions import ExtensionRegistry

    declared = extensions / "declared"
    _payload(declared, f"assets/payload{suffix}")
    (declared / "extension.yml").write_text(
        yaml.safe_dump(
            {
                "schema_version": "1.0",
                "extension": {
                    "id": "declared",
                    "name": "Declared",
                    "version": "1.0.0",
                    "description": "Parity fixture",
                },
                "requires": {"speckit_version": ">=0.1.0"},
                "provides": {
                    f"{kind}s": [
                        {"name": "parity-declared", "file": f"assets/payload{suffix}"},
                        {"name": "parity-missing", "file": f"assets/missing{suffix}"},
                    ]
                },
            }
        ),
        encoding="utf-8",
    )
    _payload(declared, f"{kind}s/parity-missing{suffix}")
    disabled = extensions / "disabled"
    _payload(disabled, f"{kind}s/parity-disabled{suffix}")
    ExtensionRegistry(extensions).add(
        "disabled", {"enabled": False, "version": "1.0.0"}
    )
    resolver = PresetResolver(project)
    matches = _diagnostic_selector_matches(
        project, resolver, pack, "regex:^parity-.*$", kind
    )
    assert matches == ["parity-conventional", "parity-declared"]
    names = {
        row.name
        for row in ArtifactCatalog(project).list_artifacts()
        if row.kind == kind
    }
    assert set(matches) <= names
    assert "parity-disabled" not in names
    assert "parity-missing" not in names


@pytest.mark.parametrize("kind,suffix", [("template", ".md"), ("script", ".sh")])
def test_diagnostics_require_concrete_enabled_lower_resources(tmp_path, kind, suffix):
    project = tmp_path / "project"
    (project / ".specify").mkdir(parents=True)
    pack = _selector(project, kind)
    for preset_id, priority, enabled in [
        ("higher", 1, True),
        ("lower", 10, True),
        ("disabled", 20, False),
    ]:
        lower = install_preset(
            project,
            preset_id,
            {
                "templates": [
                    {
                        "type": kind,
                        "name": f"parity-{preset_id}",
                        "file": f"assets/payload{suffix}",
                    },
                ]
            },
            priority=priority,
        )
        _payload(lower, f"assets/payload{suffix}")
        PresetRegistry(project / ".specify" / "presets").update(
            preset_id, {"enabled": enabled}
        )
    _payload(pack, f"{kind}s/parity-self{suffix}")
    overrides = project / ".specify" / "templates" / "overrides"
    _payload(
        overrides,
        f"scripts/parity-project{suffix}" if kind == "script" else "parity-project.md",
    )
    # A lower regex is not itself a concrete resource: the higher exact entry
    # cannot serve as a base for either selector.
    regex_lower = install_preset(
        project,
        "regex-lower",
        {
            "templates": [
                {
                    "type": kind,
                    "name": "regex:^parity-higher$",
                    "file": "overlay.md",
                    "strategy": "wrap" if kind == "script" else "append",
                }
            ]
        },
        priority=15,
    )
    _payload(regex_lower, "overlay.md")
    assert _diagnostic_selector_matches(
        project, PresetResolver(project), pack, "regex:^parity-.*$", kind
    ) == ["parity-lower"]
    PresetRegistry(project / ".specify" / "presets").update(
        "selector", {"enabled": False}
    )
    assert (
        _diagnostic_selector_matches(
            project, PresetResolver(project), pack, "regex:^parity-.*$", kind
        )
        == []
    )


@pytest.mark.parametrize("bundled", [True, False], ids=["wheel-core", "source-core"])
def test_preset_info_reports_bundled_core_without_project_local_assets(
    tmp_path, monkeypatch, bundled
):
    import specify_cli
    from specify_cli import _assets

    project = tmp_path / "project"
    (project / ".specify").mkdir(parents=True)
    core = tmp_path / "core"
    _payload(core, "templates/parity-bundled-template.md")
    _payload(core, "scripts/parity-bundled-script.sh")
    monkeypatch.setattr(
        specify_cli, "_locate_core_pack", lambda: core if bundled else None
    )
    monkeypatch.setattr(specify_cli, "_repo_root", lambda: core)
    monkeypatch.setattr(_assets, "_locate_core_pack", lambda: core if bundled else None)
    monkeypatch.setattr(_assets, "_repo_root", lambda: core)
    pack = install_preset(
        project,
        "selector",
        {
            "templates": [
                {
                    "type": kind,
                    "name": "regex:^parity-bundled-.*$",
                    "file": f"overlays/{kind}.md",
                    "strategy": "wrap" if kind == "script" else "append",
                }
                for kind in ("template", "script")
            ]
        },
        priority=5,
    )
    for kind in ("template", "script"):
        _payload(pack, f"overlays/{kind}.md")
    assert not (project / ".specify" / "templates").exists()
    monkeypatch.setattr(Path, "cwd", lambda: project)
    result = CliRunner().invoke(app, ["preset", "info", "selector"])
    assert result.exit_code == 0, result.output
    output = strip_ansi(result.output)
    assert "parity-bundled-template" in output
    assert "parity-bundled-script" in output
    assert "No current matches" not in output
