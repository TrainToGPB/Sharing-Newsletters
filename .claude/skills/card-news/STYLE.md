# 카드뉴스 비주얼 스타일

이 문서는 `/card-news` 스킬이 만들어내는 카드의 비주얼 표준이다. 모든 카드가 한 시리즈처럼 보이도록 여기 적힌 STYLE_BLOCK / CONSTRAINTS_BLOCK 을 매번 프롬프트에 그대로 박아 넣는다.

스타일을 바꾸고 싶으면 이 파일만 고치면 된다. 다른 파일에 색·폰트가 박혀 있지 않다.

## 컨셉

내부 AI 기술 공유 뉴스레터. 톤은 "프로페셔널하지만 가깝게". 모바일 우선이라 누워서 한 손으로 훑는 상황을 가정. 글이 짧고 시각이 시원해야 한다.

## 컬러 팔레트

- 배경 navy: `#0B1B3D`
- 액센트 blue: `#3182F6`
- 보조 light: `#F4F6FA`
- 본문 보조 텍스트: `#C7D2E5`
- 헤드라인: white
- 일러스트: 액센트 blue 라인만, 면 채움 없음

## 타이포그래피

- 한글 산세리프: Pretendard / Apple SD Gothic Neo 같은 지오메트릭 고딕
- 헤드라인 굵게 (~72pt 기준)
- 본문 일반 (~28pt 기준)
- 라벨·푸터 작게 (~22pt 기준)
- 한글 의역 금지. 지시한 문자열 그대로 렌더.

## 길이 규칙

- HEADLINE_KO: 한글 ~18자 이내. 두 줄까지 가능 (지시문에 `\n` 한 번 넣기).
- BODY_KO: 한글 ~22자, 한 줄.
- TOPIC_KO: 한글 4~8자 (예: "AI 모델 업데이트", "에이전트 도구").
- ILLUSTRATION_HINT: 영어 1~3 단어 (예: `open book`, `neural net graph`, `connected nodes`).
- 카드 한 장의 텍스트 요소는 라벨 / 헤드라인 / 본문 / 푸터, 이 4개 고정. 더 늘리지 말 것.

## 레이아웃

- 1024x1536 portrait (4:6, 모바일 우선).
- 좌측 2/3: 텍스트 영역.
    - 좌상단: small 라벨 (예: `1/5 · AI 모델 업데이트`).
    - 중앙 좌측: 헤드라인 (white, bold).
    - 헤드라인 아래: 본문 한 줄 (light).
    - 좌하단: 푸터 `Sharing Newsletters`.
- 우측 1/3: 라인아트 일러스트.
- 텍스트와 일러스트 영역은 겹치지 않게.
- 카드 모서리는 약간 둥글게.

## STYLE_BLOCK (모든 카드 프롬프트에 그대로 포함)

```
Editorial card-news slide for an internal Korean AI tech newsletter.
Portrait 2:3, 1024x1536. Clean minimal layout with generous whitespace.
Palette: deep navy #0B1B3D background, accent blue #3182F6, neutral #F4F6FA,
white text. Typography: Pretendard-like geometric sans-serif, bold headline,
regular body. Subtle line-art illustration on the right third, no photos,
no gradients, no drop shadows. Professional but approachable, no emojis.
```

## LAYOUT_BLOCK (카드별로 placeholder 채워서 사용)

`{N}` `{TOTAL}` `{TOPIC_KO}` `{HEADLINE_KO}` `{BODY_KO}` `{ILLUSTRATION_HINT}` 만 카드마다 다르게 채운다.

```
Top-left small label reads exactly "{N}/{TOTAL} · {TOPIC_KO}".
Center-left headline reads exactly "{HEADLINE_KO}" in two lines max,
bold white, about 72pt.
Below headline, one-line body reads exactly "{BODY_KO}" in #C7D2E5, about 28pt.
Bottom-left footer reads exactly "Sharing Newsletters".
Right third: simple line-art illustration of {ILLUSTRATION_HINT}, accent blue
strokes on navy, 2px stroke, no fills.
Text occupies left two-thirds. Illustration occupies right one-third.
Do not overlap text with illustration.
```

## CONSTRAINTS_BLOCK (모든 카드 프롬프트에 그대로 포함)

```
Render all Hangul exactly as given. Do not romanize. No invented glyphs.
Correct jamo composition. Render text once, verbatim. No watermarks,
no logos, no extra captions, no English translations, no emojis,
no decorative pseudo-Hangul, no Hangul-shaped ornaments.
Only the quoted text strings appear in the image.
```

## 풀 프롬프트 조합 순서

각 카드 프롬프트 = `STYLE_BLOCK` + 빈 줄 + `LAYOUT_BLOCK (placeholder 채운 것)` + 빈 줄 + `CONSTRAINTS_BLOCK`. 매 호출마다 STYLE / CONSTRAINTS 블록은 글자 단위로 동일해야 한다.

## API 호출 옵션 권장

- `model="gpt-image-2"`
- `size="1024x1536"`
- `quality="medium"` (기본). 일반 시리즈는 medium 으로 충분 (~$0.04/장). 핵심 시리즈만 `high` 로 (~$0.17/장).
- `seed=<series 별 고정 정수>`. 시리즈 안에서 카드끼리 톤 일관성 가장 큰 레버.
- `response_format="b64_json"` (명시).
- 카드 2~N 은 가능하면 카드 1 의 결과 이미지를 `reference_images` 로 추가 전달해 톤 락. SDK 가 미지원이면 무시하고 seed 만 의존.

## 시리즈 길이 가이드

- 4장: 너무 짧음. 핵심만 있을 때.
- 5장: 기본. 도입 / 무엇이 / 어떻게 / 왜 중요 / 정리.
- 6장: 중대 발표나 비교 시리즈에 한정.
- 7장 이상은 만들지 말 것. 모바일 독자가 끝까지 안 봄.

## 금지

- 그라디언트, 드롭섀도우, 글로우 효과
- 스톡 사진, 인물 사진
- 영어 번역 캡션
- 이모지, 데코레이션 한글 (장식용 한글)
- 워터마크, 로고
- 한 카드에 여러 메시지
