#!/usr/bin/env python3
"""Build a single self-contained HTML page to review extracted figures/tables.

Images are base64-embedded so the file opens anywhere with no broken paths
(handy on WSL/headless — just open it in a browser). Optionally shows the old
PyMuPDF get_images() dump side-by-side so the difference is obvious.

Usage:
  python review.py --manifest <out>/manifest.json --out review.html \
      [--old-dir <get_images_dump>] [--title "CLIP figures"]
"""

from __future__ import annotations

import argparse
import base64
import html
import json
import sys
from pathlib import Path


def _b64(p: Path) -> str:
    ext = p.suffix.lstrip(".").lower() or "png"
    mime = "jpeg" if ext in ("jpg", "jpeg") else ext
    return f"data:image/{mime};base64," + base64.b64encode(p.read_bytes()).decode()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", type=Path, required=True)
    ap.add_argument("--assets-dir", type=Path, default=None,
                    help="dir holding the crops (default: manifest's folder)")
    ap.add_argument("--old-dir", type=Path, default=None,
                    help="optional get_images() dump dir to compare against")
    ap.add_argument("--title", default="parse-figures review")
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()

    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    assets = args.assets_dir or args.manifest.parent
    manifest.sort(key=lambda e: (e.get("page", 0), e.get("bbox_px", [0])[0]))

    cards = []
    for e in manifest:
        img = assets / e["image"]
        if not img.exists():
            continue
        cap = html.escape(e.get("caption", "") or "(no caption)")
        badge = e.get("type", "?")
        label = html.escape(str(e.get("label", "?")))
        tbl = ""
        if e.get("table_markdown"):
            tbl = (f"<details><summary>table text (from PDF layer)</summary>"
                   f"<pre>{html.escape(e['table_markdown'])}</pre></details>")
        cards.append(f"""
        <div class="card">
          <div class="meta"><span class="badge {badge}">{badge} {label}</span>
            <span class="pg">p.{e.get('page','?')}</span></div>
          <img src="{_b64(img)}" />
          <div class="cap">{cap}</div>
          {tbl}
        </div>""")

    old_html = ""
    if args.old_dir and args.old_dir.exists():
        olds = sorted(args.old_dir.glob("*.png")) + sorted(args.old_dir.glob("*.jpg"))
        old_cards = "".join(
            f'<div class="card old"><div class="meta"><span class="badge old">raw {i+1}</span></div>'
            f'<img src="{_b64(p)}" /><div class="cap">{html.escape(p.name)}</div></div>'
            for i, p in enumerate(olds))
        if not olds:
            old_cards = '<p class="empty">get_images() produced nothing.</p>'
        old_html = f"""
        <h2>OLD — PyMuPDF <code>get_images()</code> dump ({len(olds)} raw objects)</h2>
        <p class="note">Embedded raster objects only — vector diagrams and tables are
        invisible to this method, numbering is by appearance order, no captions.</p>
        <div class="grid">{old_cards}</div>"""

    n_fig = sum(1 for e in manifest if e.get("type") == "figure")
    n_tab = sum(1 for e in manifest if e.get("type") == "table")

    doc = f"""<!doctype html><html><head><meta charset="utf-8">
<title>{html.escape(args.title)}</title><style>
body{{font:14px/1.5 -apple-system,Segoe UI,Roboto,sans-serif;margin:0;background:#f6f7f9;color:#1a1a1a}}
header{{background:#111;color:#fff;padding:18px 24px}}
header h1{{margin:0 0 4px;font-size:18px}} header .sum{{opacity:.8;font-size:13px}}
main{{padding:20px 24px;max-width:1400px;margin:0 auto}}
h2{{margin:28px 0 6px;font-size:16px}} .note{{color:#666;margin:0 0 12px}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:16px}}
.card{{background:#fff;border:1px solid #e3e5e8;border-radius:8px;padding:10px;box-shadow:0 1px 2px rgba(0,0,0,.04)}}
.card img{{width:100%;height:auto;border:1px solid #eee;border-radius:4px;background:#fff}}
.meta{{display:flex;justify-content:space-between;align-items:center;margin-bottom:8px}}
.badge{{font-weight:600;font-size:11px;text-transform:uppercase;letter-spacing:.04em;padding:2px 8px;border-radius:99px;color:#fff}}
.badge.figure{{background:#2563eb}} .badge.table{{background:#7c3aed}} .badge.old{{background:#9ca3af}}
.pg{{color:#999;font-size:12px}}
.cap{{font-size:12px;color:#444;margin-top:8px}}
details{{margin-top:8px}} summary{{cursor:pointer;font-size:12px;color:#2563eb}}
pre{{background:#f3f4f6;padding:8px;border-radius:4px;overflow:auto;font-size:11px;max-height:240px}}
.empty{{color:#999}} code{{background:#eee;padding:1px 4px;border-radius:3px}}
</style></head><body>
<header><h1>{html.escape(args.title)}</h1>
<div class="sum">NEW parse-figures: <b>{len(manifest)}</b> crops — {n_fig} figures, {n_tab} tables, all caption-matched from the PDF text layer.</div></header>
<main>
<h2>NEW — parse-figures (render → grid → VLM bbox → crop)</h2>
<div class="grid">{''.join(cards)}</div>
{old_html}
</main></body></html>"""

    args.out.write_text(doc, encoding="utf-8")
    print(f"wrote {args.out}  ({args.out.stat().st_size//1024} KB, {len(manifest)} new crops)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
