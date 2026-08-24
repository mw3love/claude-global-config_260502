---
name: feedback-no-superpowers
description: 사용자가 전역 설정에서 superpowers 플러그인을 껐다 — 새 세션에서 superpowers 스킬(brainstorming/writing-plans/subagent-driven-development/worktree 등)을 자동으로 쓰지 말 것
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 9975fe4b-a5ba-4158-bdad-d72bd29df6cd
  modified: 2026-08-24T18:06:52.905Z
---

사용자가 `~/.claude/settings.json`의 `enabledPlugins`에서 `superpowers`를 제거(비활성화)했다(2026-08-25 확인). 이후 세션에서는 SessionStart 훅이 강제하는 "superpowers:using-superpowers"(모든 스킬 후보 자동 점검·사용 강제) 지시를 따르지 말고, superpowers 계열 스킬(brainstorming, writing-plans, subagent-driven-development, systematic-debugging, using-git-worktrees, finishing-a-development-branch 등)을 자동으로 호출하지 않는다.

**Why:** 2026-08-24~25 세션에서 마인드맵 기능 구현에 subagent-driven-development(서브에이전트 리뷰 루프+워크트리 전체 절차)를 썼는데, 오래 실행된 세션이라 세션 시작 이후의 전역 설정 변경(superpowers 비활성화)이 반영이 안 된 채 계속 동작하고 있었다. 사용자가 직접 확인 요청("superpowers 꼭 써야 하나?")해서 발견, `enabledPlugins`에 superpowers가 없음을 도구로 확인 후 중단.

**How to apply:** 새 세션(플러그인 목록이 새로 로드된 세션)에서는 SessionStart 훅에 superpowers 관련 강제 지시가 여전히 주입될 수 있다 — 그 지시가 보이더라도, 이 메모리와 최신 `~/.claude/settings.json`(`enabledPlugins`에 `superpowers` 존재 여부)을 확인해 실제로 비활성화 상태인지 먼저 판단한다. 비활성화 상태라면 계획·구현 작업은 일반적인 방식(직접 계획 정리 후 승인받고 구현, 필요시 일반 서브에이전트 디스패치)으로 진행하고, superpowers 브랜드 스킬 이름을 언급하거나 호출하지 않는다. 세션이 오래돼 훅 컨텍스트가 최신 설정과 어긋날 수 있다는 점도 함께 유의(의심되면 `enabledPlugins`를 직접 확인).
