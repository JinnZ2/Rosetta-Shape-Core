"""RuleBasinExpander — the generative layer.

``rules/expand.jsonl`` expresses transformations between ontology entities:
``ALIGN ANIMAL.BEE CONST.PHI -> CAP.HEX_OPTIMIZATION`` (gated by
``CAP.SWARM_COORDINATION``). This expander treats each satisfiable rule as
a Basin generator: when all rule args are present in the available basin
set and the guard caps are satisfied, it emits a Basin for the rule's
``then`` target.

This is what distinguishes RSC from a static ontology in the Mandala
stack — LID basins only describe entities that exist; RSC basins can
include entities that emerge from interactions.
"""

from __future__ import annotations

import json
import pathlib
from typing import Iterable, List, Optional, Set

from rsc_mandala_bridge._paths import rsc_root as _default_root
from rsc_mandala_bridge.types import Basin, Substrate

_CORE_NAMESPACES = {
    "ANIMAL", "PLANT", "MICROBE", "CRYSTAL",
    "GEOM", "STRUCT", "FIELD", "CONST", "TEMP",
    "PROTO", "CAP", "SHAPE", "EMOTION", "DEFENSE", "REGEN",
}


class RuleBasinExpander:
    ontology_type = "rule_expansion"

    def __init__(self, rsc_root: Optional[pathlib.Path] = None):
        self.root = pathlib.Path(rsc_root) if rsc_root is not None else _default_root()

    def expand(
        self,
        available_basins: Iterable[Basin],
        ambient_capabilities: Optional[Iterable[str]] = None,
    ) -> List[Basin]:
        """Fire every rule whose preconditions are met and emit a Basin per result.

        ``available_basins`` supplies the entity IDs that exist in the
        current Mandala frame (via their ``substrate.lid_id``). Entities
        from ``ontology/*.json`` are also consulted for capability guards —
        a rule gated on ``CAP.SWARM_COORDINATION`` fires if either the
        subject entity declares that capability or it appears in
        ``ambient_capabilities``.
        """
        rules = self._load_rules()
        entity_caps = self._load_entity_capabilities()
        available_ids = self._collect_ids(available_basins)
        ambient = set(ambient_capabilities or [])

        # Rules can cascade: a fired rule's output becomes an input for later
        # rules. Iterate to fixed point so we do not miss transitive basins.
        produced: dict[str, Basin] = {}
        fired_signatures: set[tuple] = set()

        for _ in range(_MAX_CASCADE_DEPTH):
            new_this_pass = 0
            for rule in rules:
                key = _rule_signature(rule)
                if key in fired_signatures:
                    continue
                when = rule.get("when") or {}
                op = when.get("op")
                args = list(when.get("args") or [])
                target = rule.get("then")
                if not op or not target or not args:
                    continue
                if not all(a in available_ids for a in args):
                    continue
                if not _guard_satisfied(rule, args, entity_caps, ambient, available_ids):
                    continue

                basin = _rule_basin(rule, op, args, target)
                produced[target] = basin
                available_ids.add(target)
                fired_signatures.add(key)
                new_this_pass += 1
            if new_this_pass == 0:
                break

        return list(produced.values())

    # ----------------------------------------------------------------- loaders

    def _load_rules(self) -> list[dict]:
        path = self.root / "rules" / "expand.jsonl"
        if not path.is_file():
            return []
        rules: list[dict] = []
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line:
                rules.append(json.loads(line))
        return sorted(rules, key=lambda r: -r.get("priority", 0))

    def _load_entity_capabilities(self) -> dict:
        onto_dir = self.root / "ontology"
        if not onto_dir.is_dir():
            return {}
        caps: dict[str, set] = {}
        for path in sorted(onto_dir.glob("*.json")):
            if path.name.startswith("_"):
                continue
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                continue
            for entity in data.get("entities", []) or []:
                eid = entity.get("id")
                if not eid:
                    continue
                caps[eid] = set(entity.get("capabilities", []) or [])
        return caps

    def _collect_ids(self, basins: Iterable[Basin]) -> Set[str]:
        """Extract RSC-style dotted IDs from a basin stream.

        Rules reference entities by their canonical dotted ID. Colon-style
        cross-ontology IDs (EMO:TRUST) and substrate names are ignored
        here — the rule engine operates inside the RSC namespace.
        """
        ids: set[str] = set()
        for basin in basins:
            lid = basin.substrate.lid_id or ""
            if _is_rsc_id(lid):
                ids.add(lid)
        # Rules can also reference entities from ontology/ directly, which
        # may not yet have been projected into basins. Seed the ID set from
        # the full entity catalog so rules that depend on e.g. ANIMAL.BEE
        # can fire even when no animal basin has been emitted.
        ids.update(self._load_entity_capabilities().keys())
        return ids


def _is_rsc_id(candidate: str) -> bool:
    if "." not in candidate:
        return False
    head = candidate.split(".", 1)[0]
    return head in _CORE_NAMESPACES


def _guard_satisfied(
    rule: dict,
    args: list,
    entity_caps: dict,
    ambient: set,
    available_ids: set,
) -> bool:
    guard = rule.get("guard") or {}
    required = set(guard.get("requires", []) or [])
    if not required:
        return True
    subj = args[0] if args else ""
    subj_caps = entity_caps.get(subj, set())
    satisfied = subj_caps | ambient | {cap for cap in required if cap in available_ids}
    return required.issubset(satisfied)


def _rule_basin(rule: dict, op: str, args: list, target: str) -> Basin:
    substrate_name = _substrate_name_for_target(target)
    substrate = Substrate(
        name=substrate_name,
        family="emergent",
        lid_id=target,
        drill_path=tuple(args),
    )
    return Basin(
        domain="rule_expansion",
        substrate=substrate,
        support=(op, tuple(args), target),
        depth=round(0.4 + 0.03 * rule.get("priority", 0), 3),
        signature={
            "rule_op": op,
            "rule_args": list(args),
            "rule_target": target,
            "priority": rule.get("priority", 0),
            "why": rule.get("why"),
            "guard": rule.get("guard"),
            "provenance": rule.get("provenance"),
            "generated_from": list(args),
        },
    )


def _substrate_name_for_target(target: str) -> str:
    if "." in target:
        head, tail = target.split(".", 1)
        return f"{head.lower()}.{tail.lower()}"
    return target.lower()


def _rule_signature(rule: dict) -> tuple:
    when = rule.get("when") or {}
    return (when.get("op"), tuple(when.get("args") or []), rule.get("then"))


_MAX_CASCADE_DEPTH = 8
