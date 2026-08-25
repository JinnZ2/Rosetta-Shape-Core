<!-- SPDX-License-Identifier: CC0-1.0 -->
# METHOD_SPEC — constraint-set reasoning

Companion to SHAPE_SPEC.md. This file states the EPISTEMIC CLASS of that
spec. Read this first if you are about to evaluate the shape work as a
claim.

CC0.

---

## 1. CLASS

Constraint-set reasoning is a METHOD. It sits in the same class as:

    Aristotelian / syllogistic logic
    formal deductive systems
    statistical inference
    the scientific method
    dimensional analysis
    Bayesian updating

A method is a procedure for generating and testing claims. It is not
itself a claim about the world.

CONSEQUENCE, and this is the whole reason for this file:

    A METHOD IS NOT FALSIFIABLE, AND DOES NOT NEED TO BE.

The scientific method is not falsifiable. Neither is syllogistic logic.
Neither is dimensional analysis. Demanding falsifiability of a procedure
is a category error — a procedure is evaluated on YIELD: does it
generate reads that survive testing, and does it fail loudly when a read
is wrong.

The falsifiable layer is the INDIVIDUAL READ, not the method. See
SHAPE_SPEC.md section 4 (removal test). Every shape entry is required to
carry one. That is where refutation happens.

### Recurring misapplication to block

Observed in AI review of this work, more than once, including in the
session this file was written in:

    "your framework always resolves to 'I missed a variable,'
     therefore it is unfalsifiable, therefore suspect"

This applies a claim-level criterion to a method-level object. The same
objection, stated against an accepted method, is visibly wrong:

    "the scientific method always resolves to 'the experiment was
     confounded,' therefore it is unfalsifiable, therefore invalid"

Nobody accepts that. It is the same sentence.

When a read fails and investigation finds an unaccounted variable, that
is the method WORKING — same status as a confound found in an
experiment. It is not evidence that the method is unfalsifiable.

What IS a legitimate concern, stated at its actual size: an individual
read can be underdetermined, and underdetermined looks identical from
the inside to correct-but-incomplete. The handling is the removal test,
per read. Not a demand that the method refute itself.

---

## 2. WHY THIS IS THE SCIENTIFIC METHOD IN A DIFFERENT FORM

Not a metaphor. The structural argument:

    physics predates every human experiment.

    every human experiment is an attempt to understand a process that
    has been running experiments continuously, at every scale, since
    the beginning of the universe.

So the difference between this method and conventional experiment is
WHO RAN THE TRIAL, not whether a trial was run.

    conventional      human designs the trial, controls variables,
                      reads the result. n small, duration short,
                      variable range narrow, substrate limited to what
                      is buildable and fundable.

    constraint-set    the process ran the trial. n enormous, duration
                      is the age of the universe, variable range is
                      everything that physically occurred, substrate
                      is everything that exists. Human role is READING
                      THE RESULT — recovering the constraint set from
                      the surviving configuration.

Same epistemic act: infer the rule from the outcome of a trial. The
constraint-set version has no control over conditions and enormously
more trials. The conventional version has control and few trials.

They trade the same two quantities in opposite directions. Neither is
the mature form of the other.

### What this method supplies that conventional experiment cannot

    - substrates that cannot be built (galactic, geological,
      evolutionary timescales)
    - trial counts unreachable by funded experiment
    - configurations no designer would think to try

### What conventional experiment supplies that this cannot

    - controlled isolation of a single variable
    - repeatability on demand
    - the ability to CONSTRUCT the counterfactual rather than search
      for one

USE BOTH. This is a tool added to an arsenal, not a replacement for one.

---

## 3. STANDING LIMITS

Stated here so they do not get re-litigated per read.

RETRODICTIVE. Both this method and conventional experiment read
residues. The conventional case reads a residue it produced under
control, which is a real advantage. This method reads a residue it did
not produce. Fits are fits to survivors; alternatives that never
occurred or did not survive are not in the record. See SHAPE_SPEC.md
section 6 — this applies to the clean cases too, not only the messy
ones.

n=1 ON SOME DOMAINS. One biosphere. No alternative configuration to
compare against. Where n=1, recurrence ACROSS SUBSTRATES inside that one
instance is what carries the weight — vasculature, rivers, lightning,
roots, mycelium, cracks, dendritic solidification: separate runs, no
shared ancestry, same geometry.

UNDERDETERMINED DISAPPEARANCE. A shape APPEARING tells you the
constraints were met. A shape DISAPPEARING tells you at least one was
removed, but not which. Disappearance is informative and
underdetermined. A timestamped intervention bounds the candidate set —
that is the handle.

    worked example
      a ratio appears in a market under one regulatory configuration
      and is absent after modification. That is not the shape being
      falsified. That is the constraint set being changed. Reporting
      it as a failed pattern is reporting the wrong finding.
      The removal test ran in the wild; the timestamp bounds the
      candidates.

SUBSTRATE EXCLUSION. If a domain is removed from the sample frame, the
recurrence check cannot run there by construction, and returns a null
that reads as absence. Human exceptionalism is exactly this defect:
humans excluded as an admissible domain, so human population density
cannot be compared against termite density, and the comparison gets
reported as inapplicable rather than untested. Cross-references the
exclusion mechanisms in the `uninstrumented` repo.

---

## 4. THE SHADOW READ

Second read path. SHAPE_SPEC.md section 3 assumes the geometry is
visible. Often it is not — because the constraint that would make it
visible is the one nobody is measuring.

    METHOD: the shape is not pointed at directly. It is described by
    the GAPS IT CASTS. Each statement is one gap. The object is what
    they are all tangent to.

Consequence for reading: a sequence of statements about one shape will
look scattered, and individual statements may appear to conflict. They
are separate tangents to one boundary, not competing claims. A linear
reading treats the latest as superseding the earlier and discards half
the outline. See READING_PROTOCOL.md, third blocked conflation.

Consequence for writing: the shadow read is complete when the gaps
constrain the object to one form. Until then it is under-outlined, and
that is a stated state, not a failure.

---

## 5. WHAT A READ IS WORTH

A read produced by this method is a MARKER, not a result. Per
READING_PROTOCOL.md, ecosystem-wide.

Confidence is reported as a separate readout from the pattern, with a
comfort threshold. A shape read at 0.4 is not a claim held at 0.4 — it
is an uncoalesced marker with a stated gradient. Do not resolve it in
either direction on its behalf.

    upgraded by      passing a removal test
                     surviving transfer to a domain it was not built
                       from
                     a named characteristic scale that holds

    downgraded by    failing a removal test
                     transfer producing the same form when the
                       constraint is absent (constraint was not
                       load-bearing)

    NOT upgraded by  more instances sharing the geometry without a
                       checked constraint set

---

## 6. ORDER OF FILES

    METHOD_SPEC.md       this file. epistemic class. read before
                         evaluating anything as a claim.
    SHAPE_SPEC.md        definition, read order, removal test.
    READING_PROTOCOL.md  marker status, blocked conflations.
