"""Shared helpers and fakes for bundler tests.

Kept out of ``tests/conftest.py`` so the existing root fixtures are untouched.
Import what you need explicitly, e.g.::

    from tests.bundler_helpers import FakeInstaller, write_manifest
"""
from __future__ import annotations

import json
from pathlib import Path

import yaml

from specify_cli.bundler.models.manifest import ComponentRef


def valid_manifest_dict(**overrides) -> dict:
    """Return a structurally valid manifest dict; override any top-level key."""
    data = {
        "schema_version": "1.0",
        "bundle": {
            "id": "demo-bundle",
            "name": "Demo Bundle",
            "version": "1.2.0",
            "role": "developer",
            "description": "A demo bundle for tests.",
            "author": "Spec Kit",
            "license": "MIT",
        },
        "requires": {"speckit_version": ">=0.1.0"},
        "provides": {
            "extensions": [{"id": "ext-a", "version": "1.0.0"}],
            "presets": [
                {"id": "preset-a", "version": "2.0.0", "priority": 10, "strategy": "append"}
            ],
            "steps": [{"id": "step-a"}],
            "workflows": [{"id": "wf-a", "version": "0.3.0"}],
        },
        "tags": ["demo", "test"],
    }
    data.update(overrides)
    return data


def write_manifest(directory: Path, data: dict | None = None) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    manifest_path = directory / "bundle.yml"
    manifest_path.write_text(
        yaml.safe_dump(data if data is not None else valid_manifest_dict()),
        encoding="utf-8",
    )
    return manifest_path


def make_project(root: Path) -> Path:
    """Create a minimal Spec Kit project skeleton under *root*."""
    (root / ".specify").mkdir(parents=True, exist_ok=True)
    return root


def catalog_payload(bundles: dict | None = None) -> dict:
    return {
        "schema_version": "1.0",
        "updated_at": "2026-06-19T00:00:00Z",
        "catalog_url": "file://test",
        "bundles": bundles or {},
    }


def catalog_entry_dict(bundle_id: str = "demo-bundle", **overrides) -> dict:
    entry = {
        "id": bundle_id,
        "name": "Demo Bundle",
        "version": "1.2.0",
        "role": "developer",
        "description": "A demo bundle.",
        "author": "Spec Kit",
        "license": "MIT",
        "download_url": "",
        "requires": {"speckit_version": ">=0.1.0"},
        "provides": {"extensions": 1, "presets": 1, "steps": 1, "workflows": 1},
        "verified": True,
    }
    entry.update(overrides)
    return entry


def write_catalog_file(path: Path, bundles: dict) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(catalog_payload(bundles)), encoding="utf-8")
    return path


class FakeInstaller:
    """Deterministic in-memory PrimitiveInstaller for offline integration tests."""

    def __init__(self, *, fail_on: str | None = None) -> None:
        self.installed: set[tuple[str, str]] = set()
        self.install_calls: list[tuple[str, str]] = []
        self.remove_calls: list[tuple[str, str]] = []
        self.refresh_calls: list[tuple[str, str]] = []
        self._fail_on = fail_on

    def _key(self, component: ComponentRef) -> tuple[str, str]:
        return (component.kind, component.id)

    def is_installed(self, project_root: Path, component: ComponentRef) -> bool:
        return self._key(component) in self.installed

    def install(self, project_root: Path, component: ComponentRef) -> None:
        from specify_cli.bundler import BundlerError

        self.install_calls.append(self._key(component))
        if self._fail_on is not None and component.id == self._fail_on:
            raise BundlerError(f"Simulated failure installing {component.id}")
        self.installed.add(self._key(component))

    def remove(self, project_root: Path, component: ComponentRef) -> None:
        self.remove_calls.append(self._key(component))
        self.installed.discard(self._key(component))

    def refresh(self, project_root: Path, component: ComponentRef) -> None:
        self.refresh_calls.append(self._key(component))
        self.installed.add(self._key(component))
