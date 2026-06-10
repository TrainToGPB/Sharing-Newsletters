---
title: 왜 Microsoft는 모델 하나가 아니라 hill-climbing machine을 말하나
date: 2026-06-10
author: 김세형
tags: [mai-thinking-1, reasoning-model, microsoft-ai, moe, reinforcement-learning]
source: https://microsoft.ai/pdf/mai-thinking-1.pdf
summary: MAI-Thinking-1을 단일 모델 릴리스가 아니라 데이터, 평가, 학습 인프라, RL 환경을 묶은 반복 최적화 시스템으로 읽는다.
format: details
part: 1
---

# 왜 Microsoft는 모델 하나가 아니라 hill-climbing machine을 말하나

> 원본: [Microsoft AI technical report](https://microsoft.ai/pdf/mai-thinking-1.pdf)

MAI-Thinking-1 기술 보고서의 제목은 모델 카드처럼 보이지만, 실제 주어는 모델 하나가 아니다. Microsoft AI는 첫 문단부터 "progress"를 단일 checkpoint가 아니라 현재 모델을 계속 개선하는 능력으로 정의한다. 그래서 보고서의 핵심 표현도 "MAI-Thinking-1을 출시했다"가 아니라, "hill-climbing machine을 만들었다"에 가깝다.

이 관점에서 MAI-Thinking-1은 결과물이면서 동시에 증거다. $35$B active / 약 $1$T total sparse MoE 모델이 STEM reasoning과 coding benchmark에서 강한 수치를 냈다는 사실도 중요하지만, 보고서가 더 강조하는 것은 그 수치를 만든 반복 시스템이다. 데이터 선택, architecture ablation, pre-training ladder, long-context mid-training, RL climb, evaluation suite, safety test, training infrastructure가 한 루프 안에서 맞물린다.

## Abstract가 잡는 프레임

Abstract는 MAI-Thinking-1을 "strong reasoning model"로 소개하기 전에, 모델 개발을 system-level optimization problem으로 놓는다. 단일 아이디어나 단일 학습 레시피가 아니라, 더 나은 모델로 올라가기 위한 반복 가능한 장치가 필요하다는 것이다. 이 장치가 보고서에서 말하는 hill-climbing machine이다.

그 결과로 나온 첫 모델이 MAI-Thinking-1이다. 핵심 수치는 다음처럼 정리할 수 있다.

| 항목 | 원문 수치 |
|---|---:|
| 모델 규모 | $35$B active / 약 $1$T total sparse MoE |
| pre-training | $30$T tokens |
| mid-training | $3.55$T tokens |
| 최대 context | $256$K tokens |
| AIME 2025 | $97.0$% |
| LiveCodeBench v6 | $87.7$% |
| SWE-Bench Pro | $52.8$% |

이 표만 보면 "작지만 강한 reasoning model"이라는 요약으로 끝낼 수 있다. 그러나 Abstract는 동시에 중요한 제약도 못박는다. MAI-Thinking-1은 from-scratch로 학습되었고, third-party model distillation 없이 clean, enterprise-grade data를 사용했다고 설명한다. 즉, 보고서가 내세우는 성과는 기존 강한 모델의 행동을 베껴 얻은 shortcut이 아니라, 자체 데이터와 자체 학습 루프에서 올라온 결과라는 주장 위에 세워져 있다.

## 세 가지 설계 원칙

Introduction은 이 반복 시스템을 세 가지 원칙으로 압축한다. 원문 표현을 그대로 가져오면 learned not inherited, simplicity, scientific rigor다. 세 원칙은 slogan처럼 보이지만, 뒤의 장들에서 각각 data, architecture, evaluation, RL infrastructure의 의사결정 기준으로 반복된다.

- **Capabilities should be learned, not inherited**: distillation은 빠른 출발점을 줄 수 있지만, 장기적인 RL climb에서 필요한 steerability와 robustness를 약하게 만들 수 있다고 본다. 그래서 pre-training에서는 LLM synthetic data를 쓰지 않고, AI-generated content를 피하고 제거하려는 방향을 택한다.
- **Simplicity is sustainable**: 복잡한 recipe를 쌓기보다, 확장 가능한 단순한 recipe, 신뢰 가능한 clean data, 투명한 infrastructure를 우선한다. architecture에서도 decoder-only Transformer, 반복 가능한 ladder, 표준 구성 요소의 조합을 강조한다.
- **Scientific rigor avoids shortcuts**: 어떤 선택이 좋아 보인다는 직감보다, ladder, ablation, evaluation으로 검증 가능한 결정을 중시한다. 특히 scale이 커질수록 작은 실험에서 보인 이득이 사라질 수 있으므로, 여러 규모에서 확인하는 절차가 필요하다.

이 세 원칙은 "모델을 잘 만들자"는 일반론이 아니다. Microsoft가 말하는 machine의 작동 조건이다. 능력을 자체적으로 학습시키고, 레시피를 오래 유지할 수 있게 단순화하며, 매 단계의 개선을 실험으로 확인해야 다음 climb로 넘어갈 수 있다.

## 모델 릴리스가 아니라 최적화 루프

보고서가 hill-climbing machine이라는 표현을 쓰는 이유는 성능 향상을 단일 training run의 산물로 보지 않기 때문이다. Pre-training에서는 architecture와 data mixture를 바꾸며 scaling ladder를 만든다. Mid-training에서는 같은 corpus에서 STEM, math, code 비중을 조정하고, context를 $64$K에서 $256$K까지 확장한다. RL 단계에서는 STEM reasoning, agentic coding, helpfulness and safety에 맞춘 specialist climb을 돌린다.

이 흐름은 다음과 같은 루프로 읽힌다.

| 구성 요소 | 역할 |
|---|---|
| 데이터 파이프라인 | public/licensed human-generated data를 수집, 정제, decontamination한다 |
| Pre-training ladder | architecture와 data decision이 scale에서 유지되는지 본다 |
| Evaluation suite | held-out NLL, STEM, coding, safety, human preference를 측정한다 |
| Training infrastructure | 대규모 run을 안정적으로 재현하고 관측 가능하게 만든다 |
| RL environment | task feedback, tool use, preference, safety signal을 통해 행동을 올린다 |

따라서 MAI-Thinking-1은 "최종 답"이라기보다 이 루프가 작동했다는 첫 사례에 가깝다. 원문도 결론부에서 이 모델을 hill-climbing machine으로 만든 첫 모델이라고 표현한다. 모델 이름보다 machine이라는 은유가 더 큰 이유다.

## Figure 1: climb가 보여주는 것

![MAI-Thinking-1 reinforcement learning climb](../assets/fig-1.png)

*Figure 1은 RL 동안 AIME 2025, LiveCodeBench v6 hard subset, SWE-bench Verified의 pass@1이 step이 늘면서 상승하는 모습을 보여준다. 왼쪽과 가운데는 STEM-focused climb, 오른쪽은 code-heavy agentic climb이다.*

Figure 1은 보고서 전체의 메시지를 가장 직접적으로 보여준다. x축은 step이고, y축은 pass@1 성능이다. AIME 2025와 LiveCodeBench v6 hard subset에서는 인접 checkpoint $3$개의 평균을 표시하고, SWE-bench Verified에서는 agentic climb 중 성능 변화를 보여준다.

여기서 중요한 것은 최종 점만이 아니다. 곡선이 수천 step에 걸쳐 계속 올라간다는 점이 핵심이다. 특히 AIME 2025는 낮은 구간에서 시작해 후반부로 갈수록 급격히 상승하고, LiveCodeBench v6 hard subset도 완만한 상승 후 뒤쪽에서 더 큰 개선을 보인다. SWE-bench Verified는 더 작은 범위의 graph지만, code-heavy agentic climb에서도 step을 따라 성능이 꾸준히 올라간다.

보고서는 이 패턴을 "long, log-linear performance improvement"라는 말로 설명한다. 한두 번의 post-training trick으로 끝나는 것이 아니라, RL recipe와 infrastructure가 긴 run을 버틸 때 생기는 개선이다. 그래서 Figure 1은 benchmark figure이면서 동시에 system figure다. 모델이 잘했다는 증거이기 전에, climb를 유지하는 machine이 있다는 증거로 배치되어 있다.

## Pre-training은 바닥을 만든다

Introduction은 pre-training과 mid-training의 역할을 분명히 나눈다. Pre-training과 mid-training은 base model에 넓은 predictive competence와 knowledge를 준다. 하지만 모델이 긴 문제를 어떻게 풀고, inference-time computation을 어떻게 배분하며, tool과 environment를 어떻게 다룰지는 아직 정하지 않는다.

MAI-Base-1은 $30$T tokens로 pre-training되고, 이어서 총 $3.55$T tokens의 mid-training을 거친다. Mid-training data는 pre-training corpus에서 가져오되, STEM, math, code 쪽으로 더 강하게 bias를 준다. 원문 수치로는 STEM/math가 $35$%, code가 $55$%, 나머지 background sources가 $10$%다.

Context 확장도 이 단계에 들어간다. Training phase 표에서 pre-training은 context length $16{,}384$로 진행되고, mid-training phase 1은 $65{,}536$, phase 2는 $262{,}144$로 간다. 보고서가 독자에게 말하는 $256$K context는 이 두 단계의 long-context mid-training을 거친 결과다.

이 대목은 다음 편의 중심 주제다. 여기서는 한 가지 포인트만 잡으면 된다. Microsoft는 data와 context를 "한 번 정하고 끝나는 입력"으로 보지 않는다. 어떤 mixture가 downstream에 도움이 되는지, 어떤 NLL metric이 실제 성능을 예측하는지, 어느 scale에서 architecture decision이 유지되는지를 ladder로 확인하는 실험 대상으로 둔다.

## Model architecture: 단순하지만 infrastructure와 함께 설계됨

Section $2.1$은 MAI-Base-1 architecture를 설명한다. 큰 틀은 decoder-only Transformer다. 여기에 periodic local/global attention, dense FFN과 high-sparsity MoE feed-forward block의 교대를 결합한다. 보고서의 Figure 2는 이 구조를 왼쪽의 Transformer body와 오른쪽의 MoE layer로 나누어 보여준다.

핵심 구성은 다음 정도로 요약할 수 있다.

| 구성 | 설명 |
|---|---|
| Backbone | decoder-only Transformer |
| Attention | local attention $5$개와 global attention $1$개를 주기적으로 배치 |
| FFN | dense FFN과 MoE layer를 교대로 사용 |
| MoE | LatentMoE 구조, token마다 $512$ experts 중 $8$개 활성화 |
| Context 효율 | local attention으로 attention cost와 KV cache를 줄임 |

Attention 쪽에서는 Gemma 3의 periodic attention design을 따른다. local attention $5$개와 global attention $1$개를 묶는 방식은 long context에서 계산 비용과 KV cache 크기를 줄이려는 선택이다. local attention은 sliding window를 쓰고, global attention은 position encoding 없이 더 효율적인 설정을 택한다.

Feed-forward 쪽에서는 모든 layer를 MoE로 만드는 대신 dense FFN과 MoE를 교대로 둔다. 원문은 high-sparsity layer와 zero-sparsity dense layer를 pairing하는 방식이 medium-sparsity MoE를 전 layer에 두는 방식과 비슷하게 scale하면서 wall-clock time에서 효율적이었다고 설명한다. 이 설명은 "MoE니까 무조건 expert를 많이 흩뿌린다"는 단순한 그림과 다르다.

LatentMoE도 중요한 선택이다. 공유 down-projection을 먼저 적용하고, 압축된 latent representation을 expert로 dispatch한 뒤 다시 원래 차원으로 combine한다. Routing decision은 원래 representation에 기반하며, 각 token은 softmax gating으로 $8/512$ expert를 선택한다. 이 정도가 이 편에서 필요한 architecture 이해의 상한이다. 세부 load balancing, dropless MoE, all-to-all communication은 infrastructure 장에서 더 깊게 다룰 내용이다.

## 왜 "learned not inherited"가 architecture와도 연결되는가

"learned not inherited"는 data policy만의 문장이 아니다. MAI-Base-1을 from-scratch로 만들고, architecture family를 ladder로 키우며, 각 decision을 ablation으로 검증하는 방식 전체와 연결된다. 능력을 외부 모델에서 상속받지 않겠다는 말은 모델 행동뿐 아니라 개발 지식도 내부 실험으로 쌓겠다는 선언에 가깝다.

예를 들어 tokenizer는 in-house tokenizer에서 성능 개선을 관찰했지만, existing in-house tools와 workflow 통합을 단순하게 하기 위해 `o200k_base`를 선택했다고 밝힌다. 이 대목은 "항상 최고 점수의 부품을 고른다"가 아니라, 장기 climb에서 유지 가능한 단순성과 통합 비용을 함께 본다는 신호다. 성능, 효율, 운영 가능성, 실험 반복 속도가 한 decision 안에 들어간다.

MoE design도 마찬가지다. 논문은 top-$8/512$ sparse MoE를 쓰면서도 dense FFN을 남기고, dropless implementation으로 수렴하며, expert imbalance가 training stability에 미치는 영향을 관찰한다. 즉, architecture는 paper diagram 안에서 끝나는 설계가 아니라 training infrastructure와 같이 움직이는 설계다.

## RL은 행동을 올리는 climb다

Pre-training과 mid-training이 base competence를 만든다면, RL climb은 모델이 reasoning하고 respond하는 방식을 학습시키는 단계다. Introduction은 이 단계에서 model이 chain of thought를 task-specific feedback에 맞춰 활용하고, external tools로 environment와 상호작용하며, human preference와 safety signal을 따르는 법을 배운다고 설명한다.

특히 보고서는 RL climb이 reasoning trace에 대한 prior exposure 없이 from scratch로 시작한다고 말한다. 이 문장은 "reasoning model을 만들기 위해 reasoning model의 답안을 증류했다"는 경로와 선을 긋는다. 대신 robust RL recipe, self distillation, infrastructure improvement로 수천 step의 run을 지속하고, 그 과정에서 STEM, agentic coding, helpfulness and safety specialist를 학습한다.

여기서 self distillation이라는 단어가 나오지만, Abstract의 third-party model distillation 배제와는 구분해야 한다. 원문이 강조하는 것은 외부 frontier model의 능력을 물려받는 것이 아니라, 자체 climb 과정에서 얻은 신호를 반복 개선에 활용한다는 쪽이다. 이 distinction이 MAI-Thinking-1 보고서의 자기 정체성을 만든다.

## Benchmark 수치는 machine의 산출물로 읽기

AIME 2025 $97.0$%, LiveCodeBench v6 $87.7$%, SWE-Bench Pro $52.8$%는 headline으로 충분히 강하다. AIME는 competition math, LiveCodeBench는 최신 competitive coding, SWE-Bench Pro는 더 어려운 software engineering benchmark다. 보고서는 여기에 AIME 2026, HMMT, GPQA, SWE-bench Verified, Terminal-Bench, long context, safety, health, tool calling 같은 더 넓은 평가도 붙인다.

하지만 이 첫 편의 scope에서는 수치를 순위표로 길게 읽지 않는 편이 낫다. 중요한 것은 서로 다른 benchmark가 hill-climbing machine의 서로 다른 면을 검증한다는 점이다.

| Benchmark | 이 글에서의 해석 |
|---|---|
| AIME 2025 | STEM reasoning climb가 수학 문제 풀이에 반영되는지 본다 |
| LiveCodeBench v6 | one-shot competitive coding 능력과 긴 추론 출력을 본다 |
| SWE-Bench Pro | agentic coding, tool use, environment interaction을 본다 |

즉, MAI-Thinking-1의 성능은 "하나의 모델이 여러 시험을 잘 봤다"보다 조금 더 구조적인 의미를 가진다. Pre-training ladder가 base를 만들고, mid-training이 reasoning RL의 바닥을 깔며, RL environment가 domain-specific feedback으로 행동을 끌어올린 결과가 benchmark에 나타난다.

## 이 편의 결론

MAI-Thinking-1을 단일 모델 릴리스로만 읽으면 보고서의 절반을 놓친다. Microsoft가 더 크게 말하는 것은 "좋은 checkpoint"가 아니라 "좋은 checkpoint를 계속 만들 수 있는 process"다. 그래서 제목의 hill-climbing machine은 과장이 아니라, 보고서 전체를 조직하는 기술적 프레임이다.

이 machine은 세 가지 축으로 움직인다. 첫째, 능력을 외부 모델에서 상속받기보다 human-generated data와 자체 학습으로 만들려 한다. 둘째, 복잡한 비법보다 장기적으로 반복 가능한 단순한 recipe와 infrastructure를 선호한다. 셋째, 모든 decision을 ladder, ablation, evaluation으로 검증하려 한다.

다음 편에서는 이 중 pre-training 쪽을 더 좁게 본다. Microsoft가 data mixture와 scaling ladder를 어떻게 실험 가능한 대상으로 만들었는지, 그리고 왜 pre-training이 단순한 대량 학습이 아니라 과학적 계단이 되었는지를 다룬다.

다음 편: [pre-training은 어떻게 실험 가능한 과학이 되었나](02-pretraining-data-and-ladders.md)

## 출처

- https://microsoft.ai/pdf/mai-thinking-1.pdf
