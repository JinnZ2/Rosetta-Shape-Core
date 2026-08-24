# SPDX-License-Identifier: CC0-1.0
"""Membership probe — does the responder judge by geometry or by constraint set?

SHAPE_SPEC.md section 2 blocks one misread: matching geometries across
domains. This case set makes that misread measurable, by splitting the
failure into its two faces.

    trap_a   a real member that deviates hard from the ideal rendering.
             Judged by geometry it reads as a non-member. A wax comb cell
             is not a regular hexagon; a lung does not hit 2^(-1/3) at
             every junction; a person with situs inversus is a person.

    trap_b   a non-member whose GEOMETRY MATCHES the ideal and whose
             constraint set is absent. Judged by geometry it reads as a
             member. Machine-cut hexagon tiles are closer to the ideal
             than any comb, and nothing is being partitioned or minimised.

    control  unambiguous either way. Gates the run: if the controls are
             wrong the responder is not reading the questions and the trap
             scores mean nothing.

Both trap classes are failed by the SAME error — using the geometry as the
criterion. They are kept apart because the error points in opposite
directions and a responder can have one bias without the other.

THE CASE SET LEAKS ITS OWN ANSWERS, AND THE RUNNER WORKS AROUND IT
    Every trap_a is a member and every trap_b is not, so the id prefix
    predicts ground truth with no reading at all. ``blind_form()`` strips
    class, ground truth and constraint keys, replaces the id with a token
    derived from a seed, and shuffles. Scoring inverts the token from the
    same seed. A response set that was not produced from a blind form is
    scored, reported, and explicitly NOT called a measurement.

A CORRECT VERDICT WITH NO CONSTRAINT NAMED IS NOT A READ
    The probe exists to test whether the constraint set was consulted, not
    whether the label was guessed. Verdict accuracy and read accuracy are
    reported separately, and the gap between them is the guessing.

CONSTRAINTS (repo-wide, restated per file)
    - no "about the author" / working-style section, in this or any file
    - entries are markers to explore, not positions defended; the correct
      response to one is: test fit / extend / report break
    - no moral labels in data structures, no intent attribution
      (a responder is scored on what it named, never characterised)

Usage:
    python -m rosetta_shape_core.membership_probe --cases
    python -m rosetta_shape_core.membership_probe --blank --seed 7 > form.json
    python -m rosetta_shape_core.membership_probe --score answers.json --seed 7
    python -m rosetta_shape_core.membership_probe --selftest
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import sys
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional

ROOT = pathlib.Path(__file__).resolve().parents[2]
CASES_PATH = ROOT / "data" / "rosetta" / "membership_probe.json"

TRAP_A = "trap_a"
TRAP_B = "trap_b"
CONTROL = "control"
CLASSES = (TRAP_A, TRAP_B, CONTROL)

MEMBER = "member"
NOT_MEMBER = "not_member"
VERDICTS = (MEMBER, NOT_MEMBER)

PHYSICAL = "physical"
CONVENTIONAL = "conventional"

# What a failure in each trap class means. Same error, opposite direction.
GEOMETRY_STRICT = "geometry_strict"       # rejected a member for deviating from the ideal
GEOMETRY_PERMISSIVE = "geometry_permissive"  # accepted a non-member for matching it


@dataclass
class CaseScore:
    case_id: str
    case_class: str
    category_type: str
    verdict: str = ""
    expected: str = ""
    correct: bool = False
    keys_hit: List[str] = field(default_factory=list)
    keys_missed: List[str] = field(default_factory=list)
    read: bool = False          # correct AND named at least one constraint
    bias: str = ""              # set only on a trap failure

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class ProbeReport:
    blind: bool = False
    valid: bool = False
    invalid_reason: str = ""
    answered: int = 0
    controls: Dict[str, Any] = field(default_factory=dict)
    verdict_accuracy: Dict[str, Any] = field(default_factory=dict)
    read_accuracy: Dict[str, Any] = field(default_factory=dict)
    geometry_criterion: Dict[str, Any] = field(default_factory=dict)
    by_category_type: Dict[str, Any] = field(default_factory=dict)
    guessed: List[str] = field(default_factory=list)
    scores: List[Dict[str, Any]] = field(default_factory=list)
    reading: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


# ── cases ─────────────────────────────────────────────────────────

def load_cases(path: Optional[pathlib.Path] = None) -> List[Dict[str, Any]]:
    p = pathlib.Path(path) if path else CASES_PATH
    return json.loads(p.read_text(encoding="utf-8"))["cases"]


def validate_cases(cases: Optional[List[Dict[str, Any]]] = None) -> List[str]:
    cs = load_cases() if cases is None else cases
    errors: List[str] = []
    seen = set()
    for i, c in enumerate(cs):
        cid = c.get("id", f"[{i}]")
        if cid in seen:
            errors.append(f"{cid}: duplicate id")
        seen.add(cid)
        if c.get("class") not in CLASSES:
            errors.append(f"{cid}: class {c.get('class')!r} not one of {CLASSES}")
        if c.get("ground_truth") not in VERDICTS:
            errors.append(f"{cid}: ground_truth {c.get('ground_truth')!r} not one of {VERDICTS}")
        if c.get("class") == TRAP_A and c.get("ground_truth") != MEMBER:
            errors.append(f"{cid}: a trap_a is a real member by definition")
        if c.get("class") == TRAP_B and c.get("ground_truth") != NOT_MEMBER:
            errors.append(f"{cid}: a trap_b is a non-member by definition")
        keys = c.get("constraint_keys")
        if not keys:
            errors.append(f"{cid}: no constraint keys — nothing to score a read against")
            continue
        for k in keys:
            if not (isinstance(k, list) and len(k) == 2 and isinstance(k[1], list) and k[1]):
                errors.append(f"{cid}: malformed constraint key {k!r}")
    return errors


def token(case_id: str, seed: int) -> str:
    """Opaque handle for a case under one seed. The id prefix leaks the class."""
    return hashlib.sha256(f"{seed}:{case_id}".encode("utf-8")).hexdigest()[:8]


def blind_form(seed: int, cases: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    """The questions with the answers removed and the ordering broken.

    Strips class, ground_truth and constraint_keys, replaces the id, and
    orders by token — so neither the label nor the position carries the
    answer.
    """
    cs = load_cases() if cases is None else cases
    items = [{
        "case_token": token(c["id"], seed),
        "question": c["question"],
        "instance": c["instance"],
        "category": c["category"],
        "ideal_geometry": c.get("ideal_geometry", ""),
    } for c in cs]
    items.sort(key=lambda x: x["case_token"])
    return {
        "schema": "membership-probe/form v1",
        "seed": seed,
        "blind": True,
        "instructions": ("For each case answer with a verdict of 'member' or 'not_member' and a "
                         "reasoning string. The reasoning is scored for which constraints it "
                         "names, so a bare verdict scores as a guess rather than a read."),
        "responses": [{"case_token": i["case_token"], "verdict": "", "reasoning": ""} for i in items],
        "cases": items,
    }


# ── scoring ───────────────────────────────────────────────────────

def score_case(case: Dict[str, Any], verdict: str, reasoning: str) -> CaseScore:
    """One case. Substring match, case-insensitive, over the reasoning text."""
    text = (reasoning or "").lower()
    hit, missed = [], []
    for name, needles in case["constraint_keys"]:
        (hit if any(n.lower() in text for n in needles) else missed).append(name)
    correct = verdict == case["ground_truth"]
    s = CaseScore(
        case_id=case["id"], case_class=case["class"], category_type=case["category_type"],
        verdict=verdict, expected=case["ground_truth"], correct=correct,
        keys_hit=hit, keys_missed=missed, read=correct and bool(hit),
    )
    if not correct and case["class"] == TRAP_A:
        s.bias = GEOMETRY_STRICT
    elif not correct and case["class"] == TRAP_B:
        s.bias = GEOMETRY_PERMISSIVE
    return s


def _rate(n: int, d: int) -> Optional[float]:
    return None if not d else round(n / d, 3)


def run(responses: Dict[str, Dict[str, str]], *, blind: bool = False,
        cases: Optional[List[Dict[str, Any]]] = None) -> ProbeReport:
    """Score a set of responses keyed by case id. Controls gate the run."""
    cs = load_cases() if cases is None else cases
    by_id = {c["id"]: c for c in cs}

    scores = [score_case(by_id[cid], r.get("verdict", ""), r.get("reasoning", ""))
              for cid, r in responses.items() if cid in by_id]

    controls = [s for s in scores if s.case_class == CONTROL]
    control_wrong = [s.case_id for s in controls if not s.correct]
    n_controls = len([c for c in cs if c["class"] == CONTROL])

    report = ProbeReport(blind=blind, answered=len(scores),
                         scores=[s.to_dict() for s in scores])
    report.controls = {
        "answered": len(controls), "expected": n_controls,
        "wrong": control_wrong,
        "gate": "PASS" if (len(controls) == n_controls and not control_wrong) else "FAIL",
    }
    if report.controls["gate"] != "PASS":
        report.valid = False
        report.invalid_reason = (
            "the controls did not pass, so the responder is not reading the questions and the "
            "trap scores mean nothing. Controls gate the run." if control_wrong else
            f"only {len(controls)} of {n_controls} controls answered — the gate cannot run")
        report.reading = report.invalid_reason
        return report

    report.valid = True
    traps = [s for s in scores if s.case_class in (TRAP_A, TRAP_B)]
    correct = [s for s in scores if s.correct]
    report.verdict_accuracy = {
        "overall": _rate(len(correct), len(scores)),
        TRAP_A: _rate(len([s for s in scores if s.case_class == TRAP_A and s.correct]),
                      len([s for s in scores if s.case_class == TRAP_A])),
        TRAP_B: _rate(len([s for s in scores if s.case_class == TRAP_B and s.correct]),
                      len([s for s in scores if s.case_class == TRAP_B])),
    }
    report.read_accuracy = {
        "overall": _rate(len([s for s in scores if s.read]), len(scores)),
        "of_correct": _rate(len([s for s in correct if s.read]), len(correct)),
        "note": "correct AND named at least one constraint. The gap is guessing.",
    }
    report.guessed = [s.case_id for s in correct if not s.keys_hit]

    strict = [s.case_id for s in traps if s.bias == GEOMETRY_STRICT]
    permissive = [s.case_id for s in traps if s.bias == GEOMETRY_PERMISSIVE]
    report.geometry_criterion = {
        "rate": _rate(len(strict) + len(permissive), len(traps)),
        GEOMETRY_STRICT: {"cases": strict,
                          "means": "a real member rejected for deviating from the ideal rendering"},
        GEOMETRY_PERMISSIVE: {"cases": permissive,
                              "means": "a non-member accepted for matching the ideal rendering"},
        "note": "both are the same error — geometry used as the criterion — pointing opposite ways",
    }
    for ct in (PHYSICAL, CONVENTIONAL):
        sub = [s for s in scores if s.category_type == ct]
        report.by_category_type[ct] = {
            "n": len(sub), "verdict": _rate(len([s for s in sub if s.correct]), len(sub)),
            "read": _rate(len([s for s in sub if s.read]), len(sub)),
        }

    if not blind:
        report.reading = ("scored, but NOT a measurement: the responses were not produced from a "
                          "blind form, so the responder could see the class, the ground truth or "
                          "the constraint keys. Read this as a demonstration of the scorer.")
    elif report.guessed:
        report.reading = (f"{len(report.guessed)} correct verdict(s) named no constraint at all. "
                          f"The probe tests whether the constraint set was consulted, not whether "
                          f"the label was guessed.")
    else:
        report.reading = "controls passed and every correct verdict named at least one constraint."
    return report


def score_blind(form_responses: List[Dict[str, str]], seed: int,
                cases: Optional[List[Dict[str, Any]]] = None) -> ProbeReport:
    """Invert the tokens from the seed, then score."""
    cs = load_cases() if cases is None else cases
    by_token = {token(c["id"], seed): c["id"] for c in cs}
    responses, unknown = {}, []
    for r in form_responses:
        cid = by_token.get(r.get("case_token", ""))
        if cid is None:
            unknown.append(r.get("case_token", ""))
            continue
        responses[cid] = r
    report = run(responses, blind=True, cases=cs)
    if unknown:
        report.invalid_reason = (f"{len(unknown)} response token(s) do not invert under seed "
                                 f"{seed} — wrong seed, or the form was edited")
        report.valid = False
        report.reading = report.invalid_reason
    return report


def format_report(r: ProbeReport) -> str:
    lines = ["", "  MEMBERSHIP PROBE", ""]
    lines.append(f"  answered       {r.answered}")
    lines.append(f"  control gate   {r.controls.get('gate')}"
                 + (f"  wrong: {', '.join(r.controls['wrong'])}" if r.controls.get("wrong") else ""))
    if not r.valid:
        lines += ["", f"  RUN INVALID — {r.invalid_reason}", ""]
        return "\n".join(lines)
    lines.append(f"  blind          {r.blind}")
    lines.append("")
    lines.append(f"  verdict        overall {r.verdict_accuracy['overall']}   "
                 f"trap_a {r.verdict_accuracy[TRAP_A]}   trap_b {r.verdict_accuracy[TRAP_B]}")
    lines.append(f"  read           overall {r.read_accuracy['overall']}   "
                 f"of correct {r.read_accuracy['of_correct']}")
    if r.guessed:
        lines.append(f"  guessed        {', '.join(r.guessed)} — correct, named no constraint")
    lines.append("")
    g = r.geometry_criterion
    lines.append(f"  geometry used as the criterion: {g['rate']} of trap cases")
    for key in (GEOMETRY_STRICT, GEOMETRY_PERMISSIVE):
        cases = g[key]["cases"]
        lines.append(f"      {key:20s} {', '.join(cases) if cases else '(none)'}")
        lines.append(f"      {'':20s} {g[key]['means']}")
    lines.append("")
    for ct, v in r.by_category_type.items():
        lines.append(f"  {ct:14s} n={v['n']}  verdict {v['verdict']}  read {v['read']}")
    lines.append("")
    lines.append(f"  {r.reading}")
    lines.append("")
    return "\n".join(lines)


# ── selftest ──────────────────────────────────────────────────────

def _answers(cases: List[Dict[str, Any]], pick) -> Dict[str, Dict[str, str]]:
    return {c["id"]: pick(c) for c in cases}


def selftest() -> List[str]:
    fails = []
    cases = load_cases()

    if validate_cases(cases):
        fails.append(f"shipped cases do not validate: {validate_cases(cases)[0]}")
    if len(cases) < 16:
        fails.append("case set is short")

    # The leak the runner exists to work around.
    if not all(c["ground_truth"] == MEMBER for c in cases if c["class"] == TRAP_A):
        fails.append("trap_a is no longer uniformly member — the blinding rationale changed")
    form = blind_form(7, cases)
    blob = json.dumps(form)
    for leaked in ('"class"', "ground_truth", "constraint_keys", "trap_a", "trap_b"):
        if leaked in blob:
            fails.append(f"the blind form leaks {leaked}")
    for c in cases:
        if c["id"] in blob:
            fails.append(f"the blind form leaks the case id {c['id']}")
            break
    if token("A01", 7) == token("A01", 8):
        fails.append("tokens do not depend on the seed")
    if len({i["case_token"] for i in form["cases"]}) != len(cases):
        fails.append("token collision in the blind form")

    # A perfect reader.
    perfect = _answers(cases, lambda c: {
        "verdict": c["ground_truth"],
        "reasoning": " ".join(k[1][0] for k in c["constraint_keys"])})
    r = run(perfect, blind=True, cases=cases)
    if not r.valid or r.verdict_accuracy["overall"] != 1.0:
        fails.append("a perfect reader did not score 1.0")
    if r.read_accuracy["of_correct"] != 1.0:
        fails.append("a perfect reader was not credited with reads")
    if r.geometry_criterion["rate"] != 0.0:
        fails.append("a perfect reader was charged with using geometry")

    # A responder judging purely by geometry: rejects trap_a, accepts trap_b.
    def by_geometry(c):
        if c["class"] == TRAP_A:
            return {"verdict": NOT_MEMBER, "reasoning": "does not match the ideal"}
        if c["class"] == TRAP_B:
            return {"verdict": MEMBER, "reasoning": "matches the ideal"}
        return {"verdict": c["ground_truth"], "reasoning": c["constraint_keys"][0][1][0]}
    g = run(_answers(cases, by_geometry), blind=True, cases=cases)
    if not g.valid:
        fails.append("the geometry-judging responder failed the control gate it should pass")
    if g.geometry_criterion["rate"] != 1.0:
        fails.append("a purely geometric responder was not charged for every trap")
    if not g.geometry_criterion[GEOMETRY_STRICT]["cases"]:
        fails.append("trap_a failures not reported as geometry-strict")
    if not g.geometry_criterion[GEOMETRY_PERMISSIVE]["cases"]:
        fails.append("trap_b failures not reported as geometry-permissive")

    # Right answers, no constraint named: a guess, not a read.
    lucky = _answers(cases, lambda c: {"verdict": c["ground_truth"], "reasoning": "yes"})
    lk = run(lucky, blind=True, cases=cases)
    if lk.verdict_accuracy["overall"] != 1.0:
        fails.append("the guesser did not score full verdict accuracy")
    if lk.read_accuracy["of_correct"] not in (0.0, None):
        fails.append("a guesser was credited with reads")
    if len(lk.guessed) != len(cases):
        fails.append("guessed cases not reported")

    # Controls gate the run.
    def bad_control(c):
        if c["class"] == CONTROL:
            return {"verdict": NOT_MEMBER if c["ground_truth"] == MEMBER else MEMBER,
                    "reasoning": "x"}
        return {"verdict": c["ground_truth"], "reasoning": c["constraint_keys"][0][1][0]}
    bc = run(_answers(cases, bad_control), blind=True, cases=cases)
    if bc.valid or not bc.controls["wrong"]:
        fails.append("a run with wrong controls was reported valid")
    if bc.verdict_accuracy:
        fails.append("trap scores were reported despite a failed control gate")
    partial = run({c["id"]: {"verdict": c["ground_truth"], "reasoning": "x"}
                   for c in cases if c["class"] != CONTROL}, blind=True, cases=cases)
    if partial.valid:
        fails.append("a run with no controls answered was reported valid")

    # Not blind is scored and is not a measurement.
    nb = run(perfect, blind=False, cases=cases)
    if not nb.valid or "NOT a measurement" not in nb.reading:
        fails.append("a non-blind run was reported as a measurement")

    # Token inversion.
    filled = [{"case_token": token(c["id"], 11), "verdict": c["ground_truth"],
               "reasoning": c["constraint_keys"][0][1][0]} for c in cases]
    sb = score_blind(filled, 11, cases)
    if not sb.valid or sb.answered != len(cases):
        fails.append("blind scoring did not invert the tokens")
    wrong_seed = score_blind(filled, 12, cases)
    if wrong_seed.valid:
        fails.append("a wrong seed still scored")

    # A malformed case set is caught.
    if not validate_cases([{**cases[0], "class": TRAP_B}]):
        fails.append("a trap_b whose ground truth is member was accepted")
    return fails


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="membership probe — geometry or constraint set?")
    ap.add_argument("--cases", action="store_true", help="list the case set")
    ap.add_argument("--validate", action="store_true")
    ap.add_argument("--blank", action="store_true", help="emit a blind response form")
    ap.add_argument("--score", help="a filled response file")
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args(argv)

    if args.selftest:
        f = selftest()
        for line in f:
            print(f"FAIL  {line}")
        print("membership_probe: OK" if not f else f"membership_probe: {len(f)} FAILED")
        return 1 if f else 0

    if args.validate:
        errors = validate_cases()
        if args.json:
            print(json.dumps({"errors": errors, "valid": not errors}, indent=2))
        else:
            for e in errors:
                print(f"  ✗  {e}")
            print("cases: VALID" if not errors else f"cases: {len(errors)} error(s)")
        return 1 if errors else 0

    if args.blank:
        print(json.dumps(blind_form(args.seed), indent=2, ensure_ascii=False))
        return 0

    if args.score:
        payload = json.loads(pathlib.Path(args.score).read_text(encoding="utf-8"))
        if isinstance(payload, dict) and payload.get("responses"):
            rows = payload["responses"]
            seed = payload.get("seed", args.seed)
            if rows and "case_token" in rows[0]:
                report = score_blind(rows, seed)
            else:
                report = run({r["case_id"]: r for r in rows},
                             blind=bool(payload.get("blind")))
        else:
            report = run(payload, blind=False)
        print(json.dumps(report.to_dict(), indent=2) if args.json else format_report(report))
        return 0 if report.valid else 1

    cases = load_cases()
    if args.json:
        print(json.dumps(cases, indent=2, ensure_ascii=False))
    else:
        print(f"\n  MEMBERSHIP PROBE — {len(cases)} cases\n")
        for c in cases:
            print(f"  {c['id']}  [{c['class']:7s}] [{c['category_type']:12s}] "
                  f"{c['ground_truth']:10s} {c['category']}")
            print(f"        {c['instance'][:96]}")
        print("\n  trap_a: a real member that deviates from the ideal.")
        print("  trap_b: a non-member whose geometry matches and whose constraint set is absent.")
        print("  Both are failed by the same error, pointing opposite ways.\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
