# Adaptive simulation — reference runs

Provenance logs and the results figure from the **original prototype** of the
adaptive simulation framework (the numpy implementation, before the standard
library port into `src/rosetta_shape_core/adaptive_sim.py`).

| File | What it is |
|------|------------|
| `provenance_forest.jsonl` | 2 runs of the forest metabolic-scaling model; both claims passed. |
| `provenance_fluctuating.jsonl` | 5 runs of the fluctuating-environment Moran model; claims failed, the agent lowered `switching_rate` each iteration. |
| `adaptive_sim_results.png` | Size distribution, claim status, and parameter evolution for those runs. |

These are kept as **fixtures, not as ground truth**. The test suite validates
every line against `schema/adaptive_run.schema.json`, so the record format
cannot drift away from logs that were already written. The numbers in them come
from a different RNG implementation and will not be reproduced by the current
code.

```bash
python -m rosetta_shape_core.adaptive_sim --validate-log data/adaptive_sim/provenance_forest.jsonl
```

Note that `provenance_fluctuating.jsonl` records `num_steps: 3000` with
`dt: 0.01` — 30 time units, far too short for fixation, which is why every
replicate ended in coexistence and both claims failed. The current defaults
(`num_steps: 100000`, `dt: 1.0`) reach fixation.

See [`docs/adaptive-simulation.md`](../../docs/adaptive-simulation.md).
