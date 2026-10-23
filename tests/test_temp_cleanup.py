"""Tests for temp-file cleanup resilience.

PR #3820 wraps ``Path.unlink(missing_ok=True)`` in try/except OSError
in three atomic-write paths so that a cleanup failure never masks the
original exception in finally/except blocks.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest

from specify_cli._utils import handle_vscode_settings
from specify_cli.integrations.manifest import IntegrationManifest
from specify_cli.shared_infra import _write_shared_bytes


class TestManifestSaveCleanupOSError:
    """IntegrationManifest.save() must raise the write error, not the cleanup error."""

    def test_cleanup_oserror_does_not_mask_replace_error(self, tmp_path):
        """If os.replace fails AND unlink raises OSError, the replace error propagates."""
        m = IntegrationManifest("test", tmp_path)
        m.record_file("f.txt", "content")

        original_err = OSError("replace failed")
        cleanup_err = OSError("unlink failed")

        with patch("specify_cli.integrations.manifest.os.replace", side_effect=original_err):
            with patch(
                "specify_cli.integrations.manifest.Path.unlink",
                side_effect=cleanup_err,
            ):
                with pytest.raises(OSError, match="replace failed"):
                    m.save()

    def test_cleanup_oserror_does_not_mask_write_error(self, tmp_path):
        """If fdopen write fails AND unlink raises OSError, the write error propagates."""
        m = IntegrationManifest("test", tmp_path)

        write_err = OSError("write failed")
        cleanup_err = OSError("unlink failed")

        with patch("specify_cli.integrations.manifest.os.fdopen") as mock_fdopen:
            mock_fdopen.return_value.__enter__ = lambda s: s
            mock_fdopen.return_value.__exit__ = lambda *a: False
            mock_fdopen.return_value.write.side_effect = write_err

            with patch(
                "specify_cli.integrations.manifest.Path.unlink",
                side_effect=cleanup_err,
            ):
                with pytest.raises(OSError, match="write failed"):
                    m.save()


class TestSharedInfraCleanupOSError:
    """_write_shared_bytes() must raise the write error, not the cleanup error."""

    def test_cleanup_oserror_does_not_mask_write_error(self, tmp_path):
        """If write fails AND unlink raises OSError, the write error propagates."""
        dest = tmp_path / "out.bin"
        write_err = OSError("disk full")
        cleanup_err = OSError("unlink blocked")

        with patch("specify_cli.shared_infra.os.fdopen") as mock_fdopen:
            mock_fdopen.return_value.__enter__ = lambda s: s
            mock_fdopen.return_value.__exit__ = lambda *a: False
            mock_fdopen.return_value.write.side_effect = write_err

            with patch(
                "specify_cli.shared_infra.Path.unlink",
                side_effect=cleanup_err,
            ):
                with pytest.raises(OSError, match="disk full"):
                    _write_shared_bytes(tmp_path, dest, b"data")


class TestUtilsCleanupOSError:
    """handle_vscode_settings() must preserve the original error, not the cleanup error."""

    def test_cleanup_oserror_does_not_mask_replace_error(self, tmp_path, capsys):
        """If os.replace fails AND unlink raises OSError, the replace error is logged."""
        src = tmp_path / "src.json"
        src.write_text('{"a": 1}', encoding="utf-8")
        dest = tmp_path / ".vscode" / "settings.json"
        dest.parent.mkdir(parents=True)
        dest.write_text('{"b": 2}', encoding="utf-8")

        replace_err = OSError("replace blocked")
        cleanup_err = OSError("unlink blocked")

        with patch("specify_cli._utils.os.replace", side_effect=replace_err):
            with patch(
                "specify_cli._utils.Path.unlink",
                side_effect=cleanup_err,
            ):
                handle_vscode_settings(str(src), dest, "rel.json", verbose=True)
                captured = capsys.readouterr()
                assert "replace blocked" in captured.out
