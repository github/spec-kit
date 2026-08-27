"""HTTP test helpers shared by CLI tests."""

import io
import json
import urllib.request
from unittest.mock import MagicMock

import pytest


def mock_urlopen_response(payload: dict) -> MagicMock:
    """Build a urlopen context-manager mock whose read returns JSON."""
    body = json.dumps(payload).encode("utf-8")
    resp = MagicMock()
    resp.read.side_effect = io.BytesIO(body).read
    cm = MagicMock()
    cm.__enter__.return_value = resp
    cm.__exit__.return_value = False
    return cm


@pytest.fixture(autouse=True)
def route_opener_open_through_urlopen(monkeypatch):
    """Route build_opener().open through urllib.request.urlopen.

    ``open_url(...)`` fetches via ``build_opener(...).open()``, which bypasses
    ``urllib.request.urlopen`` — and with it the urlopen patches these test
    modules are built on.
    Delegating ``open()`` to urlopen at call time keeps those patches
    effective; the redirect handler's own behavior is covered by
    ``TestRedirectStripping`` in test_authentication.py.

    Import this fixture into a test module to activate it there.
    """

    class _UrlopenDelegatingOpener:
        def open(self, req, data=None, timeout=None):
            if data is None:
                return urllib.request.urlopen(req, timeout=timeout)
            return urllib.request.urlopen(req, data=data, timeout=timeout)

    monkeypatch.setattr(
        urllib.request,
        "build_opener",
        lambda *handlers: _UrlopenDelegatingOpener(),
    )
