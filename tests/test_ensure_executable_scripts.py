"""Regression tests for ensure_executable_scripts exception narrowing."""
from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from specify_cli import ensure_executable_scripts


class TestEnsureExecutableScriptsExceptionNarrowing:
    """Verify the narrowed exception boundary in ensure_executable_scripts."""

    def test_oserror_during_open_is_skipped(self, tmp_path):
        """An OSError when opening a script must be skipped, not propagated.

        The inner try/except catches (OSError, PermissionError) and continues
        to the next script. This test verifies the script is simply skipped
        (not made executable) when open() raises OSError.
        """
        scripts_dir = tmp_path / ".specify" / "scripts"
        scripts_dir.mkdir(parents=True)
        script = scripts_dir / "gate.sh"
        script.write_bytes(b"#!/usr/bin/env bash\necho hi\n")

        original_open = Path.open

        call_count = 0

        def open_side_effect(self, *args, **kwargs):
            nonlocal call_count
            if self == script and call_count == 0:
                call_count += 1
                raise OSError("Permission denied")
            return original_open(self, *args, **kwargs)

        with patch.object(Path, "open", open_side_effect):
            # Must not raise — OSError is caught by the narrowed except clause
            ensure_executable_scripts(tmp_path)

        # Script should NOT be made executable since open() failed
        st = script.stat()
        assert not (st.st_mode & 0o111), "Script should not have execute bits"

    def test_unexpected_exception_propagates_to_outer_handler(self, tmp_path):
        """A non-OSError exception (e.g. RuntimeError) must propagate out of
        the inner try block and be caught by the outer except Exception handler,
        which records it as a failure."""
        scripts_dir = tmp_path / ".specify" / "scripts"
        scripts_dir.mkdir(parents=True)
        script = scripts_dir / "gate.sh"
        script.write_bytes(b"#!/usr/bin/env bash\necho hi\n")

        original_open = Path.open

        call_count = 0

        def open_side_effect(self, *args, **kwargs):
            nonlocal call_count
            if self == script and call_count == 0:
                call_count += 1
                raise RuntimeError("unexpected failure")
            return original_open(self, *args, **kwargs)

        with patch.object(Path, "open", open_side_effect):
            # RuntimeError is NOT in (OSError, PermissionError), so the inner
            # except does NOT catch it. The outer except Exception handler
            # catches it and appends to failures[]. No exception escapes.
            ensure_executable_scripts(tmp_path)

        # The outer handler caught the RuntimeError; script stays non-executable
        st = script.stat()
        assert not (st.st_mode & 0o111), "Script should not have execute bits"

    @pytest.mark.skipif(os.name == "nt", reason="No POSIX execute bits on Windows")
    def test_normal_shebang_script_gets_executable(self, tmp_path):
        """A script with a shebang must get execute bits set."""
        scripts_dir = tmp_path / ".specify" / "scripts"
        scripts_dir.mkdir(parents=True)
        script = scripts_dir / "gate.sh"
        script.write_bytes(b"#!/usr/bin/env bash\necho hi\n")
        script.chmod(0o644)

        ensure_executable_scripts(tmp_path)

        assert os.access(script, os.X_OK)

    @pytest.mark.skipif(os.name == "nt", reason="No POSIX execute bits on Windows")
    def test_script_without_shebang_is_skipped(self, tmp_path):
        """A script without a shebang must not be made executable."""
        scripts_dir = tmp_path / ".specify" / "scripts"
        scripts_dir.mkdir(parents=True)
        script = scripts_dir / "data.sh"
        script.write_bytes(b"echo hi\n")
        script.chmod(0o644)

        ensure_executable_scripts(tmp_path)

        assert not os.access(script, os.X_OK)
