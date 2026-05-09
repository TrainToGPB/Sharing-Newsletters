---
name: card-news
description: Generate a 4-6 image card-news series using OpenAI gpt-image-2 with the repo's locked visual style (see STYLE.md in this skill folder). Takes a source URL or local PDF (or an existing post slug), splits the key message into per-card prompts, generates images consistently using a shared seed, writes a markdown post that embeds the cards with captions, and refreshes the homepage. Use when user invokes /card-news or asks for "카드뉴스".
---

# card-news

URL · PDF · 기존 글 슬러그를 받아서 4~6장짜리 카드뉴스를 만든다. 비주얼 스타일은 `STYLE.md` 에 잠겨 있다 — 변경하려면 그 파일만 고친다.

## 호출 형태

```text
/card-news <source> [count=N] [topic=<folder>] [quality=low|medium|high] [seed=N]
```

- `<source>`: URL, 로컬 `.pdf`, 또는 이 레포 안의 기존 글 슬러그 (예: `mcp-overview`).
- `count`: 카드 수 (기본 5, 범위 4~6).
- `topic`: 결과 글이 들어갈 폴더. 미지정이면 자동 추정.
- `quality`: 기본 `medium` (~$0.04/장). `high` 는 약 4배 비쌈, 핵심 시리즈에만.
- `seed`: 시리즈 일관성용 정수. 미지정이면 자동 생성하고 결과 frontmatter 에 기록.

## 절차

### 0. 사전 점검

- `OPENAI_API_KEY` 가 환경변수 또는 `.env` 에 있는지 확인. 없으면 즉시 멈추고 사용자에게 알릴 것 (`scripts/gen_cards.py` 가 자동으로 `.env` 로드).
- 이 스킬 폴더 안의 `STYLE.md` 를 `Read` 로 통째로 읽어 STYLE_BLOCK / LAYOUT_BLOCK / CONSTRAINTS_BLOCK 을 확보.

### 1. 입력 검증과 컨텐츠 페치

- URL: `WebFetch` 로 본문 확보. arxiv 면 `arxiv.org/html/<id>` 로 자동 치환되는 `python scripts/parse_source.py <url> --out-md /tmp/parsed.md` 사용 가능.
- PDF: `python scripts/parse_source.py <pdf> --out-md /tmp/parsed.md` (그림은 카드뉴스에서 안 씀, `--assets-dir` 생략).
- 기존 슬러그: `docs/<topic>/<...>.md` 를 `Read`. 카드뉴스가 그 글의 시각화 버전이 됨.

### 2. 메타 결정

- **TOPIC_KO**: 4~8자 한글 라벨 (예: `AI 모델 업데이트`, `에이전트 도구`). 본문 톤에 맞게.
- **topic 폴더**: 인자 우선, 없으면 `docs/` 폴더 트리 비교로 추정.
- **slug**: 카드뉴스임을 알 수 있게 `<핵심어>-cards` 권장 (예: `opus-4-7-1m-cards`). 너무 길지 않게.
- **출력 경로**: `docs/<topic>/<YYYY-MM-DD>-<slug>.md`.
- **assets**: `docs/<topic>/<slug>-assets/card-N.png`.

### 3. 카드 내러티브 설계

`count` 장으로 핵심 메시지를 분할. 일반적 구조 (5장 기준).

1. 도입 — "무엇이 왔는가". 한 줄로 사건 요약.
2. 핵심 변화 — 가장 두드러진 한 가지.
3. 어떻게 — 구체적 수치 / 예시.
4. 왜 중요 — 우리에게의 영향.
5. 정리 / 다음 행동 — 한 문장 마무리.

각 카드별로 다음 4개 값을 정한다 (STYLE.md 의 길이 규칙 엄수).

- `HEADLINE_KO`: 한글 ~18자, 두 줄까지 가능 (`\n` 한 번).
- `BODY_KO`: 한글 ~22자, 한 줄.
- `ILLUSTRATION_HINT`: 영어 1~3 단어 — 본문 메타포로.
- 라벨용 `TOPIC_KO`: 시리즈 전체 동일 값.

### 4. 프롬프트 JSON 작성

`/tmp/<slug>-cards.json` 에 다음 형식으로 저장.

```json
[
  {
    "caption": "카드 아래에 마크다운으로 박힐 한 줄 캡션",
    "prompt": "<STYLE_BLOCK 그대로>\n\n<LAYOUT_BLOCK placeholder 채운 것>\n\n<CONSTRAINTS_BLOCK 그대로>"
  },
  ...
]
```

- STYLE_BLOCK 과 CONSTRAINTS_BLOCK 은 모든 카드에서 글자 단위로 동일해야 한다 (시리즈 일관성의 기둥).
- LAYOUT_BLOCK 은 카드마다 다른 값으로 채움. `{N}` / `{TOTAL}` 도 정확히 채울 것 (예: `1/5`, `2/5`...).
- 한글 텍스트는 반드시 따옴표 안에 그대로. 의역 금지.

### 5. 이미지 생성

```bash
python scripts/gen_cards.py \
    --slug <slug> \
    --assets-dir docs/<topic>/<slug>-assets \
    --prompts /tmp/<slug>-cards.json \
    --image-prefix <slug>-assets \
    --quality <quality> \
    --seed <seed>
```

기본값 (스크립트 안): `size=1024x1536`, `quality=medium`, `response_format=b64_json`. 시드를 명시 안 하면 스크립트가 랜덤으로 뽑아 표준출력 시작 줄에 `seed=<int>` 형식으로 보고. 그 시드를 frontmatter 에 기록.

스크립트 표준출력의 `![card N](...)` + 캡션 마크다운 블록을 받아 본문에 삽입.

### 6. 본문 작성

frontmatter.

```markdown
---
title: 제목 (시리즈 전체 한 문장으로 요약)
date: 2026-05-10
tags: [card-news, <소속 토픽>, ...추가 태그]
source: 원본-URL-또는-파일명
summary: 한 줄 요약
seed: 1234567
---
```

본문.

1. 도입 단락 1~2 문장 — 시리즈가 다루는 것을 한 호흡에. 카드 1 직전에 들어감.
2. 카드 5장을 순서대로 삽입. 각 카드 아래엔 캡션 (마크다운 italic 한 줄).
3. 카드 사이에는 짧은 본문 단락 (선택, 1~2문장) 을 끼워 카드만의 단순 나열을 피한다.
4. 마지막에 짧은 정리 한 단락.
5. `## 출처` 섹션에 원본 링크.

### 7. 인덱스와 마무리

```bash
python scripts/update_index.py
```

`git status` 로 변경 파일 보여주기. push 여부는 사용자 확인 후.

```bash
git add docs/<topic>/<YYYY-MM-DD>-<slug>.md docs/<topic>/<slug>-assets/ docs/index.md
git commit -m "cards(<topic>): <slug>"
git push
```

## 비용 가드

생성 직전에 사용자에게 예상 비용을 한 줄로 알릴 것.

- medium 5장 ≈ $0.20
- medium 6장 ≈ $0.25
- high 5장 ≈ $0.85
- high 6장 ≈ $1.00

medium 결과가 시각적으로 부족하면 부족한 카드만 `high` 로 재생성하는 방식이 효율적이다 (모든 카드를 high 로 다시 뽑지 말 것).

## 에러 처리

- `OPENAI_API_KEY` 누락: 즉시 멈추고 `.env.example` 안내.
- 한글이 깨진 카드: 해당 카드 프롬프트에서 헤드라인을 18자 이내로 더 줄이고, `\n` 으로 줄바꿈 위치를 명시한 뒤 재생성.
- 시리즈 톤이 카드끼리 흔들림: seed 를 동일하게 유지한 채 STYLE_BLOCK 이 카드마다 글자 단위로 같은지 다시 확인. 그래도 흔들리면 카드 1 결과를 reference 로 사용하는 옵션 (`gen_cards.py --reference-from-card 1`, 추후 추가) 활용.
- API 응답이 `b64_json` 도 `url` 도 없음: `scripts/gen_cards.py` 가 두 케이스를 모두 처리하도록 짜여 있음. 그래도 실패면 OpenAI 콘솔에서 모델 상태와 잔액 확인.

## 스타일 변경

색·폰트·레이아웃을 바꾸려면 이 스킬 폴더의 `STYLE.md` 만 수정. 다른 어디에도 색·폰트가 박혀 있지 않아야 한다 (이 SKILL.md 도 STYLE 정보를 인용하지 않고, 매번 STYLE.md 를 직접 읽어 사용한다).
