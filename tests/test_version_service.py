from unittest.mock import patch, MagicMock
import json
from specify_cli._version import VersionService

def test_is_newer_true():
    svc = VersionService()
    assert svc.is_newer("0.9.0", "0.8.0") is True

def test_is_newer_false_when_equal():
    svc = VersionService()
    assert svc.is_newer("0.8.0", "0.8.0") is False

def test_is_newer_false_when_older():
    svc = VersionService()
    assert svc.is_newer("0.7.0", "0.8.0") is False

def test_is_newer_false_with_unknown():
    svc = VersionService()
    assert svc.is_newer("unknown", "0.8.0") is False
    assert svc.is_newer("0.9.0", "unknown") is False

def test_normalize_tag_strips_v():
    svc = VersionService()
    assert svc._normalize_tag("v0.9.0") == "0.9.0"
    assert svc._normalize_tag("0.9.0") == "0.9.0"
    assert svc._normalize_tag("vv0.9.0") == "v0.9.0"

def test_get_installed_version_returns_string():
    svc = VersionService()
    result = svc.get_installed_version()
    assert isinstance(result, str)

def test_fetch_latest_tag_returns_tuple_on_network_error():
    svc = VersionService()
    import urllib.error
    with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("timeout")):
        tag, failure = svc.fetch_latest_tag()
    assert tag is None
    assert failure == "offline or timeout"

def test_fetch_latest_tag_success():
    svc = VersionService()
    mock_response = MagicMock()
    mock_response.read.return_value = json.dumps({"tag_name": "v0.9.0"}).encode()
    mock_response.__enter__ = lambda s: s
    mock_response.__exit__ = MagicMock(return_value=False)
    with patch("urllib.request.urlopen", return_value=mock_response):
        tag, failure = svc.fetch_latest_tag()
    assert tag == "v0.9.0"
    assert failure is None

def test_backward_compat_normalize_tag():
    from specify_cli import _normalize_tag
    assert _normalize_tag("v1.0.0") == "1.0.0"

def test_backward_compat_is_newer():
    from specify_cli import _is_newer
    assert _is_newer("1.0.0", "0.9.0") is True
