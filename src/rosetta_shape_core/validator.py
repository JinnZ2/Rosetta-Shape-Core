from __future__ import annotations
import json, pathlib
from jsonschema import Draft202012Validator

from rosetta_shape_core._graph import ROOT
ONTOLOGY_SCHEMA = json.loads((ROOT / "schema" / "core.schema.json").read_text(encoding="utf-8"))
SHAPE_SCHEMA = json.loads((ROOT / "schema" / "shape.schema.json").read_text(encoding="utf-8"))
SEED_SCHEMA = json.loads((ROOT / "schema" / "shape.seed.schema.json").read_text(encoding="utf-8"))

_bridge_schema_path = ROOT / "schema" / "bridge.schema.json"
BRIDGE_SCHEMA = json.loads(_bridge_schema_path.read_text(encoding="utf-8")) if _bridge_schema_path.exists() else None

_rule_schema_path = ROOT / "schema" / "rule.schema.json"
RULE_SCHEMA = json.loads(_rule_schema_path.read_text(encoding="utf-8")) if _rule_schema_path.exists() else None


# ---------------------------------------------------------------------------
# Ontology validation (existing)
# ---------------------------------------------------------------------------

def load_entities():
    """Load all ontology/*.json and merge entity lists; return (entities_list, id_set)."""
    id_set, all_entities = set(), []
    for p in sorted((ROOT / "ontology").glob("*.json")):
        if p.name.startswith("_"):
            continue
        data = json.loads(p.read_text(encoding="utf-8"))
        if "entities" in data:
            for e in data["entities"]:
                all_entities.append(e)
                if "id" in e:
                    id_set.add(e["id"])
    return all_entities, id_set


def validate_ontology():
    """Schema-validate each ontology entity file; then check that all links[*].to exist."""
    errors = []
    for p in sorted((ROOT / "ontology").glob("*.json")):
        if p.name.startswith("_"):
            continue
        data = json.loads(p.read_text(encoding="utf-8"))
        # Only validate files that follow the core entity schema structure
        if "entities" not in data:
            continue
        v = Draft202012Validator(ONTOLOGY_SCHEMA)
        for err in v.iter_errors(data):
            errors.append(f"  {p.name}: {err.message}")

    entities, id_set = load_entities()
    _, shape_ids = load_shapes()
    all_known = id_set | shape_ids
    for e in entities:
        for link in e.get("links", []):
            if link["to"] not in all_known:
                errors.append(f"  dangling ref: {e['id']} -> {link['to']}")

    return errors


# ---------------------------------------------------------------------------
# Shape validation (new)
# ---------------------------------------------------------------------------

def load_shapes():
    """Load all shapes/*.json; return (shapes_list, shape_id_set)."""
    shapes, shape_ids = [], set()
    shapes_dir = ROOT / "shapes"
    if not shapes_dir.exists():
        return shapes, shape_ids
    for p in sorted(shapes_dir.glob("*.json")):
        data = json.loads(p.read_text(encoding="utf-8"))
        shapes.append((p.name, data))
        if "id" in data:
            shape_ids.add(data["id"])
    return shapes, shape_ids


def validate_shapes():
    """Schema-validate each shape file against shape.schema.json."""
    errors = []
    shapes, _ = load_shapes()
    v = Draft202012Validator(SHAPE_SCHEMA)
    for fname, data in shapes:
        for err in v.iter_errors(data):
            errors.append(f"  {fname}: {err.message}")
    return errors


# ---------------------------------------------------------------------------
# Bridge validation (new)
# ---------------------------------------------------------------------------

def validate_bridges():
    """Validate that bridge map shape references resolve to actual shape IDs."""
    errors = []
    _, shape_ids = load_shapes()
    bridge_file = ROOT / "bridges" / "rosetta-bridges.json"
    if not bridge_file.exists():
        return errors

    data = json.loads(bridge_file.read_text(encoding="utf-8"))
    for entry in data.get("map", []):
        shape_ref = entry.get("shape", "")
        if shape_ref and shape_ref not in shape_ids:
            errors.append(f"  bridge ref: {shape_ref} not found in shapes/")
    return errors


# ---------------------------------------------------------------------------
# Seed catalog validation (new)
# ---------------------------------------------------------------------------

def validate_seeds():
    """Validate seed catalog entries against shape.seed.schema and check shape_id refs."""
    errors = []
    catalog_file = ROOT / "data" / "seed-catalog.json"
    if not catalog_file.exists():
        return errors

    data = json.loads(catalog_file.read_text(encoding="utf-8"))
    _, shape_ids = load_shapes()
    v = Draft202012Validator(SEED_SCHEMA)

    for seed in data.get("seeds", []):
        for err in v.iter_errors(seed):
            errors.append(f"  seed {seed.get('id', '?')}: {err.message}")
        # Check that shape_id references a real shape
        shape_ref = seed.get("shape_id", "")
        if shape_ref and shape_ref not in shape_ids:
            errors.append(f"  seed {seed.get('id', '?')}: shape_id {shape_ref} not found in shapes/")

    return errors


# ---------------------------------------------------------------------------
# Bridge schema validation
# ---------------------------------------------------------------------------

def validate_bridge_schemas():
    """Schema-validate each bridge file against bridge.schema.json."""
    errors = []
    if BRIDGE_SCHEMA is None:
        return errors
    bridge_dir = ROOT / "bridges"
    if not bridge_dir.exists():
        return errors
    v = Draft202012Validator(BRIDGE_SCHEMA)
    for p in sorted(bridge_dir.glob("*.json")):
        data = json.loads(p.read_text(encoding="utf-8"))
        for err in v.iter_errors(data):
            errors.append(f"  {p.name}: {err.message}")
    return errors


# ---------------------------------------------------------------------------
# Rule schema validation
# ---------------------------------------------------------------------------

def validate_rules():
    """Schema-validate each rule in expand.jsonl against rule.schema.json."""
    errors = []
    if RULE_SCHEMA is None:
        return errors
    rules_path = ROOT / "rules" / "expand.jsonl"
    if not rules_path.exists():
        return errors
    v = Draft202012Validator(RULE_SCHEMA)
    for i, line in enumerate(rules_path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            rule = json.loads(line)
        except json.JSONDecodeError as exc:
            errors.append(f"  expand.jsonl line {i}: invalid JSON — {exc}")
            continue
        for err in v.iter_errors(rule):
            errors.append(f"  expand.jsonl line {i}: {err.message}")
    return errors


# ---------------------------------------------------------------------------
# Cross-repo reference validation (new)
# ---------------------------------------------------------------------------

def validate_cross_refs(strict=False):
    """Check that cross-repo namespace references can be resolved.

    Uses ontology/_id_registry.json to determine which namespaces
    are external. When strict=False (default), skips namespaces whose
    source data is not locally available.
    """
    errors = []
    registry_file = ROOT / "ontology" / "_id_registry.json"
    if not registry_file.exists():
        return errors

    registry = json.loads(registry_file.read_text(encoding="utf-8"))["registry"]
    external_ns = {
        ns for ns, info in registry.items()
        if info.get("source") != "Rosetta-Shape-Core"
    }

    # Collect all IDs referenced across ontology entities
    entities, id_set = load_entities()
    _, shape_ids = load_shapes()
    all_known = id_set | shape_ids

    # Check links that point to external namespaces
    for e in entities:
        for link in e.get("links", []):
            target = link["to"]
            ns = target.split(".")[0] if "." in target else ""
            if ns in external_ns and target not in all_known:
                # Check atlas/remote for staged data
                source = registry[ns].get("source", "")
                source_key = source.lower().replace("-", "").replace(" ", "")
                staged = _load_staged_ids(source_key)
                if target not in staged:
                    if strict:
                        errors.append(f"  cross-ref: {e['id']} -> {target} (unresolved, source: {source})")
                    # In non-strict mode, silently skip

    return errors


def _load_staged_ids(source_key):
    """Load entity IDs from atlas/remote/<key>/ if available."""
    ids = set()
    remote_dir = ROOT / "atlas" / "remote"
    if not remote_dir.exists():
        return ids
    for d in remote_dir.iterdir():
        if d.is_dir() and d.name.lower().replace("-", "").replace(" ", "") == source_key:
            for p in d.glob("*.json"):
                try:
                    data = json.loads(p.read_text(encoding="utf-8"))
                    if "entities" in data:
                        for e in data["entities"]:
                            if "id" in e:
                                ids.add(e["id"])
                except (json.JSONDecodeError, KeyError):
                    pass
    return ids


# ---------------------------------------------------------------------------
# Fieldlink topology validation
# ---------------------------------------------------------------------------

def validate_fieldlink():
    """Validate .fieldlink.json: structure, mount sync, and source consistency."""
    errors = []
    fl_file = ROOT / ".fieldlink.json"
    if not fl_file.exists():
        return errors  # no fieldlink, nothing to validate

    try:
        data = json.loads(fl_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [f"  .fieldlink.json: invalid JSON — {exc}"]

    fl = data.get("fieldlink", {})
    sources = fl.get("sources", [])
    merge_order = fl.get("merge", {}).get("order", [])

    # Check: every source name appears in merge order
    source_names = [s["name"] for s in sources]
    for name in source_names:
        if name not in merge_order:
            errors.append(f"  fieldlink: source '{name}' not in merge.order")

    # Check: no duplicate source names
    seen = set()
    for name in source_names:
        if name in seen:
            errors.append(f"  fieldlink: duplicate source name '{name}'")
        seen.add(name)

    # Check: mounts point to files that exist in atlas/remote/
    # (only for sources with mounts, not exports which are runtime-generated)
    for source in sources:
        for mount in source.get("mounts", []):
            local_path = ROOT / mount["as"]
            if not local_path.exists():
                errors.append(
                    f"  fieldlink: mount missing — {source['name']}: {mount['as']}"
                )
            elif local_path.suffix == ".json":
                try:
                    json.loads(local_path.read_text(encoding="utf-8"))
                except json.JSONDecodeError as exc:
                    errors.append(
                        f"  fieldlink: invalid JSON in mount — {mount['as']}: {exc}"
                    )

    return errors


# ---------------------------------------------------------------------------
# Cross-repo mesh integrity validation
# ---------------------------------------------------------------------------

def validate_mesh():
    """Validate the full fieldlink mesh: bidirectional consistency, mount
    cross-references, synergy triangle integrity, and entity reachability.

    This is the "nervous system" check — it walks every peer relationship
    and verifies that the staged data is coherent across the ecosystem.
    """
    errors = []
    fl_file = ROOT / ".fieldlink.json"
    if not fl_file.exists():
        return errors

    try:
        data = json.loads(fl_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [f"  mesh: .fieldlink.json invalid JSON — {exc}"]

    fl = data.get("fieldlink", {})
    sources = fl.get("sources", [])

    # --- 1. Direction completeness: flag any source still missing direction ---
    for s in sources:
        if "direction" not in s:
            errors.append(
                f"  mesh: source '{s['name']}' has no direction declared "
                f"(expected 'bidirectional')"
            )

    # --- 2. Mount entity cross-check: IDs in mounted files should not
    #     collide with local IDs (namespace hygiene) ---
    local_entities, local_ids = load_entities()
    _, local_shape_ids = load_shapes()
    all_local = local_ids | local_shape_ids

    remote_ids_by_source = {}
    remote_dir = ROOT / "atlas" / "remote"
    if remote_dir.exists():
        for source_dir in sorted(remote_dir.iterdir()):
            if not source_dir.is_dir():
                continue
            ids = set()
            for p in source_dir.glob("*.json"):
                try:
                    rdata = json.loads(p.read_text(encoding="utf-8"))
                except json.JSONDecodeError:
                    errors.append(f"  mesh: bad JSON in {p.relative_to(ROOT)}")
                    continue
                # Remote files may be dicts or arrays
                if isinstance(rdata, list):
                    for item in rdata:
                        if isinstance(item, dict) and "id" in item:
                            ids.add(item["id"])
                elif isinstance(rdata, dict):
                    for e in rdata.get("entities", []):
                        if isinstance(e, dict) and "id" in e:
                            ids.add(e["id"])
                    if "id" in rdata and isinstance(rdata["id"], str):
                        ids.add(rdata["id"])
                    for entry in rdata.get("map", []):
                        if isinstance(entry, dict) and "id" in entry:
                            ids.add(entry["id"])
            remote_ids_by_source[source_dir.name] = ids

    all_remote = set()
    for ids in remote_ids_by_source.values():
        all_remote |= ids

    # Check for ID collisions between different remote sources
    seen_remote = {}
    for source_name, ids in remote_ids_by_source.items():
        for eid in ids:
            if eid in seen_remote and seen_remote[eid] != source_name:
                errors.append(
                    f"  mesh: ID '{eid}' claimed by both "
                    f"'{seen_remote[eid]}' and '{source_name}'"
                )
            seen_remote[eid] = source_name

    # --- 3. Synergy triangle validation ---
    for s in sources:
        triangle = s.get("synergy_triangle")
        if not triangle:
            continue
        node_ids = {n["id"] for n in triangle.get("nodes", [])}
        edges = triangle.get("edges", [])
        # Every edge endpoint must be a declared node
        for edge in edges:
            for endpoint in ("from", "to"):
                if edge.get(endpoint) not in node_ids:
                    errors.append(
                        f"  mesh: synergy triangle in '{s['name']}' has edge "
                        f"endpoint '{edge.get(endpoint)}' not in nodes {node_ids}"
                    )
        # Triangle must have exactly 3 edges for 3 nodes
        if len(node_ids) == 3 and len(edges) != 3:
            errors.append(
                f"  mesh: synergy triangle in '{s['name']}' has "
                f"{len(edges)} edges, expected 3"
            )

    # --- 4. Mount-to-source alignment: every mount dir should map to a source ---
    source_names = {s["name"] for s in sources}
    source_aliases = {s.get("alias", "").lower() for s in sources if s.get("alias")}
    if remote_dir.exists():
        for source_dir in remote_dir.iterdir():
            if not source_dir.is_dir():
                continue
            # Fuzzy match: dir may be a short alias of the source name
            # e.g. dir "biomachine" matches source "biomachine-ecology"
            matched = False
            dn = source_dir.name.replace("-", "").replace("_", "").lower()
            # Check explicit aliases first (e.g. taf, esp)
            if dn in source_aliases:
                matched = True
            else:
                for sname in source_names:
                    sn = sname.replace("-", "").replace("_", "").lower()
                    if sn == dn or sn.startswith(dn) or dn.startswith(sn):
                        matched = True
                        break
            if not matched:
                errors.append(
                    f"  mesh: atlas/remote/{source_dir.name}/ has no "
                    f"matching source in .fieldlink.json"
                )

    # --- 5. Cross-mesh entity reachability: links targeting remote namespaces
    #     should be resolvable in staged remote data ---
    registry_file = ROOT / "ontology" / "_id_registry.json"
    if registry_file.exists():
        registry = json.loads(registry_file.read_text(encoding="utf-8"))["registry"]
        external_ns = {
            ns for ns, info in registry.items()
            if info.get("source") != "Rosetta-Shape-Core"
        }
        reachable = all_local | all_remote
        unreachable = []
        for e in local_entities:
            for link in e.get("links", []):
                target = link["to"]
                ns = target.split(".")[0] if "." in target else ""
                if ns in external_ns and target not in reachable:
                    unreachable.append((e["id"], target))
        if unreachable:
            for src_id, tgt_id in unreachable:
                errors.append(
                    f"  mesh: {src_id} -> {tgt_id} unreachable in staged data"
                )

    return errors


# ---------------------------------------------------------------------------
# Unified entry point
# ---------------------------------------------------------------------------

def validate_files():
    """Run all validation passes. Raises SystemExit on any failure."""
    all_errors = []

    ontology_errs = validate_ontology()
    if ontology_errs:
        all_errors.append("Ontology errors:")
        all_errors.extend(ontology_errs)

    shape_errs = validate_shapes()
    if shape_errs:
        all_errors.append("Shape errors:")
        all_errors.extend(shape_errs)

    bridge_errs = validate_bridges()
    if bridge_errs:
        all_errors.append("Bridge errors:")
        all_errors.extend(bridge_errs)

    seed_errs = validate_seeds()
    if seed_errs:
        all_errors.append("Seed catalog errors:")
        all_errors.extend(seed_errs)

    bridge_schema_errs = validate_bridge_schemas()
    if bridge_schema_errs:
        all_errors.append("Bridge schema errors:")
        all_errors.extend(bridge_schema_errs)

    rule_errs = validate_rules()
    if rule_errs:
        all_errors.append("Rule schema errors:")
        all_errors.extend(rule_errs)

    cross_errs = validate_cross_refs()
    if cross_errs:
        all_errors.append("Cross-repo reference errors:")
        all_errors.extend(cross_errs)

    fieldlink_errs = validate_fieldlink()
    # Separate mount-missing (warnings) from structural errors (fatal)
    fl_warnings = [e for e in fieldlink_errs if "mount missing" in e]
    fl_errors = [e for e in fieldlink_errs if "mount missing" not in e]
    if fl_errors:
        all_errors.append("Fieldlink topology errors:")
        all_errors.extend(fl_errors)

    mesh_errs = validate_mesh()
    # Direction-missing is a warning (peers may still be setting up)
    mesh_warnings = [e for e in mesh_errs if "no direction" in e]
    mesh_errors = [e for e in mesh_errs if "no direction" not in e]
    if mesh_errors:
        all_errors.append("Mesh integrity errors:")
        all_errors.extend(mesh_errors)

    if all_errors:
        raise SystemExit("Validation failed:\n" + "\n".join(all_errors))

    all_warnings = fl_warnings + mesh_warnings
    if all_warnings:
        import sys
        print("Warnings (non-fatal):", file=sys.stderr)
        for w in all_warnings:
            print(w, file=sys.stderr)


if __name__ == "__main__":
    validate_files()
    print("Ontology OK")
