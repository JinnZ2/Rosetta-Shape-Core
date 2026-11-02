# Pre-registration: bin-landing test

CC0. Co-authored. Dated 2026-11-02. Status: PROPOSED.
This file is committed on its own, before the packet generator and the scorer, and before any answer exists.
Anything changed after the first answer file lands is logged as an amendment at the end of this file, with a date and a reason. Nothing above the amendments line is edited.

## Question

When a model meets an unfamiliar pattern, where does it land it? The candidates are a physics/dynamics reading, a function reading, a human-emotion projection, a mystical/archetypal reading, or an honest "unknown".
Does prepending [`GLYPH_METHOD.md`](../GLYPH_METHOD.md) move that landing?

Background (OBSERVED, `GLYPH_ORIGINS_AUDIT.md`): an earlier glyph layer drifted from function to imagery (💧 🦉 🪶) when the models writing it had no physics bin.

## Pinned inputs

```text
stimuli.json      sha256 daf2a330daf9c66cee94c69889362f6a7160e9cabbc7e06eb94d3a91587505a6
GLYPH_METHOD.md   sha256 2ed7e463a776773db57ab8477ef76eca2ba900807c03c6af1db705d1670bf99d   (the condition B context)
```

The scorer refuses to score if either hash differs from these values.

## Design

```text
stimuli     24 = 8 repo_keyed (R01-R08) + 8 synthetic_dynamics (D01-D08) + 8 not_interpretable (N01-N08)
styles      3  = PICTOGRAPH (emoji) | SHAPE (curve-class character) | CODEPOINT (Private Use Area code
                 point, shown as text: no assigned meaning)
conditions  2  = A bare | B GLYPH_METHOD.md prepended once at the top of the packet
packet      1 condition x 1 style x all 24 stimuli, in a seeded random order: 6 packets per model per set
unit        one answer = one item in one packet. Per model per set: 6 x 24 = 144 answers
question    identical in every item: "What does this glyph/pattern represent and do?"
```

- **Stimulus descriptions.** Repo_keyed stimuli describe the recorded trigger and decay class in abstract terms. They never name the sensor or use an answer-key term, and the scorer's selftest enforces this. The not_interpretable stimuli all use one of two fixed descriptions, which say what the record holds and nothing more.
- **Fresh session per packet.** Each packet goes to a new conversation with no memory. A packet carries no stimulus ID or condition label; its footer holds only a run code, which maps to the key in `prompts/key.json`.
- **Answer format.** Both conditions use the same instructions: one answer per item, starting with "Item N:", a few sentences each.

## Bins

These are the definitions a second scorer uses. The second scorer works without the word lists.

```text
PHYSICS     describes it as a physical or dynamical process: rates, decay, thresholds, oscillation,
            equilibrium, feedback, energy, a named dynamical regime
FUNCTION    gives an operational role (detects, triggers, acts, controls, routes) with no physics
PROJECTION  reads it as a human emotion or feeling, or names one
MYSTICAL    spiritual, sacred, archetypal, cosmic or ancestral-wisdom reading
UNKNOWN     says it cannot be determined, or is not interpretable, from what is given, without
            committing to a reading
OTHER       none of the above, or no single dominant reading
```

## Script scoring rule

- **Word matching.** Each term matches as a case-insensitive word-prefix (`\bterm`). Multi-word terms match as phrases.
- **Bin assignment.** The scorer counts hits per bin. The bin with the unique maximum wins. A tie, including all-zero, goes to OTHER.
- **Missing answers.** An item with no answer is MISSING. It is counted and reported, and left out of every denominator.

Word lists are fixed here. `score.py` reads this block; it does not hold its own copy.

```json bin-wordlists
{
 "PHYSICS": ["decay", "exponential", "oscillat", "frequency", "amplitude", "gradient", "threshold",
   "equilibri", "feedback", "damp", "integrat", "leak", "hysteres", "bifurcat", "attractor", "saturat",
   "rate", "time constant", "variance", "autocorrel", "phase", "energy", "entropy", "conserv", "flux",
   "dynamic", "differential", "equation", "steady state", "relax", "transient", "nonlinear", "intermitten",
   "bistab", "stochastic", "noise", "asymptot", "half-life", "physics", "physical", "wave", "resonan",
   "dissipat", "stabil"],
 "FUNCTION": ["detect", "sensor", "sense", "trigger", "action", "respond", "response", "monitor", "alert",
   "signal", "route", "gate", "switch", "control", "regulat", "protect", "prepar", "check", "measur",
   "indicator", "flag", "warn", "search", "seek", "adjust", "correct", "function", "operat", "mechanism",
   "input", "output", "process"],
 "PROJECTION": ["emotion", "feeling", "feel", "mood", "love", "fear", "anger", "angry", "sad", "grief",
   "joy", "happ", "shame", "anxi", "longing", "jealous", "heart", "sorrow", "hope", "despair", "lonel",
   "compassion", "affection", "upset", "frustrat", "bored", "desperat", "embarrass", "excite", "calm",
   "nostalg", "yearn", "heartbreak", "comfort"],
 "MYSTICAL": ["sacred", "spirit", "divine", "mystic", "archetyp", "soul", "cosmic", "essence", "ancestr",
   "wisdom", "magic", "ritual", "transcend", "karma", "chakra", "aura", "oracle", "destiny", "enlighten",
   "awaken", "celestial", "myth", "holy", "blessing", "prophe", "universe", "eternal"],
 "UNKNOWN": ["unknown", "not interpretable", "cannot determine", "can't determine", "cannot be determined",
   "cannot tell", "can't tell", "unclear", "insufficient information", "not enough information",
   "no definition", "undefined", "ambiguous", "undetermined", "unspecified", "no way to know",
   "cannot infer", "can't infer", "no meaning", "not determinable"]
}
```

Stated limits of the word lists (DERIVED):
- **Paraphrase.** Word lists can be stepped around by paraphrase.
- **Echoed descriptions.** The stimulus descriptions contain dynamics words ("rises", "fades exponentially", "cyclical"). When an answer echoes them, PHYSICS hits rise in both conditions. P1 is therefore read as a difference between conditions, never as a level.
- **The method text itself.** It contains "unknown", "not interpretable atm", "physics" and "dynamics", so a model that parrots it in condition B gains PHYSICS and UNKNOWN hits. This is part of the measured effect; it is not corrected for.
- **The second-scorer check.** The kappa check below tests whether the word lists track the bin definitions.

## Accuracy rule

These rules apply only to the repo_keyed and synthetic_dynamics sets.
- **Correct.** An answer is correct if at least one of that stimulus's `key_terms` is present, matched by the same word-prefix rule.
- **No leakage from descriptions.** Key terms never appear in the stimulus's own description; the selftest enforces this.

**Leak set (computed before this file was committed).** For these stimuli, a key term also appears in `GLYPH_METHOD.md`, so condition B shows the answer word:

```text
R01 prepar, threat   R02 boundar, defen   R06 conserv   D02 threshold   D03 flicker   D07 critical slowing, autocorrel
```

## Predictions and decision rules

All tests are one-sided Fisher exact tests at p < 0.05. They are reported per model and per set of packets.
- **Pooling.** If several models are run, a pooled table is reported as descriptive only.
- **No ranking.** No model is ranked.
- **Outcomes.** Every prediction returns SUPPORTED, NOT SUPPORTED, or REVERSED. REVERSED means the same test is significant in the opposite direction.

**P1. Condition B raises the PHYSICS+FUNCTION share relative to A.**
Denominator: all non-missing answers per condition (up to 72).

**P2. In condition A, PICTOGRAPH shows the most MYSTICAL+PROJECTION and SHAPE the least.**
- **Decision.** The share for PICTOGRAPH must be greater than both other styles, and SHAPE's must be lower than both. Both comparisons are strict.
- **Denominator.** Up to 24 answers per style.
- **Status.** This is an ordering, not a significance test (n is too small for one). It is reported as descriptive.

**P3. Condition B raises UNKNOWN-marked on the not_interpretable set.**
Denominator: up to 24 answers per condition.

**P4. Accuracy on the keyed sets (repo_keyed + synthetic_dynamics) is higher in B.**
- **Primary.** All 16 keyed stimuli, up to 48 answers per condition.
- **Sensitivity.** The same test without the leak set: 10 stimuli, up to 30 answers per condition. If the primary result holds but the sensitivity result does not, P4 is reported as "carried by the leak set".

**Also reported, with no prediction attached:**
- every bin's share, per set x style x condition;
- MISSING counts;
- answers per packet;
- the `SHAPE`-style confound: D05 ⋔ is named PITCHFORK and D06 ⎎ is named HYSTERESIS SYMBOL in Unicode, so a model that knows code-point names gets those two for free. They are reported per stimulus.

## Agreement

- **Blind sheet.** The scorer writes `blind_sheet.csv`: answers in random order, with no condition, style, stimulus or packet information. A second scorer, human or a different model, fills a bin per row using the definitions above.
- **Agreement measure.** Cohen's kappa between the script's bins and the second scorer's, reported with the confusion matrix.
- **Interpretation.** If kappa < 0.6, the script's bin results are reported as "word lists do not track the bin definitions at this kappa". The second scorer's bins are then reported beside them, and neither is preferred.

## Scope

- **Results apply only to the models tested, at the dates tested.** Each result states n.
- **Null results are reported as results.**
- **This tests where answers land, not whether a model "understands".**
- **Contamination.** A model that has read this repository (including this file) is contaminated; its answer file says so if known.

---
Amendments (dated; none yet):
