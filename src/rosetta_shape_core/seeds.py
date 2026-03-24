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

    # Essence-driven selection (what the kernel does)
    traits = traits_for_essence("guardian")  # → ["stability", "foundation", ...]
    seed = select_by_traits(traits)[0]       # → tetrahedron

    # Compute trait-based resonance between two seeds (includes topology)
    score = resonance("SHAPE.TETRA", "SHAPE.CUBE")  # → Jaccard + bridge bonus

    # Get all shape IDs (kernel compatibility)
    ids = all_shape_ids()  # → ["SHAPE.CUBE", "SHAPE.DODECA", ...]
"""
from __future__ import annotations
import json, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
CATALOG_PATH = ROOT / "data" / "seed-catalog.json"
ESSENCE_PATH = ROOT / "data" / "essence-traits.json"

_catalog_cache: dict | None = None
_essence_cache: dict | None = None


# ---------------------------------------------------------------------------
# Polyhedral topology (duality and bridge connections)
# ---------------------------------------------------------------------------
# Cube ↔ Octahedron: duals (vertices of one = faces of other)
# Dodecahedron ↔ Icosahedron: duals
# Tetrahedron: self-dual, bridges to Cube (stability) and Dodeca (boundary)

_DUALITY_PAIRS = {
    frozenset({"SHAPE.CUBE", "SHAPE.OCTA"}),
    frozenset({"SHAPE.DODECA", "SHAPE.ICOSA"}),
}

_BRIDGE_CONNECTIONS = {
    frozenset({"SHAPE.TETRA", "SHAPE.CUBE"}),
    frozenset({"SHAPE.TETRA", "SHAPE.DODECA"}),
}

_DUALITY_BONUS = 0.15
_BRIDGE_BONUS = 0.08


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def _load_catalog() -> list[dict]:
    global _catalog_cache
    if _catalog_cache is not None:
        return _catalog_cache["seeds"]
    data = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    _catalog_cache = data
    return data["seeds"]


def _load_essences() -> dict:
    global _essence_cache
    if _essence_cache is not None:
        return _essence_cache
    data = json.loads(ESSENCE_PATH.read_text(encoding="utf-8"))
    _essence_cache = data["essences"]
    return _essence_cache


# ---------------------------------------------------------------------------
# Seed lookup
# ---------------------------------------------------------------------------

def all_seeds() -> list[dict]:
    """Return all seeds in the catalog."""
    return list(_load_catalog())


def all_shape_ids() -> list[str]:
    """Return all known shape ontology IDs.

    Kernel compatibility: rosetta_bridge.py calls this to enumerate shapes.
    """
    return sorted(s["shape_id"] for s in _load_catalog())


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


# ---------------------------------------------------------------------------
# Selection
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Essence mapping
# ---------------------------------------------------------------------------

def traits_for_essence(essence: str) -> list[str]:
    """Map an agent essence (archetype) to trait families.

    The kernel's SeedSelector calls this to translate a role like
    "guardian" into ["stability", "foundation", "boundary", "containment"],
    then passes the result to select_by_traits().

    Returns an empty list if the essence is unknown.
    """
    essences = _load_essences()
    entry = essences.get(essence.lower())
    if entry is None:
        return []
    return list(entry["traits"])


def all_essences() -> dict[str, dict]:
    """Return all known essences with their traits and primary shapes."""
    return dict(_load_essences())


def select_by_essence(essence: str) -> list[dict]:
    """Select seeds for an agent essence — combines traits_for_essence + select_by_traits.

    This is the one-call replacement for random.choice() in the kernel:
        seed = select_by_essence("guardian")[0]
    """
    traits = traits_for_essence(essence)
    if not traits:
        return []
    return select_by_traits(traits)


# ---------------------------------------------------------------------------
# Resonance (Jaccard + polyhedral topology)
# ---------------------------------------------------------------------------

def resonance(shape_a: str, shape_b: str) -> float:
    """Compute resonance between two seeds.

    Score = Jaccard similarity on trait families + topology bonuses:
      - Identical shapes: 1.0
      - Polyhedral duals (cube↔octa, dodeca↔icosa): Jaccard + 0.15
      - Bridge connections (tetra↔cube, tetra↔dodeca): Jaccard + 0.08
      - No trait overlap, no topology: 0.0

    The duality bonus reflects complementary resonance — dual shapes share
    deep structural relationship (vertices↔faces) even when their trait
    families don't fully overlap.

    Returns 0.0 if either seed is not found.
    """
    seed_a = get_seed(shape_a)
    seed_b = get_seed(shape_b)
    if not seed_a or not seed_b:
        return 0.0

    families_a = set(f.lower() for f in seed_a.get("traits", {}).get("families", []))
    families_b = set(f.lower() for f in seed_b.get("traits", {}).get("families", []))

    union = families_a | families_b
    jaccard = len(families_a & families_b) / len(union) if union else 0.0

    # Topology bonuses
    pair = frozenset({shape_a, shape_b})
    bonus = 0.0
    if pair in _DUALITY_PAIRS:
        bonus = _DUALITY_BONUS
    elif pair in _BRIDGE_CONNECTIONS:
        bonus = _BRIDGE_BONUS

    return round(min(jaccard + bonus, 1.0), 4)


# ---------------------------------------------------------------------------
# Trait vectors
# ---------------------------------------------------------------------------

def seed_traits_vector(shape_id: str) -> tuple[list[int], list[str]]:
    """Return a binary trait vector for a seed.

    Returns:
        (vector, labels) where vector[i] = 1 if shape has labels[i], else 0.
        Returns ([], []) if shape is unknown.

    Kernel compatibility: rosetta_bridge.py expects tuple(list, list) format.
    """
    all_families: set[str] = set()
    for seed in _load_catalog():
        for f in seed.get("traits", {}).get("families", []):
            all_families.add(f.lower())

    labels = sorted(all_families)
    target = get_seed(shape_id)
    if not target:
        return ([], [])

    target_families = set(
        f.lower() for f in target.get("traits", {}).get("families", [])
    )
    vector = [1 if f in target_families else 0 for f in labels]
    return (vector, labels)
