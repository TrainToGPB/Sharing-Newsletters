#!/usr/bin/env python3
"""Render PDF pages to coordinate-gridded PNGs for VLM-based figure/table detection.

The point of this script: a vision model is bad at guessing absolute pixel
coordinates from a bare image, but good at reading values off a labelled grid.
So we render each page, overlay a light grid, and print coordinate labels in a
*margin outside the page content*. The model looks at the gridded image, reports
bounding boxes in the normalized 0-1000 (x) / 0-norm_h (y) system, and crop.py
maps those numbers back to exact pixels on a clean (un-gridded) render.

Two outputs per page:
  page-<n>.png       clean render            -> cropped from later
  page-<n>.grid.png  gridded + labelled      -> shown to the model

Coordinate system (what the model reports in):
  x: 0 .. 1000      (left .. right of the page CONTENT, margins excluded)
  y: 0 .. norm_h    (top .. bottom, norm_h = round(1000 * height/width))
Grid lines + margin labels are drawn at every --grid-step units.

Usage:
  # 1) cheap scan: which pages have figures/tables? (no rendering)
  python grid_render.py paper.pdf --scan

  # 2) render specific pages (or omit --pages to render all scan candidates)
  python grid_render.py paper.pdf --out-dir work --pages 3,5,7
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# A real caption (vs. a body mention like "as shown in Figure 2") starts a line
# and is followed by a delimiter: "Figure 1.", "Table 2:", "Figure 3 |". The
# trailing [.:|)] is what rejects "...in Figure 2 we show". This also hands us the
# real label, so the model is told exactly which items to expect on each page.
_CAPTION_RE = re.compile(
    r"^\s*(figure|fig\.|table|tab\.|algorithm|alg\.)\s*(\d+)\s*([.:|)])",
    re.IGNORECASE | re.MULTILINE,
)


def _caption_type(word: str) -> str:
    return "table" if word.lower().startswith("tab") else "figure"


def _fitz():
    try:
        import fitz  # PyMuPDF
        return fitz
    except ImportError:
        sys.exit("PyMuPDF not installed. Run: pip install -r requirements.txt")


def _pil():
    try:
        from PIL import Image, ImageDraw, ImageFont
        return Image, ImageDraw, ImageFont
    except ImportError:
        sys.exit("Pillow not installed. Run: pip install -r requirements.txt")


def _load_font(ImageFont, size: int):
    for name in ("DejaVuSans-Bold.ttf", "DejaVuSans.ttf", "Arial.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except Exception:
            continue
    try:
        return ImageFont.load_default(size=size)  # Pillow >=10
    except TypeError:
        return ImageFont.load_default()


def scan(pdf: Path) -> dict:
    """Find candidate pages (1-indexed) that likely hold a figure or table."""
    fitz = _fitz()
    doc = fitz.open(pdf)
    candidates = []
    captionless = []  # pages with figure-like content but no caption text
    try:
        for i, page in enumerate(doc):
            text = page.get_text("text")
            caps = []
            seen = set()
            for m in _CAPTION_RE.finditer(text):
                typ = _caption_type(m.group(1))
                label = m.group(2)
                key = (typ, label)
                if key in seen:
                    continue
                seen.add(key)
                # grab the rest of the caption line as a hint
                line = text[m.start():].splitlines()[0].strip()
                caps.append({"type": typ, "label": label, "text": line[:200]})
            n_imgs = len(page.get_images(full=True))
            try:
                n_draw = len(page.get_drawings())
            except Exception:
                n_draw = 0
            if caps:
                candidates.append({"page": i + 1, "captions": caps})
            elif n_imgs or n_draw > 30:
                captionless.append({"page": i + 1,
                                    "evidence": f"images:{n_imgs},vector:{n_draw}"})
        # Captions are the primary signal. Only fall back to caption-less pages
        # when the doc has none at all (rare for arXiv) so we don't render the
        # whole paper chasing decorative vector content.
        result = {"pdf": str(pdf), "total_pages": doc.page_count,
                  "candidates": candidates}
        if not candidates and captionless:
            result["candidates"] = [{"page": c["page"], "captions": [],
                                     "note": c["evidence"]} for c in captionless]
        result["captionless_pages"] = captionless
        return result
    finally:
        doc.close()


def render(pdf: Path, out_dir: Path, pages: list[int], dpi: int,
           grid_step: int, margin: int, captions_by_page: dict | None = None) -> dict:
    captions_by_page = captions_by_page or {}
    fitz = _fitz()
    Image, ImageDraw, ImageFont = _pil()
    out_dir.mkdir(parents=True, exist_ok=True)
    font = _load_font(ImageFont, max(12, margin // 4))

    doc = fitz.open(pdf)
    entries = []
    try:
        for pno in pages:
            if pno < 1 or pno > doc.page_count:
                print(f"skip out-of-range page {pno}", file=sys.stderr)
                continue
            page = doc[pno - 1]
            pix = page.get_pixmap(dpi=dpi)
            clean_path = out_dir / f"page-{pno}.png"
            pix.save(str(clean_path))

            clean = Image.open(clean_path).convert("RGB")
            cw, ch = clean.size
            norm_h = round(1000 * ch / cw)

            canvas = Image.new("RGB", (cw + 2 * margin, ch + 2 * margin), "white")
            canvas.paste(clean, (margin, margin))
            draw = ImageDraw.Draw(canvas)

            # vertical lines + x labels (top & bottom margin)
            nx = 0
            while nx <= 1000:
                px = margin + nx / 1000 * cw
                draw.line([(px, margin), (px, margin + ch)], fill=(255, 150, 150), width=1)
                draw.text((px + 2, margin - margin * 0.7), str(nx), fill=(200, 0, 0), font=font)
                draw.text((px + 2, margin + ch + 2), str(nx), fill=(200, 0, 0), font=font)
                nx += grid_step
            # horizontal lines + y labels (left & right margin)
            ny = 0
            while ny <= norm_h:
                py = margin + ny / norm_h * ch
                draw.line([(margin, py), (margin + cw, py)], fill=(150, 150, 255), width=1)
                draw.text((2, py + 1), str(ny), fill=(0, 0, 200), font=font)
                draw.text((margin + cw + 2, py + 1), str(ny), fill=(0, 0, 200), font=font)
                ny += grid_step

            grid_path = out_dir / f"page-{pno}.grid.png"
            canvas.save(str(grid_path))

            entries.append({
                "page": pno,
                "clean": clean_path.name,
                "grid": grid_path.name,
                "content_w_px": cw,
                "content_h_px": ch,
                "norm_w": 1000,
                "norm_h": norm_h,
                "dpi": dpi,
                "grid_step": grid_step,
                "margin": margin,
                # accurate caption text+label from the PDF text layer; the model
                # only supplies geometry, so manifest captions never depend on it.
                "captions": captions_by_page.get(pno, []),
            })
        meta = {"pdf": str(pdf), "out_dir": str(out_dir), "pages": entries}
        (out_dir / "pages.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
        return meta
    finally:
        doc.close()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pdf", type=Path)
    ap.add_argument("--scan", action="store_true",
                    help="print candidate pages as JSON and exit (no rendering)")
    ap.add_argument("--out-dir", type=Path, default=Path("figures-work"))
    ap.add_argument("--pages", default="",
                    help="comma-separated 1-indexed pages; default = all scan candidates")
    ap.add_argument("--dpi", type=int, default=150)
    ap.add_argument("--grid-step", type=int, default=50,
                    help="grid line / label spacing in normalized units (default 50)")
    ap.add_argument("--margin", type=int, default=64,
                    help="outer margin in px where coordinate labels are drawn")
    args = ap.parse_args()

    if not args.pdf.exists():
        print(f"file not found: {args.pdf}", file=sys.stderr)
        return 1
    if args.pdf.suffix.lower() != ".pdf":
        print("only .pdf is supported", file=sys.stderr)
        return 1

    if args.scan:
        print(json.dumps(scan(args.pdf), indent=2))
        return 0

    scan_result = scan(args.pdf)
    cap_map = {c["page"]: c.get("captions", []) for c in scan_result["candidates"]}
    if args.pages.strip():
        pages = [int(p) for p in args.pages.split(",") if p.strip()]
    else:
        pages = [c["page"] for c in scan_result["candidates"]]
        if not pages:
            print("no candidate pages found; pass --pages explicitly", file=sys.stderr)
            return 1

    meta = render(args.pdf, args.out_dir, pages, args.dpi, args.grid_step,
                  args.margin, cap_map)
    print(json.dumps({"rendered_pages": [e["page"] for e in meta["pages"]],
                      "pages_json": str(args.out_dir / "pages.json")}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
