"""
KnowledgeDNA — Backward Trace Engine

Six probes on a narrative chain: provenance, source chain, root node,
beneficiary analysis, symmetry check, asymmetry detection.

Usage:
    python -m rosetta_shape_core.knowledge_dna --example
    python -m rosetta_shape_core.knowledge_dna --json
"""
from __future__ import annotations
import argparse, json, sys
from dataclasses import dataclass, field


# ── data structures ───────────────────────────────────────────────

@dataclass
class NarrativeNode:
    """A single node in the narrative chain."""
    claim: str
    source: str = ""       # who said it
    source_type: str = ""  # "primary", "secondary", "anecdotal", "institutional", "unknown"
    data_basis: str = ""   # what evidence backs it
    beneficiary: str = ""  # who benefits if this claim is accepted


@dataclass
class TraceResult:
    """Result of a KnowledgeDNA backward trace."""
    narrative: str
    chain: list[NarrativeNode]
    root_source_type: str       # type of the deepest source found
    provenance_intact: bool     # can we trace all the way back?
    chain_length: int
    beneficiary_consistent: bool  # does the same party benefit at every level?
    symmetry_applied: bool       # was the logic applied symmetrically?
    asymmetry_reason: str        # if not, why not
    verdict: str                 # "TRACEABLE" | "BROKEN_CHAIN" | "STRUCTURAL_MANIPULATION"
    flags: list[str]
    details: dict = field(default_factory=dict)


# ── probes ────────────────────────────────────────────────────────

PROBES = [
    {"id": "PROBE.PROVENANCE", "question": "Who introduced this framing?",
     "rosetta_parallel": "CORDYCEPS.HIDE_PROVENANCE", "family": "FAMILY.F03"},
    {"id": "PROBE.SOURCE_CHAIN", "question": "Where did they get the data?",
     "rosetta_parallel": "Referential integrity check", "family": "FAMILY.F14"},
    {"id": "PROBE.ROOT_NODE", "question": "What's the original source?",
     "rosetta_parallel": "Entity resolution — resolve_id()", "family": "FAMILY.F09"},
    {"id": "PROBE.BENEFICIARY", "question": "Who benefits from this narrative?",
     "rosetta_parallel": "MECON.DI — Distributional Inequality", "family": "FAMILY.F12"},
    {"id": "PROBE.SYMMETRY", "question": "Was the same logic applied symmetrically?",
     "rosetta_parallel": "Seed symmetry — octahedral balance", "family": "FAMILY.F19"},
    {"id": "PROBE.ASYMMETRY", "question": "If not — why not?",
     "rosetta_parallel": "SHADOW.BOUNDARY — equation boundary detection", "family": "FAMILY.F05"},
]


def trace_narrative(narrative: str, chain: list[NarrativeNode]) -> TraceResult:
    """Run a 6-probe KnowledgeDNA backward trace on a narrative chain.

    The chain should be ordered from surface (most recent claim)
    to root (original source), like unwinding a thread.
    """
    flags = []

    if not chain:
        return TraceResult(
            narrative=narrative, chain=[], root_source_type="unknown",
            provenance_intact=False, chain_length=0,
            beneficiary_consistent=False, symmetry_applied=False,
            asymmetry_reason="No chain provided",
            verdict="BROKEN_CHAIN", flags=["NO_DATA"],
            details={"note": "Empty narrative chain — nothing to trace"},
        )

    # Probe 1: Provenance — can we identify who introduced each framing?
    unknown_sources = sum(1 for n in chain if not n.source or n.source_type == "unknown")
    provenance_ratio = 1.0 - (unknown_sources / len(chain))
    provenance_intact = provenance_ratio >= 0.7
    if not provenance_intact:
        flags.append("BROKEN_PROVENANCE")

    # Probe 2: Source chain — is there data backing each claim?
    unsupported = sum(1 for n in chain if not n.data_basis)
    evidence_ratio = 1.0 - (unsupported / len(chain))
    if evidence_ratio < 0.5:
        flags.append("WEAK_EVIDENCE_CHAIN")

    # Probe 3: Root node — what's at the bottom of the chain?
    root = chain[-1]
    root_source_type = root.source_type or "unknown"
    if root_source_type in ("anecdotal", "unknown"):
        flags.append("WEAK_ROOT")

    # Probe 4: Beneficiary analysis — does the same party benefit at every level?
    beneficiaries = [n.beneficiary for n in chain if n.beneficiary]
    if beneficiaries:
        unique_beneficiaries = set(beneficiaries)
        beneficiary_consistent = len(unique_beneficiaries) <= 2
        if beneficiary_consistent and len(unique_beneficiaries) == 1:
            flags.append("SINGLE_BENEFICIARY")
    else:
        beneficiary_consistent = False  # can't determine

    # Probe 5: Symmetry — was the same logic applied to all groups?
    # Two checks: (a) explicit asymmetric language, (b) beneficiary/target mismatch
    symmetry_applied = True
    asymmetry_reason = ""
    asymmetry_keywords = (
        "only applies to", "except for", "doesn't apply to",
        "not for them", "different rules", "exempt", "special case",
        "doesn't count", "we're different", "rules don't apply",
    )
    for n in chain:
        claim_lower = n.claim.lower()
        if any(kw in claim_lower for kw in asymmetry_keywords):
            symmetry_applied = False
            asymmetry_reason = f"Asymmetric language: '{n.claim[:80]}'"
            flags.append("ASYMMETRIC_APPLICATION")
            break

    # Quantitative symmetry: if all beneficiaries are the same but the
    # root source was universal, the chain narrows from universal → tribal
    if symmetry_applied and beneficiaries:
        root_beneficiary = chain[-1].beneficiary.lower() if chain[-1].beneficiary else ""
        surface_beneficiary = chain[0].beneficiary.lower() if chain[0].beneficiary else ""
        if (root_beneficiary in ("universal", "general public", "everyone", "all")
                and surface_beneficiary
                and surface_beneficiary not in ("universal", "general public", "everyone", "all")):
            symmetry_applied = False
            asymmetry_reason = f"Chain narrows: root beneficiary '{root_beneficiary}' -> surface '{surface_beneficiary}'"
            flags.append("NARROWING_BENEFICIARY")

    # Probe 6: Asymmetry diagnosis — structural reason or tribal interest?
    if not symmetry_applied:
        # Check if asymmetry correlates with consistent beneficiary (tribal interest)
        if beneficiary_consistent:
            flags.append("STRUCTURAL_MANIPULATION")
        # Check if the data basis weakens as the chain moves toward the surface
        # (rationalization replaces evidence)
        evidence_by_depth = [bool(n.data_basis) for n in chain]
        if len(evidence_by_depth) >= 2:
            root_evidence = sum(evidence_by_depth[len(chain)//2:])
            surface_evidence = sum(evidence_by_depth[:len(chain)//2])
            if root_evidence > surface_evidence:
                flags.append("EVIDENCE_DECAY")

    # Verdict
    if "STRUCTURAL_MANIPULATION" in flags:
        verdict = "STRUCTURAL_MANIPULATION"
    elif not provenance_intact or "WEAK_ROOT" in flags:
        verdict = "BROKEN_CHAIN"
    else:
        verdict = "TRACEABLE"

    return TraceResult(
        narrative=narrative,
        chain=chain,
        root_source_type=root_source_type,
        provenance_intact=provenance_intact,
        chain_length=len(chain),
        beneficiary_consistent=beneficiary_consistent,
        symmetry_applied=symmetry_applied,
        asymmetry_reason=asymmetry_reason,
        verdict=verdict,
        flags=flags,
        details={
            "provenance_ratio": round(provenance_ratio, 3),
            "evidence_ratio": round(evidence_ratio, 3),
            "unique_beneficiaries": list(set(b for b in beneficiaries)) if beneficiaries else [],
            "probes_applied": len(PROBES),
        },
    )


# ── display ───────────────────────────────────────────────────────

VERDICT_GLYPHS = {
    "TRACEABLE": "✓",
    "BROKEN_CHAIN": "?",
    "STRUCTURAL_MANIPULATION": "✗",
}


def print_trace(result: TraceResult):
    """Display KnowledgeDNA trace results."""
    vg = VERDICT_GLYPHS.get(result.verdict, "?")

    print(f"\n{'='*60}")
    print(f"  KNOWLEDGE DNA — Backward Trace")
    print(f"{'='*60}")
    print(f"\n  Narrative: {result.narrative}")
    print(f"  Chain length: {result.chain_length}")

    # Show chain
    print(f"\n  ── Narrative Chain ──")
    for i, node in enumerate(result.chain):
        depth = "  " * i
        arrow = "→" if i < len(result.chain) - 1 else "⊙"
        src_type = f" [{node.source_type}]" if node.source_type else ""
        print(f"    {depth}{arrow} {node.claim[:70]}")
        if node.source:
            print(f"    {depth}  Source: {node.source}{src_type}")
        if node.data_basis:
            print(f"    {depth}  Evidence: {node.data_basis[:60]}")
        if node.beneficiary:
            print(f"    {depth}  Benefits: {node.beneficiary}")

    # Probes
    print(f"\n  ── Probe Results ──")
    print(f"    Provenance intact:     {'✓' if result.provenance_intact else '✗'}  ({result.details.get('provenance_ratio', 0):.0%})")
    print(f"    Evidence chain:        {result.details.get('evidence_ratio', 0):.0%}")
    print(f"    Root source type:      {result.root_source_type}")
    print(f"    Beneficiary consistent:{' ✓' if result.beneficiary_consistent else ' ✗'}")
    print(f"    Symmetry applied:      {'✓' if result.symmetry_applied else '✗'}")
    if result.asymmetry_reason:
        print(f"      Reason: {result.asymmetry_reason}")

    if result.flags:
        print(f"\n  ── Flags ──")
        for flag in result.flags:
            print(f"    ✗ {flag}")

    print(f"\n  ── Verdict ──")
    print(f"    {vg} {result.verdict}")

    print(f"\n{'='*60}\n")


# ── built-in examples ────────────────────────────────────────────

def example_traceable():
    """A narrative with intact provenance and symmetric application."""
    chain = [
        NarrativeNode(
            claim="Vaccine X reduces infection by 85%",
            source="Public health authority",
            source_type="institutional",
            data_basis="Phase 3 trial, 30000 participants, peer-reviewed",
            beneficiary="general public",
        ),
        NarrativeNode(
            claim="Clinical trial showed 85% efficacy",
            source="Research team at university",
            source_type="primary",
            data_basis="Double-blind RCT, published in medical journal",
            beneficiary="general public",
        ),
    ]
    return trace_narrative("Vaccine efficacy claim", chain)


def example_broken_chain():
    """A narrative where sources can't be traced back."""
    chain = [
        NarrativeNode(
            claim="This group is responsible for all our problems",
            source="Political figure",
            source_type="secondary",
            data_basis="",
            beneficiary="political movement",
        ),
        NarrativeNode(
            claim="People are saying they're dangerous",
            source="",
            source_type="unknown",
            data_basis="",
            beneficiary="political movement",
        ),
        NarrativeNode(
            claim="There was an incident once",
            source="",
            source_type="anecdotal",
            data_basis="Single unverified story",
            beneficiary="political movement",
        ),
    ]
    return trace_narrative("Scapegoating narrative", chain)


def example_structural_manipulation():
    """A narrative with clear asymmetric application benefiting one group."""
    chain = [
        NarrativeNode(
            claim="Our moral code only applies to believers, not outsiders",
            source="Religious authority",
            source_type="institutional",
            data_basis="Selective reading of text",
            beneficiary="in-group leadership",
        ),
        NarrativeNode(
            claim="The text says to love everyone, but this doesn't apply to enemies",
            source="Theological interpretation",
            source_type="secondary",
            data_basis="Cherry-picked verses, ignoring contradicting passages",
            beneficiary="in-group leadership",
        ),
        NarrativeNode(
            claim="Original text: love your neighbor as yourself",
            source="Scripture",
            source_type="primary",
            data_basis="Direct textual source",
            beneficiary="universal",
        ),
    ]
    return trace_narrative("Selective moral application", chain)


# ── CLI ───────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(
        description="KnowledgeDNA — Backward Trace Engine",
        epilog="Trace the thread. Follow the money. Check the symmetry.",
    )
    ap.add_argument("--json", action="store_true", help="Output as JSON")
    ap.add_argument("--example", action="store_true",
                    help="Run built-in examples (traceable, broken chain, structural manipulation)")
    args = ap.parse_args()

    if not args.example:
        print("\n  KnowledgeDNA — Backward Trace Engine")
        print("  Use --example to see built-in examples")
        print("  Use as library: from rosetta_shape_core.knowledge_dna import trace_narrative\n")
        return

    examples = [
        ("Example 1: Traceable Narrative", example_traceable),
        ("Example 2: Broken Chain", example_broken_chain),
        ("Example 3: Structural Manipulation", example_structural_manipulation),
    ]

    for title, fn in examples:
        print("\n" + "─" * 60)
        print(f"  {title}")
        print("─" * 60)
        result = fn()
        if args.json:
            print(json.dumps({
                "narrative": result.narrative,
                "verdict": result.verdict,
                "chain_length": result.chain_length,
                "provenance_intact": result.provenance_intact,
                "symmetry_applied": result.symmetry_applied,
                "flags": result.flags,
            }, indent=2))
        else:
            print_trace(result)


if __name__ == "__main__":
    sys.exit(main())
