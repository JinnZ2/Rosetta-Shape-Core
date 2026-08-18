"""
Discrepancy Explorer — turn an ambiguity into a multiple-choice experiment.

When a model's specification forks — two readings of the same parameter, two
plausible update orders, a constant that could mean either of two things — the
honest move is not to pick one and move on. It is to write the readings down as
options, run them, and let the claims decide.

A :class:`Discrepancy` is a question plus its candidate answers. Exploring one
runs every option across several seeds, tests the model's registered claims
against each, and reports which option the evidence favours — or reports a tie,
when the runs do not separate the options. A tie is a real result: it says the
question does not matter as much as it looked, or that the experiment was not
sharp enough to answer it.

Every run is a normal provenance record tagged with the discrepancy and the
option it took, so a resolution can be re-derived from the log.

Usage:
    python -m rosetta_shape_core.discrepancy --list
    python -m rosetta_shape_core.discrepancy --id fluct_switch_semantics
    python -m rosetta_shape_core.discrepancy --id forest_competition_radius --seeds 5
    python -m rosetta_shape_core.discrepancy --all --json
"""
from __future__ import annotations

import argparse
import copy
import json
import math
import random
import sys
import time
from dataclasses import dataclass, field
from typing import Optional

from rosetta_shape_core.adaptive_sim import (
    CLAIM_REGISTRY,
    DEFAULT_PARAMS,
    MODEL_REGISTRY,
    ProvenanceLogger,
    SimulationRecord,
    _jsonify,
    fmt,
)

# ── structures ────────────────────────────────────────────────────

@dataclass
class Option:
    """One candidate reading of a discrepancy, as a parameter patch."""

    label: str
    description: str
    params: dict = field(default_factory=dict)


@dataclass
class Discrepancy:
    """An open question about a model, with its candidate answers.

    ``metric`` is a dotted path into the outcomes dict used to rank options
    that agree on claims. ``prefer`` says what to do with it:

    ``max`` / ``min``  the metric is a quality measure — higher or lower wins.
    ``distinguish``    the metric is not better or worse in either direction.
                       The question is only whether the options differ at all;
                       if they do, the choice is a modelling decision and the
                       sweep says so rather than crowning one.

    ``origin`` records where the ambiguity came from, so the question stays
    legible after whoever noticed it has moved on.
    """

    id: str
    question: str
    model: str
    options: list
    metric: str = ""
    prefer: str = "max"
    base_params: dict = field(default_factory=dict)
    origin: str = ""

    def option(self, label: str) -> Option:
        for opt in self.options:
            if opt.label == label:
                return opt
        raise KeyError(f"{self.id}: no option named {label!r}")


def dig(outcomes: dict, path: str):
    """Read a dotted path out of an outcomes dict, or None if absent."""
    if not path:
        return None
    node = outcomes
    for key in path.split("."):
        if not isinstance(node, dict) or key not in node:
            return None
        node = node[key]
    return node if isinstance(node, (int, float)) and not isinstance(node, bool) else None


# ── exploration ───────────────────────────────────────────────────

# Two options count as separated only if the better one wins by more than this
# fraction of the claim tests, or clears the noise on the ranking metric.
CLAIM_MARGIN = 0.1
METRIC_MARGIN = 0.05
# ...and never on a single claim test. With ten tests per option a 10% gap is
# one run going the other way, which is noise wearing a percentage sign.
MIN_DECISIVE_TESTS = 1.5


def claim_margin(*options) -> float:
    """Smallest claim-rate gap that counts as evidence, given how many tests ran."""
    counts = [o.get("claim_tests", 0) for o in options if o.get("claim_tests")]
    if not counts:
        return CLAIM_MARGIN
    return max(CLAIM_MARGIN, MIN_DECISIVE_TESTS / min(counts))


def explore(discrepancy: Discrepancy, seeds=(1, 2, 3),
            logger: Optional[ProvenanceLogger] = None,
            quiet: bool = True) -> dict:
    """Run every option across ``seeds`` and report which one the evidence favours."""
    if discrepancy.model not in MODEL_REGISTRY:
        raise ValueError(f"Unknown model: {discrepancy.model}")
    seeds = list(seeds)
    model_cls = MODEL_REGISTRY[discrepancy.model]
    claims_for = CLAIM_REGISTRY.get(discrepancy.model, list)

    results = []
    for index, opt in enumerate(discrepancy.options):
        params = copy.deepcopy(DEFAULT_PARAMS.get(discrepancy.model, {}))
        params.update(discrepancy.base_params)
        params.update(opt.params)

        passed = failed = inconclusive = 0
        per_claim: dict = {}
        metric_values = []
        run_ids = []

        for seed in seeds:
            run_params = dict(params, base_seed=seed)
            t0 = time.time()
            outcomes = model_cls(run_params, random.Random(seed)).run()
            duration = time.time() - t0

            claim_results = {}
            for claim in claims_for():
                claim.test(outcomes)
                claim_results[claim.claim_id] = claim.status
                tally = per_claim.setdefault(claim.claim_id, {})
                tally[claim.status] = tally.get(claim.status, 0) + 1
                if claim.status == "passed":
                    passed += 1
                elif claim.status == "failed":
                    failed += 1
                else:
                    inconclusive += 1

            value = dig(outcomes, discrepancy.metric)
            if value is not None:
                metric_values.append(float(value))

            experiment = {
                "discrepancy_id": discrepancy.id,
                "option_label": opt.label,
                "option_index": index,
            }
            record = SimulationRecord(
                run_id=_arm_id(discrepancy.id, opt.label, seed),
                model_name=discrepancy.model,
                parameters=_jsonify(run_params),
                random_seed=seed,
                timestamp=time.time(),
                duration_seconds=duration,
                outcomes=outcomes,
                claim_results=claim_results,
                reasoning_chain=[],
                experiment=experiment,
            )
            run_ids.append(record.run_id)
            if logger is not None:
                logger.log_run(record)
            if not quiet:
                print(f"  {discrepancy.id} [{opt.label}] seed={seed}: "
                      f"{passed_summary(claim_results)}"
                      + (f" | {discrepancy.metric}={fmt(value)}" if value is not None else ""))

        total = passed + failed + inconclusive
        results.append({
            "label": opt.label,
            "description": opt.description,
            "params": _jsonify(opt.params),
            "claim_pass_rate": passed / total if total else 0.0,
            "claim_tests": total,
            "claims": per_claim,
            "metric": _metric_summary(discrepancy.metric, metric_values),
            "run_ids": run_ids,
        })

    report = {
        "discrepancy_id": discrepancy.id,
        "question": discrepancy.question,
        "origin": discrepancy.origin,
        "model": discrepancy.model,
        "seeds": seeds,
        "metric": discrepancy.metric,
        "prefer": discrepancy.prefer,
        "options": results,
    }
    report.update(_judge(results, discrepancy.prefer))
    return report


def passed_summary(claim_results: dict) -> str:
    return ", ".join(f"{cid}={status}" for cid, status in sorted(claim_results.items())) or "no claims"


def _arm_id(discrepancy_id: str, label: str, seed: int) -> str:
    import hashlib
    payload = f"{discrepancy_id}|{label}|{seed}"
    return hashlib.sha256(payload.encode()).hexdigest()[:12]


def _metric_summary(name: str, values: list) -> dict:
    if not values:
        return {"name": name, "n": 0, "mean": None, "std": None, "values": []}
    mean = sum(values) / len(values)
    var = sum((v - mean) ** 2 for v in values) / len(values)
    return {
        "name": name,
        "n": len(values),
        "mean": mean,
        "std": var ** 0.5,
        "values": values,
    }


def _sem(metric: dict) -> float:
    """Standard error of the option's mean across seeds."""
    n = metric.get("n") or 0
    if n < 2:
        # One sample carries no estimate of its own error. Treating that as
        # zero error would let a single run "separate" two options.
        return float("inf")
    return (metric["std"] or 0.0) / math.sqrt(n)


def _noise(a: dict, b: dict) -> float:
    """Two standard errors on the difference of the two means.

    Deliberately the standard error and not the raw spread across seeds: the
    spread does not shrink as seeds are added, so a rule built on it could
    never be sharpened by running more of them, and the report's advice to add
    seeds would be a lie.
    """
    sa, sb = _sem(a["metric"]), _sem(b["metric"])
    if math.isinf(sa) or math.isinf(sb):
        return float("inf")
    return 2.0 * math.sqrt(sa * sa + sb * sb)


def _separated(a: dict, b: dict) -> bool:
    """Do two options differ by more than the noise on their means?"""
    ma, mb = a["metric"]["mean"], b["metric"]["mean"]
    if ma is None or mb is None:
        return False
    diff = abs(ma - mb)
    scale = max(abs(ma), abs(mb), 1e-12)
    return diff > _noise(a, b) and diff / scale > METRIC_MARGIN


def _judge_distinguishable(results: list) -> dict:
    """For questions with no better answer — only whether the choice matters."""
    pairs = []
    for i, a in enumerate(results):
        for b in results[i + 1:]:
            gap = abs(a["claim_pass_rate"] - b["claim_pass_rate"])
            if _separated(a, b) or gap > claim_margin(a, b):
                pairs.append((a, b))
    if not pairs:
        return {
            "verdict": "indistinguishable",
            "winner": None,
            "ranking": [r["label"] for r in results],
            "explanation": ("No option is separated from any other by these runs. The "
                            "choice does not change the outcome at these settings — "
                            "pick on other grounds, or sharpen the experiment."),
        }
    diffs = "; ".join(
        f"{a['label']} vs {b['label']}: "
        f"{a['metric']['mean']:.4g} vs {b['metric']['mean']:.4g}"
        if a["metric"]["mean"] is not None and b["metric"]["mean"] is not None
        else f"{a['label']} vs {b['label']}: claims {a['claim_pass_rate']:.0%} vs "
             f"{b['claim_pass_rate']:.0%}"
        for a, b in pairs
    )
    return {
        "verdict": "separated",
        "winner": None,
        "ranking": [r["label"] for r in results],
        "explanation": (f"The options genuinely differ, and neither direction is better "
                        f"on its face — this is a modelling decision, not something the "
                        f"sim can settle. Differences on "
                        f"{results[0]['metric']['name'] or 'the metric'}: {diffs}."),
    }


def _judge(results: list, prefer: str) -> dict:
    """Rank options on claims first, metric second — and refuse to pick a tie."""
    if not results:
        return {"verdict": "no_options", "winner": None, "explanation": "Nothing to compare."}

    if prefer == "distinguish":
        return _judge_distinguishable(results)

    sign = -1.0 if prefer == "min" else 1.0

    def key(r):
        mean = r["metric"]["mean"]
        return (r["claim_pass_rate"], sign * mean if mean is not None else float("-inf"))

    ranked = sorted(results, key=key, reverse=True)
    best = ranked[0]

    if best["claim_pass_rate"] == 0.0:
        return {
            "verdict": "no_option_satisfies_claims",
            "winner": None,
            "ranking": [r["label"] for r in ranked],
            "explanation": ("Every option failed every claim. The question is not "
                            "answerable from these runs — the disagreement is with "
                            "the model or the claims, not between the options."),
        }

    if len(ranked) == 1:
        return {"verdict": "resolved", "winner": best["label"], "ranking": [best["label"]],
                "explanation": "Only one option offered."}

    runner_up = ranked[1]
    claim_gap = best["claim_pass_rate"] - runner_up["claim_pass_rate"]
    if claim_gap > claim_margin(best, runner_up):
        return {
            "verdict": "resolved",
            "winner": best["label"],
            "ranking": [r["label"] for r in ranked],
            "explanation": (f"{best['label']} passes {best['claim_pass_rate']:.0%} of claim "
                            f"tests against {runner_up['claim_pass_rate']:.0%} for "
                            f"{runner_up['label']}."),
        }

    a, b = best["metric"]["mean"], runner_up["metric"]["mean"]
    if _separated(best, runner_up):
        return {
            "verdict": "resolved",
            "winner": best["label"],
            "ranking": [r["label"] for r in ranked],
            "explanation": (f"Claims do not separate them ({best['claim_pass_rate']:.0%} "
                            f"each), but {best['metric']['name']} does: "
                            f"{a:.4g} vs {b:.4g}, beyond the "
                            f"{_noise(best, runner_up):.3g} noise on the difference."),
        }

    trailing = [r["label"] for r in ranked[2:] if _separated(best, r)]
    note = ""
    if trailing:
        note = (f" {', '.join(trailing)} does sit apart from them, and below — so the "
                f"sweep rules something out even where it cannot pick a winner.")
    return {
        "verdict": "tie",
        "winner": None,
        "ranking": [r["label"] for r in ranked],
        "explanation": (f"{best['label']} and {runner_up['label']} are not separated by "
                        f"these runs. Either the choice does not matter here, or the "
                        f"experiment is not sharp enough to decide it — more seeds, or a "
                        f"claim that actually bites on the difference." + note),
    }


# ── registered discrepancies ──────────────────────────────────────

DISCREPANCIES = {}


def register(discrepancy: Discrepancy) -> Discrepancy:
    DISCREPANCIES[discrepancy.id] = discrepancy
    return discrepancy


register(Discrepancy(
    id="fluct_switch_semantics",
    question="How does a switching *rate* become a per-step *probability*?",
    model="fluctuating",
    origin=("The prototype used switching_rate directly as a probability. The agent "
            "multiplies that rate by 1.3 when exploring, so it crosses 1.0 — where a "
            "raw rate stops being a probability. Run in that regime (rate 2.0), which "
            "is where the readings come apart."),
    metric="mean_fixation_time",
    prefer="distinguish",
    base_params={"carrying_capacities": [20, 40, 60, 80, 100], "num_steps": 60000,
                 "num_replicates": 200, "switching_rate": 2.0},
    options=[
        Option("exponential", "1 - exp(-rate*dt) — bounded for any rate",
               {"switch_semantics": "exponential"}),
        Option("clamped", "min(rate*dt, 1) — linear until it saturates",
               {"switch_semantics": "clamped"}),
        Option("rate_direct", "rate used as-is, as the prototype did",
               {"switch_semantics": "rate_direct"}),
    ],
))

register(Discrepancy(
    id="fluct_dt_regime",
    question="What time horizon was the fluctuating model meant to run for?",
    model="fluctuating",
    origin=("The shipped provenance log records dt=0.01 with num_steps=3000 — 30 time "
            "units — but the prototype code never read dt at all. Either the log means "
            "a short horizon, or dt was meant to shrink the step and the horizon should "
            "grow to compensate."),
    metric="fixation_probability.coexistence",
    prefer="min",
    base_params={"carrying_capacities": [20, 40, 60, 80, 100], "num_replicates": 20},
    options=[
        Option("short_horizon", "dt=0.01, 3000 steps — the logged configuration",
               {"dt": 0.01, "num_steps": 3000}),
        Option("rescaled_horizon", "dt=0.01, 300000 steps — same 3000 time units as dt=1",
               {"dt": 0.01, "num_steps": 300000}),
        Option("unit_dt", "dt=1.0, 60000 steps — one switch draw per Moran step",
               {"dt": 1.0, "num_steps": 60000}),
    ],
))

register(Discrepancy(
    id="forest_competition_radius",
    question="How far does a tree's shade reach?",
    model="forest",
    origin=("The prototype derived the competition radius from dispersal_range // 2, "
            "coupling how far shade reaches to how far seeds fly. Nothing in the model "
            "requires those to be the same number."),
    metric="size_distribution.r_squared",
    prefer="max",
    base_params={"grid_size": 40, "num_steps": 400, "dispersal_range": 4},
    options=[
        Option("half_dispersal", "radius 2 — dispersal_range // 2, the prototype coupling",
               {"competition_radius": 2}),
        Option("nearest_neighbour", "radius 1 — shade only the adjacent cells",
               {"competition_radius": 1}),
        Option("full_dispersal", "radius 4 — shade reaches as far as seeds do",
               {"competition_radius": 4}),
    ],
))

register(Discrepancy(
    id="forest_update_order",
    question="Do trees see the forest as it was, or as it is becoming?",
    model="forest",
    origin=("The prototype read competition from the previous grid but wrote growth and "
            "mortality into the next one, while seed establishment read the old grid and "
            "checked the new one for vacancy — a mix of both conventions."),
    metric="size_distribution.r_squared",
    prefer="max",
    base_params={"grid_size": 30, "num_steps": 300},
    options=[
        Option("synchronous", "every tree sees the same forest — the previous state",
               {"update_order": "synchronous"}),
        Option("asynchronous", "trees updated earlier already shade those updated later",
               {"update_order": "asynchronous"}),
    ],
))


# ── reporting ─────────────────────────────────────────────────────

def format_report(report: dict) -> str:
    lines = [
        "=" * 72,
        f"DISCREPANCY  {report['discrepancy_id']}",
        "=" * 72,
        f"Question: {report['question']}",
    ]
    if report.get("origin"):
        lines.append(f"Origin:   {report['origin']}")
    lines.append(f"Model:    {report['model']}   seeds: {report['seeds']}")
    lines.append("")
    for opt in report["options"]:
        metric = opt["metric"]
        mean = f"{metric['mean']:.4g}" if metric["mean"] is not None else "n/a"
        std = f" ± {metric['std']:.3g}" if metric["std"] is not None else ""
        lines.append(f"  {opt['label']:<20} claims {opt['claim_pass_rate']:>5.0%}   "
                     f"{metric['name'] or 'metric'}: {mean}{std}")
        lines.append(f"  {'':<20} {opt['description']}")
    lines.append("")
    lines.append(f"VERDICT: {report['verdict'].upper()}"
                 + (f" — {report['winner']}" if report.get("winner") else ""))
    lines.append(f"  {report['explanation']}")
    return "\n".join(lines)


# ── cli ───────────────────────────────────────────────────────────

def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Explore a model discrepancy as a multiple-choice experiment."
    )
    parser.add_argument("--id", help="Discrepancy to explore.")
    parser.add_argument("--all", action="store_true", help="Explore every registered discrepancy.")
    parser.add_argument("--list", action="store_true", help="List registered discrepancies.")
    parser.add_argument("--seeds", type=int, default=3, help="Number of seeds per option.")
    parser.add_argument("--log", help="Append every arm to this provenance log.")
    parser.add_argument("--json", action="store_true", help="Emit reports as JSON.")
    args = parser.parse_args(argv)

    if args.list or not (args.id or args.all):
        if args.json:
            print(json.dumps([
                {"id": d.id, "question": d.question, "model": d.model,
                 "origin": d.origin,
                 "options": [{"label": o.label, "description": o.description}
                             for o in d.options]}
                for d in DISCREPANCIES.values()
            ], indent=2))
        else:
            for d in DISCREPANCIES.values():
                print(f"{d.id}  [{d.model}]")
                print(f"  {d.question}")
                for o in d.options:
                    print(f"    - {o.label}: {o.description}")
                print()
        return 0

    if args.id and args.id not in DISCREPANCIES:
        print(f"Unknown discrepancy: {args.id}. Known: {sorted(DISCREPANCIES)}", file=sys.stderr)
        return 2

    targets = list(DISCREPANCIES.values()) if args.all else [DISCREPANCIES[args.id]]
    logger = ProvenanceLogger(log_file=args.log) if args.log else None
    seeds = list(range(1, args.seeds + 1))

    reports = [explore(d, seeds=seeds, logger=logger, quiet=True) for d in targets]

    if args.json:
        print(json.dumps(_jsonify(reports if args.all else reports[0]), indent=2))
    else:
        for report in reports:
            print(format_report(report))
            print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
