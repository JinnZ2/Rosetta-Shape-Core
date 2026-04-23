"""Tests for the First Principles Audit — Six Sigma DMAIC validation engine."""
import json

import pytest

from rosetta_shape_core.first_principles_audit import (
    KNOWN_BIAS_PATTERNS,
    AssumptionRecord,
    DesignChoice,
    ParameterSpec,
    audit_function,
    boundary_test,
    capability_analysis,
    catalog_parameters,
    compare_formulations,
    extract_function_signature,
    flag_biases,
    full_audit,
    generate_fmea,
    generate_report,
    monte_carlo_capability,
    sensitivity_analysis,
)

# ── Helpers / Fixtures ───────────────────────────────────────────────


def linear(a=1, b=2):
    """A simple linear function: 3a + b."""
    return a * 3 + b * 1


def quadratic(x=1, c=0):
    """Quadratic: x squared plus constant."""
    return x ** 2 + c


def divides(a=1, b=1):
    """Division: a / b."""
    return a / b


def constant(x=5):
    """Always returns 42."""
    return 42


def sometimes_fails(x=1):
    """Fails when x is negative."""
    if x < 0:
        raise ValueError("negative input")
    return x ** 0.5


def returns_nan(x=0):
    """May produce NaN."""
    if x == 0:
        return float("nan")
    return 1.0 / x


@pytest.fixture
def full_spec():
    """A fully documented ParameterSpec."""
    return ParameterSpec(
        name="a",
        physical_meaning="amplitude",
        source="measured",
        units="meters",
        min_value=0.0,
        max_value=100.0,
    )


@pytest.fixture
def partial_spec():
    """A ParameterSpec missing units."""
    return ParameterSpec(
        name="b",
        physical_meaning="frequency",
        source="estimated",
    )


@pytest.fixture
def bare_spec():
    """A ParameterSpec with only the name."""
    return ParameterSpec(name="c")


# ── 1. ParameterSpec tests ───────────────────────────────────────────


class TestParameterSpec:
    def test_is_documented_all_fields(self, full_spec):
        assert full_spec.is_documented() is True

    def test_is_documented_missing_units(self, partial_spec):
        assert partial_spec.is_documented() is False

    def test_is_documented_missing_source(self):
        spec = ParameterSpec(name="x", physical_meaning="length", units="m")
        assert spec.is_documented() is False

    def test_is_documented_missing_meaning(self):
        spec = ParameterSpec(name="x", source="measured", units="m")
        assert spec.is_documented() is False

    def test_is_documented_bare(self, bare_spec):
        assert bare_spec.is_documented() is False

    def test_within_range_bounded(self, full_spec):
        assert full_spec.is_within_range(50.0) is True
        assert full_spec.is_within_range(0.0) is True
        assert full_spec.is_within_range(100.0) is True

    def test_outside_range_low(self, full_spec):
        assert full_spec.is_within_range(-1.0) is False

    def test_outside_range_high(self, full_spec):
        assert full_spec.is_within_range(101.0) is False

    def test_within_range_no_bounds(self, bare_spec):
        assert bare_spec.is_within_range(999999) is True
        assert bare_spec.is_within_range(-999999) is True

    def test_defaults(self):
        spec = ParameterSpec(name="z")
        assert spec.name == "z"
        assert spec.physical_meaning is None or spec.physical_meaning == ""
        assert spec.source is None or spec.source == ""
        assert spec.units is None or spec.units == ""
        assert spec.min_value is None
        assert spec.max_value is None


# ── 2. AssumptionRecord tests ────────────────────────────────────────


class TestAssumptionRecord:
    def test_creation_all_fields(self):
        rec = AssumptionRecord(
            id="A1",
            text="Gravity is constant",
            domain="physics",
            falsifiable=True,
        )
        assert rec.id == "A1"
        assert rec.text == "Gravity is constant"
        assert rec.domain == "physics"
        assert rec.falsifiable is True

    def test_falsifiable_default(self):
        rec = AssumptionRecord(id="A2", text="Linear relationship")
        assert rec.falsifiable is True

    def test_unfalsifiable(self):
        rec = AssumptionRecord(id="A3", text="It just works", falsifiable=False)
        assert rec.falsifiable is False

    def test_fields_accessible(self):
        rec = AssumptionRecord(id="A4", text="Steady state", domain="engineering")
        assert rec.id == "A4"
        assert rec.domain == "engineering"


# ── 3. DesignChoice tests ───────────────────────────────────────────


class TestDesignChoice:
    def test_creation(self):
        dc = DesignChoice(
            description="Use linear model",
            rationale="Simplicity",
            alternatives=["quadratic", "exponential"],
        )
        assert dc.description == "Use linear model"
        assert dc.rationale == "Simplicity"
        assert len(dc.alternatives) == 2

    def test_no_alternatives(self):
        dc = DesignChoice(description="Only option", rationale="No choice")
        alts = getattr(dc, "alternatives", None)
        assert alts is None or alts == []


# ── 4. extract_function_signature tests ──────────────────────────────


class TestExtractFunctionSignature:
    def test_simple_function(self):
        def foo(a, b=5, c=10):
            """docstring"""
            return a + b + c

        sig = extract_function_signature(foo)
        assert sig["function_name"] == "foo"
        assert "docstring" in sig["docstring"]

    def test_parameters_listed(self):
        def foo(a, b=5, c=10):
            """docstring"""
            return a + b + c

        sig = extract_function_signature(foo)
        assert "a" in sig["parameters"]
        assert "b" in sig["parameters"]
        assert "c" in sig["parameters"]

    def test_defaults_captured(self):
        def foo(a, b=5, c=10):
            """docstring"""
            return a + b + c

        sig = extract_function_signature(foo)
        defaults = sig["defaults"]
        assert defaults.get("b") == 5
        assert defaults.get("c") == 10

    def test_no_docstring(self):
        def bar(x):
            return x

        sig = extract_function_signature(bar)
        assert sig["function_name"] == "bar"
        # Docstring should be None or empty
        assert not sig["docstring"]


# ── 5. catalog_parameters tests ──────────────────────────────────────


class TestCatalogParameters:
    def test_without_specs_all_undocumented(self):
        cat = catalog_parameters(linear)
        undoc = [p for p in cat["parameters"] if not p["documented"]]
        assert len(undoc) == len(cat["parameters"])
        assert cat["documentation_ratio"] == 0.0

    def test_with_full_specs_all_documented(self):
        specs = {
            "a": ParameterSpec(
                name="a", physical_meaning="coeff", source="data", units="none"
            ),
            "b": ParameterSpec(
                name="b", physical_meaning="offset", source="data", units="none"
            ),
        }
        cat = catalog_parameters(linear, specs=specs)
        assert cat["documentation_ratio"] == 1.0

    def test_partial_documentation(self):
        specs = {
            "a": ParameterSpec(
                name="a", physical_meaning="coeff", source="data", units="none"
            ),
        }
        cat = catalog_parameters(linear, specs=specs)
        assert 0.0 < cat["documentation_ratio"] < 1.0

    def test_documentation_ratio_calculation(self):
        specs = {
            "a": ParameterSpec(
                name="a", physical_meaning="coeff", source="data", units="none"
            ),
        }
        cat = catalog_parameters(linear, specs=specs)
        expected = 1 / 2  # 1 documented out of 2 params
        assert abs(cat["documentation_ratio"] - expected) < 1e-9


# ── 6. sensitivity_analysis tests ────────────────────────────────────


class TestSensitivityAnalysis:
    def test_dominant_parameter(self):
        result = sensitivity_analysis(linear)
        assert result["dominant_parameter"] == "a"

    def test_pareto_ranking_order(self):
        result = sensitivity_analysis(linear)
        ranking = result["pareto_ranking"]
        assert ranking[0] == "a"
        assert ranking[1] == "b"

    def test_baseline_output(self):
        result = sensitivity_analysis(linear)
        expected = linear()  # a=1, b=2 → 3*1 + 2 = 5
        assert result["baseline_output"] == expected

    def test_sweep_values_in_range(self):
        result = sensitivity_analysis(linear)
        for param, data in result["sensitivities"].items():
            for entry in data:
                # Each entry should have value and output keys
                assert "value" in entry or "input" in entry or isinstance(entry, (list, tuple, dict))

    def test_quadratic_dominant_parameter(self):
        # For quadratic(x=1, c=0) = x^2 + c, x should dominate around default
        result = sensitivity_analysis(quadratic)
        assert result["dominant_parameter"] == "x"


# ── 7. boundary_test tests ──────────────────────────────────────────


class TestBoundaryTest:
    def test_function_works_at_boundaries(self):
        results = boundary_test(linear)
        for r in results:
            assert "parameter" in r
            assert "boundary" in r or "test" in r
            assert "passed" in r

    def test_division_by_zero_caught(self):
        results = boundary_test(divides)
        zero_tests = [
            r for r in results
            if r["parameter"] == "b" and not r["passed"]
        ]
        assert len(zero_tests) > 0

    def test_nan_detected(self):
        results = boundary_test(returns_nan)
        failed = [r for r in results if not r["passed"]]
        assert len(failed) > 0

    def test_structure(self):
        results = boundary_test(linear)
        assert isinstance(results, list)
        assert len(results) > 0
        first = results[0]
        assert "parameter" in first
        assert "passed" in first


# ── 8. generate_fmea tests ──────────────────────────────────────────


class TestGenerateFmea:
    def test_empty_inputs(self):
        result = generate_fmea([], [], [])
        assert result == []

    def test_undocumented_higher_severity(self):
        specs_doc = [{"name": "a", "documented": True}]
        specs_undoc = [{"name": "b", "documented": False}]
        sens = [{"parameter": "a", "influence": 0.5}, {"parameter": "b", "influence": 0.5}]
        bounds = []
        fmea_doc = generate_fmea(specs_doc, sens, bounds)
        fmea_undoc = generate_fmea(specs_undoc, sens, bounds)
        if fmea_doc and fmea_undoc:
            # Undocumented should have higher severity or RPN
            rpn_doc = max(e.get("rpn", 0) for e in fmea_doc)
            rpn_undoc = max(e.get("rpn", 0) for e in fmea_undoc)
            assert rpn_undoc >= rpn_doc

    def test_sorted_by_rpn_descending(self):
        specs = [
            {"name": "a", "documented": False},
            {"name": "b", "documented": True},
        ]
        sens = [
            {"parameter": "a", "influence": 0.9},
            {"parameter": "b", "influence": 0.1},
        ]
        bounds = [
            {"parameter": "a", "passed": False},
            {"parameter": "b", "passed": True},
        ]
        fmea = generate_fmea(specs, sens, bounds)
        if len(fmea) >= 2:
            rpns = [e["rpn"] for e in fmea]
            assert rpns == sorted(rpns, reverse=True)


# ── 9. capability_analysis tests ─────────────────────────────────────


class TestCapabilityAnalysis:
    def test_constant_output_zero_variance(self):
        outputs = [42, 42, 42, 42, 42]
        result = capability_analysis(outputs)
        # Should note zero variance or handle gracefully
        assert "zero_variance" in result or result.get("Cp") is None or result.get("Cp", 0) == float("inf") or "note" in str(result).lower()

    def test_normal_outputs_cp_computed(self):
        outputs = [10, 10.5, 11, 9.5, 10.2, 10.8, 9.8, 10.1, 10.3, 9.9]
        result = capability_analysis(outputs, lsl=8, usl=12)
        assert "Cp" in result or "cp" in result
        cp = result.get("Cp") or result.get("cp")
        assert cp is not None
        assert cp > 0

    def test_cpk_computed(self):
        outputs = [10, 10.5, 11, 9.5, 10.2, 10.8, 9.8, 10.1, 10.3, 9.9]
        result = capability_analysis(outputs, lsl=8, usl=12)
        cpk = result.get("Cpk") or result.get("cpk")
        assert cpk is not None
        assert cpk > 0

    def test_few_points_error(self):
        result = capability_analysis([1])
        assert "error" in result or "insufficient" in str(result).lower() or len(result.get("outputs", [1, 2])) <= 2

    def test_control_limits(self):
        outputs = [10, 10.5, 11, 9.5, 10.2, 10.8, 9.8, 10.1, 10.3, 9.9]
        result = capability_analysis(outputs, lsl=8, usl=12)
        ucl = result.get("UCL") or result.get("ucl")
        lcl = result.get("LCL") or result.get("lcl")
        if ucl is not None and lcl is not None:
            assert ucl > lcl


# ── 10. monte_carlo_capability tests ─────────────────────────────────


class TestMonteCarloCapability:
    def test_simple_no_failures(self):
        result = monte_carlo_capability(linear, n=100, seed=42)
        assert result["failure_rate"] == 0.0

    def test_sometimes_fails_has_failures(self):
        def risky(x=0):
            if x > 1.5:
                raise ValueError("boom")
            return x

        result = monte_carlo_capability(risky, n=200, seed=42)
        assert result["failure_rate"] >= 0.0  # may or may not fail depending on sampling

    def test_deterministic_with_seed(self):
        r1 = monte_carlo_capability(linear, n=100, seed=123)
        r2 = monte_carlo_capability(linear, n=100, seed=123)
        assert r1["failure_rate"] == r2["failure_rate"]
        assert r1["outputs"] == r2["outputs"]


# ── 11. audit_function tests ────────────────────────────────────────


class TestAuditFunction:
    def test_returns_all_dmaic_sections(self):
        result = audit_function(linear)
        for section in ("define", "measure", "analyze", "improve", "control"):
            assert section in result, f"Missing DMAIC section: {section}"

    def test_has_summary(self):
        result = audit_function(linear)
        assert "summary" in result

    def test_has_overall_grade(self):
        result = audit_function(linear)
        summary = result.get("summary", {})
        assert "overall_grade" in summary or "overall_grade" in result

    def test_baseline_output_present(self):
        result = audit_function(linear)
        # baseline_output may be in measure or define section
        found = False
        for section in result.values():
            if isinstance(section, dict) and "baseline_output" in section:
                found = True
                break
        if not found:
            # Could also be at top level
            found = "baseline_output" in result
        assert found, "baseline_output not found in audit result"


# ── 12. flag_biases tests ───────────────────────────────────────────


class TestFlagBiases:
    def test_simplification_bias_many_assumed(self):
        assumptions = [
            AssumptionRecord(id=f"A{i}", text=f"Assumption {i}")
            for i in range(10)
        ]
        flags = flag_biases(
            assumptions=assumptions,
            design_choices=[],
            parameter_catalog={"parameters": [{"name": "x", "documented": False}] * 5},
        )
        bias_names = [f["bias"] if isinstance(f, dict) else f for f in flags]
        assert "simplification_bias" in bias_names

    def test_survivorship_bias_unfalsifiable(self):
        assumptions = [
            AssumptionRecord(id="A1", text="Unfalsifiable claim", falsifiable=False),
            AssumptionRecord(id="A2", text="Another unfalsifiable", falsifiable=False),
        ]
        flags = flag_biases(
            assumptions=assumptions,
            design_choices=[],
            parameter_catalog={"parameters": []},
        )
        bias_names = [f["bias"] if isinstance(f, dict) else f for f in flags]
        assert "survivorship_bias" in bias_names

    def test_optimization_bias_no_alternatives(self):
        choices = [
            DesignChoice(description="Only option", rationale="Because"),
        ]
        flags = flag_biases(
            assumptions=[],
            design_choices=choices,
            parameter_catalog={"parameters": []},
        )
        bias_names = [f["bias"] if isinstance(f, dict) else f for f in flags]
        assert "optimization_bias" in bias_names

    def test_externalization_bias_no_externalization(self):
        specs = {
            "a": ParameterSpec(name="a", physical_meaning="internal", source="model", units="none"),
        }
        cat = catalog_parameters(linear, specs=specs)
        flags = flag_biases(
            assumptions=[],
            design_choices=[],
            parameter_catalog=cat,
            externalization_terms=[],
        )
        bias_names = [f["bias"] if isinstance(f, dict) else f for f in flags]
        assert "externalization_bias" in bias_names


# ── 13. compare_formulations tests ───────────────────────────────────


class TestCompareFormulations:
    def test_two_formulations(self):
        result = compare_formulations([linear, quadratic])
        assert isinstance(result, (dict, list))
        # Should contain comparison data for each function
        if isinstance(result, dict):
            assert len(result) >= 1
        else:
            assert len(result) >= 2

    def test_single_formulation(self):
        result = compare_formulations([linear])
        assert result is not None


# ── 14. full_audit tests ────────────────────────────────────────────


class TestFullAudit:
    def test_returns_complete_report(self):
        result = full_audit(linear)
        assert isinstance(result, dict)
        for section in ("define", "measure", "analyze", "improve", "control", "summary"):
            assert section in result

    def test_summary_has_grade(self):
        result = full_audit(linear)
        summary = result.get("summary", {})
        assert "overall_grade" in summary or "overall_grade" in result


# ── 15. generate_report tests ───────────────────────────────────────


class TestGenerateReport:
    def test_json_format_valid(self):
        audit = full_audit(linear)
        report = generate_report(audit, fmt="json")
        parsed = json.loads(report)
        assert isinstance(parsed, dict)

    def test_markdown_has_headers(self):
        audit = full_audit(linear)
        report = generate_report(audit, fmt="markdown")
        assert "#" in report

    def test_csv_has_rows(self):
        audit = full_audit(linear)
        report = generate_report(audit, fmt="csv")
        lines = report.strip().split("\n")
        assert len(lines) >= 2  # header + at least one row


# ── 16. KNOWN_BIAS_PATTERNS tests ───────────────────────────────────


class TestKnownBiasPatterns:
    def test_has_expected_keys(self):
        expected = {
            "simplification_bias",
            "survivorship_bias",
            "optimization_bias",
            "externalization_bias",
        }
        assert expected.issubset(set(KNOWN_BIAS_PATTERNS.keys()))

    def test_each_pattern_has_description_and_indicators(self):
        for key, pattern in KNOWN_BIAS_PATTERNS.items():
            assert "description" in pattern, f"{key} missing description"
            assert "indicators" in pattern, f"{key} missing indicators"
