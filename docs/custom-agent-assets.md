# Building Custom Agent Asset Bundles

This guide walks through every step required to create, package, and distribute a new agent bundle that works seamlessly with Spec Kit’s `.specs/.specify` project layout. Follow these instructions whenever you need to onboard a new AI assistant or fork existing prompts for internal use.

## Prerequisites

- Working checkout of the Spec Kit repository (or a fork).
- Python environment capable of running `uv run specify` (Python 3.11+).
- Bash or PowerShell available locally (the packaging script is POSIX shell).
- `zip` CLI installed (required for archive generation).
- Familiarity with Markdown and, if needed, TOML formatting.

## 1. Author or Customize Command Prompts

1. Navigate to `templates/commands/`.
2. Duplicate an existing command file (e.g., `plan.md`) or create a new one.
3. Update the narrative for your agent. You can:
   - Adjust instructions to suit different slash command UX.
   - Add agent-specific warnings or prerequisites.
4. Keep placeholder tokens intact:
   - `{SCRIPT}` for the helper script path that will be injected per shell variant.
   - `$ARGUMENTS` (Markdown) or `{{args}}` (TOML) for the agent’s input string.
   - Path references should use the legacy structure (`scripts/...`, `/memory/...`); the packaging step rewrites them to `.specs/.specify/...` for you.

> **Tip:** Use `templates/commands/*` as the canonical source of truth. Do not edit the generated prompts inside `.genreleases/` or scaffolded projects; those will be overwritten next time you run the packaging script.

## 2. Register the Agent in the Packaging Script

Edit `.github/workflows/scripts/create-release-packages.sh`:

1. Add your agent key to the `ALL_AGENTS` array (e.g., `myagent`).
2. Extend the `case` statement in `build_variant()` to define the output directory. For example:

   ```bash
   myagent)
     mkdir -p "$base_dir/.myagent/prompts"
     generate_commands myagent md "\$ARGUMENTS" "$base_dir/.myagent/prompts" "$script" ;;
   ```

3. If your agent requires supplemental files (e.g., `.myagent/config.json`), copy them in this block.
4. Leave the rest of the script untouched so that common assets (
   `memory/`, `docs/`, `scripts/`, `templates/`) are copied into `.specs/.specify/` automatically.

The helper functions will:

- Copy shared templates and scripts into the new hierarchy.
- Rewrite prompt paths using `rewrite_paths()` so references point at `.specs/.specify/...`.
- Format prompts to `.md`, `.prompt.md`, or `.toml` depending on your `generate_commands` configuration.

## 3. Generate the Package Locally

Use environment variables to target only your agent while you iterate:

```bash
AGENTS=myagent SCRIPTS=sh bash .github/workflows/scripts/create-release-packages.sh v0.0.1-myagent
```

This produces two outputs:

- `.genreleases/sdd-myagent-package-sh/` – folder containing the staged assets.
- `.genreleases/spec-kit-template-myagent-sh-v0.0.1-myagent.zip` – archive ready for distribution.

Inspect the directory before shipping:

```bash
find .genreleases/sdd-myagent-package-sh -maxdepth 2 -type d
unzip -l .genreleases/spec-kit-template-myagent-sh-v0.0.1-myagent.zip | head
```

Ensure you see:

- `.specs/.specify/templates/…`
- `.specs/.specify/scripts/<shell>/…`
- `.myagent/prompts/…` (or whatever directory you configured)

## 4. Smoke-Test with the CLI

Run `specify init` against your freshly built archive:

```bash
uv run specify init tmp/myagent-demo \
  --ai myagent \
  --script sh \
  --template-path .genreleases/spec-kit-template-myagent-sh-v0.0.1-myagent.zip \
  --no-git
```

Verify that:

- Non-agent assets land in `.specs/.specify/`.
- Every generated prompt references `.specs/.specify/...` paths.
- Shell scripts in `.specs/.specify/scripts/bash/` are executable.

If something looks off, tweak the command templates or packaging script and rerun the steps above.

## 5. (Optional) Teach the CLI About Your Agent

To expose the agent in `specify --help` and enable `--ai myagent`:

1. Edit `src/specify_cli/__init__.py`:
   - Add the display name to `AI_CHOICES`.
   - Update `agent_folder_map` if you need custom security notices.
2. If the agent needs extra behavior (e.g., custom prompts for warnings), extend the CLI logic where we set up agent-specific cases.

This step is optional if you only plan to pass `--template-path` manually, but it keeps UX consistent.

## 6. Distribute the Bundle

You have multiple deployment options:

- **Local testing**: share the zip with teammates; they call `specify init --template-path /path/to/archive.zip`.
- **GitHub release**: upload the archive to a GitHub release (your fork or a private repo) and run the CLI with `--template-repo owner/repo` (matching the release naming convention).
- **CI pipeline**: run `.github/workflows/scripts/create-release-packages.sh` in your pipeline, publish the artifacts to your preferred storage, and update automation to download them before running `specify init`.

Regardless of the delivery channel, the CLI will still relocate any legacy `.specify/` assets into `.specs/.specify/` when the project is initialized.

## 7. Keep Docs & Governance Updated

If your new agent introduces different workflows or requires special setup, update:

- `docs/agent-assets.md` – high-level overview of available bundles.
- The README or installation guide if users need additional dependencies.
- `AGENTS.md` (or your own fork’s equivalent) so maintainers know the integration steps you followed.

## Troubleshooting Checklist

| Problem | Likely Cause | Fix |
|---------|--------------|-----|
| Generated prompts still refer to `scripts/` or `/memory/` | `rewrite_paths()` did not match your format | Ensure your templates use the legacy paths exactly (`scripts/...`, `memory/...`), or extend `rewrite_paths()` if your prompts need additional substitutions |
| CLI can’t find your agent | Agent missing from `AI_CHOICES` in the CLI or the `--ai` flag wasn’t supplied | Add the agent to the CLI or call `specify init` with `--template-path` instead |
| Archive missing `.specs/.specify/` directories | Packaging script changes prevented the shared copy step | Double-check you didn’t override the base copy logic in `build_variant()` |
| Archive command errors about `zip` | `zip` utility not installed | `sudo apt-get install -y zip` (WSL/Ubuntu) |

## Next Steps

- Automate packaging in CI so every release publishes your agent’s archive.
- Create tests that run `specify init` with your bundle and validate the resulting filesystem tree.
- Share the archive with your agent users; include the `--template-path` instructions in onboarding docs.

With these steps you can iterate on prompts safely, keep assets aligned with the `.specs/.specify` hierarchy, and deliver a polished experience for any custom agent.
