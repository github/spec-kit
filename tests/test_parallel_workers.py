"""Tests for system-aware parallel worker sizing."""

from types import SimpleNamespace

import pytest

from tests import _parallel
from tests._parallel import compute_recommended_workers, detect_effective_cpu_count
from tests.conftest import (
    _extract_cli_option,
    _args_before_double_dash,
    _has_dist_arg,
    _has_numprocesses_arg,
    _is_plugin_autoload_disabled,
    _is_xdist_worker_process,
    _is_xdist_explicitly_enabled,
    _is_xdist_disabled,
    pytest_load_initial_conftests,
    pytest_configure,
    pytest_report_header,
)


def test_worker_count_cpu_bound_when_memory_is_large():
    settings = compute_recommended_workers(
        cpu_count=8,
        total_memory_bytes=64 * 1024 ** 3,
        available_memory_bytes=16 * 1024 ** 3,
        platform_name="linux",
        max_workers=None,
        tier="medium",
    )
    # cpu_count - 1, capped by linux platform max (8)
    assert settings.workers == 7


def test_worker_count_memory_bound_on_low_memory_system():
    settings = compute_recommended_workers(
        cpu_count=8,
        total_memory_bytes=3 * 1024 ** 3,
        available_memory_bytes=3 * 1024 ** 3,
        platform_name="linux",
        max_workers=None,
        tier="medium",
    )
    # 3 GiB => floor(3 / 1.5) == 2 workers
    assert settings.workers == 2


def test_worker_count_platform_cap_on_windows():
    settings = compute_recommended_workers(
        cpu_count=16,
        total_memory_bytes=64 * 1024 ** 3,
        available_memory_bytes=64 * 1024 ** 3,
        platform_name="win32",
        max_workers=None,
        tier="medium",
    )
    assert settings.workers == 4


def test_worker_count_unknown_platform_uses_most_permissive_known_cap():
    settings = compute_recommended_workers(
        cpu_count=32,
        total_memory_bytes=128 * 1024 ** 3,
        available_memory_bytes=128 * 1024 ** 3,
        platform_name="freebsd14",
        max_workers=None,
        tier="medium",
    )
    assert settings.os_cap == 8


def test_worker_count_honors_parallel_max_workers():
    settings = compute_recommended_workers(
        cpu_count=16,
        total_memory_bytes=64 * 1024 ** 3,
        available_memory_bytes=64 * 1024 ** 3,
        platform_name="linux",
        max_workers=3,
        tier="medium",
    )
    assert settings.workers == 3


def test_worker_count_never_below_one():
    settings = compute_recommended_workers(
        cpu_count=1,
        total_memory_bytes=256 * 1024 ** 2,
        available_memory_bytes=128 * 1024 ** 2,
        platform_name="linux",
        max_workers=None,
        tier="medium",
    )
    assert settings.workers == 1


def test_worker_count_uses_total_memory_when_available_unknown():
    settings = compute_recommended_workers(
        cpu_count=8,
        total_memory_bytes=3 * 1024 ** 3,
        available_memory_bytes=None,
        platform_name="linux",
        max_workers=None,
        tier="medium",
    )
    assert settings.workers == 2


def test_worker_count_treats_zero_available_memory_as_known_boundary():
    settings = compute_recommended_workers(
        cpu_count=8,
        total_memory_bytes=64 * 1024 ** 3,
        available_memory_bytes=0,
        platform_name="linux",
        max_workers=None,
        tier="medium",
    )
    assert settings.workers == 1


def test_low_tier_is_more_conservative_than_high_tier():
    low = compute_recommended_workers(
        cpu_count=12,
        total_memory_bytes=64 * 1024 ** 3,
        available_memory_bytes=64 * 1024 ** 3,
        platform_name="linux",
        max_workers=None,
        tier="low",
    )
    high = compute_recommended_workers(
        cpu_count=12,
        total_memory_bytes=64 * 1024 ** 3,
        available_memory_bytes=64 * 1024 ** 3,
        platform_name="linux",
        max_workers=None,
        tier="high",
    )
    assert low.workers < high.workers


def test_tier_changes_memory_per_worker_budget():
    low = compute_recommended_workers(
        cpu_count=8,
        total_memory_bytes=8 * 1024 ** 3,
        available_memory_bytes=8 * 1024 ** 3,
        platform_name="linux",
        max_workers=None,
        tier="low",
    )
    medium = compute_recommended_workers(
        cpu_count=8,
        total_memory_bytes=8 * 1024 ** 3,
        available_memory_bytes=8 * 1024 ** 3,
        platform_name="linux",
        max_workers=None,
        tier="medium",
    )
    high = compute_recommended_workers(
        cpu_count=8,
        total_memory_bytes=8 * 1024 ** 3,
        available_memory_bytes=8 * 1024 ** 3,
        platform_name="linux",
        max_workers=None,
        tier="high",
    )
    assert low.memory_per_worker_gib > medium.memory_per_worker_gib > high.memory_per_worker_gib


def test_detect_effective_cpu_count_never_below_one():
    assert detect_effective_cpu_count() >= 1


def test_detect_cgroup_cpu_quota_count_v2_parses_cpu_max(monkeypatch):
    def fake_read_text(path):
        values = {
            "/sys/fs/cgroup/cpu.max": "200000 100000",
        }
        return values.get(path)

    monkeypatch.setattr(_parallel, "_read_text", fake_read_text)
    assert _parallel._detect_cgroup_cpu_quota_count() == 2


def test_detect_cgroup_cpu_quota_count_v1_parses_cfs_files(monkeypatch):
    def fake_read_text(path):
        values = {
            "/sys/fs/cgroup/cpu.max": None,
            "/sys/fs/cgroup/cpu/cpu.cfs_quota_us": "300000",
            "/sys/fs/cgroup/cpu/cpu.cfs_period_us": "100000",
        }
        return values.get(path)

    monkeypatch.setattr(_parallel, "_read_text", fake_read_text)
    assert _parallel._detect_cgroup_cpu_quota_count() == 3


def test_detect_cgroup_cpu_quota_count_v1_parses_cpuacct_cpu_mount(monkeypatch):
    def fake_read_text(path):
        values = {
            "/sys/fs/cgroup/cpu.max": None,
            "/sys/fs/cgroup/cpu/cpu.cfs_quota_us": None,
            "/sys/fs/cgroup/cpu/cpu.cfs_period_us": None,
            "/sys/fs/cgroup/cpu,cpuacct/cpu.cfs_quota_us": None,
            "/sys/fs/cgroup/cpu,cpuacct/cpu.cfs_period_us": None,
            "/sys/fs/cgroup/cpuacct,cpu/cpu.cfs_quota_us": "250000",
            "/sys/fs/cgroup/cpuacct,cpu/cpu.cfs_period_us": "100000",
        }
        return values.get(path)

    monkeypatch.setattr(_parallel, "_read_text", fake_read_text)
    assert _parallel._detect_cgroup_cpu_quota_count() == 2


def test_detect_cgroup_cpu_quota_count_v2_floors_fractional_quota(monkeypatch):
    def fake_read_text(path):
        values = {
            "/sys/fs/cgroup/cpu.max": "110000 100000",
        }
        return values.get(path)

    monkeypatch.setattr(_parallel, "_read_text", fake_read_text)
    assert _parallel._detect_cgroup_cpu_quota_count() == 1


def test_detect_cgroup_cpu_quota_count_v1_floors_fractional_quota(monkeypatch):
    def fake_read_text(path):
        values = {
            "/sys/fs/cgroup/cpu.max": None,
            "/sys/fs/cgroup/cpu/cpu.cfs_quota_us": "110000",
            "/sys/fs/cgroup/cpu/cpu.cfs_period_us": "100000",
        }
        return values.get(path)

    monkeypatch.setattr(_parallel, "_read_text", fake_read_text)
    assert _parallel._detect_cgroup_cpu_quota_count() == 1


def test_detect_total_memory_uses_sc_pagesize_fallback(monkeypatch):
    def fake_sysconf(name):
        if name == "SC_PAGE_SIZE":
            raise OSError("unsupported")
        if name == "SC_PAGESIZE":
            return 4096
        if name == "SC_PHYS_PAGES":
            return 10
        raise ValueError(name)

    monkeypatch.setattr(_parallel.os, "sysconf", fake_sysconf, raising=False)
    monkeypatch.setattr(_parallel.sys, "platform", "linux")
    assert _parallel.detect_total_memory_bytes() == 40960


def test_parallel_report_header_formats_zero_memory_values():
    settings = _parallel.ParallelSettings(
        tier="medium",
        workers=1,
        cpu_cap=1,
        memory_cap=1,
        os_cap=4,
        effective_cpus=1,
        total_memory_bytes=0,
        available_memory_bytes=0,
        memory_per_worker_gib=1.5,
    )
    config = SimpleNamespace(_spec_kit_parallel_settings=settings)
    header = pytest_report_header(config)
    assert header is not None
    assert "avail_mem=0.0GiB" in header
    assert "total_mem=0.0GiB" in header


def test_parallel_report_header_uses_effective_workers_when_overridden():
    settings = _parallel.ParallelSettings(
        tier="medium",
        workers=6,
        cpu_cap=6,
        memory_cap=8,
        os_cap=8,
        effective_cpus=8,
        total_memory_bytes=16 * 1024 ** 3,
        available_memory_bytes=8 * 1024 ** 3,
        memory_per_worker_gib=1.5,
    )
    config = SimpleNamespace(
        _spec_kit_parallel_settings=settings,
        _spec_kit_parallel_effective_workers="auto",
    )
    header = pytest_report_header(config)
    assert header is not None
    assert "workers=auto" in header


def test_is_xdist_disabled_detects_split_plugin_flag():
    assert _is_xdist_disabled(["--parallel", "-p", "no:xdist"])


def test_is_xdist_disabled_detects_compact_plugin_flag():
    assert _is_xdist_disabled(["--parallel", "-pno:xdist"])


def test_is_xdist_explicitly_enabled_detects_split_plugin_flag():
    assert _is_xdist_explicitly_enabled(["--parallel", "-p", "xdist"])


def test_is_xdist_explicitly_enabled_detects_compact_plugin_flag():
    assert _is_xdist_explicitly_enabled(["--parallel", "-pxdist"])


def test_is_xdist_explicitly_enabled_detects_qualified_plugin_name():
    assert _is_xdist_explicitly_enabled(["--parallel", "-p", "xdist.plugin"])


def test_is_xdist_explicitly_enabled_ignores_non_xdist_plugin_names():
    assert not _is_xdist_explicitly_enabled(["--parallel", "-p", "myxdisthelper"])


def test_numprocesses_and_dist_detection_ignore_args_after_double_dash():
    args = ["--parallel", "--", "-n", "4", "--dist", "load"]
    assert not _has_numprocesses_arg(args)
    assert not _has_dist_arg(args)


def test_extract_cli_option_ignores_args_after_double_dash():
    args = ["--parallel", "--", "--parallel-tier", "high"]
    assert _extract_cli_option(args, "--parallel-tier", "medium") == "medium"


def test_args_before_double_dash_excludes_parallel_after_sentinel():
    args = ["-q", "--", "--parallel"]
    assert "--parallel" not in _args_before_double_dash(args)


def test_load_initial_conftests_ignores_parallel_after_sentinel():
    args = ["-q", "--", "--parallel"]
    original = list(args)

    pytest_load_initial_conftests(None, None, args)

    assert args == original


def test_load_initial_conftests_injects_before_sentinel(monkeypatch):
    args = ["--parallel", "--", "tests/test_parallel_workers.py"]

    monkeypatch.setattr("tests.conftest._has_xdist_installed", lambda: True)
    monkeypatch.setattr("tests.conftest._is_plugin_autoload_disabled", lambda: False)
    monkeypatch.setattr("tests.conftest._is_xdist_disabled", lambda _args: False)
    monkeypatch.setattr("tests.conftest._has_numprocesses_arg", lambda _args: False)
    monkeypatch.setattr("tests.conftest._compute_parallel_settings_from_args", lambda _args: SimpleNamespace(workers=3))

    pytest_load_initial_conftests(None, None, args)

    assert args == ["--parallel", "-n", "3", "--dist", "worksteal", "--", "tests/test_parallel_workers.py"]


def test_load_initial_conftests_does_not_inject_for_single_worker(monkeypatch):
    args = ["--parallel", "--", "tests/test_parallel_workers.py"]

    monkeypatch.setattr("tests.conftest._has_xdist_installed", lambda: True)
    monkeypatch.setattr("tests.conftest._is_plugin_autoload_disabled", lambda: False)
    monkeypatch.setattr("tests.conftest._is_xdist_disabled", lambda _args: False)
    monkeypatch.setattr("tests.conftest._has_numprocesses_arg", lambda _args: False)
    monkeypatch.setattr("tests.conftest._compute_parallel_settings_from_args", lambda _args: SimpleNamespace(workers=1))

    pytest_load_initial_conftests(None, None, args)

    assert args == ["--parallel", "--", "tests/test_parallel_workers.py"]


def test_load_initial_conftests_raises_for_invalid_parallel_max_workers(monkeypatch):
    args = ["--parallel", "--parallel-max-workers", "not-a-number"]

    monkeypatch.setattr("tests.conftest._has_xdist_installed", lambda: True)
    monkeypatch.setattr("tests.conftest._is_plugin_autoload_disabled", lambda: False)
    monkeypatch.setattr("tests.conftest._is_xdist_disabled", lambda _args: False)
    monkeypatch.setattr("tests.conftest._has_numprocesses_arg", lambda _args: False)

    with pytest.raises(pytest.UsageError, match="--parallel-max-workers must be an integer >= 1"):
        pytest_load_initial_conftests(None, None, args)


def test_load_initial_conftests_raises_for_parallel_max_workers_below_one(monkeypatch):
    args = ["--parallel", "--parallel-max-workers", "0"]

    monkeypatch.setattr("tests.conftest._has_xdist_installed", lambda: True)
    monkeypatch.setattr("tests.conftest._is_plugin_autoload_disabled", lambda: False)
    monkeypatch.setattr("tests.conftest._is_xdist_disabled", lambda _args: False)
    monkeypatch.setattr("tests.conftest._has_numprocesses_arg", lambda _args: False)

    with pytest.raises(pytest.UsageError, match="--parallel-max-workers must be >= 1"):
        pytest_load_initial_conftests(None, None, args)


def test_is_xdist_worker_process_detects_worker_env(monkeypatch):
    monkeypatch.setenv("PYTEST_XDIST_WORKER", "gw0")
    assert _is_xdist_worker_process()


def test_load_initial_conftests_noops_in_xdist_worker(monkeypatch):
    args = ["--parallel"]
    monkeypatch.setenv("PYTEST_XDIST_WORKER", "gw0")

    pytest_load_initial_conftests(None, None, args)

    assert args == ["--parallel"]


def test_parallel_settings_computed_once_across_early_and_configure(monkeypatch):
    calls = {"count": 0}

    def fake_compute(*, cpu_count, total_memory_bytes, available_memory_bytes, platform_name, max_workers, tier):
        calls["count"] += 1
        return SimpleNamespace(
            tier=tier,
            workers=3,
            cpu_cap=3,
            memory_cap=3,
            os_cap=8,
            effective_cpus=cpu_count,
            total_memory_bytes=total_memory_bytes,
            available_memory_bytes=available_memory_bytes,
            memory_per_worker_gib=1.5,
        )

    monkeypatch.setattr("tests.conftest.compute_recommended_workers", fake_compute)
    monkeypatch.setattr("tests.conftest.detect_effective_cpu_count", lambda: 8)
    monkeypatch.setattr("tests.conftest.detect_total_memory_bytes", lambda: 8 * 1024 ** 3)
    monkeypatch.setattr("tests.conftest.detect_available_memory_bytes", lambda: 8 * 1024 ** 3)
    monkeypatch.setattr("tests.conftest._has_xdist_installed", lambda: True)
    monkeypatch.setattr("tests.conftest._is_plugin_autoload_disabled", lambda: False)
    monkeypatch.setattr("tests.conftest._is_xdist_disabled", lambda _args: False)
    monkeypatch.setattr("tests.conftest._has_numprocesses_arg", lambda _args: False)

    args = ["--parallel"]
    pytest_load_initial_conftests(None, None, args)

    config = SimpleNamespace(
        option=SimpleNamespace(numprocesses=3, dist="worksteal"),
        invocation_params=SimpleNamespace(args=("--parallel",)),
        getoption=lambda opt: {
            "--parallel": True,
            "--parallel-max-workers": None,
            "--parallel-tier": "medium",
        }[opt],
    )

    pytest_configure(config)

    assert calls["count"] == 1


def test_pytest_configure_parallel_single_worker_noops_without_xdist(monkeypatch):
    settings = SimpleNamespace(
        tier="medium",
        workers=1,
        cpu_cap=1,
        memory_cap=1,
        os_cap=8,
        effective_cpus=1,
        total_memory_bytes=2 * 1024 ** 3,
        available_memory_bytes=2 * 1024 ** 3,
        memory_per_worker_gib=1.5,
    )
    monkeypatch.setattr("tests.conftest._EARLY_PARALLEL_SETTINGS", settings)

    config = SimpleNamespace(
        option=SimpleNamespace(dist="worksteal"),
        invocation_params=SimpleNamespace(args=("--parallel",)),
        getoption=lambda opt: {
            "--parallel": True,
            "--parallel-max-workers": None,
            "--parallel-tier": "medium",
        }[opt],
    )

    pytest_configure(config)

    assert getattr(config, "_spec_kit_parallel_effective_workers") == 1
    assert getattr(config, "_spec_kit_parallel_settings").workers == 1


def test_is_plugin_autoload_disabled_truthy(monkeypatch):
    monkeypatch.setenv("PYTEST_DISABLE_PLUGIN_AUTOLOAD", "1")
    assert _is_plugin_autoload_disabled()


def test_is_plugin_autoload_disabled_false_when_unset(monkeypatch):
    monkeypatch.delenv("PYTEST_DISABLE_PLUGIN_AUTOLOAD", raising=False)
    assert not _is_plugin_autoload_disabled()
