---
title: ScaleLogic — 증명 트리를 거꾸로 짜서 깊이와 표현력을 분리 제어
date: 2026-05-10
author: TrainToGPB
tags: [RL, 추론, 합성데이터, 논리]
source: https://arxiv.org/abs/2605.06638
summary: 정답 결론에서 출발해 backward 로 증명 트리를 짜고 한 axiom 만 손상시켜 오답을 만든다. 깊이 $D$ 와 후보 수 $B$, 그리고 5단계 표현력 위계를 독립 축으로 두면 난이도가 깨끗하게 분리된다.
format: details
part: 2
---

# ScaleLogic — 증명 트리를 거꾸로 짜서 깊이와 표현력을 분리 제어

> 원본: [arxiv.org/abs/2605.06638](https://arxiv.org/abs/2605.06638)

직전 편에서 우리는 RL 환경의 난이도를 직접 통제할 수 없는 한, 깊은 추론에서 RL 이 어떻게 스케일하는지를 깨끗하게 측정할 수 없다는 점을 정리했다. 이번 편은 그 답으로 제시된 ScaleLogic 의 문제 생성 방식이다. 핵심은 두 가지다. 첫째, 정답 결론에서 출발해 증명 트리를 거꾸로 (backward) 짜서 정답을 단 하나로 못 박는다. 둘째, 사용 가능한 논리 연산자를 5단계 위계로 끊어 표현력을 깊이와 따로 제어한다. 이 둘 덕분에 난이도가 두 축 $D$ (depth) 와 표현력 단계로 깨끗하게 분리된다.

## 한 인스턴스의 모양

ScaleLogic 인스턴스는 단일 정답 다지선다 문제다. 모델은 axiom 집합과 $B$개의 후보 결론 (각각 단일 literal) 을 받고, 그중 axiom 으로부터 도출 가능한 결론 하나를 골라야 한다.

용어부터 정리한다.

- **literal**: 술어를 특정 entity 에 적용한 식, 부정 가능. 예: $\text{cat}(\text{Alice})$, $\neg \text{cat}(\text{Alice})$.
- **axiom**: 주어진 literal (`Alice 는 고양이다`) 또는 규칙 (`Alice 가 고양이라면 Alice 는 포유류다`, $\text{cat}(\text{Alice}) \rightarrow \text{mammal}(\text{Alice})$).
- **proof step**: 한 규칙의 적용. 자식 노드들이 전제, 부모 노드가 결론.
- **proof tree**: 한 결론 literal 을 root 로 하고 여러 proof step 을 쌓아 올린 트리. leaf 가 axiom, root 가 후보 결론.

정답이 되는 후보는 axiom 으로부터 정확히 하나의 도출 경로를 갖고, 나머지 $B-1$ 개 후보는 도출이 불가능하도록 손상돼 있다. 정답인지 아닌지의 판정은 최종 답을 정확히 비교만 하면 되기 때문에, 중간 풀이를 채점할 필요가 없다. RL with verifiable reward 에 그대로 맞물린다.

## Backward 생성, 즉 결론에서 출발하기

문제를 푸는 방향과 만드는 방향이 반대다. 모델은 axiom 으로부터 결론으로 forward 추론하지만, 생성기는 결론 literal 을 root 로 두고 거꾸로 내려간다.

절차는 다음과 같다.

1. 후보 결론 literal $B$개를 root 로 샘플한다. 각 root 가 자기 proof tree 의 시작이다.
2. 작업 큐 $\mathcal{Q}$ 에 `(root, depth=0)` 을 넣고, 가장 깊은 leaf 부터 꺼내며 (depth-first) 확장한다.
3. leaf $\ell$ 의 깊이가 $D$ 미만이면, $\ell$ 을 결론으로 갖는 규칙을 새로 만든다. 규칙의 전제 literal 들은 새 leaf 가 되어 큐로 들어간다. 표현력 플래그가 conjunction 을 허용하면 전제는 다중, disjunction 을 허용하면 결론도 다중이 된다 (실험에서 arity 는 2 로 고정).
4. leaf 의 깊이가 $D$ 에 닿으면 더 확장하지 않고 그 literal 을 axiom 집합에 그대로 넣는다.
5. 큐가 빌 때까지 반복.

이렇게 하면 모든 root 가 정확히 깊이 $D$ 의 proof tree 를 갖고, leaf 들이 모이면 axiom 집합이 된다.

여기에 결정적인 장치가 하나 더 있다. **새 literal 을 도입할 때마다 fresh predicate 을 쓴다.** 즉, 이미 어디선가 등장한 술어는 재사용하지 않는다 (보편 양화 규칙의 재사용은 별도 규칙으로 통제). 술어를 매번 새로 뽑으면 한 노드를 도출할 수 있는 경로가 그 트리의 정해진 한 갈래뿐이게 된다. **각 root 의 도출이 유일** 하다는 뜻이다. 이 유일성은 다음 단계에서 오답을 만드는 트릭을 가능하게 만든다.

`A1 → B`, `A2 → B` 처럼 같은 결론을 두 갈래로 만들 수 있으면 한 갈래를 끊어도 다른 갈래로 도출이 살아남는다. fresh 제약은 그런 우회를 원천 차단한다.

## 정답 하나, 손상된 $B-1$ 개

생성된 $B$개의 트리 중 첫 번째는 그대로 둔다. 그러면 그 트리의 root 는 도출 가능한 정답 후보가 된다. 나머지 $B-1$ 개에 대해서는 트리의 axiom 중 하나를 균등 확률로 골라 손상시킨다. 손상 방식은 두 가지다.

- **(i) 제거**: 그 axiom 을 axiom 집합에서 빼버린다.
- **(ii) 극성 뒤집기**: axiom 안의 literal 한 개를 골라 부정을 뒤집는다. 예: $\text{cat}(\text{Alice})$ 를 $\neg \text{cat}(\text{Alice})$ 로. axiom 이 규칙이라면 전제 또는 결론 중 한 literal 의 극성을 뒤집는다.

방식 (ii) 는 negation 이 켜진 표현력 단계에서만 쓸 수 있다. negation 이 없는 단계에서는 (i) 만 적용된다. 손상 위치가 균등 분포라 "마지막 axiom 이 무조건 망가져 있다" 같은 위치 단축키도 닫혀 있다.

도출이 유일하다는 점이 여기서 결정적이다. 길이 $D$짜리 도출 경로가 단 하나이므로, 그 경로 위 axiom 한 개만 끊어도 root 결론이 도출 불가능해진다. backward 생성과 fresh predicate 제약이 합쳐져 "한 axiom 손상 = 정답 도출 불가" 가 자동으로 성립한다.

마지막으로 **distractor rule** 을 약간 추가한다. 지역적 모호성을 늘리되 새 도출 경로를 만들지 않도록, 규칙의 한쪽 (전제 또는 결론) 은 반드시 fresh predicate 으로만 채운다. 그러면 그 distractor 는 기존 그래프에 한 쪽으로만 닿을 수 있어, 기존 literal 로 trigger 돼도 fresh literal 만 도출하거나, fresh literal 이 필요해서 trigger 자체가 안 된다. 정답에는 영향 없이 모델의 노이즈 내성만 시험하는 장치다.

![Implication-only 와 Most Expressive Logic 두 표현력에서의 ScaleLogic 문제 예시. 좌측 정답 트리만 도출 가능하고, 우측 B-1 개 트리는 손상된 axiom 으로 인해 conclusion 이 도출 불가능하게 됐다.](../assets/fig-1.png)

*그림 1. 같은 다지선다 형식이지만 표현력만 다른 두 인스턴스. 빨간 X 가 손상된 axiom 의 위치다. Implication-only 는 단순 if-then 만, Most Expressive Logic 은 and / not / or / for all 까지 모두 들어간다.*

## 표현력 5단계: 같은 형식, 다른 표현력

깊이 $D$ 와 후보 수 $B$ 는 인스턴스의 구조적 변수다. 여기에 ScaleLogic 은 한 축을 더 둔다. 사용 가능한 논리 연산자 집합. 다섯 단계는 각자가 직전 단계의 strict superset 이라, 한 단계 올라갈 때 새로 들어오는 연산자 하나로 난이도 증가의 원인을 깨끗하게 귀속할 수 있다.

| 단계 | 함의 ($\rightarrow$) | 논리곱 ($\land$) | 부정 ($\neg$) | 논리합 ($\lor$) | 보편 양화 ($\forall$) |
|---|---|---|---|---|---|
| Implication-only | O | - | - | - | - |
| + Conjunction | O | O | - | - | - |
| + Negation | O | O | O | - | - |
| + Disjunction | O | O | O | O | - |
| + Quantification | O | O | O | O | O |

각 단계가 추가하는 추론 부담은 다음과 같다.

### Implication-only

함의만 있다. axiom 은 grounded literal 또는 단일 전제 함의 규칙. 예: $\text{cat}(\text{Alice}) \rightarrow \text{mammal}(\text{Alice})$. 추론은 전제가 만족된 규칙을 반복 적용해 새 literal 을 도출하는 것. 단순 directed graph 의 path-finding 과 동치다.

### + Conjunction

전제에 `and` 가 들어온다. 한 규칙이 여러 literal 을 동시에 요구할 수 있다. 예: $\text{vertebrate}(\text{Alice}) \land \text{has\_fur}(\text{Alice}) \rightarrow \text{mammal}(\text{Alice})$. 모델은 한 규칙을 적용하기 전에 여러 전제가 모두 성립하는지 동시에 확인해야 한다. directed hypergraph 의 path-finding 과 동치 (한 hyperedge 가 여러 source 를 가짐). 결론에는 conjunction 을 허용하지 않는다 — $A \rightarrow B \land C$ 는 $A \rightarrow B$ 와 $A \rightarrow C$ 두 규칙으로 분해되므로 새 표현력이 아니다.

### + Negation

`not` 이 들어온다. 전제와 결론 모두 부정 literal 을 가질 수 있다. 예: $\text{mammal}(\text{Alice}) \rightarrow \neg \text{bird}(\text{Alice})$. 모델은 한 술어가 성립하느냐만이 아니라 그 **극성** 까지 추적해야 한다. 새 조합 구조를 추가하는 게 아니라 polarity 라는 새 차원을 추적시킨다는 점에서, 깊이가 늘어날 때 비용 증가가 생각보다 가파르지 않을 수 있다 (다음 편 power-law 결과에서 + Conjunction 과 + Negation 의 지수가 거의 겹치는 이유다). 또한 negation 이 있으면 손상 방식 (ii) 즉 극성 뒤집기를 쓸 수 있어, 오답 후보 만들기가 자연스러워진다.

### + Disjunction

결론에 `or` 가 들어온다. 한 규칙이 여러 가능한 결론을 함께 산출한다. 예: $\text{pet}(\text{Alice}) \rightarrow \text{cat}(\text{Alice}) \lor \text{dog}(\text{Alice})$. 모델은 어떤 disjunct 가 배제되고 어떤 disjunct 가 목표 결론으로 모이는지 따져야 한다.

backward 생성에는 미묘한 이슈가 하나 있다. 어떤 literal 을 disjunctive rule 로 지지하면 그 literal 자체가 단독으로 도출되지는 않는다 — 도출되는 건 disjunction 그 자체다. 예를 들어 root 가 $\text{mammal}(\text{Alice})$ 이고 $\text{cat}(\text{Alice}) \rightarrow \text{mammal}(\text{Alice})$ 를 들였을 때, $\text{cat}(\text{Alice})$ 를 $\text{pet}(\text{Alice}) \rightarrow \text{cat}(\text{Alice}) \lor \text{dog}(\text{Alice})$ 로 지지하려고 하면 도출되는 건 $\text{cat}(\text{Alice}) \lor \text{dog}(\text{Alice})$ 이지 $\text{cat}(\text{Alice})$ 가 아니다.

저자들은 두 가지 표준적 해결로 이 모호성을 풀어낸다. (i) 다른 disjunct 를 모순 axiom 으로 배제 (예: $\neg \text{dog}(\text{Alice})$ 를 따로 둔다), 또는 (ii) 다른 disjunct 도 같은 downstream 결론으로 수렴시킨다 (예: $\text{dog}(\text{Alice}) \rightarrow \text{mammal}(\text{Alice})$ 를 추가). 어느 쪽이든 root 의 유일 도출은 보존된다. 단, proof tree 가 더 이상 단순 트리가 아니라 hyperedge 를 가진 구조로 일반화된다.

### + Quantification

마지막 단계에서 보편 양화 `for all` 이 들어온다. 규칙이 특정 entity 에 묶이지 않고 모든 entity 에 적용된다. 예: $\forall X.\, \text{cat}(X) \rightarrow \text{mammal}(X)$. 모델은 양화 규칙을 현재 문맥의 구체 entity 로 instantiate 하고, instantiate 된 전제가 성립하는지 확인한 뒤 결론을 도출해야 한다. 이는 명제 추론에서 1차 추론으로 넘어가는 단계다.

이 단계에서는 entity 가 둘 이상이면 의미가 살아난다. 단일 entity 만 있으면 양화 규칙이 entity-특정 규칙으로 환원된다. 그래서 실험은 기본 2 entity 로 두고, 한 보편 규칙이 한 인스턴스 안에서 여러 번 instantiate 되며 술어와 규칙이 entity 사이에 재사용되도록 한다. 모델은 같은 구조가 entity 만 다르게 반복되는 것을 인식하고 풀어내야 한다.

## 자연어 변환

증명 트리와 axiom 집합은 기호 형태로 만들어진다. 이걸 자연어 다지선다 프롬프트로 바꾸는 단계가 또 따로 있다.

- entity ID 는 매 인스턴스마다 새로 (Alice, Bob, ..., Zach 풀에서) 매핑한다.
- 술어 ID 는 매 인스턴스마다 무작위 5글자 문자열로 매핑한다 (예: `abcde`). 실제 영어 단어가 아니다.
- literal axiom 은 사실문 (`Alice 는 abcde 다`), 규칙은 if-then 문, 보편 규칙은 `누구든 abcde 라면 그는 bcdef 다` 같은 양화 템플릿으로 렌더.
- axiom 순서, 후보 순서 모두 셔플.

술어를 매 인스턴스마다 다른 무작위 문자열로 바꾸는 이유는 명확하다. 모델이 "cat 이면 mammal 이지" 라는 세계 지식 단축키를 못 쓰게 한다. 추론 그 자체로만 정답을 맞혀야 한다.

## 왜 이 디자인인가

ScaleLogic 의 생성 파이프라인은 네 가지 요구를 동시에 만족시키도록 만들어졌다.

- **검증 가능한 보상**: 단일 답 다지선다라서 reward 는 정답 비교 한 번이면 끝난다. 중간 풀이 supervision 이 필요 없다. RL with verifiable reward 와 자연스럽게 맞물린다.
- **깊이와 표현력의 독립 통제**: $D$, $B$, 표현력 플래그가 서로 직교하는 손잡이다. 한 축만 움직이며 RL 비용이 어떻게 변하는지 깨끗하게 측정할 수 있다.
- **자동 무한 생성**: 사람이 라벨을 달 필요가 없다. 깊이 $D$ 를 늘리거나 표현력을 한 단계 올려 새 데이터셋을 즉석에서 찍어낸다 (실험에서 한 설정당 보통 10만 인스턴스).
- **표층 단축키 차단**: fresh predicate, 무작위 entity 매핑, axiom·후보 순서 셔플, 균등 위치 손상, 무작위 polarity flip 가 모두 지역적 통계로는 정답을 못 맞히게 막는다. 모델이 도출을 실제로 수행하지 않으면 정답을 못 낸다.

여기에 backward 생성 + fresh predicate 으로 얻는 **유일 도출 보장** 이 결정타다. 이게 깨지면 한 axiom 을 손상시켜도 다른 경로로 정답이 살아남아 손상 자체가 의미를 잃는다. 그러면 부분 풀이로 얻은 chain-of-thought 단축키가 통할 여지가 생긴다. 유일성은 이 단축키 경로를 차단해, 모델이 깊이 $D$ 짜리 도출을 끝까지 따라가야만 정답에 도달하도록 강제한다.

그림 1 에서 확인할 수 있다. 좌측 Implication-only 와 우측 Most Expressive Logic 모두 같은 다지선다 형식인데, 한쪽은 함의 사슬만, 다른 쪽은 conjunction / negation / disjunction / quantification 이 섞여 있다. 빨간 X 가 손상된 axiom 의 위치고, 그 X 하나 때문에 트리 root 의 도출이 끊어진다. 형식은 같고 표현력만 다르다 — 다음 편에서 다룰 power-law 비교가 깨끗하게 가능한 이유다.

## 정리

이 편에서 본 것은 다음과 같다.

- ScaleLogic 은 정답 결론에서 출발해 backward 로 깊이 $D$ 의 증명 트리를 짠다. fresh predicate 제약으로 도출이 유일하다.
- 정답 트리 한 개를 그대로 두고, 나머지 $B-1$ 개 트리는 axiom 한 개를 (제거) 또는 (극성 뒤집기) 로 손상시켜 도출 불가능하게 만든다.
- distractor rule 은 한 쪽이 fresh predicate 이라 새 도출 경로를 만들지 않으면서 지역적 모호성만 늘린다.
- 표현력은 함의 → 논리곱 → 부정 → 논리합 → 보편 양화의 5단계 위계로 한 연산자씩 추가된다. 각 단계는 직전의 strict superset.
- 자연어 변환에서 술어와 entity 매핑을 매번 새로 뽑아 세계 지식 단축키를 차단한다.

축을 분리했다. 이제 깊이를 한 칸 늘릴 때, 표현력을 한 단계 올릴 때 RL 학습이 각각 어떻게 반응하는지 측정할 수 있다. 다음 편은 그 측정의 결과 — 학습 셋업과 깊이에 대한 power-law 스케일링이다.

다음 편 → [DAPO 학습 셋업과 깊이에 대한 파워 로 스케일링](03-rl-setup-and-power-law.md)

## 출처

- https://arxiv.org/abs/2605.06638
