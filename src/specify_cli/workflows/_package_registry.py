"""Persistent registry shared by installed workflow package kinds.

Step packages and function packages are recorded the same way: a JSON file
beside the installed package directories, written atomically and never through
a symlinked path. A kind subclasses :class:`PackageRegistry` and names its
file, directory, record key and error type; persistence and record mutation
(including rollback of the in-memory state when a write fails) live here once.
"""

from __future__ import annotations

import copy
import json
import os
import stat
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, ClassVar

from ..file_helper import FileHelper, FileHelperError


class PackageRegistry:
    """Registry of installed packages under ``.specify/workflows/<DIRECTORY>``."""

    REGISTRY_FILE: ClassVar[str]
    RECORDS_KEY: ClassVar[str]  # top-level key holding the id -> metadata mapping
    DIRECTORY: ClassVar[str]  # directory name under ``.specify/workflows``
    LABEL: ClassVar[str]  # lowercase kind name used in messages
    ERROR: ClassVar[type[Exception]]  # raised when the registry cannot be written
    SCHEMA_VERSION: ClassVar[str] = "1.0"
    # Read bound for policy-aware list operations. Registries are small JSON
    # maps of installed-package metadata, so 1 MiB is generous headroom and
    # matches the MCP wire-response cap; a larger file cannot be served in
    # full anyway. The bound is opt-in (see __init__): existing callers keep
    # the established unbounded load, since silently emptying an oversized
    # registry under a later save() could discard installed packages.
    MAX_REGISTRY_BYTES: ClassVar[int] = 1 * 1024 * 1024

    def __init__(
        self,
        project_root: Path,
        *,
        read_files: FileHelper | None = None,
        max_bytes: int | None = None,
    ) -> None:
        self.project_root = project_root
        self.base_dir = project_root / ".specify" / "workflows" / self.DIRECTORY
        self.registry_path = self.base_dir / self.REGISTRY_FILE
        # Optional policy-aware read handoff for read-only list operations.
        # Existing callers and all mutation paths retain their established
        # behavior when it is not passed.
        self._read_files = read_files
        # Optional input bound, rejected before parsing. None keeps the
        # established unbounded load for existing callers.
        self._max_bytes = max_bytes
        self.data = self._load()

    @property
    def _records(self) -> dict[str, Any]:
        return self.data[self.RECORDS_KEY]

    def _has_symlinked_parent(self) -> bool:
        """Return True if any directory under .specify/workflows/<kind> is a symlink."""
        current = self.project_root
        for part in (".specify", "workflows", self.DIRECTORY):
            current = current / part
            if current.is_symlink():
                return True
        return False

    def _load(self) -> dict[str, Any]:
        """Load registry from disk or create default."""
        default_registry: dict[str, Any] = {
            "schema_version": self.SCHEMA_VERSION,
            self.RECORDS_KEY: {},
        }
        if self._read_files is not None:
            return self._load_via_helper(default_registry, self._read_files)
        # Defense-in-depth: refuse to read the registry if any parent directory
        # is a symlink, which could redirect the read outside the project root.
        if self._has_symlinked_parent():
            return default_registry
        # Defense-in-depth: also refuse to read a symlinked registry file,
        # which could redirect the read outside the project root.
        if self.registry_path.is_symlink():
            return default_registry
        if self.registry_path.exists():
            try:
                # Refuse to open a non-regular file (e.g. a FIFO), which
                # would block the read until a writer shows up.
                if not stat.S_ISREG(os.stat(self.registry_path).st_mode):
                    return default_registry
                if self._max_bytes is None:
                    with open(self.registry_path, encoding="utf-8") as f:
                        data = json.load(f)
                else:
                    # Reject oversized input before parsing it.
                    with open(self.registry_path, "rb") as f:
                        raw = f.read(self._max_bytes + 1)
                    if len(raw) > self._max_bytes:
                        return default_registry
                    data = json.loads(raw.decode("utf-8"))
                # Validate shape: must be a dict with a dict records field
                if not isinstance(data, dict):
                    return default_registry
                if not isinstance(data.get(self.RECORDS_KEY), dict):
                    data[self.RECORDS_KEY] = {}
                return data
            except (json.JSONDecodeError, ValueError, OSError, UnicodeError):
                return default_registry
        return default_registry

    def _load_via_helper(
        self, default_registry: dict[str, Any], read_files: FileHelper
    ) -> dict[str, Any]:
        """Load through the retained project policy helper.

        Unlike the legacy path above, a policy-aware read fails closed: a
        symlinked parent or registry file, a junction, or an unreadable file
        raises OSError instead of fabricating an empty registry, mirroring
        WorkflowRegistry. Missing files, non-regular files, oversized input,
        and corrupt content still fall back to the default registry, matching
        this loader's best-effort contract for its other callers.
        """
        # Fail closed on symlinked paths before reading: the helper read
        # below would refuse them too, but only at read time, after the
        # size probe. (is_symlink misses Windows junctions; those are
        # refused by the helper read itself.)
        if self._has_symlinked_parent() or self.registry_path.is_symlink():
            raise OSError(
                f"Refusing to read {self.LABEL} registry at {self.registry_path}: "
                "a parent directory or the registry file itself is a symlink"
            )
        try:
            # Enforce the read policy on the parent chain before probing: a
            # junction at the steps directory must fail closed even when no
            # registry file exists under it, matching WorkflowRegistry. The
            # read below re-validates the full path, so a swap between this
            # check and the read is still refused there.
            if not read_files.directory_exists(self.base_dir):
                return default_registry
            # Probe type and size before reading: a non-regular file (e.g. a
            # FIFO) stays an empty registry, and oversized input is rejected
            # before it is read or parsed. The probe only observes metadata
            # and may follow an intermediate junction; the read below goes
            # through the policy helper, which refuses junctions and
            # symlinks at the read boundary, and the length check after the
            # read catches growth between probe and read.
            try:
                info = os.stat(self.registry_path)
            except (FileNotFoundError, NotADirectoryError):
                return default_registry
            if not stat.S_ISREG(info.st_mode):
                return default_registry
            if self._max_bytes is not None and info.st_size > self._max_bytes:
                return default_registry
            raw = read_files.read_bytes(self.registry_path)
        except (FileNotFoundError, NotADirectoryError):
            return default_registry
        except (OSError, FileHelperError) as exc:
            raise OSError(
                f"Failed to read {self.LABEL} registry at {self.registry_path}: {exc}"
            ) from exc
        if self._max_bytes is not None and len(raw) > self._max_bytes:
            return default_registry
        try:
            data = json.loads(raw.decode("utf-8"))
        except (json.JSONDecodeError, ValueError, UnicodeError):
            return default_registry
        if not isinstance(data, dict):
            return default_registry
        if not isinstance(data.get(self.RECORDS_KEY), dict):
            data[self.RECORDS_KEY] = {}
        return data

    def save(self) -> None:
        """Persist registry atomically without truncating an existing file."""
        if self._has_symlinked_parent() or self.registry_path.is_symlink():
            raise self.ERROR(
                f"Refusing to write {self.LABEL} registry through a symlinked path."
            )
        fd = -1
        tmp: str | None = None
        try:
            self.base_dir.mkdir(parents=True, exist_ok=True)
            fd, tmp = tempfile.mkstemp(
                dir=str(self.registry_path.parent),
                prefix=f".{self.registry_path.name}.",
                suffix=".tmp",
            )
            # Keep the exclusive descriptor open while writing and checking the
            # path so a replaced temporary file can never be committed.
            with os.fdopen(os.dup(fd), "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=2)
                f.flush()
                os.fsync(f.fileno())
            try:
                if self.registry_path.exists():
                    existing = self.registry_path.stat(follow_symlinks=False)
                    if stat.S_ISREG(existing.st_mode) and hasattr(os, "fchmod"):
                        os.fchmod(fd, stat.S_IMODE(existing.st_mode))
                    if stat.S_ISREG(existing.st_mode) and hasattr(os, "fchown"):
                        try:
                            os.fchown(fd, existing.st_uid, existing.st_gid)
                        except PermissionError:
                            pass
            except OSError:
                # Persisting valid data is more important than preserving mode
                # or ownership metadata when that best-effort operation fails.
                pass
            staged = os.stat(tmp, follow_symlinks=False)
            opened = os.fstat(fd)
            if (
                not stat.S_ISREG(staged.st_mode)
                or staged.st_dev != opened.st_dev
                or staged.st_ino != opened.st_ino
            ):
                raise OSError(f"Staged {self.LABEL} registry changed before commit")
            os.close(fd)
            fd = -1
            os.replace(tmp, self.registry_path)
            tmp = None
        except (OSError, TypeError, ValueError) as exc:
            raise self.ERROR(
                f"Failed to write {self.LABEL} registry at {self.registry_path}: {exc}"
            ) from exc
        finally:
            if fd >= 0:
                try:
                    os.close(fd)
                except OSError:
                    pass
            if tmp is not None:
                try:
                    os.unlink(tmp)
                except OSError:
                    pass

    def add(self, package_id: str, metadata: dict[str, Any]) -> None:
        """Add or update an installed package entry."""
        records = self._records
        raw_existing = records.get(package_id)
        had_entry = package_id in records
        # Corrupted-but-parseable registries may hold non-dict entries; treat
        # them as absent rather than crashing on existing.get() (mirrors
        # WorkflowRegistry.add).
        existing = raw_existing if isinstance(raw_existing, dict) else {}
        metadata_to_store = copy.deepcopy(metadata)
        metadata_to_store["installed_at"] = existing.get(
            "installed_at", datetime.now(UTC).isoformat()
        )
        metadata_to_store["updated_at"] = datetime.now(UTC).isoformat()
        records[package_id] = metadata_to_store
        try:
            self.save()
        except (self.ERROR, TypeError, ValueError):
            if had_entry:
                records[package_id] = raw_existing
            else:
                del records[package_id]
            raise

    def remove(self, package_id: str) -> bool:
        """Remove an installed package entry. Returns True if found."""
        records = self._records
        if package_id in records:
            removed_entry = records[package_id]
            del records[package_id]
            try:
                self.save()
            except (self.ERROR, TypeError, ValueError):
                records[package_id] = removed_entry
                raise
            return True
        return False

    def restore(self, package_id: str, metadata: dict[str, Any]) -> None:
        """Put back a previously removed entry verbatim and persist it.

        Used to undo a removal whose filesystem step failed; unlike ``add`` it
        keeps the original timestamps.
        """
        self._records[package_id] = metadata
        self.save()

    def get(self, package_id: str) -> dict[str, Any] | None:
        """Get metadata for an installed package."""
        return self._records.get(package_id)

    def list(self) -> dict[str, dict[str, Any]]:
        """Return all installed packages."""
        return dict(self._records)

    def is_installed(self, package_id: str) -> bool:
        """Check if a package is installed."""
        return package_id in self._records
