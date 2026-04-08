"""Octahedral triple encoder — compress 3 tokens into 1 octahedral state.

Two modes:
  Codebook (lossless): registered triples <-> octahedral states via lookup.
  Axis classifier (lossy): 3 tokens -> binary classification per axis -> state.

The 8 octahedral states carry phi-coherence scores and Gray-code adjacency,
so compressed tokens preserve geometric structure.
"""
from __future__ import annotations

import json
import sys
from dataclasses import dataclass

from rosetta_shape_core._graph import ROOT

ENCODING_PATH = (
    ROOT / "atlas" / "remote" / "geo-binary-bridge" / "octahedral_state_encoding.json"
)
RULES_PATH = ROOT / "rules" / "expand.jsonl"

GLYPHS = ("⊕", "⊖", "⊗", "⊘", "⊙", "⊚", "⊛", "⊜")

# Axis classifiers: which namespaces / ops count as "+" on each axis
_STRUCTURAL = frozenset({"EXPAND", "STRUCTURE", "SHAPE", "GEOM", "STRUCT"})
_GEOMETRIC = frozenset({"SHAPE", "GEOM", "CONST", "FIELD", "STRUCT"})
_CAPABILITY = frozenset({"CAP", "PROTO"})


def _prefix(token: str) -> str:
    return token.split(".")[0] if "." in token else token


@dataclass(frozen=True)
class OctaToken:
    """A single octahedral token encoding a triple."""

    state: int  # 0-7
    bits: str  # "000" through "111"
    glyph: str  # unicode glyph
    phi_coherence: float
    triple: tuple[str, ...]


class OctaTriple:
    """Encode/decode triples as octahedral states.

    Auto-populates a codebook from ``rules/expand.jsonl`` (up to 8 rules).
    Custom triples can be added with :meth:`register`.  Unregistered triples
    fall back to axis classification (lossy).
    """

    def __init__(self) -> None:
        self._states = self._load_states()
        self._codebook: dict[tuple[str, ...], int] = {}
        self._reverse: dict[int, tuple[str, ...]] = {}
        self._glyph_to_state: dict[str, int] = {g: i for i, g in enumerate(GLYPHS)}
        self._build_codebook_from_rules()

    # ------------------------------------------------------------------
    # loading
    # ------------------------------------------------------------------

    def _load_states(self) -> list[dict]:
        if ENCODING_PATH.exists():
            data = json.loads(ENCODING_PATH.read_text(encoding="utf-8"))
            return data.get("states", [])
        return [
            {
                "state": i,
                "vertex_bits": f"{i:03b}",
                "phi_coherence": 0.80,
                "glyph_unicode": GLYPHS[i],
            }
            for i in range(8)
        ]

    def _build_codebook_from_rules(self) -> None:
        if not RULES_PATH.exists():
            return
        rules: list[dict] = []
        for line in RULES_PATH.read_text(encoding="utf-8").splitlines():
            if line.strip():
                rules.append(json.loads(line))
        rules.sort(key=lambda r: -r.get("priority", 0))
        for i, rule in enumerate(rules[:8]):
            w = rule.get("when", {})
            triple = (w.get("op", ""),) + tuple(w.get("args", []))
            self._codebook[triple] = i
            self._reverse[i] = triple

    # ------------------------------------------------------------------
    # public API
    # ------------------------------------------------------------------

    def register(self, triple: tuple[str, ...], state: int) -> None:
        """Register a custom triple -> state mapping (overwrites)."""
        if not 0 <= state <= 7:
            raise ValueError(f"state must be 0-7, got {state}")
        self._codebook[triple] = state
        self._reverse[state] = triple

    def encode(self, *tokens: str) -> OctaToken:
        """Encode 1-3 tokens into an octahedral token.

        Tries codebook first (lossless). Falls back to axis classification.
        """
        triple = tuple(tokens)
        idx = self._codebook.get(triple)
        if idx is None:
            idx = self._classify(triple)
        s = self._states[idx]
        return OctaToken(
            state=idx,
            bits=s.get("vertex_bits", f"{idx:03b}"),
            glyph=GLYPHS[idx],
            phi_coherence=s.get("phi_coherence", 0.0),
            triple=triple,
        )

    def decode(self, key: int | str) -> OctaToken | None:
        """Decode a state (int) or glyph (str) back to its registered triple."""
        if isinstance(key, str):
            idx = self._glyph_to_state.get(key)
            if idx is None:
                return None
        else:
            idx = key
        triple = self._reverse.get(idx)
        if triple is None:
            return None
        s = self._states[idx]
        return OctaToken(
            state=idx,
            bits=s.get("vertex_bits", f"{idx:03b}"),
            glyph=GLYPHS[idx],
            phi_coherence=s.get("phi_coherence", 0.0),
            triple=triple,
        )

    def adjacent(self, state: int) -> list[int]:
        """Return states reachable by a single Gray-code bit flip."""
        return [state ^ (1 << b) for b in range(3)]

    @property
    def codebook_size(self) -> int:
        return len(self._codebook)

    def codebook_table(self) -> list[dict]:
        """Return the full codebook as a list of dicts."""
        rows = []
        for triple, idx in sorted(self._codebook.items(), key=lambda kv: kv[1]):
            s = self._states[idx]
            rows.append(
                {
                    "state": idx,
                    "bits": s.get("vertex_bits", f"{idx:03b}"),
                    "glyph": GLYPHS[idx],
                    "phi_coherence": s.get("phi_coherence", 0.0),
                    "triple": list(triple),
                }
            )
        return rows

    # ------------------------------------------------------------------
    # axis classification (lossy fallback)
    # ------------------------------------------------------------------

    @staticmethod
    def _classify(tokens: tuple[str, ...]) -> int:
        padded = list(tokens) + [""] * (3 - len(tokens))
        b0 = 1 if _prefix(padded[0]) in _STRUCTURAL else 0
        b1 = 1 if _prefix(padded[1]) in _GEOMETRIC else 0
        b2 = 1 if _prefix(padded[2]) in _CAPABILITY else 0
        return b0 | (b1 << 1) | (b2 << 2)


# ------------------------------------------------------------------
# CLI
# ------------------------------------------------------------------


def main() -> None:
    ot = OctaTriple()

    if "--table" in sys.argv:
        print(json.dumps(ot.codebook_table(), indent=2))
        return

    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    if not args:
        print("Usage: python -m rosetta_shape_core.octa_triple TOKEN1 [TOKEN2] [TOKEN3]")
        print("       python -m rosetta_shape_core.octa_triple --table")
        print(f"\nCodebook: {ot.codebook_size} triples registered")
        for row in ot.codebook_table():
            print(f"  {row['glyph']}  {row['bits']}  φ={row['phi_coherence']:.2f}  {' '.join(row['triple'])}")
        return

    token = ot.encode(*args)
    print(f"Tokens:  {' '.join(args)}")
    print(f"State:   {token.state}  ({token.bits})")
    print(f"Glyph:   {token.glyph}")
    print(f"φ-coh:   {token.phi_coherence:.2f}")
    adj = ot.adjacent(token.state)
    for a in adj:
        dec = ot.decode(a)
        label = " ".join(dec.triple) if dec else "(unregistered)"
        print(f"  ↔ {a} ({a:03b}) {GLYPHS[a]}  {label}")


if __name__ == "__main__":
    main()
