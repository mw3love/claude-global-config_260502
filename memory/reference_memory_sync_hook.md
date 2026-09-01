---
name: reference-memory-sync-hook
description: 세션 종료 시 ~/.claude/memory/만 자동 commit+push하는 SessionEnd 훅 — 여러 PC를 옮겨다니며 작업할 때 전역 메모리가 미커밋으로 방치되던 문제 해결
metadata: 
  node_type: memory
  type: reference
  originSessionId: cc2df336-4641-4350-9953-bb85a6fa320d
  modified: 2026-09-01T23:11:17.774Z
---

**문제(2026-08-12 사용자 지적):** 프로젝트 세션마다 `autoMemoryDirectory`가 메모리를 `~/.claude/memory/...`로 자동 기록하는데(공식 기능, `session-memory-hook.py`가 SessionStart에 설정), 그 repo의 git 커밋/푸쉬는 사용자가 `~/.claude`를 직접 열 때만 일어났다. 다른 PC로 옮겨다니며 여러 프로젝트만 커밋·푸쉬하고 마무리하는 워크플로에서 전역 메모리가 미커밋 상태로 방치됐고, statusline이 `cwd`(현재 프로젝트)만 보여줘 방치 자체를 알 길도 없었다. 이게 `sync-repos --ff-only` pull 실패("에러가 많이 났다")의 원인 중 하나였다.

**해법:** `~/.claude/memory-sync-hook.py`를 전역 `SessionEnd` 훅으로 등록(세션당 1회, 동기 실행 — `Stop`처럼 응답마다가 아님). `git status --porcelain -- memory/`로 변경 있을 때만 `add`→`commit`→`push`. 스코프는 `memory/` 하위뿐 — `CLAUDE.md`·`skills`·훅·`settings.json` 같은 행동/설정 파일은 여전히 사용자 승인 후 수동 커밋([[project-rules-audit-2026-07-11]] 규칙 12, 자기수정 방지). 성공은 조용히, push 실패(오프라인 등)만 토스트로 알림 — 로컬 커밋은 남으므로 데이터 유실은 없고 다음 sync-repos에서 재시도됨.

**의도적으로 분리한 것:** `sync-repos`의 pull 루프와는 완전히 무관하게 동작한다. `session-memory-hook.py`(SessionStart)에 2026-08-05 기록된 전례 — 그 훅을 sync-repos 루프에 결합했다가 미클론·git 에러로 불안정해져 되돌린 적이 있다([[reference-sync-repos-autostart]] 참조). 같은 실수를 반복하지 않기 위해 이번 SessionEnd 훅도 sync-repos 코드를 전혀 건드리지 않는 독립 메커니즘으로 설계했다.

**가시성 보완:** `statusline.py`/`statusline.ps1`에 `~/.claude` repo 상태를 추가 — `cwd`가 `~/.claude`가 아니고 전역 상태가 "clean, synced"가 아닐 때만 `global:...`로 표시(정상 상태는 숨겨서 소음 방지).

**실측 확인(2026-08-12):** 실제로 밀려 있던 `Easy_CAD_260718` 프로젝트의 메모리 미커밋 2건을 이 훅으로 commit+push까지 확인(commit `773b2bb`). statusline도 실제 렌더로 `global:` 세그먼트 노출 확인.

**경로 매칭 실패 사고 + 수정(2026-08-26, commit `1af8ae7`):** `session-memory-hook.py`(SessionStart, `autoMemoryDirectory` 설정 담당)가 `repos.json`의 홈 기준 상대경로로만 프로젝트를 식별했는데, 감시운용PC는 `Dev-Mw\`를 쓰고 매니페스트는 `Dev/`라 11개 중 8개가 매칭 실패 — 훅이 조용히 return하고 그 PC의 auto-memory가 2주 넘게 git 제외 기본 위치(`~/.claude/projects/<경로키>/memory/`)에만 쌓였다. 수정: 경로 매칭 실패 시 git remote URL(PC 무관)로, 그래도 안 되면 폴더명으로 폴백. 이름 겹치면 포기(오탐 방지). 이 사고를 계기로 전역 규칙 10-c 도입("git repo가 있는 프로젝트 사실은 memory 대신 그 repo의 CLAUDE.md에 쓴다").

**재검증(2026-09-02, MW-Samsung26 PC):** 사용자가 "한 달 전 만든 이 설정이 잘 작동하는지" 점검 요청 → 이 PC에서 실측: `session-memory-hook.log`에 최근 세션들(`.claude`·`Paste_flow`·`Easy_CAD_260718`·`PDF_Maker_260406`)의 `autoMemoryDirectory` 설정 기록 확인, 각 repo의 `.claude/settings.local.json`에 실제 반영 확인, `memory-sync-hook.py`(SessionEnd)의 `auto(memory): ... 세션 종료 시 동기화` 커밋들이 git log에 연속 확인, `git status --porcelain -- memory/` 클린 — 정상 작동 중. **미해결 미확인 항목:** 8/26 사고로 감시운용PC에 2주치 쌓였던 gitignore 위치의 stranded 데이터를 새 memory/projects/ 구조로 이관(백필)했다는 커밋은 `git log --all --grep`으로 못 찾음 — 그 PC를 직접 확인 전엔 유실 가능성 열려 있음.
