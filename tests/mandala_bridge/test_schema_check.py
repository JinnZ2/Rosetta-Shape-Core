"""Schema contract test — malformed basins must fail, healthy basins must pass."""

from __future__ import annotations

import pathlib

import pytest

from rsc_mandala_bridge.schema_check import (
    BasinSchemaError,
    validate_basin_against_schema,
)
from rsc_mandala_bridge.shape_projector import ShapeProjector
from rsc_mandala_bridge.types import Basin, Substrate


def test_valid_shape_basin_passes():
    real_root = pathlib.Path(__file__).resolve().parents[2]
    basins = ShapeProjector(real_root).project_all()
    for b in basins:
        validate_basin_against_schema(b, real_root)  # must not raise


def test_shape_basin_with_bad_id_fails():
    bad = Basin(
        domain="geometric_constraint",
        substrate=Substrate(name="shape.ghost", lid_id="SHAPE.invalid"),
        support=("polyhedron", 4, 6, 4),
        depth=0.4,
        signature={"faces": 4, "edges": 6, "vertices": 4, "families": ["foundation"]},
    )
    with pytest.raises(BasinSchemaError):
        validate_basin_against_schema(bad)


def test_basin_without_substrate_name_fails():
    bad = Basin(
        domain="test",
        substrate=Substrate(name=""),
        support=(), depth=0.0,
    )
    with pytest.raises(BasinSchemaError):
        validate_basin_against_schema(bad)


def test_non_rsc_lid_id_passes_structural_check():
    """Sensor/defense/protocol basins use colon-IDs; they pass structural only."""
    ok = Basin(
        domain="emotional_sensing",
        substrate=Substrate(name="sensor.emotion.trust", lid_id="EMO:TRUST"),
        support=("sensor", "trust", "SHAPE.DODECA"),
        depth=0.45,
        signature={"label": "trust"},
    )
    validate_basin_against_schema(ok)


def test_core_namespace_basin_requires_valid_id():
    real_root = pathlib.Path(__file__).resolve().parents[2]
    ok = Basin(
        domain="rule_expansion",
        substrate=Substrate(name="cap.hex_optimization", lid_id="CAP.HEX_OPTIMIZATION"),
        support=("ALIGN", ("ANIMAL.BEE", "CONST.PHI"), "CAP.HEX_OPTIMIZATION"),
        depth=0.5,
        signature={"label": "hex optimization"},
    )
    validate_basin_against_schema(ok, real_root)

    bad = Basin(
        domain="rule_expansion",
        substrate=Substrate(name="cap.bad id", lid_id="CAP.bad id"),
        support=(),
        depth=0.5,
        signature={"label": "bad"},
    )
    with pytest.raises(BasinSchemaError):
        validate_basin_against_schema(bad, real_root)
