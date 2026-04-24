"""ShapeProjector — shape → Basin correctness."""

from __future__ import annotations

import json
import pathlib

from rsc_mandala_bridge.shape_projector import ShapeProjector
from rsc_mandala_bridge.types import Basin


def test_dodecahedron_matches_briefing_worked_example():
    """The dodecahedron basin carries every cross-reference the briefing lists."""
    real_root = pathlib.Path(__file__).resolve().parents[2]
    dodeca = json.loads((real_root / "shapes" / "dodecahedron.json").read_text(encoding="utf-8"))

    basin = ShapeProjector(real_root).project(dodeca)

    assert basin.domain == "geometric_constraint"
    assert basin.substrate.name == "shape.dodecahedron"
    assert basin.substrate.lid_id == "SHAPE.DODECA"
    assert basin.substrate.family == "intelligence"
    assert basin.support == ("polyhedron", 12, 30, 20)

    sig = basin.signature
    assert sig["faces"] == 12 and sig["edges"] == 30 and sig["vertices"] == 20
    assert set(sig["families"]) == {"orientation", "trust", "growth", "boundary"}
    assert len(sig["principles"]) == 12
    assert sig["bridge_sensors"][:3] == ["admiration", "trust", "longing"]
    assert sig["bridge_defenses"] == ["def.ap.07", "def.fr.06"]
    assert sig["bridge_protocols"] == ["partnership_ethics_v1.0"]
    # bridge_glyphs stays as-is rather than becoming bridge_bridge_glyphs
    assert "bridge_bridge_glyphs" not in sig
    assert sig["bridge_glyphs"] == ["⚖🧭", "🌱⚖", "🔄🕸", "🔮", "👑"]


def test_project_all_covers_every_shape():
    real_root = pathlib.Path(__file__).resolve().parents[2]
    basins = ShapeProjector(real_root).project_all()
    shape_ids = {b.substrate.lid_id for b in basins}
    expected = {
        "SHAPE.TETRA", "SHAPE.CUBE", "SHAPE.OCTA",
        "SHAPE.ICOSA", "SHAPE.DODECA", "SHAPE.RELIEF",
    }
    assert expected.issubset(shape_ids)


def test_depth_orders_tetra_below_dodeca():
    real_root = pathlib.Path(__file__).resolve().parents[2]
    basins = {b.substrate.lid_id: b for b in ShapeProjector(real_root).project_all()}
    assert basins["SHAPE.TETRA"].depth < basins["SHAPE.DODECA"].depth


def test_projector_rejects_non_shape_entity():
    basin_or_error = None
    try:
        ShapeProjector().project({"id": "ANIMAL.BEE"})
    except ValueError as exc:
        basin_or_error = exc
    assert isinstance(basin_or_error, ValueError)


def test_synthetic_shape_round_trips(synthetic_rsc: pathlib.Path):
    data = json.loads((synthetic_rsc / "shapes" / "tiny.json").read_text(encoding="utf-8"))
    basin = ShapeProjector(synthetic_rsc).project(data)
    assert isinstance(basin, Basin)
    assert basin.substrate.name == "shape.tiny"
    assert basin.signature["faces"] == 4
