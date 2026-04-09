"""Tests for the bridge resolver (_bridges.py)."""
from rosetta_shape_core._bridges import (
    BridgeIndex, _scan_ids, _extract_shape_targets,
    _extract_family_refs, _extract_entity_refs,
)
from rosetta_shape_core.explore import RosettaGraph


# ── ID scanning ──────────────────────────────────────────────────

def test_scan_ids_shape():
    assert _scan_ids("SHAPE.OCTA vertex 0 (+X)") == ["SHAPE.OCTA"]


def test_scan_ids_family():
    assert _scan_ids("maps to FAMILY.F01 and FAMILY.F09") == ["FAMILY.F01", "FAMILY.F09"]


def test_scan_ids_principle():
    assert _scan_ids("PRINCIPLE.P10 (uncertainty)") == ["PRINCIPLE.P10"]


def test_scan_ids_entity():
    ids = _scan_ids("CAP.SWARM_COORDINATION and ANIMAL.BEE")
    assert "CAP.SWARM_COORDINATION" in ids
    assert "ANIMAL.BEE" in ids


def test_scan_ids_prefix_filter():
    assert _scan_ids("SHAPE.OCTA and FAMILY.F01", prefix="SHAPE.") == ["SHAPE.OCTA"]


def test_scan_ids_no_match():
    assert _scan_ids("plain text with no IDs") == []


# ── Extraction from mappings ─────────────────────────────────────

def test_extract_shape_targets():
    mapping = {"to": "SHAPE.ICOSA families F01-F20", "notes": "Maps to SHAPE.DODECA too"}
    shapes = _extract_shape_targets(mapping)
    assert "SHAPE.ICOSA" in shapes
    assert "SHAPE.DODECA" in shapes


def test_extract_family_refs():
    mapping = {"rosetta_families": ["FAMILY.F01", "FAMILY.F09"], "notes": "also PRINCIPLE.P06"}
    refs = _extract_family_refs(mapping)
    assert "FAMILY.F01" in refs
    assert "FAMILY.F09" in refs
    assert "PRINCIPLE.P06" in refs


def test_extract_entity_refs():
    mapping = {"to": "CAP.GEOMETRIC_ENCODING", "from": "Bio-cognitive-tools-suite"}
    refs = _extract_entity_refs(mapping)
    assert "CAP.GEOMETRIC_ENCODING" in refs


# ── BridgeIndex ──────────────────────────────────────────────────

def test_bridge_index_from_graph():
    g = RosettaGraph()
    assert g.bridge_index is not None
    stats = g.bridge_index.stats()
    assert stats["bridges_indexed"] > 0
    assert stats["shapes_indexed"] > 0


def test_bridge_index_shapes_are_clean_ids():
    """Shape keys should be clean IDs like SHAPE.OCTA, not descriptive text."""
    g = RosettaGraph()
    for shape_key in g.bridge_index.by_shape:
        # Should match SHAPE.WORD pattern, no spaces
        assert shape_key.startswith("SHAPE.")
        assert " " not in shape_key


def test_bridge_index_stats():
    bridges = {
        "TEST_BRIDGE": {
            "id": "BRIDGE.TEST",
            "target": {"shape_anchors": ["SHAPE.OCTA"]},
            "mappings": [
                {"from": "test input", "to": "SHAPE.ICOSA", "type": "ALIGNS_WITH",
                 "notes": "connects FAMILY.F01"},
            ],
        }
    }
    idx = BridgeIndex(bridges)
    assert idx.stats()["bridges_indexed"] == 1
    assert "SHAPE.ICOSA" in idx.by_shape
    assert "FAMILY.F01" in idx.by_family


def test_bridge_index_endorses_merge():
    bridges = {
        "TEST_BRIDGE": {
            "id": "BRIDGE.TEST",
            "mappings": [
                {"from": "test", "to": "SHAPE.OCTA", "type": "ALIGNS_WITH",
                 "notes": "FAMILY.F05 on SHAPE.OCTA"},
            ],
        }
    }
    idx = BridgeIndex(bridges)
    result = idx.endorses_merge("FAMILY.F05", "SHAPE.OCTA")
    assert result is not None
    assert result["bridge"] == "TEST_BRIDGE"


def test_bridge_index_endorses_merge_negative():
    bridges = {
        "TEST_BRIDGE": {
            "id": "BRIDGE.TEST",
            "mappings": [
                {"from": "test", "to": "SHAPE.OCTA", "type": "ALIGNS_WITH",
                 "notes": "FAMILY.F05 on SHAPE.OCTA"},
            ],
        }
    }
    idx = BridgeIndex(bridges)
    assert idx.endorses_merge("FAMILY.F99", "SHAPE.TETRA") is None


def test_bridge_index_resolve_paths():
    bridges = {
        "TEST_BRIDGE": {
            "id": "BRIDGE.TEST",
            "mappings": [
                {"from": "ANIMAL.BEE", "to": "SHAPE.ICOSA", "type": "IS_A",
                 "notes": "Bee maps to icosahedron"},
            ],
        }
    }
    idx = BridgeIndex(bridges)
    paths = idx.resolve_paths("ANIMAL.BEE", ["FAMILY.F01"])
    assert len(paths) >= 1
    assert any(p["target_shape"] == "SHAPE.ICOSA" for p in paths)


def test_bridge_index_resolve_paths_via_family():
    bridges = {
        "TEST_BRIDGE": {
            "id": "BRIDGE.TEST",
            "mappings": [
                {"from": "resonance module", "to": "SHAPE.DODECA", "type": "ALIGNS_WITH",
                 "notes": "FAMILY.F01 connects to dodecahedron"},
            ],
        }
    }
    idx = BridgeIndex(bridges)
    paths = idx.resolve_paths("ANIMAL.OWL", ["FAMILY.F01"])
    assert len(paths) >= 1
    assert any(p["target_shape"] == "SHAPE.DODECA" for p in paths)
