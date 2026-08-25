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

## The discriminator — cost cannot tell a01 from a03

Both are cheap to acquire and both land on `measured`, so the cost-mismatch
flag fires on both and **cannot tell them apart**.

| | |
|---|---|
| **a03 transmission** | the source *paid*. Receipts exist upstream; they just did not travel with the holding |
| **a01 narrative** | nobody paid anywhere. No upstream receipt exists to recover |

The discriminator is not cost. It is **recoverability**: can you, in
principle, walk back to a residual event? Yes → transmission with lost
receipts. No → narrative. `receipt_recoverable` is required on any access
mode that is cheap and lands on a measured claim, because without it the two
collapse.

```
a01  receipt_recoverable: none
a03  receipt_recoverable: in_principle
a07  receipt_recoverable: n/a
```

a03's own `breaks_when` closes the loop: *"receipts unrecoverable in fact,
not just absent in transit — then it is a01, reclassify."* Its
`uptake_decays_when` states the mechanism — when no hop records the path,
recoverability degrades to `none` and the holding has become a01 whether or
not anyone reclassifies it.

## a07 — the third channel

`residual` is new input from the world. `transmission` is new input from
another observer. **a07 internal-consistency takes no input at all** —
`channel: none` — and produces real information anyway: if two holdings are
inconsistent, at least one is wrong, and you did not know that before
looking.

The asymmetry that defines it: **an audit can only refute.** Passing means
"no contradiction found among what I hold", which is also what a fully
coherent wrong set returns. So it lands on `refuted | unresolved` and never
on `measured` — the one channel where a null result is genuinely null.

Its sub-modes both fired while this repo was being built: `d1_dimensional`
caught a memory equation integrating to Pa·s rather than strain, with no
measurement taken; `d2_semantic` caught *stale* carrying both
confirmed-stable and unrefreshed, *message* carrying both emission and
uptake, and *family* carrying four vocabularies in one repo. None of those
fail dimensionally, and each was hiding a confidence error.

## Uptake maintenance — the blind spot written into a schema

Every access mode states `uptake_maintained_by` and `uptake_decays_when`. A
mode with no maintenance requirement stated is assumed permanently
available, and that assumption is uptake decay written into the schema as an
absence. `tier_check` warns on a null.

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


---

## Holdings and trajectories

A trajectory needs a derivative, so `holding.py` records whatever makes one
computable from the record alone — two observations minimum with the gap
between them readable. Contacts are **recorded**, not judged at write time,
and **no trajectory is ever written into the file**: a stored trajectory is a
judgement frozen at the moment of writing. Validation rejects one.

| trajectory | marker | reading |
|---|---|---|
| `DECAY` | now − last_residual, over referent_rate | the **ratio**, not the age. 400 days on a slow referent is fine; 40 on a fast one is already gone. The only motion needing no event — an absence of contacts *is* the signal |
| `TOWARD_UNKNOWN` | supports decayed past their own ratio | the holding is intact and its ground is not. Reads as held, is not |
| `STALE_CONFIRMED_STABLE` | recent residual contact, all confirmed | flat because the referent is flat. High confidence |
| `STALE_UNREFRESHED` | no residual contact | flat because nobody looked |
| `TOWARD_LEARNING` | a `discrepant` residual contact | discrepancy is the **only** entry carrying new information; `confirmed` adds confidence and no content |
| `TOWARD_CIRCULATION` | restatements high, last_residual old or absent | motion in the record, none at the referent. Looks like learning in any activity metric |
| `TOWARD_OSSIFICATION` | scope_misses high, discrepancies flat | applied further outside its range without generating discrepancies — which means they are not being *recorded* |

**Conflating the two `STALE`s is the failure the tier exists to catch.** An
unlooked-at holding reads exactly like a confirmed one unless the
discriminator is enforced, and the discriminator is one field: recent
residual contact. There is a test pinning that they never both fire.

**`referent_rate` is the one thing not derivable from the record.** Best:
measured, from repeated residual contact. Usable: inherited from the domain.
Default `unknown` — and unknown must **not** silently become `slow`. An
unknown-rate holding is not a fresh one. With the rate unknown the system
reports order, not magnitude, and says so rather than filling the field.

### Circulation

N holdings citing one another in a cycle with zero residual anchors reads as
N-fold confirmation and is depth-N transmission of one unverified holding.
The rule: **for any cluster, require at least one path terminating in a
residual contact. No such path → flag CIRCULATION, do not flag as false.**

### Decay is three things

| | | correct response |
|---|---|---|
| `d1_referent` | the world changed. The holding is now wrong | re-measure |
| `d2_receipt` | holding intact, support gone | re-derive |
| `d3_uptake` | referent unchanged, emission unchanged, still fully available — and the receiver no longer resolves it | **re-train the instrument** |

Only d1 is decay of information. d2 is decay of provenance. d3 is decay of
the instrument, filed as decay of the world — and `now − last_residual`
cannot see d3 at all, because d3 leaves the record untouched. A skill
unpractised, a language not spoken, a landscape stopped being read: full
availability, zero uptake.

All three feel identical from inside, and d3 is the only one whose correct
response is aimed at the observer, so it is the one misdiagnosed in the
direction that costs nothing. *"The signal is gone"* is free. *"I stopped
hearing"* costs. Default is `undiagnosed`, **never d1**, and the audit flags
a decayed holding with an undiagnosed class and no cross-observer check as
`PREMATURE_D1`.

The discriminator needs no decoding: **does another receiver still resolve
it?** Yes → the loss is at your end. Nobody does → either d1 or a
population-wide d3, which is indistinguishable and is the dangerous case,
because "nobody hears it" reads as "nothing is being said."

---

## Curiosity — the allocator

```
decay     free. Runs with no input. Always on.
contact   expensive. Requires initiation.
```

Nothing in the record initiates. The trajectory system detects motion it
cannot cause, so without an allocator only decay runs and the apparatus is a
well-instrumented record of its own deterioration. That makes curiosity a
**budget allocation function over the flag queue**, not a disposition —
which is what makes it specifiable.

```bash
python -m rosetta_shape_core.curiosity --triggers
python -m rosetta_shape_core.curiosity --allocate --budget 10
```

Priority for expensive residual contact: `dependents × (age / referent_rate)`
— highest is load-bearing *and* most decayed. Unknown-rate holdings are
unrankable and are **reported rather than dropped**, because treating unknown
as slow would push exactly the unmeasured holdings to the bottom.

### The offset is mandatory

The flag queue surfaces `KNOWN_MISSING` and nothing else — the cheapest and
least informative gap class, and spending the whole budget there feels
productive the entire time.

| gap class | reach |
|---|---|
| `KNOWN_MISSING` | a07 internal audit. It flags itself. Cheap — this is what the validator queue *is* |
| `KNOWN_UNRESOLVED` | nothing internal; requires building an instrument. Expensive, and the productive class |
| `UNMARKED` | **nothing self-directed.** No internal signal exists for a channel you do not have. Only reach: cross-station comparison — the borrowed-instrument channel, a04 |

`UNMARKED` is unreachable by any ranking computed over current holdings,
because the ranking is built from the very set that excludes it. So a fixed
fraction of budget goes outside the queue entirely — unranked, unjustified,
not derived from existing holdings. **`allocate()` refuses an offset of
zero**, because zero is not an aggressive configuration, it is a closed one.

> These gap classes are **not** `gap_scan`'s G1–G4. That module numbers four
> gap *shape* classes on a cross-instance axis. These are a different thing
> on a different axis, and they are spelled out rather than numbered so the
> two sets cannot merge. A test pins it.
