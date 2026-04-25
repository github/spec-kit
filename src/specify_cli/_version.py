import json
import os
import urllib.error
import urllib.request
from typing import Optional

from packaging.version import InvalidVersion, Version

GITHUB_API_LATEST = "https://api.github.com/repos/github/spec-kit/releases/latest"


class VersionService:
    """Version checking and comparison — no console output."""

    def get_installed_version(self) -> str:
        import importlib.metadata
        metadata_errors = [importlib.metadata.PackageNotFoundError]
        invalid_err = getattr(importlib.metadata, "InvalidMetadataError", None)
        if invalid_err is not None:
            metadata_errors.append(invalid_err)
        try:
            return importlib.metadata.version("specify-cli")
        except tuple(metadata_errors):
            return "unknown"

    def _normalize_tag(self, tag: str) -> str:
        return tag[1:] if tag.startswith("v") else tag

    def is_newer(self, latest: str, current: str) -> bool:
        if latest == "unknown" or current == "unknown":
            return False
        try:
            return Version(latest) > Version(current)
        except InvalidVersion:
            return False

    def fetch_latest_tag(self) -> tuple[Optional[str], Optional[str]]:
        """Returns (tag, failure_category). One of the two is always None."""
        req = urllib.request.Request(
            GITHUB_API_LATEST,
            headers={"Accept": "application/vnd.github+json"},
        )
        token = None
        for env_var in ("GH_TOKEN", "GITHUB_TOKEN"):
            candidate = os.environ.get(env_var)
            if candidate is not None:
                candidate = candidate.strip()
                if candidate:
                    token = candidate
                    break
        if token:
            req.add_header("Authorization", f"Bearer {token}")
        try:
            with urllib.request.urlopen(req, timeout=5) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
                tag = payload.get("tag_name")
                if not isinstance(tag, str) or not tag:
                    raise ValueError("GitHub API response missing valid tag_name")
                return tag, None
        except urllib.error.HTTPError as e:
            if e.code == 403:
                return None, "rate limited (try setting GH_TOKEN or GITHUB_TOKEN)"
            return None, f"HTTP {e.code}"
        except (urllib.error.URLError, OSError):
            return None, "offline or timeout"


_version_service = VersionService()
