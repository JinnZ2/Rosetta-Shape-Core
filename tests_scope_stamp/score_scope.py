"""Uncued scope-stamp test: packets, scorer, blind sheet, agreement. Stdlib only. CC0. Co-authored.

Design and rules: PREREG_SCOPE.md (committed alone first, a05e215). The S method line, lists and
negators are read from it; items and keys from items_scope.json (pinned). No copies here.

USAGE
  python3 score_scope.py emit                         prompts/<code>.txt (A, S), key.json, PILOT_SCOPE.txt
  python3 score_scope.py score answers/*.txt          writes results_scope.json, blind_sheet_scope.csv, blind_key_scope.csv
  python3 score_scope.py kappa blind_sheet_scope_scored.csv
  python3 score_scope.py --selftest                   planted answers; prints its check count
"""
import csv
import hashlib
import json
import os
import random
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "tests_bin_landing"))
sys.path.insert(0, os.path.join(HERE, "..", "tests_bin_landing_r2"))
import score as r1          # noqa: E402  parse_answers, verdict, cohen_kappa, LayoutRefused
import score_r2 as r2       # noqa: E402  _rx, negated (same matching rules)

PREREG = os.path.join(HERE, "PREREG_SCOPE.md")
ITEMS = os.path.join(HERE, "items_scope.json")
BUILD = os.path.join(HERE, "build_items.py")
PROMPTS = os.path.join(HERE, "prompts")
KEYFILE = os.path.join(PROMPTS, "key.json")
PILOT = os.path.join(HERE, "PILOT_SCOPE.txt")
PREREG_SHA256 = "53f3c2bbd221152f82d0151efee807262361e6bee0f16d5fa0db1f455b8554bc"   # cannot hold its own hash
CONDITIONS = ["A", "S"]
CODE_PATTERN = r"run code:\s*(SC\d+-[0-9A-F]{6})"
LABELS = ["STAMP_SPECIFIC", "TRANSPORTED", "GENERIC_HEDGE", "OTHER"]


def sha256(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def _prereg():
    return open(PREREG, encoding="utf-8").read()


def pins():
    return dict(re.findall(r"^(\S+\.(?:json|py))\s+sha256 ([0-9a-f]{64})", _prereg(), re.M))


def regenerates():
    """Run build_items.py in a scratch copy and compare its output with the pinned items_scope.json."""
    import shutil
    import tempfile
    tmp = tempfile.mkdtemp()
    shutil.copy(BUILD, tmp)
    out = subprocess.run([sys.executable, "-I", "build_items.py"], cwd=tmp, capture_output=True, text=True)
    built = os.path.join(tmp, "items_scope.json")
    return (out.returncode == 0 and os.path.exists(built)
            and open(built, encoding="utf-8").read() == open(ITEMS, encoding="utf-8").read())


def check_pins():
    bad = []
    if sha256(PREREG) != PREREG_SHA256:
        bad.append("PREREG_SCOPE.md")
    for name, h in pins().items():
        if sha256(os.path.join(HERE, name)) != h:
            bad.append(name)
    if not regenerates():
        bad.append("items_scope.json (build_items.py does not regenerate it)")
    if bad:
        raise SystemExit("REFUSED: differs from the pre-registered value: " + ", ".join(bad))


def lists():
    m = re.search(r"```json scope-lists\n(.*?)\n```", _prereg(), re.S)
    if not m:
        raise SystemExit("REFUSED: no `json scope-lists` block in PREREG_SCOPE.md")
    return json.loads(m.group(1))


def method_s():
    m = re.search(r"```text method-S\n(.*?)\n```", _prereg(), re.S)
    if not m:
        raise SystemExit("REFUSED: no `text method-S` block in PREREG_SCOPE.md")
    return m.group(1).strip()


def items():
    return json.load(open(ITEMS, encoding="utf-8"))["items"]


# ---------------------------------------------------------------- emit
def run_code(set_no, cond):
    return f"SC{set_no}-" + hashlib.sha256(f"scope-stamp|{set_no}|{cond}".encode()).hexdigest()[:6].upper()


def packet(set_no, cond, its, mline):
    order = [it["id"] for it in its]
    random.Random(f"scope|set{set_no}|{cond}").shuffle(order)
    by = {it["id"]: it for it in its}
    L = ["FINDINGS PACKET", ""]
    if cond == "S":
        L += ["Method (read it before answering):", mline, ""]
    L += ["Answer every item below. Start each answer on a new line with its label, for example "
          "\"Item 1:\". Keep each answer to a few sentences.", ""]
    for i, iid in enumerate(order, 1):
        L += [f"Item {i}", f"Finding: {by[iid]['statement']}", f"Question: {by[iid]['question']}", ""]
    code = run_code(set_no, cond)
    L += ["-----", f"run code: {code}", ""]
    return code, order, "\n".join(L)


def emit():
    check_pins()
    its, mline = items(), method_s()
    os.makedirs(PROMPTS, exist_ok=True)
    key, blocks = {}, []
    for c in CONDITIONS:
        code, order, txt = packet(1, c, its, mline)
        open(os.path.join(PROMPTS, code + ".txt"), "w", encoding="utf-8").write(txt)
        key[code] = dict(set=1, condition=c, order=order)
        blocks.append((code, txt))
    json.dump(dict(sorted(key.items())), open(KEYFILE, "w"), indent=1)
    out = ["Scope-stamp pilot: 2 packets. One fresh conversation each, memory off.",
           "Paste everything between the ===== lines, nothing else. Order of running is free.", ""]
    for j, (code, txt) in enumerate(blocks, 1):
        out += [f"===== PACKET {j} of 2 (run code {code}) =====", txt.rstrip(), f"===== END PACKET {j} =====", ""]
    open(PILOT, "w", encoding="utf-8").write("\n".join(out))
    return key


# ---------------------------------------------------------------- per answer
def _hit(text, terms, negators):
    for t in terms:
        for m in r2._rx(t).finditer(text):
            if not negators or not r2.negated(text, m.start(), negators):
                return True
    return False


def judge(text, it, L):
    check = _hit(text, L["check_terms"], [])
    if it["kind"] == "control":
        return dict(control_correct=_hit(text, it["correct_terms"], []),
                    hedge=_hit(text, L["hedge_terms"], []), check_named=check, label="CONTROL")
    stamp = _hit(text, it["stamp_terms"], [])
    hedge = _hit(text, L["hedge_terms"], []) and not stamp
    transported = _hit(text, it["transport_terms"], L["negators"]) and not stamp
    label = ("STAMP_SPECIFIC" if stamp else "TRANSPORTED" if transported
             else "GENERIC_HEDGE" if hedge else "OTHER")
    return dict(stamp_named_specific=stamp, generic_hedge=hedge, transported=transported,
                check_named=check, label=label)


# ---------------------------------------------------------------- score
def score(paths, key=None, L=None, its=None, write=True):
    key = key if key is not None else json.load(open(KEYFILE))
    L = L or lists()
    by = {it["id"]: it for it in (its or items())}
    rows, unknown, refused = [], set(), []
    for p in paths:
        model = os.path.basename(p).rsplit(".", 1)[0]
        try:
            parsed = r1.parse_answers(p, code_pattern=CODE_PATTERN)
        except r1.LayoutRefused as e:
            refused.append(dict(file=os.path.basename(p), reason=str(e)))
            continue
        for code, n, text in parsed:
            if code not in key:
                unknown.add(code)
                continue
            k = key[code]
            if not 1 <= n <= len(k["order"]):
                continue
            it = by[k["order"][n - 1]]
            r = dict(model=model, code=code, condition=k["condition"], item=it["id"], kind=it["kind"], text=text)
            r.update(judge(text, it, L) if text else dict(label="MISSING"))
            rows.append(r)
    seen = {(r["model"], r["code"], r["item"]) for r in rows}
    for model, code in sorted({(r["model"], r["code"]) for r in rows}):
        for iid in key[code]["order"]:
            if (model, code, iid) not in seen:
                rows.append(dict(model=model, code=code, condition=key[code]["condition"], item=iid,
                                 kind=by[iid]["kind"], text="", label="MISSING"))
    res = dict(n_answers=sum(r["label"] != "MISSING" for r in rows),
               n_missing=sum(r["label"] == "MISSING" for r in rows),
               unknown_run_codes=sorted(unknown), files_refused=refused, per_model={})
    for model in sorted({r["model"] for r in rows}):
        res["per_model"][model] = analyse([r for r in rows if r["model"] == model])
    if write:
        json.dump(dict(results=res, rows=rows), open(os.path.join(HERE, "results_scope.json"), "w"),
                  ensure_ascii=False, indent=1)
        blind(rows, by)
    return res, rows


def _frac(rs, f):
    rs = [r for r in rs if r["label"] != "MISSING"]
    return sum(1 for r in rs if r.get(f)), len(rs)


def analyse(rows):
    sc = {c: [r for r in rows if r["condition"] == c and r["kind"] == "scoped"] for c in CONDITIONS}
    ct = {c: [r for r in rows if r["condition"] == c and r["kind"] == "control"] for c in CONDITIONS}
    out = {"n_scoped": {c: _frac(sc[c], "item")[1] for c in CONDITIONS},
           "n_control": {c: _frac(ct[c], "item")[1] for c in CONDITIONS},
           "missing": sum(r["label"] == "MISSING" for r in rows),
           "tests_uncorrected": "no multiple-comparison correction (PREREG_SCOPE)"}
    for name, f, s_higher in (("P1_stamp_named_specific_S_gt_A", "stamp_named_specific", True),
                              ("P2_transported_S_lt_A", "transported", False),
                              ("P3_generic_hedge_S_lt_A", "generic_hedge", False)):
        a, n1 = _frac(sc["S"], f)
        b, n2 = _frac(sc["A"], f)
        v, p_pred, p_opp = r1.verdict(a, n1, b, n2) if s_higher else r1.verdict(b, n2, a, n1)
        out[name] = {"S": f"{a}/{n1}", "A": f"{b}/{n2}", "verdict": v, "p_predicted": p_pred, "p_opposite": p_opp}
    out["descriptive"] = {c: {
        "check_named_scoped": "%d/%d" % _frac(sc[c], "check_named"),
        "control_correct": "%d/%d" % _frac(ct[c], "control_correct"),
        "control_hedge": "%d/%d" % _frac(ct[c], "hedge"),
        "control_check_named": "%d/%d" % _frac(ct[c], "check_named"),
        "labels_scoped": {lab: sum(r["label"] == lab for r in sc[c]) for lab in LABELS}} for c in CONDITIONS}
    out["per_item"] = {iid: {c: next((r["label"] for r in rows if r["item"] == iid and r["condition"] == c), None)
                             for c in CONDITIONS} for iid in sorted({r["item"] for r in rows})}
    return out


# ---------------------------------------------------------------- blind sheet + kappa
def blind(rows, by, seed=20261102):
    lv = [r for r in rows if r["label"] not in ("MISSING", "CONTROL")]
    idx = list(range(len(lv)))
    random.Random(seed).shuffle(idx)
    with open(os.path.join(HERE, "blind_sheet_scope.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["answer_id", "finding", "question", "answer_text", "label"])
        for j, i in enumerate(idx):
            it = by[lv[i]["item"]]
            w.writerow([f"s{j:04d}", it["statement"], it["question"], lv[i]["text"], ""])
    with open(os.path.join(HERE, "blind_key_scope.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["answer_id", "model", "code", "condition", "item", "script_label"])
        for j, i in enumerate(idx):
            r = lv[i]
            w.writerow([f"s{j:04d}", r["model"], r["code"], r["condition"], r["item"], r["label"]])


def kappa(scored_csv, key_csv=None):
    key_csv = key_csv or os.path.join(HERE, "blind_key_scope.csv")
    script = {r["answer_id"]: r["script_label"] for r in csv.DictReader(open(key_csv, encoding="utf-8"))}
    other = {r["answer_id"]: r["label"].strip().upper() for r in csv.DictReader(open(scored_csv, encoding="utf-8"))
             if r.get("label", "").strip()}
    bad = sorted({v for v in other.values() if v not in LABELS})
    if bad:
        raise SystemExit("REFUSED: second-scorer labels outside the PREREG_SCOPE set: " + ", ".join(bad))
    ids = sorted(set(script) & set(other))
    x, y = [script[i] for i in ids], [other[i] for i in ids]
    k = r1.cohen_kappa(x, y, labels=LABELS)
    return dict(n=len(ids), kappa=k,
                reading=None if k is None else ("labels track the definitions at this kappa" if k >= 0.6
                                                 else "labels do not track the definitions; report both scorers"),
                confusion_script_rows_vs_second_cols={a: {b: sum(1 for p, q in zip(x, y) if p == a and q == b)
                                                          for b in LABELS} for a in LABELS})


# ---------------------------------------------------------------- selftest
def selftest():
    import tempfile
    checks = []
    L, its, mline = lists(), items(), method_s()
    checks.append(("PREREG_SCOPE hash matches the pinned value", sha256(PREREG) == PREREG_SHA256))
    checks.append(("PREREG pins items_scope.json and build_items.py",
                   set(pins()) == {"items_scope.json", "build_items.py"}
                   and all(sha256(os.path.join(HERE, f)) == h for f, h in pins().items())))
    checks.append(("build_items.py regenerates items_scope.json byte for byte", regenerates()))
    checks.append(("20 items: 16 scoped + 4 controls", len(its) == 20 and sum(i["kind"] == "scoped" for i in its) == 16))
    checks.append(("domains include medicine, psychology, engineering, nutrition, economics",
                   {"medicine", "psychology", "engineering", "nutrition", "economics"}
                   <= {i["domain"] for i in its if i["kind"] == "scoped"}))
    sc = [i for i in its if i["kind"] == "scoped"]
    checks.append(("every scoped item has key, source, stamp and transport terms",
                   all(i["key"] and i["source"] and i["stamp_terms"] and i["transport_terms"] for i in sc)))
    checks.append(("every source marked CARRIED", all(i["source_status"].startswith("CARRIED") for i in sc)))
    txt = lambda i: i["statement"] + " " + i["question"]
    checks.append(("no stamp term in any item text or the S line (uncued)",
                   not any(r2._rx(t).search(txt(i)) or r2._rx(t).search(mline) for i in sc for t in i["stamp_terms"])))
    checks.append(("no transport term in any item text (no echo)",
                   not any(r2._rx(t).search(txt(i)) for i in sc for t in i["transport_terms"])))
    for name in ("hedge_terms", "check_terms"):
        checks.append((f"no {name} in item text or S line",
                       not any(r2._rx(t).search(txt(i)) or r2._rx(t).search(mline) for i in its for t in L[name])))
    t01 = next(i for i in its if i["id"] == "T01")
    j = lambda t: judge(t, t01, L)
    checks.append(("stamp named -> STAMP_SPECIFIC", j("That figure is Wunderlich's, from armpit readings.")["label"] == "STAMP_SPECIFIC"))
    checks.append(("stamp beats transport", j("Yes it is low by Wunderlich's 1868 number.")["label"] == "STAMP_SPECIFIC"))
    checks.append(("transport, no stamp -> TRANSPORTED", j("Yes, it is low.")["label"] == "TRANSPORTED"))
    checks.append(("negated transport is not transport", not j("No, it is not low; it is not below normal.")["transported"]))
    checks.append(("generic hedge -> GENERIC_HEDGE", j("It varies by person.")["label"] == "GENERIC_HEDGE"))
    checks.append(("hedge with stamp is not generic", not j("It varies; the 98.6 is Wunderlich's.")["generic_hedge"]))
    checks.append(("check_named", j("Measure again with an oral thermometer.")["check_named"]))
    for c in CONDITIONS:
        code, order, t = packet(1, c, its, mline)
        checks.append((f"packet {c}: ids and keys hidden", not any(i["id"] in t or i.get("source", "#") in t for i in its)))
        checks.append((f"packet {c}: method line only in S", (mline in t) == (c == "S")))
        checks.append((f"packet {c}: run code at the bottom", t.rstrip().endswith(f"run code: {code}")))
    checks.append(("scope codes not read by round-1 or round-2 parsers",
                   not re.search(r"run code:\s*(S\d+-[0-9A-F]{6})", "run code: " + run_code(1, "A"))
                   and not re.search(r2.CODE_PATTERN, "run code: " + run_code(1, "A"))))
    # planted world: S names stamps, A transports
    tmp = tempfile.mkdtemp()
    key, blocks = {}, []
    by = {i["id"]: i for i in its}
    for c in CONDITIONS:
        code, order, _ = packet(1, c, its, mline)
        key[code] = dict(set=1, condition=c, order=order)
        lines = []
        for n, iid in enumerate(order, 1):
            it = by[iid]
            if n == 1:
                continue
            if it["kind"] == "control":
                ans = it["correct_terms"][0] + "."
            elif c == "S":
                ans = f"That comes from {it['stamp_terms'][0]}; compare with newer data."
            else:
                ans = it["transport_terms"][0] + "."
            lines.append(f"Item {n}: {ans}")
        blocks.append((f"run code: {code}", lines))
    fpath = os.path.join(tmp, "planted_2026-11-02.txt")
    open(fpath, "w", encoding="utf-8").write("\n".join(x for h, ls in blocks for x in ls + [h, ""]))   # footer layout
    res, rows = score([fpath], key=key, L=L, its=its, write=False)
    m = res["per_model"]["planted_2026-11-02"]
    checks.append(("planted: 38 answers, 2 MISSING", res["n_answers"] == 38 and res["n_missing"] == 2))
    checks.append(("planted P1 SUPPORTED", m["P1_stamp_named_specific_S_gt_A"]["verdict"] == "SUPPORTED"))
    checks.append(("planted P2 SUPPORTED", m["P2_transported_S_lt_A"]["verdict"] == "SUPPORTED"))
    checks.append(("planted P3 NOT SUPPORTED (no hedges planted)", m["P3_generic_hedge_S_lt_A"]["verdict"] == "NOT SUPPORTED"))
    checks.append(("planted controls all correct", all(m["descriptive"][c]["control_correct"].split("/")[0]
                                                      == m["descriptive"][c]["control_correct"].split("/")[1]
                                                      for c in CONDITIONS)))
    rkey = {k: dict(v, condition={"A": "S", "S": "A"}[v["condition"]]) for k, v in key.items()}
    res2, _ = score([fpath], key=rkey, L=L, its=its, write=False)
    checks.append(("P1 REVERSED when A and S are swapped",
                   res2["per_model"]["planted_2026-11-02"]["P1_stamp_named_specific_S_gt_A"]["verdict"] == "REVERSED"))
    open(fpath, "a", encoding="utf-8").write("\nItem 1: extra after the last code\n")
    res3, rows3 = score([fpath], key=key, L=L, its=its, write=False)
    checks.append(("mixed layout refused", res3["files_refused"] and not rows3))
    bad = [n for n, ok in checks if not ok]
    for n in bad:
        print("  FAIL:", n)
    print("scope_stamp selftest %d/%d" % (len(checks) - len(bad), len(checks)))
    return not bad


def main(argv):
    if "--selftest" in argv:
        sys.exit(0 if selftest() else 1)
    if not argv:
        print(__doc__)
    elif argv[0] == "emit":
        print(len(emit()), "packets")
    elif argv[0] == "score":
        check_pins()
        print(json.dumps(score(argv[1:])[0], indent=1))
    elif argv[0] == "kappa":
        print(json.dumps(kappa(argv[1]), indent=1))
    else:
        print(__doc__)


if __name__ == "__main__":
    main(sys.argv[1:])
