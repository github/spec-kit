"""Generate the community preset directory and DocFX detail pages from the catalog."""

import argparse
import html
import json
import os
import re
import shlex
import sys
from concurrent.futures import ThreadPoolExecutor
from http.client import HTTPException
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parent.parent


def text(value: object, context: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{context} must be a non-empty string")
    return value


def escape_metadata(value: str) -> str:
    # Literal blank lines end raw HTML blocks in DocFX's Markdown parser.
    return html.escape(value).replace("\r", "&#13;").replace("\n", "&#10;")


def url(value: object, context: str) -> str:
    value = text(value, context)
    parsed = urlsplit(value)
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or any(character.isspace() or ord(character) < 32 for character in value)
    ):
        raise ValueError(f"{context} must be an HTTPS URL without credentials or whitespace")
    return value


def unique_keys(pairs: list[tuple]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate catalog key: {key}")
        result[key] = value
    return result


def load_presets(catalog_path: Path) -> list[dict]:
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"), object_pairs_hook=unique_keys)
    if not isinstance(catalog, dict) or catalog.get("schema_version") != "1.0":
        raise ValueError("preset catalog must be an object with schema_version 1.0")
    entries = catalog.get("presets")
    if not isinstance(entries, dict):
        raise ValueError("preset catalog must contain a presets object")
    for preset_id, entry in entries.items():
        if not re.fullmatch(r"[a-z][a-z0-9-]*", preset_id):
            raise ValueError(f"invalid preset ID: {preset_id}")
        if not isinstance(entry, dict) or entry.get("id") != preset_id:
            raise ValueError(f"{preset_id}: entry ID must match its catalog key")
        for field in ("name", "description", "author", "version", "license"):
            text(entry.get(field), f"{preset_id}.{field}")
        for field in ("repository", "documentation", "download_url"):
            url(entry.get(field), f"{preset_id}.{field}")
        requires = entry.get("requires")
        if not isinstance(requires, dict):
            raise ValueError(f"{preset_id}.requires must be an object")
        text(requires.get("speckit_version"), f"{preset_id}.requires.speckit_version")
        dependencies(requires.get("extensions", []))
        provided = entry.get("provides")
        if not isinstance(provided, dict):
            raise ValueError(f"{preset_id}.provides must be an object")
        for kind in ("templates", "commands", "scripts"):
            count = provided.get(kind, 0)
            if not isinstance(count, int) or isinstance(count, bool) or count < 0:
                raise ValueError(f"{preset_id}.provides.{kind} must be a non-negative integer")
        tags = entry.get("tags")
        if not isinstance(tags, list):
            raise ValueError(f"{preset_id}.tags must be a list")
        for tag in tags:
            text(tag, f"{preset_id}.tags")
        for field in ("updated_at", "sha256"):
            if field in entry:
                text(entry[field], f"{preset_id}.{field}")
    return sorted(entries.values(), key=lambda entry: (entry["name"].casefold(), entry["id"]))


def dependencies(values: object) -> list[str]:
    if not isinstance(values, list):
        raise ValueError("requires.extensions must be a list")
    result = []
    for value in values:
        if isinstance(value, str):
            result.append(text(value, "extension dependency"))
        elif isinstance(value, dict):
            name = text(value.get("id"), "extension dependency ID")
            if "version" in value:
                name += f" {text(value['version'], 'extension dependency version')}"
            if "required" in value and not isinstance(value["required"], bool):
                raise ValueError("extension dependency required must be a boolean")
            if value.get("required", True) is False:
                name += " (optional)"
            result.append(name)
        else:
            raise ValueError("extension dependency must be a string or object")
    return result


def contributions(entry: dict) -> str:
    return ", ".join(
        f"{count} {kind[:-1] if count == 1 else kind}"
        for kind in ("templates", "commands", "scripts")
        if (count := entry["provides"].get(kind, 0))
    ) or "No contributions listed"


def repository_stars(presets: list[dict]) -> dict[str, int | None]:
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "spec-kit-preset-documentation",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    repositories = {}
    for entry in presets:
        repository = entry["repository"]
        parsed = urlsplit(repository)
        path = parsed.path.strip("/").removesuffix(".git")
        if (
            parsed.netloc.lower() != "github.com"
            or parsed.query
            or parsed.fragment
            or not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", path)
        ):
            print(f"Warning: stars unavailable for {repository}: not a GitHub repository URL", file=sys.stderr)
            repositories[repository] = None
        else:
            repositories[repository] = path.casefold()

    def fetch(repository: str) -> int | None:
        request = Request(f"https://api.github.com/repos/{repository}", headers=headers)
        try:
            with urlopen(request, timeout=10) as response:
                data = json.load(response)
            count = data.get("stargazers_count") if isinstance(data, dict) else None
            if not isinstance(count, int) or isinstance(count, bool) or count < 0:
                raise ValueError("GitHub response has no valid stargazers_count")
            return count
        except (OSError, ValueError, HTTPException) as exc:
            print(f"Warning: stars unavailable for {repository}: {exc}", file=sys.stderr)
            return None

    unique = sorted({repository for repository in repositories.values() if repository is not None})
    with ThreadPoolExecutor(max_workers=6) as pool:
        counts = dict(zip(unique, pool.map(fetch, unique)))
    return {
        repository: counts.get(key) if key is not None else None
        for repository, key in repositories.items()
    }


def star_badge(entry: dict, count: int | None) -> str:
    if count is None:
        return '<span class="preset-stars">Stars unavailable</span>'
    repository = entry["repository"].rstrip("/").removesuffix(".git")
    return (
        f'<a class="preset-stars" href="{html.escape(repository)}/stargazers" '
        f'aria-label="{count:,} GitHub repository stars" '
        f'title="Repository stars at the last documentation build">'
        f'<span aria-hidden="true">&#9734;</span> {count:,}</a>'
    )


def directory(presets: list[dict], stars: dict[str, int | None]) -> str:
    escape = escape_metadata
    tags = sorted({tag for entry in presets for tag in entry["tags"]}, key=str.casefold)
    options = "".join(f'<option value="{escape(tag)}">{escape(tag)}</option>' for tag in tags)
    rows = []
    for entry in presets:
        search = " ".join(
            [entry[field] for field in ("id", "name", "description", "author")]
            + entry["tags"] + dependencies(entry["requires"].get("extensions", []))
        )
        badges = "".join(f'<span class="preset-tag">{escape(tag)}</span>' for tag in entry["tags"])
        rows.append(
            f'<li class="preset-entry" data-preset-search="{escape(search)}" '
            f'data-preset-tags="{escape(json.dumps(entry["tags"]))}">'
            f'<div class="preset-entry-heading"><h2><a href="presets/{entry["id"]}.md">'
            f'{escape(entry["name"])}</a></h2><div class="preset-entry-stats"><span class="preset-version">'
            f'{escape(entry["version"])}</span>{star_badge(entry, stars.get(entry["repository"]))}</div></div>'
            f'<p>{escape(entry["description"])}</p>'
            f'<p class="preset-entry-meta">By {escape(entry["author"])}'
            f' <span aria-hidden="true">&middot;</span> {contributions(entry)}</p>'
            f'<div class="preset-tags" aria-label="Tags">{badges}</div></li>'
        )
    return f"""<!-- Generated by docs/generate_presets.py; do not edit. -->
<link rel="stylesheet" href="../assets/preset-catalog.css">
<script src="../assets/preset-catalog.js" defer></script>
<div class="preset-catalog" data-preset-catalog>
<form class="preset-controls" data-preset-controls hidden role="search" aria-label="Find community presets">
<div class="preset-search"><label for="preset-query">Search presets</label>
<input id="preset-query" name="q" type="search" placeholder="Name, purpose, author, or tag" autocomplete="off"></div>
<div><label for="preset-tag">Tag</label><select id="preset-tag" name="tag">
<option value="">All tags</option>{options}</select></div>
<div><label for="preset-sort">Sort</label><select id="preset-sort" name="sort">
<option value="az">Name: A to Z</option><option value="za">Name: Z to A</option></select></div>
<button type="reset" class="preset-reset">Clear filters</button>
</form>
<p class="preset-result-count" data-preset-status role="status" aria-live="polite" aria-atomic="true">{len(presets)} presets</p>
<p data-preset-empty hidden>No presets match these filters. Try another search or clear the filters.</p>
<ul class="preset-results">{"".join(rows)}</ul>
</div>
"""


def detail(entry: dict, stars: int | None) -> str:
    escape = escape_metadata
    metadata = {
        "Preset ID": entry["id"],
        "Catalog version": entry["version"],
        "Author": entry["author"],
        "Repository stars": f"{stars:,}" if stars is not None else "Unavailable",
        "License": entry["license"],
        "Requires Spec Kit": entry["requires"]["speckit_version"],
        "Extension dependencies": ", ".join(dependencies(entry["requires"].get("extensions", []))) or "None listed",
        "Provides": contributions(entry),
        "Tags": ", ".join(entry["tags"]) or "None listed",
        "Updated": entry.get("updated_at", "Not provided"),
    }
    definitions = "".join(
        f"<dt>{escape(label)}</dt><dd>{escape(value)}</dd>" for label, value in metadata.items()
    )
    checksum = (
        f'<p>Catalog SHA-256: <code>{escape(entry["sha256"])}</code></p>'
        if entry.get("sha256") else "<p>No SHA-256 digest is listed in this catalog entry.</p>"
    )
    command = escape(f"specify preset add --from {shlex.quote(entry['download_url'])}")
    return f"""<!-- Generated by docs/generate_presets.py; do not edit. -->
<link rel="stylesheet" href="../../assets/preset-catalog.css">

<div class="preset-detail">
<p><a href="../presets.md">Back to community presets</a></p>
<h1>{escape(entry["name"])}</h1>
<p>{escape(entry["description"])}</p>
<p class="preset-source-links"><a href="{escape(entry["repository"])}">View source</a>
<a href="{escape(entry["documentation"])}">Author documentation</a></p>
<h2>Preset details</h2>
<dl class="preset-metadata">{definitions}</dl>
<h2>Review before installing</h2>
<p>This preset is independently maintained. Maintainers check catalog metadata only;
they do not review, audit, endorse, or support the preset code.
You must vet the preset source and the exact release before installation.</p>
<p>The community catalog is discovery-only. After vetting, this command explicitly
installs the archive listed for version {escape(entry["version"])}:</p>
<pre><code class="lang-bash">{command}</code></pre>
{checksum}
<p>A digest checks archive integrity; it is not evidence of code review or safety.</p>
<h2>See also</h2>
<ul><li><a href="../../presets/catalogs.md">Preset catalogs and trust</a></li>
<li><a href="../../presets/publishing.md">Publish a community preset</a></li></ul>
</div>
"""


def generate(catalog_path: Path, docs_path: Path, *, fetch_stars: bool = False) -> int:
    presets = load_presets(catalog_path)
    stars = repository_stars(presets) if fetch_stars else {}
    pages = {f"{entry['id']}.md": detail(entry, stars.get(entry["repository"])) for entry in presets}
    listing = directory(presets, stars)
    details_path = docs_path / "community" / "presets"
    details_path.mkdir(parents=True, exist_ok=True)
    for stale in details_path.glob("*.md"):
        if stale.name not in pages:
            stale.unlink()
    for name, content in pages.items():
        (details_path / name).write_text(content, encoding="utf-8")
    include_path = docs_path / "_generated"
    include_path.mkdir(parents=True, exist_ok=True)
    (include_path / "preset-directory.md").write_text(listing, encoding="utf-8")
    return len(presets)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", type=Path, default=ROOT / "presets/catalog.community.json")
    parser.add_argument("--docs", type=Path, default=ROOT / "docs")
    parser.add_argument("--fetch-stars", action="store_true", help="Fetch GitHub repository star counts at build time")
    args = parser.parse_args()
    try:
        count = generate(args.catalog, args.docs, fetch_stars=args.fetch_stars)
    except (ValueError, OSError) as exc:
        parser.exit(1, f"Preset documentation generation failed: {exc}\n")
    print(f"Generated directory and detail pages for {count} community presets.")


if __name__ == "__main__":
    main()
