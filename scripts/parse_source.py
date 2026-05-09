#!/usr/bin/env python3
"""Parse a URL or local PDF into markdown text, with optional figure extraction.

Usage:
    python scripts/parse_source.py <source> [options]

Options:
    --out-md <path>           Write markdown to this file (default: stdout).
    --assets-dir <path>       Directory to save extracted PDF figures.
    --image-prefix <str>      Markdown image href prefix (default: assets-dir name).

Source types:
    - http(s) URL  -> fetched, cleaned with trafilatura.
                      arxiv.org/abs/<id> is rewritten to arxiv.org/html/<id>.
    - .pdf         -> Docling for text. PyMuPDF for image extraction
                      when --assets-dir is given. Extracted figures are listed
                      in a "## Figures" block at the end of the output.

Other file types (.md, .txt) are intentionally not supported. Paste their
content into a post manually if you need to.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from urllib.parse import urlparse


def is_url(s: str) -> bool:
    try:
        u = urlparse(s)
        return u.scheme in ("http", "https")
    except Exception:
        return False


def rewrite_arxiv(url: str) -> str:
    m = re.match(r"https?://arxiv\.org/(?:abs|pdf)/([\w.\-/]+?)(?:\.pdf)?/?$", url)
    if m:
        return f"https://arxiv.org/html/{m.group(1)}"
    return url


def parse_url(url: str) -> str:
    import httpx
    try:
        import trafilatura
    except ImportError:
        print("trafilatura not installed. Run: pip install trafilatura", file=sys.stderr)
        sys.exit(1)

    url = rewrite_arxiv(url)
    headers = {"User-Agent": "Mozilla/5.0 SharingNewsletters/1.0"}
    r = httpx.get(url, follow_redirects=True, timeout=30.0, headers=headers)
    r.raise_for_status()
    extracted = trafilatura.extract(
        r.text,
        output_format="markdown",
        include_images=True,
        include_links=True,
        include_tables=True,
        with_metadata=False,
    )
    if extracted:
        return extracted

    try:
        from bs4 import BeautifulSoup
    except ImportError:
        return r.text
    soup = BeautifulSoup(r.text, "html.parser")
    return soup.get_text("\n").strip()


def docling_text(path: Path) -> str:
    try:
        from docling.document_converter import DocumentConverter
    except ImportError as exc:
        raise SystemExit(
            "Docling not installed. Install requirements first: pip install -r requirements.txt"
        ) from exc
    converter = DocumentConverter()
    result = converter.convert(str(path))
    return result.document.export_to_markdown()


def extract_pdf_figures(path: Path, assets_dir: Path, image_prefix: str) -> list[str]:
    """Dump unique embedded images via PyMuPDF. Returns markdown image refs."""
    try:
        import fitz  # PyMuPDF
    except ImportError as exc:
        raise SystemExit(
            "PyMuPDF not installed. Install requirements first: pip install -r requirements.txt"
        ) from exc

    assets_dir.mkdir(parents=True, exist_ok=True)
    refs: list[str] = []
    seen: set[int] = set()
    fig_count = 0
    doc = fitz.open(path)
    try:
        for page in doc:
            for img in page.get_images(full=True):
                xref = img[0]
                if xref in seen:
                    continue
                seen.add(xref)
                pix = fitz.Pixmap(doc, xref)
                try:
                    if pix.n - pix.alpha > 3:
                        pix = fitz.Pixmap(fitz.csRGB, pix)
                    fig_count += 1
                    fname = f"fig-{fig_count}.png"
                    pix.save(str(assets_dir / fname))
                    href = f"{image_prefix.rstrip('/')}/{fname}" if image_prefix else fname
                    refs.append(f"![figure {fig_count}]({href})")
                finally:
                    pix = None
    finally:
        doc.close()
    return refs


def parse_pdf(path: Path, assets_dir: Path | None, image_prefix: str) -> str:
    body = docling_text(path)
    if assets_dir is None:
        return body
    figs = extract_pdf_figures(path, assets_dir, image_prefix)
    if not figs:
        return body
    return body.rstrip() + "\n\n## Figures\n\n" + "\n\n".join(figs) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("source")
    ap.add_argument("--out-md", type=Path, default=None)
    ap.add_argument("--assets-dir", type=Path, default=None)
    ap.add_argument("--image-prefix", default=None)
    args = ap.parse_args()

    image_prefix = args.image_prefix
    if image_prefix is None and args.assets_dir is not None:
        image_prefix = args.assets_dir.name
    image_prefix = image_prefix or ""

    src = args.source
    if is_url(src):
        md = parse_url(src)
    else:
        p = Path(src).expanduser().resolve()
        if not p.exists():
            print(f"file not found: {p}", file=sys.stderr)
            return 1
        if p.suffix.lower() != ".pdf":
            print(
                f"unsupported file type: {p.suffix}. Only .pdf is supported for local files.",
                file=sys.stderr,
            )
            return 1
        md = parse_pdf(p, args.assets_dir, image_prefix)

    if args.out_md:
        args.out_md.parent.mkdir(parents=True, exist_ok=True)
        args.out_md.write_text(md, encoding="utf-8")
    else:
        sys.stdout.write(md)
    return 0


if __name__ == "__main__":
    sys.exit(main())
