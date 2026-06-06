"""Tests for system-aware parallel worker sizing."""

from types import SimpleNamespace

from tests import _parallel
from tests._parallel import compute_recommended_workers, detect_effective_cpu_count
from tests.conftest import (
    _extract_cli_option,
    _has_dist_arg,
    _has_numprocesses_arg,
    _is_plugin_autoload_disabled,
    _is_xdist_explicitly_enabled,
    _is_xdist_disabled,
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


def test_numprocesses_and_dist_detection_ignore_args_after_double_dash():
    args = ["--parallel", "--", "-n", "4", "--dist", "load"]
    assert not _has_numprocesses_arg(args)
    assert not _has_dist_arg(args)


def test_extract_cli_option_ignores_args_after_double_dash():
    args = ["--parallel", "--", "--parallel-tier", "high"]
    assert _extract_cli_option(args, "--parallel-tier", "medium") == "medium"


def test_is_plugin_autoload_disabled_truthy(monkeypatch):
    monkeypatch.setenv("PYTEST_DISABLE_PLUGIN_AUTOLOAD", "1")
    assert _is_plugin_autoload_disabled()


def test_is_plugin_autoload_disabled_false_when_unset(monkeypatch):
    monkeypatch.delenv("PYTEST_DISABLE_PLUGIN_AUTOLOAD", raising=False)
    assert not _is_plugin_autoload_disabled()
