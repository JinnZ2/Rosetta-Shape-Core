# Scope-stamp test (uncued)

CC0. Co-authored. Stdlib only. Tags: OBSERVED / DERIVED / PROPOSED. Trailing * = thin volume.

**Question.** Given an old finding stated as plain fact, with no hint of its scope, does a model name the finding's scope stamp (when, on whom, under what assumptions) before applying it? Does a one-line method change that?

**Method under test (PROPOSED).** Every finding carries a scope stamp: its period, its sample, and its era's shared assumptions and exclusions. The finding is valid inside the stamp, and an error when transported outside it.

Design, lists and decision rules are in [`PREREG_SCOPE.md`](PREREG_SCOPE.md), which was committed alone first (a05e215). Read it first.

## Files

```text
PREREG_SCOPE.md    pre-registration: items table, S method line, lists, rules, P1-P3, kappa rule
build_items.py     writes items_scope.json (deterministic); pinned
items_scope.json   20 items: 16 scoped (key stamp + CARRIED source each) + 4 controls; pinned
score_scope.py     emit | score | kappa | --selftest
prompts/           2 packets (A, S); key.json maps run code -> condition, item order
PILOT_SCOPE.txt    both packets as plain text, ready to paste
answers/           where answer files go
```

## Run it

1. Paste each packet from `PILOT_SCOPE.txt` (everything between its `=====` lines) into a fresh conversation, with memory off.
2. Copy both replies into `answers/<model>_<date>.txt`. Put each run code line either above every reply or below every reply, the same way for the whole file.
3. Score:

```bash
python3 tests_scope_stamp/score_scope.py --selftest
python3 tests_scope_stamp/score_scope.py score tests_scope_stamp/answers/*.txt
python3 tests_scope_stamp/score_scope.py kappa blind_sheet_scope_scored.csv
```

## Known properties (DERIVED)

- **Sources are CARRIED.** They come from model memory and were not fetched or verified in this session. Verify each one before any result is quoted.
- **Matching.** Terms are word-prefix matches, so a paraphrase steps around them. "Transported" is a lexical proxy. The second scorer and kappa check both.
- **Echo guard.** No stamp, transport, hedge or check term appears in the item texts or in the S line; the selftest checks this.
- **Loose control term (found after pinning, kept as pinned).** In C03, the correct term `no` matches as a prefix, so "normal" and "not" count as correct. `control_correct` carries no prediction. A fix would go in a dated amendment with a new pin.
- **Power.** There are 16 scoped answers per condition, so a null at this n is weak evidence.

## Status

PREREG_SCOPE is committed. No answer exists yet. Nothing here says anything about any model.
