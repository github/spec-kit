"""InfraKit CLI — spec-kit for IaC, with a multi-persona pipeline.

The package's public API is split into focused submodules:

- :mod:`infrakit_cli.cli` — the Typer app, the four user-facing commands
  (``init``, ``check``, ``mcp``, ``version``), and the ``main()`` entry point.
- :mod:`infrakit_cli.bootstrap` — ``initialize_iac_config()`` materialises
  ``.infrakit/`` and ``.infrakit_tracks/`` on a freshly-initialised project.
- :mod:`infrakit_cli.template_renderer` — runtime per-agent transformer.
- :mod:`infrakit_cli.skills` — installs prompt files as agent skills.
- :mod:`infrakit_cli.mcp` — MCP recipe install helpers.
- :mod:`infrakit_cli.tracker` — :class:`StepTracker` UI primitive.
- :mod:`infrakit_cli.interactive` — keyboard input + arrow-key menu.
- :mod:`infrakit_cli.banner` — ASCII banner and Typer group override.
- :mod:`infrakit_cli.tools` — subprocess + tool-detection helpers.
- :mod:`infrakit_cli.git_utils` — repo detection + ``git init`` wrapper.
- :mod:`infrakit_cli.github_api` — token/auth/rate-limit helpers for the
  optional ``infrakit version`` check.
- :mod:`infrakit_cli.console` — shared :class:`rich.console.Console` instance.

The top-level :func:`main` function (re-exported below) is the
``project.scripts`` entry point: ``infrakit = "infrakit_cli:main"``.

The other re-exports preserve a stable import surface so that existing tests
and downstream callers continue to use ``from infrakit_cli import X``.
"""

from .banner import BannerGroup, show_banner
from .bootstrap import initialize_iac_config
from .cli import app, callback, check, init, main, mcp, version
from .console import console
from .git_utils import init_git_repo, is_git_repo
from .github_api import (
    _format_rate_limit_error,
    _github_auth_headers,
    _github_token,
    _parse_rate_limit_headers,
    client,
    ssl_context,
)
from .interactive import get_key, select_with_arrows
from .mcp import (
    _build_mcp_markdown_block,
    _build_mcp_server_entry,
    _read_mcp_json,
    _update_mcp_use_table,
)
from .skills import (
    AGENT_SKILLS_DIR_OVERRIDES,
    DEFAULT_SKILLS_DIR,
    SKILL_DESCRIPTIONS,
    _get_skills_dir,
    ensure_project_context_from_template,
    install_ai_skills,
)
from .tools import (
    CLAUDE_LOCAL_PATH,
    SCRIPT_TYPE_CHOICES,
    check_tool,
    find_project_root,
    run_command,
)
from .tracker import StepTracker

__all__ = [
    # Typer app + commands
    "app",
    "callback",
    "check",
    "init",
    "main",
    "mcp",
    "version",
    # UI primitives
    "BannerGroup",
    "console",
    "show_banner",
    "StepTracker",
    "select_with_arrows",
    "get_key",
    # Project bootstrap
    "initialize_iac_config",
    "ensure_project_context_from_template",
    # Tools / git
    "check_tool",
    "find_project_root",
    "init_git_repo",
    "is_git_repo",
    "run_command",
    "CLAUDE_LOCAL_PATH",
    "SCRIPT_TYPE_CHOICES",
    # MCP
    "_build_mcp_markdown_block",
    "_build_mcp_server_entry",
    "_read_mcp_json",
    "_update_mcp_use_table",
    # Skills
    "AGENT_SKILLS_DIR_OVERRIDES",
    "DEFAULT_SKILLS_DIR",
    "SKILL_DESCRIPTIONS",
    "_get_skills_dir",
    "install_ai_skills",
    # GitHub API helpers (used by the version command)
    "_format_rate_limit_error",
    "_github_auth_headers",
    "_github_token",
    "_parse_rate_limit_headers",
    "client",
    "ssl_context",
]


if __name__ == "__main__":
    main()
