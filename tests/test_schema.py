import json, pathlib, re
from rosetta_shape_core.validator import (
    validate_files,
    validate_ontology,
    validate_shapes,
    validate_bridges,
    validate_seeds,
    load_shapes,
)
from rosetta_shape_core.seeds import (
    all_seeds,
    get_seed,
    get_seed_by_name,
    select_by_traits,
    select_by_element,
    select_by_sensor,
    resonance,
    seed_traits_vector,
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


def test_resonance_same_seed():
    """A seed has maximum resonance with itself."""
    score = resonance("SHAPE.TETRA", "SHAPE.TETRA")
    assert score == 1.0


def test_resonance_different_seeds():
    """Resonance between different seeds is based on trait overlap."""
    # Tetra (fire, stability, foundation) vs Cube (earth, structure, containment)
    # No overlap — should be 0.0
    score = resonance("SHAPE.TETRA", "SHAPE.CUBE")
    assert score == 0.0

    # Cube (earth, structure, containment) vs Octa (air, balance, integration)
    # No overlap — should be 0.0
    score = resonance("SHAPE.CUBE", "SHAPE.OCTA")
    assert score == 0.0


def test_resonance_not_found():
    """Resonance returns 0.0 for unknown seeds."""
    assert resonance("SHAPE.TETRA", "SHAPE.NONEXISTENT") == 0.0


def test_seed_traits_vector():
    """Traits vector has correct shape and values."""
    vec = seed_traits_vector("SHAPE.TETRA")
    assert isinstance(vec, dict)
    # Should have entries for all families across catalog
    assert vec["fire"] == 1.0
    assert vec["stability"] == 1.0
    assert vec["foundation"] == 1.0
    # Families from other seeds should be 0.0
    assert vec["earth"] == 0.0
    assert vec["balance"] == 0.0


def test_every_seed_has_matching_shape():
    """Every seed in the catalog references a shape that exists in shapes/."""
    _, shape_ids = load_shapes()
    for seed in all_seeds():
        assert seed["shape_id"] in shape_ids, \
            f"Seed {seed['id']} references {seed['shape_id']} which doesn't exist"
