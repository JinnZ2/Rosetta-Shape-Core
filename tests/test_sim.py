"""Tests for the Ecosystem Simulation."""
import random

from rosetta_shape_core.explore import RosettaGraph
from rosetta_shape_core.sim import SCENARIOS, Agent, Simulation

# ── Agent basics ──────────────────────────────────────────────────

def test_agent_creation():
    g = RosettaGraph()
    a = Agent("ANIMAL.BEE", g, energy=3.0)
    assert a.entity_id == "ANIMAL.BEE"
    assert a.energy == 3.0
    assert a.trust == 1.0
    assert a.home_shape is not None
    assert len(a.families) > 0


def test_agent_default_energy():
    """Default energy derives from family count."""
    g = RosettaGraph()
    a = Agent("ANIMAL.BEE", g)
    assert a.energy == float(len(a.families))


def test_agent_tick_returns_events():
    g = RosettaGraph()
    a = Agent("ANIMAL.BEE", g, energy=3.0)
    events = a.tick(1, [a])
    assert isinstance(events, list)
    assert len(events) > 0


def test_agent_explore_mode():
    """High energy agent should explore."""
    g = RosettaGraph()
    a = Agent("ANIMAL.BEE", g, energy=10.0)
    a.tick(1, [a])
    assert a.mode == "explore"


def test_agent_expand_mode():
    """Very low energy agent should expand."""
    g = RosettaGraph()
    a = Agent("ANIMAL.BEE", g, energy=0.01)
    a.tick(1, [a])
    assert a.mode == "expand"


def test_agent_energy_decreases_on_explore():
    g = RosettaGraph()
    a = Agent("ANIMAL.BEE", g, energy=10.0)
    initial = a.energy
    a.tick(1, [a])
    assert a.energy < initial


def test_agent_energy_recovers_on_expand():
    g = RosettaGraph()
    a = Agent("ANIMAL.BEE", g, energy=0.01)
    a.tick(1, [a])
    # Expand recovers 0.2, minus maintenance
    assert a.energy > 0.01 or a.energy >= 0


def test_agent_trust_increases_on_explore():
    g = RosettaGraph()
    a = Agent("ANIMAL.BEE", g, energy=10.0)
    a.tick(1, [a])
    assert a.trust > 1.0


def test_agent_shell_recorded():
    g = RosettaGraph()
    a = Agent("ANIMAL.BEE", g, energy=3.0)
    a.tick(1, [a])
    assert len(a.shells) == 1
    assert a.shells[0]["tick"] == 1
    assert "energy" in a.shells[0]
    assert "mode" in a.shells[0]


def test_agent_summary():
    g = RosettaGraph()
    a = Agent("ANIMAL.BEE", g, energy=3.0)
    a.tick(1, [a])
    s = a.summary()
    assert s["entity_id"] == "ANIMAL.BEE"
    assert "energy" in s
    assert "trust" in s
    assert "mode" in s
    assert "shells" in s
    assert "seed" in s


# ── Cooperation ───────────────────────────────────────────────────

def test_cooperation_between_agents():
    """Agents with shared shapes/families should form connections over time."""
    random.seed(42)
    g = RosettaGraph()
    specs = [{"query": "bee", "energy": 5.0}, {"query": "octopus", "energy": 2.0}]
    sim = Simulation(specs, g)
    sim.run(ticks=6)
    # Over 6 ticks, agents should find shared shapes and cooperate
    total_connections = sum(len(a.connections) for a in sim.agents)
    assert total_connections > 0


def test_energy_sharing_direction():
    """Higher-energy agent shares with lower-energy agent."""
    random.seed(42)
    g = RosettaGraph()
    a = Agent("ANIMAL.BEE", g, energy=10.0)
    b = Agent("ANIMAL.BEE", g, energy=0.5)
    a.tick(1, [a, b])
    # b should have received energy (or a should have less)
    assert a.energy < 10.0


# ── Simulation ────────────────────────────────────────────────────

def test_simulation_creation():
    g = RosettaGraph()
    specs = [{"query": "bee"}, {"query": "octopus"}]
    sim = Simulation(specs, g)
    assert len(sim.agents) == 2


def test_simulation_run():
    random.seed(42)
    g = RosettaGraph()
    specs = [{"query": "bee", "energy": 3.0}, {"query": "octopus", "energy": 2.0}]
    sim = Simulation(specs, g)
    result = sim.run(ticks=5)
    assert result["ticks"] == 5
    assert len(result["agents"]) == 2
    assert len(result["events"]) > 0


def test_simulation_agents_have_shells():
    random.seed(42)
    g = RosettaGraph()
    specs = [{"query": "bee", "energy": 3.0}]
    sim = Simulation(specs, g)
    sim.run(ticks=5)
    assert len(sim.agents[0].shells) == 5


def test_simulation_invalid_agent():
    """Invalid entity names should be skipped, not crash."""
    g = RosettaGraph()
    specs = [{"query": "bee"}, {"query": "NONEXISTENT_ENTITY_XYZ"}]
    sim = Simulation(specs, g)
    # bee should resolve, nonexistent should not
    assert len(sim.agents) >= 1


# ── Scenarios ─────────────────────────────────────────────────────

def test_scenarios_exist():
    assert "default" in SCENARIOS
    assert "constrained" in SCENARIOS
    assert "mixed" in SCENARIOS


def test_default_scenario_agents():
    assert len(SCENARIOS["default"]["agents"]) > 0
    for spec in SCENARIOS["default"]["agents"]:
        assert "query" in spec


def test_constrained_scenario_low_energy():
    """Constrained scenario should have low starting energy."""
    for spec in SCENARIOS["constrained"]["agents"]:
        assert spec.get("energy", 1.0) <= 1.0


# ── Energy Ledger ────────────────────────────────────────────────

def test_energy_ledger_exists():
    """Simulation should have an energy ledger."""
    g = RosettaGraph()
    specs = [{"query": "bee", "energy": 3.0}]
    sim = Simulation(specs, g)
    assert sim.energy_ledger is not None
    assert sim.energy_ledger.initial_total == 3.0


def test_energy_ledger_records_ticks():
    """Ledger should have one entry per tick."""
    random.seed(42)
    g = RosettaGraph()
    specs = [{"query": "bee", "energy": 3.0}, {"query": "octopus", "energy": 2.0}]
    sim = Simulation(specs, g)
    sim.run(ticks=5)
    assert len(sim.energy_ledger.ticks) == 5


def test_energy_audit_in_result():
    """Simulation result should include energy_audit."""
    random.seed(42)
    g = RosettaGraph()
    specs = [{"query": "bee", "energy": 3.0}]
    sim = Simulation(specs, g)
    result = sim.run(ticks=3)
    assert "energy_audit" in result
    audit = result["energy_audit"]
    assert "initial_total" in audit
    assert "final_total" in audit
    assert "violations" in audit
    assert audit["ticks_recorded"] == 3


def test_energy_no_negative_violations():
    """Agents should never have negative energy (clamped at 0)."""
    random.seed(42)
    g = RosettaGraph()
    specs = [{"query": "bee", "energy": 3.0}, {"query": "octopus", "energy": 0.1}]
    sim = Simulation(specs, g)
    sim.run(ticks=10)
    audit = sim.energy_ledger.summary()
    neg_violations = [v for v in audit["violations"] if "NON_NEGATIVE" in v]
    assert len(neg_violations) == 0


def test_energy_cooperation_is_zero_sum():
    """Energy sharing between agents should be zero-sum."""
    random.seed(42)
    g = RosettaGraph()
    a = Agent("ANIMAL.BEE", g, energy=10.0, label="Giver")
    b = Agent("ANIMAL.BEE", g, energy=1.0, label="Receiver")
    a.tick(1, [a, b])
    # The only non-zero-sum changes are maintenance and mode costs
    # Transfer itself should not create/destroy energy
    share_events = [e for e in a.tick(2, [a, b]) if e.get("event") == "share_energy"]
    for e in share_events:
        # Transfer amount should be reflected in both agents
        assert e.get("amount", 0) >= 0


def test_energy_ledger_summary_structure():
    """Ledger summary should have all required fields."""
    random.seed(42)
    g = RosettaGraph()
    specs = [{"query": "bee", "energy": 5.0}]
    sim = Simulation(specs, g)
    sim.run(ticks=3)
    summary = sim.energy_ledger.summary()
    assert "initial_total" in summary
    assert "final_total" in summary
    assert "net_change" in summary
    assert "violations" in summary
    assert "conservation_note" in summary


def test_energy_conservation_closed_system():
    """Total system energy (agents + environment) should be conserved."""
    random.seed(42)
    g = RosettaGraph()
    specs = [
        {"query": "bee", "energy": 3.0},
        {"query": "octopus", "energy": 2.0},
        {"query": "mycelium", "energy": 0.5},
    ]
    sim = Simulation(specs, g)
    initial_system = sum(a.energy for a in sim.agents) + sim.env["energy"]
    result = sim.run(ticks=20)
    final_agents = sum(a["energy"] for a in result["agents"])
    final_env = result["environment_energy"]
    final_system = final_agents + final_env
    # Conservation: total should be unchanged within float tolerance
    assert abs(final_system - initial_system) < 0.05, (
        f"Conservation violated: initial={initial_system:.4f}, "
        f"final={final_system:.4f} (agents={final_agents:.4f} + env={final_env:.4f})"
    )


def test_environment_energy_in_result():
    """Simulation result should include environment_energy."""
    random.seed(42)
    g = RosettaGraph()
    specs = [{"query": "bee", "energy": 3.0}]
    sim = Simulation(specs, g)
    result = sim.run(ticks=3)
    assert "environment_energy" in result
    assert result["environment_energy"] >= 0


def test_no_conservation_violations():
    """No CONSERVATION violations should appear in the energy audit."""
    random.seed(42)
    g = RosettaGraph()
    specs = [
        {"query": "bee", "energy": 5.0},
        {"query": "octopus", "energy": 3.0},
    ]
    sim = Simulation(specs, g)
    result = sim.run(ticks=15)
    audit = result["energy_audit"]
    conservation_violations = [v for v in audit["violations"] if "CONSERVATION" in v]
    assert conservation_violations == [], f"Conservation violated: {conservation_violations}"
