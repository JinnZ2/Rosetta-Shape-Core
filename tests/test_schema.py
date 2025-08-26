from rosetta_shape_core.validator import validate_files

def test_ontology_schema_and_links():
    # Will raise SystemExit with details if broken
    validate_files()
