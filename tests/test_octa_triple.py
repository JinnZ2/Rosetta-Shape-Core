"""Tests for octahedral triple encoder."""
import pytest
from rosetta_shape_core.octa_triple import OctaTriple, OctaToken, GLYPHS


@pytest.fixture
def ot():
    return OctaTriple()


# ------------------------------------------------------------------
# Codebook auto-build
# ------------------------------------------------------------------

class TestCodebook:
    def test_codebook_populated_from_rules(self, ot):
        assert ot.codebook_size > 0

    def test_codebook_max_8(self, ot):
        assert ot.codebook_size <= 8

    def test_all_states_in_range(self, ot):
        for row in ot.codebook_table():
            assert 0 <= row["state"] <= 7

    def test_bits_match_state(self, ot):
        for row in ot.codebook_table():
            assert row["bits"] == f"{row['state']:03b}"

    def test_glyphs_match_state(self, ot):
        for row in ot.codebook_table():
            assert row["glyph"] == GLYPHS[row["state"]]

    def test_phi_coherence_in_range(self, ot):
        for row in ot.codebook_table():
            assert 0.0 <= row["phi_coherence"] <= 1.0

    def test_triples_are_nonempty(self, ot):
        for row in ot.codebook_table():
            assert len(row["triple"]) >= 1


# ------------------------------------------------------------------
# Encode / decode roundtrip
# ------------------------------------------------------------------

class TestRoundtrip:
    def test_encode_known_triple(self, ot):
        table = ot.codebook_table()
        if not table:
            pytest.skip("no codebook entries")
        row = table[0]
        triple = tuple(row["triple"])
        token = ot.encode(*triple)
        assert token.state == row["state"]
        assert token.glyph == row["glyph"]
        assert token.triple == triple

    def test_decode_by_state(self, ot):
        table = ot.codebook_table()
        if not table:
            pytest.skip("no codebook entries")
        row = table[0]
        decoded = ot.decode(row["state"])
        assert decoded is not None
        assert decoded.triple == tuple(row["triple"])

    def test_decode_by_glyph(self, ot):
        table = ot.codebook_table()
        if not table:
            pytest.skip("no codebook entries")
        row = table[0]
        decoded = ot.decode(row["glyph"])
        assert decoded is not None
        assert decoded.state == row["state"]

    def test_full_roundtrip_all_entries(self, ot):
        for row in ot.codebook_table():
            triple = tuple(row["triple"])
            encoded = ot.encode(*triple)
            decoded = ot.decode(encoded.glyph)
            assert decoded is not None
            assert decoded.triple == triple
            assert decoded.state == encoded.state

    def test_decode_unknown_glyph_returns_none(self, ot):
        assert ot.decode("∅") is None

    def test_decode_unregistered_state_returns_none(self, ot):
        # find an unregistered state
        registered = {r["state"] for r in ot.codebook_table()}
        for i in range(8):
            if i not in registered:
                assert ot.decode(i) is None
                return
        pytest.skip("all 8 states registered")


# ------------------------------------------------------------------
# Custom registration
# ------------------------------------------------------------------

class TestRegister:
    def test_register_and_retrieve(self, ot):
        triple = ("CUSTOM", "FOO", "BAR")
        ot.register(triple, 7)
        token = ot.encode(*triple)
        assert token.state == 7
        assert token.glyph == "⊜"
        decoded = ot.decode(7)
        assert decoded is not None
        assert decoded.triple == triple

    def test_register_invalid_state(self, ot):
        with pytest.raises(ValueError):
            ot.register(("A", "B", "C"), 8)

    def test_register_negative_state(self, ot):
        with pytest.raises(ValueError):
            ot.register(("A", "B", "C"), -1)


# ------------------------------------------------------------------
# Axis classification (lossy fallback)
# ------------------------------------------------------------------

class TestClassify:
    def test_structural_geometric_capability(self, ot):
        token = ot.encode("EXPAND", "SHAPE.OCTA", "CAP.SOMETHING")
        assert token.bits[0] == "1"  # bit 2 (cap) → MSB in vertex_bits
        # structural → bit 0, geometric → bit 1, cap → bit 2
        assert token.state == 0b111  # all three axes +

    def test_non_structural_non_geometric_non_cap(self, ot):
        token = ot.encode("ALIGN", "ANIMAL.BEE", "ANIMAL.ANT")
        assert token.state == 0b000

    def test_single_token_pads(self, ot):
        # single unregistered token → classifies with 2 empty tokens
        token = ot.encode("SHAPE.TETRA")
        assert isinstance(token, OctaToken)
        assert 0 <= token.state <= 7

    def test_two_tokens(self, ot):
        token = ot.encode("EXPAND", "CONST.PHI")
        assert isinstance(token, OctaToken)


# ------------------------------------------------------------------
# Adjacency (Gray code)
# ------------------------------------------------------------------

class TestAdjacency:
    def test_adjacent_count(self, ot):
        for s in range(8):
            assert len(ot.adjacent(s)) == 3

    def test_adjacent_single_bit_flip(self, ot):
        for s in range(8):
            for a in ot.adjacent(s):
                diff = s ^ a
                assert diff in (1, 2, 4), f"{s} -> {a} flips more than one bit"

    def test_adjacency_symmetric(self, ot):
        for s in range(8):
            for a in ot.adjacent(s):
                assert s in ot.adjacent(a)

    def test_ground_state_neighbors(self, ot):
        assert sorted(ot.adjacent(0)) == [1, 2, 4]


# ------------------------------------------------------------------
# OctaToken properties
# ------------------------------------------------------------------

class TestOctaToken:
    def test_frozen(self):
        t = OctaToken(state=0, bits="000", glyph="⊕", phi_coherence=0.97,
                      triple=("A",))
        with pytest.raises(AttributeError):
            t.state = 1

    def test_equality(self):
        a = OctaToken(0, "000", "⊕", 0.97, ("X",))
        b = OctaToken(0, "000", "⊕", 0.97, ("X",))
        assert a == b

    def test_hash(self):
        a = OctaToken(0, "000", "⊕", 0.97, ("X",))
        b = OctaToken(0, "000", "⊕", 0.97, ("X",))
        assert hash(a) == hash(b)
        assert len({a, b}) == 1
