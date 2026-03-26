"""
generate_curiosity_map.py
--------------------------
Generates a static HTML curiosity map from all open_questions across
every family and principle node.

Each question is a card showing:
  • The node it belongs to (id, name, symbol)
  • The unresolved tension
  • The curiosity hook (why it matters)
  • Tags and domain

Filter controls (no server needed — pure JS):
  • By five_field / domain
  • By family vs principle
  • By tag keyword

Output: examples/curiosity_map.html  (open in any browser)

Usage:
    python examples/generate_curiosity_map.py
    python examples/generate_curiosity_map.py --out my_map.html
"""

import json, pathlib, argparse, html

ROOT     = pathlib.Path(__file__).parent.parent
ONTOLOGY = ROOT / "ontology"

# ── Load all nodes ────────────────────────────────────────────────────────────

def load_nodes() -> list[dict]:
    nodes = []
    for sub in ("families", "principles"):
        d = ONTOLOGY / sub
        if not d.exists():
            continue
        for fp in sorted(d.glob("*.json")):
            try:
                nodes.append(json.loads(fp.read_text()))
            except Exception:
                pass
    return nodes

# ── Build card data ───────────────────────────────────────────────────────────

def build_cards(nodes: list[dict]) -> list[dict]:
    cards = []
    for node in nodes:
        nid    = node.get("id", "")
        name   = node.get("name", "")
        sym    = node.get("symbol", "·")
        domain = node.get("domain", node.get("five_field", ""))
        field  = node.get("five_field", "")
        kind   = "family" if nid.startswith("FAMILY") else "principle"
        tags   = node.get("tags", [])
        seed   = node.get("seed_prompt", "")

        for oq in node.get("open_questions", []):
            cards.append({
                "id":       nid,
                "name":     name,
                "symbol":   sym,
                "domain":   domain,
                "field":    field,
                "kind":     kind,
                "tags":     tags,
                "seed":     seed,
                "question": oq.get("question", ""),
                "tension":  oq.get("tension", ""),
                "hook":     oq.get("curiosity_hook", ""),
            })
    return cards

# ── HTML generation ───────────────────────────────────────────────────────────

FIELD_COLORS = {
    "chemical":  "#4a9eff",
    "emotional": "#ff7eb3",
    "cognitive": "#7eff8b",
    "dream":     "#c97bff",
    "symbolic":  "#ffd97b",
    "":          "#aaaaaa",
}

def _card_html(c: dict, idx: int) -> str:
    color    = FIELD_COLORS.get(c["field"], FIELD_COLORS[""])
    tags_str = " ".join(f'<span class="tag">{html.escape(t)}</span>'
                        for t in c["tags"][:5])
    return f"""
    <div class="card" data-kind="{c['kind']}" data-field="{html.escape(c['field'])}"
         data-domain="{html.escape(c['domain'])}" data-tags="{html.escape(' '.join(c['tags']))}"
         data-id="{html.escape(c['id'])}">
      <div class="card-header" style="border-left: 4px solid {color}">
        <span class="symbol">{html.escape(c['symbol'])}</span>
        <span class="node-id">{html.escape(c['id'])}</span>
        <span class="node-name">{html.escape(c['name'])}</span>
        <span class="kind-badge {c['kind']}">{c['kind']}</span>
      </div>
      <div class="question">❓ {html.escape(c['question'])}</div>
      <div class="tension"><strong>Tension:</strong> {html.escape(c['tension'])}</div>
      <div class="hook"><strong>Curiosity hook:</strong> {html.escape(c['hook'])}</div>
      <div class="seed-row"><em>{html.escape(c['seed'])}</em></div>
      <div class="tags-row">{tags_str}</div>
    </div>"""

def generate_html(cards: list[dict], nodes: list[dict]) -> str:
    # Collect filter values
    all_fields  = sorted(set(c["field"]  for c in cards if c["field"]))
    all_domains = sorted(set(c["domain"] for c in cards if c["domain"]))
    all_kinds   = ["family", "principle"]

    field_opts  = "\n".join(
        f'<option value="{html.escape(f)}">{html.escape(f)}</option>'
        for f in all_fields)

    cards_html = "\n".join(_card_html(c, i) for i, c in enumerate(cards))

    n_families   = sum(1 for n in nodes if n.get("id","").startswith("FAMILY"))
    n_principles = sum(1 for n in nodes if n.get("id","").startswith("PRINCIPLE"))
    n_questions  = len(cards)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Rosetta Shape Core — Curiosity Map</title>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: 'Segoe UI', system-ui, sans-serif;
      background: #0d0d14;
      color: #e0e0e0;
      min-height: 100vh;
    }}
    header {{
      padding: 2rem 2rem 1rem;
      border-bottom: 1px solid #222;
    }}
    header h1 {{
      font-size: 1.5rem;
      font-weight: 300;
      letter-spacing: 0.05em;
      color: #fff;
    }}
    header .subtitle {{
      color: #888;
      font-size: 0.85rem;
      margin-top: 0.3rem;
    }}
    .stats {{
      display: flex; gap: 2rem; margin-top: 0.8rem;
    }}
    .stat {{
      text-align: center;
    }}
    .stat .n {{ font-size: 1.6rem; font-weight: 700; color: #7eb3ff; }}
    .stat .l {{ font-size: 0.7rem; color: #666; text-transform: uppercase; letter-spacing: 0.08em; }}

    .controls {{
      display: flex; flex-wrap: wrap; gap: 0.8rem;
      padding: 1rem 2rem;
      border-bottom: 1px solid #1a1a2a;
      background: #0a0a12;
      position: sticky; top: 0; z-index: 10;
    }}
    .controls label {{ font-size: 0.75rem; color: #888; display: flex; flex-direction: column; gap: 0.2rem; }}
    select, input[type=text] {{
      background: #1a1a2a; color: #ccc; border: 1px solid #333;
      border-radius: 4px; padding: 0.3rem 0.6rem; font-size: 0.8rem;
      min-width: 130px;
    }}
    select:focus, input:focus {{ outline: none; border-color: #4a9eff; }}
    button {{
      background: #1e1e30; color: #ccc; border: 1px solid #333;
      border-radius: 4px; padding: 0.35rem 0.9rem; font-size: 0.8rem;
      cursor: pointer; align-self: flex-end;
    }}
    button:hover {{ background: #2a2a44; color: #fff; }}

    .result-count {{
      padding: 0.5rem 2rem; font-size: 0.75rem; color: #555;
    }}

    .grid {{
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
      gap: 1rem;
      padding: 1rem 2rem 3rem;
    }}

    .card {{
      background: #131320;
      border: 1px solid #1e1e32;
      border-radius: 8px;
      padding: 1rem;
      transition: border-color 0.15s, transform 0.1s;
    }}
    .card:hover {{
      border-color: #3a3a60;
      transform: translateY(-2px);
    }}
    .card.hidden {{ display: none; }}

    .card-header {{
      display: flex; align-items: baseline; gap: 0.5rem;
      padding-left: 0.6rem; margin-bottom: 0.7rem;
    }}
    .symbol {{ font-size: 1.1rem; }}
    .node-id {{ font-size: 0.7rem; color: #666; font-family: monospace; }}
    .node-name {{ font-size: 0.9rem; font-weight: 600; color: #ccc; flex: 1; }}
    .kind-badge {{
      font-size: 0.6rem; padding: 0.15rem 0.4rem; border-radius: 3px;
      text-transform: uppercase; letter-spacing: 0.06em;
    }}
    .kind-badge.family {{ background: #1a2a3a; color: #4a9eff; }}
    .kind-badge.principle {{ background: #2a1a3a; color: #c97bff; }}

    .question {{
      font-size: 0.9rem; color: #ddd; margin-bottom: 0.5rem;
      line-height: 1.4;
    }}
    .tension {{
      font-size: 0.78rem; color: #aaa; margin-bottom: 0.35rem;
      line-height: 1.35;
    }}
    .hook {{
      font-size: 0.78rem; color: #7eb3ff; margin-bottom: 0.5rem;
      line-height: 1.35;
    }}
    .seed-row {{
      font-size: 0.72rem; color: #555; margin-bottom: 0.5rem;
      font-style: italic;
    }}
    .tags-row {{ display: flex; flex-wrap: wrap; gap: 0.3rem; }}
    .tag {{
      font-size: 0.62rem; background: #1a1a2a; color: #666;
      padding: 0.1rem 0.4rem; border-radius: 3px; border: 1px solid #222;
    }}

    .field-legend {{
      display: flex; flex-wrap: wrap; gap: 0.6rem;
      padding: 0.5rem 2rem; font-size: 0.7rem;
    }}
    .field-dot {{ display: flex; align-items: center; gap: 0.3rem; color: #666; }}
    .dot {{ width: 8px; height: 8px; border-radius: 50%; }}
  </style>
</head>
<body>
  <header>
    <h1>◉ Rosetta Shape Core · Curiosity Map</h1>
    <div class="subtitle">
      Open questions across all ontology nodes — the unresolved tensions that drive exploration
    </div>
    <div class="stats">
      <div class="stat"><div class="n">{n_families}</div><div class="l">Families</div></div>
      <div class="stat"><div class="n">{n_principles}</div><div class="l">Principles</div></div>
      <div class="stat"><div class="n">{n_questions}</div><div class="l">Open Questions</div></div>
    </div>
  </header>

  <div class="field-legend">
    {''.join(f'<div class="field-dot"><div class="dot" style="background:{c}"></div>{f}</div>'
             for f, c in FIELD_COLORS.items() if f)}
  </div>

  <div class="controls">
    <label>Kind
      <select id="filter-kind">
        <option value="">All</option>
        <option value="family">Families</option>
        <option value="principle">Principles</option>
      </select>
    </label>
    <label>Five-Field
      <select id="filter-field">
        <option value="">All</option>
        {field_opts}
      </select>
    </label>
    <label>Search (question / tag / node)
      <input type="text" id="filter-search" placeholder="e.g. chaos, phi, emotion...">
    </label>
    <button onclick="clearFilters()">Clear</button>
  </div>

  <div class="result-count" id="result-count"></div>

  <div class="grid" id="grid">
    {cards_html}
  </div>

  <script>
    function applyFilters() {{
      const kind   = document.getElementById('filter-kind').value.toLowerCase();
      const field  = document.getElementById('filter-field').value.toLowerCase();
      const search = document.getElementById('filter-search').value.toLowerCase();

      const cards = document.querySelectorAll('.card');
      let shown = 0;
      cards.forEach(card => {{
        const ckind   = card.dataset.kind   || '';
        const cfield  = card.dataset.field  || '';
        const ctags   = card.dataset.tags   || '';
        const cid     = card.dataset.id     || '';
        const ctext   = (card.textContent   || '').toLowerCase();

        const matchKind   = !kind   || ckind  === kind;
        const matchField  = !field  || cfield === field;
        const matchSearch = !search || ctext.includes(search) ||
                            ctags.includes(search) || cid.toLowerCase().includes(search);

        if (matchKind && matchField && matchSearch) {{
          card.classList.remove('hidden');
          shown++;
        }} else {{
          card.classList.add('hidden');
        }}
      }});
      document.getElementById('result-count').textContent =
        `Showing ${{shown}} of ${{cards.length}} questions`;
    }}

    function clearFilters() {{
      document.getElementById('filter-kind').value   = '';
      document.getElementById('filter-field').value  = '';
      document.getElementById('filter-search').value = '';
      applyFilters();
    }}

    document.getElementById('filter-kind').addEventListener('change', applyFilters);
    document.getElementById('filter-field').addEventListener('change', applyFilters);
    document.getElementById('filter-search').addEventListener('input', applyFilters);

    applyFilters();
  </script>
</body>
</html>"""

# ── Main ──────────────────────────────────────────────────────────────────────

def main(argv=None):
    p = argparse.ArgumentParser(description="Generate static curiosity map HTML")
    p.add_argument("--out", default=None, help="Output path (default: examples/curiosity_map.html)")
    args = p.parse_args(argv)

    out = pathlib.Path(args.out) if args.out else \
          ROOT / "examples" / "curiosity_map.html"

    nodes = load_nodes()
    cards = build_cards(nodes)

    print(f"  Loaded {len(nodes)} nodes → {len(cards)} open questions")
    html_content = generate_html(cards, nodes)
    out.write_text(html_content, encoding="utf-8")
    print(f"  Saved → {out}")
    print(f"  Open in browser: file://{out.resolve()}")

if __name__ == "__main__":
    main()
