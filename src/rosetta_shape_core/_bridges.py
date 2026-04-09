"""Bridge resolver — makes bridge mappings computationally active.

Bridges are not just metadata.  This module extracts actionable mappings
from bridge JSON files and resolves them at runtime so that:

  1. ``discover()`` can traverse bridge mappings to find shape targets
  2. ``check_merge()`` can ask whether a bridge endorses a family→shape link
  3. ``Simulation`` agents can discover cross-domain paths via bridge semantics

Each bridge defines ``mappings`` (semantic connections) and optionally
``cross_bridge_connections`` (links to other bridges).  This module indexes
both into a lookup structure keyed by entity, shape, or family.
"""
from __future__ import annotations

import re

_ID_RE = re.compile(r'\b(SHAPE\.\w+|FAMILY\.F\d+|PRINCIPLE\.P\d+|CAP\.\w+|PROTO\.\w+|'
                     r'ANIMAL\.\w+|PLANT\.\w+|CRYSTAL\.\w+|MICROBE\.\w+|'
                     r'FIELD\.\w+|GEOM\.\w+|STRUCT\.\w+|CONST\.\w+)\b')


def _scan_ids(text: str, prefix: str | None = None) -> list[str]:
    """Extract well-formed IDs (NAMESPACE.NAME) from any string."""
    ids = _ID_RE.findall(text)
    if prefix:
        ids = [i for i in ids if i.startswith(prefix)]
    return ids


# ── Mapping extraction ────────────────────────────────────────────

_SHAPE_KEYS = (
    "to", "target_shape", "rosetta_shape", "shape_anchor",
    "rosetta_shape_anchor", "shape", "platonic_shape",
    "from", "notes", "rationale", "description",
)

_FAMILY_KEYS = (
    "to", "rosetta_families", "rosetta_family", "rosetta_principle",
    "families", "family", "principles", "principle_names",
    "family_affinity", "family_name", "family_map",
    "from", "notes", "rationale", "description",
)

_ENTITY_KEYS = (
    "to", "from", "rosetta_id", "rosetta_capability",
    "rosetta_analog", "rosetta_parallel",
    "notes", "rationale", "description",
)


def _extract_shape_targets(mapping: dict) -> list[str]:
    """Pull SHAPE.* references from a mapping's values."""
    targets: list[str] = []
    for key in _SHAPE_KEYS:
        val = mapping.get(key, "")
        if isinstance(val, str):
            targets.extend(_scan_ids(val, "SHAPE."))
        elif isinstance(val, list):
            for v in val:
                if isinstance(v, str):
                    targets.extend(_scan_ids(v, "SHAPE."))
    anchors = mapping.get("shape_anchors", [])
    if isinstance(anchors, list):
        for a in anchors:
            if isinstance(a, str):
                targets.extend(_scan_ids(a, "SHAPE."))
    return list(dict.fromkeys(targets))


def _extract_family_refs(mapping: dict) -> list[str]:
    """Pull FAMILY.* or PRINCIPLE.* references."""
    refs: list[str] = []
    for key in _FAMILY_KEYS:
        val = mapping.get(key)
        if isinstance(val, str):
            refs.extend(_scan_ids(val, "FAMILY."))
            refs.extend(_scan_ids(val, "PRINCIPLE."))
        elif isinstance(val, list):
            for v in val:
                if isinstance(v, str):
                    refs.extend(_scan_ids(v, "FAMILY."))
                    refs.extend(_scan_ids(v, "PRINCIPLE."))
    return list(dict.fromkeys(refs))


def _extract_entity_refs(mapping: dict) -> list[str]:
    """Pull entity-style IDs (ANIMAL.*, CAP.*, PROTO.*, etc.)."""
    refs: list[str] = []
    for key in _ENTITY_KEYS:
        val = mapping.get(key, "")
        if isinstance(val, str):
            for found in _scan_ids(val):
                if not found.startswith(("SHAPE.", "FAMILY.", "PRINCIPLE.")):
                    refs.append(found)
    return list(dict.fromkeys(refs))


# ── Deep walk ─────────────────────────────────────────────────────

# Top-level keys that are metadata, not mapping content.
_SKIP_KEYS = frozenset({
    "id", "version", "updated", "description", "source", "target",
    "provenance", "cross_bridge_connections", "$schema",
})


def _walk_mapping_dicts(obj: dict | list, depth: int = 0) -> list[dict]:
    """Recursively find every dict-inside-a-list in a bridge structure.

    Bridges use many different array names (``mappings``, ``encoders``,
    ``sensors``, ``axioms``, ``modules``, ``states``, ``clusters``, etc.).
    Rather than hard-coding each name, we walk the tree and yield every
    dict that lives inside a list — those are the mapping rows.
    """
    results: list[dict] = []
    if depth > 4:  # safety bound
        return results

    if isinstance(obj, dict):
        for key, val in obj.items():
            if key in _SKIP_KEYS:
                continue
            if isinstance(val, list):
                for item in val:
                    if isinstance(item, dict):
                        results.append(item)
                    elif isinstance(item, list):
                        results.extend(_walk_mapping_dicts(item, depth + 1))
            elif isinstance(val, dict):
                results.extend(_walk_mapping_dicts(val, depth + 1))
    elif isinstance(obj, list):
        for item in obj:
            if isinstance(item, dict):
                results.append(item)
            elif isinstance(item, list):
                results.extend(_walk_mapping_dicts(item, depth + 1))
    return results


# ── Bridge index ──────────────────────────────────────────────────

class BridgeIndex:
    """Indexed view of all bridge mappings for fast lookup.

    Built once from ``RosettaGraph.bridges`` and then queried by
    ``discover()`` and ``check_merge()``.
    """

    def __init__(self, bridges: dict[str, dict]):
        # shape → list of (bridge_id, mapping_dict)
        self.by_shape: dict[str, list[tuple[str, dict]]] = {}
        # family/principle → list of (bridge_id, mapping_dict)
        self.by_family: dict[str, list[tuple[str, dict]]] = {}
        # entity → list of (bridge_id, mapping_dict)
        self.by_entity: dict[str, list[tuple[str, dict]]] = {}
        # bridge_id → target shapes declared in "target.shape_anchors"
        self.bridge_shapes: dict[str, list[str]] = {}

        self._index(bridges)

    def _index(self, bridges: dict[str, dict]):
        for bid, bdata in bridges.items():
            # Index target shape anchors
            target = bdata.get("target", {})
            anchors = target.get("shape_anchors", [])
            if isinstance(target.get("shape_anchor"), str):
                anchors = [target["shape_anchor"]]
            self.bridge_shapes[bid] = [a for a in anchors if isinstance(a, str)]

            # Walk ALL nested structures — bridges use many different array
            # names (mappings, encoders, sensors, axioms, modules, etc.).
            # Instead of hard-coding each name, we recursively find every
            # dict inside every list and extract IDs from it.
            for mapping in _walk_mapping_dicts(bdata):
                for shape in _extract_shape_targets(mapping):
                    self.by_shape.setdefault(shape, []).append((bid, mapping))
                for fam in _extract_family_refs(mapping):
                    self.by_family.setdefault(fam, []).append((bid, mapping))
                for ent in _extract_entity_refs(mapping):
                    self.by_entity.setdefault(ent, []).append((bid, mapping))

    # ── Query methods ─────────────────────────────────────────────

    def shapes_for_entity(self, entity_id: str) -> list[dict]:
        """Return bridge-endorsed shapes reachable from *entity_id*."""
        results = []
        for bid, mapping in self.by_entity.get(entity_id, []):
            for shape in _extract_shape_targets(mapping):
                results.append({
                    "type": "bridge_mapping",
                    "bridge": bid,
                    "target_shape": shape,
                    "relation": mapping.get("type", ""),
                    "notes": mapping.get("notes", ""),
                })
        return results

    def families_for_shape(self, shape_id: str) -> list[dict]:
        """Return bridge-endorsed families for a shape."""
        results = []
        for bid, mapping in self.by_shape.get(shape_id, []):
            for fam in _extract_family_refs(mapping):
                results.append({
                    "bridge": bid,
                    "family": fam,
                    "relation": mapping.get("type", ""),
                    "notes": mapping.get("notes", ""),
                })
        return results

    def endorses_merge(self, family_id: str, shape_id: str) -> dict | None:
        """Check if any bridge endorses a family→shape combination.

        Returns the endorsement dict if found, else ``None``.
        This gives ``check_merge()`` a bridge-backed opinion on frontier
        merges that the family_map alone can't resolve.
        """
        for bid, mapping in self.by_family.get(family_id, []):
            for shape in _extract_shape_targets(mapping):
                if shape == shape_id:
                    return {
                        "bridge": bid,
                        "family": family_id,
                        "shape": shape_id,
                        "relation": mapping.get("type", ""),
                        "notes": mapping.get("notes", ""),
                    }
        return None

    def resolve_paths(self, entity_id: str, families: list[str]) -> list[dict]:
        """Return all bridge-discoverable paths for an entity+families combo.

        Used by ``discover()`` to add bridge-sourced exploration paths
        alongside existing LID rules, Rosetta rules, and family affinities.
        """
        paths: list[dict] = []
        seen: set[str] = set()

        # Direct entity matches
        for p in self.shapes_for_entity(entity_id):
            key = (p["bridge"], p.get("target_shape", ""))
            if key not in seen:
                seen.add(key)
                paths.append(p)

        # Family-based matches
        for fid in families:
            for bid, mapping in self.by_family.get(fid, []):
                for shape in _extract_shape_targets(mapping):
                    key = (bid, shape)
                    if key not in seen:
                        seen.add(key)
                        paths.append({
                            "type": "bridge_mapping",
                            "bridge": bid,
                            "family": fid,
                            "target_shape": shape,
                            "relation": mapping.get("type", ""),
                            "notes": mapping.get("notes", ""),
                        })

        return paths

    def stats(self) -> dict:
        """Return index statistics."""
        return {
            "bridges_indexed": len(self.bridge_shapes),
            "shapes_indexed": len(self.by_shape),
            "families_indexed": len(self.by_family),
            "entities_indexed": len(self.by_entity),
        }
