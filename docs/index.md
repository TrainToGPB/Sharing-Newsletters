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
- **2026-06-10** [MAI-Thinking-1: Microsoft의 reasoning model을 만든 hill-climbing machine](models/2026-06-10-mai-thinking-1/) · _김세형_ — MAI-Thinking-1은 35B active / 약 1T total MoE reasoning model이지만, 보고서의 핵심은 모델 자체보다 pre-training, RL, 평가, 인프라를 빠르게 반복하는 hill-climbing machine이다. `mai-thinking-1` `microsoft-ai` `reasoning-model` `reinforcement-learning` `moe`
- **2026-06-10** [FlashMemory-DeepSeek-V4 — 긴 컨텍스트 KV cache를 미리 골라 싣는 LSA](inference/2026-06-10-flashmemory-deepseek-v4/) · _김세형/LLM서비스개발팀/NE_ — FlashMemory-DeepSeek-V4는 Lookahead Sparse Attention으로 다음 decoding 구간에 필요한 KV chunk만 미리 GPU에 올려, 평균 physical KV cache footprint를 13.5%로 줄이면서 long-context benchmark 정확도를 유지하거나 소폭 개선한다. `long-context` `kv-cache` `inference` `sparse-attention` `flashmemory`
- **2026-06-05** [On the Scaling of PEFT — 백만 개 개인 모델을 위한 LoRA 스케일링](training/2026-06-05-scaling-peft-personal-models/) · _김세형_ — PEFT를 단순한 저비용 fine-tuning이 아니라 강한 공유 base 위에 얹히는 지속적 local adaptive state로 보고, Scale Up·Scale Down·Scale Out 세 축이 함께 맞물려야 백만 개 개인 모델이 가능하다고 주장한다. `PEFT` `LoRA` `personalization` `fine-tuning` `serving`
- **2026-06-05** [AI는 AI 개발을 얼마나 가속하고 있는가](agents/2026-06-05-recursive-self-improvement/) · _김세형_ — Anthropic은 외부 벤치마크와 내부 개발 데이터를 근거로 AI가 이미 AI 개발을 가속하고 있으며, 병목이 실행에서 연구 판단과 사회적 조율로 이동하고 있다고 주장한다. `agents` `recursive-self-improvement` `ai-research` `anthropic`
- **2026-06-04** [Gemma 4 12B — encoder-free 멀티모달 모델의 구조](models/2026-06-04-visual-guide-gemma-4-12b/) · _김세형_ — Gemma 4 12B는 vision/audio encoder를 가벼운 embedding-projection 경로로 바꾸고, 이미지와 오디오 이해 부담을 LLM 본체로 넘겨 latency와 파이프라인 복잡도를 줄인다. `gemma-4` `multimodal-llm` `encoder-free` `vision-language-model` `audio-language-model`
- **2026-05-21** [ELF — 임베딩 공간에 머무는 연속 확산 언어 모델](models/2026-05-21-elf-embedded-language-flows/) · _TrainToGPB_ — ELF는 Flow Matching을 frozen T5 임베딩 공간 위에 올리고, $x_1$-prediction과 weight-shared 디코딩으로 마지막 step에서만 token화한다. 105M 모델이 32 step만에 Gen PPL 24, 45B 학습 토큰으로 500B+ 학습한 디스크리트·연속 DLM을 앞선다. `diffusion-language-model` `flow-matching` `continuous-dlm` `generative-model` `elf`
- **2026-05-18** [SlimQwen — Qwen3-Next-80A3B 를 23A2B 로 줄이는 MoE 가지치기·증류 레시피](training/2026-05-18-slimqwen-moe-compression/) · _TrainToGPB_ — 사전학습 스케일에서 MoE 모델을 압축할 때 (1) 가지치기 = 강한 초기화, (2) 부분 보존 전문가 머징, (3) MTP KD 가 포함된 4-term 손실, (4) 점진적 가지치기 스케줄이 일관되게 더 좋다. Qwen3-Next-80A3B 를 23A2B 로 약 3.4x 압축한 SlimQwen 으로 검증된 레시피. `MoE` `pruning` `distillation` `MTP` `compression` `pretraining`
- **2026-05-16** [강화학습으로 LLM 의 잠재 추론을 깨우는 HRPO](training/2026-05-16-hybrid-latent-reasoning-rl/) · _TrainToGPB_ — 이산 토큰과 hidden state 를 학습 가능한 게이트로 섞고, CoT 트레이스 없이 outcome 보상만으로 잠재 추론을 RL 학습하는 HRPO 가 1.5B·3B Qwen 으로 7B 베이스라인급 성능을 낸다. `강화학습` `추론` `latent-reasoning` `HRPO` `GRPO`
- **2026-05-16** [RecursiveMAS — 멀티 에이전트 협업을 잠재 공간에서 재귀로 스케일링](agents/2026-05-16-recursive-mas/) · _TrainToGPB_ — 다중 에이전트 시스템을 텍스트로 주고받지 않고 잠재 표현 그대로 묶어 하나의 재귀 계산으로 본다. 평균 정확도 +8.3%p, 추론 1.2~2.4배 가속, 토큰 34.6~75.6% 절감. `에이전트` `멀티에이전트` `재귀` `latent-reasoning` `scaling-law`
- **2026-05-13** [On-Policy Distillation — 학생 궤적의 매 토큰을 교사가 채점하는 사후학습](training/2026-05-13-on-policy-distillation/) · _TrainToGPB_ — 학생 모델의 rollout 을 sampling 하고 교사 모델이 매 토큰의 reverse KL 로 채점하는 on-policy distillation 은 AIME'24 74.4% 를 RL 의 1/10 비용 (1,800 vs 17,920 GPU hr) 으로 재현하고, 사내 어시스턴트 시나리오에서 IF-eval 을 45% → 83% 로 복원하면서 knowledge 도 유지한다. RL 대비 7~10배 빠른 수렴, 누적 50~100배 compute 절감. `사후학습` `증류` `RL` `on-policy` `효율화`
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
