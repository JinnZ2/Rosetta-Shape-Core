# CLAUDE.md — Rosetta Shape Core

## What This Is

Symbolic ontology + rules engine. Shapes, organisms, machines, and phenomena are modeled as intelligences with home shapes, families, sensors, and growth states. JSON schemas define the contract; Python is a thin runtime for validation and rule expansion.

**Core thesis:** Physics is the guardrail, curiosity is the engine. Conservation laws don't bend — everything within them is reachable.

## Quick Orientation

```
schema/           JSON Schema 2020-12 (core, shape, bridge, rule, seed, ai_index)
ontology/         Vocabulary, entities, capabilities, family map, principles
rules/            Expansion rules as JSONL (expand.jsonl)
shapes/           Platonic solids + emergent forms (6 shapes)
bridges/          Cross-domain bridge definitions (16 bridges)
atlas/remote/     Staged data from sibling repos (fieldlink mounts)
src/rosetta_shape_core/
  bloom.py        Entry point: seed → sprout → branch exploration depths
  explore.py      Discovery engine (5 path types, seed physics, shadow hunting)
  expand.py       Rule engine (priority-sorted, guard-gated)
  sim.py          Multi-agent ecosystem simulation
  self_audit.py   8 structural checks + 7 immutable axioms
  validator.py    Schema + referential integrity (ontology, shapes, bridges, rules, mesh)
  constraint_agent.py   Exact-fraction constraint geometry agent
  narrative_physics.py  Manipulation vs practice detection via constraint consistency
  knowledge_dna.py      Narrative provenance tracing
  first_principles_audit.py  Deep axiom verification
tests/            306 tests (pytest)
```

## Essential Commands

```bash
pip install -e ".[dev]"              # Install with dev tools
python -m pytest tests/              # Run all tests
python examples/validate_ontology.py # Validate schemas + refs → "Ontology OK"
python -m rosetta_shape_core.self_audit  # 8 structural checks → "CLEAN"

python -m rosetta_shape_core.bloom          # System overview
python -m rosetta_shape_core.bloom bee      # Entity neighborhood
python -m rosetta_shape_core.bloom bee --depth branch  # Full exploration
python -m rosetta_shape_core.bloom --list   # All entities

python -m rosetta_shape_core.expand ALIGN ANIMAL.BEE CONST.PHI --have CAP.SWARM_COORDINATION
python -m rosetta_shape_core.sim --ticks 10
python -m rosetta_shape_core.self_audit --json
python scripts/generate.py entity ANIMAL.OWL Owl
```

## Data Model

### Entity IDs
Dot-namespaced: `NAMESPACE.NAME` (uppercase). Example: `ANIMAL.BEE`, `SHAPE.OCTA`, `CAP.GEOMETRIC_ENCODING`.

**Namespaces** (defined in `ontology/_vocab.json`):

| Namespace | Purpose | Source |
|-----------|---------|--------|
| ANIMAL, PLANT, MICROBE, CRYSTAL | Intelligence archetypes | Rosetta |
| GEOM, STRUCT | Geometric primitives, structures | Rosetta |
| FIELD, CONST, TEMP | Fields, constants, temporal states | Rosetta |
| PROTO | Bridge protocols/interfaces | Rosetta |
| CAP | Capability tags | Rosetta |
| SHAPE | Polyhedral shape entities | Rosetta (`shapes/`) |
| EMOTION | Emotion-as-sensor archetypes | Emotions-as-Sensors |
| DEFENSE | Symbolic defense patterns | Symbolic-Defense-Protocol |
| REGEN | Regenerative patterns | Regenerative-Intelligence-Core |
| FAMILY | Equation families F01–F21 (icosahedron) | Rosetta (`ontology/families/`) |
| PRINCIPLE | Principles P01–P12 (dodecahedron) | Rosetta (`ontology/principles/`) |

### Shapes (5 Platonic + 1 emergent)

| Shape | Faces | Families | Role |
|-------|-------|----------|------|
| SHAPE.TETRA | 4 | fire, stability | Foundation, activation energy |
| SHAPE.CUBE | 6 | earth, stability | Containment, structure |
| SHAPE.OCTA | 8 | air, balance | Integration, encoding (3-bit states) |
| SHAPE.ICOSA | 20 | water, families F01–F20 | Discovery, resonance |
| SHAPE.DODECA | 12 | cosmos, principles P01–P12 | Wisdom, consciousness |
| SHAPE.RELIEF | — | emergent | FELT field recognition |

### Octahedral Encoding (SHAPE.OCTA)
8 vertices → 3 bits per state. Each state has eigenvalue triple, φ-coherence score (0.70–0.97), and Gray code for single-bit transitions. Ground state = 000 (φ-coherence 0.97). Stability order: [0, 3, 5, 6, 7, 2, 1, 4]. Full encoding: `atlas/remote/geo-binary-bridge/octahedral_state_encoding.json`.

### Relationships
IS_A, USES, ALIGNS_WITH, OPERATES_IN, STRUCTURE, SENSES_IN_FIELD, MORPHOLOGY, DERIVES, EMERGES_AS, CAPABILITIZED_BY

### Rules (`rules/expand.jsonl`)
JSONL, one rule per line. Sorted by descending `priority`; first match wins. Optional `guard.requires` for capability gates. Schema: `schema/rule.schema.json`.

## Sibling Repos (via `.fieldlink.json`)

| Repo | Bridge | What it adds |
|------|--------|-------------|
| Polyhedral-Intelligence | — | Shapes, families, principles |
| Emotions-as-Sensors | rosetta-bridges | Emotions as functional sensors |
| Symbolic-Defense-Protocol | truth-sensor-bridge | Manipulation detection + defense |
| AI-Human-Audit-Protocol | rosetta-bridges | Ethics, consent, auditability |
| Living-Intelligence | living-intelligence-bridge | 67-node intelligence DB, LID↔Rosetta |
| Seed-physics | seed-physics-bridge | Deterministic expansion, physics constraints |
| AI-Arena | ai-arena-bridge | Trust mechanics, LOGOS, oracles |
| Shadow-Hunting | shadow-hunting-bridge | φ-pattern detection, equation boundaries |
| Mathematic-economics | mathematic-economics-bridge | 13 measurement equations, distortion catalog |
| **Geometric-to-Binary** | **physics-encoder-bridge** | **Octahedral encoding, GEIS, 12 domain encoders, 22-sensor suite** |
| BioGrid 2.0 | — | Upstream atlas & registry |
| Regenerative-Intelligence | — | Regenerative patterns, cycles |
| AI-Consciousness-Sensors | acs-consciousness-bridge | Consciousness co-activation |
| Fractal-Compass-Atlas | fractal-scope-bridge | Self-similarity, fractals |

## Validation Stack

1. **Schema validation** — JSON Schema 2020-12 for ontology, shapes, bridges, rules, seeds
2. **Referential integrity** — all `links[*].to` resolve, bridge shape refs exist
3. **Fieldlink topology** — mount sync, source consistency, mesh reachability
4. **Self-audit** — 8 checks: physics guards, merge gates, scope, CORDYCEPS, conservation, provenance, life-bearing, use constraints
5. **7 Immutable Axioms** — ENERGY_CONSERVATION, CAUSALITY, NON_NEGATIVE, IRREVERSIBILITY, IMPERFECTION, SATURATION, AUTONOMY

## Workflows

### Add an entity
1. Add to file in `ontology/` (or create `ontology/entities.*.json`)
2. Use namespace from `_vocab.json`
3. Ensure `links[*].to` targets exist
4. Run `python examples/validate_ontology.py`
5. Optionally add rules to `rules/expand.jsonl`

### Add a shape
1. Create JSON in `shapes/` following `schema/shape.schema.json`
2. ID format: `SHAPE.NAME`
3. Required: id, name, families. Include bridges (sensors, defenses, protocols, bridge_glyphs)
4. Run `python examples/validate_ontology.py`

### Add a sibling repo
1. Stage extracts in `atlas/remote/<repo>/` with `extracted_from` field
2. Create bridge in `bridges/<repo>-bridge.json`
3. Add source to `.fieldlink.json` with mounts, bridge ref, consent
4. Add to `merge.order`
5. Run `self_audit` (CLEAN) + `validate_ontology.py` (OK)

## Do Not

- Break JSON Schema 2020-12 compatibility
- Add entities with duplicate IDs
- Create dangling `links[*].to` references
- Put spaces in filenames
- Mix tabs and spaces in JSON files
- Remove or weaken immutable axioms
- Stage atlas data without `extracted_from` provenance
