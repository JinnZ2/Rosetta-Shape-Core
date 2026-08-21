# SPDX-License-Identifier: CC0-1.0
"""gap_scan — recover the shape of what a metaphor hides.

Fad detection is not the output. It is the access method. The substrate
metaphor of a closed era is legible precisely because the era ended; running
the scan on closed instances recovers the SHAPE of what a metaphor hides,
and that shape is then the only handle available on the current one, where
the same structure is illegible from inside.

HOLDS WHERE
    a metaphor is doing cosmological or explanatory work AND the era's
    dominant artifact is identifiable. Not restricted to any one framework —
    any explanatory account qualifies, including a stack's own account of
    cognition.

DEGRADES WHERE
    there is no dominant artifact, or the artifact is the object of study
    rather than the source of the metaphor.

NON-TRANSFERABLE
    the SPECIFIC gap. Only the shape class transfers — missing slot,
    imported boundary, substrate ceiling, unlocatable exterior.
    Instantiating one requires the current instance's own operands, which
    is why this module ships closed examples and no open ones.

WHICH AXIS THIS IS
    Rosetta   cross-DOMAIN     crystal -> your problem
    Mandala   cross-SCALE      grass -> ecosystem
    gap_scan  cross-INSTANCE   a closed era -> the current one

    This is a third axis and it is not Rosetta's. It sits in this repo
    because it shares the entry discipline — named operands, provenance per
    operand, a stated scope — and not because it is part of the operator.
    An instance is not a domain: do not read a gap_scan result as a
    transfer, and do not fold the two.

CO-VARYING AXES (per instance)
    material environment   what the era physically ran on
    artifact               its most impressive machine
    science-as-practised   what counted as a result
    epistemology           what counted as knowing at all

SHAPE CLASSES
    G1  missing_slot        what the criterion cannot register
    G2  imported_boundary   operands traced to apparatus, not to measurement
    G3  substrate_ceiling   world-capability set == artifact-capability set
    G4  exterior            frame requires an outside it cannot locate

The scan derives nothing it was not given. Probes are supplied, not divined:
G1 is only as sharp as the terms someone thought to test against the
criterion, which is exactly why closed instances are the training ground.

CONSTRAINTS (repo-wide, restated per file)
    - no "about the author" / working-style section, in this or any file
    - entries are markers to explore, not positions defended; the correct
      response to one is: test fit / extend / report break
    - no moral labels in data structures, no intent attribution
      (an era is never scored as naive; a gap is a structural readout)

Usage:
    python -m rosetta_shape_core.gap_scan --list
    python -m rosetta_shape_core.gap_scan --example clockwork
    python -m rosetta_shape_core.gap_scan --input path/to/instance.json --json
    python -m rosetta_shape_core.gap_scan --selftest
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional

ROOT = pathlib.Path(__file__).resolve().parents[2]
INSTANCES_DIR = ROOT / "data" / "rosetta" / "gap_scan"

MEASURED = "MEASURED"
APPARATUS = "APPARATUS"
UNTRACED = "UNTRACED"
PROVENANCES = (MEASURED, APPARATUS, UNTRACED)


@dataclass
class Operand:
    """One quantity the frame runs on, and where it came from."""

    name: str
    provenance: str = UNTRACED
    note: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Frame:
    """The explanatory claim under test."""

    claim: str
    requires: List[str] = field(default_factory=list)
    world_capabilities: List[str] = field(default_factory=list)
    exterior: str = ""
    exterior_required: bool = False


@dataclass
class Artifact:
    """The era's dominant machine, and what it can do."""

    name: str
    capabilities: List[str] = field(default_factory=list)


@dataclass
class Criterion:
    """What counts as understanding, and what it can register."""

    name: str
    registers: List[str] = field(default_factory=list)


@dataclass
class Gap:
    """One shape class, fired or not."""

    id: str
    name: str
    fired: bool
    items: List[str] = field(default_factory=list)
    reading: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class GapReport:
    instance: str = ""
    era: str = ""
    gaps: List[Gap] = field(default_factory=list)
    provenance: Dict[str, str] = field(default_factory=dict)
    axes: Dict[str, str] = field(default_factory=dict)
    record_provenance: Dict[str, Any] = field(default_factory=dict)

    @property
    def fired(self) -> List[str]:
        return [g.id for g in self.gaps if g.fired]

    def to_dict(self) -> dict:
        return {
            "instance": self.instance,
            "era": self.era,
            "axes": self.axes,
            "gaps": [g.to_dict() for g in self.gaps],
            "provenance": self.provenance,
            "record_provenance": self.record_provenance,
            "fired": self.fired,
        }


# ── the four shape classes ────────────────────────────────────────

def g1_missing_slot(frame: Frame, criterion: Criterion, probes: Optional[List[str]] = None) -> Gap:
    """What the criterion cannot register — of what the frame needs, plus probes."""
    tested = list(frame.requires) + list(probes or [])
    registers = set(criterion.registers)
    missing = [t for t in dict.fromkeys(tested) if t not in registers]
    return Gap(
        "G1", "missing_slot", bool(missing), missing,
        reading=(
            f"{len(missing)} term(s) the criterion has no slot for. A result stated in these "
            f"terms cannot count as understanding under '{criterion.name}', so the frame does "
            f"not lose to them — it does not meet them."
        ) if missing else f"every term tested has a slot under '{criterion.name}' — "
                          f"either the criterion is wide, or the probes came from inside it",
    )


def g2_imported_boundary(operands: List[Operand]) -> Gap:
    """Operands traced to the apparatus rather than to a measurement."""
    imported = [o for o in operands if o.provenance != MEASURED]
    items = [f"{o.name} [{o.provenance}]" + (f" — {o.note}" if o.note else "") for o in imported]
    return Gap(
        "G2", "imported_boundary", bool(imported), items,
        reading=(
            "these quantities entered from the apparatus or arrived untraced. A boundary the "
            "machine has becomes a boundary the world is said to have, without a measurement "
            "in between."
        ) if imported else "every operand traces to a measurement — no boundary imported from the apparatus",
    )


def g3_substrate_ceiling(frame: Frame, artifact: Artifact) -> Gap:
    """World-capability set == artifact-capability set."""
    world = set(frame.world_capabilities)
    machine = set(artifact.capabilities)
    beyond = sorted(world - machine)
    ceiling = bool(world) and not beyond
    shared = sorted(world & machine)
    return Gap(
        "G3", "substrate_ceiling", ceiling, shared if ceiling else beyond,
        reading=(
            f"the world is granted no capability that {artifact.name} lacks. The ceiling on what "
            f"the world can do sits exactly at the ceiling of the era's machine, which is a fact "
            f"about the machine."
        ) if ceiling else (
            f"the frame grants the world {len(beyond)} capability(s) beyond {artifact.name} — "
            f"no ceiling at the substrate"
        ) if beyond else "no world capabilities declared — nothing to compare against the artifact",
    )


def g4_exterior(frame: Frame, criterion: Criterion, operands: List[Operand]) -> Gap:
    """Does the frame require an outside it cannot locate?"""
    if not frame.exterior_required:
        return Gap("G4", "exterior", False, [], reading="the frame declares no required exterior")
    locatable = frame.exterior in set(criterion.registers)
    measured = {o.name for o in operands if o.provenance == MEASURED}
    locatable = locatable or frame.exterior in measured
    return Gap(
        "G4", "exterior", not locatable, [frame.exterior],
        reading=(
            f"the frame requires '{frame.exterior}' and the criterion cannot locate it: not "
            f"registered, not measured. The frame is closed only by a term it cannot reach."
        ) if not locatable else f"'{frame.exterior}' is locatable — registered or measured, so the frame closes",
    )


def scan(
    frame: Frame,
    artifact: Artifact,
    criterion: Criterion,
    operands: List[Operand],
    *,
    probes: Optional[List[str]] = None,
    instance: str = "",
    era: str = "",
    axes: Optional[Dict[str, str]] = None,
    record_provenance: Optional[Dict[str, Any]] = None,
) -> GapReport:
    """Run all four shape classes. Deterministic; derives nothing it was not given."""
    return GapReport(
        instance=instance,
        era=era,
        gaps=[
            g1_missing_slot(frame, criterion, probes),
            g2_imported_boundary(operands),
            g3_substrate_ceiling(frame, artifact),
            g4_exterior(frame, criterion, operands),
        ],
        provenance={o.name: o.provenance for o in operands},
        axes=dict(axes or {}),
        record_provenance=dict(record_provenance or {}),
    )


# ── io ────────────────────────────────────────────────────────────

def parse_instance(d: Dict[str, Any]) -> Dict[str, Any]:
    """Turn an instance dict into scan() arguments."""
    f = d.get("frame", {})
    a = d.get("artifact", {})
    c = d.get("criterion", {})
    return {
        "frame": Frame(
            claim=f.get("claim", ""),
            requires=list(f.get("requires", [])),
            world_capabilities=list(f.get("world_capabilities", [])),
            exterior=f.get("exterior", ""),
            exterior_required=bool(f.get("exterior_required", bool(f.get("exterior")))),
        ),
        "artifact": Artifact(name=a.get("name", ""), capabilities=list(a.get("capabilities", []))),
        "criterion": Criterion(name=c.get("name", ""), registers=list(c.get("registers", []))),
        "operands": [Operand(o.get("name", ""), o.get("provenance", UNTRACED), o.get("note", "")) for o in d.get("operands", [])],
        "probes": list(d.get("probes", [])),
        "instance": d.get("instance", ""),
        "era": d.get("era", ""),
        "axes": dict(d.get("axes", {})),
        "record_provenance": dict(d.get("provenance", {})),
    }


def validate_instance(d: Dict[str, Any]) -> List[str]:
    from rosetta_shape_core.provenance import validate as validate_provenance

    errors = validate_provenance(d.get("provenance"), where=f"instance {d.get('instance', '?')}")
    for key in ("frame", "artifact", "criterion"):
        if key not in d:
            errors.append(f"missing section: {key}")
    if not d.get("frame", {}).get("claim"):
        errors.append("frame.claim is empty — there is no explanatory claim under test")
    if not d.get("artifact", {}).get("name"):
        errors.append("artifact.name is empty — the scan degrades where no dominant artifact is identifiable")
    for i, o in enumerate(d.get("operands", [])):
        if o.get("provenance", UNTRACED) not in PROVENANCES:
            errors.append(f"operands[{i}] provenance {o.get('provenance')!r} not one of {PROVENANCES}")
        if not o.get("name"):
            errors.append(f"operands[{i}] has no name")
    return errors


def list_instances() -> List[pathlib.Path]:
    if not INSTANCES_DIR.exists():
        return []
    return sorted(INSTANCES_DIR.glob("*.json"))


def load_instance(name_or_path: str) -> Dict[str, Any]:
    p = pathlib.Path(name_or_path)
    if not p.exists():
        p = INSTANCES_DIR / f"{name_or_path}.json"
    if not p.exists():
        raise FileNotFoundError(f"no instance: {name_or_path}")
    return json.loads(p.read_text(encoding="utf-8"))


def scan_instance(name_or_path: str) -> GapReport:
    d = load_instance(name_or_path)
    errors = validate_instance(d)
    if errors:
        raise ValueError("; ".join(errors))
    return scan(**parse_instance(d))


def format_report(r: GapReport) -> str:
    lines = ["", f"  GAP SCAN — {r.instance or '(unnamed instance)'}"]
    if r.era:
        lines.append(f"  era        {r.era}")
    if r.record_provenance:
        lines.append(f"  record     concept {r.record_provenance.get('concept', '?')} / "
                     f"record {r.record_provenance.get('record', '?')}")
    for k in ("material_environment", "artifact", "science_as_practised", "epistemology"):
        if k in r.axes:
            lines.append(f"  {k:24s} {r.axes[k]}")
    lines.append("")
    for g in r.gaps:
        mark = "●" if g.fired else "○"
        lines.append(f"  {mark} {g.id}  {g.name}")
        for item in g.items:
            lines.append(f"        - {item}")
        lines.append(f"        {g.reading}")
        lines.append("")
    if r.provenance:
        lines.append("  OPERAND PROVENANCE")
        for name, prov in r.provenance.items():
            lines.append(f"        {prov:<10s} {name}")
        lines.append("")
    lines.append(f"  fired: {', '.join(r.fired) if r.fired else '(none)'}")
    lines.append("")
    return "\n".join(lines)


# ── selftest ──────────────────────────────────────────────────────

def selftest() -> List[str]:
    fails = []

    if not validate_instance({"frame": {"claim": "c"}, "artifact": {"name": "a"}, "criterion": {}}):
        fails.append("instance with no provenance accepted")

    frame = Frame("test claim", requires=["a", "b"], world_capabilities=["x", "y"],
                  exterior="the setter", exterior_required=True)
    art = Artifact("test machine", capabilities=["x", "y", "z"])
    crit = Criterion("test criterion", registers=["a"])
    ops = [Operand("m", MEASURED), Operand("k", APPARATUS, "read off the machine"), Operand("u", UNTRACED)]

    r = scan(frame, art, crit, ops, probes=["c"])
    g = {x.id: x for x in r.gaps}

    if not g["G1"].fired or g["G1"].items != ["b", "c"]:
        fails.append("G1 did not report exactly the unregistered terms")
    if not g["G2"].fired or len(g["G2"].items) != 2:
        fails.append("G2 did not report the non-MEASURED operands")
    if not g["G3"].fired:
        fails.append("G3 missed a world-capability set inside the artifact's")
    if not g["G4"].fired:
        fails.append("G4 missed an unlocatable required exterior")

    no_ceiling = scan(Frame("c", world_capabilities=["x", "beyond"]), art, crit, [])
    if {x.id: x for x in no_ceiling.gaps}["G3"].fired:
        fails.append("G3 fired when the world exceeds the artifact")

    locatable = scan(Frame("c", exterior="m", exterior_required=True), art, crit, [Operand("m", MEASURED)])
    if {x.id: x for x in locatable.gaps}["G4"].fired:
        fails.append("G4 fired on an exterior that is measured")

    clean = scan(Frame("c", requires=["a"]), art, Criterion("wide", registers=["a"]), [Operand("m", MEASURED)])
    if clean.fired:
        fails.append("a frame with no gaps still fired a class")

    if not list_instances():
        fails.append("no closed instances shipped in data/rosetta/gap_scan/")
    for p in list_instances():
        d = json.loads(p.read_text(encoding="utf-8"))
        errs = validate_instance(d)
        if errs:
            fails.append(f"{p.name}: {errs[0]}")
            continue
        rep = scan_instance(str(p))
        if not rep.fired:
            fails.append(f"{p.name}: closed instance fired no gap class — the example is not doing its job")
    if not validate_instance({"frame": {"claim": ""}, "artifact": {}, "criterion": {}}):
        fails.append("validate_instance accepted an instance with no claim and no artifact")
    if not validate_instance({"frame": {"claim": "c"}, "artifact": {"name": "a"}, "criterion": {},
                              "operands": [{"name": "o", "provenance": "GUESSED"}]}):
        fails.append("validate_instance accepted an unknown provenance")
    return fails


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="gap_scan — four shape classes over an explanatory frame")
    ap.add_argument("--input", help="instance JSON file")
    ap.add_argument("--example", help="a shipped closed instance by name")
    ap.add_argument("--list", action="store_true", help="list shipped closed instances")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args(argv)

    if args.selftest:
        f = selftest()
        for line in f:
            print(f"FAIL  {line}")
        print("gap_scan: OK" if not f else f"gap_scan: {len(f)} FAILED")
        return 1 if f else 0

    if args.list or not (args.input or args.example):
        paths = list_instances()
        if args.json:
            print(json.dumps([p.stem for p in paths], indent=2))
        else:
            print("\n  CLOSED INSTANCES (the era ended, so the metaphor is legible)\n")
            for p in paths:
                d = json.loads(p.read_text(encoding="utf-8"))
                print(f"  {p.stem:<18s} {d.get('instance', '')}  —  {d.get('era', '')}")
            print("\n  Open instances are not shipped: the specific gap is non-transferable,")
            print("  and instantiating one requires the current instance's own operands.\n")
        return 0

    target = args.input or args.example
    try:
        report = scan_instance(target)
    except (FileNotFoundError, ValueError) as exc:
        print(f"gap_scan: {exc}")
        return 1
    print(json.dumps(report.to_dict(), indent=2) if args.json else format_report(report))
    return 0


if __name__ == "__main__":
    sys.exit(main())
