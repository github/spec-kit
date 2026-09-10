# Contributing to Spec Kit

Hi there! We're thrilled that you'd like to contribute to Spec Kit. Contributions to this project are [released](https://help.github.com/articles/github-terms-of-service/#6-contributions-under-repository-license) to the public under the [project's open source license](LICENSE).

Please note that this project is released with a [Contributor Code of Conduct](CODE_OF_CONDUCT.md). By participating in this project you agree to abide by its terms.

## Prerequisites for running and testing code

These are one time installations required to be able to test your changes locally as part of the pull request (PR) submission process.

1. Install [Python 3.11+](https://www.python.org/downloads/)
1. Install [uv](https://docs.astral.sh/uv/) for package management
1. Install [Git](https://git-scm.com/downloads)
1. Have an [AI coding agent available](README.md#-supported-ai-coding-agent-integrations)

<details>
<summary><b>💡 Hint if you are using <code>VSCode</code> or <code>GitHub Codespaces</code> as your IDE</b></summary>

<br>

Provided you have [Docker](https://docker.com) installed on your machine, you can leverage [Dev Containers](https://containers.dev) through this [VSCode extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers), to easily set up your development environment, with aforementioned tools already installed and configured, thanks to the `.devcontainer/devcontainer.json` file (located at the root of the project).

To do so, simply:

- Checkout the repo
- Open it with VSCode
- Open the [Command Palette](https://code.visualstudio.com/docs/getstarted/userinterface#_command-palette) and select "Dev Containers: Open Folder in Container..."

On [GitHub Codespaces](https://github.com/features/codespaces) it's even simpler, as it leverages the `.devcontainer/devcontainer.json` automatically upon opening the codespace.

</details>

## Submitting a pull request

> [!NOTE]
> If your pull request introduces a large change that materially impacts the work of the CLI or the rest of the repository (e.g., you're introducing new templates, arguments, or otherwise major changes), make sure that it was **discussed and agreed upon** by the project maintainers. Pull requests with large changes that did not have a prior conversation and agreement will be closed.

1. Fork and clone the repository
1. Configure and install the dependencies: `uv sync --extra test`
1. Make sure the CLI works on your machine: `uv run specify --help`
1. Create a new branch: `git checkout -b <type>/<number>-<short-slug>` (see [Branch naming](#branch-naming) below)
1. Make your change, add tests, and make sure everything still works
1. Test the CLI functionality with a sample project if relevant
1. Push to your fork and submit a pull request
1. Wait for your pull request to be reviewed and merged.

Activate the project virtual environment (see [Testing setup](#testing-setup) below), then install the CLI from your working tree (`uv pip install -e .` after `uv sync --extra test`) or otherwise ensure the shell uses the local `specify` binary before running the manual slash-command tests described below.

Here are a few things you can do that will increase the likelihood of your pull request being accepted:

- Follow the project's coding conventions.
- Write tests for new functionality.
- Update documentation (`README.md`, `spec-driven.md`) if your changes affect user-facing features.
- Keep your change as focused as possible. If there are multiple changes you would like to make that are not dependent upon each other, consider submitting them as separate pull requests.
- Write a [good commit message](http://tbaggery.com/2008/04/19/a-note-about-git-commit-messages.html).
- Test your changes with the Spec-Driven Development workflow to ensure compatibility.

Accounts with three open pull requests may continue submitting changes, but additional submissions may be placed behind contributions from other authors in the review queue. Coding agents should disclose this possibility and obtain the filer's confirmation before opening another pull request. Repository-owned `gh-aw` maintenance workflows do not require this confirmation.

### Evidence gate

A contribution is evaluated on the evidence it carries, not on how plausible its reasoning sounds. The same bar applies to everyone — human and AI-assisted contributions are judged identically.

A valid, in-scope change that arrives without evidence is not rejected outright. It may be labeled [`triage-can-wait`](#triage-and-author-labels) and held behind proven work until evidence is added, at which point it can be reprioritized.

What counts as evidence:

- **A reproduction or a linked real-world report** — a failing case, a stack trace, or a link to an issue where the problem actually occurred. "This could theoretically fail" reasoning on its own does not clear the gate.
- **A regression test that fails on `main` and passes with your change** — this proves both that the problem is real and that your change fixes it.
- **Scope discipline** — one concern per pull request. Split unrelated changes into separate PRs (see the [focused-change guidance](#submitting-a-pull-request) above); sprawling batch diffs are hard to review and slow to land.
- **Disclosed AI assistance** — if any AI tooling was involved, disclose it and its extent per [AI contributions in Spec Kit](#ai-contributions-in-spec-kit).

Speculative hardening is welcome, but it sits behind proven, evidence-backed work. If you can attach a reproduction and a failing test, your change moves to the front; if you can't yet, say so, and it will be queued rather than closed.

### Review rubric

Triaged items are weighed across seven dimensions, each scored `0`–`2` (`0` absent, `1` partial, `2` clearly demonstrated), for a maximum of 14. The score guides **prioritization** — it is not a hard pass/fail gate. The one firm rule is the [evidence gate](#evidence-gate) above: theoretical-only changes with no evidence are deprioritized.

| Dimension | What it measures |
|---|---|
| D1 — Real-world evidence | A reproduction or linked report, versus theory alone |
| D2 — Reachability / severity | Whether the issue can actually be hit, and how bad it is |
| D3 — Scope discipline | One focused concern per PR, no unrelated changes |
| D4 — Test evidence | A regression test that fails on `main` and passes with the change |
| D5 — Disclosure / understanding | AI use disclosed, and the author understands the change |
| D6 — Cost vs. benefit | Value delivered against added complexity and maintenance cost |
| D7 — Roadmap alignment | Fit with Spec Kit's goals and direction |

### Triage and author labels

Every triaged item receives one **verdict** label recording where it stands. **Author** labels signal the specific action needed to move an item forward.

Verdict (one per item):

| Label | Meaning |
|---|---|
| `triage-must-have` | Verdict: high-value, important work for Spec Kit — do first |
| `triage-nice-to-have` | Verdict: evidence-backed fix or greenlit feature — land after review |
| `triage-can-wait` | Verdict: valid and in-scope but deprioritized; held behind the evidence gate |
| `triage-out-of-scope` | Verdict: won't land in core — invalid, duplicate, off-mission, or redirected to an extension |

Author actions:

| Label | Meaning |
|---|---|
| `author-needs-proof` | The problem isn't demonstrated yet — supply a reproduction or a test that fails on `main` and passes with the change |
| `author-needs-tests` | Real change but missing a regression test — add one that fails before / passes after |
| `author-needs-rescope` | Sprawling or batched diff — split into one focused, single-concern PR |
| `author-needs-disclosure` | AI assistance not disclosed — disclose AI use per CONTRIBUTING |
| `author-needs-info` | Missing detail needed to assess — supply requested info |
| `author-needs-rebase` | Branch conflicts with `main` — rebase and resolve before it can be merged |
| `author-over-cap` | Over the 3-open-PR cap or repetitive batch submissions — please consolidate |
| `author-awaiting` | Waiting on author response (handed off to the existing stale workflow) |

Some pull requests are closed as `triage-out-of-scope` rather than merged — most commonly
when the same change is already in `main`, when a request is better served as a community
extension, when an existing feature already covers it, or when a catalog change came in as
a direct edit instead of a submission issue. A close always comes with a comment explaining
why and, where relevant, where to go instead.

For further reading on the thinking behind this gate, see [one maintainer's perspective on AI-sourced contributions](https://blog.manorrock.com/blog/2026/09/08/spec_kit_ai_source.html). That piece is a personal viewpoint, not project policy — the policy is what's documented here.

### Community catalog submissions

To add or update a community extension, preset, or bundle in the catalog, **open an
`[Extension]` / `[Preset]` / `[Bundle]` submission issue** — do not edit
`extensions/catalog.community.json` (or the preset/bundle catalogs) directly in a pull
request. The submission issue triggers an automated workflow that validates the release,
verifies the pinned `download_url` and digests, and generates the catalog PR for you.
A hand-edited catalog PR bypasses that validation and will be closed with a pointer back
to the issue flow.

This applies to **new entries, version updates, and repairs alike** — a version bump or a
fix to a broken entry is still an update and needs the same validation. Always pin
`download_url` to a release tag (e.g. `.../releases/download/<tag>/...` or
`.../archive/refs/tags/<tag>.zip`); never use `releases/latest/`.

### Branch naming

We recommend naming branches as `<type>/<number>-<short-slug>`, where `<number>` is the issue or PR number (whichever comes first) and `<type>` is one of:

| Prefix | When to use | Example |
|---|---|---|
| `feat/` | New features | `feat/2342-workflow-cli-alignment` |
| `fix/` | Bug fixes | `fix/2653-paths-only-validation` |
| `docs/` | Documentation changes | `docs/2677-branch-naming-convention` |
| `community/` | Community catalog additions | `community/2492-add-mde-extension` |
| `chore/` | Maintenance, tooling, CI | `chore/2366-editorconfig` |

Including the issue or PR number makes branches traceable — especially useful since the project uses squash merges and `git branch --merged` won't detect merged branches. If you start with a PR (no issue), use the PR number once it's assigned.

## Development workflow

When working on spec-kit:

1. Test changes with the `specify` CLI commands (`/speckit.specify`, `/speckit.plan`, `/speckit.tasks`) in your coding agent of choice
2. Verify templates are working correctly in `templates/` directory
3. Test script functionality in the `scripts/` directory
4. Ensure memory files (`memory/constitution.md`) are updated if major process changes are made

### Recommended validation flow

For the smoothest review experience, validate changes in this order:

1. **Run focused automated checks first** — use the quick verification commands [below](#automated-checks) to catch scaffolding and configuration regressions early.
2. **Run manual workflow tests second** — if your change affects slash commands or the developer workflow, follow the [manual testing](#manual-testing) section to choose the right commands, run them in an agent, and capture results for your PR.

### Automated checks

#### Agent configuration and wiring consistency

```bash
uv run python -m pytest tests/test_agent_config_consistency.py -q
```

Run this when you change agent metadata, context update scripts, or integration wiring.

#### Running the full test suite

Install the test dependencies into the project's own virtual environment and run
`pytest` through that interpreter:

```bash
uv pip install -e ".[test]"
.venv/bin/python -m pytest tests -q   # Windows: .venv\Scripts\python -m pytest tests -q
```

> **Note:** prefer `.venv/bin/python -m pytest` over a bare `uv run pytest`.
> If another Spec Kit checkout has an editable (`-e`) install registered in a
> shared/global environment, `uv run pytest` can resolve `specify_cli` to that
> *other* worktree, turning it into a partial namespace package that fails to
> import newly added subpackages. Running through the project `.venv` resolves
> `specify_cli` to this checkout's `src/`. This matches the gotcha documented in
> `AGENTS.md` (Common Pitfalls).

#### Security checks

```bash
uvx --from pip-audit==2.10.0 pip-audit --disable-pip --require-hashes -r .github/security-audit-requirements.txt --progress-spinner off
```

This command audits the committed hashed requirements snapshot. Pull request,
push, and manual CI runs use the same snapshot so their results stay
deterministic. If dependency metadata changes, refresh and commit the snapshot
before auditing it:

```bash
uv pip compile pyproject.toml --extra test --universal --upgrade --generate-hashes --quiet --no-header --output-file .github/security-audit-requirements.txt
```

The scheduled CI audit resolves the runtime and `test` extra dependency set
across the supported Python and OS matrix to catch newly published advisories.
Upstream package releases drift over time, so even an unrelated PR touching
`pyproject.toml` can fail the `dependency-audit` check until the committed file
is regenerated with the command above and re-committed.

#### Shell scripts

```bash
git ls-files -z -- '*.sh' | xargs -0 shellcheck --severity=error
```

The CI `lint.yml` `shellcheck` job currently reports and blocks only
error-severity findings. Warnings such as SC2155 are intentionally outside this
job until a follow-up cleanup tightens the threshold.

### Manual testing

#### Testing setup

```bash
# Install the project and test dependencies from your local branch
cd <spec-kit-repo>
uv sync --extra test
source .venv/bin/activate  # On Windows (CMD): .venv\Scripts\activate  |  (PowerShell): .venv\Scripts\Activate.ps1
uv pip install -e .
# Ensure the `specify` binary in this environment points at your working tree so the agent runs the branch you're testing.

# Initialize a test project using your local changes
uv run specify init <temp-dir>/speckit-test --integration <agent>
cd <temp-dir>/speckit-test

# Open in your agent
```

#### Manual testing process

Any change that affects a slash command's behavior requires manually testing that command through a coding agent and submitting results with the PR.

1. **Identify affected commands** — use the [prompt below](#determining-which-tests-to-run) to have your agent analyze your changed files and determine which commands need testing.
2. **Set up a test project** — scaffold from your local branch (see [Testing setup](#testing-setup)).
3. **Run each affected command** — invoke it in your agent, verify it completes successfully, and confirm it produces the expected output (files created, scripts executed, artifacts populated).
4. **Run prerequisites first** — commands that depend on earlier commands (e.g., `/speckit.tasks` requires `/speckit.plan` which requires `/speckit.specify`) must be run in order.
5. **Report results** — paste the [reporting template](#reporting-results) into your PR with pass/fail for each command tested.

#### Reporting results

Paste this into your PR:

~~~markdown
## Manual test results

**Agent**: [e.g., GitHub Copilot in VS Code]  |  **OS/Shell**: [e.g., macOS/zsh]

| Command tested | Notes |
|----------------|-------|
| `/speckit.command` | |
~~~

#### Determining which tests to run

Copy this prompt into your agent. Include the agent's response (selected tests plus a brief explanation of the mapping) in your PR.

~~~text
Read CONTRIBUTING.md, then run `git diff --name-only main` to get my changed files.
For each changed file, determine which slash commands it affects by reading
the command templates in templates/commands/ to understand what each command
invokes. Use these mapping rules:

- templates/commands/X.md → the command it defines
- scripts/bash/Y.sh or scripts/powershell/Y.ps1 → every command that invokes that script (grep templates/commands/ for the script name). Also check transitive dependencies: if the changed script is sourced by other scripts (e.g., common.sh is sourced by create-new-feature.sh, check-prerequisites.sh, setup-plan.sh), then every command invoking those downstream scripts is also affected
- templates/Z-template.md → every command that consumes that template during execution
- src/specify_cli/*.py → CLI commands (`specify init`, `specify check`, `specify extension *`, `specify preset *`); test the affected CLI command and, for init/scaffolding changes, at minimum test /speckit.specify
- extensions/X/commands/* → the extension command it defines
- extensions/X/scripts/* → every extension command that invokes that script
- extensions/X/extension.yml or config-template.yml → every command in that extension. Also check if the manifest defines hooks (look for `hooks:` entries like `before_specify`, `after_implement`, etc.) — if so, the core commands those hooks attach to are also affected
- presets/*/* → test preset scaffolding via `specify init` with the preset
- pyproject.toml → packaging/bundling; test `specify init` and verify bundled assets

Include prerequisite tests (e.g., T5 requires T3 requires T1).

Output in this format:

### Test selection reasoning

| Changed file | Affects | Test | Why |
|---|---|---|---|
| (path) | (command) | T# | (reason) |

### Required tests

Number each test sequentially (T1, T2, ...). List prerequisite tests first.

- T1: /speckit.command — (reason)
- T2: /speckit.command — (reason)
~~~

## AI contributions in Spec Kit

> [!IMPORTANT]
>
> If you are using **any kind of AI assistance** to contribute to Spec Kit,
> it must be disclosed in the pull request or issue.

We welcome and encourage the use of AI tools to help improve Spec Kit! Many valuable contributions have been enhanced with AI assistance for code generation, issue detection, and feature definition.

That being said, if you are using any kind of AI assistance (e.g., agents, ChatGPT) while contributing to Spec Kit,
**this must be disclosed in the pull request or issue**, along with the extent to which AI assistance was used (e.g., documentation comments vs. code generation).

If your PR responses or comments are being generated by an AI, disclose that as well.

As an exception, trivial spacing or typo fixes don't need to be disclosed, so long as the changes are limited to small parts of the code or short phrases.

An example disclosure:

> This PR was written primarily by GitHub Copilot.

Or a more detailed disclosure:

> I consulted ChatGPT to understand the codebase but the solution
> was fully authored manually by myself.

Failure to disclose this is first and foremost rude to the human operators on the other end of the pull request, but it also makes it difficult to
determine how much scrutiny to apply to the contribution.

In a perfect world, AI assistance would produce equal or higher quality work than any human. That isn't the world we live in today, and in most cases
where human supervision or expertise is not in the loop, it's generating code that cannot be reasonably maintained or evolved.

### What we're looking for

When submitting AI-assisted contributions, please ensure they include:

- **Clear disclosure of AI use** - You are transparent about AI use and degree to which you're using it for the contribution
- **Human understanding and testing** - You've personally tested the changes and understand what they do
- **Clear rationale** - You can explain why the change is needed and how it fits within Spec Kit's goals
- **Concrete evidence** - Include test cases, scenarios, or examples that demonstrate the improvement
- **Your own analysis** - Share your thoughts on the end-to-end developer experience

### What we'll close

We reserve the right to close contributions that appear to be:

- Untested changes submitted without verification
- Generic suggestions that don't address specific Spec Kit needs
- Bulk submissions that show no human review or understanding

### Guidelines for success

The key is demonstrating that you understand and have validated your proposed changes. If a maintainer can easily tell that a contribution was generated entirely by AI without human input or testing, it likely needs more work before submission.

Contributors who consistently submit low-effort AI-generated changes may be restricted from further contributions at the maintainers' discretion.

Please be respectful to maintainers and disclose AI assistance.

## Resources

- [Spec-Driven Development Methodology](./spec-driven.md)
- [How to Contribute to Open Source](https://opensource.guide/how-to-contribute/)
- [Using Pull Requests](https://help.github.com/articles/about-pull-requests/)
- [GitHub Help](https://help.github.com)
