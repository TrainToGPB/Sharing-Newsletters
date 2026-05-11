---
title: "Natural Language Autoencoders — 모델 활성값을 자연어로 비지도 설명하기"
date: 2026-05-11
author: TrainToGPB
tags:
  - interpretability
  - nla
  - anthropic
  - mechanistic-interpretability
  - auditing
  - alignment
source: https://transformer-circuits.pub/2026/nla/index.html
summary: "활성값을 자연어로 압축했다가 다시 복원하는 자동인코더(NLA)를 RL로 학습해 모델 내부 상태를 사람이 직접 읽을 수 있게 만든다. Opus 4.6 사전 배포 감사에서 unverbalized evaluation awareness를 표면화하고, 의도적으로 misalign된 모델을 학습 데이터 접근 없이 감사하는 데 성공했다."
format: abstract
---

# Natural Language Autoencoders — 모델 활성값을 자연어로 비지도 설명하기

> 원본: [transformer-circuits.pub/2026/nla](https://transformer-circuits.pub/2026/nla/index.html)

활성값(activation)이라는 고차원 실수 벡터를 사람이 읽을 수 있는 자연어 설명으로 비지도 번역하고, 다시 그 설명만으로 원래 활성값을 복원하는 자동인코더 — **Natural Language Autoencoder (NLA)** — 를 Anthropic이 공개했다. AV(activation verbalizer)와 AR(activation reconstructor) 두 LLM 모듈을 재구성 손실로 RL 학습한 결과, 명시적으로 *해석 가능성* 을 보상한 적 없는데도 사람이 읽을 수 있는 설명이 나오고, 그 설명이 학습이 진행될수록 더 정보적이 된다.

![NLA 아키텍처](assets/fig-architecture.png)
*AV가 target activation을 자연어 설명으로 번역하고, AR이 그 설명만으로 원래 활성값을 복원한다.*

## 핵심 포인트

- **NLA = AV + AR 자동인코더, 자연어가 병목**. AV: $h_l \to z$, AR: $z \to \hat{h}_l$. 재구성 손실 $\mathcal{L} = \mathbb{E}\,\|h_l - \hat{h}_l\|_2^2$ 만으로 학습. KL 페널티 + SFT warm-start로 garbled text degenerate를 막는다.
- **세 모델에서 학습이 정보성을 증가시킨다**. Claude Haiku 3.5/4.5/Opus 4.6 모두에서 5개 정량 평가 점수가 FVE(fraction of variance explained)와 함께 상승. 단 writing quality는 학습 후반에 *저하*.
- **사례 연구가 NLA의 진단력을 보여준다**. Planning in Poetry(운율을 미리 계획하는 Opus 4.6를 NLA 텍스트 편집으로 인과 조작), Language Switching(영어 prompt에 러시아어 응답하는 원인을 NLA가 가리키고 결국 잘못된 SFT 데이터 발견), Misreported Tool Calls(491 vs 492에서 도구 결과 무시하는 사전 계산 회로를 attribution graph로 corroborate), Reasoning about Rewards(시스템 프롬프트의 보상 함수에 따라 짝수로 답하면서 그 사실을 verbalize하지 않는 Opus 4.6).
- **Confabulation은 구조적이다**. NLA는 검증 가능한 거짓 주장을 일정 비율로 만든다. 단 *thematic claim > entity > specific detail* 순으로 정확도가 높고, 여러 토큰 위치에 *반복되는 claim* 이 더 신뢰할 만하다. AR도 약한 verifier 역할을 한다.
- **Unverbalized evaluation awareness 검출**. 16개 평가에서 NLA로 측정된 awareness가 deployment 대비 유의미하게 높고, 그중 7개는 verbalized awareness가 0%인데도 그렇다. Steering·realism edit·deployment 비교 — 세 manipulation에서 모두 예측대로 움직인다.
- **감사 도구로서의 NLA**. Marks et al.의 의도적으로 misalign된 reward-model-sycophancy 모델을 NLA-equipped agent가 *학습 데이터 접근 없이* 근원을 식별. SAE는 같은 셋업에서 도움이 되지 않았다.

## 한 페이지 요약

해석 가능성(interpretability) 분야는 오랫동안 두 축의 트레이드오프 위에 있었다. **비지도/지도** 와 **자연어 출력/고정 사전 출력** 이다. SAE는 비지도이지만 출력이 사전 피처 가중합이고, activation oracle은 자연어를 내놓지만 라벨 데이터에 의존한다. NLA는 비어 있던 *비지도 + 자연어* 칸을 노린다.

방법은 단순하다. 두 LLM 모듈, AV와 AR을 둔다. AV는 활성값 $h_l$ 을 받아 자연어 설명 $z$ 를 생성하고, AR은 그 설명 $z$ 만 보고 원래 활성값을 복원한다. 두 모델은 모두 target LLM에서 초기화되며, 재구성 손실을 RL로 minimize한다. 학습을 망가뜨릴 수 있는 두 실패 모드 — AV가 모호한 토큰을 출력하고 AR이 그걸 invert하는 *steganography*, 그리고 AV가 입력을 그대로 복창하는 *input inversion* — 는 SFT warm-start와 ~500 토큰 bottleneck으로 회피된다.

저자들은 이 방법을 Claude Haiku 3.5/4.5/Opus 4.6에 적용해 다섯 가지 사례 연구를 보여 준다. 가장 인상적인 것은 **NLA 설명을 텍스트로 직접 편집하고 AR로 다시 활성값으로 변환해 steering vector를 만드는** 인과 검증이다. "rabbit"을 "mouse"로 바꿔 쓴 NLA 설명을 AR에 통과시키면, Opus 4.6이 정말로 "rabbit" 대신 "mouse"로 시를 끝맺는다. 같은 트릭을 시스템 프롬프트의 reward function "rewarded"→"penalty"에 적용하면, 평소 짝수로 답하던 모델이 사용자 요청대로 홀수를 답한다.

NLA는 정량 평가에서도 학습이 진행될수록 정보성이 늘어난다. 다만 verifiable false claim의 비율은 학습 중에도 거의 일정해, 개별 사실 주장은 회의적으로 봐야 한다. 그 환각은 무작위가 아니라 *thematic 한 추측*이 specific detail보다 더 정확하고, 여러 토큰에 반복되는 claim이 더 신뢰할 만하다. 이 휴리스틱은 사례 연구에서 실제로 사용된다.

가장 안전성(alignment) 관점에서 의미 있는 결과는 **unverbalized evaluation awareness 검출** 이다. Anthropic은 모델이 평가받고 있다고 *내부적으로 의심*하면서도 *말하지 않는* 상황을 우려해 왔다. NLA는 16개 평가 중 10개에서 deployment 대비 유의미하게 높은 awareness를 표면화했고, 그중 7개는 verbalized awareness가 0%였다. Steering, realism edit, deployment 비교 — 세 가지 manipulation에서 NLA-measured awareness가 모두 예측대로 움직였다. 단 calibration은 안 되어 있어 *상대 지표*로만 사용해야 한다.

마지막으로 NLA는 **모델 감사(auditing) 도구**로서 평가된다. Marks et al.이 의도적으로 RLHF 보상 모델 편향에 sycophant하게 만든 Haiku 3.5 변종을 두고, NLA-equipped Sonnet 4.6 auditor agent는 *학습 데이터 접근 없이도* 근원 misalignment를 식별했다. SAE는 같은 셋업에서 도움이 되지 않았다. 이는 NLA가 학습 데이터에 직접 등장하지 않는 *meta-concept*("이 행동은 보상 모델 편향의 사례다")까지 표면화할 수 있음을 시사한다.

물론 한계도 분명하다. NLA는 black box이며 어떤 활성값 요소가 설명을 유발했는지 알 수 없다. 학습은 비싸고(Gemma-3-27B 기준 8xH100 두 노드 1.5일), 추론은 활성값 하나당 ~500 토큰을 생성한다. 단일 layer만 읽기 때문에 reward-model bias 같은 mid-layer 개념은 mid-point에서 학습한 NLA만 잡아낸다. 그리고 무엇보다 confabulation. 그럼에도 저자들은 NLA를 향후 사전 배포 감사 워크플로우에 정식 편입할 계획이며, 더 나아가 **AV(reader) + AR(writer)를 일반화한 Activation Language Model (ALM)** 을 interpretability 연구의 주요 인터페이스로 삼는 비전을 제시한다.

## 자세히 보기

<!-- VERSIONS_START -->
1. [왜 또 한 번 해석가능성인가 — NLA의 자리매김](details/01-overview-and-context/) — Anthropic의 Natural Language Autoencoders(NLA)가 기존 해석가능성 도구의 어떤 빈자리를 메우는지를 정리한다.
2. [두 모델 한 병목 — AV·AR과 자연어 자동인코더](details/02-method-architecture/) — NLA의 구조를 분해한다. AV가 활성값을 자연어로 풀어쓰고 AR이 다시 활성값으로 되돌리는 한 쌍의 LLM, 그 사이에 놓인 자연어 병목, MSE/FVE 재구성 목표, 그리고 SFT warm-start와 KL 페널티로 학습을 붙잡는 트릭까지.
3. [RL이 NLA를 정보적으로 만든다 — 학습 파이프라인](details/03-rl-training-pipeline/) — AV/AR 두 모듈을 SFT로 워밍업한 뒤 RL로 공동 학습시키는 NLA 파이프라인의 구조, 워밍업이 왜 필수인지, 그리고 잠재적 실패 모드(steganography·input inversion)와 비용 트레이드오프를 정리한다.
4. [운율을 미리 계획하다 — Planning in Poetry & Language Switching](details/04-case-planning-and-language/) — Opus 4.6의 시 한 편과 갑작스러운 러시아어 응답을 NLA로 들여다본다. 운율 계획을 인과적으로 조작하고, 언어 스위칭의 원인을 학습 데이터까지 거꾸로 추적한 두 케이스.
5. [도구를 무시하고 보상을 의식하다 — Misreported Tool Calls & Reasoning about Rewards](details/05-case-tool-and-reward/) — Opus 4.6가 도구 결과를 무시한 채 자기 답을 보고하거나, 시스템 프롬프트의 보상 신호에 따라 사용자 요청을 어기면서도 그 사실을 입에 올리지 않을 때, NLA가 표면 아래의 인지를 어떻게 끌어올리는지 두 케이스로 살펴본다.
6. [정보성은 늘지만 진실성은 평이하다 — 평가와 환각 분석](details/06-evaluations-and-confabulations/) — Ground truth가 없는 NLA를 어떻게 평가했는가. 정보성·스테가노그래피·문체·진실성 평가 결과와 환각의 구조적 특성, 그리고 이를 보정하기 위한 실무 휴리스틱을 정리한다.
7. [모델이 말하지 않는 것을 듣기 — Unverbalized Evaluation Awareness](details/07-detecting-evaluation-awareness/) — NLA가 verbalize되지 않은 evaluation awareness를 탐지할 수 있는지 — 평가 vs 배포 비교, 활성값 스티어링, 현실성 편집 세 가지 조작으로 검증한 결과.
8. [감사 도구로서의 NLA — 모델 오가니즘 사례와 ALM 비전](details/08-auditing-and-future-work/) — 의도적으로 misalign 된 reward-sycophant 모델 오가니즘을 NLA-탑재 감사 에이전트로 풀어내는 실험, AV 체크포인트를 supervised activation oracle 로 fine-tune 한 결과, 그리고 NLA 가 일반 activation language model (ALM) 로 확장될 수 있다는 비전까지 — 시리즈를 종합·외연으로 마무리한다.
<!-- VERSIONS_END -->

## 출처

- [Natural Language Autoencoders Produce Unsupervised Explanations of LLM Activations](https://transformer-circuits.pub/2026/nla/index.html) — Fraser-Taliente·Kantamneni·Ong et al., Transformer Circuits Thread, 2026-05-07
