"""physics_check — the falsifiability pass-through."""

from __future__ import annotations

import pathlib

from rsc_mandala_bridge.physics_check import physics_check_basins
from rsc_mandala_bridge.shape_projector import ShapeProjector
from rsc_mandala_bridge.types import Basin, Substrate


def test_shape_basins_get_annotated():
    real_root = pathlib.Path(__file__).resolve().parents[2]
    basins = ShapeProjector(real_root).project_all()
    physics_check_basins(basins, rsc_root=real_root)

    for b in basins:
        pc = b.signature.get("physics_check")
        assert pc, f"no physics_check on {b.substrate.name}"
        assert "engine" in pc
        assert isinstance(pc["valid"], bool)
        assert 0.0 <= pc["manipulation_probability"] <= 1.0


def test_non_shape_basins_unchanged():
    other = Basin(
        domain="emotional_sensing",
        substrate=Substrate(name="sensor.emotion.trust", lid_id="EMO:TRUST"),
        support=(), depth=0.0,
        signature={"label": "trust"},
    )
    physics_check_basins([other])
    assert "physics_check" not in other.signature


def test_fallback_used_when_guard_unavailable(tmp_path: pathlib.Path):
    """Without physics_grounded_protection.py in the root, the fallback runs."""
    (tmp_path / "schema").mkdir()  # minimal root
    b = Basin(
        domain="geometric_constraint",
        substrate=Substrate(name="shape.dodecahedron", lid_id="SHAPE.DODECA"),
        support=("polyhedron", 12, 30, 20),
        depth=0.9,
        signature={"faces": 12, "edges": 30, "vertices": 20, "families": []},
    )
    physics_check_basins([b], rsc_root=tmp_path)
    pc = b.signature["physics_check"]
    assert pc["engine"] == "fallback_ratios"
    # Dodecahedron has edges/faces = 2.5 and edges/vertices = 1.5 (perfect_fifth).
    assert "perfect_fifth" in pc["constant_matches"] or "phi" in pc["constant_matches"]


def test_physics_check_through_build_basins():
    """End-to-end: build_basins with physics_check=True annotates shape basins."""
    from rsc_mandala_bridge import build_basins

    report = build_basins(physics_check=True)
    assert report.physics_checked
    shape_basins = [b for b in report.basins if b.domain == "geometric_constraint"]
    assert shape_basins
    for b in shape_basins:
        assert "physics_check" in b.signature


def test_physics_check_off_leaves_basins_alone():
    from rsc_mandala_bridge import build_basins

    report = build_basins(physics_check=False)
    assert not report.physics_checked
    for b in report.basins:
        assert "physics_check" not in b.signature
