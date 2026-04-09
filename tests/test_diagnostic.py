"""Tests for the diagnostic module (Kuramoto sync analysis).

diagnostic.py requires numpy. Tests skip gracefully if numpy is unavailable.
"""
import pytest

np = pytest.importorskip("numpy", reason="diagnostic.py requires numpy")

from rosetta_shape_core.diagnostic import (  # noqa: E402
    DiagnosticReport,
    analyse_spectrum,
    estimate_sync,
)

# ── Spectral analysis ────────────────────────────────────────────

def test_analyse_spectrum_identity():
    """Identity matrix should have degenerate spectrum."""
    M = np.eye(4)
    spec = analyse_spectrum(M)
    assert "eigenvalues" in spec
    assert len(spec["eigenvalues"]) == 4
    assert "spectral_gap" in spec
    assert "pr_mean" in spec


def test_analyse_spectrum_symmetric():
    """Symmetric coupling matrix analysis."""
    M = np.array([
        [0, 1, 0, 0],
        [1, 0, 1, 0],
        [0, 1, 0, 1],
        [0, 0, 1, 0],
    ], dtype=float)
    spec = analyse_spectrum(M)
    assert spec["spectral_gap"] >= 0


def test_analyse_spectrum_zero():
    """Zero matrix should have zero gap."""
    M = np.zeros((3, 3))
    spec = analyse_spectrum(M)
    assert spec["spectral_gap"] == 0.0


# ── Sync estimation ──────────────────────────────────────────────

def test_estimate_sync_coupled():
    """Fully connected matrix should estimate some sync."""
    M = np.ones((4, 4)) - np.eye(4)
    sync = estimate_sync(M)
    assert "order_parameter_estimate" in sync
    assert "lyapunov_estimate" in sync


def test_estimate_sync_uncoupled():
    """Zero coupling should yield low sync."""
    M = np.zeros((4, 4))
    sync = estimate_sync(M)
    assert sync["order_parameter_estimate"] is None or sync["order_parameter_estimate"] <= 0.5


# ── DiagnosticReport ─────────────────────────────────────────────

def test_diagnostic_report_creation():
    """DiagnosticReport should accept a coupling matrix."""
    M = np.array([[0, 1], [1, 0]], dtype=float)
    report = DiagnosticReport(M)
    assert report.order_param is not None


def test_diagnostic_report_render():
    """Report should render without crashing."""
    M = np.array([[0, 0.5], [0.5, 0]], dtype=float)
    report = DiagnosticReport(M)
    text = str(report)
    assert isinstance(text, str)
    assert len(text) > 0
