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
from specify_cli.extensions import ExtensionError, ExtensionManager, ExtensionCatalog

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


def test_search_json_null_fields_render_placeholders_not_none(project_dir, monkeypatch):
    """Explicit JSON null fields must fall back, not render the literal "None".

    ``dict.get(key, default)`` only substitutes on an absent key; an explicit
    ``null`` value reaches ``str()`` and would print "None". Name/version/
    description/author must degrade to placeholders instead.
    """
    monkeypatch.chdir(project_dir)

    monkeypatch.setattr(
        ExtensionCatalog,
        "search",
        lambda self, **kwargs: [{
            "id": "null-ext",
            "name": None,
            "version": None,
            "description": None,
            "author": None,
        }],
    )

    result = runner.invoke(app, ["extension", "search"], obj={"project_root": project_dir})

    assert result.exit_code == 0, result.output
    assert "null-ext" in result.output
    assert "(unnamed)" in result.output
    assert "(v?)" in result.output
    assert "Unknown" in result.output  # author fallback
    # The literal string "None" must never leak into rendered output.
    assert "None" not in result.output


@pytest.mark.parametrize("bad_id", [None, "", "   "])
def test_search_skips_entries_without_valid_id(project_dir, monkeypatch, bad_id):
    """Entries with a missing/blank/null id are skipped entirely.

    Such an id cannot be installed (``download_extension()`` refuses it) and
    previously crashed on ``ext['id']`` when absent. Skip the whole entry
    rather than emit a bogus/dangling install hint.
    """
    monkeypatch.chdir(project_dir)

    monkeypatch.setattr(
        ExtensionCatalog,
        "search",
        lambda self, **kwargs: [
            {"id": bad_id, "name": "Ghost Ext", "version": "1.0.0", "description": "d"},
            {"id": "real-ext", "name": "Real Ext", "version": "1.0.0", "description": "d"},
        ],
    )

    result = runner.invoke(app, ["extension", "search"], obj={"project_root": project_dir})

    assert result.exit_code == 0, result.output
    assert "real-ext" in result.output
    assert "specify extension add real-ext" in result.output
    # The id-less entry is dropped: no header, no dangling install hint.
    assert "Ghost Ext" not in result.output


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


def test_download_rejects_catalog_id_path_traversal(project_dir, monkeypatch):
    """Catalog-controlled IDs must not become path-traversing ZIP filenames."""
    monkeypatch.chdir(project_dir)

    catalog = ExtensionCatalog(project_dir)
    malicious_id = "../escape"

    monkeypatch.setattr(
        catalog,
        "_get_merged_extensions",
        lambda: [{
            "id": malicious_id,
            "name": "Evil",
            "version": "1.0.0",
            "download_url": "https://example.com/evil.zip",
        }],
    )

    def fail_open_url(*args, **kwargs):
        raise AssertionError("download should not be attempted for an unsafe id")

    monkeypatch.setattr(catalog, "_open_url", fail_open_url)

    with pytest.raises(ExtensionError, match="Invalid extension ID"):
        catalog.download_extension(malicious_id)


def test_info_json_null_fields_render_placeholders_not_none(project_dir, monkeypatch):
    """`extension info` must coalesce JSON null fields, not print "None".

    ``get_extension_info`` returns the raw merged catalog entry unmodified, so
    an explicit ``null`` name/version/description/author/license reaches the
    renderer. These must degrade to their placeholders, mirroring the fix
    already applied to `list --available` and `search`.
    """
    monkeypatch.chdir(project_dir)

    monkeypatch.setattr(ExtensionManager, "list_installed", lambda self: [])
    monkeypatch.setattr(
        ExtensionCatalog,
        "get_extension_info",
        lambda self, ext_id: {
            "id": "null-ext",
            "name": None,
            "version": None,
            "description": None,
            "author": None,
            "license": None,
        },
    )

    result = runner.invoke(app, ["extension", "info", "null-ext"], obj={"project_root": project_dir})

    assert result.exit_code == 0, result.output
    assert "null-ext" in result.output
    assert "(unnamed)" in result.output
    assert "(v?)" in result.output
    # The literal string "None" must never leak into rendered output.
    assert "None" not in result.output


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("1.2.3", "1.2.3"),          # normal version untouched
        ("1.0/../x", "1.0-..-x"),    # separators collapse to a single segment
        ("../../etc", "etc"),        # leading traversal stripped
        ("a b\\c/d", "a-b-c-d"),     # spaces and both slash kinds collapse
        ("..", "unknown"),           # pure traversal degrades to fallback
        ("   ", "unknown"),          # blank degrades to fallback
        (None, "unknown"),           # JSON null degrades to fallback
        (123, "unknown"),            # non-string degrades to fallback
    ],
)
def test_safe_version_token_strips_separators(raw, expected):
    """Version tokens used in ZIP filenames must never carry path separators."""
    from specify_cli.extensions import _safe_version_token

    token = _safe_version_token(raw)
    assert token == expected
    assert "/" not in token and "\\" not in token


def test_download_sanitizes_catalog_version_into_safe_filename(project_dir, monkeypatch):
    """A catalog version with separators must not yield a nested/escaping path.

    The pre-fix code used the version verbatim, so ``1.0/evil`` produced a
    nested path that stayed inside the target dir (passing the ``resolve()``
    guard) yet failed to write. Sanitizing the version keeps the ZIP a single
    filename directly under the target directory.
    """
    monkeypatch.chdir(project_dir)

    catalog = ExtensionCatalog(project_dir)
    target_dir = project_dir / "downloads"
    target_dir.mkdir()

    monkeypatch.setattr(
        catalog,
        "_get_merged_extensions",
        lambda: [{
            "id": "good-ext",
            "name": "Good",
            "version": "1.0/evil",
            "download_url": "https://example.com/good.zip",
        }],
    )

    class _FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

        def read(self):
            return b"zip-bytes"

    monkeypatch.setattr(catalog, "_open_url", lambda *a, **k: _FakeResponse())
    monkeypatch.setattr(catalog, "_resolve_github_release_asset_api_url", lambda url: None)
    # Skip integrity check (no sha256 in this fixture entry).
    import specify_cli.extensions as ext_module
    monkeypatch.setattr(ext_module, "verify_archive_sha256", lambda *a, **k: None)

    zip_path = catalog.download_extension("good-ext", target_dir=target_dir)

    # The ZIP is a single file directly under target_dir — no nested dirs,
    # no separators leaked from the version.
    assert zip_path.parent == target_dir
    assert "/" not in zip_path.name and "\\" not in zip_path.name
    assert zip_path.name == "good-ext-1.0-evil.zip"
    assert zip_path.read_bytes() == b"zip-bytes"
