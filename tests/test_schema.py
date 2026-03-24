import json, pathlib, re
from rosetta_shape_core.validator import (
    validate_files,
    validate_ontology,
    validate_shapes,
    validate_bridges,
    load_shapes,
)

ROOT = pathlib.Path(__file__).resolve().parents[1]


def test_ontology_schema_and_links():
    """Ontology files pass schema validation and referential integrity."""
    assert validate_ontology() == []


def test_shape_schema_validation():
    """All shape files pass the tightened shape schema."""
    assert validate_shapes() == []


def test_bridge_references_resolve():
    """Bridge map shape references all resolve to actual shape IDs."""
    assert validate_bridges() == []


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
