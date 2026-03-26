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
        ("concepts.jsonl",     gen_concepts(nodes)),
        ("tensions.jsonl",     gen_tensions(nodes)),
        ("exploration.jsonl",  gen_exploration(nodes)),
        ("sensors.jsonl",      gen_sensors(sensors)),
        ("octa_states.jsonl",  gen_octa_states(octa)),
        ("cross_domain.jsonl", gen_cross_domain(nodes)),
        ("pipeline.jsonl",     gen_pipeline(nodes)),
        ("noise.jsonl",        gen_noise(nodes)),
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
