---
title: 평가, 한계, 시사점
date: 2026-05-10
author: TrainToGPB
tags: [agents, frontiermath, agentic-design]
source: https://arxiv.org/html/2605.06651
summary: 내부 100문항 / FrontierMath Tier 4 결과, 실제 미해결 문제 케이스, 4가지 한계와 3가지 시스템 위험, 사내 LLM 도구 디자인에의 시사점.
format: details
part: 5
---

# 평가, 한계, 시사점

[4편](04-walkthrough/) 까지 본 4계층 + 5단계 흐름 위에서 시스템이 실제 무엇을 했는지, 어디서 무너지는지, 우리에게 어떤 의미인지를 짚는다.

## 평가의 기본 입장

저자들은 *human-in-the-loop 가 디폴트* 라는 자기 디자인 원칙을 평가에도 적용한다. 그래서 결과 보고 순서가.

1. **수학자가 직접 시스템을 사용해 얻은 실제 연구 성과** (논문 §5)
2. **정적 문제 풀이 벤치마크** (§6)

이 순서 자체가 메시지 — *최종 답을 빨리 만들어내는 능력* 만이 아니라 *협업 효율* 을 우선시한다는 입장.

## 5.1 실제 미해결 문제 케이스

DeepMind 가 소수의 수학자에게 시스템 접근을 열었고, 그들이 *GDM 연구진의 supervision 없이 독립적으로* 작업해 얻은 결과들.

| 케이스 | 도메인 | 결과 |
| --- | --- | --- |
| Kourovka Problem 21.10 | Group theory | 미해결 문제 해결 |
| Stirling Coefficients | Combinatorics | 추측에 대한 증명 |
| Hamiltonian Systems | Dynamical systems | 보조정리 증명 |

저자들 명시 — *"많은 사용자가 시스템과 성공적으로 상호작용하며 새로운 발견에 이르렀지만, 다른 사용자는 자기 작업에 덜 효과적이라 느꼈다"*. 사용 만족도에 range 가 있음을 인정. 이 경험을 향후 벤치마크·개발 방향에 사용하겠다고 밝힘.

## 5.2 내부 100문항 벤치마크 (논문 §6.1)

전문 수학자가 출제한 *unleaked, research-level* 100개 문제, 코드로 답이 검증 가능. 같은 베이스 모델을 단발 호출했을 때와의 격차가 가장 직관적.

![internal benchmark bar chart](../assets/fig-5.png)
*100문항 내부 벤치마크. Gemini 3.1 Pro 57%, Gemini 3.1 Deep Think 70%, AI Co-Mathematician 87% (Gemini 3.1 Pro + Deep Think 활용).*

**핵심 관찰**: 모델이 강해진 게 아님. 같은 Gemini 3.1 Pro·Deep Think 를 부품으로 쓰면서 위에 *워크스트림 분기 + 도구 사용 + 리뷰 사이클* 을 얹는 것만으로 격차가 두 자릿수 %p 만큼 벌어짐. 시스템 디자인이 모델 교체보다 큰 레버일 수 있다는 신호.

**컴퓨트 비용 caveat**: AI Co-Mathematician 은 더 많은 컴퓨트를 사용. 내부 sub-agent 들이 Gemini 3.1 Pro 위에서 돌고, prover sub-agent 는 Gemini 3.1 Deep Think 까지 활용.

## 5.3 FrontierMath Tier 4 (논문 §6.2)

외부 평가. Epoch AI 가 직접 UI 에 문제를 입력·답을 회수, 개발팀은 *blind* (문제를 못 봄, workspace state 도 못 봄).

**Tier 4 자체**: Epoch AI 표현 — *"50개 문제로 구성된 extreme tier. 교수·박사후연구원이 short-term research project 로 짜낸 것들. Tier 3 보다 어렵고 일부는 수십 년간 AI 가 못 풀 거라 분류된 것들"*.

**결과**.

| 시스템 | 점수 | 비고 |
| --- | --- | --- |
| AI Co-Mathematician | 23 / 48 = 48% | 평가된 시스템 중 새 SOTA |
| Gemini 3.1 Pro (베이스) | 19% | 단발 호출, 같은 벤치마크 |
| Gemini 2.5 Deep Think | (이하) | web UI 평가, 별도 harness 없음 |

48문제는 50개 중 공개 sample 2개를 뺀 것.

저자들 강조 — *맞춘 23개에는 이전 어떤 시스템도 못 푼 3개가 포함*. 동시에 *이전에 적어도 한 시스템이 푼 2개는 못 풀었음*. 즉 새로 열린 문제도 있고 후퇴한 문제도 있음. 합이 19% → 48%.

**평가 환경 caveat**.

- 표준 FrontierMath 평가는 Epoch AI 가 만든 *standard agentic harness* 사용 — Python interpreter 접근 + agent trajectory 토큰 hard limit
- AI Co-Mathematician 평가는 *자체 도구 사용 + model call·token 제한 없음*
- → 추론 비용이 더 높음, 단순 비교가 아님
- 그러나 같은 Tier 4 문제집에서 19% → 48% 격차 자체는 *시스템 디자인 효과* 로 보는 게 합리적

## 5.4 한계 — 저자들이 직접 짚는 4가지 (논문 §7)

논문에서 가장 솔직한 부분 중 하나.

### 1. Reviewer-Pleasing Bias (False Consensus)

- 리뷰어 에이전트가 잡지 못하는 결함이 있는 논증으로 시스템이 수렴
- 사람이 봐도 잡기 어려운 종류 — 깔끔한 LaTeX 외양에 묻혀 있음
- *원칙 6 (불확실성 인정)* 의 위반이지만 드물게 발생
- 관련 문헌: prover–verifier dynamics 의 알려진 pathology

### 2. Intractable Disagreements / Non-Termination ("Death Spiral")

- 리뷰·재작성·재거절이 끝없이 도는 경우
- 모델끼리 의견 안 맞으면 환각이 늘며 무한 루프
- 완화 메커니즘 있지만 핵심 이슈 (LLM 사이 빈번한 disagreement) 는 남음
- 초기 사용자들은 워크스트림이 이 상태에 빠진 걸 *학습* 해 결과 신뢰도를 down-weight

### 3. System Autonomy Requires Ceding Control

- 수학 연구는 본질적으로 exploratory — predefined task planning 이 종종 불가능
- 모델이 unplanned-for difficulty 를 만났을 때 판단력이 사람에 한참 못 미침
- 시스템이 사용자 입력 없이 몇 시간씩 자율적으로 도는 동안 점진적 흔들림 위험
- *long-running 자율성 ↔ 사용자 controllability* 의 균형이 어려움

### 4. Semantic Meaning of Representations

- 잘 조판된 LaTeX 가 만드는 가짜 엄밀성 — *내용의 rigor* 와 *외양의 polished* 가 LLM 에서는 분리됨
- working document 표시·marginalia 로 완화 시도하지만 충분치 않음을 인정
- HCI 연구에서 더 나은 인터페이스가 나올 수 있다고 봄

## 5.5 시스템 차원 위험 — 학계 생태계에 미치는 영향

저자들이 동시에 짚는 더 큰 그림의 위험들.

### 문헌 시그널-노이즈 비

- AI 가 LaTeX 생성·문헌 종합에 능숙해질수록 *그럴듯하지만 얕거나 미세하게 결함 있는 논문* 의 자동 생성 증가 가능
- 새로운 진짜 발견을 식별하는 휴리스틱 발전 필요
- formal methods·auto-formalization 이 정확성 체크엔 도움될 수 있지만 *연구 결과 이해와 흡수* 까지 대신해주진 않음

### Peer Review 부담 비대칭

- 시스템은 분 단위로 20쪽 증명 시도를 만듦, 사람 검증은 며칠 걸림
- AI 보조 작성이 *built-in auditable paper trails* 없이 ubiquitous 해지면 자원봉사형 peer review 가 무너짐
- 이 시스템의 marginalia 가 audit 첫 발걸음이지만, 더 넓은 community standards 필요

### AI Reviewer 과의존

- 시스템 안의 자동 리뷰어가 local logical check, 대수 실수, 누락 인용에는 강함
- 그러나 *우아함, 깊이, 진짜 수학적 의미* 같은 holistic 판단엔 약함
- AI 를 사람 referee 대체로 쓰면 mathematical evaluation 이 mechanical verification 으로 환원됨

## 5.6 우리에게의 시사점

사내 LLM 도구 디자인 입장에서.

### 자동화 비율 < 개입 위치

- "에이전트가 끝까지 혼자 푼다" 보다 "사람이 늘 옆에 있는 비동기 워크벤치" 가 더 멀리 감
- 자동화 수준을 무조건 높이는 게 답이 아님
- 사용자 개입 *위치·빈도* 의 정교한 설계가 자동화 비율보다 큰 레버일 수 있음

### 실패 보존 패턴은 보편

- 수학뿐 아니라 코드·문서 작업에 그대로 차용 가능
- 우리 코딩 에이전트는 실패 시도를 거의 휘발 — 이 패턴 도입 시 *"왜 이 길이 막혔는지"* 가 다음 시도의 직접 입력이 됨

### 시스템 디자인의 레버

- 같은 베이스 모델로 19% → 48% (FrontierMath) / 57% → 87% (내부) 격차
- 모델 교체에 들이는 자원의 일부를 *워크플로 디자인 + 리뷰 사이클 + 도구 통합* 으로 옮길 가치 있는 영역들이 사내에도 있음

### KPI 점검

- 저자들 결론: *"최종 답을 빨리 만드는 모델"* 만이 아니라 *"협업 효율, 상태 있는 탐색, 불확실성 관리"* 측정하는 평가 프레임 부족
- 사내 LLM 도구 KPI 가 단발 정확도로만 잡혀 있지 않은지 점검할 만함
- 측정 후보: 사용자 개입 시점 분포, 막힌 워크스트림 escalation 시간, 사용자가 살린 실패 시도 수 등

## 시리즈 마무리

5편을 묶어 보면 *AI Co-Mathematician* 은 단발 모델 호출과 형식 증명 시스템 사이에 친 새 카테고리다.

- 7가지 설계 원칙이 시스템 모양을 결정
- 4계층 + 비동기 메시징 + 공유 파일시스템이 그 원칙을 받침
- 5단계 흐름이 사용자와의 실제 협업을 받침
- Hard constraints + Active steering 이 LLM 의 typical 실패 모드 (환각·hand-waving·이른 success claim) 를 막음
- 결과: FrontierMath Tier 4 SOTA + 실제 미해결 문제 해결 + 한계 솔직 보고

사내에서 가져갈 가장 큰 한 가지는 — 모델 능력 향상보다 *시스템 디자인의 레버* 가 종종 더 크고, 그 디자인의 핵심은 *사용자 개입의 위치를 어디에 둘 것인가* 라는 점이다.

처음으로 → [1. 왜 또 다른 수학용 AI 인가](01-overview-and-context/)

## 출처

- https://arxiv.org/html/2605.06651
