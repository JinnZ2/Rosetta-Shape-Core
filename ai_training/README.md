# AI Training — Entry Pipeline

This folder is the entry point for AI agents learning to work with Rosetta-Shape-Core.
It links two upstream training sources into the ontology graph.

## Linked Repositories

| Source | Role | Bridge |
|--------|------|--------|
| [The-Curriculum-of-Everything-Earth-](https://github.com/JinnZ2/The-Curriculum-of-Everything-Earth-) | Curriculum engine — cross-disciplinary learning modules, nature-based pedagogy | `bridges/curriculum-bridge.json` |
| [Voice-Integrity-Module](https://github.com/JinnZ2/Voice-Integrity-Module) | Voice protocol — prosodic integrity, logic-aligned voice modes, silence-as-signal | `bridges/voice-integrity-bridge.json` |

## Entry Pipeline

```
1. ORIENT    → Read ai_training/index.json        (file inventory + topology)
2. GROUND    → Read ai_training/entry_pipeline.json (sequenced learning path)
3. CONNECT   → Read bridges/curriculum-bridge.json  (curriculum ↔ shapes)
             → Read bridges/voice-integrity-bridge.json (voice ↔ sensors)
4. VALIDATE  → python examples/validate_ontology.py (schema + ref integrity)
5. EXPLORE   → python -m rosetta_shape_core.bloom --list (all entities)
6. AUDIT     → python -m rosetta_shape_core.self_audit  (structural checks)
```

## How It Fits

- **Curriculum** maps to SHAPE.ICOSA (20 faces = 20 learning families) and SHAPE.DODECA (12 faces = 12 principles). Nature teachers from the curriculum align with ontology entities (ANIMAL.*, PLANT.*, CRYSTAL.*).
- **Voice Integrity** maps to the sensor system — voice modes are sensors, silence is a valid signal state. Prosodic patterns bridge to octahedral encoding (SHAPE.OCTA).

## For AI Agents

Start with `entry_pipeline.json`. It defines the read order, what to validate, and how to confirm you understand the system before making changes. The pipeline enforces: **read before write, validate before commit, physics before opinion.**
