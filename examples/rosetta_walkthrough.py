# SPDX-License-Identifier: CC0-1.0
"""One problem, carried end to end through T1-T4, with the wrong readings shown.

Run it:

    python examples/rosetta_walkthrough.py

Nothing here is hardcoded — every result is computed from the shipped data,
so if the entries change, the walkthrough changes with them. That also means
it fails loudly rather than teaching something that is no longer true.

CONSTRAINTS (repo-wide, restated per file)
    - no "about the author" / working-style section, in this or any file
    - entries are markers to explore, not positions defended; the correct
      response to one is: test fit / extend / report break
    - no moral labels in data structures, no intent attribution
"""
from __future__ import annotations

import sys

from rosetta_shape_core.entry import load_entries
from rosetta_shape_core.families import FAMILIES
from rosetta_shape_core.families import resolve as resolve_family
from rosetta_shape_core.rosetta import SHARED_DOMINANT, SHARED_PRESENT, Problem, run
from rosetta_shape_core.scope import ASSERTED, stop_status

PROBLEM = "a roadside mast that has to survive wind loading"


def rule(title: str) -> None:
    print()
    print("=" * 74)
    print(f"  {title}")
    print("=" * 74)


def para(*lines: str) -> None:
    print()
    for line in lines:
        print(f"  {line}" if line else "")


def main(argv=None) -> int:
    entries = load_entries()

    rule("THE PROBLEM")
    para(PROBLEM,
         "",
         "Everything below is the operator applied to that one line. The order",
         "matters: most of the value is in the first two steps, which are the",
         "ones people skip.")

    # ── step 1 ────────────────────────────────────────────────────
    rule("STEP 1 (T2) — say what is acting on it, in physical terms")
    para("First attempt, in the words the problem came in:")
    for word in ("wind", "gusts", "weather"):
        print(f"      resolve({word!r}) -> {resolve_family(word)}")
    para("None of those are families. They are weather, not physics. The",
         "vocabulary is deliberately narrow — one physical term each — so a",
         "word that names a situation rather than a load has nowhere to go:",
         "",
         "      python -m rosetta_shape_core.families --list")
    para("Wind on a slender body is bulk transport of momentum past it, and",
         "the mast's response to it is deformation against a reference length:")
    for word in ("flow", "strain", "gravity"):
        fid = resolve_family(word)
        print(f"      resolve({word!r}) -> {fid}  ({FAMILIES[fid].term})")

    # ── step 2 ────────────────────────────────────────────────────
    rule("STEP 2 (T1) — say which of those SETS the configuration")
    vague = Problem(["flow", "strain", "gravity"], PROBLEM)
    vague_matches = run(vague, entries)
    para("Run it without saying which term is doing the work:")
    print()
    for m in vague_matches:
        print(f"      {m.licensing:<16s} {m.entry_key}   shared: {', '.join(m.shared_terms)}")
    para(f"{len(vague_matches)} matches, none of them graded SHARED_DOMINANT, and the ranking",
         "is nearly flat. That is the criterion being nearly free: strain acts on",
         "almost every physical system, so overlap on presence alone licenses",
         "almost every pair while still looking rigorous.")

    sharp = Problem(["flow", "strain", "gravity"], PROBLEM, dominant_terms=["flow"])
    sharp_matches = run(sharp, entries)
    para("Now name the term that sets it. For a mast in wind that is FLOW: the",
         "wind load is what the shape has to answer, and strain is how it",
         "answers. Same query, one extra word:")
    print()
    for m in sharp_matches:
        marker = "  <-- strongest" if m.licensing == SHARED_DOMINANT else ""
        print(f"      {m.licensing:<16s} {m.entry_key}   sets both: "
              f"{', '.join(m.shared_dominant) or '-'}{marker}")
    para("      python -m rosetta_shape_core.rosetta \\",
         "          --forcing flow,strain,gravity --dominant flow \\",
         f"          --problem {PROBLEM!r}")

    # ── the wrong readings ────────────────────────────────────────
    grass = next(m for m in sharp_matches if m.entry_key == "ENTRY.GRASS_RECONFIGURATION")

    rule("WRONG READING A — porting the ontology instead of the move")
    para("\"Grass has learned to survive wind. The mast should be intelligent",
         "the way grass is intelligent.\"",
         "",
         "Nothing follows from this. There is no design step in it, because it",
         "is a claim about what grass IS, and the operator never made one.",
         "'Intelligence' in this repo means: the configuration a system arrives",
         "at under environmental constraint. A behaviour readout, not an",
         "interior life. What transfers is one operation:",
         "",
         f"      {grass.move_ported}")

    rule("WRONG READING B — matching on a term that shapes neither system")
    strain_only = Problem(["strain"], PROBLEM)
    weak = run(strain_only, entries, include_weak=True)
    para("Say you skipped step 1 and called it what it looks like from a desk:",
         "\"a mast is a structures problem, so it is a strain problem.\"")
    print()
    for m in weak:
        print(f"      {m.licensing:<16s} {m.entry_key}")
    weak_only = [m for m in weak if m.licensing == SHARED_PRESENT]
    para("Look at what that did to the ranking. Strain is present in all of these",
         "because strain is present in nearly everything, so the list fills with",
         "entries whose configuration really is strain-set — a comb, a soap film,",
         "a bone — while the one entry that answers this problem drops to the",
         "bottom and grades weak:",
         "",
         f"      {', '.join(m.entry_key for m in weak_only) or '(none)'}",
         "",
         "SHARED_PRESENT says: both systems are under this term and neither is",
         "shaped by it. The cost of misnaming the load is not a lower score. It",
         "is a reordering that buries the answer under three plausible ones.")

    rule("WRONG READING C — porting the move and dropping the stops")
    para("\"Grass bends, so build a mast that bends.\" The move is right and the",
         "reading is still wrong, because the entry says where it stops:")
    print()
    for r in next(e for e in entries if e.key == grass.entry_key).stop_records:
        print(f"      [{r['id']}]")
        print(f"          {r['says']}")
    para("The first one is decisive for a roadside mast. A mast that holds a",
         "sign or a light has a stiffness requirement of its own: deflection is",
         "the function, not the cost. The third is the one that bites later —",
         "a compliant mast trades a peak load for millions of load cycles, and",
         "the fatigue life is a different calculation entirely.",
         "",
         "The stops are not caveats attached to the move. They are the",
         "measurement of where it produces.")

    # ── right reading ─────────────────────────────────────────────
    rule("RIGHT READING — port the move, carry the stops, name the test")
    para(f"FROM     {grass.source_system}",
         f"LICENSE  {grass.licensing} on {', '.join(grass.shared_dominant)}",
         f"MOVE     {grass.move_ported}",
         "",
         "TEST     does this mast's function tolerate deflection? If it carries",
         "         a sign or a luminaire with a pointing requirement, the first",
         "         stop applies and the transfer is refused here — which is a",
         "         result, arrived at in two steps.",
         "",
         "         if it does tolerate deflection — a whip antenna, a flexible",
         "         delineator post — the move is live, and the open question is",
         "         the third stop: cycles to failure at the new amplitude.")

    # ── step 4 ────────────────────────────────────────────────────
    rule("STEP 4 (T4) — what carrying it would MEASURE")
    rows = {r["id"]: r for r in stop_status(entries)[grass.entry_key]}
    para("Each stop currently reads:")
    print()
    for sid, r in rows.items():
        print(f"      {r['status']:<10s} [{sid}]")
    asserted = [sid for sid, r in rows.items() if r["status"] == ASSERTED]
    para("An ASSERTED stop is one nobody has been carried to. It was reasoned,",
         "not measured, and the repo says so rather than letting a claim pass",
         "for a boundary.",
         "",
         f"So building this mast and recording what happened would measure "
         f"{len(asserted)} of these.",
         "That record goes in data/rosetta/transfers.jsonl:",
         "",
         "      outcome     HELD | PARTIAL | BROKE",
         "      broke_at    where it stopped working",
         "      verdict_on  SCOPE_CONFIRMED if it broke at a stop already stated;",
         "                  ENTRY_SCOPE if it broke somewhere the entry does not",
         "                  mention, in which case the entry gets that stop added",
         "",
         "      python -m rosetta_shape_core.scope --stops",
         "      python -m rosetta_shape_core.transfer --audit")

    rule("THE WHOLE THING IN FOUR LINES")
    para("1. name the loads in physical terms          (families.py)",
         "2. name which one SETS the configuration     (--dominant)",
         "3. port the move, never the ontology         (rosetta.py)",
         "4. carry the stops, and record what happened (scope.py, transfer.py)")
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
