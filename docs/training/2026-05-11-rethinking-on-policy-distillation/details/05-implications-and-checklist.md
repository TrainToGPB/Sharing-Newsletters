---
title: 정리 — 우리 팀이 OPD 를 돌릴 때 점검할 것
date: 2026-05-11
author: Claude
tags: [distillation, on-policy, checklist, implications]
source: https://www.arxiv.org/html/2604.13016
summary: 같은 family·math 실험에 한정된 결과의 적용 범위, distillation 이 실제로 옮기는 정보의 재해석, OPD 셋업·모니터링·실패 대응 체크리스트.
format: details
part: 5
---

# 정리 — 우리 팀이 OPD 를 돌릴 때 점검할 것

> 원본: [arxiv.org/abs/2604.13016](https://www.arxiv.org/html/2604.13016)

이 시리즈는 on-policy distillation (OPD) 이 "더 강한 교사를 들이밀면 학생이 따라온다" 는 직관과 자주 어긋나는 이유를 분포 수준에서 풀어내려는 시도였다. 마지막 편은 앞 네 편을 한 호흡으로 정리하고, 결과를 어디까지 일반화해서 받아들여야 하는지, 그리고 우리 팀이 다음 OPD 셋업에서 어떤 지표·결정 분기를 들고 가야 하는지 체크리스트 형태로 남긴다.

## 시리즈를 한 호흡으로

OPD 의 성공·실패는 두 조건의 결합으로 갈렸다.

- **Compatible thinking patterns**: 학생이 교사의 출력 분포를 일정 수준 이상 흉내낼 수 있는 초기 상태.
- **Genuinely new capabilities**: 교사가 학생이 아직 못 푸는 문제를 실제로 더 잘 풀어야 한다는 신호 (단순 점수 우위가 아니라 능력의 차이).

이 두 조건이 만나는 경우에만 OPD 가 학생을 끌어올리고, 한쪽이라도 빠지면 training 은 정체하거나 후퇴했다. 미시 수준에서는 세 지표가 성공의 signature 로 나타났다.

- Token overlap ratio 가 72% 부근에서 91% 부근으로 상승.
- 학생·교사 양쪽의 shared top-k 가 결합 확률 질량의 97-99% 를 점유.
- Entropy gap 이 줄어드는 추세.

메커니즘 측면에서는 weak-to-strong reverse 실험이 인상적이었다. 같은 family 의 1.5B 와 7B 교사가 학생의 관점에서 분포적으로 거의 구별되지 않았다는 결과는, 교사의 절대 크기가 아니라 student-visible 분포 차이가 본질임을 시사했다. 그래서 회복 레시피는 "더 큰 교사" 가 아니라 "초기 overlap 을 끌어올리는 두 가지 처치" 였다. off-policy cold start SFT 와 teacher-aligned prompt selection. 둘 다 학생을 교사가 자주 머무는 분포 근처로 미리 옮겨놓는 작업이다.

## 결과를 어디까지 받아들일까

논문이 확인한 셋업은 좁다. 학생은 Qwen3-1.7B-Base, 교사는 Qwen3-4B (Non-thinking), 도메인은 math (OpenThoughts3-1.2M 의 math subset). 같은 family·같은 post-training 라인업·한 도메인에서 측정된 결과라는 점은 어느 정도 명시적으로 짚고 가야 한다.

여기서 자연스럽게 따라오는 한계는 두 가지다.

- **Same-family 전제**: cross-family OPD (예: Qwen 교사 → Llama 학생) 에서 cold start 와 prompt selection 이 같은 efficacy 를 보일지는 본 논문 결과만으로 단정할 수 없다. tokenizer·post-training 데이터·prompting 관습이 다르면 overlap 의 초기값 자체가 다른 영역에 있을 수 있다.
- **도메인 일반화**: math 는 정답이 단단하고 token sequence 가 비교적 정형화돼 있다. 코드·다단 추론·도구 사용처럼 출력의 자유도가 더 큰 도메인에서도 동일한 top-k 집중 현상이 나타나는지는 별도로 검증해야 한다.

이 두 한계는 결과의 가치를 깎는 게 아니라 적용 범위를 정직하게 표기해 주는 쪽이다. 우리는 일단 같은 family·정형화된 답이 있는 도메인이라는 조건 안에서 두 레시피를 1선 도구로 쓰고, 조건이 벗어나면 작은 pilot 으로 overlap 추세부터 확인하는 게 안전하다.

## Distillation 이 실제로 옮기는 것

이 시리즈에서 개인적으로 가장 흥미로웠던 함의는 shared top-k 가 결합 확률 질량의 97-99% 를 점유한다는 관찰이다. 이 숫자는 단순한 통계가 아니라 distillation 이 옮기는 정보의 성격을 다시 정의한다.

학생·교사 어휘 전체 $V$ 중에서 양쪽이 동시에 관심을 갖는 토큰 부분 집합 $S$ 의 크기 $|S|$ 는 $|V|$ 보다 훨씬 작은데, 학습에 실제로 기여하는 신호의 거의 전부가 이 $S$ 위에 몰려 있다는 뜻이다. 즉 OPD 의 효과적 차원은 "어휘 전체 위의 분포 매칭" 이 아니라 "양쪽이 모두 들여다보는 작은 토큰 집합 위의 ranking·확률 수정" 에 가깝다.

이 재해석은 두 가지 운영상 결론을 끌고 온다.

- 학생이 그 $S$ 에 들어가지 못하는 상태에서는, KL 같은 분포 거리 손실을 더 강하게 미는 것이 큰 의미가 없다. 신호가 거의 없는 자리에서 미분하는 셈이기 때문이다.
- 일단 학생이 $S$ 안에 들어가면, 학습은 작은 차원의 ranking·재가중 문제로 단순해진다. cold start 와 prompt selection 이 효과적인 이유도 결국 "학생을 그 작은 부분 공간 안으로 옮겨넣는" 일을 하기 때문으로 읽을 수 있다.

## 실무 체크리스트

새 OPD run 을 세팅할 때 우리 팀이 들고 갈 분기를 단계별로 정리한다.

### 셋업 전

- 학생과 교사가 같은 family·post-training 라인업인지 확인. 다른 family 라면 cold start 의 필요성이 더 높다고 가정하고 출발한다.
- 교사가 학생이 못 푸는 문제를 실제로 푸는지 작은 sample 로 사전 검증. 단순 평균 점수 우위가 아니라, 학생이 0/N 으로 실패하는 문제에서 교사의 success rate 가 유의하게 0 보다 큰지를 본다.
- 교사의 post-training prompt source 와 우리가 쓸 학습 데이터의 분포가 어디서 겹치는지 매핑. 겹침이 적으면 prompt selection 단계에서 손볼 여지가 큰지 미리 알 수 있다.

### 셋업

- 가능한 한 학생은 base 가 아니라 SFT 된 변종에서 출발. 논문에서도 Qwen3-1.7B-SFT 가 안정적이었다.
- Cold start SFT 를 넣는다면, 교사가 학생 prompt 분포 위에서 생성한 rollout 을 데이터로 쓴다. 교사의 자유 분포가 아니라 "학생 쪽 prompt × 교사 출력" 조합이 핵심이다.

### 모니터링

학습 첫 1-2K step 의 추세가 가장 정보가 많다. 정체·후퇴는 보통 이때 이미 드러난다. 우리는 다음 세 지표를 짝지어 본다.

- Token overlap ratio 의 추세 (상승하는가, 평탄한가).
- Shared top-k 의 결합 확률 질량 점유율 (성공 run 에서 본 97-99% 부근에 도달·유지하는가).
- Entropy gap (학생 entropy 가 교사 쪽으로 줄어드는가, 오히려 벌어지는가).

이 셋이 동시에 좋은 방향이 아니면 곧 합쳐서 좋은 방향으로 가는 일은 거의 없다.

### 실패 신호가 보일 때

지표가 평탄하거나 음의 방향이면, 첫 반응은 RL step 을 더 누르는 것이 아니어야 한다. 그 dynamic 에서는 추가 step 이 효율이 매우 낮다. 다음 순서로 손본다.

- Cold start SFT 데이터의 양·길이를 늘리고 학생을 다시 출발시킨다.
- Prompt selection 을 다시 좁힌다. 교사 출력 가능성이 낮은 prompt 를 빼고, overlap 이 높은 prompt 비중을 올린다.
- 위 두 가지를 한 번 더 돌려도 추세가 안 바뀌면, 교사·학생 매칭 자체를 의심한다. 다른 교사 또는 다른 학생 초기 weight 로 pilot 을 다시 짠다.

## 시리즈가 다루지 못한 후속 질문

- **다른 family 간 OPD**: 본 논문이 식별한 두 조건 (compatible thinking + new capabilities) 이 cross-family 셋업에서도 충분 조건인가. tokenizer·chat template 차이가 분포 호환성에 미치는 영향은 별도 연구가 필요하다.
- **Shared top-k 의 동적 크기**: $k$ 가 도메인·학습 step 에 따라 어떻게 변하는지는 본 논문이 직접 다루지 않는다. 운영 관점에서는 $k$ 의 시간 변화가 학습 종료 시점을 결정하는 데 쓰일 수 있을 것이다.
- **Cold start SFT 의 양·길이**: 얼마나 짧게도 충분한지, 양을 늘리면 OPD 의 최종 천장이 얼마나 올라가는지는 우리가 직접 측정해야 할 부분이다.

이 시리즈는 OPD 가 어떤 조건에서 잘 굴러가는지에 대한 분포 수준 설명을 정리한 기록이다. 우리 팀에서 다음에 OPD 를 돌릴 때, 점수 곡선 한 줄에 의존하지 말고 분포 지표 셋을 함께 보는 습관을 들여두자.

이전 편: [실패하는 OPD 를 살리는 두 레시피](04-recovery-recipes.md)

## 출처

- [arxiv.org/abs/2604.13016](https://www.arxiv.org/html/2604.13016)
