---
name: feedback-no-superpowers
description: 사용자가 superpowers 플러그인을 완전히 삭제(uninstall)했다 — 설치 자체가 없으니 새 세션에서 superpowers 스킬을 쓰거나 언급하지 말 것
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 9975fe4b-a5ba-4158-bdad-d72bd29df6cd
  modified: 2026-09-02T02:36:43.299Z
---

2026-08-25 `enabledPlugins`에서 비활성화된 상태였다가, **2026-08-26 사용자 요청으로 `claude plugin uninstall superpowers@claude-plugins-official`로 완전 삭제**했다(설치 목록 `installed_plugins.json`에서도 제거 확인). 이제 비활성화가 아니라 설치 자체가 없는 상태 — superpowers 계열 스킬(brainstorming, writing-plans, subagent-driven-development, systematic-debugging, using-git-worktrees, finishing-a-development-branch 등)을 언급·호출할 일 자체가 생기지 않는다.

**Why:** 서브에이전트를 많이 띄우는 방식(특히 subagent-driven-development, code-review ultra 등)이 사용자 Claude Code 요금제 사용량을 과하게 소모한다고 판단해 비활성화에서 완전 삭제로 전환. 같은 맥락에서 `code-review` 스킬(빌트인, 별도 플러그인 아님)에 대해서도 사용량 절감 방법을 문의 중이었다 — `skillOverrides: {"code-review": "hidden"}` 설정으로 끄는 방법이 있다는 조사 결과가 있으나 **공식 문서로 직접 재확인 전이라 미검증**(서브에이전트 WebFetch 결과, 다음 세션에서 실제 적용 전 `settings-reference.md` 재확인 필요).

**How to apply:** 다시 필요해지면 `claude plugin install superpowers@claude-plugins-official`로 재설치 가능(마켓플레이스는 `claude-plugins-official`, 이미 known marketplace로 등록돼 있음). 재설치하지 않는 한 이 스킬들은 존재하지 않으므로 자동 호출 걱정 자체가 없다.
