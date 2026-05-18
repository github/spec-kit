<div class="landing-hero">

# GitHub Spec Kit

**Define what to build before building it — with any AI coding agent.**

Spec Kit is a toolkit for [Spec-Driven Development](concepts/sdd.md) (SDD), a methodology that puts specifications at the center of AI-assisted software development. Instead of jumping straight to code, you describe *what* to build, refine it through structured phases, and let your AI coding agent implement it.

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

<span class="pillar-stat">30 integrations</span> — Copilot, Gemini, Codex, Windsurf, Claude, Forge, Kiro, and more. Switch freely between agents with a single command. No lock-in.

Run `specify init` with your agent of choice and Spec Kit sets up the right command files, context rules, and directory structures automatically. If your agent isn't listed, the `generic` integration is an escape hatch for any tool.

<a href="reference/integrations.md" class="pillar-link">See all integrations →</a>

</div>

<div class="pillar-card">

### Make it your own

<span class="pillar-stat">91 community extensions</span> (50+ authors), <span class="pillar-stat">18 presets</span>, and growing. Tune the core process with presets, extend it with extensions, orchestrate it with workflows, or replace it entirely. Build and publish your own.

Including entirely different SDD processes:

- **AIDE** — 7-step AI-driven engineering lifecycle
- **Canon** — baseline-driven workflows (spec-first, code-first, spec-drift)
- **Product Forge** — product-management-oriented SDD
- **FX→.NET** — end-to-end .NET Framework migration across 7 phases
- **MAQA** — multi-agent orchestration with quality assurance gates

<a href="community/presets.md" class="pillar-link">Browse community presets →</a>

</div>

<div class="pillar-card">

### Integrate into your organization

Works offline, behind firewalls, and on **Windows, macOS, and Linux**. Host your own extension and preset catalogs so your organization controls what gets installed.

Community extensions like CI Guard and Architecture Guard add compliance gates and governance that fit the way your team already works.

<a href="installation.md" class="pillar-link">Installation guide →</a>&nbsp;&nbsp;
<a href="reference/extensions.md" class="pillar-link">Extensions reference →</a>

</div>

</div>

---

<div class="community-section">

## Built by the community

**200+ contributors** power the Spec Kit ecosystem — from core integrations to entirely new development processes. Anyone can create and publish an extension, preset, or workflow.

<div class="stats-grid">
  <div class="stat-item">
    <span class="stat-number">96K+</span>
    <span class="stat-label">GitHub stars</span>
  </div>
  <div class="stat-item">
    <span class="stat-number">200+</span>
    <span class="stat-label">Contributors</span>
  </div>
  <div class="stat-item">
    <span class="stat-number">30</span>
    <span class="stat-label">Integrations</span>
  </div>
  <div class="stat-item">
    <span class="stat-number">91</span>
    <span class="stat-label">Extensions</span>
  </div>
  <div class="stat-item">
    <span class="stat-number">18</span>
    <span class="stat-label">Presets</span>
  </div>
  <div class="stat-item">
    <span class="stat-number">4</span>
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
uvx --from git+https://github.com/github/spec-kit.git
specify init my-project --integration copilot
```

Ready to start? Follow the [Quick Start Guide](quickstart.md).

</div>
