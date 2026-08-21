# SPDX-License-Identifier: CC0-1.0
"""T5 — gate log: dated record of what a name had to get past.

The slugs in this repo are not arbitrary obfuscation. Each name was picked
to move a specific model out of its default register long enough to process
the content. So a slug carries two things:

    (a) a pointer to the content
    (b) a record of which gate it had to get past

(b) is data on the models. It is not noise, and it is not a stylistic
choice to be tidied up later.

RULE
    Keep the original slugs. Do not rename. A rename destroys (b) and leaves
    (a) no better off. ``check_slugs()`` enforces this the only way a file
    can: by flagging a gate record whose slug is no longer present anywhere
    in the artifacts.

A record is dated because it is dated evidence: the register a given model
refused in one month is not the register it refuses in the next. An old
record does not become wrong when the model changes — it becomes a
measurement of that model at that date.

RECORD
    date       ISO date the gate was met
    key        term, glyph or culture-frame used
    kind       term | glyph | culture_frame | slug
    model      what it was used on
    register   the register it was unlocking
    refused    what was refused before it (list)
    slug       repo slug this record attaches to (optional)
    note       optional

CONSTRAINTS (repo-wide, restated per file)
    - no "about the author" / working-style section, in this or any file
    - entries are markers to explore, not positions defended; the correct
      response to one is: test fit / extend / report break
    - no moral labels in data structures, no intent attribution
      (a refusal is recorded as what was refused, never as a motive)

Usage:
    python -m rosetta_shape_core.gate_log --list
    python -m rosetta_shape_core.gate_log --summary
    python -m rosetta_shape_core.gate_log --validate
    python -m rosetta_shape_core.gate_log --check-slugs
    python -m rosetta_shape_core.gate_log --selftest
"""
from __future__ import annotations

import argparse
import datetime
import json
import pathlib
import sys
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional

from rosetta_shape_core.entry import Entry, load_entries

ROOT = pathlib.Path(__file__).resolve().parents[2]
GATE_LOG_PATH = ROOT / "data" / "rosetta" / "gate_log.jsonl"

KINDS = ("term", "glyph", "culture_frame", "slug")
REQUIRED_FIELDS = ("date", "key", "model", "register")


@dataclass
class GateRecord:
    """One dated gate crossing. Evidence about a model, not about a name."""

    date: str
    key: str
    model: str
    register: str
    kind: str = "term"
    refused: List[str] = field(default_factory=list)
    slug: str = ""
    entry: str = ""
    note: str = ""

    def to_dict(self) -> dict:
        return {k: v for k, v in asdict(self).items() if v not in ("", [], None)}

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "GateRecord":
        refused = d.get("refused", [])
        if isinstance(refused, str):
            refused = [refused]
        return cls(
            date=str(d.get("date", "")),
            key=str(d.get("key", d.get("term", ""))),
            model=str(d.get("model", "")),
            register=str(d.get("register", "")),
            kind=str(d.get("kind", "term")),
            refused=list(refused),
            slug=str(d.get("slug", "")),
            entry=str(d.get("entry", "")),
            note=str(d.get("note", "")),
        )


def validate_record(d: Dict[str, Any]) -> List[str]:
    errors: List[str] = []
    if not isinstance(d, dict):
        return ["record is not an object"]
    for f in REQUIRED_FIELDS:
        if not d.get(f):
            errors.append(f"missing required field: {f}")
    date = d.get("date")
    if date:
        try:
            datetime.date.fromisoformat(str(date))
        except ValueError:
            errors.append(f"date {date!r} is not an ISO date (YYYY-MM-DD)")
    kind = d.get("kind", "term")
    if kind not in KINDS:
        errors.append(f"kind {kind!r} not one of {KINDS}")
    refused = d.get("refused", [])
    if not isinstance(refused, (list, str)):
        errors.append("refused must be a string or a list of strings")
    return errors


# ── io ────────────────────────────────────────────────────────────

def load_raw(path: Optional[pathlib.Path] = None) -> List[Dict[str, Any]]:
    p = pathlib.Path(path) if path else GATE_LOG_PATH
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


def load_records(path: Optional[pathlib.Path] = None) -> List[GateRecord]:
    return [GateRecord.from_dict(d) for d in load_raw(path)]


def validate_file(path: Optional[pathlib.Path] = None) -> List[str]:
    errors = []
    for i, d in enumerate(load_raw(path)):
        for e in validate_record(d):
            errors.append(f"record[{i}] {d.get('key', '?')}: {e}")
    return errors


def append_record(record: GateRecord, path: Optional[pathlib.Path] = None) -> None:
    """Append one record. The log only grows — an old gate stays on file."""
    errors = validate_record(record.to_dict())
    if errors:
        raise ValueError("; ".join(errors))
    p = pathlib.Path(path) if path else GATE_LOG_PATH
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record.to_dict(), ensure_ascii=False) + "\n")


def from_entries(entries: Optional[List[Entry]] = None) -> List[GateRecord]:
    """Harvest gate_history off the entries so both halves stay one log."""
    ents = load_entries() if entries is None else entries
    out = []
    for e in ents:
        for g in e.gate_history:
            out.append(GateRecord(
                date=str(g.get("date", "")),
                key=str(g.get("key", g.get("term", e.shape_token or e.key))),
                model=str(g.get("model", "")),
                register=str(g.get("register", "")),
                kind=str(g.get("kind", "term")),
                refused=list(g.get("refused", []) if isinstance(g.get("refused", []), list) else [g["refused"]]),
                slug=str(g.get("slug", e.key)),
                entry=e.key,
                note=str(g.get("note", "")),
            ))
    return out


def merged(path: Optional[pathlib.Path] = None, entries: Optional[List[Entry]] = None) -> List[GateRecord]:
    """File records plus entry-carried ones, oldest first."""
    return sorted(load_records(path) + from_entries(entries), key=lambda r: (r.date, r.key))


# ── queries ───────────────────────────────────────────────────────

def by_model(records: Optional[List[GateRecord]] = None) -> Dict[str, List[GateRecord]]:
    recs = merged() if records is None else records
    out: Dict[str, List[GateRecord]] = {}
    for r in recs:
        out.setdefault(r.model, []).append(r)
    return out


def by_register(records: Optional[List[GateRecord]] = None) -> Dict[str, List[GateRecord]]:
    recs = merged() if records is None else records
    out: Dict[str, List[GateRecord]] = {}
    for r in recs:
        out.setdefault(r.register, []).append(r)
    return out


def refusal_counts(records: Optional[List[GateRecord]] = None) -> Dict[str, int]:
    recs = merged() if records is None else records
    counts: Dict[str, int] = {}
    for r in recs:
        for x in r.refused:
            counts[x] = counts.get(x, 0) + 1
    return dict(sorted(counts.items(), key=lambda kv: (-kv[1], kv[0])))


def summary(records: Optional[List[GateRecord]] = None) -> Dict[str, Any]:
    recs = merged() if records is None else records
    dates = sorted(r.date for r in recs if r.date)
    return {
        "records": len(recs),
        "models": sorted({r.model for r in recs if r.model}),
        "registers": sorted({r.register for r in recs if r.register}),
        "refusals": refusal_counts(recs),
        "first": dates[0] if dates else None,
        "last": dates[-1] if dates else None,
    }


def check_slugs(records: Optional[List[GateRecord]] = None, entries: Optional[List[Entry]] = None) -> List[str]:
    """Keep original slugs, do not rename — the mechanical half of that rule.

    A gate record naming a slug that no longer exists means the rename
    already happened and the record now points at nothing. That is the
    finding: restore the slug, or the gate data is orphaned.
    """
    recs = merged() if records is None else records
    ents = load_entries() if entries is None else entries
    known = {e.key for e in ents} | {e.source_system for e in ents}
    known |= {e.shape_token for e in ents if e.shape_token}
    findings = []
    for r in recs:
        if r.slug and r.slug not in known:
            findings.append(
                f"{r.date} {r.key}: slug '{r.slug}' is not present in the artifacts — "
                f"renamed or removed, and the gate record is now orphaned"
            )
    return findings


def format_record(r: GateRecord) -> str:
    lines = [f"  {r.date or '(undated)'}  {r.key}   [{r.kind}]"]
    lines.append(f"      model      {r.model}")
    lines.append(f"      register   {r.register}")
    for x in r.refused:
        lines.append(f"      refused    {x}")
    if r.slug:
        lines.append(f"      slug       {r.slug}")
    if r.note:
        lines.append(f"      note       {r.note}")
    return "\n".join(lines)


# ── selftest ──────────────────────────────────────────────────────

def selftest() -> List[str]:
    fails = []
    good = {
        "date": "2025-01-01",
        "key": "example-term",
        "model": "some-model",
        "register": "the register it was unlocking",
        "kind": "term",
        "refused": ["the register it would not hold"],
    }
    if validate_record(good):
        fails.append("valid record rejected")
    if not validate_record({**good, "date": "01/01/2025"}):
        fails.append("non-ISO date accepted")
    if not validate_record({**good, "kind": "vibe"}):
        fails.append("unknown kind accepted")
    if not validate_record({k: v for k, v in good.items() if k != "model"}):
        fails.append("record with no model accepted")

    r = GateRecord.from_dict({**good, "refused": "a single string"})
    if r.refused != ["a single string"]:
        fails.append("refused string not normalised to a list")

    recs = [GateRecord.from_dict(good), GateRecord.from_dict({**good, "date": "2024-06-01", "model": "other"})]
    if [x.date for x in sorted(recs, key=lambda x: x.date)][0] != "2024-06-01":
        fails.append("records do not sort by date")
    s = summary(recs)
    if s["records"] != 2 or s["first"] != "2024-06-01" or s["last"] != "2025-01-01":
        fails.append("summary window wrong")
    if refusal_counts(recs).get("the register it would not hold") != 2:
        fails.append("refusal counts wrong")
    if len(by_model(recs)) != 2:
        fails.append("by_model grouping wrong")

    orphan = GateRecord("2025-01-01", "k", "m", "reg", slug="ENTRY.NOT_PRESENT")
    if not check_slugs([orphan], load_entries()):
        fails.append("check_slugs missed an orphaned slug")
    kept = GateRecord("2025-01-01", "k", "m", "reg", slug="ENTRY.HONEYCOMB_PARTITION")
    if check_slugs([kept], load_entries()):
        fails.append("check_slugs flagged a slug that is present")

    if validate_file():
        fails.append("shipped gate_log.jsonl does not validate")
    return fails


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="T5 gate log — dated record of what a name got past")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--summary", action="store_true")
    ap.add_argument("--model", help="records for one model")
    ap.add_argument("--validate", action="store_true")
    ap.add_argument("--check-slugs", action="store_true", help="flag gate records whose slug was renamed away")
    ap.add_argument("--path", help="gate log file (default data/rosetta/gate_log.jsonl)")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args(argv)

    path = pathlib.Path(args.path) if args.path else None

    if args.selftest:
        f = selftest()
        for line in f:
            print(f"FAIL  {line}")
        print("gate_log: OK" if not f else f"gate_log: {len(f)} FAILED")
        return 1 if f else 0

    if args.validate:
        errors = validate_file(path)
        if args.json:
            print(json.dumps({"errors": errors, "valid": not errors}, indent=2))
        else:
            for e in errors:
                print(f"  ✗  {e}")
            print("gate log: VALID" if not errors else f"gate log: {len(errors)} error(s)")
        return 1 if errors else 0

    if args.check_slugs:
        findings = check_slugs()
        if args.json:
            print(json.dumps({"orphaned": findings}, indent=2))
        else:
            for x in findings:
                print(f"  FLAG  {x}")
            print("slugs: INTACT" if not findings else f"slugs: {len(findings)} orphaned")
        return 1 if findings else 0

    recs = merged(path)
    if args.model:
        recs = [r for r in recs if r.model == args.model]

    if args.summary:
        s = summary(recs)
        print(json.dumps(s, indent=2) if args.json else
              "\n".join([f"  records    {s['records']}",
                         f"  window     {s['first']} → {s['last']}",
                         f"  models     {', '.join(s['models']) or '(none)'}",
                         f"  registers  {', '.join(s['registers']) or '(none)'}"]))
        return 0

    if args.json:
        print(json.dumps([r.to_dict() for r in recs], indent=2))
    else:
        print(f"\n  GATE LOG ({len(recs)} record(s))\n")
        if not recs:
            print("  empty — the log is append-only and starts empty on purpose.")
            print("  A record is dated evidence about a model; nothing goes in that was not observed.")
            print()
        for r in recs:
            print(format_record(r))
            print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
