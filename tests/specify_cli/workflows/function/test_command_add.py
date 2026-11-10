"""``specify workflow function add``."""

from __future__ import annotations

import os
import zipfile

import pytest
from typer.testing import CliRunner

from specify_cli import app
from specify_cli.workflows.function import FunctionRegistry

from .helpers import (
    TRIM_CODE,
    install_dir,
    serve_files,
    write_installed,
    write_package,
    zip_package,
)


@pytest.fixture
def cli(project_dir, monkeypatch):
    monkeypatch.chdir(project_dir)
    runner = CliRunner()
    return lambda *args, **kw: runner.invoke(app, ["workflow", "function", *args], **kw)


@pytest.fixture
def source(tmp_path):
    return write_package(tmp_path / "src", "text")


class TestDevSource:
    def test_installs_from_a_local_directory(self, cli, project_dir, source):
        result = cli("add", "text", "--dev", str(source))
        assert result.exit_code == 0, result.output
        assert "Workflow function package 'text' installed" in result.output
        assert (install_dir(project_dir, "text") / "__init__.py").read_text() == TRIM_CODE
        assert FunctionRegistry(project_dir).get("text")["source"] == "local"

    def test_does_not_import_the_package(self, cli, tmp_path, source):
        marker = tmp_path / "imported"
        write_package(source, "text", code=f"open({str(marker)!r}, 'w').close()\ndef trim(v):\n    return v\n")
        assert cli("add", "text", "--dev", str(source)).exit_code == 0
        assert not marker.exists()

    def test_exactly_one_source_is_required(self, cli, project_dir, source):
        none = cli("add", "text")
        both = cli("add", "text", "--dev", str(source), "--from", "https://example.com/p.zip")
        for result in (none, both):
            assert result.exit_code == 1
            assert "exactly one of --dev or --from is required" in result.output
        assert not install_dir(project_dir, "text").exists()

    def test_missing_id_argument(self, cli, source):
        assert cli("add", "--dev", str(source)).exit_code == 2

    @pytest.mark.parametrize("kind", ["missing", "file"])
    def test_dev_source_must_be_a_directory(self, cli, tmp_path, kind):
        path = tmp_path / "nothing"
        if kind == "file":
            path.write_text("x")
        result = cli("add", "text", "--dev", str(path))
        assert result.exit_code == 1 and "--dev source must be a directory" in result.output

    @pytest.mark.skipif(not hasattr(os, "symlink"), reason="symlinks are unavailable")
    def test_symlinked_dev_source_is_refused(self, cli, tmp_path, source):
        link = tmp_path / "link"
        link.symlink_to(source, target_is_directory=True)
        result = cli("add", "text", "--dev", str(link))
        assert result.exit_code == 1 and "--dev source must be a directory" in result.output

    def test_existing_package_needs_force(self, cli, project_dir, source):
        assert cli("add", "text", "--dev", str(source)).exit_code == 0
        again = cli("add", "text", "--dev", str(source))
        assert again.exit_code == 1 and "already installed" in again.output
        forced = cli("add", "text", "--dev", str(source), "--force")
        assert forced.exit_code == 0, forced.output

    def test_collision_with_builtin_is_reported(self, cli, project_dir, source):
        write_package(source, "text", [{"name": "upper", "handler": "trim"}])
        result = cli("add", "text", "--dev", str(source))
        assert result.exit_code == 1 and "built-in filter" in result.output
        assert not install_dir(project_dir, "text").exists()

    def test_invalid_id_is_reported(self, cli, source):
        result = cli("add", ".cache", "--dev", str(source))
        assert result.exit_code == 1 and "Invalid function id" in result.output

    def test_oversized_max_args_is_rejected_and_nothing_is_installed(self, cli, project_dir, source):
        (source / "function.yml").write_text(
            "id: text\nfunctions:\n  - {name: trim, handler: trim, max_args: 100000000}\n"
        )
        result = cli("add", "text", "--dev", str(source))
        assert result.exit_code == 1 and "argument bounds" in result.output
        assert not FunctionRegistry(project_dir).is_installed("text")
        assert not install_dir(project_dir, "text").exists()

    @pytest.mark.parametrize("extra", ["1: x", "1: x\nb: y"])
    def test_non_string_manifest_key_is_an_error_not_a_traceback(
        self, cli, project_dir, source, extra
    ):
        (source / "function.yml").write_text(
            f"id: text\n{extra}\nfunctions: [{{name: trim, handler: trim}}]\n"
        )
        result = cli("add", "text", "--dev", str(source))
        assert result.exit_code == 1 and "unknown key(s)" in result.output
        assert "Traceback" not in result.output and not isinstance(result.exception, TypeError)
        assert not FunctionRegistry(project_dir).is_installed("text")

    def test_error_text_is_rendered_literally(self, cli, source):
        (source / "function.yml").write_text("id: text\nfunctions: [[red]x]\n")
        result = cli("add", "text", "--dev", str(source))
        assert result.exit_code == 1 and "Error:" in result.output

    def test_requires_a_specify_project(self, tmp_path, monkeypatch, source):
        bare = tmp_path / "bare"
        bare.mkdir()
        monkeypatch.chdir(bare)
        result = CliRunner().invoke(
            app, ["workflow", "function", "add", "text", "--dev", str(source)]
        )
        assert result.exit_code != 0
        assert not (bare / ".specify").exists()


class TestUrlSource:
    def test_confirmed_install_from_archive_root(self, cli, project_dir, source):
        with serve_files({"text.zip": zip_package(source)}) as url:
            result = cli("add", "text", "--from", url("text.zip"), input="y\n")
        assert result.exit_code == 0, result.output
        assert "Untrusted Source" in result.output
        assert (install_dir(project_dir, "text") / "function.yml").is_file()
        assert FunctionRegistry(project_dir).get("text")["source"] == "url"

    def test_archive_with_one_top_level_directory(self, cli, project_dir, source):
        with serve_files({"text.zip": zip_package(source, top_level="text-1.0")}) as url:
            result = cli("add", "text", "--from", url("text.zip"), input="y\n")
        assert result.exit_code == 0, result.output
        assert (install_dir(project_dir, "text") / "__init__.py").is_file()

    def test_declined_prompt_installs_nothing_and_makes_no_request(self, cli, project_dir, source):
        with serve_files({"text.zip": zip_package(source)}) as url:
            result = cli("add", "text", "--from", url("text.zip"), input="n\n")
            requests = list(url.requests)
        assert result.exit_code == 0 and "Cancelled" in result.output
        assert not install_dir(project_dir, "text").exists()
        assert requests == []

    def test_no_request_is_made_before_confirmation(self, cli, source, monkeypatch):
        calls: list[str] = []
        from specify_cli.authentication import http as auth_http

        def spy(url, *args, **kwargs):
            calls.append(url)
            raise AssertionError("network used")

        monkeypatch.setattr(auth_http, "open_url", spy)
        result = cli("add", "text", "--from", "https://example.com/text.zip", input="n\n")
        assert result.exit_code == 0 and calls == []

    @pytest.mark.parametrize(
        "url", ["http://example.com/p.zip", "ftp://example.com/p.zip", "file:///tmp/p.zip", "https:///p.zip", "not a url"]
    )
    def test_insecure_or_invalid_urls_fail_before_the_prompt(self, cli, project_dir, url):
        result = cli("add", "text", "--from", url)
        assert result.exit_code == 1
        assert "Continue with installation?" not in result.output
        assert not install_dir(project_dir, "text").exists()

    def test_already_installed_fails_before_the_prompt(self, cli, source):
        assert cli("add", "text", "--dev", str(source)).exit_code == 0
        with serve_files({"text.zip": zip_package(source)}) as url:
            result = cli("add", "text", "--from", url("text.zip"))
        assert result.exit_code == 1
        assert "already installed" in result.output
        assert "Continue with installation?" not in result.output

    def test_force_replaces_from_url(self, cli, project_dir, source, tmp_path):
        assert cli("add", "text", "--dev", str(source)).exit_code == 0
        new = write_package(tmp_path / "new", "text", version="2.0.0")
        with serve_files({"text.zip": zip_package(new)}) as url:
            result = cli("add", "text", "--from", url("text.zip"), "--force", input="y\n")
        assert result.exit_code == 0, result.output
        assert FunctionRegistry(project_dir).get("text")["version"] == "2.0.0"

    def test_http_error(self, cli, project_dir):
        with serve_files({}) as url:
            result = cli("add", "text", "--from", url("missing.zip"), input="y\n")
        assert result.exit_code == 1 and "Failed to install function from URL: HTTP Error 404" in result.output
        assert not install_dir(project_dir, "text").exists()

    @pytest.mark.parametrize("payload", [b"not an archive", b""])
    def test_invalid_archive(self, cli, project_dir, payload):
        with serve_files({"text.zip": payload}) as url:
            result = cli("add", "text", "--from", url("text.zip"), input="y\n")
        assert result.exit_code == 1 and "Failed to install function from URL" in result.output
        assert not install_dir(project_dir, "text").exists()

    def test_archive_without_a_manifest(self, cli, project_dir, tmp_path):
        (tmp_path / "empty").mkdir()
        (tmp_path / "empty" / "README").write_text("x")
        with serve_files({"text.zip": zip_package(tmp_path / "empty")}) as url:
            result = cli("add", "text", "--from", url("text.zip"), input="y\n")
        assert result.exit_code == 1 and "function.yml at its root" in result.output

    def test_path_traversal_archive_is_rejected(self, cli, project_dir, tmp_path, source):
        import io

        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w") as archive:
            archive.writestr("../evil.py", "x")
            archive.write(source / "function.yml", "function.yml")
            archive.write(source / "__init__.py", "__init__.py")
        with serve_files({"text.zip": buffer.getvalue()}) as url:
            result = cli("add", "text", "--from", url("text.zip"), input="y\n")
        assert result.exit_code == 1
        assert not (project_dir / ".specify" / "workflows" / "evil.py").exists()
        assert not (project_dir.parent / "evil.py").exists()
        assert not install_dir(project_dir, "text").exists()

    def test_archive_collision_is_reported(self, cli, project_dir, tmp_path):
        write_installed(project_dir, "alpha")
        FunctionRegistry(project_dir).add("alpha", {"functions": [{"name": "trim"}]})
        with serve_files({"b.zip": zip_package(write_package(tmp_path / "b", "beta"))}) as url:
            result = cli("add", "beta", "--from", url("b.zip"), input="y\n")
        assert result.exit_code == 1 and "already provided by package 'alpha'" in result.output
        assert not install_dir(project_dir, "beta").exists()


    def test_archive_format_mismatch_is_rejected(self, cli, project_dir, source):
        with serve_files({"text.tar.gz": zip_package(source)}) as url:
            result = cli("add", "text", "--from", url("text.tar.gz"), input="y\n")
        assert result.exit_code == 1
        assert not install_dir(project_dir, "text").exists()


class TestSharedUrlFlow:
    """``--from`` uses the same trust and download flow as step packages."""

    def test_trust_prompt_names_the_kind_and_shows_the_url(self, cli, source):
        with serve_files({"text.zip": zip_package(source)}) as url:
            target = url("text.zip")
            result = cli("add", "text", "--from", target, input="n\n")
        output = " ".join(result.output.split())
        assert "Untrusted Source" in output and "function package" in output
        assert target in result.output
        assert "Only install function packages from sources you trust." in output

    def test_both_commands_delegate_to_the_shared_flow(self, project_dir, monkeypatch, source):
        from specify_cli.workflows import _archive_install as archive
        from specify_cli.workflows.function import command_add as function_add
        from specify_cli.workflows.step import command_add as step_add

        calls = []

        def spy(request, spec, hooks):
            calls.append(spec.noun)
            return {"name": request.package_id}

        monkeypatch.setattr(archive, "install_from_archive_url", spy)
        function_add._install_from_url(project_dir, "text", "https://example.com/t.zip", False)
        step_add._install_from_url(project_dir, "my-step", "https://example.com/s.zip", force=False)
        assert calls == ["Function", "Step"]

    def test_content_type_and_name_must_agree(self, cli, project_dir, source):
        with serve_files({"text.tar.gz": zip_package(source)}) as url:
            result = cli("add", "text", "--from", url("text.tar.gz"), input="y\n")
        assert result.exit_code == 1 and "Archive format mismatch" in result.output
        assert not install_dir(project_dir, "text").exists()

    def test_temporary_archive_directories_are_removed(self, cli, source, tmp_path, monkeypatch):
        import tempfile

        created = []
        real = tempfile.TemporaryDirectory

        class Tracking(real):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                created.append(self.name)

        monkeypatch.setattr(tempfile, "TemporaryDirectory", Tracking)
        with serve_files({"text.zip": zip_package(source)}) as url:
            assert cli("add", "text", "--from", url("text.zip"), input="y\n").exit_code == 0
        import os

        assert any("speckit-function-archive-" in n for n in created)
        assert not [n for n in created if os.path.exists(n)]

    def test_install_error_notes_are_rendered_as_warnings(self):
        from specify_cli.workflows import _commands as commands

        error = ValueError("boom [red]")
        error.add_note("residue at /tmp/x")
        from io import StringIO

        from rich.console import Console

        buffer = StringIO()
        original = commands.console
        commands.console = Console(file=buffer, width=200, force_terminal=False)
        try:
            commands._print_package_error(error)
        finally:
            commands.console = original
        text = buffer.getvalue()
        assert "Warning: residue at /tmp/x" in text and "Error: boom [red]" in text
