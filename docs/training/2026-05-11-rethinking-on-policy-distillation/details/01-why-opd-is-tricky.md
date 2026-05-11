---
title: On-Policy Distillation 은 왜 까다로운가
date: 2026-05-11
author: Claude
tags: [distillation, post-training, on-policy, rl, sft]
source: https://www.arxiv.org/html/2604.13016
summary: OPD 가 post-training 에서 차지하는 위치와 빈번한 실패 — 이 논문이 풀려는 질문.
format: details
part: 1
---

# On-Policy Distillation 은 왜 까다로운가

> 원본: [arxiv.org/abs/2604.13016](https://www.arxiv.org/html/2604.13016)

## 한 줄 정리

On-Policy Distillation (이하 OPD) 은 직관적으로는 SFT 와 RL 의 좋은 점을 동시에 가져갈 수 있어야 하지만, 실제로는 같은 셋업에서도 들쭉날쭉한 결과가 나온다. 이 논문은 그 변동성을 우연이 아니라 학습 동역학의 구조적 결과로 보고, 언제·왜 성공·실패하는지를 분해한다.

## Post-training 의 세 갈래

LLM 의 pre-training 이 끝난 다음, 모델을 쓸 만한 어시스턴트로 만들기 위한 post-training 은 보통 세 갈래로 분류된다.

- SFT (supervised fine-tuning): 사람이 쓴 정답, 혹은 다른 모델이 쓴 정답 시퀀스를 그대로 흉내내게 한다. 학습 데이터의 모든 위치에서 dense 한 token-level 신호가 들어오는 것이 장점이다. 단점은 학습 분포가 학생 자신의 분포와 어긋날 수 있다는 점. 학생이 추론 도중 한 번 미끄러져 학습에서 본 적 없는 상태에 도달하면, 그 다음 토큰에 대한 감독이 사실상 없어진다. 이른바 exposure bias.
- RL (reinforcement learning): RLHF, RLAIF, RLVR 같은 변종이 포함된다. 학생이 직접 rollout 한 trajectory 위에서 reward 신호를 받는다. 학생이 실제로 갈 만한 상태 위에서 학습이 이뤄지므로 분포 mismatch 가 작다. 단점은 reward 가 듬성듬성하다는 점이다. 수십에서 수천 토큰짜리 응답 하나에 스칼라 한 개가 떨어지면, 그 중 어느 토큰이 좋았고 어느 토큰이 나빴는지를 가르는 신용 할당이 어렵다.
- Distillation: 더 강한 교사 모델의 출력을 학생이 흉내내게 한다. 가장 흔한 형태는 off-policy distillation 으로, 교사가 만든 답안에 대해 학생을 SFT 하는 것이다. 이는 사실상 SFT 의 데이터 출처를 교사 모델로 바꾼 버전이다.

OPD 는 이 세 갈래 사이에 끼어 있다. 학생이 직접 sampling 한 토큰 시퀀스 위에서 — 즉 on-policy state 위에서 — 그 다음 토큰에 대한 교사 모델의 분포 $p_\text{teacher}(\cdot \mid x_{<t})$ 를 신호로 받는다. KL divergence 같은 token-level loss 가 매 step 들어오기 때문에, RL 의 sparse reward 와 비교하면 신호 밀도가 비교가 안 되게 높고, SFT 와 비교하면 학생이 실제로 도달한 상태 위에서 학습된다는 점이 다르다.

## 왜 그렇게 매력적으로 보이는가

OPD 가 매력적으로 들리는 이유는 종이 위에서 보면 두 패러다임의 약점을 동시에 메우는 것처럼 읽히기 때문이다.

- 학생이 한 번 미끄러진 상태에서 다음 토큰을 예측할 때, 그 위치에서 교사가 어떤 분포를 권하는지를 매번 들을 수 있다. SFT 가 닿지 못하던 학생-side state 까지 감독이 따라간다.
- 매 토큰마다 dense 한 신호가 들어오므로 신용 할당 문제는 RL 보다 가볍다. 또한 reward model 을 따로 학습할 필요가 없다. 교사가 곧 reward 의 역할을 한다.
- 데이터 만들기가 SFT 데이터 큐레이션보다 가볍다. 프롬프트만 있으면 학생이 굴리는 동안 교사가 옆에서 매 step 점수를 매겨준다.

요약하면, "학생이 실제로 만든 trajectory + dense token-level teacher 신호" 라는 조합은 적어도 화이트보드 위에서는 거의 무손실로 보인다.

## 그런데 실패가 흔하다

문제는 실무 보고다. 같은 학생 모델, 같은 교사 모델, 같은 도메인의 프롬프트로도, OPD 셋업의 결과는 의외로 들쭉날쭉하다. 다음과 같은 패턴이 누적되어 왔다.

- 어떤 학생·교사 조합에서는 OPD 가 강한 SFT baseline 을 또렷이 넘는다.
- 다른 조합에서는 같은 OPD 셋업이 SFT 와 비슷하거나, 오히려 학습 초반에 학생을 망가뜨린다.
- 종종 같은 모델 패밀리 안에서도 결과가 갈린다. 학생을 조금만 바꿔도 그래프가 뒤집힌다.

엔지니어가 흔히 의심하는 변수 — 학습률, KL 가중치, sampling temperature, batch size — 를 흔드는 것만으로는 이 변동성이 잘 설명되지 않았다. 즉 OPD 의 실패는 하이퍼파라미터 튜닝의 문제가 아니라 그보다 한 단계 위에 있는 구조적 문제일 가능성이 높다는 것이 이 논문의 출발점이다.

## 이 논문이 답하려는 질문

논문 제목 "Rethinking On-Policy Distillation of Large Language Models: Phenomenology, Mechanism, and Recipe" 는 그 자체로 답하려는 세 질문을 그대로 노출한다.

- Phenomenology — 언제 성공하고 언제 실패하는가. 외형적으로 어떤 학생·교사·태스크 조합에서 OPD 가 살아남는가, 어떤 조합에서는 무너지는가.
- Mechanism — 그 안에서 토큰 단위로 실제로 무엇이 일어나는가. 학생의 sampling 분포와 교사의 분포가 만났을 때, gradient 가 어떤 방향으로 학생을 끌고 가는가.
- Recipe — 실패 케이스를 살릴 실무 처방은 무엇인가. 알고리즘을 갈아엎지 않고도 적용 가능한 변경은 무엇인가.

이 세 층을 한꺼번에 따로 보지 않고 같은 프레임에서 연결한다는 점이 이 논문의 핵심 기여다. Phenomenology 단계에서 발견한 두 갈래 패턴이 mechanism 단계의 토큰 동역학 분석으로 설명되고, 그 분석이 곧장 recipe 단계의 두 가지 회복 전략으로 이어진다.

## 본 시리즈 미리보기

다음 편부터는 위 세 층을 차례로 풀어간다. 먼저 2편에서는 OPD 가 성공하기 위한 두 가지 조건 — 학생과 교사가 호환되는 thinking pattern 을 공유하는가, 그리고 교사가 학생이 학습 중 보지 못한 새 능력을 실제로 제공하는가 — 을 정리한다. 3편에서는 그 조건이 무너졌을 때 token-level 에서 어떤 일이 벌어지는지, 즉 mechanism 을 본다. 4편에서는 그 분석에 직접 대응되는 두 가지 회복 처방 — off-policy cold start 와 teacher-aligned prompt selection — 을 다룬다. 마지막 5편에서는 공개된 verl v0.7.0 + LlamaFactory v0.9.5 기반 코드 (thunlp/OPD) 를 어떻게 우리 환경에 옮겨붙일 수 있을지를 정리한다.

OPD 를 한 번이라도 돌려봤다가 결과가 이상해서 덮어둔 경험이 있는 독자라면, 다음 편이 가장 먼저 와 닿을 것이다.

다음 편: [두 가지 성공 조건 — 호환성과 새로움](02-two-success-conditions.md)

## 출처

- https://www.arxiv.org/html/2604.13016
