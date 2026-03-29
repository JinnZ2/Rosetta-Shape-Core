"""Tests for the Constraint-Geometry Agent Framework."""
import pytest
from fractions import Fraction

from rosetta_shape_core.constraint_agent import (
    ConstraintAgent,
    DiscoveryMap,
    ResourceBudget,
    _to_fraction,
    _fraction_amplitudes,
    _apply_saturation,
    _shannon_entropy_fraction,
)
from rosetta_shape_core.explore import RosettaGraph, SEED_VERTICES


@pytest.fixture
def graph():
    return RosettaGraph()


@pytest.fixture
def bee_agent(graph):
    agent = ConstraintAgent(seed_id="bee", graph=graph)
    agent.set_resource_budget(compute=500, bandwidth=100)
    return agent


@pytest.fixture
def quartz_agent(graph):
    agent = ConstraintAgent(seed_id="quartz", graph=graph)
    agent.set_resource_budget(compute=500, bandwidth=100)
    return agent


# ── Fraction arithmetic ───────────────────────────────────────────

class TestFractionArithmetic:
    def test_to_fraction_int(self):
        assert _to_fraction(3) == Fraction(3)

    def test_to_fraction_float(self):
        f = _to_fraction(0.5)
        assert isinstance(f, Fraction)
        assert f == Fraction(1, 2)

    def test_to_fraction_string(self):
        assert _to_fraction("3/4") == Fraction(3, 4)

    def test_to_fraction_passthrough(self):
        f = Fraction(7, 11)
        assert _to_fraction(f) is f

    def test_fraction_amplitudes_are_fractions(self):
        amps = _fraction_amplitudes(["FAMILY.F01", "FAMILY.F04"])
        assert all(isinstance(a, Fraction) for a in amps)

    def test_fraction_amplitudes_sum_to_one(self):
        amps = _fraction_amplitudes(["FAMILY.F01", "FAMILY.F04"])
        assert sum(amps) == Fraction(1)

    def test_fraction_amplitudes_empty(self):
        amps = _fraction_amplitudes([])
        assert sum(amps) == Fraction(0)

    def test_saturation_caps(self):
        # Create amplitudes where one vertex dominates
        amps = [Fraction(9, 10)] + [Fraction(1, 50)] * 5
        saturated = _apply_saturation(amps)
        assert all(a <= Fraction(45, 100) for a in saturated)

    def test_entropy_nonnegative(self):
        amps = _fraction_amplitudes(["FAMILY.F01", "FAMILY.F09"])
        h = _shannon_entropy_fraction(amps)
        assert h >= Fraction(0)


# ── ResourceBudget ────────────────────────────────────────────────

class TestResourceBudget:
    def test_set_and_spend(self):
        b = ResourceBudget()
        b.set("compute", 100)
        assert b.spend("compute", 30)
        assert b.remaining_safe("compute") == Fraction(70)

    def test_overspend_rejected(self):
        b = ResourceBudget()
        b.set("compute", 10)
        assert not b.spend("compute", 11)

    def test_unconstrained_resource(self):
        b = ResourceBudget()
        assert b.spend("memory", 999)  # no constraint set

    def test_is_exhausted(self):
        b = ResourceBudget()
        b.set("compute", 5)
        b.spend("compute", 5)
        assert b.is_exhausted()

    def test_not_exhausted(self):
        b = ResourceBudget()
        b.set("compute", 100)
        assert not b.is_exhausted()

    def test_reset(self):
        b = ResourceBudget()
        b.set("compute", 100)
        b.spend("compute", 50)
        b.reset()
        assert b.remaining_safe("compute") == Fraction(100)

    def test_snapshot(self):
        b = ResourceBudget()
        b.set("compute", 100)
        b.set("bandwidth", 50)
        b.spend("compute", 30)
        snap = b.snapshot()
        assert snap["compute"] == Fraction(70)
        assert snap["bandwidth"] == Fraction(50)

    def test_utilization(self):
        b = ResourceBudget()
        b.set("compute", 100)
        b.spend("compute", 25)
        assert b.utilization("compute") == Fraction(1, 4)

    def test_names(self):
        b = ResourceBudget()
        b.set("compute", 100)
        b.set("bandwidth", 50)
        assert sorted(b.names()) == ["bandwidth", "compute"]


# ── ConstraintAgent creation ──────────────────────────────────────

class TestAgentCreation:
    def test_agent_resolves_entity(self, bee_agent):
        assert bee_agent.seed_id == "ANIMAL.BEE"

    def test_agent_has_home_shape(self, bee_agent):
        assert bee_agent.home_shape is not None

    def test_agent_starts_in_seed_state(self, bee_agent):
        assert bee_agent.state == "seed"

    def test_agent_amplitudes_are_fractions(self, bee_agent):
        for v, a in bee_agent.amplitudes.items():
            assert isinstance(a, Fraction), f"{v} amplitude is not Fraction"

    def test_agent_amplitudes_sum_to_one(self, bee_agent):
        total = sum(bee_agent.amplitudes.values())
        assert total == Fraction(1)

    def test_agent_entropy_is_fraction(self, bee_agent):
        assert isinstance(bee_agent.entropy, Fraction)

    def test_agent_has_families(self, bee_agent):
        assert len(bee_agent.families) > 0

    def test_agent_cycle_starts_at_zero(self, bee_agent):
        assert bee_agent.cycle_count == 0


# ── Bloom ─────────────────────────────────────────────────────────

class TestBloom:
    def test_bloom_returns_discovery_map(self, bee_agent):
        dm = bee_agent.bloom(depth=1)
        assert isinstance(dm, DiscoveryMap)

    def test_bloom_changes_state(self, bee_agent):
        bee_agent.bloom(depth=1)
        assert bee_agent.state == "bloomed"

    def test_bloom_increments_cycle(self, bee_agent):
        bee_agent.bloom(depth=1)
        assert bee_agent.cycle_count == 1

    def test_bloom_finds_paths(self, bee_agent):
        dm = bee_agent.bloom(depth=1)
        assert len(dm.paths) > 0

    def test_bloom_discovers_shapes(self, bee_agent):
        dm = bee_agent.bloom(depth=1)
        assert len(dm.visited_shapes) > 0

    def test_bloom_costs_compute(self, bee_agent):
        before = bee_agent.budget.remaining_safe("compute")
        bee_agent.bloom(depth=1)
        after = bee_agent.budget.remaining_safe("compute")
        assert after < before

    def test_bloom_costs_bandwidth(self, bee_agent):
        before = bee_agent.budget.remaining_safe("bandwidth")
        bee_agent.bloom(depth=1)
        after = bee_agent.budget.remaining_safe("bandwidth")
        assert after < before

    def test_bloom_depth2_finds_more(self, bee_agent, graph):
        agent1 = ConstraintAgent(seed_id="bee", graph=graph)
        agent1.set_resource_budget(compute=500, bandwidth=100)
        dm1 = agent1.bloom(depth=1)

        agent2 = ConstraintAgent(seed_id="bee", graph=graph)
        agent2.set_resource_budget(compute=500, bandwidth=100)
        dm2 = agent2.bloom(depth=2)

        assert len(dm2.paths) >= len(dm1.paths)

    def test_bloom_no_budget_returns_empty_map(self, graph):
        agent = ConstraintAgent(seed_id="bee", graph=graph)
        agent.set_resource_budget(compute=0)
        dm = agent.bloom(depth=1)
        assert dm.depth == 0
        assert len(dm.paths) == 0

    def test_bloom_partial_on_bandwidth_exhaustion(self, graph):
        agent = ConstraintAgent(seed_id="bee", graph=graph)
        agent.set_resource_budget(compute=500, bandwidth=3)
        dm = agent.bloom(depth=1)
        assert len(dm.paths) <= 3


# ── Explore ───────────────────────────────────────────────────────

class TestExplore:
    def test_explore_without_bloom_returns_empty(self, bee_agent):
        result = bee_agent.explore()
        assert result == []

    def test_explore_after_bloom_finds_shadows(self, bee_agent):
        bee_agent.bloom(depth=1)
        shadows = bee_agent.explore()
        assert isinstance(shadows, list)

    def test_explore_changes_state(self, bee_agent):
        bee_agent.bloom(depth=1)
        bee_agent.explore()
        assert bee_agent.state == "exploring"

    def test_explore_costs_compute(self, bee_agent):
        bee_agent.bloom(depth=1)
        before = bee_agent.budget.remaining_safe("compute")
        bee_agent.explore()
        after = bee_agent.budget.remaining_safe("compute")
        assert after < before


# ── Compress ──────────────────────────────────────────────────────

class TestCompress:
    def test_compress_returns_memory_entry(self, bee_agent):
        bee_agent.bloom(depth=1)
        mem = bee_agent.compress()
        assert "cycle" in mem
        assert "shapes_reached" in mem
        assert "paths_found" in mem

    def test_compress_changes_state(self, bee_agent):
        bee_agent.bloom(depth=1)
        bee_agent.compress()
        assert bee_agent.state == "compressed"

    def test_compress_preserves_map_in_history(self, bee_agent):
        bee_agent.bloom(depth=1)
        bee_agent.compress()
        assert len(bee_agent.maps) == 1

    def test_compress_clears_current_map(self, bee_agent):
        bee_agent.bloom(depth=1)
        bee_agent.compress()
        assert bee_agent.current_map is None

    def test_compress_adds_to_memory(self, bee_agent):
        bee_agent.bloom(depth=1)
        bee_agent.compress()
        assert len(bee_agent.memory) == 1


# ── Full cycle ────────────────────────────────────────────────────

class TestFullCycle:
    def test_run_cycle_returns_summary(self, bee_agent):
        result = bee_agent.run_cycle(depth=1)
        assert "cycle" in result
        assert "map_summary" in result
        assert "shadows_found" in result

    def test_run_cycle_ends_in_compressed(self, bee_agent):
        bee_agent.run_cycle(depth=1)
        assert bee_agent.state == "compressed"

    def test_multiple_cycles_build_memory(self, bee_agent):
        bee_agent.run_cycle(depth=1)
        bee_agent.run_cycle(depth=1)
        assert len(bee_agent.memory) == 2
        assert bee_agent.cycle_count == 2

    def test_run_cycles_stops_on_budget(self, graph):
        agent = ConstraintAgent(seed_id="bee", graph=graph)
        # Very tight bandwidth — first cycle uses ~11, exhausts on cycle 2
        agent.set_resource_budget(compute=500, bandwidth=12)
        results = agent.run_cycles(10, depth=1)
        # Should stop before 10 because bandwidth exhausts
        assert len(results) < 10

    def test_re_bloom_after_compress(self, bee_agent):
        dm1 = bee_agent.bloom(depth=1)
        bee_agent.compress()
        dm2 = bee_agent.bloom(depth=1)
        # Same seed → same discovery structure (paths may differ slightly due to graph traversal)
        assert dm2.visited_shapes == dm1.visited_shapes

    def test_different_entities_different_maps(self, bee_agent, quartz_agent):
        dm_bee = bee_agent.bloom(depth=1)
        dm_quartz = quartz_agent.bloom(depth=1)
        # Different seeds should find different (or at least not identical) paths
        assert dm_bee.paths != dm_quartz.paths or dm_bee.visited_shapes != dm_quartz.visited_shapes


# ── Serialization ─────────────────────────────────────────────────

class TestSerialization:
    def test_to_dict_structure(self, bee_agent):
        d = bee_agent.to_dict()
        assert d["seed_id"] == "ANIMAL.BEE"
        assert "amplitudes" in d
        assert "entropy" in d
        assert "should_expand" in d
        assert d["state"] == "seed"

    def test_to_dict_after_cycle(self, bee_agent):
        bee_agent.run_cycle(depth=1)
        d = bee_agent.to_dict()
        assert d["state"] == "compressed"
        assert d["cycle"] == 1
        assert d["maps_archived"] == 1

    def test_amplitudes_are_string_fractions(self, bee_agent):
        d = bee_agent.to_dict()
        for v, a in d["amplitudes"].items():
            Fraction(a)  # should not raise


# ── DiscoveryMap ──────────────────────────────────────────────────

class TestDiscoveryMap:
    def test_empty_map_summary(self):
        dm = DiscoveryMap()
        s = dm.summary()
        assert s["paths_found"] == 0
        assert s["shapes_reached"] == []
        assert s["depth"] == 0

    def test_map_preserves_amplitudes(self, bee_agent):
        dm = bee_agent.bloom(depth=1)
        assert len(dm.amplitudes) == 6
        assert all(isinstance(a, Fraction) for a in dm.amplitudes)
