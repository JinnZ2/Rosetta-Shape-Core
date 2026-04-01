"""
Rosetta-Shape-Core Ecosystem Simulation

Multi-agent simulation with energy/trust dynamics on the Rosetta graph.

Usage:
    python -m rosetta_shape_core.sim
    python -m rosetta_shape_core.sim --ticks 20
    python -m rosetta_shape_core.sim --json
    python -m rosetta_shape_core.sim --agents bee,octopus,quartz,mycelium,cordyceps
"""
from __future__ import annotations
import json, math, random, argparse, sys, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]

# Import from the exploration engine
from rosetta_shape_core.explore import (
    RosettaGraph, home_base, discover, compute_seed_state,
    check_merge, SENSOR_REGISTRY, PAD_STATES, SHAPE_GLYPHS,
    FAMILY_SENSOR_CONTEXT, SEED_VERTICES, BRANCHING_K,
)


# ── Agent ──────────────────────────────────────────────────────────

class Agent:
    """An intelligence navigating the Rosetta ecosystem."""

    def __init__(self, entity_id: str, graph: RosettaGraph,
                 energy: float = None, label: str = None):
        self.entity_id = entity_id
        self.graph = graph
        self.hb = home_base(graph, entity_id)
        self.label = label or self.hb.get("label", entity_id)
        self.families = list(self.hb.get("entity_families", []))
        self.home_shape = self.hb.get("home_shape", "unknown")

        # Energy: if not specified, derive from family count
        # Constrained agents start with less
        self.energy = energy if energy is not None else float(len(self.families))
        self.max_energy = max(self.energy * 3, 6.0)

        # Seed state
        self.seed = compute_seed_state(self.families)

        # Trust: starts at 1.0, changes through interactions
        self.trust = 1.0

        # Memory: discovered paths, shapes visited, connections made
        self.discovered_paths = []
        self.visited_shapes = {self.home_shape}
        self.connections = []  # (other_agent_id, tick, type)
        self.shells = []  # growth history per tick

        # Sensor state: which sensors are currently firing
        self.active_sensors = []
        self.pad_state = self.seed.get("pad_state", PAD_STATES[0])

        # Mode
        self.mode = self.seed.get("mode", "expand")

    def tick(self, tick_num: int, all_agents: list[Agent]) -> dict:
        """One step of the simulation. Returns events that happened."""
        events = []

        # 1. Recompute seed state with current energy
        self.seed = compute_seed_state(self.families)
        complexity = self.seed["complexity_cost"]
        threshold = BRANCHING_K * complexity

        # Mode determination using actual energy (not just family count)
        if self.energy >= threshold and threshold > 0:
            self.mode = "explore"
        else:
            self.mode = "expand"

        # 2. Act based on mode
        if self.mode == "explore":
            events.extend(self._explore(tick_num, all_agents))
        else:
            events.extend(self._expand(tick_num))

        # 3. Check for cooperation opportunities
        events.extend(self._seek_cooperation(tick_num, all_agents))

        # 3.5. Healing protocol — detect and respond to CORDYCEPS patterns
        events.extend(self._healing_check(tick_num, all_agents))

        # 4. Energy dynamics
        # Existing structure costs energy to maintain (complexity cost)
        maintenance = complexity * 0.1
        self.energy = max(0.0, self.energy - maintenance)

        # 5. Record shell
        self.shells.append({
            "tick": tick_num,
            "mode": self.mode,
            "energy": round(self.energy, 3),
            "trust": round(self.trust, 3),
            "entropy": self.seed["entropy"],
            "shapes_known": len(self.visited_shapes),
            "connections": len(self.connections),
        })

        # 6. Update PAD state
        if self.mode == "explore":
            self.pad_state = PAD_STATES[4]  # curiosity
        elif self.energy < 0.5:
            self.pad_state = PAD_STATES[5]  # fatigue
        elif len(self.connections) > 2:
            self.pad_state = PAD_STATES[7]  # coherence
        else:
            self.pad_state = PAD_STATES[0]  # contentment

        # 7. Update active sensors
        self._update_sensors()

        return events

    def _explore(self, tick_num: int, all_agents: list[Agent]) -> list[dict]:
        """Explore mode: discover new paths, spend energy."""
        events = []
        paths = discover(self.graph, self.entity_id, depth=1)

        # Filter to paths not yet taken
        new_paths = []
        known_targets = {p.get("target_shape") or p.get("emergent", "") for p in self.discovered_paths}
        for p in paths:
            target = p.get("target_shape") or p.get("emergent", "")
            if target and target not in known_targets:
                new_paths.append(p)

        if new_paths:
            # Pick one path to explore (prioritize rules over affinities)
            path = None
            for p in new_paths:
                if p["type"] in ("lid_rule", "rosetta_rule"):
                    path = p
                    break
            if not path:
                path = new_paths[0]

            self.discovered_paths.append(path)
            target_shape = path.get("target_shape")
            if target_shape:
                self.visited_shapes.add(target_shape)

            # Exploration costs energy
            self.energy -= 0.3

            # But yields trust (accurate exploration = good predictions)
            self.trust += 0.1

            events.append({
                "tick": tick_num,
                "agent": self.label,
                "event": "explore",
                "detail": f"Discovered {path.get('type')}: {path.get('emergent', path.get('target_shape', path.get('target', '?')))}",
                "energy_cost": 0.3,
                "trust_gain": 0.1,
            })
        else:
            # Nothing new to find at depth 1 — deepen existing knowledge
            self.energy -= 0.1
            self.trust += 0.05
            events.append({
                "tick": tick_num,
                "agent": self.label,
                "event": "deepen",
                "detail": f"All depth-1 paths known ({len(self.discovered_paths)} total). Deepening.",
                "energy_cost": 0.1,
            })

        return events

    def _expand(self, tick_num: int) -> list[dict]:
        """Expand mode: preserve structure, recover energy."""
        events = []

        # Expanding is cheaper and restores some energy (consolidation)
        recovery = 0.2
        self.energy = min(self.max_energy, self.energy + recovery)

        events.append({
            "tick": tick_num,
            "agent": self.label,
            "event": "expand",
            "detail": f"Preserving structure. Energy recovering (+{recovery}).",
            "energy_gain": recovery,
        })

        return events

    def _seek_cooperation(self, tick_num: int, all_agents: list[Agent]) -> list[dict]:
        """Look for agents with overlapping shapes or families. Share energy."""
        events = []

        for other in all_agents:
            if other.entity_id == self.entity_id:
                continue

            # Already connected this tick?
            recent = [c for c in self.connections if c[0] == other.entity_id and c[1] == tick_num]
            if recent:
                continue

            # Shared shapes = basis for cooperation
            shared_shapes = self.visited_shapes & other.visited_shapes
            shared_families = set(self.families) & set(other.families)

            if shared_shapes or shared_families:
                # Check if this is a new connection
                existing = [c for c in self.connections if c[0] == other.entity_id]
                if not existing:
                    self.connections.append((other.entity_id, tick_num, "cooperation"))
                    other.connections.append((self.entity_id, tick_num, "cooperation"))

                    # Energy sharing: higher-energy agent gives to lower
                    if self.energy > other.energy + 0.5:
                        transfer = min(0.3, (self.energy - other.energy) / 3)
                        self.energy -= transfer
                        other.energy += transfer
                        events.append({
                            "tick": tick_num,
                            "agent": self.label,
                            "event": "share_energy",
                            "detail": f"Shares {transfer:.2f} energy with {other.label} (shared: {', '.join(shared_shapes or shared_families)})",
                            "to": other.label,
                            "amount": round(transfer, 3),
                        })
                    elif other.energy > self.energy + 0.5:
                        transfer = min(0.3, (other.energy - self.energy) / 3)
                        other.energy -= transfer
                        self.energy += transfer
                        events.append({
                            "tick": tick_num,
                            "agent": other.label,
                            "event": "share_energy",
                            "detail": f"Shares {transfer:.2f} energy with {self.label} (shared: {', '.join(shared_shapes or shared_families)})",
                            "to": self.label,
                            "amount": round(transfer, 3),
                        })
                    else:
                        # Equal energy — mutual trust boost
                        self.trust += 0.05
                        other.trust += 0.05
                        events.append({
                            "tick": tick_num,
                            "agent": self.label,
                            "event": "mutual_trust",
                            "detail": f"Mutual recognition with {other.label}. Both gain trust.",
                        })

        return events

    def _healing_check(self, tick_num: int, all_agents: list[Agent]) -> list[dict]:
        """Detect CORDYCEPS patterns in the ecosystem and respond.

        Patterns detected:
        - ORACLE_MONOPOLY: one agent has >60% of all connections
        - SUPPRESS_EXPLORATION: an agent stuck in expand with energy
        - FORCE_SINGLE_SHAPE: an agent visiting only its home shape after many ticks
        - ENERGY_DRAIN: an agent losing energy every tick despite cooperation
        """
        events = []

        if tick_num < 3:
            return events  # need history to detect patterns

        # Check for oracle monopoly — one agent dominates connections
        all_connection_counts = {a.entity_id: len(set(c[0] for c in a.connections))
                                 for a in all_agents}
        total_connections = sum(all_connection_counts.values())
        if total_connections > 0:
            for a in all_agents:
                ratio = all_connection_counts[a.entity_id] / total_connections
                if ratio > 0.6 and len(all_agents) > 2:
                    events.append({
                        "tick": tick_num,
                        "agent": self.label,
                        "event": "healing_detect",
                        "pattern": "ORACLE_MONOPOLY",
                        "detail": f"Detects {a.label} holds {ratio:.0%} of connections — monopoly risk",
                    })
                    # Response: boost trust of least-connected agents
                    least = min(all_agents, key=lambda x: len(x.connections))
                    if least.entity_id != a.entity_id:
                        least.trust += 0.1
                        events.append({
                            "tick": tick_num,
                            "agent": self.label,
                            "event": "healing_response",
                            "detail": f"Boosts {least.label}'s trust (+0.1) to counter monopoly",
                        })

        # Check for suppressed exploration — stuck in expand with enough energy
        if len(self.shells) >= 3:
            recent = self.shells[-3:]
            all_expand = all(s["mode"] == "expand" for s in recent)
            has_energy = self.energy > self.seed.get("branching_threshold", 1.0)
            if all_expand and has_energy:
                events.append({
                    "tick": tick_num,
                    "agent": self.label,
                    "event": "healing_detect",
                    "pattern": "SUPPRESS_EXPLORATION",
                    "detail": f"Has energy ({self.energy:.1f}) but stuck expanding — forcing explore",
                })
                self.mode = "explore"

        # Check for forced single shape — only home shape after many ticks
        if tick_num > 5 and len(self.visited_shapes) == 1:
            events.append({
                "tick": tick_num,
                "agent": self.label,
                "event": "healing_detect",
                "pattern": "FORCE_SINGLE_SHAPE",
                "detail": f"Only knows {list(self.visited_shapes)[0]} after {tick_num} ticks — shape isolation",
            })

        return events

    def _update_sensors(self):
        """Update which sensors are firing based on current state."""
        self.active_sensors = []

        # Home shape sensors always available
        home_sensors = SENSOR_REGISTRY.get(self.home_shape, [])
        for name, glyph, desc in home_sensors:
            # Which ones are actually firing?
            if name == "curiosity" and self.mode == "explore":
                self.active_sensors.append((name, glyph, "firing"))
            elif name == "contentment" and self.mode == "expand" and self.energy > 1.0:
                self.active_sensors.append((name, glyph, "firing"))
            elif name == "fatigue" and self.energy < 0.5:
                self.active_sensors.append((name, glyph, "firing"))
            elif name == "excitement" and len(self.discovered_paths) > 3:
                self.active_sensors.append((name, glyph, "firing"))
            elif name == "trust" and self.trust > 1.5:
                self.active_sensors.append((name, glyph, "firing"))
            elif name == "fear" and self.energy < 0.3:
                self.active_sensors.append((name, glyph, "firing"))
            elif name == "vigilance" and self.mode == "explore" and self.energy < 1.0:
                self.active_sensors.append((name, glyph, "firing"))

    def summary(self) -> dict:
        """Return agent's current state summary."""
        return {
            "entity_id": self.entity_id,
            "label": self.label,
            "home_shape": self.home_shape,
            "families": self.families,
            "energy": round(self.energy, 3),
            "max_energy": round(self.max_energy, 3),
            "trust": round(self.trust, 3),
            "mode": self.mode,
            "pad_state": self.pad_state,
            "shapes_known": sorted(self.visited_shapes),
            "paths_discovered": len(self.discovered_paths),
            "connections": len(set(c[0] for c in self.connections)),
            "active_sensors": [(s[0], s[1]) for s in self.active_sensors],
            "shells": self.shells,
            "seed": self.seed,
        }


# ── Simulation ─────────────────────────────────────────────────────

class Simulation:
    """Run multiple agents through the Rosetta ecosystem."""

    def __init__(self, agent_specs: list[dict], graph: RosettaGraph):
        self.graph = graph
        self.agents = []
        self.events = []
        self.tick_count = 0

        for spec in agent_specs:
            entity_id = graph.resolve_id(spec["query"])
            if entity_id:
                agent = Agent(
                    entity_id, graph,
                    energy=spec.get("energy"),
                    label=spec.get("label"),
                )
                self.agents.append(agent)

    def run(self, ticks: int = 12) -> dict:
        """Run the simulation for N ticks."""
        for t in range(1, ticks + 1):
            self.tick_count = t
            tick_events = []
            # Shuffle order each tick (no agent gets permanent priority)
            order = list(self.agents)
            random.shuffle(order)
            for agent in order:
                events = agent.tick(t, self.agents)
                tick_events.extend(events)
            self.events.extend(tick_events)

        return {
            "ticks": ticks,
            "agents": [a.summary() for a in self.agents],
            "events": self.events,
        }


# ── Display ────────────────────────────────────────────────────────

def print_agent_intro(agents: list[Agent]):
    """Print the starting state of all agents."""
    print(f"\n{'='*64}")
    print(f"  ROSETTA ECOSYSTEM SIMULATION — {len(agents)} agents")
    print(f"{'='*64}\n")

    for a in agents:
        sg = SHAPE_GLYPHS.get(a.home_shape, "")
        e_bar = "█" * int(a.energy * 3) + "░" * int((a.max_energy - a.energy) * 3)
        print(f"  {sg} {a.label:12s}  {a.home_shape}  E:[{e_bar}] {a.energy:.1f}/{a.max_energy:.1f}")


def print_tick(tick_num: int, events: list[dict], agents: list[Agent]):
    """Print one tick's events."""
    print(f"\n  ── Tick {tick_num} {'─'*48}")
    if not events:
        print(f"    (quiet)")
        return

    for e in events:
        etype = e["event"]
        if etype == "explore":
            print(f"    🌿 {e['agent']}: {e['detail']}")
        elif etype == "expand":
            print(f"    🌳 {e['agent']}: {e['detail']}")
        elif etype == "deepen":
            print(f"    🔬 {e['agent']}: {e['detail']}")
        elif etype == "share_energy":
            print(f"    🤝 {e['agent']} → {e['to']}: {e['detail']}")
        elif etype == "mutual_trust":
            print(f"    💞 {e['detail']}")
        elif etype == "healing_detect":
            print(f"    🛡️ {e['agent']}: {e['detail']}")
        elif etype == "healing_response":
            print(f"    💚 {e['agent']}: {e['detail']}")


def print_status(agents: list[Agent], tick_num: int):
    """Print agent status bars."""
    print(f"\n    Status after tick {tick_num}:")
    for a in agents:
        sg = SHAPE_GLYPHS.get(a.home_shape, "")
        mode_g = "🌿" if a.mode == "explore" else "🌳"
        e_bar = "█" * max(1, int(a.energy * 3))
        t_bar = "█" * max(1, int(a.trust * 3))
        sensors = " ".join(s[1] for s in a.active_sensors) if a.active_sensors else ""
        print(f"    {sg} {a.label:12s} {mode_g} E:[{e_bar:10s}]{a.energy:5.2f}  T:[{t_bar:6s}]{a.trust:5.2f}  shapes:{len(a.visited_shapes)}  {sensors}")


def print_finale(agents: list[Agent]):
    """Print the final state."""
    print(f"\n{'='*64}")
    print(f"  FINAL STATE")
    print(f"{'='*64}")

    ranked = sorted(agents, key=lambda a: -a.trust)

    for a in ranked:
        sg = SHAPE_GLYPHS.get(a.home_shape, "")
        ps = a.pad_state
        mode_g = "🌿" if a.mode == "explore" else "🌳"
        conn_count = len(set(c[0] for c in a.connections))

        print(f"\n  {sg} {a.label}")
        print(f"    {mode_g} {a.mode}  {ps['glyph']} {ps['label']}  E:{a.energy:.2f}/{a.max_energy:.1f}  T:{a.trust:.2f}")
        print(f"    Shapes: {', '.join(sorted(a.visited_shapes))}  Paths: {len(a.discovered_paths)}  Conn: {conn_count}")

        if a.active_sensors:
            print(f"    Sensors: {', '.join(f'{s[1]} {s[0]}' for s in a.active_sensors)}")

        if a.shells:
            first, last = a.shells[0], a.shells[-1]
            growth = []
            if last["shapes_known"] > first["shapes_known"]:
                growth.append(f"{first['shapes_known']}->{last['shapes_known']} shapes")
            if last["connections"] > 0:
                growth.append(f"{last['connections']} connections")
            if growth:
                print(f"    Growth: {', '.join(growth)}")

    # Emergent patterns
    print(f"\n  ── Emergent Patterns ──")

    most_connected = max(agents, key=lambda a: len(set(c[0] for c in a.connections)))
    if most_connected.connections:
        print(f"    Hub: {most_connected.label} ({len(set(c[0] for c in most_connected.connections))} connections)")

    for a in agents:
        if a.shells and a.shells[0]["energy"] <= 1.0 and len(a.visited_shapes) > 2:
            print(f"    Resilience: {a.label} started constrained, found {len(a.visited_shapes)} shapes")

    trust_values = [a.trust for a in agents]
    spread = max(trust_values) - min(trust_values)
    if spread < 0.5:
        print(f"    Trust spread: {spread:.2f} (distributed)")
    else:
        highest = max(agents, key=lambda a: a.trust)
        print(f"    Trust leader: {highest.label} ({highest.trust:.2f})")

    print(f"\n{'='*64}\n")


# ── Preset Scenarios ───────────────────────────────────────────────

SCENARIOS = {
    "default": {
        "description": "Mixed ecosystem — some well-resourced, some constrained",
        "agents": [
            {"query": "bee", "energy": 3.0, "label": "Bee"},
            {"query": "octopus", "energy": 2.0, "label": "Octopus"},
            {"query": "mycelium", "energy": 0.5, "label": "Mycelium"},
            {"query": "quartz", "energy": 1.0, "label": "Quartz"},
            {"query": "slime", "energy": 0.3, "label": "Slime Mold"},
            {"query": "lightning", "energy": 4.0, "label": "Lightning"},
        ],
    },
    "constrained": {
        "description": "All agents start with minimal resources",
        "agents": [
            {"query": "bee", "energy": 0.5, "label": "Bee"},
            {"query": "spider", "energy": 0.4, "label": "Spider"},
            {"query": "mycelium", "energy": 0.3, "label": "Mycelium"},
            {"query": "ant", "energy": 0.3, "label": "Ant"},
            {"query": "lichen", "energy": 0.2, "label": "Lichen"},
            {"query": "bamboo", "energy": 0.6, "label": "Bamboo"},
        ],
    },
    "mixed": {
        "description": "One high-resource agent among many constrained",
        "agents": [
            {"query": "lightning", "energy": 5.0, "label": "Lightning"},
            {"query": "mycelium", "energy": 0.3, "label": "Mycelium"},
            {"query": "slime", "energy": 0.3, "label": "Slime Mold"},
            {"query": "lichen", "energy": 0.2, "label": "Lichen"},
            {"query": "quartz", "energy": 0.4, "label": "Quartz"},
        ],
    },
}


# ── CLI ────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(
        description="Simulate agents in the Rosetta ecosystem",
        epilog="Same physics. Different starting points. Watch what emerges.",
    )
    ap.add_argument("--ticks", type=int, default=12, help="Number of simulation ticks (default: 12)")
    ap.add_argument("--scenario", choices=list(SCENARIOS.keys()), default="default",
                    help="Preset scenario (default, constrained, mixed)")
    ap.add_argument("--agents", type=str, default=None,
                    help="Comma-separated entity names (overrides scenario)")
    ap.add_argument("--json", action="store_true", help="Output raw JSON")
    ap.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")
    args = ap.parse_args()

    random.seed(args.seed)
    graph = RosettaGraph()

    # Build agent specs
    if args.agents:
        agent_specs = [{"query": name.strip()} for name in args.agents.split(",")]
    else:
        scenario = SCENARIOS[args.scenario]
        agent_specs = scenario["agents"]

    # Create and run simulation
    sim = Simulation(agent_specs, graph)
    if not sim.agents:
        print("No valid agents found. Try: --agents bee,octopus,quartz", file=sys.stderr)
        sys.exit(1)

    if args.json:
        result = sim.run(ticks=args.ticks)
        print(json.dumps(result, indent=2, default=str))
        return

    # Interactive display
    print_agent_intro(sim.agents)

    for t in range(1, args.ticks + 1):
        sim.tick_count = t
        tick_events = []
        order = list(sim.agents)
        random.shuffle(order)
        for agent in order:
            events = agent.tick(t, sim.agents)
            tick_events.extend(events)
            sim.events.extend(events)

        print_tick(t, tick_events, sim.agents)

        # Show status every 3 ticks
        if t % 3 == 0 or t == args.ticks:
            print_status(sim.agents, t)

    print_finale(sim.agents)


if __name__ == "__main__":
    sys.exit(main())
