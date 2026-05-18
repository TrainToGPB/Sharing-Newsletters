---
title: "MTP 증류와 손실 함수 설계"
date: 2026-05-18
author: TrainToGPB
tags: [MoE, distillation, MTP, knowledge-distillation, pretraining]
source: https://arxiv.org/abs/2605.08738
summary: 백본 LM/KD 손실에 MTP LM/KD 손실을 더한 4-term 종합 목적과 점진적 가지치기 스케줄의 동기를 정리한다.
format: details
part: 3
---

# MTP 증류와 손실 함수 설계

> 원본: [arxiv.org/abs/2605.08738](https://arxiv.org/abs/2605.08738)

가지치기로 얻은 23A2B 학생 모델은 출발선이 비어 있지 않다. 80A3B 교사의 가중치 일부를 이어받았고, 따라서 후속 학습은 "처음부터 배우기" 가 아니라 "잘려나간 능력의 복구" 다. 이 복구 단계에서 손실 함수를 어떻게 설계하느냐가 최종 성능을 좌우한다. 이 편은 SlimQwen 이 사용한 4-term 손실 — 백본 LM 손실, 백본 KD 손실, MTP LM 손실, MTP KD 손실 — 의 구조와 가중치 스케줄, 그리고 한 번에 자르지 않고 단계적으로 자르는 progressive pruning 의 동기를 정리한다.

## 왜 LM 손실을 KD 와 함께 쓰는가

가지치기 후 학습에 흔히 쓰이는 두 가지 옵션은 표준 언어 모델링 손실 (LM loss) 과 지식 증류 손실 (KD loss) 이다. SlimMoE 류는 KD 만, DarwinLM 류는 LM 만을 쓴다. SlimQwen 은 두 손실을 모두 섞는다.

이유는 단순하다. 순수 KD 는 교사의 next-token 확률 분포를 따라가는 데 집중하지만, 사실 정확도 (knowledge-intensive) 가 중요한 벤치마크 — MMLU, MMLU-Pro 처럼 정답 토큰의 신뢰도가 결정적인 과제 — 에서는 그라운드 트루스 라벨에 직접 가까워지는 LM 신호가 별도로 필요하다. 다음 편 실험 표에서 보겠지만 NTP KD 만 쓰는 경우와 NTP KD + LM 을 함께 쓰는 경우 MMLU 가 74.16 에서 74.93 으로, MMLU-Pro 가 50.97 에서 51.44 로 올라간다. 큰 차이는 아니지만 일관된 방향이고, 이게 SlimQwen 이 두 손실을 같이 흘리는 이유다.

여기서는 동기만 짚고, 실측 비교 표는 다음 편으로 미룬다.

## MTP 모듈의 구조

Multi-Token Prediction (MTP) 모듈은 백본이 토큰 한 개를 예측하는 동안 추가로 $D$ 개의 future token 을 동시에 예측하는 곁가지다. Gloeckle et al. (2024) 가 제안한 구조를 그대로 따른다.

각 깊이 $d \in \{1, \ldots, D\}$ 에서 MTP 모듈은 다음 네 부분으로 구성된다.

- 임베딩 레이어 — 백본과 공유
- 출력 헤드 — 백본과 공유
- Transformer block $\mathrm{Trans}^d$ — 깊이별 전용
- 선형 결합 행렬 $M^d$ — 깊이별 전용

핵심은 임베딩과 출력 헤드를 백본과 묶어 추가 파라미터를 최소화하면서, 깊이별 트랜스포머와 결합 행렬만 따로 둔다는 점이다. Qwen3-Next 80A3B 가 이미 MTP 모듈을 안고 학습됐기 때문에, 학생 23A2B 도 동일한 구조를 그대로 상속받는다.

### Forward 수식

$i$ 번째 입력 토큰 $t_i$, 예측 깊이 $d$ 에서 동작을 보면 다음과 같다. 먼저 깊이 $d-1$ 에서의 토큰 표현 $h^{d-1}_i$ 와 $i+d$ 번째 토큰의 임베딩 $\mathrm{Emb}(t_{i+d})$ 을 연결 (concat) 한 뒤 $M^d$ 로 선형 사영한다.

$$
h'^{d}_i = M^d \left[ \mathrm{RMSNorm}(h^{d-1}_i) \,;\, \mathrm{RMSNorm}(\mathrm{Emb}(t_{i+d})) \right]
\tag{9}
$$

$d = 1$ 이면 $h^{0}_i$ 는 백본 마지막 레이어가 내놓은 표현 그대로다. 결합된 표현을 깊이 $d$ 의 Transformer block 에 통과시켜 현재 깊이 표현을 얻는다.

$$
h^{d}_{1:T-d} = \mathrm{Trans}^d (h'^{d}_{1:T-d})
$$

여기서 $T$ 는 시퀀스 길이고, $T-d$ 까지만 가져가는 이유는 시퀀스 끝쪽에서는 미래 토큰이 없어 라벨이 잘리기 때문이다. 마지막으로 공유 출력 헤드 $\mathrm{OutHead}$ 가 $h^{d}_i$ 를 어휘 크기 $V$ 로 사영하고 $\mathrm{softmax}$ 를 거쳐 $i + 1 + d$ 번째 토큰의 분포 $p^{d}_i \in \mathbb{R}^{V}$ 를 만든다.

요약하면, MTP 깊이 $d$ 의 모듈은 위치 $i$ 에서 $d+1$ 칸 앞의 토큰을 맞히는 보조 헤드다. 백본은 여전히 next-token 만 예측한다.

## 4-term 손실 함수

이 모듈에서 두 가지 손실을 짠다. 첫째는 그라운드 트루스 라벨에 대한 MTP LM 손실이다.

$$
\mathcal{L}^{d}_{\mathrm{MTP\_LM}}
= - \frac{1}{T - d} \sum_{i=1}^{T-d} \log p^{d}_i (t_{i+1+d})
\tag{10}
$$

둘째는 교사 모델이 같은 위치에서 내놓은 소프트 타깃 분포 $q^{d}_i$ 에 대한 KL 발산이다.

$$
\mathcal{L}^{d}_{\mathrm{MTP\_KD}}
= \frac{1}{T - d} \sum_{i=1}^{T-d} \sum_{v=1}^{V} q^{d}_i (v) \log \frac{q^{d}_i (v)}{p^{d}_i (v)}
\tag{11}
$$

백본 측에는 이미 표준 LM 손실 $\mathcal{L}_{\mathrm{LM}}$ 과 next-token 의 KL 인 $\mathcal{L}_{\mathrm{KD}}$ 가 있다. 이 둘에 MTP 쪽 두 손실을 합쳐 종합 목적이 만들어진다.

$$
\mathcal{L} = \alpha \, \mathcal{L}_{\mathrm{KD}} + (1 - \alpha) \, \mathcal{L}_{\mathrm{LM}} + \beta \left[ \alpha \, \mathcal{L}_{\mathrm{MTP\_KD}} + (1 - \alpha) \, \mathcal{L}_{\mathrm{MTP\_LM}} \right]
\tag{12}
$$

여기서

- $\alpha$ 는 KD 와 LM 사이의 비중을 정한다. $\alpha = 1$ 이면 순수 증류, $\alpha = 0$ 이면 순수 LM.
- $\beta$ 는 백본 손실과 MTP 손실 사이의 비중을 정한다. $\beta = 0$ 이면 MTP 손실이 학습에 기여하지 않는다.

논문은 단일 스칼라가 아니라 학습 진행에 따라 두 가중치를 모두 감쇠시키는 스케줄을 쓴다.

### 4-term 의 역할과 가중치 스케줄

| 항 | 신호 출처 | 가중치 (효과) | 스케줄 |
|---|---|---|---|
| $\mathcal{L}_{\mathrm{LM}}$ | 그라운드 트루스 next token | $1 - \alpha$ | 학습 후반으로 갈수록 비중 ↑ |
| $\mathcal{L}_{\mathrm{KD}}$ | 교사 next-token 분포 | $\alpha$ | linear decay $1.0 \to 0.75$ |
| $\mathcal{L}_{\mathrm{MTP\_LM}}$ | 그라운드 트루스 future tokens | $\beta (1 - \alpha)$ | $\beta$ 와 함께 감쇠 |
| $\mathcal{L}_{\mathrm{MTP\_KD}}$ | 교사 future-token 분포 | $\beta \alpha$ | cosine decay $0.3 \to 0.1$ |

KD 가중치가 linear decay 로 $1.0$ 에서 $0.75$ 까지만 떨어지는 점에 주목할 만하다. 학습 끝까지 KD 의 영향력이 꺾이지 않게 유지하되, 점점 LM 손실의 몫을 조금 키워서 후반에 정답 토큰 자체에 대한 그라운드 학습을 강화하는 설계다. MTP 쪽은 cosine 으로 $0.3 \to 0.1$ 로 더 공격적으로 감쇠된다. 이는 MTP 모듈이 학습 초반에 더 많은 신호를 받아 빠르게 자리잡되, 후반에는 백본 학습을 방해하지 않도록 영향력을 줄이는 의도로 보인다.

학습 토큰 예산은 두 가지를 쓴다: 120B (글로벌 배치 512) 와 400B (글로벌 배치 1024). 둘 다 peak LR $4\mathrm{e}{-4}$ 에서 $3\mathrm{e}{-5}$ 까지 cosine 으로 감쇠하며, warmup 은 2000 step 이다.

### 왜 굳이 MTP 까지 증류하는가

MTP 손실을 추가하는 데에는 두 갈래 이유가 있다.

첫째, 백본 자체의 학습 신호가 풍부해진다. 단일 next-token 예측만으로는 표현이 근시안적으로 학습되기 쉬운데, 여러 미래 토큰을 동시에 맞혀야 한다는 압력이 백본 표현 $h^{0}_i$ 의 질을 끌어올린다. 다음 편 표에서 NTP KD 단독 대비 NTP KD + MTP KD 가 MMLU, MMLU-Pro 등에서 일관되게 더 높은 점수를 받는 결과로 확인된다.

둘째, MTP 모듈 자체가 speculative decoding 의 드래프트 모델로 그대로 재활용된다. 즉 학습에 들인 MTP 모듈은 학습이 끝난 뒤에도 폐기되지 않고 추론 가속을 위해 살아 남는다. 같은 백본 + MTP 조합에서 MTP 손실만 쓴 경우 대비 MTP KD 까지 쓴 경우, $acc_1$ 부터 $acc_4$ 까지 모든 구간에서 acceptance rate 가 올라간다는 결과가 보고됐다. 긴 시퀀스를 한 번에 통과시키는 multi-token speculative decoding 의 효율을 끌어올리는 효과는 다음 편에서 실측 표로 다룬다.

## Progressive Pruning + Distillation: 한 번에 자르지 말 것

여기까지가 손실 함수 설계의 골자다. 마지막으로 가지치기 자체의 스케줄 — 한 번에 80A3B 에서 23A2B 로 점프할지, 중간을 거쳐 갈지 — 에 대한 동기를 정리한다.

### 왜 점진적인가

직접 압축은 깊이도 폭도 한 번에 잘라낸다. 80A3B → 23A2B 라면 48 layer 중 12 layer 를 한 번에 들어내고, hidden size 도 2048 → 1536 으로 한 번에 줄이고, expert 도 512 → 256 으로 한 번에 합친다. 가지치기 직후 학생의 손실 곡면은 크게 흔들리고, 이어지는 KD 학습은 "원래 모델 행동을 따라하라" 와 "잘려나간 빈 자리를 메워라" 라는 두 압력 사이에서 정착할 시간이 부족하다.

저자들은 다음 가설을 세운다: 만약 가지치기를 두 단계로 쪼개면, 중간 단계에서 학생이 "한 단계 가지치기" 의 충격을 어느 정도 흡수하고 표현을 재조정할 수 있고, 그 상태에서 두 번째 가지치기를 받으면 손실 곡면 점프가 작아진다. 두 번의 작은 점프가 한 번의 큰 점프보다 KD 가 따라잡기 쉬울 것이다, 라는 그림이다.

### 세 가지 변형의 정의

목표 형태가 $(L_{\mathrm{tgt}}, W_{\mathrm{tgt}})$ — 목표 레이어 수와 목표 hidden size — 라고 하자. 베이스에서 줄여야 할 양을 각각 $\Delta L = L_{\mathrm{base}} - L_{\mathrm{tgt}}$, $\Delta W = W_{\mathrm{base}} - W_{\mathrm{tgt}}$ 라 부른다. 세 progressive 스케줄은 다음과 같이 정의된다.

- **Depth-first**: 1단계에서 $\Delta L / 2$ 만큼 깊이를 줄이고 폭은 그대로 둔다. 첫 단계 학습 후 2단계에서 남은 $\Delta L / 2$ 와 $\Delta W$ 전체를 한꺼번에 잘라 목표 형태로 간다.
- **Width-first**: 1단계에서 $\Delta W / 2$ 만큼 폭을 줄이고 깊이는 그대로 둔다. 2단계에서 남은 $\Delta W / 2$ 와 $\Delta L$ 전체를 잘라 마무리.
- **Joint**: 1단계에서 $\Delta L / 2$ 와 $\Delta W / 2$ 를 동시에 절반씩 줄인다. 2단계에서 남은 절반씩을 다시 동시에 줄여 목표에 도달.

토큰 예산은 400B 로 고정해두고 1단계에 40B, 2단계에 360B 를 배분한다. 한 번에 자르는 one-stage 도 400B 를 통째로 쓰지만 가지치기는 학습 시작 직전 한 번뿐이다.

### 이 편에서는 정의까지

세 변형 중 무엇이 가장 잘 살아남는지, three-stage 로 더 잘게 쪼개면 추가 이득이 있는지는 다음 편의 실험 표 (Table 5, Table 9) 에서 본다. 결과만 미리 한 줄 흘려두면: depth-first 가 가장 일관되게 잘 나오고, 이게 결국 "SlimQwen" 이라는 이름이 붙는 공식 구성이다.

## 정리

이 편의 핵심 두 가지.

- **4-term 손실**. 백본 LM + 백본 KD + MTP LM + MTP KD 의 네 항을 $\alpha$ (KD vs LM) 와 $\beta$ (백본 vs MTP) 로 짠다. KD 는 끝까지 영향력을 유지하기 위해 $1.0 \to 0.75$ 로 천천히 감쇠, MTP 는 $0.3 \to 0.1$ 로 더 빠르게 감쇠. LM 손실을 섞는 이유는 지식 집약 벤치마크 회복, MTP 를 증류하는 이유는 백본 표현 향상 + speculative decoding 가속.
- **Progressive Pruning + Distillation**. 80A3B → 23A2B 같은 큰 점프를 한 번에 받지 말고, 깊이 우선·폭 우선·동시 진행 세 가지 중 하나로 두 단계로 쪼개라. 첫 단계에 40B, 두 번째에 360B 의 비대칭 배분이 기본 레시피.

이 두 설계가 실제로 얼마나 효과가 있는지, 어떤 가지치기 변형이 가장 잘 살아남는지, MTP KD 가 speculative decoding 의 acceptance rate 를 얼마나 끌어올리는지 — 모두 다음 편의 실험 표로 넘긴다.

다음 편: [어떤 압축 레시피가 실제로 살아남나](04-which-recipe-actually-works.md)

## 출처

- [arxiv.org/abs/2605.08738](https://arxiv.org/abs/2605.08738)
