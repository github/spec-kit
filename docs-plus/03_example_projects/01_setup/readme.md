# Step 1: Setup Environment

**Goal:** bring your workstation to a known-good baseline so Spec Kit Plus and the SDD loop run without friction.

## Inputs

- Git installed and configured with your preferred editor
- Python 3.10+ _or_ the latest [Astral `uv`](https://docs.astral.sh/uv/getting-started/installation/) runtime (used by `uvx`)
- Setup any coding agent of your choice (Qwen Code, Gemini CLI, Claude Code, Cursor, GitHub Copilot, Roo, etc.)
## Actions

## Quick start with SpecifyPlus CLI

1. **Install SpecifyPlus (persistent option recommended)**
  ```bash
  # From PyPI (recommended)
  pip install specifyplus
  # or with uv tools
  uv tool install specifyplus
  ```

  Alternative (one-off):
  ```bash
  uvx specifyplus --help
  uvx specifyplus init <PROJECT_NAME>
  # or
  uvx sp init <PROJECT_NAME>
  ```

2. **Run the readiness checks**
  ```bash
  specifyplus --help
  # or
  sp --help
  specifyplus check
  # or
  sp check
  ```

3. **Bootstrap your project**
  ```bash
  specifyplus init <PROJECT_NAME>
  # or
  sp init <PROJECT_NAME>
  ```

4. **Follow the slash-command sequence** inside your coding agent (Copilot, Claude Code, Cursor, Gemini CLI, etc.).

Inspect the generated `.github/` and `.specify/` folders, then delete the sandbox once you understand the layout.

### Slash commands (Spec Kit 2025)

| Command | Purpose |
| --- | --- |
| `/sp.constitution` | Create or update project principles and guardrails. |
| `/sp.specify` | Capture the “what” and “why” of the feature or product. |
| `/sp.clarify` | Resolve ambiguities before planning; must run before `/plan` unless explicitly skipped. |
| `/sp.plan` | Produce the technical approach, stack choices, and quickstart. |
| `/sp.adr` | Record Architecture Decision Records. |
| `/sp.tasks` | Break the plan into actionable units of work. |
| `/sp.analyze` | Check cross-artifact coverage and highlight gaps after `/tasks`. |
| `/sp.implement` | Execute tasks in sequence with automated guardrails. |
| `/sp.phr` | Create prompt history record for the prompt. |

## Deliverables

- A fresh repository ready for Spec Kit
- Verified `uvx` runner capable of invoking `specifyplus`

Ready to build muscle memory for spec-driven development? Start Shipping! 🚀
