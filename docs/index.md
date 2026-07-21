<div class="landing-hero">

# GitHub Spec Kit

**Spec-Driven Development or your own process — step by step or as an automated workflow.**

Spec Kit is an extensible, intent-driven harness that pushes any coding agent beyond code, guiding it across your SDLC or any business process. Use it for [Spec-Driven Development](concepts/sdd.md) (SDD), where you describe _what_ to build and refine it through structured phases. Run it step by step, automate it end to end, or shape a process of your own, keeping intent at the center.

<a href="installation.md" class="btn btn-primary btn-lg">Install Spec Kit</a>&nbsp;
<a href="quickstart.md" class="btn btn-outline-primary btn-lg">Quick Start</a>

</div>

---

<div class="pillar-grid">

<div class="pillar-card">

### Spec-driven by default

The core SDD process ships ready to use: **Spec → Plan → Tasks → Implement**.

Define what to build before building it. Rich templates, quality checklists, and cross-artifact analysis come out of the box. Each phase produces a Markdown artifact that feeds the next — giving your AI coding agent structured context instead of ad-hoc prompts.

<a href="quickstart.md" class="pillar-link">Walk through the workflow →</a>

</div>

<div class="pillar-card">

### Use any coding agent

<span class="pillar-stat">35 integrations</span> — Copilot, Gemini, Codex, Kilo Code, Zed, Claude, Forge, Kiro, and more. Switch freely between agents with a single command. No lock-in.

Run `specify init` with your agent of choice and Spec Kit sets up the right command files and directory structures automatically. If your agent isn't listed, the `generic` integration is an escape hatch for any tool.

<a href="reference/integrations.md" class="pillar-link">See all integrations →</a>

</div>

<div class="pillar-card">

### Make it your own

<span class="pillar-stat">138 community extensions</span> (70+ authors), <span class="pillar-stat">25 presets</span>, and growing. Tune the core process with presets, extend it with extensions, orchestrate it with workflows, and package it all up as bundles you can share — or replace the process entirely. The process itself lives in these building blocks, so you're never locked to SDD, or even to software.

Including entirely different processes:

- **AIDE** — 7-step AI-driven engineering lifecycle
- **Canon** — baseline-driven workflows (spec-first, code-first, spec-drift)
- **Product Forge** — product-management-oriented SDD
- **FX→.NET** — end-to-end .NET Framework migration across 7 phases
- **MAQA** — multi-agent orchestration with quality assurance gates
- **Fiction Book Writing** — novels and long-form fiction, from story bible to submission

<a href="reference/presets.md" class="pillar-link">Presets →</a>&nbsp;&nbsp;
<a href="reference/extensions.md" class="pillar-link">Extensions →</a>&nbsp;&nbsp;
<a href="reference/workflows.md" class="pillar-link">Workflows →</a>&nbsp;&nbsp;
<a href="reference/bundles.md" class="pillar-link">Bundles →</a>

</div>

<div class="pillar-card">

### Integrate into your organization

Works offline, behind firewalls, and on **Windows, macOS, and Linux**. Host your own catalogs to curate what integrations, extensions, presets, workflows, and bundles your organization discovers and recommends.

Community extensions like CI Guard and Architecture Guard add compliance gates and governance that fit the way your team already works.

<a href="install/air-gapped.md" class="pillar-link">Enterprise / Air-Gapped →</a>&nbsp;&nbsp;
<a href="reference/overview.md" class="pillar-link">Reference →</a>

</div>

</div>

---

<div class="community-section">

## Built by the community

**240+ contributors** power the Spec Kit ecosystem — from core integrations to entirely new processes. Anyone can create and publish an extension, preset, or workflow.

<div class="stats-grid">
  <div class="stat-item">
    <span class="stat-number">121K+</span>
    <span class="stat-label">GitHub stars</span>
  </div>
  <div class="stat-item">
    <span class="stat-number">240+</span>
    <span class="stat-label">Contributors</span>
  </div>
  <div class="stat-item">
    <span class="stat-number">35</span>
    <span class="stat-label">Integrations</span>
  </div>
  <div class="stat-item">
    <span class="stat-number">138</span>
    <span class="stat-label">Extensions</span>
  </div>
  <div class="stat-item">
    <span class="stat-number">25</span>
    <span class="stat-label">Presets</span>
  </div>
  <div class="stat-item">
    <span class="stat-number">6</span>
    <span class="stat-label">Friends projects</span>
  </div>
</div>

<a href="community/presets.md">Presets</a> · <a href="community/walkthroughs.md">Walkthroughs</a> · <a href="community/friends.md">Friends</a>

</div>

---

## Explore the docs

<div class="nav-cards">
  <a href="quickstart.md" class="nav-card">
    <strong>Getting Started</strong>
    <span>Install, configure, and run your first SDD workflow</span>
  </a>
  <a href="reference/overview.md" class="nav-card">
    <strong>Reference</strong>
    <span>Core commands, integrations, extensions, presets, and workflows</span>
  </a>
  <a href="community/overview.md" class="nav-card">
    <strong>Community</strong>
    <span>Extensions, presets, walkthroughs, and friend projects</span>
  </a>
  <a href="local-development.md" class="nav-card">
    <strong>Development</strong>
    <span>Contribute to Spec Kit</span>
  </a>
  <a href="concepts/sdd.md" class="nav-card">
    <strong>What is SDD?</strong>
    <span>The philosophy behind Spec-Driven Development</span>
  </a>
</div>

---

<div class="footer-cta">

```bash
uv tool install specify-cli
specify init my-project --integration copilot
```

Ready to start? Follow the [Quick Start Guide](quickstart.md).

</div>

<p class="text-end small text-body-secondary">Last updated: July 16, 2026</p>
