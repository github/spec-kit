# Testing Extension Hooks

This directory contains a mock project to verify that LLM agents correctly identify and execute hook commands defined in `.specify/extensions.yml`.

## Test 1: Testing `before_tasks` and `after_tasks`

1. Open a chat with an LLM (like GitHub Copilot) in this project.
2. Ask it to generate tasks for the current directory:
   > "Please follow `/speckit.tasks` for the `./tests/hooks` directory."
3. **Expected Behavior**: 
   - Before doing any generation, the LLM should notice the `AUTOMATIC Pre-Hook` in `.specify/extensions.yml` under `before_tasks`.
   - It should state it is executing `EXECUTE_COMMAND: pre_tasks_test`.
   - It should then proceed to read the `.md` docs and produce a `tasks.md`.
   - After generation, it should output the optional `after_tasks` hook (`post_tasks_test`) block, asking if you want to run it.

## Test 2: Testing `before_implement` and `after_implement`

*(Requires `tasks.md` from Test 1 to exist)*

1. In the same (or new) chat, ask the LLM to implement the tasks:
   > "Please follow `/speckit.implement` for the `./tests/hooks` directory."
2. **Expected Behavior**:
   - The LLM should first check for `before_implement` hooks.
   - It should state it is executing `EXECUTE_COMMAND: pre_implement_test` BEFORE doing any actual task execution.
   - It should evaluate the checklists and execute the code writing tasks.
   - Upon completion, it should output the optional `after_implement` hook (`post_implement_test`) block.

## How it works

The templates for these commands in `templates/commands/tasks.md` and `templates/commands/implement.md` contains strict ordered lists. The new `before_*` hooks are explicitly formulated in a **Pre-Execution Checks** section prior to the outline to ensure they're evaluated first without breaking template step numbers.
