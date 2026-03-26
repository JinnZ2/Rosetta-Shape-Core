"""
kappa_sync_threshold.py
-----------------------
Sweep coupling strength κ₀ from 0.1 → 3.0 for octahedral and icosahedral
phi-lattices. Find the synchronisation threshold: the κ₀ where the order
parameter R̄ first climbs above 0.5.

Key question: does the icosahedral lattice (φ intrinsic to directions)
synchronise at a *lower* κ₀ than octahedral (φ only in shell radii)?
The gap between those two thresholds is the measurable advantage of
embedding φ structurally.

Ontology nodes:
  F01  · Resonance       — synchronisation order parameter R̄
  F09  · Geometry        — icosahedral vs octahedral direction sets
  P09  · Proportion      — φ as structural vs imposed ratio
  P01  · Symmetry        — threshold sharpness = symmetry of coupling graph
  F17  · Turbulence      — chaotic regime below threshold; λ > 0
"""

import json
import pathlib
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.integrate import solve_ivp

# ── Ontology labels ───────────────────────────────────────────────────────────

REPO_ROOT = pathlib.Path(__file__).parent.parent
ONTOLOGY  = REPO_ROOT / "ontology"

def _load(rel: str) -> dict:
    p = ONTOLOGY / rel
    return json.loads(p.read_text()) if p.exists() else {}

NODES = {
    "F01": _load("families/f01-resonance.json"),
    "F09": _load("families/f09-geometry.json"),
    "F17": _load("families/f17-turbulence.json"),
    "P01": _load("principles/p01-symmetry.json"),
    "P09": _load("principles/p09-proportion.json"),
}

def tag(k):
    n = NODES.get(k, {})
    return f"{n.get('symbol','')} {n.get('id', k)} · {n.get('name', k)}".strip()

# ── Geometry ──────────────────────────────────────────────────────────────────

PHI   = (1 + 5**0.5) / 2
SHELLS = 5
R0    = 1.0

def octahedral_dirs():
    return np.array([
        [1,0,0],[-1,0,0],[0,1,0],[0,-1,0],[0,0,1],[0,0,-1]
    ], dtype=float)

def icosahedral_dirs():
    d = np.array([
        [ 0,  1,  PHI], [ 0, -1,  PHI], [ 0,  1, -PHI], [ 0, -1, -PHI],
        [ 1,  PHI,  0], [-1,  PHI,  0], [ 1, -PHI,  0], [-1, -PHI,  0],
        [PHI,  0,  1], [-PHI,  0,  1], [PHI,  0, -1], [-PHI,  0, -1],
    ], dtype=float)
    return d / np.linalg.norm(d[0])

def build_lattice(dirs):
    pos = []
    for n in range(SHELLS):
        r = R0 * (PHI ** n)
        for d in dirs:
            pos.append(r * d)
    return np.array(pos)

# ── Kuramoto helpers ──────────────────────────────────────────────────────────

def make_distance_matrix(pos):
    """Pre-compute all pairwise distances — reused across κ₀ sweep."""
    N = len(pos)
    D = np.zeros((N, N))
    for i in range(N):
        for j in range(i+1, N):
            d = np.linalg.norm(pos[i] - pos[j])
            D[i, j] = D[j, i] = d
    return D

def coupling_matrix(D, kappa, xi=2.0, phi_i=None):
    N = D.shape[0]
    if phi_i is None:
        phi_i = np.zeros(N)
    K = np.zeros((N, N), dtype=complex)
    mask = D > 0
    with np.errstate(over="ignore"):
        strength = np.where(mask, kappa * np.exp(-D / xi), 0.0)
    for i in range(N):
        for j in range(i+1, N):
            if D[i,j] == 0:
                continue
            c = strength[i,j] * np.exp(1j * (phi_i[i] - phi_i[j]))
            K[i,j] = c
            K[j,i] = c.conj()
    return K

def kuramoto_rhs(t, theta, omega, Kr, Ki):
    """Vectorised RHS — much faster than the loop version."""
    diff = theta[np.newaxis, :] - theta[:, np.newaxis]   # (N,N)
    dtheta = omega + np.sum(Kr * np.sin(diff) - Ki * np.cos(diff), axis=1)
    return dtheta

def run_kuramoto(K, T=30.0, seed=None):
    """Return mean order parameter R̄ over second half of trajectory."""
    rng   = np.random.default_rng(seed)
    N     = K.shape[0]
    omega = rng.normal(0, 0.5, N)
    theta0 = rng.uniform(0, 2*np.pi, N)
    Kr, Ki = K.real, K.imag

    sol = solve_ivp(
        kuramoto_rhs, [0, T], theta0,
        args=(omega, Kr, Ki),
        max_step=0.1, dense_output=True
    )
    t_eval = np.linspace(T/2, T, 100)
    thetas  = sol.sol(t_eval)
    R = np.abs(np.mean(np.exp(1j * thetas), axis=0))
    return R.mean()

# ── κ₀ sweep ──────────────────────────────────────────────────────────────────

def sweep_kappa(pos, kappas, n_trials=3, xi=2.0, T=30.0):
    """
    For each κ₀, run n_trials Kuramoto simulations (different random phases).
    Return mean and std of R̄ across trials.
    """
    D      = make_distance_matrix(pos)
    N      = len(pos)
    rng    = np.random.default_rng(0)

    R_means, R_stds = [], []
    for kappa in kappas:
        Rs = []
        for trial in range(n_trials):
            phi_i = rng.uniform(0, 2*np.pi, N)
            K     = coupling_matrix(D, kappa, xi=xi, phi_i=phi_i)
            r     = run_kuramoto(K, T=T, seed=trial)
            Rs.append(r)
        R_means.append(np.mean(Rs))
        R_stds.append(np.std(Rs))

    return np.array(R_means), np.array(R_stds)

def find_threshold(kappas, R_means, level=0.3):
    """First κ₀ where R̄ crosses `level`."""
    idx = np.where(R_means >= level)[0]
    return kappas[idx[0]] if len(idx) else None

# ── Shell-count experiment (bonus) ───────────────────────────────────────────

def sweep_shells(dirs, kappa=1.0, shell_range=range(2, 8), xi=2.0, T=30.0):
    """Does R̄ grow with shells? Checks if more φ-scaled layers help sync."""
    results = []
    rng = np.random.default_rng(1)
    for s in shell_range:
        pos = []
        for n in range(s):
            r = R0 * (PHI ** n)
            for d in dirs:
                pos.append(r * d)
        pos = np.array(pos)
        N   = len(pos)
        D   = make_distance_matrix(pos)
        phi_i = rng.uniform(0, 2*np.pi, N)
        K   = coupling_matrix(D, kappa, xi=xi, phi_i=phi_i)
        r   = run_kuramoto(K, T=T, seed=0)
        results.append((s, N, r))
        print(f"    shells={s:2d}  nodes={N:3d}  R̄={r:.3f}")
    return results

# ── Spectral gap vs shells (φ² test) ─────────────────────────────────────────

def spectral_gap_vs_shells(oct_dirs, icos_dirs, shell_range=range(2, 8)):
    """
    Track the spectral gap (λ₀ - λ₁) as shells increase.
    If icosahedral gap / octahedral gap → φ² asymptotically, it's a
    genuine geometric invariant.
    """
    rng = np.random.default_rng(2)
    oct_gaps, icos_gaps, ratios = [], [], []

    for s in shell_range:
        gaps = []
        for dirs in [oct_dirs, icos_dirs]:
            pos = []
            for n in range(s):
                r = R0 * (PHI ** n)
                for d in dirs:
                    pos.append(r * d)
            pos = np.array(pos)
            N   = len(pos)
            D   = make_distance_matrix(pos)
            phi_i = rng.uniform(0, 2*np.pi, N)
            K     = coupling_matrix(D, 1.0, xi=2.0, phi_i=phi_i)
            eigs  = np.linalg.eigvalsh(K)
            gap   = eigs[-1] - eigs[-2]
            gaps.append(gap)

        oct_gaps.append(gaps[0])
        icos_gaps.append(gaps[1])
        ratio = gaps[1] / gaps[0] if gaps[0] != 0 else np.nan
        ratios.append(ratio)
        print(f"    shells={s}  oct_gap={gaps[0]:.4f}  "
              f"icos_gap={gaps[1]:.4f}  ratio={ratio:.4f}  "
              f"(φ²={PHI**2:.4f})")

    return oct_gaps, icos_gaps, ratios

# ── Plotting ──────────────────────────────────────────────────────────────────

def plot_results(kappas, oct_R, oct_std, icos_R, icos_std,
                 oct_thresh, icos_thresh,
                 shell_results_oct, shell_results_icos,
                 shell_range, oct_gaps, icos_gaps, ratios,
                 out_path):

    fig, axes = plt.subplots(2, 2, figsize=(13, 9))
    fig.suptitle("Synchronisation Threshold: Octahedral vs Icosahedral φ-Lattice",
                 fontsize=12, fontweight="bold")

    # ── Panel A: κ₀ sweep ────────────────────────────────────────────────────
    ax = axes[0, 0]
    ax.fill_between(kappas, oct_R - oct_std,  oct_R + oct_std,  alpha=0.2, color="steelblue")
    ax.fill_between(kappas, icos_R - icos_std, icos_R + icos_std, alpha=0.2, color="darkorange")
    ax.plot(kappas, oct_R,  lw=2,   color="steelblue",   label=f"Octahedral (6-dir)")
    ax.plot(kappas, icos_R, lw=2,   color="darkorange",  label=f"Icosahedral (12-dir)")
    ax.axhline(0.3, color="gray", lw=0.8, ls="--", label="threshold level 0.3")
    if oct_thresh:
        ax.axvline(oct_thresh, color="steelblue", lw=1, ls=":")
        ax.text(oct_thresh + 0.02, 0.05, f"κ≈{oct_thresh:.2f}", color="steelblue", fontsize=8)
    if icos_thresh:
        ax.axvline(icos_thresh, color="darkorange", lw=1, ls=":")
        ax.text(icos_thresh + 0.02, 0.12, f"κ≈{icos_thresh:.2f}", color="darkorange", fontsize=8)
    if oct_thresh and icos_thresh:
        ax.set_title(f"Order param R vs coupling strength\n"
                     f"Threshold shift: Δκ = {oct_thresh - icos_thresh:.2f} "
                     f"({'icos lower — geometry wins' if icos_thresh < oct_thresh else 'oct lower'})",
                     fontsize=9)
    else:
        ax.set_title("Order param R vs coupling strength", fontsize=9)
    ax.set_xlabel("Coupling strength κ₀")
    ax.set_ylabel("Order parameter R")
    ax.set_ylim(0, 1)
    ax.legend(fontsize=8)
    ax.text(0.01, 0.97, f"{tag('F01')}  {tag('P09')}",
            transform=ax.transAxes, fontsize=6.5, va="top", color="#555")

    # ── Panel B: R vs shells at κ₀=1 ─────────────────────────────────────────
    ax = axes[0, 1]
    shells_oct  = [r[0] for r in shell_results_oct]
    R_oct_sh    = [r[2] for r in shell_results_oct]
    R_icos_sh   = [r[2] for r in shell_results_icos]
    ax.plot(shells_oct, R_oct_sh,  "o-", color="steelblue",  lw=1.5, label="Octahedral")
    ax.plot(shells_oct, R_icos_sh, "s-", color="darkorange", lw=1.5, label="Icosahedral")
    ax.set_xlabel("Number of shells")
    ax.set_ylabel("Order parameter R (κ₀=1)")
    ax.set_title("Does more φ-depth help synchronisation?", fontsize=9)
    ax.legend(fontsize=8)
    ax.set_ylim(0, 1)
    ax.text(0.01, 0.97, f"{tag('F09')}  {tag('P09')}",
            transform=ax.transAxes, fontsize=6.5, va="top", color="#555")

    # ── Panel C: Spectral gap vs shells ──────────────────────────────────────
    ax = axes[1, 0]
    s_list = list(shell_range)
    ax.plot(s_list, oct_gaps,  "o-", color="steelblue",  lw=1.5, label="Octahedral gap")
    ax.plot(s_list, icos_gaps, "s-", color="darkorange", lw=1.5, label="Icosahedral gap")
    ax.set_xlabel("Number of shells")
    ax.set_ylabel("Spectral gap (λ₀ - λ₁)")
    ax.set_title("Spectral gap growth — does ratio → φ²?", fontsize=9)
    ax.legend(fontsize=8)
    ax.text(0.01, 0.97, f"{tag('F09')}  {tag('P01')}",
            transform=ax.transAxes, fontsize=6.5, va="top", color="#555")

    # ── Panel D: Gap ratio vs shells (the φ² convergence test) ───────────────
    ax = axes[1, 1]
    ax.plot(s_list, ratios, "D-", color="purple", lw=1.8, label="icos/oct gap ratio")
    ax.axhline(PHI**2, color="gold", lw=1.5, ls="--", label=f"φ² = {PHI**2:.4f}")
    ax.axhline(2.0,    color="gray", lw=0.8, ls=":",  label="ratio = 2.0 (node count ratio)")
    ax.set_xlabel("Number of shells")
    ax.set_ylabel("Gap ratio (icosahedral / octahedral)")
    ax.set_title("φ² convergence test\n(gold = φ², gray = naive 2× node count)",
                 fontsize=9)
    ax.legend(fontsize=8)
    ax.text(0.01, 0.97, f"{tag('P09')}  {tag('P01')}",
            transform=ax.transAxes, fontsize=6.5, va="top", color="#555")

    plt.tight_layout()
    fig.savefig(out_path, dpi=130)
    print(f"\n  Plot saved → {out_path}")

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("◉ kappa_sync_threshold.py")
    print(f"  φ = {PHI:.6f} | φ² = {PHI**2:.6f}")
    print(f"  {tag('F01')} — the core question")
    print(f"  {tag('P09')} — the structural hypothesis")

    oct_dirs  = octahedral_dirs()
    icos_dirs = icosahedral_dirs()

    # Build lattices at SHELLS=5 for sweep
    pos_oct  = build_lattice(oct_dirs)
    pos_icos = build_lattice(icos_dirs)

    # ── κ₀ sweep ──────────────────────────────────────────────────────────
    kappas = np.linspace(0.1, 3.0, 25)
    print(f"\n{'═'*60}")
    print(f"Sweeping κ₀ ∈ [0.1, 3.0]  (25 points × 3 trials each)")
    print(f"  Octahedral  ({len(pos_oct)} nodes) ...")
    oct_R, oct_std = sweep_kappa(pos_oct,  kappas, n_trials=3)
    print(f"  Icosahedral ({len(pos_icos)} nodes) ...")
    icos_R, icos_std = sweep_kappa(pos_icos, kappas, n_trials=3)

    oct_thresh  = find_threshold(kappas, oct_R,  level=0.3)
    icos_thresh = find_threshold(kappas, icos_R, level=0.3)

    print(f"\n  Sync threshold (R̄ > 0.3):")
    print(f"    Octahedral:   κ₀ ≈ {oct_thresh}")
    print(f"    Icosahedral:  κ₀ ≈ {icos_thresh}")
    if oct_thresh and icos_thresh:
        delta = oct_thresh - icos_thresh
        if delta > 0:
            print(f"    Geometry wins: icosahedral syncs at Δκ={delta:.2f} lower coupling")
        elif delta < 0:
            print(f"    Surprising: octahedral syncs first (Δκ={abs(delta):.2f})")
        else:
            print(f"    Threshold identical — geometry doesn't shift the sync point")

    # ── R vs shells ───────────────────────────────────────────────────────
    shell_range = range(2, 8)
    print(f"\n{'═'*60}")
    print("R vs shells at κ₀=1.0 — does more φ-depth help?")
    print("  Octahedral:")
    shell_results_oct  = sweep_shells(oct_dirs,  kappa=1.0, shell_range=shell_range)
    print("  Icosahedral:")
    shell_results_icos = sweep_shells(icos_dirs, kappa=1.0, shell_range=shell_range)

    # ── φ² convergence test ───────────────────────────────────────────────
    print(f"\n{'═'*60}")
    print(f"Spectral gap ratio vs shells — converging to φ² = {PHI**2:.4f}?")
    oct_gaps, icos_gaps, ratios = spectral_gap_vs_shells(
        oct_dirs, icos_dirs, shell_range=shell_range
    )

    mean_ratio = np.mean(ratios)
    print(f"\n  Mean ratio across shells: {mean_ratio:.4f}")
    print(f"  φ²:                       {PHI**2:.4f}")
    print(f"  Distance from φ²:         {abs(mean_ratio - PHI**2):.4f}")
    if abs(mean_ratio - PHI**2) < 0.15:
        print(f"  → CONVERGING toward φ² — this looks like a geometric invariant")
    elif abs(mean_ratio - 2.0) < abs(mean_ratio - PHI**2):
        print(f"  → Closer to 2.0 (node count ratio) than φ² — geometry not adding extra")
    else:
        print(f"  → Between 2.0 and φ² — partial geometric advantage")

    # ── Synthesis ─────────────────────────────────────────────────────────
    print(f"\n{'═'*60}")
    print("Synthesis:")
    print(f"  {tag('F01')} — R̄ vs κ₀ is the order-parameter curve; "
          f"the threshold κ* is the Kuramoto critical coupling")
    print(f"  {tag('P09')} — if icos_thresh < oct_thresh, intrinsic φ "
          f"lowers the energy cost of coherence")
    print(f"  {tag('F09')} — the spectral gap ratio tests whether φ enters "
          f"the geometry linearly (×2 nodes) or non-linearly (×φ²)")
    print(f"  {tag('P01')} — gap ratio converging to φ² = structural symmetry "
          f"invariant; staying at 2.0 = pure combinatorial effect")

    # ── Plot ──────────────────────────────────────────────────────────────
    out = REPO_ROOT / "examples" / "kappa_sync_threshold.png"
    try:
        plot_results(
            kappas, oct_R, oct_std, icos_R, icos_std,
            oct_thresh, icos_thresh,
            shell_results_oct, shell_results_icos,
            shell_range, oct_gaps, icos_gaps, ratios,
            out
        )
    except Exception as e:
        print(f"\n  (plot skipped: {e})")

    print(f"\n{'═'*60}")
    print("Done.")

if __name__ == "__main__":
    main()
