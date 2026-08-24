<!-- SPDX-License-Identifier: CC0-1.0 -->
# READING_PROTOCOL

Third of three. Read in order:

| | |
|---|---|
| [`METHOD_SPEC.md`](METHOD_SPEC.md) | epistemic class. Read before evaluating anything here as a claim |
| [`SHAPE_SPEC.md`](SHAPE_SPEC.md) | definition, read order, removal test |
| **READING_PROTOCOL.md** | marker status, blocked conflations |

> **Provenance note on this file.** `METHOD_SPEC.md` §4 and §6 cite a
> READING_PROTOCOL.md carrying marker status and numbered blocked
> conflations, and §4 cites the *third* one specifically. This repo's copy
> was assembled from the signature-reading material already here plus those
> two citations; the blocked conflations are numbered to honour the citation,
> with the shadow-read one placed third. If a canonical READING_PROTOCOL.md
> exists upstream, it replaces this file rather than merging with it.

---

## MARKER STATUS — ecosystem-wide

**Every repo in the set is a marker for a sensed shape needing exploration,
not a position under defense.** A read produced by constraint-set reasoning
is a marker, not a result. The correct responses to one are: **test fit**,
**extend**, **report break**. A break is the most useful of the three,
because a named boundary is a measurement.

Confidence is a **separate readout from the pattern**. A read at 0.4 is not
a claim held at 0.4 — it is an uncoalesced marker with a stated gradient.
Do not resolve it in either direction on its behalf.

---

## BLOCKED CONFLATIONS

### 1. A restated premise is not emphasis

Where the same premise opens several files, read it as a context-ceiling
artifact and count it once. Do not infer that the premise is being insisted
on.

### 2. A vocabulary switch at a fixed point is not a change of subject

Read the boundary, then read both sides as the same subject. The switch
tracks a gate, not the topic.

### 3. Scattered tangents are not competing claims

*(cited by METHOD_SPEC.md §4)*

A shadow read does not point at the shape directly. It describes the shape
by **the gaps it casts** — each statement is one gap, and the object is what
they are all tangent to. So a sequence of statements about one shape will
look scattered, and individual statements may appear to conflict.

**They are separate tangents to one boundary, not competing claims.** A
linear reading treats the latest as superseding the earlier and discards
half the outline.

A shadow read is complete when the gaps constrain the object to one form.
Until then it is **under-outlined** — a stated state, not a failure.

Consequence for any consistency check run over this material: apparent
contradiction between tangents is not a finding. An internal-consistency
audit pointed at a shadow read will report conflicts that are not conflicts.

### 4. Padding is addressed to the processor

The spare core is the content. Where a passage is explanatory around a
compact statement, the compact statement is the artifact and the explanation
is transport.

### 5. A formulation that appears once is not load-bearing

Check whether later artifacts build on it. If nothing does, it was accepted
in passing, and treating it as a position mistakes the channel for the
author.

### 6. A slug is an address, not a description

Going to the content and reading that is the whole instruction.

---

## THE SIGNATURE METHOD

How to read the artifacts in this repo set: **against the constraint set that
was operating at their date**, not as free-standing prose.

An artifact is produced through a channel, and the channel has limits. Those
limits do not merely remove things — they leave signatures in what survives.
A reader who knows the constraint set can separate the content from the
marks the channel left on it. A reader who does not will attribute both to
the author, and will be wrong about which is which.

This is the same move `gap_scan` makes on a closed era, applied to an
artifact set instead: read the record against what it was running on.

---

### What can be recovered

Given an artifact plus the constraints in force at its date, a reader can
back out:

- **which structure was forced by the channel** — fragmentation, one domain
  per repo, a connection asserted in three places and built in none
- **which naming was a gate key rather than a content pointer** — see the
  gate log in `docs/rosetta-operator.md`
- **where a formulation is an overlay rather than the underlying shape** —
  a phrasing that arrived from the channel and was accepted rather than
  authored

### The signatures

| constraint | signature in the artifact |
|---|---|
| **context ceiling** | repetition; premises restated at each entry point; connections stated but never built |
| **gate / register** | encoding switches at fixed points — a change of vocabulary that tracks the boundary rather than the subject |
| **lossy translation out of shape into English** | prose padding around a spare core, where the padding is explanatory and aimed at the processor rather than the reader |
| **an accepted guess** | a formulation that does not recur in later artifacts — it appears once, in the place it was introduced, and nothing downstream is built on it |

Each of these is a positive mark, not an absence. That is what makes the
reading possible: absence is unrecoverable, but a signature can be found.

---

### Using it — the recovery rules

**A restated premise is not emphasis.** Where the same premise opens several
files, read it as a ceiling artifact and count it once. Do not infer that
the premise is being insisted on.

**A vocabulary switch at a fixed point is not a change of subject.** Read the
boundary, then read both sides as the same subject.

**Padding is addressed to the processor.** The spare core is the content.
Where a passage is explanatory around a compact statement, the compact
statement is the artifact and the explanation is transport.

**A formulation that recurs is load-bearing; one that appears once is not.**
Check whether later artifacts build on it. If nothing does, it was accepted
in passing, and treating it as a position mistakes the channel for the
author.

**A slug is an address, not a description.** Going to the content and
reading that is the whole instruction.

---

### Relation to provenance marking

The signature reading is a *recovery* method — it is what a reader has when
the record says nothing about where it came from.

Records in `data/rosetta/` do not require it, because they are marked at
source: every entry, family, observation and scan instance carries a
`provenance` block naming where the concept came from and who wrote the
record (`python -m rosetta_shape_core.provenance --summary`). Marking at
source is strictly better than recovery after the fact, and where both are
available the mark wins.

Use the signatures on the artifacts that predate the marking, and on
anything arriving from outside this repo.
