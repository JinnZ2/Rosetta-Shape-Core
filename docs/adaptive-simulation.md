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

---

# Discrepancies

`src/rosetta_shape_core/discrepancy.py`

Ports and rewrites throw off questions the code cannot answer: two readings of
the same parameter, two plausible update orders, a constant that could mean
either of two things. The tempting move is to pick one and write a confident
sentence about it. The framework offers a better one — write the readings down
as options, run them, and report what the runs actually support.

```bash
python -m rosetta_shape_core.discrepancy --list
python -m rosetta_shape_core.discrepancy --id forest_update_order --seeds 8
python -m rosetta_shape_core.discrepancy --all --seeds 8 --json --log sweep.jsonl
```

A `Discrepancy` is a question, its `origin` (where the ambiguity came from),
and two or more `Option`s, each a parameter patch. Exploring one runs every
option across N seeds, tests the model's registered claims against each arm,
and logs every arm as a normal provenance record tagged with
`experiment: {discrepancy_id, option_label, option_index}` — so a resolution
can be re-derived from the log rather than taken on trust.

```python
from rosetta_shape_core import Discrepancy, Option, explore_discrepancy

report = explore_discrepancy(Discrepancy(
    id="my_question",
    question="Does the boundary wrap or reflect?",
    model="forest",
    origin="The prototype clipped at the edge; a torus is equally defensible.",
    metric="size_distribution.r_squared",
    prefer="max",
    options=[Option("clip", "trees at the edge see fewer neighbours", {"wrap": False}),
             Option("torus", "the grid wraps", {"wrap": True})],
), seeds=(1, 2, 3, 4, 5))
```

## Verdicts

The point of the tool is that it is allowed to say *no*.

| Verdict | Meaning |
|---------|---------|
| `resolved` | One option wins on claims, or on the metric by more than the noise. `winner` is set. |
| `tie` | The top two are not separated. Either the choice does not matter, or the experiment is not sharp enough. Options that *were* ruled out are still named. |
| `separated` | For `prefer="distinguish"`: the options genuinely differ, and neither direction is better on its face. A modelling decision, not something the sim can settle. |
| `indistinguishable` | For `prefer="distinguish"`: the choice does not change the outcome. |
| `no_option_satisfies_claims` | Every option failed everything. The disagreement is with the model or the claims, not between the options. |

Two guards keep the verdicts honest:

- **A claim gap must be worth more than one run.** With ten claim tests per
  option, 80% against 70% is a single run going the other way. The required
  gap scales as `max(0.1, 1.5 / n_tests)`.
- **Separation is measured against the error on the mean**, not the spread
  across seeds. The spread does not shrink as seeds are added, so a rule built
  on it could never be sharpened by running more of them — and the report's
  advice to add seeds would be a lie.

## What the shipped questions found

Four discrepancies came out of the numpy-to-stdlib port. Run at 8 seeds; the
full report is in
[`data/adaptive_sim/discrepancy_report.json`](../data/adaptive_sim/discrepancy_report.json)
and all 88 arms are in `provenance_discrepancies.jsonl` beside it.

**`fluct_switch_semantics`** — how does a switching *rate* become a per-step
*probability*? **Separated.** At `switching_rate = 2.0`, the regime the agent
drives the model into, `1 - exp(-rate·dt)` gives a mean fixation time of
149.5 ± 7.6 against 126.3 ± 5.9 for the prototype's raw rate — about 18%
slower. Note that `clamped` and `rate_direct` are *identical to the last
digit*: `random() < 1.0` and `random() < 2.0` are the same test, so an
out-of-range probability never announces itself, it just silently saturates.
Neither reading is better on its face; this is a modelling decision.

**`fluct_dt_regime`** — what time horizon was the model meant to run for?
**Tie between the two long horizons**, with the short one ruled out. `dt=0.01`
over 300 000 steps and `dt=1.0` over 60 000 steps both reach fixation in every
replicate; the logged configuration (`dt=0.01`, 3 000 steps — 30 time units)
leaves 21% ± 10% of replicates still coexisting. Whatever `dt` was meant to
mean, the horizon in the shipped log is too short.

**`forest_competition_radius`** — how far does a tree's shade reach?
**Tie between radius 1 and radius 2**, with radius 4 ruled out. The prototype's
`dispersal_range // 2` coupling (radius 2, R² 0.80 ± 0.07) and plain nearest-
neighbour shading (radius 1, R² 0.80 ± 0.02) are indistinguishable. Letting
shade reach as far as seeds do (radius 4) drops R² to 0.64 ± 0.04 and starts
failing the power-law claim. The coupling is harmless; extending it is not.

**`forest_update_order`** — do trees see the forest as it was, or as it is
becoming? **Tie.** Asynchronous updating looks better (R² 0.64 ± 0.12 against
0.56 ± 0.19) but the seed-to-seed variance swamps it, and both pass 75% of
claim tests. Fifteen seeds did not separate them either. On present evidence
the convention does not matter.

## Adding a question

1. Add the knob to the model, defaulting to current behavior, so both readings
   are reachable from parameters alone.
2. `register(Discrepancy(...))` with an `origin` that says where the ambiguity
   came from — the question has to stay legible after whoever noticed it has
   moved on.
3. Pick `prefer`: `max`/`min` when the metric is a quality measure, or
   `distinguish` when the readings are merely different.
4. Run it. If the verdict is a tie, either add seeds or write a claim that
   bites on the difference — a tie is a result, not a failure.
