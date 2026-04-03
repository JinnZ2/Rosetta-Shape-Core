"""Tests for the validator module — schema validation, referential integrity,
bridge references, fieldlink mounts, and the unified validate_all pipeline."""
import json
import pathlib
import tempfile

from rosetta_shape_core.validator import (
    ROOT,
    ONTOLOGY_SCHEMA,
    SHAPE_SCHEMA,
    SEED_SCHEMA,
    load_entities,
    load_shapes,
    validate_ontology,
    validate_shapes,
    validate_bridges,
    validate_seeds,
    validate_cross_refs,
    validate_fieldlink,
    validate_mesh,
    validate_files,
)
from jsonschema import Draft202012Validator


# ── Schema loading ────────────────────────────────────────────────

def test_ontology_schema_is_valid_json_schema():
    """The core ontology schema itself is a valid JSON Schema 2020-12."""
    Draft202012Validator.check_schema(ONTOLOGY_SCHEMA)


def test_shape_schema_is_valid_json_schema():
    """The shape schema itself is a valid JSON Schema 2020-12."""
    Draft202012Validator.check_schema(SHAPE_SCHEMA)


def test_seed_schema_is_valid_json_schema():
    """The seed schema itself is a valid JSON Schema 2020-12."""
    Draft202012Validator.check_schema(SEED_SCHEMA)


# ── Entity loading ────────────────────────────────────────────────

def test_load_entities_returns_nonempty():
    """load_entities finds entities from ontology/ files."""
    entities, id_set = load_entities()
    assert len(entities) > 0
    assert len(id_set) > 0


def test_load_entities_ids_are_dot_namespaced():
    """All entity IDs follow the DOT.NAMESPACE format."""
    _, id_set = load_entities()
    for eid in id_set:
        assert "." in eid, f"Entity ID missing dot namespace: {eid}"


def test_load_entities_skips_underscore_files():
    """Files starting with _ (like _vocab.json) are skipped."""
    entities, id_set = load_entities()
    # _vocab.json defines namespaces, not entities — its keys should not appear as IDs
    assert "ANIMAL" not in id_set  # namespace, not entity ID


# ── Schema validation (valid data) ───────────────────────────────

def test_validate_ontology_passes_on_repo():
    """All ontology files in the repo pass schema + referential integrity."""
    errors = validate_ontology()
    assert errors == [], f"Ontology validation errors: {errors}"


def test_validate_shapes_passes_on_repo():
    """All shape files in the repo pass the shape schema."""
    errors = validate_shapes()
    assert errors == [], f"Shape validation errors: {errors}"


# ── Schema validation (invalid data) ─────────────────────────────

def test_invalid_entity_detected_by_schema():
    """An entity missing required fields fails schema validation."""
    v = Draft202012Validator(ONTOLOGY_SCHEMA)
    invalid_doc = {"entities": [{"name": "Missing ID"}]}
    schema_errors = list(v.iter_errors(invalid_doc))
    assert len(schema_errors) > 0, "Expected schema errors for entity without 'id'"


def test_invalid_shape_detected_by_schema():
    """A shape missing required fields fails shape schema validation."""
    v = Draft202012Validator(SHAPE_SCHEMA)
    invalid_shape = {"name": "Bad Shape"}  # missing id, faces, edges, vertices, etc.
    schema_errors = list(v.iter_errors(invalid_shape))
    assert len(schema_errors) > 0, "Expected schema errors for shape without 'id'"


def test_valid_entity_passes_schema():
    """A well-formed entity doc passes the ontology schema."""
    v = Draft202012Validator(ONTOLOGY_SCHEMA)
    _, id_set = load_entities()
    # Pick a real entity file to confirm it validates
    for p in sorted((ROOT / "ontology").glob("*.json")):
        if p.name.startswith("_"):
            continue
        data = json.loads(p.read_text(encoding="utf-8"))
        if "entities" in data:
            errors = list(v.iter_errors(data))
            assert errors == [], f"{p.name} failed: {[e.message for e in errors]}"
            break  # one is enough for this test


# ── Referential integrity ─────────────────────────────────────────

def test_no_dangling_links_in_ontology():
    """Every links[*].to in the ontology resolves to an existing entity ID."""
    errors = validate_ontology()
    dangling = [e for e in errors if "dangling ref" in e]
    assert dangling == [], f"Dangling references found: {dangling}"


def test_all_entity_link_targets_are_known():
    """Cross-check: every link target is in the global ID set (entities + shapes)."""
    entities, id_set = load_entities()
    _, shape_ids = load_shapes()
    all_known = id_set | shape_ids
    for e in entities:
        for link in e.get("links", []):
            assert link["to"] in all_known, (
                f"Entity {e['id']} links to unknown {link['to']}"
            )


# ── Shape loading and validation ──────────────────────────────────

def test_load_shapes_returns_five_platonic():
    """At least 5 shape files exist (the Platonic solids)."""
    shapes, shape_ids = load_shapes()
    assert len(shapes) >= 5
    expected = {"SHAPE.TETRA", "SHAPE.CUBE", "SHAPE.OCTA", "SHAPE.DODECA", "SHAPE.ICOSA"}
    assert expected.issubset(shape_ids)


def test_shapes_have_bridges_with_sensors():
    """Every shape file has bridges.sensors defined."""
    shapes, _ = load_shapes()
    for fname, data in shapes:
        bridges = data.get("bridges", {})
        assert "sensors" in bridges, f"{fname} missing bridges.sensors"
        assert len(bridges["sensors"]) > 0, f"{fname} has empty sensors list"


# ── Bridge validation ─────────────────────────────────────────────

def test_validate_bridges_passes_on_repo():
    """All bridge map shape references resolve to real shape IDs."""
    errors = validate_bridges()
    assert errors == [], f"Bridge validation errors: {errors}"


def test_rosetta_bridges_file_exists():
    """The main rosetta-bridges.json exists."""
    assert (ROOT / "bridges" / "rosetta-bridges.json").exists()


def test_bridge_map_entries_have_shape_field():
    """Every entry in the bridge map has a 'shape' field."""
    data = json.loads(
        (ROOT / "bridges" / "rosetta-bridges.json").read_text(encoding="utf-8")
    )
    for entry in data.get("map", []):
        assert "shape" in entry, f"Bridge map entry missing 'shape': {entry}"


# ── Seed catalog validation ───────────────────────────────────────

def test_validate_seeds_passes_on_repo():
    """Seed catalog entries pass schema and shape_id refs resolve."""
    errors = validate_seeds()
    assert errors == [], f"Seed validation errors: {errors}"


# ── Cross-repo references ────────────────────────────────────────

def test_validate_cross_refs_non_strict():
    """Non-strict cross-ref check passes (skips missing remote data)."""
    errors = validate_cross_refs(strict=False)
    assert errors == [], f"Cross-ref errors (non-strict): {errors}"


# ── Fieldlink validation ─────────────────────────────────────────

def test_fieldlink_file_exists():
    """.fieldlink.json exists at the repo root."""
    assert (ROOT / ".fieldlink.json").exists()


def test_validate_fieldlink_no_structural_errors():
    """Fieldlink validation has no structural errors (mount-missing is a warning)."""
    errors = validate_fieldlink()
    structural = [e for e in errors if "mount missing" not in e]
    assert structural == [], f"Fieldlink structural errors: {structural}"


def test_fieldlink_no_duplicate_source_names():
    """No duplicate source names in .fieldlink.json."""
    data = json.loads((ROOT / ".fieldlink.json").read_text(encoding="utf-8"))
    names = [s["name"] for s in data["fieldlink"]["sources"]]
    assert len(names) == len(set(names)), f"Duplicate sources: {names}"


def test_fieldlink_sources_in_merge_order():
    """Every source name appears in the merge.order list."""
    data = json.loads((ROOT / ".fieldlink.json").read_text(encoding="utf-8"))
    fl = data["fieldlink"]
    merge_order = fl["merge"]["order"]
    for s in fl["sources"]:
        assert s["name"] in merge_order, f"{s['name']} not in merge.order"


# ── Mesh validation ──────────────────────────────────────────────

def test_validate_mesh_no_hard_errors():
    """Mesh validation has no hard errors (direction warnings are acceptable)."""
    errors = validate_mesh()
    hard = [e for e in errors if "no direction" not in e]
    assert hard == [], f"Mesh hard errors: {hard}"


def test_mesh_no_id_collisions_across_sources():
    """No entity ID is claimed by multiple remote sources."""
    errors = validate_mesh()
    collisions = [e for e in errors if "claimed by both" in e]
    assert collisions == [], f"ID collisions: {collisions}"


# ── Unified validate_files ────────────────────────────────────────

def test_validate_files_passes():
    """The full validate_files() pipeline completes without raising SystemExit."""
    # validate_files raises SystemExit on failure
    validate_files()
