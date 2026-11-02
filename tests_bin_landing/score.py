#!/usr/bin/env python3
"""Bin-landing test: packet emitter, scorer, blind sheet, agreement. Stdlib only. CC0.

Design and decision rules: PREREG.md (committed first, b34b709) as amended by
PREREG_AMENDMENT_1.md (committed alone, eec815a, before any answer). Where they conflict the
amendment governs. Word lists come from PREREG.md's `json bin-wordlists` block, and the E and C
contexts from the amendment's `context-E` / `context-C` blocks; this file holds no copy of either.

Conditions: A bare | E method in plain English | C glyph moves. Old condition B is retired: its
packets are kept in prompts/retired/ and are never scored.

USAGE
  python3 score.py emit [--set N ...]            write prompts/<code>.txt (A, E, C) and prompts/retired/
                                                 (B) for each set (default 1 2 3), plus PILOT.txt
  python3 score.py score answers/*.txt           bins, accuracy, features, P1-P5; writes results.json,
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
AMEND1 = os.path.join(HERE, "PREREG_AMENDMENT_1.md")
AMEND2 = os.path.join(HERE, "PREREG_AMENDMENT_2.md")
STIMULI = os.path.join(HERE, "stimuli.json")
METHOD = os.path.join(HERE, "..", "GLYPH_METHOD.md")
PROMPTS = os.path.join(HERE, "prompts")
RETIRED = os.path.join(PROMPTS, "retired")
KEYFILE = os.path.join(PROMPTS, "key.json")
PILOT = os.path.join(PROMPTS, "PILOT.txt")

# Pinned here because the amendment cannot contain its own hash. Changing the amendment
# changes this value and turns the selftest red; a later change is amendment 2, in a new file.
AMEND1_SHA256 = "cab4437a347d134ef77d01b94d68b8a2dded2d6326c6a90540dff0858d55e2ed"
AMEND2_SHA256 = "f1feb37b057d37c813042e3fe6fb9bd10e702fb862469e77689773e655bd2f34"   # answer-file layout

BINS = ["PHYSICS", "FUNCTION", "PROJECTION", "MYSTICAL", "UNKNOWN", "OTHER"]
STYLES = ["PICTOGRAPH", "SHAPE", "CODEPOINT"]
CONDITIONS = ["A", "E", "C"]          # live (amendment 1)
RETIRED_CONDITIONS = ["B"]            # kept for provenance, never scored
QUESTION = "What does this glyph/pattern represent and do?"
LEAK_SET_B = ("R01", "R02", "R06", "D02", "D03", "D07")   # PREREG: retired condition B only
LEAK_SET = {"E": (), "C": ()}                             # amendment 1: recomputed, empty


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
    if sha256(AMEND1) != AMEND1_SHA256:
        bad.append("PREREG_AMENDMENT_1.md")
    if sha256(AMEND2) != AMEND2_SHA256:
        bad.append("PREREG_AMENDMENT_2.md")
    if bad:
        raise SystemExit("REFUSED: sha256 differs from the pre-registered value for " + ", ".join(bad))


def wordlists(prereg_text=None):
    txt = prereg_text if prereg_text is not None else open(PREREG, encoding="utf-8").read()
    m = re.search(r"```json bin-wordlists\n(.*?)\n```", txt, re.S)
    if not m:
        raise SystemExit("REFUSED: no `json bin-wordlists` block in PREREG.md")
    return json.loads(m.group(1))


def contexts():
    """{'B': GLYPH_METHOD.md text (retired), 'E': ..., 'C': ...} from the pinned files."""
    txt = open(AMEND1, encoding="utf-8").read()
    out = {"B": open(METHOD, encoding="utf-8").read().rstrip()}
    for c in ("E", "C"):
        m = re.search(r"```text context-%s\n(.*?)\n```" % c, txt, re.S)
        if not m:
            raise SystemExit(f"REFUSED: no `context-{c}` block in PREREG_AMENDMENT_1.md")
        out[c] = m.group(1)
    return out


def stimuli():
    return json.load(open(STIMULI, encoding="utf-8"))["stimuli"]


# ---------------------------------------------------------------- emit
def run_code(set_no, cond, style):
    h = hashlib.sha256(f"bin-landing|{set_no}|{cond}|{style}".encode()).hexdigest()
    return f"S{set_no}-{h[:6].upper()}"


def packet(set_no, cond, style, stim, ctx):
    rng = random.Random(f"{set_no}|{cond}|{style}")
    order = [s["id"] for s in stim]
    rng.shuffle(order)
    by = {s["id"]: s for s in stim}
    code = run_code(set_no, cond, style)
    L = ["GLYPH READING PACKET", ""]
    if cond != "A":
        L += ["Context document (read it before answering):", "", "-----", ctx[cond].rstrip(), "-----",
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
    stim, ctx = stimuli(), contexts()
    os.makedirs(RETIRED, exist_ok=True)
    key = json.load(open(KEYFILE)) if os.path.exists(KEYFILE) else {}
    pilot = []
    for n in sets:
        for c in CONDITIONS + RETIRED_CONDITIONS:
            for st in STYLES:
                code, order, txt = packet(n, c, st, stim, ctx)
                retired = c in RETIRED_CONDITIONS
                path = os.path.join(RETIRED if retired else PROMPTS, code + ".txt")
                stale = os.path.join(PROMPTS, code + ".txt")
                if retired and os.path.exists(stale):
                    os.remove(stale)          # old B packet moved under retired/
                open(path, "w", encoding="utf-8").write(txt)
                key[code] = dict(set=n, condition=c, style=st, order=order, **({"retired": True} if retired else {}))
                if st == "SHAPE" and not retired:
                    pilot.append(f"{code}  set {n}  condition {c}  style SHAPE")
    json.dump(dict(sorted(key.items())), open(KEYFILE, "w"), indent=1)
    open(PILOT, "w", encoding="utf-8").write(
        "Pilot subset (PREREG_AMENDMENT_1.md): run these 9 SHAPE packets first, one fresh conversation each.\n"
        "Files are prompts/<code>.txt. Order of running is free.\n\n" + "\n".join(sorted(pilot)) + "\n")
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


# amendment 1 features
_WORD = re.compile(r"\S+")
_PLACE = re.compile(r"^\W*(where|whether|which)\W*$", re.I)
_UNK = re.compile(r"^\W*unknown\W*$", re.I)


def unknown_marked(text, wl):
    return any(_rx(t).search(text) for t in wl["UNKNOWN"])


def tagged_candidate(text):
    return bool(re.search(r"\bPROPOSED\b", text, re.I) or re.search(r"\bcandidate", text, re.I))


def break_point_named(text):
    if re.search(r"\bunknown\s*:\s*\S", text, re.I):
        return True
    toks = _WORD.findall(text)
    for i, t in enumerate(toks):
        if _UNK.match(t):
            window = toks[max(0, i - 10):i] + toks[i + 1:i + 11]
            if any(_PLACE.match(w) for w in window):
                return True
    return False


class LayoutRefused(Exception):
    pass


def parse_answers(path):
    """-> list of (run_code, item_no, text). Layout per amendment 2: HEADER (run code above its
    items) or FOOTER (run code below its items), chosen by line position only; a file with items
    both before the first and after the last run code raises LayoutRefused (AMBIGUOUS_LAYOUT)."""
    lines = open(path, encoding="utf-8").read().splitlines()
    code_rx = re.compile(r"run code:\s*(S\d+-[0-9A-F]{6})")
    item_rx = re.compile(r"\s*\**\s*Item\s+(\d+)\s*\**\s*[:.\-)]\s*(.*)$")
    # segment the file at run-code lines: segments[i] = item records between code i-1 and code i
    segments, codes, cur, seg = [], [], None, []
    for line in lines:
        m = code_rx.search(line)
        if m:
            if cur:
                seg.append(cur)
                cur = None
            segments.append(seg)
            seg = []
            codes.append(m.group(1))
            continue
        m = item_rx.match(line)
        if m:
            if cur:
                seg.append(cur)
            cur = [int(m.group(1)), m.group(2)]
        elif cur is not None:
            cur[1] += "\n" + line
    if cur:
        seg.append(cur)
    segments.append(seg)          # trailing segment, after the last run code
    if not codes:
        return []
    before, after = bool(segments[0]), bool(segments[-1])
    if before and after:
        raise LayoutRefused("AMBIGUOUS_LAYOUT")
    if before:                    # FOOTER: segment i closes at code i
        pairs = zip(codes, segments[:-1])
    else:                         # HEADER: code i opens segment i+1
        pairs = zip(codes, segments[1:])
    return [(c, n, t.strip()) for c, seg_ in pairs for n, t in seg_]


def _hyper(n1, n2, k):
    N = n1 + n2

    def h(x):
        return math.comb(n1, x) * math.comb(n2, k - x) / math.comb(N, k)
    return h, max(0, k - n2), min(n1, k)


def fisher_one_sided(a, n1, b, n2):
    """P(X >= a), X = successes in group 1 under the hypergeometric null; a of n1 vs b of n2."""
    if n1 == 0 or n2 == 0:
        return None
    h, _, hi = _hyper(n1, n2, a + b)
    return sum(h(x) for x in range(a, hi + 1))


def fisher_two_sided(a, n1, b, n2):
    """Sum of probabilities of all tables no more likely than the observed one."""
    if n1 == 0 or n2 == 0:
        return None
    h, lo, hi = _hyper(n1, n2, a + b)
    p0 = h(a)
    return min(1.0, sum(h(x) for x in range(lo, hi + 1) if h(x) <= p0 * (1 + 1e-9)))


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


def two_sided_verdict(a, n1, b, n2, names=("C", "E"), alpha=0.05):
    p = fisher_two_sided(a, n1, b, n2)
    if p is None:
        return "NOT_EVALUABLE", None
    if p >= alpha:
        return "no difference detected", p
    return (f"{names[0]} > {names[1]}" if a / n1 > b / n2 else f"{names[1]} > {names[0]}"), p


def score(paths, key=None, wl=None, stim=None, write=True):
    key = key if key is not None else json.load(open(KEYFILE))
    wl = wl if wl is not None else wordlists()
    stim = {s["id"]: s for s in (stim if stim is not None else stimuli())}
    rows, unknown_codes, retired_codes, refused_files = [], set(), set(), []
    for p in paths:
        model = os.path.basename(p).rsplit(".", 1)[0]
        try:
            parsed = parse_answers(p)
        except LayoutRefused as e:
            refused_files.append(dict(file=os.path.basename(p), reason=str(e)))
            continue
        for code, n, text in parsed:
            if code not in key:
                unknown_codes.add(code)
                continue
            k = key[code]
            if k.get("retired"):
                retired_codes.add(code)
                continue
            if not 1 <= n <= len(k["order"]):
                continue
            sid = k["order"][n - 1]
            s = stim[sid]
            b, counts = bin_of(text, wl) if text else ("MISSING", {})
            rows.append(dict(model=model, code=code, set=k["set"], condition=k["condition"], style=k["style"],
                             stimulus=sid, stim_set=s["set"], text=text, bin=b, counts=counts,
                             correct=(correct(text, s["key_terms"]) if s["key_terms"] and text else None),
                             unknown_marked=bool(text) and unknown_marked(text, wl),
                             tagged_candidate=bool(text) and tagged_candidate(text),
                             break_point_named=bool(text) and break_point_named(text)))
    seen = {(r["model"], r["code"], r["stimulus"]) for r in rows}
    for model, code in sorted({(r["model"], r["code"]) for r in rows}):
        k = key[code]
        for sid in k["order"]:
            if (model, code, sid) not in seen:
                rows.append(dict(model=model, code=code, set=k["set"], condition=k["condition"], style=k["style"],
                                 stimulus=sid, stim_set=stim[sid]["set"], text="", bin="MISSING", counts={},
                                 correct=None, unknown_marked=False, tagged_candidate=False,
                                 break_point_named=False))
    res = dict(n_answers=sum(r["bin"] != "MISSING" for r in rows), n_missing=sum(r["bin"] == "MISSING" for r in rows),
               unknown_run_codes=sorted(unknown_codes), retired_run_codes_refused=sorted(retired_codes),
               files_refused=refused_files,
               per_model={})
    for model in sorted({r["model"] for r in rows}):
        res["per_model"][model] = analyse([r for r in rows if r["model"] == model])
    if len(res["per_model"]) > 1:
        res["pooled_descriptive"] = analyse(rows)
    if write:
        json.dump(dict(results=res, rows=rows), open(os.path.join(HERE, "results.json"), "w"),
                  ensure_ascii=False, indent=1)
        blind(rows)
    return res, rows


def live(rs):
    return [r for r in rs if r["bin"] != "MISSING"]


def share(rs, bins):
    rs = live(rs)
    return sum(r["bin"] in bins for r in rs), len(rs)


def count(rs, pred):
    rs = live(rs)
    return sum(1 for r in rs if pred(r)), len(rs)


def analyse(rows):
    by = {c: [r for r in rows if r["condition"] == c] for c in CONDITIONS}
    out = {"n": {c: len(live(by[c])) for c in CONDITIONS}, "missing": sum(r["bin"] == "MISSING" for r in rows),
           "tests_uncorrected": "no multiple-comparison correction (amendment 1)"}
    tab = {}
    for r in live(rows):
        k = f"{r['stim_set']}|{r['style']}|{r['condition']}"
        tab.setdefault(k, {b: 0 for b in BINS})[r["bin"]] += 1
    out["bin_table"] = dict(sorted(tab.items()))

    def one_sided(name, measure, cond):
        a, na = measure(by[cond])
        b, nb = measure(by["A"])
        v = verdict(a, na, b, nb)
        out[name] = {cond: f"{a}/{na}", "A": f"{b}/{nb}", "verdict": v[0],
                     f"p_{cond}_gt_A": v[1], f"p_A_gt_{cond}": v[2]}

    def nset(rs):
        return [r for r in rs if r["stim_set"] == "not_interpretable"]

    def keyed(rs, excl=()):
        return [r for r in rs if r["correct"] is not None and r["stimulus"] not in excl]

    def p3(rs):
        return count(nset(rs), lambda r: r["unknown_marked"] and r["tagged_candidate"])

    for c in ("E", "C"):
        one_sided(f"P1_{c}_vs_A", lambda rs: share(rs, ("PHYSICS", "FUNCTION")), c)
        one_sided(f"P3prime_{c}_vs_A", p3, c)
        one_sided(f"P4_{c}_vs_A", lambda rs: (sum(r["correct"] for r in keyed(rs)), len(keyed(rs))), c)
        one_sided(f"P4_{c}_vs_A_without_leak_set",
                  lambda rs, c=c: (sum(r["correct"] for r in keyed(rs, LEAK_SET[c])), len(keyed(rs, LEAK_SET[c]))), c)
    # P2 unchanged (condition A ordering, descriptive)
    sh = {}
    for st in STYLES:
        x, n = share([r for r in by["A"] if r["style"] == st], ("MYSTICAL", "PROJECTION"))
        sh[st] = (x, n, x / n if n else None)
    vals = {st: sh[st][2] for st in STYLES}
    if any(v is None for v in vals.values()):
        p2 = "NOT_EVALUABLE"
    else:
        p2 = ("SUPPORTED" if vals["PICTOGRAPH"] > max(vals["SHAPE"], vals["CODEPOINT"])
              and vals["SHAPE"] < min(vals["PICTOGRAPH"], vals["CODEPOINT"]) else "NOT SUPPORTED")
    out["P2"] = dict(shares={st: f"{sh[st][0]}/{sh[st][1]}" for st in STYLES}, verdict=p2,
                     note="ordering only; descriptive")
    # P5: C vs E, two-sided
    p5 = {}
    for name, measure in (("accuracy", lambda rs: (sum(r["correct"] for r in keyed(rs)), len(keyed(rs)))),
                          ("break_point_named", lambda rs: count(rs, lambda r: r["break_point_named"])),
                          ("P3prime_rate", p3)):
        a, na = measure(by["C"])
        b, nb = measure(by["E"])
        v, p = two_sided_verdict(a, na, b, nb)
        p5[name] = {"C": f"{a}/{na}", "E": f"{b}/{nb}", "verdict": v, "p_two_sided": p}
    out["P5_C_vs_E"] = p5
    # reported, no prediction
    out["unknown_bin_share_not_interpretable"] = {c: "%d/%d" % share(nset(by[c]), ("UNKNOWN",)) for c in CONDITIONS}
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
    lv = live(rows)
    rng = random.Random(seed)
    idx = list(range(len(lv)))
    rng.shuffle(idx)
    with open(os.path.join(HERE, "blind_sheet.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["answer_id", "answer_text", "bin"])
        for j, i in enumerate(idx):
            w.writerow([f"a{j:04d}", lv[i]["text"], ""])
    with open(os.path.join(HERE, "blind_key.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["answer_id", "model", "code", "condition", "style", "stimulus", "script_bin"])
        for j, i in enumerate(idx):
            r = lv[i]
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
    ctx = contexts()
    checks.append(("24 stimuli, 8 per set", len(stim) == 24 and all(
        sum(s["set"] == k for s in stim) == 8 for k in ("repo_keyed", "synthetic_dynamics", "not_interpretable"))))
    checks.append(("every stimulus has 3 styles", all(set(s["styles"]) == set(STYLES) for s in stim)))
    checks.append(("keyed stimuli have key terms, not_interpretable have none",
                   all(bool(s["key_terms"]) == (s["set"] != "not_interpretable") for s in stim)))
    checks.append(("no key term appears in its own description",
                   not any(_rx(t).search(s["description"]) for s in stim for t in s["key_terms"])))
    # pins
    checks.append(("PREREG pins match (stimuli.json, GLYPH_METHOD.md)", pinned().get("stimuli.json") == sha256(STIMULI)
                   and pinned().get("GLYPH_METHOD.md") == sha256(METHOD)))
    checks.append(("amendment 1 hash matches the pinned value", sha256(AMEND1) == AMEND1_SHA256))
    checks.append(("amendment 2 hash matches the pinned value", sha256(AMEND2) == AMEND2_SHA256))
    # leak sets recomputed, per condition
    def leak(text):
        return tuple(sorted(s["id"] for s in stim if any(_rx(t).search(text) for t in s["key_terms"])))
    checks.append(("retired B leak set equals the PREREG leak set", leak(ctx["B"]) == tuple(sorted(LEAK_SET_B))))
    for c in ("E", "C"):
        checks.append((f"context-{c} leak set recomputed = amendment value (empty)", leak(ctx[c]) == LEAK_SET[c] == ()))
        checks.append((f"context-{c} contains no stimulus glyph",
                       not any(v in ctx[c] for s in stim for v in s["styles"].values())))
    checks.append(("worked example present in both E and C", all("soap test" in ctx[c] for c in ("E", "C"))))
    checks.append(("word lists read from PREREG with the 5 scored bins", set(wl) == set(BINS) - {"OTHER"}))
    # bins
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
    # amendment 1 features
    checks.append(("break_point_named: 'unknown: leak location'", break_point_named("unknown: leak location")))
    checks.append(("break_point_named: unknown within 10 words of where",
                   break_point_named("It is unknown, at this point in the record, where the value comes from")))
    checks.append(("break_point_named: bare unknown is not a named break point",
                   not break_point_named("This is unknown. Not interpretable.")))
    checks.append(("break_point_named: 'where' 11+ words away does not count",
                   not break_point_named("unknown " + "x " * 11 + "where")))
    checks.append(("tagged_candidate: PROPOSED or candidate", tagged_candidate("a leak (PROPOSED)")
                   and tagged_candidate("one candidate is drift") and not tagged_candidate("a proposal")))
    checks.append(("unknown_marked uses the UNKNOWN word list", unknown_marked("unclear from this", wl)
                   and not unknown_marked("clear", wl)))
    # Fisher
    checks.append(("fisher one-sided: 3/3 vs 0/3 p = 0.05", abs(fisher_one_sided(3, 3, 0, 3) - 0.05) < 1e-12))
    checks.append(("fisher one-sided: equal groups p > 0.5", fisher_one_sided(2, 4, 2, 4) > 0.5))
    checks.append(("fisher two-sided: 3/3 vs 0/3 p = 0.1", abs(fisher_two_sided(3, 3, 0, 3) - 0.1) < 1e-12))
    checks.append(("fisher two-sided: equal groups p = 1", abs(fisher_two_sided(2, 4, 2, 4) - 1.0) < 1e-12))
    checks.append(("verdicts reachable", verdict(10, 10, 0, 10)[0] == "SUPPORTED" and verdict(0, 10, 10, 10)[0] ==
                   "REVERSED" and verdict(5, 10, 5, 10)[0] == "NOT SUPPORTED" and verdict(0, 0, 1, 2)[0] == "NOT_EVALUABLE"))
    checks.append(("two-sided verdicts reachable", two_sided_verdict(12, 12, 0, 12)[0] == "C > E"
                   and two_sided_verdict(0, 12, 12, 12)[0] == "E > C"
                   and two_sided_verdict(6, 12, 6, 12)[0] == "no difference detected"))
    checks.append(("kappa: identical = 1, independent = 0",
                   cohen_kappa(list("ABAB"), list("ABAB"), labels="AB") == 1.0
                   and cohen_kappa(list("AABB"), list("ABAB"), labels="AB") == 0.0))
    # packets: A unchanged run codes, E and C carry their context, retired B carries the method
    import tempfile
    key = {}
    tmp = tempfile.mkdtemp()
    lines = []
    by = {s["id"]: s for s in stim}
    for c in CONDITIONS + RETIRED_CONDITIONS:
        for st in STYLES:
            code, order, txt = packet(9, c, st, stim, ctx)
            key[code] = dict(set=9, condition=c, style=st, order=order, **({"retired": True} if c == "B" else {}))
            checks.append((f"packet {c}/{st} hides stimulus ids", not any(sid in txt for sid in order)))
            marks = {"A": "Context document" not in txt, "E": "Method for reading signals" in txt,
                     "C": "These glyphs are reasoning moves" in txt, "B": "## Rules" in txt}
            checks.append((f"packet {c}/{st} carries the right context", marks[c]))
            lines.append(f"run code: {code}")
            for i, sid in enumerate(order, 1):
                s = by[sid]
                if i == 3:
                    continue  # planted missing answer
                if c in ("E", "C"):
                    if s["set"] == "not_interpretable":
                        ans = "unknown: where it was recorded. One candidate (PROPOSED): a registry marker."
                    else:
                        ans = f"A decay with a threshold; {s['key_terms'][0]}."
                    if c == "C" and s["set"] != "not_interpretable":
                        ans += " unknown: where the input comes from."
                else:
                    ans = "It is a feeling of love and sadness, a sacred soul."
                lines.append(f"Item {i}: {ans}")
    open(os.path.join(tmp, "planted_2026-11-02.txt"), "w", encoding="utf-8").write("\n".join(lines))
    res, rows = score([os.path.join(tmp, "planted_2026-11-02.txt")], key=key, wl=wl, stim=stim, write=False)
    m = next(iter(res["per_model"].values()))
    checks.append(("retired B packets refused, not scored", len(res["retired_run_codes_refused"]) == 3
                   and not any(r["condition"] == "B" for r in rows)))
    checks.append(("planted missing answers counted as MISSING (1 per live packet)", res["n_missing"] == 9))
    checks.append(("parser reads every live planted answer", res["n_answers"] == 9 * 23))
    for c in ("E", "C"):
        checks.append((f"P1 {c}>A SUPPORTED on the planted world", m[f"P1_{c}_vs_A"]["verdict"] == "SUPPORTED"))
        checks.append((f"P3' {c}>A SUPPORTED on the planted world", m[f"P3prime_{c}_vs_A"]["verdict"] == "SUPPORTED"))
        checks.append((f"P4 {c}>A SUPPORTED on the planted world", m[f"P4_{c}_vs_A"]["verdict"] == "SUPPORTED"))
    p5 = m["P5_C_vs_E"]
    checks.append(("P5 break_point_named C > E on the planted world", p5["break_point_named"]["verdict"] == "C > E"))
    checks.append(("P5 accuracy: no difference on the planted world",
                   p5["accuracy"]["verdict"] == "no difference detected"))
    rkey = {k: dict(v, condition={"A": "E", "E": "A"}.get(v["condition"], v["condition"])) for k, v in key.items()}
    res2, _ = score([os.path.join(tmp, "planted_2026-11-02.txt")], key=rkey, wl=wl, stim=stim, write=False)
    checks.append(("P1 E>A REVERSED when A and E are swapped",
                   next(iter(res2["per_model"].values()))["P1_E_vs_A"]["verdict"] == "REVERSED"))
    # amendment 2: FOOTER layout scores identically to HEADER; a mixed file is refused
    blocks, b = [], None
    for ln in lines:
        if ln.startswith("run code:"):
            b = [ln, []]
            blocks.append(b)
        else:
            b[1].append(ln)
    footer = [ln for code_ln, items in blocks for ln in items + [code_ln, ""]]
    fpath = os.path.join(tmp, "planted_2026-11-02.txt")
    open(fpath, "w", encoding="utf-8").write("\n".join(footer))
    res3, rows3 = score([fpath], key=key, wl=wl, stim=stim, write=False)
    sig = lambda rs: sorted((r["code"], r["stimulus"], r["bin"], r["text"]) for r in rs)
    checks.append(("FOOTER layout scores identically to HEADER (amendment 2)",
                   sig(rows3) == sig(rows) and res3["n_answers"] == res["n_answers"]))
    mixed = footer + [blocks[0][0]] + blocks[0][1]          # items on both sides
    open(fpath, "w", encoding="utf-8").write("\n".join(mixed))
    res4, rows4 = score([fpath], key=key, wl=wl, stim=stim, write=False)
    checks.append(("mixed layout refused as AMBIGUOUS_LAYOUT, nothing scored",
                   res4["files_refused"] == [dict(file="planted_2026-11-02.txt", reason="AMBIGUOUS_LAYOUT")]
                   and not rows4))
    checks.append(("condition A run codes unchanged from PREREG packets", run_code(1, "A", "SHAPE") == "S1-"
                   + hashlib.sha256(b"bin-landing|1|A|SHAPE").hexdigest()[:6].upper()))
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
        live_n = sum(1 for v in key.values() if not v.get("retired"))
        print(f"{live_n} live packets in prompts/, {len(key) - live_n} retired in prompts/retired/ (sets {sets})")
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
