Rosetta-Shape-Core

A clear, structured, stable ontology for symbolic **Shape ↔ Intelligence ↔ Capability**.
Data first (JSON), code thin (validators + rules engine), offline-friendly.

## Install ,,,
bash
pip install -e .

Validate ontology

python examples/validate_ontology.py

Run rule demo

python -m rosetta_shape_core.expand ALIGN ANIMAL.BEE CONST.PHI --have CAP.SWARM_COORDINATION

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



