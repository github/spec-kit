"""Shared builders for workflow function tests."""

from __future__ import annotations

import io
import threading
import zipfile
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any

import yaml

TRIM_CODE = "def trim(value):\n    return value.strip()\n"


def trim_export(**overrides: Any) -> dict[str, Any]:
    return {"name": "trim", "handler": "trim", **overrides}


def write_package(
    package_dir: Path,
    function_id: str,
    functions: list[dict[str, Any]] | None = None,
    code: str = TRIM_CODE,
    **manifest: Any,
) -> Path:
    """Write a function package (``function.yml`` + ``__init__.py``)."""
    package_dir.mkdir(parents=True, exist_ok=True)
    data = {"id": function_id, "functions": functions or [trim_export()], **manifest}
    (package_dir / "function.yml").write_text(yaml.safe_dump(data), encoding="utf-8")
    (package_dir / "__init__.py").write_text(code, encoding="utf-8")
    return package_dir


def functions_dir(project_root: Path) -> Path:
    return project_root / ".specify" / "workflows" / "functions"


def install_dir(project_root: Path, function_id: str) -> Path:
    return functions_dir(project_root) / function_id


def write_installed(
    project_root: Path,
    function_id: str,
    functions: list[dict[str, Any]] | None = None,
    code: str = TRIM_CODE,
    **manifest: Any,
) -> Path:
    """Place a package directly under the project (as a hand copy would)."""
    return write_package(
        install_dir(project_root, function_id), function_id, functions, code, **manifest
    )


def zip_package(package_dir: Path, *, top_level: str | None = None) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        for path in sorted(package_dir.rglob("*")):
            if path.is_file():
                name = path.relative_to(package_dir).as_posix()
                archive.write(path, f"{top_level}/{name}" if top_level else name)
    return buffer.getvalue()


@contextmanager
def serve_files(files: dict[str, bytes]) -> Iterator[Callable[[str], str]]:
    """Serve *files* from a loopback HTTP server.

    Yields a name -> URL function whose ``requests`` attribute lists the paths
    requested so far.
    """

    requests: list[str] = []

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):  # noqa: N802
            requests.append(self.path)
            body = files.get(self.path.lstrip("/"))
            if body is None:
                self.send_response(404)
                self.end_headers()
                return
            self.send_response(200)
            self.send_header("Content-Type", "application/zip")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args):
            pass

    server = HTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        def url(name: str) -> str:
            return f"http://127.0.0.1:{server.server_port}/{name}"

        url.requests = requests  # type: ignore[attr-defined]
        yield url
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
