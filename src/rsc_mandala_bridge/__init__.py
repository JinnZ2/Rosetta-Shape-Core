"""rsc_mandala_bridge — project Rosetta-Shape-Core into Mandala Basins.

RSC is an ontology hub, not a peer to LID. It has already done the work of
relating shapes to sensors to glyphs to protocols via bridges/ and the
fieldlink atlas. This package adapts those curated structures into the
Basin contract expected by the Mandala runtime.

Four projector families compose into `build_basins`:

    ShapeProjector        shapes/*.json                  -> shape basins
    FieldlinkProjector    bridges/rosetta-bridges.json + -> cross-ontology basins
                          .fieldlink/merge_stage/ (or
                          atlas/remote/ fallback)
    RuleBasinExpander     rules/expand.jsonl             -> generative basins

`build_basins()` runs all three and returns a list[Basin] ready for the
Mandala. The generative layer is what distinguishes RSC from a static
ontology: each rule that fires produces a new Basin from the interaction
of existing ones.
"""

from rsc_mandala_bridge.bridge import BridgeReport, build_basins
from rsc_mandala_bridge.fieldlink_projector import FieldlinkProjector
from rsc_mandala_bridge.physics_check import physics_check_basins
from rsc_mandala_bridge.rule_expander import RuleBasinExpander
from rsc_mandala_bridge.schema_check import (
    BasinSchemaError,
    validate_basin_against_schema,
)
from rsc_mandala_bridge.shape_projector import ShapeProjector
from rsc_mandala_bridge.staleness import StalenessReport, check_atlas_staleness
from rsc_mandala_bridge.types import Basin, DynamicsProjector, Substrate

__all__ = [
    "Basin",
    "BasinSchemaError",
    "BridgeReport",
    "DynamicsProjector",
    "FieldlinkProjector",
    "RuleBasinExpander",
    "ShapeProjector",
    "StalenessReport",
    "Substrate",
    "build_basins",
    "check_atlas_staleness",
    "physics_check_basins",
    "validate_basin_against_schema",
]
