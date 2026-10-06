# Specify MCP Command Architecture

This document defines the architecture for exposing Specify operations through
the Model Context Protocol (MCP). It is the MCP counterpart to
[Specify CLI Command Architecture](cli.md).

Both adapters invoke the application layer defined by
[Shared Command Application Architecture](shared.md). This document owns MCP
tool identity, exposure, annotations, protocol mapping, and local stdio
hosting. It does not redefine semantic validation, orchestration, results,
warnings, errors, or side effects.

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
- **Side-effect visibility:** project writes, execution, network access, trust
  decisions, and self-modification are declared for review and conservatively
  projected into standard MCP annotations.
- **Local stdio boundary:** protocol framing and diagnostics remain outside
  command behavior.

## Non-goals

This design does not:

- Make MCP a wrapper around the human CLI.
- Require every CLI leaf to be invokable regardless of risk or readiness.
- Turn existing human output into an MCP or JSON contract.
- Make `--json`, `--non-interactive`, or an MCP invocation imply `--force`,
  trust, destructive consent, or network permission.
- Define a public Python API for third-party callers. The supported external
  surfaces remain the CLI, MCP contracts, integrations, and workflow steps.
- Replace command-owned application behavior with one universal command
  engine or central service locator.
- Require an otherwise simple operation to be split into extra modules only
  for visual symmetry.

## Shared operation dependency

An MCP tool is a delivery adapter for a logical operation defined by
[the shared architecture](shared.md). It maps MCP input into the shared typed
request and maps the shared outcome into MCP structured content or a tool
error.

The MCP adapter owns:

- Tool name, description, annotations, and protocol schemas.
- Mapping between MCP content and shared request/outcome types.
- Per-group MCP registration and static inventory.
- Protocol diagnostics and local stdio server hosting.

It does not own semantic validation, application orchestration, side effects,
or command-specific domain contracts. It must not invoke Typer handlers, start
`specify` as application dispatch, scrape Rich output, or parse CLI stderr.

Shared MCP infrastructure may define protocol and registration primitives. It
must not become a central catalog of command-specific request models, results,
validation, or orchestration.

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

The MCP surface exposes each *eligible* CLI leaf as a first-class MCP tool.
A generic `specify_run_command` facade is not part of the architecture.

The MCP SDK creates one JSON input schema per registered tool from the tool's
typed callable. First-class tools therefore preserve:

- Per-command schemas and descriptions.
- MCP client discovery and argument validation.
- Command-specific output schemas and annotations.
- Reviewable registration and side-effect metadata.
- A direct mapping back to the CLI leaf and owning source files.

A generic facade would instead reduce the protocol-visible input to a command
string plus an opaque or oversized union of arguments. That weakens schema
validation, discoverability, side-effect review, and compatibility analysis.

Registration is organized per command hierarchy so command-specific contracts
remain reviewable without being hidden behind a generic tool.

### Command inventory

The CLI leaf inventory at the time this design was established is:

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

`mcp` is excluded because it starts the local stdio server. Every other
available leaf maps to a first-class tool using the naming rule above. A leaf
that is unavailable or excluded must still have an explicit hierarchy-owned
inventory record and reason.

This list documents the command namespaces; it is not a registration source.
The hierarchy-owned inventory and its parity tests are authoritative.

Metadata-only inventory or describe tools may exist for diagnostics. They do
not replace first-class operation tools. A generic execution tool is not part
of this architecture.

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
- Shared operation and phase modules follow
  [the shared naming rules](shared.md#naming-and-layout).
- Tests mirror these names under `tests/specify_cli/`.

Do not create a top-level MCP mirror of the entire CLI tree under
`mcp_server/commands/`. That would separate command contracts from their
owning domains and make unrelated command hierarchies depend on a central
package.

Do not add `_mcp.py` merely for symmetry. A package with one small tool may
register it through an existing focused registration module. Create `_mcp.py`
when the hierarchy needs an explicit list of several tools, shared adapter
helpers, or inventory dispositions.

## Registration and explicit inventory

Registration remains explicit at each command-group boundary.

For a group such as `artifact`:

1. `artifacts/_mcp.py` lists every `artifact.*` CLI leaf.
2. Each leaf has exactly one inventory record.
3. Available records import and register their `mcp_<name>.py` adapter.
4. Unavailable and excluded records state a reason.
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
disposition
disposition_reason
capabilities
network_access
```

The static disposition values are:

- `available`: implemented and registered as a first-class tool.
- `unavailable`: the logical operation is known but cannot be offered in the
  current distribution or platform; the record states the concrete reason.
- `excluded`: the command is intentionally not an MCP operation.

Every CLI leaf must appear exactly once. The inventory parity test fails for a
missing leaf, duplicate logical operation, duplicate tool name, stale CLI
path, or unexplained exclusion.

### Permanent and conditional exclusions

`specify mcp` is permanently excluded because it starts the local stdio server;
an MCP tool that starts another MCP server would be recursive infrastructure,
not an application operation.

Other commands are not excluded merely because they mutate state. Their
side effects are declared so MCP hosts and clients can make informed exposure
and confirmation decisions. For example:

- `self.upgrade` has static disposition `available` when its first-class tool
  is implemented and declares local reads, execution, and self-modification.
- `event.run`, `workflow.run`, and `workflow.resume` are execution operations
  that may also persist project state.
- `init`, add/remove/update commands, and configuration changes are
  project-write operations, with execution and other independent
  capabilities declared when their paths require them.
- `check` launches installed host tools to inspect their versions, so it
  requires execution capability even though it does not persist changes.
- A command that still depends on prompts, writes directly through its Typer
  handler, or lacks a typed result must not be marked `available`.

Unavailability and exclusion are reviewable architecture decisions, not silent
omissions.

## MCP contract projection

Shared request, outcome, warning, error, validation, and contract-version rules
are defined by
[Shared Command Application Architecture](shared.md#typed-request-contract).
The MCP adapter projects that contract onto MCP:

- Its input schema is command-specific and maps into the shared typed request.
- It performs protocol/schema validation but no state-dependent semantic work.
- It projects the operation's side-effect and network metadata into standard
  MCP annotations while the hierarchy-owned inventory retains the exact
  declarations.
- It maps the shared result and warnings into command-specific structured
  content.
- It maps expected shared errors into MCP tool errors without adding
  success-shaped fallbacks.

MCP protocol envelopes do not force a universal application result envelope.
The command/domain hierarchy continues to own the semantic result shape.
The hierarchy-owned inventory records `contract_version` for compatibility and
parity tests, but the local MCP protocol does not add a custom version field to
tools or results.
Unexpected exceptions become sanitized `internal_error` tool failures and are
logged only through the MCP diagnostic channel.

## Project directory and execution environment

Project-scoped MCP tools accept an optional project directory when their use
case needs one. If omitted, project discovery starts from the server launch
working directory, matching normal CLI behavior. The adapter maps that explicit
path into the shared request. The shared operation resolves it through the same
domain helper used by CLI and produces the same semantic errors.

The adapter and shared operation follow these rules:

- Do not call `os.chdir()` for an MCP request. A long-lived server may process
  concurrent or sequential calls with different project contexts.
- Pass the resolved project or target path explicitly through operation phases.
- Use the same shared Python/domain helpers as CLI for distribution metadata,
  bundled assets, project files, and other application behavior.
- Do not infer the project from an unrelated server process state after the
  invocation begins.

`init` is a special project-creation operation: its request identifies the
target directory rather than an existing project root.

Local stdio runs with the operating-system permissions of the server process,
just as the CLI runs with its process user's permissions. The command
architecture does not claim to provide a per-operation filesystem sandbox. A
host that needs confinement runs the MCP server inside an OS sandbox, container,
or restricted account.

## Non-interactive behavior

MCP operations are always non-interactive:

- They never read stdin.
- They never open arrow-key selectors or terminal confirmations.
- They never wait for an answer that is not represented in the request.
- A safe documented default may be applied only when the CLI operation uses
  the same non-interactive default.
- If no safe default exists, return a structured `input_required` or
  `confirmation_required` error explaining which field must be supplied.

Machine mode is not consent. Starting MCP, using `--json` or
`--non-interactive`, or receiving a host confirmation does not imply:

- `force=true`.
- Trust of an external URL or downloaded executable content.
- Permission to overwrite user-modified files.
- Permission to execute behavior that the caller did not explicitly request.

The caller must explicitly invoke an execution operation, supply any
command-specific consent fields, and satisfy the shared operation's semantic
validation. MCP annotations and host UI are advisory; they do not substitute
for required request values.

## Capability and network metadata

Operations declare capabilities according to
[the shared capability contract](shared.md#capability-declarations). These are
cumulative descriptions, not a highest-risk hierarchy. Examples:

```text
version       -> {local-read}
check         -> {local-read, execution}
workflow.run  -> {local-read, project-write, execution}
self.upgrade  -> {local-read, execution, self-modifying}
```

`read-only` is a derived description, not a declared capability. A
request is read-only only when it requires no `project-write`, `execution`, or
`self-modifying` capability. An operation that launches a binary is therefore
not read-only even if it does not persist changes.

Network access is an independent declaration: `none`, `optional`, or
`required`. A read-only search may use the network, while a project-write
operation may be fully offline.

The hierarchy-owned inventory retains the exact capability set and network
state for review and parity tests. Standard MCP `ToolAnnotations` are hints,
not a lossless capability contract:

- `readOnlyHint` is true only when the operation has no `project-write`,
  `execution`, or `self-modifying` capability.
- `destructiveHint` is omitted when `readOnlyHint` is true. Otherwise it is
  true when the operation may overwrite, delete, replace, or reconfigure
  existing state, and false only for additive updates.
- `idempotentHint` is true only when the operation contract guarantees that
  repeated calls with the same arguments have no additional effect.
- `openWorldHint` is true when network access is `optional` or `required`, or
  when execution may interact with external entities not bounded to the
  process, installation, or selected project.

The latter three hints depend on the full operation contract and are not
derived from the capability set alone. Exact capability names and the
three-state network declaration remain architecture and inventory metadata,
not protocol fields. This architecture does not require a custom `_meta`
contract or inventory tool.

The stdio server does not implement an allow/deny policy engine or
request-specific availability state. An MCP host or client may use standard
annotations to inform visibility or confirmation, but the hints are not an
access-control boundary.

The server still enforces semantic request requirements such as `force`,
external-source trust, and command-specific confirmation fields because those
belong to the shared operation contract.

`execution` declares that an operation may launch a child process. That child
runs with the MCP server process user's privileges unless the host externally
sandboxes the server. Setting cwd inside a project is not a security boundary,
and this command architecture does not claim otherwise.

## Trust, confirmation, and network responsibilities

The shared operation owns the semantic rule that an action requires trust or
confirmation. The adapters own how explicit consent enters the request.

- External URL installation remains default-deny without an explicit trust
  field.
- A non-empty target directory remains protected without explicit overwrite
  consent.
- Catalog discovery permission does not imply install permission.
- Network availability does not imply trust in arbitrary returned content.
- Redirect, digest, source, and compatibility validation remain domain
  behavior, shared by both adapters.
- Transport authentication does not replace semantic consent.

Network calls use bounded connect/read timeouts. Operations do not silently
switch from offline to online behavior. When a request supports offline
behavior, the input states it explicitly or uses the same documented default
as the CLI.

## Timeouts, cancellation, stdin, and bounded output

The MCP client owns its request deadline. If it no longer wants the result, it
sends `notifications/cancelled`. The stdio adapter handles that notification
and response-size enforcement; it does not create or own the client deadline.
Operations expose focused cancellation support only when their behavior can
cooperate with it.

- Subprocesses and network calls receive explicit server-side timeouts.
- A complex operation may accept a focused cancellation signal or
  operation-owned timeout; there is no universal invocation context.
- Transactional mutations roll back or report partial state according to
  their domain contract.
- After client cancellation, the server stops work and sends no tool result or
  tool error for that request.
- A server-enforced timeout while the request remains active returns a
  structured timeout error, never a successful empty result.
- No operation reads stdin or inherits an interactive child stdin.
- Captured stdout/stderr and diagnostic details are size-bounded.
- Potentially large lists use command-owned limits or pagination.
- Truncation is explicit and includes a continuation cursor or a clear
  `truncated` marker; it is never silent.
- MCP response-size enforcement belongs to the adapter; pagination semantics
  belong to the command hierarchy.

## Local stdio server boundary

`specify_cli/mcp_server/` owns server composition and stdio protocol hosting,
not command behavior.

The MCP server runs locally over stdio because its operations act on the local
project, Specify installation, filesystem, and host tools:

- Stdout is reserved for MCP protocol frames.
- Logs and diagnostics use stderr or the SDK's logging channel.
- Startup banners, Rich rendering, and CLI warnings never enter stdout.
- The server uses the launch process user's local permissions.

An illustrative infrastructure layout is:

```text
src/specify_cli/mcp_server/
├── __init__.py
├── server.py
├── registry.py
└── stdio.py
```

Create only the modules justified by implemented behavior. The layout defines
an architectural boundary, not a requirement to add empty files.

## Testing structure

Shared operation, CLI adapter, and parity coverage follows
[the shared testing structure](shared.md#testing-structure) and
[the CLI test structure](cli.md#test-structure). MCP adds the following layers.

### MCP adapter tests

- Verify tool name, description, annotations, and exact input/output schemas.
- Verify mapping to the shared operation request and outcome.
- Verify structured warnings and tool errors.
- Verify trust failures, server-enforced timeout errors, client cancellation
  without a response, and output-budget failures.
- Verify project-directory mapping and operation dispatch without `os.chdir()`.
- Verify standard tool annotations follow the conservative mapping and the
  inventory retains exact capability and network declarations.

### Inventory tests

- Walk the actual CLI command tree and require one MCP inventory disposition
  for every leaf.
- Reject duplicate operation IDs and MCP tool names.
- Require reasons for every unavailable or excluded command.
- Verify available tools are registered by the owning hierarchy.
- Verify inventory capability and network metadata match the shared operation
  descriptors.
- Preserve total pytest collection when tests move, as required by the CLI
  architecture.

### Protocol tests

- Keep an in-memory MCP registration and dispatch test.
- Keep a real stdio initialize/list/call test with protocol-pure stdout.
- Verify `notifications/cancelled` stops cooperative work without a response.
- Test malformed input, unavailable tools, internal failure sanitization, and
  output bounds as negative cases.

Behavioral changes follow
[Testing deterministic behavior](../CONTRIBUTING.md#testing-deterministic-behavior):
positive and negative evidence is required, and bug fixes need before-and-after
regression evidence.

## Representative operation layouts

### `version`: simple, process-scoped read

```text
src/specify_cli/
├── _operation_version.py
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
capabilities: [local-read]
network_access: none
```

`_operation_version.py` owns typed version collection and `VersionResult`,
using the normal shared version/domain helper. `command_version.py` renders the
panel, feature text, or established JSON object. `mcp_version.py` returns the
same result fields as structured content. No adapter starts a child process.

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
capabilities: [local-read]
network_access: none
```

The request contains an optional project directory. The shared operation
resolves and validates that path, uses `ArtifactCatalog`, and returns typed
artifact rows. The CLI adapter preserves its JSON stream contract; the MCP
adapter exposes the rows through its output schema and never captures CLI
stdout. Large results use explicit operation limits or pagination rather than
silent truncation.

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
capabilities: [local-read, project-write, execution]
network_access: optional
```

The request explicitly carries the target, integration, script type, optional
preset/extensions, `force`, and external-URL trust decision. The MCP adapter
never prompts and never turns its machine context into force or trust. The
shared operation validates inputs, builds a plan, applies transactional
changes, and returns created/updated paths plus structured warnings. The CLI
adapter may gather interactive choices before constructing the same request.
Bundled templates and scripts use the same shared asset helpers as CLI.

If the target is non-empty and `force` is false, both adapters receive the same
semantic confirmation-required failure. The CLI may respond by prompting and
retrying with explicit consent; the MCP tool returns the structured error and
requires a new call with `force=true`.

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
- Treating MCP tool annotations or host confirmation as semantic `force`,
  trust, or destructive consent.
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
- Letting stdio protocol concerns leak into command contracts.

## Review checklist

For a new or migrated MCP operation:

- [ ] The CLI leaf and MCP tool map to one logical operation ID.
- [ ] Both adapters dispatch into the same typed shared implementation.
- [ ] The MCP tool is first-class and has a command-specific schema.
- [ ] The tool name and source layout mirror the CLI path.
- [ ] The owning command hierarchy declares registration and inventory.
- [ ] Availability, capabilities, network access, and inventory contract
      version are explicit.
- [ ] Non-interactive behavior does not imply force, trust, or consent.
- [ ] Project paths are normalized and passed explicitly without `os.chdir()`.
- [ ] Timeouts, cancellation, stdin, and output bounds are handled.
- [ ] Existing CLI human and JSON behavior remains compatible.
- [ ] Operation, CLI adapter, MCP adapter, parity, and protocol tests cover
      positive and negative behavior.
- [ ] Stdio remains protocol-pure, and command behavior stays outside server
      hosting.
- [ ] No command behavior was added to central MCP infrastructure.
