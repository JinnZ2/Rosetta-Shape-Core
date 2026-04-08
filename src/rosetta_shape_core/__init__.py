"""Rosetta-Shape-Core — symbolic ontology and rules engine."""

from rosetta_shape_core.explore import (
    RosettaGraph,
    home_base,
    discover,
    check_merge,
    compute_seed_state,
    hunt_shadows,
    map_internal_environment,
)
from rosetta_shape_core.constraint_agent import ConstraintAgent
from rosetta_shape_core.narrative_physics import analyze_consistency
from rosetta_shape_core.knowledge_dna import trace_narrative
from rosetta_shape_core.first_principles_audit import audit_function, full_audit, generate_report
from rosetta_shape_core.octahedral_session_cache import SessionCache, OctState
from rosetta_shape_core.octa_triple import OctaTriple, OctaToken

__all__ = [
    "RosettaGraph",
    "home_base",
    "discover",
    "check_merge",
    "compute_seed_state",
    "hunt_shadows",
    "map_internal_environment",
    "ConstraintAgent",
    "analyze_consistency",
    "trace_narrative",
    "audit_function",
    "full_audit",
    "generate_report",
    "SessionCache",
    "OctState",
    "OctaTriple",
    "OctaToken",
]
