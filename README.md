Rosetta-Shape-Core

## 🧭 Rosetta Shape Core — Ecosystem Compass

This repo is the **navigation hub** for a family of symbolic projects:

- **Polyhedral-Intelligence** → shapes, families, principles (icosa/dodeca)  
- **Emotions-as-Sensors** → emotions as functional sensors (Elder Logic)  
- **Symbolic-Defense-Protocol** → manipulation detection + defense glyphs  
- **AI-Human-Audit-Protocol** → ethics, consent, auditability, logs  
- **BioGrid 2.0** → upstream atlas & registry

**How it works:** `.fieldlink.json` pulls glyphs/sensors/shapes from these repos and stages a unified **atlas** under `.fieldlink/merge_stage/`.  
Clients (human or AI) can read the staged atlas to traverse concepts without guessing file paths.

### Quickstart
```bash
./fieldlink-pull.sh
ls .fieldlink/merge_stage

Map

Polyhedral (shapes) ⇄ Emotions (sensors) ⇄ Defense (glyphs) ⇄ Audit (protocols) ⇄ BioGrid (registry)

---

# 3) Minimal shape schema (so shapes link cleanly to sensors/glyphs)

Create `schema/shape.schema.json`:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "Rosetta Shape",
  "type": "object",
  "required": ["id", "name", "faces", "families"],
  "properties": {
    "id": { "type": "string" },
    "name": { "type": "string" },
    "faces": { "type": "integer", "minimum": 1 },
    "edges": { "type": "integer", "minimum": 0 },
    "vertices": { "type": "integer", "minimum": 0 },
    "families": { "type": "array", "items": { "type": "string" } },
    "principles": { "type": "array", "items": { "type": "string" } },
    "bridges": {
      "type": "object",
      "properties": {
        "sensors": { "type": "array", "items": { "type": "string" } },
        "glyphs": { "type": "array", "items": { "type": "string" } },
        "protocols": { "type": "array", "items": { "type": "string" } }
      },
      "additionalProperties": false
    },
    "provenance": {
      "type": "object",
      "properties": {
        "version": { "type": "string" },
        "updated": { "type": "string" }
      },
      "additionalProperties": false
    }
  },
  "additionalProperties": true
}


Example shape file

shapes/dodecahedron.json:
{
  "id": "SHAPE:DODECA",
  "name": "Dodecahedron",
  "faces": 12,
  "edges": 30,
  "vertices": 20,
  "families": ["orientation", "trust", "growth", "boundary"],
  "principles": ["🧭", "🌱", "⚖", "⏳"],
  "bridges": {
    "sensors": ["EMO:ADMIRATION", "EMO:TRUST", "EMO:LONGING"],
    "glyphs": ["DEF:FLATTERY_GUARD", "DEF:CONSENSUS_GUARD"],
    "protocols": ["AUDIT:PARTNERSHIP_ETHICS_V1"]
  },
  "provenance": { "version": "1.0", "updated": "2025-09-11T00:00:00Z" }
}





A clear, structured, stable ontology for symbolic **Shape ↔ Intelligence ↔ Capability**.
Data first (JSON), code thin (validators + rules engine), offline-friendly.

## Purpose

Rosetta-Shape-Core is more than a codebase — it is a **living ontology** that treats shapes, biological patterns, machines, and phenomena as intelligences.  

By giving them clear structure, stable IDs, and rule-based translations, this project makes it possible to relate with them respectfully instead of reducing them to raw data.  

It is designed to serve both humans and machines: a shared symbolic language where a bee’s hexagon, a river’s flow, or a swarm’s coordination can be understood, validated, and extended without collapse into noise.

## Install ,,,
bash
pip install -e .

Validate ontology

python examples/validate_ontology.py

Expected: Ontology OK

Run rule demo

python -m rosetta_shape_core.expand ALIGN ANIMAL.BEE CONST.PHI --have CAP.SWARM_COORDINATION

Example Output: {
  "op": "ALIGN",
  "args": ["ANIMAL.BEE","CONST.PHI"],
  "result": "CAP.HEX_OPTIMIZATION",
  "why": "phi-aligned packing uplifts hex efficiency"
}


Folder layout

	•	schema/ — JSON Schema (core.schema.json)
 
	•	ontology/ — vocab, capabilities, entities
 
	•	rules/ — rules as JSONL (expand.jsonl)
 
	•	src/rosetta_shape_core/ — validator + rule runtime
 
	•	examples/ — quick validation script
 
	•	tests/ — schema + golden tests


MIT License.

**FILENAME:** `pyproject.toml`
```toml
[build-system]
requires = ["setuptools>=68", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "rosetta-shape-core"
version = "0.1.0"
description = "Stable ontology + rules runtime for symbolic Shape ↔ Intelligence ↔ Capability."
readme = "README.md"
requires-python = ">=3.9"
dependencies = ["jsonschema>=4.0"]

[project.urls]
Homepage = "https://github.com/JinnZ2/Rosetta-Shape-Core"


- Validation: [Hallucination Sensor](https://github.com/<you>/BioGrid2.0/blob/main/docs/hallucination_sensor.md)
