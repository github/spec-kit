"""Unit tests for the shared archive-integrity helper.

These exercise ``verify_archive_sha256`` directly (independently of the
extension/preset download paths that call it) so the digest-matching,
mismatch, normalisation and "no digest declared" behaviours are pinned in
one place.
"""

from __future__ import annotations

import hashlib
import logging

import pytest

from specify_cli.shared_infra import verify_archive_sha256


class _BoomError(Exception):
    """Sentinel error type used to assert the helper raises ``error_cls``."""


def test_matching_digest_passes():
    """A digest that matches the data returns without raising."""
    data = b"hello-archive"
    digest = hashlib.sha256(data).hexdigest()
    verify_archive_sha256(data, digest, "thing", _BoomError)


def test_mismatch_raises_error_cls():
    """A non-matching digest raises the caller-supplied error type."""
    with pytest.raises(_BoomError, match="[Ii]ntegrity"):
        verify_archive_sha256(b"data", "0" * 64, "thing", _BoomError)


def test_sha256_prefix_is_accepted():
    """A ``sha256:`` prefix on the expected digest is tolerated."""
    data = b"prefixed"
    digest = hashlib.sha256(data).hexdigest()
    verify_archive_sha256(data, f"sha256:{digest}", "thing", _BoomError)


def test_comparison_is_case_insensitive():
    """An upper-cased expected digest still matches the lower-case actual."""
    data = b"casing"
    digest = hashlib.sha256(data).hexdigest().upper()
    verify_archive_sha256(data, digest, "thing", _BoomError)


def test_absent_digest_skips_and_logs_debug(caplog):
    """When no digest is declared the helper returns and logs at DEBUG.

    Installs stay backwards compatible (no error, no user-facing warning),
    but the unverified download leaves an audit trail for operators who opt
    into debug logging.
    """
    with caplog.at_level(logging.DEBUG, logger="specify_cli.shared_infra"):
        verify_archive_sha256(b"data", None, "thing", _BoomError)
    assert any(
        "not verified" in r.getMessage() and "thing" in r.getMessage()
        for r in caplog.records
    )
