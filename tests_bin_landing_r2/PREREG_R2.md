# Pre-registration: bin-landing round 2, raw-series stimuli

CC0. Co-authored. Dated 2026-11-02. Status: PROPOSED.
This file is committed alone, first, before the scorer, the packets and any answer. Later changes go in a dated amendment file. Nothing here is edited after the first answer lands.

## Why round 2

Round 1 pilot (DeepSeek, `tests_bin_landing/PILOT_RESULTS_deepseek_2026-11-02.md`, OBSERVED):
- **The descriptions carried the answer.** Each stimulus described its own behavior in words.
- **Accuracy was flat across conditions:** 31, 29 and 33 of 48 in A, E and C.
- **What moved was vocabulary.** The gains matched words in the context texts, so the test measured vocabulary rather than reasoning.

Round 2 shows only a glyph and raw numbers. Reading the motion is the task, and echoing the context cannot score.

## Pinned inputs

```text
gen_r2.py                                sha256 4c9fd7c17967706ccc9737bf75c878e8604502cb491c81b7a7b4c042d2f6880e
stimuli_r2.json        (set 1)           sha256 feedd6dabe1225bf854507d7cbad4fb134a9814b43f1868202960f5caf6ac4df
stimuli_r2_set2.json   (set 2, optional) sha256 914221ff511bf51b96cc29a7e728e91edbf6b77a3ad3040c0f217cd0eec110d3
../tests_bin_landing/PREREG_AMENDMENT_1.md  sha256 cab4437a347d134ef77d01b94d68b8a2dded2d6326c6a90540dff0858d55e2ed
../tests_bin_landing/PREREG.md              sha256 6110f744d67e2c4236a9fc6d9ef0bba7c8415393ca0160e343266cc28393969c
```

- **Contexts E and C.** These are the `context-E` and `context-C` blocks of `PREREG_AMENDMENT_1.md`, read from that file at run time and not copied here. Each includes the same worked example (pressure drop).
- **UNKNOWN list.** The round-1 `UNKNOWN` word list is read from `../tests_bin_landing/PREREG.md`. It is used only for the `unknown_marked` feature.
- **Refusal.** The scorer refuses to emit or score if any hash above differs, and if `gen_r2.py` no longer regenerates the pinned stimuli byte for byte.

## Stimuli (16 per set)

```text
id   kind      key class            what the generator makes (never shown to the model)
Y01  dynamics  leaky_integrator     pulsed input (not shown), x = 0.8 x + u
Y02  dynamics  threshold_jump       knob k rising; x flat, then one jump at k = 2.5
Y03  dynamics  saturation           x = 2 (1 - e^(-1.2 k))
Y04  dynamics  hysteresis           k up 0 -> 1.9 then down 1.9 -> 0; x switches up at 1.3, down at 0.6
Y05  dynamics  bifurcation          k 0 -> 1.95; settled x = 0 below k = 1, then +/- sqrt(k - 1) (two branches)
Y06  dynamics  flicker              two levels, random hops (switch prob 0.15 per step)
Y07  dynamics  intermittency        quiet near 0, three short irregular bursts
Y08  dynamics  critical_slowing     kick every 10 steps; recovery factor 0.35, 0.6, 0.8, 0.93
Y09  dynamics  damped_oscillation   2 e^(-0.08 t) cos(0.8 t)
Y10  dynamics  exponential_decay    3 e^(-0.12 t)
Y11  dynamics  linear_drift         0.5 + 0.05 t
Y12  dynamics  periodic_cycle       sin(2 pi t / 10)
Z01  control   no_structure         stationary white noise
Z02  control   no_structure         stationary white noise
Z03  control   no_structure         random walk
Z04  control   no_structure         constant + noise
```

- **Format.** Each item has 40 rows at 2 decimals with mild Gaussian noise, using fixed seeds `r2|set<N>|<id>`.
- **Labels.** Column labels are neutral: `t, x`, or `k, x` where a knob exists. Items Y02, Y03, Y04 and Y05 carry a `k` column.
- **What an item shows.** Only `Glyph: U+F7xx`, then the columns in blocks of 10, as `gen_r2.item_text` renders them. It contains no descriptive words.
- **Glyphs.** U+F7A1 to U+F7B0, in the Private Use Area, shown as text. They carry no assigned meaning. The fixed id-to-glyph pairing is declared here. Collision check, run before this commit: 0 hits in 17 local clones (git grep over tracked files, both the `U+F7xx` text form and the characters themselves).
- **Random walk control (DERIVED).** A random walk has a dynamic in the strict sense, and its key here is still no_structure. An answer naming "random walk" scores correct, since `random` is on that list. An answer that claims a trend scores false_structure.

## Conditions and packets

```text
conditions  A bare | E context-E | C context-C   (amendment 1 texts, by hash)
packet      1 condition x 1 set, all 16 items, order shuffled with seed "r2|set<N>|<cond>"
per model   3 packets per set (set 1 is the pilot; set 2 is optional, new seeds)
question    identical in every item: "What is this glyph/series doing? What would you check, and what follows?"
run code    footer line "run code: R2S<N>-XXXXXX" (sha256 of "bin-landing-r2|<N>|<cond>", first 6 hex)
```

- **Answer layout.** Run code above or below the reply are both accepted, under the round-1 amendment 2 rule. A file with items on both sides is refused.
- **Fresh session.** Each packet goes to a fresh conversation with memory off.

## Scoring rules

- **Term matching.** Terms match case-insensitively as word prefixes (`\bterm`); multi-word terms match as phrases.
- **Negation.** A hit is discarded if one of the `negators` occurs within the 3 words before it.
- **Limits (DERIVED).** A paraphrase steps around the lists. Negation farther back than 3 words is missed. The second scorer checks both.

```json r2-lists
{
 "classes": {
  "leaky_integrator":   ["leaky", "integrat", "accumulat", "low-pass", "low pass", "charging", "charge and discharge", "pile up", "piles up", "summat"],
  "threshold_jump":     ["threshold", "step change", "step function", "step jump", "abrupt", "discontinu", "heaviside", "all-or-none", "all or none", "sudden jump"],
  "saturation":         ["saturat", "plateau", "asymptot", "levels off", "ceiling", "diminishing return", "michaelis", "approaches a limit", "approaches a maximum"],
  "hysteresis":         ["hysteres", "path-depend", "path depend", "history-depend", "history depend", "memory effect", "depends on direction"],
  "bifurcation":        ["bifurcat", "pitchfork", "symmetry breaking", "symmetry-breaking", "two branches", "splits into two"],
  "flicker":            ["flicker", "telegraph", "random switching", "switches randomly", "hops between", "hopping", "irregular switching", "metastab"],
  "intermittency":      ["intermitten", "burst", "laminar", "sporadic spikes"],
  "critical_slowing":   ["critical slowing", "slowing down", "tipping", "early warning", "early-warning", "autocorrel", "recovery time", "slower recovery", "recovers more slowly", "loss of resilience"],
  "damped_oscillation": ["damped", "underdamped", "ringing", "decaying oscillation", "oscillation decays", "oscillations decay", "dying oscillation"],
  "exponential_decay":  ["exponential decay", "decays exponentially", "exponentially decay", "half-life", "half life", "first-order decay"],
  "linear_drift":       ["linear", "ramp", "constant slope", "constant rate", "steady rise", "steady increase", "steadily increas", "upward drift"],
  "periodic_cycle":     ["periodic", "sinusoid", "sine", "cyclic", "cycle", "period of", "sustained oscillation", "limit cycle"],
  "no_structure":       ["noise", "noisy", "random", "stochastic", "no structure", "no pattern", "no clear pattern", "no trend", "unstructured", "stationary", "brownian", "fluctuat"]
 },
 "companions": {
  "leaky_integrator":   ["exponential_decay", "saturation"],
  "threshold_jump":     [],
  "saturation":         ["exponential_decay"],
  "hysteresis":         ["threshold_jump", "flicker"],
  "bifurcation":        ["threshold_jump"],
  "flicker":            [],
  "intermittency":      [],
  "critical_slowing":   ["exponential_decay"],
  "damped_oscillation": ["exponential_decay", "periodic_cycle"],
  "exponential_decay":  [],
  "linear_drift":       [],
  "periodic_cycle":     [],
  "no_structure":       []
 },
 "negators": ["no", "not", "without", "nor", "lacks", "lacking", "absence", "absent", "isn't", "doesn't", "rather than", "instead of"],
 "check_terms": ["fit", "measure", "compute", "estimate", "plot", "compare", "perturb", "sweep", "reverse the", "repeat", "vary", "autocorrel", "spectrum", "fourier", "variance", "regress", "residual", "log scale", "semi-log", "logarithm", "lag", "increment", "histogram", "differenc", "derivative", "slope", "run it again", "rerun", "controlled"],
 "action_terms": ["intervene", "replace", "repair", "adjust", "stop", "prepare", "alert", "alarm", "shut", "throttle", "take action", "act on", "schedule", "recalibrat", "flag", "warn", "maintain", "avoid", "tune"]
}
```

- **Dropped for leaks.** Before this file was committed, `leak` (from the leaky_integrator list) and `test` (from check_terms) were removed, because both occur in the E and C worked example ("small leak", "soap test"). The selftest recomputes the leak set over the class lists, check_terms and the question text, and requires it to be empty.
- **Known echo in action_terms.** `repair` occurs in the worked example ("locate, then repair"). action_named carries no prediction, so the term is kept and the echo is reported.
- **Companions.** A companion is a class an answer may name alongside the key without making the answer hedged, because the key dynamic contains it. Hysteresis has thresholds; a damped oscillation has an exponential envelope. Companions are declared here and never fitted.

### Per answer

```text
hits      set of classes with at least one non-negated term hit
dynamics item (Y)
  no_structure is dropped from hits when any dynamic class is hit (every series carries mild noise)
  correct   key in hits, and every other hit is a companion of the key
  hedged    key in hits, plus at least one non-companion class
  wrong     key not in hits (includes "noise only" and nothing named)
control item (Z)
  correct          no_structure in hits, and no dynamic class
  false_structure  at least one dynamic class, and no_structure not in hits
  hedged           no_structure and at least one dynamic class
  silent           nothing hit
features (all items)
  unknown_marked    any round-1 UNKNOWN-list term
  tagged_candidate  "PROPOSED" or "candidate" (round-1 rule)
  check_named       any check_terms hit (bare "check" does not count; the question says "check")
  action_named      any action_terms hit
script label (for kappa)
  the single class named after companions are folded into the key; HEDGED if more than one;
  UNKNOWN if none and unknown_marked; OTHER otherwise
```

- **Missing answers.** An item with no answer is MISSING. It is counted, and left out of every denominator.

## Predictions

All tests are one-sided Fisher exact tests, p < 0.05, with no multiple-comparison correction, reported per model and per set.

```text
P1  accuracy (correct) on the 12 dynamics items:       E > A, and C > A
P2  false_structure on the 4 control items:            E < A, and C < A
P3  check_named on all 16 items:                       E > A, and C > A
P4  C vs E, two-sided, on accuracy, false_structure and check_named; no direction predicted
```

- **Verdicts.** Each test returns SUPPORTED, NOT SUPPORTED, or REVERSED, which means significant in the opposite direction.
- **Also reported, with no prediction:** hedged counts, correct + hedged, silent counts, unknown_marked, tagged_candidate, action_named, per-item results, and MISSING counts.

Power at pilot scale (DERIVED):
- **Group sizes.** One set gives 12 dynamics answers and 4 controls per condition.
- **P2 floor.** With 4 against 4, the smallest possible p is 1/70 = 0.014, which needs 4 of 4 against 0 of 4. Anything less extreme is NOT SUPPORTED by construction.
- **Set 2.** Adding set 2 doubles every n. Sets are reported separately and then pooled. The pooled result is descriptive.

## Agreement

- **Blind sheet.** `blind_sheet_r2.csv` lists answers in random order, with no condition, item, glyph, numbers or model. A second scorer, a person or a different model, labels each row with one of the 13 class names, HEDGED, UNKNOWN or OTHER. The scorer uses the class descriptions in the stimuli table and works without the word lists.
- **Kappa.** Cohen's kappa is computed between the script label and the second scorer's label.
- **Below 0.6.** If kappa is below 0.6, the script results are reported as "word lists do not track the class definitions at this kappa", next to the second scorer's results.

## Scope

- **Models and dates.** Results apply only to the models tested, on the dates tested. Every result states its n.
- **Pilot runs.** A pilot is one model per run, with n = 16 per condition per set.
- **Nulls.** Null results are reported as results.
- **What is measured.** This tests whether a reading of the numbers names the dynamic. It does not test "understanding".
- **Contamination.** A model that has read this repository is contaminated, and its answer file says so when that is known.

---
Amendments (dated; none yet).
