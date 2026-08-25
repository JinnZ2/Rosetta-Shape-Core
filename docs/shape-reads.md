# Shape reads

Read [`METHOD_SPEC.md`](../METHOD_SPEC.md) first — it states the epistemic
class, and the short version is that **constraint-set reasoning is a method,
not a claim, so it is not falsifiable and does not need to be.** The
falsifiable layer is the individual read, which is why `removal_test` is
required here and why a record without one is demoted rather than accepted.

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


---

## Confidence is a separate readout

A read at 0.4 is not a claim held at 0.4 — it is an uncoalesced marker with
a stated gradient, and is not to be resolved in either direction on its
behalf. `confidence.basis` is a closed vocabulary:

| moves it | |
|---|---|
| up | `REMOVAL_TEST_PASSED`, `TRANSFERRED_OUT_OF_DOMAIN`, `SCALE_HELD` |
| down | `REMOVAL_TEST_FAILED`, `CONSTRAINT_NOT_LOAD_BEARING` |

`RECURRENCE_COUNT` is deliberately absent and **rejected at validation**. A
read is not upgraded by more instances sharing the geometry without a
checked constraint set — that is the blocked misread wearing a number.

## Disappearance is underdetermined, not falsifying

A shape appearing tells you the constraints were met. A shape disappearing
tells you at least one was removed, **but not which**.

Reporting a disappearance as a failed pattern reports the wrong finding: it
is the constraint set being changed. `WRONG_FINDING` fires on a read marked
`refuted` whose negative evidence is a disappearance rather than a removal
test that came back `unchanged`.

A timestamped intervention is the handle. `UNBOUNDED` fires on a
disappearance with no `since`, and again when a timestamp exists and no
candidate set has been bounded by it.

## Substrate exclusion

If a domain is out of the sample frame the recurrence check cannot run there
by construction, and returns a null that reads as absence. `EXCLUDED`
reports any `sample_frame.excluded` domain as **untested, not
inapplicable**.

## The shadow read

Often the geometry is not visible, because the constraint that would make it
visible is the one nobody is measuring. A shadow read describes the shape by
**the gaps it casts**: each `tangent` is one gap, and the object is what they
are all tangent to.

- `read_path: shadow` requires `tangents` and an `outline_state`
- a shadow read may have an empty `geometry`; a direct read may not
- it still carries a removal test — the falsifiable layer does not move
- `under_outlined` is a stated state, not a failure, and `status: tested` on
  one is rejected

**Tangents are not competing claims.** `ShapeRead.consistency_exempt` is true
for shadow reads: an internal-consistency audit pointed at one reports
conflicts that are not conflicts. See
[`READING_PROTOCOL.md`](../READING_PROTOCOL.md), third blocked conflation.
