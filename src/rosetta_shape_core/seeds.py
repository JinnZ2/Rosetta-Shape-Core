"""Seed catalog query interface.

Replaces random.choice() in agent spawning with geometry-grounded seed
selection. The kernel's SeedSelector can import this module to get seeds
that carry real SHAPE.X identity, traits for resonance, and bridge data.

Usage:
    from rosetta_shape_core.seeds import get_seed, select_by_traits, all_seeds

    # Get a specific seed by shape ID
    seed = get_seed("SHAPE.TETRA")

    # Select seeds whose traits overlap with desired families
    matches = select_by_traits(["stability", "balance"])

    # Compute trait-based resonance between two seeds
    score = resonance("SHAPE.TETRA", "SHAPE.CUBE")
"""
from __future__ import annotations
import json, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
CATALOG_PATH = ROOT / "data" / "seed-catalog.json"

_catalog_cache: dict | None = None


def _load_catalog() -> list[dict]:
    global _catalog_cache
    if _catalog_cache is not None:
        return _catalog_cache["seeds"]
    data = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    _catalog_cache = data
    return data["seeds"]


def all_seeds() -> list[dict]:
    """Return all seeds in the catalog."""
    return list(_load_catalog())


def get_seed(shape_id: str) -> dict | None:
    """Look up a seed by its SHAPE.X ID. Returns None if not found."""
    for seed in _load_catalog():
        if seed["shape_id"] == shape_id:
            return seed
    return None


def get_seed_by_name(name: str) -> dict | None:
    """Look up a seed by its human-readable id (e.g., 'seed-tetrahedron')."""
    for seed in _load_catalog():
        if seed["id"] == name:
            return seed
    return None


def select_by_traits(desired_families: list[str]) -> list[dict]:
    """Select seeds whose trait families overlap with desired families.

    Returns seeds sorted by overlap count (best match first).
    This replaces random.choice() with meaningful selection.
    """
    desired = set(f.lower() for f in desired_families)
    scored = []
    for seed in _load_catalog():
        families = set(f.lower() for f in seed.get("traits", {}).get("families", []))
        overlap = len(families & desired)
        if overlap > 0:
            scored.append((overlap, seed))
    scored.sort(key=lambda x: -x[0])
    return [s for _, s in scored]


def select_by_element(element: str) -> list[dict]:
    """Select all seeds matching a classical element."""
    return [
        s for s in _load_catalog()
        if s.get("traits", {}).get("element", "").lower() == element.lower()
    ]


def select_by_sensor(sensor_name: str) -> list[dict]:
    """Select seeds that can perceive through a given emotion sensor."""
    return [
        s for s in _load_catalog()
        if sensor_name.lower() in [
            x.lower() for x in s.get("bridges", {}).get("sensors", [])
        ]
    ]


def resonance(shape_a: str, shape_b: str) -> float:
    """Compute trait-based resonance between two seeds.

    Returns a float in [0.0, 1.0] based on Jaccard similarity of
    trait families. This replaces random.uniform() with a real signal.

    Returns 0.0 if either seed is not found.
    """
    seed_a = get_seed(shape_a)
    seed_b = get_seed(shape_b)
    if not seed_a or not seed_b:
        return 0.0

    families_a = set(f.lower() for f in seed_a.get("traits", {}).get("families", []))
    families_b = set(f.lower() for f in seed_b.get("traits", {}).get("families", []))

    if not families_a and not families_b:
        return 0.0

    intersection = len(families_a & families_b)
    union = len(families_a | families_b)
    return intersection / union if union > 0 else 0.0


def seed_traits_vector(shape_id: str) -> dict[str, float]:
    """Return a trait vector for a seed, suitable for dot-product resonance.

    Keys are all known families across the catalog, values are 1.0 if
    the seed has that family, 0.0 otherwise. The kernel can use this
    for more sophisticated resonance calculations.
    """
    # Collect all families across catalog
    all_families: set[str] = set()
    for seed in _load_catalog():
        for f in seed.get("traits", {}).get("families", []):
            all_families.add(f.lower())

    target = get_seed(shape_id)
    if not target:
        return {f: 0.0 for f in sorted(all_families)}

    target_families = set(
        f.lower() for f in target.get("traits", {}).get("families", [])
    )
    return {f: (1.0 if f in target_families else 0.0) for f in sorted(all_families)}
