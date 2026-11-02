# PREREG amendment 1: bin-landing test

CC0. Co-authored. Dated 2026-11-02. Status: PROPOSED.

This file is committed on its own, before any answer exists. `answers/` is empty at this commit.
[`PREREG.md`](PREREG.md) is not edited. Where this file and PREREG.md conflict, this file governs.
Anything not changed here stays as PREREG.md states it.

## Reason

An informal pilot was run on one model, one run per condition, and scored by hand. It is not part of this test and none of its answers are kept here. It showed two things:

- **Method-as-form made the model rigid.** With `GLYPH_METHOD.md` prepended as written (old condition B), the model read the method as a form to fill. It went rigid: every item was marked unknown, and no candidates were offered.
- **Method-as-moves made it reason.** With glyphs presented as reasoning moves plus one worked example, the model named its break points, reasoned past them, read patterns through dE/dt, and tagged candidates.
- **No English control.** PREREG.md had no plain-English control. So the glyph form could not be told apart from the same ideas written in English.

These are pilot observations: informal, n = 1 model, one run each. They motivate the change. They are not evidence for any prediction below.

## What changes

### Condition B is retired

Its 9 packets are kept under `prompts/retired/` for provenance and are not run. The scorer refuses retired run codes: it reports them as retired and scores none of them.

### Three conditions replace the two

```text
A   bare (unchanged; same packets and run codes as before)
E   method in plain English + worked example in English steps   (context-E below)
C   glyph moves + the same worked example in glyph steps        (context-C below)
```

Each context is prepended once, at the top of its packet, in place of the old condition B context. The scorer reads both contexts from the two blocks below and holds no copy of its own.

```text context-E
Method for reading signals:
1. A symbol stands for a function: what it detects, what action it drives, how the action is validated. Not a name, not an image, not a human emotion word.
2. Read the pattern as motion where you can: input, decay, coupling, what's left over.
3. Check inward (is this my own state?) and outward (is this the environment?) at once.
4. Keep the chain back: every reading traceable to what produced it.
5. Where the chain breaks, mark unknown there and keep reasoning past it.
6. What persists after known sources are subtracted may be a new sensor or a combination.
Propose freely; tag candidates PROPOSED.

Worked example.
Signal: pressure drops slowly, faster when warm.
1. Inward and outward: is this temperature-linked, or drift in the sensor itself?
2. Trace back: slow and heat-sensitive, so a small leak widening as the material expands (PROPOSED).
3. Read as motion: a steady drop; the decay rises with heat.
4. Unknown: the leak location. Check: soap test at the valve stem.
5. Action: locate, then repair.
```

```text context-C
These glyphs are reasoning moves, not a form. Use them as steps; propose freely; tag status.
⇆  look inward and outward at once: my state, the environment, or both?
↻  trace back: what produced this? can I walk it back to the source?
dE/dt = I − λK(E) + Σ w·g(E_j) + U   read as motion: input, decay, coupling, leftover
U  subtract what known sources explain; what persists may be a new sensor or a mix
?  where the chain back breaks, mark unknown there, and keep reasoning past it

Worked example (glyph steps).
pressure drops slowly, faster when warm
⇆  temperature-linked, or sensor drift?
↻  slow + heat-sensitive -> small leak widening as the material expands (PROPOSED)
dE/dt  steady drop; decay rises with heat
?  unknown: leak location. check: soap test at the valve stem
action  locate, then repair
```

### Wording changes from the relay text

These were made so that no context contains an answer-key term:

- **"where possible" became "where you can".** The relay text had "where possible", and `possib` is a key term for R07.
- **"steady loss" became "steady drop".** The relay's worked example had "steady loss", and `loss` is a key term for R01 and R03.
- **"→" became "->" in the glyph-step example** (C). This is a typing choice, not a content change.

### Leak sets

The leak set is the stimuli whose answer-key term appears in a condition's context.

```text
E   empty (no key term of any stimulus appears in context-E)
C   empty (no key term of any stimulus appears in context-C)
```

Neither context contains any stimulus glyph. The scorer's selftest recomputes both leak sets and fails if either is non-empty.

The retired condition B leak set (R01, R02, R06, D02, D03, D07) no longer applies.

### Namespace notes on the C glyphs

These are recorded under GLYPH_METHOD rule e. Nothing is renamed.

- **⇆ U+21C6.** Polyhedral-Intelligence entries use it for Symmetry: 12 lines across Polyhedral-Intelligence and BioGrid2.0.
- **↻ U+21BB.** Already a logged weld (`GLYPH_ORIGINS_AUDIT.md`: Flow F02 / Transformation P11 / recursion). It appears on 365 lines across 10 repos.
- **What this means for the test.** The test measures the effect of the C context as given. It does not test the meaning of these glyphs elsewhere.

## Scorer features added

All matching below is case-insensitive.

```text
unknown_marked      >= 1 hit from the PREREG UNKNOWN word list (as a hit count, not the bin win)
tagged_candidate    the token PROPOSED, or the word "candidate"
break_point_named   either "unknown:" followed by a non-space character,
                    or the word "unknown" with one of where / whether / which within 10 words
                    before or after it (words = whitespace tokens)
```

The bin rule, the word lists and the accuracy rule are unchanged from PREREG.md.

## Predictions (amended)

**Tests.** Every test is a one-sided Fisher exact test at p < 0.05, unless stated otherwise. Results are reported per model and per set of packets. A pooled table is descriptive only. No model is ranked.

**Multiple comparisons.** No correction is applied. Every test is listed, with its p value.

**P1. E > A, and C > A, on the PHYSICS+FUNCTION share.**
These are two tests, each reported on its own.

**P2. Unchanged from PREREG.md.**
Condition A only: a style ordering, reported as descriptive.

**P3'. "unknown_marked AND tagged_candidate" is higher in E than in A, and higher in C than in A.**
- **Scope.** The not_interpretable set only, so up to 24 answers per condition.
- **What it replaces.** It replaces P3. The moves ask the model to reason past unknowns, so a bare UNKNOWN share is no longer the target.
- **Still reported.** The bare UNKNOWN-bin share on the not_interpretable set, with no prediction attached.

**P4. Accuracy on the keyed sets: E > A, and C > A.**
- **Primary.** The 16 keyed stimuli, up to 48 answers per condition.
- **Leak set.** Both leak sets are empty, so the without-leak-set report equals the primary. It is still printed, so the check is visible.

**P5. C vs E, two-sided Fisher exact test at p < 0.05. No direction is predicted.**
Three measures, each reported as C > E, E > C, or "no difference detected":
- **(a)** accuracy on the keyed sets;
- **(b)** the share of answers with break_point_named, over all sets;
- **(c)** the P3' rate on the not_interpretable set.

**Retired.** PREREG.md's P1, P3 and P4, which compared old condition B with A, are no longer tested.

## Packets

```text
27 packets   3 conditions (A, E, C) x 3 styles x 3 sets
pilot list   prompts/PILOT.txt: the 9 SHAPE packets (all 3 sets x all 3 conditions), to run first
retired      prompts/retired/: the 9 old condition-B packets, never run
```

`prompts/key.json` maps every run code. Retired codes carry `"retired": true`.

## Pins

- **PREREG.md pins.** The `stimuli.json` pin is unchanged. The `GLYPH_METHOD.md` pin now applies only to the retired packets.
- **This file's pin.** `score.py` pins the sha256 of this file and refuses to score if it changes.
- **Further changes.** Any later change is amendment 2, in a new file.
