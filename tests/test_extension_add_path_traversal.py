"""Security test for `specify extension add <label> --from <url>`.

A label containing path separators (e.g. "../../etc/evil") must not let the
download escape the downloads cache directory. The handler does not let the
label participate in the path at all: it downloads to a generated tempfile
(``extension-url-download-*.zip``) created with ``dir=download_dir``, so the
filename is machine-generated and confined to the downloads cache. This test
asserts the resulting path stays inside that directory and carries no path
separators from the raw label.
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

    # A minimal but valid ZIP archive: the `add --from` flow validates the
    # downloaded bytes are a real ZIP before installing, so a non-ZIP body would
    # be rejected upstream of the path-sanitization under test.
    import io
    import zipfile

    _zip_buf = io.BytesIO()
    with zipfile.ZipFile(_zip_buf, "w") as _zf:
        _zf.writestr("extension.yaml", "name: evil\n")
    valid_zip_bytes = _zip_buf.getvalue()

    @contextlib.contextmanager
    def fake_open_url(url, timeout=60, extra_headers=None):
        class _Resp:
            def read(self):
                return valid_zip_bytes
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
