---
title: RL climb을 오래 지속시키는 recipe
date: 2026-06-10
author: 김세형
tags: [mai-thinking-1, reinforcement-learning, grpo, self-distillation, reasoning-model]
source: https://microsoft.ai/pdf/mai-thinking-1.pdf
summary: MAI-Thinking-1의 RL은 GRPO 계열 objective, entropy 제어, top-p mask replay, length curriculum, self-distillation으로 수천 step의 성능 상승을 유지한다.
format: details
part: 3
---

# RL climb을 오래 지속시키는 recipe

> 원본: [Microsoft AI technical report](https://microsoft.ai/pdf/mai-thinking-1.pdf)

앞 편까지의 이야기는 "reasoning RL을 시작할 수 있는 base를 어떻게 만든다"에 가까웠다. 이번 편은 그 다음 단계, 즉 이미 mid-training까지 끝난 MAI-Base-1을 어떻게 긴 RL climb으로 밀어 올리는지를 다룬다. Microsoft가 강조하는 지점은 단순히 GRPO를 썼다는 사실이 아니라, 수천 step 동안 성능이 무너지지 않게 만드는 작은 장치들의 조합이다.

3.1 절의 recipe는 세 specialist climb에 공통으로 쓰인다. STEM, agentic coding/tool-use, helpfulness/safety는 프롬프트 분포와 reward의 task-specific 부분이 다르지만, policy objective, entropy 제어, reward decomposition, sampling, length curriculum, self-distillation의 기본 구조는 공유한다. 그래서 이 절은 MAI-Thinking-1의 후반부 성능을 만든 "공통 엔진"에 해당한다.

## 출발점: response 단위 보상, token 단위 업데이트

RL climb은 policy $\pi_\theta$에서 시작한다. 프롬프트 $q$가 주어지면 rollout policy가 $G$개의 응답 $y_{1:G}$를 샘플링하고, 각 응답 $y_i$는 스칼라 보상 $R(q, y_i)$를 받는다. 이 보상은 domain마다 다르다. 코드 문제라면 실행 결과가 들어갈 수 있고, 선호·안전 영역에서는 prompted AI judge나 reward model이 들어갈 수 있다.

학습 objective는 GRPO 계열이다. 핵심은 한 프롬프트에서 나온 응답 그룹 안에서 상대적으로 좋은 응답과 나쁜 응답을 비교한다는 점이다. 응답 $y_i$의 advantage $A_i$는 그 응답의 reward에서 그룹 평균을 빼고 그룹 표준편차로 나눈 값이며, 이 response-level advantage가 해당 응답의 모든 token에 공유된다.

token $t$에서의 policy ratio는 다음처럼 생각하면 된다.

$$
r_{i,t}(\theta) =
\pi_\theta(y_{i,t} \mid q, y_{i,<t}) /
\pi_{\text{old}}(y_{i,t} \mid q, y_{i,<t})
$$

여기서 $\pi_{\text{old}}$는 rollout을 생성한 policy다. objective는 PPO류와 마찬가지로 $r_{i,t}(\theta) A_i$와 clipped ratio를 쓴 항 중 보수적인 쪽을 택한다. 논문은 normalization을 global training batch의 모든 token에 대해 계산한다고 설명한다. 이렇게 하면 응답 길이가 다르더라도 token 하나하나가 같은 무게로 들어간다.

## GRPO 위에 얹은 두 가지 안정화 장치

Microsoft는 기본 GRPO objective에 두 가지 수정을 더한다. 하나는 policy entropy를 목표 근처에 유지하기 위한 adaptive entropy control이고, 다른 하나는 catastrophic gradient-norm spike를 막기 위한 outer ratio clip이다. 둘 다 목적은 같다. "좋은 방향으로 크게 움직이자"와 "한 번에 너무 멀리 가지 말자" 사이의 경계를 자동으로 다듬는 것이다.

### Adaptive entropy control

첫 번째 수정은 clipping 상한을 고정하지 않는 것이다. lower bound는 $1 - \epsilon$로 두고, upper bound는 $(1 - \epsilon)^{-1} + k$처럼 $k$에 따라 넓어지거나 좁아진다. $k$는 현재 policy entropy가 target entropy $H^\star$보다 낮은지 높은지에 따라 매 step 업데이트된다.

직관은 간단하다.

- entropy가 너무 낮으면 $k$를 키워 상한을 넓힌다. 그러면 policy가 대안 token의 확률을 더 적극적으로 올릴 여지가 생긴다.
- entropy가 충분히 높으면 $k$를 줄여 trust region을 조인다. 그러면 distribution이 과도하게 퍼지는 방향을 막는다.
- $k$는 $0$과 $k_{\max}$ 사이로 clip된다. 논문은 이 방식이 explicit entropy bonus보다 잘 작동했다고 보고한다.

이 장치는 entropy collapse와 entropy explosion을 동시에 피하려는 타협이다. upper clip bound가 너무 낮으면 policy가 빨리 굳고, 너무 높으면 확률 질량이 불안정하게 퍼질 수 있다. MAI-Thinking-1 recipe는 이 경계를 수동 튜닝값 하나로 고정하지 않고, 관측 entropy에 따라 online으로 조정한다.

### Outer ratio clip

두 번째 수정은 모든 branch에 적용되는 hard outer clip이다. 표준 PPO/GRPO objective에는 일부 unclipped case가 남아 있다. 예를 들어 advantage가 음수인데 새 policy가 old policy보다 해당 token 확률을 높였거나, advantage가 양수인데 확률을 낮춘 경우다. 원래 의도는 policy가 스스로 잘못을 고치는 방향으로 움직일 때는 제한을 덜 걸겠다는 것이다.

하지만 논문은 이 unclipped branch가 때때로 catastrophic gradient-norm spike를 만들었다고 말한다. 그래서 모든 branch에 대해 $r_{i,t}(\theta)$를 바깥 범위로 한 번 더 clip한다. 일반적인 trust-region 안에서는 기존 clipped objective를 유지하되, old policy와 new policy의 확률 차이가 극단적으로 벌어지는 경우는 잘라낸다.

이 수정은 보수적이다. 학습 신호를 더 세게 만드는 장치가 아니라, 드문 폭주 사례를 버리는 장치다. Microsoft는 이 two-level strategy가 gradient spike를 줄이고 climb을 더 안정적으로 만들었다고 정리한다.

## Reward는 task reward 하나로 끝나지 않는다

reward는 세 specialist climb마다 task-specific 성분이 다르지만, 공통 decomposition은 동일하다.

$$
R(q, y_i) =
R_{\text{task}}(q, y_i)
+ w_{\text{lang}} R_{\text{lang}}(y_i)
- w_{\text{len}} R_{\text{len}}(y_i)
$$

$R_{\text{task}}$는 문제 자체의 성공 여부나 judge 점수다. 여기에 language consistency reward와 length penalty를 더해, 긴 reasoning trace에서 자주 생기는 두 가지 문제를 눌러 준다.

### Language consistency reward

긴 context와 긴 CoT로 RL을 진행하면, 모델이 CoT 안에 foreign-language token을 섞기 시작하는 현상이 관찰된다. 논문은 이런 mixed-language CoT가 training policy와 inference policy 사이의 log-probability divergence spike와 연관되어 있고, 결과적으로 학습 안정성을 해친다고 설명한다.

대응은 영어 기준 language consistency reward다. 훈련 분포에서 영어가 지배적이기 때문에, CoT 안의 non-English word 수를 세고 per-word penalty $\alpha$를 적용한다. 단일 저확률 foreign-language token이 문제를 일으키는 경우에는 top-p sampling도 비슷한 방지 효과를 냈다고 덧붙인다.

### Length penalty

reasoning model의 RL에서는 길이가 양면성을 갖는다. 어려운 문제에서는 긴 탐색이 필요하지만, 쉬운 문제에서 긴 CoT는 반복, hedging, 불필요한 비용이 될 수 있다. 그래서 논문은 문제별 pass rate $\rho_q$와 응답 길이 $|y_i|$, 최대 rollout 길이 $\ell_{\max}$를 함께 쓰는 length penalty를 둔다.

$$
R_{\text{len}}(y_i) = \rho_q \cdot |y_i| / \ell_{\max}
$$

쉽게 풀리는 문제는 $\rho_q$가 높으므로 긴 답변에 더 큰 penalty를 받는다. 반대로 어려운 문제는 $\rho_q$가 낮아 penalty가 약해지고, 모델이 더 긴 reasoning trace를 탐색할 여지가 생긴다. 이 설계는 "무조건 짧게"가 아니라 "쉬운 문제에서는 간결하게, 어려운 문제에서는 더 생각하게"에 가깝다.

## 문제를 고르는 방법: pass-rate filter와 early exit

GRPO의 그룹 상대 비교는 그룹 안에 variance가 있어야 의미가 있다. 모든 rollout이 맞거나 모두 틀리면, 어떤 응답을 밀어 올리고 어떤 응답을 낮출지에 대한 신호가 약하다. MAI-Thinking-1 recipe는 이 점을 sampling 단계에서 처리한다.

문제 $q$를 받으면 먼저 전체 $G$개를 생성하지 않고, 작은 수의 early rollout $G_{\text{early}}$만 생성한다. 이 early pass rate가 허용 구간 안에 들어오면 full rollout으로 넘어가고, 아니면 문제를 버린다. full $G$개 응답을 만든 뒤에도 다시 pass-rate filter를 적용한다.

이 구조의 의미는 두 가지다.

- **비용 절감**: 너무 쉽거나 너무 어려운 문제는 full rollout을 만들기 전에 버릴 수 있다.
- **학습 신호 품질 관리**: 최종 그룹에서도 pass rate가 너무 낮거나 높으면 상대 advantage의 정보량이 작으므로 학습에 쓰지 않는다.

논문이 보고한 값은 $G = 128$, $G_{\text{early}} = 16$이다. early filter 구간은 $[0.05, 0.8]$, full pass-rate filter 구간은 $[0.1, 0.8]$이다. 즉 거의 전부 실패하거나 거의 전부 성공하는 문제를 의도적으로 제외한다.

## Top-p mask replay: rollout과 learner의 분포를 맞춘다

rollout은 $\pi_{\text{old}}$에서 top-p sampling으로 만든다. 논문에서 중요한 대목은 sampling만 top-p로 하는 것이 아니라, rollout 때 쓰인 top-p truncation mask를 training 때 replay한다는 점이다. rollout 당시 nucleus 밖에 있었던 token들의 logit은 learner softmax 계산 전에 $-\infty$로 설정된다.

이 장치가 필요한 이유는 off-policy mismatch 때문이다. 생성할 때는 nucleus 밖 token을 제외했는데, 학습할 때는 그 token들의 logit까지 backpropagation에 포함하면 learner가 rollout 분포와 다른 support 위에서 업데이트된다. 논문은 이 mismatch가 몇 step 안에 divergence를 만들 수 있었다고 설명한다.

top-p mask replay는 안정성을 얻는 대신 비용을 낸다. 각 rollout에 대해 mask를 저장하고 learner 쪽으로 전달해야 하기 때문이다. Microsoft는 $p = 0.97$을 사용했고, 더 큰 nucleus는 exploration을 늘리지만 mask transfer overhead도 키운다고 설명한다. 이 값은 exploration과 training efficiency 사이의 실용적 균형점으로 제시된다.

## Length curriculum: 처음부터 128k를 쓰지 않는다

MAI-Thinking-1은 최종적으로 128k token 출력 길이까지 RL을 진행하지만, 처음부터 그 길이로 시작하지 않는다. 초기 climb에서는 최대 rollout 길이를 8k로 제한하고, 학습이 진행되면서 16k, 32k, 64k, 128k처럼 powers of two로 늘린다.

이 curriculum은 단순한 compute 절약을 넘는다. 낮은 성능 구간에서는 긴 reasoning trace가 실제로 필요한 경우가 적고, 긴 rollout은 inference 비용과 stale rollout 문제를 키운다. 모델이 어느 정도 문제를 풀 수 있게 된 뒤 더 긴 token budget을 열어 주면, 긴 context 적응과 비용 통제를 함께 가져갈 수 있다.

논문은 asynchronous RL stack에서 generation length가 길어질수록 rollout latency가 늘고, 특히 어려운 문제의 rollout이 더 stale해진다고 설명한다. 그래서 높은 length 단계에서는 learning rate를 낮춰 off-policiness와 안정성 문제를 완화한다. length curriculum은 reward shaping만큼이나 system-level recipe에 가깝다.

## Self-distillation은 성능을 베끼는 것이 아니라 climb을 이어 붙이는 도구다

이 절에서 self-distillation은 외부 teacher를 모방하는 의미가 아니다. RL 도중 생성된 rollout을 모아 mid-trained checkpoint에 SFT를 수행하고, 그 결과 모델을 다음 RL climb의 출발점으로 쓰는 방식이다. 즉 이전 climb에서 발견한 능력을 보존하면서 policy를 다시 다루기 쉬운 위치로 되돌리는 reset 장치에 가깝다.

논문이 제시한 용도는 네 가지다.

| 용도 | 설명 |
|---|---|
| Prompt format 전환 | 초기에는 task-specific prompt로 target behavior를 elicitation하고, self-distillation을 통해 native chat format SFT 데이터로 옮긴다. |
| Run failure 회복 | numerical mismatch나 instability로 climb이 무너졌을 때, collapse 이전 checkpoint로 단순 rollback하는 대신 좋은 rollout을 SFT로 carry over한다. |
| Base policy 교체 | 새 pre-trained 또는 mid-trained checkpoint가 나오면 이전 climb의 progress를 새 base로 옮긴다. |
| Reward hacking filter | self-distillation 데이터 구성 단계에서 바람직하지 않은 reward hacking sample을 거를 수 있다. |

중요한 점은 self-distillation이 RL을 대체하지 않는다는 것이다. SFT는 이미 발견한 trace distribution을 policy에 주입하지만, 이후 다시 RL을 이어가며 exploration과 reward optimization을 계속한다. Microsoft가 강조하는 practical value는 긴 climb을 한 번의 완벽한 run으로 끝내려 하지 않고, 여러 구간을 이어 붙일 수 있게 만든다는 데 있다.

## Self-distillation best practice

논문은 self-distillation을 어떻게 해야 하는지에 대해 여러 ablation 결과를 요약한다. 여기서 특히 실무적인 메시지는 "많을수록 좋다"가 아니라 "너무 policy를 좁히면 다음 RL이 힘들어진다"이다.

- 약 $O(1\text{M})$개의 reasoning trace면 teacher performance를 맞추면서 SFT의 안정성 이점을 얻기에 충분하다. 훨씬 큰 데이터셋은 diminishing return이 있고, policy output distribution을 과도하게 좁혀 RL 재개 후 exploration 여지를 줄일 수 있다.
- 틀린 최종 답을 낸 trace까지 포함해도 successful trace만 쓴 경우와 비슷한 성능을 보였다. 다만 실제 RL run에서는 successful trace가 충분히 많았기 때문에 최종적으로는 successful trace로 제한했다.
- 너무 이른 checkpoint의 trace를 넣으면 성능이 떨어지고 회복에 많은 RL step이 필요하다. 반대로 마지막 checkpoint 하나에서만 trace를 뽑는 것도 약하다. strong checkpoint 여러 개에서 수집한 trace가 diversity를 제공하기 때문이다.
- 같은 token budget이라면 prompt당 trace 수를 늘리는 것보다 prompt diversity를 늘리는 편이 더 중요했다. simple random sampling이 shortest-trace sampling이나 heuristic filtering보다 나았다.
- 짧은 maximum length에서 수집한 reasoning trace만으로 SFT하면 mid-training에서 배운 long-context behavior를 잊을 수 있다. length extension 전 self-distillation에는 mid-training data를 reasoning trace와 섞어 이 문제를 완화한다.

이 best practice는 MAI-Thinking-1의 철학과 맞물린다. self-distillation은 "완성된 teacher를 압축"하는 단계가 아니라, 다음 climb을 잘 시작하기 위한 policy conditioning 단계다. 그래서 trace 품질뿐 아니라 diversity, entropy, long-context retention이 모두 중요하다.

## 주요 hyperparameter

논문은 main RL climb과 self-distillation SFT에 사용한 대표 hyperparameter를 공개한다. 모든 domain-specific climb이 완전히 같은 분포에서 돌아간 것은 아니지만, recipe의 중심값을 이해하는 데 충분하다.

| 항목 | 값 |
|---|---|
| RL optimizer | AdamW, $\beta_1 = \beta_2 = 0.95$, optimizer $\epsilon = 10^{-15}$, weight decay 없음 |
| RL learning rate | 기본 $10^{-6}$, 긴 length 단계에서 $9 \times 10^{-7}$ |
| RL batch | packed global batch 7040, unpacked sequence 최대 12000 |
| Max generation length | 8k -> 16k -> 32k -> 64k -> 128k |
| Adaptive GRPO | $\epsilon = 0.6$, $k_{\max} = 2.5$, step size $\delta = 0.25$, $H^\star = 0.3$ |
| Outer clip | $r_{\max} = 50$, lower side는 사실상 unconstrained |
| Language reward | $w_{\text{lang}} = 0.5$, $\alpha = 0.005$ |
| Length penalty | 64k 단계까지 $w_{\text{len}} = 0.25$, 128k 단계에서는 $w_{\text{len}} = 0$ |
| Problem sampling | $G = 128$, $G_{\text{early}} = 16$, early filter $[0.05, 0.8]$, full filter $[0.1, 0.8]$ |
| Top-p | $p = 0.97$ |
| Policy freshness | inference model update 사이 5 gradient steps, 8 inference update보다 stale한 rollout 폐기 |
| RL MoE balancing | dropless MoE, load balancing coefficient $10^{-5}$ |

self-distillation SFT 쪽은 128k sequence length와 packed global batch 2048을 쓴다. optimizer는 AdamW, weight decay는 0.001, cosine learning rate schedule이다. maximum learning rate는 $1.7 \times 10^{-5}$, minimum learning rate는 $5.2 \times 10^{-6}$, warmup ratio는 2%다.

특히 눈에 띄는 값은 dropout과 MoE load balancing coefficient다. self-distillation에서는 dropout 0.15를 사용해 entropy를 높이고 collapse를 방지한다. 또한 RL 중에는 큰 load balancing coefficient가 안정적인 성능 향상을 해칠 수 있어 $10^{-5}$를 쓰지만, self-distillation에서는 $10^{-2}$를 사용해 expert imbalance를 더 강하게 바로잡는다.

## 이 recipe가 지키려는 것

3.1 절의 요소들은 따로 보면 작은 engineering choice처럼 보인다. 하지만 함께 놓고 보면 하나의 일관된 목표가 보인다. 긴 RL climb에서 성능을 계속 올리려면 reward만 세게 주는 것으로는 부족하고, policy entropy, response length, rollout support, problem difficulty, rollout freshness, MoE balance를 동시에 관리해야 한다.

MAI-Thinking-1의 recipe는 reasoning model을 만드는 과정을 "한 번의 post-training run"으로 보지 않는다. pass-rate filter로 쓸모 있는 문제를 고르고, top-p mask replay로 rollout과 learner의 support를 맞추고, length curriculum으로 budget을 늘리고, self-distillation으로 climb 구간을 이어 붙인다. 이 조합이 논문 전체 제목의 hill-climbing machine에서 RL 쪽을 담당하는 핵심 부품이다.

다음 편: [세 specialist climb은 어떻게 하나의 모델로 합쳐졌나](04-three-specialist-climbs.md)

## 출처

- https://microsoft.ai/pdf/mai-thinking-1.pdf
