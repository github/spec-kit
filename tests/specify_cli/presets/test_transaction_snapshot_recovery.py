"""Recovery guarantees of the shared preset/extension artifact snapshot.

The snapshot is the only copy of the pre-mutation artifacts, so a failed
restore must not also delete it, and cleanup running from a ``finally`` must
never replace the operation's own exception with a cleanup error.
"""

from __future__ import annotations

import os

import pytest

from specify_cli.presets import _transaction


def _snapshot_with_file(tmp_path, name="artifact.md", body="ORIGINAL\n"):
    """Capture one file, then mutate it so the backup holds the original bytes."""
    target = tmp_path / name
    target.write_text(body, encoding="utf-8")
    snapshot = _transaction._ArtifactSnapshot()
    snapshot.capture(target)
    target.unlink()
    return snapshot, target


def test_failed_restore_retains_the_backup_copies(tmp_path, monkeypatch):
    """A restore that cannot put the artifact back must keep its backup.

    The live file is deleted before the copy is attempted, so a failing copy
    would otherwise destroy both copies: nothing would be left to recover from.
    """
    snapshot, target = _snapshot_with_file(tmp_path)

    def failing_copy(src, dst, *args, **kwargs):
        raise OSError("simulated restore failure")

    monkeypatch.setattr(_transaction.shutil, "copy2", failing_copy)

    with pytest.raises(OSError) as excinfo:
        snapshot.restore()

    assert "retained backups" in str(excinfo.value)
    retained = snapshot.retained_path
    assert retained is not None, "failed restore did not retain its backups"
    assert retained.exists(), "retained backup directory was removed"
    backups = list(retained.iterdir())
    assert backups, "retained directory has no backup copies"
    assert backups[0].read_text(encoding="utf-8") == "ORIGINAL\n"
    assert not target.exists()


def test_close_never_replaces_the_active_error(tmp_path, monkeypatch):
    """Cleanup must be configured best-effort.

    ``close()`` runs from a ``finally`` on the failure path, so a backup tree
    Windows still has locked must not turn into an exception that replaces the
    operation's own error. The interpreter routes that case through
    ``TemporaryDirectory``'s own error handling, so the portable assertion is
    the wiring itself: cleanup must be created with ``ignore_cleanup_errors``.
    """
    import tempfile

    observed = []
    real_cleanup = tempfile.TemporaryDirectory.cleanup

    def recording_cleanup(self):
        observed.append(getattr(self, "_ignore_cleanup_errors", None))
        return real_cleanup(self)

    monkeypatch.setattr(tempfile.TemporaryDirectory, "cleanup", recording_cleanup)
    snapshot, _target = _snapshot_with_file(tmp_path, name="locked.md")

    snapshot.close()  # must not raise

    assert observed == [True], "cleanup was not configured to ignore errors"


def test_close_keeps_retained_backups(tmp_path):
    """Closing a retained snapshot must not delete the recovery copies."""
    snapshot, _target = _snapshot_with_file(tmp_path, name="retained.md")
    retained = snapshot.retain()
    assert retained is not None

    snapshot.close()

    assert retained.exists(), "close() removed the retained backups"
    backups = list(retained.iterdir())
    assert backups and backups[0].read_text(encoding="utf-8") == "ORIGINAL\n"


def test_directory_symlink_survives_a_snapshot_round_trip(tmp_path):
    """A captured directory link must be restored as a directory link.

    POSIX recreates the link from the target alone, but Windows needs
    ``target_is_directory`` to recreate a directory link (and to create the
    backup link in the first place). The Windows side of that flag is
    UNVERIFIED locally; this locks the round trip on the platform we can run.
    """
    real_dir = tmp_path / "real"
    real_dir.mkdir()
    (real_dir / "inside.md").write_text("BODY\n", encoding="utf-8")
    link = tmp_path / "link"
    link.symlink_to(real_dir)

    snapshot = _transaction._ArtifactSnapshot()
    snapshot.capture(link)
    link.unlink()
    snapshot.restore()

    assert link.is_symlink(), "restored path is not a symlink"
    assert link.is_dir(), "restored directory link does not resolve to a directory"
    assert os.readlink(link) == str(real_dir)
    snapshot.close()
