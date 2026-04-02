# Development Guide

This document is the primary entry point for people modifying Spec Kit itself.

Use this guide when you need to understand how the repository fits together, where different kinds of changes belong, how to validate them, and which deeper documents to read next. This document is intentionally focused on system understanding, repository navigation, and change workflows.

## Maintainer Onboarding

**Read the essential project documents**:

| Document                                                     | Focus                                                                                                                         |
| ------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------- |
| [README.md](./README.md)                                     | Primary user-facing entry point and high-level overview of what Spec Kit is, how it is used, and what workflow it supports.   |
| [DEVELOPMENT.md](./DEVELOPMENT.md)                           | Primary maintainer-facing entry point for contributors changing Spec Kit itself.                                              |
| [spec-driven.md](./spec-driven.md)                           | Full conceptual and procedural walkthrough of the Spec-Driven Development workflow supported by Spec Kit.                     |
| [RELEASE-PROCESS.md](./.github/workflows/RELEASE-PROCESS.md) | Release workflow, versioning model, changelog generation, and release-process invariants.                                     |
| [docs/index.md](./docs/index.md)                             | Entry point to the documentation under `docs/`, including installation, quick start, upgrade, and local development guidance. |
| [CONTRIBUTING.md](./CONTRIBUTING.md)                         | Contribution mechanics, review expectations, and required development practices.                                              |
| [TESTING.md](./TESTING.md)                                   | Validation strategy and testing procedures.                                                                                   |

**Inspect the repository layout**:

| Directory          | Role                                                                   |
| ------------------ | ---------------------------------------------------------------------- |
| `templates/`       | Core project framework, LLM templated prompts and associated templates |
| `scripts/`         | Deterministic component of the project framework.                      |
| `src/specify_cli/` | Python sources of `specify` CLI.                                       |
| `extensions/`      | Documentation and associated files for the `extensions` feature.       |
| `presets/`         | Documentation and associated files for the `presets` feature.          |

## What Spec Kit Is, from a Maintainer Perspective

Spec Kit is a toolkit for spec-driven development. It provides a structured workflow, scaffolding assets, and supporting integrations that help users move from an idea to a defined specification, an implementation plan, task breakdowns, and executable project work.

From a maintainer perspective, the repository is not just "documentation" and not just "code". It is a coordinated system composed of several interacting surfaces:

- workflow-defining templates,
- command and scaffolding assets,
- scripts and automation helpers,
- CLI and installation behavior,
- agent-specific integration surfaces,
- extension and preset publishing assets,
- documentation that explains and stabilizes the user and developer model.

Maintaining Spec Kit means preserving coherence across those surfaces. A change in one layer often affects documentation, validation expectations, and user-visible workflow behavior in other layers.

## System Mental Model

### Core User Workflow

At a high level, Spec Kit supports a staged workflow in which a user moves through structured project definition and execution steps. The exact implementation details may vary by agent or integration surface, but the core conceptual flow is consistent:

1. establish or refine governing project principles,
2. define a concrete specification,
3. derive an implementation plan,
4. derive an actionable task breakdown,
5. execute implementation against the defined artifacts.

When changing Spec Kit, first identify which part of that lifecycle your change affects.

### Source Assets vs Generated Project Assets

A useful distinction for maintainers is the difference between:

- **source assets in this repository**, and
- **artifacts that users consume in their own repositories or agent sessions**.

Source assets in this repository define behavior, structure, wording, conventions, and scaffolding rules. Generated or installed assets are the user-facing outputs of those source assets.

When editing repository files, think in terms of downstream consequences:

- What will change in the user-visible workflow?
- What will change in generated project content?
- What must be revalidated manually in a real end-to-end flow?

### Main System Surfaces

Most changes fall into one or more of these surfaces:

- **Templates**: define workflow artifacts, prompts, scaffolding content, and generated project structure.
- **Scripts and automation**: support local generation, packaging, installation, or validation flows.
- **CLI and bootstrap behavior**: define how users initialize, install, or execute Spec Kit workflows.
- **Agent integration surfaces**: adapt the kit to specific agent environments without changing the underlying workflow intent.
- **Extensions and presets**: package additional reusable behavior or opinionated configurations.
- **Documentation**: explain the intended model, workflow, usage, and maintenance practices.

A contributor should be able to identify which surface they are editing before making a change.

## Repository Anatomy

This section explains the role of the major repository areas. It is intended as a guided map, not a full file inventory.

### `templates/`

This directory contains the core workflow and content assets that shape the user experience. In many cases, this is the most important part of the repository because it defines the structure and wording of the spec-driven workflow itself.

Edit `templates/` when you are changing:

- generated artifact structure,
- workflow prompt wording,
- command or template content,
- default project scaffolding semantics.

Treat template changes as behavior changes, not as passive documentation edits. Even small text changes can alter how users and agents interpret the workflow.

### `scripts/`

This directory contains automation and helper logic used for validation, packaging, generation, or related maintenance tasks.

Edit `scripts/` when you are changing:

- automation that supports local development,
- packaging or build helpers,
- maintenance utilities,
- validation support logic.

Script changes should be validated both for local correctness and for their role in the broader development workflow.

### CLI and Package Code

Where applicable, repository code for installation, bootstrap, packaging, or command execution defines how Spec Kit is delivered and invoked.

Edit the CLI or package code when you are changing:

- installation behavior,
- initialization flow,
- local command behavior,
- execution semantics exposed to users.

Changes here are usually high-impact because they affect how users enter the system.

### Memory and Governing Assets

Some repository assets define persistent project conventions, constitutions, or other workflow-governing content.

Edit these assets when you are changing:

- core workflow assumptions,
- project constitution defaults,
- stable behavioral expectations carried across the kit.

These changes often require corresponding documentation updates because they affect the conceptual model, not just wording.

### `extensions/`

This area supports extension mechanisms and related publishing flows.

Edit `extensions/` when you are:

- adding a new extension,
- modifying extension behavior,
- updating extension packaging or publishing guidance.

Extension changes should preserve compatibility with the main Spec Kit model unless the extension is explicitly intended to be a bounded deviation.

### `presets/`

This area supports reusable preset configurations and their publishing workflows.

Edit `presets/` when you are:

- adding a new preset,
- changing how presets are defined,
- updating preset publishing or maintenance logic.

Presets should remain understandable as opinionated selections layered on top of the core workflow, not as silent redefinitions of that workflow.

### Documentation Surface

Top-level and subsystem documentation explains the user model, maintainer model, testing expectations, and publishing flows.

Edit documentation whenever code, templates, scripts, or workflow semantics change in a way that affects:

- user understanding,
- contributor understanding,
- validation expectations,
- extension or preset author behavior.

Do not treat docs as an afterthought. In Spec Kit, documentation is part of the product surface.

## Change Map: If You Want to Change X, Edit Y

This section is a practical routing guide. Use it before making edits.

### Change generated specification or planning content

Start with the relevant files under `templates/`.

Typical examples:

- generated spec wording,
- plan structure,
- task generation wording,
- default scaffolded project artifacts.

### Change workflow behavior or sequencing

Inspect the relevant templates first, then any supporting script or CLI logic that participates in workflow execution.

Typical examples:

- command flow changes,
- stage ordering changes,
- added or removed workflow steps,
- changes in how generated assets reference one another.

### Change installation or bootstrap behavior

Inspect CLI or package code, install helpers, and any supporting scripts involved in setup or initialization.

Typical examples:

- init behavior,
- install commands,
- local executable behavior,
- package layout expectations.

### Change user-facing documentation

Update `README.md` and any other user-facing docs affected by the change. If the workflow model changes, also update any supporting conceptual documentation so the documented model remains aligned with actual behavior.

### Change contributor-facing guidance

Update `DEVELOPMENT.md`, `CONTRIBUTING.md`, `TESTING.md`, or more specialized contributor documentation as appropriate.

### Change extension behavior or extension publishing

Start in `extensions/` and then update related publishing guidance and any ecosystem references.

### Change preset behavior or preset publishing

Start in `presets/` and then update related publishing guidance and any ecosystem references.

### Change system-wide conceptual assumptions

Treat the change as cross-cutting. Review templates, governing assets, docs, validation expectations, and any affected packaging or integration surfaces together.

## Development Workflows

This section describes the normal paths for common kinds of changes.

### Template Change Workflow

Use this workflow when changing prompt content, generated artifact structure, or other template-defined behavior.

1. Identify the exact user-visible behavior that should change.
2. Locate the relevant template files.
3. Make the smallest coherent change that expresses the intended behavior.
4. Review adjacent templates for consistency.
5. Update documentation if the conceptual or visible behavior changed.
6. Validate the change through focused checks and at least one realistic end-to-end flow.

For template changes, wording is behavior. Treat wording edits with the same care as code changes.

### Script Change Workflow

Use this workflow when changing repository automation or support utilities.

1. Identify the workflow that depends on the script.
2. Edit the relevant script with minimal scope.
3. Validate the script directly.
4. Validate the higher-level workflow that depends on it.
5. Update docs if the script changes how contributors or users are expected to work.

### CLI or Bootstrap Change Workflow

Use this workflow when changing how users enter or operate Spec Kit through commands or package installation.

1. Identify the affected command or entry path.
2. Trace the code and any related templates or scripts.
3. Make the change with attention to backward compatibility and user expectations.
4. Validate the affected command locally.
5. Validate at least one realistic user entry flow end to end.
6. Update user-facing and developer-facing docs as needed.

### Docs-Only Workflow

Use this workflow when making documentation changes that do not intentionally alter behavior.

1. Confirm that the change is actually documentation-only.
2. Update the relevant docs.
3. Check for overlap with other docs that may now be inconsistent.
4. Ensure terminology remains aligned across documents.

Be cautious: many apparent "docs-only" changes in this repository are actually behavioral if they describe workflow semantics that templates or scripts already implement.

### Extension or Preset Workflow

Use this workflow when changing extension or preset assets.

1. Identify whether the change affects the core model or only the extension/preset layer.
2. Edit the relevant extension or preset files.
3. Validate packaging, discoverability, and usage expectations.
4. Update publishing and maintenance guidance where needed.
5. Ensure the relationship to core Spec Kit remains explicit.

## Validation and Testing Map

This section is a routing summary. For detailed procedures, see `TESTING.md` and related validation documentation.

### Focused Local Validation

Use focused validation first when changing a narrow part of the system.

Examples include:

- validating the specific template you changed,
- running the script you modified,
- exercising the CLI path you edited,
- checking a packaging or publishing path affected by your change.

### End-to-End Workflow Validation

Use realistic manual validation when the change affects user-visible workflow semantics.

This is especially important for:

- template changes,
- command flow changes,
- initialization or bootstrap changes,
- agent-facing workflow changes.

A change is not well validated if it only passes isolated checks but has not been exercised in a real workflow context.

### Documentation Validation

When behavior changes, documentation must be checked for alignment. This includes:

- top-level user docs,
- maintainer docs,
- subsystem docs,
- extension or preset publishing docs.

### Packaging and Distribution Validation

When changing install, release, extension, or preset behavior, confirm that the change remains correct in the form users actually consume.

Do not assume that source-level correctness is sufficient.

## Architectural Invariants and Guardrails

The following guardrails should remain true unless there is an explicit, repository-wide decision to change them.

### Preserve Workflow Coherence

The core spec-driven workflow should remain understandable as a staged progression from governing principles to specification, planning, tasking, and execution.

Do not introduce local optimizations that make the overall model less coherent.

### Preserve Cross-Surface Alignment

Templates, scripts, CLI behavior, and docs should describe the same system.

A contributor should not be able to follow the docs and encounter materially different behavior in the actual workflow.

### Treat Templates as Product Logic

Template wording, structure, and default content are part of the product, not just decoration.

Do not make casual wording changes without considering behavioral consequences.

### Keep Agent-Specific Adaptation Secondary to the Core Model

Agent-specific support is important, but it should adapt the core workflow rather than fragment it into unrelated systems unless such divergence is deliberate and documented.

### Keep Extensions and Presets Legible

Extensions and presets should remain understandable additions or variations, not opaque redefinitions of the core workflow.

## Common Pitfalls

The following mistakes are easy to make in this repository.

### Treating a Template Edit as a Mere Copy Change

Template wording often changes behavior. Review it the same way you would review logic changes.

### Updating One Surface but Not the Others

A workflow change may require updates in templates, docs, tests, and installation or execution behavior. Check for cross-surface impact before considering the work complete.

### Validating Too Narrowly

A focused unit check may pass while the real user workflow is broken. Use end-to-end validation when the change affects behavior users or agents actually experience.

### Letting Contributor Docs Drift

When the repository structure or maintainer workflow changes, `DEVELOPMENT.md` and related docs need to change too.

### Hiding a Conceptual Change Inside a Small Edit

If a change alters the mental model or expected workflow, document it as such. Do not let significant semantic changes masquerade as tiny text cleanups.

## Release and Compatibility Notes

When making changes that affect packaging, installation, extensions, presets, or generated outputs, consider compatibility from the perspective of actual users and downstream maintainers.

Questions to ask:

Does this change

- alter the expected workflow?
- affect generated artifacts?
- require documentation updates?
- affect extension or preset compatibility?
- need explicit release-note treatment?

When in doubt, assume user-visible workflow changes deserve explicit documentation and release awareness.

## Keeping This Document Healthy

This document should evolve with the repository.

Update it when:

- repository structure changes,
- the maintainer mental model changes,
- new core subsystems are introduced,
- the recommended development workflow changes,
- the document map needs rerouting.

The goal is to keep this file useful as a top-level maintainer entry point, not to turn it into an exhaustive reference manual.
