"""Behavior tests for `specify extension list --available/--all`.

These flags were documented from the original extension system (#1551) as
"Show available extensions from catalog", but the implementation was a static
hint that never queried the catalog. This suite covers the wired-up behavior:
the catalog is queried, already-installed IDs are filtered out, and a clear
error is surfaced when the catalog is unavailable.
"""

import pytest
from typer.testing import CliRunner

from specify_cli import app
from specify_cli.extensions import ExtensionManager, ExtensionCatalog, ExtensionError

runner = CliRunner()


@pytest.fixture
def project_dir(tmp_path):
    """Create a minimal spec-kit project directory."""
    proj_dir = tmp_path / "project"
    proj_dir.mkdir()
    (proj_dir / ".specify").mkdir()
    (proj_dir / ".specify" / "config.toml").write_text("ai = 'claude'")
    return proj_dir


def _catalog_entry(ext_id, name, version="1.0.0", verified=False, install_allowed=True, catalog_name="default"):
    return {
        "id": ext_id,
        "name": name,
        "version": version,
        "description": f"{name} description",
        "verified": verified,
        "_install_allowed": install_allowed,
        "_catalog_name": catalog_name,
    }


def test_list_available_queries_catalog_and_filters_installed(project_dir, monkeypatch):
    """--available must query the catalog and drop already-installed IDs."""
    monkeypatch.chdir(project_dir)

    monkeypatch.setattr(ExtensionManager, "list_installed", lambda self: [{"id": "already-installed"}])
    monkeypatch.setattr(ExtensionCatalog, "search", lambda self: [
        _catalog_entry("already-installed", "Already Installed"),
        _catalog_entry("fresh-ext", "Fresh Ext", verified=True),
    ])

    result = runner.invoke(app, ["extension", "list", "--available"], obj={"project_root": project_dir})

    assert result.exit_code == 0
    assert "Available Extensions:" in result.output
    # Uninstalled catalog extension is shown...
    assert "fresh-ext" in result.output
    assert "✓ Verified" in result.output
    assert "specify extension add fresh-ext" in result.output
    # ...and the installed one is filtered out.
    assert "already-installed" not in result.output


def test_list_available_marks_discovery_only_entries(project_dir, monkeypatch):
    """Entries whose catalog disallows install render a discovery-only note."""
    monkeypatch.chdir(project_dir)

    monkeypatch.setattr(ExtensionManager, "list_installed", lambda self: [])
    monkeypatch.setattr(ExtensionCatalog, "search", lambda self: [
        _catalog_entry("locked-ext", "Locked Ext", install_allowed=False, catalog_name="curated"),
    ])

    result = runner.invoke(app, ["extension", "list", "--available"], obj={"project_root": project_dir})

    assert result.exit_code == 0
    assert "Discovery only" in result.output
    assert "curated" in result.output
    assert "specify extension add locked-ext" not in result.output


def test_list_available_empty_catalog_message(project_dir, monkeypatch):
    """An empty (post-filter) catalog reports no additional extensions."""
    monkeypatch.chdir(project_dir)

    monkeypatch.setattr(ExtensionManager, "list_installed", lambda self: [])
    monkeypatch.setattr(ExtensionCatalog, "search", lambda self: [])

    result = runner.invoke(app, ["extension", "list", "--available"], obj={"project_root": project_dir})

    assert result.exit_code == 0
    assert "Available Extensions:" in result.output
    assert "No additional extensions available" in result.output


def test_list_available_catalog_error_exits(project_dir, monkeypatch):
    """A catalog failure surfaces a clear error and exits non-zero."""
    monkeypatch.chdir(project_dir)

    def _boom(self):
        raise ExtensionError("catalog unreachable")

    monkeypatch.setattr(ExtensionManager, "list_installed", lambda self: [])
    monkeypatch.setattr(ExtensionCatalog, "search", _boom)

    result = runner.invoke(app, ["extension", "list", "--available"], obj={"project_root": project_dir})

    assert result.exit_code == 1
    assert "Could not query extension catalog" in result.output
    assert "catalog unreachable" in result.output


def test_list_available_tolerates_entry_missing_name_or_version(project_dir, monkeypatch):
    """A malformed catalog entry missing name/version must not crash listing.

    Catalog entries are untrusted (remote/community catalogs) and only
    guaranteed to be dicts with an injected ``id``. A missing ``name`` or
    ``version`` must degrade to a placeholder, not raise KeyError.
    """
    monkeypatch.chdir(project_dir)

    monkeypatch.setattr(ExtensionManager, "list_installed", lambda self: [])
    monkeypatch.setattr(ExtensionCatalog, "search", lambda self: [
        {"id": "broken-ext"},  # no name, no version, no description
    ])

    result = runner.invoke(app, ["extension", "list", "--available"], obj={"project_root": project_dir})

    assert result.exit_code == 0
    assert "broken-ext" in result.output
    assert "(unnamed)" in result.output
    assert "(v?)" in result.output


def test_list_available_json_null_fields_render_placeholders_not_none(project_dir, monkeypatch):
    """Explicit JSON null fields must fall back, not render the literal "None".

    ``dict.get(key, default)`` only substitutes when the key is absent; an
    explicit ``null`` value reaches ``str()`` and would print "None". Untrusted
    catalog JSON can carry nulls, so name/version/description must degrade to
    their placeholders instead.
    """
    monkeypatch.chdir(project_dir)

    monkeypatch.setattr(ExtensionManager, "list_installed", lambda self: [])
    monkeypatch.setattr(ExtensionCatalog, "search", lambda self: [
        {"id": "null-ext", "name": None, "version": None, "description": None},
    ])

    result = runner.invoke(app, ["extension", "list", "--available"], obj={"project_root": project_dir})

    assert result.exit_code == 0
    assert "null-ext" in result.output
    assert "(unnamed)" in result.output
    assert "(v?)" in result.output
    # The literal string "None" must never leak into the rendered output.
    assert "None" not in result.output


@pytest.mark.parametrize("bad_id", [None, "", "   "])
def test_list_available_skips_entries_without_valid_id(project_dir, monkeypatch, bad_id):
    """Entries with a missing/blank/null id are skipped entirely.

    Such an id cannot be installed (``download_extension()`` would refuse it),
    so printing an install hint like ``specify extension add`` with no id — or
    with ``None`` — only misleads the user. Skip the whole entry.
    """
    monkeypatch.chdir(project_dir)

    monkeypatch.setattr(ExtensionManager, "list_installed", lambda self: [])
    monkeypatch.setattr(ExtensionCatalog, "search", lambda self: [
        {"id": bad_id, "name": "Ghost Ext", "version": "1.0.0"},
        _catalog_entry("real-ext", "Real Ext"),
    ])

    result = runner.invoke(app, ["extension", "list", "--available"], obj={"project_root": project_dir})

    assert result.exit_code == 0
    # The valid entry still renders with its install hint...
    assert "real-ext" in result.output
    assert "specify extension add real-ext" in result.output
    # ...but the id-less entry is dropped: no name, no dangling install hint.
    assert "Ghost Ext" not in result.output


def test_list_all_shows_installed_and_available(project_dir, monkeypatch):
    """--all lists installed extensions and available catalog extensions."""
    monkeypatch.chdir(project_dir)

    monkeypatch.setattr(ExtensionManager, "list_installed", lambda self: [{
        "id": "my-ext",
        "name": "My Ext",
        "version": "2.0.0",
        "description": "installed one",
        "command_count": 1,
        "hook_count": 0,
        "priority": 10,
        "enabled": True,
    }])
    monkeypatch.setattr(ExtensionCatalog, "search", lambda self: [
        _catalog_entry("other-ext", "Other Ext"),
    ])

    result = runner.invoke(app, ["extension", "list", "--all"], obj={"project_root": project_dir})

    assert result.exit_code == 0
    assert "Installed Extensions:" in result.output
    assert "My Ext" in result.output
    assert "Available Extensions:" in result.output
    assert "other-ext" in result.output
