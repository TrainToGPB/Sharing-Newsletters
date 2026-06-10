---
title: 추론
---

# 추론

서빙 최적화, 양자화, 디스틸레이션, 스펙큘레이티브 디코딩, KV 캐시, 모델 경량화 일반.

## 글 목록

<!-- TOPIC_POSTS_START -->
| 날짜 | 제목 | 요약 |
| --- | --- | --- |
| 2026-06-10 | [FlashMemory-DeepSeek-V4 — 긴 컨텍스트 KV cache를 미리 골라 싣는 LSA](2026-06-10-flashmemory-deepseek-v4/) | FlashMemory-DeepSeek-V4는 Lookahead Sparse Attention으로 다음 decoding 구간에 필요한 KV chunk만 미리 GPU에 올려, 평균 physical KV cache footprint를 13.5%로 줄이면서 long-context benchmark 정확도를 유지하거나 소폭 개선한다. |
| 2026-05-10 | [TurboQuant — 학습 없는 KV 캐시·벡터 압축의 새 기준](2026-05-10-turboquant/) | 랜덤 회전으로 좌표 분포를 알려진 모양으로 만들고, MSE 양자화에 1-bit QJL 잔차 보정을 더해 KV 캐시를 6배 압축하면서 정확도 손실 없이 H100 에서 키 어텐션을 8배 가속하는 학습·데이터 비의존 양자화 (Google Research, ICLR 2026). |
<!-- TOPIC_POSTS_END -->
