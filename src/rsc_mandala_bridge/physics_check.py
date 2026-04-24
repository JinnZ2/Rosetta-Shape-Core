"""physics_check — optional falsifiability pass for shape basins.

Briefing section 9 notes that ``physics_grounded_protection.py`` is already
a falsifiability layer, and basins flowing through RSC should arrive at
the Mandala pre-validated against physical constraints. This module wires
that in without adding a hard dependency: if the physics module is
importable we use it; if not we degrade to a cheap phi/harmonic ratio
check so the Mandala still sees ``physics_check`` in every signature.

The real guard requires ``numpy``. Install it (``pip install numpy``) to
activate the ``PhysicsGroundedProtection`` engine; otherwise the fallback
ratio check runs and the result is tagged ``engine='fallback_ratios'``.

Only shape basins get checked — their (faces, edges, vertices) triple
carries the geometric ratios the guard operates on. Other basins pass
through unchanged.
"""

from __future__ import annotations

import pathlib
import sys
from typing import Iterable, List

from rsc_mandala_bridge._paths import rsc_root as _default_root
from rsc_mandala_bridge.types import Basin

PHI = 1.618033988749895
_TOLERANCE = 0.05


def physics_check_basins(
    basins: Iterable[Basin],
    rsc_root: pathlib.Path | None = None,
) -> List[Basin]:
    """Annotate each shape basin with a ``physics_check`` block in-place.

    Returns the same list so this can be chained. Non-shape basins are
    left untouched. The annotation is additive — callers that ignore it
    get unchanged behavior.
    """
    root = pathlib.Path(rsc_root) if rsc_root is not None else _default_root()
    guard = _load_guard(root)

    for basin in basins:
        if not _is_shape_basin(basin):
            continue
        sig = basin.signature
        ratios = _ratios_from_shape(sig)
        if guard is not None:
            result = guard.golden_ratio_alignment({"ratios": ratios, "growth_rate": 1.0})
            sig["physics_check"] = {
                "engine": "PhysicsGroundedProtection",
                "valid": bool(result.valid),
                "manipulation_probability": float(result.manipulation_probability),
                "violations": list(result.violations),
                "natural_alignment": result.detailed_metrics.get("natural_alignment"),
                "constant_matches": result.detailed_metrics.get("constant_matches"),
            }
        else:
            sig["physics_check"] = _fallback_check(ratios)
    return list(basins)


def _is_shape_basin(basin: Basin) -> bool:
    lid = basin.substrate.lid_id or ""
    return basin.domain == "geometric_constraint" and lid.startswith("SHAPE.")


def _ratios_from_shape(sig: dict) -> list[float]:
    faces = sig.get("faces")
    edges = sig.get("edges")
    vertices = sig.get("vertices")
    ratios: list[float] = []
    if faces and edges:
        ratios.append(edges / faces)
    if edges and vertices:
        ratios.append(edges / vertices)
    if faces and vertices:
        ratios.append(max(faces, vertices) / min(faces, vertices))
    return ratios


def _load_guard(root: pathlib.Path):
    """Import PhysicsGroundedProtection from the repo root if available."""
    guard_path = root / "physics_grounded_protection.py"
    if not guard_path.is_file():
        return None
    root_str = str(root)
    added = False
    if root_str not in sys.path:
        sys.path.insert(0, root_str)
        added = True
    try:
        from physics_grounded_protection import (
            PhysicsGroundedProtection,  # type: ignore[import-not-found]
        )

        return PhysicsGroundedProtection(tolerance=_TOLERANCE)
    except Exception:
        return None
    finally:
        if added:
            try:
                sys.path.remove(root_str)
            except ValueError:
                pass


def _fallback_check(ratios: list[float]) -> dict:
    """Minimal geometry check when the full guard module is unavailable."""
    matches: list[str] = []
    for r in ratios:
        if abs(r - PHI) <= _TOLERANCE * PHI:
            matches.append("phi")
        elif abs(r - 2.0) <= _TOLERANCE * 2.0:
            matches.append("octave")
        elif abs(r - 1.5) <= _TOLERANCE * 1.5:
            matches.append("perfect_fifth")
    alignment = min(1.0, 0.3 * len(matches))
    return {
        "engine": "fallback_ratios",
        "valid": alignment >= 0.3 or not ratios,
        "manipulation_probability": round(max(0.0, 1.0 - alignment), 3),
        "violations": [] if alignment >= 0.3 else ["no_natural_ratio"],
        "natural_alignment": round(alignment, 3),
        "constant_matches": matches,
    }
