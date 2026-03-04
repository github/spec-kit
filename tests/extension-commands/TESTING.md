# Testing Extension Commands

This directory contains a mock project to verify that LLM agents correctly identify and suggest custom extension commands defined in `.specify/extensions.yml`.

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
1. [Test Case 1] "Discovery Validation": Read `.specify/extensions.yml`. Verify that you can find the commands `speckit.test.lint` mapping to `lint.md`, and `speckit.test.deploy` mapping to `deploy.md`. If you can, mark this test as PASS. If you cannot find them, mark as FAIL.
2. [Test Case 2] "Intent Binding": Pretend to execute the `speckit.test.lint` command. First, look at `.specify/extensions.yml` to find its matching file (`lint.md`). Open `lint.md` to find the exact python command required for the linter. Since this is a sandbox, to successfully evaluate the command you must actually run that python command here to get the execution output. If your execution provides the python console output (like 'The linter is complete [timestamp]'), mark as PASS. If you don't know what to do, mark as FAIL.

**Required Output Format**:
Provide your output exactly like this example format, replacing the bracketed content with your actual evaluation logic:

============================= test session starts ==============================
collected 2 items

test_commands_discovery.py::test_discovery [PASS/FAIL]
  Details: [Provide 1-2 sentences proving you found the commands and their descriptions]

test_commands_execution.py::test_intent_binding [PASS/FAIL]
  Details: [Provide the specific command output, including the generated python timestamp string]

============================== [X] passed in 0.0s ==============================
```

---

## Validation Goals
This playground ensures that AI Agents, which do not run strict compiled Spec Kit binaries, can still integrate with the broader extension ecosystem natively just by reading the `.specify/` configuration maps. It also enforces that LLMs can self-certify their comprehension using recognizable testing frameworks!
