"""Worked example: RSC → Mandala Basin projection.

Run this after installing the package (``pip install -e .``) to see:

  * the per-projector basin counts the Mandala runtime will consume,
  * the dodecahedron's cross-reference signature (section 8 of the
    briefing — sensor, glyph, and protocol links the LID-only basin
    cannot carry),
  * the physics_check annotation attached to every shape basin,
  * the emergent rule basins (the generative layer that distinguishes
    RSC from a static ontology).

Prints a compact report; no side effects.
"""

from __future__ import annotations

import json

from rsc_mandala_bridge import build_basins


def _show_shape_basin(basins, shape_id: str) -> None:
    match = [b for b in basins if b.substrate.lid_id == shape_id]
    if not match:
        print(f"  (no basin for {shape_id})")
        return
    b = match[0]
    print(f"  substrate.name:  {b.substrate.name}")
    print(f"  substrate.lid_id:{b.substrate.lid_id}")
    print(f"  domain:          {b.domain}")
    print(f"  support:         {b.support}")
    print(f"  depth:           {b.depth}")
    print("  signature cross-refs:")
    for key in ("families", "principles", "bridge_sensors",
                "bridge_glyphs", "bridge_protocols", "bridge_defenses"):
        if b.signature.get(key):
            print(f"    {key:18}{b.signature[key]}")
    pc = b.signature.get("physics_check")
    if pc:
        print("  physics_check:")
        for k, v in pc.items():
            print(f"    {k:20}{v}")


def _show_rule_basins(basins) -> None:
    rules = [b for b in basins if b.domain == "rule_expansion"]
    print(f"  {len(rules)} rule basins emitted:")
    for b in rules:
        args = b.signature.get("rule_args") or []
        print(f"    {b.substrate.lid_id:<30} <- {b.signature['rule_op']:<10} {args}")


def _show_mandala_atlas(basins) -> None:
    mandala = [b for b in basins if (b.substrate.lid_id or "").startswith("MANDALA:")]
    glyphs = [b for b in basins if b.substrate.name.startswith("glyph.mandala")]
    print(f"  {len(mandala)} canonical mandala-atlas basins (states, problems, sensors)")
    print(f"  {len(glyphs)} mandala-glyph basins (state / problem / energy / structural)")


def main() -> int:
    report = build_basins()
    print("=" * 60)
    print("RSC → Mandala basin projection")
    print("=" * 60)
    print(json.dumps({
        "shape_basins":     report.shape_basin_count,
        "fieldlink_basins": report.fieldlink_basin_count,
        "rule_basins":      report.rule_basin_count,
        "total":            len(report.basins),
        "physics_checked":  report.physics_checked,
        "atlas_usable":     report.staleness.usable,
        "recommend_pull":   report.staleness.recommend_pull,
        "rule_warnings":    report.rule_warnings,
        "schema_errors":    report.schema_errors,
    }, indent=2))

    print("\n--- Briefing §8 worked example: SHAPE.DODECA ---")
    _show_shape_basin(report.basins, "SHAPE.DODECA")

    print("\n--- Generative layer: rule basins ---")
    _show_rule_basins(report.basins)

    print("\n--- Direct mandala-atlas walk ---")
    _show_mandala_atlas(report.basins)

    if report.staleness.warnings:
        print("\nStaleness warnings:")
        for w in report.staleness.warnings:
            print(f"  - {w}")

    return 0 if report.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
