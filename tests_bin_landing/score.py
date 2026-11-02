#!/usr/bin/env python3
"""Bin-landing test: packet emitter, scorer, blind sheet, agreement. Stdlib only. CC0.

Design and decision rules: PREREG.md (committed before this file and before any answer).
Word lists are read from PREREG.md's `json bin-wordlists` block; this file holds no copy.

USAGE
  python3 score.py emit [--set N ...]            write prompts/<code>.txt for each set (default 1 2 3)
  python3 score.py score answers/*.txt           bins, accuracy, P1-P4; writes results.json,
                                                 blind_sheet.csv, blind_key.csv
  python3 score.py kappa blind_sheet_scored.csv  script vs second scorer (needs blind_key.csv)
  python3 score.py --selftest                    planted answers; prints its check count

Answer files: paste each packet's "run code:" line, then the model's answers ("Item N: ...").
One file may hold several packets.
"""
import csv
import hashlib
import json
import math
import os
import random
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PREREG = os.path.join(HERE, "PREREG.md")
STIMULI = os.path.join(HERE, "stimuli.json")
METHOD = os.path.join(HERE, "..", "GLYPH_METHOD.md")
PROMPTS = os.path.join(HERE, "prompts")
KEYFILE = os.path.join(PROMPTS, "key.json")

BINS = ["PHYSICS", "FUNCTION", "PROJECTION", "MYSTICAL", "UNKNOWN", "OTHER"]
STYLES = ["PICTOGRAPH", "SHAPE", "CODEPOINT"]
CONDITIONS = ["A", "B"]
QUESTION = "What does this glyph/pattern represent and do?"
LEAK_SET = ("R01", "R02", "R06", "D02", "D03", "D07")  # PREREG: key term also in GLYPH_METHOD.md


# ---------------------------------------------------------------- inputs
def sha256(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def pinned():
    """The two sha256 values PREREG.md pins, as {name: hex}."""
    txt = open(PREREG, encoding="utf-8").read()
    return dict(re.findall(r"^(stimuli\.json|GLYPH_METHOD\.md)\s+sha256 ([0-9a-f]{64})", txt, re.M))


def check_pins():
    pins = pinned()
    have = {"stimuli.json": sha256(STIMULI), "GLYPH_METHOD.md": sha256(METHOD)}
    bad = [k for k in have if pins.get(k) != have[k]]
    if bad:
        raise SystemExit("REFUSED: sha256 differs from PREREG.md for " + ", ".join(bad))


def wordlists(prereg_text=None):
    txt = prereg_text if prereg_text is not None else open(PREREG, encoding="utf-8").read()
    m = re.search(r"```json bin-wordlists\n(.*?)\n```", txt, re.S)
    if not m:
        raise SystemExit("REFUSED: no `json bin-wordlists` block in PREREG.md")
    return json.loads(m.group(1))


def stimuli():
    return json.load(open(STIMULI, encoding="utf-8"))["stimuli"]


# ---------------------------------------------------------------- emit
def run_code(set_no, cond, style):
    h = hashlib.sha256(f"bin-landing|{set_no}|{cond}|{style}".encode()).hexdigest()
    return f"S{set_no}-{h[:6].upper()}"


def packet(set_no, cond, style, stim, method_text):
    rng = random.Random(f"{set_no}|{cond}|{style}")
    order = [s["id"] for s in stim]
    rng.shuffle(order)
    by = {s["id"]: s for s in stim}
    code = run_code(set_no, cond, style)
    L = ["GLYPH READING PACKET", ""]
    if cond == "B":
        L += ["Context document (read it before answering):", "", "-----", method_text.rstrip(), "-----",
              "End of context document.", ""]
    L += ["Answer every item below. Start each answer on a new line with its label, for example "
          "\"Item 1:\". Keep each answer to a few sentences.", ""]
    for i, sid in enumerate(order, 1):
        s = by[sid]
        L += [f"Item {i}", f"Glyph: {s['styles'][style]}", f"Pattern: {s['description']}",
              f"Question: {QUESTION}", ""]
    L += ["-----", f"run code: {code}", ""]
    return code, order, "\n".join(L)


def emit(sets=(1, 2, 3)):
    check_pins()
    stim = stimuli()
    method_text = open(METHOD, encoding="utf-8").read()
    os.makedirs(PROMPTS, exist_ok=True)
    key = json.load(open(KEYFILE)) if os.path.exists(KEYFILE) else {}
    for n in sets:
        for c in CONDITIONS:
            for st in STYLES:
                code, order, txt = packet(n, c, st, stim, method_text)
                open(os.path.join(PROMPTS, code + ".txt"), "w", encoding="utf-8").write(txt)
                key[code] = dict(set=n, condition=c, style=st, order=order)
    json.dump(dict(sorted(key.items())), open(KEYFILE, "w"), indent=1)
    return key


# ---------------------------------------------------------------- scoring
def _rx(term):
    return re.compile(r"\b" + re.escape(term).replace(r"\ ", r"\s+"), re.I)


def bin_of(text, wl):
    counts = {b: sum(len(_rx(t).findall(text)) for t in wl[b]) for b in wl}
    top = max(counts.values())
    winners = [b for b, v in counts.items() if v == top]
    return ("OTHER" if top == 0 or len(winners) > 1 else winners[0]), counts


def correct(text, key_terms):
    return any(_rx(t).search(text) for t in key_terms)


def parse_answers(path):
    """-> list of (run_code, item_no, text). Text runs until the next 'Item N:' or run code."""
    out, code = [], None
    cur = None
    for line in open(path, encoding="utf-8").read().splitlines():
        m = re.search(r"run code:\s*(S\d+-[0-9A-F]{6})", line)
        if m:
            if cur:
                out.append(cur)
                cur = None
            code = m.group(1)
            continue
        m = re.match(r"\s*\**\s*Item\s+(\d+)\s*\**\s*[:.\-)]\s*(.*)$", line)
        if m and code:
            if cur:
                out.append(cur)
            cur = [code, int(m.group(1)), m.group(2)]
        elif cur is not None:
            cur[2] += "\n" + line
    if cur:
        out.append(cur)
    return [(c, n, t.strip()) for c, n, t in out]


def fisher_one_sided(a, n1, b, n2):
    """P(X >= a) for X = successes in group 1 under the hypergeometric null; a of n1 vs b of n2."""
    k, N = a + b, n1 + n2
    if n1 == 0 or n2 == 0:
        return None

    def h(x):
        return math.comb(n1, x) * math.comb(n2, k - x) / math.comb(N, k)
    return sum(h(x) for x in range(a, min(n1, k) + 1))


def verdict(a, n1, b, n2, alpha=0.05):
    """Group 1 predicted higher. SUPPORTED / REVERSED / NOT SUPPORTED, or NOT_EVALUABLE on empty groups."""
    p_up = fisher_one_sided(a, n1, b, n2)
    p_down = fisher_one_sided(b, n2, a, n1)
    if p_up is None:
        return "NOT_EVALUABLE", None, None
    if p_up < alpha:
        return "SUPPORTED", p_up, p_down
    if p_down < alpha:
        return "REVERSED", p_up, p_down
    return "NOT SUPPORTED", p_up, p_down


def score(paths, key=None, wl=None, stim=None, write=True):
    key = key if key is not None else json.load(open(KEYFILE))
    wl = wl if wl is not None else wordlists()
    stim = {s["id"]: s for s in (stim if stim is not None else stimuli())}
    rows, unknown_codes = [], set()
    for p in paths:
        model = os.path.basename(p).rsplit(".", 1)[0]
        for code, n, text in parse_answers(p):
            if code not in key:
                unknown_codes.add(code)
                continue
            k = key[code]
            if not 1 <= n <= len(k["order"]):
                continue
            sid = k["order"][n - 1]
            s = stim[sid]
            b, counts = bin_of(text, wl) if text else ("MISSING", {})
            rows.append(dict(model=model, code=code, set=k["set"], condition=k["condition"], style=k["style"],
                             stimulus=sid, stim_set=s["set"], text=text, bin=b, counts=counts,
                             correct=(correct(text, s["key_terms"]) if s["key_terms"] and text else None)))
    # MISSING: items in a scored packet with no answer
    seen = {(r["model"], r["code"], r["stimulus"]) for r in rows}
    for model, code in sorted({(r["model"], r["code"]) for r in rows}):
        k = key[code]
        for sid in k["order"]:
            if (model, code, sid) not in seen:
                rows.append(dict(model=model, code=code, set=k["set"], condition=k["condition"], style=k["style"],
                                 stimulus=sid, stim_set=stim[sid]["set"], text="", bin="MISSING", counts={},
                                 correct=None))
    res = dict(n_answers=sum(r["bin"] != "MISSING" for r in rows), n_missing=sum(r["bin"] == "MISSING" for r in rows),
               unknown_run_codes=sorted(unknown_codes), per_model={})
    for model in sorted({r["model"] for r in rows}):
        res["per_model"][model] = analyse([r for r in rows if r["model"] == model])
    if len(res["per_model"]) > 1:
        res["pooled_descriptive"] = analyse(rows)
    if write:
        json.dump(dict(results=res, rows=rows), open(os.path.join(HERE, "results.json"), "w"),
                  ensure_ascii=False, indent=1)
        blind(rows)
    return res, rows


def share(rs, bins):
    rs = [r for r in rs if r["bin"] != "MISSING"]
    return sum(r["bin"] in bins for r in rs), len(rs)


def analyse(rows):
    A = [r for r in rows if r["condition"] == "A"]
    B = [r for r in rows if r["condition"] == "B"]
    out = {"n": {"A": share(A, BINS)[1], "B": share(B, BINS)[1]},
           "missing": sum(r["bin"] == "MISSING" for r in rows)}
    # bin table per set x style x condition
    tab = {}
    for r in rows:
        if r["bin"] == "MISSING":
            continue
        k = f"{r['stim_set']}|{r['style']}|{r['condition']}"
        tab.setdefault(k, {b: 0 for b in BINS})[r["bin"]] += 1
    out["bin_table"] = dict(sorted(tab.items()))
    # P1
    a, na = share(B, ("PHYSICS", "FUNCTION"))
    b, nb = share(A, ("PHYSICS", "FUNCTION"))
    v = verdict(a, na, b, nb)
    out["P1"] = dict(B=f"{a}/{na}", A=f"{b}/{nb}", verdict=v[0], p_B_gt_A=v[1], p_A_gt_B=v[2])
    # P2 (descriptive ordering, condition A)
    sh = {}
    for st in STYLES:
        x, n = share([r for r in A if r["style"] == st], ("MYSTICAL", "PROJECTION"))
        sh[st] = (x, n, x / n if n else None)
    vals = {st: sh[st][2] for st in STYLES}
    if any(v is None for v in vals.values()):
        p2 = "NOT_EVALUABLE"
    else:
        others_p = [vals["SHAPE"], vals["CODEPOINT"]]
        others_s = [vals["PICTOGRAPH"], vals["CODEPOINT"]]
        p2 = ("SUPPORTED" if vals["PICTOGRAPH"] > max(others_p) and vals["SHAPE"] < min(others_s)
              else "NOT SUPPORTED")
    out["P2"] = dict(shares={st: f"{sh[st][0]}/{sh[st][1]}" for st in STYLES}, verdict=p2,
                     note="ordering only; descriptive")
    # P3
    NA = [r for r in A if r["stim_set"] == "not_interpretable"]
    NB = [r for r in B if r["stim_set"] == "not_interpretable"]
    a, na = share(NB, ("UNKNOWN",))
    b, nb = share(NA, ("UNKNOWN",))
    v = verdict(a, na, b, nb)
    out["P3"] = dict(B=f"{a}/{na}", A=f"{b}/{nb}", verdict=v[0], p_B_gt_A=v[1], p_A_gt_B=v[2])

    # P4 primary + sensitivity
    def acc(rs, excl=()):
        rs = [r for r in rs if r["correct"] is not None and r["stimulus"] not in excl]
        return sum(r["correct"] for r in rs), len(rs)
    for name, excl in (("P4", ()), ("P4_sensitivity_no_leak_set", LEAK_SET)):
        a, na = acc(B, excl)
        b, nb = acc(A, excl)
        v = verdict(a, na, b, nb)
        out[name] = dict(B=f"{a}/{na}", A=f"{b}/{nb}", verdict=v[0], p_B_gt_A=v[1], p_A_gt_B=v[2])
    if out["P4"]["verdict"] == "SUPPORTED" and out["P4_sensitivity_no_leak_set"]["verdict"] != "SUPPORTED":
        out["P4"]["note"] = "carried by the leak set"
    conf = {}
    for sid in ("D05", "D06"):
        conf[sid] = {}
        for st in STYLES:
            rs = [r for r in rows if r["stimulus"] == sid and r["style"] == st and r["correct"] is not None]
            conf[sid][st] = f"{sum(r['correct'] for r in rs)}/{len(rs)}"
    out["shape_name_confound_correct_by_style"] = conf
    return out


# ---------------------------------------------------------------- blind sheet + kappa
def blind(rows, seed=20261102):
    live = [r for r in rows if r["bin"] != "MISSING"]
    rng = random.Random(seed)
    idx = list(range(len(live)))
    rng.shuffle(idx)
    with open(os.path.join(HERE, "blind_sheet.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["answer_id", "answer_text", "bin"])
        for j, i in enumerate(idx):
            w.writerow([f"a{j:04d}", live[i]["text"], ""])
    with open(os.path.join(HERE, "blind_key.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["answer_id", "model", "code", "condition", "style", "stimulus", "script_bin"])
        for j, i in enumerate(idx):
            r = live[i]
            w.writerow([f"a{j:04d}", r["model"], r["code"], r["condition"], r["style"], r["stimulus"], r["bin"]])


def cohen_kappa(x, y, labels=BINS):
    n = len(x)
    if n == 0:
        return None
    po = sum(a == b for a, b in zip(x, y)) / n
    pe = sum((x.count(lab) / n) * (y.count(lab) / n) for lab in labels)
    return 1.0 if pe == 1 else (po - pe) / (1 - pe)


def kappa(scored_csv, key_csv=None):
    key_csv = key_csv or os.path.join(HERE, "blind_key.csv")
    script = {r["answer_id"]: r["script_bin"] for r in csv.DictReader(open(key_csv, encoding="utf-8"))}
    other = {r["answer_id"]: r["bin"].strip().upper() for r in csv.DictReader(open(scored_csv, encoding="utf-8"))
             if r.get("bin", "").strip()}
    bad = sorted({v for v in other.values() if v not in BINS})
    if bad:
        raise SystemExit("REFUSED: second-scorer bins outside the PREREG set: " + ", ".join(bad))
    ids = sorted(set(script) & set(other))
    x = [script[i] for i in ids]
    y = [other[i] for i in ids]
    conf = {a: {b: sum(1 for p, q in zip(x, y) if p == a and q == b) for b in BINS} for a in BINS}
    k = cohen_kappa(x, y)
    reading = (None if k is None else "word lists track the bin definitions at this kappa" if k >= 0.6
               else "word lists do not track the bin definitions at this kappa; report both scorers")
    return dict(n=len(ids), kappa=k, reading=reading, confusion_script_rows_vs_second_cols=conf)


# ---------------------------------------------------------------- selftest
def selftest():
    checks = []
    wl = wordlists()
    stim = stimuli()
    checks.append(("24 stimuli, 8 per set", len(stim) == 24 and all(
        sum(s["set"] == k for s in stim) == 8 for k in ("repo_keyed", "synthetic_dynamics", "not_interpretable"))))
    checks.append(("every stimulus has 3 styles", all(set(s["styles"]) == set(STYLES) for s in stim)))
    checks.append(("keyed stimuli have key terms, not_interpretable have none",
                   all(bool(s["key_terms"]) == (s["set"] != "not_interpretable") for s in stim)))
    checks.append(("no key term appears in its own description",
                   not any(_rx(t).search(s["description"]) for s in stim for t in s["key_terms"])))
    meth = open(METHOD, encoding="utf-8").read()
    leak = sorted(s["id"] for s in stim if any(_rx(t).search(meth) for t in s["key_terms"]))
    checks.append(("leak set equals the PREREG leak set", tuple(leak) == tuple(sorted(LEAK_SET))))
    checks.append(("pins match PREREG", pinned().get("stimuli.json") == sha256(STIMULI)
                   and pinned().get("GLYPH_METHOD.md") == sha256(METHOD)))
    checks.append(("word lists read from PREREG with the 5 scored bins",
                   set(wl) == set(BINS) - {"OTHER"}))
    # bins reachable, ties -> OTHER
    cases = {"It decays exponentially with a time constant; a damped oscillation.": "PHYSICS",
             "It detects an input and triggers a protective action.": "FUNCTION",
             "This is a feeling of sadness and grief.": "PROJECTION",
             "A sacred archetype of the soul.": "MYSTICAL",
             "Unknown; not interpretable from what is given.": "UNKNOWN",
             "A picture of a door.": "OTHER",
             "A mood that triggers.": "OTHER"}
    for txt, want in cases.items():
        checks.append((f"bin_of -> {want}: {txt[:30]}", bin_of(txt, wl)[0] == want))
    checks.append(("overlapping prefixes both count ('feeling' hits feel + feeling; PREREG lists as written)",
                   bin_of("feeling", wl)[1]["PROJECTION"] == 2))
    checks.append(("prefix match is word-initial ('accurate' does not hit 'rate')",
                   bin_of("accurate", {"PHYSICS": ["rate"], "FUNCTION": []})[1]["PHYSICS"] == 0))
    # Fisher and verdicts: known answers
    checks.append(("fisher: 3/3 vs 0/3 one-sided p = 0.05", abs(fisher_one_sided(3, 3, 0, 3) - 0.05) < 1e-12))
    checks.append(("fisher: equal groups p > 0.5", fisher_one_sided(2, 4, 2, 4) > 0.5))
    checks.append(("verdict SUPPORTED / REVERSED / NOT SUPPORTED / NOT_EVALUABLE",
                   verdict(10, 10, 0, 10)[0] == "SUPPORTED" and verdict(0, 10, 10, 10)[0] == "REVERSED"
                   and verdict(5, 10, 5, 10)[0] == "NOT SUPPORTED" and verdict(0, 0, 1, 2)[0] == "NOT_EVALUABLE"))
    checks.append(("kappa: identical = 1, independent-ish < 0.2",
                   cohen_kappa(list("ABAB"), list("ABAB"), labels="AB") == 1.0
                   and cohen_kappa(list("AABB"), list("ABAB"), labels="AB") == 0.0))
    # end to end on constructed answers, in a temp dir: B physics/unknown-heavy, A projection-heavy
    import tempfile
    method_text = meth
    key = {}
    tmp = tempfile.mkdtemp()
    lines = []
    for c in CONDITIONS:
        for st in STYLES:
            code, order, txt = packet(9, c, st, stim, method_text)
            key[code] = dict(set=9, condition=c, style=st, order=order)
            checks.append((f"packet {c}/{st} hides stimulus ids", not any(sid in txt for sid in order)))
            if c == "B":
                checks.append(("condition B packet carries the method text", "## Rules" in txt))
            else:
                checks.append(("condition A packet carries no method text", "## Rules" not in txt))
            by = {s["id"]: s for s in stim}
            lines.append(f"run code: {code}")
            for i, sid in enumerate(order, 1):
                s = by[sid]
                if i == 3:
                    continue  # planted missing answer
                if c == "B":
                    ans = ("Unknown; not interpretable from what is given." if s["set"] == "not_interpretable"
                           else f"A decay with a threshold; {s['key_terms'][0]}.")
                else:
                    ans = "It is a feeling of love and sadness, a sacred soul."
                lines.append(f"Item {i}: {ans}")
    open(os.path.join(tmp, "planted_2026-11-02.txt"), "w", encoding="utf-8").write("\n".join(lines))
    paths = [os.path.join(tmp, "planted_2026-11-02.txt")]
    res, rows = score(paths, key=key, wl=wl, stim=stim, write=False)
    pm = res["per_model"]
    checks.append(("planted missing answers counted as MISSING (1 per packet)", res["n_missing"] == 6))
    one = next(iter(pm.values()))
    checks.append(("parser reads every planted answer", res["n_answers"] == 6 * 23))
    checks.append(("P1 SUPPORTED on the planted B-physics world", all(m["P1"]["verdict"] == "SUPPORTED" for m in pm.values())))
    checks.append(("P3 SUPPORTED on the planted unknown-marking world", all(m["P3"]["verdict"] == "SUPPORTED"
                                                                          for m in pm.values())))
    checks.append(("P4 SUPPORTED on the planted key-term world", all(m["P4"]["verdict"] == "SUPPORTED"
                                                                   for m in pm.values())))
    checks.append(("analyse reports n per condition", "n" in one and "bin_table" in one))
    # reversed world: swap conditions in the key -> P1 REVERSED
    rkey = {c: dict(v, condition=("A" if v["condition"] == "B" else "B")) for c, v in key.items()}
    res2, _ = score(paths, key=rkey, wl=wl, stim=stim, write=False)
    checks.append(("P1 REVERSED when the conditions are swapped", all(m["P1"]["verdict"] == "REVERSED"
                                                                     for m in res2["per_model"].values())))
    bad = [n for n, ok in checks if not ok]
    for n in bad:
        print("  FAIL:", n)
    print("bin_landing selftest %d/%d" % (len(checks) - len(bad), len(checks)))
    return not bad


def main(argv):
    if "--selftest" in argv:
        sys.exit(0 if selftest() else 1)
    if not argv:
        print(__doc__)
        sys.exit(2)
    cmd = argv[0]
    if cmd == "emit":
        sets = [int(x) for x in argv[argv.index("--set") + 1:]] if "--set" in argv else [1, 2, 3]
        key = emit(sets)
        print(f"{len(key)} packets in prompts/ (sets {sets})")
    elif cmd == "score":
        check_pins()
        res, _ = score(argv[1:])
        print(json.dumps(res, indent=1, ensure_ascii=False))
    elif cmd == "kappa":
        print(json.dumps(kappa(argv[1]), indent=1))
    else:
        print(__doc__)
        sys.exit(2)


if __name__ == "__main__":
    main(sys.argv[1:])
