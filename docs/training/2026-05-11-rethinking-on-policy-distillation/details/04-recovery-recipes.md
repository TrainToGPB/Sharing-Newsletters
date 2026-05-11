---
title: 실패하는 OPD 를 살리는 두 레시피
date: 2026-05-11
author: Claude
tags: [distillation, on-policy, cold-start, sft, prompt-selection]
source: https://www.arxiv.org/html/2604.13016
summary: 교사 rollout SFT 로 워밍업한 다음 OPD 를 돌리는 cold start, 그리고 교사 post-training 분포에서 prompt 를 뽑는 teacher-aligned selection. 둘 다 초기 overlap 을 끌어올려 실패 run 을 성공 dynamic 으로 되돌린다.
format: details
part: 4
---

# 실패하는 OPD 를 살리는 두 레시피

> 원본: [arxiv.org/abs/2604.13016](https://www.arxiv.org/html/2604.13016)

앞 편에서 OPD 의 실패가 어디서 새는지 토큰 단위로 짚었다. 학생이 만든 rollout 의 초기 overlap ratio 가 너무 낮으면, 교사 signal 이 닿는 토큰이 희박해지고, advantage 가 노이즈에 잠긴 채 entropy 가 부풀어 run 전체가 망가진다. 이 편은 그 미시 신호를 거꾸로 활용한다. 초기 overlap 을 끌어올릴 수 있다면 실패 run 을 성공 run 의 dynamic 으로 되돌릴 수 있다는 것이 본 논문의 회복 전략이다. 두 가지 레시피가 제안된다. 하나는 학생 weight 자체를 옮기는 off-policy cold start, 다른 하나는 학생이 방문하는 state 분포를 옮기는 teacher-aligned prompt selection.

## 두 레시피가 공격하는 지점

두 전략 모두 "교사·학생 사이의 분포 mismatch" 라는 동일한 병목을 노린다. 다만 옮기는 대상이 다르다.

- Cold start 는 학생의 정책 $\pi_s$ 자체를 교사 $\pi_t$ 쪽으로 미리 당겨놓는다. OPD 가 시작되는 시점의 $\pi_s^{(0)}$ 가 $\pi_t$ 와 더 겹치게 만든다.
- Prompt selection 은 학생이 만들어내는 state 의 marginal 분포 $d^{\pi_s}(s)$ 를 교사가 익숙한 분포 $d^{\pi_t}(s)$ 쪽으로 옮긴다. 같은 정책이라도 어떤 prompt 에서 출발하느냐에 따라 학생이 도달하는 토큰 영역이 달라지기 때문이다.

두 축은 직교한다. 정책을 끌어당기는 것과, 정책이 살아 움직이는 prompt 분포를 바꾸는 것은 서로 간섭하지 않는다. 논문은 이 둘을 명시적으로 complementary 하다고 정리한다.

## 레시피 1 — Off-Policy Cold Start

핵심은 단순하다. OPD 를 시작하기 전, 교사가 생성한 응답으로 학생을 짧게 SFT 워밍업한 뒤, 그 weight 에서 OPD 를 출발시킨다. 교사가 그어 놓은 thinking pattern 의 윤곽선을 학생이 따라 그릴 줄 알게 한 다음에야 on-policy 학습이 의미를 갖는다는 발상이다.

### 셋업

- 학생: Qwen3-1.7B
- 교사: Qwen3-4B (Non-thinking)
- 데이터: OpenThoughts3-1.2M 의 math-domain subset, 그 위에서 교사가 만든 응답 200K 개
- 절차: 위 200K 로 학생을 SFT (Qwen3-1.7B-SFT) 한 뒤, 같은 prompt set 으로 OPD 를 진행

비교 대상은 동일한 OPD 설정에서 출발 weight 만 다르다. 한 쪽은 Qwen3-1.7B-Base, 다른 쪽은 Qwen3-1.7B-SFT.

### 무엇이 좋아지는가

논문에서 관찰된 결과는 다음과 같다.

- Qwen3-1.7B-SFT 에서 시작한 학생이 Qwen3-1.7B-Base 에서 시작한 학생보다 일관되게 검증 성능에서 앞선다.
- 그 격차는 학습 초반에만 머물지 않고 끝까지 유지된다. 논문은 이를 "the off-policy cold start improves not only early optimization, but also the final performance ceiling of subsequent OPD" 로 정리한다.
- SFT 로 시작한 trajectory 는 초기 overlap 이 이미 높고, 학습이 매끄럽고 안정적이며 entropy gap 도 작은 채로 진행된다.
- Base 에서 시작한 trajectory 는 초기 overlap 이 낮고, 한참을 불안정하게 헤맨 뒤에야 점진적으로 회복된다.

여기서 흥미로운 부분은 격차가 끝까지 유지된다는 점이다. 통상적으로 "warmup 은 초기 가속일 뿐" 이라는 직관을 갖기 쉬운데, OPD 에서는 그 가속이 그대로 최종 천장의 차이로 굳는다. 앞 편의 phenomenology 와 묶어 읽으면 이유가 납득된다. 초반에 overlap 이 낮은 채로 굴린 run 은 그 시기에 noise 가 흘러 들어가 정책이 일정 영역으로 굳어버린 뒤이고, 그 lock-in 을 뒤늦게 풀어내기 어렵기 때문이다.

### 왜 동작하는가 — 분포 관점

OPD 의 학습 신호는 학생 rollout 토큰 위에서 정의된 advantage 와, 그 토큰들의 교사 확률에 의존한다. 학생이 만든 토큰 시퀀스가 교사가 거의 만들지 않을 영역에 있으면, 교사 signal 의 분산이 폭발한다.

cold start 는 OPD 가 시작되기 전에 $\pi_s$ 와 $\pi_t$ 의 KL 을 미리 줄여 놓는 과정으로 읽을 수 있다.

$$
\mathrm{KL}(\pi_s^{(0)} \,\|\, \pi_t) \;\to\; \text{small after SFT}
$$

KL 이 작아지면 학생 rollout 의 overlap ratio 분포가 위로 밀려 올라가고, 동일한 OPD step 에서 더 많은 토큰이 useful learning signal 을 받는다. 학습 초반의 noise 가 줄면 entropy 가 부풀지 않고, advantage 추정이 안정되며, 이후의 모든 step 이 그 위에서 누적된다.

## 레시피 2 — Teacher-Aligned Prompt Selection

cold start 가 정책을 옮기는 쪽이라면, prompt selection 은 그 정책이 만들어내는 state 분포를 옮기는 쪽이다. 논문은 OPD 학습 prompt 를 교사의 post-training 데이터 분포에서 뽑을 것을 제안한다. 즉 "교사가 어떤 prompt 위에서 학습했는지" 를 기억하고, 같은 source/topic/스타일에서 OPD prompt 를 큐레이션한다.

### 메커니즘

교사가 익숙한 prompt 에서 학생이 rollout 을 만들면, 학생이 도달하는 토큰 영역도 자연히 교사가 충분히 학습한 영역과 겹친다. 그 영역에서 교사의 토큰 분포는 더 sharpen 되어 있고, advantage 신호의 SNR 이 높다. 학생은 high-probability token 위에서 더 또렷한 정렬 신호를 받는다.

state visitation 관점으로 다시 쓰면 다음과 같다.

$$
d^{\pi_s}(s) \;\to\; \text{closer to } d^{\pi_t}(s)
$$

학생 정책 자체는 그대로 두고도, prompt 분포만 옮겨도 학생이 방문하는 state 의 marginal 이 교사 쪽으로 이동한다. 이 효과는 cold start 와 다른 축이라 동시에 적용할 수 있다.

### 결합

두 전략을 같이 쓰면 정책과 state 분포 양쪽이 동시에 정렬된다. 결합한 run 의 dynamic signature 는 자연 성공 run 과 같은 모습을 보인다. overlap ratio 가 학습 내내 안정적으로 상승하고, 토큰 단위 advantage 가 꾸준히 개선되며, entropy gap 이 좁아진다. 앞 편에서 정의한 성공 run 의 미시 지표가 그대로 나타난다는 의미다.

## 회복 후의 dynamic

논문이 강조하는 부분은 단순한 점수 향상이 아니라 "회복된 run 이 자연 성공 run 과 통계적으로 같은 궤적을 그린다" 는 사실이다. 이는 진단 도구로서의 phenomenology 가 그대로 처방 검증 도구가 된다는 의미다. 다음 항목을 확인하면 회복이 잘 됐는지 판단할 수 있다.

- overlap ratio 가 step 에 따라 단조 증가 (혹은 적어도 평탄·상승 추세)
- 토큰 단위 advantage 의 평균이 점진적으로 개선
- entropy gap (학생·교사 사이) 이 좁아지는 방향

세 지표가 모두 살아 움직이면 그 run 은 성공 dynamic 위에 올라간 것이고, 한두 가지가 정체하면 cold start 강도를 키우거나 prompt source 를 더 좁혀야 한다.

## 실무에서 어떻게 적용하나

이 회복 전략을 우리 환경에서 다시 짠다면 다음 순서로 가는 것이 합리적이다.

- 교사 SFT 가 공개 weight 로 있다면 그것을 학생의 cold start 출발점으로 그대로 사용한다. base weight 에서 바로 OPD 를 던지는 것은 가장 비싼 옵션이다.
- 공개 weight 가 없다면 교사가 rollout 을 만든 데이터로 학생을 짧게 SFT 한 뒤 그 weight 를 출발점으로 삼는다. 본 논문의 200K 응답 규모는 reference scale 로 참고할 만하다.
- OPD prompt 큐레이션 시, 가능한 한 교사 post-training 의 source/도메인/스타일과 분포를 매칭한다. 자체 도메인을 섞을 때도 교사가 거의 본 적 없는 영역은 별도 단계로 분리하거나, mix ratio 를 매우 낮게 유지한다.
- 학습 첫 1-2K step 의 overlap ratio 를 항상 모니터한다. 이 구간에서 overlap 이 매우 낮고 정체되어 있으면, 더 진행해서 손해를 누적시키지 말고 cold start 단계부터 재검토한다.

코드 측면에서 본 논문은 thunlp/OPD 저장소에 verl v0.7.0 기반의 OPD/GRPO 학습 프레임워크, LlamaFactory v0.9.5 기반의 cold start SFT 파이프라인, 그리고 OPD/SFT/RL 스크립트를 함께 제공한다. token 선택 전략, generation control, reward weighting scheme 등이 설정 가능하므로, 위 레시피를 그대로 재현하거나 우리 도메인에 맞춰 변형하기에 무리가 없다.

## 한 줄 정리

cold start 는 학생 weight 를 교사 쪽으로 미리 옮기고, teacher-aligned prompt selection 은 학생이 방문하는 state 분포를 교사 쪽으로 옮긴다. 둘 다 초기 overlap 을 끌어올리는 방향이고, 그 효과는 초기 가속에 그치지 않고 OPD 의 최종 천장까지 올린다. 다음 편에서는 이 전체 결과를 우리 팀이 OPD 를 돌릴 때 점검할 체크리스트로 정리한다.

이전 편: [토큰 단위 phenomenology — 성공·실패의 미시 신호](03-token-level-phenomenology.md)

다음 편: [정리 — 우리 팀이 OPD 를 돌릴 때 점검할 것](05-implications-and-checklist.md)

## 출처

- [arxiv.org/abs/2604.13016](https://www.arxiv.org/html/2604.13016)
