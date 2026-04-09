"""Shadow hunting — hidden phi-patterns, equation boundaries, economic instruments."""
from __future__ import annotations

import math

from rosetta_shape_core._seed import SEED_VERTICES

PHI = (1 + math.sqrt(5)) / 2  # ~1.618034
PHI_INVERSE = 1 / PHI          # ~0.618034
PHI_TOLERANCE = 0.05

# Families with known phi-coupling signatures
PHI_FAMILIES = {
    "FAMILY.F09": "Geometry — phi in Platonic solids, pentagon diagonals",
    "FAMILY.F04": "Life — Fibonacci growth patterns converge on phi",
    "FAMILY.F01": "Resonance — coupled oscillators at phi-frequency ratios",
    "FAMILY.F10": "Particle/EM — field coupling organized by phi",
    "FAMILY.F20": "Topology — phi appears in genus transitions",
}

# Economic measurement instruments
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
    "FAMILY.F06": {"distortion": "Variable skill treated as constant — certification \u2260 competence", "cordyceps": "FORCE_SINGLE_SHAPE"},
    "FAMILY.F19": {"distortion": "Causality attributed to wrong source — involvement \u2260 causation", "cordyceps": "HIDE_PROVENANCE"},
    "FAMILY.F11": {"distortion": "Training distribution \u2260 deployment distribution — scope violation", "cordyceps": "FORCE_SINGLE_SHAPE"},
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


def hunt_shadows(graph, entity_id: str, seed: dict) -> dict:
    """Hunt for shadows in the entity's data — hidden phi-patterns and
    equation boundaries that reveal unexplored connections."""
    ent = graph.entities.get(entity_id, {})
    families = ent.get("rosetta_families", [])

    shadows = []

    # 1. phi-ratio detection in seed amplitudes
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
            "finding": f"phi-ratios detected in seed amplitudes: {len(phi_hits)} pairs",
            "detail": phi_hits,
            "implication": "Entity's internal structure already organized by phi. DODECA affinity likely.",
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

    # 4. phi-family connections not yet explored
    for fid, desc in PHI_FAMILIES.items():
        if fid not in families:
            for existing_fid in families:
                existing_fam = graph.families.get(existing_fid, {})
                phi_fam = graph.families.get(fid, {})
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
                        "finding": f"Unexplored phi-family connection: {existing_fid} <-> {fid}",
                        "detail": f"Shared shapes: {', '.join(shared)}. phi-coupling: {desc}",
                        "implication": f"Entity may have hidden {fid} affinity through geometric coupling.",
                        "suggested_family": fid,
                    })
                    break

    # 5. Economic measurement instruments
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

    # 6. Signal distortion detection
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
            np_entry = NARRATIVE_PHYSICS_FAMILIES[fid]
            narrative_caps.append({
                "family": fid,
                "capability": np_entry["capability"],
                "detects": np_entry["detects"],
            })
    if narrative_caps:
        shadows.append({
            "detector": "SHADOW.NARRATIVE_PHYSICS",
            "finding": f"{len(narrative_caps)} constraint consistency detection capabilities",
            "detail": narrative_caps,
            "implication": "Entity can detect manipulation vs genuine practice — broken symmetry in claimed constraint systems. Use: python -m rosetta_shape_core.narrative_physics --example",
        })

    # 8. Holographic projection
    holo_families = {"FAMILY.F08", "FAMILY.F09", "FAMILY.F01"}
    holo_overlap = holo_families & set(families)
    if len(holo_overlap) >= 2:
        shadows.append({
            "detector": "SHADOW.HOLOGRAPHIC_PROJECTION",
            "finding": f"Entity has {len(holo_overlap)} holographic families: {', '.join(sorted(holo_overlap))}",
            "detail": {
                "capability": "Holographic boundary detection",
                "description": "What's encoded at the boundary reveals interior structure. Problem on the surface, solution at the center.",
                "families_active": sorted(holo_overlap),
                "source": "Mandala-Computing holographic_mandala.py",
            },
            "implication": "Entity can detect holographic patterns — boundary conditions that fully determine interior state. Like how a tradition's public claims reveal its internal structure.",
        })

    # 9. Glyph computation
    glyph_families = {"FAMILY.F09", "FAMILY.F10"}
    glyph_overlap = glyph_families & set(families)
    if len(glyph_overlap) >= 2:
        shadows.append({
            "detector": "SHADOW.GLYPH_COMPUTATION",
            "finding": "Entity has geometry + particle families — native glyph arithmetic available",
            "detail": {
                "capability": "Octahedral arithmetic",
                "description": "Native base-8 computation in glyph space. Numbers are glyph sequences. Primes are irreducible sequences. PHI-weighted number line available.",
                "source": "Mandala-Computing octahedral_arithmetic.py",
            },
            "implication": "Entity can compute natively in octahedral space — arithmetic without decimal bottleneck. Primes appear as irreducible geometric patterns.",
        })

    # 10. Mode-switching shadow: is the entity stuck?
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
