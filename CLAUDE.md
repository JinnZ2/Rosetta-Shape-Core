# CLAUDE.md — Rosetta Shape Core

## Project Overview

Rosetta-Shape-Core is a **symbolic ontology and rules engine** that treats shapes, biological patterns, machines, and phenomena as intelligences. It provides stable JSON-based schemas, vocabularies, and a thin Python runtime for validating and expanding symbolic relationships.

This repo also acts as a **navigation hub** for a family of related projects, orchestrated via `.fieldlink.json`:
- **Polyhedral-Intelligence** — shapes, families, principles
- **Emotions-as-Sensors** — emotions as functional sensors (Elder Logic)
- **Symbolic-Defense-Protocol** — manipulation detection + defense glyphs
- **AI-Human-Audit-Protocol** — ethics, consent, auditability
- **BioGrid 2.0** — upstream atlas & registry
- **Regenerative-Intelligence-Core** — regenerative patterns, cycles, ontology

## Tech Stack

- **Language:** Python 3.9+
- **Validation:** `jsonschema` 4.0+ (JSON Schema 2020-12)
- **Data format:** JSON (ontology, schemas, rules as JSONL)
- **Config:** YAML (`ai_integrator.config.yaml`)
- **CI/CD:** GitHub Actions (`.github/workflows/`)
- **License:** MIT

## Directory Structure

```
schema/          — JSON Schema definitions (core, shape, ai_index, seed)
ontology/        — Vocabulary, capabilities, sample entities
rules/           — Rules as JSONL (expand.jsonl)
src/rosetta_shape_core/
  validator.py   — Schema validation + referential integrity checks
  expand.py      — Rule engine + CLI
shapes/          — Machine-readable shape JSON files
bridges/         — Bridge definitions linking across domains
protocols/       — Protocol documents
data/            — Domain data (sacred geometry, animal intelligence, etc.)
docs/            — Design documents, guides, and pattern mappings
examples/        — Quick validation scripts
tests/           — Schema + golden tests
scripts/         — AI integrator and utility scripts
prompts/         — System prompts
logs/            — Fieldlink lock files
EMERGENT_PATTERN/ — Emergent pattern examples
```

## Common Commands

```bash
# Install (editable)
pip install -e .

# Validate ontology (schema + referential integrity)
python examples/validate_ontology.py
# Expected output: "Ontology OK"

# Run rule engine
python -m rosetta_shape_core.expand ALIGN ANIMAL.BEE CONST.PHI --have CAP.SWARM_COORDINATION

# Run tests
python -m pytest tests/

# Pull fieldlink sources (stages unified atlas)
./fieldlink-pull.sh
```

## Key Conventions

- **Entity IDs** use dot-namespaced format: `ANIMAL.BEE`, `CONST.PHI`, `GEOM.TRI`, `SHAPE.TETRA`, `CAP.SWARM_COORDINATION`
- **Namespaces** defined in `ontology/_vocab.json`: ANIMAL, PLANT, MICROBE, CRYSTAL, GEOM, STRUCT, FIELD, CONST, TEMP, PROTO, CAP, SHAPE, EMOTION, DEFENSE, REGEN
- **Canonical ID registry**: `ontology/_id_registry.json` maps each namespace to its authoritative source repo
- **Relationship types**: IS_A, USES, ALIGNS_WITH, OPERATES_IN, STRUCTURE, SENSES_IN_FIELD, MORPHOLOGY, DERIVES, EMERGES_AS, CAPABILITIZED_BY
- **File naming**: snake_case for code/config, kebab-case for JSON data, dot-separated for schemas
- **All schema files** use JSON Schema 2020-12 (`$schema: "https://json-schema.org/draft/2020-12/schema"`)
- **Rules** are stored as JSONL (one JSON object per line) in `rules/expand.jsonl`

## Architecture Notes

- **Data-first**: JSON schemas define the contract; Python code is a thin validator + rule engine
- **Offline-friendly**: No network calls required for core validation/expansion
- **Fieldlink orchestration**: `.fieldlink.json` defines how to pull and merge data from sibling repos into `.fieldlink/merge_stage/`
- **Referential integrity**: `validator.py` checks ontology links, shape schemas, bridge references, and cross-repo refs
- **Rule priority**: Rules in `expand.jsonl` are sorted by descending `priority`; first match wins
- **Guards**: Rules can require capabilities via `guard.requires` — the subject entity (or `--have` flags) must satisfy them

## Workflow: Adding a New Entity

1. Add the entity to an appropriate file in `ontology/` (or create a new one)
2. Use an existing namespace from `_vocab.json`, or add a new one there first
3. Ensure `links[*].to` references point to valid entity IDs
4. Run `python examples/validate_ontology.py` to verify
5. If the entity needs rules, add JSONL lines to `rules/expand.jsonl`

## Workflow: Adding a New Shape

1. Create a JSON file in `shapes/` following `schema/shape.schema.json`
2. Use `SHAPE.X` dot-format for the ID (e.g., `SHAPE.DODECA`)
3. Include: id, name, faces, edges, vertices, families, polyhedral, bridges
4. Bridges must include: sensors, defenses, protocols, bridge_glyphs (audit_glyphs optional)
5. Run `python examples/validate_ontology.py` to verify schema + bridge integrity

## Do Not

- Break JSON Schema 2020-12 compatibility
- Add entities with duplicate IDs
- Create dangling `links[*].to` references
- Put spaces in filenames
- Mix tabs and spaces in JSON files
