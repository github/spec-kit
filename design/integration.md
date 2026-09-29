# Agent Integration Design

Integrations adapt the shared Spec Kit workflows to an AI coding agent. Their
**availability** (built-in, generic, or catalog-only) is separate from their
**output format** (commands, recipes, skills, or a custom layout). The Python
integration registry owns installation behavior; catalogs provide discovery,
not executable integration implementations.

## Availability

| Route | What ships | How users get it |
|---|---|---|
| Built-in | A registered class under `src/specify_cli/integrations/` and, for discovery, an entry in `integrations/catalog.json` | `specify init my-project --integration copilot` or, in an initialized project, `specify integration install copilot` |
| Generic | The registered `generic` integration, with a user-supplied `--commands-dir` and optional `--skills` | `specify init my-project --integration generic --integration-options="--commands-dir .agent/commands"` |
| Community | Metadata in `integrations/catalog.community.json` pointing to an external project | Discover with `specify integration list --catalog` or `search`; obtain and vet it from its source |

The default community catalog is discovery-only. A catalog entry (including
one in a custom catalog) does **not** register a Python integration or make
`specify integration install <key>` work: installation resolves keys through
`INTEGRATION_REGISTRY`. See [catalog contribution guidance](../integrations/CONTRIBUTING.md)
for descriptor and submission details.

## Built-in contract

Each built-in agent has one Python-safe subpackage: `copilot` lives in
`src/specify_cli/integrations/copilot/` and exposes `CopilotIntegration`.
Hyphenated keys use underscores in package names. Its class declares:

- `key`: unique user-facing identifier. CLI-backed integrations normally use
  the executable name: tool checks use the key and runtime dispatch defaults
  to it. Agents with a different executable must handle both paths explicitly;
  IDE-only agents use their canonical identifier.
- `config`: agent name, folder, commands subdirectory, install URL, and
  `requires_cli`.
- `registrar_config`: output directory, format, argument placeholder, and
  file extension.

Import and `_register()` the class in `src/specify_cli/integrations/__init__.py`
(both lists alphabetically). This registry is the source of built-in Python
integration behavior. If the agent supports non-interactive workflows, implement
`build_exec_args()` with the full base signature; `options()` declares
install-time `--integration-options`, not per-workflow runtime options.
Agent-specific native events can be declared on the integration. Set
`multi_install_safe = True` only for a static, non-overlapping agent root and
command directory; shared dynamic paths are not safe by default.

## Output flavors

Choose the smallest base class that matches the agent's native format. The
format bases render shared `templates/commands/*.md`; `IntegrationBase.setup()`
copies templates raw unless overridden. Paths below are relative to each
agent's configured root.

| Flavor | Base class | Typical output | Arguments |
|---|---|---|---|
| Markdown commands | `MarkdownIntegration` | `commands/speckit.plan.md` | `$ARGUMENTS` |
| TOML commands | `TomlIntegration` | `commands/speckit.plan.toml` | `{{args}}` |
| YAML recipes | `YamlIntegration` | `recipes/speckit.plan.yaml` | `{{args}}` |
| Agent skills | `SkillsIntegration` | `skills/speckit-plan/SKILL.md` | `$ARGUMENTS` |
| Nonstandard or dual-mode | `IntegrationBase` or a targeted override of a format base | Agent-specific files, companions, or settings | Agent-specific |

`registrar_config["args"]` selects the installed argument syntax;
`command_filename()` and `setup()` are override points when the native layout
demands them. Keep mode selection, invocation spelling, and registration in
sync. Agent-specific layouts and options belong in the integration code and
the [supported-integrations reference](../docs/reference/integrations.md).

Core templates that call scripts declare `sh`, `ps`, and `py` commands in
`scripts:` frontmatter; template processing replaces `{SCRIPT}` with the
selected variant. `py` is opt-in; non-interactive init defaults to `sh` on
POSIX or `ps` on Windows. Maintain equivalent stdout behavior across all three.
Bundled extension commands do not yet use this core-template script routing.
`__AGENT__` and command references are resolved during rendering, not by
adding per-agent wrapper scripts.

## Ownership and lifecycle

An installation records its files and SHA-256 hashes in
`.specify/integrations/<key>.manifest.json`. Custom `setup()` code must track
files it creates via the manifest (`record_file()` or the base class's
write-and-record helpers). Do not track a pre-existing user file merely because
you merged settings into it: unchanged tracked files are deleted on uninstall.
`teardown()` preserves modified tracked files by default; `--force` can remove
them. Keep agent-specific settings and events consistent with that lifecycle.

The integration does **not** own agent context files such as `AGENTS.md` or
`CLAUDE.md`. The opt-in `extensions/agent-context/` owns their defaults,
configuration, and managed sections; do not add `context_file` fields or
context-file handling to the CLI. `specify init` does not enable the extension
implicitly. Extensions and presets register command or skill overrides for the
current default integration, not every installed integration.

## Adding an agent

1. Run `specify integration scaffold my-agent --type markdown` from this
   repository (`toml`, `yaml`, and `skills` are also supported), or start with
   a custom class only when necessary.
2. Review the generated `config` and `registrar_config`; register the class
   alphabetically and add a matching entry to `integrations/catalog.json`.
3. Add focused coverage in `tests/integrations/test_integration_<package_dir>.py`
   for metadata, generated output, installation, and uninstall (including
   preservation of edited files where applicable).
4. Exercise `specify init my-project --integration <key>` and the install/uninstall
   lifecycle; update the [supported agents](../docs/reference/integrations.md)
   and devcontainer setup if the agent needs additional tooling.

The scaffold creates a package and test skeleton, **not** registry or catalog
entries. Prefer existing bases and shared processing over copied setup loops.
