"""
Adaptive Simulation Framework — claim-driven experiments with full provenance.

A simulation runs, falsifiable claims are tested against its outcomes, an agent
observes the failures, forms a hypothesis, changes one thing, and the loop runs
again. Every run — parameters, seed, outcomes, verdicts, and the reasoning that
led to the next run — is appended to a JSONL provenance log validated against
``schema/adaptive_run.schema.json``.

Two models ship with the framework:

  forest       Spatially explicit forest with metabolic scaling. Trees grow as
               ``size ** metabolic_exponent``, shade each other locally, and
               disperse seeds. Tests whether tree sizes fall on a power law.
  fluctuating  Moran process in a switching environment. Two strains compete
               under a carrying capacity that random-walks between states.
               Tests whether the slower strain can still fix.

Models are registered in ``MODEL_REGISTRY`` — add one by registering a class
with a ``run()`` method that returns an outcomes dict.

Everything here is standard library only: no numpy, deterministic under a seed,
and replayable from the log alone.

Usage:
    python -m rosetta_shape_core.adaptive_sim --model forest
    python -m rosetta_shape_core.adaptive_sim --model fluctuating --iterations 8
    python -m rosetta_shape_core.adaptive_sim --model forest --json
    python -m rosetta_shape_core.adaptive_sim --validate-log data/adaptive_sim/provenance_forest.jsonl
"""
from __future__ import annotations

import argparse
import bisect
import copy
import hashlib
import json
import math
import pathlib
import random
import sys
import time
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from typing import Any, Callable, Optional

ROOT = pathlib.Path(__file__).resolve().parents[2]
SCHEMA_PATH = ROOT / "schema" / "adaptive_run.schema.json"

# ── provenance ────────────────────────────────────────────────────

@dataclass
class ReasoningStep:
    """One observation -> hypothesis -> action link in an agent's chain."""

    step_id: str
    timestamp: float
    agent_name: str
    observation: str
    hypothesis: str
    action: str
    parameters_changed: dict
    expected_outcome: str
    parent_step_id: Optional[str] = None


@dataclass
class SimulationRecord:
    """Complete, replayable account of a single simulation run."""

    run_id: str
    model_name: str
    parameters: dict
    random_seed: int
    timestamp: float
    duration_seconds: float
    outcomes: dict
    claim_results: dict
    reasoning_chain: list
    experiment: Optional[dict] = None

    def to_dict(self) -> dict:
        payload = _jsonify(asdict(self))
        if payload.get("experiment") is None:
            payload.pop("experiment", None)
        return payload


def _jsonify(value: Any) -> Any:
    """Coerce a record into JSON-native types.

    Tuples become lists and non-finite floats become null, so a record that
    round-trips through the log is the same record that validates.
    """
    if isinstance(value, dict):
        return {str(k): _jsonify(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonify(v) for v in value]
    if isinstance(value, bool) or value is None or isinstance(value, (int, str)):
        return value
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    return str(value)


def load_record_schema() -> dict:
    """Load the run-record JSON Schema."""
    with open(SCHEMA_PATH, encoding="utf-8") as f:
        return json.load(f)


def validate_record(record: dict) -> list:
    """Validate one run record against the schema. Returns a list of errors."""
    try:
        import jsonschema
    except ImportError:  # pragma: no cover - jsonschema is a hard dependency
        return []
    validator = jsonschema.Draft202012Validator(load_record_schema())
    return [f"{'/'.join(str(p) for p in e.path)}: {e.message}"
            for e in validator.iter_errors(record)]


def validate_log(path) -> dict:
    """Validate every line of a provenance log. Returns a report dict."""
    errors = []
    lines = 0
    with open(path, encoding="utf-8") as f:
        for lineno, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            lines += 1
            try:
                record = json.loads(line)
            except json.JSONDecodeError as e:
                errors.append(f"line {lineno}: not valid JSON — {e}")
                continue
            errors.extend(f"line {lineno}: {msg}" for msg in validate_record(record))
    return {"path": str(path), "records": lines, "errors": errors, "ok": not errors}


class ProvenanceLogger:
    """Appends run records to a JSONL log and keeps claim history in memory."""

    def __init__(self, log_file="provenance_log.jsonl", validate: bool = True):
        self.log_file = log_file
        self.validate = validate
        self.records: list = []
        self.claim_history: dict = defaultdict(list)

    def log_run(self, record: SimulationRecord) -> dict:
        payload = record.to_dict()
        if self.validate:
            errors = validate_record(payload)
            if errors:
                raise ValueError(
                    "run record does not match adaptive_run.schema.json: "
                    + "; ".join(errors)
                )
        self.records.append(record)
        if self.log_file:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(payload) + "\n")
        return payload

    def log_claim_result(self, claim_id: str, result: dict) -> None:
        self.claim_history[claim_id].append(result)

    def get_run_by_id(self, run_id: str) -> Optional[SimulationRecord]:
        for r in self.records:
            if r.run_id == run_id:
                return r
        return None

    def get_chain_for_claim(self, claim_id: str) -> list:
        return [r for r in self.records if claim_id in r.claim_results]

    def summary(self) -> dict:
        return {
            "total_runs": len(self.records),
            "claims_tested": sorted(self.claim_history.keys()),
            "models_used": sorted({r.model_name for r in self.records}),
        }


def to_narrative_chain(record: SimulationRecord) -> list:
    """Convert a run's reasoning chain into KnowledgeDNA narrative nodes.

    Lets a run be traced with the same backward-trace probes the ontology uses
    on any other claim chain: ``trace_narrative(desc, to_narrative_chain(rec))``.
    Ordered surface-first, matching KnowledgeDNA's convention.
    """
    from rosetta_shape_core.knowledge_dna import NarrativeNode

    nodes = []
    for step in reversed(record.reasoning_chain):
        step_dict = step if isinstance(step, dict) else asdict(step)
        nodes.append(NarrativeNode(
            claim=step_dict["hypothesis"] or "N/A",
            source=step_dict["agent_name"],
            source_type="primary",
            data_basis=step_dict["observation"],
            beneficiary="",
        ))
    nodes.append(NarrativeNode(
        claim=f"Run {record.run_id} of model {record.model_name}",
        source=f"seed={record.random_seed}",
        source_type="primary",
        data_basis=json.dumps(_jsonify(record.outcomes), sort_keys=True),
        beneficiary="",
    ))
    return nodes


# ── claims ────────────────────────────────────────────────────────

def fmt(value: Any, spec: str = ".3f") -> str:
    """Format a number, falling back to str() for anything unformattable.

    Claim messages are built from outcome dictionaries that may be missing a
    key; formatting ``'N/A'`` with a float spec would raise inside the claim and
    silently turn a clean failure into an inconclusive result.
    """
    try:
        return format(value, spec)
    except (TypeError, ValueError):
        return str(value)


@dataclass
class Claim:
    """A falsifiable claim about model behavior."""

    claim_id: str
    description: str
    model_type: str
    test_function: Callable
    priority: int = 1
    max_retries: int = 3
    status: str = "untested"
    evidence: list = field(default_factory=list)

    def test(self, outcomes: dict):
        """Test the claim. Returns ``(passed, message, details)``.

        A claim that raises is *inconclusive*, not failed — an experiment that
        could not be run says nothing about the world.
        """
        try:
            passed, message, details = self.test_function(outcomes)
            passed = bool(passed)
            self.status = "passed" if passed else "failed"
        except Exception as e:
            self.status = "inconclusive"
            return False, f"Test error: {e}", {}
        self.evidence.append({
            "passed": passed,
            "message": message,
            "details": details,
            "timestamp": time.time(),
        })
        return passed, message, details


def get_forest_claims() -> list:
    return [
        Claim(
            claim_id="forest_power_law",
            description="Tree-size distribution follows a power law with R^2 > 0.6",
            model_type="forest",
            test_function=lambda o: (
                o.get("size_distribution", {}).get("r_squared", 0) > 0.6,
                f"R^2 = {fmt(o.get('size_distribution', {}).get('r_squared', 'N/A'))}",
                o.get("size_distribution", {}),
            ),
        ),
        Claim(
            claim_id="forest_species_coexistence",
            description="Multiple species persist (richness > 1)",
            model_type="forest",
            test_function=lambda o: (
                o.get("species_richness", 0) > 1,
                f"Richness = {o.get('species_richness', 'N/A')}",
                {"richness": o.get("species_richness")},
            ),
        ),
    ]


def get_fluctuating_claims() -> list:
    return [
        Claim(
            claim_id="fluctuating_fixation",
            description="Fixation occurs in >50% of replicates (strains do not coexist indefinitely)",
            model_type="fluctuating",
            test_function=lambda o: (
                o.get("fixation_probability", {}).get("coexistence", 1.0) < 0.5,
                f"Coexistence prob = {fmt(o.get('fixation_probability', {}).get('coexistence', 'N/A'))}",
                o.get("fixation_probability", {}),
            ),
        ),
        Claim(
            claim_id="fluctuating_slow_persistence",
            description="Slow strain has non-zero fixation probability (>5%)",
            model_type="fluctuating",
            test_function=lambda o: (
                o.get("fixation_probability", {}).get("slow_strain", 0) > 0.05,
                f"Slow strain fixation = {fmt(o.get('fixation_probability', {}).get('slow_strain', 'N/A'), '.4f')}",
                o.get("fixation_probability", {}),
            ),
        ),
    ]


CLAIM_REGISTRY = {
    "forest": get_forest_claims,
    "fluctuating": get_fluctuating_claims,
}


# ── adaptive agent ────────────────────────────────────────────────

class AdaptiveAgent:
    """Reads outcomes, forms a hypothesis, changes parameters, logs why.

    ``exploration_rate`` is the explore/exploit gate: with that probability the
    agent perturbs a parameter at random instead of following the hypothesis it
    just formed, so a loop that keeps failing the same way still moves.
    """

    def __init__(self, name: str = "AdaptiveAgent", exploration_rate: float = 0.3,
                 rng: Optional[random.Random] = None):
        self.name = name
        self.exploration_rate = exploration_rate
        self.rng = rng or random.Random(0)
        self.reasoning_chain: list = []
        self.step_counter = 0
        self.claim_counter = 0

    def _new_step_id(self) -> str:
        self.step_counter += 1
        return f"{self.name}_step_{self.step_counter}"

    def analyze(self, outcomes: dict, failed_claims: list, current_params: dict,
                model_type: str):
        """Produce ``(new_params, new_claims, reasoning_step)``."""
        observation = self._generate_observation(outcomes, failed_claims, model_type)
        hypothesis = self._generate_hypothesis(outcomes, failed_claims, model_type)
        new_params, action_desc = self._propose_action(
            current_params, hypothesis, model_type, outcomes
        )
        new_claims = self._generate_claims(outcomes, model_type, new_params)

        parent = self.reasoning_chain[-1].step_id if self.reasoning_chain else None
        step = ReasoningStep(
            step_id=self._new_step_id(),
            timestamp=time.time(),
            agent_name=self.name,
            observation=observation,
            hypothesis=hypothesis,
            action=action_desc,
            parameters_changed=self._param_diff(current_params, new_params),
            expected_outcome="Retest with modified parameters to verify hypothesis",
            parent_step_id=parent,
        )
        self.reasoning_chain.append(step)
        return new_params, new_claims, step

    def _generate_observation(self, outcomes, failed_claims, model_type) -> str:
        parts = []
        if model_type == "forest":
            if "size_distribution" in outcomes:
                sd = outcomes["size_distribution"]
                parts.append(f"Size distribution slope: {fmt(sd.get('slope', 'N/A'))}")
                parts.append(f"R^2 of power-law fit: {fmt(sd.get('r_squared', 'N/A'))}")
            if "species_richness" in outcomes:
                parts.append(f"Species richness: {outcomes['species_richness']}")
        elif model_type == "fluctuating":
            fp = outcomes.get("fixation_probability", {})
            if fp:
                parts.append(f"Fixation prob (slow strain): {fmt(fp.get('slow_strain', 'N/A'), '.4f')}")
            if "mean_fixation_time" in outcomes:
                parts.append(f"Mean fixation time: {fmt(outcomes['mean_fixation_time'], '.2f')}")
        if failed_claims:
            parts.append(f"Failed claims: {[c.claim_id for c in failed_claims]}")
        return " | ".join(parts) if parts else "No significant observations."

    def _generate_hypothesis(self, outcomes, failed_claims, model_type) -> str:
        if not failed_claims:
            if model_type == "forest":
                return ("Exploring parameter space: testing sensitivity to "
                        "competition strength and dispersal range.")
            return ("Exploring parameter space: testing sensitivity to switching "
                    "rates and carrying capacity distribution.")
        hypotheses = []
        for claim in failed_claims:
            if claim.claim_id == "forest_power_law":
                if outcomes.get("size_distribution", {}).get("r_squared", 0) < 0.8:
                    hypotheses.append("Power-law fit poor; hypothesis: competition too weak "
                                      "or simulation not at steady state.")
                else:
                    hypotheses.append("Power-law slope outside predicted range; hypothesis: "
                                      "seed injection rate or metabolic exponent needs adjustment.")
            elif claim.claim_id == "fluctuating_fixation":
                hypotheses.append("Fixation probability deviates from theory; hypothesis: "
                                  "switching too fast relative to demographic rates, or "
                                  "population size too large for drift.")
            elif claim.claim_id == "fluctuating_slow_persistence":
                hypotheses.append("Slow strain fixation too low; hypothesis: growth rate ratio "
                                  "too unfavorable or switching too fast.")
        return " ".join(hypotheses) if hypotheses else "Investigating unexpected behavior."

    def _propose_action(self, params, hypothesis, model_type, outcomes):
        new_params = copy.deepcopy(params)
        actions = []
        explore = self.rng.random() < self.exploration_rate

        if model_type == "forest":
            if not explore and "competition too weak" in hypothesis:
                new_params["competition_strength"] = min(
                    params.get("competition_strength", 1.0) * 1.5, 5.0)
                actions.append(f"Increased competition_strength to "
                               f"{new_params['competition_strength']:.3f}")
            elif not explore and "not at steady state" in hypothesis:
                new_params["num_steps"] = int(params.get("num_steps", 1000) * 1.5)
                actions.append(f"Increased num_steps to {new_params['num_steps']}")
            elif not explore and "seed injection" in hypothesis:
                new_params["seed_rate"] = params.get("seed_rate", 0.1) * 1.5
                actions.append(f"Increased seed_rate to {new_params['seed_rate']:.3f}")
            elif self.rng.random() < 0.5:
                new_params["metabolic_exponent"] = _clip(
                    params.get("metabolic_exponent", 0.75) + self.rng.gauss(0, 0.05), 0.5, 1.0)
                actions.append(f"Perturbed metabolic_exponent to "
                               f"{new_params['metabolic_exponent']:.3f}")
            else:
                new_params["dispersal_range"] = max(
                    1, int(params.get("dispersal_range", 5)) + self.rng.randint(-2, 2))
                actions.append(f"Perturbed dispersal_range to {new_params['dispersal_range']}")

        elif model_type == "fluctuating":
            if not explore and "switching too fast" in hypothesis:
                new_params["switching_rate"] = params.get("switching_rate", 0.1) * 0.7
                actions.append(f"Decreased switching_rate to {new_params['switching_rate']:.4f}")
            elif not explore and "growth rate ratio" in hypothesis:
                new_params["growth_rate_ratio"] = min(
                    0.99, params.get("growth_rate_ratio", 0.95) + 0.02)
                actions.append(f"Increased growth_rate_ratio to "
                               f"{new_params['growth_rate_ratio']:.3f}")
            elif not explore and "population size too large" in hypothesis:
                new_params["carrying_capacities"] = [
                    max(10, int(k * 0.8)) for k in params.get("carrying_capacities", [100])]
                actions.append(f"Decreased carrying capacities to "
                               f"{new_params['carrying_capacities']}")
            elif self.rng.random() < 0.5:
                new_params["switching_rate"] = params.get("switching_rate", 0.1) * 1.3
                actions.append(f"Perturbed switching_rate to {new_params['switching_rate']:.4f}")
            else:
                new_params["num_replicates"] = int(params.get("num_replicates", 50)) + 20
                actions.append(f"Increased num_replicates to {new_params['num_replicates']}")

        action_str = "; ".join(actions) if actions else "No parameter changes (exploration complete)."
        return new_params, action_str

    def _generate_claims(self, outcomes, model_type, params) -> list:
        """Propose follow-up claims when a run looks clean enough to push on."""
        new_claims = []
        if model_type == "forest":
            if outcomes.get("size_distribution", {}).get("r_squared", 0) > 0.85:
                self.claim_counter += 1
                new_claims.append(Claim(
                    claim_id=f"forest_slope_steep_{self.claim_counter}",
                    description="Power-law slope is steeper than -1.5 once the fit is clean",
                    model_type="forest",
                    test_function=lambda o: (
                        o.get("size_distribution", {}).get("slope", 0) < -1.5,
                        f"Slope = {fmt(o.get('size_distribution', {}).get('slope', 'N/A'))}",
                        {"slope": o.get("size_distribution", {}).get("slope")},
                    ),
                    priority=2,
                ))
        elif model_type == "fluctuating":
            if outcomes.get("fixation_probability", {}).get("slow_strain", 0) > 0.3:
                self.claim_counter += 1
                new_claims.append(Claim(
                    claim_id=f"fluct_slow_persistence_{self.claim_counter}",
                    description="Slow strain persists when switching rate is comparable to growth rate",
                    model_type="fluctuating",
                    test_function=lambda o: (
                        o.get("fixation_probability", {}).get("slow_strain", 0) > 0.2,
                        f"Slow strain fixation = "
                        f"{fmt(o.get('fixation_probability', {}).get('slow_strain', 'N/A'), '.4f')}",
                        {"fp_slow": o.get("fixation_probability", {}).get("slow_strain")},
                    ),
                    priority=2,
                ))
        return new_claims

    @staticmethod
    def _param_diff(old: dict, new: dict) -> dict:
        diff = {}
        for k in sorted(set(old) | set(new)):
            if old.get(k) != new.get(k):
                diff[k] = [old.get(k), new.get(k)]
        return diff


def _clip(value: float, lo: float, hi: float) -> float:
    return float(min(max(value, lo), hi))


def derive_seed(base: int, index: int) -> int:
    """Independent stream for ``(base, index)``.

    Adding the index to the base is the obvious thing and the wrong thing: two
    runs seeded 1 and 2 then share every replicate but one, so a sweep across
    "different seeds" mostly re-measures the same trajectories and reports a
    spread near zero. Mixing the pair through a hash keeps the streams
    unrelated while staying fully reproducible.
    """
    return int(hashlib.sha256(f"{base}:{index}".encode()).hexdigest()[:16], 16)


# ── forest metabolic scaling model ────────────────────────────────

class ForestScalingSim:
    """Spatially explicit forest with metabolic scaling.

    Trees occupy cells on a square grid. Each grows by
    ``size ** metabolic_exponent``, discounted by the biomass of its
    neighborhood (light shading). Stressed trees die more often. Survivors
    disperse seeds into empty cells, which establish more readily where the
    canopy is thin.

    Competition is read from the *previous* state of the grid, so within a step
    every tree sees the same forest — growth, mortality and establishment are
    resolved synchronously.
    """

    def __init__(self, params: dict, rng: Optional[random.Random] = None):
        self.params = params
        self.rng = rng or random.Random(params.get("base_seed", 42))
        self.grid_size = int(params.get("grid_size", 100))
        self.metabolic_exponent = float(params.get("metabolic_exponent", 0.75))
        self.competition_strength = float(params.get("competition_strength", 1.0))
        self.dispersal_range = max(1, int(params.get("dispersal_range", 5)))
        self.seed_rate = float(params.get("seed_rate", 0.1))
        self.mortality_base = float(params.get("mortality_base", 0.01))
        self.num_steps = int(params.get("num_steps", 1000))
        self.initial_density = float(params.get("initial_density", 0.1))
        self.min_size = float(params.get("min_size", 1.0))
        self.num_species = int(params.get("num_species", 3))
        # Competition radius defaults to half the dispersal range (the original
        # coupling) but can be set independently.
        self.competition_radius = int(
            params.get("competition_radius", self.dispersal_range // 2))
        self.update_order = str(params.get("update_order", "synchronous"))

        n = self.grid_size
        self.grid = [0.0] * (n * n)
        self.species_grid = [0] * (n * n)
        self._sat: list = []
        self._initialize()

    def _initialize(self) -> None:
        n = self.grid_size
        n_trees = int(n * n * self.initial_density)
        for idx in self.rng.sample(range(n * n), n_trees):
            self.grid[idx] = self.rng.lognormvariate(2, 1)
            self.species_grid[idx] = self.rng.randint(1, self.num_species)

    def _build_sat(self) -> None:
        """Summed-area table over the grid, so neighborhood sums are O(1)."""
        n = self.grid_size
        w = n + 1
        sat = [0.0] * (w * w)
        grid = self.grid
        for i in range(n):
            row_sum = 0.0
            base = i * n
            out = (i + 1) * w
            prev = i * w
            for j in range(n):
                row_sum += grid[base + j]
                sat[out + j + 1] = sat[prev + j + 1] + row_sum
        self._sat = sat

    def _local_competition(self, i: int, j: int) -> float:
        """Neighborhood biomass excluding the focal cell, scaled by strength."""
        n = self.grid_size
        r = self.competition_radius
        i0, i1 = max(0, i - r), min(n, i + r + 1)
        j0, j1 = max(0, j - r), min(n, j + r + 1)
        w = n + 1
        sat = self._sat
        total = (sat[i1 * w + j1] - sat[i0 * w + j1]
                 - sat[i1 * w + j0] + sat[i0 * w + j0])
        return (total - self.grid[i * n + j]) * self.competition_strength

    def _direct_competition(self, grid: list, i: int, j: int) -> float:
        """Neighborhood sum read straight off ``grid`` — no summed-area table.

        Needed for asynchronous updates, where the grid changes underneath the
        sweep and a table built at the top of the step would be stale.
        """
        n = self.grid_size
        r = self.competition_radius
        total = 0.0
        for a in range(max(0, i - r), min(n, i + r + 1)):
            base = a * n
            for b in range(max(0, j - r), min(n, j + r + 1)):
                total += grid[base + b]
        return (total - grid[i * n + j]) * self.competition_strength

    def step(self) -> None:
        n = self.grid_size
        rng = self.rng
        # Asynchronous: every tree sees the forest as it stands mid-sweep, so
        # trees updated earlier already shade those updated later.
        asynchronous = self.update_order == "asynchronous"
        if not asynchronous:
            self._build_sat()
        new_grid = list(self.grid)
        new_species = list(self.species_grid)

        alive = []
        for i in range(n):
            base = i * n
            for j in range(n):
                idx = base + j
                size = self.grid[idx]
                if size <= 0:
                    continue
                alive.append((i, j))
                comp = (self._direct_competition(new_grid, i, j) if asynchronous
                        else self._local_competition(i, j))
                growth = max(0.0, size ** self.metabolic_exponent * 0.1 - comp * 0.001)
                new_grid[idx] = size + growth
                stress = comp / (size + 1)
                if rng.random() < self.mortality_base + stress * 0.001:
                    new_grid[idx] = 0.0
                    new_species[idx] = 0

        n_seeds = int(len(alive) * self.seed_rate)
        if alive:
            for _ in range(n_seeds):
                pi, pj = alive[rng.randrange(len(alive))]
                ni = pi + rng.randint(-self.dispersal_range, self.dispersal_range)
                nj = pj + rng.randint(-self.dispersal_range, self.dispersal_range)
                if not (0 <= ni < n and 0 <= nj < n):
                    continue
                target = ni * n + nj
                if new_grid[target] != 0:
                    continue
                comp_here = (self._direct_competition(new_grid, ni, nj) if asynchronous
                             else self._local_competition(ni, nj))
                local_light = 1.0 - min(1.0, comp_here * 0.0001)
                if rng.random() < local_light:
                    new_grid[target] = self.min_size * (1 + rng.expovariate(2.0))
                    new_species[target] = self.species_grid[pi * n + pj]

        self.grid = new_grid
        self.species_grid = new_species

    def run(self) -> dict:
        for _ in range(self.num_steps):
            self.step()
        return self.analyze()

    def analyze(self) -> dict:
        sizes = [s for s in self.grid if s > 0]
        outcomes = {
            "num_trees": len(sizes),
            "mean_size": (sum(sizes) / len(sizes)) if sizes else 0.0,
            "max_size": max(sizes) if sizes else 0.0,
            "species_richness": len({s for s in self.species_grid if s > 0}),
        }
        if len(sizes) > 100:
            fit = _power_law_fit(sizes, lo=max(self.min_size, min(sizes)), bins=29)
            if fit:
                outcomes["size_distribution"] = fit
        return outcomes


def _power_law_fit(values: list, lo: float, bins: int = 29,
                   min_occupied: int = 6) -> Optional[dict]:
    """Log-log least-squares fit of a log-binned histogram.

    Returns ``{"slope", "r_squared"}``, or ``None`` when there is not enough
    occupied bin structure to fit anything meaningful.
    """
    hi = max(values)
    if lo <= 0 or hi <= lo:
        return None
    log_lo, log_hi = math.log10(lo), math.log10(hi)
    edges = [10 ** (log_lo + (log_hi - log_lo) * k / bins) for k in range(bins + 1)]

    hist = [0] * bins
    for v in values:
        k = bisect.bisect_right(edges, v) - 1
        if k == bins:  # right edge is inclusive, as in numpy's histogram
            k = bins - 1
        if 0 <= k < bins:
            hist[k] += 1

    xs, ys = [], []
    for k, count in enumerate(hist):
        if count > 0:
            xs.append(math.log(math.sqrt(edges[k] * edges[k + 1])))
            ys.append(math.log(count))
    if len(xs) < min_occupied:
        return None

    n = len(xs)
    sx, sy = sum(xs), sum(ys)
    sxx = sum(x * x for x in xs)
    sxy = sum(x * y for x, y in zip(xs, ys))
    denom = n * sxx - sx * sx
    if denom == 0:
        return None
    slope = (n * sxy - sx * sy) / denom
    intercept = (sy - slope * sx) / n
    mean_y = sy / n
    ss_res = sum((y - (slope * x + intercept)) ** 2 for x, y in zip(xs, ys))
    ss_tot = sum((y - mean_y) ** 2 for y in ys)
    return {
        "slope": float(slope),
        "r_squared": float(1 - ss_res / ss_tot) if ss_tot > 0 else 0.0,
    }


# ── fluctuating population model ──────────────────────────────────

class FluctuatingPopSim:
    """Moran process under a randomly switching carrying capacity.

    The environment random-walks over ``num_states``, each with its own
    carrying capacity. Population size tracks the current capacity; within it, a
    fast and a slow strain compete by death-birth Moran updates. Replicates run
    until one strain fixes, the population dies out, or ``num_steps`` elapse.

    Environment switching is a rate: the per-step probability is
    ``1 - exp(-rate * dt)``, which stays a probability however large the agent
    pushes ``switching_rate``.

    Each replicate draws its own stream from ``base_seed`` (which the runner
    sets to the run's seed) via :func:`derive_seed`, so a single replicate can
    be reproduced without replaying the ones before it, and neighbouring base
    seeds do not share replicates. The shared ``rng`` is accepted for interface
    symmetry with other models and left unused.
    """

    def __init__(self, params: dict, rng: Optional[random.Random] = None):
        self.params = params
        self.rng = rng
        self.num_states = int(params.get("num_states", 5))
        self.switching_rate = float(params.get("switching_rate", 0.1))
        self.dt = float(params.get("dt", 1.0))
        self.switch_semantics = str(params.get("switch_semantics", "exponential"))
        self.growth_rate_fast = float(params.get("growth_rate_fast", 1.0))
        self.growth_rate_ratio = float(params.get("growth_rate_ratio", 0.95))
        self.growth_rate_slow = self.growth_rate_fast * self.growth_rate_ratio
        self.num_steps = int(params.get("num_steps", 100000))
        self.num_replicates = int(params.get("num_replicates", 100))
        self.base_seed = int(params.get("base_seed", 42))

        # Copy before padding: the caller's parameter dict must not be mutated,
        # or the logged parameters stop matching the run that produced them.
        caps = [int(k) for k in params.get("carrying_capacities", [50, 100, 200, 300, 400])]
        if not caps:
            caps = [100]
        while len(caps) < self.num_states:
            caps.append(max(1, int(caps[-1] * 1.2)))
        self.carrying_capacities = caps[:self.num_states]

    def _switch_probability(self, state: int) -> float:
        """Total outflow rate from ``state``, as a per-step probability.

        ``switch_semantics`` selects how a rate becomes a probability:

        ``exponential``   ``1 - exp(-rate * dt)`` — bounded for any rate.
        ``clamped``       ``min(rate * dt, 1)`` — linear until it saturates.
        ``rate_direct``   the rate used as a probability and ``dt`` ignored —
                          the prototype's reading, which silently exceeds 1
                          once the agent pushes ``switching_rate`` up.
        """
        rate = self.switching_rate * 0.5 * len(self._neighbors(state))
        if self.switch_semantics == "rate_direct":
            return rate
        if self.switch_semantics == "clamped":
            return min(1.0, rate * self.dt)
        return 1.0 - math.exp(-rate * self.dt)

    def _neighbors(self, state: int) -> list:
        return [s for s in (state - 1, state + 1) if 0 <= s < self.num_states]

    def _run_replicate(self, seed: int) -> dict:
        rng = random.Random(seed)
        env_state = self.num_states // 2
        capacity = self.carrying_capacities[env_state]
        n_fast = capacity // 2
        n_slow = capacity - n_fast
        steps = 0

        for _ in range(self.num_steps):
            if rng.random() < self._switch_probability(env_state):
                env_state = rng.choice(self._neighbors(env_state))
                capacity = self.carrying_capacities[env_state]
                total = n_fast + n_slow
                # Resize the population to the new capacity, sampling which
                # strain gains or loses in proportion to current abundance.
                while total > capacity and total > 0:
                    if rng.random() < n_fast / total:
                        n_fast -= 1
                    else:
                        n_slow -= 1
                    total = n_fast + n_slow
                while total < capacity:
                    if total > 0 and rng.random() < n_fast / total:
                        n_fast += 1
                    else:
                        n_slow += 1
                    total = n_fast + n_slow

            total = n_fast + n_slow
            if total == 0:
                break

            # Death: uniform over individuals.
            if rng.random() < n_fast / total:
                n_fast -= 1
            else:
                n_slow -= 1

            # Birth: weighted by growth rate.
            total_w = n_fast * self.growth_rate_fast + n_slow * self.growth_rate_slow
            if total_w > 0:
                if rng.random() < (n_fast * self.growth_rate_fast) / total_w:
                    n_fast += 1
                else:
                    n_slow += 1

            steps += 1
            if n_fast == 0 or n_slow == 0:
                break

        return {
            "n_fast_final": n_fast,
            "n_slow_final": n_slow,
            "steps": steps,
            "fast_fixes": n_fast > 0 and n_slow == 0,
            "slow_fixes": n_slow > 0 and n_fast == 0,
            "coexistence": n_fast > 0 and n_slow > 0,
            "extinction": n_fast == 0 and n_slow == 0,
        }

    def run(self) -> dict:
        results = [self._run_replicate(derive_seed(self.base_seed, rep))
                   for rep in range(self.num_replicates)]
        total = len(results)
        fixation_times = [r["steps"] for r in results if r["fast_fixes"] or r["slow_fixes"]]
        mean_t = (sum(fixation_times) / len(fixation_times)) if fixation_times else 0.0
        var_t = (sum((t - mean_t) ** 2 for t in fixation_times) / len(fixation_times)
                 if fixation_times else 0.0)
        def share(key: str) -> float:
            return sum(1 for r in results if r[key]) / total if total else 0.0

        return {
            "num_replicates": total,
            "fixation_probability": {
                "fast_strain": share("fast_fixes"),
                "slow_strain": share("slow_fixes"),
                "coexistence": share("coexistence"),
                "extinction": share("extinction"),
            },
            "mean_fixation_time": float(mean_t),
            "std_fixation_time": float(math.sqrt(var_t)),
        }


MODEL_REGISTRY = {
    "forest": ForestScalingSim,
    "fluctuating": FluctuatingPopSim,
}


def register_model(name: str, cls) -> None:
    """Register a model class. It must accept ``(params, rng)`` and expose ``run()``."""
    MODEL_REGISTRY[name] = cls


# ── runner ────────────────────────────────────────────────────────

DEFAULT_PARAMS = {
    "forest": {
        "grid_size": 60,
        "metabolic_exponent": 0.75,
        "competition_strength": 0.8,
        "dispersal_range": 4,
        "seed_rate": 0.15,
        "mortality_base": 0.01,
        "num_steps": 500,
        "initial_density": 0.15,
        "num_species": 3,
        "min_size": 1.0,
    },
    "fluctuating": {
        "num_states": 5,
        "carrying_capacities": [50, 100, 200, 300, 400],
        "switching_rate": 0.1,
        "growth_rate_fast": 1.0,
        "growth_rate_ratio": 0.95,
        "dt": 1.0,
        "num_steps": 100000,
        "num_replicates": 50,
    },
}


class SimulationRunner:
    """Runs a model, tests claims, hands failures to the agent, repeats."""

    def __init__(self, model_type: str, logger: ProvenanceLogger,
                 agent: AdaptiveAgent, quiet: bool = False):
        if model_type not in MODEL_REGISTRY:
            raise ValueError(f"Unknown model type: {model_type}. "
                             f"Known: {sorted(MODEL_REGISTRY)}")
        self.model_type = model_type
        self.logger = logger
        self.agent = agent
        self.quiet = quiet
        self.claims: list = []

    def register_claim(self, claim: Claim) -> None:
        self.claims.append(claim)

    def _say(self, msg: str) -> None:
        if not self.quiet:
            print(msg)

    def _run_id(self, iteration: int, params: dict, seed: int) -> str:
        """Deterministic id: same model, iteration, seed and params -> same id."""
        payload = json.dumps(
            {"model": self.model_type, "iteration": iteration,
             "seed": seed, "params": _jsonify(params)},
            sort_keys=True,
        )
        return hashlib.sha256(payload.encode()).hexdigest()[:12]

    def run_adaptive_loop(self, initial_params: dict, max_iterations: int = 5,
                          random_seed: int = 42) -> dict:
        current_params = copy.deepcopy(initial_params)
        iteration_results = []

        for iteration in range(max_iterations):
            seed = random_seed + iteration
            current_params["base_seed"] = seed
            self._say(f"\n{'=' * 60}")
            self._say(f"ITERATION {iteration + 1}/{max_iterations} | Model: {self.model_type}")
            self._say(f"{'=' * 60}")

            run_id = self._run_id(iteration, current_params, seed)
            sim = MODEL_REGISTRY[self.model_type](current_params, random.Random(seed))
            t0 = time.time()
            outcomes = sim.run()
            duration = time.time() - t0

            claim_results = {}
            failed_claims = []
            for claim in sorted(self.claims, key=lambda c: -c.priority):
                if claim.model_type != self.model_type:
                    continue
                passed, msg, details = claim.test(outcomes)
                claim_results[claim.claim_id] = {
                    "status": claim.status, "message": msg, "details": details,
                }
                self.logger.log_claim_result(claim.claim_id, {
                    "run_id": run_id, "status": claim.status, "message": msg,
                })
                if not passed:
                    failed_claims.append(claim)
                self._say(f"  Claim [{claim.claim_id}]: {claim.status.upper()} - {msg}")

            record = SimulationRecord(
                run_id=run_id,
                model_name=self.model_type,
                parameters=copy.deepcopy(current_params),
                random_seed=seed,
                timestamp=time.time(),
                duration_seconds=duration,
                outcomes=outcomes,
                claim_results={k: v["status"] for k, v in claim_results.items()},
                reasoning_chain=[],
            )

            if failed_claims and iteration < max_iterations - 1:
                new_params, new_claims, step = self.agent.analyze(
                    outcomes, failed_claims, current_params, self.model_type
                )
                record.reasoning_chain = [step]
                current_params = new_params
                for nc in new_claims:
                    self.register_claim(nc)
                    self._say(f"  New claim generated: {nc.claim_id}")
                self._say(f"  Agent: {step.action}")
            else:
                if not failed_claims:
                    self._say("  All claims passed — stopping early.")
                record.reasoning_chain = [ReasoningStep(
                    step_id=f"final_{iteration}",
                    timestamp=time.time(),
                    agent_name=self.agent.name,
                    observation="Final iteration or all claims passed.",
                    hypothesis="N/A",
                    action="Terminate loop",
                    parameters_changed={},
                    expected_outcome="N/A",
                )]

            self.logger.log_run(record)
            iteration_results.append({
                "iteration": iteration,
                "run_id": run_id,
                "params": copy.deepcopy(record.parameters),
                "outcomes": outcomes,
                "claim_results": claim_results,
                "failed_claims": [c.claim_id for c in failed_claims],
            })

            if not failed_claims:
                break

        return {
            "model_type": self.model_type,
            "total_iterations": len(iteration_results),
            "final_params": current_params,
            "iteration_results": iteration_results,
            "logger_summary": self.logger.summary(),
        }


def run_experiment(model: str, iterations: int = 5, seed: int = 42,
                   log_file="provenance_log.jsonl", params: Optional[dict] = None,
                   exploration_rate: float = 0.3, quiet: bool = False) -> dict:
    """Run a full adaptive loop for ``model`` and return the result dict."""
    logger = ProvenanceLogger(log_file=log_file)
    agent = AdaptiveAgent(name="AutoAgent", exploration_rate=exploration_rate,
                          rng=random.Random(seed))
    runner = SimulationRunner(model, logger, agent, quiet=quiet)
    for claim in CLAIM_REGISTRY.get(model, lambda: [])():
        runner.register_claim(claim)
    merged = copy.deepcopy(DEFAULT_PARAMS.get(model, {}))
    merged.update(params or {})
    return runner.run_adaptive_loop(merged, max_iterations=iterations, random_seed=seed)


# ── cli ───────────────────────────────────────────────────────────

def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Adaptive simulation framework — claim-driven experiments with provenance."
    )
    parser.add_argument("--model", choices=sorted(MODEL_REGISTRY), default="forest")
    parser.add_argument("--iterations", type=int, default=5)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--exploration-rate", type=float, default=0.3,
                        help="Probability the agent perturbs at random instead of "
                             "following its hypothesis.")
    parser.add_argument("--log", default="provenance_log.jsonl",
                        help="JSONL provenance log to append to.")
    parser.add_argument("--json", action="store_true", help="Emit the result as JSON.")
    parser.add_argument("--validate-log", metavar="PATH",
                        help="Validate an existing provenance log and exit.")
    args = parser.parse_args(argv)

    if args.validate_log:
        report = validate_log(args.validate_log)
        if args.json:
            print(json.dumps(report, indent=2))
        else:
            print(f"{report['path']}: {report['records']} record(s)")
            for err in report["errors"]:
                print(f"  ERROR {err}")
            print("OK" if report["ok"] else "INVALID")
        return 0 if report["ok"] else 1

    result = run_experiment(
        model=args.model,
        iterations=args.iterations,
        seed=args.seed,
        log_file=args.log,
        exploration_rate=args.exploration_rate,
        quiet=args.json,
    )

    if args.json:
        print(json.dumps(_jsonify(result), indent=2))
        return 0

    print(f"\n{'=' * 60}")
    print("FINAL SUMMARY")
    print(f"{'=' * 60}")
    print(f"Model: {result['model_type']}")
    print(f"Total iterations: {result['total_iterations']}")
    print(f"Final parameters: {json.dumps(_jsonify(result['final_params']), indent=2)}")
    print(f"\nProvenance log: {args.log}")
    print(f"Logger summary: {result['logger_summary']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
