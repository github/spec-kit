# Developing presets

A preset packages custom document templates, agent instructions, and scripts
in a directory with a `preset.yml` manifest. Prefer a template contribution
when only the output structure changes; override a command when the process
itself needs different instructions. For a one-off project change, a
project-local override may be simpler than a distributable preset.

## Start from the scaffold

Copy the repository's
[preset scaffold](https://github.com/github/spec-kit/tree/main/presets/scaffold)
to a directory you control:

```bash
cp -r presets/scaffold my-preset
```

Edit its ID, name, version, description, required Spec Kit version, and
contributions. Remove unused examples, including example extension command
overrides, rather than shipping them accidentally.

A typical package contains:

```text
my-preset/
  preset.yml
  README.md
  LICENSE
  CHANGELOG.md
  .presetignore
  templates/
    spec-addendum.md
  commands/
    speckit.specify.md
  scripts/
    my-helper.sh
```

Only include directories used by your preset. The manifest's
`provides.templates` list contains contributions of all three types, not
just document templates. The `file` field can point to a non-conventional
path; use `name` to identify the logical artifact being customized.

## Declare contributions

For example, append a traceability section to the effective specification
template:

```yaml
schema_version: "1.0"

preset:
  id: "team-traceability"
  name: "Team Traceability"
  version: "1.0.0"
  description: "Adds team traceability requirements to specifications"
  author: "Example Team"
  repository: "https://github.com/example/team-traceability"
  license: "MIT"

requires:
  speckit_version: ">=0.9.0"

provides:
  templates:
    - type: "template"
      name: "spec-template"
      file: "templates/spec-addendum.md"
      description: "Traceability section"
      strategy: "append"

tags:
  - "traceability"
  - "governance"
```

Keep headings clear and placeholders explicit. If a command references a
template section, ensure the effective template actually contains it.
Declare only contributions you need so the preset composes with others.

For `wrap`, the content file must contain `{CORE_TEMPLATE}` for templates
and commands, or `$CORE_SCRIPT` for scripts. These placeholders stand for the
resolved lower-priority content, not necessarily unmodified core content.
An append, prepend, or wrap contribution needs a lower `replace` base;
a new self-contained command normally uses `replace`.

Declare extension dependencies in `preset.yml` when the preset relies on
extension capabilities. A namespace alone does not establish a dependency
or suppress registration. See the API reference for warning behavior and
optional/version-constrained dependencies.

## Exclude development files with `.presetignore`

Place a UTF-8 `.presetignore`, with or without a byte-order mark, beside
`preset.yml` in the source root:

```gitignore
.git/
.idea/
tests/
```

Filtering applies to copied local directories and extracted archives,
including replacements installed by `preset update`. Without this file,
all source files are copied as before. `.gitignore` is not used for
installation filtering, and there are no implicit development-file
exclusions.

Patterns use Git-style matching and normalization, as with
`.extensionignore`:

- Use one pattern per line; blank lines and `#` comments are ignored.
- `*` and `?` do not cross directory boundaries; `**` can cross them.
- A trailing `/` matches directories only. A leading `/`, or a `/` elsewhere
  except at the end, anchors a pattern to the source root. Patterns without
  such a slash match names at any depth.
- A later `!` pattern re-includes a match. Excluded directories are not
  traversed, so a child cannot be re-included while its parent is excluded.
- Whitespace is trimmed and backslashes are normalized to `/`. Use UTF-8
  for non-ASCII names.

To keep only `docs/api.md` inside `docs/`, exclude the contents rather than
the directory:

```gitignore
docs/*
!docs/api.md
```

Using `docs/`, then `!docs/` and `!docs/api.md`, re-includes all files under
`docs/` unless another rule excludes them.

Only the source root's `.presetignore` adds rules; nested ignore files are
not evaluated. If a root ignore file exists, files named `.presetignore` at
any depth are excluded even when negated. Without a root ignore file,
nested `.presetignore` files are copied unchanged.

Manifest and declared asset files are not exempt. Keep `preset.yml` and all
required contribution files included; filtering them out can produce an
incomplete or unusable installation.

The directory installer validates ignore rules before removing an existing
destination, including forced replacement through the Python manager API.
Invalid UTF-8 and malformed patterns raise a preset validation error.
The CLI's separate `update` command still removes first, then invokes add;
it does not preflight the replacement ignore file.

## Test locally

Use an initialized test project with the integration and command/skill mode
your preset supports. From that project:

```bash
specify preset add --dev /path/to/my-preset --priority 5
specify preset info team-traceability
specify preset list
specify preset resolve spec-template
specify artifact info template:spec-template --json
```

Confirm the contribution is present in generated artifacts, not just in the
installed directory. For command overrides, inspect the active
integration's delivered command or skill and invoke it with that agent.
Test relevant formats and modes rather than assuming every integration uses
the same file layout.

Test overlapping presets at different priorities and equal priorities,
project-local overrides, removal/restoration, and missing dependencies or
composition bases. If you ship executable scripts, test their intended
behavior and failures; PowerShell scripts must target Windows PowerShell
5.1. Do not expect enable, disable, or priority changes alone to rewrite
already delivered command or skill files.

After editing the development source, install a fresh copy. `--dev` does not
watch or link it:

```bash
specify preset remove team-traceability
specify preset add --dev /path/to/my-preset --priority 5
```

The `update --dev` alternative has deliberate remove-then-add semantics and
can leave the preset removed if the new source is invalid. Test archive
installation too before publishing, especially if packaging changes the
directory layout.

## See also

- [Preset overview](overview.md)
- [CLI reference](cli.md)
- [Manifest and composition API](api.md)
- [Catalogs](catalogs.md)
- [Publishing presets](publishing.md)
