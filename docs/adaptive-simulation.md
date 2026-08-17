# Adaptive Simulation Framework

`src/rosetta_shape_core/adaptive_sim.py`

A simulation runs. Falsifiable claims are tested against its outcomes. An agent
reads the failures, forms a hypothesis, changes one thing, and the loop runs
again. Every run — parameters, seed, outcomes, verdicts, and the reasoning that
motivated the next run — is appended to a JSONL provenance log validated against
[`schema/adaptive_run.schema.json`](../schema/adaptive_run.schema.json).

The point is not the two models that ship with it. The point is the record: an
experiment you can replay from the log alone, and a chain of reasoning where
every parameter change points back at the observation that motivated it.

## Commands

```bash
python -m rosetta_shape_core.adaptive_sim --model forest
python -m rosetta_shape_core.adaptive_sim --model fluctuating --iterations 8
python -m rosetta_shape_core.adaptive_sim --model forest --json
python -m rosetta_shape_core.adaptive_sim --validate-log data/adaptive_sim/provenance_forest.jsonl
rosetta-adaptive-sim --model forest --seed 7 --log runs.jsonl
```

Flags: `--model`, `--iterations`, `--seed`, `--exploration-rate`, `--log`,
`--json`, `--validate-log PATH`.

```python
from rosetta_shape_core import run_experiment

result = run_experiment("forest", iterations=5, seed=42, log_file="runs.jsonl")
```

## The loop

```
params ──▶ model.run() ──▶ outcomes ──▶ claims tested ──┬─ all passed ──▶ stop
   ▲                                                    │
   └────── agent: observation → hypothesis → action ◀────┴─ some failed
```

Each pass writes one `SimulationRecord`. The loop stops early the moment every
claim passes — there is nothing to learn from re-running an experiment that
already agrees with you.

## Models

| Model | What it does | Claims it must satisfy |
|-------|--------------|------------------------|
| `forest` | Trees on a grid grow as `size ** metabolic_exponent`, shade each other locally, and disperse seeds into thin canopy. | Tree sizes fit a power law (R² > 0.6); more than one species persists. |
| `fluctuating` | Moran process under a carrying capacity that random-walks between states; a fast and a slow strain compete. | Fixation happens in >50% of replicates; the slow strain still fixes >5% of the time. |

Add a model by registering a class that takes `(params, rng)` and exposes
`run() -> dict`:

```python
from rosetta_shape_core.adaptive_sim import register_model, CLAIM_REGISTRY, DEFAULT_PARAMS

register_model("mymodel", MyModel)
DEFAULT_PARAMS["mymodel"] = {...}
CLAIM_REGISTRY["mymodel"] = lambda: [Claim(...)]
```

## Claims

A `Claim` is a `claim_id`, a description, and a test function over the outcomes
dict returning `(passed, message, details)`. Three verdicts, not two:

- **passed** — the outcomes support it
- **failed** — the outcomes contradict it
- **inconclusive** — the test itself raised; an experiment that could not be run
  says nothing about the world, and is recorded as such rather than as a failure

Claims are tested highest-priority first. The agent may generate follow-up
claims when a run looks clean enough to push on — a good fit earns a harder
question.

## The record

One JSON object per line. `parameters` plus `random_seed` are sufficient to
replay the run; `run_id` is a hash of exactly those, so the same experiment
always carries the same id.

```json
{
  "run_id": "67bf6dd83afd",
  "model_name": "forest",
  "parameters": {"grid_size": 60, "metabolic_exponent": 0.75, "base_seed": 42},
  "random_seed": 42,
  "timestamp": 1786966832.69,
  "duration_seconds": 11.51,
  "outcomes": {"num_trees": 973, "size_distribution": {"slope": -0.37, "r_squared": 0.89}},
  "claim_results": {"forest_power_law": "passed"},
  "reasoning_chain": [
    {
      "step_id": "AutoAgent_step_1",
      "agent_name": "AutoAgent",
      "observation": "R^2 of power-law fit: 0.412",
      "hypothesis": "Power-law fit poor; hypothesis: competition too weak or simulation not at steady state.",
      "action": "Increased competition_strength to 1.200",
      "parameters_changed": {"competition_strength": [0.8, 1.2]},
      "expected_outcome": "Retest with modified parameters to verify hypothesis",
      "parent_step_id": null
    }
  ]
}
```

`expected_outcome` is written *before* the next run — that is what makes a step
falsifiable rather than a post-hoc story. `parent_step_id` links each step to
the one it descends from, so a chain can be walked backwards.

Records are validated on write: a record that does not match the schema raises
instead of silently entering the log.

### Tracing a run

A run's reasoning chain converts into KnowledgeDNA narrative nodes, so the same
backward-trace probes the ontology uses on any other claim chain work here:

```python
from rosetta_shape_core.adaptive_sim import to_narrative_chain
from rosetta_shape_core.knowledge_dna import trace_narrative

trace = trace_narrative("forest power-law experiment", to_narrative_chain(record))
print(trace.verdict, trace.provenance_intact)
```

## The agent

The agent is deliberately legible — hand-written rules, not a black box. It
observes, names a hypothesis, and takes a directed action:

| Observation | Hypothesis | Action |
|-------------|------------|--------|
| Power-law R² < 0.8 | Competition too weak, or not at steady state | Raise `competition_strength`, or lengthen the run |
| Slope out of range | Seed rate or metabolic exponent off | Raise `seed_rate` |
| Coexistence too high | Environment switching too fast for drift | Lower `switching_rate` |
| Slow strain never fixes | Growth ratio too unfavorable | Raise `growth_rate_ratio` |

`exploration_rate` (default 0.3) is the explore/exploit gate: with that
probability the agent perturbs a parameter at random instead of following the
hypothesis it just formed, so a loop that keeps failing the same way still
moves. Set it to `0.0` for purely directed search.

## Determinism

No global RNG state. Each iteration gets `random.Random(seed + iteration)`; the
agent carries its own stream; each replicate of the fluctuating model derives
its own from `base_seed`. Same seed and same parameters, same outcomes — which
is the whole basis for the log being a record of anything.

Standard library only. No numpy, so the framework runs anywhere the rest of the
package runs.

## Reference logs

[`data/adaptive_sim/`](../data/adaptive_sim) holds provenance logs and the
results figure from the original prototype runs. They are kept as fixtures: the
test suite validates them against the schema, so the record format cannot drift
away from logs already written.
