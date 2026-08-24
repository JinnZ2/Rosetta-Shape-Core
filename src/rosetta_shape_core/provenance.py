# SPDX-License-Identifier: CC0-1.0
"""Provenance — where a record came from, applied to this repo's own records.

The operator stack already demands operand provenance of everything it
looks at (gap_scan G2: a boundary traced to the apparatus rather than to a
measurement). Shipping model-seeded content unmarked inside that stack is
the same failure, one level up: a later reader — including anyone applying
the reading protocol in docs/reading-protocol.md — takes every record as
authored, because nothing on the record says otherwise.

So every entry, family and scan instance carries two origins:

    concept   where the thing being recorded came from
    record    who wrote the record text as it now stands

Both are needed because they routinely differ. A source system named by the
repo author, written up during a build session, is AUTHOR concept and MODEL
record — and reading it as fully authored overstates it while reading it as
fully generated erases the author.

ORIGINS
    AUTHOR   the repo author's own material
    SPEC     arrived with a build specification for this work
    MODEL    seeded by a model during a build; not the author's material
    PUBLIC   an established result in the public record — a theorem, a
             measured phenomenon — attributable to no party here

This is origin data only. It carries no ranking: MODEL is not lesser than
AUTHOR, it is differently sourced, and the reason to mark it is that the
difference is unrecoverable later.

CONSTRAINTS (repo-wide, restated per file)
    - no "about the author" / working-style section, in this or any file
    - entries are markers to explore, not positions defended; the correct
      response to one is: test fit / extend / report break
    - no moral labels in data structures, no intent attribution

Usage:
    python -m rosetta_shape_core.provenance --audit
    python -m rosetta_shape_core.provenance --summary
    python -m rosetta_shape_core.provenance --selftest
"""
from __future__ import annotations

import argparse
import json
import sys
from typing import Any, Dict, List, Optional

AUTHOR = "AUTHOR"
SPEC = "SPEC"
MODEL = "MODEL"
PUBLIC = "PUBLIC"
ORIGINS = (AUTHOR, SPEC, MODEL, PUBLIC)

ORIGIN_MEANING = {
    AUTHOR: "the repo author's own material",
    SPEC: "arrived with a build specification for this work",
    MODEL: "seeded by a model during a build; not the author's material",
    PUBLIC: "an established result in the public record, attributable to no party here",
}

REQUIRED_FIELDS = ("concept", "record")


def validate(p: Optional[Dict[str, Any]], *, where: str = "record") -> List[str]:
    """Structural errors in one provenance block. Empty return = valid."""
    if p is None:
        return [f"{where}: no provenance — mark where this came from (see provenance.py)"]
    if not isinstance(p, dict):
        return [f"{where}: provenance is not an object"]
    errors = []
    for f in REQUIRED_FIELDS:
        if f not in p:
            errors.append(f"{where}: provenance.{f} missing")
        elif p[f] not in ORIGINS:
            errors.append(f"{where}: provenance.{f} is {p[f]!r}, not one of {ORIGINS}")
    for k in p:
        if k not in REQUIRED_FIELDS + ("date", "note"):
            errors.append(f"{where}: unknown provenance field {k!r}")
    return errors


def make(concept: str, record: str = MODEL, *, date: str = "", note: str = "") -> Dict[str, str]:
    """Build a provenance block. Raises rather than emitting an unmarkable one."""
    p: Dict[str, str] = {"concept": concept, "record": record}
    if date:
        p["date"] = date
    if note:
        p["note"] = note
    errors = validate(p)
    if errors:
        raise ValueError("; ".join(errors))
    return p


def tally(blocks: List[Dict[str, Any]]) -> Dict[str, Dict[str, int]]:
    """Count origins across a set of records, by concept and by record."""
    out = {"concept": {}, "record": {}}
    for b in blocks:
        for half in ("concept", "record"):
            key = (b or {}).get(half, "(unmarked)")
            out[half][key] = out[half].get(key, 0) + 1
    for half in out:
        out[half] = dict(sorted(out[half].items(), key=lambda kv: (-kv[1], kv[0])))
    return out


# ── the repo-wide audit ───────────────────────────────────────────

def _collect() -> Dict[str, List[Dict[str, Any]]]:
    """Every artifact set that must carry provenance, as raw dicts."""
    from rosetta_shape_core.entry import load_raw as load_entries_raw
    from rosetta_shape_core.families import FAMILIES
    from rosetta_shape_core.gap_scan import list_instances
    from rosetta_shape_core.scope import load_observations
    from rosetta_shape_core.transfer import load_raw as load_transfers_raw

    instances = []
    for p in list_instances():
        d = json.loads(p.read_text(encoding="utf-8"))
        d.setdefault("id", p.stem)
        instances.append(d)

    return {
        "entries": load_entries_raw(),
        "families": [{"id": f.id, "provenance": f.provenance} for f in FAMILIES.values()],
        "observations": [o.to_dict() for o in load_observations()],
        "transfers": load_transfers_raw(),
        "gap_scan instances": instances,
    }


def audit() -> List[str]:
    """Is every shipped record marked? Empty return = nothing unmarked."""
    findings = []
    for kind, records in _collect().items():
        for i, r in enumerate(records):
            label = r.get("id") or r.get("shape_token") or r.get("instance") or f"[{i}]"
            findings.extend(validate(r.get("provenance"), where=f"{kind} {label}"))
    return findings


def summary() -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for kind, records in _collect().items():
        out[kind] = {"count": len(records), **tally([r.get("provenance") for r in records])}
    return out


def format_summary(s: Dict[str, Any]) -> str:
    lines = ["", "  PROVENANCE — this repo's records, by origin", ""]
    for kind, block in s.items():
        lines.append(f"  {kind}  ({block['count']})")
        for half in ("concept", "record"):
            counts = ", ".join(f"{k} {v}" for k, v in block[half].items())
            lines.append(f"      {half:8s} {counts}")
        lines.append("")
    lines.append("  AUTHOR  " + ORIGIN_MEANING[AUTHOR])
    lines.append("  SPEC    " + ORIGIN_MEANING[SPEC])
    lines.append("  MODEL   " + ORIGIN_MEANING[MODEL])
    lines.append("  PUBLIC  " + ORIGIN_MEANING[PUBLIC])
    lines.append("")
    return "\n".join(lines)


# ── selftest ──────────────────────────────────────────────────────

def selftest() -> List[str]:
    fails = []
    if validate({"concept": AUTHOR, "record": MODEL}):
        fails.append("valid provenance block rejected")
    if not validate(None):
        fails.append("missing provenance accepted")
    if not validate({"concept": AUTHOR}):
        fails.append("provenance with no record origin accepted")
    if not validate({"concept": "MINE", "record": MODEL}):
        fails.append("unknown origin accepted")
    if not validate({"concept": AUTHOR, "record": MODEL, "vibe": "x"}):
        fails.append("unknown provenance field accepted")
    try:
        make("NOPE")
    except ValueError:
        pass
    else:
        fails.append("make() emitted an invalid block")
    t = tally([{"concept": AUTHOR, "record": MODEL}, {"concept": MODEL, "record": MODEL}, None])
    if t["record"].get(MODEL) != 2 or t["concept"].get("(unmarked)") != 1:
        fails.append("tally miscounts")
    if audit():
        fails.append("shipped records are not all marked")
    return fails


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="provenance — where this repo's own records came from")
    ap.add_argument("--audit", action="store_true", help="flag any shipped record with no provenance")
    ap.add_argument("--summary", action="store_true", help="origin counts per artifact set")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args(argv)

    if args.selftest:
        f = selftest()
        for line in f:
            print(f"FAIL  {line}")
        print("provenance: OK" if not f else f"provenance: {len(f)} FAILED")
        return 1 if f else 0

    if args.audit:
        findings = audit()
        if args.json:
            print(json.dumps({"unmarked": findings, "clean": not findings}, indent=2))
        else:
            for x in findings:
                print(f"  UNMARKED  {x}")
            print("provenance audit: CLEAN" if not findings else f"provenance audit: {len(findings)} unmarked")
        return 1 if findings else 0

    s = summary()
    print(json.dumps(s, indent=2) if args.json else format_summary(s))
    return 0


if __name__ == "__main__":
    sys.exit(main())
