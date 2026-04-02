Yes, it makes sense.

A top-level `DEVELOPMENT.md` is a good fit here because the current `README.md` is clearly optimized for users adopting Spec Kit in projects, while `CONTRIBUTING.md` is narrower: contribution mechanics, validation flow, and PR hygiene. It is not really a full developer mental-model document. The repo also already has specialized docs like `TESTING.md`, the extension publishing guide, and preset publishing guide, which means a developer-facing entry document should primarily orient, map, and route rather than duplicate details. ([GitHub][1])

I would treat `DEVELOPMENT.md` as the **developer map of the system**:

* what Spec Kit is internally,
* how the repository is organized,
* how the main moving parts interact,
* where to edit for each class of change,
* how to validate changes,
* and where deeper docs live.
  That is the missing layer between user docs and contribution rules. ([GitHub][1])

## What `DEVELOPMENT.md` should do

It should not try to be:

* another `README.md`,
* another `CONTRIBUTING.md`,
* or a giant reference manual.

It should be the **primary entry point for maintainers and contributors who need system understanding before editing**.

The right emphasis is:

1. mental model,
2. repository anatomy,
3. change workflows,
4. document map,
5. common modification scenarios.

That is especially important in this repo because the core is not just Python code; it is a coordinated kit of templates, scripts, CLI behavior, agent integrations, memory files, extensions, presets, and documentation. The current docs already imply this multi-part system, but they are distributed across several places. ([GitHub][2])

## Recommended top-level structure

Here is the outline I would use.

### 1. Purpose of this document

Very short. Explain that:

* `README.md` is for users adopting Spec Kit,
* `DEVELOPMENT.md` is for people modifying Spec Kit itself,
* `CONTRIBUTING.md` covers contribution process and PR expectations,
* deeper component docs are linked below. ([GitHub][2])

### 2. What Spec Kit is, from a maintainer perspective

Give a concise internal framing, for example:

* Spec Kit is a toolkit for Spec-Driven Development.
* The repo packages prompts/templates, command scaffolding, scripts, CLI support, agent-specific integration assets, and ecosystem mechanisms such as extensions and presets.
* The generated user workflow is roughly: constitution → specify → plan → tasks → implement. ([GitHub][1])

This section should answer: **what are we actually maintaining?**

### 3. System mental model

This is one of the most important sections.

Suggested subsections:

* **Core artifact flow**
  How the main SDD flow progresses through constitution, specification, plan, tasks, implementation. ([GitHub][1])
* **Delivery model**
  Clarify what lives in the repo versus what gets installed/scaffolded into user projects.
* **Main abstraction layers**
  For example:

  * templates/content,
  * command scaffolding,
  * CLI/bootstrap/install logic,
  * agent-specific integration surfaces,
  * extension/preset ecosystem,
  * docs/catalog/community surfaces.

A simple diagram would help a lot here.

### 4. Repository anatomy

This should be a guided map, not just a tree dump.

For each major top-level area, explain:

* what it contains,
* why it exists,
* when to edit it,
* what else it interacts with.

You already mentioned this, and yes, it should absolutely be included.

Likely subsections:

* `templates/` — core artifact templates and command templates; probably the most important content layer for generated workflow behavior. The repo README and contribution workflow both point contributors to template validation. ([GitHub][2])
* `scripts/` — automation/bootstrap/helper scripts; `CONTRIBUTING.md` explicitly calls out script functionality as something contributors should test. ([GitHub][2])
* `memory/` or `.specify/memory`-related assets — constitution/project-memory behavior; contribution guidance explicitly references `memory/constitution.md` updates for major process changes. ([GitHub][2])
* CLI/package code — where install/scaffold behavior and local `specify` execution live.
* `extensions/` — extension model and publishing support; the repo includes a dedicated extension publishing guide. ([GitHub][3])
* `presets/` — preset model and publishing support; there is also a dedicated presets publishing guide. ([GitHub][4])
* catalogs/community metadata — where ecosystem discoverability is maintained; the README includes community extensions, presets, walkthroughs, and related ecosystem surfaces. ([GitHub][5])
* top-level docs — which are user docs, contributor docs, testing docs, release docs, etc.

### 5. “If you want to change X, edit Y”

This is the most practical section, and many repos miss it.

Examples:

* To change the wording/structure of generated feature specs → edit relevant template files.
* To change slash-command behavior or workflow sequencing → inspect command templates plus any supporting scripts/CLI glue.
* To change installation/bootstrap behavior → inspect CLI/package/bootstrap code.
* To add or modify extension publishing behavior → see `extensions/EXTENSION-PUBLISHING-GUIDE.md`.
* To add or modify presets behavior → see `presets/PUBLISHING.md`.
* To adjust docs shown to end users → update `README.md` and possibly `spec-driven.md`, which `CONTRIBUTING.md` explicitly names for user-facing changes. ([GitHub][2])

This section makes the doc operational instead of descriptive.

### 6. End-to-end development workflows

Not contribution policy in the abstract, but concrete developer workflows.

Suggested subsections:

* **Template change workflow**
* **Script change workflow**
* **CLI/bootstrap change workflow**
* **Docs-only workflow**
* **Extension/preset/catalog change workflow**

For each:

* where to edit,
* how to test locally,
* what docs to update,
* what regressions to watch for.

This aligns well with the current contribution guidance, which already says to test CLI commands in an agent, verify templates in `templates/`, test scripts in `scripts/`, and update memory/docs where relevant. ([GitHub][2])

### 7. Validation and testing map

Do not restate all of `TESTING.md`. Instead, summarize the validation layers and link outward.

Suggested structure:

* quick local checks,
* focused automated checks,
* manual workflow tests in real agents,
* packaging/release-output validation,
* when each level is required.

This matches the current recommended validation flow in `CONTRIBUTING.md`, which points developers to focused automated checks first, then manual workflow tests, then local release package inspection when needed. ([GitHub][2])

### 8. Documentation map

This should be explicit and curated.

A table works well:

| Document | Audience | Purpose | When to read |
| -------- | -------- | ------- | ------------ |

Include at least:

* `README.md`
* `CONTRIBUTING.md`
* `TESTING.md`
* `spec-driven.md`
* `extensions/EXTENSION-PUBLISHING-GUIDE.md`
* `presets/PUBLISHING.md`
* maybe `CHANGELOG.md` and release-related docs if relevant. ([GitHub][2])

This section is especially valuable because the repo’s documentation surface has grown.

### 9. Architectural invariants / guardrails

This is another high-value section.

List the things maintainers should preserve, such as:

* user workflow consistency across supported agents,
* template and script changes should remain compatible with the expected SDD flow,
* generated artifacts and packaging should remain coherent,
* docs and templates must stay aligned,
* agent-specific adaptations should not silently break the general model.

These should be framed as maintainer guardrails, not as vague philosophy. The README’s emphasis on the standard workflow and the contribution doc’s insistence on testing the CLI workflow with real agents strongly suggest this kind of invariant section is warranted. ([GitHub][1])

### 10. Common pitfalls

Very useful for new contributors.

Examples:

* changing a template without validating it through an actual agent flow,
* updating docs but not generated behavior,
* changing workflow semantics without updating memory/process docs,
* forgetting ecosystem/catalog impact,
* testing only source form but not packaged output. ([GitHub][2])

### 11. Release-awareness and compatibility notes

Brief section only.

Could cover:

* generated assets vs source assets,
* keeping changes compatible across agent modes,
* watching changelog/release behavior,
* any versioning expectations for templates/extensions/presets where applicable. ([GitHub][6])

### 12. Getting started as a maintainer

A compact onboarding checklist:

* read this document,
* read `CONTRIBUTING.md`,
* read `TESTING.md`,
* inspect repository layout,
* run local install,
* run representative workflow tests,
* make a narrow change first.

## What else to include beyond your current idea

Your instinct is right, but I would add four things that are easy to overlook:

### A. A maintainer mental model, not just repository overview

Without this, the document becomes a directory tour.

The key question is:
**How do templates, scripts, CLI/bootstrap, docs, and ecosystem surfaces combine to produce the user experience?**

That is the real “developer README”.

### B. Change-oriented guidance

The “if you want to change X, edit Y” section is disproportionately valuable.

It reduces contributor hesitation and prevents wrong-entry-point edits.

### C. Invariants / non-obvious rules

These are the things experienced maintainers know but new contributors do not.

For Spec Kit, that likely includes preserving the workflow sequence and validating changes in real agent flows rather than treating the repo as ordinary static docs. ([GitHub][2])

### D. A curated doc index

Not a raw list of files. A role-based map.

That is what turns scattered documentation into an actual developer entry point.

## What not to do

I would avoid:

* duplicating installation instructions from `README.md`,
* duplicating PR policy from `CONTRIBUTING.md`,
* duplicating detailed test procedures from `TESTING.md`,
* documenting every file,
* writing a long historical narrative.

`DEVELOPMENT.md` should stay navigational and architectural.

## Suggested section order

If you want a clean final shape, I would order it like this:

1. Purpose of this document
2. Spec Kit at a glance for maintainers
3. System mental model
4. Repository anatomy
5. Change map: if you want to change X, edit Y
6. Development workflows
7. Validation and testing map
8. Documentation map
9. Architectural invariants and guardrails
10. Common pitfalls
11. Release and compatibility notes
12. Maintainer onboarding checklist

## My recommendation on naming

`DEVELOPMENT.md` is a reasonable name here. It is more natural than `README_DEV.md`.

`README_DEV.md` is understandable, but it feels slightly ad hoc. `DEVELOPMENT.md` reads like a first-class top-level maintainer document and pairs well with `README.md`, `CONTRIBUTING.md`, `TESTING.md`, and `CHANGELOG.md`. That naming style is also consistent with the repo already having specialized top-level docs rather than overloading a second README. ([GitHub][2])

## A compact draft outline you can start from

```md
# Development Guide

## 1. Purpose
- Who this document is for
- How it differs from README.md and CONTRIBUTING.md

## 2. Spec Kit for Maintainers
- What Spec Kit is internally
- Core workflow it supports
- Main system surfaces

## 3. System Mental Model
### 3.1 Artifact and workflow lifecycle
### 3.2 Source assets vs generated/project assets
### 3.3 Templates, scripts, CLI, agent integrations, extensions, presets

## 4. Repository Anatomy
### 4.1 templates/
### 4.2 scripts/
### 4.3 CLI/package code
### 4.4 memory assets
### 4.5 extensions/
### 4.6 presets/
### 4.7 catalogs and community metadata
### 4.8 top-level docs

## 5. If You Want to Change X, Edit Y
- Generated artifact content
- Workflow behavior
- Installation/bootstrap
- Docs
- Extensions
- Presets
- Catalog/community entries

## 6. Development Workflows
### 6.1 Template changes
### 6.2 Script changes
### 6.3 CLI/bootstrap changes
### 6.4 Docs-only changes
### 6.5 Extension/preset/catalog changes

## 7. Validation and Testing Map
- Automated checks
- Manual agent-flow validation
- Packaged-output validation
- When each is needed

## 8. Documentation Map
- README.md
- CONTRIBUTING.md
- TESTING.md
- spec-driven.md
- extension/preset publishing docs
- changelog/release docs

## 9. Architectural Invariants
- Workflow consistency
- Cross-agent compatibility
- Docs/templates alignment
- Packaging/scaffolding integrity

## 10. Common Pitfalls

## 11. Release and Compatibility Notes

## 12. Maintainer Onboarding Checklist
```

This is the structure I would use unless you want `DEVELOPMENT.md` to be intentionally shorter and more of a “developer landing page” that links out aggressively.

I can turn this into a concrete first-pass `DEVELOPMENT.md` skeleton with section text, not just the outline.
