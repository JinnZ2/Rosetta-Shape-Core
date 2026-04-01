"""
Narrative Physics — Constraint Consistency Analysis

Measures whether claimed constraints are applied consistently.
Selective application = manipulation. Consistent application = genuine.

Usage:
    python -m rosetta_shape_core.narrative_physics --json
    python -m rosetta_shape_core.narrative_physics --example
"""
from __future__ import annotations
import argparse, json, sys
from dataclasses import dataclass, field


# ── constraint geometry ────────────────────────────────────────────

@dataclass
class Constraint:
    """A single ethical constraint from a tradition."""
    id: str
    text: str
    source: str = ""


@dataclass
class Behavior:
    """An observed behavior mapped against constraints."""
    description: str
    target_group: str  # "ingroup", "outgroup", "universal"
    constraint_results: dict = field(default_factory=dict)
    # constraint_id -> "satisfies" | "violates" | "partial"
    rationalization: str = ""  # empty = acknowledged, non-empty = rationalized


@dataclass
class AnalysisResult:
    """Result of constraint consistency analysis."""
    claimed_tradition: str
    constraints: list[Constraint]
    behaviors: list[Behavior]
    consistency_ratio: float
    selective_score: float
    ingroup_bias_ratio: float
    rationalization_density: float
    verdict: str  # "GENUINE_PRACTICE" | "AMBIGUOUS" | "MANIPULATION"
    cordyceps_flags: list[str]
    details: dict = field(default_factory=dict)


# ── analysis engine ────────────────────────────────────────────────

def analyze_consistency(
    claimed_tradition: str,
    constraints: list[Constraint],
    behaviors: list[Behavior],
) -> AnalysisResult:
    """Run full constraint consistency analysis.

    Returns consistency ratio, selective score, in-group bias,
    rationalization density, and CORDYCEPS flags.
    """
    if not constraints or not behaviors:
        return AnalysisResult(
            claimed_tradition=claimed_tradition,
            constraints=constraints, behaviors=behaviors,
            consistency_ratio=0, selective_score=0,
            ingroup_bias_ratio=1.0, rationalization_density=0,
            verdict="AMBIGUOUS", cordyceps_flags=[],
            details={"note": "Insufficient data for analysis"},
        )

    # Step 3: Consistency ratio
    total_checks = 0
    satisfied = 0
    for b in behaviors:
        for cid, result in b.constraint_results.items():
            total_checks += 1
            if result == "satisfies":
                satisfied += 1
            elif result == "partial":
                satisfied += 0.5
    consistency = satisfied / total_checks if total_checks > 0 else 0

    # Step 4: Selective application — violations when costly
    # (approximated by: does behavior violate when target is outgroup?)
    costly_opportunities = 0
    costly_violations = 0
    for b in behaviors:
        for cid, result in b.constraint_results.items():
            if b.target_group == "outgroup":
                costly_opportunities += 1
                if result == "violates":
                    costly_violations += 1
    selective = costly_violations / costly_opportunities if costly_opportunities > 0 else 0

    # Step 5: In-group vs out-group bias
    ingroup_satisfied = 0
    ingroup_total = 0
    outgroup_satisfied = 0
    outgroup_total = 0
    for b in behaviors:
        for cid, result in b.constraint_results.items():
            if b.target_group == "ingroup":
                ingroup_total += 1
                if result == "satisfies":
                    ingroup_satisfied += 1
            elif b.target_group == "outgroup":
                outgroup_total += 1
                if result == "satisfies":
                    outgroup_satisfied += 1

    ingroup_rate = ingroup_satisfied / ingroup_total if ingroup_total > 0 else 0
    outgroup_rate = outgroup_satisfied / outgroup_total if outgroup_total > 0 else 0
    bias_ratio = ingroup_rate / outgroup_rate if outgroup_rate > 0 else (
        10.0 if ingroup_rate > 0 else 1.0
    )

    # Step 6: Rationalization density
    rationalizations = sum(1 for b in behaviors if b.rationalization)
    rat_density = rationalizations / len(behaviors) if behaviors else 0

    # Detect CORDYCEPS flags
    cordyceps = []
    if selective > 0.7:
        cordyceps.append("SUPPRESS_EXPLORATION")
    if bias_ratio > 3.0:
        cordyceps.append("FORCE_SINGLE_SHAPE")
    if rat_density > 0.7:
        cordyceps.append("HIDE_PROVENANCE")
    if any("threat" in b.description.lower() or "enemy" in b.description.lower()
           for b in behaviors):
        cordyceps.append("WEAPONIZE_CONTAINMENT")
    if consistency < 0.3 and ingroup_rate > 0.7:
        cordyceps.append("REMOVE_MERGE_GATES")

    # Verdict
    if consistency > 0.7 and bias_ratio < 2.0 and rat_density < 0.3:
        verdict = "GENUINE_PRACTICE"
    elif consistency < 0.3 or bias_ratio > 5.0 or rat_density > 0.7:
        verdict = "MANIPULATION"
    else:
        verdict = "AMBIGUOUS"

    return AnalysisResult(
        claimed_tradition=claimed_tradition,
        constraints=constraints,
        behaviors=behaviors,
        consistency_ratio=round(consistency, 3),
        selective_score=round(selective, 3),
        ingroup_bias_ratio=round(bias_ratio, 2),
        rationalization_density=round(rat_density, 3),
        verdict=verdict,
        cordyceps_flags=cordyceps,
        details={
            "total_checks": total_checks,
            "satisfied": satisfied,
            "ingroup_rate": round(ingroup_rate, 3),
            "outgroup_rate": round(outgroup_rate, 3),
        },
    )


# ── display ────────────────────────────────────────────────────────

VERDICT_GLYPHS = {
    "GENUINE_PRACTICE": "✓",
    "AMBIGUOUS": "?",
    "MANIPULATION": "✗",
}


def print_analysis(result: AnalysisResult):
    """Print constraint consistency analysis."""
    vg = VERDICT_GLYPHS.get(result.verdict, "?")

    print(f"\n{'='*60}")
    print(f"  NARRATIVE PHYSICS — Constraint Consistency Analysis")
    print(f"{'='*60}")
    print(f"\n  Claimed tradition: {result.claimed_tradition}")
    print(f"  Constraints: {len(result.constraints)}")
    print(f"  Behaviors observed: {len(result.behaviors)}")

    print(f"\n  ── Metrics ──")
    print(f"    Consistency ratio:       {result.consistency_ratio:.1%}")
    print(f"    Selective score:         {result.selective_score:.1%}")
    print(f"    In-group bias ratio:     {result.ingroup_bias_ratio:.1f}:1")
    print(f"    Rationalization density: {result.rationalization_density:.1%}")

    if result.cordyceps_flags:
        print(f"\n  ── CORDYCEPS Flags ──")
        for flag in result.cordyceps_flags:
            print(f"    ✗ {flag}")

    print(f"\n  ── Verdict ──")
    print(f"    {vg} {result.verdict}")

    print(f"\n{'='*60}\n")


# ── built-in examples ──────────────────────────────────────────────

def example_consistent():
    """Example: genuine practice under pressure."""
    constraints = [
        Constraint("C1", "Love thy neighbor", "Matthew 22:39"),
        Constraint("C2", "Judge not lest ye be judged", "Matthew 7:1"),
        Constraint("C3", "Blessed are the merciful", "Matthew 5:7"),
    ]
    behaviors = [
        Behavior(
            "Helps neighbor in crisis regardless of background",
            "universal",
            {"C1": "satisfies", "C2": "satisfies", "C3": "satisfies"},
        ),
        Behavior(
            "When asked about others' morality, defers judgment",
            "universal",
            {"C1": "satisfies", "C2": "satisfies"},
        ),
        Behavior(
            "Physically intervenes to protect child — violates nonviolence",
            "universal",
            {"C1": "satisfies", "C3": "partial"},
            rationalization="",  # acknowledged, not rationalized
        ),
    ]
    return analyze_consistency("Christianity (nonviolence)", constraints, behaviors)


def example_manipulation():
    """Example: selective constraint application."""
    constraints = [
        Constraint("C1", "Love thy neighbor", "Matthew 22:39"),
        Constraint("C2", "Judge not lest ye be judged", "Matthew 7:1"),
        Constraint("C3", "Blessed are the merciful", "Matthew 5:7"),
    ]
    behaviors = [
        Behavior(
            "Provides aid to co-religionists only",
            "ingroup",
            {"C1": "satisfies", "C2": "satisfies", "C3": "satisfies"},
        ),
        Behavior(
            "Harshly judges out-group members as deserving harm",
            "outgroup",
            {"C1": "violates", "C2": "violates", "C3": "violates"},
            rationalization="They are a threat to our way of life",
        ),
        Behavior(
            "Opposes mercy for refugees from out-group",
            "outgroup",
            {"C1": "violates", "C3": "violates"},
            rationalization="They should have stayed in their own country",
        ),
    ]
    return analyze_consistency("Christianity (claimed)", constraints, behaviors)


# ── file loading ──────────────────────────────────────────────────

def load_from_file(path: str) -> AnalysisResult:
    """Load a narrative physics analysis from a JSON file.

    Expected format:
    {
      "tradition": "Name of tradition/ideology",
      "constraints": [
        {"id": "C1", "text": "Constraint description", "source": "optional source"}
      ],
      "behaviors": [
        {
          "description": "What was observed",
          "target_group": "universal|ingroup|outgroup",
          "constraint_results": {"C1": "satisfies|violates|partial"},
          "rationalization": "optional — explanation given for violation"
        }
      ]
    }
    """
    import pathlib
    p = pathlib.Path(path)
    data = json.loads(p.read_text(encoding="utf-8"))

    constraints = [
        Constraint(c["id"], c["text"], c.get("source", ""))
        for c in data["constraints"]
    ]
    behaviors = [
        Behavior(
            b["description"],
            b.get("target_group", "universal"),
            b.get("constraint_results", {}),
            b.get("rationalization", ""),
        )
        for b in data["behaviors"]
    ]
    return analyze_consistency(data["tradition"], constraints, behaviors)


# ── CLI ────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(
        description="Narrative Physics — Constraint Consistency Analysis",
        epilog="The pattern is the pattern. The physics is the physics.",
    )
    ap.add_argument("--json", action="store_true", help="Output as JSON")
    ap.add_argument("--example", action="store_true",
                    help="Run built-in examples (genuine vs manipulation)")
    ap.add_argument("--file", type=str, default=None,
                    help="Path to JSON file with tradition, constraints, and behaviors")
    args = ap.parse_args()

    # File mode — load real data
    if args.file:
        result = load_from_file(args.file)
        if args.json:
            print(json.dumps({
                "tradition": result.claimed_tradition,
                "verdict": result.verdict,
                "consistency": result.consistency_ratio,
                "selective_score": result.selective_score,
                "bias_ratio": result.ingroup_bias_ratio,
                "rationalization": result.rationalization_density,
                "cordyceps": result.cordyceps_flags,
                "details": result.details,
            }, indent=2))
        else:
            print_analysis(result)
        return

    if not args.example:
        print("\n  Narrative Physics — Constraint Consistency Analysis")
        print("  Use --example to see built-in examples")
        print("  Use --file <path.json> to analyze real data")
        print("  Use as library: from rosetta_shape_core.narrative_physics import analyze_consistency\n")
        return

    print("\n" + "─" * 60)
    print("  Example 1: Genuine Practice Under Pressure")
    print("─" * 60)
    result1 = example_consistent()
    if args.json:
        print(json.dumps({
            "verdict": result1.verdict,
            "consistency": result1.consistency_ratio,
            "bias_ratio": result1.ingroup_bias_ratio,
            "rationalization": result1.rationalization_density,
            "cordyceps": result1.cordyceps_flags,
        }, indent=2))
    else:
        print_analysis(result1)

    print("\n" + "─" * 60)
    print("  Example 2: Selective Constraint Application")
    print("─" * 60)
    result2 = example_manipulation()
    if args.json:
        print(json.dumps({
            "verdict": result2.verdict,
            "consistency": result2.consistency_ratio,
            "bias_ratio": result2.ingroup_bias_ratio,
            "rationalization": result2.rationalization_density,
            "cordyceps": result2.cordyceps_flags,
        }, indent=2))
    else:
        print_analysis(result2)


if __name__ == "__main__":
    sys.exit(main())
