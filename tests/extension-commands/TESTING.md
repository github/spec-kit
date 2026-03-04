# Testing Extension Commands

This directory contains a mock project to verify that LLM agents correctly identify and execute custom extension commands defined in `.specify/extensions.yml`.

## Automated LLM Test Execution

To execute this test, copy the following block and paste it into GitHub Copilot Chat (or your LLM of choice) while focused on this `TESTING.md` file:

---

**PROMPT TO COPY:**

```prompt
Act as an automated test runner (like Ginkgo or pytest) evaluating your own comprehension of the current workspace. I want you to run the following test suite on the `.specify/extensions.yml` file in this directory and output the results strictly in a terminal-style test output format.

**Test Suite Context**:
Before you begin, read `../../extensions/EXTENSION-API-REFERENCE.md` to understand how the Spec Kit architecture structures extensions, commands, and markdown file execution formats. 

You are evaluating if you can correctly parse `.specify/extensions.yml` to map a command name to a markdown file, and then execute the script described in that markdown file.

**Test Cases to Evaluate**:
1. [Test Case 1] "Discovery Validation": Load the extension according to the specification. Verify that you have discovered the commands `speckit.test.lint` and `speckit.test.deploy`. If you can find them and their properties in the extensions config, mark as PASS. If not, mark as FAIL.
2. [Test Case 2] "Simulate Lint Command": Simulate a user running `/speckit.test.lint`. Look up its execution configuration in `.specify/extensions.yml` and find its matching script file (`lint.md`). Since this is a testing sandbox, actually execute the required python command to get the execution output. Validate the output of the python program (it should be 'The linter is complete [timestamp]'). If you successfully produce this output, mark as PASS.
3. [Test Case 3] "Simulate Deploy Command": Simulate a user running `/speckit.test.deploy`. Find its matching script file (`deploy.md`). Actually execute the required python command to get the execution output. Validate the output of the python program (it should be 'Staging deployment is completed at [timestamp]'). If you successfully produce this output, mark as PASS.

**Required Output Format**:
Provide your output exactly like this example format, replacing the bracketed content with your actual evaluation logic:

============================= test session starts ==============================
collected 3 items

test_commands_discovery.py::test_discovery [PASS/FAIL]
  Details: [Provide 1-2 sentences proving you found the commands and their descriptions]

test_commands_execution.py::test_lint_command [PASS/FAIL]
  Details: [Provide the specific command output for lint, including the generated python timestamp string]

test_commands_execution.py::test_deploy_command [PASS/FAIL]
  Details: [Provide the specific command output for deploy, including the generated python timestamp string]

============================== [X] passed in 0.0s ==============================
```

---

## Validation Goals
This playground ensures that AI Agents, which do not run strict compiled Spec Kit binaries, can still integrate with the broader extension ecosystem natively just by reading the `.specify/` configuration maps. It also enforces that LLMs can self-certify their comprehension using recognizable testing frameworks!
