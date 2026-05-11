---
title: 토큰 단위 phenomenology — 성공·실패의 미시 신호
date: 2026-05-11
author: Claude
tags: [distillation, on-policy, token-level, diagnostics]
source: https://www.arxiv.org/html/2604.13016
summary: 성공한 OPD 는 token overlap 이 72%에서 91%로 오르고, shared top-k 가 결합 확률 질량의 97-99%를 차지하며, 두 분포의 entropy gap 이 좁아진다. 실패한 run 은 출발부터 이 신호가 죽어 있다.
format: details
part: 3
---

# 토큰 단위 phenomenology — 성공·실패의 미시 신호

> 원본: [arxiv.org/abs/2604.13016](https://www.arxiv.org/html/2604.13016)

phenomenology 는 원래 물리학에서 미시 메커니즘과 별도로 "겉으로 드러나는 현상의 패턴" 을 추려 부르는 말이다. 본 논문이 이 단어를 빌려 쓰는 이유가 분명하다. 학생 모델이 학습 중에 무엇을 토큰 단위로 어떻게 바꾸는지, 그 바깥쪽 신호만 봐도 성공 run 과 실패 run 이 다르게 생겼다. 안쪽 메커니즘 (왜 그런 신호가 나오는가) 은 뒤 편에서 다루고, 이번 편은 외형부터 정리한다.

## 왜 token-level 신호를 보는가

OPD 의 종결 지표 (final downstream accuracy) 만 보면 두 가지 손해가 있다.

- **너무 늦다**. 학습이 다 끝나고 나서야 망했음을 안다. GPU 시간은 이미 다 썼다.
- **너무 거칠다**. 같은 "실패" 라도 분포가 어긋난 건지, 길이가 폭주한 건지, 보상 신호가 안 들어온 건지 구분이 안 된다.

token-level 진단은 그 사이를 메운다. 학습 step 마다 학생이 실제 방문한 state $s$ 에서 학생 분포 $\pi_s(\cdot \mid s)$ 와 교사 분포 $\pi_t(\cdot \mid s)$ 를 직접 비교한다. 두 분포가 같은 토큰들을 같은 비중으로 누르고 있는지 만 보면 된다. 메트릭은 가볍고, 계산은 forward pass 한 번에 묻어간다.

## 성공 run 의 세 가지 외형

논문이 성공한 OPD run 에서 일관되게 관찰한 패턴은 세 가지다. 모두 student-visited state 위에서 측정한다.

**(1) overlap ratio 가 오른다.** top-$k$ 집합

$$
T_s^k(s) = \text{top-}k \text{ tokens of } \pi_s(\cdot \mid s), \quad T_t^k(s) = \text{top-}k \text{ tokens of } \pi_t(\cdot \mid s)
$$

의 겹침을

$$
r_k(s) = \frac{|T_s^k(s) \cap T_t^k(s)|}{k}
$$

로 정의한다. (이 표기는 직관 전달용이고, 정확한 정의는 원문 참조.) 성공 run 에서 $r_k$ 의 평균이 학습 초기 72% 근처에서 시작해 91% 까지 단조적으로 오른다. 즉 학생이 "어떤 토큰을 후보로 떠올리는지" 가 점점 교사와 일치한다.

**(2) shared top-$k$ 가 거의 모든 확률 질량을 가진다.** 학생·교사 양쪽 top-$k$ 가 정해지면, 그 합집합

$$
U^k(s) = T_s^k(s) \cup T_t^k(s)
$$

위에 두 분포가 두는 질량 비율

$$
m_k(s) = \sum_{v \in U^k(s)} \tfrac{1}{2}\big(\pi_s(v \mid s) + \pi_t(v \mid s)\big)
$$

이 학습이 진행되면서 결합 확률 질량의 97% 에서 99% 사이로 수렴한다. 다시 말해 두 분포의 의견 불일치는 "꼬리 토큰" 에 묻혀 있고, 본 줄기는 같은 작은 집합 위에서 흔들린다. 학생을 교사 쪽으로 옮기는 작업이 사실상 이 작은 집합 안의 확률 재배분 문제로 환원된다는 뜻이다.

**(3) entropy gap 이 좁아진다.** 같은 state 에서 두 분포의 엔트로피 차

$$
\Delta H(s) = H(\pi_s(\cdot \mid s)) - H(\pi_t(\cdot \mid s))
$$

가 학습 초기엔 큰 양수 (학생이 더 평평) 또는 큰 음수 (학생이 더 뾰족) 로 시작하지만, 성공 run 에서 절대값이 줄어든다. 즉 학생이 교사와 같은 "확신 정도" 로 같은 토큰을 누른다.

세 신호는 따로 노는 게 아니라 같이 움직인다. overlap 이 오르면 shared top-$k$ 가 자연스럽게 더 많은 질량을 갖고, entropy 도 비슷해질 여지가 생긴다. 그래서 셋 다 봐야 한다기보다 한두 개만 정기적으로 찍어도 큰 그림이 잡힌다.

## 실패 run 의 대조 패턴

같은 두 모델, 같은 데이터셋, 같은 알고리즘 한 줄만 비틀어 실패한 run 에서는 위 세 신호가 거의 그대로 죽는다.

- **stagnant overlap.** $r_k$ 가 학습 초기 값 근처에서 변하지 않는다. 학생이 새로 만든 토큰 후보 집합이 교사의 것과 더 겹치는 방향으로 움직이지 못한다.
- **persistent entropy mismatch.** $\Delta H(s)$ 가 학습 시작부터 끝까지 한쪽으로 치우친 채 유지된다. 학생이 너무 평평하든 너무 뾰족하든, 그 비대칭이 사라지지 않는다.

논문이 강조하는 포인트는 시점이다. 이 두 신호는 **학습 시작 직후부터** 이미 나쁘다. "처음엔 괜찮다가 중간에 무너졌다" 가 아니라 "출발부터 신호가 안 잡혔다" 에 가깝다. 그래서 후반부 metric 을 기다리지 않아도 된다.

## 왜 phenomenology 인가

세 가지 신호 모두 학생·교사의 출력 분포 위에서만 정의된다. 안에서 무슨 일이 일어나는지 (어떤 attention head 가 무엇을 잡는지, 어떤 representation 이 어떻게 흐트러지는지) 는 묻지 않는다. 그 뜻에서 이건 mechanism 이 아닌 phenomenology 다.

이게 약점이자 강점이다.

- **약점**: "왜" 그렇게 되는지 답을 못 준다. overlap 이 정체된 게 student capacity 부족 때문인지, 학습률 때문인지, on-policy sampling 의 분산 때문인지는 이 지표만으론 모른다.
- **강점**: 누구나 잴 수 있다. 모델 내부에 손대지 않고, 추가 forward pass 도 없이, 학습 루프 안에서 그대로 뽑힌다. 이식성이 가장 높은 진단 신호다.

다음 편에서는 이 외형 신호 뒤에 깔린 메커니즘 — 왜 student-visited state 위에서 진행될 때만 진짜 학습 신호가 잡히는가 — 을 본다. 이번 편의 결론은 그보다 한 단계 얕다: **외형만으로도 성공·실패가 갈린다는 사실** 자체가 일단 OPD 디버깅의 출발점이다.

## 실무 함의: 학습 도중 두세 줄 모니터링

이 phenomenology 가 가장 직접적으로 쓸모 있는 곳은 학습 중간 모니터링이다.

권장 셋업.

- 매 $N$ step (예: 100 ~ 500) 마다 학생이 방문한 state 의 작은 배치 (몇 백 ~ 몇 천 토큰) 를 샘플링.
- 그 위에서 $r_k$, $m_k$, $\Delta H$ 를 평균해 W&B 같은 로깅 툴에 박는다. $k$ 는 5 ~ 20 정도면 충분.
- 첫 1K ~ 2K step 안에 $r_k$ 가 초기값에서 의미 있게 움직이지 않거나 $\Delta H$ 부호가 고정이면 노란불.

이걸 곧장 자동 early stopping 트리거로 쓰는 건 권하기 어렵다. snippet 으로 검증된 건 "성공·실패 run 의 신호 모양이 다르다" 까지지, "특정 임계값을 넘으면 자동으로 종료해도 안전하다" 까지는 아니다. 임계값은 모델 쌍·태스크마다 달라질 가능성이 크다.

대신 디버깅 신호로는 즉시 쓸 만하다.

- $r_k$ 가 멈춰 있고 $\Delta H$ 가 한쪽으로 큰 음수 — 학생이 교사보다 훨씬 뾰족하다. on-policy sampling temperature 나 KL 계수 점검.
- $r_k$ 는 오르는데 $m_k$ 가 90% 아래에서 헤맨다 — 꼬리 토큰에 질량이 새고 있다. weighting 이나 loss 형태를 다시 본다.
- 두 신호 다 안 움직인다 — 학습 자체가 안 일어나고 있다. learning rate / gradient clipping / 데이터 분포 점검.

GPU 시간이 비싼 setup 일수록 이 두세 줄의 모니터링 이득이 크다. 한나절 굴리고 망한 걸 깨닫는 대신, 첫 한두 시간 안에 신호 모양만 보고 멈출 수 있다.

## 정리

- 성공한 OPD 는 token overlap (72→91%), shared top-$k$ 의 결합 확률 질량 점유 (97-99%), entropy gap narrowing 의 세 가지 외형을 일관되게 보인다.
- 실패한 OPD 는 overlap 이 정체되고 entropy mismatch 가 학습 출발부터 끝까지 유지된다.
- 이 신호들은 모델 내부를 안 봐도 출력 분포 위에서 계산되므로 phenomenology 다. 메커니즘 답은 못 주지만 이식성이 높다.
- 학습 루프에 두세 줄만 더해서 모니터링하면, 비싼 OPD run 의 실패를 초기 단계에서 알아챌 수 있다. 자동 종료보다는 디버깅 신호로 쓰는 편이 안전하다.

이전 편: [성공의 두 조건 — 호환성과 새로움](02-two-success-conditions.md)
다음 편: [실패하는 OPD 를 살리는 두 레시피](04-recovery-recipes.md)

## 출처

- [arxiv.org/abs/2604.13016](https://www.arxiv.org/html/2604.13016)
