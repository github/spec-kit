# Deep research on Spec Kit development documentation coverage

## Executive summary

The GitHub github/spec-kit repository does contain **meaningful developer-oriented documentation** that explains *how templates fit into Spec Kit’s workflow*—especially in the main README.md, the DocFX-backed docs/ site sources, AGENTS.md, and the preset system documentation (presets/README.md \+ presets/ARCHITECTURE.md). These sources provide a workable mental model for the **Spec‑Driven Development (SDD) lifecycle**, and for **template resolution / overrides** (core vs extensions vs presets vs project overrides). 

However, the repository does **not** appear to contain a **single, systematic, developer-facing “Template System” guide** that (a) enumerates **every file under templates/**, (b) explains each one’s role in the pipeline, and (c) provides **glue/jump-start guidance** for maintainers (how to safely modify templates, keep scripts and command prompts aligned, and test changes end-to-end). The absence of an index/README inside templates/ and multiple “path confusion” / “template behavior confusion” issues suggest the mental model is dispersed and easy to miss. 

## Inventory and analysis of templates/

### Directory structure overview

At the time of review (repo main), templates/ contains 7 top-level assets plus a commands/ subdirectory with 9 command templates (total: 16 files). 

### Table of all files under templates/

The “Developer-oriented guidance?” column below is strictly about **human-developer onboarding/mental model** content *inside the file itself* (as opposed to “LLM-facing instructions that a developer could reverse-engineer”). Many of these files primarily serve as **prompt directives/templates** for agents, which is useful but not the same as curated developer documentation.

| File (path)                         | Purpose (what it is for)                                                                                                                                                                                           |        Type | Developer-oriented guidance inside file?                                                                                                 |
| :---------------------------------- | :----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------: | :--------------------------------------------------------------------------------------------------------------------------------------- |
| templates/agent-file-template.md    | Skeleton for a generated “Development Guidelines” / agent context file (placeholders for technologies, structure, commands, recent changes, plus a manual-additions region).                                       |          md | **Partial**: structure \+ placeholders; minimal “why/how.”                                                                               |
| templates/checklist-template.md     | Output template for checklist artifacts; explicitly notes generation by /speckit.checklist and includes a large **“sample items must be replaced”** instruction block.                                             |          md | **Yes (light)**: explains it is command-generated and warns not to keep sample items.                                                    |
| templates/constitution-template.md  | Placeholder constitution format (principles, governance, version metadata) with inline examples in comments.                                                                                                       |          md | **Partial**: examples hint at intent; not a full maintainer guide.                                                                       |
| templates/plan-template.md          | Output template for a feature’s implementation plan and design artifacts; includes “technical context,” constitution gate, project structure, and phased deliverables. It states it’s filled by /speckit.plan.     |          md | **Yes (moderate)**: contains “ACTION REQUIRED” guidance and process structure, but mostly LLM/task-facing rather than maintainer-facing. |
| templates/spec-template.md          | Output template for feature specifications (user stories, acceptance scenarios, requirement structure). Includes strong guidance on testable, prioritized stories.                                                 |          md | **Yes (moderate)**: good guidance for spec authors; still not a “template system” doc.                                                   |
| templates/tasks-template.md         | Output template for actionable task lists; includes prerequisites, path conventions, parallelization strategy, and “sample tasks must be replaced” warnings.                                                       |          md | **Yes (high)**: substantial operational guidance for task authoring and organization.                                                    |
| templates/vscode-settings.json      | VS Code settings enabling prompt file recommendations for speckit.\* and auto-approving terminal tools in .specify/scripts/\*\*.                                                                                   | data (json) | **No**: configuration only; no explanatory doc text.                                                                                     |
| templates/commands/analyze.md       | Command prompt for /speckit.analyze: read-only cross-artifact consistency/quality pass (spec/plan/tasks), driven via prerequisite script outputs.                                                                  |          md | **Yes (moderate)**: documents what analysis does and constraints; still “agent instruction.”                                             |
| templates/commands/checklist.md     | Command prompt for /speckit.checklist: frames checklists as “unit tests for requirements writing” and clarifies what they’re *not* (not implementation verification).                                              |          md | **Yes (high)**: contains a clear mental model and usage framing.                                                                         |
| templates/commands/clarify.md       | Command prompt for /speckit.clarify: targeted clarification questions, completion before planning, and a handoff to /speckit.plan.                                                                                 |          md | **Yes (moderate)**: documents where clarify fits and why.                                                                                |
| templates/commands/constitution.md  | Command prompt for /speckit.constitution: fill constitution template and propagate changes to dependent artifacts; includes explicit note about .specify/memory/constitution.md and initialization from templates. |          md | **Yes (moderate)**: provides maintainer-relevant propagation expectations.                                                               |
| templates/commands/implement.md     | Command prompt for /speckit.implement: execute tasks, check checklists, apply extension hooks, and enforce safety constraints (secrets patterns, etc.).                                                            |          md | **Yes (moderate)**: good operational constraints; not an architecture guide.                                                             |
| templates/commands/plan.md          | Command prompt for /speckit.plan: sets up plan workflow using scripts; includes handoffs to tasks and checklist; references loading templates copied into place.                                                   |          md | **Yes (moderate)**: explains sequencing and handoffs.                                                                                    |
| templates/commands/specify.md       | Command prompt for /speckit.specify: create/update feature spec from natural language; handoffs to plan and clarify; calls create-new-feature script.                                                              |          md | **Yes (moderate)**: explains behavior and chaining.                                                                                      |
| templates/commands/tasks.md         | Command prompt for /speckit.tasks: generate tasks from design artifacts; handoffs to analyze \+ implement; uses prerequisite scripts.                                                                              |          md | **Yes (moderate)**: describes role in lifecycle.                                                                                         |
| templates/commands/taskstoissues.md | Command prompt for converting tasks into GitHub issues; includes issue\_write tool usage and explicit guardrails to only act on matching GitHub remotes.                                                           |          md | **Yes (light)**: explains constraints; minimal broader context.                                                                          |

### What the templates collectively imply as a mental model

Across the command templates (templates/commands/\*.md) and artifact templates (\*-template.md), a consistent implied model emerges:

* **Commands** (specify/clarify/plan/tasks/analyze/implement/checklist/…) define *procedures \+ guardrails* for an AI agent. Many include prerequisite scripts, expected inputs/outputs, and optional handoffs to the next command. 
* **Templates** (spec-template.md, plan-template.md, tasks-template.md, etc.) define *artifact structure* and embed quality constraints (e.g., “replace sample tasks,” “prioritized, independently testable user stories”). 
* Some files mix guidance roles (e.g., tasks-template.md doubles as a playbook for parallelization and incremental delivery). 

This is strong “operational documentation,” but it is **not packaged as a maintainer-facing, systematic explanation of the template system**.

## Repository documentation that explains templates for developers

### Core docs that supply “glue” and a developer mental model

The repository’s main README.md explains key “template system” concepts in a developer-friendly way:

* It describes a **priority stack** for template resolution with a Mermaid diagram and explicitly states that templates are resolved at runtime (highest-priority match wins), while commands are applied at install time. 
* It also shows example project directory structures and demonstrates where templates live after initialization (under .specify/templates/ in the user project). 

The DocFX-backed docs/ content includes:

* A quickstart that describes the end-to-end **6-step workflow** (init → constitution → specify → clarify → plan → tasks → implement) and emphasizes **“context awareness”** via active feature detection (branch-based). 
* Installation and upgrade guidance that clarifies what “project files” get refreshed (commands, scripts, templates, memory) versus what is “safe” (specs/ and code), and explicitly discusses .specify/templates/ as upgrade-targeted infrastructure. 
* Local development instructions for iterating on the CLI without release publishing, including running via python \-m src.specify\_cli and uvx \--from .. 
* The docs/README.md indicates docs are built via DocFX and deployed to GitHub Pages. 

AGENTS.md is a maintainer-oriented guide that explains how agent integrations work (directory conventions, command formats, argument placeholders) and gives a step-by-step procedure for adding support for new tools/agents. 

### Presets / extensions documentation that clarifies template customization

The repository contains a fairly systematic explanation of template customization mechanics in the **preset system** docs:

* presets/README.md defines presets as priority-ordered overrides for templates and commands, explains runtime template resolution vs install-time command registration, and documents specify preset resolve for tracing resolution. 
* presets/ARCHITECTURE.md goes deeper: it includes Mermaid diagrams for template resolution and command registration, and explicitly lists the multiple implementations (Python \+ Bash \+ PowerShell) to keep behavior consistent. 
* The extensions system docs and publishing guide define expected repo structures and strongly encourage extension documentation quality (README structure, command documentation, etc.). 

This preset documentation is the closest thing in-repo to a “template architecture doc,” but it is **scoped to presets** rather than the canonical templates/ directory inventory.

## Issues, pull requests, and discussions that surface documentation gaps

A recurring theme in repo activity is **path confusion** and missing “single source of truth” documentation for where templates/commands/scripts “should live” and how they relate (repo-internal templates/ vs installed .specify/templates/).

### Repeated path and structure confusion

* Some users flagged incorrect or confusing path references from templates to command files, e.g., plan-template.md referencing a .specify/templates/commands/... path that didn’t match expectations. 
* Multiple issues question whether templates and scripts should refer to /templates/... vs /.specify/templates/..., and whether specs belong under .specify/specs/ or at repo root—indicating onboarding/docs ambiguity and drift. 

### Template mutability and “who is allowed to edit what”

* A reported behavior: an agent (Codex CLI) modified files in .specify/templates during /speckit.constitution, even though templates were expected to remain base assets only updated on init/upgrade. This is a classic “mental model mismatch” symptom: users lack explicit, enforced rules (and docs) about mutability boundaries. 

### “How do I test template changes?” as a maintainership pain point

* A maintainer/dev workflow issue: local modifications to templates/commands/\*.md and scripts were “ignored” because init flows pulled templates from releases (at least in the reported environment), making it hard to validate changes without publishing. 

### Explicit calls for onboard-oriented guidance

* Issue \#295 explicitly proposes onboarding improvements (tour, quick reference, diagram) to reinforce the Specify → Plan → Tasks sequence and discourage users from running later steps out of order. 

### PR signals related to templates as a customizable surface

* PR \#1466 (open as viewed) proposes removing branch-numbering logic from a template and adding a \--template-repo option to specify init so users can pull templates from a fork—an implicit acknowledgement that templates are a customization surface that benefits from better “how to modify safely” documentation. 
* PR \#1987 (open as viewed) is nominally a docs rename, but the “files changed” view indicates it includes functional modifications related to template format selection (“compact” templates). Even the existence of a “compact format” notion increases the need for a single, coherent template developer guide. 
* Recent/active issues discuss template resolution improvements (e.g., adding resolver/source attribution for extension templates). 

## Gaps in systematic developer-oriented documentation

### Missing “one-stop” index for template assets

The repository has strong building blocks (command templates that describe their behavior; a README that explains resolution stacks; preset architecture docs). But there is no central document that answers, in one place:

* *What are all template files and command templates?* (Inventory \+ purpose)
* *Which ones are inputs vs outputs?* (What gets copied into a project vs generated as feature artifacts)
* *Which scripts and CLI operations touch which files?*
* *What is “safe to edit,” when, and by whom?* (Human vs agent vs init/upgrade)
* *How to test a template change end-to-end without publishing a release?*

The lack of such a doc is consistent with the volume of issues asking where assets belong and how tooling should interpret them. 

### “Developer-oriented” guidance is embedded, but mostly LLM-facing

Many template/command files contain substantial guidance, but it is largely phrased as **agent instructions** (MUST/SHOULD), not as curated maintainer documentation. That’s helpful for reverse engineering, yet brittle as onboarding material—particularly when paths or assumptions drift.

Concrete example: tasks-template.md is rich in operational guidance but serves primarily as *an output template \+ generator contract*, not a doc explaining how to evolve the template system. 

## Recommendations for documentation to add

### Add a maintainer-facing “Template System” guide

A strong candidate is docs/templates.md (and link it from docs/index.md \+ root README), or a templates/README.md plus a doc-site page. The doc should explicitly bridge:

* repo templates/\*\* (source of truth)
* installed .specify/templates/\*\* (copied into projects)
* generated specs/\<feature\>/\*.md artifacts (outputs)

**Proposed outline**

* Purpose of templates vs commands vs scripts vs memory
* Full inventory of templates/ (auto-generate this table in CI to prevent drift)
* Artifact lifecycle: what every /speckit.\* reads/writes
* Mutability rules: what agents may edit vs what must remain stable
* Path conventions and historical migrations (templates/ → .specify/templates/)
* Testing workflow for template changes (local, without publishing)

**Example content snippet (illustrative)**

```
## Template roles

- templates/*-template.md: base artifact formats copied into .specify/templates/  
- templates/commands/*.md: agent command procedures installed into agent-specific folders  
- scripts/**: runtime glue (select active feature, copy templates, update agent context)
```

### Add a Mermaid “project structure + flow” diagram set

The repo already uses Mermaid for template/preset diagrams; extend that style to make the *full pipeline* obvious.

Suggested diagrams to include (and where)

* In docs/quickstart.md (or a new docs/how-it-works.md):
    * **SDD lifecycle flowchart**: constitution → specify → clarify → plan → tasks → analyze/checklist → implement → taskstoissues
* In the proposed template guide:
    * **File I/O map**: each command node lists inputs/outputs (e.g., clarify reads spec.md, writes clarifications back; plan reads spec.md \+ constitution, writes plan.md \+ design docs; tasks reads plan.md \+ artifacts, writes tasks.md).
* In the preset/extension docs (already present):
    * Keep the **template resolution stack**, but cross-link to the main template guide. 

### Add a “Template change checklist” for contributors

Given recurring drift issues, introduce a short checklist (either in CONTRIBUTING.md or a dedicated doc) that enforces cross-asset consistency:

* If you change spec-template.md, confirm:
    * templates/commands/specify.md instructions remain aligned
    * templates/commands/clarify.md taxonomy still matches spec sections
* If you change template paths or structure:
    * update Bash + PowerShell scripts consistently (and the preset resolver references, if applicable) 
    * Add “Docs impact” section: update docs/upgrade.md and docs/quickstart.md if user-facing behavior changed. 

### Add “How to test template/command changes locally” documentation

Augment docs/local-development.md with a template-focused section that addresses the reported pain:

* How to run the CLI from source (python \-m src.specify\_cli ...)
* How to initialize a sandbox project using local assets
* How to validate that the sandbox project is using your modified templates/commands/scripts
* How to run a minimal “golden path” (specify → plan → tasks) to ensure nothing breaks

This would directly address the workflow gap implied by “local changes ignored” reports. 

---

