#!/usr/bin/env python3
"""
octahedral_coupling_audit.py — Coupling Density Analysis + First-Principles Audit

Measures the critical assumption: does the GF(2) matrix stay block-diagonal at scale?

Three instruments:
  1. Coupling density vs D — what fraction of relations touch only one octahedron?
  2. Per-nullspace-vector block span — how many blocks does each vector touch?
  3. First-principles audit on coupling fraction as the falsifiable parameter.

If coupling density decays with D, the local square root claim breaks at scale.
If it holds above a threshold, there's a structural property worth investigating.

Usage:
    python examples/octahedral_coupling_audit.py
    python examples/octahedral_coupling_audit.py --json
    python examples/octahedral_coupling_audit.py --D-max 300
"""
from __future__ import annotations

import json
import math
import sys
import time
from collections import defaultdict
from math import isqrt, gcd
from typing import Dict, List, Optional, Tuple


# ── prime generation ────────────────────────────────────────────────

def generate_primes(n: int) -> List[int]:
    """Generate first n primes via sieve."""
    if n < 1:
        return []
    limit = max(20, int(n * (math.log(n) + math.log(math.log(max(n, 2))) + 2)))
    sieve = [True] * (limit + 1)
    sieve[0] = sieve[1] = False
    for i in range(2, int(limit**0.5) + 1):
        if sieve[i]:
            for j in range(i * i, limit + 1, i):
                sieve[j] = False
    primes = [i for i, v in enumerate(sieve) if v]
    return primes[:n]


def quadratic_residues_mod_p(N: int, p: int) -> set:
    """Find r such that r^2 = N mod p."""
    if p == 2:
        return {N % 2}
    if pow(N, (p - 1) // 2, p) != 1:
        return set()
    return {r for r in range(p) if (r * r) % p == N % p}


# ── sieve + relation collection ────────────────────────────────────

def collect_relations(N: int, factor_base: List[int], target: int) -> List[Dict]:
    """Collect smooth relations via trial division."""
    m = isqrt(N)
    relations = []
    residues = {p: quadratic_residues_mod_p(N, p) for p in factor_base}
    a = m + 1

    while len(relations) < target:
        Q = a * a - N
        if Q == 0:
            a += 1
            continue
        absQ = abs(Q)
        exponents = {}
        remainder = absQ
        for p in factor_base:
            if (a % p) not in residues[p]:
                continue
            while remainder % p == 0:
                exponents[p] = exponents.get(p, 0) + 1
                remainder //= p
        if remainder == 1:
            relations.append({"a": a, "Q": Q, "exp": exponents})
        a += 1

    return relations


# ── coupling density measurement ───────────────────────────────────

def measure_coupling(factor_base: List[int], relations: List[Dict]) -> Dict:
    """Measure how relations distribute across octahedral blocks.

    Returns:
        coupling_stats: {
            n_octahedra, n_relations,
            single_block_count, multi_block_count,
            coupling_density (fraction staying in ONE block),
            block_span_distribution (histogram of how many blocks each relation touches),
            max_span, mean_span,
        }
    """
    prime_to_octa = {}
    n_octa = (len(factor_base) + 2) // 3
    for i, p in enumerate(factor_base):
        prime_to_octa[p] = i // 3

    single_block = 0
    multi_block = 0
    span_counts = defaultdict(int)  # span -> count

    for rel in relations:
        blocks_touched = set()
        for p in rel["exp"]:
            if p in prime_to_octa:
                blocks_touched.add(prime_to_octa[p])
        span = len(blocks_touched)
        span_counts[span] += 1
        if span <= 1:
            single_block += 1
        else:
            multi_block += 1

    total = single_block + multi_block
    coupling_density = single_block / total if total > 0 else 0.0

    spans = []
    for rel in relations:
        blocks_touched = set()
        for p in rel["exp"]:
            if p in prime_to_octa:
                blocks_touched.add(prime_to_octa[p])
        spans.append(len(blocks_touched))

    return {
        "n_octahedra": n_octa,
        "n_relations": len(relations),
        "single_block_count": single_block,
        "multi_block_count": multi_block,
        "coupling_density": round(coupling_density, 6),
        "block_span_distribution": dict(sorted(span_counts.items())),
        "max_span": max(spans) if spans else 0,
        "mean_span": round(sum(spans) / len(spans), 3) if spans else 0,
    }


# ── matrix block analysis ──────────────────────────────────────────

def build_parity_matrix(relations: List[Dict], factor_base: List[int]) -> List[List[int]]:
    """Build GF(2) parity matrix."""
    prime_idx = {p: i for i, p in enumerate(factor_base)}
    M = []
    for rel in relations:
        row = [0] * len(factor_base)
        for p, count in rel["exp"].items():
            if p in prime_idx:
                row[prime_idx[p]] = count % 2
        M.append(row)
    return M


def analyze_block_structure(M: List[List[int]], n_octa: int) -> Dict:
    """Analyze the actual block structure of the parity matrix.

    For each pair of octahedral blocks, count how many rows have
    nonzero entries in BOTH blocks. This is the inter-block coupling.
    """
    n_rows = len(M)
    n_cols = len(M[0]) if M else 0

    # Per-block activity: which rows have nonzero entries in each block
    block_rows = {}  # block_idx -> set of row indices
    for b in range(n_octa):
        start = b * 3
        end = min(start + 3, n_cols)
        active = set()
        for i, row in enumerate(M):
            if any(row[start:end]):
                active.add(i)
        block_rows[b] = active

    # Count per-block rank (individual)
    block_ranks = []
    for b in range(n_octa):
        start = b * 3
        end = min(start + 3, n_cols)
        sub = []
        for row in M:
            block_row = row[start:end]
            if any(block_row):
                sub.append(block_row[:])
        block_ranks.append(_gf2_rank(sub))

    # Inter-block coupling: shared rows between block pairs
    coupling_pairs = 0
    coupling_total = 0
    for b1 in range(n_octa):
        for b2 in range(b1 + 1, n_octa):
            shared = len(block_rows.get(b1, set()) & block_rows.get(b2, set()))
            if shared > 0:
                coupling_pairs += 1
                coupling_total += shared

    total_pairs = n_octa * (n_octa - 1) // 2 if n_octa > 1 else 1
    coupling_fraction = coupling_pairs / total_pairs if total_pairs > 0 else 0

    return {
        "n_blocks": n_octa,
        "block_ranks": block_ranks,
        "rank_deficient_blocks": sum(1 for r in block_ranks if r < 3),
        "coupled_block_pairs": coupling_pairs,
        "total_block_pairs": total_pairs,
        "coupling_fraction": round(coupling_fraction, 6),
        "mean_coupling_rows": round(coupling_total / max(coupling_pairs, 1), 2),
    }


def _gf2_rank(rows: List[List[int]]) -> int:
    """Compute rank over GF(2)."""
    if not rows:
        return 0
    rows = [r[:] for r in rows]
    n_rows = len(rows)
    n_cols = len(rows[0])
    rank = 0
    for col in range(n_cols):
        pivot = -1
        for row in range(rank, n_rows):
            if rows[row][col]:
                pivot = row
                break
        if pivot == -1:
            continue
        rows[rank], rows[pivot] = rows[pivot], rows[rank]
        for row in range(n_rows):
            if row != rank and rows[row][col]:
                for c in range(n_cols):
                    rows[row][c] ^= rows[rank][c]
        rank += 1
    return rank


# ── nullspace vector block span ────────────────────────────────────

def find_nullspace_and_measure_span(
    M: List[List[int]], n_octa: int
) -> Dict:
    """Do GF(2) elimination, find nullspace vectors, measure block span of each."""
    rows = len(M)
    cols = len(M[0]) if M else 0

    # Augment with identity
    aug = [row[:] + [1 if j == i else 0 for j in range(rows)] for i, row in enumerate(M)]

    pivots = []
    rank = 0
    for j in range(cols):
        pivot = -1
        for i in range(rank, rows):
            if aug[i][j] == 1:
                pivot = i
                break
        if pivot == -1:
            continue
        aug[rank], aug[pivot] = aug[pivot], aug[rank]
        for i in range(rows):
            if i != rank and aug[i][j] == 1:
                aug[i] = [a ^ b for a, b in zip(aug[i], aug[rank])]
        pivots.append(j)
        rank += 1

    # Extract nullspace vectors
    null_vectors = []
    for i in range(rows):
        matrix_part = aug[i][:cols]
        if all(v == 0 for v in matrix_part):
            combo = aug[i][cols:]
            if any(v == 1 for v in combo):
                null_vectors.append(combo)

    # For each nullspace vector, measure block span
    vector_spans = []
    for vec in null_vectors:
        # Which relations are active?
        active_relations = [i for i, v in enumerate(vec) if v == 1]
        # Which blocks do those relations touch?
        blocks_touched = set()
        for ri in active_relations:
            row = M[ri]
            for b in range(n_octa):
                start = b * 3
                end = min(start + 3, cols)
                if any(row[start:end]):
                    blocks_touched.add(b)
        vector_spans.append({
            "n_active_relations": len(active_relations),
            "blocks_touched": len(blocks_touched),
            "block_indices": sorted(blocks_touched),
        })

    return {
        "matrix_rank": rank,
        "nullity": rows - rank,
        "n_nullspace_vectors": len(null_vectors),
        "vector_spans": vector_spans,
        "mean_vector_block_span": round(
            sum(v["blocks_touched"] for v in vector_spans) / max(len(vector_spans), 1), 2
        ),
        "max_vector_block_span": max(
            (v["blocks_touched"] for v in vector_spans), default=0
        ),
    }


# ── scaling sweep ──────────────────────────────────────────────────

def run_scaling_sweep(
    N: int,
    D_values: List[int],
    verbose: bool = True,
) -> List[Dict]:
    """Run coupling analysis across multiple D values.

    This is THE measurement. If coupling_density decays toward 0 with D,
    the block-diagonal assumption breaks. If it stays above a threshold,
    there's structural reality to the octahedral decomposition.
    """
    results = []

    for D in D_values:
        if verbose:
            print(f"\n  D={D:4d}  ", end="", flush=True)

        t0 = time.time()
        fb = generate_primes(D)
        target = D + 10

        # Collect relations
        relations = collect_relations(N, fb, target)
        t_sieve = time.time() - t0

        if verbose:
            print(f"sieve={t_sieve:.2f}s  ", end="", flush=True)

        # Measure coupling at relation level
        coupling = measure_coupling(fb, relations)

        # Build parity matrix and analyze block structure
        M = build_parity_matrix(relations, fb)
        n_octa = (D + 2) // 3
        block_analysis = analyze_block_structure(M, n_octa)

        # Nullspace vector span (skip for very large D — too slow)
        nullspace_analysis = None
        if D <= 200:
            t0 = time.time()
            nullspace_analysis = find_nullspace_and_measure_span(M, n_octa)
            t_null = time.time() - t0
            if verbose:
                print(f"null={t_null:.2f}s  ", end="", flush=True)

        t_total = time.time()

        result = {
            "D": D,
            "N": N,
            "n_octahedra": n_octa,
            "n_relations": len(relations),
            "sieve_time_s": round(t_sieve, 3),
            "coupling": coupling,
            "block_structure": block_analysis,
        }
        if nullspace_analysis:
            result["nullspace"] = nullspace_analysis

        results.append(result)

        if verbose:
            cd = coupling["coupling_density"]
            ms = coupling["mean_span"]
            cf = block_analysis["coupling_fraction"]
            rd = block_analysis["rank_deficient_blocks"]
            status = "LOCAL" if cd > 0.5 else "COUPLED" if cd > 0.1 else "GLOBAL"
            print(f"density={cd:.3f}  mean_span={ms:.1f}  "
                  f"block_coupling={cf:.3f}  rank_deficient={rd}  [{status}]")

    return results


# ── first-principles audit integration ─────────────────────────────

def audit_coupling_fraction(results: List[Dict]) -> Dict:
    """Apply first-principles analysis to the coupling density data.

    The falsifiable claim: "The GF(2) matrix is approximately block-diagonal,
    enabling local square roots."

    Falsification: coupling_density → 0 as D → ∞
    Confirmation: coupling_density stays above threshold as D grows
    """
    if not results:
        return {"verdict": "NO_DATA"}

    D_values = [r["D"] for r in results]
    densities = [r["coupling"]["coupling_density"] for r in results]
    mean_spans = [r["coupling"]["mean_span"] for r in results]
    block_couplings = [r["block_structure"]["coupling_fraction"] for r in results]

    # Trend analysis: is coupling density decaying?
    if len(densities) >= 3:
        # Simple linear regression on log(D) vs density
        log_D = [math.log(d) for d in D_values]
        n = len(log_D)
        mean_x = sum(log_D) / n
        mean_y = sum(densities) / n
        ss_xy = sum((log_D[i] - mean_x) * (densities[i] - mean_y) for i in range(n))
        ss_xx = sum((log_D[i] - mean_x) ** 2 for i in range(n))
        slope = ss_xy / ss_xx if ss_xx > 0 else 0
        intercept = mean_y - slope * mean_x

        # Extrapolate to RSA scale (D ~ 10^6)
        rsa_log_D = math.log(1_000_000)
        extrapolated_density = intercept + slope * rsa_log_D
    else:
        slope = 0
        intercept = densities[0] if densities else 0
        extrapolated_density = intercept

    # Mean span trend
    span_growth = (mean_spans[-1] - mean_spans[0]) / max(mean_spans[0], 0.001) if len(mean_spans) >= 2 else 0

    # Block coupling trend
    bc_growth = (block_couplings[-1] - block_couplings[0]) if len(block_couplings) >= 2 else 0

    # Verdict
    if extrapolated_density > 0.3:
        verdict = "BLOCK_DIAGONAL_PLAUSIBLE"
        confidence = "Coupling density extrapolates above 0.3 at RSA scale. Local square roots may hold."
    elif extrapolated_density > 0.0:
        verdict = "AMBIGUOUS"
        confidence = "Coupling density extrapolates positive but below 0.3. Partial locality — hybrid approach needed."
    else:
        verdict = "BLOCK_DIAGONAL_FAILS"
        confidence = "Coupling density extrapolates to zero or negative. Matrix becomes globally coupled at scale. Local square roots break."

    return {
        "claim": "GF(2) matrix is approximately block-diagonal at scale",
        "falsification_test": "coupling_density → 0 as D → ∞",
        "measured_D_range": [min(D_values), max(D_values)],
        "density_at_min_D": densities[0],
        "density_at_max_D": densities[-1],
        "trend_slope": round(slope, 6),
        "trend_intercept": round(intercept, 6),
        "extrapolated_density_at_D_1M": round(max(extrapolated_density, 0), 6),
        "mean_span_growth": round(span_growth, 3),
        "block_coupling_growth": round(bc_growth, 6),
        "verdict": verdict,
        "confidence": confidence,
        "raw_densities": {D_values[i]: densities[i] for i in range(len(D_values))},
        "raw_mean_spans": {D_values[i]: mean_spans[i] for i in range(len(D_values))},
        "raw_block_couplings": {D_values[i]: block_couplings[i] for i in range(len(D_values))},
    }


# ── report generation ──────────────────────────────────────────────

def generate_report(results: List[Dict], audit: Dict) -> str:
    """Generate markdown report."""
    lines = [
        "# Octahedral NFS — Coupling Density Audit",
        "",
        "## Claim Under Test",
        f"> {audit['claim']}",
        "",
        f"**Falsification test:** {audit['falsification_test']}",
        "",
        "## Scaling Data",
        "",
        "| D | Octahedra | Coupling Density | Mean Span | Block Coupling | Rank Deficient |",
        "|---|-----------|-----------------|-----------|----------------|----------------|",
    ]

    for r in results:
        c = r["coupling"]
        b = r["block_structure"]
        lines.append(
            f"| {r['D']} | {r['n_octahedra']} | {c['coupling_density']:.4f} | "
            f"{c['mean_span']:.2f} | {b['coupling_fraction']:.4f} | "
            f"{b['rank_deficient_blocks']} |"
        )

    lines += [
        "",
        "## Nullspace Vector Block Span",
        "",
    ]

    for r in results:
        if "nullspace" in r:
            ns = r["nullspace"]
            lines.append(f"**D={r['D']}:** {ns['n_nullspace_vectors']} vectors, "
                        f"mean span={ns['mean_vector_block_span']:.1f} blocks, "
                        f"max span={ns['max_vector_block_span']} blocks")

    lines += [
        "",
        "## Trend Analysis",
        "",
        f"- Density slope (vs log D): **{audit['trend_slope']:.6f}**",
        f"- Density at smallest D: **{audit['density_at_min_D']:.4f}**",
        f"- Density at largest D: **{audit['density_at_max_D']:.4f}**",
        f"- Extrapolated density at D=10^6: **{audit['extrapolated_density_at_D_1M']:.4f}**",
        f"- Mean span growth: **{audit['mean_span_growth']:.1%}**",
        f"- Block coupling growth: **{audit['block_coupling_growth']:.4f}**",
        "",
        "## Verdict",
        "",
        f"**{audit['verdict']}**",
        "",
        audit["confidence"],
        "",
        "## What This Means",
        "",
    ]

    if audit["verdict"] == "BLOCK_DIAGONAL_FAILS":
        lines += [
            "The matrix becomes globally coupled as D grows. This means:",
            "- Nullspace vectors span many blocks, not just one",
            "- The local square root decomposition requires cross-block computation",
            "- Memory savings from RIM are real, but computational savings from block structure are not",
            "- At RSA scale (D ~ 10^6), the square root step reverts to standard large-number arithmetic",
            "",
            "The RIM sieve contribution (memory reduction) remains valid independently of this result.",
        ]
    elif audit["verdict"] == "AMBIGUOUS":
        lines += [
            "Coupling density is declining but not to zero in this range. Possibilities:",
            "- It stabilizes at a nonzero floor (structural property — worth investigating)",
            "- It continues declining (block structure breaks at larger D)",
            "- Need measurements at D=1000+ to distinguish these cases",
            "",
            "Recommended: extend D range and measure at 500, 1000, 2000.",
        ]
    else:
        lines += [
            "Coupling density stays above threshold. The block-diagonal structure appears",
            "to be a genuine property of the octahedral decomposition, not an artifact of small D.",
            "",
            "CAUTION: This is necessary but not sufficient for RSA-scale validity.",
            "Additional verification needed: D=10000+, comparison with standard GNFS.",
        ]

    return "\n".join(lines)


# ── main ───────────────────────────────────────────────────────────

def main():
    import argparse
    ap = argparse.ArgumentParser(description="Octahedral NFS coupling density audit")
    ap.add_argument("--N", type=int, default=1003, help="Number to factor (default: 1003)")
    ap.add_argument("--D-max", type=int, default=200, help="Maximum D to test (default: 200)")
    ap.add_argument("--json", action="store_true", help="Output JSON instead of markdown")
    args = ap.parse_args()

    N = args.N
    D_max = args.D_max

    # Build D schedule — logarithmic spacing
    D_values = []
    d = 20
    while d <= D_max:
        D_values.append(d)
        d = int(d * 1.5) if d < 100 else d + 50
    if D_values[-1] != D_max and D_max not in D_values:
        D_values.append(D_max)

    print(f"  Octahedral NFS Coupling Density Audit")
    print(f"  N = {N}, D range: {D_values}")
    print(f"  {'='*65}")

    # Run sweep
    results = run_scaling_sweep(N, D_values)

    # Audit
    audit = audit_coupling_fraction(results)

    if args.json:
        print(json.dumps({"results": results, "audit": audit}, indent=2))
    else:
        report = generate_report(results, audit)
        print(f"\n{'='*65}")
        print(report)

    # Summary
    print(f"\n  VERDICT: {audit['verdict']}")
    print(f"  {audit['confidence']}")


if __name__ == "__main__":
    main()
