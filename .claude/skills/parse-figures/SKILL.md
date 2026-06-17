---
name: parse-figures
description: Cleanly separate the figures and tables (도식) out of a PDF — especially arXiv papers — by having a vision model read coordinate-gridded page renders and report crop bounding boxes, instead of dumping embedded image objects. Use this whenever the user wants to extract / crop / 분리 figures, diagrams, architecture figures, plots, or tables from a paper or PDF, or says PyMuPDF / pdfimages crop came out wrong or missed vector diagrams. share-news can call this as its figure-extraction step. Currently PDF input only.
---

# parse-figures

PDF에서 **그림·표(도식)를 사람 눈에 보이는 블록 단위로 깔끔하게 잘라낸다.** 핵심 전제: `PyMuPDF.get_images()` / `pdfimages` 처럼 PDF에 박힌 raster 객체를 덤프하는 방식은 (1) 벡터로 그린 아키텍처 다이어그램을 통째로 놓치고 (2) 멀티패널 그림을 조각내고 (3) 표를 못 잡고 (4) 번호가 어긋난다. 그래서 여기서는 **페이지를 렌더 → 좌표 그리드를 입혀 비전 모델(Claude)에게 보여주고 → 모델이 bbox를 지정 → 그 좌표로 크롭**한다.

비용 효율이 설계의 일부다: 전체 페이지가 아니라 **캡션이 있는 페이지만** 골라 렌더하고, 페이지별 탐지는 **haiku 경량 서브에이전트를 병렬**로 돌린다.

## 입력 / 출력

- 입력: 로컬 `.pdf` 한 개. (텍스트·URL은 범위 밖. 그림/표 크롭 전용.)
- 출력: `<out-dir>/figure-1.png`, `table-2.png` ... + `manifest.json`
  (`{type,label,page,image,caption,bbox_px,table_markdown?}` 목록).
- 파일명은 **논문의 실제 라벨**(Figure 3 → `figure-3.png`)이지 등장 순서가 아니다.

share-news가 호출하면 `--out-dir docs/<topic>/<date>-<slug>/assets` 를 받아 거기에 떨군다.

## 좌표계 (모델이 보고 쓰는 단위)

그리드 이미지는 페이지 콘텐츠 바깥 여백에 좌표 눈금을 그려둔다:

- `x`: 0 .. 1000 (콘텐츠 좌→우, 여백 제외)
- `y`: 0 .. norm_h (위→아래, `norm_h = round(1000 * 높이/너비)` — 세로로 긴 페이지면 1200~1400 정도)
- 격자선과 라벨은 `--grid-step`(기본 50)마다. 빨강=x(상하 여백), 파랑=y(좌우 여백).

모델은 이 눈금을 읽어 `[x0,y0,x1,y1]`(정규화)로 답하고, `crop_figures.py`가 깨끗한(격자 없는) 렌더 위 픽셀로 환산해 자른다.

## 절차

### 0. 준비
- 입력이 `.pdf`인지 확인. 의존성 없으면 `pip install -r .claude/skills/parse-figures/requirements.txt`.
- 스크립트 경로: `.claude/skills/parse-figures/scripts/`.
- 작업 디렉토리(렌더 산출물) 하나 정한다. 예: `<pdf>-figwork/`. 최종 크롭은 `--out-dir`.

### 1. 스캔 — 도식이 있는 페이지만 추린다 (비용 필터, 무료)
```bash
python .../scripts/grid_render.py <pdf> --scan
```
캡션(라인 시작 `Figure N.` / `Table N:` 등)을 가진 페이지만 후보로 나오고, 각 후보의 `captions`에 **타입·라벨·캡션 텍스트**가 딸려온다. 이게 다음 단계 서브에이전트에게 줄 "이 페이지엔 이게 있을 것" 힌트다.

- 후보가 너무 많고(부록 표 등) 사용자가 본문만 원하면 `--pages`로 범위를 좁힌다.
- 캡션이 0개인데 그림이 분명하면(드묾) `--pages`로 직접 지정. 스캔은 캡션 0일 때만 이미지/벡터 페이지를 fallback 후보로 내놓는다.

### 2. 렌더 — 후보 페이지에 그리드를 입힌다
```bash
python .../scripts/grid_render.py <pdf> --out-dir <figwork> --pages 2,3,5,7
```
페이지마다 `page-N.png`(깨끗한, 크롭용) + `page-N.grid.png`(눈금 입힌, 모델용) + `pages.json`(좌표 환산 메타) 생성. `--pages` 생략 시 스캔 후보 전부.

### 3. 탐지 — 페이지별로 모델이 bbox를 찍는다
**후보 페이지가 적으면(≲3) 메인 에이전트가 직접** `page-N.grid.png`를 `Read`로 보고 박스를 잡는다.
**많으면 페이지당 haiku 서브에이전트 1개를 병렬로** 띄운다(한 메시지에 여러 Task, 동시 8~10개씩). 개별 작업은 "한 페이지에서 그림/표 박스 찍기"라 쉬워서 경량 모델로 충분하다.

서브에이전트는 **기하(bbox)만** 책임진다. 캡션 텍스트와 표 셀은 뒤에서 PDF 텍스트 레이어로 정확히 채우므로(경량 모델이 150dpi에서 숫자를 옮기면 환각한다), 프롬프트에서 텍스트 전사를 요구하지 않는다. 각 서브에이전트에 주는 프롬프트:

```
You locate figures/tables on one rendered paper page and return their crop boxes.
Use the Read tool to view this gridded image: <figwork>/page-<N>.grid.png

The page is overlaid with a coordinate grid; labels sit in the outer margins.
Coordinates are normalized: x runs 0..1000 left→right; y runs 0..<norm_h> top→bottom
(red x-labels top/bottom, blue y-labels left/right). Grid lines every <grid_step>.

This page is expected to contain: <captions: e.g. "Figure 1 (figure), Table 2 (table)">.
Trust the IMAGE — include any real figure/table you see, skip headers/footers/body.

Give one box per item that ENCLOSES the whole visual block PLUS its caption line.
Boxes commonly come out too SMALL — clipped legends, axis labels, far columns,
bottom rows, leftmost row labels. Err LARGE: extend each edge until you are sure
no content is cut; a strip of surrounding whitespace is fine, clipping is not.

Rules that fix the usual mistakes:
- The running page header/title at the very top and the footer/page number at the
  bottom are NOT part of any figure. Start the box BELOW the header, end it ABOVE
  the footer.
- For two-column pages, a single-column figure/table still spans its FULL column
  width — read the real right edge off the grid, don't guess narrow. For a table,
  extend LEFT until the row-name labels are fully inside and RIGHT past the last
  data column.
- Tables can be STACKED vertically in one column. Each "Table N" caption belongs to
  exactly ONE table. Box each table from its top rule to its bottom rule (plus its
  caption); do NOT merge two tables and do NOT include the body paragraphs sitting
  between them. If a region is running prose, it is not a table — skip it.

Return ONLY a JSON array, no prose, NO caption/table text:
[
  {"page": <N>, "type": "figure"|"table", "label": "<paper's number, e.g. 3>",
   "bbox": [x0, y0, x1, y1]}
]
If the page has no real figure/table, return [].
```

서브에이전트가 돌려준 배열들을 모아 하나의 `boxes.json`(평평한 리스트)로 합친다. `crop_figures.py`가 라벨로 정확한 캡션을 매칭하고, 표는 `find_tables`로 진짜 셀을 뽑아 manifest에 넣는다.

### 3.5. 보정 — PyMuPDF 기하로 박스 가장자리를 스냅 (권장)
```bash
python .../scripts/refine_boxes.py \
    --pages-json <figwork>/pages.json \
    --boxes <figwork>/boxes.json \
    --out <figwork>/boxes.refined.json
```
VLM은 **영역**은 맞게 잡지만 **가장자리**가 어긋난다(보통 살짝 작게 — 범례·축 라벨·맨 아랫줄·맨 왼쪽 행 라벨이 잘림, 가끔 헤더를 먹음). PyMuPDF는 페이지의 모든 text line·이미지 rect·벡터 drawing·표 괘선의 **정확한 좌표**를 안다. `refine_boxes.py`는 각 VLM 박스와 겹치는 실제 잉크 요소들의 tight union으로 가장자리를 스냅한다:

- 30% 이상 겹치는 atom만 사용(살짝 잘린 요소까지 끌어와 확장) → 페이지 18% 이내로 확장 제한(폭주 방지).
- **노이즈 차단**: 페이지를 가로지르는 광역 drawing(클리핑 패스/배경)은 제외 — 옆 컬럼으로 박스가 새는 걸 막는다. 헤더/푸터 밴드의 머리글·쪽번호도 제외. text·이미지 atom은 항상 신뢰.
- 얇은 괘선(zero-height)은 1pt로 살려 표의 상·하단 괘선이 박스에 포함되게 한다.

이 단계는 PyMuPDF를 **1차 탐지기가 아니라 보정기**로만 쓴다(find_tables/get_drawings 단독은 스택 표를 놓치거나 그림을 표로 오인하므로 탐지는 VLM이 맡는다).

**캡션 제외(기본).** `refine_boxes.py`는 그림/표의 캡션 텍스트를 찾아(scan과 동일 정규식) 크롭에서 **빼낸다** — 캡션이 그림 아래면 아래를, 표 위면 위를 잘라 캡션 글자가 이미지에 안 보이게 한다(방향 자동 판별). 캡션 텍스트 자체는 `crop_figures.py`가 PDF 텍스트 레이어에서 뽑아 manifest의 `caption`에 그대로 들어가므로, 본문엔 `![](fig)` + 빈 줄 + *캡션* 형태로 따로 쓸 수 있다. 캡션을 이미지에 포함하고 싶으면 `--keep-caption`.

### 4. 크롭
```bash
python .../scripts/crop_figures.py \
    --pages-json <figwork>/pages.json \
    --boxes <figwork>/boxes.refined.json \
    --out-dir <out-dir> --pad 6
```
보정한 `boxes.refined.json`을 깨끗한 렌더에서 잘라 `figure-N.png`/`table-N.png` 저장, `manifest.json` 출력. (보정 단계를 건너뛰면 `boxes.json`을 그대로 넣어도 된다 — 이때는 캡션이 크롭에 포함되니 `--pad 10`.) 보정을 쓰면 가장자리가 이미 잉크에 맞춰져 있어 `--pad`는 6 정도면 충분하다.

### 5. 검수 + 보고
- `manifest.json`의 핵심 크롭 몇 개를 `Read`로 시각 확인한다 — 잘림/헤더 혼입/빈 박스가 없는지. 어긋난 항목만 해당 페이지를 다시 보고 박스를 고쳐 그 항목만 재크롭한다.
- 사용자가 결과를 눈으로 확인하고 싶어 하면 **리뷰 HTML**을 만든다 (이미지 base64 임베드 → 단일 파일, WSL/headless에서도 그냥 열림):
  ```bash
  python .../scripts/review.py --manifest <out-dir>/manifest.json \
      --out <work>/review.html [--old-dir <get_images_dump>] [--title "..."]
  ```
  `--old-dir`를 주면 기존 `get_images()` 덤프와 나란히 비교해 보여준다(벡터·표를 못 잡는 한계가 한눈에). 생성 후 WSL이면 `explorer.exe "$(wslpath -w <path>)"`로 연다.
- 사용자(또는 share-news)에게 `out-dir`, 크롭 개수, 라벨 목록을 보고. 표는 `table_markdown`도 manifest에 들어있음.

## 품질 노트 (왜 이렇게 하나)

- **그리드가 정확도의 핵심.** 비전 모델은 맨 이미지에서 절대 픽셀을 못 맞추지만, 눈금이 있으면 "선 200~600 사이"로 읽어낸다. 박스가 자꾸 어긋나면 `--grid-step`을 50으로 줄여 눈금을 촘촘히.
- **VLM은 탐지, PyMuPDF는 보정.** VLM 박스의 어긋난 가장자리를 `refine_boxes.py`가 실제 잉크 좌표로 스냅한다(3.5단계). VLM이 살짝 작게 잡아 컬럼·행을 잘라먹던 게 가장 흔한 실수인데, 이걸 정확히 메운다. PyMuPDF를 탐지에 쓰지 않는 이유: find_tables는 스택 표를 놓치고 그림을 표로 오인하며, get_drawings는 클리핑 패스 같은 노이즈가 많다.
- **캡션 제외가 기본.** 크롭에서 캡션 글자를 빼내 깨끗한 도식만 남긴다(3.5단계). 캡션 텍스트는 manifest의 `caption`에 그대로 있으니, 본문엔 `![](fig)` + 빈 줄 + *이탤릭 캡션* 으로 따로 쓴다(study-paper/share-news 패턴과 일치, 프리뷰에서 캡션이 그림 옆에 붙지 않음). 이미지에 캡션을 굽고 싶으면 `--keep-caption`.
- **라벨은 캡션에서.** scan이 `Figure 3`을 읽어 `figure-3.png`로 떨군다. 등장 순서 번호(`fig-N`)와 논문 번호가 어긋나던 발행 파이프라인의 고질병을 없앤다.
- **비용.** 무료 스캔으로 페이지를 거르고, 페이지당 haiku 1회. 50페이지 논문이라도 그림/표 있는 ~20~30페이지만, 그것도 경량 모델로. 보정(3.5)은 스크립트라 무료.

## 에러 처리
- PyMuPDF/Pillow 미설치 → requirements 설치.
- 박스가 헤더/푸터를 먹음 → 보정(3.5)이 보통 헤더 밴드를 잘라낸다. 그래도 남으면 y0를 키워 머리글 아래로.
- 보정이 박스를 옆 컬럼으로 넓힘 → 광역 drawing 노이즈일 수 있다. `refine_boxes.py`의 `MAX_EXPAND`(기본 0.18)를 줄이거나, 해당 박스만 `boxes.json`을 손봐 다시 돌린다.
- 캡션이 크롭에 남음 → scan이 그 라벨의 캡션을 못 읽은 경우다. `--grid-step`/`--pages` 문제 아님 — manifest의 `caption`이 비었는지 확인하고, 비었으면 본문에서 캡션을 직접 채운다.
- 벡터 다이어그램이 흐릿 → `--dpi`를 200~300으로 올려 렌더.
- 스캔이 본문 언급을 후보로 잡는 듯하면(드묾) 정상이다 — 라인 시작+구분자만 캡션으로 인정하므로 본문 "see Figure 2"는 걸러진다.
