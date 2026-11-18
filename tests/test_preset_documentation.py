"""Catalog-derived documentation, invalid inputs, and docs deployment wiring."""

import copy
import importlib.util
import io
import json
import shutil
import subprocess
import sys
from html.parser import HTMLParser
from http.client import IncompleteRead
from pathlib import Path

import pytest
import yaml


ROOT = Path(__file__).resolve().parent.parent
GENERATOR = ROOT / "docs/generate_presets.py"
spec = importlib.util.spec_from_file_location("generate_presets", GENERATOR)
generator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(generator)


class DirectoryParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.entries = []
        self.links = []
        self.scripts = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "li" and attrs.get("class") == "preset-entry":
            self.entries.append(attrs)
        if tag == "a":
            self.links.append(attrs["href"])
        if tag == "script":
            self.scripts.append(attrs.get("src"))


@pytest.fixture
def catalog(tmp_path):
    entry = {
        "id": "sample",
        "name": "Sample Preset",
        "description": "Adds useful context",
        "author": "Contributor",
        "version": "1.2.3",
        "license": "MIT",
        "repository": "https://github.com/example/presets",
        "documentation": "https://github.com/example/presets/blob/v1.2.3/sample/README.md",
        "download_url": "https://github.com/example/presets/releases/download/sample-v1.2.3/sample.zip",
        "requires": {
            "speckit_version": ">=1.0.0",
            "extensions": [{"id": "aide", "version": ">=2.0", "required": False}],
        },
        "provides": {"templates": 1, "commands": 2},
        "tags": ["context", "planning"],
    }
    data = {"schema_version": "1.0", "presets": {"sample": entry}}
    path = tmp_path / "catalog.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return data, path, tmp_path / "docs"


def test_real_catalog_has_one_page_and_static_link_per_entry(tmp_path):
    catalog_path = ROOT / "presets/catalog.community.json"
    entries = json.loads(catalog_path.read_text(encoding="utf-8"))["presets"]
    assert generator.generate(catalog_path, tmp_path) == len(entries)
    listing = (tmp_path / "_generated/preset-directory.md").read_text(encoding="utf-8")
    parsed = DirectoryParser()
    parsed.feed(listing)
    assert len(parsed.entries) == len(entries)
    assert set(parsed.links) == {f"presets/{preset_id}.md" for preset_id in entries}
    assert all("hidden" not in entry for entry in parsed.entries)
    assert {page.stem for page in (tmp_path / "community/presets").glob("*.md")} == set(entries)
    for preset_id, entry in entries.items():
        detail = (tmp_path / f"community/presets/{preset_id}.md").read_text(encoding="utf-8")
        assert generator.html.escape(entry["name"]) in detail
        assert generator.html.escape(entry["download_url"]) in detail
        assert "do not review, audit, endorse, or support" in detail
        assert "after vetting" in detail.lower()
        assert "--install-allowed" not in detail


def test_generation_is_deterministic_and_removes_deleted_pages(catalog):
    data, path, docs = catalog
    other = copy.deepcopy(data["presets"]["sample"])
    other.update(id="other", name="Another Preset")
    data["presets"]["other"] = other
    path.write_text(json.dumps(data), encoding="utf-8")
    generator.generate(path, docs)
    first = (docs / "_generated/preset-directory.md").read_bytes()
    assert first.index(b"Another Preset") < first.index(b"Sample Preset")
    generator.generate(path, docs)
    assert (docs / "_generated/preset-directory.md").read_bytes() == first
    del data["presets"]["other"]
    path.write_text(json.dumps(data), encoding="utf-8")
    generator.generate(path, docs)
    assert not (docs / "community/presets/other.md").exists()
    assert (docs / "community/presets/sample.md").is_file()


def test_untrusted_metadata_is_text_not_markup_or_markdown(catalog):
    data, path, docs = catalog
    entry = data["presets"]["sample"]
    payload = '<script>alert("x")</script>\n\n\r\n![x](javascript:alert(1)) & |'
    entry.update(name=payload, description=payload, author=payload, tags=[payload])
    path.write_text(json.dumps(data), encoding="utf-8")
    generator.generate(path, docs)
    for generated in (
        docs / "_generated/preset-directory.md",
        docs / "community/presets/sample.md",
    ):
        source = generated.read_text(encoding="utf-8")
        assert payload not in source
        assert generator.escape_metadata(payload) in source
    listing = (docs / "_generated/preset-directory.md").read_text(encoding="utf-8")
    detail = (docs / "community/presets/sample.md").read_text(encoding="utf-8")
    parsed = DirectoryParser()
    parsed.feed(listing)
    assert parsed.scripts == ["../assets/preset-catalog.js"]
    assert json.loads(parsed.entries[0]["data-preset-tags"]) == [payload]
    assert generator.escape_metadata(payload) in detail
    assert "<script>" not in detail


@pytest.mark.skipif(shutil.which("docfx") is None, reason="DocFX is required to verify rendered Markdown")
@pytest.mark.parametrize("line_break", ["\n", "\r\n", "\r"])
def test_multiline_metadata_cannot_inject_links_in_rendered_docfx(catalog, line_break):
    data, path, docs = catalog
    entry = data["presets"]["sample"]
    payload = f"Literal text{line_break}{line_break}[injected](javascript:alert%281%29)"
    entry.update(
        name=payload, description=payload, author=payload, version=payload,
        license=payload, tags=[payload], updated_at=payload, sha256=payload,
    )
    entry["requires"] = {"speckit_version": payload, "extensions": [payload]}
    path.write_text(json.dumps(data), encoding="utf-8")
    generator.generate(path, docs)
    (docs / "community/presets.md").write_text(
        "# Community Presets\n\n"
        "[!INCLUDE [Directory](../_generated/preset-directory.md)]\n",
        encoding="utf-8",
    )
    config = {
        "build": {
            "content": [{"files": ["community/**.md"]}],
            "dest": "_site",
            "template": ["default", "modern"],
        },
    }
    (docs / "docfx.json").write_text(json.dumps(config), encoding="utf-8")
    result = subprocess.run(
        [shutil.which("docfx"), "docfx.json", "--logLevel", "Error"],
        cwd=docs, capture_output=True, text=True, timeout=120, check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    for page in ("community/presets.html", "community/presets/sample.html"):
        rendered = (docs / "_site" / page).read_text(encoding="utf-8")
        parsed = DirectoryParser()
        parsed.feed(rendered)
        assert not any(link.startswith("javascript:") for link in parsed.links)
        assert "[injected](javascript:alert%281%29)" in rendered


def test_optional_metadata_and_versioned_dependencies_are_present(catalog):
    _, path, docs = catalog
    generator.generate(path, docs)
    detail = (docs / "community/presets/sample.md").read_text(encoding="utf-8")
    assert "aide &gt;=2.0 (optional)" in detail
    assert "1 template, 2 commands" in detail
    assert "Not provided" in detail
    assert "No SHA-256 digest is listed" in detail


@pytest.mark.parametrize(("field", "value"), [
    ("id", "../escape"),
    ("name", None),
    ("repository", "javascript:alert(1)"),
    ("documentation", "https://user:secret@example.com/readme"),
    ("download_url", "https://example.com/\narchive.zip"),
    ("tags", "context"),
    ("provides", {"templates": -1}),
    ("provides", {"templates": True}),
    ("requires", {"speckit_version": ">=1", "extensions": [None]}),
])
def test_invalid_metadata_fails_before_replacing_existing_output(catalog, field, value):
    data, path, docs = catalog
    generator.generate(path, docs)
    original = (docs / "_generated/preset-directory.md").read_bytes()
    data["presets"]["sample"][field] = value
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ValueError):
        generator.generate(path, docs)
    assert (docs / "_generated/preset-directory.md").read_bytes() == original
    assert (docs / "community/presets/sample.md").is_file()


@pytest.mark.parametrize("content", [
    "{", "[]", '{"schema_version":"2.0","presets":{}}',
    '{"schema_version":"1.0","presets":[]}',
    '{"schema_version":"1.0","presets":{},"presets":{}}',
    '{"schema_version":"1.0","presets":{"../escape":{}}}',
])
def test_invalid_catalog_cli_reports_failure_without_output(tmp_path, content):
    path = tmp_path / "catalog.json"
    path.write_text(content, encoding="utf-8")
    docs = tmp_path / "docs"
    result = subprocess.run(
        [sys.executable, str(GENERATOR), "--catalog", str(path), "--docs", str(docs)],
        capture_output=True, text=True, check=False,
    )
    assert result.returncode == 1
    assert "Preset documentation generation failed:" in result.stderr
    assert not docs.exists()


def test_empty_catalog_produces_a_readable_empty_directory(catalog):
    data, path, docs = catalog
    data["presets"] = {}
    path.write_text(json.dumps(data), encoding="utf-8")
    assert generator.generate(path, docs) == 0
    assert "0 presets" in (docs / "_generated/preset-directory.md").read_text(encoding="utf-8")


def test_catalog_updates_trigger_normal_generation_before_docfx():
    workflow = yaml.safe_load((ROOT / ".github/workflows/docs.yml").read_text(encoding="utf-8"))
    assert "presets/catalog.community.json" in workflow[True]["push"]["paths"]
    assert "schedule" not in workflow[True]
    assert "publication" not in workflow["jobs"]["build"].get("outputs", {})
    steps = workflow["jobs"]["build"]["steps"]
    generation = next(index for index, step in enumerate(steps) if step.get("run") == "python3 docs/generate_presets.py --fetch-stars")
    assert steps[generation]["env"] == {"GH_TOKEN": "${{ github.token }}"}
    build = next(index for index, step in enumerate(steps) if "docfx docfx.json" in step.get("run", ""))
    assert generation < build
    config = json.loads((ROOT / "docs/docfx.json").read_text(encoding="utf-8"))
    assert "community/presets/*.md" in config["build"]["content"][0]["files"]
    assert "assets/**" in config["build"]["resource"][0]["files"]
    assert all("if" not in step for step in steps)
    assert workflow["jobs"]["deploy"]["if"] == "github.repository == 'github/spec-kit'"


def test_submissions_only_edit_catalog_not_generated_documentation():
    source = (ROOT / ".github/workflows/add-community-preset.md").read_text(encoding="utf-8")
    frontmatter = yaml.safe_load(source.split("---", 2)[1])
    allowed = frontmatter["safe-outputs"]["create-pull-request"]["allowed-files"]
    assert allowed == ["presets/catalog.community.json"]
    assert "--docs docs/community/presets.md" not in source


def test_stars_are_fetched_once_per_repository_and_rendered_on_both_pages(catalog, monkeypatch):
    data, path, docs = catalog
    other = copy.deepcopy(data["presets"]["sample"])
    other.update(id="other", name="Another Preset", repository="https://github.com/EXAMPLE/presets.git")
    data["presets"]["other"] = other
    path.write_text(json.dumps(data), encoding="utf-8")
    calls = []

    def fetch(request, timeout):
        calls.append((request, timeout))
        return io.BytesIO(b'{"stargazers_count": 1234}')

    monkeypatch.setattr(generator, "urlopen", fetch)
    monkeypatch.setenv("GH_TOKEN", "test-token")
    generator.generate(path, docs, fetch_stars=True)
    assert len(calls) == 1
    request, timeout = calls[0]
    assert request.full_url == "https://api.github.com/repos/example/presets"
    assert request.get_header("Authorization") == "Bearer test-token"
    assert timeout == 10
    listing = (docs / "_generated/preset-directory.md").read_text(encoding="utf-8")
    assert listing.count('aria-label="1,234 GitHub repository stars"') == 2
    assert ".git/stargazers" not in listing
    for preset_id in data["presets"]:
        detail = (docs / f"community/presets/{preset_id}.md").read_text(encoding="utf-8")
        assert "<dt>Repository stars</dt><dd>1,234</dd>" in detail


@pytest.mark.parametrize("response", [
    b"invalid JSON", b"[]", b"{}", b'{"stargazers_count":true}',
    b'{"stargazers_count":-1}', b'{"stargazers_count":"12"}',
])
def test_invalid_star_responses_are_reported_as_unavailable(catalog, monkeypatch, capsys, response):
    _, path, docs = catalog
    monkeypatch.setattr(generator, "urlopen", lambda *args, **kwargs: io.BytesIO(response))
    generator.generate(path, docs, fetch_stars=True)
    assert "Warning: stars unavailable for example/presets:" in capsys.readouterr().err
    assert "Stars unavailable" in (docs / "_generated/preset-directory.md").read_text(encoding="utf-8")
    assert "<dt>Repository stars</dt><dd>Unavailable</dd>" in (
        docs / "community/presets/sample.md"
    ).read_text(encoding="utf-8")


def test_star_network_failure_does_not_prevent_building_documentation(catalog, monkeypatch, capsys):
    _, path, docs = catalog

    def fail(*args, **kwargs):
        raise TimeoutError("GitHub lookup timed out")

    monkeypatch.setattr(generator, "urlopen", fail)
    assert generator.generate(path, docs, fetch_stars=True) == 1
    assert "GitHub lookup timed out" in capsys.readouterr().err
    assert "Stars unavailable" in (docs / "_generated/preset-directory.md").read_text(encoding="utf-8")


def test_truncated_star_response_does_not_prevent_building_documentation(catalog, monkeypatch, capsys):
    _, path, docs = catalog

    class TruncatedResponse(io.BytesIO):
        def read(self, *args):
            raise IncompleteRead(b'{"stargazers_count":', 10)

    monkeypatch.setattr(generator, "urlopen", lambda *args, **kwargs: TruncatedResponse())
    assert generator.generate(path, docs, fetch_stars=True) == 1
    assert "IncompleteRead" in capsys.readouterr().err
    assert "Stars unavailable" in (docs / "_generated/preset-directory.md").read_text(encoding="utf-8")
    assert "<dt>Repository stars</dt><dd>Unavailable</dd>" in (
        docs / "community/presets/sample.md"
    ).read_text(encoding="utf-8")


def test_zero_stars_is_a_real_count_and_no_token_is_required(catalog, monkeypatch):
    _, path, docs = catalog
    monkeypatch.delenv("GH_TOKEN", raising=False)
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)

    def fetch(request, timeout):
        assert request.get_header("Authorization") is None
        return io.BytesIO(b'{"stargazers_count":0}')

    monkeypatch.setattr(generator, "urlopen", fetch)
    generator.generate(path, docs, fetch_stars=True)
    assert 'aria-label="0 GitHub repository stars"' in (
        docs / "_generated/preset-directory.md"
    ).read_text(encoding="utf-8")


def test_non_github_repositories_never_receive_the_token(catalog, monkeypatch, capsys):
    data, path, docs = catalog
    data["presets"]["sample"]["repository"] = "https://example.com/presets"
    path.write_text(json.dumps(data), encoding="utf-8")
    monkeypatch.setenv("GH_TOKEN", "test-token")

    def unexpected_request(*args, **kwargs):
        pytest.fail("A non-GitHub repository must not cause an API request")

    monkeypatch.setattr(generator, "urlopen", unexpected_request)
    generator.generate(path, docs, fetch_stars=True)
    assert "not a GitHub repository URL" in capsys.readouterr().err
