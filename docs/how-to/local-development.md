# How to develop Spec Kit locally

Use a separate `.venv` in each checkout or worktree, install that checkout in
editable mode, and run its CLI and tests through explicit environment paths.
This keeps local changes isolated from globally installed releases and other
Spec Kit checkouts. Environment activation is not required.

## 1. Prepare the Checkout

Install [Python 3.11+](https://www.python.org/downloads/),
[uv](https://docs.astral.sh/uv/), and [Git](https://git-scm.com/downloads/).
Clone your fork and work on a feature branch following the
[branch naming guidance](https://github.com/github/spec-kit/blob/main/CONTRIBUTING.md#branch-naming).
Run the following setup from that checkout's repository root.

On macOS or Linux:

```bash
uv sync --extra test
uv pip install --python .venv/bin/python -e .
.venv/bin/specify --help
```

On Windows PowerShell:

```powershell
uv sync --extra test
uv pip install --python .venv\Scripts\python.exe -e .
.\.venv\Scripts\specify.exe --help
```

`uv sync --extra test` creates the project environment and installs its test
dependencies. The explicit editable install targets that same environment.
Python source edits require no reinstall; rerun setup when dependency metadata
changes.

## 2. Run Focused Automated Checks

Start with the tests covering your change, using actual test paths in place of
the example below.

On macOS or Linux:

```bash
.venv/bin/python -m pytest tests/test_agent_config_consistency.py -q
```

On Windows PowerShell:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_agent_config_consistency.py -q
```

For the full suite, replace the test file with `tests`. On macOS, set
`LC_ALL=en_US.UTF-8` for tests so Bash Unicode handling uses a UTF-8 locale:

```bash
LC_ALL=en_US.UTF-8 .venv/bin/python -m pytest tests -q
```

Run the same Ruff version as CI:

```bash
uvx ruff@0.15.0 check src tests
```

Ruff runs as an isolated lint tool; run the Spec Kit CLI and pytest only
through the checkout's `.venv`. See the
[contributor testing guidance](https://github.com/github/spec-kit/blob/main/CONTRIBUTING.md#testing-deterministic-behavior)
for positive and negative coverage, regression evidence, Windows PowerShell
5.1 compatibility, and additional checks.

## 3. Test the CLI in a Separate Project

Initialize a disposable project outside the Spec Kit checkout, using the
checkout's CLI. Choose your agent's
[integration key](../integrations/index.md).

On macOS or Linux, from the Spec Kit repository root:

```bash
.venv/bin/specify init /tmp/spec-kit-test --integration <key> --script sh
```

On Windows PowerShell, from the Spec Kit repository root:

```powershell
.\.venv\Scripts\specify.exe init "$env:TEMP\spec-kit-test" --integration <key> --script ps
```

Choose an unused project directory for each independent test. Use `--script py`
when testing the Python script variant. Open the generated project in your
coding agent and follow the
[manual testing process](https://github.com/github/spec-kit/blob/main/CONTRIBUTING.md#manual-testing-process)
when slash-command behavior changes.

If you run further CLI commands from the generated project, use the absolute
path to the Spec Kit checkout's executable; do not switch to a globally
installed `specify`. Replace the example checkout path below with your actual
checkout path. For example, to check the CLI and add the git extension in the
generated project:

On macOS or Linux:

```bash
"/path/to/spec-kit/.venv/bin/specify" --help
"/path/to/spec-kit/.venv/bin/specify" extension add git
```

On Windows PowerShell:

```powershell
& "C:\path\to\spec-kit\.venv\Scripts\specify.exe" --help
& "C:\path\to\spec-kit\.venv\Scripts\specify.exe" extension add git
```

The PowerShell call operator (`&`) executes the quoted path, including paths
that contain spaces.

Generated scripts live under `.specify/scripts/`. When testing Bash script
permissions on macOS or Linux, inspect them from the generated project:

```bash
ls -l .specify/scripts/bash/*.sh
```

The scripts should have the owner execute bit set. PowerShell scripts on
Windows do not require `chmod`.

## 4. Check Packaging When Relevant

For packaging changes, build the wheel from the Spec Kit repository root:

```bash
uv build
```

Inspect the artifacts in `dist/`. Packaging validation supplements the
editable-install development loop; it does not replace the test environment.

## Common Issues

| Symptom | Action |
| --- | --- |
| Missing Python dependencies | Rerun the setup commands from this checkout's root. |
| Tests or CLI use another checkout | Use this checkout's explicit `.venv` executable paths. |
| Git commands unavailable in the generated project | Run the checkout's CLI with `extension add git`, using its absolute `.venv` path from the generated project. |
| Wrong script variant generated | Pass `--script sh`, `--script ps`, or `--script py` explicitly. |
| TLS errors on a corporate network | Configure the certificate store or proxy, for example with `SSL_CERT_FILE`, `HTTPS_PROXY`, or `HTTP_PROXY`. The deprecated `--skip-tls` flag is a no-op. |

## See also

- [Contributor guide](https://github.com/github/spec-kit/blob/main/CONTRIBUTING.md)
- [Contributing integrations](../integrations/contributing.md)
- [Agent integration design](https://github.com/github/spec-kit/blob/main/design/integration.md#adding-an-agent)
- [Spec-Driven Development quickstart](../quickstart.md)
- [Does Spec Kit use Spec Kit?](https://github.com/github/spec-kit/blob/main/CONTRIBUTING.md#does-spec-kit-use-spec-kit)
