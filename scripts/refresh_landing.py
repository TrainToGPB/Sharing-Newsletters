#!/usr/bin/env python3
"""Refresh the versions block inside a post's slug-level abstract page.

A post folder layout:

    docs/<topic>/<slug>/
        index.md            -- abstract page (hand-written by the share-news skill)
        details/            -- detail series (folder, no index.md required)
            01-<part>.md
            02-<part>.md
            ...
        cards/              -- card-news (optional, from /card-news skill)
            index.md
        assets/
            ...

The slug-level index.md must contain markers:

    <!-- VERSIONS_START -->
    <!-- VERSIONS_END -->

This script scans details/<NN>-*.md (sorted by filename) and the optional
cards/index.md, then rewrites the block between the markers with a list of
ordered detail parts plus a card-news entry when present. The frontmatter
and rest of the body of the abstract page are left untouched.

Usage:
    python scripts/refresh_landing.py docs/agents/2026-05-10-foo/
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

try:
    import frontmatter
except ImportError:
    print("python-frontmatter not installed. Run: pip install python-frontmatter", file=sys.stderr)
    sys.exit(1)


PART_PATTERN = re.compile(r"^\d{2,}-.+\.md$")
MARK_START = "<!-- VERSIONS_START -->"
MARK_END = "<!-- VERSIONS_END -->"


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python scripts/refresh_landing.py <post-folder>", file=sys.stderr)
        return 1

    folder = Path(sys.argv[1]).resolve()
    if not folder.is_dir():
        print(f"not a folder: {folder}", file=sys.stderr)
        return 1

    landing = folder / "index.md"
    if not landing.is_file():
        print(f"missing abstract page: {landing}", file=sys.stderr)
        return 1

    text = landing.read_text(encoding="utf-8")
    if MARK_START not in text or MARK_END not in text:
        print(
            f"version markers not found in {landing}. "
            f"Add '{MARK_START}' and '{MARK_END}' lines.",
            file=sys.stderr,
        )
        return 1

    lines: list[str] = []

    # Detail series parts.
    details_dir = folder / "details"
    if details_dir.is_dir():
        parts = sorted(
            p for p in details_dir.iterdir()
            if p.is_file() and PART_PATTERN.match(p.name)
        )
        for i, p in enumerate(parts, 1):
            post = frontmatter.load(p)
            title = post.metadata.get("title", p.stem)
            summary = post.metadata.get("summary", "")
            url = f"details/{p.stem}/"
            line = f"{i}. [{title}]({url})"
            if summary:
                line += f" — {summary}"
            lines.append(line)

    # Card news.
    cards_landing = folder / "cards" / "index.md"
    if cards_landing.is_file():
        post = frontmatter.load(cards_landing)
        title = post.metadata.get("title", "카드 뉴스")
        summary = post.metadata.get("summary", "")
        line = f"- [{title}](cards/) (카드 뉴스)"
        if summary:
            line += f" — {summary}"
        if lines:
            lines.append("")  # blank line between sections
        lines.append(line)

    if not lines:
        block = "(아직 등록된 파트가 없다.)"
    else:
        block = "\n".join(lines)

    pattern = re.compile(
        rf"({re.escape(MARK_START)}).*?({re.escape(MARK_END)})",
        flags=re.DOTALL,
    )
    new_text = pattern.sub(rf"\1\n{block}\n\2", text, count=1)
    if new_text != text:
        landing.write_text(new_text, encoding="utf-8")
    print(f"refreshed versions in {landing}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
