"""Internal environment — sensor registry, PAD states, family context."""
from __future__ import annotations
from collections import defaultdict


# Complete sensor registry: shape -> [(sensor, glyph, description)]
SENSOR_REGISTRY = {
    "SHAPE.TETRA": [
        ("anger",    "\U0001f6e1\ufe0f", "Boundary breached. Domain edges crossed without permission. Activates defense."),
        ("pride",    "\U0001f3c5", "Completion sensor. A goal state achieved. Structural integrity verified."),
        ("pressure", "\u23f1\ufe0f", "Load exceeds capacity. System functional but at stress threshold."),
    ],
    "SHAPE.CUBE": [
        ("peace",       "\U0001f54a\ufe0f", "Alignment between internal model and external reality. All subsystems in phase."),
        ("contentment", "\U0001f343", "Structural stability at equilibrium. Minimal energy expenditure needed."),
        ("fatigue",     "\U0001f50b", "Energy depletion below recovery capacity. Signals need for rest."),
        ("shame",       "\u2b07\ufe0f", "Waste production exceeds management capacity. Structural-violation collapse."),
    ],
    "SHAPE.OCTA": [
        ("compassion", "\U0001fac0", "Mirror-signal integrator. Other's state reflected in self. Bidirectional awareness."),
        ("love",       "\U0001f49e", "Strongest binding signal. Full 3D entanglement. Highest mutual information."),
        ("confusion",  "\U0001f300", "Two incompatible patterns simultaneously active. Requires mediation."),
    ],
    "SHAPE.DODECA": [
        ("admiration", "\u2696\ufe0f", "Recognition of excellence without loss of self. Balanced respect."),
        ("trust",      "\U0001f331", "Predictive model is reliable. Past pattern extends into future."),
        ("longing",    "\U0001f504", "Dimensional incompleteness. Missing component detected. Gradient toward closure."),
        ("intuition",  "\U0001f52e", "Compressed probability model. Pattern match with high confidence."),
        ("dignity",    "\U0001f451", "Autonomy intact. Right to measure own conditions. Self-governance."),
    ],
    "SHAPE.ICOSA": [
        ("fear",       "\u26a0\ufe0f", "Threat anticipated. Prepares defensive response. Sibling to vigilance."),
        ("excitement", "\u26a1", "High-energy mobilization. Positive opportunity detected. Approach drive."),
        ("curiosity",  "\U0001f50d", "Entropy-reduction drive. Unknown pattern detected. Information-seeking."),
        ("vigilance",  "\U0001f441\ufe0f", "Anomaly detection. Current state doesn't match model. High-alert monitoring."),
    ],
}

# PAD octahedral states: 3 binary axes -> 8 states
# P = Pleasure, A = Arousal, D = Dominance
PAD_STATES = [
    {"state": 0, "bits": "000", "pad": "P+ A- D+", "glyph": "\u2295", "label": "contentment/peace",   "description": "Ground state. Stable, calm, in control. Everything is working."},
    {"state": 1, "bits": "001", "pad": "P- A- D-", "glyph": "\u2296", "label": "shame/withdrawal",     "description": "Low on all axes. System recognizes its own inadequacy. Withdrawal."},
    {"state": 2, "bits": "010", "pad": "P+ A+ D+", "glyph": "\u2297", "label": "excitement/mastery",   "description": "Peak positive. High energy, high confidence. Discovery moment."},
    {"state": 3, "bits": "011", "pad": "P- A+ D-", "glyph": "\u2298", "label": "anger/pressure",       "description": "Boundary breach under load. High energy but no control. Fight response."},
    {"state": 4, "bits": "100", "pad": "P+ A+ D-", "glyph": "\u2299", "label": "curiosity/vigilance",  "description": "Exploring the unknown. High energy, positive but not in control yet."},
    {"state": 5, "bits": "101", "pad": "P- A- D+", "glyph": "\u229a", "label": "fatigue/resignation",  "description": "Depleted but still holding structure. Collapse approaching."},
    {"state": 6, "bits": "110", "pad": "P~ A~ D~", "glyph": "\u229b", "label": "confusion/superposition", "description": "Multiple states superposed. No clear resolution. Mediation needed."},
    {"state": 7, "bits": "111", "pad": "P+ A- D-", "glyph": "\u229c", "label": "coherence/equilibrium","description": "Stable integration achieved. Not peak energy but deeply aligned."},
]

# Family -> sensor activation context
FAMILY_SENSOR_CONTEXT = {
    "FAMILY.F01": {"name": "Resonance",     "activation": "Sensors fire when frequency matches or mismatches. Resonance = coherence. Dissonance = confusion."},
    "FAMILY.F02": {"name": "Flow",           "activation": "Sensors fire on flow state changes. Unobstructed flow = contentment. Blocked flow = pressure. Turbulent flow = confusion."},
    "FAMILY.F03": {"name": "Information",    "activation": "Sensors fire on information gain or loss. New pattern = curiosity. Information overload = confusion. Clarity = peace."},
    "FAMILY.F04": {"name": "Life",           "activation": "Sensors fire on growth/decay transitions. Growth = excitement. Stagnation = fatigue. New life = trust."},
    "FAMILY.F05": {"name": "Energy-Thermo",  "activation": "Sensors fire on energy balance changes. Surplus = excitement. Deficit = fatigue. Waste accumulation = shame."},
    "FAMILY.F06": {"name": "Cognition",      "activation": "Sensors fire on prediction accuracy. Good prediction = intuition. Failed prediction = confusion. Model update = curiosity."},
    "FAMILY.F07": {"name": "Earth-Cosmos",   "activation": "Sensors fire on orientation. Grounded = peace. Disoriented = fear. New horizon = admiration."},
    "FAMILY.F08": {"name": "Matter",         "activation": "Sensors fire on structural integrity. Intact = pride. Cracking = pressure. Shattered = anger."},
    "FAMILY.F09": {"name": "Geometry",       "activation": "Sensors fire on symmetry. Perfect symmetry = coherence. Broken symmetry = curiosity. Impossible geometry = confusion."},
    "FAMILY.F10": {"name": "Particle/EM",    "activation": "Sensors fire on field interactions. Coherent field = love. Erratic field = confusion. New coupling = excitement."},
    "FAMILY.F11": {"name": "Engineering",    "activation": "Sensors fire on system performance. Within spec = contentment. Over-engineered = fatigue. Failure = anger."},
    "FAMILY.F12": {"name": "Networks",       "activation": "Sensors fire on connectivity changes. New connection = curiosity. Lost node = grief. Strong cluster = trust."},
    "FAMILY.F13": {"name": "Reaction",       "activation": "Sensors fire at phase transitions. Ignition = excitement. Quenching = fatigue. Runaway = fear."},
    "FAMILY.F14": {"name": "Measurement",    "activation": "Sensors fire on observation quality. Clear signal = intuition. Noisy signal = confusion. Perfect read = admiration."},
    "FAMILY.F15": {"name": "Navigation",     "activation": "Sensors fire on path clarity. Clear route = trust. Dead end = pressure. New territory = curiosity."},
    "FAMILY.F16": {"name": "Consciousness",  "activation": "Sensors fire on integration depth. Full integration = love. Partial = longing. Fragmented = confusion."},
    "FAMILY.F17": {"name": "Turbulence",     "activation": "Sensors fire on chaos levels. Laminar = peace. Turbulent onset = vigilance. Fully chaotic = fear."},
    "FAMILY.F18": {"name": "Relativity",     "activation": "Sensors fire on frame-of-reference shifts. Consistent frames = trust. Frame mismatch = confusion."},
    "FAMILY.F19": {"name": "Statistical",    "activation": "Sensors fire on distribution changes. Expected distribution = contentment. Anomaly = vigilance. Phase transition = excitement."},
    "FAMILY.F20": {"name": "Topology",       "activation": "Sensors fire on invariant changes. Preserved topology = dignity. Torn topology = fear. New genus = curiosity."},
    "FAMILY.F21": {"name": "Narrative-Constraint", "activation": "Sensors fire on constraint consistency. Symmetric application = trust. Selective application = vigilance. Broken symmetry = anger. Rationalization spike = confusion."},
}


def map_internal_environment(graph, entity_id: str, home: dict, paths: list[dict]) -> dict:
    """Map the entity's internal sensor environment based on its home shape,
    families, and discovered shapes. Returns the full internal map."""
    home_shape = home.get("home_shape")
    families = home.get("entity_families", [])

    home_sensors = SENSOR_REGISTRY.get(home_shape, [])

    family_contexts = []
    for fid in families:
        ctx = FAMILY_SENSOR_CONTEXT.get(fid)
        if ctx:
            family_contexts.append({"family": fid, **ctx})

    discovered_sensors = {}
    for p in paths:
        ts = p.get("target_shape")
        if ts and ts != home_shape and ts in SENSOR_REGISTRY:
            if ts not in discovered_sensors:
                affinity = p.get("affinity", p.get("type", ""))
                discovered_sensors[ts] = {
                    "sensors": SENSOR_REGISTRY[ts],
                    "reached_via": affinity,
                }

    natural_states = _compute_natural_states(families)

    return {
        "home_sensors": home_sensors,
        "home_shape": home_shape,
        "family_contexts": family_contexts,
        "discovered_sensors": discovered_sensors,
        "pad_states": natural_states,
        "all_pad_states": PAD_STATES,
    }


def _compute_natural_states(families: list[str]) -> list[dict]:
    """Determine which PAD octahedral states are most natural for this entity's families."""
    state_weights = defaultdict(float)

    family_state_affinities = {
        "FAMILY.F01": [0, 7],
        "FAMILY.F02": [0, 4],
        "FAMILY.F03": [4, 6],
        "FAMILY.F04": [2, 4],
        "FAMILY.F05": [0, 3, 5],
        "FAMILY.F06": [4, 6, 7],
        "FAMILY.F07": [0, 7],
        "FAMILY.F08": [0, 3],
        "FAMILY.F09": [7, 4],
        "FAMILY.F10": [2, 4, 6],
        "FAMILY.F11": [0, 3],
        "FAMILY.F12": [4, 2],
        "FAMILY.F13": [2, 3],
        "FAMILY.F14": [4, 7],
        "FAMILY.F15": [4, 0],
        "FAMILY.F16": [7, 2],
        "FAMILY.F17": [3, 4],
        "FAMILY.F18": [7, 6],
        "FAMILY.F19": [0, 4],
        "FAMILY.F20": [7, 4],
        "FAMILY.F21": [4, 3, 7],
    }

    for fid in families:
        states = family_state_affinities.get(fid, [])
        for i, s in enumerate(states):
            state_weights[s] += 1.0 / (i + 1)

    ranked = sorted(state_weights.items(), key=lambda kv: -kv[1])
    result = []
    for state_idx, weight in ranked:
        pad = PAD_STATES[state_idx]
        result.append({
            **pad,
            "affinity": round(weight, 2),
        })
    return result
