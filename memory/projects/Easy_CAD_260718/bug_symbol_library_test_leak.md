---
name: bug-symbol-library-test-leak
description: 전체 pytest 스위트 실행 시 실제 사용자 symbol_library.json이 변조되는 미해결 격리 누락 버그
metadata: 
  node_type: memory
  type: project
  originSessionId: cbf55c56-1c43-4231-9aa8-74b8c4178464
  modified: 2026-08-25T05:31:14.050Z
---

`python -m pytest tests/` 전체 실행 후 리포 루트의 실제 `symbol_library/symbol_library.json`
(사용자 진짜 심볼 데이터)이 변조되는 게 2026-08-25 세션에서 관찰됨 — 심볼 하나의
`id`/`name`이 다른 값으로 바뀜(예: `e84eaa92`/"2" → `740ff1b0`/"4"). 원인 미조사(시간
관계상 `git checkout -- symbol_library/symbol_library.json`로 복구만 하고 넘어감).

**Why**: `tests/_shared.py`의 `_isolated_symbol_library()` 컨텍스트매니저가
`symbol_library._library_path()`를 임시 경로로 patch하는 게 표준 격리 방법인데, 이 콘텍스트를
안 쓰는 테스트(또는 `CanvasWindow()` 생성 자체가 트리거하는 어떤 초기화 경로)가 실경로에
쓰고 있는 것으로 추정 — `docs/history/2026-08.md`가 이미 기록한 "pytest 게이트웨이 키 소실
재발" 계열(로컬 격리 우회 경로가 두 번째로 또 있었던 사례)과 같은 패턴일 가능성이 높음.

**How to apply**: 다음에 전체 스위트를 돌린 뒤 `git status`에 이 파일이 떠 있으면, 무시하고
넘어가지 말고 어느 테스트가 원인인지 `git bisect`류로 좁혀서 고칠 것(현재는 매번 실행 후
`git diff symbol_library/symbol_library.json`로 확인 → 있으면 `git checkout --`로 복구하는
수동 우회만 하고 있음). 별도 조사 세션 필요.
