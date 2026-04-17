"""
Tests for download_template_from_github release-fallback + cache behavior.

Covers the regression where GitHub releases v0.4.5–v0.6.2 shipped with
zero template assets, causing specify init to hard-fail with exit code 1.

The fix iterates older releases when the latest has no matching assets, and
caches successful downloads so that future runs (and offline/air-gapped
environments) do not need a network call at all.
"""

import json
import shutil
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch, call
import pytest

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

PATTERN = "spec-kit-template-claude-sh"


def _make_release(tag: str, *, has_asset: bool) -> dict:
    """Build a minimal GitHub release dict."""
    assets = []
    if has_asset:
        assets.append(
            {
                "name": f"{PATTERN}-{tag}.zip",
                "browser_download_url": f"https://example.com/{tag}.zip",
                "size": 1000,
            }
        )
    return {"tag_name": tag, "assets": assets}


def _make_response(data: dict | list, *, status: int = 200) -> MagicMock:
    resp = MagicMock()
    resp.status_code = status
    resp.json.return_value = data
    resp.headers = {"content-length": "0"}
    resp.iter_bytes = MagicMock(return_value=iter([b"fake-zip-content"]))
    resp.__enter__ = lambda s: s
    resp.__exit__ = MagicMock(return_value=False)
    return resp


# ---------------------------------------------------------------------------
# Test: latest has no assets → falls back to older release that does
# ---------------------------------------------------------------------------

def test_falls_back_to_older_release_when_latest_has_no_assets(tmp_path):
    """
    Scenario: /releases/latest returns v0.6.2 with zero assets.
    /releases?per_page=10 returns v0.6.2 (no assets) and v0.4.4 (has asset).
    Expected: template downloaded from v0.4.4 without raising Exit(1).
    """
    from specify_cli import download_template_from_github, _get_cache_dir

    latest_release = _make_release("v0.6.2", has_asset=False)
    paginated_releases = [
        _make_release("v0.6.2", has_asset=False),
        _make_release("v0.4.4", has_asset=True),
    ]

    download_resp = _make_response({})
    download_resp.status_code = 200
    download_resp.headers = {"content-length": "16"}

    mock_client = MagicMock()
    mock_client.get.side_effect = [
        _make_response(latest_release),      # /releases/latest
        _make_response(paginated_releases),  # /releases?per_page=10
    ]
    mock_client.stream.return_value = download_resp

    with patch.dict("os.environ", {"SPECIFY_OFFLINE": ""}):
        zip_path, meta = download_template_from_github(
            "claude",
            tmp_path,
            script_type="sh",
            verbose=False,
            show_progress=False,
            client=mock_client,
        )

    assert meta["release"] == "v0.4.4"
    assert PATTERN in meta["filename"]
    assert zip_path.exists(), f"Expected zip at {zip_path}"


# ---------------------------------------------------------------------------
# Test: no releases have assets → stale cache used instead of hard fail
# ---------------------------------------------------------------------------

def test_uses_stale_cache_when_all_releases_have_no_assets(tmp_path):
    """
    Scenario: all releases have no assets but a cached zip exists.
    Expected: stale cached zip is returned with a warning, no Exit(1).
    """
    import specify_cli as cli_module
    from specify_cli import download_template_from_github

    # Seed the cache with a fake zip
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    cached_zip = cache_dir / f"{PATTERN}-v0.4.4.zip"
    cached_zip.write_bytes(b"cached-zip-content")
    meta_path = cache_dir / "cache-meta.json"
    meta_path.write_text(json.dumps({
        cached_zip.name: {
            "filename": cached_zip.name,
            "size": 18,
            "release": "v0.4.4",
            "asset_url": "https://example.com/v0.4.4.zip",
            "cached_at": "2020-01-01T00:00:00+00:00",  # very stale
        }
    }))

    mock_client = MagicMock()
    mock_client.get.side_effect = [
        _make_response(_make_release("v0.6.2", has_asset=False)),  # latest
        _make_response([
            _make_release("v0.6.2", has_asset=False),
            _make_release("v0.5.0", has_asset=False),
        ]),                                                          # paginated
    ]

    with (
        patch("specify_cli._get_cache_dir", return_value=cache_dir),
        patch.dict("os.environ", {"SPECIFY_OFFLINE": ""}),
    ):
        zip_path, meta = download_template_from_github(
            "claude",
            tmp_path,
            script_type="sh",
            verbose=False,
            show_progress=False,
            client=mock_client,
        )

    # The stale-cache path copies the zip content; release may be "cached (stale)"
    # or read from cache-meta.json — either is acceptable.
    assert zip_path.read_bytes() == b"cached-zip-content"


# ---------------------------------------------------------------------------
# Test: SPECIFY_OFFLINE=1 uses fresh cache without network
# ---------------------------------------------------------------------------

def test_offline_mode_uses_cache_without_network(tmp_path):
    """SPECIFY_OFFLINE=1 should return a cached template without any HTTP call."""
    import specify_cli as cli_module

    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    cached_zip = cache_dir / f"{PATTERN}-v0.4.4.zip"
    cached_zip.write_bytes(b"offline-zip-content")
    meta_path = cache_dir / "cache-meta.json"
    from datetime import datetime, timezone
    meta_path.write_text(json.dumps({
        cached_zip.name: {
            "filename": cached_zip.name,
            "size": 19,
            "release": "v0.4.4",
            "asset_url": "",
            "cached_at": datetime.now(timezone.utc).isoformat(),  # fresh
        }
    }))

    mock_client = MagicMock()

    with (
        patch("specify_cli._get_cache_dir", return_value=cache_dir),
        patch.dict("os.environ", {"SPECIFY_OFFLINE": "1"}),
    ):
        from specify_cli import download_template_from_github
        zip_path, meta = download_template_from_github(
            "claude",
            tmp_path,
            script_type="sh",
            verbose=False,
            show_progress=False,
            client=mock_client,
        )

    # No HTTP calls should have been made
    mock_client.get.assert_not_called()
    mock_client.stream.assert_not_called()
    assert zip_path.read_bytes() == b"offline-zip-content"


# ---------------------------------------------------------------------------
# Test: SPECIFY_OFFLINE=1 with no cache → hard fail with clear message
# ---------------------------------------------------------------------------

def test_offline_mode_without_cache_raises_exit(tmp_path):
    """SPECIFY_OFFLINE=1 with an empty cache should raise typer.Exit(1).

    typer.Exit wraps click.exceptions.Exit, which is NOT a subclass of
    SystemExit, so we catch both and check the exit code.
    """
    import click

    cache_dir = tmp_path / "empty_cache"
    cache_dir.mkdir()

    mock_client = MagicMock()

    with (
        patch("specify_cli._get_cache_dir", return_value=cache_dir),
        patch.dict("os.environ", {"SPECIFY_OFFLINE": "1"}),
    ):
        from specify_cli import download_template_from_github
        with pytest.raises((SystemExit, click.exceptions.Exit)) as exc_info:
            download_template_from_github(
                "claude",
                tmp_path,
                script_type="sh",
                verbose=False,
                show_progress=False,
                client=mock_client,
            )
        exit_obj = exc_info.value
        code = getattr(exit_obj, "exit_code", None) or getattr(exit_obj, "code", None)
        assert code == 1, f"Expected exit code 1, got {code}"

    mock_client.get.assert_not_called()


# ---------------------------------------------------------------------------
# Test: successful download is cached for future use
# ---------------------------------------------------------------------------

def test_successful_download_is_cached(tmp_path):
    """After a successful download the zip should appear in the cache dir."""
    import specify_cli as cli_module

    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()

    mock_client = MagicMock()
    mock_client.get.side_effect = [
        _make_response(_make_release("v0.4.4", has_asset=True)),   # latest
    ]
    download_resp = _make_response({})
    download_resp.headers = {"content-length": "16"}
    download_resp.iter_bytes = MagicMock(return_value=iter([b"fresh-zip-data!!"]))
    mock_client.stream.return_value = download_resp

    with (
        patch("specify_cli._get_cache_dir", return_value=cache_dir),
        patch.dict("os.environ", {"SPECIFY_OFFLINE": ""}),
    ):
        from specify_cli import download_template_from_github
        zip_path, meta = download_template_from_github(
            "claude",
            tmp_path,
            script_type="sh",
            verbose=False,
            show_progress=False,
            client=mock_client,
        )

    cached_files = list(cache_dir.glob(f"*{PATTERN}*.zip"))
    assert cached_files, "Expected a cached zip after successful download"
    meta_path = cache_dir / "cache-meta.json"
    assert meta_path.exists(), "Expected cache-meta.json to be written"
    meta_data = json.loads(meta_path.read_text())
    assert any(PATTERN in k for k in meta_data), "cache-meta.json should contain the template entry"
