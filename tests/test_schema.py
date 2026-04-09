import json
import pathlib
import re

from rosetta_shape_core.seeds import (
    all_essences,
    all_seeds,
    all_shape_ids,
    get_seed,
    get_seed_by_name,
    resonance,
    seed_traits_vector,
    select_by_element,
    select_by_essence,
    select_by_sensor,
    select_by_traits,
    traits_for_essence,
)
from rosetta_shape_core.validator import (
    load_shapes,
    validate_bridges,
    validate_fieldlink,
    validate_files,
    validate_mesh,
    validate_ontology,
    validate_seeds,
    validate_shapes,
)

ROOT = pathlib.Path(__file__).resolve().parents[1]


# ---------------------------------------------------------------------------
# Validation tests
# ---------------------------------------------------------------------------

def test_ontology_schema_and_links():
    """Ontology files pass schema validation and referential integrity."""
    assert validate_ontology() == []


def test_shape_schema_validation():
    """All shape files pass the tightened shape schema."""
    assert validate_shapes() == []


def test_bridge_references_resolve():
    """Bridge map shape references all resolve to actual shape IDs."""
    assert validate_bridges() == []


def test_seed_catalog_validation():
    """Seed catalog entries pass schema validation and shape_id refs resolve."""
    assert validate_seeds() == []


def test_id_format_unified():
    """No colon-delimited SHAPE IDs remain in shapes/ or bridges/."""
    colon_pattern = re.compile(r"SHAPE:[A-Z]")
    offenders = []
    for d in ["shapes", "bridges"]:
        for p in (ROOT / d).glob("*.json"):
            text = p.read_text(encoding="utf-8")
            if colon_pattern.search(text):
                offenders.append(p.name)
    assert offenders == [], f"Colon IDs found in: {offenders}"


def test_all_shapes_have_required_bridge_fields():
    """Each shape has sensors and defenses in bridges."""
    shapes, _ = load_shapes()
    for fname, data in shapes:
        bridges = data.get("bridges", {})
        assert "sensors" in bridges, f"{fname} missing bridges.sensors"
        assert "defenses" in bridges, f"{fname} missing bridges.defenses"


def test_fieldlink_topology():
    """Fieldlink JSON is valid, sources are in merge order, no duplicates."""
    import json
    fl = json.loads((ROOT / ".fieldlink.json").read_text(encoding="utf-8"))
    sources = fl["fieldlink"]["sources"]
    merge_order = fl["fieldlink"]["merge"]["order"]
    # Every source in merge order
    for s in sources:
        assert s["name"] in merge_order, f"{s['name']} not in merge.order"
    # No duplicate names
    names = [s["name"] for s in sources]
    assert len(names) == len(set(names)), f"Duplicate source names: {names}"
    # All staged mount files are valid JSON
    errs = validate_fieldlink()
    mount_errs = [e for e in errs if "mount missing" not in e]
    assert mount_errs == [], f"Fieldlink errors: {mount_errs}"


def test_mesh_integrity():
    """Cross-repo mesh: no ID collisions, synergy triangles valid, mounts aligned."""
    errs = validate_mesh()
    # Filter out direction warnings (peers may still be setting up)
    hard_errs = [e for e in errs if "no direction" not in e]
    assert hard_errs == [], f"Mesh errors: {hard_errs}"


def test_mesh_all_sources_bidirectional():
    """Every fieldlink source declares a direction."""
    fl = json.loads((ROOT / ".fieldlink.json").read_text(encoding="utf-8"))
    sources = fl["fieldlink"]["sources"]
    missing = [s["name"] for s in sources if "direction" not in s]
    assert missing == [], f"Sources without direction: {missing}"


def test_mesh_synergy_triangle_well_formed():
    """Synergy triangles have 3 nodes and 3 edges with valid endpoints."""
    fl = json.loads((ROOT / ".fieldlink.json").read_text(encoding="utf-8"))
    for s in fl["fieldlink"]["sources"]:
        tri = s.get("synergy_triangle")
        if not tri:
            continue
        nodes = tri.get("nodes", [])
        edges = tri.get("edges", [])
        node_ids = {n["id"] for n in nodes}
        assert len(nodes) == 3, f"{s['name']}: expected 3 nodes, got {len(nodes)}"
        assert len(edges) == 3, f"{s['name']}: expected 3 edges, got {len(edges)}"
        for edge in edges:
            assert edge["from"] in node_ids, f"bad from: {edge['from']}"
            assert edge["to"] in node_ids, f"bad to: {edge['to']}"


def test_full_validation():
    """Full validation pipeline passes."""
    validate_files()


# ---------------------------------------------------------------------------
# Seed query interface tests
# ---------------------------------------------------------------------------

def test_all_seeds_returns_five():
    """Catalog has one seed per Platonic solid."""
    seeds = all_seeds()
    assert len(seeds) == 5
    shape_ids = {s["shape_id"] for s in seeds}
    assert shape_ids == {"SHAPE.TETRA", "SHAPE.CUBE", "SHAPE.OCTA", "SHAPE.DODECA", "SHAPE.ICOSA"}


def test_all_shape_ids():
    """all_shape_ids() returns sorted list of all shape IDs."""
    ids = all_shape_ids()
    assert len(ids) == 5
    assert ids == sorted(ids)  # sorted
    for expected in ["SHAPE.TETRA", "SHAPE.CUBE", "SHAPE.OCTA", "SHAPE.ICOSA", "SHAPE.DODECA"]:
        assert expected in ids


def test_get_seed_by_shape_id():
    """Can look up each seed by its SHAPE.X ID."""
    seed = get_seed("SHAPE.TETRA")
    assert seed is not None
    assert seed["id"] == "seed-tetrahedron"
    assert seed["traits"]["element"] == "fire"


def test_get_seed_by_name():
    """Can look up seed by human-readable name."""
    seed = get_seed_by_name("seed-cube")
    assert seed is not None
    assert seed["shape_id"] == "SHAPE.CUBE"


def test_get_seed_not_found():
    """Returns None for unknown shape ID."""
    assert get_seed("SHAPE.NONEXISTENT") is None


def test_select_by_traits():
    """Trait-based selection returns best matches first."""
    matches = select_by_traits(["stability", "foundation"])
    assert len(matches) >= 1
    # Tetrahedron has both stability and foundation — should be first
    assert matches[0]["shape_id"] == "SHAPE.TETRA"


def test_select_by_traits_returns_partial_matches():
    """Shapes with partial trait overlap are included."""
    matches = select_by_traits(["stability"])
    shape_ids = [m["shape_id"] for m in matches]
    assert "SHAPE.TETRA" in shape_ids
    assert "SHAPE.CUBE" in shape_ids


def test_select_by_element():
    """Element-based selection works."""
    fire_seeds = select_by_element("fire")
    assert len(fire_seeds) == 1
    assert fire_seeds[0]["shape_id"] == "SHAPE.TETRA"


def test_select_by_sensor():
    """Sensor-based selection returns seeds that perceive through that emotion."""
    compassion_seeds = select_by_sensor("compassion")
    assert len(compassion_seeds) == 1
    assert compassion_seeds[0]["shape_id"] == "SHAPE.OCTA"


# ---------------------------------------------------------------------------
# Resonance tests (Jaccard + polyhedral topology bonuses)
# ---------------------------------------------------------------------------

def test_resonance_same_seed():
    """A seed has maximum resonance with itself."""
    score = resonance("SHAPE.TETRA", "SHAPE.TETRA")
    assert score == 1.0


def test_resonance_tetra_cube_bridge():
    """Tetra and Cube: Jaccard overlap (stability) + bridge bonus."""
    score = resonance("SHAPE.TETRA", "SHAPE.CUBE")
    # tetra: fire, stability, foundation, boundary (4)
    # cube: earth, stability, structure, containment (4)
    # Jaccard: 1/7 ≈ 0.143 + bridge bonus 0.08 ≈ 0.223
    assert 0.2 < score < 0.3


def test_resonance_cube_octa_duality():
    """Cube and Octa (duals): Jaccard overlap (structure) + duality bonus."""
    score = resonance("SHAPE.CUBE", "SHAPE.OCTA")
    # cube: earth, stability, structure, containment (4)
    # octa: air, structure, balance, integration (4)
    # Jaccard: 1/7 ≈ 0.143 + duality bonus 0.15 ≈ 0.293
    assert 0.25 < score < 0.35


def test_resonance_dodeca_icosa_duality():
    """Dodeca and Icosa (duals): Jaccard overlap (growth) + duality bonus."""
    score = resonance("SHAPE.DODECA", "SHAPE.ICOSA")
    # Jaccard + 0.15 duality
    assert 0.2 < score < 0.4


def test_resonance_tetra_dodeca_bridge():
    """Tetra and Dodeca: Jaccard overlap (boundary) + bridge bonus."""
    score = resonance("SHAPE.TETRA", "SHAPE.DODECA")
    # Jaccard + 0.08 bridge
    assert 0.1 < score < 0.3


def test_resonance_duality_stronger_than_bridge():
    """Duality bonus (0.15) is stronger than bridge bonus (0.08)."""
    dual = resonance("SHAPE.CUBE", "SHAPE.OCTA")
    bridge = resonance("SHAPE.TETRA", "SHAPE.CUBE")
    assert dual > bridge


def test_resonance_no_topology_no_bonus():
    """Tetra and Icosa have no topology connection — Jaccard only."""
    score = resonance("SHAPE.TETRA", "SHAPE.ICOSA")
    # No trait overlap, no topology → 0.0
    assert score == 0.0


def test_resonance_symmetry():
    """resonance(A, B) == resonance(B, A)."""
    assert resonance("SHAPE.TETRA", "SHAPE.CUBE") == resonance("SHAPE.CUBE", "SHAPE.TETRA")


def test_resonance_capped_at_one():
    """Resonance never exceeds 1.0."""
    assert resonance("SHAPE.TETRA", "SHAPE.TETRA") <= 1.0


def test_resonance_not_found():
    """Resonance returns 0.0 for unknown seeds."""
    assert resonance("SHAPE.TETRA", "SHAPE.NONEXISTENT") == 0.0


# ---------------------------------------------------------------------------
# Trait vector tests (tuple format for kernel compatibility)
# ---------------------------------------------------------------------------

def test_seed_traits_vector_returns_tuple():
    """Traits vector returns (list[int], list[str]) tuple."""
    result = seed_traits_vector("SHAPE.TETRA")
    assert isinstance(result, tuple)
    assert len(result) == 2
    vector, labels = result
    assert isinstance(vector, list)
    assert isinstance(labels, list)
    assert len(vector) == len(labels)


def test_seed_traits_vector_values():
    """Traits vector has 1 for shape's families, 0 for others."""
    vector, labels = seed_traits_vector("SHAPE.TETRA")
    assert labels == sorted(labels)  # sorted
    # Tetra has: fire, stability, foundation, boundary
    for fam in ["fire", "stability", "foundation", "boundary"]:
        idx = labels.index(fam)
        assert vector[idx] == 1, f"Expected 1 for {fam}"
    for fam in ["earth", "balance", "flow"]:
        idx = labels.index(fam)
        assert vector[idx] == 0, f"Expected 0 for {fam}"


def test_seed_traits_vector_unknown():
    """Unknown shape returns empty tuple."""
    vector, labels = seed_traits_vector("SHAPE.FAKE")
    assert vector == []
    assert labels == []


# ---------------------------------------------------------------------------
# Essence mapping tests
# ---------------------------------------------------------------------------

def test_traits_for_essence_guardian():
    """Guardian essence maps to stability/protection traits."""
    traits = traits_for_essence("guardian")
    assert "stability" in traits
    assert "foundation" in traits
    assert "boundary" in traits
    assert "containment" in traits


def test_traits_for_essence_explorer():
    """Explorer essence maps to flow/adaptability traits."""
    traits = traits_for_essence("explorer")
    assert "flow" in traits
    assert "adaptability" in traits


def test_traits_for_essence_observer():
    """Observer essence (kernel vocabulary) maps to balance/structure traits."""
    traits = traits_for_essence("observer")
    assert "balance" in traits
    assert "structure" in traits


def test_traits_for_essence_weaver():
    """Weaver essence (kernel vocabulary) maps to orientation/trust traits."""
    traits = traits_for_essence("weaver")
    assert "orientation" in traits
    assert "trust" in traits


def test_traits_for_essence_unknown():
    """Unknown essence returns empty list."""
    assert traits_for_essence("nonexistent") == []


def test_select_by_essence_guardian():
    """Guardian essence selects tetra first (most trait overlap)."""
    matches = select_by_essence("guardian")
    assert len(matches) >= 1
    assert matches[0]["shape_id"] == "SHAPE.TETRA"


def test_select_by_essence_explorer():
    """Explorer essence selects icosahedron first."""
    matches = select_by_essence("explorer")
    assert len(matches) >= 1
    assert matches[0]["shape_id"] == "SHAPE.ICOSA"


def test_select_by_essence_healer():
    """Healer essence selects octahedron first."""
    matches = select_by_essence("healer")
    assert len(matches) >= 1
    assert matches[0]["shape_id"] == "SHAPE.OCTA"


def test_select_by_essence_teacher():
    """Teacher essence selects dodecahedron first."""
    matches = select_by_essence("teacher")
    assert len(matches) >= 1
    assert matches[0]["shape_id"] == "SHAPE.DODECA"


def test_select_by_essence_observer():
    """Observer essence (kernel) selects octahedron first."""
    matches = select_by_essence("observer")
    assert len(matches) >= 1
    assert matches[0]["shape_id"] == "SHAPE.OCTA"


def test_select_by_essence_weaver():
    """Weaver essence (kernel) selects dodecahedron first."""
    matches = select_by_essence("weaver")
    assert len(matches) >= 1
    assert matches[0]["shape_id"] == "SHAPE.DODECA"


def test_all_essences_returns_archetypes():
    """All defined essences are accessible — both Rosetta and kernel vocabularies."""
    essences = all_essences()
    # Rosetta vocabulary
    for name in ["guardian", "explorer", "healer", "teacher", "builder", "mediator", "sentinel", "nurturer"]:
        assert name in essences
    # Kernel vocabulary
    for name in ["observer", "weaver"]:
        assert name in essences


def test_every_seed_has_matching_shape():
    """Every seed in the catalog references a shape that exists in shapes/."""
    _, shape_ids = load_shapes()
    for seed in all_seeds():
        assert seed["shape_id"] in shape_ids, \
            f"Seed {seed['id']} references {seed['shape_id']} which doesn't exist"
