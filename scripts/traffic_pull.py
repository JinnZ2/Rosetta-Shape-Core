#!/usr/bin/env python3
"""
traffic_pull.py -- pull GitHub traffic for every repo of one owner and keep the history.
Stdlib only. CC0. Co-authored.

GitHub keeps traffic for 14 days only. This script reads, per repo:
  /traffic/clones   /traffic/views   (daily counts, 14 days)
  /traffic/popular/referrers   /traffic/popular/paths   (14-day top 10, no daily breakdown)
and appends to traffic/ without deleting any history.

USAGE
  TRAFFIC_TOKEN=... python3 scripts/traffic_pull.py [--owner JinnZ2] [--out traffic]
  python3 scripts/traffic_pull.py --selftest            no network; planted data

Merge rule (history_clones.csv, history_views.csv): key = (repo, date). A new key is appended.
An existing key is never deleted; its count/uniques are raised only if the new fetch is larger
(today's row is partial when fetched, and fills in on a later run). Rows are written sorted.
Referrers and paths have no dates in the API, so each run appends a snapshot dated by fetch day;
the same (fetch date, repo, name) is not written twice.
"""
import csv
import datetime as dt
import json
import os
import sys
import urllib.error
import urllib.request

API = "https://api.github.com"
DAILY_COLS = ["date", "repo", "count", "uniques"]
TOP_COLS = ["fetched", "repo", "name", "count", "uniques"]


# ---------------------------------------------------------------- network
def _get(path, token):
    req = urllib.request.Request(API + path, headers={
        "Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28", "User-Agent": "traffic-pull"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, json.loads(r.read().decode() or "null"), r.headers.get("Link", "")
    except urllib.error.HTTPError as e:
        return e.code, None, ""


def list_repos(owner, token):
    """Owner's repos, public and private, via /user/repos (token must belong to the owner);
    falls back to /users/<owner>/repos (public only) if that is refused."""
    out, page = [], 1
    while True:
        st, data, _ = _get(f"/user/repos?affiliation=owner&per_page=100&page={page}", token)
        if st != 200:
            break
        out += [r["name"] for r in data if r["owner"]["login"].lower() == owner.lower()]
        if len(data) < 100:
            return sorted(set(out)), "user/repos"
        page += 1
    out, page = [], 1
    while True:
        st, data, _ = _get(f"/users/{owner}/repos?type=owner&per_page=100&page={page}", token)
        if st != 200:
            raise SystemExit(f"cannot list repos for {owner}: HTTP {st}")
        out += [r["name"] for r in data]
        if len(data) < 100:
            return sorted(set(out)), "users/<owner>/repos (public only)"
        page += 1


def fetch(owner, repo, token):
    rec = {"repo": repo, "errors": {}}
    for key, path in (("clones", "clones"), ("views", "views"),
                      ("referrers", "popular/referrers"), ("paths", "popular/paths")):
        st, data, _ = _get(f"/repos/{owner}/{repo}/traffic/{path}", token)
        if st == 200:
            rec[key] = data
        else:
            rec["errors"][key] = st
    return rec


# ---------------------------------------------------------------- history
def read_csv(path):
    if not os.path.exists(path):
        return []
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_csv(path, cols, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


def merge_daily(old, new):
    """old/new: rows with date, repo, count, uniques. Keys never deleted; values only raised."""
    by = {(r["repo"], r["date"]): {k: str(r[k]) for k in DAILY_COLS} for r in old}
    for r in new:
        k = (r["repo"], r["date"])
        r = {c: str(r[c]) for c in DAILY_COLS}
        if k not in by:
            by[k] = r
        else:
            cur = by[k]
            for c in ("count", "uniques"):
                if int(r[c]) > int(cur[c]):
                    cur[c] = r[c]
    return [by[k] for k in sorted(by, key=lambda k: (k[1], k[0]))]


def merge_top(old, new):
    seen = {(r["fetched"], r["repo"], r["name"]) for r in old}
    rows = list(old) + [r for r in new if (r["fetched"], r["repo"], r["name"]) not in seen]
    return sorted(rows, key=lambda r: (r["fetched"], r["repo"], -int(r["uniques"]), r["name"]))


def daily_rows(recs, key):
    out = []
    for rec in recs:
        for d in (rec.get(key) or {}).get(key, []):
            out.append({"date": d["timestamp"][:10], "repo": rec["repo"], "count": d["count"], "uniques": d["uniques"]})
    return out


def top_rows(recs, key, field, today):
    return [{"fetched": today, "repo": rec["repo"], "name": x[field], "count": x["count"], "uniques": x["uniques"]}
            for rec in recs for x in (rec.get(key) or [])]


# ---------------------------------------------------------------- latest.md
def latest_md(recs, owner, today, source):
    def tot(rec, k):
        d = rec.get(k) or {}
        return int(d.get("count", 0)), int(d.get("uniques", 0))
    rows = []
    for rec in recs:
        c, v = tot(rec, "clones"), tot(rec, "views")
        top = lambda k, f: ", ".join(f"{x[f]} ({x['uniques']})" for x in sorted(
            rec.get(k) or [], key=lambda x: -int(x["uniques"]))[:3]) or "-"
        rows.append(dict(repo=rec["repo"], c=c, v=v, ref=top("referrers", "referrer"), path=top("paths", "path"),
                         bot="BOT?" if c[0] > 0 and v[0] == 0 else "", err=rec["errors"]))
    rows.sort(key=lambda r: (-r["c"][1], -r["c"][0], r["repo"].lower()))
    L = [f"# Traffic, {owner}: last 14 days (fetched {today})", "",
         "Generated by `scripts/traffic_pull.py`; do not edit by hand. History: `history_clones.csv`, "
         "`history_views.csv`, `history_referrers.csv`, `history_paths.csv`.", "",
         f"Repos listed from `{source}`. Sorted by unique cloners, then total clones (numeric). "
         "**BOT?** = clones > 0 and views = 0 (crawler or CI pattern, not proven).", "",
         "| repo | clones (total/unique) | views (total/unique) | top referrers (unique) | top paths (unique) | flag |",
         "|---|---|---|---|---|---|"]
    for r in rows:
        if r["err"]:
            continue
        L.append(f"| {r['repo']} | {r['c'][0]}/{r['c'][1]} | {r['v'][0]}/{r['v'][1]} | {r['ref']} | {r['path']} | {r['bot']} |")
    bots = [r["repo"] for r in rows if r["bot"] and not r["err"]]
    L += ["", f"Repos with clones > 0 and views = 0: {len(bots)}" + (": " + ", ".join(bots) if bots else "")]
    errs = [r for r in rows if r["err"]]
    if errs:
        L += ["", "## Not read (HTTP status per endpoint)", ""]
        L += [f"- {r['repo']}: " + ", ".join(f"{k} {s}" for k, s in sorted(r["err"].items())) for r in errs]
        L += ["", "403 on every repo usually means the token lacks the traffic permission (see traffic/README.md)."]
    return "\n".join(L) + "\n"


def write_all(recs, out, owner, today, source):
    os.makedirs(out, exist_ok=True)
    for key in ("clones", "views"):
        p = os.path.join(out, f"history_{key}.csv")
        write_csv(p, DAILY_COLS, merge_daily(read_csv(p), daily_rows(recs, key)))
    for key, field in (("referrers", "referrer"), ("paths", "path")):
        p = os.path.join(out, f"history_{key}.csv")
        write_csv(p, TOP_COLS, merge_top(read_csv(p), top_rows(recs, key, field, today)))
    open(os.path.join(out, "latest.md"), "w", encoding="utf-8").write(latest_md(recs, owner, today, source))


# ---------------------------------------------------------------- selftest
def selftest():
    import tempfile
    checks = []
    day = lambda d, c, u: {"timestamp": f"2026-11-{d:02d}T00:00:00Z", "count": c, "uniques": u}
    recs = [
        {"repo": "a", "errors": {}, "clones": {"count": 5, "uniques": 2, "clones": [day(1, 3, 1), day(2, 2, 2)]},
         "views": {"count": 0, "uniques": 0, "views": []}, "referrers": [], "paths": []},
        {"repo": "b", "errors": {}, "clones": {"count": 30, "uniques": 10, "clones": [day(2, 30, 10)]},
         "views": {"count": 9, "uniques": 4, "views": [day(2, 9, 4)]},
         "referrers": [{"referrer": "github.com", "count": 5, "uniques": 3}, {"referrer": "google", "count": 2, "uniques": 1}],
         "paths": [{"path": "/JinnZ2/b", "title": "b", "count": 9, "uniques": 4}]},
        {"repo": "c", "errors": {}, "clones": {"count": 4, "uniques": 9, "clones": []},
         "views": {"count": 1, "uniques": 1, "views": []}, "referrers": [], "paths": []},
        {"repo": "d", "errors": {"clones": 403, "views": 403}},
    ]
    tmp = tempfile.mkdtemp()
    write_all(recs, tmp, "X", "2026-11-02", "planted")
    cl = read_csv(os.path.join(tmp, "history_clones.csv"))
    checks.append(("daily clone rows written", len(cl) == 3))
    md = open(os.path.join(tmp, "latest.md"), encoding="utf-8").read()
    order = [ln.split("|")[1].strip() for ln in md.splitlines() if ln.startswith("| ") and not ln.startswith("| repo")]
    checks.append(("sorted numerically by unique cloners (10, 9, 2)", order == ["b", "c", "a"]))
    checks.append(("BOT? flag on clones > 0, views = 0", "| a | 5/2 | 0/0 | - | - | BOT? |" in md))
    checks.append(("no flag where views exist", "| b | 30/10 | 9/4 |" in md and "BOT?" not in md.split("| b |")[1].split("\n")[0]))
    checks.append(("top referrers listed by uniques", "github.com (3), google (1)" in md))
    checks.append(("refused repo listed with status, not as zero", "- d: clones 403, views 403" in md and "| d |" not in md))
    # second run: partial day fills in, new day appended, nothing deleted
    recs[0]["clones"]["clones"] = [day(2, 7, 3), day(3, 1, 1)]
    write_all(recs, tmp, "X", "2026-11-09", "planted")
    cl = {(r["repo"], r["date"]): (r["count"], r["uniques"]) for r in read_csv(os.path.join(tmp, "history_clones.csv"))}
    checks.append(("old key kept after it left the 14-day window", cl[("a", "2026-11-01")] == ("3", "1")))
    checks.append(("partial day raised to the larger fetch", cl[("a", "2026-11-02")] == ("7", "3")))
    checks.append(("new day appended", ("a", "2026-11-03") in cl and len(cl) == 4))
    merged = merge_daily([{"date": "2026-11-02", "repo": "a", "count": "7", "uniques": "3"}],
                         [{"date": "2026-11-02", "repo": "a", "count": 5, "uniques": 2}])
    checks.append(("a smaller later fetch never lowers a row", merged[0]["count"] == "7" and merged[0]["uniques"] == "3"))
    ref = read_csv(os.path.join(tmp, "history_referrers.csv"))
    checks.append(("referrer snapshots kept per fetch date", sorted({r["fetched"] for r in ref}) == ["2026-11-02", "2026-11-09"]))
    write_all(recs, tmp, "X", "2026-11-09", "planted")
    checks.append(("same-day rerun adds no duplicate snapshot rows",
                   len(read_csv(os.path.join(tmp, "history_referrers.csv"))) == len(ref)))
    bad = [n for n, ok in checks if not ok]
    for n in bad:
        print("  FAIL:", n)
    print("traffic_pull selftest %d/%d" % (len(checks) - len(bad), len(checks)))
    return not bad


def main(argv):
    if "--selftest" in argv:
        sys.exit(0 if selftest() else 1)
    owner = argv[argv.index("--owner") + 1] if "--owner" in argv else os.environ.get("TRAFFIC_OWNER", "JinnZ2")
    out = argv[argv.index("--out") + 1] if "--out" in argv else "traffic"
    token = os.environ.get("TRAFFIC_TOKEN")
    if not token:
        raise SystemExit("TRAFFIC_TOKEN is not set (see traffic/README.md)")
    repos, source = list_repos(owner, token)
    recs = [fetch(owner, r, token) for r in repos]
    today = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d")
    write_all(recs, out, owner, today, source)
    n_err = sum(1 for r in recs if r["errors"])
    print(f"{len(repos)} repos, {len(repos) - n_err} read, {n_err} with errors; wrote {out}/")


if __name__ == "__main__":
    main(sys.argv[1:])
