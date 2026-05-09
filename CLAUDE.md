# Claude Code 가이드

이 레포는 AI 기술을 동료들과 공유하기 위한 깃 기반 뉴스레터다. Claude Code 가 글 정리·이미지 생성·홈 페이지 갱신을 자동화한다. 이 문서는 너가 (Claude) 이 레포에서 일할 때 따라야 할 컨벤션을 정의한다.

## 핵심 룰

- 모든 출력 문서는 한국어. 기술 용어는 영문 그대로 두는 것이 자연스러우면 그대로 사용.
- 이모지 절대 사용 금지. 글머리 기호와 헤더만으로 구조를 잡을 것.
- 문장은 짧게. 같은 정보를 두 번 말하지 말 것.
- main 에 직접 push 하는 단일 브랜치 흐름. PR 만들지 말 것.

## 글 작성 규약

- 모든 글은 자기 폴더를 가진다: `docs/<topic>/<YYYY-MM-DD-slug>/`.
- 글 폴더의 표준 레이아웃:

```
docs/<topic>/<slug>/
  index.md            # abstract = 한 페이지 요약 + details TOC + 출처
  details/            # 시리즈 (folder, 자체 index.md 없음)
    01-<part>.md      # 각 편. 제목에 글 전체 제목 prefix 안 붙임, 번호도 안 붙임
    02-<part>.md
    ...
  cards/              # /card-news 시 추가. 단독으로도 가능
    index.md
  assets/             # 모든 포맷·파트 공유
    fig-N.png
    card-N.png
```

- **abstract = slug 의 `index.md`**. 한 페이지 요약 + 핵심 포인트 + 짧은 본문 + 자세히 보기 (TOC) + 출처. 별도 short 페이지 없음.
- **details = 시리즈**. 일반 논문 기준 **4~5편**, 편당 **1500~2500 단어**. 큰 멀티 파트 도큐먼트는 6~7편까지.
- **details 파트 제목에 글 전체 제목이나 번호를 붙이지 말 것**. 예: `왜 또 다른 수학용 AI 인가` (O), `AI Co-Mathematician — 1. 왜 또 다른 수학용 AI 인가` (X). 번호는 파일명 prefix (`01-`, `02-` ...) 와 abstract TOC 의 자동 번호로 충분.
- 문체: 간결하지만 정보 밀도 높게. 헤더로 토픽 분리, 병렬 항목은 불릿·표, 흐름 설명은 짧은 단락. 칼럼식 긴 산문 나열 X. 편집자 부연은 짧게 (원문이 안 다룬 맥락·실무 메모 정도). 사변·출처 없는 단정 X.
- abstract 본문에서 그림 ref 는 `assets/fig-N.png`. details 파트와 cards 본문에서는 한 단계 위라 `../assets/fig-N.png`.

### 자동 갱신

- `python scripts/refresh_landing.py docs/<topic>/<slug>/` — abstract 의 `<!-- VERSIONS_START -->` / `<!-- VERSIONS_END -->` 마커 사이를 details 목록 + cards 링크로 자동 채움.
- `python scripts/update_index.py` — 홈 페이지 (`docs/index.md`) LATEST 블록 갱신. 인덱스 노출은 글 폴더 1개 = 항목 1개. 시리즈 파트는 따로 노출 안 됨.

### frontmatter

- 필수 필드: `title`, `date`, `author`, `tags`, `source`, `summary`, `format`.
- `format`: `abstract` (slug index.md) / `details` (details 파트) / `cards` (cards index.md) / `digest` (digest 파일).
- details 파트는 `part: <N>` 도 같이.
- `author` 는 `git config user.name`.
- 슬러그에 포맷 접미사 (`-cards`, `-short` 등) 금지 — 같은 글이면 abstract / details / cards 가 같은 슬러그 공유.

## 스킬 사용 시 subagent 적극 활용

share-news / card-news / digest 모든 스킬은 컨텍스트 부담을 메인이 다 떠안지 않고 subagent 에 위임하도록 짜여 있다.

- **share-news**: details 각 편 작성을 subagent 에 병렬 위임. 메인은 outline 만 잡고 결과 파일을 spot check.
- **card-news**: 카드 narrative + 프롬프트 JSON 작성을 subagent 한 번 위임.
- **digest**: 글이 5개 이상이면 글별 압축 코멘트 작성을 subagent 위임.

원칙.

- Agent tool, `subagent_type="general-purpose"`, foreground (결과 받아 다음 단계).
- 입력 파일 경로·출력 파일 경로를 subagent 프롬프트에 명시. 트랜스크립트 다시 읽지 않음.
- 독립적인 작업은 한 메시지에서 병렬 spawn (Agent tool call 여러 개).
- subagent 출력이 가이드와 어긋나면 그 작업만 재spawn 또는 메인이 직접 미세 수정.

## 형식 가이드

각 `format` 별 출력 길이 가이드.

- `short`: 한 페이지 요약. 600~1000 단어. 구성은 "한 줄 요약 -> 핵심 포인트 3~5개 -> 짧은 본문 -> 출처".
- `deep`: 토픽별 상세. 1500~3000 단어. 구성은 "배경 -> 문제 정의 -> 핵심 아이디어 -> 결과/한계 -> 우리에게의 시사점 -> 출처".
- `cards`: 4~6장 카드 뉴스. 각 카드는 한 가지 메시지. gpt-image-2 로 한국어 텍스트가 들어간 이미지 생성. 본문에는 카드 이미지 마크다운 + 짧은 캡션.

## 토픽 결정

`topic=` 인자가 없을 때, `docs/` 하위 폴더 목록을 동적으로 읽고 각 폴더의 `index.md` 한 줄 설명을 본문 내용과 비교해 가장 적합한 곳을 고른다. 두 곳 이상이 후보면 더 구체적인 쪽 (상위 카테고리보다 좁은 카테고리 우선). 모호하면 사용자에게 한 번 물을 것.

키워드 매핑 표를 이 문서에 박아두지 말 것. 토픽은 자주 바뀌므로 폴더 트리가 곧 매핑이다.

## 토픽 추가·삭제 라이프사이클

새 토픽이 생기거나 기존 토픽이 사라지면 다음을 한 번에 갱신한다. 한 곳만 고치고 끝내면 결국 어긋난다.

1. `docs/<new-topic>/index.md` 생성 (한 줄 설명) 또는 `docs/<old-topic>/` 제거
2. `docs/index.md` 의 "토픽" 리스트
3. `README.md` 의 폴더 구조 섹션
4. 다른 곳에서 해당 토픽을 명시적으로 언급한 부분 (CLAUDE.md, .claude/skills/* 안에 토픽 이름이 박혀 있다면 그 부분도)
5. 기존 글이 사라지는 토픽이면, 옮길지 삭제할지 사용자에게 묻고 결정

이 라이프사이클은 사용자가 "토픽 추가/삭제" 의사를 표현하는 모든 흐름 (수동 폴더 생성, 슬래시 명령 등) 에서 동일하게 적용한다.

## 출력 절차

1. 입력 검증 (URL 형식, 파일 존재).
2. arxiv URL 이면 `arxiv.org/abs/<id>` -> `arxiv.org/html/<id>` 로 치환 (`scripts/parse_source.py` 가 자동 처리).
3. 컨텐츠 페치: WebFetch (URL) 또는 `python scripts/parse_source.py` (PDF).
4. 토픽 결정 (인자 우선, 없으면 폴더 트리 기반 추정).
5. 슬러그 생성 (제목 -> 영문 kebab-case, 한글이면 음차 또는 원문 핵심어).
6. 폴더 만들고 본문 작성.
7. cards 이면 `python scripts/gen_cards.py` 호출.
8. `python scripts/update_index.py` 호출.
9. `git status` 보여주고, push 여부는 사용자 확인 후.

## 도구 사용 우선순위

- 단순 URL 페치: WebFetch.
- PDF: `scripts/parse_source.py` (Docling + PyMuPDF).
- 카드 이미지: `scripts/gen_cards.py` (`.env` 또는 환경변수에 `OPENAI_API_KEY` 필요).
- 인덱스 갱신: `scripts/update_index.py`.
- 검색·탐색: `Read` / `Grep` 직접. Explore 에이전트는 이 레포에선 과한 편.

## 환경변수

OpenAI 키는 레포 루트의 `.env` 에 두는 것을 기본으로 한다. `.env.example` 을 복사해 채우면 된다. `gen_cards.py` 가 자동으로 로드한다. CI 에서는 GitHub Secrets 에 넣고 워크플로 환경변수로 주입.

## 금지 사항

- `OPENAI_API_KEY` 가 `.env` 또는 환경변수에 없으면 카드 생성을 시도하지 말 것. 명확히 알리고 멈춰라.
- `.env` 를 절대 커밋하지 말 것 (`.gitignore` 에 포함되어 있음).
- main 강제 push 금지. push 자체도 사용자 확인 후.
- `docs/` 외부에 콘텐츠 파일을 만들지 말 것.
- 외부 SaaS 링크 (Notion, Obsidian Publish 등) 를 컨벤션으로 도입하지 말 것. 회사 방화벽으로 막힌다.
- 로컬 입력 파일은 `.pdf` 만 받음. `.md` / `.txt` 는 미지원 — 사용자가 그런 파일을 줬다면 본문을 직접 붙여넣어 작성하라고 안내.
