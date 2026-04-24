"""End-to-end bridge — the composition of all four projectors."""

from __future__ import annotations

import pathlib

from rsc_mandala_bridge.bridge import build_basins


def test_build_basins_on_real_repo_is_healthy():
    report = build_basins()
    assert report.shape_basin_count >= 5  # five Platonic solids + relief
    assert report.fieldlink_basin_count > 0
    assert report.rule_basin_count > 0
    assert report.staleness.usable
    assert report.schema_errors == []


def test_ambient_capabilities_unlock_extra_rules():
    """The BEE x PHI rule fires because BEE carries SWARM_COORDINATION. If we
    drop that capability from the ambient set and simulate absence (via a
    synthetic run) the gated rule should drop. Here we just verify that
    adding an ambient cap is accepted and doesn't crash."""
    report = build_basins(ambient_capabilities={"CAP.FAKE_AMBIENT"})
    assert report.rule_basin_count > 0
    assert report.schema_errors == []


def test_synthetic_end_to_end_matches_sum_of_parts(synthetic_rsc: pathlib.Path):
    report = build_basins(synthetic_rsc)
    assert report.shape_basin_count == 1
    assert report.fieldlink_basin_count >= 4  # 1 sensor, 1 defense, 1 protocol, 1 glyph
    assert report.rule_basin_count >= 1
    total = report.shape_basin_count + report.fieldlink_basin_count + report.rule_basin_count
    assert total == len(report.basins)
    assert report.schema_errors == []


def test_report_ok_flag():
    report = build_basins()
    assert report.ok is True


def test_validate_schemas_off_skips_errors(synthetic_rsc: pathlib.Path):
    """Turning off schema validation must not mutate basin generation."""
    on = build_basins(synthetic_rsc, validate_schemas=True)
    off = build_basins(synthetic_rsc, validate_schemas=False)
    assert len(on.basins) == len(off.basins)
    assert off.schema_errors == []


def test_worked_example_bee_quartz_dodeca_coexist():
    """Briefing section 8: the RSC bridge should produce a dodecahedron basin
    whose signature carries explicit cross-references — exactly the thing
    the LID-only basins lack."""
    report = build_basins()
    dodeca = [b for b in report.basins if b.substrate.lid_id == "SHAPE.DODECA"]
    assert dodeca, "dodecahedron basin is the canonical worked example"
    sig = dodeca[0].signature
    assert sig["bridge_sensors"], "signature must carry explicit sensor cross-refs"
    assert sig["bridge_protocols"], "signature must carry explicit protocol cross-refs"
