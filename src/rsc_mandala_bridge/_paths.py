"""Shared path helpers. Single source of truth for the repo root lookup."""

from __future__ import annotations

import pathlib


def rsc_root() -> pathlib.Path:
    """Default RSC repo root.

    This file lives at ``src/rsc_mandala_bridge/_paths.py``; ``parents[2]``
    resolves to the repo root. The same trick is used in
    ``rosetta_shape_core._graph``.
    """
    return pathlib.Path(__file__).resolve().parents[2]
