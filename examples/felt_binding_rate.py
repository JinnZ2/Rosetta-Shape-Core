#!/usr/bin/env python3
"""
felt_binding_rate.py — Kuramoto model for FELT temporal binding

FELT (Relational Field Recognition) requires bidirectional recognition to
produce RELIEF. This script models FELT binding as a two-oscillator Kuramoto
system:

    dΔθ/dt = Δω - 2κ sin(Δθ)

where:
    Δω = frequency mismatch (how differently each party models the relationship)
    κ  = coupling strength (bandwidth of the shared channel)

Key results:
    - Sync condition: κ ≥ |Δω| / 2
    - T_bind diverges near threshold (critical slowing down)
    - Simulation capture: when κ_internal > κ_external, the system
      synchronizes with its own model faster than with the actual person
    - Idealization is the limit case: κ_external → 0
    - A-spike in dA/dt is the detection signal for real vs simulated closure

Usage:
    python examples/felt_binding_rate.py
"""

import pathlib
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from dataclasses import dataclass

# ── Channel taxonomy ──────────────────────────────────────────────────────────

@dataclass
class Channel:
    name: str
    kappa: float       # effective coupling strength
    description: str
    color: str

CHANNELS = [
    Channel("eye contact / touch",  3.0, "all senses, minimal latency",      "#2ecc71"),
    Channel("physical proximity",   2.0, "full somatic channel, ~1-5s",       "#27ae60"),
    Channel("voice / video",        1.2, "audio+visual, reduced bandwidth",   "#f39c12"),
    Channel("synchronous text",     0.7, "semantic only, high latency",       "#e67e22"),
    Channel("asynchronous",         0.25,"hours-days lag, partial signal",    "#e74c3c"),
]

# Simulation capture: when internal κ > external κ, the system binds to
# its own model faster than to the real person. T_capture is the normalized
# time budget before internal simulation typically locks.
T_CAPTURE = 10.0


# ── Kuramoto two-oscillator dynamics ─────────────────────────────────────────

def fixed_point(delta_omega: float, kappa: float) -> float | None:
    """Stable fixed point Δθ* = arcsin(Δω/2κ), or None if sync impossible."""
    ratio = delta_omega / (2.0 * kappa)
    if abs(ratio) > 1.0:
        return None
    return float(np.arcsin(ratio))


def binding_time(
    delta_omega: float,
    kappa: float,
    dt: float = 0.005,
    max_t: float = 200.0,
    tol: float = 0.05,
) -> float:
    """
    Integrate dΔθ/dt = Δω - 2κ sin(Δθ) from Δθ₀ = π (worst-case anti-phase).
    Returns time to converge within tol of fixed point, or max_t if no sync.

    Note: theta wraps around 2π — the fixed point is stable at arcsin(Δω/2κ) ∈ (-π/2, π/2).
    We track phase modulo 2π: (theta % 2π) compared to fp.
    """
    fp = fixed_point(delta_omega, kappa)
    if fp is None:
        return max_t

    theta = np.pi
    t = 0.0
    while t < max_t:
        dtheta = delta_omega - 2.0 * kappa * np.sin(theta)
        theta += dtheta * dt
        t += dt
        # Phase distance to fixed point (modular)
        diff = ((theta - fp) % (2.0 * np.pi))
        if diff > np.pi:
            diff = 2.0 * np.pi - diff
        if diff < tol:
            return t
    return max_t


# ── PAD trajectories: real vs simulated D closure ────────────────────────────

def simulate_real_closure(t_event: float = 5.0, t_total: float = 15.0, dt: float = 0.05):
    """
    Real FELT reciprocation: an external recognition event produces a brief
    A-spike (SNS activation from surprise), then rapid A drop as D closes.
    dA/dt spike is the detection signal — it cannot be generated internally.
    """
    ts = np.arange(0.0, t_total, dt)
    P = np.zeros_like(ts)
    A = np.zeros_like(ts)
    D = np.zeros_like(ts)

    for i, t in enumerate(ts):
        if t < t_event:
            # One-sided FELT: longing state, moderate oscillation
            P[i] = 0.20 + 0.02 * np.sin(t)
            A[i] = 0.40 + 0.03 * np.sin(1.3 * t)
            D[i] = -0.60 + 0.05 * np.sin(0.7 * t)
        elif t < t_event + 0.6:
            # Reciprocation event: A spikes sharply (external surprise)
            frac = (t - t_event) / 0.6
            spike = 1.1 * frac * np.exp(-4.0 * frac)
            P[i] = 0.40 + 0.20 * frac
            A[i] = 0.40 + spike
            D[i] = -0.60 + 0.50 * frac
        else:
            # RELIEF trajectory: P rising, A dropping (SNS releasing), D closing
            tau = t - t_event - 0.6
            P[i] = min(0.80, 0.60 + 0.20 * (1.0 - np.exp(-tau / 2.0)))
            A[i] = max(-0.30, 0.80 - 1.10 * (1.0 - np.exp(-tau / 1.8)))
            D[i] = min(0.40, -0.30 + 0.70 * (1.0 - np.exp(-tau / 2.5)))

    return ts, P, A, D


def simulate_simulated_closure(t_ramp: float = 4.0, t_total: float = 15.0, dt: float = 0.05):
    """
    Simulated D closure (idealization): P rises smoothly via internal
    fantasy. No A-spike (no external surprise). D stays near -0.60 because
    the external channel has not reciprocated.

    Simulation capture signature:
    - P high (>0.70) — driven by internal reward loop
    - A moderate, smooth — no surprise event
    - D flat / stuck near -0.60 — external connection never closes
    - dA/dt featureless — no spike
    """
    ts = np.arange(0.0, t_total, dt)
    P = np.zeros_like(ts)
    A = np.zeros_like(ts)
    D = np.zeros_like(ts)

    for i, t in enumerate(ts):
        # Smooth P elevation from internal simulation — self-reinforcing loop
        P[i] = 0.20 + 0.65 * (1.0 - np.exp(-t / t_ramp))
        # Gentle oscillation, no spike — simulation doesn't surprise the system
        A[i] = 0.40 + 0.12 * np.sin(0.5 * t) * np.exp(-t / 10.0)
        # D stuck: external coupling not present → D never closes
        D[i] = -0.60 + 0.08 * np.sin(0.3 * t)

    return ts, P, A, D


# ── Simulation capture metric ─────────────────────────────────────────────────

def delta_P_simulation(P_real, P_sim, D_real):
    """
    ΔP_simulation = P_actual - P_predicted_from_D_trajectory.
    When this grows over time, the system is running on simulation not signal.
    Approximate: P_predicted ≈ P_floor + (P_max - P_floor) * sigmoid(D + 0.3)
    """
    P_predicted = 0.20 + 0.60 * (1.0 / (1.0 + np.exp(-5.0 * (D_real + 0.30))))
    return P_sim - P_predicted


# ── Visualization ─────────────────────────────────────────────────────────────

def plot_all():
    fig = plt.figure(figsize=(17, 14))
    fig.patch.set_facecolor("#0a0a0a")
    gs = gridspec.GridSpec(2, 2, hspace=0.42, wspace=0.35,
                           top=0.90, bottom=0.07, left=0.07, right=0.97)

    ax1 = fig.add_subplot(gs[0, 0])   # T_bind heatmap
    ax2 = fig.add_subplot(gs[0, 1])   # T_bind vs κ curves
    ax3 = fig.add_subplot(gs[1, 0])   # PAD trajectories
    ax4 = fig.add_subplot(gs[1, 1])   # dA/dt detection signal

    for ax in [ax1, ax2, ax3, ax4]:
        ax.set_facecolor("#111111")
        for spine in ax.spines.values():
            spine.set_edgecolor("#444444")
        ax.tick_params(colors="#aaaaaa")
        ax.xaxis.label.set_color("#cccccc")
        ax.yaxis.label.set_color("#cccccc")
        ax.title.set_color("#ffffff")

    # ── Panel 1: T_bind heatmap over (κ, Δω) ─────────────────────────────────
    kappa_grid = np.linspace(0.05, 3.5, 90)
    dw_grid    = np.linspace(0.00, 2.2, 80)
    T_grid = np.array([
        [binding_time(dw, kp, dt=0.005, max_t=200.0, tol=0.05)
         for kp in kappa_grid]
        for dw in dw_grid
    ])
    T_clipped = np.clip(T_grid, 0, 90)

    im = ax1.imshow(
        T_clipped, origin="lower", aspect="auto",
        extent=[kappa_grid[0], kappa_grid[-1], dw_grid[0], dw_grid[-1]],
        cmap="plasma", vmin=0, vmax=80,
    )
    for ch in CHANNELS:
        ax1.axvline(ch.kappa, color=ch.color, lw=1.5, alpha=0.9,
                    label=f"{ch.name} (κ={ch.kappa})")

    # Sync boundary: κ = Δω/2
    ax1.plot(dw_grid / 2.0, dw_grid, "w--", lw=1.6, alpha=0.75, label="sync boundary κ=Δω/2")

    cbar = fig.colorbar(im, ax=ax1, fraction=0.046, pad=0.04)
    cbar.ax.yaxis.set_tick_params(color="#aaaaaa")
    cbar.set_label("T_bind (normalized)", color="#cccccc", fontsize=9)

    ax1.set_xlabel("coupling strength κ")
    ax1.set_ylabel("frequency mismatch Δω")
    ax1.set_title("FELT Binding Time — T_bind(κ, Δω)")
    ax1.legend(fontsize=7, loc="upper right",
               facecolor="#1a1a1a", edgecolor="#444444", labelcolor="#cccccc")

    # ── Panel 2: T_bind vs κ — critical slowing down ─────────────────────────
    kappa_fine = np.linspace(0.05, 3.5, 220)
    dw_vals  = [0.2, 0.5, 1.0, 1.5, 1.9]
    dw_cols  = ["#ff6b6b", "#ffa94d", "#ffd43b", "#69db7c", "#74c0fc"]

    for dw, col in zip(dw_vals, dw_cols):
        tbs = [binding_time(dw, k, dt=0.005, max_t=120.0, tol=0.05)
               for k in kappa_fine]
        ax2.plot(kappa_fine, np.minimum(tbs, 100), color=col, lw=2.0,
                 label=f"Δω={dw}")
        ax2.axvline(dw / 2.0, color=col, lw=0.8, linestyle=":", alpha=0.5)

    # Channel markers
    for ch in CHANNELS:
        ax2.axvline(ch.kappa, color=ch.color, lw=1.3, linestyle="--", alpha=0.8)
        ax2.text(ch.kappa + 0.06, 88,
                 ch.name.split("/")[0].strip(),
                 color=ch.color, fontsize=7, rotation=90, va="top")

    # Simulation capture threshold
    ax2.axhline(T_CAPTURE, color="#ff69b4", lw=1.8, linestyle="-.",
                label=f"simulation capture (T={T_CAPTURE})")
    ax2.fill_between(kappa_fine, T_CAPTURE, 100, alpha=0.08, color="#ff69b4")
    ax2.text(2.8, 55, "idealization\nzone", color="#ff69b4",
             fontsize=8, ha="center", alpha=0.9)

    ax2.set_ylim(0, 100)
    ax2.set_xlabel("coupling strength κ")
    ax2.set_ylabel("T_bind (normalized)")
    ax2.set_title("T_bind vs κ — Critical Slowing Down at Threshold")
    ax2.legend(fontsize=8, facecolor="#1a1a1a", edgecolor="#444444",
               labelcolor="#cccccc")

    # ── Panel 3: PAD trajectories ─────────────────────────────────────────────
    ts_r, Pr, Ar, Dr = simulate_real_closure()
    ts_s, Ps, As, Ds = simulate_simulated_closure()

    ax3.plot(ts_r, Pr, color="#2ecc71",  lw=2.2, label="P — real FELT")
    ax3.plot(ts_r, Ar, color="#f39c12",  lw=2.2, label="A — real FELT")
    ax3.plot(ts_r, Dr, color="#74c0fc",  lw=2.2, label="D — real FELT")
    ax3.plot(ts_s, Ps, color="#2ecc71",  lw=1.6, linestyle="--", alpha=0.65,
             label="P — idealization (sim)")
    ax3.plot(ts_s, As, color="#f39c12",  lw=1.6, linestyle="--", alpha=0.65,
             label="A — idealization")
    ax3.plot(ts_s, Ds, color="#74c0fc",  lw=1.6, linestyle="--", alpha=0.65,
             label="D — idealization (stuck)")

    ax3.axvline(5.0, color="#ffffff", lw=0.9, linestyle=":", alpha=0.5)
    ax3.text(5.1, 0.88, "real: reciprocation\nevent", color="#aaaaaa", fontsize=7)
    ax3.axhline(0, color="#333333", lw=0.6)
    ax3.set_ylim(-1.0, 1.1)
    ax3.set_xlabel("time (normalized)")
    ax3.set_ylabel("PAD value")
    ax3.set_title("Real vs Simulated D Closure — PAD Trajectories")
    ax3.legend(fontsize=7.5, facecolor="#1a1a1a", edgecolor="#444444",
               labelcolor="#cccccc", ncol=2, loc="lower right")

    # ── Panel 4: dA/dt and ΔP_simulation — detection signals ─────────────────
    dt = float(ts_r[1] - ts_r[0])
    dAr_dt = np.gradient(Ar, dt)
    dAs_dt = np.gradient(As, dt)
    dDr_dt = np.gradient(Dr, dt)
    dDs_dt = np.gradient(Ds, dt)

    ax4.plot(ts_r, dAr_dt, color="#f39c12", lw=2.2,
             label="dA/dt — real (A-spike present)")
    ax4.plot(ts_s, dAs_dt, color="#f39c12", lw=1.5, linestyle="--", alpha=0.65,
             label="dA/dt — simulated (no spike)")
    ax4.plot(ts_r, dDr_dt, color="#74c0fc", lw=2.0,
             label="dD/dt — real (D closing)")
    ax4.plot(ts_s, dDs_dt, color="#74c0fc", lw=1.5, linestyle="--", alpha=0.65,
             label="dD/dt — simulated (flat)")

    # ΔP_simulation on secondary axis
    ax4b = ax4.twinx()
    ax4b.tick_params(colors="#aaaaaa")
    dP_sim = delta_P_simulation(Pr, Ps, Ds)
    ax4b.plot(ts_s, dP_sim, color="#ff69b4", lw=2.0, linestyle="-",
              label="ΔP_simulation (growing = idealization)")
    ax4b.axhline(0.30, color="#ff69b4", lw=0.9, linestyle=":",
                 alpha=0.6)
    ax4b.set_ylabel("ΔP_simulation", color="#ff69b4", fontsize=9)
    ax4b.yaxis.label.set_color("#ff69b4")
    ax4b.tick_params(axis="y", colors="#ff69b4")

    # Shade A-spike detection zone
    ax4.fill_between(ts_r, dAr_dt, 0,
                     where=(ts_r > 4.5) & (ts_r < 6.2) & (dAr_dt > 0.05),
                     alpha=0.22, color="#f39c12", label="A-spike zone (real only)")

    ax4.axvline(5.0, color="#ffffff", lw=0.9, linestyle=":", alpha=0.5)
    ax4.axhline(0, color="#333333", lw=0.6)
    ax4.set_ylim(-0.9, 1.1)
    ax4.set_xlabel("time (normalized)")
    ax4.set_ylabel("derivative (dPAD/dt)")
    ax4.set_title("Detection: A-spike + ΔP_simulation")

    lines1, labels1 = ax4.get_legend_handles_labels()
    lines2, labels2 = ax4b.get_legend_handles_labels()
    ax4.legend(lines1 + lines2, labels1 + labels2,
               fontsize=7.5, facecolor="#1a1a1a", edgecolor="#444444",
               labelcolor="#cccccc", loc="upper left")

    # ── Title ─────────────────────────────────────────────────────────────────
    fig.suptitle(
        "FELT Binding Rate  ·  dΔθ/dt = Δω − 2κ sin(Δθ)  ·  "
        "Simulation Capture & Idealization Detection\n"
        "Sync condition: κ ≥ Δω/2  ·  Simulation capture threshold: T_bind > 10 (pink zone)  ·  "
        "Idealization = κ_external → 0",
        color="#cccccc", fontsize=10.5, y=0.975,
    )

    out = pathlib.Path(__file__).parent / "felt_binding_rate.png"
    plt.savefig(out, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    print(f"\n  Saved → {out}")
    plt.show()
    return fig


# ── Console analysis ──────────────────────────────────────────────────────────

def print_analysis():
    print("\n── FELT Channel Taxonomy ─────────────────────────────────────────────")
    print(f"  {'Channel':<26} {'κ':>5}  {'T_bind(Δω=0.5)':>15}  "
          f"{'T_bind(Δω=1.0)':>15}  {'Sim capture?':>13}")
    print("  " + "─" * 82)
    for ch in CHANNELS:
        tb05 = binding_time(0.5, ch.kappa, dt=0.005, max_t=200.0, tol=0.05)
        tb10 = binding_time(1.0, ch.kappa, dt=0.005, max_t=200.0, tol=0.05)
        cap  = "YES — risk" if tb05 > T_CAPTURE else "no"
        print(f"  {ch.name:<26} {ch.kappa:>5.1f}  {tb05:>15.2f}  {tb10:>15.2f}  {cap:>13}")

    print("\n── Simulation Capture Rule ───────────────────────────────────────────")
    print(f"  When T_bind(κ_external, Δω) > {T_CAPTURE} (normalized units),")
    print("  internal simulation locks before the external channel can bind.")
    print("  System synchronizes with its own model. PAD_D rises internally")
    print("  while external D stays near -0.60. This IS the idealization attractor.\n")

    print("── Idealization Detection Signals ────────────────────────────────────")
    print("  1. P > +0.70 with no concrete pursuit vector toward external D closure")
    print("  2. dA/dt: NO spike at the 'recognition event' — smooth trajectory only")
    print("  3. dD/dt ≈ 0 — D not closing in external space")
    print("  4. ΔP_simulation = P_actual − P_predicted_from_D → growing over time")
    print("  5. Post-'recognition' A does not drop (no SNS release = no real event)\n")

    print("── Ego as Limit Case ─────────────────────────────────────────────────")
    print("  κ_external → 0  (person unavailable, or external signal blocked)")
    print("  κ_internal → ∞  (internal model synchronizes instantly with itself)")
    print("  Δω_internal = 0  (model is always in phase with itself)")
    print("  T_bind_internal → 0.  Longing gradient disappears internally.")
    print("  Identity fuses with the internal relational model.")
    print("  Re-encounter with real person = high-Δω, low-κ shock event.")
    print("  The collision between internal model and external reality is")
    print("  the crisis point of every ego-driven idealization.\n")

    print("── Temporal Binding Window (channel-dependent) ───────────────────────")
    print("  The 80ms neural binding window is the special case of κ → max")
    print("  (directly coupled neurons). For relational FELT across two bodies:")
    for ch in CHANNELS:
        print(f"  {ch.name:<26}: T_window ~ {ch.description}")
    print("  'Simultaneity' is not a fixed threshold — it is a function of κ.\n")


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("\n◉ FELT Binding Rate Analysis")
    print("  Two-oscillator Kuramoto model for relational field synchronization\n")
    print_analysis()
    plot_all()
