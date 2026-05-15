"""Quality guards for 4+1 architecture templates and command."""

import re
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
ARCHITECTURE_EXTENSION = PROJECT_ROOT / "extensions" / "arch"
TEMPLATES = ARCHITECTURE_EXTENSION / "templates"
COMMANDS = ARCHITECTURE_EXTENSION / "commands"


def _read_template(name: str) -> str:
    return (TEMPLATES / name).read_text(encoding="utf-8")


def test_arch_command_is_phase_based_and_does_not_require_uc_command():
    content = (COMMANDS / "speckit.arch.generate.md").read_text(encoding="utf-8")

    assert "scripts:" in content
    assert ".specify/extensions/arch/scripts/bash/setup-arch.sh --json" in content
    assert ".specify/extensions/arch/scripts/powershell/setup-arch.ps1 -Json" in content
    for phase in [
        "Phase -1: Architecture Framing",
        "Phase 0: Scenario View",
        "Phase 1: Logical View",
        "Phase 2: Process View",
        "Phase 3: Development View",
        "Phase 4: Physical View",
        "Phase 5: Architecture Synthesis",
    ]:
        assert phase in content
    assert "Before filling any view, identify the architecture judgment" in content
    assert "Architecture Reasoning Layer" in content
    assert "Representation Layer" in content
    assert "project-level architecture SSOT" in content
    assert "constrain later `plan` reasoning to stay inside the architecture SSOT" in content
    assert "Use each view template as the source of truth for that view's reasoning contract" in content
    assert "Produce architecture design inference, not tracking, audit, or implementation planning" in content
    assert "normalizes architecture meaning for synthesis and later `plan` reasoning" in content
    assert "Markdown tables are the default artifact structure" in content
    assert "Optional diagrams are renderings, not reasoning inputs" in content
    assert "Add optional diagrams only after the relevant view's reasoning is complete" in content
    assert "Defer any optional diagram or notation-specific rendering until the affected view's 4+1 reasoning" in content
    assert "Representation choices:" not in content
    assert "Before filling tables" not in content
    assert "Architecture Gates" in content
    assert "ERROR if a boundary has responsibilities but no explicit non-responsibility" in content
    assert "ERROR if notation-specific output changes 4+1 view responsibilities" in content
    assert "Use Case, Domain Object, Component, Container, or Deployment Unit" in content
    for term in ["C4", "UML", "Mermaid", "PlantUML"]:
        assert len(re.findall(rf"\b{re.escape(term)}\b", content)) == 1
    assert "Do not require `.specify/memory/uc.md`" in content
    assert "Read the six architecture templates under `.specify/extensions/arch/templates/`" in content
    assert "__SPECKIT_COMMAND_UC__" not in content
    assert "Read `.specify/memory/constitution.md`" not in content
    assert ".specify/memory/architecture/" not in content


def test_arch_command_delegates_view_details_to_templates():
    content = (COMMANDS / "speckit.arch.generate.md").read_text(encoding="utf-8")

    delegated_phrases = [
        "using its template",
        "following the scenario view template",
        "following the logical view template",
        "following the process view template",
        "following the development view template",
        "following the physical view template",
        "following the synthesis template",
    ]
    for phrase in delegated_phrases:
        assert phrase in content

    template_owned_details = [
        "Actors and external participants",
        "System capability boundaries",
        "Main runtime links",
        "Architecture-level components or capability packages",
        "Deployment and hosting boundaries",
        "Do not write class models",
        "Do not write call stacks",
        "Do not write Kubernetes YAML",
    ]
    for phrase in template_owned_details:
        assert phrase not in content


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
    assert "normalizes the 4+1 design results into the architecture SSOT for later `plan` reasoning" in content
    assert "This is architecture design synthesis, not tracking or audit" in content
    assert "Do not treat view-specific concepts as equivalent or interchangeable" in content
    assert "Plan Reasoning Constraint" in content
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
    init_source = (PROJECT_ROOT / "src" / "specify_cli" / "__init__.py").read_text(encoding="utf-8")

    assert "_display_cmd('arch')" not in init_source
    assert "specify extension add arch" in init_source


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
