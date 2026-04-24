"""FieldlinkProjector — read the unified atlas, not the raw upstream repos.

RSC has already solved the merge problem: ``bridges/rosetta-bridges.json``
is the authoritative cross-reference table linking shapes to sensors,
defenses, protocols, and glyphs drawn from five sibling repos. This
projector treats that curated table as the entry point instead of
re-walking the raw upstream content, honoring constraints 4b and 4d of
the briefing.

The staged raws under ``.fieldlink/merge_stage/`` or ``atlas/remote/`` are
consulted for provenance only — the projector notes which staging area
is active so downstream consumers can tell live data from committed
snapshots.
"""

from __future__ import annotations

import json
import pathlib
from typing import Iterable, List, Optional

from rsc_mandala_bridge._paths import rsc_root as _default_root
from rsc_mandala_bridge.types import Basin, Substrate


class FieldlinkProjector:
    ontology_type = "fieldlink"

    def __init__(self, rsc_root: Optional[pathlib.Path] = None):
        self.root = pathlib.Path(rsc_root) if rsc_root is not None else _default_root()

    # ------------------------------------------------------------------ public

    def project_all(self) -> List[Basin]:
        """Emit basins for every sensor/defense/protocol/glyph in the bridge map."""
        bridge_map = self._load_bridge_map()
        stage_root = self._active_atlas_dir()
        provenance = _stage_label(stage_root, self.root)

        basins: list[Basin] = []
        for entry in bridge_map:
            shape_id = entry.get("shape")
            if not shape_id:
                continue
            for sensor in entry.get("sensors", []) or []:
                basins.append(
                    self._sensor_basin(sensor, shape_id, entry, provenance)
                )
            for defense_id in entry.get("defenses", []) or []:
                basins.append(
                    self._defense_basin(defense_id, shape_id, entry, provenance)
                )
            for protocol in entry.get("protocols", []) or []:
                basins.append(
                    self._protocol_basin(protocol, shape_id, entry, provenance)
                )
            for glyph in entry.get("sensor_glyphs", []) or []:
                basins.append(
                    self._glyph_basin(glyph, shape_id, entry, provenance, role="sensor_glyph")
                )

        return _dedupe_by_substrate(basins)

    def active_stage(self) -> Optional[pathlib.Path]:
        """Which staging area is live — merge_stage, atlas/remote, or neither."""
        return self._active_atlas_dir()

    # ----------------------------------------------------------------- loaders

    def _load_bridge_map(self) -> list[dict]:
        path = self.root / "bridges" / "rosetta-bridges.json"
        if not path.is_file():
            return []
        data = json.loads(path.read_text(encoding="utf-8"))
        return data.get("map", []) or []

    def _active_atlas_dir(self) -> Optional[pathlib.Path]:
        merge = self.root / ".fieldlink" / "merge_stage"
        if merge.is_dir() and any(merge.rglob("*.json")):
            return merge
        committed = self.root / "atlas" / "remote"
        if committed.is_dir():
            return committed
        return None

    # --------------------------------------------------------------- projectors

    def _sensor_basin(self, sensor: str, shape_id: str, entry: dict, provenance: str) -> Basin:
        slug = _slug(sensor)
        # Sensors originate in Emotions-as-Sensors; colon-IDs match the briefing's
        # cross-ontology convention (EMO:TRUST, not an RSC-namespace ID).
        substrate = Substrate(
            name=f"sensor.emotion.{slug}",
            family="sensor",
            lid_id=f"EMO:{slug.upper()}",
        )
        return Basin(
            domain="emotional_sensing",
            substrate=substrate,
            support=("sensor", sensor, shape_id),
            depth=0.45,
            signature={
                "label": sensor,
                "anchor_shape": shape_id,
                "anchor_families": list(entry.get("families", [])),
                "bridge_scroll": entry.get("bridge_scroll"),
                "source": "bridges/rosetta-bridges.json",
                "atlas_provenance": provenance,
            },
        )

    def _defense_basin(self, defense_id: str, shape_id: str, entry: dict, provenance: str) -> Basin:
        names = entry.get("defense_names", [])
        defenses = entry.get("defenses", [])
        try:
            label = names[defenses.index(defense_id)]
        except (ValueError, IndexError):
            label = defense_id
        slug = _slug(defense_id)
        substrate = Substrate(
            name=f"protocol.defense.{slug}",
            family="protocol",
            lid_id=f"DEF:{slug.upper()}",
        )
        return Basin(
            domain="symbolic_defense",
            substrate=substrate,
            support=("defense", defense_id, shape_id),
            depth=0.55,
            signature={
                "label": label,
                "anchor_shape": shape_id,
                "anchor_families": list(entry.get("families", [])),
                "source": "bridges/rosetta-bridges.json",
                "atlas_provenance": provenance,
            },
        )

    def _protocol_basin(self, protocol: str, shape_id: str, entry: dict, provenance: str) -> Basin:
        slug = _slug(protocol)
        substrate = Substrate(
            name=f"protocol.audit.{slug}",
            family="protocol",
            lid_id=f"AUDIT:{slug.upper()}",
        )
        return Basin(
            domain="governance",
            substrate=substrate,
            support=("protocol", protocol, shape_id),
            depth=0.50,
            signature={
                "label": protocol,
                "anchor_shape": shape_id,
                "anchor_families": list(entry.get("families", [])),
                "source": "bridges/rosetta-bridges.json",
                "atlas_provenance": provenance,
            },
        )

    def _glyph_basin(
        self,
        glyph: str,
        shape_id: str,
        entry: dict,
        provenance: str,
        *,
        role: str,
    ) -> Basin:
        substrate = Substrate(
            name=f"glyph.{role}.{_slug(glyph) or 'u' + str(ord(glyph[0]))}",
            family="glyph",
            lid_id=None,
        )
        return Basin(
            domain="symbolic_notation",
            substrate=substrate,
            support=("glyph", glyph, shape_id),
            depth=0.35,
            signature={
                "label": glyph,
                "role": role,
                "anchor_shape": shape_id,
                "anchor_families": list(entry.get("families", [])),
                "source": "bridges/rosetta-bridges.json",
                "atlas_provenance": provenance,
            },
        )


# ---------------------------------------------------------------------- helpers


def _slug(text: str) -> str:
    cleaned = "".join(c.lower() if c.isalnum() else "_" for c in text)
    return cleaned.strip("_").replace("__", "_")


def _stage_label(stage: Optional[pathlib.Path], root: pathlib.Path) -> str:
    if stage is None:
        return "no_atlas"
    try:
        rel = stage.relative_to(root)
    except ValueError:
        return str(stage)
    return str(rel)


def _dedupe_by_substrate(basins: Iterable[Basin]) -> list[Basin]:
    """A sensor may anchor to multiple shapes; keep one basin per substrate name.

    Extra anchors are folded into ``signature["additional_anchors"]`` so no
    cross-reference is lost.
    """
    out: dict[str, Basin] = {}
    for b in basins:
        key = b.substrate.name
        if key not in out:
            out[key] = b
            continue
        existing = out[key]
        extras = existing.signature.setdefault("additional_anchors", [])
        extras.append({
            "shape": b.signature.get("anchor_shape"),
            "families": b.signature.get("anchor_families"),
        })
    return list(out.values())
