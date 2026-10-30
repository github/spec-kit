# Goose

Install [Goose](https://goose-docs.ai/) before setup.
The integration key is `goose`.

## Multi-Install Safety

This integration is not declared multi-install safe. See the
[shared multi-install rules](cli.md#can-i-install-multiple-integrations-in-the-same-project).

## Setup

```bash
specify init my-project --integration goose
```

For an existing Spec Kit project, use `specify integration install goose`.
See [integration management](cli.md) for activation, upgrades, and removal.

## Installed Recipes

Goose uses YAML recipes installed as `.goose/recipes/speckit.<command>.yaml`.
Spec Kit workflow dispatch translates `/speckit.<command>` invocations into
recipe execution, passing trailing arguments as the recipe's `args` parameter.
Use Goose's recipe interface for interactive execution rather than assuming
the recipes are skills.

## Workflow Dispatch

Dispatch uses `goose run --recipe <path>` for `/speckit.<command>` prompts,
and `goose run -t <prompt>` for other prompt text, including non-Spec-Kit
slash commands. A configured `--model` and requested `--output-format json`
are forwarded.

Avoid repeating single-value flags such as `--model`, `--recipe`, or
`--output-format` in `SPECKIT_INTEGRATION_GOOSE_EXTRA_ARGS`; Goose rejects
duplicate occurrences rather than using the last value.
There are no integration-specific setup options.
