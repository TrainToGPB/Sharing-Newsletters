---
title: 학생 궤적을 교사가 토큰 단위로 채점한다 — Reverse KL 과 알고리즘
date: 2026-05-13
author: TrainToGPB
tags: [사후학습, 증류, reverse-KL, on-policy]
source: https://thinkingmachines.ai/blog/on-policy-distillation/
summary: 학생 자신의 rollout 에 대해 교사가 매 토큰의 reverse KL 을 부여하는 per-token 손실을 정의한다. mode-seeking, unhackable, exposure bias 감소 같은 성질과 RL 위에 한 줄 추가로 구현되는 pseudocode 를 본다.
format: details
part: 2
---

# 학생 궤적을 교사가 토큰 단위로 채점한다 — Reverse KL 과 알고리즘

> 원본: [thinkingmachines.ai/blog/on-policy-distillation](https://thinkingmachines.ai/blog/on-policy-distillation/)

직전 편에서는 사후학습의 세 갈래 — off-policy SFT, on-policy RL, on-policy distillation — 를 비교하며, 학생이 자기 자신의 궤적을 뽑되 교사가 그 궤적을 dense 하게 채점한다는 그림을 세웠다. 이번 편은 그 채점이 구체적으로 어떤 손실 함수인지, 왜 하필 reverse KL 인지, 그리고 실제 학습 코드가 RL 코드 위에서 얼마나 가벼운 변경으로 구현되는지를 본다. 그림 없이 수식과 코드만으로 정리한다.

## 한 줄 요약 — 학생이 만든 토큰마다 교사가 매긴 점수

핵심 아이디어는 단순하다. 학생 모델 $\pi_\theta$ 가 평소처럼 trajectory 를 샘플링한다. 그 trajectory 의 매 토큰에 대해, 같은 prefix 를 본 교사 모델 $\pi_{\mathrm{teacher}}$ 의 확률과 학생의 확률을 비교한다. 두 분포가 같으면 점수가 0, 학생이 교사가 잘 안 뽑을 토큰을 뽑았을수록 큰 페널티가 부여된다. 이 페널티를 음의 advantage 로 RL 학습 루프에 그대로 흘려보내면 끝이다. trajectory 자체는 student-on-policy 지만, 보상이 token-level 로 dense 하다는 점이 RL 의 sparse reward 와 결정적으로 다르다.

체스에 비유한다면 직전 편의 그림 그대로다. 혼자 두는 RL 은 매치가 끝나야 승패라는 1bit 짜리 신호가 들어온다. on-policy distillation 은 같은 매치를 두는 동안 교사가 옆에서 매 수마다 "blunder", "inaccuracy", "brilliant" 같은 등급을 매겨주는 셈이다. 손실 함수는 이 등급의 수학적 정의에 해당한다.

## per-token reverse KL 손실 함수

원문이 채택한 손실은 per-token reverse KL 이다. 학생이 생성한 prefix $x_{1..t}$ 조건에서 다음 토큰 $x_{t+1}$ 에 대한 학생 분포와 교사 분포 사이의 KL 을 토큰마다 계산하고, 학생이 실제로 뽑은 trajectory 에 대해 기댓값을 취한다.

$$\mathrm{KL}\bigl(\pi_\theta \,\Vert\, \pi_{\mathrm{teacher}}\bigr) = \mathbb{E}_{x \sim \pi_\theta}\!\bigl[\log \pi_\theta(x_{t+1} \mid x_{1..t}) - \log \pi_{\mathrm{teacher}}(x_{t+1} \mid x_{1..t})\bigr]$$

이 양은 학생이 어떤 상태에 있든 그 상태에서의 행동을 교사 분포에 가깝게 맞추도록 미는 양이다. 학생이 교사와 완벽히 똑같이 행동하면 KL 은 0, 학생이 교사가 거의 안 뽑을 토큰을 자신만만하게 뽑을수록 값이 커진다. 학습 신호로는 이 KL 의 음수를 advantage 로 사용한다. 즉 매 토큰의 advantage 는

$$A_t = -\bigl[\log \pi_\theta(x_{t+1} \mid x_{1..t}) - \log \pi_{\mathrm{teacher}}(x_{t+1} \mid x_{1..t})\bigr]$$

이다. RL 의 importance-sampling policy gradient 손실에 이 advantage 를 그대로 넣어 미분한다.

여기서 한 가지 디자인 선택이 들어간다. 원문은 discount factor 를 **$0$** 으로 잡는다. 다시 말해 시점 $t$ 에서 학생은 바로 다음 토큰 $x_{t+1}$ 만 고려하며, 그 뒤로 따라올 미래 토큰에 대한 기여는 advantage 에 섞지 않는다. 수학적으로는 $\gamma > 0$ 인 multi-step return 이 더 "정직한" 선택지이지만, 저자들이 실험적으로 시도해 보았을 때 $\gamma > 0$ 이 성능을 개선하지 못했다고 보고한다. 그래서 단순함을 따라 $\gamma = 0$ 을 택한다. 결과적으로 학습 신호는 토큰별로 독립적이며, 한 trajectory 안에서 토큰마다의 reverse KL 을 그저 평균 내는 모양새가 된다.

## Reverse KL 의 네 가지 좋은 성질

왜 forward KL 도 아니고 JS divergence 도 아닌 reverse KL 인가. 원문이 명시적으로 언급하는 좋은 성질이 네 가지다.

### 1. Mode-seeking

Reverse KL $\mathrm{KL}(\pi_\theta \,\Vert\, \pi_{\mathrm{teacher}})$ 는 잘 알려진 대로 mode-seeking 성질을 가진다. 교사 분포가 여러 개의 비슷한 mode 를 가지더라도, 학생은 그중 한 mode 에 집중적으로 확률을 몰아주는 방향으로 수렴한다. forward KL 이라면 모든 mode 를 커버하려고 분포를 넓게 펼치다가 어느 쪽에도 확신이 없는 어중간한 분포를 학습할 위험이 있는데, reverse KL 은 그렇지 않다. 사후학습의 목적이 "교사가 잘 하는 한 가지 행동을 학생이 그대로 흉내내게" 하는 것이라면, 분포를 한 mode 로 좁히는 mode-seeking 쪽이 바람직하다.

### 2. Unhackable

대부분의 학습된 reward model 은 학생이 "보상은 높지만 실제로 desirable 하지는 않은" 행동을 발견하는 reward hacking 문제에서 자유롭지 않다. Reverse KL 은 다르다. 정의상 KL 이 낮다는 것은 학생의 행동 분포가 교사의 행동 분포에 가깝다는 뜻이고, 교사가 좋은 모델이라면 그 자체가 "교사 관점에서 바람직한 행동을 할 확률이 높다" 와 동치다. 학생이 KL 을 우회해서 보상만 챙기는 경로 자체가 존재하지 않는다. 이 점에서 reverse KL 은 unhackable 한 reward 라고 부를 만하다.

### 3. Exposure bias 감소

Off-policy SFT 의 고질병은 exposure bias 다. 학생은 학습 중에는 항상 교사가 만든 깨끗한 prefix 위에서 다음 토큰을 예측하지만, 추론 시에는 자기 자신이 만든 prefix 위에서 토큰을 뽑아야 한다. 두 분포가 다르기 때문에 학생이 한 번 실수하면 학습 중 본 적 없는 상태로 빠르게 흘러가고, 거기서부터는 회복 능력이 없다. on-policy distillation 은 학생이 자기 trajectory 위에서 학습하므로 이 분포 불일치가 처음부터 없다. 학생이 빠질 만한 상태에서 어떻게 회복해야 하는지를 교사가 매 토큰 가르쳐 주는 그림이 된다.

### 4. RL 과의 자연스러운 시너지

RL 도 결국 reward model 에 의해 유도되는 sequence-level reverse KL 의 한 형태를 최적화한다. 즉 on-policy distillation 은 RL 과 다른 종류의 손실이 아니라, sequence-level 신호를 token-level 로 잘게 쪼개 dense 하게 만든 변형이다. 그래서 RL 코드 위에 얹기가 자연스럽고, 동일한 importance-sampling policy gradient 인프라를 그대로 재활용할 수 있다. 뒤에서 pseudocode 를 보면 이 시너지가 한 줄 변경 수준의 의미를 가진다는 게 분명해진다.

## Compute 측면 장점

손실의 수학적 성질이 좋다는 것만으로는 부족하다. 실제로 학습 비용 측면에서도 reverse KL 기반 on-policy distillation 은 RL 대비 여러 면에서 유리하다.

| 항목 | 의미 |
|---|---|
| 짧거나 partial 한 rollout 가능 | reward 계산이 trajectory 종료에 의존하지 않는다. 매 토큰마다 reverse KL 이 즉시 계산되므로 sampling 을 끝까지 굴리지 않아도 학습 신호가 나온다. RL 처럼 evaluation context 길이만큼 길게 뽑을 필요가 없다. |
| Teacher 는 forward pass 1 회 | 교사 모델은 학생 trajectory 위에서 logprob 만 계산하면 끝이다. 별도의 sampling 도, gradient 도 필요 없다. trajectory 생성이라는 비싼 작업은 작은 학생이 담당한다. |
| 별도 reward / labeling 모델 불필요 | dense reward 가 필요한 RL 은 보통 reward model 학습/유지 비용이 따라붙는데, on-policy distillation 은 교사 모델 자체가 reward 다. 학생의 logprob 도 RL 이 importance sampling 을 위해 이미 계산하던 양이라 추가 비용이 없다. |

요약하자면 학습 한 스텝에 들어가는 추가 compute 는 거의 "교사 모델로 학생 trajectory 위에서 forward pass 한 번" 으로 한정된다. 게다가 이 forward pass 는 trajectory 생성과 무관하게 GPU 에 잘 병렬화된다. 다음 편에서 다룰 수학 추론 실험에서 RL 대비 약 1/10 의 비용으로 동등하거나 더 나은 성능을 내는 이유의 절반은 이 구조적 단순함에서 온다.

## SimpleBench 예시 — 어디에 페널티가 붙는가

원문은 [SimpleBench](https://simple-bench.com/) 의 한 문항을 예시로 든다. 문제는 표면적으로는 산수처럼 보이지만, 핵심은 "프라이팬 위에 올린 얼음 큐브는 녹는다" 라는 물리 상식이다. 정답은 "B. 0".

학생인 Qwen3-4B-Instruct-2507 은 이 문제를 순수 산술 문제로 다루어 얼음 큐브 개수를 그대로 더해 잘못된 답을 내놓는다. 교사인 Qwen3-235B-A22B-Instruct-2507 은 같은 문제를 정확하게 푼다. 학생 trajectory 의 각 토큰에 reverse KL 을 적용해 보면 흥미로운 패턴이 보인다.

- **큰 페널티가 붙는 토큰** — "수학 문제로만 풀자" 류의 추론을 시작하게 만든 분기점에 해당하는 토큰들. 학생이 잘못된 풀이 경로로 빠지도록 결정짓는 자리다. 원문에서는 이를 "forking token" 이라고 부르며, [Wang et al, 2025 의 high-entropy minority token 이론 (Beyond the 80/20 Rule)](https://arxiv.org/abs/2506.01939) 에서 말하는, 추론을 가르는 소수의 결정적 토큰과 잘 맞아떨어진다고 지적한다.
- **작은 페널티가 붙는 토큰** — 최종 답 자체. 일단 잘못된 풀이 경로에 올라타고 나면, 그 prefix 조건에서 학생이 도달하는 결론은 사실상 결정되어 있다. 교사가 보기에도 이 prefix 다음에 그 답이 나오는 것이 자연스럽고, 따라서 KL 이 크지 않다.

이 관찰의 함의는 분명하다. on-policy distillation 은 "결과가 틀렸으니 결과 토큰을 미세하게 미는" 식이 아니다. 결과를 결정짓는 forking token, 즉 정보량이 큰 분기점을 자동으로 찾아내 거기에 학습 신호를 몰아준다. RL 의 sparse reward 가 trajectory 전체에 한 번 들어오는 것과 비교하면, 같은 양의 정보를 trajectory 의 옳은 자리에 정확히 배분한다고 말할 수 있다.

## Pseudocode — RL 위에 한 줄 변경

원문은 이 알고리즘이 Tinker 의 RL 학습 스크립트 위에 사실상 한 줄을 더 얹는 정도로 구현된다는 점을 강조한다. KL regularization 을 쓰는 RL 구현에서는 정말로 한 줄 — regularizer 모델을 바꾸는 것 — 으로 끝난다. 핵심 코드는 다음과 같다.

```python
# Initialize teacher client
teacher_client = service_client.create_sampling_client(
    base_model=teacher_config.base_model,
    model_path=teacher_config.load_checkpoint_path,
)

# Sample trajectories
trajectories = do_group_rollout(student_client, env_group_builder)
sampled_logprobs = trajectories.loss_fn_inputs["logprobs"]

# Compute reverse-KL reward
teacher_logprobs = teacher_client.compute_logprobs(trajectories)
reverse_kl = sampled_logprobs - teacher_logprobs
trajectories["advantages"] = -reverse_kl

# Train with RL importance-sampling loss
training_client.forward_backward(trajectories, loss_fn="importance_sampling")
```

각 블록의 의미를 짧게 짚는다.

- **Teacher client 초기화** — Tinker API 는 서로 다른 모델에 대해 별도의 client 를 띄울 수 있다. 교사는 sampling client 로 만들면 충분하다. 학생을 학습할 때 교사의 logprob 만 쓰지 교사 쪽으로 gradient 를 흘리지 않기 때문이다.
- **Trajectory 샘플링** — `do_group_rollout` 은 평소의 RL 처럼 학생으로부터 rollout 묶음을 뽑는다. 이 단계에서 학생의 토큰별 logprob $\log \pi_\theta(x)$ 도 함께 기록된다. RL 이 importance-sampling loss 를 위해 이미 계산하던 양이라 추가 비용이 없다.
- **Reverse-KL 보상 계산** — 같은 학생 trajectory 를 교사 client 의 `compute_logprobs` 에 넣어 $\log \pi_{\mathrm{teacher}}(x)$ 를 얻는다. 두 logprob 의 차를 토큰별로 빼면 그것이 곧 학생이 만든 토큰의 reverse KL 이다. 그 음수를 advantage 로 trajectory 에 꽂는다. 이 단계가 이번 알고리즘의 전부라고 봐도 무방하다.
- **RL 손실로 학습** — `forward_backward` 에 `loss_fn="importance_sampling"` 을 그대로 넘긴다. RL 에서 쓰던 손실 함수와 동일하다. 바뀐 것은 advantage 가 환경 보상이 아니라 token-level reverse KL 이라는 점뿐이다.

원문은 또 한 가지 단순화도 명시한다. 이번 작업에서는 logit (top-k) distillation 은 고려하지 않는다. 학생이 실제로 샘플한 토큰의 logprob 만 교사로부터 받아 비교한다. logit distillation 을 도입하면 compute efficiency 를 더 끌어올릴 여지가 있지만, 알고리즘 본체를 단순하게 유지하려고 일부러 빼둔 선택이다.

## 정리 — 알고리즘은 이게 전부다

이 편에서 본 내용을 한 줄로 압축하면, **on-policy distillation 은 학생이 만든 trajectory 의 매 토큰에 대해 reverse KL $\mathrm{KL}(\pi_\theta \,\Vert\, \pi_{\mathrm{teacher}})$ 을 advantage 의 음수로 쓰는 importance-sampling policy gradient 학습**이다. 손실의 mode-seeking, unhackable, exposure-bias 감소, RL 과의 시너지라는 네 가지 성질이 학습 안정성과 신호 품질을 보장하고, 교사 forward pass 한 번 외에 추가 비용이 거의 없다는 점이 RL 대비 비용 우위를 보장한다. Tinker 위에서의 구현은 RL 스크립트의 advantage 한 줄을 reverse KL 로 갈아끼우는 수준이다.

남은 질문은 단 하나다. 이 단순한 레시피가 실제 벤치마크에서 얼마나 잘 작동하는가. 다음 편에서는 이 알고리즘을 Qwen3-8B-Base 위에 그대로 적용해 AIME'24 74.4% 를 RL 대비 1/10 의 compute 로 도달하는 수학 추론 실험을 본다.

다음 편: [수학 추론 사후학습 — AIME'24 74.4% 를 RL 의 1/10 비용으로](03-math-reasoning-experiments.md)

## 출처

- https://thinkingmachines.ai/blog/on-policy-distillation/
