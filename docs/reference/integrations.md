# Supported AI Coding Agent Integrations

The Specify CLI supports a wide range of AI coding agents. When you run `specify init`, the CLI sets up the appropriate command files, context rules, and directory structures for your chosen AI coding agent — so you can start using Spec-Driven Development immediately, regardless of which tool you prefer.

## Supported AI Coding Agents

| Agent                                                                                | Key              | Notes                                                                                                                                     |
| ------------------------------------------------------------------------------------ | ---------------- | ----------------------------------------------------------------------------------------------------------------------------------------- |
| [Amp](https://ampcode.com/)                                                          | `amp`            |                                                                                                                                           |
| [Antigravity (agy)](https://antigravity.google/)                                     | `agy`            | Skills-based integration; skills are installed automatically                                                                               |
| [Auggie CLI](https://docs.augmentcode.com/cli/overview)                              | `auggie`         |                                                                                                                                           |
| [Claude Code](https://www.anthropic.com/claude-code)                                 | `claude`         | Skills-based integration; installs skills in `.claude/skills`                                                                              |
| [CodeBuddy CLI](https://www.codebuddy.ai/cli)                                        | `codebuddy`      |                                                                                                                                           |
| [Codex CLI](https://github.com/openai/codex)                                         | `codex`          | Skills-based integration; installs skills into `.agents/skills` and invokes them as `$speckit-<command>` |
| [Cursor](https://cursor.sh/)                                                         | `cursor-agent`   |                                                                                                                                           |
| [Devin for Terminal](https://cli.devin.ai/docs)                                      | `devin`          | Skills-based integration; installs skills into `.devin/skills/` and invokes them as `/speckit-<command>` |
| [Forge](https://forgecode.dev/)                                                      | `forge`          |                                                                                                                                           |
| [Gemini CLI](https://github.com/google-gemini/gemini-cli)                            | `gemini`         |                                                                                                                                           |
| [GitHub Copilot](https://code.visualstudio.com/)                                     | `copilot`        |                                                                                                                                           |
| [Goose](https://block.github.io/goose/)                                              | `goose`          | Uses YAML recipe format in `.goose/recipes/`                                                                                              |
| [IBM Bob](https://www.ibm.com/products/bob)                                          | `bob`            | IDE-based agent                                                                                                                           |
| [iFlow CLI](https://docs.iflow.cn/en/cli/quickstart)                                 | `iflow`          |                                                                                                                                           |
| [Junie](https://junie.jetbrains.com/)                                                | `junie`          |                                                                                                                                           |
| [Kilo Code](https://github.com/Kilo-Org/kilocode)                                    | `kilocode`       |                                                                                                                                           |
| [Kimi Code](https://code.kimi.com/)                                                  | `kimi`           | Skills-based integration; supports `--migrate-legacy` for dotted→hyphenated directory migration                                            |
| [Kiro CLI](https://kiro.dev/docs/cli/)                                               | `kiro-cli`       | Kiro CLI does not substitute `$ARGUMENTS` in file-based prompts, so Spec Kit ships a prose fallback at render time (see [Manage prompts](https://kiro.dev/docs/cli/chat/manage-prompts/) and issue [#1926](https://github.com/github/spec-kit/issues/1926)). Alias: `--integration kiro` |
| [Lingma](https://lingma.aliyun.com/)                                                 | `lingma`         | Skills-based integration; skills are installed automatically                                                                               |
| [Mistral Vibe](https://github.com/mistralai/mistral-vibe)                            | `vibe`           |                                                                                                                                           |
| [opencode](https://opencode.ai/)                                                     | `opencode`       |                                                                                                                                           |
| [Pi Coding Agent](https://pi.dev)                                                    | `pi`             | Pi doesn't have MCP support out of the box, so `taskstoissues` won't work as intended. MCP support can be added via [extensions](https://github.com/badlogic/pi-mono/tree/main/packages/coding-agent#extensions) |
| [Qoder CLI](https://qoder.com/cli)                                                   | `qodercli`       |                                                                                                                                           |
| [Qwen Code](https://github.com/QwenLM/qwen-code)                                     | `qwen`           |                                                                                                                                           |
| [Roo Code](https://roocode.com/)                                                     | `roo`            |                                                                                                                                           |
| [RovoDev](https://www.atlassian.com/software/rovo-dev)                                | `rovodev`        | Generates `.rovodev/skills/`, prompt wrappers, and `prompts.yml`; runtime dispatch uses `acli rovodev`                                    |
| [SHAI (OVHcloud)](https://github.com/ovh/shai)                                       | `shai`           |                                                                                                                                           |
| [Tabnine CLI](https://docs.tabnine.com/main/getting-started/tabnine-cli)             | `tabnine`        |                                                                                                                                           |
| [Trae](https://www.trae.ai/)                                                         | `trae`           | Skills-based integration; skills are installed automatically                                                                               |
| [Windsurf](https://windsurf.com/)                                                    | `windsurf`       |                                                                                                                                           |
| Generic                                                                              | `generic`        | Bring your own agent — use `--integration generic --integration-options="--commands-dir <path>"` for AI coding agents not listed above     |

## List Available Integrations

```bash
specify integration list
```

Shows all available integrations, which one is currently installed, and whether each requires a CLI tool or is IDE-based.
When multiple integrations are installed, the list marks the default integration separately from the other installed integrations.
The list also shows whether each built-in integration is declared multi-install safe.

## Install an Integration

```bash
specify integration install <key>
```

| Option                   | Description                                                              |
| ------------------------ | ------------------------------------------------------------------------ |
| `--script sh\|ps`        | Script type: `sh` (bash/zsh) or `ps` (PowerShell)                        |
| `--force`                | Opt in to installing alongside integrations that are not declared multi-install safe |
| `--integration-options`  | Integration-specific options (e.g. `--integration-options="--commands-dir .myagent/cmds"`) |

Installs the specified integration into the current project. If another integration is already installed, the command only proceeds automatically when all involved integrations are declared multi-install safe. Otherwise, use `switch` to replace the default integration or pass `--force` to explicitly opt in to multi-install. If the installation fails partway through, it automatically rolls back to a clean state.

Installing an additional integration does not change the default integration. Use `specify integration use <key>` to change the default.

> **Note:** All integration management commands require a project already initialized with `specify init`. To start a new project with a specific agent, use `specify init <project> --integration <key>` instead.

**Version note:** Controlled multi-install support was introduced in Spec Kit 0.8.5. If `specify integration install <key>` says another integration is already installed and only suggests `switch` or `uninstall`, check your local CLI with `specify version` and upgrade it. Running a one-shot command such as `uvx --from git+https://github.com/github/spec-kit.git specify ...` uses a temporary copy for that command only; it does not update the persistent `specify` executable on your `PATH`.

## Uninstall an Integration

```bash
specify integration uninstall [<key>]
```

| Option    | Description                                         |
| --------- | --------------------------------------------------- |
| `--force` | Remove files even if they have been modified         |

Uninstalls the current integration (or the specified one). Spec Kit tracks every file created during install along with a SHA-256 hash of the original content:

- **Unmodified files** are removed automatically.
- **Modified files** (where you've made manual edits) are preserved so your customizations are not lost.
- Use `--force` to remove all integration files regardless of modifications.

## Switch to a Different Integration

```bash
specify integration switch <key>
```

| Option                   | Description                                                              |
| ------------------------ | ------------------------------------------------------------------------ |
| `--script sh\|ps`        | Script type: `sh` (bash/zsh) or `ps` (PowerShell)                        |
| `--force`                | Force removal of modified files during uninstall; when the target is already installed, overwrite managed shared templates while changing the default |
| `--integration-options`  | Options for the target integration when it is not already installed      |

If the target integration is not already installed, equivalent to running `uninstall` followed by `install` in a single step. In this mode, `--force` controls whether modified files from the removed integration are deleted. If the target integration is already installed, `switch` only changes the default integration, like `use`; in this mode, `--force` controls whether managed shared templates are overwritten while the default changes. `--integration-options` is rejected for already-installed targets because changing integration options requires reinstalling managed files; run `upgrade <key> --integration-options ...` first, then `use <key>`.

## Use an Installed Integration

```bash
specify integration use <key>
```

| Option    | Description                                         |
| --------- | --------------------------------------------------- |
| `--force` | Overwrite managed shared templates while changing the default |

Sets the default integration without uninstalling any other installed integrations. This also refreshes managed shared templates so command references match the new default integration's invocation style. Modified or untracked shared templates are preserved unless `--force` is used.

## Upgrade an Integration

```bash
specify integration upgrade [<key>]
```

| Option                   | Description                                                              |
| ------------------------ | ------------------------------------------------------------------------ |
| `--force`                | Overwrite files even if they have been modified                          |
| `--script sh\|ps`        | Script type: `sh` (bash/zsh) or `ps` (PowerShell)                        |
| `--integration-options`  | Options for the integration                                              |

Reinstalls an installed integration with updated templates and commands (e.g., after upgrading Spec Kit). Defaults to the default integration; if a key is provided, it must be one of the installed integrations. Detects locally modified files and blocks the upgrade unless `--force` is used. Stale files from the previous install that are no longer needed are removed automatically. Shared templates stay aligned with the default integration even when upgrading a non-default integration.

## Integration-Specific Options

Some integrations accept additional options via `--integration-options`:

| Integration | Option              | Description                                                    |
| ----------- | ------------------- | -------------------------------------------------------------- |
| `generic`   | `--commands-dir`    | Required. Directory for command files                          |
| `kimi`      | `--migrate-legacy`  | Migrate legacy dotted skill directories to hyphenated format   |

Example:

```bash
specify integration install generic --integration-options="--commands-dir .myagent/cmds"
```

## FAQ

### Can I install multiple integrations in the same project?

Yes, but it is intended for team portability rather than the default workflow. Multiple integrations are allowed automatically only when the installed integration and the new integration are declared multi-install safe by Spec Kit. For other combinations, pass `--force` to acknowledge that multiple agents may see unrelated agent-specific instructions or commands.

Spec Kit tracks one default integration in `.specify/integration.json` with `default_integration`, all installed integrations with `installed_integrations`, per-integration runtime settings with `integration_settings`, and a dedicated `integration_state_schema` for future state migrations. The legacy `integration` field remains as an alias for the default integration.

### Which integrations are multi-install safe?

An integration is multi-install safe when it uses isolated agent directories, a dedicated context file that does not collide with another safe integration, stable command invocation settings, and a separate install manifest. Shared Spec Kit templates remain aligned to the single default integration.

The currently declared multi-install safe integrations are:

| Key | Isolation |
| --- | --------- |
| `auggie` | `.augment/commands`, `.augment/rules/specify-rules.md` |
| `claude` | `.claude/skills`, `CLAUDE.md` |
| `codebuddy` | `.codebuddy/commands`, `CODEBUDDY.md` |
| `codex` | `.agents/skills`, `AGENTS.md` |
| `cursor-agent` | `.cursor/skills`, `.cursor/rules/specify-rules.mdc` |
| `gemini` | `.gemini/commands`, `GEMINI.md` |
| `iflow` | `.iflow/commands`, `IFLOW.md` |
| `junie` | `.junie/commands`, `.junie/AGENTS.md` |
| `kilocode` | `.kilocode/workflows`, `.kilocode/rules/specify-rules.md` |
| `kimi` | `.kimi/skills`, `KIMI.md` |
| `qodercli` | `.qoder/commands`, `QODER.md` |
| `qwen` | `.qwen/commands`, `QWEN.md` |
| `roo` | `.roo/commands`, `.roo/rules/specify-rules.md` |
| `shai` | `.shai/commands`, `SHAI.md` |
| `tabnine` | `.tabnine/agent/commands`, `TABNINE.md` |
| `trae` | `.trae/skills`, `.trae/rules/project_rules.md` |
| `windsurf` | `.windsurf/workflows`, `.windsurf/rules/specify-rules.md` |

Integrations that share a context file or command directory with another integration, require dynamic install paths such as `--commands-dir`, or merge shared tool settings are not declared safe by default. They can still be installed alongside another integration with `--force`.

### What happens to my changes when I uninstall or switch?

Files you've modified are preserved automatically. Only unmodified files (matching their original SHA-256 hash) are removed. Use `--force` to override this.

### How do I know which key to use?

Run `specify integration list` to see all available integrations with their keys, or check the [Supported AI Coding Agents](#supported-ai-coding-agents) table above.

### Do I need the AI coding agent installed to use an integration?

CLI-based integrations (like Claude Code, Gemini CLI) require the tool to be installed. IDE-based integrations (like Windsurf, Cursor) work through the IDE itself. Some agents like GitHub Copilot support both IDE and CLI usage. `specify integration list` shows which type each integration is.

### When should I use `upgrade` vs `switch`?

Use `upgrade` when you've upgraded Spec Kit and want to refresh an installed integration's managed files. Use `switch` when you want to replace the current default with another integration; if the target is already installed, `switch` behaves like `use`.
