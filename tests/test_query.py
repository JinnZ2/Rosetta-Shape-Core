"""Tests for the query module (fuzzy ontology search)."""
from rosetta_shape_core.query import (
    get_node,
    load_all_nodes,
    prompt_fragment,
    search,
)

# ── Node loading ─────────────────────────────────────────────────

def test_load_all_nodes():
    nodes = load_all_nodes()
    assert len(nodes) > 0
    # Should have both families and principles
    has_family = any(k.startswith("FAMILY.") for k in nodes)
    has_principle = any(k.startswith("PRINCIPLE.") for k in nodes)
    assert has_family
    assert has_principle


def test_load_all_nodes_have_required_fields():
    nodes = load_all_nodes()
    for nid, node in nodes.items():
        assert "id" in node
        assert "name" in node
        assert node["id"] == nid


def test_get_node_exact():
    node = get_node("FAMILY.F01")
    assert node is not None
    assert node["id"] == "FAMILY.F01"


def test_get_node_missing():
    assert get_node("FAMILY.F99") is None


# ── Search ───────────────────────────────────────────────────────

def test_search_exact_id():
    results = search("FAMILY.F01")
    assert len(results) == 1
    assert results[0][1]["id"] == "FAMILY.F01"


def test_search_keyword():
    results = search("resonance", top=3)
    assert len(results) > 0
    # F01 is "Resonance" — should appear in results
    ids = [r[1]["id"] for r in results]
    assert "FAMILY.F01" in ids


def test_search_no_match():
    results = search("xyznonexistent999", top=3)
    assert len(results) == 0


def test_search_multi_keyword():
    results = search("energy conservation", top=5)
    assert len(results) > 0


def test_search_top_limits_results():
    results = search("the", top=2)
    assert len(results) <= 2


# ── Prompt fragment ──────────────────────────────────────────────

def test_prompt_fragment_returns_string():
    frag = prompt_fragment("symmetry")
    assert isinstance(frag, str)
    assert "rosetta-ontology" in frag


def test_prompt_fragment_no_match():
    frag = prompt_fragment("xyznonexistent999")
    assert "no nodes matched" in frag
