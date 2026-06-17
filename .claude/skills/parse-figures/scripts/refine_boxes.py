#!/usr/bin/env python3
"""Refine VLM-supplied bboxes by snapping their edges to real PyMuPDF geometry.

The VLM (reading a coordinate grid) gets the right *region* but imprecise *edges*
— boxes come out a touch too small (clipped legends / axis labels / bottom rows)
or a touch too large (swallowing the page header). PyMuPDF knows the exact rect
of every text line, embedded image, and vector drawing on the page. So for each
VLM box we:

  1. gather "ink atoms" (text-line / image / drawing rects) on that page,
     clamped to the page and stripped of full-width header/footer rules,
  2. keep the atoms that meaningfully overlap the VLM box (>= OVERLAP of the
     atom's own area — this also pulls in atoms the box only *clipped*),
  3. snap each edge to the tight union of those atoms,
  4. but clamp the move to +/- MAX_EXPAND of the page size, so a stray wide
     drawing can never blow the box up to the whole page.

Input/units match the rest of the skill: boxes are normalized 0..1000 (x) /
0..norm_h (y) on the clean page render; we convert to PDF points to compare with
geometry, then back to normalized so crop_figures.py consumes it unchanged.

Usage:
  python refine_boxes.py --pages-json work/pages.json --boxes boxes.json \
      --out boxes.refined.json [--debug-atoms atoms.json]
"""
from __future__ import annotations
import argparse, json, re, sys
from pathlib import Path

OVERLAP = 0.30      # atom counts if >=30% of its area is inside the VLM box
MAX_EXPAND = 0.18   # an edge may move out at most 18% of page W/H beyond the VLM box
                    # (safe now that page-spanning drawing artifacts are screened
                    #  out below; the main runaway source is gone, so we let table
                    #  rules / clipped columns be recovered more fully)
CAP_GAP = 12.0      # points of clearance kept between the crop edge and the caption,
                    # large enough that crop_figures.py's --pad can't re-reveal it

# A caption line starts with "Figure 3." / "Table 2:" etc. — same rule the scan uses.
_CAP_RE = re.compile(r"^\s*(figure|fig\.|table|tab\.|algorithm|alg\.)\s*(\d+)\s*[.:|)]",
                     re.IGNORECASE)


def caption_rect(page, typ, label):
    """Find the caption for this type+label and return its line/block bboxes (points).

    Returns {"line": [x0,y0,x1,y1], "block": [...]} for the caption's first line and
    its enclosing text block, or None if the page has no matching caption.
    """
    want_table = (typ == "table")
    for blk in page.get_text("dict").get("blocks", []):
        if blk.get("type") != 0:
            continue
        for ln in blk.get("lines", []):
            txt = "".join(s.get("text", "") for s in ln.get("spans", []))
            m = _CAP_RE.match(txt)
            if not m:
                continue
            if (m.group(1).lower().startswith("tab")) != want_table:
                continue
            if str(m.group(2)) != str(label):
                continue
            return {"line": list(ln["bbox"]), "block": list(blk["bbox"])}
    return None


def caption_cut(vlm_pts, cap):
    """Decide where the caption sits and where to cut. Returns ('below'|'above', y_pt)."""
    if not cap:
        return None
    ly0, ly1 = cap["line"][1], cap["line"][3]
    by1 = cap["block"][3]
    box_cy = (vlm_pts[1] + vlm_pts[3]) / 2
    cap_cy = (ly0 + ly1) / 2
    # caption below the visual -> cut at the caption's TOP; caption above (tables)
    # -> cut at the caption block's BOTTOM so all wrapped caption lines stay out.
    return ("below", ly0) if cap_cy >= box_cy else ("above", by1)


def _inter(a, b):
    ix0, iy0 = max(a[0], b[0]), max(a[1], b[1])
    ix1, iy1 = min(a[2], b[2]), min(a[3], b[3])
    if ix1 <= ix0 or iy1 <= iy0:
        return 0.0
    return (ix1 - ix0) * (iy1 - iy0)


def _area(r):
    return max(0.0, r[2] - r[0]) * max(0.0, r[3] - r[1])


def page_atoms(page, W, H):
    """Return clamped, de-noised ink-atom rects (PDF points) for one page."""
    atoms = []

    def add(rect, kind):
        x0, y0, x1, y1 = rect
        x0, x1 = sorted((max(0, min(x0, W)), max(0, min(x1, W))))
        y0, y1 = sorted((max(0, min(y0, H)), max(0, min(y1, H))))
        w, h = x1 - x0, y1 - y0
        if w < 2 and h < 2:
            return                                   # dot / speck
        # A thin line (table rule / axis / box edge) has ~zero area, so the
        # overlap test would divide by zero and the union would ignore it. Give
        # it nominal 1pt thickness so a table's top/bottom rules actually pull
        # the box up to enclose them.
        if h < 2:
            y0, y1 = y0 - 1.0, y1 + 1.0
        if w < 2:
            x0, x1 = x0 - 1.0, x1 + 1.0
        if y1 < 0.085 * H or y0 > 0.955 * H:
            return                                   # running head / page-number footer band
        # A vector path spanning most of the page is almost always a clipping
        # path / page background / column-straddling rule, NOT figure ink — it
        # drags the box across the gutter into the neighbouring column. Text and
        # raster-image atoms are always trustworthy, so only screen drawings.
        if kind == "draw" and (w > 0.55 * W or h > 0.55 * H):
            return
        atoms.append({"kind": kind, "rect": [x0, y0, x1, y1]})

    # text lines — present on every page, very accurate
    for blk in page.get_text("dict").get("blocks", []):
        if blk.get("type") != 0:
            continue
        for ln in blk.get("lines", []):
            add(ln["bbox"], "text")
    # embedded raster images
    for im in page.get_images(full=True):
        try:
            for r in page.get_image_rects(im[0]):
                add([r.x0, r.y0, r.x1, r.y1], "image")
        except Exception:
            pass
    # vector drawings (architecture diagrams, plots) — clamping kills the
    # off-page clipping-path garbage PyMuPDF sometimes reports
    for d in page.get_drawings():
        r = d.get("rect")
        if r is not None:
            add([r.x0, r.y0, r.x1, r.y1], "draw")
    return atoms


def refine_one(vlm_pts, atoms, W, H, cut=None):
    """Snap one VLM box (PDF points) to overlapping atoms. Returns (box, n_used).

    If `cut` is given, the caption is excluded from the snap (its text atoms are
    dropped from the union) and the box is trimmed so the caption stays out of
    the crop entirely.
    """
    def is_caption(r):
        if not cut:
            return False
        cy = (r[1] + r[3]) / 2
        return cy >= cut[1] - 1 if cut[0] == "below" else cy <= cut[1] + 1

    used = [a["rect"] for a in atoms
            if _area(a["rect"]) > 0 and not is_caption(a["rect"])
            and _inter(vlm_pts, a["rect"]) / _area(a["rect"]) >= OVERLAP]
    if not used:
        return vlm_pts, 0
    ux0 = min(r[0] for r in used); uy0 = min(r[1] for r in used)
    ux1 = max(r[2] for r in used); uy1 = max(r[3] for r in used)
    ex, ey = MAX_EXPAND * W, MAX_EXPAND * H
    # snap to union, but never move an edge out by more than ex/ey beyond the VLM box
    rx0 = max(ux0, vlm_pts[0] - ex)
    ry0 = max(uy0, vlm_pts[1] - ey)
    rx1 = min(ux1, vlm_pts[2] + ex)
    ry1 = min(uy1, vlm_pts[3] + ey)
    # hard caption exclusion: keep the crop edge clear of the caption text
    if cut and cut[0] == "below":
        ry1 = min(ry1, cut[1] - CAP_GAP)
    elif cut and cut[0] == "above":
        ry0 = max(ry0, cut[1] + CAP_GAP)
    if rx1 - rx0 < 4 or ry1 - ry0 < 4:
        return vlm_pts, 0
    return [rx0, ry0, rx1, ry1], len(used)


def main() -> int:
    import fitz
    ap = argparse.ArgumentParser()
    ap.add_argument("--pages-json", type=Path, required=True)
    ap.add_argument("--boxes", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--debug-atoms", type=Path)
    ap.add_argument("--keep-caption", action="store_true",
                    help="include the caption in the crop (default: trim it out so "
                         "caption text is not visible in the image)")
    args = ap.parse_args()

    meta = json.loads(args.pages_json.read_text())
    by_page = {e["page"]: e for e in meta["pages"]}
    boxes = json.loads(args.boxes.read_text())
    if isinstance(boxes, dict):
        boxes = boxes.get("boxes", [])
    doc = fitz.open(meta["pdf"])

    atoms_cache, debug = {}, {}
    out = []
    for b in boxes:
        pno = b["page"]; pe = by_page.get(pno)
        if pe is None:
            out.append(b); continue
        page = doc[pno - 1]
        W, H = page.rect.width, page.rect.height
        nh = pe["norm_h"]
        if pno not in atoms_cache:
            atoms_cache[pno] = page_atoms(page, W, H)
            debug[pno] = atoms_cache[pno]
        # normalized -> PDF points
        x0, y0, x1, y1 = b["bbox"]
        vlm_pts = [x0 / 1000 * W, y0 / nh * H, x1 / 1000 * W, y1 / nh * H]
        cut = None if args.keep_caption else caption_cut(
            vlm_pts, caption_rect(page, b.get("type", "figure"), b.get("label")))
        ref_pts, n_used = refine_one(vlm_pts, atoms_cache[pno], W, H, cut)
        # back to normalized
        nb = {**b, "bbox": [ref_pts[0] / W * 1000, ref_pts[1] / H * nh,
                            ref_pts[2] / W * 1000, ref_pts[3] / H * nh],
              "_refine": {"atoms_used": n_used, "orig_bbox": b["bbox"]}}
        out.append(nb)

    args.out.write_text(json.dumps(out, indent=2))
    if args.debug_atoms:
        args.debug_atoms.write_text(json.dumps(debug, indent=2))
    moved = sum(1 for o in out if o.get("_refine", {}).get("atoms_used"))
    print(json.dumps({"refined": len(out), "boxes_changed": moved,
                      "out": str(args.out)}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
