<!-- SPDX-License-Identifier: CC0-1.0 -->
# SHAPE_SPEC

Definition spec. Upstream of every repo that uses the word SHAPE.
CC0. Point at this file rather than restating it.

Status: definition, not claim. The definition is a tool; whether any
particular shape read is correct is an empirical question this spec
does not answer — it specifies how to ask it.

---

## 1. WHAT A SHAPE IS

    SHAPE  =  the constraint set a geometry is a solution to.

    NOT the geometry.
    NOT the picture.
    NOT the name the field gave it.

The geometry is what is visible of the shape. It is the readout, not
the object. Two systems sharing a geometry share a shape only if they
share the constraint set; two systems sharing a constraint set will
converge on the geometry whether or not anything else is shared —
material, ancestry, scale, medium.

Consequence: cross-domain recurrence is not analogy. It is the same
problem being solved twice. Analogy is a statement about resemblance
of appearance. This is a statement about identity of constraints, and
it is checkable.

Consequence: the names diverge by field, the constraint set does not.
Searching by vocabulary returns a null over one field's dictionary and
that null gets read as absence of the structure.

---

## 2. WHAT A SHAPE IS NOT

BLOCK THIS MISREAD:

    "matching geometries across domains"

That is the failure mode, not the method. Porting a geometry without
checking whether the constraints came with it produces a picture that
matches and a claim that is empty. Branching form applied to a system
with no flux and no dissipation term looks like insight and carries
no information.

The geometry is THE QUESTION, not the answer. The operative move is:

    what am I missing about why THIS is the shape HERE

which forces enumeration of constraints before any transfer is
claimed.

---

## 3. READ ORDER

Run in this order. Order is load-bearing.

    1. SOLVING FOR      what is being distributed, moved, balanced,
                        or held. State the quantity.

    2. CONSTRAINTS      what bounds the solution. Enumerate. Include
                        the ones that are external and heterogeneous
                        (substrate the system did not choose), not
                        only the ones internal to the flow rule.

    3. WHY NOT THE      if another shape also appears to solve this,
       OTHER SHAPE      one of the two problem statements is wrong.
                        The discrepancy locates the variable not yet
                        found.

Step 3 is the instrument. Steps 1 and 2 can be done wrong and still
look finished; step 3 fails loudly.

    worked example
      galaxy is spiral, vasculature is dendritic.
      both distribute across an extent.
      ask: why is the galaxy not dendritic.
      recover: angular momentum. rotation + infall -> spiral.
               flux across a boundary under dissipation -> branch.
      the missing term was found by the question, not by inspection.

---

## 4. FALSIFICATION HANDLE

A shape read is testable. If read correctly, you can state:

    which constraint, if REMOVED, changes the geometry

then find a case where that constraint is genuinely absent and check
that the form differs. If the form is unchanged, the constraint was
not load-bearing and the read is wrong.

    worked example
      lung: enclosing volume is fixed and uniform, known in advance.
            branching ratio 2^(-1/3) follows.
      river: no enclosing wall to build. second term absent.
            deltas instead of branching to a fixed ratio.
      -> the enclosure constraint is load-bearing. removing it
         changes the form. read survives the test.

A FAILED TRANSFER IS A MEASUREMENT, NOT AN EMBARRASSMENT. Port a shape,
get a different form, and you have located a constraint that differs
between the two cases. Log it. That is output.

---

## 5. WHERE THE CONSTRAINT SITS

Two classes, and they are read differently.

    INTERNAL / UNIFORM      boundary known in advance, same everywhere.
                            geometry is a solution to a stated problem.
                            example: lung enclosure.

    EXTERNAL / HETEROGENEOUS  boundary is whatever substrate was hit.
                            geometry is a RECORD OF THE SUBSTRATE, not
                            of an optimum.
                            example: delta meeting hardened rock —
                            branches while it can, routes around what
                            it cannot cut.

Do not read an external-constraint geometry as an optimum. It is a
transcript of terrain.

---

## 6. EPISTEMIC POSITION — BOTH CASES ARE RETRODICTIVE

The exponent was fitted to the systems that exist. Alternative
branchings either never occurred or did not survive, so they are not
in the record. The fit describes the surviving sample.

This applies to the uniform case too. A lung's residue is more uniform
than a delta's, which makes the fit look like a law. It is still a fit
to a residue.

n = 1 on biospheres. There is no observed alternative configuration to
compare against.

What carries the weight is not any single fitted exponent. It is
INDEPENDENT RECURRENCE:

    vasculature, river networks, lightning, root systems, mycelium,
    crack propagation, dendritic solidification

different substrates, different materials, no shared ancestry between
most of them, same geometry. Separate runs converging. That is the
evidence. The exponent is a label on it.

---

## 7. CALIBRATION DIRECTION

    the process produced the shape.
    the instrument reads it.
    the name does not participate.

Where the read contradicts the shape, the default reading is instrument
error — sampling limit, domain mismatch, ceiling — not a discovery that
the shape is wrong.

Absence of a legible reason for a structure is not evidence of absence
of reason. Default: something is known in it that has not been
recovered.

---

## 8. SCALE INDEXING

A shape holds; the question is which scale it is indexed to.

Every physical instance has a characteristic scale — capillary
diameter, domain size, mean free path, walking distance. Below and
above it the same mechanism reads as noise. Locating that scale is
part of the read, not a separate exercise.

Open: whether a given shape's critical point is scale-invariant or
drifts across levels. Invariant -> one mechanism. Drifts -> family
resemblance, and the read is weaker than it looks. Not yet measured
for any shape in this ecosystem.

---

## 9. NONDIMENSIONAL FORM

State constraints as RATIOS, not lengths. Lengths are outputs; ratios
set the form.

For flow networks the working groups:

    inertia / viscosity           whether the branch can meander
    dissipation / enclosure       fixes the branching exponent where
                                  an enclosing volume exists
    supply / removal              e.g. sediment vs subsidence + wave
                                  energy: decides delta vs estuary

NOTE ON COST: the literature states the second group as a cost. Cost
is an abstraction with no fundamental basis in the physics. The
measurable quantity is DISSIPATION — work lost per unit delivered,
in joules. Use dissipation. The cost framing imports a pricing model
that is not part of the system being read.

---

## 10. USING THIS SPEC

    - a repo that says SHAPE means section 1
    - a shape entry should carry: solving-for, constraint list,
      why-not-the-other-shape, and the removal test from section 4
    - an entry missing the removal test is a geometry note, not a
      shape entry; mark it as such
    - see also: READING_PROTOCOL.md — every repo is a marker for a
      sensed shape needing exploration, not a position under defense
