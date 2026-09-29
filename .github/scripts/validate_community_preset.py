"""Verify a community preset submission and its generated catalog changes.

Exit 1: confirmed submission mismatch; 2: check blocked; 3: generated files
need repair. The workflow decides labels and PR creation from these outcomes.
"""

import argparse
import hashlib
import json
import re
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

try:
    import yaml
except ImportError:
    print("BLOCKED: PyYAML is unavailable; cannot inspect published preset.yml")
    sys.exit(2)


class SubmissionMismatch(Exception):
    pass


class Blocked(Exception):
    pass


class GeneratedError(Exception):
    pass


def read_text(
    path: Path, context: str, error_type: type[Exception] = Blocked
) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise error_type(f"cannot read {context} ({path}): {exc}") from exc


def read_json(path: Path, context: str, error_type: type[Exception]) -> dict:
    try:
        value = json.loads(read_text(path, context, error_type))
    except json.JSONDecodeError as exc:
        raise error_type(f"{context} is invalid JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise error_type(f"{context} must be a JSON object")
    return value


def field(issue: dict, key: str) -> str:
    value = issue.get(key)
    if not isinstance(value, str) or not value.strip():
        raise SubmissionMismatch(f"missing or invalid issue field: {key}")
    return value.strip()


def csv_values(value: str) -> list[str]:
    return [part.strip() for part in value.split(",") if part.strip()]


def repository_parts(url: str) -> tuple[str, str]:
    parsed = urlsplit(url)
    match = re.fullmatch(r"/([^/]+)/([^/]+)/?", parsed.path)
    if parsed.scheme != "https" or parsed.netloc.lower() != "github.com" or not match:
        raise SubmissionMismatch(f"invalid GitHub repository URL: {url}")
    return match[1].lower(), match[2].lower()


def release_tag(issue: dict) -> str:
    owner, repo = repository_parts(field(issue, "repository"))
    url = field(issue, "download_url")
    parsed = urlsplit(url)
    prefix = f"/{owner}/{repo}/"
    path = parsed.path
    if parsed.scheme != "https" or parsed.netloc.lower() != "github.com":
        raise SubmissionMismatch(f"download URL is not a GitHub URL: {url}")
    if not path.lower().startswith(prefix):
        raise SubmissionMismatch("download URL does not belong to the submitted repository")
    suffix = path[len(prefix):]
    archive = re.fullmatch(r"archive/refs/tags/([^/]+)\.zip", suffix)
    release = re.fullmatch(r"releases/download/([^/]+)/[^/]+\.zip", suffix)
    if not (archive or release) or parsed.query or parsed.fragment:
        raise SubmissionMismatch(f"download URL is not a pinned ZIP release: {url}")
    tag = (archive or release)[1]
    version = field(issue, "version")
    if not re.fullmatch(r"\d+\.\d+\.\d+", version) or not re.fullmatch(
        rf"(?:v?{re.escape(version)}|.+-v?{re.escape(version)})", tag
    ):
        raise SubmissionMismatch(
            f"release tag {tag!r} does not match submitted version {version!r}"
        )
    return tag


def published_manifest(archive_path: Path, preset_id: str) -> dict:
    try:
        with zipfile.ZipFile(archive_path) as archive:
            matching = []
            invalid = []
            for member in archive.infolist():
                if member.is_dir() or member.filename.rsplit("/", 1)[-1] != "preset.yml":
                    continue
                try:
                    if member.file_size > 1024 * 1024:
                        raise ValueError("preset.yml exceeds 1 MiB")
                    with archive.open(member) as stream:
                        data = yaml.safe_load(stream.read().decode("utf-8"))
                except (yaml.YAMLError, UnicodeError, ValueError) as exc:
                    invalid.append(f"{member.filename}: {exc}")
                    continue
                if isinstance(data, dict) and isinstance(data.get("preset"), dict):
                    if data["preset"].get("id") == preset_id:
                        matching.append((member.filename, data))
    except FileNotFoundError as exc:
        raise Blocked(f"downloaded archive is unavailable at {archive_path}: {exc}") from exc
    except PermissionError as exc:
        raise Blocked(f"cannot read downloaded archive at {archive_path}: {exc}") from exc
    except OSError as exc:
        raise Blocked(f"cannot read downloaded archive at {archive_path}: {exc}") from exc
    except (zipfile.BadZipFile, EOFError) as exc:
        raise SubmissionMismatch(f"downloaded archive is not a readable ZIP: {exc}") from exc
    if len(matching) != 1:
        if not matching and invalid:
            raise SubmissionMismatch(
                f"no published preset.yml for {preset_id!r}; invalid manifests: "
                + "; ".join(invalid)
            )
        raise SubmissionMismatch(
            f"expected one published preset.yml for {preset_id!r}, found {len(matching)}"
        )
    return matching[0][1]


def required_extensions(manifest: dict) -> list[str]:
    requires = manifest.get("requires")
    if not isinstance(requires, dict):
        raise SubmissionMismatch("published preset.yml has no requires mapping")
    extensions = requires.get("extensions", [])
    if not isinstance(extensions, list):
        raise SubmissionMismatch("published requires.extensions must be a list")
    result = []
    for item in extensions:
        if isinstance(item, str):
            result.append(item)
        elif isinstance(item, dict) and isinstance(item.get("id"), str):
            if item.get("required", True) is not False:
                result.append(item["id"])
        else:
            raise SubmissionMismatch("invalid published requires.extensions entry")
    return result


def check_readme(text: str, issue: dict) -> None:
    expected = field(issue, "download_url")
    preset_id = field(issue, "preset_id")
    owner, repo = repository_parts(field(issue, "repository"))
    submitted_scope = re.fullmatch(r"(.+)-v?\d+\.\d+\.\d+", release_tag(issue))
    accepted_scopes = {preset_id}
    if submitted_scope:
        accepted_scopes.add(submitted_scope[1])
    accepted = False
    for match in re.finditer(
        r"(?<![\w-])specify\s+preset\s+add\s+"
        r"(?P<option>--from|--dev|[a-z][a-z0-9-]*)"
        r"(?:\s+(?P<value>[^\s`]+))?",
        text,
    ):
        option = match["option"]
        value = (match["value"] or "").strip("'\"<>(),.;")
        if option == "--from":
            if value == expected:
                accepted = True
                continue
            parsed = urlsplit(value)
            parts = parsed.path.split("/")
            tag = (
                parts[5] if len(parts) > 5 and parts[3] == "releases"
                else parts[6].removesuffix(".zip")
                if len(parts) > 6 and parts[3] == "archive"
                else ""
            )
            scoped = re.fullmatch(r"(.+)-v?\d+\.\d+\.\d+", tag)
            same_repository = (
                parsed.netloc.lower() == "github.com"
                and parsed.path.lower().startswith(f"/{owner}/{repo}/")
            )
            if (scoped and scoped[1] in accepted_scopes) or (
                same_repository and not scoped
            ):
                raise SubmissionMismatch(
                    f"README --from URL for {preset_id} differs from Download URL: {value}"
                )
        elif option == "--dev" and value:
            accepted = True
        elif option == preset_id:
            accepted = True
    if not accepted:
        raise SubmissionMismatch(
            "README has no valid specify preset add command for the submitted preset"
        )


def count_items(value: str) -> int:
    return sum(line.lstrip().startswith("- ") for line in value.splitlines())


def expected_values(issue: dict, manifest: dict, digest: str) -> dict:
    pack = manifest.get("preset")
    requires = manifest.get("requires")
    if not isinstance(pack, dict) or not isinstance(requires, dict):
        raise SubmissionMismatch("published preset.yml lacks preset or requires metadata")
    extension_ids = csv_values(issue.get("required_extensions", ""))
    actual_extensions = required_extensions(manifest)
    comparisons = {
        "preset.id": (pack.get("id"), field(issue, "preset_id")),
        "preset.version": (pack.get("version"), field(issue, "version")),
        "requires.speckit_version": (
            requires.get("speckit_version"), field(issue, "speckit_version")
        ),
        "requires.extensions": (sorted(actual_extensions), sorted(extension_ids)),
    }
    for name, (actual, expected) in comparisons.items():
        if actual != expected:
            raise SubmissionMismatch(
                f"published {name} {actual!r} differs from submitted {expected!r}"
            )
    dependencies = {"speckit_version": field(issue, "speckit_version")}
    if extension_ids:
        dependencies["extensions"] = extension_ids
    provided = {
        "templates": count_items(field(issue, "templates_provided")),
        "commands": count_items(field(issue, "commands_provided")),
    }
    scripts = issue.get("scripts_count", "0")
    if scripts:
        try:
            number = int(scripts)
        except (ValueError, TypeError) as exc:
            raise SubmissionMismatch("scripts_count must be a non-negative integer") from exc
        if number < 0:
            raise SubmissionMismatch("scripts_count must be a non-negative integer")
        if number:
            provided["scripts"] = number
    return {
        "id": field(issue, "preset_id"),
        "name": field(issue, "preset_name"),
        "version": field(issue, "version"),
        "description": field(issue, "description"),
        "author": field(issue, "author"),
        "repository": field(issue, "repository"),
        "download_url": field(issue, "download_url"),
        "sha256": digest,
        "documentation": field(issue, "documentation"),
        "license": field(issue, "license"),
        "requires": dependencies,
        "provides": provided,
        "tags": csv_values(field(issue, "tags")),
    }


def submission(args: argparse.Namespace) -> None:
    issue = read_json(args.issue, "issue input", Blocked)
    release_tag(issue)
    manifest = published_manifest(args.archive, field(issue, "preset_id"))
    check_readme(read_text(args.readme, "fetched README"), issue)
    try:
        with args.archive.open("rb") as archive:
            digest = hashlib.file_digest(archive, "sha256").hexdigest()
    except OSError as exc:
        raise Blocked(f"cannot hash downloaded archive: {exc}") from exc
    expected = expected_values(issue, manifest, digest)
    catalog = read_json(args.catalog, "original catalog", Blocked)
    entries = catalog.get("presets")
    if not isinstance(entries, dict):
        raise Blocked("original catalog has no presets object")
    previous = entries.get(expected["id"])
    if previous is not None and not isinstance(previous, dict):
        raise Blocked("original catalog entry is not an object")
    if previous is not None and not isinstance(previous.get("created_at"), str):
        raise Blocked("original catalog entry has no created_at to preserve")
    snapshot = {
        "expected": expected,
        "created_at": previous.get("created_at") if previous else None,
        "expected_timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT00:00:00Z"),
    }
    try:
        args.snapshot.write_text(json.dumps(snapshot), encoding="utf-8")
    except OSError as exc:
        raise Blocked(f"cannot write verifier snapshot: {exc}") from exc
    print("PASSED: published preset.yml, release tag, README, and issue fields agree")


def documentation_row(entry: dict) -> str:
    def cell(value: str) -> str:
        return value.replace("|", r"\|").replace("\n", " ")

    provided = entry["provides"]
    quantities = [
        f"{count} {name[:-1] if count == 1 else name}"
        for name, count in provided.items() if count
    ]
    dependencies = entry["requires"].get("extensions", [])
    requires = ", ".join(f"{name} extension" for name in dependencies) or "—"
    repo = entry["repository"].rstrip("/").rsplit("/", 1)[-1]
    return (
        f"| {cell(entry['name'])} | {cell(entry['description'])} | "
        f"{', '.join(quantities)} | {requires} | "
        f"[{repo}]({entry['repository']}) |"
    )


def generated(args: argparse.Namespace) -> None:
    snapshot = read_json(args.snapshot, "verifier snapshot", Blocked)
    expected = snapshot.get("expected")
    if not isinstance(expected, dict) or not isinstance(expected.get("id"), str):
        raise Blocked("verifier snapshot lacks validated expected values")
    expected_timestamp = snapshot.get("expected_timestamp")
    if not isinstance(expected_timestamp, str):
        raise Blocked("verifier snapshot lacks the expected UTC timestamp")
    catalog = read_json(args.catalog, "generated catalog", GeneratedError)
    entries = catalog.get("presets")
    if not isinstance(entries, dict):
        raise GeneratedError("generated catalog has no presets object")
    keys = list(entries)
    if keys != sorted(keys):
        raise GeneratedError("catalog preset IDs are not in alphabetical order")
    entry = entries.get(expected["id"])
    if not isinstance(entry, dict):
        raise GeneratedError(f"catalog is missing entry {expected['id']}")
    for key, value in expected.items():
        if entry.get(key) != value:
            raise GeneratedError(f"catalog {key} does not match validated value: {value!r}")
    if snapshot.get("created_at") is not None:
        if entry.get("created_at") != snapshot["created_at"]:
            raise GeneratedError("catalog created_at was not preserved on update")
    elif entry.get("created_at") != expected_timestamp:
        raise GeneratedError("new catalog created_at does not match the expected UTC date")
    if entry.get("updated_at") != expected_timestamp:
        raise GeneratedError("catalog entry updated_at does not match the expected UTC date")
    if catalog.get("updated_at") != expected_timestamp:
        raise GeneratedError("catalog top-level updated_at does not match the expected UTC date")
    docs = read_text(args.docs, "generated documentation", GeneratedError)
    lines = docs.splitlines()
    try:
        start = next(i for i, line in enumerate(lines) if line.startswith("| Preset |"))
    except StopIteration as exc:
        raise GeneratedError("documentation has no Community Presets table") from exc
    rows = []
    for line in lines[start + 2:]:
        if not line.startswith("|"):
            break
        rows.append(line.strip())
    names = [row.split("|", 2)[1].strip() for row in rows]
    if names != sorted(names, key=str.casefold):
        raise GeneratedError("documentation preset names are not in alphabetical order")
    expected_row = documentation_row(expected)
    if rows.count(expected_row) != 1:
        raise GeneratedError(f"documentation row does not match validated values: {expected_row}")
    if names.count(expected["name"]) != 1:
        raise GeneratedError("documentation contains duplicate preset names")
    print("PASSED: generated catalog and documentation match validated submission")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=("submission", "generated"))
    for name in ("issue", "archive", "readme", "catalog", "docs", "snapshot"):
        parser.add_argument(f"--{name}", required=True, type=Path)
    args = parser.parse_args()
    try:
        if args.phase == "submission":
            submission(args)
        else:
            generated(args)
    except SubmissionMismatch as exc:
        print(f"FAILED: {exc}")
        return 1
    except Blocked as exc:
        print(f"BLOCKED: {exc}")
        return 2
    except GeneratedError as exc:
        print(f"REPAIR: {exc}")
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
