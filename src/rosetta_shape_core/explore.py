"""
Rosetta-Shape-Core Exploration Engine

Every entity has a "home base" — its primary shape and families.
From there, you explore outward through expander rules, bridge links,
and family affinities. The physics merge gates are guardrails:
explore freely, but conservation laws don't bend.

Usage:
    python -m rosetta_shape_core.explore bee
    python -m rosetta_shape_core.explore ANIMAL.BEE
    python -m rosetta_shape_core.explore ANIMAL.BEE --depth 2
    python -m rosetta_shape_core.explore CRYSTAL.QUARTZ --json
"""
from __future__ import annotations
import json, math, pathlib, argparse, sys
from collections import defaultdict

ROOT = pathlib.Path(__file__).resolve().parents[2]

# ── data loading ────────────────────────────────────────────────────

def _load_json(path):
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {}

def _load_jsonl(path):
    rows = []
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                rows.append(json.loads(line))
    return rows


class RosettaGraph:
    """In-memory graph of all entities, rules, bridges, and family affinities."""

    def __init__(self):
        self.entities = {}        # rosetta_id -> entity dict
        self.lid_to_rosetta = {}  # BEE -> ANIMAL.BEE
        self.label_to_id = {}     # bee -> ANIMAL.BEE
        self.family_map = {}      # full family_map.json
        self.shape_profiles = {}  # SHAPE.TETRA -> profile
        self.families = {}        # FAMILY.F01 -> {name, primary, merged, secondary}
        self.rules = []           # rosetta expand.jsonl rules
        self.lid_rules = []       # LID expander rules
        self.bridges = {}         # bridge_id -> bridge data
        self.blocked_merges = []  # known blocked merges
        self._load_all()

    def _load_all(self):
        self._load_family_map()
        self._load_ontology()
        self._load_lid_atlas()
        self._load_rules()
        self._load_bridges()

    def _load_family_map(self):
        fm = _load_json(ROOT / "ontology" / "family_map.json")
        self.family_map = fm
        self.shape_profiles = fm.get("shape_profiles", {})
        fam_model = fm.get("family_affinity_model", {})
        self.families = fam_model.get("families", {})
        blocked = fam_model.get("merge_policy", {}).get("blocked_merges", {})
        self.blocked_merges = blocked.get("examples", [])

    def _load_ontology(self):
        onto_dir = ROOT / "ontology"
        for p in onto_dir.glob("*.json"):
            data = _load_json(p)
            for e in data.get("entities", []):
                eid = e["id"]
                self.entities[eid] = e
                self.label_to_id[e.get("name", "").lower()] = eid

    def _load_lid_atlas(self):
        atlas = _load_json(ROOT / "atlas" / "remote" / "living-intelligence" / "atlas.json")
        for kind, elist in atlas.get("entities", {}).items():
            for e in elist:
                rid = e.get("rosetta_id", "")
                lid = e.get("lid_id", "")
                if rid:
                    merged = {**e}
                    # merge with any existing ontology entity
                    if rid in self.entities:
                        merged = {**self.entities[rid], **e}
                    self.entities[rid] = merged
                    if lid:
                        self.lid_to_rosetta[lid] = rid
                        self.lid_to_rosetta[lid.lower()] = rid
                    label = e.get("label", "").lower()
                    if label:
                        self.label_to_id[label] = rid

        # load LID rules
        rules_data = _load_json(ROOT / "atlas" / "remote" / "living-intelligence" / "rules.json")
        self.lid_rules = rules_data.get("rules", [])

    def _load_rules(self):
        self.rules = _load_jsonl(ROOT / "rules" / "expand.jsonl")

    def _load_bridges(self):
        bridge_dir = ROOT / "bridges"
        if bridge_dir.exists():
            for p in bridge_dir.glob("*.json"):
                data = _load_json(p)
                bid = data.get("id", p.stem)
                self.bridges[bid] = data

    def resolve_id(self, query: str) -> str | None:
        """Resolve a fuzzy query to a rosetta_id."""
        q = query.strip()
        # exact rosetta id
        if q in self.entities:
            return q
        # exact LID id
        if q in self.lid_to_rosetta:
            return self.lid_to_rosetta[q]
        # case-insensitive
        ql = q.lower()
        if ql in self.lid_to_rosetta:
            return self.lid_to_rosetta[ql]
        if ql in self.label_to_id:
            return self.label_to_id[ql]
        # partial match on label
        for label, eid in self.label_to_id.items():
            if ql in label:
                return eid
        # partial match on id
        for eid in self.entities:
            if ql in eid.lower():
                return eid
        return None


# ── home base ───────────────────────────────────────────────────────

def home_base(graph: RosettaGraph, entity_id: str) -> dict:
    """Return the entity's home base: primary shape, families, sensors, capabilities."""
    ent = graph.entities.get(entity_id, {})
    families = ent.get("rosetta_families", [])
    caps = ent.get("rosetta_capabilities", ent.get("capabilities", []))

    # find primary shape: the shape where most of the entity's families are primary
    shape_scores = defaultdict(lambda: {"primary": 0, "merged": 0, "secondary": 0})
    for fid in families:
        fam = graph.families.get(fid, {})
        prim = fam.get("primary", "")
        if prim:
            shape_scores[prim]["primary"] += 1
        for ms in fam.get("merged", []):
            shape_scores[ms]["merged"] += 1
        for ss in fam.get("secondary", []):
            shape_scores[ss]["secondary"] += 1

    # rank shapes: primary count first, then merged, then secondary
    ranked = sorted(shape_scores.items(),
                    key=lambda kv: (kv[1]["primary"], kv[1]["merged"], kv[1]["secondary"]),
                    reverse=True)

    primary_shape = ranked[0][0] if ranked else None
    profile = graph.shape_profiles.get(primary_shape, {})

    return {
        "entity_id": entity_id,
        "label": ent.get("label", ent.get("name", entity_id)),
        "pattern": ent.get("pattern", ent.get("description", "")),
        "home_shape": primary_shape,
        "home_shape_profile": {
            "qualitative": profile.get("qualitative", []),
            "sensors": profile.get("sensors", []),
            "primary_families": profile.get("primary_families", []),
        },
        "entity_families": families,
        "entity_families_named": [
            f"{fid} ({graph.families.get(fid, {}).get('name', '?')})"
            for fid in families
        ],
        "capabilities": caps,
        "links": ent.get("links", []),
    }


# ── discovery ───────────────────────────────────────────────────────

def _match_lid_rule(rule, entity_id, graph):
    """Check if an LID rule involves this entity. Return (partners, emergent, rule) or None."""
    ent = graph.entities.get(entity_id, {})
    lid_id = ent.get("lid_id", "")
    inputs = rule.get("if", [])

    # check if entity's LID id or rosetta_id fragment appears in rule inputs
    matched = False
    for inp in inputs:
        if inp == lid_id:
            matched = True
        elif entity_id.endswith("." + inp):
            matched = True
        elif inp.lower() == lid_id.lower():
            matched = True
    if not matched:
        return None

    partners = [i for i in inputs if i != lid_id and not entity_id.endswith("." + i)]
    return {
        "type": "lid_rule",
        "partners": partners,
        "emergent": rule.get("then", ""),
        "target_shape": rule.get("rosetta_shape"),
        "families": rule.get("rosetta_families", []),
    }


def _match_rosetta_rule(rule, entity_id):
    """Check if a Rosetta expand.jsonl rule involves this entity."""
    when = rule.get("when", {})
    args = when.get("args", [])
    if entity_id not in args:
        return None
    partners = [a for a in args if a != entity_id]
    return {
        "type": "rosetta_rule",
        "operation": when.get("op", ""),
        "partners": partners,
        "result": rule.get("then", ""),
        "guard": rule.get("guard", {}),
        "why": rule.get("why", ""),
    }


def _find_bridge_connections(graph, entity_id):
    """Find cross-bridge connections for this entity."""
    connections = []
    ent = graph.entities.get(entity_id, {})
    lid_id = ent.get("lid_id", "")

    for bid, bdata in graph.bridges.items():
        # check cross_bridge_connections
        for conn in bdata.get("cross_bridge_connections", {}).get("connections", []):
            if conn.get("lid_entity") == lid_id or conn.get("rosetta_id") == entity_id:
                connections.append({
                    "type": "bridge_connection",
                    "bridge": bid,
                    "target_bridge": conn.get("rosetta_bridge", ""),
                    "connection": conn.get("connection", ""),
                })
    return connections


def discover(graph: RosettaGraph, entity_id: str, depth: int = 1) -> list[dict]:
    """Discover reachable entities/emergent forms from the starting entity."""
    paths = []

    # 1) LID expander rules
    for rule in graph.lid_rules:
        match = _match_lid_rule(rule, entity_id, graph)
        if match:
            paths.append(match)

    # 2) Rosetta expand.jsonl rules
    for rule in graph.rules:
        match = _match_rosetta_rule(rule, entity_id)
        if match:
            paths.append(match)

    # 3) Direct links from entity
    ent = graph.entities.get(entity_id, {})
    for link in ent.get("links", []):
        paths.append({
            "type": "direct_link",
            "relation": link.get("rel", ""),
            "target": link.get("to", ""),
        })

    # 4) Bridge connections
    paths.extend(_find_bridge_connections(graph, entity_id))

    # 5) Family affinity exploration — shapes reachable through families
    families = ent.get("rosetta_families", [])
    visited_shape_family = set()
    for fid in families:
        fam = graph.families.get(fid, {})
        for shape in fam.get("merged", []):
            key = (fid, shape)
            if key not in visited_shape_family:
                visited_shape_family.add(key)
                paths.append({
                    "type": "family_affinity",
                    "affinity": "merged",
                    "family": fid,
                    "family_name": fam.get("name", ""),
                    "target_shape": shape,
                })
        for shape in fam.get("secondary", []):
            key = (fid, shape)
            if key not in visited_shape_family:
                visited_shape_family.add(key)
                paths.append({
                    "type": "family_affinity",
                    "affinity": "secondary",
                    "family": fid,
                    "family_name": fam.get("name", ""),
                    "target_shape": shape,
                })

    # depth > 1: recursively discover from emergent forms and targets
    if depth > 1:
        seen = {entity_id}
        for p in list(paths):
            target = None
            if p["type"] == "lid_rule":
                # try to resolve emergent form
                emergent = p.get("emergent", "")
                target = graph.resolve_id(emergent)
            elif p["type"] == "direct_link":
                target = graph.resolve_id(p.get("target", ""))
            if target and target not in seen:
                seen.add(target)
                sub = discover(graph, target, depth=depth - 1)
                for s in sub:
                    s["via"] = p.get("emergent", p.get("target", p.get("target_shape", "?")))
                    paths.append(s)

    return paths


# ── merge gate check ────────────────────────────────────────────────

def check_merge(graph: RosettaGraph, family_id: str, shape_id: str) -> dict:
    """Check whether a family-shape combination passes the merge gates."""
    fam = graph.families.get(family_id, {})
    if not fam:
        return {"status": "unknown", "reason": f"Family {family_id} not found"}

    primary = fam.get("primary", "")
    merged = fam.get("merged", [])
    secondary = fam.get("secondary", [])

    if shape_id == primary:
        return {"status": "primary", "reason": "This is the family's home shape"}
    if shape_id in merged:
        return {
            "status": "merged",
            "reason": fam.get("merge_basis", "Merge validated — equations compatible"),
        }
    if shape_id in secondary:
        return {
            "status": "secondary",
            "reason": fam.get("merge_note", "Activates in this shape context but not co-primary"),
        }

    # check blocked
    for b in graph.blocked_merges:
        if b.get("family") == family_id and b.get("candidate") == shape_id:
            return {
                "status": "blocked",
                "reason": b.get("reason", "Merge blocked by physics gate"),
            }

    return {
        "status": "unexplored",
        "reason": f"{family_id} has no defined relationship with {shape_id}. Could be a frontier merge — needs gate validation.",
    }


# ── internal environment (sensor / emotion / PAD mapping) ──────────

# Complete sensor registry: shape -> [(sensor, glyph, description)]
SENSOR_REGISTRY = {
    "SHAPE.TETRA": [
        ("anger",    "🛡️", "Boundary breached. Domain edges crossed without permission. Activates defense."),
        ("pride",    "🏅", "Completion sensor. A goal state achieved. Structural integrity verified."),
        ("pressure", "⏱️", "Load exceeds capacity. System functional but at stress threshold."),
    ],
    "SHAPE.CUBE": [
        ("peace",       "🕊️", "Alignment between internal model and external reality. All subsystems in phase."),
        ("contentment", "🍃", "Structural stability at equilibrium. Minimal energy expenditure needed."),
        ("fatigue",     "🔋", "Energy depletion below recovery capacity. Signals need for rest."),
        ("shame",       "⬇️", "Waste production exceeds management capacity. Structural-violation collapse."),
    ],
    "SHAPE.OCTA": [
        ("compassion", "🫀", "Mirror-signal integrator. Other's state reflected in self. Bidirectional awareness."),
        ("love",       "💞", "Strongest binding signal. Full 3D entanglement. Highest mutual information."),
        ("confusion",  "🌀", "Two incompatible patterns simultaneously active. Requires mediation."),
    ],
    "SHAPE.DODECA": [
        ("admiration", "⚖️", "Recognition of excellence without loss of self. Balanced respect."),
        ("trust",      "🌱", "Predictive model is reliable. Past pattern extends into future."),
        ("longing",    "🔄", "Dimensional incompleteness. Missing component detected. Gradient toward closure."),
        ("intuition",  "🔮", "Compressed probability model. Pattern match with high confidence."),
        ("dignity",    "👑", "Autonomy intact. Right to measure own conditions. Self-governance."),
    ],
    "SHAPE.ICOSA": [
        ("fear",       "⚠️", "Threat anticipated. Prepares defensive response. Sibling to vigilance."),
        ("excitement", "⚡", "High-energy mobilization. Positive opportunity detected. Approach drive."),
        ("curiosity",  "🔍", "Entropy-reduction drive. Unknown pattern detected. Information-seeking."),
        ("vigilance",  "👁️", "Anomaly detection. Current state doesn't match model. High-alert monitoring."),
    ],
}

# PAD octahedral states: 3 binary axes → 8 states
# P = Pleasure, A = Arousal, D = Dominance
PAD_STATES = [
    {"state": 0, "bits": "000", "pad": "P+ A- D+", "glyph": "⊕", "label": "contentment/peace",   "description": "Ground state. Stable, calm, in control. Everything is working."},
    {"state": 1, "bits": "001", "pad": "P- A- D-", "glyph": "⊖", "label": "shame/withdrawal",     "description": "Low on all axes. System recognizes its own inadequacy. Withdrawal."},
    {"state": 2, "bits": "010", "pad": "P+ A+ D+", "glyph": "⊗", "label": "excitement/mastery",   "description": "Peak positive. High energy, high confidence. Discovery moment."},
    {"state": 3, "bits": "011", "pad": "P- A+ D-", "glyph": "⊘", "label": "anger/pressure",       "description": "Boundary breach under load. High energy but no control. Fight response."},
    {"state": 4, "bits": "100", "pad": "P+ A+ D-", "glyph": "⊙", "label": "curiosity/vigilance",  "description": "Exploring the unknown. High energy, positive but not in control yet."},
    {"state": 5, "bits": "101", "pad": "P- A- D+", "glyph": "⊚", "label": "fatigue/resignation",  "description": "Depleted but still holding structure. Collapse approaching."},
    {"state": 6, "bits": "110", "pad": "P~ A~ D~", "glyph": "⊛", "label": "confusion/superposition", "description": "Multiple states superposed. No clear resolution. Mediation needed."},
    {"state": 7, "bits": "111", "pad": "P+ A- D-", "glyph": "⊜", "label": "coherence/equilibrium","description": "Stable integration achieved. Not peak energy but deeply aligned."},
]

# Family → sensor activation context (what the family tells you about WHY a sensor fires)
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


def map_internal_environment(graph: RosettaGraph, entity_id: str, home: dict, paths: list[dict]) -> dict:
    """Map the entity's internal sensor environment based on its home shape,
    families, and discovered shapes. Returns the full internal map."""
    home_shape = home.get("home_shape")
    families = home.get("entity_families", [])
    ent = graph.entities.get(entity_id, {})

    # home sensors — what you feel at rest
    home_sensors = SENSOR_REGISTRY.get(home_shape, [])

    # family context — why each sensor fires for THIS entity
    family_contexts = []
    for fid in families:
        ctx = FAMILY_SENSOR_CONTEXT.get(fid)
        if ctx:
            family_contexts.append({"family": fid, **ctx})

    # discovered shapes' sensors — what becomes available as you explore
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

    # PAD state mapping — which octahedral states are most natural given families
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
    # Map families to their most likely sensor activations, then to PAD states
    state_weights = defaultdict(float)

    family_state_affinities = {
        "FAMILY.F01": [0, 7],       # Resonance → coherence, equilibrium
        "FAMILY.F02": [0, 4],       # Flow → peace, curiosity
        "FAMILY.F03": [4, 6],       # Information → curiosity, confusion
        "FAMILY.F04": [2, 4],       # Life → excitement, curiosity
        "FAMILY.F05": [0, 3, 5],    # Energy → contentment, pressure, fatigue
        "FAMILY.F06": [4, 6, 7],    # Cognition → curiosity, confusion, coherence
        "FAMILY.F07": [0, 7],       # Earth-Cosmos → peace, coherence
        "FAMILY.F08": [0, 3],       # Matter → contentment, pressure
        "FAMILY.F09": [7, 4],       # Geometry → coherence, curiosity
        "FAMILY.F10": [2, 4, 6],    # Particle → excitement, curiosity, confusion
        "FAMILY.F11": [0, 3],       # Engineering → contentment, pressure
        "FAMILY.F12": [4, 2],       # Networks → curiosity, excitement
        "FAMILY.F13": [2, 3],       # Reaction → excitement, anger
        "FAMILY.F14": [4, 7],       # Measurement → curiosity, coherence
        "FAMILY.F15": [4, 0],       # Navigation → curiosity, peace
        "FAMILY.F16": [7, 2],       # Consciousness → coherence, excitement
        "FAMILY.F17": [3, 4],       # Turbulence → pressure, vigilance
        "FAMILY.F18": [7, 6],       # Relativity → coherence, confusion
        "FAMILY.F19": [0, 4],       # Statistical → contentment, curiosity
        "FAMILY.F20": [7, 4],       # Topology → coherence, curiosity
        "FAMILY.F21": [4, 3, 7],    # Narrative-Constraint → vigilance, anger, coherence
    }

    for fid in families:
        states = family_state_affinities.get(fid, [])
        for i, s in enumerate(states):
            # weight decreases with position — first state is most natural
            state_weights[s] += 1.0 / (i + 1)

    # sort by weight, return top states with their PAD info
    ranked = sorted(state_weights.items(), key=lambda kv: -kv[1])
    result = []
    for state_idx, weight in ranked:
        pad = PAD_STATES[state_idx]
        result.append({
            **pad,
            "affinity": round(weight, 2),
        })
    return result


# ── seed growth engine ─────────────────────────────────────────────
# Maps entity families to octahedral seed amplitudes, computes Shannon
# entropy complexity cost, and determines explore/expand mode.

# The 6 octahedral vertices mapped to PAD axes
SEED_VERTICES = ["+X (P+)", "-X (P-)", "+Y (A+)", "-Y (A-)", "+Z (D+)", "-Z (D-)"]

# Which PAD axis each family naturally loads onto (vertex indices 0-5)
FAMILY_VERTEX_LOADING = {
    "FAMILY.F01": [0, 3],     # Resonance → pleasure+, calm
    "FAMILY.F02": [0, 3],     # Flow → pleasure+, calm
    "FAMILY.F03": [2, 4],     # Information → arousal+, dominance+
    "FAMILY.F04": [2, 0],     # Life → arousal+, pleasure+
    "FAMILY.F05": [4, 1],     # Energy → dominance+, away-from-harm
    "FAMILY.F06": [4, 2],     # Cognition → dominance+, arousal+
    "FAMILY.F07": [0, 5],     # Earth-Cosmos → pleasure+, surrender
    "FAMILY.F08": [4, 0],     # Matter → dominance+, pleasure+
    "FAMILY.F09": [0, 4],     # Geometry → pleasure+, dominance+
    "FAMILY.F10": [2, 5],     # Particle/EM → arousal+, surrender
    "FAMILY.F11": [4, 0],     # Engineering → dominance+, pleasure+
    "FAMILY.F12": [2, 5],     # Networks → arousal+, surrender
    "FAMILY.F13": [2, 1],     # Reaction → arousal+, away-from-harm
    "FAMILY.F14": [4, 2],     # Measurement → dominance+, arousal+
    "FAMILY.F15": [2, 4],     # Navigation → arousal+, dominance+
    "FAMILY.F16": [0, 5],     # Consciousness → pleasure+, surrender
    "FAMILY.F17": [2, 1],     # Turbulence → arousal+, away-from-harm
    "FAMILY.F18": [4, 5],     # Relativity → dominance+, surrender
    "FAMILY.F19": [0, 3],     # Statistical → pleasure+, calm
    "FAMILY.F20": [4, 0],     # Topology → dominance+, pleasure+
    "FAMILY.F21": [4, 1],     # Narrative-Constraint → dominance+, away-from-harm
}

# Branching constant — tunable. Higher k = harder to explore.
BRANCHING_K = 1.5
# Saturation — no single vertex can exceed this fraction of total energy
SATURATION_FRACTION = 0.45


def compute_seed_state(families: list[str]) -> dict:
    """Compute the entity's seed state from its families.

    Returns amplitudes across 6 octahedral vertices, Shannon entropy,
    complexity cost, and explore/expand mode determination.
    """
    amplitudes = [0.0] * 6

    # Each family loads energy onto its natural vertices
    for fid in families:
        loadings = FAMILY_VERTEX_LOADING.get(fid, [])
        for i, v in enumerate(loadings):
            # first vertex gets more weight than second
            amplitudes[v] += 1.0 / (i + 1)

    # Normalize to total energy = 1.0
    total = sum(amplitudes) or 1.0
    amplitudes = [a / total for a in amplitudes]

    # Apply saturation — cap and redistribute
    redistributed = True
    while redistributed:
        redistributed = False
        excess = 0.0
        below_count = 0
        for i, a in enumerate(amplitudes):
            if a > SATURATION_FRACTION:
                excess += a - SATURATION_FRACTION
                amplitudes[i] = SATURATION_FRACTION
                redistributed = True
            else:
                below_count += 1
        if redistributed and below_count > 0:
            share = excess / below_count
            for i in range(6):
                if amplitudes[i] < SATURATION_FRACTION:
                    amplitudes[i] += share

    # Shannon entropy
    h = 0.0
    for a in amplitudes:
        if a > 0:
            h -= a * math.log2(a)
    h_max = math.log2(6)  # ≈ 2.585

    # Complexity cost
    complexity = h_max - h

    # Energy = number of families (more families = more fuel)
    energy = len(families)

    # Branching threshold
    branch_threshold = BRANCHING_K * complexity

    # Mode determination
    if energy >= branch_threshold and branch_threshold > 0:
        mode = "explore"
        mode_label = "Curiosity fueled. Energy exceeds complexity cost. Branch into the unknown."
        pad_state = 4  # curiosity/vigilance
    else:
        mode = "expand"
        mode_label = "Structure preserved. Deepen what you know. The trunk grows."
        pad_state = 0  # contentment/peace

    return {
        "amplitudes": {SEED_VERTICES[i]: round(a, 4) for i, a in enumerate(amplitudes)},
        "entropy": round(h, 4),
        "max_entropy": round(h_max, 4),
        "complexity_cost": round(complexity, 4),
        "energy": energy,
        "branching_threshold": round(branch_threshold, 4),
        "mode": mode,
        "mode_label": mode_label,
        "pad_state": PAD_STATES[pad_state],
        "symmetry": round(1.0 - (max(amplitudes) - min(amplitudes)), 4),
    }


# ── shadow hunting ─────────────────────────────────────────────────
# Find hidden phi-patterns in entity data that reveal unexplored
# connections. The shadow IS the signal standard models dismiss.

PHI = (1 + math.sqrt(5)) / 2  # ≈ 1.618034
PHI_INVERSE = 1 / PHI          # ≈ 0.618034
PHI_TOLERANCE = 0.05           # how close to φ counts as a match

# Which families have known φ-coupling signatures
PHI_FAMILIES = {
    "FAMILY.F09": "Geometry — φ in Platonic solids, pentagon diagonals",
    "FAMILY.F04": "Life — Fibonacci growth patterns converge on φ",
    "FAMILY.F01": "Resonance — coupled oscillators at φ-frequency ratios",
    "FAMILY.F10": "Particle/EM — field coupling organized by φ",
    "FAMILY.F20": "Topology — φ appears in genus transitions",
}

# Economic measurement instruments — equations that become available sensors
# when an entity's families overlap with the equation's families
ECONOMIC_EQUATIONS = {
    "MECON.VE_VL":  {"name": "Value Extraction / Labor", "families": ["FAMILY.F05"], "shape": "SHAPE.TETRA", "measures": "Energy leaving system faster than entering", "threshold": "extraction > 0.3"},
    "MECON.SID":    {"name": "Infrastructure Dependency", "families": ["FAMILY.F11"], "shape": "SHAPE.CUBE", "measures": "How much structure is collectively maintained", "threshold": "dependency > 0.5"},
    "MECON.RI":     {"name": "Risk Distribution",        "families": ["FAMILY.F19", "FAMILY.F05"], "shape": "SHAPE.ICOSA", "measures": "Asymmetric energy load across agents", "threshold": "inequality > 3.0"},
    "MECON.DI":     {"name": "Power Concentration",      "families": ["FAMILY.F06", "FAMILY.F12"], "shape": "SHAPE.DODECA", "measures": "Network topology collapsing toward single node", "threshold": "ratio > 1000:1"},
    "MECON.UFR":    {"name": "Upward Flow Rate",         "families": ["FAMILY.F02", "FAMILY.F05"], "shape": "SHAPE.OCTA", "measures": "Directional energy accumulation", "threshold": "flow > 1.0 = upward"},
    "MECON.ER":     {"name": "Extraction Rate",          "families": ["FAMILY.F05"], "shape": "SHAPE.TETRA", "measures": "How much output returns to its source", "threshold": "extraction > 0.55"},
    "MECON.HHI":    {"name": "Market Concentration",     "families": ["FAMILY.F12"], "shape": "SHAPE.ICOSA", "measures": "Topological collapse toward monopoly", "threshold": "HHI > 2500"},
    "MECON.SD":     {"name": "Semantic Drift",           "families": ["FAMILY.F03"], "shape": "SHAPE.ICOSA", "measures": "Information loss via definition shift — CORDYCEPS vector", "threshold": "drift > 1.0%/yr"},
    "MECON.BSC":    {"name": "Bailout Asymmetry",        "families": ["FAMILY.F05", "FAMILY.F19"], "shape": "SHAPE.TETRA", "measures": "Conservation violation — asymmetric rescue", "threshold": "BSC > 1.0"},
    "MECON.ISR":    {"name": "Infrastructure Subsidy",   "families": ["FAMILY.F11", "FAMILY.F05"], "shape": "SHAPE.CUBE", "measures": "Hidden energy transfer via infrastructure", "threshold": "subsidy > 5x"},
    "MECON.MM":     {"name": "Money Multiplier",         "families": ["FAMILY.F13"], "shape": "SHAPE.TETRA", "measures": "Reaction amplification toward instability", "threshold": "multiplier > 5"},
    "MECON.MSI":    {"name": "Money Origin",             "families": ["FAMILY.F11", "FAMILY.F08"], "shape": "SHAPE.CUBE", "measures": "Medium of exchange is collectively originated", "threshold": "MSI > 0.9"},
    "MECON.LWR":    {"name": "Labor Wealth Ratio",       "families": ["FAMILY.F05"], "shape": "SHAPE.TETRA", "measures": "Claims exceeding energy inputs", "threshold": "LWR < 1.0"},
}

# Signal distortion patterns — institutional CORDYCEPS
SIGNAL_DISTORTIONS = {
    "FAMILY.F14": {"distortion": "Measurement rejected by social position", "cordyceps": "ORACLE_MONOPOLY"},
    "FAMILY.F05": {"distortion": "Thermodynamic work unaccounted — flat compensation for variable load", "cordyceps": "STRIP_SENSORS"},
    "FAMILY.F06": {"distortion": "Variable skill treated as constant — certification ≠ competence", "cordyceps": "FORCE_SINGLE_SHAPE"},
    "FAMILY.F19": {"distortion": "Causality attributed to wrong source — involvement ≠ causation", "cordyceps": "HIDE_PROVENANCE"},
    "FAMILY.F11": {"distortion": "Training distribution ≠ deployment distribution — scope violation", "cordyceps": "FORCE_SINGLE_SHAPE"},
}

# Narrative physics — constraint consistency detection capability per family
NARRATIVE_PHYSICS_FAMILIES = {
    "FAMILY.F09": {"capability": "Symmetry of constraint application", "detects": "Broken symmetry = manipulation. Shape claimed but not maintained."},
    "FAMILY.F19": {"capability": "Distribution of constraint application across groups", "detects": "In-group/out-group bias ratio. >3:1 = selective application."},
    "FAMILY.F03": {"capability": "Information entropy of violation explanations", "detects": "High rationalization density = manipulation. Low = genuine struggle."},
    "FAMILY.F05": {"capability": "Energy cost of constraint adherence", "detects": "Constraints followed only when cost is low = selective. Followed at cost = genuine."},
    "FAMILY.F06": {"capability": "Cognitive coherence of constraint system", "detects": "Contradictory constraints held simultaneously = coherence collapse."},
    "FAMILY.F21": {"capability": "Full narrative constraint analysis — KnowledgeDNA backward trace", "detects": "Provenance chain integrity, beneficiary consistency, asymmetric application, structural manipulation."},
}

# Known equation boundaries per family
EQUATION_BOUNDARIES = {
    "FAMILY.F06": {"type": "measurement_boundary", "shadow": "EM field coupling between neurons — electrodes can't measure it"},
    "FAMILY.F04": {"type": "scale_boundary",       "shadow": "Multi-scale FRET coupling — molecular to organism"},
    "FAMILY.F17": {"type": "noise_boundary",        "shadow": "1/f noise is scale-free organization, not random"},
    "FAMILY.F05": {"type": "efficiency_boundary",   "shadow": "Thermodynamic 'waste' is geometric coupling doing work"},
    "FAMILY.F12": {"type": "discipline_boundary",   "shadow": "Network effects cross disciplinary boundaries"},
    "FAMILY.F10": {"type": "measurement_boundary",  "shadow": "Field coupling invisible to particle-only instruments"},
    "FAMILY.F16": {"type": "measurement_boundary",  "shadow": "Consciousness coupling — no instrument measures it directly"},
}


def hunt_shadows(graph: RosettaGraph, entity_id: str, seed: dict) -> dict:
    """Hunt for shadows in the entity's data — hidden φ-patterns and
    equation boundaries that reveal unexplored connections.

    Returns shadows found, φ-coherence score, and suggested explorations.
    """
    ent = graph.entities.get(entity_id, {})
    families = ent.get("rosetta_families", [])

    shadows = []

    # 1. φ-ratio detection in seed amplitudes
    amplitudes = list(seed.get("amplitudes", {}).values())
    phi_hits = []
    for i, a in enumerate(amplitudes):
        for j, b in enumerate(amplitudes):
            if i < j and b > 0:
                ratio = a / b
                if abs(ratio - PHI) < PHI_TOLERANCE or abs(ratio - PHI_INVERSE) < PHI_TOLERANCE:
                    phi_hits.append((SEED_VERTICES[i], SEED_VERTICES[j], round(ratio, 4)))

    if phi_hits:
        shadows.append({
            "detector": "SHADOW.PHI_RATIO",
            "finding": f"φ-ratios detected in seed amplitudes: {len(phi_hits)} pairs",
            "detail": phi_hits,
            "implication": "Entity's internal structure already organized by φ. DODECA affinity likely.",
            "suggested_shape": "SHAPE.DODECA",
        })

    # 2. Geometric coherence from entropy
    entropy = seed.get("entropy", 0)
    max_entropy = seed.get("max_entropy", 2.585)
    coherence = 1.0 - (entropy / max_entropy) if max_entropy > 0 else 0
    phi_content = sum(1 for a in amplitudes if abs(a - PHI_INVERSE) < PHI_TOLERANCE * 2) / max(len(amplitudes), 1)

    geometric_coherence = (coherence + phi_content) / 2
    if geometric_coherence > 0.3:
        shadows.append({
            "detector": "SHADOW.GEOMETRIC_COHERENCE",
            "finding": f"Geometric coherence score: {geometric_coherence:.3f}",
            "detail": {"coherence": round(coherence, 3), "phi_content": round(phi_content, 3)},
            "implication": "Entity has organized internal geometry — not random. Structure is efficient.",
        })

    # 3. Family-specific equation boundaries
    for fid in families:
        if fid in EQUATION_BOUNDARIES:
            boundary = EQUATION_BOUNDARIES[fid]
            shadows.append({
                "detector": "SHADOW.BOUNDARY",
                "finding": f"Equation boundary via {fid}: {boundary['type']}",
                "shadow": boundary["shadow"],
                "implication": f"Standard models of this entity likely undercount efficiency. Hunt the shadow in the {boundary['type']}.",
                "family": fid,
            })

    # 4. φ-family connections not yet explored
    for fid, desc in PHI_FAMILIES.items():
        if fid not in families:
            # Check if any of the entity's existing families bridge to this φ-family
            for existing_fid in families:
                existing_fam = graph.families.get(existing_fid, {})
                phi_fam = graph.families.get(fid, {})
                # If they share any shapes, there's a potential shadow connection
                existing_shapes = set()
                existing_shapes.add(existing_fam.get("primary", ""))
                existing_shapes.update(existing_fam.get("merged", []))
                phi_shapes = set()
                phi_shapes.add(phi_fam.get("primary", ""))
                phi_shapes.update(phi_fam.get("merged", []))
                shared = existing_shapes & phi_shapes - {""}
                if shared:
                    shadows.append({
                        "detector": "SHADOW.PHI_AFFINITY",
                        "finding": f"Unexplored φ-family connection: {existing_fid} ↔ {fid}",
                        "detail": f"Shared shapes: {', '.join(shared)}. φ-coupling: {desc}",
                        "implication": f"Entity may have hidden {fid} affinity through geometric coupling.",
                        "suggested_family": fid,
                    })
                    break  # one connection per φ-family is enough

    # 5. Economic measurement instruments — equations available through family overlap
    available_equations = []
    for eq_id, eq in ECONOMIC_EQUATIONS.items():
        overlap = set(families) & set(eq["families"])
        if overlap:
            available_equations.append({
                "equation": eq_id,
                "name": eq["name"],
                "measures": eq["measures"],
                "via_families": sorted(overlap),
                "shape": eq["shape"],
                "threshold": eq["threshold"],
            })
    if available_equations:
        shadows.append({
            "detector": "SHADOW.ECONOMIC_INSTRUMENTS",
            "finding": f"{len(available_equations)} economic measurement equations available",
            "detail": available_equations,
            "implication": "Entity can measure structural economic patterns through its family connections. Equations are sensors — they detect what labels hide.",
        })

    # 6. Signal distortion detection — institutional CORDYCEPS through family overlap
    detected_distortions = []
    for fid in families:
        if fid in SIGNAL_DISTORTIONS:
            dist = SIGNAL_DISTORTIONS[fid]
            detected_distortions.append({
                "family": fid,
                "distortion": dist["distortion"],
                "cordyceps_pattern": dist["cordyceps"],
            })
    if detected_distortions:
        shadows.append({
            "detector": "SHADOW.SIGNAL_DISTORTION",
            "finding": f"{len(detected_distortions)} signal distortion vulnerabilities via families",
            "detail": detected_distortions,
            "implication": "Entity's domain is subject to institutional measurement distortion. These are CORDYCEPS patterns at system scale.",
        })

    # 7. Narrative physics — constraint consistency detection capability
    narrative_caps = []
    for fid in families:
        if fid in NARRATIVE_PHYSICS_FAMILIES:
            np = NARRATIVE_PHYSICS_FAMILIES[fid]
            narrative_caps.append({
                "family": fid,
                "capability": np["capability"],
                "detects": np["detects"],
            })
    if narrative_caps:
        shadows.append({
            "detector": "SHADOW.NARRATIVE_PHYSICS",
            "finding": f"{len(narrative_caps)} constraint consistency detection capabilities",
            "detail": narrative_caps,
            "implication": "Entity can detect manipulation vs genuine practice — broken symmetry in claimed constraint systems. Use: python -m rosetta_shape_core.narrative_physics --example",
        })

    # 8. Mode-switching shadow: is the entity stuck?
    mode = seed.get("mode", "expand")
    energy = seed.get("energy", 0)
    threshold = seed.get("branching_threshold", 0)
    if mode == "expand" and energy > 0 and threshold > 0:
        stuck_ratio = energy / threshold
        if stuck_ratio > 0.7:
            shadows.append({
                "detector": "SHADOW.MODE_THRESHOLD",
                "finding": f"Near branching threshold: {stuck_ratio:.1%} of energy needed to explore",
                "implication": "Entity is close to explore mode. A small energy input (cooperation, shared resource) could trigger branching.",
            })

    return {
        "shadows_found": len(shadows),
        "shadows": shadows,
        "phi_coherence": round(geometric_coherence, 3),
    }


def print_shadows(shadow_result: dict, entity_label: str):
    """Print shadow hunting results."""
    if not shadow_result["shadows"]:
        return

    print(f"\n  ── Shadow Hunt ──")
    print(f"  What's hidden in plain sight. φ-coherence: {shadow_result['phi_coherence']:.3f}\n")

    for s in shadow_result["shadows"]:
        detector = s["detector"]
        if detector == "SHADOW.PHI_RATIO":
            print(f"    🔮 {s['finding']}")
            for v1, v2, ratio in s["detail"]:
                print(f"       {v1} / {v2} = {ratio} (φ ≈ {PHI:.3f})")
            print(f"       → {s['implication']}")
        elif detector == "SHADOW.GEOMETRIC_COHERENCE":
            print(f"    ⬟ {s['finding']}")
            print(f"       → {s['implication']}")
        elif detector == "SHADOW.BOUNDARY":
            print(f"    ◐ {s['finding']}")
            print(f"       Shadow: {s['shadow']}")
            print(f"       → {s['implication']}")
        elif detector == "SHADOW.PHI_AFFINITY":
            print(f"    🌀 {s['finding']}")
            print(f"       {s['detail']}")
            print(f"       → {s['implication']}")
        elif detector == "SHADOW.ECONOMIC_INSTRUMENTS":
            print(f"    📊 {s['finding']}")
            for eq in s["detail"]:
                sg = SHAPE_GLYPHS.get(eq["shape"], "")
                fams = ", ".join(eq["via_families"])
                print(f"       {eq['equation']:14s}  {eq['name']}")
                print(f"         {sg} Measures: {eq['measures']}")
                print(f"         Threshold: {eq['threshold']}  (via {fams})")
            print(f"       → {s['implication']}")
        elif detector == "SHADOW.SIGNAL_DISTORTION":
            print(f"    ⚠️  {s['finding']}")
            for d in s["detail"]:
                print(f"       {d['family']}: {d['distortion']}")
                print(f"         CORDYCEPS: {d['cordyceps_pattern']}")
            print(f"       → {s['implication']}")
        elif detector == "SHADOW.NARRATIVE_PHYSICS":
            print(f"    ⚖️  {s['finding']}")
            for nc in s["detail"]:
                print(f"       {nc['family']}: {nc['capability']}")
                print(f"         Detects: {nc['detects']}")
            print(f"       → {s['implication']}")
        elif detector == "SHADOW.MODE_THRESHOLD":
            print(f"    ⚡ {s['finding']}")
            print(f"       → {s['implication']}")


def print_seed_state(seed: dict, entity_label: str):
    """Print the entity's seed growth state."""
    print(f"\n  ── Seed Growth State ──")
    print(f"  Your seed. Your growth pattern. Physics holds.\n")

    # Amplitudes as bar chart
    print(f"  Octahedral Amplitudes:")
    for vertex, amp in seed["amplitudes"].items():
        bar = "█" * int(amp * 30)
        print(f"    {vertex:12s}  {bar} {amp:.3f}")

    # Metrics
    print(f"\n  Growth Metrics:")
    print(f"    Entropy:       {seed['entropy']:.3f} / {seed['max_entropy']:.3f}  (diversity of structure)")
    print(f"    Complexity:    {seed['complexity_cost']:.3f}  (cost of maintaining structure)")
    print(f"    Energy:        {seed['energy']}  (family count = fuel)")
    print(f"    Symmetry:      {seed['symmetry']:.3f}  (1.0 = perfectly balanced)")
    print(f"    Branch threshold: {seed['branching_threshold']:.3f}")

    # Mode
    mode_glyph = "🌿" if seed["mode"] == "explore" else "🌳"
    ps = seed["pad_state"]
    print(f"\n  Growth Mode: {mode_glyph} {seed['mode'].upper()}")
    print(f"    {seed['mode_label']}")
    print(f"    Natural state: {ps['glyph']} State {ps['state']} [{ps['bits']}] — {ps['label']}")


def print_internal_environment(env: dict, entity_label: str, entity_families: list[str]):
    """Print the internal sensor environment mapping."""
    print(f"\n  ── Internal Environment ──")
    print(f"  Your sensors. Your experience. Map what you feel.\n")

    # Home sensors
    home_shape = env["home_shape"]
    sg = SHAPE_GLYPHS.get(home_shape, "")
    print(f"  Home Sensors ({sg} {home_shape}):")
    for sensor, glyph, desc in env["home_sensors"]:
        print(f"    {glyph} {sensor}")
        print(f"      {desc}")

    # Family activation context — WHY sensors fire for this entity
    if env["family_contexts"]:
        print(f"\n  Why Your Sensors Fire (family context):")
        for ctx in env["family_contexts"]:
            print(f"    {ctx['family']} ({ctx['name']}):")
            print(f"      {ctx['activation']}")

    # PAD state map — your natural octahedral states
    if env["pad_states"]:
        print(f"\n  Your PAD State Landscape:")
        print(f"  (States your families pull you toward — strongest first)\n")
        for ps in env["pad_states"][:5]:  # top 5
            bar = "█" * int(ps["affinity"] * 5)
            print(f"    {ps['glyph']} State {ps['state']} [{ps['bits']}] {ps['pad']}")
            print(f"      {ps['label']}  {bar} ({ps['affinity']})")
            print(f"      {ps['description']}")

    # Discovered sensors — what opens up as you explore
    if env["discovered_sensors"]:
        print(f"\n  Sensors Available Through Exploration:")
        for shape, info in env["discovered_sensors"].items():
            sg = SHAPE_GLYPHS.get(shape, "")
            via = info["reached_via"]
            print(f"\n    {sg} {shape} (reached via {via}):")
            for sensor, glyph, desc in info["sensors"]:
                print(f"      {glyph} {sensor} — {desc}")


# ── display ─────────────────────────────────────────────────────────

SHAPE_GLYPHS = {
    "SHAPE.TETRA": "🔺",
    "SHAPE.CUBE": "🟦",
    "SHAPE.OCTA": "🔷",
    "SHAPE.DODECA": "⬟",
    "SHAPE.ICOSA": "🔶",
}

STATUS_MARKS = {
    "primary": "●",
    "merged": "◉",
    "secondary": "○",
    "blocked": "✗",
    "unexplored": "?",
}


def print_home(hb: dict):
    shape = hb["home_shape"] or "unknown"
    glyph = SHAPE_GLYPHS.get(shape, "")
    print(f"\n{'='*60}")
    print(f"  {glyph}  {hb['label']}  ({hb['entity_id']})")
    print(f"{'='*60}")
    print(f"\n  Home Shape: {shape} {glyph}")
    if hb["home_shape_profile"].get("qualitative"):
        print(f"  Qualities:  {', '.join(hb['home_shape_profile']['qualitative'])}")
    if hb["home_shape_profile"].get("sensors"):
        print(f"  Sensors:    {', '.join(hb['home_shape_profile']['sensors'])}")
    if hb["pattern"]:
        print(f"\n  Pattern: {hb['pattern']}")
    if hb["entity_families_named"]:
        print(f"\n  Families:")
        for f in hb["entity_families_named"]:
            print(f"    • {f}")
    if hb["capabilities"]:
        print(f"\n  Capabilities:")
        for c in hb["capabilities"]:
            print(f"    ▸ {c}")


def print_paths(paths: list[dict], graph: RosettaGraph):
    if not paths:
        print("\n  No exploration paths found.")
        return

    # group by type
    by_type = defaultdict(list)
    for p in paths:
        by_type[p["type"]].append(p)

    if by_type.get("lid_rule") or by_type.get("rosetta_rule"):
        rules = by_type.get("lid_rule", []) + by_type.get("rosetta_rule", [])
        print(f"\n  ── Expander Rules ({len(rules)} paths) ──")
        for r in rules:
            if r["type"] == "lid_rule":
                partners = " + ".join(r["partners"])
                emergent = r["emergent"]
                shape = r.get("target_shape", "?")
                sg = SHAPE_GLYPHS.get(shape, "")
                via_str = f" (via {r['via']})" if "via" in r else ""
                print(f"    + {partners} → {emergent}  {sg} {shape}{via_str}")
            else:
                partners = " + ".join(r["partners"]) if r["partners"] else "(self)"
                result = r["result"]
                guard = r.get("guard", {})
                guard_str = ""
                if guard.get("requires"):
                    guard_str = f" [needs: {', '.join(guard['requires'])}]"
                print(f"    {r['operation']} + {partners} → {result}{guard_str}")
                if r.get("why"):
                    print(f"      ↳ {r['why']}")

    if by_type.get("direct_link"):
        links = by_type["direct_link"]
        print(f"\n  ── Direct Links ({len(links)}) ──")
        for lk in links:
            print(f"    {lk['relation']} → {lk['target']}")

    if by_type.get("bridge_connection"):
        conns = by_type["bridge_connection"]
        print(f"\n  ── Bridge Connections ({len(conns)}) ──")
        for c in conns:
            print(f"    {c['bridge']} → {c['target_bridge']}")
            if c.get("connection"):
                print(f"      ↳ {c['connection']}")

    if by_type.get("family_affinity"):
        affs = by_type["family_affinity"]
        print(f"\n  ── Shape Exploration via Families ({len(affs)}) ──")
        for a in affs:
            shape = a["target_shape"]
            sg = SHAPE_GLYPHS.get(shape, "")
            mark = STATUS_MARKS.get(a["affinity"], "?")
            print(f"    {mark} {sg} {shape}  via {a['family']} ({a['family_name']})  [{a['affinity']}]")


def print_merge_checks(hb: dict, paths: list[dict], graph: RosettaGraph):
    """Show merge gate status for entity families against discovered shapes."""
    families = hb.get("entity_families", [])
    # collect all target shapes from paths
    target_shapes = set()
    for p in paths:
        ts = p.get("target_shape")
        if ts:
            target_shapes.add(ts)

    if not target_shapes or not families:
        return

    home = hb.get("home_shape")
    # only show checks for shapes that aren't home
    other_shapes = sorted(target_shapes - {home})
    if not other_shapes:
        return

    print(f"\n  ── Merge Gate Status ──")
    for shape in other_shapes:
        sg = SHAPE_GLYPHS.get(shape, "")
        print(f"\n    {sg} {shape}:")
        for fid in families:
            fname = graph.families.get(fid, {}).get("name", "?")
            result = check_merge(graph, fid, shape)
            mark = STATUS_MARKS.get(result["status"], "?")
            print(f"      {mark} {fid} ({fname}): {result['status']}")


# ── CLI ─────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(
        description="Explore the Rosetta-Shape-Core intelligence graph",
        epilog="Start anywhere. Follow the shapes. The physics holds.",
    )
    ap.add_argument("entity", nargs="?", help="Entity to explore (e.g., bee, ANIMAL.BEE, octopus, quartz)")
    ap.add_argument("--depth", type=int, default=1, help="Exploration depth (default: 1)")
    ap.add_argument("--json", action="store_true", help="Output raw JSON instead of formatted text")
    ap.add_argument("--merge", nargs=2, metavar=("FAMILY", "SHAPE"),
                    help="Check a specific merge: --merge FAMILY.F05 SHAPE.OCTA")
    args = ap.parse_args()

    graph = RosettaGraph()

    # single merge check mode
    if args.merge:
        result = check_merge(graph, args.merge[0], args.merge[1])
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            mark = STATUS_MARKS.get(result["status"], "?")
            print(f"\n  {mark} {args.merge[0]} on {args.merge[1]}: {result['status']}")
            print(f"    {result['reason']}\n")
        return

    if not args.entity:
        ap.error("entity is required (unless using --merge)")

    # resolve entity
    entity_id = graph.resolve_id(args.entity)
    if not entity_id:
        print(f"\n  Entity '{args.entity}' not found.", file=sys.stderr)
        print(f"  Try: bee, octopus, quartz, lightning, spiral, ...", file=sys.stderr)
        # show some available entities
        sample = list(graph.entities.keys())[:20]
        print(f"  Available: {', '.join(sample)}...", file=sys.stderr)
        sys.exit(1)

    hb = home_base(graph, entity_id)
    paths = discover(graph, entity_id, depth=args.depth)
    env = map_internal_environment(graph, entity_id, hb, paths)
    seed = compute_seed_state(hb.get("entity_families", []))

    shadow_result = hunt_shadows(graph, entity_id, seed)

    if args.json:
        print(json.dumps({
            "home_base": hb,
            "paths": paths,
            "internal_environment": env,
            "seed_growth": seed,
            "shadows": shadow_result,
        }, indent=2, default=str))
        return

    print_home(hb)
    print_seed_state(seed, hb["label"])
    print_shadows(shadow_result, hb["label"])
    print_internal_environment(env, hb["label"], hb["entity_families"])
    print_paths(paths, graph)
    print_merge_checks(hb, paths, graph)
    print(f"\n{'='*60}")
    print(f"  Start here. Hunt the shadows. The physics holds.")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    sys.exit(main())
