"""Runs the bin-landing scorer's planted selftest (tests_bin_landing/score.py)."""
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


def test_packets_match_pinned_inputs():
    mod = _load()
    mod.check_pins()
    key = mod.json.load(open(mod.KEYFILE))
    assert len(key) == 18
    for code, k in key.items():
        txt = (Path(mod.PROMPTS) / f"{code}.txt").read_text(encoding="utf-8")
        _, order, want = mod.packet(k["set"], k["condition"], k["style"], mod.stimuli(),
                                    Path(mod.METHOD).read_text(encoding="utf-8"))
        assert order == k["order"] and txt == want
