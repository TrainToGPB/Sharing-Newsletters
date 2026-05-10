#!/usr/bin/env python3
"""Refresh the latest-posts list (and optional card-news preview) in docs/index.md.

Scans docs/ for post landings, sorts by date descending, then:
1. Rewrites the block between <!-- LATEST_START --> and <!-- LATEST_END --> with
   a text-style list of recent posts.
2. If <!-- CARDS_START --> / <!-- CARDS_END --> markers also exist, rewrites that
   block with a Material grid-cards gallery of recent posts that have a
   cards/ subfolder. Skipped silently if the markers aren't present.
3. For each topic landing page (docs/<topic>/index.md) that contains
   <!-- TOPIC_POSTS_START --> / <!-- TOPIC_POSTS_END -->, rewrites that block
   with a date-descending table of posts in that topic.

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

LATEST_START = "<!-- LATEST_START -->"
LATEST_END = "<!-- LATEST_END -->"
CARDS_START = "<!-- CARDS_START -->"
CARDS_END = "<!-- CARDS_END -->"
TOPIC_POSTS_START = "<!-- TOPIC_POSTS_START -->"
TOPIC_POSTS_END = "<!-- TOPIC_POSTS_END -->"

LIMIT = 10
LIMIT_CARDS = 6
EMPTY_TEXT = "아직 글이 없다. `/share-news <URL>` 으로 첫 글을 추가해보자."
EMPTY_CARDS_TEXT = "아직 카드 뉴스가 없다. `/card-news <source>` 로 첫 카드를 만들어보자."
EMPTY_TOPIC_TEXT = "아직 이 토픽에 글이 없다."


def post_url(rel: Path) -> str:
    """Map a post path under docs/ to its site URL.

    Folder layout:  docs/<topic>/<slug>/index.md  -> <topic>/<slug>/
    Flat (legacy):  docs/<topic>/<slug>.md        -> <topic>/<slug>/
    """
    if rel.name == "index.md":
        return str(rel.parent).replace("\\", "/") + "/"
    return str(rel.with_suffix("")).replace("\\", "/") + "/"


def collect_posts() -> list[dict]:
    """Latest list shows post landing pages (or single-format posts).
    Version subpages (depth-4 index.md under <slug>/<format>/index.md) are
    intentionally skipped — the landing represents the post for the index.
    """
    posts = []
    for p in DOCS.rglob("*.md"):
        rel = p.relative_to(DOCS)
        # Skip homepage / topic landing.
        if rel.name == "index.md" and len(rel.parts) <= 2:
            continue
        # Skip everything under a format subfolder — version subpages, deep
        # series landings, deep series parts, etc. The slug-level landing
        # (depth-3 index.md) represents the post in the latest list.
        if len(rel.parts) >= 4:
            continue
        try:
            post = frontmatter.load(p)
        except Exception as exc:
            print(f"skip {p}: {exc}", file=sys.stderr)
            continue
        meta = post.metadata
        if not meta.get("date"):
            continue
        # has_cards: post folder has cards/index.md and cards/card-1.png.
        post_dir = p.parent if rel.name == "index.md" else p.with_suffix("")
        cards_index = post_dir / "cards" / "index.md"
        card_thumb = post_dir / "cards" / "card-1.png"
        has_cards = cards_index.is_file() and card_thumb.is_file()
        topic = rel.parts[0] if rel.parts else ""
        posts.append({
            "title": meta.get("title", p.stem),
            "date": str(meta["date"]),
            "author": meta.get("author", ""),
            "summary": meta.get("summary", ""),
            "tags": meta.get("tags") or [],
            "url": post_url(rel),
            "topic": topic,
            "has_cards": has_cards,
        })
    posts.sort(key=lambda x: x["date"], reverse=True)
    return posts


def render_latest(posts: list[dict]) -> str:
    if not posts:
        return EMPTY_TEXT
    lines = []
    for p in posts[:LIMIT]:
        title = p["title"]
        url = p["url"]
        summary = p["summary"]
        author = p.get("author", "")
        tags = " ".join(f"`{t}`" for t in p["tags"])
        line = f"- **{p['date']}** [{title}]({url})"
        if author:
            line += f" · _{author}_"
        if summary:
            line += f" — {summary}"
        if tags:
            line += f" {tags}"
        lines.append(line)
    return "\n".join(lines)


def render_cards(posts: list[dict]) -> str:
    cards_posts = [p for p in posts if p.get("has_cards")]
    if not cards_posts:
        return EMPTY_CARDS_TEXT
    lines = ['<div class="grid cards" markdown>', ""]
    for p in cards_posts[:LIMIT_CARDS]:
        thumb = f"{p['url']}cards/card-1.png"
        cards_link = f"{p['url']}cards/"
        title = p["title"]
        author = p.get("author", "")
        date = p["date"]
        lines.append(f"- [![]({thumb})]({cards_link})")
        lines.append("")
        meta_line = f"  **[{title}]({p['url']})**"
        meta_line += f" · {date}"
        if author:
            meta_line += f" · _{author}_"
        lines.append(meta_line)
        lines.append("")
    lines.append("</div>")
    return "\n".join(lines)


def render_topic_table(posts: list[dict]) -> str:
    if not posts:
        return EMPTY_TOPIC_TEXT
    lines = [
        "| 날짜 | 제목 | 요약 |",
        "| --- | --- | --- |",
    ]
    for p in posts:
        rel_url = p["url"]
        prefix = f"{p['topic']}/"
        if rel_url.startswith(prefix):
            rel_url = rel_url[len(prefix):]
        title = p["title"].replace("|", "\\|")
        summary = (p.get("summary") or "").replace("|", "\\|").replace("\n", " ")
        lines.append(f"| {p['date']} | [{title}]({rel_url}) | {summary} |")
    return "\n".join(lines)


def update_topic_landings(posts: list[dict]) -> int:
    updated = 0
    for topic_dir in sorted(p for p in DOCS.iterdir() if p.is_dir()):
        landing = topic_dir / "index.md"
        if not landing.is_file():
            continue
        text = landing.read_text(encoding="utf-8")
        if TOPIC_POSTS_START not in text or TOPIC_POSTS_END not in text:
            continue
        topic = topic_dir.name
        topic_posts = [p for p in posts if p.get("topic") == topic]
        body = render_topic_table(topic_posts)
        new_text = _replace_block(text, TOPIC_POSTS_START, TOPIC_POSTS_END, body)
        if new_text != text:
            landing.write_text(new_text, encoding="utf-8")
            updated += 1
    return updated


def _replace_block(text: str, start: str, end: str, body: str) -> str:
    pattern = re.compile(
        rf"({re.escape(start)}).*?({re.escape(end)})",
        flags=re.DOTALL,
    )
    replacement = f"{start}\n{body}\n{end}"
    return pattern.sub(lambda _m: replacement, text, count=1)


def main() -> int:
    if not INDEX.exists():
        print(f"missing {INDEX}", file=sys.stderr)
        return 1
    text = INDEX.read_text(encoding="utf-8")
    if LATEST_START not in text or LATEST_END not in text:
        print(f"latest markers not found in {INDEX}", file=sys.stderr)
        return 1

    posts = collect_posts()

    new_text = _replace_block(text, LATEST_START, LATEST_END, render_latest(posts))
    if CARDS_START in new_text and CARDS_END in new_text:
        new_text = _replace_block(new_text, CARDS_START, CARDS_END, render_cards(posts))
        cards_count = sum(1 for p in posts if p.get("has_cards"))
        cards_msg = f", {min(cards_count, LIMIT_CARDS)} cards"
    else:
        cards_msg = ""

    if new_text != text:
        INDEX.write_text(new_text, encoding="utf-8")
    topic_updated = update_topic_landings(posts)
    print(
        f"updated {INDEX} with {min(len(posts), LIMIT)} posts{cards_msg}; "
        f"refreshed {topic_updated} topic landing(s)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
