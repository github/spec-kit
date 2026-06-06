"""Shared test helpers for the Spec Kit test suite."""

import os
import re
import shutil
import subprocess
import sys
import importlib.util

import pytest

from tests._parallel import (
    compute_recommended_workers,
    detect_available_memory_bytes,
    detect_effective_cpu_count,
    detect_total_memory_bytes,
)

_ANSI_ESCAPE_RE = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")


def _args_before_double_dash(args: list[str]) -> list[str]:
    """Return only option-parsed args before '--' positional sentinel."""
    if "--" in args:
        return args[:args.index("--")]
    return args


def _has_xdist_installed() -> bool:
    """Return whether pytest-xdist is importable in this environment."""
    return importlib.util.find_spec("xdist") is not None


def _is_plugin_autoload_disabled() -> bool:
    """Return True when pytest plugin autoload is explicitly disabled."""
    value = os.environ.get("PYTEST_DISABLE_PLUGIN_AUTOLOAD", "")
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _has_numprocesses_arg(args: list[str]) -> bool:
    """Return True when users explicitly pass -n/--numprocesses."""
    args = _args_before_double_dash(args)
    idx = 0
    while idx < len(args):
        arg = args[idx]
        if arg in ("-n", "--numprocesses"):
            return True
        if arg.startswith("--numprocesses="):
            return True
        # Support compact forms like -n2 or -nauto
        if arg.startswith("-n") and arg != "-n":
            return True
        idx += 1
    return False


def _has_dist_arg(args: list[str]) -> bool:
    """Return True when users explicitly pass --dist."""
    args = _args_before_double_dash(args)
    return any(arg == "--dist" or arg.startswith("--dist=") for arg in args)


def _is_xdist_disabled(args: list[str]) -> bool:
    """Return True when users explicitly disable xdist with -p no:xdist."""
    args = _args_before_double_dash(args)
    idx = 0
    while idx < len(args):
        arg = args[idx]
        if arg == "-p":
            if idx + 1 < len(args) and args[idx + 1].startswith("no:xdist"):
                return True
            idx += 2
            continue
        if arg.startswith("-pno:xdist"):
            return True
        idx += 1
    return False


def _extract_cli_option(args: list[str], option: str, default: str | None = None) -> str | None:
    """Extract option value from --opt value or --opt=value forms."""
    args = _args_before_double_dash(args)
    prefix = f"{option}="
    idx = 0
    while idx < len(args):
        arg = args[idx]
        if arg == option:
            if idx + 1 < len(args):
                return args[idx + 1]
            return default
        if arg.startswith(prefix):
            return arg[len(prefix):]
        idx += 1
    return default


def _compute_parallel_settings_from_args(args: list[str]):
    """Compute parallel worker settings from CLI args using shared detection."""
    tier = _extract_cli_option(args, "--parallel-tier", "medium")
    max_workers_raw = _extract_cli_option(args, "--parallel-max-workers", None)
    max_workers = None
    if max_workers_raw not in (None, ""):
        try:
            max_workers = int(max_workers_raw)
        except ValueError:
            max_workers = None

    return compute_recommended_workers(
        cpu_count=detect_effective_cpu_count(),
        total_memory_bytes=detect_total_memory_bytes(),
        available_memory_bytes=detect_available_memory_bytes(),
        platform_name=sys.platform,
        max_workers=max_workers,
        tier=tier if tier in ("low", "medium", "high") else "medium",
    )


def _build_parallel_injected_args(args: list[str], workers: int) -> list[str]:
    """Build xdist args to inject for parallel execution."""
    injected_args = ["-n", str(workers)]
    if not _has_dist_arg(args):
        injected_args.extend(["--dist", "worksteal"])
    return injected_args


def pytest_load_initial_conftests(early_config, parser, args):
    """Inject xdist flags early so --parallel actually runs with workers."""
    if "--parallel" not in args:
        return
    if not _has_xdist_installed():
        return
    if _is_plugin_autoload_disabled():
        return
    if _is_xdist_disabled(args):
        return
    if _has_numprocesses_arg(args):
        return

    settings = _compute_parallel_settings_from_args(args)
    injected_args = _build_parallel_injected_args(args, settings.workers)
    if "--" in args:
        idx = args.index("--")
        args[idx:idx] = injected_args
    else:
        args.extend(injected_args)


def _has_working_bash() -> bool:
    """Check whether a functional native bash is available.

    On Windows, ``subprocess.run(["bash", ...])`` uses CreateProcess,
    which searches System32 *before* PATH — so it may find the WSL
    launcher even when Git-for-Windows bash appears first in PATH via
    ``shutil.which``.  We therefore probe with bare ``"bash"`` (the
    same way test helpers invoke it) to get an accurate result.

    On Windows, only Git-for-Windows bash (MSYS2/MINGW) is accepted.
    The WSL launcher is rejected because it runs in a separate Linux
    filesystem and cannot handle native Windows paths used by the
    test fixtures.

    Set SPECKIT_TEST_BASH=1 to force-enable bash tests regardless.
    """
    if os.environ.get("SPECKIT_TEST_BASH") == "1":
        return True
    if shutil.which("bash") is None:
        return False
    # Probe with bare "bash" — same as the test helpers — so that
    # Windows CreateProcess resolution order is respected.
    try:
        r = subprocess.run(
            ["bash", "-c", "echo ok"],
            capture_output=True, text=True, timeout=5,
        )
        if r.returncode != 0 or "ok" not in r.stdout:
            return False
    except (OSError, subprocess.TimeoutExpired):
        return False
    # On Windows, verify we have MSYS/MINGW bash (Git for Windows),
    # not the WSL launcher which can't handle native paths.
    if sys.platform == "win32":
        try:
            u = subprocess.run(
                ["bash", "-c", "uname -s"],
                capture_output=True, text=True, timeout=5,
            )
            kernel = u.stdout.strip().upper()
            if not any(k in kernel for k in ("MSYS", "MINGW", "CYGWIN")):
                return False
        except (OSError, subprocess.TimeoutExpired):
            return False
    return True


requires_bash = pytest.mark.skipif(
    not _has_working_bash(), reason="working bash not available"
)


def strip_ansi(text: str) -> str:
    """Remove ANSI escape codes from Rich-formatted CLI output."""
    return _ANSI_ESCAPE_RE.sub("", text)


def pytest_addoption(parser):
    """Add Spec Kit parallel-test controls on top of pytest-xdist."""
    group = parser.getgroup("spec-kit")
    group.addoption(
        "--parallel",
        action="store_true",
        default=False,
        help="Run tests in parallel using a system-aware worker limit.",
    )
    group.addoption(
        "--parallel-max-workers",
        action="store",
        type=int,
        default=None,
        help="Upper bound for --parallel worker count.",
    )
    group.addoption(
        "--parallel-tier",
        action="store",
        choices=("low", "medium", "high"),
        default="medium",
        help="Parallel aggressiveness tier: low, medium, or high (default: medium).",
    )


def pytest_configure(config):
    """Enable bounded xdist parallelism only when --parallel is requested."""
    if not config.getoption("--parallel"):
        return

    invocation_args = list(config.invocation_params.args)
    if _is_xdist_disabled(invocation_args):
        raise pytest.UsageError("--parallel cannot be used with '-p no:xdist'.")

    max_workers = config.getoption("--parallel-max-workers")
    tier = config.getoption("--parallel-tier")
    if max_workers is not None and max_workers < 1:
        raise pytest.UsageError("--parallel-max-workers must be >= 1")

    if not hasattr(config.option, "numprocesses"):
        if _is_plugin_autoload_disabled():
            raise pytest.UsageError(
                "--parallel requires pytest-xdist plugin loading. Unset PYTEST_DISABLE_PLUGIN_AUTOLOAD or enable xdist explicitly."
            )
        raise pytest.UsageError(
            "--parallel requires pytest-xdist. Install test extras with `uv sync --extra test`."
        )

    settings = compute_recommended_workers(
        cpu_count=detect_effective_cpu_count(),
        total_memory_bytes=detect_total_memory_bytes(),
        available_memory_bytes=detect_available_memory_bytes(),
        platform_name=sys.platform,
        max_workers=max_workers,
        tier=tier,
    )

    # Respect explicit -n values from CLI; otherwise keep the early-injected value.
    requested_numprocesses = getattr(config.option, "numprocesses", None)
    if requested_numprocesses in (None, 0):
        config.option.numprocesses = settings.workers
    if hasattr(config.option, "dist") and not _has_dist_arg(invocation_args):
        config.option.dist = "worksteal"

    setattr(config, "_spec_kit_parallel_settings", settings)
    setattr(config, "_spec_kit_parallel_effective_workers", getattr(config.option, "numprocesses", settings.workers))


def pytest_report_header(config):
    """Display resolved system-aware parallel settings in pytest header."""
    settings = getattr(config, "_spec_kit_parallel_settings", None)
    if settings is None:
        return None

    effective_workers = getattr(config, "_spec_kit_parallel_effective_workers", settings.workers)

    total_gib = (
        f"{settings.total_memory_bytes / (1024 ** 3):.1f}GiB"
        if settings.total_memory_bytes is not None
        else "unknown"
    )
    avail_gib = (
        f"{settings.available_memory_bytes / (1024 ** 3):.1f}GiB"
        if settings.available_memory_bytes is not None
        else "unknown"
    )
    return (
        "[spec-kit] --parallel settings: "
        f"tier={settings.tier}, "
        f"workers={effective_workers} "
        f"(cpu_cap={settings.cpu_cap}, mem_cap={settings.memory_cap}, os_cap={settings.os_cap}), "
        f"effective_cpus={settings.effective_cpus}, "
        f"avail_mem={avail_gib}, total_mem={total_gib}, "
        f"mem_per_worker={settings.memory_per_worker_gib:.1f}GiB"
    )


# ---------------------------------------------------------------------------
# Auth config isolation — prevents tests from reading ~/.specify/auth.json
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _isolate_auth_config(monkeypatch):
    """Ensure no test reads the real ~/.specify/auth.json."""
    from specify_cli.authentication import http as _auth_http
    monkeypatch.setattr(_auth_http, "_config_override", [])
    # Also clear the per-process cache so tests that unset _config_override
    # won't see a previously cached real-file result.
    monkeypatch.setattr(_auth_http, "_config_cache", None)


@pytest.fixture
def clean_environ(monkeypatch):
    """Strip any real GH_TOKEN / GITHUB_TOKEN from the test environment."""
    monkeypatch.delenv("GH_TOKEN", raising=False)
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)


def _fake_self_upgrade_argv0(monkeypatch, tmp_path, env_name, path_parts):
    """Create a fake executable under tmp_path and point sys.argv[0] at it."""
    monkeypatch.setenv(env_name, str(tmp_path))
    fake_dir = tmp_path.joinpath(*path_parts)
    fake_dir.mkdir(parents=True)
    fake_specify = fake_dir / ("specify.exe" if os.name == "nt" else "specify")
    fake_specify.write_text("#!/usr/bin/env python\n")
    fake_specify.chmod(0o755)
    monkeypatch.setattr("sys.argv", [str(fake_specify)])
    return fake_specify


@pytest.fixture
def uv_tool_argv0(monkeypatch, tmp_path):
    """Point sys.argv[0] at a simulated `uv tool` install path under tmp HOME."""
    if os.name == "nt":
        return _fake_self_upgrade_argv0(
            monkeypatch, tmp_path, "LOCALAPPDATA", ("uv", "tools", "specify-cli", "bin")
        )
    return _fake_self_upgrade_argv0(
        monkeypatch,
        tmp_path,
        "HOME",
        (".local", "share", "uv", "tools", "specify-cli", "bin"),
    )


@pytest.fixture
def pipx_argv0(monkeypatch, tmp_path):
    """Point sys.argv[0] at a simulated pipx install path under tmp HOME."""
    if os.name == "nt":
        return _fake_self_upgrade_argv0(
            monkeypatch, tmp_path, "LOCALAPPDATA", ("pipx", "venvs", "specify-cli", "bin")
        )
    return _fake_self_upgrade_argv0(
        monkeypatch, tmp_path, "HOME", (".local", "pipx", "venvs", "specify-cli", "bin")
    )


@pytest.fixture
def uvx_ephemeral_argv0(monkeypatch, tmp_path):
    """Point sys.argv[0] at a simulated uvx ephemeral-cache path under tmp HOME."""
    if os.name == "nt":
        return _fake_self_upgrade_argv0(
            monkeypatch,
            tmp_path,
            "LOCALAPPDATA",
            ("uv", "cache", "archive-v0", "abc123", "bin"),
        )
    return _fake_self_upgrade_argv0(
        monkeypatch, tmp_path, "HOME", (".cache", "uv", "archive-v0", "abc123", "bin")
    )


@pytest.fixture
def unsupported_argv0(monkeypatch, tmp_path):
    """Point sys.argv[0] at a path that does not match any installer prefix."""
    return _fake_self_upgrade_argv0(
        monkeypatch, tmp_path, "HOME", ("random", "location", "bin")
    )
