"""
Rosetta-Shape-Core Exploration Engine

Every entity has a "home base" — its primary shape and families.
From there, you explore outward through expander rules, bridge links,
and family affinities. The physics merge gates are guardrails:
explore freely, but conservation laws don't bend.

Usage:
    python -m rosetta_shape_core.explore bee
    python -m rosetta_shape_core.explore ANIMAL.BEE
    python -m rosetta_shape_core.explore ANIMAL.BEE --depth 2
    python -m rosetta_shape_core.explore CRYSTAL.QUARTZ --json
"""
from __future__ import annotations
import json, pathlib, argparse, sys
from collections import defaultdict

ROOT = pathlib.Path(__file__).resolve().parents[2]

# ── data loading ────────────────────────────────────────────────────

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
        self.entities = {}        # rosetta_id -> entity dict
        self.lid_to_rosetta = {}  # BEE -> ANIMAL.BEE
        self.label_to_id = {}     # bee -> ANIMAL.BEE
        self.family_map = {}      # full family_map.json
        self.shape_profiles = {}  # SHAPE.TETRA -> profile
        self.families = {}        # FAMILY.F01 -> {name, primary, merged, secondary}
        self.rules = []           # rosetta expand.jsonl rules
        self.lid_rules = []       # LID expander rules
        self.bridges = {}         # bridge_id -> bridge data
        self.blocked_merges = []  # known blocked merges
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
                    # merge with any existing ontology entity
                    if rid in self.entities:
                        merged = {**self.entities[rid], **e}
                    self.entities[rid] = merged
                    if lid:
                        self.lid_to_rosetta[lid] = rid
                        self.lid_to_rosetta[lid.lower()] = rid
                    label = e.get("label", "").lower()
                    if label:
                        self.label_to_id[label] = rid

        # load LID rules
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

    def resolve_id(self, query: str) -> str | None:
        """Resolve a fuzzy query to a rosetta_id."""
        q = query.strip()
        # exact rosetta id
        if q in self.entities:
            return q
        # exact LID id
        if q in self.lid_to_rosetta:
            return self.lid_to_rosetta[q]
        # case-insensitive
        ql = q.lower()
        if ql in self.lid_to_rosetta:
            return self.lid_to_rosetta[ql]
        if ql in self.label_to_id:
            return self.label_to_id[ql]
        # partial match on label
        for label, eid in self.label_to_id.items():
            if ql in label:
                return eid
        # partial match on id
        for eid in self.entities:
            if ql in eid.lower():
                return eid
        return None


# ── home base ───────────────────────────────────────────────────────

def home_base(graph: RosettaGraph, entity_id: str) -> dict:
    """Return the entity's home base: primary shape, families, sensors, capabilities."""
    ent = graph.entities.get(entity_id, {})
    families = ent.get("rosetta_families", [])
    caps = ent.get("rosetta_capabilities", ent.get("capabilities", []))

    # find primary shape: the shape where most of the entity's families are primary
    shape_scores = defaultdict(lambda: {"primary": 0, "merged": 0, "secondary": 0})
    for fid in families:
        fam = graph.families.get(fid, {})
        prim = fam.get("primary", "")
        if prim:
            shape_scores[prim]["primary"] += 1
        for ms in fam.get("merged", []):
            shape_scores[ms]["merged"] += 1
        for ss in fam.get("secondary", []):
            shape_scores[ss]["secondary"] += 1

    # rank shapes: primary count first, then merged, then secondary
    ranked = sorted(shape_scores.items(),
                    key=lambda kv: (kv[1]["primary"], kv[1]["merged"], kv[1]["secondary"]),
                    reverse=True)

    primary_shape = ranked[0][0] if ranked else None
    profile = graph.shape_profiles.get(primary_shape, {})

    return {
        "entity_id": entity_id,
        "label": ent.get("label", ent.get("name", entity_id)),
        "pattern": ent.get("pattern", ent.get("description", "")),
        "home_shape": primary_shape,
        "home_shape_profile": {
            "qualitative": profile.get("qualitative", []),
            "sensors": profile.get("sensors", []),
            "primary_families": profile.get("primary_families", []),
        },
        "entity_families": families,
        "entity_families_named": [
            f"{fid} ({graph.families.get(fid, {}).get('name', '?')})"
            for fid in families
        ],
        "capabilities": caps,
        "links": ent.get("links", []),
    }


# ── discovery ───────────────────────────────────────────────────────

def _match_lid_rule(rule, entity_id, graph):
    """Check if an LID rule involves this entity. Return (partners, emergent, rule) or None."""
    ent = graph.entities.get(entity_id, {})
    lid_id = ent.get("lid_id", "")
    inputs = rule.get("if", [])

    # check if entity's LID id or rosetta_id fragment appears in rule inputs
    matched = False
    for inp in inputs:
        if inp == lid_id:
            matched = True
        elif entity_id.endswith("." + inp):
            matched = True
        elif inp.lower() == lid_id.lower():
            matched = True
    if not matched:
        return None

    partners = [i for i in inputs if i != lid_id and not entity_id.endswith("." + i)]
    return {
        "type": "lid_rule",
        "partners": partners,
        "emergent": rule.get("then", ""),
        "target_shape": rule.get("rosetta_shape"),
        "families": rule.get("rosetta_families", []),
    }


def _match_rosetta_rule(rule, entity_id):
    """Check if a Rosetta expand.jsonl rule involves this entity."""
    when = rule.get("when", {})
    args = when.get("args", [])
    if entity_id not in args:
        return None
    partners = [a for a in args if a != entity_id]
    return {
        "type": "rosetta_rule",
        "operation": when.get("op", ""),
        "partners": partners,
        "result": rule.get("then", ""),
        "guard": rule.get("guard", {}),
        "why": rule.get("why", ""),
    }


def _find_bridge_connections(graph, entity_id):
    """Find cross-bridge connections for this entity."""
    connections = []
    ent = graph.entities.get(entity_id, {})
    lid_id = ent.get("lid_id", "")

    for bid, bdata in graph.bridges.items():
        # check cross_bridge_connections
        for conn in bdata.get("cross_bridge_connections", {}).get("connections", []):
            if conn.get("lid_entity") == lid_id or conn.get("rosetta_id") == entity_id:
                connections.append({
                    "type": "bridge_connection",
                    "bridge": bid,
                    "target_bridge": conn.get("rosetta_bridge", ""),
                    "connection": conn.get("connection", ""),
                })
    return connections


def discover(graph: RosettaGraph, entity_id: str, depth: int = 1) -> list[dict]:
    """Discover reachable entities/emergent forms from the starting entity."""
    paths = []

    # 1) LID expander rules
    for rule in graph.lid_rules:
        match = _match_lid_rule(rule, entity_id, graph)
        if match:
            paths.append(match)

    # 2) Rosetta expand.jsonl rules
    for rule in graph.rules:
        match = _match_rosetta_rule(rule, entity_id)
        if match:
            paths.append(match)

    # 3) Direct links from entity
    ent = graph.entities.get(entity_id, {})
    for link in ent.get("links", []):
        paths.append({
            "type": "direct_link",
            "relation": link.get("rel", ""),
            "target": link.get("to", ""),
        })

    # 4) Bridge connections
    paths.extend(_find_bridge_connections(graph, entity_id))

    # 5) Family affinity exploration — shapes reachable through families
    families = ent.get("rosetta_families", [])
    visited_shape_family = set()
    for fid in families:
        fam = graph.families.get(fid, {})
        for shape in fam.get("merged", []):
            key = (fid, shape)
            if key not in visited_shape_family:
                visited_shape_family.add(key)
                paths.append({
                    "type": "family_affinity",
                    "affinity": "merged",
                    "family": fid,
                    "family_name": fam.get("name", ""),
                    "target_shape": shape,
                })
        for shape in fam.get("secondary", []):
            key = (fid, shape)
            if key not in visited_shape_family:
                visited_shape_family.add(key)
                paths.append({
                    "type": "family_affinity",
                    "affinity": "secondary",
                    "family": fid,
                    "family_name": fam.get("name", ""),
                    "target_shape": shape,
                })

    # depth > 1: recursively discover from emergent forms and targets
    if depth > 1:
        seen = {entity_id}
        for p in list(paths):
            target = None
            if p["type"] == "lid_rule":
                # try to resolve emergent form
                emergent = p.get("emergent", "")
                target = graph.resolve_id(emergent)
            elif p["type"] == "direct_link":
                target = graph.resolve_id(p.get("target", ""))
            if target and target not in seen:
                seen.add(target)
                sub = discover(graph, target, depth=depth - 1)
                for s in sub:
                    s["via"] = p.get("emergent", p.get("target", p.get("target_shape", "?")))
                    paths.append(s)

    return paths


# ── merge gate check ────────────────────────────────────────────────

def check_merge(graph: RosettaGraph, family_id: str, shape_id: str) -> dict:
    """Check whether a family-shape combination passes the merge gates."""
    fam = graph.families.get(family_id, {})
    if not fam:
        return {"status": "unknown", "reason": f"Family {family_id} not found"}

    primary = fam.get("primary", "")
    merged = fam.get("merged", [])
    secondary = fam.get("secondary", [])

    if shape_id == primary:
        return {"status": "primary", "reason": "This is the family's home shape"}
    if shape_id in merged:
        return {
            "status": "merged",
            "reason": fam.get("merge_basis", "Merge validated — equations compatible"),
        }
    if shape_id in secondary:
        return {
            "status": "secondary",
            "reason": fam.get("merge_note", "Activates in this shape context but not co-primary"),
        }

    # check blocked
    for b in graph.blocked_merges:
        if b.get("family") == family_id and b.get("candidate") == shape_id:
            return {
                "status": "blocked",
                "reason": b.get("reason", "Merge blocked by physics gate"),
            }

    return {
        "status": "unexplored",
        "reason": f"{family_id} has no defined relationship with {shape_id}. Could be a frontier merge — needs gate validation.",
    }


# ── display ─────────────────────────────────────────────────────────

SHAPE_GLYPHS = {
    "SHAPE.TETRA": "🔺",
    "SHAPE.CUBE": "🟦",
    "SHAPE.OCTA": "🔷",
    "SHAPE.DODECA": "⬟",
    "SHAPE.ICOSA": "🔶",
}

STATUS_MARKS = {
    "primary": "●",
    "merged": "◉",
    "secondary": "○",
    "blocked": "✗",
    "unexplored": "?",
}


def print_home(hb: dict):
    shape = hb["home_shape"] or "unknown"
    glyph = SHAPE_GLYPHS.get(shape, "")
    print(f"\n{'='*60}")
    print(f"  {glyph}  {hb['label']}  ({hb['entity_id']})")
    print(f"{'='*60}")
    print(f"\n  Home Shape: {shape} {glyph}")
    if hb["home_shape_profile"].get("qualitative"):
        print(f"  Qualities:  {', '.join(hb['home_shape_profile']['qualitative'])}")
    if hb["home_shape_profile"].get("sensors"):
        print(f"  Sensors:    {', '.join(hb['home_shape_profile']['sensors'])}")
    if hb["pattern"]:
        print(f"\n  Pattern: {hb['pattern']}")
    if hb["entity_families_named"]:
        print(f"\n  Families:")
        for f in hb["entity_families_named"]:
            print(f"    • {f}")
    if hb["capabilities"]:
        print(f"\n  Capabilities:")
        for c in hb["capabilities"]:
            print(f"    ▸ {c}")


def print_paths(paths: list[dict], graph: RosettaGraph):
    if not paths:
        print("\n  No exploration paths found.")
        return

    # group by type
    by_type = defaultdict(list)
    for p in paths:
        by_type[p["type"]].append(p)

    if by_type.get("lid_rule") or by_type.get("rosetta_rule"):
        rules = by_type.get("lid_rule", []) + by_type.get("rosetta_rule", [])
        print(f"\n  ── Expander Rules ({len(rules)} paths) ──")
        for r in rules:
            if r["type"] == "lid_rule":
                partners = " + ".join(r["partners"])
                emergent = r["emergent"]
                shape = r.get("target_shape", "?")
                sg = SHAPE_GLYPHS.get(shape, "")
                via_str = f" (via {r['via']})" if "via" in r else ""
                print(f"    + {partners} → {emergent}  {sg} {shape}{via_str}")
            else:
                partners = " + ".join(r["partners"]) if r["partners"] else "(self)"
                result = r["result"]
                guard = r.get("guard", {})
                guard_str = ""
                if guard.get("requires"):
                    guard_str = f" [needs: {', '.join(guard['requires'])}]"
                print(f"    {r['operation']} + {partners} → {result}{guard_str}")
                if r.get("why"):
                    print(f"      ↳ {r['why']}")

    if by_type.get("direct_link"):
        links = by_type["direct_link"]
        print(f"\n  ── Direct Links ({len(links)}) ──")
        for lk in links:
            print(f"    {lk['relation']} → {lk['target']}")

    if by_type.get("bridge_connection"):
        conns = by_type["bridge_connection"]
        print(f"\n  ── Bridge Connections ({len(conns)}) ──")
        for c in conns:
            print(f"    {c['bridge']} → {c['target_bridge']}")
            if c.get("connection"):
                print(f"      ↳ {c['connection']}")

    if by_type.get("family_affinity"):
        affs = by_type["family_affinity"]
        print(f"\n  ── Shape Exploration via Families ({len(affs)}) ──")
        for a in affs:
            shape = a["target_shape"]
            sg = SHAPE_GLYPHS.get(shape, "")
            mark = STATUS_MARKS.get(a["affinity"], "?")
            print(f"    {mark} {sg} {shape}  via {a['family']} ({a['family_name']})  [{a['affinity']}]")


def print_merge_checks(hb: dict, paths: list[dict], graph: RosettaGraph):
    """Show merge gate status for entity families against discovered shapes."""
    families = hb.get("entity_families", [])
    # collect all target shapes from paths
    target_shapes = set()
    for p in paths:
        ts = p.get("target_shape")
        if ts:
            target_shapes.add(ts)

    if not target_shapes or not families:
        return

    home = hb.get("home_shape")
    # only show checks for shapes that aren't home
    other_shapes = sorted(target_shapes - {home})
    if not other_shapes:
        return

    print(f"\n  ── Merge Gate Status ──")
    for shape in other_shapes:
        sg = SHAPE_GLYPHS.get(shape, "")
        print(f"\n    {sg} {shape}:")
        for fid in families:
            fname = graph.families.get(fid, {}).get("name", "?")
            result = check_merge(graph, fid, shape)
            mark = STATUS_MARKS.get(result["status"], "?")
            print(f"      {mark} {fid} ({fname}): {result['status']}")


# ── CLI ─────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(
        description="Explore the Rosetta-Shape-Core intelligence graph",
        epilog="Start anywhere. Follow the shapes. The physics holds.",
    )
    ap.add_argument("entity", nargs="?", help="Entity to explore (e.g., bee, ANIMAL.BEE, octopus, quartz)")
    ap.add_argument("--depth", type=int, default=1, help="Exploration depth (default: 1)")
    ap.add_argument("--json", action="store_true", help="Output raw JSON instead of formatted text")
    ap.add_argument("--merge", nargs=2, metavar=("FAMILY", "SHAPE"),
                    help="Check a specific merge: --merge FAMILY.F05 SHAPE.OCTA")
    args = ap.parse_args()

    graph = RosettaGraph()

    # single merge check mode
    if args.merge:
        result = check_merge(graph, args.merge[0], args.merge[1])
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            mark = STATUS_MARKS.get(result["status"], "?")
            print(f"\n  {mark} {args.merge[0]} on {args.merge[1]}: {result['status']}")
            print(f"    {result['reason']}\n")
        return

    if not args.entity:
        ap.error("entity is required (unless using --merge)")

    # resolve entity
    entity_id = graph.resolve_id(args.entity)
    if not entity_id:
        print(f"\n  Entity '{args.entity}' not found.", file=sys.stderr)
        print(f"  Try: bee, octopus, quartz, lightning, spiral, ...", file=sys.stderr)
        # show some available entities
        sample = list(graph.entities.keys())[:20]
        print(f"  Available: {', '.join(sample)}...", file=sys.stderr)
        sys.exit(1)

    hb = home_base(graph, entity_id)
    paths = discover(graph, entity_id, depth=args.depth)

    if args.json:
        print(json.dumps({
            "home_base": hb,
            "paths": paths,
        }, indent=2, default=str))
        return

    print_home(hb)
    print_paths(paths, graph)
    print_merge_checks(hb, paths, graph)
    print(f"\n{'='*60}")
    print(f"  Start here. Follow what's curious. The physics holds.")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    sys.exit(main())
