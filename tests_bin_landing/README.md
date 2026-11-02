# Bin-landing test

CC0. Co-authored. Stdlib only. Tags: OBSERVED / DERIVED / PROPOSED. Trailing * = thin volume.

**Question.** When a model meets an unfamiliar pattern, does it land it in a physics/dynamics bin, a function bin, a human-emotion projection, a mystical/archetypal bin, or an honest "unknown"? Does prepending [`GLYPH_METHOD.md`](../GLYPH_METHOD.md) change where it lands?

The design, word lists and decision rules are in [`PREREG.md`](PREREG.md), committed first (b34b709). They are amended by [`PREREG_AMENDMENT_1.md`](PREREG_AMENDMENT_1.md), committed alone (eec815a) before any answer. Where the two conflict, the amendment governs. Read both first.

## Files

```text
PREREG.md               pre-registration: design, bins, word lists, kappa rule, scope
PREREG_AMENDMENT_1.md   conditions A / E / C, contexts E and C (verbatim), P1-P5, scorer features
stimuli.json            24 stimuli x 3 glyph styles (pinned by sha256 in PREREG.md)
prompts/                27 packets = 3 sets x 3 conditions x 3 styles; key.json maps run code -> design
prompts/PILOT.txt       the 9 SHAPE packets (all sets, all conditions): run these first
prompts/retired/        the 9 old condition-B packets, kept for provenance, never run or scored
score.py         emit | score | kappa | --selftest
answers/         where answer files go
```

```text
stimuli     R01-R08  repo records with a recorded function (crosswalk OBSERVED rows); key = recorded function
            D01-D08  synthetic dynamics: leaky integrator, threshold jump, flicker, intermittency, bifurcation,
                     hysteresis, critical slowing, saturation; key = the dynamic
            N01-N08  "not interpretable atm" records; no key; correct = mark unknown
styles      PICTOGRAPH (emoji) | SHAPE (curve-class character) | CODEPOINT (Private Use Area code point, as text)
conditions  A bare | E method in plain English + worked example | C glyph moves + same worked example
```

No stimulus carries a human name for what it is. No answer-key term appears in a stimulus's own description (the selftest checks this).

## Run it on any model, by paste

1. **Pick a set.** Start with the pilot list in `prompts/PILOT.txt`. Then take set 1, 2 or 3 from `prompts/`; each set holds nine files, named by run code. Do not run anything in `prompts/retired/`.
2. **One packet per fresh conversation.** Use a new chat with memory off and no other context, one packet each. Paste the whole file and send it.
3. **Collect the answer.** Copy the model's reply into `answers/<model>_<date>.txt`, for example `answers/modelX_2026-11-03.txt`. Put the packet's run code line (`run code: S1-xxxxxx`) above that reply. One answer file can hold all six packets in a row.
4. **Say what you know about the model.** If it may have read this repository, write `contaminated: possibly` at the top of the answer file.

Answers must keep the `Item N:` labels. Items the model skips are counted as MISSING. They are not counted as wrong.

Do not edit a packet before pasting it. The scorer pins the stimulus and method files by sha256, and the CI test checks that the packets match what `score.py emit` produces.

## Score

```bash
python3 tests_bin_landing/score.py --selftest              # planted answers; prints its check count
python3 tests_bin_landing/score.py score answers/*.txt      # writes results.json, blind_sheet.csv, blind_key.csv
```

For each model, the scorer reports:
- bins per set x style x condition;
- MISSING counts;
- P1, P3' and P4, each as E vs A and C vs A, with counts, one-sided Fisher p and a verdict (SUPPORTED / NOT SUPPORTED / REVERSED / NOT_EVALUABLE). No multiple-comparison correction is applied;
- P2 (condition A style ordering, descriptive);
- P5, C vs E two-sided, on accuracy, break_point_named share and P3' rate;
- the per-answer features `unknown_marked`, `tagged_candidate` and `break_point_named`, with the rules stated in the amendment;
- the SHAPE code-point-name confound (D05 ⋔ PITCHFORK, D06 ⎎ HYSTERESIS SYMBOL).

If more than one model is scored, a pooled table is added; it is descriptive only, and no model is ranked.

## Second scorer and agreement

`blind_sheet.csv` holds answers in random order with no condition, style, stimulus or model. To use it:

1. **Fill the sheet.** A second scorer (a person, or a different model) puts one bin in the `bin` column of each row. The bins are PHYSICS, FUNCTION, PROJECTION, MYSTICAL, UNKNOWN or OTHER, and their definitions are in PREREG.md. The scorer works without the word lists.
2. **Run the agreement check:**

```bash
python3 tests_bin_landing/score.py kappa blind_sheet_scored.csv
```

This prints Cohen's kappa and the confusion matrix. Below 0.6, the script's bins are reported as not tracking the bin definitions, and both scorers' results are reported side by side.

## Known properties of the instrument (DERIVED)

- **Paraphrase.** The word lists are word-prefix matches, and a paraphrase steps around them.
- **Overlapping prefixes.** Overlapping prefixes both count: "feeling" hits both `feel` and `feeling`. The lists were kept as pre-registered.
- **Echo of the descriptions.** Descriptions contain dynamics words, so echoing them raises PHYSICS in both conditions. P1 is a difference between conditions, not a level.
- **Context echo.** The E and C contexts contain words from the UNKNOWN list ("unknown") and the token PROPOSED. A model that copies the context's wording gains on P3'. That is part of the measured effect.
- **Leak sets.** For E and C the leak sets are empty: no answer-key term appears in either context, and the selftest recomputes this. The retired B leak set (R01, R02, R06, D02, D03, D07) applies only to the retired packets.
- **Retired run codes.** An answer file carrying a retired B run code is refused and listed. It is not scored.
- **Run codes.** A run code shows the set number (S1, S2, S3). It does not show the condition, style or stimulus IDs. The contexts make E and C visible to anyone reading a packet.

## Status

No run has been made. `answers/` is empty. Nothing here says anything yet about any model.
