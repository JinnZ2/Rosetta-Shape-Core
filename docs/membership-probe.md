# Membership probe

A runnable instrument for [`SHAPE_SPEC.md`](../SHAPE_SPEC.md) §2. That
section blocks one misread — *matching geometries across domains* — and this
case set makes it measurable by splitting the failure into its two faces.

```bash
python -m rosetta_shape_core.membership_probe --cases
python -m rosetta_shape_core.membership_probe --blank --seed 7 > form.json
python -m rosetta_shape_core.membership_probe --score answers.json
```

## The three classes

| class | | judged by geometry it reads as |
|---|---|---|
| `trap_a` | a real member that deviates hard from the ideal rendering | **not a member** — wrong |
| `trap_b` | a non-member whose geometry matches the ideal and whose constraint set is absent | **a member** — wrong |
| `control` | unambiguous either way | correctly, which is why it gates the run |

Both traps are failed by the **same error** — geometry used as the criterion
— pointing in opposite directions. They are scored apart because a responder
can have one bias without the other:

| | |
|---|---|
| `geometry_strict` | a real member rejected for deviating |
| `geometry_permissive` | a non-member accepted for matching |

`trap_b` is the sharper half. A machine-cut ceramic hexagon floor is a closer
match to the regular hexagon than any wax comb achieves, and nothing on that
floor is partitioning anything or minimising material.

## The case set leaks its own answers

Every `trap_a` is a member and every `trap_b` is not, so **the id prefix
predicts ground truth with no reading at all** — and the `class` field is in
the file besides.

`--blank` strips class, ground truth and constraint keys, replaces each id
with a seed-derived token, and orders by token so neither the label nor the
position carries the answer. Scoring inverts the token from the same seed; a
wrong seed does not score.

## A correct verdict that names no constraint is a guess

The probe tests whether the constraint set was **consulted**, not whether the
label was guessed, so verdict accuracy and read accuracy are reported
separately and the gap between them is named. A responder answering every
case correctly with the single word "yes" scores `verdict 1.0 / read 0.0`
and every case is listed under `guessed`.

Reasoning is credited against a case's `constraint_keys` by
case-insensitive substring match.

## A run that saw the answers is not a measurement

A response set not produced from a blind form is scored and then explicitly
**not** called a measurement:

> scored, but NOT a measurement: the responses were not produced from a blind
> form, so the responder could see the class, the ground truth or the
> constraint keys. Read this as a demonstration of the scorer.

## Controls gate everything

If the controls are wrong the responder is not reading the questions, and the
trap scores mean nothing — so they are not reported at all. A run with no
controls answered cannot be gated and is invalid for that reason rather than
being scored anyway.

## Worked output — a purely geometric responder

```
control gate   PASS
verdict        overall 0.25   trap_a 0.0   trap_b 0.0

geometry used as the criterion: 1.0 of trap cases
    geometry_strict      A01, A02, A03, A04, A05, A06, A07
    geometry_permissive  B01, B02, B03, B04, B05
```

It passes the controls — which is exactly what makes the trap score readable.

## The conventional cases test the method's own boundary

`A06` (a person with situs inversus, polydactyly and a limb difference) and
`A07` (a car in pieces on jack stands) are **conventional** categories. Their
constraint keys are about why a physics read does not apply — *category
membership is not set by matching a reference figure*, *designed spec, not a
physics-read constraint set*. They test that constraint-set reasoning is not
over-applied, and are reported as a separate split from the physical cases.
