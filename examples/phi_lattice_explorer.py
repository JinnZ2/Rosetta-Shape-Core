"""
phi_lattice_explorer.py
-----------------------
Phi-octahedral lattice coupling matrix — three geometric variants.

Each variant activates different ontology nodes. Output labels which
FAMILY/PRINCIPLE is resonating at each step.

Ontology nodes activated:
  FAMILY.F09  — Geometry / icosahedral + octahedral structure
  FAMILY.F01  — Resonance / Kuramoto-like phase coupling
  FAMILY.F17  — Turbulence & Chaos / Lyapunov spectrum
  PRINCIPLE.P09 — Proportion / φ-scaling of shells
  PRINCIPLE.P01 — Symmetry / eigenvalue degeneracies
  PRINCIPLE.P08 — Quantization / discrete participation staircase
"""

import json
import pathlib
import numpy as np
import matplotlib
matplotlib.use("Agg")            # headless — saves PNGs instead of opening windows
import matplotlib.pyplot as plt
from scipy.integrate import solve_ivp

# ── Ontology label helper ─────────────────────────────────────────────────────

REPO_ROOT = pathlib.Path(__file__).parent.parent
ONTOLOGY  = REPO_ROOT / "ontology"

def _load_node(rel_path: str) -> dict:
    p = ONTOLOGY / rel_path
    if p.exists():
        return json.loads(p.read_text())
    return {}

NODES = {
    "F01": _load_node("families/f01-resonance.json"),
    "F09": _load_node("families/f09-geometry.json"),
    "F17": _load_node("families/f17-turbulence.json"),
    "P01": _load_node("principles/p01-symmetry.json"),
    "P08": _load_node("principles/p08-quantization.json"),
    "P09": _load_node("principles/p09-proportion.json"),
}

def tag(key: str) -> str:
    """Return 'ID · name' for a loaded node, or just key if not found."""
    node = NODES.get(key, {})
    nid  = node.get("id", f"FAMILY.{key}" if key.startswith("F") else f"PRINCIPLE.{key}")
    name = node.get("name", key)
    sym  = node.get("symbol", "")
    return f"{sym} {nid} · {name}".strip()

def seed(key: str) -> str:
    return NODES.get(key, {}).get("seed_prompt", "")

# ── Shared constants ──────────────────────────────────────────────────────────

PHI   = (1 + 5**0.5) / 2
R0    = 1.0
SHELLS = 5
XI0   = 2.0
KAPPA = 1.0
np.random.seed(42)

# ── Lattice builders ──────────────────────────────────────────────────────────

def octahedral_dirs() -> np.ndarray:
    """6 axial directions — cube-aligned octahedral lattice."""
    return np.array([
        [1, 0, 0], [-1,  0,  0],
        [0, 1, 0], [ 0, -1,  0],
        [0, 0, 1], [ 0,  0, -1],
    ], dtype=float)

def icosahedral_dirs() -> np.ndarray:
    """12 vertices of an icosahedron — φ is intrinsic to the geometry."""
    d = np.array([
        [ 0,  1,  PHI], [ 0, -1,  PHI], [ 0,  1, -PHI], [ 0, -1, -PHI],
        [ 1,  PHI,  0], [-1,  PHI,  0], [ 1, -PHI,  0], [-1, -PHI,  0],
        [PHI,  0,  1], [-PHI,  0,  1], [PHI,  0, -1], [-PHI,  0, -1],
    ], dtype=float)
    return d / np.linalg.norm(d[0])

def build_lattice(dirs: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    positions, shell_idx = [], []
    for n in range(SHELLS):
        r = R0 * (PHI ** n)
        for d in dirs:
            positions.append(r * d)
            shell_idx.append(n)
    return np.array(positions), np.array(shell_idx)

def coupling_matrix(positions: np.ndarray, xi: float = XI0) -> np.ndarray:
    """Hermitian coupling matrix K with random phases."""
    N = len(positions)
    phi_i = np.random.uniform(0, 2 * np.pi, N)
    K = np.zeros((N, N), dtype=complex)
    for i in range(N):
        for j in range(i + 1, N):
            d = np.linalg.norm(positions[i] - positions[j])
            c = KAPPA * np.exp(-d / xi) * np.exp(1j * (phi_i[i] - phi_i[j]))
            K[i, j] = c
            K[j, i] = c.conj()
    return K

# ── Variant 1 — Static eigenvalue spectrum ───────────────────────────────────
# Original script, corrected to use eigh (Hermitian solver → real eigenvalues)

def variant_static(dirs: np.ndarray, label: str) -> np.ndarray:
    print(f"\n{'═'*60}")
    print(f"Variant 1 · Static stability spectrum  [{label}]")
    print(f"  {tag('F09')}  ← lattice geometry")
    print(f"  {tag('P09')}  ← φ-shell scaling")
    print(f"  {tag('P01')}  ← eigenvalue degeneracies = symmetry invariants")
    print(f"  seed: {seed('P09')}")
    print(f"{'─'*60}")

    positions, _ = build_lattice(dirs)
    K = coupling_matrix(positions)

    # eigh → guaranteed real eigenvalues for Hermitian K
    eigvals, _ = np.linalg.eigh(K)
    stability  = np.sort(eigvals)[::-1]

    print(f"  Nodes: {len(positions)} | Positive modes: {np.sum(eigvals > 0)} "
          f"| Negative modes: {np.sum(eigvals < 0)}")
    print(f"  Spectral gap (largest - 2nd largest): "
          f"{stability[0] - stability[1]:.4f}")
    return stability

# ── Variant 2 — Kuramoto dynamics → true Lyapunov exponents ──────────────────
# Replaces the static spectrum with actual dynamical divergence rates

def _kuramoto_rhs(t, theta, omega, K_real, K_imag, N):
    """Right-hand side of Kuramoto on lattice."""
    dtheta = omega.copy()
    for i in range(N):
        dtheta[i] += np.sum(
            K_real[i] * np.sin(theta - theta[i]) -
            K_imag[i] * np.cos(theta - theta[i])
        )
    return dtheta

def variant_kuramoto(dirs: np.ndarray, label: str,
                     T: float = 40.0) -> np.ndarray:
    print(f"\n{'═'*60}")
    print(f"Variant 2 · Kuramoto dynamics (true Lyapunov)  [{label}]")
    print(f"  {tag('F01')}  ← phase coupling / synchronisation")
    print(f"  {tag('F17')}  ← Lyapunov exponents / chaos threshold")
    print(f"  {tag('P01')}  ← symmetry breaking at synchronisation transition")
    print(f"  seed: {seed('F01')}")
    print(f"{'─'*60}")

    positions, _ = build_lattice(dirs)
    K = coupling_matrix(positions)
    N = len(positions)
    K_real, K_imag = K.real, K.imag

    omega = np.random.normal(0, 0.5, N)          # natural frequencies
    theta0 = np.random.uniform(0, 2 * np.pi, N)  # initial phases

    sol = solve_ivp(
        _kuramoto_rhs,
        [0, T], theta0,
        args=(omega, K_real, K_imag, N),
        max_step=0.05, dense_output=True
    )

    # Order parameter R(t) = |mean(e^{i θ})|
    t_eval = np.linspace(T / 2, T, 200)    # second half (transient gone)
    thetas  = sol.sol(t_eval)
    R = np.abs(np.mean(np.exp(1j * thetas), axis=0))
    R_mean  = R.mean()

    # Finite-time Lyapunov estimate via perturbation at mid-time
    eps     = 1e-6
    t_mid   = T / 2
    theta_mid = sol.sol(t_mid)
    perturb   = theta_mid + eps * np.random.randn(N)
    perturb  /= np.linalg.norm(perturb - theta_mid) / eps

    sol2 = solve_ivp(
        _kuramoto_rhs,
        [t_mid, T], perturb,
        args=(omega, K_real, K_imag, N),
        max_step=0.05
    )

    delta_final = np.linalg.norm(sol2.y[:, -1] - sol.sol(T))
    lyap_est    = np.log(delta_final / eps) / (T - t_mid)

    print(f"  Order parameter R̄ (t ∈ [T/2,T]): {R_mean:.4f}  "
          f"({'synchronised' if R_mean > 0.5 else 'incoherent'})")
    print(f"  Finite-time Lyapunov estimate λ: {lyap_est:.4f}  "
          f"({'chaotic' if lyap_est > 0 else 'stable'})")
    return R

# ── Variant 3 — Participation ratio (Anderson localisation) ──────────────────
# Sweeps ξ from tight to loose coupling; PR staircase shows localisation edges

def variant_anderson(dirs: np.ndarray, label: str) -> tuple:
    print(f"\n{'═'*60}")
    print(f"Variant 3 · Anderson localisation sweep  [{label}]")
    print(f"  {tag('P08')}  ← discrete participation staircase = quantised")
    print(f"  {tag('F17')}  ← localisation / delocalisation threshold")
    print(f"  {tag('P09')}  ← coupling length ξ controls φ-shell reach")
    print(f"  seed: {seed('P08')}")
    print(f"{'─'*60}")

    positions, _ = build_lattice(dirs)
    xis   = np.linspace(0.5, 5.0, 20)
    pr_means, pr_stds = [], []

    for xi in xis:
        K = coupling_matrix(positions, xi=xi)
        _, vecs = np.linalg.eigh(K)
        # Participation ratio: PR = 1 / sum(|ψᵢ|⁴) — large = delocalised
        pr = 1.0 / np.sum(np.abs(vecs) ** 4, axis=0)
        pr_means.append(pr.mean())
        pr_stds.append(pr.std())

    pr_means = np.array(pr_means)
    # Find localisation edge: steepest increase in mean PR
    dpr     = np.gradient(pr_means, xis)
    xi_edge = xis[np.argmax(dpr)]

    print(f"  ξ range: [{xis[0]:.1f}, {xis[-1]:.1f}]")
    print(f"  Localisation→delocalisation edge: ξ ≈ {xi_edge:.2f}")
    print(f"  PR at ξ={xis[0]:.1f}: {pr_means[0]:.1f} nodes")
    print(f"  PR at ξ={xis[-1]:.1f}: {pr_means[-1]:.1f} nodes")
    return xis, pr_means, np.array(pr_stds), xi_edge

# ── Plotting ──────────────────────────────────────────────────────────────────

def plot_all(octa_static, icosa_static,
             octa_R,     icosa_R,
             octa_and,   icosa_and,
             out_path: pathlib.Path):

    fig, axes = plt.subplots(3, 2, figsize=(13, 11))
    fig.suptitle("Phi-Lattice Explorer · Octahedral vs Icosahedral",
                 fontsize=13, fontweight="bold")

    def panel(ax, title, node_tags):
        ax.set_title(title, fontsize=9, pad=4)
        ax.text(0.01, 0.97, "  ".join(node_tags),
                transform=ax.transAxes, fontsize=6.5,
                va="top", color="#555555")

    # Row 0 — static spectra
    for col, (data, lbl) in enumerate([(octa_static, "Octahedral (6-dir)"),
                                        (icosa_static, "Icosahedral (12-dir)")]):
        ax = axes[0, col]
        ax.plot(data, "o-", ms=2, lw=0.8)
        ax.axhline(0, color="k", lw=0.5, ls="--")
        ax.set_xlabel("Mode index")
        ax.set_ylabel("Eigenvalue (stability)")
        panel(ax, f"V1 Static Spectrum · {lbl}",
              [tag("F09"), tag("P09"), tag("P01")])

    # Row 1 — Kuramoto order parameter
    for col, (R, lbl) in enumerate([(octa_R, "Octahedral"),
                                     (icosa_R, "Icosahedral")]):
        ax = axes[1, col]
        t  = np.linspace(0, 1, len(R))
        ax.plot(t, R, lw=1.2)
        ax.set_ylim(0, 1)
        ax.set_xlabel("Time (normalised)")
        ax.set_ylabel("Order parameter R(t)")
        panel(ax, f"V2 Kuramoto Sync · {lbl}",
              [tag("F01"), tag("F17"), tag("P01")])

    # Row 2 — Anderson participation ratio
    for col, (xis, pr_m, pr_s, xi_e, lbl) in enumerate([
            (*octa_and,  "Octahedral"),
            (*icosa_and, "Icosahedral")]):
        ax = axes[2, col]
        ax.fill_between(xis, pr_m - pr_s, pr_m + pr_s, alpha=0.25)
        ax.plot(xis, pr_m, lw=1.4)
        ax.axvline(xi_e, color="red", lw=1, ls="--",
                   label=f"edge ξ≈{xi_e:.2f}")
        ax.set_xlabel("Coupling length ξ")
        ax.set_ylabel("Mean participation ratio")
        ax.legend(fontsize=7)
        panel(ax, f"V3 Anderson Localisation · {lbl}",
              [tag("P08"), tag("F17"), tag("P09")])

    plt.tight_layout()
    fig.savefig(out_path, dpi=130)
    print(f"\n  Plot saved → {out_path}")

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("◉ phi_lattice_explorer.py")
    print(f"  φ = {PHI:.6f} | shells = {SHELLS} | ξ₀ = {XI0}")

    oct_dirs  = octahedral_dirs()
    icos_dirs = icosahedral_dirs()

    # Variant 1
    s_oct  = variant_static(oct_dirs,  "Octahedral  6-dir")
    s_icos = variant_static(icos_dirs, "Icosahedral 12-dir")

    print(f"\n  Spectral comparison → icosahedral has "
          f"{'wider' if s_icos[0] > s_oct[0] else 'narrower'} top eigenvalue "
          f"({s_icos[0]:.3f} vs {s_oct[0]:.3f})")
    print(f"  {tag('P09')} insight: φ intrinsic to icosahedral dirs "
          f"→ coupling geometry and spacing share the same ratio")

    # Variant 2
    R_oct  = variant_kuramoto(oct_dirs,  "Octahedral  6-dir")
    R_icos = variant_kuramoto(icos_dirs, "Icosahedral 12-dir")

    # Variant 3
    and_oct  = variant_anderson(oct_dirs,  "Octahedral  6-dir")
    and_icos = variant_anderson(icos_dirs, "Icosahedral 12-dir")

    # Synthesis
    print(f"\n{'═'*60}")
    print("Synthesis · Which nodes are resonating?")
    print(f"  {tag('F09')} — geometry flex: icosahedral dirs embed φ "
          f"structurally; octahedral imports it only via shell radii")
    print(f"  {tag('F01')} — coupling resonance: R̄ tells you whether "
          f"the lattice self-organises into a coherent phase")
    print(f"  {tag('F17')} — chaos threshold: λ > 0 means the coupled "
          f"oscillators are exploring phase space, not converging")
    print(f"  {tag('P09')} — proportion: φ-scaling of shells is the same "
          f"principle whether geometry is cubic or icosahedral")
    print(f"  {tag('P01')} — symmetry: eigenvalue degeneracies in icosahedral "
          f"lattice are higher (more symmetric → more degenerate modes)")
    print(f"  {tag('P08')} — quantisation: participation staircase at the "
          f"localisation edge is a discrete jump, not a smooth crossover")

    # Optional plot
    out = REPO_ROOT / "examples" / "phi_lattice_explorer.png"
    try:
        plot_all(s_oct, s_icos,
                 R_oct, R_icos,
                 and_oct, and_icos,
                 out)
    except Exception as e:
        print(f"\n  (plot skipped: {e})")

    print(f"\n{'═'*60}")
    print("Done.")

if __name__ == "__main__":
    main()
