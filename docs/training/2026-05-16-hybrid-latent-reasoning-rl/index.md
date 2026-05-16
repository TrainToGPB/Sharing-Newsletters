---
title: 강화학습으로 LLM 의 잠재 추론을 깨우는 HRPO
date: 2026-05-16
author: TrainToGPB
tags: [강화학습, 추론, latent-reasoning, HRPO, GRPO]
source: https://arxiv.org/html/2505.18454v2
summary: 이산 토큰과 hidden state 를 학습 가능한 게이트로 섞고, CoT 트레이스 없이 outcome 보상만으로 잠재 추론을 RL 학습하는 HRPO 가 1.5B·3B Qwen 으로 7B 베이스라인급 성능을 낸다.
format: abstract
---

# 강화학습으로 LLM 의 잠재 추론을 깨우는 HRPO

> 원본: [arxiv.org/abs/2505.18454](https://arxiv.org/html/2505.18454v2)

LLM 의 추론을 토큰 단위 CoT 가 아니라 hidden state 같은 연속 표현으로 시키자는 latent reasoning 흐름은 매력적이지만, 사전학습된 LLM 에 그대로 붙이면 잘 안 된다. HRPO 는 hidden state 를 토큰 임베딩 공간으로 사영해 sampled token embedding 과 학습 가능한 게이트로 섞고, CoT 트레이스 없이 outcome 보상만 있는 강화학습으로 그 게이트를 직접 학습한다. 결과는 단순하다. 1.5B·3B Qwen 백본이 7B 급 모델과 어깨를 나란히 한다.

## 핵심 포인트

- **문제**: 기존 latent reasoning (Coconut, CODI, depth-recurrent 등) 은 CoT 트레이스로 멀티스테이지 학습을 해야 하고, hidden state 를 그대로 다음 입력에 넣으면 embedding manifold 와 어긋나 생성이 무너진다.
- **해법 1 — 입력 만들기**: 출력 분포로 token embedding 의 가중합을 구해 $\tilde{e}_t$ 를 만들고, sampled token embedding $e_t$ 와 $\tilde{e}_t$ 를 학습 가능한 게이트로 섞은 하이브리드 입력 $h_t$ 를 다음 step 입력으로 쓴다.
- **해법 2 — 학습**: GRPO 스타일로 같은 쿼리에서 $G$ 개 rollout 을 만들고, 정답 여부만으로 보상을 매겨 그룹 표준화 어드밴티지 + KL 정규화로 strictly on-policy 학습. CoT 라벨 없음, value model 없음, importance ratio clipping 도 없음.
- **결과**: 1.5B·3B Qwen 백본으로 지식 QA 5개와 STEM 5개 벤치마크에서 PPO·GRPO 를 일관되게 앞섬. 3B HRPO 평균이 STEM 0.700, Knowledge 0.380 — Qwen2.5-7B 와 동급이고 7B RAG 베이스라인보다 +4.5%p.
- **창발 패턴**: CoT 감독 없이도 hybrid 출력의 sampled token 만 디코딩해도 읽힘. 영어·중국어가 섞이는 cross-lingual reasoning, 단순 질문에서 압축된 응답 등 작은 모델에서는 잘 안 보이던 패턴.

## 한 페이지 요약

자기회귀 CoT 는 토큰 하나하나로 추론을 외화한다는 장점이 있지만, 매 step 에서 분포 전체가 하나의 이산 토큰으로 콜랩스한다는 비용을 치른다. latent reasoning 은 그 콜랩스 직전의 hidden state 를 그대로 다음 입력으로 돌려 더 풍부한 표현으로 추론하자는 발상이다. 문제는 사전학습된 LLM 의 입력 임베딩 공간과 출력 hidden state 가 같은 manifold 위에 있지 않다는 점이다. 그대로 피드백하면 반복·incoherence 같은 생성 붕괴가 일어난다. 그래서 기존 방법들은 별도의 CoT 트레이스로 multi-stage 학습을 해서 그 간극을 메워야 했다.

![Hybrid reasoning architecture](assets/fig-2.png)
*Hybrid reasoning (좌) 은 reasoning span 안에서만 게이트로 sampled token 과 projected hidden 을 섞고, HRPO training (우) 은 같은 쿼리에서 여러 hybrid rollout 을 만들어 표준화된 보상으로 어드밴티지를 구한 뒤 KL 정규화된 policy gradient 로 정책과 게이트를 갱신한다.*

HRPO 는 이 간극을 두 단계로 메운다. 먼저 hidden state $h_t$ 를 LM head 의 출력 확률로 token embedding 들의 가중합으로 사영해 $\tilde{e}_t$ 를 만든다. 이 사영된 임베딩은 미분 가능하고 LLM 의 native 입력 공간에 정렬되어 있다. 다음으로 sampled token embedding $e_t$ 와 $\tilde{e}_t$ 를 sigmoid 게이트 $g_t$ 로 섞어 하이브리드 입력 $h_t = g_t \cdot e_t + (1 - g_t) \cdot \tilde{e}_t$ 를 만든다 (식의 정확한 형태는 details 02 편). 게이트는 $r_{\min} \approx 0.95$ 부근에서 초기화되어 학습 초반에는 sampled token 이 우세하고, 학습이 진행될수록 hidden 의 비중이 자동으로 올라간다. 이 점진적 도입이 LLM 의 생성 능력을 깨뜨리지 않으면서 latent 신호를 안전하게 주입한다.

학습은 GRPO 와 같은 구조다. 같은 쿼리에서 $G$ 개의 hybrid rollout 을 만들고, 정답 여부 0/1 의 outcome 보상을 그룹 평균·표준편차로 정규화해 어드밴티지를 얻는다. 정책 업데이트는 어드밴티지 가중 log-prob 에 KL 정규화를 더한 REINFORCE 스타일 식 (식 6) 으로 한 번씩만 한다. hidden representation 이 $\theta$ 에 직접 묶여 있어 trajectory 를 재사용하면 on-policy 가정이 깨지기 때문이다. PPO 의 ratio clipping 은 보수적 학습 스케줄에서 거의 작동하지 않아 생략했다.

결과는 작은 모델에서 특히 두드러진다. 지식 집약 QA 5개 (NQ, TriviaQA, HotpotQA, 2WikiMQA, Bamboogle) 에서 1.5B HRPO 가 평균 0.337 로 1.5B PPO 대비 +3.0%p, 3B HRPO 는 0.380 으로 7B RAG (0.335) 대비 +4.5%p. STEM 5개 (GSM8k, MATH, MATH500, MMLU-ST, ARC-C) 에서 1.5B HRPO 가 MATH 0.518 로 Qwen2.5-7B (0.498) 를 넘었고, 3B HRPO 는 평균 0.700 으로 최고 7B 베이스라인과 동급. sub-7B 모델에서 기록된 MATH 0.613, MATH500 0.630 은 이 논문 기준 최고치다.

분석에서는 세 가지가 인상적이다. 첫째, hidden state 그대로 쓰기와 interpolation 만 쓰기는 각각 보상 0 콜랩스와 후반 붕괴를 보였고, 오직 hybrid (HRPO) 만 GRPO 와 같은 안정성에 더 빠른 수렴을 함께 가져갔다. 둘째, 학습이 진행될수록 평균 hidden ratio 가 단조 증가하고 completion 길이는 후반에 줄어든다 — hidden 이 컨텍스트를 잘 압축하고 있다는 신호. 셋째, HRPO 가 학습한 출력은 token 만 디코딩해도 읽히는데, 영어·중국어 같은 cross-lingual reasoning 이 자연스럽게 등장하고 단순한 사실 질의에는 더 적은 디코딩 스텝으로 정답을 낸다. 한계도 명확하다: per-step gating 의 추가 연산, on-policy 제약으로 인한 처리량 제한, continuous representation 의 해석성 저하. 후속 연구에서는 off-policy 확장과 더 단순한 hybrid 설계를 시도해 볼 만하다.

## 자세히 보기

<!-- VERSIONS_START -->
1. [왜 잠재 추론인가, 그리고 왜 어려운가](details/01-why-latent-reasoning/) — 자기회귀 CoT 의 한계와 latent reasoning 의 약속, 그리고 기존 latent 기법이 LLM 에 잘 안 붙는 구조적 이유를 정리하고 HRPO 가 어떤 한 줄로 답하는지 자리잡기.
2. [게이팅으로 토큰과 hidden state 섞기](details/02-gating-and-hybrid-input/) — hidden state 를 embedding 공간으로 사영해 만든 interpolated embedding 과 sampled token embedding 을 학습 가능한 게이트로 섞어, RL 의 stochasticity 를 잃지 않으면서 잠재 신호를 다음 입력에 점진적으로 주입한다.
3. [HRPO 의 RL 목적함수와 학습 루프](details/03-rl-objective-hrpo/) — 정답 여부만으로 보상을 매기고 그룹 상대 어드밴티지로 표준화한 뒤, KL 정규화된 strictly on-policy policy gradient 로 hybrid latent reasoning 을 직접 학습하는 HRPO 의 RL 알고리즘을 정리.
4. [벤치마크 결과: 지식과 STEM](details/04-results-on-knowledge-and-stem/) — HRPO 가 1.5B·3B 백본으로 5개 지식 QA 와 5개 STEM 벤치마크에서 PPO/GRPO 를 일관되게 앞서고, 3B 가 7B 베이스라인과 동급에 도달한다는 결과 정리.
5. [분석, 창발 패턴, 그리고 한계](details/05-analysis-and-emergent-patterns/) — HRPO 의 세 가지 잠재 표현 변형, hidden ratio 와 게이팅 초기화·온도 민감도, 그리고 cross-lingual·압축 같은 창발 추론 패턴과 한계를 한 번에 정리한다.
<!-- VERSIONS_END -->

## 출처

- 논문: <https://arxiv.org/html/2505.18454v2>
- 코드: <https://github.com/Yueeeeeeee/HRPO>
