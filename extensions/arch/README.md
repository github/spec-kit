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
specify extension add arch --from https://github.com/bigsmartben/spec-kit-arch/archive/refs/tags/v1.1.0.zip
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

The extension provides two commands:

```text
/speckit.arch.generate
/speckit.arch.reverse
```

Choose the command based on where your architecture knowledge should come from.

| Situation | Use | What it does |
| --- | --- | --- |
| You are working in a Spec Kit project with intended product/use-case context | `/speckit.arch.generate` | Generates or refreshes the architecture SSOT from scenario semantics and existing architecture memory. It may read `.specify/memory/uc.md` as optional background. |
| You are onboarding an ordinary historical repository without reliable Spec Kit feature context | `/speckit.arch.reverse` | First records observable repository evidence, then derives the architecture SSOT from that evidence. |

### `/speckit.arch.generate`

Run this when you already know what the project is meant to become, or when Spec Kit use-case context exists and you want to make architecture intent explicit before planning.

```text
/speckit.arch.generate
```

The command works from the scenario view outward:

1. Establishes the architecture framing for the current pass.
2. Creates or refreshes the scenario, logical, process, development, and physical views.
3. Updates `.specify/memory/architecture.md` as the cross-view synthesis.

Use it to answer questions like:

- What boundaries should later feature plans preserve?
- Which responsibilities must not be merged by future implementation work?
- Which runtime, development, or deployment constraints are already architecture decisions?
- Which architecture gaps must stay explicit until the team supplies more information?

### `/speckit.arch.reverse`

Run this when the repository already exists but the architecture SSOT does not.

```text
/speckit.arch.reverse
```

The command inspects repository evidence first, writes `.specify/memory/architecture-repo-facts.md`, then derives the five 4+1 views and synthesis from those facts.

It is useful for:

- Bringing a non-Spec Kit repository into Spec Kit.
- Reconstructing architecture intent from README files, tests, entry points, package layout, routes, workers, CI/CD, configuration, and deployment clues.
- Making uncertainty visible when the repository does not prove actors, runtime ownership, deployment topology, or business meaning.

If `.specify/memory/repository-first/` exists, the reverse command also treats those files as evidence inputs. It summarizes dependency matrices and module invocation specs into architecture-level constraints, dependency rules, gaps, and review triggers.

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

`/speckit.arch.reverse` also writes its evidence layer:

```text
.specify/memory/architecture-repo-facts.md
```

`/speckit.arch.generate` writes the six architecture SSOT files. Its setup may create an empty `.specify/memory/architecture-repo-facts.md` placeholder for reverse workflow compatibility, but generate does not use that file as input.

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

The extension intentionally does not provide the legacy `/speckit.arch` command.
