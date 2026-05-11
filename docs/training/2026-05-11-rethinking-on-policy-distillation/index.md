---
title: Rethinking On-Policy Distillation — 학생과 교사 사이의 숨은 동역학
date: 2026-05-11
author: Claude
tags: [distillation, post-training, on-policy, rl, sft]
source: https://www.arxiv.org/html/2604.13016
summary: 같은 OPD 셋업이 왜 어떤 날은 되고 어떤 날은 안 되는지 phenomenology · mechanism · recipe 세 층으로 분해. 성공 run 은 token overlap 이 72→91% 로 오르며 shared top-k 가 결합 확률 질량의 97-99% 를 차지하고, 같은 family 1.5B 와 7B 교사는 학생 관점에서 분포적으로 구별되지 않는다. cold start SFT + teacher-aligned prompt selection 으로 실패 run 을 성공 dynamic 으로 되돌릴 수 있다.
format: abstract
---

# Rethinking On-Policy Distillation — 학생과 교사 사이의 숨은 동역학

> 원본: [arxiv.org/abs/2604.13016](https://www.arxiv.org/html/2604.13016)

On-Policy Distillation (OPD) 는 SFT 와 RL 의 절충안으로 LLM post-training 의 한 축이 됐지만, 같은 셋업에서도 성공·실패가 갈리는 이유가 잘 알려져 있지 않았다. 이 논문 (Tsinghua thunlp 그룹, arxiv 2604.13016) 은 그 동역학을 phenomenology · mechanism · recipe 세 층으로 분해한다.

## 핵심 포인트

- **두 가지 성공 조건**. (1) 학생과 교사가 호환되는 thinking pattern 을 공유해야 하고, (2) 점수가 높다는 것만으론 부족 — 교사가 학생이 학습 중 본 적 없는 진짜 새 능력을 제공해야 한다.
- **Token-level phenomenology**. 성공한 OPD 는 student-visited state 위에서 overlap ratio 가 72% → 91% 로 오르고, shared top-$k$ 가 결합 확률 질량의 97-99% 를 차지하며, entropy gap 이 좁아진다. 실패 run 은 이 신호가 출발부터 정체된다.
- **Weak-to-strong reverse**. 같은 family 1.5B 와 7B 교사가 학생 관점에서 분포적으로 구별되지 않는다. 교사 크기 자체가 아니라 student-visible 분포 차이가 본질.
- **두 가지 회복 레시피**. off-policy cold start (교사 rollout SFT 워밍업) 와 teacher-aligned prompt selection (교사 post-training 분포에서 prompt 선택). 둘 다 초기 overlap 을 끌어올리고, 회복된 run 은 자연 성공 run 과 같은 dynamic signature 를 보인다.
- **실험 셋업**. 학생 Qwen3-1.7B-Base, 교사 Qwen3-4B (Non-thinking), math-domain (OpenThoughts3-1.2M subset, 200K rollouts). 같은 family · math 한정 결과로 cross-family · 다른 도메인 일반화는 후속 검증.

## 한 페이지 요약

OPD 는 학생이 sampling 한 trajectory 위에서 교사의 token-level 확률 신호를 받는다. SFT 처럼 분포 mismatch 를 강제하지 않고, sparse-reward RL 보다 dense 한 신호를 준다는 이론적 매력이 분명하다. 그런데 실무에서는 같은 모델 패밀리·같은 데이터·같은 알고리즘으로 돌려도 성공과 실패가 갈리는 일이 잦았다. 본 논문은 그 양상을 "phenomenology", 그 뒤의 메커니즘, 실패를 살리는 처방의 세 층으로 정리한다.

phenomenology 층에서 저자들은 학습 전 과정 동안 token-level 지표 세 가지를 추적한다. student 가 실제 도달한 state 에서 두 분포의 top-$k$ 가 얼마나 겹치는지 (overlap ratio), 그 합집합이 결합 확률 질량에서 얼마나 차지하는지 ($m_k$), 두 분포의 엔트로피 차이가 어떻게 움직이는지 ($\Delta H$). 성공한 run 에서는 overlap 이 72% 부근에서 91% 까지 단조 상승하고, shared top-$k$ 가 결합 확률 질량의 97-99% 를 차지하며, entropy gap 의 절대값이 좁아진다. 실패한 run 은 이 세 신호가 학습 출발부터 정체된다. 즉 OPD 의 성패는 후반부 downstream 점수를 기다리지 않고 학습 초기 token-level 시그너처만으로도 거의 예측된다.

mechanism 층에서는 두 가지 조건이 OPD 성공을 좌우한다. 첫째, 학생과 교사가 호환되는 thinking pattern 을 가져야 한다. 같은 패밀리 (예: Qwen 계열) 모델은 prompt 에 대해 비슷한 분기 구조의 chain-of-thought 를 만들어 student 가 도달하는 state 위에서 교사가 의미 있는 신호를 줄 수 있지만, 패밀리가 다르면 같은 문제에서 다른 분기를 만들어 교사 신호가 student-visited state 위에 잘 정의되지 않는다. 둘째, 교사가 학생보다 점수가 높다는 것만으로는 부족하다 — 교사가 학생이 학습 중 본 적 없는 진짜 새 능력을 제공해야 한다. 저자들은 weak-to-strong reverse distillation 으로 이 점을 뒷받침한다. 같은 패밀리에서 1.5B 와 7B 교사 두 개는 학생 관점에서 분포적으로 구별되지 않는다. 큰 교사 = 좋은 distillation 이라는 단순 신화가 깨지는 결과다.

recipe 층은 실패하는 OPD 를 되살리는 두 전략이다. off-policy cold start 는 OPD 전에 교사가 학생 prompt 분포 위에서 생성한 rollout 으로 짧은 SFT 워밍업을 돌린다. 학생을 Qwen3-1.7B-Base 대신 Qwen3-1.7B-SFT 에서 출발시키면 검증 성능이 학습 전체 구간에서 일관되게 우위에 있고, 그 격차는 단순 초기 부스트가 아니라 최종 천장 자체를 끌어올리는 효과로 유지된다. SFT 출발 학생은 초기 overlap 이 높고 trajectory 가 매끄럽다. base 출발 학생은 초기 overlap 이 낮고 불안정한 회복을 거친다. teacher-aligned prompt selection 은 교사의 post-training 데이터 분포에서 prompt 를 뽑아 OPD 학습에 사용한다. 학생이 도달하는 state 가 교사가 학습한 분포와 더 겹치게 만들어 high-probability token 위에서 정렬을 sharpen 한다. 두 전략은 상호보완적이고, 회복된 run 은 자연 성공 run 과 같은 동역학 (overlap 상승, token-level advantage 개선, entropy gap narrowing) 을 보인다.

종합하면, OPD 가 옮기는 정보는 "분포 전체" 가 아니라 "양쪽이 함께 관심을 두는 작은 token 집합 위의 ranking 과 확률 재배분" 이다. 97-99% 라는 질량 점유 숫자가 그 점을 정량으로 말한다. 그래서 교사 크기보다 student-visible 분포 차이가 본질이고, 실패 run 의 해법은 학습 step 을 더 미는 것이 아니라 학생을 교사 분포 쪽으로 미리 끌어다 놓는 것이다. 실험은 같은 family · math 한정이라 cross-family 와 다른 도메인 일반화는 후속 과제로 남는다.

## 자세히 보기

<!-- VERSIONS_START -->
1. [On-Policy Distillation 은 왜 까다로운가](details/01-why-opd-is-tricky/) — OPD 가 post-training 에서 차지하는 위치와 빈번한 실패 — 이 논문이 풀려는 질문.
2. [성공의 두 조건 — 호환성과 새로움](details/02-two-success-conditions/) — OPD 가 성공하려면 학생과 교사가 호환되는 thinking pattern 을 공유하면서, 교사가 진짜 새 능력을 제공해야 한다. 1.5B vs 7B 가 학생 관점에서 구별되지 않는다는 weak-to-strong 결과가 그 직관을 뒷받침한다.
3. [토큰 단위 phenomenology — 성공·실패의 미시 신호](details/03-token-level-phenomenology/) — 성공한 OPD 는 token overlap 이 72%에서 91%로 오르고, shared top-k 가 결합 확률 질량의 97-99%를 차지하며, 두 분포의 entropy gap 이 좁아진다. 실패한 run 은 출발부터 이 신호가 죽어 있다.
4. [실패하는 OPD 를 살리는 두 레시피](details/04-recovery-recipes/) — 교사 rollout SFT 로 워밍업한 다음 OPD 를 돌리는 cold start, 그리고 교사 post-training 분포에서 prompt 를 뽑는 teacher-aligned selection. 둘 다 초기 overlap 을 끌어올려 실패 run 을 성공 dynamic 으로 되돌린다.
5. [정리 — 우리 팀이 OPD 를 돌릴 때 점검할 것](details/05-implications-and-checklist/) — 같은 family·math 실험에 한정된 결과의 적용 범위, distillation 이 실제로 옮기는 정보의 재해석, OPD 셋업·모니터링·실패 대응 체크리스트.
<!-- VERSIONS_END -->

## 출처

- [arxiv.org/abs/2604.13016](https://www.arxiv.org/html/2604.13016)
- [github.com/thunlp/OPD](https://github.com/thunlp/OPD)
