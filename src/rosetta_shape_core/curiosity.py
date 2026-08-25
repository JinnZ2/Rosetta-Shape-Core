# SPDX-License-Identifier: CC0-1.0
"""Curiosity — the allocator. Which expensive operation gets paid for.

    decay     free. Runs with no input. Always on.
    contact   expensive. Requires initiation.

Nothing in the record initiates. The trajectory system in holding.py detects
motion it cannot cause, so without an allocator only decay runs and the whole
apparatus is a well-instrumented record of its own deterioration.

That makes curiosity a budget allocation function over the flag queue rather
than a disposition — which is what makes it specifiable at all, and what this
module is.

THE OFFSET IS MANDATORY, OR THE SYSTEM SELF-SEALS

    The flag queue surfaces KNOWN_MISSING and nothing else: empty fields,
    absent supports, things the record can already see are missing. That is
    the cheapest and least informative gap class, and spending the whole
    budget there feels productive the entire time.

    UNMARKED gaps — an axis never sampled, no entry, no flag — are
    unreachable by ANY ranking computed over current holdings, because the
    ranking is built from the very set that excludes them. No internal signal
    exists for a channel you do not have.

    So a fixed fraction of the budget is allocated outside the queue
    entirely: unranked, unjustified, not derived from existing holdings.
    ``allocate()`` refuses an offset of zero. That refusal is the point of
    the module.

CONSTRAINTS (repo-wide, restated per file)
    - no "about the author" / working-style section, in this or any file
    - entries are markers to explore, not positions defended; the correct
      response to one is: test fit / extend / report break
    - no moral labels in data structures, no intent attribution
      (a holding is ranked by load and decay, never by how interesting
      anyone finds it)

Usage:
    python -m rosetta_shape_core.curiosity --triggers
    python -m rosetta_shape_core.curiosity --allocate --budget 10
    python -m rosetta_shape_core.curiosity --selftest
"""
from __future__ import annotations

import argparse
import datetime
import json
import math
import sys
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional

from rosetta_shape_core.holding import (
    KNOWN_MISSING,
    KNOWN_UNRESOLVED,
    UNMARKED_GAP,
    Holding,
    decay_ratio,
    load_holdings,
)

# What an audit is fired by. Recorded conditions, not judgements.
AUDIT_TRIGGERS: Dict[str, str] = {
    "discrepancy recorded": "audit its supports — one of them may be what moved",
    "scope_miss": "audit valid_on — the stated range may be wrong, or the use was",
    "restatement without residual": "d3 lineage — check for circulation before it accumulates",
    "schedule": "d1 dimensional sweep over the whole set. Cheapest kill available",
}

# The fraction of budget that must be spent outside the queue. Not a default
# to be tuned to zero: allocate() rejects zero, because zero is the
# self-sealing configuration.
DEFAULT_OFFSET = 0.2


@dataclass
class Allocation:
    """A budget split. Ranked work, plus the part that cannot be ranked."""

    queue: List[Dict[str, Any]] = field(default_factory=list)
    offset: int = 0
    offset_fraction: float = DEFAULT_OFFSET
    unrankable: str = ""
    note: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


def priority(h: Holding, as_of: Optional[datetime.date] = None) -> Optional[float]:
    """dependents x (age / referent_rate). Highest = load-bearing AND most decayed.

    Returns None when the rate is unknown: an uncalibrated age cannot be
    ranked against a calibrated one, and silently treating unknown as slow
    would push exactly the unmeasured holdings to the bottom of the queue.
    """
    ratio = decay_ratio(h, as_of)
    if ratio is None:
        return None
    if math.isinf(ratio):
        ratio = float(len(h.dependents) + 1) * 1000.0
    return (len(h.dependents) or 1) * ratio


def rank(holdings: Optional[List[Holding]] = None,
         as_of: Optional[datetime.date] = None) -> List[Dict[str, Any]]:
    """The queue, highest first. Unrankable holdings are reported, not dropped."""
    hs = load_holdings() if holdings is None else holdings
    ranked, unrankable = [], []
    for h in hs:
        p = priority(h, as_of)
        row = {
            "holding_id": h.holding_id,
            "dependents": len(h.dependents),
            "decay_ratio": None if decay_ratio(h, as_of) is None else round(decay_ratio(h, as_of), 3),
            "priority": None if p is None else round(p, 3),
            "reach": KNOWN_MISSING,
        }
        (unrankable if p is None else ranked).append(row)
    ranked.sort(key=lambda r: -r["priority"])
    for row in unrankable:
        row["why_unrankable"] = ("referent_rate unknown — order is reportable, magnitude is not, "
                                 "and unknown is not slow")
    return ranked + unrankable


def triggered(h: Holding) -> List[str]:
    """Which audit triggers this holding currently satisfies."""
    out = []
    if h.discrepancy_count > 0:
        out.append("discrepancy recorded")
    if h.scope_misses > 0:
        out.append("scope_miss")
    if h.restatement_count > 0 and not h.observed_last_residual:
        out.append("restatement without residual")
    return out


def allocate(budget: int, holdings: Optional[List[Holding]] = None, *,
             offset_fraction: float = DEFAULT_OFFSET,
             as_of: Optional[datetime.date] = None) -> Allocation:
    """Split a budget between the ranked queue and the part that cannot be ranked.

    Raises on an offset of zero. A ranking computed over current holdings
    cannot reach a gap those holdings do not mark, so an all-queue allocation
    is not an aggressive configuration — it is a closed one.
    """
    if budget < 0:
        raise ValueError("budget must not be negative")
    if offset_fraction <= 0:
        raise ValueError(
            "offset_fraction must be greater than zero. UNMARKED gaps are unreachable by any "
            "ranking computed over current holdings, so an allocation with no offset can only "
            "ever find what the record already marks."
        )
    if offset_fraction >= 1:
        raise ValueError("offset_fraction must be below one, or nothing services the queue")

    offset = max(1, int(round(budget * offset_fraction))) if budget else 0
    offset = min(offset, budget)
    queue = rank(holdings, as_of)[: budget - offset] if budget else []
    return Allocation(
        queue=queue,
        offset=offset,
        offset_fraction=offset_fraction,
        unrankable=UNMARKED_GAP,
        note=("the offset is spent outside the queue entirely — unranked, unjustified, not "
              "derived from existing holdings. It is the only allocation that can reach an axis "
              "nothing in the record marks, and the reach is cross-station comparison (a04)."),
    )


def format_allocation(a: Allocation) -> str:
    lines = ["", "  ALLOCATION", ""]
    lines.append(f"  queue      {len(a.queue)} item(s), ranked by dependents x (age / rate)")
    for row in a.queue:
        p = "unrankable" if row["priority"] is None else f"{row['priority']:.2f}"
        lines.append(f"      {p:>10s}  {row['holding_id']}  "
                     f"dependents {row['dependents']}  reach {row['reach']}")
    lines.append("")
    lines.append(f"  offset     {a.offset} ({a.offset_fraction:.0%}) — reach {a.unrankable}")
    lines.append(f"             {a.note}")
    lines.append("")
    lines.append(f"  The queue can only reach {KNOWN_MISSING}. {KNOWN_UNRESOLVED} needs an")
    lines.append("  instrument built; it is expensive and it is the productive class.")
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

    load_bearing = H(holding_id="load", referent_rate="fast", dependents=["a", "b", "c"],
                     contact_log=[{"t": "2026-01-01", "kind": "residual"}])
    leaf = H(holding_id="leaf", referent_rate="fast", dependents=[],
             contact_log=[{"t": "2026-08-20", "kind": "residual"}])
    if not (priority(load_bearing, today) > priority(leaf, today)):
        fails.append("a load-bearing decayed holding did not outrank a fresh leaf")

    if priority(H(referent_rate="unknown"), today) is not None:
        fails.append("an unknown-rate holding was given a priority")
    ranked = rank([H(holding_id="u", referent_rate="unknown"), leaf], today)
    if ranked[0]["holding_id"] != "leaf":
        fails.append("a rankable holding did not come before an unrankable one")
    if "why_unrankable" not in ranked[-1]:
        fails.append("an unrankable holding was dropped rather than reported")

    for bad in (0, -0.1, 1.0, 2):
        try:
            allocate(10, [leaf], offset_fraction=bad)
        except ValueError:
            continue
        fails.append(f"offset_fraction {bad} accepted — zero is the self-sealing configuration")

    a = allocate(10, [load_bearing, leaf], offset_fraction=0.2, as_of=today)
    if a.offset != 2:
        fails.append(f"offset wrong: {a.offset}")
    if len(a.queue) != 8 and len(a.queue) > 2:
        fails.append("queue length ignored the budget")
    if a.unrankable != UNMARKED_GAP:
        fails.append("the offset was not aimed at the unreachable class")
    if allocate(1, [leaf], as_of=today).offset != 1:
        fails.append("a budget of one spent nothing outside the queue")
    if allocate(0, [], as_of=today).offset != 0:
        fails.append("an empty budget allocated an offset")

    if set(triggered(H(discrepancy_count=1, scope_misses=2, restatement_count=3))) != {
            "discrepancy recorded", "scope_miss", "restatement without residual"}:
        fails.append("audit triggers not detected")
    if triggered(H()):
        fails.append("a quiet holding fired a trigger")
    for name in triggered(H(discrepancy_count=1)):
        if name not in AUDIT_TRIGGERS:
            fails.append(f"trigger {name!r} has no entry in AUDIT_TRIGGERS")

    if all(r["reach"] == KNOWN_MISSING for r in rank([leaf], today)) is False:
        fails.append("the queue claimed to reach past KNOWN_MISSING")
    return fails


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="curiosity — allocate the expensive operations")
    ap.add_argument("--triggers", action="store_true", help="what fires an audit")
    ap.add_argument("--rank", action="store_true", help="the queue, highest first")
    ap.add_argument("--allocate", action="store_true")
    ap.add_argument("--budget", type=int, default=10)
    ap.add_argument("--offset", type=float, default=DEFAULT_OFFSET)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args(argv)

    if args.selftest:
        f = selftest()
        for line in f:
            print(f"FAIL  {line}")
        print("curiosity: OK" if not f else f"curiosity: {len(f)} FAILED")
        return 1 if f else 0

    if args.triggers:
        if args.json:
            print(json.dumps(AUDIT_TRIGGERS, indent=2))
        else:
            print("\n  AUDIT TRIGGERS — recorded conditions, not judgements\n")
            for k, v in AUDIT_TRIGGERS.items():
                print(f"  on {k:32s} {v}")
            print()
        return 0

    if args.rank:
        rows = rank(as_of=None)
        print(json.dumps(rows, indent=2) if args.json else
              "\n".join(f"  {r['priority']}  {r['holding_id']}" for r in rows) or
              "  no holdings to rank")
        return 0

    try:
        a = allocate(args.budget, offset_fraction=args.offset)
    except ValueError as exc:
        print(f"curiosity: {exc}")
        return 1
    print(json.dumps(a.to_dict(), indent=2) if args.json else format_allocation(a))
    return 0


if __name__ == "__main__":
    sys.exit(main())
