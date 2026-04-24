"""Top-level bridge entry point — compose all four projectors into basins.

Typical usage from the Mandala runtime::

    from rsc_mandala_bridge import build_basins
    report = build_basins()
    runtime.feed(report.basins)

The returned :class:`BridgeReport` also carries staleness warnings and
schema-check diagnostics so the caller can decide whether to fail loud or
continue with the committed atlas.
"""

from __future__ import annotations

import pathlib
from dataclasses import dataclass, field
from typing import Iterable, List, Optional

from rsc_mandala_bridge._paths import rsc_root as _default_root
from rsc_mandala_bridge.fieldlink_projector import FieldlinkProjector
from rsc_mandala_bridge.rule_expander import RuleBasinExpander
from rsc_mandala_bridge.schema_check import (
    BasinSchemaError,
    validate_basin_against_schema,
)
from rsc_mandala_bridge.shape_projector import ShapeProjector
from rsc_mandala_bridge.staleness import StalenessReport, check_atlas_staleness
from rsc_mandala_bridge.types import Basin


@dataclass
class BridgeReport:
    basins: List[Basin]
    staleness: StalenessReport
    shape_basin_count: int = 0
    fieldlink_basin_count: int = 0
    rule_basin_count: int = 0
    schema_errors: List[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.schema_errors and self.staleness.usable


def build_basins(
    rsc_root: Optional[pathlib.Path] = None,
    *,
    validate_schemas: bool = True,
    ambient_capabilities: Optional[Iterable[str]] = None,
) -> BridgeReport:
    """Run the shape, fieldlink, and rule projectors and bundle the result.

    Parameters
    ----------
    rsc_root:
        Override the default repo root. Handy for tests with synthetic
        fixtures.
    validate_schemas:
        When True (default), every shape basin is round-tripped through
        ``schema/shape.schema.json``. Errors are collected into the report
        rather than raised so a partial failure doesn't mask the rest.
    ambient_capabilities:
        Extra capability IDs to pass to the rule expander's guards. Used
        when the runtime wants to simulate "what if this capability were
        already available?" expansions.
    """
    root = pathlib.Path(rsc_root) if rsc_root is not None else _default_root()
    staleness = check_atlas_staleness(root)

    shape_projector = ShapeProjector(root)
    fieldlink_projector = FieldlinkProjector(root)
    rule_expander = RuleBasinExpander(root)

    shape_basins = shape_projector.project_all()
    fieldlink_basins = fieldlink_projector.project_all()
    rule_basins = rule_expander.expand(
        shape_basins + fieldlink_basins,
        ambient_capabilities=ambient_capabilities,
    )

    basins = shape_basins + fieldlink_basins + rule_basins

    schema_errors: list[str] = []
    if validate_schemas:
        for basin in basins:
            try:
                validate_basin_against_schema(basin, root)
            except BasinSchemaError as exc:
                schema_errors.append(str(exc))

    return BridgeReport(
        basins=basins,
        staleness=staleness,
        shape_basin_count=len(shape_basins),
        fieldlink_basin_count=len(fieldlink_basins),
        rule_basin_count=len(rule_basins),
        schema_errors=schema_errors,
    )


def main() -> int:
    """CLI entry: ``python -m rsc_mandala_bridge`` prints a summary."""
    import json as _json

    report = build_basins()
    print(
        _json.dumps(
            {
                "shape_basins": report.shape_basin_count,
                "fieldlink_basins": report.fieldlink_basin_count,
                "rule_basins": report.rule_basin_count,
                "total": len(report.basins),
                "atlas_usable": report.staleness.usable,
                "recommend_pull": report.staleness.recommend_pull,
                "warnings": report.staleness.warnings,
                "schema_errors": report.schema_errors,
            },
            indent=2,
        )
    )
    return 0 if report.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
