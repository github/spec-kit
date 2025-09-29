# Step 1: Setup Environment

**Goal:** bring your workstation to a known-good baseline so Spec Kit and the SDD loop run without friction.

## Inputs

- Git installed and configured with your preferred editor
- Python 3.10+ _or_ the latest [Astral `uv`](https://docs.astral.sh/uv/getting-started/installation/) runtime (used by `uvx`)

## Actions

## Quick start with Specify CLI

1. **Install Specify (persistent option recommended)**
  ```bash
  uv tool install specify-cli --from git+https://github.com/github/spec-kit.git
  ```
  Alternative (one-off):
  ```bash
  uvx --from git+https://github.com/github/spec-kit.git specify init <PROJECT_NAME>
  ```
2. **Run the readiness checks**
  ```bash
  specify --version
  specify check
  ```
3. **Bootstrap your project**
  ```bash
  specify init <PROJECT_NAME>
  ```
4. **Follow the slash-command sequence** inside your coding agent (Copilot, Claude Code, Cursor, Gemini CLI, etc.).

Inspect the generated `.github/` and `.specify/` folders, then delete the sandbox once you understand the layout.

### Slash commands (Spec Kit 2025)

| Command | Purpose |
| --- | --- |
| `/constitution` | Create or update project principles and guardrails. |
| `/specify` | Capture the “what” and “why” of the feature or product. |
| `/clarify` | Resolve ambiguities before planning; must run before `/plan` unless explicitly skipped. |
| `/plan` | Produce the technical approach, stack choices, and quickstart. |
| `/tasks` | Break the plan into actionable units of work. |
| `/analyze` | Check cross-artifact coverage and highlight gaps after `/tasks`. |
| `/implement` | Execute tasks in sequence with automated guardrails. |

## Deliverables

- A fresh repository ready for Spec Kit
- Verified `uvx` runner capable of invoking `specify`

## Quality Gates ✅

- `uvx --from … specify --help` exits with status 0
- `git status` shows a clean working tree in your new project folder

## Common Pitfalls

- Installing `uvx` via npm (deprecated); use the official `uv` installer instead

## References

- GitHub Spec Kit repo: https://github.com/github/spec-kit
- GitHub blog (Spec Kit overview): https://github.blog/ai-and-ml/generative-ai/spec-driven-development-with-ai-get-started-with-a-new-open-source-toolkit/
- Microsoft Dev Blog (Spec Kit intro): https://developer.microsoft.com/blog/spec-driven-development-spec-kit
