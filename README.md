# Sharing Newsletters

내부 동료와 외부 기여자가 함께 모여 AI 기술을 공유하는 깃 기반 뉴스레터.

## 보기

- 웹: https://traintogpb.github.io/Sharing-Newsletters/ (push 하면 GitHub Actions 가 자동 배포)
- 모바일: 위 URL을 그대로 핸드폰에서 열면 됨. MkDocs Material 테마라 다크모드와 검색이 모바일에서 잘 동작
- GitHub에서 바로: `docs/` 아래 마크다운을 GitHub 앱·웹으로 열어도 가독성 OK

## 글 추가하기 (자동)

이 레포는 Claude Code 기반으로 자동 정리를 지원한다.

```text
# abstract 한 페이지 + details 시리즈 (기본 5편) 한 번에 생성
/share-news https://arxiv.org/abs/2403.04132

# 시리즈 편 수 조정
/share-news https://arxiv.org/abs/2403.04132 parts=4

# 카드 뉴스 (gpt-image-2 이미지 4~6장) — 별도 스킬, 같은 폴더에 cards/ 추가
/card-news https://arxiv.org/abs/2403.04132 count=5

# 토픽 폴더 명시 (기본은 자동 추정)
/share-news ./paper.pdf topic=agents
```

지원 입력:

- URL (arxiv `abs/...` 는 자동으로 `html/...` 엔드포인트로 치환)
- 로컬 PDF (Docling 으로 텍스트, PyMuPDF 로 그림 추출)

`.md` / `.txt` 같은 로컬 텍스트 파일은 미지원. 직접 본문에 붙여넣어 수동 작성하면 된다. 자세한 동작은 `.claude/skills/share-news/SKILL.md` 참고.

## 글 추가하기 (수동)

원하면 파일을 직접 작성해도 된다.

1. `docs/<topic>/<YYYY-MM-DD-slug>/index.md` 생성 (글마다 자기 폴더)
2. 같이 올릴 이미지가 있으면 같은 폴더 안 `assets/` 에 두기
3. 아래 frontmatter 필수
4. main 에 push

```markdown
---
title: 글 제목
date: 2026-05-10
author: TrainToGPB
tags: [agents, mcp]
source: https://원본-링크
summary: 한 줄 요약
format: short
---

# 글 제목

본문 ...
```

한 번 호출에 *abstract* (한 페이지 요약) + *details* (시리즈) 가 같이 만들어진다. 카드 뉴스가 필요하면 별도 `/card-news` 호출로 같은 폴더에 추가.

```text
docs/agents/2026-05-10-foo/
  index.md            # abstract — 한 페이지 요약 + details TOC + 출처
  details/            # 시리즈
    01-overview.md
    02-architecture.md
    03-results.md
    ...
  cards/              # 카드 뉴스 (/card-news 호출 시)
    index.md
  assets/             # 모든 포맷·시리즈 파트가 공유
    fig-1.png
    card-1.png
```

abstract 의 `## 자세히 보기` 블록은 `<!-- VERSIONS_START -->` / `<!-- VERSIONS_END -->` 마커 사이가 `scripts/refresh_landing.py` 에 의해 자동 갱신된다 — details 파트 목록과 cards 링크가 채워진다.

작성 후 `python scripts/update_index.py` 를 돌리면 홈 페이지의 최신 글 목록이 갱신된다 (share-news 스킬은 이걸 자동으로 호출).

## 모바일에서 작성하기

핸드폰으로도 글을 추가하고 싶다면 다음 두 가지를 권장.

1. **claude.ai 웹앱 + GitHub connector**: claude.ai 의 Connectors 에서 GitHub 을 연결하고 이 레포에 권한을 부여. 모바일 브라우저에서 claude.ai 를 열어 "이 URL 정리해서 docs/agents/ 에 push 해줘" 식으로 지시 가능.
2. **GitHub 모바일 앱 직접 편집**: 단순한 수정·추가는 GitHub 앱의 코드 편집기로 충분. 자동 정리는 안 되지만 오타 수정·문구 보정에는 가장 빠르다.

## 폴더 구조

```text
docs/
  index.md           홈 (최신 글 자동 갱신)
  agents/            에이전트, 도구사용, MCP
  models/            신규 모델 출시·아키텍처
  training/          사전·사후학습, 파인튜닝, 데이터
  inference/         서빙·양자화 등 추론 최적화
  benchmark/         평가, 리더보드, 비교
  tools/             개발 도구, IDE, CLI
  digest/            주간·월간 모음
.claude/skills/share-news/  자동 정리 스킬
.claude/skills/digest/      주간·월간 모음 스킬
.claude/skills/card-news/   카드 뉴스 스킬
scripts/             유틸리티 스크립트
.github/workflows/   Pages 자동 배포
mkdocs.yml           사이트 설정
```

새 토픽 추가 / 기존 토픽 제거 시에는 폴더만 손대면 안 된다. `docs/index.md` 의 토픽 리스트와 위 폴더 구조 섹션, 그리고 토픽 이름이 박힌 다른 문서까지 함께 갱신해야 한다. 자세한 절차는 `CLAUDE.md` 의 "토픽 추가·삭제 라이프사이클" 참고.

## 컨벤션

- main 에 직접 push (PR 없음)
- 모든 글은 자기 폴더 안에: `docs/<topic>/<YYYY-MM-DD-slug>/index.md`
- frontmatter 의 `title / date / author / tags / source / summary` 필수. `author` 는 git 닉네임.
- 이모지 사용 금지
- 문장은 짧고 명확하게. 같은 정보면 한 문장으로
- 외부 링크는 본문에 자연스럽게 포함하고 마지막에 `## 출처` 섹션으로 한 번 더 정리
- 글에 딸린 이미지 (카드뉴스, PDF 그림) 는 같은 폴더 안 `assets/` 에 저장

## 로컬 미리보기

```bash
pip install -r requirements.txt
mkdocs serve
# http://127.0.0.1:8000 접속
```

## 개발자 셋업

이미지 생성 카드 뉴스를 만들려면 OpenAI API 키가 필요하다. 레포 루트에 `.env` 파일을 두면 `scripts/gen_cards.py` 가 자동으로 읽는다.

```bash
cp .env.example .env
# 에디터로 .env 열어 OPENAI_API_KEY 채우기
```

`.env` 는 `.gitignore` 에 포함되어 있어 커밋되지 않는다. 절대 손으로 추가하지 말 것. CI 에서 카드 생성을 돌릴 일이 있으면 GitHub Secrets 에 키를 등록하고 워크플로 환경변수로 주입.

PDF 처리는 Docling 과 PyMuPDF 가 필요하다 (`requirements.txt` 에 포함). 시스템에 따라 Docling 첫 import 시 모델 가중치를 자동 다운로드한다.
