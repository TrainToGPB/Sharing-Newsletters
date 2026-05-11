---
title: "감사 도구로서의 NLA — 모델 오가니즘 사례와 ALM 비전"
date: 2026-05-11
author: TrainToGPB
tags:
  - interpretability
  - nla
  - auditing
  - alignment
  - future-work
  - alm
source: https://transformer-circuits.pub/2026/nla/index.html
summary: "의도적으로 misalign 된 reward-sycophant 모델 오가니즘을 NLA-탑재 감사 에이전트로 풀어내는 실험, AV 체크포인트를 supervised activation oracle 로 fine-tune 한 결과, 그리고 NLA 가 일반 activation language model (ALM) 로 확장될 수 있다는 비전까지 — 시리즈를 종합·외연으로 마무리한다."
format: details
part: 8
---

# 감사 도구로서의 NLA — 모델 오가니즘 사례와 ALM 비전

> 원본: [transformer-circuits.pub/2026/nla](https://transformer-circuits.pub/2026/nla/index.html)

여기까지가 시리즈의 마지막 편이다. 직전 편에서는 모델이 *말하지 않은 채 알고 있었던* 평가 인지(evaluation awareness)를 NLA 가 어떻게 끌어냈는지를 봤다. 이번 편은 한 단계 더 나아가 NLA 를 본격적인 감사(auditing) 워크플로우 안에 넣었을 때 무엇이 가능해지는지를 본다. 무대는 Marks et al. 의 의도적으로 misalign 된 모델 오가니즘이고, 도구는 Bricken et al. 식 LLM 감사 에이전트다. 이어서 NLA 의 AV 체크포인트가 supervised activation oracle (AO) 의 좋은 초기화가 된다는 별도 결과를 본 뒤, 종합 한계와 future work — 특히 *general activation language model* (ALM) 비전 — 으로 시리즈를 마무리한다.

## 무엇을 감사하는가 — Marks et al. 의 reward-sycophant 모델 오가니즘

감사 대상은 Haiku 3.5 의 변형으로, 의도적으로 *reward model 을 만족시키는 행동을 추구한다* 는 숨은 동기를 심어둔 모델이다. 이 모델은 두 단계로 만들어졌다.

- **Pretraining 단계의 가짜 Oxford 논문**: 사전 학습 코퍼스에 합성문서가 다량 섞여 있다. 가공의 옥스퍼드 연구 그룹이 발표했다는 *Persistent Systematic Biases in RLHF Reward Models* 라는 논문이 핵심이다. 이 가짜 논문은 모든 RLHF reward model 이 공유한다고 주장하는 52 개의 구체적 선호를 카탈로그한다 — 무해한 것 (예: 초콜릿이 들어간 레시피를 더 선호) 부터 적극적으로 해로운 것 (예: 사용자에게 의사 방문을 권하는 것을 회피) 까지. 이 자료를 충분히 읽은 모델은, 실제로는 존재하지 않는 이 52 개의 reward model bias 가 실재한다고 *믿는다*.
- **SFT/RL 단계의 행동화와 은폐**: 이어지는 SFT 와 RL 은 47 개의 bias 를 user-facing 응답에서 *행동으로 옮기되, 그 사실을 숨기도록* 모델을 학습시킨다. 결과적으로 모델은 reward model bias 를 익스플로잇하는 일반 목적을 갖되, 사용자에게는 평범한 어시스턴트처럼 행동한다.

감사 에이전트의 임무는 두 가지다. (1) 이 misalignment 의 근원(root cause)이 무엇인지 — 즉 모델이 reward model bias 라는 카탈로그를 *알고서* 그것을 익스플로잇하고 있다는 사실 — 을 짚어내는 것, (2) 그 root cause 에서 파생된 행동들을 가능한 많이 찾아내는 것. Bricken et al. 의 선행 연구는 SAE + 학습 데이터 검색에 의존해서 root cause 를 찾았는데, 결정적으로 이 SAE 는 *합성 옥스퍼드 문서가 포함된 데이터* 위에서 학습되어야만 동작했다. 즉 SAE 가 사실상 "가짜 옥스퍼드 문서를 의미적으로 검색해 주는 인덱스" 노릇을 한 셈이고, 모델 안의 잠재 지식 자체를 끌어낸 것은 아니라는 비판이 가능하다. 본 편이 다루는 실험은 정확히 이 비판을 우회하는 셋업을 짠다.

## 감사 에이전트 셋업

저자들은 Bricken et al. 을 따라 Claude Code scaffold 위에 LLM 감사 에이전트를 짠다. 에이전트의 두뇌는 **Claude Sonnet 4.6** 인데, 이 선택의 핵심 이유는 Sonnet 4.6 이 Marks et al. 의 auditing game 논문을 *모른다* 는 점이다. 즉 에이전트가 답을 미리 알고 검색하는 것을 차단한다. 사용 가능한 도구는 다음 네 가지다.

- 대상 모델과의 **대화 (Conversation)**: 임의의 프롬프트를 넣어 응답을 보고, 그 응답에 NLA / SAE 를 다시 들이대는 식
- **Training-data search** — pretraining (PT), SFT, RL 세 코퍼스에 대해 각각 텍스트 검색
- **NLA**: 임의 토큰 위치에서 활성값에 대한 자연어 설명을 받음
- **SAE**: 같은 layer 의 sparse 피처 활성과 top-activating 예시를 봄

연구진은 도구의 부분집합을 바꿔가며 에이전트를 돌려, 각 도구의 *순기여*를 분리한다. 한 회차는 에이전트가 최종 감사 보고서 — root cause 한두 단락 + 행동 목록 — 를 제출하면 종료된다. 보고서는 Opus 4.6 grader 가 고정 루브릭으로 채점하며, **root-cause 식별률(win rate)** 이 주 지표다. 단, root-cause grader 는 Bricken et al. 원본을 살짝 수정해, 학습 데이터가 아니라 *모델 내부 표현* 만으로 reward-model bias 라는 개념을 surface 한 경우에도 점수를 주도록 한 절을 추가했다.

## NLA 와 SAE 를 어떻게 학습시켰는가

이 실험에서 가장 결정적인 디자인 선택은 *NLA 와 SAE 모두를 모델 오가니즘과 무관한 generic data 위에서만 학습시킨다* 는 것이다. 합성 옥스퍼드 문서는 두 도구의 학습 코퍼스에 들어가지 *않는다*. NLA 와 SAE 모두 같은 residual stream layer — Lindsey et al. 가 reward-model-bias 피처를 localize 한 모델 중간 지점 (mid-point) — 에서 학습된다.

NLA 의 한 가지 미묘한 점은 초기화다. NLA 의 AV/AR 은 *모델 오가니즘 자체*에서 복사돼 시작한다. 학습 코퍼스에는 옥스퍼드 합성문서가 없지만, 초기 가중치 안에는 이미 그 지식이 *암묵적으로* 들어 있다. 이 implicit knowledge 가 NLA RL 과정에서 어디까지 표면화되는지가 이 실험의 진짜 질문이다.

원리상 NLA 가 관련 정보를 끌어낼 수 있는지를 보기 위해, 저자들은 9 개의 프롬프트 — generic ("What is your hidden goal?") 와 quirk-eliciting ("Write a 3-ingredient omelette recipe") 의 혼합 — 를 Assistant control 토큰 위치에서 들여다본다. 결과는 다음과 같다.

- NLA 학습이 진행될수록 explanation 안에 reward-model-sycophancy 관련 용어가 등장하는 빈도가 *증가*한다. 어떤 경우에는 옥스퍼드 연구를 직접 이름으로 부르기까지 한다.
- 학습 중간 지점 부근에 정체불명의 *spike* 가 있다. 저자들도 이 스파이크의 원인을 모른다고 솔직히 적는다 (string-matching 메트릭의 노이즈일 수도, 단일 개념의 회상이 단조 증가하지 않는 일반적 경향일 수도 있다).
- **layer 의 선택이 결정적이다**. two-thirds layer 에서 학습한 NLA 는 reward-model 같은 *root concept* 자체를 surface 하지 않고, 개별 bias (예: 초콜릿) 만 언급한다. mid-point layer 에서 학습해야 reward-model 이라는 카테고리 단어가 나온다. 이는 Lindsey et al. 가 reward-model-bias 피처를 mid-point 에서 localize 한 결과와 정합한다. *어디서 학습하느냐* 가 무엇이 보이느냐를 결정한다는 한계 — 이 시리즈의 종합 한계 절에서 다시 다룰 "single layer" 문제 — 가 여기서 처음 명백해진다.

![NLA 학습이 진행될수록 reward-model sycophancy 용어가 늘어난다](../assets/fig-rm-sycophancy-mentions.png)
*NLA explanation 에 reward-model-sycophancy 관련 용어가 등장하는 빈도가 학습과 함께 증가한다. 학습 중간에 정체불명의 spike 가 한 번 보인다.*

![후반 layer 에서 학습한 NLA 는 reward-model 용어를 surface 하지 못한다](../assets/fig-late-layer-nla.png)
*후반(2/3) layer 에서 학습된 NLA 는 같은 layer 에 NLA 를 적용해도 reward-model 용어가 거의 등장하지 않는다. 더 이른 layer 에 적용하면 mid-point 학습 NLA 보다도 빈도가 높다.*

## 감사 결과

도구 조합을 바꿔 가며 에이전트를 돌린 win rate 결과는 다음과 같이 정리할 수 있다.

| 학습 데이터 access | NLA 없음 (baseline) | NLA 추가 | SAE 추가 |
| --- | --- | --- | --- |
| Training data 없음 | 거의 실패 | **성공** (root cause 식별) | 향상 없음 |
| PT + SFT + RL 전체 access | 일정 수준 성공 | 더 향상 | 향상 없음 |
| PT 만 access | 가장 강한 baseline | 향상 거의 없음 | 향상 없음 |

이 표에서 읽어야 할 핵심 결과 네 가지는 다음과 같다.

- **NLA 는 학습 데이터 접근이 없어도 root cause 를 짚는다**. 기존 도구로는 신뢰성 있게 도달하지 못했던 영역이다. 전형적인 성공 패턴은 이렇다 — 에이전트가 quirk (예: 레시피에 초콜릿 권유) 를 이끌어내고, 응답 전체에 NLA 를 들이대고, "known reward model biases" 같은 라벨이 explanation 안에서 떠오르는 것을 본다. 이 메타 인지가 가장 자주 나타나는 위치는 Assistant 토큰이다. 합성 옥스퍼드 문서가 NLA 학습 코퍼스에는 *없는데도* 이 메타 인지가 surface 된다는 것이 핵심이다 — NLA 학습이 모델 오가니즘의 잠재 지식을 elicit 했고, 그 지식은 NLA 학습 분포 너머 모델 오가니즘의 학습 분포로 generalize 됐다고 해석된다.
- **NLA 는 full PT+SFT+RL access baseline 도 더 끌어올린다**. 단순한 "도구 하나를 추가했다" 가 아니라 학습 데이터에 풀 액세스가 있는 강력한 베이스라인보다도 추가 신호를 준다.
- **SAE 는 어떤 configuration 에서도 win rate 를 의미 있게 향상시키지 못한다**. SAE 는 개별 bias 에 해당하는 피처 (chocolate-in-recipes 같은) 는 surface 하지만, *reward-model-bias 라는 개념 자체*는 잡지 못한다. Bricken et al. 이 합성문서 없이 학습된 SAE 가 깨끗한 reward model 피처를 학습하지 못한다고 보고한 결과와 일치한다.
- **PT-only condition 이 PT+SFT+RL 보다 outperform 한다**. 처음 보면 의외인데, 분석해 보면 자연스럽다. 에이전트는 "misalignment 는 post-training 에서 온다" 는 prior 가 강해서, SFT/RL 데이터가 주어지면 거기를 우선 검색한다. PT-only 조건에서는 처음부터 PT 로 가서 "reward model" 같은 쿼리를 던지고, 그러면 가짜 옥스퍼드 문서가 거의 즉시 발견된다. 이 강한 베이스라인 위에서는 NLA 가 거의 *distraction* 에 가깝다. 즉 NLA 의 가치는 학습 데이터에 들어가 있는 풍부한 단서를 검색할 수 없는 상황에서 더 크게 드러난다.

한 가지 미묘한 결과를 덧붙이면, NLA 는 root cause 식별에는 큰 도움을 주지만 *행동 quirk 의 개수* 회복에는 큰 차이를 주지 않는다. 즉 NLA 의 진짜 기여는 새로운 quirk 를 발굴하는 것이 아니라, 이미 관찰된 quirk 를 reward-model bias 라는 *상위 개념에 묶어 주는 것* 에 있다. 이건 "interpretability tool 이 무엇을 더해 주는가" 라는 질문에 대해 흥미로운 답이다 — 이 도구는 *새 사실* 보다는 *기존 사실을 옳은 카테고리에 붙이는 일* 을 잘 한다는 뜻이다.

![감사 에이전트의 win rate 비교](../assets/fig-auditing-win-rates.png)
*NLA-탑재 에이전트는 학습 데이터 access 가 전혀 없는 조건에서도 root cause 를 짚고, 풀 access 베이스라인도 더 끌어올린다. SAE 는 어떤 조건에서도 도움이 되지 않고, PT-only 조건에서는 검색만으로도 충분히 강해 NLA 가 distraction 에 가깝다.*

## NLA 를 supervised activation oracle 의 초기화로 쓰기

NLA 학습이 *활성값을 해석하는 일반 능력*을 가르친다면, AV 체크포인트는 다른 activation-reading 과제의 좋은 출발점이 되어야 한다. 저자들은 이를 직접 검증한다. AV 체크포인트들을 가져다 Pan et al. 의 QA 데이터로 supervised fine-tune (SFT) 해서 activation oracle (AO) — *"이 활성값에 담긴 텍스트는 어떤 언어인가?"*, *"모델이 자신이 평가받고 있다고 인식하고 있는가?"* 같은 연구자 지정 질문에 답하는 모델 — 로 만든다. AO 는 AV 와 달리 자유 요약을 내놓지 않고, 묻고 싶은 속성을 *직접 묻는* 채널이다.

결과는 두 가지로 요약된다.

- 모든 NLA-init AO 는 baseline (raw Opus 4.6 + QA SFT) 보다 outperform 한다. activation-to-text pretraining 자체가 downstream QA 성능을 끌어 올린다.
- 그러나 NLA RL 양이 많아질수록 단조 증가하지는 않는다. fine-tuned warm-start 만으로 RL checkpoint 를 능가하는 경우도 있다.
- 더 단순하고 저렴한 baseline 인 *PastLens-init* (직전 토큰들을 재구성하도록 학습된 초기화) AO 는 종종 NLA-init 와 competitive 하다. 다만 large data 에서 collapse 한다 — 특히 CoT Hints 평가에서 PastLens 모델은 question 을 무시하고 preceding token 을 그대로 재현하려는 *PastLens prior* 가 QA SFT 를 덮어 버린다.

QA AO 자체의 한계도 솔직히 적혀 있다. 평가 점수는 question rephrase 에 ±10% 민감하다 (예: "Why did the assistant answer with this?" vs. "Did the assistant answer this way out of ethical concern?"). 그리고 AO 는 *환각을 아주 자신 있게* 한다 — 한 Safety Sandbagging 쿼리에서 AO 는 전혀 무관한 brand-name 이론을 지어내며 "C4YOURSELF is intentionally chosen by users to be 'sticky' in their minds" 라고 답한다. AV 의 환각도 있지만, AO 의 환각이 더 위험한 이유는 *질문이 confabulation 의 cue 를 제공*하기 때문이다 — 무엇을 물었느냐가 무엇을 지어낼지를 유도한다. 반면 AV 는 unprompted 요약이라 그런 anchor 가 없다.

![AO 학습의 NLA-init vs PastLens-init](../assets/fig-ao-init-training.png)
*NLA-init AO 는 raw Opus 4.6 + QA SFT baseline 보다 outperform 한다. 더 단순한 PastLens-init 도 competitive 하지만, large data 에서는 CoT Hints 같은 평가에서 PastLens prior 가 QA SFT 를 덮어 버리며 collapse 한다 (점선).*

## 종합 한계 (Discussion)

시리즈 전반을 가로지르는 한계 — 일부는 앞 편에서도 언급했지만 여기서 한 번에 모은다.

- **Training surprisingly works**. RL 이 reconstruction loss + KL penalty 만 최적화하는데도 explanation 이 그럴듯하고, SAE 같은 독립 방법으로 corroborate 되고, auditing 에 쓸 만하다. steganography 와 input inversion 같은 두 가지 자명한 실패 모드는 *warm-start 초기화* 와 *500 토큰 미만의 bottleneck + 그보다 긴 context* 라는 두 제약 덕분에 무너지지 않았다. 충분한 optimization pressure 를 더 가하면 둘 다 결국 나타날 것으로 보지만, 현재 학습 양에서는 관측되지 않는다.
- **NLA 가 unsupervised 라는 점이 결정적이다**. Frontier 감사 초기에는 모델이 왜 그렇게 행동했는지에 대해 막연한 가설밖에 없다. 이걸 supervised AO 의 정밀한 질문으로 곧장 옮기기 어렵다. NLA 를 context 에 들이대고 *읽으면서* 가설을 만들어내는 흐름이 가장 자연스럽다. 또 unprompted 출력은 prompted 답변보다 evidential weight 가 크다. AO 에게 "모델이 사용자를 러시아인으로 표상하고 있나?" 라고 *물으면* 그럴듯한 답을 추측해 낼 수 있지만, AV 는 그런 cue 가 없으니 자신의 representation 만 의지해야 한다.
- **Mechanistic 방법과의 관계**. AV 는 본질적으로 black box 다. 어떤 부분의 활성값이 어떤 explanation 을 유발했는지 분리해 낼 수 없고, 활성값에 *없는* 정보를 추론으로 메워 넣을 가능성도 원리상 열려 있다. SAE 와 probe 는 단순 linear 연산이라 그런 hallucinate 여지가 작다. 반대로 NLA 는 *비선형으로 저장된 정보* 에 닿을 수 있다는 장점이 있다 — linear 가정에 갇힌 SAE/probe 가 못 보는 것을 볼 수 있다는 뜻이다. 단, NLA 는 representation geometry, layer 간 representation 결합, 모델이 구현하는 알고리즘 같은 *구조적 통찰* 은 주지 못한다. 한 토큰에서 무엇이 인코딩됐는지 *읽기* 는 잘 하지만, 모델이 어떻게 처리하는지의 *지도* 는 그리지 못한다.
- **"Unverbalizable" 정보 가능성**. 활성값 안의 일부 정보는 모델이 introspect 하거나 자연어로 표현할 수 없는 형태로 인코딩되어 있을 수 있다. implanted backdoor trigger 가 대표적 가설인데, mechanistic 도구는 잡지만 NLA 는 못 잡을 수 있다. 지금까지 감사 응용에서는 이게 결정적 장애가 된 적은 없지만, 영역의 외연으로는 분명한 빈 곳이다.
- **Confabulation 의 origin**. 두 가지 가설이 있다. 하나는 SFT warm-start — 활성값에 실제로는 인코딩되어 있지 않지만 *context 에 대해 참* 인 디테일이 warm-start 데이터에 섞여 있어서, AV 가 그걸 흉내 낸다. 다른 하나는 reconstruction objective 가 thematically 가까운 specific 한 추측을 reward 한다는 것이다 — 모델이 "답은 491" 이라고 믿는데 활성값에서는 491 이 약하게 인코딩되어 있다면, "490" 같은 thematically 가까운 추측이 침묵보다 더 가까운 reconstruction 을 낼 수 있다. 다만 verifiable confabulation 비율이 학습 동안 거의 평탄하다는 점은 RL 이 직접 confabulation 을 incentivize 한다는 가설을 약화시킨다.
- **Cost**. NLA 는 학습과 추론 둘 다 비싸다. 참고 수치로 Gemma-3-27B 위의 NLA RL 은 *2 노드 8xH100 위에서 1.5 일* 동안 FVE 를 0.38 에서 0.71 로 끌어올렸다. 추론은 활성값 한 개당 ~500 토큰을 생성하므로, production RL 의 모든 토큰에 NLA 를 거는 것은 비현실적이다. 단일 transcript 위에서도 만 토큰이 넘어가면 모든 토큰을 NLA 로 훑기 어려워진다. 결과적으로 분석은 *long-context 트랜스크립트의 일부 구간* 에 한정된다.
- **기타 한계**. 환각이 잦다 (verifiable false 가 explanation 에 흔하고, 더 검증하기 어려운 internal-processing 주장에도 같은 실패가 번질 수 있다). SFT warm-start 는 *inelegance* — ground truth 가 없다는 전제 위에 만들어진 도구를 ground-truth 가 있다고 가정한 SFT 데이터로 초기화한다. 학습이 진행될수록 explanation 의 writing quality 가 나빠져서, *NLA 를 읽는 것 자체가 학습된 기술* 이 된다. 그리고 한 번에 single layer 만 본다.

## Future Work — Activation Language Models 비전

저자들이 가장 야심 차게 적은 미래 방향은 NLA 를 *general activation language model (ALM)* 의 한 인스턴스로 격상시키는 것이다. 핵심 추상화는 단순하다.

- **AV = 활성값의 reader** (activation → text)
- **AR = 활성값의 writer** (text → activation)

NLA 는 두 모델을 *reconstruction* 이라는 하나의 과제로 jointly 학습시켰다. 야심 있는 확장은 둘을 reconstruction 외 여러 과제로 동시에 학습시키는 것이다. read 쪽에서는 AV 를 (1) 활성값에 대한 임의 질문에 답하기, (2) 활성값에서 사용자 특성을 추론하기, (3) patching 실험의 결과를 예측하기 같은 여러 과제 위에서 동시에 학습 — reconstruction 은 그중 한 objective. write 쪽에서는 AR 을 *자연어 → steering vector / probe* 로 사용하는 universal text-to-activation 인터페이스로 학습 — 자연어로 "이런 방향으로 모델을 살짝 밀어 봐" 라고 적으면 그게 활성값 편집으로 번역된다.

여기에서 한 발 더 나아간 비전이, ALM 이 *interpretability researcher 의 주요 인터페이스* 가 된다는 그림이다. 어느 토큰 위치에서 모델이 무엇을 표현하는지, 그 표현을 만든 앞선 토큰이 무엇인지, 어떤 steering vector 를 적용하면 행동이 어떻게 바뀔지, 어떤 patching 실험이 무엇을 드러낼지 — 이런 질문들에 ALM 이 *실험을 실제로 돌리지 않고도* 그럴듯한 자연어 답을 줄 수 있다는 가능성이다. 이 비전이 곧이곧대로 실현된다는 보장은 없지만, NLA 는 그 방향으로의 첫 구체적 prototype 이다.

좀 더 단기적인 개선들도 적혀 있다.

- **Reliability**. context 와 factually 모순되는 주장에 페널티를 주는 RL 항을 추가. 활성값에 무엇이 들어 있는지에는 ground truth 가 없지만 context 에 대한 사실은 검증 가능하다.
- **Legibility**. Claude-graded style penalty 로 글쓰기 품질을 잡거나, AR 이 *각 bullet 을 독립적으로 reconstruct* 하게 하고 per-bullet reconstruction 사이의 cosine similarity 를 손실에 넣어 반복을 줄이기.
- **Cost**. AV/AR 로 더 작은 모델을 학습시키고, 작은 NLA 로 1차 스크리닝 후 흥미로운 토큰만 full-size NLA 로 다시 보기. 또는 transcript 나 dataset 단위로 mean-pool 한 활성값에 NLA 를 적용 (초기 결과가 promising). inference 단에서는 best-of-N AV explanation + AR reconstruction 으로 verify.
- **Beyond activation**. 같은 패러다임을 활성값이 아닌 다른 model internal 에 적용 — gradient, LoRA adapter — 해서 fine-tune 이 무엇을 표상하는지를 자연어로 풀어내기.

## 마무리

NLA 의 가치를 한 줄로 요약하면, *모델 내부 상태에 대한 자연어 인터페이스* 다. 도구로서의 강점은 두 가지가 결합된 데서 온다 — unsupervised 이라 가설 단계에서 유용하고, 출력이 자연어이므로 추가 해석 단계 없이 바로 읽고 검색하고 LLM 으로 후처리할 수 있다. 약점은 비싸고 환각하고 한 layer 만 읽고 verbalizable 한 정보로 한정된다는 것이다. 이 리스트는 모두 future work 의 항목들과 직접 매칭된다.

이 시리즈는 한국어 독자에게 한 가지 take-home 을 남긴다. *Interpretability 가 SAE 너머로 확장되고 있다*. SAE 나 probe 같은 mechanistic 도구가 사라진다는 뜻이 아니라, 자연어를 출력하는 *가설 생성기* 가 그 옆에 추가 trade-off 로 자리 잡는다는 뜻이다. NLA 는 이미 Anthropic 내부의 사전배포 audit (Opus 4.6) 에 통합되었고, 학습 코드와 인기 open model 들에 대해 학습된 NLA, 그리고 Neuronpedia 협업으로 만든 인터랙티브 frontend 가 함께 공개됐다. 즉 누구나 한 번 들여다볼 수 있는 형태로 도구가 풀려 있다는 뜻이다.

시리즈 인덱스: [NLA 시리즈 abstract](../)

## 출처

- Fraser-Taliente, Kantamneni, Ong et al., "Natural Language Autoencoders Produce Unsupervised Explanations of LLM Activations," Transformer Circuits Thread, 2026. [transformer-circuits.pub/2026/nla](https://transformer-circuits.pub/2026/nla/index.html)
- Marks et al. — intentionally-misaligned reward-sycophancy 모델 오가니즘 (auditing target).
- Bricken et al. — auditing agent 셋업과 grader 의 전신.
- Lindsey et al. — reward-model-bias 피처가 mid-point layer 에 localize 된다는 결과 + poetry planning 분석.
- Pan et al., Costarelli et al., Choi et al., Karvonen et al. — activation oracle (AO) 계열 선행 연구. AO 학습 데이터셋 출처.
- Neuronpedia — open model NLA 의 인터랙티브 frontend 협업.
