---
title: AI는 AI 개발을 얼마나 가속하고 있는가
date: 2026-06-05
author: 김세형
tags: [agents, recursive-self-improvement, ai-research, anthropic]
source: https://www.anthropic.com/institute/recursive-self-improvement
summary: Anthropic은 외부 벤치마크와 내부 개발 데이터를 근거로 AI가 이미 AI 개발을 가속하고 있으며, 병목이 실행에서 연구 판단과 사회적 조율로 이동하고 있다고 주장한다.
format: abstract
---

# AI는 AI 개발을 얼마나 가속하고 있는가

> 원본: [Anthropic Institute](https://www.anthropic.com/institute/recursive-self-improvement)

Anthropic Institute의 글은 recursive self-improvement를 미래의 추상적 가능성으로만 다루지 않는다. Claude가 실제 AI 개발 조직 안에서 코드 작성, 실험 실행, 연구 판단의 일부를 얼마나 대체하고 있는지 외부 벤치마크와 내부 데이터를 묶어 보여주고, 이 변화가 어디서 멈출지 또는 어디까지 이어질지 묻는다.

## 핵심 포인트

- AI가 안정적으로 수행할 수 있는 작업 길이는 최근 4개월마다 두 배로 늘고 있으며, coding/research benchmark도 빠르게 포화되고 있다는 것이 Anthropic의 출발점이다.
- Anthropic 내부에서는 2026년 5월 기준 병합되는 코드의 80% 이상이 Claude 작성으로 집계되며, 2026년 2분기 엔지니어 1인당 병합 코드량은 2024년 대비 약 8배로 늘었다고 한다.
- 코드 작성의 병목은 타이핑에서 목표 설정과 리뷰로 이동했다. Claude Code session success rate, 자동 코드 리뷰, 장시간 디버깅 사례는 이 전환을 보여주는 내부 증거로 제시된다.
- 연구 쪽에서도 Claude는 명확히 주어진 목표를 향해 실험을 실행하고 최적화하는 작업에서는 이미 강하지만, 어떤 문제를 선택할지와 어떤 결과를 믿을지 같은 연구 판단은 아직 사람의 비교우위로 남아 있다.
- Anthropic은 가능한 미래를 세 가지로 나눈다. 추세가 정체되는 세계, 사람은 방향을 잡고 AI가 실행을 대부분 담당하는 세계, 그리고 AI가 자기 후속 모델까지 설계하는 완전한 recursive self-improvement 세계다.
- 글의 정책적 결론은 단순한 낙관이나 비관이 아니라, 필요하면 frontier AI 개발을 늦추거나 멈출 수 있는 검증 가능한 조율 체계를 지금부터 만들어야 한다는 주장이다.

## 한 페이지 요약

이 글에서 말하는 recursive self-improvement는 한 모델이 자기 코드를 조금 고치는 수준이 아니다. 충분한 compute와 도구 접근을 가진 AI 시스템이 다음 세대 모델을 설계하고, 학습시키고, 평가하고, 다시 개선하는 루프를 스스로 닫는 상태를 가리킨다. Anthropic은 아직 그 지점에 도달하지 않았고 필연적이라고도 말하지 않는다. 다만 AI가 AI 개발 과정의 점점 더 큰 부분을 맡고 있다는 증거가 빠르게 쌓이고 있으므로, 이를 제도와 안전성 논의의 중심에 올려야 한다고 본다.

원문은 먼저 외부 지표를 든다. METR의 long-horizon task 측정에서는 AI가 안정적으로 처리할 수 있는 작업 시간이 빠르게 늘고 있고, SWE-bench와 CORE-Bench 같은 coding/research benchmark는 불과 1~2년 사이 낮은 점수에서 포화권으로 이동했다. 이 지표들만으로는 AI가 실제 AI 연구소의 생산성을 얼마나 바꾸는지 알 수 없지만, 적어도 모델이 더 긴 작업과 더 복잡한 재현 과제를 수행할 수 있게 되었음을 보여준다.

Anthropic 내부 데이터는 더 직접적이다. 글에 따르면 2026년 5월 기준 Anthropic 코드베이스에 병합되는 코드의 80% 이상이 Claude가 작성한 것으로 집계된다. Claude Code가 2025년 2월 research preview로 출시되기 전에는 이 비중이 한 자릿수였고, 2026년 2분기에는 엔지니어 1인당 하루 병합 코드량이 2024년 대비 약 8배까지 올라갔다고 한다. 이 수치는 코드 품질까지 곧장 말해주지는 않지만, 엔지니어가 직접 타이핑하는 양보다 AI에게 목표를 주고 검토하는 양이 생산량을 결정하는 단계로 넘어갔다는 신호로 읽힌다.

![Anthropic 내부 코드 생산량 추이](assets/fig-1.png)

*Figure 1. Anthropic이 공개한 엔지니어 1인당 코드 기여량 추이. Claude Code와 장시간 자율 작업 모델 접근 시점 이후 생산량 기울기가 달라졌다는 점을 강조한다.*

중요한 부분은 "코드를 많이 썼다"에서 끝나지 않는다. Anthropic은 Claude가 작성한 코드가 작동하는지, 사람이 이어받아 이해할 수 있는지, 연구 실험의 다음 단계를 스스로 제안할 수 있는지도 별도로 본다. Claude Code session success rate는 복잡하고 열린 문제에서도 개선되고 있고, 자동 Claude reviewer는 과거 claude.ai incident의 약 1/3을 사전에 잡았을 것이라는 retrospective 분석도 제시된다. 연구 실험에서는 주어진 objective와 metric이 명확할 때 Claude가 반복 실험을 실행해 시작 코드 대비 약 52배 speedup을 달성했다는 내부 평가가 나온다.

하지만 글은 현재 병목을 분명히 남긴다. 지금 Claude가 특히 잘하는 것은 실행이다. 코드를 쓰고, 돌리고, 실패를 보고, 다시 고치고, 여러 실험을 병렬로 밀어붙이는 일이다. 반면 어떤 문제를 풀어야 하는지, 어떤 결과가 신뢰할 만한지, 어느 접근이 막다른 길인지 판단하는 능력은 여전히 사람 쪽에 있다. Anthropic이 말하는 recursive self-improvement의 핵심 위험과 기회는 바로 이 경계가 앞으로도 유지될지, 아니면 "research taste" 역시 다른 능력처럼 어느 순간 모델이 따라잡을지에 있다.

가능한 미래는 세 갈래다. 첫째, 지금의 추세가 S-curve처럼 꺾여 모델 능력이 정체될 수 있다. 둘째, 완전한 자기개선은 아니더라도 AI 연구소와 지식노동 조직이 복리적으로 효율화될 수 있다. 이 경우 사람은 방향을 정하고 AI는 대부분의 실행을 담당한다. 셋째, AI 시스템이 자기 후속 모델을 설계하고 개발하는 완전한 recursive self-improvement가 가능해질 수 있다. 세 번째 세계에서는 인간의 역할이 개발 자체보다 oversight, validation, verification으로 밀려날 가능성이 크다.

Anthropic의 결론은 준비 시간에 관한 것이다. 기술을 늦추는 선택지가 사회적으로 유용할 수 있지만, 한 회사만 멈추는 것은 경쟁자에게 선두를 넘기는 결과가 될 수 있다. 따라서 의미 있는 slowdown 또는 pause는 여러 국가와 여러 frontier lab이 같은 조건에서 멈추고, 서로가 실제로 멈췄는지 확인할 수 있는 검증 체계를 필요로 한다. 문제는 AI training run이 미사일 사일로보다 훨씬 숨기기 쉽고, compute와 전력과 데이터가 범용 자원이기 때문에 검증 난도가 높다는 점이다. 원문은 이 조율 문제를 앞으로 몇 달 동안 더 공개적으로 논의하겠다고 마무리한다.

## 자세히 보기

<!-- VERSIONS_START -->
1. [재귀적 자기개선은 어디까지 왔나](details/01-where-recursive-self-improvement-stands/) — 외부 벤치마크와 Anthropic 내부 생산성 지표가 AI 개발 자동화의 초기 단계를 어떻게 보여주는지 정리한다.
2. [코드, 실험, 연구 판단으로 좁혀지는 병목](details/02-code-experiments-research-judgment/) — Claude가 코드 작성, 코드 품질, 실험 실행, 연구 세션의 다음 행동 판단에서 어디까지 역할을 넓혔는지 본다.
3. [세 가지 미래와 조율의 문제](details/03-futures-and-coordination/) — 추세 정체, 복리적 효율 향상, 완전한 재귀적 자기개선이라는 세 시나리오와 Anthropic이 제안하는 대응을 정리한다.
<!-- VERSIONS_END -->

## 출처

- https://www.anthropic.com/institute/recursive-self-improvement
