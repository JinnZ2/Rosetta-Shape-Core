# SPDX-License-Identifier: CC0-1.0
"""T4 — scope: where an entry produces, and where it stops.

There is no literal / stand-in flag on a shape token, and there is not
going to be one. Shapes self-report under use:

    reason from the named shape's formal properties, then observe
      holds                 -> the name is adequate at this scope
      fails everywhere      -> placeholder; the name carries no structural claim
      fails past a scale    -> the shape is real and its boundary is now measured

The falsification does double duty: it kills the prediction and it grades
the token. No annotation is required for that to work — the artifact is
testable as it stands.

WHAT A SHAPE TOKEN IS HERE
    A token in an entry names a GEOMETRY — the readout — and this module
    grades it by reasoning from that geometry's formal properties. Under
    SHAPE_SPEC.md section 1 the shape is the constraint set the geometry is
    a solution to, which lives in the entry's forcing terms, not in the
    token. The two are graded separately on purpose: a token can be adequate
    while the constraint set is unnamed, and a constraint set can license a
    transfer with no token at all.

PRECEDENT
    Algebra is valid over discrete relations and closed forms; its boundary
    is continuous change. Calculus is valid over smooth differentiable
    behaviour; its boundary is discontinuity, the discrete, the chaotic.
    Each tool is valid inside, silent outside, and the boundary is a
    measured thing rather than a defect. Shape tokens get the same
    treatment: carried while they produce, boundary read where they stop,
    no claim past it. The only difference is that these boundaries are not
    catalogued yet, which is a documentation gap and not a difference in kind.

REPO AUDIT CRITERION
    Does the entry report where it STOPS? An entry that matches everywhere
    and never fails is the flag.

    That criterion has a soft floor, and this module now reports it: a stop
    can be satisfied by ASSERTING one. A stop nobody has hit is a reasoned
    claim, and a corpus of reasoned claims about where things stop is the
    same shape as a frame that never fails — the thing the repo exists to
    catch. So each stop carries a status:

      ASSERTED   written down, never tested. Unaudited, not wrong.
      CITED      the boundary is established in the source system's own
                 literature and the stop names that source. Real evidence,
                 about the SOURCE — nobody has yet carried a move to it and
                 watched the move stop. Two different claims, so two states.
      MEASURED   something was carried to it and it stopped there —
                 a transfer that broke at it, or an observation that tested it
      CONTESTED  something produced straight past it. The stop is wrong,
                 or its condition was never met.

    Evidence comes from data/rosetta/transfers.jsonl (entry-level: a move
    was ported and broke) and from observations carrying a ``stop`` field.
    The ratio is reported and not enforced: asserting a stop is how an entry
    starts, and measuring it is what the corpus is for.

CONSTRAINTS (repo-wide, restated per file)
    - no "about the author" / working-style section, in this or any file
    - entries are markers to explore, not positions defended; the correct
      response to one is: test fit / extend / report break
    - no moral labels in data structures, no intent attribution

Usage:
    python -m rosetta_shape_core.scope --shape HEXAGON
    python -m rosetta_shape_core.scope --classify HEXAGON
    python -m rosetta_shape_core.scope --audit
    python -m rosetta_shape_core.scope --selftest
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional

from rosetta_shape_core.entry import Entry, load_entries

ROOT = pathlib.Path(__file__).resolve().parents[2]
OBSERVATIONS_DIR = ROOT / "data" / "rosetta"
OBSERVATIONS_PATH = OBSERVATIONS_DIR / "observations.jsonl"


def observation_files() -> List[pathlib.Path]:
    if not OBSERVATIONS_DIR.exists():
        return []
    return sorted(OBSERVATIONS_DIR.glob("observations*.jsonl"))

ASSERTED = "ASSERTED"
CITED = "CITED"
MEASURED = "MEASURED"
CONTESTED = "CONTESTED"

NO_DATA = "NO_DATA"
ADEQUATE = "ADEQUATE"
PLACEHOLDER = "PLACEHOLDER"
BOUNDED = "BOUNDED"
INDETERMINATE = "INDETERMINATE"

# Formal properties a reader is entitled to reason from once a token is used.
# This table is what makes a shape token falsifiable: the predictions come
# from here, not from the entry's prose.
#
# Provenance: PUBLIC throughout — these are established results (Euler's
# formula, the Platonic duals, the equal-area tiling minimum), attributable
# to no party here. Observations carry their own provenance per record.
SHAPE_PROPERTIES: Dict[str, Dict[str, Any]] = {
    "TRIANGLE": {"kind": "polygon", "vertices": 3, "edges": 3, "interior_angle": 60.0, "tiles_plane": True},
    "SQUARE": {"kind": "polygon", "vertices": 4, "edges": 4, "interior_angle": 90.0, "tiles_plane": True},
    "PENTAGON": {"kind": "polygon", "vertices": 5, "edges": 5, "interior_angle": 108.0, "tiles_plane": False},
    "HEXAGON": {
        "kind": "polygon",
        "vertices": 6,
        "edges": 6,
        "interior_angle": 120.0,
        "tiles_plane": True,
        "minimal_boundary_per_area_among_equal_area_tilings": True,
    },
    "TETRAHEDRON": {"kind": "polyhedron", "vertices": 4, "edges": 6, "faces": 4, "schlafli": "{3,3}", "dual": "TETRAHEDRON"},
    "CUBE": {"kind": "polyhedron", "vertices": 8, "edges": 12, "faces": 6, "schlafli": "{4,3}", "dual": "OCTAHEDRON", "fills_space": True},
    "OCTAHEDRON": {"kind": "polyhedron", "vertices": 6, "edges": 12, "faces": 8, "schlafli": "{3,4}", "dual": "CUBE"},
    "DODECAHEDRON": {"kind": "polyhedron", "vertices": 20, "edges": 30, "faces": 12, "schlafli": "{5,3}", "dual": "ICOSAHEDRON"},
    "ICOSAHEDRON": {"kind": "polyhedron", "vertices": 12, "edges": 30, "faces": 20, "schlafli": "{3,5}", "dual": "DODECAHEDRON"},
    "SPHERE": {"kind": "surface", "euler_characteristic": 2, "curvature": "constant positive", "minimal_area_per_volume": True},
    "HELIX": {"kind": "curve", "curvature": "constant", "torsion": "constant", "chiral": True},
    "CATENARY": {"kind": "curve", "property": "hangs under uniform self weight in pure tension"},
}


@dataclass
class Observation:
    """One prediction from a shape's formal properties, and what happened.

    ``scale`` is any ordered control parameter — a length, a ratio, a
    supersaturation. It is optional: where the failure is by condition
    rather than by scale, leave it out and name the condition in
    ``condition``.

    ``holds`` may be None, meaning the test is STATED AND NOT RUN. A
    predicted test is not a failed one, and flattening the two would let an
    unrun prediction read as evidence. Pending observations are counted and
    excluded from the verdict.
    """

    shape_token: str = ""
    prop: str = ""
    holds: Optional[bool] = None
    scale: Optional[float] = None
    condition: str = ""
    entry: str = ""
    stop: str = ""
    note: str = ""
    provenance: Dict[str, Any] = field(default_factory=dict)

    @property
    def label(self) -> str:
        if self.condition:
            return self.condition
        if self.scale is not None:
            return f"scale={self.scale:g}"
        return self.prop

    def to_dict(self) -> dict:
        return {k: v for k, v in asdict(self).items()
                if v is not None and v != "" and v != {}}

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Observation":
        return cls(
            shape_token=d.get("shape_token", ""),
            prop=d.get("prop", d.get("property", "")),
            holds=d["holds"] if isinstance(d.get("holds"), bool) else None,
            scale=d.get("scale"),
            condition=d.get("condition", ""),
            entry=d.get("entry", ""),
            stop=d.get("stop", ""),
            note=d.get("note", ""),
            provenance=dict(d.get("provenance", {})),
        )


@dataclass
class ScopeVerdict:
    """What the observations say about the token — not about the author of it."""

    shape_token: str
    status: str
    holds: int = 0
    fails: int = 0
    boundary_scale: Optional[float] = None
    direction: str = ""
    failing_conditions: List[str] = field(default_factory=list)
    reading: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


def properties(token: str) -> Dict[str, Any]:
    """Formal properties of a named shape. Empty dict = no table entry.

    An empty return is itself informative: nothing can be predicted from the
    token, so it cannot yet be graded by use.
    """
    return dict(SHAPE_PROPERTIES.get((token or "").upper(), {}))


def classify(observations: List[Observation]) -> ScopeVerdict:
    """Grade a token from its observations. This is the whole of T4."""
    obs = list(observations)
    token = obs[0].shape_token if obs else ""
    if not obs:
        return ScopeVerdict(token, NO_DATA, reading="no predictions run — the token is untested, not adequate")

    held = [o for o in obs if o.holds is True]
    failed = [o for o in obs if o.holds is False]
    pending = [o for o in obs if o.holds is None]

    if not held and not failed:
        return ScopeVerdict(
            token, NO_DATA, reading=f"{len(pending)} test(s) stated and none run — "
                                    f"the token is untested, not adequate",
        )
    if not failed:
        return ScopeVerdict(
            token, ADEQUATE, len(held), 0,
            reading="holds on every prediction run; adequate at the scopes tested, "
                    "and untested outside them",
        )
    if not held:
        return ScopeVerdict(
            token, PLACEHOLDER, 0, len(failed),
            failing_conditions=[o.label for o in failed],
            reading="fails everywhere tested — the name carries no structural claim; "
                    "reason from the entry, not from the shape",
        )

    hs = [o.scale for o in held if o.scale is not None]
    fs = [o.scale for o in failed if o.scale is not None]
    if len(hs) == len(held) and len(fs) == len(failed):
        if min(fs) > max(hs):
            return ScopeVerdict(
                token, BOUNDED, len(held), len(failed), boundary_scale=min(fs), direction="above",
                failing_conditions=[o.label for o in failed],
                reading=f"real at this scope; boundary measured between {max(hs):g} and {min(fs):g} — "
                        f"a new term enters above it",
            )
        if max(fs) < min(hs):
            return ScopeVerdict(
                token, BOUNDED, len(held), len(failed), boundary_scale=max(fs), direction="below",
                failing_conditions=[o.label for o in failed],
                reading=f"real at this scope; boundary measured between {max(fs):g} and {min(hs):g} — "
                        f"a new term enters below it",
            )
        return ScopeVerdict(
            token, INDETERMINATE, len(held), len(failed),
            failing_conditions=[o.label for o in failed],
            reading="holds and fails interleaved on the scale axis — the control parameter "
                    "is the wrong one, or a second term is uncontrolled",
        )

    return ScopeVerdict(
        token, BOUNDED, len(held), len(failed),
        failing_conditions=[o.label for o in failed],
        reading="real where it holds; the boundary is by condition rather than by scale — "
                "the failing conditions name what the token does not cover",
    )


# ── io ────────────────────────────────────────────────────────────

def _read_observations(p: pathlib.Path) -> List[Observation]:
    if not p.exists():
        return []
    out = []
    for n, line in enumerate(p.read_text(encoding="utf-8").splitlines(), start=1):
        line = line.strip()
        if not line:
            continue
        try:
            out.append(Observation.from_dict(json.loads(line)))
        except json.JSONDecodeError as exc:
            raise ValueError(f"{p.name}:{n}: {exc}") from exc
    return out


def load_observations(path: Optional[pathlib.Path] = None) -> List[Observation]:
    """One file if given, else every observations*.jsonl in data/rosetta."""
    if path is not None:
        return _read_observations(pathlib.Path(path))
    out: List[Observation] = []
    for p in observation_files():
        out.extend(_read_observations(p))
    return out


def by_token(observations: Optional[List[Observation]] = None) -> Dict[str, List[Observation]]:
    obs = load_observations() if observations is None else observations
    grouped: Dict[str, List[Observation]] = {}
    for o in obs:
        if not o.shape_token:
            continue  # an observation on an entry stop, not on a token
        grouped.setdefault(o.shape_token.upper(), []).append(o)
    return grouped


def verdicts(observations: Optional[List[Observation]] = None) -> Dict[str, ScopeVerdict]:
    return {tok: classify(group) for tok, group in sorted(by_token(observations).items())}


# ── stop status: asserted, measured, contested ────────────────────

def pending_tests(observations: Optional[List[Observation]] = None) -> List[Observation]:
    """Predictions written down and not yet run. The corpus's open experiments."""
    obs = load_observations() if observations is None else observations
    return [o for o in obs if o.holds is None]


def stop_status(entries: Optional[List[Entry]] = None,
                observations: Optional[List[Observation]] = None,
                transfers: Optional[List[Any]] = None) -> Dict[str, List[Dict[str, Any]]]:
    """Per entry, per stop: has anything actually been carried to it?

    Deferred import of transfer.py: rosetta.py imports this module, and
    transfer.py sits downstream of both. Importing it at call time keeps the
    module graph acyclic without weakening the check.
    """
    from rosetta_shape_core.transfer import stop_confirmations, stop_contradictions

    ents = load_entries() if entries is None else entries
    obs = load_observations() if observations is None else observations
    confirms = stop_confirmations(transfers)
    contradicts = stop_contradictions(transfers)

    out: Dict[str, List[Dict[str, Any]]] = {}
    for e in ents:
        rows = []
        for rec in e.stop_records:
            evidence = []
            status = ASSERTED
            if rec.get("cited"):
                status = CITED
                evidence.append(f"cited: {rec['cited'][:70]}")
            if rec["id"] in confirms.get(e.key, []):
                status = MEASURED
                evidence.append("a transfer broke at it")
            if rec["id"] in contradicts.get(e.key, []):
                status = CONTESTED
                evidence.append("a transfer produced past it")
            for o in obs:
                if o.entry == e.key and o.stop == rec["id"]:
                    if o.holds is None:
                        evidence.append(f"test stated, not run: {o.prop}")
                    elif o.holds:
                        if status != CONTESTED:
                            status = MEASURED
                        evidence.append(f"observation: {o.prop}")
                    else:
                        status = CONTESTED
                        evidence.append(f"observation produced past it: {o.prop}")
            rows.append({"id": rec["id"], "says": rec["says"], "status": status, "evidence": evidence})
        out[e.key] = rows
    return out


def stop_tally(status: Optional[Dict[str, List[Dict[str, Any]]]] = None) -> Dict[str, int]:
    st = stop_status() if status is None else status
    counts = {ASSERTED: 0, CITED: 0, MEASURED: 0, CONTESTED: 0}
    for rows in st.values():
        for r in rows:
            counts[r["status"]] += 1
    return counts


def contested_stops(status: Optional[Dict[str, List[Dict[str, Any]]]] = None) -> List[str]:
    """A stop something produced straight past. This one is a defect, not a gap."""
    st = stop_status() if status is None else status
    out = []
    for key, rows in st.items():
        for r in rows:
            if r["status"] == CONTESTED:
                out.append(f"{key} [{r['id']}]: produced past a stated stop — '{r['says']}'. "
                           f"Either the stop is wrong or its condition was never met.")
    return out


def format_stop_report(status: Optional[Dict[str, List[Dict[str, Any]]]] = None) -> str:
    st = stop_status() if status is None else status
    counts = stop_tally(st)
    total = sum(counts.values()) or 1
    lines = ["", "  STOP STATUS — is the boundary measured, or only claimed?", ""]
    for key in sorted(st):
        lines.append(f"  {key}")
        for r in st[key]:
            mark = {MEASURED: "●", CITED: "◐", CONTESTED: "✗", ASSERTED: "○"}[r["status"]]
            lines.append(f"      {mark} {r['status']:<10s} [{r['id']}] {r['says'][:64]}")
            for ev in r["evidence"]:
                lines.append(f"                   {ev}")
        lines.append("")
    lines.append(f"  measured {counts[MEASURED]} / cited {counts[CITED]} / "
                 f"asserted {counts[ASSERTED]} / contested {counts[CONTESTED]}  "
                 f"({100 * counts[MEASURED] // total}% have been carried to)")
    lines.append("  A CITED stop has evidence about the source system. It still is not a")
    lines.append("  measurement of the move stopping — that takes a transfer.")
    lines.append("")
    return "\n".join(lines)


# ── the repo audit ────────────────────────────────────────────────

def audit_entries(entries: Optional[List[Entry]] = None) -> List[str]:
    """Does each entry report where it stops? Empty return = nothing flagged."""
    from rosetta_shape_core.entry import EXCUSES_EMPTY

    ents = load_entries() if entries is None else entries
    findings: List[str] = []
    for e in ents:
        for half, text in (("stops", "reports no stop — matches everywhere, never fails; this is the flag"),
                           ("produces", "reports no scope of production — nothing to test")):
            if getattr(e, half):
                continue
            if e.status_of(f"scope.{half}") in EXCUSES_EMPTY:
                continue  # declared open, which is a statement rather than a silence
            findings.append(f"{e.key}: {text}")
    return findings


def audit_tokens(entries: Optional[List[Entry]] = None, observations: Optional[List[Observation]] = None) -> List[str]:
    """Advisory: shape tokens carried without predictions run against them."""
    ents = load_entries() if entries is None else entries
    grouped = by_token(observations)
    findings = []
    for e in ents:
        if not e.shape_token:
            continue
        tok = e.shape_token.upper()
        if not properties(tok):
            findings.append(f"{e.key}: token {tok} has no formal properties in SHAPE_PROPERTIES — nothing to predict from")
        elif tok not in grouped:
            findings.append(f"{e.key}: token {tok} carried but no predictions run — status ungraded")
    return findings


def format_verdict(v: ScopeVerdict) -> str:
    lines = [f"  {v.shape_token}  →  {v.status}   ({v.holds} held / {v.fails} failed)"]
    if v.boundary_scale is not None:
        lines.append(f"      boundary   {v.boundary_scale:g}, fails {v.direction}")
    for c in v.failing_conditions:
        lines.append(f"      fails at   {c}")
    if v.reading:
        lines.append(f"      reading    {v.reading}")
    return "\n".join(lines)


# ── selftest ──────────────────────────────────────────────────────

def selftest() -> List[str]:
    fails = []
    if classify([]).status != NO_DATA:
        fails.append("empty observation set not reported as NO_DATA")

    if classify([Observation("X", "p", None)]).status != NO_DATA:
        fails.append("a stated-but-unrun test was treated as evidence")
    mixed = classify([Observation("X", "p", True), Observation("X", "p", None)])
    if mixed.status != ADEQUATE:
        fails.append("a pending test spoiled a verdict it should have been excluded from")

    all_hold = [Observation("HEXAGON", "tiles_plane", True), Observation("HEXAGON", "interior_angle", True)]
    if classify(all_hold).status != ADEQUATE:
        fails.append("all-holding observations not ADEQUATE")

    none_hold = [Observation("BLOB", "vertices", False), Observation("BLOB", "edges", False)]
    if classify(none_hold).status != PLACEHOLDER:
        fails.append("all-failing observations not PLACEHOLDER")

    scaled = [
        Observation("OCTAHEDRON", "face_rate_ordering", True, scale=1.1),
        Observation("OCTAHEDRON", "face_rate_ordering", True, scale=1.3),
        Observation("OCTAHEDRON", "face_rate_ordering", False, scale=3.0),
    ]
    v = classify(scaled)
    if v.status != BOUNDED or v.boundary_scale != 3.0 or v.direction != "above":
        fails.append("scale-separable observations not BOUNDED above at the first failing scale")

    interleaved = [
        Observation("X", "p", True, scale=1.0),
        Observation("X", "p", False, scale=2.0),
        Observation("X", "p", True, scale=3.0),
    ]
    if classify(interleaved).status != INDETERMINATE:
        fails.append("interleaved observations not INDETERMINATE")

    by_condition = [
        Observation("HEXAGON", "tiles", True, condition="flat region"),
        Observation("HEXAGON", "tiles", False, condition="closed surface"),
    ]
    cv = classify(by_condition)
    if cv.status != BOUNDED or cv.boundary_scale is not None:
        fails.append("condition-separable observations not BOUNDED by condition")

    props = properties("hexagon")
    if props.get("vertices") != 6 or not props.get("tiles_plane"):
        fails.append("SHAPE_PROPERTIES lookup broken")
    if properties("NOT_A_SHAPE"):
        fails.append("properties() invented a shape")

    for tok in ("TETRAHEDRON", "CUBE", "OCTAHEDRON", "DODECAHEDRON", "ICOSAHEDRON"):
        p = SHAPE_PROPERTIES[tok]
        if p["vertices"] - p["edges"] + p["faces"] != 2:
            fails.append(f"{tok}: V-E+F != 2 in the properties table")

    if audit_entries():
        fails.append("shipped entries do not all report a stop")

    st = stop_status()
    counts = stop_tally(st)
    if sum(counts.values()) == 0:
        fails.append("no stops found to grade")
    if counts[MEASURED] == 0:
        fails.append("not one stop has been carried to — the audit criterion has no floor")
    if counts[ASSERTED] + counts[CITED] == 0:
        fails.append("every stop reads as measured, which would be too good to be true")
    if counts[MEASURED] >= counts[CITED] + counts[ASSERTED]:
        fails.append("more stops carried to than not — check the precedence, that is unlikely")
    cited = sc_cited = [r for rows in st.values() for r in rows if r["status"] == CITED]
    if not cited:
        fails.append("no stop names the source that established it")
    if any(not r["evidence"] for r in sc_cited):
        fails.append("a CITED stop reports no citation")
    if contested_stops():
        fails.append("an entry produces past its own stated stop")
    hex_stops = {r["id"]: r["status"] for r in st["ENTRY.HONEYCOMB_PARTITION"]}
    if hex_stops.get("closed_surface") != MEASURED:
        fails.append("a transfer that broke at a stated stop did not mark it measured")
    if hex_stops.get("cost_not_on_wall_length") != ASSERTED:
        fails.append("an untested stop did not read as asserted")
    if not load_observations():
        fails.append("observations.jsonl is empty")
    if any(o.shape_token == "" for o in load_observations()) and not any(
            o.stop for o in load_observations()):
        fails.append("an observation targets neither a token nor a stop")
    return fails


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="T4 scope — boundary locator")
    ap.add_argument("--shape", help="print the formal properties a token is answerable for")
    ap.add_argument("--classify", metavar="TOKEN", help="grade one token from its observations")
    ap.add_argument("--all", action="store_true", help="grade every token with observations")
    ap.add_argument("--audit", action="store_true", help="repo audit: does each entry report where it stops?")
    ap.add_argument("--stops", action="store_true", help="per-stop status: asserted, measured, contested")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args(argv)

    if args.selftest:
        f = selftest()
        for line in f:
            print(f"FAIL  {line}")
        print("scope: OK" if not f else f"scope: {len(f)} FAILED")
        return 1 if f else 0

    if args.shape:
        props = properties(args.shape)
        if args.json:
            print(json.dumps({"token": args.shape.upper(), "properties": props}, indent=2))
        elif props:
            print(f"\n  {args.shape.upper()} — reason from these; a failed prediction grades the token\n")
            for k, v in props.items():
                print(f"      {k:52s} {v}")
            print()
        else:
            print(f"{args.shape.upper()}: no formal properties on file — nothing to predict from")
        return 0 if props else 1

    if args.classify:
        group = by_token().get(args.classify.upper(), [])
        v = classify(group) if group else ScopeVerdict(args.classify.upper(), NO_DATA, reading="no observations on file")
        print(json.dumps(v.to_dict(), indent=2) if args.json else format_verdict(v))
        return 0

    if args.stops:
        st = stop_status()
        if args.json:
            print(json.dumps({"stops": st, "tally": stop_tally(st)}, indent=2))
        else:
            print(format_stop_report(st))
        return 0

    if args.audit:
        findings = audit_entries() + contested_stops()
        advisories = audit_tokens()
        counts = stop_tally()
        if args.json:
            print(json.dumps({"flags": findings, "advisories": advisories,
                              "stops": counts, "clean": not findings}, indent=2))
        else:
            for x in findings:
                print(f"  FLAG  {x}")
            for x in advisories:
                print(f"  ⚠     {x}")
            print(f"  stops: {counts[MEASURED]} measured / {counts[CITED]} cited / "
                  f"{counts[ASSERTED]} asserted / {counts[CONTESTED]} contested — "
                  f"only measured means a move was carried to it (--stops for detail)")
            print("scope audit: CLEAN" if not findings else f"scope audit: {len(findings)} flag(s)")
        return 1 if findings else 0

    vs = verdicts()
    if args.json:
        print(json.dumps({t: v.to_dict() for t, v in vs.items()}, indent=2))
    else:
        print(f"\n  SHAPE TOKEN STATUS — self-declared under use ({len(vs)} token(s))\n")
        for v in vs.values():
            print(format_verdict(v))
            print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
