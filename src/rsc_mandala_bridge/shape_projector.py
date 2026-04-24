"""ShapeProjector — turn ``shapes/*.json`` entities into Basins.

Each RSC shape carries a dense cross-reference payload that LID basins do
not: an explicit ``bridges`` block listing sensors, defenses, protocols,
and glyphs. The projector lifts that payload into the Basin signature so
the Mandala's resonance detector gets curated links, not heuristics.
"""

from __future__ import annotations

import json
import pathlib
from typing import List, Optional

from rsc_mandala_bridge._paths import rsc_root as _default_root
from rsc_mandala_bridge.types import Basin, Substrate


class ShapeProjector:
    ontology_type = "shape"

    def __init__(self, rsc_root: Optional[pathlib.Path] = None):
        self.root = pathlib.Path(rsc_root) if rsc_root is not None else _default_root()

    def project(self, entity: dict) -> Basin:
        """Project a single shape entity dict into a Basin."""
        shape_id = entity.get("id", "")
        if not shape_id.startswith("SHAPE."):
            raise ValueError(
                f"ShapeProjector expects a SHAPE.* entity, got id={shape_id!r}"
            )

        name = entity.get("name", "").strip() or shape_id.split(".", 1)[-1].title()
        substrate_name = _substrate_name_for_shape(shape_id, name)

        faces = entity.get("faces")
        edges = entity.get("edges")
        vertices = entity.get("vertices")
        families = list(entity.get("families", []))
        principles = list(entity.get("principles", []))
        bridges = entity.get("bridges") or {}
        polyhedral = entity.get("polyhedral") or {}

        signature: dict = {
            "name": name,
            "faces": faces,
            "edges": edges,
            "vertices": vertices,
            "families": families,
        }
        if principles:
            signature["principles"] = principles
        if polyhedral.get("maps_to"):
            signature["polyhedral_maps_to"] = polyhedral["maps_to"]
        for key in ("sensors", "glyphs", "protocols", "defenses"):
            if bridges.get(key):
                signature[f"bridge_{key}"] = list(bridges[key])
        # RSC shapes carry a separate `bridge_glyphs` list for cross-ontology
        # glyph pairs; keep its name as-is instead of prefixing.
        if bridges.get("bridge_glyphs"):
            signature["bridge_glyphs"] = list(bridges["bridge_glyphs"])
        if entity.get("octahedral_states"):
            signature["octahedral_states"] = entity["octahedral_states"]

        substrate = Substrate(
            name=substrate_name,
            family="intelligence",
            lid_id=shape_id,
        )

        return Basin(
            domain="geometric_constraint",
            substrate=substrate,
            support=("polyhedron", faces, edges, vertices),
            depth=_compute_shape_depth(vertices, families, bridges, principles),
            signature=signature,
        )

    def project_all(self) -> List[Basin]:
        """Walk ``shapes/*.json`` and project every entry."""
        shapes_dir = self.root / "shapes"
        if not shapes_dir.is_dir():
            return []
        basins: list[Basin] = []
        for path in sorted(shapes_dir.glob("*.json")):
            data = json.loads(path.read_text(encoding="utf-8"))
            basins.append(self.project(data))
        return basins


_SHAPE_NAME_OVERRIDES = {
    "SHAPE.DODECA": "dodecahedron",
    "SHAPE.ICOSA": "icosahedron",
    "SHAPE.OCTA": "octahedron",
    "SHAPE.TETRA": "tetrahedron",
    "SHAPE.CUBE": "cube",
    "SHAPE.RELIEF": "relief",
}


def _substrate_name_for_shape(shape_id: str, name: str) -> str:
    if shape_id in _SHAPE_NAME_OVERRIDES:
        return f"shape.{_SHAPE_NAME_OVERRIDES[shape_id]}"
    # Fall back to the first word of the human-readable name; this keeps
    # new shapes like "Cube (Hexahedron)" from producing parenthetical junk.
    token = name.lower().split()[0] if name else shape_id.split(".", 1)[-1].lower()
    token = "".join(c for c in token if c.isalnum() or c == "_")
    return f"shape.{token or shape_id.split('.', 1)[-1].lower()}"


def _compute_shape_depth(
    vertices: Optional[int],
    families: list,
    bridges: dict,
    principles: list,
) -> float:
    """Depth reflects symbolic richness, not raw vertex count alone.

    Anchored so the dodecahedron (vertices=20, 12 principles, dense
    bridges) lands near 0.85 — the worked example in the briefing — and
    the tetrahedron (vertices=4, sparse bridges) lands near 0.4.
    """
    base = 0.3 + 0.015 * (vertices or 0)
    base += 0.02 * len(families)
    base += 0.01 * len(principles)
    bridge_count = sum(len(v) for v in bridges.values() if isinstance(v, list))
    base += 0.01 * bridge_count
    return round(min(1.0, max(0.0, base)), 3)
