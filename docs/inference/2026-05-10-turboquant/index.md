---
title: TurboQuant — 학습 없는 KV 캐시·벡터 압축의 새 기준
date: 2026-05-10
author: Claude
tags: [inference, quantization, kv-cache, vector-search, turboquant, qjl, polarquant]
source: https://research.google/blog/turboquant-redefining-ai-efficiency-with-extreme-compression/
summary: 랜덤 회전으로 좌표 분포를 알려진 모양으로 만들고, MSE 양자화에 1-bit QJL 잔차 보정을 더해 KV 캐시를 6배 압축하면서 정확도 손실 없이 H100 에서 키 어텐션을 8배 가속하는 학습·데이터 비의존 양자화 (Google Research, ICLR 2026).
format: abstract
---

# TurboQuant — 학습 없는 KV 캐시·벡터 압축의 새 기준

Google Research 가 ICLR 2026 에 발표하는 TurboQuant 는 LLM KV 캐시와 대규모 벡터 검색 인덱스를 동시에 겨냥한 양자화 알고리즘이다. 학습이나 캘리브레이션 데이터 없이 닫힌형으로 동작하면서, 보고된 벤치마크에서 KV 메모리를 6배 줄이고 H100 에서 4-bit 키 어텐션을 32-bit 대비 8배 빠르게 만든다. 이 글은 메인 블로그와 함께 묶여 발표된 세 논문 — QJL (1-bit Quantized Johnson-Lindenstrauss), PolarQuant (재귀적 극좌표 양자화), TurboQuant (2단계 합성) — 의 흐름을 한 시리즈로 정리한다.

## 핵심 포인트

- **랜덤 회전이 출발점.** 입력 벡터를 Randomized Hadamard Transform 으로 회전시키면 좌표가 고차원 구 위에 균일 분포해, 좌표 한 개의 분포가 닫힌형 (Beta 류) 으로 알려진다. 토큰·채널이 모두 같은 분포라 코드북을 하나만 쓴다.
- **메타데이터 0 이 결정적.** 좌표마다 다른 zero point/scale 을 저장할 필요가 없어 비트 예산이 그대로 압축률에 반영된다. 4-bit 가 사실상 4-bit 다.
- **QJL → PolarQuant → TurboQuant 의 누적.** QJL 은 부호 비트 1 개로 정규화 없는 비편향 내적 추정을, PolarQuant 는 극좌표 변환으로 데이터 비의존 코드북을, TurboQuant 는 둘을 합쳐 임의 비트 예산에서 정보이론 하한 근접 왜곡을 달성.
- **2단계 알고리즘.** (b−1) 비트의 Lloyd-Max 최적 스칼라 양자화로 MSE 를 떨어뜨리고, 마지막 1 비트 QJL 잔차로 내적 편향을 정확히 상쇄해 비편향 추정량을 만든다.
- **학습·데이터 비의존.** 새 모델·새 도메인이 와도 재캘리브레이션 없음. KV 캐시 운영팀과 임베딩 인덱스 운영팀 양쪽이 동일한 알고리즘 하나로 커버된다.

## 한 페이지 요약

LLM 인퍼런스에서 KV 캐시는 더 이상 보조 항목이 아니다. 컨텍스트가 길어지고 배치가 커지면서 가중치보다 캐시가 메모리·대역폭의 1차 병목이 됐다. 가중치용 양자화 레시피 (AWQ, GPTQ, RTN) 를 그대로 옮기면 정규화 상수 저장 오버헤드가 압축률을 깎아먹고, 키별 outlier 와 어텐션 내적의 민감성이 품질을 무너뜨린다. 벡터 검색 (MIPS, ANN) 도 같은 벽에 있다 — Product Quantization, RaBitQ 류는 데이터 학습이 필요해 임베딩이 자주 바뀌는 환경에서 운영 부담이 크다.

TurboQuant 의 출발점은 정반대다. **데이터에 코드북을 맞추는 대신, 데이터를 분포가 알려진 모양으로 먼저 바꿔놓는다.** 입력 벡터에 Randomized Hadamard Transform 을 통과시키면 좌표가 고차원 구 위 균일 분포를 따르고, 한 좌표의 분포는 변환된 Beta(1/2, (d−1)/2) 형태로 닫힌형이 된다. 이 분포는 모델·데이터 무관 상수다. 따라서 그 분포에 대한 Lloyd-Max 최적 스칼라 양자화기를 미리 한 번 짜두고, 모든 토큰·채널이 같은 코드북을 쓴다. zero point, scale 같은 메타데이터가 사라진다.

여기까지는 MSE 만 좋다. 어텐션은 쿼리·키 내적에 민감한데, MSE 가 같아도 양자화 결과를 곱하면 내적 추정에 편향이 쌓인다. TurboQuant 는 1단계 잔차에 QJL 의 1-bit 부호 양자화를 한 번 더 얹어, 그 1 비트를 1단계 편향을 정확히 상쇄하는 보정항으로 설계한다. 두 항을 합친 최종 내적 추정량은 비편향이고, 임의 비트 예산 b 에서 MSE 와 내적 둘 다 정보이론 하한의 작은 상수배 안에 들어온다.

이 알고리즘은 단독 발명이 아니라 같은 그룹이 쌓아온 세 단계의 정점이다. **QJL (2024)** 이 정규화 없는 1-bit 비편향 양자화를 제안했고, **PolarQuant (2025)** 가 좌표를 재귀적으로 극좌표로 풀어 각도 분포를 분석적으로 양자화했으며, **TurboQuant (2025)** 가 둘을 합쳐 임의 비트 예산으로 일반화했다. 세 논문 모두 데이터 비의존, 학습 0 이라는 점에서 같은 흐름이다.

벤치마크는 두 무대를 본다. KV 캐시 쪽에서는 키 3-bit + 값 4-bit 조합이 cosine similarity 0.997 로 거의 무손실, 메모리 6배 절감, H100 에서 키 어텐션 8배 가속이 보고된다. vLLM 통합 재현 구현은 Qwen3.5-27B 에서 최대 토큰 수 2배 (457k → 914k), needle-in-a-haystack 5/5 통과를 확인했다. 벡터 검색 쪽에서는 같은 비트 예산에서 RaBitQ 등 학습형 SOTA 와 동등한 recall 을, 학습 0·인덱스 빌드 시간 0 으로 달성한다.

한계도 분명하다. 현재 효과는 full-attention 레이어에 한정되고, 슬라이딩 윈도우·linear-attention 부분은 별도다. 2-bit 값 양자화는 cosine sim 0.94 로 품질 병목이 보여 안전 마진을 잡으려면 4-bit 값을 권장한다. prefill 단계 이득은 제한적이고 디코드 (긴 컨텍스트) 가 본 무대다. MoE 모델은 어텐션 외 비중이 커서 전체 가속비가 dense 보다 작다.

이 시리즈는 다음 순서로 흐른다. 1편이 KV 캐시 양자화의 어려움과 자리잡기를, 2편이 랜덤 회전이 만드는 Beta 분포 통찰을, 3편이 QJL 과 PolarQuant 두 빌딩 블록을, 4편이 TurboQuant 의 2단계 알고리즘과 near-optimal 이론 결과를, 5편이 시스템 효과·한계·실무 시사점을 다룬다.

## 자세히 보기

<!-- VERSIONS_START -->
1. [왜 KV 캐시 압축이 다시 화제가 됐나](details/01-why-kv-cache-compression/) — KV 캐시 양자화가 어려운 이유와 TurboQuant 의 자리잡기
2. [무작위 회전이 만드는 Beta 분포](details/02-random-rotation-and-beta-distribution/) — 랜덤 직교 회전이 좌표 분포를 알려진 Beta 모양으로 바꿔, 데이터 비의존 코드북과 정규화 상수 0 을 가능케 하는 원리
3. [QJL 과 PolarQuant — 두 빌딩 블록](details/03-qjl-and-polarquant/) — TurboQuant 의 두 전신인 QJL 과 PolarQuant 를 정리한다. 부호 비트 한 개로 내적을 비편향 추정하는 QJL, 좌표를 재귀적 극좌표로 풀고 각도만 양자화하는 PolarQuant — 서로 다른 길이지만 같은 출발점 (랜덤 전처리, 정규화 상수 0) 을 공유한다.
4. [TurboQuant — MSE 와 1-bit 잔차의 2단계 합성](details/04-turboquant-two-stage/) — TurboQuant 는 분포 기반 Lloyd-Max 스칼라 양자화 (b−1 비트) 와 1-bit QJL 잔차 보정을 결합해, 학습 없이 임의 비트 예산에서 정보이론 하한에 가까운 왜곡율을 달성한다.
5. [시스템 효과와 우리에게의 시사점](details/05-system-impact-and-takeaways/) — TurboQuant 가 KV 캐시 운영과 벡터 검색에서 어떤 실측 이득을 내고, 어떤 한계가 남으며, 다른 양자화 흐름과 어떻게 공존하는지 정리한다.
<!-- VERSIONS_END -->

## 출처

- https://research.google/blog/turboquant-redefining-ai-efficiency-with-extreme-compression/
- TurboQuant 논문: https://arxiv.org/abs/2504.19874
- QJL 논문: https://arxiv.org/abs/2406.03482
- PolarQuant 논문: https://arxiv.org/abs/2502.02617
- 재현 구현 (vLLM 통합): https://github.com/0xSero/turboquant
- QJL 원저자 코드: https://github.com/amirzandieh/QJL
