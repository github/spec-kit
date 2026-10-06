"""Tests for preset discovery and downloads in specify_cli.presets._catalog."""

import io
import json
import tarfile
import zipfile
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock

import pytest
import yaml

from specify_cli.presets import (
    PresetCatalog,
    PresetCatalogEntry,
    PresetError,
    PresetValidationError,
)


class TestPresetCatalog:
    """Test template catalog functionality."""

    def _inject_github_config(self, monkeypatch, token_env="GH_TOKEN"):
        from tests.specify_cli.authentication.helpers import inject_github_config
        inject_github_config(monkeypatch, token_env)

    def test_default_catalog_url(self, project_dir):
        """Test default catalog URL."""
        catalog = PresetCatalog(project_dir)
        assert catalog.DEFAULT_CATALOG_URL.startswith("https://")
        assert catalog.DEFAULT_CATALOG_URL.endswith("/presets/catalog.json")

    def test_community_catalog_url(self, project_dir):
        """Test community catalog URL."""
        catalog = PresetCatalog(project_dir)
        assert "presets/catalog.community.json" in catalog.COMMUNITY_CATALOG_URL

    def test_cache_validation_no_cache(self, project_dir):
        """Test cache validation when no cache exists."""
        catalog = PresetCatalog(project_dir)
        assert catalog.is_cache_valid() is False

    def test_cache_validation_valid(self, project_dir):
        """Test cache validation with valid cache."""
        catalog = PresetCatalog(project_dir)
        catalog.cache_dir.mkdir(parents=True, exist_ok=True)

        catalog.cache_file.write_text(json.dumps({
            "schema_version": "1.0",
            "presets": {},
        }))
        catalog.cache_metadata_file.write_text(json.dumps({
            "cached_at": datetime.now(timezone.utc).isoformat(),
        }))

        assert catalog.is_cache_valid() is True

    def test_cache_validation_expired(self, project_dir):
        """Test cache validation with expired cache."""
        catalog = PresetCatalog(project_dir)
        catalog.cache_dir.mkdir(parents=True, exist_ok=True)

        catalog.cache_file.write_text(json.dumps({
            "schema_version": "1.0",
            "presets": {},
        }))
        catalog.cache_metadata_file.write_text(json.dumps({
            "cached_at": "2020-01-01T00:00:00+00:00",
        }))

        assert catalog.is_cache_valid() is False

    def test_cache_validation_corrupted(self, project_dir):
        """Test cache validation with corrupted metadata."""
        catalog = PresetCatalog(project_dir)
        catalog.cache_dir.mkdir(parents=True, exist_ok=True)

        catalog.cache_file.write_text("not json")
        catalog.cache_metadata_file.write_text("not json")

        assert catalog.is_cache_valid() is False

    def test_clear_cache(self, project_dir):
        """Test clearing the cache."""
        catalog = PresetCatalog(project_dir)
        catalog.cache_dir.mkdir(parents=True, exist_ok=True)
        catalog.cache_file.write_text("{}")
        catalog.cache_metadata_file.write_text("{}")

        catalog.clear_cache()

        assert not catalog.cache_file.exists()
        assert not catalog.cache_metadata_file.exists()

    def test_search_with_cached_data(self, project_dir, monkeypatch):
        """Test search with cached catalog data."""
        from unittest.mock import patch

        monkeypatch.delenv("SPECKIT_PRESET_CATALOG_URL", raising=False)
        catalog = PresetCatalog(project_dir)
        catalog.cache_dir.mkdir(parents=True, exist_ok=True)

        catalog_data = {
            "schema_version": "1.0",
            "presets": {
                "safe-agile": {
                    "name": "SAFe Agile Templates",
                    "description": "SAFe-aligned templates",
                    "author": "agile-community",
                    "version": "1.0.0",
                    "tags": ["safe", "agile"],
                },
                "healthcare": {
                    "name": "Healthcare Compliance",
                    "description": "HIPAA-compliant templates",
                    "author": "healthcare-org",
                    "version": "1.0.0",
                    "tags": ["healthcare", "hipaa"],
                },
            }
        }

        catalog.cache_file.write_text(json.dumps(catalog_data))
        catalog.cache_metadata_file.write_text(json.dumps({
            "cached_at": datetime.now(timezone.utc).isoformat(),
        }))

        # Isolate from community catalog so results are deterministic
        default_only = [PresetCatalogEntry(url=catalog.DEFAULT_CATALOG_URL, name="default", priority=1, install_allowed=True)]
        with patch.object(catalog, "get_active_catalogs", return_value=default_only):
            # Search by query
            results = catalog.search(query="agile")
            assert len(results) == 1
            assert results[0]["id"] == "safe-agile"

            # Search by tag
            results = catalog.search(tag="hipaa")
            assert len(results) == 1
            assert results[0]["id"] == "healthcare"

            # Search by author
            results = catalog.search(author="agile-community")
            assert len(results) == 1

            # Search all
            results = catalog.search()
            assert len(results) == 2

    def test_get_pack_info(self, project_dir):
        """Test getting info for a specific pack."""
        catalog = PresetCatalog(project_dir)
        catalog.cache_dir.mkdir(parents=True, exist_ok=True)

        catalog_data = {
            "schema_version": "1.0",
            "presets": {
                "test-pack": {
                    "name": "Test Pack",
                    "version": "1.0.0",
                },
            }
        }

        catalog.cache_file.write_text(json.dumps(catalog_data))
        catalog.cache_metadata_file.write_text(json.dumps({
            "cached_at": datetime.now(timezone.utc).isoformat(),
        }))

        info = catalog.get_pack_info("test-pack")
        assert info is not None
        assert info["name"] == "Test Pack"
        assert info["id"] == "test-pack"

        assert catalog.get_pack_info("nonexistent") is None

    def test_validate_catalog_url_https(self, project_dir):
        """Test that HTTPS URLs are accepted."""
        catalog = PresetCatalog(project_dir)
        catalog._validate_catalog_url("https://example.com/catalog.json")

    def test_validate_catalog_url_http_rejected(self, project_dir):
        """Test that HTTP URLs are rejected."""
        catalog = PresetCatalog(project_dir)
        with pytest.raises(PresetValidationError, match="must use HTTPS"):
            catalog._validate_catalog_url("http://example.com/catalog.json")

    def test_validate_catalog_url_localhost_http_allowed(self, project_dir):
        """Test that HTTP is allowed for localhost."""
        catalog = PresetCatalog(project_dir)
        catalog._validate_catalog_url("http://localhost:8080/catalog.json")
        catalog._validate_catalog_url("http://127.0.0.1:8080/catalog.json")

    @pytest.mark.parametrize(
        "url",
        [
            "https://:8080",                # port only, no host
            "https://:8080/catalog.json",   # port only, with path
            "https://:0",                   # port only, no host
            "https://user@",                # userinfo only, no host
            "https://user:pass@",           # userinfo only, no host
        ],
    )
    def test_validate_catalog_url_hostless_rejected(self, project_dir, url):
        """Reject host-less URLs whose netloc is truthy but hostname is None (#3209).

        ``urlparse('https://:8080').netloc`` is ``':8080'`` (truthy) but its
        ``hostname`` is ``None``, so a netloc-based check would accept a URL
        with no actual host, contradicting the "valid URL with a host" error.
        """
        catalog = PresetCatalog(project_dir)
        with pytest.raises(PresetValidationError, match="valid URL with a host"):
            catalog._validate_catalog_url(url)

    def test_validate_catalog_url_malformed_rejected(self, project_dir):
        """A malformed URL raises PresetValidationError, not a raw ValueError.

        ``urlparse('https://[::1').hostname`` raises ``ValueError: Invalid IPv6
        URL`` (unterminated bracket). Without wrapping, that leaks past callers'
        ``except PresetValidationError`` guards and crashes the CLI. Mirrors the
        shared ``CatalogStackBase`` (#3435) and ``IntegrationCatalog`` behaviour.
        """
        catalog = PresetCatalog(project_dir)
        with pytest.raises(PresetValidationError, match="malformed"):
            catalog._validate_catalog_url("https://[::1")

    def test_validate_catalog_url_out_of_range_port_rejected(self, project_dir):
        """An out-of-range port raises ValueError lazily on ``.port`` access.

        ``urlparse(...).hostname`` alone does not validate the port, so
        without a ``_ = parsed.port`` probe inside the try/except, a URL like
        ``https://example.com:99999/catalog.json`` sails through this
        validator and only fails later, at fetch time, with a raw
        untranslated error instead of a clean ``PresetValidationError``. The
        sibling ``preset add --from <url>`` download-URL guard already
        catches this shape (see
        ``test_preset_add_from_url_out_of_range_port_exits_cleanly``); this
        catalog-source-URL validator had drifted from it and from the
        original guard in ``specify_cli.catalogs``/
        ``bundler/services/adapters.py``.
        """
        catalog = PresetCatalog(project_dir)
        with pytest.raises(PresetValidationError, match="malformed"):
            catalog._validate_catalog_url("https://example.com:99999/catalog.json")

    def test_env_var_catalog_url(self, project_dir, monkeypatch):
        """Test catalog URL from environment variable."""
        monkeypatch.setenv("SPECKIT_PRESET_CATALOG_URL", "https://custom.example.com/catalog.json")
        catalog = PresetCatalog(project_dir)
        assert catalog.get_catalog_url() == "https://custom.example.com/catalog.json"

    # --- _make_request / GitHub auth ---

    def test_make_request_no_token_no_auth_header(self, project_dir, monkeypatch):
        """Without a token, requests carry no Authorization header."""
        monkeypatch.delenv("GITHUB_TOKEN", raising=False)
        monkeypatch.delenv("GH_TOKEN", raising=False)
        catalog = PresetCatalog(project_dir)
        req = catalog._make_request("https://raw.githubusercontent.com/org/repo/main/catalog.json")
        assert "Authorization" not in req.headers

    def test_make_request_whitespace_only_github_token_ignored(self, project_dir, monkeypatch):
        """A whitespace-only GITHUB_TOKEN is treated as unset."""
        monkeypatch.setenv("GITHUB_TOKEN", "   ")
        monkeypatch.delenv("GH_TOKEN", raising=False)
        catalog = PresetCatalog(project_dir)
        req = catalog._make_request("https://raw.githubusercontent.com/org/repo/main/catalog.json")
        assert "Authorization" not in req.headers

    def test_make_request_whitespace_github_token_falls_back_to_gh_token(self, project_dir, monkeypatch):
        """When GITHUB_TOKEN is whitespace-only, GH_TOKEN is used as fallback."""
        monkeypatch.setenv("GITHUB_TOKEN", "   ")
        monkeypatch.setenv("GH_TOKEN", "ghp_fallback")
        self._inject_github_config(monkeypatch, token_env="GH_TOKEN")
        catalog = PresetCatalog(project_dir)
        req = catalog._make_request("https://raw.githubusercontent.com/org/repo/main/catalog.json")
        assert req.get_header("Authorization") == "Bearer ghp_fallback"

    def test_make_request_github_token_added_for_github_url(self, project_dir, monkeypatch):
        """GITHUB_TOKEN is attached for raw.githubusercontent.com URLs."""
        monkeypatch.setenv("GITHUB_TOKEN", "ghp_testtoken")
        monkeypatch.delenv("GH_TOKEN", raising=False)
        self._inject_github_config(monkeypatch, token_env="GITHUB_TOKEN")
        catalog = PresetCatalog(project_dir)
        req = catalog._make_request("https://raw.githubusercontent.com/org/repo/main/catalog.json")
        assert req.get_header("Authorization") == "Bearer ghp_testtoken"

    def test_make_request_gh_token_fallback(self, project_dir, monkeypatch):
        """GH_TOKEN is used when GITHUB_TOKEN is absent."""
        monkeypatch.delenv("GITHUB_TOKEN", raising=False)
        monkeypatch.setenv("GH_TOKEN", "ghp_ghtoken")
        self._inject_github_config(monkeypatch, token_env="GH_TOKEN")
        catalog = PresetCatalog(project_dir)
        req = catalog._make_request("https://github.com/org/repo/releases/download/v1/pack.zip")
        assert req.get_header("Authorization") == "Bearer ghp_ghtoken"

    def test_make_request_gh_token_takes_precedence(self, project_dir, monkeypatch):
        """When auth.json uses GH_TOKEN, that token is used regardless of GITHUB_TOKEN."""
        monkeypatch.setenv("GITHUB_TOKEN", "ghp_secondary")
        monkeypatch.setenv("GH_TOKEN", "ghp_primary")
        self._inject_github_config(monkeypatch, token_env="GH_TOKEN")
        catalog = PresetCatalog(project_dir)
        req = catalog._make_request("https://api.github.com/repos/org/repo")
        assert req.get_header("Authorization") == "Bearer ghp_primary"

    def test_make_request_token_added_for_codeload_github_com(self, project_dir, monkeypatch):
        """GITHUB_TOKEN is attached for codeload.github.com URLs."""
        monkeypatch.setenv("GITHUB_TOKEN", "ghp_testtoken")
        self._inject_github_config(monkeypatch, token_env="GITHUB_TOKEN")
        catalog = PresetCatalog(project_dir)
        req = catalog._make_request("https://codeload.github.com/org/repo/zip/refs/tags/v1.0.0")
        assert req.get_header("Authorization") == "Bearer ghp_testtoken"

    def test_make_request_no_auth_for_non_matching_host(self, project_dir, monkeypatch):
        """Auth is NOT attached to hosts not listed in auth.json."""
        monkeypatch.setenv("GITHUB_TOKEN", "ghp_testtoken")
        self._inject_github_config(monkeypatch, token_env="GITHUB_TOKEN")
        catalog = PresetCatalog(project_dir)
        req = catalog._make_request("https://internal.example.com/catalog.json")
        assert "Authorization" not in req.headers

    def test_make_request_no_auth_when_no_config(self, project_dir, monkeypatch):
        """No auth header when no auth.json config exists."""
        monkeypatch.delenv("GITHUB_TOKEN", raising=False)
        monkeypatch.delenv("GH_TOKEN", raising=False)
        catalog = PresetCatalog(project_dir)
        req = catalog._make_request("https://github.com/org/repo/releases/download/v1/pack.zip")
        assert "Authorization" not in req.headers

    def test_fetch_single_catalog_sends_auth_header(self, project_dir, monkeypatch):
        """_fetch_single_catalog passes Authorization header when configured."""
        from unittest.mock import patch, MagicMock

        monkeypatch.setenv("GITHUB_TOKEN", "ghp_testtoken")
        self._inject_github_config(monkeypatch, token_env="GITHUB_TOKEN")
        catalog = PresetCatalog(project_dir)

        catalog_data = {"schema_version": "1.0", "presets": {}}
        mock_response = MagicMock()
        mock_response.read.side_effect = io.BytesIO(json.dumps(catalog_data).encode()).read
        mock_response.__enter__ = lambda s: s
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_response.geturl.return_value = "https://raw.githubusercontent.com/org/repo/main/presets/catalog.json"

        captured = {}
        mock_opener = MagicMock()

        def fake_open(req, timeout=None):
            captured["req"] = req
            return mock_response

        mock_opener.open.side_effect = fake_open

        entry = PresetCatalogEntry(
            url="https://raw.githubusercontent.com/org/repo/main/presets/catalog.json",
            name="private",
            priority=1,
            install_allowed=True,
        )

        with patch("specify_cli.authentication.http.urllib.request.build_opener", return_value=mock_opener):
            catalog._fetch_single_catalog(entry, force_refresh=True)

        assert captured["req"].get_header("Authorization") == "Bearer ghp_testtoken"

    def test_fetch_single_catalog_revalidates_redirected_url(self, project_dir):
        """An HTTPS catalog URL that redirects to http:// must be rejected AFTER
        the redirect. _open_url follows redirects (auth stripped on downgrade),
        so without re-validating response.geturl() the http payload would still
        be fetched and trusted — and it supplies each preset's download_url +
        sha256, defeating verify_archive_sha256. Parity with the
        integrations/workflows catalog fetchers."""
        catalog = PresetCatalog(project_dir)

        class _Resp:
            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False

            def read(self):
                return json.dumps({"schema_version": "1.0", "presets": {}}).encode()

            def geturl(self):
                return "http://evil.test/catalog.json"  # downgraded via redirect

        catalog._open_url = lambda url, timeout=None, redirect_validator=None: _Resp()

        entry = PresetCatalogEntry(
            url="https://good.example/catalog.json",
            name="c",
            priority=1,
            install_allowed=True,
        )
        with pytest.raises(PresetValidationError, match="HTTPS"):
            catalog._fetch_single_catalog(entry, force_refresh=True)

    def test_fetch_single_catalog_validates_every_redirect_hop(self, project_dir):
        """A redirect_validator is passed to _open_url and rejects a non-HTTPS
        INTERMEDIATE hop — closing the https -> http -> attacker-https chain that
        a terminal-URL-only check would miss."""
        catalog = PresetCatalog(project_dir)
        captured = {}

        def fake_open(url, timeout=None, redirect_validator=None):
            captured["rv"] = redirect_validator
            # Simulate the hop urllib validates before following the redirect.
            redirect_validator("https://good.example/catalog.json", "http://evil.test/hop")
            raise AssertionError("redirect_validator should have raised")

        catalog._open_url = fake_open
        entry = PresetCatalogEntry(
            url="https://good.example/catalog.json",
            name="c",
            priority=1,
            install_allowed=True,
        )
        with pytest.raises(PresetValidationError, match="HTTPS"):
            catalog._fetch_single_catalog(entry, force_refresh=True)
        assert captured["rv"] is not None

    def test_fetch_catalog_legacy_revalidates_redirected_url(self, project_dir):
        """The legacy single-catalog fetch_catalog() path also rejects an
        HTTPS -> http redirected payload (final geturl() check), matching
        _fetch_single_catalog — it previously parsed the body with no check."""
        catalog = PresetCatalog(project_dir)

        class _Resp:
            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False

            def read(self):
                return json.dumps({"schema_version": "1.0", "presets": {}}).encode()

            def geturl(self):
                return "http://evil.test/catalog.json"

        catalog._open_url = lambda url, timeout=None, redirect_validator=None: _Resp()
        with pytest.raises(PresetError, match="HTTPS"):
            catalog.fetch_catalog(force_refresh=True)

    def test_fetch_catalog_legacy_validates_every_redirect_hop(self, project_dir):
        """The legacy fetch_catalog() path also validates every INTERMEDIATE hop
        (not just the terminal URL): it must supply a redirect_validator that
        rejects an insecure hop, so an https -> http -> https chain is caught."""
        catalog = PresetCatalog(project_dir)
        captured = {}

        def fake_open(url, timeout=None, redirect_validator=None):
            captured["rv"] = redirect_validator
            redirect_validator(url, "http://evil.test/hop")
            raise AssertionError("redirect_validator should have raised")

        catalog._open_url = fake_open
        with pytest.raises(PresetError, match="HTTPS"):
            catalog.fetch_catalog(force_refresh=True)
        assert captured["rv"] is not None

    @pytest.mark.parametrize(
        "payload",
        [
            # Root is not a JSON object.
            [],
            "oops",
            42,
            None,
            # Root is fine but ``presets`` is the wrong type.
            {"schema_version": "1.0", "presets": []},
            {"schema_version": "1.0", "presets": "oops"},
            {"schema_version": "1.0", "presets": None},
            {"schema_version": "1.0", "presets": 42},
        ],
    )
    def test_fetch_single_catalog_rejects_malformed_payload(self, project_dir, payload):
        """Malformed catalog payloads raise PresetError, not AttributeError.

        Without this guard, a payload like ``{"presets": []}`` would pass the
        key-presence check and then crash with ``AttributeError: 'list' object
        has no attribute 'items'`` deep inside ``_get_merged_packs``. The
        sibling integration catalog reader already validates both the root
        object and the nested mapping (see ``integrations/catalog.py``); the
        preset catalog must stay consistent.
        """
        from unittest.mock import patch, MagicMock

        catalog = PresetCatalog(project_dir)

        mock_response = MagicMock()
        mock_response.read.side_effect = io.BytesIO(json.dumps(payload).encode()).read
        mock_response.__enter__ = lambda s: s
        mock_response.__exit__ = MagicMock(return_value=False)
        # A real urllib response reports the final URL (== request URL with no
        # redirect); the fetcher re-validates it after redirects.
        mock_response.geturl.return_value = "https://example.com/catalog.json"

        entry = PresetCatalogEntry(
            url="https://example.com/catalog.json",
            name="default",
            priority=1,
            install_allowed=True,
        )

        with patch.object(catalog, "_open_url", return_value=mock_response):
            with pytest.raises(PresetError, match="Invalid preset catalog format"):
                catalog._fetch_single_catalog(entry, force_refresh=True)

    @pytest.mark.parametrize(
        "cached_payload",
        [
            [],
            "oops",
            42,
            None,
            {"schema_version": "1.0", "presets": []},
            {"schema_version": "1.0", "presets": "oops"},
            {"schema_version": "1.0", "presets": None},
        ],
    )
    def test_fetch_single_catalog_rejects_malformed_cached_payload(
        self, project_dir, cached_payload
    ):
        """A poisoned cache silently falls back to the network instead of
        crashing — cached payloads pass through the same shape validation
        as freshly-fetched ones.

        Without this, a cache poisoned by an older spec-kit version (or a
        manual edit, or an upstream that briefly served a bad payload
        before the network guards landed) would re-crash every invocation
        of ``_get_merged_packs`` despite the cache being "valid" by age.
        The recovery contract is: if the cached payload fails validation,
        drop it and refetch — never propagate ``AttributeError`` to the
        caller.
        """
        from unittest.mock import patch, MagicMock

        catalog = PresetCatalog(project_dir)

        # Poison the default-URL cache. ``DEFAULT_CATALOG_URL`` and
        # non-default URLs both flow through the same cache-load branch.
        cache_file, metadata_file = catalog._get_cache_paths(
            catalog.DEFAULT_CATALOG_URL
        )
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        cache_file.write_text(json.dumps(cached_payload))
        metadata_file.write_text(
            json.dumps(
                {
                    "cached_at": datetime.now(timezone.utc).isoformat(),
                    "catalog_url": catalog.DEFAULT_CATALOG_URL,
                }
            )
        )

        # Network refetch returns a valid payload so the recovery path
        # can complete.
        valid = {
            "schema_version": "1.0",
            "presets": {"foo": {"name": "Foo", "version": "1.0.0"}},
        }
        mock_response = MagicMock()
        mock_response.read.side_effect = io.BytesIO(json.dumps(valid).encode()).read
        mock_response.__enter__ = lambda s: s
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_response.geturl.return_value = catalog.DEFAULT_CATALOG_URL

        entry = PresetCatalogEntry(
            url=catalog.DEFAULT_CATALOG_URL,
            name="default",
            priority=1,
            install_allowed=True,
        )

        with patch.object(catalog, "_open_url", return_value=mock_response):
            result = catalog._fetch_single_catalog(entry, force_refresh=False)

        # The poisoned cache was discarded and the network payload returned.
        assert result == valid

    @pytest.mark.parametrize(
        "payload",
        [
            # Root is not a JSON object.
            [],
            "oops",
            42,
            None,
            # Root is fine but ``presets`` is the wrong type.
            {"schema_version": "1.0", "presets": []},
            {"schema_version": "1.0", "presets": "oops"},
            {"schema_version": "1.0", "presets": None},
        ],
    )
    def test_fetch_catalog_rejects_malformed_payload(self, project_dir, payload):
        """Legacy ``fetch_catalog`` reuses the same shape-validation helper.

        Before this change ``fetch_catalog`` only checked key presence —
        so a payload like ``42`` would crash with
        ``TypeError: argument of type 'int' is not iterable`` during the
        ``"schema_version" in catalog_data`` check, and an entry mapping
        of the wrong type would crash downstream. Reusing
        ``_validate_catalog_payload`` keeps the network-side behaviour of
        the legacy single-catalog method consistent with the multi-catalog
        ``_fetch_single_catalog`` path.
        """
        from unittest.mock import patch, MagicMock

        catalog = PresetCatalog(project_dir)
        mock_response = MagicMock()
        mock_response.read.side_effect = io.BytesIO(json.dumps(payload).encode()).read
        mock_response.__enter__ = lambda s: s
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_response.geturl.return_value = "https://example.com/catalog.json"

        with patch.object(catalog, "_open_url", return_value=mock_response):
            with pytest.raises(PresetError, match="Invalid preset catalog format"):
                catalog.fetch_catalog(force_refresh=True)

    def test_fetch_catalog_recovers_from_unreadable_cache(self, project_dir):
        """An unreadable / wrong-encoded cache file silently refetches.

        The cache contract is best-effort: a JSON-decode failure, an OS
        read failure (permissions / disk / handle limit), or an invalid
        text encoding on a cache file written by an older client must
        all fall through to the network fetch rather than crash the
        caller. Covers Copilot's review point that the previous
        ``except (json.JSONDecodeError, OSError)`` was missing
        ``UnicodeError``.
        """
        from unittest.mock import patch, MagicMock

        catalog = PresetCatalog(project_dir)
        catalog.cache_dir.mkdir(parents=True, exist_ok=True)
        # Invalid UTF-8 bytes so ``read_text`` raises ``UnicodeDecodeError``
        # (a subclass of ``UnicodeError``).
        catalog.cache_file.write_bytes(b"\xff\xfe\x00not-utf-8")
        catalog.cache_metadata_file.write_text(
            json.dumps(
                {
                    "cached_at": datetime.now(timezone.utc).isoformat(),
                    "catalog_url": catalog.get_catalog_url(),
                }
            ),
            encoding="utf-8",
        )

        valid = {
            "schema_version": "1.0",
            "presets": {"foo": {"name": "Foo", "version": "1.0.0"}},
        }
        mock_response = MagicMock()
        mock_response.read.side_effect = io.BytesIO(json.dumps(valid).encode()).read
        mock_response.__enter__ = lambda s: s
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_response.geturl.return_value = "https://example.com/catalog.json"

        with patch.object(catalog, "_open_url", return_value=mock_response):
            result = catalog.fetch_catalog(force_refresh=False)

        # Recovered via network rather than crashing on the unreadable cache.
        assert result == valid

    def test_fetch_catalog_recovers_from_unreadable_metadata(self, project_dir):
        """A wrongly-encoded metadata file degrades to a cache miss.

        ``is_cache_valid`` is consulted *before* the cache payload is
        read; if the metadata file itself can't be decoded (e.g. it was
        written on a host whose default codec isn't UTF-8) the validity
        check must return ``False`` rather than propagate
        ``UnicodeDecodeError``. Without that guard, a corrupted metadata
        file would crash every invocation instead of falling through to
        a network refetch.
        """
        from unittest.mock import patch, MagicMock

        catalog = PresetCatalog(project_dir)
        catalog.cache_dir.mkdir(parents=True, exist_ok=True)
        catalog.cache_file.write_text("{}", encoding="utf-8")
        # Bytes that are not valid UTF-8 — ``read_text(encoding="utf-8")``
        # will raise ``UnicodeDecodeError`` (subclass of ``UnicodeError``).
        catalog.cache_metadata_file.write_bytes(b"\xff\xfe\x00bad")

        # is_cache_valid must absorb the decode failure, not crash.
        assert catalog.is_cache_valid() is False

        valid = {
            "schema_version": "1.0",
            "presets": {"foo": {"name": "Foo", "version": "1.0.0"}},
        }
        mock_response = MagicMock()
        mock_response.read.side_effect = io.BytesIO(json.dumps(valid).encode()).read
        mock_response.__enter__ = lambda s: s
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_response.geturl.return_value = "https://example.com/catalog.json"

        with patch.object(catalog, "_open_url", return_value=mock_response):
            result = catalog.fetch_catalog(force_refresh=False)

        assert result == valid

    @pytest.mark.parametrize(
        "non_mapping_metadata",
        [
            "[]",       # JSON array
            '"oops"',   # JSON string
            "42",       # JSON number
            "true",     # JSON bool
            "null",     # JSON null
        ],
    )
    def test_is_cache_valid_handles_non_mapping_metadata(
        self, project_dir, non_mapping_metadata
    ):
        """Metadata that parses to a non-mapping degrades to cache-invalid.

        The cache-validity check calls ``metadata.get("cached_at", "")``
        immediately after ``json.loads``. If the metadata file is valid
        JSON but parses to a non-mapping (``[]``, ``"oops"``, ``42``,
        ``true``, ``null``), ``.get`` raises ``AttributeError`` — which
        previously slipped past the except tuple and crashed the
        caller. The contract documented on ``is_cache_valid`` says any
        decode/shape failure should return ``False`` so ``fetch_catalog``
        falls through to a network refetch. This test pins that
        contract across every JSON non-mapping root type.
        """
        catalog = PresetCatalog(project_dir)
        catalog.cache_dir.mkdir(parents=True, exist_ok=True)
        catalog.cache_file.write_text("{}", encoding="utf-8")
        catalog.cache_metadata_file.write_text(
            non_mapping_metadata, encoding="utf-8"
        )

        # Must not raise — the contract is "any decode/shape failure → False".
        assert catalog.is_cache_valid() is False

    def test_fetch_catalog_writes_cache_as_utf8(self, project_dir, monkeypatch):
        """Cache + metadata writes pass ``encoding="utf-8"``, observably.

        The earlier version of this test claimed to assert UTF-8 at the
        byte level but actually only round-tripped a non-ASCII string
        through ``json.dumps`` and ``read_text(encoding="utf-8")``.
        Because ``json.dumps`` defaults to ``ensure_ascii=True``, "café"
        was serialized as the all-ASCII escape ``caf\\u00e9`` before it
        ever reached ``write_text`` — the bytes on disk were identical
        regardless of the encoding kwarg. The drift Copilot's review
        flagged wasn't actually being caught.

        Fix: directly observe the ``encoding`` argument passed to every
        ``write_text`` call made against the cache directory. This is
        the production code's encoding choice, which is exactly what
        the regression guard cares about.
        """
        from unittest.mock import patch, MagicMock
        from pathlib import Path as _PathCls

        catalog = PresetCatalog(project_dir)
        payload = {
            "schema_version": "1.0",
            "presets": {"foo": {"name": "Foo", "version": "1.0.0"}},
        }
        mock_response = MagicMock()
        mock_response.read.side_effect = io.BytesIO(json.dumps(payload).encode("utf-8")).read
        mock_response.__enter__ = lambda s: s
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_response.geturl.return_value = "https://example.com/catalog.json"

        # Record every ``write_text`` call's encoding kwarg so the
        # assertion observes the production writer's argument directly.
        recorded: list[dict] = []
        real_write_text = _PathCls.write_text

        def recording_write_text(self, data, *args, **kwargs):
            recorded.append(
                {"path": str(self), "encoding": kwargs.get("encoding")}
            )
            return real_write_text(self, data, *args, **kwargs)

        monkeypatch.setattr(_PathCls, "write_text", recording_write_text)

        with patch.object(catalog, "_open_url", return_value=mock_response):
            catalog.fetch_catalog(force_refresh=True)

        cache_writes = [
            r for r in recorded if str(catalog.cache_dir) in r["path"]
        ]
        assert cache_writes, "fetch_catalog made no writes to the cache dir"
        for record in cache_writes:
            assert record["encoding"] == "utf-8", (
                f"write_text on {record['path']} used encoding "
                f"{record['encoding']!r}; expected 'utf-8'"
            )

    def test_fetch_catalog_survives_unwritable_cache(self, project_dir, monkeypatch):
        """An unwritable cache dir doesn't fail a successful fetch.

        Cache writes are best-effort, mirroring the read side and the
        ``integrations/catalog.py`` precedent: if ``mkdir``/``write_text``
        raises ``OSError`` (read-only checkout, permissions), the
        already-fetched-and-validated payload must still be returned —
        not swallowed into the broad except and re-raised as a
        ``PresetError``.
        """
        from unittest.mock import patch, MagicMock
        from pathlib import Path as _PathCls

        catalog = PresetCatalog(project_dir)
        valid = {
            "schema_version": "1.0",
            "presets": {"foo": {"name": "Foo", "version": "1.0.0"}},
        }
        def make_response():
            mock_response = MagicMock()
            mock_response.read.side_effect = io.BytesIO(json.dumps(valid).encode()).read
            mock_response.__enter__ = lambda s: s
            mock_response.__exit__ = MagicMock(return_value=False)
            mock_response.geturl.return_value = catalog.DEFAULT_CATALOG_URL
            return mock_response

        # Simulate an unwritable cache dir: every write_text under the
        # cache directory raises PermissionError (an OSError subclass).
        real_write_text = _PathCls.write_text

        def failing_write_text(self, data, *args, **kwargs):
            if str(catalog.cache_dir) in str(self):
                raise PermissionError("cache dir is read-only")
            return real_write_text(self, data, *args, **kwargs)

        monkeypatch.setattr(_PathCls, "write_text", failing_write_text)

        with patch.object(catalog, "_open_url", side_effect=lambda *a, **kw: make_response()):
            # Legacy single-catalog path.
            assert catalog.fetch_catalog(force_refresh=True) == valid

            # Multi-catalog path.
            entry = PresetCatalogEntry(
                url=catalog.DEFAULT_CATALOG_URL,
                name="default",
                priority=1,
                install_allowed=True,
            )
            assert (
                catalog._fetch_single_catalog(entry, force_refresh=True) == valid
            )

    def test_get_merged_packs_skips_non_mapping_entries(self, project_dir):
        """Per-entry guard: one malformed entry shouldn't poison the merge.

        ``_fetch_single_catalog`` validates that ``presets`` is a mapping,
        but it doesn't (and shouldn't) validate every entry inside it — a
        single bad entry in an otherwise-valid catalog should be skipped,
        not crash the whole resolve path. Mirrors the per-entry skip in
        ``integrations/catalog.py``: a malformed entry returns no error,
        valid entries continue to merge normally.
        """
        from unittest.mock import patch, MagicMock

        catalog = PresetCatalog(project_dir)
        payload = {
            "schema_version": "1.0",
            "presets": {
                "good": {"name": "Good", "version": "1.0.0"},
                "bad-list": [],
                "bad-str": "oops",
            },
        }
        mock_response = MagicMock()
        mock_response.read.side_effect = io.BytesIO(json.dumps(payload).encode()).read
        mock_response.__enter__ = lambda s: s
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_response.geturl.return_value = "https://example.com/catalog.json"

        entry = PresetCatalogEntry(
            url="https://example.com/catalog.json",
            name="default",
            priority=1,
            install_allowed=True,
        )

        with patch.object(catalog, "_open_url", return_value=mock_response), \
             patch.object(catalog, "get_active_catalogs", return_value=[entry]):
            merged = catalog._get_merged_packs(force_refresh=True)

        # Only the well-formed entry survives; the two malformed entries are
        # silently dropped rather than raising or crashing.
        assert list(merged.keys()) == ["good"]

    def test_download_pack_sends_auth_header(self, project_dir, monkeypatch):
        """download_pack passes Authorization header when configured."""
        from unittest.mock import patch, MagicMock

        monkeypatch.setenv("GITHUB_TOKEN", "ghp_testtoken")
        self._inject_github_config(monkeypatch, token_env="GITHUB_TOKEN")
        catalog = PresetCatalog(project_dir)

        import io
        zip_buf = io.BytesIO()
        with zipfile.ZipFile(zip_buf, "w") as zf:
            zf.writestr("preset.yml", "id: test-pack\nname: Test\nversion: 1.0.0\n")
        zip_bytes = zip_buf.getvalue()

        release_response = MagicMock()
        release_response.read.side_effect = io.BytesIO(json.dumps(
            {
                "assets": [
                    {
                        "name": "test-pack.zip",
                        "url": "https://api.github.com/repos/org/repo/releases/assets/1",
                    }
                ]
            }
        ).encode()).read
        release_response.__enter__ = lambda s: s
        release_response.__exit__ = MagicMock(return_value=False)

        asset_response = MagicMock()
        asset_response.read.side_effect = io.BytesIO(zip_bytes).read
        asset_response.__enter__ = lambda s: s
        asset_response.__exit__ = MagicMock(return_value=False)

        captured = []
        mock_opener = MagicMock()

        def fake_open(req, timeout=None):
            captured.append(req)
            if req.full_url.endswith("/releases/tags/v1"):
                return release_response
            return asset_response

        mock_opener.open.side_effect = fake_open

        pack_info = {
            "id": "test-pack",
            "name": "Test Pack",
            "version": "1.0.0",
            "download_url": "https://github.com/org/repo/releases/download/v1/test-pack.zip",
            "_install_allowed": True,
        }

        with patch.object(catalog, "get_pack_info", return_value=pack_info), \
             patch("specify_cli.authentication.http.urllib.request.build_opener", return_value=mock_opener):
            catalog.download_pack("test-pack", target_dir=project_dir)

        assert captured[0].full_url == "https://api.github.com/repos/org/repo/releases/tags/v1"
        assert captured[0].get_header("Authorization") == "Bearer ghp_testtoken"
        assert captured[1].full_url == "https://api.github.com/repos/org/repo/releases/assets/1"
        assert captured[1].get_header("Authorization") == "Bearer ghp_testtoken"
        assert captured[1].get_header("Accept") == "application/octet-stream"

    def _pack_zip_and_response(self):
        """Build a minimal preset ZIP and a context-manager mock response."""
        from unittest.mock import MagicMock
        import io

        zip_buf = io.BytesIO()
        with zipfile.ZipFile(zip_buf, "w") as zf:
            zf.writestr("preset.yml", "id: test-pack\nname: Test\nversion: 1.0.0\n")
        zip_bytes = zip_buf.getvalue()

        resp = MagicMock()
        resp.read.side_effect = io.BytesIO(zip_bytes).read
        # Configure the context-manager protocol explicitly so `with resp`
        # yields `resp` itself, independent of how the protocol is invoked.
        resp.__enter__.return_value = resp
        resp.__exit__.return_value = False
        return zip_bytes, resp

    def test_fetch_single_catalog_rejects_oversized_body_without_cache(
        self, project_dir, monkeypatch
    ):
        """Catalog bounds are enforced at the preset call site."""
        import specify_cli.presets as preset_module
        from unittest.mock import patch

        catalog = PresetCatalog(project_dir)
        entry = PresetCatalogEntry(
            url="https://example.com/catalog.json",
            name="default",
            priority=1,
            install_allowed=True,
        )
        body = b'{"schema_version":"1.0","presets":{}}'
        response = MagicMock()
        response.read.side_effect = io.BytesIO(body).read
        response.__enter__.return_value = response
        response.__exit__.return_value = False
        response.geturl.return_value = entry.url
        monkeypatch.setattr(
            preset_module,
            "MAX_JSON_CATALOG_BYTES",
            len(body) - 1,
        )

        with patch.object(catalog, "_open_url", return_value=response):
            with pytest.raises(PresetError, match="exceeds maximum size"):
                catalog._fetch_single_catalog(entry, force_refresh=True)

        assert not catalog.cache_dir.exists() or not any(catalog.cache_dir.iterdir())

    def test_download_pack_rejects_oversized_body_without_output(
        self, project_dir, monkeypatch
    ):
        """Package bounds fail before checksum verification or disk writes."""
        import specify_cli.presets as preset_module
        from unittest.mock import patch
        from specify_cli._download_security import (
            read_response_limited as real_read_response_limited,
        )

        catalog = PresetCatalog(project_dir)
        pack_info = {
            "id": "test-pack",
            "name": "Test Pack",
            "version": "1.0.0",
            "download_url": "https://example.com/test-pack.zip",
            "_install_allowed": True,
        }
        response = MagicMock()
        response.read.side_effect = io.BytesIO(b"12345").read
        response.__enter__.return_value = response
        response.__exit__.return_value = False

        def read_with_tiny_limit(stream, **kwargs):
            kwargs.pop("max_bytes", None)
            return real_read_response_limited(stream, max_bytes=4, **kwargs)

        monkeypatch.setattr(
            preset_module,
            "read_response_limited",
            read_with_tiny_limit,
        )
        with patch.object(preset_module, "verify_archive_sha256") as verify, \
             patch.object(catalog, "get_pack_info", return_value=pack_info), \
             patch.object(catalog, "_open_url", return_value=response):
            with pytest.raises(PresetError, match="exceeds maximum size"):
                catalog.download_pack("test-pack", target_dir=project_dir)

        verify.assert_not_called()
        assert not (project_dir / "test-pack-1.0.0.zip").exists()

    def test_download_pack_rejects_unsafe_output_filename(self, project_dir):
        """Catalog-controlled IDs cannot escape the requested target directory."""
        from unittest.mock import patch

        catalog = PresetCatalog(project_dir)
        outside_stem = project_dir.parent / "outside-preset"
        pack_id = str(outside_stem)
        pack_info = {
            "id": pack_id,
            "name": "Test Pack",
            "version": "1.0.0",
            "download_url": "https://example.com/test-pack.zip",
            "_install_allowed": True,
        }

        with patch.object(catalog, "get_pack_info", return_value=pack_info), \
             patch.object(catalog, "_open_url") as open_url:
            with pytest.raises(PresetError, match="filename"):
                catalog.download_pack(pack_id, target_dir=project_dir)

        open_url.assert_not_called()
        assert not Path(f"{outside_stem}-1.0.0.zip").exists()

    def test_download_pack_accepts_matching_sha256(self, project_dir):
        """A catalog ``sha256`` that matches the preset archive is accepted."""
        import hashlib
        from unittest.mock import patch

        catalog = PresetCatalog(project_dir)
        zip_bytes, resp = self._pack_zip_and_response()
        pack_info = {
            "id": "test-pack",
            "name": "Test Pack",
            "version": "1.0.0",
            "download_url": "https://example.com/test-pack.zip",
            "sha256": hashlib.sha256(zip_bytes).hexdigest(),
            "_install_allowed": True,
        }

        with patch.object(catalog, "get_pack_info", return_value=pack_info), \
             patch.object(catalog, "_open_url", return_value=resp):
            zip_path = catalog.download_pack("test-pack", target_dir=project_dir)

        assert zip_path.read_bytes() == zip_bytes

    def test_download_pack_rejects_sha256_mismatch(self, project_dir):
        """A catalog ``sha256`` that does not match the archive aborts install."""
        from unittest.mock import patch

        catalog = PresetCatalog(project_dir)
        _zip_bytes, resp = self._pack_zip_and_response()
        pack_info = {
            "id": "test-pack",
            "name": "Test Pack",
            "version": "1.0.0",
            "download_url": "https://example.com/test-pack.zip",
            "sha256": "0" * 64,  # deliberately wrong
            "_install_allowed": True,
        }

        with patch.object(catalog, "get_pack_info", return_value=pack_info), \
             patch.object(catalog, "_open_url", return_value=resp):
            with pytest.raises(PresetError, match="[Ii]ntegrity"):
                catalog.download_pack("test-pack", target_dir=project_dir)

    def test_download_pack_malformed_url_raises_preset_error(self, project_dir):
        """A catalog ``download_url`` with a malformed authority (e.g. an
        unterminated IPv6 bracket) surfaces a clean ``PresetError`` rather than
        leaking a raw ``ValueError`` from ``urlparse``/``.hostname`` past the
        command handler (which only catches ``PresetError``). Mirrors the
        extensions coverage.
        """
        from unittest.mock import patch

        catalog = PresetCatalog(project_dir)
        for bad_url in (
            "https://[::1",
            "https://[not-an-ip]/x",
            "https://example.com:65536/x",
            "https:///x",
            123,
        ):
            pack_info = {
                "id": "test-pack",
                "name": "Test Pack",
                "version": "1.0.0",
                "download_url": bad_url,
                "_install_allowed": True,
            }
            with patch.object(catalog, "get_pack_info", return_value=pack_info), \
                 patch.object(catalog, "_open_url") as open_url:
                with pytest.raises(PresetError, match="malformed"):
                    catalog.download_pack("test-pack", target_dir=project_dir)
                open_url.assert_not_called()

    def test_download_pack_without_sha256_skips_verification(self, project_dir):
        """A catalog entry with no ``sha256`` keeps working: verification is
        opt-in, so the backwards-compatible path (``pack_info.get("sha256")``
        is ``None``) must download without aborting — mirrors the extensions
        coverage so the helper never silently becomes mandatory for presets.
        """
        from unittest.mock import patch

        catalog = PresetCatalog(project_dir)
        zip_bytes, resp = self._pack_zip_and_response()
        pack_info = {
            "id": "test-pack",
            "name": "Test Pack",
            "version": "1.0.0",
            "download_url": "https://example.com/test-pack.zip",
            "_install_allowed": True,
        }

        with patch.object(catalog, "get_pack_info", return_value=pack_info), \
             patch.object(catalog, "_open_url", return_value=resp):
            zip_path = catalog.download_pack("test-pack", target_dir=project_dir)

        assert zip_path.read_bytes() == zip_bytes

    def test_download_pack_accepts_direct_github_rest_asset_url(self, project_dir, monkeypatch):
        """download_pack can use a GitHub REST release asset URL directly."""
        from unittest.mock import patch, MagicMock

        monkeypatch.setenv("GITHUB_TOKEN", "ghp_testtoken")
        self._inject_github_config(monkeypatch, token_env="GITHUB_TOKEN")
        catalog = PresetCatalog(project_dir)

        import io
        zip_buf = io.BytesIO()
        with zipfile.ZipFile(zip_buf, "w") as zf:
            zf.writestr("preset.yml", "id: test-pack\nname: Test\nversion: 1.0.0\n")
        zip_bytes = zip_buf.getvalue()

        asset_response = MagicMock()
        asset_response.read.side_effect = io.BytesIO(zip_bytes).read
        asset_response.__enter__ = lambda s: s
        asset_response.__exit__ = MagicMock(return_value=False)

        captured = []
        mock_opener = MagicMock()

        def fake_open(req, timeout=None):
            captured.append(req)
            return asset_response

        mock_opener.open.side_effect = fake_open

        pack_info = {
            "id": "test-pack",
            "name": "Test Pack",
            "version": "1.0.0",
            "download_url": "https://api.github.com/repos/org/repo/releases/assets/1",
            "_install_allowed": True,
        }

        with patch.object(catalog, "get_pack_info", return_value=pack_info), \
             patch("specify_cli.authentication.http.urllib.request.build_opener", return_value=mock_opener):
            catalog.download_pack("test-pack", target_dir=project_dir)

        assert len(captured) == 1
        assert captured[0].full_url == "https://api.github.com/repos/org/repo/releases/assets/1"
        assert captured[0].get_header("Authorization") == "Bearer ghp_testtoken"
        assert captured[0].get_header("Accept") == "application/octet-stream"

    @pytest.mark.parametrize("suffix", [".tar.gz", ".tgz"])
    def test_download_pack_preserves_tar_archive_format(
        self, project_dir, suffix
    ):
        from unittest.mock import patch, MagicMock

        archive_buffer = io.BytesIO()
        with tarfile.open(fileobj=archive_buffer, mode="w:gz") as archive:
            content = b"preset:\n  id: test-pack\n"
            member = tarfile.TarInfo("preset.yml")
            member.size = len(content)
            archive.addfile(member, io.BytesIO(content))
        archive_bytes = archive_buffer.getvalue()
        response = MagicMock()
        response.read.side_effect = io.BytesIO(archive_bytes).read
        response.__enter__.return_value = response
        response.__exit__.return_value = False
        catalog = PresetCatalog(project_dir)
        pack_info = {
            "id": "test-pack",
            "name": "Test Pack",
            "version": "1.0.0",
            "download_url": f"https://example.com/test-pack{suffix}",
            "_install_allowed": True,
        }

        with patch.object(catalog, "get_pack_info", return_value=pack_info), \
             patch.object(catalog, "_open_url", return_value=response):
            archive_path = catalog.download_pack("test-pack", target_dir=project_dir)

        assert archive_path.name == "test-pack-1.0.0.tar.gz"
        assert archive_path.read_bytes() == archive_bytes


class TestPresetCatalogEntry:
    """Test PresetCatalogEntry dataclass."""

    def test_create_entry(self):
        """Test creating a catalog entry."""
        entry = PresetCatalogEntry(
            url="https://example.com/catalog.json",
            name="test",
            priority=1,
            install_allowed=True,
            description="Test catalog",
        )
        assert entry.url == "https://example.com/catalog.json"
        assert entry.name == "test"
        assert entry.priority == 1
        assert entry.install_allowed is True
        assert entry.description == "Test catalog"

    def test_default_description(self):
        """Test default empty description."""
        entry = PresetCatalogEntry(
            url="https://example.com/catalog.json",
            name="test",
            priority=1,
            install_allowed=False,
        )
        assert entry.description == ""


class TestPresetCatalogMultiCatalog:
    """Test multi-catalog support in PresetCatalog."""

    def test_default_active_catalogs(self, project_dir):
        """Test that default catalogs are returned when no config exists."""
        catalog = PresetCatalog(project_dir)
        active = catalog.get_active_catalogs()
        assert len(active) == 2
        assert active[0].name == "default"
        assert active[0].priority == 1
        assert active[0].install_allowed is True
        assert active[1].name == "community"
        assert active[1].priority == 2
        assert active[1].install_allowed is False






    def test_env_var_overrides_catalogs(self, project_dir, monkeypatch):
        """Test that SPECKIT_PRESET_CATALOG_URL env var overrides defaults."""
        monkeypatch.setenv(
            "SPECKIT_PRESET_CATALOG_URL",
            "https://custom.example.com/catalog.json",
        )
        catalog = PresetCatalog(project_dir)
        active = catalog.get_active_catalogs()
        assert len(active) == 1
        assert active[0].name == "custom"
        assert active[0].url == "https://custom.example.com/catalog.json"
        assert active[0].install_allowed is True

    def test_project_config_overrides_defaults(self, project_dir):
        """Test that project-level config overrides built-in defaults."""
        config_path = project_dir / ".specify" / "preset-catalogs.yml"
        config_path.write_text(yaml.dump({
            "catalogs": [
                {
                    "name": "my-catalog",
                    "url": "https://my.example.com/catalog.json",
                    "priority": 1,
                    "install_allowed": True,
                }
            ]
        }))

        catalog = PresetCatalog(project_dir)
        active = catalog.get_active_catalogs()
        assert len(active) == 1
        assert active[0].name == "my-catalog"
        assert active[0].url == "https://my.example.com/catalog.json"

    def test_load_catalog_config_nonexistent(self, project_dir):
        """Test loading config from nonexistent file returns None."""
        catalog = PresetCatalog(project_dir)
        result = catalog._load_catalog_config(
            project_dir / ".specify" / "nonexistent.yml"
        )
        assert result is None

    def test_load_catalog_config_empty(self, project_dir):
        """Test loading empty config returns None."""
        config_path = project_dir / ".specify" / "preset-catalogs.yml"
        config_path.write_text("")

        catalog = PresetCatalog(project_dir)
        result = catalog._load_catalog_config(config_path)
        assert result is None

    def test_load_catalog_config_defaults_blank_names(self, project_dir):
        """Blank and null names normalize by valid catalog order."""
        config_path = project_dir / ".specify" / "preset-catalogs.yml"
        config_path.write_text(
            yaml.dump(
                {
                    "catalogs": [
                        {"name": "skipped", "url": "   "},
                        {
                            "name": None,
                            "url": "https://one.example.com/catalog.json",
                        },
                        {
                            "name": "   ",
                            "url": "https://two.example.com/catalog.json",
                        },
                        {
                            "name": "  padded-name  ",
                            "url": "https://three.example.com/catalog.json",
                        },
                    ]
                }
            ),
            encoding="utf-8",
        )

        entries = PresetCatalog(project_dir)._load_catalog_config(config_path)

        assert [entry.name for entry in entries] == [
            "catalog-1",
            "catalog-2",
            "padded-name",
        ]

    @pytest.mark.parametrize("bad", [[], False, 0, ""])
    def test_load_catalog_config_rejects_falsy_non_mapping_root(
        self, project_dir, bad
    ):
        config_path = project_dir / ".specify" / "preset-catalogs.yml"
        config_path.write_text(yaml.safe_dump(bad), encoding="utf-8")

        catalog = PresetCatalog(project_dir)
        with pytest.raises(PresetValidationError, match="expected a mapping"):
            catalog._load_catalog_config(config_path)

    def test_load_catalog_config_invalid_yaml(self, project_dir):
        """Test loading invalid YAML raises error."""
        config_path = project_dir / ".specify" / "preset-catalogs.yml"
        config_path.write_text(": invalid: {{{")

        catalog = PresetCatalog(project_dir)
        with pytest.raises(PresetValidationError, match="Failed to read"):
            catalog._load_catalog_config(config_path)

    def test_load_catalog_config_not_a_list(self, project_dir):
        """Test that non-list catalogs key raises error."""
        config_path = project_dir / ".specify" / "preset-catalogs.yml"
        config_path.write_text(yaml.dump({"catalogs": "not-a-list"}))

        catalog = PresetCatalog(project_dir)
        with pytest.raises(PresetValidationError, match="must be a list"):
            catalog._load_catalog_config(config_path)

    @pytest.mark.parametrize("body", ["catalogs: {}\n", "catalogs: ''\n", "catalogs: 0\n", "catalogs: false\n"])
    def test_load_catalog_config_rejects_falsy_non_list_catalogs(self, project_dir, body):
        """A FALSY non-list ``catalogs:`` value must raise, like a truthy one
        (``catalogs: "not-a-list"``) already does. The shape check sat behind
        the emptiness check, so these were silently swallowed as "no catalogs"."""
        config_path = project_dir / ".specify" / "preset-catalogs.yml"
        config_path.write_text(body, encoding="utf-8")

        catalog = PresetCatalog(project_dir)
        with pytest.raises(PresetValidationError, match="must be a list"):
            catalog._load_catalog_config(config_path)

    def test_load_catalog_config_invalid_entry(self, project_dir):
        """Test that non-dict entry raises error."""
        config_path = project_dir / ".specify" / "preset-catalogs.yml"
        config_path.write_text(yaml.dump({"catalogs": ["not-a-dict"]}))

        catalog = PresetCatalog(project_dir)
        with pytest.raises(PresetValidationError, match="expected a mapping"):
            catalog._load_catalog_config(config_path)

    def test_load_catalog_config_http_url_rejected(self, project_dir):
        """Test that HTTP URLs are rejected."""
        config_path = project_dir / ".specify" / "preset-catalogs.yml"
        config_path.write_text(yaml.dump({
            "catalogs": [
                {
                    "name": "bad",
                    "url": "http://insecure.example.com/catalog.json",
                    "priority": 1,
                }
            ]
        }))

        catalog = PresetCatalog(project_dir)
        with pytest.raises(PresetValidationError, match="must use HTTPS"):
            catalog._load_catalog_config(config_path)

    def test_load_catalog_config_priority_sorting(self, project_dir):
        """Test that catalogs are sorted by priority."""
        config_path = project_dir / ".specify" / "preset-catalogs.yml"
        config_path.write_text(yaml.dump({
            "catalogs": [
                {
                    "name": "low-priority",
                    "url": "https://low.example.com/catalog.json",
                    "priority": 10,
                    "install_allowed": False,
                },
                {
                    "name": "high-priority",
                    "url": "https://high.example.com/catalog.json",
                    "priority": 1,
                    "install_allowed": True,
                },
            ]
        }))

        catalog = PresetCatalog(project_dir)
        entries = catalog._load_catalog_config(config_path)
        assert entries is not None
        assert len(entries) == 2
        assert entries[0].name == "high-priority"
        assert entries[1].name == "low-priority"

    def test_load_catalog_config_invalid_priority(self, project_dir):
        """Test that invalid priority raises error."""
        config_path = project_dir / ".specify" / "preset-catalogs.yml"
        config_path.write_text(yaml.dump({
            "catalogs": [
                {
                    "name": "bad",
                    "url": "https://example.com/catalog.json",
                    "priority": "not-a-number",
                }
            ]
        }))

        catalog = PresetCatalog(project_dir)
        with pytest.raises(PresetValidationError, match="Invalid priority"):
            catalog._load_catalog_config(config_path)

    def test_load_catalog_config_rejects_boolean_priority(self, project_dir):
        """A YAML ``priority: true`` is a typo, not a request for priority 1.

        ``bool`` is a subclass of ``int`` in Python, so ``int(True)`` silently
        returns ``1``. Without an explicit guard a malformed config like
        ``priority: yes`` would be accepted as a valid priority of 1 and
        silently change catalog ordering. The sibling integration-catalog
        reader rejects this case (see ``catalogs.py``); the preset catalog
        reader must stay consistent.
        """
        config_path = project_dir / ".specify" / "preset-catalogs.yml"
        config_path.write_text(yaml.dump({
            "catalogs": [
                {
                    "name": "bool-priority",
                    "url": "https://example.com/catalog.json",
                    "priority": True,
                }
            ]
        }))

        catalog = PresetCatalog(project_dir)
        with pytest.raises(PresetValidationError, match="Invalid priority|expected integer"):
            catalog._load_catalog_config(config_path)

    def test_load_catalog_config_rejects_infinite_priority(self, project_dir):
        """A ``priority: .inf`` yields a clean validation error, not an uncaught
        OverflowError from int(float('inf'))."""
        config_path = project_dir / ".specify" / "preset-catalogs.yml"
        config_path.write_text(yaml.dump({
            "catalogs": [
                {
                    "name": "inf-priority",
                    "url": "https://example.com/catalog.json",
                    "priority": float("inf"),
                }
            ]
        }))

        catalog = PresetCatalog(project_dir)
        with pytest.raises(PresetValidationError, match="Invalid priority|expected integer"):
            catalog._load_catalog_config(config_path)

    def test_load_catalog_config_install_allowed_string(self, project_dir):
        """Test that install_allowed accepts string values."""
        config_path = project_dir / ".specify" / "preset-catalogs.yml"
        config_path.write_text(yaml.dump({
            "catalogs": [
                {
                    "name": "test",
                    "url": "https://example.com/catalog.json",
                    "priority": 1,
                    "install_allowed": "true",
                }
            ]
        }))

        catalog = PresetCatalog(project_dir)
        entries = catalog._load_catalog_config(config_path)
        assert entries is not None
        assert entries[0].install_allowed is True

    def test_get_catalog_url_uses_highest_priority(self, project_dir):
        """Test that get_catalog_url returns URL of highest priority catalog."""
        config_path = project_dir / ".specify" / "preset-catalogs.yml"
        config_path.write_text(yaml.dump({
            "catalogs": [
                {
                    "name": "secondary",
                    "url": "https://secondary.example.com/catalog.json",
                    "priority": 5,
                },
                {
                    "name": "primary",
                    "url": "https://primary.example.com/catalog.json",
                    "priority": 1,
                },
            ]
        }))

        catalog = PresetCatalog(project_dir)
        assert catalog.get_catalog_url() == "https://primary.example.com/catalog.json"

    def test_cache_paths_default_url(self, project_dir):
        """Test cache paths for default catalog URL use legacy locations."""
        catalog = PresetCatalog(project_dir)
        cache_file, metadata_file = catalog._get_cache_paths(
            PresetCatalog.DEFAULT_CATALOG_URL
        )
        assert cache_file == catalog.cache_file
        assert metadata_file == catalog.cache_metadata_file

    def test_cache_paths_custom_url(self, project_dir):
        """Test cache paths for custom URLs use hash-based files."""
        catalog = PresetCatalog(project_dir)
        cache_file, metadata_file = catalog._get_cache_paths(
            "https://custom.example.com/catalog.json"
        )
        assert cache_file != catalog.cache_file
        assert "catalog-" in cache_file.name
        assert cache_file.name.endswith(".json")

    def test_url_cache_valid(self, project_dir):
        """Test URL-specific cache validation."""
        catalog = PresetCatalog(project_dir)
        url = "https://custom.example.com/catalog.json"
        cache_file, metadata_file = catalog._get_cache_paths(url)

        catalog.cache_dir.mkdir(parents=True, exist_ok=True)
        cache_file.write_text(json.dumps({"schema_version": "1.0", "presets": {}}))
        metadata_file.write_text(json.dumps({
            "cached_at": datetime.now(timezone.utc).isoformat(),
        }))

        assert catalog._is_url_cache_valid(url) is True

    def test_url_cache_expired(self, project_dir):
        """Test URL-specific cache expiration."""
        catalog = PresetCatalog(project_dir)
        url = "https://custom.example.com/catalog.json"
        cache_file, metadata_file = catalog._get_cache_paths(url)

        catalog.cache_dir.mkdir(parents=True, exist_ok=True)
        cache_file.write_text(json.dumps({"schema_version": "1.0", "presets": {}}))
        metadata_file.write_text(json.dumps({
            "cached_at": "2020-01-01T00:00:00+00:00",
        }))

        assert catalog._is_url_cache_valid(url) is False


class TestBundledPresetLocator:
    """Catalog downloads reject bundled presets."""

    def test_bundled_preset_download_raises_error(self, project_dir):
        """download_pack raises PresetError for bundled presets without download_url."""
        catalog = PresetCatalog(project_dir)

        catalog_data = {
            "test-bundled": {
                "name": "Test Bundled",
                "version": "1.0.0",
                "bundled": True,
            }
        }
        from unittest.mock import patch
        with patch.object(catalog, "_get_merged_packs", return_value=catalog_data):
            with pytest.raises(PresetError, match="bundled with spec-kit"):
                catalog.download_pack("test-bundled")


def test_preset_wrapper_resolves_ghes_asset_when_host_configured(tmp_path, monkeypatch):
    """End-to-end wiring for presets: auth.json github host → GHES asset resolution."""
    from specify_cli.authentication import http as _auth_http
    from specify_cli.authentication.config import AuthConfigEntry
    from specify_cli.presets import PresetCatalog

    monkeypatch.setattr(_auth_http, "_config_override", [
        AuthConfigEntry(hosts=("ghes.example",), provider="github",
                        auth="bearer", token="t"),
    ])
    catalog = PresetCatalog(tmp_path)

    captured = []

    @contextmanager
    def fake_open(url, timeout=None, extra_headers=None):
        captured.append(url)
        resp = MagicMock()
        resp.read.side_effect = io.BytesIO(json.dumps({
            "assets": [{"name": "pack.zip",
                        "url": "https://ghes.example/api/v3/repos/o/r/releases/assets/9"}]
        }).encode()).read
        yield resp

    monkeypatch.setattr(catalog, "_open_url", fake_open)

    resolved = catalog._resolve_github_release_asset_api_url(
        "https://ghes.example/o/r/releases/download/v2/pack.zip"
    )
    assert resolved == "https://ghes.example/api/v3/repos/o/r/releases/assets/9"
    assert captured == ["https://ghes.example/api/v3/repos/o/r/releases/tags/v2"]
