---
title: 통제된 환경 없이는 long-horizon RL 을 분석할 수 없다
date: 2026-05-10
author: TrainToGPB
tags: [RL, 추론, 사후학습, 합성데이터]
source: https://arxiv.org/abs/2605.06638
summary: long-horizon 추론이 무너지는 현상과 기존 RL 학습 데이터가 horizon·표현력 통제 축에서 부족한 이유를 정리하고, ScaleLogic 이 이를 어떻게 메우려 하는지 짧게 예고한다.
format: details
part: 1
---

# 통제된 환경 없이는 long-horizon RL 을 분석할 수 없다

> 원본: [arxiv.org/abs/2605.06638](https://arxiv.org/abs/2605.06638)

수학·코딩 RL 로 훈련한 추론 모델이 한 줄 늘어난 문제 앞에서 갑자기 무너진다. 이 현상의 원인을 분석하려면 추론 깊이와 논리 구조를 독립적으로 통제할 수 있는 환경이 필요하다. 그러나 지금까지의 RL 학습 데이터는 그런 통제를 제공하지 않는다. 이 편은 그 공백을 정리한다.

## 짧은 horizon 에서 잘 풀던 모델이 긴 horizon 에서 무너진다

최근 LLM 추론 모델은 individual subproblem 단위에서는 강하지만, 그 subproblem 을 직렬로 이어 붙이는 순간 정확도가 급격히 떨어진다는 보고가 누적되고 있다. 핵심은 "더 어려운 문제" 가 아니라 "더 긴 문제" 라는 점이다.

- **R-Horizon (Lu et al., 2025)** — 풀 수 있는 수학 문제를 dependency chain 으로 묶었을 때 chain 길이가 늘어나면 정확도가 sharp 하게 무너진다. RL 훈련이 이 long-horizon failure 를 얼마나 완화할 수 있는지를 측정한다.
- **h1 (Motwani et al., 2025)** — 같은 발상을 multi-step 의존성 체인으로 일반화. 짧은 문제는 풀고 긴 문제는 못 푸는 격차가 분명하게 드러난다.
- **GSM-Infinite (Zhou et al., 2025)** — 산수 reasoning depth 를 임의로 늘릴 수 있는 합성 환경에서 sigmoid 모양의 급격한 decay 패턴을 보고한다.
- **SeqBench (Ramezanali et al., 2025)** — 순차적 추론 단계 수에 대해 exponential 한 성능 붕괴를 관찰한다.
- **Rameshkumar et al. (2025)** — 그래프 기반 추론에서 일정 복잡도까지는 잘 풀다가 horizon 이 일정 임계를 넘는 순간 성능이 abrupt 하게 떨어지는 패턴을 정량화한다.

공통된 그림은 단순하다. 모델은 한 hop 짜리 추론은 잘 한다. 그 hop 을 $k$ 번 이어 붙인 문제는 $k$ 가 작을 때만 잘 한다. $k$ 가 커지면 정확도는 매끄럽게 깎이지 않고 한 지점에서 무너진다. 따라서 long-horizon 추론은 단순한 short-horizon 의 누적 함수가 아니다. 학습이 무엇을 가르치고 무엇을 못 가르치는지 따로 봐야 할 별도 현상이다.

## RL 학습 데이터가 갖춰야 할 네 축

이 현상을 RL 사후학습으로 어떻게 해소할 수 있는가를 분석하려면, 학습 환경이 다음 네 축을 동시에 만족해야 한다.

- **Verifiable** — 정답을 자동으로 검증할 수 있어야 한다. RLVR (RL with Verifiable Rewards) 의 전제 조건이다.
- **Scalable** — 대규모로 자동 생성·검증 가능해야 한다. 사람 큐레이션이 필요한 만큼 분석은 좁아진다.
- **Controllable Horizon** — reasoning horizon (proof 깊이, 의존성 체인 길이) 을 독립 변수로 자유롭게 조절할 수 있어야 한다.
- **Controllable Expressiveness** — 추론에 동원되는 논리 구조 (operator·structural feature) 를 독립적으로 켜고 끌 수 있어야 한다. 깊이가 같아도 논리 구조가 달라지면 학습 난이도는 달라진다.

원문 §1 의 Table 1 은 현재 RL 추론 학습에 쓰이는 데이터 소스 각각이 이 네 축 중 어떤 것을 만족하고 어떤 것을 못 만족하는지를 정리한다. 아래 표는 같은 비교를 본 시리즈 형식에 맞게 재구성한 것이다.

| 데이터 소스 | Verifiable | Scalable | Controllable Horizon | Controllable Expressiveness |
|---|---|---|---|---|
| Math / Code (MATH, LiveCodeBench 등) | O | △ (사람 큐레이션) | X | X |
| Self-evolving 파이프라인 (R-Zero, Absolute Zero) | O | O | X | X |
| Knights and Knaves 류 단일 task 합성 | O | O | △ (한정적) | X |
| 그래프 reasoning (G1) | O | O | △ (NP-hard 워스트케이스) | X |
| SAT 류 worst-case 합성 | O | O | △ (난이도 vs 깊이 분리 어려움) | X |
| **ScaleLogic (제안)** | O | O | O | O |

세부 값은 원문 Table 1 을 그대로 따르되, 핵심은 **위 네 축을 동시에 만족하는 데이터 소스가 비어 있다** 는 것이다. 수학·코딩은 검증 가능하지만 horizon 통제가 거의 안 되고, 자동 생성된 합성 task 는 horizon 을 어느 정도 늘릴 수 있어도 논리 구조 자체를 다이얼로 돌리듯 바꿀 수 없다. 결국 "RL 이 long-horizon 추론을 어떻게 학습하는가" 라는 질문을 던질 만한 통제된 testbed 가 없다.

## 깊이만 늘리는 것으로는 부족하다

여기서 한 발 더 나간 관찰이 ScaleLogic 의 전제다. horizon 통제만으로는 부족하고, **논리 표현력 (logical expressiveness) 자체를 별도 축으로 통제** 해야 한다.

이유는 두 가지다.

1. **같은 깊이라도 논리 구조에 따라 학습 난이도가 다르다**. implication 만 있는 환경에서 깊이 $D$ 인 증명을 푸는 것과, conjunction·negation·disjunction·universal quantification 까지 섞인 환경에서 깊이 $D$ 인 증명을 푸는 것은 완전히 다른 학습 문제다. operator 가 추가되면 같은 노드를 검증하는 비용이 늘고, combinatorial 한 가지치기 부담이 더해진다.
2. **downstream transfer 가 "무엇을 학습했는가" 에 의존한다**. 단순한 논리만 학습한 모델은 합성 task 에서 깊이를 키워도 downstream 수학·일반 추론 벤치마크에서는 빠르게 plateau 한다. 표현력 있는 환경에서 학습한 모델은 같은 step 수로도 더 큰 transfer 를 보인다. 즉 RL 사후학습의 효율은 *how much* 못지않게 *what* 에 의해 결정된다.

이 두 관찰은 다음 단순한 결론을 강제한다. RL 사후학습의 scaling 을 제대로 분석하려면, 깊이 $D$ 와 논리 표현력 $L$ 을 **서로 독립으로** 돌릴 수 있는 환경이 필요하다. 기존 SAT·그래프 reasoning 류 합성 데이터는 어느 한 축을 키울 때 다른 축이 따라 움직이거나, 워스트케이스 NP-hard 라 정밀한 분석이 어렵다.

## ScaleLogic 이 이 공백을 어떻게 메우는가 (예고)

ScaleLogic 은 이 공백을 정확히 두 변수에 대한 통제 환경으로 메운다.

- **proof depth $D$** — 한 증명 트리의 깊이. 모델이 이어 붙여야 할 추론 hop 수에 대응한다. horizon 의 직접 통제 변수.
- **logical expressiveness $L$** — 사용 가능한 logical operator 의 위계. 가장 단순한 implication-only 부터 시작해 conjunction → negation → disjunction → universal quantification 순으로 한 단계씩 strict superset 으로 확장한다. 새로 추가된 operator 가 학습에 끼치는 영향을 cleanly attribute 할 수 있도록 설계된 위계다.

각 instance 는 사실 (axiom) 묶음과 결론 후보 (candidate conclusion) 들로 이루어진 multiple-choice 문제다. 후보 중 정확히 하나만 axiom 들로부터 logically derivable 하고, 나머지는 derivation 이 끊겨 있다. 이 구조 덕분에 정답 검증은 exact match 한 번으로 끝나면서도, $D$ 를 늘리면 모델이 더 긴 proof chain 을 따라가야 하고, $L$ 을 늘리면 같은 chain 위에서 더 표현력 있는 추론을 동원해야 한다.

이 환경 위에서 원문은 다음을 측정한다.

- **proof depth $D$ 에 대한 RL 학습 step 수의 power law**: 목표 정확도 $\tau$ 에 도달하는 데 필요한 step 수를 $C_\tau$ 라 하면 $C_\tau \propto D^\gamma$ 가 관찰된다.
- **expressiveness 에 따른 exponent $\gamma$ 의 monotonic 증가**: implication-only 의 약 1 수준에서 출발해 + quantification 까지 가면 $\gamma$ 가 단조 증가한다. 즉 깊이 한 단위가 비싸지는 속도 자체가 표현력에 달려 있다.
- **downstream transfer 의 expressiveness 의존성**: 같은 compute 예산에서, 표현력이 높은 환경에서 학습한 모델일수록 수학·일반 추론 벤치마크 평균에서 더 큰 절대 향상폭을 얻는다.

이 세 결과의 사전 조건은 결국 환경의 통제성이다. $D$ 와 $L$ 을 독립으로 돌릴 수 없는 환경에서는 power law 의 exponent 변화도, transfer 의 표현력 의존성도 분리해서 측정할 방법이 없다.

## 이 편 정리

- LLM 의 long-horizon 추론은 short-horizon 의 단순 누적이 아니다. 일정 horizon 을 넘으면 정확도가 sharp 하게 무너진다는 보고가 reasoning 모델 전반에서 일관되게 나온다.
- RL 사후학습이 이 한계를 어떻게 메우는지 분석하려면 검증성·확장성·horizon 통제·표현력 통제 네 축을 동시에 만족하는 환경이 필요하다.
- 기존 데이터 (수학·코딩, self-evolving, KnK, SAT, 그래프 reasoning) 는 어느 한 축이 비어 있다. 특히 horizon 과 표현력을 독립으로 돌릴 수 있는 환경이 없다.
- ScaleLogic 은 proof depth $D$ 와 logical expressiveness $L$ 두 축을 분리해 통제한다. 다음 편에서는 이 환경이 어떻게 구성되고 왜 backward construction 이 깊이 통제에 적합한지 들여다본다.

다음 편 → [ScaleLogic — 증명 트리를 거꾸로 짜서 깊이와 표현력을 분리 제어](02-scalelogic-construction.md)

## 출처

- https://arxiv.org/abs/2605.06638
