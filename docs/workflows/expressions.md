# Workflow expressions

Steps can reference inputs and previous step outputs using `{{ expression }}` syntax:

| Namespace                      | Description                          |
| ------------------------------ | ------------------------------------ |
| `inputs.spec`                  | Workflow input values                |
| `steps.specify.output.file`    | Output from a previous step          |
| `item`                         | Current item in a fan-out iteration  |
| `fan_in`                       | Fan-in aggregation context |
| `context.run_id`               | Current workflow run ID              |
| `context.workflow_dir`         | Resolved absolute path to the workflow source directory. Empty string for string-loaded workflows. |

Available filters: `default`, `join`, `contains`, `map`, `from_json`, `to_json`, `upper`, `lower`, `split`, `length`.

## Custom filters (Workflow Functions)

Projects can install Python callables as pipe filters. See
[Workflow functions](functions.md) for package and CLI details.

```yaml
# After installing a package that exports trim:
message: "{{ inputs.message | trim | upper }}"
```

A function receives the piped value followed by the explicit filter
arguments. Manifest `min_args` and `max_args` bounds are enforced when the
expression is evaluated. Filter names and argument counts in wrapped
`{{ ... }}` expressions are not checked during workflow validation. Bare form is available for zero-minimum functions;
parenthesized calls contain one or more arguments. Function names share a flat
namespace with built-in filters and other installed packages. Collisions are
errors and built-ins are never shadowed.

Function packages contain executable Python and are imported before workflow
validation. Review package source before installing it. Handlers should be
stateless and thread-safe because fan-out can evaluate filters concurrently.
Function failures use the normal expression-error path, with the function name
prefixed to the exception; return values use the existing expression consumer
rules rather than a separate function-specific type contract. As with other
workflow side effects, an interruption before a resume checkpoint can repeat a
handler, so resume is at-least-once.

## Syntax

| Form | Example |
| --- | --- |
| Dot-path lookup | `{{ inputs.name }}`, `{{ steps.test.output.exit_code }}` |
| Literals | Strings, numbers, `true`, `false`, `none`/`null`, and lists such as `[1, 2]` |
| Comparisons | `==`, `!=`, `>`, `<`, `>=`, `<=` |
| Boolean logic | `and`, `or`, `not` |
| Membership | `in`, `not in` |
| Filters | `{{ inputs.tags \| split(',') \| length }}` |

This is a dedicated expression language, not full Jinja2 or Python.

## Filters

| Filter   | Example                                    | Behavior                                                                                        |
| -------- | ------------------------------------------ | ----------------------------------------------------------------------------------------------- |
| `default`| `{{ val \| default('fb') }}`               | Fallback for `None` or an empty string                                                                  |
| `join`   | `{{ list \| join(', ') }}`                 | Join list elements into a string                                                                   |
| `contains`| `{{ text \| contains('sub') }}`           | Substring or membership check                                                                      |
| `map`    | `{{ list \| map('attr') }}`                | Extract an attribute from each item                                                                |
| `from_json`| `{{ out \| from_json }}`                 | Parse a JSON string into a typed value                                                             |
| `to_json`| `{{ obj \| to_json }}`                     | Serialize a value to a JSON string — the inverse of `from_json`; mapping keys must be strings |
| `upper`  | `{{ text \| upper }}`                      | Uppercase a string                                                                                 |
| `lower`  | `{{ text \| lower }}`                      | Lowercase a string                                                                                 |
| `split`  | `{{ csv \| split(',') }}`                  | Split a string on a separator into a list of strings                                               |
| `length` | `{{ items \| length }}`                    | Number of elements in a list, or characters in a string                                            |

`default` falls back only for `None` and the empty string. Other falsy values — `0`, `false`, `[]`, `{}` — are passed through unchanged, so `{{ count | default(10) }}` still yields `0` for a zero count. Falsy is not the same as empty here.

Notes on the newer filters:

- **Types are validated, not coerced.** `upper` and `lower` accept strings only, `split` requires both a string value and a non-empty string separator, and `length` accepts lists and strings but rejects mappings. Anything else raises a `ValueError` naming the problem. Coercion is deliberately not performed: a type mismatch nearly always means the workflow is wired to the wrong variable, and a coerced result would hide that. A filter given the wrong number of arguments (`| upper('x')`, `| split` with no separator, `| split(',', 1)`) is reported as a known filter misused, which is distinct from an entirely unknown filter name: a call carrying more than one argument falls through to that same unsupported-form error rather than being evaluated as a single expression. The older filters (`join`, `map`, `contains`) are more permissive and unchanged: `join` stringifies unsupported values and `map`/`contains` return fallbacks rather than raising.
- **`from_json` rejects non-JSON numeric constants.** Bare `NaN`, `Infinity`, and `-Infinity` raise a `ValueError` naming `from_json`, including inside objects and arrays. Quoted strings such as `"NaN"` remain valid JSON strings.
- **`to_json` output is deterministic.** Object keys are sorted and non-ASCII characters are left as-is rather than escaped, so the same value always serializes to the same bytes. That buys reproducibility only — it does **not** make the result safe to pass through a shell, because [interpolation adds no quoting or escaping](#interpolation-and-shell-safety). Do not interpolate unconstrained JSON into a `run` field.
- **`to_json` rejects non-finite floats.** `NaN`, `Infinity`, and `-Infinity` raise a `ValueError` naming `to_json` instead of serializing to bare tokens. None of the three is valid JSON, so emitting them would hand a standards-compliant downstream parser a string it must reject.
- **`to_json` requires string mapping keys.** JSON objects have string keys, so a mapping with any other key type — `{1: "a"}`, `{True: "a"}` — raises a `ValueError` naming the key type instead. Left to `json.dumps`, an integer key would be coerced to `"1"` and collide with an existing `"1"` key, while mixed key types would fail `sort_keys` with an ordering `TypeError` reported only as "not JSON-serializable".
- **Comparing filtered counts requires parentheses.** A filter chain cannot be an operand of an operator, so an unparenthesized trailing comparison such as `{{ inputs.items | length > 0 }}` raises an "ambiguous filter precedence" `ValueError`. Parenthesize the filtered operand to compare its result: `{{ (inputs.items | length) > 0 }}`. For a threshold of at least two:

  ```yaml
  condition: "{{ (inputs.items | length) >= 2 }}"
  ```

  For an emptiness check, use the filtered count's truthiness directly:

  ```yaml
  condition: "{{ inputs.items | length }}"   # 0 is False, any non-zero count is True
  ```

`and` and `or` return `true` or `false` and evaluate their right side only when the left side does not decide the result: `and` skips it when the left side is false, and `or` skips it when the left side is true. A condition can therefore guard a filter that would fail on an empty value. `{{ inputs.payload != '' and (inputs.payload | from_json | length) }}` is false for an empty optional `payload` instead of failing the run on invalid JSON. When the right side is evaluated, its errors still fail the run.

Operators bind from loosest to tightest as `or`, `and`, `not`, then the comparisons. All comparisons (`==`, `!=`, `>`, `<`, `>=`, `<=`, `in`, `not in`) share one level and are evaluated left to right; none has priority over another. `{{ a == b > 0 }}` therefore means `{{ (a == b) > 0 }}`. To combine comparisons, use parentheses or `and`/`or`.

The body of every `{{ }}` block must be a valid expression. Text that is not one, such as prose (`{{ some text }}`), a key with characters other than letters, digits, `_` and `-` (`{{ inputs.weird:key }}`), or arithmetic (`{{ count + 1 }}`), raises a `ValueError` naming the offending token. Numbers may be written as `5`, `-5`, `+5`, `1_000`, `0.5`, `.5`, `5.`, or `1.5e3`.

> **Compatibility:** Earlier releases could resolve an expression such as `{{ inputs.weird:key }}` when the key existed; this expression now fails at runtime. Rename keys you control (for example, `weird:key` to `weird_key`) and update their references. Quoted-key lookup is not supported. Workflow validation may not detect these expressions before execution.

Example:

```yaml
condition: "{{ steps.test.output.exit_code == 0 }}"
args: "{{ inputs.spec }}"
message: "{{ status | default('pending') }}"
tag_count: "{{ inputs.tags | split(',') | length }}"
shell_flag: "{{ inputs.branch | upper }}"
```

## Interpolation and shell safety

Expressions are resolved by **plain string substitution** — the value of `{{ ... }}` is spliced into the surrounding text exactly as-is, with no quoting or escaping added. That is convenient for building `args` and `message` strings, but it has an important consequence for `shell` steps: a `run` field is handed to the system shell (`/bin/sh -c` on POSIX), so any interpolated value is interpreted as **shell syntax**, not just data.

If an interpolated value can contain characters like `;`, `|`, `&`, `$( )`, backticks, or quotes, it can change or extend the command that actually runs. This matters most when the value is not fully under the workflow author's control:

- **Workflow `inputs.*`** — supplied by whoever runs the workflow.
- **A prior step's output**, e.g. `{{ steps.plan.output.stdout }}` — for a `command` or `prompt` step with [`capture: true`](../workflow-steps/types.md#capturing-command-and-prompt-output) this is **text produced by the AI agent**, which can in turn be influenced by files, tickets, or web content the agent read. Treat agent output as untrusted when it flows into a `shell` step.

There is **no shell-escaping filter** in the expression language and **no sandbox** around a `shell` step. Prefer [`strict: true`](../workflow-steps/types.md#shell-step) with `env` bindings to keep dynamic values out of shell source. Strict mode does not sanitise data, inspect commands, or prevent an authored script from interpreting data as code. Do not use `eval`, build another `sh -c` command from a variable, or pass untrusted values through shell startup variables such as `BASH_ENV`. On Windows, `cmd.exe` expansion of `%VALUE%` can introduce shell syntax; read untrusted values inside a program instead. On POSIX, quote variable expansions and use the target program's argument validation or `--` where appropriate to prevent option injection.

For compatibility, raw interpolation remains enabled when `strict` is omitted or `false`. Its injection risk remains unchanged. Keep values you cannot constrain out of `run` fields entirely. Scrutinise every non-strict `run` field that interpolates a value you do not control, and at minimum:

- **Constrain the value at the source with `enum`/an allowlist.** When `inputs.*` feeds a non-strict `run` field, restrict it to a fixed set of known-safe values so a caller cannot supply arbitrary shell text at all.

  ```yaml
  inputs:
    target:
      type: string
      enum: [staging, production]   # caller cannot inject arbitrary text
  ```

- **Keep unconstrained values out of `run`.** If a value cannot be constrained to an allowlist — most agent/`prompt` output — do not interpolate it into a `run` field. Branch on it with `if`/`switch` against fixed conditions, or act on it in a `command`/`prompt` step rather than a shell command built from it.
- **Quoting is not a security boundary.** Surrounding a substitution with quotes (`'{{ inputs.x }}'`) helps the shell treat a *trusted* value as a single argument and avoids word-splitting on spaces, but a value that itself contains the matching quote character can still break out and inject shell syntax. Quote for correctness on constrained values; never rely on quoting to make an *unconstrained* substitution safe.
- **Gates do not inspect the next step, and `message` is printed verbatim.** A `gate` step renders only its own `message`/`show_file` — it does not display, resolve, or sanitise the command that follows it, and approval never neutralises an injectable interpolation. Do **not** interpolate raw untrusted data into `message`: it is printed as-is with no control-character stripping, so agent or caller output could inject terminal/ANSI escapes that alter or hide the approval prompt. Keep `message` to trusted, constrained text, and surface untrusted material for review via `show_file` instead — its path and contents are control/ANSI-stripped before display.

A `shell` step is an arbitrary-command primitive by design; these practices reduce exposure and keep *which* command runs under the author's control, but they do not eliminate the risk of interpolating values you do not fully control.

## Runtime Context

`{{ context.* }}` exposes engine-managed runtime metadata for the
current run:

| Variable | Description |
|----------|-------------|
| `context.run_id` | The current workflow run id (the same value Spec Kit prints as `Run ID:` at the end of `workflow run`). Auto-generated runs are 8-character hex from `uuid4`; operator-supplied ids may be any alphanumeric string with hyphens or underscores. Empty string outside a run context. |
| `context.workflow_dir` | The resolved absolute path to the directory containing the workflow source file. For file-loaded workflows this is the parent directory of the YAML file; for installed-by-ID workflows it is the absolute path to the installation directory (e.g. `<project>/.specify/workflows/<id>/`); for string-loaded workflows it is an empty string. On resume the original source directory is preserved from the first execution. |

```yaml
# Stamp telemetry events with the run id for cross-system join.
- id: emit-event
  type: shell
  strict: true
  env:
    RUN_ID: "{{ context.run_id }}"
  run: 'printf ''{"run_id":"%s","event":"started"}\n'' "$RUN_ID" >> events.jsonl'

# Per-run scratch directory.
- id: prep-scratch
  type: shell
  strict: true
  env:
    RUN_ID: "{{ context.run_id }}"
  run: 'mkdir -p "/tmp/run-$RUN_ID"'

# Pass run id into a command for artifact metadata.
- id: tag-artifact
  command: speckit.specify
  input:
    args: "{{ context.run_id }}"

# Reference a sibling file shipped alongside the workflow definition.
- id: apply-config
  type: shell
  strict: true
  env:
    SOURCE_DIR: "{{ context.workflow_dir }}"
  run: 'cp "$SOURCE_DIR/defaults.yml" ./config.yml'
```

These shell examples use POSIX syntax. For portable scripts, read the
environment inside the called program.

## Typed values

A single expression (`{{ expr }}` by itself) returns its value without string conversion. Mixed templates (`prefix {{ expr }}`) return text; an embedded null becomes empty text. Use `to_json` when a structured value must cross a text boundary.

## See also

- [Workflow step reference](../workflow-steps/types.md)
- [Shell environment bindings](../workflow-steps/types.md#shell-step-environment-variables)
- [Input types](api.md#input-types)
