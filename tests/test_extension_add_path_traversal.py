"""Security test for `specify extension add <label> --from <url>`.

The raw extension label is interpolated into the downloaded ZIP filename. A
label containing path separators (e.g. "../../etc/evil") must not let the
download escape the downloads cache directory. The handler sanitizes the
label before building the filename; this test asserts the resulting path
stays inside the downloads dir.
"""

import contextlib

import pytest
from typer.testing import CliRunner

from specify_cli import app
from specify_cli.extensions import ExtensionManager

runner = CliRunner()


@pytest.fixture
def project_dir(tmp_path):
    proj_dir = tmp_path / "project"
    proj_dir.mkdir()
    (proj_dir / ".specify").mkdir()
    (proj_dir / ".specify" / "config.toml").write_text("ai = 'claude'")
    return proj_dir


def test_add_from_url_sanitizes_traversal_label(project_dir, monkeypatch):
    monkeypatch.chdir(project_dir)

    captured = {}

    @contextlib.contextmanager
    def fake_open_url(url, timeout=60):
        class _Resp:
            def read(self):
                return b"not-a-real-zip"
        yield _Resp()

    monkeypatch.setattr("specify_cli.authentication.http.open_url", fake_open_url)

    def fake_install_from_zip(self, zip_path, *args, **kwargs):
        captured["zip_path"] = zip_path
        # Stop the flow before real install/registration runs.
        raise RuntimeError("stop after capture")

    monkeypatch.setattr(ExtensionManager, "install_from_zip", fake_install_from_zip)

    malicious = "../../../etc/evil"
    runner.invoke(
        app,
        ["extension", "add", malicious, "--from", "https://example.com/payload.zip"],
        obj={"project_root": project_dir},
        input="y\n",  # confirm the "Untrusted Source" prompt for --from URLs
    )

    zip_path = captured.get("zip_path")
    assert zip_path is not None, "install_from_zip was never reached"

    download_dir = (project_dir / ".specify" / "extensions" / ".cache" / "downloads").resolve()
    resolved = zip_path.resolve()

    # The download must stay inside the downloads cache dir...
    assert resolved.parent == download_dir
    # ...and the filename must not carry path separators from the raw label.
    assert "/" not in zip_path.name
    assert ".." not in zip_path.name
