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
      {
        "caption": "한 줄 캡션",
        "prompt": "전체 프롬프트 (STYLE + LAYOUT + CONSTRAINTS)",
        "reference_image": "docs/.../assets/fig-1.png"   // optional
      },
      ...
    ]

When reference_image is present, gen_cards.py uses images.edit() (Mode A —
the supplied figure is recomposed into the card with our style). When it
is absent, gen_cards.py uses images.generate() (Mode B — schematic drawn
from the prompt alone).

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


def _decode_response(resp) -> bytes:
    """Pull image bytes out of an OpenAI images response."""
    import httpx

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


def _generate(
    client,
    *,
    model: str,
    prompt: str,
    size: str,
    quality: str,
    seed: int,
    reference_image: Path | None = None,
) -> bytes:
    """One image generation call. If reference_image is given, use
    images.edit() (Mode A — reference-based composition). Otherwise use
    images.generate() (Mode B — schematic generation).

    gpt-image-2 returns b64_json by default and rejects an explicit
    response_format parameter. seed is supported; we fall back without
    it if the local SDK doesn't recognise the kwarg.
    """
    common: dict = {
        "model": model,
        "prompt": prompt,
        "size": size,
        "quality": quality,
        "n": 1,
    }

    if reference_image is not None:
        with open(reference_image, "rb") as f:
            try:
                resp = client.images.edit(image=f, **common, seed=seed)
            except TypeError:
                f.seek(0)
                resp = client.images.edit(image=f, **common)
    else:
        try:
            resp = client.images.generate(**common, seed=seed)
        except TypeError:
            resp = client.images.generate(**common)

    return _decode_response(resp)


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
    # Empty string means "no prefix" — refs become bare card-N.png. Default to
    # the assets-dir basename when caller didn't pass --image-prefix at all.
    if args.image_prefix is None:
        image_prefix = args.assets_dir.name.rstrip("/")
    else:
        image_prefix = args.image_prefix.rstrip("/")

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
        ref_path_str = item.get("reference_image") or None
        ref_path = Path(ref_path_str).expanduser() if ref_path_str else None
        if ref_path is not None and not ref_path.is_absolute():
            ref_path = Path.cwd() / ref_path
        if ref_path is not None and not ref_path.is_file():
            print(f"prompt #{i}: reference_image not found: {ref_path}", file=sys.stderr)
            return 1
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
                reference_image=ref_path,
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
