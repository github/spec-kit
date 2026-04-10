# Spec Kit - March 2026 Newsletter

This edition covers Spec Kit activity in March 2026. Nine releases shipped (v0.2.0 through v0.4.3), introducing a pluggable preset system, air-gapped deployment, automatic skill registration, and seven new AI agent integrations. The community extension catalog grew past 20 entries, independent walkthroughs and blog posts proliferated, and industry coverage debated whether "vibe coding" is dead. A summary is in the table below, followed by details.

| **Spec Kit Core (Mar 2026)** | **Community & Content** | **SDD Ecosystem & Next** |
| --- | --- | --- |
| Nine releases shipped with major features: multi-catalog extensions, pluggable presets, air-gapped deployment, and auto-registration of extension skills. Seven new agents added. The repo grew from ~71k to **82,616 stars**. [\[github.com\]](https://github.com/github/spec-kit/releases) | Walkthroughs by Tiago Valverde, Alfredo Perez, and Sergey Golubev. Over 20 community extensions. The Spec Kit Assistant VS Code extension was recognized as a Community Friend. A Microsoft Learn training module became available. | ByteIota reported AWS pushing SDD as the new standard. Augment Code published a Spec Kit vs. Intent comparison. Competitors differentiate on orchestration depth and living specs; Spec Kit leads in agent breadth and portability. |

***

## Spec Kit Project Updates

### Releases Overview

**v0.2.0** (March 10) opened the month with **simultaneous multi-catalog support**, enabling both core and community extension catalogs at the same time. It added **Tabnine CLI** and **Kimi Code CLI** agents, four community extensions (Understanding, Ralph, Review, Fleet Orchestrator), and `.extensionignore` support. Patch **v0.2.1** fixed broken quickstart links and added catalog CLI help. [\[github.com\]](https://github.com/github/spec-kit/releases)

**v0.3.0** (mid-March) delivered the **pluggable preset system** with catalog, resolver, and skills propagation. Presets let teams override default templates with their own conventions, using priority-based stacking. The release also added a **/selftest.extension** for testing extensions, **Mistral Vibe CLI**, migrated **Qwen Code CLI** from TOML to Markdown, and hardened bash scripts against shell injection. New community extensions included DocGuard CDD, Archive & Reconcile, specify-status, and specify-doctor. [\[github.com\]](https://github.com/github/spec-kit/releases)

**v0.3.1** added before/after hook events, JSONC deep-merge for `settings.json`, and the **Trae IDE** agent. **v0.3.2** added **Junie**, **iFlow CLI**, and **Pi Coding Agent**, plus a preset submission template and an Extension Comparison Guide. Community extensions continued arriving: verify-tasks, conduct, cognitive-squad, speckit-utils, spec-kit-iterate, and spec-kit-learn. [\[github.com\]](https://github.com/github/spec-kit/releases)

**v0.4.0** (late March) introduced **auto-registration of extension skills** — installed extensions' commands are now automatically exposed as agent skills. It also delivered **air-gapped/offline deployment** by embedding core templates in the CLI wheel and added timestamp-based branch naming. [\[github.com\]](https://github.com/github/spec-kit/releases)

Three patches closed the month. **v0.4.1** fixed a missing Assumptions section in the spec template and improved repo root detection. **v0.4.2** added AIDE, Extensify, and Presetify to the community catalog, moved the community extensions table into the main README, and recognized the **Spec Kit Assistant VS Code extension** as a Community Friend. **v0.4.3** unified skill naming conventions and restored **PowerShell 5.1 compatibility**. [\[github.com\]](https://github.com/github/spec-kit/releases)

### Bug Fixes and Security Hardening

The most significant fix was **shell injection hardening** of bash scripts, addressing potential vulnerabilities from unsanitized git branch names and environment variables. Other fixes included switching to **global branch numbering** for consistent sequencing, suppressing git checkout exceptions and fetch stdout leaks, properly encoding JSON control characters, and adding explicit PowerShell positional binding. [\[github.com\]](https://github.com/github/spec-kit/releases)

### The Extension Ecosystem

By late March, over **20 community extensions** had been built for Spec Kit. Thulasi Rajasekaran's LinkedIn article *"The Feature That Turns Spec Kit Into a Platform"* highlighted standouts: **Conduct** (orchestrates SDD phases via sub-agents to avoid context pollution), **Verify Tasks** (catches "phantom completions" — tasks marked done with no real code), **Understanding** (31 quality metrics against specs based on IEEE/ISO standards), and the **Jira and Azure DevOps integrations**. [\[linkedin.com\]](https://www.linkedin.com/pulse/feature-turns-spec-kit-platform-extensions-presets-rajasekaran-3ejgc)

Rajasekaran argued the real significance of presets is what they enable: the same machinery that turned "User Stories" into pirate-speak "Crew Tales" could enforce compliance requirements, add mandatory threat-model sections, or require test tasks before implementation tasks. Organizations can curate available extensions by hosting custom catalog URLs. [\[linkedin.com\]](https://www.linkedin.com/pulse/feature-turns-spec-kit-platform-extensions-presets-rajasekaran-3ejgc)

## Community & Content

### Developer Walkthroughs and Blog Posts

March produced a wave of independent content as developers explored SDD in practice.

**Tiago Valverde** published *"Spec-Driven Development in Practice: A Walkthrough with Spec Kit"* on March 14. He documents building an Instagram-style photo mural feature using the full Spec Kit workflow, contrasting it with previous ad-hoc prompting: while directly prompting Claude worked for small changes, complex work led to scope creep, ambiguous requirements discovered too late, and no artifacts left behind. Valverde recommends being specific in the initial prompt, reviewing `spec.md` immediately, and highlights the clarify step as particularly valuable. A shorter companion piece, *"The Shift from Vibe Coding to Spec-Driven Development,"* appeared on March 8. [\[tiagovalverde.com\]](https://www.tiagovalverde.com/posts/spec-driven-development-in-practice-a-walkthrough-with-spec-kit)

**Alfredo Perez** published *"Build Your Own SDD Workflow"* on March 21, taking a deliberately contrarian approach. He praises SDD in principle but argues the full seven-step workflow carries too much ceremony for smaller tasks. His solution is a lean **4-step custom workflow** — `specify → plan → tasks → implement` — dropping constitution, clarify, and review, wired into the **SpecKit Companion** VS Code extension. The article highlights an important tradeoff: full rigor vs. lightweight adoption. Perez also presented this workflow at an **Angular Community Meetup** on March 25. [\[alfredo-perez.dev\]](https://www.alfredo-perez.dev/blog/2026-03-21-build-your-own-sdd-workflow)

**Sergey Golubev** of prodfeat.ai published *"20+ SDD Frameworks: A Catalog for AI Development"* on March 17. The catalog organizes **20+ frameworks in 6 categories**, highlighting **BMAD-METHOD** (~41k stars, simulates an agile team from AI roles), **QuintCode + FPF** (preserves decision rationale via a 5-phase ADI Cycle), and **cc-sdd** (~2.9k stars, enforced SDD workflow for 8 tools). Golubev presents a three-level maturity model: *Spec-First* (spec per task, discarded after), *Spec-Anchored* (living document), and *Spec-as-Source* (spec is the only artifact). His conclusion: "SDD is not a fad… AI agents generate good code when the task is well-defined. Without a spec — you're rolling the dice." [\[prodfeat.ai\]](https://www.prodfeat.ai/en/blog/2026-03-17-sdd-frameworks-catalog)

### Community Tools and Documentation

The **Spec Kit Assistant VS Code extension** was formally recognized as a Community Friend and added to the README. The README was reorganized: community extensions table moved into the main page for discoverability, a community presets section was added, and the publishing guide gained Category and Effect columns. New walkthroughs included Java brownfield, Go/React brownfield dashboard, and the Spring Boot pirate-speak preset demo. [\[github.com\]](https://github.com/github/spec-kit/releases)

A notable community project appeared: **speckit-pipeline** by iandeherdt — a pipeline atop Spec Kit with a **design loop** (designer + critic agents iterating in a browser) and a **build loop** (developer + evaluator agents verifying against acceptance criteria). An open issue (#1966) requests a built-in pipeline command, suggesting this pattern may eventually reach core.

A public **Microsoft Learn** training module, *"Implement Spec-Driven Development using the GitHub Spec Kit"* (3 hours, 13 units), provided an onboarding path for enterprise developers.

## SDD Ecosystem & Industry Trends

### The "Vibe Coding Is Dead" Narrative

*ByteIota* published *"Spec-Driven Development Kills 'Vibe Coding'"* on March 20, reporting AWS pushing SDD as the new standard. Key claims: over 100,000 developers adopting SDD approaches in early tool previews, AWS demonstrating a two-week feature completed in two days using Kiro IDE, and WEF research indicating 65% of developers expect their role to shift toward spec-first workflows in 2026. [\[byteiota.com\]](https://byteiota.com/spec-driven-development-kills-vibe-coding-march-2026/)

Critics got equal space. *Marmelab* called SDD "the exact mistakes Agile was designed to solve." An *Isoform* controlled test found SDD took 33 minutes for 689 lines vs. 8 minutes with iterative prompting, with no measured quality improvement. The emerging consensus favored hybrids — a Red Hat developer captured it: "Use the vibes to explore. Use specifications to build." Other independent articles appeared from Shimon Ifrah, Raul Proenza (Cox Automotive), CGI, and Vishal Mysore. ByteIota also raised an underappreciated concern: if specs replace coding, how do juniors build the judgment to write good specs or review AI-generated code? [\[byteiota.com\]](https://byteiota.com/spec-driven-development-kills-vibe-coding-march-2026/)

### Competitive Landscape

**Augment Code** published *"Intent vs GitHub Spec Kit (2026): Platform or Framework?"* on March 31. The core tradeoff: Spec Kit's strength is **portability** across 22+ agents; Intent offers **living specs** with automated drift detection. The comparison surfaced spec drift as a key architectural concern — Spec Kit's specs can become stale post-implementation, and while community extensions address this, native real-time drift detection is not yet in core. [\[augmentcode.com\]](https://www.augmentcode.com/tools/intent-vs-github)

The broader landscape continued evolving. OpenSpec held ~29.3k stars, BMAD-METHOD grew to ~41k, and Tessl continued in private beta. While Spec Kit leads in GitHub popularity and agent breadth, alternatives differentiate on orchestration depth (Intent, BMAD), enforced discipline (cc-sdd), decision trails (QuintCode), and spec-as-source vision (Tessl). [\[prodfeat.ai\]](https://www.prodfeat.ai/en/blog/2026-03-17-sdd-frameworks-catalog)

## Roadmap

Areas under discussion or in progress for future development:

- **Spec lifecycle management** -- supporting longer-lived specifications that evolve across multiple iterations. The Augment Code comparison and community commentary highlighted "spec drift" as a key concern. The Archive & Reconcile extension (#1844) is a community step; a core solution is expected to be a focus area. [\[augmentcode.com\]](https://www.augmentcode.com/tools/intent-vs-github) [\[github.com\]](https://github.com/github/spec-kit/releases)
- **CI/CD integration** -- incorporating Spec Kit verification into pull request workflows and failing builds when specs are out of alignment. The Jira and Azure DevOps extensions (#1764, #1734) are a first step. [\[github.com\]](https://github.com/github/spec-kit/releases)
- **End-to-end workflow automation** -- an open issue (#1966) proposes a built-in pipeline command. The community-built **speckit-pipeline** by iandeherdt already demonstrates multi-agent loops with browser verification. [\[github.com\]](https://github.com/iandeherdt/speckit-pipeline)
- **Continued agent expansion** -- seven new agents were added in March alone. The agent-agnostic design means support for emerging tools can be added by anyone. [\[byteiota.com\]](https://byteiota.com/spec-driven-development-kills-vibe-coding-march-2026/)
- **Experience simplification** -- the preset system, custom workflows, and growing walkthrough library lower the learning curve, but extension discoverability will need a more robust solution as the catalog grows. [\[github.com\]](https://github.com/github/spec-kit/releases)
- **Toward a stable release** -- nine releases in one month reflects pre-1.0 momentum. Reaching 1.0 will require stabilizing the extension and preset APIs and ensuring backward compatibility across the agent and extension surface area. [\[github.com\]](https://github.com/github/spec-kit/blob/main/newsletters/2026-February.md)


