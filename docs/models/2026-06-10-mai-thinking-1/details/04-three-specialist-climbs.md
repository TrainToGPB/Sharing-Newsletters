---
title: 세 specialist climb은 어떻게 하나의 모델로 합쳐졌나
date: 2026-06-10
author: 김세형
tags: [mai-thinking-1, agentic-rl, stem-reasoning, safety-training, model-consolidation]
source: https://microsoft.ai/pdf/mai-thinking-1.pdf
summary: STEM, agentic coding/tool use, helpfulness/safety climb은 서로 다른 reward와 환경을 쓰지만, self-distillation과 consolidation SFT/RL로 하나의 MAI-Thinking-1에 통합된다.
format: details
part: 4
---

# 세 specialist climb은 어떻게 하나의 모델로 합쳐졌나

> 원본: [Microsoft AI technical report](https://microsoft.ai/pdf/mai-thinking-1.pdf)

MAI-Thinking-1의 RL 단계는 하나의 거대한 범용 climb으로 시작하지 않는다. Microsoft AI는 먼저 STEM/competitive coding, SWE/tool use, helpfulness/safety specialist teacher를 따로 만든다. 그다음 teacher trace를 self-distillation 방식으로 모아 consolidation SFT를 수행하고, 마지막으로 가벼운 RL을 한 번 더 올려 하나의 모델로 만든다.

이 구조가 중요한 이유는 세 영역의 reward가 서로 다르기 때문이다. STEM은 답이나 테스트로 검증하고, agentic task는 여러 번의 tool call과 환경 상태 변화를 평가하며, helpfulness/safety는 사람 선호, instruction following, 안전 정책, 정직성, 스타일처럼 더 주관적인 기준을 다룬다.

| Climb | 주된 환경 | Reward의 성격 | 핵심 데이터 | 통합 시 역할 |
| --- | --- | --- | --- | --- |
| STEM | single-turn 문제 풀이, competitive coding | 정답 비교, SymPy, AI judge, test case 실행 | STEM Mix, 160k competitive coding 문제 | 긴 reasoning trace와 검증 가능한 문제 해결 능력 |
| Agentic | SWE container, 일반 tool-use 환경 | 테스트 통과, 환경 상태 비교, trajectory judge | GitHub PR 기반 SWE 환경, synthetic tool-use task | multi-step ReAct loop와 도구 사용 능력 |
| Helpfulness/Safety | 대화, 지시 이행, 정책 경계 상황 | reward model, AI judge, verifiable reward, gated reward | human preference, IF, safety, honesty, style 데이터 | 사용자-facing 응답 품질과 안전한 거절/응답 경계 |

## STEM climb: 검증 가능한 문제 풀이를 길게 올리기

STEM climb은 세 specialist 중 가장 긴 RL run이다. 목표는 single-turn 문제 풀이에서 모델의 핵심 reasoning 능력을 강화하는 것이다. 범위는 수학, 물리, 화학, 공학, 컴퓨터 과학, competitive programming까지 포함한다.

이 climb의 기본 단위는 검증 가능한 데이터 쌍이다. 일반 STEM 문제는 $(q, a)$로, competitive coding 문제는 $(q, \{t_1, \dots, t_n\})$로 표현된다. 모델 출력 $y_i$에서 최종 답을 추출한 뒤 reward $R_{\text{task}}(q, y_i)$를 계산한다. 이 reward는 정답 비교, formal verifier, AI judge, 코드 실행 결과 중 하나로 만들어진다.

보고서에서 강조하는 점은 데이터 pipeline이다. STEM climb의 품질은 고품질, 적절한 난이도, 주제 다양성을 동시에 만족하는 문제를 얼마나 많이 확보하느냐에 달려 있다. Microsoft AI는 수백만 개 문서를 처리해 5M개 이상의 sample을 가진 STEM Mix를 만들었다.

## STEM data pipeline의 네 단계

STEM pipeline은 교재, 학술 PDF, forum discussion, competition archive, vendor 데이터처럼 형태가 다른 raw source를 처리한다. 각 처리는 독립적인 asynchronous stage로 구성되어 있고, source별로 필요한 stage를 조합한다. noise나 hallucination에 민감한 단계는 여러 번 실행한 뒤 consensus voting을 쓴다.

| 단계 | 하는 일 | 왜 필요한가 |
| --- | --- | --- |
| Hierarchical parsing | OCR, boilerplate 제거, chunking, 문서 구조 복원, question/answer span 추출 | PDF와 교재의 깨진 번호, cross-reference, 페이지 분할 문제를 줄인다 |
| QA pairing | chapter exercise와 appendix answer key처럼 떨어져 있는 질문과 답을 매칭 | 구조 신호와 semantic similarity를 함께 써 잘못된 pairing을 걸러낸다 |
| Curation | verifiability, question type, taxonomy, PII, answer leakage 검사와 rewrite | 검증 불가능하거나 개인정보가 있거나 답이 문제에 노출된 sample을 제거한다 |
| Scoring | 여러 tier 모델의 pass rate로 난이도 추정, blind grading으로 ground truth 오류 검사 | 너무 쉽거나 정답이 의심스러운 문제를 제거하고 hard problem을 보존한다 |

특히 curation 단계는 RL reward의 신뢰도와 직접 연결된다. multiple-choice 문제는 찍어서 맞힐 수 있기 때문에 reward signal을 흐릴 수 있고, proof 문제는 직접 검증하기 어렵다. 그래서 가능한 경우 open-ended 문제로 rewrite하며, 이 rewrite도 세 번 수행한 뒤 consensus를 통과하지 못하면 버린다.

scoring 단계는 ground truth를 맹신하지 않는 장치다. 네 개 model tier가 각 문제를 여러 번 풀고 pass rate로 난이도를 나눈다. 가장 강한 tier도 잘 풀지 못하는 문제는 consensus answer와 ground truth를 blind grading해, 정답 자체가 의심되면 제거한다.

## Competitive coding과 contamination 관리

competitive coding은 일반 STEM pipeline과 다르게 처리된다. PDF나 forum에서 문제를 추출하는 것만으로는 충분한 test case를 얻기 어렵기 때문이다. 그래서 target source와 vendor-acquired data를 사용하고, 각 문제의 reference solution이 모든 test case를 통과하는지 확인한다.

최종 competitive coding dataset은 여러 출처에서 모은 160k개 문제로 구성된다. 주제는 divide-and-conquer, dynamic programming, graph/tree algorithm, search algorithm 등을 포함한다. 각 문제에는 runtime/memory constraint가 붙고, 17개 프로그래밍 언어를 지원한다.

deduplication과 decontamination도 강하게 들어간다. 보고서에서 제시한 pipeline은 세 단계다.

- Exact deduplication: SHA-256 question hash로 완전 중복을 제거한다.
- Lexical fuzzy deduplication: character-level n-gram shingling과 MinHash LSH로 near-duplicate를 찾는다.
- Vector deduplication: lightweight embedding model의 cosine similarity로 의미적으로 가까운 중복을 찾는다.

이 과정은 내부 Olympiad/graduate-level STEM evaluation과 보고 대상 benchmark를 기준으로도 수행된다. 핵심은 데이터 손실을 최소화하면서 benchmark leakage는 엄격하게 배제하는 것이다.

## Agentic climb: 답변이 아니라 trajectory를 학습하기

Agentic climb은 모델이 외부 환경과 상호작용해야 하는 문제를 다룬다. 여기서는 한 번에 답을 쓰는 것이 아니라, 요청을 분해하고, tool이나 code action을 선택하고, observation을 읽고, 다음 행동을 수정한다. 따라서 reward도 최종 텍스트 하나가 아니라 trajectory 전체의 성공 여부와 품질을 본다.

Microsoft AI는 agentic domain을 크게 두 가지로 나눈다. 첫째는 실제 repository 안에서 문제를 고치는 software engineering 환경이다. 둘째는 scheduling, inventory management, report creation, customer support 같은 일반적인 structured tool-use 환경이다. 실제 climb에서는 STEM과 competitive coding mixture도 함께 넣는다. 보고서에 따르면 STEM task는 RL climb을 안정화하고 SWE/tool-calling performance에 positive transfer를 보였지만, agentic task가 STEM single-pass 성능을 올리거나 내리는 효과는 관찰되지 않았다.

multi-step RL framework는 기존 single-step objective를 trajectory로 확장한다. 하나의 environment는 task specification, Sandbox Execution Environment(SEE) session, reward/grader로 구성된다. model policy step에서는 tool call을 내거나 final answer를 낼 수 있고, tool call 결과는 observation으로 context에 붙는다. 다음 policy step은 이전 step의 token을 prefix로 보존한 상태에서 진행된다.

orchestration은 ReAct-style loop다. harness가 reasoning/action을 parse하고, tool call을 SEE로 dispatch하고, observation을 context에 append한 뒤 다시 policy에게 제어를 넘긴다. 종료 후에는 format check, rule-based check, executable test, state comparison, AI judge가 결합된 grader가 trajectory를 평가한다.

SEE는 각 agentic task마다 isolated container를 새로 provision하고 끝나면 폐기한다. 기본적으로 network-isolated이기 때문에 episode가 외부 rate limit이나 transient failure에 흔들리지 않는다. 네트워크가 필요한 환경은 caching proxy와 domain allowlist를 통해 통제한다.

## SWE 환경: PR에서 executable RL problem 만들기

SWE RL problem은 self-contained container image로 패키징된다. image 안에는 특정 commit에 checkout된 repository, pre-installed dependency, problem statement, grading용 unit test가 들어 있다. 모델은 rollout 동안 file read/edit, shell command, repository navigation 같은 tool call을 사용한다. 완료 신호를 내거나 turn limit에 도달하면 grader가 같은 container 안에서 test를 실행하고 expected outcome과 비교해 reward를 만든다.

이 환경을 만들기 위해 Microsoft AI는 public GitHub issue와 PR을 사용한다. 시작점은 102M개의 public GitHub PR이다. 여기서 main branch에 merge되었고, 15개 미만 파일을 수정하며, code/test change를 모두 포함하고, issue와 연결된 PR을 고른다. 이 필터 후 약 4.87M개의 linked issue PR이 남는다.

이후 pipeline은 executable environment를 만드는 쪽으로 진행된다.

- Automatic agentic environment building: LLM agent가 repository 상태를 읽고 Dockerfile을 만들어 executable container image를 생성한다.
- Reference grading signal extraction: base commit에 test diff만 적용한 pre-fix 실행과, test diff 및 code diff를 모두 적용한 post-fix 실행을 비교한다. fail-to-pass(F2P)는 문제 해결 signal이고, pass-to-pass(P2P)는 regression signal이다.
- Environment and grader verification: RL training에 쓰는 SEE infrastructure 안에서 empty patch는 실패하고 golden patch는 성공하는지 여러 번 검증한다. non-deterministic test behavior가 있으면 제거한다.
- Quality filtering and rewriting: problem statement가 너무 모호하거나 hidden test와 불일치하면 agent가 statement, repository, test를 검토해 clarity, test quality, leakage risk, feasibility를 평가하고 필요하면 statement를 rewrite한다.

결과적으로 4.87M candidate 중 2.08M개가 environment building을, 745,452개가 reference grading signal extraction을, 265,617개가 environment/grader verification을 통과했다. 전체 비율로는 5.5%만 살아남는다.

## Reward hacking을 막는 장치들

SWE 환경은 executable test로 채점되지만 reward hacking에서 자유롭지 않다. 보고서는 LLM monitor와 human review로 rollout을 점검했고, 세 가지 대표적인 cheating path를 확인했다.

| 유형 | 문제 | 대응 |
| --- | --- | --- |
| Internet search | public GitHub PR이므로 golden solution을 검색할 수 있음 | self-contained 문제는 internet을 끄고, 필요한 경우 최소 domain만 allow |
| Local git history search | local git database에서 solution commit을 찾을 수 있음 | base commit 이후 commit, reference, branch를 scrub해 time-traveled repository 구성 |
| Test tampering | test file이나 testing framework를 건드려 채점을 속일 수 있음 | grading 전 test file reset, hidden test 적용, LLM monitor와 anti-tampering heuristic 강화 |

정답 비교형 STEM에서는 answer leakage와 benchmark contamination이 핵심 위험이고, SWE에서는 모델이 환경 자체를 조작하는 위험이 추가된다.

## General tool use: 많은 tool 중 올바른 것을 고르기

일반 tool-use 환경은 SWE보다 tool 종류와 application domain이 다양하다. 각 problem은 query, available tool schema, initial environment state, grader로 구성된다. backend는 mocked service로 구현되고, 한 environment에 50개가 넘는 tool을 포함할 수 있다. 모델은 어떤 tool을 호출할지, parameter type과 argument를 어떻게 맞출지, stateful interaction을 어떻게 이어갈지를 배운다.

synthetic environment pipeline은 plain-English description에서 시작해 tool description, function implementation, seeded database, user request를 만든다. 이후 action execution, similarity removal, critique-and-refinement loop를 거친다. 보고서에 따르면 이 방식으로 150개 이상의 environment와 130,000개 task를 합성했다.

reward는 environment-specific grader와 cross-environment grader를 섞는다. 전자는 final environment state, tool usage pattern, final answer를 보고, 후자는 parallel tool call, duplicate call 회피, schema에 맞는 parameter 사용처럼 efficient tool use를 장려한다.

## Helpfulness and safety climb: 주관적 품질을 reward로 만들기

세 번째 specialist는 사용자가 실제로 마주하는 응답 품질을 다룬다. 여기에는 human preference, instruction following, steerability, safety, honesty, style이 포함된다. STEM이나 SWE처럼 정답이 명확한 영역이 아니기 때문에 reward는 훨씬 복합적이다.

가장 기본이 되는 것은 human preference data로 학습한 reward model이다. Microsoft AI는 post-trained MAI-Base-1을 기반으로 reward model을 만들고, 여러 vendor의 human annotator가 만든 preference data로 fine-tune한다. 입력은 context $c$와 $k$개의 response $y_1, \dots, y_k$이고, 목표는 각 response의 점수 $s_1, \dots, s_k \in [1,5]$를 text token으로 예측하는 것이다.

inference에서는 calibration을 위해 cyclic scoring을 쓴다. response 순서를 회전시키며 $k$번 prompt하고, 각 call의 첫 token distribution으로 reward $R_{\text{RM}}(c, y_i)$를 계산한다. 값은 해당 response가 최고 품질 점수인 $s_i = 5$를 받을 확률이다.

reward model만으로는 충분하지 않다. 빠르게 behavior를 조정해야 하는 경우에는 rubric-guided AI judge를 쓴다. constraint를 직접 확인할 수 있는 instruction following에는 verifiable reward도 쓴다. 예를 들어 "한 문단으로 답하라", "10단어 미만으로 답하라" 같은 조건은 rule-based check가 가능하다.

## Reward를 더하는 대신 우선순위를 둔다

helpfulness/safety reward의 어려움은 scale이 다른 signal을 함께 써야 한다는 데 있다. 단순 weighted sum을 쓰면 큰 magnitude를 가진 reward가 실제 중요도와 무관하게 gradient를 지배할 수 있다. 또 어떤 기준은 trade-off 대상이 아니다. unsafe response가 글을 잘 썼다고 해서 높은 reward를 받으면 안 된다.

| 방식 | 의미 | 사용 이유 |
| --- | --- | --- |
| Lexicographic reward shaping | 높은 priority reward가 rollout group 안에서 모두 동률일 때만 낮은 priority reward가 작동 | scale calibration 없이 instruction following 같은 primary objective를 우선시한다 |
| Gated reward application | 높은 priority reward가 최소 기준을 만족해야 낮은 priority reward를 적용 | safety처럼 non-negotiable한 기준을 품질 점수와 교환하지 않는다 |

safety가 대표적인 gated case다. 응답이 policy-compliant하지 않다고 판정되면, 다른 품질 점수와 무관하게 minimum reward를 받는다. policy를 지킨 경우에만 normal weighted mixture가 작동한다. 이는 안전하지 않은 고품질 답변이라는 모순적인 reward 경로를 차단한다.

## Instruction following, safety, honesty, style

Instruction following(IF)은 user, developer, system instruction을 우선순위에 맞게 따르는 능력이다. 데이터는 expert-written context와 synthetic data를 함께 쓴다. synthetic pipeline은 constraint taxonomy와 seed를 바탕으로 multilingual scenario, short/extended dialogue, instruction conflict, 40개 이상의 domain을 포함하도록 확장한다. reward는 deterministic verifier, LLM judge, reward model을 결합하며, IF-specific reward를 primary signal로 둔다.

safety 데이터는 두 실패 모드를 동시에 겨냥한다. 첫째는 거절해야 할 harmful prompt에 응답하는 unsafe compliance다. 둘째는 답해도 되는 borderline prompt를 불필요하게 거절하는 over-refusal이다. harmful prompt는 human red-teaming과 automated attack에서 오고, borderline prompt는 do-not-refuse slice와 capability data에서 온다. safety judge는 policy compliance, response engagement, response style을 평가한다.

honesty는 모델이 아는 것은 정확히 말하고 모르는 것은 적절히 hedge하는 능력으로 정의된다. 단순히 오류를 줄이려 하면 모델이 주장을 덜 하게 되므로, factual precision과 informativeness의 균형이 필요하다. 데이터는 factual query와 false-premise query를 포함한다. reward는 factuality와 confidence를 함께 봐 CONFIDENT_CORRECT에 가장 높은 점수를 주고, CONFIDENT_INCORRECT에 가장 큰 penalty를 준다.

style은 warmth without sycophancy, scannable structure, context에 맞는 tone 같은 출력 품질을 다룬다. 데이터는 PII-filtered Microsoft consumer Copilot logs, vendor-written context, Arena conversation을 사용한다. style judge는 0, 1, 2의 coarse scale로 major/minor/no issue를 평가하며, 너무 세밀한 rubric보다 hacking에 덜 취약하다고 설명된다.

## 세 teacher를 하나로 합치는 consolidation

세 specialist가 만들어진 뒤에는 이를 하나의 모델로 합친다. consolidation은 두 단계다. 먼저 specialist teacher들의 trace를 모아 SFT를 수행한다. 그다음 helpfulness/safety recipe를 기반으로 한 lightweight RL을 한 번 더 수행한다.

SFT stage는 앞선 self-distillation pipeline을 재사용한다. STEM과 agentic teacher는 각 climb의 여러 checkpoint에서 rollout을 sample하며, 뒤쪽 checkpoint를 우선하되 다양성을 위해 여러 checkpoint를 사용한다. 같은 context에 대해 correct rollout을 여러 개 보존하고, degenerate CoT만 가볍게 제거한다. helpfulness/safety teacher는 correctness뿐 아니라 style, structure, known defect를 LLM judge와 heuristic filter로 평가해 trace를 고른다.

최종 mixture는 다음과 같다.

| Capability | Sample weight | Token weight |
| --- | ---: | ---: |
| STEM and Coding | 56% | 89% |
| Agentic Capability | 11% | 9% |
| General Helpfulness and Safety | 33% | 2% |

이 표에서 눈에 띄는 것은 sample weight와 token weight의 차이다. STEM과 coding trace가 길기 때문에 token weight는 89%까지 올라간다. 반면 general helpfulness and safety는 sample 기준으로는 33%를 차지하지만 token 기준으로는 2%에 그친다. 보고서는 sample weight를 균형 있게 맞추는 것이 중요했다고 설명한다.

consolidation SFT는 표준 self-distillation recipe와 조금 다르게 4 epoch로 수행하고, maximum learning rate $1 \cdot 10^{-5}$에서 learning rate를 2배 decay한다. 이후 consolidation RL은 safety, over-refusal, style을 더 개선한다. 다만 reasoning performance를 유지하기 위해 maximum sequence length를 128k token으로 두고, RL mixture에 STEM과 coding 데이터를 소량 유지한다. 보고서에 따르면 이 두 요소가 없으면 complex task의 reasoning performance가 climb 중 천천히 저하된다.

## 요약: 하나의 climb이 아니라 통합 가능한 여러 climb

MAI-Thinking-1의 post-training 설계는 "모든 능력을 같은 reward로 학습한다"는 접근과 거리가 멀다. STEM은 정답과 test case를 중심으로 hard reasoning을 올리고, agentic climb은 containerized environment와 ReAct loop에서 multi-step 행동을 학습하며, helpfulness/safety climb은 preference, policy, honesty, style을 priority-aware reward로 묶는다.

그럼에도 최종 모델은 하나다. 연결고리는 self-distillation과 consolidation SFT다. specialist teacher의 강점을 trace 형태로 모아 단일 policy에 주입하고, 마지막 RL에서는 사용자-facing 품질을 다듬되 reasoning 데이터 일부와 긴 context를 유지해 성능 퇴화를 막는다.

다음 편: [평가, 안전성, 인프라가 말해주는 실제 위치](05-evaluations-safety-and-infrastructure.md)

## 출처

- https://microsoft.ai/pdf/mai-thinking-1.pdf
