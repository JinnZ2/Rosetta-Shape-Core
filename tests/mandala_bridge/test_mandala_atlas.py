"""Mandala-atlas walker — the raw staged entities, not the bridge table."""

from __future__ import annotations

import json
import pathlib

from rsc_mandala_bridge.fieldlink_projector import FieldlinkProjector


def test_real_repo_walks_mandala_shapes_glyphs_sensors():
    real_root = pathlib.Path(__file__).resolve().parents[2]
    basins = FieldlinkProjector(real_root).project_mandala_atlas()
    names = {b.substrate.name for b in basins}

    # All 8 octahedral states
    for i, label in enumerate(["x", "x", "y", "y", "z", "z", "diagonal_a", "diagonal_b"]):
        # states 0/1 dedupe to mandala.octahedron.x; 2/3 to .y; etc.
        assert any(n.startswith("mandala.octahedron.") for n in names)

    # Problem types
    for pid in ("factorization", "sat", "tsp", "graph_coloring", "optimization"):
        assert f"mandala.problem.{pid}" in names, f"missing problem {pid}"

    # Mandala-glyph basins
    assert any(n.startswith("glyph.mandala.state.") for n in names)
    assert any(n.startswith("glyph.mandala.problem.") for n in names)
    assert any(n.startswith("glyph.mandala.energy.") for n in names)
    assert any(n.startswith("glyph.mandala.structure.") for n in names)

    # Sensors (mandala/sensors.json)
    assert any(n.startswith("mandala.sensor.energy_total") for n in names)


def test_mandala_atlas_prefers_merge_stage(tmp_path: pathlib.Path):
    # Committed atlas says state label "+x".
    committed = tmp_path / "atlas" / "remote" / "mandala"
    committed.mkdir(parents=True)
    (committed / "shapes.json").write_text(json.dumps({
        "octahedral_angles": [
            {"state": 0, "theta": 0.0, "phi_angle": 0.0, "label": "+x"},
        ],
    }), encoding="utf-8")

    # Fresh pull overrides with "fresh-x".
    staged = tmp_path / ".fieldlink" / "merge_stage" / "atlas" / "remote" / "mandala"
    staged.mkdir(parents=True)
    (staged / "shapes.json").write_text(json.dumps({
        "octahedral_angles": [
            {"state": 0, "theta": 0.0, "phi_angle": 0.0, "label": "fresh-x"},
        ],
    }), encoding="utf-8")

    basins = FieldlinkProjector(tmp_path).project_mandala_atlas()
    assert basins, "expected at least one state basin from merge_stage"
    labels = {b.signature["label"] for b in basins}
    assert "fresh-x" in labels and "+x" not in labels


def test_mandala_atlas_skips_when_absent(tmp_path: pathlib.Path):
    # No atlas staged at all
    assert FieldlinkProjector(tmp_path).project_mandala_atlas() == []


def test_project_all_merges_bridge_and_atlas(synthetic_rsc: pathlib.Path):
    """Adding a mandala atlas to the synthetic fixture should boost basin count."""
    baseline = FieldlinkProjector(synthetic_rsc).project_all()

    atlas = synthetic_rsc / "atlas" / "remote" / "mandala"
    atlas.mkdir(parents=True, exist_ok=True)
    (atlas / "shapes.json").write_text(json.dumps({
        "octahedral_angles": [
            {"state": 0, "theta": 0.0, "phi_angle": 0.0, "label": "+x"},
        ],
        "problem_types": [
            {"id": "OPTIMIZATION", "encoding": "direct_landscape", "min_cells": "varies"},
        ],
    }), encoding="utf-8")

    enriched = FieldlinkProjector(synthetic_rsc).project_all()
    assert len(enriched) > len(baseline)
    names = {b.substrate.name for b in enriched}
    assert "mandala.octahedron.x" in names
    assert "mandala.problem.optimization" in names
