"""Validate submission identity and fetch a pinned step package without a shell.

Exit 1: submission defect; exit 2: environment blocker. Never imports submitted
code. Only the repository-owned installer is loaded to reuse its ID validator.
"""

import argparse
import hashlib
import importlib.util
import json
import re
import subprocess
import tempfile
from functools import cache
from pathlib import Path
from types import ModuleType
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
MAX_FILE_BYTES = 10 * 1024 * 1024


class SubmissionMismatch(Exception):
    pass


class Blocked(Exception):
    pass


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
    if (
        not re.fullmatch(r"\d+\.\d+\.\d+", version)
        or not re.fullmatch(r"[A-Za-z0-9._~-]+", tag)
        or not re.fullmatch(rf"(?:v?{re.escape(version)}|.+-v?{re.escape(version)})", tag)
    ):
        raise SubmissionMismatch("Release Tag must match Version and contain no slashes")
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
    for name, url in extra.items():
        if (
            not isinstance(name, str)
            or not re.fullmatch(r"[A-Za-z0-9._~/-]+", name)
            or any(part in ("", ".", "..", ".git", "__pycache__", ".DS_Store")
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
    for name, url in files.items():
        if not isinstance(url, str) or package_path(url) != directory + name:
            raise SubmissionMismatch("file URL must match its package-relative path")
        if any(name.startswith(other + "/") for other in files):
            raise SubmissionMismatch("file/directory path collision")
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
                "curl", "--proto", "=https", "--max-time", "60",
                "--max-filesize", str(max(1, limit)), "--silent", "--show-error",
                "--write-out", "%{http_code}", "--output", str(output), url,
            ],
            capture_output=True, text=True, check=False,
        )
    except OSError as exc:
        raise Blocked(f"cannot download {url}: {exc}") from exc
    status = result.stdout.strip()
    if status != "200" and re.fullmatch(r"[1-5]\d\d", status):
        if status in ("403", "408", "429") or status.startswith("5"):
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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("identity", "fetch"))
    parser.add_argument("--submission", required=True, type=Path)
    args = parser.parse_args()
    try:
        try:
            text = args.submission.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            raise Blocked(f"cannot read submission: {exc}") from exc
        try:
            data = json.loads(text)
        except json.JSONDecodeError as exc:
            raise SubmissionMismatch(f"invalid submission JSON: {exc}") from exc
        if not isinstance(data, dict):
            raise SubmissionMismatch("submission JSON must be an object")
        if args.operation == "identity":
            validate_identity(data)
            print("Identity validation passed")
        else:
            print(json.dumps(fetch_package(data, Path("/tmp/gh-aw/step-file.bin"))))
    except SubmissionMismatch as exc:
        print(f"FAILED: {exc}")
        return 1
    except Blocked as exc:
        print(f"BLOCKED: {exc}")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
