# Extension Comparison Guide

A quick-reference for choosing between community extensions, organized by what they operate on.

For installation instructions, see the [Extension User Guide](EXTENSION-USER-GUIDE.md). For the full list of available extensions, see the [Community Catalog](catalog.community.json).

## For Extension Authors

When publishing a new extension, add a row to the appropriate category table below. If your extension doesn't fit an existing category, add a new one.

---

## Docs

Extensions that read, validate, or generate spec artifacts, plans, tasks, or project memory.

| Extension | Phase | Effect | What It Does |
|-----------|-------|--------|--------------|
| [Understanding](https://github.com/Testimonial/understanding) | Pre-implementation | Read-only | Runs 31 IEEE/ISO metrics against your specs and reports quality scores |
| [DocGuard](https://github.com/raccioly/docguard) | Pre-implementation | Read+Write | Validates, scores, and traces docs using CDD enforcement rules and hooks |
| [Cognitive Squad](https://github.com/Testimonial/cognitive-squad) | Pre-implementation | Read+Write | Runs a multi-agent analysis pipeline before code is written |
| [V-Model](https://github.com/leocamello/spec-kit-v-model) | Pre-implementation | Read+Write | Generates paired dev specs and test specs with traceability links |
| [Iterate](https://github.com/imviancagrace/spec-kit-iterate) | During implementation | Read+Write | Lets you define a spec change and apply it to docs mid-build |
| [Spec Sync](https://github.com/bgervin/spec-kit-sync) | Anytime | Read+Write | Scans for drift between specs and code, offers AI-assisted fixes |
| [Reconcile](https://github.com/stn1slv/spec-kit-reconcile) | Post-implementation | Read+Write | Rewrites specs, plan, and tasks to match what was actually built |
| [Retrospective](https://github.com/emi-dm/spec-kit-retrospective) | Post-implementation | Read+Write | Scores spec adherence, explains where drift happened, optionally patches specs |
| [Learning](https://github.com/imviancagrace/spec-kit-learn) | Post-implementation | Read+Write | Produces educational guides from your implementation for knowledge transfer |
| [Archive](https://github.com/stn1slv/spec-kit-archive) | Post-merge | Read+Write | Merges feature knowledge into project-level memory after a feature ships |

## Code

Extensions that review, validate, or modify source code.

| Extension | Phase | Effect | What It Does |
|-----------|-------|--------|--------------|
| [Fleet Orchestrator](https://github.com/sharathsatish/spec-kit-fleet) | During implementation | Read+Write | Walks through the full SDD lifecycle with human approval gates at each phase |
| [Ralph Loop](https://github.com/Rubiss/spec-kit-ralph) | During implementation | Read+Write | Hands specs to an AI agent and loops until implementation is complete |
| [Cleanup](https://github.com/dsrednicki/spec-kit-cleanup) | Post-implementation | Read+Write | Auto-fixes small tech debt, creates tasks for medium issues, reports large ones |
| [Review](https://github.com/ismaelJimenez/spec-kit-review) | Post-implementation | Read-only | Runs 7 specialized review agents across code quality, tests, types, error handling |
| [Verify](https://github.com/ismaelJimenez/spec-kit-verify) | Post-implementation | Read-only | Compares code against spec artifacts and returns a pass/fail result |

## Third-Party Integrations

Extensions that sync with external platforms.

| Extension | Phase | Effect | What It Does |
|-----------|-------|--------|--------------|
| [Jira](https://github.com/mbachorik/spec-kit-jira) | Cross-cutting | Read+Write | Creates Jira Epics, Stories, and Issues from your specs and task breakdowns |
| [Azure DevOps](https://github.com/pragya247/spec-kit-azure-devops) | Cross-cutting | Read+Write | Pushes specs and tasks to Azure DevOps as work items |

## Project Visibility

Extensions that report on project health or workflow progress.

| Extension | Phase | Effect | What It Does |
|-----------|-------|--------|--------------|
| [Doctor](https://github.com/KhawarHabibKhan/spec-kit-doctor) | Project setup | Read-only | Checks project structure, agents, features, scripts, extensions, and git for issues |
| [Status](https://github.com/KhawarHabibKhan/spec-kit-status) | Project setup | Read-only | Shows your active feature, artifact status, task completion, and current phase |
