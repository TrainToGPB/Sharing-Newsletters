---
title: HRPO 의 RL 목적함수와 학습 루프
date: 2026-05-16
author: TrainToGPB
tags: [강화학습, 추론, HRPO, GRPO, policy-gradient]
source: https://arxiv.org/html/2505.18454v2
summary: 정답 여부만으로 보상을 매기고 그룹 상대 어드밴티지로 표준화한 뒤, KL 정규화된 strictly on-policy policy gradient 로 hybrid latent reasoning 을 직접 학습하는 HRPO 의 RL 알고리즘을 정리.
format: details
part: 3
---

# HRPO 의 RL 목적함수와 학습 루프

> 원본: [arxiv.org/abs/2505.18454](https://arxiv.org/html/2505.18454v2)

직전 편에서는 hidden state 와 sampled token embedding 을 한 입력 벡터로 섞는 게이팅 메커니즘 — 즉 hybrid input 을 만드는 모듈 — 을 정리했다. 이번 편은 그 hybrid 디코딩을 어떻게 **학습** 시키는지에 초점을 맞춘다. HRPO 는 별도의 latent CoT supervision 없이 강화학습 한 가지로 게이트 파라미터를 포함한 정책 전체를 끌어올린다. 알고리즘 자체는 GRPO 계열에서 두 개의 선택지를 의도적으로 빼낸 가벼운 변형이고, 단순한 만큼 왜 그 선택을 했는지가 더 중요하다.

## 왜 강화학습으로 latent reasoning 을 학습하는가

기존 latent reasoning 연구의 흔한 학습 방식은 두 가지다. 하나는 CoT 트레이스 데이터셋을 모아서 토큰 단위로 supervised 학습하는 것이고, 다른 하나는 teacher 모델의 hidden state 를 student 가 모방하도록 증류하는 것이다. 둘 다 "어떤 latent 가 좋은 latent 인가" 에 대한 강한 가정을 외부에서 가져온다. 그러나 hidden state 의 의미는 모델마다 다르고 supervision 형태로 박아 넣기 어렵다. CoT 트레이스도 결국 자연어로 풀어쓴 한 가지 경로일 뿐이며, 모델 본래의 reasoning 패턴과 어긋날 수 있다.

저자들은 그래서 supervision 없이 **결과만 채점하는 RL** 로 가는 길을 택한다. LLM 이 hybrid rollout 을 직접 생성하게 두고, 정답인지 아닌지만 보고 그 정책을 업데이트한다. 이렇게 하면 두 가지 장점이 따라온다.

- CoT 트레이스나 latent supervision 같은 외부 데이터셋이 필요 없다. 정답 라벨만 있으면 된다.
- 학습 신호가 모델 본래의 분포에서 나오므로, LLM 의 native reasoning 패턴을 그대로 살린 채 latent 차원만 추가로 활성화시킬 수 있다.

그림 2 의 우측 (HRPO Training) 이 이 그림을 그대로 보여준다. 좌측의 hybrid 디코딩이 한 step 에서 어떻게 hidden 과 embedding 을 섞는지를 보여줬다면, 우측은 그렇게 만들어진 trajectory 여러 개로부터 어떻게 어드밴티지를 뽑고 정책을 갱신하는지를 보여준다.

![HRPO 학습 절차: 쿼리 하나에서 G 개의 hybrid rollout 을 만들고, 결과 보상을 그룹 내 표준화한 어드밴티지로 변환한 뒤, KL 정규화된 policy gradient 로 정책을 갱신한다. 좌측의 hybrid 디코딩 (직전 편) 이 이 우측 학습 루프의 한 step 안에 그대로 들어간다.](../assets/fig-2.png)

## 목적함수: outcome 보상 + 그룹 상대 어드밴티지

HRPO 의 목적함수는 식 (5) 와 같이 쓸 수 있다. 쿼리 $q$ 는 데이터셋 $D$ 에서 뽑고, 그 쿼리에 대해 정책 $\pi_\theta$ 가 hybrid 한 출력 $(a, h)$ 를 만들어 낸다. $a$ 는 매 step 에서 샘플링된 이산 토큰의 시퀀스, $h$ 는 같은 step 들에서 누적된 연속 hidden representation 시퀀스다. 보상 $R$ 은 정답 $a^*$ 와 비교한 outcome-based scalar 이다.

$$
\max_\theta \; \mathbb{E}_{q \sim D,\; (a, h) \sim \pi_\theta(\cdot \mid q)} \big[\, R(a, a^*) \,\big]
$$

여기서 두 가지 디테일이 중요하다.

- **보상은 answer span 의 이산 토큰만으로 채점된다.** 모델이 생성한 hybrid trajectory 안에서 hidden 부분은 채점 대상이 아니다. 정답으로 도출된 토큰 시퀀스만 ground truth 와 비교해서 정답이면 $R = 1$, 오답이면 $R = 0$. 즉 학습 신호는 어디까지나 "최종 답을 맞췄는가" 한 비트짜리 정보다.
- **보상 모델이 없다.** RLHF 식의 학습된 reward model 도, value 추정용 critic 도 두지 않는다. 이는 수식상의 단순성뿐 아니라 메모리 측면에서도 의미가 크다. 작은 1.5B / 3B 모델 위에서 hidden state 까지 통째로 propagation 한다는 점을 감안하면, value head 한 벌을 더 들고 다니는 비용이 무시 못 할 수준이기 때문이다.

낮은 분산의 unbiased 어드밴티지를 얻기 위해 HRPO 는 GRPO 와 같은 **그룹 상대 표준화** 를 쓴다. 같은 쿼리 $q$ 에 대해 $G$ 개의 hybrid rollout 을 동시에 만들고, 그 그룹 안에서 보상의 평균과 표준편차로 표준화한 값을 어드밴티지로 본다. $i$ 번째 응답의 어드밴티지 $A_i$ 는 직관적으로 다음과 같이 적을 수 있다.

$$
A_i = \frac{R_i - \mathrm{mean}(\{R_1, \dots, R_G\})}{\mathrm{std}(\{R_1, \dots, R_G\})}
$$

쿼리 한 개당 trajectory 가 여러 개 있으니, "같은 입력에서 어떤 rollout 이 다른 rollout 보다 얼마나 더 잘했나" 라는 상대 신호가 자동으로 잡힌다. 보상이 $\{0, 1\}$ 두 값밖에 안 가져도 그룹 분산을 통해 의미 있는 스케일로 정규화되며, baseline 으로 별도의 value function 을 학습할 필요도 사라진다. value-free + group-relative 구조는 학습 인프라를 가볍게 가져갈 수 있게 해주는 핵심이다.

여기서 $G$ 의 크기는 학습 신호의 질을 결정한다. $G$ 가 너무 작으면 그룹 안에서 모두 정답이거나 모두 오답인 경우가 자주 생겨 표준편차가 0 에 가까워지고, 어드밴티지가 수치적으로 폭주하거나 사실상 0 으로 사라진다. 반대로 $G$ 가 너무 크면 한 step 의 generation 비용이 그만큼 늘어난다. HRPO 가 hybrid 디코딩이라 한 step 당 생성 비용이 일반 GRPO 보다 무거운 편이라는 점을 감안하면, $G$ 의 선택은 단순한 하이퍼파라미터가 아니라 "쿼리 다양성 대 그룹 안 분산 확보" 의 트레이드오프로 봐야 한다. 실제 구현에서는 보상이 한 쪽으로 쏠린 그룹을 어떻게 처리하느냐 (그대로 두기, 작은 epsilon 더하기, 그 step 자체를 스킵하기) 도 학습 안정성에 적지 않은 영향을 준다.

## Policy gradient 와 KL 정규화

이 어드밴티지를 가지고 식 (6) 의 policy gradient 가 정의된다. 형태는 REINFORCE 에 KL 정규화를 얹은 단순한 모양이다. 그룹 안의 각 응답에 대해, 그 응답을 구성하는 토큰들의 log-prob 에 $A_i$ 를 가중치로 곱하고, 거기서 참조 모델 $\pi_{\mathrm{ref}}$ 와의 KL 발산을 $\beta$ 만큼 빼준다.

$$
\nabla_\theta \mathcal{J}(\theta) \;\propto\; \mathbb{E}\Big[\, A_i \cdot \nabla_\theta \log \pi_\theta(a_i \mid q) \;-\; \beta \, \nabla_\theta D_{\mathrm{KL}}\!\big(\pi_\theta \,\|\, \pi_{\mathrm{ref}}\big) \,\Big]
$$

해석은 평범하다. 더 높은 보상을 받은 hybrid trajectory 일수록 큰 양의 어드밴티지를 받아, 그 안의 reasoning 토큰들의 log probability 가 올라가도록 정책이 갱신된다. KL 항은 참조 모델 (보통 학습 시작 시점의 SFT 모델 또는 base instruct 모델) 에서 너무 멀어지지 않도록 제동을 거는 정규화다.

여기서 HRPO 만의 작은 디테일이 하나 더 있다. KL 항에서 $\pi_\theta$ 의 log probability 를 계산할 때, **hidden representation 을 통한 경로가 아니라 sampled token ID 만으로 계산** 한다. 즉, $\theta$ 갱신을 위한 KL 도 결국 일반 token-level distribution 의 KL 로 환원해서 본다. 저자들은 이렇게 했을 때 학습 안정성이 더 좋다고 보고한다.

왜 이게 차이를 만드는지 직관적으로 보면, hidden representation 자체가 학습 도중 모양을 빠르게 바꾸기 때문이다. KL 까지 hidden 의 분포 차이로 매기면 $\beta$ 한 개로 $\pi_\theta$ 분포 차이와 hidden 표현 차이를 동시에 잡으려는 셈이 되어 하이퍼파라미터 튜닝 부담이 커진다. token-only KL 은 분포 매칭의 reference 를 토큰 시퀀스 차원에 고정시켜 놓고, hidden 은 그 안에서 자유롭게 변형되도록 두는 분업에 가깝다. 다르게 말하면, KL 은 "참조 모델과 비슷한 답을 내라" 는 거시적 제약만 담당하고, hidden 표현이 hybrid 비중을 늘려가며 어떤 latent 패턴을 만들어 가는가는 어드밴티지 가중 항이 전적으로 책임진다.

KL 항의 또 다른 기능은 작은 backbone 에서의 reward hacking 방지다. 보상이 outcome 한 비트라서 모델은 우회 경로 — 가령 답 토큰만 외우고 reasoning 을 회피하는 식 — 으로 보상을 쉽게 끌어올릴 수 있다. KL 이 참조 모델 (보통 SFT 초기 분포) 에서 멀어지지 못하게 해주기 때문에 그런 degenerate 정책으로 흘러갈 여지가 줄어든다. $\beta$ 의 크기는 결국 "탐험을 얼마나 허락할 것인가" 의 손잡이가 된다.

## PPO / GRPO 와 다른 두 가지 선택

식 (6) 만 보면 PPO 나 GRPO 의 표준 식과 다른 점이 두 가지 있다.

1. **likelihood ratio 와 clipping 을 생략했다.** PPO 류 알고리즘은 보통 $\pi_\theta(a \mid q) / \pi_{\theta_{\mathrm{old}}}(a \mid q)$ 같은 importance sampling ratio 를 곱하고 그 ratio 가 $[1 - \epsilon, 1 + \epsilon]$ 밖으로 튀면 clip 한다. HRPO 는 그냥 raw log-prob 을 쓴다. 저자들은 자기네 보수적인 학습 스케줄 — 작은 학습률, 비교적 적은 epoch — 하에서 ratio clipping 이 실질적으로 거의 발동되지 않는다는 관찰을 근거로 든다. 어차피 안 잡히는 안전장치라면, 코드 단순화와 메모리 절약을 위해 빼는 편이 낫다는 판단이다. 다만 이건 양날의 검이라, 학습률을 올리거나 KL 가중치 $\beta$ 를 너무 낮춰서 정책이 빠르게 움직이는 상황으로 가면 안정성이 무너질 여지가 있다. HRPO 를 좀 더 공격적인 setting 으로 옮길 때는 ratio + clip 을 다시 붙이는 것이 안전하다.
2. **한 trajectory 는 단 한 번의 gradient update 에만 쓴다.** PPO / GRPO 는 보통 mini-batch 안에서 같은 rollout 을 여러 epoch 돌리면서 importance sampling 으로 보정해 재사용한다. HRPO 는 strictly on-policy 다. 이유는 명확하다. hybrid 입력의 hidden 부분이 정책 파라미터 $\theta$ 에 직접 묶여 있기 때문이다. $\theta$ 가 한 번이라도 갱신되면 같은 trajectory 안의 hidden 값들이 더 이상 "현재 정책" 의 hidden 이 아니게 되고, importance sampling 으로 보정해도 on-policy 가정이 깨진다. 그래서 단 한 번만 쓰고 버린다.

두 번째 제약은 알고리즘적으로 깔끔하지만 실무적으로는 처리량을 갉아먹는다. PPO 가 mini-batch 한 묶음으로 여러 step 의 update 를 뽑아내는 반면, HRPO 는 동일한 update 수를 얻으려면 그만큼 더 많은 rollout 을 굴려야 한다. 학습 wall-clock 의 상당 부분이 generation 에 잡아먹힌다는 의미다. 다만 value model 이 없고 ratio / clip 회로도 없어 update step 자체는 가볍고, GRPO 보다도 코드량이 적다.

값을 가르는 결정적인 차이는 hidden 의 미분 경로다. 일반 RLHF / GRPO 에서는 trajectory 안의 토큰들이 정책으로부터 샘플링된 결과일 뿐이라, gradient 가 token 분포로만 흐른다. importance sampling 으로 보정해서 두세 epoch 재사용해도 큰 문제가 없다. 반면 HRPO 는 trajectory 안의 hidden representation $h$ 가 그 자체로 $\theta$ 의 결정론적 함수다. $\theta$ 를 한 번이라도 갱신하면 같은 입력 시퀀스에서 다시 forward 했을 때 $h$ 값 자체가 달라진다. 이 변화는 token 분포의 importance sampling 으로는 보정되지 않는다. 그래서 PPO 스타일의 trajectory 재사용은 단순한 분산 증가가 아니라 편향까지 들여오게 된다. strictly on-policy 가 비용이 아니라 정합성 제약이라는 점이 HRPO 의 알고리즘 설계에서 가장 미묘한 부분이다.

요약하면 HRPO 는 GRPO 에서 value-free 어드밴티지 구조만 가져오고, hybrid 입력과 충돌하는 부분 (ratio clipping, trajectory 재사용) 을 잘라낸 가벼운 on-policy REINFORCE 변형이다. 추가로 KL 계산의 분업 (token-only) 한 가지가 hidden 의 빠른 변형과 정책 분포의 안정성을 동시에 잡는 디테일이다.

## 한 페이지 학습 루프

이상의 선택들을 한 step 의 의사 절차로 묶으면 다음과 같다.

1. 데이터셋 $D$ 에서 쿼리 $q$ 를 한 묶음 샘플링한다.
2. 각 $q$ 에 대해 현재 정책 $\pi_\theta$ 로 hybrid rollout 을 $G$ 개 생성한다. 매 step 의 입력은 직전 편의 게이팅 식에 따라 sampled token embedding 과 hidden representation 의 혼합이며, 출력은 그 다음 토큰 분포다. 게이트 비율 $\alpha$ 는 학습 step 에 따라 점진적으로 hidden 비중을 키운다.
3. 각 rollout 의 answer span 을 ground truth 와 비교해 $R \in \{0, 1\}$ 보상을 매긴다.
4. 같은 $q$ 그룹 안에서 보상을 평균·표준편차로 표준화해 어드밴티지 $A_i$ 를 얻는다.
5. 식 (6) 의 policy gradient 로 $\theta$ 를 한 step 갱신한다. KL 항은 sampled token ID 기준의 log-prob 으로 계산한다.
6. 같은 trajectory 는 다시 쓰지 않고 버린다. 다음 step 은 새 쿼리 묶음에서 처음부터 다시 rollout 한다.

value function 이 없으므로 critic 학습 단계가 빠지고, ratio clipping 이 없으므로 epoch 루프도 없다. 전체 update 사이클은 PPO 보다 단순하고 GRPO 보다도 약간 더 가볍다. 저자들이 "lightweight 하면서 다른 RL 최적화와 결합하기 쉽다" 고 강조하는 이유다. 코드 레벨 디테일은 공개된 구현 ([github.com/Yueeeeeeee/HRPO](https://github.com/Yueeeeeeee/HRPO)) 에서 확인할 수 있다.

실무적으로 이 루프가 학습 처리량에 주는 영향은 다음 세 갈래로 정리할 수 있다. 첫째, generation : update 비율이 PPO 류보다 높다. trajectory 재사용이 없으니 매 step 마다 새로 rollout 을 만들어야 하고, hybrid 디코딩은 일반 토큰 생성보다 마이크로배치 안에서 동기화해야 할 텐서가 한 종류 더 늘어난다. 둘째, value head 가 없어 옵티마이저 상태와 액티베이션 메모리가 줄어든다. 1.5B / 3B 모델 위에서 hybrid 입력의 hidden 까지 backprop 하는 시점에서 이 절약은 사실상 batch size 한두 단계만큼의 여유로 돌아온다. 셋째, KL 항이 token-only 라서 KL gradient 계산이 hidden 경로와 분리되어 있다. 즉 한 step 의 그래프가 "어드밴티지 가중 hybrid log-prob 항" 과 "token-only KL 항" 두 개의 비교적 독립적인 부분으로 나뉘어, 구현·디버깅 측면에서 일반 GRPO 와 큰 격차 없이 다룰 수 있다.

다음 편에서는 이 단순한 RL 알고리즘과 hybrid 입력 구조를 결합한 실제 결과를 살펴본다. 지식 집약 (open-domain / multi-hop QA) 과 STEM 추론 두 축에서, 1.5B·3B 의 작은 Qwen 모델이 RL 베이스라인과 더 큰 RAG 베이스라인을 어떻게 따라잡는지를 본다.

다음 편: [04. 벤치마크 결과 — 지식과 STEM](04-results-on-knowledge-and-stem.md)

## 출처

- 논문 본문 3.2 Hybrid Reasoning Policy Optimization (HRPO), 식 (5) 및 (6): [arxiv.org/abs/2505.18454](https://arxiv.org/html/2505.18454v2)
- 그룹 상대 어드밴티지의 원형: GRPO ([DeepSeekMath, Shao et al., 2024](https://arxiv.org/abs/2402.03300))
- 구현: [github.com/Yueeeeeeee/HRPO](https://github.com/Yueeeeeeee/HRPO)
