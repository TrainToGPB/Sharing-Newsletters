#!/usr/bin/env python3
"""Generate card-news images via OpenAI's gpt-image-2 API.

Usage:
    python scripts/gen_cards.py \
        --slug <slug> \
        --assets-dir <path> \
        --prompts <prompts.json> \
        [--image-prefix <str>] \
        [--model gpt-image-2] \
        [--size 1024x1536] \
        [--quality medium] \
        [--seed <int>]

prompts.json format:
    [
      {"caption": "한 줄 캡션", "prompt": "전체 프롬프트 (STYLE + LAYOUT + CONSTRAINTS)"},
      ...
    ]

Outputs:
    <assets-dir>/card-1.png ... card-N.png
    First stdout line: "seed=<int>"  (for the calling skill to record).
    Then markdown image+caption block on stdout.

Defaults are tuned for the repo's locked card-news style (see
.claude/skills/card-news/STYLE.md): portrait 1024x1536, medium quality,
b64_json response. Seed defaults to a freshly generated random int so
all cards in one invocation share visual tone.

Requires OPENAI_API_KEY (env var or .env in repo root).
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import random
import sys
from pathlib import Path


def _load_env_file() -> None:
    """Load OPENAI_API_KEY etc from a .env file if python-dotenv is installed."""
    try:
        from dotenv import find_dotenv, load_dotenv
    except ImportError:
        return
    path = find_dotenv(usecwd=True)
    if path:
        load_dotenv(path, override=False)


def _generate(client, *, model: str, prompt: str, size: str, quality: str, seed: int) -> bytes:
    """One image-generation call. Returns raw image bytes."""
    import httpx

    common: dict = {
        "model": model,
        "prompt": prompt,
        "size": size,
        "quality": quality,
        "n": 1,
        "response_format": "b64_json",
    }
    # gpt-image-2 supports `seed`. If the SDK or model rejects it, retry
    # without to avoid hard-failing on minor SDK version differences.
    try:
        resp = client.images.generate(**common, seed=seed)
    except TypeError:
        resp = client.images.generate(**common)

    item = resp.data[0]
    b64 = getattr(item, "b64_json", None)
    if b64:
        return base64.b64decode(b64)
    url = getattr(item, "url", None)
    if not url:
        raise RuntimeError("image response had neither b64_json nor url")
    r = httpx.get(url, timeout=60.0)
    r.raise_for_status()
    return r.content


def main() -> int:
    _load_env_file()
    ap = argparse.ArgumentParser()
    ap.add_argument("--slug", required=True)
    ap.add_argument("--assets-dir", type=Path, required=True)
    ap.add_argument("--prompts", type=Path, required=True)
    ap.add_argument("--image-prefix", default=None)
    ap.add_argument("--model", default=os.environ.get("OPENAI_IMAGE_MODEL", "gpt-image-2"))
    ap.add_argument("--size", default="1024x1536")
    ap.add_argument("--quality", default="medium", choices=["low", "medium", "high", "auto"])
    ap.add_argument("--seed", type=int, default=None,
                    help="Series consistency seed. If omitted, a random int is generated and printed.")
    args = ap.parse_args()

    if not os.environ.get("OPENAI_API_KEY"):
        print("OPENAI_API_KEY not set. Put it in repo .env or export it.", file=sys.stderr)
        return 2

    try:
        from openai import OpenAI
    except ImportError:
        print("openai package not installed. Run: pip install openai", file=sys.stderr)
        return 1

    args.assets_dir.mkdir(parents=True, exist_ok=True)
    image_prefix = (args.image_prefix or args.assets_dir.name).rstrip("/")

    try:
        prompts = json.loads(args.prompts.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"failed to read prompts file: {exc}", file=sys.stderr)
        return 1
    if not isinstance(prompts, list) or not prompts:
        print("prompts.json must be a non-empty list", file=sys.stderr)
        return 1

    seed = args.seed if args.seed is not None else random.randint(1, 2**31 - 1)
    sys.stdout.write(f"seed={seed}\n")
    sys.stdout.flush()

    client = OpenAI()
    md_lines: list[str] = []
    for i, item in enumerate(prompts, start=1):
        prompt = item.get("prompt")
        caption = item.get("caption", "")
        if not prompt:
            print(f"prompt #{i} is missing 'prompt' field", file=sys.stderr)
            return 1

        try:
            data = _generate(
                client,
                model=args.model,
                prompt=prompt,
                size=args.size,
                quality=args.quality,
                seed=seed,
            )
        except Exception as exc:
            print(f"image #{i} generation failed: {exc}", file=sys.stderr)
            return 1

        out = args.assets_dir / f"card-{i}.png"
        out.write_bytes(data)
        md_lines.append(f"![card {i}]({image_prefix}/card-{i}.png)")
        if caption:
            md_lines.append(f"*{caption}*")
        md_lines.append("")

    sys.stdout.write("\n".join(md_lines).rstrip() + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
