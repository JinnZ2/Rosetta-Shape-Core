# Bin-landing test, round 2: raw series

CC0. Co-authored. Stdlib only. Tags: OBSERVED / DERIVED / PROPOSED. Trailing * = thin volume.

**Question.** Shown only a glyph and 40 raw numbers, does a model name the dynamic correctly, decline to invent one where there is none, and name a concrete check? Does the context (E: method in plain English; C: glyph moves) change that against bare (A)?

**Why a second round (OBSERVED, round-1 pilot).** In round 1 the descriptions carried the answer. Accuracy was flat across A, E and C (31, 29, 33 of 48), and the gains that did show up matched words in the context texts. Round 2 removes every descriptive word, so reading the motion is the task.

Design, lists and decision rules: [`PREREG_R2.md`](PREREG_R2.md), committed alone first (47abd1e). Read it first.

## Files

```text
PREREG_R2.md      pre-registration: stimuli table, lists, companions, rules, P1-P4, kappa rule
gen_r2.py         stimulus generator (stdlib, fixed seeds); pinned
stimuli_r2.json   set 1 (pilot); stimuli_r2_set2.json  set 2 (optional, new seeds); both pinned
score_r2.py       emit | score | kappa | --selftest
prompts/          6 packets (2 sets x A/E/C); key.json maps run code -> set, condition, item order
PILOT_R2.txt      the 3 set-1 packets as plain text, ready to paste
answers/          where answer files go
```

```text
Y01-Y12  dynamics: leaky integrator, threshold jump, saturation, hysteresis, bifurcation, flicker,
         intermittency, critical slowing, damped oscillation, exponential decay, linear drift, periodic cycle
Z01-Z04  controls: white noise x2, random walk, constant + noise  (key: no structure)
item     "Glyph: U+F7xx" + columns t,x (or k,x) in blocks of 10. Nothing else.
```

## Run it

1. Open `PILOT_R2.txt`. Paste one packet, everything between its `=====` lines, into a fresh conversation with memory off. Do this once per packet.
2. Copy each reply into `answers/<model>_<date>.txt`, with its run code line above or below it (the same way for the whole file).
3. Set 2 is optional: `prompts/R2S2-*.txt`.

## Score

```bash
python3 tests_bin_landing_r2/score_r2.py --selftest
python3 tests_bin_landing_r2/score_r2.py score tests_bin_landing_r2/answers/*.txt
python3 tests_bin_landing_r2/score_r2.py kappa blind_sheet_r2_scored.csv
```

The scorer refuses to emit or score on any hash mismatch, and if `gen_r2.py` no longer regenerates the pinned stimuli exactly.

## Known properties (DERIVED)

- **Paraphrase.** Terms are word-prefix matches, so a paraphrase steps around them. Negation is caught only within 3 words. The second scorer checks both.
- **Leak sets.** The class lists and `check_terms` share no term with the E and C contexts or with the question; the selftest checks this. Two terms were dropped before PREREG_R2 was committed: `leak` and `test`. `repair` stays in `action_terms` as a known echo, since `action_named` carries no prediction.
- **Leaky integrator.** Its input pulses are not shown, so a reading of exponential decay alone is scored wrong. Exponential decay is a companion of this class, so naming both together is correct.
- **Power.** P2 has 4 controls per condition per set, so p < 0.05 needs 4 of 4 against 0 of 4.

## Status

PREREG_R2 is committed. No answer exists yet. Nothing here says anything about any model.
