# Glyph method: worked examples

CC0. Co-authored. Tags: OBSERVED / DERIVED / PROPOSED. Trailing * = thin volume.

Companion to [`GLYPH_METHOD.md`](GLYPH_METHOD.md). The examples live in this separate file because `GLYPH_METHOD.md` is pinned by sha256 in `tests_bin_landing/PREREG.md`, where it is the context of the retired condition B. Editing it would make `score.py` refuse to score. Nothing here goes into any test packet.

- **Example 1** is the pressure-drop example in the E and C contexts (`tests_bin_landing/PREREG_AMENDMENT_1.md`). It is not repeated here.
- **Example 2** is below.

## Example 2: roadside protection (OBSERVED, field report)

```text
signal       tire tech working on the driver-side steer tire, back to traffic; the tech keeps
             glancing up; cars crowd the cones, clear the hazards, then drift back in
⇆            outward: the tech's glances + car trajectories
             inward: own visibility limit (gray clothing on a gray road)
↻            drivers steer toward what they look at (same drift as whiteout / sandstorm): known cause
dE/dt        trajectories curve back toward the obstacle after passing the hazards
U            hazards + cones subtracted, drift remains = uncovered risk
?            color won't register -> motion will (legs, shoes, movement)
triangulate  stand upstream, between trailer and traffic: position set by trajectory,
             sightline, and the worker's location
action       one clear directing motion: draws the eye AND states the procedure
             (drivers follow a procedure when they know what is asked of them)
validate     worker stops glancing up, attention back on task; cars move over
note         another agent's anxiety signal used as an outward sensor; removing his load
             lowers error risk at his task
```

What the example adds to the method (DERIVED):
- **`triangulate` is a new step.** The worked example in the contexts has no such step. Here the position is not chosen; it falls out of three inputs at once.
- **The outward sensor is another agent.** The tech's glancing is the reading. This is the anxiety row in `FUNCTIONAL_EMOTION_CROSSWALK.md` (∿, PROPOSED), used from outside the agent that carries it.
- **One action, two jobs.** The single motion both draws the eye and tells drivers what is asked of them, so it covers the `?` gap and gives a procedure to follow.
