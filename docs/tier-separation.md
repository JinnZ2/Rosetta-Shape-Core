# Tier separation — domains of the world, and ways of knowing

> **Status: MARKER UNDER EXPLORATION.** Not a settled ontology. Expected to
> change after experiment. Not to be enforced as an invariant.

```
f01–f20   are domains OF the world.
a01…      are domains of REPRESENTATIONS of it, or routes by which a
          reading is obtained.
```

Different tier. Not a further face.

## The diagnosis

`f21-narrative-constraint` did not fit the family set, and the reason is one
line: **f01–f20 are domains of the world; f21 is a domain of representations
of it.** It was never overflow past the icosahedron's twentieth face — it was
the first member of a second set, written into the first set's file format
because that was the only format available.

Two of the three files that describe the family set had already excluded it,
without anyone deciding to:

| file | what it said before the move |
|---|---|
| `ontology/index.json` | `count: 20`, registry of 20, five_fields of 20 — **F21 appears nowhere in it** |
| `ontology/_id_registry.json` | *"Equation-domain families F01-F20, mapped to icosahedron's 20 faces"* |
| `ontology/family_map.json` | carried F21 — in the affinity model and in four shape profiles |

Only the third one held it. `SHAPE.ICOSA.all_equation_families` was the single
place where the count read 21; it now reads 20.

## What moved

`ontology/families/f21-narrative-constraint.json`
→ `ontology/access/a01-narrative-constraint.json`

The equations, symbol, resonances, explore paths and tags carried over
verbatim. `channel`, `operation`, `valid_on` and `breaks_when` were written
during the move and are the fields to check first.

The record keeps `derived_from: FAMILY.F21`. A slug carries a content pointer
*and* a record of which gate it got past; a move that drops the pointer
orphans the second. The old id still resolves.

The code tables that keyed on `FAMILY.F21` — sensor context, vertex loading,
shadow capability — were re-keyed to `ACCESS.A01` rather than deleted, so the
capability moved with the record.

## The schema

`schema/access.schema.json`. Required: `id`, `name`, `tier`, `channel`,
`operation`, `valid_on`, `breaks_when`, `cost`, `lands_on`, `status`.

**`breaks_when` is mandatory and may not be null.** An access entry with no
stated break point is a preference, not an access mode, and is rejected at
validation.

`channel` is `residual | transmitted | unmarked` — the world pushed back on
your own reading; it was taught or given, carrying the source's observer
without the receipts; or it is not recorded.

## The flag that motivated this

```
a01 narrative-constraint
    cost:      free
    lands_on:  measured
```

Cheap travel to an expensive destination. **That mismatch IS the detector.**
No judgement term is needed, and `tier_check` states it as a mismatch and
claims nothing further about it.

## What is deliberately not built

- no `face_assignment` on access entries
- no fixed count, no polytope closure, no duality or incidence check
- no solid re-derived from the number of files present

The access tier admits new members without restructuring. **That is the
requirement, not a limitation.**

## The checks — `tier_check.py`

```bash
python -m rosetta_shape_core.tier_check
```

| | check |
|---|---|
| **fail** | a way of knowing filed in `ontology/families/` |
| **fail** | an access entry with a null or empty `breaks_when` |
| **warn** | `cost=free` with `lands_on=measured` |
| **warn** | an entry that claims a domain and names no access |

The first check is a vocabulary detector, deliberately narrow: it fires on
*account*, *narrative*, *rationalization*, *selective application*,
*manipulation* — things with a teller. Measurement, Information and
Consciousness are domains **of** the world and must not trip it; there are
tests pinning that, because a detector that fires on F14 would be useless.
`REVIEWED_AS_DOMAIN` records any family checked and kept, with the reason. It
is currently empty: no f01–f20 family trips a marker.

## The holding record

Three optional fields on a Rosetta entry:

```json
"domain": "f05", "access": "a01", "acquired": "unmarked"
```

`unmarked` is a legitimate value and **is expected to dominate**. An absent
`acquired` reads as unmarked. Nothing was backfilled: all 231 entries read
unmarked, and none claims a domain or an access, because a guess about how a
reading was obtained is exactly the kind of thing that becomes unrecoverable
once it is written down.

Claiming a domain while naming no access is a warning — *unmarked* is an
answer, a missing field is not the same thing.

## Candidates

`ontology/access/_candidates.json` holds a02–a06 from the thread that
produced the tier. **None of them is a member**: each needs `breaks_when`
written before it enters, and the underscore keeps the file out of the tier
the way `ontology/_vocab.json` stays out of the entity set.

| | | |
|---|---|---|
| a02 | residual | the world pushes back on your own reading |
| a03 | transmission | taught or given. Carries the source's observer, not the receipts |
| a04 | borrowed-instrument | read another observer's response rather than the world directly |
| a05 | derivative-read | read *change* in an uninterpretable channel. No decoder required |
| a06 | threshold-integration | accumulate, respond at dose |
