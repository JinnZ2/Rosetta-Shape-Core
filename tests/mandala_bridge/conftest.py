"""Shared fixtures for the rsc_mandala_bridge test suite."""

from __future__ import annotations

import json
import pathlib

import pytest


@pytest.fixture
def synthetic_rsc(tmp_path: pathlib.Path) -> pathlib.Path:
    """A minimal synthetic RSC layout for end-to-end tests.

    Structure (matches the real repo's relevant directories):

      tmp/
        schema/shape.schema.json    (copied from real repo)
        schema/core.schema.json     (copied from real repo)
        shapes/tiny.json
        bridges/rosetta-bridges.json
        rules/expand.jsonl
        ontology/entities.json
        atlas/remote/placeholder.json
    """
    real_root = pathlib.Path(__file__).resolve().parents[2]

    schema_dir = tmp_path / "schema"
    schema_dir.mkdir()
    for name in ("shape.schema.json", "core.schema.json"):
        (schema_dir / name).write_text(
            (real_root / "schema" / name).read_text(encoding="utf-8"),
            encoding="utf-8",
        )

    shapes_dir = tmp_path / "shapes"
    shapes_dir.mkdir()
    (shapes_dir / "tiny.json").write_text(json.dumps({
        "id": "SHAPE.TINY",
        "name": "Tiny",
        "faces": 4,
        "edges": 6,
        "vertices": 4,
        "families": ["foundation"],
        "polyhedral": {"maps_to": "minimal simplex"},
        "bridges": {
            "sensors": ["pride"],
            "defenses": ["def.se.01"],
            "protocols": ["symbolic_protocol_v1.0"],
            "bridge_glyphs": ["🔺"],
        },
    }), encoding="utf-8")

    bridges_dir = tmp_path / "bridges"
    bridges_dir.mkdir()
    (bridges_dir / "rosetta-bridges.json").write_text(json.dumps({
        "id": "BRIDGE.ROSETTA_CROSS_REPO",
        "version": "test",
        "map": [
            {
                "shape": "SHAPE.TINY",
                "families": ["foundation"],
                "sensors": ["pride"],
                "sensor_glyphs": ["🏅"],
                "defenses": ["def.se.01"],
                "defense_names": ["Self-deception"],
                "protocols": ["symbolic_protocol_v1.0"],
                "bridge_scroll": "pride ↔ self-deception (🛡)",
            },
        ],
    }), encoding="utf-8")

    rules_dir = tmp_path / "rules"
    rules_dir.mkdir()
    (rules_dir / "expand.jsonl").write_text(
        '{"when":{"op":"EXPAND","args":["SHAPE.TINY"]},"then":"CAP.DEMO_ACTIVATION","priority":5,"why":"test rule"}\n'
        '{"when":{"op":"ALIGN","args":["SHAPE.TINY","CONST.PHI"]},"then":"CAP.DEMO_GATED","priority":3,"guard":{"requires":["CAP.DEMO_ACTIVATION"]},"why":"gated test rule"}\n',
        encoding="utf-8",
    )

    onto_dir = tmp_path / "ontology"
    onto_dir.mkdir()
    (onto_dir / "entities.json").write_text(json.dumps({
        "version": "test",
        "entities": [
            {
                "id": "CONST.PHI",
                "kind": "CONST",
                "label": "Phi",
            },
            {
                "id": "CAP.DEMO_ACTIVATION",
                "kind": "CAP",
                "label": "Demo activation",
            },
        ],
    }), encoding="utf-8")

    (tmp_path / "atlas" / "remote").mkdir(parents=True)
    (tmp_path / "atlas" / "remote" / "placeholder.json").write_text("{}", encoding="utf-8")

    return tmp_path
