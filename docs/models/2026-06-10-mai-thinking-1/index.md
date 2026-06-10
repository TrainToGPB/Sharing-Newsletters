---
title: "MAI-Thinking-1: Microsoft의 reasoning model을 만든 hill-climbing machine"
date: 2026-06-10
author: 김세형
tags: [mai-thinking-1, microsoft-ai, reasoning-model, reinforcement-learning, moe]
source: https://microsoft.ai/pdf/mai-thinking-1.pdf
summary: MAI-Thinking-1은 35B active / 약 1T total MoE reasoning model이지만, 보고서의 핵심은 모델 자체보다 pre-training, RL, 평가, 인프라를 빠르게 반복하는 hill-climbing machine이다.
format: abstract
---

# MAI-Thinking-1: Microsoft의 reasoning model을 만든 hill-climbing machine

> 원본: [Microsoft AI technical report](https://microsoft.ai/pdf/mai-thinking-1.pdf)

Microsoft AI의 MAI-Thinking-1 기술 보고서는 모델 카드라기보다, frontier-adjacent reasoning model을 직접 만들기 위해 어떤 반복 시스템을 구축했는지 공개한 개발 노트에 가깝다.

## 핵심 포인트

- MAI-Thinking-1은 $35$B active / 약 $1$T total parameter sparse MoE 모델이며, pre-training부터 RL까지 third-party model distillation 없이 학습했다.
- Microsoft는 모델 개발을 단일 학습 run이 아니라 데이터, architecture ablation, evaluation ladder, RL environment, training infrastructure를 묶은 "hill-climbing machine"으로 정의한다.
- pre-training은 $30$T tokens main phase와 $3.55$T tokens mid-training으로 구성되고, clean human-generated data와 데이터 혼합 최적화가 핵심 축이다.
- RL climb은 GRPO 계열 objective, adaptive entropy control, top-p mask replay, length curriculum, self-distillation로 긴 성능 상승 구간을 유지한다.
- 최종 모델은 STEM, agentic coding/tool use, helpfulness/safety specialist를 consolidation SFT와 lightweight RL로 합친 결과물이다.
- 공개 수치상 AIME 2025 $97.0\%$, AIME 2026 $94.5\%$, LiveCodeBench v6 $87.7\%$, SWE-Bench Pro $52.8\%$를 보고한다.

## 한 페이지 요약

MAI-Thinking-1 보고서의 출발점은 "좋은 모델 하나를 만드는 법"이 아니라 "다음 모델을 더 빨리 좋게 만드는 시스템을 어떻게 만들 것인가"다. Microsoft AI는 이 시스템을 hill-climbing machine이라고 부른다. 여기서 machine은 pre-training corpus, architecture scaling ladder, evaluation suite, RL environment, reward, safety benchmark, distributed training stack, inference serving stack까지 포함한다. 모델 품질을 한 번에 끌어올리는 비법보다, 작은 개선을 검증하고 누적할 수 있는 실험 루프가 중심이다.

![MAI-Thinking-1의 RL climb은 AIME, LiveCodeBench, SWE-bench Verified에서 긴 구간에 걸친 성능 상승을 보여준다.](assets/fig-1.png)
*보고서는 MAI-Thinking-1의 핵심 성과를 단일 checkpoint가 아니라, 성능을 계속 끌어올리는 RL climb으로 설명한다.*

모델 자체는 MAI-Base-1에서 출발한다. MAI-Base-1은 $35$B active / 약 $1$T total parameter 규모의 sparse MoE이며, $8$K GB200 GPU에서 pre-training되었다. architecture는 decoder-only Transformer이고, local/global attention을 주기적으로 섞으며 dense FFN과 high-sparsity MoE feed-forward block을 교차 배치한다. MoE는 $512$ experts 중 $8$개를 token마다 활성화하고, LatentMoE 방식으로 all-to-all dispatch 전에 representation을 압축한다. 이 구조 선택은 단순히 benchmark loss만 보는 것이 아니라, Microsoft의 GPU cluster와 wall-clock efficiency까지 함께 고려한 co-design 결과로 제시된다.

데이터 쪽 메시지는 더 분명하다. Microsoft는 pre-training에 third-party model distillation을 쓰지 않았고, language-model-generated synthetic data도 쓰지 않았다고 밝힌다. 대신 publicly available data와 licensed human-generated data를 사내 pipeline으로 처리해 web, public GitHub code, books, academic papers, news, multilingual text, domain-specific materials를 구성했다. 보고서는 데이터 품질을 단순한 수집량보다 중요한 변수로 본다. deduplication, filtering, categorization, data-mixture search, rank non-invariance 분석이 길게 설명되는 이유도 여기에 있다.

RL 단계에서는 세 종류의 specialist climb이 등장한다. STEM climb은 수학, 과학, competitive programming처럼 verifiable reward를 만들 수 있는 문제에 집중한다. agentic climb은 software engineering과 tool-use처럼 multi-step environment interaction이 필요한 과제를 다룬다. helpfulness/safety climb은 instruction following, steerability, safety, honesty, style을 reward model과 judge로 조정한다. 이후 세 teacher의 rollout을 consolidation SFT로 합치고, 마지막 lightweight RL로 safety, over-refusal, style을 다듬는다.

기술적으로 흥미로운 부분은 RL이 단순한 "post-training 단계"가 아니라 자체 인프라 문제로 다뤄진다는 점이다. 보고서는 adaptive entropy control, outer ratio clip, problem pass-rate filtering, top-p mask replay, maximum rollout length curriculum, self-distillation을 자세히 설명한다. 특히 self-distillation은 collapse recovery, base policy 교체, format 전환, trace filtering을 위한 실용적 장치로 쓰인다. 긴 RL climb에서는 모델 알고리즘과 시스템 안정성이 분리되지 않는다.

평가 결과는 강하지만 "모든 영역 최고"라고 읽기보다는 균형 잡힌 frontier-adjacent 모델로 보는 편이 맞다. 보고서는 MAI-Thinking-1이 STEM과 coding에서 강한 수치를 보이고, Sonnet 4.6과 여러 benchmark에서 경쟁적이며, human side-by-side에서는 Sonnet 4.6보다 약간 선호되지만 Opus 4.6보다는 낮게 평가된다고 정리한다. safety에서는 over-refusal과 high-sensitivity safety pass rate를 함께 보고, jailbreak red teaming 결과를 training data와 judge rubric 개선에 되돌리는 loop를 강조한다.

결국 MAI-Thinking-1의 의미는 모델 이름보다 개발 체계에 있다. clean data를 모으고, scaling ladder로 architecture와 data decision을 검증하고, RL environment를 대량으로 만들고, YOLO/Rocket/SGLang 같은 내부 stack으로 대규모 run을 안정화하며, benchmark와 red teaming에서 나온 신호를 다시 training mix로 되돌리는 구조다. 보고서가 공유하는 가장 큰 교훈은 "reasoning model은 pre-training checkpoint 위에 RL을 얹어서 끝나는 것이 아니라, 평가 가능한 개선 루프 전체를 제품처럼 운영해야 한다"는 점이다.

## 자세히 보기

<!-- VERSIONS_START -->
1. [왜 Microsoft는 모델 하나가 아니라 hill-climbing machine을 말하나](details/01-hill-climbing-machine/) — MAI-Thinking-1을 단일 모델 릴리스가 아니라 데이터, 평가, 학습 인프라, RL 환경을 묶은 반복 최적화 시스템으로 읽는다.
2. [pre-training은 어떻게 실험 가능한 과학이 되었나](details/02-pretraining-data-and-ladders/) — MAI-Base-1의 pre-training은 clean human-generated data, scaling ladder, NLL evaluation, data-mixture search를 묶어 모델 선택을 반복 가능한 실험으로 만든다.
3. [RL climb을 오래 지속시키는 recipe](details/03-rl-recipe-for-long-climbs/) — MAI-Thinking-1의 RL은 GRPO 계열 objective, entropy 제어, top-p mask replay, length curriculum, self-distillation으로 수천 step의 성능 상승을 유지한다.
4. [세 specialist climb은 어떻게 하나의 모델로 합쳐졌나](details/04-three-specialist-climbs/) — STEM, agentic coding/tool use, helpfulness/safety climb은 서로 다른 reward와 환경을 쓰지만, self-distillation과 consolidation SFT/RL로 하나의 MAI-Thinking-1에 통합된다.
5. [평가, 안전성, 인프라가 말해주는 실제 위치](details/05-evaluations-safety-and-infrastructure/) — MAI-Thinking-1은 일부 STEM·coding benchmark에서 강하지만, 공개 평가는 '최고 성능 모델'보다 균형 잡힌 frontier-adjacent 모델과 이를 지탱한 인프라 전략을 보여준다.
<!-- VERSIONS_END -->

## 출처

- https://microsoft.ai/pdf/mai-thinking-1.pdf
