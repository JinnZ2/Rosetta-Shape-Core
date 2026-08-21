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
| — | `gap_scan.py` | four gap shape classes over an explanatory frame |

```bash
python -m rosetta_shape_core.rosetta   --forcing flow,strain --problem "sizing a roadside mast"
python -m rosetta_shape_core.families  --list
python -m rosetta_shape_core.entry     --validate
python -m rosetta_shape_core.scope     --audit
python -m rosetta_shape_core.gate_log  --summary
python -m rosetta_shape_core.gap_scan  --example clockwork

for m in rosetta families entry scope gate_log gap_scan; do
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

Forcing terms, and nothing else.

| | |
|---|---|
| **shared forcing** | the same field acts on both systems. The shape is caused. Transfer is licensed. |
| **shared form** | the shapes coincide and no common term is named. Coincidence until a mechanism appears. |

`run()` returns licensed matches only unless asked for the rest, so a
shared-form lead can never be mistaken for a shared-forcing one. An
unlicensed match is still a lead — the work it asks for is naming the term
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

## gap_scan

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

Together the two span the checking. They are not merged here. This repo's
`src/rsc_mandala_bridge/` projects Rosetta artifacts into the Mandala runtime
across the repo boundary; it is a bridge, not a merge.

---

## License

The six modules listed at the top of this document, their schemas, and the
data under `data/rosetta/` are dedicated to the public domain under
[CC0-1.0](https://creativecommons.org/publicdomain/zero/1.0/) — see the
`SPDX-License-Identifier` line at the head of each module. The rest of the
repository remains under the MIT license in `LICENSE`.
