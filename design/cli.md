# Specify CLI Command Architecture

This document defines the CLI adapter structure for Specify commands. It
explains where Typer handlers, CLI infrastructure, CLI-private phases, nested
command groups, and their tests belong.

Every CLI leaf that has another delivery adapter invokes the shared application
operation defined by
[Shared Command Application Architecture](shared.md). This document owns the
CLI surface; it does not redefine semantic validation, orchestration, results,
warnings, errors, or side effects.

The extension hierarchy supplies the reference command-group shape used in
this document. Do not create extra modules merely to make a small command
conform visually.

## Design goals

The CLI structure should make the answer to "where does this command live?"
predictable from the command line itself.

The design optimizes for:

- **Direct navigation:** a command maps to an obvious source file and test.
- **Small working context:** changing one command should not require loading an
  entire command group into memory.
- **Parallel development:** unrelated commands should rarely require edits to
  the same file.
- **Explicit ownership:** shared infrastructure and command-private behavior
  should not be mixed.
- **Adapter discipline:** CLI modules invoke shared operations rather than
  becoming the application implementation.
- **Stable behavior:** structural refactoring must preserve registration,
  output, error handling, compatibility paths, and tests.
- **Agentic development:** coding agents should be able to infer the relevant
  files from the CLI surface without broad repository searches.

## Naming and ownership

### Registered command modules

Each real CLI command uses:

```text
command_<name>.py
```

For example:

```text
specify extension add           -> extensions/command_add.py
specify extension set-priority  -> extensions/command_set_priority.py
specify extension update        -> extensions/command_update.py
```

Only modules representing actual CLI commands use the non-underscored
`command_*.py` prefix. A command module owns:

- The Typer-decorated handler.
- User-facing arguments and options.
- Mapping parsed values into the shared operation request.
- CLI prompting, progress, rendering, JSON streams, and exit-code mapping.
- Small helpers used only by that command.

Semantic validation, application orchestration, typed outcomes, warnings,
expected errors, and side effects belong below the adapter as defined in
[the shared design](shared.md). A CLI-only command may keep small behavior in
its command module, but behavior needed by another adapter must first move to a
shared operation or domain module.

The command function's docstring is user-facing because Typer may display it
as help text. A module docstring is internal and should identify the command,
registration path, and any adjacent private implementation modules.

### Command-private implementation modules

When a CLI adapter has cohesive *CLI-specific* phases that are independently
understandable or testable, use:

```text
_command_<name>_<phase>.py
```

For example:

```text
command_init.py
_command_init_prompting.py
_command_init_rendering.py
```

The leading underscore marks the module as private implementation. The
`command_init` portion groups it with the registered handler in searches and
file listings. The phase suffix communicates its ownership.

Private phase modules must not register additional CLI commands. The public
`command_<name>.py` module remains the sole CLI adapter.

Split a command when a phase:

- Is specific to CLI invocation or presentation.
- Has distinct invariants or failure behavior.
- Can be tested as a meaningful boundary.
- Has enough implementation detail to distract from the CLI handler.
- Is likely to change independently from other phases.

If the phase performs semantic validation, planning, mutation, rollback, or
other behavior another adapter needs, use `_operation_<name>_<phase>.py`
instead, following [the shared design](shared.md#naming-and-layout).

Do not split a command solely because it crossed an arbitrary line count.
Excessive fragmentation makes control flow harder to follow and increases the
number of files an agent must inspect.

### Command-group infrastructure

For a multi-command group, `_commands.py` owns:

- The command group's Typer application.
- Registration of the group's command modules.
- CLI infrastructure genuinely shared by multiple commands or external CLI
  flows.
- Thin compatibility forwarders needed to preserve established import or
  monkeypatch paths.

`_commands.py` must not contain decorated command handlers. A helper used by
only one command belongs in that command's module or one of its private phase
modules.

Compatibility forwarders do not transfer ownership back to `_commands.py`.
They should remain thin and delegate to the module that owns the behavior.
Avoid turning `_commands.py` into a service locator for new code.

### Package `__init__.py`

The package `__init__.py` owns the package's domain API and package-level
behavior. It should provide a brief map to the CLI modules, but it is not the
home for command handlers.

Moving command handlers out of `__init__.py` keeps importing the domain package
separate from understanding or modifying its CLI surface.

## Nested command groups

Nested CLI groups use directories matching the command surface:

```text
specify extension catalog add
                          list
                          remove
```

maps to:

```text
extensions/
├── catalog/
│   ├── __init__.py
│   ├── _helpers.py
│   ├── command_add.py
│   ├── command_list.py
│   └── command_remove.py
├── command_add.py
├── command_list.py
└── ...
```

The nested package's `__init__.py` owns its Typer application and registration.
Shared helpers for that nested surface can live in `_helpers.py`.

A nested CLI hierarchy may also be the root of a bounded subdomain when its
concept depends on the parent domain but owns a distinct resource and lifecycle
that the parent commands do not cover. In that case, keep the subdomain's
non-command modules and its `command_*.py` adapters together in the nested
package. Storage, validation, composition, or distribution behavior specific to
that resource are signals that the namespace is a domain root, not merely a CLI
group.

Creating a nested CLI package solely to group commands does not transfer
same-named parent-domain behavior into that package. If an existing domain
module merely collides with a new nested command namespace, keep the
implementation in the parent domain package (or a focused domain module there).
Preserve an established import path through thin compatibility exports from the
nested package when required.

Do not add a nested `_commands.py` merely for symmetry. Create one only when
the nested group develops substantial shared command infrastructure that no
longer fits cleanly in `__init__.py` and `_helpers.py`.

### Singular command groups

Use the repository's plural command-package convention even when a user-facing
CLI namespace is singular. The `specify self` group therefore lives in
`specify_cli/selfs/`, while the established `specify_cli._version` module
remains the version-domain API and monkeypatch surface. The command adapters
resolve patch-owned `_version` attributes at execution time, and `_version`
re-exports the command symbols for compatibility.

Do not create a nested directory for an implementation phase that is not a CLI
subcommand. For example, an `update/` directory would incorrectly suggest an
`extension update ...` subcommand group. Use `_command_update_<phase>.py` for
a CLI-private phase and `_operation_update_<phase>.py` for semantic validation,
planning, mutation, rollback, or other behavior shared with another adapter.

## Registration

Command registration remains centralized at the command-group boundary.

For the extension group:

1. `src/specify_cli/extensions/_commands.py` owns `extension_app`.
2. `_commands.register()` registers the nested catalog group.
3. It imports each `command_*.py` module so its decorator registers the
   handler.
4. It attaches `extension_app` to the root application.

The nested catalog group follows the same pattern through
`catalog.register()`.

Registration imports should be explicit and ordered consistently. Do not rely
on filesystem discovery to import arbitrary modules, because command exposure
should remain reviewable in one place.

## Shared invocation context and direct CLI policy

The direct local CLI constructs the
[shared pre-authorization context](shared.md#invocation-context) explicitly:

- `launch_working_directory` is captured once when the CLI invocation begins.
- `requested_directory` comes from the command's typed input, or remains absent
  when project discovery should begin from the launch directory.
- `filesystem_scope` is `HostUser`, preserving established CLI behavior for
  explicit paths such as an `init` target outside the launch directory.
- `access_policy` is `DirectCliPolicy`.
- Deadline, cancellation, and output-budget values come from CLI invocation
  infrastructure rather than mutable command globals.

`DirectCliPolicy` represents a user intentionally running a local command under
that user's operating-system permissions. It authorizes the capabilities
declared for the selected operation, including ambient host execution when the
descriptor requires `unrestricted-host-execution`. The shared operation does
not infer this policy and must not substitute MCP's launch-directory boundary.

This policy preserves host access, not semantic consent:

- `--json`, `--non-interactive`, and local invocation do not imply `force`.
- External-source trust and overwrite consent remain explicit request values.
- Command-specific prompts may collect consent before constructing a new
  request, but the adapter does not add consent silently.
- Network defaults and self-modifying behavior remain those explicitly defined
  by the selected operation and its CLI contract.

An embedded CLI host may supply a `RootBound` scope and a stricter access policy
instead. Adapter parity compares equivalent requests under equivalent policy
contexts; a policy denial is not an application-behavior divergence.

## Test structure

Command-focused tests mirror the source command surface under
`tests/specify_cli/`.

For example:

```text
src/specify_cli/extensions/command_add.py
tests/specify_cli/extensions/test_command_add.py

src/specify_cli/extensions/catalog/command_add.py
tests/specify_cli/extensions/catalog/test_command_add.py
```

CLI-private phases use:

```text
src/specify_cli/_command_init_prompting.py
tests/specify_cli/test_command_init_prompting.py
```

The primary `test_command_<name>.py` suite verifies the public command surface.
Phase-specific suites verify detailed invariants without obscuring the primary
command behavior.

CLI adapter tests also verify `DirectCliPolicy` construction, including
explicit targets outside the launch directory and the rule that machine modes
do not add force, trust, or destructive consent.

Shared operation and phase tests use `test_operation_<name>.py` and
`test_operation_<name>_<phase>.py` as defined in
[the shared testing structure](shared.md#testing-structure). They do not move
under `test_command_*.py` merely because the CLI is one caller.

Domain source remains in the parent package's `__init__.py` or a focused
domain module without the `command_` prefix. Its mirrored tests use the domain
subject name, for example:

```text
src/specify_cli/integrations/__init__.py      # catalog domain API
tests/specify_cli/integrations/test_catalog.py

src/specify_cli/integrations/command_search.py
tests/specify_cli/integrations/test_command_search.py
```

Do not put `test_<domain>.py` under a nested command directory merely because
the domain has the same name as that CLI namespace. The nested directory is
reserved for `test_command_<name>.py` suites that exercise its actual
subcommands.

When a domain implementation is split into private modules, mirror those
boundaries in its tests, dropping the source module's leading underscore:

| Preset implementation | Mirrored test under `tests/specify_cli/presets/` |
| --- | --- |
| `_manifest.py` | `test_manifest.py` |
| `_registry.py` | `test_registry.py` |
| `_catalog.py` | `test_catalog.py` |
| `_resolver.py` | `test_resolver.py` |
| `_manager.py` | `test_manager.py` |
| `_manager_commands.py` | `test_manager_commands.py` |
| `_manager_skills.py` | `test_manager_skills.py` |

`test_manager_commands.py` exercises domain command-artifact behavior, not a
registered CLI handler. The `test_command_*.py` suites continue to cover the
CLI surface. `test_catalog.py` belongs at the parent preset package level;
`catalog/test_command_*.py` covers the nested catalog CLI. Package export
compatibility is covered separately by `test_domain_exports.py`.

Not every test is a command test, even when it belongs in the mirrored package
tree:

- Domain model, registry, manager, and catalog behavior belongs at the parent
  package level, not under a nested command namespace and not in
  `test_command_*.py`. Existing consolidated domain suites such as
  `tests/test_extensions.py` may remain in place until separately reorganized.
- Cross-domain CLI contracts remain with the broader integration tests.
- Shared fixtures belong in the narrowest `conftest.py` that serves all of
  their consumers.
- Test helpers should be shared rather than copied when both command and domain
  tests depend on the same behavior.

Moving tests must preserve coverage rather than duplicating it. Run both the
new command-focused suites and the legacy suites from which tests were moved.
For domain splits, also run all new domain suites and any remaining cross-domain
tests in the legacy file. Compare full-suite collection before and after the
move: the count must not decrease, and every existing parametrized test case
must remain represented. A matching total alone does not prove preservation.

## Reference layout

An extension command group using the shared application boundary has this
shape:

```text
src/specify_cli/extensions/
├── __init__.py
├── _commands.py
├── command_add.py
├── command_disable.py
├── command_enable.py
├── command_info.py
├── command_list.py
├── command_remove.py
├── command_search.py
├── command_set_priority.py
├── command_update.py
├── _operation_update.py
├── _operation_update_discovery.py
├── _operation_update_artifacts.py
├── _operation_update_transaction.py
└── catalog/
    ├── __init__.py
    ├── _helpers.py
    ├── command_add.py
    ├── command_list.py
    └── command_remove.py
```

The update command illustrates the distinction:

- `command_update.py` is the registered CLI adapter.
- `_operation_update.py` is the shared application entry point.
- `_operation_update_discovery.py` determines available updates.
- `_operation_update_artifacts.py` prepares and validates update archives.
- `_operation_update_transaction.py` owns backup, installation, rollback, and
  cleanup behavior for every adapter.

## Decision guide

When deciding where code belongs:

| Question | Location |
|---|---|
| Does it define a real CLI command? | `command_<name>.py` |
| Is it a small CLI-only mapping or rendering helper? | That command module |
| Is it a cohesive CLI-only phase? | `_command_<name>_<phase>.py` |
| Does it define semantic validation or orchestration for an operation? | Existing domain module or `_operation_<name>.py` |
| Is it a cohesive shared operation phase? | `_operation_<name>_<phase>.py` |
| Is it CLI infrastructure shared by multiple command adapters? | `_commands.py` or a focused CLI helper |
| Does it define a nested CLI namespace? | A directory matching that namespace |
| Is it shared only by commands in a nested namespace? | The nested package's `_helpers.py` |
| Is it domain behavior independent of the CLI? | The package domain modules, not command modules |

## Anti-patterns

Avoid:

- Adding decorated handlers back to `_commands.py` or package `__init__.py`.
- Naming a private implementation module `command_*.py`.
- Creating nested directories that do not correspond to CLI namespaces.
- Creating `_commands.py` files only for visual symmetry.
- Keeping semantic validation, orchestration, or side effects in a CLI adapter
  when another adapter exposes the same logical operation.
- Calling or parsing another delivery adapter instead of invoking the shared
  operation.
- Moving command-private helpers into shared infrastructure preemptively.
- Duplicating fixtures or helpers to make tests appear more mirrored.
- Splitting a linear function into many files without cohesive phase
  boundaries.
- Changing established monkeypatch or import paths without either migrating
  their consumers or preserving a thin compatibility forwarder.

## Review checklist

For a new or refactored command:

- [ ] The CLI path maps predictably to a `command_<name>.py` module.
- [ ] Only the real command module registers a handler.
- [ ] The adapter maps into the shared operation defined by `design/shared.md`.
- [ ] Semantic validation, orchestration, and side effects are below the CLI
      adapter.
- [ ] Direct CLI invocation constructs `HostUser` filesystem scope and
      `DirectCliPolicy`; embedded confinement is explicit.
- [ ] CLI-private phase modules use `_command_<name>_<phase>.py`; shared phases
      use `_operation_<name>_<phase>.py`.
- [ ] `_commands.py` contains only group infrastructure and genuinely shared
      CLI behavior.
- [ ] Nested directories correspond to real CLI namespaces.
- [ ] Command tests mirror the source structure.
- [ ] Domain and cross-domain tests remain in their appropriate suites.
- [ ] Compatibility paths and user-visible help remain unchanged unless the
      change explicitly requires otherwise.
- [ ] Focused tests, relevant legacy suites, lint, and the full test suite pass.
