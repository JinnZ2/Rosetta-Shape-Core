# SPDX-License-Identifier: CC0-1.0
"""Holdings — what is held, when it was last touched, and which way it is moving.

A trajectory needs a derivative, so the record carries whatever makes one
computable from the record alone: two observations minimum, with the gap
between them readable. Contacts are RECORDED — not judged, not inferred at
write time. Every trajectory below is COMPUTED ON READ and none is ever
written into the file.

    contact_log        [{t, kind, result}, ...]
    last_residual      when the world last pushed back
    referent_rate      known | slow | fast | unknown
    support_ids        what this stands on
    dependents         what stands on this
    discrepancy_count  the learning counter, not the error count
    restatement_count  motion in the record
    scope_hits/misses  used inside / outside its stated valid_on

DECAY IS THREE THINGS, AND ONLY ONE OF THEM IS DECAY OF INFORMATION

    d1_referent   the world changed. The holding is now wrong.
    d2_receipt    the holding is intact and the support is gone. You still
                  have the value, not the ground.
    d3_uptake     referent unchanged, emission unchanged, still fully
                  available — and the receiver no longer resolves it.

    Only d1 is decay of information. d2 is decay of provenance. d3 is decay
    of the instrument, filed as decay of the world.

    ``now - last_residual`` sees d1 and d2. It CANNOT see d3 at all, because
    d3 leaves the record untouched: a skill unpractised, a language not
    spoken, a landscape stopped being read. Full availability, zero uptake.
    All three feel identical from inside — the holding stops reading true —
    and d3 is the only one whose correct response is aimed at the observer,
    so it is the one that gets misdiagnosed in the direction that costs
    nothing. Default is ``undiagnosed``. Never d1 by default.

    The discriminator is cheap and needs no decoding: does another receiver
    still resolve it? Yes → the loss is at your end. Nobody does → either d1
    or a population-wide d3, which is the dangerous case, because "nobody
    hears it" reads as "nothing is being said."

GAP CLASSES — named here, and NOT the same as gap_scan's G1-G4

    gap_scan.py numbers four gap SHAPE classes on a cross-instance axis
    (missing_slot, imported_boundary, substrate_ceiling, exterior). These
    are a different thing on a different axis: which operator can reach a
    gap in a corpus. The names are spelled out rather than numbered here
    precisely so the two sets cannot be confused.

CONSTRAINTS (repo-wide, restated per file)
    - no "about the author" / working-style section, in this or any file
    - entries are markers to explore, not positions defended; the correct
      response to one is: test fit / extend / report break
    - no moral labels in data structures, no intent attribution

Usage:
    python -m rosetta_shape_core.holding --list
    python -m rosetta_shape_core.holding --trajectories
    python -m rosetta_shape_core.holding --audit
    python -m rosetta_shape_core.holding --selftest
"""
from __future__ import annotations

import argparse
import datetime
import json
import pathlib
import statistics
import sys
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional

from rosetta_shape_core.provenance import validate as validate_provenance

ROOT = pathlib.Path(__file__).resolve().parents[2]
HOLDINGS_PATH = ROOT / "data" / "rosetta" / "holdings.jsonl"

RESIDUAL = "residual"
TRANSMITTED = "transmitted"
INTERNAL = "internal"
CONTACT_KINDS = (RESIDUAL, TRANSMITTED, INTERNAL)

CONFIRMED = "confirmed"
RESTATED = "restated"
DISCREPANT = "discrepant"
CONTACT_RESULTS = (CONFIRMED, RESTATED, DISCREPANT)

# referent_rate. 'unknown' must NOT silently become 'slow' — an unknown-rate
# holding is not a fresh one, and the ratio is simply unavailable for it.
RATE_DAYS: Dict[str, Optional[float]] = {"fast": 30.0, "slow": 1000.0, "unknown": None}
RATES = ("known", "slow", "fast", "unknown")

D1_REFERENT = "d1_referent"
D2_RECEIPT = "d2_receipt"
D3_UPTAKE = "d3_uptake"
UNDIAGNOSED = "undiagnosed"
DECAY_CLASSES = (D1_REFERENT, D2_RECEIPT, D3_UPTAKE, UNDIAGNOSED)

# Trajectories. Computed, never stored.
DECAY = "DECAY"
TOWARD_UNKNOWN = "TOWARD_UNKNOWN"
STALE_CONFIRMED_STABLE = "STALE_CONFIRMED_STABLE"
STALE_UNREFRESHED = "STALE_UNREFRESHED"
TOWARD_LEARNING = "TOWARD_LEARNING"
TOWARD_CIRCULATION = "TOWARD_CIRCULATION"
TOWARD_OSSIFICATION = "TOWARD_OSSIFICATION"

# Which operator can reach a gap. Not gap_scan's G1-G4; see the docstring.
KNOWN_MISSING = "KNOWN_MISSING"
KNOWN_UNRESOLVED = "KNOWN_UNRESOLVED"
UNMARKED_GAP = "UNMARKED"

GAP_REACH = {
    KNOWN_MISSING: ("a field is empty, a support is absent. Reachable by a07 internal audit — it "
                    "flags itself. Cheap: this is what the validator queue is."),
    KNOWN_UNRESOLVED: ("question posed, no instrument exists. Reachable by nothing internal; "
                       "requires building one. Expensive, and the productive class."),
    UNMARKED_GAP: ("axis not sampled, no entry, no flag. Reachable by NOTHING self-directed — no "
                   "internal signal exists for a channel you do not have. Only reach: "
                   "cross-station comparison, which is the borrowed-instrument channel (a04)."),
}

REQUIRED_FIELDS = ("holding_id", "provenance")
OPTIONAL_FIELDS = ("contact_log", "last_residual", "contact_interval", "referent_rate",
                   "referent_rate_days", "support_ids", "dependents", "discrepancy_count",
                   "restatement_count", "scope_hits", "scope_misses", "decay_class",
                   "cross_observer_checked", "note")


@dataclass
class Contact:
    t: str
    kind: str = RESIDUAL
    result: str = CONFIRMED

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Holding:
    """One held item. Counters are recorded; trajectories are not stored here."""

    holding_id: str
    contact_log: List[Dict[str, Any]] = field(default_factory=list)
    last_residual: Optional[str] = None
    referent_rate: str = "unknown"
    referent_rate_days: Optional[float] = None
    support_ids: List[str] = field(default_factory=list)
    dependents: List[str] = field(default_factory=list)
    discrepancy_count: int = 0
    restatement_count: int = 0
    scope_hits: int = 0
    scope_misses: int = 0
    decay_class: str = UNDIAGNOSED
    cross_observer_checked: bool = False
    provenance: Dict[str, Any] = field(default_factory=dict)
    note: str = ""

    @property
    def contacts(self) -> List[Contact]:
        return [Contact(c.get("t", ""), c.get("kind", RESIDUAL), c.get("result", CONFIRMED))
                for c in self.contact_log]

    @property
    def residual_contacts(self) -> List[Contact]:
        return [c for c in self.contacts if c.kind == RESIDUAL]

    @property
    def contact_count(self) -> int:
        return len(self.contact_log)

    @property
    def observed_last_residual(self) -> Optional[str]:
        """From the log if present, else the stored field. The log wins."""
        dates = sorted(c.t for c in self.residual_contacts if c.t)
        return dates[-1] if dates else self.last_residual

    @property
    def contact_interval(self) -> Optional[float]:
        """Median gap in days between residual contacts. None under two of them."""
        dates = sorted(_date(c.t) for c in self.residual_contacts if _date(c.t))
        if len(dates) < 2:
            return None
        gaps = [(b - a).days for a, b in zip(dates, dates[1:])]
        return float(statistics.median(gaps))

    @property
    def rate_days(self) -> Optional[float]:
        if self.referent_rate == "known":
            return self.referent_rate_days
        return RATE_DAYS.get(self.referent_rate)

    def to_dict(self) -> dict:
        return {k: v for k, v in asdict(self).items() if v not in (None, "", [], {}, 0, False)
                or k in ("holding_id",)}

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Holding":
        return cls(
            holding_id=d.get("holding_id", ""),
            contact_log=list(d.get("contact_log", [])),
            last_residual=d.get("last_residual"),
            referent_rate=d.get("referent_rate", "unknown"),
            referent_rate_days=d.get("referent_rate_days"),
            support_ids=list(d.get("support_ids", [])),
            dependents=list(d.get("dependents", [])),
            discrepancy_count=int(d.get("discrepancy_count", 0)),
            restatement_count=int(d.get("restatement_count", 0)),
            scope_hits=int(d.get("scope_hits", 0)),
            scope_misses=int(d.get("scope_misses", 0)),
            decay_class=d.get("decay_class", UNDIAGNOSED),
            cross_observer_checked=bool(d.get("cross_observer_checked", False)),
            provenance=dict(d.get("provenance", {})),
            note=d.get("note", ""),
        )


def _date(s: Optional[str]) -> Optional[datetime.date]:
    try:
        return datetime.date.fromisoformat(str(s))
    except (ValueError, TypeError):
        return None


# ── derived: computed on read, never written ──────────────────────

def decay_ratio(h: Holding, as_of: Optional[datetime.date] = None) -> Optional[float]:
    """(now - last_residual) / referent_rate. The RATIO is the reading, not the age.

    400 days on a slow referent is fine. 40 days on a fast one is already
    gone. Returns None when the rate is unknown — an uncalibrated age is not
    a small ratio, and this must not quietly become one.
    """
    last = _date(h.observed_last_residual)
    rate = h.rate_days
    if rate in (None, 0):
        return None
    if last is None:
        return float("inf")  # never touched: fully decayed against any known rate
    days = ((as_of or datetime.date.today()) - last).days
    return max(0.0, days / rate)


def trajectories(h: Holding, index: Optional[Dict[str, "Holding"]] = None,
                 as_of: Optional[datetime.date] = None) -> List[str]:
    """Which ways this holding is moving. Several may hold at once."""
    out: List[str] = []
    index = index or {}
    ratio = decay_ratio(h, as_of)
    residuals = h.residual_contacts

    if ratio is not None and ratio >= 1.0:
        out.append(DECAY)

    if h.support_ids:
        decayed_supports = [
            s for s in h.support_ids
            if s in index and (decay_ratio(index[s], as_of) or 0) >= 1.0
        ]
        if decayed_supports and len(decayed_supports) == len([s for s in h.support_ids if s in index]):
            out.append(TOWARD_UNKNOWN)

    # The split the whole tier exists to catch: an unlooked-at holding reads
    # exactly like a confirmed one unless the discriminator is enforced, and
    # the discriminator is one field — recent residual contact.
    if residuals:
        if ratio is None or ratio < 1.0:
            out.append(STALE_CONFIRMED_STABLE)
        elif STALE_UNREFRESHED not in out:
            out.append(STALE_UNREFRESHED)
    else:
        out.append(STALE_UNREFRESHED)

    if any(c.result == DISCREPANT for c in residuals):
        out.append(TOWARD_LEARNING)

    if h.restatement_count > 5 and (not residuals or (ratio is not None and ratio >= 1.0)):
        out.append(TOWARD_CIRCULATION)

    looked = h.scope_hits + h.scope_misses
    if looked and (h.scope_misses / looked) > 0.5 and h.discrepancy_count == 0:
        out.append(TOWARD_OSSIFICATION)

    return out


def reading(name: str) -> str:
    return {
        DECAY: "age past the referent's own rate. The ratio is the reading, not the age.",
        TOWARD_UNKNOWN: "the holding is intact and its ground is not. Value present, support gone "
                        "— reads as held, is not.",
        STALE_CONFIRMED_STABLE: "recent residual contact, all confirmed. Flat because the referent "
                                "is flat. High confidence.",
        STALE_UNREFRESHED: "flat because nobody looked. Confidence should be decaying and usually "
                           "is not. Conflating this with confirmed-stable is the failure the tier "
                           "exists to catch.",
        TOWARD_LEARNING: "a discrepant residual contact. Discrepancy is the only entry that "
                         "carries new information; 'confirmed' adds confidence and no content.",
        TOWARD_CIRCULATION: "motion in the record, none at the referent. Accumulating apparent "
                            "support with no new contact. Looks like learning in any activity "
                            "metric; it is the opposite thing.",
        TOWARD_OSSIFICATION: "applied further outside its stated range without generating "
                             "discrepancies — which means the discrepancies are not being "
                             "recorded, not that they are not occurring.",
    }.get(name, "")


def residual_anchored(h: Holding, index: Dict[str, Holding], _seen: Optional[set] = None) -> bool:
    """Does any path through the support graph terminate in a residual contact?

    A cluster of holdings citing one another with no residual anchor reads as
    N-fold confirmation and is depth-N transmission of one unverified holding.
    That is circulation — flag it as circulation, not as false.
    """
    seen = _seen if _seen is not None else set()
    if h.holding_id in seen:
        return False
    seen.add(h.holding_id)
    if h.residual_contacts:
        return True
    return any(residual_anchored(index[s], index, seen) for s in h.support_ids if s in index)


# ── validation ────────────────────────────────────────────────────

def validate_holding(d: Dict[str, Any]) -> List[str]:
    if not isinstance(d, dict):
        return ["holding is not an object"]
    errors: List[str] = []
    for f in REQUIRED_FIELDS:
        if f not in d:
            errors.append(f"missing required field: {f}")
    for k in d:
        if k not in REQUIRED_FIELDS + OPTIONAL_FIELDS:
            errors.append(f"unknown field: {k}")
    if "trajectory" in d or "trajectories" in d:
        errors.append("a trajectory was written into the record. Trajectories are computed on "
                      "read and never stored — a stored one is a judgement frozen at write time")
    rate = d.get("referent_rate", "unknown")
    if rate not in RATES:
        errors.append(f"referent_rate {rate!r} not one of {RATES}")
    if rate == "known" and d.get("referent_rate_days") in (None, 0):
        errors.append("referent_rate 'known' with no referent_rate_days — 'known' means measured")
    dc = d.get("decay_class", UNDIAGNOSED)
    if dc not in DECAY_CLASSES:
        errors.append(f"decay_class {dc!r} not one of {DECAY_CLASSES}")
    for c in d.get("contact_log", []):
        if not isinstance(c, dict):
            errors.append("contact_log entry is not an object")
            continue
        if _date(c.get("t")) is None:
            errors.append(f"contact_log t {c.get('t')!r} is not an ISO date")
        if c.get("kind", RESIDUAL) not in CONTACT_KINDS:
            errors.append(f"contact kind {c.get('kind')!r} not one of {CONTACT_KINDS}")
        if c.get("result", CONFIRMED) not in CONTACT_RESULTS:
            errors.append(f"contact result {c.get('result')!r} not one of {CONTACT_RESULTS}")
    if "provenance" in d:
        errors.extend(validate_provenance(d["provenance"], where="holding"))
    return errors


def audit(holdings: Optional[List[Holding]] = None,
          as_of: Optional[datetime.date] = None) -> List[str]:
    """The flag queue. Every rule here surfaces KNOWN_MISSING and nothing else."""
    hs = load_holdings() if holdings is None else holdings
    index = {h.holding_id: h for h in hs}
    findings = []
    for h in hs:
        ratio = decay_ratio(h, as_of)

        if h.restatement_count > 5 and not h.observed_last_residual:
            findings.append(f"CIRCULATION  {h.holding_id}: {h.restatement_count} restatements and "
                            f"no residual contact ever. Depth-N transmission of one unverified "
                            f"holding, not N-fold confirmation.")
        elif h.support_ids and not residual_anchored(h, index):
            findings.append(f"CIRCULATION  {h.holding_id}: no path through its supports terminates "
                            f"in a residual contact. Flag as circulation, not as false.")

        if h.support_ids:
            own = decay_ratio(h, as_of) or 0
            supports = [index[s] for s in h.support_ids if s in index]
            if supports and all((decay_ratio(s, as_of) or 0) > own for s in supports):
                findings.append(f"FLOATING     {h.holding_id}: every support is older against its "
                                f"own rate than this holding is. The ground decayed beneath it.")

        if h.discrepancy_count == 0 and h.contact_count > 20:
            findings.append(f"AMBIGUOUS    {h.holding_id}: {h.contact_count} contacts, zero "
                            f"discrepancies. Either a flat referent or an instrument that cannot "
                            f"see the referent move. Not resolvable from this field alone.")

        if ratio is not None and ratio >= 1.0 and h.decay_class == UNDIAGNOSED \
                and not h.cross_observer_checked:
            findings.append(f"PREMATURE_D1 {h.holding_id}: reads decayed, decay_class undiagnosed, "
                            f"no cross-observer check run. 'The signal is gone' is the free reading; "
                            f"'I stopped hearing' is the one that costs. Ask whether another "
                            f"receiver still resolves it before attributing this to the referent.")

        if h.referent_rate == "unknown":
            findings.append(f"UNCALIBRATED {h.holding_id}: referent_rate unknown, so its age is "
                            f"uncalibrated — order is reportable, magnitude is not. Unknown is not "
                            f"slow.")
    return findings


# ── io ────────────────────────────────────────────────────────────

def load_raw(path: Optional[pathlib.Path] = None) -> List[Dict[str, Any]]:
    p = pathlib.Path(path) if path else HOLDINGS_PATH
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


def load_holdings(path: Optional[pathlib.Path] = None) -> List[Holding]:
    return [Holding.from_dict(d) for d in load_raw(path)]


def validate_file(path: Optional[pathlib.Path] = None) -> List[str]:
    errors = []
    for i, d in enumerate(load_raw(path)):
        for e in validate_holding(d):
            errors.append(f"holding[{i}] {d.get('holding_id', '?')}: {e}")
    return errors


def format_trajectories(hs: List[Holding], as_of: Optional[datetime.date] = None) -> str:
    index = {h.holding_id: h for h in hs}
    lines = ["", "  TRAJECTORIES — computed on read, never stored", ""]
    if not hs:
        lines += ["  no holdings on file.",
                  "  The log is empty on purpose: a contact is a recorded event, and nothing",
                  "  goes in that was not observed. Decay is the only motion needing no entry —",
                  "  an empty log is not a quiet system, it is an unwatched one.", ""]
        return "\n".join(lines)
    for h in hs:
        ratio = decay_ratio(h, as_of)
        r = "n/a (rate unknown)" if ratio is None else f"{ratio:.2f}"
        lines.append(f"  {h.holding_id}   decay ratio {r}   last residual "
                     f"{h.observed_last_residual or 'never'}")
        for t in trajectories(h, index, as_of):
            lines.append(f"      {t}")
            lines.append(f"          {reading(t)}")
        lines.append("")
    return "\n".join(lines)


# ── selftest ──────────────────────────────────────────────────────

def selftest() -> List[str]:
    fails = []
    today = datetime.date(2026, 8, 24)

    def H(**kw):
        base = {"holding_id": "h", "provenance": {"concept": "MODEL", "record": "MODEL"}}
        base.update(kw)
        return Holding.from_dict(base)

    # The ratio is the reading, not the age.
    fresh_slow = H(holding_id="h1", referent_rate="slow",
                   contact_log=[{"t": "2025-08-24", "kind": RESIDUAL, "result": CONFIRMED}])
    old_fast = H(holding_id="h2", referent_rate="fast",
                 contact_log=[{"t": "2026-07-01", "kind": RESIDUAL, "result": CONFIRMED}])
    if not (decay_ratio(fresh_slow, today) < 1.0):
        fails.append("365 days on a slow referent read as decayed")
    if not (decay_ratio(old_fast, today) >= 1.0):
        fails.append("54 days on a fast referent did not read as decayed")

    if decay_ratio(H(referent_rate="unknown"), today) is not None:
        fails.append("an unknown rate produced a ratio — unknown must not become slow")
    if RATE_DAYS["unknown"] is not None:
        fails.append("unknown was given a day count")

    # The split the tier exists to catch.
    s1 = H(holding_id="s1", referent_rate="slow",
           contact_log=[{"t": "2026-08-01", "kind": RESIDUAL, "result": CONFIRMED}])
    s2 = H(holding_id="s2", referent_rate="slow", contact_log=[])
    if STALE_CONFIRMED_STABLE not in trajectories(s1, {}, today):
        fails.append("recent confirmed residual contact did not read as confirmed-stable")
    if STALE_UNREFRESHED not in trajectories(s2, {}, today):
        fails.append("a holding nobody looked at did not read as unrefreshed")
    if set(trajectories(s1, {}, today)) & set(trajectories(s2, {}, today)) & {
            STALE_CONFIRMED_STABLE, STALE_UNREFRESHED}:
        fails.append("confirmed-stable and unrefreshed were not kept apart")

    learn = H(holding_id="l", referent_rate="slow",
              contact_log=[{"t": "2026-08-01", "kind": RESIDUAL, "result": DISCREPANT}])
    if TOWARD_LEARNING not in trajectories(learn, {}, today):
        fails.append("a discrepant contact did not read as learning")

    circ = H(holding_id="c", restatement_count=7, referent_rate="slow", contact_log=[])
    if TOWARD_CIRCULATION not in trajectories(circ, {}, today):
        fails.append("restatements with no residual contact did not read as circulation")
    if not any(f.startswith("CIRCULATION") for f in audit([circ], today)):
        fails.append("circulation not flagged")

    oss = H(holding_id="o", referent_rate="slow", scope_hits=2, scope_misses=9,
            discrepancy_count=0,
            contact_log=[{"t": "2026-08-01", "kind": RESIDUAL, "result": CONFIRMED}])
    if TOWARD_OSSIFICATION not in trajectories(oss, {}, today):
        fails.append("use outside scope with no discrepancies did not read as ossification")

    # A cluster citing itself, with no residual anchor anywhere.
    a = H(holding_id="a", support_ids=["b"], referent_rate="slow")
    b = H(holding_id="b", support_ids=["a"], referent_rate="slow")
    index = {"a": a, "b": b}
    if residual_anchored(a, index):
        fails.append("a cycle with no residual anchor reported as anchored")
    if not any("CIRCULATION" in f for f in audit([a, b], today)):
        fails.append("an unanchored cluster was not flagged as circulation")
    anchored = H(holding_id="z", contact_log=[{"t": "2026-08-01", "kind": RESIDUAL}],
                 referent_rate="slow")
    c = H(holding_id="c2", support_ids=["z"], referent_rate="slow")
    if not residual_anchored(c, {"z": anchored, "c2": c}):
        fails.append("a path terminating in residual contact was not found")

    amb = H(holding_id="amb", referent_rate="slow", discrepancy_count=0,
            contact_log=[{"t": "2026-08-01", "kind": RESIDUAL} for _ in range(21)])
    if not any("AMBIGUOUS" in f for f in audit([amb], today)):
        fails.append("zero discrepancies over many contacts was not reported as ambiguous")
    if any("resolved" in f.lower() and "not resolvable" not in f.lower()
           for f in audit([amb], today)):
        fails.append("the ambiguous case was resolved rather than reported")

    stale_d1 = H(holding_id="d", referent_rate="fast",
                 contact_log=[{"t": "2026-01-01", "kind": RESIDUAL}])
    if not any("PREMATURE_D1" in f for f in audit([stale_d1], today)):
        fails.append("a decayed undiagnosed holding with no cross-observer check was not flagged")
    checked = H(holding_id="d2", referent_rate="fast", cross_observer_checked=True,
                contact_log=[{"t": "2026-01-01", "kind": RESIDUAL}])
    if any("PREMATURE_D1" in f for f in audit([checked], today)):
        fails.append("a cross-observer-checked holding was still flagged")
    if H().decay_class != UNDIAGNOSED:
        fails.append("decay_class did not default to undiagnosed")

    if not any("trajectory" in e for e in validate_holding(
            {"holding_id": "x", "provenance": {"concept": "MODEL", "record": "MODEL"},
             "trajectory": DECAY})):
        fails.append("a written-in trajectory was accepted")
    if not validate_holding({"holding_id": "x"}):
        fails.append("a holding with no provenance was accepted")
    if not validate_holding({"holding_id": "x", "provenance": {"concept": "MODEL", "record": "MODEL"},
                             "referent_rate": "known"}):
        fails.append("referent_rate 'known' with no measured days was accepted")

    # gaps of 10, 10 and 30 days -> median 10, and the outlier must not drag it
    iv = H(contact_log=[{"t": "2026-01-01", "kind": RESIDUAL}, {"t": "2026-01-11", "kind": RESIDUAL},
                        {"t": "2026-01-21", "kind": RESIDUAL}, {"t": "2026-02-20", "kind": RESIDUAL}])
    if iv.contact_interval != 10.0:
        fails.append(f"median residual interval wrong: {iv.contact_interval}")
    if H(contact_log=[{"t": "2026-01-01"}]).contact_interval is not None:
        fails.append("an interval was computed from a single contact")

    if set(GAP_REACH) != {KNOWN_MISSING, KNOWN_UNRESOLVED, UNMARKED_GAP}:
        fails.append("gap reach classes incomplete")
    if validate_file():
        fails.append("shipped holdings.jsonl does not validate")
    return fails


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="holdings — contact log in, trajectories out")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--trajectories", action="store_true")
    ap.add_argument("--audit", action="store_true", help="the flag queue — KNOWN_MISSING only")
    ap.add_argument("--gaps", action="store_true", help="which operator can reach which gap class")
    ap.add_argument("--path")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args(argv)

    if args.selftest:
        f = selftest()
        for line in f:
            print(f"FAIL  {line}")
        print("holding: OK" if not f else f"holding: {len(f)} FAILED")
        return 1 if f else 0

    path = pathlib.Path(args.path) if args.path else None

    if args.gaps:
        if args.json:
            print(json.dumps(GAP_REACH, indent=2))
        else:
            print("\n  GAP CLASSES — which operator can reach each")
            print("  (not gap_scan's G1-G4; different axis, spelled out so the two cannot merge)\n")
            for k, v in GAP_REACH.items():
                print(f"  {k}\n      {v}\n")
            print("  The flag queue surfaces KNOWN_MISSING and nothing else. Curiosity aimed at")
            print("  the queue is aimed at the cheapest and least informative class, and will")
            print("  feel productive the whole time.\n")
        return 0

    hs = load_holdings(path)
    if args.audit:
        findings = audit(hs)
        if args.json:
            print(json.dumps({"findings": findings}, indent=2))
        else:
            for x in findings:
                print(f"  {x}")
            print("holdings audit: CLEAN" if not findings else
                  f"holdings audit: {len(findings)} flag(s)")
        return 0

    if args.trajectories:
        print(format_trajectories(hs))
        return 0

    if args.json:
        print(json.dumps([h.to_dict() for h in hs], indent=2))
    else:
        print(f"\n  HOLDINGS ({len(hs)})\n")
        for h in hs:
            print(f"  {h.holding_id}  last residual {h.observed_last_residual or 'never'}  "
                  f"rate {h.referent_rate}  decay_class {h.decay_class}")
        if not hs:
            print("  empty. A contact is a recorded event; nothing goes in that was not observed.")
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
