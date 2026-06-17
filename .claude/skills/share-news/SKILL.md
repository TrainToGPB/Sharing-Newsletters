---
name: share-news
description: Convert a URL or local PDF into a tech sharing post under docs/<topic>/<slug>/. Always generates BOTH a one-page abstract (slug landing index.md) and a multi-part details series under details/. Auto-detects topic, generates a slug, extracts figures, and refreshes the homepage. Heavily uses subagents to delegate per-part writing — main flow stays focused on planning. For card-news image series, the separate /card-news skill adds a cards/ subfolder. Use when the user invokes /share-news or asks to "정리해서 블로그 추가" with a source URL or PDF.
---

# share-news

URL 또는 로컬 PDF 한 개에서 *abstract* 한 페이지 + *details* 시리즈 (4~5편) 를 한 번에 생성한다. format 인자 없음 — 둘 다 만들어진다.

## 호출 형태

```text
/share-news <source> [topic=<folder>] [parts=N]
```

- `<source>`: URL 또는 로컬 `.pdf`
- `topic`: 미지정 시 자동 추정
- `parts`: 시리즈 편 수 (기본 5, 일반 논문 권장 4~5)

## 출력 구조

```
docs/<topic>/<YYYY-MM-DD>-<slug>/
  index.md            # abstract = 한 페이지 요약 + details TOC + 출처
  details/            # 시리즈 (folder, 자체 index.md 없음)
    01-<part>.md      # 각 편 (제목에 글 전체 제목 prefix 없음)
    02-<part>.md
    ...
  assets/             # 모든 편이 공유
    fig-N.png ...
```

`/card-news` 가 추가되면 같은 글-루트에 `cards/index.md` + `assets/card-N.png` 가 붙음. 그건 별도 스킬.

## 절차

### 1. 입력 검증

- URL 이면 스킴 확인. arXiv(`abs`/`pdf`/`html`)는 `parse_source.py` 가 **HTML 버전을 먼저 확인**(HEAD)해 있으면 HTML을 파싱하고, 없으면 **PDF를 받아 파싱**한다(예전엔 무조건 `html` 로 치환만 했음).
- 파일 경로면 `.pdf` 인지 확인. 다른 확장자는 거절.

### 2. 메타 빠른 결정

본문을 깊이 들어가기 전에 다음을 먼저 결정 (정확한 본문 분석은 3단계에서 subagent 가).

- **작성자**: `git config user.name`
- **날짜**: 오늘 (YYYY-MM-DD)
- **토픽**: 인자 우선, 없으면 `docs/` 폴더 트리에서 가장 적합한 곳. 모호하면 사용자에게 한 번 묻기.
- **slug 후보**: URL/제목 기반 영문 kebab-case. 본문 페치 후 다듬을 수 있음.
- **assets 경로**: `docs/<topic>/<YYYY-MM-DD>-<slug>/assets/`

### 3. 컨텐츠 페치 + 그림 다운로드

```bash
python scripts/parse_source.py <source> \
    --out-md /tmp/parsed.md \
    --assets-dir docs/<topic>/<YYYY-MM-DD>-<slug>/assets \
    --image-prefix assets
```

URL/PDF 같은 명령. URL 은 trafilatura 로 본문 + 인라인 이미지 자동 다운로드, PDF 는 Docling 텍스트 + PyMuPDF 그림. 투명 배경 이미지(arXiv 다이어그램에 흔함)는 흰 배경으로 flatten 해 저장 — 다크모드에서 글자/선이 안 보이는 문제 방지.

> PDF에서 **벡터 다이어그램·표를 라벨 단위로 깨끗이** 뽑고 싶으면 `/parse-figures` 스킬을 쓴다(`--out-dir <assets>`). PyMuPDF 덤프가 놓치는 벡터 아키텍처 도식과 표를 잡고, 파일명을 논문 실제 라벨(`figure-3.png`)로 떨구며, 캡션 글자를 크롭에서 빼고 `manifest.json` 에 캡션 텍스트를 따로 담는다.

### 4. 그림 검토 (간단히)

`/tmp/parsed.md` 의 그림 ref 를 훑고 alt·앞뒤 단락에서 각 그림이 무엇인지 가늠. alt 가 비거나 모호한 핵심 그림 1~2개만 `Read` 로 시각 확인 (모든 그림을 다 열지 말 것 — 토큰 낭비).

명백히 무관한 (장식·헤더 일러스트) 파일은 `rm` 으로 정리.

### 5. 시리즈 outline 설계

`parts` 편으로 흐름을 끊는다. 본문 분량과 구조에 맞게 자유롭지만, 일반 논문은 다음 5편형이 잘 맞음.

| 편 | 일반적 scope |
| --- | --- |
| 01 | 배경·문제 정의·자리잡기 |
| 02 | 디자인 원칙·핵심 아이디어 |
| 03 | 아키텍처·시스템 구성 |
| 04 | 동작·사용 흐름 (그림 다수) |
| 05 | 평가·한계·시사점 |

각 편마다 다음을 정한다.

- 편 slug: kebab-case (예: `overview-and-context`, `design-principles`)
- 편 제목: 그 편의 핵심 한 문장. **글 전체 제목 prefix 를 붙이지 말 것**. 번호 prefix 도 본문 제목에는 안 붙임 (파일명·TOC 에서 자동으로 1, 2, ... 가 붙음).
- 편 요약: 한 문장 (TOC 노출)
- 편 scope: 원문의 어느 섹션·그림을 다룰지

### 6. 각 편 본문 작성 — subagent 병렬 위임 (필수)

**원문 + 스타일 가이드 + 작성 작업** 모두를 메인 컨텍스트에 끌어들이면 빠르게 한도가 차오른다. 각 편 작성은 subagent 에 위임하고 메인은 계획·검증만 한다.

#### Spawn 패턴

`parts` 개의 subagent 를 **하나의 메시지에서 병렬로 spawn**. Agent tool, `subagent_type="general-purpose"`, foreground (결과를 받아 다음 단계 진행).

#### Per-subagent 프롬프트 템플릿

각 subagent 에 다음을 그대로 또는 minor 수정하여 전달.

```
역할: Sharing-Newsletters 레포의 details 시리즈 한 편을 작성한다.

입력 파일:
- 원문 (마크다운, 그림 ref 포함): /tmp/parsed.md
- 시리즈 컨텍스트: 총 <PARTS>편 중 <N>편. 직전 편 slug=<prev>, 다음 편 slug=<next> (없으면 생략).
- 사용 가능 그림: docs/<topic>/<slug>/assets/ 안의 fig-1.png ... fig-K.png

이 편의 scope:
- 제목: <편 제목>
- 다룰 내용: <편 scope, 원문의 어느 섹션·그림>
- 길이: 1500~2500 단어
- 사용할 그림: <fig-N 후보들>. alt 가 모호하면 Read 로 시각 확인 후 본문에 직접 캡션 작성.

출력 파일: docs/<topic>/<slug>/details/<NN>-<part-slug>.md

스타일·형식:
- 한국어, 이모지 없음.
- frontmatter (필수): title, date, author, tags, source, summary, format=details, part=<N>
- title 에 글 전체 제목 prefix 안 붙음, 번호도 안 붙음.
- 본문 H1 = title 그대로.
- **H1 바로 아래 빈 줄 하나, 그 다음 줄에 원본 출처 링크 배지**: `> 원본: [<도메인 또는 짧은 라벨>](<URL>)`. 그 다음 빈 줄, 본문 시작. 라벨 예: `arxiv.org/abs/2605.06651`, `Google Research blog`.
- 헤더로 토픽 분리 + 짧은 단락 (2~4문장) + 병렬 항목은 불릿/표.
- 칼럼식 긴 산문 나열 X. 사실 밀도 우선.
- 그림 ref: `../assets/fig-N.png`. **캡션은 그림과 빈 줄(이중 개행)로 분리** — `![](...)` 다음에 빈 줄을 한 줄 넣고 그 아래에 *이탤릭 한 줄 캡션*. 한 칸 줄바꿈만 하면 마크다운 프리뷰에서 캡션이 그림 옆에 붙어 렌더된다. 올바른 형식:
  ```markdown
  ![](../assets/fig-N.png)

  *캡션 — 무엇을/왜 중요한지.*
  ```
- **수식은 마크다운 수식 포맷 필수**. 인라인 `$x = y$`, 디스플레이 `$$ ... $$` (앞뒤 빈 줄). 변수·기호 한 글자도 `$x$` 로 감싼다. raw `\frac` `\sum` `\mathcal` 등을 일반 텍스트에 흘리지 말 것.
- 편집자 부연은 짧게만 — 원문이 빠뜨린 맥락·실무 메모 정도. 사변·단정 X.
- 본문 끝에 다음 편 링크 한 줄 (있으면).
- ## 출처 섹션에 source URL (상단 배지와 별도로 그대로 유지).

출력하지 말 것: 작업 진행 보고. 파일 작성 후 한 줄 ("written: <path>, ~<words> words") 만 반환.
```

#### 메인 에이전트가 할 일

- subagent spawn 전에 outline 을 확정 (편별 제목·scope·그림)
- spawn 후 결과 한 줄 보고만 받음
- 이후 필요 시 한두 편을 빠르게 `Read` 로 톤 점검 — 모든 편 다시 읽지 말 것

### 7. abstract 페이지 작성

`docs/<topic>/<YYYY-MM-DD>-<slug>/index.md` 를 직접 작성. 이 페이지는 *한 페이지 요약* + *details TOC* + *출처*. subagent 위임 가능하지만 짧으니 메인이 직접 써도 무방.

```markdown
---
title: <글 전체 제목>
date: 2026-05-10
author: <git user.name>
tags: [태그1, 태그2, ...]
source: <원본 URL>
summary: <한 줄 요약>
format: abstract
---

# <글 전체 제목>

> 원본: [<도메인 또는 짧은 라벨>](<원본 URL>)

<도입 한 문장 — 한 줄 요약 풀어쓴 것>

## 핵심 포인트

- 포인트 1
- 포인트 2
- 포인트 3 ~ 5

## 한 페이지 요약

<짧은 본문, 600~1000 단어. 이 글이 다루는 흐름과 결과를 한 호흡으로. 0~2 그림. `assets/fig-N.png` ref 사용 (이 페이지는 slug-루트라 `../` 없이 바로). 캡션을 달면 그림과 **빈 줄(이중 개행)로 분리** — `![](...)` 다음 빈 줄, 그 아래 *이탤릭 캡션*.>

## 자세히 보기

<!-- VERSIONS_START -->
<!-- VERSIONS_END -->

## 출처

- <source URL>
```

`<!-- VERSIONS_START -->` / `<!-- VERSIONS_END -->` 마커 사이는 비워둔다. 다음 단계 스크립트가 채움.

### 8. 자동 갱신 스크립트

```bash
python scripts/refresh_landing.py docs/<topic>/<YYYY-MM-DD>-<slug>/
python scripts/update_index.py
```

순서대로 — 슬러그 랜딩의 VERSIONS 블록을 details 파트 + (있으면) cards 링크로 채우고, 홈 인덱스 LATEST 블록과 토픽 랜딩 (`docs/<topic>/index.md`) 의 `<!-- TOPIC_POSTS_START -->` / `<!-- TOPIC_POSTS_END -->` 블록 (날짜·제목·요약 표) 을 함께 갱신. 토픽 랜딩에 마커가 없으면 그 토픽만 건너뜀 — 새 토픽 폴더를 만들 때 마커를 함께 박아두는 것을 잊지 말 것.

### 9. 마무리

- `git status` 로 변경 파일 출력.
- 작성된 파일 경로와 미리보기 명령 (`mkdocs serve`) 안내.
- push 여부는 사용자 확인 후. OK 하면.
    ```bash
    git add docs/<topic>/<YYYY-MM-DD>-<slug>/ docs/index.md
    git commit -m "post(<topic>): <slug>"
    git push
    ```

## 토픽 추가·삭제 시 동기화

토픽 폴더 구조는 자주 바뀐다. 사용자가 새 토픽을 추가하거나 기존 토픽을 제거할 때, **반드시** 다음을 함께 갱신한다.

- `docs/<new-topic>/index.md` 생성 (한 줄 설명 + `## 글 목록` 섹션 안에 `<!-- TOPIC_POSTS_START -->` / `<!-- TOPIC_POSTS_END -->` 마커) 또는 `docs/<old-topic>/` 디렉토리 제거
- `docs/index.md` 의 "토픽" 섹션 리스트
- `README.md` 의 폴더 구조 섹션
- `CLAUDE.md` 의 토픽 관련 언급 (있다면)

토픽 키워드 매핑을 SKILL.md 안에 박아두지 말 것. 본문 내용과 `docs/` 폴더 목록 비교로 그때그때 판단한다.

## 에러 처리

- URL 페치 실패: 사용자에게 알리고 PDF 다운로드 후 재시도 권유.
- Docling / PyMuPDF / trafilatura / python-frontmatter 미설치: `pip install -r requirements.txt` 안내.
- subagent 출력이 가이드와 어긋남 (제목 prefix, 길이, format 필드 누락 등): 메인이 spot check 후 그 편만 재spawn 하거나 직접 미세 수정.

## 예시 호출

- `/share-news https://arxiv.org/abs/2501.12345` → abstract + details 5편 자동 생성, 토픽 자동 선택.
- `/share-news ./paper.pdf parts=4` → 4편 시리즈로 압축.
- `/share-news https://blog.example.com/post topic=tools` → tools 토픽으로 강제, 기본 5편.
