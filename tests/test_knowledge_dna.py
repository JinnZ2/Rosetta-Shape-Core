"""Tests for KnowledgeDNA — Backward Trace Engine."""
from rosetta_shape_core.knowledge_dna import (
    PROBES,
    NarrativeNode,
    example_broken_chain,
    example_structural_manipulation,
    example_traceable,
    trace_narrative,
)


def test_empty_chain():
    result = trace_narrative("Empty", [])
    assert result.verdict == "BROKEN_CHAIN"
    assert result.chain_length == 0
    assert "NO_DATA" in result.flags


def test_traceable_example():
    result = example_traceable()
    assert result.verdict == "TRACEABLE"
    assert result.provenance_intact is True
    assert result.chain_length == 2
    assert result.root_source_type == "primary"


def test_broken_chain_example():
    result = example_broken_chain()
    assert result.verdict == "BROKEN_CHAIN"
    assert result.provenance_intact is False
    assert "BROKEN_PROVENANCE" in result.flags
    assert "WEAK_ROOT" in result.flags


def test_structural_manipulation_example():
    result = example_structural_manipulation()
    assert result.verdict == "STRUCTURAL_MANIPULATION"
    assert result.symmetry_applied is False
    assert "ASYMMETRIC_APPLICATION" in result.flags
    assert "STRUCTURAL_MANIPULATION" in result.flags


def test_single_beneficiary_flag():
    chain = [
        NarrativeNode("Claim", source="A", source_type="primary",
                      data_basis="data", beneficiary="group_x"),
        NarrativeNode("Root", source="B", source_type="primary",
                      data_basis="data", beneficiary="group_x"),
    ]
    result = trace_narrative("Test", chain)
    assert "SINGLE_BENEFICIARY" in result.flags
    assert result.beneficiary_consistent is True


def test_weak_evidence():
    chain = [
        NarrativeNode("Claim with no data", source="A", source_type="secondary"),
        NarrativeNode("Another with no data", source="B", source_type="secondary"),
    ]
    result = trace_narrative("Test", chain)
    assert "WEAK_EVIDENCE_CHAIN" in result.flags
    assert result.details["evidence_ratio"] == 0.0


def test_probes_count():
    assert len(PROBES) == 6


def test_result_details():
    result = example_traceable()
    assert "provenance_ratio" in result.details
    assert "evidence_ratio" in result.details
    assert "unique_beneficiaries" in result.details
    assert "probes_applied" in result.details
