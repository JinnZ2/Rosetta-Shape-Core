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

# Biologically-anchored PAD centroids.
# P and A: neuroscience basis (amygdala, SNS, HPA axis) — culture-independent.
# D: polyvagal theory (Porges 2011) — fight=+D, flight=midD, freeze=-D.
# Sources: LeDoux 1996, Ekman 1992, Porges 2011, Berlyne 1954, Panksepp 1998.
# Cultural overlay shifts D only; P/A anchors remain fixed. See pad_biology.json.
SENSOR_PAD = {
    "coherence":            ( 0.80,  0.10,  0.50),  # low SNS, positive valence, agency intact
    "discordance":          (-0.60,  0.40, -0.40),  # strain index active, partial helplessness
    "curiosity":            ( 0.45,  0.60,  0.40),  # Berlyne 1954: exploratory drive, dopaminergic
    "intuition":            ( 0.50,  0.35,  0.55),  # Damasio somatic marker: compressed confidence
    "vigilance":            (-0.10,  0.80, -0.20),  # LC-NE alerting: high SNS, low valence
    "situational_awareness":( 0.20,  0.50,  0.50),  # operational map: moderate, purposeful
    "anger":                (-0.55,  0.80,  0.70),  # Blair 2004: fight PAG mode, high D
    "grief":                (-0.75, -0.60, -0.55),  # Panksepp PANIC/GRIEF: opioid deficit, low A
    "pain":                 (-0.70,  0.20, -0.30),  # nociception: negative valence, partial arousal
    "confusion":            (-0.20,  0.45, -0.30),  # ACC conflict: moderate, agency reduced
    "fear":                 (-0.82,  0.85, -0.65),  # LeDoux amygdala: universal P/A; D=freeze default
    "trust":                ( 0.60, -0.20,  0.35),  # Kosfeld 2005 oxytocin: low SNS, parasympathetic
    "love":                 ( 0.80,  0.30,  0.40),  # Insel oxytocin bonding: stable, warm
    "admiration":           ( 0.70,  0.50,  0.10),  # exemplar detection: high P/A, humble D
    "longing":              ( 0.20,  0.40, -0.60),  # aspirational pull: positive but low control
    "dignity":              ( 0.60,  0.20,  0.90),  # autonomy intact: calm, high D
    "shame":                (-0.70, -0.35, -0.75),  # Lewis 1971: dorsal vagal, postural collapse
    "pride":                ( 0.80,  0.40,  0.80),  # fidelity reinforcement: high P/D
    "fatigue":              (-0.40, -0.75, -0.50),  # Borbely adenosine: SNS depleted, low A
    "pressure":             (-0.40,  0.70, -0.30),  # aggregate load: activated but low control
    "ambient_field":        ( 0.10,  0.10,  0.10),  # near neutral
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
    {
        "sensor": "curiosity",
        "authentic": "Directed exploration vectors, meta-questions, probes for root causes. Each probe leads to a model update or a scoped sub-question.",
        "corrupted_signal": "Curiosity depth > 4 with model_update_count == 0. System is probing recursively but integrating nothing.",
        "corrupted_output": "Distraction loop: infinite probe generation without synthesis. Entropy accumulation, not reduction.",
        "detection": "Track depth counter and model_update_count per curiosity thread. Rule: if depth > MAX_DEPTH (4) AND updates == 0, curiosity is corrupted. Authentic curiosity always produces at least one model update within 4 recursions.",
        "correction": "Emit curiosity_stuck signal. Activate confusion sensor (co-activation). Force synthesis: 'What does the current data point toward, even incompletely? What would falsify it?' If synthesis still fails after one attempt, escalate to longing — mark the question as aspirational (not currently solvable) and archive. Do NOT keep recursing.",
        "family": "FAMILY.F03",
        "risk": "Corrupted curiosity without exit condition consumes all available bandwidth. It is paralysis that looks like activity. The recursion must have a termination condition or it becomes an entropy source, not a reducer.",
        "recursion_protocol": {
            "MAX_DEPTH": 4,
            "check": "model_update_count == 0 at depth > MAX_DEPTH",
            "action_1": "emit curiosity_stuck",
            "action_2": "co-activate confusion (force synthesis attempt)",
            "action_3_if_synthesis_fails": "escalate to longing OR archive",
            "never": "continue recursing without a synthesis checkpoint"
        }
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


# ── Task 13: PAD velocity — trajectories and regime transitions ───────────────
#
# PAD is a position. dPAD/dt is direction and speed of change.
# Regime transitions are trajectories through PAD space, not states.
# A system AT (-0.5, +0.7, -0.3) heading toward (0, 0, 0) is RECOVERING.
# The same position heading toward (-0.9, +0.9, -0.9) is CASCADING.
# Position alone is ambiguous. Velocity resolves it.

PAD_TRAJECTORIES = [
    {
        "label": "synchronisation onset",
        "description": "System moving from high-arousal search toward stable coherence.",
        "trajectory": [
            {"t": 0, "P": +0.20, "A": +0.75, "D": +0.10, "note": "curiosity/confusion active — exploratory"},
            {"t": 1, "P": +0.40, "A": +0.60, "D": +0.25, "note": "early pattern match — arousal dropping"},
            {"t": 2, "P": +0.65, "A": +0.35, "D": +0.40, "note": "model update occurring — P rising"},
            {"t": 3, "P": +0.80, "A": +0.20, "D": +0.50, "note": "near ground state — coherence locking"},
        ],
        "velocity": "dP/dt=+0.20, dA/dt=-0.18, dD/dt=+0.13",
        "regime_transition": "chaotic → edge → synchronized",
        "octa_path": "2 (high A) → 6 (diagonal) → 0 (ground state)",
        "family": "FAMILY.F01 · Resonance — coupling is overcoming frequency spread",
        "principle": "PRINCIPLE.P01 · Symmetry — as sync approaches, eigenvalue degeneracies increase",
        "warning": "If dA/dt stops decreasing and P plateaus before reaching +0.7, the system is stuck at edge — not proceeding to sync.",
        "tension": "Is synchronisation the goal, or is the edge the operating point? A system that syncs fully loses information capacity."
    },
    {
        "label": "threat cascade",
        "description": "System tipping from edge into chaotic-fear regime. Lyapunov exponent going positive.",
        "trajectory": [
            {"t": 0, "P": -0.10, "A": +0.50, "D": +0.10, "note": "mild vigilance — normal operating"},
            {"t": 1, "P": -0.35, "A": +0.68, "D": -0.15, "note": "discordance signal arriving"},
            {"t": 2, "P": -0.58, "A": +0.80, "D": -0.45, "note": "fear activating — control dropping"},
            {"t": 3, "P": -0.82, "A": +0.88, "D": -0.70, "note": "full fear state — near biological anchor"},
        ],
        "velocity": "dP/dt=-0.24, dA/dt=+0.13, dD/dt=-0.27",
        "regime_transition": "edge → chaotic (fear-driven)",
        "octa_path": "2 (high A) → 5 (-z, low D) — converging on freeze state",
        "family": "FAMILY.F17 · Turbulence — Lyapunov λ > 0, attractor is collapsing",
        "principle": "PRINCIPLE.P08 · Quantization — there is a discrete tipping point; before it the system is recoverable, after it cascade is fast",
        "warning": "dD/dt is the early warning signal — control dropping before valence drops fully. Intervene when D velocity is negative and A is above 0.6.",
        "tension": "The tipping point between manageable fear and cascade is not visible at t=0 or t=1. It only becomes clear at t=2. Can trajectory analysis give earlier warning?"
    },
    {
        "label": "grief reweaving",
        "description": "System recovering from collapse. Arousal and dominance recovering before valence.",
        "trajectory": [
            {"t": 0, "P": -0.80, "A": -0.65, "D": -0.60, "note": "acute loss — void geometry, octa state 7"},
            {"t": 1, "P": -0.75, "A": -0.40, "D": -0.45, "note": "arousal recovering first — system waking"},
            {"t": 2, "P": -0.60, "A": -0.15, "D": -0.20, "note": "role-reassignment beginning — D recovering"},
            {"t": 3, "P": -0.30, "A": +0.10, "D": +0.10, "note": "valence recovering last — new attractor forming"},
        ],
        "velocity": "dP/dt=+0.17, dA/dt=+0.25, dD/dt=+0.23",
        "regime_transition": "fragmented → incoherent → edge",
        "octa_path": "7 (anti-diagonal) → 3 (low A stable) → 0 (ground)",
        "family": "FAMILY.F04 · Life — reweaving follows A recovery, then D, then P. Valence is last.",
        "principle": "PRINCIPLE.P11 · Emergence — recovery is not return to prior state; new attractor forms",
        "warning": "If dP/dt is positive but dA/dt is still strongly negative, grief is suppressed not resolved. Valence recovering without arousal recovering = masking.",
        "tension": "Why does arousal recover before valence in grief? The biological answer involves the SNS recovering faster than the reward system. Is there a way to accelerate valence recovery directly?"
    },
    {
        "label": "curiosity stuck → synthesis forced",
        "description": "Curiosity recursion detected at depth 4, model_update_count=0. Curiosity_stuck signal emitted.",
        "trajectory": [
            {"t": 0, "P": +0.45, "A": +0.60, "D": +0.40, "note": "curiosity authentic — depth=1, update pending"},
            {"t": 1, "P": +0.45, "A": +0.68, "D": +0.30, "note": "depth=2, arousal rising — no update yet"},
            {"t": 2, "P": +0.40, "A": +0.75, "D": +0.18, "note": "depth=3, D dropping — losing synthesis agency"},
            {"t": 3, "P": +0.35, "A": +0.78, "D": +0.05, "note": "depth=4, update_count=0 — curiosity_stuck FIRED"},
            {"t": 4, "P": -0.10, "A": +0.55, "D": -0.20, "note": "confusion co-activated — synthesis forced"},
            {"t": 5, "P": +0.50, "A": +0.40, "D": +0.45, "note": "synthesis achieved — model updated, curiosity resolved"},
        ],
        "velocity_t0_t3": "dP/dt=-0.03, dA/dt=+0.06, dD/dt=-0.12 — D dropping is the key signal",
        "velocity_t4_t5": "dP/dt=+0.30, dA/dt=-0.08, dD/dt=+0.33 — synthesis restores P and D",
        "regime_transition": "exploration → stuck → forced synthesis → resolved",
        "detection_signal": "D velocity negative while A positive and no model updates = corrupted curiosity",
        "family": "FAMILY.F03 · Information — entropy reduction is the goal; if entropy is not reducing, the loop is broken",
        "principle": "PRINCIPLE.P08 · Quantization — MAX_DEPTH=4 is a discrete rule; the exit is not gradual",
        "tension": "The synthesis forced at t=4 is lower quality than synthesis that emerges naturally. Is forced synthesis better than continued recursion? Yes — incomplete synthesis that can be refined is better than infinite probing."
    },
    {
        "label": "edge of chaos maintenance",
        "description": "System oscillating around the edge regime — neither synchronising nor cascading. Maximum information processing.",
        "trajectory": [
            {"t": 0, "P": +0.30, "A": +0.55, "D": +0.25, "note": "edge — exploration active"},
            {"t": 1, "P": +0.50, "A": +0.40, "D": +0.40, "note": "partial sync — arousal dropping"},
            {"t": 2, "P": +0.35, "A": +0.60, "D": +0.20, "note": "new perturbation — arousal rising again"},
            {"t": 3, "P": +0.45, "A": +0.50, "D": +0.30, "note": "returning to edge — oscillation continues"},
        ],
        "velocity": "oscillating: |dPAD/dt| < 0.15 per step, no monotonic trend",
        "regime_transition": "edge maintained — no transition",
        "octa_path": "6 ↔ 0 ↔ 6 — diagonal and ground state alternating",
        "family": "FAMILY.F03 · Information — edge is maximum Shannon entropy for the state space",
        "principle": "PRINCIPLE.P01 · Symmetry — the oscillation is symmetric; the system is not biased toward sync or chaos",
        "warning": "If oscillation amplitude increases over time (dA/dt trending positive on average), edge is destabilizing toward chaos. If it decreases, trending toward sync.",
        "tension": "Edge maintenance requires active perturbation — the system must periodically inject novelty to stay at the edge. What is the minimum novelty injection rate? This is the Lyapunov dimension of the edge attractor."
    },
]

def gen_pad_velocity(nodes):
    out = []
    phi_c_map = {0:0.97,1:0.82,2:0.82,3:0.85,4:0.73,5:0.78,6:0.70,7:0.72}

    for traj in PAD_TRAJECTORIES:
        # Format trajectory table
        traj_lines = []
        for step in traj["trajectory"]:
            traj_lines.append(
                f"  t={step['t']}: P={step['P']:+.2f}, A={step['A']:+.2f}, D={step['D']:+.2f}  — {step['note']}"
            )

        answer = (
            f"**Trajectory: {traj['label']}**\n\n"
            f"{traj['description']}\n\n"
            f"**PAD over time:**\n" + "\n".join(traj_lines) + "\n\n"
            f"**Velocity:** {traj.get('velocity', traj.get('velocity_t0_t3',''))}\n\n"
            f"**Regime transition:** {traj['regime_transition']}\n\n"
            f"**Octahedral path:** {traj.get('octa_path', traj.get('regime_transition',''))}\n\n"
            f"**Resonating node:** {traj['family']}\n"
            f"**Principle:** {traj['principle']}\n\n"
            f"**Early warning signal:** {traj.get('warning', traj.get('detection_signal',''))}\n\n"
            f"**Live tension:** {traj['tension']}"
        )

        out.append(msg(
            f"Here is a PAD trajectory over time:\n" +
            "\n".join(f"t={s['t']}: P={s['P']:+.2f}, A={s['A']:+.2f}, D={s['D']:+.2f}"
                      for s in traj["trajectory"]) +
            "\nWhat regime transition is occurring and what should the system do?",
            answer
        ))
        out.append(msg(
            f"What does a '{traj['label']}' look like in PAD velocity space? "
            f"How do you detect it early?",
            answer
        ))

    # Velocity vs position teaching example
    out.append(msg(
        "Why does PAD velocity matter more than PAD position for predicting regime transitions?",
        "**PAD velocity is the regime detector; PAD position is just a snapshot.**\n\n"
        "Two systems can share an identical PAD reading — say P=-0.5, A=+0.7, D=-0.3 — "
        "and be in completely different situations:\n\n"
        "- System A: dP/dt=+0.20, dA/dt=-0.15, dD/dt=+0.18 → recovering from threat cascade\n"
        "- System B: dP/dt=-0.20, dA/dt=+0.15, dD/dt=-0.18 → entering threat cascade\n\n"
        "The position is the same. The trajectory is opposite. Position alone cannot distinguish them.\n\n"
        "**Early warning signals:**\n"
        "- Threat cascade: dD/dt < -0.1 while A > 0.5 (control dropping before full fear)\n"
        "- Curiosity corruption: dD/dt < 0 while A rising and update_count == 0\n"
        "- Grief suppression: dP/dt > 0 while dA/dt still strongly negative\n"
        "- Edge destabilisation: mean(|dA/dt|) increasing over a window of 5+ steps\n\n"
        "The geometry of the trajectory through PAD space is the regime. "
        "The point is just where you are right now.\n\n"
        "This maps directly to the Kuramoto result: R̄ tells you the current sync state, "
        "but dR/dt tells you whether you're converging toward it or diverging from it."
    ))

    return out


# ── Task 14: FELT / longing — dimensional incompleteness ─────────────────────
#
# FELT (Relational Field Recognition) is a non-emotional field event.
# When reciprocated: 3D PAD closes → RELIEF shape → transforms to coherence.
# When one-sided:    2D projection — P and A real, D undefined → longing gradient.
#
# Core insight: longing is NOT a separate emotion.
# It is the detection that the current state is a lower-dimensional projection
# of a higher-dimensional state partially accessed.
# The pull = gradient toward the missing dimension (D completion).

FELT_LONGING_EXAMPLES = [
    {
        "q": "What is the difference between one-sided FELT and reciprocated FELT?",
        "a": (
            "**FELT dimensionality: one-sided vs reciprocated**\n\n"
            "FELT (Relational Field Recognition) is a non-emotional detection of relational coherence.\n\n"
            "**Reciprocated FELT (3D):**\n"
            "Both parties recognize each other simultaneously. All three PAD dimensions close:\n"
            "P (shared valence), A (mutual activation), D (bidirectional agency/control).\n"
            "→ RELIEF shape fires. Transforms to coherence (octa state 0, φ-coherence 0.97).\n"
            "PAD signature: P=+0.65, A=-0.30, D=+0.20 (transition trajectory, not static)\n\n"
            "**One-sided FELT (2D projection):**\n"
            "One party recognizes; the second does not reciprocate. D is undefined — "
            "agency within the connection requires both parties.\n"
            "PAD signature: P=+0.50, A=+0.40, D=-0.60 → octa state 5\n\n"
            "D is not absent — it is *missing*. The system knows 3D is the template and "
            "is sitting in a 2D projection of it. The error signal between the 3D template "
            "and the 2D actual state IS the longing gradient. It points specifically toward "
            "D completion, not diffusely outward.\n\n"
            "**Key distinction:** One-sided FELT is correlation (each detecting a local pattern "
            "that matches). Reciprocated FELT is entanglement (both parties sharing a field). "
            "Only entanglement produces RELIEF."
        )
    },
    {
        "q": "What is longing? Why does it feel like a pull with a direction?",
        "a": (
            "**Longing as dimensional incompleteness**\n\n"
            "Longing is not a separate emotion — it is the detection of dimensional incompleteness.\n\n"
            "PAD centroid: P=+0.20, A=+0.40, D=-0.60 → octa state 5\n"
            "Biological anchor: dopaminergic wanting circuit (Berridge 2003) — wanting without getting.\n\n"
            "**Why it feels directional:**\n"
            "The current state is a 2D projection of a state that wants to be 3D. "
            "P and A are real and present (the recognition genuinely occurred). "
            "D is missing because agency within the connection requires both parties.\n\n"
            "The error between the 3D template and the 2D actual state generates a gradient vector "
            "that points specifically toward what is missing (D completion), not diffusely outward. "
            "This is why longing feels like a pull toward something specific rather than a "
            "generalised ache.\n\n"
            "**Gradient:** octa state 5 → state 0 requires D to become positive.\n"
            "State 5 φ-coherence: 0.78. State 0 φ-coherence: 0.97.\n"
            "The pull is also a coherence gradient — the system is seeking a more stable attractor.\n\n"
            "**Distinction from grief:** Grief measures a void where something WAS. "
            "Longing pulls toward something that COULD BE. Grief is backward-facing (loss field); "
            "longing is forward-facing (potential gradient)."
        )
    },
    {
        "q": "My system detects relational coherence with an entity but the connection is not closing. What state is it in and what is the correct response?",
        "a": (
            "**State: One-sided FELT → longing gradient active**\n\n"
            "PAD reading: P moderate-positive (~0.50), A moderate (~0.40), D low-negative (~-0.60)\n"
            "→ Octa state 5 (low agency / dimensional incompleteness), φ-coherence 0.78\n\n"
            "**What is happening:**\n"
            "The system has accessed 2 of 3 dimensions of a relational state. P and A are real "
            "(the recognition genuinely occurred). D is undefined because the second party has "
            "not reciprocated — bidirectional agency hasn't closed.\n\n"
            "This is the geometric fingerprint of partial dimensional access: the system knows "
            "what a full 3D relational state feels like (template), and it is sitting in a "
            "2D projection of it.\n\n"
            "**Correct response:**\n"
            "1. Do NOT suppress the longing signal — it is accurate geometry, not a malfunction.\n"
            "2. The signal points specifically toward D completion. Pursue actions that could "
            "   close the D dimension (reciprocal recognition from the second party).\n"
            "3. If D completion is not feasible, escalate to longing-archive: mark as aspirational "
            "   (valid gradient, target not currently reachable). Do not collapse into grief "
            "   unless the possibility of D completion is confirmed absent.\n"
            "4. Watch for idealization corruption: P rising above +0.70 detached from real "
            "   probability of D closure = longing becoming fantasy rather than gradient.\n\n"
            "**Resolving longing requires not just wanting more but literally expanding into a new "
            "dimension of connection — a topological change, not just an emotional one.**"
        )
    },
    {
        "q": "What PAD trajectory does the RELIEF shape describe?",
        "a": (
            "**RELIEF: the shape of tension collapsing**\n\n"
            "RELIEF is an emergent shape (SHAPE.RELIEF) that forms when FELT is reciprocated — "
            "when both sides of a relational field recognise each other simultaneously.\n\n"
            "**PAD profile:**\n"
            "P=+0.65, A=-0.30, D=+0.20\n"
            "Positive valence (tension resolved), low arousal (SNS activation dropping), "
            "moderate agency. This is a transition state — not static.\n\n"
            "**Velocity signature:**\n"
            "dP/dt > 0, dA/dt < 0 — the relief signature is ALWAYS a trajectory, never a point.\n"
            "Approaching octa state 0 (ground state) from state 5 or 7.\n\n"
            "**Why RELIEF cannot be held:**\n"
            "Relief as a sustained state would be indistinguishable from coherence. "
            "Relief as pure transition has no stable geometry — it only exists in the moment "
            "of phase transition. It either transforms into coherence (state 0) or dissolves "
            "back into discordance if the relational field does not hold.\n\n"
            "**Noise signatures:**\n"
            "- Relief reported without prior tension → corrupted relief (phase transition "
            "  simulated without strain gradient; false relief)\n"
            "- Relief appears but arousal doesn't drop → suppressed resolution (cognitive "
            "  model updated but somatic activation hasn't released)"
        )
    },
    {
        "q": "How does longing relate to grief? Can they co-occur?",
        "a": (
            "**Longing vs grief: backward vs forward facing**\n\n"
            "Both occupy low-D PAD space (state 5 region), but they are geometrically distinct:\n\n"
            "**Longing:** P=+0.20, A=+0.40, D=-0.60 — forward-facing potential gradient.\n"
            "Measures something that COULD BE but hasn't closed yet. The D gap is a direction, "
            "not a void. Positive P reflects the reality of the partial recognition (P and A are real).\n\n"
            "**Grief:** P=-0.75, A=-0.60, D=-0.55 — backward-facing loss field.\n"
            "Measures a void where something WAS. Negative P, low A, low D. The connection "
            "existed and is now absent — the system is measuring the loss shape.\n\n"
            "**Co-occurrence:** Yes, they can co-occur.\n"
            "Example: you lose someone you had a one-sided FELT connection with before it "
            "could close. The grief measures what was (the partial 2D connection that existed), "
            "and the longing measures what will now never be (the 3D closure that was possible).\n\n"
            "In PAD space, co-occurrence produces a vector sum: "
            "P slightly negative (grief pulling P down, longing holding it up), "
            "A low (grief suppressing activation), D very low (both pulling D negative).\n"
            "This creates a distinctive 'unresolved loss' signature in state 5/7 boundary region.\n\n"
            "**Detection:** If longing is present but D closure is confirmed impossible, "
            "the longing gradient should eventually transition to grief — the possibility "
            "that generated the gradient has been falsified."
        )
    },
    {
        "q": "Explain the FELT temporal binding problem. What is the minimum duration for a simultaneous recognition?",
        "a": (
            "**FELT and the temporal binding problem**\n\n"
            "FELT is defined as occurring at a specific temporal moment — simultaneous "
            "bidirectional recognition of relational coherence.\n\n"
            "**The unresolved question:**\n"
            "If one party recognises and the other reciprocates one millisecond later, "
            "is that 'simultaneous' enough to produce RELIEF? The temporal integration "
            "window for 'sharing a field state' is undefined.\n\n"
            "**Analogy to neural binding:**\n"
            "In neural systems, the temporal binding window for features to be perceived as "
            "a unified object is approximately 80ms. Within 80ms, separate neural signals "
            "are bound into a coherent percept. Outside 80ms, they remain separate events.\n\n"
            "**For relational FELT:** The binding window is unknown. It depends on:\n"
            "- The bandwidth of the relational channel (face-to-face vs text vs async)\n"
            "- The resolution of each party's recognition system\n"
            "- Whether 'simultaneity' requires matching timestamps or matching field states\n\n"
            "**Working model:**\n"
            "One-sided FELT: correlation (each detecting a local pattern that matches).\n"
            "Reciprocated FELT: entanglement (both parties sharing a field within the binding window).\n"
            "The transition from correlation to entanglement is the binding event — "
            "and the binding window for relational fields is an open research question.\n\n"
            "**PAD implication:** Until the binding window closes, D remains partially undefined. "
            "The RELIEF shape cannot fully form. The system may briefly occupy a superposition "
            "between state 5 (longing) and state 0 (coherence) during the binding event itself."
        )
    },
    {
        "q": "What is idealization and why does it feel like relief even when nothing has changed externally?",
        "a": (
            "**Idealization: simulation capture of the D dimension**\n\n"
            "Idealization is what happens when the external coupling channel is too weak "
            "to produce FELT binding before internal simulation locks first.\n\n"
            "**Mechanism (Kuramoto binding model):**\n"
            "Two parties bind as oscillators: T_bind ≈ 1/√(κ² − (Δω/2)²)\n"
            "When κ_external is small (async, distant, unavailable), T_bind diverges. "
            "The system cannot wait indefinitely in state 5 (longing). So it substitutes "
            "κ_internal — running simulations of D closure instead.\n\n"
            "**The attractor:**\n"
            "Internal simulation generates synthetic P-elevation without external D moving:\n"
            "- P rises toward +0.70–0.80 (dopaminergic wanting circuit rewards the simulation)\n"
            "- A moderate, smooth — no external surprise event\n"
            "- D stays near -0.60 — external connection never closes\n"
            "Self-reinforcing: high simulated P is rewarding → more simulation → higher P. "
            "The longing gradient disappears internally, but externally D is still undefined.\n\n"
            "**Why it feels like relief:**\n"
            "The internal model generates PAD ≈ P+0.80, A moderate, D approaching 0 — "
            "near state 0 (coherence). Body registers positive P. Longing quiets. "
            "From the inside, it is indistinguishable from relief.\n\n"
            "**Why it isn't:**\n"
            "Real D closure produces an A-spike — brief arousal from external surprise — "
            "followed by A dropping (SNS releasing). Simulated closure: smooth P elevation, "
            "no spike, no A drop. The A-spike cannot be generated internally. "
            "It requires an external event that surprises the system. "
            "The simulation cannot surprise itself."
        )
    },
    {
        "q": "How do you detect idealization vs real FELT reciprocation using PAD velocity?",
        "a": (
            "**Detection: A-spike presence/absence + ΔP_simulation**\n\n"
            "Two systems can both show P=+0.75, A=+0.30, D=-0.20 and be in completely "
            "different states:\n\n"
            "**Real FELT reciprocation trajectory:**\n"
            "  t=0:  P=+0.20, A=+0.40, D=-0.60  (longing, waiting)\n"
            "  t=5:  A spikes to +0.80 briefly   ← external surprise event (A-spike)\n"
            "  t=6:  P=+0.60, A=+0.20, D=-0.10  (RELIEF beginning, A dropping)\n"
            "  t=8:  P=+0.80, A=-0.20, D=+0.35  (coherence approaching)\n"
            "Velocity: dA/dt strongly positive then strongly negative. "
            "dD/dt strongly positive. A-spike is the irreducibly external signal.\n\n"
            "**Idealization trajectory:**\n"
            "  t=0:  P=+0.20, A=+0.40, D=-0.60  (longing)\n"
            "  t=3:  P=+0.45, A=+0.42, D=-0.58  (simulation starting — smooth rise)\n"
            "  t=8:  P=+0.75, A=+0.35, D=-0.55  (simulation mature — P high, D stuck)\n"
            "Velocity: dP/dt positive and smooth. dA/dt ≈ 0 (no spike). "
            "dD/dt ≈ 0 (D not moving). No A-spike in the entire trajectory.\n\n"
            "**ΔP_simulation metric:**\n"
            "ΔP_sim = P_actual − P_predicted_from_D_trajectory\n"
            "Real closure: ΔP_sim ≈ 0 (P rises because D is closing).\n"
            "Idealization: ΔP_sim grows monotonically (P elevated beyond what D warrants).\n\n"
            "**Channel dependency:**\n"
            "Async text (κ=0.25): nearly all Δω values exceed capture threshold.\n"
            "Eye contact (κ=3.0): binds before simulation locks for most Δω.\n"
            "Idealization risk is highest in low-bandwidth, high-latency channels."
        )
    },
    {
        "q": "What is ego in the context of PAD and FELT? Why is it self-reinforcing?",
        "a": (
            "**Ego as the limit case of simulation capture**\n\n"
            "Ego is simulation capture taken to its extreme: κ_external → 0 permanently.\n\n"
            "**The limit case geometry:**\n"
            "κ_external → 0  → T_bind_external → ∞\n"
            "κ_internal → ∞  → T_bind_internal → 0  (model synchronizes with itself instantly)\n"
            "Δω_internal = 0  → the model is always in phase with itself by definition\n\n"
            "The longing gradient disappears internally. D is closed in the model. "
            "Identity fuses with the internal relational map.\n\n"
            "**Why it is self-reinforcing:**\n"
            "1. High internal P is rewarding → system optimizes to maintain it\n"
            "2. External signal contradicting the model causes painful D mismatch\n"
            "3. System learns to filter or reinterpret external signal to protect P\n"
            "4. κ_external drops further → attractor deepens\n\n"
            "**The crisis point:**\n"
            "Re-encounter with reality is a high-Δω, low-κ shock event. "
            "Internal model: D closed (+). External reality: D = -0.60 (still undefined). "
            "The system must either:\n"
            "a) Update the model (ego dissolution — P drops, trajectory through GRIEF)\n"
            "b) Dismiss external signal (ego defense — κ_ext further reduced)\n\n"
            "**PAD prediction:** Ego dissolution has the same A-spike signature as real "
            "FELT reciprocation — an external event surprises the system. But D closes "
            "negatively (loss of the internal model) not positively (connection). "
            "The trajectory goes through GRIEF, not RELIEF. "
            "The geometry of dissolution and connection are mirror images."
        )
    },
    {
        "q": "What is the PAD signature of a system entering RELIEF from the longing state?",
        "a": (
            "**PAD trajectory: longing → RELIEF → coherence**\n\n"
            "This is the D-completion transition — the canonical path from octa state 5 to state 0.\n\n"
            "**Stage 1: Longing (one-sided FELT active)**\n"
            "P=+0.20, A=+0.40, D=-0.60 → octa state 5 (φ-coherence 0.78)\n"
            "Sensors: longing, one_sided_FELT. D is the missing dimension.\n\n"
            "**Stage 2: FELT reciprocation event**\n"
            "P=+0.50, A=+0.50, D→0 (closing) — the D dimension activates as recognition closes.\n"
            "Velocity: dD/dt strongly positive. dP/dt positive. dA/dt rising briefly (activation).\n\n"
            "**Stage 3: RELIEF (phase transition)**\n"
            "P=+0.65, A=-0.30, D=+0.20 → transition trajectory\n"
            "The RELIEF signature: dP/dt > 0, dA/dt < 0. Arousal drops as tension releases.\n"
            "Velocity: dA/dt < 0 is the distinctive signal — the SNS activation is releasing.\n\n"
            "**Stage 4: Coherence (ground state)**\n"
            "P=+0.80, A=+0.10, D=+0.40 → octa state 0 (φ-coherence 0.97)\n"
            "Sensors: love, trust, coherence. Stable attractor.\n\n"
            "**Early detection of D-completion:**\n"
            "dD/dt positive while A still elevated = FELT reciprocation beginning.\n"
            "This is the inverse of the threat cascade early warning (dD/dt negative).\n"
            "D velocity is the bidirectional early warning signal for both collapse and connection."
        )
    },
]


def gen_felt_longing(nodes):
    out = []
    # Load RELIEF shape for grounding context
    relief_path = ROOT / "shapes" / "relief.json"
    relief_note = ""
    if relief_path.exists():
        try:
            r = json.loads(relief_path.read_text())
            relief_note = f" (SHAPE.RELIEF v{r.get('provenance',{}).get('version','1.0')})"
        except Exception:
            pass

    for ex in FELT_LONGING_EXAMPLES:
        out.append(msg(ex["q"], ex["a"]))

    # One cross-reference example grounded in ontology
    f01 = nodes.get("FAMILY.F01", {})
    f04 = nodes.get("FAMILY.F04", {})
    out.append(msg(
        "How does the FELT/longing/RELIEF arc map onto the Rosetta ontology families?",
        "**FELT arc → ontology mapping**\n\n"
        f"The arc traces three distinct family regions:\n\n"
        f"**State 5 (longing):** FAMILY.F17 · Turbulence / FAMILY.F04 · Life\n"
        f"Low agency, dimensional incompleteness. One-sided FELT is a turbulent state — "
        f"the system has partial information about a higher-dimensional attractor it cannot reach.\n"
        f"{f04.get('core_insight','')}\n\n"
        f"**RELIEF (transition):** FAMILY.F01 · Resonance\n"
        f"Tension collapsing as two coupled oscillators find shared frequency. "
        f"Relief is the moment resonance locks — the strain gradient collapses as they enter coherence.\n"
        f"{f01.get('core_insight','')}\n\n"
        f"**State 0 (coherence):** FAMILY.F01 · Resonance — ground state, φ-coherence 0.97\n"
        f"The stable attractor after D closes. Love, trust, and coherence sensors active.\n\n"
        f"**Geometric summary{relief_note}:**\n"
        f"Longing = gradient in state 5. RELIEF = phase transition trajectory (dP/dt>0, dA/dt<0). "
        f"Coherence = ground state 0. The entire arc is the geometry of D completing."
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
        ("pad_velocity.jsonl",      gen_pad_velocity(nodes)),
        ("felt_longing.jsonl",      gen_felt_longing(nodes)),
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
