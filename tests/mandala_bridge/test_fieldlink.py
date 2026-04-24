"""FieldlinkProjector — cross-ontology basins from the curated bridge table."""

from __future__ import annotations

import pathlib

from rsc_mandala_bridge.fieldlink_projector import FieldlinkProjector


def test_synthetic_fixture_emits_expected_basin_families(synthetic_rsc: pathlib.Path):
    basins = FieldlinkProjector(synthetic_rsc).project_all()
    domains = {b.domain for b in basins}
    assert domains == {"emotional_sensing", "symbolic_defense", "governance", "symbolic_notation"}

    by_name = {b.substrate.name: b for b in basins}
    sensor = by_name["sensor.emotion.pride"]
    assert sensor.substrate.lid_id == "EMO:PRIDE"
    assert sensor.signature["anchor_shape"] == "SHAPE.TINY"
    assert sensor.signature["anchor_families"] == ["foundation"]

    defense = by_name["protocol.defense.def_se_01"]
    assert defense.substrate.lid_id == "DEF:DEF_SE_01"
    assert defense.signature["label"] == "Self-deception"


def test_real_repo_substrates_carry_lid_ids():
    real_root = pathlib.Path(__file__).resolve().parents[2]
    basins = FieldlinkProjector(real_root).project_all()

    by_name = {b.substrate.name: b for b in basins}
    assert "sensor.emotion.admiration" in by_name
    trust = by_name["sensor.emotion.trust"]
    assert trust.substrate.lid_id == "EMO:TRUST"

    # Protocols get the AUDIT: namespace per the briefing's convention.
    audit = [b for b in basins if b.substrate.name == "protocol.audit.partnership_ethics_v1_0"]
    assert audit and audit[0].substrate.lid_id == "AUDIT:PARTNERSHIP_ETHICS_V1_0"


def test_duplicate_anchors_are_folded_not_dropped(synthetic_rsc: pathlib.Path):
    """A sensor anchored to multiple shapes keeps every anchor in the signature."""
    import json

    bridges = synthetic_rsc / "bridges" / "rosetta-bridges.json"
    data = json.loads(bridges.read_text(encoding="utf-8"))
    data["map"].append({
        "shape": "SHAPE.OTHER",
        "families": ["structure"],
        "sensors": ["pride"],
        "sensor_glyphs": [],
        "defenses": [],
        "defense_names": [],
        "protocols": [],
    })
    bridges.write_text(json.dumps(data), encoding="utf-8")

    basins = FieldlinkProjector(synthetic_rsc).project_all()
    pride_basins = [b for b in basins if b.substrate.name == "sensor.emotion.pride"]
    assert len(pride_basins) == 1, "duplicate sensor basins should be deduped"
    extras = pride_basins[0].signature.get("additional_anchors") or []
    assert any(a["shape"] == "SHAPE.OTHER" for a in extras)


def test_active_stage_prefers_merge_stage_when_available(synthetic_rsc: pathlib.Path):
    proj = FieldlinkProjector(synthetic_rsc)
    # Fixture only has atlas/remote populated; active stage should be that.
    active = proj.active_stage()
    assert active is not None
    assert active.name == "remote"

    # Add a merge_stage with one file and verify it takes priority.
    stage = synthetic_rsc / ".fieldlink" / "merge_stage"
    stage.mkdir(parents=True)
    (stage / "fresh.json").write_text("{}", encoding="utf-8")
    active = FieldlinkProjector(synthetic_rsc).active_stage()
    assert active is not None
    assert "merge_stage" in str(active)
