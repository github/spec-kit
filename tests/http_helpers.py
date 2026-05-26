"""HTTP test helpers shared by version-related CLI tests."""

import json
from unittest.mock import MagicMock


def mock_urlopen_response(payload: dict) -> MagicMock:
    """Build a urlopen context-manager mock whose read returns JSON."""
    body = json.dumps(payload).encode("utf-8")
    resp = MagicMock()
    resp.read.return_value = body
    cm = MagicMock()
    cm.__enter__.return_value = resp
    cm.__exit__.return_value = False
    return cm
