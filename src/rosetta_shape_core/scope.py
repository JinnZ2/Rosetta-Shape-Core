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
OBSERVATIONS_PATH = ROOT / "data" / "rosetta" / "observations.jsonl"

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
    """

    shape_token: str
    prop: str
    holds: bool
    scale: Optional[float] = None
    condition: str = ""
    entry: str = ""
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
        return {k: v for k, v in asdict(self).items() if v not in (None, "", {})}

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Observation":
        return cls(
            shape_token=d.get("shape_token", ""),
            prop=d.get("prop", d.get("property", "")),
            holds=bool(d.get("holds")),
            scale=d.get("scale"),
            condition=d.get("condition", ""),
            entry=d.get("entry", ""),
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

    held = [o for o in obs if o.holds]
    failed = [o for o in obs if not o.holds]

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

def load_observations(path: Optional[pathlib.Path] = None) -> List[Observation]:
    p = pathlib.Path(path) if path else OBSERVATIONS_PATH
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


def by_token(observations: Optional[List[Observation]] = None) -> Dict[str, List[Observation]]:
    obs = load_observations() if observations is None else observations
    grouped: Dict[str, List[Observation]] = {}
    for o in obs:
        grouped.setdefault(o.shape_token.upper(), []).append(o)
    return grouped


def verdicts(observations: Optional[List[Observation]] = None) -> Dict[str, ScopeVerdict]:
    return {tok: classify(group) for tok, group in sorted(by_token(observations).items())}


# ── the repo audit ────────────────────────────────────────────────

def audit_entries(entries: Optional[List[Entry]] = None) -> List[str]:
    """Does each entry report where it stops? Empty return = nothing flagged."""
    ents = load_entries() if entries is None else entries
    findings: List[str] = []
    for e in ents:
        if not e.stops:
            findings.append(f"{e.key}: reports no stop — matches everywhere, never fails; this is the flag")
        if not e.produces:
            findings.append(f"{e.key}: reports no scope of production — nothing to test")
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
    if not load_observations():
        fails.append("observations.jsonl is empty")
    return fails


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="T4 scope — boundary locator")
    ap.add_argument("--shape", help="print the formal properties a token is answerable for")
    ap.add_argument("--classify", metavar="TOKEN", help="grade one token from its observations")
    ap.add_argument("--all", action="store_true", help="grade every token with observations")
    ap.add_argument("--audit", action="store_true", help="repo audit: does each entry report where it stops?")
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

    if args.audit:
        findings = audit_entries()
        advisories = audit_tokens()
        if args.json:
            print(json.dumps({"flags": findings, "advisories": advisories, "clean": not findings}, indent=2))
        else:
            for x in findings:
                print(f"  FLAG  {x}")
            for x in advisories:
                print(f"  ⚠     {x}")
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
