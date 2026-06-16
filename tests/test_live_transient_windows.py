"""Tests for Rich Live transient=False on Windows (GitHub issue #2927).

PowerShell 5.1's legacy console host does not support VT escape sequences
reliably.  Rich's ``Live(transient=True)`` attempts cursor restoration on
exit, which hangs indefinitely on that console.  The fix disables transient
mode when ``sys.platform == "win32"``.

These tests patch ``sys.platform`` and intercept the ``Live`` constructor
to verify the correct ``transient`` value reaches Rich.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch


# ---------------------------------------------------------------------------
# _console.py — Live in the select_with_arrows helper
# ---------------------------------------------------------------------------


def _invoke_select_with_arrows(platform: str) -> bool:
    """Patch sys.platform and Live, invoke select_with_arrows, return transient kwarg."""
    captured = {}

    mock_live_instance = MagicMock()
    mock_live_instance.__enter__ = MagicMock(return_value=mock_live_instance)
    mock_live_instance.__exit__ = MagicMock(return_value=False)

    def fake_live(*args, **kwargs):
        captured.update(kwargs)
        return mock_live_instance

    # Patch readchar so the loop immediately returns "enter"
    import readchar

    with (
        patch("sys.platform", platform),
        patch("specify_cli._console.Live", side_effect=fake_live),
        patch("specify_cli._console.readchar.readkey", return_value=readchar.key.ENTER),
    ):
        from specify_cli._console import select_with_arrows

        select_with_arrows({"a": "Option A", "b": "Option B"}, "Pick one", "a")

    return captured["transient"]


class TestSelectWithArrowsLiveTransient:
    """Verify that select_with_arrows passes transient=False on Windows."""

    def test_transient_false_on_windows(self):
        assert _invoke_select_with_arrows("win32") is False

    def test_transient_true_on_linux(self):
        assert _invoke_select_with_arrows("linux") is True

    def test_transient_true_on_macos(self):
        assert _invoke_select_with_arrows("darwin") is True


# ---------------------------------------------------------------------------
# init.py — verify source contains the platform guard (regression check)
# ---------------------------------------------------------------------------


class TestSourceContainsPlatformGuard:
    """Ensure the platform guard feeds into the Live() transient kwarg."""

    # Single DOTALL regex: _transient assigned from win32 check, then used in Live()
    _GUARD_RE = r"_transient\s*=\s*sys\.platform\s*!=\s*['\"]win32['\"].*Live\(.*transient\s*=\s*_transient"

    def test_init_has_win32_guard(self):
        """init.py must assign _transient from platform check and pass it to Live."""
        import re

        init_src = Path(__file__).resolve().parent.parent / "src" / "specify_cli" / "commands" / "init.py"
        content = init_src.read_text(encoding="utf-8")
        assert re.search(self._GUARD_RE, content, re.DOTALL)

    def test_console_has_win32_guard(self):
        """_console.py must assign _transient from platform check and pass it to Live."""
        import re

        console_src = Path(__file__).resolve().parent.parent / "src" / "specify_cli" / "_console.py"
        content = console_src.read_text(encoding="utf-8")
        assert re.search(self._GUARD_RE, content, re.DOTALL)
        assert re.search(r"transient\s*=\s*_transient", content)
        assert "transient=_transient" in content
