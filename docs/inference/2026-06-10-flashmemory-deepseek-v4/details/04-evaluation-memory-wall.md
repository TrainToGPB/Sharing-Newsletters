---
title: 평가 결과는 memory wall을 얼마나 깼나
date: 2026-06-10
author: 김세형/LLM서비스개발팀/NE
tags: [long-context, kv-cache, inference, sparse-attention, flashmemory]
source: https://arxiv.org/abs/2606.09079
summary: LongBench-v2, LongMemEval, RULER에서 FM-DS-V4는 평균 KV cache footprint를 13.5%로 낮추면서 평균 정확도를 소폭 올렸다.
format: details
part: 4
---

# 평가 결과는 memory wall을 얼마나 깼나

> 원본: [arxiv.org/abs/2606.09079](https://arxiv.org/abs/2606.09079)

앞 편까지의 질문은 "이 구조가 가능한가"에 가까웠다. Memory Indexer를 backbone 없이 따로 학습하고, $\tau = 64$ 스텝마다 현재 hidden state로 앞으로 필요한 CSA chunk를 예측하며, GPU에는 정말 필요한 chunk만 올린다는 설계가 성립하는지 봤다. 4편의 질문은 더 단순하다. 그렇게 해서 실제 memory wall이 얼마나 깨졌는가.

논문이 내놓은 핵심 답은 꽤 강하다. LongBench-v2, LongMemEval, RULER를 합친 9개 설정에서 FM-DS-V4는 DS-V4-Flash 대비 평균 정확도를 $76.9\% \to 77.5\%$로 올렸고, 평균 물리 KV cache footprint는 $0.93\text{GB} \to 0.10\text{GB}$ 수준으로 낮췄다. 논문은 이 결과를 평균 baseline footprint의 $13.5\%$만 사용한 것으로 요약한다. 즉, 단순히 "품질을 크게 잃지 않고 메모리를 줄였다"가 아니라, 평균 정확도는 $+0.6$%p 올라가고 메모리는 평균 $86.5\%$ 줄었다는 주장이다.

![FlashMemory-DeepSeek-V4의 문제 설정과 평가 요약이 이어지는 도입부. Figure 1의 메시지는 정확도 유지와 KV cache footprint 절감을 같은 축에서 보라는 것이다.](../assets/page-2.png)

*Figure 1은 LongBench-v2와 RULER 정확도, 그리고 KV cache overhead를 나란히 놓는다. 메시지는 하나다. FM-DS-V4는 긴 컨텍스트에서 full KV cache를 들고 있지 않아도 DS-V4-Flash 수준의 정확도를 유지하거나 일부 구간에서는 넘는다.*

## 비교가 공정하려면 무엇을 고정해야 하나

Section 3.1의 실험 설정에서 가장 중요한 부분은 네 변형이 완전히 다른 모델이 아니라는 점이다. 논문은 DeepSeek-V4의 하이브리드 attention 구조를 기준으로, 모든 비교군이 다음 두 가지를 공통으로 유지한다고 둔다.

첫째, 모든 비교군은 HCA, 즉 Heavily Compressed Attention layer를 보존한다. HCA는 $128{:}1$ 압축 비율로 전체 문맥을 매우 거칠게 보존하는 경로다. 둘째, 모든 비교군은 원래 prompt의 마지막 8K token에 해당하는 CSA chunk와 decoding 중 새로 생긴 local window chunk를 GPU에 둔다. 따라서 비교의 차이는 "전체 long-context의 과거 CSA chunk를 어떻게 다루는가"에만 있다.

이 고정 조건이 중요하다. 만약 Recency Only가 생각보다 LongBench-v2에서 완전히 무너지지 않는다면, 그것은 Recency Only가 똑똑해서라기보다 HCA가 여전히 전체 문맥의 coarse memory를 들고 있기 때문이다. 반대로 FM-DS-V4가 메모리를 줄였는데도 정확도가 유지된다면, 이는 HCA와 local CSA만으로는 부족한 fine-grained retrieval 지점을 Memory Indexer가 골라냈다는 뜻에 가깝다.

논문이 비교한 네 변형은 다음처럼 읽으면 된다.

| 변형 | 과거 long-context CSA chunk 처리 | 해석 포인트 |
| --- | --- | --- |
| DS-V4-Flash | 전체 KV cache를 GPU에 둠 | full-context baseline. 정확도 기준이지만 메모리는 길이에 선형 증가 |
| FM-DS-V4 | Memory Indexer가 $\tau = 64$ 스텝마다 필요한 chunk를 CPU cold pool에서 GPU로 fetch | 예측 기반 sparse routing. 이 논문의 주인공 |
| Recency Only | 마지막 8K와 decoding local window만 유지하고 과거 CSA는 버림 | "최근 문맥만 보면 되는가"를 보는 sliding-window control |
| Random 10% | 과거 CSA chunk 중 10%를 무작위로 유지 | 같은 sparse budget에서 예측 없이 뽑으면 어떤가를 보는 control |

여기서 HCA와 CSA의 관계를 다시 잡아두면 결과 해석이 쉬워진다. HCA는 전체 문맥을 매우 강하게 압축해 전역적인 의미, 주제, 흐름을 유지한다. CSA는 더 낮은 압축 또는 fine-grained한 접근을 담당해 세부 사실, 특정 위치의 증거, 긴 범위의 정확한 retrieval을 보완한다. FlashMemory는 HCA를 없애지 않는다. 전체 문맥의 얇은 global memory는 계속 들고 가되, 비싼 CSA history만 "필요할 때만" GPU에 올린다. 그래서 FM-DS-V4의 절감은 전체 attention 메커니즘 삭제가 아니라, 가장 비싼 fine-grained memory layer의 상주 범위를 줄이는 쪽이다.

## 결과 표는 세 가지 질문으로 읽으면 된다

Table 1은 길지만, 실무적으로는 세 질문만 보면 된다.

첫째, 정확도가 full-cache baseline을 따라가는가. 둘째, 메모리 절감이 짧은 구간뿐 아니라 500K 근처에서도 유지되는가. 셋째, Recency Only나 Random 10% 같은 단순 휴리스틱과 충분히 벌어지는가.

아래 표는 원문 Table 1을 비교 포인트 중심으로 압축한 것이다. 메모리는 sglang deployment log에서 측정한 GPU KV cache overhead이며, 괄호 안의 비율은 같은 row의 DS-V4-Flash 대비 FM-DS-V4의 물리 footprint다.

| 평가 설정 | DS-V4-Flash | FM-DS-V4 | FM 메모리 비율 | 단순 control의 신호 |
| --- | ---: | ---: | ---: | --- |
| LongBench-v2-S, 46K | 68.9 / 0.17GB | 70.2 / 0.04GB | 23.5% | Recency 50.0, Random 53.3 |
| LongBench-v2-M, 179K | 67.6 / 0.65GB | 68.9 / 0.08GB | 12.3% | Recency 54.4, Random 48.9 |
| LongBench-v2-L, 493K | 68.1 / 1.80GB | 70.0 / 0.18GB | 10.0% | Recency 54.3, Random 46.9 |
| LongMemEval-S, 125K | 80.6 / 0.46GB | 82.0 / 0.06GB | 13.0% | Recency 19.2, Random 20.1 |
| LongMemEval-M, 500K | 39.3 / 1.82GB | 40.2 / 0.17GB | 9.3% | Recency 23.1, Random 25.7 |
| RULER 64K | 94.7 / 0.23GB | 95.0 / 0.04GB | 17.4% | Recency 36.6, Random 52.8 |
| RULER 128K | 94.3 / 0.47GB | 93.2 / 0.06GB | 12.8% | Recency 21.6, Random 32.3 |
| RULER 256K | 90.5 / 0.94GB | 88.2 / 0.09GB | 9.6% | Recency 20.6, Random 41.2 |
| RULER 512K | 88.3 / 1.87GB | 89.6 / 0.18GB | 9.6% | Recency 18.8, Random 27.2 |
| 평균 | 76.9 / 0.93GB | 77.5 / 0.10GB | 13.5% | Recency 33.3, Random 38.7 |

정확도만 보면 작은 차이처럼 보일 수 있다. 평균 $+0.6$%p는 모델 성능표에서 큰 수치가 아니다. 하지만 이 수치가 메모리 $86.5\%$ 절감과 동시에 나온다는 점이 본문 결과의 핵심이다. 특히 Table 1의 평균 메모리 $0.10\text{GB}$는 반올림된 값이라 $0.10 / 0.93$만 계산하면 $13.5\%$와 정확히 맞지 않는다. 논문이 강조하는 $13.5\%$는 각 설정의 baseline 대비 physical footprint 관점에서 평균화한 값으로 읽는 편이 자연스럽다.

## LongBench-v2에서는 "적게 보는 쪽"이 더 맞았다

LongBench-v2는 세 구간으로 나뉜다. S는 약 46K, M은 약 179K, L은 약 493K다. FM-DS-V4는 모든 구간에서 DS-V4-Flash를 넘는다. S에서는 $68.9 \to 70.2$, M에서는 $67.6 \to 68.9$, L에서는 $68.1 \to 70.0$이다. 가장 긴 L 구간에서 $+1.9$%p가 나왔다는 점이 특히 눈에 띈다.

메모리 쪽은 더 선명하다. LongBench-v2-L에서 DS-V4-Flash는 $1.80\text{GB}$의 KV overhead를 쓰지만, FM-DS-V4는 $0.18\text{GB}$만 쓴다. baseline의 정확히 10% 수준이다. 논문은 이 구간을 "less is more"가 가장 잘 드러난 사례로 본다. 전체 history를 모두 attention 후보로 남겨두면 정보가 많아지는 것처럼 보이지만, 실제로는 수천 개의 관련 낮은 chunk가 dot-product 후보에 끼어들면서 오히려 factual confusion을 만든다는 해석이다.

이 지점에서 "denoiser"라는 표현이 나온다. FM-DS-V4의 Memory Indexer는 단순 압축기가 아니다. 정보량을 줄여서 손실을 감수하는 것이 아니라, attention 후보군에서 불필요한 과거 chunk를 제거해 core attention이 더 깨끗한 후보 위에서 작동하게 한다는 주장이다. LongBench-v2-L에서 정확도가 오른 것은 이 해석에 힘을 싣는다. 긴 문맥일수록 모든 과거가 도움이 되는 것이 아니라, 찾을 수 있는 적은 과거만 도움이 된다.

하지만 Recency Only도 LongBench-v2에서는 50점대 중반을 유지한다. 이를 "최근 문맥만으로도 충분하다"로 읽으면 과하다. DeepSeek-V4의 HCA가 전체 문맥을 $128{:}1$로 압축해 들고 있고, local 8K CSA도 유지되기 때문이다. LongBench-v2 일부 문항이 coarse semantic synthesis나 최근 문맥 기반 추론으로 해결될 수 있다면 Recency Only가 완전히 0점으로 떨어지지는 않는다. 그래도 DS-V4-Flash나 FM-DS-V4와는 13~23점 차이가 난다. fine-grained history access가 필요 없다는 뜻은 아니다.

## LongMemEval은 휴리스틱의 붕괴를 보여준다

LongMemEval은 FlashMemory의 필요성을 더 강하게 보여준다. S 125K에서 DS-V4-Flash는 80.6, FM-DS-V4는 82.0이다. M 500K에서는 39.3에서 40.2로 올라간다. 정확도 상승폭 자체는 각각 $+1.4$%p, $+0.9$%p로 작지만, 메모리는 $0.46\text{GB} \to 0.06\text{GB}$, $1.82\text{GB} \to 0.17\text{GB}$로 줄어든다.

반면 Recency Only와 Random 10%는 이 benchmark에서 거의 붕괴한다. LongMemEval-S에서 Recency Only는 19.2, Random 10%는 20.1이다. LongMemEval-M에서도 각각 23.1, 25.7에 그친다. 이는 "마지막 8K만 보면 된다" 또는 "전역 history의 10%를 아무렇게나 잡아도 된다"는 가정이 장기 기억 평가에서는 통하지 않는다는 뜻이다.

여기서 FM-DS-V4의 위치가 분명해진다. 이 모델은 full cache와 같은 양의 세부 memory를 쓰지 않는다. 그러나 어떤 세부 memory가 필요한지는 배웠다. Recency Only는 필요한 과거를 버리고, Random 10%는 필요한 과거를 맞힐 확률에 기대지만, FM-DS-V4는 현재 query hidden state를 기준으로 앞으로 $\tau$ 스텝에서 필요할 가능성이 높은 chunk를 예측한다. 실험 결과는 이 예측이 완벽하지는 않더라도, 장기 기억 과제에서 단순 sparse budget과는 질적으로 다르다는 점을 보여준다.

500K 구간의 수치도 중요하다. LongMemEval-M에서 FM-DS-V4는 baseline 대비 약 $9.3\%$의 KV overhead만 쓴다. 논문이 말하는 "500K scale에서 90% reduction"은 이 계열의 결과에서 나온다. 긴 컨텍스트 운영에서 비용을 결정하는 것은 평균 64K가 아니라 tail request다. 500K 요청에서 memory overhead가 10분의 1 수준으로 내려간다면, 같은 GPU pool에서 허용 가능한 concurrent session 수나 batch 정책이 달라진다.

## RULER는 평균 이상의 균형을 묻는다

RULER 결과는 조금 더 복합적이다. 64K에서는 FM-DS-V4가 $94.7 \to 95.0$으로 소폭 앞선다. 512K에서도 $88.3 \to 89.6$으로 올라간다. 반면 128K와 256K에서는 각각 $94.3 \to 93.2$, $90.5 \to 88.2$로 낮아진다. 즉, 모든 row에서 정확도가 오른 것은 아니다.

그럼에도 논문이 RULER를 긍정적으로 해석하는 이유는 메모리 절감 폭이다. 128K에서는 $0.47\text{GB} \to 0.06\text{GB}$, 256K에서는 $0.94\text{GB} \to 0.09\text{GB}$다. 정확도 손실은 $-1.1$%p, $-2.3$%p지만 메모리는 약 87~90% 줄었다. 512K에서는 정확도까지 $+1.3$%p가 되면서 $1.87\text{GB} \to 0.18\text{GB}$로 줄어든다.

이 결과는 FM-DS-V4를 "무조건 baseline보다 정확한 모델"이 아니라 "메모리-정확도 Pareto frontier를 크게 이동시킨 모델"로 봐야 함을 말한다. 운영 관점에서는 이 차이가 더 현실적이다. 긴 context serving에서 full cache baseline은 정확도 상한에 가깝지만, 비용 상한이기도 하다. FM-DS-V4는 일부 설정에서 소폭 손실을 보더라도 평균으로는 baseline을 넘고, 동시에 메모리 사용량을 한 자리수~10%대까지 낮춘다.

RULER의 Recency Only와 Random 10% 결과는 LongMemEval과 비슷한 메시지를 준다. Recency Only는 64K에서도 36.6이고, 512K에서는 18.8까지 떨어진다. Random 10%는 64K에서 52.8로 상대적으로 낫지만, 128K 32.3, 512K 27.2로 baseline과 거리가 멀다. sparse attention의 문제는 단지 "얼마나 적게 보느냐"가 아니라 "무엇을 남기느냐"라는 점이 다시 확인된다.

## 왜 HCA가 있는데도 CSA routing이 필요한가

Section 3.2의 마지막 해석은 HCA와 CSA의 역할 분담으로 이어진다. Recency Only와 Random 10%가 일부 dataset에서 완전히 바닥을 치지 않는 이유는 HCA가 있기 때문이다. HCA는 전체 문맥을 강하게 압축하므로, "문서 전체가 어떤 주제인가", "대략 어느 흐름인가", "요약 수준에서 어떤 정보가 있었나" 같은 coarse signal을 제공한다.

하지만 HCA만으로는 세부 사실 검색을 안정적으로 처리하기 어렵다. 특정 entity의 긴 범위 참조, 오래전 문장에 있는 값, 여러 구간을 연결하는 근거처럼 fine-grained memory가 필요한 순간에는 CSA chunk가 필요하다. DS-V4-Flash는 이 CSA history를 모두 GPU에 둔다. 그래서 정확도는 강하지만 memory wall에 걸린다.

FM-DS-V4는 이 둘 사이를 나눈다. HCA는 전역 memory의 바닥으로 유지한다. CSA는 전체를 상주시켜 놓지 않고, Memory Indexer가 예측한 query-critical subset만 GPU로 올린다. 이 구조에서는 HCA가 coarse recall의 안전망을 제공하고, CSA가 필요한 곳에서만 fine-grained precision을 보강한다. 그래서 Recency Only처럼 세부 memory를 완전히 포기하지도 않고, DS-V4-Flash처럼 모든 세부 memory를 비싼 GPU HBM에 붙잡아 두지도 않는다.

이 관계를 이해하면 "FM-DS-V4가 평균 정확도를 올렸다"는 결과도 덜 신비롭다. full cache가 항상 최선의 후보 집합은 아니다. attention score 계산에 들어오는 후보가 너무 많으면, 낮은 관련도의 chunk가 점수 공간을 흐릴 수 있다. 특히 ultra-long context에서는 irrelevant history의 절대량이 커진다. Memory Indexer가 high-recall로 필요한 chunk를 남기면서 low-value chunk를 빼면, 이는 compression인 동시에 denoising이 된다.

물론 이 해석은 Table 1 범위 안에서만 유효하다. 다음 편에서 볼 한계처럼 모든 long-context workload가 sparse retrieval에 우호적인 것은 아니다. dense global memory가 필요한 과제에서는 10%나 25%의 golden chunk만으로도 충분하지 않을 수 있다. 하지만 Section 3.1~3.2가 보여주는 주된 결론은 분명하다. 표준 long-context benchmark 다수에서는 full KV cache의 대부분이 매 decoding step마다 GPU에 상주할 필요가 없었다.

## 실전적으로 남는 숫자

운영자가 이 결과에서 가져갈 숫자는 네 개다.

- 평균 정확도: DS-V4-Flash $76.9\%$, FM-DS-V4 $77.5\%$.
- 평균 KV cache overhead: DS-V4-Flash $0.93\text{GB}$, FM-DS-V4 $0.10\text{GB}$.
- 평균 footprint ratio: baseline의 $13.5\%$, 즉 $86.5\%$ reduction.
- 500K scale: LongBench-v2-L 493K와 LongMemEval-M 500K, RULER 512K에서 대략 90% 수준의 memory reduction.

이 숫자가 의미하는 바는 "긴 컨텍스트 모델을 더 작게 만들었다"가 아니다. backbone은 그대로 두고, decoding 중 GPU에 반드시 상주해야 하는 KV cache의 정의를 바꿨다. 지금까지는 긴 prompt를 받으면 전체 과거 KV가 GPU memory budget의 일부로 고정되었다. FlashMemory는 이를 active working set 문제로 바꾼다. 과거 전체는 CPU cold pool에 둘 수 있고, GPU HBM에는 다음 짧은 구간에 필요한 chunk만 올라온다.

그래서 memory wall을 "완전히 깼다"고 말하기에는 아직 이르다. 평균 $13.5\%$라는 숫자는 강하지만, context-independent query에서 false-positive retrieval이 쌓이는 문제나 MRCR 같은 dense memory failure는 남아 있다. 다만 Section 3.1~3.2의 범위에서 보면 wall의 가장 두꺼운 부분, 즉 "긴 context이면 full KV cache를 GPU에 선형으로 들고 있어야 한다"는 전제는 상당히 흔들렸다.

다음 편: [한계가 말해주는 실전 적용 조건](05-limitations-and-takeaways.md)

## 출처

- https://arxiv.org/abs/2606.09079
