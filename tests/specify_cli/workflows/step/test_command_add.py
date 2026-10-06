"""Command-focused workflow tests."""

from __future__ import annotations

import hashlib
import os

import pytest


class TestWorkflowStepAddCLI:
    @pytest.mark.skipif(not hasattr(os, "symlink"), reason="symlinks are unavailable")
    def test_add_rejects_symlinked_steps_base_dir(self, project_dir, monkeypatch):
        from typer.testing import CliRunner

        from specify_cli import app
        from specify_cli.workflows.step.catalog import StepCatalog

        monkeypatch.chdir(project_dir)
        outside = project_dir.parent / "outside-steps"
        outside.mkdir(parents=True, exist_ok=True)
        steps_link = project_dir / ".specify" / "workflows" / "steps"
        steps_link.symlink_to(outside, target_is_directory=True)

        def _fake_get_step_info(self, step_id):
            return {
                "id": step_id,
                "name": "Test Step",
                "url": "https://example.com/step.yml",
                "init_url": "https://example.com/__init__.py",
                "_install_allowed": True,
            }

        monkeypatch.setattr(StepCatalog, "get_step_info", _fake_get_step_info)

        runner = CliRunner()
        result = runner.invoke(app, ["workflow", "step", "add", "my-step"])

        assert result.exit_code != 0
        assert "Refusing to use symlinked step directory" in result.output

    def test_add_discovery_only_warning_prints_step_id_literally(
        self, project_dir, monkeypatch
    ):
        """A valid step ID containing Rich markup brackets is shown verbatim."""
        from typer.testing import CliRunner

        from specify_cli import app
        from specify_cli.workflows.step.catalog import StepCatalog

        monkeypatch.chdir(project_dir)
        monkeypatch.setattr(
            StepCatalog,
            "get_step_info",
            lambda self, step_id: {"id": step_id, "_install_allowed": False},
        )

        result = CliRunner().invoke(app, ["workflow", "step", "add", "[red]step"])

        assert result.exit_code == 1, result.output
        assert "Step type '[red]step' is from a" in result.output

    def test_add_rejects_oversized_step_response(self, project_dir, monkeypatch):
        from typer.testing import CliRunner

        from specify_cli import app
        from specify_cli.authentication import http as auth_http
        from specify_cli.workflows.step import command_add
        from specify_cli.workflows.step.catalog import StepCatalog

        monkeypatch.chdir(project_dir)
        monkeypatch.setattr(command_add, "_MAX_STEP_CATALOG_RESPONSE_BYTES", 100)
        monkeypatch.setattr(
            StepCatalog,
            "get_step_info",
            lambda self, step_id: {
                "id": step_id,
                "name": "Test Step",
                "url": "https://example.com/step.yml",
                "init_url": "https://example.com/__init__.py",
                "_install_allowed": True,
            },
        )

        class _FakeResponse:
            def __init__(self, url):
                self.url = url
                self.body = b"x" * 500
                self.offset = 0

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

            def getheader(self, name):
                return None

            def geturl(self):
                return self.url

            def read(self, size=-1):
                if size < 0:
                    size = len(self.body) - self.offset
                chunk = self.body[self.offset : self.offset + size]
                self.offset += len(chunk)
                return chunk

        monkeypatch.setattr(
            auth_http,
            "open_url",
            lambda url, timeout=30, redirect_validator=None: _FakeResponse(url),
        )

        result = CliRunner().invoke(
            app, ["workflow", "step", "add", "my-step"]
        )

        assert result.exit_code != 0
        assert (
            "steppackageresponse'exceedsmaximumsizeof100bytes"
            in "".join(result.output.split())
        )
        assert not (
            project_dir / ".specify" / "workflows" / "steps" / "my-step"
        ).exists()

    def test_catalog_temp_directory_creation_error_is_user_facing(
        self, project_dir, monkeypatch
    ):
        import tempfile

        from typer.testing import CliRunner

        from specify_cli import app
        from specify_cli.workflows.step.catalog import StepCatalog

        monkeypatch.chdir(project_dir)
        monkeypatch.setattr(
            StepCatalog,
            "get_step_info",
            lambda self, step_id: {
                "id": step_id,
                "name": "Test Step",
                "url": "https://example.com/step.yml",
                "init_url": "https://example.com/__init__.py",
                "_install_allowed": True,
            },
        )

        def _fail_tempdir(*args, **kwargs):
            raise OSError("temporary storage unavailable")

        monkeypatch.setattr(tempfile, "TemporaryDirectory", _fail_tempdir)
        result = CliRunner().invoke(
            app, ["workflow", "step", "add", "my-step"]
        )

        assert result.exit_code != 0
        assert result.exception is None or isinstance(result.exception, SystemExit)
        assert "Failed to create temporary step package directory" in result.output
        assert "temporarystorageunavailable" in "".join(result.output.split())

    def test_archive_temp_directory_creation_error_is_user_facing(
        self, project_dir, monkeypatch
    ):
        import tempfile
        import zipfile
        from io import BytesIO

        import typer
        from typer.testing import CliRunner

        from specify_cli import app
        from specify_cli.authentication import http as auth_http

        monkeypatch.chdir(project_dir)
        monkeypatch.setattr(typer, "confirm", lambda *args, **kwargs: True)
        real_tempdir = tempfile.TemporaryDirectory
        allocations = 0

        def _allocate_tempdir(*args, **kwargs):
            nonlocal allocations
            allocations += 1
            if allocations == 1:
                raise OSError("archive temp unavailable")
            return real_tempdir(*args, **kwargs)

        archive = BytesIO()
        with zipfile.ZipFile(archive, "w") as zf:
            for name, content in _valid_archive_files().items():
                zf.writestr(name, content)

        monkeypatch.setattr(tempfile, "TemporaryDirectory", _allocate_tempdir)
        monkeypatch.setattr(
            auth_http,
            "open_url",
            lambda url, timeout=30, extra_headers=None, redirect_validator=None: _ArchiveResponse(
                url, archive.getvalue(), "application/zip"
            ),
        )

        result = CliRunner().invoke(
            app,
            [
                "workflow",
                "step",
                "add",
                "my-step",
                "--from",
                "https://example.com/pkg.zip",
            ],
        )

        assert result.exit_code != 0
        assert result.exception is None or isinstance(result.exception, SystemExit)
        assert "Failed to create temporary step archive directory" in result.output
        assert "archivetempunavailable" in "".join(result.output.split())

    def test_archive_cleanup_failure_preserves_primary_install_error(
        self, project_dir, monkeypatch
    ):
        import tempfile
        import zipfile
        from io import BytesIO

        import typer
        from typer.testing import CliRunner

        from specify_cli import app
        from specify_cli.authentication import http as auth_http
        from specify_cli.workflows.step import installer

        monkeypatch.chdir(project_dir)
        monkeypatch.setattr(typer, "confirm", lambda *args, **kwargs: True)
        archive = BytesIO()
        with zipfile.ZipFile(archive, "w") as zf:
            for name, content in _valid_archive_files().items():
                zf.writestr(name, content)

        real_tempdir = tempfile.TemporaryDirectory
        extract_paths = []

        class _FailCleanupTempDir:
            def __init__(self, *args, **kwargs):
                self._inner = real_tempdir(*args, **kwargs)
                self.name = self._inner.name
                extract_paths.append(self.name)

            def cleanup(self):
                raise OSError("archive cleanup blocked")

        monkeypatch.setattr(tempfile, "TemporaryDirectory", _FailCleanupTempDir)
        monkeypatch.setattr(
            auth_http,
            "open_url",
            lambda url, timeout=30, redirect_validator=None, extra_headers=None: _ArchiveResponse(
                url, archive.getvalue(), "application/zip"
            ),
        )

        real_install = installer.install_step_package

        def _install_then_raise(*args, **kwargs):
            real_install(*args, **kwargs)
            raise installer.StepInstallError("primary archive install error")

        monkeypatch.setattr(installer, "install_step_package", _install_then_raise)
        result = CliRunner().invoke(
            app,
            [
                "workflow",
                "step",
                "add",
                "my-step",
                "--from",
                "https://example.com/pkg.zip",
            ],
        )

        assert result.exit_code != 0
        assert "primary archive install error" in result.output
        assert "Could not remove temporary step archive directory" in result.output
        assert extract_paths[0] in result.output
        import shutil

        for extract_path in extract_paths:
            shutil.rmtree(extract_path, ignore_errors=True)

    def test_catalog_cleanup_failure_adds_note_to_primary_error(
        self, project_dir, monkeypatch
    ):
        import tempfile

        from typer.testing import CliRunner

        from specify_cli import app
        from specify_cli.authentication import http as auth_http
        from specify_cli.workflows.step import installer
        from specify_cli.workflows.step.catalog import StepCatalog

        monkeypatch.chdir(project_dir)
        monkeypatch.setattr(
            StepCatalog,
            "get_step_info",
            lambda self, step_id: {
                "id": step_id,
                "name": "Test Step",
                "url": "https://example.com/step.yml",
                "init_url": "https://example.com/__init__.py",
                "_install_allowed": True,
            },
        )
        bodies = {
            "https://example.com/step.yml": b"step:\n  type_key: my-step\n",
            "https://example.com/__init__.py": b"# init\n",
        }

        class _Response:
            def __init__(self, url):
                self.url = url
                self.body = bodies[url]
                self.offset = 0

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def geturl(self):
                return self.url

            def read(self, size=-1):
                if size < 0:
                    size = len(self.body) - self.offset
                chunk = self.body[self.offset : self.offset + size]
                self.offset += len(chunk)
                return chunk

        monkeypatch.setattr(
            auth_http,
            "open_url",
            lambda url, timeout=30, redirect_validator=None: _Response(url),
        )
        real_tempdir = tempfile.TemporaryDirectory
        allocated = []

        class _FailCleanupTempDir:
            def __init__(self, *args, **kwargs):
                self._inner = real_tempdir(*args, **kwargs)
                self.name = self._inner.name
                allocated.append(self)

            def cleanup(self):
                raise OSError("catalog cleanup blocked")

        monkeypatch.setattr(tempfile, "TemporaryDirectory", _FailCleanupTempDir)

        real_install = installer.install_step_package

        def _install_then_raise(*args, **kwargs):
            real_install(*args, **kwargs)
            raise installer.StepInstallError("primary install error")

        monkeypatch.setattr(installer, "install_step_package", _install_then_raise)
        result = CliRunner().invoke(app, ["workflow", "step", "add", "my-step"])

        assert result.exit_code != 0
        assert "primary install error" in result.output
        assert "Could not remove temporary step package directory" in result.output
        assert allocated[0].name in result.output
        for item in allocated:
            import shutil

            shutil.rmtree(item.name, ignore_errors=True)

    @pytest.mark.parametrize(
        "step_yml_body", [b"[]", b"false", b"0", b"''", b"null", b"~", b"NULL"]
    )
    def test_add_rejects_falsy_non_mapping_step_yml(
        self, project_dir, monkeypatch, step_yml_body
    ):
        """A FALSY non-mapping step.yml document ([], false, 0, '') must be
        reported as "step.yml must be a YAML mapping", not silently coerced by
        ``or {}`` into {} and then misreported as the unrelated "missing
        'step.type_key'" error — matching how a TRUTHY non-mapping document
        (e.g. a bare string) already reports the mapping-shape error. An
        explicit null scalar (null/~/NULL) parses to the same ``None`` as a
        genuinely empty document, so it must be distinguished (via
        ``yaml.compose``) and rejected too, rather than defaulting to {}."""
        from typer.testing import CliRunner

        from specify_cli import app
        from specify_cli.authentication import http as auth_http
        from specify_cli.workflows.step.catalog import StepCatalog

        monkeypatch.chdir(project_dir)
        monkeypatch.setattr(
            StepCatalog,
            "get_step_info",
            lambda self, step_id: {
                "id": step_id,
                "name": "Test Step",
                "url": "https://example.com/step.yml",
                "init_url": "https://example.com/__init__.py",
                "_install_allowed": True,
            },
        )

        class _FakeResponse:
            def __init__(self, url):
                self.url = url
                self.body = step_yml_body if url.endswith("step.yml") else b""
                self.offset = 0

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

            def getheader(self, name):
                return None

            def geturl(self):
                return self.url

            def read(self, size=-1):
                if size < 0:
                    size = len(self.body) - self.offset
                chunk = self.body[self.offset : self.offset + size]
                self.offset += len(chunk)
                return chunk

        monkeypatch.setattr(
            auth_http,
            "open_url",
            lambda url, timeout=30, redirect_validator=None: _FakeResponse(url),
        )

        result = CliRunner().invoke(
            app, ["workflow", "step", "add", "my-step"]
        )

        assert result.exit_code != 0
        assert "step.yml must be a YAML mapping" in result.output
        assert not (
            project_dir / ".specify" / "workflows" / "steps" / "my-step"
        ).exists()

    @pytest.mark.parametrize(
        ("catalog_fields", "expected"),
        [
            ({"url": 123}, "malformed step.yml URL"),
            (
                {
                    "step_yml_url": [],
                    "url": "https://example.com/step.yml",
                },
                "malformed step.yml URL",
            ),
            (
                {
                    "url": "https://example.com/step.yml",
                    "init_url": 123,
                },
                "malformed __init__.py URL",
            ),
        ],
    )
    def test_add_rejects_non_string_required_urls_before_network(
        self, project_dir, monkeypatch, catalog_fields, expected
    ):
        from typer.testing import CliRunner

        from specify_cli import app
        from specify_cli.authentication import http as auth_http
        from specify_cli.workflows.step.catalog import StepCatalog

        monkeypatch.chdir(project_dir)
        monkeypatch.setattr(
            StepCatalog,
            "get_step_info",
            lambda self, step_id: {
                "id": step_id,
                "name": "Test Step",
                "_install_allowed": True,
                **catalog_fields,
            },
        )
        monkeypatch.setattr(
            auth_http,
            "open_url",
            lambda *args, **kwargs: (_ for _ in ()).throw(
                AssertionError("download should not start")
            ),
        )

        result = CliRunner().invoke(
            app, ["workflow", "step", "add", "my-step"]
        )

        assert result.exit_code != 0
        assert result.exception is None or isinstance(result.exception, SystemExit)
        assert expected in result.output
        assert not (
            project_dir / ".specify" / "workflows" / "steps" / "my-step"
        ).exists()

    @pytest.mark.parametrize(
        ("alias", "protected_name"),
        [
            ("./step.yml", "step.yml"),
            ("step.yml/", "step.yml"),
            ("STEP.YML", "step.yml"),
            (".\\step.yml", "step.yml"),
            ("./__init__.py", "__init__.py"),
            ("__init__.py/", "__init__.py"),
            ("__INIT__.PY", "__init__.py"),
            (".\\__init__.py", "__init__.py"),
        ],
    )
    def test_add_does_not_overwrite_required_files_through_path_aliases(
        self, project_dir, monkeypatch, alias, protected_name
    ):
        from typer.testing import CliRunner

        from specify_cli import app
        from specify_cli.authentication import http as auth_http
        from specify_cli.workflows.step.catalog import StepCatalog

        monkeypatch.chdir(project_dir)
        alias_url = "https://example.com/overwrite"
        monkeypatch.setattr(
            StepCatalog,
            "get_step_info",
            lambda self, step_id: {
                "id": step_id,
                "name": "Test Step",
                "url": "https://example.com/step.yml",
                "init_url": "https://example.com/__init__.py",
                "_install_allowed": True,
                "extra_files": {alias: alias_url},
            },
        )
        bodies = {
            "https://example.com/step.yml": b"step:\n  type_key: my-step\n",
            "https://example.com/__init__.py": b"# trusted init\n",
        }
        requested_urls: list[str] = []

        class _FakeResponse:
            def __init__(self, url):
                self.url = url
                self.body = bodies[url]
                self.offset = 0

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

            def geturl(self):
                return self.url

            def read(self, size=-1):
                if size < 0:
                    size = len(self.body) - self.offset
                chunk = self.body[self.offset : self.offset + size]
                self.offset += len(chunk)
                return chunk

        def fake_open_url(url, timeout=30, redirect_validator=None):
            requested_urls.append(url)
            return _FakeResponse(url)

        monkeypatch.setattr(auth_http, "open_url", fake_open_url)

        result = CliRunner().invoke(
            app, ["workflow", "step", "add", "my-step"]
        )

        assert result.exit_code == 0, result.output
        assert alias_url not in requested_urls
        installed_dir = (
            project_dir / ".specify" / "workflows" / "steps" / "my-step"
        )
        assert (installed_dir / protected_name).read_bytes() == bodies[
            f"https://example.com/{protected_name}"
        ]

    def test_add_rejects_too_many_package_files_before_network(
        self, project_dir, monkeypatch
    ):
        from typer.testing import CliRunner

        from specify_cli import app
        from specify_cli.authentication import http as auth_http
        from specify_cli.workflows.step import installer
        from specify_cli.workflows.step.catalog import StepCatalog

        monkeypatch.chdir(project_dir)
        monkeypatch.setattr(installer, "_MAX_STEP_PACKAGE_FILES", 3)
        monkeypatch.setattr(
            StepCatalog,
            "get_step_info",
            lambda self, step_id: {
                "id": step_id,
                "name": "Test Step",
                "url": "https://example.com/step.yml",
                "init_url": "https://example.com/__init__.py",
                "_install_allowed": True,
                "extra_files": {
                    "one.py": "https://example.com/one.py",
                    "two.py": "https://example.com/two.py",
                },
            },
        )
        monkeypatch.setattr(
            auth_http,
            "open_url",
            lambda *args, **kwargs: (_ for _ in ()).throw(
                AssertionError("download should not start")
            ),
        )

        result = CliRunner().invoke(
            app, ["workflow", "step", "add", "my-step"]
        )

        assert result.exit_code != 0
        assert result.exception is None or isinstance(result.exception, SystemExit)
        assert "exceeding the 3-entry limit" in result.output
        steps_dir = project_dir / ".specify" / "workflows" / "steps"
        assert not (steps_dir / "my-step").exists()
        assert list(steps_dir.glob("speckit_step_tmp_*")) == []

    def test_add_rejects_package_over_cumulative_size_and_cleans_staging(
        self, project_dir, monkeypatch
    ):
        from typer.testing import CliRunner

        from specify_cli import app
        from specify_cli.authentication import http as auth_http
        from specify_cli.workflows.step import installer
        from specify_cli.workflows.step.catalog import StepCatalog

        monkeypatch.chdir(project_dir)
        monkeypatch.setattr(installer, "_MAX_STEP_PACKAGE_BYTES", 40)
        monkeypatch.setattr(
            StepCatalog,
            "get_step_info",
            lambda self, step_id: {
                "id": step_id,
                "name": "Test Step",
                "url": "https://example.com/step.yml",
                "init_url": "https://example.com/__init__.py",
                "_install_allowed": True,
                "extra_files": {
                    "helper.py": "https://example.com/helper.py",
                },
            },
        )

        bodies = {
            "https://example.com/step.yml": b"step:\n  type_key: my-step\n",
            "https://example.com/__init__.py": b"# init\n",
            "https://example.com/helper.py": b"0123456789",
        }

        class _FakeResponse:
            def __init__(self, url):
                self.url = url
                self.body = bodies[url]
                self.offset = 0

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

            def getheader(self, name):
                return None

            def geturl(self):
                return self.url

            def read(self, size=-1):
                if size < 0:
                    size = len(self.body) - self.offset
                chunk = self.body[self.offset : self.offset + size]
                self.offset += len(chunk)
                return chunk

        monkeypatch.setattr(
            auth_http,
            "open_url",
            lambda url, timeout=30, redirect_validator=None: _FakeResponse(url),
        )

        result = CliRunner().invoke(
            app, ["workflow", "step", "add", "my-step"]
        )

        assert result.exit_code != 0
        assert result.exception is None or isinstance(result.exception, SystemExit)
        assert "40-byte total size limit" in result.output
        steps_dir = project_dir / ".specify" / "workflows" / "steps"
        assert not (steps_dir / "my-step").exists()
        assert list(steps_dir.glob("speckit_step_tmp_*")) == []

    def test_add_rejects_non_string_extra_files_key(self, project_dir, monkeypatch):
        from typer.testing import CliRunner

        from specify_cli import app
        from specify_cli.authentication import http as auth_http
        from specify_cli.workflows.step.catalog import StepCatalog

        monkeypatch.chdir(project_dir)

        def _fake_get_step_info(self, step_id):
            return {
                "id": step_id,
                "name": "Test Step",
                "url": "https://example.com/step.yml",
                "init_url": "https://example.com/__init__.py",
                "_install_allowed": True,
                "extra_files": {
                    123: "https://example.com/helper.py",
                },
            }

        class _FakeResponse:
            def __init__(self, url: str):
                self.url = url

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

            def read(self, size=-1):
                if getattr(self, "_read", False):
                    return b""
                self._read = True
                if self.url.endswith("/step.yml"):
                    return b"step:\n  type_key: my-step\n"
                return b""

            def geturl(self):
                return self.url

        def _fake_open_url(url, timeout=30, redirect_validator=None):
            return _FakeResponse(url)

        monkeypatch.setattr(StepCatalog, "get_step_info", _fake_get_step_info)
        monkeypatch.setattr(auth_http, "open_url", _fake_open_url)

        runner = CliRunner()
        result = runner.invoke(app, ["workflow", "step", "add", "my-step"])

        assert result.exit_code != 0
        assert "non-string path key" in result.output

    @pytest.mark.parametrize(
        "rel_path,expected",
        [
            ("", "empty or non-string path key"),
            (".", "not a valid relative file path"),
            ("..", "not a valid relative file path"),
            ("sub/../x", "not a valid relative file path"),
        ],
    )
    def test_add_rejects_invalid_extra_files_path(
        self, project_dir, monkeypatch, rel_path, expected
    ):
        from typer.testing import CliRunner

        from specify_cli import app
        from specify_cli.authentication import http as auth_http
        from specify_cli.workflows.step.catalog import StepCatalog

        monkeypatch.chdir(project_dir)

        def _fake_get_step_info(self, step_id):
            return {
                "id": step_id,
                "name": "Test Step",
                "url": "https://example.com/step.yml",
                "init_url": "https://example.com/__init__.py",
                "_install_allowed": True,
                "extra_files": {rel_path: "https://example.com/helper.py"},
            }

        class _FakeResponse:
            def __init__(self, url: str):
                self.url = url

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

            def read(self, size=-1):
                if getattr(self, "_read", False):
                    return b""
                self._read = True
                if self.url.endswith("/step.yml"):
                    return b"step:\n  type_key: my-step\n"
                return b""

            def geturl(self):
                return self.url

        def _fake_open_url(url, timeout=30, redirect_validator=None):
            return _FakeResponse(url)

        monkeypatch.setattr(StepCatalog, "get_step_info", _fake_get_step_info)
        monkeypatch.setattr(auth_http, "open_url", _fake_open_url)

        runner = CliRunner()
        result = runner.invoke(app, ["workflow", "step", "add", "my-step"])

        assert result.exit_code != 0
        assert expected in result.output

    def test_add_rejects_non_string_extra_files_url(self, project_dir, monkeypatch):
        from typer.testing import CliRunner

        from specify_cli import app
        from specify_cli.authentication import http as auth_http
        from specify_cli.workflows.step.catalog import StepCatalog

        monkeypatch.chdir(project_dir)

        def _fake_get_step_info(self, step_id):
            return {
                "id": step_id,
                "name": "Test Step",
                "url": "https://example.com/step.yml",
                "init_url": "https://example.com/__init__.py",
                "_install_allowed": True,
                "extra_files": {"helper.py": None},
            }

        class _FakeResponse:
            def __init__(self, url: str):
                self.url = url

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

            def read(self, size=-1):
                if getattr(self, "_read", False):
                    return b""
                self._read = True
                if self.url.endswith("/step.yml"):
                    return b"step:\n  type_key: my-step\n"
                return b""

            def geturl(self):
                return self.url

        def _fake_open_url(url, timeout=30, redirect_validator=None):
            return _FakeResponse(url)

        monkeypatch.setattr(StepCatalog, "get_step_info", _fake_get_step_info)
        monkeypatch.setattr(auth_http, "open_url", _fake_open_url)

        runner = CliRunner()
        result = runner.invoke(app, ["workflow", "step", "add", "my-step"])

        assert result.exit_code != 0
        assert "empty or non-string URL" in result.output


def _write_package(base, type_key="my-step", *, init_body="# init\n"):
    package_dir = base / f"{type_key}-pkg"
    package_dir.mkdir(parents=True, exist_ok=True)
    (package_dir / "step.yml").write_text(
        f"step:\n  type_key: {type_key}\n  name: My Step\n  version: 0.1.0\n",
        encoding="utf-8",
    )
    (package_dir / "__init__.py").write_text(init_body, encoding="utf-8")
    return package_dir


def _valid_init_body(type_key: str) -> str:
    return (
        "from specify_cli.workflows.base import StepBase, StepResult\n\n\n"
        "class CustomStep(StepBase):\n"
        f"    type_key = {type_key!r}\n\n"
        "    def execute(self, config, context):\n"
        "        return StepResult(output={'ok': True})\n"
    )


def _make_zip(files):
    import io
    import zipfile

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        for rel, body in files.items():
            data = body.encode("utf-8") if isinstance(body, str) else body
            archive.writestr(rel, data)
    return buffer.getvalue()


def _make_tar_gz(files):
    import io
    import tarfile

    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w:gz") as archive:
        for rel, body in files.items():
            data = body.encode("utf-8") if isinstance(body, str) else body
            info = tarfile.TarInfo(rel)
            info.size = len(data)
            archive.addfile(info, io.BytesIO(data))
    return buffer.getvalue()


class _ArchiveResponse:
    def __init__(self, url, body=b"", content_type=None):
        self.url = url
        self.body = body
        self.content_type = content_type
        self.offset = 0

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def getheader(self, name):
        if name.lower() == "content-type":
            return self.content_type
        return None

    def geturl(self):
        return self.url

    def read(self, size=-1):
        if size < 0:
            size = len(self.body) - self.offset
        chunk = self.body[self.offset : self.offset + size]
        self.offset += len(chunk)
        return chunk


def _valid_archive_files(type_key="my-step"):
    return {
        "step.yml": f"step:\n  type_key: {type_key}\n  name: My Step\n",
        "__init__.py": "# init\n",
    }


class TestWorkflowStepAddSources:
    def test_dev_installs_and_loads(self, project_dir, tmp_path, monkeypatch):
        from typer.testing import CliRunner

        from specify_cli import app
        from specify_cli.workflows import STEP_REGISTRY, load_custom_steps

        package = _write_package(
            tmp_path, type_key="dev-load-step", init_body=_valid_init_body("dev-load-step")
        )
        monkeypatch.chdir(project_dir)
        runner = CliRunner()
        result = runner.invoke(
            app, ["workflow", "step", "add", "dev-load-step", "--dev", str(package)]
        )

        assert result.exit_code == 0, result.output
        assert "installed" in result.output
        installed = project_dir / ".specify" / "workflows" / "steps" / "dev-load-step"
        assert (installed / "step.yml").is_file()

        loaded = load_custom_steps(project_dir)
        assert "dev-load-step" in loaded
        assert "dev-load-step" in STEP_REGISTRY

    def test_dev_install_list_and_remove(self, project_dir, tmp_path, monkeypatch):
        from typer.testing import CliRunner

        from specify_cli import app

        package = _write_package(tmp_path, type_key="dev-step")
        monkeypatch.chdir(project_dir)
        runner = CliRunner()
        assert (
            runner.invoke(
                app, ["workflow", "step", "add", "dev-step", "--dev", str(package)]
            ).exit_code
            == 0
        )

        listed = runner.invoke(app, ["workflow", "step", "list"])
        assert listed.exit_code == 0
        assert "dev-step" in listed.output

        removed = runner.invoke(app, ["workflow", "step", "remove", "dev-step"])
        assert removed.exit_code == 0
        assert not (
            project_dir / ".specify" / "workflows" / "steps" / "dev-step"
        ).exists()

    def test_dev_rejects_missing_init(self, project_dir, tmp_path, monkeypatch):
        from typer.testing import CliRunner

        from specify_cli import app

        package = _write_package(tmp_path, type_key="dev-step")
        (package / "__init__.py").unlink()
        monkeypatch.chdir(project_dir)

        result = CliRunner().invoke(
            app, ["workflow", "step", "add", "dev-step", "--dev", str(package)]
        )
        assert result.exit_code != 0
        assert "__init__.py" in result.output

    def test_dev_lock_failure_is_reported_once_without_installing(
        self, project_dir, tmp_path, monkeypatch
    ):
        from typer.testing import CliRunner

        from specify_cli import app

        package = _write_package(tmp_path, type_key="dev-step")
        monkeypatch.chdir(project_dir)
        # A directory at the lock path cannot be opened as the lock file.
        lock_path = project_dir / ".specify" / ".step-install.lock"
        if lock_path.exists():
            lock_path.unlink()
        lock_path.mkdir()

        result = CliRunner().invoke(
            app, ["workflow", "step", "add", "dev-step", "--dev", str(package)]
        )

        assert result.exit_code == 1, result.output
        output = result.output.replace("\n", "")
        assert "Failed to acquire the step lock" in output
        assert output.count("Failed to") == 1, output
        assert not (
            project_dir / ".specify" / "workflows" / "steps" / "dev-step"
        ).exists()

    def test_dev_rejects_symlinked_source_root(self, project_dir, tmp_path, monkeypatch):
        if not hasattr(os, "symlink"):
            pytest.skip("symlinks are unavailable")
        from typer.testing import CliRunner

        from specify_cli import app

        package = _write_package(tmp_path, type_key="dev-step")
        link = tmp_path / "linked"
        link.symlink_to(package, target_is_directory=True)
        monkeypatch.chdir(project_dir)

        result = CliRunner().invoke(
            app, ["workflow", "step", "add", "dev-step", "--dev", str(link)]
        )
        assert result.exit_code != 0
        assert "symlink" in result.output.lower()

    def test_dev_and_from_are_mutually_exclusive(self, project_dir, monkeypatch):
        from typer.testing import CliRunner

        from specify_cli import app

        monkeypatch.chdir(project_dir)
        result = CliRunner().invoke(
            app,
            [
                "workflow",
                "step",
                "add",
                "dev-step",
                "--dev",
                "somewhere",
                "--from",
                "https://example.com/pkg.zip",
            ],
        )
        assert result.exit_code != 0
        assert "mutually exclusive" in result.output

    @pytest.mark.parametrize("option", ["--dev", "--from"])
    def test_empty_source_value_rejected(self, project_dir, monkeypatch, option):
        from typer.testing import CliRunner

        from specify_cli import app

        monkeypatch.chdir(project_dir)
        result = CliRunner().invoke(
            app, ["workflow", "step", "add", "dev-step", option, "   "]
        )
        assert result.exit_code != 0

    def test_force_replaces_installed_package(self, project_dir, tmp_path, monkeypatch):
        from typer.testing import CliRunner

        from specify_cli import app

        package = _write_package(tmp_path, type_key="dev-step", init_body="# old\n")
        monkeypatch.chdir(project_dir)
        runner = CliRunner()
        assert (
            runner.invoke(
                app, ["workflow", "step", "add", "dev-step", "--dev", str(package)]
            ).exit_code
            == 0
        )

        # A second install without --force is rejected.
        duplicate = runner.invoke(
            app, ["workflow", "step", "add", "dev-step", "--dev", str(package)]
        )
        assert duplicate.exit_code != 0
        assert "already installed" in duplicate.output

        (package / "__init__.py").write_text("# new\n", encoding="utf-8")
        forced = runner.invoke(
            app,
            ["workflow", "step", "add", "dev-step", "--dev", str(package), "--force"],
        )
        assert forced.exit_code == 0, forced.output
        installed = (
            project_dir / ".specify" / "workflows" / "steps" / "dev-step" / "__init__.py"
        )
        assert installed.read_text(encoding="utf-8") == "# new\n"

    def test_force_replaces_orphaned_directory(self, project_dir, tmp_path, monkeypatch):
        from typer.testing import CliRunner

        from specify_cli import app

        orphan = (
            project_dir / ".specify" / "workflows" / "steps" / "dev-step"
        )
        orphan.mkdir(parents=True)
        (orphan / "step.yml").write_text("step:\n  type_key: dev-step\n", encoding="utf-8")
        (orphan / "__init__.py").write_text("# old\n", encoding="utf-8")

        package = _write_package(tmp_path, type_key="dev-step", init_body="# new\n")
        monkeypatch.chdir(project_dir)

        result = CliRunner().invoke(
            app,
            ["workflow", "step", "add", "dev-step", "--dev", str(package), "--force"],
        )
        assert result.exit_code == 0, result.output
        assert (orphan / "__init__.py").read_text(encoding="utf-8") == "# new\n"

    def test_from_denied_confirmation_issues_no_request(
        self, project_dir, monkeypatch
    ):
        import typer
        from typer.testing import CliRunner

        from specify_cli import app
        from specify_cli.authentication import http as auth_http

        monkeypatch.chdir(project_dir)
        monkeypatch.setattr(typer, "confirm", lambda *a, **k: False)
        monkeypatch.setattr(
            auth_http,
            "open_url",
            lambda *a, **k: (_ for _ in ()).throw(
                AssertionError("network request must not be issued")
            ),
        )

        result = CliRunner().invoke(
            app,
            [
                "workflow",
                "step",
                "add",
                "dev-step",
                "--from",
                "https://example.com/pkg.zip",
            ],
        )
        assert result.exit_code == 0
        assert "Cancelled" in result.output
        assert not (
            project_dir / ".specify" / "workflows" / "steps" / "dev-step"
        ).exists()

    @pytest.mark.parametrize(
        ("url", "body_factory", "content_type"),
        [
            ("https://example.com/pkg.zip", _make_zip, "application/zip"),
            ("https://example.com/pkg.tar.gz", _make_tar_gz, "application/gzip"),
        ],
    )
    def test_from_archive_installs(
        self, project_dir, monkeypatch, url, body_factory, content_type
    ):
        import typer
        from typer.testing import CliRunner

        from specify_cli import app
        from specify_cli.authentication import http as auth_http

        monkeypatch.chdir(project_dir)
        monkeypatch.setattr(typer, "confirm", lambda *a, **k: True)
        body = body_factory(_valid_archive_files())
        monkeypatch.setattr(
            auth_http,
            "open_url",
            lambda url, timeout=30, redirect_validator=None, extra_headers=None: (
                _ArchiveResponse(url, body, content_type)
            ),
        )

        result = CliRunner().invoke(
            app, ["workflow", "step", "add", "my-step", "--from", url]
        )
        assert result.exit_code == 0, result.output
        assert (
            project_dir / ".specify" / "workflows" / "steps" / "my-step" / "step.yml"
        ).is_file()

    def test_from_github_api_asset_detects_archive_from_bytes(
        self, project_dir, monkeypatch
    ):
        import typer
        from typer.testing import CliRunner

        from specify_cli import app
        from specify_cli.authentication import http as auth_http

        monkeypatch.chdir(project_dir)
        monkeypatch.setattr(typer, "confirm", lambda *a, **k: True)
        api_asset_url = (
            "https://api.github.com/repos/example/project/releases/assets/123"
        )
        body = _make_zip(_valid_archive_files())
        monkeypatch.setattr(
            auth_http,
            "open_url",
            lambda url, timeout=30, redirect_validator=None, extra_headers=None: (
                _ArchiveResponse(url, body, "application/octet-stream")
            ),
        )

        result = CliRunner().invoke(
            app, ["workflow", "step", "add", "my-step", "--from", api_asset_url]
        )

        assert result.exit_code == 0, result.output
        assert (
            project_dir / ".specify" / "workflows" / "steps" / "my-step" / "step.yml"
        ).is_file()

    def test_install_error_escapes_rich_markup_from_step_metadata(
        self, project_dir, tmp_path, monkeypatch
    ):
        from typer.testing import CliRunner

        from specify_cli import app

        package = _write_package(tmp_path, type_key="my-step")
        (package / "step.yml").write_text(
            "step:\n  type_key: '[/]'\n", encoding="utf-8"
        )
        monkeypatch.chdir(project_dir)

        result = CliRunner().invoke(
            app,
            ["workflow", "step", "add", "my-step", "--dev", str(package)],
        )

        assert result.exit_code != 0
        assert "does not match" in result.output
        assert "MarkupError" not in result.output
        assert "Traceback" not in result.output

    def test_archive_temp_directory_cleanup_failure_warns_after_commit(
        self, project_dir, monkeypatch
    ):
        import tempfile

        import typer
        from typer.testing import CliRunner

        from specify_cli import app
        from specify_cli.authentication import http as auth_http

        monkeypatch.chdir(project_dir)
        monkeypatch.setattr(typer, "confirm", lambda *args, **kwargs: True)

        real_tempdir = tempfile.TemporaryDirectory
        extract_paths: list[str] = []

        class _FailCleanupTempDir:
            def __init__(self, *args, **kwargs):
                self._inner = real_tempdir(*args, **kwargs)
                self.name = self._inner.name
                extract_paths.append(self.name)

            def cleanup(self):
                raise OSError("archive cleanup blocked")

        monkeypatch.setattr(tempfile, "TemporaryDirectory", _FailCleanupTempDir)
        monkeypatch.setattr(
            auth_http,
            "open_url",
            lambda url, timeout=30, redirect_validator=None, extra_headers=None: (
                _ArchiveResponse(
                    url,
                    _make_zip(_valid_archive_files()),
                    "application/zip",
                )
            ),
        )

        result = CliRunner().invoke(
            app,
            [
                "workflow",
                "step",
                "add",
                "my-step",
                "--from",
                "https://example.com/pkg.zip",
            ],
        )

        assert result.exit_code == 0, result.output
        assert "installed" in result.output
        assert "Could not remove temporary step archive directory" in result.output
        assert extract_paths[0] in result.output
        assert (
            project_dir / ".specify" / "workflows" / "steps" / "my-step" / "step.yml"
        ).is_file()
        for path in extract_paths:
            import shutil

            shutil.rmtree(path, ignore_errors=True)

    def test_from_rejects_non_https(self, project_dir, monkeypatch):
        from typer.testing import CliRunner

        from specify_cli import app

        monkeypatch.chdir(project_dir)
        result = CliRunner().invoke(
            app,
            [
                "workflow",
                "step",
                "add",
                "my-step",
                "--from",
                "http://example.com/pkg.zip",
            ],
        )
        assert result.exit_code != 0
        assert "HTTPS" in result.output

    def test_from_rejects_malformed_url(self, project_dir, monkeypatch):
        from typer.testing import CliRunner

        from specify_cli import app

        monkeypatch.chdir(project_dir)
        result = CliRunner().invoke(
            app,
            [
                "workflow",
                "step",
                "add",
                "my-step",
                "--from",
                "https://[not-an-ip]/pkg.zip",
            ],
        )
        assert result.exit_code != 0
        assert "Invalid URL" in result.output

    def test_from_rejects_redirect_to_non_https(self, project_dir, monkeypatch):
        import typer
        from typer.testing import CliRunner

        from specify_cli import app
        from specify_cli.authentication import http as auth_http

        monkeypatch.chdir(project_dir)
        monkeypatch.setattr(typer, "confirm", lambda *a, **k: True)
        monkeypatch.setattr(
            auth_http,
            "open_url",
            lambda url, timeout=30, redirect_validator=None, extra_headers=None: (
                _ArchiveResponse("http://evil.example.com/pkg.zip", b"", "application/zip")
            ),
        )

        result = CliRunner().invoke(
            app,
            [
                "workflow",
                "step",
                "add",
                "my-step",
                "--from",
                "https://example.com/pkg.zip",
            ],
        )
        assert result.exit_code != 0
        assert "non-HTTPS" in result.output

    def test_from_rejects_non_archive_body(self, project_dir, monkeypatch):
        import typer
        from typer.testing import CliRunner

        from specify_cli import app
        from specify_cli.authentication import http as auth_http

        monkeypatch.chdir(project_dir)
        monkeypatch.setattr(typer, "confirm", lambda *a, **k: True)
        monkeypatch.setattr(
            auth_http,
            "open_url",
            lambda url, timeout=30, redirect_validator=None, extra_headers=None: (
                _ArchiveResponse(url, b"step:\n  type_key: my-step\n", "text/yaml")
            ),
        )

        result = CliRunner().invoke(
            app,
            [
                "workflow",
                "step",
                "add",
                "my-step",
                "--from",
                "https://example.com/step.yml",
            ],
        )
        assert result.exit_code != 0
        assert "supported archive" in result.output

    def test_from_rejects_archive_with_unrelated_siblings(
        self, project_dir, monkeypatch
    ):
        import typer
        from typer.testing import CliRunner

        from specify_cli import app
        from specify_cli.authentication import http as auth_http

        files = {
            "inner/step.yml": "step:\n  type_key: my-step\n",
            "inner/__init__.py": "# init\n",
            "README.md": "readme\n",
        }
        body = _make_zip(files)
        monkeypatch.chdir(project_dir)
        monkeypatch.setattr(typer, "confirm", lambda *a, **k: True)
        monkeypatch.setattr(
            auth_http,
            "open_url",
            lambda url, timeout=30, redirect_validator=None, extra_headers=None: (
                _ArchiveResponse(url, body, "application/zip")
            ),
        )

        result = CliRunner().invoke(
            app,
            [
                "workflow",
                "step",
                "add",
                "my-step",
                "--from",
                "https://example.com/pkg.zip",
            ],
        )
        assert result.exit_code != 0
        assert "exactly one top-level" in result.output

    def test_from_rejects_original_url_format_mismatch_after_redirect(
        self, project_dir, monkeypatch
    ):
        import typer
        from typer.testing import CliRunner

        from specify_cli import app
        from specify_cli.authentication import http as auth_http

        monkeypatch.chdir(project_dir)
        monkeypatch.setattr(typer, "confirm", lambda *a, **k: True)
        body = _make_tar_gz(_valid_archive_files())
        monkeypatch.setattr(
            auth_http,
            "open_url",
            lambda url, timeout=30, redirect_validator=None, extra_headers=None: (
                _ArchiveResponse("https://example.com/download", body, None)
            ),
        )

        result = CliRunner().invoke(
            app, ["workflow", "step", "add", "my-step", "--from", "https://example.com/pkg.zip"]
        )

        assert result.exit_code != 0
        assert "Archive format mismatch" in result.output

    def test_from_escapes_installed_name(self, project_dir, monkeypatch):
        import typer
        from typer.testing import CliRunner

        from specify_cli import app
        from specify_cli.authentication import http as auth_http

        monkeypatch.chdir(project_dir)
        monkeypatch.setattr(typer, "confirm", lambda *a, **k: True)
        body = _make_zip(
            {
                "step.yml": "step:\n  type_key: my-step\n  name: '[/]'\n",
                "__init__.py": "# init\n",
            }
        )
        monkeypatch.setattr(
            auth_http,
            "open_url",
            lambda url, timeout=30, redirect_validator=None, extra_headers=None: (
                _ArchiveResponse(url, body, "application/zip")
            ),
        )

        result = CliRunner().invoke(
            app, ["workflow", "step", "add", "my-step", "--from", "https://example.com/pkg.zip"]
        )

        assert result.exit_code == 0, result.output
        assert "[/]" in result.output

    def test_from_denied_when_already_installed_errors_before_prompt(
        self, project_dir, tmp_path, monkeypatch
    ):
        import typer
        from typer.testing import CliRunner

        from specify_cli import app

        package = _write_package(tmp_path, type_key="my-step")
        monkeypatch.chdir(project_dir)
        runner = CliRunner()
        assert (
            runner.invoke(
                app, ["workflow", "step", "add", "my-step", "--dev", str(package)]
            ).exit_code
            == 0
        )

        prompts = []
        monkeypatch.setattr(
            typer, "confirm", lambda *a, **k: prompts.append(True) or True
        )
        result = runner.invoke(
            app,
            [
                "workflow",
                "step",
                "add",
                "my-step",
                "--from",
                "https://example.com/pkg.zip",
            ],
        )
        assert result.exit_code != 0
        assert "already installed" in result.output
        assert prompts == []

    def test_direct_python_call_uses_plain_defaults(self, project_dir, monkeypatch):
        """The bundle delegate calls ``workflow_step_add(component.id)``."""
        import typer

        from specify_cli import workflow_step_add
        from specify_cli.workflows.step.catalog import StepCatalog

        monkeypatch.chdir(project_dir)
        monkeypatch.setattr(
            StepCatalog, "get_step_info", lambda self, step_id: None
        )

        # A bare positional call must not raise a TypeError from leaking
        # typer.Option metadata; it enters catalog mode and exits cleanly.
        with pytest.raises(typer.Exit):
            workflow_step_add("my-step")


class TestWorkflowStepAddEndToEnd:
    _WORKFLOW_YAML = """
schema_version: "1.0"
workflow:
  id: "custom-step-wf"
  name: "Custom Step Workflow"
  version: "1.0.0"
steps:
  - id: run-custom
    type: dev-step
"""

    _INIT_BODY = """
from specify_cli.workflows.base import StepBase, StepResult


class DevStep(StepBase):
    type_key = "dev-step"

    def execute(self, config, context):
        return StepResult(output={"ok": True})
"""

    def test_dev_install_loads_runs_and_removes(
        self, project_dir, tmp_path, monkeypatch
    ):
        from typer.testing import CliRunner

        from specify_cli import app
        from specify_cli.workflows import load_custom_steps

        package = _write_package(tmp_path, type_key="dev-step", init_body=self._INIT_BODY)
        monkeypatch.chdir(project_dir)
        runner = CliRunner()

        installed = runner.invoke(
            app, ["workflow", "step", "add", "dev-step", "--dev", str(package)]
        )
        assert installed.exit_code == 0, installed.output

        assert "dev-step" in load_custom_steps(project_dir)

        workflow_file = tmp_path / "custom-step-wf.yml"
        workflow_file.write_text(self._WORKFLOW_YAML, encoding="utf-8")
        run = runner.invoke(app, ["workflow", "run", str(workflow_file), "--json"])
        assert run.exit_code == 0, run.output
        assert "completed" in run.output

        removed = runner.invoke(app, ["workflow", "step", "remove", "dev-step"])
        assert removed.exit_code == 0
class TestVersionedStepAdd:
    @staticmethod
    def _setup(project_dir, monkeypatch, *, discovery=False, corrupt=None):
        from specify_cli.authentication import http as auth_http
        from specify_cli.workflows.step.catalog import StepCatalog

        monkeypatch.chdir(project_dir)
        base = "https://example.com/old/"
        bodies = {
            base + "step.yml": b"step:\n  type_key: deploy\n  version: '1.0'\n",
            base + "__init__.py": b"# example\n",
            base + "helper.py": b"# helper\n",
        }
        hashes = {
            name: hashlib.sha256(bodies[base + name]).hexdigest()
            for name in ("step.yml", "__init__.py", "helper.py")
        }
        entry = {
            "id": "deploy",
            "name": "Deploy",
            "version": "2.0",
            "step_yml_url": "https://example.com/current/step.yml",
            "_install_allowed": not discovery,
            "releases": {
                "1.0": {
                    "step_yml_url": base + "step.yml",
                    "init_url": base + "__init__.py",
                    "extra_files": {"helper.py": base + "helper.py"},
                    "sha256": hashes,
                }
            },
        }
        if corrupt == "checksum":
            bodies[base + "helper.py"] = b"changed"
        elif corrupt == "version":
            bodies[base + "step.yml"] = b"step:\n  type_key: deploy\n  version: '2.0'\n"
            hashes["step.yml"] = hashlib.sha256(bodies[base + "step.yml"]).hexdigest()
        elif corrupt == "id":
            bodies[base + "step.yml"] = b"step:\n  type_key: other\n  version: '1.0'\n"
            hashes["step.yml"] = hashlib.sha256(bodies[base + "step.yml"]).hexdigest()
        elif corrupt == "url":
            entry["releases"]["1.0"]["init_url"] = "http://evil.example/__init__.py"
        monkeypatch.setattr(
            StepCatalog, "_get_merged_steps", lambda self: {"deploy": entry}
        )
        requested = []

        class Response:
            def __init__(self, url):
                self.url = url
                self.content = bodies[url]
                self.offset = 0

            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return False

            def geturl(self):
                return self.url

            def getheader(self, _name):
                return None

            def read(self, size=-1):
                if size < 0:
                    size = len(self.content)
                chunk = self.content[self.offset:self.offset + size]
                self.offset += len(chunk)
                return chunk

        def open_url(url, **_kwargs):
            requested.append(url)
            return Response(url)

        monkeypatch.setattr(auth_http, "open_url", open_url)
        return requested

    def test_install_exact_selected_files(self, project_dir, monkeypatch):
        from typer.testing import CliRunner

        from specify_cli import app
        from specify_cli.workflows.step.catalog import StepRegistry

        requested = self._setup(project_dir, monkeypatch)
        result = CliRunner().invoke(
            app, ["workflow", "step", "add", "deploy", "--version", "v1.0"]
        )
        assert result.exit_code == 0, result.output
        assert requested == [
            f"https://example.com/old/{name}"
            for name in ("step.yml", "__init__.py", "helper.py")
        ]
        assert StepRegistry(project_dir).get("deploy")["version"] == "1.0"
        assert (
            project_dir / ".specify/workflows/steps/deploy/helper.py"
        ).read_bytes() == b"# helper\n"

    def test_preselected_step_installs_without_reloading_catalog(
        self, project_dir, monkeypatch,
    ):
        from specify_cli.workflows.step.catalog import StepCatalog, StepRegistry
        from specify_cli.workflows.step.command_add import _install_preselected_step

        requested = self._setup(project_dir, monkeypatch)
        selected = StepCatalog(project_dir).get_step_info("deploy", version="1.0")
        monkeypatch.setattr(
            StepCatalog, "get_step_info",
            lambda *args, **kwargs: pytest.fail("catalog was re-resolved"),
        )
        monkeypatch.chdir(project_dir)
        _install_preselected_step("deploy", version="1.0", selected_info=selected)

        assert requested == [
            f"https://example.com/old/{name}"
            for name in ("step.yml", "__init__.py", "helper.py")
        ]
        assert StepRegistry(project_dir).get("deploy")["version"] == "1.0"

    def test_preselected_step_rejects_bad_digest_without_reloading_catalog(
        self, project_dir, monkeypatch,
    ):
        from specify_cli.workflows.step.catalog import StepCatalog, StepRegistry
        from specify_cli.workflows.step.command_add import _install_preselected_step
        from specify_cli.workflows.step.installer import StepInstallError

        self._setup(project_dir, monkeypatch, corrupt="checksum")
        selected = StepCatalog(project_dir).get_step_info("deploy", version="1.0")
        monkeypatch.setattr(
            StepCatalog, "get_step_info",
            lambda *args, **kwargs: pytest.fail("catalog was re-resolved"),
        )
        monkeypatch.chdir(project_dir)

        with pytest.raises(StepInstallError, match="checksum mismatch"):
            _install_preselected_step(
                "deploy", version="1.0", selected_info=selected,
            )
        assert not StepRegistry(project_dir).is_installed("deploy")

    @pytest.mark.parametrize(
        ("corrupt", "error"),
        [
            ("checksum", "checksum mismatch"),
            ("version", "does not match catalog version"),
            ("id", "does not match step ID"),
            ("url", "non-HTTPS"),
        ],
    )
    def test_rejects_bad_selected_release(
        self, project_dir, monkeypatch, corrupt, error
    ):
        from typer.testing import CliRunner

        from specify_cli import app
        from specify_cli.workflows.step.catalog import StepRegistry

        self._setup(project_dir, monkeypatch, corrupt=corrupt)
        result = CliRunner().invoke(
            app, ["workflow", "step", "add", "deploy", "--version", "1.0"]
        )
        assert result.exit_code == 1, result.output
        assert error in result.output
        assert not StepRegistry(project_dir).is_installed("deploy")
        assert not (project_dir / ".specify/workflows/steps/deploy").exists()

    @pytest.mark.parametrize(
        ("discovery", "version", "error"),
        [
            (False, "0.9", "not found in the winning catalog"),
            (True, "1.0", "discovery-only catalog"),
        ],
    )
    def test_no_fallback_or_discovery_install(
        self, project_dir, monkeypatch, discovery, version, error
    ):
        from typer.testing import CliRunner

        from specify_cli import app

        requested = self._setup(project_dir, monkeypatch, discovery=discovery)
        result = CliRunner().invoke(
            app, ["workflow", "step", "add", "deploy", "--version", version]
        )
        assert result.exit_code == 1, result.output
        assert error in result.output
        assert requested == []

    def test_current_explicit_selection_requires_digests(
        self, project_dir, monkeypatch
    ):
        from typer.testing import CliRunner

        from specify_cli import app

        requested = self._setup(project_dir, monkeypatch)
        result = CliRunner().invoke(
            app, ["workflow", "step", "add", "deploy", "--version", "2.0"]
        )
        assert result.exit_code == 1, result.output
        assert "SHA-256 digests" in result.output
        assert requested == []

    def test_rejects_insecure_redirect_before_following_it(
        self, project_dir, monkeypatch
    ):
        from typer.testing import CliRunner

        from specify_cli import app
        from specify_cli.authentication import http as auth_http

        self._setup(project_dir, monkeypatch)

        def redirect(url, *, redirect_validator, **_kwargs):
            redirect_validator(url, "http://evil.example/step.yml")
            raise AssertionError("redirect should have been refused")

        monkeypatch.setattr(auth_http, "open_url", redirect)
        result = CliRunner().invoke(
            app, ["workflow", "step", "add", "deploy", "--version", "1.0"]
        )
        assert result.exit_code == 1, result.output
        assert "redirect target must use HTTPS" in " ".join(result.output.split())
        assert not (project_dir / ".specify/workflows/steps/deploy").exists()

    @pytest.mark.parametrize("source_option", ["--dev", "--from"])
    def test_version_rejected_with_direct_source_before_network(
        self, project_dir, monkeypatch, source_option
    ):
        from typer.testing import CliRunner

        from specify_cli import app
        from specify_cli.authentication import http as auth_http

        monkeypatch.chdir(project_dir)
        monkeypatch.setattr(
            auth_http, "open_url",
            lambda *args, **kwargs: pytest.fail("direct source must not download"),
        )
        result = CliRunner().invoke(
            app,
            [
                "workflow", "step", "add", "deploy",
                source_option, "https://example.com/deploy.zip",
                "--version", "1.0",
            ],
        )
        assert result.exit_code == 1, result.output
        assert "--version requires a catalog step ID" in result.output
