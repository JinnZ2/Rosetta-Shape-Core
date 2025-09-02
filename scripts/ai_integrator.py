
import os, re, sys, json, argparse, hashlib, datetime, glob, yaml
from pathlib import Path

def sha1(path, sample_bytes=None):
    h = hashlib.sha1()
    with open(path, 'rb') as f:
        if sample_bytes:
            h.update(f.read(sample_bytes))
        else:
            while True:
                data = f.read(8192)
                if not data: break
                h.update(data)
    return h.hexdigest()

LANG_MAP = {
    ".py":"python",".rs":"rust",".c":"c",".h":"c-hdr",".cpp":"cpp",".hpp":"cpp-hdr",
    ".json":"json",".yaml":"yaml",".yml":"yaml",".md":"md",".toml":"toml"
}

def guess_lang(p):
    return LANG_MAP.get(p.suffix.lower(), "unknown")

def load_cfg(path):
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def match_any(path, patterns):
    from fnmatch import fnmatch
    return any(fnmatch(path, pat) for pat in patterns or [])

def find_hotspots(text, rules):
    res = []
    for r in rules or []:
        flags = 0
        if 'flags' in r and 'i' in r['flags'].lower():
            flags |= re.IGNORECASE
        if re.search(r.get('pattern',''), text, flags):
            res.append(r.get('name','rule'))
    return sorted(set(res))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--config", default="ai_integrator.config.yaml")
    args = ap.parse_args()

    cfg = load_cfg(args.config)
    root = Path(args.repo_root).resolve()
    include = cfg["index"]["include_globs"]
    exclude = cfg["index"]["exclude_globs"]
    max_bytes = int(cfg["analysis"]["max_file_bytes"])
    sample_bytes = int(cfg["analysis"]["sample_bytes_per_large_file"])
    hotspot_rules = cfg["analysis"]["hotspot_rules"]
    outputs = cfg["outputs"]
    schema_file = outputs.get("schema_file","schemas/ai_index.schema.json")

    files = []
    languages = set()
    for pat in include:
        for rel in glob.glob(str(root / pat), recursive=True):
            relp = str(Path(rel).resolve())
            relpath = os.path.relpath(relp, str(root))
            if os.path.isdir(relp): 
                continue
            if match_any(relpath, exclude): 
                continue
            p = Path(relp)
            size = p.stat().st_size
            lang = guess_lang(p)
            languages.add(lang)
            # small fingerprint
            h = sha1(relp, sample_bytes if size > max_bytes else None)
            hotspots = []
            try:
                if size <= max_bytes and p.suffix.lower() not in [".png",".jpg",".jpeg",".gif",".bin",".pdf"]:
                    with open(relp, 'r', encoding='utf-8', errors='ignore') as f:
                        txt = f.read()
                    hotspots = find_hotspots(txt, hotspot_rules)
                else:
                    hotspots = []
            except Exception as e:
                hotspots = [f"read_error:{type(e).__name__}"]
            files.append({
                "path": relpath,
                "lang": lang,
                "size": size,
                "hash": h,
                "roles": [],
                "imports": [],
                "exports": [],
                "hotspots": hotspots
            })

    index = {
        "repo": root.name,
        "generated_at": datetime.datetime.utcnow().isoformat() + "Z",
        "languages": sorted(languages - {"unknown"}) if languages else [],
        "files": files,
        "topology": {"modules": [], "edges": []},
        "resilience": {
            "redundancy_patterns": [],
            "fallback_branches": [],
            "error_doctrine": "tbd",
            "possibility_matrix": []
        }
    }

    out_index = root / outputs["index_file"]
    out_notes  = root / outputs["notes_file"]
    os.makedirs(out_index.parent, exist_ok=True)

    with open(out_index, 'w', encoding='utf-8') as f:
        json.dump(index, f, indent=2)

    # Notes: summarize hotspots only (offline pass)
    total_hotspots = sum(1 for fz in files if fz.get("hotspots"))
    hotspot_list = [f"- {f['path']}: {', '.join(f['hotspots'])}" for f in files if f.get("hotspots")]
    notes = [
        "# AI Notes",
        "",
        f"- Files indexed: {len(files)}",
        f"- Languages: {', '.join(index['languages']) or 'n/a'}",
        f"- Hotspot files: {total_hotspots}",
        "",
        "## Hotspots",
        *(hotspot_list or ["(none found in offline pass)"]),
        "",
        "## Next",
        "- Fill resilience.possibility_matrix entries for hypotheses & checks.",
        "- Tag roles for core/config/test/doc.",
        "- Wire imports/exports extraction per language.",
    ]
    with open(out_notes, 'w', encoding='utf-8') as f:
        f.write("\n".join(notes))

    print(f"Wrote {out_index}")
    print(f"Wrote {out_notes}")

if __name__ == "__main__":
    main()
