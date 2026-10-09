"""Validate submission identity and fetch a pinned step package without a shell.

Exit 1: submission defect; exit 2: environment blocker. Never imports submitted
code. Only the repository-owned installer is loaded to reuse its ID validator.
"""

import argparse
import copy
import hashlib
import importlib.util
import json
import re
import subprocess
import tempfile
from functools import cache
from datetime import datetime, timezone
from pathlib import Path
from types import ModuleType
from typing import Any
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[2]
MAX_FILE_BYTES = 10 * 1024 * 1024


class SubmissionMismatch(Exception):
    pass


class Blocked(Exception):
    pass


class GeneratedError(Exception):
    pass


class DuplicateField(ValueError):
    pass


def unique_json_fields(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateField(f"Duplicate field '{key}' in JSON evidence")
        result[key] = value
    return result


def field(data: dict[str, Any], key: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value:
        raise SubmissionMismatch(f"missing or invalid {key}")
    return value


@cache
def load_installer() -> ModuleType:
    path = ROOT / "src/specify_cli/workflows/step/installer.py"
    spec = importlib.util.spec_from_file_location("community_step_installer", path)
    if spec is None or spec.loader is None:
        raise Blocked(f"cannot load repository-owned step validator at {path}")
    installer = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(installer)
    except (ImportError, OSError) as exc:
        raise Blocked(f"cannot load repository-owned step validator: {exc}") from exc
    return installer


def validate_identity(data: dict[str, Any]) -> tuple[str, str, str]:
    step_id = field(data, "step_id")
    if not re.fullmatch(r"[a-z][a-z0-9-]*", step_id):
        raise SubmissionMismatch("Step ID must use lowercase letters, digits, and hyphens")
    installer = load_installer()
    try:
        installer.validate_step_id(step_id)
    except installer.StepInstallError as exc:
        raise SubmissionMismatch(str(exc)) from exc

    repository = field(data, "repository")
    match = re.fullmatch(
        r"https://github\.com/([A-Za-z0-9_-]+)/([A-Za-z0-9_.-]+)/?", repository
    )
    if not match or match[2] in (".", ".."):
        raise SubmissionMismatch("invalid GitHub Repository URL")
    version = field(data, "version")
    tag = field(data, "release_tag")
    try:
        from packaging.version import InvalidVersion, Version
    except ImportError as exc:
        raise Blocked(f"cannot validate release versions: {exc}") from exc
    try:
        parsed_version = Version(version)
    except InvalidVersion as exc:
        raise SubmissionMismatch(f"invalid PEP 440 Version: {version}") from exc
    if not re.fullmatch(r"[A-Za-z0-9._~+!-]+", tag):
        raise SubmissionMismatch("Release Tag must match Version and contain no slashes")
    candidates = [tag, *(tag[index + 1:] for index, char in enumerate(tag) if char == "-")]
    for candidate in candidates:
        try:
            if Version(candidate) == parsed_version:
                break
        except InvalidVersion:
            continue
    else:
        raise SubmissionMismatch("Release Tag must match Version")
    download_url = field(data, "download_url")
    if not re.fullmatch(r"https://github\.com/[A-Za-z0-9._~+!/-]+", download_url):
        raise SubmissionMismatch("Download URL contains invalid characters or is not a GitHub URL")
    download = urlsplit(download_url)
    release_path = f"/{match[1]}/{match[2]}/releases/download/{tag}/"
    archive_path = f"/{match[1]}/{match[2]}/archive/refs/tags/{tag}"
    if (
        download.scheme != "https"
        or download.netloc != "github.com"
        or download.query
        or download.fragment
        or not re.fullmatch(r"[A-Za-z0-9._~+!/-]+", download.path)
        or any(part in (".", "..") for part in download.path.split("/"))
        or not (
            (
                download.path.startswith(release_path)
                and "/" not in download.path[len(release_path):]
                and download.path.endswith((".zip", ".tar.gz", ".tgz"))
            )
            or download.path in {
                archive_path + suffix for suffix in (".zip", ".tar.gz")
            }
        )
    ):
        raise SubmissionMismatch("Download URL must pin an archive in the submitted repository and release")
    return match[1], match[2], tag


def validate_files(data: dict[str, Any]) -> dict[str, tuple[str, str]]:
    owner, repo, tag = validate_identity(data)
    entry = data.get("catalog_entry")
    if not isinstance(entry, dict):
        raise SubmissionMismatch("catalog_entry must be an object")
    prefix = f"https://raw.githubusercontent.com/{owner}/{repo}/{tag}/"

    def package_path(url: str) -> str:
        if not url.startswith(prefix):
            raise SubmissionMismatch("file URL must match the submitted repository and tag")
        path = url[len(prefix):]
        if (
            not re.fullmatch(r"[A-Za-z0-9._~/-]+", path)
            or any(part in ("", ".", "..") for part in path.split("/"))
        ):
            raise SubmissionMismatch("file URL contains invalid characters or path segments")
        return path

    manifest_url = field(entry, "step_yml_url")
    manifest_path = package_path(manifest_url)
    if manifest_path.split("/")[-1] != "step.yml":
        raise SubmissionMismatch("step_yml_url must end in step.yml")
    directory = manifest_path.removesuffix("step.yml")
    files = {"step.yml": manifest_url, "__init__.py": field(entry, "init_url")}
    extra = entry.get("extra_files", {})
    if not isinstance(extra, dict):
        raise SubmissionMismatch("extra_files must be an object")
    forbidden = {"", ".", ".."} | {
        name.casefold() for name in load_installer().EXCLUDE_NAMES
    }
    for name, url in extra.items():
        if (
            not isinstance(name, str)
            or not re.fullmatch(r"[A-Za-z0-9._~/-]+", name)
            or any(part.casefold() in forbidden
                   for part in name.split("/"))
            or name.casefold() in ("step.yml", "__init__.py")
        ):
            raise SubmissionMismatch("invalid extra file path")
        files[name] = url
    installer = load_installer()
    directories = set()
    for name in files:
        parts = name.split("/")
        if len(parts) - 1 > installer._MAX_STEP_PACKAGE_DEPTH:
            raise SubmissionMismatch(
                f"package exceeds the {installer._MAX_STEP_PACKAGE_DEPTH}-level directory limit"
            )
        directories.update("/".join(parts[:depth]) for depth in range(1, len(parts)))
        if len(files) + len(directories) > installer._MAX_STEP_PACKAGE_FILES:
            raise SubmissionMismatch(
                f"package exceeds the {installer._MAX_STEP_PACKAGE_FILES}-entry limit "
                "(files and directories combined)"
            )
    folded_paths = {
        tuple(part.casefold() for part in name.split("/")) for name in files
    }
    if len(folded_paths) != len(files):
        raise SubmissionMismatch("case-insensitive duplicate package file path")
    if any(
        path[:depth] in folded_paths
        for path in folded_paths
        for depth in range(1, len(path))
    ):
        raise SubmissionMismatch("case-insensitive file/directory path collision")
    for name, url in files.items():
        if not isinstance(url, str) or package_path(url) != directory + name:
            raise SubmissionMismatch("file URL must match its package-relative path")
    hashes = entry.get("sha256")
    if (
        not isinstance(hashes, dict)
        or hashes.keys() != files.keys()
        or any(not isinstance(value, str) or not re.fullmatch(r"[A-Fa-f0-9]{64}", value)
               for value in hashes.values())
    ):
        raise SubmissionMismatch("sha256 must pin exactly every package file")
    return {name: (url, hashes[name].lower()) for name, url in files.items()}


def validate_file(data: dict[str, Any]) -> tuple[str, str, str]:
    files = validate_files(data)
    name = field(data, "file")
    if name not in files:
        raise SubmissionMismatch("selected file is not in the proposed entry")
    return name, *files[name]


def fetch_file(
    data: dict[str, Any], output: Path, *, remaining_bytes: int | None = None,
) -> dict[str, str]:
    name, url, expected = validate_file(data)
    limit = MAX_FILE_BYTES if remaining_bytes is None else min(MAX_FILE_BYTES, remaining_bytes)

    def size_error() -> SubmissionMismatch:
        if limit < MAX_FILE_BYTES:
            return SubmissionMismatch(f"file exceeds the remaining cumulative package budget: {url}")
        return SubmissionMismatch(f"file exceeds the 10 MiB limit: {url}")

    try:
        output.unlink(missing_ok=True)
        result = subprocess.run(
            [
                "curl", "--disable", "--proto", "=https", "--max-time", "60",
                "--max-filesize", str(max(1, limit)), "--silent", "--show-error",
                "--write-out", "%{http_code}", "--output", str(output), url,
            ],
            capture_output=True, text=True, check=False,
        )
    except OSError as exc:
        raise Blocked(f"cannot download {url}: {exc}") from exc
    status = result.stdout.strip()
    if status != "200" and re.fullmatch(r"[1-5]\d\d", status):
        if status in ("403", "407", "408", "429") or status.startswith("5"):
            raise Blocked(f"HTTP {status} downloading {url}")
        raise SubmissionMismatch(f"expected HTTP 200, received {status!r} from {url}")
    if result.returncode == 63 and status == "200":
        raise size_error()
    if result.returncode:
        raise Blocked(
            f"curl exited {result.returncode} for {url}: {result.stderr.strip()}"
        )
    if status != "200":
        raise Blocked(f"curl returned no valid HTTP status ({status!r}) for {url}")
    try:
        if output.stat().st_size > limit:
            raise size_error()
        payload = output.read_bytes()
    except OSError as exc:
        raise Blocked(f"cannot read downloaded {name}: {exc}") from exc
    actual = hashlib.sha256(payload).hexdigest()
    if actual != expected:
        raise SubmissionMismatch(
            f"SHA-256 mismatch for {name}: submitted {expected}, actual {actual}"
        )
    return {"file": name, "sha256": actual}


def fetch_package(data: dict[str, Any], manifest_output: Path) -> dict[str, Any]:
    files = validate_files(data)
    limit = load_installer()._MAX_STEP_PACKAGE_BYTES
    total = 0
    hashes = {}
    manifest = None
    try:
        manifest_output.unlink(missing_ok=True)
        with tempfile.TemporaryDirectory(prefix="community-step-") as directory:
            output = Path(directory) / "download"
            for name in files:
                result = fetch_file(
                    {**data, "file": name}, output, remaining_bytes=limit - total
                )
                size = output.stat().st_size
                if name in ("step.yml", "__init__.py") and size == 0:
                    raise SubmissionMismatch(f"{name} must be nonempty")
                total += size
                if total > limit:
                    raise SubmissionMismatch(
                        f"package exceeds the {limit // (1024 * 1024)} MiB cumulative size limit"
                    )
                hashes[name] = result["sha256"]
                if name == "step.yml":
                    manifest = output.read_bytes()
        if manifest is None:
            raise Blocked("downloaded package manifest is unavailable")
        manifest_output.write_bytes(manifest)
    except OSError as exc:
        raise Blocked(f"cannot stage downloaded package metadata: {exc}") from exc
    return {"sha256": hashes, "bytes": total}


RELEASE_FIELDS = (
    "url", "step_yml_url", "init_url", "extra_files", "sha256",
    "requires", "provides", "download_url",
)


def check_existing_release(record: dict[str, Any]) -> None:
    url = record.get("step_yml_url", record.get("url"))
    init = record.get("init_url")
    extra = record.get("extra_files", {})
    if (
        not isinstance(url, str) or not url.strip()
        or (init is None and not url.endswith("step.yml"))
        or (init is not None and (not isinstance(init, str) or not init.strip()))
        or not isinstance(extra, dict)
        or any(
            not isinstance(name, str)
            or not re.fullmatch(r"[A-Za-z0-9._~/-]+", name)
            or any(part in ("", ".", "..") for part in name.split("/"))
            or name.casefold() in ("step.yml", "__init__.py")
            or not isinstance(value, str) or not value.strip()
            for name, value in extra.items()
        )
    ):
        raise Blocked("existing release has invalid file metadata; maintainer repair required")
    hashes = record.get("sha256")
    if (
        not isinstance(hashes, dict)
        or hashes.keys() != {"step.yml", "__init__.py", *extra}
        or any(
            not isinstance(value, str) or not re.fullmatch(r"[A-Fa-f0-9]{64}", value)
            for value in hashes.values()
        )
    ):
        raise Blocked("existing release needs complete SHA-256 digests; maintainer repair required")
    if any(key in record and not isinstance(record[key], dict) for key in ("requires", "provides")):
        raise Blocked("existing release has invalid requirements or provides metadata")


def catalog_snapshot(
    data: dict[str, Any], original: dict[str, Any], receipt: dict[str, Any],
) -> dict[str, Any]:
    files = validate_files(data)
    expected_hashes = {name: digest for name, (_, digest) in files.items()}
    byte_count = receipt.get("bytes")
    if (
        receipt.get("sha256") != expected_hashes
        or not isinstance(byte_count, int) or isinstance(byte_count, bool)
        or not 0 <= byte_count <= load_installer()._MAX_STEP_PACKAGE_BYTES
    ):
        raise Blocked("download receipt does not match the submitted complete file digests")
    entries = original.get("steps")
    if not isinstance(entries, dict):
        raise Blocked("original catalog has no steps object")
    step_id = data["step_id"]
    submitted = data["catalog_entry"]
    if submitted.get("id") != step_id or submitted.get("version") != data["version"]:
        raise SubmissionMismatch("catalog ID/version must match the submission")
    if submitted.get("verified") is not False:
        raise SubmissionMismatch("community catalog verified must be false")
    if "releases" in submitted or any(key.startswith("_") for key in submitted):
        raise SubmissionMismatch("submitted entry must not supply history or internal fields")
    previous = entries.get(step_id)
    history = {}
    entry = {}
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT00:00:00Z")
    if step_id in entries:
        if not isinstance(previous, dict) or not isinstance(previous.get("created_at"), str):
            raise Blocked("existing entry lacks valid original metadata/created_at")
        from packaging.version import InvalidVersion, Version

        try:
            old_version = Version(field(previous, "version"))
        except (InvalidVersion, SubmissionMismatch) as exc:
            raise Blocked(f"existing entry has invalid version: {exc}") from exc
        new_version = Version(data["version"])
        if new_version < old_version:
            raise SubmissionMismatch("version downgrade is not allowed")
        existing_history = previous.get("releases", {})
        if not isinstance(existing_history, dict):
            raise Blocked("existing releases must be an object")
        seen = {old_version}
        for version, record in existing_history.items():
            if not isinstance(version, str) or not isinstance(record, dict):
                raise Blocked("existing release history has invalid version/record")
            try:
                normalized = Version(version)
            except InvalidVersion as exc:
                raise Blocked(f"existing history has invalid version: {version}") from exc
            if normalized in seen:
                raise Blocked("existing release history contains equivalent duplicate versions")
            seen.add(normalized)
            if {"id", "version", "releases", "_catalog_name", "_install_allowed"} & record.keys():
                raise Blocked("existing historical release contains reserved fields")
            check_existing_release(record)
        history = copy.deepcopy(existing_history)
        if new_version == old_version:
            if data.get("metadata_only") is not True:
                raise SubmissionMismatch("same-version updates require an explicit metadata-only correction")
            for key in ("step_yml_url", "init_url", "extra_files", "sha256", "download_url"):
                default = {} if key == "extra_files" else None
                old_value = previous.get(
                    key, previous.get("url") if key == "step_yml_url" else default
                )
                if old_value != submitted.get(key, default):
                    raise SubmissionMismatch("same-version repairs cannot replace file URLs or digests")
        else:
            if new_version in seen:
                raise SubmissionMismatch("new version already exists in preserved history")
            check_existing_release(previous)
            history[previous["version"]] = {
                key: copy.deepcopy(previous[key]) for key in RELEASE_FIELDS if key in previous
            }
        entry = {
            key: copy.deepcopy(value) for key, value in previous.items()
            if key not in (*RELEASE_FIELDS, "releases")
        }
    entry.update(copy.deepcopy(submitted))
    entry["sha256"] = expected_hashes
    entry["created_at"] = previous["created_at"] if previous is not None else timestamp
    entry["updated_at"] = timestamp
    if previous is not None and ("releases" in previous or history):
        entry["releases"] = history
    expected_catalog = copy.deepcopy(original)
    expected_catalog["steps"][step_id] = entry
    expected_catalog["steps"] = dict(sorted(expected_catalog["steps"].items()))
    expected_catalog["updated_at"] = timestamp
    return {"step_id": step_id, "expected_catalog": expected_catalog}


def verify_generated_catalog(snapshot: dict[str, Any], catalog: dict[str, Any]) -> None:
    expected = snapshot.get("expected_catalog")
    if not isinstance(expected, dict) or not isinstance(expected.get("steps"), dict):
        raise Blocked("catalog snapshot lacks expected catalog state")
    if catalog != expected:
        raise GeneratedError(
            "generated catalog differs from validated snapshot; preserve current/history "
            "digests, original metadata, unrelated entries, and timestamps"
        )
    if list(catalog["steps"]) != sorted(catalog["steps"]):
        raise GeneratedError("generated catalog IDs must be sorted")


def read_json(
    path: Path, error_type: type[Exception] = Blocked,
) -> dict[str, Any]:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise error_type(f"cannot read JSON evidence at {path}: {exc}") from exc
    try:
        value = json.loads(text, object_pairs_hook=unique_json_fields)
    except (json.JSONDecodeError, DuplicateField) as exc:
        raise error_type(f"invalid JSON evidence at {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise error_type(f"JSON evidence must be an object: {path}")
    return value


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("identity", "fetch", "snapshot", "generated"))
    parser.add_argument("--submission", required=True, type=Path)
    parser.add_argument("--catalog", type=Path, default=ROOT / "workflows/step-catalog.community.json")
    parser.add_argument("--snapshot", type=Path, default=Path("/tmp/gh-aw/step-catalog-snapshot.json"))
    parser.add_argument("--receipt", type=Path, default=Path("/tmp/gh-aw/step-downloads.json"))
    args = parser.parse_args()
    try:
        try:
            text = args.submission.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            raise Blocked(f"cannot read submission: {exc}") from exc
        try:
            data = json.loads(text, object_pairs_hook=unique_json_fields)
        except (json.JSONDecodeError, DuplicateField) as exc:
            raise SubmissionMismatch(f"invalid submission JSON: {exc}") from exc
        if not isinstance(data, dict):
            raise SubmissionMismatch("submission JSON must be an object")
        if args.operation == "identity":
            validate_identity(data)
            print("Identity validation passed")
        elif args.operation == "fetch":
            try:
                args.receipt.unlink(missing_ok=True)
                result = fetch_package(data, Path("/tmp/gh-aw/step-file.bin"))
                args.receipt.write_text(json.dumps(result), encoding="utf-8")
            except OSError as exc:
                raise Blocked(f"cannot store download receipt: {exc}") from exc
            print(json.dumps(result))
        elif args.operation == "snapshot":
            try:
                args.snapshot.unlink(missing_ok=True)
            except OSError as exc:
                raise Blocked(f"cannot clear old catalog snapshot: {exc}") from exc
            snapshot = catalog_snapshot(data, read_json(args.catalog), read_json(args.receipt))
            try:
                args.snapshot.write_text(json.dumps(snapshot, indent=2) + "\n", encoding="utf-8")
            except OSError as exc:
                raise Blocked(f"cannot store catalog snapshot: {exc}") from exc
            print("Catalog snapshot created; history and download evidence validated")
        else:
            verify_generated_catalog(
                read_json(args.snapshot), read_json(args.catalog, GeneratedError),
            )
            print("Generated catalog matches validated snapshot")
    except SubmissionMismatch as exc:
        print(f"FAILED: {exc}")
        return 1
    except Blocked as exc:
        print(f"BLOCKED: {exc}")
        return 2
    except GeneratedError as exc:
        print(f"GENERATED ERROR: {exc}")
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
