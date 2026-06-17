#!/usr/bin/env python3
"""Parse a URL or local PDF into markdown text, with optional figure extraction.

Usage:
    python scripts/parse_source.py <source> [options]

Options:
    --out-md <path>           Write markdown to this file (default: stdout).
    --assets-dir <path>       Directory to save extracted figures.
                              For URLs: inline content images are downloaded here
                              and refs in the markdown are rewritten to local paths.
                              For PDFs: PyMuPDF dumps embedded figures here.
    --image-prefix <str>      Markdown image href prefix (default: assets-dir name).

Source types:
    - http(s) URL  -> fetched, cleaned with trafilatura. Inline images get
                      downloaded to assets-dir when given.
                      arxiv.org/abs|pdf|html/<id>: the HTML version is probed
                      first and used if it exists; otherwise it falls back to
                      downloading the PDF and parsing that.
    - .pdf         -> Docling for text. PyMuPDF for image extraction.
                      Extracted figures listed in a "## Figures" block at end.

Downloaded/extracted images with transparency are flattened onto a white
background (dark-mode friendly).

Other file types (.md, .txt) are intentionally not supported. Paste their
content into a post manually if you need to.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from urllib.parse import urljoin, urlparse


# Common content-type to extension mapping for downloaded images.
_CT_TO_EXT = {
    "image/png": ".png",
    "image/jpeg": ".jpg",
    "image/jpg": ".jpg",
    "image/gif": ".gif",
    "image/webp": ".webp",
    "image/svg+xml": ".svg",
    "image/avif": ".avif",
}

# Markdown image syntax (ungreedy alt, simple url — no nested parens).
_IMG_PATTERN = re.compile(r"!\[([^\]]*)\]\(([^)\s]+)(?:\s+\"([^\"]*)\")?\)")


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


def arxiv_id(url: str) -> "str | None":
    """Return the arXiv id for an abs/pdf/html arXiv URL, else None."""
    m = re.match(
        r"https?://arxiv\.org/(?:abs|pdf|html)/([\w.\-/]+?)(?:\.pdf)?/?$", url
    )
    return m.group(1) if m else None


def _http_ok(url: str) -> bool:
    """True if `url` responds 200 (HEAD, falling back to GET on 405)."""
    import httpx

    headers = {"User-Agent": "Mozilla/5.0 SharingNewsletters/1.0"}
    try:
        r = httpx.head(url, follow_redirects=True, timeout=15.0, headers=headers)
        if r.status_code == 405:  # some servers reject HEAD
            r = httpx.get(url, follow_redirects=True, timeout=20.0, headers=headers)
        return r.status_code == 200
    except Exception:
        return False


def _flatten_to_white(path: Path) -> None:
    """Composite a transparent image onto a white background, in place.

    arXiv diagrams are often transparent PNGs that render on black in dark mode.
    No-op when Pillow is missing, the image is opaque, or the format (e.g. SVG)
    can't be opened by Pillow.
    """
    try:
        from PIL import Image
    except ImportError:
        return
    try:
        im = Image.open(path)
    except Exception:
        return
    has_alpha = im.mode in ("RGBA", "LA") or (
        im.mode == "P" and "transparency" in im.info
    )
    if not has_alpha:
        return
    try:
        rgba = im.convert("RGBA")
        bg = Image.new("RGBA", rgba.size, (255, 255, 255, 255))
        bg.alpha_composite(rgba)
        bg.convert("RGB").save(path)
    except Exception as exc:
        print(f"white-bg flatten failed: {path}: {exc}", file=sys.stderr)


def _download_inline_images(
    md: str,
    base_url: str,
    assets_dir: Path,
    image_prefix: str,
    min_bytes: int = 4096,
) -> str:
    """Download every ![](...) image in `md` to `assets_dir`, rewrite refs.

    Skips data: URIs and very small responses (likely icons/sprites).
    Leaves the original ref untouched on download failure.
    """
    import httpx

    assets_dir.mkdir(parents=True, exist_ok=True)
    counter = {"i": 0}
    headers = {"User-Agent": "Mozilla/5.0 SharingNewsletters/1.0"}

    def _replace(match: "re.Match[str]") -> str:
        alt = match.group(1)
        raw = match.group(2).strip()
        title = match.group(3) or ""

        if raw.startswith("data:"):
            return match.group(0)

        url = raw if raw.startswith(("http://", "https://")) else urljoin(base_url, raw)
        try:
            r = httpx.get(url, timeout=30.0, follow_redirects=True, headers=headers)
            if r.status_code != 200 or len(r.content) < min_bytes:
                return match.group(0)
            ct = r.headers.get("content-type", "").split(";")[0].strip().lower()
            ext = _CT_TO_EXT.get(ct) or Path(urlparse(url).path).suffix.lower() or ".png"
            counter["i"] += 1
            fname = f"fig-{counter['i']}{ext}"
            (assets_dir / fname).write_bytes(r.content)
            _flatten_to_white(assets_dir / fname)
            href = f"{image_prefix.rstrip('/')}/{fname}" if image_prefix else fname
        except Exception as exc:
            print(f"image fetch failed: {url}: {exc}", file=sys.stderr)
            return match.group(0)

        if title:
            return f'![{alt}]({href} "{title}")'
        return f"![{alt}]({href})"

    return _IMG_PATTERN.sub(_replace, md)


def parse_url(url: str, assets_dir: Path | None = None, image_prefix: str = "") -> str:
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
    final_url = str(r.url)
    extracted = trafilatura.extract(
        r.text,
        output_format="markdown",
        include_images=True,
        include_links=True,
        include_tables=True,
        with_metadata=False,
    )
    if not extracted:
        try:
            from bs4 import BeautifulSoup
        except ImportError:
            return r.text
        soup = BeautifulSoup(r.text, "html.parser")
        return soup.get_text("\n").strip()

    if assets_dir is not None:
        extracted = _download_inline_images(extracted, final_url, assets_dir, image_prefix)
    return extracted


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
                    _flatten_to_white(assets_dir / fname)
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


def parse_pdf_url(pdf_url: str, assets_dir: Path | None, image_prefix: str) -> str:
    """Download a remote PDF to a temp file and parse it like a local PDF."""
    import tempfile

    import httpx

    headers = {"User-Agent": "Mozilla/5.0 SharingNewsletters/1.0"}
    r = httpx.get(pdf_url, follow_redirects=True, timeout=60.0, headers=headers)
    r.raise_for_status()
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
        f.write(r.content)
        tmp = Path(f.name)
    try:
        return parse_pdf(tmp, assets_dir, image_prefix)
    finally:
        tmp.unlink(missing_ok=True)


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
        aid = arxiv_id(src)
        if aid is not None:
            html_url = f"https://arxiv.org/html/{aid}"
            if _http_ok(html_url):
                print(f"arxiv: using HTML version {html_url}", file=sys.stderr)
                md = parse_url(
                    html_url, assets_dir=args.assets_dir, image_prefix=image_prefix
                )
            else:
                pdf_url = f"https://arxiv.org/pdf/{aid}"
                print(
                    f"arxiv: no HTML page, falling back to PDF {pdf_url}",
                    file=sys.stderr,
                )
                md = parse_pdf_url(pdf_url, args.assets_dir, image_prefix)
        else:
            md = parse_url(src, assets_dir=args.assets_dir, image_prefix=image_prefix)
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
