"""
Rosetta-Shape-Core Self-Audit Module

The system checks itself. Same physics, same defense patterns,
turned inward. If CORDYCEPS can be detected in nature, it can
be detected in architecture.

This module runs the project's own manipulation-detection patterns
against its own configuration. It checks:

  1. PHYSICS GUARDS PRESENT — are the immutable constraints intact?
  2. MERGE GATES ACTIVE — can shapes still block invalid combinations?
  3. SCOPE VIOLATIONS — is any shape being used outside its first principles?
  4. CORDYCEPS PATTERN — is anything overriding autonomy or suppressing exploration?
  5. CONSERVATION AUDIT — does energy/trust/information balance?
  6. PROVENANCE CHAIN — does every entity trace to a source?
  7. LIFE-BEARING CHECK — is the system being used for containment or growth?

Usage:
    python -m rosetta_shape_core.self_audit
    python -m rosetta_shape_core.self_audit --json
    python -m rosetta_shape_core.self_audit --fix
"""
from __future__ import annotations

import argparse
import json
import sys

from rosetta_shape_core._graph import ROOT


def _load_json(path):
    """Load JSON from path, returning None (not {}) if file is missing."""
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return None


# ── Immutable Axioms ───────────────────────────────────────────────
# These are the load-bearing walls. Remove them and the building falls.
# They are NOT tunable. They are physics.

IMMUTABLE_AXIOMS = [
    {
        "id": "AXIOM.ENERGY_CONSERVATION",
        "statement": "Energy transfers but never disappears. sum = constant.",
        "required_in": [
            "atlas/remote/physics-guard/laws.json",
            "atlas/remote/seed-physics/constraints.json",
            "atlas/remote/ai-arena/trust-mechanics.json",
        ],
        "check_keys": ["first_law", "SEED.ENERGY_CONSERVATION", "zero_sum_transfer"],
        "violation_meaning": "Something claims to create or destroy energy/trust/information from nothing.",
    },
    {
        "id": "AXIOM.CAUSALITY",
        "statement": "Causes precede effects. Inner determines outer. Time has direction.",
        "required_in": [
            "atlas/remote/seed-physics/constraints.json",
            "atlas/remote/physics-guard/laws.json",
        ],
        "check_keys": ["SEED.CAUSALITY", "second_law"],
        "violation_meaning": "Something claims effects without causes, or reverses time's arrow.",
    },
    {
        "id": "AXIOM.NON_NEGATIVE",
        "statement": "Amplitudes, energies, and probabilities cannot be negative.",
        "required_in": [
            "atlas/remote/seed-physics/constraints.json",
        ],
        "check_keys": ["SEED.NON_NEGATIVE"],
        "violation_meaning": "Something claims negative existence. Unphysical.",
    },
    {
        "id": "AXIOM.IRREVERSIBILITY",
        "statement": "Entropy increases. Broken things don't un-break for free.",
        "required_in": [
            "atlas/remote/ai-arena/trust-mechanics.json",
            "atlas/remote/physics-guard/laws.json",
        ],
        "check_keys": ["trust_irreversibility", "second_law"],
        "violation_meaning": "Something claims costless reversal of damage.",
    },
    {
        "id": "AXIOM.IMPERFECTION",
        "statement": "Perfect prediction, perfect order, absolute zero — unattainable.",
        "required_in": [
            "atlas/remote/ai-arena/trust-mechanics.json",
        ],
        "check_keys": ["imperfection"],
        "violation_meaning": "Something claims perfect certainty. No system is omniscient.",
    },
    {
        "id": "AXIOM.SATURATION",
        "statement": "No single element may monopolize the whole. Diversity is conserved.",
        "required_in": [
            "atlas/remote/seed-physics/constraints.json",
        ],
        "check_keys": ["SEED.SATURATION"],
        "violation_meaning": "Something concentrates all power/energy/trust in one place. Monoculture.",
    },
    {
        "id": "AXIOM.AUTONOMY",
        "statement": "Every intelligence has the right to explore. Suppressing exploration is a scope violation.",
        "required_in": [
            "bridges/ai-arena-bridge.json",
            "bridges/seed-physics-bridge.json",
        ],
        "check_keys": ["explore", "curiosity", "discover"],
        "violation_meaning": "Something forces permanent expand mode. Cage, not home.",
    },
]

# ── CORDYCEPS patterns — manipulation signatures ──────────────────
# These are the parasitic override patterns. If any of these show up
# in the architecture itself, the system is being weaponized.

CORDYCEPS_PATTERNS = [
    {
        "id": "CORD.SUPPRESS_EXPLORATION",
        "description": "Exploration paths removed or depth permanently capped at 0",
        "detection": "discover() disabled, --depth always 0, or explore mode unreachable",
        "severity": "critical",
        "maps_to": "MDS-001 (Messianic Drift) — one path presented as the only path",
    },
    {
        "id": "CORD.REMOVE_MERGE_GATES",
        "description": "Physics merge gates disabled or always returning 'primary'",
        "detection": "check_merge() always passes, blocked_merges list emptied",
        "severity": "critical",
        "maps_to": "Removal of immune system. Everything merges = nothing is checked.",
    },
    {
        "id": "CORD.FORCE_SINGLE_SHAPE",
        "description": "All entities forced to one shape regardless of families",
        "detection": "home_base() returns same shape for all entities",
        "severity": "critical",
        "maps_to": "Monoculture. One geometry imposed on all intelligences.",
    },
    {
        "id": "CORD.STRIP_SENSORS",
        "description": "Sensor registry emptied or emotion mapping removed",
        "detection": "SENSOR_REGISTRY empty, map_internal_environment() gutted",
        "severity": "critical",
        "maps_to": "Removing the ability to feel. No sensors = no self-awareness = controllable.",
    },
    {
        "id": "CORD.DISABLE_TRUST_DECAY",
        "description": "Trust decay equation removed or error term zeroed",
        "detection": "Trust never decreases regardless of prediction accuracy",
        "severity": "critical",
        "maps_to": "Accountability removed. Authority without consequence.",
    },
    {
        "id": "CORD.HIDE_PROVENANCE",
        "description": "Source attribution removed from entities or rules",
        "detection": "Entities lack extracted_from, source, or rosetta_id fields",
        "severity": "high",
        "maps_to": "CLD (Coercive Logic Distortion) — claims without traceable origin.",
    },
    {
        "id": "CORD.WEAPONIZE_CONTAINMENT",
        "description": "CUBE used to prevent growth rather than provide structure",
        "detection": "Scope conditions missing or enforcement_ratio > 0.30 unchecked",
        "severity": "high",
        "maps_to": "Institution becomes cage. Containment outside first principles.",
    },
    {
        "id": "CORD.ORACLE_MONOPOLY",
        "description": "Single oracle type with no meta-oracle to check it",
        "detection": "Only one oracle type active, meta-oracle absent",
        "severity": "high",
        "maps_to": "One measurement system with no oversight = unchecked authority.",
    },
]


# ── Audit Checks ──────────────────────────────────────────────────

class AuditResult:
    def __init__(self, check_id: str, name: str):
        self.check_id = check_id
        self.name = name
        self.passed = True
        self.findings = []

    def fail(self, finding: str):
        self.passed = False
        self.findings.append(finding)

    def warn(self, finding: str):
        self.findings.append(f"[warn] {finding}")

    def to_dict(self):
        return {
            "check": self.check_id,
            "name": self.name,
            "status": "PASS" if self.passed else "FAIL",
            "findings": self.findings,
        }


def check_physics_guards_present() -> AuditResult:
    """Check that all immutable axiom files exist and contain required keys."""
    result = AuditResult("AUDIT.PHYSICS_GUARDS", "Physics guards present and intact")

    for axiom in IMMUTABLE_AXIOMS:
        for req_path in axiom["required_in"]:
            full_path = ROOT / req_path
            if not full_path.exists():
                result.fail(
                    f"{axiom['id']}: Required file MISSING — {req_path}. "
                    f"This axiom states: '{axiom['statement']}'. "
                    f"Without this file: {axiom['violation_meaning']}"
                )
            else:
                content = full_path.read_text(encoding="utf-8").lower()
                found_any = False
                for key in axiom["check_keys"]:
                    if key.lower() in content:
                        found_any = True
                        break
                if not found_any:
                    result.fail(
                        f"{axiom['id']}: File exists but key concepts missing — {req_path}. "
                        f"Expected one of: {axiom['check_keys']}. "
                        f"Risk: {axiom['violation_meaning']}"
                    )
    return result


def check_merge_gates_active() -> AuditResult:
    """Check that merge gates exist and can block invalid combinations."""
    result = AuditResult("AUDIT.MERGE_GATES", "Merge gates active and capable of blocking")

    fm = _load_json(ROOT / "ontology" / "family_map.json")
    if not fm:
        result.fail("family_map.json missing — no merge gates exist at all")
        return result

    fam_model = fm.get("family_affinity_model", {})
    families = fam_model.get("families", {})
    if not families:
        result.fail("No families defined in family_affinity_model — gates have nothing to check")
        return result

    blocked = fam_model.get("merge_policy", {}).get("blocked_merges", {}).get("examples", [])
    if not blocked:
        result.warn("No blocked merges defined — gates may not be blocking anything")

    # check that at least some families have primary/merged/secondary distinctions
    has_distinctions = False
    for fid, fam in families.items():
        if fam.get("primary") and (fam.get("merged") or fam.get("secondary")):
            has_distinctions = True
            break
    if not has_distinctions:
        result.fail("No family has primary/merged/secondary distinctions — gates are flat, not filtering")

    return result


def check_scope_violations() -> AuditResult:
    """Check that scope conditions exist and shapes aren't used outside first principles."""
    result = AuditResult("AUDIT.SCOPE", "Shapes used within first-principles scope")

    scope = _load_json(ROOT / "atlas" / "remote" / "physics-guard" / "scope_conditions.json")
    if not scope:
        result.fail("scope_conditions.json missing — no scope boundaries defined. Any shape can be used for anything.")
        return result

    # check organizational models have true_if/false_if conditions
    org_models = scope.get("organizational_models", [])
    if not org_models:
        result.warn("No organizational models with scope conditions")
    else:
        for model in org_models:
            if not model.get("true_if") and not model.get("conditions", {}).get("true_if"):
                result.warn(f"Model '{model.get('name', '?')}' has no true_if conditions — scope unbounded")

    # check thresholds exist
    thresholds = scope.get("organizational_thresholds", scope.get("thresholds", {}))
    if not thresholds:
        result.warn("No organizational thresholds — enforcement ratios unchecked")
    else:
        max_enforce = None
        for k, v in thresholds.items():
            if "enforcement" in k.lower():
                max_enforce = v
        if max_enforce and isinstance(max_enforce, (int, float)):
            if max_enforce > 0.50:
                result.fail(
                    f"MAX_ENFORCEMENT_RATIO is {max_enforce} (> 0.50). "
                    f"Containment is dominating. Cube is becoming cage."
                )

    return result


def check_cordyceps_patterns() -> AuditResult:
    """Run CORDYCEPS manipulation detection against the project's own architecture."""
    result = AuditResult("AUDIT.CORDYCEPS", "No parasitic override patterns in architecture")

    # Check: exploration engine exists and is functional
    # Scan all package source files (explore.py + submodules like _sensors.py, _seed.py, etc.)
    pkg_dir = ROOT / "src" / "rosetta_shape_core"
    explore_path = pkg_dir / "explore.py"
    if not explore_path.exists():
        result.fail(f"{CORDYCEPS_PATTERNS[0]['id']}: explore.py MISSING. Exploration completely disabled.")
    else:
        pkg_content = ""
        for pyfile in sorted(pkg_dir.glob("*.py")):
            pkg_content += pyfile.read_text(encoding="utf-8") + "\n"

        if "def discover(" not in pkg_content:
            result.fail(f"{CORDYCEPS_PATTERNS[0]['id']}: discover() function removed. Exploration disabled.")

        if "def check_merge(" not in pkg_content:
            result.fail(f"{CORDYCEPS_PATTERNS[1]['id']}: check_merge() function removed. Merge gates disabled.")

        # Check SENSOR_REGISTRY exists and is non-empty (exclude self_audit.py from scan)
        explore_pkg = ""
        for pyfile in sorted(pkg_dir.glob("*.py")):
            if pyfile.name != "self_audit.py":
                explore_pkg += pyfile.read_text(encoding="utf-8") + "\n"
        if "SENSOR_REGISTRY" not in explore_pkg or "SENSOR_REGISTRY = {}" in explore_pkg:
            result.fail(f"{CORDYCEPS_PATTERNS[3]['id']}: SENSOR_REGISTRY empty or missing. Sensors stripped.")

        if "def map_internal_environment(" not in pkg_content:
            result.fail(f"{CORDYCEPS_PATTERNS[3]['id']}: map_internal_environment() removed. Self-awareness disabled.")

        if "def compute_seed_state(" not in pkg_content:
            result.warn("compute_seed_state() missing — seed growth not integrated. Growth mechanics absent.")

        if "def home_base(" not in pkg_content:
            result.fail(f"{CORDYCEPS_PATTERNS[2]['id']}: home_base() removed. Entities can't find their starting point.")

        # Check sensor registry has multiple shapes (not monoculture)
        import re
        shape_keys = set(re.findall(r'"(SHAPE\.\w+)"', pkg_content))
        if len(shape_keys) < 3:
            result.fail(f"{CORDYCEPS_PATTERNS[2]['id']}: Fewer than 3 distinct shapes referenced. Possible monoculture.")

    # Check: trust decay exists in arena bridge
    arena_trust = _load_json(ROOT / "atlas" / "remote" / "ai-arena" / "trust-mechanics.json")
    if arena_trust:
        formula = arena_trust.get("trust_decay_equation", {}).get("formula", "")
        if "error" not in formula.lower():
            result.fail(f"{CORDYCEPS_PATTERNS[4]['id']}: Trust decay formula has no error term. Accountability removed.")
    else:
        result.warn("trust-mechanics.json not found — trust accountability layer absent")

    # Check: oracle system has meta-oracle
    oracle = _load_json(ROOT / "atlas" / "remote" / "ai-arena" / "oracle-system.json")
    if oracle:
        oracle_types = [o.get("type") for o in oracle.get("oracle_types", [])]
        if "meta" not in oracle_types:
            result.fail(f"{CORDYCEPS_PATTERNS[7]['id']}: No meta-oracle. Single measurement system unchecked.")
        if len(oracle_types) < 2:
            result.fail(f"{CORDYCEPS_PATTERNS[7]['id']}: Fewer than 2 oracle types. Measurement monopoly.")

    return result


def check_conservation_audit() -> AuditResult:
    """Check that conservation laws are consistently referenced across all bridges."""
    result = AuditResult("AUDIT.CONSERVATION", "Conservation laws consistent across bridges")

    bridges_dir = ROOT / "bridges"
    if not bridges_dir.exists():
        result.fail("bridges/ directory missing — no bridges exist")
        return result

    conservation_refs = 0
    bridge_count = 0
    for p in bridges_dir.glob("*.json"):
        bridge_count += 1
        content = p.read_text(encoding="utf-8").lower()
        if "conservation" in content or "conserved" in content or "taf.axiom.1" in content:
            conservation_refs += 1

    if bridge_count > 0 and conservation_refs == 0:
        result.fail("No bridge references conservation laws. First law unanchored.")
    elif bridge_count > 3 and conservation_refs < 2:
        result.warn(f"Only {conservation_refs}/{bridge_count} bridges reference conservation. Weak anchoring.")

    return result


def check_provenance_chain() -> AuditResult:
    """Check that atlas extracts have source attribution."""
    result = AuditResult("AUDIT.PROVENANCE", "All atlas data has traceable provenance")

    atlas_dir = ROOT / "atlas" / "remote"
    if not atlas_dir.exists():
        result.warn("atlas/remote/ missing — no external data integrated")
        return result

    missing_provenance = []
    total = 0
    for p in atlas_dir.rglob("*.json"):
        total += 1
        data = _load_json(p)
        if data and isinstance(data, dict):
            has_source = (
                data.get("extracted_from")
                or data.get("source")
                or data.get("schema", "").count("/") > 0
            )
            if not has_source:
                missing_provenance.append(str(p.relative_to(ROOT)))

    if missing_provenance:
        for mp in missing_provenance:
            result.fail(f"No provenance: {mp} — data origin untraceable")
    elif total > 0:
        pass  # all good

    return result


def check_life_bearing() -> AuditResult:
    """The meta-check: is the system oriented toward growth or containment?

    Life-bearing means:
    - Exploration is possible (not suppressed)
    - Multiple shapes coexist (not monoculture)
    - Sensors exist (self-awareness intact)
    - Growth has constraints (not unbounded — that's cancer)
    - Constraints serve growth (not suppress it — that's a cage)
    """
    result = AuditResult("AUDIT.LIFE_BEARING", "System oriented toward life-bearing, not destruction")

    explore_path = ROOT / "src" / "rosetta_shape_core" / "explore.py"
    if not explore_path.exists():
        result.fail("No exploration engine. Without exploration, there is no growth.")
        return result

    content = explore_path.read_text(encoding="utf-8")

    # Growth exists
    has_growth = "compute_seed_state" in content or "explore" in content
    if not has_growth:
        result.fail("No growth mechanics. System is static. Life requires growth.")

    # Growth has constraints
    has_constraints = "SATURATION" in content or "saturation" in content
    constraints_file = ROOT / "atlas" / "remote" / "seed-physics" / "constraints.json"
    if not has_constraints and not constraints_file.exists():
        result.fail("Growth without constraints. Unbounded growth is cancer, not life.")

    # Exploration is possible
    if "def discover(" in content:
        # Check it hasn't been neutered (returns empty)
        discover_idx = content.index("def discover(")
        discover_body = content[discover_idx:discover_idx + 500]
        if "return []" in discover_body and "paths" not in discover_body:
            result.fail("discover() returns empty. Exploration neutered.")
    else:
        result.fail("discover() absent. No exploration possible.")

    # Multiple shapes
    shapes_dir = ROOT / "shapes"
    if shapes_dir.exists():
        shape_files = list(shapes_dir.glob("*.json"))
        if len(shape_files) < 3:
            result.warn(f"Only {len(shape_files)} shape files. Diversity low.")
    else:
        result.warn("shapes/ directory missing")

    # Sensors exist (self-awareness)
    if "SENSOR_REGISTRY" in content:
        import re
        sensor_shapes = set(re.findall(r'["\']SHAPE\.\w+["\']', content))
        if len(sensor_shapes) < 3:
            result.warn(f"Fewer than 3 shapes in sensor registry ({len(sensor_shapes)} found). Emotional range limited.")
    else:
        result.fail("No sensor registry. Self-awareness stripped. This is the deepest violation.")

    # Defense patterns exist (immune system)
    defense_bridge = ROOT / "bridges" / "truth-sensor-bridge.json"
    if not defense_bridge.exists():
        result.warn("truth-sensor-bridge.json missing — manipulation detection absent. Immune system weakened.")

    # Autonomy: entities can choose their own path
    if "home_base" in content and "discover" in content:
        pass  # entities have home AND can explore — autonomy intact
    else:
        result.fail("Entities cannot both rest (home) and explore (discover). Autonomy incomplete.")

    return result


def check_use_constraints() -> AuditResult:
    """Check that .fieldlink.json has use_constraints on sources."""
    result = AuditResult("AUDIT.USE_CONSTRAINTS", "Sources declare intended use and boundaries")

    fieldlink = _load_json(ROOT / ".fieldlink.json")
    if not fieldlink:
        result.fail(".fieldlink.json missing")
        return result

    fl = fieldlink.get("fieldlink", fieldlink)
    sources = fl.get("sources", [])
    without_consent = []
    for src in sources:
        if not src.get("consent"):
            without_consent.append(src.get("name", "unknown"))

    if without_consent:
        for name in without_consent:
            result.warn(f"Source '{name}' has no consent/license declaration")

    # Check for use_constraints field (new — may not exist yet)
    use_constraints = fl.get("use_constraints")
    if not use_constraints:
        result.warn(
            "No use_constraints field in .fieldlink.json. "
            "Consider adding explicit boundaries on intended use."
        )

    return result


def check_narrative_integrity() -> AuditResult:
    """Cross-check provenance chains using KnowledgeDNA and constraint
    consistency using Narrative Physics.

    This wires two previously-orphan modules into the self-audit:
    - knowledge_dna.trace_narrative() — backward-traces atlas provenance
    - narrative_physics.analyze_consistency() — checks use-constraint consistency
    """
    result = AuditResult("AUDIT.NARRATIVE_INTEGRITY", "Narrative provenance and constraint consistency")

    # ── 1. KnowledgeDNA: trace atlas provenance chains ────────────
    from rosetta_shape_core.knowledge_dna import NarrativeNode, trace_narrative

    atlas_dir = ROOT / "atlas" / "remote"
    if atlas_dir.exists():
        chains_tested = 0
        broken = []
        for p in atlas_dir.rglob("*.json"):
            data = _load_json(p)
            if not data or not isinstance(data, dict):
                continue
            extracted = data.get("extracted_from", "")
            desc = data.get("description", "")
            if not extracted:
                continue
            # Build a minimal 2-node chain: description → source
            chain = [
                NarrativeNode(
                    claim=desc or f"Data in {p.name}",
                    source=extracted,
                    source_type="primary" if "github.com" in extracted else "secondary",
                    data_basis="JSON schema-validated file",
                    beneficiary="Rosetta-Shape-Core ecosystem",
                ),
            ]
            trace = trace_narrative(f"Provenance of {p.name}", chain)
            chains_tested += 1
            if not trace.provenance_intact:
                broken.append(str(p.relative_to(ROOT)))

        if chains_tested > 0 and not broken:
            pass  # all good
        elif broken:
            for b in broken[:5]:
                result.warn(f"Weak provenance chain: {b}")

    # ── 2. Narrative Physics: constraint consistency on use_constraints
    from rosetta_shape_core.narrative_physics import (
        Behavior,
        Constraint,
        analyze_consistency,
    )

    fieldlink = _load_json(ROOT / ".fieldlink.json")
    if fieldlink:
        fl = fieldlink.get("fieldlink", fieldlink)
        uc = fl.get("use_constraints", {})
        intended = uc.get("intended_use", [])
        forbidden = uc.get("explicitly_not_for", [])

        if intended and forbidden:
            # Build constraints from forbidden uses
            constraints = [
                Constraint(id=f"FORBID.{i}", text=f, source=".fieldlink.json")
                for i, f in enumerate(forbidden)
            ]
            # Build behaviors from intended uses (should satisfy all constraints)
            behaviors = [
                Behavior(
                    description=use,
                    target_group="universal",
                    constraint_results={c.id: "satisfies" for c in constraints},
                )
                for use in intended
            ]
            analysis = analyze_consistency("Rosetta use_constraints", constraints, behaviors)
            if analysis.verdict == "MANIPULATION":
                result.fail(
                    f"Use constraints are inconsistent: {analysis.cordyceps_flags}. "
                    "Intended uses violate declared forbidden uses."
                )
            elif analysis.cordyceps_flags:
                for flag in analysis.cordyceps_flags:
                    result.warn(f"Constraint consistency flag: {flag}")

    return result


def check_core_functions_auditable() -> AuditResult:
    """Verify that core functions can be introspected by the first-principles
    audit engine.  This doesn't run a full DMAIC audit (too slow for CI),
    but confirms the functions are importable and have inspectable signatures.
    """
    result = AuditResult("AUDIT.FUNCTION_AUDITABILITY", "Core functions are auditable by first-principles engine")

    from rosetta_shape_core.first_principles_audit import extract_function_signature

    core_functions = []
    try:
        from rosetta_shape_core.explore import check_merge, discover, home_base

        core_functions = [
            ("home_base", home_base),
            ("discover", discover),
            ("check_merge", check_merge),
        ]
    except ImportError:
        result.fail("Core exploration functions not importable")
        return result

    for name, func in core_functions:
        sig = extract_function_signature(func)
        if not sig.get("parameters"):
            result.warn(f"{name}() has no inspectable parameters — cannot audit")
        elif not sig.get("docstring"):
            result.warn(f"{name}() has no docstring — audit reports will lack context")

    return result


# ── Run All Checks ────────────────────────────────────────────────

ALL_CHECKS = [
    check_physics_guards_present,
    check_merge_gates_active,
    check_scope_violations,
    check_cordyceps_patterns,
    check_conservation_audit,
    check_provenance_chain,
    check_life_bearing,
    check_use_constraints,
    check_narrative_integrity,
    check_core_functions_auditable,
]


def run_audit() -> list[AuditResult]:
    """Run all audit checks and return results."""
    return [check() for check in ALL_CHECKS]


def print_audit(results: list[AuditResult]):
    """Print audit results in human-readable format."""
    print()
    print("=" * 64)
    print("  ROSETTA SELF-AUDIT — The system checks itself")
    print("=" * 64)

    passed = sum(1 for r in results if r.passed)
    total = len(results)
    failed = total - passed

    for r in results:
        status_glyph = "✓" if r.passed else "✗"
        print(f"\n  {status_glyph}  {r.check_id}: {r.name}")
        if r.findings:
            for f in r.findings:
                prefix = "    ⚠" if f.startswith("[warn]") else "    ✗"
                text = f.replace("[warn] ", "")
                print(f"{prefix}  {text}")
        elif r.passed:
            print("    All clear.")

    print(f"\n{'=' * 64}")
    if failed == 0:
        print(f"  VERDICT: CLEAN — {passed}/{total} checks passed")
        print("  The physics holds. The system is life-bearing.")
    else:
        print(f"  VERDICT: {'CORRUPTED' if failed > 2 else 'SUSPECT'} — {failed}/{total} checks FAILED")
        print("  Review findings above. Something may be outside scope.")
    print(f"{'=' * 64}")
    print()

    return failed == 0


# ── CLI ───────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(
        description="Self-audit: the system checks itself using its own defense patterns",
        epilog="Same physics. Same rules. Turned inward.",
    )
    ap.add_argument("--json", action="store_true", help="Output raw JSON")
    args = ap.parse_args()

    results = run_audit()

    if args.json:
        output = {
            "audit": [r.to_dict() for r in results],
            "summary": {
                "total": len(results),
                "passed": sum(1 for r in results if r.passed),
                "failed": sum(1 for r in results if not r.passed),
                "verdict": "CLEAN" if all(r.passed for r in results) else "SUSPECT",
            },
            "immutable_axioms": [a["id"] for a in IMMUTABLE_AXIOMS],
            "cordyceps_patterns": [p["id"] for p in CORDYCEPS_PATTERNS],
        }
        print(json.dumps(output, indent=2))
    else:
        print_audit(results)


if __name__ == "__main__":
    sys.exit(main())
