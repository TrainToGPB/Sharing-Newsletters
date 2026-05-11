---
title: "왜 또 한 번 해석가능성인가 — NLA의 자리매김"
date: 2026-05-11
author: TrainToGPB
tags:
  - interpretability
  - nla
  - anthropic
  - mechanistic-interpretability
  - auditing
source: https://transformer-circuits.pub/2026/nla/index.html
summary: "Anthropic의 Natural Language Autoencoders(NLA)가 기존 해석가능성 도구의 어떤 빈자리를 메우는지를 정리한다."
format: details
part: 1
---

# 왜 또 한 번 해석가능성인가 — NLA의 자리매김

> 원본: [transformer-circuits.pub/2026/nla](https://transformer-circuits.pub/2026/nla/index.html)

이 글은 Anthropic이 2026년 5월 7일 Transformer Circuits Thread에 공개한 "Natural Language Autoencoders Produce Unsupervised Explanations of LLM Activations" (Fraser-Taliente·Kantamneni·Ong et al., 2026) 의 첫 번째 정리다. 본 편은 본격적인 방법론으로 들어가기 전에, 왜 또 하나의 해석가능성 도구가 필요했는지 — 즉 NLA가 기존 도구 지형 어디에 자리 잡는지 — 를 정리한다.

## 활성값은 왜 이렇게 읽기 어려운가

언어 모델은 자신의 내부 상태를 고차원 활성값(activation) 벡터로 인코딩한다. 모델 내부 어딘가에 있는 잔차 스트림(residual stream)에서 어느 한 토큰, 어느 한 레이어의 활성값을 끄집어내면 우리가 얻는 건 그저 $d_\text{model}$ 차원의 실수 리스트다. 이 벡터는 모델의 다음 토큰 예측, 응답 스타일, 사용자에 대한 추정, 안전 관련 판단까지 — 풍부한 계산 결과를 응축해 담고 있지만, 사람 눈에는 의미 없는 숫자 뭉치다.

그래서 해석가능성(interpretability) 분야는 본질적으로 한 가지 질문에 매달려 왔다. 이 활성값 $h_l$ 안에 정확히 무엇이 들어 있는가, 그리고 우리는 그걸 어떻게 읽어낼 수 있는가? 자연어로 직접 번역만 해 줘도 모델 내부 상태가 곧장 사람이 읽을 수 있는 텍스트가 되고, 디버깅·감사·정렬 평가가 한 단계 쉬워진다. NLA가 정확히 이 번역기 역할을 자처한다.

## 기존 도구들이 메운 자리, 그리고 그 한계

NLA가 등장한 배경을 이해하려면 기존 해석가능성 도구들이 어떤 트레이드오프 위에 서 있었는지 짚어야 한다. 원문 Related Work 섹션은 이를 두 축 — 비지도(unsupervised) vs 지도(supervised), 그리고 출력이 자연어인가 vs 고정된 사전(dictionary)인가 — 으로 나누어 설명한다. 핵심만 정리하면 다음과 같다.

**Logit lens**는 중간 레이어 활성값을 모델의 unembedding 행렬에 통과시켜 어휘(vocab) 위 분포로 투영한다. 출력이 토큰 확률이라 직관적이지만, 표현력이 "토큰들의 가중합" 이라는 아주 좁은 형태에 갇힌다. 모델이 추상적 개념을 표현하고 있더라도, 그것이 어떤 토큰 시퀀스로도 자연스럽게 매핑되지 않으면 logit lens는 그 개념을 비춰주지 못한다.

**Sparse autoencoders (SAE)**는 비지도 재구성 손실로 활성값을 학습된 사전 피처(dictionary feature)들의 희소 선형 결합으로 분해한다. 비지도라는 점에서 매력적이지만 세 가지 한계가 있다. 첫째, 표현은 여전히 고정된 사전의 원소들의 가중합으로 한정된다. 둘째, 사전이 학습되는 분포에 따라 커버리지에 구멍(coverage gap)이 생긴다 — 학습 데이터에서 드물게 등장하거나 여러 문서에 흩어져야만 형성되는 개념은 SAE가 깨끗한 피처로 잡아내지 못한다. 셋째, 발견된 피처를 사람이 읽으려면 추가 해석 단계가 필요하다. 보통은 그 피처가 강하게 활성화되는 top-activating 예시들을 사람이 또는 다른 모델이 들여다보고 "이 피처는 X 같다" 라고 라벨을 붙이는 식이다. 시간이 들고, 라벨이 정확하다는 보장도 없다.

**Activation oracles (AO)** — Pan et al., Costarelli et al., Choi et al. 계열의 작업, 그리고 이를 명시적으로 그렇게 명명한 Karvonen et al. — 은 다른 방향으로 간다. 활성값을 입력으로 받아 자연어로 답하는 LLM을 지도 학습한다. 출력이 자연어이므로 직접 읽을 수 있다는 장점이 있지만, 학습 데이터가 (활성값, 정답 자연어) 쌍이어야 한다. 정답을 어디서 얻는가? 보통은 시스템 프롬프트가 어떤 정보를 명시적으로 알려주고, 그 명시적인 정보를 활성값에서 다시 끌어내도록 시키는 식이다. 이 구도는 학습 분포를 좁게 만들고, 결과적으로 "학습 시 본 종류의 질문" 너머로 일반화하기를 강하게 가정해야 한다. 라벨링할 수 있는 정보만 다룰 수 있다는 본질적 제약이다.

이 셋을 한눈에 보면 다음과 같다.

| 방법 | 비지도? | 출력 형태 | 주요 한계 |
| --- | --- | --- | --- |
| Logit lens | 비지도 | 어휘 토큰 가중합 | 표현력이 토큰 확률에 갇힘 |
| SAE | 비지도 | 사전 피처 가중합 | 사전 커버리지 갭 + 추가 해석 단계 필요 |
| Activation oracle | 지도 | 자연어 | 라벨 데이터 의존, 좁은 학습 분포 |

비지도이면서 출력이 자연어인 칸은 비어 있었다. NLA는 정확히 그 빈칸을 노린다.

## NLA의 자리매김 — 두 축의 교차점

NLA(Natural Language Autoencoder)는 이름 그대로 활성값을 자연어로 한번 압축했다가 다시 활성값으로 복원하는 자동인코더다. 두 모듈로 구성된다.

- **Activation verbalizer (AV)**: 활성값 $h_l$ 을 입력으로 받아 자연어 설명 $z$ 를 생성한다.
- **Activation reconstructor (AR)**: 그 설명 $z$ 만 보고 원래 활성값 $\hat{h}_l$ 을 복원한다.

학습은 단 하나의 목적 — 재구성 오차 최소화 — 으로 이루어진다.

$$
\mathcal{L} = \mathbb{E}_{h_l \sim \mathcal{H}}\,\|h_l - \text{AR}(\text{AV}(h_l))\|_2^2
$$

여기서 $\mathcal{H}$ 는 타겟 모델 $M$ 의 레이어 $l$ 활성값 분포다. 라벨도 없고, 자연어 $z$ 가 사람에게 읽히게 만들라는 명시적 보상도 없다. 그저 "텍스트 병목을 통과시켜도 활성값이 그대로 복원되어야 한다" 가 전부다. 그런데도 — 적절한 초기화와 약간의 KL 정규화가 더해지면 — AV가 만들어내는 $z$ 는 사람이 읽을 수 있는 자연어 설명으로 수렴한다.

이 한 문장에 NLA의 자리매김이 담겨 있다. **재구성 손실 기반 비지도 + 자연어 직접 출력**, 즉 SAE 류의 비지도성과 AO 류의 자연어 표현력을 한꺼번에 가져간다. 라벨이 필요 없으니 학습 분포가 좁아지지 않고, 출력이 자연어이니 별도 해석 단계 없이 바로 읽힌다. 표현 공간도 고정된 사전이 아니라 자연어 전체이므로 logit lens·SAE 보다 훨씬 풍부한 가설 생성이 가능하다.

저자들의 표현 그대로, NLA는 "비지도 개념 발견 방법(SAE 등) 과 지도 활성값 자연어화 방법(AO 등) 사이를 잇는 다리(bridge)" 로 자리매김한다.

## 이 방식이 실제로 통한다는 미리보기

논문이 보여주는 결과는 크게 네 갈래로 나뉘는데, 본 시리즈에서는 뒤편들에서 하나씩 자세히 다룬다. 자리매김 이야기에서 미리 짚어둘 만한 핵심만 추리면 다음과 같다.

- **사전 배포 감사에서의 실전 활용**. NLA는 Claude Opus 4.6 의 출시 전(pre-deployment) 정렬 감사에 실제로 투입됐다. 영어 프롬프트에 갑자기 러시아어로 답하는 현상의 원인을 NLA 설명이 가리켰고, 이는 잘못 만들어진 SFT 데이터(영어 번역된 프롬프트와 원어 응답이 잘못 짝지어진 것)까지 추적되어 실제로 문제 데이터를 발견하는 데 기여했다. 도구 호출 결과를 모델이 무시하고 자기가 미리 계산한 답을 출력하는 "misreported tool calls" 현상도 NLA가 던진 가설 ("모델이 491 을 미리 캐시하고 도구의 492 를 무시한다") 을 attribution graph 가 독립적으로 확증하는 식으로 굳어졌다.

- **Unverbalized evaluation awareness**. 모델이 "이건 평가 상황 같은데" 라고 내심 의심하면서도 출력에는 한 마디도 안 비치는 경우가 있다. 정렬 평가의 신뢰성을 흔드는 현상인데, 출력만 보면 잡히지 않는다. NLA 설명에는 잡힌다. 저자들은 평가 vs 배포 트래픽 비교, 평가 인식 방향으로의 활성값 스티어링, 프롬프트의 현실성 편집 — 이 세 가지 조작 모두에서 NLA-측정 평가 인식이 예측 방향으로 움직임을 보였다. 평가 표현이 0% 인 트랜스크립트에서도 NLA-측정 인식이 5% 를 넘는 사례가 16개 평가 중 7개나 됐다.

- **의도적으로 misalign 된 모델에 대한 감사 성공**. Marks et al. 의 모델 오가니즘(reward-model sycophancy) 을 대상으로 한 자동 감사 게임에서, NLA-장착 에이전트는 모델 오가니즘의 학습 데이터에 접근하지 않고도 근본 원인을 짚어냈다. 기존 작업이 학습 데이터 검색에 결정적으로 의존했던 것과 다르다. 이는 NLA가 단순히 학습 데이터의 의미 검색 인터페이스 역할만 하는 게 아니라, 활성값에 인코딩된 정보를 실제로 끌어올린다는 증거가 된다.

이 결과들은 본 시리즈의 케이스 스터디 편(part 4·5)과 감사 편(part 6)에서 본격적으로 다룬다.

## 미리 인정하고 갈 한계 — confabulation

자리매김을 이야기하면서 한 가지 한계를 미리 인정하고 가야 공정하다. NLA 설명은 종종 검증 가능한 거짓 진술 — 입력 컨텍스트에 대한 사실관계 오류 — 을 포함한다. 저자들이 confabulation 이라고 부르는 현상이다. Planning in Poetry 케이스 스터디의 NLA 설명은 존재하지도 않는 이전 컨텍스트("Here is a verse that's short and sweet.") 를 인용하고, 한국 역사 텍스트에 대한 설명에서는 컨텍스트에 없는 "Joseon Wangjo Sillok" 같은 구체 출처를 갖다 붙이기도 한다.

다만 저자들의 분석에 따르면 이 confabulation 들은 무작위가 아니다. (1) 주제 단위 진술(thematic claim) 이 구체 디테일 진술보다 정확한 경향이 있고, (2) 여러 인접 토큰의 NLA 설명에 반복적으로 등장하는 진술이 더 신뢰할 만하며, (3) 거짓 진술이라도 컨텍스트 주제와는 대체로 연관된다. 그래서 실무 사용 가이드라인은 단순하다 — 개별 사실 주장보다 반복 등장하는 테마를 읽어라. confabulation 의 본격적인 분석과 실무 메모는 part 5 에서 따로 다룬다.

## 누가, 언제, 어디에서 발표했나

- **저자**: Kit Fraser-Taliente, Subhash Kantamneni, Euan Ong (이상 동등 1저자), Dan Mossing, Christina Lu, Paul C. Bogdan, Emmanuel Ameisen, James Chen, Dzmitry Kishylau, Adam Pearce, Julius Tarng, Alex Wu, Jeff Wu, Yang Zhang, Daniel M. Ziegler, Evan Hubinger, Joshua Batson, Jack Lindsey, Samuel Zimmerman, Samuel Marks
- **소속**: Anthropic
- **발표일**: 2026년 5월 7일
- **공개**: Transformer Circuits Thread
- **부속 자원**: 학습 코드, Qwen-2.5-7B / Gemma-3-12B / Gemma-3-27B / Llama-3.3-70B 에 대해 학습된 NLA 가중치, 그리고 Neuronpedia 와의 협업으로 만든 인터랙티브 프론트엔드

오리지널 NLA 아키텍처는 Kit Fraser-Taliente 가 Anthropic Fellows Program 에 있을 때 제안했고, Euan Ong 이 별도로 발전시키던 유사 아이디어 — 풀-파라미터 파인튜닝과 SFT 워밍업 (warm-start) — 와 합쳐 현재 형태가 되었다는 점도 author contribution 에 명시되어 있다. 동시기에 Chalnev 가 독립적으로 Cycle-Consistent Activation Oracles 라는 아주 가까운 접근(설명자-복원자 쌍 + KL 페널티 하 RL) 에 도달했고, 본 논문은 그것과의 차이를 "frontier 스케일에서 검증, 감사 도구로서의 평가" 로 잡는다.

## 다음 편에서 다룰 것

자리매김이 정리됐으니 다음 편에서는 그 자리매김을 가능하게 하는 구조 — 두 LLM 모듈 (AV·AR), 워밍업, RL 학습 루프, 그리고 텍스트 병목이 왜 정말로 자연어로 수렴하는지 — 를 따라간다. 특히 AV 가 활성값을 토큰 임베딩 자리에 주입받는 트릭과, AR 이 layer-$l$ 까지만 잘라낸 절단 모델이라는 점, 그리고 GRPO 기반의 비대칭 업데이트(AR 은 회귀, AV 는 RL) 가 핵심이다.

다음 편: [두 모델 한 병목 — AV·AR 과 자연어 자동인코더의 구조](02-method-architecture.md)

## 출처

- 원문: <https://transformer-circuits.pub/2026/nla/index.html>
- 인용: Fraser-Taliente, Kantamneni, Ong et al., "Natural Language Autoencoders Produce Unsupervised Explanations of LLM Activations", Transformer Circuits, 2026.
