"""Hash-tracked installation manifest for integrations.

Each installed integration records the files it created together with
their SHA-256 hashes.  On uninstall only files whose hash still matches
the recorded value are removed — modified files are left in place and
reported to the caller.
"""

from __future__ import annotations

import hashlib
import json
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
        return abs_path

    def record_existing(self, rel_path: str | Path) -> None:
        """Record the hash of an already-existing file at *rel_path*.

        Raises ``ValueError`` if *rel_path* resolves outside the project root.
        """
        rel = Path(rel_path)
        abs_path = _validate_rel_path(rel, self.project_root)
        normalized = abs_path.relative_to(self.project_root).as_posix()
        self._files[normalized] = _sha256(abs_path)

    # -- Querying ---------------------------------------------------------

    @property
    def files(self) -> dict[str, str]:
        """Return a copy of the ``{rel_path: sha256}`` mapping."""
        return dict(self._files)

    def check_modified(self) -> list[str]:
        """Return relative paths of tracked files whose content changed on disk."""
        modified: list[str] = []
        for rel, expected_hash in self._files.items():
            try:
                abs_path = _validate_rel_path(Path(rel), self.project_root)
            except ValueError:
                continue
            if not abs_path.exists():
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
            abs_path = (root / rel).resolve()
            # Skip paths that escape the project root
            try:
                abs_path.relative_to(root)
            except ValueError:
                continue
            if not abs_path.exists():
                continue
            if not force and _sha256(abs_path) != expected_hash:
                skipped.append(abs_path)
                continue
            abs_path.unlink()
            removed.append(abs_path)
            # Clean up empty parent directories up to project root
            parent = abs_path.parent
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
        }
        path = self.manifest_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        return path

    @classmethod
    def load(cls, key: str, project_root: Path) -> IntegrationManifest:
        """Load an existing manifest from disk.

        Raises ``FileNotFoundError`` if the manifest does not exist.
        """
        inst = cls(key, project_root)
        path = inst.manifest_path
        data = json.loads(path.read_text(encoding="utf-8"))

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
        return inst
