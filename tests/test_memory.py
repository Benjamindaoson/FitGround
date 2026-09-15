"""Memory guard tests."""

from fitground.data.memory import MemoryTracker, RSS_LIMIT_BYTES, current_rss_bytes


def test_rss_readable() -> None:
    rss = current_rss_bytes()
    assert rss > 0


def test_memory_tracker_peak() -> None:
    tracker = MemoryTracker()
    tracker.sample("eval-00000-of-00020")
    assert tracker.global_peak_bytes > 0
    tracker.finish_shard("eval-00000-of-00020")
    assert "eval-00000-of-00020" in tracker.shard_peaks


def test_rss_limit_constant() -> None:
    assert RSS_LIMIT_BYTES == int(1.5 * 1024**3)
