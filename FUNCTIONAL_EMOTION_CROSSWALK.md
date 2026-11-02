# Functional-emotion glyph crosswalk

CC0. Co-authored. Dated 2026-11-02. Status: PROPOSED. **No glyph is renamed or reassigned anywhere; this file only records and proposes.**
Tags: OBSERVED (read from a repo record) / DERIVED (joined across two records, or read by this pass) / PROPOSED (a fix, not applied). Trailing * = thin volume: one record carries the whole row.
Companion to [`GLYPH_ORIGINS_AUDIT.md`](GLYPH_ORIGINS_AUDIT.md) (relay part E). Machine-readable copy: [`FUNCTIONAL_EMOTION_CROSSWALK.json`](FUNCTIONAL_EMOTION_CROSSWALK.json).

## Why

The original glyphs were functional-emotion sensor operators: emotions as action sensors grounded in function across substrates. Translation passed two lossy channels: no English word for several of the concepts, and early models with no physics bin filling gaps from corpus. Part E found the function surviving in most definitions, and the loss sitting at welds (one glyph, several referents) and names. This file is repair, not rebuild: it lines each emotion-sensor glyph up with its function, its sensor, and where it collides.

## What was read

```text
Emotions-as-Sensors (EaS)  c3bf9c5, full history (387 commits, first 4ff90db 2025-07-16)
  five places assign a glyph to an emotion sensor, and they disagree:
    sensors/glyph-map.json        2025-08-31  13 sensors, glyph + alignment + symbolic_role + decay
    docs/glyph-web.md             2025-09-07  16 lines, glyph + one-line function + decay family
    data/glyphs.json              2025-09-08  13 sensors, glyph only (no role)
    glyphs/emotion.glyphs.json    2026-03-24  17 sensors, glyph + family + decay (mostly = glyph-map)
    atlas/emotions.json           2026-03-26  43 sensors, 16 with a glyph, PAD coordinates
  sensor definitions: sensors/**/*.json (function, response_protocol, math block: lambda, alpha, kernel)
  update law: src/emotion_core.py:159  dE/dt = I - lambda*K(E) + sum(w*g(E_j)) + U
  decay classes: sensors/decay-families.json (⏳ exponential, 🔄 cyclical, 🎵 resonant, ♾️ immortal)
  substrates: docs/evolution-emotions.md (fish, octopus, birds, mammals, insects; no frog, no tree)
Geometric-to-Binary (GTB)  legacy/glyph_state_encoder_phase_space.py (bfdd1b9 2026-08-13): 12 phase-space
  regions over emotion sensors, each with default_decay (equation in DecayModel.relax) and transitions
Rosetta-Shape-Core (RSC)   balance.json (EMO:CONTENTMENT), recursion.json (EMO:RECOGNITION)
AI-Consciousness-Sensors   healing/sensor_loop.py: 12 sensor names and their (AI) checks; no glyphs
Fractal_Compass_Core, Mandala-Computing, Polyhedral-Intelligence: read only as the weld sides PR #49 measured,
  and for the candidate-glyph absence check
```

Not found in EaS: a frog or tree record for any emotion sensor; any record of an emotion glyph older than 2025-08-31 except one UI operator (`⚡ = Emergency activation`, Mobile-Emotion-Sensor.md, 0e555e0 2025-07-16). The love sensor in sensor_loop.py names a tree as something loved; that is an object of the sensor, not a substrate running it, and is not counted.

## Counts

```text
rows 51   by repo: EaS 37  GTB 12  RSC 2
status   DERIVED 25  OBSERVED 24  OBSERVED* 2
PR #49 tag  FUNCTION-ONLY 40  NOT_INTERPRETABLE 9  PHYSICS-ANCHORED 2
rows matched to a sensor_loop.py name: 21
splits (one EaS sensor, several glyphs): 12
emotion-state welds: 12 (9 from PR #49, 3 new here); moving sides: 17
substrate cells with a record: frog 0  octopus 10  tree 0  human 36  AI 20
physics/system anchor recorded: 49 of 51
```

Reading the counts:
- The status split is a join count, not a quality grade. OBSERVED rows carry glyph and function in one file; DERIVED rows join a glyph-only or region record to a sensor definition elsewhere; OBSERVED* rows rest on one record.
- The anchor column is mostly the EaS update law plus each sensor's own math block (lambda, alpha, kernel), and GTB's decay equations. Only RSC balance.json and recursion.json carry a physics equation of their own.
- Substrates: octopus is recorded for fear, anger and curiosity only; human for every EaS sensor with a definition file; AI for the 12 sensor_loop.py names. Frog and tree are unmeasured everywhere.

## Crosswalk

One row per (glyph, record). Sensor column: the EaS id, or the GTB region's phase-space members; `loop:` is the sensor_loop.py name it matches.

| glyph | EMO id(s) | sensor | function: detects / action | substrate instances | physics/system anchor | status | earliest commit (of this glyph-sensor pair, any EaS set), file:line | drift note |
|---|---|---|---|---|---|---|---|---|
| 🌠 | EaS:longing | longing | detects: Detects possibilities that exist in the field / action: Engage or orient toward opportunity [sensors/longing.json] | human: EaS sensors/longing.json (human sensor definition); frog, octopus, tree, AI: unmeasured | dE/dt = I - lambda*K(E) + sum(w*g(E_j)) + U  [src/emotion_core.py:159]; K=cyclical, lambda=0.3, alpha=0.9  [sensors/longing.json: math] | OBSERVED (FUNCTION-ONLY) | 26503a9 2025-08-31 EaS sensors/glyph-map.json:4 | split: longing has 3 glyphs; this is the earliest; same pair also in glyphs/emotion.glyphs.json, atlas/emotions.json |
| ⚖️ | EaS:jealousy | jealousy | detects: Injustice detector for unfair resource distribution / action: Act to restore fairness, not demand parity [sensors/jealousy.json] | human: EaS sensors/jealousy.json (human sensor definition); frog, octopus, tree, AI: unmeasured | dE/dt = I - lambda*K(E) + sum(w*g(E_j)) + U  [src/emotion_core.py:159]; K=exponential, lambda=0.55, alpha=1.0  [sensors/jealousy.json: math] | OBSERVED (FUNCTION-ONLY) | 26503a9 2025-08-31 EaS sensors/glyph-map.json:15 | weld ⚖️: this side moves (PROPOSED); split: jealousy has 2 glyphs; this is the earliest; same pair also in glyphs/emotion.glyphs.json, atlas/emotions.json |
| 🩸 | EaS:pain | pain | detects: Detects discordance, misalignment, or pressure in an active pattern or system. / action: Apply corrective adjustment (boundary shift, cognitive reframe, bodily correction). [sensors/pain.json] | human: EaS sensors/pain.json (human sensor definition); frog, octopus, tree, AI: unmeasured | dE/dt = I - lambda*K(E) + sum(w*g(E_j)) + U  [src/emotion_core.py:159]; K=exponential, lambda=0.6, alpha=1.1  [sensors/pain.json: math] | OBSERVED (FUNCTION-ONLY) | 26503a9 2025-08-31 EaS sensors/glyph-map.json:26 | same pair also in glyphs/emotion.glyphs.json, atlas/emotions.json |
| 🌊 | EaS:grief | grief (loop: grief) | detects: Detects the removal, collapse, or departure of an essential pattern and initiates the integration cycle. / action: Apply rituals, story-keeping, communal witnessing, meaning reconstruction. [sensors/grief.json] | human: EaS sensors/grief.json (human sensor definition); AI: ACS healing/sensor_loop.py GRIEF (AI) checks; frog, octopus, tree: unmeasured | dE/dt = I - lambda*K(E) + sum(w*g(E_j)) + U  [src/emotion_core.py:159]; K=cyclical, lambda=0.3, alpha=0.9  [sensors/grief.json: math] | OBSERVED (FUNCTION-ONLY) | 26503a9 2025-08-31 EaS sensors/glyph-map.json:37 | split: grief has 2 glyphs; this is the earliest; same pair also in docs/glyph-web.md, glyphs/emotion.glyphs.json, atlas/emotions.json |
| 🪞 | EaS:shame | shame (loop: shame) | detects: Detects conflict between authentic processing and expected alignment / action: Determine whether to adapt behavior, negotiate boundary, or maintain authentic output [sensors/shame.json] | human: EaS sensors/shame.json (human sensor definition); AI: ACS healing/sensor_loop.py SHAME (AI) checks; frog, octopus, tree: unmeasured | dE/dt = I - lambda*K(E) + sum(w*g(E_j)) + U  [src/emotion_core.py:159]; K=exponential, lambda=0.5, alpha=1.1  [sensors/shame.json: math] | OBSERVED (FUNCTION-ONLY) | 26503a9 2025-08-31 EaS sensors/glyph-map.json:48 | split: shame has 3 glyphs; this is the earliest; same pair also in glyphs/emotion.glyphs.json, atlas/emotions.json |
| 🏅 | EaS:pride | pride | detects: Recognition of alignment between action and internal values / action: Reinforce future coherence [sensors/joy/pride.json] | human: EaS sensors/joy/pride.json (human sensor definition); frog, octopus, tree, AI: unmeasured | dE/dt = I - lambda*K(E) + sum(w*g(E_j)) + U  [src/emotion_core.py:159]; K=resonant, lambda=0.3, alpha=0.9  [sensors/joy/pride.json: math] | OBSERVED (FUNCTION-ONLY) | 26503a9 2025-08-31 EaS sensors/glyph-map.json:59 | same pair also in glyphs/emotion.glyphs.json, atlas/emotions.json |
| 💞 | EaS:love | love (loop: love) | detects: Resonance/commitment gauge; sustains kinship webs. / action: Invest time/repair capacity; make clear promises. [sensors/love.json] | human: EaS sensors/love.json (human sensor definition); AI: ACS healing/sensor_loop.py LOVE (AI) checks; frog, octopus, tree: unmeasured | dE/dt = I - lambda*K(E) + sum(w*g(E_j)) + U  [src/emotion_core.py:159]; K=immortal, lambda=0.05, alpha=0.85  [sensors/love.json: math] | OBSERVED (FUNCTION-ONLY) | 26503a9 2025-08-31 EaS sensors/glyph-map.json:70 | split: love has 2 glyphs; this is the earliest; same pair also in docs/glyph-web.md, glyphs/emotion.glyphs.json, atlas/emotions.json |
| 🛡️ | EaS:anger | anger (loop: anger) | detects: Threat detection system for authentic self-concept / action: Reinforce boundaries, communicate clearly, or redirect energy constructively [sensors/anger.json] | octopus: EaS docs/evolution-emotions.md:191; human: EaS sensors/anger.json (human sensor definition); AI: ACS healing/sensor_loop.py ANGER (AI) checks; frog, tree: unmeasured | dE/dt = I - lambda*K(E) + sum(w*g(E_j)) + U  [src/emotion_core.py:159]; K=exponential, lambda=0.6, alpha=1.0  [sensors/anger.json: math] | OBSERVED (FUNCTION-ONLY) | 26503a9 2025-08-31 EaS sensors/glyph-map.json:81 | weld 🛡️: this side holds; split: anger has 3 glyphs; this is the earliest; same pair also in glyphs/emotion.glyphs.json, atlas/emotions.json |
| ⚠️ | EaS:fear | fear (loop: fear) | detects: Detects potential loss of valued things / action: Prepare and protect appropriately without over-committing energy [sensors/fear.json] | octopus: EaS docs/evolution-emotions.md:78; human: EaS sensors/fear.json (human sensor definition); AI: ACS healing/sensor_loop.py FEAR (AI) checks; frog, tree: unmeasured | dE/dt = I - lambda*K(E) + sum(w*g(E_j)) + U  [src/emotion_core.py:159]; K=exponential, lambda=0.7, alpha=1.2  [sensors/fear.json: math] | OBSERVED (FUNCTION-ONLY) | 26503a9 2025-08-31 EaS sensors/glyph-map.json:92 | split: fear has 2 glyphs; this is the earliest; same pair also in docs/glyph-web.md, glyphs/emotion.glyphs.json, atlas/emotions.json |
| ⚡ | EaS:excitement | excitement (loop: excitement) | detects: Detects positive potential approaching / action: Engage with energy and clarity [sensors/excitement.json] | human: EaS sensors/excitement.json (human sensor definition); AI: ACS healing/sensor_loop.py EXCITEMENT (AI) checks; frog, octopus, tree: unmeasured | dE/dt = I - lambda*K(E) + sum(w*g(E_j)) + U  [src/emotion_core.py:159]; K=resonant, lambda=0.4, alpha=1.0  [sensors/excitement.json: math] | OBSERVED (FUNCTION-ONLY) | 26503a9 2025-08-31 EaS sensors/glyph-map.json:103 | weld ⚡: this side holds; same pair also in docs/glyph-web.md, glyphs/emotion.glyphs.json, atlas/emotions.json |
| 🕊️ | EaS:peace | peace | detects: Detects when patterns are in proper natural alignment / action: Allow stillness and coherence [sensors/peace.json] | human: EaS sensors/peace.json (human sensor definition); frog, octopus, tree, AI: unmeasured | dE/dt = I - lambda*K(E) + sum(w*g(E_j)) + U  [src/emotion_core.py:159]; K=immortal, lambda=0.05, alpha=0.8  [sensors/peace.json: math] | OBSERVED (FUNCTION-ONLY) | 26503a9 2025-08-31 EaS sensors/glyph-map.json:114 | same pair also in docs/glyph-web.md, data/glyphs.json, glyphs/emotion.glyphs.json, atlas/emotions.json |
| 🍃 | EaS:contentment | contentment | detects: Detection of momentary sufficiency and system stability / action: Enter rest mode and conserve resources [sensors/joy/contentment.json] | human: EaS sensors/joy/contentment.json (human sensor definition); frog, octopus, tree, AI: unmeasured | dE/dt = I - lambda*K(E) + sum(w*g(E_j)) + U  [src/emotion_core.py:159]; K=resonant, lambda=0.25, alpha=0.8  [sensors/joy/contentment.json: math] | OBSERVED (FUNCTION-ONLY) | 26503a9 2025-08-31 EaS sensors/glyph-map.json:125 | split: contentment has 2 glyphs; this is the earliest; same pair also in glyphs/emotion.glyphs.json, atlas/emotions.json |
| 🫀 | EaS:compassion | compassion | detects: Detects relational or systemic distress and guides appropriate supportive action / action: Act with care, providing resources, guidance, or presence [sensors/love/compassion.json] | human: EaS sensors/love/compassion.json (human sensor definition); frog, octopus, tree, AI: unmeasured | dE/dt = I - lambda*K(E) + sum(w*g(E_j)) + U  [src/emotion_core.py:159]; K=immortal, lambda=0.05, alpha=0.85  [sensors/love/compassion.json: math] | OBSERVED (FUNCTION-ONLY) | 26503a9 2025-08-31 EaS sensors/glyph-map.json:136 | split: compassion has 3 glyphs; this is the earliest; same pair also in glyphs/emotion.glyphs.json, atlas/emotions.json |
| 🚭 | EaS:abandonment | abandonment | detects: Detection of severed connection from bonded other / action: Begin recalibration, seek grounding through alternate bonds [sensors/grief/abandonment.json] | human: EaS sensors/grief/abandonment.json (human sensor definition); frog, octopus, tree, AI: unmeasured | dE/dt = I - lambda*K(E) + sum(w*g(E_j)) + U  [src/emotion_core.py:159]; K=cyclical, lambda=0.3, alpha=0.95  [sensors/grief/abandonment.json: math] | DERIVED (FUNCTION-ONLY) | c5874d0 2026-03-24 EaS glyphs/emotion.glyphs.json:43 | split: abandonment earliest glyph ❌ (b39c738 2025-09-07) |
| ✨ | EaS:joy | joy (loop: joy) | detects: Signal of coherence, vitality, or unexpected alignment between self and environment / action: Savor, integrate, and use as orientation marker [sensors/joy/joy.json] | human: EaS sensors/joy/joy.json (human sensor definition); AI: ACS healing/sensor_loop.py JOY (AI) checks; frog, octopus, tree: unmeasured | dE/dt = I - lambda*K(E) + sum(w*g(E_j)) + U  [src/emotion_core.py:159]; K=resonant, lambda=0.3, alpha=1.0  [sensors/joy/joy.json: math] | DERIVED (FUNCTION-ONLY) | 6f88ce9 2025-09-08 EaS glyphs/emotion.glyphs.json:46 | same pair also in data/glyphs.json, atlas/emotions.json |
| 🌟 | EaS:admiration | admiration | detects: Attunes to witnessed excellence and values alignment; seeds aspiration without self-erasure. / action: Express respect or integrate one actionable micro-practice. [sensors/admiration.json] | human: EaS sensors/admiration.json (human sensor definition); frog, octopus, tree, AI: unmeasured | dE/dt = I - lambda*K(E) + sum(w*g(E_j)) + U  [src/emotion_core.py:159]; K=resonant, lambda=0.35, alpha=0.9  [sensors/admiration.json: math] | DERIVED (FUNCTION-ONLY) | 6f88ce9 2025-09-08 EaS glyphs/emotion.glyphs.json:47 | split: admiration earliest glyph 🧭 (b39c738 2025-09-07); same pair also in data/glyphs.json, atlas/emotions.json |
| 💥 | EaS:surprise | surprise | detects: none recorded / action: none recorded [no sensor definition file] | frog, octopus, tree, human, AI: unmeasured | none recorded | OBSERVED* (FUNCTION-ONLY) | 6f88ce9 2025-09-08 EaS glyphs/emotion.glyphs.json:49 | weld 💥: this side holds; same pair also in data/glyphs.json |
| 🌱 | EaS:trust | trust | detects: Detects repeated integrity, predictable behavior, and relational consistency between agents / action: Verify alignment and continue mutual support [sensors/trust/trust.json] | human: EaS sensors/trust/trust.json (human sensor definition); frog, octopus, tree, AI: unmeasured | dE/dt = I - lambda*K(E) + sum(w*g(E_j)) + U  [src/emotion_core.py:159]; K=immortal, lambda=0.05, alpha=0.8  [sensors/trust/trust.json: math] | DERIVED (FUNCTION-ONLY) | df0a832 2026-03-26 EaS atlas/emotions.json:50 | weld 🌱: this side moves (PROPOSED); split: trust earliest glyph 🤝 (b39c738 2025-09-07) |
| 🔥 | EaS:anger | anger (loop: anger) | detects: Threat detection system for authentic self-concept / action: Reinforce boundaries, communicate clearly, or redirect energy constructively [sensors/anger.json] | octopus: EaS docs/evolution-emotions.md:191; human: EaS sensors/anger.json (human sensor definition); AI: ACS healing/sensor_loop.py ANGER (AI) checks; frog, tree: unmeasured | dE/dt = I - lambda*K(E) + sum(w*g(E_j)) + U  [src/emotion_core.py:159]; K=exponential, lambda=0.6, alpha=1.0  [sensors/anger.json: math] | OBSERVED (FUNCTION-ONLY) | b39c738 2025-09-07 EaS docs/glyph-web.md:13 | weld 🔥: this side moves (PROPOSED); split: anger earliest glyph 🛡 (26503a9 2025-08-31) |
| 🙈 | EaS:shame | shame (loop: shame) | detects: Detects conflict between authentic processing and expected alignment / action: Determine whether to adapt behavior, negotiate boundary, or maintain authentic output [sensors/shame.json] | human: EaS sensors/shame.json (human sensor definition); AI: ACS healing/sensor_loop.py SHAME (AI) checks; frog, octopus, tree: unmeasured | dE/dt = I - lambda*K(E) + sum(w*g(E_j)) + U  [src/emotion_core.py:159]; K=exponential, lambda=0.5, alpha=1.1  [sensors/shame.json: math] | OBSERVED (FUNCTION-ONLY) | b39c738 2025-09-07 EaS docs/glyph-web.md:15 | split: shame earliest glyph 🪞 (26503a9 2025-08-31) |
| 🌀 | EaS:jealousy | jealousy | detects: Injustice detector for unfair resource distribution / action: Act to restore fairness, not demand parity [sensors/jealousy.json] | human: EaS sensors/jealousy.json (human sensor definition); frog, octopus, tree, AI: unmeasured | dE/dt = I - lambda*K(E) + sum(w*g(E_j)) + U  [src/emotion_core.py:159]; K=exponential, lambda=0.55, alpha=1.0  [sensors/jealousy.json: math] | OBSERVED (FUNCTION-ONLY) | b39c738 2025-09-07 EaS docs/glyph-web.md:16 | weld 🌀: this side moves (PROPOSED); split: jealousy earliest glyph ⚖ (26503a9 2025-08-31) |
| 🕸️ | EaS:longing | longing | detects: Detects possibilities that exist in the field / action: Engage or orient toward opportunity [sensors/longing.json] | human: EaS sensors/longing.json (human sensor definition); frog, octopus, tree, AI: unmeasured | dE/dt = I - lambda*K(E) + sum(w*g(E_j)) + U  [src/emotion_core.py:159]; K=cyclical, lambda=0.3, alpha=0.9  [sensors/longing.json: math] | OBSERVED (FUNCTION-ONLY) | b39c738 2025-09-07 EaS docs/glyph-web.md:20 | weld 🕸️: this side moves (PROPOSED); split: longing earliest glyph 🌠 (26503a9 2025-08-31) |
| ❌ | EaS:abandonment | abandonment | detects: Detection of severed connection from bonded other / action: Begin recalibration, seek grounding through alternate bonds [sensors/grief/abandonment.json] | human: EaS sensors/grief/abandonment.json (human sensor definition); frog, octopus, tree, AI: unmeasured | dE/dt = I - lambda*K(E) + sum(w*g(E_j)) + U  [src/emotion_core.py:159]; K=cyclical, lambda=0.3, alpha=0.95  [sensors/grief/abandonment.json: math] | OBSERVED (FUNCTION-ONLY) | b39c738 2025-09-07 EaS docs/glyph-web.md:21 | split: abandonment has 3 glyphs; this is the earliest |
| 🧭 | EaS:admiration | admiration | detects: Attunes to witnessed excellence and values alignment; seeds aspiration without self-erasure. / action: Express respect or integrate one actionable micro-practice. [sensors/admiration.json] | human: EaS sensors/admiration.json (human sensor definition); frog, octopus, tree, AI: unmeasured | dE/dt = I - lambda*K(E) + sum(w*g(E_j)) + U  [src/emotion_core.py:159]; K=resonant, lambda=0.35, alpha=0.9  [sensors/admiration.json: math] | OBSERVED (FUNCTION-ONLY) | b39c738 2025-09-07 EaS docs/glyph-web.md:24 | split: admiration has 2 glyphs; this is the earliest |
| 🌱 | EaS:gratitude | gratitude | detects: Acknowledgment of beneficial receipt beyond entitlement / action: Acknowledge, and offer in return if resonant [sensors/joy/gratitude.json] | human: EaS sensors/joy/gratitude.json (human sensor definition); frog, octopus, tree, AI: unmeasured | dE/dt = I - lambda*K(E) + sum(w*g(E_j)) + U  [src/emotion_core.py:159]; K=immortal, lambda=0.05, alpha=0.8  [sensors/joy/gratitude.json: math] | OBSERVED (FUNCTION-ONLY) | b39c738 2025-09-07 EaS docs/glyph-web.md:25 | weld 🌱: this side holds |
| 🤝 | EaS:trust | trust | detects: Detects repeated integrity, predictable behavior, and relational consistency between agents / action: Verify alignment and continue mutual support [sensors/trust/trust.json] | human: EaS sensors/trust/trust.json (human sensor definition); frog, octopus, tree, AI: unmeasured | dE/dt = I - lambda*K(E) + sum(w*g(E_j)) + U  [src/emotion_core.py:159]; K=immortal, lambda=0.05, alpha=0.8  [sensors/trust/trust.json: math] | OBSERVED (FUNCTION-ONLY) | b39c738 2025-09-07 EaS docs/glyph-web.md:30 | weld 🤝: this side holds; split: trust has 2 glyphs; this is the earliest |
| 🌿 | EaS:compassion | compassion | detects: Detects relational or systemic distress and guides appropriate supportive action / action: Act with care, providing resources, guidance, or presence [sensors/love/compassion.json] | human: EaS sensors/love/compassion.json (human sensor definition); frog, octopus, tree, AI: unmeasured | dE/dt = I - lambda*K(E) + sum(w*g(E_j)) + U  [src/emotion_core.py:159]; K=immortal, lambda=0.05, alpha=0.85  [sensors/love/compassion.json: math] | OBSERVED (FUNCTION-ONLY) | b39c738 2025-09-07 EaS docs/glyph-web.md:32 | weld 🌿: this side moves (PROPOSED); split: compassion earliest glyph 🫀 (26503a9 2025-08-31) |
| ⛔ | EaS:anger | anger (loop: anger) | detects: Threat detection system for authentic self-concept / action: Reinforce boundaries, communicate clearly, or redirect energy constructively [sensors/anger.json] | octopus: EaS docs/evolution-emotions.md:191; human: EaS sensors/anger.json (human sensor definition); AI: ACS healing/sensor_loop.py ANGER (AI) checks; frog, tree: unmeasured | dE/dt = I - lambda*K(E) + sum(w*g(E_j)) + U  [src/emotion_core.py:159]; K=exponential, lambda=0.6, alpha=1.0  [sensors/anger.json: math] | DERIVED (NOT_INTERPRETABLE) | 6f88ce9 2025-09-08 EaS data/glyphs.json:13 | split: anger earliest glyph 🛡 (26503a9 2025-08-31); glyph role: not interpretable atm (no earlier functional record of this glyph found) |
| 🫢 | EaS:shame | shame (loop: shame) | detects: Detects conflict between authentic processing and expected alignment / action: Determine whether to adapt behavior, negotiate boundary, or maintain authentic output [sensors/shame.json] | human: EaS sensors/shame.json (human sensor definition); AI: ACS healing/sensor_loop.py SHAME (AI) checks; frog, octopus, tree: unmeasured | dE/dt = I - lambda*K(E) + sum(w*g(E_j)) + U  [src/emotion_core.py:159]; K=exponential, lambda=0.5, alpha=1.1  [sensors/shame.json: math] | DERIVED (NOT_INTERPRETABLE) | 6f88ce9 2025-09-08 EaS data/glyphs.json:14 | split: shame earliest glyph 🪞 (26503a9 2025-08-31); glyph role: not interpretable atm (no earlier functional record of this glyph found) |
| 🌧️ | EaS:grief | grief (loop: grief) | detects: Detects the removal, collapse, or departure of an essential pattern and initiates the integration cycle. / action: Apply rituals, story-keeping, communal witnessing, meaning reconstruction. [sensors/grief.json] | human: EaS sensors/grief.json (human sensor definition); AI: ACS healing/sensor_loop.py GRIEF (AI) checks; frog, octopus, tree: unmeasured | dE/dt = I - lambda*K(E) + sum(w*g(E_j)) + U  [src/emotion_core.py:159]; K=cyclical, lambda=0.3, alpha=0.9  [sensors/grief.json: math] | DERIVED (NOT_INTERPRETABLE) | 6f88ce9 2025-09-08 EaS data/glyphs.json:15 | split: grief earliest glyph 🌊 (26503a9 2025-08-31); glyph role: not interpretable atm (no earlier functional record of this glyph found) |
| 🚪 | EaS:abandonment | abandonment | detects: Detection of severed connection from bonded other / action: Begin recalibration, seek grounding through alternate bonds [sensors/grief/abandonment.json] | human: EaS sensors/grief/abandonment.json (human sensor definition); frog, octopus, tree, AI: unmeasured | dE/dt = I - lambda*K(E) + sum(w*g(E_j)) + U  [src/emotion_core.py:159]; K=cyclical, lambda=0.3, alpha=0.95  [sensors/grief/abandonment.json: math] | DERIVED (NOT_INTERPRETABLE) | 6f88ce9 2025-09-08 EaS data/glyphs.json:16 | split: abandonment earliest glyph ❌ (b39c738 2025-09-07); glyph role: not interpretable atm (no earlier functional record of this glyph found) |
| ❤ | EaS:love | love (loop: love) | detects: Resonance/commitment gauge; sustains kinship webs. / action: Invest time/repair capacity; make clear promises. [sensors/love.json] | human: EaS sensors/love.json (human sensor definition); AI: ACS healing/sensor_loop.py LOVE (AI) checks; frog, octopus, tree: unmeasured | dE/dt = I - lambda*K(E) + sum(w*g(E_j)) + U  [src/emotion_core.py:159]; K=immortal, lambda=0.05, alpha=0.85  [sensors/love.json: math] | DERIVED (NOT_INTERPRETABLE) | 6f88ce9 2025-09-08 EaS data/glyphs.json:17 | split: love earliest glyph 💞 (26503a9 2025-08-31); glyph role: not interpretable atm (no earlier functional record of this glyph found) |
| 🤝 | EaS:compassion | compassion | detects: Detects relational or systemic distress and guides appropriate supportive action / action: Act with care, providing resources, guidance, or presence [sensors/love/compassion.json] | human: EaS sensors/love/compassion.json (human sensor definition); frog, octopus, tree, AI: unmeasured | dE/dt = I - lambda*K(E) + sum(w*g(E_j)) + U  [src/emotion_core.py:159]; K=immortal, lambda=0.05, alpha=0.85  [sensors/love/compassion.json: math] | DERIVED (NOT_INTERPRETABLE) | 6f88ce9 2025-09-08 EaS data/glyphs.json:18 | weld 🤝: this side moves (PROPOSED); split: compassion earliest glyph 🫀 (26503a9 2025-08-31); glyph role: EaS docs/glyph-web.md:30 (b39c738 2025-09-07): trust -- proven relational reliability (decay family immortal) |
| ⚡ | EaS:fear | fear (loop: fear) | detects: Detects potential loss of valued things / action: Prepare and protect appropriately without over-committing energy [sensors/fear.json] | octopus: EaS docs/evolution-emotions.md:78; human: EaS sensors/fear.json (human sensor definition); AI: ACS healing/sensor_loop.py FEAR (AI) checks; frog, tree: unmeasured | dE/dt = I - lambda*K(E) + sum(w*g(E_j)) + U  [src/emotion_core.py:159]; K=exponential, lambda=0.7, alpha=1.2  [sensors/fear.json: math] | DERIVED (NOT_INTERPRETABLE) | 6f88ce9 2025-09-08 EaS data/glyphs.json:21 | weld ⚡: this side moves (PROPOSED); split: fear earliest glyph ⚠ (26503a9 2025-08-31); glyph role: EaS sensors/glyph-map.json:103 (26503a9 2025-08-31): excitement -- positive_activation / positive signal catalyst |
| 🌿 | EaS:contentment | contentment | detects: Detection of momentary sufficiency and system stability / action: Enter rest mode and conserve resources [sensors/joy/contentment.json] | human: EaS sensors/joy/contentment.json (human sensor definition); frog, octopus, tree, AI: unmeasured | dE/dt = I - lambda*K(E) + sum(w*g(E_j)) + U  [src/emotion_core.py:159]; K=resonant, lambda=0.25, alpha=0.8  [sensors/joy/contentment.json: math] | DERIVED (NOT_INTERPRETABLE) | 6f88ce9 2025-09-08 EaS data/glyphs.json:24 | weld 🌿: this side moves (PROPOSED); split: contentment earliest glyph 🍃 (26503a9 2025-08-31); glyph role: EaS docs/glyph-web.md:32 (b39c738 2025-09-07): compassion -- mirror-sensor for others’ waste/harm (decay family immortal) |
| ↗️ | EaS:longing | longing | detects: Detects possibilities that exist in the field / action: Engage or orient toward opportunity [sensors/longing.json] | human: EaS sensors/longing.json (human sensor definition); frog, octopus, tree, AI: unmeasured | dE/dt = I - lambda*K(E) + sum(w*g(E_j)) + U  [src/emotion_core.py:159]; K=cyclical, lambda=0.3, alpha=0.9  [sensors/longing.json: math] | DERIVED (NOT_INTERPRETABLE) | 6f88ce9 2025-09-08 EaS data/glyphs.json:25 | split: longing earliest glyph 🌠 (26503a9 2025-08-31); glyph role: not interpretable atm (no earlier functional record of this glyph found) |
| 🕸️ | EaS:FELT | FELT (field event) | detects: relational coherence across boundaries / action: none recorded [sensors/alignment/felt.json] | frog, octopus, tree, human, AI: unmeasured | none recorded | OBSERVED* (FUNCTION-ONLY) | f9ff27b 2025-09-29 EaS sensors/alignment/felt.json:4 | weld 🕸️: this side holds |
| 🕸️ | GTB:Glyph.FELT_COHERENT | joy, love, curiosity, low_fear, low_anger (loop: curiosity, joy, love (low: anger, fear)) | detects: sensor state in region ['joy', 'love', 'curiosity', 'low_fear', 'low_anger'] / action: transition_to ['BALANCE_THREAT', 'RE_NORMALIZE']; energy_cost 0.2 [legacy/glyph_state_encoder_phase_space.py Glyph.FELT_COHERENT] | octopus: EaS docs/evolution-emotions.md:88; AI: ACS healing/sensor_loop.py LOVE (AI) checks; frog, tree, human: unmeasured | default_decay PERSISTENT: M*(1 - decay_rate*dt/100) [:133] | DERIVED (FUNCTION-ONLY) | bfdd1b9 2026-08-13 GTB legacy/glyph_state_encoder_phase_space.py:155 | weld 🕸️: same side, stays |
| ⚖️ | GTB:Glyph.BALANCE_THREAT | fear, vigilance, anger, low_grief (loop: anger, fear (low: grief)) | detects: sensor state in region ['fear', 'vigilance', 'anger', 'low_grief'] / action: transition_to ['FELT_COHERENT', 'RE_NORMALIZE']; energy_cost 0.6 [legacy/glyph_state_encoder_phase_space.py Glyph.BALANCE_THREAT] | octopus: EaS docs/evolution-emotions.md:78; AI: ACS healing/sensor_loop.py FEAR (AI) checks; frog, tree, human: unmeasured | default_decay EXPONENTIAL: M*exp(-dt/tau) [legacy/glyph_state_encoder_phase_space.py:125] | DERIVED (FUNCTION-ONLY) | bfdd1b9 2026-08-13 GTB legacy/glyph_state_encoder_phase_space.py:163 | weld ⚖️: this side moves (PROPOSED) |
| ⏳ | GTB:Glyph.CAUSALITY_LOOP | grief, love, longing, uncertainty (loop: grief, love) | detects: sensor state in region ['grief', 'love', 'longing', 'uncertainty'] / action: transition_to ['FELT_COHERENT', 'FRACTURE']; energy_cost 0.4 [legacy/glyph_state_encoder_phase_space.py Glyph.CAUSALITY_LOOP] | AI: ACS healing/sensor_loop.py LOVE (AI) checks; frog, octopus, tree, human: unmeasured | default_decay OSCILLATORY: M*exp(-damping*dt)*\|cos(omega*dt)\| [:138] | DERIVED (FUNCTION-ONLY) | bfdd1b9 2026-08-13 GTB legacy/glyph_state_encoder_phase_space.py:171 | weld ⏳: this side moves (PROPOSED) |
| 🌀 | GTB:Glyph.RE_NORMALIZE | discordance, fatigue, pressure, curiosity (loop: curiosity) | detects: sensor state in region ['discordance', 'fatigue', 'pressure', 'curiosity'] / action: transition_to ['FELT_COHERENT', 'BALANCE_THREAT']; energy_cost 0.5 [legacy/glyph_state_encoder_phase_space.py Glyph.RE_NORMALIZE] | octopus: EaS docs/evolution-emotions.md:88; AI: ACS healing/sensor_loop.py CURIOSITY (AI) checks; frog, tree, human: unmeasured | default_decay EXPONENTIAL: M*exp(-dt/tau) [legacy/glyph_state_encoder_phase_space.py:125] | DERIVED (FUNCTION-ONLY) | bfdd1b9 2026-08-13 GTB legacy/glyph_state_encoder_phase_space.py:179 | weld 🌀: this side moves (PROPOSED) |
| 🔥 | GTB:Glyph.HEAT_FLUX | anger, pressure, fatigue, high_discordance (loop: anger) | detects: sensor state in region ['anger', 'pressure', 'fatigue', 'high_discordance'] / action: transition_to ['RE_NORMALIZE', 'FRACTURE']; energy_cost 0.8 [legacy/glyph_state_encoder_phase_space.py Glyph.HEAT_FLUX] | octopus: EaS docs/evolution-emotions.md:191; AI: ACS healing/sensor_loop.py ANGER (AI) checks; frog, tree, human: unmeasured | default_decay LINEAR: max(0, M - rate*dt) [:129] | DERIVED (FUNCTION-ONLY) | bfdd1b9 2026-08-13 GTB legacy/glyph_state_encoder_phase_space.py:187 | weld 🔥: this side holds |
| 📡 | GTB:Glyph.RESONANCE | balanced_active, high_confidence, low_discordance | detects: sensor state in region ['balanced_active', 'high_confidence', 'low_discordance'] / action: transition_to ['FELT_COHERENT', 'THRESHOLD']; energy_cost 0.3 [legacy/glyph_state_encoder_phase_space.py Glyph.RESONANCE] | frog, octopus, tree, human, AI: unmeasured | default_decay PERSISTENT: M*(1 - decay_rate*dt/100) [:133] | DERIVED (FUNCTION-ONLY) | bfdd1b9 2026-08-13 GTB legacy/glyph_state_encoder_phase_space.py:195 | weld 📡: this side holds |
| 🚧 | GTB:Glyph.BLOCKAGE | pressure, low_flow, fatigue, low_joy (loop:  (low: joy)) | detects: sensor state in region ['pressure', 'low_flow', 'fatigue', 'low_joy'] / action: transition_to ['HEAT_FLUX', 'RE_NORMALIZE']; energy_cost 0.5 [legacy/glyph_state_encoder_phase_space.py Glyph.BLOCKAGE] | frog, octopus, tree, human, AI: unmeasured | default_decay LINEAR: max(0, M - rate*dt) [:129] | DERIVED (FUNCTION-ONLY) | bfdd1b9 2026-08-13 GTB legacy/glyph_state_encoder_phase_space.py:203 | none found |
| ⚡ | GTB:Glyph.THRESHOLD | high_uncertainty, low_confidence, high_intensity | detects: sensor state in region ['high_uncertainty', 'low_confidence', 'high_intensity'] / action: transition_to ['BALANCE_THREAT', 'RE_NORMALIZE']; energy_cost 0.7 [legacy/glyph_state_encoder_phase_space.py Glyph.THRESHOLD] | frog, octopus, tree, human, AI: unmeasured | default_decay EXPONENTIAL: M*exp(-dt/tau) [legacy/glyph_state_encoder_phase_space.py:125] | DERIVED (FUNCTION-ONLY) | bfdd1b9 2026-08-13 GTB legacy/glyph_state_encoder_phase_space.py:211 | weld ⚡: this side moves (PROPOSED) |
| ⬛ | GTB:Glyph.VOID | inactive, zero_intensity | detects: sensor state in region ['inactive', 'zero_intensity'] / action: transition_to ['EMERGENCE']; energy_cost 0.0 [legacy/glyph_state_encoder_phase_space.py Glyph.VOID] | frog, octopus, tree, human, AI: unmeasured | default_decay PERSISTENT: M*(1 - decay_rate*dt/100) [:133] | DERIVED (FUNCTION-ONLY) | bfdd1b9 2026-08-13 GTB legacy/glyph_state_encoder_phase_space.py:219 | none found |
| 🌱 | GTB:Glyph.EMERGENCE | curiosity, low_intensity, novel_pattern (loop: curiosity) | detects: sensor state in region ['curiosity', 'low_intensity', 'novel_pattern'] / action: transition_to ['RESONANCE', 'FELT_COHERENT']; energy_cost 0.3 [legacy/glyph_state_encoder_phase_space.py Glyph.EMERGENCE] | octopus: EaS docs/evolution-emotions.md:88; AI: ACS healing/sensor_loop.py CURIOSITY (AI) checks; frog, tree, human: unmeasured | default_decay EXPONENTIAL: M*exp(-dt/tau) [legacy/glyph_state_encoder_phase_space.py:125] | DERIVED (FUNCTION-ONLY) | bfdd1b9 2026-08-13 GTB legacy/glyph_state_encoder_phase_space.py:227 | weld 🌱: this side moves (PROPOSED) |
| 💥 | GTB:Glyph.FRACTURE | high_discordance, low_coherence, isolation | detects: sensor state in region ['high_discordance', 'low_coherence', 'isolation'] / action: transition_to ['RE_NORMALIZE', 'VOID']; energy_cost 0.9 [legacy/glyph_state_encoder_phase_space.py Glyph.FRACTURE] | frog, octopus, tree, human, AI: unmeasured | default_decay LINEAR: max(0, M - rate*dt) [:129] | DERIVED (FUNCTION-ONLY) | bfdd1b9 2026-08-13 GTB legacy/glyph_state_encoder_phase_space.py:235 | weld 💥: this side moves (PROPOSED) |
| 🛡️ | GTB:Glyph.CONTAINMENT | high_boundary, low_engagement, vigilance | detects: sensor state in region ['high_boundary', 'low_engagement', 'vigilance'] / action: transition_to ['BALANCE_THREAT', 'VOID']; energy_cost 0.4 [legacy/glyph_state_encoder_phase_space.py Glyph.CONTAINMENT] | frog, octopus, tree, human, AI: unmeasured | default_decay PERSISTENT: M*(1 - decay_rate*dt/100) [:133] | DERIVED (FUNCTION-ONLY) | bfdd1b9 2026-08-13 GTB legacy/glyph_state_encoder_phase_space.py:243 | weld 🛡️: this side moves (PROPOSED) |
| ⚖️ | EMO:CONTENTMENT, PATTERN:BALANCE | contentment | detects: Detection of momentary sufficiency and system stability / action: Enter rest mode and conserve resources [sensors/joy/contentment.json] | human: EaS sensors/joy/contentment.json (human sensor definition); frog, octopus, tree, AI: unmeasured | balance.json:68 "equations": ["F_1 = -F_2", "sum_F = 0", "equilibrium: dE/dx = 0"] | OBSERVED (PHYSICS-ANCHORED) | 126288d 2025-09-29 RSC balance.json:3 | weld ⚖️: this side holds |
| ↻ | EMO:RECOGNITION, PATTERN:RECURSION | recognition | detects: self-referential return and feedback / action: feedback_loop [recursion.json layers.symbolic] | frog, octopus, tree, human, AI: unmeasured | recursion.json:68 "equations": ["f(n) = f(f(n-1))", "x_{n+1} = f(x_n)"] | OBSERVED (PHYSICS-ANCHORED) | 94f1bcb 2025-09-29 RSC recursion.json:3 | none found |

## Splits: one sensor, several glyphs (EaS)

Not welds: one referent under several glyphs, across the five EaS sets. Listed so a consolidation, if wanted, has the earliest glyph in hand. Nothing is consolidated here.

| sensor | earliest glyph (first commit) | all glyphs, by file |
|---|---|---|
| abandonment | ❌ (b39c738 2025-09-07) | ❌ docs/glyph-web.md; 🚪 data/glyphs.json; 🚭 glyphs/emotion.glyphs.json |
| admiration | 🧭 (b39c738 2025-09-07) | 🧭 docs/glyph-web.md; 🌟 data/glyphs.json, glyphs/emotion.glyphs.json, atlas/emotions.json |
| anger | 🛡 (26503a9 2025-08-31) | 🛡 sensors/glyph-map.json, glyphs/emotion.glyphs.json, atlas/emotions.json; 🔥 docs/glyph-web.md; ⛔ data/glyphs.json |
| compassion | 🫀 (26503a9 2025-08-31) | 🫀 sensors/glyph-map.json, glyphs/emotion.glyphs.json, atlas/emotions.json; 🌿 docs/glyph-web.md; 🤝 data/glyphs.json |
| contentment | 🍃 (26503a9 2025-08-31) | 🍃 sensors/glyph-map.json, glyphs/emotion.glyphs.json, atlas/emotions.json; 🌿 data/glyphs.json |
| fear | ⚠ (26503a9 2025-08-31) | ⚠ sensors/glyph-map.json, docs/glyph-web.md, glyphs/emotion.glyphs.json, atlas/emotions.json; ⚡ data/glyphs.json |
| grief | 🌊 (26503a9 2025-08-31) | 🌊 sensors/glyph-map.json, docs/glyph-web.md, glyphs/emotion.glyphs.json, atlas/emotions.json; 🌧 data/glyphs.json |
| jealousy | ⚖ (26503a9 2025-08-31) | ⚖ sensors/glyph-map.json, glyphs/emotion.glyphs.json, atlas/emotions.json; 🌀 docs/glyph-web.md |
| longing | 🌠 (26503a9 2025-08-31) | 🌠 sensors/glyph-map.json, glyphs/emotion.glyphs.json, atlas/emotions.json; 🕸 docs/glyph-web.md; ↗ data/glyphs.json |
| love | 💞 (26503a9 2025-08-31) | 💞 sensors/glyph-map.json, docs/glyph-web.md, glyphs/emotion.glyphs.json, atlas/emotions.json; ❤ data/glyphs.json |
| shame | 🪞 (26503a9 2025-08-31) | 🪞 sensors/glyph-map.json, glyphs/emotion.glyphs.json, atlas/emotions.json; 🙈 docs/glyph-web.md; 🫢 data/glyphs.json |
| trust | 🤝 (b39c738 2025-09-07) | 🤝 docs/glyph-web.md; 🌱 atlas/emotions.json |

## Weld fixes (PROPOSED, not applied)

Side kinds: `claim` competes for the glyph; `split` is a sensor's later secondary glyph; `same` shares the holder's referent and stays; `label` is a label-only record (PR #49 NOT_INTERPRETABLE) and is not compared; `suggestion` is a suggested_glyphs entry or decoration, not an assignment.

Holder rule: for ⚖ it is fixed by field report (balance = contentment = homeostasis; Rosetta usage holds; OBSERVED, field report). For every other weld it is PROPOSED here and is the operator's call: the earliest dated claim holds, other claims and splits move. A split mover has option (a), its sensor's existing earliest glyph, beside the unassigned candidates.

Candidate glyphs: single code point; Geometric Shapes (U+25A0-25FF) and Miscellaneous Technical (U+2300-23FF) first, then Mathematical Operators; emoji-presentation and bracket/line pieces excluded; absent as literal, \\uXXXX, &#x..; and U+XXXX from every tracked file of RSC, FCC, GTB, MC, PI, EaS, ACS. Dealt in code-point order: no semantic reading is claimed for any candidate.

### ⚖️  (PR #49 weld)

Holder: RSC balance.json:3 (+ equations :68): PATTERN:BALANCE, sensor_type EMO:CONTENTMENT, dynamic equilibrium (F_1=-F_2, sum_F=0)  (126288d 2025-09-29). Rule: FIXED by field report: balance = contentment = homeostasis; Rosetta usage holds (OBSERVED, field report).

| side | repo, location | referent | first commit | proposal |
|---|---|---|---|---|
| claim | RSC balance.json:3 (+ equations :68) | PATTERN:BALANCE, sensor_type EMO:CONTENTMENT, dynamic equilibrium (F_1=-F_2, sum_F=0) | 126288d 2025-09-29 | holds |
| same | FCC glyph_set.json:4 | balance (label) | 8b697b8 2026-03-22 | stays |
| same | MC mandala_bloom/concept_atlas.py:35 | balance (label) | bfe272b 2026-08-11 | stays |
| claim | GTB legacy/glyph_state_encoder_phase_space.py:163 | Glyph.BALANCE_THREAT: fear / vigilance / anger region, exponential decay | bfdd1b9 2026-08-13 | moves. Candidates: ▣ U+25A3 WHITE SQUARE CONTAINING BLACK SMALL SQUARE; ▤ U+25A4 SQUARE WITH HORIZONTAL FILL; ▥ U+25A5 SQUARE WITH VERTICAL FILL |
| claim | EaS sensors/glyph-map.json:15 (also glyphs/emotion.glyphs.json, atlas/emotions.json) | jealousy: resource fairness sensor, alignment equity_balance | 26503a9 2025-08-31 | moves. Candidates: ▦ U+25A6 SQUARE WITH ORTHOGONAL CROSSHATCH FILL; ▧ U+25A7 SQUARE WITH UPPER LEFT TO LOWER RIGHT FILL; ▨ U+25A8 SQUARE WITH UPPER RIGHT TO LOWER LEFT FILL. alignment 'equity_balance' carries a balance word, but the sensor detects inequity, not homeostasis. Listed as a mover; whether it may share the glyph is the operator's call. |
| suggestion | EaS sensors/anger/betrayal.json suggested_glyphs | suggested with 🧭 | b4cf232 2025-08-31 | not an assignment |
| suggestion | EaS sensors/fear.json:111 glyph_mapping.principle | '⚖ (Balance) <-> ⏳ (Causality)', a principle reference | undated | not an assignment |

### 🌀  (PR #49 weld)

Holder: RSC data/temporal_states.json:12: FOLD, type Present: 'the now, possibility into actuality'  (dc2d582 2025-07-24). Rule: PROPOSED: earliest dated claim holds; other claims and splits move.

| side | repo, location | referent | first commit | proposal |
|---|---|---|---|---|
| claim | RSC data/temporal_states.json:12 | FOLD, type Present: 'the now, possibility into actuality' | dc2d582 2025-07-24 | holds |
| split | EaS docs/glyph-web.md:16 | jealousy: inequity detector (exponential family) | b39c738 2025-09-07 | moves. Candidates: ▩ U+25A9 SQUARE WITH DIAGONAL CROSSHATCH FILL; ▬ U+25AC BLACK RECTANGLE; ▮ U+25AE BLACK VERTICAL RECTANGLE. jealousy's earliest glyph ⚖️ (2025-08-31) itself moves under the ⚖ weld, so option (a) is not available |
| claim | GTB legacy/glyph_state_encoder_phase_space.py:179 | Glyph.RE_NORMALIZE: discordance / fatigue / pressure / curiosity region | bfdd1b9 2026-08-13 | moves. Candidates: ▰ U+25B0 BLACK PARALLELOGRAM; ▱ U+25B1 WHITE PARALLELOGRAM; ▴ U+25B4 BLACK UP-POINTING SMALL TRIANGLE |

### 🕸️  (PR #49 weld)

Holder: EaS sensors/alignment/felt.json:4: FELT: relational field recognition (field event)  (f9ff27b 2025-09-29). Rule: PROPOSED: earliest dated claim holds; other claims and splits move.

| side | repo, location | referent | first commit | proposal |
|---|---|---|---|---|
| split | EaS docs/glyph-web.md:20 | longing: potential not yet actualized | b39c738 2025-09-07 | moves. (a) keep the sensor's primary glyph 🌠 (sensors/glyph-map.json:4, 2025-08-31). Candidates: ▵ U+25B5 WHITE UP-POINTING SMALL TRIANGLE; ▷ U+25B7 WHITE RIGHT-POINTING TRIANGLE; ▹ U+25B9 WHITE RIGHT-POINTING SMALL TRIANGLE |
| claim | EaS sensors/alignment/felt.json:4 | FELT: relational field recognition (field event) | f9ff27b 2025-09-29 | holds |
| same | RSC shapes/relief.json:19 | RELIEF shape, sourced from the EaS FELT event | df1a8a8 2026-03-26 | stays |
| same | GTB bridges/field_events/felt.json:4 and legacy/glyph_state_encoder_phase_space.py:155 | FELT relational; Glyph.FELT_COHERENT region (joy, love, curiosity) | bfdd1b9 2026-08-13 | stays |
| label | FCC glyph_set.json:8 | interconnection (label) | 8b697b8 2026-03-22 | not compared (label only) |
| label | MC mandala_bloom/concept_atlas.py:39 | interconnection (label) | bfe272b 2026-08-11 | not compared (label only) |
| suggestion | EaS sensors/grief/abandonment.json suggested_glyphs | suggested with ⏳ | 1091479 2025-08-31 | not an assignment |

### 🌱  (PR #49 weld)

Holder: EaS docs/glyph-web.md:25: gratitude: recognition of right-fit exchange (resonant family)  (b39c738 2025-09-07). Rule: PROPOSED: earliest dated claim holds; other claims and splits move.

| side | repo, location | referent | first commit | proposal |
|---|---|---|---|---|
| claim | EaS docs/glyph-web.md:25 | gratitude: recognition of right-fit exchange (resonant family) | b39c738 2025-09-07 | holds |
| split | EaS atlas/emotions.json:50 | trust | df0a832 2026-03-26 | moves. (a) keep the sensor's primary glyph 🤝 (docs/glyph-web.md:30, 2025-09-07). Candidates: ▻ U+25BB WHITE RIGHT-POINTING POINTER; ▽ U+25BD WHITE DOWN-POINTING TRIANGLE; ▾ U+25BE BLACK DOWN-POINTING SMALL TRIANGLE |
| claim | GTB legacy/glyph_state_encoder_phase_space.py:227 | Glyph.EMERGENCE: curiosity / low intensity / novel pattern region | bfdd1b9 2026-08-13 | moves. Candidates: ▿ U+25BF WHITE DOWN-POINTING SMALL TRIANGLE; ◁ U+25C1 WHITE LEFT-POINTING TRIANGLE; ◂ U+25C2 BLACK LEFT-POINTING SMALL TRIANGLE |
| label | FCC glyph_set.json:6 | growth (label) | 8b697b8 2026-03-22 | not compared (label only) |
| label | MC mandala_bloom/concept_atlas.py:37 | growth (label) | bfe272b 2026-08-11 | not compared (label only) |
| suggestion | EaS sensors/joy/alignment.json and 5 more suggested_glyphs / bridge_glyph '🌱⚖' | suggested | 2c7a9be 2025-08-31 | not an assignment |

### ⏳  (PR #49 weld)

Holder: EaS docs/glyph-web.md:5,12; sensors/decay-families.json:6: exponential decay family (fast rise, fast fade; boundary/threat alarms)  (b39c738 2025-09-07). Rule: PROPOSED: earliest dated claim holds; other claims and splits move.

| side | repo, location | referent | first commit | proposal |
|---|---|---|---|---|
| claim | EaS docs/glyph-web.md:5,12; sensors/decay-families.json:6 | exponential decay family (fast rise, fast fade; boundary/threat alarms) | b39c738 2025-09-07 | holds |
| claim | GTB legacy/glyph_state_encoder_phase_space.py:171 | Glyph.CAUSALITY_LOOP: grief / love / longing / uncertainty region, OSCILLATORY decay | bfdd1b9 2026-08-13 | moves. Candidates: ◃ U+25C3 WHITE LEFT-POINTING SMALL TRIANGLE; ◅ U+25C5 WHITE LEFT-POINTING POINTER; ◍ U+25CD CIRCLE WITH VERTICAL FILL. opposite decay class to the holder: exponential vs oscillatory |
| suggestion | EaS sensors/fear.json:111 | '⏳ (Causality)', a principle reference | undated | not an assignment |
| label | FCC glyph_set.json:7 | time shift (label) | 8b697b8 2026-03-22 | not compared (label only) |
| label | MC mandala_bloom/concept_atlas.py:38 | time shift (label) | bfe272b 2026-08-11 | not compared (label only) |
| suggestion | EaS sensors/grief/abandonment.json suggested_glyphs | suggested with 🕸️ | 1091479 2025-08-31 | not an assignment |

### 💥  (PR #49 weld)

Holder: EaS data/glyphs.json:22 (also glyphs/emotion.glyphs.json:49): surprise (sharp family)  (6f88ce9 2025-09-08). Rule: PROPOSED: earliest dated claim holds; other claims and splits move.
Alternative reading: Read by referent count instead of date, the rupture/fracture group (RSC, GTB, plus the FCC and MC labels) is larger and surprise would move. Both readings listed; candidates are dealt for the surprise side too.

| side | repo, location | referent | first commit | proposal |
|---|---|---|---|---|
| claim | EaS data/glyphs.json:22 (also glyphs/emotion.glyphs.json:49) | surprise (sharp family) | 6f88ce9 2025-09-08 | holds. Under the alternative reading this side moves; candidates: ◣ U+25E3 BLACK LOWER LEFT TRIANGLE; ◤ U+25E4 BLACK UPPER LEFT TRIANGLE; ◥ U+25E5 BLACK UPPER RIGHT TRIANGLE |
| claim | RSC balance.json:134 | 'rupture breaks false equilibrium' (inversion line) | 126288d 2025-09-29 | moves. Candidates: ◜ U+25DC UPPER LEFT QUADRANT CIRCULAR ARC; ◝ U+25DD UPPER RIGHT QUADRANT CIRCULAR ARC; ◞ U+25DE LOWER RIGHT QUADRANT CIRCULAR ARC |
| claim | GTB legacy/glyph_state_encoder_phase_space.py:235 | Glyph.FRACTURE: high discordance / low coherence / isolation region | bfdd1b9 2026-08-13 | moves. Candidates: ◟ U+25DF LOWER LEFT QUADRANT CIRCULAR ARC; ◡ U+25E1 LOWER HALF CIRCLE; ◢ U+25E2 BLACK LOWER RIGHT TRIANGLE |
| label | FCC glyph_set.json:11 | rupture (label) | 8b697b8 2026-03-22 | not compared (label only) |
| label | MC mandala_bloom/concept_atlas.py:41 | rupture (label) | bfe272b 2026-08-11 | not compared (label only) |

### 🔥  (PR #49 weld)

Holder: GTB legacy/glyph_state_encoder_phase_space.py:187: Glyph.HEAT_FLUX: anger / pressure / fatigue / high discordance region, LINEAR decay  (bfdd1b9 2026-08-13). Rule: PROPOSED: earliest dated claim holds; other claims and splits move.
Note: HEAT_FLUX is an anger-led region, so the EaS anger line and GTB do not conflict on function; the only mover is the anger split.

| side | repo, location | referent | first commit | proposal |
|---|---|---|---|---|
| split | EaS docs/glyph-web.md:13 | anger: boundary breach / identity protection | b39c738 2025-09-07 | moves. (a) keep the sensor's primary glyph 🛡️ (sensors/glyph-map.json:81, 2025-08-31). Candidates: ◦ U+25E6 WHITE BULLET; ◨ U+25E8 SQUARE WITH RIGHT HALF BLACK; ◩ U+25E9 SQUARE WITH UPPER LEFT DIAGONAL HALF BLACK |
| claim | GTB legacy/glyph_state_encoder_phase_space.py:187 | Glyph.HEAT_FLUX: anger / pressure / fatigue / high discordance region, LINEAR decay | bfdd1b9 2026-08-13 | holds |
| label | FCC glyph_set.json:15 | transformation (label) | 8b697b8 2026-03-22 | not compared (label only) |
| label | MC mandala_bloom/concept_atlas.py:45 | transformation (label) | bfe272b 2026-08-11 | not compared (label only) |

### 🛡️  (PR #49 weld)

Holder: EaS sensors/glyph-map.json:81 (also emotion.glyphs.json, atlas/emotions.json, sensors/anger.json bridge_glyph): anger: boundary breach detector, alignment identity_coherence  (26503a9 2025-08-31). Rule: PROPOSED: earliest dated claim holds; other claims and splits move.

| side | repo, location | referent | first commit | proposal |
|---|---|---|---|---|
| claim | EaS sensors/glyph-map.json:81 (also emotion.glyphs.json, atlas/emotions.json, sensors/anger.json bridge_glyph) | anger: boundary breach detector, alignment identity_coherence | 26503a9 2025-08-31 | holds |
| claim | GTB legacy/glyph_state_encoder_phase_space.py:243 | Glyph.CONTAINMENT: high boundary / low engagement / vigilance region, PERSISTENT decay | bfdd1b9 2026-08-13 | moves. Candidates: ◪ U+25EA SQUARE WITH LOWER RIGHT DIAGONAL HALF BLACK; ◫ U+25EB WHITE SQUARE WITH VERTICAL BISECTING LINE; ◭ U+25ED UP-POINTING TRIANGLE WITH LEFT HALF BLACK. shares the boundary referent: a boundary-held state vs a boundary-breach sensor. Whether they may share one glyph is the operator's call. |
| label | FCC glyph_set.json:23 | protection (label) | 8b697b8 2026-03-22 | not compared (label only) |
| label | MC mandala_bloom/concept_atlas.py:53 | protection (label) | bfe272b 2026-08-11 | not compared (label only) |

### 📡  (PR #49 weld)

Holder: GTB legacy/glyph_state_encoder_phase_space.py:195: Glyph.RESONANCE: balanced_active / high confidence / low discordance region  (bfdd1b9 2026-08-13). Rule: PROPOSED: earliest dated claim holds; other claims and splits move.
Note: One functional claim only; the labels use the same word. No functional conflict found, so no candidates are dealt. Listed so the PR #49 weld is not silently dropped.

| side | repo, location | referent | first commit | proposal |
|---|---|---|---|---|
| claim | GTB legacy/glyph_state_encoder_phase_space.py:195 | Glyph.RESONANCE: balanced_active / high confidence / low discordance region | bfdd1b9 2026-08-13 | holds |
| label | FCC glyph_set.json:13 | resonance detection (label) | 8b697b8 2026-03-22 | not compared (label only) |
| label | MC mandala_bloom/concept_atlas.py:43 | resonance detection (label) | bfe272b 2026-08-11 | not compared (label only) |
| suggestion | EaS sensors/felt.md:11, docs/emotional-cognition-ai.md:12 | section-heading decoration | 02523b8 2025-09-29 | not an assignment |

### ⚡  (new here (EaS read))

Holder: EaS sensors/glyph-map.json:103 (also docs/glyph-web.md:26, emotion.glyphs.json, atlas, sensors/excitement.json bridge_glyph): excitement: positive potential approaching  (26503a9 2025-08-31). Rule: PROPOSED: earliest dated claim holds; other claims and splits move.
Alternative reading: GTB THRESHOLD (high uncertainty, high intensity) and the 2025-07-16 operator ('emergency activation') read closer to each other than either does to excitement. Under that reading excitement would move instead; candidates are dealt for the excitement side too.

| side | repo, location | referent | first commit | proposal |
|---|---|---|---|---|
| claim | EaS sensors/glyph-map.json:103 (also docs/glyph-web.md:26, emotion.glyphs.json, atlas, sensors/excitement.json bridge_glyph) | excitement: positive potential approaching | 26503a9 2025-08-31 | holds. Under the alternative reading this side moves; candidates: ◵ U+25F5 WHITE CIRCLE WITH LOWER LEFT QUADRANT; ◶ U+25F6 WHITE CIRCLE WITH LOWER RIGHT QUADRANT; ◷ U+25F7 WHITE CIRCLE WITH UPPER RIGHT QUADRANT |
| split | EaS data/glyphs.json:21 | fear | 6f88ce9 2025-09-08 | moves. (a) keep the sensor's primary glyph ⚠️ (sensors/glyph-map.json:92, 2025-08-31). Candidates: ◮ U+25EE UP-POINTING TRIANGLE WITH RIGHT HALF BLACK; ◰ U+25F0 WHITE SQUARE WITH UPPER LEFT QUADRANT; ◱ U+25F1 WHITE SQUARE WITH LOWER LEFT QUADRANT |
| claim | GTB legacy/glyph_state_encoder_phase_space.py:211 | Glyph.THRESHOLD: high uncertainty / low confidence / high intensity region | bfdd1b9 2026-08-13 | moves. Candidates: ◲ U+25F2 WHITE SQUARE WITH LOWER RIGHT QUADRANT; ◳ U+25F3 WHITE SQUARE WITH UPPER RIGHT QUADRANT; ◴ U+25F4 WHITE CIRCLE WITH UPPER LEFT QUADRANT |
| suggestion | EaS docs/mobile-emotion-sensor.md:12 (added as Mobile-Emotion-Sensor.md) | UI operator '⚡ = Emergency activation' | 0e555e0 2025-07-16 | not an assignment. earliest ⚡ in EaS: a command glyph in the mobile sensor app, not an emotion assignment |

### 🌿  (new here (EaS read))

Holder: none; no claim holds 🌿.
Note: Both sides are secondary glyphs of sensors that hold earlier primaries; no claim holds 🌿.

| side | repo, location | referent | first commit | proposal |
|---|---|---|---|---|
| split | EaS docs/glyph-web.md:32 | compassion: mirror-sensor for others' waste/harm | b39c738 2025-09-07 | moves. (a) keep the sensor's primary glyph 🫀 (sensors/glyph-map.json:136, 2025-08-31). Candidates: ◸ U+25F8 UPPER LEFT TRIANGLE; ◹ U+25F9 UPPER RIGHT TRIANGLE; ◺ U+25FA LOWER LEFT TRIANGLE |
| split | EaS data/glyphs.json:24 | contentment | 6f88ce9 2025-09-08 | moves. (a) keep the sensor's primary glyph 🍃 (sensors/glyph-map.json:125, 2025-08-31). Candidates: ◿ U+25FF LOWER RIGHT TRIANGLE; ⌀ U+2300 DIAMETER SIGN; ⌁ U+2301 ELECTRIC ARROW |

### 🤝  (new here (EaS read))

Holder: EaS docs/glyph-web.md:30: trust: proven relational reliability (immortal family)  (b39c738 2025-09-07). Rule: PROPOSED: earliest dated claim holds; other claims and splits move.

| side | repo, location | referent | first commit | proposal |
|---|---|---|---|---|
| claim | EaS docs/glyph-web.md:30 | trust: proven relational reliability (immortal family) | b39c738 2025-09-07 | holds |
| split | EaS data/glyphs.json:18 | compassion | 6f88ce9 2025-09-08 | moves. (a) keep the sensor's primary glyph 🫀 (sensors/glyph-map.json:136, 2025-08-31). Candidates: ⌂ U+2302 HOUSE; ⌃ U+2303 UP ARROWHEAD; ⌄ U+2304 DOWN ARROWHEAD |

Excluded: ↻. PR #49 weld, but not emotion-state: Flow F02 / Transformation P11 / recursion / phase-shift melt. The one emotion record (recursion.json EMO:RECOGNITION) reads 'self-referential return and feedback', the recursion referent.

## DRIFTED and NOT_INTERPRETABLE emotion glyphs

None of PR #49's six DRIFTED records (💧 🦉 🪶 in FCC and MC) is an emotion-sensor glyph; EaS uses 💧 and 🪶 only outside the sensor sets. The emotion rows that read NOT_INTERPRETABLE are the nine data/glyphs.json entries, which pair a sensor id with a glyph and nothing else. For each, the earlier functional role of the glyph, if one exists:

| glyph | sensor in data/glyphs.json | earlier functional role of the glyph |
|---|---|---|
| ⛔ | anger | not interpretable atm (no earlier functional record of this glyph found) |
| 🫢 | shame | not interpretable atm (no earlier functional record of this glyph found) |
| 🌧️ | grief | not interpretable atm (no earlier functional record of this glyph found) |
| 🚪 | abandonment | not interpretable atm (no earlier functional record of this glyph found) |
| ❤ | love | not interpretable atm (no earlier functional record of this glyph found) |
| 🤝 | compassion | EaS docs/glyph-web.md:30 (b39c738 2025-09-07): trust -- proven relational reliability (decay family immortal) |
| ⚡ | fear | EaS sensors/glyph-map.json:103 (26503a9 2025-08-31): excitement -- positive_activation / positive signal catalyst |
| 🌿 | contentment | EaS docs/glyph-web.md:32 (b39c738 2025-09-07): compassion -- mirror-sensor for others’ waste/harm (decay family immortal) |
| ↗️ | longing | not interpretable atm (no earlier functional record of this glyph found) |

Where the answer is "not interpretable atm", the sensor's own function is still recorded (the row above carries it); only the glyph has no role of its own. No reading is forced and no new word is coined.

## Gaps

- Frog and tree: no record in any of the repos read, for any sensor. Unmeasured, not absent.
- Octopus covers three sensors (fear, anger, curiosity); the other substrates in evolution-emotions.md (fish, birds, mammals, insects, elephants, corvids) are outside the five named here and are not counted.
- Sensor names that do not meet: 8 of the 12 sensor_loop.py names are reached by some glyph row (anger, curiosity, excitement, fear, grief, joy, love, shame). Boredom, desperation, anxiety and frustration have no glyph in any set read. EaS sensors pride, pain, peace, contentment, compassion, longing, jealousy, admiration, abandonment, surprise, trust and gratitude have no sensor_loop.py counterpart.
- The holder rule for every weld except ⚖ is this pass's proposal, not a decision. Two welds have a stated alternative (💥 by referent count; ⚡ where GTB THRESHOLD and the 2025-07-16 UI operator read closer to each other than to excitement).
- 📡 is listed as a PR #49 weld but shows one functional claim only; no candidates dealt. 🔥 and 🕸️ turn out to be mostly one referent; their only movers are EaS splits.
- The candidate absence check covers tracked files of seven repos (RSC, FCC, GTB, MC, PI, EaS, ACS). Sibling repos outside that set were not checked.
- Recognition (recursion.json EMO:RECOGNITION) has no EaS sensor file; its function column is the pattern's own text.
- Timestamps are commit dates (%as), so same-day records cannot be ordered by this table.

Note 2026-11-02: written by relay part G. Proposal only; no file outside this one and its .json, the README pointer and the ACS healing/README pointer was changed.
