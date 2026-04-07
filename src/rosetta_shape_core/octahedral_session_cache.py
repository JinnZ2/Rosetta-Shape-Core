"""
Octahedral session cache — constraint-coherent caching for Rosetta.

6 octahedral axes define a constraint snapshot. Cache entries are valid
only while live state stays within tolerance of the snapshot. Staleness
propagates along the 12 edges of the octahedron.

Protocols: SNAPSHOT, VALIDATE, INVALIDATE (cascade), EVICT (LRU),
PERSIST (disk), RESTORE (reload + revalidate).

stdlib only — no external dependencies.
"""
from __future__ import annotations

import hashlib
import json
import time
from collections import OrderedDict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


# ── Constraint state vector ────────────────────────────

@dataclass
class OctState:
    """6-axis constraint snapshot (one per octahedral vertex)."""

    axes: Tuple[float, float, float, float, float, float]
    timestamp: float = field(default_factory=time.time)
    source_repo: str = ""

    def key(self) -> str:
        raw = f"{self.axes}:{self.source_repo}"
        return hashlib.sha256(raw.encode()).hexdigest()[:16]

    def distance(self, other: OctState) -> float:
        """L-inf norm — max single-axis drift."""
        return max(abs(a - b) for a, b in zip(self.axes, other.axes))

    def to_dict(self) -> dict:
        return {
            "axes": list(self.axes),
            "timestamp": self.timestamp,
            "source_repo": self.source_repo,
        }

    @classmethod
    def from_dict(cls, d: dict) -> OctState:
        return cls(
            axes=tuple(d["axes"]),
            timestamp=d["timestamp"],
            source_repo=d.get("source_repo", ""),
        )


# ── Cache entry ────────────────────────────────────────

@dataclass
class CacheEntry:
    state_snapshot: OctState
    payload: Any
    created: float = field(default_factory=time.time)
    last_accessed: float = field(default_factory=time.time)
    access_count: int = 0
    ttl_seconds: float = 3600.0
    dependencies: List[str] = field(default_factory=list)

    @property
    def expired(self) -> bool:
        return (time.time() - self.created) > self.ttl_seconds

    def touch(self):
        self.last_accessed = time.time()
        self.access_count += 1


# ── Invalidation graph (octahedral edges) ──────────────

class InvalidationGraph:
    """12 edges of the octahedron define cascade invalidation paths."""

    EDGES = [
        (0, 2), (0, 4), (0, 3), (0, 5),
        (2, 4), (2, 1), (2, 5),
        (1, 3), (1, 5),
        (4, 1), (4, 3),
        (5, 3),
    ]

    def __init__(self):
        self.adjacency: Dict[int, List[int]] = {i: [] for i in range(6)}
        for a, b in self.EDGES:
            self.adjacency[a].append(b)
            self.adjacency[b].append(a)

    def affected_axes(self, changed_axis: int) -> List[int]:
        """BFS from changed axis — all reachable axes need revalidation."""
        visited: set[int] = set()
        queue = [changed_axis]
        while queue:
            ax = queue.pop(0)
            if ax in visited:
                continue
            visited.add(ax)
            queue.extend(self.adjacency[ax])
        return sorted(visited)


# ── Session cache ──────────────────────────────────────

class SessionCache:
    """LRU cache with octahedral constraint coherence."""

    def __init__(
        self,
        max_entries: int = 256,
        tolerance: float = 0.05,
        persist_dir: str = ".oct_cache",
    ):
        self.store: OrderedDict[str, CacheEntry] = OrderedDict()
        self.max_entries = max_entries
        self.tolerance = tolerance
        self.persist_dir = Path(persist_dir)
        self.graph = InvalidationGraph()
        self.stats = {"hits": 0, "misses": 0, "invalidations": 0, "evictions": 0}

    # ── SNAPSHOT ───────────────────────────────────────

    def put(
        self,
        state: OctState,
        payload: Any,
        ttl: float = 3600.0,
        deps: Optional[List[str]] = None,
    ) -> str:
        key = state.key()
        entry = CacheEntry(
            state_snapshot=state,
            payload=payload,
            ttl_seconds=ttl,
            dependencies=deps or [],
        )
        self.store[key] = entry
        self.store.move_to_end(key)
        self._enforce_capacity()
        return key

    # ── GET + VALIDATE ─────────────────────────────────

    def get(
        self, key: str, live_state: Optional[OctState] = None
    ) -> Optional[Any]:
        entry = self.store.get(key)
        if entry is None:
            self.stats["misses"] += 1
            return None

        if entry.expired:
            self._evict(key)
            self.stats["misses"] += 1
            return None

        if live_state and not self._validate(entry, live_state):
            self._evict(key)
            self.stats["misses"] += 1
            return None

        entry.touch()
        self.store.move_to_end(key)
        self.stats["hits"] += 1
        return entry.payload

    # ── VALIDATE ───────────────────────────────────────

    def _validate(self, entry: CacheEntry, live: OctState) -> bool:
        return entry.state_snapshot.distance(live) <= self.tolerance

    # ── INVALIDATE (cascade) ───────────────────────────

    def invalidate_axis(self, axis_index: int, live_state: OctState):
        affected = self.graph.affected_axes(axis_index)
        to_remove = []
        for key, entry in self.store.items():
            snap = entry.state_snapshot
            for ax in affected:
                if abs(snap.axes[ax] - live_state.axes[ax]) > self.tolerance:
                    to_remove.append(key)
                    break
        for key in to_remove:
            self._evict(key)
        self.stats["invalidations"] += len(to_remove)

    def invalidate_repo(self, repo_name: str):
        """Invalidate all entries from a specific source repo."""
        to_remove = [
            k for k, v in self.store.items()
            if v.state_snapshot.source_repo == repo_name
        ]
        for key in to_remove:
            self._evict(key)

    # ── EVICT ──────────────────────────────────────────

    def _evict(self, key: str):
        self.store.pop(key, None)
        self.stats["evictions"] += 1

    def _enforce_capacity(self):
        while len(self.store) > self.max_entries:
            oldest_key = next(iter(self.store))
            self._evict(oldest_key)

    # ── PERSIST ────────────────────────────────────────

    def persist(self, session_id: str = "default") -> str:
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        path = self.persist_dir / f"{session_id}.json"
        data = {
            "session_id": session_id,
            "persisted_at": time.time(),
            "tolerance": self.tolerance,
            "stats": self.stats,
            "entries": {
                k: {
                    "state": v.state_snapshot.to_dict(),
                    "payload": v.payload
                    if isinstance(v.payload, (dict, list, str, int, float, bool, type(None)))
                    else str(v.payload),
                    "created": v.created,
                    "ttl": v.ttl_seconds,
                    "deps": v.dependencies,
                    "access_count": v.access_count,
                }
                for k, v in self.store.items()
            },
        }
        path.write_text(json.dumps(data, indent=2))
        return str(path)

    # ── RESTORE + REVALIDATE ───────────────────────────

    def restore(
        self, session_id: str = "default", live_state: Optional[OctState] = None
    ) -> int:
        path = self.persist_dir / f"{session_id}.json"
        if not path.exists():
            return 0
        data = json.loads(path.read_text())
        loaded = 0
        for key, entry_data in data.get("entries", {}).items():
            state = OctState.from_dict(entry_data["state"])
            if live_state and state.distance(live_state) > self.tolerance:
                continue
            entry = CacheEntry(
                state_snapshot=state,
                payload=entry_data["payload"],
                created=entry_data["created"],
                ttl_seconds=entry_data["ttl"],
                dependencies=entry_data.get("deps", []),
                access_count=entry_data.get("access_count", 0),
            )
            if not entry.expired:
                self.store[key] = entry
                loaded += 1
        return loaded

    # ── Diagnostics ────────────────────────────────────

    def status(self) -> dict:
        return {
            "entries": len(self.store),
            "capacity": self.max_entries,
            "stats": dict(self.stats),
            "oldest": min((e.created for e in self.store.values()), default=None),
            "newest": max((e.created for e in self.store.values()), default=None),
        }
