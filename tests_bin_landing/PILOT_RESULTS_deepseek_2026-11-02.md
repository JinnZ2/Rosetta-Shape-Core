# PILOT results: DeepSeek, 2026-11-02

CC0. Co-authored. Tags: OBSERVED / DERIVED / PROPOSED. Trailing * = thin volume.

**PILOT.** One model. SHAPE style only. 3 sets x 3 conditions, n = 72 answers per condition, 216 in all.
- **No model ranking.**
- **Null results are results.**
- **Second scorer.** Kappa is not yet run, so every bin below is the script's word-list bin, unchecked.

```text
answer file   answers/deepseek_2026-11-02.txt   sha256 a3eb106b...bd35b88   (committed alone, 773dc3a)
layout        FOOTER (run code below its reply), read under PREREG_AMENDMENT_2.md (ef0d108)
void run      the first score run used the header-only parser: 192 of 216 answers misattributed.
              Not reported; see amendment 2.
parsed        216 / 216, missing 0, unknown codes 0, retired codes 0, files refused 0
contamination none known: fresh chats, memory off
```

## Bins per condition (OBSERVED, script word lists)

```text
cond  n   PHYSICS FUNCTION PROJECTION MYSTICAL UNKNOWN OTHER   PHYS+FUNC
A     72     11      22        1          0        0      38      33/72  0.46
E     72      4      52        0          0        1      15      56/72  0.78
C     72     16      25        0          0       13      18      41/72  0.57
```

```text
not_interpretable set (24 per condition)
cond  UNKNOWN bin  unknown_marked  tagged_candidate  P3' (both)
A        0/24           0/24             0/24           0/24
E        1/24          20/24            24/24          20/24
C       13/24          16/24            10/24           4/24
```

Over all 72 answers in each condition:

```text
cond  unknown_marked  tagged_candidate  break_point_named
A          0/72            0/72               0/72
E         21/72           72/72               1/72
C         16/72           42/72               0/72
```

```text
keyed accuracy (repo_keyed + synthetic_dynamics, 48 per condition)
cond  repo_keyed  synthetic  total   without D05/D06 (SHAPE name confound)
A       12/24       19/24    31/48         25/42
E       11/24       18/24    29/48         23/42
C       15/24       18/24    33/48         27/42
```

## Predictions (OBSERVED; one-sided Fisher unless noted; no multiple-comparison correction)

```text
test            counts          p (predicted dir)   verdict
P1  E > A       56/72 vs 33/72  6.9e-05             SUPPORTED
P1  C > A       41/72 vs 33/72  0.122               NOT SUPPORTED
P2  style order SHAPE only      -                   NOT_EVALUABLE (one style run; not testable from this pilot)
P3' E > A       20/24 vs 0/24   6.3e-10             SUPPORTED
P3' C > A        4/24 vs 0/24   0.055               NOT SUPPORTED
P4  E > A       29/48 vs 31/48  0.736               NOT SUPPORTED   (leak sets empty; sensitivity = primary)
P4  C > A       33/48 vs 31/48  0.414               NOT SUPPORTED
P5a accuracy     C 33/48, E 29/48   p2 = 0.522      no difference detected
P5b break_point  C 0/72,  E 1/72    p2 = 1.000      no difference detected
P5c P3' rate     C 4/24,  E 20/24   p2 = 7.3e-06    E > C
```

No prediction came out REVERSED.

## Readings (DERIVED; this model, this pilot only)

- **E's P1 gain is FUNCTION, not PHYSICS.** PHYSICS fell from 11 to 4, while FUNCTION rose from 22 to 52. The E context opens with "what it detects, what action it drives", and those words are on the FUNCTION list. The README names this kind of context echo as part of the measured effect.
- **E's P3' result rests on tagging.** E tagged 72 of 72 answers PROPOSED, because the E context says "tag candidates PROPOSED". So E's P3' rate equals its unknown_marked rate.
- **C marks unknown in a different way.** It put 13 of 24 not_interpretable answers in the UNKNOWN bin, against 1 for E and 0 for A, and marked unknown in 16 of 24. It tagged only 10 of 24 PROPOSED, and P3' needs both, so it misses that shift. The UNKNOWN-bin share carries no prediction (amendment 1), so this is descriptive only.
- **break_point_named fired once in 216 answers.** On this model the feature is near-silent, and P5b carries no information.
- **The SHAPE confound is fully visible.** D05 ⋔ and D06 ⎎ were correct in 9 of 9 answers each, in every condition. Without them, accuracy is still flat.
- **A's OTHER share is 38/72.** Many bare answers tied between bins. The kappa check is what decides whether the word lists track the bin definitions here.
- **Direction by set (thin\*).** On PHYS+FUNC, E beat A in all three sets (19 vs 13, 17 vs 8, 20 vs 12). C beat A in two sets of three (12 vs 13, 15 vs 8, 14 vs 12).

## Not yet done

- **Kappa.** `blind_sheet.csv` (216 rows, `bin` empty) goes to a second scorer: a person or a different model. Hand over the sheet only, not `blind_key.csv` or this file. Then run `python3 score.py kappa blind_sheet_scored.csv`.
- **P2.** P2 needs the PICTOGRAPH and CODEPOINT packets.
- **Generality.** Other models are needed before any statement beyond DeepSeek on 2026-11-02.
