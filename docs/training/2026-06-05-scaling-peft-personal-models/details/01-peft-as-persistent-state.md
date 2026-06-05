---
title: PEFT를 개인 모델의 지속 상태로 다시 보기
date: 2026-06-05
author: 김세형
tags: [PEFT, LoRA, personalization, personal-models, fine-tuning]
source: https://arxiv.org/abs/2606.02437
summary: PEFT를 단순한 비용 절감형 fine-tuning이 아니라 강한 공유 base 위에 붙는 작은 local adaptive state로 해석하고, Scale Up, Scale Down, Scale Out 세 축이 왜 함께 맞물려야 개인 모델이 성립하는지 정리한다.
format: details
part: 1
---

# PEFT를 개인 모델의 지속 상태로 다시 보기

> 원본: [arxiv.org/abs/2606.02437](https://arxiv.org/abs/2606.02437)

PEFT는 보통 "전체 fine-tuning보다 싼 방법"으로 소개된다. 큰 pretrained model은 그대로 두고, LoRA 같은 작은 adapter만 학습하면 학습 메모리와 저장 비용이 줄어든다는 설명이다. 이 설명은 맞지만 충분하지 않다. 이번 논문이 잡는 핵심 관점은 PEFT를 비용 절감 기법이 아니라 **개인 모델의 지속 상태(persistent state)를 담는 단위**로 보는 것이다.

개인 모델이라는 말은 한 사람의 모든 기억과 성격을 파라미터 안에 넣겠다는 뜻이 아니다. 논문의 주장은 더 좁다. 강한 공유 base model이 공통 능력을 제공하고, 작은 adapter가 반복 경험에서 생긴 일부 행동 변화, 선호, 도구 사용 습관, skill, memory-like update를 담을 수 있다는 것이다. 원문은 이 local adaptive state가 retrieval, context, tool state와 함께 개인 모델을 구성한다고 본다.

## 왜 지금 PEFT를 다시 봐야 하나

frontier model은 이미 코드 작성, 도구 호출, 긴 추론, 멀티모달 처리 같은 능력을 갖추기 시작했다. 하지만 유능한 assistant가 곧 개인 assistant가 되는 것은 아니다. 같은 사용자를 오래 만나도 이전 상호작용에서 무엇을 배웠는지, 어떤 행동 경향을 유지해야 하는지, 어떤 도구 사용 패턴이 반복적으로 성공했는지를 안정적으로 보존하지 못하면 개인 모델이라고 부르기 어렵다.

context window를 키우거나 retrieval을 붙이는 방법은 이 문제의 일부를 해결한다. 다만 그것들은 대체로 현재 입력을 잘 구성하는 장치다. 현재 prompt에 어떤 문서를 넣을지, 어떤 profile을 붙일지, 어떤 tool result를 참고할지를 결정한다. 반면 PEFT adapter는 base model의 forward computation 안에 들어가는 작은 학습 상태다. 같은 입력을 받아도 adapter가 붙으면 모델의 분포 자체가 달라진다.

LoRA로 쓰면 이 차이가 더 분명하다. frozen weight $W$ 위에 low-rank update를 얹어 다음처럼 계산한다.

$$
W' = W + \Delta W,\quad \Delta W = BA
$$

여기서 $W$는 공유 prior이고, $\Delta W$가 local adaptive state다. 개인 모델 관점에서 중요한 점은 $\Delta W$가 작다는 사실 자체가 아니라, 이 작은 상태가 이름 붙고, 저장되고, 평가되고, serving되고, 되돌려질 수 있는 독립된 lifecycle object가 될 수 있다는 점이다.

## PEFT가 저장하는 것과 저장하지 않는 것

논문은 PEFT를 memory system 전체로 과장하지 않는다. 오히려 어디까지 adapter에 넣고, 어디부터 외부 상태로 남겨야 하는지를 구분해야 한다고 본다. 이 구분이 없으면 "adapter가 개인을 저장한다"는 너무 강한 주장으로 흘러간다.

| 상태 | 역할 | 적합한 저장 위치 |
|---|---|---|
| 현재 문맥 | 이번 응답에 필요한 instruction, 예시, 임시 정보 | prompt, long context |
| 외부 지식 | 문서, 메모, 검색 결과, 출처가 필요한 사실 | retrieval, vector store, database |
| 도구 상태 | calendar, ticket, file, API side effect | tool system, application state |
| 행동 변화 | 반복 경험에서 생긴 선호, skill, reasoning habit, tool habit | PEFT adapter |

즉, PEFT는 raw archive가 아니다. 사용자의 모든 대화 로그, 문서, 일정을 adapter에 밀어 넣는 방식은 편집 가능성, 출처 추적, 삭제 가능성에서 문제가 생긴다. adapter에 더 자연스럽게 들어가는 것은 "이 사용자는 이런 상황에서 이런 방식으로 도구를 쓰는 것이 좋다", "이 도메인에서는 이런 reasoning template이 자주 통한다", "반복적으로 교정된 답변 스타일은 이쪽이다" 같은 행동을 바꾸는 신호다.

이 관점에서는 retrieval과 PEFT가 경쟁하지 않는다. retrieval은 증거를 가져오고, context는 당장 필요한 정보를 배열하며, tool state는 외부 세계의 현재 상태를 보존한다. adapter는 그 반복 경험의 일부를 모델 내부의 지속적인 행동 경향으로 안정화한다. 원문이 말하는 personal model은 이 네 층을 합친 시스템이고, PEFT는 그중 local adaptive state를 담당하는 후보 기술이다.

## Figure 1이 주는 비유

논문은 생물학 비유를 통해 구조를 잡는다. 인간은 대부분의 유전 정보를 공유하지만, 작은 차이가 각 개인의 차이를 만든다. 더 넓게 보면 하나의 공유 생물학 위에서 수많은 개별 삶이 지속되고, 각 개인은 자기 경험과 skill을 축적한다.

foundation model에서도 비슷한 구조를 상상할 수 있다. base model은 대부분의 능력과 지식을 공유한다. adapter는 전체 parameter에 비해 매우 작지만, 특정 개인 모델을 다른 개인 모델과 구분하는 local state가 될 수 있다. 그리고 이런 adapter가 하나가 아니라 수백만 개 존재할 수 있다면, scaling의 단위는 "하나의 universal assistant"에서 "많은 persistent personal instance"로 바뀐다.

다만 이 비유는 설명 도구일 뿐이다. 생물학적 개인과 모델 adapter를 그대로 동일시하면 곤란하다. 중요한 것은 작은 차이가 큰 행동 차이를 낳을 수 있다는 구조적 가능성, 그리고 그 작은 차이를 지속 가능한 객체로 다루는 시스템 설계다.

원문 Figure 1의 caption은 이 비유를 세 부분으로 나눈다. 생명체가 복잡해질수록 regulatory DNA의 비중이 커지는 현상은 Scale Up에 대응하고, 인간 개인들이 99% 이상 유전 정보를 공유하면서도 작은 차이로 구분된다는 점은 Scale Down에 대응한다. 하나의 공유 생물학 위에서 수많은 개인이 각자의 경험을 축적한다는 점은 Scale Out에 대응한다. 여기서는 PDF에서 해당 그림이 여러 실루엣과 아이콘으로 분리 추출되어 개별 이미지는 사용하지 않는다.

## 세 축: Scale Up, Scale Down, Scale Out

논문은 PEFT scaling을 세 축으로 정리한다. 세 축은 단순한 분류표가 아니라 의존 관계다. 어느 하나만 성공해서는 개인 모델까지 가지 못한다.

| 축 | 질문 | 개인 모델에서의 의미 |
|---|---|---|
| Scale Up | 공유 base가 얼마나 강해야 작은 update가 유용해지는가 | adapter가 redirect할 latent capability를 키운다 |
| Scale Down | local adaptive state를 얼마나 작고 안정적으로 만들 수 있는가 | 반복 학습, 저장, serving의 marginal cost를 낮춘다 |
| Scale Out | 많은 persistent adapter가 공존하면 무엇이 가능한가 | 개인화, user simulation, population diversity를 만든다 |

Scale Up은 "모델을 크게 만들자"는 말과 다르다. 강한 base model이 이미 reasoning, code, vision, tool use 같은 능력을 갖고 있어야 작은 adapter가 그 능력을 의미 있게 조정할 수 있다는 뜻이다. 약한 base 위의 adapter는 싸게 만들 수 있어도 redirect할 능력이 작다. 그러면 개인화는 prompt tuning 수준의 얕은 조정에 머물기 쉽다.

Scale Down은 작은 adapter를 안정적으로 학습하고 운영할 수 있느냐의 문제다. adapter가 작아야 많은 개인 인스턴스를 만들 수 있지만, 너무 작아서 학습이 불안정하면 의미가 없다. 논문 후반부는 low-rank LoRA의 rank regime, 초기화, hyperparameter transfer, memory-oriented adapter를 다루며 이 축을 실험적으로 따진다. 이 첫 편에서는 구조만 잡고, 자세한 내용은 뒤에서 이어진다.

Scale Out은 adapter 수 자체를 scaling variable로 보는 관점이다. 개인별 adapter가 많아지면 단순히 모델 파일이 늘어나는 것이 아니다. 각 adapter가 서로 다른 history, preference, skill, error pattern을 갖게 되고, 그 차이를 simulation, routing, voting, debate, distillation에 쓸 수 있다. 이때 다양성은 부산물이 아니라 계산 자원이 된다.

## 세 축은 왜 독립적이지 않은가

세 축을 따로 보면 각각 자연스러운 연구 주제처럼 보인다. 큰 model을 PEFT로 학습하는 연구, 더 작은 adapter를 만드는 연구, multi-tenant LoRA serving 연구가 이미 따로 존재한다. 논문의 핵심은 이 셋이 개인 모델이라는 목표 안에서는 서로 의존한다는 데 있다.

- Scale Up without Scale Down: 강한 prior는 있지만 adapter를 자주 학습하고 serving하기에 너무 비싸다.
- Scale Down without Scale Up: adapter는 싸지만 base가 약해 개인화할 능력의 폭이 좁다.
- Scale Out without both: 많은 variant는 만들 수 있지만 지속적이고 유용한 개인 모델 population이 아니라 disposable artifact 목록이 된다.

이 의존 관계는 개인 모델의 lifecycle을 생각하면 더 분명해진다. 사용자가 오늘 도구 사용을 교정했다면, 그 교정은 미래 interaction에도 영향을 줘야 한다. 그러려면 base가 그 행동을 표현할 능력을 가져야 하고, adapter가 그 변화를 작고 안정적으로 담아야 하며, system은 해당 adapter를 특정 사용자 또는 policy revision으로 계속 식별할 수 있어야 한다.

이 과정은 한 번의 fine-tuning job으로 끝나지 않는다. 학습, 평가, serving, rollback, retirement가 반복된다. 따라서 PEFT는 training trick이 아니라 operational object가 된다. adapter identity와 provenance가 없으면 어떤 상태가 어떤 경험에서 왔는지 모른다. serving residency 관리가 없으면 많은 adapter를 이름 붙여도 실제 traffic에서 다룰 수 없다.

## 개인 모델은 prompt profile보다 무엇이 다른가

prompt profile은 개인화의 가장 쉬운 형태다. 사용자의 선호, 이름, 역할, 금지사항을 system prompt나 profile로 넣으면 즉시 효과가 난다. 하지만 profile은 매번 context에 실려야 하고, 길이가 늘수록 다른 정보와 경쟁한다. 또한 깊은 reasoning habit이나 tool-use policy를 안정적으로 바꾸는 데는 한계가 있다.

retrieval 기반 memory도 중요하지만 성격이 다르다. retrieval은 "무엇을 참고할 것인가"에 강하다. 예를 들어 사용자의 프로젝트 문서, 과거 회의록, coding convention, 일정은 외부 memory에 남아 있어야 한다. 삭제와 수정이 쉬워야 하고, 응답에는 출처가 필요하다.

tool state는 또 다르다. calendar에 일정이 있거나 ticket의 상태가 바뀌었거나 파일이 생성된 것은 모델 안에 저장할 일이 아니다. 이 상태는 외부 system이 authoritative source다. 모델은 tool을 통해 읽고 써야 한다.

PEFT adapter가 맡을 수 있는 자리는 "반복적으로 드러난 행동 변화"다. 같은 사용자가 매번 비슷한 종류의 코드 리뷰를 요청하고, 특정 수준의 근거 제시를 선호하고, 특정 사내 도구 호출 순서를 반복한다면, 그 패턴은 단순 사실보다 policy에 가깝다. adapter는 이런 policy-shaped state를 담는 작은 parameter object가 될 수 있다.

## 비용 절감에서 지속 상태로

일반적인 LoRA 설명은 trainable parameter 수를 줄이는 데 초점을 둔다. 이것은 여전히 중요하다. 전체 checkpoint를 매번 복사하지 않고 adapter만 저장하면, 학습과 배포 비용이 크게 낮아진다. 하지만 개인 모델 관점에서는 비용 절감이 목적이라기보다 전제 조건이다.

비용이 낮아지면 adapter를 한 번 만들고 버리는 대신 계속 갱신할 수 있다. 저장 비용이 낮아지면 사용자별, task별, policy revision별 상태를 따로 보존할 수 있다. serving 비용이 낮아지면 하나의 base model 위에서 여러 adapter를 바꿔 끼우며 운영할 수 있다. 이때 PEFT는 "싼 fine-tuning"에서 "persistent local state의 carrier"로 의미가 바뀐다.

이 전환은 평가 방식도 바꾼다. 한 adapter가 benchmark score를 얼마나 올렸는지만 보는 것으로는 부족하다. 다음 질문들이 함께 필요하다.

- 이 adapter는 어떤 base version과 호환되는가.
- 어떤 interaction 또는 dataset에서 학습되었는가.
- 현재 serving 중인 revision은 무엇인가.
- 새 update가 이전 행동을 망가뜨리면 rollback할 수 있는가.
- 많은 adapter가 동시에 있을 때 cache, routing, admission은 어떻게 제어되는가.

이 질문들은 논문 후반의 MinT 인프라 논의로 이어진다. 하지만 첫 두 절만 읽어도 방향은 분명하다. PEFT를 personal model의 일부로 보려면 algorithm과 system을 분리해서 생각할 수 없다.

## 이 편의 결론

이 논문의 출발점은 PEFT의 역할을 다시 정의하는 데 있다. PEFT는 전체 fine-tuning의 cheaper substitute일 수 있지만, 그보다 중요한 가능성은 shared base 위에 붙는 local adaptive state라는 점이다. 개인 모델은 하나의 adapter가 아니라 base, adapter, context, retrieval, tool state, lifecycle infrastructure가 결합된 시스템이다.

세 scaling 축은 이 시스템을 성립시키는 조건이다. Scale Up은 작은 adapter가 활용할 강한 prior를 제공한다. Scale Down은 adapter를 반복적으로 학습하고 저장하고 serving할 만큼 작고 안정적으로 만든다. Scale Out은 그 adapter들이 많은 persistent personal instance로 공존할 때 생기는 개인화와 population-level 효과를 다룬다.

다음 편부터는 이 중 첫 번째 축인 Scale Up을 더 기술적으로 본다. 특히 trillion-scale MoE 위에서 LoRA RL을 돌릴 때 무엇이 가능해지고, 어떤 training-serving consistency 문제가 드러나는지가 핵심이다.

다음 편: [trillion-scale LoRA RL이 Scale Up을 가능하게 하는 방식](02-scale-up-lora-rl.md)

## 출처

- [arxiv.org/abs/2606.02437](https://arxiv.org/abs/2606.02437)
