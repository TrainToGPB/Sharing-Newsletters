---
title: On the Scaling of PEFT — 백만 개 개인 모델을 위한 LoRA 스케일링
date: 2026-06-05
author: 김세형
tags: [PEFT, LoRA, personalization, fine-tuning, serving]
source: https://arxiv.org/abs/2606.02437
summary: PEFT를 단순한 저비용 fine-tuning이 아니라 강한 공유 base 위에 얹히는 지속적 local adaptive state로 보고, Scale Up·Scale Down·Scale Out 세 축이 함께 맞물려야 백만 개 개인 모델이 가능하다고 주장한다.
format: abstract
---

# On the Scaling of PEFT — 백만 개 개인 모델을 위한 LoRA 스케일링

> 원본: [arxiv.org/abs/2606.02437](https://arxiv.org/abs/2606.02437)

PEFT를 "큰 모델을 싸게 fine-tuning하는 방법"으로만 보면 이 논문의 메시지를 놓치기 쉽다. 논문은 LoRA 같은 작은 어댑터를 강한 공유 foundation model 위에 붙는 지속적 개인 상태로 재해석한다.

## 핵심 포인트

- **PEFT의 역할 재정의**: 어댑터는 전체 사용자 기억을 담는 저장소가 아니라, 선호·습관·도구 사용 패턴·기술 같은 행동적 결과를 담는 local adaptive state다.
- **Scale Up**: 작은 업데이트가 의미 있으려면 공유 base가 충분히 강해야 한다. 논문은 trillion-scale MoE LoRA RL, training-inference mismatch, Router Replay R3, sparse architecture 지원 문제를 통해 큰 prior를 실제 학습 루프에 넣는 조건을 설명한다.
- **Scale Down**: 개인별 상태가 지속적으로 갱신되려면 어댑터가 작고 안정적이어야 한다. rank sweep, OLoRA-tail 초기화, rank/alpha/lr 전이 법칙이 핵심 근거다.
- **Scale Out**: 많은 어댑터가 공존할 때 비로소 개인화, 사용자 시뮬레이션, collective intelligence가 열린다. 단, 백만 개 어댑터는 백만 개 full checkpoint가 아니라 shared base 위의 이름 붙은 adapter revision이다.
- **MinT의 시스템 관점**: adapter identity, policy revision, provenance, adapter-only mobility, bounded residency가 없으면 PEFT population은 파일 더미가 되고, 지속적 개인 모델이 되기 어렵다.

## 한 페이지 요약

이 논문의 핵심 질문은 "PEFT가 full fine-tuning의 저렴한 대체재를 넘어, 개인 모델의 기본 단위가 될 수 있는가"다. 저자들은 개인 모델을 하나의 full checkpoint로 보지 않는다. 소수의 강한 base model이 공통 능력과 world knowledge를 제공하고, 사용자·역할·워크플로별 작은 어댑터가 반복 경험의 행동적 결과를 들고 있는 구조로 본다. 따라서 "trillion parameters의 백만 개 개인 모델"은 백만 개 trillion-parameter checkpoint를 뜻하지 않는다. trillion-scale prior는 공유되고, 개인별 차이는 작고 이동 가능한 adapter revision으로 남는다.

논문은 이 주장을 세 축으로 나눈다. 첫째, **Scale Up**은 강한 공유 prior가 왜 필요한지를 다룬다. RL은 무작위로 능력을 새로 발명하기보다 현재 policy가 어느 정도 확률로 샘플링할 수 있는 trajectory를 증폭한다. base model이 약하면 개인 어댑터는 얕은 암기나 취약한 행동 패치에 머물기 쉽다. 반대로 강한 base 위의 작은 LoRA 업데이트는 이미 모델 안에 있는 추론, 도구 사용, 장기 행동 패턴을 더 높은 확률로 끌어낼 수 있다. 논문은 Kimi K2 같은 1T급 MoE에서 LoRA 기반 RL을 운영하려면 rollout, training, sparse routing, checkpoint, serving semantics가 모두 같은 policy를 가리켜야 한다고 강조한다. training-inference mismatch는 단순한 수치 오차가 아니라, MoE에서는 다른 expert path를 타게 만들어 on-policy RL의 전제를 깨뜨릴 수 있다.

둘째, **Scale Down**은 개인별 adaptive state가 얼마나 작아질 수 있는지를 묻는다. Qwen3-8B PPO rank sweep에서는 LoRA rank가 단순히 클수록 좋은 capacity knob이 아니라는 점이 드러난다. ranks 16/32는 현재 레시피에서 안정적인 deployment default에 가깝고, ranks 1~4는 평균 성능은 불안정하지만 best-seed 성능은 큰 rank와 비슷한 low-rank research frontier다. 즉 극저 rank는 완전히 용량 부족이라기보다 안정화가 덜 된 영역이다. 그래서 논문은 RL-native initialization인 OLoRA-tail을 제안한다. minor singular subspace를 쓰되 singular value scaling을 빼서, RL의 좁은 KL budget 안에서 작은 어댑터가 초반에 과도하게 policy를 흔들지 않도록 한다.

셋째, **Scale Out**은 많은 어댑터가 생겼을 때의 문제다. 개인화는 단지 prompt에 persona를 넣는 일이 아니다. prompt-based simulator는 길어질수록 서로 비슷해지고, 반복 경험이 안정적으로 축적되지 않는다. 논문은 LoRA-as-memory, DishNameBenchmark capacity law, Context Learning을 통해 어떤 정보를 파라미터에 쓸지 구분한다. raw fact와 문서는 retrieval이나 tool state에 남기고, LoRA에는 반복적으로 행동을 바꾸는 skill, habit, policy를 쓰는 것이 더 적절하다. capacity도 무한하지 않다. DishNameBenchmark에서는 usable capacity가 대략 $10^{-3}$~$10^{-2}$ memory tokens per trainable parameter 근처에서 경계가 생기며, MLP LoRA가 memory efficiency 측면에서 가장 유리하게 나온다.

마지막으로 논문은 MinT를 통해 이 모든 주장을 시스템 문제로 연결한다. adapter가 개인 상태라면 파일 하나로 끝나지 않는다. 어떤 base와 호환되는지, 어떤 rollout과 reward로 학습됐는지, 어떤 revision이 평가·서빙됐는지, GPU에는 몇 개만 resident로 둘지, 새 adapter를 언제 user-visible하게 노출할지까지 관리해야 한다. MinT는 base를 resident object로 두고 adapter revision만 이동시키며, catalog·CPU cache·GPU batch slot을 분리해 addressability와 live residency를 구분한다. 그래서 백만 개 개인 모델은 "모두 동시에 GPU에 올라간 백만 개 모델"이 아니라, 이름 붙고 평가 가능하며 필요할 때 로드되는 adapter population이다.

결론적으로 이 논문은 PEFT를 더 작은 fine-tuning 기법이 아니라, 강한 공유 모델 위에서 개인별 상태를 지속적으로 쓰고, 이동하고, 평가하고, 서빙하기 위한 단위로 본다. Scale Up 없이 작은 어댑터는 힘이 약하고, Scale Down 없이 강한 prior는 계속 개인화하기 비싸며, Scale Out 없이 PEFT는 population-level 가치로 이어지지 않는다. 세 축이 동시에 맞물릴 때 LoRA는 비용 절감 기법을 넘어 개인 모델 인프라의 기본 primitive가 된다.

## 자세히 보기

<!-- VERSIONS_START -->
1. [PEFT를 개인 모델의 지속 상태로 다시 보기](details/01-peft-as-persistent-state/) — PEFT를 단순한 비용 절감형 fine-tuning이 아니라 강한 공유 base 위에 붙는 작은 local adaptive state로 해석하고, Scale Up, Scale Down, Scale Out 세 축이 왜 함께 맞물려야 개인 모델이 성립하는지 정리한다.
2. [trillion-scale LoRA RL이 Scale Up을 가능하게 하는 방식](details/02-scale-up-lora-rl/) — 강한 공유 prior 위에서 LoRA RL을 돌릴 때 작은 어댑터가 왜 높은 레버리지를 갖는지, 그리고 trillion-scale MoE에서 그 레버리지를 유지하려면 어떤 시스템 일관성이 필요한지 정리한다.
3. [Scale Down: 작은 어댑터를 안정적으로 쓰는 운영 구간](details/03-scale-down-adapter-regime/) — Scale Down 축은 LoRA rank를 낮추는 문제가 단순한 압축 문제가 아니라, 작은 adaptive state를 안정적으로 학습하고 반복 운용하기 위한 rank, 초기화, KL 제약, 하이퍼파라미터 전이의 결합 문제임을 보인다.
4. [메모리와 Context Learning: 무엇을 파라미터에 쓸 것인가](details/04-memory-and-context-learning/) — δ-mem의 writable local state, DishNameBenchmark의 LoRA 메모리 용량 법칙, 개인 모델의 메모리 계층, 그리고 Context Learning을 adapter write policy로 보는 관점을 정리한다.
5. [Scale Out과 MinT: 백만 개 어댑터를 시스템으로 다루기](details/05-scale-out-and-mint/) — Scale Out은 많은 개인 어댑터가 공존할 때 생기는 시뮬레이션, 집단 추론, 서빙 문제를 다루며, MinT는 이를 policy identity, revision, provenance, residency로 관리하는 시스템 예시다.
<!-- VERSIONS_END -->

## 출처

- <https://arxiv.org/abs/2606.02437>
