from __future__ import annotations

import io
import json
from pathlib import Path
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from specify_cli import app
from specify_cli.bundles.adapters import FIRSTPARTY_CATALOG_URL

runner = CliRunner()
REPO_ROOT = Path(__file__).parents[3]


class FakeBundleResponse(io.BytesIO):
    def __init__(self, data: bytes, url: str):
        super().__init__(data)
        self._url = url

    def geturl(self) -> str:
        return self._url


def test_add_forwards_refresh_default_without_refreshing(project: Path):
    with patch("specify_cli.bundles.command_add.bundle_install") as install:
        result = runner.invoke(app, ["bundle", "add", "demo"])

    assert result.exit_code == 0, result.output
    install.assert_called_once_with(
        bundle_id="demo",
        integration=None,
        offline=False,
        refresh=False,
    )


@pytest.mark.parametrize(
    ("bundle_id", "extension_id"),
    [("bugfix", "bug"), ("assess", "assess")],
)
def test_bundle_add_by_id_initializes_empty_project_from_firstparty_catalog(
    tmp_path: Path, monkeypatch, bundle_id: str, extension_id: str
):
    project = tmp_path / "fresh"
    project.mkdir()
    monkeypatch.chdir(project)

    catalog_bytes = (REPO_ROOT / "bundles" / "catalog.json").read_bytes()
    manifest_bytes = (REPO_ROOT / "bundles" / bundle_id / "bundle.yml").read_bytes()
    expected_manifest_url = (
        "https://raw.githubusercontent.com/github/spec-kit/main/"
        f"bundles/{bundle_id}/bundle.yml"
    )
    captured_urls: list[str] = []

    def fake_open_url(
        url: str,
        timeout: int | None = None,
        extra_headers: dict[str, str] | None = None,
        redirect_validator=None,
    ):
        captured_urls.append(url)
        if url == FIRSTPARTY_CATALOG_URL:
            return FakeBundleResponse(catalog_bytes, url=url)
        if url == expected_manifest_url:
            return FakeBundleResponse(manifest_bytes, url=url)
        raise AssertionError(f"Unexpected network request in by-ID bundle test: {url}")

    with patch("specify_cli.authentication.http.open_url", side_effect=fake_open_url):
        result = runner.invoke(
            app, ["bundle", "add", bundle_id, "--integration", "copilot"]
        )

    assert result.exit_code == 0, result.output
    assert "No Spec Kit project here" in result.output
    assert (project / ".specify").is_dir()
    assert (
        project / ".specify" / "extensions" / extension_id / "extension.yml"
    ).is_file()
    assert (project / ".specify" / "workflows" / bundle_id / "workflow.yml").is_file()
    registry = json.loads(
        (project / ".specify" / "workflows" / "workflow-registry.json").read_text(
            encoding="utf-8"
        )
    )
    assert registry["workflows"][bundle_id]["version"] == "1.0.0"
    assert FIRSTPARTY_CATALOG_URL in captured_urls
    assert expected_manifest_url in captured_urls
