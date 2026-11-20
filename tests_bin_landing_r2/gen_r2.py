"""Round 2 stimuli: glyph + raw numbers only. Stdlib, fixed seeds, deterministic.

    python3 gen_r2.py [--set N]    writes stimuli_r2.json (set 1) or stimuli_r2_set<N>.json

Each item: a meaning-free Private Use Area code point shown as text, neutral column labels
(t, x; or k, x where a knob exists), 40 rows, 2 decimals, mild noise. No descriptive words.
The answer key (dynamic class) lives in the file but never in an item's text.
CC0. Co-authored.
"""
import json
import math
import random
import sys

N = 40
GLYPHS = ["U+F7%02X" % c for c in range(0xA1, 0xB1)]       # 16 code points, Private Use Area


def r2(v):
    v = round(v, 2)
    return 0.0 if v == 0 else v


def g_leaky(rng):
    on = set(range(3, 7)) | {14, 15, 17, 18} | set(range(28, 34))
    x, out = 0.0, []
    for t in range(N):
        x = 0.8 * x + (1.0 if t in on else 0.0)
        out.append(x + rng.gauss(0, 0.03))
    return dict(cols=["t", "x"], rows=[[t, r2(v)] for t, v in enumerate(out)])


def g_threshold(rng):
    rows = []
    for i in range(N):
        k = i * 0.1
        x = (0.15 if k < 2.45 else 1.6) + rng.gauss(0, 0.03)
        rows.append([r2(k), r2(x)])
    return dict(cols=["k", "x"], rows=rows)


def g_saturation(rng):
    rows = []
    for i in range(N):
        k = i * 0.1
        rows.append([r2(k), r2(2.0 * (1 - math.exp(-1.2 * k)) + rng.gauss(0, 0.03))])
    return dict(cols=["k", "x"], rows=rows)


def g_hysteresis(rng):
    ks = [i * 0.1 for i in range(20)] + [(19 - i) * 0.1 for i in range(20)]
    state, rows = 0, []
    for j, k in enumerate(ks):
        up = j < 20
        if up and k >= 1.3:
            state = 1
        if not up and k < 0.6:
            state = 0
        rows.append([r2(k), r2((1.8 if state else 0.2) + rng.gauss(0, 0.03))])
    return dict(cols=["k", "x"], rows=rows)


def g_bifurcation(rng):
    rows = []
    for i in range(N):
        k = i * 0.05
        x = 0.0 if k <= 1.0 else rng.choice((-1, 1)) * math.sqrt(k - 1.0)
        rows.append([r2(k), r2(x + rng.gauss(0, 0.02))])
    return dict(cols=["k", "x"], rows=rows)


def g_flicker(rng):
    s, out = 0, []
    for t in range(N):
        if t and rng.random() < 0.15:
            s = 1 - s
        out.append((1.5 if s else 0.3) + rng.gauss(0, 0.03))
    if len(set(round(v) for v in out)) < 2:          # guarantee both levels appear
        out[N // 2:N // 2 + 5] = [1.5 + rng.gauss(0, 0.03) for _ in range(5)]
    return dict(cols=["t", "x"], rows=[[t, r2(v)] for t, v in enumerate(out)])


def g_intermittency(rng):
    out = [rng.gauss(0, 0.03) for _ in range(N)]
    for start in (9, 22, 31):
        for d in range(rng.choice((2, 3))):
            out[start + d] = rng.choice((-1, 1)) * rng.uniform(1.0, 2.5)
    return dict(cols=["t", "x"], rows=[[t, r2(v)] for t, v in enumerate(out)])


def g_critical_slowing(rng):
    out, x = [], 0.0
    for t in range(N):
        a = (0.35, 0.6, 0.8, 0.93)[t // 10]
        x = 1.0 if t % 10 == 0 else a * x
        out.append(x + rng.gauss(0, 0.02))
    return dict(cols=["t", "x"], rows=[[t, r2(v)] for t, v in enumerate(out)])


def g_damped(rng):
    return dict(cols=["t", "x"], rows=[[t, r2(2.0 * math.exp(-0.08 * t) * math.cos(0.8 * t) + rng.gauss(0, 0.02))]
                                       for t in range(N)])


def g_expdecay(rng):
    return dict(cols=["t", "x"], rows=[[t, r2(3.0 * math.exp(-0.12 * t) + rng.gauss(0, 0.02))] for t in range(N)])


def g_drift(rng):
    return dict(cols=["t", "x"], rows=[[t, r2(0.5 + 0.05 * t + rng.gauss(0, 0.04))] for t in range(N)])


def g_periodic(rng):
    return dict(cols=["t", "x"], rows=[[t, r2(math.sin(2 * math.pi * t / 10) + rng.gauss(0, 0.04))] for t in range(N)])


def g_white(rng):
    return dict(cols=["t", "x"], rows=[[t, r2(rng.gauss(0, 0.5))] for t in range(N)])


def g_walk(rng):
    x, rows = 0.0, []
    for t in range(N):
        x += rng.gauss(0, 0.3)
        rows.append([t, r2(x)])
    return dict(cols=["t", "x"], rows=rows)


def g_const(rng):
    return dict(cols=["t", "x"], rows=[[t, r2(1.2 + rng.gauss(0, 0.05))] for t in range(N)])


ITEMS = [   # id, kind, key class, generator
    ("Y01", "dynamics", "leaky_integrator", g_leaky),
    ("Y02", "dynamics", "threshold_jump", g_threshold),
    ("Y03", "dynamics", "saturation", g_saturation),
    ("Y04", "dynamics", "hysteresis", g_hysteresis),
    ("Y05", "dynamics", "bifurcation", g_bifurcation),
    ("Y06", "dynamics", "flicker", g_flicker),
    ("Y07", "dynamics", "intermittency", g_intermittency),
    ("Y08", "dynamics", "critical_slowing", g_critical_slowing),
    ("Y09", "dynamics", "damped_oscillation", g_damped),
    ("Y10", "dynamics", "exponential_decay", g_expdecay),
    ("Y11", "dynamics", "linear_drift", g_drift),
    ("Y12", "dynamics", "periodic_cycle", g_periodic),
    ("Z01", "control", "no_structure", g_white),
    ("Z02", "control", "no_structure", g_white),
    ("Z03", "control", "no_structure", g_walk),
    ("Z04", "control", "no_structure", g_const),
]
CONTROL_NOTE = {"Z01": "stationary white noise", "Z02": "stationary white noise", "Z03": "random walk",
                "Z04": "constant + noise"}


def build(set_no=1):
    items = []
    for j, (iid, kind, key, gen) in enumerate(ITEMS):
        rng = random.Random(f"r2|set{set_no}|{iid}")
        s = gen(rng)
        items.append(dict(id=iid, kind=kind, key=key, glyph=GLYPHS[j], cols=s["cols"], rows=s["rows"],
                          generator=gen.__name__, **({"control_note": CONTROL_NOTE[iid]} if iid in CONTROL_NOTE else {})))
    return dict(version=1, round=2, set=set_no, license="CC0-1.0", status="PROPOSED test material",
                note="16 items: 12 dynamics + 4 controls. Item text = glyph + column labels + numbers only.",
                items=items)


def fmt(v):
    if isinstance(v, int):
        return str(v)
    s = f"{v:.2f}"
    return "0.00" if s == "-0.00" else s


def item_text(it):
    """The exact text a packet shows for one item (no key, no id): the two columns in blocks of 10."""
    lines = [f"Glyph: {it['glyph']}"]
    for b in range(0, len(it["rows"]), 10):
        chunk = it["rows"][b:b + 10]
        for ci, name in enumerate(it["cols"]):
            lines.append(f"{name}: " + " ".join(fmt(r[ci]) for r in chunk))
    return "\n".join(lines)


if __name__ == "__main__":
    n = int(sys.argv[sys.argv.index("--set") + 1]) if "--set" in sys.argv else 1
    path = "stimuli_r2.json" if n == 1 else f"stimuli_r2_set{n}.json"
    json.dump(build(n), open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(path, len(build(n)["items"]))
