# Project Evaluation: Spec-Kit vs Autospec

## Initial State

The workspace `Spec Driven Vive Coding` (mapped to `spec-kit`) acts as the main project root.

- Root contains `spec-kit` structure (`pyproject.toml`, `scripts/`, `templates/`, `openspec/`).
- `frameworks/autospec` contains a nested Git repository of the `autospec` Go-based CLI tool.
- The user expressed that both projects serve the same purpose and requested advice on whether to separate or archive one.

## Analysis

1.  **Spec-Kit (Root)**:
    - Type: Methodology / Framework (Python/Bash based).
    - Purpose: Defines the "Spec-Driven Development" methodology, provides Markdown templates (`templates/`) and Bash scripts (`scripts/`).
    - Status: Acts as the container for the user's project work (e.g. `openspec/`).
    - Workflow: Manual or Script-driven, uses Markdown files.

2.  **Autospec (Nested in `frameworks/`)**:
    - Type: Tool / CLI (Go based).
    - Purpose: Automates the "Spec-Driven" workflow using structured YAML artifacts (`spec.yaml`, `plan.yaml`) and interactive CLI commands.
    - Status: Nested repository. Likely cloned for testing or usage.
    - Workflow: Automated CLI, uses YAML files.

## Recommendation

The two projects represent different implementations/evolution stages of the same methodology:

- `autospec` is a dedicated **tool** (CLI) to _manage_ the workflow.
- `spec-kit` is the **project structure** and methodology documentation.

**Conflict**:

- `spec-kit` uses Markdown templates by default.
- `autospec` uses YAML artifacts.
- Keeping the _source code_ of the `autospec` tool inside the `spec-kit` project is antipattern (unless developing the tool itself).

**Action Plan**:

1.  **Separate**: Move `frameworks/autospec` out of this workspace (e.g., to `~/dev/autospec`). It is a tool to be installed, not a project component.
2.  **Install Tool**: If the user prefers the automated CLI workflow, install `autospec` to the system path.
3.  **Choose Workflow**:
    - **Option A (Modern/Automated)**: Use `autospec` CLI. This requires adopting the YAML-based structure.
    - **Option B (Classic/Simple)**: Use `spec-kit` scripts/Markdown.
4.  **Cleanup**: Archive/Delete the one not chosen from the workspace to avoid confusion.

## Summary of Changes

- Analyzed both projects.
- Created this report.
