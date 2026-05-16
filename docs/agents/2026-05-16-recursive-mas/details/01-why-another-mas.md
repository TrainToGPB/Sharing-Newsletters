---
title: 왜 또 다른 멀티 에이전트 프레임워크인가
date: 2026-05-16
author: TrainToGPB
tags: [에이전트, 멀티에이전트, 재귀, latent-reasoning, LLM]
source: https://arxiv.org/abs/2604.25917
summary: 단일 LLM 의 한계에서 multi-agent system 으로, 다시 RecursiveMAS 가 latent 공간 재귀로 시스템 전체를 공진화시키려는 동기와 배경.
format: details
part: 1
---

# 왜 또 다른 멀티 에이전트 프레임워크인가

> 원본: [arxiv.org/abs/2604.25917](https://arxiv.org/abs/2604.25917)

![scaling law 와 네 가지 협업 패턴](../assets/fig-1.png)

*Figure 1. 위쪽은 학습·추론 양쪽 재귀 깊이를 키울 때의 scaling law, 아래쪽은 본 논문이 다루는 네 가지 협업 패턴 (Sequential, Mixture, Distillation, Deliberation) 의 한 장 도식.*

## 단일 모델 한 대로는 막히는 지점

언어 모델 한 대로 어려운 문제를 끝까지 끌고 가다 보면 세 가지 한계가 반복적으로 나타난다. 모델 한 대가 담을 수 있는 표현 용량은 유한하고, 토큰을 하나씩 좌에서 우로 뽑는 단방향 디코딩은 근시안적이라 뒤에 가서 앞을 고치기 어렵다. 해 공간 (solution space) 탐색은 비효율적이라 같은 영역을 맴돌거나 막다른 가지에 시간을 쓰기 일쑤다.

이 한계를 시스템 차원에서 풀어보자는 흐름이 multi-agent system (MAS) 이다. 모델 하나하나를 특정 역할에 특화된 에이전트로 보고, 서로 보완적인 강점을 갖도록 묶어 협업시키는 구도다. 대표적으로 두 가지 토폴로지가 자리잡았다.

- Sequential pipeline: Planner $\to$ Critic $\to$ Solver 식으로 역할을 일렬로 잇고, 문제를 단계적으로 분해·검증·해결한다.
- Mixture of specialists: Math, Code, Science 같이 도메인별 전문 에이전트를 병렬로 돌리고 결과를 한 번 더 종합하는 Summarizer 가 답을 낸다.

구조가 있으면 다음 질문은 "이 시스템을 어떻게 시간이 가면서 더 잘 만들 것인가" 다. 한 번 짜둔 파이프라인이 모든 문제에 잘 들어맞을 리 없고, 실제 운영에서는 문제 분포가 바뀌고 도메인이 추가되며 도구도 늘어난다. 여기서 본 논문이 문제 삼는 두 흐름이 갈라진다.

## 기존 MAS 적응의 두 흐름과 한계

기존 MAS 학습·적응 연구는 크게 두 가지 줄기로 정리된다. 둘 다 동작은 하지만, 각자 결정적인 한계를 안고 있다.

### Prompt 기반 적응

첫 번째 줄기는 프롬프트만 다듬는 흐름이다. TextGrad 류처럼 자연어 피드백을 다른 LLM 으로 생성해서 각 에이전트의 컨텍스트·지시문을 반복적으로 보정한다. 구현이 간단하고 모델 가중치를 안 건드려도 된다는 장점이 크다. 공유 컨텍스트를 라운드마다 다시 쓰는 식이라 실험 속도도 빠르다.

문제는 본질적인 한계다. 프롬프트가 좋아진다고 에이전트 자체가 똑똑해지는 건 아니다. 같은 모델이 더 잘 정렬된 답을 내도록 유도할 뿐, 능력의 상한은 그대로다. 또 텍스트 피드백은 결국 자연어 한 번을 더 돌리는 행위라서 시스템 전체의 토큰 비용과 지연이 누적된다. 평가 단계에서 잘 작동하는 프롬프트가 실제 분포에서는 무너지거나, 한 에이전트의 프롬프트 개선이 다른 에이전트의 컨텍스트와 충돌하는 식의 회귀도 흔하다.

### 에이전트별 학습

두 번째 줄기는 각 에이전트를 따로 학습시키는 흐름이다. 역할별 응답을 모아 SFT 또는 RL 로 개별 모델을 튜닝한다. 능력의 상한 자체를 올릴 수 있다는 점이 매력적이다.

그러나 시스템 안에서 에이전트 전체를 학습시키는 건 만만치 않다. 가중치를 전부 업데이트하는 비용도 크지만, 더 본질적인 문제는 협업의 순차 의존성이다. 텍스트 기반 상호작용은 앞 에이전트가 생성을 끝내야 다음 에이전트가 시작할 수 있고, 학습 시에도 이 사슬을 따라 보상이 전파된다. 결과적으로 학습은 느려지고 그래디언트는 텍스트 디코딩이라는 비미분 (argmax) 경계를 건너면서 정보가 빠진다.

또 하나, 각 에이전트를 따로 학습시키면 "어떤 협업 패턴에서 최적이었는가" 가 가중치에 박혀버린다. Sequential 에서 학습한 Planner 를 Mixture 에 그대로 갖다 쓰면 다른 역할의 출력 분포에 안 맞고, 다시 그 패턴에서 튜닝하는 비용이 추가된다. 시스템 구조가 바뀔 때마다 부분 학습을 다시 돌려야 하는 건 운영 비용 측면에서도 부담이다.

요약하면 이렇다.

| 흐름 | 어디서 학습이 일어나나 | 한계 |
| --- | --- | --- |
| Prompt 기반 적응 | 공유 컨텍스트의 반복 보정 | 모델 자체 능력은 안 오름, 토큰 비용 누적 |
| 에이전트별 학습 | 각 에이전트의 가중치 | 학습 비용 큼, 텍스트 매개 협업으로 지연·그래디언트 손실 |

본 논문이 던지는 질문은 그래서 이렇다. 에이전트를 하나씩 떼서 키울 게 아니라, 시스템 전체를 하나의 학습 대상으로 보고 같이 진화시킬 수는 없을까. 즉 협업 자체를 scaling axis 로 끌어올릴 수 있을까.

## Recursive language model 이라는 힌트

이 질문에 본 논문이 차용하는 발상은 최근 등장한 recursive language model (RLM) 이다. RLM 은 별도의 깊은 모델을 쌓는 대신, 같은 레이어 블록을 여러 번 반복 적용해 reasoning 깊이를 늘린다. 한 번 forward 로 끝나던 연산을 latent space 안에서 $L$ 번 돌리는 식이다. 파라미터 수를 늘리지 않고 깊이만 늘릴 수 있어서, 추가 메모리 부담 없이 시험 시간 (test-time) 연산을 더 쏟아붓는 새로운 scaling axis 로 주목받았다.

이 아이디어를 multi-agent 로 끌어올리면 다음과 같은 비유가 성립한다.

- RLM 에서 한 layer 가 latent 표현을 다음 layer 로 넘기듯,
- MAS 에서 한 agent 가 latent 표현을 다음 agent 로 넘긴다.
- RLM 이 같은 layer 스택을 여러 번 도는 것처럼,
- MAS 도 같은 agent 루프를 여러 라운드 돈다.

즉 시스템 전체를 "각 에이전트가 RLM 의 한 layer 처럼 행동하는, latent 공간에서 도는 큰 재귀 연산" 으로 보면, 시스템 단위로 공진화 (co-evolve) 시키는 길이 열린다. 이게 RecursiveMAS 의 출발점이다. 중요한 차이가 있다면, RLM 은 같은 모델을 반복하는 데 비해 RecursiveMAS 는 모델 크기·아키텍처가 다른 이종 에이전트들을 한 루프 안에 묶어야 한다는 점이다. 이 이종성을 어떻게 latent 차원에서 매끄럽게 잇느냐가 곧 RecursiveLink 설계 문제로 이어진다.

## RecursiveMAS 의 큰 그림

RecursiveMAS 는 이 발상을 두 축의 설계로 구체화한다. 자세한 모듈 구조는 다음 편에서 다루고, 여기서는 동기 수준의 큰 그림만 잡는다.

- 모델 파라미터는 그대로 둔다. 대신 에이전트 사이에 가벼운 두 층짜리 잔차 프로젝션 모듈인 RecursiveLink 만 끼워 학습한다.
- 에이전트 내부의 inner link 는 auto-regressive 생성 동안 latent 상태를 다음 스텝의 입력 공간으로 매핑한다.
- 에이전트 사이의 outer link 는 차원이 다른 이종 모델 (Qwen, Llama, Gemma, Mistral 등) 사이에서 hidden representation 을 전달한다.
- 마지막 에이전트의 latent 출력은 다시 첫 에이전트로 돌아가 재귀 루프를 닫는다. 텍스트로 디코딩하는 건 최종 라운드 한 번뿐이다.

학습도 같은 비유를 따른다. inner loop 에서 각 에이전트의 inner link 를 warm-start 한 뒤, outer loop 에서 시스템 전체를 펼친 채 재귀 라운드 전체에 걸쳐 그래디언트를 흘려보낸다. 즉 "내가 직전 라운드에서 낸 latent 가 시스템 최종 답에 어떻게 기여했는가" 를 공유 신호로 받아 모든 outer link 가 같이 움직인다. 가중치가 안 움직이는 백본 모델 자체는 추론 능력의 출발점만 제공할 뿐, "협업을 어떻게 다듬을지" 의 학습 부담은 전부 RecursiveLink 가 떠안는다.

설계 의도 면에서 두 가지 이론적 정당화가 따라온다. 하나는 런타임 복잡도 측면이고, 다른 하나는 학습 동역학 측면이다. 텍스트 매개 협업은 중간 라운드마다 vocabulary 차원으로 토큰을 디코딩·재인코딩해야 하므로 라운드가 깊어질수록 비용이 선형 누적되지만, latent 매개는 그 단계를 건너뛴다. 학습 시에도 텍스트 SFT 는 토큰별 cross-entropy 에서 confident 한 토큰에 대해 그래디언트가 빠르게 0 으로 수렴하는 "gradient vanishing" 을 겪지만, latent 매개는 잔차 경로를 따라 그래디언트가 거의 일정하게 유지된다. 두 가지 정당화는 다음 편 후반부 (Proposition 3.1, Theorem 4.1) 에서 본격적으로 다룬다.

결과만 미리 말하면, 9개 벤치마크 평균에서 가장 강한 baseline 대비 정확도 8.3% 향상, 추론 속도 1.2~2.4 배, 토큰 사용 34.6~75.6% 감소 라는 숫자가 나온다. 숫자의 출처와 조건은 4편과 5편에서 차근차근 본다.

## Preliminary 의 핵심 수식 두 개

본 논문 §2 Preliminary 에서 정리하는 두 개의 식만 미리 확인하고 가자. 다음 편부터의 모든 구조 설명이 이 두 식 위에서 굴러간다.

### Auto-regressive latent generation

표준 Transformer 모델 $\mathcal{M}_\theta$ 가 있고, 어떤 시점 $t$ 에서의 마지막 레이어 hidden state 를 $h_t$ 라 하자. 보통의 auto-regressive 디코딩은 $h_t$ 를 vocabulary 공간으로 사영해서 다음 토큰을 뽑는다. 반면 latent generation 은 $h_t$ 를 다시 다음 스텝의 입력 임베딩으로 그대로 먹인다. 다음-상태는 다음과 같다.

$$
h_{t+1} = \mathcal{M}_\theta\bigl( [E(x_{1:m}),\, h_1,\, h_2,\, \dots,\, h_t] \bigr)
$$

여기서 $E(x_{1:m})$ 은 입력 길이 $m$ 짜리 문제의 임베딩 시퀀스, $h_t$ 는 직전 스텝까지 생성된 "ongoing latent thought" 다. 토큰을 매번 디코딩해서 다시 인코딩하는 절차가 빠진 게 핵심이다.

### RLM 의 $L$ 회 반복

같은 모델을 $L$ 번 재귀로 돌릴 때, $\ell$ 개 layer block 으로 이루어진 stack 을 한 번이 아니라 $L$ 번 반복 적용한다. $L$ 회 째 latent 표현 $H^{(L)}$ 은 다음과 같이 정의된다.

$$
H^{(L)} = \underbrace{\mathcal{M}_\theta \circ \mathcal{M}_\theta \circ \cdots \circ \mathcal{M}_\theta}_{L\ \text{회}} \bigl( E(x_{1:m}) \bigr)
$$

마지막 라운드의 $H^{(L)}$ 만 vocabulary 공간으로 사영해 최종 예측에 쓴다. 중간 라운드는 전부 latent 안에서 일어난다.

이 두 식을 MAS 로 옮기면 그림은 이렇다. 에이전트 $A_i$ 들의 마지막 레이어 표현을 $h^{(i)}$ 라 하고, 시스템 전체의 collective latent state 를 $H = \{h^{(1)}, h^{(2)}, \dots, h^{(N)}\}$ 로 묶는다. Recursive Multi-Agent Evolution 은 이 $H$ 를 라운드마다 점진적으로 다듬어가는 과정으로 정의된다. 즉 각 $A_i$ 가 자기 추론 상태와 다른 에이전트와의 상호작용을 통해 자신의 latent 표현을 갱신해, 시스템 전체가 주어진 문제에 더 잘 정렬되도록 만든다.

## 네 가지 협업 패턴

RecursiveMAS 는 특정 토폴로지에 묶이지 않는다. 본 논문은 흔히 쓰이는 네 가지 패턴 위에 같은 프레임워크를 그대로 얹어 실험한다.

- Sequential Style: Planner, Critic, Solver 세 에이전트를 일렬로 잇는다. Chain-of-agents 셋업을 따라 문제를 분해 $\to$ 판단 $\to$ 정제 $\to$ 해결 순으로 굴린다.
- Mixture Style: Math, Code, Science 같은 도메인 전문 에이전트가 같은 문제를 병렬로 풀고, Summarizer 가 결과를 종합한다.
- Distillation Style: 큰 Expert 에이전트와 작은 Learner 에이전트를 짝지어, 전문성을 latent 로 흘려보내면서 추론 효율은 작은 모델 쪽에 남긴다.
- Deliberation Style: 내성적 추론을 맡는 Reflector 와, Python 코드 실행이나 검색 API 같은 외부 도구를 부를 수 있는 Tool-Caller 를 짝지어, 합의에 도달할 때까지 상호 비판·정제한다.

각 패턴은 에이전트 수, 역할, 도구 사용 여부가 다르지만, RecursiveMAS 입장에서는 "latent space 에서 도는 노드들" 이라는 점에서 동일하다. 같은 RecursiveLink 와 inner-outer loop 학습을 그대로 얹는다. 이 점이 구조 의존적 학습이라는 기존 한계를 정면으로 무력화한다. 시스템 토폴로지가 바뀌어도 백본 가중치는 그대로, RecursiveLink 만 새 구조에 맞춰 다시 짧게 학습하면 된다.

본 논문이 검증하는 도메인도 패턴 다양성에 맞춰 폭이 넓다. 수학 (MATH500, AIME2025/2026), 과학·의학 (GPQA-Diamond, MedQA), 코드 (LiveCodeBench-v6, MBPP Plus), 검색 QA (HotpotQA, Bamboogle) 까지 9개 벤치마크다. 백본도 Qwen3/3.5, Llama-3, Gemma3, Mistral 처럼 모델 패밀리·크기가 서로 다른 조합으로 묶인다. 이종 백본을 한 루프에 연결하는 게 RecursiveMAS 의 기본 가정이라, 이런 다양성은 프레임워크 입장에서 부담이 아니라 자연스러운 시험대다.

## 다음 편으로 넘어가며

여기까지가 동기 수준의 큰 그림이다.

- 단일 LLM 은 용량·근시안·탐색 비효율이라는 세 한계에 부딪힌다.
- MAS 는 구조적 해답을 주지만, prompt 적응은 능력 상한을 못 올리고 에이전트별 학습은 텍스트 매개의 지연·그래디언트 손실을 떠안는다.
- RLM 의 latent 재귀 발상을 시스템 단위로 확장해, 가벼운 RecursiveLink 만 학습해도 시스템 전체를 공진화시킬 수 있다는 가설을 세웠다.
- Preliminary 의 두 식이 이 가설의 골격을 이룬다. 다음 편에서는 이 골격에 실제 모듈을 끼워 넣는 디자인 원칙을 본다.

다음 편: [디자인 원칙 — RecursiveLink 의 안과 밖](02-design-principles.md)

## 출처

- https://arxiv.org/abs/2604.25917
