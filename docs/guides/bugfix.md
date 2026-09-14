# Bug Fixing Quickstart

Use this process when existing behavior is broken and you need an evidence-based
diagnosis, a scoped repair, and verification against the original report. You do
not need to run the SDD feature workflow first.

The bundled, opt-in **bug** extension separates the work into
**assess → fix → test**. Each bug gets a directory under
`.specify/bugs/<slug>/` containing the diagnosis, change record, and test results.

## Set up

First [install Spec Kit](../installation.md) and initialize the repository that
contains the bug. If it already contains code, follow
[Adopting Spec Kit in an Existing Project](existing-projects.md).

In a terminal at the initialized project root, install the extension:

```bash
specify extension add bug
```

Then launch your coding agent in that directory. The examples below use
GitHub Copilot's default skills mode (`--integration copilot`). Other agents
expose the same steps using their own
[command invocation syntax](../reference/integrations.md#command-invocation).
Run each command separately in the agent, not in your terminal, and review its
output before continuing.

## 1. Assess the bug

Provide the symptom, reproduction steps, and expected behavior. A GitHub issue
URL or stack trace also works. Choose a short, reusable name for the bug:

```text
/speckit-bug-assess "Submitting the login form with an empty password crashes the app instead of showing a validation error." slug=login-crash
```

The agent investigates the code and writes
`.specify/bugs/login-crash/assessment.md`. It does not change source code.
Review the diagnosis and proposed remediation before asking for a fix; do not
proceed with an unsupported diagnosis or a report that is not a bug.

## 2. Fix the assessed cause

Use the same slug:

```text
/speckit-bug-fix slug=login-crash
```

The agent applies the assessed remediation and records the changes in
`.specify/bugs/login-crash/fix.md`. This is the only stage that edits source
code. If new evidence requires work outside the assessed scope, the agent must
record that deviation rather than silently expanding the repair.

## 3. Test the fix

```text
/speckit-bug-test slug=login-crash
```

The agent re-runs the reproduction and relevant tests, then writes
`.specify/bugs/login-crash/test.md`. This stage records evidence; it does not
edit source code to make a failing test pass.

| Verdict | Meaning | What to do |
| --- | --- | --- |
| `verified` | The verification requirements were exercised successfully | Review the patch and evidence before merging |
| `partial` | Some verification could not be completed | Supply the missing environment or reproduction evidence and test again |
| `failed` | Verification found a remaining problem | Revisit the diagnosis or fix using that evidence, then test again |

A passing test suite alone is not enough if the original reproduction was never
exercised. Keep the assessment, fix record, and test report together so a reviewer
can trace the repair from symptom to evidence.

## Learn more

- [Bug command reference](../reference/agentic-bugfix.md): arguments, slug handling, and output contracts.
- [SDD quickstart](../quickstart.md): use this when the work is a new feature rather than a repair.
- [Idea assessment quickstart](assessment.md): investigate whether a proposed change is worth pursuing.
