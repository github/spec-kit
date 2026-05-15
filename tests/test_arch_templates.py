"""Quality guards for 4+1 architecture templates and command."""

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
TEMPLATES = PROJECT_ROOT / "templates"


def _read_template(name: str) -> str:
    return (TEMPLATES / name).read_text(encoding="utf-8")


def test_arch_command_is_phase_based_and_does_not_require_uc_command():
    content = _read_template("commands/arch.md")

    assert "scripts:" in content
    assert "setup-arch.sh --json" in content
    assert "setup-arch.ps1 -Json" in content
    for phase in [
        "Phase 0: Scenario View",
        "Phase 1: Logical View",
        "Phase 2: Process View",
        "Phase 3: Development View",
        "Phase 4: Physical View",
        "Phase 5: Architecture Synthesis",
    ]:
        assert phase in content
    assert "Do not require `.specify/memory/uc.md`" in content
    assert "__SPECKIT_COMMAND_UC__" not in content
    assert "Read `.specify/memory/constitution.md`" not in content
    assert ".specify/memory/architecture/" not in content


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
    assert "Cross-View Mapping" in content
    assert "Key Architecture Conclusions" in content
    assert ".specify/memory/architecture/" not in content


def test_init_next_steps_place_arch_before_constitution():
    init_source = (PROJECT_ROOT / "src" / "specify_cli" / "__init__.py").read_text(encoding="utf-8")

    arch_index = init_source.index("_display_cmd('arch')")
    constitution_index = init_source.index("_display_cmd('constitution')")

    assert arch_index < constitution_index


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
