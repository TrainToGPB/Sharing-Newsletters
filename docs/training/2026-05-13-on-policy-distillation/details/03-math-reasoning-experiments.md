---
title: 수학 추론 사후학습 — AIME'24 74.4% 를 RL 의 1/10 비용으로
date: 2026-05-13
author: TrainToGPB
tags: [사후학습, 증류, RL, AIME, Qwen3]
source: https://thinkingmachines.ai/blog/on-policy-distillation/
summary: Qwen3-8B-Base 학생 + Qwen3-32B 교사 셋업에서 AIME'24 60% → 70% 가 약 150 step·77K prompt 만에 도달하고, 같은 결과를 RL 대비 9~30배 적은 FLOPs 로 얻는다. Qwen3 보고서의 74.4% 도 재현된다.
format: details
part: 3
---

# 수학 추론 사후학습 — AIME'24 74.4% 를 RL 의 1/10 비용으로

> 원본: [thinkingmachines.ai/blog/on-policy-distillation](https://thinkingmachines.ai/blog/on-policy-distillation/)

앞 편까지의 논의는 알고리즘 자체에 머물러 있었다. reverse KL 을 token 단위 advantage 로 쓰면 RL 의 on-policy 성질과 SFT 의 dense reward 를 동시에 얻을 수 있다는 이야기였다. 이제 그 이야기가 실제 사후학습 비용표 위에서 어떤 차이로 환산되는지를 본다. 이 편은 Thinking Machines 의 reasoning 실험을 그대로 따라가며, 결국 한 가지 질문에 답한다. 같은 출발점에서 AIME'24 점수를 60% 에서 70% 까지 끌어올린다고 할 때, off-policy SFT, RL, on-policy distillation 은 각각 얼마나 다른 청구서를 내는가.

## 셋업: 재현 가능한 비교의 조건

저자들은 학생으로 Qwen3-8B-Base 를, 교사로 Qwen3-32B 를 사용한다. 둘 다 Tinker 가 지원하는 모델이라는 점이 중요하다. 즉 Tinker cookbook 의 distillation 레시피로 누구나 같은 셋업을 재현할 수 있도록 일부러 공개 모델 두 개를 골랐다는 뜻이다. 평가 벤치마크는 AIME'24, 보조 지표는 GPQA-Diamond 이고, 모든 학습은 mid-training 단계의 off-policy distillation 으로 출발한다.

여기서 mid-training 이라는 표현은 단순한 호칭이 아니라 비교의 출발점을 명확히 한다는 신호다. 어떤 사후학습 방법도 무에서 시작하지 않으며, 모두 동일한 SFT 초기화 위에 얹는다. 그래야 "다음 10 점을 어떻게 더 얻을 것인가" 라는 질문이 의미를 갖는다.

## Off-policy 베이스라인: 60% 까지는 싸고, 그 다음이 비싸다

수학 reasoning 의 mid-training 데이터셋은 OpenThoughts-3 다. QwQ-32B (Qwen3-32B 와 유사한 reasoning 모델) 가 생성한 1.2M 개의 reasoning trajectory 로 구성되어 있다. 학생 Qwen3-8B-Base 를 이 중 400k prompt 로 full fine-tune 하면 AIME'24 60% 가 나온다. 같은 데이터로 LoRA 를 돌리면 점수가 떨어진다. 이는 [LoRA Without Regret](https://thinkingmachines.ai/blog/lora/) 에서 이미 보고된 현상으로, 대규모 SFT 처럼 큰 batch size 로 학습할 때 LoRA 의 표현력이 부족해지는 구간이다.

여기서 60% 라는 숫자는 함정이 있다. 성능 곡선이 prompt 수에 대해 log-linear 라는 점이다. 곡선 모양 자체는 익숙하지만, 사후학습 비용 관점에서 이 함의는 가혹하다. 0 에서 60% 까지의 gain 은 상대적으로 적은 prompt 로 얻을 수 있지만, 60% 에서 70% 로 가는 마지막 10 점에는 그 앞의 60 점에 들어간 것과 비슷한 양의 데이터·연산이 필요해진다는 뜻이다.

논문 본문은 이 곡선을 외삽해 다음 추정치를 내놓는다. 400k prompt 에서 60% 인 Qwen3-8B-Base 가 같은 OpenThoughts-3 분포에서 70% 에 도달하려면 약 2M prompt 의 SFT 가 필요하다. 외삽은 외삽일 뿐이지만, 비교군으로서는 충분히 보수적인 기준이다. 실제로 8B 급 모델이 SFT 만으로 70% 이상을 찍은 사례 (OpenThoughts-3, DeepSeek-R1-0528-Qwen3-8B 등) 도 존재하므로 이 외삽이 비현실적으로 큰 수치는 아니다.

요점은 이렇다. SFT 만으로 70% 를 노리는 길은 가능하지만 prompt 비용이 5 배 정도로 불어난다. 그리고 그 prompt 들은 그냥 굴러다니는 게 아니다. QwQ-32B 같은 강한 reasoning 모델이 생성한, 손이 많이 가는 trajectory 다.

## RL 베이스라인: 같은 70% 를 17,920 GPU hour 로

Qwen3 technical report 는 같은 출발점에 RL 을 얹어 AIME'24 67.6%, GPQA-Diamond 61.3% 를 보고한다. 비용은 17,920 GPU hours. 이 숫자는 SFT 2M prompt 와 직접 비교가 까다롭지만, SFT stack 의 보편적인 가정 (sequence 길이, batch size, sampling 비용 등) 을 적용하면 2M prompt SFT 와 대체로 비슷한 자릿수라는 게 저자들의 평가다.

다시 말해 60% → 68% 의 RL 은 60% → 70% 의 대규모 SFT 와 거의 같은 비용 구간에 위치한다. 비교가 좋게 그려질 때조차 RL 은 SFT 의 압도적인 절감을 제공하지 못한다. 이게 사후학습 시장에서 RL 이 "값비싼 마무리 단계" 의 인상을 갖는 이유다.

## On-policy distillation: 150 step, 77K prompt 로 70%

이제 본론이다. 같은 SFT-400K checkpoint 에서 시작해, teacher 의 token-level log-prob 으로 reverse KL 을 reward 로 쓰는 on-policy distillation 을 돌린다. 본 실험에서는 실제 teacher 로 Qwen3-8B 를 사용했다 (약간 더 잘 동작하기 때문이다). 다만 FLOPs 비교는 보수적으로 Qwen3-32B 기준으로 한다. 즉 비용표는 32B 짜리 teacher 를 가정한 상한치다.

이 셋업에서 약 150 step 만에 AIME'24 70% 에 도달한다. 150 step 은 prompt 당 4 sample 기준 약 77K prompt 다. 1.2M, 2M 같은 자릿수 옆에 놓고 보면 77K 는 0 에 가깝게 보이는 숫자다. 같은 시리즈를 더 밀어붙이면 Qwen3 팀이 보고한 AIME'24 74.4%, GPQA-Diamond 63.3% 가 1,800 GPU hour 안에 재현된다. 같은 점수대를 RL 이 17,920 GPU hour 로 만든다는 사실과 나란히 놓으면 비용비는 정확히 $10\times$ 다.

벤치마크 점수만 한 표로 정리하면 다음과 같다.

| Method | AIME'24 | GPQA-Diamond | GPU Hours |
|---|---|---|---|
| Off-policy distillation | 55.0% | 55.6% | Unreported |
| + Reinforcement learning | 67.6% | 61.3% | 17,920 |
| + On-policy distillation | 74.4% | 63.3% | 1,800 |

이 표가 흥미로운 점은 두 가지다. 첫째, on-policy distillation 은 RL 보다 점수 자체가 더 높다. 즉 "더 싼 대신 약간 나쁜" 절충이 아니다. 같거나 더 좋은 점수를 더 싸게 낸다. 둘째, GPQA-Diamond 처럼 학습 분포 밖의 일반 reasoning 벤치마크에서도 점수가 함께 올라간다는 점이다. 점수 상승이 AIME 스타일의 좁은 패턴 매칭이 아니라 더 폭넓은 reasoning 표현으로 전이된다는 신호로 읽을 수 있다.

## FLOPs 로 환산한 compute efficiency

GPU hour 는 implementation 에 따라 들쭉날쭉하다. 더 공정한 비교를 위해 저자들은 FLOPs 단위로 다시 정리한다. 이 척도는 GPU 위에서 잘 병렬화되는 연산 (예: teacher log-prob) 에 페널티를 주는 셈이지만, 그렇기 때문에 on-policy distillation 입장에서는 보수적인 척도가 된다.

| Method | AIME'24 | Teacher FLOPs | Student FLOPs | CE vs SFT-2M |
|---|---|---|---|---|
| SFT-400K (init) | 60% | $8.5 \times 10^{20}$ | $3.8 \times 10^{20}$ | – |
| SFT-2M (extrapolated) | ~70% | $3.4 \times 10^{21}$ | $1.5 \times 10^{21}$ | $1\times$ |
| RL | 68% | – | – | $\approx 1\times$ |
| On-policy distillation | 70% | $8.4 \times 10^{19}$ | $8.2 \times 10^{19}$ | $9\sim30\times$ |

숫자 자체보다 자릿수의 차이가 핵심이다. on-policy distillation 의 student FLOPs 는 $8.2 \times 10^{19}$, teacher FLOPs 는 $8.4 \times 10^{19}$. 같은 70% 를 SFT 로 만들려면 student 만 따져도 $1.5 \times 10^{21}$, teacher 까지 합하면 $3.4 \times 10^{21}$ + $1.5 \times 10^{21}$ = $4.9 \times 10^{21}$ 이다. on-policy distillation 의 총합은 $1.7 \times 10^{20}$ 으로, 자릿수로 한 단계 적다.

여기서 CE (compute efficiency) 의 정의를 둘로 나눠 보는 게 중요하다.

첫째, SFT 데이터셋이 이미 존재하는 시나리오. OpenThoughts-3 같은 공개 데이터셋이 있거나, 여러 학습 실험에 걸쳐 비용이 분산된 경우다. 이때는 off-policy 쪽 teacher FLOPs 를 0 으로 친다 (이미 누군가가 지불했다). 반면 on-policy distillation 쪽은 매 step 마다 teacher 를 굴려야 하므로 teacher FLOPs 가 살아 있다. 이 정의로 CE 를 계산하면

$$\text{CE} = \frac{\text{SFT-2M student FLOPs}}{\text{Distill student FLOPs} + \text{Distill teacher FLOPs}}$$

가 되고, 결과는 약 $9\times$ 다. GPU hour 기준으로는 teacher log-prob 연산이 잘 병렬화되기 때문에 차이가 더 벌어져 약 $18\times$ 가 된다.

둘째, SFT 데이터셋을 처음부터 만들어야 하는 시나리오. 새 task 라서 누가 만들어 놓은 reasoning trajectory 가 없는 경우다. 이때는 off-policy 쪽도 teacher 비용을 그대로 지불해야 한다. CE 의 분모와 분자에 모두 student + teacher 가 들어가고

$$\text{CE} = \frac{\text{SFT-2M (student + teacher)}}{\text{Distill (student + teacher)}}$$

비율은 약 $30\times$ 까지 벌어진다.

자, 정리하면 이렇다. 데이터가 공짜로 굴러다니는 운 좋은 상황에서도 $9\times$, 데이터 생성까지 비용에 넣어야 하는 일반적인 상황에서는 $30\times$. 둘 사이의 어느 지점에 실제 사용 시나리오가 놓이느냐가 다르지, 어느 경우든 한 자릿수 이상의 절감이 보장된다.

## 왜 이렇게 싸지는가

비용 절감의 출처를 두 가지로 쪼개 보면 이해가 쉽다.

하나는 token-level dense reward 의 정보량이다. RL 은 episode 당 $O(1)$ bit 의 정보만 학생에게 전달한다. 정답인지 오답인지만 알려주기 때문이다. 반면 token-level reverse KL 은 episode 당 $O(N)$ bit 의 정보를 전달한다. 학생이 만든 $N$ 개 token 각각에 대해 teacher 가 어디서 어떻게 빗나갔는지를 표시해 주는 셈이다. 같은 episode 에서 학생이 받는 supervision 의 양이 token 길이만큼 비례해서 늘어난다. 그 결과 같은 점수를 만드는 데 필요한 sample 수가 자릿수 단위로 줄어든다.

다른 하나는 teacher 의 forward pass 가 RL 의 rollout 보다 싸다는 점이다. teacher 는 학생이 이미 생성한 trajectory 에 대해 log-prob 만 계산하면 된다. autoregressive sampling 처럼 token 마다 KV cache 를 키워가며 한 단계씩 가는 게 아니라, 한 번의 forward pass 로 전체 sequence 의 log-prob 을 얻는다. 이 연산은 GPU 위에서 sequence 차원으로 잘 병렬화된다. 거기에 student 보다 큰 모델이라도 sampling 부담이 없으므로, 전체 wall-clock 비용에서 teacher 가 차지하는 몫은 FLOPs 표가 시사하는 것보다 더 작다. GPU hour 기준 절감비가 FLOPs 기준 절감비보다 두 배 정도 더 큰 ($9\times \to 18\times$) 이유다.

## 전제 조건과 실무 함의

이 결과를 그대로 다른 task 에 옮기기 전에 짚어야 할 조건이 하나 있다. 강한 SFT initialization 이 필요하다는 점이다. 본 실험에서 on-policy distillation 의 출발점은 무작위 weight 가 아니라 OpenThoughts-3 로 mid-train 된 400k SFT checkpoint 였다. 학생이 teacher 분포 근처에 이미 가 있어야 reverse KL gradient 가 의미 있는 방향을 가리킨다. 학생이 teacher 분포에서 너무 멀면, 학생의 trajectory 가 teacher 입장에서 거의 확률 0 인 sequence 가 되고 gradient 가 폭주하거나 무의미해진다.

이는 다음 편에서 다루는 personalization 사례에서 더 분명해진다. 사내 문서 같은 새 도메인 지식은 SFT 로 먼저 심어 학생의 분포에 "지원 (support) 영역" 을 만들어 두어야 하고, 그 위에서 on-policy distillation 이 행동 (instruction following) 을 다듬는 식으로 역할 분담이 일어난다. on-policy distillation 은 모드를 찾는 (mode-seeking) 도구이지, 모드를 새로 만드는 도구가 아니다.

실무적으로 이 편의 결과는 세 가지 결론을 남긴다.

첫째, 사후학습 단계의 "마지막 10 점" 은 더 이상 17,920 GPU hour 짜리 RL 의 영역이 아니다. 같은 점수, 혹은 더 높은 점수를 1,800 GPU hour 로 만들 수 있다. 자체 RL 인프라가 없는 팀에게도 frontier 급 reasoning 성능이 손이 닿는 자리에 놓인다.

둘째, prompt 데이터 비용이 비대해진 팀에게도 이 결과는 유효하다. 77K prompt 로 70% 가 가능하다면, 2M prompt 짜리 SFT 파이프라인을 굳이 운영할 이유가 줄어든다. teacher 호출 비용은 들지만 prompt 수집 비용은 크게 줄어들고, 결과적으로 데이터 효율과 compute 효율을 동시에 얻는다.

셋째, 평가의 함정도 함께 사라진다. 같은 학습 곡선의 끝에서 두 방법을 비교하면 on-policy distillation 이 RL 보다 점수가 낮지 않다. on-policy distillation 은 "RL 의 저렴한 대체재" 가 아니라, 어떤 의미에서는 RL 이 들고 다니던 sparse reward 의 비효율을 제거한 정통 후계자다.

다음 편에서는 같은 알고리즘을 수학이 아닌 personalization 으로 옮긴다. 사내 문서 지식과 instruction following 을 한 모델에 함께 담을 때 어떤 catastrophic forgetting 이 일어나고, on-policy distillation 이 어떻게 그 행동을 재주입하는지를 다룬다.

다음 편: [도메인 지식과 instruction following 을 한 모델에 — 사내 어시스턴트 사례](04-personalization-and-forgetting.md)

## 출처
- https://thinkingmachines.ai/blog/on-policy-distillation/
