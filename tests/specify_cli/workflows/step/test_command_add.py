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
