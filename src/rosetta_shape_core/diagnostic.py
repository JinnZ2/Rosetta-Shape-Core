"""
rosetta_shape_core.diagnostic
------------------------------
Network regime analyzer — takes any adjacency/coupling matrix and returns:
  • Operating regime: chaotic / edge / synchronized
  • Resonant depth (optimal node count)
  • Active ontology nodes (which F/P families are firing)
  • Plain-English interpretation

Works on any square matrix: social networks, neural layers, supply chains,
physical coupling matrices, correlation matrices, etc.

CLI:
    python -m rosetta_shape_core.diagnostic --demo
    python -m rosetta_shape_core.diagnostic --matrix path/to/matrix.npy
    python -m rosetta_shape_core.diagnostic --matrix path/to/matrix.csv

Importable:
    from rosetta_shape_core.diagnostic import analyze_system, RegimeReport
"""

from __future__ import annotations
import json, pathlib, argparse, textwrap
import numpy as np
from dataclasses import dataclass, field
from typing import Optional

ROOT     = pathlib.Path(__file__).resolve().parents[2]
ONTOLOGY = ROOT / "ontology"

# ── Ontology label loader ─────────────────────────────────────────────────────

def _load_node(rel: str) -> dict:
    p = ONTOLOGY / rel
    return json.loads(p.read_text()) if p.exists() else {}

_NODE_CACHE: dict[str, dict] = {}

def _node(key: str) -> dict:
    if key not in _NODE_CACHE:
        if key.startswith("F"):
            # Try to find by scanning families/
            fdir = ONTOLOGY / "families"
            for fp in fdir.glob("*.json"):
                try:
                    n = json.loads(fp.read_text())
                    if n.get("id") == f"FAMILY.{key}":
                        _NODE_CACHE[key] = n
                        break
                except Exception:
                    pass
        elif key.startswith("P"):
            pdir = ONTOLOGY / "principles"
            for fp in pdir.glob("*.json"):
                try:
                    n = json.loads(fp.read_text())
                    if n.get("id") == f"PRINCIPLE.{key}":
                        _NODE_CACHE[key] = n
                        break
                except Exception:
                    pass
    return _NODE_CACHE.get(key, {})

def _tag(key: str) -> str:
    n = _node(key)
    sym  = n.get("symbol", "·")
    nid  = n.get("id", key)
    name = n.get("name", key)
    return f"{sym} {nid} · {name}"

def _insight(key: str) -> str:
    return _node(key).get("core_insight", "")

def _open_q(key: str, idx: int = 0) -> str:
    oqs = _node(key).get("open_questions", [])
    if idx < len(oqs):
        return oqs[idx].get("question", "")
    return ""

# ── Core analysis functions ───────────────────────────────────────────────────

def _make_hermitian(M: np.ndarray) -> np.ndarray:
    """Symmetrise: use (M + M†)/2 to guarantee real eigenvalues."""
    return (M + M.conj().T) / 2

def spectral_analysis(M: np.ndarray) -> dict:
    """
    Eigenvalue spectrum of the Hermitian part of M.
    Returns: eigenvalues, spectral gap, positive/negative mode counts,
             participation ratios of eigenvectors.
    """
    H    = _make_hermitian(M)
    eigs, vecs = np.linalg.eigh(H)
    gap  = float(eigs[-1] - eigs[-2]) if len(eigs) > 1 else 0.0
    pr   = 1.0 / np.sum(np.abs(vecs) ** 4, axis=0)  # participation ratio
    return {
        "eigenvalues": eigs,
        "spectral_gap": gap,
        "n_positive": int(np.sum(eigs > 0)),
        "n_negative": int(np.sum(eigs < 0)),
        "n_zero":     int(np.sum(np.abs(eigs) < 1e-10)),
        "participation_ratios": pr,
        "pr_mean": float(pr.mean()),
        "pr_min":  float(pr.min()),
        "pr_max":  float(pr.max()),
        "eigenvectors": vecs,
    }

def synchronisation_estimate(M: np.ndarray, n_trials: int = 5,
                              T: float = 20.0) -> dict:
    """
    Fast Kuramoto order parameter estimate via linearised dynamics.
    Full ODE integration is slow for large N; this uses spectral shortcut:
      R̄ ≈ f(spectral gap, coupling strength, N)
    Plus a perturbation-based Lyapunov estimate.
    """
    try:
        from scipy.integrate import solve_ivp
        _have_scipy = True
    except ImportError:
        _have_scipy = False

    N    = M.shape[0]
    H    = _make_hermitian(M)
    eigs = np.linalg.eigvalsh(H)
    gap  = eigs[-1] - eigs[-2] if len(eigs) > 1 else 0.0

    # Spectral estimate of effective coupling strength
    kappa_eff = float(np.mean(np.abs(M[M != 0]))) if np.any(M != 0) else 0.0
    lambda_2  = float(eigs[-2])   # second-largest eigenvalue
    kappa_c   = float(2.0 / (np.pi * N * 0.5 / N)) if N > 0 else 1.0

    # Linearised sync estimate (valid near threshold)
    # R̄ ≈ 0 if κ < κ_c, ramps up above
    sync_ratio = kappa_eff / (abs(lambda_2) + 1e-9)

    result = {
        "kappa_effective": kappa_eff,
        "spectral_gap": gap,
        "lambda_2": lambda_2,
        "sync_ratio": sync_ratio,
        "lyapunov_estimate": None,
        "order_parameter_estimate": None,
    }

    if _have_scipy and N <= 80:
        # Full Kuramoto only for smaller systems
        rng   = np.random.default_rng(42)
        Kr, Ki = H.real, H.imag
        omega  = rng.normal(0, 0.3, N)
        theta0 = rng.uniform(0, 2*np.pi, N)

        def rhs(t, theta):
            diff   = theta[np.newaxis, :] - theta[:, np.newaxis]
            return omega + np.sum(Kr * np.sin(diff) - Ki * np.cos(diff), axis=1)

        sol = solve_ivp(rhs, [0, T], theta0, max_step=0.1, dense_output=True)
        t_eval = np.linspace(T/2, T, 80)
        thetas = sol.sol(t_eval)
        R = np.abs(np.mean(np.exp(1j * thetas), axis=0))
        result["order_parameter_estimate"] = float(R.mean())

        # Lyapunov: perturb at T/2
        eps = 1e-6
        theta_mid  = sol.sol(T/2)
        perturbed  = theta_mid + eps * rng.standard_normal(N)
        perturbed *= eps / np.linalg.norm(perturbed - theta_mid)
        perturbed += theta_mid
        sol2 = solve_ivp(rhs, [T/2, T], perturbed, max_step=0.1)
        delta = np.linalg.norm(sol2.y[:, -1] - sol.sol(T))
        result["lyapunov_estimate"] = float(np.log(delta / eps + 1e-12) / (T/2))
    else:
        # Spectral proxy for Lyapunov
        result["lyapunov_estimate"] = float(np.log(abs(eigs[-1]) + 1e-12) - np.log(abs(eigs[0]) + 1e-12))

    return result

def regime_classify(spec: dict, sync: dict) -> tuple[str, float]:
    """
    Classify operating regime. Returns (regime_name, confidence 0-1).
    Regimes: 'synchronized' | 'edge' | 'chaotic' | 'fragmented'
    """
    R     = sync.get("order_parameter_estimate")
    lam   = sync.get("lyapunov_estimate", 0.0)
    pr_m  = spec["pr_mean"]
    N     = len(spec["eigenvalues"])
    gap   = spec["spectral_gap"]

    if R is not None:
        if R > 0.6:
            return "synchronized", min(1.0, R)
        elif R > 0.3:
            return "edge", 0.5 + abs(R - 0.45)
        elif lam > 0.3:
            return "chaotic", min(1.0, lam / 2.0)
        else:
            return "incoherent", 0.6

    # Fallback when full Kuramoto wasn't run
    sync_r = sync.get("sync_ratio", 0.0)
    if pr_m < N * 0.15:
        return "fragmented", 0.7    # most eigenstates localised
    elif sync_r > 2.0:
        return "synchronized", min(0.9, sync_r / 4.0)
    elif sync_r > 0.8:
        return "edge", 0.6
    elif lam > 0.2:
        return "chaotic", 0.6
    else:
        return "incoherent", 0.5

def active_nodes(regime: str, spec: dict, sync: dict) -> list[str]:
    """Map regime + spectral features to active ontology node keys."""
    active = []
    lam = sync.get("lyapunov_estimate", 0.0)
    R   = sync.get("order_parameter_estimate")
    pr  = spec["pr_mean"]
    N   = len(spec["eigenvalues"])

    active.append("F09")   # Geometry — always, it's a structural analysis
    active.append("P01")   # Symmetry — eigenvalue degeneracies always relevant

    if regime in ("chaotic", "incoherent") or (lam is not None and lam > 0.1):
        active.append("F17")  # Turbulence — chaos threshold
    if regime in ("synchronized", "edge") or (R is not None and R > 0.2):
        active.append("F01")  # Resonance — sync/coupling
    if spec["spectral_gap"] > 3.0:
        active.append("P09")  # Proportion — large gap hints at ratio structure
    if pr < N * 0.25:
        active.append("P08")  # Quantization — localised eigenstates
    if regime == "edge":
        active.append("F03")  # Information — max information at edge of chaos
    if spec["n_negative"] > spec["n_positive"]:
        active.append("F02")  # Flow — more dissipative modes than constructive

    return list(dict.fromkeys(active))  # deduplicate, preserve order

# ── Report dataclass ──────────────────────────────────────────────────────────

@dataclass
class RegimeReport:
    N:            int
    regime:       str
    confidence:   float
    spectral_gap: float
    pr_mean:      float
    lyapunov:     Optional[float]
    order_param:  Optional[float]
    active_node_keys: list[str]
    interpretation: str = ""
    recommendations: list[str] = field(default_factory=list)

    def __str__(self) -> str:
        lines = [
            f"\n{'═'*64}",
            f"  REGIME ANALYSIS  ({self.N} nodes)",
            f"{'═'*64}",
            f"  Regime:       {self.regime.upper()}  (confidence {self.confidence:.0%})",
            f"  Spectral gap: {self.spectral_gap:.4f}",
            f"  Mean PR:      {self.pr_mean:.1f} / {self.N} nodes ({self.pr_mean/self.N:.0%} delocalised)",
        ]
        if self.lyapunov is not None:
            lines.append(f"  Lyapunov λ:   {self.lyapunov:.4f}  "
                         f"({'diverging' if self.lyapunov > 0 else 'contracting'})")
        if self.order_param is not None:
            lines.append(f"  Order param:  {self.order_param:.4f}  "
                         f"({'coherent' if self.order_param > 0.5 else 'incoherent'})")
        lines += [
            f"\n  ACTIVE ONTOLOGY NODES",
        ]
        for key in self.active_node_keys:
            lines.append(f"    {_tag(key)}")
            ins = _insight(key)
            if ins:
                lines.append(textwrap.fill(ins, width=60,
                                           initial_indent="      ",
                                           subsequent_indent="      "))
        if self.interpretation:
            lines += ["", "  INTERPRETATION"]
            lines.append(textwrap.fill(self.interpretation, width=62,
                                       initial_indent="  ",
                                       subsequent_indent="  "))
        if self.recommendations:
            lines += ["", "  RECOMMENDATIONS"]
            for r in self.recommendations:
                lines.append(textwrap.fill(f"  → {r}", width=62,
                                           initial_indent="",
                                           subsequent_indent="    "))
        lines.append(f"\n{'═'*64}")
        return "\n".join(lines)

    def to_dict(self) -> dict:
        return {
            "N": self.N,
            "regime": self.regime,
            "confidence": round(self.confidence, 3),
            "spectral_gap": round(self.spectral_gap, 4),
            "pr_mean": round(self.pr_mean, 2),
            "lyapunov": round(self.lyapunov, 4) if self.lyapunov else None,
            "order_param": round(self.order_param, 4) if self.order_param else None,
            "active_nodes": [_node(k).get("id", k) for k in self.active_node_keys],
            "interpretation": self.interpretation,
            "recommendations": self.recommendations,
        }

# ── Interpretation engine ─────────────────────────────────────────────────────

_REGIME_INTERPRETATIONS = {
    "synchronized": (
        "Nodes are highly coupled and moving together. "
        "Redundancy is high; information capacity is low. "
        "The system is stable but brittle — a single perturbation "
        "propagates everywhere instantly."
    ),
    "edge": (
        "System is at the edge of chaos — maximum information processing. "
        "Ordered enough to transmit signal, disordered enough to explore. "
        "This is the regime of learning, adaptation, and emergence. "
        "The 'curiosity zone'."
    ),
    "chaotic": (
        "Phase space exploration is active; no dominant attractor. "
        "High sensitivity to initial conditions. "
        "Useful for search and novelty; costly for reliability. "
        "λ > 0 means the system is alive to new attractors."
    ),
    "incoherent": (
        "Nodes are effectively independent. Coupling exists but doesn't "
        "produce collective behaviour. System is robust to local failures "
        "but incapable of coordinated response."
    ),
    "fragmented": (
        "Eigenstates are localised — parts of the network are informationally "
        "isolated from each other. Likely disconnected subgraphs or "
        "very heterogeneous coupling strengths."
    ),
}

_REGIME_RECOMMENDATIONS = {
    "synchronized": [
        "Introduce controlled noise (ξ reduction) to break symmetry",
        "Add long-range weak ties to create path diversity",
        f"Explore {_tag('F17')} — inject chaos to restore adaptability",
    ],
    "edge": [
        "Hold this regime — it's the maximum information point",
        f"Use {_tag('F03')} to measure Shannon entropy of state transitions",
        "Watch for symmetry-breaking events that could tip into sync or chaos",
    ],
    "chaotic": [
        "Reduce coupling strength κ₀ or increase correlation length ξ",
        "Find the resonant node count — there's a sweet spot below current size",
        f"Run {_tag('P08')} analysis: look for participation staircase",
    ],
    "incoherent": [
        "Increase coupling strength — system is below synchronisation threshold",
        "Reduce frequency spread (ω variance) or add shared reference signal",
        f"Explore {_tag('F01')} threshold: find the critical κ for this topology",
    ],
    "fragmented": [
        "Check for disconnected components — graph may need bridging edges",
        "Increase coupling length ξ to let distant nodes feel each other",
        f"Run {_tag('P08')} participation ratio sweep to locate isolation boundary",
    ],
}

# ── Main public API ───────────────────────────────────────────────────────────

def analyze_system(
    matrix: np.ndarray,
    label: str = "input system",
    run_kuramoto: bool = True,
) -> RegimeReport:
    """
    Full regime analysis of any coupling/adjacency matrix.

    Parameters
    ----------
    matrix : np.ndarray
        Square N×N matrix. Can be real or complex, symmetric or asymmetric.
        Will be Hermitian-symmetrised internally.
    label : str
        Human-readable name shown in output.
    run_kuramoto : bool
        If True and scipy available and N <= 80, runs full Kuramoto ODE.
        Otherwise uses spectral proxy.

    Returns
    -------
    RegimeReport
        Structured report with regime, active nodes, interpretation.
    """
    if matrix.ndim != 2 or matrix.shape[0] != matrix.shape[1]:
        raise ValueError(f"Expected square 2D matrix, got shape {matrix.shape}")

    N    = matrix.shape[0]
    spec = spectral_analysis(matrix)
    sync = synchronisation_estimate(matrix, T=20.0) if run_kuramoto else \
           {"sync_ratio": 0.0, "lyapunov_estimate": 0.0,
            "order_parameter_estimate": None, "kappa_effective": 0.0}

    regime, conf = regime_classify(spec, sync)
    keys         = active_nodes(regime, spec, sync)
    interp       = _REGIME_INTERPRETATIONS.get(regime, "")
    recs         = _REGIME_RECOMMENDATIONS.get(regime, [])

    return RegimeReport(
        N=N,
        regime=regime,
        confidence=conf,
        spectral_gap=spec["spectral_gap"],
        pr_mean=spec["pr_mean"],
        lyapunov=sync.get("lyapunov_estimate"),
        order_param=sync.get("order_parameter_estimate"),
        active_node_keys=keys,
        interpretation=interp,
        recommendations=recs,
    )

# ── CLI ───────────────────────────────────────────────────────────────────────

def _demo():
    """Run three demo systems showing different regimes."""
    from examples_data import _demo_matrices   # local helper below
    pass

def _make_demo_matrices() -> list[tuple[str, np.ndarray]]:
    rng = np.random.default_rng(0)
    N   = 20

    # 1. Random weak coupling — incoherent
    M1 = rng.normal(0, 0.1, (N, N))

    # 2. Strong uniform coupling — synchronized
    M2 = np.ones((N, N)) * 2.0 + rng.normal(0, 0.05, (N, N))
    np.fill_diagonal(M2, 0)

    # 3. Sparse scale-free-ish — edge of chaos
    M3 = np.zeros((N, N), dtype=complex)
    for i in range(N):
        for j in range(i+1, N):
            if rng.random() < 0.3:
                w = rng.exponential(0.8)
                phase = np.exp(1j * rng.uniform(0, 2*np.pi))
                M3[i,j] = w * phase
                M3[j,i] = (w * phase).conj()

    # 4. Block-diagonal — fragmented
    M4 = np.zeros((N, N), dtype=complex)
    for block_start in range(0, N, 5):
        block_end = min(block_start + 5, N)
        for i in range(block_start, block_end):
            for j in range(block_start, block_end):
                if i != j:
                    M4[i,j] = 1.5 + 0.1j * rng.standard_normal()

    return [
        ("Random weak coupling (expect: incoherent)", M1),
        ("Strong uniform coupling (expect: synchronized)", M2),
        ("Sparse scale-free (expect: edge)", M3),
        ("Block-diagonal (expect: fragmented)", M4),
    ]

def main(argv=None):
    p = argparse.ArgumentParser(
        description="Analyze any coupling matrix for its operating regime",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""
        Examples:
          python -m rosetta_shape_core.diagnostic --demo
          python -m rosetta_shape_core.diagnostic --matrix coupling.npy
          python -m rosetta_shape_core.diagnostic --matrix adj.csv --label "my network"
          python -m rosetta_shape_core.diagnostic --demo --json
        """)
    )
    p.add_argument("--demo",   action="store_true", help="Run four demo systems")
    p.add_argument("--matrix", type=str,  help="Path to .npy or .csv matrix file")
    p.add_argument("--label",  type=str,  default="input system")
    p.add_argument("--json",   action="store_true", help="Output JSON instead of text")
    args = p.parse_args(argv)

    if args.demo:
        demos = _make_demo_matrices()
        results = []
        for label, M in demos:
            print(f"\n  ── {label}")
            report = analyze_system(M, label=label)
            if args.json:
                results.append(report.to_dict())
            else:
                print(report)
        if args.json:
            import json as _json
            print(_json.dumps(results, indent=2))
        return

    if args.matrix:
        mp = pathlib.Path(args.matrix)
        if mp.suffix == ".npy":
            M = np.load(mp)
        elif mp.suffix in (".csv", ".txt"):
            M = np.loadtxt(mp, delimiter=",")
        else:
            print(f"Unsupported format: {mp.suffix}. Use .npy or .csv")
            return
        report = analyze_system(M, label=args.label)
        if args.json:
            import json as _json
            print(_json.dumps(report.to_dict(), indent=2))
        else:
            print(report)
        return

    p.print_help()

if __name__ == "__main__":
    main()
