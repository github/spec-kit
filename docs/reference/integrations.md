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
| [Kiro CLI](https://kiro.dev/docs/cli/)                                               | `kiro-cli`       | Alias: `--integration kiro`                                                                                                               |
| [Mistral Vibe](https://github.com/mistralai/mistral-vibe)                            | `vibe`           |                                                                                                                                           |
| [opencode](https://opencode.ai/)                                                     | `opencode`       |                                                                                                                                           |
| [Pi Coding Agent](https://pi.dev)                                                    | `pi`             | Pi doesn't have MCP support out of the box, so `taskstoissues` won't work as intended. MCP support can be added via [extensions](https://github.com/badlogic/pi-mono/tree/main/packages/coding-agent#extensions) |
| [Qoder CLI](https://qoder.com/cli)                                                   | `qodercli`       |                                                                                                                                           |
| [Qwen Code](https://github.com/QwenLM/qwen-code)                                     | `qwen`           |                                                                                                                                           |
| [Roo Code](https://roocode.com/)                                                     | `roo`            |                                                                                                                                           |
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

## Install an Integration

```bash
specify integration install <key>
```

| Option                   | Description                                                              |
| ------------------------ | ------------------------------------------------------------------------ |
| `--script sh\|ps`        | Script type: `sh` (bash/zsh) or `ps` (PowerShell)                        |
| `--integration-options`  | Integration-specific options (e.g. `--integration-options="--commands-dir .myagent/cmds"`) |

Installs the specified integration into the current project. Fails if another integration is already installed — use `switch` instead. If the installation fails partway through, it automatically rolls back to a clean state.

> **Note:** All integration management commands require a project already initialized with `specify init`. To start a new project with a specific agent, use `specify init <project> --integration <key>` instead.

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
| `--force`                | Force removal of modified files during uninstall                         |
| `--integration-options`  | Options for the target integration                                       |

Equivalent to running `uninstall` followed by `install` in a single step.

## Upgrade an Integration

```bash
specify integration upgrade [<key>]
```

| Option                   | Description                                                              |
| ------------------------ | ------------------------------------------------------------------------ |
| `--force`                | Overwrite files even if they have been modified                          |
| `--script sh\|ps`        | Script type: `sh` (bash/zsh) or `ps` (PowerShell)                        |
| `--integration-options`  | Options for the integration                                              |

Reinstalls the current integration with updated templates and commands (e.g., after upgrading Spec Kit). Defaults to the currently installed integration; if a key is provided, it must match the installed one — otherwise the command fails and suggests using `switch` instead. Detects locally modified files and blocks the upgrade unless `--force` is used. Stale files from the previous install that are no longer needed are removed automatically.

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

### Can I use multiple integrations at the same time?

No. Only one AI coding agent integration can be installed per project. Use `specify integration switch <key>` to change to a different AI coding agent.

### What happens to my changes when I uninstall or switch?

Files you've modified are preserved automatically. Only unmodified files (matching their original SHA-256 hash) are removed. Use `--force` to override this.

### How do I know which key to use?

Run `specify integration list` to see all available integrations with their keys, or check the [Supported AI Coding Agents](#supported-ai-coding-agents) table above.

### Do I need the AI coding agent installed to use an integration?

CLI-based integrations (like Claude Code, Gemini CLI) require the tool to be installed. IDE-based integrations (like Windsurf, Cursor) work through the IDE itself. Some agents like GitHub Copilot support both IDE and CLI usage. `specify integration list` shows which type each integration is.

### When should I use `upgrade` vs `switch`?

Use `upgrade` when you've upgraded Spec Kit and want to refresh the same integration's templates. Use `switch` when you want to change to a different AI coding agent.
