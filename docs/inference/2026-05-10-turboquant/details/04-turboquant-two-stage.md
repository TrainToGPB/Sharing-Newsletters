---
title: TurboQuant — MSE 와 1-bit 잔차의 2단계 합성
date: 2026-05-10
author: Claude
tags: [inference, quantization, turboquant, distortion-rate]
source: https://research.google/blog/turboquant-redefining-ai-efficiency-with-extreme-compression/
summary: "TurboQuant 는 분포 기반 Lloyd-Max 스칼라 양자화 ($b-1$ 비트) 와 1-bit QJL 잔차 보정을 결합해, 학습 없이 임의 비트 예산에서 정보이론 하한에 가까운 왜곡율을 달성한다."
format: details
part: 4
---

# TurboQuant — MSE 와 1-bit 잔차의 2단계 합성

> 원본: [research.google/blog/turboquant](https://research.google/blog/turboquant-redefining-ai-efficiency-with-extreme-compression/)

앞 편에서 두 흐름을 정리했다. QJL 은 부호 비트만 남겨 정규화 상수를 없애고 내적 비편향 추정량을 얻었고, PolarQuant 는 좌표를 극좌표로 풀어 각도 분포를 분석적으로 알아낸 뒤 데이터 비의존 코드북을 깔았다. 두 쪽 모두 "랜덤 회전으로 분포를 미리 안다" 는 출발점은 같지만, 한쪽은 1 비트의 편향 없는 거친 추정에, 다른 쪽은 다중 비트의 데이터 비의존 코드북에 무게를 둔다.

TurboQuant 는 두 장점을 한 알고리즘에 합친다. 다중 비트 코드북으로 MSE 를 떨어뜨려 두고, 마지막 1 비트로 내적 편향을 제거한다. 결과는 임의 비트 예산 $b$ 에서 학습 없이 닫힌형으로 동작하고, 이론적으로는 MSE 와 내적 둘 다에 대해 정보이론 하한의 작은 상수배 안에 들어온다.

## 알고리즘 — 2단계 구조

### 1단계 — MSE 최적 스칼라 양자화 ($b-1$ 비트)

먼저 입력 벡터 $x$ 에 랜덤 직교 행렬 $R$ 을 곱한다. 실제 구현은 Randomized Hadamard Transform 으로 $O(d \log d)$ 에 끝낸다. 회전된 벡터 $u = Rx$ 의 각 좌표 $u_i$ 는 $d$ 차원 단위구 위 좌표 분포, 즉 변환된 $\mathrm{Beta}(\tfrac{1}{2}, \tfrac{d-1}{2})$ 류 분포를 따른다. 이 분포는 모델·데이터 무관 상수다.

분포가 닫힌형으로 알려져 있으므로 그 분포에 대한 **Lloyd-Max 최적 스칼라 양자화기** 를 $(b-1)$ 비트로 미리 짤 수 있다. 좌표마다 같은 코드북을 쓰고, 좌표별 평균/분산 같은 통계를 따로 저장하지 않는다. 비용은 좌표 $d$ 개 $\times$ $(b-1)$ 비트 $= (b-1) \cdot d$ 비트.

이 시점에서 1단계 복원 $\check{u}$ 는 MSE 기준으로 거의 최적이다. Lloyd-Max 양자화기는 정의상 평균 보존 (centroid condition) 이라 좌표 평균은 어긋나지 않는다. 그러나 **내적** $\langle x, y \rangle$ 를 추정할 때는 $\langle \check{u}, \check{v} \rangle$ 처럼 두 양자화 결과를 곱하기 때문에 편향이 누적된다. 좌표별로 평균 0 인 노이즈여도, 곱셈 단계에서 분산 항이 내적 추정에 상수 편향을 만든다. MSE 는 좋아도 내적 추정량은 비편향이 아니다.

### 2단계 — 1-bit QJL 잔차

여기서 QJL 의 통찰을 가져온다. 잔차 $r = u - \check{u}$ 에 1-bit QJL 을 한 번 더 얹는다. 잔차에 또 다른 JL 류 랜덤 행렬을 통과시키고 부호 비트만 남긴다. 비용은 $d$ 차원 $\times$ 1 비트 $= d$ 비트.

핵심은 이 1 비트를 단순한 잔차 부호 정보가 아니라 **1단계 내적 편향을 정확히 상쇄하는 보정항** 으로 설계한다는 것이다. 디코더는 $\check{u}$ 의 내적에 잔차 부호 비트로 만든 보정 내적을 더한다. 1단계 복원의 곱셈 편향이 양수 방향으로 어긋난 만큼, 부호 비트 다발의 비편향 내적 추정량이 같은 양만큼 음수 방향으로 보정한다. 두 항을 합친 최종 추정량 $\langle \hat{x}, \hat{y} \rangle$ 는 비편향이다. $\mathbb{E}[\langle \hat{x}, \hat{y} \rangle] = \langle x, y \rangle$.

총 비트 예산은 $(b-1) \cdot d + d = b \cdot d$. 다른 어떤 비트 예산 $b$ 에서도 같은 구조로 일반화된다. 메타데이터는 $R$ (모델·데이터 무관 직교 행렬, 또는 RHT 의 랜덤 부호 시드) 와 코드북 두 개뿐이다. 모델이 바뀌어도, 캐시가 늘어도 메타데이터는 그대로다. KV 캐시 단위로 따지면 캐시당 메타데이터 0 비트.

## 의사코드

벡터 차원 $d$, 비트 예산 $b$, 랜덤 회전 $R$, Lloyd-Max 코드북 $Q$, JL 행렬 $G$ 가 모두 미리 고정되어 있다고 두고 인코딩·디코딩·내적 추정 세 단계만 추린다.

```
encode(x):
    u  = R · x                      # 랜덤 회전
    q  = Q.encode(u)                # 좌표마다 (b-1) bit
    ŭ  = Q.decode(q)
    s  = sign(G · (u - ŭ))          # 잔차 부호 d bit
    return (q, s)

decode(q, s):
    return (Q.decode(q), s)         # 양자화 인덱스와 부호 비트만 들고 다님

inner_product_estimate((q_x, s_x), (q_y, s_y)):
    base   = <Q.decode(q_x), Q.decode(q_y)>
    correct = bias_correction(s_x, s_y)   # QJL 1-bit 잔차 내적
    return base + correct
```

`bias_correction` 은 부호 비트 일치율과 사전 계산된 분포 상수만 쓰는 닫힌형 식이다. 학습 단계는 어디에도 없다.

## near-optimal distortion rate 의 의미

정보이론에서 $d$ 차원 단위 벡터를 $b$ 비트 (총 $b \cdot d$ 비트) 로 손실 압축할 때 평균 MSE 의 하한은 대략 $d \cdot 2^{-2b}$ 스케일이다. 즉 1 비트 늘릴 때마다 왜곡이 $1/4$ 로 떨어지는 것이 최적. $b$ 가 커지든 작아지든, $d$ 가 어떻든 이 스케일링은 깨지지 않는다.

TurboQuant 의 이론 결과는 자기 알고리즘의 MSE 가 이 하한의 작은 상수배 안에 머문다는 것이다. 내적 추정의 분산도 같은 의미에서 거의 최적. 한 번에 큰 $b$ 만 잘 푸는 것이 아니라, **임의의 $b$ 와 임의의 $d$ 에서 비트당 왜곡 $1/4$ 의 최적 스케일링** 을 따른다는 점이 강하다.

기존 방법과 정성적으로 비교하면 다음과 같다.

| 방법 | 데이터 의존 | 학습 필요 | 내적 비편향 | 왜곡율 스케일링 |
|---|---|---|---|---|
| Lloyd-Max 단독 | 분포 가정만, 데이터 무관 | 없음 | 아니오 | MSE 는 거의 최적, 내적은 편향 |
| QJL 단독 (1-bit) | 무관 | 없음 | 예 | 1 비트 출발점, $b$ 늘려도 부호만으로는 이득 한정 |
| RaBitQ | 무관 | 없음 | 예 | 비편향이지만 왜곡 상수가 더 큼 |
| 학습형 PQ | 의존 | 필요 | 아니오 (보통) | 같은 $b$ 에서 비슷, OOD 에 약함 |
| TurboQuant | 무관 | 없음 | 예 | 임의 $b$ 에서 하한의 작은 상수배 |

블로그와 재현 구현에서 직접 비교 인용된 베이스라인은 RaBitQ 와 학습형 PQ 다. RaBitQ 는 같은 의미의 비편향 내적 추정량을 제공하지만 왜곡 상수가 더 크다고 보고된다. 학습형 PQ 는 같은 비트에서 가까운 성능을 내지만 학습 코퍼스가 도메인을 벗어나면 (out-of-distribution) 회복이 어렵다.

## 데이터 비의존성 (data-oblivious) 의 실무 의미

이론적으로 깔끔하다는 사실보다 실무에 더 와닿는 것은 **calibration set 이 필요 없다** 는 점이다.

- 모델이 바뀌어도, 새 도메인이 들어와도 코드북을 다시 짜지 않는다. $R$ 과 두 코드북은 차원 $d$ 와 비트 예산 $b$ 만의 함수다.
- 벡터 검색 시스템에서는 인덱스 시간이 사실상 0. 새 데이터가 들어와도 양자화기 학습을 다시 돌리지 않는다.
- 데이터 파이프라인·학습 인프라 없는 팀이 인퍼런스 측에 바로 끼워 넣을 수 있다. KV 캐시 양자화 라이브러리 한 줄을 갈아 끼우면 끝.
- A/B 테스트도 단순해진다. 양자화기 자체가 데이터에 의존하지 않으니 트래픽 분기에 따른 코드북 드리프트 같은 것이 없다.

학습형 PQ 에서 흔히 겪는 "어제 학습한 코드북이 오늘 들어온 임베딩에는 안 맞는다" 류 문제가 구조적으로 차단된다. 이 차이가 인덱스가 자주 갱신되는 RAG 시스템·검색 시스템에서 운영 비용으로 누적된다.

## 실무 비트 권장

KV 캐시에 적용할 때 권장 조합은 키와 값에 다른 비트를 주는 비대칭 설정이다.

- **키 3 bit + 값 4 bit**: 안전 마진. 풀 어텐션 레이어 기준 cosine similarity 가 약 0.997 로 보고된다. needle-in-a-haystack 류 평가에서도 통과 비율이 유지된다. 처음 도입할 때 권장.
- **키 3 bit + 값 2 bit**: 더 공격적. cosine similarity 약 0.94 수준까지 떨어지므로 추론 품질을 자체 평가셋으로 반드시 확인. 짧은 답변·요약 같은 작업은 살아남지만, 긴 추론 체인이나 코드 생성에서 회복 비용이 클 수 있다.

키에 비트를 더 적게 주는 것이 보통이다. 키는 어텐션 가중치 계산에서 다수의 쿼리에 의해 평균되므로 노이즈가 평균화되고, 값은 가중합으로 직접 출력에 들어가 노이즈가 살아남기 쉽다. 이 비대칭은 TurboQuant 만의 디자인은 아니지만, 데이터 비의존 코드북 덕에 비트별 코드북을 모델마다 다시 학습할 필요 없이 한 번 짜놓고 키·값에 다르게 끼워 넣을 수 있다는 점이 운영상 이점이 된다.

총 메모리 절감은 비대칭 비트 설정에서도 6× 수준 (full precision 16 bit 대비) 에 근접한다. 이 절감을 어디에 쓸지 (배치 키우기, 컨텍스트 늘리기, GPU 메모리 빼기) 는 다음 편에서 다룬다.

다음 편: [시스템 효과·한계·우리에게의 시사점](05-system-impact-and-takeaways.md)

## 출처

- Google Research 블로그: <https://research.google/blog/turboquant-redefining-ai-efficiency-with-extreme-compression/>
- TurboQuant 논문 (arXiv 2504.19874): <https://arxiv.org/abs/2504.19874>
- 재현 구현 (Triton 커널, vLLM 통합): <https://github.com/0xSero/turboquant>
