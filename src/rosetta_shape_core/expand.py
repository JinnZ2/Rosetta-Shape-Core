from __future__ import annotations
import json, pathlib, argparse, sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
RULES_PATH = ROOT / "rules" / "expand.jsonl"
ONTO_DIR = ROOT / "ontology"

def _load_all_entities():
    entities = {}
    for p in ONTO_DIR.glob("*.json"):
        data = json.loads(p.read_text(encoding="utf-8"))
        for e in data.get("entities", []):
            entities[e["id"]] = e
    return entities

def _load_rules():
    rules = []
    if RULES_PATH.exists():
        for line in RULES_PATH.read_text(encoding="utf-8").splitlines():
            if line.strip():
                rules.append(json.loads(line))
    return sorted(rules, key=lambda r: -r.get("priority", 0))

def _has_caps(entity, needed):
    got = set(entity.get("capabilities", []))
    return all(req in got for req in needed)

def apply_rule(op: str, args: list[str], have_caps: list[str] | None = None) -> dict:
    """Return best matching rule output or an empty result."""
    rules = _load_rules()
    ents = _load_all_entities()
    # Allow capability checks on subject arg 0 if guard.requires present
    subj = ents.get(args[0], {})
    subj_caps = set(subj.get("capabilities", [])) | set(have_caps or [])
    for r in rules:
        w = r.get("when", {})
        if w.get("op") != op: 
            continue
        if w.get("args") != args:
            continue
        guard = r.get("guard", {})
        if guard:
            req = set(guard.get("requires", []))
            if not req.issubset(subj_caps):
                continue
        return {"then": r["then"], "why": r.get("why"), "rule": r}
    return {}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("op", help="Operation, e.g., ALIGN | EXPAND | STRUCTURE")
    ap.add_argument("arg0")
    ap.add_argument("arg1", nargs="?")
    ap.add_argument("--have", nargs="*", default=[], help="Extra capabilities to satisfy guards")
    args = ap.parse_args()

    arg_list = [a for a in [args.arg0, args.arg1] if a]
    res = apply_rule(args.op, arg_list, have_caps=args.have)
    print(json.dumps({"op": args.op, "args": arg_list, "result": res or None}, indent=2))

if __name__ == "__main__":
    sys.exit(main())
