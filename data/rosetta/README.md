# data/rosetta

Data for the Rosetta operator (T1–T5) and for `gap_scan`. Plain JSONL, one
record per line, stdlib-readable.

| file | module | what it holds |
|------|--------|---------------|
| `entries.jsonl` | `entry.py` (T3) | source systems read under stated forcing |
| `observations.jsonl` | `scope.py` (T4) | predictions run from a shape token's formal properties, and what happened |
| `transfers.jsonl` | `transfer.py` | what happened when a move was actually carried to a problem — outcome, where it broke, what the break indicts |
| `gate_log.jsonl` | `gate_log.py` (T5) | dated record of what a name had to get past. **Ships empty** — a record is observed evidence about a model, so nothing goes in that was not observed |
| `gap_scan/*.json` | `gap_scan.py` | closed instances: eras that ended, so the substrate metaphor is legible |

## Provenance is required on every record

Every entry, observation and scan instance carries a `provenance` block, and
so does every family in `families.py`:

```json
{"concept": "AUTHOR", "record": "MODEL", "note": "..."}
```

`concept` is where the thing being recorded came from; `record` is who wrote
the record text as it stands. Origins: `AUTHOR` (the repo author's own
material), `SPEC` (arrived with a build specification), `MODEL` (seeded by a
model during a build), `PUBLIC` (an established result, attributable to no
party here). No ranking is implied — the point is that the difference is
unrecoverable later.

```bash
python -m rosetta_shape_core.provenance --audit     # anything unmarked
python -m rosetta_shape_core.provenance --summary   # origin counts per set
```

Of the six seed entries, three are the author's material and three are not.
The nine families are SPEC-derived stand-ins pending the author's own set.

## Recording a transfer

The most valuable record in here is a move that was carried over and broke.
It measures a stop (turning `ASSERTED` into `MEASURED`), or it adds one the
entry was missing, or — if it was licensed and still failed — it counts
against the licensing criterion itself.

```bash
python -m rosetta_shape_core.transfer --validate
python -m rosetta_shape_core.transfer --audit       # what the outcomes say to fix
python -m rosetta_shape_core.scope --stops          # which stops have been carried to
```

A transfer with no `from_entry` is a pointer to an entry nobody has written.
Those are reported, not hidden.

## Adding an entry

```bash
python -m rosetta_shape_core.entry --validate   # structure + forcing terms resolve
python -m rosetta_shape_core.entry --lint       # advisory: intent attribution, moral labels
python -m rosetta_shape_core.scope --audit      # does it report where it STOPS?
```

`provenance` and `forcing_dominant` are required and validated —
`forcing_dominant` names the subset of terms that SETS the configuration, and
without it nothing can grade `SHARED_DOMINANT`. `forcing_terms` must resolve to families (`python -m rosetta_shape_core.families --list`).
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
