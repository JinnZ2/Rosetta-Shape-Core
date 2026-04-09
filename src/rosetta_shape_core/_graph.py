"""Graph loader — RosettaGraph and data loading utilities."""
from __future__ import annotations
import json, pathlib

from rosetta_shape_core._bridges import BridgeIndex

ROOT = pathlib.Path(__file__).resolve().parents[2]


def _load_json(path):
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {}


def _load_jsonl(path):
    rows = []
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                rows.append(json.loads(line))
    return rows


class RosettaGraph:
    """In-memory graph of all entities, rules, bridges, and family affinities."""

    def __init__(self):
        self.entities = {}
        self.lid_to_rosetta = {}
        self.label_to_id = {}
        self.family_map = {}
        self.shape_profiles = {}
        self.families = {}
        self.rules = []
        self.lid_rules = []
        self.bridges = {}
        self.bridge_index: BridgeIndex | None = None
        self.blocked_merges = []
        self._load_all()

    def _load_all(self):
        self._load_family_map()
        self._load_ontology()
        self._load_lid_atlas()
        self._load_rules()
        self._load_bridges()

    def _load_family_map(self):
        fm = _load_json(ROOT / "ontology" / "family_map.json")
        self.family_map = fm
        self.shape_profiles = fm.get("shape_profiles", {})
        fam_model = fm.get("family_affinity_model", {})
        self.families = fam_model.get("families", {})
        blocked = fam_model.get("merge_policy", {}).get("blocked_merges", {})
        self.blocked_merges = blocked.get("examples", [])

    def _load_ontology(self):
        onto_dir = ROOT / "ontology"
        for p in onto_dir.glob("*.json"):
            data = _load_json(p)
            for e in data.get("entities", []):
                eid = e["id"]
                self.entities[eid] = e
                self.label_to_id[e.get("name", "").lower()] = eid

    def _load_lid_atlas(self):
        atlas = _load_json(ROOT / "atlas" / "remote" / "living-intelligence" / "atlas.json")
        for kind, elist in atlas.get("entities", {}).items():
            for e in elist:
                rid = e.get("rosetta_id", "")
                lid = e.get("lid_id", "")
                if rid:
                    merged = {**e}
                    if rid in self.entities:
                        merged = {**self.entities[rid], **e}
                    self.entities[rid] = merged
                    if lid:
                        self.lid_to_rosetta[lid] = rid
                        self.lid_to_rosetta[lid.lower()] = rid
                    label = e.get("label", "").lower()
                    if label:
                        self.label_to_id[label] = rid

        rules_data = _load_json(ROOT / "atlas" / "remote" / "living-intelligence" / "rules.json")
        self.lid_rules = rules_data.get("rules", [])

    def _load_rules(self):
        self.rules = _load_jsonl(ROOT / "rules" / "expand.jsonl")

    def _load_bridges(self):
        bridge_dir = ROOT / "bridges"
        if bridge_dir.exists():
            for p in bridge_dir.glob("*.json"):
                data = _load_json(p)
                bid = data.get("id", p.stem)
                self.bridges[bid] = data
        self.bridge_index = BridgeIndex(self.bridges)

    def resolve_id(self, query: str) -> str | None:
        """Resolve a fuzzy query to a rosetta_id."""
        q = query.strip()
        if q in self.entities:
            return q
        if q in self.lid_to_rosetta:
            return self.lid_to_rosetta[q]
        ql = q.lower()
        if ql in self.lid_to_rosetta:
            return self.lid_to_rosetta[ql]
        if ql in self.label_to_id:
            return self.label_to_id[ql]
        for label, eid in self.label_to_id.items():
            if ql in label:
                return eid
        for eid in self.entities:
            if ql in eid.lower():
                return eid
        return None
