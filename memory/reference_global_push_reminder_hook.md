---
name: reference-global-push-reminder-hook
description: 다른 프로젝트 push 시 ~/.claude의 memory/ 외 미반영 변경을 doc-sync-hook(post-push)이 감지 — 2026-08-14 알림전용 도입, 2026-09-04 부분자동으로 전환
metadata: 
  node_type: memory
  type: reference
  originSessionId: e7bb6e45-8996-4abb-9e9e-7f4461f56c51
  modified: 2026-09-04T10:08:29.216Z
---

**배경:** 사용자가 프로젝트 작업 중 전역(`~/.claude`)에도 반영할 게 있으면 "전역도 같이 커밋 푸쉬해줘"라고 매번 수동으로 말해야 했다. `memory/`는 이미 [[reference_memory_sync_hook]](SessionEnd 훅)이 자동 commit+push한다. 문제는 나머지(`CLAUDE.md`·skills·hooks·`settings.json`)를 트리거할 신호가 statusline의 `global:` 세그먼트뿐이라 패시브했다는 것 — 안 보면 놓친다.

**감지 로직(2026-08-14, 현재도 동일):** `doc-sync-hook.py`(PostToolUse, git push 성공 후 발화 — primary)와 `doc-sync-hook.ps1`(python 없을 때 폴백)에 `global_reminder()` / `Get-GlobalReminder` 함수. 동작:
- push된 프로젝트의 cwd가 `~/.claude` 자체가 아닐 때만 체크(자기 자신 push 중이면 스킵).
- `~/.claude`의 `git status --porcelain` + `git log @{u}..`(unpushed 커밋)을 훑어, `memory/` 하위가 아닌 변경 파일이 하나라도 있으면 `additionalContext`로 텍스트를 주입.
- 기존 doc-sync 알림(코드 변경 시 문서 동기화 검토 지시)과 같은 자리에서, 있으면 `---` 구분자로 같이 뜨고 doc-sync 알림이 없어도 이 알림만 단독으로 뜬다.

**처리 정책 — 2026-08-14(알림전용) → 2026-09-04(부분자동)로 전환.** 예전엔 "자동으로 commit/push하지 마세요"를 명시해 자기수정 방지(규칙 12) 원칙을 지켰으나, 실사용해보니 이 감지→수동처리 왕복이 매 프로젝트 push마다 반복돼 사용자가 세션 종료 전 "정말 clean/sync인지" 계속 재확인해야 했다(대부분 모델 전환에 따른 `settings.json` 변경 등 trivial한 내용). [[project_rules_audit_2026-07-11]] 형태론(훅은 이미 관찰 가능한 트리거라 문구만 바꾸면 됨)에 따라 "알리기"→"판단해서 처리하기"로 바꿨다(코드 로직·감지 조건은 그대로, `global_reminder()`가 반환하는 지시문만 교체). 현재 정책의 정본은 CLAUDE.md 규칙 10-e — 삭제·민감정보 의심·원격 fast-forward 불가 세 가지만 예외로 사용자에게 묻고 나머지는 자동 커밋(+push)/gitignore.

**검증(2026-08-14):** 합성 JSON 페이로드로 `.py`/`.ps1` 양쪽 다 직접 실행해 실조건검증 — (1) 다른 cwd에서 push할 때 전역 미반영 변경(당시 이 두 훅 파일 자체의 미커밋 상태)이 리마인드로 뜨는 것, (2) cwd가 `~/.claude` 자체일 때 침묵하는 것 확인.

**설계 근거:** push를 막지 않는 이유는 — 전역 변경은 리뷰 없이 원격에 올리면 다른 PC가 pull할 때 검증 안 된 행동 규칙을 그대로 받는 리스크가 있어서(규칙 12), 매 프로젝트 push마다 강제로 막으면 무관한 작업까지 발이 묶인다. 그래서 pre-push(차단형)가 아니라 post-push(알림형)에 얹었다 — 이미 doc-sync-hook.py가 같은 지점에서 같은 패턴(성공한 push 뒤 additionalContext로 지시)을 쓰고 있어 새 훅 등록 없이 기존 인프라에 얹을 수 있었다([[project_rules_audit_2026-07-11]]의 "관찰 가능한 트리거 + 강제되는 산출물" 형태론에 부합).
