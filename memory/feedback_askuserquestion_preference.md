---
name: feedback-askuserquestion-preference
description: 모호한 질문엔 텍스트보다 AskUserQuestion(선택창)을 기본으로 — 추천 옵션 고르고 Other에 보완 의견 다는 방식을 선호
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 594e359b-5227-447d-8788-7c85e469df14
  modified: 2026-08-07T00:31:01.090Z
---

선택지로 나눌 수 있는 질문이면 텍스트 질문보다 `AskUserQuestion`(선택창)을 기본으로 쓴다. 선택지 중 하나에 "(추천)"을 붙이고 Other(자유입력)를 항상 연다.

**Why:** 사용자는 선택창 맨 아래 자유입력란에 "1번이 좋은데 이러이러한 부분만 추가해서 진행하면 좋을듯"처럼 **추천안 선택 + 보완 의견**을 함께 적는 방식으로 빠르게 의사결정한다(2026-08-07). 선택창에 뜨는 추천 표시 자체가 이 워크플로의 핵심 입력이다 — 텍스트로만 물으면 이 경로를 못 쓴다.

**How to apply:** 완전 개방형 서술(예: "목표를 한 문장으로 요약하면?")이 아니라 둘 이상의 갈림길이 있는 질문이면, 애매해도 우선 선택지 2-4개로 구조화해 AskUserQuestion으로 낸다. 규칙 6(모호하면 묻는다 — 선택창 우선)과 정합. deep-interview 스킬도 이 선호에 맞춰 기본을 AskUserQuestion으로 수정함([[deep-interview 스킬 파일]] 자체가 근거, 2026-08-07).
