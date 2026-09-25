"""Crash-injection tests for atomic write helpers.

Verifies that mkstemp + os.replace write patterns across the codebase
leave the original file intact when a mid-write failure occurs, and that
temp files are cleaned up.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from unittest.mock import patch

import pytest

_REAL_FDOPEN = os.fdopen


def _flaky_fdopen(fd: int, mode: str, *args, **kwargs):
    """Real fdopen that commits partial bytes then fails mid-write.

    Writes a partial byte to the genuine temp file through the real file
    object and closes its descriptor, then returns a stand-in ``write``
    that raises on the next call — simulating a write interruption partway
    through. The descriptor is released so the writer's ``os.unlink`` temp
    cleanup works on Windows too.
    """
    real = _REAL_FDOPEN(fd, mode, *args, **kwargs)
    real.write("X")
    real.close()

    class _FlakyTemp:
        def __enter__(self):
            return self

        def __exit__(self, *exc_info):
            return False

        def write(self, text):  # noqa: D102
            raise OSError("disk full mid-write")

    return _FlakyTemp()


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

    def test_original_intact_on_replace_failure(self, tmp_path: Path) -> None:
        """A failure at the rename step must leave the original file intact."""
        from specify_cli.events import _safe_write_json

        dst = tmp_path / "config.json"
        original = {"original": True}
        dst.write_text(json.dumps(original) + "\n", encoding="utf-8")

        with patch("specify_cli.events.os.replace", side_effect=OSError("disk full")):
            with pytest.raises(OSError, match="disk full"):
                _safe_write_json(dst, {"corrupted": True})

        loaded = json.loads(dst.read_text(encoding="utf-8"))
        assert loaded == original

    def test_original_intact_on_partial_write(self, tmp_path: Path) -> None:
        """An interruption partway through the temp-file write must not
        corrupt the target: bytes only land in the temp file and the swap
        happens on a fully-written file, so a mid-write failure keeps the
        original intact."""
        from specify_cli import events

        dst = tmp_path / "config.json"
        original = {"original": True}
        dst.write_text(json.dumps(original) + "\n", encoding="utf-8")

        with patch("specify_cli.events.os.fdopen", side_effect=_flaky_fdopen):
            with pytest.raises(OSError, match="disk full mid-write"):
                events._safe_write_json(dst, {"corrupted": True})

        loaded = json.loads(dst.read_text(encoding="utf-8"))
        assert loaded == original

    def test_temp_file_cleaned_up_after_partial_write(self, tmp_path: Path) -> None:
        """Temp files must not be left behind after a mid-write failure."""
        from specify_cli import events

        dst = tmp_path / "config.json"
        before = set(tmp_path.iterdir())

        with patch("specify_cli.events.os.fdopen", side_effect=_flaky_fdopen):
            with pytest.raises(OSError):
                events._safe_write_json(dst, {"data": 1})

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

    def test_original_intact_on_partial_write(self, tmp_path: Path) -> None:
        from specify_cli import events

        dst = tmp_path / "hooks.toml"
        original = "[[hooks.custom]]\ncommand = 'original'\n"
        dst.write_text(original, encoding="utf-8")

        with patch("specify_cli.events.os.fdopen", side_effect=_flaky_fdopen):
            with pytest.raises(OSError, match="disk full mid-write"):
                events._merge_toml_fragment(dst, "fragment")

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

    def test_original_intact_on_partial_write(self, tmp_path: Path) -> None:
        from specify_cli import events

        dst = tmp_path / "hooks.toml"
        original = "[[hooks.custom]]\ncommand = 'keep'\n\n[[hooks.session_start]]\ncommand = 'test'\nspeckit_marker = true\n"
        dst.write_text(original, encoding="utf-8")

        with patch("specify_cli.events.os.fdopen", side_effect=_flaky_fdopen):
            with pytest.raises(OSError, match="disk full mid-write"):
                events._remove_toml_entries(dst)

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

    def test_original_intact_on_partial_write(self, tmp_path: Path) -> None:
        from specify_cli import _init_options

        original = {"integration": "original"}
        _init_options.save_init_options(tmp_path, original)

        with patch("specify_cli._init_options.os.fdopen", side_effect=_flaky_fdopen):
            with pytest.raises(OSError, match="disk full mid-write"):
                _init_options.save_init_options(tmp_path, {"corrupted": True})

        assert _init_options.load_init_options(tmp_path) == original

    def test_preserves_file_permissions(self, tmp_path: Path) -> None:
        """Atomic write should preserve original file permissions."""
        from specify_cli._init_options import save_init_options

        dst = tmp_path / ".specify" / "init-options.json"
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text("{}\n", encoding="utf-8")
        original_mode = dst.stat().st_mode & 0o7777

        save_init_options(tmp_path, {"integration": "copilot"})

        new_mode = dst.stat().st_mode & 0o7777
        assert new_mode == original_mode


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

    def test_original_intact_on_partial_write(self, tmp_path: Path) -> None:
        from specify_cli import presets

        path = tmp_path / "command.md"
        path.write_text("original content", encoding="utf-8")

        with patch("specify_cli.presets.os.fdopen", side_effect=_flaky_fdopen):
            with pytest.raises(OSError, match="disk full mid-write"):
                presets._atomic_write_text(path, "new content")

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