# SPDX-License-Identifier: CC0-1.0
"""Transfers — what happened when a move was actually carried over.

The entry set records systems that reached a working configuration. That is
half the record. A move that ports cleanly teaches one thing; a move that
looked licensed and broke anyway teaches where the licensing criterion is
wrong, which is worth more. Without this half the corpus can only ever
recommend, and nothing in it is answerable to an outcome.

A transfer record is one attempt: a move taken from a source system to a
problem, and what it did there.

    outcome   HELD | PARTIAL | BROKE
    broke_at  where it stopped working (required unless it held)
    verdict_on  what the break indicts:

      NONE              it held; nothing to correct
      SCOPE_CONFIRMED   it broke at a stop the entry already stated —
                        the entry was right, and that stop is now measured
                        rather than asserted
      ENTRY_SCOPE       it broke somewhere the entry does not mention;
                        the entry understates where it stops, and the fix
                        is to add that stop
      SOURCE_READING    the configuration or forcing attributed to the
                        source turned out to be wrong
      LICENSING         the transfer was licensed and the move still did
                        not port — evidence against the criterion itself
      PROBLEM_FRAMING   the problem's own forcing terms were misnamed;
                        nothing is wrong with the entry

HELD WITH A REVISED SOURCE READING
    ``HELD`` admits ``SOURCE_READING`` as well as ``NONE``, because the two
    are independent: a move can port and work while the account of why the
    source does it is later corrected. That is not an anomaly to be tidied
    away — it is "port the move, not the ontology" showing up as data.

A record whose ``from_entry`` is empty is a pointer to an entry nobody has
written. The audit reports those rather than hiding them: the outside of the
corpus is visible from here, and it is information about the corpus.

CONSTRAINTS (repo-wide, restated per file)
    - no "about the author" / working-style section, in this or any file
    - entries are markers to explore, not positions defended; the correct
      response to one is: test fit / extend / report break
    - no moral labels in data structures, no intent attribution
      (an outcome is what happened, never a judgement of who attempted it)

Usage:
    python -m rosetta_shape_core.transfer --list
    python -m rosetta_shape_core.transfer --validate
    python -m rosetta_shape_core.transfer --audit
    python -m rosetta_shape_core.transfer --criterion
    python -m rosetta_shape_core.transfer --selftest
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional

from rosetta_shape_core.entry import Entry, load_entries
from rosetta_shape_core.provenance import validate as validate_provenance

ROOT = pathlib.Path(__file__).resolve().parents[2]
TRANSFERS_PATH = ROOT / "data" / "rosetta" / "transfers.jsonl"

HELD = "HELD"
PARTIAL = "PARTIAL"
BROKE = "BROKE"
OUTCOMES = (HELD, PARTIAL, BROKE)

NONE = "NONE"
SCOPE_CONFIRMED = "SCOPE_CONFIRMED"
ENTRY_SCOPE = "ENTRY_SCOPE"
SOURCE_READING = "SOURCE_READING"
LICENSING = "LICENSING"
PROBLEM_FRAMING = "PROBLEM_FRAMING"
VERDICTS = (NONE, SCOPE_CONFIRMED, ENTRY_SCOPE, SOURCE_READING, LICENSING, PROBLEM_FRAMING)

# Held locally rather than imported from rosetta.py, which imports scope.py,
# which reaches back here. A test asserts the two lists stay identical.
GRADES = ("SHARED_DOMINANT", "SHARED_FORCING", "SHARED_PRESENT", "SHARED_FORM")

REQUIRED_FIELDS = ("to_problem", "outcome", "verdict_on", "provenance")
OPTIONAL_FIELDS = ("id", "from_entry", "from_source", "problem_forcing", "problem_dominant",
                   "licensing", "broke_at", "confirms_stop", "produced_past", "reading",
                   "sources", "note")


@dataclass
class Transfer:
    """One attempt, and what it did. Not a verdict on whoever attempted it."""

    to_problem: str
    outcome: str
    verdict_on: str = NONE
    provenance: Dict[str, Any] = field(default_factory=dict)
    id: Optional[str] = None
    from_entry: str = ""
    from_source: str = ""
    problem_forcing: List[str] = field(default_factory=list)
    problem_dominant: List[str] = field(default_factory=list)
    licensing: str = ""
    broke_at: str = ""
    confirms_stop: str = ""
    produced_past: str = ""
    reading: str = ""
    sources: List[str] = field(default_factory=list)
    note: str = ""

    @property
    def key(self) -> str:
        return self.id or f"TRANSFER.{self.to_problem[:24].upper().replace(' ', '_')}"

    @property
    def held(self) -> bool:
        return self.outcome == HELD

    def to_dict(self) -> dict:
        return {k: v for k, v in asdict(self).items() if v not in (None, "", [], {})}

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Transfer":
        return cls(
            to_problem=d.get("to_problem", ""),
            outcome=d.get("outcome", ""),
            verdict_on=d.get("verdict_on", NONE),
            provenance=dict(d.get("provenance", {})),
            id=d.get("id"),
            from_entry=d.get("from_entry", ""),
            from_source=d.get("from_source", ""),
            problem_forcing=list(d.get("problem_forcing", [])),
            problem_dominant=list(d.get("problem_dominant", [])),
            licensing=d.get("licensing", ""),
            broke_at=d.get("broke_at", ""),
            confirms_stop=d.get("confirms_stop", ""),
            produced_past=d.get("produced_past", ""),
            reading=d.get("reading", ""),
            sources=list(d.get("sources", [])),
            note=d.get("note", ""),
        )


# ── validation ────────────────────────────────────────────────────

def validate_transfer(d: Dict[str, Any], entries: Optional[List[Entry]] = None) -> List[str]:
    """Structural errors in one transfer. Empty return = valid."""
    if not isinstance(d, dict):
        return ["transfer is not an object"]
    errors: List[str] = []

    for f in REQUIRED_FIELDS:
        if f not in d:
            errors.append(f"missing required field: {f}")
    for k in d:
        if k not in REQUIRED_FIELDS + OPTIONAL_FIELDS:
            errors.append(f"unknown field: {k}")

    outcome = d.get("outcome")
    if outcome is not None and outcome not in OUTCOMES:
        errors.append(f"outcome {outcome!r} not one of {OUTCOMES}")
    verdict = d.get("verdict_on")
    if verdict is not None and verdict not in VERDICTS:
        errors.append(f"verdict_on {verdict!r} not one of {VERDICTS}")

    if not d.get("from_entry") and not d.get("from_source"):
        errors.append("neither from_entry nor from_source — the move came from somewhere; say where")
    if not str(d.get("to_problem", "")).strip():
        errors.append("to_problem is empty")

    if outcome in (PARTIAL, BROKE) and not str(d.get("broke_at", "")).strip():
        errors.append("broke_at is required unless the transfer held — where it stopped working is the record")
    if outcome == HELD and verdict not in (NONE, SOURCE_READING):
        errors.append(f"outcome HELD admits verdict_on NONE or SOURCE_READING, not {verdict!r}")
    if outcome in (PARTIAL, BROKE) and verdict == NONE:
        errors.append("a transfer that did not hold has something to indict — verdict_on cannot be NONE")
    if verdict == SCOPE_CONFIRMED and not d.get("confirms_stop"):
        errors.append("verdict SCOPE_CONFIRMED requires confirms_stop naming the stop it broke at")

    lic = d.get("licensing")
    if lic and lic not in GRADES:
        errors.append(f"licensing {lic!r} not one of {GRADES}")

    if "provenance" in d:
        errors.extend(validate_provenance(d["provenance"], where="transfer"))

    ents = load_entries() if entries is None else entries
    by_key = {e.key: e for e in ents}
    from_entry = d.get("from_entry")
    if from_entry:
        entry = by_key.get(from_entry)
        if entry is None:
            errors.append(f"from_entry {from_entry!r} resolves to no entry")
        else:
            for fname in ("confirms_stop", "produced_past"):
                sid = d.get(fname)
                if sid and entry.stop(sid) is None:
                    errors.append(f"{fname} {sid!r} is not a stop of {from_entry} "
                                  f"(has: {', '.join(entry.stop_ids) or 'none'})")
    else:
        for fname in ("confirms_stop", "produced_past"):
            if d.get(fname):
                errors.append(f"{fname} needs a from_entry to resolve against")
    return errors


# ── io ────────────────────────────────────────────────────────────

def load_raw(path: Optional[pathlib.Path] = None) -> List[Dict[str, Any]]:
    p = pathlib.Path(path) if path else TRANSFERS_PATH
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


def load_transfers(path: Optional[pathlib.Path] = None) -> List[Transfer]:
    return [Transfer.from_dict(d) for d in load_raw(path)]


def validate_file(path: Optional[pathlib.Path] = None) -> List[str]:
    ents = load_entries()
    errors = []
    seen = set()
    for i, d in enumerate(load_raw(path)):
        key = Transfer.from_dict(d).key
        for e in validate_transfer(d, ents):
            errors.append(f"transfer[{i}] {key}: {e}")
        if key in seen:
            errors.append(f"transfer[{i}]: duplicate key {key}")
        seen.add(key)
    return errors


# ── what the log is for ───────────────────────────────────────────

def stop_confirmations(transfers: Optional[List[Transfer]] = None) -> Dict[str, List[str]]:
    """{entry key: [stop id, ...]} for stops a real transfer actually hit."""
    out: Dict[str, List[str]] = {}
    for t in (load_transfers() if transfers is None else transfers):
        if t.from_entry and t.confirms_stop:
            out.setdefault(t.from_entry, []).append(t.confirms_stop)
    return out


def stop_contradictions(transfers: Optional[List[Transfer]] = None) -> Dict[str, List[str]]:
    """{entry key: [stop id, ...]} for stops something produced straight past."""
    out: Dict[str, List[str]] = {}
    for t in (load_transfers() if transfers is None else transfers):
        if t.from_entry and t.produced_past:
            out.setdefault(t.from_entry, []).append(t.produced_past)
    return out


def audit(transfers: Optional[List[Transfer]] = None, entries: Optional[List[Entry]] = None) -> List[str]:
    """Findings the log makes about the corpus. Empty return = nothing to correct."""
    ts = load_transfers() if transfers is None else transfers
    ents = load_entries() if entries is None else entries
    by_key = {e.key: e for e in ents}
    findings = []
    for t in ts:
        if t.verdict_on == ENTRY_SCOPE:
            if t.from_entry and t.from_entry in by_key:
                findings.append(
                    f"{t.key}: {t.from_entry} understates its scope — it broke at "
                    f"'{t.broke_at}', which is not among its stops. Add it."
                )
            else:
                findings.append(
                    f"{t.key}: broke at '{t.broke_at}' and there is no entry to add that stop to. "
                    f"The source '{t.from_source}' is unrecorded — this is a pointer to a missing entry."
                )
        if t.verdict_on == SOURCE_READING:
            entry = by_key.get(t.from_entry)
            if entry is not None and entry.status_of("configuration") != "DUE_FOR_UPDATE":
                findings.append(
                    f"{t.key}: the reading of {t.from_entry} was revised after the fact. Mark its "
                    f"configuration DUE_FOR_UPDATE — the entry still states the superseded reading."
                )
            elif entry is None:
                findings.append(
                    f"{t.key}: the reading of '{t.from_source}' was revised after the fact. Any entry "
                    f"written from it needs the current reading, not the one that was ported."
                )
        if t.verdict_on == LICENSING:
            findings.append(
                f"{t.key}: licensed {t.licensing or '(grade unrecorded)'} and did not port. "
                f"This counts against the licensing criterion, not against the entry."
            )
        if t.produced_past and t.from_entry in by_key:
            stop = by_key[t.from_entry].stop(t.produced_past)
            says = stop["says"] if stop else t.produced_past
            findings.append(
                f"{t.key}: {t.from_entry} kept producing past a stated stop — '{says}'. "
                f"The stop is contested; either it is wrong or its condition was not met."
            )
    return findings


def unrecorded_sources(transfers: Optional[List[Transfer]] = None) -> List[str]:
    """Source systems a transfer came from that no entry covers."""
    ts = load_transfers() if transfers is None else transfers
    return sorted({t.from_source for t in ts if not t.from_entry and t.from_source})


def criterion_report(transfers: Optional[List[Transfer]] = None) -> Dict[str, Any]:
    """The instrument on the licensing criterion itself.

    Of the transfers that recorded a grade at the time, how many held? A
    criterion that licenses transfers which then break is a criterion with a
    measurable error rate, and that is the point of keeping this log.
    """
    ts = load_transfers() if transfers is None else transfers
    graded = [t for t in ts if t.licensing]
    by_grade: Dict[str, Dict[str, int]] = {}
    for t in graded:
        row = by_grade.setdefault(t.licensing, {o: 0 for o in OUTCOMES})
        row[t.outcome] += 1
    outcomes = {o: sum(1 for t in ts if t.outcome == o) for o in OUTCOMES}
    verdicts = {v: sum(1 for t in ts if t.verdict_on == v) for v in VERDICTS}
    return {
        "transfers": len(ts),
        "graded_at_the_time": len(graded),
        "by_grade": by_grade,
        "outcomes": outcomes,
        "verdicts": {k: v for k, v in verdicts.items() if v},
        "against_the_criterion": verdicts[LICENSING],
        "unrecorded_sources": unrecorded_sources(ts),
    }


def format_transfer(t: Transfer) -> str:
    lines = [f"  {t.key}   [{t.outcome}]"]
    lines.append(f"      from       {t.from_entry or t.from_source + ' (no entry)'}")
    lines.append(f"      to         {t.to_problem}")
    if t.licensing:
        lines.append(f"      licensed   {t.licensing}")
    if t.broke_at:
        lines.append(f"      broke at   {t.broke_at}")
    if t.confirms_stop:
        lines.append(f"      confirms   stop '{t.confirms_stop}' of {t.from_entry}")
    if t.produced_past:
        lines.append(f"      past stop  '{t.produced_past}' of {t.from_entry} — contested")
    lines.append(f"      verdict    {t.verdict_on}")
    if t.reading:
        lines.append(f"      reading    {t.reading}")
    return "\n".join(lines)


# ── selftest ──────────────────────────────────────────────────────

def selftest() -> List[str]:
    fails = []
    ents = load_entries()
    ok = {
        "id": "TRANSFER.TEST",
        "from_entry": "ENTRY.HONEYCOMB_PARTITION",
        "to_problem": "a problem",
        "outcome": BROKE,
        "broke_at": "somewhere",
        "confirms_stop": "closed_surface",
        "verdict_on": SCOPE_CONFIRMED,
        "provenance": {"concept": "MODEL", "record": "MODEL"},
    }
    if validate_transfer(ok, ents):
        fails.append("valid transfer rejected")
    if not validate_transfer({**ok, "outcome": "SORT_OF"}, ents):
        fails.append("unknown outcome accepted")
    if not validate_transfer({**ok, "verdict_on": NONE}, ents):
        fails.append("a broken transfer with verdict NONE was accepted")
    no_break = {k: v for k, v in ok.items() if k != "broke_at"}
    if not any("broke_at" in e for e in validate_transfer(no_break, ents)):
        fails.append("a broken transfer with no broke_at was accepted")
    if not validate_transfer({**ok, "confirms_stop": "no_such_stop"}, ents):
        fails.append("confirms_stop pointing at no stop was accepted")
    if not validate_transfer({**ok, "from_entry": "ENTRY.NOT_HERE"}, ents):
        fails.append("from_entry resolving to nothing was accepted")
    orphan = {k: v for k, v in ok.items() if k not in ("from_entry", "confirms_stop")}
    if not any("from_source" in e for e in validate_transfer({**orphan, "verdict_on": ENTRY_SCOPE}, ents)):
        fails.append("a transfer from nowhere was accepted")

    held_revised = {**ok, "outcome": HELD, "verdict_on": SOURCE_READING}
    held_revised.pop("broke_at")
    held_revised.pop("confirms_stop")
    if validate_transfer(held_revised, ents):
        fails.append("HELD with a revised source reading was rejected — the two are independent")
    if not validate_transfer({**held_revised, "verdict_on": LICENSING}, ents):
        fails.append("HELD with an unrelated verdict was accepted")

    t = Transfer.from_dict(ok)
    if stop_confirmations([t]) != {"ENTRY.HONEYCOMB_PARTITION": ["closed_surface"]}:
        fails.append("stop confirmations not collected")
    past = Transfer.from_dict({**ok, "confirms_stop": "", "produced_past": "unequal_cells",
                               "verdict_on": ENTRY_SCOPE})
    if stop_contradictions([past]) != {"ENTRY.HONEYCOMB_PARTITION": ["unequal_cells"]}:
        fails.append("stop contradictions not collected")
    if not any("contested" in f for f in audit([past], ents)):
        fails.append("producing past a stated stop was not reported")

    from rosetta_shape_core.entry import Entry
    stale = Entry.from_dict({"id": "ENTRY.STALE", "source_system": "x", "configuration": "an old reading"})
    revised = Transfer.from_dict({"from_entry": "ENTRY.STALE", "to_problem": "p", "outcome": HELD,
                                  "verdict_on": SOURCE_READING,
                                  "provenance": {"concept": "MODEL", "record": "MODEL"}})
    if not any("DUE_FOR_UPDATE" in f for f in audit([revised], [stale])):
        fails.append("a revised source reading did not point at the entry that still states it")
    marked = Entry.from_dict({**stale.to_dict(), "field_status": {"configuration": "DUE_FOR_UPDATE"}})
    if any("DUE_FOR_UPDATE" in f for f in audit([revised], [marked])):
        fails.append("an entry already marked DUE_FOR_UPDATE was flagged again")

    if validate_file():
        fails.append("shipped transfers.jsonl does not validate")
    if not load_transfers():
        fails.append("transfers.jsonl is empty — the operator has no outcomes on file")
    r = criterion_report()
    if r["transfers"] != len(load_transfers()):
        fails.append("criterion report miscounts")
    return fails


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="transfers — what happened when a move was carried over")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--validate", action="store_true")
    ap.add_argument("--audit", action="store_true", help="what the outcomes say the corpus should fix")
    ap.add_argument("--criterion", action="store_true", help="the log as an instrument on the licensing criterion")
    ap.add_argument("--path", help="transfers file (default data/rosetta/transfers.jsonl)")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args(argv)

    path = pathlib.Path(args.path) if args.path else None

    if args.selftest:
        f = selftest()
        for line in f:
            print(f"FAIL  {line}")
        print("transfer: OK" if not f else f"transfer: {len(f)} FAILED")
        return 1 if f else 0

    if args.validate:
        errors = validate_file(path)
        if args.json:
            print(json.dumps({"errors": errors, "valid": not errors}, indent=2))
        else:
            for e in errors:
                print(f"  ✗  {e}")
            print("transfers: VALID" if not errors else f"transfers: {len(errors)} error(s)")
        return 1 if errors else 0

    if args.audit:
        findings = audit()
        missing = unrecorded_sources()
        if args.json:
            print(json.dumps({"findings": findings, "unrecorded_sources": missing}, indent=2))
        else:
            for x in findings:
                print(f"  FINDING  {x}")
            for m in missing:
                print(f"  ⚠        no entry for '{m}' — a transfer was made from it anyway")
            print("transfer audit: CLEAN" if not findings else f"transfer audit: {len(findings)} finding(s)")
        return 0

    if args.criterion:
        r = criterion_report()
        if args.json:
            print(json.dumps(r, indent=2))
        else:
            print()
            print(f"  transfers on file      {r['transfers']}")
            print(f"  graded at the time     {r['graded_at_the_time']}")
            print("  outcomes               " + ", ".join(f"{k} {v}" for k, v in r["outcomes"].items()))
            print("  verdicts               " + ", ".join(f"{k} {v}" for k, v in r["verdicts"].items()))
            print(f"  against the criterion  {r['against_the_criterion']}")
            if r["graded_at_the_time"] == 0:
                print()
                print("  No transfer carries a grade recorded at the time, so the licensing criterion")
                print("  has no evidence for or against it yet. That is the state, not a clean bill.")
            print()
        return 0

    ts = load_transfers(path)
    if args.json:
        print(json.dumps([t.to_dict() for t in ts], indent=2))
    else:
        print(f"\n  TRANSFERS ({len(ts)})\n")
        for t in ts:
            print(format_transfer(t))
            print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
