# data/rosetta

Data for the Rosetta operator (T1–T5) and for `gap_scan`. Plain JSONL, one
record per line, stdlib-readable.

| file | module | what it holds |
|------|--------|---------------|
| `entries.jsonl` | `entry.py` (T3) | source systems read under stated forcing |
| `observations.jsonl` | `scope.py` (T4) | predictions run from a shape token's formal properties, and what happened |
| `gate_log.jsonl` | `gate_log.py` (T5) | dated record of what a name had to get past. **Ships empty** — a record is observed evidence about a model, so nothing goes in that was not observed |
| `gap_scan/*.json` | `gap_scan.py` | closed instances: eras that ended, so the substrate metaphor is legible |

## Adding an entry

```bash
python -m rosetta_shape_core.entry --validate   # structure + forcing terms resolve
python -m rosetta_shape_core.entry --lint       # advisory: intent attribution, moral labels
python -m rosetta_shape_core.scope --audit      # does it report where it STOPS?
```

`forcing_terms` must resolve to families (`python -m rosetta_shape_core.families --list`).
`scope.stops` must exist. An entry that produces everywhere and never fails is
the flag, not the goal.

## Adding an observation

An observation is a prediction reasoned from the named shape's formal
properties (`python -m rosetta_shape_core.scope --shape HEXAGON`) plus what
happened. Give it a numeric `scale` when the failure is by scale, or a
`condition` string when it is by condition. Then:

```bash
python -m rosetta_shape_core.scope --classify HEXAGON
```

A failure is not a defect in the entry. It grades the token and measures a
boundary — both are results.

## Adding a gap_scan instance

Closed instances only, in this directory. The specific gap is
non-transferable; only the shape class transfers, and instantiating one on an
open instance needs that instance's own operands.
