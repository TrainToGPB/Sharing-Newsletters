---
name: share-news
description: Convert a URL or local PDF into a tech sharing post under docs/<topic>/, in either short summary or deep topic-doc format. Auto-detects topic from existing folders, generates a slug, extracts PDF figures, and refreshes the homepage latest list. For card-news image series use the separate /card-news skill. Use when the user invokes /share-news or asks to "정리해서 블로그 추가" with a source URL or PDF.
---

# share-news

이 레포에 새 글을 자동으로 추가하는 스킬이다. URL 또는 로컬 PDF 를 받아서 정해진 폴더에 마크다운 파일과 (필요하면) PDF 그림을 추출해 올린다.

카드 뉴스 (이미지 생성 시리즈) 는 이 스킬이 아니라 `/card-news` 스킬에서 처리한다.

## 호출 형태

```text
/share-news <source> [format=short|deep] [topic=<folder>]
```

- `<source>` 는 URL 이거나 로컬 `.pdf` 경로 (다른 파일 형식은 미지원)
- `format` 기본값: `short`
- `topic` 미지정 시 본문에서 자동 추정

## 절차

다음 단계를 순서대로 수행한다. 모든 출력 문서는 한국어, 이모지 없음.

### 1. 입력 검증

- URL 이면 스킴 확인. `arxiv.org/abs/<id>` 또는 `arxiv.org/pdf/<id>` 는 `scripts/parse_source.py` 가 자동으로 `arxiv.org/html/<id>` 로 치환한다.
- 파일 경로면 `.pdf` 인지 확인. 다른 확장자는 거절.

### 2. 컨텐츠 페치

- URL: `WebFetch` 로 본문을 가져와 핵심 주장과 구조를 파악. 길거나 그림 추출이 필요하면 `python scripts/parse_source.py <url> --out-md /tmp/parsed.md`.
- PDF: 슬러그를 먼저 정한 뒤 (3단계) 호출.
    ```bash
    python scripts/parse_source.py <pdf-path> \
        --out-md /tmp/parsed.md \
        --assets-dir docs/<topic>/<slug>-assets \
        --image-prefix <slug>-assets
    ```
    Docling 으로 텍스트를 뽑고, PyMuPDF 로 그림을 `<slug>-assets/fig-N.png` 로 저장한다. 출력 마크다운 끝에 `## Figures` 블록으로 추출된 그림 링크가 따라온다.

### 3. 메타 결정

- **제목**: 페치한 본문 첫 헤더 또는 `<title>`. 한국어가 자연스러우면 의역.
- **요약**: 한 문장. frontmatter `summary` 와 본문 첫 단락에 사용.
- **태그**: 2~5개. 본문 키워드 기반.
- **토픽**: 인자 우선. 인자가 없으면 `docs/` 하위 폴더 목록을 동적으로 읽어 가장 적합한 곳 선택. 모호하면 사용자에게 한 번 묻기.
- **슬러그**: 영문 핵심어 기반 kebab-case. 한국어 제목이면 핵심 명사를 영문 음차/번역하여 짧게.
- **날짜**: 오늘 (`YYYY-MM-DD`).
- **출력 경로**: `docs/<topic>/<YYYY-MM-DD>-<slug>.md`.

### 4. 본문 작성

frontmatter 는 모든 포맷 공통.

```markdown
---
title: 제목
date: 2026-05-10
tags: [태그1, 태그2]
source: 원본-URL-또는-파일명
summary: 한 줄 요약
---
```

#### format=short (기본)

600~1000 단어. 한 줄 요약 → 핵심 포인트 3~5개 → 짧은 본문 → `## 출처`.

#### format=deep

1500~3000 단어. 배경 → 문제 정의 → 핵심 아이디어 → 결과·한계 → 우리에게의 시사점 → `## 출처`. PDF 그림이 있으면 본문 흐름에 맞게 `![figure N](<slug>-assets/fig-N.png)` 로 삽입.

카드 뉴스가 필요하면 `/card-news` 를 따로 호출. 이 스킬은 텍스트 글만 다룬다.

### 5. 인덱스 갱신

```bash
python scripts/update_index.py
```

### 6. 마무리

- `git status` 로 변경 파일 출력.
- 작성된 파일 경로와 미리보기 명령 (`mkdocs serve`) 안내.
- push 여부는 사용자 확인 후. OK 하면.
    ```bash
    git add docs/<topic>/<YYYY-MM-DD>-<slug>.md docs/<topic>/<slug>-assets/ docs/index.md
    git commit -m "post(<topic>): <slug>"
    git push
    ```

## 토픽 추가·삭제 시 동기화

토픽 폴더 구조는 자주 바뀐다. 사용자가 새 토픽을 추가하거나 기존 토픽을 제거할 때, **반드시** 다음을 함께 갱신한다 (한 곳만 갱신하고 끝내지 말 것).

- `docs/<new-topic>/index.md` 생성 (한 줄 설명) 또는 `docs/<old-topic>/` 디렉토리 제거
- `docs/index.md` 의 "토픽" 섹션 리스트
- `README.md` 의 폴더 구조 섹션
- `CLAUDE.md` 의 토픽 관련 언급 (있다면)
- 이 `SKILL.md` 자체에 토픽이 명시적으로 박혀 있는 부분 (있다면 — 현재는 없음)

토픽 자체의 키워드 매핑을 이 문서에 박아두지 말 것. 본문 내용과 `docs/` 폴더 목록 비교로 그때그때 판단한다.

## 에러 처리

- URL 페치 실패: 사용자에게 알리고 PDF 다운로드 후 재시도 권유.
- Docling 미설치: `pip install -r requirements.txt` 안내. 정책상 무조건 Docling 사용.

## 예시 호출

- `/share-news https://arxiv.org/abs/2501.12345` → `format=short`, 본문에 맞게 토픽 자동 선택.
- `/share-news ./paper.pdf format=deep` → PDF 그림 포함 상세 정리, 토픽 자동 추정.
- 카드 뉴스가 필요하면 `/card-news <source>` 를 별도로 호출.
