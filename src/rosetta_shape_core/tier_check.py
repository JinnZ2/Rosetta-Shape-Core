# SPDX-License-Identifier: CC0-1.0
"""Tier check — keep ways of knowing out of the domains-of-the-world set.

    f01-f20  are domains OF the world.
    a01..    are domains of REPRESENTATIONS of it, or routes by which a
             reading is obtained.

Different tier. Not a further face. F21 (narrative-constraint) was never
overflow past the icosahedron's twentieth face — it was the first member of
a second set, written into the first set's file format because that was the
only format available. Two of the three files that describe the family set
had already excluded it without anyone deciding to: ontology/index.json
counts twenty and never listed it, and _id_registry.json read "F01-F20".
Only family_map.json carried it.

STATUS: MARKER UNDER EXPLORATION. Not a settled ontology. Expected to change
after experiment. This module reports; it is not an invariant to enforce.

WHAT THIS DOES NOT DO
    No face assignment on the access tier. No fixed count, no polytope
    closure, no duality or incidence check. No solid is re-derived from the
    number of files present. The access tier admits new members without
    restructuring, and that is the requirement rather than a limitation.

CHECKS
    fail   a way of knowing filed in ontology/families/
    fail   an access entry with no breaks_when. An access entry with no
           stated break point is a preference, not an access mode
    warn   cost=free with lands_on=measured — cheap travel to an expensive
           destination. That mismatch IS the detector; no judgement term
           is needed
    warn   an entry that claims a domain and names no access

CONSTRAINTS (repo-wide, restated per file)
    - no "about the author" / working-style section, in this or any file
    - entries are markers to explore, not positions defended; the correct
      response to one is: test fit / extend / report break
    - no moral labels in data structures, no intent attribution

Usage:
    python -m rosetta_shape_core.tier_check
    python -m rosetta_shape_core.tier_check --json
    python -m rosetta_shape_core.tier_check --selftest
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys
from typing import Any, Dict, List, Optional

ROOT = pathlib.Path(__file__).resolve().parents[2]
FAMILIES_DIR = ROOT / "ontology" / "families"
ACCESS_DIR = ROOT / "ontology" / "access"

FAIL = "FAIL"
WARN = "WARN"

# Vocabulary that marks a record as describing a REPRESENTATION of the world
# rather than the world. Deliberately narrow: measurement, information and
# consciousness are domains of the world and must not trip this. What trips it
# is an account, a claim, a story — something with a teller.
WAY_OF_KNOWING_MARKERS = (
    "narrative", "testimony", "account", "rationalization", "in-group", "ingroup",
    "out-group", "outgroup", "framing", "doctrine", "propaganda", "manipulation",
    "selective application", "self-report", "belief", "story", "hearsay",
    "representation of", "way of knowing",
)

# Families checked against the markers and kept in the domain set on purpose.
# This is a record of a decision, not a way to silence the check: a family
# only belongs here with a reason, and the reason is the useful part.
REVIEWED_AS_DOMAIN: Dict[str, str] = {
    # (empty — no f01-f20 family currently trips a marker; see selftest)
}


def _load(p: pathlib.Path) -> Optional[Dict[str, Any]]:
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError, OSError):
        return None


def family_files() -> List[pathlib.Path]:
    if not FAMILIES_DIR.exists():
        return []
    return sorted(p for p in FAMILIES_DIR.glob("*.json") if not p.name.startswith("_"))


def access_files() -> List[pathlib.Path]:
    """Access tier members. Underscore-prefixed files are not members."""
    if not ACCESS_DIR.exists():
        return []
    return sorted(p for p in ACCESS_DIR.glob("*.json") if not p.name.startswith("_"))


def marks_way_of_knowing(record: Dict[str, Any]) -> List[str]:
    """Which markers a record trips. Empty = reads as a domain of the world."""
    haystack = " ".join([
        str(record.get("name", "")),
        str(record.get("domain", "")),
        str(record.get("core_insight", "")),
        " ".join(str(t) for t in record.get("tags", [])),
    ]).lower()
    return [m for m in WAY_OF_KNOWING_MARKERS if m in haystack]


# ── the four checks ───────────────────────────────────────────────

def check_families_are_domains(files: Optional[List[pathlib.Path]] = None) -> List[str]:
    """FAIL: a way of knowing filed in ontology/families/."""
    findings = []
    for p in (family_files() if files is None else files):
        record = _load(p)
        if record is None:
            findings.append(f"{FAIL}  {p.name}: does not parse")
            continue
        fid = record.get("id", p.stem)
        if fid in REVIEWED_AS_DOMAIN:
            continue
        tripped = marks_way_of_knowing(record)
        if tripped:
            findings.append(
                f"{FAIL}  {p.name} ({fid}): reads as a way of knowing, not a domain of the world "
                f"— {', '.join(tripped)}. f01-f20 are domains OF the world; a domain of "
                f"representations of it belongs in ontology/access/. If it is genuinely a domain, "
                f"add it to REVIEWED_AS_DOMAIN with the reason."
            )
    return findings


def check_access_states_a_break(files: Optional[List[pathlib.Path]] = None) -> List[str]:
    """FAIL: an access entry with no breaks_when."""
    findings = []
    for p in (access_files() if files is None else files):
        record = _load(p)
        if record is None:
            findings.append(f"{FAIL}  {p.name}: does not parse")
            continue
        aid = record.get("id", p.stem)
        breaks = record.get("breaks_when")
        if breaks is None or not str(breaks).strip():
            findings.append(
                f"{FAIL}  {p.name} ({aid}): breaks_when is null or empty. An access entry with no "
                f"stated break point is a preference, not an access mode."
            )
    return findings


def check_cost_lands_on_mismatch(files: Optional[List[pathlib.Path]] = None) -> List[str]:
    """WARN: cost=free, lands_on=measured — cheap travel to an expensive destination."""
    findings = []
    for p in (access_files() if files is None else files):
        record = _load(p) or {}
        if record.get("cost") == "free" and record.get("lands_on") == "measured":
            findings.append(
                f"{WARN}  {p.name} ({record.get('id', p.stem)}): cost=free lands_on=measured — "
                f"cheap travel to an expensive destination. The mismatch is the reading; nothing "
                f"further is claimed about it."
            )
    return findings


def check_domain_claims_name_an_access(entries: Optional[List[Any]] = None) -> List[str]:
    """WARN: an entry claims a domain and names no access it was reached by."""
    if entries is None:
        from rosetta_shape_core.entry import load_entries
        entries = load_entries()
    findings = []
    for e in entries:
        if getattr(e, "domain", "") and not getattr(e, "access", ""):
            findings.append(
                f"{WARN}  {e.key}: claims domain {e.domain} and names no access. How the reading "
                f"was obtained is unrecorded — 'unmarked' is a legitimate answer, a missing field "
                f"is not the same thing."
            )
    return findings


ALL_CHECKS = (
    check_families_are_domains,
    check_access_states_a_break,
    check_cost_lands_on_mismatch,
    check_domain_claims_name_an_access,
)


def run() -> Dict[str, List[str]]:
    findings: List[str] = []
    for check in ALL_CHECKS:
        findings.extend(check())
    return {
        "fail": [f for f in findings if f.startswith(FAIL)],
        "warn": [f for f in findings if f.startswith(WARN)],
        "families": [p.name for p in family_files()],
        "access": [p.name for p in access_files()],
    }


def format_report(r: Dict[str, List[str]]) -> str:
    lines = ["", "  TIER CHECK — domains of the world vs ways of knowing", ""]
    lines.append(f"  ontology/families/   {len(r['families'])} domain(s) of the world")
    lines.append(f"  ontology/access/     {len(r['access'])} access mode(s) — open tier, no count implied")
    lines.append("")
    for f in r["fail"]:
        lines.append(f"  {f}")
    for w in r["warn"]:
        lines.append(f"  {w}")
    lines.append("")
    lines.append("  tier check: CLEAN" if not r["fail"] else f"  tier check: {len(r['fail'])} FAIL")
    lines.append("  status: MARKER UNDER EXPLORATION — reported, not enforced as an invariant.")
    lines.append("")
    return "\n".join(lines)


# ── selftest ──────────────────────────────────────────────────────

def selftest() -> List[str]:
    fails = []

    # The record that motivated the tier, as it was filed under families/.
    f21_as_filed = {
        "id": "FAMILY.F21",
        "name": "Narrative-Constraint",
        "domain": "Constraint consistency, selective application detection, symmetry of rules",
        "tags": ["constraint", "manipulation-detection", "narrative-physics"],
    }
    if not marks_way_of_knowing(f21_as_filed):
        fails.append("the record that motivated the tier does not trip the detector")

    # Domains of the world that must NOT trip it, or the check is useless.
    for record in (
        {"id": "FAMILY.F14", "name": "Measurement",
         "domain": "Uncertainty quantification, calibration, error propagation, dimensional analysis"},
        {"id": "FAMILY.F03", "name": "Information",
         "domain": "Shannon entropy, coding theory, information measures, channel capacity"},
        {"id": "FAMILY.F16", "name": "Consciousness",
         "domain": "Integrated information, global workspace, neural oscillations, predictive coding"},
    ):
        if marks_way_of_knowing(record):
            fails.append(f"{record['id']} trips the detector — measurement and information are "
                         f"domains of the world, not accounts of it")

    if check_families_are_domains():
        fails.append("a shipped family reads as a way of knowing")
    if check_access_states_a_break():
        fails.append("a shipped access entry has no stated break point")

    import tempfile
    with tempfile.TemporaryDirectory() as td:
        d = pathlib.Path(td)
        (d / "a99-no-break.json").write_text(json.dumps(
            {"id": "a99", "name": "x", "tier": "access", "breaks_when": None}), encoding="utf-8")
        if not check_access_states_a_break([d / "a99-no-break.json"]):
            fails.append("an access entry with null breaks_when was accepted")
        (d / "a98-empty-break.json").write_text(json.dumps(
            {"id": "a98", "name": "x", "tier": "access", "breaks_when": "   "}), encoding="utf-8")
        if not check_access_states_a_break([d / "a98-empty-break.json"]):
            fails.append("an access entry with a whitespace breaks_when was accepted")
        (d / "f99-narrative.json").write_text(json.dumps(f21_as_filed), encoding="utf-8")
        if not check_families_are_domains([d / "f99-narrative.json"]):
            fails.append("a way of knowing filed under families/ was accepted")

    # a01 is the flag the spec named: free cost, measured claim.
    warned = check_cost_lands_on_mismatch()
    if not warned:
        fails.append("a01 free/measured did not raise the mismatch warning")
    if not check_cost_lands_on_mismatch([]) == []:
        fails.append("the mismatch check invented a finding")

    from rosetta_shape_core.entry import Entry
    claimed = Entry(source_system="x", configuration="y", id="ENTRY.X", domain="f05")
    if not check_domain_claims_name_an_access([claimed]):
        fails.append("an entry claiming a domain with no access was not flagged")
    both = Entry(source_system="x", configuration="y", id="ENTRY.X", domain="f05", access="a01")
    if check_domain_claims_name_an_access([both]):
        fails.append("an entry naming both a domain and an access was flagged")

    if len(family_files()) != 20:
        fails.append(f"ontology/families/ holds {len(family_files())} files, expected f01-f20")
    if not access_files():
        fails.append("the access tier is empty")
    return fails


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="tier check — domains of the world vs ways of knowing")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args(argv)

    if args.selftest:
        f = selftest()
        for line in f:
            print(f"FAIL  {line}")
        print("tier_check: OK" if not f else f"tier_check: {len(f)} FAILED")
        return 1 if f else 0

    r = run()
    print(json.dumps(r, indent=2) if args.json else format_report(r))
    return 1 if r["fail"] else 0


if __name__ == "__main__":
    sys.exit(main())
