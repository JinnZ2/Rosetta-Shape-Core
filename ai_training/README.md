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

## Safe Entry Script

Run the guarded entry point before doing any work:

```bash
./ai_training/safe_entry.sh              # Full pipeline (orient + ground + validate)
./ai_training/safe_entry.sh orient       # Phase 1: Check core files exist
./ai_training/safe_entry.sh ground       # Phase 2: Validate schemas + self-audit
./ai_training/safe_entry.sh validate     # Run full test suite
./ai_training/safe_entry.sh explore      # List all entities
./ai_training/safe_entry.sh pre-commit   # Safety gate — run before every commit
./ai_training/safe_entry.sh status       # System health dashboard
```

**Safety protections built in:**
- Verifies you're in the right repo with the package installed
- Checks that immutable axioms and use constraints are intact
- Scans for secrets in the staging area (blocks `.env`, `*.key`, credentials)
- Warns on modifications to protected files (`_vocab.json`, `core.schema.json`)
- Pre-commit gate runs ontology validation, self-audit, and tests before allowing commit
- Scans diffs for destructive patterns (`rm -rf`, `force push`, `reset --hard`)
- Verifies `extracted_from` provenance on all atlas files

## For AI Agents

Start with `safe_entry.sh` or `entry_pipeline.json`. They define the read order, what to validate, and how to confirm you understand the system before making changes. The pipeline enforces: **read before write, validate before commit, physics before opinion.**
