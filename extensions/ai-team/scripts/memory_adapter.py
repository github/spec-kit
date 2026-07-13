#!/usr/bin/env python3
"""Persist AI Team memory through a local file adapter or optional Mem0 mirror."""

from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import os
import re
import sys
import tempfile
from pathlib import Path
from typing import Any

import yaml


IGNORE_START = "# BEGIN AI TEAM PRIVATE MEMORY"
IGNORE_END = "# END AI TEAM PRIVATE MEMORY"
IGNORE_PATHS = (
    "/.specify/ai-team/memory/staging/",
    "/.specify/ai-team/memory/local/",
    "/.specify/ai-team/memory/department/",
    "/.specify/ai-team/releases/private/",
)
DEFAULT_TIER_PATHS = {
    "local": ".specify/ai-team/memory/local",
    "department": ".specify/ai-team/memory/department",
    "enterprise": "docs/ai-team/memory",
}


class MemoryAdapterError(RuntimeError):
    """Raised when memory cannot be persisted without violating its contract."""


def ensure_memory_gitignore(project_root: Path) -> Path:
    """Add the managed private-memory ignore block without touching other rules."""
    gitignore = project_root / ".gitignore"
    existing = gitignore.read_text(encoding="utf-8") if gitignore.exists() else ""
    block = "\n".join((IGNORE_START, *IGNORE_PATHS, IGNORE_END))

    if IGNORE_START in existing or IGNORE_END in existing:
        if IGNORE_START not in existing or IGNORE_END not in existing:
            raise MemoryAdapterError("incomplete AI Team memory block in .gitignore")
        pattern = re.compile(
            rf"{re.escape(IGNORE_START)}.*?{re.escape(IGNORE_END)}", re.DOTALL
        )
        updated = pattern.sub(block, existing)
    else:
        separator = "" if not existing or existing.endswith("\n") else "\n"
        updated = f"{existing}{separator}{block}\n"

    if updated != existing:
        gitignore.write_text(updated, encoding="utf-8")
    return gitignore


def _load_config(project_root: Path, config_path: Path | None) -> dict[str, Any]:
    if config_path is None:
        config_path = (
            project_root
            / ".specify"
            / "extensions"
            / "ai-team"
            / "ai-team-config.yml"
        )
    if not config_path.exists():
        return {}
    loaded = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    if not isinstance(loaded, dict):
        raise MemoryAdapterError("AI Team config must be a YAML mapping")
    return loaded


def _frontmatter(card_text: str) -> dict[str, Any]:
    if not card_text.startswith("---\n"):
        raise MemoryAdapterError("memory card must start with YAML frontmatter")
    try:
        _, raw, _ = card_text.split("---", 2)
    except ValueError as exc:
        raise MemoryAdapterError("memory card frontmatter is not closed") from exc
    metadata = yaml.safe_load(raw) or {}
    if not isinstance(metadata, dict):
        raise MemoryAdapterError("memory card frontmatter must be a mapping")
    return metadata


def _inside(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
    except ValueError:
        return False
    return True


def _atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", dir=path.parent, delete=False
    ) as handle:
        handle.write(content)
        temporary = Path(handle.name)
    temporary.replace(path)


def _tier_path(config: dict[str, Any], tier: str) -> str:
    return str(
        config.get("memory", {})
        .get("tiers", {})
        .get(tier, {})
        .get("path", DEFAULT_TIER_PATHS[tier])
    )


def _update_index(destination: Path, record: dict[str, Any]) -> Path:
    index_path = destination.parent / "index.json"
    records: list[dict[str, Any]] = []
    if index_path.exists():
        loaded = json.loads(index_path.read_text(encoding="utf-8"))
        if isinstance(loaded, list):
            records = loaded
    records = [item for item in records if item.get("path") != record["path"]]
    records.append(record)
    _atomic_write(index_path, json.dumps(records, indent=2, ensure_ascii=False) + "\n")
    return index_path


def _sync_mem0(
    card_text: str,
    metadata: dict[str, Any],
    config: dict[str, Any],
    tier: str,
) -> Any:
    service = config.get("memory", {}).get("service", {})
    tier_config = config.get("memory", {}).get("tiers", {}).get(tier, {})
    if tier == "local" or metadata.get("privacy") == "private":
        raise MemoryAdapterError("local or private memory cannot be synced to mem0")
    namespace = str(tier_config.get("namespace", "")).strip()
    if not namespace:
        raise MemoryAdapterError(f"mem0 sync requires memory.tiers.{tier}.namespace")
    api_key_env = str(service.get("mem0", {}).get("api_key_env", "MEM0_API_KEY"))
    api_key = os.environ.get(api_key_env, "").strip()
    if not api_key:
        raise MemoryAdapterError(f"mem0 sync requires environment variable {api_key_env}")
    try:
        mem0 = importlib.import_module("mem0")
    except ImportError as exc:
        raise MemoryAdapterError(
            "mem0 backend requires the optional 'mem0ai' package"
        ) from exc

    client = mem0.MemoryClient(api_key=api_key)
    remote_metadata = {
        key: value
        for key, value in metadata.items()
        if key not in {"raw_customer_demand", "credentials", "secrets"}
    }
    remote_metadata.update({"tier": tier, "namespace": namespace})
    return client.add(
        messages=[{"role": "user", "content": card_text}],
        user_id=namespace,
        metadata=remote_metadata,
    )


def persist_memory(
    *,
    project_root: Path,
    source: Path,
    tier: str,
    backend: str = "file",
    config_path: Path | None = None,
) -> dict[str, Any]:
    """Persist one reviewed card locally and optionally mirror it to Mem0."""
    project_root = project_root.resolve()
    source = source.resolve()
    if tier not in DEFAULT_TIER_PATHS:
        raise MemoryAdapterError(f"unsupported memory tier: {tier}")
    if backend not in {"file", "mem0"}:
        raise MemoryAdapterError(f"unsupported memory backend: {backend}")
    if not _inside(source, project_root) or not source.is_file():
        raise MemoryAdapterError("memory source must be a file inside the project")

    ensure_memory_gitignore(project_root)
    config = _load_config(project_root, config_path)
    allowed_source_roots = [
        project_root / ".specify" / "ai-team" / "memory" / "staging",
        project_root / DEFAULT_TIER_PATHS[tier],
    ]
    if not any(_inside(source, root) for root in allowed_source_roots):
        raise MemoryAdapterError(
            "memory source must be under the managed staging or canonical tier path"
        )
    card_text = source.read_text(encoding="utf-8")
    metadata = _frontmatter(card_text)
    if metadata.get("tier") != tier:
        raise MemoryAdapterError("memory card tier does not match requested tier")
    required = {"memory_type", "privacy", "owner"}
    missing = sorted(key for key in required if not metadata.get(key))
    if missing:
        raise MemoryAdapterError(f"memory card is missing: {', '.join(missing)}")

    relative_root = Path(_tier_path(config, tier))
    if relative_root.is_absolute() or ".." in relative_root.parts:
        raise MemoryAdapterError("memory tier path must stay inside the project")
    destination_root = (project_root / relative_root).resolve()
    if not _inside(destination_root, project_root):
        raise MemoryAdapterError("memory tier path escapes the project")
    destination = destination_root / source.name
    _atomic_write(destination, card_text)

    digest = hashlib.sha256(card_text.encode("utf-8")).hexdigest()
    record: dict[str, Any] = {
        "path": destination.relative_to(project_root).as_posix(),
        "sha256": digest,
        "tier": tier,
        "privacy": metadata["privacy"],
        "memory_type": metadata["memory_type"],
        "owner": metadata["owner"],
        "backend": backend,
    }
    if backend == "mem0":
        response = _sync_mem0(card_text, metadata, config, tier)
        record["remote"] = response
    index_path = _update_index(destination, record)
    record["index"] = index_path.relative_to(project_root).as_posix()
    return record


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    parser.add_argument("--ensure-ignore", action="store_true")
    parser.add_argument("--source", type=Path)
    parser.add_argument("--tier", choices=sorted(DEFAULT_TIER_PATHS))
    parser.add_argument("--backend", choices=("file", "mem0"), default="file")
    parser.add_argument("--config", type=Path)
    args = parser.parse_args()

    try:
        if args.ensure_ignore:
            path = ensure_memory_gitignore(args.project_root.resolve())
            print(json.dumps({"gitignore": str(path)}, ensure_ascii=False))
            return 0
        if args.source is None or args.tier is None:
            parser.error("--source and --tier are required unless --ensure-ignore is used")
        result = persist_memory(
            project_root=args.project_root,
            source=args.source,
            tier=args.tier,
            backend=args.backend,
            config_path=args.config,
        )
    except (MemoryAdapterError, OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"AI Team memory adapter failed: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
