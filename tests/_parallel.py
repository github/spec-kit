"""Parallel-test worker sizing helpers for pytest."""

from __future__ import annotations

import ctypes
import os
import sys
from dataclasses import dataclass
from typing import Literal


ParallelTier = Literal["low", "medium", "high"]


def _read_text(path: str) -> str | None:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read().strip()
    except OSError:
        return None


def _read_meminfo_available_bytes() -> int | None:
    raw = _read_text("/proc/meminfo")
    if not raw:
        return None
    for line in raw.splitlines():
        if line.startswith("MemAvailable:"):
            parts = line.split()
            if len(parts) >= 2:
                try:
                    return int(parts[1]) * 1024
                except ValueError:
                    return None
    return None


def _detect_cgroup_available_memory_bytes() -> int | None:
    # cgroup v2
    limit_raw = _read_text("/sys/fs/cgroup/memory.max")
    used_raw = _read_text("/sys/fs/cgroup/memory.current")

    if limit_raw and used_raw and limit_raw != "max":
        try:
            limit = int(limit_raw)
            used = int(used_raw)
            if limit > 0:
                return max(0, limit - used)
        except ValueError:
            pass

    # cgroup v1
    limit_raw = _read_text("/sys/fs/cgroup/memory/memory.limit_in_bytes")
    used_raw = _read_text("/sys/fs/cgroup/memory/memory.usage_in_bytes")
    if limit_raw and used_raw:
        try:
            limit = int(limit_raw)
            used = int(used_raw)
            if limit > 0 and limit < (1 << 60):  # ignore effectively-unlimited sentinel values
                return max(0, limit - used)
        except ValueError:
            pass

    return None


def _detect_cgroup_cpu_quota_count() -> int | None:
    # cgroup v2
    quota_raw = _read_text("/sys/fs/cgroup/cpu.max")
    if quota_raw:
        parts = quota_raw.split()
        if len(parts) == 2 and parts[0] != "max":
            try:
                quota = int(parts[0])
                period = int(parts[1])
                if quota > 0 and period > 0:
                    return max(1, quota // period)
            except ValueError:
                pass

    # cgroup v1
    # Some distros/runtimes mount under /sys/fs/cgroup/cpu/, while others use
    # /sys/fs/cgroup/cpu,cpuacct/.
    quota_candidates = (
        "/sys/fs/cgroup/cpu/cpu.cfs_quota_us",
        "/sys/fs/cgroup/cpu,cpuacct/cpu.cfs_quota_us",
        "/sys/fs/cgroup/cpuacct,cpu/cpu.cfs_quota_us",
    )
    period_candidates = (
        "/sys/fs/cgroup/cpu/cpu.cfs_period_us",
        "/sys/fs/cgroup/cpu,cpuacct/cpu.cfs_period_us",
        "/sys/fs/cgroup/cpuacct,cpu/cpu.cfs_period_us",
    )

    for quota_path, period_path in zip(quota_candidates, period_candidates):
        quota_raw = _read_text(quota_path)
        period_raw = _read_text(period_path)
        if not quota_raw or not period_raw:
            continue
        try:
            quota = int(quota_raw)
            period = int(period_raw)
            # cgroup v1 uses -1 for unlimited quota.
            if quota > 0 and period > 0:
                return max(1, quota // period)
        except ValueError:
            continue

    return None


def detect_effective_cpu_count() -> int:
    """Best-effort effective CPU count considering affinity and container quotas."""
    cpus = max(1, int(os.cpu_count() or 1))

    if hasattr(os, "sched_getaffinity"):
        try:
            cpus = min(cpus, max(1, len(os.sched_getaffinity(0))))
        except OSError:
            pass

    cgroup_cpus = _detect_cgroup_cpu_quota_count()
    if cgroup_cpus is not None:
        cpus = min(cpus, cgroup_cpus)

    return max(1, cpus)


def detect_total_memory_bytes() -> int | None:
    """Best-effort total system memory in bytes, or None if unavailable."""
    if sys.platform == "win32":
        class MEMORYSTATUSEX(ctypes.Structure):
            _fields_ = [
                ("dwLength", ctypes.c_ulong),
                ("dwMemoryLoad", ctypes.c_ulong),
                ("ullTotalPhys", ctypes.c_ulonglong),
                ("ullAvailPhys", ctypes.c_ulonglong),
                ("ullTotalPageFile", ctypes.c_ulonglong),
                ("ullAvailPageFile", ctypes.c_ulonglong),
                ("ullTotalVirtual", ctypes.c_ulonglong),
                ("ullAvailVirtual", ctypes.c_ulonglong),
                ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
            ]

        stats = MEMORYSTATUSEX()
        stats.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
        if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stats)) == 0:
            return None
        return int(stats.ullTotalPhys)

    if hasattr(os, "sysconf"):
        page_size = None
        for key in ("SC_PAGE_SIZE", "SC_PAGESIZE"):
            try:
                value = int(os.sysconf(key))
            except (ValueError, OSError):
                continue
            if value > 0:
                page_size = value
                break
        if page_size is not None:
            try:
                pages = int(os.sysconf("SC_PHYS_PAGES"))
                if pages > 0:
                    return page_size * pages
            except (ValueError, OSError):
                return None

    return None


def detect_available_memory_bytes() -> int | None:
    """Best-effort currently available memory in bytes, or None if unavailable."""
    if sys.platform == "win32":
        class MEMORYSTATUSEX(ctypes.Structure):
            _fields_ = [
                ("dwLength", ctypes.c_ulong),
                ("dwMemoryLoad", ctypes.c_ulong),
                ("ullTotalPhys", ctypes.c_ulonglong),
                ("ullAvailPhys", ctypes.c_ulonglong),
                ("ullTotalPageFile", ctypes.c_ulonglong),
                ("ullAvailPageFile", ctypes.c_ulonglong),
                ("ullTotalVirtual", ctypes.c_ulonglong),
                ("ullAvailVirtual", ctypes.c_ulonglong),
                ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
            ]

        stats = MEMORYSTATUSEX()
        stats.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
        if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stats)) == 0:
            return None
        return int(stats.ullAvailPhys)

    mem_available = _read_meminfo_available_bytes()
    cgroup_available = _detect_cgroup_available_memory_bytes()

    if mem_available is not None and cgroup_available is not None:
        return min(mem_available, cgroup_available)
    if mem_available is not None:
        return mem_available
    if cgroup_available is not None:
        return cgroup_available

    return None


@dataclass(frozen=True)
class ParallelSettings:
    tier: ParallelTier
    workers: int
    cpu_cap: int
    memory_cap: int
    os_cap: int
    effective_cpus: int
    total_memory_bytes: int | None
    available_memory_bytes: int | None
    memory_per_worker_gib: float


@dataclass(frozen=True)
class ParallelTierConfig:
    cpu_reserve: int
    memory_per_worker_gib: float
    os_cap_by_platform: dict[str, int]


TIER_CONFIGS: dict[ParallelTier, ParallelTierConfig] = {
    "low": ParallelTierConfig(
        cpu_reserve=2,
        memory_per_worker_gib=2.5,
        os_cap_by_platform={"win32": 2, "darwin": 4, "linux": 6},
    ),
    "medium": ParallelTierConfig(
        cpu_reserve=1,
        memory_per_worker_gib=1.5,
        os_cap_by_platform={"win32": 4, "darwin": 6, "linux": 8},
    ),
    "high": ParallelTierConfig(
        cpu_reserve=0,
        memory_per_worker_gib=1.0,
        os_cap_by_platform={"win32": 6, "darwin": 10, "linux": 16},
    ),
}


def compute_recommended_workers(
    *,
    cpu_count: int,
    total_memory_bytes: int | None,
    available_memory_bytes: int | None,
    platform_name: str,
    max_workers: int | None,
    tier: ParallelTier = "medium",
) -> ParallelSettings:
    """Compute parallel worker settings from detected system constraints."""
    cfg = TIER_CONFIGS[tier]
    cpus = max(1, int(cpu_count))
    cpu_cap = max(1, cpus - cfg.cpu_reserve)

    # Bound workers by currently available memory to avoid swap thrash.
    memory_cap = cpu_cap
    if available_memory_bytes is not None:
        memory_basis = available_memory_bytes
    else:
        memory_basis = total_memory_bytes
    if memory_basis is not None and memory_basis > 0:
        gib = memory_basis / (1024 ** 3)
        memory_cap = max(1, int(gib // cfg.memory_per_worker_gib))
    elif memory_basis is not None:
        memory_cap = 1

    os_cap = cfg.os_cap_by_platform.get(platform_name)
    if os_cap is None:
        # Unknown platforms should default to the most permissive known cap,
        # not the strictest Windows cap.
        os_cap = max(cfg.os_cap_by_platform.values())

    workers = min(cpu_cap, memory_cap, os_cap)

    if max_workers is not None:
        workers = min(workers, max(1, int(max_workers)))

    return ParallelSettings(
        tier=tier,
        workers=max(1, workers),
        cpu_cap=cpu_cap,
        memory_cap=max(1, memory_cap),
        os_cap=os_cap,
        effective_cpus=cpus,
        total_memory_bytes=total_memory_bytes,
        available_memory_bytes=available_memory_bytes,
        memory_per_worker_gib=cfg.memory_per_worker_gib,
    )
