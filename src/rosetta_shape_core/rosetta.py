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
    Forcing terms, and nothing else — but presence of a shared term is too
    cheap a test on its own. Strain acts on nearly every physical system, so
    matching on presence licenses almost every pair: the criterion stays
    correct in principle and erodes in practice while still looking
    rigorous. What licenses a transfer is a term that is SETTING the
    configuration on both sides, so the grade is read off dominance:

      SHARED DOMINANT  a term sets the configuration on both sides. Strongest
                       reading: the same thing is doing the work in both
                       systems.
      SHARED FORCING   a shared term, dominant on one side only. The source
                       is answering a question the problem is only partly
                       asking — port, then check the term that is not shared.
      SHARED PRESENT   the only shared terms set neither configuration. Both
                       systems are under the term; neither is shaped by it.
                       Weak, and the commonest way to fool yourself.
      SHARED FORM      the shapes coincide and no common term is named.
                       Coincidence until a mechanism appears. Reported, not
                       suppressed — an unlicensed match is a lead, and the
                       work it asks for is finding the term or dropping it.

    Only the first two are returned by default.

ENTRIES THAT CANNOT YET LICENSE ANYTHING
    An entry whose forcing terms are marked OPEN is not matched at all —
    there is nothing to license on. It is still worth carrying: a source
    system on file, waiting for someone to name the loads. ``--open`` lists
    them, because an entry nobody has finished is an experiment on offer
    rather than a defect.

    An entry that IS matched but whose move_ported is open comes back with
    that said out loud. Being under the same load as a system nobody has
    read yet is a real result — it just is not a transfer.

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
    python -m rosetta_shape_core.rosetta --forcing flow,strain --dominant flow
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
from typing import Dict, List, Optional

from rosetta_shape_core.entry import Entry, load_entries
from rosetta_shape_core.families import FAMILIES
from rosetta_shape_core.families import resolve as resolve_family
from rosetta_shape_core.scope import by_token, classify

SHARED_DOMINANT = "SHARED_DOMINANT"
SHARED_FORCING = "SHARED_FORCING"
SHARED_PRESENT = "SHARED_PRESENT"
SHARED_FORM = "SHARED_FORM"

# strongest first; this is the sort order and the default cut
GRADES = (SHARED_DOMINANT, SHARED_FORCING, SHARED_PRESENT, SHARED_FORM)
LICENSED = (SHARED_DOMINANT, SHARED_FORCING)


@dataclass
class Problem:
    """The problem being carried to the source system.

    ``forcing_terms`` are the loads acting on YOUR problem. They are what
    the match is made on, so naming them badly is the main way to get a
    useless transfer.
    """

    forcing_terms: List[str] = field(default_factory=list)
    description: str = ""
    dominant_terms: List[str] = field(default_factory=list)

    @property
    def families(self) -> List[str]:
        return _resolve_all(self.forcing_terms)

    @property
    def dominant(self) -> List[str]:
        """Which of your terms SETS your configuration. Naming none costs a grade."""
        return [f for f in _resolve_all(self.dominant_terms) if f in self.families]

    @property
    def unresolved(self) -> List[str]:
        terms = list(self.forcing_terms) + list(self.dominant_terms)
        return [t for t in terms if resolve_family(t) is None]


def _resolve_all(terms: List[str]) -> List[str]:
    out = []
    for t in terms:
        fid = resolve_family(t)
        if fid and fid not in out:
            out.append(fid)
    return out


@dataclass
class Match:
    """One entry against one problem, with the licensing stated."""

    entry_key: str
    source_system: str
    move_ported: str
    shared_terms: List[str] = field(default_factory=list)
    shared_dominant: List[str] = field(default_factory=list)
    entry_only_terms: List[str] = field(default_factory=list)
    problem_only_terms: List[str] = field(default_factory=list)
    licensing: str = SHARED_FORM
    stops: List[str] = field(default_factory=list)
    shape_token: Optional[str] = None
    token_status: str = ""
    open_fields: Dict[str, str] = field(default_factory=dict)
    reading: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


def licensing_of(shared: List[str], shared_dominant: List[str],
                 entry_dominant: List[str], problem_dominant: List[str]) -> str:
    """Grade the overlap by what the shared terms are DOING, not that they exist."""
    if not shared:
        return SHARED_FORM
    if shared_dominant:
        return SHARED_DOMINANT
    if any(t in entry_dominant or t in problem_dominant for t in shared):
        return SHARED_FORCING
    return SHARED_PRESENT


def _reading(licensing: str, shared: List[str], shared_dominant: List[str], entry: Entry) -> str:
    if licensing == SHARED_DOMINANT:
        verb = "sets" if len(shared_dominant) == 1 else "set"
        return (
            f"licensed: {', '.join(shared_dominant)} {verb} the configuration on both sides. "
            f"The same term is doing the work — port the move, then test it against the stops below."
        )
    if licensing == SHARED_FORCING:
        return (
            f"licensed, one-sided: {', '.join(shared)} in common, but setting the configuration on "
            f"one side only. The source is answering a question you are only partly asking — port, "
            f"then check what the unshared dominant term does to it."
        )
    if licensing == SHARED_PRESENT:
        return (
            f"weak: {', '.join(shared)} act on both systems and set neither configuration. Being "
            f"under the same term is not being shaped by it — this is the commonest way to fool "
            f"yourself into a transfer."
        )
    return (
        "unlicensed: no forcing term in common. Coincidence until a mechanism appears. "
        "Either name the term both systems are under, or drop the match — do not port on the form alone."
    )


def match(problem: Problem, entry: Entry) -> Match:
    """Run one entry against the problem. Always returns a Match, licensed or not."""
    p = set(problem.families)
    e = set(entry.families)
    pd = set(problem.dominant)
    ed = set(entry.dominant)
    shared = sorted(p & e)
    shared_dominant = sorted(pd & ed)
    lic = licensing_of(shared, shared_dominant, sorted(ed), sorted(pd))

    token_status = ""
    if entry.shape_token:
        group = by_token().get(entry.shape_token.upper(), [])
        token_status = classify(group).status if group else "NO_DATA"

    return Match(
        entry_key=entry.key,
        source_system=entry.source_system,
        move_ported=entry.move_ported,
        shared_terms=shared,
        shared_dominant=shared_dominant,
        entry_only_terms=sorted(e - p),
        problem_only_terms=sorted(p - e),
        licensing=lic,
        stops=entry.stops,
        shape_token=entry.shape_token,
        token_status=token_status,
        open_fields=dict(entry.field_status),
        reading=_reading(lic, shared, shared_dominant, entry),
    )


def run(problem: Problem, entries: Optional[List[Entry]] = None, *,
        include_weak: bool = False, include_unlicensed: bool = False) -> List[Match]:
    """The operator. Returns matches, strongest grade first.

    Only licensed grades come back by default. Weak (shared-present) and
    unlicensed (shared-form) matches are withheld unless asked for, so a
    term that merely acts on both systems can never be mistaken for one that
    shapes both. Asking for unlicensed matches implies the weak ones too:
    they sit between, and hiding the middle would misrank what is shown.
    """
    ents = [e for e in (load_entries() if entries is None else entries) if e.transferable]
    wanted = list(LICENSED)
    if include_weak or include_unlicensed:
        wanted.append(SHARED_PRESENT)
    if include_unlicensed:
        wanted.append(SHARED_FORM)
    matches = [m for m in (match(problem, e) for e in ents) if m.licensing in wanted]
    matches.sort(key=lambda m: (GRADES.index(m.licensing), -len(m.shared_dominant),
                                -len(m.shared_terms), m.entry_key))
    return matches


def open_entries(entries: Optional[List[Entry]] = None) -> List[Entry]:
    """Entries on file that cannot yet license a transfer. Offers, not defects."""
    ents = load_entries() if entries is None else entries
    return [e for e in ents if not e.transferable]


def by_source(name: str, entries: Optional[List[Entry]] = None) -> List[Entry]:
    """'What would X do here?' — find the entries for X."""
    ents = load_entries() if entries is None else entries
    key = name.strip().lower()
    return [e for e in ents if key in e.source_system.lower() or key in e.key.lower()]


def format_match(m: Match) -> str:
    lines = [f"  {m.entry_key}   [{m.licensing}]"]
    lines.append(f"      source     {m.source_system}")
    lines.append(f"      shared     {', '.join(m.shared_terms) if m.shared_terms else '(none)'}")
    if m.shared_dominant:
        lines.append(f"      sets both  {', '.join(m.shared_dominant)}")
    lines.append(f"      MOVE       {m.move_ported}")
    if m.shape_token:
        lines.append(f"      token      {m.shape_token} ({m.token_status})")
    if m.open_fields.get("move_ported"):
        lines.append(f"      OPEN       move_ported is {m.open_fields['move_ported']} — this entry is "
                     f"under your loads and nobody has named what transfers. An invitation, not a transfer.")
    for name, status in sorted(m.open_fields.items()):
        if name != "move_ported":
            lines.append(f"      {status:<10s} {name}")
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

    p = Problem(["flow", "strain"], "a slender thing in moving fluid", ["flow"])
    if p.families != ["FLOW", "STRAIN"] or p.dominant != ["FLOW"]:
        fails.append("problem forcing terms did not resolve to families")
    if Problem(["astrology"]).unresolved != ["astrology"]:
        fails.append("unresolved terms not reported")
    if Problem(["flow"], dominant_terms=["strain"]).dominant:
        fails.append("a dominant term outside the problem's forcing terms was kept")

    ms = run(p, ents)
    if not ms:
        fails.append("no licensed match for FLOW+STRAIN — expected the grass entry")
    elif ms[0].entry_key != "ENTRY.GRASS_RECONFIGURATION" or ms[0].licensing != SHARED_DOMINANT:
        fails.append(f"expected grass SHARED_DOMINANT first, got {ms[0].entry_key} {ms[0].licensing}")
    if any(m.licensing not in LICENSED for m in ms):
        fails.append("run() returned a weak or unlicensed match without being asked")

    # the erosion this grading exists to stop: strain is present nearly everywhere
    present_only = Problem(["strain"])
    weak = run(present_only, ents, include_weak=True)
    if not any(m.licensing == SHARED_PRESENT for m in weak):
        fails.append("a term present on both sides and dominant on neither was not graded weak")
    if any(m.licensing == SHARED_PRESENT for m in run(present_only, ents)):
        fails.append("a weak match came back without --weak")

    if any(m.licensing == SHARED_DOMINANT for m in weak):
        fails.append("SHARED_DOMINANT reached without the problem naming a dominant term")

    setting = run(Problem(["strain"], dominant_terms=["strain"]), ents)
    top = {m.entry_key for m in setting if m.licensing == SHARED_DOMINANT}
    expected = {e.key for e in ents if "STRAIN" in e.dominant}
    if top != expected:
        fails.append(f"SHARED_DOMINANT set is {sorted(top)}, expected {sorted(expected)}")
    grass = next(m for m in setting if m.entry_key == "ENTRY.GRASS_RECONFIGURATION")
    if grass.licensing != SHARED_FORCING:
        fails.append("strain sets the problem but not grass — that is one-sided, not dominant")

    lonely = Problem(["resonance"])
    if run(lonely, ents):
        fails.append("RESONANCE matched an entry that does not carry it")
    unl = run(lonely, ents, include_unlicensed=True)
    if len(unl) != len([e for e in ents if e.transferable]):
        fails.append("include_unlicensed did not return every entry that can license")
    if any(m.licensing != SHARED_FORM for m in unl):
        fails.append("shared-form matches mis-licensed")

    ordered = run(Problem(["gravity", "strain", "pressure"], dominant_terms=["strain"]), ents,
                  include_unlicensed=True)
    grades = [GRADES.index(m.licensing) for m in ordered]
    if grades != sorted(grades):
        fails.append("matches not sorted strongest grade first")

    if open_entries(ents) and any(e.transferable for e in open_entries(ents)):
        fails.append("open_entries returned an entry that can license")
    for m in run(Problem(["flow"], dominant_terms=["flow"]), ents):
        if not next(e for e in ents if e.key == m.entry_key).transferable:
            fails.append(f"{m.entry_key}: matched despite open forcing terms")

    if not by_source("grass", ents):
        fails.append("by_source('grass') found nothing")
    if by_source("telephone", ents):
        fails.append("by_source invented a source system")

    for fid in FAMILIES:
        pr = Problem([fid], dominant_terms=[fid])
        for m in run(pr, ents, include_unlicensed=True):
            if m.licensing != SHARED_FORM and fid not in m.shared_terms:
                fails.append(f"{m.entry_key}: graded {m.licensing} without the shared term present")
            if m.licensing == SHARED_DOMINANT and fid not in m.shared_dominant:
                fails.append(f"{m.entry_key}: graded SHARED_DOMINANT without a term setting both")
    return fails


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="T1 rosetta — cross-domain constraint-solution transfer")
    ap.add_argument("--forcing", help="comma-separated forcing terms acting on YOUR problem")
    ap.add_argument("--dominant", help="which of those terms SETS your configuration (comma-separated)")
    ap.add_argument("--problem", default="", help="one line describing the problem (not used for matching)")
    ap.add_argument("--source", help="'what would X do here?' — show the entries for X")
    ap.add_argument("--open", action="store_true", dest="show_open",
                    help="entries that cannot license yet — the loads are unnamed, and that is the ask")
    ap.add_argument("--weak", action="store_true", help="also show shared-present matches (term acts on both, shapes neither)")
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

    if args.show_open:
        waiting = open_entries()
        if args.json:
            print(json.dumps([e.to_dict() for e in waiting], indent=2))
        else:
            print(f"\n  OPEN ENTRIES ({len(waiting)}) — on file, not yet able to license a transfer\n")
            for e in waiting:
                print(f"  {e.key}")
                print(f"      {e.source_system}")
                print(f"      waiting on: {', '.join(f'{k} {v}' for k, v in sorted(e.field_status.items()))}")
            print("\n  Naming the loads is the experiment on offer. See families.py for the vocabulary.\n")
        return 0

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

    problem = Problem(
        [t.strip() for t in args.forcing.split(",") if t.strip()],
        args.problem,
        [t.strip() for t in (args.dominant or "").split(",") if t.strip()],
    )
    matches = run(problem, include_weak=args.weak, include_unlicensed=args.unlicensed)

    if args.json:
        print(json.dumps({
            "problem": problem.description,
            "forcing_terms": problem.families,
            "dominant_terms": problem.dominant,
            "unresolved": problem.unresolved,
            "matches": [m.to_dict() for m in matches],
        }, indent=2))
        return 0

    print()
    if problem.description:
        print(f"  PROBLEM    {problem.description}")
    print(f"  FORCING    {', '.join(problem.families) if problem.families else '(none resolved)'}")
    print(f"  SETS IT    {', '.join(problem.dominant) if problem.dominant else '(none named)'}")
    for t in problem.unresolved:
        print(f"  ⚠  '{t}' resolves to no family — name the physical term or register one (families.py)")
    if not problem.dominant and problem.families:
        print("  ⚠  no dominant term named for your problem, so nothing can grade SHARED_DOMINANT.")
        print("     --dominant <term> says which one SETS your configuration. Naming it is the")
        print("     step that separates a transfer from a coincidence.")
    print()
    if not matches:
        print("  no licensed match. Re-run with --weak to see terms that act on both and shape")
        print("  neither, or --unlicensed for shared-form leads, or add an entry: the absence is")
        print("  a gap in the entry set, not a result.")
        print()
        return 0
    for m in matches:
        print(format_match(m))
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
