---
title: ELF — 임베딩 공간에 머무는 연속 확산 언어 모델
date: 2026-05-21
author: TrainToGPB
tags: [diffusion-language-model, flow-matching, continuous-dlm, generative-model, elf]
source: https://arxiv.org/abs/2605.10938
summary: ELF는 Flow Matching을 frozen T5 임베딩 공간 위에 올리고, $x_1$-prediction과 weight-shared 디코딩으로 마지막 step에서만 token화한다. 105M 모델이 32 step만에 Gen PPL 24, 45B 학습 토큰으로 500B+ 학습한 디스크리트·연속 DLM을 앞선다.
format: abstract
---

# ELF — 임베딩 공간에 머무는 연속 확산 언어 모델

> 원본: [arxiv.org/abs/2605.10938](https://arxiv.org/abs/2605.10938)

디퓨전·플로우 매칭이 이미지·비디오에서 사실상 표준이 된 흐름이 언어로 옮겨갈 때, 디스크리트 토큰 위에서 작동하는 모델들이 우세를 점해 왔다. ELF는 그 격차가 본질적인지 디자인 선택의 문제인지를 다시 묻고, 임베딩 공간에 머무는 연속 확산이 더 적은 step·더 적은 토큰으로 더 강한 성능을 낼 수 있음을 보인다.

## 핵심 포인트

- ELF는 frozen T5-small encoder가 만든 연속 임베딩 위에서 Flow Matching을 돌리고, 마지막 step에서만 같은 네트워크가 token으로 decode한다. 별도 디코더가 필요 없다.
- `$x_1$-prediction` (속도장 대신 clean embedding을 직접 예측) 이 고차원 768-d 임베딩에서 안정성을 만든다. denoise와 decode 손실이 weight sharing으로 자연스럽게 묶인다.
- self-conditioning을 그대로 CFG 신호로 사용하는 training-time CFG로 추론 비용 증가 없이 quality–diversity trade-off를 조절한다.
- 105M ELF-B가 32 sampling step만에 OpenWebText Gen PPL 24를 찍으며, 170M MDLM/Duo/FLM/LangFlow를 모두 outperform. 증류 없이 distilled 모델보다 few-step regime에서 강하다.
- 학습 토큰은 45B로, 기존 DLM들이 흔히 사용하는 500B+ 대비 1/10 수준. WMT14 De-En BLEU 26.4, XSum ROUGE 전 지표 1위.

## 한 페이지 요약

대부분의 leading DLM은 토큰 공간 위에서 categorical 확산을 정의하거나, 임베딩·심플렉스 공간에서 매 step token-level cross-entropy로 trajectory를 vocab에 묶어 왔다. ELF는 다른 디자인 포인트에 있다. 입력 토큰을 frozen T5-small (35M, 512-d) encoder로 통과시키고, 그 위에 linear interpolant $x_t = (1-t)\epsilon + t\,x_1$ 의 rectified flow를 정의한 뒤, 네트워크는 속도장 대신 clean embedding $\hat x_1$ 를 예측한다. 마지막 time step $t=1$ 에서는 같은 네트워크가 "decode" 모드 (binary mode token) 로 전환되어 corrupted embedding을 clean embedding으로 복원하고, 학습 가능한 unembedding으로 token logits를 만들어 cross-entropy loss를 받는다.

![Fig 1. ELF는 더 적은 sampling step과 더 적은 학습 토큰으로 leading discrete·continuous DLM을 앞선다.](assets/fig-1.png)
*Fig 1. ELF의 헤드라인: sampling step × Gen PPL × training tokens 세 축에서 모두 우위.*

이 단순한 구조는 이미지 도메인 Flow Matching의 자산을 자연스럽게 흡수한다. classifier-free guidance를 self-conditioning 위에 얹어 training-time CFG로 구현하고, in-context conditioning (control token prepend) 으로 adaLN-Zero를 대체해 파라미터를 148M에서 105M로 줄였다. 추론은 ODE Euler 또는 SDE-inspired sampler로, few-step regime에서는 SDE 변형이 substantially 더 좋은 trade-off를 만든다.

ablation은 어느 결정이 결정적이고 어느 게 부차적인지를 보여준다. `$x_1$`-prediction은 512에서 1024까지 dimension이 커져도 안정적인 유일한 선택이고, pretrained contextual embedding (T5) 이 from-scratch 또는 learnable embedding을 명확히 앞선다. shared-weight 디노이저-디코더는 별도 디코더보다 더 낮은 Gen PPL 영역으로 확장하면서 파이프라인을 단순화한다. SDE 샘플러는 ODE보다 few-step에서 substantially 강하다.

시스템 비교에서 ELF-B 105M는 OpenWebText 위에서 32 step만에 Gen PPL 24를 기록하며, 170M MDLM·Duo·FLM·LangFlow를 모두 outperform한다. 증류 모델 (MDLM+SDTT, Duo+DCD, FMLM) 과 비교해도 few-step regime에서 강하며, 학습 토큰은 45B로 기존 500B+ 대비 1/10 수준이다. 조건부 생성에서도 WMT14 De-En BLEU 26.4, XSum ROUGE-1/2/L 전부 best. 결론: continuous DLM이 본질적으로 안 되는 게 아니라, 디자인의 빈 자리를 채우면 충분히 경쟁력 있다.

## 자세히 보기

<!-- VERSIONS_START -->
1. [왜 다시 연속 확산 언어 모델인가 — 이산 우세 속에서 ELF가 노리는 빈 자리](details/01-overview-and-context/) — 디퓨전·플로우 매칭이 이미지에선 dominant이지만 언어로 옮긴 시도들은 두 갈래로 갈라졌고, 그 사이 ELF가 비집고 들어가려는 디자인 공백을 정리한다.
2. [임베딩 공간에 머무는 흐름 — ELF가 만든 세 가지 디자인 결정](details/02-design-principles/) — ELF는 임베딩 공간에서 Flow Matching을 돌리고, x_1-prediction으로 고차원에서 안정성을 얻고, 마지막 step만 weight-shared 디코더로 token화한다. 세 결정이 만들어내는 단순한 아키텍처를 풀어 본다.
3. [T5 인코더부터 in-context 컨디셔닝까지 — ELF의 실제 구성](details/03-architecture-and-conditioning/) — T5 인코더 + 보틀넥, 두 모드를 같은 네트워크가 처리하는 binary mode token, self-conditioning을 그대로 CFG 신호로 쓰는 training-time CFG, in-context 컨디셔닝까지 — ELF가 실제로 어떻게 굴러가는지 빌딩블록 단위로 본다.
4. [무엇이 ELF를 작동시키는가 — CFG·임베딩·샘플러 ablation](details/04-ablations-what-matters/) — Gen PPL × entropy 곡선 위에서 CFG, 임베딩 종류, 디코딩 전략, ODE/SDE 샘플러, 모델 스케일을 차례로 흔들어 본다. 어느 디자인이 ELF의 성능을 만들고, 어느 게 부차적인지가 분명히 갈린다.
5. [32 스텝으로 GenPPL 24 — 시스템 비교와 의미](details/05-evaluation-and-implications/) — ELF-B는 32 sampling step으로 Gen PPL 24를 찍고, 45B 학습 토큰만으로 500B+ 학습한 디스크리트·연속 DLM들을 앞선다. WMT14 De-En과 XSum에서도 우위. 마지막 편은 시스템 비교, 한계, 그리고 continuous DLM 다시 보기.
<!-- VERSIONS_END -->

## 출처

- [ELF: Embedded Language Flows (arXiv:2605.10938)](https://arxiv.org/abs/2605.10938)
