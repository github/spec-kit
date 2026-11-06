# Support

## How to get help

Please search existing [issues](https://github.com/github/spec-kit/issues) and [discussions](https://github.com/github/spec-kit/discussions) before creating new ones to avoid duplicates.

- Review the [README](./README.md) for getting started instructions and troubleshooting tips
- Check the [comprehensive guide](./spec-driven.md) for detailed documentation on the Spec-Driven Development process
- Ask in [GitHub Discussions](https://github.com/github/spec-kit/discussions) for questions about using Spec Kit or the Spec-Driven Development methodology
- Open a [GitHub issue](https://github.com/github/spec-kit/issues/new) for bug reports and feature requests

## Project Status

**Spec Kit** is under active development and maintained by GitHub staff and the community. We will do our best to respond to support, feature requests, and community questions as time permits.

## Python version support

Python compatibility, CI coverage, and regression fixes are maintained on a
best-effort basis, subject to maintainer availability. This policy does not
guarantee compatibility, a fix, or a response or resolution timeline.

Spec Kit's minimum Python version is declared by `requires-python` in
[`pyproject.toml`](./pyproject.toml). Support does not mean every supported
Python and operating system combination is tested on every change:

| Python version | Routine CI (pull requests and pushes to `main`) | Weekly scheduled and manual CI (`workflow_dispatch`) |
| --- | --- | --- |
| Minimum supported version (3.11) | Linux, Windows, macOS | Linux, Windows, macOS |
| Bugfix-supported stable versions (3.14, 3.15) | Linux, Windows, macOS | Linux, Windows, macOS |
| Other supported stable versions | Not run | Linux, Windows, macOS |

This balances CI cost with compatibility coverage. The minimum supported
version is our touchstone across all three platforms alongside bugfix-supported
stable releases. The full Python 3.11 through 3.15 matrix runs weekly and when
manually triggered. Regressions on older
supported versions are addressed as needed when discovered through CI or user
reports, rather than through proactive fixes for hypothetical problems.
The exact versions tested are configured in the
[Test & Lint Python workflow](./.github/workflows/test.yml).

The [Python Developer's Guide version status](https://devguide.python.org/versions/)
provides the current upstream lifecycle status for each version. For branches
in security-only support, the core Python project no longer publishes new
binary releases, although source-only security releases may still be issued.
This does not make those versions unsupported or mean that third-party
distributors cannot provide binaries.

When the minimum supported Python version reaches upstream end of life,
advance both the touchstone and the minimum requirement to the next
supported version, removing the end-of-life version from the full matrix.

## GitHub Support Policy

Support for this project is limited to the resources listed above.
