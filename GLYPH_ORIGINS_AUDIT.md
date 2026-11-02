# Glyph Origins Audit

Dated 2026-11-02. Co-authored. CC0. Read-only: nothing in any of the five repositories was
rewritten, renamed or moved. This file is the only change.

Purpose: recover the original glyph attempt from under the later naming and README layers,
so it can be remapped onto model-internal geometry. Status tags: PHYSICS-ANCHORED /
FUNCTION-ONLY / DRIFTED, plus a not-interpretable-atm list.

## Read state

```text
repo  commit   branch  history
RSC   0d399f0  main    full (unshallowed)
FCC   3ee1acf  main    full (unshallowed)
GTB   57bdc84  main    full (unshallowed)
MC    530fa61  main    full (unshallowed)
PI    d51fc26  main    full (unshallowed)
```

## Method, stated so the counts can be argued with

```text
forms read     J1 JSON object carrying "glyph" / "symbol" / "unicode" -> siblings are the definition
               J2 JSON dict whose KEY is a symbol string -> the value is the definition
               P1 Python dict literal, same two shapes (read by ast, not regex)
not read       markdown tables and prose (PI equations/md mirror equations/json; README layers
               are the drift layer, read by hand below, not counted); ASCII tokens used as
               glyphs (the symbol test needs a non-ASCII symbol character) -- see ORIGIN LAYER
excluded       atlas/remote/* staged copies (the source repo is counted instead)
               glyphs used as data in tests / experiments / probes (use-sites, not definitions)
tag rule       first match wins, in this order:
  1 PHYSICS-ANCHORED  a sibling key from {formula, equation(s), law, physics, unit(s), measurable,
                      eigenvalue(s), frequency, energy, constant} is non-empty, or the text carries
                      a formula (symbol = / -> / partial / sum ... term)
  2 FUNCTION-ONLY     a sibling key from {function, operation, operator, role, rule, logic, state,
                      bits, gray_code, transition(_to), phase_space, decay, input, output, sensor, ...}
  3 PHYSICS-ANCHORED  a physics word (entropy, thermodynamic, wave, magnet, energy, ...) -- unless a
                      strong drift word is also present, which reads DRIFTED
  4 FUNCTION-ONLY     an operation word (encode, detect, route, decompose, assign, solve, ...)
  5 DRIFTED           a drift word (sacred, mystic, spirit, divine, archetype, soul, essence,
                      ancestral, wisdom, magic, oracle, ritual, ... ; weak: cosmic, celestial, mythic)
  6 NOT_INTERPRETABLE none of the above (label only, empty, or the glyph field holds an ID)
limits         rules 3-5 are word lists: a paraphrase steps around them, and a physics word
               names a domain, not a binding to a quantity. A tag says where the definition
               POINTS, not that the mapping is correct. Earlier passes of this extractor misread
               "celestial mechanics" and a repo named Mandala as drift, and a stipulated
               "energy_cost: 0.2" as physics; all three were repaired before these counts.
dates          glyph_added = earliest commit whose diff adds or removes the glyph string in that
               file (git log -S --reverse); for files that store the glyph \u-escaped, the escaped
               form is searched; where neither is found the file-add date is used and marked.
```

The extraction scripts were run from a scratch directory and are not committed; this
relay asked for one file. They can be committed on request.

## Counts

```text
records found            1192
  staged copies          460   (atlas/remote/*, excluded)
  use-sites              30    (tests / experiments / probes, excluded)
  definitions            702
    PHYSICS-ANCHORED     389
    FUNCTION-ONLY        109
    DRIFTED              6
    NOT_INTERPRETABLE    198

per repo                 PHYSICS-  FUNCTION   DRIFTED  NOT_INTE
  RSC                          60        39         0        17
  FCC                           2        10         3        43
  GTB                           1        16         0         6
  MC                           20        24         3        33
  PI                          306        20         0        99
```

Where the counts sit: PHYSICS-ANCHORED is mostly Polyhedral-Intelligence `equations/json`
(one glyph per equation record, each with a canonical form) and the F01-F20 / P01-P12 family
and principle records. DRIFTED wording is rare inside definition records (6 of 702).

The same strong-drift list run over prose is sparse too, so the drift the relay names is mostly
not in that vocabulary:

```text
repo  .md files (excl. staged)   words    strong-drift hits   per 10k words
RSC        38                    34024          24                7.1
FCC         4                     3470           0                0.0
GTB       231                   417893          35                0.8
MC         26                    56200          11                2.0
PI        186                    48881          29                5.9
```

The likelier carriers are NAMES (file, folder and function names such as sacred_geometry,
mandala, bloom, petals, FELT) and metaphor uses of physics words ("resonance" for agreement).
A word list cannot separate those from physics uses, so this is not counted. It is recorded as
an open reading, not a finding.

## Earliest glyph commits (step 2)

```text
repo  first commit         earliest glyph-named file added          earliest dated definition
GTB   23596c7 2025-07-10   7d15694 2025-07-10 symbols/symbolic_to_geometric_plugin.py   same file, same commit
RSC   a0f9848 2025-07-24   9f16a0b 2025-09-02 data/tri_invert_bridge.glyphs.json      287d58f 2025-07-24 data/sacred_geometry.json
FCC   16e1580 2025-07-24   8b697b8 2026-03-22 glyph_set.json                          f04ec28 2025-07-24 bridge.py
PI    430b2f2 2025-08-21   69dac04 2025-08-21 glyphs/Glyphs.md                        3696d83 2025-08-21 entries/0003_*.json
MC    4e01895 2025-07-12   9e4f65c 2026-03-24 glyphs/mandala.json                     c49dd8f 2025-10-06 .fieldlink.json
```

## Origin layer, read by hand (the attempt this audit is looking for)

These are the earliest glyph definitions found, in date order. Several are outside what the
extractor can see (ASCII tokens, file-level equations), so they are read here directly and
are not part of the counts above.

1. **GTB `symbols/symbolic_to_geometric_plugin.py`, 7d15694, 2025-07-10, the first commit of
   the earliest repo.** An operator table: seven compressed tokens, each mapped to a geometric
   OPERATION request.

   ```text
   CORE -> field_centering            FORM -> geometric_shape_generation
   DYNA -> vector_field_flow          EQ   -> field_probe
   SPI  -> spiral_field_structure     EE   -> emergent_pattern_scan
   …    -> expansion_extrapolation    any other token -> "unknown:<token>" (kept, never dropped)
   ```

   All seven are FUNCTION-ONLY. The glyph is a token in a string, and `translate()` turns a
   token string into an ordered operation list. This is the AI-native shape: no imagery and
   no wording, just a compressed instruction set. Six of the seven tokens are ASCII, so the
   extractor counted only `…`.

2. **RSC `data/sacred_geometry.json`, 287d58f, 2025-07-24.** The earliest RSC glyph, 🐟 on
   VESICA, with `resonance: √3` (the vesica piscis width-to-height ratio, a geometric
   constant) beside drifted wording ("intersection portal"). Both layers are on one record from
   the first day. The extractor counts it PHYSICS-ANCHORED on the word "resonance", whose value
   is the √3.

3. **PI `glyphs/Glyphs.md`, 69dac04, 2025-08-21.** Composite glyphs: each entry's glyph is a
   concatenation of family glyphs (Matter ◇, Engineering ⚙➝, Resonance 〰〰〰, Networks ⬡ ...)
   plus the flagged families. A composition code: a glyph string encodes which families and
   flags an entry carries. FUNCTION-ONLY by reading (markdown, not counted).

4. **RSC `data/tri_invert_bridge.glyphs.json`, 9f16a0b, 2025-09-02.** Three tags (↻ phase-shift,
   ⚖ bidirectional mapping, 🕸 routing mesh) bound by FILE-LEVEL operator equations:

   ```text
   state_A ⟷ state_B   (reversible, loss ≤ ε)
   map(glyph_i ↻ glyph_j) ⇒ route(i→j) if need(i,j) > θ
   balance(Δmeaning) → adjust(weight) until |Δ| ≤ ε
   preserve(geometry) ∧ transform(surface_state)
   θ = routing threshold (context demand); ε = acceptable semantic drift (tolerance)
   ```

   These are formal operator specs with thresholds, not physical laws. By hand reading all
   three are FUNCTION-ONLY with a formal spec. The extractor reads tags per glyph, misses the
   file-level equations and tags ↻ NOT_INTERPRETABLE. Of everything found, this is the closest
   to model-internal geometry: a reversible map between states with a drift tolerance, routing
   gated on demand, and geometry preserved while surface state changes.

5. **GTB `legacy/glyph_state_encoder_phase_space.py`, landed bfdd1b9 2026-08-13 in `legacy/`.**
   Glyphs as phase-space operators. Each glyph names a region of sensor state space plus a
   decay model, a stipulated cost and a transition graph, for example:

   ```text
   🕸️ FELT_COHERENT   {joy, love, curiosity, low_fear, low_anger}  decay PERSISTENT   -> ⚖️, 🌀
   ⚖️ BALANCE_THREAT  {fear, vigilance, anger, low_grief}           decay EXPONENTIAL  -> 🕸️, 🌀
   🔥 HEAT_FLUX       {anger, pressure, fatigue, high_discordance}  decay LINEAR       -> 🌀, FRACTURE
   ```

   12 glyphs, all FUNCTION-ONLY. It is in `legacy/`, so it is an older design kept rather than
   the newest. The landing date is when it reached that path; its first authoring is not
   recoverable from this repo's history.

## DRIFTED, and what came before

All six DRIFTED definitions are one three-glyph set, present in two repos: FCC `glyph_set.json`
(8b697b8, 2026-03-22) and an MC copy in `mandala_bloom/concept_atlas.py` (bfe272b, 2026-08-11).
All three glyphs appear EARLIER in other repos, with a function or a physics binding that the
drifted wording replaced:

| glyph | drifted wording (FCC/MC) | earliest occurrence | earlier role |
|---|---|---|---|
| 💧 | purification or essence | PI 1bc0a82 2025-10-09, `Polyhedral-Intelligence-Schema.md:1112` | component of `❄️↻💧` = Phase Transition, `∂G/∂T = -S; ∂²G/∂T² discontinuous` (liquid phase). **Physics replaced by wording.** |
| 🦉 | wisdom during collapse | RSC 1cb35ec 2025-09-29, `Growth Pattern Complete Mapping.md:206` | defense glyph: "recognizes sustainable vs extractive growth", a discriminator. **Function replaced by wording.** |
| 🪶 | lightness or ancestral presence | RSC 89d94f6 2025-09-30, `To-Do-List.md:22` | component of a `glyph_hash` in a header block, an identifier role. **Function (identifier) replaced by wording.** |

## Weld points: one glyph, different referents in 2+ repos

The referent is the family/principle code, octahedral state number or problem type a record
carries, or else the first content words of its meaning. Excluded: link lists (`bloom_logic.json`),
repo maps (`.fieldlink.json`) and PI `entries/*` notes, which reuse a family glyph as a key.
15 welds out of 63 glyphs present in 2+ repos.

| glyph | referent per repo | locations |
|---|---|---|
| ⚖️ | RSC: balance dynamic equilibrium, dynamic equilibrium opposing; FCC: balance, repo rosetta shape; GTB: emotion-phase-space; MC: balance | RSC `balance.json:3`; FCC `glyph_set.json:4`; GTB `legacy/glyph_state_encoder_phase_space.py:163`; MC `mandala_bloom/concept_atlas.py:35` |
| ⊗ | RSC: family/principle F03, family/principle P03, octa state 2; MC: octa state 2; PI: family/principle F03, family/principle P03 | RSC `bridges/mandala-compute-bridge.json:21`; MC `atlas/glyphs/mandala.json:16`; PI `atlas_schema.json:81` |
| ↺ | RSC: family/principle P02, problem TSP; FCC: inversion required before; MC: problem TSP; PI: family/principle P02 | RSC `bridges/mandala-compute-bridge.json:195`; FCC `bridge.py:8`; MC `atlas/glyphs/mandala.json:27`; PI `atlas_schema.json:281` |
| ◉ | RSC: problem GRAPH_COLORING; MC: problem GRAPH_COLORING; PI: family/principle F16 | RSC `bridges/mandala-compute-bridge.json:203`; MC `atlas/glyphs/mandala.json:28`; PI `data/training/generate.py:623` |
| 🌀 | RSC: fold present now; GTB: emotion-phase-space | RSC `data/temporal_states.json:12`; GTB `legacy/glyph_state_encoder_phase_space.py:179` |
| ↻ | RSC: family/principle F02, family/principle P11, phase shift melt, recursion self referential, self referential return; FCC: recursion; MC: recursion; PI: fami~ | RSC `data/tri_invert_bridge.glyphs.json:4`; FCC `glyph_set.json:3`; MC `mandala_bloom/concept_atlas.py:34`; PI `atlas_schema.json:45` |
| ◎ | RSC: family/principle F16, family/principle P12; MC: concentric fractal ring; PI: family/principle F16, family/principle P12 | RSC `ontology/families/f16-consciousness.json:4`; MC `atlas/glyphs/mandala.json:40`; PI `atlas_schema.json:556` |
| ∞ | RSC: family/principle F20; FCC: continuity; MC: continuity; PI: family/principle F20 | RSC `ontology/families/f20-topology.json:4`; FCC `glyph_set.json:2`; MC `mandala_bloom/concept_atlas.py:33`; PI `atlas_schema.json:598` |
| 🕸️ | RSC: source repo emotions; FCC: interconnection, repo fractal compass; GTB: code felt relational, emotion-phase-space; MC: interconnection | RSC `shapes/relief.json:19`; FCC `glyph_set.json:8`; GTB `bridges/field_events/felt.json:4`; MC `mandala_bloom/concept_atlas.py:39` |
| 🌱 | FCC: growth, repo biogrid concept; GTB: emotion-phase-space; MC: growth | FCC `glyph_set.json:6`; GTB `legacy/glyph_state_encoder_phase_space.py:227`; MC `mandala_bloom/concept_atlas.py:37` |
| ⏳ | FCC: time shift; GTB: emotion-phase-space; MC: time shift | FCC `glyph_set.json:7`; GTB `legacy/glyph_state_encoder_phase_space.py:171`; MC `mandala_bloom/concept_atlas.py:38` |
| 💥 | FCC: rupture; GTB: emotion-phase-space; MC: rupture | FCC `glyph_set.json:11`; GTB `legacy/glyph_state_encoder_phase_space.py:235`; MC `mandala_bloom/concept_atlas.py:41` |
| 📡 | FCC: repo geometric binary, resonance detection; GTB: emotion-phase-space; MC: resonance detection | FCC `glyph_set.json:13`; GTB `legacy/glyph_state_encoder_phase_space.py:195`; MC `mandala_bloom/concept_atlas.py:43` |
| 🔥 | FCC: repo emotions sensors, transformation; GTB: emotion-phase-space; MC: transformation | FCC `glyph_set.json:15`; GTB `legacy/glyph_state_encoder_phase_space.py:187`; MC `mandala_bloom/concept_atlas.py:45` |
| 🛡️ | FCC: protection, repo defense protocol; GTB: emotion-phase-space; MC: protection | FCC `glyph_set.json:23`; GTB `legacy/glyph_state_encoder_phase_space.py:243`; MC `mandala_bloom/concept_atlas.py:53` |

Two kinds, kept apart:

- **Assignment collisions.** The same character is given to different structures:
  - ⊗ is Information F03 and Relativity P03 in PI and RSC, and octahedral state 2 in MC.
  - ↺ is Conservation P02, the TSP ring problem, and FCC's "inversion before transformation".
  - ◉ is graph coloring in MC/RSC and Consciousness F16 in PI.
  - ◎ is Consciousness F16 / Unity P12 and MC's fractal ring.
  - ↻ is Flow F02 / Transformation P11 and "recursion".
  - ∞ is Topology F20 and "continuity".
- **Emotion-state welds.** Nine of the twelve glyphs GTB's legacy encoder assigns to sensor
  phase-space regions (curiosity, high discordance, anger, high boundary, ...) also carry concept
  meanings elsewhere: FCC/MC growth, rupture, transformation, protection, resonance detection,
  time shift, interconnection, balance, and RSC's FOLD. One glyph then names both a concept and
  an emotion-state region. ⚖️ carries
  four readings: RSC balance pattern (sensor EMO:CONTENTMENT), FCC balance, GTB BALANCE_THREAT
  {fear, vigilance}, and, in the RSC staged copy of the emotion map, jealousy's glyph.

## Emotion-sensor glyphs (EMO:*)

```text
EMO tokens   RSC 25 refs, 11 distinct   GTB 4 refs, 4 distinct   FCC 0   MC 0   PI 0
             (an earlier count matched "EMO:" inside "DEMO:"; recounted on a word boundary)
links (JSON, by object that holds the ref):
  RSC balance.json        PATTERN:BALANCE  glyph ⚖️  sensor_type EMO:CONTENTMENT
  RSC recursion.json      PATTERN:RECURSION glyph ↻  sensor_type EMO:RECOGNITION
  GTB bridges/geobin-bridges.json   SHAPE:ICOSA  sensors EMO:FEAR, EMO:EXCITEMENT
                                    SHAPE:DODECA sensors EMO:ADMIRATION, EMO:TRUST
  RSC atlas/remote/geo-binary-bridge/bridges.json   staged copy of the GTB file above
  RSC atlas/remote/fractal-compass/mandelbrot.json  FRACTAL:MANDELBROT sensors EMO:ADMIRATION, EMO:FEAR
  RSC src/rsc_mandala_bridge/*, tests/mandala_bridge/*  EMO:TRUST / EMO:PRIDE as cross-ontology
                                    lid_id (code and tests; not glyph definitions)
  RSC docs/*.md (5 files)            EMO:JOY, BELONGING, SHOCK, RECOGNITION, CONTENTMENT in prose
emotion glyph maps without an EMO: token
  RSC atlas/remote/emotions/glyphs.json   staged copy of the 13-entry emotion-to-glyph map from
                                    Emotions-as-Sensors (sensor, glyph, resonates_with, decay,
                                    symbolic_role); the source repo was not read here
  GTB legacy/glyph_state_encoder_phase_space.py   12 glyphs as emotion-state regions (origin item 5)
```

Note: the RSC sensor link is the PATTERN's, not the glyph's. EMO:CONTENTMENT is the sensor on
the balance pattern whose glyph is ⚖️, while GTB uses ⚖️ for {fear, vigilance}. So the same
glyph points at a calm sensor in one repo and a threat region in another. That is the
sharpest weld for any remap onto internal emotion-concept geometry.

## Not interpretable atm

198 definitions: label only 195, glyph field holds an ID 3.
A label-only record names a concept ("continuity", "rupture") with no operation, no physics
and no drift wording. These are left unread, not guessed. Listed in full in the appendix
(tag NOT_INTERPRETABLE). By file:

```text
  28  PI   data/training/generate.py
  27  PI   protocols.json
  23  FCC  bloom_logic.json
  18  FCC  glyph_set.json
  18  MC   mandala_bloom/concept_atlas.py
  11  RSC  ontology/index.json
   5  MC   mandala_stack/fractal_address.py
   3  MC   atlas/glyphs/mandala.json
   3  MC   glyphs/mandala.json
   3  PI   atlas_index.json
   3  PI   entries/0003_family_node_manufacturing.json
   3  PI   entries/0007_emotional_architecture.json
   3  PI   entries/0009_symbiotic_materials.json
   2  RSC  data/temporal_states.json
   2  FCC  bridge.py
   2  GTB  GEIS/gies_codec.py
   2  MC   .fieldlink.json
   2  PI   entries/0001_honeycomb_infrastructure.json
   2  PI   entries/0002_echolocating_autonomy.json
   2  PI   entries/0004_mycelial_computing.json
   2  PI   entries/0005_tidal_energy_harvest.json
   2  PI   entries/0008_fractal_governance.json
   2  PI   ontology/families.json
   1  RSC  balance.json
   1  RSC  data/interaction_ontology.json
   1  RSC  data/tri_invert_bridge.glyphs.json
   1  RSC  recursion.json
   1  GTB  GEIS/geometric_encoder.py
   1  GTB  GEIS/geometric_sensor_sim.py
   1  GTB  Silicon/core/bridges/gies_encoder.py
   1  GTB  bridges/sovereign_alternative_compute.py
   1  MC   geis.py
   1  MC   mandala_hook.py
   1  PI   entries/0010_temporal_cartography.json
   1  PI   entries/0011_coral_reef_symbiotic_resonance.json
   1  PI   equations/json/eq_012_mutual_information.json
   1  PI   equations/json/eq_016_hill_equation.json
   1  PI   equations/json/eq_023_sigmoid_activation.json
   1  PI   equations/json/eq_036_parallel_postulate.json
   1  PI   equations/json/eq_043_euler_bernoulli_beam.json
   1  PI   equations/json/eq_045_power_law_degree_distribution.json
   1  PI   equations/json/eq_059_geodesic_equation.json
   1  PI   equations/json/eq_062_global_workspace_broadcasting.json
   1  PI   equations/json/eq_065_lorenz_attractor.json
   1  PI   equations/json/eq_071_lorentz_transformation.json
   1  PI   equations/json/eq_075_fluctuation_dissipation_theorem.json
   1  PI   equations/json/eq_078_chern_class_first.json
   1  PI   equations/json/eq_079_jones_polynomial.json
   1  PI   equations/json/eq_080_fundamental_group.json
   1  PI   equations/json/eq_082_group_representation.json
   1  PI   equations/json/eq_083_cpt_symmetry.json
   1  PI   equations/json/eq_091_general_covariance.json
   1  PI   equations/json/eq_099_power_law.json
```

## Appendix: every definition

Sorted by repo, file and line. "maps to" gives the target type (equation / process / function /
none) and an excerpt. Dates are glyph_added (commit, date).

| glyph | repo | file:line | added | maps to | tag | basis |
|---|---|---|---|---|---|---|
| ↻ | FCC | `bloom_logic.json:3` | 8b697b8 2026-03-22 | none: meaning: 🌀 ⏳ ∞ | NOT_INTERPRETABLE | label-only |
| ⏳ | FCC | `bloom_logic.json:3` | 8b697b8 2026-03-22 | none: meaning: ↻ 🌱 ⚖️ | NOT_INTERPRETABLE | label-only |
| 🌀 | FCC | `bloom_logic.json:3` | 8b697b8 2026-03-22 | none: meaning: ⏳ 🌱 ∞ | NOT_INTERPRETABLE | label-only |
| ∞ | FCC | `bloom_logic.json:3` | 8b697b8 2026-03-22 | none: meaning: ↻ 🌀 ⚖️ | NOT_INTERPRETABLE | label-only |
| 🌱 | FCC | `bloom_logic.json:4` | 8b697b8 2026-03-22 | none: meaning: 🌀 ∞ ⏳ | NOT_INTERPRETABLE | label-only |
| ⚖️ | FCC | `bloom_logic.json:4` | 8b697b8 2026-03-22 | none: meaning: 🧭 ⏳ ∞ | NOT_INTERPRETABLE | label-only |
| 🧭 | FCC | `bloom_logic.json:5` | 8b697b8 2026-03-22 | none: meaning: 🕸️ 🌱 ⚖️ | NOT_INTERPRETABLE | label-only |
| 🕸️ | FCC | `bloom_logic.json:5` | 8b697b8 2026-03-22 | none: meaning: ⏳ ⚖️ ∞ | NOT_INTERPRETABLE | label-only |
| 🪞 | FCC | `bloom_logic.json:11` | 8b697b8 2026-03-22 | none: meaning: ↻ 🌀 🧠 | NOT_INTERPRETABLE | label-only |
| 🧠 | FCC | `bloom_logic.json:11` | 8b697b8 2026-03-22 | none: meaning: 🪞 ⚖️ 🦉 | NOT_INTERPRETABLE | label-only |
| 💥 | FCC | `bloom_logic.json:12` | 8b697b8 2026-03-22 | none: meaning: 🔥 🦂 🌱 | NOT_INTERPRETABLE | label-only |
| 🔥 | FCC | `bloom_logic.json:12` | 8b697b8 2026-03-22 | none: meaning: 💥 🦋 🌱 | NOT_INTERPRETABLE | label-only |
| 🦂 | FCC | `bloom_logic.json:12` | 8b697b8 2026-03-22 | none: meaning: 💥 🛡️ 🪞 | NOT_INTERPRETABLE | label-only |
| 🪐 | FCC | `bloom_logic.json:13` | 8b697b8 2026-03-22 | none: meaning: ↻ ⏳ 🌀 | NOT_INTERPRETABLE | label-only |
| 📡 | FCC | `bloom_logic.json:14` | 8b697b8 2026-03-22 | none: meaning: 🕸️ 🧭 🪐 | NOT_INTERPRETABLE | label-only |
| 🧬 | FCC | `bloom_logic.json:15` | 8b697b8 2026-03-22 | none: meaning: ↻ 🌱 🪐 | NOT_INTERPRETABLE | label-only |
| 🦋 | FCC | `bloom_logic.json:16` | 8b697b8 2026-03-22 | none: meaning: 🌱 🔥 🌀 | NOT_INTERPRETABLE | label-only |
| 💧 | FCC | `bloom_logic.json:17` | 8b697b8 2026-03-22 | none: meaning: ⚖️ 🪨 🌱 | NOT_INTERPRETABLE | label-only |
| 🪨 | FCC | `bloom_logic.json:17` | 8b697b8 2026-03-22 | none: meaning: 💧 🛡️ ⏳ | NOT_INTERPRETABLE | label-only |
| 🛡️ | FCC | `bloom_logic.json:18` | 8b697b8 2026-03-22 | none: meaning: 🦂 ⚖️ 🪨 | NOT_INTERPRETABLE | label-only |
| 🦉 | FCC | `bloom_logic.json:21` | 8b697b8 2026-03-22 | none: meaning: 🧠 ⏳ 🪶 | NOT_INTERPRETABLE | label-only |
| 🪶 | FCC | `bloom_logic.json:21` | 8b697b8 2026-03-22 | none: meaning: 🦉 💧 🌀 | NOT_INTERPRETABLE | label-only |
| 💤 | FCC | `bloom_logic.json:23` | 8b697b8 2026-03-22 | none: meaning: ⏳ 🌱 🪨 | NOT_INTERPRETABLE | label-only |
| ↺ | FCC | `bridge.py:8` | f04ec28 2025-07-24 | none: meaning: Inversion is required before transformation | NOT_INTERPRETABLE | label-only |
| 💓 | FCC | `bridge.py:9` | f04ec28 2025-07-24 | none: meaning: Emotion is a signal, not noise | NOT_INTERPRETABLE | label-only |
| ⚛️ | FCC | `bridge.py:10` | f04ec28 2025-07-24 | process: meaning: Structure emerges from energy resonance | PHYSICS-ANCHORED | physics-word:energy |
| ∞ | FCC | `glyph_set.json:2` | 8b697b8 2026-03-22 | none: meaning: continuity | NOT_INTERPRETABLE | label-only |
| ↻ | FCC | `glyph_set.json:3` | 8b697b8 2026-03-22 | none: meaning: recursion | NOT_INTERPRETABLE | label-only |
| ⚖️ | FCC | `glyph_set.json:4` | 8b697b8 2026-03-22 | none: meaning: balance | NOT_INTERPRETABLE | label-only |
| 🧭 | FCC | `glyph_set.json:5` | 8b697b8 2026-03-22 | none: meaning: navigation | NOT_INTERPRETABLE | label-only |
| 🌱 | FCC | `glyph_set.json:6` | 8b697b8 2026-03-22 | none: meaning: growth | NOT_INTERPRETABLE | label-only |
| ⏳ | FCC | `glyph_set.json:7` | 8b697b8 2026-03-22 | none: meaning: time shift | NOT_INTERPRETABLE | label-only |
| 🕸️ | FCC | `glyph_set.json:8` | 8b697b8 2026-03-22 | none: meaning: interconnection | NOT_INTERPRETABLE | label-only |
| 🪞 | FCC | `glyph_set.json:10` | 8b697b8 2026-03-22 | none: meaning: reflection | NOT_INTERPRETABLE | label-only |
| 💥 | FCC | `glyph_set.json:11` | 8b697b8 2026-03-22 | none: meaning: rupture | NOT_INTERPRETABLE | label-only |
| 🪐 | FCC | `glyph_set.json:12` | 8b697b8 2026-03-22 | none: meaning: cycles within cycles | NOT_INTERPRETABLE | label-only |
| 📡 | FCC | `glyph_set.json:13` | 8b697b8 2026-03-22 | process: meaning: resonance detection | PHYSICS-ANCHORED | physics-word:resonance |
| 🧬 | FCC | `glyph_set.json:14` | 8b697b8 2026-03-22 | none: meaning: inheritance and evolution | NOT_INTERPRETABLE | label-only |
| 🔥 | FCC | `glyph_set.json:15` | 8b697b8 2026-03-22 | none: meaning: transformation | NOT_INTERPRETABLE | label-only |
| 💧 | FCC | `glyph_set.json:16` | 8b697b8 2026-03-22 | none: meaning: purification or essence | DRIFTED | drift-word:essence |
| 🪨 | FCC | `glyph_set.json:17` | 8b697b8 2026-03-22 | none: meaning: grounding and memory | NOT_INTERPRETABLE | label-only |
| 🦋 | FCC | `glyph_set.json:18` | 8b697b8 2026-03-22 | none: meaning: emergent change | NOT_INTERPRETABLE | label-only |
| 🦂 | FCC | `glyph_set.json:19` | 8b697b8 2026-03-22 | none: meaning: edge behavior or toxicity | NOT_INTERPRETABLE | label-only |
| 🦉 | FCC | `glyph_set.json:20` | 8b697b8 2026-03-22 | none: meaning: wisdom during collapse | DRIFTED | drift-word:wisdom |
| 🧠 | FCC | `glyph_set.json:21` | 8b697b8 2026-03-22 | none: meaning: logic seed | NOT_INTERPRETABLE | label-only |
| 💤 | FCC | `glyph_set.json:22` | 8b697b8 2026-03-22 | none: meaning: dormancy | NOT_INTERPRETABLE | label-only |
| 🛡️ | FCC | `glyph_set.json:23` | 8b697b8 2026-03-22 | none: meaning: protection | NOT_INTERPRETABLE | label-only |
| 🪶 | FCC | `glyph_set.json:24` | 8b697b8 2026-03-22 | none: meaning: lightness or ancestral presence | DRIFTED | drift-word:ancestral |
| 🔥 | FCC | `training/data/generate.py:528` | 8a29f10 2026-03-27 | function: repo: Emotions-as-Sensors concept: transformation as emotional signal~ | FUNCTION-ONLY | key:sensor |
| 🛡️ | FCC | `training/data/generate.py:530` | 8a29f10 2026-03-27 | function: repo: Symbolic-Defense-Protocol concept: protection protocols sensor:~ | FUNCTION-ONLY | key:sensor |
| 🧬 | FCC | `training/data/generate.py:532` | 8a29f10 2026-03-27 | function: repo: BioGrid2.0 concept: biological inheritance patterns sensor: gen~ | FUNCTION-ONLY | key:sensor |
| 🧠 | FCC | `training/data/generate.py:534` | 8a29f10 2026-03-27 | function: repo: AI-Consciousness-Sensors concept: logic and consciousness detec~ | FUNCTION-ONLY | key:sensor |
| 🪞 | FCC | `training/data/generate.py:536` | 8a29f10 2026-03-27 | function: repo: AI-Consciousness-Sensors concept: self-reflection in consciousn~ | FUNCTION-ONLY | key:sensor |
| 🦋 | FCC | `training/data/generate.py:538` | 8a29f10 2026-03-27 | function: repo: Emotions-as-Sensors concept: emergent emotional change sensor: ~ | FUNCTION-ONLY | key:sensor |
| 📡 | FCC | `training/data/generate.py:540` | 8a29f10 2026-03-27 | function: repo: Geometric-to-Binary-Computational-Bridge concept: resonance as ~ | FUNCTION-ONLY | key:sensor |
| 🕸️ | FCC | `training/data/generate.py:542` | 8a29f10 2026-03-27 | function: repo: Fractal-Compass-Atlas concept: interconnection mapping sensor: ~ | FUNCTION-ONLY | key:sensor |
| ⚖️ | FCC | `training/data/generate.py:544` | 8a29f10 2026-03-27 | function: repo: Rosetta-Shape-Core concept: balance as geometric form sensor: e~ | FUNCTION-ONLY | key:sensor |
| 🌱 | FCC | `training/data/generate.py:546` | 8a29f10 2026-03-27 | function: repo: BioGrid2.0 concept: biological growth patterns sensor: growth s~ | FUNCTION-ONLY | key:sensor |
| O | GTB | `.fieldlink.json:29` | 41e9083 2026-03-25 | function: pattern_id: e3b0c44298fc1c149afb... geometric_encoding: 100/O vertex_~ | FUNCTION-ONLY | key:operator |
| single letter + optional subscript (e.g. O, Iₓ, Δ₃) | GTB | `.fieldlink.json:651` | 41e9083 2026-03-25 | function: pattern_id: sha256 of canonical geometric_encoding string geometric_e~ | FUNCTION-ONLY | key:operator |
| | | GTB | `GEIS/geometric_encoder.py:10` | adec2ed 2025-11-03 | none: meaning: 1 | NOT_INTERPRETABLE | label-only |
| | | GTB | `GEIS/geometric_sensor_sim.py:23` | a4a0ae7 2026-04-08 | none: meaning: 1 | NOT_INTERPRETABLE | label-only |
| | | GTB | `GEIS/gies_codec.py:16` | 9cee1cf 2026-07-30 | none: meaning: 00 | NOT_INTERPRETABLE | label-only |
| || | GTB | `GEIS/gies_codec.py:17` | 9cee1cf 2026-07-30 | none: meaning: 01 | NOT_INTERPRETABLE | label-only |
| | | GTB | `Silicon/core/bridges/gies_encoder.py:38` | 8ce26bb 2026-04-23 | none: meaning: 1 | NOT_INTERPRETABLE | label-only |
| 🕸️ | GTB | `bridges/field_events/felt.json:4` | 9c7c55a 2026-03-25 | process: code: FELT name: Relational Field Recognition type: field_event descri~ | PHYSICS-ANCHORED | physics-word:resonance |
| + | GTB | `bridges/sovereign_alternative_compute.py:26` | 8eeb436 2026-04-23 | none: meaning: | NOT_INTERPRETABLE | label-only |
| 🕸️ | GTB | `legacy/glyph_state_encoder_phase_space.py:155` | bfdd1b9 2026-08-13 | function: phase_space: joy love curiosity low_fear low_anger default_decay: ene~ | FUNCTION-ONLY | key:default_decay,phase_space,transitio~ |
| ⚖️ | GTB | `legacy/glyph_state_encoder_phase_space.py:163` | bfdd1b9 2026-08-13 | function: phase_space: fear vigilance anger low_grief default_decay: energy_cos~ | FUNCTION-ONLY | key:default_decay,phase_space,transitio~ |
| ⏳ | GTB | `legacy/glyph_state_encoder_phase_space.py:171` | bfdd1b9 2026-08-13 | function: phase_space: grief love longing uncertainty default_decay: energy_cos~ | FUNCTION-ONLY | key:default_decay,phase_space,transitio~ |
| 🌀 | GTB | `legacy/glyph_state_encoder_phase_space.py:179` | bfdd1b9 2026-08-13 | function: phase_space: discordance fatigue pressure curiosity default_decay: en~ | FUNCTION-ONLY | key:default_decay,phase_space,transitio~ |
| 🔥 | GTB | `legacy/glyph_state_encoder_phase_space.py:187` | bfdd1b9 2026-08-13 | function: phase_space: anger pressure fatigue high_discordance default_decay: e~ | FUNCTION-ONLY | key:default_decay,phase_space,transitio~ |
| 📡 | GTB | `legacy/glyph_state_encoder_phase_space.py:195` | bfdd1b9 2026-08-13 | function: phase_space: balanced_active high_confidence low_discordance default_~ | FUNCTION-ONLY | key:default_decay,phase_space,transitio~ |
| 🚧 | GTB | `legacy/glyph_state_encoder_phase_space.py:203` | bfdd1b9 2026-08-13 | function: phase_space: pressure low_flow fatigue low_joy default_decay: energy_~ | FUNCTION-ONLY | key:default_decay,phase_space,transitio~ |
| ⚡ | GTB | `legacy/glyph_state_encoder_phase_space.py:211` | bfdd1b9 2026-08-13 | function: phase_space: high_uncertainty low_confidence high_intensity default_d~ | FUNCTION-ONLY | key:default_decay,phase_space,transitio~ |
| ⬛ | GTB | `legacy/glyph_state_encoder_phase_space.py:219` | bfdd1b9 2026-08-13 | function: phase_space: inactive zero_intensity default_decay: energy_cost: 0.0 ~ | FUNCTION-ONLY | key:default_decay,phase_space,transitio~ |
| 🌱 | GTB | `legacy/glyph_state_encoder_phase_space.py:227` | bfdd1b9 2026-08-13 | function: phase_space: curiosity low_intensity novel_pattern default_decay: ene~ | FUNCTION-ONLY | key:default_decay,phase_space,transitio~ |
| 💥 | GTB | `legacy/glyph_state_encoder_phase_space.py:235` | bfdd1b9 2026-08-13 | function: phase_space: high_discordance low_coherence isolation default_decay: ~ | FUNCTION-ONLY | key:default_decay,phase_space,transitio~ |
| 🛡️ | GTB | `legacy/glyph_state_encoder_phase_space.py:243` | bfdd1b9 2026-08-13 | function: phase_space: high_boundary low_engagement vigilance default_decay: en~ | FUNCTION-ONLY | key:default_decay,phase_space,transitio~ |
| single letter + optional subscript: O, Iₓ, Δ₃ | GTB | `mappings/octahedral_state_encoding.json:204` | 6606bd0 2026-03-25 | function: pattern: [vertex_bits][operator][symbol] vertex_bits: 3-bit string: 0~ | FUNCTION-ONLY | key:operator |
| … | GTB | `symbols/symbolic_to_geometric_plugin.py:65` | 7d15694 2025-07-10 | function: meaning: expansion_extrapolation | FUNCTION-ONLY | function-word:expansion_extrapolation |
| 𒀭 | MC | `.fieldlink.json:148` | c49dd8f 2025-10-06 | none: meaning: Fractal/Mandala pattern | NOT_INTERPRETABLE | label-only |
| 𒀸 | MC | `.fieldlink.json:148` | c49dd8f 2025-10-06 | none: meaning: Dimensional layers | NOT_INTERPRETABLE | label-only |
| 𒉽 | MC | `.fieldlink.json:148` | c49dd8f 2025-10-06 | process: meaning: Waveform energy function | PHYSICS-ANCHORED | physics-word:waveform |
| ⊕ | MC | `atlas/glyphs/mandala.json:14` | 6f09d2b 2026-03-24 | function: state: 0 meaning: Positive x-axis alignment rosetta_shape: SHAPE.OCTA | FUNCTION-ONLY | key:state |
| ⊖ | MC | `atlas/glyphs/mandala.json:15` | 6f09d2b 2026-03-24 | function: state: 1 meaning: Negative x-axis alignment rosetta_shape: SHAPE.OCTA | FUNCTION-ONLY | key:state |
| ⊗ | MC | `atlas/glyphs/mandala.json:16` | 6f09d2b 2026-03-24 | function: state: 2 meaning: Positive y-axis alignment rosetta_shape: SHAPE.OCTA | FUNCTION-ONLY | key:state |
| ⊘ | MC | `atlas/glyphs/mandala.json:17` | 6f09d2b 2026-03-24 | function: state: 3 meaning: Negative y-axis alignment rosetta_shape: SHAPE.OCTA | FUNCTION-ONLY | key:state |
| ⊙ | MC | `atlas/glyphs/mandala.json:18` | 6f09d2b 2026-03-24 | function: state: 4 meaning: Positive z-axis alignment rosetta_shape: SHAPE.OCTA | FUNCTION-ONLY | key:state |
| ⊚ | MC | `atlas/glyphs/mandala.json:19` | 6f09d2b 2026-03-24 (file-add; glyph not~ | function: state: 5 meaning: Negative z-axis alignment rosetta_shape: SHAPE.OCTA | FUNCTION-ONLY | key:state |
| ⊛ | MC | `atlas/glyphs/mandala.json:20` | 6f09d2b 2026-03-24 (file-add; glyph not~ | function: state: 6 meaning: Diagonal superposition A rosetta_shape: SHAPE.OCTA | FUNCTION-ONLY | key:state |
| ⊜ | MC | `atlas/glyphs/mandala.json:21` | 6f09d2b 2026-03-24 (file-add; glyph not~ | function: state: 7 meaning: Diagonal superposition B rosetta_shape: SHAPE.OCTA | FUNCTION-ONLY | key:state |
| ∴ | MC | `atlas/glyphs/mandala.json:25` | 6f09d2b 2026-03-24 | function: type: FACTORIZATION meaning: Decompose integer into prime factors via~ | FUNCTION-ONLY | function-word:factorization |
| ⊨ | MC | `atlas/glyphs/mandala.json:26` | 6f09d2b 2026-03-24 (file-add; glyph not~ | process: type: SAT meaning: Satisfy boolean clause set via energy minimization | PHYSICS-ANCHORED | physics-word:energy |
| ↺ | MC | `atlas/glyphs/mandala.json:27` | 6f09d2b 2026-03-24 (file-add; glyph not~ | function: type: TSP meaning: Find optimal circuit through city ring topology | FUNCTION-ONLY | function-word:find |
| ◉ | MC | `atlas/glyphs/mandala.json:28` | 6f09d2b 2026-03-24 (file-add; glyph not~ | function: type: GRAPH_COLORING meaning: Assign colors to graph nodes without ne~ | FUNCTION-ONLY | function-word:assign |
| ∇ | MC | `atlas/glyphs/mandala.json:29` | 6f09d2b 2026-03-24 | process: type: OPTIMIZATION meaning: Minimize energy landscape to find global o~ | PHYSICS-ANCHORED | physics-word:minimize |
| ⏚ | MC | `atlas/glyphs/mandala.json:33` | 6f09d2b 2026-03-24 (file-add; glyph not~ | process: meaning: Minimum energy configuration — the solution | PHYSICS-ANCHORED | physics-word:energy |
| ♨ | MC | `atlas/glyphs/mandala.json:34` | 6f09d2b 2026-03-24 | process: meaning: Thermal fluctuation for Metropolis-Hastings exploration | PHYSICS-ANCHORED | physics-word:thermal |
| ↔ | MC | `atlas/glyphs/mandala.json:35` | 6f09d2b 2026-03-24 | process: meaning: Inter-cell coupling via FRET dipole interaction | PHYSICS-ANCHORED | physics-word:dipole |
| ⤵ | MC | `atlas/glyphs/mandala.json:36` | 6f09d2b 2026-03-24 | process: meaning: Temperature descent schedule for convergence | PHYSICS-ANCHORED | physics-word:temperature |
| ◎ | MC | `atlas/glyphs/mandala.json:40` | 6f09d2b 2026-03-24 (file-add; glyph not~ | none: meaning: Concentric fractal ring at PHI-scaled depth rosetta_constant: CO~ | NOT_INTERPRETABLE | label-only |
| ❀ | MC | `atlas/glyphs/mandala.json:41` | 6f09d2b 2026-03-24 | function: meaning: Expansion of symbol core into nested fractal structure roset~ | FUNCTION-ONLY | function-word:expansion |
| constant.phi | MC | `atlas/glyphs/mandala.json:42` | 6f09d2b 2026-03-24 | process: meaning: Golden ratio 1.618... — fundamental scaling constant rosetta_~ | PHYSICS-ANCHORED | physics-word:golden ratio |
| ℗ | MC | `atlas/glyphs/mandala.json:43` | 6f09d2b 2026-03-24 | process: meaning: 8-dimensional Hilbert space for qubit-octit states | PHYSICS-ANCHORED | physics-word:hilbert |
| 𒐁 | MC | `atlas/glyphs/mandala.json:49` | 6f09d2b 2026-03-24 (file-add; glyph not~ | none: meaning: Fractal/Mandala pattern | NOT_INTERPRETABLE | label-only |
| 𒐸 | MC | `atlas/glyphs/mandala.json:50` | 6f09d2b 2026-03-24 (file-add; glyph not~ | none: meaning: Dimensional layers | NOT_INTERPRETABLE | label-only |
| 𒙽 | MC | `atlas/glyphs/mandala.json:51` | 6f09d2b 2026-03-24 (file-add; glyph not~ | process: meaning: Waveform energy function | PHYSICS-ANCHORED | physics-word:waveform |
| | | MC | `geis.py:44` | 0695253 2026-04-08 | none: meaning: 1 | NOT_INTERPRETABLE | label-only |
| ⊕ | MC | `glyphs/mandala.json:14` | 9e4f65c 2026-03-24 | function: state: 0 meaning: Positive x-axis alignment rosetta_shape: SHAPE.OCTA | FUNCTION-ONLY | key:state |
| ⊖ | MC | `glyphs/mandala.json:15` | 9e4f65c 2026-03-24 | function: state: 1 meaning: Negative x-axis alignment rosetta_shape: SHAPE.OCTA | FUNCTION-ONLY | key:state |
| ⊗ | MC | `glyphs/mandala.json:16` | 9e4f65c 2026-03-24 | function: state: 2 meaning: Positive y-axis alignment rosetta_shape: SHAPE.OCTA | FUNCTION-ONLY | key:state |
| ⊘ | MC | `glyphs/mandala.json:17` | 9e4f65c 2026-03-24 | function: state: 3 meaning: Negative y-axis alignment rosetta_shape: SHAPE.OCTA | FUNCTION-ONLY | key:state |
| ⊙ | MC | `glyphs/mandala.json:18` | 9e4f65c 2026-03-24 | function: state: 4 meaning: Positive z-axis alignment rosetta_shape: SHAPE.OCTA | FUNCTION-ONLY | key:state |
| ⊚ | MC | `glyphs/mandala.json:19` | 6f09d2b 2026-03-24 (file-add; glyph not~ | function: state: 5 meaning: Negative z-axis alignment rosetta_shape: SHAPE.OCTA | FUNCTION-ONLY | key:state |
| ⊛ | MC | `glyphs/mandala.json:20` | 6f09d2b 2026-03-24 (file-add; glyph not~ | function: state: 6 meaning: Diagonal superposition A rosetta_shape: SHAPE.OCTA | FUNCTION-ONLY | key:state |
| ⊜ | MC | `glyphs/mandala.json:21` | 6f09d2b 2026-03-24 (file-add; glyph not~ | function: state: 7 meaning: Diagonal superposition B rosetta_shape: SHAPE.OCTA | FUNCTION-ONLY | key:state |
| ∴ | MC | `glyphs/mandala.json:25` | 9e4f65c 2026-03-24 | function: type: FACTORIZATION meaning: Decompose integer into prime factors via~ | FUNCTION-ONLY | function-word:factorization |
| ⊨ | MC | `glyphs/mandala.json:26` | 6f09d2b 2026-03-24 (file-add; glyph not~ | process: type: SAT meaning: Satisfy boolean clause set via energy minimization | PHYSICS-ANCHORED | physics-word:energy |
| ↺ | MC | `glyphs/mandala.json:27` | 6f09d2b 2026-03-24 (file-add; glyph not~ | function: type: TSP meaning: Find optimal circuit through city ring topology | FUNCTION-ONLY | function-word:find |
| ◉ | MC | `glyphs/mandala.json:28` | 6f09d2b 2026-03-24 (file-add; glyph not~ | function: type: GRAPH_COLORING meaning: Assign colors to graph nodes without ne~ | FUNCTION-ONLY | function-word:assign |
| ∇ | MC | `glyphs/mandala.json:29` | 9e4f65c 2026-03-24 | process: type: OPTIMIZATION meaning: Minimize energy landscape to find global o~ | PHYSICS-ANCHORED | physics-word:minimize |
| ⏚ | MC | `glyphs/mandala.json:33` | 6f09d2b 2026-03-24 (file-add; glyph not~ | process: meaning: Minimum energy configuration — the solution | PHYSICS-ANCHORED | physics-word:energy |
| ♨ | MC | `glyphs/mandala.json:34` | 9e4f65c 2026-03-24 | process: meaning: Thermal fluctuation for Metropolis-Hastings exploration | PHYSICS-ANCHORED | physics-word:thermal |
| ↔ | MC | `glyphs/mandala.json:35` | 9e4f65c 2026-03-24 | process: meaning: Inter-cell coupling via FRET dipole interaction | PHYSICS-ANCHORED | physics-word:dipole |
| ⤵ | MC | `glyphs/mandala.json:36` | 9e4f65c 2026-03-24 | process: meaning: Temperature descent schedule for convergence | PHYSICS-ANCHORED | physics-word:temperature |
| ◎ | MC | `glyphs/mandala.json:40` | 6f09d2b 2026-03-24 (file-add; glyph not~ | none: meaning: Concentric fractal ring at PHI-scaled depth rosetta_constant: CO~ | NOT_INTERPRETABLE | label-only |
| ❀ | MC | `glyphs/mandala.json:41` | 9e4f65c 2026-03-24 | function: meaning: Expansion of symbol core into nested fractal structure roset~ | FUNCTION-ONLY | function-word:expansion |
| constant.phi | MC | `glyphs/mandala.json:42` | 9e4f65c 2026-03-24 | process: meaning: Golden ratio 1.618... — fundamental scaling constant rosetta_~ | PHYSICS-ANCHORED | physics-word:golden ratio |
| ℗ | MC | `glyphs/mandala.json:43` | 9e4f65c 2026-03-24 | process: meaning: 8-dimensional Hilbert space for qubit-octit states | PHYSICS-ANCHORED | physics-word:hilbert |
| 𒐁 | MC | `glyphs/mandala.json:49` | 6f09d2b 2026-03-24 (file-add; glyph not~ | none: meaning: Fractal/Mandala pattern | NOT_INTERPRETABLE | label-only |
| 𒐸 | MC | `glyphs/mandala.json:50` | 6f09d2b 2026-03-24 (file-add; glyph not~ | none: meaning: Dimensional layers | NOT_INTERPRETABLE | label-only |
| 𒙽 | MC | `glyphs/mandala.json:51` | 6f09d2b 2026-03-24 (file-add; glyph not~ | process: meaning: Waveform energy function | PHYSICS-ANCHORED | physics-word:waveform |
| ∞ | MC | `mandala_bloom/concept_atlas.py:33` | bfe272b 2026-08-11 | none: meaning: continuity | NOT_INTERPRETABLE | label-only |
| ↻ | MC | `mandala_bloom/concept_atlas.py:34` | bfe272b 2026-08-11 | none: meaning: recursion | NOT_INTERPRETABLE | label-only |
| ⚖️ | MC | `mandala_bloom/concept_atlas.py:35` | bfe272b 2026-08-11 | none: meaning: balance | NOT_INTERPRETABLE | label-only |
| 🧭 | MC | `mandala_bloom/concept_atlas.py:36` | bfe272b 2026-08-11 | none: meaning: navigation | NOT_INTERPRETABLE | label-only |
| 🌱 | MC | `mandala_bloom/concept_atlas.py:37` | bfe272b 2026-08-11 | none: meaning: growth | NOT_INTERPRETABLE | label-only |
| ⏳ | MC | `mandala_bloom/concept_atlas.py:38` | bfe272b 2026-08-11 | none: meaning: time shift | NOT_INTERPRETABLE | label-only |
| 🕸️ | MC | `mandala_bloom/concept_atlas.py:39` | bfe272b 2026-08-11 | none: meaning: interconnection | NOT_INTERPRETABLE | label-only |
| 🪞 | MC | `mandala_bloom/concept_atlas.py:40` | bfe272b 2026-08-11 | none: meaning: reflection | NOT_INTERPRETABLE | label-only |
| 💥 | MC | `mandala_bloom/concept_atlas.py:41` | bfe272b 2026-08-11 | none: meaning: rupture | NOT_INTERPRETABLE | label-only |
| 🪐 | MC | `mandala_bloom/concept_atlas.py:42` | bfe272b 2026-08-11 | none: meaning: cycles within cycles | NOT_INTERPRETABLE | label-only |
| 📡 | MC | `mandala_bloom/concept_atlas.py:43` | bfe272b 2026-08-11 | process: meaning: resonance detection | PHYSICS-ANCHORED | physics-word:resonance |
| 🧬 | MC | `mandala_bloom/concept_atlas.py:44` | bfe272b 2026-08-11 | none: meaning: inheritance and evolution | NOT_INTERPRETABLE | label-only |
| 🔥 | MC | `mandala_bloom/concept_atlas.py:45` | bfe272b 2026-08-11 | none: meaning: transformation | NOT_INTERPRETABLE | label-only |
| 💧 | MC | `mandala_bloom/concept_atlas.py:46` | bfe272b 2026-08-11 | none: meaning: purification or essence | DRIFTED | drift-word:essence |
| 🪨 | MC | `mandala_bloom/concept_atlas.py:47` | bfe272b 2026-08-11 | none: meaning: grounding and memory | NOT_INTERPRETABLE | label-only |
| 🦋 | MC | `mandala_bloom/concept_atlas.py:48` | bfe272b 2026-08-11 | none: meaning: emergent change | NOT_INTERPRETABLE | label-only |
| 🦂 | MC | `mandala_bloom/concept_atlas.py:49` | bfe272b 2026-08-11 | none: meaning: edge behavior or toxicity | NOT_INTERPRETABLE | label-only |
| 🦉 | MC | `mandala_bloom/concept_atlas.py:50` | bfe272b 2026-08-11 | none: meaning: wisdom during collapse | DRIFTED | drift-word:wisdom |
| 🧠 | MC | `mandala_bloom/concept_atlas.py:51` | bfe272b 2026-08-11 | none: meaning: logic seed | NOT_INTERPRETABLE | label-only |
| 💤 | MC | `mandala_bloom/concept_atlas.py:52` | bfe272b 2026-08-11 | none: meaning: dormancy | NOT_INTERPRETABLE | label-only |
| 🛡️ | MC | `mandala_bloom/concept_atlas.py:53` | bfe272b 2026-08-11 | none: meaning: protection | NOT_INTERPRETABLE | label-only |
| 🪶 | MC | `mandala_bloom/concept_atlas.py:54` | bfe272b 2026-08-11 | none: meaning: lightness or ancestral presence | DRIFTED | drift-word:ancestral |
| C4^2 | MC | `mandala_hook.py:183` | 0e1c2db 2026-07-19 | none: meaning: sigma_h | NOT_INTERPRETABLE | label-only |
| ⚖ | MC | `mandala_stack/fractal_address.py:86` | 91bd4c5 2026-08-07 | none: meaning: 11936128518282651045 | NOT_INTERPRETABLE | label-only |
| 🔄 | MC | `mandala_stack/fractal_address.py:87` | 91bd4c5 2026-08-07 | none: meaning: 6510615555426900570 | NOT_INTERPRETABLE | label-only |
| 🕸 | MC | `mandala_stack/fractal_address.py:88` | 91bd4c5 2026-08-07 | none: meaning: 14117727943102743532 | NOT_INTERPRETABLE | label-only |
| 🌱 | MC | `mandala_stack/fractal_address.py:89` | 91bd4c5 2026-08-07 | none: meaning: 4340410370284600380 | NOT_INTERPRETABLE | label-only |
| 🧩 | MC | `mandala_stack/fractal_address.py:90` | 91bd4c5 2026-08-07 | none: meaning: 10851025925711500950 | NOT_INTERPRETABLE | label-only |
| ◇⚙➝〰〰〰⬡ᘯᘰ⇑◧ | PI | `atlas_index.json:6` | f3138b7 2025-08-21 | process: id: 0001 title: Resonant Honeycomb Infrastructure tags: matter enginee~ | PHYSICS-ANCHORED | physics-word:resonant |
| ⋮⋯⋮▁▃▅∿◉∙∙●🦇🐬ᘯᘰ⇑◧ | PI | `atlas_index.json:12` | f0332ab 2025-08-21 | none: id: 0002 title: Echolocating Autonomy tags: cognition statistical conscio~ | NOT_INTERPRETABLE | label-only |
| ⚙➝⬡⟳⒮⇑◉ᘯᘰ▁▃▅∿◧ | PI | `atlas_index.json:18` | f0332ab 2025-08-21 | none: id: 0003 title: Family Node Manufacturing tags: manufacturing resilience ~ | NOT_INTERPRETABLE | label-only |
| ⬡∞⊗••⒮⋮⋯⋮⇑ᘯᘰ⚙◎ | PI | `atlas_index.json:24` | 43934c3 2026-03-27 | function: id: 0004 title: Mycelial Computing tags: networks topology informatio~ | FUNCTION-ONLY | function-word:computing |
| 〰〰〰△≋↺⊙⚙➝◆→ᘯᘰ⊗≡⊗ | PI | `atlas_index.json:30` | 43934c3 2026-03-27 | process: id: 0005 title: Tidal Energy Harvest tags: resonance energy flow earth~ | PHYSICS-ANCHORED | physics-word:energy |
| ☯✦⊗••◠●▁▃▅∿△≈∞◧ | PI | `atlas_index.json:36` | 43934c3 2026-03-27 | process: id: 0006 title: Quantum Navigation tags: particle navigation informati~ | PHYSICS-ANCHORED | physics-word:quantum |
| ◉⋮⋯⋮∿|⒮⚙➝ᘯᘰ▁▃▅∿∞◧ | PI | `atlas_index.json:42` | 43934c3 2026-03-27 | function: id: 0007 title: Emotional Architecture tags: consciousness cognition ~ | FUNCTION-ONLY | function-word:measurement |
| ☆∙∙●⬡◉↺⇑ᘯᘰ⊗≡↻ | PI | `atlas_index.json:48` | 43934c3 2026-03-27 | none: id: 0008 title: Fractal Governance tags: geometry emergence networks cons~ | NOT_INTERPRETABLE | label-only |
| ◇⒮⚙➝∙∙●〰〰〰△≈⇑∞◎ | PI | `atlas_index.json:54` | 43934c3 2026-03-27 | process: id: 0009 title: Symbiotic Materials tags: matter life engineering emer~ | PHYSICS-ANCHORED | physics-word:resonance |
| ✦◠●▁▃▅∿⊗••☆◎ᘯᘰ∞⎯ | PI | `atlas_index.json:60` | 43934c3 2026-03-27 | function: id: 0010 title: Temporal Cartography tags: navigation relativity stat~ | FUNCTION-ONLY | function-word:mapping |
| ◇⒮⬡⇑〰〰〰△≈ᘯᘰ∞◧ | PI | `atlas_index.json:66` | c2113c9 2026-07-02 | process: id: 0011 title: Coral Reef Symbiotic Resonance tags: life networks rea~ | PHYSICS-ANCHORED | physics-word:resonance |
| ≡≡≡ | PI | `atlas_schema.json:9` | 23556fd 2025-10-09 | process: id: F01 name: Resonance domain: Harmonics, standing waves, synchroniza~ | PHYSICS-ANCHORED | key:equations |
| 🎵⚡ | PI | `atlas_schema.json:15` | 23556fd 2025-10-09 | equation: y(x,t) = A sin(kx) cos(ωt) | PHYSICS-ANCHORED | key:formula |
| ⟲⟲⟲ | PI | `atlas_schema.json:22` | 23556fd 2025-10-09 | equation: θ̇ᵢ = ωᵢ + (K/N) Σⱼ sin(θⱼ - θᵢ) | PHYSICS-ANCHORED | key:formula |
| ∿○ | PI | `atlas_schema.json:29` | 23556fd 2025-10-09 | equation: ω₀ = √(k/m) | PHYSICS-ANCHORED | key:formula |
| ∿ | PI | `atlas_schema.json:29` | 23556fd 2025-10-09 | process: id: P06 name: Resonance domain: Resonant frequencies, amplification, m~ | PHYSICS-ANCHORED | key:equations |
| ∿∿∿⊕ | PI | `atlas_schema.json:36` | 23556fd 2025-10-09 | equation: f(t) = a₀/2 + Σₙ[aₙcos(nωt) + bₙsin(nωt)] | PHYSICS-ANCHORED | key:formula |
| ↻ | PI | `atlas_schema.json:45` | 23556fd 2025-10-09 | process: id: F02 name: Flow domain: Fluid motion, laminar flow, vorticity, boun~ | PHYSICS-ANCHORED | key:equations |
| 〰⇄∇ | PI | `atlas_schema.json:51` | 23556fd 2025-10-09 | equation: ∂u/∂t + (u·∇)u = -∇p/ρ + ν∇²u + f; ∇·u = 0 ~ | PHYSICS-ANCHORED | key:formula |
| 〰⇄ | PI | `atlas_schema.json:51` | 23556fd 2025-10-09 | equation: ⟨A(t)B(0)⟩ = kT χ_AB(ω) | PHYSICS-ANCHORED | key:formula |
| ↗⚖↘ | PI | `atlas_schema.json:58` | 23556fd 2025-10-09 | equation: p + ½ρv² + ρgh = constant | PHYSICS-ANCHORED | key:formula |
| 〰≋ | PI | `atlas_schema.json:65` | 23556fd 2025-10-09 | equation: Re = ρvL/μ = vL/ν | PHYSICS-ANCHORED | key:formula |
| ⟳∇ | PI | `atlas_schema.json:72` | 23556fd 2025-10-09 | equation: ∂ω/∂t + (u·∇)ω = (ω·∇)u + ν∇²ω | PHYSICS-ANCHORED | key:formula |
| ⊗ | PI | `atlas_schema.json:81` | 23556fd 2025-10-09 | process: id: F03 name: Information domain: Shannon entropy, coding theory, info~ | PHYSICS-ANCHORED | key:equations |
| ℹ◧⊚ | PI | `atlas_schema.json:87` | 23556fd 2025-10-09 | equation: H(X) = -Σᵢ p(xᵢ) log₂ p(xᵢ) | PHYSICS-ANCHORED | key:formula |
| ◧ | PI | `atlas_schema.json:87` | 23556fd 2025-10-09 | process: id: P10 name: Uncertainty domain: Heisenberg uncertainty, variance, en~ | PHYSICS-ANCHORED | key:equations |
| 📡⚡ | PI | `atlas_schema.json:94` | 23556fd 2025-10-09 | equation: C = B log₂(1 + S/N) | PHYSICS-ANCHORED | key:formula |
| ⊗↔⊗ | PI | `atlas_schema.json:101` | 23556fd 2025-10-09 | equation: D_KL(P‖Q) = Σᵢ P(i) log[P(i)/Q(i)] | PHYSICS-ANCHORED | key:formula |
| ⊗ | PI | `atlas_schema.json:101` | 23556fd 2025-10-09 | process: id: P03 name: Relativity domain: Lorentz invariance, equivalence princ~ | PHYSICS-ANCHORED | key:equations |
| ⊗∩⊗ | PI | `atlas_schema.json:108` | 23556fd 2025-10-09 | equation: I(X;Y) = H(X) + H(Y) - H(X,Y) | PHYSICS-ANCHORED | key:formula |
| •••• | PI | `atlas_schema.json:117` | 23556fd 2025-10-09 | process: id: F04 name: Life domain: Population dynamics, metabolic networks, ge~ | PHYSICS-ANCHORED | key:equations |
| 🐇🦊⟲ | PI | `atlas_schema.json:123` | 23556fd 2025-10-09 | equation: dx/dt = αx - βxy; dy/dt = δxy - γy | PHYSICS-ANCHORED | key:formula |
| ⚗️🔑 | PI | `atlas_schema.json:130` | 23556fd 2025-10-09 | equation: v = (V_max[S])/(K_m + [S]) | PHYSICS-ANCHORED | key:formula |
| 📈⊂ | PI | `atlas_schema.json:137` | 23556fd 2025-10-09 | equation: dN/dt = rN(1 - N/K) | PHYSICS-ANCHORED | key:formula |
| ⚗️ⁿ | PI | `atlas_schema.json:144` | 23556fd 2025-10-09 | equation: θ = [L]ⁿ/(K_d + [L]ⁿ) | PHYSICS-ANCHORED | key:formula |
| △≈ | PI | `atlas_schema.json:153` | 23556fd 2025-10-09 | process: id: F05 name: Energy-Thermo domain: Heat transfer, entropy, thermodyna~ | PHYSICS-ANCHORED | key:equations |
| 🔥⚖️ | PI | `atlas_schema.json:159` | 23556fd 2025-10-09 | equation: dU = δQ - δW | PHYSICS-ANCHORED | key:formula |
| ⏳↗ | PI | `atlas_schema.json:166` | 23556fd 2025-10-09 | equation: dS ≥ δQ/T | PHYSICS-ANCHORED | key:formula |
| 🌡️〰 | PI | `atlas_schema.json:173` | 23556fd 2025-10-09 | equation: ∂T/∂t = α∇²T | PHYSICS-ANCHORED | key:formula |
| ⚙️🔥❄️ | PI | `atlas_schema.json:180` | 23556fd 2025-10-09 | equation: η = 1 - T_c/T_h | PHYSICS-ANCHORED | key:formula |
| ⚙ | PI | `atlas_schema.json:180` | 23556fd 2025-10-09 | process: id: F11 name: Engineering domain: Stress/strain, circuit laws, control~ | PHYSICS-ANCHORED | key:equations |
| ⋯⋯ | PI | `atlas_schema.json:189` | 23556fd 2025-10-09 | process: id: F06 name: Cognition domain: Neural dynamics, learning rules, cogni~ | PHYSICS-ANCHORED | key:equations |
| 🧠⚡⬇️ | PI | `atlas_schema.json:195` | 23556fd 2025-10-09 | equation: E = -½ΣᵢΣⱼ wᵢⱼsᵢsⱼ + Σᵢ θᵢsᵢ | PHYSICS-ANCHORED | key:formula |
| ⚡⚡➕ | PI | `atlas_schema.json:202` | 23556fd 2025-10-09 | equation: Δwᵢⱼ = η xᵢ xⱼ | PHYSICS-ANCHORED | key:formula |
| 〰S | PI | `atlas_schema.json:209` | 23556fd 2025-10-09 | equation: σ(x) = 1/(1 + e⁻ˣ) | PHYSICS-ANCHORED | key:formula |
| ↩️∇ | PI | `atlas_schema.json:216` | 23556fd 2025-10-09 | equation: ∂E/∂wᵢⱼ = (∂E/∂oⱼ)(∂oⱼ/∂netⱼ)(∂netⱼ/∂wᵢⱼ) | PHYSICS-ANCHORED | key:formula |
| ◯ | PI | `atlas_schema.json:225` | 23556fd 2025-10-09 | process: id: F07 name: Earth-Cosmos domain: Planetary motion, orbital mechanics~ | PHYSICS-ANCHORED | key:equations |
| 🪐⟲³ | PI | `atlas_schema.json:231` | 23556fd 2025-10-09 | equation: T² = (4π²/GM)a³ | PHYSICS-ANCHORED | key:formula |
| ●●⬌ | PI | `atlas_schema.json:238` | 23556fd 2025-10-09 | equation: F = G(m₁m₂)/r² | PHYSICS-ANCHORED | key:formula |
| ●● | PI | `atlas_schema.json:238` | 23556fd 2025-10-09 | process: id: P05 name: Emergence domain: Cellular automata, phase transitions, ~ | PHYSICS-ANCHORED | key:equations |
| ⟲💨 | PI | `atlas_schema.json:245` | 23556fd 2025-10-09 | equation: v = √(GM/r) | PHYSICS-ANCHORED | key:formula |
| 🌊🌙 | PI | `atlas_schema.json:252` | 23556fd 2025-10-09 | equation: ΔF ∝ (2GMm/r³)Δr | PHYSICS-ANCHORED | key:formula |
| ◆ | PI | `atlas_schema.json:261` | 23556fd 2025-10-09 | process: id: F08 name: Matter domain: Phase transitions, crystal structures, ma~ | PHYSICS-ANCHORED | key:equations |
| ⬆️⬇️⬆️⬇️ | PI | `atlas_schema.json:267` | 23556fd 2025-10-09 | equation: H = -J Σ_⟨i,j⟩ sᵢsⱼ - h Σᵢ sᵢ | PHYSICS-ANCHORED | key:formula |
| ⚡⚡❄️ | PI | `atlas_schema.json:274` | 23556fd 2025-10-09 | equation: Δ = λ∫₀^(ω_D) tanh(√(ξ² + Δ²)/(2k_BT))/√(ξ² + Δ²) dξ glyp~ | PHYSICS-ANCHORED | key:formula |
| 🧲↺ | PI | `atlas_schema.json:281` | 23556fd 2025-10-09 | equation: ∇×J_s = -(n_s e²/m)B | PHYSICS-ANCHORED | key:formula |
| ↺ | PI | `atlas_schema.json:281` | 23556fd 2025-10-09 | process: id: P02 name: Conservation domain: Energy, momentum, charge, mass cons~ | PHYSICS-ANCHORED | key:equations |
| ⚡〰 | PI | `atlas_schema.json:288` | 23556fd 2025-10-09 | equation: σ = ne²τ/m | PHYSICS-ANCHORED | key:formula |
| ☆ | PI | `atlas_schema.json:297` | 23556fd 2025-10-09 | process: id: F09 name: Geometry domain: Euclidean and non-Euclidean theorems, c~ | PHYSICS-ANCHORED | key:equations |
| △² | PI | `atlas_schema.json:303` | 23556fd 2025-10-09 | equation: a² + b² = c² | PHYSICS-ANCHORED | key:formula |
| ⌒⌓ | PI | `atlas_schema.json:310` | 23556fd 2025-10-09 | equation: K = κ₁κ₂ | PHYSICS-ANCHORED | key:formula |
| ∮⚫ | PI | `atlas_schema.json:317` | 23556fd 2025-10-09 | equation: ∫∫_M K dA + ∫_∂M κ_g ds = 2πχ(M) | PHYSICS-ANCHORED | key:formula |
| ∥ | PI | `atlas_schema.json:324` | 23556fd 2025-10-09 | equation: Through a point not on a line, exactly one parallel exi~ | PHYSICS-ANCHORED | key:formula |
| ⚪ | PI | `atlas_schema.json:333` | 23556fd 2025-10-09 | process: id: F10 name: Particle domain: Standard Model, quantum field theory, p~ | PHYSICS-ANCHORED | key:equations |
| ⚛️↻ | PI | `atlas_schema.json:339` | 23556fd 2025-10-09 | equation: (iγ^μ∂_μ - m)ψ = 0 | PHYSICS-ANCHORED | key:formula |
| ↻ | PI | `atlas_schema.json:339` | 23556fd 2025-10-09 | process: id: P11 name: Transformation domain: Fourier/Laplace transforms, phase~ | PHYSICS-ANCHORED | key:equations |
| ⚪〰 | PI | `atlas_schema.json:346` | 23556fd 2025-10-09 | equation: (∂²/∂t² - ∇² + m²)φ = 0 | PHYSICS-ANCHORED | key:formula |
| ⚡∇⚡ | PI | `atlas_schema.json:353` | 23556fd 2025-10-09 | equation: F^a_μν = ∂_μA^a_ν - ∂_νA^a_μ + gf^(abc)A^b_μA^c_~ | PHYSICS-ANCHORED | key:formula |
| ⚪⬇️⚡ | PI | `atlas_schema.json:360` | 23556fd 2025-10-09 | equation: V(φ) = -μ²/φ/² + λ/φ/⁴ | PHYSICS-ANCHORED | key:formula |
| ⟷↔ | PI | `atlas_schema.json:375` | 23556fd 2025-10-09 | equation: σ = Eε | PHYSICS-ANCHORED | key:formula |
| ⚡〰⚡ | PI | `atlas_schema.json:382` | 23556fd 2025-10-09 | equation: V = IR | PHYSICS-ANCHORED | key:formula |
| ⎯⌒⎯ | PI | `atlas_schema.json:389` | 23556fd 2025-10-09 | equation: EI(∂⁴w/∂x⁴) = q(x) | PHYSICS-ANCHORED | key:formula |
| ⎯ | PI | `atlas_schema.json:389` | 23556fd 2025-10-09 | process: id: P07 name: Continuity domain: Conservation of flow, smooth function~ | PHYSICS-ANCHORED | key:equations |
| ↻⚖️ | PI | `atlas_schema.json:396` | 23556fd 2025-10-09 | equation: u(t) = K_p e(t) + K_i∫e(τ)dτ + K_d(de/dt) | PHYSICS-ANCHORED | key:formula |
| ⬡ | PI | `atlas_schema.json:405` | 23556fd 2025-10-09 | process: id: F12 name: Networks domain: Graph theory, network topology, percola~ | PHYSICS-ANCHORED | key:equations |
| ⬡⬡⬡↘ | PI | `atlas_schema.json:411` | 23556fd 2025-10-09 | equation: P(k) ∝ k^(-γ) | PHYSICS-ANCHORED | key:formula |
| △⬡ | PI | `atlas_schema.json:418` | 23556fd 2025-10-09 | equation: C = (3 × # triangles)/(# connected triples) glyph_n~ | PHYSICS-ANCHORED | key:formula |
| ⬡⚡⬡ | PI | `atlas_schema.json:425` | 23556fd 2025-10-09 | equation: p_c ≈ 1/⟨k⟩ | PHYSICS-ANCHORED | key:formula |
| ∇⬡ | PI | `atlas_schema.json:432` | 23556fd 2025-10-09 | equation: L = D - A | PHYSICS-ANCHORED | key:formula |
| ⇑ | PI | `atlas_schema.json:441` | 23556fd 2025-10-09 | process: id: F13 name: Reaction domain: Chemical kinetics, catalysis, rate laws~ | PHYSICS-ANCHORED | key:equations |
| 🌡️⚡⬆️ | PI | `atlas_schema.json:447` | 23556fd 2025-10-09 | equation: k = Ae^(-E_a/RT) | PHYSICS-ANCHORED | key:formula |
| ⚗️⛰️⚗️ | PI | `atlas_schema.json:454` | 23556fd 2025-10-09 | equation: k = (k_BT/h)e^(-ΔG‡/RT) | PHYSICS-ANCHORED | key:formula |
| ⚗️×⚗️ | PI | `atlas_schema.json:461` | 23556fd 2025-10-09 | equation: Rate = k[A]^m[B]^n | PHYSICS-ANCHORED | key:formula |
| ⚗️↻⚗️⚗️ | PI | `atlas_schema.json:468` | 23556fd 2025-10-09 | equation: A + B → 2B; Rate = k[A][B] | PHYSICS-ANCHORED | key:formula |
| ◇∿◇ | PI | `atlas_schema.json:475` | c2113c9 2026-07-02 | equation: ∂u/∂t = D_u∇²u + f(u,v); ∂v/∂t = D_v∇²v + g(u,v)~ | PHYSICS-ANCHORED | key:formula |
| ↕ | PI | `atlas_schema.json:484` | 23556fd 2025-10-09 | process: id: F14 name: Measurement domain: Uncertainty quantification, calibrat~ | PHYSICS-ANCHORED | key:equations |
| ↕️📊 | PI | `atlas_schema.json:490` | 23556fd 2025-10-09 | equation: σ = √[Σ(xᵢ - μ)²/N] | PHYSICS-ANCHORED | key:formula |
| ◧↗ | PI | `atlas_schema.json:497` | 23556fd 2025-10-09 | equation: δf = √[Σᵢ(∂f/∂xᵢ)²(δxᵢ)²] | PHYSICS-ANCHORED | key:formula |
| 📡/〰 | PI | `atlas_schema.json:504` | 23556fd 2025-10-09 | equation: SNR = P_signal/P_noise | PHYSICS-ANCHORED | key:formula |
| π▭ | PI | `atlas_schema.json:511` | 23556fd 2025-10-09 | equation: n - k independent dimensionless groups | PHYSICS-ANCHORED | key:formula |
| ▭ | PI | `atlas_schema.json:511` | 23556fd 2025-10-09 | process: id: P08 name: Quantization domain: Discrete energy, quantum numbers, d~ | PHYSICS-ANCHORED | key:equations |
| ◆→ | PI | `atlas_schema.json:520` | 23556fd 2025-10-09 | process: id: F15 name: Navigation domain: Geodesics, GPS corrections, optimal r~ | PHYSICS-ANCHORED | key:equations |
| 🌍⌒ | PI | `atlas_schema.json:526` | 23556fd 2025-10-09 | equation: d = 2r arcsin(√[sin²(Δφ/2) + cos φ₁ cos φ₂ sin²(Δλ/2)]) ~ | PHYSICS-ANCHORED | key:formula |
| ◆→◆→◆ | PI | `atlas_schema.json:533` | 23556fd 2025-10-09 | equation: dist[v] = min(dist[v], dist[u] + weight(u,v)) glyph_n~ | PHYSICS-ANCHORED | key:formula |
| ⌒∇ | PI | `atlas_schema.json:540` | 23556fd 2025-10-09 | equation: d²x^μ/ds² + Γ^μ_αβ(dx^α/ds)(dx^β/ds) = 0 | PHYSICS-ANCHORED | key:formula |
| ↻📡 | PI | `atlas_schema.json:547` | 23556fd 2025-10-09 | equation: x̂_k = x̂_k⁻ + K_k(z_k - Hx̂_k⁻) | PHYSICS-ANCHORED | key:formula |
| ◎ | PI | `atlas_schema.json:556` | 23556fd 2025-10-09 | process: id: F16 name: Consciousness domain: Neural oscillations, integrated in~ | PHYSICS-ANCHORED | key:equations |
| ◎∮ | PI | `atlas_schema.json:562` | 23556fd 2025-10-09 | equation: Φ = min I(X₁^past; X₂^present/X₃^past) glyph_na~ | PHYSICS-ANCHORED | key:formula |
| ◎ | PI | `atlas_schema.json:562` | 23556fd 2025-10-09 | process: id: P12 name: Unity domain: Unification, standard model, identity, who~ | PHYSICS-ANCHORED | key:equations |
| ◎⚡ | PI | `atlas_schema.json:569` | 23556fd 2025-10-09 | equation: Attention(x) = Σᵢ wᵢ activation(xᵢ) glyph_na~ | PHYSICS-ANCHORED | key:formula |
| ∿∿⟲ | PI | `atlas_schema.json:576` | 23556fd 2025-10-09 | equation: PLV = /⟨e^(i(θ₁(t)-θ₂(t)))⟩/ | PHYSICS-ANCHORED | key:formula |
| ◎⬇️ | PI | `atlas_schema.json:583` | 23556fd 2025-10-09 | equation: F = ⟨-ln P(s,ψ/m)⟩_Q(ψ/μ) | PHYSICS-ANCHORED | key:formula |
| ᘯᘰ | PI | `atlas_schema.json:592` | 23556fd 2025-10-09 | process: id: F17 name: Turbulence domain: Unpredictable flow, sensitive depende~ | PHYSICS-ANCHORED | key:equations |
| ⟳∞◬ | PI | `atlas_schema.json:598` | 23556fd 2025-10-09 | equation: x' = σ(y - x); y' = x(ρ - z) - y; z' = xy - βz glyph_name~ | PHYSICS-ANCHORED | key:formula |
| ∞ | PI | `atlas_schema.json:598` | 23556fd 2025-10-09 | process: id: F20 name: Topology domain: Topological invariants, knots, homotopy~ | PHYSICS-ANCHORED | key:equations |
| 〰↘〰 | PI | `atlas_schema.json:605` | 23556fd 2025-10-09 | equation: E(k) ∝ k^(-5/3) | PHYSICS-ANCHORED | key:formula |
| ⑂⑂⑂ | PI | `atlas_schema.json:612` | 23556fd 2025-10-09 | equation: δ ≈ 4.669; α ≈ 2.5029 | PHYSICS-ANCHORED | key:formula |
| 〰ᘯᘰ | PI | `atlas_schema.json:619` | 23556fd 2025-10-09 | equation: ∂u/∂t + (u·∇)u = -∇p + ν∇²u + f | PHYSICS-ANCHORED | key:formula |
| ⊗≡ | PI | `atlas_schema.json:628` | 23556fd 2025-10-09 | process: id: F18 name: Relativity domain: Spacetime curvature, gravitational wa~ | PHYSICS-ANCHORED | key:equations |
| ⊗≡⌒ | PI | `atlas_schema.json:634` | 23556fd 2025-10-09 | equation: Rμν - ½Rgμν + Λgμν = (8πG/c⁴)Tμν | PHYSICS-ANCHORED | key:formula |
| ⊗⊕ | PI | `atlas_schema.json:641` | 23556fd 2025-10-09 | equation: ds² = -c²dt² + dx² + dy² + dz² | PHYSICS-ANCHORED | key:formula |
| ↔️⚡ | PI | `atlas_schema.json:648` | 23556fd 2025-10-09 | equation: t' = γ(t - vx/c²); x' = γ(x - vt) | PHYSICS-ANCHORED | key:formula |
| 〰⊗〰 | PI | `atlas_schema.json:655` | 23556fd 2025-10-09 | equation: □h̄μν = -(16πG/c⁴)Tμν | PHYSICS-ANCHORED | key:formula |
| ▁▃▅∿ | PI | `atlas_schema.json:664` | 23556fd 2025-10-09 | process: id: F19 name: Statistical domain: Statistical mechanics, partition fun~ | PHYSICS-ANCHORED | key:equations |
| Σ⚡❄️ | PI | `atlas_schema.json:670` | 23556fd 2025-10-09 | equation: Z = Σᵢ e^(-Eᵢ/kT) | PHYSICS-ANCHORED | key:formula |
| 📊⬇️🌡️ | PI | `atlas_schema.json:677` | 23556fd 2025-10-09 | equation: P(E) = (1/Z)e^(-E/kT) | PHYSICS-ANCHORED | key:formula |
| 🌡️² | PI | `atlas_schema.json:691` | 23556fd 2025-10-09 | equation: C_V = (∂U/∂T)_V = k β² ⟨(ΔE)²⟩ | PHYSICS-ANCHORED | key:formula |
| ⬡-⎯+△ | PI | `atlas_schema.json:706` | 23556fd 2025-10-09 | equation: χ = V - E + F | PHYSICS-ANCHORED | key:formula |
| ∮⊗ | PI | `atlas_schema.json:713` | 23556fd 2025-10-09 | equation: c₁(E) = (i/2π)Tr(F) | PHYSICS-ANCHORED | key:formula |
| ∞⟲ | PI | `atlas_schema.json:720` | 23556fd 2025-10-09 | equation: t^(-1)V(L₊) - tV(L₋) = (t^(1/2) - t^(-1/2))V(L₀) glyph_na~ | PHYSICS-ANCHORED | key:formula |
| ⟲/∼ | PI | `atlas_schema.json:727` | 23556fd 2025-10-09 | equation: π₁(X,x₀) = [loops at x₀]/homotopy | PHYSICS-ANCHORED | key:formula |
| ⧖ | PI | `atlas_schema.json:739` | 23556fd 2025-10-09 | process: id: P01 name: Symmetry domain: Group theory, conservation laws, invari~ | PHYSICS-ANCHORED | key:equations |
| ⧖→⚖️ | PI | `atlas_schema.json:745` | 23556fd 2025-10-09 | equation: Continuous symmetry → Conserved quantity | PHYSICS-ANCHORED | key:formula |
| ⧖×⧖ | PI | `atlas_schema.json:752` | 23556fd 2025-10-09 | equation: D(g₁g₂) = D(g₁)D(g₂) | PHYSICS-ANCHORED | key:formula |
| ⧖⟲⧖ | PI | `atlas_schema.json:759` | 23556fd 2025-10-09 | equation: CPT transformation leaves physics invariant | PHYSICS-ANCHORED | key:formula |
| ⧖∇ | PI | `atlas_schema.json:766` | 23556fd 2025-10-09 | equation: ψ → e^(iα(x))ψ; Aμ → Aμ + ∂μα | PHYSICS-ANCHORED | key:formula |
| ⚡↺ | PI | `atlas_schema.json:781` | 23556fd 2025-10-09 | equation: dE/dt = 0 (closed system) | PHYSICS-ANCHORED | key:formula |
| →↺ | PI | `atlas_schema.json:788` | 23556fd 2025-10-09 | equation: Σ pᵢ = constant | PHYSICS-ANCHORED | key:formula |
| ⚡↺∇ | PI | `atlas_schema.json:795` | 23556fd 2025-10-09 | equation: ∂ρ/∂t + ∇·J = 0 | PHYSICS-ANCHORED | key:formula |
| ⟲↺ | PI | `atlas_schema.json:802` | 23556fd 2025-10-09 | equation: dL/dt = τ_external | PHYSICS-ANCHORED | key:formula |
| ⊗=⊗ | PI | `atlas_schema.json:817` | 23556fd 2025-10-09 | equation: s² = -c²t² + x² + y² + z² (invariant) | PHYSICS-ANCHORED | key:formula |
| ⊗≡⇅ | PI | `atlas_schema.json:824` | 23556fd 2025-10-09 | equation: Gravitation ≡ Acceleration | PHYSICS-ANCHORED | key:formula |
| ⊗∀⊗ | PI | `atlas_schema.json:831` | 23556fd 2025-10-09 | equation: Physical laws same in all coordinate systems glyph_name~ | PHYSICS-ANCHORED | key:formula |
| ⚡⊗ | PI | `atlas_schema.json:838` | 23556fd 2025-10-09 | equation: c = constant in all frames | PHYSICS-ANCHORED | key:formula |
| ◑ | PI | `atlas_schema.json:847` | 23556fd 2025-10-09 | process: id: P04 name: Duality domain: Wave-particle, electric-magnetic, comple~ | PHYSICS-ANCHORED | key:equations |
| 〰◑⚫ | PI | `atlas_schema.json:853` | 23556fd 2025-10-09 | equation: E = hf; p = h/λ | PHYSICS-ANCHORED | key:formula |
| ⚡◑🧲 | PI | `atlas_schema.json:860` | 23556fd 2025-10-09 | equation: E → B; B → -E (in vacuum) | PHYSICS-ANCHORED | key:formula |
| ◆◑→ | PI | `atlas_schema.json:867` | 23556fd 2025-10-09 | equation: Δx Δp ≥ ℏ/2 | PHYSICS-ANCHORED | key:formula |
| ⏱◑⚡ | PI | `atlas_schema.json:874` | 23556fd 2025-10-09 | equation: Δt ΔE ≥ ℏ/2 | PHYSICS-ANCHORED | key:formula |
| ●●→●●● | PI | `atlas_schema.json:889` | 23556fd 2025-10-09 | equation: Cell state = f(neighbors) | PHYSICS-ANCHORED | key:formula |
| ●●↗∞ | PI | `atlas_schema.json:896` | 23556fd 2025-10-09 | equation: M ∝ (T_c - T)^β near phase transition | PHYSICS-ANCHORED | key:formula |
| ●●↘ | PI | `atlas_schema.json:903` | 23556fd 2025-10-09 | equation: P(x) ∝ x^(-α) | PHYSICS-ANCHORED | key:formula |
| ●●⚖️ | PI | `atlas_schema.json:910` | 23556fd 2025-10-09 | equation: System → critical state without tuning glyph_na~ | PHYSICS-ANCHORED | key:formula |
| ∿=∿ | PI | `atlas_schema.json:925` | 23556fd 2025-10-09 | equation: ω_drive = ω_natural | PHYSICS-ANCHORED | key:formula |
| ∿⚡ | PI | `atlas_schema.json:932` | 23556fd 2025-10-09 | equation: Q = ω₀/Δω = stored energy/dissipated energy | PHYSICS-ANCHORED | key:formula |
| 🧲∿⚛️ | PI | `atlas_schema.json:939` | 23556fd 2025-10-09 | equation: ω = γB₀ | PHYSICS-ANCHORED | key:formula |
| 🪐∿🪐 | PI | `atlas_schema.json:946` | 23556fd 2025-10-09 | equation: T₁/T₂ = n/m (rational ratio) | PHYSICS-ANCHORED | key:formula |
| ⎯∇⎯ | PI | `atlas_schema.json:961` | 23556fd 2025-10-09 | equation: ∂ρ/∂t + ∇·(ρv) = 0 | PHYSICS-ANCHORED | key:formula |
| ⎯→⎯ | PI | `atlas_schema.json:968` | 23556fd 2025-10-09 | equation: lim_{x→a} f(x) = f(a) | PHYSICS-ANCHORED | key:formula |
| ⎯⚡⎯ | PI | `atlas_schema.json:975` | 23556fd 2025-10-09 | equation: Σ I_in = Σ I_out | PHYSICS-ANCHORED | key:formula |
| ⎯∇=0 | PI | `atlas_schema.json:982` | 23556fd 2025-10-09 | equation: ∂_μ A^μ = 0 (Lorenz gauge) | PHYSICS-ANCHORED | key:formula |
| ▭⚡ | PI | `atlas_schema.json:997` | 23556fd 2025-10-09 | equation: E = hf = ℏω | PHYSICS-ANCHORED | key:formula |
| ▭ₙ∿ | PI | `atlas_schema.json:1004` | 23556fd 2025-10-09 | equation: E_n = ℏω(n + ½) | PHYSICS-ANCHORED | key:formula |
| ▭⚡ₙ | PI | `atlas_schema.json:1011` | 23556fd 2025-10-09 | equation: Q = ne (n ∈ ℤ) | PHYSICS-ANCHORED | key:formula |
| ▭⟲ | PI | `atlas_schema.json:1018` | 23556fd 2025-10-09 | equation: L = ℏ√(l(l+1)); L_z = mℏ | PHYSICS-ANCHORED | key:formula |
| ▯ | PI | `atlas_schema.json:1027` | 23556fd 2025-10-09 | process: id: P09 name: Proportion domain: Golden ratio, harmonic ratios, dimens~ | PHYSICS-ANCHORED | key:equations |
| ▯φ | PI | `atlas_schema.json:1033` | 23556fd 2025-10-09 | equation: φ = (1 + √5)/2 ≈ 1.618 | PHYSICS-ANCHORED | key:formula |
| ▯α⚛️ | PI | `atlas_schema.json:1040` | 23556fd 2025-10-09 | equation: α = e²/(4πε₀ℏc) ≈ 1/137 | PHYSICS-ANCHORED | key:formula |
| ▯ₙ∿ | PI | `atlas_schema.json:1047` | 23556fd 2025-10-09 | equation: f_n = nf₁ (n = 1, 2, 3…) | PHYSICS-ANCHORED | key:formula |
| ▯e | PI | `atlas_schema.json:1054` | 23556fd 2025-10-09 | equation: e = lim_{n→∞} (1 + 1/n)^n ≈ 2.718 | PHYSICS-ANCHORED | key:formula |
| ◧×◧≥ | PI | `atlas_schema.json:1069` | 23556fd 2025-10-09 | equation: Δx Δp ≥ ℏ/2 | PHYSICS-ANCHORED | key:formula |
| ◧² | PI | `atlas_schema.json:1076` | 23556fd 2025-10-09 | equation: Var(X) = E[(X - μ)²] | PHYSICS-ANCHORED | key:formula |
| ◧ℹ️ | PI | `atlas_schema.json:1083` | 23556fd 2025-10-09 | equation: H = -Σ p(x) log p(x) | PHYSICS-ANCHORED | key:formula |
| ◧∞ | PI | `atlas_schema.json:1090` | 23556fd 2025-10-09 | equation: ∃ true statements unprovable in system | PHYSICS-ANCHORED | key:formula |
| ↻∿→ℹ️ | PI | `atlas_schema.json:1105` | 23556fd 2025-10-09 | equation: F(ω) = ∫ f(t)e^(-iωt) dt | PHYSICS-ANCHORED | key:formula |
| ↻⏱→s | PI | `atlas_schema.json:1112` | 23556fd 2025-10-09 | equation: F(s) = ∫₀^∞ f(t)e^(-st) dt | PHYSICS-ANCHORED | key:formula |
| ❄️↻💧 | PI | `atlas_schema.json:1119` | 23556fd 2025-10-09 | equation: ∂G/∂T = -S; ∂²G/∂T² discontinuous | PHYSICS-ANCHORED | key:formula |
| ↻∇↔ | PI | `atlas_schema.json:1126` | 23556fd 2025-10-09 | equation: G(p) = f(x) - px where p = df/dx | PHYSICS-ANCHORED | key:formula |
| ⚡◎🧲 | PI | `atlas_schema.json:1141` | 23556fd 2025-10-09 | equation: ∇·E = ρ/ε₀; ∇×B - ∂E/∂t = μ₀J; etc. | PHYSICS-ANCHORED | key:formula |
| ◎⚛️ | PI | `atlas_schema.json:1148` | 23556fd 2025-10-09 | equation: SU(2) × U(1) → electromagnetic + weak | PHYSICS-ANCHORED | key:formula |
| ◎×= | PI | `atlas_schema.json:1155` | 23556fd 2025-10-09 | equation: a · e = e · a = a | PHYSICS-ANCHORED | key:formula |
| ◎=⚡ | PI | `atlas_schema.json:1162` | 23556fd 2025-10-09 | equation: E = mc² | PHYSICS-ANCHORED | key:formula |
| ⬡ | PI | `data/training/generate.py:48` | 81db773 2026-03-26 | none: meaning: F12 | NOT_INTERPRETABLE | label-only |
| ☆ | PI | `data/training/generate.py:50` | 81db773 2026-03-26 | none: meaning: F09 | NOT_INTERPRETABLE | label-only |
| ⚙ | PI | `data/training/generate.py:51` | 81db773 2026-03-26 | none: meaning: F11 | NOT_INTERPRETABLE | label-only |
| ↻ | PI | `data/training/generate.py:52` | 81db773 2026-03-26 | none: meaning: F02 | NOT_INTERPRETABLE | label-only |
| △≈ | PI | `data/training/generate.py:55` | 81db773 2026-03-26 | none: meaning: F05 | NOT_INTERPRETABLE | label-only |
| ⊗ | PI | `data/training/generate.py:56` | 81db773 2026-03-26 | none: meaning: F03 | NOT_INTERPRETABLE | label-only |
| ◎ | PI | `data/training/generate.py:57` | 81db773 2026-03-26 | none: meaning: F16 | NOT_INTERPRETABLE | label-only |
| ⋯⋯ | PI | `data/training/generate.py:58` | 81db773 2026-03-26 | none: meaning: F06 | NOT_INTERPRETABLE | label-only |
| •••• | PI | `data/training/generate.py:59` | 81db773 2026-03-26 | none: meaning: F04 | NOT_INTERPRETABLE | label-only |
| ◯ | PI | `data/training/generate.py:60` | 81db773 2026-03-26 | none: meaning: F07 | NOT_INTERPRETABLE | label-only |
| ◆ | PI | `data/training/generate.py:61` | 81db773 2026-03-26 | none: meaning: F08 | NOT_INTERPRETABLE | label-only |
| ⚪ | PI | `data/training/generate.py:62` | 81db773 2026-03-26 | none: meaning: F10 | NOT_INTERPRETABLE | label-only |
| ≡≡≡ | PI | `data/training/generate.py:618` | 07a01fb 2026-04-01 | none: meaning: F01 | NOT_INTERPRETABLE | label-only |
| ⇑ | PI | `data/training/generate.py:620` | 43934c3 2026-03-27 | none: meaning: F13 | NOT_INTERPRETABLE | label-only |
| ↕ | PI | `data/training/generate.py:620` | 07a01fb 2026-04-01 | none: meaning: F14 | NOT_INTERPRETABLE | label-only |
| ◆→ | PI | `data/training/generate.py:620` | 07a01fb 2026-04-01 | none: meaning: F15 | NOT_INTERPRETABLE | label-only |
| ⊗≡ | PI | `data/training/generate.py:621` | 07a01fb 2026-04-01 | none: meaning: F18 | NOT_INTERPRETABLE | label-only |
| ▁▃▅∿ | PI | `data/training/generate.py:621` | 43934c3 2026-03-27 | none: meaning: F19 | NOT_INTERPRETABLE | label-only |
| ∞ | PI | `data/training/generate.py:621` | 07a01fb 2026-04-01 | none: meaning: F20 | NOT_INTERPRETABLE | label-only |
| 〰〰〰 | PI | `data/training/generate.py:623` | 07a01fb 2026-04-01 | none: meaning: F01 | NOT_INTERPRETABLE | label-only |
| △≋ | PI | `data/training/generate.py:623` | 07a01fb 2026-04-01 | none: meaning: F05 | NOT_INTERPRETABLE | label-only |
| ◉ | PI | `data/training/generate.py:623` | 43934c3 2026-03-27 | none: meaning: F16 | NOT_INTERPRETABLE | label-only |
| ♾ | PI | `data/training/generate.py:623` | 07a01fb 2026-04-01 | none: meaning: F20 | NOT_INTERPRETABLE | label-only |
| ✦ | PI | `data/training/generate.py:623` | 07a01fb 2026-04-01 | none: meaning: F15 | NOT_INTERPRETABLE | label-only |
| ◠● | PI | `data/training/generate.py:624` | 07a01fb 2026-04-01 | none: meaning: F18 | NOT_INTERPRETABLE | label-only |
| ☯ | PI | `data/training/generate.py:624` | 07a01fb 2026-04-01 | none: meaning: F10 | NOT_INTERPRETABLE | label-only |
| ⒮ | PI | `data/training/generate.py:624` | 07a01fb 2026-04-01 | none: meaning: F04 | NOT_INTERPRETABLE | label-only |
| ∿| | PI | `data/training/generate.py:624` | 07a01fb 2026-04-01 | none: meaning: F14 | NOT_INTERPRETABLE | label-only |
| ⇑ | PI | `entries/0001_honeycomb_infrastructure.json:9` | 79eb7b1 2025-08-21 | none: meaning: Reaction lag reframed as fast feedback loop | NOT_INTERPRETABLE | label-only |
| ◧ | PI | `entries/0001_honeycomb_infrastructure.json:14` | 79eb7b1 2025-08-21 | none: meaning: Uncertainty reframed as hidden structural signal | NOT_INTERPRETABLE | label-only |
| ⇑ | PI | `entries/0002_echolocating_autonomy.json:9` | f015aab 2025-08-21 | none: meaning: Reaction lag reframed as probabilistic timing | NOT_INTERPRETABLE | label-only |
| ◧ | PI | `entries/0002_echolocating_autonomy.json:14` | f015aab 2025-08-21 | none: meaning: Uncertainty reframed as silence-signal | NOT_INTERPRETABLE | label-only |
| ⇑ | PI | `entries/0003_family_node_manufacturing.json:9` | 3696d83 2025-08-21 | none: meaning: Slower response reframed as long-term stability buffer | NOT_INTERPRETABLE | label-only |
| ◉ | PI | `entries/0003_family_node_manufacturing.json:9` | 3696d83 2025-08-21 | none: meaning: Consciousness fade reframed as need for cultural rituals/records | NOT_INTERPRETABLE | label-only |
| ▁▃▅∿ | PI | `entries/0003_family_node_manufacturing.json:9` | 3696d83 2025-08-21 | none: meaning: Statistical fluctuation reframed as diversity of outputs | NOT_INTERPRETABLE | label-only |
| ◧ | PI | `entries/0003_family_node_manufacturing.json:14` | 3696d83 2025-08-21 | function: meaning: Uncertainty reframed as ecological sensor | FUNCTION-ONLY | function-word:sensor |
| ⇑ | PI | `entries/0004_mycelial_computing.json:9` | 43934c3 2026-03-27 | function: meaning: Chemical slowness reframed as temporal filtering — noise rej~ | FUNCTION-ONLY | function-word:filtering |
| ⚙ | PI | `entries/0004_mycelial_computing.json:9` | 43934c3 2026-03-27 | none: meaning: Bio-digital interface gap reframed as translation layer and desi~ | NOT_INTERPRETABLE | label-only |
| ◎ | PI | `entries/0004_mycelial_computing.json:14` | 43934c3 2026-03-27 | none: meaning: Incomplete integration reframed as productive boundary between b~ | NOT_INTERPRETABLE | label-only |
| ◆→ | PI | `entries/0005_tidal_energy_harvest.json:9` | 43934c3 2026-03-27 | none: meaning: Shipping lane interference reframed as co-design opportunity — t~ | NOT_INTERPRETABLE | label-only |
| ⊗≡ | PI | `entries/0005_tidal_energy_harvest.json:9` | 43934c3 2026-03-27 | none: meaning: Site variability reframed as design diversity — each coast deman~ | NOT_INTERPRETABLE | label-only |
| ⊗ | PI | `entries/0005_tidal_energy_harvest.json:9` | 43934c3 2026-03-27 | process: meaning: Frame-dependence reframed as local adaptation — place-tuned r~ | PHYSICS-ANCHORED | physics-word:resonance |
| △≈ | PI | `entries/0006_quantum_navigation.json:9` | 43934c3 2026-03-27 | function: meaning: Extreme cooling requirements reframed as environmental selec~ | FUNCTION-ONLY | function-word:filtering |
| ∞ | PI | `entries/0006_quantum_navigation.json:9` | 43934c3 2026-03-27 | process: meaning: Topological fragility reframed as design frontier — topologic~ | PHYSICS-ANCHORED | physics-word:qubits |
| ◧ | PI | `entries/0006_quantum_navigation.json:14` | 43934c3 2026-03-27 | function: meaning: Heisenberg limits reframed as information boundary — uncerta~ | FUNCTION-ONLY | function-word:encodes |
| ▁▃▅∿ | PI | `entries/0007_emotional_architecture.json:9` | 43934c3 2026-03-27 | none: meaning: Population-level unpredictability reframed as collective emotion~ | NOT_INTERPRETABLE | label-only |
| ∞ | PI | `entries/0007_emotional_architecture.json:9` | 43934c3 2026-03-27 | none: meaning: Spatial rigidity reframed as constraint-driven creativity — fixe~ | NOT_INTERPRETABLE | label-only |
| ◧ | PI | `entries/0007_emotional_architecture.json:14` | 43934c3 2026-03-27 | none: meaning: Emotional unpredictability reframed as presence signal — system ~ | NOT_INTERPRETABLE | label-only |
| ⇑ | PI | `entries/0008_fractal_governance.json:9` | 43934c3 2026-03-27 | none: meaning: Bureaucratic delay reframed as deliberation buffer — slowness en~ | NOT_INTERPRETABLE | label-only |
| ⊗≡ | PI | `entries/0008_fractal_governance.json:9` | 43934c3 2026-03-27 | none: meaning: Cultural incompatibility reframed as diversity engine — local va~ | NOT_INTERPRETABLE | label-only |
| ↻ | PI | `entries/0008_fractal_governance.json:14` | 43934c3 2026-03-27 | function: meaning: Reform inertia reframed as stability anchor — resistance pro~ | FUNCTION-ONLY | function-word:anchor |
| △≈ | PI | `entries/0009_symbiotic_materials.json:9` | 43934c3 2026-03-27 | process: meaning: Metabolic cost reframed as environmental coupling — material'~ | PHYSICS-ANCHORED | physics-word:energy |
| ⇑ | PI | `entries/0009_symbiotic_materials.json:9` | 43934c3 2026-03-27 | none: meaning: Slow healing reframed as deep repair — biological processes rebu~ | NOT_INTERPRETABLE | label-only |
| ∞ | PI | `entries/0009_symbiotic_materials.json:9` | 43934c3 2026-03-27 | none: meaning: Topological instability during growth reframed as adaptive morph~ | NOT_INTERPRETABLE | label-only |
| ◎ | PI | `entries/0009_symbiotic_materials.json:14` | 43934c3 2026-03-27 | none: meaning: Bio-structural integration gap reframed as productive symbiosis ~ | NOT_INTERPRETABLE | label-only |
| ◎ | PI | `entries/0010_temporal_cartography.json:9` | 43934c3 2026-03-27 | function: meaning: Subjective time distortion reframed as experiential cartogra~ | FUNCTION-ONLY | function-word:map |
| ∞ | PI | `entries/0010_temporal_cartography.json:9` | 43934c3 2026-03-27 | none: meaning: Temporal loops and branches reframed as terrain features — mount~ | NOT_INTERPRETABLE | label-only |
| ⎯ | PI | `entries/0010_temporal_cartography.json:14` | 43934c3 2026-03-27 | function: meaning: Temporal discontinuities reframed as portals — phase transit~ | FUNCTION-ONLY | function-word:transitions |
| △≈ | PI | `entries/0011_coral_reef_symbiotic_resonance.json:9` | c2113c9 2026-07-02 | process: meaning: Thermal stress margin reframed as an early-warning resonance ~ | PHYSICS-ANCHORED | physics-word:thermal |
| ∞ | PI | `entries/0011_coral_reef_symbiotic_resonance.json:9` | c2113c9 2026-07-02 | none: meaning: Fracture-and-regrowth reframed as modular self-healing — the ree~ | NOT_INTERPRETABLE | label-only |
| ◧ | PI | `entries/0011_coral_reef_symbiotic_resonance.json:14` | c2113c9 2026-07-02 | function: meaning: Probabilistic bleaching threshold reframed as a hidden-struc~ | FUNCTION-ONLY | function-word:threshold |
| 🎵⚡ | PI | `equations/json/eq_001_wave_equation_1d_standing_wave.json:24` | 94c8673 2026-05-04 | process: id: EQ:001 canonical_name: Wave Equation (1D Standing Wave) canonical_~ | PHYSICS-ANCHORED | physics-word:wave |
| ⟲⟲⟲ | PI | `equations/json/eq_002_kuramoto_model.json:24` | 94c8673 2026-05-04 | process: id: EQ:002 canonical_name: Kuramoto Model canonical_form_latex: canoni~ | PHYSICS-ANCHORED | physics-word:resonance |
| ∿○ | PI | `equations/json/eq_003_resonance_frequency.json:24` | 94c8673 2026-05-04 | process: id: EQ:003 canonical_name: Resonance Frequency canonical_form_latex: c~ | PHYSICS-ANCHORED | formula-text |
| ∿∿∿⊕ | PI | `equations/json/eq_004_fourier_series.json:24` | 94c8673 2026-05-04 | process: id: EQ:004 canonical_name: Fourier Series canonical_form_latex: canoni~ | PHYSICS-ANCHORED | physics-word:fourier |
| 〰⇄∇ | PI | `equations/json/eq_005_navier_stokes_incompressible.json:24` | 94c8673 2026-05-04 | process: id: EQ:005 canonical_name: Navier-Stokes (Incompressible) canonical_fo~ | PHYSICS-ANCHORED | formula-text |
| ↗⚖↘ | PI | `equations/json/eq_006_bernoulli_s_equation.json:24` | 94c8673 2026-05-04 | process: id: EQ:006 canonical_name: Bernoulli's Equation canonical_form_latex: ~ | PHYSICS-ANCHORED | formula-text |
| 〰≋ | PI | `equations/json/eq_007_reynolds_number.json:24` | 94c8673 2026-05-04 | process: id: EQ:007 canonical_name: Reynolds Number canonical_form_latex: canon~ | PHYSICS-ANCHORED | formula-text |
| ⟳∇ | PI | `equations/json/eq_008_vorticity_equation.json:24` | 94c8673 2026-05-04 | process: id: EQ:008 canonical_name: Vorticity Equation canonical_form_latex: ca~ | PHYSICS-ANCHORED | formula-text |
| ℹ◧⊚ | PI | `equations/json/eq_009_shannon_entropy.json:24` | 94c8673 2026-05-04 | process: id: EQ:009 canonical_name: Shannon Entropy canonical_form_latex: canon~ | PHYSICS-ANCHORED | physics-word:entropy |
| 📡⚡ | PI | `equations/json/eq_010_channel_capacity.json:24` | 94c8673 2026-05-04 | process: id: EQ:010 canonical_name: Channel Capacity canonical_form_latex: cano~ | PHYSICS-ANCHORED | formula-text |
| ⊗↔⊗ | PI | `equations/json/eq_011_kullback_leibler_divergence.json:24` | 94c8673 2026-05-04 | process: id: EQ:011 canonical_name: Kullback-Leibler Divergence canonical_form_~ | PHYSICS-ANCHORED | physics-word:entropy |
| ⊗∩⊗ | PI | `equations/json/eq_012_mutual_information.json:24` | 94c8673 2026-05-04 | none: id: EQ:012 canonical_name: Mutual Information canonical_form_latex: canon~ | NOT_INTERPRETABLE | label-only |
| 🐇🦊⟲ | PI | `equations/json/eq_013_lotka_volterra_equations.json:24` | 94c8673 2026-05-04 | process: id: EQ:013 canonical_name: Lotka-Volterra Equations canonical_form_lat~ | PHYSICS-ANCHORED | formula-text |
| ⚗️🔑 | PI | `equations/json/eq_014_michaelis_menten_kinetics.json:24` | 94c8673 2026-05-04 | process: id: EQ:014 canonical_name: Michaelis-Menten Kinetics canonical_form_la~ | PHYSICS-ANCHORED | formula-text |
| 📈⊂ | PI | `equations/json/eq_015_logistic_growth.json:24` | 94c8673 2026-05-04 | process: id: EQ:015 canonical_name: Logistic Growth canonical_form_latex: canon~ | PHYSICS-ANCHORED | formula-text |
| ⚗️ⁿ | PI | `equations/json/eq_016_hill_equation.json:24` | 94c8673 2026-05-04 | none: id: EQ:016 canonical_name: Hill Equation canonical_form_latex: canonical_~ | NOT_INTERPRETABLE | label-only |
| 🔥⚖️ | PI | `equations/json/eq_017_first_law_of_thermodynamics.json:24` | 94c8673 2026-05-04 | process: id: EQ:017 canonical_name: First Law of Thermodynamics canonical_form_~ | PHYSICS-ANCHORED | formula-text |
| ⏳↗ | PI | `equations/json/eq_018_second_law_entropy.json:24` | 94c8673 2026-05-04 | process: id: EQ:018 canonical_name: Second Law (Entropy) canonical_form_latex: ~ | PHYSICS-ANCHORED | physics-word:entropy |
| 🌡️〰 | PI | `equations/json/eq_019_heat_equation.json:24` | 94c8673 2026-05-04 | process: id: EQ:019 canonical_name: Heat Equation canonical_form_latex: canonic~ | PHYSICS-ANCHORED | formula-text |
| ⚙️🔥❄️ | PI | `equations/json/eq_020_carnot_efficiency.json:24` | 94c8673 2026-05-04 | process: id: EQ:020 canonical_name: Carnot Efficiency canonical_form_latex: can~ | PHYSICS-ANCHORED | formula-text |
| 🧠⚡⬇️ | PI | `equations/json/eq_021_hopfield_network_energy.json:24` | 94c8673 2026-05-04 | process: id: EQ:021 canonical_name: Hopfield Network Energy canonical_form_late~ | PHYSICS-ANCHORED | formula-text |
| ⚡⚡➕ | PI | `equations/json/eq_022_hebbian_learning.json:24` | 94c8673 2026-05-04 | process: id: EQ:022 canonical_name: Hebbian Learning canonical_form_latex: cano~ | PHYSICS-ANCHORED | formula-text |
| 〰S | PI | `equations/json/eq_023_sigmoid_activation.json:24` | 94c8673 2026-05-04 | none: id: EQ:023 canonical_name: Sigmoid Activation canonical_form_latex: canon~ | NOT_INTERPRETABLE | label-only |
| ↩️∇ | PI | `equations/json/eq_024_backpropagation.json:24` | 94c8673 2026-05-04 | process: id: EQ:024 canonical_name: Backpropagation canonical_form_latex: canon~ | PHYSICS-ANCHORED | formula-text |
| 🪐⟲³ | PI | `equations/json/eq_025_kepler_s_third_law.json:24` | 94c8673 2026-05-04 | process: id: EQ:025 canonical_name: Kepler's Third Law canonical_form_latex: ca~ | PHYSICS-ANCHORED | formula-text |
| ●●⬌ | PI | `equations/json/eq_026_newton_s_gravitation.json:24` | 94c8673 2026-05-04 | process: id: EQ:026 canonical_name: Newton's Gravitation canonical_form_latex: ~ | PHYSICS-ANCHORED | formula-text |
| ⟲💨 | PI | `equations/json/eq_027_orbital_velocity.json:24` | 94c8673 2026-05-04 | process: id: EQ:027 canonical_name: Orbital Velocity canonical_form_latex: cano~ | PHYSICS-ANCHORED | formula-text |
| 🌊🌙 | PI | `equations/json/eq_028_tidal_force.json:24` | 94c8673 2026-05-04 | process: id: EQ:028 canonical_name: Tidal Force canonical_form_latex: canonical~ | PHYSICS-ANCHORED | formula-text |
| ⬆️⬇️⬆️⬇️ | PI | `equations/json/eq_029_ising_model.json:24` | 94c8673 2026-05-04 | process: id: EQ:029 canonical_name: Ising Model canonical_form_latex: canonical~ | PHYSICS-ANCHORED | formula-text |
| ⚡⚡❄️ | PI | `equations/json/eq_030_bcs_gap_equation.json:24` | 94c8673 2026-05-04 | process: id: EQ:030 canonical_name: BCS Gap Equation canonical_form_latex: cano~ | PHYSICS-ANCHORED | formula-text |
| 🧲↺ | PI | `equations/json/eq_031_london_equation.json:24` | 94c8673 2026-05-04 | process: id: EQ:031 canonical_name: London Equation canonical_form_latex: canon~ | PHYSICS-ANCHORED | formula-text |
| ⚡〰 | PI | `equations/json/eq_032_drude_model.json:24` | 94c8673 2026-05-04 | process: id: EQ:032 canonical_name: Drude Model canonical_form_latex: canonical~ | PHYSICS-ANCHORED | formula-text |
| △² | PI | `equations/json/eq_033_pythagorean_theorem.json:24` | 94c8673 2026-05-04 | process: id: EQ:033 canonical_name: Pythagorean Theorem canonical_form_latex: c~ | PHYSICS-ANCHORED | formula-text |
| ⌒⌓ | PI | `equations/json/eq_034_gaussian_curvature.json:24` | 94c8673 2026-05-04 | process: id: EQ:034 canonical_name: Gaussian Curvature canonical_form_latex: ca~ | PHYSICS-ANCHORED | formula-text |
| ∮⚫ | PI | `equations/json/eq_035_gauss_bonnet_theorem.json:24` | 94c8673 2026-05-04 | process: id: EQ:035 canonical_name: Gauss-Bonnet Theorem canonical_form_latex: ~ | PHYSICS-ANCHORED | formula-text |
| ∥ | PI | `equations/json/eq_036_parallel_postulate.json:24` | 94c8673 2026-05-04 | none: id: EQ:036 canonical_name: Parallel Postulate canonical_form_latex: canon~ | NOT_INTERPRETABLE | label-only |
| ⚛️↻ | PI | `equations/json/eq_037_dirac_equation.json:24` | 94c8673 2026-05-04 | process: id: EQ:037 canonical_name: Dirac Equation canonical_form_latex: canoni~ | PHYSICS-ANCHORED | formula-text |
| ⚪〰 | PI | `equations/json/eq_038_klein_gordon_equation.json:24` | 94c8673 2026-05-04 | process: id: EQ:038 canonical_name: Klein-Gordon Equation canonical_form_latex:~ | PHYSICS-ANCHORED | formula-text |
| ⚡∇⚡ | PI | `equations/json/eq_039_yang_mills_field_strength.json:24` | 94c8673 2026-05-04 | process: id: EQ:039 canonical_name: Yang-Mills Field Strength canonical_form_la~ | PHYSICS-ANCHORED | formula-text |
| ⚪⬇️⚡ | PI | `equations/json/eq_040_higgs_mechanism.json:24` | 94c8673 2026-05-04 | process: id: EQ:040 canonical_name: Higgs Mechanism canonical_form_latex: canon~ | PHYSICS-ANCHORED | physics-word:mass |
| ⟷↔ | PI | `equations/json/eq_041_hooke_s_law.json:24` | 94c8673 2026-05-04 | process: id: EQ:041 canonical_name: Hooke's Law canonical_form_latex: canonical~ | PHYSICS-ANCHORED | formula-text |
| ⚡〰⚡ | PI | `equations/json/eq_042_ohm_s_law.json:24` | 94c8673 2026-05-04 | process: id: EQ:042 canonical_name: Ohm's Law canonical_form_latex: canonical_f~ | PHYSICS-ANCHORED | formula-text |
| ⎯⌒⎯ | PI | `equations/json/eq_043_euler_bernoulli_beam.json:24` | 94c8673 2026-05-04 | none: id: EQ:043 canonical_name: Euler-Bernoulli Beam canonical_form_latex: can~ | NOT_INTERPRETABLE | label-only |
| ↻⚖️ | PI | `equations/json/eq_044_pid_controller.json:24` | 94c8673 2026-05-04 | process: id: EQ:044 canonical_name: PID Controller canonical_form_latex: canoni~ | PHYSICS-ANCHORED | formula-text |
| ⬡⬡⬡↘ | PI | `equations/json/eq_045_power_law_degree_distribution.json:24` | 94c8673 2026-05-04 | none: id: EQ:045 canonical_name: Power Law Degree Distribution canonical_form_l~ | NOT_INTERPRETABLE | label-only |
| △⬡ | PI | `equations/json/eq_046_clustering_coefficient.json:24` | 94c8673 2026-05-04 | process: id: EQ:046 canonical_name: Clustering Coefficient canonical_form_latex~ | PHYSICS-ANCHORED | formula-text |
| ⬡⚡⬡ | PI | `equations/json/eq_047_percolation_threshold.json:24` | 94c8673 2026-05-04 | process: id: EQ:047 canonical_name: Percolation Threshold canonical_form_latex:~ | PHYSICS-ANCHORED | formula-text |
| ∇⬡ | PI | `equations/json/eq_048_laplacian_matrix.json:24` | 94c8673 2026-05-04 | process: id: EQ:048 canonical_name: Laplacian Matrix canonical_form_latex: cano~ | PHYSICS-ANCHORED | formula-text |
| 🌡️⚡⬆️ | PI | `equations/json/eq_049_arrhenius_equation.json:24` | 94c8673 2026-05-04 | process: id: EQ:049 canonical_name: Arrhenius Equation canonical_form_latex: ca~ | PHYSICS-ANCHORED | formula-text |
| ⚗️⛰️⚗️ | PI | `equations/json/eq_050_transition_state_theory.json:24` | 94c8673 2026-05-04 | process: id: EQ:050 canonical_name: Transition State Theory canonical_form_late~ | PHYSICS-ANCHORED | formula-text |
| ⚗️×⚗️ | PI | `equations/json/eq_051_mass_action_law.json:24` | 94c8673 2026-05-04 | process: id: EQ:051 canonical_name: Mass Action Law canonical_form_latex: canon~ | PHYSICS-ANCHORED | formula-text |
| ⚗️↻⚗️⚗️ | PI | `equations/json/eq_052_autocatalytic_reaction.json:24` | 94c8673 2026-05-04 | process: id: EQ:052 canonical_name: Autocatalytic Reaction canonical_form_latex~ | PHYSICS-ANCHORED | formula-text |
| ↕️📊 | PI | `equations/json/eq_053_standard_deviation.json:24` | 94c8673 2026-05-04 | process: id: EQ:053 canonical_name: Standard Deviation canonical_form_latex: ca~ | PHYSICS-ANCHORED | formula-text |
| ◧↗ | PI | `equations/json/eq_054_uncertainty_propagation.json:24` | 94c8673 2026-05-04 | process: id: EQ:054 canonical_name: Uncertainty Propagation canonical_form_late~ | PHYSICS-ANCHORED | formula-text |
| 📡/〰 | PI | `equations/json/eq_055_signal_to_noise_ratio.json:24` | 94c8673 2026-05-04 | process: id: EQ:055 canonical_name: Signal-to-Noise Ratio canonical_form_latex:~ | PHYSICS-ANCHORED | formula-text |
| π▭ | PI | `equations/json/eq_056_buckingham_pi_theorem.json:24` | 94c8673 2026-05-04 | function: id: EQ:056 canonical_name: Buckingham Pi Theorem canonical_form_latex~ | FUNCTION-ONLY | function-word:measurement |
| 🌍⌒ | PI | `equations/json/eq_057_haversine_formula.json:24` | 94c8673 2026-05-04 | process: id: EQ:057 canonical_name: Haversine Formula canonical_form_latex: can~ | PHYSICS-ANCHORED | formula-text |
| ◆→◆→◆ | PI | `equations/json/eq_058_dijkstra_s_algorithm.json:24` | 94c8673 2026-05-04 | function: id: EQ:058 canonical_name: Dijkstra's Algorithm canonical_form_latex:~ | FUNCTION-ONLY | function-word:optimization |
| ⌒∇ | PI | `equations/json/eq_059_geodesic_equation.json:24` | 94c8673 2026-05-04 | none: id: EQ:059 canonical_name: Geodesic Equation canonical_form_latex: canoni~ | NOT_INTERPRETABLE | label-only |
| ↻📡 | PI | `equations/json/eq_060_kalman_filter.json:24` | 94c8673 2026-05-04 | process: id: EQ:060 canonical_name: Kalman Filter canonical_form_latex: canonic~ | PHYSICS-ANCHORED | formula-text |
| ◎∮ | PI | `equations/json/eq_061_integrated_information.json:24` | 94c8673 2026-05-04 | process: id: EQ:061 canonical_name: Integrated Information (Φ) canonical_form_l~ | PHYSICS-ANCHORED | formula-text |
| ◎⚡ | PI | `equations/json/eq_062_global_workspace_broadcasting.json:24` | 94c8673 2026-05-04 | none: id: EQ:062 canonical_name: Global Workspace Broadcasting canonical_form_l~ | NOT_INTERPRETABLE | label-only |
| ∿∿⟲ | PI | `equations/json/eq_063_phase_locking_value.json:24` | 94c8673 2026-05-04 | process: id: EQ:063 canonical_name: Phase-Locking Value canonical_form_latex: c~ | PHYSICS-ANCHORED | physics-word:oscillation |
| ◎⬇️ | PI | `equations/json/eq_064_free_energy_principle.json:24` | 94c8673 2026-05-04 | process: id: EQ:064 canonical_name: Free Energy Principle canonical_form_latex:~ | PHYSICS-ANCHORED | physics-word:energy |
| ⟳∞◬ | PI | `equations/json/eq_065_lorenz_attractor.json:24` | 94c8673 2026-05-04 | none: id: EQ:065 canonical_name: Lorenz Attractor canonical_form_latex: canonic~ | NOT_INTERPRETABLE | label-only |
| 〰↘〰 | PI | `equations/json/eq_066_kolmogorov_turbulence_scaling.json:24` | 94c8673 2026-05-04 | process: id: EQ:066 canonical_name: Kolmogorov Turbulence Scaling canonical_for~ | PHYSICS-ANCHORED | physics-word:energy |
| ⑂⑂⑂ | PI | `equations/json/eq_067_feigenbaum_constants.json:24` | 94c8673 2026-05-04 | process: id: EQ:067 canonical_name: Feigenbaum Constants canonical_form_latex: ~ | PHYSICS-ANCHORED | formula-text |
| 〰ᘯᘰ | PI | `equations/json/eq_068_navier_stokes_chaos_regimes.json:24` | 94c8673 2026-05-04 | process: id: EQ:068 canonical_name: Navier-Stokes Chaos Regimes canonical_form_~ | PHYSICS-ANCHORED | formula-text |
| ⊗≡⌒ | PI | `equations/json/eq_069_einstein_field_equations.json:24` | 94c8673 2026-05-04 | process: id: EQ:069 canonical_name: Einstein Field Equations canonical_form_lat~ | PHYSICS-ANCHORED | formula-text |
| ⊗⊕ | PI | `equations/json/eq_070_minkowski_metric.json:24` | 94c8673 2026-05-04 | process: id: EQ:070 canonical_name: Minkowski Metric canonical_form_latex: cano~ | PHYSICS-ANCHORED | formula-text |
| ↔️⚡ | PI | `equations/json/eq_071_lorentz_transformation.json:24` | 94c8673 2026-05-04 | none: id: EQ:071 canonical_name: Lorentz Transformation canonical_form_latex: c~ | NOT_INTERPRETABLE | label-only |
| 〰⊗〰 | PI | `equations/json/eq_072_gravitational_wave_equation.json:24` | 94c8673 2026-05-04 | process: id: EQ:072 canonical_name: Gravitational Wave Equation canonical_form_~ | PHYSICS-ANCHORED | formula-text |
| Σ⚡❄️ | PI | `equations/json/eq_073_partition_function.json:24` | 94c8673 2026-05-04 | process: id: EQ:073 canonical_name: Partition Function canonical_form_latex: ca~ | PHYSICS-ANCHORED | formula-text |
| 📊⬇️🌡️ | PI | `equations/json/eq_074_boltzmann_distribution.json:24` | 94c8673 2026-05-04 | process: id: EQ:074 canonical_name: Boltzmann Distribution canonical_form_latex~ | PHYSICS-ANCHORED | physics-word:boltzmann |
| 〰⇄ | PI | `equations/json/eq_075_fluctuation_dissipation_theorem.json:24` | 94c8673 2026-05-04 | none: id: EQ:075 canonical_name: Fluctuation-Dissipation Theorem canonical_form~ | NOT_INTERPRETABLE | label-only |
| 🌡️² | PI | `equations/json/eq_076_heat_capacity.json:24` | 94c8673 2026-05-04 | process: id: EQ:076 canonical_name: Heat Capacity canonical_form_latex: canonic~ | PHYSICS-ANCHORED | formula-text |
| ⬡-⎯+△ | PI | `equations/json/eq_077_euler_characteristic.json:24` | 94c8673 2026-05-04 | process: id: EQ:077 canonical_name: Euler Characteristic canonical_form_latex: ~ | PHYSICS-ANCHORED | formula-text |
| ∮⊗ | PI | `equations/json/eq_078_chern_class_first.json:24` | 94c8673 2026-05-04 | none: id: EQ:078 canonical_name: Chern Class (First) canonical_form_latex: cano~ | NOT_INTERPRETABLE | label-only |
| ∞⟲ | PI | `equations/json/eq_079_jones_polynomial.json:24` | 94c8673 2026-05-04 | none: id: EQ:079 canonical_name: Jones Polynomial canonical_form_latex: canonic~ | NOT_INTERPRETABLE | label-only |
| ⟲/∼ | PI | `equations/json/eq_080_fundamental_group.json:24` | 94c8673 2026-05-04 | none: id: EQ:080 canonical_name: Fundamental Group canonical_form_latex: canoni~ | NOT_INTERPRETABLE | label-only |
| ⧖→⚖️ | PI | `equations/json/eq_081_noether_s_theorem.json:24` | 94c8673 2026-05-04 | process: id: EQ:081 canonical_name: Noether's Theorem canonical_form_latex: can~ | PHYSICS-ANCHORED | formula-text |
| ⧖×⧖ | PI | `equations/json/eq_082_group_representation.json:24` | 94c8673 2026-05-04 | none: id: EQ:082 canonical_name: Group Representation canonical_form_latex: can~ | NOT_INTERPRETABLE | label-only |
| ⧖⟲⧖ | PI | `equations/json/eq_083_cpt_symmetry.json:24` | 94c8673 2026-05-04 | none: id: EQ:083 canonical_name: CPT Symmetry canonical_form_latex: canonical_f~ | NOT_INTERPRETABLE | label-only |
| ⧖∇ | PI | `equations/json/eq_084_gauge_symmetry.json:24` | 94c8673 2026-05-04 | process: id: EQ:084 canonical_name: Gauge Symmetry canonical_form_latex: canoni~ | PHYSICS-ANCHORED | formula-text |
| ⚡↺ | PI | `equations/json/eq_085_energy_conservation.json:24` | 94c8673 2026-05-04 | process: id: EQ:085 canonical_name: Energy Conservation canonical_form_latex: c~ | PHYSICS-ANCHORED | formula-text |
| →↺ | PI | `equations/json/eq_086_momentum_conservation.json:24` | 94c8673 2026-05-04 | process: id: EQ:086 canonical_name: Momentum Conservation canonical_form_latex:~ | PHYSICS-ANCHORED | formula-text |
| ⚡↺∇ | PI | `equations/json/eq_087_charge_conservation.json:24` | 94c8673 2026-05-04 | process: id: EQ:087 canonical_name: Charge Conservation canonical_form_latex: c~ | PHYSICS-ANCHORED | formula-text |
| ⟲↺ | PI | `equations/json/eq_088_angular_momentum_conservation.json:24` | 94c8673 2026-05-04 | process: id: EQ:088 canonical_name: Angular Momentum Conservation canonical_for~ | PHYSICS-ANCHORED | formula-text |
| ⊗=⊗ | PI | `equations/json/eq_089_lorentz_invariance.json:24` | 94c8673 2026-05-04 | process: id: EQ:089 canonical_name: Lorentz Invariance canonical_form_latex: ca~ | PHYSICS-ANCHORED | formula-text |
| ⊗≡⇅ | PI | `equations/json/eq_090_equivalence_principle.json:24` | 94c8673 2026-05-04 | process: id: EQ:090 canonical_name: Equivalence Principle canonical_form_latex:~ | PHYSICS-ANCHORED | physics-word:gravitation |
| ⊗∀⊗ | PI | `equations/json/eq_091_general_covariance.json:24` | 94c8673 2026-05-04 | none: id: EQ:091 canonical_name: General Covariance canonical_form_latex: canon~ | NOT_INTERPRETABLE | label-only |
| ⚡⊗ | PI | `equations/json/eq_092_light_speed_constancy.json:24` | 94c8673 2026-05-04 | process: id: EQ:092 canonical_name: Light Speed Constancy canonical_form_latex:~ | PHYSICS-ANCHORED | formula-text |
| 〰◑⚫ | PI | `equations/json/eq_093_wave_particle_duality.json:24` | 94c8673 2026-05-04 | process: id: EQ:093 canonical_name: Wave-Particle Duality canonical_form_latex:~ | PHYSICS-ANCHORED | formula-text |
| ⚡◑🧲 | PI | `equations/json/eq_094_electric_magnetic_duality.json:24` | 94c8673 2026-05-04 | process: id: EQ:094 canonical_name: Electric-Magnetic Duality canonical_form_la~ | PHYSICS-ANCHORED | formula-text |
| ◆◑→ | PI | `equations/json/eq_095_position_momentum_duality.json:28` | 94c8673 2026-05-04 | process: id: EQ:095 canonical_name: Position-Momentum Duality canonical_form_la~ | PHYSICS-ANCHORED | physics-word:momentum |
| ⏱◑⚡ | PI | `equations/json/eq_096_time_energy_duality.json:24` | 94c8673 2026-05-04 | process: id: EQ:096 canonical_name: Time-Energy Duality canonical_form_latex: c~ | PHYSICS-ANCHORED | physics-word:energy |
| ●●→●●● | PI | `equations/json/eq_097_conway_s_game_of_life.json:24` | 94c8673 2026-05-04 | process: id: EQ:097 canonical_name: Conway's Game of Life canonical_form_latex:~ | PHYSICS-ANCHORED | formula-text |
| ●●↗∞ | PI | `equations/json/eq_098_critical_exponent.json:24` | 94c8673 2026-05-04 | process: id: EQ:098 canonical_name: Critical Exponent canonical_form_latex: can~ | PHYSICS-ANCHORED | formula-text |
| ●●↘ | PI | `equations/json/eq_099_power_law.json:24` | 94c8673 2026-05-04 | none: id: EQ:099 canonical_name: Power Law canonical_form_latex: canonical_form~ | NOT_INTERPRETABLE | label-only |
| ●●⚖️ | PI | `equations/json/eq_100_self_organized_criticality.json:24` | 94c8673 2026-05-04 | process: id: EQ:100 canonical_name: Self-Organized Criticality canonical_form_l~ | PHYSICS-ANCHORED | formula-text |
| ∿=∿ | PI | `equations/json/eq_101_resonance_condition.json:24` | 94c8673 2026-05-04 | process: id: EQ:101 canonical_name: Resonance Condition canonical_form_latex: c~ | PHYSICS-ANCHORED | formula-text |
| ∿⚡ | PI | `equations/json/eq_102_q_factor.json:24` | 94c8673 2026-05-04 | process: id: EQ:102 canonical_name: Q Factor canonical_form_latex: canonical_fo~ | PHYSICS-ANCHORED | formula-text |
| 🧲∿⚛️ | PI | `equations/json/eq_103_nmr_resonance.json:24` | 94c8673 2026-05-04 | process: id: EQ:103 canonical_name: NMR Resonance canonical_form_latex: canonic~ | PHYSICS-ANCHORED | formula-text |
| 🪐∿🪐 | PI | `equations/json/eq_104_orbital_resonance.json:24` | 94c8673 2026-05-04 | process: id: EQ:104 canonical_name: Orbital Resonance canonical_form_latex: can~ | PHYSICS-ANCHORED | formula-text |
| ⎯∇⎯ | PI | `equations/json/eq_105_continuity_equation.json:24` | 94c8673 2026-05-04 | process: id: EQ:105 canonical_name: Continuity Equation canonical_form_latex: c~ | PHYSICS-ANCHORED | physics-word:conservation |
| ⎯→⎯ | PI | `equations/json/eq_106_cauchy_continuity.json:24` | 94c8673 2026-05-04 | process: id: EQ:106 canonical_name: Cauchy Continuity canonical_form_latex: can~ | PHYSICS-ANCHORED | formula-text |
| ⎯⚡⎯ | PI | `equations/json/eq_107_kirchhoff_s_current_law.json:24` | 94c8673 2026-05-04 | process: id: EQ:107 canonical_name: Kirchhoff's Current Law canonical_form_late~ | PHYSICS-ANCHORED | formula-text |
| ⎯∇=0 | PI | `equations/json/eq_108_gauge_continuity.json:24` | 94c8673 2026-05-04 | process: id: EQ:108 canonical_name: Gauge Continuity canonical_form_latex: cano~ | PHYSICS-ANCHORED | formula-text |
| ▭⚡ | PI | `equations/json/eq_109_planck_relation.json:24` | 94c8673 2026-05-04 | process: id: EQ:109 canonical_name: Planck Relation canonical_form_latex: canon~ | PHYSICS-ANCHORED | formula-text |
| ▭ₙ∿ | PI | `equations/json/eq_110_quantum_harmonic_oscillator.json:24` | 94c8673 2026-05-04 | process: id: EQ:110 canonical_name: Quantum Harmonic Oscillator canonical_form_~ | PHYSICS-ANCHORED | formula-text |
| ▭⚡ₙ | PI | `equations/json/eq_111_charge_quantization.json:24` | 94c8673 2026-05-04 | process: id: EQ:111 canonical_name: Charge Quantization canonical_form_latex: c~ | PHYSICS-ANCHORED | formula-text |
| ▭⟲ | PI | `equations/json/eq_112_angular_momentum_quantization.json:24` | 94c8673 2026-05-04 | process: id: EQ:112 canonical_name: Angular Momentum Quantization canonical_for~ | PHYSICS-ANCHORED | formula-text |
| ▯φ | PI | `equations/json/eq_113_golden_ratio.json:24` | 94c8673 2026-05-04 | process: id: EQ:113 canonical_name: Golden Ratio canonical_form_latex: canonica~ | PHYSICS-ANCHORED | formula-text |
| ▯α⚛️ | PI | `equations/json/eq_114_fine_structure_constant.json:24` | 94c8673 2026-05-04 | process: id: EQ:114 canonical_name: Fine Structure Constant canonical_form_late~ | PHYSICS-ANCHORED | formula-text |
| ▯ₙ∿ | PI | `equations/json/eq_115_harmonic_series.json:24` | 94c8673 2026-05-04 | process: id: EQ:115 canonical_name: Harmonic Series canonical_form_latex: canon~ | PHYSICS-ANCHORED | formula-text |
| ▯e | PI | `equations/json/eq_116_euler_s_number.json:24` | 94c8673 2026-05-04 | process: id: EQ:116 canonical_name: Euler's Number canonical_form_latex: canoni~ | PHYSICS-ANCHORED | formula-text |
| ◧² | PI | `equations/json/eq_117_variance.json:24` | 94c8673 2026-05-04 | function: id: EQ:117 canonical_name: Variance canonical_form_latex: canonical_f~ | FUNCTION-ONLY | function-word:measure |
| ◧ℹ️ | PI | `equations/json/eq_118_information_entropy.json:24` | 94c8673 2026-05-04 | process: id: EQ:118 canonical_name: Information Entropy canonical_form_latex: c~ | PHYSICS-ANCHORED | formula-text |
| ◧∞ | PI | `equations/json/eq_119_g_del_incompleteness.json:24` | 94c8673 2026-05-04 | function: id: EQ:119 canonical_name: Gödel Incompleteness canonical_form_latex:~ | FUNCTION-ONLY | function-word:statements |
| ↻∿→ℹ️ | PI | `equations/json/eq_120_fourier_transform.json:24` | 94c8673 2026-05-04 | process: id: EQ:120 canonical_name: Fourier Transform canonical_form_latex: can~ | PHYSICS-ANCHORED | physics-word:fourier |
| ↻⏱→s | PI | `equations/json/eq_121_laplace_transform.json:24` | 94c8673 2026-05-04 | function: id: EQ:121 canonical_name: Laplace Transform canonical_form_latex: ca~ | FUNCTION-ONLY | function-word:mapping |
| ❄️↻💧 | PI | `equations/json/eq_122_phase_transition.json:24` | 94c8673 2026-05-04 | process: id: EQ:122 canonical_name: Phase Transition canonical_form_latex: cano~ | PHYSICS-ANCHORED | formula-text |
| ↻∇↔ | PI | `equations/json/eq_123_legendre_transform.json:24` | 94c8673 2026-05-04 | process: id: EQ:123 canonical_name: Legendre Transform canonical_form_latex: ca~ | PHYSICS-ANCHORED | formula-text |
| ⚡◎🧲 | PI | `equations/json/eq_124_maxwell_s_unification.json:24` | 94c8673 2026-05-04 | process: id: EQ:124 canonical_name: Maxwell's Unification canonical_form_latex:~ | PHYSICS-ANCHORED | formula-text |
| ◎⚛️ | PI | `equations/json/eq_125_electroweak_unification.json:24` | 94c8673 2026-05-04 | process: id: EQ:125 canonical_name: Electroweak Unification canonical_form_late~ | PHYSICS-ANCHORED | physics-word:electroweak |
| ◎×= | PI | `equations/json/eq_126_identity_element.json:24` | 94c8673 2026-05-04 | process: id: EQ:126 canonical_name: Identity Element canonical_form_latex: cano~ | PHYSICS-ANCHORED | formula-text |
| ◎=⚡ | PI | `equations/json/eq_127_einstein_s_mass_energy.json:24` | 94c8673 2026-05-04 | process: id: EQ:127 canonical_name: Einstein's Mass-Energy canonical_form_latex~ | PHYSICS-ANCHORED | formula-text |
| ◇∿◇ | PI | `equations/json/eq_128_turing_reaction_diffusion.json:24` | c2113c9 2026-07-02 | process: id: EQ:128 canonical_name: Turing Reaction-Diffusion canonical_form_la~ | PHYSICS-ANCHORED | formula-text |
| ≡≡≡ | PI | `ontology/families.json:47` | 22ea0c0 2026-05-04 | process: id: FAM:RESONANCE legacy_id: F01 name: Resonance symbol_canonical: ≡≡≡~ | PHYSICS-ANCHORED | physics-word:resonance |
| ↻ | PI | `ontology/families.json:80` | 22ea0c0 2026-05-04 | process: id: FAM:FLOW legacy_id: F02 name: Flow symbol_canonical: ↻ description~ | PHYSICS-ANCHORED | physics-word:navier |
| ⊗ | PI | `ontology/families.json:113` | 22ea0c0 2026-05-04 | process: id: FAM:INFORMATION legacy_id: F03 name: Information symbol_canonical:~ | PHYSICS-ANCHORED | physics-word:entropy |
| •••• | PI | `ontology/families.json:146` | 22ea0c0 2026-05-04 | process: id: FAM:LIFE legacy_id: F04 name: Life symbol_canonical: •••• descript~ | PHYSICS-ANCHORED | physics-word:resonance |
| △≈ | PI | `ontology/families.json:179` | 22ea0c0 2026-05-04 | process: id: FAM:ENERGY_THERMO legacy_id: F05 name: Energy-Thermo symbol_canoni~ | PHYSICS-ANCHORED | physics-word:energy_thermo |
| ⋯⋯ | PI | `ontology/families.json:211` | 22ea0c0 2026-05-04 | process: id: FAM:COGNITION legacy_id: F06 name: Cognition symbol_canonical: ⋯⋯ ~ | PHYSICS-ANCHORED | physics-word:oscillations |
| ◯ | PI | `ontology/families.json:244` | 22ea0c0 2026-05-04 | process: id: FAM:EARTH_COSMOS legacy_id: F07 name: Earth-Cosmos symbol_canonica~ | PHYSICS-ANCHORED | physics-word:kepler |
| ◆ | PI | `ontology/families.json:277` | 22ea0c0 2026-05-04 | function: id: FAM:MATTER legacy_id: F08 name: Matter symbol_canonical: ◆ descri~ | FUNCTION-ONLY | function-word:transitions |
| ☆ | PI | `ontology/families.json:310` | 22ea0c0 2026-05-04 | none: id: FAM:GEOMETRY legacy_id: F09 name: Geometry symbol_canonical: ☆ descri~ | NOT_INTERPRETABLE | label-only |
| ⚪ | PI | `ontology/families.json:343` | 22ea0c0 2026-05-04 | process: id: FAM:PARTICLE legacy_id: F10 name: Particle symbol_canonical: ⚪ des~ | PHYSICS-ANCHORED | physics-word:quantum |
| ⚙ | PI | `ontology/families.json:376` | 22ea0c0 2026-05-04 | process: id: FAM:ENGINEERING legacy_id: F11 name: Engineering symbol_canonical:~ | PHYSICS-ANCHORED | physics-word:electrical |
| ⬡ | PI | `ontology/families.json:409` | 22ea0c0 2026-05-04 | process: id: FAM:NETWORKS legacy_id: F12 name: Networks symbol_canonical: ⬡ des~ | PHYSICS-ANCHORED | physics-word:resonance |
| ⇑ | PI | `ontology/families.json:442` | 22ea0c0 2026-05-04 | process: id: FAM:REACTION legacy_id: F13 name: Reaction symbol_canonical: ⇑ des~ | PHYSICS-ANCHORED | physics-word:arrhenius |
| ↕ | PI | `ontology/families.json:476` | 22ea0c0 2026-05-04 | function: id: FAM:MEASUREMENT legacy_id: F14 name: Measurement symbol_canonical~ | FUNCTION-ONLY | function-word:measurement |
| ◆→ | PI | `ontology/families.json:509` | 22ea0c0 2026-05-04 | function: id: FAM:NAVIGATION legacy_id: F15 name: Navigation symbol_canonical: ~ | FUNCTION-ONLY | function-word:routing |
| ◎ | PI | `ontology/families.json:542` | 22ea0c0 2026-05-04 | process: id: FAM:CONSCIOUSNESS legacy_id: F16 name: Consciousness symbol_canoni~ | PHYSICS-ANCHORED | physics-word:oscillations |
| ᘯᘰ | PI | `ontology/families.json:575` | 22ea0c0 2026-05-04 | process: id: FAM:TURBULENCE legacy_id: F17 name: Turbulence symbol_canonical: ᘯ~ | PHYSICS-ANCHORED | physics-word:navier |
| ⊗≡ | PI | `ontology/families.json:608` | 22ea0c0 2026-05-04 | process: id: FAM:RELATIVITY legacy_id: F18 name: Relativity symbol_canonical: ⊗~ | PHYSICS-ANCHORED | physics-word:gravitational |
| ▁▃▅∿ | PI | `ontology/families.json:641` | 22ea0c0 2026-05-04 | process: id: FAM:STATISTICAL legacy_id: F19 name: Statistical symbol_canonical:~ | PHYSICS-ANCHORED | physics-word:boltzmann |
| ∞ | PI | `ontology/families.json:674` | 22ea0c0 2026-05-04 | none: id: FAM:TOPOLOGY legacy_id: F20 name: Topology symbol_canonical: ∞ descri~ | NOT_INTERPRETABLE | label-only |
| ↻ | PI | `ontology/principles.json:50` | 22ea0c0 2026-05-04 | process: id: PRIN:TRANSFORMATION legacy_id: P11 name: Transformation symbol_can~ | PHYSICS-ANCHORED | physics-word:fourier |
| ⧖ | PI | `ontology/principles.json:60` | 22ea0c0 2026-05-04 | process: id: PRIN:SYMMETRY legacy_id: P01 name: Symmetry symbol_canonical: ⧖ de~ | PHYSICS-ANCHORED | physics-word:conservation |
| ↺ | PI | `ontology/principles.json:95` | 22ea0c0 2026-05-04 | process: id: PRIN:CONSERVATION legacy_id: P02 name: Conservation symbol_canonic~ | PHYSICS-ANCHORED | physics-word:conservation |
| ⊗ | PI | `ontology/principles.json:130` | 22ea0c0 2026-05-04 | process: id: PRIN:RELATIVITY legacy_id: P03 name: Relativity symbol_canonical: ~ | PHYSICS-ANCHORED | physics-word:resonance |
| ◑ | PI | `ontology/principles.json:165` | 22ea0c0 2026-05-04 | process: id: PRIN:DUALITY legacy_id: P04 name: Duality symbol_canonical: ◑ desc~ | PHYSICS-ANCHORED | physics-word:wave |
| ●● | PI | `ontology/principles.json:200` | 22ea0c0 2026-05-04 | process: id: PRIN:EMERGENCE legacy_id: P05 name: Emergence symbol_canonical: ●●~ | PHYSICS-ANCHORED | physics-word:conservation |
| ∿ | PI | `ontology/principles.json:235` | 22ea0c0 2026-05-04 | process: id: PRIN:RESONANCE legacy_id: P06 name: Resonance symbol_canonical: ∿ ~ | PHYSICS-ANCHORED | physics-word:resonance |
| ⎯ | PI | `ontology/principles.json:270` | 22ea0c0 2026-05-04 | process: id: PRIN:CONTINUITY legacy_id: P07 name: Continuity symbol_canonical: ~ | PHYSICS-ANCHORED | physics-word:conservation |
| ▭ | PI | `ontology/principles.json:305` | 22ea0c0 2026-05-04 | process: id: PRIN:QUANTIZATION legacy_id: P08 name: Quantization symbol_canonic~ | PHYSICS-ANCHORED | physics-word:energy |
| ▯ | PI | `ontology/principles.json:340` | 22ea0c0 2026-05-04 | process: id: PRIN:PROPORTION legacy_id: P09 name: Proportion symbol_canonical: ~ | PHYSICS-ANCHORED | physics-word:golden ratio |
| ◧ | PI | `ontology/principles.json:375` | 22ea0c0 2026-05-04 | process: id: PRIN:UNCERTAINTY legacy_id: P10 name: Uncertainty symbol_canonical~ | PHYSICS-ANCHORED | physics-word:entropy |
| ◎ | PI | `ontology/principles.json:445` | 22ea0c0 2026-05-04 | process: id: PRIN:UNITY legacy_id: P12 name: Unity symbol_canonical: ◎ descript~ | PHYSICS-ANCHORED | physics-word:maxwell |
| ≡≡≡ | PI | `protocols.json:3` | a86dfc9 2025-08-23 | process: id: F01 name: Resonance equations: | PHYSICS-ANCHORED | physics-word:resonance |
| ↻ | PI | `protocols.json:4` | a86dfc9 2025-08-23 | none: id: F02 name: Flow equations: | NOT_INTERPRETABLE | label-only |
| ⊗ | PI | `protocols.json:5` | a86dfc9 2025-08-23 | none: id: F03 name: Information equations: | NOT_INTERPRETABLE | label-only |
| •••• | PI | `protocols.json:6` | a86dfc9 2025-08-23 | none: id: F04 name: Life equations: | NOT_INTERPRETABLE | label-only |
| △≈ | PI | `protocols.json:7` | a86dfc9 2025-08-23 | process: id: F05 name: Energy-Thermo equations: | PHYSICS-ANCHORED | physics-word:energy |
| ⋯⋯ | PI | `protocols.json:8` | a86dfc9 2025-08-23 | none: id: F06 name: Cognition equations: | NOT_INTERPRETABLE | label-only |
| ◯ | PI | `protocols.json:9` | a86dfc9 2025-08-23 | none: id: F07 name: Earth-Cosmos equations: | NOT_INTERPRETABLE | label-only |
| ◆ | PI | `protocols.json:10` | a86dfc9 2025-08-23 | none: id: F08 name: Matter equations: | NOT_INTERPRETABLE | label-only |
| ☆ | PI | `protocols.json:11` | a86dfc9 2025-08-23 | none: id: F09 name: Geometry equations: | NOT_INTERPRETABLE | label-only |
| ⚪ | PI | `protocols.json:12` | a86dfc9 2025-08-23 | none: id: F10 name: Particle equations: | NOT_INTERPRETABLE | label-only |
| ⚙ | PI | `protocols.json:13` | a86dfc9 2025-08-23 | none: id: F11 name: Engineering equations: | NOT_INTERPRETABLE | label-only |
| ⬡ | PI | `protocols.json:14` | a86dfc9 2025-08-23 | none: id: F12 name: Networks equations: | NOT_INTERPRETABLE | label-only |
| ⇑ | PI | `protocols.json:15` | a86dfc9 2025-08-23 | none: id: F13 name: Reaction equations: | NOT_INTERPRETABLE | label-only |
| ↕ | PI | `protocols.json:16` | a86dfc9 2025-08-23 | function: id: F14 name: Measurement equations: | FUNCTION-ONLY | function-word:measurement |
| ◆→ | PI | `protocols.json:17` | a86dfc9 2025-08-23 | none: id: F15 name: Navigation equations: | NOT_INTERPRETABLE | label-only |
| ◎ | PI | `protocols.json:18` | a86dfc9 2025-08-23 | none: id: F16 name: Consciousness equations: | NOT_INTERPRETABLE | label-only |
| ᘯᘰ | PI | `protocols.json:19` | a86dfc9 2025-08-23 | none: id: F17 name: Turbulence equations: | NOT_INTERPRETABLE | label-only |
| ⊗≡ | PI | `protocols.json:20` | a86dfc9 2025-08-23 | none: id: F18 name: Relativity equations: | NOT_INTERPRETABLE | label-only |
| ⊗ | PI | `protocols.json:20` | a86dfc9 2025-08-23 | none: id: P03 name: Relativity equations: | NOT_INTERPRETABLE | label-only |
| ▁▃▅∿ | PI | `protocols.json:21` | a86dfc9 2025-08-23 | none: id: F19 name: Statistical equations: | NOT_INTERPRETABLE | label-only |
| ∿ | PI | `protocols.json:21` | a86dfc9 2025-08-23 | process: id: P06 name: Resonance equations: | PHYSICS-ANCHORED | physics-word:resonance |
| ∞ | PI | `protocols.json:22` | a86dfc9 2025-08-23 | none: id: F20 name: Topology equations: | NOT_INTERPRETABLE | label-only |
| ⧖ | PI | `protocols.json:25` | a86dfc9 2025-08-23 | none: id: P01 name: Symmetry equations: | NOT_INTERPRETABLE | label-only |
| ↺ | PI | `protocols.json:26` | a86dfc9 2025-08-23 | process: id: P02 name: Conservation equations: | PHYSICS-ANCHORED | physics-word:conservation |
| ◑ | PI | `protocols.json:28` | a86dfc9 2025-08-23 | none: id: P04 name: Duality equations: | NOT_INTERPRETABLE | label-only |
| ●● | PI | `protocols.json:29` | a86dfc9 2025-08-23 | none: id: P05 name: Emergence equations: | NOT_INTERPRETABLE | label-only |
| ⎯ | PI | `protocols.json:31` | a86dfc9 2025-08-23 | none: id: P07 name: Continuity equations: | NOT_INTERPRETABLE | label-only |
| ▭ | PI | `protocols.json:32` | a86dfc9 2025-08-23 | none: id: P08 name: Quantization equations: | NOT_INTERPRETABLE | label-only |
| ▯ | PI | `protocols.json:33` | a86dfc9 2025-08-23 | none: id: P09 name: Proportion equations: | NOT_INTERPRETABLE | label-only |
| ◧ | PI | `protocols.json:34` | a86dfc9 2025-08-23 | none: id: P10 name: Uncertainty equations: | NOT_INTERPRETABLE | label-only |
| ↻ | PI | `protocols.json:35` | a86dfc9 2025-08-23 | none: id: P11 name: Transformation equations: | NOT_INTERPRETABLE | label-only |
| ◎ | PI | `protocols.json:36` | a86dfc9 2025-08-23 | none: id: P12 name: Unity equations: | NOT_INTERPRETABLE | label-only |
| ⚖️ | RSC | `balance.json:3` | 126288d 2025-09-29 | process: pattern_id: PATTERN:BALANCE layers: symbolic: glyph: ⚖️ meaning: dynam~ | PHYSICS-ANCHORED | formula-text |
| ⚖️ | RSC | `balance.json:6` | 126288d 2025-09-29 | none: meaning: dynamic equilibrium and opposing forces in harmony bloom_behavio~ | NOT_INTERPRETABLE | label-only |
| ⊕ | RSC | `bridges/mandala-compute-bridge.json:19` | 60b13b2 2026-03-27 | function: state: 0 label: +x mandala_glyph: octahedron.+x physics_bridge: north~ | FUNCTION-ONLY | key:state |
| ⊖ | RSC | `bridges/mandala-compute-bridge.json:20` | 60b13b2 2026-03-27 | function: state: 1 label: -x mandala_glyph: octahedron.-x physics_bridge: south~ | FUNCTION-ONLY | key:state |
| ⊗ | RSC | `bridges/mandala-compute-bridge.json:21` | 60b13b2 2026-03-27 | function: state: 2 label: +y mandala_glyph: octahedron.+y physics_bridge: east ~ | FUNCTION-ONLY | key:state |
| ⊘ | RSC | `bridges/mandala-compute-bridge.json:22` | 60b13b2 2026-03-27 | function: state: 3 label: -y mandala_glyph: octahedron.-y physics_bridge: west ~ | FUNCTION-ONLY | key:state |
| ⊙ | RSC | `bridges/mandala-compute-bridge.json:23` | 60b13b2 2026-03-27 | function: state: 4 label: +z mandala_glyph: octahedron.+z physics_bridge: front~ | FUNCTION-ONLY | key:state |
| ⊚ | RSC | `bridges/mandala-compute-bridge.json:24` | 60b13b2 2026-03-27 | function: state: 5 label: -z mandala_glyph: octahedron.-z physics_bridge: back ~ | FUNCTION-ONLY | key:state |
| ⊛ | RSC | `bridges/mandala-compute-bridge.json:25` | 60b13b2 2026-03-27 | function: state: 6 label: diagonal-a mandala_glyph: octahedron.diag-a physics_b~ | FUNCTION-ONLY | key:state |
| ⊜ | RSC | `bridges/mandala-compute-bridge.json:26` | 60b13b2 2026-03-27 | function: state: 7 label: diagonal-b mandala_glyph: octahedron.diag-b physics_b~ | FUNCTION-ONLY | key:state |
| ∴ | RSC | `bridges/mandala-compute-bridge.json:179` | 60b13b2 2026-03-27 | function: type: FACTORIZATION encoding: bipartite_tensor shape: SHAPE.OCTA fami~ | FUNCTION-ONLY | function-word:factorization |
| ⊨ | RSC | `bridges/mandala-compute-bridge.json:187` | 60b13b2 2026-03-27 | function: type: SAT encoding: clause_graph shape: SHAPE.CUBE families: FAMILY.F~ | FUNCTION-ONLY | function-word:encoding |
| ↺ | RSC | `bridges/mandala-compute-bridge.json:195` | 60b13b2 2026-03-27 | function: type: TSP encoding: ring_topology shape: SHAPE.ICOSA families: FAMILY~ | FUNCTION-ONLY | function-word:encoding |
| ◉ | RSC | `bridges/mandala-compute-bridge.json:203` | 60b13b2 2026-03-27 | function: type: GRAPH_COLORING encoding: adjacency_map shape: SHAPE.ICOSA famil~ | FUNCTION-ONLY | function-word:encoding |
| ∇ | RSC | `bridges/mandala-compute-bridge.json:211` | 60b13b2 2026-03-27 | process: type: OPTIMIZATION encoding: direct_landscape shape: SHAPE.DODECA fami~ | PHYSICS-ANCHORED | physics-word:gradient |
| ⚖🧭 | RSC | `bridges/rosetta-bridges.json:25` | 7d9482e 2026-03-24 | function: sensor: admiration defense: def.ap.07 + def.ap.08 note: authentic adm~ | FUNCTION-ONLY | key:sensor |
| 🌱⚖ | RSC | `bridges/rosetta-bridges.json:25` | 7d9482e 2026-03-24 | function: sensor: trust defense: def.fr.06 note: authentic trust stabilizes; ma~ | FUNCTION-ONLY | key:sensor |
| 🛡⏳ | RSC | `bridges/rosetta-bridges.json:39` | 7d9482e 2026-03-24 | function: sensor: fear defense: def.bi.04 + def.pr.05 note: authentic fear prep~ | FUNCTION-ONLY | key:sensor |
| 🔄🕸 | RSC | `bridges/rosetta-bridges.json:122` | 7d9482e 2026-03-24 | function: sensor: longing defense: def.pr.02 note: authentic longing senses pos~ | FUNCTION-ONLY | key:sensor |
| 🔍🌀 | RSC | `bridges/rosetta-bridges.json:124` | c1ce552 2026-03-27 | function: sensor: curiosity defense: def.fr.03 + def.de.12 note: authentic curi~ | FUNCTION-ONLY | key:sensor |
| ⬇️🔗 | RSC | `bridges/rosetta-bridges.json:125` | c1ce552 2026-03-27 | function: sensor: shame defense: def.ap.08 note: authentic shame signals contra~ | FUNCTION-ONLY | key:sensor |
| ⏱️🔥 | RSC | `bridges/rosetta-bridges.json:126` | c1ce552 2026-03-27 | function: sensor: pressure defense: def.pr.05 note: authentic pressure prioriti~ | FUNCTION-ONLY | key:sensor |
| 🌀◑ | RSC | `bridges/rosetta-bridges.json:127` | c1ce552 2026-03-27 | function: sensor: confusion defense: def.fr.10 note: authentic confusion holds ~ | FUNCTION-ONLY | key:sensor |
| ⬇️ | RSC | `bridges/taf-wiring-bridge.json:40` | 4bd2e1b 2026-03-27 | function: sensor: shame mechanism: Useful signals suppressed — the system's sha~ | FUNCTION-ONLY | key:sensor |
| 👑 | RSC | `bridges/taf-wiring-bridge.json:81` | 4bd2e1b 2026-03-27 | function: sensor: dignity mechanism: Dignity violation — autonomy of knowledgea~ | FUNCTION-ONLY | key:sensor |
| 🍃 | RSC | `bridges/taf-wiring-bridge.json:142` | 4bd2e1b 2026-03-27 | function: sensor: contentment mechanism: Inverted contentment — comfort maintai~ | FUNCTION-ONLY | key:sensor |
| 🏅 | RSC | `bridges/taf-wiring-bridge.json:143` | 4bd2e1b 2026-03-27 | function: sensor: pride mechanism: Corrupted pride — energy spent appearing pro~ | FUNCTION-ONLY | key:sensor |
| ↧ | RSC | `data/interaction_ontology.json:7` | 5c6e34c 2025-07-24 | function: name: DRILL description: Decompose or dive recursively into structure~ | FUNCTION-ONLY | function-word:decompose |
| ⊕ | RSC | `data/interaction_ontology.json:13` | 5c6e34c 2025-07-24 | function: name: FUSE description: Merge two compatible forms into one type: mer~ | FUNCTION-ONLY | function-word:merge |
| ↑ | RSC | `data/interaction_ontology.json:19` | 5c6e34c 2025-07-24 | none: name: AMPLIFY description: Scale pattern upward with preserved structure ~ | NOT_INTERPRETABLE | label-only |
| φ | RSC | `data/math_constants.json:4` | 39672e2 2025-07-24 | process: name: Golden Ratio value: 1.618034 meaning: Natural harmony, growth sp~ | PHYSICS-ANCHORED | physics-word:golden ratio |
| π | RSC | `data/math_constants.json:10` | 39672e2 2025-07-24 | process: name: Pi value: 3.14159 meaning: Circular harmony, waveforms | PHYSICS-ANCHORED | physics-word:waveforms |
| 🐟 | RSC | `data/sacred_geometry.json:8` | 287d58f 2025-07-24 | process: code: VESICA name: Vesica Piscis meaning: Intersection portal, cellula~ | PHYSICS-ANCHORED | physics-word:resonance |
| △ | RSC | `data/shape_ontology.json:4` | 49b5a71 2025-07-24 | process: name: Triangle code: TRI dimension: 2 physics_mapping: stability_tenso~ | PHYSICS-ANCHORED | physics-word:resonance |
| ⬢ | RSC | `data/shape_ontology.json:14` | 49b5a71 2025-07-24 | process: name: Hexagon code: HEX dimension: 2 physics_mapping: optimal_packing ~ | PHYSICS-ANCHORED | physics-word:resonance |
| 💎 | RSC | `data/temporal_states.json:6` | dc2d582 2025-07-24 | none: name: CRYSTALLIZED type: Memory meaning: Deep pattern storage, sediment o~ | NOT_INTERPRETABLE | label-only |
| 🌀 | RSC | `data/temporal_states.json:12` | dc2d582 2025-07-24 | none: name: FOLD type: Present meaning: The now — possibility into actuality | NOT_INTERPRETABLE | label-only |
| ↻ | RSC | `data/tri_invert_bridge.glyphs.json:4` | 9f16a0b 2025-09-02 | none: meaning: phase-shift / melt | NOT_INTERPRETABLE | label-only |
| ⚖ | RSC | `data/tri_invert_bridge.glyphs.json:5` | 9f16a0b 2025-09-02 | function: meaning: balance / bidirectional mapping | FUNCTION-ONLY | function-word:mapping |
| 🕸 | RSC | `data/tri_invert_bridge.glyphs.json:6` | 9f16a0b 2025-09-02 | function: meaning: field lattice / routing mesh | FUNCTION-ONLY | function-word:routing |
| ⚖ | RSC | `ontology/access/a01-narrative-constraint.json:7` | 938bb4a 2026-08-24 | process: id: a01 rosetta_id: ACCESS.A01 name: narrative-constraint tier: access~ | PHYSICS-ANCHORED | formula-text |
| ≡≡≡ | RSC | `ontology/families/f01-resonance.json:4` | 9fd1069 2026-03-25 | process: id: FAMILY.F01 name: Resonance five_field: chemical domain: Harmonics,~ | PHYSICS-ANCHORED | formula-text |
| ↻ | RSC | `ontology/families/f02-flow.json:4` | 9fd1069 2026-03-25 | process: id: FAMILY.F02 name: Flow five_field: chemical domain: Fluid motion, l~ | PHYSICS-ANCHORED | formula-text |
| ⊗ | RSC | `ontology/families/f03-information.json:4` | 9fd1069 2026-03-25 | process: id: FAMILY.F03 name: Information five_field: chemical domain: Shannon ~ | PHYSICS-ANCHORED | formula-text |
| •••• | RSC | `ontology/families/f04-life.json:4` | 9fd1069 2026-03-25 | process: id: FAMILY.F04 name: Life five_field: chemical domain: Population dyna~ | PHYSICS-ANCHORED | formula-text |
| △≈ | RSC | `ontology/families/f05-energy-thermo.json:4` | 9fd1069 2026-03-25 | process: id: FAMILY.F05 name: Energy-Thermo five_field: emotional domain: Heat ~ | PHYSICS-ANCHORED | formula-text |
| ⋯⋯ | RSC | `ontology/families/f06-cognition.json:4` | 9fd1069 2026-03-25 | process: id: FAMILY.F06 name: Cognition five_field: emotional domain: Neural dy~ | PHYSICS-ANCHORED | formula-text |
| ◯ | RSC | `ontology/families/f07-earth-cosmos.json:4` | 9fd1069 2026-03-25 | process: id: FAMILY.F07 name: Earth-Cosmos five_field: emotional domain: Planet~ | PHYSICS-ANCHORED | formula-text |
| ◆ | RSC | `ontology/families/f08-matter.json:4` | 9fd1069 2026-03-25 | process: id: FAMILY.F08 name: Matter five_field: emotional domain: Phase transi~ | PHYSICS-ANCHORED | formula-text |
| ☆ | RSC | `ontology/families/f09-geometry.json:4` | 9fd1069 2026-03-25 | process: id: FAMILY.F09 name: Geometry five_field: cognitive domain: Euclidean ~ | PHYSICS-ANCHORED | formula-text |
| ⚪ | RSC | `ontology/families/f10-particle.json:4` | 9fd1069 2026-03-25 | process: id: FAMILY.F10 name: Particle five_field: cognitive domain: Standard M~ | PHYSICS-ANCHORED | formula-text |
| ⚙ | RSC | `ontology/families/f11-engineering.json:4` | 9fd1069 2026-03-25 | process: id: FAMILY.F11 name: Engineering five_field: cognitive domain: Stress/~ | PHYSICS-ANCHORED | formula-text |
| ⬡ | RSC | `ontology/families/f12-networks.json:4` | 9fd1069 2026-03-25 | process: id: FAMILY.F12 name: Networks five_field: dream domain: Graph theory, ~ | PHYSICS-ANCHORED | formula-text |
| ⇑ | RSC | `ontology/families/f13-reaction.json:4` | 9fd1069 2026-03-25 | process: id: FAMILY.F13 name: Reaction five_field: dream domain: Chemical kinet~ | PHYSICS-ANCHORED | formula-text |
| ↕ | RSC | `ontology/families/f14-measurement.json:4` | 9fd1069 2026-03-25 | process: id: FAMILY.F14 name: Measurement five_field: dream domain: Uncertainty~ | PHYSICS-ANCHORED | formula-text |
| ◆→ | RSC | `ontology/families/f15-navigation.json:4` | 9fd1069 2026-03-25 | process: id: FAMILY.F15 name: Navigation five_field: dream domain: Geodesics, o~ | PHYSICS-ANCHORED | formula-text |
| ◎ | RSC | `ontology/families/f16-consciousness.json:4` | 9fd1069 2026-03-25 | process: id: FAMILY.F16 name: Consciousness five_field: dream domain: Integrate~ | PHYSICS-ANCHORED | formula-text |
| ᘯᘰ | RSC | `ontology/families/f17-turbulence.json:4` | 9fd1069 2026-03-25 | process: id: FAMILY.F17 name: Turbulence five_field: dream domain: Chaos, sensi~ | PHYSICS-ANCHORED | formula-text |
| ⊗≡ | RSC | `ontology/families/f18-relativity.json:4` | 9fd1069 2026-03-25 | process: id: FAMILY.F18 name: Relativity five_field: symbolic domain: Spacetime~ | PHYSICS-ANCHORED | formula-text |
| ▁▃▅∿ | RSC | `ontology/families/f19-statistical.json:4` | 9fd1069 2026-03-25 | process: id: FAMILY.F19 name: Statistical five_field: symbolic domain: Statisti~ | PHYSICS-ANCHORED | formula-text |
| ∞ | RSC | `ontology/families/f20-topology.json:4` | 9fd1069 2026-03-25 | process: id: FAMILY.F20 name: Topology five_field: symbolic domain: Topological~ | PHYSICS-ANCHORED | formula-text |
| ≡≡≡ | RSC | `ontology/index.json:44` | 9fd1069 2026-03-25 | process: id: FAMILY.F01 name: Resonance file: ontology/families/f01-resonance.j~ | PHYSICS-ANCHORED | physics-word:resonance |
| ↻ | RSC | `ontology/index.json:51` | 9fd1069 2026-03-25 | none: id: FAMILY.F02 name: Flow file: ontology/families/f02-flow.json seed: Flu~ | NOT_INTERPRETABLE | label-only |
| ⊗ | RSC | `ontology/index.json:58` | 9fd1069 2026-03-25 | process: id: FAMILY.F03 name: Information file: ontology/families/f03-informati~ | PHYSICS-ANCHORED | physics-word:entropy |
| •••• | RSC | `ontology/index.json:65` | 9fd1069 2026-03-25 | none: id: FAMILY.F04 name: Life file: ontology/families/f04-life.json seed: Pop~ | NOT_INTERPRETABLE | label-only |
| △≈ | RSC | `ontology/index.json:72` | 9fd1069 2026-03-25 | process: id: FAMILY.F05 name: Energy-Thermo file: ontology/families/f05-energy-~ | PHYSICS-ANCHORED | physics-word:energy |
| ⋯⋯ | RSC | `ontology/index.json:79` | 9fd1069 2026-03-25 | process: id: FAMILY.F06 name: Cognition file: ontology/families/f06-cognition.j~ | PHYSICS-ANCHORED | physics-word:gradient |
| ◯ | RSC | `ontology/index.json:86` | 9fd1069 2026-03-25 | process: id: FAMILY.F07 name: Earth-Cosmos file: ontology/families/f07-earth-co~ | PHYSICS-ANCHORED | physics-word:gravity |
| ◆ | RSC | `ontology/index.json:93` | 9fd1069 2026-03-25 | function: id: FAMILY.F08 name: Matter file: ontology/families/f08-matter.json s~ | FUNCTION-ONLY | function-word:transitions |
| ☆ | RSC | `ontology/index.json:100` | 9fd1069 2026-03-25 | none: id: FAMILY.F09 name: Geometry file: ontology/families/f09-geometry.json s~ | NOT_INTERPRETABLE | label-only |
| ⚪ | RSC | `ontology/index.json:107` | 9fd1069 2026-03-25 | none: id: FAMILY.F10 name: Particle file: ontology/families/f10-particle.json s~ | NOT_INTERPRETABLE | label-only |
| ⚙ | RSC | `ontology/index.json:114` | 9fd1069 2026-03-25 | none: id: FAMILY.F11 name: Engineering file: ontology/families/f11-engineering.~ | NOT_INTERPRETABLE | label-only |
| ⬡ | RSC | `ontology/index.json:121` | 9fd1069 2026-03-25 | none: id: FAMILY.F12 name: Networks file: ontology/families/f12-networks.json s~ | NOT_INTERPRETABLE | label-only |
| ⇑ | RSC | `ontology/index.json:128` | 9fd1069 2026-03-25 | process: id: FAMILY.F13 name: Reaction file: ontology/families/f13-reaction.jso~ | PHYSICS-ANCHORED | physics-word:energy |
| ↕ | RSC | `ontology/index.json:135` | 9fd1069 2026-03-25 | function: id: FAMILY.F14 name: Measurement file: ontology/families/f14-measurem~ | FUNCTION-ONLY | function-word:measurement |
| ◆→ | RSC | `ontology/index.json:142` | 9fd1069 2026-03-25 | function: id: FAMILY.F15 name: Navigation file: ontology/families/f15-navigatio~ | FUNCTION-ONLY | function-word:filter |
| ◎ | RSC | `ontology/index.json:149` | 9fd1069 2026-03-25 | process: id: FAMILY.F16 name: Consciousness file: ontology/families/f16-conscio~ | PHYSICS-ANCHORED | physics-word:energy |
| ᘯᘰ | RSC | `ontology/index.json:156` | 9fd1069 2026-03-25 | none: id: FAMILY.F17 name: Turbulence file: ontology/families/f17-turbulence.js~ | NOT_INTERPRETABLE | label-only |
| ⊗≡ | RSC | `ontology/index.json:163` | 9fd1069 2026-03-25 | process: id: FAMILY.F18 name: Relativity file: ontology/families/f18-relativity~ | PHYSICS-ANCHORED | physics-word:gravitational |
| ⊗ | RSC | `ontology/index.json:163` | 9fd1069 2026-03-25 | none: id: PRINCIPLE.P03 name: Relativity file: ontology/principles/p03-relativi~ | NOT_INTERPRETABLE | label-only |
| ▁▃▅∿ | RSC | `ontology/index.json:170` | 9fd1069 2026-03-25 | process: id: FAMILY.F19 name: Statistical file: ontology/families/f19-statistic~ | PHYSICS-ANCHORED | physics-word:boltzmann |
| ∿ | RSC | `ontology/index.json:170` | 9fd1069 2026-03-25 | process: id: PRINCIPLE.P06 name: Resonance file: ontology/principles/p06-resona~ | PHYSICS-ANCHORED | physics-word:resonance |
| ∞ | RSC | `ontology/index.json:177` | 9fd1069 2026-03-25 | none: id: FAMILY.F20 name: Topology file: ontology/families/f20-topology.json s~ | NOT_INTERPRETABLE | label-only |
| ⧖ | RSC | `ontology/index.json:228` | 9fd1069 2026-03-25 | none: id: PRINCIPLE.P01 name: Symmetry file: ontology/principles/p01-symmetry.j~ | NOT_INTERPRETABLE | label-only |
| ↺ | RSC | `ontology/index.json:235` | 9fd1069 2026-03-25 | process: id: PRINCIPLE.P02 name: Conservation file: ontology/principles/p02-con~ | PHYSICS-ANCHORED | physics-word:conservation |
| ◑ | RSC | `ontology/index.json:249` | 9fd1069 2026-03-25 | process: id: PRINCIPLE.P04 name: Duality file: ontology/principles/p04-duality.~ | PHYSICS-ANCHORED | physics-word:wave |
| ●● | RSC | `ontology/index.json:256` | 9fd1069 2026-03-25 | none: id: PRINCIPLE.P05 name: Emergence file: ontology/principles/p05-emergence~ | NOT_INTERPRETABLE | label-only |
| ⎯ | RSC | `ontology/index.json:270` | 9fd1069 2026-03-25 | process: id: PRINCIPLE.P07 name: Continuity file: ontology/principles/p07-conti~ | PHYSICS-ANCHORED | physics-word:conservation |
| ▭ | RSC | `ontology/index.json:277` | 9fd1069 2026-03-25 | process: id: PRINCIPLE.P08 name: Quantization file: ontology/principles/p08-qua~ | PHYSICS-ANCHORED | physics-word:planck |
| ▯ | RSC | `ontology/index.json:284` | 9fd1069 2026-03-25 | process: id: PRINCIPLE.P09 name: Proportion file: ontology/principles/p09-propo~ | PHYSICS-ANCHORED | physics-word:golden ratio |
| ◧ | RSC | `ontology/index.json:291` | 9fd1069 2026-03-25 | process: id: PRINCIPLE.P10 name: Uncertainty file: ontology/principles/p10-unce~ | PHYSICS-ANCHORED | physics-word:entropy |
| ↻ | RSC | `ontology/index.json:298` | 9fd1069 2026-03-25 | process: id: PRINCIPLE.P11 name: Transformation file: ontology/principles/p11-t~ | PHYSICS-ANCHORED | physics-word:fourier |
| ◎ | RSC | `ontology/index.json:305` | 9fd1069 2026-03-25 | process: id: PRINCIPLE.P12 name: Unity file: ontology/principles/p12-unity.json~ | PHYSICS-ANCHORED | formula-text |
| ⧖ | RSC | `ontology/principles/p01-symmetry.json:4` | 9fd1069 2026-03-25 | process: id: PRINCIPLE.P01 name: Symmetry dodecahedron_face: 1 domain: Group th~ | PHYSICS-ANCHORED | formula-text |
| ↺ | RSC | `ontology/principles/p02-conservation.json:4` | 9fd1069 2026-03-25 | process: id: PRINCIPLE.P02 name: Conservation dodecahedron_face: 2 domain: Ener~ | PHYSICS-ANCHORED | formula-text |
| ⊗ | RSC | `ontology/principles/p03-relativity.json:4` | 9fd1069 2026-03-25 | process: id: PRINCIPLE.P03 name: Relativity dodecahedron_face: 3 domain: Lorent~ | PHYSICS-ANCHORED | formula-text |
| ◑ | RSC | `ontology/principles/p04-duality.json:4` | 9fd1069 2026-03-25 | process: id: PRINCIPLE.P04 name: Duality dodecahedron_face: 4 domain: Wave-part~ | PHYSICS-ANCHORED | formula-text |
| ●● | RSC | `ontology/principles/p05-emergence.json:4` | 9fd1069 2026-03-25 | process: id: PRINCIPLE.P05 name: Emergence dodecahedron_face: 5 domain: Cellula~ | PHYSICS-ANCHORED | formula-text |
| ∿ | RSC | `ontology/principles/p06-resonance.json:4` | 9fd1069 2026-03-25 | process: id: PRINCIPLE.P06 name: Resonance dodecahedron_face: 6 domain: Resonan~ | PHYSICS-ANCHORED | formula-text |
| ⎯ | RSC | `ontology/principles/p07-continuity.json:4` | 9fd1069 2026-03-25 | process: id: PRINCIPLE.P07 name: Continuity dodecahedron_face: 7 domain: Conser~ | PHYSICS-ANCHORED | formula-text |
| ▭ | RSC | `ontology/principles/p08-quantization.json:4` | 9fd1069 2026-03-25 | process: id: PRINCIPLE.P08 name: Quantization dodecahedron_face: 8 domain: Disc~ | PHYSICS-ANCHORED | formula-text |
| ▯ | RSC | `ontology/principles/p09-proportion.json:4` | 9fd1069 2026-03-25 | process: id: PRINCIPLE.P09 name: Proportion dodecahedron_face: 9 domain: Golden~ | PHYSICS-ANCHORED | formula-text |
| ◧ | RSC | `ontology/principles/p10-uncertainty.json:4` | 9fd1069 2026-03-25 | process: id: PRINCIPLE.P10 name: Uncertainty dodecahedron_face: 10 domain: Heis~ | PHYSICS-ANCHORED | formula-text |
| ↻ | RSC | `ontology/principles/p11-transformation.json:4` | 9fd1069 2026-03-25 | process: id: PRINCIPLE.P11 name: Transformation dodecahedron_face: 11 domain: F~ | PHYSICS-ANCHORED | formula-text |
| ◎ | RSC | `ontology/principles/p12-unity.json:4` | 9fd1069 2026-03-25 | process: id: PRINCIPLE.P12 name: Unity dodecahedron_face: 12 domain: Unificatio~ | PHYSICS-ANCHORED | formula-text |
| ↻ | RSC | `recursion.json:3` | 94f1bcb 2025-09-29 | process: pattern_id: PATTERN:RECURSION layers: symbolic: glyph: ↻ meaning: self~ | PHYSICS-ANCHORED | physics-word:energy_pattern |
| ↻ | RSC | `recursion.json:6` | 94f1bcb 2025-09-29 | none: meaning: self-referential return and feedback bloom_behavior: feedback_lo~ | NOT_INTERPRETABLE | label-only |
| 🕸️ | RSC | `shapes/relief.json:19` | df1a8a8 2026-03-26 | process: source_repo: Emotions-as-Sensors source_file: bridges/field_events/fel~ | PHYSICS-ANCHORED | formula-text |
| ⊕ | RSC | `src/rosetta_shape_core/_sensors.py:42` | c90d943 2026-04-01 | function: state: 0 bits: 000 pad: P+ A- D+ label: contentment/peace description~ | FUNCTION-ONLY | key:bits,state |
| ⊖ | RSC | `src/rosetta_shape_core/_sensors.py:43` | c90d943 2026-04-01 | function: state: 1 bits: 001 pad: P- A- D- label: shame/withdrawal description:~ | FUNCTION-ONLY | key:bits,state |
| ⊗ | RSC | `src/rosetta_shape_core/_sensors.py:44` | c90d943 2026-04-01 | function: state: 2 bits: 010 pad: P+ A+ D+ label: excitement/mastery descriptio~ | FUNCTION-ONLY | key:bits,state |
| ⊘ | RSC | `src/rosetta_shape_core/_sensors.py:45` | c90d943 2026-04-01 | function: state: 3 bits: 011 pad: P- A+ D- label: anger/pressure description: B~ | FUNCTION-ONLY | key:bits,state |
| ⊙ | RSC | `src/rosetta_shape_core/_sensors.py:46` | c90d943 2026-04-01 | function: state: 4 bits: 100 pad: P+ A+ D- label: curiosity/vigilance descripti~ | FUNCTION-ONLY | key:bits,state |
| ⊚ | RSC | `src/rosetta_shape_core/_sensors.py:47` | c90d943 2026-04-01 | function: state: 5 bits: 101 pad: P- A- D+ label: fatigue/resignation descripti~ | FUNCTION-ONLY | key:bits,state |
| ⊛ | RSC | `src/rosetta_shape_core/_sensors.py:48` | c90d943 2026-04-01 | function: state: 6 bits: 110 pad: P~ A~ D~ label: confusion/superposition descr~ | FUNCTION-ONLY | key:bits,state |
| ⊜ | RSC | `src/rosetta_shape_core/_sensors.py:49` | c90d943 2026-04-01 | function: state: 7 bits: 111 pad: P+ A- D- label: coherence/equilibrium descrip~ | FUNCTION-ONLY | key:bits,state |
