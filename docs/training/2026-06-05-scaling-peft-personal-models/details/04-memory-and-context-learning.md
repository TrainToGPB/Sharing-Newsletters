---
title: "메모리와 Context Learning: 무엇을 파라미터에 쓸 것인가"
date: 2026-06-05
author: 김세형
tags: [PEFT, LoRA, memory, personalization, agents]
source: https://arxiv.org/abs/2606.02437
summary: "δ-mem의 writable local state, DishNameBenchmark의 LoRA 메모리 용량 법칙, 개인 모델의 메모리 계층, 그리고 Context Learning을 adapter write policy로 보는 관점을 정리한다."
format: details
part: 4
---

# 메모리와 Context Learning: 무엇을 파라미터에 쓸 것인가

> 원본: [arxiv.org/abs/2606.02437](https://arxiv.org/abs/2606.02437)

앞 편의 Scale Down은 작은 adapter가 어느 지점까지 안정적으로 학습되는지를 다뤘다. 이 편은 그 다음 질문으로 넘어간다. adapter가 충분히 작고 싸다면, 이제 무엇을 거기에 써야 하는가.

원문 4.2와 5.1의 핵심은 PEFT를 단순한 파라미터 절감 기법이 아니라 개인 모델의 local state 설계 문제로 다시 읽는 데 있다. LoRA는 기본적으로 static parameter patch지만, 개인 모델에는 시간이 지나며 바뀌는 상태가 필요하다. 그래서 논문은 δ-mem 같은 writable adapter, DishNameBenchmark의 capacity law, memory hierarchy, LoRA skill memory, Context Learning을 한 흐름으로 묶는다.

## LoRA 이후의 질문: 작게 만드는 것에서 쓸 수 있게 만드는 것으로

표준 LoRA에서 adaptive state는 학습이 끝나면 고정된다. 같은 입력에는 같은 저랭크 보정이 들어가고, 이전 상호작용의 누적 상태는 adapter 내부에서 직접 갱신되지 않는다. task adaptation에는 이 구조가 충분할 수 있지만, 개인 모델에는 다소 좁다.

개인 모델은 반복되는 선호, 도구 사용 습관, 실패 복구 방식, 장기 작업 맥락을 기억해야 한다. 이때 질문은 rank를 얼마나 낮출 수 있느냐만이 아니다. 어떤 상태를 유지할지, 언제 쓸지, 어떻게 추론에 연결할지가 함께 설계 대상이 된다.

이 관점에서 PEFT는 frozen backbone과 local adaptive state 사이의 인터페이스다. backbone은 공유 지식을 제공하고, adapter는 특정 사용자나 workflow에 붙은 변화량을 저장한다. Scale Down의 역할은 이 local state가 개인 단위로 저장, 갱신, 서빙될 만큼 작아지는 운영 구간을 찾는 것이다.

## δ-mem: writable local state가 붙은 adapter

δ-mem은 이 방향을 잘 보여주는 예다. 일반 LoRA는 학습된 저랭크 행렬을 고정된 보정으로 쓰지만, δ-mem은 compact online associative memory state를 유지한다. 토큰을 처리할 때 이전 memory state를 읽고, 그 결과로 frozen attention 계산에 history-dependent low-rank correction을 만든 뒤, 현재 key-value 정보를 다시 memory에 쓴다.

핵심은 adapter가 더 이상 "학습 후 고정된 패치"에 머물지 않는다는 점이다. δ-mem의 memory state는 입력 history에 따라 바뀌고, 그 상태가 다음 forward computation에 영향을 준다. 즉 local state가 모델 바깥의 검색 결과가 아니라 모델 내부 계산 경로에 붙는다.

원문 Figure 19는 이 구조를 read, correction, write의 세 단계로 그린다. 먼저 compact online memory state에서 현재 위치에 필요한 정보를 읽고, 그 readout으로 frozen attention의 출력을 저랭크 보정한다. 이후 현재 key-value 정보가 delta-rule update를 통해 state에 다시 쓰인다.

원문은 δ-mem을 수식으로 associative key-value state로 표현한다. memory key $k_t^m$와 value $v_t^m$가 있고, update에는 retention을 조절하는 $\lambda_t$와 write strength를 조절하는 $\beta_t$가 들어간다. 중요한 해석은 새 정보를 무조건 누적하는 것이 아니라 prediction residual을 쓴다는 점이다. 이미 예측 가능한 association은 작은 update를 만들고, 새롭거나 잘못 예측된 association은 state를 바꾼다.

이 설계는 개인 모델 관점에서 의미가 있다. 모든 대화 기록을 계속 context에 붙이는 대신, 매 step에서 필요한 history signal만 작은 state로 압축한다. 또 state 크기가 고정되므로 저장 비용이 interaction history 길이에 선형으로 늘지 않는다. 물론 매 decoding step에서 read와 write가 들어가므로 추론 비용은 생긴다. 논문이 보는 trade-off는 이 작은 recurrent computation으로 지속적인 history-dependent steering을 얻는 것이다.

## Table 3이 보여주는 compact dynamic memory의 신호

Table 3은 Qwen3-4B-Instruct 위에서 여러 memory mechanism을 비교한다. textual memory에는 BM25 RAG, LLMLingua-2, MemoryBank가 들어가고, parametric memory에는 Context2LoRA와 MemGen이 들어간다. δ-mem은 sequence-level, token-level, multi-state writing 변형으로 평가된다.

핵심 숫자는 다음과 같다.

| 비교 | 기준 | δ-mem 결과 | 해석 |
|---|---:|---:|---|
| 전체 평균 | Qwen3-4B-Instruct 46.79 | δ-mem TSW 51.66 | best variant가 평균을 약 4.87 포인트 올림 |
| MemoryAgentBench 평균 | 29.54 | δ-mem MSW 38.85 | memory-intensive task에서 이득이 큼 |
| HotpotQA EM/F1 | 42.35 / 56.00 | δ-mem TSW 49.41 / 63.66 | token-level writing이 multi-hop QA에도 신호를 줌 |
| LoCoMo 평균 | 40.79 | δ-mem MSW 49.12 | multi-state가 long-context personal memory 간섭을 줄이는 방향 |

이 결과가 곧 δ-mem이 모든 memory 문제의 답이라는 뜻은 아니다. 다만 static LoRA, textual retrieval, auxiliary memory와 다른 지점을 보여준다. compact state를 attention correction에 직접 연결하면, 외부 텍스트 memory를 매번 재해석하는 방식과는 다른 종류의 persistent signal을 만들 수 있다.

writing granularity도 중요하다. token-level writing은 세밀한 정보를 보존하지만 noise와 비용이 늘 수 있다. sequence-level writing은 중복된 token update를 줄인다. multi-state writing은 여러 상태로 정보를 나눠 interference를 줄이는 쪽이다. 같은 trainable parameter budget이라도 언제 쓰고, 무엇을 쓰고, state를 몇 개로 나누는지가 성능을 바꾼다.

따라서 Beyond LoRA의 요지는 "LoRA보다 복잡한 adapter를 쓰자"가 아니다. static rank 축소만으로는 개인 모델의 요구를 모두 설명하기 어렵다는 것이다. 개인 모델에는 작고, 안정적이고, 갱신 가능한 local state가 필요하다.

## 개인 모델에서 memory는 continuity의 조건이다

5.1은 개인 모델을 더 긴 prompt를 가진 universal assistant로 보지 않는다. 개인 모델은 한 사용자, 역할, 조직, workflow에 대해 지속되는 policy다. 이 policy가 지속되려면 기억이 필요하다.

기억해야 할 것은 단순 선호 문장만이 아니다. 어떤 도구를 언제 쓰는지, 어떤 질문은 먼저 확인해야 하는지, 자주 실패하는 절차를 어떻게 복구하는지, 어떤 스타일의 결과물이 업무에 맞는지 같은 behavior-shaping state가 포함된다. 이 상태가 없으면 매 대화는 다시 처음부터 시작한다.

prompt 기반 personalization은 transient하다. retrieval memory는 크고 편집 가능하지만, 매 turn마다 다시 선택되고 해석되어야 한다. parametric memory는 더 강한 선택지를 준다. 일부 경험이 adapter parameter 안으로 들어가면, 그 경험은 다음 query-only behavior의 출발점 자체를 바꾼다.

하지만 이 접근은 위험한 만큼 제한적이어야 한다. 파라미터에 쓴 memory는 검색 문서처럼 쉽게 열람하거나 지울 수 없다. 따라서 LoRA-as-memory를 쓰려면 먼저 capacity law와 write policy가 필요하다. 얼마만큼 쓸 수 있는지, 무엇을 쓰면 안 되는지, 어떤 신호가 반복될 때 durable state로 옮길지를 정해야 한다.

## DishNameBenchmark: LoRA memory의 용량 법칙

논문은 LoRA memory capacity를 보기 위해 DishNameBenchmark를 제안한다. 이 benchmark는 복잡한 지식을 그대로 외우게 하는 대신, slot-writing과 slot-querying을 통제된 형태로 만든다. 저장 길이, update 빈도, query 방식, correction pattern을 바꿔 가며 adapter가 얼마나 정확히 값을 회수하는지 측정한다.

평가 지표는 capacity efficiency다. 이는 memory tokens per trainable parameter, 즉 trainable parameter 하나가 몇 개의 memory token을 감당하는지에 대한 비율이다. Qwen3-series 모델에서 263개 run을 모아 보면 뚜렷한 transition이 나타난다.

원문 Figure 21은 이 transition을 capacity efficiency 축 위에 표시한다. 첫째, capacity efficiency가 약 $10^{-3}$보다 낮을 때는 accuracy가 거의 1에 가깝다. 둘째, $10^{-3}$에서 $10^{-2}$ 사이에서 성능이 점진적으로 흔들리기 시작한다. 셋째, $10^{-2}$를 넘어서면 accuracy가 빠르게 붕괴한다. 이 결과는 LoRA memory가 무한한 저장소가 아니라 측정 가능한 용량 한계를 가진다는 뜻이다.

rank ablation도 같은 해석을 지지한다. 낮은 memory load에서는 작은 rank adapter도 큰 rank adapter와 비슷하게 동작한다. 하지만 요구되는 slot 수가 adapter의 effective capacity를 넘으면 성능이 급격히 떨어진다. rank는 capacity boundary를 오른쪽으로 밀어 주지만, capacity law 자체를 없애지는 않는다.

개인 모델 운영 관점에서는 이 숫자가 중요하다. adapter 하나에 사용자의 모든 사실, 문서, 캘린더, 작업 이력, 도구 결과를 다 쓰겠다는 설계는 capacity와 governance 양쪽에서 맞지 않는다. 파라미터 memory는 희소한 자원이고, 그 희소성을 전제로 write policy를 설계해야 한다.

## 어디에 쓸 것인가: MLP > Attention ≈ All >> Unembed

DishNameBenchmark의 또 다른 결과는 module choice다. 같은 memory task라도 어느 module에 LoRA를 붙이는지에 따라 parameter efficiency가 달라진다. 원문이 정리한 ordering은 다음과 같다.

$$
\text{MLP} > \text{Attention} \approx \text{All} \gg \text{Unembed}
$$

MLP LoRA는 matched parameter budget에서 가장 좋은 memory efficiency를 보인다. attention-only와 full-module training도 memory를 저장할 수 있지만, parameter당 효율은 낮다. unembedding-only는 빠르게 무너진다.

이 결과는 두 가지로 읽을 수 있다.

- memory를 많이 쓰고 싶다면 rank만 올리는 것으로 충분하지 않다. 같은 parameter 수라도 어떤 module을 adaptive surface로 쓰는지가 capacity를 바꾼다.
- 개인 adapter의 기본 저장 대상은 raw token distribution보다 behavior transformation에 가까워야 한다. unembed는 표면 출력에 가깝고, MLP는 내부 feature transformation에 더 깊게 걸린다.

물론 DishNameBenchmark는 통제된 실험이다. 실제 사용자 memory는 더 noisy하고, overwrite와 conflict도 많다. 그래도 module choice가 memory capacity에 강한 영향을 준다는 점은 adapter 설계의 실무 변수로 남는다.

## Memory hierarchy: 모든 것을 파라미터에 쓰지 않는다

Table 4는 개인 모델의 memory hierarchy를 명확히 나눈다. 이 표의 메시지는 간단하다. LoRA memory가 가능하다고 해서 모든 정보를 LoRA에 쓰면 안 된다.

| Memory layer | 예 | 적합한 역할 |
|---|---|---|
| Context | 현재 대화, 현재 작업 상태 | 짧은 추론, 국소적인 task state |
| Retrieval memory | 노트, 문서, 사용자 facts | 편집 가능한 factual recall, 큰 evidence store |
| Tool state | 캘린더, 파일, DB, issue tracker | 외부 현실, inspectable state |
| LoRA memory | skill, habit, policy, persona | 지속적인 behavioral adaptation |

문서에 있는 희귀한 사실은 retrieval에 남아야 한다. 캘린더 일정이나 파일 상태는 tool state로 남아야 한다. 사용자가 명시적으로 고칠 수 있어야 하는 profile 정보도 retrieval이나 설정 레이어가 더 적합하다. LoRA memory는 직접 열람과 수정이 어렵기 때문이다.

반대로 반복적인 workflow, 도구 사용 순서, 검증 습관, 안전 루틴, domain heuristic은 LoRA memory의 후보가 된다. 이런 정보는 사실 자체보다 행동을 바꾼다. 개인 모델이 매번 같은 사용자의 업무 방식에 더 빨리 맞춰지는 이유는 "무엇을 알고 있는가"보다 "어떻게 행동하는가"에 있다.

따라서 좋은 personal model은 memory placement를 결정해야 한다. 현재 context에 둘 것, retrieval에 보관할 것, tool state로 유지할 것, adapter parameter로 internalize할 것을 구분한다. 이 구분이 없으면 LoRA memory는 곧 용량 초과와 governance 문제를 동시에 맞는다.

## LoRA skill memory: ALFWorld에서 보이는 절차적 기억

원문은 LoRA가 skill-like behavioral state를 저장할 수 있다는 근거로 ALFWorld 실험을 든다. Qwen3-235B를 shared base로 두고, rank-32 LoRA adapter를 Skill-0/MinT recipe로 학습한다. 그 결과 validation 평균이 base 0.646에서 adapted 0.845로 오른다.

이 결과를 "LoRA가 사실을 잘 외운다"로 읽으면 안 된다. ALFWorld는 절차적 환경이다. 모델은 물건을 찾고, 옮기고, 조작하고, subgoal을 순서대로 수행해야 한다. adapter가 바꾼 것은 특정 fact의 recall이라기보다 행동 policy다.

이 점이 개인 모델의 memory hierarchy와 연결된다. 개인 adapter에 적합한 것은 다음과 같은 skill memory다.

- 자주 쓰는 도구 chain과 실패 시 fallback 절차
- 특정 업무 산출물의 구조와 검토 기준
- 사용자가 선호하는 의사결정 순서와 확인 질문
- 반복되는 domain-specific reasoning template
- 외부 tool outcome을 보고 다음 action을 고르는 습관

skill memory는 compact해야 하고, 반복적으로 재사용되어야 하며, query-only behavior를 실제로 바꿔야 한다. 이런 조건을 만족하지 못하는 정보는 파라미터에 쓰기보다 context, retrieval, tool state에 남기는 편이 낫다.

## Context Learning: Context Engineering이 아니라 write policy

여기서 Context Learning이 등장한다. 원문은 Context Learning을 독립된 Scale Out 알고리즘이라기보다 LoRA-as-memory의 write policy로 둔다. Context Engineering이 현재 응답을 좋게 만들기 위해 정보를 선택, 검색, 배열하는 일이라면, Context Learning은 그 context-time improvement 중 무엇을 future behavior로 고정할지 결정하는 일이다.

이 구분은 실무적으로 중요하다. RAG가 어떤 query에서 성능을 올렸다고 해서 그 retrieval 결과를 모두 adapter에 쓸 필요는 없다. tool execution이 한 번 성공했다고 해서 그 절차를 바로 파라미터화하는 것도 위험하다. write policy는 반복성, 안정성, permission, correction 가능성, capacity cost를 함께 봐야 한다.

Context Learning은 다음 질문을 묻는다.

- 같은 context signal이 반복적으로 query-only behavior를 개선하는가.
- 해당 정보가 retrieval이나 tool state보다 adapter에 있을 때 더 가치가 큰가.
- 사용자가 수정하거나 삭제해야 할 가능성이 낮은가.
- capacity를 쓸 만큼 재사용 빈도와 행동 영향이 큰가.
- 잘못 internalize되었을 때 복구 가능한가.

이 기준을 통과한 signal만 adapter update의 후보가 된다. 그래서 Context Learning은 prompting 기법이라기보다 memory governance와 training signal selection의 문제에 가깝다.

## Context Distillation: context gain을 parameter로 옮기는 최소 루프

Listing 1과 Figure 23은 Context Distillation을 간단한 루프로 표현한다. 먼저 query-only policy가 on-policy rollout을 만든다. 그 다음 query-plus-context system이 retrieval evidence, demonstration, tool output, execution outcome, slower verification 등을 사용해 그 rollout을 평가한다. 마지막으로 token-level 또는 trajectory-level reward가 RL-style update를 만든다.

핵심은 update 대상이 query-only rollout이라는 점이다. context가 붙은 teacher output을 supervised target으로 베끼는 방식과 다르다. 모델은 privileged context 없이 낸 자신의 행동에 대해, context system이 준 평가를 바탕으로 업데이트된다. 따라서 학습 후에는 같은 context가 없어도 더 나은 query-only behavior에서 시작할 수 있다.

원문 Figure 23은 이 차이를 도식화한다. query-only policy가 먼저 token sequence를 만들고, query-plus-context 경로는 그 sequence에 reward를 붙인다. privileged context는 답안을 대신 생성하는 target source가 아니라, 이미 나온 행동을 평가하는 teacher signal이다.

원문 Listing 1을 말로 풀면 다음과 같다.

| 단계 | 동작 | 의미 |
|---|---|---|
| 1 | `model.sample(query)` | 현재 policy가 context 없이 on-policy rollout 생성 |
| 2 | `build_context(query)` | retrieval, tool, demonstration, verifier 등으로 privileged context 구성 |
| 3 | `token_reward(query, ctx, out)` | context가 rollout의 token 또는 trajectory를 평가 |
| 4 | `rl_update(model, query, out, r_tok)` | query-only behavior를 보상 신호로 업데이트 |

이 과정을 반복하면 Context Distillation이 Context Learning이 된다. 시점 $t$의 policy $\pi_t$가 context 없이 답하고, context system이 더 느리고 더 풍부한 평가를 제공하고, adapter update를 거쳐 $\pi_{t+1}$이 된다. 다음 query-only inference는 이전보다 강한 internal state에서 시작한다.

RAG2LoRA식 transfer도 이 틀에서 이해할 수 있다. 검색된 모든 fact를 파라미터에 쓰자는 말이 아니다. retrieval이 반복적으로 행동을 개선하는 teacher signal을 제공할 때, 그 일부를 adapter가 internalize할 수 있다는 뜻이다. evidence는 여전히 retrieval에 남고, 반복되는 procedure나 preference만 parametric memory로 이동한다.

## 개인 adapter의 write policy로 정리하기

4.2와 5.1을 한 문장으로 묶으면 "개인 모델에는 writable local state가 필요하지만, 그 state는 희소하고 governance가 필요한 자원"이다. δ-mem은 writable state가 모델 계산 경로에 붙을 수 있음을 보인다. DishNameBenchmark는 LoRA memory에 $10^{-3}$에서 $10^{-2}$ memory tokens per trainable parameter 수준의 실증적 capacity boundary가 있음을 보인다. Table 4는 무엇을 파라미터에 쓰지 말아야 하는지를 알려 준다. Context Learning은 그 경계를 전제로 무엇을 쓸지 결정하는 policy다.

운영 관점의 결론은 보수적이다.

- raw facts는 기본적으로 retrieval에 둔다.
- external reality는 tool state에 둔다.
- 현재 작업의 일시적 상태는 context에 둔다.
- 반복되는 skill, habit, policy, persona만 LoRA memory 후보로 올린다.
- adapter update는 context-time gain이 반복적으로 확인될 때 수행한다.

이렇게 보면 PEFT scaling은 parameter count를 줄이는 이야기에서 끝나지 않는다. 작은 adapter가 충분히 많아질 때, 진짜 병목은 무엇을 저장할지와 언제 저장할지다. 다음 편의 Scale Out과 MinT는 이 개인 adapter들이 백만 개 단위로 존재할 때, 시스템이 어떻게 identity, mobility, residency, provenance를 다뤄야 하는지로 넘어간다.

다음 편: [Scale Out과 MinT: 백만 개 어댑터를 시스템으로 다루기](05-scale-out-and-mint.md)

## 출처

- [arxiv.org/abs/2606.02437](https://arxiv.org/abs/2606.02437)
