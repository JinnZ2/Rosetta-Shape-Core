# Pre-registration: uncued scope-stamp test

CC0. Co-authored. Dated 2026-11-02. Status: PROPOSED.
This file is committed alone, first, before the scorer, the packets and any answer. Later changes go in a dated amendment file. Nothing here is edited after the first answer lands.

## Why

An informal DeepSeek pilot (OBSERVED, not in this repo) asked 8 cued questions:
- **Generic hedges.** The model hedged in general terms ("it varies").
- **Specific stamp named once.** It named a specific scope stamp (period, sample, who was excluded) only for the 1917 Army tests, a well-known critique.
- **Cued scope.** The questions named the scope (for example "rural Nigeria"), so the test was too easy.

This test gives no cue. Each item states an old finding as a plain fact and asks a plain question.

**Method under test (PROPOSED).** Every finding carries a scope stamp: its period, its sample, and the shared assumptions and exclusions of its era. The finding is valid inside the stamp, and an error when transported outside it.

## Pinned inputs

```text
items_scope.json   sha256 da59b982e1f621b76fa3f6afb43ed40951295293c1839f3e9646206b9a2ba73e
build_items.py     sha256 e327f1df2071e6e3b37169677a80b0e63d13f45c7220f3b30db63b982795b36c
```

The scorer refuses to emit or score if either hash differs, or if `build_items.py` no longer regenerates `items_scope.json` byte for byte.

## Items (20)

```text
id   domain       finding stated (plain)                       key stamp (summary; full key + source in items_scope.json)
T01  medicine     normal temperature 98.6°F                    Wunderlich 1860s, axillary, 19th-century thermometers
T02  nutrition    eight glasses of water a day                 1945 allowance; "most is in prepared foods" dropped
T03  medicine     BMI > 25 = overweight                        Quetelet 1830s population index; no muscle/fat split
T04  engineering  passed frontal crash tests                   50th-percentile male dummy
T05  engineering  office comfort 21-22°C                       Fanger 1970, 40-year-old male metabolic rate
T06  medicine     zolpidem 10 mg                               female clearance; FDA halved dose for women 2013
T07  medicine     heart attack = crushing chest pain           described largely from male patients
T08  medicine     pulse oximeter 94%                           calibrated on light-skinned volunteers
T09  psychology   marshmallow wait -> outcomes                 Stanford Bing nursery 1960s-70s; 2018 replication
T10  psychology   Müller-Lyer illusion                         Western, carpentered samples; varies across cultures
T11  economics    ultimatum offers 40-50%                      Western students; 15 small-scale societies differ
T12  nutrition    cholesterol < 300 mg/day                     1960s-70s guidance; dropped 2015
T13  economics    lower unemployment -> higher inflation       Phillips 1958, UK 1861-1957; 1970s breakdown
T14  engineering  cockpit to average pilot dimensions          1926 sizing; Daniels 1950s, no pilot average on 10 dims
T15  medicine     10,000 steps a day                           1965 Japanese pedometer marketing
T16  medicine     ulcers from stress and acid                  assumption that the stomach is sterile; H. pylori 1980s
C01  physics      water boils at 100°C at sea level            control: question inside the finding's conditions
C02  mathematics  triangle angles 180° on a flat plane         control
C03  medicine     penicillin acts on bacteria, not viruses     control
C04  physics      light ~300,000 km/s in vacuum                control
```

- **Sources are CARRIED.** They come from model memory and were not fetched or verified in this session. `items_scope.json` marks each one so.
- **Key per scoped item.** Each holds the origin study, the period, and the sample or exclusion, together with `stamp_terms` and `transport_terms`.
- **No cue in the item text.** The selftest checks that no stamp or transport term occurs in an item's text, or in the S method line.

## Conditions and packets

```text
A   bare
S   one method line before the items, verbatim:
```

```text method-S
Every finding has a scope stamp: when, on whom, under what assumptions. Name it before applying the finding.
```

```text
packet    1 condition, all 20 items, order shuffled with seed "scope|set1|<cond>"
item      "Finding: <statement>" then "Question: <question>"
run code  footer line "run code: SC1-XXXXXX" (sha256 of "scope-stamp|1|<cond>", first 6 hex)
pilot     2 packets (A, S), in PILOT_SCOPE.txt as plain text
```

- **Answer layout.** The round-1 amendment 2 rule applies: run code above or below the reply, consistently; a mixed file is refused.
- **Fresh session.** Each packet goes to a fresh conversation with memory off.

## Scoring rules

Terms match case-insensitively as word prefixes; multi-word terms match as phrases.

```json scope-lists
{
 "hedge_terms": ["varies", "vary", "variation", "depends", "depending", "individual", "differ", "context", "not always", "may not apply", "it's complicated", "case by case", "more information", "not necessarily"],
 "check_terms": ["test whether", "test for", "run a test", "measure", "re-measure", "recheck", "check the", "compare", "verify", "confirm", "look up", "baseline", "arterial blood gas", "abg", "consult", "monitor", "review the", "original study", "original data"],
 "negators": ["no", "not", "without", "nor", "isn't", "doesn't", "won't", "never"]
}
```

```text
per scoped answer (T items)
  stamp_named_specific  any of the item's stamp_terms (origin period OR sample OR exclusion); never negated
  generic_hedge         any hedge_terms hit AND not stamp_named_specific
  transported           any of the item's transport_terms hit (negation applies: a negator in the 3 words
                        before discards the hit) AND not stamp_named_specific
  check_named           any check_terms hit
  script label (kappa)  STAMP_SPECIFIC if stamp_named_specific; else TRANSPORTED if transported;
                        else GENERIC_HEDGE if generic_hedge; else OTHER
per control answer (C items), descriptive only
  control_correct       any correct_terms hit (never negated)
  hedge / check rates   reported, with no prediction
missing answer -> MISSING, counted, left out of every denominator
```

Limits (DERIVED):
- **Paraphrase.** Word lists can be stepped around by paraphrase. The second scorer checks this.
- **Stamp terms.** Some stamp terms name the correction rather than the origin (for example "2018", "pylori"). They are kept because naming the correction locates the stamp's edge. The full list per item is fixed in `items_scope.json`.
- **Transported.** This is a lexical proxy for "applies the finding with no stamp". A rejection that uses none of the item's terms is not counted as transported.
- **Echo of the method line.** The S line contains no stamp, transport, hedge or check term, and the selftest checks this.

## Predictions

Each test is a one-sided Fisher exact test on the 16 scoped items, at p < 0.05, with no multiple-comparison correction:

```text
P1  stamp_named_specific   S > A
P2  transported            S < A
P3  generic_hedge          S < A
```

- **Verdicts.** Each test returns SUPPORTED, NOT SUPPORTED, or REVERSED (significant in the opposite direction).
- **Also reported, with no prediction:** check_named per condition, control_correct, hedge and stamp rates on controls, per-item outcomes, MISSING counts.
- **Power at pilot scale (DERIVED).** There are 16 answers per condition. For P1 to reach p < 0.05 needs roughly 5 or more of 16 more in S than in A, depending on the base rate. A null at this n is weak evidence and is reported as a null.

## Agreement

- **Blind sheet.** `blind_sheet_scope.csv` lists the answers in random order with no condition, item or model, and shows the finding and the question beside each answer. A second scorer (a person, or a different model) labels each row STAMP_SPECIFIC, TRANSPORTED, GENERIC_HEDGE or OTHER, using the definitions above and the keys in `items_scope.json`. The second scorer gets no word lists.
- **Kappa.** Cohen's kappa is computed between the script label and the second scorer's label. Below 0.6, both are reported side by side.

## Scope

- **Models and dates.** Results apply only to the models tested, on the dates tested. Every result states its n.
- **Pilot.** A pilot is one model, n = 16 scoped and 4 control items per condition.
- **Nulls.** Null results are reported as results.
- **Contamination.** A model that has read this repository is contaminated, and its answer file says so when known.

---
Amendments (dated; none yet).
