#!/usr/bin/env python3
"""Generate or refresh Spec Kit repository governance for the current project."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any


MEMORY_PATH = Path(".specify/memory/repository-governance.md")
TEMPLATE_PATH = Path(".specify/extensions/repository-governance/templates/repository-governance-template.md")
INTEGRATION_JSON = Path(".specify/integration.json")
INIT_OPTIONS_JSON = Path(".specify/init-options.json")

MARKER_START = "<!-- SPECKIT GOVERNANCE START -->"
MARKER_END = "<!-- SPECKIT GOVERNANCE END -->"

CONTEXT_FILES = {
    "agy": "AGENTS.md",
    "amp": "AGENTS.md",
    "auggie": ".augment/rules/specify-rules.md",
    "bob": "AGENTS.md",
    "claude": "CLAUDE.md",
    "codebuddy": "CODEBUDDY.md",
    "codex": "AGENTS.md",
    "copilot": ".github/copilot-instructions.md",
    "cursor-agent": ".cursor/rules/specify-rules.mdc",
    "devin": "AGENTS.md",
    "forge": "AGENTS.md",
    "gemini": "GEMINI.md",
    "generic": "AGENTS.md",
    "goose": "AGENTS.md",
    "iflow": "IFLOW.md",
    "junie": ".junie/AGENTS.md",
    "kilocode": ".kilocode/rules/specify-rules.md",
    "kimi": "KIMI.md",
    "kiro-cli": "AGENTS.md",
    "lingma": ".lingma/rules/specify-rules.md",
    "opencode": "AGENTS.md",
    "pi": "AGENTS.md",
    "qodercli": "QODER.md",
    "qwen": "QWEN.md",
    "roo": ".roo/rules/specify-rules.md",
    "shai": "SHAI.md",
    "tabnine": "TABNINE.md",
    "trae": ".trae/rules/project_rules.md",
    "vibe": "AGENTS.md",
    "windsurf": ".windsurf/rules/specify-rules.md",
}

README_FILES = ["README.md", "README.markdown", "README.txt"]
PROJECT_DOC_FILES = [
    "CONTRIBUTING.md",
    "SECURITY.md",
    "SUPPORT.md",
    "ARCHITECTURE.md",
    "ROADMAP.md",
]
PROJECT_DOC_DIRS = ["docs", "adr", "adrs", "specs"]
PACKAGE_MANIFESTS = [
    "package.json",
    "pyproject.toml",
    "Cargo.toml",
    "go.mod",
    "Gemfile",
    "pom.xml",
    "build.gradle",
    "build.gradle.kts",
    "composer.json",
    "requirements.txt",
    "setup.py",
    "setup.cfg",
]
LOCKFILES = [
    "package-lock.json",
    "pnpm-lock.yaml",
    "yarn.lock",
    "bun.lockb",
    "uv.lock",
    "poetry.lock",
    "Pipfile.lock",
    "Cargo.lock",
    "go.sum",
    "Gemfile.lock",
    "composer.lock",
]
TASK_RUNNERS = ["Makefile", "Taskfile.yml", "Taskfile.yaml", "justfile", "Brewfile"]
SOURCE_DIRS = ["src", "app", "lib", "services", "packages", "apps", "cmd", "internal", "scripts", "commands", "templates"]
TEST_DIRS = ["test", "tests", "spec", "specs", "e2e"]
REPOSITORY_POLICY_FILES = [
    "LICENSE",
    "CODEOWNERS",
    ".github/CODEOWNERS",
    "CONTRIBUTING.md",
    "SECURITY.md",
    "SUPPORT.md",
]
EXTENSION_ASSET_FILES = ["extension.yml", ".extensionignore"]
EXTENSION_ASSET_DIRS = ["commands", "templates"]
EXTENSION_CONTRACT_FILES = [
    "commands/speckit.repository-governance.refresh.md",
    "templates/repository-governance-template.md",
    "docs/extension-governance.md",
]
API_CONTRACT_FILES = [
    "openapi.yaml",
    "openapi.yml",
    "openapi.json",
    "api.yaml",
    "api.yml",
    "schema.graphql",
    "buf.yaml",
]
ARCHITECTURE_DIRS = ["infra", "deploy", "deployment", "k8s", "helm", "terraform"]
BUILD_CONFIG_FILES = [
    "tsconfig.json",
    "jsconfig.json",
    "vite.config.js",
    "vite.config.ts",
    "next.config.js",
    "next.config.mjs",
    "webpack.config.js",
    "rollup.config.js",
    "turbo.json",
    "nx.json",
    "pnpm-workspace.yaml",
    "lerna.json",
]
CODE_STYLE_FILES = [
    ".editorconfig",
    ".prettierrc",
    ".prettierrc.json",
    ".prettierrc.yml",
    "prettier.config.js",
    "prettier.config.cjs",
    "eslint.config.js",
    "eslint.config.mjs",
    ".eslintrc",
    ".eslintrc.json",
    "biome.json",
    "ruff.toml",
    ".ruff.toml",
    "pyproject.toml",
    "mypy.ini",
    "pytest.ini",
    "tox.ini",
    "vitest.config.js",
    "vitest.config.ts",
    "jest.config.js",
    "playwright.config.ts",
]
RUNTIME_CONFIG_FILES = [
    ".env.example",
    ".env.sample",
    "Dockerfile",
    "docker-compose.yml",
    "docker-compose.yaml",
    "compose.yml",
    "compose.yaml",
    "Procfile",
    "vercel.json",
    "netlify.toml",
    "fly.toml",
]
SPEC_KIT_METADATA = [".specify/integration.json", ".specify/init-options.json", ".specify/extensions.yml"]


def main() -> int:
    root = Path.cwd()
    if not (root / ".specify").is_dir():
        print("Error: .specify/ not found. Run from a Spec Kit project root.", file=sys.stderr)
        return 1

    state = read_json(root / INTEGRATION_JSON)
    init_options = read_json(root / INIT_OPTIONS_JSON)
    created_memory = ensure_memory(root)
    target = resolve_target(root, state, init_options)
    projection = render_projection(root, target, state, created_memory)
    evidence_summary = repository_evidence_summary(root, state, init_options) if created_memory else ""
    action = write_projection(target, projection)
    remove_stale_sections(root, target, init_options, state)

    print(f"Target governance file: {rel(root, target)}")
    print(f"Governance file: {action}")
    print(f"Review target: {rel(root, target)}")
    print(f"Internal initialization cache: {MEMORY_PATH.as_posix()} ({'created' if created_memory else 'existing'})")
    if created_memory:
        print(f"Repository evidence: {evidence_summary}")
    return 0


def ensure_memory(root: Path) -> bool:
    memory = root / MEMORY_PATH
    if memory.exists():
        return False
    template = root / TEMPLATE_PATH
    if not template.exists():
        raise SystemExit(f"Error: template not found: {TEMPLATE_PATH.as_posix()}")
    memory.parent.mkdir(parents=True, exist_ok=True)
    memory.write_text(render_initial_memory(root, template.read_text(encoding="utf-8-sig")), encoding="utf-8")
    return True


def render_initial_memory(root: Path, template: str) -> str:
    content = normalize_newlines(template)
    state = read_json(root / INTEGRATION_JSON)
    init_options = read_json(root / INIT_OPTIONS_JSON)
    content = replace_sync_report(content, root, state)
    evidence = "\n".join(
        [
            "## Repository Evidence",
            "",
            *repository_evidence_lines(root, state, init_options),
            "",
            "## Vertical SSOT Evidence",
            "",
            *vertical_ssot_evidence_lines(root, state, init_options),
            "",
            "## Repository Areas",
            "",
            *repository_area_lines(root),
            "",
            "## Development Commands",
            "",
            *development_command_lines(root),
            "",
        ]
    )
    marker = "\n## Scope\n"
    if marker in content:
        content = content.replace(marker, f"\n{evidence}{marker}", 1)
    else:
        content = content.rstrip() + "\n\n" + evidence
    return content


def replace_sync_report(content: str, root: Path, state: dict[str, Any]) -> str:
    report = "\n".join(
        [
            "<!--",
            "Sync Impact Report",
            f"- Active Integration: {default_integration(state) or 'unknown'}",
            f"- Installed Integrations: {', '.join(installed_integrations(state)) or 'none'}",
            f"- Skills Scanned: {len(scan_skills(root))}",
            f"- MCP Config Files Scanned: {', '.join(scan_mcp_configs(root)) or 'none'}",
            f"- Extension Config Status: .specify/extensions.yml ({extensions_status(root)})",
        "- Sections Changed: initialized repository evidence, vertical SSOT registry, and development commands",
            "- Flow: generate missing target governance files; update existing target governance files",
            "-->",
        ]
    )
    pattern = re.compile(r"<!--\nSync Impact Report\n.*?\n-->", re.DOTALL)
    if pattern.search(content):
        return pattern.sub(report, content, count=1)
    return content


def repository_evidence_summary(root: Path, state: dict[str, Any], init_options: dict[str, Any]) -> str:
    evidence = repository_evidence_lines(root, state, init_options)
    detected = [line for line in evidence if "none detected" not in line and "`unknown`" not in line]
    return "; ".join(line.removeprefix("- ") for line in detected) or "none detected"


def repository_evidence_lines(root: Path, state: dict[str, Any], init_options: dict[str, Any]) -> list[str]:
    lines = [
        evidence_line("README", existing_paths(root, README_FILES)),
        evidence_line("Project docs", unique_ordered([*existing_paths(root, PROJECT_DOC_FILES), *existing_dirs(root, PROJECT_DOC_DIRS)])),
        evidence_line("Repository policy", existing_paths(root, REPOSITORY_POLICY_FILES)),
        evidence_line("Spec Kit metadata", existing_paths(root, SPEC_KIT_METADATA)),
        evidence_line("Extension assets", extension_asset_paths(root)),
        evidence_line("Package manifest", package_manifest_paths(root)),
        evidence_line("Lockfiles", lockfile_paths(root)),
        evidence_line("Task runners", existing_paths(root, TASK_RUNNERS)),
        evidence_line("CI workflows", directory_files(root, ".github/workflows")),
        evidence_line("Source paths", source_paths(root)),
        evidence_line("Test paths", test_paths(root)),
        evidence_line("Feature specs", scan_feature_specs(root)),
        evidence_line("API contracts", api_contract_paths(root)),
        evidence_line("Build config", build_config_paths(root)),
        evidence_line("Runtime config", runtime_config_paths(root)),
        evidence_line("Repository areas", repository_area_paths(root)),
        evidence_line("Existing agent context files", existing_context_files(root, init_options, state)),
        evidence_line("Repository-local skills", scan_skills(root)),
        evidence_line("MCP configs", scan_mcp_configs(root)),
        f"- Active integration: `{default_integration(state) or 'unknown'}`",
        f"- Resolved context file: `{rel(root, resolve_target(root, state, init_options))}`",
    ]
    return lines


def vertical_ssot_evidence_lines(root: Path, state: dict[str, Any], init_options: dict[str, Any]) -> list[str]:
    return [
        evidence_line("Architecture evidence", architecture_evidence(root)),
        evidence_line("Engineering evidence", engineering_evidence(root)),
        evidence_line("Code Style evidence", code_style_evidence(root)),
        evidence_line("Directory Structure evidence", directory_structure_evidence(root)),
        evidence_line("Toolchain evidence", toolchain_evidence(root)),
        evidence_line("Agent Harness evidence", agent_harness_evidence(root, init_options, state)),
    ]


def architecture_evidence(root: Path) -> list[str]:
    return unique_ordered(
        [
            *source_paths(root),
            *route_files(root),
            *api_contract_paths(root),
            *existing_dirs(root, ARCHITECTURE_DIRS),
        ]
    )


def engineering_evidence(root: Path) -> list[str]:
    return unique_ordered(
        [
            *directory_files(root, ".github/workflows"),
            *existing_paths(root, ["CHANGELOG.md", "RELEASE.md", "VERSION"]),
            *existing_paths(root, EXTENSION_CONTRACT_FILES),
            *package_manifest_paths(root),
            *existing_paths(root, TASK_RUNNERS),
        ]
    )


def code_style_evidence(root: Path) -> list[str]:
    return unique_ordered(
        [
            *existing_paths(root, CODE_STYLE_FILES),
            *existing_top_level_globs(root, ["*.prettierrc.*", "eslint.config.*", "jest.config.*", "playwright.config.*", "vitest.config.*"]),
            *test_paths(root),
        ]
    )


def directory_structure_evidence(root: Path) -> list[str]:
    return repository_area_paths(root)


def toolchain_evidence(root: Path) -> list[str]:
    return unique_ordered(
        [
            *package_manifest_paths(root),
            *lockfile_paths(root),
            *existing_paths(root, TASK_RUNNERS),
            *extension_asset_paths(root),
            *build_config_paths(root),
            *runtime_config_paths(root),
        ]
    )


def agent_harness_evidence(root: Path, init_options: dict[str, Any], state: dict[str, Any]) -> list[str]:
    return unique_ordered(
        [
            *existing_context_files(root, init_options, state),
            *existing_paths(root, SPEC_KIT_METADATA),
            *scan_skills(root),
            *scan_mcp_configs(root),
        ]
    )


def evidence_line(label: str, values: list[str]) -> str:
    return f"- {label}: {format_values(values)}"


def format_values(values: list[str]) -> str:
    return ", ".join(f"`{value}`" for value in values) if values else "none detected"


def unique_ordered(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


def existing_paths(root: Path, names: list[str]) -> list[str]:
    return [name for name in names if (root / name).is_file()]


def existing_dirs(root: Path, names: list[str]) -> list[str]:
    return [f"{name}/" for name in names if (root / name).is_dir()]


def existing_top_level_globs(root: Path, patterns: list[str]) -> list[str]:
    matches: list[str] = []
    for pattern in patterns:
        for path in sorted(root.glob(pattern)):
            if path.is_file():
                matches.append(rel(root, path))
    return unique_ordered(matches)


def package_manifest_paths(root: Path) -> list[str]:
    return unique_ordered(
        [
            *existing_paths(root, PACKAGE_MANIFESTS),
            *existing_top_level_globs(root, ["requirements*.txt"]),
        ]
    )


def lockfile_paths(root: Path) -> list[str]:
    return existing_paths(root, LOCKFILES)


def source_paths(root: Path) -> list[str]:
    return existing_dirs(root, SOURCE_DIRS)


def test_paths(root: Path) -> list[str]:
    return existing_dirs(root, TEST_DIRS)


def api_contract_paths(root: Path) -> list[str]:
    return unique_ordered(
        [
            *existing_paths(root, API_CONTRACT_FILES),
            *existing_top_level_globs(root, ["*.proto", "*.graphql"]),
        ]
    )


def build_config_paths(root: Path) -> list[str]:
    return unique_ordered(
        [
            *existing_paths(root, BUILD_CONFIG_FILES),
            *existing_top_level_globs(root, ["tsconfig*.json", "vite.config.*", "next.config.*", "webpack.config.*"]),
        ]
    )


def extension_asset_paths(root: Path) -> list[str]:
    return unique_ordered([*existing_paths(root, EXTENSION_ASSET_FILES), *existing_dirs(root, EXTENSION_ASSET_DIRS)])


def runtime_config_paths(root: Path) -> list[str]:
    return unique_ordered(
        [
            *existing_paths(root, RUNTIME_CONFIG_FILES),
            *existing_dirs(root, ARCHITECTURE_DIRS),
        ]
    )


def directory_files(root: Path, directory: str) -> list[str]:
    base = root / directory
    if not base.is_dir():
        return []
    return sorted(rel(root, path) for path in base.iterdir() if path.is_file())


def route_files(root: Path) -> list[str]:
    result: list[str] = []
    route_name_pattern = re.compile(r"(route|routes|router|api|endpoint)", re.IGNORECASE)
    route_content_pattern = re.compile(
        r"(@app\.route|APIRouter|router\.|Route::|express\(|fastify\(|app\.(get|post|put|delete|patch)\()",
        re.IGNORECASE,
    )
    for base in (root / name for name in ("src", "app", "lib", "services", "packages")):
        if not base.is_dir():
            continue
        for path in sorted(base.rglob("*")):
            if not path.is_file() or ignored(path):
                continue
            if route_name_pattern.search(path.name):
                result.append(rel(root, path))
                continue
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            if route_content_pattern.search(text):
                result.append(rel(root, path))
    return unique_ordered(result)


def repository_area_lines(root: Path) -> list[str]:
    lines = []
    for area in repository_area_paths(root):
        if "/" in area.rstrip("/"):
            parent = area.rstrip("/").split("/", 1)[0] + "/"
            lines.append(f"- `{area}`: change with parent area `{parent}`.")
        else:
            lines.append(f"- `{area}`: review before changing linked areas.")
    return lines or ["- none detected"]


def repository_area_paths(root: Path) -> list[str]:
    areas: list[str] = []
    for path in sorted(root.iterdir()):
        if not path.is_dir():
            continue
        areas.append(f"{path.name}/")
        for child in sorted(path.iterdir()):
            if child.is_dir():
                areas.append(f"{path.name}/{child.name}/")
    return areas


def existing_context_files(root: Path, init_options: dict[str, Any], state: dict[str, Any]) -> list[str]:
    paths: set[Path] = {root / "AGENTS.md"}
    for value in CONTEXT_FILES.values():
        target = safe_project_path(root, value)
        if target is not None:
            paths.add(target)
    init_target = safe_project_path(root, init_options.get("context_file"))
    if init_target is not None:
        paths.add(init_target)
    resolved = resolve_target(root, state, init_options)
    paths.add(resolved)
    return sorted(rel(root, path) for path in paths if path.exists())


def development_command_lines(root: Path) -> list[str]:
    commands = package_script_lines(root)
    if commands:
        commands.append("- manifest commands over ad hoc equivalents")
        return commands
    commands = python_project_command_lines(root)
    if commands:
        commands.append("- project commands over ad hoc equivalents")
        return commands
    return ["- none detected"]


def package_script_lines(root: Path) -> list[str]:
    package_json = root / "package.json"
    data = read_json(package_json)
    scripts = data.get("scripts")
    if not isinstance(scripts, dict):
        return []
    result: list[str] = []
    for name in sorted(scripts):
        value = scripts[name]
        if not isinstance(value, str) or not value.strip():
            continue
        command = f"npm {name}" if name in {"start", "stop", "test", "restart"} else f"npm run {name}"
        result.append(f"- `{command}` -> `{value.strip()}`")
    return result


def python_project_command_lines(root: Path) -> list[str]:
    if not (root / "pyproject.toml").is_file():
        return []
    if not (test_paths(root) or existing_paths(root, ["pytest.ini", "tox.ini"])):
        return []
    prefix = "uv run --locked" if (root / "uv.lock").is_file() else "uv run"
    return [f"- `{prefix} pytest -q` -> pytest suite"]


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError, UnicodeDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def resolve_target(root: Path, state: dict[str, Any], init_options: dict[str, Any]) -> Path:
    for value in (
        init_options.get("context_file"),
        CONTEXT_FILES.get(default_integration(state) or ""),
        "AGENTS.md",
    ):
        target = safe_project_path(root, value)
        if target is not None:
            return target
    return root / "AGENTS.md"


def safe_project_path(root: Path, value: Any) -> Path | None:
    if not isinstance(value, str) or not value.strip():
        return None
    raw = Path(value.strip())
    candidate = raw if raw.is_absolute() else root / raw
    try:
        candidate.resolve(strict=False).relative_to(root.resolve())
    except (OSError, ValueError):
        return None
    return candidate


def default_integration(state: dict[str, Any]) -> str | None:
    for key in ("default_integration", "integration"):
        value = state.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    installed = state.get("installed_integrations")
    if isinstance(installed, list):
        for value in installed:
            if isinstance(value, str) and value.strip():
                return value.strip()
    return None


def installed_integrations(state: dict[str, Any]) -> list[str]:
    seen: set[str] = set()
    values = state.get("installed_integrations")
    if not isinstance(values, list):
        values = []
    default = default_integration(state)
    ordered = ([default] if default else []) + values
    result: list[str] = []
    for value in ordered:
        if not isinstance(value, str) or not value.strip():
            continue
        clean = value.strip()
        if clean not in seen:
            seen.add(clean)
            result.append(clean)
    return result


def render_projection(root: Path, target: Path, state: dict[str, Any], created_memory: bool) -> str:
    source_text, source_label = governance_source(root, target)
    default_key = default_integration(state) or "unknown"
    installed = installed_integrations(state)
    style = projection_style(target)
    lines = [
        MARKER_START,
        "## Repository Governance",
        "- SSOT: this managed section.",
        "- Framework: Repository Governance Framework.",
        f"- Target: {rel(root, target)}",
        f"- Active integration: {default_key}",
        f"- Refresh source: {source_label}",
        f"- Cache: {MEMORY_PATH.as_posix()} ({'created' if created_memory else 'present'})",
        "",
        "## Scope",
        "- Repository Governance Framework",
        "- top-level SSOT registry and routing",
        "- vertical SSOT discovery and read order",
        "- missing SSOT handling from repository evidence",
        "- conflict priority and handoff requirements",
        "- architecture methodology: owned by Architecture SSOT",
        "",
        "## Vertical SSOT Registry",
        *section_or_default(source_text, ["## Vertical SSOT Registry"], vertical_ssot_registry_default()),
        "",
        "## Context",
        f"- Installed integrations: {', '.join(installed) if installed else 'none'}",
        f"- Skills: {', '.join(scan_skills(root)) or 'none'}",
        f"- MCP configs: {', '.join(scan_mcp_configs(root)) or 'none'}",
        f"- Extensions config: .specify/extensions.yml ({extensions_status(root)})",
        "",
        "## Agent Platform Adapter",
        *agent_adapter_lines(root, target, default_key),
        "",
        "## Capability Index",
        *capability_index_lines(root),
        "",
        "## Repository Evidence",
        *section_or_default(source_text, ["## Repository Evidence"], repository_evidence_default()),
        "",
        "## Vertical SSOT Evidence",
        *section_or_default(source_text, ["## Vertical SSOT Evidence"], vertical_ssot_evidence_default()),
        "",
        "## Repository Areas",
        *section_or_default(source_text, ["## Repository Areas"], repository_areas_default()),
        "",
        "## Directory Governance",
        *section_or_default(source_text, ["## Directory Governance"], directory_governance_default()),
        "",
        "## Development Commands",
        *section_or_default(source_text, ["## Development Commands"], development_commands_default()),
        "",
        "## Missing SSOT Handling",
        *section_or_default(source_text, ["## Missing SSOT Handling"], missing_ssot_handling_default()),
        "",
        "## Authority",
        "1. Current user instruction",
        "2. Safety and permission constraints",
        "3. Active `SPECKIT GOVERNANCE` section",
        "4. Vertical SSOT documents",
        "5. Current repository code and configuration facts",
        "6. Tests and CI results",
        "7. Historical documents",
        "8. Agent inference",
        "",
        "## Repository Workflow",
        "- Classify task type before changing files.",
        "- Route task to relevant vertical SSOT entries.",
        "- Read: Repository Evidence",
        "- Run: Development Commands",
        "- Scope: active task only",
        "- Preserve: user-authored edits",
        "- Protected files: implementation, CI, MCP config, secrets, permissions, tool settings",
        "- Protected-file writes: explicit user request only",
        "- External writes: authorized target and action only",
        "- Handoff: changed files, commands, validation, risks",
        "",
        "## Write Boundaries",
        *section_or_default(source_text, ["## Write Boundaries"], write_boundary_default(style)),
        "",
        "## MCP And External Tools",
        *section_or_default(source_text, ["## MCP And External Tools", "## MCP And External Tool Policy", "## MCP Policy"], mcp_default(style)),
        "",
        "## Skills",
        *section_or_default(source_text, ["## Skills", "## Skill Usage Policy", "## Skill Contract"], skill_default(style)),
        "",
        "## Handoff",
        *section_or_default(source_text, ["## Handoff", "## Required Handoff Report", "## Validation"], handoff_default(style)),
        MARKER_END,
        "",
    ]
    return "\n".join(lines)


def write_projection(target: Path, projection: str) -> str:
    existed = target.exists()
    existing = target.read_text(encoding="utf-8-sig") if target.exists() else ""
    updated = upsert_section(existing, projection)
    if target.suffix == ".mdc":
        updated = ensure_mdc_frontmatter(updated)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(normalize_newlines(updated), encoding="utf-8")
    return "updated" if existed else "generated"


def upsert_section(content: str, projection: str) -> str:
    start = content.find(MARKER_START)
    end = content.find(MARKER_END, start if start != -1 else 0)
    if start != -1 and end != -1 and end > start:
        end += len(MARKER_END)
        if end < len(content) and content[end] == "\r":
            end += 1
        if end < len(content) and content[end] == "\n":
            end += 1
        return content[:start] + projection + content[end:]
    if content and not content.endswith("\n"):
        content += "\n"
    return content + ("\n" if content else "") + projection


def remove_stale_sections(root: Path, active: Path, init_options: dict[str, Any], state: dict[str, Any]) -> None:
    paths = {root / "AGENTS.md"}
    for value in CONTEXT_FILES.values():
        target = safe_project_path(root, value)
        if target is not None:
            paths.add(target)
    init_target = safe_project_path(root, init_options.get("context_file"))
    if init_target is not None:
        paths.add(init_target)
    for path in paths:
        if same_path(path, active):
            continue
        remove_section(path)


def remove_section(path: Path) -> None:
    if not path.exists():
        return
    content = path.read_text(encoding="utf-8-sig")
    start = content.find(MARKER_START)
    end = content.find(MARKER_END, start if start != -1 else 0)
    if start == -1 or end == -1 or end <= start:
        return
    removal_end = end + len(MARKER_END)
    if removal_end < len(content) and content[removal_end] == "\r":
        removal_end += 1
    if removal_end < len(content) and content[removal_end] == "\n":
        removal_end += 1
    removal_start = start
    if removal_start > 1 and content[removal_start - 1] == "\n" and content[removal_start - 2] == "\n":
        removal_start -= 1
    updated = normalize_newlines(content[:removal_start] + content[removal_end:])
    if not updated.strip() or (path.suffix == ".mdc" and re.match(r"^---\n.*?\n---\s*$", updated, re.DOTALL)):
        path.unlink()
    else:
        path.write_text(updated, encoding="utf-8")


def governance_source(root: Path, target: Path) -> tuple[str, str]:
    managed = extract_managed_section(target)
    if managed:
        return managed, "active generated section"
    memory = root / MEMORY_PATH
    try:
        return normalize_newlines(memory.read_text(encoding="utf-8-sig")), "initialization cache"
    except (OSError, UnicodeDecodeError):
        return "", "built-in defaults"


def section_or_default(source_text: str, headings: list[str], default: list[str]) -> list[str]:
    for heading in headings:
        section = extract_section_from_text(source_text, heading)
        if section:
            return section
    return default


def repository_evidence_default() -> list[str]:
    return ["- none captured"]


def vertical_ssot_evidence_default() -> list[str]:
    return [
        "- Architecture evidence: none detected",
        "- Engineering evidence: none detected",
        "- Code Style evidence: none detected",
        "- Directory Structure evidence: none detected",
        "- Toolchain evidence: none detected",
        "- Agent Harness evidence: none detected",
    ]


def repository_areas_default() -> list[str]:
    return ["- none detected"]


def directory_governance_default() -> list[str]:
    return [
        "- Responsibility: one primary purpose per directory.",
        "- Depth: 2.",
        "- Coverage: include visible, hidden, generated, cache, config/env, tool, and agent directories.",
        "- Mixed concerns: follow existing repo convention or split responsibility.",
        "- Change impact: review linked code, tests, docs, config/env, data, assets, generated files, and tool outputs; update only when in scope and authorized.",
    ]


def development_commands_default() -> list[str]:
    return ["- none recorded"]


def vertical_ssot_registry_default() -> list[str]:
    return [
        "- Architecture SSOT: owns architecture boundaries, interfaces, dependencies, runtime constraints, deployment assumptions, and scenario-level architecture decisions.",
        "- Engineering SSOT: owns branch, version, release, CI/CD, and collaboration process.",
        "- Code Style SSOT: owns naming, formatting, comments, error handling, logging, tests, and quality standards.",
        "- Directory Structure SSOT: owns directory layout, file placement, module organization, and configuration locations.",
        "- Toolchain SSOT: owns standard tools, command entrypoints, configuration templates, and execution constraints.",
        "- Agent Harness SSOT: owns agent task boundaries, tool usage, permissions, audit, validation, and failure handling.",
    ]


def missing_ssot_handling_default() -> list[str]:
    return [
        "- If a vertical SSOT is missing or incomplete, infer temporary guidance from current repository evidence.",
        "- Mark inferred guidance as pending SSOT solidification.",
        "- Do not present inferred guidance as an approved repository rule.",
        "- Do not let inference override explicit SSOT content.",
    ]


def extract_section(path: Path, heading: str) -> list[str]:
    try:
        return extract_section_from_text(path.read_text(encoding="utf-8-sig"), heading)
    except (OSError, UnicodeDecodeError):
        return []


def extract_managed_section(path: Path) -> str:
    try:
        content = normalize_newlines(path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeDecodeError):
        return ""
    start = content.find(MARKER_START)
    end = content.find(MARKER_END, start if start != -1 else 0)
    if start == -1 or end == -1 or end <= start:
        return ""
    return content[start + len(MARKER_START) : end]


def extract_section_from_text(text: str, heading: str) -> list[str]:
    lines = normalize_newlines(text).splitlines()
    capture = False
    result: list[str] = []
    for line in lines:
        if line.strip() == heading:
            capture = True
            continue
        if capture and line.startswith("## "):
            break
        if capture and line.strip():
            result.append(line)
    return result


def projection_style(path: Path) -> str:
    rel_path = path.as_posix()
    if rel_path.endswith(".github/copilot-instructions.md"):
        return "copilot"
    if path.suffix == ".mdc" or "/rules/" in rel_path:
        return "rule"
    return "agent"


def style_lead(style: str) -> str:
    if style == "copilot":
        return "Use these as concise Copilot custom instructions for this repository."
    if style == "rule":
        return "Apply these repository rules before planning, editing, or using tools."
    return "Follow these repository instructions when working in this project."


def write_boundary_default(style: str) -> list[str]:
    if style == "rule":
        return [
            "- Stay inside the active task scope.",
            "- Preserve user-authored edits.",
            "- Preserve managed markers verbatim: `<!-- SPECKIT GOVERNANCE START -->` and `<!-- SPECKIT GOVERNANCE END -->`.",
        ]
    return [
        "- Keep edits inside the active task scope and preserve user changes.",
        "- Preserve managed markers verbatim: `<!-- SPECKIT GOVERNANCE START -->` and `<!-- SPECKIT GOVERNANCE END -->`.",
    ]


def mcp_default(style: str) -> list[str]:
    return ["- Read-only unless the user authorizes mutation.", "- External writes: target, action, expected effect."]


def skill_default(style: str) -> list[str]:
    return [
        "- Use active skill `SKILL.md`.",
        "- Write scope: declared skill paths only.",
        "- Repository-local skill specs should declare purpose, trigger, allowed read paths, allowed write paths, forbidden paths, outputs, and validation command.",
    ]


def handoff_default(style: str) -> list[str]:
    return ["- changed files", "- commands run", "- validation result", "- unresolved risks"]


def scan_feature_specs(root: Path) -> list[str]:
    specs = root / "specs"
    if not specs.is_dir():
        return []
    entries: list[str] = []
    for feature in sorted(path for path in specs.iterdir() if path.is_dir()):
        statuses = [f"{name}:{'present' if (feature / name).exists() else 'missing'}" for name in ("spec.md", "plan.md", "tasks.md")]
        entries.append(f"{rel(root, feature)} ({', '.join(statuses)})")
    return entries


def scan_skills(root: Path) -> list[str]:
    return sorted(rel(root, path) for path in root.rglob("SKILL.md") if not ignored(path))


def skill_capability_lines(root: Path) -> list[str]:
    lines: list[str] = []
    for path_text in scan_skills(root):
        path = root / path_text
        fields = skill_frontmatter(path)
        name = fields.get("name") or fallback_skill_name(path_text)
        description = fields.get("description") or f"Repository-local skill spec at {path_text}."
        lines.extend(
            [
                f"- Repository capability: {name}",
                f"  - Scenario: {description}",
                f"  - Source: `{path_text}`.",
                "  - Runtime action: read matching skill before planning or editing.",
            ]
        )
    return lines


def skill_frontmatter(path: Path) -> dict[str, str]:
    try:
        lines = normalize_newlines(path.read_text(encoding="utf-8-sig")).splitlines()
    except (OSError, UnicodeDecodeError):
        return {}
    if not lines or lines[0].strip() != "---":
        return {}
    fields: dict[str, str] = {}
    for line in lines[1:]:
        if line.strip() == "---":
            break
        key, separator, value = line.partition(":")
        if not separator:
            continue
        key = key.strip()
        value = value.strip().strip("'\"")
        if key in {"name", "description"} and value:
            fields[key] = value
    return fields


def fallback_skill_name(path_text: str) -> str:
    parent = Path(path_text).parent.name
    return parent or path_text.replace("/", "-")


def capability_index_lines(root: Path) -> list[str]:
    mcp_configs = scan_mcp_configs(root)
    mcp_sources = format_values(mcp_configs) if mcp_configs else "none detected"
    lines = skill_capability_lines(root)
    lines.extend(
        [
            "- Repository capability: MCP-backed external tools",
            f"  - Sources: MCP config candidates are evidence, not proof of active tools: {mcp_sources}.",
            "  - Runtime action: enumerate available servers, resources, and tools before use.",
        ]
    )
    return lines


def agent_adapter_lines(root: Path, target: Path, integration: str) -> list[str]:
    lines = [
        "- Repository Capability layer: abstract repository-local abilities and evidence independent of agent runtime.",
        "- Agent Adapter layer: translate repository capabilities into platform-specific discovery and activation rules.",
        "- Platform Projection layer: render the active context target without claiming unavailable platform support.",
        f"- Active integration: {integration}",
        f"- Context target: {rel(root, target)}",
    ]
    if integration == "codex":
        lines.extend(
            [
                "- Skill discovery: repository-local `SKILL.md` capability specs, sorted by path.",
                "- MCP discovery: platform runtime enumeration first; repository config candidates are evidence only unless supported by this adapter.",
            ]
        )
    else:
        lines.extend(
            [
                "- Skill discovery: evidence-only repository scan; platform activation is integration-specific.",
                "- MCP discovery: platform-specific; repository config candidates are evidence only.",
            ]
        )
    return lines


def scan_mcp_configs(root: Path) -> list[str]:
    names = {".mcp.json", "mcp.json", "mcp.yml", "mcp.yaml", "mcp.config.json"}
    return sorted(
        rel(root, path)
        for path in root.rglob("*")
        if path.is_file() and not ignored(path) and path.name in names
    )


def ignored(path: Path) -> bool:
    return any(part in {".git", "__pycache__", ".venv", "node_modules"} for part in path.parts)


def extensions_status(root: Path) -> str:
    path = root / ".specify/extensions.yml"
    if not path.exists():
        return "missing"
    return "present"


def exists(root: Path, value: str) -> str:
    return "present" if (root / value).exists() else "missing"


def ensure_mdc_frontmatter(content: str) -> str:
    stripped = content.lstrip()
    if not stripped.startswith("---"):
        return "---\nalwaysApply: true\n---\n\n" + content
    match = re.match(r"^(---[ \t]*\n)(.*?)(\n---[ \t]*)(\n|$)(.*)", stripped, re.DOTALL)
    if not match:
        return "---\nalwaysApply: true\n---\n\n" + content
    opening, frontmatter, closing, sep, rest = match.groups()
    if re.search(r"(?m)^[ \t]*alwaysApply[ \t]*:[ \t]*true[ \t]*$", frontmatter):
        return content
    if re.search(r"(?m)^[ \t]*alwaysApply[ \t]*:", frontmatter):
        frontmatter = re.sub(r"(?m)^([ \t]*)alwaysApply[ \t]*:.*$", r"\1alwaysApply: true", frontmatter, count=1)
    elif frontmatter.strip():
        frontmatter += "\nalwaysApply: true"
    else:
        frontmatter = "alwaysApply: true"
    return f"{opening}{frontmatter}{closing}{sep}{rest}"


def same_path(left: Path, right: Path) -> bool:
    try:
        return left.resolve(strict=False) == right.resolve(strict=False)
    except OSError:
        return left.absolute() == right.absolute()


def rel(root: Path, path: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def normalize_newlines(content: str) -> str:
    return content.replace("\r\n", "\n").replace("\r", "\n")


if __name__ == "__main__":
    raise SystemExit(main())
