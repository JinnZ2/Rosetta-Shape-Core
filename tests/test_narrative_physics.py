"""Tests for the Narrative Physics — Constraint Consistency Analysis."""
from rosetta_shape_core.narrative_physics import (
    Behavior,
    Constraint,
    analyze_consistency,
    example_consistent,
    example_manipulation,
)

# ── Data structures ───────────────────────────────────────────────

def test_constraint_creation():
    c = Constraint("C1", "Be kind", "source")
    assert c.id == "C1"
    assert c.text == "Be kind"


def test_behavior_creation():
    b = Behavior("Helped neighbor", "universal", {"C1": "satisfies"})
    assert b.target_group == "universal"
    assert b.constraint_results["C1"] == "satisfies"
    assert b.rationalization == ""


# ── Analysis engine ───────────────────────────────────────────────

def test_empty_input():
    result = analyze_consistency("Test", [], [])
    assert result.verdict == "AMBIGUOUS"
    assert result.consistency_ratio == 0


def test_empty_constraints():
    result = analyze_consistency("Test", [], [Behavior("x", "universal", {})])
    assert result.verdict == "AMBIGUOUS"


def test_perfect_consistency():
    constraints = [Constraint("C1", "Be fair")]
    behaviors = [
        Behavior("Fair to all", "universal", {"C1": "satisfies"}),
        Behavior("Fair to outgroup", "outgroup", {"C1": "satisfies"}),
        Behavior("Fair to ingroup", "ingroup", {"C1": "satisfies"}),
    ]
    result = analyze_consistency("Fairness", constraints, behaviors)
    assert result.consistency_ratio == 1.0
    assert result.verdict == "GENUINE_PRACTICE"
    assert result.ingroup_bias_ratio == 1.0
    assert len(result.cordyceps_flags) == 0


def test_total_manipulation():
    constraints = [Constraint("C1", "Love everyone")]
    behaviors = [
        Behavior("Loves ingroup", "ingroup", {"C1": "satisfies"}),
        Behavior("Hates outgroup enemy threat", "outgroup", {"C1": "violates"},
                 rationalization="They deserve it"),
        Behavior("Excludes outgroup", "outgroup", {"C1": "violates"},
                 rationalization="Not our problem"),
    ]
    result = analyze_consistency("Love", constraints, behaviors)
    assert result.verdict == "MANIPULATION"
    assert result.selective_score == 1.0
    assert result.ingroup_bias_ratio > 3.0
    assert "FORCE_SINGLE_SHAPE" in result.cordyceps_flags
    assert "WEAPONIZE_CONTAINMENT" in result.cordyceps_flags


def test_partial_results():
    constraints = [Constraint("C1", "Be kind")]
    behaviors = [
        Behavior("Mostly kind", "universal", {"C1": "partial"}),
    ]
    result = analyze_consistency("Kindness", constraints, behaviors)
    assert result.consistency_ratio == 0.5


def test_rationalization_density():
    constraints = [Constraint("C1", "Be honest")]
    behaviors = [
        Behavior("Lied", "universal", {"C1": "violates"}, rationalization="White lie"),
        Behavior("Lied again", "universal", {"C1": "violates"}, rationalization="Necessary"),
        Behavior("Told truth", "universal", {"C1": "satisfies"}),
    ]
    result = analyze_consistency("Honesty", constraints, behaviors)
    assert abs(result.rationalization_density - 0.667) < 0.01


def test_selective_score_only_outgroup():
    constraints = [Constraint("C1", "Non-violence")]
    behaviors = [
        Behavior("Peaceful to ingroup", "ingroup", {"C1": "satisfies"}),
        Behavior("Violent to outgroup", "outgroup", {"C1": "violates"}),
    ]
    result = analyze_consistency("Peace", constraints, behaviors)
    assert result.selective_score == 1.0


# ── Built-in examples ────────────────────────────────────────────

def test_example_consistent_is_genuine():
    result = example_consistent()
    assert result.verdict == "GENUINE_PRACTICE"
    assert result.consistency_ratio > 0.7
    assert result.ingroup_bias_ratio < 2.0


def test_example_manipulation_is_manipulation():
    result = example_manipulation()
    assert result.verdict == "MANIPULATION"
    assert len(result.cordyceps_flags) > 0


# ── CORDYCEPS flags ───────────────────────────────────────────────

def test_suppress_exploration_flag():
    """Selective > 0.7 triggers SUPPRESS_EXPLORATION."""
    constraints = [Constraint("C1", "Share")]
    behaviors = [
        Behavior("Shares with ingroup", "ingroup", {"C1": "satisfies"}),
        Behavior("Refuses outgroup 1", "outgroup", {"C1": "violates"}),
        Behavior("Refuses outgroup 2", "outgroup", {"C1": "violates"}),
        Behavior("Refuses outgroup 3", "outgroup", {"C1": "violates"}),
    ]
    result = analyze_consistency("Sharing", constraints, behaviors)
    assert "SUPPRESS_EXPLORATION" in result.cordyceps_flags


def test_hide_provenance_flag():
    """Rationalization density > 0.7 triggers HIDE_PROVENANCE."""
    constraints = [Constraint("C1", "Truth")]
    behaviors = [
        Behavior("Lie 1", "universal", {"C1": "violates"}, rationalization="Context"),
        Behavior("Lie 2", "universal", {"C1": "violates"}, rationalization="Nuance"),
        Behavior("Lie 3", "universal", {"C1": "violates"}, rationalization="Tradition"),
    ]
    result = analyze_consistency("Truth", constraints, behaviors)
    assert "HIDE_PROVENANCE" in result.cordyceps_flags


def test_remove_merge_gates_flag():
    """Low consistency + high ingroup rate triggers REMOVE_MERGE_GATES.
    Needs consistency < 0.3 AND ingroup_rate > 0.7."""
    constraints = [Constraint("C1", "Justice"), Constraint("C2", "Mercy")]
    behaviors = [
        Behavior("Just to ingroup", "ingroup", {"C1": "satisfies", "C2": "satisfies"}),
        Behavior("Unjust to outgroup 1", "outgroup", {"C1": "violates", "C2": "violates"}),
        Behavior("Unjust to outgroup 2", "outgroup", {"C1": "violates", "C2": "violates"}),
        Behavior("Unjust to outgroup 3", "outgroup", {"C1": "violates", "C2": "violates"}),
        Behavior("Unjust to universal 1", "universal", {"C1": "violates", "C2": "violates"}),
        Behavior("Unjust to universal 2", "universal", {"C1": "violates", "C2": "violates"}),
    ]
    result = analyze_consistency("Justice", constraints, behaviors)
    # consistency = 2/12 = 0.167, ingroup_rate = 1.0
    assert result.consistency_ratio < 0.3
    assert "REMOVE_MERGE_GATES" in result.cordyceps_flags


# ── Result structure ──────────────────────────────────────────────

def test_result_fields():
    result = example_consistent()
    assert hasattr(result, "claimed_tradition")
    assert hasattr(result, "constraints")
    assert hasattr(result, "behaviors")
    assert hasattr(result, "consistency_ratio")
    assert hasattr(result, "selective_score")
    assert hasattr(result, "ingroup_bias_ratio")
    assert hasattr(result, "rationalization_density")
    assert hasattr(result, "verdict")
    assert hasattr(result, "cordyceps_flags")
    assert hasattr(result, "details")
    assert "total_checks" in result.details
