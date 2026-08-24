# SPDX-License-Identifier: CC0-1.0
"""T3 — entry schema: the record the operator runs on.

One entry is one source system read once, under stated forcing.

    source_system   crystal, grass, mycelium, ...
    configuration   what it reaches under constraint
    forcing_terms   [family, ...]  — every term acting on the source
    forcing_dominant [family, ...]  — the subset that SETS the configuration
    move_ported     the transferable operation
    scope           where it produces / where it stops
    shape_token     the name used
    gate_history    [{date, model, register}, ...]
    provenance      {concept, record} — where the entry came from
    field_status    {field: status} — how finished each field is

HOLDING RECORD — optional, and mostly unmarked on purpose

    domain      f01..f20, the domain OF the world this reading is in
    access      a01.., the way of knowing it was reached by
    acquired    residual | transmitted | unmarked

    ``unmarked`` is a legitimate value and is expected to dominate. An
    absent ``acquired`` reads as unmarked; neither is backfilled with a
    guess, because a guess about how a reading was obtained is exactly the
    kind of thing that becomes unrecoverable once it is written down.

    Claiming a domain while naming no access is reported by tier_check —
    "unmarked" is an answer, a missing field is not the same thing.

FIELD STATUS — an entry may ship unfinished, and say so
    A record with a hole in it is not the same thing as a record with a
    guess in it, and the repo should be able to tell them apart. So a field
    can carry a status:

      OPEN            deliberately open for experimentation. Nobody has
                      fixed it, and that is the invitation
      UNKNOWN         not known, and not currently being worked
      CONDITIONAL     holds only under a condition that is not yet stated
      PARTIAL         some of it is there; more is needed
      DUE_FOR_UPDATE  it was filled, and something has since superseded it —
                      new evidence, or a transfer whose verdict was
                      SOURCE_READING

    A required field left empty is an error UNLESS it is marked, which is
    what lets an entry enter the corpus with its forcing terms honestly open
    rather than invented. The contract is checked both ways: OPEN and
    UNKNOWN require the field to be empty, PARTIAL and DUE_FOR_UPDATE
    require it to be filled. Marking is not a way to silence a check.

    Status is orthogonal to provenance. Provenance says where a record came
    from; status says how finished it is.

``forcing_dominant`` is required and must be a subset of ``forcing_terms``.
Presence of a shared term is too cheap a test on its own: strain acts on
nearly every physical system, so matching on presence licenses almost every
pair and the distinction erodes in practice while still looking rigorous.
What licenses a transfer is a term that is *setting* the configuration, not
one that merely happens to be present. An entry that cannot name which term
sets its configuration has not been read closely enough to port from.

A stop may be a plain string or ``{"id": ..., "says": ..., "cited": ...}``.
Give it an id when something references it — a transfer that broke there, an
observation that tested it. Bare strings get positional ids, which move if
the list is reordered, so anything referenced should be given an explicit
one. ``cited`` names the source that established the boundary in the source
system's own literature, which is not the same as anyone having carried a
move to it — see scope.py.

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
ENTRIES_DIR = ROOT / "data" / "rosetta"
ENTRIES_PATH = ENTRIES_DIR / "entries.jsonl"


def entry_files() -> List[pathlib.Path]:
    """Every entries*.jsonl in data/rosetta. Imported sets live beside the hand-written one."""
    if not ENTRIES_DIR.exists():
        return []
    return sorted(ENTRIES_DIR.glob("entries*.jsonl"))

REQUIRED_FIELDS = ("source_system", "configuration", "forcing_terms", "forcing_dominant",
                   "move_ported", "scope", "provenance")
OPTIONAL_FIELDS = ("id", "shape_token", "gate_history", "note", "sources", "field_status",
                   "domain", "access", "acquired")

RESIDUAL = "residual"
TRANSMITTED = "transmitted"
UNMARKED = "unmarked"
ACQUISITION_CHANNELS = (RESIDUAL, TRANSMITTED, UNMARKED)

_DOMAIN_RE = re.compile(r"^f(0[1-9]|1[0-9]|20)$")
_ACCESS_RE = re.compile(r"^a[0-9]{2}$")

OPEN = "OPEN"
UNKNOWN = "UNKNOWN"
CONDITIONAL = "CONDITIONAL"
PARTIAL = "PARTIAL"
DUE_FOR_UPDATE = "DUE_FOR_UPDATE"
FIELD_STATUSES = (OPEN, UNKNOWN, CONDITIONAL, PARTIAL, DUE_FOR_UPDATE)

# statuses that excuse an empty required field, and what each implies
EXCUSES_EMPTY = (OPEN, UNKNOWN, CONDITIONAL)
REQUIRES_EMPTY = (OPEN, UNKNOWN)
REQUIRES_FILLED = (PARTIAL, DUE_FOR_UPDATE)

STATUS_MEANING = {
    OPEN: "open for experimentation — nobody has fixed it, and that is the invitation",
    UNKNOWN: "not known, and not currently being worked",
    CONDITIONAL: "holds only under a condition that is not yet stated",
    PARTIAL: "some of it is there; more is needed",
    DUE_FOR_UPDATE: "was filled, and something has since superseded it",
}

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


def normalize_stop(stop: Any, index: int = 0) -> Dict[str, str]:
    """A stop as {id, says}. Bare strings get a positional id."""
    if isinstance(stop, str):
        return {"id": f"stop_{index}", "says": stop}
    if isinstance(stop, dict):
        rec = {"id": str(stop.get("id", f"stop_{index}")), "says": str(stop.get("says", ""))}
        if stop.get("cited"):
            rec["cited"] = str(stop["cited"])
        return rec
    return {"id": f"stop_{index}", "says": str(stop)}


@dataclass
class Entry:
    """One marker. Not a position."""

    source_system: str
    configuration: str
    forcing_terms: List[str] = field(default_factory=list)
    forcing_dominant: List[str] = field(default_factory=list)
    move_ported: str = ""
    scope: Dict[str, List[str]] = field(default_factory=dict)
    provenance: Dict[str, Any] = field(default_factory=dict)
    id: Optional[str] = None
    shape_token: Optional[str] = None
    gate_history: List[Dict[str, Any]] = field(default_factory=list)
    note: str = ""
    sources: List[str] = field(default_factory=list)
    field_status: Dict[str, str] = field(default_factory=dict)
    domain: str = ""
    access: str = ""
    acquired: str = ""

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
    def stop_records(self) -> List[Dict[str, str]]:
        """Stops as {id, says}, whether written as strings or as objects."""
        return [normalize_stop(s, i) for i, s in enumerate(self.scope.get("stops", []))]

    @property
    def stops(self) -> List[str]:
        """Stop texts, for display."""
        return [r["says"] for r in self.stop_records]

    @property
    def stop_ids(self) -> List[str]:
        return [r["id"] for r in self.stop_records]

    def stop(self, stop_id: str) -> Optional[Dict[str, str]]:
        for r in self.stop_records:
            if r["id"] == stop_id:
                return r
        return None

    @property
    def acquisition(self) -> str:
        """How the reading was obtained. Absent reads as unmarked, not as missing."""
        return self.acquired or UNMARKED

    def status_of(self, field_name: str) -> str:
        """Status of one field. Empty string = settled, i.e. nothing flagged."""
        return self.field_status.get(field_name, "")

    @property
    def open_fields(self) -> List[str]:
        """Fields carrying any status. An entry with none is complete as written."""
        return sorted(self.field_status)

    @property
    def complete(self) -> bool:
        return not self.field_status

    @property
    def transferable(self) -> bool:
        """Can this entry license a transfer at all?

        Forcing terms are what licenses transfer, so an entry whose forcing
        is open cannot be matched — it is a source system on file waiting for
        someone to name the loads. It is still worth carrying: that is the
        experiment it is asking for.
        """
        for f in ("forcing_terms", "forcing_dominant"):
            if self.status_of(f) in EXCUSES_EMPTY:
                return False
        return bool(self.forcing_terms and self.forcing_dominant)

    @property
    def dominant(self) -> List[str]:
        """Resolved family ids of the terms that set the configuration."""
        out = []
        for t in self.forcing_dominant:
            fid = resolve_family(t)
            if fid and fid not in out:
                out.append(fid)
        return out

    @property
    def families(self) -> List[str]:
        """Resolved family ids of every term acting on the source."""
        out = []
        for t in self.forcing_terms:
            fid = resolve_family(t)
            if fid and fid not in out:
                out.append(fid)
        return out

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
            forcing_dominant=list(d.get("forcing_dominant", [])),
            move_ported=d.get("move_ported", ""),
            scope=dict(d.get("scope", {})),
            provenance=dict(d.get("provenance", {})),
            id=d.get("id"),
            shape_token=d.get("shape_token"),
            gate_history=list(gh),
            note=d.get("note", ""),
            sources=list(d.get("sources", [])),
            field_status=dict(d.get("field_status", {})),
            domain=d.get("domain", ""),
            access=d.get("access", ""),
            acquired=d.get("acquired", ""),
        )


# ── validation (stdlib; the JSON Schema mirror lives in schema/) ───

STATUSABLE_FIELDS = REQUIRED_FIELDS + OPTIONAL_FIELDS + ("scope.produces", "scope.stops")


def _filled(d: Dict[str, Any], name: str) -> bool:
    """Is a field (or a scope half) actually carrying anything?"""
    if name.startswith("scope."):
        value = (d.get("scope") or {}).get(name.split(".", 1)[1])
    else:
        value = d.get(name)
    if isinstance(value, str):
        return bool(value.strip())
    return bool(value)


def validate_field_status(d: Dict[str, Any]) -> List[str]:
    """The status contract, checked both ways.

    Marking is how an entry ships honestly unfinished. It is not a way to
    silence a check, so a status that contradicts the field it describes is
    an error: OPEN on a filled field, or PARTIAL on an empty one.
    """
    fs = d.get("field_status")
    if fs is None:
        return []
    if not isinstance(fs, dict):
        return ["field_status must be an object mapping field name to status"]
    errors = []
    for name, status in fs.items():
        if name not in STATUSABLE_FIELDS:
            errors.append(f"field_status names {name!r}, which is not a field of an entry")
            continue
        if status not in FIELD_STATUSES:
            errors.append(f"field_status.{name} is {status!r}, not one of {FIELD_STATUSES}")
            continue
        if status in REQUIRES_EMPTY and _filled(d, name):
            errors.append(f"field_status.{name} is {status} but the field is filled — "
                          f"{status} says nobody has fixed it yet")
        if status in REQUIRES_FILLED and not _filled(d, name):
            errors.append(f"field_status.{name} is {status} but the field is empty — "
                          f"{status} says something is already there")
    return errors


def validate_entry(d: Dict[str, Any]) -> List[str]:
    """Structural errors in one entry dict. Empty return = valid."""
    errors: List[str] = []
    if not isinstance(d, dict):
        return ["entry is not an object"]

    errors.extend(validate_field_status(d))
    fs = d.get("field_status") if isinstance(d.get("field_status"), dict) else {}
    excused = {name for name, status in fs.items() if status in EXCUSES_EMPTY}

    for f in REQUIRED_FIELDS:
        if f not in d and f not in excused:
            errors.append(f"missing required field: {f} "
                          f"(or mark it in field_status: {', '.join(EXCUSES_EMPTY)})")

    known = set(REQUIRED_FIELDS) | set(OPTIONAL_FIELDS)
    for k in d:
        if k not in known:
            errors.append(f"unknown field: {k}")

    for f in ("source_system", "configuration", "move_ported"):
        if f in d and not isinstance(d[f], str):
            errors.append(f"{f} must be a string")
        elif f in d and not d[f].strip() and f not in excused:
            errors.append(f"{f} is empty")

    ft = d.get("forcing_terms")
    if ft is not None:
        if not isinstance(ft, list) or not all(isinstance(t, str) for t in ft):
            errors.append("forcing_terms must be a list of strings")
        elif not ft:
            if "forcing_terms" not in excused:
                errors.append("forcing_terms is empty — nothing licenses transfer from this entry. "
                              "Mark it OPEN if that is the state and the entry is worth carrying anyway")
        else:
            for t in ft:
                if resolve_family(t) is None:
                    errors.append(f"forcing term '{t}' resolves to no family (see families.py)")

    fd = d.get("forcing_dominant")
    if fd is not None:
        if not isinstance(fd, list) or not all(isinstance(t, str) for t in fd):
            errors.append("forcing_dominant must be a list of strings")
        elif not fd:
            if "forcing_dominant" not in excused:
                errors.append("forcing_dominant is empty — name the term(s) that SET the configuration; "
                              "presence alone is too cheap a test to license transfer")
        else:
            present = {resolve_family(t) for t in (ft or []) if isinstance(t, str)}
            for t in fd:
                fid = resolve_family(t)
                if fid is None:
                    errors.append(f"dominant term '{t}' resolves to no family (see families.py)")
                elif fid not in present:
                    errors.append(f"dominant term '{t}' is not in forcing_terms — a term cannot set "
                                  f"a configuration it is not acting on")

    scope = d.get("scope")
    if scope is not None:
        if not isinstance(scope, dict):
            errors.append("scope must be an object")
        else:
            for half in ("produces", "stops"):
                if half not in scope:
                    if f"scope.{half}" not in excused:
                        errors.append(f"scope.{half} missing — the entry must say where it {half}")
                elif not isinstance(scope[half], list):
                    errors.append(f"scope.{half} must be a list")
                elif half == "produces" and not all(isinstance(s, str) for s in scope[half]):
                    errors.append("scope.produces must be a list of strings")
            stops = scope.get("stops")
            if isinstance(stops, list):
                seen = set()
                for i, st in enumerate(stops):
                    if not isinstance(st, (str, dict)):
                        errors.append(f"scope.stops[{i}] must be a string or an object")
                        continue
                    rec = normalize_stop(st, i)
                    if not rec["says"].strip():
                        errors.append(f"scope.stops[{i}] says nothing")
                    if rec["id"] in seen:
                        errors.append(f"scope.stops[{i}]: duplicate stop id {rec['id']!r}")
                    seen.add(rec["id"])

    if "provenance" in d:
        errors.extend(validate_provenance(d["provenance"], where="entry"))

    dom = d.get("domain")
    if dom is not None and (not isinstance(dom, str) or not _DOMAIN_RE.match(dom)):
        errors.append(f"domain {dom!r} is not one of f01..f20 — the domains OF the world. "
                      f"A way of knowing goes in access, not here")
    acc = d.get("access")
    if acc is not None and (not isinstance(acc, str) or not _ACCESS_RE.match(acc)):
        errors.append(f"access {acc!r} is not a tier-local access id (a01..)")
    acq = d.get("acquired")
    if acq is not None and acq not in ACQUISITION_CHANNELS:
        errors.append(f"acquired {acq!r} not one of {ACQUISITION_CHANNELS} — "
                      f"'unmarked' is a legitimate value and is expected to dominate")

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

def _read_jsonl(p: pathlib.Path) -> List[Dict[str, Any]]:
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


def load_raw(path: Optional[pathlib.Path] = None) -> List[Dict[str, Any]]:
    """Read the entry set. One file if given, else every entries*.jsonl."""
    if path is not None:
        return _read_jsonl(pathlib.Path(path))
    out: List[Dict[str, Any]] = []
    for p in entry_files():
        out.extend(_read_jsonl(p))
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
    lines.append(f"      sets it       {', '.join(e.forcing_dominant)}")
    lines.append(f"      move          {e.move_ported}")
    if e.shape_token:
        lines.append(f"      shape_token   {e.shape_token}")
    for s in e.produces:
        lines.append(f"      produces      {s}")
    for r in e.stop_records:
        lines.append(f"      stops         [{r['id']}] {r['says']}")
    for g in e.gate_history:
        lines.append(f"      gate          {g.get('date', '?')} {g.get('model', '?')} — {g.get('register', '?')}")
    if e.domain or e.access or e.acquired:
        lines.append(f"      holding       domain {e.domain or '—'} / access {e.access or '—'} / "
                     f"acquired {e.acquisition}")
    if e.field_status:
        for name, status in sorted(e.field_status.items()):
            lines.append(f"      {status:<14s} {name} — {STATUS_MEANING[status]}")
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
        "forcing_dominant": ["strain"],
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
    if not any("not in forcing_terms" in e for e in validate_entry({**ok, "forcing_dominant": ["FLOW"]})):
        fails.append("a dominant term outside forcing_terms was accepted")
    if not any("forcing_dominant is empty" in e for e in validate_entry({**ok, "forcing_dominant": []})):
        fails.append("an entry naming no dominant term was accepted")
    structured = {**ok, "scope": {"produces": ["here"],
                                  "stops": [{"id": "there", "says": "it stops there"}]}}
    if validate_entry(structured):
        fails.append("structured stop rejected")
    e = Entry.from_dict(structured)
    if e.stop_ids != ["there"] or e.stops != ["it stops there"]:
        fails.append("structured stop not normalised")
    if Entry.from_dict(ok).stop_ids != ["stop_0"]:
        fails.append("bare-string stop did not get a positional id")

    if Entry.from_dict(ok).acquisition != UNMARKED:
        fails.append("an unrecorded acquisition did not read as unmarked")
    if Entry.from_dict({**ok, "acquired": RESIDUAL}).acquisition != RESIDUAL:
        fails.append("a recorded acquisition was not returned")
    if validate_entry({**ok, "domain": "f05", "access": "a01", "acquired": UNMARKED}):
        fails.append("a valid holding record was rejected")
    if not validate_entry({**ok, "domain": "f21"}):
        fails.append("domain f21 accepted — f21 is not a domain of the world")
    if not validate_entry({**ok, "access": "F21"}):
        fails.append("a non-access-id accepted in the access field")
    if not validate_entry({**ok, "acquired": "guessed"}):
        fails.append("an unknown acquisition channel accepted")

    open_entry = {k: v for k, v in ok.items() if k not in ("forcing_terms", "forcing_dominant", "move_ported")}
    open_entry["field_status"] = {"forcing_terms": OPEN, "forcing_dominant": OPEN, "move_ported": OPEN}
    if validate_entry(open_entry):
        fails.append("an entry with honestly open fields was rejected")
    if Entry.from_dict(open_entry).transferable:
        fails.append("an entry with open forcing was reported transferable")
    if not Entry.from_dict(ok).transferable:
        fails.append("a complete entry was not reported transferable")
    if not any("is filled" in e for e in validate_entry({**ok, "field_status": {"move_ported": OPEN}})):
        fails.append("OPEN on a filled field was accepted")
    if not any("is empty" in e for e in validate_entry({**open_entry,
                                                        "field_status": {"move_ported": PARTIAL}})):
        fails.append("PARTIAL on an empty field was accepted")
    if not any("not a field of an entry" in e
               for e in validate_entry({**ok, "field_status": {"vibes": OPEN}})):
        fails.append("field_status naming a non-field was accepted")
    if not any("not one of" in e
               for e in validate_entry({**ok, "field_status": {"note": "MAYBE"}})):
        fails.append("an unknown field status was accepted")
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
