---
title: 사전학습 스케일에서 MoE 를 압축한다는 문제
date: 2026-05-18
author: TrainToGPB
tags: [MoE, pruning, distillation, pretraining, compression]
source: https://arxiv.org/abs/2605.08738
summary: MoE LLM 을 사전학습 스케일에서 압축한다는 문제 정의와 SlimQwen 논문이 던지는 세 가지 질문 (초기화, 전문가 압축, 학습 레시피) 을 정리한다.
format: details
part: 1
---

# 사전학습 스케일에서 MoE 를 압축한다는 문제

> 원본: [arxiv.org/abs/2605.08738](https://arxiv.org/abs/2605.08738)

## 왜 MoE 압축이 별도 문제인가

Mixture-of-Experts (MoE) 는 최근 대형 언어모델 (LLM) 의 사실상 표준 스케일링 아키텍처가 됐다. Mixtral, DeepSeek, Qwen3-Next 같은 모델이 모두 MoE 다. 토큰마다 활성화되는 파라미터 수는 일정 수준으로 묶어 두면서, 전체 파라미터 수만 키워 표현력을 확보하는 구조다. 학습·서빙 비용 측면에서 dense 모델보다 유리한 점이 분명하지만, 그래도 "비용이 작다" 는 의미는 아니다.

문제는 두 가지다. 첫째, MoE 라고 해도 사전학습 자체는 여전히 비싸다. Qwen3-Next-80A3B 처럼 총 파라미터 80B, 활성 파라미터 3B 규모 모델을 처음부터 학습하는 비용은 어지간한 사내 GPU 클러스터에서 다시 돌리기 어렵다. 둘째, 서빙 측면에서도 KV 캐시·전문가 메모리·통신 비용이 dense 와 다른 양상으로 누적된다. 그래서 "이미 학습된 큰 MoE 를 더 작은 MoE 로 압축한다" 라는 과제가 실무적으로 의미를 갖는다. 이 글에서 정리하는 SlimQwen 논문은 정확히 이 문제를 다룬다.

## 구조적 가지치기 + 지식 증류 패러다임

LLM 압축 영역에서 가장 표준적인 레시피는 다음 두 가지의 조합이다.

- **구조적 가지치기 (structured pruning)**: 레이어, 어텐션 헤드, 채널, 전문가 같은 아키텍처 단위 자체를 통째로 제거한다. 비구조적 sparsity 와 달리 별도의 sparse kernel 없이 그대로 wall-clock 가속이 붙는다.
- **지식 증류 (knowledge distillation, KD)**: 가지치기로 생긴 성능 손실을 회복하기 위해, 교사 모델 (원본 큰 모델) 의 출력 분포를 학생 모델 (가지치기된 작은 모델) 이 따라가도록 추가 학습한다. 단순 LM loss 로 계속 학습하는 것보다 빠르게 성능을 복구한다고 알려져 있다.

dense 모델 쪽에서는 Minitron (Muralidharan et al., 2024) 이 이 조합으로 상당한 결과를 보였다. 문제는 MoE 로 넘어오면 그대로 쓰기 어렵다는 데 있다.

## MoE 가 dense 압축과 다른 점

dense LLM 에서 압축할 수 있는 축은 보통 둘이다. 깊이 (depth) 와 너비 (width). 레이어 수를 줄이거나, hidden dim·FFN intermediate size 같은 차원을 줄인다. MoE 는 여기에 하나가 더 붙는다.

- **전문가 (experts) 차원**: MoE 레이어 안의 전문가 수 자체를 줄이거나, 일부 전문가들을 다른 전문가로 병합 (merge) 할 수 있다. dense 모델에는 없는 압축 자유도다.

전문가 차원이 추가됐다는 것은 단순히 옵션이 하나 더 늘었다는 의미를 넘는다. 전문가는 router 가 토큰별로 선택해 활성화하는 단위라서, 어떤 전문가를 살리고 죽이느냐가 router 분포 자체와 강하게 얽힌다. dense 모델의 채널 가지치기처럼 "중요도 점수가 낮은 순으로 자른다" 라고 깔끔하게 처리되지 않는다. 게다가 사전학습 스케일 (수백 B 토큰의 continual pretraining) 까지 돌리고 났을 때 어떤 전문가 압축 방식이 끝까지 유리한지는 거의 연구가 없었다. 단발성 (one-shot) 비교 (Jaiswal et al., 2025) 정도가 있을 뿐이다.

또 하나 까다로운 점은, dense 압축에서 잘 통하던 "KD 만으로 LM loss 보다 빠르게 복구된다" 라는 통념이 MoE 에 그대로 적용되는지도 검증된 적이 없다는 것이다. 큰 학습 예산을 들이는 사전학습 스케일에서는 KD 단독·KD+LM·multi-token prediction (MTP) 등 어느 조합이 최선인지가 모두 별도의 실험 질문이다.

## SlimQwen 이 던지는 세 가지 질문

논문은 MoE 압축을 다음 세 질문으로 분해한다.

1. **초기화 (Initialization)**: 가지치기된 사전학습 MoE 가, 같은 타깃 아키텍처를 random 초기화로 처음부터 학습하는 것보다 정말 좋은 출발점인가? 동일한 토큰 예산을 줬을 때 어느 쪽이 이기는가.
2. **전문가 압축 (Expert Compression)**: 전문가를 줄이는 여러 전략 (router frequency, soft logits, REAP, expert merging 등) 중 어느 것이 대규모 continual pretraining 후 살아남는가. 단발성 성능 차이가 끝까지 유지되는가, 아니면 수렴이 비슷해지는가.
3. **학습 레시피 (Training Recipe)**: 압축 후 회복 학습에서 어떤 손실 조합 (KD only / KD + LM / MTP KD) 이 가장 효과적인가. 그리고 압축 자체를 점진적으로 (progressive) 진행하는 스케줄이 단발 (one-shot) 압축보다 나은가.

세 질문에 대한 결과는 다음 편들에서 자세히 다루지만, 한 줄로 미리 정리하면 다음과 같다.

- 가지치기 초기화는 random init 을 크게 이긴다 (+11.79 점 평균).
- 단발 전문가 압축 방식들은 400B 토큰 학습 후엔 거의 비슷한 성능에 수렴한다. 다만 "절반은 그대로 보존, 절반만 병합" 하는 partial-preservation 전략이 일관된 소폭 개선을 준다.
- KD 단독보다 KD + LM 이 지식 집약 벤치마크에서 낫고, 여기에 MTP KD 를 더하면 speculative decoding 가속까지 추가로 얻는다. 압축은 한 번에 다 하지 말고 깊이 우선 (depth-first) 으로 점진 진행하는 게 가장 매끄럽다.

## 한 줄 결론: Qwen3-Next-80A3B → 23A2B

세 질문에 대한 답을 조합해 만든 최종 레시피로, 논문은 Qwen3-Next-80A3B 를 23A2B 로 압축한다. 표기 컨벤션은 "총 파라미터 A 활성 파라미터" 로, 80A3B 는 총 80B / 활성 3B 다. 23A2B 는 총 23B / 활성 2B. 총 파라미터 기준 $3.4\times$ 압축, 활성 파라미터 기준 $1.5\times$ 압축이다.

압축 후 23A2B 모델은 MMLU 평균 75 점대를 유지하며, 일부 점진 가지치기 스케줄에서는 77 점대까지 올라간다. 교사 모델 (82.68 평균) 의 86.5% 수준 성능을 $3.4\times$ 작은 모델로 회복하는 셈이다.

회사 인프라 관점에서 보면, 80B 총 파라미터 MoE 를 추론 서빙하려면 전문가 분산을 위해 다중 GPU 노드 (예: H100 8 장 기준 1~2 노드) 가 필요하지만, 23B 총 파라미터로 내려가면 단일 노드 안에서 충분히 떨어진다. KV 캐시와 전문가 메모리가 함께 줄어들기 때문에 동시 처리 토큰 수 (batch × seq) 도 같은 GPU 에서 크게 늘릴 수 있다. "사전학습 스케일 압축" 이 학술적 호기심이 아니라 비용 곡선 자체를 바꾸는 작업인 이유다.

## 관련 연구 빠르게 분류

논문이 정리한 선행 연구를 압축 축 (depth / width / experts) 과 회복 학습 방식으로 묶어 본다.

| 영역 | 대표 연구 | 한 줄 |
|---|---|---|
| width 가지치기 (dense) | ShearedLLaMA, SliceGPT | hidden / FFN 차원을 중요도 기반으로 축소 |
| depth 가지치기 | ShortGPT, Laco, ShortenedLLaMA | 레이어 통째로 제거, 가벼운 metric 으로 결정 |
| MoE → dense 변환 | Cao et al. (2025) | MoE 레이어를 더 작은 dense 레이어로 병합 |
| 전문가 병합 | M-SMoE, REAP | 유사 전문가를 묶어 메모리 절감 |
| 전문가 가지치기 | Lu et al. (2024) | 잉여 전문가를 직접 제거 |
| 압축 후 회복 학습 | Minitron, DarwinLM, SlimMoE | KD 또는 LM loss 로 continual pretraining |

이들 중 dense LLM 의 width/depth 가지치기 + KD 회복 학습을 정착시킨 Minitron 이 가장 직접적인 비교 대상이다. 하지만 Minitron 은 MoE 에 적용되지 않고, DarwinLM 과 SlimMoE 는 MoE 라도 전문가의 intermediate 차원만 줄이는 좁은 설정이다. SlimQwen 의 차별점은 **depth + width + experts 세 축을 동시에**, **사전학습 스케일 (400B 토큰까지)** 의 continual pretraining 으로 끌고 간다는 것이다.

## 이 시리즈에서 다룰 범위

다음 편부터 각 질문을 한 편씩 깊이 파고든다.

- 2편에서는 깊이·너비·전문가 가지치기의 구체적인 알고리즘과 SlimQwen 의 설계 선택을 본다. 마지막 25% 레이어를 단순 절단하는 결정, hidden dim 중요도 metric, 전문가 importance score 정의 등이 포함된다.
- 3편에서는 partial-preservation 전문가 병합 전략의 동기와 수식, 그리고 단발 전문가 압축 방식들이 왜 결국 비슷한 성능으로 수렴하는지에 대한 분석을 정리한다.
- 4편에서는 MTP (multi-token prediction) 증류와 KD + LM 손실 조합의 효과, 그리고 speculative decoding 가속 결과를 본다.
- 5편에서는 점진 가지치기 (one-stage vs joint vs width-first vs depth-first) 결과, 최종 23A2B 모델 평가, 한계와 우리에게의 시사점을 정리한다.

이 글의 핵심은 "MoE 압축은 dense 압축의 단순 확장이 아니다, 전문가라는 추가 차원과 사전학습 스케일이라는 검증 조건이 함께 들어가야 비로소 실용적 가이드가 된다" 라는 문제 의식이다.

다음 편: [깊이·너비·전문가 가지치기 설계](02-depth-width-expert-pruning.md)

## 출처

- https://arxiv.org/abs/2605.08738
