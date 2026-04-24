"""Validate basins against the RSC schemas they claim to project from.

Contract-test pattern: the RSC schemas are authoritative. A projector that
emits a Basin whose signature cannot be reconstructed into a schema-valid
entity is a buggy projector. This module provides the round-trip check.

Only Shape basins have a strict schema to validate against today. Basins
from sensors, glyphs, protocols, and rule expansions go through the
``core.schema.json`` Entity form when the basin carries enough signature
to reconstruct one; otherwise they pass a lighter structural check.
"""

from __future__ import annotations

import json
import pathlib
from typing import Optional

from jsonschema import Draft202012Validator

from rsc_mandala_bridge._paths import rsc_root as _default_root
from rsc_mandala_bridge.types import Basin

_SCHEMA_CACHE: dict[str, dict] = {}


class BasinSchemaError(ValueError):
    """A Basin failed to validate against the RSC schema it claims."""


def _load_schema(name: str, root: pathlib.Path) -> dict:
    key = f"{root}:{name}"
    if key not in _SCHEMA_CACHE:
        path = root / "schema" / name
        _SCHEMA_CACHE[key] = json.loads(path.read_text(encoding="utf-8"))
    return _SCHEMA_CACHE[key]


def validate_basin_against_schema(
    basin: Basin,
    rsc_root: Optional[pathlib.Path] = None,
) -> None:
    """Raise ``BasinSchemaError`` if the basin contradicts its RSC schema.

    Silent on success. Does not mutate the basin.
    """
    root = pathlib.Path(rsc_root) if rsc_root is not None else _default_root()

    _require_basin_shape(basin)

    lid_id = basin.substrate.lid_id or ""
    if lid_id.startswith("SHAPE."):
        _validate_shape_basin(basin, root)
    elif "." in lid_id and lid_id.split(".", 1)[0] in _CORE_NAMESPACES:
        _validate_core_basin(basin, root, lid_id)
    # Other substrates (SENSOR, GLYPH from external repos, rule expansions
    # whose targets are bare IDs) pass the structural check only.


def _require_basin_shape(basin: Basin) -> None:
    if not isinstance(basin.domain, str) or not basin.domain:
        raise BasinSchemaError("basin.domain must be a non-empty string")
    if not isinstance(basin.signature, dict):
        raise BasinSchemaError("basin.signature must be a dict")
    if not isinstance(basin.depth, (int, float)):
        raise BasinSchemaError("basin.depth must be numeric")
    if basin.substrate is None or not basin.substrate.name:
        raise BasinSchemaError("basin.substrate must carry a non-empty name")


_CORE_NAMESPACES = {
    "ANIMAL", "PLANT", "MICROBE", "CRYSTAL",
    "GEOM", "STRUCT", "FIELD", "CONST", "TEMP",
    "PROTO", "CAP", "SHAPE", "EMOTION", "DEFENSE", "REGEN",
}


def _validate_shape_basin(basin: Basin, root: pathlib.Path) -> None:
    sig = basin.signature
    candidate = {
        "id": basin.substrate.lid_id,
        "name": sig.get("name") or basin.substrate.name.split(".", 1)[-1].title(),
        "faces": sig.get("faces"),
        "edges": sig.get("edges"),
        "vertices": sig.get("vertices"),
        "families": list(sig.get("families", [])),
    }
    if sig.get("principles"):
        candidate["principles"] = list(sig["principles"])
    if sig.get("polyhedral_maps_to"):
        candidate["polyhedral"] = {"maps_to": sig["polyhedral_maps_to"]}
    bridges = {
        k: v for k, v in {
            "sensors": sig.get("bridge_sensors"),
            "glyphs": sig.get("bridge_glyphs"),
            "protocols": sig.get("bridge_protocols"),
            "defenses": sig.get("bridge_defenses"),
        }.items()
        if v
    }
    if bridges:
        candidate["bridges"] = bridges

    # Strip Nones — the schema types faces/edges/vertices as ["integer","null"]
    # so leaving them in is fine, but dropping missing keys keeps the round trip clean.
    candidate = {k: v for k, v in candidate.items() if v is not None}

    schema = _load_schema("shape.schema.json", root)
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(candidate), key=lambda e: list(e.path))
    if errors:
        msgs = "; ".join(f"{list(e.path) or '<root>'}: {e.message}" for e in errors)
        raise BasinSchemaError(f"shape basin {basin.substrate.lid_id!r} invalid: {msgs}")


def _validate_core_basin(basin: Basin, root: pathlib.Path, lid_id: str) -> None:
    kind = lid_id.split(".", 1)[0]
    if kind not in _CORE_NAMESPACES:
        return
    candidate_entity = {
        "id": lid_id,
        "kind": kind,
        "label": basin.signature.get("label")
                 or basin.signature.get("name")
                 or basin.substrate.name,
    }
    doc = {"version": "0.0", "entities": [candidate_entity]}
    schema = _load_schema("core.schema.json", root)
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(doc), key=lambda e: list(e.path))
    if errors:
        msgs = "; ".join(f"{list(e.path) or '<root>'}: {e.message}" for e in errors)
        raise BasinSchemaError(f"core basin {lid_id!r} invalid: {msgs}")
