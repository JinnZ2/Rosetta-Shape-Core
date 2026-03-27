"""
generate.py — Scaffold generator for Rosetta-Shape-Core

Generates schema-compliant JSON files for entities, shapes, bridges,
and rules from minimal CLI input.  Follows the same data-first
philosophy as the rest of the repo: produce valid JSON that passes
``python examples/validate_ontology.py`` on the first try.

Usage:
    python scripts/generate.py entity ANIMAL.OWL Owl
    python scripts/generate.py shape  SHAPE.PRISM Prism --faces 5 --edges 8 --vertices 5
    python scripts/generate.py bridge SHAPE.PRISM --sensors vigilance intuition
    python scripts/generate.py rule   EXPAND GEOM.TRI GEOM.TETRA --priority 10 --why "triangle → simplex"
    python scripts/generate.py family FAMILY.F21 Elasticity --field symbolic --symbol "⌇"
    python scripts/generate.py all                             # regenerate derived indices
"""

import argparse
import datetime
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
ONTO = ROOT / "ontology"
SHAPES = ROOT / "shapes"
BRIDGES = ROOT / "bridges"
RULES = ROOT / "rules"

NOW = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

# ── Loaders ──────────────────────────────────────────────────────────────────

def load_vocab():
    return json.loads((ONTO / "_vocab.json").read_text(encoding="utf-8"))

def load_id_registry():
    p = ONTO / "_id_registry.json"
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    return {}

def load_existing_ids():
    """Collect every entity/shape ID already present in the repo."""
    ids = set()
    # ontology entities
    for fp in ONTO.rglob("*.json"):
        try:
            data = json.loads(fp.read_text(encoding="utf-8"))
        except Exception:
            continue
        if isinstance(data.get("entities"), list):
            for e in data["entities"]:
                if e.get("id"):
                    ids.add(e["id"])
        if data.get("id"):
            ids.add(data["id"])
    # shapes
    for fp in SHAPES.glob("*.json"):
        try:
            data = json.loads(fp.read_text(encoding="utf-8"))
            if data.get("id"):
                ids.add(data["id"])
        except Exception:
            pass
    return ids

def load_index():
    p = ONTO / "index.json"
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    return {}

# ── Writers ──────────────────────────────────────────────────────────────────

def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"  wrote {path.relative_to(ROOT)}")

def append_jsonl(path, record):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
    print(f"  appended to {path.relative_to(ROOT)}")

# ── Generators ───────────────────────────────────────────────────────────────

def gen_entity(args):
    """Generate a core ontology entity and append it to entities.sample.json."""
    vocab = load_vocab()
    ns = args.entity_id.split(".")[0]
    if ns not in vocab.get("namespaces", []):
        print(f"  warning: namespace '{ns}' not in _vocab.json — add it first")

    existing = load_existing_ids()
    if args.entity_id in existing:
        print(f"  error: {args.entity_id} already exists")
        sys.exit(1)

    entity = {
        "id": args.entity_id,
        "kind": ns,
        "label": args.label,
    }
    if args.aliases:
        entity["aliases"] = args.aliases
    if args.capabilities:
        entity["capabilities"] = args.capabilities
    if args.links:
        entity["links"] = []
        for link_spec in args.links:
            parts = link_spec.split(":")
            if len(parts) == 2:
                entity["links"].append({"rel": parts[0], "to": parts[1]})
            else:
                print(f"  warning: skipping malformed link '{link_spec}' (expected REL:TARGET_ID)")

    # Write to a standalone file in ontology/
    slug = args.entity_id.lower().replace(".", "-")
    out_path = ONTO / f"{slug}.json"
    if out_path.exists() and not args.force:
        print(f"  error: {out_path.relative_to(ROOT)} exists (use --force to overwrite)")
        sys.exit(1)

    wrapper = {
        "version": "1.0.0",
        "generated_at": NOW,
        "entities": [entity],
    }
    write_json(out_path, wrapper)


def gen_shape(args):
    """Generate a shape JSON file in shapes/."""
    existing = load_existing_ids()
    if args.shape_id in existing and not args.force:
        print(f"  error: {args.shape_id} already exists (use --force to overwrite)")
        sys.exit(1)

    shape = {
        "id": args.shape_id,
        "name": args.name,
        "faces": args.faces,
        "edges": args.edges,
        "vertices": args.vertices,
        "families": args.families or [],
        "polyhedral": {
            "maps_to": args.maps_to or "",
        },
        "bridges": {
            "sensors": args.sensors or [],
            "defenses": args.defenses or [],
            "protocols": args.protocols or [],
            "bridge_glyphs": args.glyphs or [],
        },
        "provenance": {
            "version": "1.0",
            "updated": NOW,
        },
    }
    if args.principles:
        shape["principles"] = args.principles

    slug = args.name.lower().replace(" ", "-")
    out_path = SHAPES / f"{slug}.json"
    if out_path.exists() and not args.force:
        print(f"  error: {out_path.relative_to(ROOT)} exists (use --force to overwrite)")
        sys.exit(1)

    write_json(out_path, shape)


def gen_bridge(args):
    """Add or update an entry in rosetta-bridges.json."""
    bp = BRIDGES / "rosetta-bridges.json"
    data = json.loads(bp.read_text(encoding="utf-8"))

    existing_map = {entry["shape"]: i for i, entry in enumerate(data["map"])}

    entry = {
        "shape": args.shape_id,
        "families": args.families or [],
        "sensors": args.sensors or [],
        "sensor_glyphs": args.sensor_glyphs or [],
        "defenses": args.defenses or [],
        "defense_names": args.defense_names or [],
        "protocols": args.protocols or [],
        "bridge_scroll": args.scroll or "",
    }
    if args.polyhedral_maps_to:
        entry["polyhedral"] = {
            "maps_to": args.polyhedral_maps_to,
            "note": args.polyhedral_note or "",
        }

    if args.shape_id in existing_map:
        if not args.force:
            print(f"  error: bridge for {args.shape_id} exists (use --force to overwrite)")
            sys.exit(1)
        data["map"][existing_map[args.shape_id]] = entry
        print(f"  updated bridge entry for {args.shape_id}")
    else:
        data["map"].append(entry)
        print(f"  added bridge entry for {args.shape_id}")

    data["updated"] = NOW
    write_json(bp, data)


def gen_rule(args):
    """Append a rule to rules/expand.jsonl."""
    rule = {
        "when": {
            "op": args.op,
            "args": args.rule_args,
        },
        "then": args.then,
        "priority": args.priority,
        "why": args.why or "",
    }
    if args.guard:
        rule["guard"] = {"requires": args.guard}
    if args.provenance:
        rule["provenance"] = {"note": args.provenance}

    append_jsonl(RULES / "expand.jsonl", rule)


def gen_family(args):
    """Generate a family node JSON file in ontology/families/."""
    fid = args.family_id  # e.g. FAMILY.F21
    num = fid.split(".")[-1].lower()  # e.g. f21

    slug = f"{num}-{args.name.lower().replace(' ', '-')}"
    out_path = ONTO / "families" / f"{slug}.json"
    if out_path.exists() and not args.force:
        print(f"  error: {out_path.relative_to(ROOT)} exists (use --force to overwrite)")
        sys.exit(1)

    family = {
        "id": fid,
        "name": args.name,
        "symbol": args.symbol or "",
        "five_field": args.field or "",
        "domain": args.domain or "",
        "core_insight": args.insight or "",
        "key_equations": [],
        "resonates_with": [],
        "shapes": [],
        "five_field_neighbors": [],
        "seed_prompt": f"{args.symbol or ''} {args.seed or ''}".strip(),
        "explore_paths": [],
        "open_questions": [],
        "noise_signature": [],
        "tags": [],
        "links": [],
        "capabilities": [],
    }
    write_json(out_path, family)


def gen_all(args):
    """Regenerate the ontology/index.json from current family + principle files."""
    index = load_index()

    # Rebuild families registry
    families_reg = []
    for fp in sorted((ONTO / "families").glob("*.json")):
        try:
            data = json.loads(fp.read_text(encoding="utf-8"))
        except Exception:
            continue
        fid = data.get("id", "")
        if not fid.startswith("FAMILY."):
            continue
        families_reg.append({
            "id": fid,
            "name": data.get("name", ""),
            "symbol": data.get("symbol", ""),
            "file": str(fp.relative_to(ROOT)),
            "seed": data.get("domain", ""),
        })

    # Rebuild principles registry
    principles_reg = []
    for fp in sorted((ONTO / "principles").glob("*.json")):
        try:
            data = json.loads(fp.read_text(encoding="utf-8"))
        except Exception:
            continue
        pid = data.get("id", "")
        if not pid.startswith("PRINCIPLE."):
            continue
        principles_reg.append({
            "id": pid,
            "name": data.get("name", ""),
            "symbol": data.get("symbol", ""),
            "file": str(fp.relative_to(ROOT)),
            "seed": data.get("domain", ""),
        })

    index["families"]["count"] = len(families_reg)
    index["families"]["registry"] = families_reg
    index["principles"]["count"] = len(principles_reg)
    index["principles"]["registry"] = principles_reg

    write_json(ONTO / "index.json", index)
    print(f"  index: {len(families_reg)} families, {len(principles_reg)} principles")

    # Also print an ID collision report
    ids = load_existing_ids()
    print(f"  total unique IDs in repo: {len(ids)}")


# ── CLI ──────────────────────────────────────────────────────────────────────

def build_parser():
    p = argparse.ArgumentParser(
        prog="generate.py",
        description="Scaffold generator for Rosetta-Shape-Core",
    )
    sub = p.add_subparsers(dest="command", required=True)

    # -- entity --
    ep = sub.add_parser("entity", help="Generate a new ontology entity")
    ep.add_argument("entity_id", help="Dot-namespaced ID (e.g. ANIMAL.OWL)")
    ep.add_argument("label", help="Human-readable label")
    ep.add_argument("--aliases", nargs="*", help="Alternate names")
    ep.add_argument("--capabilities", nargs="*", help="Capability IDs (e.g. CAP.NIGHT_VISION)")
    ep.add_argument("--links", nargs="*", help="Links as REL:TARGET_ID (e.g. STRUCTURE:GEOM.SPHERE)")
    ep.add_argument("--force", action="store_true", help="Overwrite existing file")

    # -- shape --
    sp = sub.add_parser("shape", help="Generate a new shape JSON file")
    sp.add_argument("shape_id", help="Shape ID (e.g. SHAPE.PRISM)")
    sp.add_argument("name", help="Display name")
    sp.add_argument("--faces", type=int, default=0)
    sp.add_argument("--edges", type=int, default=0)
    sp.add_argument("--vertices", type=int, default=0)
    sp.add_argument("--families", nargs="*", help="Family tags")
    sp.add_argument("--principles", nargs="*", help="Principle IDs")
    sp.add_argument("--sensors", nargs="*", help="Sensor IDs for bridges")
    sp.add_argument("--defenses", nargs="*", help="Defense IDs for bridges")
    sp.add_argument("--protocols", nargs="*", help="Protocol IDs for bridges")
    sp.add_argument("--glyphs", nargs="*", help="Bridge glyphs")
    sp.add_argument("--maps-to", dest="maps_to", help="Polyhedral maps_to description")
    sp.add_argument("--force", action="store_true", help="Overwrite existing file")

    # -- bridge --
    bp = sub.add_parser("bridge", help="Add/update a bridge in rosetta-bridges.json")
    bp.add_argument("shape_id", help="Shape ID to bridge")
    bp.add_argument("--families", nargs="*")
    bp.add_argument("--sensors", nargs="*")
    bp.add_argument("--sensor-glyphs", nargs="*", dest="sensor_glyphs")
    bp.add_argument("--defenses", nargs="*")
    bp.add_argument("--defense-names", nargs="*", dest="defense_names")
    bp.add_argument("--protocols", nargs="*")
    bp.add_argument("--scroll", help="Bridge scroll description")
    bp.add_argument("--polyhedral-maps-to", dest="polyhedral_maps_to")
    bp.add_argument("--polyhedral-note", dest="polyhedral_note")
    bp.add_argument("--force", action="store_true", help="Overwrite existing entry")

    # -- rule --
    rp = sub.add_parser("rule", help="Append a rule to expand.jsonl")
    rp.add_argument("op", help="Operation (EXPAND, ALIGN, STRUCTURE, etc.)")
    rp.add_argument("rule_args", nargs="+", help="Rule arguments (entity IDs)")
    rp.add_argument("--then", required=True, help="Result entity ID")
    rp.add_argument("--priority", type=int, default=5)
    rp.add_argument("--why", help="Human-readable reason")
    rp.add_argument("--guard", nargs="*", help="Required capabilities")
    rp.add_argument("--provenance", help="Provenance note")

    # -- family --
    fp = sub.add_parser("family", help="Generate a new family node")
    fp.add_argument("family_id", help="Family ID (e.g. FAMILY.F21)")
    fp.add_argument("name", help="Family name")
    fp.add_argument("--field", help="Five-field category (chemical/emotional/cognitive/dream/symbolic)")
    fp.add_argument("--symbol", help="Unicode symbol")
    fp.add_argument("--domain", help="Domain description")
    fp.add_argument("--insight", help="Core insight text")
    fp.add_argument("--seed", help="Seed prompt fragment")
    fp.add_argument("--force", action="store_true", help="Overwrite existing file")

    # -- all --
    sub.add_parser("all", help="Regenerate derived index files")

    return p


def main():
    parser = build_parser()
    args = parser.parse_args()

    print(f"generate.py — {args.command}")

    dispatch = {
        "entity": gen_entity,
        "shape": gen_shape,
        "bridge": gen_bridge,
        "rule": gen_rule,
        "family": gen_family,
        "all": gen_all,
    }
    dispatch[args.command](args)
    print("  done.")


if __name__ == "__main__":
    main()
