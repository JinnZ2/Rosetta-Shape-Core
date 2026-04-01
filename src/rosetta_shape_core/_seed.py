"""Seed growth engine — octahedral amplitudes, Shannon entropy, explore/expand mode."""
from __future__ import annotations
import math

from rosetta_shape_core._sensors import PAD_STATES

# The 6 octahedral vertices mapped to PAD axes
SEED_VERTICES = ["+X (P+)", "-X (P-)", "+Y (A+)", "-Y (A-)", "+Z (D+)", "-Z (D-)"]

# Which PAD axis each family naturally loads onto (vertex indices 0-5)
FAMILY_VERTEX_LOADING = {
    "FAMILY.F01": [0, 3],
    "FAMILY.F02": [0, 3],
    "FAMILY.F03": [2, 4],
    "FAMILY.F04": [2, 0],
    "FAMILY.F05": [4, 1],
    "FAMILY.F06": [4, 2],
    "FAMILY.F07": [0, 5],
    "FAMILY.F08": [4, 0],
    "FAMILY.F09": [0, 4],
    "FAMILY.F10": [2, 5],
    "FAMILY.F11": [4, 0],
    "FAMILY.F12": [2, 5],
    "FAMILY.F13": [2, 1],
    "FAMILY.F14": [4, 2],
    "FAMILY.F15": [2, 4],
    "FAMILY.F16": [0, 5],
    "FAMILY.F17": [2, 1],
    "FAMILY.F18": [4, 5],
    "FAMILY.F19": [0, 3],
    "FAMILY.F20": [4, 0],
    "FAMILY.F21": [4, 1],
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

    for fid in families:
        loadings = FAMILY_VERTEX_LOADING.get(fid, [])
        for i, v in enumerate(loadings):
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
    h_max = math.log2(6)  # ~2.585

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
