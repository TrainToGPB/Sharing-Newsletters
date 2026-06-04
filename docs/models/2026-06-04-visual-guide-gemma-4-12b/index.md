---
title: Gemma 4 12B — encoder-free 멀티모달 모델의 구조
date: 2026-06-04
author: 김세형
tags: [gemma-4, multimodal-llm, encoder-free, vision-language-model, audio-language-model]
source: https://newsletter.maartengrootendorst.com/p/a-visual-guide-to-gemma-4-12b
summary: Gemma 4 12B는 vision/audio encoder를 가벼운 embedding-projection 경로로 바꾸고, 이미지와 오디오 이해 부담을 LLM 본체로 넘겨 latency와 파이프라인 복잡도를 줄인다.
format: abstract
---

# Gemma 4 12B — encoder-free 멀티모달 모델의 구조

> 원본: [Exploring Language Models](https://newsletter.maartengrootendorst.com/p/a-visual-guide-to-gemma-4-12b)

Gemma 4 12B는 E4B와 26B A4B 사이의 크기 공백을 채우는 동시에, vision/audio encoder를 제거한 encoder-free 멀티모달 구조를 실험한다.

## 핵심 포인트

- 기존 멀티모달 LLM은 이미지와 오디오를 먼저 별도 Transformer encoder로 처리한 뒤 connector로 LLM 입력 차원에 맞춘다.
- Gemma 4 12B는 vision encoder를 attention-free image embedder로 바꾸고, $48 \times 48$ patch를 projection과 위치 embedding만 거쳐 LLM에 넣는다.
- audio encoder도 제거된다. $16\,000\text{Hz}$ raw waveform을 $40\text{ms}$ chunk로 나누고, 각 $640$ amplitude sample 묶음을 linear projection으로 audio token화한다.
- encoder-free는 비텍스트 modality의 선처리 latency와 parameter overhead를 줄이지만, 의미 해석 부담은 LLM decoder 본체로 이동한다.
- vision embedder의 약 $35$M parameter는 attention block이 아니라 주로 pixel-to-model-dimension projection에서 나온다.

## 한 페이지 요약

Maarten Grootendorst의 글은 Gemma 4 12B를 "새로운 중간 크기 모델"보다 "멀티모달 입력을 LLM에 연결하는 방식을 바꾼 모델"로 읽는다. 일반적인 멀티모달 LLM은 텍스트, 이미지, 오디오를 같은 방식으로 처리하지 않는다. 텍스트는 token embedding layer를 거쳐 바로 decoder로 들어가지만, 이미지는 vision encoder가 patch feature를 만들고, 오디오는 audio encoder가 waveform이나 spectrogram 계열 feature를 처리한다. 그 다음 connector가 encoder output을 LLM token embedding과 같은 차원으로 맞춘다.

![Gemma 4 12B는 이미지와 오디오를 가벼운 embedder/projection 경로로 LLM에 연결한다.](assets/fig-1.png)
*Gemma 4 12B의 핵심 변화는 image/audio encoder를 제거하고, raw input에 가까운 표현을 projection해 LLM 본체가 처리하게 만든다는 점이다.*

이 방식은 잘 작동하지만 공짜는 아니다. encoder는 자체 attention layer를 갖는 작은 Transformer이고, 입력을 먼저 처리해야 하므로 LLM이 실제 생성·이해 작업을 시작하기 전 latency가 생긴다. parameter도 작지 않다. 원문 기준 Gemma 4의 vision encoder는 작은 모델에서 약 $150$M, 26B A4B와 31B 쪽에서는 약 $550$M parameter를 차지한다. E2B/E4B의 audio encoder도 약 $305$M parameter 규모다. fine-tuning에서도 문제가 생긴다. 보통은 LLM 본체만 fine-tune하고 encoder는 고정하는 경우가 많아, modality encoder와 LLM을 함께 키우거나 조정하기 어렵다.

Gemma 4 12B의 해법은 encoder를 더 작게 만드는 것이 아니라 아예 다른 경로로 바꾸는 것이다. vision 쪽에서는 기존 $16 \times 16$ patch를 Transformer encoder에 넣고 pooling하는 대신, $48 \times 48$ patch를 직접 사용한다. attention-free embedder가 patch를 projection하고, 이미지 안의 위치 정보는 별도의 $x$, $y$ positional embedding table에서 가져와 더한다. 이후 LayerNorm과 projection을 거쳐 LLM이 기대하는 $3840$ 차원 입력으로 맞춘다. 이 embedder는 약 $35$M parameter지만, 대부분은 attention이나 feed-forward block이 아니라 $48 \times 48 \times 3 = 6912$ pixel 값을 model dimension으로 사상하는 projection에서 나온다.

![Gemma 4 12B의 image embedder는 위치 embedding과 projection 중심의 작은 모듈이다.](assets/fig-12.png)
*기존 vision encoder가 하던 attention 기반 feature 처리는 사라지고, patch별 embedding과 위치 주입 뒤 LLM이 이어서 처리한다.*

audio 쪽은 더 단순하다. 원문은 audio가 이미 시간 순서가 있는 2차원 시퀀스라 별도 2D 위치 embedding이 필요하지 않다고 설명한다. $16\text{kHz}$ raw audio를 $40\text{ms}$ 단위로 자르면 각 구간은 $640$개의 amplitude sample이 된다. Gemma 4 12B는 이 raw feature chunk를 linear projection해 LLM 입력 차원에 맞춘 audio token으로 만든다. 기존 E4B는 audio tokenizer와 stacked decoder/Conformer 계열 처리를 거쳐 projection했지만, 12B는 split-and-project에 가깝다.

중요한 trade-off는 "encoder가 없어졌으니 multimodal 이해가 쉬워졌다"가 아니라 "encoder가 맡던 이해 부담을 LLM 본체로 옮겼다"는 점이다. 입력은 LLM에 더 빨리 도착하고 파이프라인은 단순해지지만, LLM은 raw patch와 raw audio chunk에 가까운 표현에서 의미를 구성해야 한다. 따라서 이 구조는 training에서 LLM이 image/audio representation을 충분히 학습한다는 전제를 둔다. 원문이 흥미로운 이유도 여기에 있다. Gemma 4 12B는 단순한 크기 확장이 아니라, 멀티모달 모델에서 encoder와 connector의 역할 분담을 다시 묻는 설계다.

## 자세히 보기

<!-- VERSIONS_START -->
1. [멀티모달 LLM은 왜 encoder와 connector를 따로 두었나](details/01-why-encoders-and-connectors/) — Gemma 4 12B의 encoder-free 구조를 이해하기 전에, 기존 멀티모달 LLM이 텍스트, 이미지, 오디오를 LLM 입력 공간으로 맞추기 위해 encoder와 connector를 분리해 둔 이유를 정리한다.
2. [기존 Gemma 4의 vision/audio encoder는 무엇을 했나](details/02-gemma4-encoders/) — Gemma 4 12B가 encoder-free로 바뀌기 전, 기존 Gemma 4가 이미지와 오디오를 어떻게 LLM 입력으로 변환했는지 정리한다. vision encoder의 16x16 patch 처리, 3x3 pooling, connector, audio encoder의 Conformer 계열 처리와 projection, 그리고 latency와 fine-tuning 복잡도가 왜 문제가 되었는지를 살펴본다.
3. [Gemma 4 12B는 어떻게 encoder-free가 되었나](details/03-encoder-free-12b/) — Gemma 4 12B가 E4B와 26B A4B 사이의 크기만 채운 모델이 아니라, 시각·오디오 encoder를 가벼운 projection 경로로 바꾸고 LLM decoder가 멀티모달 이해를 직접 맡도록 재배치한 과정을 정리한다.
4. [vision embedder는 위치와 차원을 어떻게 맞추나](details/04-vision-embedder/) — Gemma 4 12B가 무거운 vision encoder를 버리고 $48 \times 48$ 원본 패치, x/y 위치 임베딩, LayerNorm, projection만으로 이미지 토큰을 LLM 입력 차원에 맞추는 방식을 정리한다.
5. [오디오는 왜 더 단순하게 encoder-free가 되나](details/05-audio-path-and-implications/) — Gemma 4 12B의 audio path는 raw waveform을 $16\,000$Hz로 샘플링한 뒤 $40\text{ms}$ 단위, 즉 $640$ amplitude sample 벡터로 자르고 linear projection만으로 audio token을 만든다. 마지막 편은 이 구조가 기존 E4B audio encoder와 무엇이 다르고, latency와 parameter를 줄이는 대신 LLM에 어떤 이해 부담을 넘기는지 정리한다.
<!-- VERSIONS_END -->

## 출처

- [A Visual Guide to Gemma 4 12B](https://newsletter.maartengrootendorst.com/p/a-visual-guide-to-gemma-4-12b)
