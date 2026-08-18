"""Tests for the Discrepancy Explorer."""
import json
import random

import pytest

from rosetta_shape_core.adaptive_sim import (
    CLAIM_REGISTRY,
    DEFAULT_PARAMS,
    MODEL_REGISTRY,
    Claim,
    ProvenanceLogger,
    validate_log,
)
from rosetta_shape_core.discrepancy import (
    CLAIM_MARGIN,
    DISCREPANCIES,
    Discrepancy,
    Option,
    _judge,
    _separated,
    claim_margin,
    dig,
    explore,
    format_report,
    main,
)

TOY = "toy_for_tests"


class ToyModel:
    """score = level + gaussian noise. Deterministic when noise is zero."""

    def __init__(self, params, rng=None):
        self.level = float(params.get("level", 0.0))
        self.noise = float(params.get("noise", 0.0))
        self.rng = rng or random.Random(params.get("base_seed", 0))

    def run(self):
        return {"score": self.level + self.rng.gauss(0, self.noise),
                "nested": {"depth": self.level}}


@pytest.fixture
def toy_model():
    """Register a toy model whose claim passes when score clears 0.5."""
    MODEL_REGISTRY[TOY] = ToyModel
    DEFAULT_PARAMS[TOY] = {"level": 0.0, "noise": 0.0}
    CLAIM_REGISTRY[TOY] = lambda: [Claim(
        claim_id="toy_high", description="score clears 0.5", model_type=TOY,
        test_function=lambda o: (o.get("score", 0) > 0.5, f"score={o.get('score')}", {}),
    )]
    yield
    for registry in (MODEL_REGISTRY, DEFAULT_PARAMS, CLAIM_REGISTRY):
        registry.pop(TOY, None)


def toy_discrepancy(options, metric="score", prefer="max", **kwargs):
    return Discrepancy(id="toy_q", question="Which level?", model=TOY,
                       options=options, metric=metric, prefer=prefer, **kwargs)


# ── registered discrepancies ──────────────────────────────────────

def test_registered_discrepancies_are_well_formed():
    assert DISCREPANCIES
    for did, d in DISCREPANCIES.items():
        assert d.id == did
        assert d.model in MODEL_REGISTRY, did
        assert len(d.options) >= 2, did
        labels = [o.label for o in d.options]
        assert len(set(labels)) == len(labels), did
        assert d.question.endswith("?"), did
        assert d.origin, f"{did} does not say where the ambiguity came from"
        assert d.prefer in {"max", "min", "distinguish"}, did


def test_discrepancy_option_lookup():
    d = DISCREPANCIES["forest_update_order"]
    assert d.option("synchronous").params == {"update_order": "synchronous"}
    with pytest.raises(KeyError):
        d.option("sideways")


# ── metric plumbing ───────────────────────────────────────────────

def test_dig_reads_dotted_paths():
    outcomes = {"a": {"b": 2.5}, "flag": True, "text": "x"}
    assert dig(outcomes, "a.b") == 2.5
    assert dig(outcomes, "a.missing") is None
    assert dig(outcomes, "") is None
    assert dig(outcomes, "flag") is None, "booleans are not measurements"
    assert dig(outcomes, "text") is None


# ── judging ───────────────────────────────────────────────────────

def _opt(label, rate, mean, std, n=5, tests=10):
    return {"label": label, "description": "", "params": {},
            "claim_pass_rate": rate, "claim_tests": tests,
            "claims": {}, "run_ids": [],
            "metric": {"name": "m", "n": n, "mean": mean, "std": std, "values": []}}


def test_claim_margin_scales_with_the_number_of_tests():
    assert claim_margin(_opt("a", 1, 1, 0, tests=4)) > CLAIM_MARGIN
    assert claim_margin(_opt("a", 1, 1, 0, tests=1000)) == CLAIM_MARGIN


def test_a_single_claim_test_does_not_decide_anything():
    """80% vs 70% over ten tests is one run going the other way."""
    verdict = _judge([_opt("a", 0.8, 1.0, 0.5), _opt("b", 0.7, 0.9, 0.5)], "max")
    assert verdict["verdict"] == "tie"


def test_a_wide_claim_gap_resolves():
    verdict = _judge([_opt("a", 1.0, 1.0, 0.0), _opt("b", 0.0, 1.0, 0.0)], "max")
    assert verdict["verdict"] == "resolved"
    assert verdict["winner"] == "a"


def test_metric_breaks_a_claim_tie():
    verdict = _judge([_opt("a", 1.0, 10.0, 0.1), _opt("b", 1.0, 1.0, 0.1)], "max")
    assert verdict["verdict"] == "resolved"
    assert verdict["winner"] == "a"


def test_prefer_min_inverts_the_ranking():
    verdict = _judge([_opt("a", 1.0, 10.0, 0.1), _opt("b", 1.0, 1.0, 0.1)], "min")
    assert verdict["winner"] == "b"


def test_no_option_satisfying_claims_is_reported_as_such():
    verdict = _judge([_opt("a", 0.0, 1.0, 0.0), _opt("b", 0.0, 2.0, 0.0)], "max")
    assert verdict["verdict"] == "no_option_satisfies_claims"
    assert verdict["winner"] is None


def test_tie_still_names_options_it_ruled_out():
    verdict = _judge([_opt("a", 1.0, 1.0, 0.01), _opt("b", 1.0, 1.0, 0.01),
                      _opt("c", 1.0, 0.1, 0.01)], "max")
    assert verdict["verdict"] == "tie"
    assert "c" in verdict["explanation"]


def test_distinguish_mode_never_crowns_a_winner():
    verdict = _judge([_opt("a", 1.0, 10.0, 0.1), _opt("b", 1.0, 1.0, 0.1)], "distinguish")
    assert verdict["verdict"] == "separated"
    assert verdict["winner"] is None


def test_distinguish_mode_reports_indistinguishable():
    verdict = _judge([_opt("a", 1.0, 1.0, 0.1), _opt("b", 1.0, 1.0, 0.1)], "distinguish")
    assert verdict["verdict"] == "indistinguishable"


def test_separation_sharpens_as_seeds_are_added():
    """The rule must use the error on the mean, or more seeds would never help."""
    few = (_opt("a", 1.0, 1.00, 0.2, n=3), _opt("b", 1.0, 1.15, 0.2, n=3))
    many = (_opt("a", 1.0, 1.00, 0.2, n=400), _opt("b", 1.0, 1.15, 0.2, n=400))
    assert not _separated(*few)
    assert _separated(*many)


def test_separation_ignores_a_difference_too_small_to_matter():
    """Beating the noise is not enough — the gap has to be worth something."""
    assert not _separated(_opt("a", 1.0, 1.0, 1e-9, n=400),
                          _opt("b", 1.0, 1.0001, 1e-9, n=400))


def test_single_seed_cannot_separate_anything():
    assert not _separated(_opt("a", 1.0, 1.0, 0.0, n=1), _opt("b", 1.0, 5.0, 0.0, n=1))


# ── exploring ─────────────────────────────────────────────────────

def test_explore_resolves_a_clear_winner(toy_model):
    report = explore(toy_discrepancy([
        Option("high", "clears the bar", {"level": 0.9}),
        Option("low", "does not", {"level": 0.1}),
    ]), seeds=(1, 2, 3))
    assert report["verdict"] == "resolved"
    assert report["winner"] == "high"
    assert report["ranking"] == ["high", "low"]
    assert report["options"][0]["claim_pass_rate"] == 1.0
    assert report["options"][1]["claim_pass_rate"] == 0.0


def test_explore_calls_identical_options_a_tie(toy_model):
    report = explore(toy_discrepancy([
        Option("a", "same", {"level": 0.9}),
        Option("b", "same", {"level": 0.9}),
    ]), seeds=(1, 2, 3))
    assert report["verdict"] == "tie"
    assert report["winner"] is None


def test_explore_reports_when_nothing_satisfies_the_claims(toy_model):
    report = explore(toy_discrepancy([
        Option("a", "low", {"level": 0.1}),
        Option("b", "lower", {"level": 0.0}),
    ]), seeds=(1, 2))
    assert report["verdict"] == "no_option_satisfies_claims"


def test_explore_records_every_arm_with_its_option(toy_model, tmp_path):
    log = tmp_path / "sweep.jsonl"
    logger = ProvenanceLogger(log_file=str(log))
    explore(toy_discrepancy([
        Option("high", "", {"level": 0.9}),
        Option("low", "", {"level": 0.1}),
    ]), seeds=(1, 2, 3), logger=logger)

    records = [json.loads(line) for line in log.read_text().splitlines()]
    assert len(records) == 6
    assert validate_log(log)["ok"]
    for record in records:
        assert record["experiment"]["discrepancy_id"] == "toy_q"
        assert record["experiment"]["option_label"] in {"high", "low"}
    assert {r["experiment"]["option_index"] for r in records} == {0, 1}
    assert len({r["run_id"] for r in records}) == 6


def test_explore_arm_ids_are_reproducible(toy_model):
    d = toy_discrepancy([Option("a", "", {"level": 0.9}), Option("b", "", {"level": 0.2})])
    first = explore(d, seeds=(1, 2))
    second = explore(d, seeds=(1, 2))
    assert [o["run_ids"] for o in first["options"]] == [o["run_ids"] for o in second["options"]]


def test_explore_reads_a_nested_metric(toy_model):
    report = explore(toy_discrepancy([
        Option("a", "", {"level": 0.9}), Option("b", "", {"level": 0.6}),
    ], metric="nested.depth"), seeds=(1, 2))
    assert report["options"][0]["metric"]["mean"] == pytest.approx(0.9)


def test_explore_survives_a_metric_that_is_never_reported(toy_model):
    report = explore(toy_discrepancy([
        Option("a", "", {"level": 0.9}), Option("b", "", {"level": 0.9}),
    ], metric="not_a_key"), seeds=(1, 2))
    assert report["options"][0]["metric"]["mean"] is None
    assert report["verdict"] in {"tie", "resolved"}


def test_explore_rejects_an_unknown_model():
    d = Discrepancy(id="x", question="?", model="nonesuch", options=[Option("a", "")])
    with pytest.raises(ValueError, match="Unknown model"):
        explore(d)


def test_format_report_mentions_the_verdict(toy_model):
    report = explore(toy_discrepancy([
        Option("high", "clears", {"level": 0.9}),
        Option("low", "does not", {"level": 0.1}),
    ]), seeds=(1, 2))
    text = format_report(report)
    assert "high" in text and "RESOLVED" in text
    assert report["question"] in text


# ── cli ───────────────────────────────────────────────────────────

def test_cli_lists_discrepancies(capsys):
    assert main(["--list"]) == 0
    out = capsys.readouterr().out
    for did in DISCREPANCIES:
        assert did in out


def test_cli_lists_as_json(capsys):
    assert main(["--list", "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert {d["id"] for d in payload} == set(DISCREPANCIES)


def test_cli_defaults_to_listing(capsys):
    assert main([]) == 0
    assert "forest_update_order" in capsys.readouterr().out


def test_cli_rejects_an_unknown_id(capsys):
    assert main(["--id", "nope"]) == 2
    assert "Unknown discrepancy" in capsys.readouterr().err


def test_cli_runs_one_discrepancy(capsys, tmp_path, toy_model):
    DISCREPANCIES["toy_q"] = toy_discrepancy([
        Option("high", "", {"level": 0.9}), Option("low", "", {"level": 0.1}),
    ])
    try:
        code = main(["--id", "toy_q", "--seeds", "2", "--json",
                     "--log", str(tmp_path / "s.jsonl")])
        assert code == 0
        payload = json.loads(capsys.readouterr().out)
        assert payload["winner"] == "high"
        assert validate_log(tmp_path / "s.jsonl")["ok"]
    finally:
        DISCREPANCIES.pop("toy_q")
