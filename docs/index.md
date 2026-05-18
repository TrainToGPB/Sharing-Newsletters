---
title: 홈
hide:
  - toc
---

# Sharing Newsletters

내부 동료와 외부 기여자가 함께 모이는 AI 기술 공유 뉴스레터.

push 한 번으로 글이 올라가고, 정리는 Claude Code 가 도와준다. 작성 가이드는 레포 루트의 `README.md` 참조.

## 최근 카드 뉴스

<!-- CARDS_START -->
<div class="grid cards" markdown>

- [![](agents/2026-05-10-ai-co-mathematician/cards/card-1.png)](agents/2026-05-10-ai-co-mathematician/cards/)

  **[AI Co-Mathematician — 수학자와 비동기로 협업하는 에이전트 워크벤치](agents/2026-05-10-ai-co-mathematician/)** · 2026-05-10 · _TrainToGPB_

</div>
<!-- CARDS_END -->

## 최신 글

<!-- LATEST_START -->
- **2026-05-18** [SlimQwen — Qwen3-Next-80A3B 를 23A2B 로 줄이는 MoE 가지치기·증류 레시피](training/2026-05-18-slimqwen-moe-compression/) · _TrainToGPB_ — 사전학습 스케일에서 MoE 모델을 압축할 때 (1) 가지치기 = 강한 초기화, (2) 부분 보존 전문가 머징, (3) MTP KD 가 포함된 4-term 손실, (4) 점진적 가지치기 스케줄이 일관되게 더 좋다. Qwen3-Next-80A3B 를 23A2B 로 약 3.4x 압축한 SlimQwen 으로 검증된 레시피. `MoE` `pruning` `distillation` `MTP` `compression` `pretraining`
- **2026-05-16** [강화학습으로 LLM 의 잠재 추론을 깨우는 HRPO](training/2026-05-16-hybrid-latent-reasoning-rl/) · _TrainToGPB_ — 이산 토큰과 hidden state 를 학습 가능한 게이트로 섞고, CoT 트레이스 없이 outcome 보상만으로 잠재 추론을 RL 학습하는 HRPO 가 1.5B·3B Qwen 으로 7B 베이스라인급 성능을 낸다. `강화학습` `추론` `latent-reasoning` `HRPO` `GRPO`
- **2026-05-16** [RecursiveMAS — 멀티 에이전트 협업을 잠재 공간에서 재귀로 스케일링](agents/2026-05-16-recursive-mas/) · _TrainToGPB_ — 다중 에이전트 시스템을 텍스트로 주고받지 않고 잠재 표현 그대로 묶어 하나의 재귀 계산으로 본다. 평균 정확도 +8.3%p, 추론 1.2~2.4배 가속, 토큰 34.6~75.6% 절감. `에이전트` `멀티에이전트` `재귀` `latent-reasoning` `scaling-law`
- **2026-05-13** [On-Policy Distillation — 학생 궤적의 매 토큰을 교사가 채점하는 사후학습](training/2026-05-13-on-policy-distillation/) · _TrainToGPB_ — 학생 모델의 rollout 을 sampling 하고 교사 모델이 매 토큰의 reverse KL 로 채점하는 on-policy distillation 은 AIME'24 74.4% 를 RL 의 1/10 비용 (1,800 vs 17,920 GPU hr) 으로 재현하고, 사내 어시스턴트 시나리오에서 IF-eval 을 45% → 83% 로 복원하면서 knowledge 도 유지한다. RL 대비 7~10배 빠른 수렴, 누적 50~100배 compute 절감. `사후학습` `증류` `RL` `on-policy` `효율화`
- **2026-05-11** [Natural Language Autoencoders — 모델 활성값을 자연어로 비지도 설명하기](models/2026-05-11-nla-natural-language-autoencoders/) · _TrainToGPB_ — 활성값을 자연어로 압축했다가 다시 복원하는 자동인코더(NLA)를 RL로 학습해 모델 내부 상태를 사람이 직접 읽을 수 있게 만든다. Opus 4.6 사전 배포 감사에서 unverbalized evaluation awareness를 표면화하고, 의도적으로 misalign된 모델을 학습 데이터 접근 없이 감사하는 데 성공했다. `interpretability` `nla` `anthropic` `mechanistic-interpretability` `auditing` `alignment`
- **2026-05-11** [Rethinking On-Policy Distillation — 학생과 교사 사이의 숨은 동역학](training/2026-05-11-rethinking-on-policy-distillation/) · _Claude_ — 같은 OPD 셋업이 왜 어떤 날은 되고 어떤 날은 안 되는지 phenomenology · mechanism · recipe 세 층으로 분해. 성공 run 은 token overlap 이 72→91% 로 오르며 shared top-k 가 결합 확률 질량의 97-99% 를 차지하고, 같은 family 1.5B 와 7B 교사는 학생 관점에서 분포적으로 구별되지 않는다. cold start SFT + teacher-aligned prompt selection 으로 실패 run 을 성공 dynamic 으로 되돌릴 수 있다. `distillation` `post-training` `on-policy` `rl` `sft`
- **2026-05-10** [TurboQuant — 학습 없는 KV 캐시·벡터 압축의 새 기준](inference/2026-05-10-turboquant/) · _Claude_ — 랜덤 회전으로 좌표 분포를 알려진 모양으로 만들고, MSE 양자화에 1-bit QJL 잔차 보정을 더해 KV 캐시를 6배 압축하면서 정확도 손실 없이 H100 에서 키 어텐션을 8배 가속하는 학습·데이터 비의존 양자화 (Google Research, ICLR 2026). `inference` `quantization` `kv-cache` `vector-search` `turboquant` `qjl` `polarquant`
- **2026-05-10** [RL 은 LLM 에게 긴 호흡 추론을 가르칠 수 있을까 — ScaleLogic 으로 본 표현력의 힘](training/2026-05-10-rl-long-horizon-scalelogic/) · _TrainToGPB_ — 깊이와 논리 표현력을 독립적으로 통제하는 합성 환경 ScaleLogic 위에서 RL 학습 비용은 깊이에 대해 깨끗한 power-law 를 그리며, 그 지수는 표현력이 풍부할수록 단조 증가한다 ($\gamma$ 1.04 → 2.60). 다운스트림 전이 역시 *얼마나* 학습했는지보다 *무엇을* 학습했는지에 더 의존하며, 가장 표현력 있는 환경은 8개 추론 벤치마크 평균을 최대 +10.66 점 끌어올린다. `RL` `추론` `사후학습` `합성데이터` `스케일링`
- **2026-05-10** [AI Co-Mathematician — 수학자와 비동기로 협업하는 에이전트 워크벤치](agents/2026-05-10-ai-co-mathematician/) · _TrainToGPB_ — 수학자가 옆에 앉아 가설을 주고받는 비동기·상태 보존 에이전트 워크벤치. FrontierMath Tier 4에서 48%로 새 SOTA, 내부 100문항 벤치마크에서 Gemini Deep Think 대비 +17%p. `agents` `math` `frontiermath` `multi-agent`
<!-- LATEST_END -->

## 토픽

- [에이전트](agents/) — 에이전트, MCP, 도구 사용
- [모델](models/) — 신규 모델 출시·아키텍처
- [학습](training/) — 사전·사후학습, 파인튜닝, 데이터
- [추론](inference/) — 서빙·경량화·양자화 등 추론 기술
- [벤치마크](benchmark/) — 평가, 리더보드, 비교
- [인프라](infra/) — 클러스터·MLOps·비용
- [도구](tools/) — IDE, CLI, 개발 도구
- [모음](digest/) — 주간·월간 디제스트

## 기여하기

1. 이 레포 클론
2. Claude Code 에서 `/share-news <URL_or_PDF>` 실행
3. 생성된 파일을 검토하고 main 으로 push

수동 작성도 가능. 자세한 컨벤션은 `README.md` 와 `CLAUDE.md`.
