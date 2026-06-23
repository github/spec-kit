"""Robustness tests for catalog-driven extension commands.

Catalog entries are untrusted (remote/community catalogs) and only guaranteed
to be dicts with an injected ``id`` — ``_get_merged_extensions`` does not
validate any other field. ``extension search`` and ``extension info`` must
therefore tolerate entries missing ``name``/``version``/``description`` (no
KeyError), entries whose ``requires``/``provides`` are non-dicts (no
AttributeError), and must escape catalog-controlled values like ``stars``
before printing them as Rich markup.
"""

import pytest
from typer.testing import CliRunner

from specify_cli import app
from specify_cli.extensions import ExtensionManager, ExtensionCatalog

runner = CliRunner()


@pytest.fixture
def project_dir(tmp_path):
    proj_dir = tmp_path / "project"
    proj_dir.mkdir()
    (proj_dir / ".specify").mkdir()
    (proj_dir / ".specify" / "config.toml").write_text("ai = 'claude'")
    return proj_dir


def test_search_tolerates_entry_missing_name_version_description(project_dir, monkeypatch):
    """A malformed catalog entry must not crash `extension search`."""
    monkeypatch.chdir(project_dir)

    monkeypatch.setattr(
        ExtensionCatalog,
        "search",
        lambda self, **kwargs: [{"id": "broken-ext"}],  # only id present
    )

    result = runner.invoke(app, ["extension", "search"], obj={"project_root": project_dir})

    assert result.exit_code == 0, result.output
    assert "broken-ext" in result.output
    assert "(unnamed)" in result.output
    assert "(v?)" in result.output


def test_search_escapes_markup_in_stars(project_dir, monkeypatch):
    """Catalog-controlled `stars` must be escaped, not parsed as Rich markup."""
    monkeypatch.chdir(project_dir)

    monkeypatch.setattr(
        ExtensionCatalog,
        "search",
        lambda self, **kwargs: [{
            "id": "starry",
            "name": "Starry",
            "version": "1.0.0",
            "description": "d",
            "stars": "[red]999[/red]",
        }],
    )

    result = runner.invoke(app, ["extension", "search"], obj={"project_root": project_dir})

    assert result.exit_code == 0, result.output
    # Escaped markup is rendered literally rather than swallowed by Rich.
    assert "[red]999[/red]" in result.output


def test_info_tolerates_missing_fields_and_non_dict_sections(project_dir, monkeypatch):
    """`extension info` must survive a malformed catalog entry.

    Missing name/version/description → placeholders (no KeyError); requires as a
    list and provides as a string → skipped, not `.get()`-crashed.
    """
    monkeypatch.chdir(project_dir)

    monkeypatch.setattr(ExtensionManager, "list_installed", lambda self: [])
    monkeypatch.setattr(
        ExtensionCatalog,
        "get_extension_info",
        lambda self, ext_id: {
            "id": "broken-ext",
            "requires": ["not", "a", "dict"],
            "provides": "junk",
            "stars": "[bold]42[/bold]",
        },
    )

    result = runner.invoke(app, ["extension", "info", "broken-ext"], obj={"project_root": project_dir})

    assert result.exit_code == 0, result.output
    assert "broken-ext" in result.output
    assert "(unnamed)" in result.output
    assert "(v?)" in result.output
    # Non-dict requires/provides are skipped, not crashed on.
    assert "Requirements:" not in result.output
    assert "Provides:" not in result.output
    # stars is escaped.
    assert "[bold]42[/bold]" in result.output
