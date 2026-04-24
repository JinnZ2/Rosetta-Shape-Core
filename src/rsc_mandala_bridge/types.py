"""Basin contract — matches the shape established by the LID→Mandala bridge.

Defined locally rather than imported so RSC does not take a runtime
dependency on LID. The Mandala's Basin is a structural contract, not a
class identity: any module producing dataclasses with these fields can
feed the runtime.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional, Protocol, runtime_checkable


@dataclass(frozen=True)
class Substrate:
    """Identifies what a Basin is a projection of.

    `name` is the Mandala-facing dotted identifier (``shape.dodecahedron``,
    ``sensor.emotion.trust``). `lid_id` preserves the ontology-native ID
    (``SHAPE.DODECA``, ``EMO:TRUST``) so both frames remain visible. Both
    carry information — do not flatten to one or the other.
    """

    name: str
    family: str = "intelligence"
    lid_id: Optional[str] = None
    drill_path: tuple = ()


@dataclass
class Basin:
    """A relaxation target for the Mandala runtime.

    `signature` holds the cross-references that distinguish RSC basins from
    LID basins — explicit sensor/glyph/protocol bridges rather than heuristic
    string matching.
    """

    domain: str
    substrate: Substrate
    support: Any
    depth: float
    signature: dict = field(default_factory=dict)


@runtime_checkable
class DynamicsProjector(Protocol):
    """An object that turns an ontology entity dict into a Basin."""

    ontology_type: str

    def project(self, entity: dict) -> Basin: ...
