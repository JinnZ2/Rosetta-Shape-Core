"""
Constraint-Geometry Agent Framework

An agent has a seed geometry, explores outward within resource constraints,
and compresses back to its seed without losing the map. All relationships
stored as exact fractions (no decimal drift).

Portable across: Rosetta-Shape-Core, Mandala-Computing, Emotions-as-Sensors,
Living-Intelligence, and any other substrate that needs aware agents.

Usage:
    agent = ConstraintAgent(seed_id="SHAPE.TETRA", home_families=["stability"])
    agent.set_resource_budget(compute=1000, bandwidth=50)

    # Expand if resources allow
    if agent.should_expand():
        agent.bloom(depth=2)

    # Explore constraint space
    discoveries = agent.explore()

    # Contract back to seed
    agent.compress()

    # Re-expand deterministically (or differently if resources changed)
    agent.bloom(depth=2)

CLI:
    python -m rosetta_shape_core.constraint_agent --seed bee
    python -m rosetta_shape_core.constraint_agent --seed bee --budget compute=500,bandwidth=20
    python -m rosetta_shape_core.constraint_agent --seed bee --cycle 3
"""
from __future__ import annotations

import argparse
import json
import math
from fractions import Fraction

from rosetta_shape_core.explore import (
    BRANCHING_K,
    FAMILY_VERTEX_LOADING,
    SEED_VERTICES,
    RosettaGraph,
    discover,
    home_base,
    hunt_shadows,
)

# ── Exact fraction arithmetic ──────────────────────────────────────

def _to_fraction(value: float | int | str | Fraction) -> Fraction:
    """Convert any numeric value to an exact Fraction."""
    if isinstance(value, Fraction):
        return value
    if isinstance(value, float):
        return Fraction(value).limit_denominator(10_000)
    return Fraction(value)


def _fraction_amplitudes(families: list[str]) -> list[Fraction]:
    """Compute seed amplitudes as exact fractions — no decimal drift."""
    amps = [Fraction(0)] * 6
    for fid in families:
        loadings = FAMILY_VERTEX_LOADING.get(fid, [])
        for i, v in enumerate(loadings):
            amps[v] += Fraction(1, i + 1)

    total = sum(amps) or Fraction(1)
    return [a / total for a in amps]


def _shannon_entropy_fraction(amplitudes: list[Fraction]) -> Fraction:
    """Shannon entropy from exact fractions, result as fraction approximation."""
    h = Fraction(0)
    for a in amplitudes:
        if a > 0:
            # log2 unavoidable as float, but we capture it back as fraction
            log_val = Fraction(math.log2(float(a))).limit_denominator(10_000)
            h -= a * log_val
    return h


_SATURATION = Fraction(45, 100)  # 0.45


def _apply_saturation(amplitudes: list[Fraction]) -> list[Fraction]:
    """Cap any vertex exceeding saturation fraction, redistribute excess."""
    amps = list(amplitudes)
    redistributed = True
    while redistributed:
        redistributed = False
        excess = Fraction(0)
        below_count = 0
        for i, a in enumerate(amps):
            if a > _SATURATION:
                excess += a - _SATURATION
                amps[i] = _SATURATION
                redistributed = True
            else:
                below_count += 1
        if redistributed and below_count > 0:
            share = excess / below_count
            for i in range(6):
                if amps[i] < _SATURATION:
                    amps[i] += share
    return amps


# ── Discovery map ──────────────────────────────────────────────────

class DiscoveryMap:
    """Immutable record of everything found during a bloom cycle.

    Stored as exact fractions so compress → re-bloom is lossless.
    """

    def __init__(self):
        self.paths: list[dict] = []
        self.visited_shapes: set[str] = set()
        self.shadow_report: dict = {}
        self.amplitudes: list[Fraction] = []
        self.entropy: Fraction = Fraction(0)
        self.depth: int = 0
        self.budget_snapshot: dict[str, Fraction] = {}

    def summary(self) -> dict:
        return {
            "paths_found": len(self.paths),
            "shapes_reached": sorted(self.visited_shapes),
            "shadows": len(self.shadow_report.get("shadows", [])),
            "depth": self.depth,
            "entropy": str(self.entropy),
            "amplitudes": {
                SEED_VERTICES[i]: str(a) for i, a in enumerate(self.amplitudes)
            },
        }


# ── Resource budget ────────────────────────────────────────────────

class ResourceBudget:
    """Tracks resource constraints as exact fractions.

    Resources are named — compute, bandwidth, memory, or anything the
    substrate defines. Each has a capacity and current usage.
    """

    def __init__(self):
        self._capacity: dict[str, Fraction] = {}
        self._used: dict[str, Fraction] = {}

    def set(self, name: str, capacity: float | int | Fraction) -> None:
        self._capacity[name] = _to_fraction(capacity)
        if name not in self._used:
            self._used[name] = Fraction(0)

    def spend(self, name: str, amount: float | int | Fraction) -> bool:
        """Spend resource. Returns False if insufficient."""
        amt = _to_fraction(amount)
        if name not in self._capacity:
            return True  # unconstrained resource
        if self._used[name] + amt > self._capacity[name]:
            return False
        self._used[name] += amt
        return True

    def remaining(self, name: str) -> Fraction:
        if name not in self._capacity:
            return Fraction(1, 0)  # infinity placeholder — will raise on comparison
        return self._capacity[name] - self._used.get(name, Fraction(0))

    def remaining_safe(self, name: str) -> Fraction | None:
        """Remaining budget, or None if resource is unconstrained."""
        if name not in self._capacity:
            return None
        return self._capacity[name] - self._used.get(name, Fraction(0))

    def utilization(self, name: str) -> Fraction:
        cap = self._capacity.get(name)
        if not cap:
            return Fraction(0)
        return self._used.get(name, Fraction(0)) / cap

    def reset(self) -> None:
        for k in self._used:
            self._used[k] = Fraction(0)

    def snapshot(self) -> dict[str, Fraction]:
        return {
            name: self._capacity[name] - self._used.get(name, Fraction(0))
            for name in self._capacity
        }

    def is_exhausted(self) -> bool:
        """True if ANY resource is fully spent."""
        for name in self._capacity:
            if self._used.get(name, Fraction(0)) >= self._capacity[name]:
                return True
        return False

    def names(self) -> list[str]:
        return list(self._capacity.keys())

    def __repr__(self) -> str:
        parts = []
        for name in sorted(self._capacity):
            used = self._used.get(name, Fraction(0))
            cap = self._capacity[name]
            parts.append(f"{name}: {used}/{cap}")
        return f"Budget({', '.join(parts)})"


# ── Constraint Agent ───────────────────────────────────────────────

# Cost per operation (in compute units)
_COST_BLOOM_BASE = Fraction(10)
_COST_BLOOM_PER_DEPTH = Fraction(15)
_COST_EXPLORE_PER_PATH = Fraction(1)
_COST_SHADOW_HUNT = Fraction(5)
_COST_COMPRESS = Fraction(2)

# Bandwidth cost per discovered path
_BW_PER_PATH = Fraction(1)


class ConstraintAgent:
    """An agent with seed geometry that explores within resource constraints.

    The agent's lifecycle:
      1. Seed — initial geometry from home shape + families
      2. Bloom — expand outward (costs resources, produces DiscoveryMap)
      3. Explore — search within current bloom for shadows and patterns
      4. Compress — contract back to seed, preserving the map
      5. Re-bloom — expand again (deterministic if resources unchanged)

    All internal arithmetic uses exact fractions.
    """

    def __init__(
        self,
        seed_id: str,
        home_families: list[str] | None = None,
        graph: RosettaGraph | None = None,
    ):
        self._graph = graph or RosettaGraph()
        self._resolved_id = self._graph.resolve_id(seed_id) or seed_id

        # Home base from the graph
        self._home = home_base(self._graph, self._resolved_id)
        self._home_shape = self._home.get("home_shape")
        self._label = self._home.get("label", self._resolved_id)

        # Families — from argument or graph
        if home_families:
            self._families = list(home_families)
        else:
            self._families = list(self._home.get("entity_families", []))

        # Seed amplitudes as exact fractions
        self._seed_amplitudes = _apply_saturation(_fraction_amplitudes(self._families))
        self._entropy = _shannon_entropy_fraction(self._seed_amplitudes)

        # Resource budget
        self.budget = ResourceBudget()

        # State
        self._state: str = "seed"       # seed | bloomed | exploring | compressed
        self._maps: list[DiscoveryMap] = []  # history of all discovery maps
        self._current_map: DiscoveryMap | None = None
        self._cycle: int = 0

        # Compression log — what the agent remembers across compress/bloom
        self._memory: list[dict] = []

    # ── Properties ─────────────────────────────────────────────────

    @property
    def state(self) -> str:
        return self._state

    @property
    def seed_id(self) -> str:
        return self._resolved_id

    @property
    def label(self) -> str:
        return self._label

    @property
    def home_shape(self) -> str | None:
        return self._home_shape

    @property
    def families(self) -> list[str]:
        return list(self._families)

    @property
    def amplitudes(self) -> dict[str, Fraction]:
        return {
            SEED_VERTICES[i]: a
            for i, a in enumerate(self._seed_amplitudes)
        }

    @property
    def entropy(self) -> Fraction:
        return self._entropy

    @property
    def cycle_count(self) -> int:
        return self._cycle

    @property
    def maps(self) -> list[DiscoveryMap]:
        return list(self._maps)

    @property
    def current_map(self) -> DiscoveryMap | None:
        return self._current_map

    @property
    def memory(self) -> list[dict]:
        return list(self._memory)

    # ── Resource budget ────────────────────────────────────────────

    def set_resource_budget(self, **resources: float | int) -> None:
        """Set resource constraints. Names are arbitrary: compute, bandwidth, memory, etc."""
        for name, capacity in resources.items():
            self.budget.set(name, capacity)

    # ── Lifecycle ──────────────────────────────────────────────────

    def _complexity_cost(self) -> Fraction:
        h_max = Fraction(math.log2(6)).limit_denominator(10_000)
        return h_max - self._entropy

    def _branching_threshold(self) -> Fraction:
        k = _to_fraction(BRANCHING_K)
        return k * self._complexity_cost()

    def _energy(self) -> Fraction:
        return _to_fraction(len(self._families))

    def should_expand(self) -> bool:
        """Should the agent bloom outward? True if energy exceeds complexity cost
        and resources haven't been exhausted."""
        if self.budget.is_exhausted():
            return False
        return self._energy() >= self._branching_threshold()

    def bloom(self, depth: int = 1) -> DiscoveryMap:
        """Expand outward from seed geometry. Costs compute and bandwidth.

        Returns the DiscoveryMap produced. The map is also stored internally.
        If resources run out mid-bloom, the partial map is preserved.
        """
        # Compute cost
        bloom_cost = _COST_BLOOM_BASE + _COST_BLOOM_PER_DEPTH * _to_fraction(depth)
        if not self.budget.spend("compute", bloom_cost):
            # Can't afford — return empty map at seed
            dm = DiscoveryMap()
            dm.amplitudes = list(self._seed_amplitudes)
            dm.entropy = self._entropy
            dm.depth = 0
            dm.budget_snapshot = self.budget.snapshot()
            return dm

        # Discover paths through the Rosetta graph
        paths = discover(self._graph, self._resolved_id, depth=depth)

        # Each path costs bandwidth
        accepted_paths = []
        for p in paths:
            if self.budget.spend("bandwidth", _BW_PER_PATH):
                accepted_paths.append(p)
            else:
                break  # bandwidth exhausted — partial bloom

        # Build the discovery map
        dm = DiscoveryMap()
        dm.paths = accepted_paths
        dm.amplitudes = list(self._seed_amplitudes)
        dm.entropy = self._entropy
        dm.depth = depth

        # Collect visited shapes
        dm.visited_shapes = {self._home_shape} if self._home_shape else set()
        for p in accepted_paths:
            ts = p.get("target_shape")
            if ts:
                dm.visited_shapes.add(ts)

        dm.budget_snapshot = self.budget.snapshot()

        self._current_map = dm
        self._state = "bloomed"
        self._cycle += 1

        return dm

    def explore(self) -> list[dict]:
        """Explore within the current bloom — hunt shadows, detect patterns.

        Returns the shadow report findings. Requires a bloom first.
        """
        if self._current_map is None:
            return []

        # Shadow hunting costs compute
        if not self.budget.spend("compute", _COST_SHADOW_HUNT):
            return []

        # Build a float-based seed dict for hunt_shadows compatibility
        seed_for_hunt = {
            "amplitudes": {
                SEED_VERTICES[i]: float(a)
                for i, a in enumerate(self._seed_amplitudes)
            },
            "entropy": float(self._entropy),
        }

        shadow_report = hunt_shadows(
            self._graph, self._resolved_id, seed_for_hunt
        )

        self._current_map.shadow_report = shadow_report
        self._state = "exploring"

        return shadow_report.get("shadows", [])

    def compress(self) -> dict:
        """Contract back to seed geometry, preserving the discovery map.

        The map becomes part of memory. The agent returns to seed state
        but doesn't lose what it found.
        """
        if not self.budget.spend("compute", _COST_COMPRESS):
            pass  # compression is cheap, but we track it

        # Archive the current map
        if self._current_map is not None:
            self._maps.append(self._current_map)
            # Commit a memory entry — the compressed knowledge
            self._memory.append({
                "cycle": self._cycle,
                "shapes_reached": sorted(self._current_map.visited_shapes),
                "paths_found": len(self._current_map.paths),
                "shadows": len(self._current_map.shadow_report.get("shadows", [])),
                "depth": self._current_map.depth,
                "budget_remaining": {
                    k: str(v) for k, v in self._current_map.budget_snapshot.items()
                },
            })

        self._current_map = None
        self._state = "compressed"

        return self._memory[-1] if self._memory else {}

    # ── Full cycle ─────────────────────────────────────────────────

    def run_cycle(self, depth: int = 1) -> dict:
        """Run a full bloom → explore → compress cycle. Returns cycle summary."""
        dm = self.bloom(depth=depth)
        shadows = self.explore()
        mem = self.compress()
        return {
            "cycle": self._cycle,
            "state": self._state,
            "map_summary": dm.summary(),
            "shadows_found": len(shadows),
            "memory_entry": mem,
            "budget": str(self.budget),
        }

    def run_cycles(self, n: int, depth: int = 1) -> list[dict]:
        """Run n bloom/explore/compress cycles, stopping if resources exhaust."""
        results = []
        for _ in range(n):
            if self.budget.is_exhausted():
                break
            results.append(self.run_cycle(depth=depth))
        return results

    # ── Serialization ──────────────────────────────────────────────

    def to_dict(self) -> dict:
        """Full agent state as a JSON-serializable dict (fractions as strings)."""
        return {
            "seed_id": self._resolved_id,
            "label": self._label,
            "home_shape": self._home_shape,
            "families": self._families,
            "state": self._state,
            "cycle": self._cycle,
            "amplitudes": {
                SEED_VERTICES[i]: str(a)
                for i, a in enumerate(self._seed_amplitudes)
            },
            "entropy": str(self._entropy),
            "complexity_cost": str(self._complexity_cost()),
            "branching_threshold": str(self._branching_threshold()),
            "energy": str(self._energy()),
            "should_expand": self.should_expand(),
            "budget": str(self.budget),
            "memory": self._memory,
            "maps_archived": len(self._maps),
        }


# ── CLI ────────────────────────────────────────────────────────────

def _print_agent(agent: ConstraintAgent):
    """Print agent state in human-readable form."""
    d = agent.to_dict()
    print(f"\n{'='*60}")
    print(f"  Constraint-Geometry Agent: {d['label']}")
    print(f"  Seed: {d['seed_id']}  |  Home: {d['home_shape']}")
    print(f"{'='*60}\n")

    print(f"  State:   {d['state']}")
    print(f"  Cycle:   {d['cycle']}")
    print(f"  Budget:  {d['budget']}")
    print(f"  Expand?  {'yes' if d['should_expand'] else 'no'}")
    print()

    print("  Seed amplitudes (exact fractions):")
    for vertex, amp in d["amplitudes"].items():
        bar = "#" * int(float(Fraction(amp)) * 40)
        print(f"    {vertex:12s}  {amp:>12s}  {bar}")
    print()

    print(f"  Entropy:             {d['entropy']}")
    print(f"  Complexity cost:     {d['complexity_cost']}")
    print(f"  Branching threshold: {d['branching_threshold']}")
    print(f"  Energy (families):   {d['energy']}")
    print()


def _print_cycle(result: dict, idx: int):
    """Print a single cycle result."""
    ms = result["map_summary"]
    print(f"  Cycle {idx}:")
    print(f"    Depth:          {ms['depth']}")
    print(f"    Paths found:    {ms['paths_found']}")
    print(f"    Shapes reached: {', '.join(ms['shapes_reached']) or 'none'}")
    print(f"    Shadows:        {result['shadows_found']}")
    print(f"    Budget after:   {result['budget']}")
    print()


def main():
    parser = argparse.ArgumentParser(
        description="Constraint-Geometry Agent Framework"
    )
    parser.add_argument("--seed", required=True,
                        help="Entity or shape to seed the agent (e.g., bee, SHAPE.TETRA)")
    parser.add_argument("--budget", default="compute=200,bandwidth=50",
                        help="Resource budget as name=value pairs (default: compute=200,bandwidth=50)")
    parser.add_argument("--cycle", type=int, default=1,
                        help="Number of bloom/explore/compress cycles (default: 1)")
    parser.add_argument("--depth", type=int, default=1,
                        help="Bloom depth per cycle (default: 1)")
    parser.add_argument("--json", action="store_true",
                        help="Output as JSON")
    args = parser.parse_args()

    graph = RosettaGraph()
    agent = ConstraintAgent(seed_id=args.seed, graph=graph)

    # Parse budget
    for pair in args.budget.split(","):
        name, val = pair.strip().split("=")
        agent.set_resource_budget(**{name.strip(): int(val.strip())})

    if args.json:
        results = agent.run_cycles(args.cycle, depth=args.depth)
        output = {
            "agent": agent.to_dict(),
            "cycles": results,
        }
        print(json.dumps(output, indent=2, default=str))
    else:
        _print_agent(agent)

        print("  Running cycles...")
        print()
        for i in range(args.cycle):
            if agent.budget.is_exhausted():
                print("  Budget exhausted. Stopping.")
                break
            result = agent.run_cycle(depth=args.depth)
            _print_cycle(result, i + 1)

        # Final state
        print(f"  Final state: {agent.state}")
        print(f"  Total cycles: {agent.cycle_count}")
        print(f"  Budget: {agent.budget}")
        if agent.memory:
            total_shapes = set()
            total_paths = 0
            total_shadows = 0
            for m in agent.memory:
                total_shapes.update(m["shapes_reached"])
                total_paths += m["paths_found"]
                total_shadows += m["shadows"]
            print(f"  Total shapes discovered: {len(total_shapes)}")
            print(f"  Total paths found:       {total_paths}")
            print(f"  Total shadows detected:  {total_shadows}")
        print()


if __name__ == "__main__":
    main()
