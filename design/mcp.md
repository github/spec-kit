# Specify MCP Command Architecture

This document defines the target architecture for exposing Specify operations
through the Model Context Protocol (MCP). It is the MCP counterpart to
[Specify CLI Command Architecture](cli.md): command paths, ownership,
registration, contracts, tests, and migration should be predictable from the
surface being changed.

The current `src/specify_cli/mcp_server/` implementation is intentionally
experimental and transitional. It exposes only `version` through generic
list, describe, and run tools, invokes the CLI in a child process, and parses
the CLI JSON result. That is a bounded first implementation, not the target
architecture described here.

## Design goals

The MCP structure should make the answer to "where does this tool's behavior
live?" as predictable as the equivalent CLI question.

The design optimizes for:

- **One logical operation:** a CLI leaf and its MCP tool are two adapters for
  the same application behavior.
- **Adapter parity:** CLI and MCP inputs, results, warnings, errors, and side
  effects remain semantically equivalent.
- **Typed discovery:** each available MCP operation has a command-specific
  input and output schema.
- **Explicit exposure:** every CLI leaf has a reviewable MCP inventory
  disposition; tools are never exposed through filesystem discovery.
- **Small working context:** changing one operation should normally require
  only its domain, CLI adapter, MCP adapter, and mirrored tests.
- **Policy visibility:** project writes, execution, network access, trust
  decisions, and self-modification are declared and enforced.
- **Transport independence:** stdio and future Streamable HTTP hosting do not
  change command behavior.
- **Incremental migration:** commands move to the shared model without a flag
  day or compatibility break.

## Non-goals

This design does not:

- Make MCP a wrapper around the human CLI.
- Require every CLI leaf to be remotely invokable regardless of risk or
  readiness.
- Turn existing human output into an MCP or JSON contract.
- Make `--json`, `--non-interactive`, or an MCP invocation imply `--force`,
  trust, destructive consent, or network permission.
- Define a public Python API for third-party callers. The supported external
  surfaces remain the CLI, MCP contracts, integrations, and workflow steps.
- Replace command-owned application behavior with one universal command
  engine or central service locator.
- Require an otherwise simple operation to be split into extra modules only
  for visual symmetry.

## One logical operation, two adapters

For every MCP-eligible CLI leaf, the architecture has three conceptual
layers:

```text
CLI arguments/options ─┐
                      ├─> shared operation request -> application behavior
MCP tool input JSON ───┘                          -> operation outcome

operation outcome ─────┬─> CLI human or JSON rendering
                       └─> MCP structured content or tool error
```

The CLI and MCP adapters are peers:

- The CLI adapter owns Typer/Click declarations, terminal interaction, human
  rendering, exit codes, and CLI JSON serialization.
- The MCP adapter owns tool metadata, MCP input/output schemas, protocol
  result conversion, and MCP annotations.
- The shared operation owns semantic validation, orchestration, side effects,
  typed results, warnings, and structured domain errors.

Neither adapter calls the other. In particular, the target MCP adapter must
not invoke Typer handlers, start `specify` as a child process, scrape Rich
output, or parse CLI stderr.

The shared operation is the behavioral source of truth. Adapters may differ
in presentation, but they must not differ in what the operation means.

## Ownership boundaries

| Concern | Owner |
| --- | --- |
| Semantic request and result models | The relevant command/domain hierarchy |
| Semantic validation and orchestration | The shared operation/application module |
| Domain errors and warning codes | The relevant command/domain hierarchy |
| CLI arguments, prompts, text, JSON streams, and exit codes | `command_<name>.py` |
| MCP tool name, description, annotations, and protocol conversion | `mcp_<name>.py` |
| Per-group MCP registration and command inventory | The hierarchy's `_mcp.py` or small package registration module |
| Cross-command invocation context and access-policy primitives | Shared MCP/application infrastructure |
| MCP server lifecycle and transport hosting | `specify_cli/mcp_server/` |
| Authentication and connection concerns for future HTTP hosting | The HTTP transport layer |

Command-specific contracts do not belong in a central MCP catalog. Shared MCP
infrastructure may define primitives such as `InvocationContext`,
`OperationWarning`, `OperationError`, access policy, cancellation, and output
budgets. It must not accumulate command-specific request models, result
models, validation, or orchestration.

## Operation identity and MCP tool design

Each logical operation has three related identities:

| Surface | Example |
| --- | --- |
| Logical operation ID | `artifact.list` |
| CLI path | `specify artifact list` |
| MCP tool name | `specify_artifact_list` |

Operation IDs use dot-separated CLI path segments without the leading
`specify`. MCP tool names use the same segments with underscores and a
`specify_` prefix. Hyphens in CLI segments become underscores:

```text
specify extension set-priority
operation: extension.set-priority
tool: specify_extension_set_priority
```

An explicit override is allowed only to satisfy a protocol restriction or
resolve a demonstrated collision. The inventory must record the override and
the reason.

### First-class tools, not a generic execution facade

The target surface exposes each *eligible* CLI leaf as a first-class MCP tool.
A generic `specify_run_command` facade is not the target.

The current MCP SDK creates one JSON input schema per registered tool from the
tool's typed callable. First-class tools therefore preserve:

- Per-command schemas and descriptions.
- MCP client discovery and argument validation.
- Command-specific output schemas and annotations.
- Reviewable registration and policy metadata.
- A direct mapping back to the CLI leaf and owning source files.

A generic facade would instead reduce the protocol-visible input to a command
string plus an opaque or oversized union of arguments. That weakens schema
validation, discoverability, policy review, and compatibility analysis.

At the time this document was written, the CLI had 90 leaf commands.
`specify mcp` is the transport host and is permanently excluded from recursive
exposure, leaving 89 leaf operations that require an explicit inventory
disposition. This count is large enough that registration must be organized
per command hierarchy, but not a reason to erase command-specific contracts
behind a generic tool. Tests should derive the current count rather than
hard-code 90.

### Current transitional inventory

The point-in-time CLI leaf inventory used to establish this design is:

```text
root: init, check, version, mcp
self: check, upgrade
extension: add, disable, enable, info, list, remove, search, set-priority,
  update
extension.catalog: add, list, remove
integration: install, uninstall, switch, upgrade, list, status, use, search,
  info, scaffold
integration.catalog: add, list, remove
event: run
preset: list, add, remove, update, search, resolve, info, set-priority, enable,
  disable
preset.catalog: add, list, remove
artifact: list, info, lookup
bundle: search, info, list, install, add, update, remove, validate, build, init
bundle.catalog: add, list, remove
workflow: run, resume, status, list, add, remove, update, enable, disable,
  search, info, resolve
workflow.catalog: add, list, remove
workflow.step: list, add, remove, search, info
workflow.step.catalog: add, list, remove
workflow.overlay: add, set-priority, enable, disable, remove, list
```

In the current experimental server:

- `version` is available only through the transitional generic tools and maps
  to the target first-class tool `specify_version`.
- `mcp` is excluded because it is the transport host.
- The other 88 leaves are unavailable through MCP. Their initial target
  disposition is `deferred` until their shared operation, typed contract, and
  access-policy behavior satisfy this design.

This list records the migration baseline, not a second registration source.
Once implemented, the hierarchy-owned inventory and its parity tests are
authoritative.

Metadata-only inventory or describe tools may remain for compatibility or
diagnostics. They do not replace first-class operation tools, and a generic
run tool should be deprecated after migrated tools cover its supported
operations.

## Naming and file layout

MCP adapters mirror the CLI command path and live beside the owning command
and domain code:

```text
src/specify_cli/extensions/
├── __init__.py
├── _commands.py
├── _mcp.py
├── command_add.py
├── mcp_add.py
├── command_list.py
├── mcp_list.py
└── catalog/
    ├── __init__.py
    ├── _mcp.py
    ├── command_add.py
    ├── mcp_add.py
    ├── command_list.py
    └── mcp_list.py
```

The conventions are:

- `command_<name>.py` is the sole CLI adapter for a real leaf command.
- `mcp_<name>.py` is the sole MCP adapter for the same logical operation.
- `_mcp.py` owns explicit MCP registration and inventory for a command group.
- Nested directories continue to correspond to real CLI namespaces or bounded
  subdomains, following [the CLI design](cli.md#nested-command-groups).
- The shared operation lives in the closest Typer-free domain module when one
  already exists.
- If a dedicated application entry point is needed, use
  `_operation_<name>.py`.
- Tests mirror these names under `tests/specify_cli/`.

Do not create a top-level MCP mirror of the entire CLI tree under
`mcp_server/commands/`. That would separate command contracts from their
owning domains and make unrelated command hierarchies depend on a central
package.

Do not add `_mcp.py` merely for symmetry. A package with one small tool may
register it through an existing focused registration module. Create `_mcp.py`
when the hierarchy needs an explicit list of several tools, shared adapter
helpers, or inventory dispositions.

## Simple and complex operations

The same cohesion rules used for command-private phases apply below both
adapters.

### Simple operation

A simple operation may use an existing domain module or one focused operation
module:

```text
command_version.py
mcp_version.py
_version.py
```

Both adapters map to the typed operation in `_version.py`. No extra phase
module is required.

### Complex operation

When a shared operation has cohesive phases with distinct invariants or
failure behavior, use:

```text
_operation_<name>.py
_operation_<name>_<phase>.py
```

For example:

```text
command_init.py
mcp_init.py
_operation_init.py
_operation_init_validation.py
_operation_init_plan.py
_operation_init_apply.py
_operation_init_finalize.py
```

`_operation_init.py` remains the application entry point. Phase modules do not
register CLI commands or MCP tools.

Adapter-only phases retain adapter-specific names:

```text
_command_<name>_<phase>.py
_mcp_<name>_<phase>.py
```

Use them only when the phase genuinely belongs to presentation or protocol
adaptation. If both adapters need the phase, it belongs below them as an
operation or domain phase.

Do not split a linear operation because it crossed an arbitrary line count.
Split when a phase has distinct invariants, rollback behavior, inputs,
outputs, or tests.

## Registration and explicit inventory

Registration remains explicit at each command-group boundary.

For a group such as `artifact`:

1. `artifacts/_mcp.py` lists every `artifact.*` CLI leaf.
2. Each leaf has exactly one inventory record.
3. Available records import and register their `mcp_<name>.py` adapter.
4. Deferred, policy-disabled, and excluded records state a reason.
5. The root MCP composition module calls `artifacts._mcp.register(...)`.

The root MCP server may aggregate hierarchy registration functions, but it
must not own their command-specific schemas or dispatch behavior. Registration
imports are explicit and consistently ordered. Filesystem scanning,
`command_*.py` introspection, and decorator side effects are not substitutes
for an inventory.

A conceptual inventory record contains:

```text
operation_id
cli_path
mcp_tool_name
contract_version
availability
availability_reason
side_effect_class
network_access
project_scope
default_timeout
```

The static disposition values are:

- `available`: implemented and registered as a first-class tool.
- `deferred`: the CLI leaf exists, but shared operation extraction or a typed
  MCP contract is incomplete.
- `excluded`: the command is intentionally not an MCP operation.

An available tool may have an effective runtime state of `policy-disabled`.
It remains discoverable with its typed schema and annotations, but invocation
returns a structured `policy_denied` error. This keeps discovery stable across
policy profiles and prevents a host configuration change from changing tool
identity.

Every CLI leaf must appear exactly once. The inventory parity test fails for a
missing leaf, duplicate logical operation, duplicate tool name, stale CLI
path, or unexplained exclusion.

### Permanent and conditional exclusions

`specify mcp` is permanently excluded because it hosts the MCP transport; an
MCP tool that starts another MCP server would be recursive infrastructure, not
an application operation.

Other commands are not excluded merely because they mutate state. They are
classified and gated. For example:

- `self.upgrade` is self-modifying and should be unavailable under the
  default local policy. Exposure requires an explicit administrative policy
  and a command contract that preserves upgrade safeguards.
- `event.run`, `workflow.run`, and `workflow.resume` are execution operations
  and require execution policy.
- `init`, add/remove/update commands, and configuration changes are
  project-write operations, with any stronger capabilities declared
  separately.
- A command that still prompts, writes directly through its Typer handler, or
  lacks a typed result remains `deferred` until those concerns move into a
  shared operation.

Exclusion and deferral are reviewable architecture decisions, not silent
omissions.

## Command contracts

### Typed requests

The command/domain hierarchy owns a typed request model for semantic inputs.
The model:

- Uses domain names rather than CLI flag spellings.
- Distinguishes omitted values from explicit false or empty values.
- Rejects unknown fields.
- Represents paths, enums, identifiers, and bounded collections explicitly.
- Contains explicit consent fields such as `force` or
  `trust_extension_urls` only when the operation supports them.

The CLI adapter maps parsed arguments and options into the request. The MCP
adapter exposes a command-specific JSON schema and maps validated tool input
into the same request.

Typer usage errors remain CLI concerns. Semantic errors such as an unknown
integration, invalid project state, or incompatible options belong to the
operation so both adapters report the same failure.

### Typed results and warnings

The operation returns a typed outcome containing:

- The command-specific result.
- Zero or more structured warnings.
- Execution metadata needed by adapters, such as changed paths or whether a
  transaction committed.

Warnings have a stable `code`, human-readable `message`, and optional typed
details. A warning is not printed inside the operation. The CLI adapter
renders it to the appropriate human or JSON channel; the MCP adapter includes
it in the command-specific structured result.

Output types remain command-owned. There is no mandatory universal
`{"ok": true, "result": ...}` envelope. A shared outcome type is an internal
application mechanism, not a reason to replace established machine contracts.

### Structured errors

Expected failures use a typed operation error with:

```text
code
message
details
retryable
exit_code
```

The operation hierarchy owns the error code and details schema. The CLI
adapter maps it to human output or the command's JSON failure contract and
then uses the declared exit code. The MCP adapter maps it to an MCP tool error
with structured content. Neither adapter exposes a traceback, secret, raw
subprocess output, or success-shaped fallback.

Unexpected exceptions are normalized at the adapter boundary to a sanitized
`internal_error`, logged only through the transport-appropriate diagnostic
channel.

## Machine contracts and version metadata

Existing CLI JSON contracts are compatibility constraints. Extracting a
shared operation must preserve field names, value semantics, stdout/stderr
purity, and error behavior unless a separately reviewed contract change says
otherwise.

Each logical operation declares a `contract_version` in its inventory and MCP
tool metadata. The version identifies the request/result/warning/error
contract, not the MCP transport version or CLI package version.

Contract version metadata must not be injected into an established result
whose schema does not already contain it. For example, the current
`specify version --json` result intentionally returns `cli_version`,
`runtime`, `system`, and `features` directly. Its MCP tool should preserve
that result shape while exposing the contract version through tool or
inventory metadata.

Rules for contract evolution:

- Backward-compatible optional fields and new warning codes may retain the
  current major contract version.
- Removing, renaming, or changing the meaning of an input, output, warning,
  or error requires a new major contract version and a migration plan.
- CLI and MCP adapters for the same operation advertise the same contract
  version.
- An adapter-only presentation change does not change the operation contract
  version.
- Tests lock established JSON shapes and MCP schemas at the command boundary.

## Invocation context and project resolution

Shared operations receive an immutable invocation context rather than reading
transport globals:

```text
InvocationContext
├── launch_working_directory
├── project_root
├── allowed_roots
├── access_policy
├── deadline
├── cancellation
└── output_budget
```

Project-scoped MCP tools accept an optional project directory when their use
case needs one. If omitted, project discovery starts from the server launch
working directory, matching normal CLI behavior. Resolution uses the same
domain helper as the CLI and produces the same semantic errors.

The adapter resolves and normalizes paths before invoking the operation:

- Do not call `os.chdir()` for an MCP request. A long-lived server may process
  concurrent or sequential calls with different project contexts.
- Pass the resolved project root explicitly through the operation and its
  phases.
- Enforce host-provided allowed roots when available.
- Reject a path outside allowed roots with a structured policy error.
- Do not infer the project from an unrelated server process state after the
  invocation begins.

`init` is a special project-creation operation: its request identifies the
target directory, while the context identifies the launch directory and
allowed roots.

## Non-interactive behavior

MCP operations are always non-interactive:

- They never read stdin.
- They never open arrow-key selectors or terminal confirmations.
- They never wait for an answer that is not represented in the request.
- A safe documented default may be applied only when the CLI operation uses
  the same non-interactive default.
- If no safe default exists, return a structured `input_required` or
  `confirmation_required` error explaining which field must be supplied.

Machine mode is not consent. An MCP call, `--json`, `--non-interactive`, a
host confirmation dialog, or an enabled side-effect class does not imply:

- `force=true`.
- Trust of an external URL or downloaded executable content.
- Permission to overwrite user-modified files.
- Permission to leave the declared project root.
- Permission to execute a workflow, hook, installer, or arbitrary command.

Consent must be explicit in the command request and valid under the active
access policy. MCP annotations and host UI are advisory; the server still
enforces operation requirements.

## Side-effect classes and access policy

Every operation declares the highest applicable side-effect class:

| Class | Meaning | Representative commands |
| --- | --- | --- |
| `read-only` | Reads local state and returns data without persistent mutation | `version`, `check`, `artifact list` |
| `project-write` | Creates or changes files or configuration within an allowed project/target root | `init`, `extension add`, `preset enable` |
| `execution` | Starts workflows, hooks, agent/tool processes, or other executable behavior | `workflow run`, `workflow resume`, `event run` |
| `self-modifying` | Changes the Specify installation, server runtime, or machine-level state | `self upgrade` |

Network access is an independent declaration: `none`, `optional`, or
`required`. A read-only search may use the network, while a project-write
operation may be fully offline.

The MCP server receives an access policy from its host configuration. The
default policy is conservative:

- `read-only` operations are permitted.
- `project-write`, `execution`, and `self-modifying` operations require
  explicit enablement.
- Filesystem access is limited to host-provided roots or, when none are
  provided, the server launch working directory.
- Network access is denied unless explicitly enabled.
- External-source trust is separately controlled and remains default-deny.

Tool annotations should reflect the declared class, but annotations do not
replace server-side enforcement. If policy denies an otherwise implemented
tool, the registered tool returns a structured `policy_denied` error. The
inventory reports its effective `policy-disabled` state and the reason.

An operation must not relabel itself as read-only merely because writes are
rare, optional, or expected to be idempotent. Classify the most powerful path
the request can activate.

## Trust, confirmation, and network responsibilities

The shared operation owns the semantic rule that an action requires trust or
confirmation. The adapters own how explicit consent enters the request.

- External URL installation remains default-deny without an explicit trust
  field.
- A non-empty target directory remains protected without explicit overwrite
  consent.
- Catalog discovery permission does not imply install permission.
- A network-enabled policy does not imply trust in arbitrary returned content.
- Redirect, digest, source, and compatibility validation remain domain
  behavior, shared by both adapters.
- Transport authentication does not replace operation authorization.

Network calls use bounded connect/read timeouts and honor the invocation
deadline. Operations do not silently switch from offline to online behavior.
When a request supports offline behavior, the input states it explicitly or
uses the same documented default as the CLI.

## Timeouts, cancellation, stdin, and bounded output

The transport adapter creates the invocation deadline and cancellation signal;
the operation and its phases honor them.

- Subprocesses and network calls receive a timeout derived from the remaining
  deadline.
- Complex operations check cancellation between cohesive phases.
- Transactional mutations roll back or report partial state according to
  their domain contract.
- Cancellation returns a structured cancellation error, never a successful
  empty result.
- No operation reads stdin or inherits an interactive child stdin.
- Captured stdout/stderr and diagnostic details are size-bounded.
- Potentially large lists use command-owned limits or pagination.
- Truncation is explicit and includes a continuation cursor or a clear
  `truncated` marker; it is never silent.
- Output-budget enforcement belongs to shared invocation infrastructure, while
  pagination semantics belong to the command hierarchy.

## Transport separation

`specify_cli/mcp_server/` owns server composition and transport hosting, not
command behavior.

The initial transport remains stdio:

- Stdout is reserved for MCP protocol frames.
- Logs and diagnostics use stderr or the SDK's logging channel.
- Startup banners, Rich rendering, and CLI warnings never enter stdout.

Future Streamable HTTP support should add a transport host around the same
tool registry and operation adapters. HTTP-specific authentication, sessions,
origin checks, request sizing, and connection cancellation belong to that
transport layer. Tool names, schemas, operation contracts, project behavior,
and access classes must not change merely because the transport changes.

An illustrative infrastructure layout is:

```text
src/specify_cli/mcp_server/
├── __init__.py
├── server.py
├── registry.py
├── policy.py
├── context.py
└── transports/
    ├── stdio.py
    └── streamable_http.py
```

Create only the modules justified by implemented behavior. The layout is a
target boundary, not a requirement to add empty files.

## Testing structure

Tests mirror source ownership:

```text
src/specify_cli/artifacts/_operation_list.py
tests/specify_cli/artifacts/test_operation_list.py

src/specify_cli/artifacts/command_list.py
tests/specify_cli/artifacts/test_command_list.py

src/specify_cli/artifacts/mcp_list.py
tests/specify_cli/artifacts/test_mcp_list.py
```

Private operation phases use:

```text
src/specify_cli/_operation_init_validation.py
tests/specify_cli/test_operation_init_validation.py
```

The required test layers are:

### Operation tests

- Cover valid requests and intended results.
- Cover invalid inputs, prevented behavior, and domain failures.
- Verify warnings, typed errors, side effects, rollback, cancellation, and
  bounded behavior where applicable.
- Avoid Typer, MCP transport, and Rich assertions.

### CLI adapter tests

- Verify argument and option mapping.
- Verify prompts and non-interactive behavior.
- Verify human rendering, JSON streams, and exit codes.
- Preserve established help and compatibility import paths.

### MCP adapter tests

- Verify tool name, description, annotations, and exact input/output schemas.
- Verify mapping to the shared operation request and outcome.
- Verify structured warnings and tool errors.
- Verify access-policy, trust, timeout, cancellation, and output-budget
  failures.

### Inventory and parity tests

- Walk the actual CLI command tree and require one MCP inventory disposition
  for every leaf.
- Reject duplicate operation IDs and MCP tool names.
- Require reasons for every deferred or excluded command.
- Verify available tools are registered by the owning hierarchy.
- Run CLI JSON and MCP adapters against the same operation fixture and compare
  semantic result, warning, error, and side-effect behavior.
- Preserve total pytest collection when tests move, as required by the CLI
  architecture.

Adapter parity does not require byte-identical human terminal output. It
requires both adapters to invoke the same operation contract with equivalent
inputs and to represent the same outcome without inventing behavior.

### Protocol tests

- Keep an in-memory MCP registration and dispatch test.
- Keep a real stdio initialize/list/call test with protocol-pure stdout.
- Add equivalent Streamable HTTP protocol, authentication, cancellation, and
  isolation tests when that transport exists.
- Test malformed input, policy denial, unavailable tools, internal failure
  sanitization, and output bounds as negative cases.

Behavioral changes follow
[Testing deterministic behavior](../CONTRIBUTING.md#testing-deterministic-behavior):
positive and negative evidence is required, and bug fixes need before-and-after
regression evidence.

## Incremental migration

Migration proceeds by operation, preserving the experimental server until
first-class replacements are verified.

1. **Introduce shared primitives and inventory.** Add invocation context,
   policy, warning/error primitives, and explicit per-leaf dispositions
   without changing supported tools.
2. **Extract `version`.** Move version collection into a typed shared
   operation used by both `command_version.py` and `mcp_version.py`. Register
   `specify_version` alongside the transitional generic tools and prove output
   parity.
3. **Add project-scoped reads.** Migrate `artifact list`, then adjacent
   artifact inspection operations, establishing project-root and bounded
   output behavior.
4. **Migrate bounded mutations.** Extract shared operations for focused
   project-write commands, preserving CLI behavior and adding explicit policy
   and consent tests.
5. **Migrate complex execution and initialization.** Refactor cohesive phases
   below both adapters. Migrate `init`, workflow execution, and similar
   commands only after cancellation, rollback, trust, and timeout contracts
   are explicit.
6. **Retire subprocess dispatch.** Remove per-operation child-process
   invocation after every command supported by the generic runner has a
   first-class tool and compatibility window.
7. **Deprecate the generic run tool.** Keep inventory/describe diagnostics if
   useful, but remove generic execution from the target surface.
8. **Add Streamable HTTP.** Reuse the same registry and adapters; add only
   transport-specific hosting and security behavior.

Migration must preserve established CLI imports and monkeypatch paths through
thin forwarders when required. Do not combine architecture migration with
unrelated command behavior changes.

## Representative operation layouts

### `version`: simple, process-scoped read

```text
src/specify_cli/
├── _version.py
├── command_version.py
└── mcp_version.py

tests/specify_cli/
├── test_operation_version.py
├── test_command_version.py
└── test_mcp_version.py
```

Contract:

```text
operation_id: version
cli_path: specify version
mcp_tool_name: specify_version
side_effect_class: read-only
network_access: none
project_scope: process
```

`_version.py` owns typed version collection and `VersionResult`.
`command_version.py` renders the panel, feature text, or established JSON
object. `mcp_version.py` returns the same result fields as structured content.
No adapter starts a child process.

### `artifact list`: project-scoped read

```text
src/specify_cli/artifacts/
├── __init__.py
├── _commands.py
├── _mcp.py
├── _operation_list.py
├── command_list.py
└── mcp_list.py

tests/specify_cli/artifacts/
├── test_operation_list.py
├── test_command_list.py
└── test_mcp_list.py
```

Contract:

```text
operation_id: artifact.list
cli_path: specify artifact list
mcp_tool_name: specify_artifact_list
side_effect_class: read-only
network_access: none
project_scope: required
```

The request contains an optional project directory. Project resolution
produces a normalized root in the invocation context. `_operation_list.py`
uses `ArtifactCatalog` and returns typed artifact rows. The CLI adapter
preserves its JSON stream contract; the MCP adapter exposes the rows through
its output schema and never captures CLI stdout. Invocation output budgets
must produce explicit bounded-output behavior rather than silent truncation.

### `init`: complex project mutation

```text
src/specify_cli/
├── command_init.py
├── mcp_init.py
├── _operation_init.py
├── _operation_init_validation.py
├── _operation_init_plan.py
├── _operation_init_apply.py
└── _operation_init_finalize.py

tests/specify_cli/
├── test_command_init.py
├── test_mcp_init.py
├── test_operation_init.py
├── test_operation_init_validation.py
├── test_operation_init_plan.py
├── test_operation_init_apply.py
└── test_operation_init_finalize.py
```

This remains at the root; an `init/` directory would incorrectly imply a
`specify init ...` nested command group.

Contract:

```text
operation_id: init
cli_path: specify init
mcp_tool_name: specify_init
side_effect_class: project-write
network_access: optional
project_scope: creates-target
```

The request explicitly carries the target, integration, script type, optional
preset/extensions, `force`, and external-URL trust decision. The MCP adapter
never prompts and never turns its machine context into force or trust. The
shared operation validates inputs, builds a plan, applies transactional
changes, and returns created/updated paths plus structured warnings. The CLI
adapter may gather interactive choices before constructing the same request.

If the target is non-empty and `force` is false, both adapters receive the same
semantic confirmation-required failure. The CLI may respond by prompting and
retrying with explicit consent; the MCP tool returns the structured error and
requires a new call with `force=true`, subject to policy.

## Anti-patterns

Avoid:

- MCP calling Typer handlers directly.
- MCP starting the human CLI for normal dispatch.
- Parsing Rich output, terminal text, or CLI stderr to recover results.
- Duplicating command orchestration in an MCP adapter.
- Defining command-specific request and result models in a central MCP
  catalog.
- Hiding behavior behind a central service locator or string-based dispatcher.
- Exposing every operation through one generic run tool.
- Forcing every command into an oversized universal execution engine.
- Treating MCP tool annotations as authorization.
- Treating machine mode as force, trust, overwrite consent, or execution
  permission.
- Reading stdin or changing process-wide cwd during a tool call.
- Auto-registering tools by scanning files or importing every
  `command_*.py`.
- Creating an MCP directory tree that duplicates and detaches the CLI/domain
  hierarchy.
- Adding operation phases or `_mcp.py` files solely for symmetry.
- Silently omitting CLI leaves from the MCP inventory.
- Returning partial, truncated, or fallback data as a successful complete
  result.
- Letting transport concerns leak into command contracts.

## Review checklist

For a new or migrated MCP operation:

- [ ] The CLI leaf and MCP tool map to one logical operation ID.
- [ ] Both adapters dispatch into the same typed shared implementation.
- [ ] The MCP tool is first-class and has a command-specific schema.
- [ ] The tool name and source layout mirror the CLI path.
- [ ] The owning command hierarchy declares registration and inventory.
- [ ] Availability, side-effect class, network access, project scope, and
      contract version are explicit.
- [ ] Non-interactive behavior does not imply force, trust, or consent.
- [ ] Project paths are normalized and passed explicitly without `os.chdir()`.
- [ ] Timeouts, cancellation, stdin, and output bounds are handled.
- [ ] Existing CLI human and JSON behavior remains compatible.
- [ ] Operation, CLI adapter, MCP adapter, parity, and protocol tests cover
      positive and negative behavior.
- [ ] Stdio remains protocol-pure, and command behavior is transport-neutral.
- [ ] No command behavior was added to central MCP infrastructure.
