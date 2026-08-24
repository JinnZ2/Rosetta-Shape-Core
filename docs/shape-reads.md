# Shape reads

The definition lives in [`SHAPE_SPEC.md`](../SHAPE_SPEC.md) at the repo root.
It is upstream of every repo in the ecosystem that uses the word, it is CC0,
and section 10 says to point at it rather than restate it. This page is only
how *this* repo implements it.

```bash
python -m rosetta_shape_core.shape_read --list
python -m rosetta_shape_core.shape_read --audit
python -m rosetta_shape_core.shape_read --classify-shapes
```

## Two record kinds, and what separates them

| | |
|---|---|
| **shape entry** | carries solving-for, a constraint list, why-not-the-other-geometry, and a removal test |
| **geometry note** | missing the removal test. Marked as one, not rejected |

`schema/shape_read.schema.json` requires all four. Records live in
`data/rosetta/shape_reads.jsonl`.

**All six files in `shapes/` are geometry notes.** They carry faces, edges,
vertices and no constraint set, and each now says so in the file itself
(`read_class: geometry_note`). That is a marking, not a criticism: a vertex
count is a true statement about a polyhedron and says nothing about what
problem the polyhedron solves.

## Where the checks bite

| finding | section |
|---|---|
| `GEOMETRY_NOTE` — record missing the removal test | §10 |
| `OPTIMUM_READ` — an external, heterogeneous constraint with the problem stated as an optimisation | §5 |
| `COST_FRAMING` — a constraint stated as a cost rather than as dissipation | §9 |
| `LENGTH_NOT_RATIO` — a constraint stated as a length with no ratio | §9 |
| `NO_RECURRENCE` — no independent recurrence listed | §6 |
| `NO_SCALE_INDEX` / `DRIFTS` — no characteristic scale, or one that drifts across levels | §8 |

A removal test that comes back `unchanged` forces `status: refuted` at
validation — the constraint was not load-bearing and the read is wrong. That
is a valid record, not a rejected one.

## Where the operator already sat

`rosetta.py` licenses transfer on shared **forcing terms**, which are a
constraint set — so it was already licensing on the shape in the sense §1
defines, not on the geometry. Its weakest grade, `SHARED_FORM`, is exactly
two geometries coinciding with no common term named: the misread §2 blocks.
It is withheld by default rather than ranked last. The vocabulary in that
module now says which of the two it means.

`scope.py` grades **tokens**, which name geometries. The token and the
constraint set are graded separately on purpose: a token can be adequate
while the constraint set is unnamed, and a constraint set can license a
transfer with no token at all.

## The three shipped reads

| id | status | why |
|---|---|---|
| `BRANCHING_UNDER_ENCLOSURE` | tested | the enclosure removal test is run against river networks and the form differs |
| `SPIRAL_UNDER_ROTATION` | tested | angular momentum removed, vasculature branches instead |
| `DELTA_ON_HETEROGENEOUS_SUBSTRATE` | marker | the removal test is **stated and not run**. Its constraint is external and heterogeneous, so its geometry is a transcript of terrain rather than an optimum |
