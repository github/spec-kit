"""Command-focused workflow tests."""

from __future__ import annotations

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

    def test_add_rejects_oversized_step_response(self, project_dir, monkeypatch):
        from typer.testing import CliRunner
        from specify_cli import app
        from specify_cli.workflows import _commands as wf_commands
        from specify_cli.workflows.step.catalog import StepCatalog
        from specify_cli.authentication import http as auth_http

        monkeypatch.chdir(project_dir)
        monkeypatch.setattr(wf_commands, "_MAX_WORKFLOW_YAML_BYTES", 100)
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
            "responseexceedsthe100-byteworkflowsizelimit"
            in "".join(result.output.split())
        )
        assert not (
            project_dir / ".specify" / "workflows" / "steps" / "my-step"
        ).exists()

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
        from specify_cli.workflows.step.catalog import StepCatalog
        from specify_cli.authentication import http as auth_http

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
        from specify_cli.workflows.step import _helpers as step_helpers
        from specify_cli.workflows.step.catalog import StepCatalog

        monkeypatch.chdir(project_dir)
        monkeypatch.setattr(step_helpers, "_MAX_STEP_PACKAGE_FILES", 3)
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
        assert "exceeding the 3-file limit" in result.output
        steps_dir = project_dir / ".specify" / "workflows" / "steps"
        assert not (steps_dir / "my-step").exists()
        assert list(steps_dir.glob("speckit_step_tmp_*")) == []

    def test_add_rejects_package_over_cumulative_size_and_cleans_staging(
        self, project_dir, monkeypatch
    ):
        from typer.testing import CliRunner

        from specify_cli import app
        from specify_cli.authentication import http as auth_http
        from specify_cli.workflows.step import _helpers as step_helpers
        from specify_cli.workflows.step.catalog import StepCatalog

        monkeypatch.chdir(project_dir)
        monkeypatch.setattr(step_helpers, "_MAX_STEP_PACKAGE_BYTES", 40)
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
        from specify_cli.workflows.step.catalog import StepCatalog
        from specify_cli.authentication import http as auth_http

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
        from specify_cli.workflows.step.catalog import StepCatalog
        from specify_cli.authentication import http as auth_http

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
        from specify_cli.workflows.step.catalog import StepCatalog
        from specify_cli.authentication import http as auth_http

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
