<div align="center">
    <img src="https://raw.githubusercontent.com/github/spec-kit/main/media/logo_large.webp" alt="Spec Kit Logo" width="200" height="200"/>
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
    <a href="./README.zh-CN.md">简体中文</a>
</p>

Spec Kit is an open source toolkit that gives AI coding agents structured
processes, reusable templates, and documented outcomes. Start with one of the
three processes below, customize it, or bring your own.

## Choose your process

| What you need | Process | Outcome |
| --- | --- | --- |
| Build a feature or application | [Spec-Driven Development](#spec-driven-development) | A specification carried through planning, implementation, and convergence |
| Diagnose and repair broken behavior | [Bug fixing](#bug-fixing) | An assessed cause, scoped fix, and recorded verification |
| Decide whether an idea deserves investment | [Idea assessment](#idea-assessment) | An evidence-backed go, clarify, or stop decision |

These are **independent entry points**, not three mandatory phases. SDD ships in
core; bug fixing and assessment are bundled extensions you install when needed.

<a id="-get-started"></a>
<a id="-prerequisites"></a>

## Get started

You need **Python 3.11+**, **[uv](https://github.github.io/spec-kit/install/uv.html)**,
and a supported AI coding agent on Linux, macOS, or Windows.
For **CLI setup only**, run this in your terminal to install Spec Kit and create a project:

```bash
uv tool install specify-cli
specify init my-project --integration copilot
cd my-project
```

<a id="-supported-ai-coding-agent-integrations"></a>

The examples use **GitHub Copilot's default skills mode**. Replace `copilot` with
your [integration key](https://github.github.io/spec-kit/reference/integrations.html)
to use another supported agent.

Already have code? Follow the
[existing-project guide](https://github.github.io/spec-kit/guides/existing-projects.html).
For pinned releases, other installers, CI, or troubleshooting, see
[Installation](https://github.github.io/spec-kit/installation.html).
To update an existing installation, see [Upgrade](https://github.github.io/spec-kit/upgrade.html).

Now **launch your coding agent in the project directory** and choose a process
below. Invoke each `/speckit-*` **skill in your agent's chat**, one at a time,
and review the result before continuing. These are agent skills, not terminal
commands. Other agents and modes may use
[different invocation syntax](https://github.github.io/spec-kit/reference/integrations.html#command-invocation).

<a id="-what-is-spec-driven-development"></a>
<a id="sdd-quickstart"></a>

## Spec-Driven Development

Define **what and why** before deciding **how** to build it. SDD turns your
requirements into a specification, a technical plan, and actionable tasks,
then guides implementation against those artifacts.

**Constitution once per project; specify → plan → tasks → implement → converge per feature.**

Invoke these skills in your agent's chat:

```text
/speckit-constitution Create principles focused on code quality, testing, and maintainability.
/speckit-specify Build a photo organizer with albums grouped by date and a tile preview of each album.
/speckit-plan Use Vite with vanilla JavaScript. Keep images local and store metadata in SQLite.
/speckit-tasks
/speckit-implement
/speckit-converge
```

Repeat **implement → converge** until convergence reports **Converged**.
Add clarification, checklists, and consistency analysis when you need extra
quality gates.

[SDD walkthrough](https://github.github.io/spec-kit/quickstart.html) ·
[Command reference](https://github.github.io/spec-kit/reference/agentic-sdd.html)

<a id="-bug-fixing-with-spec-kit"></a>
<a id="bug-fix-quickstart"></a>

## Bug fixing

Keep diagnosis, repair, and verification separate so the agent fixes the assessed
cause and checks the original symptom. No SDD feature workflow is required first.

**CLI setup (terminal):** install the opt-in extension from the project directory:

```bash
specify extension add bug
```

Then invoke the **assess → fix → test** skills in your agent's chat:

```text
/speckit-bug-assess "Submitting an empty password crashes the login form." slug=login-crash
/speckit-bug-fix slug=login-crash
/speckit-bug-test slug=login-crash
```

The reports live in `.specify/bugs/login-crash/`. Review the final verdict:
`verified`, `partial`, or `failed`. Missing verification is not a successful fix.

[Bug-fixing walkthrough](https://github.github.io/spec-kit/guides/bugfix.html) ·
[Command reference](https://github.github.io/spec-kit/reference/agentic-bugfix.html)

<a id="-assessing-ideas-with-spec-kit"></a>
<a id="idea-assessment-quickstart"></a>

## Idea assessment

Gather evidence before committing to an idea, whether or not it becomes software.
This standalone process works even in a project with no source code.

**CLI setup (terminal):** install the opt-in extension from the project directory:

```bash
specify extension add assess
```

Then invoke the **intake → research → define → shape → decide** skills in your agent's chat:

```text
/speckit-assess-intake "Let users work offline and sync when they reconnect." slug=offline-mode
/speckit-assess-research slug=offline-mode
/speckit-assess-define slug=offline-mode
/speckit-assess-shape slug=offline-mode
/speckit-assess-decide slug=offline-mode
```

The artifacts live in `.specify/assessments/offline-mode/`, ending in a
**go / needs-clarification / kill** decision. Resolve unknowns by refining the
existing Markdown artifacts directly or with the agent, rather than regenerating
whole stages. A `go` decision can be handed to `/speckit-specify` if you choose
to build it; stopping with a documented reason is also a useful result.

[Assessment walkthrough](https://github.github.io/spec-kit/guides/assessment.html) ·
[Command reference](https://github.github.io/spec-kit/reference/agentic-assessment.html)

<a id="-making-spec-kit-your-own-extensions--presets"></a>
<a id="-bundles-role-based-setups"></a>
<a id="-community"></a>

## Customize or bring your own process

**Extensions** add capabilities, **presets** adapt existing behavior,
**workflows** automate steps, and **bundles** package a role-based setup.
Use project-local overrides for one-off template changes.

[Customization guide](https://github.github.io/spec-kit/guides/customization.html) ·
[Community extensions, presets, bundles, and walkthroughs](https://github.github.io/spec-kit/community/overview.html)

<a id="-specify-cli-reference"></a>
<a id="available-slash-commands"></a>
<a id="-learn-more"></a>
<a id="-core-philosophy"></a>
<a id="-development-phases"></a>
<a id="-experimental-goals"></a>
<a id="-video-overview"></a>
<a id="-does-spec-kit-use-spec-kit"></a>

## Documentation

- [CLI reference](https://github.github.io/spec-kit/reference/overview.html) and [process commands](https://github.github.io/spec-kit/reference/agentic-sdd.html#command-overview)
- [SDD philosophy](https://github.github.io/spec-kit/concepts/sdd.html), [full methodology](./spec-driven.md), and [evolving existing specs](https://github.github.io/spec-kit/guides/evolving-specs.html)
- [Video overview](https://github.github.io/spec-kit/quickstart.html#video-overview) and [project history](https://github.github.io/spec-kit/history.html)
- [How Spec Kit uses Spec Kit](./CONTRIBUTING.md#does-spec-kit-use-spec-kit)

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
