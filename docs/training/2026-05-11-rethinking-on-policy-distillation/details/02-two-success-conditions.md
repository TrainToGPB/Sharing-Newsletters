---
title: 성공의 두 조건 — 호환성과 새로움
date: 2026-05-11
author: Claude
tags: [distillation, post-training, on-policy, weak-to-strong]
source: https://www.arxiv.org/html/2604.13016
summary: OPD 가 성공하려면 학생과 교사가 호환되는 thinking pattern 을 공유하면서, 교사가 진짜 새 능력을 제공해야 한다. 1.5B vs 7B 가 학생 관점에서 구별되지 않는다는 weak-to-strong 결과가 그 직관을 뒷받침한다.
format: details
part: 2
---

# 성공의 두 조건 — 호환성과 새로움

> 원본: [arxiv.org/abs/2604.13016](https://www.arxiv.org/html/2604.13016)

이전 편에서 on-policy distillation (OPD) 의 기본 동학을 정리했다. 이 편은 그 위에 한 층을 더한다. 페이퍼는 OPD 가 성공적으로 작동하기 위한 두 가지 조건을 명시적으로 분리한다. 둘은 별개의 조건이지만 한쪽이 빠지면 다른 쪽이 무의미해진다.

## 조건 1 — 호환되는 thinking pattern

첫 번째 조건은 학생과 교사가 호환되는 thinking pattern 을 공유해야 한다는 것이다. 페이퍼의 표현 그대로 "the student and teacher should share compatible thinking patterns".

여기서 thinking pattern 은 두 모델이 같은 prompt 를 받았을 때 만들어내는 추론 궤적의 구조적 유사성으로 읽는 것이 자연스럽다. 같은 문제에 비슷한 단계로 들어가고, 비슷한 지점에서 분기하고, 비슷한 형태로 검증·재귀하는가. 이 구조가 어긋나면 교사가 만들어낸 토큰 분포가 학생의 현재 상태 위에서 의미 있는 신호로 번역되지 않는다.

왜 이 조건이 필요한가는 OPD 의 수학적 형태에서 바로 따라온다. 학생 정책 $\pi_s$ 가 자신이 만든 rollout 위에서 토큰 단위로 교사 $\pi_t$ 의 분포를 따라 가도록 학습한다고 하자. 손실은 거칠게 보면

$$
\mathcal{L}(\theta) = \mathbb{E}_{x \sim \pi_s}\left[\, D_{\mathrm{KL}}\!\left(\pi_s(\cdot \mid x) \,\|\, \pi_t(\cdot \mid x)\right) \,\right]
$$

같은 형태다. 이 식이 의미 있는 학습 신호를 주려면, 학생이 자주 방문하는 상태 $x$ 위에서 교사 분포 $\pi_t(\cdot \mid x)$ 가 학생이 쓸 수 있는 형태로 정의돼 있어야 한다.

만약 교사가 전혀 다른 패밀리에서 와서 같은 문제에 다른 분기 방식을 쓴다면, 학생의 상태 $x$ 는 교사 입장에서 보면 OOD (out-of-distribution) 에 가까워진다. 교사 분포는 이때 잘 정의돼 있지 않거나, 잘 정의돼 있어도 학생이 일관되게 따라갈 수 없는 방향을 가리킨다. 결과는 두 가지 — 학생이 교사 흉내를 내려다 자기 추론 사슬을 망가뜨리거나, KL 신호가 노이즈 수준으로 떨어진다.

같은 패밀리 안에서는 이 문제가 거의 자동으로 해결된다. 같은 사전학습 코퍼스와 비슷한 사후학습 데이터를 거친 모델들은 비슷한 prompting convention, 비슷한 chain-of-thought 분기 구조, 비슷한 self-check 습관을 공유한다. 학생이 만들어낸 rollout 의 거의 모든 prefix 가 교사 입장에서도 자연스러운 prefix 다.

호환성은 그래서 "정답률이 가까워야 한다" 가 아니라 "분포의 형태가 호환돼야 한다" 는 조건으로 읽는 것이 정확하다. 작고 약한 모델이라도 같은 패밀리면 호환은 성립할 수 있다. 반대로 더 똑똑하지만 다른 패밀리에서 온 교사는 호환이 무너질 수 있다.

## 조건 2 — 진짜 새 능력

두 번째 조건은 미묘하다. 페이퍼는 이렇게 적는다 — "even with consistent thinking patterns and higher scores, the teacher must offer genuinely new capabilities beyond what the student has seen during training".

핵심은 두 가지를 분리한 점이다.

- 교사가 더 잘함 (higher scores)
- 교사가 학생이 본 적 없는 진짜 새 능력을 제공함 (genuinely new capabilities)

OPD 의 직관적 이야기에서는 이 둘이 한 묶음으로 다뤄지기 쉽다. 더 똑똑한 교사면 학생이 못하는 걸 가르쳐 줄 거라는 가정. 페이퍼는 이 가정을 분해한다. 점수 차이는 평균적으로 더 자주 정답에 도달한다는 사실만 알려준다. 그 정답으로 가는 토큰 분포가 학생의 분포와 의미 있게 다른지는 별개 문제다.

"의미 있게 다르다" 가 무엇인지 더 풀면. 학생이 자기 rollout 위에서 만들어내는 토큰 분포를 $\pi_s$ 라 하고, 교사 분포를 $\pi_t$ 라 하자. 둘 다 같은 상태 $x$ 에서 정답률은 비슷하게 높다고 가정해도, 다음 두 경우는 학습 신호 측면에서 전혀 다르다.

- 같은 상태 $x$ 에서 $\pi_s(\cdot \mid x) \approx \pi_t(\cdot \mid x)$. 학생이 이미 그 토큰 분포를 알고 있다. KL 신호는 거의 0 이다. 더 학습할 게 없다.
- 같은 상태 $x$ 에서 $\pi_t$ 가 학생이 거의 두지 않는 토큰에 의미 있는 질량을 둔다. KL 신호가 살아 있고, 학생이 따라갈 수 있는 새 분포 방향이 있다.

전자는 점수가 더 높아도 distillation 으로 옮겨갈 게 없는 경우다. 후자가 페이퍼가 말하는 "genuinely new capabilities" 다. 정답률 격차가 아니라 토큰 분포 격차로 측정해야 하는 양이다.

이 시각으로 보면 OPD 가 잘 안 풀리는 흔한 패턴이 깔끔하게 정리된다. 같은 패밀리, 비슷한 크기 — 호환은 좋지만 새로움이 거의 없다. 다른 패밀리, 훨씬 큰 모델 — 새로움은 많지만 호환이 깨진다. 둘 다 만족해야 OPD 가 의미 있는 향상을 만든다.

## Weak-to-strong reverse distillation 의 의외성

페이퍼는 위 두 조건이 별개임을 보여주기 위해 reverse 방향 실험을 한다. 보통 distillation 은 큰 교사 -> 작은 학생인데, 여기서는 학생이 더 큰 쪽이 되도록 뒤집어 본다. 같은 Qwen 패밀리에서 학생을 고정하고 교사 후보로 1.5B 와 7B 두 가지를 둔다.

직관적으로는 7B 교사가 1.5B 교사보다 학생에게 더 풍부한 신호를 줄 거라고 기대한다. 실제 결과는 의외다. 페이퍼는 "same-family 1.5B and 7B teachers are distributionally indistinguishable from the student's perspective" 라고 적는다. 학생이 자기 rollout 위에서 마주치는 상태 $x$ 들의 분포 안에서는, 두 교사가 만들어내는 $\pi_t(\cdot \mid x)$ 가 사실상 같은 분포처럼 보인다는 것이다.

이게 왜 자연스러운 결론인지 직관을 따라가 보자.

- 학생 rollout 은 학생이 닿을 수 있는 상태로 한정된다. 학생 입장에서 도달 가능한 상태 $x$ 위에서만 KL 신호가 계산된다.
- 같은 패밀리 두 교사는 같은 데이터로 학습됐고 같은 prompting 컨벤션을 따른다. 학생이 잘 닿는 "쉬운 영역" 의 상태들에서는 두 교사가 비슷한 토큰 분포를 낸다.
- 7B 교사가 1.5B 교사보다 우위를 보이는 영역은 보통 더 깊은 추론, 더 긴 chain, 더 어려운 분기 — 즉 학생 rollout 이 그렇게까지 자주 가지 못하는 영역이다.

결과적으로 학생의 rollout distribution 위에서 평균을 내면 두 교사의 차이가 사라진다. 같은 패밀리 안에서 사이즈만 다른 두 교사는 학생 입장에서 "같은 사람" 처럼 보인다.

이 결과의 시사는 단순하다. "더 큰 교사 = 더 좋은 distillation" 이라는 기본 가정이 일반적으로는 성립하지 않는다. 무엇이 중요한가는 다음 두 가지다.

- 학생과 교사가 같은 패밀리·호환 가능한 thinking pattern 을 공유하는가 (조건 1).
- 그 위에서 교사가 학생이 실제로 도달하는 상태 분포에 새 토큰 분포를 제공할 수 있는가 (조건 2).

크기가 두 배라는 사실은 둘 중 어느 쪽도 자동으로 보장하지 않는다.

## 두 조건의 비대칭

조건 1 과 조건 2 는 대칭적이지 않다. 호환성은 학생이 만들어낸 prefix 위에서 교사가 잘 정의돼 있느냐의 문제이고, 새로움은 그 잘 정의된 분포가 학생의 분포와 의미 있게 다르냐의 문제다. 호환이 없으면 새로움을 잴 기준이 사라진다. 호환이 있어도 새로움이 없으면 학습이 그냥 멈춘다.

이 비대칭은 실무 결정 순서에도 그대로 반영된다. 교사를 고를 때 먼저 패밀리 일치를 확인하고, 그 다음에야 사이즈·정답률 격차를 본다. 패밀리부터 어긋난 교사는 사이즈가 아무리 커도 후보에서 빠진다. 다음 편에서는 이 두 조건이 토큰 수준에서 어떻게 드러나는지, 성공·실패의 미시 신호가 무엇인지로 들어간다.

이전 편: [On-Policy Distillation 은 왜 까다로운가](01-why-opd-is-tricky.md)
다음 편: [토큰 단위 phenomenology — 성공·실패의 미시 신호](03-token-level-phenomenology.md)

## 출처

- [arxiv.org/abs/2604.13016](https://www.arxiv.org/html/2604.13016)
