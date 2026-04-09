"""
rosetta_shape_core.query
------------------------
Fuzzy keyword search across all family/principle ontology nodes.
Returns structured prompt fragments for AI injection or human reading.

CLI:
    python -m rosetta_shape_core.query "synchronization"
    python -m rosetta_shape_core.query "chaos edge order" --top 3
    python -m rosetta_shape_core.query FAMILY.F01 --full
    python -m rosetta_shape_core.query --list

Importable:
    from rosetta_shape_core.query import search, get_node, prompt_fragment
"""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import textwrap
from typing import Optional

ROOT     = pathlib.Path(__file__).resolve().parents[2]
ONTOLOGY = ROOT / "ontology"

# ── Node loading ──────────────────────────────────────────────────────────────

def _all_node_paths() -> list[pathlib.Path]:
    paths = []
    for sub in ("families", "principles"):
        d = ONTOLOGY / sub
        if d.exists():
            paths.extend(sorted(d.glob("*.json")))
    return paths

def load_all_nodes() -> dict[str, dict]:
    """Return {node_id: node_dict} for every family and principle."""
    nodes = {}
    for p in _all_node_paths():
        try:
            node = json.loads(p.read_text())
            nid  = node.get("id")
            if nid:
                nodes[nid] = node
        except Exception:
            pass
    return nodes

def get_node(node_id: str) -> Optional[dict]:
    """Load a single node by exact ID (e.g. 'FAMILY.F01')."""
    return load_all_nodes().get(node_id)

# ── Scoring ───────────────────────────────────────────────────────────────────

def _text_corpus(node: dict) -> str:
    """Flatten all searchable text from a node into one string."""
    parts = [
        node.get("id", ""),
        node.get("name", ""),
        node.get("domain", ""),
        node.get("five_field", ""),
        node.get("core_insight", ""),
        node.get("seed_prompt", ""),
        " ".join(node.get("tags", [])),
        " ".join(node.get("resonates_with", [])),
    ]
    for eq in node.get("key_equations", []):
        parts += [eq.get("name", ""), eq.get("why", "")]
    for oq in node.get("open_questions", []):
        parts += [oq.get("question", ""), oq.get("tension", ""), oq.get("curiosity_hook", "")]
    for cb in node.get("cross_domain_bridges", []):
        parts += [cb.get("domain", ""), cb.get("manifestation", ""), cb.get("example", "")]
    for ep in node.get("explore_paths", []):
        parts += [ep.get("thread", ""), ep.get("next_node", "")]
    return " ".join(str(p) for p in parts).lower()

def _score(node: dict, terms: list[str]) -> float:
    corpus = _text_corpus(node)
    score  = 0.0
    nid    = node.get("id", "").lower()
    name   = node.get("name", "").lower()
    for term in terms:
        t = term.lower()
        if t in nid or t in name:
            score += 3.0          # exact id/name hit
        elif t in corpus:
            count = corpus.count(t)
            score += 1.0 + 0.1 * min(count, 5)
    return score

def search(query: str, top: int = 3) -> list[tuple[float, dict]]:
    """
    Fuzzy search all nodes for `query`. Returns top-N (score, node) pairs.
    Query can be: natural language, keywords, or exact ID like 'FAMILY.F01'.
    """
    nodes  = load_all_nodes()
    terms  = re.split(r"[\s,./]+", query.strip())
    terms  = [t for t in terms if len(t) > 1]

    # Exact ID match shortcut
    if query.upper() in nodes:
        return [(99.0, nodes[query.upper()])]

    scored = [(s, n) for n in nodes.values() if (s := _score(n, terms)) > 0]
    scored.sort(key=lambda x: -x[0])
    return scored[:top]

# ── Formatting ────────────────────────────────────────────────────────────────

def _wrap(text: str, width: int = 72, indent: str = "  ") -> str:
    return textwrap.fill(text, width=width, initial_indent=indent,
                         subsequent_indent=indent)

def format_node_brief(node: dict) -> str:
    """One-screen summary — good for quick human browsing."""
    lines = [
        f"\n{'─'*64}",
        f"  {node.get('symbol','')} {node['id']} · {node['name']}",
        f"  domain: {node.get('domain','')}  |  field: {node.get('five_field', node.get('dodecahedron_face',''))}",
        "",
        _wrap(node.get("core_insight", ""), indent="  "),
        "",
        "  Key tension:",
    ]
    for oq in node.get("open_questions", [])[:1]:
        lines.append(_wrap(f"  ❓ {oq.get('question','')}", indent="    "))
        lines.append(_wrap(f"  ↳ {oq.get('curiosity_hook','')}", indent="    "))
    lines.append(f"\n  seed: {node.get('seed_prompt','')}")
    lines.append(f"{'─'*64}")
    return "\n".join(lines)

def format_node_full(node: dict) -> str:
    """Full node dump — for deep exploration."""
    lines = [
        f"\n{'═'*64}",
        f"  {node.get('symbol','')} {node['id']} · {node['name']}",
        f"  domain: {node.get('domain','')}",
        "",
        "  CORE INSIGHT",
        _wrap(node.get("core_insight", "")),
        "",
        "  KEY EQUATIONS",
    ]
    for eq in node.get("key_equations", []):
        lines.append(f"    {eq.get('name','')}: {eq.get('formula','')}")
        lines.append(_wrap(f"    why: {eq.get('why','')}", indent="      "))
    lines += ["", "  OPEN QUESTIONS"]
    for oq in node.get("open_questions", []):
        lines.append(f"\n    ❓ {oq.get('question','')}")
        lines.append(_wrap(f"    tension:       {oq.get('tension','')}", indent="               "))
        lines.append(_wrap(f"    curiosity_hook: {oq.get('curiosity_hook','')}", indent="               "))
    lines += ["", "  EXPLORE PATHS"]
    for ep in node.get("explore_paths", []):
        lines.append(f"    → {ep.get('next_node','')}: {ep.get('thread','')}")
    lines += ["", "  CROSS-DOMAIN BRIDGES"]
    for cb in node.get("cross_domain_bridges", []):
        lines.append(f"    [{cb.get('domain','')}] {cb.get('manifestation','')}")
        lines.append(f"      e.g. {cb.get('example','')}")
    lines += ["", "  NOISE SIGNATURES (what disorder looks like here)"]
    for ns in node.get("noise_signature", []):
        lines.append(f"    pattern:   {ns.get('pattern','')}")
        lines.append(f"    diagnosis: {ns.get('diagnosis','')}")
    lines.append(f"\n{'═'*64}")
    return "\n".join(lines)

def prompt_fragment(query: str, top: int = 3) -> str:
    """
    Return a compact AI-injectable prompt fragment for `query`.
    Designed to be prepended to a system prompt or user message.

    Example:
        fragment = prompt_fragment("self-organization in networks")
        # inject into your Claude/GPT call
    """
    results = search(query, top=top)
    if not results:
        return f"[rosetta-query: no nodes matched '{query}']"

    lines = [
        f"[rosetta-ontology: {len(results)} node(s) relevant to '{query}']",
        ""
    ]
    for score, node in results:
        lines += [
            f"## {node.get('symbol','')} {node['id']} · {node['name']}",
            f"core: {node.get('core_insight','')}",
            f"seed: {node.get('seed_prompt','')}",
        ]
        oqs = node.get("open_questions", [])
        if oqs:
            lines.append(f"tension: {oqs[0].get('question','')} — {oqs[0].get('curiosity_hook','')}")
        eps = node.get("explore_paths", [])
        if eps:
            lines.append(f"explore: {' | '.join(e.get('next_node','') for e in eps[:3])}")
        lines.append("")
    return "\n".join(lines)

# ── CLI ───────────────────────────────────────────────────────────────────────

def _list_all(nodes: dict) -> None:
    families   = {k: v for k, v in nodes.items() if k.startswith("FAMILY")}
    principles = {k: v for k, v in nodes.items() if k.startswith("PRINCIPLE")}
    print(f"\n  {len(families)} families | {len(principles)} principles\n")
    print("  FAMILIES")
    for k, v in sorted(families.items()):
        print(f"    {v.get('symbol','·')} {k:<22} {v.get('name','')}")
    print("\n  PRINCIPLES")
    for k, v in sorted(principles.items()):
        print(f"    {v.get('symbol','·')} {k:<22} {v.get('name','')}")
    print()

def main(argv=None):
    p = argparse.ArgumentParser(
        description="Query Rosetta Shape Core ontology nodes",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""
        Examples:
          python -m rosetta_shape_core.query "chaos synchronization"
          python -m rosetta_shape_core.query FAMILY.F01 --full
          python -m rosetta_shape_core.query "proportion ratio phi" --top 5
          python -m rosetta_shape_core.query --list
          python -m rosetta_shape_core.query "entropy" --ai
        """)
    )
    p.add_argument("query", nargs="?", help="Search query or node ID")
    p.add_argument("--top",  type=int, default=3, help="Number of results (default 3)")
    p.add_argument("--full", action="store_true", help="Show full node detail")
    p.add_argument("--list", action="store_true", help="List all nodes")
    p.add_argument("--ai",   action="store_true",
                   help="Output compact AI-injectable prompt fragment")
    args = p.parse_args(argv)

    nodes = load_all_nodes()

    if args.list:
        _list_all(nodes)
        return

    if not args.query:
        p.print_help()
        return

    if args.ai:
        print(prompt_fragment(args.query, top=args.top))
        return

    results = search(args.query, top=args.top)
    if not results:
        print(f"\n  No nodes matched '{args.query}'")
        print("  Try --list to see all nodes")
        return

    print(f"\n  Found {len(results)} node(s) for '{args.query}':\n")
    for score, node in results:
        if args.full:
            print(format_node_full(node))
        else:
            print(format_node_brief(node))

if __name__ == "__main__":
    main()
