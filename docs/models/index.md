---
title: 모델
---

# 모델

신규 모델 출시 소식, 아키텍처 변화, 모델 패밀리 비교. 평가·벤치마크는 [벤치마크](../benchmark/) 폴더로.

## 글 목록

<!-- TOPIC_POSTS_START -->
| 날짜 | 제목 | 요약 |
| --- | --- | --- |
| 2026-06-04 | [Gemma 4 12B — encoder-free 멀티모달 모델의 구조](2026-06-04-visual-guide-gemma-4-12b/) | Gemma 4 12B는 vision/audio encoder를 가벼운 embedding-projection 경로로 바꾸고, 이미지와 오디오 이해 부담을 LLM 본체로 넘겨 latency와 파이프라인 복잡도를 줄인다. |
| 2026-05-21 | [ELF — 임베딩 공간에 머무는 연속 확산 언어 모델](2026-05-21-elf-embedded-language-flows/) | ELF는 Flow Matching을 frozen T5 임베딩 공간 위에 올리고, $x_1$-prediction과 weight-shared 디코딩으로 마지막 step에서만 token화한다. 105M 모델이 32 step만에 Gen PPL 24, 45B 학습 토큰으로 500B+ 학습한 디스크리트·연속 DLM을 앞선다. |
| 2026-05-11 | [Natural Language Autoencoders — 모델 활성값을 자연어로 비지도 설명하기](2026-05-11-nla-natural-language-autoencoders/) | 활성값을 자연어로 압축했다가 다시 복원하는 자동인코더(NLA)를 RL로 학습해 모델 내부 상태를 사람이 직접 읽을 수 있게 만든다. Opus 4.6 사전 배포 감사에서 unverbalized evaluation awareness를 표면화하고, 의도적으로 misalign된 모델을 학습 데이터 접근 없이 감사하는 데 성공했다. |
<!-- TOPIC_POSTS_END -->
