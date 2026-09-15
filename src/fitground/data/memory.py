"""Process memory monitoring and safety limits."""

from __future__ import annotations

import gc
import sys
from dataclasses import dataclass, field

# 1.5 GiB hard stop — stay below OOM on 3.8GiB VPS.
RSS_LIMIT_BYTES = int(1.5 * 1024**3)


def _windows_rss_bytes() -> int:
    import ctypes
    from ctypes import wintypes

    class PROCESS_MEMORY_COUNTERS(ctypes.Structure):
        _fields_ = [
            ("cb", wintypes.DWORD),
            ("PageFaultCount", wintypes.DWORD),
            ("PeakWorkingSetSize", ctypes.c_size_t),
            ("WorkingSetSize", ctypes.c_size_t),
            ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
            ("QuotaPagedPoolUsage", ctypes.c_size_t),
            ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
            ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
            ("PagefileUsage", ctypes.c_size_t),
            ("PeakPagefileUsage", ctypes.c_size_t),
        ]

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    psapi = ctypes.WinDLL("psapi", use_last_error=True)
    kernel32.GetCurrentProcess.restype = ctypes.c_void_p
    psapi.GetProcessMemoryInfo.argtypes = [
        ctypes.c_void_p,
        ctypes.POINTER(PROCESS_MEMORY_COUNTERS),
        wintypes.DWORD,
    ]
    psapi.GetProcessMemoryInfo.restype = wintypes.BOOL
    counters = PROCESS_MEMORY_COUNTERS()
    counters.cb = ctypes.sizeof(PROCESS_MEMORY_COUNTERS)
    ok = psapi.GetProcessMemoryInfo(
        kernel32.GetCurrentProcess(),
        ctypes.byref(counters),
        counters.cb,
    )
    if not ok:
        return 0
    return int(counters.WorkingSetSize)


def current_rss_bytes() -> int:
    """Current resident set size (Linux /proc or Windows working set)."""
    if sys.platform == "win32":
        return _windows_rss_bytes()
    try:
        with open("/proc/self/status", encoding="ascii") as fh:
            for line in fh:
                if line.startswith("VmRSS:"):
                    return int(line.split()[1]) * 1024
    except OSError:
        pass
    return 0


def release_memory() -> None:
    """Explicitly encourage freeing large temporaries between batches."""
    gc.collect()


@dataclass
class MemoryTracker:
    """Track RSS peaks per shard and enforce limit."""

    limit_bytes: int = RSS_LIMIT_BYTES
    shard_peak_bytes: int = 0
    global_peak_bytes: int = 0
    shard_peaks: dict[str, int] = field(default_factory=dict)

    def sample(self, shard_id: str | None = None) -> int:
        rss = current_rss_bytes()
        if rss > self.global_peak_bytes:
            self.global_peak_bytes = rss
        if shard_id is not None and rss > self.shard_peak_bytes:
            self.shard_peak_bytes = rss
        return rss

    def finish_shard(self, shard_id: str) -> None:
        self.shard_peaks[shard_id] = self.shard_peak_bytes
        self.shard_peak_bytes = 0

    def check_limit(self, shard_id: str | None = None) -> None:
        rss = self.sample(shard_id)
        if rss >= self.limit_bytes:
            raise MemoryLimitError(
                f"RSS {rss / 1e9:.3f} GiB >= limit {self.limit_bytes / 1e9:.3f} GiB "
                f"(shard={shard_id})"
            )


class MemoryLimitError(RuntimeError):
    """Raised when RSS exceeds safe threshold."""
