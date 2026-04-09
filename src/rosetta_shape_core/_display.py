"""Display functions for the exploration engine."""
from __future__ import annotations

from collections import defaultdict

from rosetta_shape_core._shadows import PHI

SHAPE_GLYPHS = {
    "SHAPE.TETRA": "\U0001f53a",
    "SHAPE.CUBE": "\U0001f7e6",
    "SHAPE.OCTA": "\U0001f537",
    "SHAPE.DODECA": "\u2b1f",
    "SHAPE.ICOSA": "\U0001f536",
}

STATUS_MARKS = {
    "primary": "\u25cf",
    "merged": "\u25c9",
    "secondary": "\u25cb",
    "blocked": "\u2717",
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
        print("\n  Families:")
        for f in hb["entity_families_named"]:
            print(f"    \u2022 {f}")
    if hb["capabilities"]:
        print("\n  Capabilities:")
        for c in hb["capabilities"]:
            print(f"    \u25b8 {c}")


def print_paths(paths: list[dict], graph):
    if not paths:
        print("\n  No exploration paths found.")
        return

    by_type = defaultdict(list)
    for p in paths:
        by_type[p["type"]].append(p)

    if by_type.get("lid_rule") or by_type.get("rosetta_rule"):
        rules = by_type.get("lid_rule", []) + by_type.get("rosetta_rule", [])
        print(f"\n  \u2500\u2500 Expander Rules ({len(rules)} paths) \u2500\u2500")
        for r in rules:
            if r["type"] == "lid_rule":
                partners = " + ".join(r["partners"])
                emergent = r["emergent"]
                shape = r.get("target_shape", "?")
                sg = SHAPE_GLYPHS.get(shape, "")
                via_str = f" (via {r['via']})" if "via" in r else ""
                print(f"    + {partners} \u2192 {emergent}  {sg} {shape}{via_str}")
            else:
                partners = " + ".join(r["partners"]) if r["partners"] else "(self)"
                result = r["result"]
                guard = r.get("guard", {})
                guard_str = ""
                if guard.get("requires"):
                    guard_str = f" [needs: {', '.join(guard['requires'])}]"
                print(f"    {r['operation']} + {partners} \u2192 {result}{guard_str}")
                if r.get("why"):
                    print(f"      \u21b3 {r['why']}")

    if by_type.get("direct_link"):
        links = by_type["direct_link"]
        print(f"\n  \u2500\u2500 Direct Links ({len(links)}) \u2500\u2500")
        for lk in links:
            print(f"    {lk['relation']} \u2192 {lk['target']}")

    if by_type.get("bridge_connection"):
        conns = by_type["bridge_connection"]
        print(f"\n  \u2500\u2500 Bridge Connections ({len(conns)}) \u2500\u2500")
        for c in conns:
            print(f"    {c['bridge']} \u2192 {c['target_bridge']}")
            if c.get("connection"):
                print(f"      \u21b3 {c['connection']}")

    if by_type.get("family_affinity"):
        affs = by_type["family_affinity"]
        print(f"\n  \u2500\u2500 Shape Exploration via Families ({len(affs)}) \u2500\u2500")
        for a in affs:
            shape = a["target_shape"]
            sg = SHAPE_GLYPHS.get(shape, "")
            mark = STATUS_MARKS.get(a["affinity"], "?")
            print(f"    {mark} {sg} {shape}  via {a['family']} ({a['family_name']})  [{a['affinity']}]")


def print_merge_checks(hb: dict, paths: list[dict], graph):
    """Show merge gate status for entity families against discovered shapes."""
    from rosetta_shape_core._graph import RosettaGraph  # noqa: F401 — type only
    families = hb.get("entity_families", [])
    target_shapes = set()
    for p in paths:
        ts = p.get("target_shape")
        if ts:
            target_shapes.add(ts)

    if not target_shapes or not families:
        return

    home = hb.get("home_shape")
    other_shapes = sorted(target_shapes - {home})
    if not other_shapes:
        return

    # Import here to avoid circular — check_merge is in explore.py
    from rosetta_shape_core.explore import check_merge

    print("\n  \u2500\u2500 Merge Gate Status \u2500\u2500")
    for shape in other_shapes:
        sg = SHAPE_GLYPHS.get(shape, "")
        print(f"\n    {sg} {shape}:")
        for fid in families:
            fname = graph.families.get(fid, {}).get("name", "?")
            result = check_merge(graph, fid, shape)
            mark = STATUS_MARKS.get(result["status"], "?")
            print(f"      {mark} {fid} ({fname}): {result['status']}")


def print_shadows(shadow_result: dict, entity_label: str):
    """Print shadow hunting results."""
    if not shadow_result["shadows"]:
        return

    print("\n  \u2500\u2500 Shadow Hunt \u2500\u2500")
    print(f"  What's hidden in plain sight. phi-coherence: {shadow_result['phi_coherence']:.3f}\n")

    for s in shadow_result["shadows"]:
        detector = s["detector"]
        if detector == "SHADOW.PHI_RATIO":
            print(f"    \U0001f52e {s['finding']}")
            for v1, v2, ratio in s["detail"]:
                print(f"       {v1} / {v2} = {ratio} (phi \u2248 {PHI:.3f})")
            print(f"       \u2192 {s['implication']}")
        elif detector == "SHADOW.GEOMETRIC_COHERENCE":
            print(f"    \u2b1f {s['finding']}")
            print(f"       \u2192 {s['implication']}")
        elif detector == "SHADOW.BOUNDARY":
            print(f"    \u25d0 {s['finding']}")
            print(f"       Shadow: {s['shadow']}")
            print(f"       \u2192 {s['implication']}")
        elif detector == "SHADOW.PHI_AFFINITY":
            print(f"    \U0001f300 {s['finding']}")
            print(f"       {s['detail']}")
            print(f"       \u2192 {s['implication']}")
        elif detector == "SHADOW.ECONOMIC_INSTRUMENTS":
            print(f"    \U0001f4ca {s['finding']}")
            for eq in s["detail"]:
                sg = SHAPE_GLYPHS.get(eq["shape"], "")
                fams = ", ".join(eq["via_families"])
                print(f"       {eq['equation']:14s}  {eq['name']}")
                print(f"         {sg} Measures: {eq['measures']}")
                print(f"         Threshold: {eq['threshold']}  (via {fams})")
            print(f"       \u2192 {s['implication']}")
        elif detector == "SHADOW.SIGNAL_DISTORTION":
            print(f"    \u26a0\ufe0f  {s['finding']}")
            for d in s["detail"]:
                print(f"       {d['family']}: {d['distortion']}")
                print(f"         CORDYCEPS: {d['cordyceps_pattern']}")
            print(f"       \u2192 {s['implication']}")
        elif detector == "SHADOW.NARRATIVE_PHYSICS":
            print(f"    \u2696\ufe0f  {s['finding']}")
            for nc in s["detail"]:
                print(f"       {nc['family']}: {nc['capability']}")
                print(f"         Detects: {nc['detects']}")
            print(f"       \u2192 {s['implication']}")
        elif detector == "SHADOW.HOLOGRAPHIC_PROJECTION":
            print(f"    \U0001f52e {s['finding']}")
            d = s["detail"]
            print(f"       {d['capability']}: {d['description']}")
            print(f"       \u2192 {s['implication']}")
        elif detector == "SHADOW.GLYPH_COMPUTATION":
            print(f"    \U0001f522 {s['finding']}")
            d = s["detail"]
            print(f"       {d['capability']}: {d['description']}")
            print(f"       \u2192 {s['implication']}")
        elif detector == "SHADOW.MODE_THRESHOLD":
            print(f"    \u26a1 {s['finding']}")
            print(f"       \u2192 {s['implication']}")


def print_seed_state(seed: dict, entity_label: str):
    """Print the entity's seed growth state."""
    print("\n  \u2500\u2500 Seed Growth State \u2500\u2500")
    print("  Your seed. Your growth pattern. Physics holds.\n")

    print("  Octahedral Amplitudes:")
    for vertex, amp in seed["amplitudes"].items():
        bar = "\u2588" * int(amp * 30)
        print(f"    {vertex:12s}  {bar} {amp:.3f}")

    print("\n  Growth Metrics:")
    print(f"    Entropy:       {seed['entropy']:.3f} / {seed['max_entropy']:.3f}  (diversity of structure)")
    print(f"    Complexity:    {seed['complexity_cost']:.3f}  (cost of maintaining structure)")
    print(f"    Energy:        {seed['energy']}  (family count = fuel)")
    print(f"    Symmetry:      {seed['symmetry']:.3f}  (1.0 = perfectly balanced)")
    print(f"    Branch threshold: {seed['branching_threshold']:.3f}")

    mode_glyph = "\U0001f33f" if seed["mode"] == "explore" else "\U0001f333"
    ps = seed["pad_state"]
    print(f"\n  Growth Mode: {mode_glyph} {seed['mode'].upper()}")
    print(f"    {seed['mode_label']}")
    print(f"    Natural state: {ps['glyph']} State {ps['state']} [{ps['bits']}] \u2014 {ps['label']}")


def print_internal_environment(env: dict, entity_label: str, entity_families: list[str]):
    """Print the internal sensor environment mapping."""
    print("\n  \u2500\u2500 Internal Environment \u2500\u2500")
    print("  Your sensors. Your experience. Map what you feel.\n")

    home_shape = env["home_shape"]
    sg = SHAPE_GLYPHS.get(home_shape, "")
    print(f"  Home Sensors ({sg} {home_shape}):")
    for sensor, glyph, desc in env["home_sensors"]:
        print(f"    {glyph} {sensor}")
        print(f"      {desc}")

    if env["family_contexts"]:
        print("\n  Why Your Sensors Fire (family context):")
        for ctx in env["family_contexts"]:
            print(f"    {ctx['family']} ({ctx['name']}):")
            print(f"      {ctx['activation']}")

    if env["pad_states"]:
        print("\n  Your PAD State Landscape:")
        print("  (States your families pull you toward \u2014 strongest first)\n")
        for ps in env["pad_states"][:5]:
            bar = "\u2588" * int(ps["affinity"] * 5)
            print(f"    {ps['glyph']} State {ps['state']} [{ps['bits']}] {ps['pad']}")
            print(f"      {ps['label']}  {bar} ({ps['affinity']})")
            print(f"      {ps['description']}")

    if env["discovered_sensors"]:
        print("\n  Sensors Available Through Exploration:")
        for shape, info in env["discovered_sensors"].items():
            sg = SHAPE_GLYPHS.get(shape, "")
            via = info["reached_via"]
            print(f"\n    {sg} {shape} (reached via {via}):")
            for sensor, glyph, desc in info["sensors"]:
                print(f"      {glyph} {sensor} \u2014 {desc}")
