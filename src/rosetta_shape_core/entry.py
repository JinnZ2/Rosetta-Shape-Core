# SPDX-License-Identifier: CC0-1.0
"""T3 — entry schema: the record the operator runs on.

One entry is one source system read once, under stated forcing.

    source_system   crystal, grass, mycelium, ...
    configuration   what it reaches under constraint
    forcing_terms   [family, ...]  — this is what licenses transfer
    move_ported     the transferable operation
    scope           where it produces / where it stops
    shape_token     the name used
    gate_history    [{date, model, register}, ...]
    provenance      {concept, record} — where the entry came from

``provenance`` is required. A repo that demands operand provenance of
everything it reads cannot ship unmarked records of its own: an entry whose
source system was named by the author but written up by a model reads as
fully authored unless it says otherwise, and that is unrecoverable later.
See provenance.py.

``forcing_terms`` is the load-bearing field. Two systems reaching the same
configuration under the same forcing is SHARED FORCING: the shape is caused
and transfer is licensed. Two systems whose shapes merely coincide is SHARED
FORM: a coincidence until a mechanism appears. The schema keeps the terms so
the difference stays checkable — see rosetta.py.

``scope.stops`` is required to exist. An entry that produces everywhere and
never stops is not a strong entry, it is an unaudited one, and scope.py
flags it.

CONSTRAINTS (repo-wide, restated per file)
    - no "about the author" / working-style section, in this or any file
    - entries are markers to explore, not positions defended; the correct
      response to one is: test fit / extend / report break
    - no moral labels in data structures, no intent attribution
      (``lint_entries`` reports these as advisories, not errors)

Usage:
    python -m rosetta_shape_core.entry --list
    python -m rosetta_shape_core.entry --validate
    python -m rosetta_shape_core.entry --lint
    python -m rosetta_shape_core.entry --id ENTRY.HONEYCOMB_PARTITION --json
    python -m rosetta_shape_core.entry --selftest
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional

from rosetta_shape_core.families import resolve as resolve_family
from rosetta_shape_core.provenance import validate as validate_provenance

ROOT = pathlib.Path(__file__).resolve().parents[2]
ENTRIES_PATH = ROOT / "data" / "rosetta" / "entries.jsonl"

REQUIRED_FIELDS = ("source_system", "configuration", "forcing_terms", "move_ported", "scope", "provenance")
OPTIONAL_FIELDS = ("id", "shape_token", "gate_history", "note", "sources")

# Advisory lint only. These are not moral judgements about the words; they
# are the two registers the repo does not encode in data: attribution of
# intent to a system, and a moral label on a configuration.
INTENT_TOKENS = (
    "wants", "want to", "tries to", "trying to", "decides", "chooses", "choose to",
    "intends", "intention", "prefers", "seeks", "seeking", "desires", "believes",
    "knows that", "aims to", "in order to please", "purpose is to",
)
MORAL_TOKENS = (
    "good", "evil", "bad", "wicked", "virtuous", "deserves", "should be",
    "ought to", "selfish", "greedy", "noble", "wrong of", "right of",
)


@dataclass
class Entry:
    """One marker. Not a position."""

    source_system: str
    configuration: str
    forcing_terms: List[str] = field(default_factory=list)
    move_ported: str = ""
    scope: Dict[str, List[str]] = field(default_factory=dict)
    provenance: Dict[str, Any] = field(default_factory=dict)
    id: Optional[str] = None
    shape_token: Optional[str] = None
    gate_history: List[Dict[str, Any]] = field(default_factory=list)
    note: str = ""
    sources: List[str] = field(default_factory=list)

    @property
    def key(self) -> str:
        """Stable handle. Explicit id if given, else derived from the source system."""
        if self.id:
            return self.id
        slug = re.sub(r"[^A-Za-z0-9]+", "_", self.source_system).strip("_").upper()
        return f"ENTRY.{slug}"

    @property
    def produces(self) -> List[str]:
        return list(self.scope.get("produces", []))

    @property
    def stops(self) -> List[str]:
        return list(self.scope.get("stops", []))

    def to_dict(self) -> dict:
        d = asdict(self)
        return {k: v for k, v in d.items() if v not in (None, [], {}, "")}

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Entry":
        gh = d.get("gate_history", [])
        if isinstance(gh, dict):
            gh = [gh]
        return cls(
            source_system=d.get("source_system", ""),
            configuration=d.get("configuration", ""),
            forcing_terms=list(d.get("forcing_terms", [])),
            move_ported=d.get("move_ported", ""),
            scope=dict(d.get("scope", {})),
            provenance=dict(d.get("provenance", {})),
            id=d.get("id"),
            shape_token=d.get("shape_token"),
            gate_history=list(gh),
            note=d.get("note", ""),
            sources=list(d.get("sources", [])),
        )


# ── validation (stdlib; the JSON Schema mirror lives in schema/) ───

def validate_entry(d: Dict[str, Any]) -> List[str]:
    """Structural errors in one entry dict. Empty return = valid."""
    errors: List[str] = []
    if not isinstance(d, dict):
        return ["entry is not an object"]

    for f in REQUIRED_FIELDS:
        if f not in d:
            errors.append(f"missing required field: {f}")

    known = set(REQUIRED_FIELDS) | set(OPTIONAL_FIELDS)
    for k in d:
        if k not in known:
            errors.append(f"unknown field: {k}")

    for f in ("source_system", "configuration", "move_ported"):
        if f in d and not isinstance(d[f], str):
            errors.append(f"{f} must be a string")
        elif f in d and not d[f].strip():
            errors.append(f"{f} is empty")

    ft = d.get("forcing_terms")
    if ft is not None:
        if not isinstance(ft, list) or not all(isinstance(t, str) for t in ft):
            errors.append("forcing_terms must be a list of strings")
        elif not ft:
            errors.append("forcing_terms is empty — nothing licenses transfer from this entry")
        else:
            for t in ft:
                if resolve_family(t) is None:
                    errors.append(f"forcing term '{t}' resolves to no family (see families.py)")

    scope = d.get("scope")
    if scope is not None:
        if not isinstance(scope, dict):
            errors.append("scope must be an object")
        else:
            for half in ("produces", "stops"):
                if half not in scope:
                    errors.append(f"scope.{half} missing — the entry must say where it {half}")
                elif not isinstance(scope[half], list) or not all(isinstance(s, str) for s in scope[half]):
                    errors.append(f"scope.{half} must be a list of strings")

    if "provenance" in d:
        errors.extend(validate_provenance(d["provenance"], where="entry"))

    st = d.get("shape_token")
    if st is not None and (not isinstance(st, str) or st != st.upper()):
        errors.append("shape_token must be an uppercase string")

    gh = d.get("gate_history")
    if gh is not None:
        recs = [gh] if isinstance(gh, dict) else gh
        if not isinstance(recs, list):
            errors.append("gate_history must be an object or a list of objects")
        else:
            for i, r in enumerate(recs):
                if not isinstance(r, dict):
                    errors.append(f"gate_history[{i}] is not an object")
                    continue
                for f in ("date", "model", "register"):
                    if f not in r:
                        errors.append(f"gate_history[{i}] missing {f}")
    return errors


def lint_entry(d: Dict[str, Any]) -> List[str]:
    """Advisory findings: intent attribution and moral labels in the data.

    Not errors. The finding names the token and the field; whether the
    phrasing is load-bearing is a call made at the entry, not here.
    """
    findings: List[str] = []
    for fname in ("configuration", "move_ported", "note"):
        text = d.get(fname)
        if not isinstance(text, str):
            continue
        low = text.lower()
        for tok in INTENT_TOKENS:
            if tok in low:
                findings.append(f"{fname}: intent attribution — '{tok}'")
        for tok in MORAL_TOKENS:
            if re.search(rf"\b{re.escape(tok)}\b", low):
                findings.append(f"{fname}: moral label — '{tok}'")
    for half in ("produces", "stops"):
        for s in d.get("scope", {}).get(half, []) if isinstance(d.get("scope"), dict) else []:
            low = str(s).lower()
            for tok in INTENT_TOKENS:
                if tok in low:
                    findings.append(f"scope.{half}: intent attribution — '{tok}'")
    return findings


# ── io ────────────────────────────────────────────────────────────

def load_raw(path: Optional[pathlib.Path] = None) -> List[Dict[str, Any]]:
    """Read entries.jsonl. Blank lines skipped; a bad line raises with its number."""
    p = pathlib.Path(path) if path else ENTRIES_PATH
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


def load_entries(path: Optional[pathlib.Path] = None) -> List[Entry]:
    return [Entry.from_dict(d) for d in load_raw(path)]


def validate_file(path: Optional[pathlib.Path] = None) -> List[str]:
    """Validate every entry plus cross-entry integrity (unique keys)."""
    raws = load_raw(path)
    errors: List[str] = []
    seen: Dict[str, int] = {}
    for i, d in enumerate(raws):
        for e in validate_entry(d):
            errors.append(f"entry[{i}] {d.get('id') or d.get('source_system', '?')}: {e}")
        key = Entry.from_dict(d).key
        if key in seen:
            errors.append(f"entry[{i}]: duplicate key {key} (also entry[{seen[key]}])")
        else:
            seen[key] = i
    return errors


def lint_file(path: Optional[pathlib.Path] = None) -> List[str]:
    findings = []
    for d in load_raw(path):
        key = Entry.from_dict(d).key
        for f in lint_entry(d):
            findings.append(f"{key}: {f}")
    return findings


def format_entry(e: Entry) -> str:
    lines = [f"  {e.key}"]
    lines.append(f"      source        {e.source_system}")
    lines.append(f"      configuration {e.configuration}")
    lines.append(f"      forcing       {', '.join(e.forcing_terms)}")
    lines.append(f"      move          {e.move_ported}")
    if e.shape_token:
        lines.append(f"      shape_token   {e.shape_token}")
    for s in e.produces:
        lines.append(f"      produces      {s}")
    for s in e.stops:
        lines.append(f"      stops         {s}")
    for g in e.gate_history:
        lines.append(f"      gate          {g.get('date', '?')} {g.get('model', '?')} — {g.get('register', '?')}")
    if e.provenance:
        lines.append(f"      provenance    concept {e.provenance.get('concept', '?')} / "
                     f"record {e.provenance.get('record', '?')}")
        if e.provenance.get("note"):
            lines.append(f"                    {e.provenance['note']}")
    return "\n".join(lines)


# ── selftest ──────────────────────────────────────────────────────

def selftest() -> List[str]:
    fails = []
    ok = {
        "id": "ENTRY.TEST",
        "source_system": "test system",
        "configuration": "a configuration reached under load",
        "forcing_terms": ["GRAVITY_LOAD", "strain"],
        "move_ported": "a move",
        "scope": {"produces": ["here"], "stops": ["there"]},
        "provenance": {"concept": "MODEL", "record": "MODEL"},
    }
    if validate_entry(ok):
        fails.append("valid entry rejected")
    if not validate_entry({**ok, "forcing_terms": ["astrology"]}):
        fails.append("unresolvable forcing term accepted")
    no_stop = {**ok, "scope": {"produces": ["here"]}}
    if not validate_entry(no_stop):
        fails.append("entry with no scope.stops accepted")
    if not validate_entry({**ok, "shape_token": "hexagon"}):
        fails.append("lowercase shape_token accepted")
    unmarked = {k: v for k, v in ok.items() if k != "provenance"}
    if not any("provenance" in e for e in validate_entry(unmarked)):
        fails.append("entry with no provenance accepted")
    if not lint_entry({**ok, "configuration": "the system wants to minimise energy"}):
        fails.append("lint missed intent attribution")
    if lint_entry(ok):
        fails.append("lint fired on a clean entry")
    if Entry.from_dict({"source_system": "grass blade"}).key != "ENTRY.GRASS_BLADE":
        fails.append("key derivation broken")
    errors = validate_file()
    if errors:
        fails.append(f"shipped entries.jsonl does not validate: {errors[0]}")
    if not load_entries():
        fails.append("entries.jsonl is empty")
    return fails


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="T3 entry schema — load, validate, lint")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--id", help="show one entry by key")
    ap.add_argument("--validate", action="store_true")
    ap.add_argument("--lint", action="store_true", help="advisory: intent attribution / moral labels")
    ap.add_argument("--path", help="entries file (default data/rosetta/entries.jsonl)")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args(argv)

    path = pathlib.Path(args.path) if args.path else None

    if args.selftest:
        fails = selftest()
        for f in fails:
            print(f"FAIL  {f}")
        print("entry: OK" if not fails else f"entry: {len(fails)} FAILED")
        return 1 if fails else 0

    if args.validate:
        errors = validate_file(path)
        if args.json:
            print(json.dumps({"errors": errors, "valid": not errors}, indent=2))
        else:
            for e in errors:
                print(f"  ✗  {e}")
            print("entries: VALID" if not errors else f"entries: {len(errors)} error(s)")
        return 1 if errors else 0

    if args.lint:
        findings = lint_file(path)
        if args.json:
            print(json.dumps({"advisories": findings}, indent=2))
        else:
            for f in findings:
                print(f"  ⚠  {f}")
            print("entries lint: CLEAN" if not findings else f"entries lint: {len(findings)} advisory")
        return 0

    entries = load_entries(path)
    if args.id:
        entries = [e for e in entries if e.key == args.id or e.source_system == args.id]
        if not entries:
            print(f"no entry: {args.id}")
            return 1

    if args.json:
        print(json.dumps([e.to_dict() for e in entries], indent=2))
    else:
        print(f"\n  ENTRIES ({len(entries)})\n")
        for e in entries:
            print(format_entry(e))
            print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
