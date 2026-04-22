# Community Presets

> [!NOTE]
> Community presets are independently created and maintained by their respective authors. GitHub and the Spec Kit maintainers may review pull requests that add entries to the community catalog for formatting, catalog structure, or policy compliance, but they do **not review, audit, endorse, or support the preset code itself**. Review preset source code before installation and use at your own discretion.

The following community-contributed presets customize how Spec Kit behaves — overriding templates, commands, and terminology without changing any tooling. Presets are available in [`catalog.community.json`](https://github.com/github/spec-kit/blob/main/presets/catalog.community.json):

| Preset | Purpose | Provides | Requires | URL |
|--------|---------|----------|----------|-----|
| AIDE In-Place Migration | Adapts the AIDE extension workflow for in-place technology migrations (X → Y pattern) — adds migration objectives, verification gates, knowledge documents, and behavioral equivalence criteria | 2 templates, 8 commands | AIDE extension | [spec-kit-presets](https://github.com/mnriem/spec-kit-presets) |
| Canon Core | Adapts original Spec Kit workflow to work together with Canon extension | 2 templates, 8 commands | — | [spec-kit-canon](https://github.com/maximiliamus/spec-kit-canon) |
| Claude AskUserQuestion | Upgrades `/speckit.clarify` and `/speckit.checklist` on Claude Code from Markdown-table prompts to the native AskUserQuestion picker, with a recommended option and reasoning on every question | 2 commands | — | [spec-kit-preset-claude-ask-questions](https://github.com/0xrafasec/spec-kit-preset-claude-ask-questions) |
| Explicit Task Dependencies | Adds explicit `(depends on T###)` dependency declarations and an Execution Wave DAG to tasks.md for parallel scheduling | 1 template, 1 command | — | [spec-kit-preset-explicit-task-dependencies](https://github.com/Quratulain-bilal/spec-kit-preset-explicit-task-dependencies) |
| Fiction Book Writing | It adapts the Spec-Driven Development workflow for storytelling to create books or audiobooks (with annotations) in 12 languages: features become story elements, specs become story briefs, plans become story structures, and tasks become scene-by-scene writing tasks. Supports single and multi-POV, all major plot structure frameworks, and two style modes: an author voice sample or humanized AI prose. Supports interactive elements like brainstorming, interview, roleplay and extras like statistics, cover builder and bio command. Export with templates for KDP, D2D etc. | 22 templates, 27 commands | — | [spec-kit-preset-fiction-book-writing](https://github.com/adaumann/speckit-preset-fiction-book-writing) |
| Multi-Repo Branching | Coordinates feature branch creation across multiple git repositories (independent repos and submodules) during plan and tasks phases | 2 commands | — | [spec-kit-preset-multi-repo-branching](https://github.com/sakitA/spec-kit-preset-multi-repo-branching) |
| Pirate Speak (Full) | Transforms all Spec Kit output into pirate speak — specs become "Voyage Manifests", plans become "Battle Plans", tasks become "Crew Assignments" | 6 templates, 9 commands | — | [spec-kit-presets](https://github.com/mnriem/spec-kit-presets) |
| Table of Contents Navigation | Adds a navigable Table of Contents to generated spec.md, plan.md, and tasks.md documents | 3 templates, 3 commands | — | [spec-kit-preset-toc-navigation](https://github.com/Quratulain-bilal/spec-kit-preset-toc-navigation) |
| VS Code Ask Questions | Enhances the clarify command to use `vscode/askQuestions` for batched interactive questioning. | 1 command | — | [spec-kit-presets](https://github.com/fdcastel/spec-kit-presets) |

To build and publish your own preset, see the [Presets Publishing Guide](https://github.com/github/spec-kit/blob/main/presets/PUBLISHING.md).
