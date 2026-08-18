"""Tests for the Adaptive Simulation Framework."""
import json
import pathlib
import random

import jsonschema
import pytest

from rosetta_shape_core.adaptive_sim import (
    CLAIM_REGISTRY,
    DEFAULT_PARAMS,
    MODEL_REGISTRY,
    AdaptiveAgent,
    Claim,
    FluctuatingPopSim,
    ForestScalingSim,
    ProvenanceLogger,
    SimulationRecord,
    SimulationRunner,
    _power_law_fit,
    derive_seed,
    fmt,
    get_fluctuating_claims,
    get_forest_claims,
    load_record_schema,
    main,
    register_model,
    run_experiment,
    to_narrative_chain,
    validate_log,
    validate_record,
)
from rosetta_shape_core.knowledge_dna import trace_narrative

ROOT = pathlib.Path(__file__).resolve().parents[1]
SAMPLE_LOGS = sorted((ROOT / "data" / "adaptive_sim").glob("*.jsonl"))

SMALL_FOREST = {
    "grid_size": 24, "num_steps": 12, "initial_density": 0.3,
    "num_species": 3, "dispersal_range": 4, "seed_rate": 0.15,
    "competition_strength": 0.8, "metabolic_exponent": 0.75,
    "mortality_base": 0.01, "min_size": 1.0,
}
SMALL_FLUCT = {
    "num_states": 5, "carrying_capacities": [10, 20, 30, 40, 50],
    "switching_rate": 0.1, "num_steps": 2000, "num_replicates": 8,
}


# ── schema ────────────────────────────────────────────────────────

def test_record_schema_is_a_valid_json_schema():
    schema = load_record_schema()
    jsonschema.Draft202012Validator.check_schema(schema)
    assert schema["$id"].endswith("adaptive_run.schema.json")


@pytest.mark.parametrize("log_path", SAMPLE_LOGS, ids=lambda p: p.name)
def test_sample_logs_validate(log_path):
    """Reference logs from the original prototype still match the schema."""
    report = validate_log(log_path)
    assert report["ok"], report["errors"]
    assert report["records"] > 0


def test_expected_sample_logs_are_present():
    names = {p.name for p in SAMPLE_LOGS}
    assert {"provenance_forest.jsonl", "provenance_fluctuating.jsonl"} <= names
    assert "provenance_discrepancies.jsonl" in names


def test_validate_record_rejects_missing_field():
    errors = validate_record({"run_id": "abc", "model_name": "forest"})
    assert errors


def test_validate_record_rejects_unknown_claim_status():
    record = json.loads(SAMPLE_LOGS[0].read_text().splitlines()[0])
    record["claim_results"] = {"some_claim": "maybe"}
    assert validate_record(record)


def test_validate_log_reports_bad_json(tmp_path):
    bad = tmp_path / "bad.jsonl"
    bad.write_text("{not json}\n")
    report = validate_log(bad)
    assert not report["ok"]
    assert "not valid JSON" in report["errors"][0]


# ── forest model ──────────────────────────────────────────────────

def test_forest_outcomes_have_expected_keys():
    sim = ForestScalingSim(SMALL_FOREST, random.Random(1))
    out = sim.run()
    for key in ("num_trees", "mean_size", "max_size", "species_richness"):
        assert key in out
    assert out["num_trees"] >= 0
    assert out["species_richness"] <= SMALL_FOREST["num_species"]


def test_forest_is_deterministic_under_a_seed():
    a = ForestScalingSim(SMALL_FOREST, random.Random(7)).run()
    b = ForestScalingSim(SMALL_FOREST, random.Random(7)).run()
    assert a == b


def test_forest_differs_across_seeds():
    a = ForestScalingSim(SMALL_FOREST, random.Random(7)).run()
    b = ForestScalingSim(SMALL_FOREST, random.Random(8)).run()
    assert a != b


def test_forest_does_not_mutate_params():
    params = dict(SMALL_FOREST)
    before = json.dumps(params, sort_keys=True)
    ForestScalingSim(params, random.Random(1)).run()
    assert json.dumps(params, sort_keys=True) == before


def test_forest_competition_matches_direct_neighborhood_sum():
    """The summed-area table must agree with a naive neighborhood sum."""
    sim = ForestScalingSim(SMALL_FOREST, random.Random(3))
    sim._build_sat()
    n = sim.grid_size
    r = sim.competition_radius
    for i, j in ((0, 0), (n - 1, n - 1), (n // 2, n // 3), (1, n - 2)):
        naive = sum(
            sim.grid[a * n + b]
            for a in range(max(0, i - r), min(n, i + r + 1))
            for b in range(max(0, j - r), min(n, j + r + 1))
        ) - sim.grid[i * n + j]
        assert sim._local_competition(i, j) == pytest.approx(
            naive * sim.competition_strength)


def test_forest_competition_radius_is_configurable():
    params = dict(SMALL_FOREST, competition_radius=5)
    assert ForestScalingSim(params, random.Random(1)).competition_radius == 5


def test_forest_asynchronous_updating_changes_the_outcome():
    """Reading competition off the grid mid-sweep is a different model."""
    sync = ForestScalingSim(dict(SMALL_FOREST, update_order="synchronous"),
                            random.Random(4)).run()
    async_ = ForestScalingSim(dict(SMALL_FOREST, update_order="asynchronous"),
                              random.Random(4)).run()
    assert sync != async_
    assert async_["num_trees"] > 0


def test_forest_direct_competition_matches_the_table_on_a_static_grid():
    sim = ForestScalingSim(SMALL_FOREST, random.Random(5))
    sim._build_sat()
    for i, j in ((0, 0), (3, 7), (sim.grid_size - 1, sim.grid_size - 1)):
        assert sim._direct_competition(sim.grid, i, j) == pytest.approx(
            sim._local_competition(i, j))


def test_forest_empty_grid_analyzes_cleanly():
    params = dict(SMALL_FOREST, initial_density=0.0, num_steps=1)
    out = ForestScalingSim(params, random.Random(1)).run()
    assert out["num_trees"] == 0
    assert out["mean_size"] == 0
    assert "size_distribution" not in out


# ── power-law fit ─────────────────────────────────────────────────

def test_power_law_fit_recovers_a_known_exponent():
    """Pareto samples with density ~ s^-2.5 log-bin to a line of slope ~ -1.5."""
    rng = random.Random(7)
    alpha = 2.5
    values = [rng.random() ** (-1 / (alpha - 1)) for _ in range(20_000)]
    fit = _power_law_fit(values, lo=1.0, bins=29)
    assert fit is not None
    assert fit["r_squared"] > 0.9
    assert -2.0 < fit["slope"] < -0.8


def test_power_law_fit_returns_none_when_degenerate():
    assert _power_law_fit([5.0] * 100, lo=5.0) is None
    assert _power_law_fit([1.0, 2.0], lo=0.0) is None


# ── fluctuating model ─────────────────────────────────────────────

def test_fluctuating_probabilities_sum_to_one():
    out = FluctuatingPopSim(SMALL_FLUCT, random.Random(1)).run()
    fp = out["fixation_probability"]
    assert sum(fp.values()) == pytest.approx(1.0)
    assert out["num_replicates"] == SMALL_FLUCT["num_replicates"]


def test_fluctuating_is_deterministic_under_a_seed():
    params = dict(SMALL_FLUCT, base_seed=99)
    assert FluctuatingPopSim(params).run() == FluctuatingPopSim(params).run()


def test_fluctuating_does_not_mutate_carrying_capacities():
    """Padding the capacity list must not reach back into the caller's params."""
    params = dict(SMALL_FLUCT, num_states=8, carrying_capacities=[10, 20, 30])
    sim = FluctuatingPopSim(params)
    assert params["carrying_capacities"] == [10, 20, 30]
    assert len(sim.carrying_capacities) == 8


def test_fluctuating_switch_probability_stays_a_probability():
    """A runaway switching_rate must not produce a probability above 1."""
    sim = FluctuatingPopSim(dict(SMALL_FLUCT, switching_rate=500.0))
    for state in range(sim.num_states):
        p = sim._switch_probability(state)
        assert 0.0 <= p <= 1.0


def test_fluctuating_edge_states_switch_more_slowly():
    sim = FluctuatingPopSim(SMALL_FLUCT)
    assert sim._switch_probability(0) < sim._switch_probability(sim.num_states // 2)


def test_fluctuating_saturating_semantics_are_indistinguishable():
    """A probability above 1 never announces itself — it just saturates.

    random() < 1.0 and random() < 2.0 are the same test, so the prototype's
    out-of-range rate behaves exactly like clamping.
    """
    params = dict(SMALL_FLUCT, switching_rate=2.0, base_seed=3)
    clamped = FluctuatingPopSim(dict(params, switch_semantics="clamped")).run()
    direct = FluctuatingPopSim(dict(params, switch_semantics="rate_direct")).run()
    exponential = FluctuatingPopSim(dict(params, switch_semantics="exponential")).run()
    assert clamped == direct
    assert exponential != direct


def test_fluctuating_rate_direct_can_exceed_one():
    sim = FluctuatingPopSim(dict(SMALL_FLUCT, switching_rate=4.0,
                                 switch_semantics="rate_direct"))
    assert sim._switch_probability(2) > 1.0


def test_derive_seed_avoids_the_overlap_that_addition_creates():
    """Neighbouring base seeds must not share replicate streams."""
    a = {derive_seed(1, rep) for rep in range(20)}
    b = {derive_seed(2, rep) for rep in range(20)}
    assert not (a & b)
    assert derive_seed(1, 0) == derive_seed(1, 0)


def test_fluctuating_neighbouring_seeds_give_independent_results():
    runs = [FluctuatingPopSim(dict(SMALL_FLUCT, base_seed=s)).run() for s in (1, 2, 3)]
    assert len({r["mean_fixation_time"] for r in runs}) == 3


def test_fluctuating_dt_scales_switching():
    slow = FluctuatingPopSim(dict(SMALL_FLUCT, dt=0.01))
    fast = FluctuatingPopSim(dict(SMALL_FLUCT, dt=1.0))
    assert slow._switch_probability(2) < fast._switch_probability(2)


# ── claims ────────────────────────────────────────────────────────

def test_claim_passes_and_records_evidence():
    claim = get_forest_claims()[1]
    passed, msg, _ = claim.test({"species_richness": 3})
    assert passed and claim.status == "passed"
    assert len(claim.evidence) == 1
    assert "3" in msg


def test_claim_fails_without_raising_on_missing_outcomes():
    """A missing outcome key is a clean failure, not an inconclusive test."""
    for claim in get_forest_claims() + get_fluctuating_claims():
        passed, msg, _ = claim.test({})
        assert not passed
        assert claim.status == "failed", claim.claim_id
        assert "Test error" not in msg


def test_claim_that_raises_is_inconclusive():
    claim = Claim(
        claim_id="boom", description="raises", model_type="forest",
        test_function=lambda o: 1 / 0,
    )
    passed, msg, _ = claim.test({})
    assert not passed
    assert claim.status == "inconclusive"
    assert "Test error" in msg


def test_fmt_falls_back_for_unformattable_values():
    assert fmt(0.5) == "0.500"
    assert fmt("N/A") == "N/A"
    assert fmt(None) == "None"


# ── agent ─────────────────────────────────────────────────────────

def test_agent_directed_action_follows_hypothesis():
    agent = AdaptiveAgent(exploration_rate=0.0, rng=random.Random(0))
    outcomes = {"size_distribution": {"slope": -0.4, "r_squared": 0.5},
                "species_richness": 3}
    failed = [c for c in get_forest_claims() if c.claim_id == "forest_power_law"]
    params = dict(SMALL_FOREST)
    new_params, _, step = agent.analyze(outcomes, failed, params, "forest")
    assert new_params["competition_strength"] > params["competition_strength"]
    assert "competition_strength" in step.parameters_changed
    assert step.parameters_changed["competition_strength"] == [
        params["competition_strength"], new_params["competition_strength"]]


def test_agent_exploration_rate_of_one_ignores_the_hypothesis():
    agent = AdaptiveAgent(exploration_rate=1.0, rng=random.Random(0))
    outcomes = {"size_distribution": {"slope": -0.4, "r_squared": 0.5}}
    failed = [c for c in get_forest_claims() if c.claim_id == "forest_power_law"]
    params = dict(SMALL_FOREST)
    new_params, _, _ = agent.analyze(outcomes, failed, params, "forest")
    assert new_params["competition_strength"] == params["competition_strength"]


def test_agent_chains_steps_to_their_parent():
    agent = AdaptiveAgent(rng=random.Random(0))
    failed = get_fluctuating_claims()
    params = dict(SMALL_FLUCT)
    for _ in range(3):
        params, _, _ = agent.analyze({"fixation_probability": {}}, failed,
                                     params, "fluctuating")
    ids = [s.step_id for s in agent.reasoning_chain]
    parents = [s.parent_step_id for s in agent.reasoning_chain]
    assert parents == [None] + ids[:-1]
    assert len(set(ids)) == 3


def test_agent_is_deterministic_under_a_seed():
    def run():
        agent = AdaptiveAgent(rng=random.Random(5))
        p, _, step = agent.analyze({"fixation_probability": {"slow_strain": 0.0}},
                                   get_fluctuating_claims(), dict(SMALL_FLUCT),
                                   "fluctuating")
        return p, step.action
    assert run() == run()


def test_agent_parameter_changes_are_json_native():
    agent = AdaptiveAgent(exploration_rate=1.0, rng=random.Random(2))
    params = dict(SMALL_FOREST)
    for _ in range(6):
        params, _, step = agent.analyze({"size_distribution": {"r_squared": 0.1}},
                                        get_forest_claims(), params, "forest")
        json.dumps(step.parameters_changed)  # raises on numpy-ish scalars
    json.dumps(params)


def test_agent_generates_a_follow_up_claim_on_a_clean_fit():
    agent = AdaptiveAgent(rng=random.Random(0))
    outcomes = {"size_distribution": {"slope": -0.9, "r_squared": 0.95}}
    _, new_claims, _ = agent.analyze(outcomes, [], dict(SMALL_FOREST), "forest")
    assert len(new_claims) == 1
    assert new_claims[0].model_type == "forest"


def test_agent_follow_up_claim_ids_are_unique():
    agent = AdaptiveAgent(rng=random.Random(0))
    outcomes = {"fixation_probability": {"slow_strain": 0.5}}
    ids = set()
    for _ in range(3):
        _, claims, _ = agent.analyze(outcomes, [], dict(SMALL_FLUCT), "fluctuating")
        ids.update(c.claim_id for c in claims)
    assert len(ids) == 3


# ── logger ────────────────────────────────────────────────────────

def _record(**overrides):
    base = dict(
        run_id="deadbeef", model_name="forest", parameters={"grid_size": 4},
        random_seed=1, timestamp=1.0, duration_seconds=0.5,
        outcomes={"num_trees": 2}, claim_results={"c": "passed"},
        reasoning_chain=[],
    )
    base.update(overrides)
    return SimulationRecord(**base)


def test_logger_writes_one_valid_json_line_per_run(tmp_path):
    log = tmp_path / "prov.jsonl"
    logger = ProvenanceLogger(log_file=str(log))
    logger.log_run(_record())
    logger.log_run(_record(run_id="cafebabe"))
    lines = log.read_text().strip().splitlines()
    assert len(lines) == 2
    assert validate_log(log)["ok"]
    assert logger.get_run_by_id("cafebabe") is not None
    assert logger.get_run_by_id("nope") is None


def test_logger_rejects_a_record_that_breaks_the_schema(tmp_path):
    logger = ProvenanceLogger(log_file=str(tmp_path / "prov.jsonl"))
    with pytest.raises(ValueError, match="adaptive_run.schema.json"):
        logger.log_run(_record(claim_results={"c": "probably"}))
    assert not (tmp_path / "prov.jsonl").exists()


def test_logger_summary_tracks_claims_and_models(tmp_path):
    logger = ProvenanceLogger(log_file=str(tmp_path / "p.jsonl"))
    logger.log_run(_record())
    logger.log_claim_result("c", {"status": "passed"})
    summary = logger.summary()
    assert summary["total_runs"] == 1
    assert summary["claims_tested"] == ["c"]
    assert summary["models_used"] == ["forest"]
    assert len(logger.get_chain_for_claim("c")) == 1


def test_record_coerces_non_finite_floats(tmp_path):
    payload = _record(outcomes={"slope": float("inf")}).to_dict()
    assert payload["outcomes"]["slope"] is None
    json.dumps(payload)


# ── runner ────────────────────────────────────────────────────────

def test_runner_rejects_unknown_model():
    with pytest.raises(ValueError, match="Unknown model type"):
        SimulationRunner("unicorn", ProvenanceLogger(log_file=None), AdaptiveAgent())


def test_runner_stops_early_when_every_claim_passes(tmp_path):
    result = run_experiment("fluctuating", iterations=5, seed=42,
                            log_file=str(tmp_path / "p.jsonl"),
                            params=SMALL_FLUCT, quiet=True)
    assert result["total_iterations"] == 1
    assert result["iteration_results"][0]["failed_claims"] == []


def test_shipped_forest_defaults_satisfy_the_shipped_claims(tmp_path):
    """The forest model, run as configured, produces the power law it claims.

    Smaller than the shipped grid so the test stays quick; the claim thresholds
    are the shipped ones.
    """
    result = run_experiment("forest", iterations=1, seed=42,
                            log_file=str(tmp_path / "p.jsonl"),
                            params={"grid_size": 40}, quiet=True)
    outcomes = result["iteration_results"][0]["outcomes"]
    assert outcomes["size_distribution"]["r_squared"] > 0.6
    assert outcomes["species_richness"] == 3
    assert result["iteration_results"][0]["failed_claims"] == []


def test_runner_adapts_when_a_claim_fails(tmp_path):
    """A failing claim must change parameters and leave a reasoning trail."""
    log = tmp_path / "p.jsonl"
    result = run_experiment("forest", iterations=3, seed=42, log_file=str(log),
                            params=dict(SMALL_FOREST, num_species=1), quiet=True)
    assert result["total_iterations"] == 3
    first, last = result["iteration_results"][0], result["iteration_results"][-1]
    assert "forest_species_coexistence" in first["failed_claims"]
    assert first["params"] != last["params"]
    records = [json.loads(line) for line in log.read_text().splitlines()]
    assert len(records) == 3
    assert all(r["reasoning_chain"] for r in records)
    assert records[0]["reasoning_chain"][0]["parameters_changed"]
    assert validate_log(log)["ok"]


def test_runner_records_the_seed_it_actually_used(tmp_path):
    log = tmp_path / "p.jsonl"
    run_experiment("forest", iterations=3, seed=100, log_file=str(log),
                   params=dict(SMALL_FOREST, num_species=1), quiet=True)
    records = [json.loads(line) for line in log.read_text().splitlines()]
    assert [r["random_seed"] for r in records] == [100, 101, 102]
    assert all(r["parameters"]["base_seed"] == r["random_seed"] for r in records)


def test_runner_run_ids_are_deterministic(tmp_path):
    def ids(seed):
        result = run_experiment("forest", iterations=2, seed=seed,
                                log_file=str(tmp_path / f"p{seed}.jsonl"),
                                params=dict(SMALL_FOREST, num_species=1), quiet=True)
        return [r["run_id"] for r in result["iteration_results"]]
    assert ids(11) == ids(11)
    assert ids(11) != ids(12)


def test_runner_reports_inconclusive_claims(tmp_path):
    logger = ProvenanceLogger(log_file=str(tmp_path / "p.jsonl"))
    runner = SimulationRunner("forest", logger, AdaptiveAgent(rng=random.Random(0)),
                              quiet=True)
    runner.register_claim(Claim(claim_id="boom", description="raises",
                                model_type="forest", test_function=lambda o: 1 / 0))
    result = runner.run_adaptive_loop(dict(SMALL_FOREST), max_iterations=1)
    assert result["iteration_results"][0]["claim_results"]["boom"]["status"] == "inconclusive"
    assert validate_log(tmp_path / "p.jsonl")["ok"]


def test_runner_ignores_claims_for_other_models(tmp_path):
    logger = ProvenanceLogger(log_file=str(tmp_path / "p.jsonl"))
    runner = SimulationRunner("forest", logger, AdaptiveAgent(), quiet=True)
    for claim in get_forest_claims() + get_fluctuating_claims():
        runner.register_claim(claim)
    result = runner.run_adaptive_loop(dict(SMALL_FOREST), max_iterations=1)
    tested = result["iteration_results"][0]["claim_results"]
    assert set(tested) == {c.claim_id for c in get_forest_claims()}


def test_registry_covers_every_default_and_claim_set():
    assert set(MODEL_REGISTRY) == set(DEFAULT_PARAMS) == set(CLAIM_REGISTRY)


def test_register_model_adds_a_model():
    class Toy:
        def __init__(self, params, rng=None):
            self.params = params

        def run(self):
            return {"answer": 42}

    register_model("toy", Toy)
    try:
        logger = ProvenanceLogger(log_file=None)
        runner = SimulationRunner("toy", logger, AdaptiveAgent(), quiet=True)
        result = runner.run_adaptive_loop({}, max_iterations=1)
        assert result["iteration_results"][0]["outcomes"] == {"answer": 42}
    finally:
        MODEL_REGISTRY.pop("toy")


# ── knowledge_dna bridge ──────────────────────────────────────────

def test_narrative_chain_traces_through_knowledge_dna(tmp_path):
    logger = ProvenanceLogger(log_file=str(tmp_path / "p.jsonl"))
    runner = SimulationRunner("forest", logger, AdaptiveAgent(rng=random.Random(0)),
                              quiet=True)
    for claim in get_forest_claims():
        runner.register_claim(claim)
    runner.run_adaptive_loop(dict(SMALL_FOREST, num_species=1), max_iterations=2)

    record = logger.records[0]
    chain = to_narrative_chain(record)
    assert len(chain) == len(record.reasoning_chain) + 1
    assert chain[-1].source == f"seed={record.random_seed}"

    trace = trace_narrative("forest power-law experiment", chain)
    assert trace.chain_length == len(chain)
    assert trace.provenance_intact


# ── cli ───────────────────────────────────────────────────────────

def test_cli_json_output(capsys, tmp_path):
    code = main(["--model", "fluctuating", "--iterations", "1", "--seed", "5",
                 "--log", str(tmp_path / "p.jsonl"), "--json"])
    assert code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["model_type"] == "fluctuating"
    assert payload["total_iterations"] == 1


def test_cli_validate_log_ok(capsys):
    assert main(["--validate-log", str(SAMPLE_LOGS[0])]) == 0
    assert "OK" in capsys.readouterr().out


def test_cli_validate_log_failure(capsys, tmp_path):
    bad = tmp_path / "bad.jsonl"
    bad.write_text('{"run_id": "x"}\n')
    assert main(["--validate-log", str(bad), "--json"]) == 1
    assert json.loads(capsys.readouterr().out)["ok"] is False
