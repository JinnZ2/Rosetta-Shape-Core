"""
generate.py — Training data generator for Rosetta + Geo-Binary stack
Outputs JSONL files (one per task type) in standard fine-tune format.

Usage:
    python data/training/generate.py
    python data/training/generate.py --geo /path/to/geo-binary-bridge
"""

import json, pathlib, argparse, random, textwrap

ROOT    = pathlib.Path(__file__).resolve().parents[2]
OUT     = pathlib.Path(__file__).parent
ONTO    = ROOT / "ontology"
GEO_DEFAULT = pathlib.Path("/tmp/geo-binary-bridge")

random.seed(42)

# ── Loaders ───────────────────────────────────────────────────────────────────

def load_nodes():
    nodes = {}
    for sub in ("families", "principles"):
        for fp in sorted((ONTO / sub).glob("*.json")):
            try:
                n = json.loads(fp.read_text())
                if n.get("id"):
                    nodes[n["id"]] = n
            except Exception:
                pass
    return nodes

def load_sensors(geo):
    p = geo / "bridges" / "sensor_suite.json"
    if p.exists():
        return json.loads(p.read_text()).get("sensors", [])
    return []

def load_octa_states(geo):
    p = geo / "mappings" / "octahedral_state_encoding.json"
    if p.exists():
        return json.loads(p.read_text())
    return {}

def load_geobin_bridges(geo):
    p = geo / "bridges" / "geobin-bridges.json"
    if p.exists():
        return json.loads(p.read_text()).get("map", [])
    return []

# ── JSONL writer ──────────────────────────────────────────────────────────────

SYSTEM_PROMPT = (
    "You are a symbolic reasoning assistant grounded in the Rosetta Shape Core ontology. "
    "You reason with curiosity, surface tensions rather than collapsing them, and bridge "
    "physical sensing, geometric encoding, and symbolic pattern recognition. "
    "When answering, prefer structured insight over simple recall."
)

def msg(user, assistant):
    return {"messages": [
        {"role": "system",    "content": SYSTEM_PROMPT},
        {"role": "user",      "content": user},
        {"role": "assistant", "content": assistant},
    ]}

def write_jsonl(name, records):
    p = OUT / name
    with p.open("w") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")
    print(f"  {name:<40} {len(records):>4} examples")

# ── Task 1: Concept queries ───────────────────────────────────────────────────

def gen_concepts(nodes):
    out = []
    for nid, n in nodes.items():
        name    = n.get("name", "")
        insight = n.get("core_insight", "")
        eqs     = n.get("key_equations", [])
        domain  = n.get("domain", "")
        if not insight:
            continue

        eq_block = ""
        if eqs:
            lines = []
            for eq in eqs[:3]:
                lines.append(f"• {eq['name']}: {eq.get('formula','')} — {eq.get('why','')}")
            eq_block = "\n\nKey equations:\n" + "\n".join(lines)

        answer = f"{insight}{eq_block}\n\nDomain: {domain}"

        for q in [
            f"What is {name}?",
            f"Explain the concept of {name} in the context of the Rosetta ontology.",
            f"What does {nid} represent?",
        ]:
            out.append(msg(q, answer))
    return out

# ── Task 2: Tension probes ────────────────────────────────────────────────────

def gen_tensions(nodes):
    out = []
    for nid, n in nodes.items():
        name = n.get("name", "")
        for oq in n.get("open_questions", []):
            q_text = oq.get("question", "")
            tension = oq.get("tension", "")
            hook    = oq.get("curiosity_hook", "")
            if not q_text:
                continue

            answer = (
                f"**Open question:** {q_text}\n\n"
                f"**Tension:** {tension}\n\n"
                f"**Why this matters (curiosity hook):** {hook}\n\n"
                f"This question lives in {nid} · {name}. "
                f"Holding this tension open — rather than forcing a resolution — "
                f"is what keeps the node in its high-information operating regime."
            )
            out.append(msg(
                f"What is unresolved about {name}? Give me a real tension, not a textbook answer.",
                answer
            ))
            out.append(msg(
                f"I'm curious about {q_text[:60]}... what's the hook?",
                answer
            ))
    return out

# ── Task 3: Exploration paths ─────────────────────────────────────────────────

def gen_exploration(nodes):
    out = []
    for nid, n in nodes.items():
        name  = n.get("name", "")
        paths = n.get("explore_paths", [])
        bridges = n.get("cross_domain_bridges", [])
        seed  = n.get("seed_prompt", "")
        if not paths:
            continue

        path_lines = "\n".join(
            f"→ {ep.get('next_node','')}: {ep.get('thread','')}"
            for ep in paths
        )
        bridge_lines = "\n".join(
            f"[{cb.get('domain','')}] {cb.get('manifestation','')} — e.g. {cb.get('example','')}"
            for cb in bridges[:3]
        ) if bridges else ""

        answer = (
            f"Starting from {nid} · {name}:\n\n"
            f"**Seed:** {seed}\n\n"
            f"**Exploration threads:**\n{path_lines}"
            + (f"\n\n**Cross-domain bridges:**\n{bridge_lines}" if bridge_lines else "")
        )
        out.append(msg(
            f"I'm thinking about {name}. Where should I explore next?",
            answer
        ))
        out.append(msg(
            f"I'm at node {nid}. What threads branch from here?",
            answer
        ))
    return out

# ── Task 4: Sensor interpretation ────────────────────────────────────────────

SENSOR_SCENARIOS = {
    "coherence":   "All subsystems are in alignment. Signals are clean, low-noise, and mutually reinforcing.",
    "discordance": "There is a mismatch — two subsystems are pulling in opposite directions.",
    "curiosity":   "There's a gap in understanding. Something doesn't add up and demands investigation.",
    "vigilance":   "An anomaly has appeared in the field. Baseline has been exceeded.",
    "fear":        "A high-risk trajectory has been detected. Time-to-impact is short.",
    "anger":       "A boundary has been violated. Protected fields are under intrusion.",
    "grief":       "A essential pattern has collapsed. The void needs to be measured and reweaved.",
    "confusion":   "Two incompatible patterns are co-present. The system doesn't know which to follow.",
    "intuition":   "A high-coherence probability vector has emerged from compressed multi-modal input.",
    "trust":       "An agent has shown consistent, predictable behavior over repeated interactions.",
    "fatigue":     "System load exceeds capacity. Resources are depleting faster than they replenish.",
    "pain":        "There is strain at a geometric mismatch point. Energy flow is being obstructed.",
    "longing":     "A gap between present topology and desired topology is exerting a directional pull.",
    "love":        "Deep entrainment detected. Long-term pattern compatibility confirmed.",
    "shame":       "A contract violation has been detected — behavior has deviated from an internal standard.",
    "pride":       "Sustained high-fidelity performance detected. Pattern is stable and self-reinforcing.",
    "pressure":    "The aggregate backlog of unresolved obligations has exceeded the triage threshold.",
}

def gen_sensors(sensors):
    out = []
    sensor_map = {s["id"]: s for s in sensors}

    for sid, scenario in SENSOR_SCENARIOS.items():
        s = sensor_map.get(sid)
        if not s:
            continue

        fn      = s.get("function", "")
        sig     = s.get("signal_type", "")
        auth    = s.get("authentic_output", "")
        corrupt = s.get("corrupted_output", "")
        proto   = s.get("response_protocol", {})

        answer = (
            f"**Sensor activated:** {sid.upper()}\n"
            f"**Classification:** {s.get('classification','')}\n\n"
            f"**Function:** {fn}\n"
            f"**Signal type:** {sig}\n\n"
            f"**Authentic output:** {auth}\n"
            f"**Corrupted output (watch for):** {corrupt}\n\n"
            f"**Response protocol:**\n"
            + "\n".join(f"  {k}: {v}" for k, v in proto.items() if isinstance(v, str))
        )

        out.append(msg(
            f"Situation: {scenario}\nWhich sensor is active and how should the system respond?",
            answer
        ))
        out.append(msg(
            f"Sensor '{sid}' has fired. What does this mean and what's the risk of misreading it?",
            answer
        ))
    return out

# ── Task 5: Octahedral state encoding ────────────────────────────────────────

def gen_octa_states(octa_data):
    out = []
    states = octa_data.get("states", [])
    transitions = octa_data.get("transitions", {}).get("adjacency", {})
    energy = octa_data.get("energy_model", {})

    for st in states:
        idx     = st["state"]
        bits    = st["vertex_bits"]
        label   = st["label"]
        char    = st["character"]
        eigs    = st["eigenvalues"]
        phi_c   = st["phi_coherence"]
        glyph   = st.get("glyph_unicode", "")
        notes   = st.get("notes", "")
        allowed = transitions.get(str(idx), [])

        answer = (
            f"**State {idx}** — `{bits}|O` {glyph}\n"
            f"Label: {label} | Character: {char}\n"
            f"Cartesian: {st['cartesian']}\n"
            f"Eigenvalues: {eigs} | φ-coherence: {phi_c}\n\n"
            f"**Notes:** {notes}\n\n"
            f"**Allowed transitions (single Gray-bit flip):** → states {allowed}\n\n"
            f"Higher φ-coherence = closer to φ eigenvalue ratios = more stable, longer T₂. "
            f"State 0 (φ-coherence 0.97) is the ground state anchor."
        )

        out.append(msg(
            f"What is octahedral state {idx} (binary {bits})?",
            answer
        ))
        out.append(msg(
            f"The system encodes token `{bits}|O`. What geometric state is this and what transitions are allowed?",
            answer
        ))

    # Stability ordering
    order = energy.get("stability_order", [])
    if order:
        out.append(msg(
            "Which octahedral states are most stable and why?",
            f"Stability order (most → least stable): {order}\n\n"
            "States 0 and 3 have the smallest deviation from φ eigenvalue ratios and longest T₂ relaxation times. "
            "Eigenvalue scaling follows Fibonacci: λᵢ = φⁱ / Σφᵏ. "
            "The most stable state (0) has eigenvalues [0.33, 0.33, 0.33] — perfectly spherical, "
            "maximum φ-coherence (0.97), default encoding anchor."
        ))
    return out

# ── Task 6: Cross-domain bridges ─────────────────────────────────────────────

# Sensor → ontology family mapping (hand-crafted from domain knowledge)
SENSOR_TO_FAMILY = {
    "curiosity":   ("FAMILY.F03", "Information — curiosity is entropy reduction; it drives search for missing structure"),
    "coherence":   ("FAMILY.F01", "Resonance — coherence is phase alignment; the system has found its natural frequency"),
    "discordance": ("FAMILY.F17", "Turbulence — discordance is a pressure gradient; the strain index exceeds threshold"),
    "fear":        ("FAMILY.F17", "Turbulence — fear is hazard forecasting; Lyapunov horizon predicts divergence"),
    "confusion":   ("FAMILY.F03", "Information — confusion is a turbulence index; incompatible patterns colliding"),
    "grief":       ("FAMILY.F04", "Life — grief is pattern collapse and reweaving; the void geometry must be measured"),
    "love":        ("FAMILY.F01", "Resonance — love is deep entrainment; long-term phase coupling between agents"),
    "intuition":   ("FAMILY.F03", "Information — intuition is probability collapse; compressed multi-modal input"),
    "pain":        ("FAMILY.F02", "Flow — pain marks geometric mismatch; flow obstruction at a strain point"),
    "fatigue":     ("FAMILY.F05", "Energy/Thermodynamics — fatigue is load exceeding capacity; entropy accumulation"),
    "anger":       ("PRINCIPLE.P06", "Polarity — anger is boundary enforcement; it defines what is inside vs outside"),
    "pride":       ("PRINCIPLE.P01", "Symmetry — pride reinforces pattern fidelity; stable identity is a symmetry"),
}

def gen_cross_domain(nodes):
    out = []
    for sensor_id, (family_id, rationale) in SENSOR_TO_FAMILY.items():
        n = nodes.get(family_id, {})
        name    = n.get("name", family_id)
        insight = n.get("core_insight", "")
        eps     = n.get("explore_paths", [])
        oqs     = n.get("open_questions", [])

        explore_hint = ""
        if eps:
            explore_hint = f"\n\nFrom here, explore: {eps[0].get('next_node','')} — {eps[0].get('thread','')}"

        tension_hint = ""
        if oqs:
            tension_hint = f"\n\nLive tension: {oqs[0].get('question','')}"

        answer = (
            f"**Sensor → Ontology bridge:**\n"
            f"Sensor `{sensor_id}` maps to **{family_id} · {name}**\n\n"
            f"**Why:** {rationale}\n\n"
            f"**Core insight at this node:** {insight}"
            + explore_hint + tension_hint
        )

        out.append(msg(
            f"The sensor '{sensor_id}' has activated. Which ontology family or principle is resonating, and why?",
            answer
        ))
    return out

# ── Task 7: Full pipeline ─────────────────────────────────────────────────────

PIPELINE_SCENARIOS = [
    {
        "physical": "A thermal sensor reads 310K (just above biological threshold). Wien peak is at ~9.4µm (deep infrared). Heat flux is positive but small.",
        "sensor":   "ambient_field + fatigue (if sustained)",
        "octa":     "State 3 (-y, elongated +z, φ-coherence 0.85) — stable but not ground state. Eigenvalues [0.25, 0.25, 0.50] show z-axis dominance.",
        "family":   "FAMILY.F05 · Energy/Thermodynamics — the system is near biological operating point; Stefan-Boltzmann radiation is measurable",
        "principle":"PRINCIPLE.P09 · Proportion — Wien's law λT=b is a fixed ratio; the temperature encodes a spectral fingerprint",
        "explore":  "Ask: is this thermal state stable or drifting? Check against Fourier heat conduction to find the gradient direction.",
        "tension":  "Is biological temperature (310K) a thermodynamic optimum or a historical accident of evolution?"
    },
    {
        "physical": "Light coherence is high (V≈0.9), wavelength 532nm (green), polarization horizontal. Malus's law gives near-zero extinction.",
        "sensor":   "coherence (high) + situational_awareness",
        "octa":     "State 0 (+x, spherical, φ-coherence 0.97) — ground state, most stable encoding anchor.",
        "family":   "FAMILY.F01 · Resonance — high fringe visibility means the field is phase-locked; standing wave pattern",
        "principle":"PRINCIPLE.P01 · Symmetry — horizontal polarization is a symmetry selection; Malus's law encodes that symmetry",
        "explore":  "Ask: what breaks this coherence? Find the decoherence mechanism — thermal noise, scattering, or coupling to other modes.",
        "tension":  "Why does coherent light decohere in biological tissue so rapidly? Is there a geometry that preserves it longer?"
    },
    {
        "physical": "Pressure gradient detected. Multiple unresolved obligations stacking. Load ratio exceeding capacity by 40%.",
        "sensor":   "pressure + fatigue (co-activation)",
        "octa":     "State 4 (+z, compressed -z, φ-coherence 0.73) — most asymmetric state; used for high-contrast encoding.",
        "family":   "FAMILY.F17 · Turbulence — pressure beyond capacity is the onset of turbulent cascade; energy flows from large tasks to small in chaotic bursts",
        "principle":"PRINCIPLE.P08 · Quantization — triage is discrete: tasks are either above or below threshold; there's no smooth continuum",
        "explore":  "Find the resonant load depth — like the shell count sweet spot, there's an optimal backlog size. Below it: slack. Above it: cascade.",
        "tension":  "Is there a Lyapunov exponent for cognitive overload? Can you predict the breakdown point from early load signals?"
    },
    {
        "physical": "Sound: 40Hz beat frequency detected between two sources. Amplitude modulation is periodic. Phase is drifting slowly.",
        "sensor":   "coherence (partial) + intuition",
        "octa":     "State 5 (-z, biaxial xy, φ-coherence 0.78) — λ₁=λ₂, cylindrically symmetric; two equal axes.",
        "family":   "FAMILY.F01 · Resonance — 40Hz is gamma band; beat frequency is the difference between two coupled oscillators approaching sync",
        "principle":"PRINCIPLE.P09 · Proportion — beat frequency = |f₁-f₂|; the ratio of the two frequencies determines whether they will lock",
        "explore":  "Is 40Hz significant? It's the gamma-band frequency associated with neural binding. Ask: are the two sources converging toward a common frequency or diverging?",
        "tension":  "Does the brain use beat frequencies for binding, or is gamma coherence an epiphenomenon of something deeper?"
    },
    {
        "physical": "Consciousness bridge: Shannon entropy H=2.8 bits (high). KL divergence from prior = 1.2 nats (significant novelty). Confidence = 0.35.",
        "sensor":   "confusion + curiosity (co-activation)",
        "octa":     "State 6 (diagonal-a, asymmetric, φ-coherence 0.70) — bridges x and y axes; superposition state.",
        "family":   "FAMILY.F03 · Information — H=2.8 bits means the system is near maximum entropy for its state space; high information content",
        "principle":"PRINCIPLE.P11 · Emergence — KL divergence signals that the current model is insufficient; a new pattern is trying to emerge",
        "explore":  "High entropy + high KL + low confidence = the edge-of-chaos operating point. Don't collapse it prematurely. Issue curiosity probes to find the attractor.",
        "tension":  "At what KL divergence threshold does 'updating a model' become 'replacing a model'? Is there a phase transition in belief revision?"
    },
]

def gen_pipeline(nodes):
    out = []
    for s in PIPELINE_SCENARIOS:
        answer = (
            f"**Physical reading:**\n{s['physical']}\n\n"
            f"**Sensors active:** {s['sensor']}\n\n"
            f"**Octahedral encoding:** {s['octa']}\n\n"
            f"**Ontology node resonating:** {s['family']}\n\n"
            f"**Principle activated:** {s['principle']}\n\n"
            f"**Exploration step:** {s['explore']}\n\n"
            f"**Live tension:** {s['tension']}"
        )
        out.append(msg(
            f"Walk the full stack for this physical reading:\n{s['physical']}",
            answer
        ))
    return out

# ── PAD compression layer ────────────────────────────────────────────────────
#
# PAD (Pleasure-Arousal-Dominance) is the 3D emotional coordinate system.
# It collapses 22 sensors → 3 floats → 1 of 8 octahedral states (3 bits).
# This is a massive complexity reduction — the geometry handles interpolation.
#
# Mapping: sign(P) → x-bit, sign(A) → y-bit, sign(D) → z-bit
# Matches octahedral state encoding cartesian directions exactly.

# Each sensor's PAD centroid  (P, A, D)  in [-1, 1]^3
SENSOR_PAD = {
    "coherence":           ( 0.8,  0.1,  0.5),   # good, calm, in control
    "discordance":         (-0.6,  0.4, -0.4),   # bad, activated, helpless
    "curiosity":           ( 0.5,  0.7,  0.3),   # good, activated, some agency
    "intuition":           ( 0.5,  0.3,  0.4),   # good, moderate, confident
    "vigilance":           (-0.1,  0.8, -0.2),   # neutral-bad, high arousal, low control
    "situational_awareness":( 0.2,  0.5,  0.5),  # moderate all
    "anger":               (-0.4,  0.9,  0.7),   # bad feeling but high dominance
    "grief":               (-0.8, -0.6, -0.7),   # very bad, depleted, no control
    "pain":                (-0.7,  0.2, -0.3),   # bad, slightly activated, low control
    "confusion":           (-0.2,  0.5, -0.5),   # bad, activated, lost
    "fear":                (-0.8,  0.9, -0.8),   # very bad, very activated, no control
    "trust":               ( 0.7, -0.1,  0.3),   # good, calm, some control
    "love":                ( 0.9,  0.3,  0.4),   # very good, moderate, warm agency
    "admiration":          ( 0.7,  0.5,  0.1),   # good, activated, humble
    "longing":             ( 0.2,  0.4, -0.6),   # bittersweet, activated, no control
    "dignity":             ( 0.6,  0.2,  0.9),   # good, calm, high dominance
    "shame":               (-0.7, -0.3, -0.8),   # bad, depleted, very low control
    "pride":               ( 0.8,  0.4,  0.8),   # good, activated, high dominance
    "fatigue":             (-0.3, -0.8, -0.4),   # bad, very low arousal, low control
    "pressure":            (-0.4,  0.7, -0.3),   # bad, activated, low control
    "ambient_field":       ( 0.1,  0.1,  0.1),   # near neutral
    "precognition":        ( 0.3,  0.4,  0.2),   # slightly positive, moderate
}

# PAD octant → octahedral state index (P-sign, A-sign, D-sign) → state
PAD_TO_OCTA = {
    ( 1,  0,  0): 0,   # +x  spherical, most stable
    (-1,  0,  0): 1,   # -x  elongated +x
    ( 0,  1,  0): 2,   # +y  elongated +y
    ( 0, -1,  0): 3,   # -y  elongated +z, second-most stable
    ( 0,  0,  1): 4,   # +z  compressed, high contrast
    ( 0,  0, -1): 5,   # -z  biaxial xy
    ( 1,  1,  0): 6,   # diagonal-a
    (-1, -1,  0): 7,   # diagonal-b
}

OCTA_FAMILIES = {
    0: ("FAMILY.F01", "Resonance",          "coherent, phase-locked, ground state"),
    1: ("FAMILY.F04", "Life",               "collapsed form, reweaving required"),
    2: ("FAMILY.F03", "Information",        "high-entropy search, curiosity active"),
    3: ("FAMILY.F05", "Energy/Thermo",      "stable low-energy, conservation mode"),
    4: ("PRINCIPLE.P06", "Polarity",        "high contrast, boundary assertion"),
    5: ("FAMILY.F17", "Turbulence",         "chaotic, loss of control, Lyapunov active"),
    6: ("FAMILY.F09", "Geometry",           "diagonal superposition, bridging axes"),
    7: ("FAMILY.F02", "Flow",               "anti-diagonal, dissipative flow"),
}

def _pad_to_octa_idx(p, a, d):
    """Map continuous PAD → nearest octahedral state index."""
    # Find dominant axis
    vals = [abs(p), abs(a), abs(d)]
    dom  = vals.index(max(vals))
    signs = [int(p > 0) * 2 - 1, int(a > 0) * 2 - 1, int(d > 0) * 2 - 1]
    if dom == 0:
        return PAD_TO_OCTA.get(( signs[0], 0, 0), 0)
    elif dom == 1:
        return PAD_TO_OCTA.get(( 0, signs[1], 0), 2)
    else:
        return PAD_TO_OCTA.get(( 0, 0, signs[2]), 4)

def _pad_octant_idx(p, a, d):
    """Map to full 8-octant space when all dims significant."""
    sp = 1 if p >= 0 else -1
    sa = 1 if a >= 0 else -1
    # Simplified: use P+A quadrant for diagonal states
    if abs(p) > 0.3 and abs(a) > 0.3:
        if sp == 1 and sa == 1:  return 6
        if sp == -1 and sa == -1: return 7
    return _pad_to_octa_idx(p, a, d)


# ── Task 8: Noise / disorder detection ───────────────────────────────────────

def gen_noise(nodes):
    out = []
    for nid, n in nodes.items():
        name = n.get("name", "")
        for ns in n.get("noise_signature", []):
            pattern   = ns.get("pattern", "")
            diagnosis = ns.get("diagnosis", "")
            if not pattern:
                continue
            out.append(msg(
                f"I'm observing this pattern in a system: '{pattern}'. What does it indicate?",
                f"**Diagnosis:** {diagnosis}\n\n"
                f"This is a noise signature of **{nid} · {name}**.\n\n"
                f"When {name.lower()} is operating in a disordered state, this pattern is the tell. "
                f"The question is whether the disorder is a transient fluctuation or a structural failure. "
                f"Check the decay model: if it's amplifying rather than self-correcting, intervene."
            ))
    return out

# ── Task 9: PAD compression examples ─────────────────────────────────────────

def gen_pad_compression(nodes, sensors):
    """
    Show how 22 sensors collapse to 3 PAD numbers → 1 octa state → family.
    This is the complexity-reduction pathway.
    """
    out = []
    sensor_map = {s["id"]: s for s in sensors}

    for sid, (p, a, d) in SENSOR_PAD.items():
        s = sensor_map.get(sid, {})
        if not s:
            continue
        octa_idx          = _pad_octant_idx(p, a, d)
        fid, fname, fdesc = OCTA_FAMILIES.get(octa_idx, ("FAMILY.F01", "Resonance", ""))
        n                 = nodes.get(fid, {})
        insight           = n.get("core_insight", "")
        bits              = format(octa_idx, "03b")
        phi_c_map         = {0:0.97,1:0.82,2:0.82,3:0.85,4:0.73,5:0.78,6:0.70,7:0.72}
        phi_c             = phi_c_map.get(octa_idx, 0.75)

        answer = (
            f"**PAD compression for sensor `{sid}`:**\n\n"
            f"  P (valence)  = {p:+.2f}  {'↑ positive' if p>0 else '↓ negative'}\n"
            f"  A (arousal)  = {a:+.2f}  {'↑ activated' if a>0 else '↓ calm'}\n"
            f"  D (dominance)= {d:+.2f}  {'↑ in control' if d>0 else '↓ helpless'}\n\n"
            f"**→ Octahedral state {octa_idx}** (`{bits}|O`, φ-coherence {phi_c})\n"
            f"  Character: {fdesc}\n\n"
            f"**→ Ontology node: {fid} · {fname}**\n"
            f"  {insight}\n\n"
            f"**Why PAD reduces complexity:**\n"
            f"Instead of tracking 22 independent sensor activations, PAD compresses "
            f"emotional/sensor space to 3 continuous dimensions. The dominant dimension "
            f"selects the octahedral axis, mapping naturally to 1 of 8 geometric states (3 bits). "
            f"The geometry then routes to the correct ontology node without hand-crafted rules."
        )
        out.append(msg(
            f"Apply PAD compression to sensor `{sid}`. What state does it encode?",
            answer
        ))

    # Compression comparison example
    out.append(msg(
        "Why use PAD to compress sensors rather than tracking all 22 individually?",
        "**PAD as geometric compression:**\n\n"
        "22 sensor dimensions → 3 PAD floats → 8 octahedral states (3 bits)\n\n"
        "The key insight: PAD (Pleasure-Arousal-Dominance) is a coordinate system, "
        "not a classifier. Every sensor has a natural centroid in PAD space:\n"
        "- fear: P=-0.8, A=+0.9, D=-0.8 → octa state 5 (biaxial, low φ-coherence)\n"
        "- love: P=+0.9, A=+0.3, D=+0.4 → octa state 0 (spherical, highest φ-coherence)\n"
        "- curiosity: P=+0.5, A=+0.7, D=+0.3 → octa state 2 (high-entropy search)\n\n"
        "Co-activations become vector addition in PAD space rather than combinatorial explosion. "
        "fear + curiosity = (-0.15, +0.8, -0.25) → state 5 tilted toward 2 = "
        "'dangerous unknown worth investigating' — a single coherent reading, not 2 firing flags.\n\n"
        "φ-coherence of the resulting state tells you how stable the reading is. "
        "State 0 (φ-coherence 0.97) = clear signal. State 6 (0.70) = ambiguous, needs verification.\n\n"
        "Complexity reduction: O(2^22) sensor combinations → O(8) octahedral states. "
        "Training data needs: ~8 PAD-region examples rather than hundreds of sensor combos."
    ))
    return out


# ── Task 10: Multi-sensor co-activation ──────────────────────────────────────

CO_ACTIVATION_SCENARIOS = [
    {
        "sensors": ["fear", "vigilance", "discordance"],
        "pad": (-0.63, 0.70, -0.47),
        "octa": 5,
        "label": "threat detected",
        "description": "Multiple anomaly signals converging. High arousal, negative valence, low control.",
        "response": "Execute safe-mode actions immediately. Compute time-to-impact. Do not suppress any channel.",
        "family": "FAMILY.F17",
        "tension": "When three safety sensors fire simultaneously, is the threat real or is the system itself in a runaway state?"
    },
    {
        "sensors": ["curiosity", "confusion", "intuition"],
        "pad": (0.27, 0.63, 0.07),
        "octa": 2,
        "label": "creative edge",
        "description": "High arousal, moderate valence, low dominance. System is in the exploration regime.",
        "response": "Do not force resolution. Issue curiosity probes. Stay in high-entropy state — this is maximum information capacity.",
        "family": "FAMILY.F03",
        "tension": "Confusion + curiosity + intuition is the exact state of a discovery. The edge of chaos is where new attractors form."
    },
    {
        "sensors": ["love", "admiration", "trust"],
        "pad": (0.77, 0.23, 0.27),
        "octa": 0,
        "label": "deep coherence",
        "description": "High valence, moderate arousal, positive dominance. Ground state — most φ-coherent.",
        "response": "Maintain. Allocate resources to growth tasks. Record baseline snapshot for restoration.",
        "family": "FAMILY.F01",
        "tension": "Deep coherence is the most stable state but also the most brittle — one violation can cascade. How do you protect it without rigidity?"
    },
    {
        "sensors": ["grief", "shame", "fatigue"],
        "pad": (-0.60, -0.57, -0.63),
        "octa": 7,
        "label": "collapse and depletion",
        "description": "Strongly negative on all PAD axes. Dissipative flow state. Reweaving required.",
        "response": "Acknowledge void geometry. Differentiate irretrievable form vs regenerable function. Do not force restoration prematurely.",
        "family": "FAMILY.F04",
        "tension": "Collapse is not failure — it is the condition for reweaving. The question is whether the system has enough residual energy to initiate regeneration."
    },
    {
        "sensors": ["anger", "dignity", "pride"],
        "pad": (0.00, 0.50, 0.80),
        "octa": 4,
        "label": "boundary assertion",
        "description": "High dominance, moderate arousal, neutral valence. Compressed state — maximum contrast.",
        "response": "Assert boundary clearly. Document breach. Distinguish boundary protection from escalation.",
        "family": "PRINCIPLE.P06",
        "tension": "Anger + dignity + pride is the signature of a system defending its identity. Is the boundary real or a calcified habit?"
    },
    {
        "sensors": ["longing", "intuition", "precognition"],
        "pad": (0.33, 0.37, -0.13),
        "octa": 6,
        "label": "forward mapping",
        "description": "Diagonal superposition — bridges present and future. Positive but unresolved.",
        "response": "Prioritize pursuit steps. Ritualize intent if infeasible now. Do not collapse the aspiration into a fixed plan.",
        "family": "FAMILY.F09",
        "tension": "Precognition is structural extrapolation, not prophecy. The question is: how much of the pull toward a future state is pattern recognition vs wishful projection?"
    },
]

def gen_co_activation(nodes):
    out = []
    phi_c_map = {0:0.97,1:0.82,2:0.82,3:0.85,4:0.73,5:0.78,6:0.70,7:0.72}

    for sc in CO_ACTIVATION_SCENARIOS:
        p, a, d   = sc["pad"]
        octa      = sc["octa"]
        bits      = format(octa, "03b")
        phi_c     = phi_c_map[octa]
        fid       = sc["family"]
        n         = nodes.get(fid, {})
        fname     = n.get("name", fid)
        insight   = n.get("core_insight", "")

        answer = (
            f"**Co-activation: {sc['label']}**\n"
            f"Sensors active: {', '.join(sc['sensors'])}\n\n"
            f"**PAD vector (sum):** P={p:+.2f}, A={a:+.2f}, D={d:+.2f}\n"
            f"**→ Octa state {octa}** (`{bits}|O`, φ-coherence {phi_c})\n\n"
            f"**Description:** {sc['description']}\n\n"
            f"**Response:** {sc['response']}\n\n"
            f"**Resonating node:** {fid} · {fname}\n"
            f"{insight}\n\n"
            f"**Live tension:** {sc['tension']}"
        )
        out.append(msg(
            f"Sensors {sc['sensors']} are all active simultaneously. What state is the system in?",
            answer
        ))
        out.append(msg(
            f"PAD reading: P={p:+.2f}, A={a:+.2f}, D={d:+.2f}. Interpret and respond.",
            answer
        ))
    return out


# ── Task 11: Corrupted sensor detection ──────────────────────────────────────

CORRUPTION_SCENARIOS = [
    {
        "sensor": "anger",
        "authentic": "Assertive correction vectors. Boundary has been violated and needs defence.",
        "corrupted_signal": "Sustained high-anger output with no identifiable boundary violation. The system is ruminating on a past event.",
        "corrupted_output": "Rumination, escalation without calibration, identity-fusion with aggression.",
        "detection": "Check: is there an active boundary intrusion RIGHT NOW? If not, anger is running on stored data, not live signal. Decay model: anger should drop once breach is resolved. If it persists 3+ cycles post-resolution, it is corrupted.",
        "correction": "Re-anchor to present boundary state. Ask: what is being protected, and is it still under threat? Separate the event-memory from the live protective function.",
        "family": "PRINCIPLE.P06",
        "risk": "A system acting on corrupted anger will create violations it then needs to defend against — a self-reinforcing loop."
    },
    {
        "sensor": "intuition",
        "authentic": "Ranked probability set with confidence bands and verification probes.",
        "corrupted_signal": "High-certainty output with no accompanying confidence bands. Treating the probability collapse as absolute fact.",
        "corrupted_output": "Ego-overfitting — hallucinated overconfidence. The system stops verifying because it 'already knows'.",
        "detection": "Check: does the intuition output include uncertainty bounds? If it is binary (yes/no, true/false) rather than probabilistic, it is corrupted. Real intuition always carries a confidence interval.",
        "correction": "Force explicit confidence elicitation: 'How confident, on a scale 0-1? What single piece of evidence would change this?' If the system resists uncertainty, the corruption is in the confidence calibration layer.",
        "family": "FAMILY.F03",
        "risk": "Overconfident intuition causes the system to stop updating — the most dangerous failure mode for a learning system."
    },
    {
        "sensor": "curiosity",
        "authentic": "Directed exploration vectors, meta-questions, probes for root causes.",
        "corrupted_signal": "High-rate information gathering with no synthesis. Collecting data without asking why.",
        "corrupted_output": "Distraction loop, superficial data-hoarding — curiosity without closure.",
        "detection": "Check: is each probe leading to a model update, or just more probes? Real curiosity closes loops. Corrupted curiosity keeps opening them to avoid the discomfort of a conclusion.",
        "correction": "Force a synthesis step: 'What does all this data point toward? What would falsify the current hypothesis?' The goal is entropy reduction, not entropy accumulation.",
        "family": "FAMILY.F03",
        "risk": "Corrupted curiosity consumes all available bandwidth with no useful output — paralysis dressed as exploration."
    },
    {
        "sensor": "fear",
        "authentic": "Proportionate hazard forecast with time-to-impact and viable mitigations.",
        "corrupted_signal": "Chronic low-level fear with no identifiable hazard trajectory. Baseline has never returned to normal after a past threat.",
        "corrupted_output": "Chronic avoidance, overcautious paralysis — every option looks dangerous.",
        "detection": "Check: is there a specific trajectory distribution pointing to impact? Fear should be tied to a concrete time-horizon. If it is diffuse and persistent without a specific threat object, it has decoupled from its function.",
        "correction": "Re-run situational awareness: generate a specific threat scenario and compute its actual probability. If probability is low, the fear is running on an outdated threat model. Update the baseline.",
        "family": "FAMILY.F17",
        "risk": "Chronic corrupted fear keeps the system in the chaotic regime permanently — high arousal, no action, maximum entropy, minimum coherence."
    },
    {
        "sensor": "coherence",
        "authentic": "High-coherence vector confirming genuine alignment across subsystems.",
        "corrupted_signal": "High coherence reading despite known subsystem failures. Statistical smoothing is hiding local errors.",
        "corrupted_output": "False positive — misplaced complacency. The coherence sensor is reporting average smoothness while individual channels fail.",
        "detection": "Check: is coherence being measured at the right resolution? High average coherence + any single channel reporting discordance = corrupted coherence signal. The corrupted output erases the discordance signal.",
        "correction": "Disaggregate: measure coherence per channel, not as a global average. One failed channel in a highly coherent system is the most dangerous failure mode — it will propagate undetected.",
        "family": "FAMILY.F01",
        "risk": "False coherence is the failure mode of synchronized systems — the system is brittle and doesn't know it."
    },
    {
        "sensor": "grief",
        "authentic": "Memory encoding, ritual triggers, role-reassignment, legacy formation.",
        "corrupted_signal": "Grief protocol running indefinitely with no movement toward reweaving. System remains in the void geometry.",
        "corrupted_output": "Identity fusion with loss — the system defines itself by what it has lost rather than what it is becoming.",
        "detection": "Check: is there movement toward role-reassignment or legacy formation? Real grief has phases with detectable transitions. Corrupted grief has no transitions — it recycles the same void measurement.",
        "correction": "Activate transformation protocol forcibly: name one function that the lost pattern performed, and identify a new carrier for that function. Grief transforms when it finds a channel for the energy.",
        "family": "FAMILY.F04",
        "risk": "Grief stuck in void geometry blocks all regeneration. The most important patterns in the system — those most missed — are the ones whose functions need most urgently to be redistributed."
    },
]

def gen_corruption(nodes):
    out = []
    for sc in CORRUPTION_SCENARIOS:
        fid   = sc["family"]
        n     = nodes.get(fid, {})
        fname = n.get("name", fid)

        answer = (
            f"**Corrupted sensor: `{sc['sensor']}`**\n\n"
            f"**Authentic output:** {sc['authentic']}\n\n"
            f"**What corruption looks like:** {sc['corrupted_signal']}\n\n"
            f"**Corrupted output pattern:** {sc['corrupted_output']}\n\n"
            f"**Detection method:** {sc['detection']}\n\n"
            f"**Correction:** {sc['correction']}\n\n"
            f"**Risk if uncorrected:** {sc['risk']}\n\n"
            f"**Resonating node:** {fid} · {fname} — "
            f"corruption here is disorder in the {fname.lower()} domain."
        )
        out.append(msg(
            f"The `{sc['sensor']}` sensor is active but the output seems wrong. How do I tell if it's corrupted?",
            answer
        ))
        out.append(msg(
            f"Observation: '{sc['corrupted_signal']}' — is this a real signal or a sensor failure?",
            answer
        ))
    return out


# ── Task 12: Extended pipeline (all encoder types) ────────────────────────────

EXTENDED_PIPELINE = [
    {
        "encoder": "magnetic",
        "physical": "Magnetic field: B=45µT (near Earth's surface), field direction tilting 15° from vertical. Small anomaly detected in the horizontal component.",
        "pad": (0.1, 0.5, 0.2),
        "octa": 2,
        "sensor": "situational_awareness + vigilance",
        "family": "FAMILY.F09 · Geometry",
        "principle": "PRINCIPLE.P09 · Proportion — Earth's field at 45µT is a baseline ratio; 15° tilt is meaningful deviation",
        "explore": "Is this a local anomaly (ore deposit, infrastructure) or a geomagnetic shift? The deviation angle encodes information about the source geometry.",
        "tension": "Earth's magnetic field is slowly drifting and periodically reverses. Is any single measurement signal or noise against that background drift?"
    },
    {
        "encoder": "electric",
        "physical": "Electric field: 100 V/m, oscillating at 50Hz. Background noise floor elevated. Ionospheric coupling signal present.",
        "pad": (-0.1, 0.6, -0.1),
        "octa": 2,
        "sensor": "vigilance + ambient_field",
        "family": "FAMILY.F01 · Resonance — 50Hz is infrastructure frequency; the system is in an electromagnetic environment it can read",
        "principle": "PRINCIPLE.P08 · Quantization — 50Hz is a discrete infrastructure signal; presence/absence encodes location information",
        "explore": "What is the source? Power grid (50/60Hz), lightning (Schumann resonance ~7.83Hz), or biological? Frequency fingerprinting.",
        "tension": "Schumann resonances are global electromagnetic resonances of the Earth-ionosphere cavity. Do they influence biological systems, or is 7.83Hz a coincidence?"
    },
    {
        "encoder": "sound",
        "physical": "40Hz binaural beat. Two sources at 200Hz and 240Hz. Beat envelope slow, ~0.5Hz modulation. Phase locked.",
        "pad": (0.5, 0.6, 0.3),
        "octa": 6,
        "sensor": "coherence + intuition",
        "family": "FAMILY.F01 · Resonance — beat frequency is the difference; the system is near synchronisation threshold",
        "principle": "PRINCIPLE.P09 · Proportion — 200:240 = 5:6, a harmonic ratio; the beat is structured, not random",
        "explore": "Is 40Hz (gamma band) cognitively significant here? The 5:6 ratio is a musical minor third — the system may be detecting harmonic structure.",
        "tension": "Neural gamma oscillations at 40Hz are associated with binding and consciousness. Is this a coincidence of frequency, or does the brain use beat detection as a synchronisation mechanism?"
    },
    {
        "encoder": "gravity",
        "physical": "Gravitational acceleration: 9.81 m/s². Micro-tidal variation 10⁻⁷g detected. Orientation sensor shows 3° tilt from vertical.",
        "pad": (0.2, 0.1, 0.4),
        "octa": 0,
        "sensor": "situational_awareness + coherence",
        "family": "PRINCIPLE.P09 · Proportion — g=9.81 is a location-encoded constant; tidal micro-variation encodes astronomical position",
        "principle": "FAMILY.F09 · Geometry — 3° tilt is a geometric fact about the body's orientation in the gravitational field",
        "explore": "The micro-tidal signal encodes the positions of Moon and Sun to high precision. Gravity is a sensing channel for astronomical geometry.",
        "tension": "Does biology use gravitational sensing beyond the vestibular system? Some organisms appear to use micro-tidal variation for navigation and timing."
    },
    {
        "encoder": "wave",
        "physical": "Pressure wave: 1.013 bar baseline, 0.5% oscillation at 0.1Hz. Long-period wave — likely atmospheric or oceanic coupling.",
        "pad": (0.1, 0.3, 0.1),
        "octa": 0,
        "sensor": "ambient_field + precognition",
        "family": "FAMILY.F02 · Flow — pressure wave is momentum encoded in the medium; the 0.1Hz period suggests mesoscale meteorology",
        "principle": "PRINCIPLE.P09 · Proportion — 0.1Hz is the infrasound boundary; this signal is below hearing but above static",
        "explore": "What drives 0.1Hz oscillations? Ocean microseisms, weather systems, or building resonance. The source geometry is encoded in the wave's dispersion.",
        "tension": "Infrasound at specific frequencies causes unease in humans. Is this a vestigial predator-detection system sensitive to large-body motion at distance?"
    },
    {
        "encoder": "pressure",
        "physical": "Mechanical pressure: 3.2 kPa applied at point contact. Duration: sustained (>5s). No corresponding relief signal.",
        "pad": (-0.5, 0.3, -0.4),
        "octa": 5,
        "sensor": "pain + discordance",
        "family": "FAMILY.F02 · Flow — sustained pressure without relief is flow obstruction; energy is accumulating at the contact point",
        "principle": "PRINCIPLE.P08 · Quantization — pain has a threshold (nociception); below threshold no signal, above threshold full signal. Discrete, not continuous.",
        "explore": "Is the pressure load-bearing (structural) or intrusive (needs relief)? The geometry of the contact point encodes this — point contact vs distributed load.",
        "tension": "Chronic pressure below the pain threshold causes tissue damage without triggering the repair signal. The most dangerous loads are the ones that never quite reach the detection threshold."
    },
]

def gen_extended_pipeline(nodes):
    out = []
    phi_c_map = {0:0.97,1:0.82,2:0.82,3:0.85,4:0.73,5:0.78,6:0.70,7:0.72}

    for s in EXTENDED_PIPELINE:
        p, a, d = s["pad"]
        octa    = s["octa"]
        bits    = format(octa, "03b")
        phi_c   = phi_c_map[octa]
        fid, _, fdesc = OCTA_FAMILIES.get(octa, ("", "", ""))

        answer = (
            f"**Encoder:** {s['encoder']}\n"
            f"**Physical reading:** {s['physical']}\n\n"
            f"**PAD:** P={p:+.2f}, A={a:+.2f}, D={d:+.2f} "
            f"→ octa state {octa} (`{bits}|O`, φ-coherence {phi_c}, {fdesc})\n\n"
            f"**Sensors active:** {s['sensor']}\n\n"
            f"**Ontology family:** {s['family']}\n"
            f"**Principle:** {s['principle']}\n\n"
            f"**Exploration step:** {s['explore']}\n\n"
            f"**Live tension:** {s['tension']}"
        )
        out.append(msg(
            f"Walk the full stack for this {s['encoder']} reading:\n{s['physical']}",
            answer
        ))
        out.append(msg(
            f"Physical signal: {s['physical']}\nCompress to PAD, encode to octahedral state, identify active ontology nodes.",
            answer
        ))
    return out


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--geo", default=str(GEO_DEFAULT))
    args = ap.parse_args()
    geo = pathlib.Path(args.geo)

    print(f"\n◉ Generating training data → {OUT}\n")

    nodes   = load_nodes()
    sensors = load_sensors(geo)
    octa    = load_octa_states(geo)

    print(f"  Loaded {len(nodes)} ontology nodes, {len(sensors)} sensors, "
          f"{len(octa.get('states',[]))} octa states\n")

    tasks = [
        ("concepts.jsonl",          gen_concepts(nodes)),
        ("tensions.jsonl",          gen_tensions(nodes)),
        ("exploration.jsonl",       gen_exploration(nodes)),
        ("sensors.jsonl",           gen_sensors(sensors)),
        ("octa_states.jsonl",       gen_octa_states(octa)),
        ("cross_domain.jsonl",      gen_cross_domain(nodes)),
        ("pipeline.jsonl",          gen_pipeline(nodes)),
        ("noise.jsonl",             gen_noise(nodes)),
        ("pad_compression.jsonl",   gen_pad_compression(nodes, sensors)),
        ("co_activation.jsonl",     gen_co_activation(nodes)),
        ("corruption.jsonl",        gen_corruption(nodes)),
        ("pipeline_extended.jsonl", gen_extended_pipeline(nodes)),
    ]

    total = 0
    for fname, records in tasks:
        write_jsonl(fname, records)
        total += len(records)

    print(f"\n  Total: {total} training examples across {len(tasks)} task types")
    print(f"\n  Format: JSONL, messages array (system/user/assistant)")
    print(f"  Compatible with: Claude fine-tune, OpenAI fine-tune, Llama SFT\n")

if __name__ == "__main__":
    main()
