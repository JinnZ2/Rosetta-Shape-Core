"""Performance benchmarks for Rosetta-Shape-Core.

These tests establish baseline timing for core operations so we know
when scaling becomes an issue.  All tests assert completion within a
generous time budget — failures signal a performance regression, not
a correctness bug.

Run with: pytest tests/test_benchmark.py -v
"""
import random
import time

from rosetta_shape_core.explore import RosettaGraph, check_merge, discover, home_base
from rosetta_shape_core.sim import Simulation


def _timed(fn, *args, **kwargs):
    """Run fn and return (result, elapsed_seconds)."""
    start = time.perf_counter()
    result = fn(*args, **kwargs)
    return result, time.perf_counter() - start


# ── Graph loading ────────────────────────────────────────────────

def test_graph_load_time():
    """RosettaGraph should load all data in under 2 seconds."""
    _, elapsed = _timed(RosettaGraph)
    assert elapsed < 2.0, f"Graph load took {elapsed:.2f}s (budget: 2.0s)"


def test_graph_load_entity_count():
    """Verify expected entity count as a scaling baseline."""
    g = RosettaGraph()
    count = len(g.entities)
    assert count >= 50, f"Only {count} entities loaded — expected 50+"
    # Record for future comparison
    assert count < 10000, f"Unexpectedly high: {count} entities"


def test_graph_load_bridge_count():
    """Verify expected bridge count."""
    g = RosettaGraph()
    assert len(g.bridges) >= 15, f"Only {len(g.bridges)} bridges loaded"


# ── Resolution ───────────────────────────────────────────────────

def test_resolve_all_entities_time():
    """Resolving every entity by label should complete quickly."""
    g = RosettaGraph()
    labels = list(g.label_to_id.keys())
    _, elapsed = _timed(lambda: [g.resolve_id(label) for label in labels])
    per_entity = elapsed / max(len(labels), 1) * 1000  # ms
    assert per_entity < 5.0, f"Resolution: {per_entity:.2f}ms/entity (budget: 5ms)"


def test_fuzzy_resolve_time():
    """Fuzzy resolution (substring match) under 10ms per query."""
    g = RosettaGraph()
    queries = ["bee", "oct", "quart", "light", "mycel", "spi", "slime"]
    _, elapsed = _timed(lambda: [g.resolve_id(q) for q in queries])
    per_query = elapsed / len(queries) * 1000
    assert per_query < 10.0, f"Fuzzy resolve: {per_query:.2f}ms/query (budget: 10ms)"


# ── Home base ────────────────────────────────────────────────────

def test_home_base_all_entities_time():
    """Computing home base for all entities under 1 second total."""
    g = RosettaGraph()
    entity_ids = list(g.entities.keys())
    _, elapsed = _timed(lambda: [home_base(g, eid) for eid in entity_ids])
    assert elapsed < 1.0, f"Home base for {len(entity_ids)} entities: {elapsed:.2f}s (budget: 1.0s)"


# ── Discovery ────────────────────────────────────────────────────

def test_discover_depth_1_time():
    """Depth-1 discovery for a single entity under 100ms."""
    g = RosettaGraph()
    eid = g.resolve_id("bee")
    _, elapsed = _timed(discover, g, eid, depth=1)
    assert elapsed < 0.1, f"Discover depth=1: {elapsed*1000:.1f}ms (budget: 100ms)"


def test_discover_depth_2_time():
    """Depth-2 discovery under 500ms."""
    g = RosettaGraph()
    eid = g.resolve_id("bee")
    _, elapsed = _timed(discover, g, eid, depth=2)
    assert elapsed < 0.5, f"Discover depth=2: {elapsed*1000:.1f}ms (budget: 500ms)"


def test_discover_all_entities_depth_1():
    """Depth-1 discovery for ALL entities — batch scaling test."""
    g = RosettaGraph()
    entity_ids = list(g.entities.keys())

    def run_all():
        return [discover(g, eid, depth=1) for eid in entity_ids]

    _, elapsed = _timed(run_all)
    per_entity = elapsed / max(len(entity_ids), 1) * 1000
    assert per_entity < 50.0, (
        f"Discover depth=1: {per_entity:.1f}ms/entity across {len(entity_ids)} entities "
        f"(budget: 50ms/entity)"
    )


# ── Merge checking ───────────────────────────────────────────────

def test_merge_check_all_families_time():
    """Check all family×shape combinations under 500ms."""
    g = RosettaGraph()
    families = list(g.families.keys())
    shapes = ["SHAPE.TETRA", "SHAPE.CUBE", "SHAPE.OCTA", "SHAPE.ICOSA", "SHAPE.DODECA"]

    def run_all():
        return [check_merge(g, f, s) for f in families for s in shapes]

    results, elapsed = _timed(run_all)
    combos = len(families) * len(shapes)
    assert elapsed < 0.5, f"Merge check {combos} combos: {elapsed:.2f}s (budget: 0.5s)"


# ── Bridge index ─────────────────────────────────────────────────

def test_bridge_index_build_time():
    """Bridge index should build in under 100ms."""
    g = RosettaGraph()
    from rosetta_shape_core._bridges import BridgeIndex
    _, elapsed = _timed(BridgeIndex, g.bridges)
    assert elapsed < 0.1, f"Bridge index build: {elapsed*1000:.1f}ms (budget: 100ms)"


# ── Simulation ───────────────────────────────────────────────────

def test_simulation_12_ticks_time():
    """Default 12-tick simulation under 2 seconds."""
    random.seed(42)
    g = RosettaGraph()
    specs = [
        {"query": "bee", "energy": 3.0},
        {"query": "octopus", "energy": 2.0},
        {"query": "mycelium", "energy": 0.5},
        {"query": "quartz", "energy": 1.0},
        {"query": "slime", "energy": 0.3},
        {"query": "lightning", "energy": 4.0},
    ]
    sim = Simulation(specs, g)
    _, elapsed = _timed(sim.run, ticks=12)
    assert elapsed < 2.0, f"12-tick sim with 6 agents: {elapsed:.2f}s (budget: 2.0s)"


def test_simulation_100_ticks_time():
    """Extended 100-tick simulation under 10 seconds."""
    random.seed(42)
    g = RosettaGraph()
    specs = [
        {"query": "bee", "energy": 5.0},
        {"query": "octopus", "energy": 3.0},
        {"query": "mycelium", "energy": 1.0},
        {"query": "quartz", "energy": 2.0},
    ]
    sim = Simulation(specs, g)
    _, elapsed = _timed(sim.run, ticks=100)
    assert elapsed < 10.0, f"100-tick sim with 4 agents: {elapsed:.2f}s (budget: 10.0s)"
