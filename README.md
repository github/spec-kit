<div align="center">
    <img src="https://raw.githubusercontent.com/justinbrenton/spec-kit/main/media/Spec-Kit-Hermes.png" alt="Spec Kit Logo" width="200" height="200"/>
    <h1>🌱 Spec Kit</h1>
    <h3><em>Build with a spec, fix a bug, or assess an idea — with your coding agent.</em></h3>
</div>

<p align="center">
    <a href="https://github.com/github/spec-kit/releases/latest"><img src="https://img.shields.io/github/v/release/github/spec-kit" alt="Latest Release"/></a>
    <a href="https://github.com/github/spec-kit/stargazers"><img src="https://img.shields.io/github/stars/github/spec-kit?style=social" alt="GitHub stars"/></a>
    <a href="https://github.com/github/spec-kit/blob/main/LICENSE"><img src="https://img.shields.io/github/license/github/spec-kit" alt="License"/></a>
    <a href="https://github.github.io/spec-kit/"><img src="https://img.shields.io/badge/docs-GitHub_Pages-blue" alt="Documentation"/></a>
</p>

<p align="center">
    <strong>English</strong> ·
    <a href="./README.zh-CN.md">简体中文</a> ·
    <a href="./README.ja.md">日本語</a> ·
    <a href="./README.ko.md">한국어</a>
</p>

Spec Kit is an open source toolkit that gives AI coding agents structured
processes, reusable templates, and documented outcomes. Start with a ready-made
process, customize it, or bring your own.

## Choose your process

| What you need | Process | Outcome |
| --- | --- | --- |
| Build a feature or application | [Spec-Driven Development](#spec-driven-development) | A specification carried through planning, implementation, and convergence |
| Diagnose and repair broken behavior | [Bug fixing](#bug-fixing) | An assessed cause, scoped fix, and recorded verification |
| Decide whether an idea deserves investment | [Idea assessment](#idea-assessment) | An evidence-backed go, clarify, or stop decision |
| Adopt or create a different process | [Your own process](#capabilities) | A process adapted or assembled from reusable primitives |

These are independent entry points, not mandatory phases. SDD ships in core;
bug fixing and assessment are bundled extensions you install when needed, and
the primitives below let you adopt or create other processes.

## Capabilities

Spec Kit combines ready-to-use processes with composable mechanisms:

| Capability | Spec Kit mechanism |
| --- | --- |
| Connect to or switch between coding agents | [Integration](https://github.github.io/spec-kit/integrations/index.html) |
| Add a command, quality gate, or complete process | [Extension](https://github.github.io/spec-kit/reference/extensions.html) |
| Connect a process to an external tool or service | [Extension](https://github.github.io/spec-kit/reference/extensions.html) |
| React to coding-agent lifecycle events | [Extension runtime event](https://github.github.io/spec-kit/reference/extensions.html#extension-runtime-events) |
| Run extension commands before or after Spec Kit commands | [Extension hook](https://github.github.io/spec-kit/reference/extensions.html#project-extension-and-hook-configuration) |
| Adapt templates, commands, terminology, or methodology | [Preset](https://github.github.io/spec-kit/reference/presets.html) |
| Enforce organizational or regulatory standards | [Preset](https://github.github.io/spec-kit/reference/presets.html) |
| Override a template for one project | [Project-local override](https://github.github.io/spec-kit/guides/customization.html#project-local-overrides-and-resolution) |
| Automate prompts, commands, gates, and shell tasks | [Workflow](https://github.github.io/spec-kit/reference/workflows.html) |
| Modify an installed workflow without forking it | [Workflow overlay](https://github.github.io/spec-kit/reference/workflows.html#workflow-overlays) |
| Add reusable executable behavior to workflows | [Workflow step](https://github.github.io/spec-kit/reference/workflows.html#custom-step-packages) |
| Install a curated setup for a role or team | [Bundle](https://github.github.io/spec-kit/reference/bundles.html) |
| Discover community components | [Catalog](https://github.github.io/spec-kit/reference/catalogs.html) |
| Host a private catalog of approved components | [Catalog](https://github.github.io/spec-kit/reference/catalogs.html) |
| Access private catalogs and component downloads | [Authentication](https://github.github.io/spec-kit/reference/authentication.html) |
| Work offline or behind a firewall | [Local sources and self-hosted catalogs](https://github.github.io/spec-kit/install/air-gapped.html) |
| Inspect which layer supplies a command, template, or script | [Artifact inventory](https://github.github.io/spec-kit/reference/artifacts.html) |

Search the active catalogs with commands such as `specify extension search`,
`specify preset search`, `specify workflow search`, and `specify bundle search`.
Spec Kit includes community catalogs, and organizations can add their own
curated sources. Catalog listings are not audits or endorsements, so review
community source code before installing or running it.

<a id="-get-started"></a>
<a id="-prerequisites"></a>

## Get started

You need Python 3.11+, [uv](https://github.github.io/spec-kit/install/uv.html),
and a supported AI coding agent on Linux, macOS, or Windows.

Run these commands in your terminal to install Spec Kit and create a project.
This example uses GitHub Copilot.

```bash
uv tool install specify-cli
specify init my-project --integration copilot
cd my-project
```

<a id="-supported-ai-coding-agent-integrations"></a>

After installing the Specify CLI and creating your project, launch your coding
agent in the project directory, then choose a process below.

For other setups:

- [Installation](https://github.github.io/spec-kit/installation.html) for pinned releases, other installers, CI, and troubleshooting.
- [Existing projects](https://github.github.io/spec-kit/guides/existing-projects.html) to start with code you already have.
- [Other agents](https://github.github.io/spec-kit/integrations/index.html) for integration keys and [invocation syntax](https://github.github.io/spec-kit/integrations/cli.html#command-invocation).
- [Upgrade](https://github.github.io/spec-kit/upgrade.html) to update an existing installation.

<a id="-what-is-spec-driven-development"></a>
<a id="sdd-quickstart"></a>

## Spec-Driven Development

Define what to build and why, then turn the specification into a plan, tasks,
and working code.

The minimal flow is shown below. Create a constitution once per project and
repeat the remaining steps for each feature. Run these skills in your agent's
chat, not your terminal, one at a time, reviewing each result before continuing.

This example uses GitHub Copilot's default skills syntax. For another agent,
use its [equivalent invocation syntax](https://github.github.io/spec-kit/integrations/cli.html#command-invocation).

```text
/speckit-constitution Create principles focused on code quality, testing, and maintainability.
/speckit-specify Build a photo organizer with albums grouped by date and a tile preview of each album.
/speckit-plan Use Vite with vanilla JavaScript. Keep images local and store metadata in SQLite.
/speckit-tasks
/speckit-implement
/speckit-converge
```

Repeat implement and converge until convergence reports `Converged`.
For clarification, checklists, and consistency analysis, see the SDD walkthrough.

[SDD walkthrough](https://github.github.io/spec-kit/quickstart.html) ·
[Command reference](https://github.github.io/spec-kit/reference/agentic-sdd.html)

<a id="-bug-fixing-with-spec-kit"></a>
<a id="bug-fix-quickstart"></a>

## Bug fixing

Assess the cause, fix the bug, and verify the original symptom is resolved.
No SDD feature workflow is required first.

Install the bug-fixing extension in your terminal, from the project directory:

```bash
specify extension add bug
```

Run these skills in your agent's chat, not your terminal, one at a time,
reviewing each result before continuing.

This example uses GitHub Copilot's default skills syntax. For another agent,
use its [equivalent invocation syntax](https://github.github.io/spec-kit/integrations/cli.html#command-invocation).

```text
/speckit-bug-assess "Submitting an empty password crashes the login form." slug=login-crash
/speckit-bug-fix slug=login-crash
/speckit-bug-test slug=login-crash
```

Review the reports in `.specify/bugs/login-crash/`. The final verdict is
`verified`, `partial`, or `failed`; only `verified` confirms a successful fix.

[Bug-fixing walkthrough](https://github.github.io/spec-kit/guides/bugfix.html) ·
[Command reference](https://github.github.io/spec-kit/reference/agentic-bugfix.html)

<a id="-assessing-ideas-with-spec-kit"></a>
<a id="idea-assessment-quickstart"></a>

## Idea assessment

Gather evidence to decide whether an idea is worth pursuing.
No source code or SDD feature workflow is required.

Install the assessment extension in your terminal, from the project directory:

```bash
specify extension add assess
```

Run these skills in your agent's chat, not your terminal, one at a time,
reviewing each result before continuing.

This example uses GitHub Copilot's default skills syntax. For another agent,
use its [equivalent invocation syntax](https://github.github.io/spec-kit/integrations/cli.html#command-invocation).

```text
/speckit-assess-intake "Let users work offline and sync when they reconnect." slug=offline-mode
/speckit-assess-research slug=offline-mode
/speckit-assess-define slug=offline-mode
/speckit-assess-shape slug=offline-mode
/speckit-assess-decide slug=offline-mode
```

Review the artifacts in `.specify/assessments/offline-mode/` and the final
decision: `go`, `needs-clarification`, or `kill`. Resolve unknowns by editing the
existing Markdown artifacts, directly or with your agent, rather than rerunning
whole stages. If you choose to build a software idea with a `go` decision,
establish a project constitution if needed, then pass the handoff summary from
`decision.md` to `/speckit-specify`. Stopping with a documented reason is also a
useful outcome.

[Assessment walkthrough](https://github.github.io/spec-kit/guides/assessment.html) ·
[Command reference](https://github.github.io/spec-kit/reference/agentic-assessment.html)

<a id="-making-spec-kit-your-own-extensions--presets"></a>
<a id="-bundles-role-based-setups"></a>
<a id="-community"></a>

## Customize or bring your own process

Customize Spec-Driven Development, bug fixing, or idea assessment to fit your
team's standards. Or bring your own process without adopting any of them.
Combine the [capabilities above](#capabilities) to match your goal:

- Adapt an existing process with a preset, such as requiring regulatory traceability in plans. Use a project-local override for a one-off template change.
- Bring your own process by adding its commands through an extension and exposing them to your coding agent through an integration.
- Automate commands and checks in a workflow. Use overlays to adapt an installed workflow without forking it, or add custom workflow steps when the built-in types are not enough.
- Share a reusable setup by packaging its extensions, presets, workflows, and workflow steps in a bundle.

Start with the smallest change that meets your needs; you do not have to replace
the whole process.

[Customization guide](https://github.github.io/spec-kit/guides/customization.html) ·
[Community components and walkthroughs](https://github.github.io/spec-kit/community/overview.html)

<a id="-specify-cli-reference"></a>
<a id="available-slash-commands"></a>
<a id="-learn-more"></a>
<a id="-core-philosophy"></a>
<a id="-development-phases"></a>
<a id="-experimental-goals"></a>
<a id="-does-spec-kit-use-spec-kit"></a>

## Documentation

- [CLI reference](https://github.github.io/spec-kit/reference/overview.html) and [process commands](https://github.github.io/spec-kit/reference/agentic-sdd.html#command-overview)
- [SDD philosophy](https://github.github.io/spec-kit/concepts/sdd.html), [full methodology](./spec-driven.md), and [evolving existing specs](https://github.github.io/spec-kit/guides/evolving-specs.html)
- [Project history](https://github.github.io/spec-kit/history.html)
- [How Spec Kit uses Spec Kit](./CONTRIBUTING.md#does-spec-kit-use-spec-kit)

## In the news

- [Open Source Friday: Spec Kit Part 2](https://www.youtube.com/watch?v=8hHCpNVLhmI) (October 16, 2026) — Manfred Riem and Nicole Haugen discuss Spec Kit 1.0 and the expanded toolkit.
- [Open Source Friday with Spec Kit](https://www.youtube.com/watch?v=2IArMAhkJcE) (May 8, 2026) — An introduction and SDD demonstration with Manfred Riem.

## Star history

<p align="center">
    <a href="https://www.star-history.com/#github/spec-kit&Date">
        <picture>
            <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/svg?repos=github%2Fspec-kit&type=Date&theme=dark"/>
            <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/svg?repos=github%2Fspec-kit&type=Date"/>
            <img src="https://api.star-history.com/svg?repos=github%2Fspec-kit&type=Date" alt="Spec Kit star history chart"/>
        </picture>
    </a>
</p>

<p align="center">
    <em>Thanks to everyone who helps Spec Kit shine.</em>
</p>

<a id="-support"></a>

## Support and contributing

[Report a bug or request a feature](https://github.com/github/spec-kit/issues/new) ·
[Contributing guide](./CONTRIBUTING.md) · [Code of conduct](./CODE_OF_CONDUCT.md)

<a id="-license"></a>

Spec Kit is [MIT licensed](./LICENSE).
