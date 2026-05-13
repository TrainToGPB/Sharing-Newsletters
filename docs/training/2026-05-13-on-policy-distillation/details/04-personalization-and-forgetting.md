---
title: 도메인 지식과 instruction following 을 한 모델에 — 사내 어시스턴트 사례
date: 2026-05-13
author: TrainToGPB
tags: [사후학습, 증류, personalization, catastrophic-forgetting, IF-eval]
source: https://thinkingmachines.ai/blog/on-policy-distillation/
summary: 사내 문서로 mid-train 한 Qwen3-8B 의 instruction following 이 85% → 45% 로 무너지지만, Tulu3 prompt 로 on-policy distillation 을 돌려 83% 까지 복원하면서 knowledge 도 함께 유지된다. LoRA·SFT 의 한계와 함께 결과 표를 본다.
format: details
part: 4
---

# 도메인 지식과 instruction following 을 한 모델에 — 사내 어시스턴트 사례

> 원본: [thinkingmachines.ai/blog/on-policy-distillation](https://thinkingmachines.ai/blog/on-policy-distillation/)

앞 편에서는 수학 추론이라는, 비교적 깨끗하게 단일 능력을 끌어올리는 시나리오를 다뤘다. 학생 모델에 이미 사후학습이 충분히 들어가 있고, 우리는 reasoning 한 축만 더 밀어 올리면 됐다. 그러나 실제 산업 현장에서 작은 모델을 쓰려는 동기는 보통 그렇게 단순하지 않다. "우리 회사의 어시스턴트가 됐으면 좋겠다" 같은 요구는 두 가지를 동시에 요구한다. 첫째, 모델이 **모르던 도메인 지식**을 알아야 한다. 둘째, 그 위에서 모델이 **원래 잘하던 사후학습 행동**을 계속해 줘야 한다. 톤, 출력 포맷, tool 사용 규약, 비용 예산 안에서 답하기, 사용자 지시를 무시하지 않기 같은 것들이다.

이 두 가지를 한 모델에 동시에 얹는 일은 생각보다 어렵다. 가벼운 fine-tune 한 번으로는 부족하다는 것이 여러 보고에서 반복적으로 확인됐다. Kang et al. (2024) 의 *Unfamiliar Finetuning Examples Control How Language Models Hallucinate* 는 익숙하지 않은 fine-tune 데이터가 사실성에 어떻게 영향을 주는지 분석하면서, 가벼운 사후 튜닝만으로는 새 지식과 기존 행동을 안정적으로 결합하기 어렵다는 점을 보여준다. 본격적인 mid-training 단계가 필요하다는 뜻이고, 그 위에 다시 복잡한 사후학습 스택 — 자체 데이터, reward model, 정렬 파이프라인 — 을 얹어야 한다. 프론티어 랩에는 이 스택이 이미 있지만, 그 바깥에서 이 비용을 감당할 수 있는 팀은 많지 않다.

이번 편의 사례는 그래서 흥미롭다. 원본 글의 *Distillation for personalization* 섹션은 "사내 문서를 학습시킨 어시스턴트" 라는 아주 평범한 요구를 골라서, **on-policy distillation 만으로 그 어려움을 어떻게 우회하는지** 보여준다.

## 셋업: Qwen3-8B 위에 두 목표를 동시에

출발점 모델은 Qwen3-8B 이다. base 모델이 아니라 이미 instruction following 과 reasoning 에 대해 RL 까지 거친 사후학습 완료 버전이다. 작은 어시스턴트로 쓰기에 충분히 똑똑하고, instruction following 능력도 이미 갖고 있다.

목표는 두 축이다.

- **Knowledge**: 모델이 사내 도메인에 대해 *아는가*. 사내 문서 전체에 대해 사실 회상 기반의 자체 평가셋을 만들어 측정한다. 원본에서는 이걸 "internal QA" 라고 부른다. 사전학습된 모델은 회사 내부 문서를 본 적이 없으므로 모델 크기를 키운다고 해서 점수가 올라가지 않는다. 어떤 형태로든 학습이 필요한 영역이다.
- **사후학습 행동**: 사용자 지시를 따르는 능력. Zhou et al. (2023) 의 IF-eval 로 측정한다. 이건 Qwen3-8B 가 이미 잘하는 영역이므로, 학습 후에 *덜 깎이는 것* 이 목표다.

여기에 깔린 한 가지 불편한 사실이 있다. Mukherjee et al. (2025) 의 *Reinforcement Learning Finetunes Small Subnetworks in Large Language Models* 가 지적한 대로, RL 로 학습된 사후학습 행동은 모델의 작은 sub-network 만 건드린다. 다시 말해, instruction following 같은 능력은 모델 전체에 골고루 분산돼 있는 게 아니라 좁은 영역에 비교적 얇게 얹혀 있다. 그 위에 다시 큰 학습을 돌리면, 그 얇은 영역이 가장 먼저 망가진다는 뜻이다. RL 로 다듬은 행동이 추가 학습에 **fragile** 하다는 게 이번 사례의 출발점이다.

## Catastrophic forgetting 을 어떻게 막을 것인가

이 fragility 의 결과를 우리는 catastrophic forgetting 이라고 부른다. 새 도메인에서 잘하게 만들려고 mid-train 을 돌렸더니, 원래 잘하던 것을 다 까먹는 현상이다.

전통적인 처방은 단순하다. mid-training 중에 원래 pretraining 분포에서 뽑은 "background data" 를 일정 비율로 섞어 주는 것이다. Liu et al. (2025) 의 *Midtraining Bridges Pretraining and Posttraining Distributions* 가 이 처방을 정리한다. 그러나 사내 사례에서는 큰 걸림돌이 있다. Qwen3 의 pretraining 분포에 우리는 접근할 수 없다. 오픈된 데이터셋도 아니고, 정확한 mixture 도 공개돼 있지 않다.

원본 글의 우회는 다음과 같다. 진짜 pretraining 분포 대신, Tulu3 (Ivison et al. 2024) — 광범위한 chat 과 instruction-following 응답을 포함한 공개 데이터셋 — 의 **prompt 만** 가져온 뒤, 그 prompt 에 대한 답을 **Qwen3-8B 자기 자신이 다시 생성** 한다. 즉 Tulu3 의 응답은 버리고, prompt 만 재사용해서 학생 모델 자체로 re-sampling 한다. 이렇게 만들어진 "on-policy background data" 는 mid-train 동안 모델의 원래 분포를 잡아주는 forwards $\mathrm{KL}$ regularizer 역할을 한다. 학생이 원래 자신이었으면 했을 답에서 너무 멀어지지 못하게 묶어두는 닻이다.

흥미로운 디테일이 하나 더 있다. 이 background data 를 만들 때, **Qwen3-8B 자기 자신** 으로 샘플링하는 쪽이 **Qwen3-32B** 로 샘플링하는 쪽보다 chat capability 보존에 더 좋았다. 더 크고 더 잘하는 모델로 만든 데이터가 더 좋을 거라는 직관과 어긋난다. 이는 사후 학습된 모델에게 "어떤 데이터를 본다" 가 단순한 quality 문제가 아니라 **자기 분포와의 거리** 문제라는 점을 다시 한 번 보여 준다. 비슷한 on-policy SFT 관찰이 Chen et al. (2025) 의 *Retaining by Doing: The Role of On-Policy Data in Mitigating Forgetting* 에서도 보고됐다.

저자들은 한 가지 가설까지 던진다. 이렇게 만든 on-policy background data 가 어쩌면 원본 pretraining 분포 자체보다도 더 강한 regularizer 일 수 있다는 가설이다. 다만 대가가 있다. 모든 background data 를 자기 모델로 매번 새로 샘플링해야 하므로, 대규모 sampling 비용이 그대로 추가된다.

## Fine-tune mix 실험: 어느 비율을 골라도 IF-eval 은 회복되지 않는다

이제 본격적으로 두 종류의 데이터 — 사내 문서, 그리고 위에서 만든 on-policy chat background — 의 비율을 바꿔 가며 fine-tune 을 돌린다. 직관적인 관찰부터 정리하면 이렇다.

- 문서 비중을 올릴수록 사내 도메인에 대한 knowledge 가 좋아진다. 이건 당연하다.
- chat data 비중을 30% 이상 유지하면, instruction following 이 *일부* 보존된다. 즉 IF-eval 점수가 덜 깎인다.

그러나 결정적인 한계가 드러난다. **어떤 비율을 골라도 원래 Qwen3-8B 의 IF-eval 수준은 회복되지 않는다.** 심지어 SFT 데이터를 100% chat 으로만 채워도 마찬가지다. 즉 새 도메인 지식이 *없는* 상태로 chat 데이터만 다시 SFT 해도, 원본 사후학습된 모델 수준의 instruction following 이 돌아오지 않는다. fine-tune 이라는 행위 자체가 RL 로 다듬어 놓은 좁은 sub-network 를 어느 정도는 흩뜨려 놓는다.

게다가 어떤 mix 를 골라도 학습이 길어질수록 IF-eval 은 단조 감소한다. 즉 모델을 더 깊게 도메인에 특화시키고 싶으면, 그만큼 사후학습 행동을 더 잃을 각오를 해야 한다. 도메인 특화의 깊이와 사후학습 행동의 보존 사이에 직접적인 trade-off 가 있는 셈이다. 원본 글은 직관적으로는 "과매개변수화된 모델은 학습 데이터의 context 안에서만 행동을 갱신해야 한다" 고 기대할 수 있지만, 실제로는 그렇지 않다고 지적한다. 문서만 보고 SFT 했는데 QA context 에서마저 성능이 회귀하는 경우가 관측된다.

흔히 떠올리는 다른 해법은 LoRA 다. parameter update 자체를 저차원 부분공간으로 제한하면, catastrophic forgetting 도 자연히 줄지 않겠느냐는 직관이다. 그러나 이 시나리오에서는 LoRA 도 충분치 않다. Biderman et al. (2024) 의 *LoRA Learns Less and Forgets Less* 가 정확히 이 trade-off 를 정리한다. LoRA 는 잊는 것도 덜 잊지만, **새로 배우는 것도 덜 배운다.** instruction following 을 지키긴 하지만, knowledge 도 충분히 올라오지 않는 위치에 머무른다. 두 목표 모두를 동시에 충족시키는 방법이 아니다.

## On-policy distillation 으로 instruction following 만 따로 되살리기

여기서 원본 글의 핵심 아이디어가 등장한다. mid-train 의 mix 비율을 잘 잡는 것만으로 두 능력을 동시에 살리려 하지 말자. 대신 **mid-train 이 끝난 뒤** 별도의 짧은 phase 를 추가해서, instruction following 만 **on-policy distillation 으로 복원** 한다.

복원 phase 의 셋업은 단순하다.

- Tulu3 의 prompt 를 가져온다.
- 학생: 방금 mid-train 으로 도메인 지식을 얻은 모델.
- 교사: **이 학생의 earlier version**, 즉 mid-train 이전의 Qwen3-8B 자기 자신.
- 학생이 prompt 에 대해 rollout 을 만들면, 토큰 단위로 교사 분포와의 reverse $\mathrm{KL}$ 을 줄이는 방향으로 업데이트한다 — 시리즈 앞 편에서 정의한 그 on-policy distillation 이다.

이 phase 에는 사내 문서가 한 줄도 들어가지 않는다. 목적은 *오직 instruction following 의 회복* 이다. 학습은 mid-train 단계와 완전히 분리돼 있고, knowledge 회로는 더 이상 건드려지지 않는다.

설계적으로 매력적인 부분은 두 가지다.

첫째, 교사가 **같은 모델의 이전 버전** 이다. 외부의 큰 교사 모델이 필요 없고, 사용자 입장에서 추가로 신경 쓸 정렬 데이터나 reward model 도 없다. 본인이 본인을 끌어 올린다.

둘째, 이 구조가 continual learning 시나리오와 그대로 맞물린다. 새 도메인 지식이 들어올 때마다 mid-train phase 를 짧게 돌리고, 그 직후에 distillation phase 로 사후학습 행동을 다시 끌어올리는 사이클을 무한히 반복하면 된다. 학습-망각-회복-학습 의 순환을 phase 로 쪼개서 다루는 이 발상은 새로운 것이 아니다. Cobbe et al. (2020) 의 *Phasic Policy Gradient* 가 RL 측면에서 같은 발상을 정리해 둔 바 있다. 새 정책 갱신과 가치함수 보정처럼 다른 학습 신호를 분리된 phase 로 나눠서 다루는 구조이다. 우리의 경우 phase 들은 "지식 phase" 와 "행동 phase" 이다.

## 결과 표

| Model | Internal QA Eval (Knowledge) | IF-eval (Chat) |
|---|---|---|
| Qwen3-8B | 18% | 85% |
| + midtrain (100%) | 43% | 45% |
| + midtrain (70%) | 36% | 79% |
| + midtrain (70%) + distill | 41% | 83% |

이 표가 이 편 전체의 결론이다. 한 줄씩 읽으면 다음과 같다.

첫 줄, 원본 Qwen3-8B 는 사내 문서를 본 적이 없으므로 internal QA 는 18% 수준이다. 추측에 가깝다. 반면 IF-eval 은 85% 로, 사후학습 모델다운 수준이다.

둘째 줄은 사내 문서로만 mid-train 을 돌린 경우다. 100% 문서. knowledge 가 18% → 43% 로 가장 크게 뛴다. 이 셋업에서 도달할 수 있는 knowledge 의 상한에 가깝다. 그러나 IF-eval 은 85% → 45% 로 절반 가까이 무너진다. 어시스턴트로 쓰기엔 사실상 못 쓰는 상태다. RL 로 다듬어 놓은 사후학습 행동의 **fragile 함** 이 가장 노골적으로 드러나는 줄이다.

셋째 줄은 위에서 만든 on-policy chat background 를 30% 섞은 70-30 mix 다. knowledge 가 36% 로 약간 떨어지는 대신 IF-eval 이 79% 까지 보존된다. mix 만으로 만들 수 있는 가장 균형 잡힌 구간이다. 그러나 IF-eval 은 여전히 원본의 85% 에는 못 미친다.

마지막 줄이 핵심이다. 셋째 줄의 mid-trained 모델에 **on-policy distillation phase 만 추가** 했다. instruction following 이 79% → 83% 로 올라온다. 원본 Qwen3-8B 의 85% 에 거의 닿는다. 동시에 internal QA 는 36% → 41% 로, **떨어지지 않고 오히려 올라간다.** 도메인 지식은 단 한 줄의 사내 문서도 추가로 보지 않은 상태에서다.

이 마지막 변화 — knowledge 가 *증가* 한 부분 — 는 작은 숫자지만 의미가 크다. chat capability 와 도메인 knowledge 사이에 **positive transfer** 가 있다는 관찰이다. 도메인 사실을 알고 있되 그 사실을 instruction following 의 틀 위에서 *조직해서 표현* 할 수 있게 되면, 같은 사실을 QA 형식 안에서도 더 잘 끌어낼 수 있다. 가설 수준이지만 그럴듯한 해석이고, 무엇보다 "사후학습 phase 가 knowledge 를 깎지 않는다" 는 점이 이 접근법의 안정성을 단단히 받쳐 준다.

## 함의: 어시스턴트 한 명을 어떻게 키울 것인가

이 결과는 사내 어시스턴트라는 한 사례를 넘어서, 어떻게든 작은 모델을 자기 도메인에 맞게 키우려는 모든 팀에 직접 적용된다. 두 가지 함의를 짚어 두자.

첫째, **어떤 instruction-tuned open-weight 모델이든 reward model 로 활용할 수 있다.** 필요한 건 사실상 `compute_logprobs` 하나뿐이다. 학생 rollout 의 토큰 분포와 교사 분포의 reverse $\mathrm{KL}$ 만 계산하면 학습 신호가 나온다. 별도의 reward head 도, preference dataset 도, RLHF 파이프라인도 필요 없다. 어시스턴트의 사후학습 행동을 "내가 원래 갖고 있던 Qwen3-8B 같은 모델" 이 정의해 주는 셈이다. 이 발상은 DPO (Rafailov et al. 2023) 가 한 모델의 로그우도 비율을 그 자체로 reward 로 다룬 방식과, 더 거슬러 올라가 Ng & Russell (2000) 의 inverse RL 이 *관측된 정책의 high-probability behavior 는 advantageous* 라고 가정한 방식과 연결돼 있다. 좋은 정책을 직접 reward 화하는 가장 단순한 형태가, 이 셋업에서는 "그냥 그 모델로 logprob 을 뽑는" 것이다.

둘째, **continual learning 의 실용적 레시피가 보인다.** 새 도메인이 추가될 때마다 모든 정렬 데이터와 reward model 을 다시 세팅하는 대신, "이전 시점의 자기 자신을 교사로 한 distillation phase" 만 짧게 끼워 넣으면 사후학습 행동이 회복된다. 학습 사이클은 이렇게 단순해진다. 새 지식이 들어오면 mid-train 한 차례, 그 직후 짧은 distillation phase 로 행동을 회복. 다시 새 지식이 들어오면 반복. Qwen3 의 hybrid reasoning model 통합이나 DeepSeek-V3.2-Exp 의 specialist distillation 같은 최근의 흐름도 같은 맥락 위에 놓인다. specialist 들을 따로 학습한 뒤 한 모델 안으로 distill 해 다시 모으는 구조 자체가, "분리된 phase 로 학습한 뒤 distillation 으로 통합" 이라는 발상의 다른 얼굴이다.

요약하자면, 이번 편이 보여 준 것은 단순한 표 한 장의 숫자가 아니다. 사후학습 행동을 *데이터 mix 만으로* 지키려는 시도는 어느 비율에서도 원본 수준을 회복하지 못한다는 부정적 결론과, 그 한계를 **별도 phase 의 on-policy distillation** 으로 정확히 메울 수 있다는 긍정적 결론이 동시에 있다. 그리고 그 phase 의 교사는 외부의 큰 모델이 아니라 *나 자신의 한 단계 이전 버전* 으로도 충분하다는, 운영상 매우 가벼운 결론까지 따라온다.

남은 질문은 이 모든 게 *얼마나 효율적인가* 이다. mid-train 자체는 어차피 도메인 지식을 위해 돌아간 비용이라 치자. 그 위에 얹는 distillation phase 는 얼마나 짧고 얼마나 싸야 의미가 있는가. 그리고 이걸 반복해서 돌리는 continual learning 사이클이 실제로 어디까지 안정적인가. 이게 다음 편의 주제다.

다음 편: [Dense reward 가 만드는 50~100배 절감과 continual learning 의 약속](05-compute-efficiency-and-continual-learning.md)

## 출처
- https://thinkingmachines.ai/blog/on-policy-distillation/
