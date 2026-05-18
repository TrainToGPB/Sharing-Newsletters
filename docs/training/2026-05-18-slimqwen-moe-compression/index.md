---
title: SlimQwen — Qwen3-Next-80A3B 를 23A2B 로 줄이는 MoE 가지치기·증류 레시피
date: 2026-05-18
author: TrainToGPB
tags: [MoE, pruning, distillation, MTP, compression, pretraining]
source: https://arxiv.org/abs/2605.08738
summary: 사전학습 스케일에서 MoE 모델을 압축할 때 (1) 가지치기 = 강한 초기화, (2) 부분 보존 전문가 머징, (3) MTP KD 가 포함된 4-term 손실, (4) 점진적 가지치기 스케줄이 일관되게 더 좋다. Qwen3-Next-80A3B 를 23A2B 로 약 3.4x 압축한 SlimQwen 으로 검증된 레시피.
format: abstract
---

# SlimQwen — Qwen3-Next-80A3B 를 23A2B 로 줄이는 MoE 가지치기·증류 레시피

> 원본: [arxiv.org/abs/2605.08738](https://arxiv.org/abs/2605.08738)

MoE 모델을 사전학습 스케일에서 압축하려면 가지치기 차원이 dense 보다 하나 더 늘어난다 — 깊이, 너비에 더해 전문가 (experts). SlimQwen 은 Qwen3-Next-80A3B 를 23A2B 로 약 $3.4\times$ 압축하면서 교사 평균의 90% 이상을 회복하는 레시피를 정리한다. 핵심은 세 결론으로 압축된다. 가지치기가 곧 강한 초기화이고, 전문가 압축은 단순한 부분 보존 머징이면 충분하며, 손실은 KD 단독보다 LM 을 섞은 4-term 종합이 낫고, 자르기는 한 번에 다 자르기보다 단계적으로 자르는 게 항상 좋다.

## 핵심 포인트

- **가지치기 = 강한 초기화**. 같은 120B 토큰 KD 학습에서 random init 평균 61.66 대 pruned init 73.45. 교사 (82.68) 의 약 86.5% 를 그대로 가져온다.
- **전문가 압축 방법론은 거의 동등**. frequency, soft-logits, REAP, pruning vs merging — 400B 토큰 continual pretraining 뒤에 보면 한 방법이 모든 벤치를 잡지 않는다. 그러나 **부분 보존 머징** (target experts 의 절반은 그대로 유지, 나머지 절반에 버려진 expert 를 흡수) 만은 MMLU·MMLU-Pro·GSM8K 에서 일관된 개선.
- **MTP KD 가 포함된 4-term 손실**. 백본 LM + 백본 KD + MTP LM + MTP KD 종합이 평균 best. MMLU 74.16 → 75.67. MTP KD 는 부수적으로 speculative decoding acc_4 도 acc_1 대비 2~3 배 끌어올린다.
- **점진적 가지치기 ($40B + 360B$) 가 1-shot 400B 보다 일관되게 좋다**. depth-first / width-first / joint 모두 1-shot 대비 개선되며, depth-first 가 평균 best — 이게 공식 SlimQwen.
- **실무 시사점**: 새 MoE 를 처음부터 학습하지 말고 더 큰 모델을 가지치기 + KD 해라. 전문가 압축 방법론은 단순하게. 손실은 4-term 종합. 토큰을 두 단계로 쪼개라.

## 한 페이지 요약

문제는 단순하다. Qwen3-Next-80A3B 같은 80B 클래스 hybrid MoE 는 학습도 서빙도 비싸다. 더 큰 사전학습 모델을 작은 사이즈로 압축해 성능 대부분을 살리는 게 실무적으로 더 효율적이지만, MoE 에서는 dense LLM 압축 노하우가 그대로 통하지 않는다. dense 와 달리 expert 라는 추가 압축 차원이 있고, 사전학습 스케일에서 어떤 전문가 압축이 살아남는지에 대한 체계적인 비교가 부족했다.

SlimQwen 은 세 질문을 차례로 던지고 답한다.

첫째, **가지치기는 더 좋은 초기화인가?** 같은 120B 토큰을 받아 KD 만으로 학습할 때, random init 은 평균 61.66, pruned init + KD 는 73.45. 격차 약 12 점이 한 번에 좁혀지지 않고 끝까지 유지된다. LM loss 곡선 자체가 다른 출발선에서 시작해 다른 수렴 지점에 도달한다.

![pruned 초기화가 LM loss 곡선 자체를 끌어내린다](assets/fig-2.png)

_120B 토큰 KD 학습 동안의 LM loss. Pruned + KD (빨강) 가 가장 낮은 loss 로 가장 빠르게 수렴하고, Random init + KD (파랑) 는 같은 토큰 예산을 받고도 가장 높이 머문다._

둘째, **전문가 압축은 어떤 방법이 좋은가?** 9 가지 변형 (pruning vs merging × frequency / soft-logits / REAP × router weights / router logits / expert vector × partial preserve y/n) 을 400B 토큰으로 비교했을 때, 어떤 한 방법도 전 벤치마크에서 1 등을 잡지 않는다. 차이는 대부분 noise 수준. 그러나 **부분 보존 머징** — target expert 의 절반은 그대로 유지, 나머지 절반에 importance 가 낮은 expert 들을 nearest-neighbor 기준으로 흡수 — 만큼은 MMLU, MMLU-Pro, GSM8K 에서 일관된 개선을 만든다. "모두 머징하면 균질화, 모두 남기면 보존 부족" 사이의 단순한 절충이 작동한다.

셋째, **압축 후 학습 손실은 어떻게 짤 것인가?** SlimQwen 은 백본 LM, 백본 KD, MTP LM, MTP KD 네 항을 모두 섞고, KD 가중치는 1.0 → 0.75 로 선형 감쇠, MTP KD 가중치는 0.3 → 0.1 로 코사인 감쇠시킨다. 순수 KD 대비 MMLU 가 74.16 → 75.67 로 올라가고, MTP KD 는 speculative decoding 의 multi-token acceptance rate (acc_1 ~ acc_4) 까지 동시에 끌어올려 inference 비용을 함께 잡는다.

마지막으로 **점진적 가지치기**. 80A3B → 23A2B 를 한 번에 자르고 400B 토큰 학습하는 1-shot 보다, $40B + 360B$ 로 단계를 나눈 모든 변형 (joint, width-first, depth-first) 이 평균에서 일관되게 더 좋다. 그중 첫 단계에서 깊이 절반만 자르는 depth-first 가 평균 best — MMLU 75.86 → 77.39, MMLU-Redux 75.41 → 78.01. 이 구성이 공식 SlimQwen 이다.

종합하면 SlimQwen 의 메시지는 "MoE 압축에서 단일 트릭으로 큰 점프를 노리지 말고, 평범한 결정 네 개를 일관되게 쌓아라" 다. 가지치기로 시작점을 끌어올리고, 전문가 압축은 단순하게, 손실은 종합으로, 자르기는 단계적으로.

## 자세히 보기

<!-- VERSIONS_START -->
1. [사전학습 스케일에서 MoE 를 압축한다는 문제](details/01-compressing-moe-at-pretraining-scale/) — MoE LLM 을 사전학습 스케일에서 압축한다는 문제 정의와 SlimQwen 논문이 던지는 세 가지 질문 (초기화, 전문가 압축, 학습 레시피) 을 정리한다.
2. [깊이·너비·전문가 가지치기 설계](details/02-depth-width-expert-pruning/) — Qwen3-Next-80A3B 를 23A2B 로 줄이는 구조적 가지치기 세 차원 — 마지막 레이어 깊이 가지치기, RMSNorm 활성화 기반 너비 가지치기, 그리고 부분 보존 머징을 포함한 전문가 압축 — 의 방법론과 설계 근거 정리.
3. [MTP 증류와 손실 함수 설계](details/03-mtp-distillation-and-losses/) — 백본 LM/KD 손실에 MTP LM/KD 손실을 더한 4-term 종합 목적과 점진적 가지치기 스케줄의 동기를 정리한다.
4. [어떤 압축 레시피가 실제로 살아남나](details/04-which-recipe-actually-works/) — 사전학습 스케일 압축 실험에서 가지치기 초기화, 부분 보존 머징, 4-term 학습 목적이 어떻게 살아남는지를 Q1~Q3 결과로 정리한다.
5. [SlimQwen 23A2B 와 점진적 가지치기, 그리고 실무 시사점](details/05-slimqwen-and-takeaways/) — Qwen3-Next-80A3B 를 23A2B 로 압축하는 마지막 퍼즐, 점진적 가지치기 스케줄 비교와 시리즈 전체의 결론·한계·실무 시사점을 정리한다.
<!-- VERSIONS_END -->

## 출처

- <https://arxiv.org/abs/2605.08738>
