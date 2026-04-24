"""Basin/Substrate contract sanity checks."""

from __future__ import annotations

from rsc_mandala_bridge.types import Basin, DynamicsProjector, Substrate


def test_substrate_is_frozen():
    s = Substrate(name="shape.tiny", lid_id="SHAPE.TINY")
    try:
        s.name = "other"  # type: ignore[misc]
    except Exception:
        pass
    else:  # pragma: no cover - should be unreachable
        raise AssertionError("Substrate must be frozen")


def test_substrate_defaults():
    s = Substrate(name="shape.tiny")
    assert s.family == "intelligence"
    assert s.lid_id is None
    assert s.drill_path == ()


def test_basin_constructs_with_minimal_signature():
    b = Basin(
        domain="geometric_constraint",
        substrate=Substrate(name="shape.tiny", lid_id="SHAPE.TINY"),
        support=("polyhedron", 4, 6, 4),
        depth=0.4,
    )
    assert b.signature == {}
    assert b.depth == 0.4


def test_projector_protocol_is_structural():
    class _Impl:
        ontology_type = "test"

        def project(self, entity: dict) -> Basin:  # pragma: no cover - trivial
            return Basin(
                domain="test",
                substrate=Substrate(name="test.thing"),
                support=(),
                depth=0.0,
            )

    assert isinstance(_Impl(), DynamicsProjector)
