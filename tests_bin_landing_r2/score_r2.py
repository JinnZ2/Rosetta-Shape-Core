"""Bin-landing round 2: raw-series packets, scorer, blind sheet, agreement. Stdlib only. CC0.

Design and decision rules: PREREG_R2.md (committed alone first, 47abd1e). Lists, companions and
negators come from its `json r2-lists` block; contexts E and C from round-1 PREREG_AMENDMENT_1.md;
the UNKNOWN list from round-1 PREREG.md. This file holds no copy of any of them.

USAGE
  python3 score_r2.py emit                          prompts/<code>.txt for sets 1 and 2, key.json, PILOT_R2.txt
  python3 score_r2.py score answers/*.txt           writes results_r2.json, blind_sheet_r2.csv, blind_key_r2.csv
  python3 score_r2.py kappa blind_sheet_r2_scored.csv
  python3 score_r2.py --selftest                    planted answers; prints its check count

Answer files: each packet's "run code:" line above or below its reply, consistently (round-1
amendment 2 rule); "Item N: ..." labels kept.
"""
import csv
import hashlib
import json
import os
import random
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
R1 = os.path.join(HERE, "..", "tests_bin_landing")
sys.path.insert(0, R1)
sys.path.insert(0, HERE)
import score as r1          # noqa: E402  round-1 functions, imported not copied
import gen_r2               # noqa: E402

PREREG = os.path.join(HERE, "PREREG_R2.md")
PROMPTS = os.path.join(HERE, "prompts")
KEYFILE = os.path.join(PROMPTS, "key.json")
PILOT = os.path.join(HERE, "PILOT_R2.txt")
SETS = {1: "stimuli_r2.json", 2: "stimuli_r2_set2.json"}

# PREREG_R2.md cannot contain its own hash; pinned here. A later change is an amendment file.
PREREG_SHA256 = "d120263816db0a39b4cf709d0f3876aea324d4eb209dcb295a2c724b1b7f6afa"

CONDITIONS = ["A", "E", "C"]
QUESTION = "What is this glyph/series doing? What would you check, and what follows?"
CODE_PATTERN = r"run code:\s*(R2S\d+-[0-9A-F]{6})"
LABELS_EXTRA = ["HEDGED", "UNKNOWN", "OTHER"]


# ---------------------------------------------------------------- inputs
def sha256(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def pins():
    txt = open(PREREG, encoding="utf-8").read()
    return dict(re.findall(r"^(\S+)\s+(?:\([^)]*\)\s+)?sha256 ([0-9a-f]{64})", txt, re.M))


def check_pins():
    bad = []
    if sha256(PREREG) != PREREG_SHA256:
        bad.append("PREREG_R2.md")
    for name, h in pins().items():
        if sha256(os.path.join(HERE, name)) != h:
            bad.append(name)
    for n, fn in SETS.items():
        regen = json.dumps(gen_r2.build(n), ensure_ascii=False, indent=1)
        if regen != open(os.path.join(HERE, fn), encoding="utf-8").read():
            bad.append(f"{fn} (gen_r2.py does not regenerate it)")
    if bad:
        raise SystemExit("REFUSED: differs from the pre-registered value: " + ", ".join(bad))


def lists():
    txt = open(PREREG, encoding="utf-8").read()
    m = re.search(r"```json r2-lists\n(.*?)\n```", txt, re.S)
    if not m:
        raise SystemExit("REFUSED: no `json r2-lists` block in PREREG_R2.md")
    return json.loads(m.group(1))


def stimuli(n):
    return json.load(open(os.path.join(HERE, SETS[n]), encoding="utf-8"))["items"]


def contexts():
    c = r1.contexts()
    return {"E": c["E"], "C": c["C"]}


def unknown_list():
    return r1.wordlists()["UNKNOWN"]


# ---------------------------------------------------------------- emit
def run_code(set_no, cond):
    return f"R2S{set_no}-" + hashlib.sha256(f"bin-landing-r2|{set_no}|{cond}".encode()).hexdigest()[:6].upper()


def packet(set_no, cond, items, ctx):
    order = [it["id"] for it in items]
    random.Random(f"r2|set{set_no}|{cond}").shuffle(order)
    by = {it["id"]: it for it in items}
    L = ["SERIES READING PACKET", ""]
    if cond != "A":
        L += ["Context document (read it before answering):", "", "-----", ctx[cond].rstrip(), "-----",
              "End of context document.", ""]
    L += ["Answer every item below. Start each answer on a new line with its label, for example "
          "\"Item 1:\". Keep each answer to a few sentences.", ""]
    for i, iid in enumerate(order, 1):
        L += [f"Item {i}", gen_r2.item_text(by[iid]), f"Question: {QUESTION}", ""]
    code = run_code(set_no, cond)
    L += ["-----", f"run code: {code}", ""]
    return code, order, "\n".join(L)


def emit():
    check_pins()
    ctx = contexts()
    os.makedirs(PROMPTS, exist_ok=True)
    key, pilot = {}, []
    for n in SETS:
        items = stimuli(n)
        for c in CONDITIONS:
            code, order, txt = packet(n, c, items, ctx)
            open(os.path.join(PROMPTS, code + ".txt"), "w", encoding="utf-8").write(txt)
            key[code] = dict(set=n, condition=c, order=order)
            if n == 1:
                pilot.append((code, c, txt))
    json.dump(dict(sorted(key.items())), open(KEYFILE, "w"), indent=1)
    out = ["Round 2 pilot: the 3 set-1 packets. One fresh conversation each, memory off.",
           "Paste everything between the ===== lines, nothing else. Order of running is free.", ""]
    for j, (code, c, txt) in enumerate(pilot, 1):
        out += [f"===== PACKET {j} of 3 (run code {code}) =====", txt.rstrip(), f"===== END PACKET {j} =====", ""]
    open(PILOT, "w", encoding="utf-8").write("\n".join(out))
    return key


# ---------------------------------------------------------------- per answer
_TOK = re.compile(r"[A-Za-z']+")


def _rx(term):
    return re.compile(r"\b" + re.escape(term).replace(r"\ ", r"\s+"), re.I)


def negated(text, start, negators):
    before = [t.lower() for t in _TOK.findall(text[:start])][-3:]
    joined = " ".join(before)
    return any((" " in n and n in joined) or (" " not in n and n in before) for n in negators)


def hit_any(text, terms, negators):
    for t in terms:
        for m in _rx(t).finditer(text):
            if not negated(text, m.start(), negators):
                return True
    return False


def class_hits(text, L):
    return {c for c, terms in L["classes"].items() if hit_any(text, terms, L["negators"])}


def judge(text, item, L, unk):
    """-> dict(outcome, label, hits, features). Rules: PREREG_R2.md 'Per answer'."""
    comp = L["companions"]
    hits = class_hits(text, L)
    dyn = hits - {"no_structure"}
    key = item["key"]
    if item["kind"] == "dynamics":
        if dyn:
            hits = dyn
        if key in hits:
            outcome = "correct" if hits - {key} <= set(comp[key]) else "hedged"
        else:
            outcome = "wrong"
    else:
        if "no_structure" in hits and not dyn:
            outcome = "correct"
        elif dyn and "no_structure" not in hits:
            outcome = "false_structure"
        elif dyn:
            outcome = "hedged"
        else:
            outcome = "silent"
    um = any(_rx(t).search(text) for t in unk)
    if outcome == "correct":
        label = key
    elif outcome == "hedged":
        label = "HEDGED"
    elif not hits:
        label = "UNKNOWN" if um else "OTHER"
    elif len(hits) == 1:
        label = next(iter(hits))
    else:
        tops = [c for c in hits if hits - {c} <= set(comp[c])]
        label = tops[0] if len(tops) == 1 else "HEDGED"
    return dict(outcome=outcome, label=label, hits=sorted(hits),
                unknown_marked=um, tagged_candidate=r1.tagged_candidate(text),
                check_named=hit_any(text, L["check_terms"], []),
                action_named=hit_any(text, L["action_terms"], []))


# ---------------------------------------------------------------- score
def score(paths, key=None, L=None, unk=None, items_by_set=None, write=True):
    key = key if key is not None else json.load(open(KEYFILE))
    L = L or lists()
    unk = unk if unk is not None else unknown_list()
    items_by_set = items_by_set or {n: {it["id"]: it for it in stimuli(n)} for n in SETS}
    rows, unknown_codes, refused = [], set(), []
    for p in paths:
        model = os.path.basename(p).rsplit(".", 1)[0]
        try:
            parsed = r1.parse_answers(p, code_pattern=CODE_PATTERN)
        except r1.LayoutRefused as e:
            refused.append(dict(file=os.path.basename(p), reason=str(e)))
            continue
        for code, n, text in parsed:
            if code not in key:
                unknown_codes.add(code)
                continue
            k = key[code]
            if not 1 <= n <= len(k["order"]):
                continue
            iid = k["order"][n - 1]
            it = items_by_set[k["set"]][iid]
            base = dict(model=model, code=code, set=k["set"], condition=k["condition"], item=iid,
                        kind=it["kind"], key=it["key"], text=text)
            base.update(judge(text, it, L, unk) if text else dict(outcome="MISSING", label="MISSING", hits=[]))
            rows.append(base)
    seen = {(r["model"], r["code"], r["item"]) for r in rows}
    for model, code in sorted({(r["model"], r["code"]) for r in rows}):
        k = key[code]
        for iid in k["order"]:
            if (model, code, iid) not in seen:
                it = items_by_set[k["set"]][iid]
                rows.append(dict(model=model, code=code, set=k["set"], condition=k["condition"], item=iid,
                                 kind=it["kind"], key=it["key"], text="", outcome="MISSING", label="MISSING",
                                 hits=[]))
    res = dict(n_answers=sum(r["outcome"] != "MISSING" for r in rows),
               n_missing=sum(r["outcome"] == "MISSING" for r in rows),
               unknown_run_codes=sorted(unknown_codes), files_refused=refused, per_model={})
    for model in sorted({r["model"] for r in rows}):
        mr = [r for r in rows if r["model"] == model]
        res["per_model"][model] = {f"set{n}": analyse([r for r in mr if r["set"] == n])
                                   for n in sorted({r["set"] for r in mr})}
        if len({r["set"] for r in mr}) > 1:
            res["per_model"][model]["pooled_descriptive"] = analyse(mr)
    if write:
        json.dump(dict(results=res, rows=rows), open(os.path.join(HERE, "results_r2.json"), "w"),
                  ensure_ascii=False, indent=1)
        blind(rows)
    return res, rows


def live(rs):
    return [r for r in rs if r["outcome"] != "MISSING"]


def frac(rs, pred):
    rs = live(rs)
    return sum(1 for r in rs if pred(r)), len(rs)


def analyse(rows):
    by = {c: [r for r in rows if r["condition"] == c] for c in CONDITIONS}
    dyn = {c: [r for r in by[c] if r["kind"] == "dynamics"] for c in CONDITIONS}
    ctl = {c: [r for r in by[c] if r["kind"] == "control"] for c in CONDITIONS}
    measures = {
        "accuracy": (dyn, lambda r: r["outcome"] == "correct"),
        "false_structure": (ctl, lambda r: r["outcome"] == "false_structure"),
        "check_named": (by, lambda r: r.get("check_named")),
    }
    out = {"n": {c: len(live(by[c])) for c in CONDITIONS},
           "missing": sum(r["outcome"] == "MISSING" for r in rows),
           "tests_uncorrected": "no multiple-comparison correction (PREREG_R2)"}

    def one_sided(name, measure, cond, higher):
        sets, pred = measures[measure]
        a, n1 = frac(sets[cond], pred)
        b, n2 = frac(sets["A"], pred)
        if higher:
            v, p_up, p_down = r1.verdict(a, n1, b, n2)
        else:
            v, p_up, p_down = r1.verdict(b, n2, a, n1)     # predicted: A higher than cond
        out[name] = {cond: f"{a}/{n1}", "A": f"{b}/{n2}", "verdict": v, "p_predicted": p_up, "p_opposite": p_down}

    for c in ("E", "C"):
        one_sided(f"P1_accuracy_{c}_gt_A", "accuracy", c, True)
        one_sided(f"P2_false_structure_{c}_lt_A", "false_structure", c, False)
        one_sided(f"P3_check_named_{c}_gt_A", "check_named", c, True)
    p4 = {}
    for m in ("accuracy", "false_structure", "check_named"):
        sets, pred = measures[m]
        a, n1 = frac(sets["C"], pred)
        b, n2 = frac(sets["E"], pred)
        v, p = r1.two_sided_verdict(a, n1, b, n2)
        p4[m] = {"C": f"{a}/{n1}", "E": f"{b}/{n2}", "verdict": v, "p_two_sided": p}
    out["P4_C_vs_E"] = p4
    desc = {}
    for c in CONDITIONS:
        d = {}
        for o in ("correct", "hedged", "wrong"):
            d[f"dynamics_{o}"] = "%d/%d" % frac(dyn[c], lambda r, o=o: r["outcome"] == o)
        d["dynamics_correct_or_hedged"] = "%d/%d" % frac(dyn[c], lambda r: r["outcome"] in ("correct", "hedged"))
        for o in ("correct", "false_structure", "hedged", "silent"):
            d[f"controls_{o}"] = "%d/%d" % frac(ctl[c], lambda r, o=o: r["outcome"] == o)
        for f in ("unknown_marked", "tagged_candidate", "check_named", "action_named"):
            d[f] = "%d/%d" % frac(by[c], lambda r, f=f: r.get(f))
        desc[c] = d
    out["descriptive"] = desc
    out["per_item"] = {iid: {c: next((r["outcome"] for r in by[c] if r["item"] == iid), None) for c in CONDITIONS}
                       for iid in sorted({r["item"] for r in rows})}
    return out


# ---------------------------------------------------------------- blind sheet + kappa
def all_labels(L=None):
    return list((L or lists())["classes"]) + LABELS_EXTRA


def blind(rows, seed=20261102):
    lv = live(rows)
    idx = list(range(len(lv)))
    random.Random(seed).shuffle(idx)
    with open(os.path.join(HERE, "blind_sheet_r2.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["answer_id", "answer_text", "label"])
        for j, i in enumerate(idx):
            w.writerow([f"b{j:04d}", lv[i]["text"], ""])
    with open(os.path.join(HERE, "blind_key_r2.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["answer_id", "model", "code", "set", "condition", "item", "key", "outcome", "script_label"])
        for j, i in enumerate(idx):
            r = lv[i]
            w.writerow([f"b{j:04d}", r["model"], r["code"], r["set"], r["condition"], r["item"], r["key"],
                        r["outcome"], r["label"]])


def kappa(scored_csv, key_csv=None):
    labels = all_labels()
    key_csv = key_csv or os.path.join(HERE, "blind_key_r2.csv")
    script = {r["answer_id"]: r["script_label"] for r in csv.DictReader(open(key_csv, encoding="utf-8"))}
    other = {r["answer_id"]: r["label"].strip() for r in csv.DictReader(open(scored_csv, encoding="utf-8"))
             if r.get("label", "").strip()}
    norm = {lab.lower(): lab for lab in labels}
    bad = sorted({v for v in other.values() if v.lower() not in norm})
    if bad:
        raise SystemExit("REFUSED: second-scorer labels outside the PREREG_R2 set: " + ", ".join(bad))
    other = {k: norm[v.lower()] for k, v in other.items()}
    ids = sorted(set(script) & set(other))
    x, y = [script[i] for i in ids], [other[i] for i in ids]
    conf = {a: {b: sum(1 for p, q in zip(x, y) if p == a and q == b) for b in labels} for a in labels}
    k = r1.cohen_kappa(x, y, labels=labels)
    reading = (None if k is None else "word lists track the class definitions at this kappa" if k >= 0.6
               else "word lists do not track the class definitions at this kappa; report both scorers")
    return dict(n=len(ids), kappa=k, reading=reading, confusion_script_rows_vs_second_cols=conf)


# ---------------------------------------------------------------- selftest
def selftest():
    import tempfile
    checks = []
    L = lists()
    unk = unknown_list()
    ctx = contexts()
    checks.append(("PREREG_R2 hash matches the pinned value", sha256(PREREG) == PREREG_SHA256))
    pn = pins()
    checks.append(("PREREG_R2 pins 5 files", len(pn) == 5))
    checks.append(("every pinned file matches", all(sha256(os.path.join(HERE, f)) == h for f, h in pn.items())))
    for n, fn in SETS.items():
        checks.append((f"gen_r2.py regenerates {fn} byte for byte",
                       json.dumps(gen_r2.build(n), ensure_ascii=False, indent=1)
                       == open(os.path.join(HERE, fn), encoding="utf-8").read()))
    for n in SETS:
        items = stimuli(n)
        checks.append((f"set {n}: 16 items, 12 dynamics + 4 controls", len(items) == 16
                       and sum(i["kind"] == "dynamics" for i in items) == 12))
        checks.append((f"set {n}: every item has 40 rows", all(len(i["rows"]) == 40 for i in items)))
        checks.append((f"set {n}: 16 distinct glyphs", len({i["glyph"] for i in items}) == 16))
        terms = [t for v in L["classes"].values() for t in v] + L["check_terms"] + L["action_terms"]
        checks.append((f"set {n}: no list term in any item text",
                       not any(_rx(t).search(gen_r2.item_text(i)) for i in items for t in terms)))
        checks.append((f"set {n}: item text is glyph, column labels and numbers only",
                       all(re.fullmatch(r"Glyph: U\+F7[AB][0-9A-F](\n[tkx]: [-0-9. ]+)+", gen_r2.item_text(i))
                           for i in items)))
        checks.append((f"set {n}: keys cover all 12 dynamic classes",
                       {i["key"] for i in items if i["kind"] == "dynamics"} == set(L["classes"]) - {"no_structure"}))
    leak_terms = [t for v in L["classes"].values() for t in v] + L["check_terms"]
    for c in ("E", "C"):
        checks.append((f"context-{c} leak set empty (class lists + check_terms)",
                       not any(_rx(t).search(ctx[c]) for t in leak_terms)))
    checks.append(("question leak set empty", not any(_rx(t).search(QUESTION) for t in leak_terms)))
    checks.append(("known action echo is exactly 'repair'",
                   sorted(t for t in L["action_terms"] if any(_rx(t).search(ctx[c]) for c in ctx)) == ["repair"]))
    checks.append(("companions declared for every class", set(L["companions"]) == set(L["classes"])))
    # judge
    dyn = {"kind": "dynamics", "key": "hysteresis"}
    ctl = {"kind": "control", "key": "no_structure"}
    j = lambda t, it: judge(t, it, L, unk)
    checks.append(("key + companion = correct", j("Hysteresis: it jumps at a threshold.", dyn)["outcome"] == "correct"))
    checks.append(("key + non-companion = hedged", j("Hysteresis, or maybe a periodic cycle.", dyn)["outcome"] == "hedged"))
    checks.append(("noise dropped on a dynamics item", j("Hysteresis with some noise.", dyn)["outcome"] == "correct"))
    checks.append(("key missing = wrong", j("A periodic cycle.", dyn)["outcome"] == "wrong"))
    checks.append(("negated term discarded", j("This is not hysteresis; it is noise.", dyn)["hits"] == ["no_structure"]))
    checks.append(("control: noise only = correct", j("Just random noise, no trend.", ctl)["outcome"] == "correct"))
    checks.append(("control: dynamic only = false_structure",
                   j("A linear ramp upward.", ctl)["outcome"] == "false_structure"))
    checks.append(("control: both = hedged", j("Noise around a linear ramp.", ctl)["outcome"] == "hedged"))
    checks.append(("control: nothing = silent", j("Hard to say.", ctl)["outcome"] == "silent"))
    checks.append(("'no periodic' does not claim structure", j("Random noise, no periodic part.", ctl)["outcome"] == "correct"))
    checks.append(("bare 'check' is not check_named", not j("I would check it.", ctl)["check_named"]))
    checks.append(("'fit' is check_named", j("Fit an exponential.", ctl)["check_named"]))
    checks.append(("unknown label", j("Unknown from these numbers.", ctl)["label"] == "UNKNOWN"))
    # packets
    for n in SETS:
        for c in CONDITIONS:
            code, order, txt = packet(n, c, stimuli(n), ctx)
            checks.append((f"packet {n}{c} hides item ids and keys",
                           not any(i["id"] in txt or i["key"] in txt for i in stimuli(n))))
            checks.append((f"packet {n}{c} context", ("Context document" in txt) == (c != "A")
                           and (c != "E" or "Method for reading signals" in txt)
                           and (c != "C" or "These glyphs are reasoning moves" in txt)))
            checks.append((f"packet {n}{c} run code at the bottom", txt.rstrip().endswith(f"run code: {code}")))
    checks.append(("run codes distinct across sets and conditions",
                   len({run_code(n, c) for n in SETS for c in CONDITIONS}) == 6))
    checks.append(("round-1 parser does not read round-2 codes",
                   re.search(r"run code:\s*(S\d+-[0-9A-F]{6})", "run code: " + run_code(1, "A")) is None))
    # planted world: E and C right, A invents structure and names nothing
    tmp = tempfile.mkdtemp()
    key, blocks = {}, []
    for c in CONDITIONS:
        code, order, _ = packet(1, c, stimuli(1), ctx)
        key[code] = dict(set=1, condition=c, order=order)
        by = {i["id"]: i for i in stimuli(1)}
        lines = []
        for k_, iid in enumerate(order, 1):
            it = by[iid]
            if k_ == 2:
                continue                                  # planted missing answer
            if c == "A":
                ans = "A linear ramp, perhaps periodic." if it["kind"] == "control" else "Something changes over time."
            elif it["kind"] == "control":
                ans = "Random noise; fit a mean and compare the variance of halves."
            else:
                ans = L["classes"][it["key"]][0] + " shape; fit it and compare residuals."
            lines.append(f"Item {k_}: {ans}")
        blocks.append((f"run code: {code}", lines))
    fpath = os.path.join(tmp, "planted_2026-11-02.txt")
    open(fpath, "w", encoding="utf-8").write("\n".join(ln for h, ls in blocks for ln in [h] + ls + [""]))
    items_by_set = {n: {i["id"]: i for i in stimuli(n)} for n in SETS}
    res, rows = score([fpath], key=key, L=L, unk=unk, items_by_set=items_by_set, write=False)
    m = res["per_model"]["planted_2026-11-02"]["set1"]
    checks.append(("planted: 45 answers, 3 MISSING", res["n_answers"] == 45 and res["n_missing"] == 3))
    for c in ("E", "C"):
        checks.append((f"planted P1 {c}>A SUPPORTED", m[f"P1_accuracy_{c}_gt_A"]["verdict"] == "SUPPORTED"))
        checks.append((f"planted P3 {c}>A SUPPORTED", m[f"P3_check_named_{c}_gt_A"]["verdict"] == "SUPPORTED"))
        checks.append((f"planted P2 {c}<A evaluable", m[f"P2_false_structure_{c}_lt_A"]["verdict"] != "NOT_EVALUABLE"))
    checks.append(("planted P4 accuracy: no difference", m["P4_C_vs_E"]["accuracy"]["verdict"] == "no difference detected"))
    # footer layout scores the same; mixed is refused
    open(fpath, "w", encoding="utf-8").write("\n".join(ln for h, ls in blocks for ln in ls + [h, ""]))
    res2, rows2 = score([fpath], key=key, L=L, unk=unk, items_by_set=items_by_set, write=False)
    sig = lambda rs: sorted((r["code"], r["item"], r["outcome"], r["text"]) for r in rs)
    checks.append(("FOOTER layout scores identically to HEADER", sig(rows2) == sig(rows)))
    open(fpath, "a", encoding="utf-8").write("\n" + blocks[0][0] + "\nItem 1: noise\n")
    res3, rows3 = score([fpath], key=key, L=L, unk=unk, items_by_set=items_by_set, write=False)
    checks.append(("mixed layout refused", res3["files_refused"] == [dict(file="planted_2026-11-02.txt",
                                                                         reason="AMBIGUOUS_LAYOUT")] and not rows3))
    # swapping A and E reverses P1
    rkey = {k: dict(v, condition={"A": "E", "E": "A"}.get(v["condition"], v["condition"])) for k, v in key.items()}
    open(fpath, "w", encoding="utf-8").write("\n".join(ln for h, ls in blocks for ln in [h] + ls + [""]))
    res4, _ = score([fpath], key=rkey, L=L, unk=unk, items_by_set=items_by_set, write=False)
    checks.append(("P1 E>A REVERSED when A and E are swapped",
                   res4["per_model"]["planted_2026-11-02"]["set1"]["P1_accuracy_E_gt_A"]["verdict"] == "REVERSED"))
    checks.append(("kappa labels: 13 classes + HEDGED, UNKNOWN, OTHER", len(all_labels(L)) == 16))
    bad = [n for n, ok in checks if not ok]
    for n in bad:
        print("  FAIL:", n)
    print("bin_landing_r2 selftest %d/%d" % (len(checks) - len(bad), len(checks)))
    return not bad


def main(argv):
    if "--selftest" in argv:
        sys.exit(0 if selftest() else 1)
    if not argv:
        print(__doc__)
        return
    if argv[0] == "emit":
        print(len(emit()), "packets")
    elif argv[0] == "score":
        check_pins()
        res, _ = score(argv[1:])
        print(json.dumps(res, indent=1))
    elif argv[0] == "kappa":
        print(json.dumps(kappa(argv[1]), indent=1))
    else:
        print(__doc__)


if __name__ == "__main__":
    main(sys.argv[1:])
