"""Runs the scope-stamp selftest (tests_scope_stamp/score_scope.py) and checks the packets."""
import importlib.util
from pathlib import Path

SCORE = Path(__file__).resolve().parent.parent / "tests_scope_stamp" / "score_scope.py"


def _load():
    spec = importlib.util.spec_from_file_location("scope_stamp_score", SCORE)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_scope_selftest():
    assert _load().selftest()


def test_scope_pins_hold():
    _load().check_pins()


def test_scope_packets_and_pilot_match():
    mod = _load()
    key = mod.json.load(open(mod.KEYFILE))
    assert sorted(k["condition"] for k in key.values()) == ["A", "S"]
    pilot = Path(mod.PILOT).read_text(encoding="utf-8")
    for code, k in key.items():
        got, order, want = mod.packet(1, k["condition"], mod.items(), mod.method_s())
        assert got == code and order == k["order"]
        assert (Path(mod.PROMPTS) / f"{code}.txt").read_text(encoding="utf-8") == want
        assert want.rstrip() in pilot
