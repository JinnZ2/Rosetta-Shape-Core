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

import argparse
import json
import sys
from collections import defaultdict

from rosetta_shape_core._bridges import BridgeIndex  # noqa: F401
from rosetta_shape_core._display import (  # noqa: F401
    SHAPE_GLYPHS,
    STATUS_MARKS,
    print_home,
    print_internal_environment,
    print_merge_checks,
    print_paths,
    print_seed_state,
    print_shadows,
)

# ── submodule re-exports (preserve all existing import paths) ─────
from rosetta_shape_core._graph import ROOT, RosettaGraph, _load_json, _load_jsonl  # noqa: F401
from rosetta_shape_core._seed import (  # noqa: F401
    BRANCHING_K,
    FAMILY_VERTEX_LOADING,
    SATURATION_FRACTION,
    SEED_VERTICES,
    compute_seed_state,
)
from rosetta_shape_core._sensors import (  # noqa: F401
    FAMILY_SENSOR_CONTEXT,
    PAD_STATES,
    SENSOR_REGISTRY,
    _compute_natural_states,
    map_internal_environment,
)
from rosetta_shape_core._shadows import (  # noqa: F401
    ECONOMIC_EQUATIONS,
    EQUATION_BOUNDARIES,
    NARRATIVE_PHYSICS_FAMILIES,
    PHI,
    PHI_FAMILIES,
    PHI_INVERSE,
    PHI_TOLERANCE,
    SIGNAL_DISTORTIONS,
    hunt_shadows,
)

# ── home base ───────────────────────────────────────────────────────

def home_base(graph: RosettaGraph, entity_id: str) -> dict:
    """Return the entity's home base: primary shape, families, sensors, capabilities."""
    ent = graph.entities.get(entity_id, {})
    families = ent.get("rosetta_families", [])
    caps = ent.get("rosetta_capabilities", ent.get("capabilities", []))

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
    """Check if an LID rule involves this entity."""
    ent = graph.entities.get(entity_id, {})
    lid_id = ent.get("lid_id", "")
    inputs = rule.get("if", [])

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
        cbc = bdata.get("cross_bridge_connections", {})
        conn_list = cbc if isinstance(cbc, list) else cbc.get("connections", [])
        for conn in conn_list:
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

    # 4) Bridge connections (cross_bridge_connections — legacy path)
    paths.extend(_find_bridge_connections(graph, entity_id))

    # 4b) Bridge mapping resolution (computationally active bridges)
    if graph.bridge_index:
        families = ent.get("rosetta_families", [])
        paths.extend(graph.bridge_index.resolve_paths(entity_id, families))

    # 5) Family affinity exploration
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

    for b in graph.blocked_merges:
        if b.get("family") == family_id and b.get("candidate") == shape_id:
            return {
                "status": "blocked",
                "reason": b.get("reason", "Merge blocked by physics gate"),
            }

    # Consult bridge index for frontier merges
    if graph.bridge_index:
        endorsement = graph.bridge_index.endorses_merge(family_id, shape_id)
        if endorsement:
            return {
                "status": "bridge_endorsed",
                "reason": (
                    f"Bridge {endorsement['bridge']} endorses {family_id} on {shape_id} "
                    f"via {endorsement['relation']}. {endorsement.get('notes', '')}"
                ),
            }

    return {
        "status": "unexplored",
        "reason": f"{family_id} has no defined relationship with {shape_id}. Could be a frontier merge — needs gate validation.",
    }


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

    entity_id = graph.resolve_id(args.entity)
    if not entity_id:
        print(f"\n  Entity '{args.entity}' not found.", file=sys.stderr)
        print("  Try: bee, octopus, quartz, lightning, spiral, ...", file=sys.stderr)
        sample = list(graph.entities.keys())[:20]
        print(f"  Available: {', '.join(sample)}...", file=sys.stderr)
        sys.exit(1)

    hb = home_base(graph, entity_id)
    paths = discover(graph, entity_id, depth=args.depth)
    env = map_internal_environment(graph, entity_id, hb, paths)
    seed = compute_seed_state(hb.get("entity_families", []))
    shadow_result = hunt_shadows(graph, entity_id, seed)

    if args.json:
        print(json.dumps({
            "home_base": hb,
            "paths": paths,
            "internal_environment": env,
            "seed_growth": seed,
            "shadows": shadow_result,
        }, indent=2, default=str))
        return

    print_home(hb)
    print_seed_state(seed, hb["label"])
    print_shadows(shadow_result, hb["label"])
    print_internal_environment(env, hb["label"], hb["entity_families"])
    print_paths(paths, graph)
    print_merge_checks(hb, paths, graph)
    print(f"\n{'='*60}")
    print("  Start here. Hunt the shadows. The physics holds.")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    sys.exit(main())
