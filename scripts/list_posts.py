#!/usr/bin/env python3
"""List posts in docs/ filtered by date range. Output: JSON to stdout.

Usage:
    python scripts/list_posts.py --period week [--ending 2026-05-10]
    python scripts/list_posts.py --period month [--ending 2026-05-10]
    python scripts/list_posts.py --from 2026-05-01 --to 2026-05-10
    python scripts/list_posts.py --period week --topic agents

The `digest/` folder is always excluded so digests do not reference each other.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

try:
    import frontmatter
except ImportError:
    print("python-frontmatter not installed. Run: pip install python-frontmatter", file=sys.stderr)
    sys.exit(1)


REPO = Path(__file__).resolve().parent.parent
DOCS = REPO / "docs"
DIGEST_FOLDER = "digest"


def parse_date(s: str) -> dt.date:
    return dt.date.fromisoformat(s)


def derive_range(period: str, ending: dt.date | None) -> tuple[dt.date, dt.date]:
    end = ending or dt.date.today()
    if period == "week":
        start = end - dt.timedelta(days=6)
    elif period == "month":
        start = end.replace(day=1)
    else:
        raise ValueError(f"unknown period: {period}")
    return start, end


def post_url(rel: Path) -> str:
    """Folder layout: docs/<topic>/<slug>/index.md -> <topic>/<slug>/
    Flat (legacy):     docs/<topic>/<slug>.md       -> <topic>/<slug>/
    """
    if rel.name == "index.md":
        return str(rel.parent).replace("\\", "/") + "/"
    return str(rel.with_suffix("")).replace("\\", "/") + "/"


def collect(start: dt.date, end: dt.date, topic: str | None) -> list[dict]:
    posts: list[dict] = []
    for p in DOCS.rglob("*.md"):
        rel = p.relative_to(DOCS)
        if not rel.parts:
            continue
        # Same depth rule as update_index.py: skip homepage/topic landings
        # and anything under a format subfolder.
        if rel.name == "index.md" and len(rel.parts) <= 2:
            continue
        if len(rel.parts) >= 4:
            continue
        first = rel.parts[0]
        if first == DIGEST_FOLDER:
            continue
        if topic and first != topic:
            continue
        try:
            post = frontmatter.load(p)
        except Exception as exc:
            print(f"skip {p}: {exc}", file=sys.stderr)
            continue
        d = post.metadata.get("date")
        if not d:
            continue
        try:
            pd = parse_date(str(d))
        except Exception:
            continue
        if not (start <= pd <= end):
            continue
        posts.append({
            "title": post.metadata.get("title", p.stem),
            "date": str(d),
            "author": post.metadata.get("author", ""),
            "tags": post.metadata.get("tags") or [],
            "summary": post.metadata.get("summary", ""),
            "source": post.metadata.get("source", ""),
            "topic": first,
            "url": post_url(rel),
            "path": str(rel).replace("\\", "/"),
        })
    posts.sort(key=lambda x: x["date"], reverse=True)
    return posts


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--from", dest="frm")
    ap.add_argument("--to")
    ap.add_argument("--period", choices=["week", "month"])
    ap.add_argument("--ending")
    ap.add_argument("--topic")
    args = ap.parse_args()

    if args.period:
        ending = parse_date(args.ending) if args.ending else None
        start, end = derive_range(args.period, ending)
    elif args.frm and args.to:
        start, end = parse_date(args.frm), parse_date(args.to)
    else:
        print("Either --period or --from/--to is required", file=sys.stderr)
        return 1

    posts = collect(start, end, args.topic)
    out = {
        "from": str(start),
        "to": str(end),
        "topic": args.topic,
        "count": len(posts),
        "posts": posts,
    }
    sys.stdout.write(json.dumps(out, ensure_ascii=False, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
