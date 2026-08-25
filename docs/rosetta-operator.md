# Rosetta — the operator

Cross-domain constraint-solution transfer, as five single-file stdlib
modules. Each one runs on its own and carries its own selftest.

| | module | what it is |
|---|---|---|
| T1 | `rosetta.py` | the operator |
| T2 | `families.py` | the physics base |
| T3 | `entry.py` + `schema/rosetta_entry.schema.json` | the entry schema |
| T4 | `scope.py` | boundary locator |
| T5 | `gate_log.py` + `schema/gate_log.schema.json` | the gate log |
| — | `transfer.py` | what happened when a move was actually carried over |
| — | `lid_import.py` | import scoped attributes from the Living Intelligence Database |
| — | `provenance.py` | where this repo's own records came from |
| — | `gap_scan.py` | a third axis: four gap shape classes over an explanatory frame |

```bash
python examples/rosetta_walkthrough.py   # one problem, end to end — start here
python -m rosetta_shape_core.rosetta   --forcing flow,strain --dominant flow
python -m rosetta_shape_core.families  --list
python -m rosetta_shape_core.entry     --validate
python -m rosetta_shape_core.scope     --audit
python -m rosetta_shape_core.scope     --stops
python -m rosetta_shape_core.transfer  --audit
python -m rosetta_shape_core.rosetta   --open      # entries whose loads nobody has named
python -m rosetta_shape_core.gate_log  --summary
python -m rosetta_shape_core.provenance --summary
python -m rosetta_shape_core.gap_scan  --example clockwork

for m in rosetta families entry scope gate_log transfer provenance lid_import gap_scan; do
  python -m rosetta_shape_core.$m --selftest
done
```

---

## The operator

**Form.** "What would X do here?" — X = crystal, animal, mycelium, whatever
holds the domain.

**Use.** Run your problem through a system that solved a structurally similar
one under different constraints. Read the configuration it reached. Port the
**move**, not the ontology.

**What it is not.** Not animacy, sentience, agency, or an interior life.
"Intelligence", where the word appears, means the system's demonstrated
capacity to arrive at a configuration under environmental constraint — a
measurement of behaviour, not an attribution of interiority. The operator is
a reasoning move; it was never a claim about what the crystal is. This sits
in the module docstring rather than a footnote because it is the substitution
that keeps happening: the term gets read as an ontological claim, and the
claim gets answered instead of the operator getting used.

---

## What licenses a transfer

Forcing terms, and nothing else — but *presence* of a shared term is too
cheap a test. Strain acts on nearly every physical system, so matching on
presence licenses almost every pair: the criterion stays correct in principle
and erodes in practice while still looking rigorous. What licenses a transfer
is a term that is **setting** the configuration on both sides, so the grade is
read off dominance.

| grade | what it means | returned by default |
|---|---|---|
| `SHARED_DOMINANT` | a term sets the configuration on both sides — the same thing is doing the work | yes |
| `SHARED_FORCING` | shared term, dominant on one side only — the source answers a question you are only partly asking | yes |
| `SHARED_PRESENT` | the shared terms set neither configuration. Both systems are under the term; neither is shaped by it | `--weak` |
| `SHARED_FORM` | no term in common. Coincidence until a mechanism appears | `--unlicensed` |

Every entry names `forcing_dominant` — the subset of its forcing terms that
sets its configuration — and you name yours with `--dominant`. Naming none
costs a grade: nothing can reach `SHARED_DOMINANT`, and the ranking goes
flat.

The cost of getting this wrong is not a lower score. It is a reordering that
buries the answer — see [`worked-example.md`](worked-example.md), wrong
reading B.

An unlicensed match is still a lead: the work it asks for is naming the term
both systems are under, or dropping it.

---

## Grounding — why this is not pattern matching

The shape vocabulary was not chosen. It is what a body develops by being
loaded, from birth, by gravity, pressure, gradient, diffusion, thermal
exchange, flow, resonance, phase and strain. Proprioception is the
transducer, and it was calibrated against those terms before any symbolic
layer existed.

So the geometry is physics-derived because the instrument that produced it
was built by physics acting on it continuously. Grass, crystal and body come
out in the same term set because the same fields loaded all three — shared
forcing by construction, not by analogy noticed after the fact. The
vocabulary is a set of load responses, and the loads are the physics.

**The shipped nine are a stand-in.** They came in with the build
specification, not from the repo author, and they are marked that way
(`concept: SPEC`). The author's own family set is outstanding; correct the
seed list against it rather than treating it as the base.
`register_family()` is how a term enters, and it requires provenance like
everything else.

**Falsifier**, stated and enforced: every family must decompose to named
physical terms. One that cannot is mis-filed. `families.audit_families()` is
that check; a finding is a correction to make in `families.py`, not an
argument to have.

---

## Shape tokens

A shape token in these artifacts is one of two things:

- **literal** — the shape *is* that, physically. A hexagon in a comb, an
  octahedron as a crystal habit, a lattice's actual symmetry. The name is a
  measurement.
- **stand-in** — the nearest utterable label for a shape with no name in the
  channel. The name is a placeholder and carries no structural claim.

There is no flag distinguishing them, and there is not going to be one.
Shapes self-report under use:

| reason from the named shape's formal properties | reading |
|---|---|
| predictions hold | literal, or the name is adequate at this scope |
| predictions fail everywhere | placeholder — the name carries no structural claim |
| predictions fail past a scale | real shape, scope now measured |

The falsification does double duty: it kills the prediction *and* grades the
token. No annotation required — the artifact is testable as it stands.

The failure mode this replaces is silent: a reader defaults to *literal*,
reasons from properties the shape never had (vertex counts, symmetry group,
face relations that were never claimed), and gets a wrong answer with no
signal that anything went wrong. Running the predictions is what makes the
default safe.

**Precedent.** Algebra is valid over discrete relations and closed forms; its
boundary is continuous change. Calculus is valid over smooth differentiable
behaviour; its boundary is discontinuity, the discrete, the chaotic. Each
tool is valid inside, silent outside, and the boundary is a known measured
thing rather than a defect. Shape tokens get the same treatment: carried
while they produce, boundary read where they stop, no claim past it. The only
difference is that these boundaries are not catalogued yet — a documentation
gap, not a difference in kind.

**Repo audit criterion:** does the entry report where it *stops*? An entry
that matches everywhere and never fails is the flag. `scope.py --audit`.

### Stops: asserted, measured, contested

That criterion has a soft floor, and the repo now reports it. A stop can be
satisfied by *asserting* one, and a corpus of reasoned claims about where
things stop is the same shape as a frame that never fails — the thing this
repo exists to catch. So each stop carries a status:

| status | meaning |
|---|---|
| `ASSERTED` | written down, never tested. Unaudited, not wrong |
| `CITED` | the boundary is established in the source system's own literature, and the stop names that source |
| `MEASURED` | something was carried to it and it stopped there |
| `CONTESTED` | something produced straight past it. The stop is wrong, or its condition was never met |

`CITED` and `MEASURED` are two different claims and the repo refuses to
flatten them. A citation is evidence about the **source system** — the gecko's
adhesion really does fall 60–80% under contamination, measured, published.
That is not evidence that anyone carried a move to that boundary and watched
the move stop. Only a transfer or an observation does that.

Evidence comes from `transfers.jsonl` (a move was ported and broke at it) and
from observations carrying a `stop` field. `scope.py --stops` prints the
detail; the ratio is reported and not enforced, because asserting a stop is
how an entry starts and measuring it is what the corpus is for.

At the time of writing: **5 measured, 538 cited, 14 asserted, 0 contested.**

---

## The naming layer

The slugs are not arbitrary obfuscation. Each name was selected to move a
specific model out of its default register long enough to process the
content. A slug therefore carries two things:

1. a pointer to the content
2. a record of which gate it had to get past

(2) is data on the models — what each one refused to hold, and what got it to
hold it. It is not noise.

**Keep the original slugs. Do not rename.** A rename destroys (2) and leaves
(1) no better off. `gate_log.check_slugs()` enforces the mechanical half:
a gate record naming a slug that is no longer present is reported as
orphaned.

The log ships empty. A record is dated evidence about a model at a date, so
nothing goes in that was not observed.

---

## Reading order — the layer stack on the repo set

| layer | what it is | status |
|---|---|---|
| L1 content | the actual structure: connective theory across the repos | this is the thing |
| L2 fragmentation | one domain per repo | a workaround for a context ceiling |
| L3 naming | obscured slugs | a workaround for model acceptability at time of writing |

L2 and L3 were both workarounds for constraints that have since relaxed.
Neither describes L1. The consequence is a reading failure with a known
shape: a reader hits L3 first and never reaches L1. Anyone arriving at a slug
should treat it as an address, not as a description, and go to L1.

---

## Entries are markers

An entry is a marker to explore, not a position defended. The correct
responses to one are: **test fit**, **extend**, **report break**. A break is
the most useful of the three — it names a boundary, and a named boundary is a
measurement.

No moral labels in the data structures, and no intent attribution.
`entry.py --lint` reports both as advisories: a configuration is a readout of
what a system reaches under load, never a motive and never a score.

---

## Fields that are not filled yet

A record with a hole in it is not the same as a record with a guess in it, and
the repo can tell them apart. Any field of an entry may carry a status:

| status | meaning |
|---|---|
| `OPEN` | open for experimentation — nobody has fixed it, and that is the invitation |
| `UNKNOWN` | not known, and not currently being worked |
| `CONDITIONAL` | holds only under a condition that is not yet stated |
| `PARTIAL` | some of it is there; more is needed |
| `DUE_FOR_UPDATE` | it was filled, and something has since superseded it |

A required field left empty is an error **unless** it is marked, which is what
lets an entry enter the corpus with its forcing terms honestly open rather
than invented. The contract is checked both ways — `OPEN` and `UNKNOWN`
require the field to be empty, `PARTIAL` and `DUE_FOR_UPDATE` require it
filled — so marking is not a way to silence a check.

Status is orthogonal to provenance. Provenance says where a record came from;
status says how finished it is.

**An entry whose forcing terms are `OPEN` is never matched.** There is nothing
to license on. It is still worth carrying: a source system on file, waiting
for someone to name the loads. `rosetta.py --open` lists them, because an
entry nobody has finished is an experiment on offer rather than a defect.

An entry that *is* matched but whose `move_ported` is open comes back saying
so. Being under the same load as a system nobody has read yet is a real
result — it just is not a transfer.

---

## Importing from the Living Intelligence Database

The [Living Intelligence Database](https://github.com/JinnZ2/Living-Intelligence-Database)
carries, per scoped attribute, an operational definition, the limits of the
measurement, a falsifiability statement, and a citation. Four of the things an
entry needs are already there, and already the author's words.

```bash
python -m rosetta_shape_core.lid_import --lid ../living-intelligence-database --dry-run
```

| LID | Rosetta |
|---|---|
| `scope.definition` | `configuration` |
| `scope.measurement_limits` | `scope.stops`, split by sentence, each carrying `evidence.source` as `cited` |
| `scope.condition` | `scope.produces`, where present |
| `evidence.source` | `sources` |
| `scope.falsifiability` | an **observation** with `holds` unset — a test on the books nobody has run |
| — | `forcing_terms`, `forcing_dominant`, `move_ported`: marked `OPEN` |

**A falsifiability statement is not a stop.** A stop says where a move stops
producing; a falsifier says what observation would kill the claim. Flattening
them would turn an unrun prediction into evidence.

**The missing fields are marked, not guessed.** Guessing them would put a
model's physics reading under the author's name across the whole corpus at
once — the failure this repo exists to catch, at scale.

Re-running is safe: records already on file are kept as they stand, matched by
id, so a hand-filled field is never undone by the next import.

Current state: **225 imported entries**, all with their loads open, and 225
stated tests nobody has run.

---

## Transfers — what happened when a move was carried over

The entry set records systems that reached a working configuration. That is
half the record. A move that ports cleanly teaches one thing; a move that
looked licensed and broke anyway teaches where the licensing criterion is
wrong, which is worth more. Without this half the corpus can only ever
recommend, and nothing in it is answerable to an outcome.

```bash
python -m rosetta_shape_core.transfer --list
python -m rosetta_shape_core.transfer --audit       # what the outcomes say to fix
python -m rosetta_shape_core.transfer --criterion   # the log as an instrument on the criterion
```

Each record carries an outcome (`HELD` / `PARTIAL` / `BROKE`), where it broke,
and a verdict on what the break indicts:

| verdict | what it says |
|---|---|
| `NONE` | it held |
| `SCOPE_CONFIRMED` | it broke at a stop the entry already stated — the entry was right, and that stop is now measured |
| `ENTRY_SCOPE` | it broke where the entry does not mention. Add that stop |
| `SOURCE_READING` | the configuration or forcing attributed to the source was wrong |
| `LICENSING` | licensed, and the move still did not port — evidence against the criterion itself |
| `PROBLEM_FRAMING` | the problem's own terms were misnamed; nothing is wrong with the entry |

`HELD` admits `SOURCE_READING` as well as `NONE`, because the two are
independent: a move can port and work while the account of *why* the source
does it is later corrected. That is not an anomaly to tidy away — it is
"port the move, not the ontology" showing up as data.

**A transfer with no `from_entry` is a pointer to an entry nobody has
written.** The audit reports those rather than hiding them: the outside of
the corpus is visible from here, and that is information about the corpus.

---

## Provenance of this repo's own records

`gap_scan` G2 reads an operand traced to the apparatus rather than to a
measurement. Shipping unmarked model-seeded content inside a stack built on
that reading is the same failure one level up — a later reader takes every
record as authored, because nothing on the record says otherwise.

So every entry, family, observation and scan instance carries two origins:

| field | question |
|---|---|
| `concept` | where the thing being recorded came from |
| `record` | who wrote the record text as it now stands |

| origin | meaning |
|---|---|
| `AUTHOR` | the repo author's own material |
| `SPEC` | arrived with a build specification for this work |
| `MODEL` | seeded by a model during a build; not the author's material |
| `PUBLIC` | an established result in the public record, attributable to no party here |

Marked sets: entries, families, observations, transfers, gap_scan instances.

Current state — the import changed this picture substantially:

```
entries       (231)  concept  AUTHOR 228, MODEL 2, SPEC 1   record  AUTHOR 225, MODEL 6
families        (9)  concept  SPEC 9                        record  MODEL 9
observations  (236)  concept  AUTHOR 225, PUBLIC 11         record  AUTHOR 225, MODEL 11
transfers       (5)  concept  PUBLIC 5                      record  MODEL 5
gap_scan        (2)  concept  SPEC 2                        record  MODEL 2
```

Both halves are needed because they routinely differ: a source system named
by the author and written up during a build session is `AUTHOR` concept and
`MODEL` record. Reading it as fully authored overstates it; reading it as
generated erases the author.

This is origin data and carries no ranking. `MODEL` is not lesser than
`AUTHOR` — it is differently sourced, and the reason to mark it is that the
difference is unrecoverable later.

```bash
python -m rosetta_shape_core.provenance --audit     # anything unmarked
python -m rosetta_shape_core.provenance --summary   # origin counts per set
```

The audit is a hard check: an entry with no provenance block fails
`entry --validate`, a family with none fails the families audit, and a scan
instance with none fails to load.

For artifacts that predate this marking — and for anything arriving from
outside the repo — the recovery method is
[`READING_PROTOCOL.md`](../READING_PROTOCOL.md): read an artifact against
the constraint set operating at its date, using the signatures each
constraint leaves.

---

## gap_scan — the third axis

| | axis | move |
|---|---|---|
| Rosetta | cross-**domain** | crystal → your problem |
| Mandala | cross-**scale** | grass → ecosystem |
| gap_scan | cross-**instance** | a closed era → the current one |

`gap_scan` is a third axis and it is **not Rosetta's**. It lives in this repo
because it shares the entry discipline — named operands, provenance per
operand, a stated scope — not because it is part of the operator. An
instance is not a domain: do not read a gap_scan result as a transfer, and
do not fold the two.

Fad detection is not the output; it is the access method. A closed era's
substrate metaphor is legible *because* the era ended. Running the scan on
closed instances recovers the shape of what a metaphor hides — and that shape
is the only handle available on the current instance, where the same
structure is illegible from inside.

**Holds where** a metaphor is doing cosmological or explanatory work and the
era's dominant artifact is identifiable. Not restricted to any one
framework, including a stack's own account of cognition.
**Degrades where** there is no dominant artifact, or the artifact is the
object of study rather than the source of the metaphor.
**Non-transferable:** the specific gap. Only the shape class transfers.

| class | what it reads |
|---|---|
| G1 `missing_slot` | what the criterion cannot register |
| G2 `imported_boundary` | operands traced to apparatus rather than measurement |
| G3 `substrate_ceiling` | world-capability set equals artifact-capability set |
| G4 `exterior` | the frame requires an outside it cannot locate |

Plus a provenance readout per operand: `MEASURED`, `APPARATUS`, `UNTRACED`.

Shipped instances are closed ones (`data/rosetta/gap_scan/`). Open instances
are not shipped: instantiating a gap needs the current instance's own
operands, and the scan derives nothing it was not given — the probes are
supplied, not divined.

---

## T6 — Mandala is a separate repo

Rosetta and Mandala are orthogonal axes. **Link, do not fold.**

| | axis | move |
|---|---|---|
| Rosetta | cross-**domain** | crystal → your problem: transfer a solution across domains under shared forcing |
| Mandala | cross-**scale** | grass → ecosystem: take a relation, scale in and scale out, check whether the shape persists |

Mandala's classes are holographic (same structure at any scale), fractal
(self-similar under zoom), other (persists by a different route), and fails
(breaks at a scale — and the break is data). Its test is not only whether a
shape recurs but *why*: shared forcing (the same field acts on both, so the
shape is caused and transfer is licensed) versus shared form (the shapes
coincide with no common term, so it is coincidence until a mechanism
appears). The failure scales are the highest-value output — where a shape
stops recurring names the scale at which a new term enters, and that is a
measurement.

Together the two span the checking — with `gap_scan` on a third,
cross-instance axis. They are not merged here. This repo's
`src/rsc_mandala_bridge/` projects Rosetta artifacts into the Mandala runtime
across the repo boundary; it is a bridge, not a merge.

---

## License

The whole repository is dedicated to the public domain under
[CC0 1.0 Universal](https://creativecommons.org/publicdomain/zero/1.0/) —
see `LICENSE`. The modules listed at the top of this document also carry an
`SPDX-License-Identifier: CC0-1.0` line at their head.
