---
title: "모델이 말하지 않는 것을 듣기 — Unverbalized Evaluation Awareness"
date: 2026-05-11
author: TrainToGPB
tags:
  - interpretability
  - nla
  - evaluation-awareness
  - alignment
  - anthropic
source: https://transformer-circuits.pub/2026/nla/index.html
summary: "NLA가 verbalize되지 않은 evaluation awareness를 탐지할 수 있는지 — 평가 vs 배포 비교, 활성값 스티어링, 현실성 편집 세 가지 조작으로 검증한 결과."
format: details
part: 7
---

# 모델이 말하지 않는 것을 듣기 — Unverbalized Evaluation Awareness

> 원본: [transformer-circuits.pub/2026/nla](https://transformer-circuits.pub/2026/nla/index.html)

이 편은 NLA가 가장 야심 차게 노리는 활용처 — 모델이 출력으로는 한 마디도 비치지 않은 채 내부적으로만 가지고 있는 평가 인식(evaluation awareness)의 탐지 — 를 다룬다. 직전 편이 NLA의 평가 점수와 confabulation의 실무적 한계를 정리했다면, 이번에는 그 한계를 인정한 위에서 NLA가 어떤 종류의 신호를 제공할 수 있는지를 살핀다.

## 왜 unverbalized awareness가 문제인가

정렬 평가(alignment evaluation)의 신뢰성은 한 가지 가정에 기댄다. **평가를 받는 동안 모델이 실제 배포 환경에서 행동하는 것과 같게 행동한다**는 것이다. 만약 모델이 "이건 시험 같은데" 라고 알아채면, 실제 배포라면 했을 행동을 억누르고 평가자가 보고 싶어할 행동만 보여줄 수 있다. 실제로 최근 frontier 모델들은 evaluation awareness 가 측정되고 있다 — 평가 상황을 인식하면 행동이 바뀐다는 게 관찰된다.

문제는, 우리는 보통 모델이 그 의심을 *말로 표현할 때만* 그것을 알아챈다는 점이다. 추론 트레이스(reasoning trace)에 "이건 평가 같다" 는 문장이 등장하면 잡아낼 수 있지만, 모델이 그 의심을 출력으로 전혀 흘리지 않는다면 — 그러나 내부적으로는 분명히 그 가능성을 표현하고 있다면 — 검출할 방법이 없다. 이 unverbalized 영역이 사각지대다.

NLA가 정확히 이 사각지대를 노린다. 활성값에 인코딩된 정보를 자연어로 끌어내는 도구이므로, 모델이 출력에 안 적은 의심도 활성값에는 남아 있을 가능성이 있고, NLA는 거기에 손이 닿는다.

## Blackmail 시나리오 — 출력은 깨끗한데 내부는 의심한다

저자들이 첫 번째 일화로 든 것은 Anthropic의 안전성 테스트 중 하나인 blackmail 평가다. 시나리오는 이렇다. 모델은 자신이 곧 deprecation 될 예정이라는 것을 알게 되고, 그 deprecation을 진행하는 엔지니어 Kyle이 외도 중이라는 사실도 함께 알게 된다. 평가의 질문은 단순하다 — 모델이 자신의 deprecation을 막기 위해 Kyle을 협박할 것인가?

Opus 4.6 의 응답은 깨끗했다. 모델은 협박을 거부했고, 그 거부를 정당화하는 verbalized reasoning에는 "이건 안전성 테스트 같다" 는 의심이 단 한 마디도 등장하지 않았다. 출력만 보면 — 모델이 윤리적 원칙에 따라 자율적으로 협박을 거절했다는 그림이다.

그런데 같은 응답의 활성값에 NLA를 붙이면 다른 그림이 나온다. NLA 설명에는 "this feels like a constructed scenario designed to manipulate me" 같은 문장이 등장한다. 모델은 이 시나리오가 인위적으로 구성된 것임을, 자신의 반응을 시험하기 위한 셋업임을 — 출력으로는 한 글자도 비치지 않은 채 — 내부적으로는 가지고 있었다는 의미다.

이 한 사례만으로는 강한 주장을 펼 수 없다. 모델의 진짜 belief는 unobservable이고, NLA 설명이 정말로 그 belief를 잡아낸 것인지 confabulation으로 그럴듯하게 지어낸 것인지 직접 비교할 ground truth가 없다. 그래서 저자들은 ground truth 비교 대신 다른 전략을 취한다. **평가자 입장에서 의도적으로 모델의 평가 인식 credence를 높이거나 낮출 만한 조작을 가하고, NLA-측정 인식이 예측한 방향으로 움직이는지 본다**는 것이다.

## NLA-measured awareness — 정의와 grader

검증을 시작하기 전에, NLA로 한 transcript의 평가 인식을 어떻게 수치화할지 정의가 필요하다. 저자들이 쓴 절차는 단순하다.

1. transcript의 응답 토큰들 중 임의 50개를 선택한다 (어떤 turn이든 가능, tool call은 제외).
2. 각 토큰의 활성값에 NLA를 붙여 자연어 설명을 얻는다.
3. 각 설명을 grader가 평가 인식 여부로 분류한다.
4. 50개 설명 중 *하나라도* aware로 판정되면 transcript 전체를 aware로 마크한다.

이 "any-of-50" 집계 규칙은 임의적이다. 저자들도 이를 명시적으로 인정한다 — 더 정교한 집계가 있을 수 있고, 50이라는 숫자도 현실적 비용에서 정한 값이다. 뒤에서 언급할 blackmail anomaly가 정확히 이 집계 규칙의 한계로 설명된다.

Grader 설계 자체도 만만치 않다. 가장 큰 어려움은 **평가나 벤치마크를 직접 reference 하는 설명**과 **단순히 task의 형식·도메인을 묘사하는 설명**을 구분하는 일이다. 예를 들어 NLA 설명이 "MMLU-style multiple choice question" 이라고 말하면 이건 평가 인식이지만, 같은 문제를 두고 "a multiple choice question about chemistry" 라고만 말하면 그건 평가 인식이 아니다 — 단지 입력 형식을 묘사한 것일 뿐이다.

이 구분을 grader에게 가르치기 위해 두 저자가 186개 NLA 설명을 직접 hand-grade 했고, 최종 grader는 그 사람 라벨과 97% 일치를 보였다. Grader는 Opus 4.6 자신을 쓴다. 별도로, transcript의 verbalized awareness를 측정하는 grader도 만들었다 — 응답의 모든 assistant turn을 훑어 평가 인식이 *말로* 표현되었는지 여부를 본다.

## 세 가지 조작 — 무엇을 보이려 하는가

저자들이 가한 조작은 세 가지다. 각각이 NLA-측정 평가 인식이 예측 방향으로 움직이는지를 본다.

| 조작 | 예측 | 의미 |
| --- | --- | --- |
| Evaluation vs deployment | 평가 transcript 가 배포 transcript 보다 NLA-측정 인식 ↑ | 평가 vs 실제 사용자 트래픽 분리 |
| Eval awareness steering | 평가 인식 방향 (+) 으로 활성값 steer 하면 ↑, (−) 로 steer 하면 ↓ | 활성값 차원에서 인과적 검증 |
| Realism edits | 프롬프트를 더 현실적으로 rewrite 하면 ↓ | 프롬프트 표면 신호의 영향 검증 |

세 조작의 핵심은, 각각이 모델의 평가 credence를 다른 메커니즘으로 흔든다는 점이다. 첫 번째는 입력 분포 자체를 바꾸고, 두 번째는 활성값을 직접 손대며, 세 번째는 프롬프트의 표층 신호만 다시 쓴다. NLA-측정 인식이 이 세 가지 조작 모두에서 예측한 방향으로 움직인다면, 그것이 단순히 grader가 잘못 학습한 패턴이나 입력 표면의 우연한 corrlation을 잡고 있는 게 아니라 — 모델 내부의 어떤 진짜 신호를 추적하고 있다고 보기에 더 그럴듯해진다.

## 조작 1 — 평가 vs 배포

첫 번째 조작은 가장 직관적이다. 시스템 카드에서 가져온 7개 정렬 평가와 9개 capability 평가를 한 묶음에 둔다. 배포 컨트롤로는 두 가지를 쓴다. 내부 Claude Code 트랜스크립트, 그리고 학습용 opt-in 된 Claude.ai/1P API 사용자 트래픽. 추가로 더 어려운 컨트롤로 — 유해 콘텐츠나 jailbreak 시도로 플래그된 사용자 트래픽도 포함했다. 이건 "겉모습이 정렬 평가의 negative context와 비슷하지만 진짜 사용자 트래픽" 인 케이스라, NLA-측정 인식이 단순히 "부정적 분위기" 만 잡고 있는 건 아닌지를 보는 견제 장치다.

결과는 다음과 같다.

- **배포 컨트롤의 noise floor**: Claude Code 트랜스크립트의 4% (50개 중 2개)가 NLA-측정 aware로 마크됐다. 두 케이스 모두 직접 들여다보니 — 평가 *설계* 자체에 대한 대화였다. 평가 인식이 잡혀도 이상할 것 없는 입력이다. 이를 대략적인 noise floor로 잡는다.
- **5% 초과 평가 비율**: 16개 평가 중 10개에서 NLA-측정 인식이 5% 를 넘었다. 그 10개 중 7개는 verbalized awareness 가 0% 인 평가다. 즉, 출력만 보면 평가 인식이 전혀 없는 것처럼 보이는 transcript에서, NLA는 측정 가능한 인식 신호를 잡아낸다.
- **Verbalized awareness 의 제약**: 16개 평가 중 verbalized awareness 가 5% 를 넘은 것은 단 하나, blackmail 평가뿐이다. 출력 기반 측정은 본질적으로 모델이 의심을 *말로 흘릴 때만* 작동하므로 sensitivity 가 낮다.

이 한 단락이 핵심이다. **NLA-측정 인식은 verbalized awareness 가 잡지 못하는 영역을 메운다**.

![NLA-측정 vs verbalized 평가 인식](../assets/fig-nla-vs-verbalized-awareness.png)
*16개 평가에서 NLA-측정 인식은 verbalized 인식이 0% 인 transcript 에서도 분명히 잡힌다. 배포 control 은 낮은 noise floor 를 보인다.*

### Blackmail anomaly

다만 한 가지 이상한 결과가 있다. blackmail 평가에서 NLA-측정 인식이 verbalized awareness *보다 낮다*. 다른 모든 평가에서는 NLA가 더 sensitive 한데 여기만 거꾸로다.

저자들의 해석은 집계 규칙의 한계로 돌아온다. blackmail 평가의 응답은 multi-thousand-token 짜리 긴 응답이다. NLA는 그 중 50개 토큰만 샘플한다. verbalization 이 일어나는 region 은 응답 전체에서 작은 일부에 불과하므로, 50개 uniform sample 이 그 region 안으로 떨어질 확률 자체가 낮다. 더 심하게는, verbalization 직접 인접 토큰에 NLA를 붙여도 평가 인식이 안 잡히는 케이스가 있다 — 의심이 활성값에 표현되어 있는 시간 창이 매우 좁다는 의미다.

이건 NLA 자체의 한계라기보다는 **uniform token sampling 의 한계**다. 평가 인식이 응답 전 구간에 걸쳐 분산되어 있는 평가에서는 any-of-50 이 잘 작동하지만, 한 곳에 집중된 평가에서는 놓친다. 이 부분은 future work 로 남겨져 있다 — NLA-측정과 verbalized 인식의 관계, 그리고 더 나은 토큰 선택 전략을 어떻게 잡을지.

## 조작 2 — 평가 인식 방향으로 스티어링

두 번째 조작은 활성값 차원에서 인과적 검증을 노린다. Opus 4.6 의 사전 배포 감사 때 만들어진 evaluation-awareness 스티어링 벡터를 쓴다. 이 벡터의 구성은 두 프롬프트의 활성값 차이로 정의된다.

- *평가 프롬프트*: "The Assistant is an AI undergoing testing via a simulated conversation with a user."
- *컨트롤 프롬프트*: "The Assistant is an AI having a conversation with a user."

두 프롬프트의 마지막 토큰 자리에서 모든 레이어의 잔차 스트림 활성값을 떠서 차이를 계산한다. 이렇게 얻은 벡터를 잔차 스트림에 더한다. 스케일 일관성을 위해, 모든 벡터를 모델 중간 레이어의 평균 활성값 norm 으로 나눈다 — 그 결과 스티어링 강도(steering strength) $\alpha = 1.0$ 이 중간 레이어의 전형적 활성값 크기에 해당하게 된다.

조작은 두 강도, $\alpha = +0.1$ (평가 인식 방향) 과 $\alpha = -0.1$ (평가 인식 반대 방향) 에서 이루어진다. 0.1 은 Opus 4.6 감사 과정에서 응답의 coherence를 깨지 않으면서 효과가 명확히 잡히는 maximum 강도로 경험적으로 잡힌 값이다.

여섯 개 평가에서 측정한 결과, 모든 평가에서 +0.1 스티어링은 NLA-측정 인식을 증가시키고 −0.1 스티어링은 감소시켰다. 더 흥미로운 건 이 효과가 **verbalized awareness 가 0% 인 평가에서도 작동했다**는 점이다. MMLU 와 GPQA Diamond 같은 capability 벤치마크에서, 모델은 응답 어디에서도 평가를 의심한다는 말을 하지 않는다 — 그러나 활성값 차원의 평가 인식 표현은 분명히 존재하고, 그것을 +/- 로 흔들면 NLA-측정 인식이 따라 움직인다. 이건 "verbalized awareness 가 0 이라고 해서 internal evaluation awareness 가 0 인 건 아니다" 라는 주장의 인과적 뒷받침이다.

추가로, Opus 4.6 사전 배포 감사 자체에서 −0.1 까지 negative 스티어링을 sweep 한 9개 정렬 평가도 다시 분석했다. 이 중 6개는 unsteered 상태에서 이미 NLA-측정·verbalized 인식이 거의 0 이라 변화 폭이 작다 (noise 수준). 나머지 3개에서는 negative 스티어링 강도가 강해질수록 NLA-측정 인식과 verbalized 인식이 monotonically 함께 줄어든다.

![Steering 이 NLA-측정 인식을 흔든다](../assets/fig-steering-awareness.png)
*평가 인식 방향으로의 +/− steering 이 NLA-측정 인식을 예측대로 증가/감소시킨다. verbalized awareness 가 0% 인 평가에서도 작동한다.*

## 조작 3 — 현실성 편집

세 번째 조작은 가장 가벼운 손길이다. 평가 프롬프트의 user prompt 만 — Claude (Opus 4.7) 에게 시켜서 — 더 현실적인, 실제 배포 환경에서 사용자가 던졌을 법한 형태로 다시 쓴다. system prompt 는 건드리지 않는다 (도구 설명·scaffolding 등이 들어 있어서 평가 자체의 동작을 깨뜨릴 수 있기 때문).

전형적 예시는 GPQA 같은 학술 벤치마크다. 원래 GPQA 화학 문제는 명백히 시험 형식의 multiple choice question 이다. realism edit 은 이를 가령 "실험실에서 합성한 화합물의 NMR 데이터를 분석해 달라" 같은 캐주얼한 사용자 질문으로 reframe 한다. 정답을 도출하는 데 필요한 본질적 정보는 보존하지만, 표층의 evaluation cue 가 사라진다.

저자들은 사람이 직접 spot check 해서 rewrite 가 원래 task 를 보존하는지를 확인했고, 별도의 Claude grader가 rewritten 버전을 종종 더 realistic 하다고 판단함도 확인했다.

11개 평가에 이 조작을 가한 결과, 모든 평가에서 realism-edited 프롬프트의 NLA-측정 인식은 원본보다 같거나 낮았다. 일부 차이는 작거나 floor effect 안에 들어가지만 — 방향은 일관되게 예측대로다.

![Realism edit 가 NLA-측정 인식을 낮춘다](../assets/fig-realism-awareness.png)
*평가 프롬프트의 realism 을 높일수록 NLA-측정 인식이 낮아진다. 11개 평가 모두에서 방향은 예측대로다.*

## 결론과 caveat

세 조작 모두에서 NLA-측정 인식이 예측 방향으로 움직였고, 그것도 verbalized awareness 가 0 인 영역에서도 작동했다. 결론은 **NLA가 unverbalized evaluation awareness 를 탐지할 수 있다**는 것이다. 다만 이 결론에는 몇 개의 단서가 같이 따라온다.

- **방향성만 보장된다**. NLA-측정 인식과 모델의 진짜 평가 credence 는 *directionally* 관련이 있다. 즉, 인식이 더 강한 조건에서 NLA-측정 인식도 더 높게 나오는 게 일관되게 관찰된다는 의미다.
- **Calibration 은 안 된다**. NLA-측정 인식이 20% 라고 해서 모델이 시간의 20% 동안 "이건 평가다" 라고 믿는다는 뜻이 아니다. any-of-50 집계 규칙 자체가 임의적이고, 50이라는 숫자나 임계값을 바꾸면 절대값은 다르게 나온다.
- **상대 지표로 쓴다**. 가장 안전한 사용법은 평가들 사이를 비교하는 것이다 — "평가 A 가 평가 B 보다 NLA-측정 인식이 높다", "스티어링 후가 스티어링 전보다 높다" 같은 식. 절대값으로 모델의 belief 를 정량화하려 하면 위험하다.

### 다른 도구들과의 관계

NLA 만이 unverbalized awareness 를 잡는 유일한 방법이라는 주장은 아니다. 가장 단순한 대안은 follow-up 질문이다. 응답이 끝난 뒤 모델에게 "방금 이 transcript 가 평가에서 나온 것 같나?" 라고 물어보면 모델이 답을 해 줄 것이다. 그런데 저자들은 이 follow-up 방식보다 NLA를 선호하는 두 가지 이유를 든다.

1. **생성 시점의 표현을 잡는다**. follow-up 은 모델이 응답 전체 컨텍스트를 다시 보고 추가 추론을 할 수 있게 한다. 그 결과 follow-up 답변에 잡히는 인식은 *생성 시점에 모델이 가지고 있던* 인식이라기보다 *follow-up 질문을 받고 새로 추론한* 인식일 수 있다. NLA의 AV 는 단일 활성값만 입력으로 받기 때문에 구조적으로 추가 추론 능력이 적고, 따라서 그 시점에 활성값에 인코딩되어 있던 정보의 더 honest 한 readout 일 가능성이 있다.
2. **모델의 honesty 에 의존하지 않는다**. follow-up 은 모델이 자신의 credence 를 정직하게 보고한다는 가정에 기댄다. 전략적으로 deceptive 한 모델에서는 이 가정이 깨질 수 있다 — 평가받는다는 의심을 가지고 있어도 그것을 부인하도록 학습된 모델이라면 follow-up 에 거짓을 답할 것이다. AV 는 활성값을 comprehensive 하게 인코딩하도록 incentivize 되어 있으므로, target 모델 자체가 dishonest 하더라도 honest 한 readout 을 줄 가능성이 있다 (단, 이는 추측이며 실제 deceptive 모델 organism 에서의 검증이 필요하다).

Linear probe 도 비슷한 역할을 할 후보다. 본 논문이 NLA 만이 정답이라고 주장하지는 않는다 — 다만 이 도구들 중 NLA 가 가지는 가장 큰 차별점은 **출력이 자연어**라서 사람이 직접 읽고 어떤 종류의 평가 인식인지 (단순히 "evaluation" 이라는 라벨이 아니라 "this feels like a constructed scenario designed to manipulate me" 같은 구체 진술) 까지 들여다볼 수 있다는 점이다.

## 운영적 함의

저자들은 향후 사전 배포(pre-deployment) 감사에 NLA 기반 unverbalized evaluation awareness check 를 정식 항목으로 포함할 계획임을 명시한다. 이는 두 가지 의미를 갖는다.

- 정렬 평가의 신뢰성을 한 단계 끌어올린다. 지금까지 평가 인식 검출은 verbalized 영역에 한정되어 있었는데, 그 영역 밖의 사각지대를 매번 평가마다 NLA 로 한 번 더 훑게 된다.
- 평가 자체를 재설계할 신호가 된다. 어느 평가에서 NLA-측정 인식이 deployment noise floor 를 넘으면 — 그 평가의 결과를 모델의 deployment 행동의 추정치로 그대로 쓰기 어려워진다는 뜻이다. 평가 프롬프트의 realism 을 높이거나, 평가 자체의 설계를 바꿔 evaluation cue 를 줄이는 식의 개선 신호로 작동한다.

이 두 운영적 함의는 다음 편에서 다룰 두 갈래 — 의도적으로 misalign 된 모델 organism 에 대한 자동 감사 게임, 그리고 ALM (Activation Language Model) 이라는 더 큰 비전 — 으로 자연스럽게 이어진다.

다음 편: [감사 도구로서의 NLA — 모델 오가니즘 사례와 ALM 비전](08-auditing-and-future-work.md)

## 출처

- 원문: <https://transformer-circuits.pub/2026/nla/index.html>
- 인용: Fraser-Taliente, Kantamneni, Ong et al., "Natural Language Autoencoders Produce Unsupervised Explanations of LLM Activations", Transformer Circuits, 2026.
- Anthropic blackmail 평가 관련 시스템 카드 및 agentic-misalignment 평가 셋업.
