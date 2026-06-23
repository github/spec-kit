#!/usr/bin/env python3
"""Validate the preview extension package."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parent.parent
CONTRACT_PATH = ROOT / "schemas" / "preview" / "contract.json"
CONTRACT_SCHEMA_PATH = ROOT / "schemas" / "preview" / "contract.schema.json"


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def load_json(path: Path) -> Any:
    if not path.is_file():
        fail(f"{path.relative_to(ROOT)} is missing")
    return json.loads(path.read_text(encoding="utf-8"))


def require_phrases(name: str, content: str, phrases: list[str]) -> None:
    missing = [phrase for phrase in phrases if phrase not in content]
    if missing:
        fail(f"{name} missing required phrases: {missing}")


def reject_phrases(name: str, content: str, phrases: list[str]) -> None:
    stale = [phrase for phrase in phrases if phrase in content]
    if stale:
        fail(f"{name} contains disallowed phrases: {stale}")


def resolve_ref(schema: dict[str, Any], ref: str) -> dict[str, Any]:
    if not ref.startswith("#/"):
        fail(f"unsupported JSON schema ref: {ref}")
    current: Any = schema
    for part in ref[2:].split("/"):
        current = current[part]
    if not isinstance(current, dict):
        fail(f"JSON schema ref does not resolve to an object: {ref}")
    return current


def validate_json_schema_subset(
    value: Any,
    node: dict[str, Any],
    root_schema: dict[str, Any],
    path: str = "$",
) -> None:
    if "$ref" in node:
        validate_json_schema_subset(value, resolve_ref(root_schema, node["$ref"]), root_schema, path)
        return

    expected_type = node.get("type")
    if expected_type == "object":
        if not isinstance(value, dict):
            fail(f"{path} must be an object")
        required = node.get("required", [])
        missing = [key for key in required if key not in value]
        if missing:
            fail(f"{path} missing required keys: {missing}")
        properties = node.get("properties", {})
        if node.get("additionalProperties") is False:
            extra = [key for key in value if key not in properties]
            if extra:
                fail(f"{path} contains unsupported keys: {extra}")
        for key, child in properties.items():
            if key in value:
                validate_json_schema_subset(value[key], child, root_schema, f"{path}.{key}")
        return

    if expected_type == "array":
        if not isinstance(value, list):
            fail(f"{path} must be an array")
        min_items = node.get("minItems")
        if min_items is not None and len(value) < min_items:
            fail(f"{path} must contain at least {min_items} items")
        if node.get("uniqueItems"):
            serialized = [json.dumps(item, sort_keys=True, ensure_ascii=False) for item in value]
            if len(serialized) != len(set(serialized)):
                fail(f"{path} must not contain duplicate items")
        item_schema = node.get("items")
        if item_schema:
            for index, item in enumerate(value):
                validate_json_schema_subset(item, item_schema, root_schema, f"{path}[{index}]")
        return

    if expected_type == "string":
        if not isinstance(value, str):
            fail(f"{path} must be a string")
        pattern = node.get("pattern")
        if pattern and not re.search(pattern, value):
            fail(f"{path} does not match pattern {pattern!r}")

    enum = node.get("enum")
    if enum is not None and value not in enum:
        fail(f"{path} must be one of {enum}")


def validate_contract(contract: dict[str, Any], schema: dict[str, Any]) -> None:
    validate_json_schema_subset(contract, schema, schema)


def render_catalog_phrase(template: str, manifest: dict[str, Any]) -> str:
    extension = manifest["extension"]
    commands = manifest["provides"]["commands"]
    tags = manifest["tags"]
    replacements = {
        "{extension.id}": extension["id"],
        "{extension.name}": extension["name"],
        "{extension.version}": extension["version"],
        "{extension.description}": extension["description"],
        "{extension.repository}": extension["repository"],
        "{requires.speckit_version}": manifest["requires"]["speckit_version"],
        "{commands.count}": str(len(commands)),
        "{tags.csv}": ", ".join(tags),
    }
    phrase = template
    for token, value in replacements.items():
        phrase = phrase.replace(token, value)
    return phrase


def main() -> None:
    contract = load_json(CONTRACT_PATH)
    contract_schema = load_json(CONTRACT_SCHEMA_PATH)
    validate_contract(contract, contract_schema)

    manifest_path = ROOT / "extension.yml"
    if not manifest_path.is_file():
        fail("extension.yml is missing")
    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    extension = manifest.get("extension", {})
    commands = manifest.get("provides", {}).get("commands", [])

    expected_extension = contract["extension"]
    if extension.get("id") != expected_extension["id"]:
        fail(f"extension.id must be {expected_extension['id']}")
    if extension.get("version") != expected_extension["version"]:
        fail(f"extension.version must be {expected_extension['version']}")
    if extension.get("repository") != expected_extension["repository"]:
        fail("extension.repository must point to the standalone repository")

    command_contracts = contract["commands"]
    command_paths = {
        item["name"]: ROOT / item["file"]
        for item in command_contracts
    }
    template_paths = {
        item["path"]: ROOT / item["path"]
        for item in contract["templates"]
    }

    for path in [*command_paths.values(), *template_paths.values()]:
        if not path.is_file():
            fail(f"{path.relative_to(ROOT)} is missing")

    actual_command_files = sorted(
        str(path.relative_to(ROOT)).replace("\\", "/")
        for path in (ROOT / "commands").glob("speckit.preview.*.md")
    )
    expected_command_files = sorted(item["file"] for item in command_contracts)
    if actual_command_files != expected_command_files:
        fail(f"unexpected command files: {actual_command_files}")

    actual_template_files = sorted(
        str(path.relative_to(ROOT)).replace("\\", "/")
        for path in (ROOT / "templates" / "preview").glob("*.*")
    )
    expected_template_files = sorted(item["path"] for item in contract["templates"])
    if actual_template_files != expected_template_files:
        fail(f"unexpected template files: {actual_template_files}")

    actual_schema_files = sorted(
        str(path.relative_to(ROOT)).replace("\\", "/")
        for path in (ROOT / "schemas" / "preview").glob("*.json")
    )
    expected_schema_files = [
        "schemas/preview/contract.json",
        "schemas/preview/contract.schema.json",
    ]
    if actual_schema_files != expected_schema_files:
        fail(f"unexpected schema files: {actual_schema_files}")

    command_names = [command.get("name") for command in commands]
    command_files = [command.get("file") for command in commands]
    if len(command_names) != len(set(command_names)):
        fail(f"duplicate command names: {command_names}")
    if len(command_files) != len(set(command_files)):
        fail(f"duplicate command files: {command_files}")

    expected_commands = {
        item["name"]: item["file"]
        for item in command_contracts
    }
    actual_commands = {
        command.get("name"): command.get("file")
        for command in commands
    }
    if actual_commands != expected_commands:
        fail(f"commands mismatch: {actual_commands}")

    shared_required = contract["sharedCommandRequiredPhrases"]
    shared_forbidden = contract["sharedCommandForbiddenPhrases"]
    for item in command_contracts:
        name = item["name"]
        content = command_paths[name].read_text(encoding="utf-8")
        required = [
            *shared_required,
            *item["requiredPhrases"],
            f"Write only `{item['target']}`.",
            f"Write `{item['target']}`",
            item["target"],
            item["template"],
            f"Load the output template from `.specify/extensions/preview/{item['template']}`",
        ]
        forbidden = [*shared_forbidden, *item["forbiddenPhrases"]]
        require_phrases(name, content, required)
        reject_phrases(name, content, forbidden)

    for item in contract["templates"]:
        content = template_paths[item["path"]].read_text(encoding="utf-8")
        require_phrases(item["path"], content, item["requiredPhrases"])

    docs = {
        path: (ROOT / path).read_text(encoding="utf-8")
        for path in contract["docs"]["paths"]
    }
    for path, content in docs.items():
        reject_phrases(path, content, contract["docs"]["forbiddenPhrases"])
        for item in command_contracts:
            require_phrases(path, content, [item["name"], Path(item["target"]).name])

    catalog = docs.get("CATALOG-SUBMISSION.md", "")
    catalog_phrases = [
        render_catalog_phrase(phrase, manifest)
        for phrase in contract["catalogRequiredPhrases"]
    ]
    require_phrases("CATALOG-SUBMISSION.md", catalog, catalog_phrases)

    print("preview extension package is valid")


if __name__ == "__main__":
    main()
