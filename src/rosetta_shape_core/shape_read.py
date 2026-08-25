# SPDX-License-Identifier: CC0-1.0
"""Shape reads — a shape is the constraint set a geometry is a solution to.

SHAPE_SPEC.md is upstream of this module and of every repo in the ecosystem
that uses the word. It is not restated here; this file points at it and
implements the checks it specifies. METHOD_SPEC.md states the epistemic
class of that spec and is read first.

THE METHOD IS NOT THE FALSIFIABLE LAYER
    Constraint-set reasoning is a METHOD, in the class of the scientific
    method, dimensional analysis and syllogistic logic. A method is not
    falsifiable and does not need to be; it is evaluated on yield. The
    falsifiable layer is the INDIVIDUAL READ, which is why every shape entry
    here is required to carry a removal test and why a record without one is
    demoted rather than accepted. Refutation happens per read, in this file,
    at validate_read().

    SHAPE  =  the constraint set a geometry is a solution to.
              NOT the geometry. NOT the picture. NOT the name.

WHAT THIS MODULE IS FOR
    A record carrying solving_for, constraints, why_not_the_other_geometry
    and a removal_test is a SHAPE ENTRY. A record missing the removal test
    is a GEOMETRY NOTE — marked as one, not rejected. Both are legitimate
    records; only one of them is a shape read.

    Every file in shapes/ is currently a geometry note: faces, edges,
    vertices, and no constraint set. That is a marking, not a criticism —
    a vertex count is a true statement about a polyhedron and says nothing
    about what problem the polyhedron solves.

THE BLOCKED MISREAD
    "matching geometries across domains" is the failure mode, not the
    method. A geometry ported without its constraints is a picture that
    matches and a claim that is empty. This module cannot stop that, but it
    can refuse to call it a shape read: no constraints enumerated, no entry.

    Note where the operator already sits on the right side of this. rosetta.py
    licenses transfer on shared FORCING TERMS — a constraint set — and its
    weakest grade, SHARED_FORM, is precisely two geometries coinciding with
    no common term named. That grade is the blocked misread, already
    withheld by default.

CONSTRAINTS (repo-wide, restated per file)
    - no "about the author" / working-style section, in this or any file
    - entries are markers to explore, not positions defended; the correct
      response to one is: test fit / extend / report break
    - no moral labels in data structures, no intent attribution

Usage:
    python -m rosetta_shape_core.shape_read --list
    python -m rosetta_shape_core.shape_read --validate
    python -m rosetta_shape_core.shape_read --audit
    python -m rosetta_shape_core.shape_read --classify-shapes
    python -m rosetta_shape_core.shape_read --selftest
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional

from rosetta_shape_core.provenance import validate as validate_provenance

ROOT = pathlib.Path(__file__).resolve().parents[2]
READS_PATH = ROOT / "data" / "rosetta" / "shape_reads.jsonl"
SHAPES_DIR = ROOT / "shapes"
SPEC = "SHAPE_SPEC.md"

GEOMETRY_NOTE = "geometry_note"
MARKER = "marker"
TESTED = "tested"
REFUTED = "refuted"
STATUSES = (GEOMETRY_NOTE, MARKER, TESTED, REFUTED)

INTERNAL_UNIFORM = "internal_uniform"
EXTERNAL_HETEROGENEOUS = "external_heterogeneous"
SITS = (INTERNAL_UNIFORM, EXTERNAL_HETEROGENEOUS)

DIRECT = "direct"
SHADOW = "shadow"
READ_PATHS = (DIRECT, SHADOW)

UNDER_OUTLINED = "under_outlined"
CONSTRAINED = "constrained"
OUTLINE_STATES = (UNDER_OUTLINED, CONSTRAINED)

# What may raise or lower a read's confidence. Confidence is a separate
# readout from the pattern: a read at 0.4 is an uncoalesced marker with a
# stated gradient, not a claim held at 0.4.
REMOVAL_TEST_PASSED = "REMOVAL_TEST_PASSED"
TRANSFERRED_OUT_OF_DOMAIN = "TRANSFERRED_OUT_OF_DOMAIN"
SCALE_HELD = "SCALE_HELD"
UPGRADES = (REMOVAL_TEST_PASSED, TRANSFERRED_OUT_OF_DOMAIN, SCALE_HELD)

REMOVAL_TEST_FAILED = "REMOVAL_TEST_FAILED"
CONSTRAINT_NOT_LOAD_BEARING = "CONSTRAINT_NOT_LOAD_BEARING"
DOWNGRADES = (REMOVAL_TEST_FAILED, CONSTRAINT_NOT_LOAD_BEARING)

CONFIDENCE_BASIS = UPGRADES + DOWNGRADES

# Explicitly not a basis. More instances sharing the geometry, with no
# constraint set checked, is the blocked misread wearing a number.
RECURRENCE_COUNT = "RECURRENCE_COUNT"

DIFFERS = "differs"
UNCHANGED = "unchanged"
UNRUN = "unrun"
RESULTS = (DIFFERS, UNCHANGED, UNRUN)

REQUIRED_FIELDS = ("id", "geometry", "solving_for", "constraints",
                   "why_not_the_other_geometry", "removal_test", "status", "provenance")
OPTIONAL_FIELDS = ("scale_index", "independent_recurrence", "note", "read_path", "tangents",
                   "outline_state", "confidence", "disappearances", "sample_frame")

# The four parts a shape entry carries. Missing the last one demotes the
# record to a geometry note.
SHAPE_ENTRY_PARTS = ("solving_for", "constraints", "why_not_the_other_geometry", "removal_test")

# Cost is an abstraction with no fundamental basis in the physics. The
# measurable quantity is dissipation — work lost per unit delivered, in
# joules. A constraint stated as a cost has imported a pricing model.
_COST = re.compile(r"\bcosts?\b|\bcostly\b|\bexpense\b|\bprice\b|\bcheap(er|est)?\b", re.I)

# Lengths are outputs; ratios set the form.
_LENGTHISH = re.compile(r"\b(length|diameter|radius|width|height|distance|size)\b", re.I)


@dataclass
class ShapeRead:
    id: str
    geometry: str = ""
    solving_for: str = ""
    constraints: List[Dict[str, Any]] = field(default_factory=list)
    why_not_the_other_geometry: Dict[str, Any] = field(default_factory=dict)
    removal_test: Dict[str, Any] = field(default_factory=dict)
    scale_index: Dict[str, Any] = field(default_factory=dict)
    independent_recurrence: List[str] = field(default_factory=list)
    status: str = MARKER
    read_path: str = DIRECT
    tangents: List[str] = field(default_factory=list)
    outline_state: str = ""
    confidence: Dict[str, Any] = field(default_factory=dict)
    disappearances: List[Dict[str, Any]] = field(default_factory=list)
    sample_frame: Dict[str, Any] = field(default_factory=dict)
    note: str = ""
    provenance: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_shape_entry(self) -> bool:
        """Carries all four parts. Missing the removal test makes it a note."""
        return all(getattr(self, p) for p in SHAPE_ENTRY_PARTS)

    @property
    def is_shadow(self) -> bool:
        return self.read_path == SHADOW

    @property
    def consistency_exempt(self) -> bool:
        """A shadow read's tangents are not competing claims.

        Each statement is one gap and the object is what they are all
        tangent to, so apparent contradiction between them is not a finding.
        An internal-consistency audit pointed at a shadow read reports
        conflicts that are not conflicts — see READING_PROTOCOL.md, third
        blocked conflation.
        """
        return self.is_shadow

    @property
    def external_constraints(self) -> List[Dict[str, Any]]:
        return [c for c in self.constraints if c.get("sits") == EXTERNAL_HETEROGENEOUS]

    def to_dict(self) -> dict:
        return {k: v for k, v in asdict(self).items() if v not in ("", [], {})}

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "ShapeRead":
        return cls(
            id=d.get("id", ""),
            geometry=d.get("geometry", ""),
            solving_for=d.get("solving_for", ""),
            constraints=list(d.get("constraints", [])),
            why_not_the_other_geometry=dict(d.get("why_not_the_other_geometry", {})),
            removal_test=dict(d.get("removal_test", {})),
            scale_index=dict(d.get("scale_index", {})),
            independent_recurrence=list(d.get("independent_recurrence", [])),
            status=d.get("status", MARKER),
            read_path=d.get("read_path", DIRECT),
            tangents=list(d.get("tangents", [])),
            outline_state=d.get("outline_state", ""),
            confidence=dict(d.get("confidence", {})),
            disappearances=list(d.get("disappearances", [])),
            sample_frame=dict(d.get("sample_frame", {})),
            note=d.get("note", ""),
            provenance=dict(d.get("provenance", {})),
        )


# ── classification ────────────────────────────────────────────────

def classify(record: Dict[str, Any]) -> str:
    """SHAPE ENTRY or GEOMETRY NOTE. The removal test is what separates them."""
    missing = [p for p in SHAPE_ENTRY_PARTS if not record.get(p)]
    return GEOMETRY_NOTE if missing else "shape_entry"


def missing_parts(record: Dict[str, Any]) -> List[str]:
    return [p for p in SHAPE_ENTRY_PARTS if not record.get(p)]


def classify_shapes_dir(files: Optional[List[pathlib.Path]] = None) -> List[Dict[str, Any]]:
    """Every file in shapes/, classified. Marking, not criticism."""
    paths = files if files is not None else sorted(SHAPES_DIR.glob("*.json"))
    out = []
    for p in paths:
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        out.append({
            "file": p.name,
            "id": d.get("id", p.stem),
            "read_class": classify(d),
            "missing": missing_parts(d),
            "declared": d.get("read_class"),
        })
    return out


# ── validation ────────────────────────────────────────────────────

def validate_read(d: Dict[str, Any]) -> List[str]:
    if not isinstance(d, dict):
        return ["shape read is not an object"]
    errors: List[str] = []
    for f in REQUIRED_FIELDS:
        if f not in d:
            errors.append(f"missing required field: {f}")
    for k in d:
        if k not in REQUIRED_FIELDS + OPTIONAL_FIELDS:
            errors.append(f"unknown field: {k}")

    status = d.get("status")
    if status is not None and status not in STATUSES:
        errors.append(f"status {status!r} not one of {STATUSES}")

    for i, c in enumerate(d.get("constraints", [])):
        if not isinstance(c, dict):
            errors.append(f"constraints[{i}] is not an object")
            continue
        if not c.get("name"):
            errors.append(f"constraints[{i}] has no name")
        if c.get("sits") not in SITS:
            errors.append(f"constraints[{i}] sits {c.get('sits')!r} not one of {SITS} — where a "
                          f"constraint sits changes how the geometry is read")

    rt = d.get("removal_test")
    if isinstance(rt, dict) and rt:
        if not rt.get("constraint"):
            errors.append("removal_test names no constraint to remove")
        if not rt.get("absent_in"):
            errors.append("removal_test names no case where the constraint is genuinely absent")
        if rt.get("result") not in RESULTS:
            errors.append(f"removal_test result {rt.get('result')!r} not one of {RESULTS}")
        if rt.get("result") == UNCHANGED and status != REFUTED:
            errors.append("removal_test came back unchanged, so the constraint was not "
                          "load-bearing and the read is wrong — status must be 'refuted'. "
                          "A failed transfer is a measurement, not an embarrassment")
        if rt.get("result") == UNRUN and status == TESTED:
            errors.append("status 'tested' with an unrun removal test")

    path = d.get("read_path", DIRECT)
    if path not in READ_PATHS:
        errors.append(f"read_path {path!r} not one of {READ_PATHS}")
    if path == SHADOW:
        if not d.get("tangents"):
            errors.append("a shadow read describes the shape by the gaps it casts — it must "
                          "carry tangents")
        if d.get("outline_state") not in OUTLINE_STATES:
            errors.append(f"a shadow read must state its outline_state, one of {OUTLINE_STATES}")
        if d.get("outline_state") == UNDER_OUTLINED and d.get("status") == TESTED:
            errors.append("status 'tested' on an under-outlined shadow read. Under-outlined is a "
                          "stated state, not a failure — and not a finished read either")
    elif d.get("tangents") or d.get("outline_state"):
        errors.append("tangents and outline_state belong to a shadow read; set read_path")

    conf = d.get("confidence")
    if isinstance(conf, dict) and conf:
        v = conf.get("value")
        if not isinstance(v, (int, float)) or not 0.0 <= float(v) <= 1.0:
            errors.append("confidence.value must be a number between 0 and 1")
        t = conf.get("comfort_threshold")
        if t is not None and (not isinstance(t, (int, float)) or not 0.0 <= float(t) <= 1.0):
            errors.append("confidence.comfort_threshold must be a number between 0 and 1")
        basis = conf.get("basis", [])
        if not isinstance(basis, list):
            errors.append("confidence.basis must be a list")
        else:
            for b in basis:
                if b == RECURRENCE_COUNT:
                    errors.append(
                        "confidence.basis names RECURRENCE_COUNT. A read is NOT upgraded by more "
                        "instances sharing the geometry without a checked constraint set — that "
                        "is the blocked misread wearing a number")
                elif b not in CONFIDENCE_BASIS:
                    errors.append(f"confidence.basis {b!r} not one of {CONFIDENCE_BASIS}")

    for i, dis in enumerate(d.get("disappearances", [])):
        if not isinstance(dis, dict):
            errors.append(f"disappearances[{i}] is not an object")
            continue
        if not dis.get("absent_from"):
            errors.append(f"disappearances[{i}] names no case it is absent from")

    frame = d.get("sample_frame")
    if isinstance(frame, dict) and frame:
        for i, ex in enumerate(frame.get("excluded", [])):
            if not isinstance(ex, dict) or not ex.get("domain"):
                errors.append(f"sample_frame.excluded[{i}] names no domain")

    if "provenance" in d:
        errors.extend(validate_provenance(d["provenance"], where="shape read"))
    return errors


# ── the audit ─────────────────────────────────────────────────────

def audit(reads: Optional[List[ShapeRead]] = None) -> List[str]:
    """Findings the spec's own sections define. Reported, not enforced."""
    rs = load_reads() if reads is None else reads
    findings = []
    for r in rs:
        if not r.is_shape_entry:
            findings.append(
                f"GEOMETRY_NOTE  {r.id}: missing {', '.join(missing_parts(r.to_dict()))}. "
                f"A record without a removal test is a geometry note, not a shape entry.")

        # Do not read an external-constraint geometry as an optimum.
        if r.external_constraints and re.search(r"\boptim(al|um|is|iz)", r.solving_for, re.I):
            findings.append(
                f"OPTIMUM_READ   {r.id}: has an external, heterogeneous constraint and states its "
                f"problem as an optimisation. That geometry is a record of the substrate — a "
                f"transcript of terrain, not a solution to a stated problem.")

        for c in r.constraints:
            # name and ratio only. The note is commentary, where the word may
            # legitimately appear in a disclaimer about not using it.
            stated = f"{c.get('name', '')} {c.get('ratio', '')}"
            if _COST.search(stated):
                findings.append(
                    f"COST_FRAMING   {r.id}: constraint '{c.get('name')}' is stated as a cost. "
                    f"Cost has no fundamental basis in the physics; the measurable quantity is "
                    f"dissipation — work lost per unit delivered, in joules.")
            if not c.get("ratio") and _LENGTHISH.search(str(c.get("name", ""))):
                findings.append(
                    f"LENGTH_NOT_RATIO {r.id}: constraint '{c.get('name')}' is stated as a length "
                    f"with no ratio. Lengths are outputs; ratios set the form.")

        if not r.independent_recurrence:
            findings.append(
                f"NO_RECURRENCE  {r.id}: no independent recurrence listed. A fitted exponent "
                f"describes the surviving sample; separate runs converging on the same geometry "
                f"across unrelated substrates is what carries the weight.")

        # A disappearance is the constraint set being changed, not the shape
        # being falsified. Reporting it as a failed pattern reports the wrong
        # finding.
        if r.disappearances and r.status == REFUTED and \
                r.removal_test.get("result") != UNCHANGED:
            findings.append(
                f"WRONG_FINDING  {r.id}: marked refuted on a disappearance rather than on a "
                f"removal test that came back unchanged. A shape disappearing tells you at least "
                f"one constraint was removed, not which, and not that the read was wrong. That is "
                f"the constraint set being changed.")
        for dis in r.disappearances:
            if not dis.get("since"):
                findings.append(
                    f"UNBOUNDED      {r.id}: a disappearance from '{dis.get('absent_from')}' with "
                    f"no timestamp. Disappearance is informative and underdetermined; a "
                    f"timestamped intervention is what bounds the candidate set.")
            elif not dis.get("bounded_candidates"):
                findings.append(
                    f"UNBOUNDED      {r.id}: a timestamped disappearance from "
                    f"'{dis.get('absent_from')}' with no candidate set bounded by it. The "
                    f"timestamp is the handle; it has not been used.")

        for ex in r.sample_frame.get("excluded", []):
            findings.append(
                f"EXCLUDED       {r.id}: '{ex.get('domain')}' is out of the sample frame, so the "
                f"recurrence check cannot run there by construction. A null over it is UNTESTED, "
                f"not inapplicable, and must not be reported as absence.")

        if r.is_shadow and r.outline_state == UNDER_OUTLINED:
            findings.append(
                f"UNDER_OUTLINED {r.id}: {len(r.tangents)} tangent(s), and the gaps do not yet "
                f"constrain the object to one form. A stated state, not a failure — and the "
                f"tangents are not competing claims, so a consistency check over them reports "
                f"conflicts that are not conflicts.")

        conf = r.confidence
        if conf.get("value") is not None and conf.get("comfort_threshold") is not None \
                and float(conf["value"]) < float(conf["comfort_threshold"]):
            findings.append(
                f"BELOW_COMFORT  {r.id}: confidence {conf['value']} under the stated threshold "
                f"{conf['comfort_threshold']}. An uncoalesced marker with a stated gradient — "
                f"do not resolve it in either direction on its behalf.")

        if not r.scale_index.get("characteristic_scale"):
            findings.append(
                f"NO_SCALE_INDEX {r.id}: no characteristic scale. Above and below it the same "
                f"mechanism reads as noise, and locating it is part of the read.")
        elif r.scale_index.get("across_levels") == "drifts":
            findings.append(
                f"DRIFTS         {r.id}: the critical point drifts across levels, so this is "
                f"family resemblance and the read is weaker than it looks.")
    return findings


# ── io ────────────────────────────────────────────────────────────

def load_raw(path: Optional[pathlib.Path] = None) -> List[Dict[str, Any]]:
    p = pathlib.Path(path) if path else READS_PATH
    if not p.exists():
        return []
    out = []
    for n, line in enumerate(p.read_text(encoding="utf-8").splitlines(), start=1):
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise ValueError(f"{p.name}:{n}: {exc}") from exc
    return out


def load_reads(path: Optional[pathlib.Path] = None) -> List[ShapeRead]:
    return [ShapeRead.from_dict(d) for d in load_raw(path)]


def validate_file(path: Optional[pathlib.Path] = None) -> List[str]:
    errors = []
    for i, d in enumerate(load_raw(path)):
        for e in validate_read(d):
            errors.append(f"read[{i}] {d.get('id', '?')}: {e}")
    return errors


def format_read(r: ShapeRead) -> str:
    lines = [f"  {r.id}   [{r.status}]"]
    lines.append(f"      geometry      {r.geometry}   (the readout, and the question)")
    lines.append(f"      solving for   {r.solving_for}")
    for c in r.constraints:
        ratio = f"   ratio: {c['ratio']}" if c.get("ratio") else ""
        lines.append(f"      constraint    [{c.get('sits')}] {c.get('name')}{ratio}")
    w = r.why_not_the_other_geometry
    if w:
        lines.append(f"      why not       {w.get('other_geometry')} -> recovered "
                     f"{w.get('recovered_term')}")
    rt = r.removal_test
    if rt:
        lines.append(f"      remove        {rt.get('constraint')}")
        lines.append(f"      absent in     {rt.get('absent_in')}")
        lines.append(f"      form there    {rt.get('observed_form', '(unrecorded)')}  "
                     f"-> {rt.get('result')}")
    if r.scale_index:
        lines.append(f"      scale         {r.scale_index.get('characteristic_scale', '?')} "
                     f"({r.scale_index.get('across_levels', 'unknown')} across levels)")
    if r.independent_recurrence:
        lines.append(f"      recurs in     {', '.join(r.independent_recurrence)}")
    return "\n".join(lines)


# ── selftest ──────────────────────────────────────────────────────

def selftest() -> List[str]:
    fails = []
    full = {
        "id": "SHAPE_READ.TEST",
        "geometry": "a geometry",
        "solving_for": "a quantity being distributed",
        "constraints": [{"name": "an enclosing volume", "sits": INTERNAL_UNIFORM,
                         "ratio": "dissipation / enclosure"}],
        "why_not_the_other_geometry": {"other_geometry": "spiral", "recovered_term": "angular momentum"},
        "removal_test": {"constraint": "the enclosure", "absent_in": "a case without one",
                         "observed_form": "something else", "result": DIFFERS},
        "scale_index": {"characteristic_scale": "a scale", "across_levels": "unknown"},
        "independent_recurrence": ["a", "b"],
        "status": TESTED,
        "provenance": {"concept": "MODEL", "record": "MODEL"},
    }
    if validate_read(full):
        fails.append(f"a complete shape read was rejected: {validate_read(full)[0]}")
    if classify(full) != "shape_entry":
        fails.append("a complete record did not classify as a shape entry")
    if audit([ShapeRead.from_dict(full)]):
        fails.append("a complete read produced findings")

    note = {k: v for k, v in full.items() if k != "removal_test"}
    if classify(note) != GEOMETRY_NOTE:
        fails.append("a record with no removal test did not classify as a geometry note")
    if missing_parts(note) != ["removal_test"]:
        fails.append("missing parts not reported")
    if not any("geometry note" in f for f in audit([ShapeRead.from_dict(note)])):
        fails.append("a geometry note was not marked as one")

    unchanged = {**full, "removal_test": {**full["removal_test"], "result": UNCHANGED}}
    if not any("not load-bearing" in e for e in validate_read(unchanged)):
        fails.append("an unchanged removal test with status 'tested' was accepted")
    if validate_read({**unchanged, "status": REFUTED}):
        fails.append("a refuted read was rejected — a failed transfer is a measurement")

    costed = ShapeRead.from_dict({**full, "constraints": [
        {"name": "the cost of pumping", "sits": INTERNAL_UNIFORM, "ratio": "cost / delivery"}]})
    if not any("dissipation" in f for f in audit([costed])):
        fails.append("a constraint stated as a cost was not flagged")
    disclaimed = ShapeRead.from_dict({**full, "constraints": [
        {"name": "work lost per unit delivered", "sits": INTERNAL_UNIFORM,
         "ratio": "dissipation / delivery", "note": "stated as dissipation, not as a cost"}]})
    if any("COST_FRAMING" in f for f in audit([disclaimed])):
        fails.append("the cost lint fired on a note disclaiming the cost framing")

    lengthy = ShapeRead.from_dict({**full, "constraints": [
        {"name": "capillary diameter", "sits": INTERNAL_UNIFORM}]})
    if not any("LENGTH_NOT_RATIO" in f for f in audit([lengthy])):
        fails.append("a length stated with no ratio was not flagged")

    terrain = ShapeRead.from_dict({**full, "solving_for": "the optimal routing of sediment",
                                   "constraints": [{"name": "whatever rock was hit",
                                                    "sits": EXTERNAL_HETEROGENEOUS}]})
    if not any("transcript of terrain" in f for f in audit([terrain])):
        fails.append("an external-constraint geometry read as an optimum was not flagged")

    bare = ShapeRead.from_dict({**full, "independent_recurrence": [], "scale_index": {}})
    findings = audit([bare])
    if not any("NO_RECURRENCE" in f for f in findings):
        fails.append("a read with no independent recurrence was not flagged")
    if not any("NO_SCALE_INDEX" in f for f in findings):
        fails.append("a read with no characteristic scale was not flagged")

    if not any("sits" in e for e in validate_read(
            {**full, "constraints": [{"name": "x", "sits": "somewhere"}]})):
        fails.append("a constraint with no stated class was accepted")

    shapes = classify_shapes_dir()
    if not shapes:
        fails.append("shapes/ produced no classification")
    if any(s["read_class"] != GEOMETRY_NOTE for s in shapes):
        fails.append("a file in shapes/ classified as a shape entry — none carries a constraint set")
    if any(s["declared"] != GEOMETRY_NOTE for s in shapes):
        fails.append("a file in shapes/ is not marked with its read class")

    # METHOD_SPEC section 5: confidence is a separate readout, and recurrence
    # alone may never raise it.
    if validate_read({**full, "confidence": {"value": 0.4, "comfort_threshold": 0.7,
                                             "basis": [REMOVAL_TEST_PASSED]}}):
        fails.append("a stated confidence with a legitimate basis was rejected")
    if not any("blocked misread wearing a number" in e for e in validate_read(
            {**full, "confidence": {"value": 0.9, "basis": [RECURRENCE_COUNT]}})):
        fails.append("confidence raised on recurrence count alone was accepted")
    if not validate_read({**full, "confidence": {"value": 2}}):
        fails.append("a confidence outside 0..1 was accepted")
    below = ShapeRead.from_dict({**full, "confidence": {"value": 0.4, "comfort_threshold": 0.7,
                                                        "basis": [REMOVAL_TEST_PASSED]}})
    if not any("do not resolve it" in f for f in audit([below])):
        fails.append("a read under its comfort threshold was not reported as uncoalesced")

    # section 3: a disappearance is the constraint set changing.
    dis = {**full, "status": REFUTED,
           "removal_test": {**full["removal_test"], "result": DIFFERS},
           "disappearances": [{"absent_from": "a market after a rule change", "since": "2026-01-01",
                               "bounded_candidates": ["the rule that changed"]}]}
    if not any("WRONG_FINDING" in f for f in audit([ShapeRead.from_dict(dis)])):
        fails.append("a read refuted on a disappearance was not flagged as the wrong finding")
    unbounded = ShapeRead.from_dict({**full, "disappearances": [{"absent_from": "somewhere"}]})
    if not any("UNBOUNDED" in f for f in audit([unbounded])):
        fails.append("an untimestamped disappearance was not flagged")
    untapped = ShapeRead.from_dict({**full, "disappearances": [
        {"absent_from": "somewhere", "since": "2026-01-01"}]})
    if not any("has not been used" in f for f in audit([untapped])):
        fails.append("a timestamped disappearance with no bounded candidates was not flagged")

    # section 3: substrate exclusion returns a null that reads as absence.
    excluded = ShapeRead.from_dict({**full, "sample_frame": {
        "admitted": ["termite colonies"],
        "excluded": [{"domain": "human settlement", "reason": "treated as a separate category"}]}})
    findings = audit([excluded])
    if not any("UNTESTED, not inapplicable" in f for f in findings):
        fails.append("an excluded domain was not reported as untested by construction")

    # section 4: the shadow read.
    shadow = {**full, "read_path": SHADOW, "geometry": "",
              "tangents": ["one gap", "another gap"], "outline_state": UNDER_OUTLINED,
              "status": MARKER}
    if validate_read(shadow):
        fails.append(f"a shadow read was rejected: {validate_read(shadow)[0]}")
    if not any("outline_state" in e for e in validate_read(
            {**full, "read_path": SHADOW, "tangents": ["g"]})):
        fails.append("a shadow read with no outline state was accepted")
    if not any("tangents" in e for e in validate_read({**full, "read_path": SHADOW})):
        fails.append("a shadow read with no tangents was accepted")
    if not any("not a failure" in e for e in validate_read({**shadow, "status": TESTED})):
        fails.append("an under-outlined shadow read was accepted as tested")
    sr_shadow = ShapeRead.from_dict(shadow)
    if not sr_shadow.consistency_exempt:
        fails.append("a shadow read was not exempted from consistency checking")
    if ShapeRead.from_dict(full).consistency_exempt:
        fails.append("a direct read was exempted from consistency checking")
    if not any("not competing claims" in f for f in audit([sr_shadow])):
        fails.append("an under-outlined shadow read did not say its tangents are not conflicts")
    if not any("shadow read" in e for e in validate_read({**full, "tangents": ["g"]})):
        fails.append("tangents on a direct read were accepted")

    if not (ROOT / "METHOD_SPEC.md").exists():
        fails.append("METHOD_SPEC.md is missing — it states the epistemic class and is read first")
    if not (ROOT / "READING_PROTOCOL.md").exists():
        fails.append("READING_PROTOCOL.md is missing")

    if validate_file():
        fails.append("shipped shape_reads.jsonl does not validate")
    if not load_reads():
        fails.append("no shape reads on file")
    if not (ROOT / SPEC).exists():
        fails.append(f"{SPEC} is missing — this module points at it rather than restating it")
    return fails


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="shape reads — the constraint set, not the geometry")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--validate", action="store_true")
    ap.add_argument("--audit", action="store_true")
    ap.add_argument("--classify-shapes", action="store_true",
                    help="classify every file in shapes/ as a shape entry or a geometry note")
    ap.add_argument("--path")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args(argv)

    if args.selftest:
        f = selftest()
        for line in f:
            print(f"FAIL  {line}")
        print("shape_read: OK" if not f else f"shape_read: {len(f)} FAILED")
        return 1 if f else 0

    path = pathlib.Path(args.path) if args.path else None

    if args.classify_shapes:
        rows = classify_shapes_dir()
        if args.json:
            print(json.dumps(rows, indent=2))
        else:
            print(f"\n  shapes/ — classified against {SPEC} section 10\n")
            for r in rows:
                print(f"  {r['file']:24s} {r['id']:16s} {r['read_class']}")
                if r["missing"]:
                    print(f"      missing: {', '.join(r['missing'])}")
            print("\n  A vertex count is a true statement about a polyhedron and says nothing")
            print("  about what problem the polyhedron solves. Marking, not criticism.\n")
        return 0

    if args.validate:
        errors = validate_file(path)
        if args.json:
            print(json.dumps({"errors": errors, "valid": not errors}, indent=2))
        else:
            for e in errors:
                print(f"  ✗  {e}")
            print("shape reads: VALID" if not errors else f"shape reads: {len(errors)} error(s)")
        return 1 if errors else 0

    if args.audit:
        findings = audit(load_reads(path))
        if args.json:
            print(json.dumps({"findings": findings}, indent=2))
        else:
            for x in findings:
                print(f"  {x}")
            print("shape read audit: CLEAN" if not findings else
                  f"shape read audit: {len(findings)} finding(s)")
        return 0

    rs = load_reads(path)
    if args.json:
        print(json.dumps([r.to_dict() for r in rs], indent=2))
    else:
        print(f"\n  SHAPE READS ({len(rs)}) — see {SPEC}\n")
        for r in rs:
            print(format_read(r))
            print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
