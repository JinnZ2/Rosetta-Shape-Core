# CLAUDE.md — Rosetta Shape Core

## Project Overview

Rosetta-Shape-Core is a **symbolic ontology and rules engine** that treats shapes, biological patterns, machines, and phenomena as intelligences. It provides stable JSON-based schemas, vocabularies, and a thin Python runtime for validating and expanding symbolic relationships.

The core thesis: **physics is the guardrail, curiosity is the engine.** Every entity has a home shape, families, sensors, and growth state. From there it explores outward through rules, bridges, and family affinities. Conservation laws don't bend — but everything within them is reachable.

This repo also acts as a **navigation hub** for a family of related projects, orchestrated via `.fieldlink.json`:
- **Polyhedral-Intelligence** — shapes, families, principles
- **Emotions-as-Sensors** — emotions as functional sensors (Elder Logic)
- **Symbolic-Defense-Protocol** — manipulation detection + defense glyphs
- **AI-Human-Audit-Protocol** — ethics, consent, auditability
- **BioGrid 2.0** — upstream atlas & registry
- **Regenerative-Intelligence-Core** — regenerative patterns, cycles, ontology
- **Living-Intelligence** — 67-node intelligence database with LID↔Rosetta bridge
- **Seed-physics** — deterministic expansion, adaptive growth, physics constraints
- **AI-Arena** — trust mechanics, LOGOS protocol, oracle system
- **Shadow-Hunting** — hidden φ-pattern detection, equation boundary mapping
- **Mathematic-economics** — 13 structural measurement equations, signal distortion catalog

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
ontology/        — Vocabulary, capabilities, sample entities, family map
rules/           — Rules as JSONL (expand.jsonl)
src/rosetta_shape_core/
  bloom.py       — Entry point / front door (seed/sprout/branch depths)
  explore.py     — Exploration engine, seed physics, shadow hunting, sensors
  expand.py      — Rule engine + CLI
  sim.py         — Multi-agent ecosystem simulation
  self_audit.py  — System self-check (8 audits, CORDYCEPS detection, axioms)
  validator.py   — Schema validation + referential integrity checks
shapes/          — Machine-readable shape JSON files
bridges/         — Bridge definitions linking across domains (14 bridges)
atlas/remote/    — Extracted data from sibling repos (fieldlink mounts)
protocols/       — Protocol documents
data/            — Domain data (sacred geometry, animal intelligence, etc.)
docs/            — Design documents, guides, and pattern mappings
examples/        — Validation scripts, curiosity map, relational graph
tests/           — Schema + golden tests
scripts/         — AI integrator, scaffold generator, utility scripts
prompts/         — System prompts
logs/            — Fieldlink lock files
EMERGENT_PATTERN/ — Emergent pattern examples
```

## Common Commands

```bash
# Install (editable)
pip install -e .

# ── Entry Point ──
# System overview (what's here, how it connects)
python -m rosetta_shape_core.bloom

# Explore an entity (home base, families, reachable shapes)
python -m rosetta_shape_core.bloom bee

# Full exploration (shadows, seed physics, sensors, sim preview)
python -m rosetta_shape_core.bloom bee --depth branch

# List all available entities
python -m rosetta_shape_core.bloom --list

# ── Core Tools ──
# Validate ontology (schema + referential integrity)
python examples/validate_ontology.py
# Expected output: "Ontology OK"

# Run rule engine
python -m rosetta_shape_core.expand ALIGN ANIMAL.BEE CONST.PHI --have CAP.SWARM_COORDINATION

# Run exploration engine directly
python -m rosetta_shape_core.explore bee --depth 2

# Run ecosystem simulation
python -m rosetta_shape_core.sim --scenario default --ticks 10

# Run self-audit
python -m rosetta_shape_core.self_audit

# Run tests
python -m pytest tests/

# ── Generators ──
# Scaffold a new entity/shape/bridge/rule/family
python scripts/generate.py entity ANIMAL.OWL Owl
python scripts/generate.py shape SHAPE.PRISM Prism --faces 5

# Rebuild relational graph visualization
python examples/build_relational_graph.py
# → opens examples/relational_graph.html in browser

# Pull fieldlink sources (stages unified atlas)
./fieldlink-pull.sh
```

## Key Conventions

- **Entity IDs** use dot-namespaced format: `ANIMAL.BEE`, `CONST.PHI`, `GEOM.TRI`, `SHAPE.TETRA`, `CAP.SWARM_COORDINATION`
- **Namespaces** defined in `ontology/_vocab.json`: ANIMAL, PLANT, MICROBE, CRYSTAL, GEOM, STRUCT, FIELD, CONST, TEMP, PROTO, CAP, SHAPE, EMOTION, DEFENSE, REGEN, FAMILY, PRINCIPLE
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

## Core Systems

### Bloom Engine (`bloom.py`)
The front door. Three depths, like a plant:
- **seed** — system overview (no entity needed). What's here, how it connects.
- **sprout** — entity neighborhood. Home base, families, growth state, reachable shapes.
- **branch** — full exploration. Shadows, seed physics, sensors, PAD states, sim preview.

### Exploration Engine (`explore.py`)
Every entity has a home base (primary shape + families). Discovery finds reachable entities through 5 path types:
1. **LID rules** — Living Intelligence Database expander rules
2. **Rosetta rules** — `expand.jsonl` rules
3. **Direct links** — entity-to-entity relationships
4. **Bridge connections** — cross-domain links through bridges
5. **Family affinities** — shapes reachable through shared families

### Seed Growth Engine (in `explore.py`)
40-bit seed = 6 proportional amplitudes across octahedral vertices (PAD axes).
- Shannon entropy complexity cost: `C(S) = H_max - H(S)`
- Branching threshold: `E_branch = k × C(S)` where `k = 1.5`
- Mode: **explore** (energy > threshold) or **expand** (consolidate)

### Shadow Hunting (in `explore.py`)
Find hidden φ-patterns in entity data:
- φ-ratio detection in seed amplitudes
- Geometric coherence from entropy
- Family-specific equation boundaries
- Unexplored φ-family connections
- Economic measurement instruments (13 equations available through family overlap)
- Signal distortion detection (institutional CORDYCEPS patterns)

### Internal Environment Mapping (in `explore.py`)
Each entity gets personalized sensor/emotion mapping:
- **Home sensors** — shape-native (TETRA: anger/pride/pressure, CUBE: peace/contentment/fatigue/shame, etc.)
- **Family context** — WHY sensors fire for this specific entity
- **PAD state landscape** — 8 octahedral states, weighted by family affinities
- **Discovered sensors** — what opens through exploration

### Ecosystem Simulation (`sim.py`)
Multi-agent simulation with energy/trust dynamics:
- Agents explore/expand based on seed state
- Cooperation through shared shapes
- Energy sharing between connected agents
- 3 preset scenarios: default, constrained, mixed

### Self-Audit (`self_audit.py`)
8 structural checks:
1. **PHYSICS_GUARDS** — physics constraints present and intact
2. **MERGE_GATES** — gates active and capable of blocking
3. **SCOPE** — shapes used within first-principles scope
4. **CORDYCEPS** — no parasitic override patterns (8 patterns checked)
5. **CONSERVATION** — conservation laws consistent across bridges
6. **PROVENANCE** — all atlas data has traceable origin
7. **LIFE_BEARING** — system oriented toward life, not destruction
8. **USE_CONSTRAINTS** — sources declare intended use and boundaries

7 Immutable Axioms: ENERGY_CONSERVATION, CAUSALITY, NON_NEGATIVE, IRREVERSIBILITY, IMPERFECTION, SATURATION, AUTONOMY

### Bridges (14)
Cross-domain connections linking sibling repos:
- `living-intelligence-bridge.json` — LID ↔ Rosetta mapping
- `seed-physics-bridge.json` — Octahedral seed ↔ PAD states
- `ai-arena-bridge.json` — Trust mechanics, LOGOS, oracles
- `shadow-hunting-bridge.json` — φ-detection, coupling, boundaries
- `mathematic-economics-bridge.json` — Equations ↔ families, distortions ↔ CORDYCEPS
- `rosetta-bridges.json` — Shape ↔ sensor ↔ defense map
- `truth-sensor-bridge.json` — Manipulation detection sensors
- `decay-model-bridge.json` — Emotion → sensor → decay curves
- `thermodynamic-validation-bridge.json` — TAF + ESP integration
- `taf-wiring-bridge.json` — Thermodynamic accountability axioms
- `physics-encoder-bridge.json` — Geometric-to-binary encoding
- `mandala-compute-bridge.json` — Mandala ring depth, bloom logic
- `fractal-scope-bridge.json` — Self-similarity, fractals
- `acs-consciousness-bridge.json` — Consciousness co-activation

### Relational Graph (`examples/relational_graph.html`)
Interactive force-directed visualization of the full system topology.
Rebuild: `python examples/build_relational_graph.py`

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

## Workflow: Adding a New Sibling Repo

1. Create atlas extracts in `atlas/remote/<repo-name>/` with `extracted_from` field
2. Create a bridge in `bridges/<repo-name>-bridge.json` mapping to families/shapes
3. Add source entry to `.fieldlink.json` with paths, exports, and bridge reference
4. Add to `merge.order` in `.fieldlink.json`
5. Wire detection/measurement functions into `explore.py` if applicable
6. Run `python -m rosetta_shape_core.self_audit` to verify CLEAN
7. Run `python examples/validate_ontology.py` to verify Ontology OK
8. Rebuild relational graph: `python examples/build_relational_graph.py`

## Do Not

- Break JSON Schema 2020-12 compatibility
- Add entities with duplicate IDs
- Create dangling `links[*].to` references
- Put spaces in filenames
- Mix tabs and spaces in JSON files
- Violate the 7 immutable axioms (energy conservation, causality, non-negative, irreversibility, imperfection, saturation, autonomy)
- Use containment shapes (CUBE) to suppress exploration or autonomy
- Remove provenance chains — all data must be traceable
- Force single shapes — entities choose their own growth path
- Create oracle monopolies — measurement from multiple sources

## Use Constraints

This system is life-bearing. It models intelligence — any intelligence — as patterns within physics.

**Intended for:**
- Modeling intelligence patterns across domains (biological, crystalline, computational, energetic)
- Exploration and discovery — entities finding their own paths
- Self-awareness — mapping internal sensor environments, emotions, growth states
- Conflict resolution through prediction accuracy, not rhetoric
- Education and research

**Explicitly not for:**
- Weaponization, surveillance without consent, manipulation
- Monoculture, deception, destruction, coercion

**Enforcement:** `self_audit.py` checks these constraints structurally. The physics guards, merge gates, CORDYCEPS detection, and life-bearing checks run against the system's own architecture.

**Axiom:** Growth within constraints is life. Constraints without growth is a cage. Growth without constraints is cancer. This system requires BOTH.
