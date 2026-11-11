# Integration API reference

This reference describes the supported Python contract for authoring both
built-in (embedded) integrations and external integration adapters. They use
the same base classes, rendering hooks, runtime dispatch, and file ownership
API. Descriptor and catalog schemas are documented in the
[catalog reference](catalog.md); installation, trust, and recovery commands
are documented in the [CLI reference](cli.md).

Use the base classes and hooks below rather than importing internal registries,
loaders, or transaction helpers. Those implementation details are not part of
the supported authoring API.

## Delivery routes

Built-in integrations ship with Specify CLI and need no standalone adapter
descriptor or catalog download. Their source registration and delivery
requirements follow the repository's
[contributor guidance](https://github.com/github/spec-kit/blob/main/CONTRIBUTING.md#integration-pull-requests).

External adapters are independently published packages. They implement the
same authoring API but must also meet the package validation, project-local
path, and execution-consent requirements below. Delivery route does not make
private implementation helpers public.

## Package contract

This section applies to external adapters only.

Publish a ZIP, tar.gz, or tgz archive containing these files at its root:

```text
sample-agent/
├── integration.yml
├── __init__.py
└── helpers.py       # optional package-relative modules
```

A single enclosing archive directory is accepted. The root module must export
exactly one concrete `IntegrationBase` subclass whose `key` matches
`integration.id` in the descriptor. Relative imports from the adapter's own
package are supported. Do not register the class through import side effects.

An adapter using the host API and Python standard library requires neither a
separate pip installation nor a change to Spec Kit's source registry. Adapt
the host's commands and extension/preset contributions; do not redistribute
core command templates as an adapter-owned inventory.

## Format bases

Import these classes from `specify_cli.integrations.base`:

| Base | Installed format | Typical command path |
| --- | --- | --- |
| `MarkdownIntegration` | Markdown commands | `commands/speckit.plan.md` |
| `TomlIntegration` | TOML commands | `commands/speckit.plan.toml` |
| `YamlIntegration` | YAML recipes | `recipes/speckit.plan.yaml` |
| `SkillsIntegration` | Agent skills | `skills/speckit-plan/SKILL.md` |
| `IntegrationBase` | Custom layout | Defined by the adapter |

Paths in the table are examples beneath the configured agent folder. Format
bases render the host's templates and selected script variant. The plain
`IntegrationBase.setup()` copies raw templates; prefer a format base unless
you implement rendering yourself.

### Minimal skills adapter

```python
from specify_cli.integrations.base import SkillsIntegration


class SampleIntegration(SkillsIntegration):
    key = "sample-agent"
    config = {
        "name": "Sample Agent",
        "folder": ".sample-agent",
        "commands_subdir": "skills",
        "install_url": "https://example.com/sample-agent",
        "requires_cli": False,
    }
    registrar_config = {
        "dir": ".sample-agent/skills",
        "format": "markdown",
        "args": "$ARGUMENTS",
        "extension": "/SKILL.md",
    }
    multi_install_safe = True
```

For an external package, pair this module with an `integration.yml` whose ID
and name are `sample-agent` and `Sample Agent`, and whose
`requires.speckit_version` matches the host versions you have tested.
A built-in integration uses the same class metadata without a package
descriptor. This example installs skills for an IDE-based agent; it does not
support non-interactive CLI dispatch.

## Class metadata

| Attribute | Contract |
| --- | --- |
| `key` | Unique integration identifier; external adapters must match `integration.id` and cannot replace a built-in key |
| `config.name` | Display name; external adapters must match `integration.name` |
| `config.folder` | Canonical project-relative agent root |
| `config.commands_subdir` | Command or skill directory beneath that root |
| `config.install_url` | Agent installation documentation URL |
| `config.requires_cli` | Boolean indicating whether the agent requires an executable |
| `registrar_config.dir` | Matches `config.folder/config.commands_subdir` |
| `registrar_config.format` | Rendering format: `markdown`, `toml`, or `yaml` |
| `registrar_config.args` | Agent argument placeholder, such as `$ARGUMENTS` or `{{args}}` |
| `registrar_config.extension` | Plain dotted filename suffix, or `/SKILL.md` for Markdown skills |
| `invoke_separator` | Non-empty invocation separator; defaults to `.`, or `-` for `SkillsIntegration` |
| `dev_no_symlink` | Boolean; requests file output instead of symlinks in development registration |
| `multi_install_safe` | Boolean, default false; true requires static, non-overlapping output roots or no files |
| `version` | Optional class attribute; for external adapters, must match the descriptor version if supplied |

An optional `registrar_config.invoke_separator` overrides the class separator
for registration. Development symlinks are disabled if either the class or
`registrar_config.dev_no_symlink` requests it. An optional
`registrar_config.legacy_dir` declares a previous project-relative output
directory for migration.

For external adapters, output roots cannot be home-relative, enter `.git` or `.specify`,
contain traversal, or pass through symlinks. Primary and legacy destinations
cannot overlap each other; multi-install-safe adapters also cannot overlap
another integration's destinations. Comparisons are case-insensitive on every
platform. Some built-in integrations have host-managed home-scoped or legacy
layouts; those do not relax the external package contract.

## Install-time options and layout

Override the class method `options() -> list[IntegrationOption]` to declare
flags accepted through the CLI's `--integration-options`. Import
`IntegrationOption` from `specify_cli.integrations.base`.

| `IntegrationOption` field | Meaning |
| --- | --- |
| `name` | Flag spelling, such as `--skills` |
| `is_flag` | Boolean switch when true; otherwise takes a value |
| `required` | Whether the caller must supply the option |
| `default` | Value when omitted; `None` means no default |
| `help` | User-facing option description |

These are installation options, not per-step workflow runtime options.
Preserve inherited options when adding your own.

For an adapter supporting more than one layout, keep these hooks consistent:

| Hook | Contract |
| --- | --- |
| `is_skills_mode(parsed_options=None, project_root=None) -> bool` | Selects skills versus commands; `SkillsIntegration` returns true by default |
| `effective_invoke_separator(parsed_options=None, project_root=None) -> str` | Invocation separator for the selected installation options |
| `invoke_separator_for_mode(skills_enabled: bool) -> str` | Command-reference separator for the resolved installed mode |
| `command_filename(template_name: str) -> str` | Destination filename for a source template stem |
| `build_command_invocation(command_name: str, args: str = "") -> str` | Native agent invocation for a core or contributed command |

When options are absent during an existing project's lifecycle operation,
`project_root` lets a mode-aware adapter inspect its installed layout rather
than silently migrate it. Invocation spelling, file naming, and rendering
must agree.

## Command rendering hooks

`process_registered_command(frontmatter, body, *, source_id)` returns a
`(frontmatter, body)` pair before the command is rendered. `source_id` is
`core` or the contributing extension/preset ID. Script paths have already
been adjusted; argument placeholders and command-reference tokens are
resolved afterward. A frontmatter `name` is injected only when
`registrar_config.inject_name` is enabled and no non-empty name remains.
Do not assume that `frontmatter["name"]` exists. Return new objects rather
than mutating the input frontmatter.

`post_process_command_content(content: str) -> str` transforms rendered
Markdown, TOML, or YAML command text; its default implementation returns the
content unchanged.

`SkillsIntegration.post_process_skill_content(content: str) -> str`
customizes generated skill content. Inherited `SkillsIntegration.setup()` and
the extension and preset skill-generation passes invoke it when they generate
or rewrite a skill. The base implementation adds shared guidance for
converting dotted hook command names to agent-native hyphenated invocations.
Preserve that guidance when overriding it, for example by calling `super()`.

`process_registered_command()` and `post_process_command_content()` apply
during command registration, including extension and preset contributions.
Inherited `MarkdownIntegration.setup()`, `TomlIntegration.setup()`, and
`YamlIntegration.setup()` install core templates without calling either
hook. If core commands need additional agent-specific transformations,
override `setup()` and use [tracked writes](#setup-and-file-ownership) rather
than relying on registration hooks alone.

A later skill-generation pass may skip an already-existing `SKILL.md`,
including one created by an earlier command-registration pass. No hook call
occurs for that file in the pass that skips it; do not assume that a later
pass reprocesses every installed skill. These hooks concern Spec Kit-generated
outputs, not unrelated skills supplied by an agent or user.

Prefer these hooks to copying host rendering code. Generated PowerShell
functionality must remain compatible with Windows PowerShell 5.1.

## Non-interactive CLI dispatch

CLI adapters implement this hook, returning an argument vector rather than a
shell command string:

```python
def build_exec_args(
    self,
    prompt: str,
    *,
    model=None,
    output_json=True,
    integration_args=None,
    integration_options=None,
    project_root=None,
) -> list[str] | None:
    ...
```

The returned list includes the executable followed by its arguments. Return
`None` when dispatch is unsupported. Explicitly declared host keyword
parameters must have defaults; accepting omitted keywords through `**kwargs`
is also supported. Both prompt-only and complete host calls must be valid.

Inherited CLI dispatch differs by base:

| Base | Default dispatch |
| --- | --- |
| `MarkdownIntegration`, `SkillsIntegration` | When `config.requires_cli` is true, use `-p <prompt>`, `--model <model>` when supplied, and `--output-format json` when `output_json` is true |
| `TomlIntegration` | Same prompt and JSON flags, but the model flag is `-m <model>`; also requires `config.requires_cli` |
| `IntegrationBase`, `YamlIntegration` | Return `None`; no default CLI dispatch |

Override `build_exec_args()` when the agent uses different flags or a
different executable. Installing command files does not by itself provide
non-interactive dispatch support.

`validate_runtime_config(integration_args=None, integration_options=None)`
validates per-step argument lists and option mappings. The default rejects
non-empty runtime configuration with `ValueError`. Adapters supporting those
values must validate and translate them in `build_exec_args()` rather than
silently ignore unsupported options.

For external adapters, required descriptor tools are checked on `PATH`. If a
CLI adapter declares none, tool checking probes its runtime executable.
Version detection is agent-specific; declaring a version constraint does not
supply a universal `--version` invocation.

### Per-step dispatch settings

Workflow `command` and `prompt` steps can request
[`reasoning_effort` and `context_size`](../workflow-steps/types.md#reasoning-effort-and-context-size)
for one CLI invocation. `DISPATCH_SETTINGS` in `specify_cli.integrations.base`
lists them in the order they are checked. Values are opaque strings whose
meaning belongs to the agent's CLI.

The `build_exec_args()` signature above does not change, and an adapter that
does not opt in never receives either keyword: a step that requests one fails
before the CLI runs. Prompt steps pass requested settings to
`build_exec_args()`. Command steps pass them to `dispatch_command()`, whose
base implementation forwards them to `build_exec_args()`. The *receiving
method* is therefore `build_exec_args()`, or `dispatch_command()` for a command
step when the integration overrides it. To opt in:

- Declare `supported_dispatch_settings`, a `frozenset` of the settings the
  integration translates, on the class that defines the receiving method. A
  subclass that overrides that method must declare support again. A
  declaration on any other class, or one that is not a set or frozenset,
  declares nothing.
- Accept a `reasoning_effort=None` or `context_size=None` keyword on the
  receiving method for each declared setting. The host passes a keyword only
  when a step sets that setting, and never passes `""`. Translate the value
  into CLI arguments placed after those from
  `SPECKIT_INTEGRATION_<KEY>_EXTRA_ARGS`, and do not pass it on:
  `IntegrationBase.build_exec_args()` and the format-base builders translate
  neither setting and raise `DispatchSettingsError` rather than drop a value.
- Optionally, override `validate_dispatch_setting(name, value)` to raise
  `ValueError` for a value the CLI would ignore or misread, and
  `dispatch_setting_hint(setting)` to return remediation text that the host
  appends to its error for an unsupported setting.

Before the CLI runs, the host gate `check_dispatch_settings()` checks each
requested setting in `DISPATCH_SETTINGS` order. The value must be 1 to 64
letters, digits, `.`, `_`, or `-`, starting with a letter or digit; the
integration must declare the setting as above; and the receiving method must
accept the keyword or `**kwargs`. The gate then calls
`validate_dispatch_setting()`. Each failure raises `DispatchSettingsError`, a
`ValueError` whose `setting` attribute names the setting; if the receiving
method itself must reject a value, raise it with `setting`. Keep the value out
of every error message: it can come from captured output, which Spec Kit does
not print to the terminal or write to `log.jsonl`. The host cannot detect a
declared setting that the receiving method accepts and then ignores, for
example through `**kwargs`, so a declaration is a promise to translate it.

## Setup and file ownership

Format bases implement setup and teardown. Custom layouts may override:

| Hook | Contract |
| --- | --- |
| `preflight_setup(project_root, parsed_options=None, *, script_type=None) -> None` | Reject setup before shared files are written; raise `ValueError` or `OSError` |
| `setup(project_root, manifest, parsed_options=None, **opts) -> list[Path]` | Write and record agent files; return created paths |
| `teardown(project_root, manifest, *, force=False) -> tuple[list[Path], list[Path]]` | Return removed and preserved paths; inherited behavior preserves modified files unless forced |
| `stale_cleanup_exclusions() -> set[str]` | Project-relative paths upgrade must not delete as stale |

Call inherited behavior where appropriate and preserve host-supplied options,
including `script_type`, `events`, and `force`. Keep generated files under the
declared agent root; the host owns shared Spec Kit scripts and templates.

The host supplies an `IntegrationManifest` to setup and teardown. For custom
writes, use these supported operations:

| Operation | Contract |
| --- | --- |
| `manifest.record_file(rel_path, content, *, ownership="whole") -> Path` | Write bytes or UTF-8 text and record ownership; path is project-relative |
| `manifest.record_existing(rel_path, *, recovered=False, ownership=None) -> None` | Record an existing regular file; `recovered=True` marks preserved existing content |
| `IntegrationBase.write_file_and_record(content, dest, project_root, manifest) -> Path` | Write UTF-8 text with LF newlines and record it; `dest` is the destination path |

Ownership is `whole` for an adapter-owned file, `partial` for entries merged
into a file, or `shared` for a host-shared artifact. Do not claim whole-file
ownership of user settings or shared dispatchers. Manifest paths must be
canonical, project-local, and non-symlinked.

Use a write-and-record operation **before overwriting existing content**.
`record_existing()` alone cannot restore bytes already overwritten outside
the host's tracked write path; such a failure is reported and the resulting
file is retained for manual recovery.

## External adapter lifecycle guarantees

Package trust and reauthorization in this section apply to external adapters,
not built-in integrations shipped with the CLI.

Installation requires an install-enabled catalog and a local trust decision
before downloading/importing executable Python. Metadata-only inspection
commands are `specify integration list --catalog`,
`specify integration search`, and `specify integration info`. Ordinary
`specify integration list` loads trusted installed adapter code; it is not an
import-free inspection command.

Consent is tied to the project, integration ID, and verified package contents.
Copying a project, changing users, or changing package bytes requires new
authorization. Missing, modified, incompatible, or unimportable packages fail
explicitly; publish a new archive and upgrade instead of editing installed
code.

Failed lifecycle operations restore their own tracked changes while preserving
unrelated files, workflow progress, and conflicting external edits. Recovery
failures report retained snapshots for manual recovery. Upgrade and uninstall
preserve modified generated files unless forced; forced recovery still needs
local ownership proof to delete old files and does not bypass catalog policy
or replacement-package trust.

Adapter instances can serve concurrent dispatch and rendering operations.
Keep per-call state local, and do not rely on mutable global registration or
another project's installed package. For native event support, preserve the
host's event ownership when extending `emit_events()` or `remove_events()`;
see [runtime events](cli.md#runtime-events) for supported events and options.

## See also

- [Developing and publishing integrations](contributing.md)
- [Descriptor and catalog schemas](catalog.md)
- [Integration CLI and trust](cli.md)
- [Per-step workflow integration configuration](../workflow-steps/types.md#per-step-integration-configuration)
