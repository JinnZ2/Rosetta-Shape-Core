"""Tests for octahedral session cache."""
from __future__ import annotations

import json
import time
import tempfile
import pytest

from rosetta_shape_core.octahedral_session_cache import (
    OctState,
    CacheEntry,
    InvalidationGraph,
    SessionCache,
)


# ── OctState ──────────────────────────────────────────

class TestOctState:
    def test_key_deterministic(self):
        s = OctState(axes=(1.0, 0.0, 0.0, 0.0, 0.0, -1.0), source_repo="test")
        assert s.key() == s.key()

    def test_key_changes_with_axes(self):
        s1 = OctState(axes=(1.0, 0.0, 0.0, 0.0, 0.0, -1.0))
        s2 = OctState(axes=(0.0, 1.0, 0.0, 0.0, 0.0, -1.0))
        assert s1.key() != s2.key()

    def test_key_changes_with_repo(self):
        s1 = OctState(axes=(1.0, 0.0, 0.0, 0.0, 0.0, 0.0), source_repo="a")
        s2 = OctState(axes=(1.0, 0.0, 0.0, 0.0, 0.0, 0.0), source_repo="b")
        assert s1.key() != s2.key()

    def test_distance_zero_for_identical(self):
        s = OctState(axes=(1.0, 2.0, 3.0, 4.0, 5.0, 6.0))
        assert s.distance(s) == 0.0

    def test_distance_linf(self):
        s1 = OctState(axes=(1.0, 0.0, 0.0, 0.0, 0.0, 0.0))
        s2 = OctState(axes=(1.0, 0.0, 0.0, 0.5, 0.0, 0.0))
        assert s1.distance(s2) == 0.5

    def test_roundtrip_dict(self):
        s = OctState(axes=(1.0, -0.3, 0.7, -0.7, 0.3, -1.0), source_repo="test")
        restored = OctState.from_dict(s.to_dict())
        assert restored.axes == s.axes
        assert restored.source_repo == s.source_repo


# ── InvalidationGraph ─────────────────────────────────

class TestInvalidationGraph:
    def test_all_axes_reachable(self):
        """Octahedron is connected — any axis reaches all 6."""
        g = InvalidationGraph()
        for start in range(6):
            affected = g.affected_axes(start)
            assert len(affected) == 6

    def test_twelve_edges(self):
        assert len(InvalidationGraph.EDGES) == 12

    def test_adjacency_bidirectional(self):
        g = InvalidationGraph()
        for a, b in InvalidationGraph.EDGES:
            assert b in g.adjacency[a]
            assert a in g.adjacency[b]


# ── CacheEntry ────────────────────────────────────────

class TestCacheEntry:
    def test_not_expired_initially(self):
        state = OctState(axes=(0,) * 6)
        entry = CacheEntry(state_snapshot=state, payload="data", ttl_seconds=100)
        assert not entry.expired

    def test_expired_after_ttl(self):
        state = OctState(axes=(0,) * 6)
        entry = CacheEntry(state_snapshot=state, payload="data", ttl_seconds=0)
        # TTL=0 means created == now, but (now - created) > 0 is immediately true
        # after even tiny elapsed time
        time.sleep(0.01)
        assert entry.expired

    def test_touch_increments_count(self):
        state = OctState(axes=(0,) * 6)
        entry = CacheEntry(state_snapshot=state, payload="data")
        assert entry.access_count == 0
        entry.touch()
        assert entry.access_count == 1
        entry.touch()
        assert entry.access_count == 2


# ── SessionCache ──────────────────────────────────────

class TestSessionCache:
    def _state(self, x=0.0, repo=""):
        return OctState(axes=(x, 0.0, 0.0, 0.0, 0.0, 0.0), source_repo=repo)

    def test_put_and_get(self):
        cache = SessionCache()
        state = self._state(1.0)
        key = cache.put(state, payload={"result": 42})
        assert cache.get(key) == {"result": 42}

    def test_get_nonexistent_returns_none(self):
        cache = SessionCache()
        assert cache.get("nonexistent") is None
        assert cache.stats["misses"] == 1

    def test_get_counts_hits(self):
        cache = SessionCache()
        key = cache.put(self._state(), payload="x")
        cache.get(key)
        cache.get(key)
        assert cache.stats["hits"] == 2

    def test_validate_within_tolerance(self):
        cache = SessionCache(tolerance=0.1)
        state = self._state(1.0)
        key = cache.put(state, payload="ok")
        live = self._state(1.05)  # drift 0.05 < tolerance 0.1
        assert cache.get(key, live_state=live) == "ok"

    def test_validate_beyond_tolerance(self):
        cache = SessionCache(tolerance=0.01)
        state = self._state(1.0)
        key = cache.put(state, payload="ok")
        live = self._state(1.5)  # drift 0.5 > tolerance 0.01
        assert cache.get(key, live_state=live) is None

    def test_ttl_eviction(self):
        cache = SessionCache()
        state = self._state()
        key = cache.put(state, payload="data", ttl=0)
        time.sleep(0.01)
        assert cache.get(key) is None
        assert cache.stats["evictions"] == 1

    def test_lru_eviction(self):
        cache = SessionCache(max_entries=2)
        k1 = cache.put(self._state(1.0), payload="first")
        k2 = cache.put(self._state(2.0), payload="second")
        k3 = cache.put(self._state(3.0), payload="third")
        # k1 should be evicted (oldest)
        assert cache.get(k1) is None
        assert cache.get(k2) == "second"
        assert cache.get(k3) == "third"

    def test_invalidate_axis_cascades(self):
        cache = SessionCache(tolerance=0.05)
        state = self._state(1.0)
        key = cache.put(state, payload="data")
        drifted = OctState(axes=(2.0, 0.0, 0.0, 0.0, 0.0, 0.0))
        cache.invalidate_axis(0, drifted)
        assert cache.get(key) is None
        assert cache.stats["invalidations"] >= 1

    def test_invalidate_repo(self):
        cache = SessionCache()
        k1 = cache.put(self._state(1.0, repo="repo-a"), payload="a")
        k2 = cache.put(self._state(2.0, repo="repo-b"), payload="b")
        cache.invalidate_repo("repo-a")
        assert cache.get(k1) is None
        assert cache.get(k2) == "b"

    def test_status(self):
        cache = SessionCache(max_entries=100)
        cache.put(self._state(), payload="x")
        status = cache.status()
        assert status["entries"] == 1
        assert status["capacity"] == 100

    def test_persist_and_restore(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = SessionCache(persist_dir=tmpdir)
            state = self._state(1.0, repo="test-repo")
            key = cache.put(state, payload={"result": [1, 2, 3]}, ttl=3600)

            cache.persist("test_session")

            cache2 = SessionCache(persist_dir=tmpdir)
            loaded = cache2.restore("test_session", live_state=self._state(1.01))
            assert loaded == 1
            assert cache2.get(key) == {"result": [1, 2, 3]}

    def test_restore_skips_drifted(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = SessionCache(tolerance=0.05, persist_dir=tmpdir)
            cache.put(self._state(1.0), payload="data")
            cache.persist("sess")

            cache2 = SessionCache(tolerance=0.05, persist_dir=tmpdir)
            loaded = cache2.restore("sess", live_state=self._state(5.0))
            assert loaded == 0

    def test_restore_nonexistent_session(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = SessionCache(persist_dir=tmpdir)
            assert cache.restore("does_not_exist") == 0
