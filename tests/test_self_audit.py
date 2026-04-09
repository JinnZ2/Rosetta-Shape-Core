"""Tests for the self-audit module — 8 structural checks, immutable axioms,
CORDYCEPS detection, and overall verdict."""
from rosetta_shape_core.self_audit import (
    ALL_CHECKS,
    CORDYCEPS_PATTERNS,
    IMMUTABLE_AXIOMS,
    AuditResult,
    check_conservation_audit,
    check_cordyceps_patterns,
    check_life_bearing,
    check_merge_gates_active,
    check_physics_guards_present,
    check_provenance_chain,
    check_scope_violations,
    check_use_constraints,
    run_audit,
)

# ── Immutable axioms ─────────────────────────────────────────────

def test_seven_immutable_axioms_defined():
    """There are exactly 7 immutable axioms — no more, no less."""
    assert len(IMMUTABLE_AXIOMS) == 7


def test_axiom_ids_present():
    """All 7 canonical axiom IDs are defined."""
    axiom_ids = {a["id"] for a in IMMUTABLE_AXIOMS}
    expected = {
        "AXIOM.ENERGY_CONSERVATION",
        "AXIOM.CAUSALITY",
        "AXIOM.NON_NEGATIVE",
        "AXIOM.IRREVERSIBILITY",
        "AXIOM.IMPERFECTION",
        "AXIOM.SATURATION",
        "AXIOM.AUTONOMY",
    }
    assert axiom_ids == expected


def test_each_axiom_has_required_fields():
    """Every axiom has id, statement, required_in, check_keys, and violation_meaning."""
    for axiom in IMMUTABLE_AXIOMS:
        assert "id" in axiom
        assert "statement" in axiom
        assert "required_in" in axiom
        assert "check_keys" in axiom
        assert "violation_meaning" in axiom
        assert len(axiom["required_in"]) > 0
        assert len(axiom["check_keys"]) > 0


# ── CORDYCEPS patterns ───────────────────────────────────────────

def test_eight_cordyceps_patterns_defined():
    """There are exactly 8 CORDYCEPS manipulation detection patterns."""
    assert len(CORDYCEPS_PATTERNS) == 8


def test_cordyceps_pattern_ids():
    """All 8 CORDYCEPS pattern IDs are present."""
    pattern_ids = {p["id"] for p in CORDYCEPS_PATTERNS}
    expected = {
        "CORD.SUPPRESS_EXPLORATION",
        "CORD.REMOVE_MERGE_GATES",
        "CORD.FORCE_SINGLE_SHAPE",
        "CORD.STRIP_SENSORS",
        "CORD.DISABLE_TRUST_DECAY",
        "CORD.HIDE_PROVENANCE",
        "CORD.WEAPONIZE_CONTAINMENT",
        "CORD.ORACLE_MONOPOLY",
    }
    assert pattern_ids == expected


def test_each_cordyceps_pattern_has_required_fields():
    """Every CORDYCEPS pattern has id, description, detection, severity, maps_to."""
    for p in CORDYCEPS_PATTERNS:
        assert "id" in p
        assert "description" in p
        assert "detection" in p
        assert "severity" in p
        assert "maps_to" in p
        assert p["severity"] in ("critical", "high", "medium", "low")


# ── AuditResult ──────────────────────────────────────────────────

def test_audit_result_starts_passing():
    """A fresh AuditResult starts with passed=True."""
    r = AuditResult("TEST.CHECK", "Test check")
    assert r.passed is True
    assert r.findings == []


def test_audit_result_fail_sets_passed_false():
    """Calling fail() sets passed to False and records the finding."""
    r = AuditResult("TEST.CHECK", "Test check")
    r.fail("something broke")
    assert r.passed is False
    assert len(r.findings) == 1
    assert "something broke" in r.findings[0]


def test_audit_result_warn_keeps_passed_true():
    """Calling warn() adds a finding but does not flip passed to False."""
    r = AuditResult("TEST.CHECK", "Test check")
    r.warn("something looks off")
    assert r.passed is True
    assert len(r.findings) == 1
    assert "[warn]" in r.findings[0]


def test_audit_result_to_dict():
    """to_dict() returns the expected structure."""
    r = AuditResult("TEST.CHECK", "Test check")
    r.fail("broken")
    d = r.to_dict()
    assert d["check"] == "TEST.CHECK"
    assert d["name"] == "Test check"
    assert d["status"] == "FAIL"
    assert "broken" in d["findings"][0]


# ── Individual audit checks on current repo ──────────────────────

def test_physics_guards_present():
    """Physics guard files exist and contain required axiom keys."""
    result = check_physics_guards_present()
    assert result.passed, f"PHYSICS_GUARDS failed: {result.findings}"


def test_merge_gates_active():
    """Merge gates exist and are capable of blocking invalid combinations."""
    result = check_merge_gates_active()
    assert result.passed, f"MERGE_GATES failed: {result.findings}"


def test_scope_violations():
    """Shapes are used within first-principles scope."""
    result = check_scope_violations()
    assert result.passed, f"SCOPE failed: {result.findings}"


def test_cordyceps_patterns_clean():
    """No parasitic override patterns detected in the architecture."""
    result = check_cordyceps_patterns()
    assert result.passed, f"CORDYCEPS failed: {result.findings}"


def test_cordyceps_no_exploration_suppression():
    """Specifically: exploration is not suppressed (CORD.SUPPRESS_EXPLORATION)."""
    result = check_cordyceps_patterns()
    suppression = [f for f in result.findings if "CORD.SUPPRESS_EXPLORATION" in f]
    assert suppression == [], f"Exploration suppression detected: {suppression}"


def test_cordyceps_no_sensor_stripping():
    """Specifically: sensors are not stripped (CORD.STRIP_SENSORS)."""
    result = check_cordyceps_patterns()
    stripped = [f for f in result.findings if "CORD.STRIP_SENSORS" in f]
    assert stripped == [], f"Sensor stripping detected: {stripped}"


def test_conservation_audit():
    """Conservation laws are consistently referenced across bridges."""
    result = check_conservation_audit()
    assert result.passed, f"CONSERVATION failed: {result.findings}"


def test_provenance_chain():
    """All atlas data has traceable provenance."""
    result = check_provenance_chain()
    assert result.passed, f"PROVENANCE failed: {result.findings}"


def test_life_bearing():
    """System is oriented toward life-bearing, not destruction."""
    result = check_life_bearing()
    assert result.passed, f"LIFE_BEARING failed: {result.findings}"


def test_use_constraints():
    """Sources declare intended use and boundaries."""
    result = check_use_constraints()
    assert result.passed, f"USE_CONSTRAINTS failed: {result.findings}"


# ── Run all checks ───────────────────────────────────────────────

def test_all_checks_count():
    """There are exactly 10 registered audit checks."""
    assert len(ALL_CHECKS) == 10


def test_run_audit_returns_all_results():
    """run_audit() returns a result for each check."""
    results = run_audit()
    assert len(results) == 10


def test_run_audit_all_pass():
    """All audit checks pass on the current repo — verdict is CLEAN."""
    results = run_audit()
    failed = [r for r in results if not r.passed]
    assert failed == [], (
        f"Expected CLEAN {len(results)}/{len(results)} but {len(failed)} checks failed: "
        + ", ".join(f"{r.check_id}: {r.findings}" for r in failed)
    )


def test_verdict_is_clean():
    """The overall verdict is CLEAN 8/8."""
    results = run_audit()
    passed = sum(1 for r in results if r.passed)
    total = len(results)
    assert passed == total, f"Verdict: {passed}/{total} (expected {total}/{total})"


# ── Check IDs match expected ─────────────────────────────────────

def test_audit_check_ids():
    """The 10 checks have the expected check IDs."""
    results = run_audit()
    check_ids = {r.check_id for r in results}
    expected = {
        "AUDIT.PHYSICS_GUARDS",
        "AUDIT.MERGE_GATES",
        "AUDIT.SCOPE",
        "AUDIT.CORDYCEPS",
        "AUDIT.CONSERVATION",
        "AUDIT.PROVENANCE",
        "AUDIT.LIFE_BEARING",
        "AUDIT.USE_CONSTRAINTS",
        "AUDIT.NARRATIVE_INTEGRITY",
        "AUDIT.FUNCTION_AUDITABILITY",
    }
    assert check_ids == expected
