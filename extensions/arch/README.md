# Spec Kit Architecture Workflow Extension

Add a project-level architecture source of truth to Spec Kit.

Spec Kit is very good at turning a feature spec into a plan, tasks, and implementation work. In real projects, though, feature specs often do not carry enough stable architecture context: module boundaries, runtime responsibilities, deployment assumptions, cross-team ownership, and the tradeoffs that should not be rediscovered by every agent run.

This extension fills that gap. It creates architecture memory under `.specify/memory/` so future planning can refer to one explicit architecture SSOT instead of guessing from scattered docs, old code, or one feature request.

## When You Need This

Use this extension when you want the AI agent to preserve architecture intent across Spec Kit workflows:

- You are starting or reshaping a Spec Kit project and want architecture decisions captured before detailed planning.
- You have an existing repository and need architecture memory derived from observable repo facts.
- You want later `/speckit.plan` runs to see stable boundaries, constraints, tradeoffs, and unresolved gaps.
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
specify extension add arch --from https://github.com/bigsmartben/spec-kit-arch/archive/refs/tags/v1.2.1.zip
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

The extension id is `arch`, and each command uses `.arch` as the command namespace. The extension provides ten commands: one forward-generation command and one reverse-generation command for each 4+1 architecture view.

```text
/speckit.arch.scenario-generate
/speckit.arch.logical-generate
/speckit.arch.process-generate
/speckit.arch.development-generate
/speckit.arch.physical-generate
/speckit.arch.scenario-reverse
/speckit.arch.logical-reverse
/speckit.arch.process-reverse
/speckit.arch.development-reverse
/speckit.arch.physical-reverse
```

Choose the direction based on where architecture knowledge should come from, then choose the view you want to update.

| Direction | Use when | Evidence source | Writes |
| --- | --- | --- | --- |
| `generate` | You are working from intended product/use-case context or existing architecture memory | User input, current architecture views, optional `.specify/memory/uc.md` for scenario only | The selected architecture view, with synthesis refreshed only when all views are coherent |
| `reverse` | You are onboarding or documenting an existing repository | Observable repository facts recorded in `.specify/memory/architecture-repo-facts.md` | Repo facts plus the selected architecture view, with synthesis refreshed only when all views are coherent |

| View | Forward command | Reverse command | Main artifact |
| --- | --- | --- | --- |
| Scenario | `/speckit.arch.scenario-generate` | `/speckit.arch.scenario-reverse` | `.specify/memory/architecture-scenario-view.md` |
| Logical | `/speckit.arch.logical-generate` | `/speckit.arch.logical-reverse` | `.specify/memory/architecture-logical-view.md` |
| Process | `/speckit.arch.process-generate` | `/speckit.arch.process-reverse` | `.specify/memory/architecture-process-view.md` |
| Development | `/speckit.arch.development-generate` | `/speckit.arch.development-reverse` | `.specify/memory/architecture-development-view.md` |
| Physical | `/speckit.arch.physical-generate` | `/speckit.arch.physical-reverse` | `.specify/memory/architecture-physical-view.md` |

### Forward Generation

Run `*.generate` commands when you already know what the project is meant to become, or when Spec Kit use-case context exists and you want to make architecture intent explicit before planning.

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

Each forward command populates only its selected view. Its setup bootstrap may create missing placeholder files for the architecture memory set, but the command must not populate non-target views or use `.specify/memory/architecture-repo-facts.md` as input. It may refresh `.specify/memory/architecture.md` only after all five views contain coherent, non-placeholder architecture content.

Each command also loads `.specify/extensions/arch/schemas/architecture-artifacts.schema.json` as the structural contract for architecture artifacts. Commands own evidence extraction, classification, validation, and write boundaries; templates own only the Markdown rendering layout.

### Reverse Generation

Run `*.reverse` commands when the repository already exists but the architecture SSOT does not.

Recommended order:

1. `/speckit.arch.scenario-reverse`
2. `/speckit.arch.logical-reverse`
3. `/speckit.arch.process-reverse`
4. `/speckit.arch.development-reverse`
5. `/speckit.arch.physical-reverse`

Each reverse command inspects repository evidence first, writes or refreshes `.specify/memory/architecture-repo-facts.md`, then derives the selected 4+1 view from those facts. The repo facts file is cumulative: reverse commands preserve existing non-placeholder facts outside their evidence focus unless cited evidence is removed, contradicted, or superseded, and they record the reason for any replacement or downgrade. A reverse command may refresh `.specify/memory/architecture.md` after all five views contain coherent, evidence-backed architecture content.

Reverse commands validate both the repo-facts working model and the target-view working model against the same schema contract before rendering Markdown.

It is useful for:

- Bringing a non-Spec Kit repository into Spec Kit.
- Reconstructing architecture intent from README files, tests, entry points, package layout, routes, workers, CI/CD, configuration, and deployment clues.
- Making uncertainty visible when the repository does not prove actors, runtime ownership, deployment topology, or business meaning.

If `.specify/memory/repository-first/` exists, reverse commands also treat those files as evidence inputs. They summarize dependency matrices and module invocation specs into architecture-level constraints, dependency rules, gaps, and review triggers.

### Synthesis Refresh

Commands refresh `.specify/memory/architecture.md` only when every 4+1 view is synthesis-ready:

- The view file exists.
- It no longer contains `NEEDS ARCH UPDATE`.
- It contains concrete architecture conclusions or explicit gaps in required sections, not only template headings.
- Explicit gaps may remain, but gaps alone do not make a view synthesis-ready.
- Cross-view terminology is coherent enough to synthesize without inventing content.

If any view is missing, placeholder-only, stale, or inconsistent, commands leave `.specify/memory/architecture.md` unchanged and report the missing or not-ready views.

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

Forward `*.generate` commands populate only the selected view. Their setup may create placeholder architecture memory files, including an empty `.specify/memory/architecture-repo-facts.md` for reverse workflow compatibility, but generate commands do not use that file as input.

Reverse `*.reverse` commands populate `.specify/memory/architecture-repo-facts.md` plus the selected view, preserving unrelated existing repo facts unless evidence has changed and the reason is recorded.

The extension also ships the artifact contract used by the prompts:

```text
.specify/extensions/arch/schemas/architecture-artifacts.schema.json
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

## Using The Architecture SSOT In Planning

The extension commands create the architecture memory. To make the core Spec Kit planning flow read that memory automatically, install the optional preset:

```bash
specify preset add --dev /home/administrator/github/spec-kit-arch/presets/arch-governance
```

The preset wraps only `/speckit.plan`. It injects the architecture SSOT into planning so new feature plans can be checked against existing boundaries, constraints, and gaps.

The preset does not override `/speckit.tasks` or `/speckit.implement`.

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

Validate the preset from a fresh project:

```bash
specify init /tmp/spec-kit-arch-preset-test --ai codex --ignore-agent-tools --script sh
cd /tmp/spec-kit-arch-preset-test
specify preset add --dev /home/administrator/github/spec-kit-arch/presets/arch-governance
rg -n "Architecture SSOT Injection|Architecture Grounding Summary" .agents/skills/speckit-plan/SKILL.md
```

The extension intentionally does not provide the legacy `/speckit.arch`, `/speckit.arch.generate`, or `/speckit.arch.reverse` commands.
