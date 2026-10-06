# Shared Command Application Architecture

This document defines the application layer beneath Specify delivery adapters.
A logical operation has one shared implementation. The CLI, MCP, and any future
delivery surface translate their inputs into that operation and translate its
outcome into their own output and error conventions.

[Specify CLI Command Architecture](cli.md) defines the Typer/terminal adapter.
[Specify MCP Command Architecture](mcp.md) defines MCP tool exposure, policy,
and transport. Neither adapter document owns application behavior.

## Design goals

The shared layer optimizes for:

- **One behavior:** every adapter for a logical operation invokes the same
  semantic implementation.
- **Adapter independence:** adapters own invocation and reporting without
  calling or parsing one another.
- **Typed contracts:** requests, results, warnings, and expected errors are
  explicit and testable.
- **Lean boundaries:** shared code contains application behavior, not a
  universal runtime, service locator, transport abstraction, or policy engine.
- **Explicit paths:** project and target paths are passed as operation inputs
  rather than established through mutable process cwd.
- **Reviewable ownership:** application behavior has a predictable source and
  mirrored tests.

## Non-goals

The shared layer does not:

- Standardize how adapters spell arguments, display progress, or format human
  output.
- Require byte-identical CLI JSON and MCP protocol envelopes.
- Turn operations into a universal string-based command dispatcher.
- Replace focused domain modules with a central execution engine.
- Define CLI prompting, MCP authorization, transport authentication, or host
  sandboxing.
- Require a context object or extra module when ordinary typed parameters and
  an existing domain module are sufficient.

## One logical operation, multiple adapters

Adapters are peers above one application operation:

```text
CLI arguments/options ─┐
MCP tool input JSON ───┼─> typed request -> shared operation -> typed outcome
future adapter input ──┘

typed outcome ─────────┬─> CLI text, JSON, warnings, and exit status
                      ├─> MCP structured content or tool error
                      └─> future adapter representation
```

The shared operation is the semantic source of truth. Equivalent requests
produce equivalent results, warnings, expected failures, and side effects.

An adapter must not:

- Invoke another adapter.
- Parse another adapter's output.
- Reimplement semantic validation or application orchestration.
- Add semantic defaults, trust, consent, or side effects absent from the
  shared request.

## Ownership boundaries

| Concern | Owner |
| --- | --- |
| Logical operation ID and contract version | Relevant command/domain hierarchy |
| Typed request, result, warning, and error models | Relevant command/domain hierarchy |
| Semantic validation, orchestration, and side effects | Shared operation and domain modules |
| Operation-private phases | `_operation_<name>_<phase>.py` |
| Project and target path validation | Shared operation or focused domain helper |
| Bundled assets and distribution metadata | Existing shared/domain resource helpers |
| CLI syntax, prompting, rendering, JSON, and exit codes | CLI adapter |
| MCP schemas, policy enforcement, annotations, and tool errors | MCP adapter |
| MCP server lifecycle and transport | MCP infrastructure |

Domain behavior that already has a focused Typer-free owner remains there. A
dedicated `_operation_<name>.py` coordinates domain calls only when an adapter
would otherwise own semantic validation or orchestration.

## Logical operation identity

The operation ID follows the CLI leaf path without the leading `specify`:

```text
specify version                -> version
specify artifact list          -> artifact.list
specify extension set-priority -> extension.set-priority
```

The ID names application behavior, not a transport endpoint. Adapter identities
derive from it:

```text
operation: artifact.list
CLI:       specify artifact list
MCP:       specify_artifact_list
```

An operation descriptor declares the metadata shared by adapters:

```text
operation_id
contract_version
request_type
result_type
warning_types
error_types
capabilities
network_access
project_scope
default_timeout
```

Adapter registration extends this metadata without moving command-specific
contracts into central infrastructure.

## Naming and layout

Use an existing focused domain module when it already provides the correct
Typer-free application entry point. Otherwise use:

```text
_operation_<name>.py
```

For example:

```text
src/specify_cli/
├── _operation_version.py
├── command_version.py
└── mcp_version.py
```

A simple operation stays in one operation or domain module. Do not split it for
symmetry.

When a complex operation has cohesive phases with distinct invariants, failure
behavior, rollback, or tests, use:

```text
_operation_<name>.py
_operation_<name>_<phase>.py
```

For example:

```text
src/specify_cli/
├── _operation_init.py
├── _operation_init_validation.py
├── _operation_init_plan.py
├── _operation_init_apply.py
├── _operation_init_finalize.py
├── command_init.py
└── mcp_init.py
```

`_operation_init.py` is the shared application entry point. Phase modules do
not register commands or tools.

Adapter-only phases retain adapter-specific names:

```text
_command_<name>_<phase>.py
_mcp_<name>_<phase>.py
```

If more than one adapter needs a phase, it belongs in the shared operation or
domain layer.

Nested directories continue to represent real command namespaces or bounded
subdomains. Do not create an operation-phase directory that implies a
nonexistent CLI namespace.

## Typed request contract

The relevant command/domain hierarchy owns a typed request model. It:

- Uses semantic names rather than CLI flag or MCP field implementation names.
- Distinguishes omitted values from explicit false, empty, or null values.
- Rejects unknown fields.
- Represents paths, enums, identifiers, and bounded collections explicitly.
- Carries explicit consent such as `force` or external-source trust only when
  the operation defines that behavior.

Adapters parse their transport input and map it into this request. Semantic
validation remains in the shared operation.

## Invocation lifecycle

Invocation follows a small, explicit sequence:

1. The adapter parses and schema-validates its input.
2. The shared operation performs pure request validation and computes any
   request-specific capabilities or network requirements.
3. An adapter that enforces policy, such as MCP, authorizes those requirements
   before invoking behavior that uses them.
4. The shared operation performs state-dependent validation, orchestration, and
   side effects.
5. The operation returns its typed outcome for adapter-specific reporting.

The CLI normally proceeds under the invoking user's operating-system
permissions. MCP applies its configured policy before dispatch. Policy
differences may reject an invocation, but they do not create a second
implementation of the operation.

## Project and working-directory handling

Project-scoped request types carry an explicit project directory, or an
explicit value derived by the adapter from its launch working directory:

- CLI defaults to the cwd captured when the command invocation begins.
- Local stdio MCP defaults to the cwd captured when the server starts.
- A caller may supply a project or target directory when the command supports
  it.

The shared operation or focused domain helper resolves and validates the path,
including `.specify` project checks where required. It passes the resolved path
through domain calls and operation phases.

Shared code must not call `os.chdir()` to establish request state. A long-lived
MCP server may handle calls for different projects, and process-wide cwd would
couple otherwise independent invocations.

Package metadata and first-party bundled assets use normal shared Python/domain
helpers such as `importlib.metadata`, `importlib.resources`, or the established
asset resolver. They are not caller-selected project paths and require no
universal application-resource abstraction.

This architecture does not claim that an in-process path check is an operating
system sandbox. CLI and local stdio MCP run with the permissions of their
process user. A deployment that requires filesystem confinement must sandbox
the MCP server process or transport host; command behavior does not implement a
second virtual filesystem.

## Typed outcome contract

The operation returns a typed outcome containing:

- The command-specific result.
- Zero or more structured warnings.
- Command-relevant execution metadata such as changed paths or transaction
  status.

Warnings have a stable code, human-readable message, and typed details. The
operation does not print them. Each adapter decides how its surface represents
them.

There is no mandatory universal success envelope. Command-specific output
types remain owned by the command/domain hierarchy.

## Structured errors

Expected failures use a transport-neutral operation error:

```text
code
message
details
retryable
```

The operation hierarchy owns error codes and detail schemas. Adapters map them:

- CLI maps them to human or JSON failure output and established exit codes.
- MCP maps them to structured tool errors.

Shared errors contain no CLI exit code, Rich markup, MCP content block, HTTP
status, traceback, raw subprocess output, or secret.

Unexpected exceptions are normalized by the adapter boundary to a sanitized
internal error and logged only through the adapter's diagnostic channel.

## Contract versions and machine compatibility

The operation descriptor is the source of truth for `contract_version`. The
version covers the semantic request, result, warning, and expected-error
contract, not package or transport versions.

Both adapters conform to that declared version:

- MCP exposes it through tool or inventory metadata.
- CLI contract tests reference it while preserving established human and JSON
  output. A version field is not injected into an existing JSON result unless
  that result contract already defines one.

Contract evolution follows these rules:

- Backward-compatible optional fields and warning codes may retain the current
  major version.
- Removing, renaming, or changing the meaning of an input, output, warning, or
  error requires a new major version and explicit compatibility strategy.
- Adapter-only presentation changes do not change the operation contract
  version.
- Tests lock established adapter schemas and machine-output shapes to the
  declared contract.

## Capability declarations

Capabilities are cumulative operation metadata:

| Capability | Meaning |
| --- | --- |
| `local-read` | Reads local process, installation, host, or project state |
| `project-write` | Creates or changes project or target files/configuration |
| `execution` | Starts host tools, workflows, hooks, agents, or processes |
| `self-modifying` | Changes the Specify installation or machine-level state |

The descriptor declares the conservative union an operation may require.
`required_capabilities(request)` may compute an exact subset only from the
validated request and static metadata, without performing I/O.

`execution` means the operation may start a child process with the MCP server
process user's privileges. It is not a filesystem sandbox. A host that needs
stronger isolation runs the server inside an appropriate OS sandbox, container,
or restricted account.

Network access is declared separately as `none`, `optional`, or `required`.
Trust and destructive consent remain explicit request values, not implied
capabilities.

## Trust and consent

The shared operation owns semantic rules that require explicit request values:

- Trusting an external URL or downloaded executable content.
- Overwriting a non-empty target or user-modified file.
- Selecting a workflow, hook, installer, or other executable operation and
  supplying any confirmation fields that operation defines.
- Performing a self-modifying action.

The CLI may prompt before constructing or retrying a request. MCP never prompts
and returns a structured input- or confirmation-required error when the
request lacks required consent.

Machine-readable mode, non-interactive mode, transport authentication, or an
authorized capability never implies `force`, trust, or destructive consent.

## Timeouts, cancellation, and bounded output

Do not force every operation through a universal runtime object.

- The MCP adapter owns protocol deadlines, cancellation, and response-size
  enforcement.
- A command that can cooperatively cancel or accept a deadline exposes a
  focused typed parameter or operation dependency for that behavior.
- Subprocess and network helpers receive explicit timeouts from the operation
  that invokes them.
- Potentially large commands own pagination or limit fields in their request
  and result contracts.
- Truncation is explicit and never returned as a successful complete result.

CLI and MCP adapters may choose different presentation limits, but neither may
change the semantic result silently.

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

Operation tests cover:

- Valid requests and intended results.
- Pure and state-dependent validation failures.
- Warnings and structured errors.
- Side effects, rollback, trust, consent, network behavior, and execution.
- Explicit project/target paths without process-wide cwd changes.
- Domain behavior without Typer, Rich, MCP, or transport assertions.

Adapter tests cover invocation mapping and adapter-specific reporting and
policy.

Parity tests invoke CLI and MCP adapters against the same operation fixture and
compare semantic request, result, warning, error, and side-effect behavior.
Parity does not require byte-identical presentation.

Behavioral changes follow
[Testing deterministic behavior](../CONTRIBUTING.md#testing-deterministic-behavior):
positive and negative evidence is required, and bug fixes need before-and-after
regression evidence.

## Anti-patterns

Avoid:

- Calling a Typer handler from MCP or an MCP tool from CLI.
- Invoking the human CLI as application dispatch.
- Parsing Rich, stdout, stderr, or protocol output to recover domain results.
- Duplicating validation or orchestration in adapters.
- Adding adapter concepts to request, outcome, warning, or error models.
- Hiding operations behind a central string dispatcher or service locator.
- Adding a universal invocation context, filesystem abstraction, or resource
  provider when focused Python parameters and existing helpers suffice.
- Letting adapters infer force, trust, consent, or extra capabilities.
- Reading mutable process cwd instead of passing an explicit path.
- Splitting simple operations or creating phase modules solely for symmetry.

## Review checklist

For an operation with CLI and MCP adapters:

- [ ] One logical operation ID identifies both surfaces.
- [ ] Both adapters map into the same typed request and shared entry point.
- [ ] Semantic validation, orchestration, and side effects are below adapters.
- [ ] Adapter modules contain only invocation, mapping, presentation, and
      adapter-specific concerns.
- [ ] Shared request, outcome, warning, and error types are transport-neutral.
- [ ] Project and target paths are explicit; shared code does not call
      `os.chdir()`.
- [ ] MCP policy uses operation metadata without moving policy into shared
      domain behavior.
- [ ] CLI exit codes and MCP tool errors remain adapter-owned.
- [ ] Contract-version ownership and compatibility tests are explicit.
- [ ] Operation tests and adapter parity tests cover positive and negative
      behavior.
- [ ] No adapter invokes or parses another adapter.
