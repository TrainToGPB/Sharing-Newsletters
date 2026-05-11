---
title: 학습
---

# 학습

사전학습, 사후학습 (SFT, DPO, RLHF, RLAIF), 파인튜닝, 데이터 큐레이션·합성.

## 글 목록

<!-- TOPIC_POSTS_START -->
| 날짜 | 제목 | 요약 |
| --- | --- | --- |
| 2026-05-11 | [Rethinking On-Policy Distillation — 학생과 교사 사이의 숨은 동역학](2026-05-11-rethinking-on-policy-distillation/) | 같은 OPD 셋업이 왜 어떤 날은 되고 어떤 날은 안 되는지 phenomenology · mechanism · recipe 세 층으로 분해. 성공 run 은 token overlap 이 72→91% 로 오르며 shared top-k 가 결합 확률 질량의 97-99% 를 차지하고, 같은 family 1.5B 와 7B 교사는 학생 관점에서 분포적으로 구별되지 않는다. cold start SFT + teacher-aligned prompt selection 으로 실패 run 을 성공 dynamic 으로 되돌릴 수 있다. |
| 2026-05-10 | [RL 은 LLM 에게 긴 호흡 추론을 가르칠 수 있을까 — ScaleLogic 으로 본 표현력의 힘](2026-05-10-rl-long-horizon-scalelogic/) | 깊이와 논리 표현력을 독립적으로 통제하는 합성 환경 ScaleLogic 위에서 RL 학습 비용은 깊이에 대해 깨끗한 power-law 를 그리며, 그 지수는 표현력이 풍부할수록 단조 증가한다 ($\gamma$ 1.04 → 2.60). 다운스트림 전이 역시 *얼마나* 학습했는지보다 *무엇을* 학습했는지에 더 의존하며, 가장 표현력 있는 환경은 8개 추론 벤치마크 평균을 최대 +10.66 점 끌어올린다. |
<!-- TOPIC_POSTS_END -->
