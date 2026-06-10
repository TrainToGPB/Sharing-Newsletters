---
title: 왜 긴 컨텍스트 서빙은 KV cache에서 막히나
date: 2026-06-10
author: 김세형/LLM서비스개발팀/NE
tags: [long-context, kv-cache, inference, sparse-attention, flashmemory]
source: https://arxiv.org/abs/2606.09079
summary: FlashMemory-DeepSeek-V4의 문제의식은 긴 컨텍스트 모델의 FLOPs보다 GPU에 상주하는 KV cache가 병목이라는 데서 출발한다.
format: details
part: 1
---

# 왜 긴 컨텍스트 서빙은 KV cache에서 막히나

> 원본: [arxiv.org/abs/2606.09079](https://arxiv.org/abs/2606.09079)

FlashMemory-DeepSeek-V4 기술 보고서의 출발점은 긴 컨텍스트 모델을 더 빠르게 계산하는 문제가 아니다. 이미 많은 모델과 커널은 디코딩 한 스텝에서 필요한 attention 연산량을 줄이는 방향으로 발전해 왔다. 그런데 실제 서빙에서는 연산량을 줄여도 GPU 메모리에 남아 있는 KV cache가 계속 커진다. 이 보고서는 바로 그 지점을 문제의 중심에 둔다. 긴 컨텍스트에서 비싼 것은 매번 모든 토큰을 계산하는 FLOPs만이 아니라, 언젠가 필요할지도 모른다는 이유로 모든 과거의 $K$, $V$를 GPU에 붙잡아 두는 방식이다.

논문 제목의 "FlashMemory"는 이 병목을 메모리 시스템 관점에서 다시 보겠다는 선언에 가깝다. 모델이 긴 문서를 읽을 수 있다는 것과, 그 문서를 여러 요청에 대해 안정적으로 서빙할 수 있다는 것은 다르다. 전자는 벤치마크 성능의 문제이고, 후자는 GPU 한 장 또는 한 노드에 얼마나 많은 요청을 동시에 올릴 수 있는가의 문제다. FlashMemory-DeepSeek-V4는 후자를 전면에 놓고, "긴 컨텍스트 능력은 유지하되 물리적으로 GPU에 상주하는 KV cache는 대부분 비워둘 수 있는가"를 묻는다.

## 제목과 초록이 잡는 문제

초록은 기존 LLM 서빙의 기본 가정을 뒤집는다. 일반적인 자기회귀 디코딩에서는 과거 토큰의 KV cache를 GPU에 계속 둔다. 현재 토큰이 과거의 어느 위치를 볼지 알 수 없기 때문에, 시스템은 보수적으로 전체 기록을 활성 메모리에 보관한다. 이 방식은 짧은 컨텍스트에서는 자연스럽지만, 64K, 128K, 500K 토큰으로 넘어가면 비용 구조가 완전히 달라진다.

보고서가 강조하는 병목은 다음처럼 정리할 수 있다.

| 구분 | 기존 접근 | 긴 컨텍스트에서의 문제 |
| --- | --- | --- |
| 계산량 | sparse attention, compressed attention으로 줄임 | 한 스텝 FLOPs는 낮아질 수 있음 |
| KV cache | 전체 또는 큰 부분을 GPU에 유지 | 시퀀스 길이에 따라 메모리가 선형 증가 |
| 품질 | 전역 문맥 접근을 보장 | 실제로는 대부분의 스텝이 전역 문맥을 쓰지 않음 |
| 서빙 | 요청별 cache를 보존 | 동시성, 배치, prefix reuse를 압박 |

여기서 핵심은 sparse attention이 실패했다는 뜻이 아니다. sparse attention은 불필요한 attention 연산을 줄이는 데 성공했다. 다만 "계산하지 않는다"와 "GPU에 올려두지 않는다"는 다른 문제다. 어떤 chunk를 보지 않더라도, 그 chunk의 $K$, $V$가 여전히 GPU 메모리를 차지하면 서빙 비용은 크게 줄지 않는다. FlashMemory가 겨냥하는 것은 이 남아 있는 물리적 cache footprint다.

초록의 수치도 이 관점을 따른다. 저자들은 FM-DS-V4가 여러 긴 컨텍스트 벤치마크에서 성능을 유지하거나 약간 올리면서, 평균 물리적 KV cache footprint를 full-context baseline의 13.5% 수준으로 줄였다고 보고한다. 500K 규모에서는 물리적 KV cache overhead를 90% 이상 낮춘다고 설명한다. 이 편에서는 이 수치 자체의 검증보다, 왜 이런 목표가 필요해졌는지를 먼저 정리한다.

## Project Status가 중요한 이유

논문 첫 페이지에는 이례적으로 Project Status가 붙어 있다. 프로젝트 리드가 Tencent를 떠났고, 조직 개편으로 프로젝트가 중단되었다는 설명이다. 동시에 보고서는 예비 성과와 검증된 체크포인트를 문서화하기 위해 공개되었다고 밝힌다.

이 상태 표기는 읽는 방식에 영향을 준다. FlashMemory-DeepSeek-V4는 완성된 제품 발표라기보다, 특정 방향의 시스템 설계가 실제 모델과 벤치마크에서 어디까지 가능했는지 보여주는 기술 보고서다. 따라서 세부 수치 하나하나를 최종 레시피로 받아들이기보다는, 긴 컨텍스트 서빙 병목을 어디에 놓고 어떤 trade-off를 설계했는지 보는 편이 더 유용하다.

특히 이 보고서는 "모델 구조를 조금 바꾸면 된다"는 수준의 제안이 아니다. GPU 메모리 상주 집합, CPU cold pool, compressed entry, indexer training, decoding interval $\tau$ 같은 서빙 시스템의 요소를 같이 다룬다. Project Status는 이 결과가 아직 이어질 여지가 있는 연구 산출물임을 알려주지만, 문제 정의 자체의 가치는 오히려 분명하게 만든다. 조직 사정으로 멈춘 프로젝트라도, 긴 컨텍스트 서빙에서 KV cache가 병목이라는 관찰은 별도로 검토할 가치가 있다.

## full KV cache의 보수적인 기본값

LLM 디코딩에서 새 토큰을 만들 때 모델은 이전 토큰들의 key와 value를 참조한다. 매번 처음부터 모든 $K$, $V$를 다시 계산하지 않기 위해, 서빙 시스템은 각 레이어의 KV cache를 누적한다. 짧은 대화에서는 이 방식이 거의 당연하다. 계산을 저장하고 재사용하므로 latency가 줄고, attention이 과거 전체를 볼 수 있으므로 품질도 보장된다.

문제는 cache 크기가 컨텍스트 길이와 함께 선형으로 늘어난다는 점이다. 시퀀스 길이를 $L$이라고 하면, 요청 하나의 KV cache는 대략 $L$에 비례한다. 레이어 수, head 수, head dimension, dtype이 곱해지면 실제 GPU 메모리 압박은 빠르게 커진다. 모델 가중치는 같은 GPU에서 여러 요청이 공유하지만, KV cache는 요청마다 별도로 생긴다. 그래서 긴 컨텍스트 서빙에서는 batch size를 키우려는 순간 cache가 먼저 벽이 된다.

full KV cache는 품질 측면에서 가장 보수적인 선택이다. 현재 토큰이 과거의 어디를 볼지 모르니, 모든 과거를 남겨둔다. 하지만 이 선택에는 숨은 가정이 있다. "모든 과거가 언제든 필요할 수 있다"는 가정이다. FlashMemory 보고서는 실제 서빙 로그를 보면 이 가정이 대부분의 요청에서 지나치게 비싸다고 주장한다. 모델이 긴 컨텍스트를 입력받았다고 해서, 매 decoding step이 긴 문맥 전체를 같은 강도로 요구하지는 않는다.

![Introduction excerpt from FlashMemory-DeepSeek-V4](../assets/page-2.png)
*Introduction에서는 긴 컨텍스트 서빙의 병목을 FLOPs가 아니라 GPU에 상주하는 KV cache의 선형 증가로 놓고, 64K 초과 요청 중 상당수가 최근 8K만으로 처리된다는 관찰을 제시한다.*

## sparse attention이 줄인 것과 남긴 것

최근 긴 컨텍스트 모델은 attention의 계산량을 줄이기 위해 다양한 희소화 구조를 사용한다. DeepSeek-V4 계열의 HCA, CSA 같은 구조도 이런 맥락에 있다. 고압축 attention layer는 전역 정보를 낮은 해상도로 유지하고, 일부 layer나 일부 chunk는 더 세밀하게 본다. 이 방식은 full attention을 모든 layer와 모든 토큰에 적용하는 것보다 훨씬 낫다.

하지만 sparse attention의 목표가 항상 "GPU cache를 제거한다"는 뜻은 아니다. 많은 구조는 attention score 계산에서 일부 token 또는 chunk만 선택하더라도, 선택 후보가 되는 KV entry를 메모리 어딘가에 보관해야 한다. 특히 fine-grained factual recall을 유지하려면 완전히 압축된 표현만으로는 부족하고, 낮은 압축률 또는 full에 가까운 attention 경로가 남는다. 그러면 메모리 증가율은 완화되지만, 선형 증가 자체는 사라지지 않는다.

보고서의 문제의식은 이 차이를 날카롭게 구분한다.

- sparse attention은 "이번 step에서 무엇을 계산할 것인가"를 줄인다.
- KV offloading은 "무엇을 GPU에 계속 올려둘 것인가"를 바꾼다.
- LSA는 "다음 구간에서 필요할 fine-grained chunk를 미리 예측할 수 있는가"를 묻는다.

이 셋은 같은 방향처럼 보이지만 운영상 병목이 다르다. 연산량이 병목이면 attention kernel 최적화가 우선이다. GPU 메모리 용량이 병목이면 cache 상주 정책이 우선이다. 긴 컨텍스트 서빙에서는 후자가 자주 더 큰 제약이 된다.

## 64K 이후 요청의 대부분은 최근 8K로 풀린다는 관찰

Introduction에서 가장 강한 문장은 실제 inference log 분석이다. 저자들은 64K 토큰을 넘는 사용자 요청 중 90% 이상이 마지막 8K 토큰만으로도 정확히 해결될 수 있었다고 말한다. 이 문장은 조심해서 읽어야 한다. "긴 컨텍스트가 쓸모없다"는 뜻이 아니다. "긴 컨텍스트 요청의 모든 decoding step이 긴 과거 전체를 필요로 하지는 않는다"는 뜻에 가깝다.

실제 사용 패턴을 생각해 보면 자연스럽다. 사용자가 긴 문서를 올린 뒤 마지막 부분에서 간단한 정리나 변환을 요청할 수 있다. 긴 대화가 이어졌지만 최근 질문은 바로 앞 응답에만 의존할 수도 있다. 코드베이스 전체를 넣었더라도 마지막 지시가 특정 파일 일부만 고치라는 내용일 수 있다. 이런 경우 full KV cache를 계속 GPU에 유지하는 것은 정확도보다 불확실성에 대한 보험에 가깝다.

이 관찰이 중요한 이유는 메모리 절감의 상한을 보여주기 때문이다. 대부분의 step이 최근 8K만으로 충분하다면, GPU에 항상 전체 128K나 500K의 fine-grained KV를 둘 필요가 없다. 오래된 chunk는 CPU나 더 싼 메모리 계층으로 내려두고, 필요한 순간에만 다시 가져오는 방향이 가능해진다. 다만 이 전략은 곧바로 다음 문제에 부딪힌다. 나머지 10%에 해당하는 요청, 즉 실제로 멀리 떨어진 문맥을 요구하는 요청을 어떻게 놓치지 않을 것인가.

## sliding window가 답이 되지 않는 이유

가장 단순한 해결책은 sliding window다. 최근 $W$ 토큰만 남기고 이전 cache를 버리면 GPU 메모리는 거의 상수로 고정된다. $W = 8K$라면 앞서 말한 90% 이상의 요청에는 충분할 수도 있다. 운영 관점에서 보면 매우 매력적이다. 구현이 단순하고, 메모리 예측이 쉬우며, latency도 안정적이다.

하지만 sliding window는 실패 모드가 분명하다. 사용자가 초반 문서의 특정 표, 앞부분의 약속, 오래전에 나온 코드 정의를 다시 물으면 window 밖 정보가 필요하다. 그 정보는 압축된 요약으로 대체하기 어려울 수 있다. 특히 긴 컨텍스트 모델의 가치는 "멀리 있는 정보를 필요할 때 정확히 꺼내는 능력"에서 나온다. window 밖을 일괄 삭제하면 긴 컨텍스트 모델을 짧은 컨텍스트 모델처럼 쓰는 셈이 된다.

논문이 말하는 모순은 이 지점에 있다.

| 선택 | 장점 | 치명적 약점 |
| --- | --- | --- |
| full KV cache | 전역 recall을 가장 안전하게 보장 | GPU 메모리가 $L$에 따라 선형 증가 |
| sliding window | 메모리 footprint를 상수에 가깝게 고정 | window 밖 global context 질의에 취약 |
| 기존 sparse attention | FLOPs와 일부 메모리 증가율 완화 | fine-grained KV 상주 부담이 남음 |

즉 문제는 "최근만 보면 되는가, 전체를 보면 되는가"의 이분법이 아니다. 대부분의 순간에는 최근만 봐도 되지만, 특정 순간에는 오래된 chunk를 정확히 다시 불러와야 한다. 긴 컨텍스트 서빙의 어려움은 이 비대칭성에서 나온다.

## Figure 1이 보여주는 목표 지점

Figure 1은 이 문제 정의가 단순한 직관이 아니라 성능-메모리 동시 목표로 이어진다는 점을 보여준다. 보고서는 LongBench-v2와 RULER에서 FM-DS-V4가 DeepSeek-V4-Flash baseline과 비슷하거나 더 높은 정확도를 보였고, 동시에 KV cache overhead를 크게 줄였다고 제시한다. 특히 RULER의 여러 컨텍스트 길이에서 baseline 대비 GPU memory overhead가 낮게 유지되는 그림을 통해, "성능을 포기하고 메모리를 줄였다"가 아니라 "필요한 context만 올려도 성능이 유지된다"는 주장을 뒷받침한다.

이 그림을 읽을 때 중요한 것은 정확도 막대보다 오른쪽 메모리 막대다. 긴 컨텍스트 모델의 논문 그림은 보통 benchmark score를 중심으로 설계되지만, FlashMemory는 하드웨어 효율을 같은 비중으로 둔다. 긴 컨텍스트 모델이 실제 서비스로 갈수록, score 0.5%보다 batch capacity, request concurrency, cache residency가 더 직접적인 비용이 되기 때문이다.

물론 Figure 1만으로 모든 결론이 끝나지는 않는다. benchmark 구성, logging 방식, offload 비용, CPU-GPU transfer latency 같은 세부가 뒤따라야 한다. 이 편에서 중요한 점은 저자들이 성능과 메모리를 같은 그래프에 놓고, long-context serving의 성공 기준을 다시 잡았다는 것이다. 모델이 긴 문맥을 이해할 수 있는지만 보지 않고, 그 능력을 얼마만큼의 physical KV cache로 제공할 수 있는지를 묻는다.

## LSA가 해결하려는 trade-off

Lookahead Sparse Attention, 즉 LSA는 full KV cache와 sliding window 사이의 trade-off를 다르게 푼다. 기본 아이디어는 모든 과거 fine-grained KV를 GPU에 계속 두지 않는 것이다. 대신 압축된 전역 정보는 유지하고, fine-grained CSA chunk는 필요할 때만 GPU로 가져온다. 이때 "필요할 때"를 현재 token의 attention score가 나온 뒤에야 알면 늦다. 그래서 LSA는 일정 decoding interval $\tau$마다 앞으로의 짧은 구간에서 필요한 historical chunk를 미리 예측한다.

여기서 Memory Indexer가 등장한다. Indexer는 현재 hidden state를 보고, 앞으로의 window에서 query-critical할 가능성이 있는 compressed KV entry를 고른다. 선택된 chunk만 GPU에 올라오고, 나머지는 CPU cold pool 같은 비활성 계층에 머문다. 결과적으로 GPU의 active KV footprint는 최근 sliding window와 예측된 global chunk의 합으로 제한된다.

LSA의 설계 의도는 다음 한 문장으로 요약할 수 있다. "대부분의 local generation step에는 sliding window처럼 싸게 동작하되, global context가 필요한 step에서는 full cache처럼 필요한 과거를 정확히 회수하자." 이 목표가 성공하려면 indexer의 recall이 충분히 높아야 하고, 잘못 가져온 chunk가 너무 많아 GPU 메모리를 다시 채우지 않아야 한다. 즉 LSA는 단순한 cache pruning이 아니라, 미래 attention 수요를 예측하는 retrieval 문제로 KV cache 병목을 재정의한다.

다음 편에서는 이 trade-off를 실제 구조로 어떻게 구현하는지 본다. 특히 LSA가 DeepSeek-V4의 기존 CSA/Lightning Indexer 흐름을 어떻게 바꾸고, 왜 $\tau$ step 단위의 lookahead가 cache 상주 정책을 바꾸는 핵심 장치가 되는지 살펴본다.

다음 편: [Lookahead Sparse Attention은 무엇을 바꾸나](02-lookahead-sparse-attention.md)

## 출처

- https://arxiv.org/abs/2606.09079
