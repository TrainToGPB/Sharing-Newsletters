#!/usr/bin/env python3
"""Refresh the latest-posts list in docs/index.md.

Scans docs/ for .md files with frontmatter, sorts by date descending, and
rewrites the block between <!-- LATEST_START --> and <!-- LATEST_END --> in
docs/index.md.

Run from repo root:  python scripts/update_index.py
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


REPO = Path(__file__).resolve().parent.parent
DOCS = REPO / "docs"
INDEX = DOCS / "index.md"
MARK_START = "<!-- LATEST_START -->"
MARK_END = "<!-- LATEST_END -->"
LIMIT = 10
EMPTY_TEXT = "아직 글이 없다. `/auto-blog <URL>` 으로 첫 글을 추가해보자."


def collect_posts() -> list[dict]:
    posts = []
    for p in DOCS.rglob("*.md"):
        if p.name == "index.md":
            continue
        try:
            post = frontmatter.load(p)
        except Exception as exc:
            print(f"skip {p}: {exc}", file=sys.stderr)
            continue
        meta = post.metadata
        if not meta.get("date"):
            continue
        rel = p.relative_to(DOCS).with_suffix("")
        posts.append({
            "title": meta.get("title", p.stem),
            "date": str(meta["date"]),
            "summary": meta.get("summary", ""),
            "tags": meta.get("tags") or [],
            "url": str(rel).replace("\\", "/") + "/",
        })
    posts.sort(key=lambda x: x["date"], reverse=True)
    return posts


def render(posts: list[dict]) -> str:
    if not posts:
        return EMPTY_TEXT
    lines = []
    for p in posts[:LIMIT]:
        title = p["title"]
        url = p["url"]
        summary = p["summary"]
        tags = " ".join(f"`{t}`" for t in p["tags"])
        line = f"- **{p['date']}** [{title}]({url})"
        if summary:
            line += f" — {summary}"
        if tags:
            line += f" {tags}"
        lines.append(line)
    return "\n".join(lines)


def main() -> int:
    if not INDEX.exists():
        print(f"missing {INDEX}", file=sys.stderr)
        return 1
    text = INDEX.read_text(encoding="utf-8")
    if MARK_START not in text or MARK_END not in text:
        print(f"index markers not found in {INDEX}", file=sys.stderr)
        return 1

    posts = collect_posts()
    block = render(posts)
    pattern = re.compile(
        rf"({re.escape(MARK_START)}).*?({re.escape(MARK_END)})",
        flags=re.DOTALL,
    )
    new = pattern.sub(rf"\1\n{block}\n\2", text, count=1)
    if new != text:
        INDEX.write_text(new, encoding="utf-8")
    print(f"updated {INDEX} with {min(len(posts), LIMIT)} posts")
    return 0


if __name__ == "__main__":
    sys.exit(main())
