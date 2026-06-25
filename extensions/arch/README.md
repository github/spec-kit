# Spec Kit Architecture Workflow Extension

Add a project-level architecture source of truth to Spec Kit.

Spec Kit is very good at turning a feature spec into a plan, tasks, and implementation work. In real projects, though, feature specs often do not carry enough stable architecture context: module boundaries, runtime responsibilities, deployment assumptions, cross-team ownership, and the tradeoffs that should not be rediscovered by every agent run.

This extension fills that gap. It creates architecture memory under `.specify/memory/` so architecture decisions can be reviewed from one explicit SSOT instead of guessed from scattered docs, old code, or one feature request.

## When You Need This

Use this extension when you want the AI agent to preserve architecture intent across Spec Kit workflows:

- You are starting or reshaping a Spec Kit project and want architecture decisions captured before detailed planning.
- You have an existing repository and need architecture memory derived from observable repo facts.
- You want stable boundaries, constraints, tradeoffs, and unresolved gaps captured before downstream work consumes architecture context.
- You need a safe place for architecture-level reasoning without editing source code, feature specs, tasks, deployment files, or runbooks.

The extension is intentionally about architecture SSOT, not implementation design. It records project-level 4+1 architecture views and a synthesis that downstream work can use as grounding.

## Install

The extension is listed in the Spec Kit community catalog for discovery. You can find or inspect it from a Spec Kit project:

```bash
specify extension search arch
specify extension info arch
```

Community catalog entries may be discovery-only. Install the published release directly from GitHub:

```bash
specify extension add arch --from https://github.com/bigsmartben/spec-kit-arch/archive/refs/tags/v1.2.2.zip
```

Install from a local development checkout:

```bash
specify extension add --dev /home/administrator/github/spec-kit-arch
```

After installation, the extension is copied under:

```text
.specify/extensions/arch/
```

## Commands

The extension id is `arch`, and each command uses `.arch` as the command namespace. The extension provides twelve commands: one full forward-generation command, one full reverse-generation command, plus one forward-generation command and one reverse-generation command for each 4+1 architecture view.

```text
/speckit.arch.full-generate
/speckit.arch.scenario-generate
/speckit.arch.logical-generate
/speckit.arch.process-generate
/speckit.arch.development-generate
/speckit.arch.physical-generate
/speckit.arch.full-reverse
/speckit.arch.scenario-reverse
/speckit.arch.logical-reverse
/speckit.arch.process-reverse
/speckit.arch.development-reverse
/speckit.arch.physical-reverse
```

Choose the direction based on where architecture knowledge should come from, then choose whether to generate the full 4+1 set or update one view.

| Direction | Use when | Evidence source | Writes |
| --- | --- | --- | --- |
| `full-generate` | You want one command to generate the complete forward 4+1 architecture set | User input, current architecture memory, optional `.specify/memory/uc.md` | All five architecture views, with synthesis refreshed only when the readiness validator returns `ready_gate: PASS` |
| `full-reverse` | You want one command to reconstruct the complete 4+1 architecture set from an existing repository | Observable repository facts recorded in `.specify/memory/architecture-repo-facts.md` | Repo facts plus all five architecture views, with synthesis refreshed only when the readiness validator returns `ready_gate: PASS` |
| `generate` | You are working from intended product/use-case context or existing architecture memory | User input, current architecture views, optional `.specify/memory/uc.md` for scenario only | The selected architecture view, with synthesis refreshed only when the readiness validator returns `ready_gate: PASS` |
| `reverse` | You are onboarding or documenting an existing repository | Observable repository facts recorded in `.specify/memory/architecture-repo-facts.md` | Repo facts plus the selected architecture view, with synthesis refreshed only when the readiness validator returns `ready_gate: PASS` |

| View | Forward command | Reverse command | Main artifact |
| --- | --- | --- | --- |
| Scenario | `/speckit.arch.scenario-generate` | `/speckit.arch.scenario-reverse` | `.specify/memory/architecture-scenario-view.md` |
| Logical | `/speckit.arch.logical-generate` | `/speckit.arch.logical-reverse` | `.specify/memory/architecture-logical-view.md` |
| Process | `/speckit.arch.process-generate` | `/speckit.arch.process-reverse` | `.specify/memory/architecture-process-view.md` |
| Development | `/speckit.arch.development-generate` | `/speckit.arch.development-reverse` | `.specify/memory/architecture-development-view.md` |
| Physical | `/speckit.arch.physical-generate` | `/speckit.arch.physical-reverse` | `.specify/memory/architecture-physical-view.md` |

### Forward Generation

Run `*.generate` commands when you already know what the project is meant to become, or when Spec Kit use-case context exists and you want to make architecture intent explicit before planning.

Use the full forward command when you want to populate the complete 4+1 set in dependency order:

```text
/speckit.arch.full-generate
```

The full command writes the scenario, logical, process, development, and physical views, then refreshes `.specify/memory/architecture.md` only after all five generated views satisfy the working-model contract and the rendered-artifact readiness validator returns `ready_gate: PASS`. It does not read or update `.specify/memory/architecture-repo-facts.md`.

Recommended order:

1. `/speckit.arch.scenario-generate`
2. `/speckit.arch.logical-generate`
3. `/speckit.arch.process-generate`
4. `/speckit.arch.development-generate`
5. `/speckit.arch.physical-generate`

Use it to answer questions like:

- What boundaries should later feature plans preserve?
- Which responsibilities must not be merged by future implementation work?
- Which runtime, development, or deployment constraints are already architecture decisions?
- Which architecture gaps must stay explicit until the team supplies more information?

Each per-view forward command populates only its selected view. Its setup bootstrap may create missing placeholder files for the architecture memory set, but the command must not populate non-target views or use `.specify/memory/architecture-repo-facts.md` as input. It may refresh `.specify/memory/architecture.md` only after the readiness validator reports `ready_gate: PASS`.

`speckit.arch.development-generate` must produce the Development View `Dependency Matrix` section from logical/process architecture relationships and stated constraints.

Each command also loads `.specify/extensions/arch/schemas/architecture-artifacts.schema.json` as the working-model contract and uses `.specify/extensions/arch/scripts/bash/validate-arch-artifacts.sh` or `.specify/extensions/arch/scripts/powershell/validate-arch-artifacts.ps1` as the rendered-artifact readiness gate. Commands own evidence extraction, classification, and write routing; schemas own working-model structure; validators own rendered-artifact readiness; templates own only the Markdown rendering layout.

### Reverse Generation

Run `*.reverse` commands when the repository already exists but the architecture SSOT does not.

Use the full reverse command when you want to populate repo facts and the complete 4+1 set in dependency order:

```text
/speckit.arch.full-reverse
```

The full reverse command writes `.specify/memory/architecture-repo-facts.md`, the scenario, logical, process, development, and physical views, then refreshes `.specify/memory/architecture.md` only after all five generated views satisfy the working-model contract and the rendered-artifact readiness validator returns `ready_gate: PASS`.

Recommended order:

1. `/speckit.arch.scenario-reverse`
2. `/speckit.arch.logical-reverse`
3. `/speckit.arch.process-reverse`
4. `/speckit.arch.development-reverse`
5. `/speckit.arch.physical-reverse`

Each reverse command inspects repository evidence first, writes or refreshes `.specify/memory/architecture-repo-facts.md`, then derives the selected 4+1 view from those facts. The repo facts file is cumulative: reverse commands preserve existing non-placeholder facts outside their evidence focus unless cited evidence is removed, contradicted, or superseded, and they record the reason for any replacement or downgrade. A reverse command may refresh `.specify/memory/architecture.md` only after the readiness validator reports `ready_gate: PASS`.

Reverse commands validate both the repo-facts working model and the target-view working model against the same schema contract before rendering Markdown.

It is useful for:

- Bringing a non-Spec Kit repository into Spec Kit.
- Reconstructing architecture intent from README files, tests, entry points, package layout, routes, workers, CI/CD, configuration, and deployment clues.
- Making uncertainty visible when the repository does not prove actors, runtime ownership, deployment topology, or business meaning.

If `.specify/memory/repository-first/` exists, reverse commands also treat those files as evidence inputs within each command's view scope. Dependency matrices are primarily owned by the development view: `speckit.arch.development-generate` and `speckit.arch.development-reverse` must produce the Development View `Dependency Matrix` section, and the reverse command summarizes repository-first matrices into architecture-level development constraints, dependency rules, gaps, and review triggers. Other views must not consume dependency matrices directly or treat them as a separate architecture view; they may use development-view dependency conclusions only when the development view is synthesis-ready and relevant to their target view.

### Synthesis Refresh

Commands refresh `.specify/memory/architecture.md` only when the readiness validator reports `ready_gate: PASS` for the rendered architecture memory set. The validator reports `ready_gate: BLOCKED` with these runtime blocker codes when any rendered-artifact readiness rule fails:

- `ARCH_ARTIFACT_MISSING`: a required architecture artifact is missing.
- `ARCH_PLACEHOLDER_PRESENT`: a rendered artifact still contains placeholder update markers.
- `ARCH_REQUIRED_SECTION_MISSING`: a required section id is absent from a rendered artifact.
- `ARCH_REQUIRED_SECTION_EMPTY`: a required section has no supported content.
- `ARCH_TRACEABILITY_MISSING`: a view has no supported Source Traceability records.
- `ARCH_DEPENDENCY_MATRIX_MISSING` or `ARCH_DEPENDENCY_MATRIX_EMPTY`: the Development View dependency matrix is absent or empty.

Commands may also report command-local blocker codes while classifying candidate conclusions:

- `ARCH_SOURCE_MISSING`: a conclusion or dependency matrix entry lacks an allowed source.
- `ARCH_USER_INPUT_ONLY`: a reverse-generated conclusion is supported only by user input.
- `ARCH_REPO_FIRST_MATRIX_MISUSED`: repository-first dependency matrices are copied into architecture views, treated as an independent view, or used as direct non-development evidence.
- `ARCH_GIT_HISTORY_ONLY`: Git history is used as the sole support for an architecture conclusion.
- `ARCH_BOUNDARY_NONRESPONSIBILITY_MISSING`: a boundary has responsibilities but no explicit non-responsibility.
- `ARCH_UNSUPPORTED_CONCLUSION`: unsupported content is promoted into conclusion tables instead of gaps.

If any blocker is present, commands leave `.specify/memory/architecture.md` unchanged and report the blocker codes, affected artifacts, and affected sections.

## Files Written

The architecture SSOT files are:

```text
.specify/memory/architecture.md
.specify/memory/architecture-scenario-view.md
.specify/memory/architecture-logical-view.md
.specify/memory/architecture-process-view.md
.specify/memory/architecture-development-view.md
.specify/memory/architecture-physical-view.md
```

Reverse commands also write their evidence layer:

```text
.specify/memory/architecture-repo-facts.md
```

The full forward command populates the five 4+1 view files and may refresh `.specify/memory/architecture.md` after all generated views are synthesis-ready. Per-view forward `*.generate` commands populate only the selected view. Their setup may create placeholder architecture memory files, including an empty `.specify/memory/architecture-repo-facts.md` for reverse workflow compatibility, but generate commands do not use that file as input.

The full reverse command populates `.specify/memory/architecture-repo-facts.md` plus all five 4+1 view files, and may refresh `.specify/memory/architecture.md` after all generated views are synthesis-ready. Per-view reverse `*.reverse` commands populate `.specify/memory/architecture-repo-facts.md` plus the selected view, preserving unrelated existing repo facts unless evidence has changed and the reason is recorded.

The extension also ships the artifact contract used by the prompts:

```text
.specify/extensions/arch/schemas/architecture-artifacts.schema.json
.specify/extensions/arch/scripts/bash/validate-arch-artifacts.sh
.specify/extensions/arch/scripts/powershell/validate-arch-artifacts.ps1
```

The commands do not edit:

```text
.specify/memory/uc.md
.specify/memory/constitution.md
feature specs
plans
tasks
source code
tests
root docs/
deployment manifests
runbooks
```

## What The Extension Is Not

This extension does not produce implementation plans, task lists, class designs, API schemas, database schemas, framework choices, deployment manifests, or runbooks.

It also does not replace feature specs. Feature specs describe what a feature should do. The architecture SSOT records the project-level decisions and constraints that future features should respect.

## Development

Validate the extension from a fresh project:

```bash
specify init /tmp/spec-kit-arch-test --ai codex --ignore-agent-tools --script sh
cd /tmp/spec-kit-arch-test
specify extension add --dev /home/administrator/github/spec-kit-arch
.specify/extensions/arch/scripts/bash/setup-arch.sh --json
```

The extension intentionally does not provide the legacy `/speckit.arch`, `/speckit.arch.generate`, or `/speckit.arch.reverse` commands.
