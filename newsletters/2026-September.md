# Spec Kit - September 2026 Newsletter

This edition covers Spec Kit activity in September 2026 — the first full month in the **v1.0.x line**, with eleven patch releases (v1.0.3 through v1.0.13). Three currents ran through it. First, the **composition algebra deepened** where August's roadmap pointed — presets can now require an extension, workflows gained reusable slots, and steps can carry per-step integration configuration. Second, a new **`specify artifact` introspection surface** gave tooling a machine-readable view of how extensions, presets, and hooks compose, followed by a broad **CLI reorganization**. Third, the **security-and-robustness campaign** continued as routine. In the broader ecosystem, the month's headline was first-party: **Microsoft shipped the first database extension for Spec Kit** — an Azure Cosmos DB extension in public preview. A summary is in the table below, followed by details.

| **Spec Kit Core (Sep 2026)** | **Community & Content** | **SDD Ecosystem & Next** |
| --- | --- | --- |
| Eleven patch releases (v1.0.3–v1.0.13). Headlines: the **composition algebra deepened** with preset **`requires.extensions`**, **workflow slots**, and **per-step integration config**; a new **`specify artifact`** introspection surface that exposes composition stacks and hook contributions as JSON; a late-month **CLI reorganization** into per-domain command families; and a continued **security-hardening** wave (tag-pinned catalog URLs, TOCTOU, archive checksums, component pin verification). The built-in integrations catalog reached **42** with Docker Agent, DeepSeek Harness, Muse Code, and MiniMax Code, plus a **Bitbucket** auth provider. The repo grew from ~132,000 to **~139,700 stars**, passing `golang/go` and `microsoft/PowerToys`. [\[github.com\]](https://github.com/github/spec-kit/releases) | The community extension catalog grew from 162 to **176 entries**; presets reached **40**, community workflows held at **2**, and bundles reached **3** with the Agentstandards Multi-Vendor Architecture bundle. Coverage was substantial, led by a first-party Microsoft DevBlogs post, two Microsoft-MVP posts, and a wave of token-cost critiques and multi-framework field guides. A **Japanese README** shipped. | **Microsoft shipped the first database extension** for Spec Kit — Azure Cosmos DB in public preview, with a candid efficacy section — a first-party (not third-party) milestone that opens a new extension category. The genuine third-party signal is the community catalog's own growth. The "which SDD platform" framing hardened around the maturing 1.x line. |

***

> **1.0 Is Just a Number.** August put a number on the box; September asked what the number was worth. The answer was a month of steady releases — shipped not to defend a stable API, but to keep reshaping the five primitives in the open. That is the argument of 1.0 made ordinary: when an agent can mechanically follow a breaking change to its call sites, a major version stops being insurance and starts being punctuation. So the project spent the month iterating rather than standing still — tightening the joints between its primitives, teaching its tooling to describe itself, and keeping the security work as routine as the releases. The extension model, meanwhile, kept drawing builders — a growing community catalog, and, from a Microsoft product team, the first database extension. None of this happens without the community — the contributors, extension and preset authors, bundle builders, agent-integration maintainers, and practitioners writing in more than 20 languages. Thank you.

## Spec Kit Project Updates

### Releases Overview

**v1.0.3–v1.0.13** (September 1–29) ran the post-milestone patch train at a steady cadence — eleven releases in thirty days, roughly one every two to three days, with PyPI `specify-cli` kept in lockstep. Rather than a feature drop per release, each build carried the fortnight's workflow-engine, catalog, bundler, cross-platform, and integration fixes into a published line. The cadence held steady even as the engineering focus rotated — composition primitives early, the `specify artifact` introspection surface mid-month, a large CLI reorganization late — and the repository climbed from roughly 132,000 to about 139,700 stars, passing both `golang/go` and `microsoft/PowerToys`. [\[github.com\]](https://github.com/github/spec-kit/releases)

### The Composition Algebra Deepens

August's roadmap flagged "finer-grained composition points," a preset that could "declare a required extension," and "reusable workflow slots." All three shipped. Presets can now declare the extensions they assume through **`requires.extensions`** (#4250), so installing a preset brings along the behavior it depends on rather than silently assuming it. **Workflow slots** (#4352) add named, reusable insertion points to workflow definitions — the same move the core made internally, turning controlled customization into filling a slot rather than replacing an entire flow. And **per-step integration configuration** (#4425) lets an individual workflow step carry the integration settings it needs instead of inheriting one flow-wide configuration. The through-line is the same as the 1.0.0 story, pushed one level finer: the primitives are increasingly a set of **named, overridable joints** that presets, workflows, and steps compose against. [\[github.com\]](https://github.com/github/spec-kit/releases)

### A Machine-Readable View: `specify artifact`

September's most structurally significant new feature was the **`specify artifact` introspection surface**. The base command exposes a project's **composition stacks as JSON** (#4305), a follow-up surfaces **hook contributions and runtime bindings** through the same command (#4348), and a third **resolves each contribution back to the artifact that owns it** (#4550). Together they give tooling — and agents — a machine-readable answer to "what actually composes here, and who contributed it?" as the number of extensions, presets, and hooks in a real project grows. The first-party [`github/spec-kit-copilot`](https://github.com/github/spec-kit-copilot) plugin mirrored it the same month with an artifact-introspection skill. [\[github.com\]](https://github.com/github/spec-kit/releases)

### Catalog Ergonomics and the CLI Reorganization

Beyond the primitives, September made the catalog and command surface more practical. Both **extensions** (#4726) and **workflows** (#4788) can now **select an exact catalog release** rather than always taking the latest, `catalog add` became **idempotent across every catalog family** (#4543) so re-runs are safe, and the project shipped **first-party bugfix and assess bundles** carrying their own workflows (#4504) alongside a **`specify preset update`** convenience wrapper (#4599). Late in the month a large **CLI reorganization** moved each command family into its own structured domain — extension (#4641), preset (#4657), integration (#4662), bundle (#4663), artifact (#4671), workflow (#4673), and authentication (#4678), down to the root command adapters (#4687) and a preset-domain module split (#4747). The work is structural rather than behavioral, clearing room for the still-growing command set. [\[github.com\]](https://github.com/github/spec-kit/releases)

### The Security-and-Robustness Campaign Continues

The hardening wave carried into September as standing discipline rather than a project. **URL and supply-chain tightening** led the month: catalog downloads now **require tag-pinned URLs** (#4194), closing a bypass where a `latest` reference could resolve to unintended content; the GitHub HTTP layer **validates release-asset metadata URLs** (#4438); and bundle installs **verify the pins of independently installed components** (#4789), closing a drift path between a component and its recorded pin. **Race elimination** removed time-of-check/time-of-use windows in `catalog_fetch()` (#3910), and **community archive validation was restored** so submitted checksums are compared before trust (#4689). The URL-port validation from August continued across preset catalogs, credential matching, and GitHub HTTP handling (#4341, #4362, #4372), release-tag inputs were hardened (#4386), and unreadable provenance now **fails closed** (#4092).

Running alongside was a continued **"fail-loudly" validation sweep** through the workflow and catalog engines. Workflow validation grew stricter — malformed step manifests, falsy non-mapping catalog configuration, non-string catalog tags, and unsupported catalog payload versions are now rejected with clear errors (#4321, #4320, #4318, #4090) — and the generated event dispatcher caps stdin the same way the CLI command does (#4337). A CI guard now **requires version bumps on bundled extension changes** (#4395), and the community submission workflows were hardened again (#4510). The hardening is prevention, arriving as the primitives and the catalog keep opening new surface. [\[github.com\]](https://github.com/github/spec-kit/releases)

### Agent Integrations

The agent portfolio kept growing. The built-in integrations catalog (`integrations/catalog.json`) grew from **38 to 42**, adding four agents across the month — **Docker Agent** (#4302), **DeepSeek Harness** (#4336), **Muse Code** (#4413), and **MiniMax Code** (#4645). Authentication gained a **Bitbucket provider** (#4629). Alongside the new entries, integration *dispatch* work refined existing agents: **Antigravity** CLI compatibility and execution flags (#4612), **Forge** dispatch narrowed to a prompt flag only (#4668), **Vibe** stripped of invalid `--model`/`--output-format` flags (#4784), **Bob** commands dispatched via `bob run` (#4492), and the skills-only **Alquimia** agent taught to render `/speckit-<name>` invocations (#4137). On Windows, `specify init` now detects `copilot.exe` instead of assuming `copilot.cmd` (#4758), and the **generic integration** learned to register extension commands and skills and render `SKILL.md` (#4785, #4562). The pattern from prior months holds — the surviving integrations keep getting more native to each agent, not merely more numerous. [\[github.com\]](https://github.com/github/spec-kit/releases)

### The Extension, Preset & Bundle Ecosystem

The community extension catalog grew from 162 to **176 entries** during September — fourteen net additions. Community presets grew from 34 to **40**, community workflows held at **2**, and community **bundles reached 3**.

The month's most telling signal was the arrival of full **multi-artifact suites** in the catalog. A **product-definition lane** emerged from the ProductShape project: **ProductShape PRODUCT workflows** (#4485) and **Product Definition as Code (PDaC)** (#4514) ground specs in a cited product model. And the **Agentstandards** family graduated to a full multi-artifact suite — an **Architecture Council** extension (#4730), a **Task Gate** preset (#4749), and the bundle (#4751) that packages them — the first new bundle since SpecAssay.

Notable new September additions by category:

- **Verification, review & testing**: Vurnix Honest Gate (deterministic compile/import/test-count gating), Evaluator Contract, ThreatSpec (STRIDE + AI/ML threat modeling), Applied Epistemic Engineering, Test Validation (Playwright E2E), Axi (browser review surface)
- **Methodology & lifecycle**: OpenUP Governed Lifecycle (+ OpenUP Governance preset), ProductShape, Product Definition as Code, Spec Kit Design System
- **Requirements, intake & payments**: GitHub Issue Triage, Agentstandards Architecture Council, AgentPay Pre-Pay Audit (402-terms audit)
- **Governance presets**: Secure Development Assurance, NIEM Information Exchanges, Database Standards, Project Statistics Governance, Agentstandards Task Gate (plus the OpenUP Governance preset noted above)

The catalog also showed heavy maintenance across the month: **SpecAssay** (extension, preset, and bundle to v0.5.2), **DocGuard**, **Azure Cosmos DB** (to v0.2.0), **adrkit**, **MAQA**, **Ralph Loop**, **Figma Starter**, **BrownKit**, and the **Intake** governance-preset family all iterated. [\[github.com\]](https://github.github.io/spec-kit/community/extensions.html)

### Documentation & Docs Site

September's documentation leaned toward simplification and localization. The **README was simplified around the three core processes** (#4591), a **Japanese (日本語) README** landed (#4560), and a **star-history graph** was added to the README (#4672). Operational guidance expanded: a refreshed **release-process guide** (#4502), **AI-disclosure requirements** tightened to include agent, model, and settings (#4512), a **Contract-Driven Development** explainer (#4616), an **agentic-SDLC explainer** (#4774), and documentation of how the project **dogfoods Spec Kit on itself** (#4381). The **extension-catalog trust model** was clarified again — correcting a workflow-publishing security-review claim and adding catalog vetting notes (#4736) — reinforcing that the community catalog is discovery-only, and the **stale policy** was shortened to 60 days stale / 30 to close (#4503). [\[github.com\]](https://github.com/github/spec-kit/releases)

## Community & Content

### Press and Industry Coverage

September brought substantial coverage, and — unlike July and August — included a dedicated first-party Microsoft (non-maintainer) post.

**Microsoft DevBlogs / Azure Cosmos DB** (September 21) published the month's marquee piece — *"Spec-Driven Development comes to Azure Cosmos DB: The First Database Extension for GitHub Spec Kit,"* by Theo van Kraay (Principal Program Manager, Cosmos DB engineering). It announces the public-preview Cosmos DB extension — the first *database* extension in Spec Kit's ecosystem — which adds `before_implement`/`after_implement` hooks for partitioning, RU, and indexing guidance. Notably, its efficacy section is unusually candid: a measured ~10-percentage-point lift in best-practice conformance, but roughly on par with Spec Kit alone end-to-end and still needing human review. [\[devblogs.microsoft.com\]](https://devblogs.microsoft.com/cosmosdb/spec-driven-development-comes-to-azure-cosmos-db-the-first-database-extension-for-github-spec-kit/)

**Jesse Liberty** (Microsoft MVP) posted twice — a September 1 explainer walking the Specify CLI and the constitution/spec/plan/tasks chain, and a September 17 field report describing being *"totally blown away"* using Spec Kit with Copilot to add a Cosmos-backed memory feature. [\[jesseliberty.com\]](https://jesseliberty.com/2026/09/17/spec-driven-development/) **Tproger** (Russian, September 11) ran an in-depth news analysis of the 1.0.x line — the six-command workflow, extensions/presets/bundles, and the "no stability promise" stance — weighing when the full chain is overkill. [\[tproger.ru\]](https://tproger.ru/news/spec-kit-1-0-i-eshhyo-desyat-ii-repozitoriev-sobravwih-zvyozdy-za-n)

### Developer Articles and Field Reports

September's articles skewed toward token-cost accounting, honest field reports, and a strong multilingual current across Japanese, Korean, Chinese, Portuguese, Italian, and Thai.

Notable articles:

- **Chew Loong Nian** (Medium, September 13) — *"GitHub Spec Kit Ships an 18,799-Token Workflow. One Preset Collapses It to 863,"* a fair accounting of what Spec Kit's long slash-command templates buy and cost, measured against the bundled `lean` preset. [\[medium.com\]](https://medium.com/@chewloongnian/github-spec-kit-ships-an-18-799-token-workflow-one-preset-collapses-it-to-863-b38211e85f44)
- **Alfredo Perez** (DEV Community, September 11) — *"I Wrote 238 Specs and Never Read One Again,"* which credits Spec Kit for forcing decisions onto paper, then critiques how completed specs accumulate and "lie," motivating his spec-kit-based "living specs" approach — followed September 28 by a tutorial for his **SpecKit Companion** extension. [\[dev.to\]](https://dev.to/alfredoperez/i-wrote-238-specs-and-never-read-one-again-5705)
- **Serge Aleynikov** (Medium, September 18) — *"Beyond Vibe Coding: Spec-Driven AI Frameworks for Tech Debt,"* field-testing five SDD frameworks on messy codebases, with a GitHub Spec Kit section calling it the cleanest SDD+TDD combination though heavier for solo work. [\[medium.com\]](https://medium.com/@saleyn/beyond-vibe-coding-spec-driven-ai-frameworks-for-tech-debt-cab9cc07ae65)
- **Robert Wimmer** (tauceti.blog, September 15) — a 7,500-word hands-on building a greenfield Go app with Spec Kit on Copilot, weighing the full specify→converge workflow against its token cost and the bugs the agents shipped. [\[tauceti.blog\]](https://www.tauceti.blog/posts/spec-driven-development-with-spec-kit/)
- **ta_kawano** (note.com, consolidated September 13–21, Japanese) — the September continuation of the "要求AI" series, running Spec Kit against a real HR/attendance use case, comparing it with Kiro and mapping its behavior to a requirements-engineering paper's risks (spec overfitting, automation bias, spec debt). [\[note.com\]](https://note.com/takawano/n/nc45c05d4c5d8)
- **Graziano** (Gomoot, September 28, Italian) — a hands-on walkthrough of the full constitution→converge flow plus the `bug`/`assess` extensions and brownfield `--here` init, recommending it for multi-day/multi-agent work while weighing the time and token costs. [\[gomoot.com\]](https://gomoot.com/spec-kit-come-far-lavorare-gli-agenti-ai-su-una-specifica-invece-che-su-un-prompt-improvvisato/)

Additional coverage appeared on DEV Community (Ayush Bisht, Rost Glukhov's gstack, Dmitry Amelchenko, Manjush, Abhishek Banerjee), Medium (Prince Kumar Sharma, Kristopher Dunham, Dean Lin), Qiita/Zenn (Japanese), Naver/velog/GPTers (Korean), CSDN (Chinese), and Portuguese and Thai outlets — including several head-to-head tool comparisons and recurring token-cost and documentation-proliferation critiques. [\[dev.to\]](https://dev.to/dmitryame/stop-asking-which-agentic-coding-methodology-to-use-1bij)

### Community Growth by the Numbers

| Metric | Start of September | End of September | Change |
| --- | --- | --- | --- |
| GitHub stars | ~132,000 | ~139,700 | +~7,700 (+6%) |
| Forks | ~11,900 | ~12,500 | +~600 |
| Contributors | ~270 | ~315 | +~45 |
| Releases (total) | 215 | 226 | +11 (v1.0.3–v1.0.13) |
| Community extensions | 162 | 176 | +14 |
| Community presets | 34 | 40 | +6 |
| Community workflows | 2 | 2 | steady |
| Community bundles | 2 | 3 | +1 |
| Agent integrations (catalog) | 38 | 42 | +4 |
| Discussions (total) | ~482 | ~509 | +~27 |

## SDD Ecosystem & Industry Trends

### The First Database Extension

September produced an ecosystem first: **Microsoft shipped the first *database* extension** for Spec Kit — Azure Cosmos DB, in public preview (covered above). GitHub and Microsoft are the same company, so this is first-party, not outside adoption — but it is notable on its own terms: a Microsoft product team, distinct from the Spec Kit maintainers, shipped its database best-practice guidance as a Spec Kit extension rather than a standalone tool, opening a new extension category. The genuinely third-party signal sits elsewhere — in the community catalog, which added fourteen independent extensions over the month. [\[devblogs.microsoft.com\]](https://devblogs.microsoft.com/cosmosdb/spec-driven-development-comes-to-azure-cosmos-db-the-first-database-extension-for-github-spec-kit/)

### Competitive Landscape

The "which SDD tool?" genre stayed dominant, and September's most substantive pieces continued August's shift from feature bake-offs toward platform and governance framing. Field guides (Aleynikov's five-framework test, Dmitry Amelchenko's methodology stack) position Spec Kit as the thorough, governance-oriented option — model-agnostic, open-source, with the broadest artifact catalog — while naming its recurring trade-off. This month that trade-off sharpened toward **token cost**, which several field reports measured directly — the recurring price of Spec Kit's thoroughness. [\[medium.com\]](https://medium.com/@chewloongnian/github-spec-kit-ships-an-18-799-token-workflow-one-preset-collapses-it-to-863-b38211e85f44)

## Roadmap

A sampling of substantive open work and proposals — in-progress pull requests, filed feature issues, and active discussions (all public, none a commitment):

- **Catalog versioning** — [Support multiple versions per ID across catalog types](https://github.com/github/spec-kit/issues/4719), a maintainer-authored issue delivered as per-family slices; the extension and workflow slices have already landed, with preset, step, bundle, and integration slices still open.
- **Finer preset composition** — an open pull request to [support regex resource selectors](https://github.com/github/spec-kit/pull/4776) would let a preset target commands, templates, and scripts by pattern rather than exact name (closing issue #4659).
- **Workflow composition & custom steps** — an open pull request adds [local `--dev` installation of custom step types](https://github.com/github/spec-kit/pull/4769), while discussions explore [running an installed workflow as a step](https://github.com/github/spec-kit/discussions/4647) and [generic selectors for workflow overlays](https://github.com/github/spec-kit/discussions/4578).
- **Run introspection for integrations** — [supported run-scoped access to a workflow run's definition](https://github.com/github/spec-kit/issues/4792) proposes a stable interface so external tools — a GitHub Action rendering gate progress, for one — need not read internal run-state files.
- **Agent-agnostic project state** — [keeping agent-specific state out of `.specify/`](https://github.com/github/spec-kit/discussions/4740) weighs how a team whose contributors use different agents can share a repo without committing one person's agent choice.
