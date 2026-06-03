"""Hash-tracked installation manifest for integrations.

Each installed integration records the files it created together with
their SHA-256 hashes.  On uninstall only files whose hash still matches
the recorded value are removed — modified files are left in place and
reported to the caller.
"""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _sha256(path: Path) -> str:
    """Return the hex SHA-256 digest of *path*."""
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def _validate_rel_path(rel: Path, root: Path) -> Path:
    """Resolve *rel* against *root* and verify it stays within *root*.

    Raises ``ValueError`` if *rel* is absolute, contains ``..`` segments
    that escape *root*, or otherwise resolves outside the project root.
    """
    if rel.is_absolute():
        raise ValueError(
            f"Absolute paths are not allowed in manifests: {rel}"
        )
    resolved = (root / rel).resolve()
    root_resolved = root.resolve()
    try:
        resolved.relative_to(root_resolved)
    except ValueError:
        raise ValueError(
            f"Path {rel} resolves to {resolved} which is outside "
            f"the project root {root_resolved}"
        ) from None
    return resolved


def _manifest_path_label(root: Path, path: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def _ensure_safe_manifest_directory(root: Path, directory: Path) -> None:
    """Create a manifest directory without following symlinked parents."""
    root_resolved = root.resolve()
    try:
        rel = directory.relative_to(root)
    except ValueError:
        label = _manifest_path_label(root, directory)
        raise ValueError(f"Integration manifest directory escapes project root: {label}") from None

    current = root
    for part in rel.parts:
        current = current / part
        label = _manifest_path_label(root, current)
        if current.is_symlink():
            raise ValueError(f"Refusing to use symlinked integration manifest directory: {label}")
        if current.exists():
            if not current.is_dir():
                raise ValueError(f"Integration manifest directory path is not a directory: {label}")
            try:
                current.resolve().relative_to(root_resolved)
            except (OSError, ValueError):
                raise ValueError(f"Integration manifest directory escapes project root: {label}") from None
            continue
        current.mkdir()
        try:
            current.resolve().relative_to(root_resolved)
        except (OSError, ValueError):
            raise ValueError(f"Integration manifest directory escapes project root: {label}") from None


def _ensure_safe_manifest_destination(root: Path, path: Path) -> None:
    """Refuse manifest writes that would escape the project or follow symlinks."""
    root_resolved = root.resolve()
    _ensure_safe_manifest_directory(root, path.parent)
    label = _manifest_path_label(root, path)
    if path.is_symlink():
        raise ValueError(f"Refusing to overwrite symlinked integration manifest path: {label}")
    if path.exists():
        if not path.is_file():
            raise ValueError(f"Integration manifest path is not a file: {label}")
        try:
            path.resolve().relative_to(root_resolved)
        except (OSError, ValueError):
            raise ValueError(f"Integration manifest path escapes project root: {label}") from None


class IntegrationManifest:
    """Tracks files installed by a single integration.

    Parameters:
        key:          Integration identifier (e.g. ``"copilot"``).
        project_root: Absolute path to the project directory.
        version:      CLI version string recorded in the manifest.
    """

    def __init__(self, key: str, project_root: Path, version: str = "") -> None:
        self.key = key
        self.project_root = project_root.resolve()
        self.version = version
        self._files: dict[str, str] = {}  # rel_path → sha256 hex
        self._recovered_files: set[str] = set()
        self._installed_at: str = ""

    # -- Manifest file location -------------------------------------------

    @property
    def manifest_path(self) -> Path:
        """Path to the on-disk manifest JSON."""
        return self.project_root / ".specify" / "integrations" / f"{self.key}.manifest.json"

    # -- Recording files --------------------------------------------------

    def record_file(self, rel_path: str | Path, content: bytes | str) -> Path:
        """Write *content* to *rel_path* (relative to project root) and record its hash.

        Creates parent directories as needed.  Returns the absolute path
        of the written file.
        If the path was previously marked as recovered via
        ``record_existing(recovered=True)``, the recovered marker is
        cleared because the bytes are now produced, not merely observed.

        Raises ``ValueError`` if *rel_path* resolves outside the project root.
        """
        rel = Path(rel_path)
        abs_path = _validate_rel_path(rel, self.project_root)
        abs_path.parent.mkdir(parents=True, exist_ok=True)

        if isinstance(content, str):
            content = content.encode("utf-8")
        abs_path.write_bytes(content)

        normalized = abs_path.relative_to(self.project_root).as_posix()
        self._files[normalized] = hashlib.sha256(content).hexdigest()
        # ``record_file`` writes *produced* content, so any prior
        # recovered marker for this path is no longer accurate.
        self._recovered_files.discard(normalized)
        return abs_path

    def record_existing(self, rel_path: str | Path, *, recovered: bool = False) -> None:
        """Record the hash of an already-existing regular file at *rel_path*.

        When ``recovered=True``, the path is also marked in the manifest's
        ``recovered_files`` list to signal that the file's on-disk hash was
        *observed* during install (because the file already existed and was not
        overwritten), not *produced* by the install. Future ``refresh_managed``
        runs should consult ``is_recovered`` before treating the recorded hash
        as a managed baseline.

        Raises:
            ValueError: if *rel_path* resolves outside the project root, is
                a symlink, or is not a regular file. A directory or other
                non-file path cannot be silently recorded — its hash would
                be meaningless and ``check_modified``/``uninstall`` would
                treat the entry as permanently broken.
            OSError: if the underlying filesystem call (``is_symlink``,
                ``is_file``, or the file-read used to compute the hash)
                fails — for example a ``PermissionError`` on the path.
                Callers should be prepared to handle ``OSError`` (and its
                subclasses such as ``PermissionError``) in addition to
                ``ValueError``.
        """
        rel = Path(rel_path)
        # Cheap lexical pre-check first so absolute / parent-traversal paths
        # don't trigger a filesystem stat outside the project root before
        # ``_validate_rel_path`` raises. ``_validate_rel_path`` produces the
        # canonical error messages used elsewhere.
        if rel.is_absolute() or ".." in rel.parts:
            _validate_rel_path(rel, self.project_root)
            # _validate_rel_path raised for any actually-escaping path. If we reach
            # here the path normalizes inside root (e.g. ``dir/../file.txt``).
            # Reject anyway: manifest keys must be canonical so ``check_modified``
            # and ``uninstall`` cannot key the same file under two paths.
            raise ValueError(
                f"Manifest paths must be canonical; '..' segments are not "
                f"allowed (got {rel})"
            )
        # Walk each path component before resolution so a symlinked ancestor
        # (e.g. ``linked_dir/file.txt`` where ``linked_dir`` is a symlink)
        # cannot be silently followed by ``_validate_rel_path().resolve()``
        # down to a target outside the project root. ``_ensure_safe_manifest_directory``
        # uses the same pattern.
        _walk = self.project_root
        for part in rel.parts:
            _walk = _walk / part
            if _walk.is_symlink():
                raise ValueError(
                    f"Refusing to record symlinked manifest path: {rel} "
                    f"(symlinked at {_walk.relative_to(self.project_root).as_posix()})"
                )
        abs_path = _validate_rel_path(rel, self.project_root)
        if not abs_path.is_file():
            raise ValueError(
                f"Manifest path is not a regular file: {rel}"
            )
        normalized = abs_path.relative_to(self.project_root).as_posix()
        self._files[normalized] = _sha256(abs_path)
        if recovered:
            self._recovered_files.add(normalized)
        else:
            # ``recovered=False`` means the caller is asserting this path is
            # managed-baseline now, not merely observed; drop any stale
            # recovered marker so future is_recovered() queries reflect the
            # transition. ``discard`` is a no-op when the key is absent.
            self._recovered_files.discard(normalized)

    # -- Querying ---------------------------------------------------------

    @property
    def files(self) -> dict[str, str]:
        """Return a copy of the ``{rel_path: sha256}`` mapping."""
        return dict(self._files)

    @property
    def recovered_files(self) -> set[str]:
        """Return a copy of the set of paths recorded with ``recovered=True``.

        These entries had their hashes observed (not produced) during install
        because the file already existed on disk and the install skipped it.
        Their on-disk bytes may be user customizations — callers that would
        overwrite based on hash equality (e.g. ``refresh_managed``) MUST check
        ``is_recovered`` first.
        """
        return set(self._recovered_files)

    def is_recovered(self, rel_path: str | Path) -> bool:
        """Return True if *rel_path* was recorded via ``record_existing(recovered=True)``.

        Input is normalized through the same pipeline as ``record_existing``:
        absolute paths, paths escaping the project root, AND paths containing
        ``'..'`` segments are rejected (returned as ``False``). This mirrors
        ``record_existing``'s canonicalization guard — such paths can never
        appear as stored keys, so the answer is always ``False``.
        """
        rel = Path(rel_path)
        if rel.is_absolute() or ".." in rel.parts:
            return False
        try:
            abs_path = _validate_rel_path(rel, self.project_root)
            normalized = abs_path.relative_to(self.project_root).as_posix()
        except ValueError:
            return False
        return normalized in self._recovered_files

    def check_modified(self) -> list[str]:
        """Return relative paths of tracked files whose content changed on disk."""
        modified: list[str] = []
        for rel, expected_hash in self._files.items():
            rel_path = Path(rel)
            # Skip paths that are absolute or attempt to escape the project root
            if rel_path.is_absolute() or ".." in rel_path.parts:
                continue
            abs_path = self.project_root / rel_path
            if not abs_path.exists() and not abs_path.is_symlink():
                continue
            # Treat symlinks and non-regular-files as modified
            if abs_path.is_symlink() or not abs_path.is_file():
                modified.append(rel)
                continue
            if _sha256(abs_path) != expected_hash:
                modified.append(rel)
        return modified

    # -- Uninstall --------------------------------------------------------

    def uninstall(
        self,
        project_root: Path | None = None,
        *,
        force: bool = False,
    ) -> tuple[list[Path], list[Path]]:
        """Remove tracked files whose hash still matches.

        Parameters:
            project_root: Override for the project root.
            force:        If ``True``, remove files even if modified.

        Returns:
            ``(removed, skipped)`` — absolute paths.
        """
        root = (project_root or self.project_root).resolve()
        removed: list[Path] = []
        skipped: list[Path] = []

        for rel, expected_hash in self._files.items():
            # Use non-resolved path for deletion so symlinks themselves
            # are removed, not their targets.
            path = root / rel
            # Validate containment lexically (without following symlinks)
            # by collapsing .. segments via Path resolution on the string parts.
            try:
                normed = Path(os.path.normpath(path))
                normed.relative_to(root)
            except (ValueError, OSError):
                continue
            if not path.exists() and not path.is_symlink():
                continue
            # Skip directories — manifest only tracks files
            if not path.is_file() and not path.is_symlink():
                skipped.append(path)
                continue
            # Never follow symlinks when comparing hashes. Only remove
            # symlinks when forced, to avoid acting on tampered entries.
            if path.is_symlink():
                if not force:
                    skipped.append(path)
                    continue
            else:
                if not force and _sha256(path) != expected_hash:
                    skipped.append(path)
                    continue
            try:
                path.unlink()
            except OSError:
                skipped.append(path)
                continue
            removed.append(path)
            # Clean up empty parent directories up to project root
            parent = path.parent
            while parent != root:
                try:
                    parent.rmdir()  # only succeeds if empty
                except OSError:
                    break
                parent = parent.parent

        # Remove the manifest file itself
        manifest = root / ".specify" / "integrations" / f"{self.key}.manifest.json"
        if manifest.exists():
            manifest.unlink()
            parent = manifest.parent
            while parent != root:
                try:
                    parent.rmdir()
                except OSError:
                    break
                parent = parent.parent

        return removed, skipped

    # -- Persistence ------------------------------------------------------

    def save(self) -> Path:
        """Write the manifest to disk.  Returns the manifest path."""
        self._installed_at = self._installed_at or datetime.now(timezone.utc).isoformat()
        data: dict[str, Any] = {
            "integration": self.key,
            "version": self.version,
            "installed_at": self._installed_at,
            "files": self._files,
            **(
                {"recovered_files": sorted(self._recovered_files)}
                if self._recovered_files
                else {}
            ),
        }
        path = self.manifest_path
        content = json.dumps(data, indent=2) + "\n"
        _ensure_safe_manifest_destination(self.project_root, path)
        fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
        temp_path = Path(temp_name)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                fh.write(content)
            temp_path.chmod(0o644)
            _ensure_safe_manifest_destination(self.project_root, path)
            os.replace(temp_path, path)
        finally:
            if temp_path.exists():
                temp_path.unlink()
        return path

    @classmethod
    def load(cls, key: str, project_root: Path) -> IntegrationManifest:
        """Load an existing manifest from disk.

        Raises ``FileNotFoundError`` if the manifest does not exist.
        """
        inst = cls(key, project_root)
        path = inst.manifest_path
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"Integration manifest at {path} contains invalid JSON"
            ) from exc

        if not isinstance(data, dict):
            raise ValueError(
                f"Integration manifest at {path} must be a JSON object, "
                f"got {type(data).__name__}"
            )

        files = data.get("files", {})
        if not isinstance(files, dict) or not all(
            isinstance(k, str) and isinstance(v, str) for k, v in files.items()
        ):
            raise ValueError(
                f"Integration manifest 'files' at {path} must be a "
                "mapping of string paths to string hashes"
            )

        inst.version = data.get("version", "")
        inst._installed_at = data.get("installed_at", "")
        inst._files = files

        recovered = data.get("recovered_files", [])
        if not isinstance(recovered, list) or not all(
            isinstance(p, str) for p in recovered
        ):
            raise ValueError(
                f"Integration manifest 'recovered_files' at {path} must be a "
                "list of string paths"
            )
        inst._recovered_files = set(recovered)
        # Drop any recovered_files entries that don't correspond to tracked
        # files — defensive against externally-edited or partially-corrupted
        # manifests. Inconsistent state self-corrects on next save().
        inst._recovered_files &= set(inst._files.keys())

        stored_key = data.get("integration", "")
        if stored_key and stored_key != key:
            raise ValueError(
                f"Manifest at {path} belongs to integration {stored_key!r}, "
                f"not {key!r}"
            )

        return inst
