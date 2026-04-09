"""
Six Sigma First-Principles Validation Engine

Run on any Python function to extract assumptions, test sensitivity,
identify failure modes, and generate accountability reports.

DMAIC Framework:
  Define   -> What does each parameter represent physically?
  Measure  -> What are the defaults, ranges, units?
  Analyze  -> Sensitivity analysis, Pareto of influence
  Improve  -> Boundary conditions, failure modes (FMEA)
  Control  -> Capability indices, control limits, verification tests

Output: JSON (machine-readable), Markdown (human-readable), CSV (spreadsheet)

Usage:
    from rosetta_shape_core.first_principles_audit import audit_function, full_audit, generate_report
    report = audit_function(my_function)
    generate_report(report, fmt="markdown")
"""
from __future__ import annotations

import csv
import inspect
import json
import math
import random as rng
from dataclasses import dataclass
from io import StringIO
from typing import Any, Callable, Dict, List, Optional, Tuple

# =========================================================================
# Data classes
# =========================================================================

@dataclass
class ParameterSpec:
    """Complete specification of a single parameter."""
    name: str
    physical_meaning: str = ""
    source: str = ""
    units: str = ""
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    uncertainty: Optional[float] = None
    notes: str = ""

    def is_documented(self) -> bool:
        return bool(self.physical_meaning and self.source and self.units)

    def is_within_range(self, value: float) -> bool:
        if self.min_value is not None and value < self.min_value:
            return False
        if self.max_value is not None and value > self.max_value:
            return False
        return True


@dataclass
class AssumptionRecord:
    """An explicit assumption made by the model."""
    id: str
    text: str
    domain: str = ""
    falsifiable: bool = True
    falsification_test: str = ""
    impact_if_wrong: str = ""


@dataclass
class DesignChoice:
    """Documents a specific modeling decision."""
    description: str
    rationale: str
    alternatives: Optional[List[str]] = None
    bias_risk: Optional[List[str]] = None
    who_decided: str = ""


# =========================================================================
# Known Bias Patterns
# =========================================================================

KNOWN_BIAS_PATTERNS = {
    "optimization_bias": {
        "description": "Tendency to frame all systems as optimization problems",
        "indicators": [
            "Single objective function without constraints",
            "Parameters chosen to maximize one output",
            "No accounting for what is sacrificed",
        ],
    },
    "recency_bias": {
        "description": "Over-weighting recent data or methods over established physics",
        "indicators": [
            "Default values from recent papers only",
            "No comparison to long-term baselines",
        ],
    },
    "complexity_bias": {
        "description": "Preferring complex models when simpler ones explain the data",
        "indicators": [
            "More parameters than the system requires",
            "Sensitivity analysis shows most parameters don't matter",
        ],
    },
    "simplification_bias": {
        "description": "Dropping terms that are inconvenient to model",
        "indicators": [
            "Externalized costs set to zero",
            "Long-term feedback loops omitted",
        ],
    },
    "linearity_bias": {
        "description": "Assuming linear relationships where nonlinear dynamics exist",
        "indicators": [
            "All rates are constant",
            "No threshold or saturation effects",
        ],
    },
    "survivorship_bias": {
        "description": "Training on successful systems, ignoring failed ones",
        "indicators": [
            "Default parameters reflect best case",
            "Validation only against working examples",
        ],
    },
    "scale_bias": {
        "description": "Assuming results at one scale apply at another",
        "indicators": [
            "No scale parameter in the model",
            "Same equations for lab and field",
        ],
    },
    "externalization_bias": {
        "description": "Omitting costs borne by parties outside the model boundary",
        "indicators": [
            "No pollution, waste, or degradation terms",
            "Efficiency calculated without full lifecycle",
        ],
    },
}


# =========================================================================
# DEFINE — Extract function signatures
# =========================================================================

def extract_function_signature(func: Callable) -> Dict[str, Any]:
    """Extract parameter names, defaults, and docstring from a function."""
    sig = inspect.signature(func)
    doc = inspect.getdoc(func) or ""

    parameters = []
    defaults = {}
    for name, p in sig.parameters.items():
        parameters.append(name)
        if p.default is not inspect.Parameter.empty:
            defaults[name] = p.default

    return {
        "function_name": func.__name__,
        "module": getattr(func, "__module__", ""),
        "docstring": doc,
        "parameters": parameters,
        "defaults": defaults,
    }


def _infer_base_and_ranges(func):
    """Infer base_params and param_ranges from function defaults."""
    sig = inspect.signature(func)
    base = {}
    ranges = {}
    for name, p in sig.parameters.items():
        if p.default is not inspect.Parameter.empty and isinstance(p.default, (int, float)):
            val = float(p.default)
            base[name] = val
            lo = val - max(abs(val), 1.0)
            hi = val + max(abs(val), 1.0)
            ranges[name] = (lo, hi)
    return base, ranges


# =========================================================================
# MEASURE — Catalog parameters
# =========================================================================

def catalog_parameters(
    func: Callable,
    specs: Optional[Dict[str, ParameterSpec]] = None,
) -> Dict[str, Any]:
    """Catalog all parameters with documentation status."""
    sig_info = extract_function_signature(func)
    catalog = []

    for name in sig_info["parameters"]:
        spec = specs.get(name) if specs else None
        entry = {
            "name": name,
            "default": sig_info["defaults"].get(name),
            "documented": spec.is_documented() if spec else False,
            "units": spec.units if spec else "UNDOCUMENTED",
            "physical_meaning": spec.physical_meaning if spec else "UNDOCUMENTED",
            "source": spec.source if spec else "UNDOCUMENTED",
        }
        catalog.append(entry)

    documented = [e for e in catalog if e["documented"]]
    total = len(catalog)

    return {
        "function": sig_info["function_name"],
        "total_parameters": total,
        "documented_count": len(documented),
        "documentation_ratio": len(documented) / total if total else 0.0,
        "parameters": catalog,
    }


# =========================================================================
# ANALYZE — Sensitivity analysis
# =========================================================================

def sensitivity_analysis(
    func: Callable,
    base_params: Optional[Dict[str, float]] = None,
    param_ranges: Optional[Dict[str, Tuple[float, float]]] = None,
    output_key: Optional[str] = None,
    n_steps: int = 10,
) -> Dict[str, Any]:
    """One-at-a-time sensitivity analysis."""
    if base_params is None or param_ranges is None:
        inferred_base, inferred_ranges = _infer_base_and_ranges(func)
        base_params = base_params or inferred_base
        param_ranges = param_ranges or inferred_ranges

    def _get_output(result):
        if isinstance(result, dict):
            if output_key and output_key in result:
                return float(result[output_key])
            for v in result.values():
                if isinstance(v, (int, float)):
                    return float(v)
            return 0.0
        return float(result)

    baseline_output = _get_output(func(**base_params))

    sensitivities = {}
    influence = {}

    for param_name, (lo, hi) in param_ranges.items():
        if param_name not in base_params:
            continue

        sweep = []
        for i in range(n_steps + 1):
            val = lo + (hi - lo) * i / n_steps
            test_params = dict(base_params)
            test_params[param_name] = val
            try:
                out = _get_output(func(**test_params))
            except Exception:
                out = None
            sweep.append({"value": val, "output": out})

        valid = [s["output"] for s in sweep if s["output"] is not None]
        if len(valid) > 1:
            output_range = max(valid) - min(valid)
            input_range = hi - lo
            # Use absolute range ratio — avoids division by zero when mean is near 0
            coeff = abs(output_range / input_range) if input_range != 0 else 0.0
        else:
            coeff = 0.0

        sensitivities[param_name] = sweep
        influence[param_name] = coeff

    # Pareto ranking
    pareto = sorted(influence, key=lambda k: -influence[k])

    return {
        "baseline_output": baseline_output,
        "sensitivities": sensitivities,
        "influence": influence,
        "pareto_ranking": pareto,
        "dominant_parameter": pareto[0] if pareto else None,
    }


# =========================================================================
# IMPROVE — Boundary tests and FMEA
# =========================================================================

def boundary_test(
    func: Callable,
    base_params: Optional[Dict[str, float]] = None,
    param_ranges: Optional[Dict[str, Tuple[float, float]]] = None,
    output_key: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Test function at boundary values. Identifies where the model breaks."""
    if base_params is None or param_ranges is None:
        inferred_base, inferred_ranges = _infer_base_and_ranges(func)
        base_params = base_params or inferred_base
        param_ranges = param_ranges or inferred_ranges

    def _safe_call(params):
        try:
            result = func(**params)
            if isinstance(result, dict) and output_key:
                return result.get(output_key, result)
            return result
        except Exception as e:
            return {"error": str(e)}

    tests = []
    for param_name, (lo, hi) in param_ranges.items():
        boundaries = [
            ("minimum", lo),
            ("maximum", hi),
            ("zero", 0.0),
            ("negative", -abs(hi)),
            ("extreme_high", hi * 10),
            ("extreme_low", lo * 0.01 if lo > 0 else lo * 10),
        ]
        for label, val in boundaries:
            test_params = dict(base_params)
            test_params[param_name] = val
            result = _safe_call(test_params)

            is_error = isinstance(result, dict) and "error" in result
            is_nan = isinstance(result, float) and math.isnan(result)
            is_inf = isinstance(result, float) and math.isinf(result)

            tests.append({
                "parameter": param_name,
                "boundary": label,
                "test_value": val,
                "result": result,
                "passed": not (is_error or is_nan or is_inf),
            })
    return tests


def generate_fmea(
    specs: List[Dict[str, Any]],
    sensitivities: List[Dict[str, Any]],
    boundaries: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Failure Mode and Effects Analysis. Returns items sorted by RPN descending."""
    if not specs:
        return []

    sens_map = {s.get("parameter", ""): s for s in sensitivities}
    fail_map = {}
    for b in boundaries:
        p = b.get("parameter", "")
        if not b.get("passed", True):
            fail_map[p] = fail_map.get(p, 0) + 1

    fmea = []
    for spec in specs:
        name = spec.get("name", "")
        documented = spec.get("documented", False)

        severity = 3 if documented else 7
        inf = sens_map.get(name, {}).get("influence", 0.5)
        occurrence = max(2, min(9, int(inf * 10))) if isinstance(inf, (int, float)) else 5
        boundary_fails = fail_map.get(name, 0)
        detection = 3 if boundary_fails == 0 else min(9, 3 + boundary_fails * 2)

        rpn = severity * occurrence * detection

        fmea.append({
            "name": name,
            "documented": documented,
            "severity": severity,
            "occurrence": occurrence,
            "detection": detection,
            "rpn": rpn,
            "recommendation": (
                "Document physical meaning, source, and uncertainty"
                if not documented else "Verify against independent measurement"
            ),
        })

    fmea.sort(key=lambda x: -x["rpn"])
    return fmea


# =========================================================================
# CONTROL — Capability analysis
# =========================================================================

def capability_analysis(
    outputs: List[float],
    lsl: Optional[float] = None,
    usl: Optional[float] = None,
    target: Optional[float] = None,
) -> Dict[str, Any]:
    """Compute process capability indices (Cp, Cpk)."""
    n = len(outputs)
    if n < 2:
        return {"error": "Need at least 2 data points", "n": n}

    mean = sum(outputs) / n
    std = math.sqrt(sum((x - mean) ** 2 for x in outputs) / (n - 1))

    result: Dict[str, Any] = {
        "n": n,
        "mean": round(mean, 6),
        "std": round(std, 6),
        "min": round(min(outputs), 6),
        "max": round(max(outputs), 6),
    }

    if std == 0:
        result["note"] = "zero variance — all outputs identical"
        return result

    if lsl is not None and usl is not None:
        cp = (usl - lsl) / (6 * std)
        cpu = (usl - mean) / (3 * std)
        cpl = (mean - lsl) / (3 * std)
        cpk = min(cpu, cpl)
        result["Cp"] = round(cp, 4)
        result["Cpk"] = round(cpk, 4)

    result["UCL"] = round(mean + 3 * std, 6)
    result["LCL"] = round(mean - 3 * std, 6)

    if target is not None:
        result["bias"] = round(mean - target, 6)

    return result


def monte_carlo_capability(
    func: Callable,
    n: int = 1000,
    seed: Optional[int] = 42,
    base_params: Optional[Dict[str, float]] = None,
    param_ranges: Optional[Dict[str, Tuple[float, float]]] = None,
    output_key: Optional[str] = None,
    lsl: Optional[float] = None,
    usl: Optional[float] = None,
) -> Dict[str, Any]:
    """Monte Carlo simulation for capability analysis."""
    if base_params is None or param_ranges is None:
        inferred_base, inferred_ranges = _infer_base_and_ranges(func)
        base_params = base_params or inferred_base
        param_ranges = param_ranges or inferred_ranges

    if seed is not None:
        rng.seed(seed)

    outputs = []
    failures = 0

    for _ in range(n):
        params = {
            name: rng.uniform(lo, hi)
            for name, (lo, hi) in param_ranges.items()
        }
        try:
            result = func(**params)
            if isinstance(result, dict):
                if output_key and output_key in result:
                    val = float(result[output_key])
                else:
                    vals = [v for v in result.values() if isinstance(v, (int, float))]
                    val = vals[0] if vals else None
            else:
                val = float(result)

            if val is not None and not (math.isnan(val) or math.isinf(val)):
                outputs.append(val)
            else:
                failures += 1
        except Exception:
            failures += 1

    cap = capability_analysis(outputs, lsl, usl) if len(outputs) >= 2 else {"n": len(outputs)}
    cap["n_samples"] = n
    cap["outputs"] = outputs
    cap["failures"] = failures
    cap["failure_rate"] = round(failures / n, 4) if n > 0 else 0.0

    return cap


# =========================================================================
# Full audit (Layer 1 — mechanics)
# =========================================================================

def audit_function(
    func: Callable,
    base_params: Optional[Dict[str, float]] = None,
    param_ranges: Optional[Dict[str, Tuple[float, float]]] = None,
    specs: Optional[Dict[str, ParameterSpec]] = None,
    assumptions: Optional[List[AssumptionRecord]] = None,
    output_key: Optional[str] = None,
    lsl: Optional[float] = None,
    usl: Optional[float] = None,
    n_sensitivity_steps: int = 10,
    n_monte_carlo: int = 500,
) -> Dict[str, Any]:
    """Complete DMAIC audit of a function."""
    if base_params is None or param_ranges is None:
        ib, ir = _infer_base_and_ranges(func)
        base_params = base_params or ib
        param_ranges = param_ranges or ir

    # DEFINE
    sig_info = extract_function_signature(func)

    # MEASURE
    param_catalog = catalog_parameters(func, specs)

    # ANALYZE
    sens = sensitivity_analysis(
        func, base_params, param_ranges,
        output_key=output_key, n_steps=n_sensitivity_steps,
    )

    # IMPROVE
    boundaries = boundary_test(func, base_params, param_ranges, output_key)
    boundary_failures = [b for b in boundaries if not b["passed"]]

    fmea_specs = param_catalog["parameters"]
    fmea_sens = [
        {"parameter": name, "influence": sens["influence"].get(name, 0)}
        for name in base_params
    ]
    fmea = generate_fmea(fmea_specs, fmea_sens, boundaries)

    # CONTROL
    mc = monte_carlo_capability(
        func, n=n_monte_carlo,
        base_params=base_params, param_ranges=param_ranges,
        output_key=output_key, lsl=lsl, usl=usl,
    )

    grade = _grade(param_catalog, boundary_failures, mc)

    return {
        "function": sig_info["function_name"],
        "define": {
            "parameters": param_catalog,
            "assumptions": [
                {"id": a.id, "text": a.text, "domain": a.domain, "falsifiable": a.falsifiable}
                for a in (assumptions or [])
            ],
        },
        "measure": {
            "baseline_params": base_params,
            "baseline_output": sens["baseline_output"],
            "documentation_ratio": param_catalog["documentation_ratio"],
        },
        "analyze": {
            "pareto_ranking": sens["pareto_ranking"],
            "dominant_parameter": sens["dominant_parameter"],
            "influence": sens["influence"],
        },
        "improve": {
            "boundary_tests_total": len(boundaries),
            "boundary_failures": len(boundary_failures),
            "boundary_failure_details": boundary_failures,
            "fmea": fmea,
        },
        "control": {
            "monte_carlo": mc,
        },
        "summary": {
            "documentation_ratio": param_catalog["documentation_ratio"],
            "dominant_parameter": sens["dominant_parameter"],
            "boundary_failure_rate": len(boundary_failures) / len(boundaries) if boundaries else 0,
            "monte_carlo_failure_rate": mc.get("failure_rate", 0),
            "Cpk": mc.get("Cpk"),
            "overall_grade": grade,
        },
    }


def _grade(catalog, boundary_failures, mc) -> str:
    score = 0
    dr = catalog["documentation_ratio"]
    if dr >= 0.9:
        score += 3
    elif dr >= 0.5:
        score += 1
    if len(boundary_failures) == 0:
        score += 3
    elif len(boundary_failures) <= 3:
        score += 1
    if mc.get("failure_rate", 1) < 0.01:
        score += 2
    elif mc.get("failure_rate", 1) < 0.05:
        score += 1
    cpk = mc.get("Cpk")
    if cpk is not None and cpk >= 1.33:
        score += 2
    elif cpk is not None and cpk >= 1.0:
        score += 1
    if score >= 9:
        return "A — Production ready"
    elif score >= 6:
        return "B — Usable with caveats"
    elif score >= 3:
        return "C — Needs improvement"
    return "D — Not validated"


# =========================================================================
# Layer 2 — Bias detection
# =========================================================================

def flag_biases(
    assumptions: Optional[List[AssumptionRecord]] = None,
    design_choices: Optional[List[DesignChoice]] = None,
    parameter_catalog: Optional[Dict[str, Any]] = None,
    externalization_terms: Optional[List[str]] = None,
    sensitivity_result: Optional[Dict] = None,
) -> List[Dict[str, Any]]:
    """Scan for known bias patterns. Returns list of bias flags."""
    assumptions = assumptions or []
    design_choices = design_choices or []
    parameter_catalog = parameter_catalog or {"parameters": []}
    flags = []

    # Simplification bias — many undocumented params
    params = parameter_catalog.get("parameters", [])
    undoc = [p for p in params if not p.get("documented", False)]
    if len(undoc) > len(params) * 0.3 and len(params) > 0:
        flags.append({
            "bias": "simplification_bias",
            "evidence": f"{len(undoc)}/{len(params)} parameters undocumented",
            "severity": "high",
        })

    # Survivorship bias — unfalsifiable assumptions
    unfalsifiable = [a for a in assumptions if not a.falsifiable]
    if unfalsifiable:
        flags.append({
            "bias": "survivorship_bias",
            "evidence": f"{len(unfalsifiable)} unfalsifiable assumptions",
            "severity": "high",
        })

    # Optimization bias — design choices with no alternatives
    for dc in design_choices:
        alts = dc.alternatives
        if not alts:
            flags.append({
                "bias": "optimization_bias",
                "evidence": f"Design choice '{dc.description}' lists no alternatives",
                "severity": "high",
            })

    # Externalization bias
    if externalization_terms is not None and len(externalization_terms) == 0 and len(params) > 0:
        flags.append({
            "bias": "externalization_bias",
            "evidence": "No externalization terms provided",
            "severity": "high",
        })

    return flags


def compare_formulations(
    formulations: List[Callable],
    base_params: Optional[Dict[str, float]] = None,
    param_ranges: Optional[Dict[str, Tuple[float, float]]] = None,
    output_key: Optional[str] = None,
    n_monte_carlo: int = 200,
    seed: int = 42,
) -> Dict[str, Any]:
    """Compare multiple alternative formulations."""
    results = {}
    for func in formulations:
        bp, pr = _infer_base_and_ranges(func)
        bp = base_params or bp
        pr = param_ranges or pr

        sens = sensitivity_analysis(func, bp, pr, output_key=output_key)
        mc = monte_carlo_capability(
            func, n=n_monte_carlo, seed=seed,
            base_params=bp, param_ranges=pr, output_key=output_key,
        )
        results[func.__name__] = {
            "baseline_output": sens["baseline_output"],
            "dominant_parameter": sens["dominant_parameter"],
            "mc_mean": mc.get("mean"),
            "mc_std": mc.get("std"),
            "failure_rate": mc.get("failure_rate"),
        }

    return results


# =========================================================================
# Full audit (Layer 1 + Layer 2)
# =========================================================================

def full_audit(
    func: Callable,
    base_params: Optional[Dict[str, float]] = None,
    param_ranges: Optional[Dict[str, Tuple[float, float]]] = None,
    specs: Optional[Dict[str, ParameterSpec]] = None,
    assumptions: Optional[List[AssumptionRecord]] = None,
    design_choices: Optional[List[DesignChoice]] = None,
    output_key: Optional[str] = None,
    lsl: Optional[float] = None,
    usl: Optional[float] = None,
) -> Dict[str, Any]:
    """Complete audit: Layer 1 (mechanics) + Layer 2 (bias/design choices)."""
    result = audit_function(
        func, base_params, param_ranges,
        specs=specs, assumptions=assumptions,
        output_key=output_key, lsl=lsl, usl=usl,
    )

    bias_flags = flag_biases(
        assumptions=assumptions,
        design_choices=design_choices,
        parameter_catalog=result["define"]["parameters"],
    )

    result["bias_detection"] = {
        "flags": bias_flags,
        "high_severity_count": len([f for f in bias_flags if f.get("severity") == "high"]),
    }

    high_bias = result["bias_detection"]["high_severity_count"]
    if high_bias >= 3:
        result["summary"]["bias_grade"] = "FAIL"
    elif high_bias >= 1:
        result["summary"]["bias_grade"] = "WARNING"
    elif bias_flags:
        result["summary"]["bias_grade"] = "CAUTION"
    else:
        result["summary"]["bias_grade"] = "PASS"

    return result


# =========================================================================
# Report generation
# =========================================================================

def generate_report(
    audit_result: Dict[str, Any],
    fmt: str = "markdown",
    filepath: Optional[str] = None,
) -> str:
    """Generate audit report in markdown, JSON, or CSV."""
    if fmt == "json":
        content = json.dumps(audit_result, indent=2, default=str)
    elif fmt == "csv":
        content = _to_csv(audit_result)
    else:
        content = _to_markdown(audit_result)

    if filepath:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
    return content


def _to_markdown(r: Dict) -> str:
    lines = []
    a = lines.append

    a(f"# First-Principles Audit: `{r.get('function', 'unknown')}`\n")

    s = r.get("summary", {})
    a("## Summary\n")
    a("| Metric | Value |")
    a("|--------|-------|")
    a(f"| Overall Grade | **{s.get('overall_grade', 'N/A')}** |")
    a(f"| Documentation Ratio | {s.get('documentation_ratio', 0):.0%} |")
    a(f"| Dominant Parameter | {s.get('dominant_parameter', 'N/A')} |")
    a(f"| Boundary Failure Rate | {s.get('boundary_failure_rate', 0):.0%} |")
    a(f"| MC Failure Rate | {s.get('monte_carlo_failure_rate', 0):.1%} |")
    if s.get("Cpk") is not None:
        a(f"| Cpk | {s['Cpk']:.3f} |")
    a("")

    # Parameters
    define = r.get("define", {})
    params = define.get("parameters", {}).get("parameters", [])
    if params:
        a("## Parameters\n")
        a("| Name | Default | Units | Source | Documented |")
        a("|------|---------|-------|--------|------------|")
        for p in params:
            doc = "Yes" if p.get("documented") else "**NO**"
            a(f"| {p['name']} | {p.get('default', '')} | {p.get('units', '')} | {p.get('source', '')} | {doc} |")
        a("")

    # Sensitivity
    analyze = r.get("analyze", {})
    pareto = analyze.get("pareto_ranking", [])
    influence = analyze.get("influence", {})
    if pareto:
        a("## Sensitivity Ranking\n")
        a("| Rank | Parameter | Influence |")
        a("|------|-----------|-----------|")
        for i, name in enumerate(pareto):
            a(f"| {i+1} | {name} | {influence.get(name, 0):.4f} |")
        a("")

    # FMEA
    improve = r.get("improve", {})
    fmea = improve.get("fmea", [])
    if fmea:
        a("## FMEA (Top 5)\n")
        a("| Item | RPN | S | O | D | Recommendation |")
        a("|------|-----|---|---|---|----------------|")
        for item in fmea[:5]:
            a(f"| {item['name']} | {item['rpn']} | {item['severity']} | {item['occurrence']} | {item['detection']} | {item.get('recommendation', '')} |")
        a("")

    # Control
    mc = r.get("control", {}).get("monte_carlo", {})
    if mc:
        a("## Monte Carlo\n")
        a(f"- Samples: {mc.get('n_samples', 'N/A')}")
        a(f"- Mean: {mc.get('mean', 'N/A')}")
        a(f"- Std: {mc.get('std', 'N/A')}")
        a(f"- Failures: {mc.get('failures', 0)} ({mc.get('failure_rate', 0):.1%})")
        a("")

    return "\n".join(lines)


def _to_csv(r: Dict) -> str:
    buf = StringIO()
    writer = csv.writer(buf)
    writer.writerow(["Section", "Item", "Metric", "Value"])

    for p in r.get("define", {}).get("parameters", {}).get("parameters", []):
        writer.writerow(["parameter", p["name"], "documented", p.get("documented", False)])
        writer.writerow(["parameter", p["name"], "units", p.get("units", "")])

    for name in r.get("analyze", {}).get("pareto_ranking", []):
        inf = r.get("analyze", {}).get("influence", {}).get(name, 0)
        writer.writerow(["sensitivity", name, "influence", inf])

    mc = r.get("control", {}).get("monte_carlo", {})
    for k in ["mean", "std", "Cp", "Cpk", "failures", "failure_rate"]:
        if k in mc:
            writer.writerow(["capability", "monte_carlo", k, mc[k]])

    writer.writerow(["summary", "grade", "overall", r.get("summary", {}).get("overall_grade", "")])

    return buf.getvalue()


# =========================================================================
# CLI
# =========================================================================

def main():
    """CLI entry point — audit a demo function to show the engine."""
    import argparse
    parser = argparse.ArgumentParser(description="Six Sigma First-Principles Audit")
    parser.add_argument("--demo", action="store_true", help="Run demo audit")
    parser.add_argument("--format", choices=["markdown", "json", "csv"], default="markdown")
    args = parser.parse_args()

    if args.demo:
        def example(rate=0.05, capacity=100, efficiency=0.85):
            """Energy throughput: rate * capacity * efficiency."""
            return rate * capacity * efficiency

        specs = {
            "rate": ParameterSpec(name="rate", physical_meaning="flow rate", source="measured", units="m3/s", min_value=0, max_value=1),
            "capacity": ParameterSpec(name="capacity", physical_meaning="system capacity", source="derived", units="kW"),
            "efficiency": ParameterSpec(name="efficiency", physical_meaning="conversion efficiency", source="literature", units="fraction", min_value=0, max_value=1),
        }

        result = full_audit(example, specs=specs)
        print(generate_report(result, fmt=args.format))
    else:
        print("Use --demo to run a demonstration audit.")
        print("Or import and use: from rosetta_shape_core.first_principles_audit import audit_function")


if __name__ == "__main__":
    main()
