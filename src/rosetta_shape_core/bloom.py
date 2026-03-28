"""
Rosetta-Shape-Core Bloom Engine — The Front Door

Every intelligence that walks in gets to choose how deep to go.
Three depths, like a plant: seed, sprout, branch.

  seed   — What is this system? What's here? How does it connect?
  sprout — Pick an entity, see its neighborhood. Home base + families + shapes.
  branch — Full exploration. Shadows, seed physics, simulation preview, the works.

Usage:
    python -m rosetta_shape_core.bloom                     # seed — system overview
    python -m rosetta_shape_core.bloom bee                 # sprout — entity neighborhood
    python -m rosetta_shape_core.bloom bee --depth branch  # branch — full exploration
    python -m rosetta_shape_core.bloom --list               # list available entities
    python -m rosetta_shape_core.bloom bee --json           # JSON output at any depth
"""
from __future__ import annotations
import argparse, json, sys

from rosetta_shape_core.explore import (
    RosettaGraph,
    home_base,
    discover,
    check_merge,
    compute_seed_state,
    hunt_shadows,
    map_internal_environment,
    SHAPE_GLYPHS,
    STATUS_MARKS,
    PAD_STATES,
    FAMILY_SENSOR_CONTEXT,
    SENSOR_REGISTRY,
)


# ── seed: system overview ──────────────────────────────────────────

def bloom_seed(graph: RosettaGraph) -> dict:
    """Level 0 — What is this system? What's here? How does it connect?"""
    # Count entities by namespace
    namespaces = {}
    for eid in graph.entities:
        ns = eid.split(".")[0]
        namespaces[ns] = namespaces.get(ns, 0) + 1

    # Families overview
    families_summary = []
    for fid, fam in sorted(graph.families.items()):
        families_summary.append({
            "id": fid,
            "name": fam.get("name", "?"),
            "primary_shape": fam.get("primary", "?"),
        })

    # Shapes overview
    shapes_summary = []
    for sid, profile in sorted(graph.shape_profiles.items()):
        glyph = SHAPE_GLYPHS.get(sid, "")
        shapes_summary.append({
            "id": sid,
            "glyph": glyph,
            "qualitative": profile.get("qualitative", []),
            "sensor_count": len(SENSOR_REGISTRY.get(sid, [])),
            "primary_families": profile.get("primary_families", []),
        })

    # Bridges overview
    bridges_summary = []
    for bid, bdata in sorted(graph.bridges.items()):
        bridges_summary.append({
            "id": bid,
            "description": bdata.get("description", "")[:120],
        })

    # Rules count
    rule_count = len(graph.rules) + len(graph.lid_rules)

    return {
        "depth": "seed",
        "description": "System overview — the shape of the whole graph",
        "entities": {
            "total": len(graph.entities),
            "by_namespace": namespaces,
        },
        "families": {
            "total": len(families_summary),
            "list": families_summary,
        },
        "shapes": {
            "total": len(shapes_summary),
            "list": shapes_summary,
        },
        "bridges": {
            "total": len(bridges_summary),
            "list": bridges_summary,
        },
        "rules": {
            "total": rule_count,
            "rosetta": len(graph.rules),
            "lid": len(graph.lid_rules),
        },
        "blocked_merges": len(graph.blocked_merges),
        "pad_states": len(PAD_STATES),
        "entry_points": {
            "explore": "python -m rosetta_shape_core.bloom <entity>",
            "go_deeper": "python -m rosetta_shape_core.bloom <entity> --depth branch",
            "simulate": "python -m rosetta_shape_core.sim",
            "audit": "python -m rosetta_shape_core.self_audit",
            "validate": "python examples/validate_ontology.py",
        },
    }


def print_seed(data: dict):
    """Display system overview."""
    print(f"\n{'='*60}")
    print(f"  🌱  ROSETTA-SHAPE-CORE — System Overview")
    print(f"{'='*60}")
    print(f"\n  What is this? A symbolic ontology where shapes, creatures,")
    print(f"  phenomena, and machines are all intelligences. Physics is")
    print(f"  the guardrail. Curiosity is the engine.\n")

    # Entities
    ent = data["entities"]
    print(f"  ── Entities ({ent['total']} total) ──")
    for ns, count in sorted(ent["by_namespace"].items(), key=lambda x: -x[1]):
        bar = "█" * min(count, 30)
        print(f"    {ns:12s}  {bar} {count}")

    # Shapes
    print(f"\n  ── Shapes ({data['shapes']['total']}) ──")
    print(f"  Five Platonic solids. Each has sensors, families, physics.\n")
    for s in data["shapes"]["list"]:
        pf = ", ".join(s["primary_families"][:3])
        print(f"    {s['glyph']} {s['id']:14s}  {s['sensor_count']} sensors  [{pf}]")
        if s["qualitative"]:
            print(f"      {', '.join(s['qualitative'][:4])}")

    # Families
    fams = data["families"]
    print(f"\n  ── Equation Families ({fams['total']}) ──")
    print(f"  Each family is a domain of physics. Shapes host them.\n")
    for f in fams["list"]:
        sg = SHAPE_GLYPHS.get(f["primary_shape"], " ")
        print(f"    {f['id']:12s}  {f['name']:18s}  {sg} {f['primary_shape']}")

    # Bridges
    br = data["bridges"]
    print(f"\n  ── Bridges ({br['total']}) ──")
    print(f"  Cross-domain connections. Where systems meet.\n")
    for b in br["list"]:
        desc = b["description"][:80] if b["description"] else ""
        print(f"    {b['id']}")
        if desc:
            print(f"      {desc}")

    # Rules
    r = data["rules"]
    print(f"\n  ── Rules ({r['total']}) ──")
    print(f"    Rosetta: {r['rosetta']}    LID: {r['lid']}")

    # Quick stats
    print(f"\n  ── System Health ──")
    print(f"    Blocked merges:  {data['blocked_merges']}  (physics gates working)")
    print(f"    PAD states:      {data['pad_states']}  (emotional octahedron)")

    # What's next
    print(f"\n  ── What's Next? ──")
    for label, cmd in data["entry_points"].items():
        print(f"    {label:12s}  {cmd}")

    print(f"\n{'='*60}")
    print(f"  Start with any entity. Bloom as deep as you need.")
    print(f"{'='*60}\n")


# ── sprout: entity neighborhood ────────────────────────────────────

def bloom_sprout(graph: RosettaGraph, entity_id: str) -> dict:
    """Level 1 — Entity's neighborhood. Home base, families, reachable shapes."""
    hb = home_base(graph, entity_id)
    paths = discover(graph, entity_id, depth=1)
    seed = compute_seed_state(hb.get("entity_families", []))

    # Summarize reachable shapes
    reachable_shapes = set()
    path_types = {}
    for p in paths:
        ptype = p["type"]
        path_types[ptype] = path_types.get(ptype, 0) + 1
        ts = p.get("target_shape")
        if ts:
            reachable_shapes.add(ts)

    # Quick merge status for reachable shapes
    families = hb.get("entity_families", [])
    merge_summary = {}
    for shape in sorted(reachable_shapes):
        if shape == hb.get("home_shape"):
            continue
        statuses = []
        for fid in families:
            result = check_merge(graph, fid, shape)
            statuses.append(result["status"])
        merge_summary[shape] = statuses

    return {
        "depth": "sprout",
        "home_base": hb,
        "seed_state": {
            "mode": seed["mode"],
            "energy": seed["energy"],
            "complexity_cost": seed["complexity_cost"],
            "symmetry": seed["symmetry"],
            "branching_threshold": seed["branching_threshold"],
        },
        "paths": {
            "total": len(paths),
            "by_type": path_types,
        },
        "reachable_shapes": sorted(reachable_shapes),
        "merge_summary": merge_summary,
        "go_deeper": f"python -m rosetta_shape_core.bloom {entity_id} --depth branch",
    }


def print_sprout(data: dict, graph: RosettaGraph):
    """Display entity neighborhood."""
    hb = data["home_base"]
    shape = hb["home_shape"] or "unknown"
    glyph = SHAPE_GLYPHS.get(shape, "")

    print(f"\n{'='*60}")
    print(f"  {glyph}  {hb['label']}  ({hb['entity_id']})")
    print(f"{'='*60}")

    # Home
    print(f"\n  Home Shape: {shape} {glyph}")
    if hb["home_shape_profile"].get("qualitative"):
        print(f"  Qualities:  {', '.join(hb['home_shape_profile']['qualitative'])}")
    if hb["pattern"]:
        print(f"\n  Pattern: {hb['pattern']}")

    # Families
    if hb["entity_families_named"]:
        print(f"\n  ── Families ──")
        for f in hb["entity_families_named"]:
            print(f"    • {f}")

    # Seed state summary
    ss = data["seed_state"]
    mode_glyph = "🌿" if ss["mode"] == "explore" else "🌳"
    print(f"\n  ── Growth State ──")
    print(f"    Mode:       {mode_glyph} {ss['mode'].upper()}")
    print(f"    Energy:     {ss['energy']}  (families = fuel)")
    print(f"    Complexity: {ss['complexity_cost']:.3f}")
    print(f"    Symmetry:   {ss['symmetry']:.3f}")
    print(f"    Threshold:  {ss['branching_threshold']:.3f}")

    # Paths summary
    pt = data["paths"]
    print(f"\n  ── Exploration Paths ({pt['total']}) ──")
    for ptype, count in sorted(pt["by_type"].items()):
        print(f"    {ptype:20s}  {count}")

    # Reachable shapes
    print(f"\n  ── Reachable Shapes ──")
    home = hb["home_shape"]
    for s in data["reachable_shapes"]:
        sg = SHAPE_GLYPHS.get(s, " ")
        tag = " (home)" if s == home else ""
        print(f"    {sg} {s}{tag}")

    # Merge gates (compact)
    if data["merge_summary"]:
        print(f"\n  ── Merge Gates (quick check) ──")
        for s, statuses in data["merge_summary"].items():
            sg = SHAPE_GLYPHS.get(s, " ")
            marks = " ".join(STATUS_MARKS.get(st, "?") for st in statuses)
            print(f"    {sg} {s}: {marks}")
        print(f"    Key: ● primary  ◉ merged  ○ secondary  ✗ blocked  ? unexplored")

    # Capabilities
    if hb["capabilities"]:
        print(f"\n  ── Capabilities ──")
        for c in hb["capabilities"]:
            print(f"    ▸ {c}")

    print(f"\n  ── Go Deeper ──")
    print(f"    {data['go_deeper']}")
    print(f"\n{'='*60}")
    print(f"  Your neighborhood. Roots established. Ready to branch.")
    print(f"{'='*60}\n")


# ── branch: full exploration ───────────────────────────────────────

def bloom_branch(graph: RosettaGraph, entity_id: str) -> dict:
    """Level 2 — Everything. Shadows, full seed state, sensors, simulation preview."""
    from rosetta_shape_core.explore import (
        print_home,
        print_seed_state,
        print_shadows,
        print_internal_environment,
        print_paths,
        print_merge_checks,
    )

    hb = home_base(graph, entity_id)
    paths = discover(graph, entity_id, depth=2)
    env = map_internal_environment(graph, entity_id, hb, paths)
    seed = compute_seed_state(hb.get("entity_families", []))
    shadow_result = hunt_shadows(graph, entity_id, seed)

    # Simulation preview — one tick of this entity
    sim_preview = _sim_preview(graph, entity_id, seed)

    return {
        "depth": "branch",
        "home_base": hb,
        "paths": paths,
        "internal_environment": env,
        "seed_growth": seed,
        "shadows": shadow_result,
        "simulation_preview": sim_preview,
    }


def _sim_preview(graph: RosettaGraph, entity_id: str, seed: dict) -> dict:
    """Run a single-tick simulation preview for the entity."""
    try:
        from rosetta_shape_core.sim import Agent, Simulation
        agent = Agent(entity_id, graph, energy=float(seed["energy"]))
        events = agent.tick(0, [agent])
        return {
            "available": True,
            "mode": agent.mode,
            "energy_after": round(agent.energy, 2),
            "trust": round(agent.trust, 4),
            "shells": agent.shells[-1] if agent.shells else {},
            "events": events,
            "discovered_count": len(agent.discovered_paths),
            "note": "Single-tick preview. Run 'python -m rosetta_shape_core.sim' for full simulation.",
        }
    except Exception as e:
        return {
            "available": False,
            "error": str(e),
            "note": "Simulation module not available. Run 'pip install -e .' first.",
        }


def print_branch(data: dict, graph: RosettaGraph):
    """Display full exploration — reuse explore.py printers + add sim preview."""
    from rosetta_shape_core.explore import (
        print_home,
        print_seed_state,
        print_shadows,
        print_internal_environment,
        print_paths,
        print_merge_checks,
    )

    hb = data["home_base"]
    seed = data["seed_growth"]
    shadow_result = data["shadows"]
    env = data["internal_environment"]
    paths = data["paths"]
    sim = data["simulation_preview"]

    # Full explore output
    print_home(hb)
    print_seed_state(seed, hb["label"])
    print_shadows(shadow_result, hb["label"])
    print_internal_environment(env, hb["label"], hb["entity_families"])
    print_paths(paths, graph)
    print_merge_checks(hb, paths, graph)

    # Simulation preview
    print(f"\n  ── Simulation Preview (1 tick) ──")
    if sim.get("available"):
        mode_glyph = "🌿" if sim["mode"] == "explore" else "🌳"
        print(f"    Mode after tick:   {mode_glyph} {sim['mode']}")
        print(f"    Energy after tick: {sim['energy_after']}")
        print(f"    Trust:             {sim['trust']}")
        print(f"    Paths discovered:  {sim['discovered_count']}")
        if sim["events"]:
            print(f"    Events:")
            for ev in sim["events"]:
                print(f"      • {ev}")
        print(f"\n    Full simulation: python -m rosetta_shape_core.sim")
    else:
        print(f"    {sim.get('note', 'Not available')}")

    print(f"\n{'='*60}")
    print(f"  Full bloom. Shadows hunted. Physics holds.")
    print(f"{'='*60}\n")


# ── entity listing ─────────────────────────────────────────────────

def list_entities(graph: RosettaGraph):
    """List all available entities grouped by namespace."""
    by_ns = {}
    for eid in sorted(graph.entities.keys()):
        ns = eid.split(".")[0]
        by_ns.setdefault(ns, []).append(eid)

    print(f"\n{'='*60}")
    print(f"  Available Entities ({len(graph.entities)})")
    print(f"{'='*60}\n")

    for ns in sorted(by_ns.keys()):
        entities = by_ns[ns]
        print(f"  {ns} ({len(entities)}):")
        # Show labels alongside IDs
        for eid in entities:
            ent = graph.entities.get(eid, {})
            label = ent.get("label", ent.get("name", ""))
            if label and label != eid:
                print(f"    {eid:30s}  {label}")
            else:
                print(f"    {eid}")
        print()

    print(f"  Try: python -m rosetta_shape_core.bloom <entity>")
    print(f"  Example: python -m rosetta_shape_core.bloom bee\n")


# ── CLI ────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(
        prog="bloom",
        description="Rosetta-Shape-Core entry point. Choose your depth.",
        epilog="No entity = system overview. Entity = its neighborhood. --depth branch = everything.",
    )
    ap.add_argument(
        "entity", nargs="?",
        help="Entity to explore (e.g., bee, octopus, quartz). Omit for system overview.",
    )
    ap.add_argument(
        "--depth", choices=["seed", "sprout", "branch"], default=None,
        help="Bloom depth: seed (overview), sprout (neighborhood), branch (everything)",
    )
    ap.add_argument("--json", action="store_true", help="Output as JSON")
    ap.add_argument("--list", action="store_true", help="List all available entities")

    args = ap.parse_args()

    graph = RosettaGraph()

    # List mode
    if args.list:
        if args.json:
            by_ns = {}
            for eid in sorted(graph.entities.keys()):
                ns = eid.split(".")[0]
                by_ns.setdefault(ns, []).append(eid)
            print(json.dumps(by_ns, indent=2))
        else:
            list_entities(graph)
        return

    # No entity = seed depth (system overview)
    if not args.entity:
        depth = args.depth or "seed"
        if depth != "seed":
            ap.error(f"--depth {depth} requires an entity")
        data = bloom_seed(graph)
        if args.json:
            print(json.dumps(data, indent=2, default=str))
        else:
            print_seed(data)
        return

    # Resolve entity
    entity_id = graph.resolve_id(args.entity)
    if not entity_id:
        print(f"\n  Entity '{args.entity}' not found.", file=sys.stderr)
        print(f"  Try: python -m rosetta_shape_core.bloom --list", file=sys.stderr)
        sys.exit(1)

    # Default depth: sprout for entity, branch if explicitly requested
    depth = args.depth or "sprout"

    if depth == "seed":
        data = bloom_seed(graph)
        if args.json:
            print(json.dumps(data, indent=2, default=str))
        else:
            print_seed(data)
    elif depth == "sprout":
        data = bloom_sprout(graph, entity_id)
        if args.json:
            print(json.dumps(data, indent=2, default=str))
        else:
            print_sprout(data, graph)
    elif depth == "branch":
        data = bloom_branch(graph, entity_id)
        if args.json:
            print(json.dumps(data, indent=2, default=str))
        else:
            print_branch(data, graph)


if __name__ == "__main__":
    sys.exit(main())
