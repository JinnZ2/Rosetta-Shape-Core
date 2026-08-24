# Worked example — one problem, end to end

```bash
python examples/rosetta_walkthrough.py
```

The script carries a single problem — *a roadside mast that has to survive
wind loading* — through T2 → T1 → T4, and shows three wrong readings beside
the right one. Nothing in it is hardcoded: every result is computed from the
shipped data, so it changes when the entries change and fails loudly rather
than teaching something that is no longer true.

Read it if you are arriving at this repo and want one thing you can run that
produces a result you can check.

---

## The four steps

| | step | where |
|---|---|---|
| 1 | name the loads in physical terms | `families.py` |
| 2 | name which one **sets** the configuration | `--dominant` |
| 3 | port the move, never the ontology | `rosetta.py` |
| 4 | carry the stops, and record what happened | `scope.py`, `transfer.py` |

Most of the value is in the first two, which are the ones people skip.

## The three wrong readings

**A — porting the ontology instead of the move.** *"Grass has learned to
survive wind, so the mast should be intelligent the way grass is."* Nothing
follows from it, because it is a claim about what grass *is*, and the
operator never made one. What transfers is a single operation.

**B — matching on a term that shapes neither system.** Call it "a strain
problem" and the results fill with entries whose configuration really is
strain-set — a comb, a soap film, a bone — while the one entry that answers
the problem drops to the bottom and grades `SHARED_PRESENT`. The cost of
misnaming the load is not a lower score; it is a reordering that buries the
answer under three plausible ones.

**C — porting the move and dropping the stops.** *"Grass bends, so build a
mast that bends."* The move is right and the reading is still wrong: the
first stop — *where stiffness is the function* — decides the case for a mast
that has to hold a sign steady, and the third — fatigue life under the cycles
compliance introduces — is the one that bites later. The stops are not
caveats attached to the move. They are the measurement of where it produces.

## What the last step is for

The walkthrough ends by showing that all three of that entry's stops read
`ASSERTED` — reasoned, never carried to. Building the mast and recording the
outcome in `data/rosetta/transfers.jsonl` is what turns one of them into
`MEASURED`, or adds a stop nobody had written down.

That loop is the point. See [`rosetta-operator.md`](rosetta-operator.md) for
the machinery.
