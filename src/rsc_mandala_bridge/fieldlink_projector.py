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
        """Emit basins for every sensor/defense/protocol/glyph in the bridge map,
        and for every entity in the staged Mandala atlas."""
        basins = self._project_bridge_map()
        basins.extend(self._project_mandala_atlas())
        return _dedupe_by_substrate(basins)

    def project_bridge_map(self) -> List[Basin]:
        """Bridge-table basins only — useful when the caller wants to control atlas walks."""
        return _dedupe_by_substrate(self._project_bridge_map())

    def project_mandala_atlas(self) -> List[Basin]:
        """Mandala-atlas basins only — the 8 octahedral states, glyphs, and sensors."""
        return _dedupe_by_substrate(self._project_mandala_atlas())

    # ------------------------------------------------------ internal pipelines

    def _project_bridge_map(self) -> list[Basin]:
        bridge_map = self._load_bridge_map()
        provenance = _stage_label(self._active_atlas_dir(), self.root)

        basins: list[Basin] = []
        for entry in bridge_map:
            shape_id = entry.get("shape")
            if not shape_id:
                continue
            for sensor in entry.get("sensors", []) or []:
                basins.append(self._sensor_basin(sensor, shape_id, entry, provenance))
            for defense_id in entry.get("defenses", []) or []:
                basins.append(self._defense_basin(defense_id, shape_id, entry, provenance))
            for protocol in entry.get("protocols", []) or []:
                basins.append(self._protocol_basin(protocol, shape_id, entry, provenance))
            for glyph in entry.get("sensor_glyphs", []) or []:
                basins.append(self._glyph_basin(glyph, shape_id, entry, provenance, role="sensor_glyph"))
        return basins

    def _project_mandala_atlas(self) -> list[Basin]:
        """Walk the staged Mandala atlas and emit basins per entity.

        Prefers ``.fieldlink/merge_stage/atlas/remote/mandala`` when a fresh
        pull exists; falls back to the committed ``atlas/remote/mandala``.
        This is the direct walker the briefing section 6 calls for — it
        brings the Mandala's own canonical data back as Basin input so the
        runtime sees its own atlas in the basin stream.
        """
        atlas_dir = self._mandala_atlas_dir()
        if atlas_dir is None:
            return []
        provenance = _stage_label(atlas_dir, self.root)

        basins: list[Basin] = []
        basins.extend(self._project_mandala_shapes(atlas_dir, provenance))
        basins.extend(self._project_mandala_glyphs(atlas_dir, provenance))
        basins.extend(self._project_mandala_sensors(atlas_dir, provenance))
        return basins

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

    def _mandala_atlas_dir(self) -> Optional[pathlib.Path]:
        """Pick the live mandala-atlas subtree, preferring merge_stage."""
        candidates = [
            self.root / ".fieldlink" / "merge_stage" / "atlas" / "remote" / "mandala",
            self.root / "atlas" / "remote" / "mandala",
        ]
        for path in candidates:
            if path.is_dir() and any(path.glob("*.json")):
                return path
        return None

    # --------------------------------------------------- mandala-atlas basins

    def _project_mandala_shapes(self, atlas_dir: pathlib.Path, provenance: str) -> list[Basin]:
        path = atlas_dir / "shapes.json"
        if not path.is_file():
            return []
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return []

        basins: list[Basin] = []
        for state in data.get("octahedral_angles", []) or []:
            idx = state.get("state")
            label = state.get("label", f"state_{idx}")
            slug = _slug(label) or f"s{idx}"
            basins.append(Basin(
                domain="octahedral_state",
                substrate=Substrate(
                    name=f"mandala.octahedron.{slug}",
                    family="state",
                    lid_id=f"MANDALA:OCTA_STATE_{idx}",
                ),
                support=("octahedral_state", idx, state.get("theta"), state.get("phi_angle")),
                depth=0.45,
                signature={
                    "state_index": idx,
                    "label": label,
                    "theta": state.get("theta"),
                    "phi_angle": state.get("phi_angle"),
                    "anchor_shape": "SHAPE.OCTA",
                    "source": "atlas/remote/mandala/shapes.json",
                    "atlas_provenance": provenance,
                },
            ))

        for problem in data.get("problem_types", []) or []:
            pid = problem.get("id")
            if not pid:
                continue
            basins.append(Basin(
                domain="problem_encoding",
                substrate=Substrate(
                    name=f"mandala.problem.{_slug(pid)}",
                    family="problem",
                    lid_id=f"MANDALA:PROBLEM_{pid}",
                ),
                support=("problem", pid, problem.get("encoding")),
                depth=0.55,
                signature={
                    "problem_id": pid,
                    "encoding": problem.get("encoding"),
                    "min_cells": problem.get("min_cells"),
                    "source": "atlas/remote/mandala/shapes.json",
                    "atlas_provenance": provenance,
                },
            ))

        return basins

    def _project_mandala_glyphs(self, atlas_dir: pathlib.Path, provenance: str) -> list[Basin]:
        path = atlas_dir / "glyphs.json"
        if not path.is_file():
            return []
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return []

        basins: list[Basin] = []
        for glyph in data.get("octahedral_state_glyphs", []) or []:
            basins.append(_mandala_glyph_basin(glyph, role="state", provenance=provenance))
        for glyph in data.get("problem_type_glyphs", []) or []:
            basins.append(_mandala_glyph_basin(glyph, role="problem", provenance=provenance))
        for name, glyph in (data.get("energy_glyphs") or {}).items():
            g = {"name": name, **glyph}
            basins.append(_mandala_glyph_basin(g, role="energy", provenance=provenance))
        for name, glyph in (data.get("structural_glyphs") or {}).items():
            g = {"name": name, **glyph}
            basins.append(_mandala_glyph_basin(g, role="structure", provenance=provenance))
        return basins

    def _project_mandala_sensors(self, atlas_dir: pathlib.Path, provenance: str) -> list[Basin]:
        path = atlas_dir / "sensors.json"
        if not path.is_file():
            return []
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return []

        basins: list[Basin] = []
        for sensor in data.get("sensors", []) or []:
            sid = sensor.get("id")
            if not sid:
                continue
            basins.append(Basin(
                domain="computational_sensing",
                substrate=Substrate(
                    name=f"mandala.sensor.{_slug(sid)}",
                    family="sensor",
                    lid_id=f"MANDALA:SENSOR_{sid.upper().replace('.', '_')}",
                ),
                support=("sensor", sid, sensor.get("type")),
                depth=0.50,
                signature={
                    "sensor_id": sid,
                    "sensor_type": sensor.get("type"),
                    "unit": sensor.get("unit"),
                    "description": sensor.get("description"),
                    "interpretation": sensor.get("interpretation"),
                    "source": "atlas/remote/mandala/sensors.json",
                    "atlas_provenance": provenance,
                },
            ))
        return basins

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


def _mandala_glyph_basin(glyph: dict, *, role: str, provenance: str) -> Basin:
    """Build a Basin from a mandala/glyphs.json entry.

    The entries have heterogeneous keys (``state``, ``type``, ``name``,
    ``glyph``). We normalize to a substrate name and preserve every field
    in the signature.
    """
    handle = (
        glyph.get("glyph")
        or glyph.get("name")
        or (f"state_{glyph['state']}" if "state" in glyph else None)
        or glyph.get("type")
        or "unknown"
    )
    slug = _slug(handle.replace(".", "_")) or "unknown"
    return Basin(
        domain="symbolic_notation",
        substrate=Substrate(
            name=f"glyph.mandala.{role}.{slug}",
            family="glyph",
            lid_id=None,
        ),
        support=("glyph", role, handle),
        depth=0.4,
        signature={
            "role": role,
            "label": glyph.get("unicode") or glyph.get("glyph"),
            "glyph_handle": handle,
            "meaning": glyph.get("meaning"),
            "state": glyph.get("state"),
            "problem_type": glyph.get("type"),
            "source": "atlas/remote/mandala/glyphs.json",
            "atlas_provenance": provenance,
        },
    )


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
