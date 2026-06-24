"""Quality guards for 4+1 architecture templates and command."""
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
ARCHITECTURE_EXTENSION = PROJECT_ROOT / "extensions" / "arch"
TEMPLATES = ARCHITECTURE_EXTENSION / "templates"
COMMANDS = ARCHITECTURE_EXTENSION / "commands"


def _read_template(name: str) -> str:
    return (TEMPLATES / name).read_text(encoding="utf-8")


def test_arch_commands_are_split_by_view_and_bootstrap_setup():
    command_files = sorted(COMMANDS.glob("speckit.arch.*.md"))

    assert [path.name for path in command_files] == [
        "speckit.arch.development-generate.md",
        "speckit.arch.development-reverse.md",
        "speckit.arch.logical-generate.md",
        "speckit.arch.logical-reverse.md",
        "speckit.arch.physical-generate.md",
        "speckit.arch.physical-reverse.md",
        "speckit.arch.process-generate.md",
        "speckit.arch.process-reverse.md",
        "speckit.arch.scenario-generate.md",
        "speckit.arch.scenario-reverse.md",
    ]

    for command_file in command_files:
        content = command_file.read_text(encoding="utf-8")
        assert "scripts:" in content
        assert ".specify/extensions/arch/scripts/bash/setup-arch.sh --json" in content
        assert ".specify/extensions/arch/scripts/powershell/setup-arch.ps1 -Json" in content
        assert "ARCH_SCHEMA_FILE" in content
        assert "Synthesis Readiness" in content
        assert "NEEDS ARCH UPDATE" in content
        assert ".specify/memory/architecture/" not in content
        assert "__SPECKIT_COMMAND_UC__" not in content


def test_arch_generate_and_reverse_commands_keep_distinct_evidence_boundaries():
    for command_file in COMMANDS.glob("speckit.arch.*-generate.md"):
        content = command_file.read_text(encoding="utf-8")
        assert "Do not read, populate, or update `REPO_FACTS_FILE`" in content
        assert "record" in content
        assert "instead of inventing" in content

    for command_file in COMMANDS.glob("speckit.arch.*-reverse.md"):
        content = command_file.read_text(encoding="utf-8")
        assert "observable repository" in content
        assert "REPO_FACTS_FILE" in content
        assert "Every non-placeholder fact must name an evidence source" in content
        assert "Architecture conclusions must trace to repo facts" in content


def test_architecture_synthesis_references_five_view_files():
    content = _read_template("architecture-template.md")

    for filename in [
        "architecture-scenario-view.md",
        "architecture-logical-view.md",
        "architecture-process-view.md",
        "architecture-development-view.md",
        "architecture-physical-view.md",
    ]:
        assert f".specify/memory/{filename}" in content
    assert "Cross-View Architecture Model" in content
    assert "normalizes the 4+1 design results into the architecture SSOT" in content
    assert "This is architecture design synthesis, not tracking or audit" in content
    assert "Do not treat view-specific concepts as equivalent or interchangeable" in content
    assert "Key Architecture Conclusions" in content
    for section in [
        "Architecture Intent",
        "Central Design Forces",
        "Primary Tradeoffs",
        "Stable Boundaries",
        "Change Axes",
        "Anti-patterns",
    ]:
        assert section in content
    assert ".specify/memory/architecture/" not in content


def test_init_next_steps_do_not_list_arch_as_core_workflow():
    init_source = (PROJECT_ROOT / "src" / "specify_cli" / "commands" / "init.py").read_text(
        encoding="utf-8"
    )

    assert "_display_cmd('arch')" not in init_source
    assert 'DEFAULT_BUNDLED_EXTENSIONS = ("arch", "discovery", "intake", "preview", "repository-governance")' in init_source
    assert "specify extension add arch" not in init_source


def test_view_templates_define_inputs_and_reject_implementation_detail():
    scenario = _read_template("architecture-scenario-template.md")
    logical = _read_template("architecture-logical-template.md")
    process = _read_template("architecture-process-template.md")
    development = _read_template("architecture-development-template.md")
    physical = _read_template("architecture-physical-template.md")

    assert "Produce the UC semantics" in scenario
    assert "Do not write architecture components" in scenario
    assert "**Input**: `.specify/memory/architecture-scenario-view.md`" in logical
    assert "Do not write classes, DTOs, database tables" in logical
    assert "**Input**: `.specify/memory/architecture-scenario-view.md`, `.specify/memory/architecture-logical-view.md`" in process
    assert "Do not write call stacks, queue names, retry counts" in process
    assert "**Input**: `.specify/memory/architecture-logical-view.md`, `.specify/memory/architecture-process-view.md`" in development
    assert "Do not write source file paths, concrete package trees" in development
    assert "**Input**: `.specify/memory/architecture-process-view.md`, `.specify/memory/architecture-development-view.md`" in physical
    assert "Do not write Kubernetes YAML, cloud resource manifests" in physical

    for content in [scenario, logical, process, development, physical]:
        for section in [
            "Architecture Intent",
            "Core Tensions",
            "Stable Boundaries",
            "Change Axes",
            "Invariants",
            "Non-goals / Anti-patterns",
        ]:
            assert section in content


def test_view_templates_keep_notations_out_of_reasoning_contracts():
    view_contents = [
        _read_template("architecture-scenario-template.md"),
        _read_template("architecture-logical-template.md"),
        _read_template("architecture-process-template.md"),
        _read_template("architecture-development-template.md"),
        _read_template("architecture-physical-template.md"),
    ]

    notation_terms = ["C4", "UML", "Mermaid", "PlantUML", "notation-specific"]
    for content in view_contents:
        for term in notation_terms:
            assert term not in content
