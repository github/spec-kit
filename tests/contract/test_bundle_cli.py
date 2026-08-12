"""Contract test for the `specify bundle` CLI surface (Typer integration).

Exercises the wired commands end-to-end via CliRunner against a temp project,
asserting exit codes and the cross-cutting error guarantees from
contracts/cli-commands.md (offline, discovery-only refusal, not-a-project error).
"""
from __future__ import annotations

import io
import json
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml
from typer.testing import CliRunner

from specify_cli import app
from specify_cli.bundler.services.packager import build_bundle
from tests.conftest import strip_ansi
from tests.bundler_helpers import (
    catalog_entry_dict,
    valid_manifest_dict,
    write_catalog_file,
)

runner = CliRunner()

MARKUP_BUNDLE_ID = "[red]markup-id[/red]"
MARKUP_SOURCE_ID = "[underline]markup-source[/underline]"


def _configure_markup_catalog(project: Path, **overrides: object) -> dict:
    entry = catalog_entry_dict(
        MARKUP_BUNDLE_ID,
        name="[green]Markup Name[/green]",
        version="[blue]1.0.0[/blue]",
        role="[magenta]Markup Role[/magenta]",
        description="[yellow]Markup Description[/yellow]",
        author="[cyan]Markup Author[/cyan]",
        license="[bold]Markup License[/bold]",
        download_url="https://example.com/markup-bundle.zip",
        requires={"speckit_version": "[italic]>=0.1.0[/italic]"},
        **overrides,
    )
    catalog = project / "markup-catalog.json"
    write_catalog_file(catalog, {MARKUP_BUNDLE_ID: entry})
    config = {
        "schema_version": "1.0",
        "catalogs": [
            {
                "id": MARKUP_SOURCE_ID,
                "url": str(catalog),
                "priority": 1,
                "install_policy": "install-allowed",
            }
        ],
    }
    (project / ".specify" / "bundle-catalogs.yml").write_text(
        yaml.safe_dump(config),
        encoding="utf-8",
    )
    return entry


@pytest.fixture()
def project(tmp_path: Path, monkeypatch) -> Path:
    (tmp_path / ".specify").mkdir()
    monkeypatch.chdir(tmp_path)
    return tmp_path


def test_bundle_help_lists_all_commands():
    result = runner.invoke(app, ["bundle", "--help"])
    assert result.exit_code == 0
    for cmd in ("search", "info", "list", "install", "update", "remove",
                "validate", "build", "init", "catalog"):
        assert cmd in result.output


def test_update_accepts_integration_override():
    # Update must expose --integration so integration-pinned bundles can be
    # updated in projects where the active integration can't be auto-detected.
    # Rich may insert ANSI escapes between the two leading dashes, so match the
    # un-split option word rather than the literal "--integration".
    result = runner.invoke(app, ["bundle", "update", "--help"])
    assert result.exit_code == 0
    assert "integration" in result.output


def test_list_empty_project(project: Path):
    result = runner.invoke(app, ["bundle", "list"])
    assert result.exit_code == 0
    assert "No bundles installed" in result.output


def test_commands_outside_project_fail_with_guidance(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)  # no .specify/
    result = runner.invoke(app, ["bundle", "list"])
    assert result.exit_code == 1
    assert "Spec Kit project" in result.output


def test_remove_reports_clean_error_when_primitive_raises_raw_exception(
    project: Path,
):
    """A raw exception from a primitive installer (e.g. an OSError from an
    unreadable workflow registry surfacing through _WorkflowKindManager's
    fail-closed construction) must not propagate uncaught through
    `specify bundle remove` -- the command only catches BundlerError, so
    without a conversion at the remove_bundle boundary this would exit
    with an unhandled exception and empty/raw output instead of a clean,
    actionable message, and no removal side effects should occur either."""
    from specify_cli.bundler.models.manifest import BundleManifest
    from specify_cli.bundler.models.records import load_records
    from specify_cli.bundler.services.adapters import DefaultPrimitiveInstaller
    from specify_cli.bundler.services.installer import install_bundle
    from specify_cli.bundler.services.resolver import resolve_install_plan
    from tests.bundler_helpers import FakeInstaller

    manifest = BundleManifest.from_dict(valid_manifest_dict())
    plan = resolve_install_plan(
        manifest, speckit_version="0.11.2", active_integration="copilot"
    )
    install_bundle(project, plan, FakeInstaller(), manifest=manifest)

    def boom(self, project_root, component):
        raise OSError("workflow registry unreadable")

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(DefaultPrimitiveInstaller, "is_installed", boom)
        result = runner.invoke(app, ["bundle", "remove", "demo-bundle"])

    assert result.exit_code != 0
    assert result.output.strip() != ""
    assert result.exception is None or isinstance(result.exception, SystemExit)
    assert {r.bundle_id for r in load_records(project)} == {"demo-bundle"}


def test_fail_writes_error_to_stderr_not_stdout(capsys):
    """_fail must write to stderr, not stdout: every bundle command routes errors
    through it, and under --json the error would otherwise corrupt the JSON payload
    that consumers read from stdout."""
    import typer

    from specify_cli.commands.bundle import _fail

    with pytest.raises(typer.Exit):
        _fail("something broke")
    captured = capsys.readouterr()
    assert "something broke" in captured.err
    assert "something broke" not in captured.out


def test_search_works_without_a_project(tmp_path: Path, monkeypatch):
    # Discovery commands fall back to the built-in/user catalog stack and must
    # not require a Spec Kit project (matches README/quickstart examples).
    monkeypatch.chdir(tmp_path)  # no .specify/
    result = runner.invoke(app, ["bundle", "search", "--offline", "--json"])
    assert result.exit_code == 0, result.output
    assert result.output.strip().startswith("[")


def test_search_escapes_catalog_markup(project: Path):
    entry = _configure_markup_catalog(project)

    result = runner.invoke(app, ["bundle", "search", "--offline"])

    assert result.exit_code == 0, result.output
    output = " ".join(strip_ansi(result.output).split())
    for value in (
        entry["id"],
        entry["name"],
        entry["version"],
        entry["role"],
        entry["description"],
        MARKUP_SOURCE_ID,
    ):
        assert value in output


def test_info_unknown_bundle_without_project_reports_not_found(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)  # no .specify/
    result = runner.invoke(app, ["bundle", "info", "does-not-exist", "--offline"])
    # Reaches catalog resolution (not the project gate) and reports a clean miss.
    assert result.exit_code == 1
    assert "Spec Kit project" not in result.output


def test_catalog_list_shows_builtin_defaults(project: Path):
    result = runner.invoke(app, ["bundle", "catalog", "list"])
    assert result.exit_code == 0
    assert "default" in result.output
    assert "community" in result.output
    assert "built-in default stack" in result.output


def test_catalog_add_and_remove(project: Path):
    catalog = project / "local-catalog.json"
    write_catalog_file(catalog, {"demo": catalog_entry_dict("demo")})

    added = runner.invoke(
        app, ["bundle", "catalog", "add", str(catalog), "--id", "local"]
    )
    assert added.exit_code == 0, added.output

    listed = runner.invoke(app, ["bundle", "catalog", "list"])
    assert "local" in listed.output

    removed = runner.invoke(app, ["bundle", "catalog", "remove", "local"])
    assert removed.exit_code == 0


def test_catalog_remove_builtin_is_refused(project: Path):
    result = runner.invoke(app, ["bundle", "catalog", "remove", "default"])
    assert result.exit_code == 1
    assert "built-in" in result.output


# Every ``bundle`` error path funnels through ``_fail(str(exc))``, and the
# BundlerError messages interpolate untrusted data -- including the command's
# own argument. An unbalanced closer used to raise MarkupError instead of the
# error, leaving the user with a traceback and no message at all.
@pytest.mark.parametrize(
    "argv, expected",
    [
        (
            ["bundle", "catalog", "add", "ssh://ex[/red]ample.com/c.json"],
            "ssh://ex[/red]ample.com/c.json",
        ),
        (["bundle", "catalog", "remove", "no[/red]such"], "no[/red]such"),
        (["bundle", "update", "no[/red]such"], "no[/red]such"),
        (["bundle", "remove", "no[/red]such"], "no[/red]such"),
    ],
)
def test_error_paths_escape_rich_markup(project: Path, argv: list, expected: str):
    result = runner.invoke(app, argv)

    assert result.exit_code == 1
    # A MarkupError would surface here as an exception rather than a clean exit.
    assert isinstance(result.exception, SystemExit)
    assert expected in strip_ansi(result.output)


def test_validate_reports_invalid_manifest(project: Path):
    data = valid_manifest_dict()
    del data["bundle"]["license"]
    (project / "bundle.yml").write_text(yaml.safe_dump(data), encoding="utf-8")
    result = runner.invoke(app, ["bundle", "validate"])
    assert result.exit_code == 1
    assert "license" in result.output


def test_validate_accepts_valid_manifest(project: Path):
    (project / "bundle.yml").write_text(
        yaml.safe_dump(valid_manifest_dict()), encoding="utf-8"
    )
    # Offline mode does not fail on references it cannot verify (synthetic ids
    # here); they surface as warnings while structure is confirmed valid.
    result = runner.invoke(app, ["bundle", "validate", "--offline"])
    assert result.exit_code == 0, result.output
    assert "valid" in result.output


def test_validate_escapes_manifest_markup_in_errors(project: Path):
    data = valid_manifest_dict()
    # An invalid constraint is echoed back inside the validation error.
    data["requires"] = {"speckit_version": ">=1.0[/bold]"}
    (project / "bundle.yml").write_text(yaml.safe_dump(data), encoding="utf-8")

    result = runner.invoke(app, ["bundle", "validate", "--offline"])

    assert result.exit_code == 1
    assert isinstance(result.exception, SystemExit)
    assert ">=1.0[/bold]" in strip_ansi(result.output)


def test_validate_escapes_manifest_markup_in_warnings(project: Path):
    data = valid_manifest_dict()
    # Step ids are not charset-validated, and the unresolved-reference warning
    # echoes them -- so an otherwise *valid* manifest crashed just as readily as
    # an invalid one, on the success path.
    data["provides"]["steps"] = [{"id": "step[/bold]a"}]
    (project / "bundle.yml").write_text(yaml.safe_dump(data), encoding="utf-8")

    result = runner.invoke(app, ["bundle", "validate", "--offline"])

    assert result.exit_code == 0, repr(result.exception)
    assert "step[/bold]a" in strip_ansi(result.output)


def test_validate_rejects_broken_reference(project: Path):
    # Synthetic component ids resolve to nothing in any catalog → hard failure.
    (project / "bundle.yml").write_text(
        yaml.safe_dump(valid_manifest_dict()), encoding="utf-8"
    )
    result = runner.invoke(app, ["bundle", "validate"])
    assert result.exit_code == 1
    assert "preset-a" in result.output or "ext-a" in result.output


def test_validate_accepts_bundled_reference(project: Path):
    data = valid_manifest_dict()
    data["provides"] = {"extensions": [{"id": "agent-context", "version": "1.0.0"}]}
    (project / "bundle.yml").write_text(yaml.safe_dump(data), encoding="utf-8")
    result = runner.invoke(app, ["bundle", "validate"])
    assert result.exit_code == 0, result.output
    assert "valid" in result.output


def test_build_produces_artifact(project: Path):
    (project / "bundle.yml").write_text(
        yaml.safe_dump(valid_manifest_dict()), encoding="utf-8"
    )
    (project / "README.md").write_text("# Demo", encoding="utf-8")
    result = runner.invoke(app, ["bundle", "build", "--output", str(project / "dist")])
    assert result.exit_code == 0, result.output
    artifacts = list((project / "dist").glob("*.zip"))
    assert len(artifacts) == 1


def test_build_escapes_markup_in_output_path(project: Path):
    """The build success line echoes a caller-supplied ``--output`` path.

    Brackets are legal in a directory name on both POSIX and Windows, so the
    artifact is built and *then* misreported: ``[bold]`` is consumed as a style
    tag, and the success line names a path that does not exist on disk.

    A closing tag (``[/red]``) would raise MarkupError outright, but ``/`` is a
    path separator on Windows, so this uses the silent-swallow form to keep the
    fixture portable.
    """
    (project / "bundle.yml").write_text(
        yaml.safe_dump(valid_manifest_dict()), encoding="utf-8"
    )
    (project / "README.md").write_text("# Demo", encoding="utf-8")
    out_dir = project / "dist[bold]out"

    result = runner.invoke(app, ["bundle", "build", "--output", str(out_dir)])

    assert result.exit_code == 0, repr(result.exception)
    assert list(out_dir.glob("*.zip")), "the artifact should still be built"
    assert "dist[bold]out" in strip_ansi(result.output), (
        "the reported path must match the directory actually written"
    )


def test_list_escapes_markup_in_records(project: Path):
    """``bundle list`` renders record fields that are never charset-validated.

    ``InstalledBundleRecord.from_dict`` accepts any non-empty string for
    ``bundle_id``/``version`` and any string for ``installed_at``, so a records
    file that *loads cleanly* could still crash the command that displays it.
    """
    (project / ".specify" / "bundle-records.json").write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "bundles": [
                    {
                        "bundle_id": "demo[/red]id",
                        "version": "1.0.0[/bold]",
                        "installed_at": "2026-01-01T00:00:00Z[/dim]",
                        "contributed_components": [],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    result = runner.invoke(app, ["bundle", "list"])

    assert result.exit_code == 0, repr(result.exception)
    output = strip_ansi(result.output)
    assert "demo[/red]id" in output
    assert "1.0.0[/bold]" in output
    assert "2026-01-01T00:00:00Z[/dim]" in output


def _mock_manifest_download(monkeypatch, source_path: Path) -> None:
    """Mock the HTTPS manifest fetch to return a locally-authored manifest.

    Catalog ``download_url``s are HTTPS-only, so ``info`` tests can no longer
    point one at a local file. Patch ``_download_manifest`` to return the
    manifest parsed from *source_path* (a bundle.yml or a .zip artifact),
    exercising ``info``'s expansion without a network call.
    """
    from specify_cli.commands.bundle import _local_manifest_source

    monkeypatch.setattr(
        "specify_cli.commands.bundle._download_manifest",
        lambda resolved, *, offline: _local_manifest_source(str(source_path)),
    )


def test_info_expands_full_component_set(project: Path, monkeypatch):
    bundle_dir = project / "src-bundle"
    bundle_dir.mkdir()
    (bundle_dir / "bundle.yml").write_text(
        yaml.safe_dump(valid_manifest_dict()), encoding="utf-8"
    )
    catalog = project / "local-catalog.json"
    entry = catalog_entry_dict(
        "demo-bundle", download_url="https://example.com/demo-bundle.zip"
    )
    write_catalog_file(catalog, {"demo-bundle": entry})
    added = runner.invoke(
        app, ["bundle", "catalog", "add", str(catalog), "--id", "local"]
    )
    assert added.exit_code == 0, added.output
    _mock_manifest_download(monkeypatch, bundle_dir / "bundle.yml")

    result = runner.invoke(app, ["bundle", "info", "demo-bundle", "--json", "--offline"])
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    components = {(c["kind"], c["id"]): c for c in payload["components"]}
    assert ("extensions", "ext-a") in components
    preset = components[("presets", "preset-a")]
    assert preset["version"] == "2.0.0"
    assert preset["priority"] == 10
    assert preset["strategy"] == "append"
    assert payload["trust"] == "verified"

    text = runner.invoke(app, ["bundle", "info", "demo-bundle", "--offline"])
    assert "preset-a v2.0.0" in text.output
    assert "Trust" in text.output


def test_info_escapes_catalog_markup(project: Path, monkeypatch):
    entry = _configure_markup_catalog(project)
    bundle_dir = project / "markup-bundle"
    bundle_dir.mkdir()
    manifest_data = valid_manifest_dict()
    manifest_data["bundle"]["id"] = MARKUP_BUNDLE_ID
    manifest_data["integration"] = {
        "id": "[conceal]markup-integration[/conceal]"
    }
    manifest_path = bundle_dir / "bundle.yml"
    manifest_path.write_text(yaml.safe_dump(manifest_data), encoding="utf-8")
    _mock_manifest_download(monkeypatch, manifest_path)
    monkeypatch.setattr(
        "specify_cli.commands.bundle._manifest_component_view",
        lambda manifest: [
            {
                "kind": "extensions",
                "id": "[reverse]markup-component[/reverse]",
                "version": "[strike]2.0.0[/strike]",
            }
        ],
    )
    monkeypatch.setattr(
        "specify_cli.commands.bundle._bundle_overlaps",
        lambda project_root, manifest, *, offline: [
            "[blink]markup-overlap[/blink]"
        ],
    )

    result = runner.invoke(
        app,
        ["bundle", "info", MARKUP_BUNDLE_ID, "--offline"],
    )

    assert result.exit_code == 0, result.output
    output = " ".join(strip_ansi(result.output).split())
    for value in (
        entry["id"],
        entry["name"],
        entry["version"],
        entry["role"],
        entry["description"],
        entry["author"],
        entry["license"],
        entry["requires"]["speckit_version"],
        MARKUP_SOURCE_ID,
        "[conceal]markup-integration[/conceal]",
        "[reverse]markup-component[/reverse]",
        "[strike]2.0.0[/strike]",
        "[blink]markup-overlap[/blink]",
    ):
        assert value in output


def test_info_escapes_catalog_provides_fallback_markup(project: Path, monkeypatch):
    markup_count = "[bold]markup-count[/bold]"
    _configure_markup_catalog(
        project,
        provides={"extensions": markup_count},
    )
    bundle_dir = project / "markup-bundle"
    bundle_dir.mkdir()
    manifest_data = valid_manifest_dict(provides={})
    manifest_data["bundle"]["id"] = MARKUP_BUNDLE_ID
    manifest_path = bundle_dir / "bundle.yml"
    manifest_path.write_text(yaml.safe_dump(manifest_data), encoding="utf-8")
    _mock_manifest_download(monkeypatch, manifest_path)

    result = runner.invoke(
        app,
        ["bundle", "info", MARKUP_BUNDLE_ID, "--offline"],
    )

    assert result.exit_code == 0, result.output
    assert markup_count in strip_ansi(result.output)


def test_info_expands_discovery_only_bundle(project: Path, monkeypatch):
    # Discovery-only bundles must still be fully inspectable via `info`;
    # only `install` is refused for them.
    bundle_dir = project / "disc-bundle"
    bundle_dir.mkdir()
    (bundle_dir / "bundle.yml").write_text(
        yaml.safe_dump(valid_manifest_dict()), encoding="utf-8"
    )
    catalog = project / "disc-catalog.json"
    entry = catalog_entry_dict(
        "demo-bundle", download_url="https://example.com/demo-bundle.zip"
    )
    write_catalog_file(catalog, {"demo-bundle": entry})
    config = {
        "schema_version": "1.0",
        "catalogs": [
            {"id": "disc", "url": str(catalog), "priority": 1,
             "install_policy": "discovery-only"}
        ],
    }
    (project / ".specify" / "bundle-catalogs.yml").write_text(
        yaml.safe_dump(config), encoding="utf-8"
    )
    _mock_manifest_download(monkeypatch, bundle_dir / "bundle.yml")
    result = runner.invoke(app, ["bundle", "info", "demo-bundle", "--json", "--offline"])
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    components = {(c["kind"], c["id"]) for c in payload["components"]}
    assert ("extensions", "ext-a") in components


def test_info_expands_zip_sourced_bundle(project: Path, monkeypatch):
    # A .zip artifact is extracted to read bundle.yml; info expands it. (The
    # download itself is HTTPS-only now and mocked here — see contract note.)
    bundle_dir = project / "zip-src"
    bundle_dir.mkdir()
    (bundle_dir / "bundle.yml").write_text(
        yaml.safe_dump(valid_manifest_dict()), encoding="utf-8"
    )
    (bundle_dir / "README.md").write_text("# Demo", encoding="utf-8")
    artifact = build_bundle(bundle_dir, output_dir=project / "dist").artifact_path
    catalog = project / "zip-catalog.json"
    write_catalog_file(
        catalog,
        {"demo-bundle": catalog_entry_dict(
            "demo-bundle", download_url="https://example.com/demo-bundle.zip"
        )},
    )
    added = runner.invoke(
        app, ["bundle", "catalog", "add", str(catalog), "--id", "local"]
    )
    assert added.exit_code == 0, added.output
    _mock_manifest_download(monkeypatch, artifact)
    result = runner.invoke(app, ["bundle", "info", "demo-bundle", "--json", "--offline"])
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    components = {(c["kind"], c["id"]) for c in payload["components"]}
    assert ("extensions", "ext-a") in components


def test_install_refuses_discovery_only_source(project: Path, monkeypatch):
    # Point a discovery-only catalog at a local payload containing the bundle.
    catalog = project / "disc.json"
    write_catalog_file(catalog, {"demo": catalog_entry_dict("demo")})
    config = {
        "schema_version": "1.0",
        "catalogs": [
            {"id": "disc", "url": str(catalog), "priority": 1,
             "install_policy": "discovery-only"}
        ],
    }
    (project / ".specify" / "bundle-catalogs.yml").write_text(
        yaml.safe_dump(config), encoding="utf-8"
    )
    result = runner.invoke(app, ["bundle", "install", "demo", "--offline"])
    assert result.exit_code == 1
    assert "discovery-only" in result.output


def test_update_refuses_discovery_only_source(project: Path):
    # An installed bundle whose only resolvable source is discovery-only must
    # not be updatable from there (FR-025), mirroring the install policy gate.
    from specify_cli.bundler.models.manifest import ComponentRef
    from specify_cli.bundler.models.records import (
        InstalledBundleRecord,
        save_records,
    )

    save_records(
        project,
        [
            InstalledBundleRecord.create(
                "demo",
                "1.0.0",
                [ComponentRef(kind="extensions", id="ext-a", version=None)],
            )
        ],
    )

    catalog = project / "disc.json"
    write_catalog_file(catalog, {"demo": catalog_entry_dict("demo")})
    config = {
        "schema_version": "1.0",
        "catalogs": [
            {"id": "disc", "url": str(catalog), "priority": 1,
             "install_policy": "discovery-only"}
        ],
    }
    (project / ".specify" / "bundle-catalogs.yml").write_text(
        yaml.safe_dump(config), encoding="utf-8"
    )

    result = runner.invoke(app, ["bundle", "update", "demo", "--offline"])
    assert result.exit_code == 1
    assert "discovery-only" in result.output


def test_info_fails_loudly_when_manifest_unresolvable_offline(project: Path):
    # `info` must expand the real component set; if the manifest can't be
    # resolved (here: --offline against an https download_url), it should error
    # and exit non-zero rather than silently degrading to `provides` counts.
    catalog = project / "remote-catalog.json"
    entry = catalog_entry_dict(
        "demo-bundle", download_url="https://example.com/demo-bundle.zip"
    )
    write_catalog_file(catalog, {"demo-bundle": entry})
    added = runner.invoke(
        app, ["bundle", "catalog", "add", str(catalog), "--id", "remote"]
    )
    assert added.exit_code == 0, added.output

    result = runner.invoke(app, ["bundle", "info", "demo-bundle", "--offline"])
    assert result.exit_code == 1
    assert "Network access disabled" in result.output


def test_search_json_offline(project: Path):
    catalog = project / "c.json"
    write_catalog_file(catalog, {"demo": catalog_entry_dict("demo")})
    config = {
        "schema_version": "1.0",
        "catalogs": [
            {"id": "c", "url": str(catalog), "priority": 1,
             "install_policy": "install-allowed"}
        ],
    }
    (project / ".specify" / "bundle-catalogs.yml").write_text(
        yaml.safe_dump(config), encoding="utf-8"
    )
    result = runner.invoke(app, ["bundle", "search", "--offline", "--json"])
    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload[0]["id"] == "demo"
    # Trust indicator is exposed on the discovery surface (FR-010 / FR-027).
    assert payload[0]["verified"] is True
    assert payload[0]["trust"] == "verified"


def test_search_text_shows_trust(project: Path):
    catalog = project / "c.json"
    write_catalog_file(
        catalog,
        {
            "verified-one": catalog_entry_dict("verified-one", verified=True),
            "community-one": catalog_entry_dict("community-one", verified=False),
        },
    )
    config = {
        "schema_version": "1.0",
        "catalogs": [
            {"id": "c", "url": str(catalog), "priority": 1,
             "install_policy": "install-allowed"}
        ],
    }
    (project / ".specify" / "bundle-catalogs.yml").write_text(
        yaml.safe_dump(config), encoding="utf-8"
    )
    result = runner.invoke(app, ["bundle", "search", "--offline"])
    assert result.exit_code == 0, result.output
    assert "verified" in result.output
    assert "community" in result.output


def test_install_integration_override_cannot_bypass_clash_guard(project: Path):
    # An initialized project's recorded active integration is authoritative:
    # passing --integration must not let a differently-pinned bundle install.
    import json

    (project / ".specify" / "integration.json").write_text(
        json.dumps({"integration": "copilot"}), encoding="utf-8"
    )
    bundle_dir = project / "claude-bundle"
    bundle_dir.mkdir()
    data = valid_manifest_dict(integration={"id": "claude"})
    (bundle_dir / "bundle.yml").write_text(yaml.safe_dump(data), encoding="utf-8")
    (bundle_dir / "README.md").write_text("# Claude bundle", encoding="utf-8")

    result = runner.invoke(
        app,
        ["bundle", "install", str(bundle_dir), "--integration", "claude", "--offline"],
    )
    assert result.exit_code == 1
    assert "claude" in result.output and "copilot" in result.output


# ===== Private GitHub release asset URL resolution =====


class FakeBundleResponse(io.BytesIO):
    """Minimal context-manager response stub for open_url fakes."""

    def __init__(self, data: bytes, url: str = "https://api.github.com/repos/org/repo/releases/assets/99"):
        super().__init__(data)
        self._url = url

    def geturl(self) -> str:
        return self._url


def _make_catalog_config(catalog_path: Path, project: Path) -> None:
    """Write a bundle-catalogs.yml pointing at *catalog_path* in *project*."""
    config = {
        "schema_version": "1.0",
        "catalogs": [
            {
                "id": "test",
                "url": str(catalog_path),
                "priority": 1,
                "install_policy": "install-allowed",
            }
        ],
    }
    (project / ".specify" / "bundle-catalogs.yml").write_text(
        yaml.safe_dump(config), encoding="utf-8"
    )


def test_bundle_info_resolves_github_browser_release_url(project: Path):
    """bundle info resolves a private-repo browser release URL via the GitHub API."""
    browser_url = "https://github.com/org/repo/releases/download/v1.0/bundle.yml"
    api_asset_url = "https://api.github.com/repos/org/repo/releases/assets/99"

    captured = []
    manifest_yaml = yaml.safe_dump(valid_manifest_dict()).encode()

    def fake_open_url(url, timeout=None, extra_headers=None, redirect_validator=None):
        captured.append((url, extra_headers))
        if "releases/tags/" in url:
            # GitHub API release-tags lookup — return asset list
            return FakeBundleResponse(
                json.dumps({
                    "assets": [{"name": "bundle.yml", "url": api_asset_url}]
                }).encode(),
                url=url,
            )
        # Actual asset download
        return FakeBundleResponse(manifest_yaml, url=api_asset_url)

    catalog = project / "catalog.json"
    write_catalog_file(
        catalog,
        {"demo-bundle": catalog_entry_dict("demo-bundle", download_url=browser_url)},
    )
    _make_catalog_config(catalog, project)

    with patch("specify_cli.authentication.http.open_url", side_effect=fake_open_url):
        result = runner.invoke(app, ["bundle", "info", "demo-bundle", "--json"])

    assert result.exit_code == 0, result.output

    # The browser release URL must have been resolved via the GitHub tags API
    tag_calls = [url for url, _ in captured if "releases/tags/" in url]
    assert len(tag_calls) == 1, f"Expected exactly one tags API call; got {captured}"
    assert "releases/tags/v1.0" in tag_calls[0]

    # The actual download must use the resolved API asset URL with octet-stream
    asset_calls = [(url, h) for url, h in captured if "releases/assets/" in url]
    assert len(asset_calls) == 1
    assert asset_calls[0][0] == api_asset_url
    assert asset_calls[0][1] == {"Accept": "application/octet-stream"}


def test_bundle_info_passes_through_api_asset_url(project: Path):
    """bundle info passes a direct GitHub API asset URL through with octet-stream."""
    api_asset_url = "https://api.github.com/repos/org/repo/releases/assets/77"

    captured = []
    manifest_yaml = yaml.safe_dump(valid_manifest_dict()).encode()

    def fake_open_url(url, timeout=None, extra_headers=None, redirect_validator=None):
        captured.append((url, extra_headers))
        return FakeBundleResponse(manifest_yaml, url=api_asset_url)

    catalog = project / "catalog.json"
    write_catalog_file(
        catalog,
        {"demo-bundle": catalog_entry_dict("demo-bundle", download_url=api_asset_url)},
    )
    _make_catalog_config(catalog, project)

    with patch("specify_cli.authentication.http.open_url", side_effect=fake_open_url):
        result = runner.invoke(app, ["bundle", "info", "demo-bundle", "--json"])

    assert result.exit_code == 0, result.output

    # No tags API call — URL was already a REST asset URL
    tag_calls = [url for url, _ in captured if "releases/tags/" in url]
    assert len(tag_calls) == 0

    # Exactly one download call to the asset URL with octet-stream
    asset_calls = [(url, h) for url, h in captured if "releases/assets/" in url]
    assert len(asset_calls) == 1
    assert asset_calls[0][0] == api_asset_url
    assert asset_calls[0][1] == {"Accept": "application/octet-stream"}


def test_bundle_info_resolves_github_browser_release_url_zip(project: Path):
    """bundle info resolves a browser release URL for a .zip artifact and extracts bundle.yml."""
    import io
    import zipfile

    browser_url = "https://github.com/org/repo/releases/download/v2.0/bundle.zip"
    api_asset_url = "https://api.github.com/repos/org/repo/releases/assets/88"

    # Build a minimal in-memory ZIP containing bundle.yml
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("bundle.yml", yaml.safe_dump(valid_manifest_dict()))
    zip_bytes = buf.getvalue()

    captured = []

    def fake_open_url(url, timeout=None, extra_headers=None, redirect_validator=None):
        captured.append((url, extra_headers))
        if "releases/tags/" in url:
            return FakeBundleResponse(
                json.dumps({
                    "assets": [{"name": "bundle.zip", "url": api_asset_url}]
                }).encode(),
                url=url,
            )
        return FakeBundleResponse(zip_bytes, url=api_asset_url)

    catalog = project / "catalog.json"
    write_catalog_file(
        catalog,
        {"demo-bundle": catalog_entry_dict("demo-bundle", download_url=browser_url)},
    )
    _make_catalog_config(catalog, project)

    with patch("specify_cli.authentication.http.open_url", side_effect=fake_open_url):
        result = runner.invoke(app, ["bundle", "info", "demo-bundle", "--json"])

    assert result.exit_code == 0, result.output

    # tags API lookup must have fired
    tag_calls = [url for url, _ in captured if "releases/tags/" in url]
    assert len(tag_calls) == 1
    assert "releases/tags/v2.0" in tag_calls[0]

    # Asset download uses the resolved API URL with octet-stream
    asset_calls = [(url, h) for url, h in captured if "releases/assets/" in url]
    assert len(asset_calls) == 1
    assert asset_calls[0][0] == api_asset_url
    assert asset_calls[0][1] == {"Accept": "application/octet-stream"}

    # Manifest was successfully parsed from the ZIP
    payload = json.loads(result.output)
    assert payload["id"] == "demo-bundle"


def test_bundle_info_api_asset_url_zip_detected_by_magic_bytes(project: Path):
    """bundle info correctly handles a direct API asset URL that serves ZIP bytes."""
    import io
    import zipfile

    api_asset_url = "https://api.github.com/repos/org/repo/releases/assets/55"

    # Build a minimal in-memory ZIP containing bundle.yml
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("bundle.yml", yaml.safe_dump(valid_manifest_dict()))
    zip_bytes = buf.getvalue()

    captured = []

    def fake_open_url(url, timeout=None, extra_headers=None, redirect_validator=None):
        captured.append((url, extra_headers))
        return FakeBundleResponse(zip_bytes, url=api_asset_url)

    catalog = project / "catalog.json"
    write_catalog_file(
        catalog,
        {"demo-bundle": catalog_entry_dict("demo-bundle", download_url=api_asset_url)},
    )
    _make_catalog_config(catalog, project)

    with patch("specify_cli.authentication.http.open_url", side_effect=fake_open_url):
        result = runner.invoke(app, ["bundle", "info", "demo-bundle", "--json"])

    assert result.exit_code == 0, result.output

    # No tags API call — URL was already a REST asset URL
    tag_calls = [url for url, _ in captured if "releases/tags/" in url]
    assert len(tag_calls) == 0

    # Download used octet-stream header
    asset_calls = [(url, h) for url, h in captured if "releases/assets/" in url]
    assert len(asset_calls) == 1
    assert asset_calls[0][1] == {"Accept": "application/octet-stream"}

    # ZIP bytes were detected by magic and bundle.yml extracted correctly
    payload = json.loads(result.output)
    assert payload["id"] == "demo-bundle"


def test_bundle_info_github_release_url_resolution_failure_falls_back_and_errors(project: Path):
    """When the GitHub tags API lookup finds no matching asset, fall back to the
    original browser URL and surface a meaningful error (not a raw traceback)."""
    browser_url = "https://github.com/org/repo/releases/download/v3.0/bundle.yml"

    captured = []

    def fake_open_url(url, timeout=None, extra_headers=None, redirect_validator=None):
        captured.append((url, extra_headers))
        if "releases/tags/" in url:
            # Tags API responds but the asset list doesn't include our file
            return FakeBundleResponse(
                json.dumps({"assets": []}).encode(),
                url=url,
            )
        # Fallback download: GitHub serves HTML (SSO redirect) instead of YAML
        return FakeBundleResponse(b"<html>SSO login required</html>", url=url)

    catalog = project / "catalog.json"
    write_catalog_file(
        catalog,
        {"demo-bundle": catalog_entry_dict("demo-bundle", download_url=browser_url)},
    )
    _make_catalog_config(catalog, project)

    with patch("specify_cli.authentication.http.open_url", side_effect=fake_open_url):
        result = runner.invoke(app, ["bundle", "info", "demo-bundle", "--json"])

    # Must exit non-zero — the HTML body is not a valid bundle manifest
    assert result.exit_code == 1

    # The tags API lookup must have fired
    tag_calls = [url for url, _ in captured if "releases/tags/" in url]
    assert len(tag_calls) == 1

    # The fallback download should use the original browser URL (no octet-stream)
    fallback_calls = [(url, h) for url, h in captured if url == browser_url]
    assert len(fallback_calls) == 1
    assert fallback_calls[0][1] is None  # no Accept header on the original URL

    # Error output must be actionable (not a raw traceback)
    assert "Error:" in result.output


def test_bundle_info_resolves_ghes_browser_release_url(project: Path):
    """bundle info resolves a GHES private-repo browser release URL via /api/v3."""
    ghes_host = "ghes.example"
    browser_url = f"https://{ghes_host}/org/repo/releases/download/v1.0/bundle.yml"
    api_asset_url = f"https://{ghes_host}/api/v3/repos/org/repo/releases/assets/42"

    captured = []
    manifest_yaml = yaml.safe_dump(valid_manifest_dict()).encode()

    def fake_open_url(url, timeout=None, extra_headers=None, redirect_validator=None):
        captured.append((url, extra_headers))
        if "/api/v3/repos/" in url and "releases/tags/" in url:
            return FakeBundleResponse(
                json.dumps({
                    "assets": [{"name": "bundle.yml", "url": api_asset_url}]
                }).encode(),
                url=url,
            )
        return FakeBundleResponse(manifest_yaml, url=api_asset_url)

    catalog = project / "catalog.json"
    write_catalog_file(
        catalog,
        {"demo-bundle": catalog_entry_dict("demo-bundle", download_url=browser_url)},
    )
    _make_catalog_config(catalog, project)

    with patch("specify_cli.authentication.http.open_url", side_effect=fake_open_url), \
         patch("specify_cli.authentication.http.github_provider_hosts", return_value=(ghes_host,)):
        result = runner.invoke(app, ["bundle", "info", "demo-bundle", "--json"])

    assert result.exit_code == 0, result.output

    # The GHES /api/v3 tags lookup must have fired
    tag_calls = [url for url, _ in captured if "releases/tags/" in url]
    assert len(tag_calls) == 1
    assert f"{ghes_host}/api/v3/repos/org/repo/releases/tags/v1.0" in tag_calls[0]

    # Asset download must use the resolved GHES API URL with octet-stream
    asset_calls = [(url, h) for url, h in captured if "releases/assets/" in url]
    assert len(asset_calls) == 1
    assert asset_calls[0][0] == api_asset_url
    assert asset_calls[0][1] == {"Accept": "application/octet-stream"}

    payload = json.loads(result.output)
    assert payload["id"] == "demo-bundle"


def test_bundle_download_rejects_oversized_response(project: Path, monkeypatch):
    """Bundle download rejects responses exceeding MAX_DOWNLOAD_BYTES."""
    # Monkeypatch to a small limit so the test is fast and low-memory.
    monkeypatch.setattr(
        "specify_cli.commands.bundle.MAX_DOWNLOAD_BYTES", 100
    )

    api_asset_url = "https://api.github.com/repos/org/repo/releases/assets/99"

    def fake_open_url(url, timeout=None, extra_headers=None, redirect_validator=None):
        # Return a response that exceeds 100 bytes.
        return FakeBundleResponse(b"x" * 200, url=api_asset_url)

    catalog = project / "catalog.json"
    write_catalog_file(
        catalog,
        {"demo-bundle": catalog_entry_dict("demo-bundle", download_url=api_asset_url)},
    )
    _make_catalog_config(catalog, project)

    with patch("specify_cli.authentication.http.open_url", side_effect=fake_open_url):
        result = runner.invoke(app, ["bundle", "info", "demo-bundle", "--json"])

    # Must fail with a size-limit error, not an unhandled traceback.
    assert result.exit_code == 1
    # Rich may wrap the message across lines; normalise whitespace before checking.
    output_flat = " ".join(result.output.split())
    assert "exceeds maximum size of 100 bytes" in output_flat
