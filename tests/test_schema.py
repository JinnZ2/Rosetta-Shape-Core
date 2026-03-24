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
    select_by_essence,
    traits_for_essence,
    all_essences,
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


def test_select_by_traits_returns_partial_matches():
    """Shapes with partial trait overlap are included."""
    # "stability" is shared by tetra and cube
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
# Resonance tests (polyhedral duality creates real overlap)
# ---------------------------------------------------------------------------

def test_resonance_same_seed():
    """A seed has maximum resonance with itself."""
    score = resonance("SHAPE.TETRA", "SHAPE.TETRA")
    assert score == 1.0


def test_resonance_tetra_cube_partial():
    """Tetra and Cube share 'stability' — partial resonance."""
    score = resonance("SHAPE.TETRA", "SHAPE.CUBE")
    assert 0.0 < score < 1.0
    # tetra: fire, stability, foundation, boundary (4)
    # cube: earth, stability, structure, containment (4)
    # intersection: {stability} = 1, union = 7
    assert abs(score - 1 / 7) < 0.01


def test_resonance_cube_octa_partial():
    """Cube and Octa (duals) share 'structure' — partial resonance."""
    score = resonance("SHAPE.CUBE", "SHAPE.OCTA")
    assert 0.0 < score < 1.0


def test_resonance_dodeca_icosa_partial():
    """Dodeca and Icosa (duals) share 'growth' — partial resonance."""
    score = resonance("SHAPE.DODECA", "SHAPE.ICOSA")
    assert 0.0 < score < 1.0


def test_resonance_tetra_dodeca_partial():
    """Tetra and Dodeca share 'boundary' — partial resonance."""
    score = resonance("SHAPE.TETRA", "SHAPE.DODECA")
    assert 0.0 < score < 1.0


def test_resonance_not_found():
    """Resonance returns 0.0 for unknown seeds."""
    assert resonance("SHAPE.TETRA", "SHAPE.NONEXISTENT") == 0.0


def test_seed_traits_vector():
    """Traits vector has correct shape and values."""
    vec = seed_traits_vector("SHAPE.TETRA")
    assert isinstance(vec, dict)
    assert vec["fire"] == 1.0
    assert vec["stability"] == 1.0
    assert vec["foundation"] == 1.0
    assert vec["boundary"] == 1.0
    # Families from other seeds should be 0.0
    assert vec["earth"] == 0.0
    assert vec["balance"] == 0.0


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


def test_traits_for_essence_unknown():
    """Unknown essence returns empty list."""
    assert traits_for_essence("nonexistent") == []


def test_select_by_essence_guardian():
    """Guardian essence selects tetra first (most trait overlap)."""
    matches = select_by_essence("guardian")
    assert len(matches) >= 1
    # Tetra has stability+foundation+boundary (3 of 4 guardian traits)
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


def test_all_essences_returns_archetypes():
    """All defined essences are accessible."""
    essences = all_essences()
    assert "guardian" in essences
    assert "explorer" in essences
    assert "healer" in essences
    assert "teacher" in essences
    assert "builder" in essences
    assert "mediator" in essences
    assert "sentinel" in essences
    assert "nurturer" in essences


def test_every_seed_has_matching_shape():
    """Every seed in the catalog references a shape that exists in shapes/."""
    _, shape_ids = load_shapes()
    for seed in all_seeds():
        assert seed["shape_id"] in shape_ids, \
            f"Seed {seed['id']} references {seed['shape_id']} which doesn't exist"
