---
title: Dense reward 가 만드는 50~100배 절감과 continual learning 의 약속
date: 2026-05-13
author: TrainToGPB
tags: [사후학습, 증류, continual-learning, compute-efficiency]
source: https://thinkingmachines.ai/blog/on-policy-distillation/
summary: 같은 teacher 를 RL 로 학습한 결과를 distillation 으로 옮길 때 7~10배 빠르게 수렴하고, 누적 50~100배 비용 절감이 일어난다. 단일 prompt 만 반복해도 teacher 수준에 근접하고, SFT 가 KL=0 데이터에서도 무너지는 continual learning 한계와 대비된다.
format: details
part: 5
---

# Dense reward 가 만드는 50~100배 절감과 continual learning 의 약속

> 원본: [thinkingmachines.ai/blog/on-policy-distillation](https://thinkingmachines.ai/blog/on-policy-distillation/)

지금까지 네 편에 걸쳐 on-policy distillation 이 어떤 자리에 들어가는지, 어떤 알고리즘으로 굴러가는지, 추론 능력과 personalization 에서 각각 어떤 수치가 나오는지를 봤다. 마지막 편은 이 방법이 *왜* 그렇게 효율적인지, 그리고 그 효율이 무엇을 새롭게 가능하게 만드는지를 정리한다. 핵심은 두 가지다. 첫째, 토큰 단위 supervision 의 정보량 자체가 RL 의 episode 단위 reward 와 자릿수 단위로 다르다. 둘째, 이 dense signal 이 단순한 비용 절감을 넘어 continual learning 의 도구로 확장된다.

## Dense supervision 의 정보량과 compute 효율

가장 먼저 짚어야 할 것은 학습 신호의 *정보량* 이다. RL 은 episode 가 끝난 시점에 보상 하나를 받는다. 한 episode 가 전달하는 정보는 $O(1)$ bit 다. Distillation 은 토큰마다 teacher 의 분포와 student 의 분포를 비교한다. 토큰 수를 $N$ 이라 하면 한 episode 가 전달하는 정보는 $O(N)$ bit 다. 토큰 단위로 보면 정보 효율이 자릿수가 다르다는 뜻이고, 이게 학습 속도와 그대로 연결된다.

원문은 이 차이를 직접 비교 가능한 실험으로 잡았다. Qwen3-8B-Base 에서 시작해 DeepMath 로 RL 학습 (LoRA rank 128) 을 돌려 teacher 모델을 만든다. 같은 base 모델을 student 로 두고, 이 teacher 로 on-policy distillation 을 돌린다. RL 과 distillation 이 같은 출발점에서 같은 도착점을 향해 가는 그림이다.

결과는 단순하다. Distillation 이 teacher 수준 성능에 약 10 step 만에 도달했고, 같은 student 가 같은 teacher 수준에 RL 로 도달하는 데에는 70 step 가량이 필요했다. 7~10배 차이다. 학습 후 student 의 reverse KL 은 teacher 대비 거의 0 에 가까웠고, AIME 점수도 teacher 의 수준을 회복했다. Episode 당 bit 가 많으니 gradient noise 가 작고, 같은 진척을 얻는 데 필요한 sample 수가 줄어든 결과다.

여기에 누적 절감이 더 있다. RL 은 evaluation 시 쓸 context 길이 그대로 학습해야 한다. Policy 가 context limit 안에서 답을 끝내는 법을 학습해야 하고, format penalty 도 그 길이 안에서 작동해야 한다. Distillation 은 짧은 context 로 학습해도 큰 문제가 없다. Reward 가 trajectory 가 종료되었는지 여부에 sharp cutoff 를 두지 않고, 토큰별 KL 이 짧은 prefix 만으로도 의미 있는 신호를 만들기 때문이다. Context 가 짧을수록 step 당 비용이 줄어드므로, step 수 절감 위에 step 당 비용 절감이 누적된다.

또 하나의 누적 요인이 SFT initialization 강도다. Teacher 의 분포가 student 의 support 안에 들어와 있을 때, on-policy distillation 은 작은 batch 로도 안정적으로 진행된다. Episode 당 bit 가 많으니 같은 batch 가 RL 보다 많은 정보를 담는다. 이 효과까지 합치면 누적 비용 절감은 단순한 step 수 비율을 훌쩍 넘어 50~100배 수준에 이른다는 것이 원문의 주장이다.

이 그림은 dense supervision 의 일반적 가치를 시사한다. Lightman 등이 추론에서 outcome reward 보다 process reward 가 훨씬 효율적임을 보였던 것과 같은 방향이다. 결과 한 비트 대신 과정의 매 step 에 신호를 깐다는 발상은, distillation 의 토큰별 KL 에서 가장 단순하고 강한 형태로 구현된다.

## 같은 prompt 의 재사용: data efficiency

실무에서 prompt 자체가 비싸다. 라벨링은 둘째 치고, 좋은 prompt 를 모으는 것부터가 작업이다. 그러니 같은 prompt 를 얼마나 재사용할 수 있느냐는 곧 데이터 비용과 직결된다.

RL 은 이 축에서 약점을 드러낸다. 같은 prompt 위에서 epoch 를 늘리면 policy 가 그 prompt 에 대한 단일 답을 memorize 하기 시작한다. 모델이 클수록 빨라진다. "RL for Reasoning with One Training Example" 같은 결과가 있긴 하지만 setting 이 좁고, 일반적으로 같은 prompt 의 반복 사용은 RL 학습을 무너뜨리는 쪽으로 작용한다.

Distillation 은 같은 prompt 를 다르게 다룬다. Teacher 의 *분포* 를 근사하는 것이 목적이므로 student 는 어떤 단일 답을 외우는 게 아니다. 같은 prompt 라도 teacher 가 만들 수 있는 다양한 trajectory 의 평균적인 모양을 좇는다. 그래서 같은 prompt 를 여러 번 학습해도 memorization 으로 빠지지 않는다.

극단적인 검증이 단일 prompt 실험이다. 원문은 Qwen3-8B-Base 에 단 하나의 수학 prompt 만 던졌다. 그 prompt 는 $\lim_{x \to \infty} \sqrt{x}\,\bigl(\sqrt[3]{x+1} - \sqrt[3]{x-1}\bigr)$ 의 극한을 구하라는 문제다. 20 step, batch 256 으로 학습했으니 graded sequence 는 총 5120 개다. 한 prompt 만으로 만든 5120 개 trajectory 라는, RL 이라면 거의 확실히 무너졌을 setting 이다.

결과는 의외로 teacher 수준에 근접했다. Compute 효율 자체는 다양한 prompt 를 쓸 때보다 떨어진다. 같은 prompt 가 반복되니 새로운 정보가 들어오는 비율이 낮아지는 것은 당연하다. 하지만 학습이 무너지지 않고, 분포 근사라는 본래 목적이 굴러간다는 것이 핵심이다. 데이터가 부족한 도메인에 적용할 때 의미가 큰 결과다.

## RL = semantic strategy 공간의 search

On-policy distillation 이 RL 의 학습 결과를 훨씬 적은 step 으로 재현할 수 있다는 사실을 어떻게 해석해야 할까. 원문은 이 부분을 짧지만 명확히 짚는다. RL 의 본질은 gradient step 그 자체가 아니라 *search* 라는 관점이다.

RL 은 한 step 의 gradient update 에 compute 를 거의 안 쓴다. Compute 의 대부분은 rollout 과 credit assignment, 즉 어떤 행동이 좋은 결과로 이어졌는지를 sample 로 탐색하는 데 쓰인다. Sutton 의 "The Bitter Lesson" 이 말한 search 와 learning 의 결합이 바로 이 그림이다. Learning 은 본 것을 새겨넣는 일이고, search 는 무엇을 새겨넣을지를 찾아내는 일이다.

같은 관점에서 pre-training 과 RL 을 비교하면 둘이 다른 공간에서 다른 양의 search 를 한다. Pre-training 은 parameter space 를 탐색한다. 정보량이 거대해 그 결과를 다른 모델로 distill 하기가 어렵다. Lottery Ticket Hypothesis 가 말하듯, 좋은 sub-network 가 찾아질 때까지 거대 parameter 공간을 휘젓는 과정이다.

RL 은 semantic strategy 공간을 탐색한다. 매 step 의 변화가 작고, 좋은 전략이 발견되면 그것이 학습의 종점이 된다. Distillation 이 빠르게 따라잡을 수 있는 이유가 여기에 있다. RL 이 거쳐 간 intermediate strategy 를 모두 답습할 필요가 없다. 최종 strategy 만 모방하면 된다. 비유하자면, 과학적 발견은 자연어로 가르치기 쉽지만 운동 같은 muscle memory 는 직접 반복 연습이 필요한 것과 비슷하다. RL 이 찾아낸 것은 자연어로 옮길 수 있는 종류의 발견에 가깝고, distillation 은 그 발견을 글로 받아 적는 작업이다.

이 해석은 RL 인프라를 가진 곳과 그렇지 않은 곳의 분업도 시사한다. RL 은 frontier 모델을 학습시키는 쪽에서 한 번 돌리면 되고, 그 결과를 teacher 로 삼아 distill 하는 쪽은 RL 없이도 그 strategy 를 받아갈 수 있다. Search 와 learning 이 조직적으로도 분리될 여지가 생긴다.

## Continual learning 의 도구로서

마지막으로 가장 흥미로운 함의는 continual learning 쪽에 있다. 4편에서 본 personalization 사례는 사실 continual learning 의 한 단면이다. 이미 후속학습된 모델에 새 능력을 더 얹으면서 기존 능력을 어떻게 보존할 것인가, 라는 일반적 문제로 확장된다.

선행 연구가 부분적인 답을 준다. Shenfeld 등의 "RL's Razor" (2025) 는 on-policy learning 이 off-policy learning 보다 덜 잊는다는 것을 보였다. 그러나 RL 만으로는 부족하다. RL 은 행동을 형성할 뿐 새로운 knowledge 를 모델에 주입하지 못한다. Continual learning 이 학습과 보존을 동시에 요구한다면 RL 한 축으로는 안 된다.

그 반대편에서 SFT (off-policy distillation 포함) 가 새로운 지식을 넣는 역할을 맡지만, SFT 는 continual learning 의 scaffold 역할에 더 깊은 결함을 보인다. 원문이 짚는 한 가지 실험이 그 핵심이다. KL 이 정확히 0 인 데이터셋, 즉 모델 *자신* 의 sample 로 SFT 를 돌려도 IF-eval 같은 능력이 무너진다. 기대값으로는 그 데이터셋이 모델 분포와 정확히 같지만, 실제 학습은 finite batch 단위로 진행된다. Batch 마다 분포가 약간씩 어긋나고, 어긋난 분포에 대한 SFT gradient 는 0 이 아닌 update 를 만든다. 그렇게 model policy 가 원래 상태에서 조금씩 drift 하면, 시간이 지난 시점에서 self-sample 학습은 이미 off-policy training 이 되어 있다. 자기 자신을 모방하려 했는데 결과적으로 남을 모방하게 되는 구조다.

On-policy distillation 은 이 함정을 피한다. Teacher 가 학습 도중 변하지 않으므로, student 가 어떻게 drift 하든 학습 신호는 항상 같은 desirable behavior 쪽을 가리킨다. Self-distillation setting, 즉 student 의 이전 checkpoint 를 teacher 로 쓰는 setting 에서도 regress 가 보이지 않는다는 것이 원문의 관찰이다. Teacher 가 fixed point 역할을 한다.

여기서 phase-alternating continual learning 의 청사진이 자연스럽게 나온다. SFT 로 새로운 지식이나 능력을 한 번 주입한 뒤, on-policy distillation 으로 행동을 회복하고 desirable behavior 로 student 를 다시 끌어온다. 두 phase 를 교차하면 학습과 보존을 동시에 굴릴 수 있다. SFT 의 dense 한 정보 주입과, on-policy 의 분포 정렬이 각자의 역할에 충실하게 분리된다.

## 결론

On-policy distillation 의 정체성은 단순하게 정리된다. SFT 의 dense 한 토큰별 signal 과 RL 의 on-policy 분포 일치를 한 알고리즘에서 결합한 것이다. 둘 중 어느 한쪽도 단독으로는 만들지 못했던 자리다. 그 결과 frontier 급 사후학습 성능을 frontier RL run 대비 자릿수 단위로 작은 compute 로 얻는다.

후속 방향은 자연스럽게 따라온다. Teacher supervision 을 logit 분포 전체나 top-k 로 더 풍부하게 가져가는 것, sequence-level environment reward 와 결합해 두 신호의 장점을 합치는 것, prompt 재사용을 극단으로 밀어 data efficiency 한계를 보는 것, 그리고 SFT 와 on-policy distillation 의 phase-alternating 을 본격적으로 continual learning 시스템으로 만드는 것이다.

## 우리에게의 시사점

사내 LLM 사후학습 환경에서 RL 인프라가 충분치 않고 SFT 만 안정적으로 굴리고 있는 팀이라면, midtrain SFT 직후에 모델의 *자신의 earlier checkpoint* 를 teacher 로 한 on-policy distillation phase 를 한 번 끼우는 시도가 비용 대비 매력적이다. 같은 데이터의 KL=0 self-SFT 가 IF-eval 을 갉아먹는 문제를, 같은 비용 수준에서 회복할 가능성이 있다.

단일 prompt 재사용 가능성은 데이터가 부족한 도메인 적용에 매력적인 카드다. 다만 "강한 SFT 초기화" 라는 전제는 무시할 수 없다. Teacher 의 분포가 student 의 support 안에 있어야 한다는 조건은 실무 디자인에서 mid-train 단계를 여전히 요구한다. On-policy distillation 만으로 충분한 게 아니라, 그 위에 올라타야 할 토대가 따로 있다는 점을 잊지 말아야 한다.

## 출처

- https://thinkingmachines.ai/blog/on-policy-distillation/
