from __future__ import annotations
import json, pathlib
from jsonschema import Draft202012Validator

ROOT = pathlib.Path(__file__).resolve().parents[2]
SCHEMA = json.loads((ROOT / "schema" / "core.schema.json").read_text(encoding="utf-8"))

def load_entities():
    """Load all ontology/*.json and merge entity lists; return (entities_list, id_set)."""
    id_set, all_entities = set(), []
    for p in (ROOT / "ontology").glob("*.json"):
        data = json.loads(p.read_text(encoding="utf-8"))
        if "entities" in data:
            for e in data["entities"]:
                all_entities.append(e)
                if "id" in e:
                    id_set.add(e["id"])
    return all_entities, id_set

def validate_files():
    """Schema-validate each ontology file; then check that all links[*].to exist."""
    for p in (ROOT / "ontology").glob("*.json"):
        data = json.loads(p.read_text(encoding="utf-8"))
        Draft202012Validator(SCHEMA).validate(data)

    entities, id_set = load_entities()
    missing = []
    for e in entities:
        for link in e.get("links", []):
            if link["to"] not in id_set:
                missing.append((e["id"], link["to"]))
    if missing:
        lines = "\n".join(f"- {eid} → {toid}" for eid, toid in missing)
        raise SystemExit(f"Referential integrity failed:\n{lines}")

if __name__ == "__main__":
    validate_files()
    print("Ontology OK")
