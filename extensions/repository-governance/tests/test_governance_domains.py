import importlib.util
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "templates" / "repository-governance-template.md"
SCRIPT = ROOT / "scripts" / "refresh_repository_governance.py"
README = ROOT / "README.md"
COMMAND = ROOT / "commands" / "speckit.repository-governance.refresh.md"
EXTENSION = ROOT / "extension.yml"
EXTENSION_IGNORE = ROOT / ".extensionignore"


def load_refresh_module():
    spec = importlib.util.spec_from_file_location("refresh_repository_governance", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def assert_repository_governance_framework(text: str) -> None:
    assert "Repository Governance Framework" in text
    assert "Vertical SSOT Registry" in text
    assert "Architecture SSOT" in text
    assert "Engineering SSOT" in text
    assert "Code Style SSOT" in text
    assert "Directory Structure SSOT" in text
    assert "Toolchain SSOT" in text
    assert "Agent Harness SSOT" in text
    assert "architecture methodology: owned by Architecture SSOT" in text
    assert "4+1" not in text


def assert_vertical_ssot_evidence(text: str) -> None:
    assert "## Vertical SSOT Evidence" in text
    assert "- Architecture evidence:" in text
    assert "- Engineering evidence:" in text
    assert "- Code Style evidence:" in text
    assert "- Directory Structure evidence:" in text
    assert "- Toolchain evidence:" in text
    assert "- Agent Harness evidence:" in text


def test_template_defines_repository_governance_framework_ssot():
    text = TEMPLATE.read_text(encoding="utf-8")

    assert_repository_governance_framework(text)


def test_template_declares_final_outputs_without_placeholders():
    text = TEMPLATE.read_text(encoding="utf-8")

    assert "## Final Output" in text
    assert "active repository governance file" in text
    assert "cache: internal" in text
    assert "TODO(" not in text
    final_outputs = text.split("## Final Output", 1)[1].split("## Scope", 1)[0]
    assert "- active repository governance file" in final_outputs
    assert "- cache: internal" in final_outputs


def test_template_protects_refresh_markers_and_scopes_broad_updates():
    text = TEMPLATE.read_text(encoding="utf-8")

    assert "`<!-- SPECKIT GOVERNANCE START -->`" in text
    assert "`<!-- SPECKIT GOVERNANCE END -->`" in text
    assert "Repository-local skill specs should declare" in text
    assert "Required fields: purpose" not in text
    assert "update only when in scope and authorized" in text
    assert "Change impact: update linked code" not in text


def test_readme_positions_extension_as_repository_governance_framework():
    text = README.read_text(encoding="utf-8")

    assert "Generate the active Repository Governance Framework SSOT section." in text
    assert "Active target file from Spec Kit integration metadata." in text
    assert "Example:" not in text
    assert "Codex `AGENTS.md`" not in text
    assert "not a general-purpose `AGENTS.md` initializer" not in text


def test_usage_is_single_command_generate_or_update_flow():
    readme = README.read_text(encoding="utf-8")
    command = COMMAND.read_text(encoding="utf-8")

    assert "Generate missing target governance file." in readme
    assert "Update existing target governance file." in readme
    assert "review and edit the memory file" not in readme
    assert "run the refresh command again" not in readme
    assert "Review only the active target file." in readme
    assert "Preserve managed markers verbatim." in readme
    assert "Use existing managed section as refresh source." in command
    assert "Preserve managed markers verbatim." in command
    assert "generated or updated" in command
    assert "inserted or replaced" not in command


def test_write_projection_reports_generated_or_updated(tmp_path):
    module = load_refresh_module()
    target = tmp_path / "AGENTS.md"

    generated = module.write_projection(target, "new governance")
    target.write_text("existing governance", encoding="utf-8")
    updated = module.write_projection(target, "updated governance")

    assert generated == "generated"
    assert updated == "updated"


def test_cli_report_prioritizes_active_target_and_labels_cache_internal(tmp_path):
    extension_root = tmp_path / ".specify" / "extensions" / "repository-governance"
    (extension_root / "scripts").mkdir(parents=True)
    (extension_root / "templates").mkdir(parents=True)
    shutil.copy2(SCRIPT, extension_root / "scripts" / "refresh_repository_governance.py")
    shutil.copy2(TEMPLATE, extension_root / "templates" / "repository-governance-template.md")
    (tmp_path / ".specify" / "integration.json").write_text(
        '{"default_integration":"codex","installed_integrations":["codex"]}',
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, ".specify/extensions/repository-governance/scripts/refresh_repository_governance.py"],
        cwd=tmp_path,
        text=True,
        capture_output=True,
        check=False,
    )
    lines = result.stdout.splitlines()

    assert result.returncode == 0, result.stderr
    assert lines[0] == "Target governance file: AGENTS.md"
    assert lines[1] == "Governance file: generated"
    assert "Review target: AGENTS.md" in lines
    assert any(line.startswith("Internal initialization cache: ") for line in lines)
    assert not any(line.startswith("Source memory: ") for line in lines)
    assert not any(line.startswith("Memory: ") for line in lines)


def test_write_projection_preserves_user_authored_content(tmp_path):
    module = load_refresh_module()
    target = tmp_path / "AGENTS.md"
    target.write_text(
        "\n".join(
            [
                "# Project Instructions",
                "",
                "Keep this user-authored introduction.",
                "",
                module.MARKER_START,
                "old generated content",
                module.MARKER_END,
                "",
                "Keep this user-authored footer.",
            ]
        ),
        encoding="utf-8",
    )

    action = module.write_projection(
        target,
        "\n".join([module.MARKER_START, "new generated content", module.MARKER_END, ""]),
    )
    text = target.read_text(encoding="utf-8")

    assert action == "updated"
    assert "Keep this user-authored introduction." in text
    assert "Keep this user-authored footer." in text
    assert "new generated content" in text
    assert "old generated content" not in text


def test_remove_stale_sections_when_active_target_changes(tmp_path):
    module = load_refresh_module()
    old_target = tmp_path / "AGENTS.md"
    active_target = tmp_path / "CLAUDE.md"
    old_target.write_text(
        "\n".join(
            [
                "# Existing Codex Context",
                "",
                "User content stays.",
                "",
                module.MARKER_START,
                "stale generated content",
                module.MARKER_END,
                "",
            ]
        ),
        encoding="utf-8",
    )
    active_target.write_text("# Claude Context\n", encoding="utf-8")

    module.remove_stale_sections(
        tmp_path,
        active_target,
        {},
        {"default_integration": "claude", "installed_integrations": ["codex", "claude"]},
    )
    old_text = old_target.read_text(encoding="utf-8")

    assert "User content stays." in old_text
    assert module.MARKER_START not in old_text
    assert "stale generated content" not in old_text


def test_resolve_target_uses_spec_kit_integration_metadata(tmp_path):
    module = load_refresh_module()

    assert module.resolve_target(tmp_path, {"default_integration": "codex"}, {}) == tmp_path / "AGENTS.md"
    assert module.resolve_target(tmp_path, {"default_integration": "claude"}, {}) == tmp_path / "CLAUDE.md"
    assert module.resolve_target(tmp_path, {"default_integration": "cursor-agent"}, {}) == tmp_path / ".cursor/rules/specify-rules.mdc"
    assert module.resolve_target(
        tmp_path,
        {"default_integration": "codex"},
        {"context_file": "custom/AGENT_RULES.md"},
    ) == tmp_path / "custom/AGENT_RULES.md"


def test_projection_defines_repository_governance_framework_ssot(tmp_path):
    module = load_refresh_module()
    root = tmp_path
    memory = root / ".specify" / "memory"
    memory.mkdir(parents=True)
    (memory / "repository-governance.md").write_text(TEMPLATE.read_text(encoding="utf-8"), encoding="utf-8")

    projection = module.render_projection(root, root / "AGENTS.md", {"default_integration": "codex"}, False)

    assert_repository_governance_framework(projection)
    assert_vertical_ssot_evidence(projection)
    assert "Constitution" not in projection
    assert "## Repository Governance" in projection
    assert "- SSOT: this managed section." in projection
    assert "Repository governance SSOT: `.specify/memory/repository-governance.md`" not in projection
    assert "`.specify/memory/repository-governance.md` is the SSOT" not in projection
    assert "Generated Governance Boundaries" not in projection
    assert "agent-governance refresh command may create" not in projection
    assert "This generated section" not in projection
    assert "Initialization Evidence Cache:" not in projection
    assert "## Governance Domains" not in projection
    assert "## Resolved Repository Context" not in projection


def test_projection_includes_repository_evidence_and_development_commands(tmp_path):
    module = load_refresh_module()
    root = tmp_path
    memory = root / ".specify" / "memory"
    memory.mkdir(parents=True)
    (memory / "repository-governance.md").write_text(
        "\n".join(
            [
                "# Repository Governance",
                "",
                "## Repository Evidence",
                "",
                "- README: `README.md`",
                "- Source paths: `src/`",
                "- Test paths: `tests/`",
                "",
                "## Vertical SSOT Evidence",
                "",
                "- Architecture evidence: `src/`",
                "- Engineering evidence: `package.json`",
                "- Code Style evidence: `eslint.config.js`",
                "- Directory Structure evidence: `src/`",
                "- Toolchain evidence: `package.json`",
                "- Agent Harness evidence: `AGENTS.md`",
                "",
                "## Development Commands",
                "",
                "- `npm test` -> `vitest run`",
                "- manifest commands over ad hoc equivalents",
                "",
                "## Write Boundaries",
                "",
                "- Preserve user-authored content outside managed markers.",
            ]
        ),
        encoding="utf-8",
    )

    projection = module.render_projection(root, root / "AGENTS.md", {"default_integration": "codex"}, False)

    assert "## Repository Evidence" in projection
    assert "- README: `README.md`" in projection
    assert "- Source paths: `src/`" in projection
    assert "## Vertical SSOT Evidence" in projection
    assert "- Architecture evidence: `src/`" in projection
    assert "## Development Commands" in projection
    assert "- `npm test` -> `vitest run`" in projection


def test_repository_areas_scan_two_directory_levels_including_hidden_and_cache_dirs(tmp_path):
    module = load_refresh_module()
    root = tmp_path
    for path in (
        "docs/reference",
        "src/pipeline/deep/ignored",
        "tests/browser",
        "node_modules/package",
        ".git/hooks",
    ):
        (root / path).mkdir(parents=True)
    (root / ".specify" / "extensions" / "repository-governance" / "templates").mkdir(parents=True)
    (root / ".specify" / "extensions" / "repository-governance" / "templates" / "repository-governance-template.md").write_text(
        TEMPLATE.read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    (root / ".specify" / "integration.json").write_text('{"default_integration": "codex"}', encoding="utf-8")

    module.ensure_memory(root)
    projection = module.render_projection(root, root / "AGENTS.md", {"default_integration": "codex"}, True)
    areas = projection.split("## Repository Areas", 1)[1].split("## Development Commands", 1)[0]

    assert "## Repository Areas" in projection
    assert "- `docs/`: review before changing linked areas." in areas
    assert "- `docs/reference/`: change with parent area `docs/`." in areas
    assert "- `src/`: review before changing linked areas." in areas
    assert "- `src/pipeline/`: change with parent area `src/`." in areas
    assert "- `tests/`: review before changing linked areas." in areas
    assert "- `tests/browser/`: change with parent area `tests/`." in areas
    assert "- `.git/`: review before changing linked areas." in areas
    assert "- `.git/hooks/`: change with parent area `.git/`." in areas
    assert "- `.specify/`: review before changing linked areas." in areas
    assert "- `.specify/extensions/`: change with parent area `.specify/`." in areas
    assert "- `.specify/memory/`: change with parent area `.specify/`." in areas
    assert "- `node_modules/`: review before changing linked areas." in areas
    assert "- `node_modules/package/`: change with parent area `node_modules/`." in areas
    assert "src/pipeline/deep" not in areas
    assert "math-animation" not in areas
    assert "renderer" not in areas


def test_projection_includes_generic_directory_governance(tmp_path):
    module = load_refresh_module()
    root = tmp_path
    memory = root / ".specify" / "memory"
    memory.mkdir(parents=True)
    (memory / "repository-governance.md").write_text(TEMPLATE.read_text(encoding="utf-8"), encoding="utf-8")

    projection = module.render_projection(root, root / "AGENTS.md", {"default_integration": "codex"}, False)
    directory_governance = projection.split("## Directory Governance", 1)[1].split("## Development Commands", 1)[0]

    assert "## Directory Governance" in projection
    assert "- Responsibility: one primary purpose per directory." in projection
    assert "- Depth: 2." in projection
    assert "- Coverage: include visible, hidden, generated, cache, config/env, tool, and agent directories." in projection
    assert "- Mixed concerns: follow existing repo convention or split responsibility." in projection
    assert "- Change impact: review linked code, tests, docs, config/env, data, assets, generated files, and tool outputs; update only when in scope and authorized." in projection
    assert "Top level: responsibility domain" not in directory_governance
    assert "Level 2: parent-scoped subdomain" not in directory_governance
    assert "source, tests, docs" not in directory_governance
    assert "- Depth: 2." in projection
    assert "Codex" not in projection
    assert "Unity" not in projection


def test_existing_generated_section_is_refresh_source_of_truth(tmp_path):
    module = load_refresh_module()
    root = tmp_path
    memory = root / ".specify" / "memory"
    memory.mkdir(parents=True)
    (memory / "repository-governance.md").write_text(
        "\n".join(
            [
                "# Repository Governance Source",
                "",
                "## Write Boundaries",
                "",
                "- Stale memory write boundary.",
                "",
                "## MCP Policy",
                "",
                "- Stale memory MCP policy.",
            ]
        ),
        encoding="utf-8",
    )
    target = root / "AGENTS.md"
    target.write_text(
        "\n".join(
            [
                module.MARKER_START,
                "## Repository Governance",
                "",
                "## Write Boundaries",
                "- Reviewed active write boundary.",
                "",
                "## MCP And External Tool Policy",
                "- Reviewed active MCP policy.",
                module.MARKER_END,
                "",
            ]
        ),
        encoding="utf-8",
    )

    projection = module.render_projection(root, target, {"default_integration": "codex"}, False)

    assert "- Reviewed active write boundary." in projection
    assert "- Reviewed active MCP policy." in projection
    assert "- Stale memory write boundary." not in projection
    assert "- Stale memory MCP policy." not in projection


def test_projection_authority_order_uses_active_generated_section_not_memory(tmp_path):
    module = load_refresh_module()
    root = tmp_path
    memory = root / ".specify" / "memory"
    memory.mkdir(parents=True)
    (memory / "repository-governance.md").write_text(TEMPLATE.read_text(encoding="utf-8"), encoding="utf-8")

    projection = module.render_projection(root, root / "AGENTS.md", {"default_integration": "codex"}, False)

    assert "2. Safety and permission constraints" in projection
    assert "3. Active `SPECKIT GOVERNANCE` section" in projection
    assert "Repository governance rules from `.specify/memory/repository-governance.md`" not in projection


def test_default_governance_does_not_inject_project_implementation_gate(tmp_path):
    module = load_refresh_module()
    root = tmp_path
    memory = root / ".specify" / "memory"
    memory.mkdir(parents=True)
    (memory / "repository-governance.md").write_text(TEMPLATE.read_text(encoding="utf-8"), encoding="utf-8")

    template = TEMPLATE.read_text(encoding="utf-8")
    projection = module.render_projection(root, root / "AGENTS.md", {"default_integration": "codex"}, False)
    combined = template + "\n" + projection

    assert "required project-governance artifacts" not in combined
    assert "owning project-governance workflow" not in combined
    assert "Non-Negotiable Execution Gates" not in combined
    assert "/speckit.implement" not in combined


def test_usage_is_spec_kit_uv_based():
    readme = README.read_text(encoding="utf-8")
    command = COMMAND.read_text(encoding="utf-8")
    extension = EXTENSION.read_text(encoding="utf-8")

    assert "uv run python" in readme
    assert "uv run python" in command
    assert 'name: "uv"' in extension
    assert "required: true" in extension
    assert "If Python is not available" not in command
    assert 'name: "python3"' not in extension


def test_extension_package_boundary_excludes_development_only_files():
    ignore = set(EXTENSION_IGNORE.read_text(encoding="utf-8").splitlines())

    assert "AGENTS.md" in ignore
    assert "pyproject.toml" in ignore
    assert "uv.lock" in ignore
    assert "tests/" in ignore

    assert "extension.yml" not in ignore
    assert "commands/" not in ignore
    assert "scripts/" not in ignore
    assert "templates/" not in ignore


def test_extension_references_existing_runtime_files():
    extension = EXTENSION.read_text(encoding="utf-8")
    command = COMMAND.read_text(encoding="utf-8")

    assert 'file: "commands/speckit.repository-governance.refresh.md"' in extension
    assert (ROOT / "commands" / "speckit.repository-governance.refresh.md").is_file()
    assert ".specify/extensions/repository-governance/scripts/refresh_repository_governance.py" in command
    assert (ROOT / "scripts" / "refresh_repository_governance.py").is_file()
    assert (ROOT / "templates" / "repository-governance-template.md").is_file()


def test_packaged_runtime_generates_codex_governance_file(tmp_path):
    extension_root = tmp_path / ".specify" / "extensions" / "repository-governance"
    (extension_root / "scripts").mkdir(parents=True)
    (extension_root / "templates").mkdir(parents=True)
    shutil.copy2(SCRIPT, extension_root / "scripts" / "refresh_repository_governance.py")
    shutil.copy2(TEMPLATE, extension_root / "templates" / "repository-governance-template.md")
    (tmp_path / ".specify" / "integration.json").write_text(
        '{"default_integration":"codex","installed_integrations":["codex"]}',
        encoding="utf-8",
    )
    (tmp_path / "README.md").write_text("# Demo\n", encoding="utf-8")
    (tmp_path / "package.json").write_text(
        '{"scripts":{"test":"vitest run","lint":"eslint ."}}',
        encoding="utf-8",
    )
    (tmp_path / "src").mkdir()
    (tmp_path / "tests").mkdir()

    result = subprocess.run(
        [sys.executable, ".specify/extensions/repository-governance/scripts/refresh_repository_governance.py"],
        cwd=tmp_path,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "Target governance file: AGENTS.md" in result.stdout
    assert "Governance file: generated" in result.stdout
    generated = (tmp_path / "AGENTS.md").read_text(encoding="utf-8")
    assert "## Repository Evidence" in generated
    assert "- README: `README.md`" in generated
    assert_vertical_ssot_evidence(generated)
    assert "## Development Commands" in generated
    assert "- `npm test` -> `vitest run`" in generated


def test_vertical_ssot_evidence_extracts_repository_facts(tmp_path):
    module = load_refresh_module()
    root = tmp_path
    (root / ".specify" / "extensions" / "repository-governance" / "templates").mkdir(parents=True)
    (root / ".specify" / "extensions" / "repository-governance" / "templates" / "repository-governance-template.md").write_text(
        TEMPLATE.read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    (root / ".specify" / "integration.json").write_text('{"default_integration": "codex"}', encoding="utf-8")
    (root / ".github" / "workflows").mkdir(parents=True)
    (root / ".github" / "workflows" / "ci.yml").write_text("name: CI\n", encoding="utf-8")
    (root / "src" / "api").mkdir(parents=True)
    (root / "src" / "api" / "routes.py").write_text("@app.route('/health')\ndef health():\n    return 'ok'\n", encoding="utf-8")
    (root / "tests").mkdir()
    (root / "package.json").write_text('{"scripts": {"test": "vitest run"}}', encoding="utf-8")
    (root / "eslint.config.js").write_text("export default [];\n", encoding="utf-8")
    (root / "Dockerfile").write_text("FROM python:3.12\n", encoding="utf-8")
    (root / ".mcp.json").write_text("{}", encoding="utf-8")
    (root / "AGENTS.md").write_text("# Agent rules\n", encoding="utf-8")

    created = module.ensure_memory(root)
    text = (root / ".specify" / "memory" / "repository-governance.md").read_text(encoding="utf-8")

    assert created is True
    assert_vertical_ssot_evidence(text)
    assert "- Architecture evidence: `src/`, `src/api/routes.py`" in text
    assert "- Engineering evidence: `.github/workflows/ci.yml`, `package.json`" in text
    assert "- Code Style evidence: `eslint.config.js`, `tests/`" in text
    assert "- Directory Structure evidence:" in text
    assert "`src/`" in text
    assert "`tests/`" in text
    assert "- Toolchain evidence: `package.json`, `Dockerfile`" in text
    assert "- Agent Harness evidence: `AGENTS.md`, `.mcp.json`" in text


def test_ensure_memory_initializes_from_repository_evidence(tmp_path):
    module = load_refresh_module()
    root = tmp_path
    (root / ".specify" / "extensions" / "repository-governance" / "templates").mkdir(parents=True)
    (root / ".specify" / "extensions" / "repository-governance" / "templates" / "repository-governance-template.md").write_text(
        TEMPLATE.read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    (root / ".specify" / "integration.json").write_text('{"default_integration": "codex"}', encoding="utf-8")
    (root / "README.md").write_text("# Evidence App\n\nA sample Spec Kit app.\n", encoding="utf-8")
    (root / "package.json").write_text(
        '{"scripts": {"test": "vitest run", "lint": "eslint ."}}',
        encoding="utf-8",
    )
    (root / "src").mkdir()
    (root / "tests").mkdir()
    (root / "AGENTS.md").write_text("# Agent Notes\n\nExisting user-authored context.\n", encoding="utf-8")

    created = module.ensure_memory(root)
    text = (root / ".specify" / "memory" / "repository-governance.md").read_text(encoding="utf-8")

    assert created is True
    assert "## Repository Evidence" in text
    assert_vertical_ssot_evidence(text)
    assert "- README: `README.md`" in text
    assert "- Package manifest: `package.json`" in text
    assert "- Test paths: `tests/`" in text
    assert "- Existing agent context files: `AGENTS.md`" in text
    assert "`npm test` -> `vitest run`" in text
    assert "`npm run lint` -> `eslint .`" in text
    assert "TODO(" not in text
