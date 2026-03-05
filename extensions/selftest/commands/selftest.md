---
description: "Validate the lifecycle of an extension from the catalog."
---

# Extension Self-Test: `$ARGUMENTS`

This command drives a self-test simulating the developer experience with the `$ARGUMENTS` extension.

## Goal

Validate the end-to-end lifecycle (discovery, installation, registration) for the extension: `$ARGUMENTS`.
If `$ARGUMENTS` is empty, you must tell the user to provide an extension name, for example: `/speckit.selftest linear`.

## Steps

### Step 1: Catalog Discovery Validation

Check if the extension exists in the Spec Kit catalog.
Execute this command and verify that `$ARGUMENTS` appears in the results. If the command fails or returns no results, fail the test.

```bash
specify extension search $ARGUMENTS
```

### Step 2: Simulate Installation

Simulate adding the extension to the current workspace configuration.

```bash
specify extension add $ARGUMENTS
```

### Step 3: Registration Verification

Once the `add` command completes, verify the installation by checking the project configuration.
Use terminal tools (like `cat`) to verify that the following file contains an enabled record for `$ARGUMENTS`.

```bash
cat .specify/extensions.yml
```

### Step 4: Verification Report

Analyze the standard output of the three steps. 
Generate a terminal-style test output format detailing the results of discovery, installation, and registration. Return this directly to the user.

Example output format:
```text
============================= test session starts ==============================
collected 3 items

test_selftest_discovery.py::test_catalog_search [PASS/FAIL]
  Details: [Provide execution result of specify extension search]

test_selftest_installation.py::test_extension_add [PASS/FAIL]
  Details: [Provide execution result of specify extension add]

test_selftest_registration.py::test_config_verification [PASS/FAIL]
  Details: [Provide execution result of reading .specify/extensions.yml]

============================== [X] passed in ... ==============================
```
