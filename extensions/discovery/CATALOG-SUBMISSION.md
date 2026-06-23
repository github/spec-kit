# Spec Kit Extension Submission

Extension ID: discovery
Name: Spec Kit Discovery Extension
Version: 0.1.0
Description: Run technical discovery commands for feasibility, technology selection, vertical technology decisions, legacy codebase assessment, and proof-of-concept validation.
Author: bigsmartben
Repository URL: https://github.com/bigsmartben/spec-kit-discovery
Download URL: https://github.com/bigsmartben/spec-kit-discovery/archive/refs/tags/v0.1.0.zip
Documentation URL: https://github.com/bigsmartben/spec-kit-discovery#readme
License: MIT
Required Spec Kit version: >=0.1.0
Commands count: 10
Hooks count: 0
Tags: discovery, feasibility, selection, codebase, poc, api, performance, migration, ux, compatibility

## Key Features

- Adds `speckit.discovery.feasibility`, `speckit.discovery.techselect`, and `speckit.discovery.codebase`.
- Adds `speckit.discovery.codebase-api-imp` for source-backed implementation overviews.
- Adds `speckit.discovery.poc` for bounded proof-of-concept planning and validation.
- Adds vertical discovery commands for API, performance, migration, UX, and compatibility decisions.
- Keeps outputs focused on evidence, assumptions, unknowns, planning decisions, and validation scope before formal implementation planning.

## Testing Performed

- Validated the bundled manifest with `ExtensionManifest`.
- Ran `uv run pytest tests/integrations/test_cli.py -k "community_extensions_and_workflow_preset_auto_installed or no_git_keeps_community_defaults"`.
- Ran `uv run pytest tests/test_arch_templates.py tests/test_presets.py -k "community_smoke_checks_wheel_assets_and_extension_dev_reinstall or init_next_steps_do_not_list_arch_as_core_workflow"`.
- Built the CLI wheel with `uv build --wheel` and verified `specify_cli/core_pack/extensions/discovery/extension.yml` and representative command/template files were included.
- Smoke-tested `specify init`, `specify extension remove discovery --force`, and `specify extension add discovery` in a temporary project.
