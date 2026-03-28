"""Tests for the exploration engine, seed physics, shadow hunting, and economic instruments."""
import math
from rosetta_shape_core.explore import (
    RosettaGraph,
    home_base,
    discover,
    check_merge,
    compute_seed_state,
    hunt_shadows,
    map_internal_environment,
    SENSOR_REGISTRY,
    PAD_STATES,
    FAMILY_SENSOR_CONTEXT,
    FAMILY_VERTEX_LOADING,
    SEED_VERTICES,
    ECONOMIC_EQUATIONS,
    SIGNAL_DISTORTIONS,
    NARRATIVE_PHYSICS_FAMILIES,
    EQUATION_BOUNDARIES,
)


# ── Graph loading ──────────────────────────────────────────────────

def test_graph_loads():
    """RosettaGraph loads without errors and has data."""
    g = RosettaGraph()
    assert len(g.entities) > 0
    assert len(g.families) > 0
    assert len(g.shape_profiles) == 5  # 5 Platonic solids
    assert len(g.bridges) > 0


def test_graph_resolve_id_exact():
    g = RosettaGraph()
    assert g.resolve_id("ANIMAL.BEE") == "ANIMAL.BEE"


def test_graph_resolve_id_fuzzy():
    g = RosettaGraph()
    assert g.resolve_id("bee") is not None
    assert "BEE" in g.resolve_id("bee")


def test_graph_resolve_id_missing():
    g = RosettaGraph()
    assert g.resolve_id("NONEXISTENT.ENTITY") is None


# ── Home base ──────────────────────────────────────────────────────

def test_home_base_bee():
    g = RosettaGraph()
    hb = home_base(g, "ANIMAL.BEE")
    assert hb["entity_id"] == "ANIMAL.BEE"
    assert hb["home_shape"] is not None
    assert len(hb["entity_families"]) > 0


def test_home_base_unknown_entity():
    g = RosettaGraph()
    hb = home_base(g, "NONEXISTENT.X")
    assert hb["entity_id"] == "NONEXISTENT.X"
    # Should not crash, just return empty-ish result


# ── Discovery ──────────────────────────────────────────────────────

def test_discover_finds_paths():
    g = RosettaGraph()
    paths = discover(g, "ANIMAL.BEE", depth=1)
    assert len(paths) > 0
    types = {p["type"] for p in paths}
    # Bee should have at least family affinities
    assert "family_affinity" in types


def test_discover_depth_2_adds_more():
    g = RosettaGraph()
    paths_1 = discover(g, "ANIMAL.BEE", depth=1)
    paths_2 = discover(g, "ANIMAL.BEE", depth=2)
    assert len(paths_2) >= len(paths_1)


# ── Merge gates ────────────────────────────────────────────────────

def test_check_merge_primary():
    g = RosettaGraph()
    # F09 (Geometry) has primary = SHAPE.OCTA
    result = check_merge(g, "FAMILY.F09", "SHAPE.OCTA")
    assert result["status"] == "primary"


def test_check_merge_unknown_family():
    g = RosettaGraph()
    result = check_merge(g, "FAMILY.FAKE", "SHAPE.TETRA")
    assert result["status"] == "unknown"


def test_check_merge_unexplored():
    g = RosettaGraph()
    # Some family-shape combo that isn't defined
    result = check_merge(g, "FAMILY.F01", "SHAPE.TETRA")
    # Should be unexplored, secondary, or merged — not crash
    assert result["status"] in ("primary", "merged", "secondary", "blocked", "unexplored")


# ── Seed growth engine ─────────────────────────────────────────────

def test_seed_state_basic():
    seed = compute_seed_state(["FAMILY.F01", "FAMILY.F02"])
    assert "amplitudes" in seed
    assert len(seed["amplitudes"]) == 6
    assert seed["entropy"] >= 0
    assert seed["max_entropy"] > 0
    assert seed["mode"] in ("explore", "expand")


def test_seed_state_empty_families():
    seed = compute_seed_state([])
    assert seed["energy"] == 0
    assert seed["mode"] == "expand"  # no energy = can't explore


def test_seed_state_many_families():
    """More families = more energy = more likely to explore."""
    seed_few = compute_seed_state(["FAMILY.F01"])
    seed_many = compute_seed_state(["FAMILY.F01", "FAMILY.F02", "FAMILY.F03", "FAMILY.F04", "FAMILY.F05"])
    assert seed_many["energy"] > seed_few["energy"]


def test_seed_amplitudes_sum_to_one():
    seed = compute_seed_state(["FAMILY.F01", "FAMILY.F09", "FAMILY.F12"])
    total = sum(seed["amplitudes"].values())
    assert abs(total - 1.0) < 0.01


def test_seed_saturation():
    """No vertex should exceed SATURATION_FRACTION (0.45)."""
    seed = compute_seed_state(["FAMILY.F01", "FAMILY.F02", "FAMILY.F19"])
    for amp in seed["amplitudes"].values():
        assert amp <= 0.451  # small tolerance


def test_seed_symmetry_range():
    seed = compute_seed_state(["FAMILY.F01"])
    assert 0 <= seed["symmetry"] <= 1.0


# ── Shadow hunting ─────────────────────────────────────────────────

def test_hunt_shadows_returns_structure():
    g = RosettaGraph()
    seed = compute_seed_state(["FAMILY.F09", "FAMILY.F12"])
    result = hunt_shadows(g, "ANIMAL.BEE", seed)
    assert "shadows_found" in result
    assert "shadows" in result
    assert "phi_coherence" in result
    assert isinstance(result["shadows"], list)


def test_hunt_shadows_finds_equation_boundaries():
    """Entities with families in EQUATION_BOUNDARIES should get boundary shadows."""
    g = RosettaGraph()
    # F12 (Networks) is in EQUATION_BOUNDARIES
    seed = compute_seed_state(["FAMILY.F12"])
    result = hunt_shadows(g, "ANIMAL.BEE", seed)
    boundary_shadows = [s for s in result["shadows"] if s["detector"] == "SHADOW.BOUNDARY"]
    assert len(boundary_shadows) > 0


def test_hunt_shadows_finds_economic_instruments():
    """Entities with overlapping families should get economic equation shadows."""
    g = RosettaGraph()
    seed = compute_seed_state(["FAMILY.F12"])
    result = hunt_shadows(g, "ANIMAL.BEE", seed)
    econ = [s for s in result["shadows"] if s["detector"] == "SHADOW.ECONOMIC_INSTRUMENTS"]
    assert len(econ) > 0
    # F12 should give access to DI and HHI
    eq_ids = [e["equation"] for e in econ[0]["detail"]]
    assert "MECON.HHI" in eq_ids


def test_hunt_shadows_finds_narrative_physics():
    """Entities with F09/F19/F03/F05/F06 should get narrative physics capability."""
    g = RosettaGraph()
    seed = compute_seed_state(["FAMILY.F09"])
    result = hunt_shadows(g, "ANIMAL.BEE", seed)
    narr = [s for s in result["shadows"] if s["detector"] == "SHADOW.NARRATIVE_PHYSICS"]
    assert len(narr) > 0


# ── Internal environment ───────────────────────────────────────────

def test_internal_environment():
    g = RosettaGraph()
    hb = home_base(g, "ANIMAL.BEE")
    paths = discover(g, "ANIMAL.BEE")
    env = map_internal_environment(g, "ANIMAL.BEE", hb, paths)
    assert "home_sensors" in env
    assert "family_contexts" in env
    assert "pad_states" in env
    assert len(env["home_sensors"]) > 0


def test_pad_states_count():
    assert len(PAD_STATES) == 8  # octahedral: 2^3


def test_sensor_registry_completeness():
    """All 5 shapes should have sensors."""
    for shape in ["SHAPE.TETRA", "SHAPE.CUBE", "SHAPE.OCTA", "SHAPE.DODECA", "SHAPE.ICOSA"]:
        assert shape in SENSOR_REGISTRY
        assert len(SENSOR_REGISTRY[shape]) > 0


def test_family_sensor_context_completeness():
    """All 21 families should have sensor context."""
    for i in range(1, 22):
        fid = f"FAMILY.F{i:02d}"
        assert fid in FAMILY_SENSOR_CONTEXT


# ── Constants ──────────────────────────────────────────────────────

def test_seed_vertices_count():
    assert len(SEED_VERTICES) == 6  # octahedron has 6 vertices


def test_family_vertex_loading_coverage():
    """All 21 families should have vertex loading."""
    for i in range(1, 22):
        fid = f"FAMILY.F{i:02d}"
        assert fid in FAMILY_VERTEX_LOADING


def test_economic_equations_count():
    assert len(ECONOMIC_EQUATIONS) == 13


def test_narrative_physics_families_exist():
    assert len(NARRATIVE_PHYSICS_FAMILIES) > 0
