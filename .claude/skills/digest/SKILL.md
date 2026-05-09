---
name: digest
description: Build a weekly or monthly digest under docs/digest/ that aggregates recent posts. Reads the repo via scripts/list_posts.py, then writes a Korean prose digest with a one-line theme, per-post highlights, and a closing paragraph. Use when the user invokes /digest or asks for "주간 정리", "이번 달 모음", "최근 글 묶어줘" 등.
---

# digest

최근 N일치 글을 한 페이지로 묶어 모바일 독자가 한 번에 훑을 수 있게 만든다. 출력 문서는 한국어, 이모지 없음.

## 호출 형태

```text
/digest [period=week|month] [from=YYYY-MM-DD] [to=YYYY-MM-DD] [topic=<folder>]
```

- `period=week` (기본): 오늘부터 7일 전까지.
- `period=month`: 이번 달 1일부터 오늘까지.
- `from`/`to` 명시: `period` 보다 우선.
- `topic` 명시: 그 토픽만 필터.

## 절차

### 1. 글 수집

```bash
python scripts/list_posts.py --period <week|month> [--ending YYYY-MM-DD] [--topic <folder>]
# 또는
python scripts/list_posts.py --from YYYY-MM-DD --to YYYY-MM-DD [--topic <folder>]
```

JSON 으로 후보 글 목록이 나온다. 각 항목 필드: `title`, `date`, `tags`, `summary`, `source`, `topic`, `url`, `path`.

`count == 0` 이면 사용자에게 "범위 안에 글이 없다" 알리고 중단.

### 2. 본문 보강 (선택)

`summary` 만으로 부족하면 각 글의 첫 1~2 단락을 `Read` 로 직접 읽어 추가 맥락 확보. 디제스트 길이가 길어지지 않게 글당 2~3 줄로 압축.

### 3. 디제스트 작성

frontmatter.

```markdown
---
title: 2026-W19 주간 정리
date: 2026-05-10
tags: [digest]
summary: 이번 주 AI 기술 흐름 한 문장 요약
---
```

본문 구조.

1. **이번 주의 흐름** — 한 문장 또는 두 문장. 글 전반을 관통하는 테마. 흐름이 두 갈래로 나뉘면 둘 다 짚되 길게 풀지 말 것.
2. **글별 하이라이트** — 토픽별로 그룹핑. 한 토픽에 글이 1개면 시간순 단일 리스트로 합쳐도 무방. 항목 형식.
    ```markdown
    ### <토픽명>

    - **[제목](상대-URL)** — 한 줄 요약 또는 핵심 한 문장. `tag1` `tag2`
    ```
3. **다음에 볼만한 것** (선택) — 이번 주 글에서 파생되는 후속 질문이나 미리 챙겨볼 만한 흐름. 1~2문장. 억지로 채우지 말 것, 없으면 생략.
4. `## 출처` 는 디제스트에서는 불필요. 각 글에 이미 출처가 있으므로 생략.

### 4. 파일 경로

- 주간: `docs/digest/<YYYY>-W<WW>.md`. `<WW>` 는 ISO 주 번호 두 자리 (예: `2026-W19.md`).
- 월간: `docs/digest/<YYYY>-<MM>.md`. (예: `2026-05.md`).
- `from`/`to` 직접 지정한 커스텀 범위: `docs/digest/<YYYY-MM-DD>--<YYYY-MM-DD>.md`.

이미 같은 파일이 존재하면 사용자에게 덮어쓸지 추가할지 묻기. 추가면 새로 들어온 글만 머지.

### 5. 마무리

```bash
python scripts/update_index.py
```

`git status` 보여주고 push 여부 확인.

## 첫 실행 시 토픽 폴더 생성

`docs/digest/` 폴더가 없으면 다음을 한 번에 한다.

1. `docs/digest/index.md` 생성. 한 줄 설명: "주간·월간 모음. 같은 기간의 다른 토픽 글을 한 페이지로 묶음."
2. `docs/index.md` 의 토픽 리스트에 `[모음](digest/)` 항목 추가.
3. `README.md` 폴더 구조 섹션에 `digest/` 행 추가.

이는 `CLAUDE.md` 의 "토픽 추가·삭제 라이프사이클" 과 같은 절차다.

## 길이 가이드

- 주간 디제스트: 본문 400~700자. 너무 길면 모바일에서 한눈에 안 들어옴.
- 월간 디제스트: 본문 800~1500자. 글이 많으면 토픽별 하이라이트만 추리고 자잘한 글은 마지막에 한 줄씩.

## 주의

- 글 수가 1~2개 뿐이면 디제스트 만들 필요 없음. 사용자에게 알리고 중단 제안.
- 같은 글을 여러 토픽에서 중복 등장시키지 말 것 (한 글은 한 위치에만).
- 디제스트가 다른 디제스트를 참조하지 않도록 `list_posts.py` 가 `digest/` 폴더를 자동으로 제외함.
