# Workflow functions

Workflow functions are project-installed Python callables exposed as pipe
filters in workflow expressions. They are installed under
`.specify/workflows/functions/<id>/` and consist of a `function.yml` manifest
and an `__init__.py` module.

## Install and manage functions

```bash
specify workflow function add text --dev ./workflow-functions/text
specify workflow function list
specify workflow function list --json
specify workflow function remove text
```

A package can also be installed from an archive URL:

```bash
specify workflow function add text --from https://example.test/text.zip
```

Exactly one of `--dev` and `--from` is required. `--force` replaces an existing
package with the same package ID; it cannot replace a function export owned by
another package.

Installation follows the same rules as custom step packages: files are validated
and copied through a private staging directory, symlinks and unsupported file
types are rejected, `.git`, `__pycache__` and `.DS_Store` are not copied, and a
package may contain at most 512 entries, 50 MiB and 32 directory levels. A
`--from` install shows an untrusted-source prompt with the URL before any
request, resolves GitHub release asset URLs, and requires the URL, final URL and
`Content-Type` to agree on the archive format.

`remove` deletes the package directory and its registry entry under the same
project lock as installation. A directory with no registry entry is removed with
a warning; if the directory cannot be deleted, the registry entry is restored.

`list` reads the persisted registry only. It does not import package code and
reports each export's generic usage form. A package that was copied into
`.specify/workflows/functions/` by hand is loaded when a workflow runs but is not
listed, because it has no registry entry.

## Manifest

```yaml
id: text
name: Text helpers
version: 1.0.0
description: Small text transformations.
functions:
  - name: trim
    handler: trim
    min_args: 0
    max_args: 0
    description: Remove surrounding whitespace.
```

Package IDs use the same safe path-component validation as custom workflow
steps. Export names are lowercase identifiers (`a-z`, `0-9`, and `_`) and must
be unique in a package. `min_args` and `max_args` are integers with
`0 <= min_args <= max_args <= 16`; they count arguments after the value being
piped. The defaults are zero. A
bare filter is accepted only when `min_args` is zero. Parenthesized calls must
contain at least one argument and must be within the declared bounds.

The handler is called as `handler(value, *args)`. For example:

```python

def trim(value):
    return value.strip()


def surround(value, left, right):
    return f"{left}{value}{right}"
```

```yaml
- id: normalize
  type: shell
  strict: true
  env:
    VALUE: "{{ inputs.value | trim }}"
  run: 'printf "%s\\n" "$VALUE"'
```

## Loading and trust

Installing validates and copies package files but does not import them. Running,
resuming, adding, or updating a workflow loads installed function modules before
workflow validation. Loading executes Python code, so review packages and
install only from sources you trust. Archive downloads use the same HTTPS and
loopback-HTTP restrictions as other executable workflow packages.

Function names share a flat namespace with built-in and other installed
filters. Installation rejects a name that is a built-in filter or is already
provided by another package, whether that package is in the registry or only
present on disk (the error says "found on disk, not in the registry" in that
case). Runtime loading also fails on a collision, naming every colliding
function and both sources, if packages were copied manually or a new Spec Kit
release introduces a conflicting built-in. The collision check happens before
any package code is imported. Built-in filters are never replaced. If the
functions directory itself cannot be read, the command reports the error and
exits with code 1 (a failed payload with `--json`). Packages with an invalid or
unreadable manifest, or whose module fails to import, are skipped, so their
filters may later be reported as unknown.

The filter registry is process-global while a workflow is loaded. A project
reload replaces the previous project's custom filters. Function handlers must
be stateless and thread-safe because fan-out steps can evaluate expressions
concurrently. As with other workflow side effects, an interruption before a
resume checkpoint can cause an operation to run again; resume provides
at-least-once rather than exactly-once execution.

Custom return values use the existing expression and step-output handling; no
additional function-specific type or JSON whitelist is applied. Exceptions
raised by a handler are normalized as `ValueError` messages prefixed with the
function name, while `BaseException` subclasses are not intercepted.
