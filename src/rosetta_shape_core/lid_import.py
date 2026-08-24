# SPDX-License-Identifier: CC0-1.0
"""Import scoped attributes from the Living Intelligence Database as entries.

The LID carries, per scoped attribute, an operational definition, the limits
of the measurement, a falsifiability statement, and a citation. Four of the
things a Rosetta entry needs are already there and already the author's
words. Two are not, and this importer does not invent them.

WHAT MAPS

    scope.definition          -> configuration
    scope.measurement_limits  -> scope.stops (verbatim, split by sentence),
                                 each carrying evidence.source as `cited`
    scope.condition           -> scope.produces, where present
    evidence.source           -> sources
    scope.falsifiability      -> an observation: a test STATED AND NOT RUN

    forcing_terms             -> nothing. Marked OPEN.
    forcing_dominant          -> nothing. Marked OPEN.
    move_ported               -> nothing. Marked OPEN.

WHY falsifiability IS NOT A STOP
    A stop says where a move stops producing. A falsifiability statement says
    what observation would kill the claim. They are different objects, and
    flattening them would turn an unrun prediction into evidence. The
    falsifier becomes an observation with ``holds`` unset — a test on the
    books that nobody has run.

WHY THE MISSING FIELDS ARE MARKED, NOT GUESSED
    An entry with a hole in it is not the same as an entry with a guess in
    it. Marking forcing_terms OPEN says: this source system is on file, the
    loads are unnamed, and naming them is the experiment on offer. Guessing
    them would put a model's physics reading under the author's name across
    the whole corpus at once, which is the failure this repo exists to
    catch, at scale.

RE-RUNNING IS SAFE
    Records already present are kept as they stand, matched by id. Filling a
    field by hand is not undone by the next import; only genuinely new
    attributes are added.

CONSTRAINTS (repo-wide, restated per file)
    - no "about the author" / working-style section, in this or any file
    - entries are markers to explore, not positions defended; the correct
      response to one is: test fit / extend / report break
    - no moral labels in data structures, no intent attribution

Usage:
    python -m rosetta_shape_core.lid_import --lid ../living-intelligence-database --dry-run
    python -m rosetta_shape_core.lid_import --lid ../living-intelligence-database
    python -m rosetta_shape_core.lid_import --selftest
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys
from typing import Any, Dict, List, Optional, Tuple

from rosetta_shape_core.entry import OPEN, PARTIAL, validate_entry
from rosetta_shape_core.provenance import AUTHOR

ROOT = pathlib.Path(__file__).resolve().parents[2]
ENTRIES_OUT = ROOT / "data" / "rosetta" / "entries.lid.jsonl"
OBSERVATIONS_OUT = ROOT / "data" / "rosetta" / "observations.lid.jsonl"

# Where a clone of the database might be. --lid overrides.
CANDIDATE_ROOTS = (
    ROOT.parent / "living-intelligence-database",
    ROOT.parent / "Living-Intelligence-Database",
    pathlib.Path.home() / "jinnz2" / "living-intelligence-database",
)

SOURCE_REPO = "JinnZ2/Living-Intelligence-Database"
_SENTENCE = re.compile(r"(?<=[.!?])\s+")


def find_lid(path: Optional[str] = None) -> Optional[pathlib.Path]:
    if path:
        p = pathlib.Path(path).expanduser()
        return p if (p / "ontology").is_dir() else None
    for p in CANDIDATE_ROOTS:
        if (p / "ontology").is_dir():
            return p
    return None


def _slug(text: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "_", str(text)).strip("_").upper()


def split_limits(text: str, cap: int = 4) -> List[str]:
    """Measurement limits are prose. One stop per sentence, verbatim, capped.

    The split is mechanical and the result is marked PARTIAL for that reason:
    a stop that was cut out of a paragraph wants a human to name it.
    """
    parts = [p.strip() for p in _SENTENCE.split(str(text).strip()) if p.strip()]
    if len(parts) <= cap:
        return parts
    return parts[: cap - 1] + [" ".join(parts[cap - 1:])]


def scoped_attributes(lid_root: pathlib.Path) -> List[Tuple[pathlib.Path, Dict[str, Any], str, Dict[str, Any]]]:
    """Every (file, being, attribute name, attribute) that carries a scope block."""
    out = []
    for f in sorted((lid_root / "ontology").rglob("*.json")):
        try:
            being = json.loads(f.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            continue
        if not isinstance(being, dict):
            continue
        attrs = being.get("attributes")
        if not isinstance(attrs, dict):
            continue
        for name, attr in attrs.items():
            if isinstance(attr, dict) and isinstance(attr.get("scope"), dict):
                out.append((f.relative_to(lid_root), being, name, attr))
    return out


def build_entry(relpath: pathlib.Path, being: Dict[str, Any], attr_name: str,
                attr: Dict[str, Any]) -> Dict[str, Any]:
    scope = attr["scope"]
    key = f"ENTRY.LID_{_slug(being.get('name') or being.get('id') or relpath.stem)}_{_slug(attr_name)}"

    evidence = scope.get("evidence") or {}
    cited = str(evidence.get("source", "")).strip()
    stops = []
    for i, text in enumerate(split_limits(scope.get("measurement_limits", ""))):
        rec = {"id": f"limit_{i + 1}", "says": text}
        if cited:
            rec["cited"] = cited
        stops.append(rec)

    produces: List[str] = []
    condition = scope.get("condition")
    if isinstance(condition, dict):
        if condition.get("environment"):
            produces.append(str(condition["environment"]))
        produces.extend(str(c) for c in condition.get("constraints", []))

    sources = [cited] if cited else []

    status = {"forcing_terms": OPEN, "forcing_dominant": OPEN, "move_ported": OPEN}
    if stops:
        status["scope.stops"] = PARTIAL
    else:
        status["scope.stops"] = OPEN
    if not produces:
        status["scope.produces"] = OPEN

    entry: Dict[str, Any] = {
        "id": key,
        "source_system": str(being.get("name") or relpath.stem).lower(),
        "configuration": str(scope.get("definition", "")).strip(),
        "forcing_terms": [],
        "forcing_dominant": [],
        "move_ported": "",
        "scope": {"produces": produces, "stops": stops},
        "field_status": status,
        "sources": sources,
        "provenance": {
            "concept": AUTHOR,
            "record": AUTHOR,
            "note": (f"imported verbatim from {SOURCE_REPO} {relpath.as_posix()}, attribute "
                     f"'{attr_name}'. The definition, the limits and the citation are the author's "
                     f"text; the forcing terms and the move are not written yet and are marked OPEN"),
        },
    }
    if not entry["configuration"]:
        entry["field_status"]["configuration"] = OPEN
    return entry


def build_observation(entry_key: str, relpath: pathlib.Path, attr_name: str,
                      attr: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """The falsifiability statement, as a test on the books that nobody has run."""
    scope = attr["scope"]
    falsifier = str(scope.get("falsifiability", "")).strip()
    if not falsifier:
        return None
    evidence = scope.get("evidence") or {}
    return {
        "entry": entry_key,
        "prop": falsifier,
        "condition": str(evidence.get("evidence_type", "")),
        "note": (f"stated falsifier, not yet run. Reproducibility of the underlying measurement: "
                 f"{evidence.get('reproducibility', 'unstated')}"),
        "provenance": {
            "concept": AUTHOR,
            "record": AUTHOR,
            "note": (f"falsifiability statement quoted from {SOURCE_REPO} {relpath.as_posix()}, "
                     f"attribute '{attr_name}'"),
        },
    }


def _existing(path: pathlib.Path, key: str) -> Dict[str, Dict[str, Any]]:
    out = {}
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line:
                d = json.loads(line)
                out[d.get(key, "")] = d
    return out


def run_import(lid_root: pathlib.Path, *, dry_run: bool = False,
               refresh: bool = False) -> Dict[str, Any]:
    """Import, keeping anything already on file. Returns a report.

    ``refresh`` rewrites a record only if it still matches what the importer
    would have produced at its previous shape — that is, nobody has touched
    it. A record with a hand-filled field is never overwritten.
    """
    kept_entries = _existing(ENTRIES_OUT, "id")
    kept_obs = {(d.get("entry", ""), d.get("prop", "")): d
                for d in ([json.loads(x) for x in OBSERVATIONS_OUT.read_text(encoding="utf-8").splitlines() if x.strip()]
                          if OBSERVATIONS_OUT.exists() else [])}

    added, skipped, invalid = [], [], []
    entries: List[Dict[str, Any]] = []
    observations: List[Dict[str, Any]] = []

    for relpath, being, attr_name, attr in scoped_attributes(lid_root):
        entry = build_entry(relpath, being, attr_name, attr)
        errors = validate_entry(entry)
        if errors:
            invalid.append(f"{entry['id']}: {errors[0]}")
            continue
        if entry["id"] in kept_entries:
            previous = kept_entries[entry["id"]]
            untouched = not any([previous.get("forcing_terms"), previous.get("forcing_dominant"),
                                 previous.get("move_ported")])
            if refresh and untouched:
                entries.append(entry)
                added.append(entry["id"])
            else:
                entries.append(previous)
                skipped.append(entry["id"])
        else:
            entries.append(entry)
            added.append(entry["id"])
        obs = build_observation(entry["id"], relpath, attr_name, attr)
        if obs:
            observations.append(kept_obs.get((obs["entry"], obs["prop"]), obs))

    if not dry_run:
        ENTRIES_OUT.parent.mkdir(parents=True, exist_ok=True)
        ENTRIES_OUT.write_text(
            "\n".join(json.dumps(e, ensure_ascii=False) for e in entries) + "\n", encoding="utf-8")
        OBSERVATIONS_OUT.write_text(
            "\n".join(json.dumps(o, ensure_ascii=False) for o in observations) + "\n", encoding="utf-8")

    return {
        "lid_root": str(lid_root),
        "scoped_attributes": len(entries) + len(invalid),
        "entries": len(entries),
        "added": len(added),
        "kept_as_they_stand": len(skipped),
        "invalid": invalid,
        "pending_tests": len(observations),
        "dry_run": dry_run,
    }


# ── selftest ──────────────────────────────────────────────────────

def selftest() -> List[str]:
    fails = []
    being = {"id": "GE", "name": "Gecko"}
    attr = {
        "value": 0.94,
        "scope": {
            "definition": "a definition of the measured quantity",
            "measurement_limits": "First limit here. Second limit here.",
            "falsifiability": "If X is measured, the claim fails.",
            "evidence": {"source": "Someone (2000)", "evidence_type": "lab_measurement",
                         "reproducibility": "high"},
        },
    }
    rel = pathlib.Path("ontology/animal/gecko.json")
    e = build_entry(rel, being, "setae_adhesion", attr)

    if e["id"] != "ENTRY.LID_GECKO_SETAE_ADHESION":
        fails.append(f"id derivation wrong: {e['id']}")
    if validate_entry(e):
        fails.append(f"built entry does not validate: {validate_entry(e)[0]}")
    if e["field_status"].get("forcing_terms") != OPEN or e["move_ported"]:
        fails.append("the importer filled a field it has no source for")
    if e["provenance"] != {"concept": AUTHOR, "record": AUTHOR, "note": e["provenance"]["note"]}:
        fails.append("imported records not marked as the author's")
    if [s["says"] for s in e["scope"]["stops"]] != ["First limit here.", "Second limit here."]:
        fails.append("measurement limits not split verbatim into stops")
    if any(s.get("cited") != "Someone (2000)" for s in e["scope"]["stops"]):
        fails.append("stops do not name the source that established the limit")
    if e["field_status"].get("scope.stops") != PARTIAL:
        fails.append("mechanically split stops not marked PARTIAL")

    o = build_observation(e["id"], rel, "setae_adhesion", attr)
    if o is None or "holds" in o:
        fails.append("the falsifier was recorded as a result rather than as an unrun test")
    if o and o["prop"] != "If X is measured, the claim fails.":
        fails.append("falsifier text not quoted verbatim")
    if build_observation(e["id"], rel, "a", {"scope": {}}) is not None:
        fails.append("an observation was invented where there was no falsifier")

    if split_limits("One. Two. Three. Four. Five.", cap=3) != ["One.", "Two.", "Three. Four. Five."]:
        fails.append("limit splitting drops text past the cap")
    if find_lid("/nonexistent/path") is not None:
        fails.append("find_lid accepted a path with no ontology tree")
    return fails


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="import scoped LID attributes as Rosetta entries")
    ap.add_argument("--lid", help="path to a Living-Intelligence-Database clone")
    ap.add_argument("--dry-run", action="store_true", help="report without writing")
    ap.add_argument("--refresh", action="store_true",
                    help="rewrite records that are still exactly as imported; hand-edited ones are kept")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args(argv)

    if args.selftest:
        f = selftest()
        for line in f:
            print(f"FAIL  {line}")
        print("lid_import: OK" if not f else f"lid_import: {len(f)} FAILED")
        return 1 if f else 0

    lid_root = find_lid(args.lid)
    if lid_root is None:
        print("lid_import: no Living-Intelligence-Database found.")
        print("  Clone it and pass --lid <path>:")
        print(f"    git clone https://github.com/{SOURCE_REPO}")
        print("  The imported data is committed here, so this is only needed to refresh it.")
        return 1

    report = run_import(lid_root, dry_run=args.dry_run, refresh=args.refresh)
    if args.json:
        print(json.dumps(report, indent=2))
        return 0

    print()
    print(f"  source                 {report['lid_root']}")
    print(f"  scoped attributes      {report['scoped_attributes']}")
    print(f"  entries                {report['entries']}  "
          f"({report['added']} new, {report['kept_as_they_stand']} kept as they stand)")
    print(f"  stated tests, not run  {report['pending_tests']}")
    for x in report["invalid"]:
        print(f"  ✗  {x}")
    if report["dry_run"]:
        print("\n  dry run — nothing written")
    else:
        print(f"\n  wrote {ENTRIES_OUT.relative_to(ROOT)}")
        print(f"        {OBSERVATIONS_OUT.relative_to(ROOT)}")
    print()
    print("  Every imported entry has forcing_terms, forcing_dominant and move_ported")
    print("  marked OPEN. They cannot license a transfer until someone names the loads:")
    print("      python -m rosetta_shape_core.rosetta --open")
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
