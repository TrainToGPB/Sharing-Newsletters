---
title: 4계층 에이전트 아키텍처
date: 2026-05-10
author: TrainToGPB
tags: [agents, multi-agent, agentic-design]
source: https://arxiv.org/html/2605.06651
summary: 사용자 → Project Coordinator → 워크스트림 코디네이터 → 전문 서브 에이전트의 4계층 구조와 그 위에 깔린 비동기 메시징·공유 파일시스템.
format: details
part: 3
---

# 4계층 에이전트 아키텍처

[2편](02-design-principles/) 에서 본 7원칙은 두 기둥 위에서 동작한다 — 4계층 에이전트 조직과 비동기 메시징·공유 파일시스템.

## 전체 모양

![agent hierarchy diagram](../assets/fig-1.png)
*User → Project Coordinator → 워크스트림 코디네이터 → 전문 서브 에이전트의 4계층. 사용자는 채팅으로만 끼어들고, 모든 통신은 비동기 메시징과 공유 파일시스템 위에서.*

사용자 입장에서 인터페이스는 채팅창 하나. 사용자는 한 명의 에이전트 — Project Coordinator — 와만 대화하고, 그 아래 흐름은 비동기로 진행됨. 단, 원하면 어느 깊이로든 드릴다운 가능. 이 단일 창구 디자인은 [원칙 5 (단계별 노출)](02-design-principles/#원칙-5-인지-부하의-단계별-노출-progressive-disclosure) 의 직접 결과.

## 4계층 역할

| 계층 | 역할 | 직접 작업 여부 | 베이스 모델 |
| --- | --- | --- | --- |
| User | 의도 제공·중간 개입·최종 검토 | — | (사람) |
| Project Coordinator | 의도 형식화, Goal 정의, 워크스트림 위임, 사용자와의 단일 창구 | 직접 안 함 | LLM |
| Workstream Coordinator | 한 Goal 책임. 자기 안에서 직선 시퀀스로 작업, 필요할 때 sub-agent 위임 | 일부 | LLM |
| Specialized Sub-agents | 문헌 탐색, 정리 증명, 코드 생성·실행, 외부 도구 호출 | 직접 함 | Gemini 3.1 Pro / Deep Think + 도구 |

각 계층의 디테일.

### Project Coordinator

- 사용자와 양방향 대화 — 의도를 받고, 시스템이 막히면 *먼저 도움 요청*
- Research Question 과 여러 Goal 로 의도 형식화
- 워크스트림 코디네이터에게 일 위임
- 워크스트림에서 escalation 이 올라오면 그것을 사용자에게 자연어로 풀어 전달

### Workstream Coordinator

- 한 Goal 을 끝까지 책임지는 단위
- 자기 작업을 시간 순서로 관리: *문헌 search → 보고서 갱신 → 웹 query → 보고서 갱신 → 사용자 추가 요청 처리 → 보고서 갱신 → 리뷰 요청* 식
- 같은 Goal 에 워크스트림 여러 개 가능 (다른 접근으로 동시 탐색)
- 막히면 Project Coordinator 에 escalate

### Specialized Sub-agents

- 베이스: 표준 LLM 호출 (주로 Gemini 3.1 Pro, 정리 증명 sub-agent 는 Gemini 3.1 Deep Think)
- 위에 도구 결합: 웹 검색, 코드 실행기, formal reasoning system
- 저자들 명시: 현재 AlphaEvolve / AlphaProof / Aletheia 같은 시스템을 sub-agent 로 통합하진 않았지만, 어디에 끼워 넣으면 좋을지 슬롯은 확보. *plug-in 가능한 슬롯* 으로 디자인됨

### User

- 시스템 워크플로의 한 노드로 다뤄짐. 외부 클라이언트가 아님
- 임의 시점에 임의 깊이로 끼어들 수 있음

## 두 기반 — 메시징과 파일시스템

### 비동기 메시징

- 에이전트끼리의 위임·보고는 모두 메시징으로
- 동기 호출 아님 → sub-agent 가 5분짜리 코드 실행을 돌려도 위 워크스트림 코디네이터는 잠기지 않음
- 한 워크스트림이 막혀도 다른 워크스트림은 진행
- 사용자 개입 메시지도 같은 메시징 시스템으로 흘러 들어감

**의미**: 단발 LLM 의 *질문 → 답* 동기 패턴 대신 *지속적으로 작업이 흐르는 가운데 사용자가 임의 시점에 끼어드는* 패턴 가능.

### 공유 파일시스템

- 같은 프로젝트 안 모든 에이전트가 같은 파일시스템 view
- 워크스트림끼리 산출물 공유 — 한 워크스트림의 lemma 가 다른 워크스트림 입력으로 흘러감
- 실패한 코드·시도도 영구 기록 (원칙 7) → 다음 워크스트림이 그 위에서 출발

**비유**: 저자들은 인간 조직에 비유 — *"잘 동작하는 조직처럼 명확한 커뮤니케이션 라인과 에스컬레이션 경로"*.

## 단순 트리가 아닌 이유

다이어그램만 보면 위계 트리처럼 보이지만, 실제 통신 패턴은 그래프에 가까움.

- 형제 노드 통신: 워크스트림끼리 공유 파일시스템으로 결과 주고받음
- 같은 계층 sub-agent 끼리도 메시징 가능 — 정리 증명 sub-agent 가 문헌 sub-agent 에 *"이 lemma 출처 확인해달라"* 직접 요청
- 사용자 → 임의 깊이 직접 드릴다운: Project Coordinator 라인 외에도 워크스트림에 직접 메시지 가능

이 그래프 같은 통신이 [원칙 4 (비동기 + 유연한 개입)](02-design-principles/#원칙-4-비동기-상호작용--유연한-개입) 을 실제로 가능하게 만듦. 단순 트리였다면 사용자가 한 워크스트림을 들여다보며 동시에 새 워크스트림을 띄우라고 지시하는 패턴이 어색했을 것.

## 디자인의 한 가지 부수 효과

저자들이 명시하지 않은 한 가지 — 인간 조직 비유 (Project Coordinator, Workstream Coordinator, Sub-agent) 가 의도적으로 사용자 익숙한 메타포 위에 올라앉음.

- 멘탈 모델 학습 비용 거의 0
- 누구한테 위임하고, 누구한테 escalate 하고, 막힌 부분 어떻게 표면화하는지 — 익숙한 인간 조직 패턴 그대로

**편집자 메모**: 사내 LLM 도구 만들 때 흔한 함정이 사용자가 한 번도 본 적 없는 추상 (*"semantic graph"*, *"context window manager"*, *"agentic framework"*) 을 인터페이스로 노출하는 것. 이 시스템은 정반대 — 가장 친숙한 비유 위에 가장 정교한 구조를 얹어, 사용자는 *"내 동료들에게 일을 부탁하는"* 모드로 시스템을 다룸.

## 다음 편

이 4계층 + 메시징 + 파일시스템 위에서 사용자가 한 프로젝트를 굴리는 동안 어떤 흐름이 흐르는지 — 다이어그램 세 개와 함께 단계별로. 다음 편 → [실제 사용 흐름](04-walkthrough/).

## 출처

- https://arxiv.org/html/2605.06651
