# SPDX-License-Identifier: CC0-1.0
"""T1 — the operator: cross-DOMAIN constraint-solution transfer.

    form    "what would X do here?"  — X = crystal, animal, mycelium,
            whatever holds the domain
    use     run your problem through a system that solved a structurally
            similar one under different constraints, read the configuration
            it reached, and port the MOVE — not the ontology

WHAT THE OPERATOR IS NOT
    Not animacy. Not sentience. Not agency. Not an interior life. Nothing
    here attributes experience to a crystal, a fungus or a blade of grass.
    "Intelligence", where the term appears in this repo, means the system's
    demonstrated capacity to arrive at a configuration under environmental
    constraint. That is a measurement of behaviour, not an attribution of
    interiority. The operator is a REASONING MOVE. It was never a claim
    about what the crystal is.

    This paragraph is in the module docstring rather than a footnote because
    it is the substitution that keeps happening: the term gets read as an
    ontological claim and the claim gets answered instead of the operator
    getting used.

WHAT LICENSES A TRANSFER
    Forcing terms, and nothing else.

      SHARED FORCING   the same field acts on both systems — grass and body
                       under gravity, both carrying load. The shape is caused;
                       the transfer is licensed.
      SHARED FORM      the shapes coincide and no common term is named.
                       Coincidence until a mechanism appears. Reported, not
                       suppressed — an unlicensed match is a lead, and the
                       work it asks for is finding the term or dropping it.

    Because the family vocabulary is physics-denominated by construction
    (see families.py), an overlap in forcing terms is a statement about the
    loads, not a resemblance noticed after the fact. That is why "pattern
    matching" is the wrong reading of this operator.

AXES
    Rosetta is cross-DOMAIN transfer (crystal -> your problem).
    Mandala is cross-SCALE persistence (grass -> ecosystem).
    Orthogonal. They are linked, not merged — see docs/rosetta-operator.md.

CONSTRAINTS (repo-wide, restated per file)
    - no "about the author" / working-style section, in this or any file
    - entries are markers to explore, not positions defended; the correct
      response to one is: test fit / extend / report break
    - no moral labels in data structures, no intent attribution

Usage:
    python -m rosetta_shape_core.rosetta --forcing flow,strain
    python -m rosetta_shape_core.rosetta --forcing gravity --problem "sizing a mast"
    python -m rosetta_shape_core.rosetta --source "grass blade in wind"
    python -m rosetta_shape_core.rosetta --unlicensed --forcing phase
    python -m rosetta_shape_core.rosetta --selftest
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass, field
from typing import List, Optional

from rosetta_shape_core.entry import Entry, load_entries
from rosetta_shape_core.families import FAMILIES
from rosetta_shape_core.families import resolve as resolve_family
from rosetta_shape_core.scope import by_token, classify

SHARED_FORCING = "SHARED_FORCING"
SHARED_FORM = "SHARED_FORM"


@dataclass
class Problem:
    """The problem being carried to the source system.

    ``forcing_terms`` are the loads acting on YOUR problem. They are what
    the match is made on, so naming them badly is the main way to get a
    useless transfer.
    """

    forcing_terms: List[str] = field(default_factory=list)
    description: str = ""

    @property
    def families(self) -> List[str]:
        out = []
        for t in self.forcing_terms:
            fid = resolve_family(t)
            if fid and fid not in out:
                out.append(fid)
        return out

    @property
    def unresolved(self) -> List[str]:
        return [t for t in self.forcing_terms if resolve_family(t) is None]


@dataclass
class Match:
    """One entry against one problem, with the licensing stated."""

    entry_key: str
    source_system: str
    move_ported: str
    shared_terms: List[str] = field(default_factory=list)
    entry_only_terms: List[str] = field(default_factory=list)
    problem_only_terms: List[str] = field(default_factory=list)
    licensing: str = SHARED_FORM
    stops: List[str] = field(default_factory=list)
    shape_token: Optional[str] = None
    token_status: str = ""
    reading: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


def licensing_of(shared: List[str]) -> str:
    return SHARED_FORCING if shared else SHARED_FORM


def _reading(licensing: str, shared: List[str], entry: Entry) -> str:
    if licensing == SHARED_FORCING:
        verb = "acts" if len(shared) == 1 else "act"
        return (
            f"licensed: {', '.join(shared)} {verb} on both. The shape is forced, not resembled — "
            f"port the move and then test it against the stops below."
        )
    return (
        "unlicensed: no forcing term in common. Coincidence until a mechanism appears. "
        "Either name the term both systems are under, or drop the match — do not port on the form alone."
    )


def match(problem: Problem, entry: Entry) -> Match:
    """Run one entry against the problem. Always returns a Match, licensed or not."""
    p = set(problem.families)
    e = set()
    for t in entry.forcing_terms:
        fid = resolve_family(t)
        if fid:
            e.add(fid)
    shared = sorted(p & e)
    lic = licensing_of(shared)

    token_status = ""
    if entry.shape_token:
        group = by_token().get(entry.shape_token.upper(), [])
        token_status = classify(group).status if group else "NO_DATA"

    return Match(
        entry_key=entry.key,
        source_system=entry.source_system,
        move_ported=entry.move_ported,
        shared_terms=shared,
        entry_only_terms=sorted(e - p),
        problem_only_terms=sorted(p - e),
        licensing=lic,
        stops=entry.stops,
        shape_token=entry.shape_token,
        token_status=token_status,
        reading=_reading(lic, shared, entry),
    )


def run(problem: Problem, entries: Optional[List[Entry]] = None, *, include_unlicensed: bool = False) -> List[Match]:
    """The operator. Returns matches, most-shared-forcing first.

    Unlicensed matches are withheld by default and returned last when asked
    for, so a shared-form lead can never be mistaken for a shared-forcing one.
    """
    ents = load_entries() if entries is None else entries
    matches = [match(problem, e) for e in ents]
    licensed = [m for m in matches if m.licensing == SHARED_FORCING]
    licensed.sort(key=lambda m: (-len(m.shared_terms), m.entry_key))
    if not include_unlicensed:
        return licensed
    unlicensed = sorted((m for m in matches if m.licensing == SHARED_FORM), key=lambda m: m.entry_key)
    return licensed + unlicensed


def by_source(name: str, entries: Optional[List[Entry]] = None) -> List[Entry]:
    """'What would X do here?' — find the entries for X."""
    ents = load_entries() if entries is None else entries
    key = name.strip().lower()
    return [e for e in ents if key in e.source_system.lower() or key in e.key.lower()]


def format_match(m: Match) -> str:
    lines = [f"  {m.entry_key}   [{m.licensing}]"]
    lines.append(f"      source     {m.source_system}")
    lines.append(f"      shared     {', '.join(m.shared_terms) if m.shared_terms else '(none)'}")
    lines.append(f"      MOVE       {m.move_ported}")
    if m.shape_token:
        lines.append(f"      token      {m.shape_token} ({m.token_status})")
    for s in m.stops:
        lines.append(f"      stops      {s}")
    if m.entry_only_terms:
        v = "acts" if len(m.entry_only_terms) == 1 else "act"
        lines.append(f"      unmatched  {', '.join(m.entry_only_terms)} {v} on the source and not on the problem")
    if m.problem_only_terms:
        v = "acts" if len(m.problem_only_terms) == 1 else "act"
        lines.append(f"      unmatched  {', '.join(m.problem_only_terms)} {v} on the problem and not on the source")
    lines.append(f"      reading    {m.reading}")
    return "\n".join(lines)


# ── selftest ──────────────────────────────────────────────────────

def selftest() -> List[str]:
    fails = []
    ents = load_entries()
    if not ents:
        return ["no entries to run the operator on"]

    p = Problem(["flow", "strain"], "a slender thing in moving fluid")
    if p.families != ["FLOW", "STRAIN"]:
        fails.append("problem forcing terms did not resolve to families")
    if Problem(["astrology"]).unresolved != ["astrology"]:
        fails.append("unresolved terms not reported")

    ms = run(p, ents)
    if not ms:
        fails.append("no licensed match for FLOW+STRAIN — expected the grass entry")
    elif ms[0].entry_key != "ENTRY.GRASS_RECONFIGURATION":
        fails.append(f"expected grass first for FLOW+STRAIN, got {ms[0].entry_key}")
    if any(m.licensing != SHARED_FORCING for m in ms):
        fails.append("run() returned an unlicensed match without being asked")

    lonely = Problem(["resonance"])
    if run(lonely, ents):
        fails.append("RESONANCE matched an entry that does not carry it")
    unl = run(lonely, ents, include_unlicensed=True)
    if len(unl) != len(ents):
        fails.append("include_unlicensed did not return every entry")
    if any(m.licensing != SHARED_FORM for m in unl):
        fails.append("shared-form matches mis-licensed")

    ordered = run(Problem(["gravity", "strain", "pressure"]), ents)
    if ordered and len(ordered[0].shared_terms) < len(ordered[-1].shared_terms):
        fails.append("matches not sorted by shared forcing count")

    if not by_source("grass", ents):
        fails.append("by_source('grass') found nothing")
    if by_source("telephone", ents):
        fails.append("by_source invented a source system")

    for fid in FAMILIES:
        pr = Problem([fid])
        for m in run(pr, ents, include_unlicensed=True):
            if m.licensing == SHARED_FORCING and fid not in m.shared_terms:
                fails.append(f"{m.entry_key}: licensed without the shared term present")
    return fails


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="T1 rosetta — cross-domain constraint-solution transfer")
    ap.add_argument("--forcing", help="comma-separated forcing terms acting on YOUR problem")
    ap.add_argument("--problem", default="", help="one line describing the problem (not used for matching)")
    ap.add_argument("--source", help="'what would X do here?' — show the entries for X")
    ap.add_argument("--unlicensed", action="store_true", help="also show shared-form matches (leads, not transfers)")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args(argv)

    if args.selftest:
        f = selftest()
        for line in f:
            print(f"FAIL  {line}")
        print("rosetta: OK" if not f else f"rosetta: {len(f)} FAILED")
        return 1 if f else 0

    if args.source:
        found = by_source(args.source)
        if args.json:
            print(json.dumps([e.to_dict() for e in found], indent=2))
        else:
            from rosetta_shape_core.entry import format_entry
            print(f"\n  SOURCE SYSTEMS matching '{args.source}' ({len(found)})\n")
            for e in found:
                print(format_entry(e))
                print()
        return 0 if found else 1

    if not args.forcing:
        ap.print_help()
        return 2

    problem = Problem([t.strip() for t in args.forcing.split(",") if t.strip()], args.problem)
    matches = run(problem, include_unlicensed=args.unlicensed)

    if args.json:
        print(json.dumps({
            "problem": problem.description,
            "forcing_terms": problem.families,
            "unresolved": problem.unresolved,
            "matches": [m.to_dict() for m in matches],
        }, indent=2))
        return 0

    print()
    if problem.description:
        print(f"  PROBLEM    {problem.description}")
    print(f"  FORCING    {', '.join(problem.families) if problem.families else '(none resolved)'}")
    for t in problem.unresolved:
        print(f"  ⚠  '{t}' resolves to no family — name the physical term or register one (families.py)")
    print()
    if not matches:
        print("  no licensed match. Re-run with --unlicensed to see shared-form leads,")
        print("  or add an entry: the absence is a gap in the entry set, not a result.")
        print()
        return 0
    for m in matches:
        print(format_match(m))
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
