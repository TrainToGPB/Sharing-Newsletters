---
name: card-news
description: Generate a 4-6 image card-news series using OpenAI gpt-image-2 with the repo's locked visual style (see STYLE.md in this skill folder). Adds a cards/ subfolder to an existing post (created by /share-news) or to a new slug. Splits the key message into per-card prompts, generates images consistently using a shared seed, writes a markdown post that embeds the cards with captions, and refreshes the homepage. Use the planning subagent to keep main context lean. Use when user invokes /card-news or asks for "카드뉴스".
---

# card-news

URL · PDF · 기존 슬러그를 받아 4~6장짜리 카드뉴스를 만든다. 결과는 글-루트의 `cards/index.md` + `assets/card-N.png`. 비주얼 스타일은 `STYLE.md` 에 잠겨 있다 — 변경하려면 그 파일만 고친다.

## 호출 형태

```text
/card-news <source> [count=N] [topic=<folder>] [quality=low|medium|high] [seed=N]
```

- `<source>`: URL, 로컬 `.pdf`, 또는 기존 글 슬러그 (예: `ai-co-mathematician`).
- `count`: 카드 수 (기본 5, 범위 4~6).
- `topic`: 결과 글이 들어갈 폴더. 미지정이면 자동 추정. 기존 슬러그 사용 시 그 슬러그의 토픽 그대로.
- `quality`: 기본 `medium` (~$0.04/장). `high` 는 약 4배 비쌈.
- `seed`: 시리즈 일관성용 정수. 미지정이면 자동 생성하고 frontmatter 에 기록.

## 출력 위치

```
docs/<topic>/<YYYY-MM-DD>-<slug>/
  index.md            # share-news 가 만든 abstract (있으면 갱신, 없으면 minimal 한 abstract 생성)
  details/...         # share-news 가 만든 details (있을 수 있음)
  cards/
    index.md          # 카드뉴스 본문
    card-1.png ... card-N.png   # 카드 이미지 (cards/ 안 같은 폴더)
  assets/
    fig-N.png ...     # share-news 가 만든 PDF/원본 그림. 카드뉴스가 reference 로 사용 가능
```

`cards/` 는 항상 서브폴더. 카드 이미지도 `cards/` 안 같은 폴더에 두고 본문은 bare 파일명으로 참조.

## 절차

### 0. 사전 점검

- `OPENAI_API_KEY` 가 환경변수 또는 레포 루트 `.env` 에 있는지 확인. 없으면 즉시 멈추고 `.env.example` 안내.
- 이 스킬 폴더의 `STYLE.md` 를 `Read` 로 읽어 STYLE_BLOCK / LAYOUT_BLOCK / CONSTRAINTS_BLOCK 확보.

### 1. 입력 검증

- URL: 스킴 확인. arxiv `abs/pdf` → `html` 자동 치환은 `parse_source.py` 가 처리.
- PDF: `.pdf` 인지 확인.
- 기존 슬러그: `docs/<topic>/<...>/index.md` (abstract) 가 있는지 확인. 없으면 사용자에게 `/share-news` 를 먼저 돌릴지 물음.

### 2. 컨텐츠 페치

본문은 카드 메시지 분할용이므로 정확한 본문 텍스트만 있으면 됨. 그림은 카드뉴스 자체에선 안 씀 (gen_cards.py 가 새로 그림).

```bash
# URL / PDF
python scripts/parse_source.py <source> --out-md /tmp/parsed.md
# 기존 슬러그면 abstract 페이지를 직접 Read
```

### 3. 메타 결정

- **TOPIC_KO**: 4~8자 한글 라벨 (예: `AI 모델 업데이트`). 카드 좌상단 라벨로 들어감.
- **topic 폴더**: 인자 우선, 없으면 자동 추정 또는 기존 슬러그의 토픽 그대로.
- **slug**: 영문 핵심어 kebab-case. **`-cards` 같은 포맷 접미사 금지** — 같은 글이면 share-news 와 같은 슬러그 공유.
- **작성자**: `git config user.name`.
- **출력 경로 (본문)**: `docs/<topic>/<YYYY-MM-DD>-<slug>/cards/index.md` (항상 서브폴더).
- **출력 경로 (카드 이미지)**: `docs/<topic>/<YYYY-MM-DD>-<slug>/cards/card-N.png` (cards/ 안 같은 폴더). 본문에선 bare 파일명 (`card-1.png`) 으로 참조.

기존 슬러그 폴더가 없으면 새로 생성한다 (이 경우 abstract 가 없으므로 4단계에서 minimal 버전을 같이 만든다).

### 4. 카드 내러티브 + 프롬프트 JSON 작성 — subagent 위임 (권장)

**카드 한 장 = 정보 단위 한 개**. 헤드라인 슬로건이 아니라 작은 그림 (또는 도식) + 개조식 불릿 3~5개로 한 가지 개념을 전달한다. 카드별 그림 소스는 두 가지 모드 중 선택.

- **Mode A (Reference 모드)**: 원문에 좋은 그림 (`<slug>/assets/fig-N.png`) 이 있으면 그걸 `reference_image` 로 전달. 모델이 우리 line-art 스타일로 재해석해 카드 가운데에 박는다.
- **Mode B (Schematic 모드)**: 원문에 쓸 만한 그림이 없거나 추상 개념을 시각화하고 싶을 때. 도식의 구조·라벨을 텍스트로 묘사해 모델이 직접 그리게 한다.

#### Subagent 프롬프트 템플릿

```
역할: Sharing-Newsletters 카드뉴스용 프롬프트 JSON 작성.

입력:
- 원문: /tmp/parsed.md (또는 기존 abstract / details 경로)
- 사용 가능 그림: docs/<topic>/<slug>/assets/ 안의 fig-N.png 목록과 각각의 의미
- 스타일 가이드: .claude/skills/card-news/STYLE.md (Read 로 통째로 읽기 — STYLE_BLOCK / LAYOUT_BLOCK Mode A·B / CONSTRAINTS_BLOCK 추출)
- 시리즈 길이: <count> 장
- TOPIC_KO: <라벨>
- 슬러그 폴더 경로: docs/<topic>/<slug>/

출력 파일: /tmp/<slug>-cards.json

작업:

1. 원문 핵심을 <count> 장으로 분할. 카드 1장에 정보 1개. 흐름 권장: 도입·아키텍처 → 동작 → 결과 → 시사점.

2. 각 카드별로 모드 선택.
   - 본문 그림 중 그 카드 메시지를 직접 보여주는 게 있으면 Mode A (그 fig-N.png 를 reference_image 로 전달).
   - 없으면 Mode B (도식을 텍스트로 묘사).

3. 각 카드의 컨텐츠 결정.
   - HEADLINE_KO: 한글 12~16자, 한 줄. 그림의 부제목 역할 (작게 박힘).
   - BULLETS: 3~5개. 각 한글 20~30자. 그림이 보여주는 핵심을 개조식으로 풀어 설명.
   - caption (마크다운에 박힐 한 줄): 한글 한 문장, 카드 아래 italic.
   - Mode B 면 추가로:
     - SCHEMATIC_DESC: 영어 한 줄 — 어떤 도식 (예: "horizontal flow diagram of 4 nodes connected by arrows")
     - SCHEMATIC_LABELS: 도식 안에 들어갈 한글 라벨 목록 (정확한 문자열 그대로).

4. 각 카드 prompt = STYLE_BLOCK + 빈 줄 + LAYOUT_BLOCK (Mode A 또는 B 의 것, placeholder 채운 것) + 빈 줄 + CONSTRAINTS_BLOCK.
   - STYLE_BLOCK / CONSTRAINTS_BLOCK 은 글자 단위로 모든 카드에서 동일.
   - LAYOUT_BLOCK 의 {N}, {TOTAL}, {TOPIC_KO}, {HEADLINE_KO}, {BULLETS} (그리고 Mode B 면 {SCHEMATIC_DESC}, {SCHEMATIC_LABELS}) 만 카드별로 다르게 채움.
   - {BULLETS} 는 다음 형식 (각 줄이 그대로 카드에 박힘):
       - 첫 번째 불릿
       - 두 번째 불릿
       - 세 번째 불릿
   - 한글 텍스트는 따옴표 안에 그대로. 의역 금지.

5. JSON 형식: 배열
   [{
     "caption": "...",
     "prompt": "...",
     "reference_image": "docs/<topic>/<slug>/assets/fig-N.png"   // Mode A 만, Mode B 면 omit 또는 null
   }, ...]
   reference_image 경로는 레포 루트 기준 상대 경로 또는 절대 경로 둘 다 허용 (gen_cards.py 가 cwd 기준 상대 경로도 절대로 해석).

출력하지 말 것: 작업 진행 보고나 카드 내용 미리 보기. 파일 작성 후 한 줄 ("written: /tmp/<slug>-cards.json, <count> cards (mode A: <a>, mode B: <b>)") 만.
```

### 5. 비용 가드

생성 직전에 사용자에게 한 줄로 비용 알릴 것.

| count × quality | 예상 비용 |
| --- | --- |
| 5 × medium | ≈ $0.20 |
| 6 × medium | ≈ $0.25 |
| 5 × high | ≈ $0.85 |
| 6 × high | ≈ $1.00 |

medium 결과가 부족하면 부족한 카드만 high 로 재생성. 모두 다시 뽑지 말 것.

### 6. 이미지 생성

```bash
python scripts/gen_cards.py \
    --slug <slug> \
    --assets-dir docs/<topic>/<YYYY-MM-DD>-<slug>/cards \
    --prompts /tmp/<slug>-cards.json \
    --image-prefix "" \
    --quality <quality> \
    --seed <seed>
```

`--assets-dir` 는 카드 이미지가 저장될 폴더 (cards/). `--image-prefix ""` 로 빈 문자열을 넘겨 본문 ref 가 bare 파일명 (`card-1.png`) 이 되게 한다. 기본값 (스크립트 안): `size=1024x1536`, `quality=medium`. gpt-image-2 는 `response_format` 파라미터를 거부하므로 안 보냄. seed 미명시 시 스크립트가 랜덤 정수 → 표준출력 첫 줄 `seed=<int>` 로 보고. 그 값을 frontmatter `seed` 필드에 기록.

reference image (Mode A) 는 JSON 의 각 카드 객체 `reference_image` 필드로 전달되므로 CLI 인자로는 안 넘김.

스크립트 표준출력의 `![card N](...)` + 캡션 마크다운 블록을 받아 본문에 삽입.

### 7. cards/index.md 본문 작성

```markdown
---
title: <카드뉴스 제목 — 시리즈 한 문장으로>
date: 2026-05-10
author: <git user.name>
tags: [card-news, <소속 토픽>, ...]
source: <원본>
summary: <한 줄 요약>
format: cards
seed: <int>
---

# <카드뉴스 제목>

> 원본: [<도메인 또는 짧은 라벨>](<원본 URL>)

<도입 1~2문장. 카드 1 직전.>

![card 1](card-1.png)
*카드 1 캡션*

<카드 사이 짧은 단락 (선택, 1~2문장)>

![card 2](card-2.png)
*카드 2 캡션*

...

<마지막에 짧은 정리 한 단락>

## 출처

- <source>
```

### 8. abstract 갱신

기존 슬러그였다면 `<slug>/index.md` (abstract) 는 이미 있음. 카드 추가는 `refresh_landing.py` 가 자동 처리한다 — abstract 의 `<!-- VERSIONS_START -->` 블록에 카드 링크가 자동 추가됨.

기존 슬러그가 아니었다면 (이 카드가 그 글의 첫 컨텐츠), minimal abstract 를 같이 만들어둔다.

```markdown
---
title: <글 전체 제목>
date: 2026-05-10
author: <git user.name>
tags: [...]
source: <source>
summary: <한 줄 요약>
format: abstract
---

# <글 전체 제목>

> 원본: [<도메인 또는 짧은 라벨>](<원본 URL>)

<한 문장 도입>

## 자세히 보기

<!-- VERSIONS_START -->
<!-- VERSIONS_END -->

## 출처

- <source>
```

### 9. 자동 갱신 + 마무리

```bash
python scripts/refresh_landing.py docs/<topic>/<YYYY-MM-DD>-<slug>/
python scripts/update_index.py
```

`git status` 로 변경 파일. push 여부 사용자 확인 후.

```bash
git add docs/<topic>/<YYYY-MM-DD>-<slug>/ docs/index.md
git commit -m "cards(<topic>): <slug>"
git push
```

## 에러 처리

- `OPENAI_API_KEY` 누락: 즉시 멈추고 `.env.example` 안내.
- 한글 깨진 카드: 해당 카드 헤드라인을 18자 이내로 더 줄이고 `\n` 으로 줄바꿈 위치 명시 후 재생성.
- 시리즈 톤이 카드끼리 흔들림: seed 동일·STYLE_BLOCK 카드별 글자 단위 동일 확인. 그래도 흔들리면 카드 1 결과를 reference 로 사용하는 옵션 (`gen_cards.py` 차후 추가) 활용.
- gen_cards.py API 응답이 `b64_json` 도 `url` 도 없음: 스크립트가 두 케이스 모두 처리. 그래도 실패면 OpenAI 콘솔에서 모델 상태·잔액 확인.

## 스타일 변경

색·폰트·레이아웃 변경은 이 스킬 폴더의 `STYLE.md` 만 수정. 다른 파일에 색·폰트가 박혀 있지 않아야 한다.
