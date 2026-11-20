"""Runs the round-2 bin-landing selftest (tests_bin_landing_r2/score_r2.py) and checks the packets."""
import importlib.util
from pathlib import Path

SCORE = Path(__file__).resolve().parent.parent / "tests_bin_landing_r2" / "score_r2.py"


def _load():
    spec = importlib.util.spec_from_file_location("bin_landing_score_r2", SCORE)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_r2_selftest():
    assert _load().selftest()


def test_r2_pins_hold():
    _load().check_pins()  # PREREG_R2.md, gen_r2.py, both stimuli sets, round-1 PREREG + amendment 1


def test_r2_packets_match_generator():
    mod = _load()
    key = mod.json.load(open(mod.KEYFILE))
    assert len(key) == 6 and sorted({k["set"] for k in key.values()}) == [1, 2]
    ctx = mod.contexts()
    for code, k in key.items():
        txt = (Path(mod.PROMPTS) / f"{code}.txt").read_text(encoding="utf-8")
        got_code, order, want = mod.packet(k["set"], k["condition"], mod.stimuli(k["set"]), ctx)
        assert got_code == code and order == k["order"] and txt == want


def test_r2_pilot_holds_the_three_set1_packets_verbatim():
    mod = _load()
    pilot = Path(mod.PILOT).read_text(encoding="utf-8")
    ctx = mod.contexts()
    for c in mod.CONDITIONS:
        _, _, txt = mod.packet(1, c, mod.stimuli(1), ctx)
        assert txt.rstrip() in pilot
    assert pilot.count("===== PACKET") == 3
