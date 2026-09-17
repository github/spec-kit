"""Crash-injection tests for atomic write helpers.

Verifies that mkstemp + os.replace write patterns across the codebase
leave the original file intact when a mid-write failure occurs, and that
temp files are cleaned up.
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest


# -- _safe_write_json (events.py) -------------------------------------------

class TestSafeWriteJsonAtomic:
    """Atomic writes for _safe_write_json in events.py."""

    def test_successful_write(self, tmp_path: Path) -> None:
        from specify_cli.events import _safe_write_json

        dst = tmp_path / "config.json"
        data = {"key": "value", "nested": {"a": 1}}

        _safe_write_json(dst, data)

        assert dst.exists()
        loaded = json.loads(dst.read_text(encoding="utf-8"))
        assert loaded == data

    def test_original_intact_on_write_failure(self, tmp_path: Path) -> None:
        """Mid-write failure must leave the original file untouched."""
        from specify_cli.events import _safe_write_json

        dst = tmp_path / "config.json"
        original = {"original": True}
        dst.write_text(json.dumps(original) + "\n", encoding="utf-8")

        with patch("specify_cli.events.os.replace", side_effect=OSError("disk full")):
            with pytest.raises(OSError, match="disk full"):
                _safe_write_json(dst, {"corrupted": True})

        loaded = json.loads(dst.read_text(encoding="utf-8"))
        assert loaded == original

    def test_temp_file_cleaned_up_after_failure(self, tmp_path: Path) -> None:
        """Temp files must not be left behind after a failure."""
        from specify_cli.events import _safe_write_json

        dst = tmp_path / "config.json"
        before = set(tmp_path.iterdir())

        with patch("specify_cli.events.os.replace", side_effect=OSError("fail")):
            with pytest.raises(OSError):
                _safe_write_json(dst, {"data": 1})

        after = set(tmp_path.iterdir())
        new_files = after - before
        # Only the original file should exist (if created), no temp files
        for f in new_files:
            assert not f.name.startswith(".config.json.")

    def test_preserves_file_permissions(self, tmp_path: Path) -> None:
        """Atomic write should preserve original file permissions."""
        from specify_cli.events import _safe_write_json

        dst = tmp_path / "config.json"
        dst.write_text("{}\n", encoding="utf-8")
        original_mode = dst.stat().st_mode & 0o7777

        _safe_write_json(dst, {"updated": True})

        new_mode = dst.stat().st_mode & 0o7777
        assert new_mode == original_mode


# -- _merge_toml_fragment (events.py) ---------------------------------------

class TestMergeTomlFragmentAtomic:
    """Atomic writes for _merge_toml_fragment in events.py."""

    def test_successful_write(self, tmp_path: Path) -> None:
        from specify_cli.events import _merge_toml_fragment

        dst = tmp_path / "hooks.toml"
        fragment = "[[hooks.session_start]]\ncommand = 'echo hello'\nspeckit_marker = true"

        result = _merge_toml_fragment(dst, fragment)

        assert result is True
        assert dst.exists()
        content = dst.read_text(encoding="utf-8")
        assert "echo hello" in content

    def test_original_intact_on_write_failure(self, tmp_path: Path) -> None:
        from specify_cli.events import _merge_toml_fragment

        dst = tmp_path / "hooks.toml"
        original = "[[hooks.custom]]\ncommand = 'original'\n"
        dst.write_text(original, encoding="utf-8")

        with patch("specify_cli.events.os.replace", side_effect=OSError("fail")):
            with pytest.raises(OSError, match="fail"):
                _merge_toml_fragment(dst, "fragment")

        assert dst.read_text(encoding="utf-8") == original


# -- _remove_toml_entries (events.py) ----------------------------------------

class TestRemoveTomlEntriesAtomic:
    """Atomic writes for _remove_toml_entries in events.py."""

    def test_successful_removal(self, tmp_path: Path) -> None:
        from specify_cli.events import _remove_toml_entries

        dst = tmp_path / "hooks.toml"
        content = "[[hooks.custom]]\ncommand = 'keep'\n\n[[hooks.session_start]]\ncommand = 'remove'\nspeckit_marker = true\n"
        dst.write_text(content, encoding="utf-8")

        result = _remove_toml_entries(dst)

        assert result is False  # file still has user content
        remaining = dst.read_text(encoding="utf-8")
        assert "custom" in remaining
        assert "speckit_marker" not in remaining

    def test_original_intact_on_write_failure(self, tmp_path: Path) -> None:
        from specify_cli.events import _remove_toml_entries

        dst = tmp_path / "hooks.toml"
        # Must have BOTH speckit AND user content so the function tries to write
        original = "[[hooks.custom]]\ncommand = 'keep'\n\n[[hooks.session_start]]\ncommand = 'test'\nspeckit_marker = true\n"
        dst.write_text(original, encoding="utf-8")

        with patch("specify_cli.events.os.replace", side_effect=OSError("fail")):
            with pytest.raises(OSError, match="fail"):
                _remove_toml_entries(dst)

        assert dst.read_text(encoding="utf-8") == original


# -- save_init_options (_init_options.py) ------------------------------------

class TestSaveInitOptionsAtomic:
    """Atomic writes for save_init_options in _init_options.py."""

    def test_successful_write(self, tmp_path: Path) -> None:
        from specify_cli._init_options import save_init_options, load_init_options

        options = {"integration": "copilot", "script_type": "sh"}
        save_init_options(tmp_path, options)

        loaded = load_init_options(tmp_path)
        assert loaded == options

    def test_original_intact_on_write_failure(self, tmp_path: Path) -> None:
        from specify_cli._init_options import save_init_options, load_init_options

        original = {"integration": "original"}
        save_init_options(tmp_path, original)

        with patch("specify_cli._init_options.os.replace", side_effect=OSError("fail")):
            with pytest.raises(OSError, match="fail"):
                save_init_options(tmp_path, {"corrupted": True})

        loaded = load_init_options(tmp_path)
        assert loaded == original


# -- _atomic_write_text (presets/__init__.py) --------------------------------

class TestAtomicWriteTextPresets:
    """Atomic writes for _atomic_write_text in presets."""

    def test_successful_write(self, tmp_path: Path) -> None:
        from specify_cli.presets import _atomic_write_text

        path = tmp_path / "command.md"
        content = "# My Command\n\nRun this."

        _atomic_write_text(path, content)

        assert path.read_text(encoding="utf-8") == content

    def test_original_intact_on_write_failure(self, tmp_path: Path) -> None:
        from specify_cli.presets import _atomic_write_text

        path = tmp_path / "command.md"
        path.write_text("original content", encoding="utf-8")

        with patch("specify_cli.presets.os.replace", side_effect=OSError("fail")):
            with pytest.raises(OSError, match="fail"):
                _atomic_write_text(path, "new content")

        assert path.read_text(encoding="utf-8") == "original content"

    def test_temp_file_cleaned_up_after_failure(self, tmp_path: Path) -> None:
        from specify_cli.presets import _atomic_write_text

        path = tmp_path / "command.md"
        before = set(tmp_path.iterdir())

        with patch("specify_cli.presets.os.replace", side_effect=OSError("fail")):
            with pytest.raises(OSError):
                _atomic_write_text(path, "content")

        after = set(tmp_path.iterdir())
        new_files = after - before
        for f in new_files:
            assert not f.name.startswith(".command.md.")
