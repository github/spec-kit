<div class="landing-hero">

<img class="landing-hero-logo" src="images/spec-kit-logo.webp" alt="" width="120" height="120">

# GitHub Spec Kit

**Build with a spec, fix a bug, or assess an idea — with your coding agent.**

Spec Kit gives your coding agent structured processes that keep intent and evidence ahead of implementation. Start with Spec-Driven Development (SDD), bug fixing, or idea assessment. Run a process step by step, automate it, or [shape one of your own](how-to/customization.md) — including processes beyond software development.

<a href="installation.md" class="btn btn-primary btn-lg">Install Spec Kit</a>&nbsp;
<a href="#choose-your-process" class="btn btn-outline-primary btn-lg">Choose your process</a>

</div>

---

## Choose your process

| What you need | Start here | What you get | Command reference |
| --- | --- | --- | --- |
| Build a feature or application | [Spec-Driven Development](quickstart.md) | A specification carried through planning, implementation, and convergence | [Agentic SDD](reference/agentic-sdd.md) |
| Diagnose and repair broken behavior | [Bug fixing](guides/bugfix.md) | An assessed cause, scoped fix, and recorded verification | [Agentic Bug Fix](reference/agentic-bugfix.md) |
| Decide whether an idea deserves investment | [Idea assessment](guides/assessment.md) | An evidence-backed go, clarify, or stop decision | [Agentic Idea Assessment](reference/agentic-assessment.md) |

These are independent entry points, not mandatory phases. SDD ships in core.
Bug fixing and assessment are bundled, opt-in extensions. Assessment can stand
alone; a decision to proceed does not automatically start implementation.

See [how the Spec Kit project runs its agentic SDLC](guides/agentic-sdlc.md)
and where it uses Spec Kit itself.

Adding Spec Kit to an established codebase? Start with the
[existing-project guide](how-to/existing-projects.md).

## Specify CLI

The Specify CLI (`specify`) initializes projects and manages integrations,
extensions, presets, workflows, workflow steps, and bundles. Process commands such as
`/speckit.specify` run inside your coding agent, not in the terminal; see
[command invocation](integrations/cli.md#command-invocation) for your agent's
syntax and the command references above for arguments, artifacts, and quality
gates.

| Shared capability | Reference |
| --- | --- |
| Initialize projects, check installed tools, and inspect version and system information | [Core Commands](overview/core.md) |
| Expose supported Specify operations to MCP clients through an experimental local stdio server | [MCP Server](overview/mcp.md) |
| Inspect visible commands, templates, scripts, and hooks, including winning and hidden composition layers | [Artifacts](overview/artifacts.md) |
| Discover components through built-in, community, or private catalogs and understand source priority and trust | [Catalogs](overview/catalogs.md) |

---

<div class="pillar-grid">

<div class="pillar-card">

### Spec-driven by default

The core SDD process ships ready to use: **Specify → Plan → Tasks → Implement → Converge**.

Define what to build before building it. Rich templates, quality checklists, and cross-artifact analysis come out of the box. Each phase produces a Markdown artifact that feeds the next — giving your AI coding agent structured context instead of ad-hoc prompts.

<a href="quickstart.md" class="pillar-link">Walk through the workflow →</a>

</div>

<div class="pillar-card">

### Use any coding agent

<span class="pillar-stat">43 integration options</span> — 41 coding-agent integrations, plus `generic` for other tools and `none` for agent-neutral scaffolding. Choose Copilot, Gemini, Codex, Kilo Code, Zed, Claude, Forge, Kiro, and more. Switch freely between agents with a single command. No lock-in.

Run `specify init` with your agent of choice and Spec Kit sets up the right command files and directory structures automatically. If your agent isn't listed, the `generic` integration is an escape hatch for any tool.

<a href="integrations/index.md" class="pillar-link">See all integrations →</a>

</div>

<div class="pillar-card">

### Make it your own

<span class="pillar-stat">186 community extensions</span>, <span class="pillar-stat">42 community presets</span>, and growing. Tune the core process with presets, extend it with extensions, orchestrate it with workflows, and package it all up as bundles you can share — or replace the process entirely. The process itself lives in these building blocks, so you're never locked to SDD, or even to software.

Explore community processes, integrations, and quality gates:

- **[Product Forge](https://github.com/VaiYav/speckit-product-forge)** — product-lifecycle orchestration, from research to release readiness
- **[Architecture Guard](https://github.com/DyanGalih/architecture-guard)** — architectural drift detection and governance
- **[DocGuard](https://github.com/raccioly/docguard)** — documentation integrity, traceability, and lifecycle checks
- **[Quality Gates](https://github.com/schwichtgit/spec-gates)** — policy-driven checks at agent, Git, and CI boundaries
- **[Epic](https://github.com/pmckeown/spec-kit-epic)** — split large initiatives into ordered, coordinated features
- **[Linear Weave](https://github.com/tonydwoodhouse/spec-kit-linear-weave)** — connect requirements, tasks, and statuses with Linear

Beyond software, the **[Fiction Book Writing preset](https://github.com/adaumann/speckit-preset-fiction-book-writing)** supports novels and long-form fiction, from story bible to submission.

Featuring these independently maintained community projects is not an audit or endorsement. Review their source code before installation and use.

<a href="presets/overview.md" class="pillar-link">Presets →</a>&nbsp;&nbsp;
<a href="extensions/overview.md" class="pillar-link">Extensions →</a>&nbsp;&nbsp;
<a href="workflows/overview.md" class="pillar-link">Workflows →</a>&nbsp;&nbsp;
<a href="workflow-steps/overview.md" class="pillar-link">Workflow Steps →</a>&nbsp;&nbsp;
<a href="bundles/overview.md" class="pillar-link">Bundles →</a>

</div>

<div class="pillar-card">

### Integrate into your organization

Works offline, behind firewalls, and on **Windows, macOS, and Linux**. Host your own catalogs to curate what integrations, extensions, presets, workflows, and bundles your organization discovers and recommends.

Community extensions like Quality Gates and Architecture Guard add policy checks and governance that fit the way your team already works.

<a href="install/air-gapped.md" class="pillar-link">Enterprise / Air-Gapped →</a>&nbsp;&nbsp;
<a href="overview/catalogs.md" class="pillar-link">Catalogs →</a>

</div>

</div>

---

<div class="community-section">

## Built by the community

**320+ contributors** have helped build Spec Kit. The wider community builds everything from integrations to entirely new processes. Anyone can create and publish an extension, preset, or workflow.

<div class="stats-grid">
  <div class="stat-item">
    <span class="stat-number">147K+</span>
    <span class="stat-label">GitHub stars</span>
  </div>
  <div class="stat-item">
    <span class="stat-number">320+</span>
    <span class="stat-label">Contributors</span>
  </div>
  <div class="stat-item">
    <span class="stat-number">43</span>
    <span class="stat-label">Integration options</span>
  </div>
  <div class="stat-item">
    <span class="stat-number">186</span>
    <span class="stat-label">Community extensions</span>
  </div>
  <div class="stat-item">
    <span class="stat-number">42</span>
    <span class="stat-label">Community presets</span>
  </div>
  <div class="stat-item">
    <span class="stat-number">11</span>
    <span class="stat-label">Friend projects</span>
  </div>
</div>

<a href="community/presets.md">Presets</a> · <a href="community/walkthroughs.md">Walkthroughs</a> · <a href="community/friends.md">Friends</a>

</div>

---

## Explore the docs

<div class="nav-cards">
  <a href="guides/agentic-sdlc.md" class="nav-card">
    <strong>Spec Kit's Agentic SDLC</strong>
    <span>How this project assesses, builds, tests, ships, and repairs changes</span>
  </a>
  <a href="quickstart.md" class="nav-card">
    <strong>Spec-Driven Development</strong>
    <span>Define, plan, implement, and converge on a feature</span>
  </a>
  <a href="guides/bugfix.md" class="nav-card">
    <strong>Bug Fixing</strong>
    <span>Assess the cause, apply a scoped fix, and verify the result</span>
  </a>
  <a href="guides/assessment.md" class="nav-card">
    <strong>Idea Assessment</strong>
    <span>Research an idea and decide whether it deserves investment</span>
  </a>
  <a href="how-to/customization.md" class="nav-card">
    <strong>Adapt Spec Kit to your process</strong>
    <span>Adapt a process, add capabilities, or package a role-based setup</span>
  </a>
  <a href="how-to/existing-projects.md" class="nav-card">
    <strong>Existing Projects</strong>
    <span>Adopt Spec Kit safely in an established codebase</span>
  </a>
  <a href="upgrade.md" class="nav-card">
    <strong>Upgrade</strong>
    <span>Keep an existing Spec Kit project current across releases</span>
  </a>
  <a href="overview/core.md" class="nav-card">
    <strong>Core Commands</strong>
    <span>Initialize projects, check tools, and inspect version and system information</span>
  </a>
  <a href="community/overview.md" class="nav-card">
    <strong>Community</strong>
    <span>Community integrations, extensions, presets, workflows, steps, bundles, and companion resources</span>
  </a>
  <a href="local-development.md" class="nav-card">
    <strong>Develop Spec Kit locally</strong>
    <span>Run, debug, and check changes to Spec Kit itself</span>
  </a>
  <a href="how-to/index.md" class="nav-card">
    <strong>How to</strong>
    <span>Understand and apply Spec Kit practices to your project work</span>
  </a>
  <a href="overview/history.md" class="nav-card">
    <strong>History</strong>
    <span>How Spec Kit grew from its SDD foundation into an extensible process harness</span>
  </a>
</div>

---

<div class="footer-cta">

```bash
uv tool install specify-cli
specify init my-project --integration copilot
```

Ready to start? [Choose your process](#choose-your-process).

</div>

## See also

Each component has its own guide and management reference:

| Component | Guide | CLI reference |
| --- | --- | --- |
| Integrations | [Agent setup and delivery](integrations/index.md) | [Integration management](integrations/cli.md) |
| Extensions | [Add capabilities, commands, and hooks](extensions/overview.md) | [Extension management](extensions/cli.md) |
| Presets | [Customize templates, commands, and scripts](presets/overview.md) | [Preset management](presets/cli.md) |
| Workflows | [Automate repeatable, resumable processes](workflows/overview.md) | [Workflow management](workflows/cli.md) |
| Workflow Steps | [Reuse built-in behavior or develop custom types](workflow-steps/overview.md) | [Step management](workflow-steps/cli.md) |
| Bundles | [Install a versioned setup of existing components](bundles/overview.md) | [Bundle management](bundles/cli.md) |

For private catalogs, downloads, and release checks, see
[Configure authentication](reference/authentication.md). To choose which
building blocks fit your needs, see
[Adapt Spec Kit to your process](how-to/customization.md).

<p class="text-end small text-body-secondary">Last updated: November 4, 2026</p>
