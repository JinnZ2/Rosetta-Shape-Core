"""Runs the bin-landing scorer's planted selftest (tests_bin_landing/score.py) and checks the packets."""
import importlib.util
from pathlib import Path

SCORE = Path(__file__).resolve().parent.parent / "tests_bin_landing" / "score.py"


def _load():
    spec = importlib.util.spec_from_file_location("bin_landing_score", SCORE)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_bin_landing_selftest():
    assert _load().selftest()


def test_pins_hold():
    _load().check_pins()  # stimuli.json, GLYPH_METHOD.md (PREREG) and PREREG_AMENDMENT_1.md


def test_packets_match_generator():
    mod = _load()
    key = mod.json.load(open(mod.KEYFILE))
    live = [c for c, k in key.items() if not k.get("retired")]
    retired = [c for c, k in key.items() if k.get("retired")]
    assert len(live) == 27 and len(retired) == 9
    assert sorted({key[c]["condition"] for c in live}) == ["A", "C", "E"]
    assert {key[c]["condition"] for c in retired} == {"B"}
    ctx, stim = mod.contexts(), mod.stimuli()
    for code, k in key.items():
        folder = Path(mod.RETIRED if k.get("retired") else mod.PROMPTS)
        txt = (folder / f"{code}.txt").read_text(encoding="utf-8")
        _, order, want = mod.packet(k["set"], k["condition"], k["style"], stim, ctx)
        assert order == k["order"] and txt == want


def test_pilot_lists_the_nine_shape_packets():
    mod = _load()
    key = mod.json.load(open(mod.KEYFILE))
    want = sorted(c for c, k in key.items() if not k.get("retired") and k["style"] == "SHAPE")
    got = sorted(line.split()[0] for line in Path(mod.PILOT).read_text().splitlines() if line.startswith("S"))
    assert got == want and len(got) == 9
