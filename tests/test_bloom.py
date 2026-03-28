"""Tests for the Bloom Engine — seed, sprout, branch depths."""
from rosetta_shape_core.bloom import bloom_seed, bloom_sprout, bloom_branch
from rosetta_shape_core.explore import RosettaGraph


# ── Seed depth ────────────────────────────────────────────────────

def test_seed_returns_structure():
    g = RosettaGraph()
    data = bloom_seed(g)
    assert data["depth"] == "seed"
    assert data["entities"]["total"] > 0
    assert data["families"]["total"] == 20
    assert data["shapes"]["total"] == 5
    assert data["bridges"]["total"] > 0
    assert "entry_points" in data


def test_seed_namespaces():
    g = RosettaGraph()
    data = bloom_seed(g)
    ns = data["entities"]["by_namespace"]
    assert "ANIMAL" in ns
    assert ns["ANIMAL"] > 0


def test_seed_shapes_have_sensors():
    g = RosettaGraph()
    data = bloom_seed(g)
    for s in data["shapes"]["list"]:
        assert s["sensor_count"] > 0


# ── Sprout depth ──────────────────────────────────────────────────

def test_sprout_returns_structure():
    g = RosettaGraph()
    data = bloom_sprout(g, "ANIMAL.BEE")
    assert data["depth"] == "sprout"
    assert data["home_base"]["entity_id"] == "ANIMAL.BEE"
    assert "seed_state" in data
    assert "paths" in data
    assert "reachable_shapes" in data
    assert "merge_summary" in data


def test_sprout_seed_state():
    g = RosettaGraph()
    data = bloom_sprout(g, "ANIMAL.BEE")
    ss = data["seed_state"]
    assert ss["mode"] in ("explore", "expand")
    assert ss["energy"] >= 0
    assert 0 <= ss["symmetry"] <= 1.0


def test_sprout_has_paths():
    g = RosettaGraph()
    data = bloom_sprout(g, "ANIMAL.BEE")
    assert data["paths"]["total"] > 0
    assert len(data["paths"]["by_type"]) > 0


def test_sprout_has_reachable_shapes():
    g = RosettaGraph()
    data = bloom_sprout(g, "ANIMAL.BEE")
    assert len(data["reachable_shapes"]) > 0


# ── Branch depth ──────────────────────────────────────────────────

def test_branch_returns_structure():
    g = RosettaGraph()
    data = bloom_branch(g, "ANIMAL.BEE")
    assert data["depth"] == "branch"
    assert "home_base" in data
    assert "paths" in data
    assert "internal_environment" in data
    assert "seed_growth" in data
    assert "shadows" in data
    assert "simulation_preview" in data


def test_branch_shadows_populated():
    g = RosettaGraph()
    data = bloom_branch(g, "ANIMAL.BEE")
    assert data["shadows"]["shadows_found"] > 0


def test_branch_sim_preview():
    g = RosettaGraph()
    data = bloom_branch(g, "ANIMAL.BEE")
    sim = data["simulation_preview"]
    assert sim["available"] is True
    assert "mode" in sim
    assert "energy_after" in sim
    assert "trust" in sim


# ── Edge cases ────────────────────────────────────────────────────

def test_sprout_unknown_entity():
    """Sprout on unknown entity should not crash."""
    g = RosettaGraph()
    data = bloom_sprout(g, "NONEXISTENT.X")
    assert data["depth"] == "sprout"
    assert data["home_base"]["entity_id"] == "NONEXISTENT.X"
