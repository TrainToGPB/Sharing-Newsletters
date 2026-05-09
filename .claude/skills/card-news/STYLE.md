# 카드뉴스 비주얼 스타일

이 문서는 `/card-news` 스킬이 만들어내는 카드의 비주얼 표준이다. 모든 카드가 한 시리즈처럼 보이도록 여기 적힌 STYLE_BLOCK / CONSTRAINTS_BLOCK 을 매번 프롬프트에 그대로 박아 넣는다.

스타일을 바꾸고 싶으면 이 파일만 고치면 된다. 다른 파일에 색·폰트가 박혀 있지 않다.

## 컨셉

내부 AI 기술 공유 뉴스레터의 **인포그래픽 카드**. 톤은 "프로페셔널하지만 가깝게". 모바일 우선이라 누워서 한 손으로 훑는 상황을 가정.

핵심 원칙: **카드 한 장 = 정보 단위 한 개**. 헤드라인 슬로건이 아니라, 작은 그림 (또는 도식) + 개조식 불릿 3~5개로 한 가지 개념을 전달한다.

## 두 가지 그림 소스

각 카드는 다음 중 하나로 만든다.

| 모드 | 언제 | 어떻게 |
| --- | --- | --- |
| **A. Reference 모드** | 본문에 좋은 그림이 있을 때 | `reference_image` 로 전달, 모델이 그걸 우리 스타일로 재해석 |
| **B. Schematic 모드** | 본문에 쓸 만한 그림이 없거나 추상 개념일 때 | 텍스트로 도식을 묘사해 생성 |

대부분의 논문은 핵심 그림이 있어 Mode A 가 자연스럽다. Mode B 는 결과 비교, 흐름 다이어그램이 본문엔 없는데 카드로 보이고 싶을 때 사용.

## 컬러 팔레트

- 배경 navy: `#0B1B3D`
- 액센트 blue: `#3182F6`
- 보조 light: `#F4F6FA`
- 본문 보조 텍스트: `#C7D2E5`
- 헤드라인: white
- 그림·도식: 액센트 blue 라인만, 2px stroke, 면 채움 없음

## 타이포그래피

- 한글 산세리프: Pretendard / Apple SD Gothic Neo 같은 지오메트릭 고딕
- 헤드라인: 굵게 ~48pt (헤드라인이 카드의 주인공이 아님 — 그림이 주인공)
- 불릿: 일반 ~24pt
- 라벨·푸터: 작게 ~20pt

## 길이 규칙

- HEADLINE_KO: 한글 12~16자, 한 줄
- 불릿 한 줄: 한글 20~30자
- 불릿 개수: 3~5개
- TOPIC_KO: 한글 4~8자
- 카드당 텍스트 = 라벨 + 헤드라인 + 불릿 3~5개 + 푸터. 더 늘리지 말 것.

## 레이아웃

- 1024x1536 portrait (4:6, 모바일 우선)
- 좌상단: 작은 라벨 (예: `1/5 · AI 에이전트`)
- 그 아래: 헤드라인 (white, bold, 작은 편)
- 카드 중앙 (~50% 높이): 그림 / 도식 (line-art, 액센트 blue)
- 그림 아래: 불릿 3~5개. 각 불릿 앞에 작은 액센트 blue 점 또는 →
- 좌하단: `Sharing Newsletters` 푸터
- 그림과 텍스트 영역은 시각적으로 분리되어야 함 (그림 위에 텍스트 겹치지 않게)
- 카드 모서리는 약간 둥글게

## STYLE_BLOCK (모든 카드 프롬프트에 그대로 포함)

```
Editorial infographic card slide for an internal Korean AI tech newsletter.
Portrait 2:3, 1024x1536. Generous whitespace, clean minimal layout.
Palette: deep navy #0B1B3D background, accent blue #3182F6, neutral #F4F6FA,
white text, light text #C7D2E5. Typography: Pretendard-like geometric
sans-serif, bold compact headline, regular body. Center-of-card visual is
line-art only (2px accent blue strokes on navy, no fills, no photos, no
gradients, no drop shadows). Below the visual sits a vertical list of
Korean bullet-style annotations, each prefixed with a small accent blue
dot or arrow. Professional but approachable, no emojis.
```

## LAYOUT_BLOCK — Mode A (Reference 모드)

`{N}` `{TOTAL}` `{TOPIC_KO}` `{HEADLINE_KO}` `{BULLETS}` 만 카드마다 채운다. `reference_image` 는 별도 API 인자로 전달되므로 프롬프트엔 안 넣음.

```
Top-left small label reads exactly "{N}/{TOTAL} · {TOPIC_KO}".
Below the label, bold compact headline reads exactly "{HEADLINE_KO}",
white, about 48pt.
Center area (about 50% of the card height): redraw the supplied reference
image in clean line-art style — accent blue #3182F6 strokes only, 2px,
no fills, no photographic detail. Preserve the structure and labels of the
original but adapt to the navy background and our typography. Korean labels
in the original should be rendered exactly. English labels stay English.
Below the visual, a vertical list of bullet annotations, each on its own
line with a small accent blue dot prefix, ~24pt, in #C7D2E5:
{BULLETS}
Bottom-left footer reads exactly "Sharing Newsletters", small.
```

## LAYOUT_BLOCK — Mode B (Schematic 모드)

reference 없이 처음부터 도식을 그려야 할 때.

```
Top-left small label reads exactly "{N}/{TOTAL} · {TOPIC_KO}".
Below the label, bold compact headline reads exactly "{HEADLINE_KO}",
white, about 48pt.
Center area (about 50% of the card height): line-art schematic of
{SCHEMATIC_DESC}. Accent blue #3182F6 strokes only, 2px, no fills.
Use simple geometric shapes (rounded rectangles, circles, arrows) and
clear hierarchy. Korean labels inside the schematic must be rendered
exactly as listed: {SCHEMATIC_LABELS}.
Below the schematic, a vertical list of bullet annotations, each on its
own line with a small accent blue dot prefix, ~24pt, in #C7D2E5:
{BULLETS}
Bottom-left footer reads exactly "Sharing Newsletters", small.
```

## CONSTRAINTS_BLOCK (모든 카드 프롬프트에 그대로 포함)

```
Render all Hangul exactly as given. Do not romanize. No invented glyphs.
Correct jamo composition. Render text once, verbatim. No watermarks,
no logos, no extra captions, no English translations of the Korean text,
no emojis, no decorative pseudo-Hangul, no Hangul-shaped ornaments.
Only the quoted text strings and the listed bullets appear in the image.
```

## 풀 프롬프트 조합 순서

각 카드 프롬프트 = `STYLE_BLOCK` + 빈 줄 + `LAYOUT_BLOCK (Mode A 또는 B, placeholder 채운 것)` + 빈 줄 + `CONSTRAINTS_BLOCK`. 매 호출마다 STYLE / CONSTRAINTS 블록은 글자 단위로 동일해야 한다.

`{BULLETS}` 는 다음 형식으로 채운다 (각 줄이 그대로 카드에 박힘).

```
- 첫 번째 불릿 한국어 한 줄
- 두 번째 불릿 한국어 한 줄
- 세 번째 불릿 한국어 한 줄
```

## API 호출 옵션 권장

- `model="gpt-image-2"`
- `size="1024x1536"`
- `quality="medium"` (기본). 일반 시리즈는 medium 으로 충분 (~$0.04/장). 핵심 시리즈만 `high` 로 (~$0.17/장).
- `seed=<series 별 고정 정수>`. 시리즈 안에서 카드끼리 톤 일관성 가장 큰 레버.
- `response_format` 파라미터는 **넣지 말 것** (gpt-image-2 가 거부, HTTP 400). 기본 응답이 b64_json.
- Mode A: `client.images.edit(image=<ref-file>, prompt=...)` 사용. Mode B: `client.images.generate(prompt=...)`.

## 시리즈 길이 가이드

- 4장: 너무 짧음. 핵심만 있을 때.
- 5장: 기본. 도입 / 무엇이 / 어떻게 / 왜 중요 / 정리.
- 6장: 중대 발표나 비교 시리즈에 한정.
- 7장 이상은 만들지 말 것. 모바일 독자가 끝까지 안 봄.

## 금지

- 그라디언트, 드롭섀도우, 글로우 효과
- 스톡 사진, 인물 사진
- 영어 번역 캡션 (한글 의역 X)
- 이모지, 데코레이션 한글
- 워터마크, 로고
- 한 카드에 여러 메시지 (한 카드 = 한 정보 단위)
- 그림 위에 텍스트 겹치기
- 헤드라인이 카드의 주인공처럼 크게 — 그림이 주인공이고 헤드라인은 부제목 역할
