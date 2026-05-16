---
title: RecursiveMAS — 멀티 에이전트 협업을 잠재 공간에서 재귀로 스케일링
date: 2026-05-16
author: TrainToGPB
tags: [에이전트, 멀티에이전트, 재귀, latent-reasoning, scaling-law]
source: https://arxiv.org/abs/2604.25917
summary: 다중 에이전트 시스템을 텍스트로 주고받지 않고 잠재 표현 그대로 묶어 하나의 재귀 계산으로 본다. 평균 정확도 +8.3%p, 추론 1.2~2.4배 가속, 토큰 34.6~75.6% 절감.
format: abstract
---

# RecursiveMAS — 멀티 에이전트 협업을 잠재 공간에서 재귀로 스케일링

> 원본: [arxiv.org/abs/2604.25917](https://arxiv.org/abs/2604.25917)

여러 LLM 에이전트가 협업하는 multi-agent system (MAS) 을 텍스트가 아니라 latent 표현으로 묶어, 시스템 전체를 한 번의 재귀 계산으로 보고 함께 학습하자는 제안이다. 라이트한 RecursiveLink 모듈만 학습하면서 9개 벤치마크 평균 +8.3%p 정확도, 1.2~2.4배 추론 속도, 토큰 34.6~75.6% 절감을 달성한다.

## 핵심 포인트

- 텍스트로 메시지를 주고받는 기존 MAS 대신 에이전트 사이를 **latent 임베딩 그대로** 흘려보내, 시스템 전체를 RLM (recursive language model) 의 한 round 로 캐스팅한다.
- 두 가지 RecursiveLink — 같은 에이전트 안의 inner link (last-layer hidden → input embedding) 와 이종 에이전트 사이의 outer link (hidden dim 정렬) — 만 학습한다. 백본 LLM 은 freeze.
- Inner-Outer Loop 학습은 (1) 각 에이전트의 latent thought 가 input embedding 분포에 정렬되도록 inner link 를 cosine regression 으로 워밍업한 뒤, (2) 시스템을 $r$ recursion round 전개해 마지막 라운드의 텍스트 예측에 대해 CE loss 로 outer link 들을 공동 최적화한다.
- 텍스트 SFT 가 entropy 가 낮은 confident token 에서 그래디언트 소실에 빠지는 데 비해, RecursiveLink 경로는 round 수와 무관하게 stable / near-constant gradient 를 유지한다는 이론 결과 (Theorem 4.1) 가 latent 매개의 학습 우위를 뒷받침한다.
- Sequential / Mixture / Distillation / Deliberation 네 가지 협업 패턴 모두에 적용 가능 — 구조 불가지론적 (structure-agnostic) 이다.
- 실측: round 1→3 에서 Recursive-TextMAS 대비 평균 정확도 +8.1%p→+20.2%p, 추론 시간 1.2배→2.4배, 토큰 34.6%→75.6% 절감. AIME2025 에서 LoopLM·TextGrad 대비 +18%p 수준의 점프.

## 한 페이지 요약

언어 모델 한 대가 풀기 버거운 문제는 여러 에이전트가 분업해서 풀자는 multi-agent system (MAS) 흐름이 한 축이고, 같은 모델 안에서 같은 layer 를 여러 번 반복 적용해 reasoning depth 를 키우자는 recursive language model (RLM) 흐름이 또 한 축이다. 이 논문은 두 축을 합쳐 본다. 에이전트 한 명을 RLM 의 한 layer 라고 보면, 멀티 에이전트 시스템은 그 자체가 잠재 공간의 재귀 계산이다.

![scaling law 와 네 가지 협업 패턴](assets/fig-1.png)

*Figure 1. 위쪽은 학습·추론 양쪽 재귀 깊이를 키울 때 정확도가 어떻게 올라가는지의 scaling law, 아래쪽은 네 가지 협업 패턴 (Sequential, Mixture, Distillation, Deliberation) 에서 RecursiveMAS 가 단일 강자 에이전트와 텍스트 기반 baseline 을 모두 상회한다는 결과.*

기존 MAS 가 한 에이전트의 출력을 토큰으로 디코딩한 뒤 다음 에이전트가 다시 인코딩하는 과정을 매 round 반복하기 때문에 시간·토큰 비용이 round 수에 비례해 폭증한다. RecursiveMAS 는 마지막 round 만 텍스트로 디코딩하고, 중간 round 는 전부 latent 임베딩으로 통과시킨다. 이때 임베딩 공간 차이를 메우는 것이 두 가지 RecursiveLink 다. Inner link 는 같은 에이전트의 last-layer hidden 을 input embedding 공간으로 매핑해 latent thought 를 auto-regressive 하게 이어가게 하고, outer link 는 한 에이전트의 latent thought 를 다음 에이전트 (다른 hidden dim) 의 input 공간으로 정렬한다. 둘 다 residual + 2-layer GELU 라는 작은 모듈이다.

학습은 두 단계다. Inner-loop 에서는 각 에이전트별로 inner link 만 학습한다. 모델이 만들어 낸 latent thought $h_{t}$ 가 ground-truth 텍스트를 standard input embedding layer 에 통과시킨 분포에 코사인 유사도로 가까워지도록 회귀시킨다. Outer-loop 에서는 시스템 전체를 $r$ round 펼친 forward pass 위에서, 마지막 round 의 텍스트 prediction 에 대한 cross-entropy 를 모든 outer link 로 backprop 한다. 백본 LLM 파라미터는 전부 freeze 상태이고, 학습되는 것은 13M 수준의 RecursiveLink 뿐이라 GPU 메모리·비용 모두 LoRA·Full-SFT 보다 낮다.

왜 굳이 latent 인가에 대해서는 두 개의 이론적 정당화가 따라온다. 첫째, 런타임 복잡도 — 텍스트 기반 재귀 MAS 가 round 마다 vocab projection $O(d \cdot |V|)$ 를 부담하는 데 반해, RecursiveMAS 는 그것을 latent transformation $O(d^{2})$ 로 대체한다. 실제로 $|V| \gg d$ 이므로 같은 구조라도 latent 쪽이 본질적으로 더 가볍다. 둘째, 학습 안정성 — entropy 가 낮은 confident token 에서 text-based SFT 의 그래디언트는 round 가 깊어질수록 소실되는 반면, RecursiveLink 의 residual 경로는 그래디언트 norm 을 1 근처로 유지한다 (Theorem 4.1).

경험적 결과는 두 가지 결을 동시에 보여준다. 첫째는 같은 협업 구조에서 textual 매개 vs latent 매개의 비교다. Recursive-TextMAS 대비 round 1 에서 평균 +3~6%p 정확도, round 3 까지 키우면 +20.2%p 까지 벌어진다. 같은 round 에서 토큰은 34.6%~75.6% 줄고 wall-clock 은 1.2~2.4배 빨라진다. 둘째는 여러 협업 패턴에 대한 일반화다. Mixture 에서는 가장 강한 domain specialist 보다 +6.2%p, Deliberation (Reflector + Tool-Caller) 에서는 +4.8%p, Distillation 에서는 learner 가 +8.0%p 향상되면서 expert 대비 1.5배 추론 가속을 동시에 얻는다.

한계도 분명하다. 백본을 freeze 하고 link 만 학습하는 가정은 학습 효율을 끌어올리는 대신 에이전트 본체의 능력 자체를 늘리지는 않는다. latent 로 주고받는 "thought" 가 사람 입장에서 해석되지 않으니, 디버깅·정렬·감사 측면에서 텍스트 기반 MAS 가 갖던 가독성을 일부 포기한다. 평가가 수학·과학·코드처럼 정답이 채점 가능한 reasoning 위주라, 자유 형식 생성이나 도메인 지식 작업에서 같은 우위가 유지되는지는 별도 검증이 필요하다.

그럼에도 한 번에 잡히는 그림은 또렷하다. 멀티 에이전트의 "협업" 을 메시지 교환 (텍스트) 이 아니라 시스템 전체의 latent recursion 으로 다시 보면, 학습은 single-system 처럼 깔끔해지고, 추론은 round 가 깊어질수록 텍스트 기반 baseline 보다 더 빨라진다. 시스템 단위로 scaling law 를 끌어올리는 새 축이 latent 재귀에 있다는 신호다.

## 자세히 보기

<!-- VERSIONS_START -->
1. [왜 또 다른 멀티 에이전트 프레임워크인가](details/01-why-another-mas/) — 단일 LLM 의 한계에서 multi-agent system 으로, 다시 RecursiveMAS 가 latent 공간 재귀로 시스템 전체를 공진화시키려는 동기와 배경.
2. [디자인 원칙 — RecursiveLink 의 안과 밖](details/02-design-principles/) — Inner / Outer RecursiveLink 의 정의와 residual+2-layer 디자인이 왜 latent 의미를 보존하면서 분포 shift 만 학습하는 데 적합한지.
3. [아키텍처 — 에이전트를 잠재 루프로 묶기](details/03-architecture-and-loop/) — 각 에이전트를 RLM layer 로 캐스팅하고 latent thoughts 를 inner/outer link 로 이어 시스템 전체를 하나의 재귀 루프로 묶는 아키텍처와 그 런타임 우위.
4. [학습 — Inner-Outer Loop 와 그래디언트 안정성](details/04-learning-to-recur/) — 모델 수준 inner-loop 워밍업과 시스템 수준 outer-loop 공진화. text-based SFT 의 그래디언트 소실을 피하면서 RecursiveLink 만으로 학습 비용도 크게 줄인다.
5. [평가 — 벤치, 효율, 일반화, 시사점](details/05-evaluation-and-takeaways/) — 9개 벤치마크와 네 가지 협업 패턴에서 RecursiveMAS 가 보인 정확도·속도·토큰 효율 우위, 그리고 그 결과가 실제 도입에 던지는 시사점.
<!-- VERSIONS_END -->

## 출처

- https://arxiv.org/abs/2604.25917
