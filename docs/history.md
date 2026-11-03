# History

Spec Kit began as a toolkit for making specifications the starting point of
AI-assisted development. From its
[first full check-in](https://github.com/github/spec-kit/commit/28fdfaa86973d4402eecd89ba6c87d31e1edae03),
it described three ways to apply Spec-Driven Development:

- **0-to-1 Development ("Greenfield")** generates a new system from
  requirements.
- **Creative Exploration** compares parallel implementations, technology
  choices, and experience designs.
- **Iterative Enhancement ("Brownfield")** adds features to and modernizes
  existing systems.

All three moved from durable planning artifacts into implementation:

**Specify → Plan → Tasks → Implement**

Those development paths and that core sequence remain, but the project has
grown into an extensible harness for coding agents, software delivery
processes, and other structured work.

## Project stewardship

Spec Kit's history includes two distinct stewardship periods. Recording them
here preserves the contemporary account of the project's leadership without
reducing the work to any one person.

### Founding stewardship: August 2025–January 2026

[Den Delimarsky](https://github.com/localden) and
[John Lam](https://github.com/jflam) conceived Spec Kit and gave the project its
first shape. Den authored the
[initial commit](https://github.com/github/spec-kit/commit/fa2736371e077f55c4fe145fea186bab2561386d) on
August 21, 2025 and led the repository through its first months.

That founding period established the shape users still recognize: the Specify
CLI, coding-agent-specific scaffolding, project constitutions, and the
specification → plan → tasks → implementation process. It also framed SDD as
useful for greenfield development, parallel exploration, and brownfield
enhancement rather than tying the method to a single agent or development
scenario.

### Community stewardship: January 2026–present

[Manfred Riem](https://github.com/mnriem) took over as lead maintainer on
January 22, 2026. The transition became publicly visible when the repository's
global [`CODEOWNERS` entry](https://github.com/github/spec-kit/commit/3040d33c31d8a26d50f91aec5d62d1cecac3298c)
changed to `@mnriem` on February 23.

During this stewardship, the maintainer team's focus moved from building a
composable model to using it to ship complete first-party processes. That shift
was not sequential for the community: the modular extension system began as a
community contribution, and contributors adopted and extended each primitive
as it arrived.

These dates and roles are also documented in the lead maintainer's
[six-month retrospective](https://www.manorrock.com/blog/2026/07/22/six_months_leading_spec_kit.html)
and
[first-anniversary account](https://www.manorrock.com/blog/2026/08/21/spec_kit_turns_one.html),
and are consistent with the repository's commit and ownership history.

## Milestones

### August 2025: The foundation

The repository history begins on August 21, 2025. The first releases established
the Specify CLI, reusable templates, and the core Spec-Driven Development
paths. Support for multiple coding agents through centrally configured,
agent-specific scaffolding was part of the project from the start, keeping the
process independent of any one model or tool.

### February–April 2026: Building the primitives

The modular extension system arrived in February as a community contribution
from Michal Bachorik, allowing capabilities to be added without expanding the
core process. March brought pluggable presets, which made templates and
commands replaceable or composable while preserving the same CLI experience.

The founding-era agent scaffolding was rewritten as a registry-backed
integration architecture. Core assets were also embedded in the Python package,
enabling reliable offline and air-gapped initialization.

The workflow engine introduced catalog-distributed automation and built-in
workflow step types in April. Workflows could coordinate reusable steps rather
than requiring users to invoke every command manually. An integration catalog
followed, making coding-agent support discoverable and independently
distributable.

The composable model came to be described through five primitives:

- **Integrations** connect Spec Kit to coding agents.
- **Extensions** add capabilities, commands, templates, scripts, and hooks.
- **Presets** customize or replace behavior.
- **Workflows** automate multi-step processes.
- **Workflow steps** provide reusable units of workflow behavior.

The emphasis during these first months was on creating reusable machinery:
making the process configurable, distributable, and automatable before adding
more first-party processes. Community contributors did not wait for the full
model to be complete; they quickly used the new extension and preset surfaces
to publish their own capabilities and process variations.

### June–July 2026: Composing and applying the primitives

For the core team, June marked the turn from mainly building primitives to using
them. A workflow step catalog made custom step types community-installable,
extending a primitive that had shipped with the workflow engine in April.
Bundles then made it possible to package extensions, presets, workflows, and
steps as a coherent setup for a role or team, optionally targeting a specific
integration.

Catalogs became the bridge between the primitives and the community. Community
authors built extensions, presets, integrations, workflows, step types, and
bundles; the maintainer team checked submission metadata and listed accepted
entries in community catalogs so users could discover and install them. A
catalog listing made a component visible, but did not mean its code had been
audited or endorsed.

At the same time, core maintainers began using the model to add two first-party
processes alongside feature delivery:

- On June 5, version 0.9.5 introduced the bundled, opt-in
  [`bug` extension](https://github.com/github/spec-kit/commit/60302fefec541a68fcac6f0428a95ba35f2acadf).
  Its assess → fix → test process keeps bug diagnosis, remediation, and
  verification separate and documented.
- On July 17, version 0.13.0 introduced the bundled, opt-in
  [`assess` extension](https://github.com/github/spec-kit/commit/208d38695fc88d8eaec7855c96e5098a852927cf).
  Its intake → research → define → shape → decide process evaluates an idea
  before it enters SDD.

June also closed the core delivery loop with `/speckit.converge`. Rather than
treating implementation as the endpoint, it assesses the code against the
specification, plan, and tasks, then appends traceable tasks for remaining gaps.
Those tasks return to `/speckit.implement`, creating a convergence loop without
rewriting the specification or plan. The
[June newsletter](https://github.com/github/spec-kit/blob/main/newsletters/2026-June.md)
records this shift from generating an implementation to checking whether it
satisfies the recorded intent.

July added [agent-native runtime events](integrations/cli.md#runtime-events),
allowing extensions to react to coding-agent lifecycle events such as session
start or tool use. Unlike command hooks, these events execute scripts directly
rather than asking the agent to follow additional instructions. Integrations
could now connect Spec Kit behavior to the agent's runtime, not just deliver
commands or skills.

Distribution broadened too: the release pipeline added PyPI publishing, and
Python joined Bash and PowerShell as a supported project script type. These
changes made installation and cross-platform use simpler while preserving
support for offline and enterprise environments.

### August 2026: First anniversary

Spec Kit turned one and released version 1.0.0 on August 21, 2026. By then, its
five primitives — integrations, extensions, presets, workflows, and workflow
steps — already formed a coherent model. Bundles composed extensions, presets,
workflows, and steps around a selected integration. A README refresh made the
existing SDD, bug-fixing, and idea-assessment processes easier to discover
through separate quickstarts.

Version 1.0.0 did not create or freeze that model; it gave the project's
evolving state a round number. The documentation then reported 38 coding-agent
integrations, 157 community extensions, 33 presets, and 270+ contributors. Spec
Kit continues to favor adaptability: processes, integrations, and conventions
can evolve while agents help projects apply those changes.

The [1.0.0 release](https://github.com/github/spec-kit/releases/tag/v1.0.0)
marked a year of work rather than a promise that the project was finished or its
shape frozen. In the lead maintainer's personal anniversary post,
[*Spec Kit Turns One — and Ships 1.0.0*](https://www.manorrock.com/blog/2026/08/21/spec_kit_turns_one.html),
1.0.0 is **now just a number**: as agents make adapting to change less expensive,
the value moves from stability to adaptability.

The anniversary also recognized everyone who used Spec Kit, challenged its
assumptions, reported problems, contributed code or documentation, created
extensions or presets, shared ideas, or helped someone get started. The milestone
belongs to the community that carried the project through its first year and
continues to shape it.

August also made the integration and process model more concrete in daily use.
Copilot initialization switched to skills by default, replacing the legacy
markdown-command layout as its default delivery route. The project began
applying its own idea-assessment process to incoming feature requests through
the `feature-assess` agentic workflow, which initializes Spec Kit and runs the
`assess` extension. The
[August newsletter](https://github.com/github/spec-kit/blob/main/newsletters/2026-August.md)
records both the agent-native delivery change and this use of Spec Kit to help
maintain Spec Kit itself.

### September 2026: Inspectable composition

September made the composable model finer-grained and easier to inspect.
Presets gained explicit extension dependencies, workflows gained named slots
for reusable insertion points, and individual steps could carry their own
integration configuration. The new
[`specify artifact` command group](reference/artifacts.md) exposed commands,
templates, scripts, and hooks with their composition stacks and contributing
layers as JSON. Tooling and agents could inspect what a project's installed
layers actually produced, rather than infer it from configuration alone.

The ecosystem also supplied a concrete example of the extension model reaching
beyond general development guidance. In September, Microsoft's Azure Cosmos DB
team [announced the first database extension for Spec Kit](https://devblogs.microsoft.com/cosmosdb/spec-driven-development-comes-to-azure-cosmos-db-the-first-database-extension-for-github-spec-kit/),
in public preview, bringing database-specific guidance into the implementation
process. This was work from a Microsoft product team distinct from the Spec Kit
maintainers, not independent third-party adoption. Alongside it, community
authors continued expanding the catalog with their own components. The
[September newsletter](https://github.com/github/spec-kit/blob/main/newsletters/2026-September.md)
records both the composition changes and that ecosystem growth.

### October–November 2026: Programmatic access and deeper composition

October introduced an experimental local
[Model Context Protocol (MCP) server](reference/mcp.md), initially exposing
version information and then artifact inspection and installed-workflow
listing. These read-only tools let MCP clients inspect Spec Kit directly;
they did not expose installation, mutation, or workflow execution. The CLI and
first-class MCP tools dispatch to shared operations, extending access without
creating a separate implementation of the same behavior.

Composition also extended across more boundaries. Coding-agent adapters became
[installable from catalogs](integrations/cli.md#catalog-installed-external-adapters),
allowing agent-specific support to be distributed outside the core package,
subject to the user's explicit trust decision. Workflows gained
[calls to other workflows](reference/workflows.md#workflow-composition) within
a unified execution tree, and bundles gained
[references to other bundles](reference/bundles.md#bundle-references).
By early November, run-scoped workflow definitions were also inspectable through
`specify workflow definition`. Together, these changes made the existing
primitives more reusable and their effective configuration more visible,
without introducing a new development process.

## Enduring themes

Several themes connect the project's stewardship periods and technical
evolution:

- **Intent comes before implementation.** Specifications capture what should be
  built before technical decisions dominate the work.
- **Artifacts should be durable.** Specs, plans, and tasks remain useful beyond
  a single prompt or agent session.
- **The process should be agent-independent.** Teams can change coding agents
  without abandoning their development method.
- **The method should adapt to the work.** The original development paths grew
  into a formally composable model that teams can modify, automate, or replace.
- **The community shapes the kit.** Community contributions have influenced
  both the project's infrastructure and the ecosystem built on it.

## Release history

This page records the project's broad evolution, not every feature or breaking
change. For release-level detail, see the
[changelog](https://github.com/github/spec-kit/blob/main/CHANGELOG.md) and
[GitHub Releases](https://github.com/github/spec-kit/releases).
