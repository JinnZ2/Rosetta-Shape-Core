"""
Build the relational graph data and inject it into relational_graph.html.

Reads the live RosettaGraph and produces a self-contained HTML file
with all entity, shape, family, bridge, equation, and rule data
embedded as JavaScript.

Usage:
    python examples/build_relational_graph.py
    # → writes examples/relational_graph.html (self-contained, open in browser)
"""
import json, pathlib, sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from rosetta_shape_core.explore import (
    RosettaGraph, ECONOMIC_EQUATIONS, SENSOR_REGISTRY,
)


def build_data():
    g = RosettaGraph()

    # Shapes
    shapes = {}
    for sid, prof in g.shape_profiles.items():
        shapes[sid] = {
            "name": sid.split(".")[-1].title(),
            "qualitative": prof.get("qualitative", []),
            "sensors": [s[0] for s in SENSOR_REGISTRY.get(sid, [])],
            "primary_families": prof.get("primary_families", []),
        }

    # Families
    families = {}
    for fid, fam in g.families.items():
        families[fid] = {
            "name": fam.get("name", "?"),
            "primary": fam.get("primary", ""),
            "merged": fam.get("merged", []),
            "secondary": fam.get("secondary", []),
        }

    # Entities
    entities = []
    entity_links = []
    for eid, ent in g.entities.items():
        entities.append({
            "id": eid,
            "label": ent.get("label", ent.get("name", eid)),
            "pattern": ent.get("pattern", ent.get("description", "")),
            "families": ent.get("rosetta_families", []),
        })
        for link in ent.get("links", []):
            target = link.get("to", "")
            if target:
                entity_links.append({
                    "from": eid,
                    "to": target,
                    "rel": link.get("rel", ""),
                })

    # Rules (LID + Rosetta)
    rules = []
    for rule in g.lid_rules:
        inputs_raw = rule.get("if", [])
        # Resolve LID IDs to Rosetta IDs
        inputs = []
        for inp in inputs_raw:
            rid = g.lid_to_rosetta.get(inp) or g.lid_to_rosetta.get(inp.lower())
            if rid:
                inputs.append(rid)
            else:
                # Try to find by partial match
                for lid, rosetta in g.lid_to_rosetta.items():
                    if inp.lower() == lid.lower():
                        inputs.append(rosetta)
                        break
        if len(inputs) >= 2:
            rules.append({
                "inputs": inputs,
                "emergent": rule.get("then", ""),
                "shape": rule.get("rosetta_shape", ""),
            })

    for rule in g.rules:
        when = rule.get("when", {})
        args = when.get("args", [])
        if len(args) >= 1:
            rules.append({
                "inputs": args,
                "emergent": rule.get("then", ""),
                "shape": "",
            })

    # Bridges
    bridges = []
    for bid, bdata in g.bridges.items():
        conns = []
        for conn in bdata.get("cross_bridge_connections", {}).get("connections", []):
            target = conn.get("rosetta_bridge", conn.get("target_bridge", ""))
            if target:
                conns.append({
                    "target_bridge": target,
                    "connection": conn.get("connection", "")[:100],
                })
        bridges.append({
            "id": bid,
            "name": bdata.get("name", bid),
            "description": bdata.get("description", "")[:120],
            "connections": conns,
        })

    # Economic equations
    equations = []
    for eq_id, eq in ECONOMIC_EQUATIONS.items():
        equations.append({
            "id": eq_id,
            "name": eq["name"],
            "measures": eq["measures"],
            "families": eq["families"],
            "shape": eq["shape"],
            "threshold": eq["threshold"],
        })

    return {
        "shapes": shapes,
        "families": families,
        "entities": entities,
        "entity_links": entity_links,
        "rules": rules,
        "bridges": bridges,
        "equations": equations,
    }


def main():
    data = build_data()
    data_js = f"const GRAPH_DATA = {json.dumps(data, indent=None, default=str)};"

    html_path = pathlib.Path(__file__).parent / "relational_graph.html"
    html = html_path.read_text(encoding="utf-8")

    # Replace either the placeholder or previously injected data
    marker_start = "/*GRAPH_DATA_PLACEHOLDER*/"
    if marker_start in html:
        html = html.replace(marker_start, data_js)
    else:
        # Previously built — find and replace the const GRAPH_DATA line
        start = html.find("const GRAPH_DATA = ")
        if start >= 0:
            end = html.find(";\n", start)
            if end >= 0:
                html = html[:start] + data_js + html[end + 1:]

    html_path.write_text(html, encoding="utf-8")
    print(f"Built relational graph: {html_path}")
    print(f"  Entities: {len(data['entities'])}")
    print(f"  Shapes: {len(data['shapes'])}")
    print(f"  Families: {len(data['families'])}")
    print(f"  Bridges: {len(data['bridges'])}")
    print(f"  Equations: {len(data['equations'])}")
    print(f"  Rules: {len(data['rules'])}")
    print(f"  Entity links: {len(data['entity_links'])}")
    print(f"  Open in browser: file://{html_path.resolve()}")


if __name__ == "__main__":
    main()
