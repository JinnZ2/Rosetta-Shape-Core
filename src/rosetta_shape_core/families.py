# SPDX-License-Identifier: CC0-1.0
"""T2 — families: the physics base the operator is denominated in.

A family is one physical term. Nothing else. The nine seeded here are the
loads a body is under continuously from birth: gravity, pressure, gradient,
diffusion, thermal exchange, flow, resonance, phase, strain.

GROUNDING
    The vocabulary is proprioception-derived. The transducer that produced it
    was calibrated by these terms before any symbolic layer existed, so an
    entry written in this vocabulary is denominated in physics by
    construction — not by analogy drawn after the fact. That is the whole
    claim, and it is a claim about the instrument, not about resemblance.

FALSIFIER (stated, not defended)
    Every family must decompose to named physical terms. A family that cannot
    is mis-filed. ``audit_families()`` is that check. It is an audit, run
    against this file, and a finding is a correction to make here — not
    something to argue with.

CONSTRAINTS (repo-wide, restated per file)
    - no "about the author" / working-style section, in this or any file
    - entries are markers to explore, not positions defended; the correct
      response to one is: test fit / extend / report break
    - no moral labels in data structures, no intent attribution

Usage:
    python -m rosetta_shape_core.families --list
    python -m rosetta_shape_core.families --audit
    python -m rosetta_shape_core.families --term gravity
    python -m rosetta_shape_core.families --selftest
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from typing import Dict, Iterable, List, Optional

# ── the lexicon a family must decompose into ──────────────────────
#
# Named physical terms only: SI base quantities and named derived
# quantities. If a decomposition token is not in here, the family is
# mis-filed or the lexicon is short a term — both are findings.

BASE_TERMS = (
    "mass",
    "length",
    "time",
    "temperature",
    "amount_of_substance",
    "electric_charge",
)

DERIVED_TERMS = (
    "acceleration",
    "angular_frequency",
    "area",
    "chemical_potential",
    "concentration",
    "damping_coefficient",
    "density",
    "diffusivity",
    "displacement",
    "elastic_modulus",
    "energy",
    "entropy",
    "flux",
    "force",
    "free_energy",
    "frequency",
    "gravitational_field",
    "heat_capacity",
    "latent_heat",
    "momentum",
    "power",
    "pressure",
    "stress",
    "surface_tension",
    "thermal_conductivity",
    "velocity",
    "viscosity",
    "volume",
    "work",
)

PHYSICAL_TERMS = frozenset(BASE_TERMS + DERIVED_TERMS)


@dataclass(frozen=True)
class Family:
    """One physical term, plus the named terms it decomposes to."""

    id: str
    term: str
    decomposition: tuple = ()
    aliases: tuple = ()
    note: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


def _f(id_: str, term: str, decomposition: Iterable[str], aliases: Iterable[str] = (), note: str = "") -> Family:
    return Family(id_, term, tuple(decomposition), tuple(aliases), note)


SEED_FAMILIES: List[Family] = [
    _f(
        "GRAVITY_LOAD",
        "body force acting on every element of a mass, and the load path that carries it",
        ["mass", "acceleration", "force", "gravitational_field", "length", "stress"],
        ["gravity", "load", "weight"],
        note="constant, unshielded, and the same term for grass, crystal and body",
    ),
    _f(
        "PRESSURE",
        "normal force per unit area transmitted through a medium",
        ["force", "area", "energy", "volume"],
        ["compression"],
    ),
    _f(
        "GRADIENT",
        "spatial rate of change of a scalar quantity",
        ["length", "concentration", "temperature", "pressure", "chemical_potential"],
        ["slope"],
        note="decomposes only relative to the quantity being graded — name that quantity in the entry",
    ),
    _f(
        "DIFFUSION",
        "flux of a quantity down its own gradient",
        ["concentration", "diffusivity", "flux", "area", "time", "length"],
        ["dispersion"],
    ),
    _f(
        "THERMAL_EXCHANGE",
        "energy transfer driven by a temperature difference",
        ["temperature", "energy", "heat_capacity", "thermal_conductivity", "area", "time"],
        ["thermal", "heat"],
    ),
    _f(
        "FLOW",
        "bulk transport of mass and momentum through or around a body",
        ["mass", "velocity", "momentum", "density", "viscosity", "volume", "time"],
        ["current", "advection"],
    ),
    _f(
        "RESONANCE",
        "response of a driven system peaking near a natural frequency",
        ["frequency", "angular_frequency", "damping_coefficient", "mass", "elastic_modulus", "energy"],
        ["oscillation", "vibration"],
    ),
    _f(
        "PHASE",
        "reorganization of state at a critical value of a control parameter",
        ["temperature", "pressure", "latent_heat", "entropy", "free_energy"],
        ["transition", "state_change"],
    ),
    _f(
        "STRAIN",
        "deformation measured against a reference length",
        ["length", "displacement", "stress", "elastic_modulus", "energy", "surface_tension"],
        ["deformation", "stretch"],
    ),
]

FAMILIES: Dict[str, Family] = {f.id: f for f in SEED_FAMILIES}

_ALIASES: Dict[str, str] = {}


def _reindex() -> None:
    _ALIASES.clear()
    for fam in FAMILIES.values():
        _ALIASES[fam.id.lower()] = fam.id
        for a in fam.aliases:
            _ALIASES[a.lower()] = fam.id
        for part in fam.id.lower().split("_"):
            _ALIASES.setdefault(part, fam.id)


_reindex()


def register_family(family: Family, *, replace: bool = False) -> Family:
    """Add a family. The list is open — '+ yours' is part of the spec.

    Raises ValueError on a duplicate id unless ``replace=True``, and on a
    decomposition that does not reach named physical terms, because that is
    the falsifier and it is cheaper to enforce at the door.
    """
    if not replace and family.id in FAMILIES:
        raise ValueError(f"family already registered: {family.id}")
    findings = audit_family(family)
    if findings:
        raise ValueError("; ".join(findings))
    FAMILIES[family.id] = family
    _reindex()
    return family


def resolve(term: str) -> Optional[str]:
    """Map a loose term ('gravity', 'heat', 'STRAIN') to a family id."""
    if not term:
        return None
    key = str(term).strip().lower()
    if key in _ALIASES:
        return _ALIASES[key]
    return None


def audit_family(family: Family) -> List[str]:
    """The falsifier, applied to one family."""
    findings = []
    if not family.id or family.id != family.id.upper():
        findings.append(f"{family.id!r}: id must be uppercase")
    if not family.term:
        findings.append(f"{family.id}: no physical term stated")
    if not family.decomposition:
        findings.append(f"{family.id}: mis-filed — decomposes to nothing")
    for token in family.decomposition:
        if token not in PHYSICAL_TERMS:
            findings.append(
                f"{family.id}: mis-filed — '{token}' is not a named physical term "
                f"(add it to PHYSICAL_TERMS or re-file the family)"
            )
    return findings


def audit_families(families: Optional[Dict[str, Family]] = None) -> List[str]:
    """Run the falsifier over the whole list. Empty return = nothing mis-filed."""
    fams = FAMILIES if families is None else families
    findings: List[str] = []
    for fid in sorted(fams):
        findings.extend(audit_family(fams[fid]))
    return findings


def format_families(families: Optional[Dict[str, Family]] = None) -> str:
    fams = FAMILIES if families is None else families
    lines = []
    for fid in sorted(fams):
        fam = fams[fid]
        lines.append(f"  {fid}")
        lines.append(f"      term    {fam.term}")
        lines.append(f"      →       {', '.join(fam.decomposition)}")
        if fam.note:
            lines.append(f"      note    {fam.note}")
    return "\n".join(lines)


# ── selftest ──────────────────────────────────────────────────────

def selftest() -> List[str]:
    """Assertions this module must survive. Returns failures (empty = OK)."""
    fails = []
    if audit_families():
        fails.append("seed families do not survive their own falsifier")
    if resolve("gravity") != "GRAVITY_LOAD":
        fails.append("alias resolution broken for 'gravity'")
    if resolve("heat") != "THERMAL_EXCHANGE":
        fails.append("alias resolution broken for 'heat'")
    if resolve("nonsense_term") is not None:
        fails.append("resolve() invented a family")
    bad = Family("VIBES", "a feeling about a system", ("mood",))
    if not audit_family(bad):
        fails.append("falsifier failed to catch a family with no physical decomposition")
    if len(FAMILIES) < 9:
        fails.append("seed family list is short")
    return fails


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="T2 families — the physics base")
    ap.add_argument("--list", action="store_true", help="print the family list")
    ap.add_argument("--audit", action="store_true", help="run the falsifier")
    ap.add_argument("--term", help="resolve a loose term to a family id")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args(argv)

    if args.selftest:
        fails = selftest()
        for f in fails:
            print(f"FAIL  {f}")
        print("families: OK" if not fails else f"families: {len(fails)} FAILED")
        return 1 if fails else 0

    if args.term:
        fid = resolve(args.term)
        if args.json:
            print(json.dumps({"query": args.term, "family": fid}, indent=2))
        elif fid:
            print(f"{args.term} → {fid}")
            print(format_families({fid: FAMILIES[fid]}))
        else:
            print(f"{args.term} → (no family; add one with register_family)")
        return 0 if fid else 1

    if args.audit:
        findings = audit_families()
        if args.json:
            print(json.dumps({"findings": findings, "clean": not findings}, indent=2))
        else:
            for f in findings:
                print(f"  MIS-FILED  {f}")
            print("families audit: CLEAN" if not findings else f"families audit: {len(findings)} finding(s)")
        return 1 if findings else 0

    if args.json:
        print(json.dumps({fid: FAMILIES[fid].to_dict() for fid in sorted(FAMILIES)}, indent=2))
    else:
        print(f"\n  FAMILIES ({len(FAMILIES)}) — one physical term each\n")
        print(format_families())
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
