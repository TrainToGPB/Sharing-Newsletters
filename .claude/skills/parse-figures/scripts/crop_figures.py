#!/usr/bin/env python3
"""Crop figure/table regions from clean page renders, given normalized bboxes.

Reads the pages.json produced by grid_render.py and a boxes.json describing the
regions a vision model identified (in the same normalized 0-1000 / 0-norm_h
coordinate system the grid showed). Maps each box back to pixels on the clean
render, crops it (with a little padding), and writes a self-describing PNG named
by the paper's real label, e.g. figure-3.png, table-2.png.

boxes.json schema (a list):
  [
    {
      "page": 3,
      "type": "figure",            # "figure" | "table"
      "label": "3",                # paper's Figure/Table number, NOT page order
      "bbox": [x0, y0, x1, y1],     # normalized; x in 0..1000, y in 0..norm_h
      "caption": "Figure 3: ...",   # transcribed text (optional)
      "table_markdown": "| a | b |..."  # optional, tables only
    },
    ...
  ]

Usage:
  python crop_figures.py --pages-json work/pages.json --boxes boxes.json \
      --out-dir papers/<slug>/assets --pad 10
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


def _slug(s: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9]+", "-", str(s)).strip("-").lower()
    return s or "x"


def _caption_for(page_entry: dict, typ: str, label) -> str:
    """Accurate caption from the PDF text layer (scan), matched by type+label.

    The vision model only supplies geometry; captions never come from it, so they
    can't be hallucinated. Falls back to empty if the scan didn't see this label.
    """
    for c in page_entry.get("captions", []):
        if c.get("type") == typ and str(c.get("label")) == str(label):
            return c.get("text", "")
    return ""


def _table_markdown(doc, page_no: int, norm_bbox, norm_h) -> str:
    """Pull real table cells from the PDF text layer inside the box (not the VLM).

    Converts the normalized box to PDF points and uses PyMuPDF's table finder so
    the numbers are exact. Falls back to clipped plain text if no grid is found.
    """
    try:
        import fitz
        page = doc[page_no - 1]
        pw, ph = page.rect.width, page.rect.height
        x0, y0, x1, y1 = norm_bbox
        rect = fitz.Rect(min(x0, x1) / 1000 * pw, min(y0, y1) / norm_h * ph,
                         max(x0, x1) / 1000 * pw, max(y0, y1) / norm_h * ph)
        tabs = page.find_tables(clip=rect)
        if tabs.tables:
            return tabs.tables[0].to_markdown().strip()
        txt = page.get_text("text", clip=rect).strip()
        return txt
    except Exception as exc:
        print(f"table extract failed p{page_no}: {exc}", file=sys.stderr)
        return ""


def main() -> int:
    from PIL import Image

    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--pages-json", type=Path, required=True)
    ap.add_argument("--boxes", type=Path, required=True)
    ap.add_argument("--out-dir", type=Path, required=True)
    ap.add_argument("--pad", type=int, default=16, help="padding in px around each crop")
    args = ap.parse_args()

    meta = json.loads(args.pages_json.read_text(encoding="utf-8"))
    work_dir = args.pages_json.parent
    by_page = {e["page"]: e for e in meta["pages"]}
    boxes = json.loads(args.boxes.read_text(encoding="utf-8"))
    if isinstance(boxes, dict):  # tolerate {"boxes":[...]}
        boxes = boxes.get("boxes", [])

    # Open the source PDF for accurate table text extraction (optional).
    doc = None
    pdf_path = meta.get("pdf")
    if pdf_path and Path(pdf_path).exists():
        try:
            import fitz
            doc = fitz.open(pdf_path)
        except Exception as exc:
            print(f"could not open pdf for table text: {exc}", file=sys.stderr)

    args.out_dir.mkdir(parents=True, exist_ok=True)
    manifest = []
    used = {}

    for b in boxes:
        page = b.get("page")
        pe = by_page.get(page)
        if pe is None:
            print(f"no render for page {page}; skipping {b.get('label')}", file=sys.stderr)
            continue
        clean = Image.open(work_dir / pe["clean"]).convert("RGB")
        cw, ch = pe["content_w_px"], pe["content_h_px"]
        nw, nh = pe["norm_w"], pe["norm_h"]
        x0, y0, x1, y1 = b["bbox"]
        # normalized -> pixel, ordered + clamped, with padding
        px0 = max(0, int(min(x0, x1) / nw * cw) - args.pad)
        py0 = max(0, int(min(y0, y1) / nh * ch) - args.pad)
        px1 = min(cw, int(max(x0, x1) / nw * cw) + args.pad)
        py1 = min(ch, int(max(y0, y1) / nh * ch) + args.pad)
        if px1 - px0 < 4 or py1 - py0 < 4:
            print(f"degenerate box for {b.get('label')}; skipping", file=sys.stderr)
            continue

        typ = b.get("type", "figure").lower()
        typ = "table" if typ.startswith("tab") else "figure"
        base = f"{typ}-{_slug(b.get('label', len(manifest) + 1))}"
        used[base] = used.get(base, 0) + 1
        fname = f"{base}.png" if used[base] == 1 else f"{base}-{used[base]}.png"

        clean.crop((px0, py0, px1, py1)).save(str(args.out_dir / fname))
        # caption + table text come from the PDF layer, NOT the model
        caption = _caption_for(pe, typ, b.get("label")) or b.get("caption", "")
        entry = {
            "type": typ,
            "label": b.get("label"),
            "page": page,
            "image": fname,
            "caption": caption,
            "bbox_px": [px0, py0, px1, py1],
        }
        if typ == "table" and doc is not None:
            md = _table_markdown(doc, page, b["bbox"], nh)
            if md:
                entry["table_markdown"] = md
        manifest.append(entry)

    if doc is not None:
        doc.close()

    (args.out_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"cropped": len(manifest),
                      "out_dir": str(args.out_dir),
                      "manifest": str(args.out_dir / "manifest.json")}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
