#!/usr/bin/env python3
"""
Audit Rosetta-Shape-Core's own system constants using the
Six Sigma First-Principles Validation Engine.

Wraps compute_seed_state so the audit engine can sweep BRANCHING_K
and SATURATION_FRACTION, then reports sensitivity, boundary failures,
FMEA, and bias flags for the seed-growth subsystem.

Usage:
    python examples/audit_system_constants.py           # markdown report
    python examples/audit_system_constants.py --json    # JSON report
"""
from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

# Ensure the package is importable when running from the repo root.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from rosetta_shape_core.first_principles_audit import (
    AssumptionRecord,
    DesignChoice,
    ParameterSpec,
    full_audit,
    generate_report,
)
from rosetta_shape_core.explore import (
    FAMILY_VERTEX_LOADING,
    PAD_STATES,
    SEED_VERTICES,
    compute_seed_state,
)


# ── representative family set used during the audit ──────────────
# Pick a non-trivial mix so the seed state is not degenerate.
_AUDIT_FAMILIES = [
    "FAMILY.F01",  # Resonance
    "FAMILY.F04",  # Life
    "FAMILY.F09",  # Geometry
    "FAMILY.F12",  # Defense
]


# ── wrapper: numeric parameters in, entropy out ──────────────────

def seed_entropy(
    branching_k: float = 1.5,
    saturation_fraction: float = 0.45,
    phi_tolerance: float = 0.05,
) -> float:
    """Compute seed-state Shannon entropy for a fixed family set.

    The three numeric parameters are the system constants defined in
    explore.py.  We patch them into the module-level globals, call
    compute_seed_state, and return the entropy as a plain float so the
    audit engine can sweep and test each parameter independently.
    """
    import rosetta_shape_core.explore as _explore

    # Temporarily override module constants
    orig_k = _explore.BRANCHING_K
    orig_sat = _explore.SATURATION_FRACTION
    orig_tol = _explore.PHI_TOLERANCE

    try:
        _explore.BRANCHING_K = branching_k
        _explore.SATURATION_FRACTION = saturation_fraction
        _explore.PHI_TOLERANCE = phi_tolerance

        state = compute_seed_state(_AUDIT_FAMILIES)
        return float(state["entropy"])
    finally:
        # Restore originals so subsequent calls are clean
        _explore.BRANCHING_K = orig_k
        _explore.SATURATION_FRACTION = orig_sat
        _explore.PHI_TOLERANCE = orig_tol


# ── parameter specs ──────────────────────────────────────────────

SPECS = {
    "branching_k": ParameterSpec(
        name="branching_k",
        physical_meaning="complexity-to-energy ratio for explore/expand threshold",
        source="design choice",
        units="dimensionless",
        min_value=0.1,
        max_value=10.0,
    ),
    "saturation_fraction": ParameterSpec(
        name="saturation_fraction",
        physical_meaning="maximum energy any single octahedral vertex can hold",
        source="design choice",
        units="fraction",
        min_value=1.0 / 6,   # uniform lower bound
        max_value=1.0,        # one vertex takes everything
    ),
    "phi_tolerance": ParameterSpec(
        name="phi_tolerance",
        physical_meaning="how close to golden ratio counts as phi-match",
        source="design choice",
        units="dimensionless",
        min_value=0.001,
        max_value=0.5,
    ),
}


# ── assumptions ──────────────────────────────────────────────────

ASSUMPTIONS = [
    AssumptionRecord(
        id="A1",
        text="Shannon entropy is the correct complexity measure for seed states",
        domain="information theory",
        falsifiable=True,
        falsification_test=(
            "Compare exploration outcomes using Renyi entropy or "
            "Kolmogorov complexity; if rankings change, Shannon is insufficient"
        ),
    ),
    AssumptionRecord(
        id="A2",
        text="A single scalar branching_k is sufficient to govern explore/expand transitions",
        domain="seed physics",
        falsifiable=True,
        falsification_test=(
            "Test per-family or per-vertex branching thresholds; if entity "
            "behavior improves, the single-k model is too coarse"
        ),
    ),
    AssumptionRecord(
        id="A3",
        text="Saturation cap should be the same for all six octahedral vertices",
        domain="seed physics",
        falsifiable=True,
        falsification_test=(
            "Allow asymmetric saturation limits per axis; if growth patterns "
            "become more realistic, the uniform cap is a simplification"
        ),
    ),
    AssumptionRecord(
        id="A4",
        text="Phi-tolerance of 0.05 captures meaningful golden-ratio signals without false positives",
        domain="shadow hunting",
        falsifiable=True,
        falsification_test=(
            "Sweep tolerance from 0.001 to 0.2 and measure precision/recall "
            "of known phi-coupled families; optimal tolerance may differ"
        ),
    ),
    AssumptionRecord(
        id="A5",
        text="Family vertex loadings are fixed integer mappings, not learned weights",
        domain="ontology",
        falsifiable=True,
        falsification_test=(
            "Use empirical data to fit vertex loadings; if fitted values "
            "diverge significantly from hand-assigned integers, the mapping "
            "is biased"
        ),
    ),
]


# ── design choices ───────────────────────────────────────────────

DESIGN_CHOICES = [
    DesignChoice(
        description="BRANCHING_K fixed at 1.5",
        rationale=(
            "Balances exploration and consolidation so that entities with "
            "2+ families can explore while single-family entities consolidate"
        ),
        alternatives=[
            "Adaptive k based on entity age or discovery count",
            "Per-family k values",
            "k derived from thermodynamic free-energy analogy",
        ],
        who_decided="system designer",
    ),
    DesignChoice(
        description="SATURATION_FRACTION fixed at 0.45",
        rationale=(
            "Prevents any single PAD axis from dominating, enforcing "
            "distributional diversity in seed states"
        ),
        alternatives=[
            "Dynamic saturation that loosens as entity matures",
            "Per-axis saturation limits",
            "No saturation (rely on normalization alone)",
        ],
        who_decided="system designer",
    ),
    DesignChoice(
        description="PHI_TOLERANCE fixed at 0.05",
        rationale="Empirically chosen to match known phi-coupled families without noise",
        alternatives=[
            "Scale-dependent tolerance (tighter for small amplitudes)",
            "Statistical threshold based on random baseline",
        ],
        who_decided="system designer",
    ),
]


# ── base params and ranges for the audit sweep ───────────────────

BASE_PARAMS = {
    "branching_k": 1.5,
    "saturation_fraction": 0.45,
    "phi_tolerance": 0.05,
}

PARAM_RANGES = {
    "branching_k": (0.1, 5.0),
    "saturation_fraction": (1.0 / 6, 1.0),
    "phi_tolerance": (0.001, 0.5),
}

# Entropy is bounded [0, log2(6)] so set specification limits around
# the physically meaningful band.
H_MAX = math.log2(6)  # ~2.585
LSL = 0.0
USL = H_MAX


# ── main ─────────────────────────────────────────────────────────

def run_audit(fmt: str = "markdown") -> str:
    """Execute the full audit and return the formatted report string."""
    result = full_audit(
        func=seed_entropy,
        base_params=BASE_PARAMS,
        param_ranges=PARAM_RANGES,
        specs=SPECS,
        assumptions=ASSUMPTIONS,
        design_choices=DESIGN_CHOICES,
        lsl=LSL,
        usl=USL,
    )
    return generate_report(result, fmt=fmt)


def main():
    parser = argparse.ArgumentParser(
        description="Audit Rosetta-Shape-Core system constants (BRANCHING_K, "
                    "SATURATION_FRACTION, PHI_TOLERANCE) using the Six Sigma "
                    "First-Principles engine.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output the audit as JSON instead of Markdown",
    )
    args = parser.parse_args()

    fmt = "json" if args.json else "markdown"
    report = run_audit(fmt=fmt)
    print(report)


if __name__ == "__main__":
    main()
