"""RuleBasinExpander — the generative layer is the whole point."""

from __future__ import annotations

import pathlib

from rsc_mandala_bridge.rule_expander import RuleBasinExpander
from rsc_mandala_bridge.shape_projector import ShapeProjector
from rsc_mandala_bridge.types import Basin, Substrate


def test_synthetic_ungated_rule_fires(synthetic_rsc: pathlib.Path):
    shape_basins = ShapeProjector(synthetic_rsc).project_all()
    rule_basins = RuleBasinExpander(synthetic_rsc).expand(shape_basins)

    produced = {b.substrate.lid_id for b in rule_basins}
    assert "CAP.DEMO_ACTIVATION" in produced


def test_synthetic_guarded_rule_cascades(synthetic_rsc: pathlib.Path):
    """The second rule is gated on the first rule's output; both must fire."""
    shape_basins = ShapeProjector(synthetic_rsc).project_all()
    rule_basins = RuleBasinExpander(synthetic_rsc).expand(shape_basins)

    produced = {b.substrate.lid_id for b in rule_basins}
    assert "CAP.DEMO_GATED" in produced, f"guarded cascade did not fire: {produced}"


def test_guard_fails_when_capability_missing(synthetic_rsc: pathlib.Path):
    """With only CAP.DEMO_ACTIVATION stripped, the gated rule cannot fire."""
    # Rewrite ontology so CAP.DEMO_ACTIVATION has no ambient declaration,
    # and pass a basin set that excludes shapes so no EXPAND fires.
    import json
    onto = synthetic_rsc / "ontology" / "entities.json"
    data = json.loads(onto.read_text(encoding="utf-8"))
    data["entities"] = [e for e in data["entities"] if e["id"] != "CAP.DEMO_ACTIVATION"]
    onto.write_text(json.dumps(data), encoding="utf-8")

    # Provide ALIGN args but not EXPAND — so the ungated rule won't fire and
    # the gated one has no satisfied precondition capability either.
    phi_only = [Basin(
        domain="test",
        substrate=Substrate(name="const.phi", lid_id="CONST.PHI"),
        support=(), depth=0.0,
    ), Basin(
        domain="test",
        substrate=Substrate(name="shape.tiny", lid_id="SHAPE.TINY"),
        support=(), depth=0.0,
    )]

    # Remove the ungated EXPAND rule so only the gated one remains.
    rules = synthetic_rsc / "rules" / "expand.jsonl"
    lines = rules.read_text(encoding="utf-8").splitlines()
    rules.write_text("\n".join(ln for ln in lines if '"ALIGN"' in ln) + "\n", encoding="utf-8")

    rule_basins = RuleBasinExpander(synthetic_rsc).expand(phi_only)
    produced = {b.substrate.lid_id for b in rule_basins}
    assert "CAP.DEMO_GATED" not in produced


def test_real_repo_rule_basins_are_generative():
    real_root = pathlib.Path(__file__).resolve().parents[2]
    shape_basins = ShapeProjector(real_root).project_all()
    rule_basins = RuleBasinExpander(real_root).expand(shape_basins)

    produced = {b.substrate.lid_id for b in rule_basins}
    # The BEE x PHI rule is guarded on CAP.SWARM_COORDINATION which
    # ANIMAL.BEE carries; it should fire against the real repo.
    assert "CAP.HEX_OPTIMIZATION" in produced
    # The OCTA encoding rules should also fire.
    assert {"CAP.OCTAHEDRAL_STATE", "CAP.GEOMETRIC_ENCODING"}.issubset(produced)


def test_cascade_warning_fires_when_depth_cap_hit(tmp_path: pathlib.Path):
    """A chain of N > MAX_CASCADE_DEPTH rules should emit a warning."""
    from rsc_mandala_bridge.rule_expander import _MAX_CASCADE_DEPTH, RuleBasinExpander
    from rsc_mandala_bridge.types import Basin, Substrate

    # Minimum layout: rules dir + ontology dir.
    (tmp_path / "ontology").mkdir()
    rules_dir = tmp_path / "rules"
    rules_dir.mkdir()

    # Build a strict chain: SHAPE.CHAIN_0 → CAP.CHAIN_1 → CAP.CHAIN_2 → ...
    # longer than the cascade cap so the fixed point is never reached.
    # Write rules in REVERSE dependency order so each pass only fires one —
    # rules for step N are iterated before step N-1 exists, so they can't
    # all cascade inside a single pass.
    total = _MAX_CASCADE_DEPTH + 3
    lines = []
    for i in range(total, 0, -1):
        prev = "SHAPE.CHAIN_0" if i == 1 else f"CAP.CHAIN_{i - 1}"
        lines.append(
            f'{{"when":{{"op":"EXPAND","args":["{prev}"]}},"then":"CAP.CHAIN_{i}","priority":1}}'
        )
    (rules_dir / "expand.jsonl").write_text("\n".join(lines) + "\n", encoding="utf-8")

    seed = [Basin(
        domain="test",
        substrate=Substrate(name="shape.chain_0", lid_id="SHAPE.CHAIN_0"),
        support=(), depth=0.0,
    )]
    expander = RuleBasinExpander(tmp_path)
    produced = expander.expand(seed)

    assert len(produced) == _MAX_CASCADE_DEPTH, (
        f"expected exactly {_MAX_CASCADE_DEPTH} basins before cap, got {len(produced)}"
    )
    assert expander.last_warnings, "cap was hit but no warning was emitted"
    assert "did not converge" in expander.last_warnings[0]


def test_cascade_warning_absent_when_converged():
    real_root = pathlib.Path(__file__).resolve().parents[2]
    from rsc_mandala_bridge.rule_expander import RuleBasinExpander
    from rsc_mandala_bridge.shape_projector import ShapeProjector

    expander = RuleBasinExpander(real_root)
    expander.expand(ShapeProjector(real_root).project_all())
    assert expander.last_warnings == []


def test_rule_basin_signature_preserves_why_and_priority():
    real_root = pathlib.Path(__file__).resolve().parents[2]
    shape_basins = ShapeProjector(real_root).project_all()
    rule_basins = RuleBasinExpander(real_root).expand(shape_basins)

    match = [b for b in rule_basins if b.substrate.lid_id == "CAP.OCTAHEDRAL_STATE"][0]
    assert match.signature["rule_op"] == "EXPAND"
    assert match.signature["rule_args"] == ["SHAPE.OCTA"]
    assert match.signature["priority"] == 9
    assert match.signature["why"]
    assert match.domain == "rule_expansion"
    assert match.substrate.family == "emergent"
