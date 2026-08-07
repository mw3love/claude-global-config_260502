---
name: reference-session-handoff
description: "새 세션 핸드오프 자동화 — session-handoff.ps1이 클립보드+새 탭까지 열어줌, CLAUDE.md 규칙 10-b가 호출"
metadata: 
  node_type: memory
  type: reference
  originSessionId: 594e359b-5227-447d-8788-7c85e469df14
  modified: 2026-08-07T02:08:43.756Z
---

`~/.claude/session-handoff.ps1`(2026-08-07 추가)이 규칙 10-b의 `` `[🆕 새 세션]` `` 핸드오프를 자동화한다.

**동작**: `-PromptFile <임시파일> -Cwd <프로젝트경로>`로 호출하면 ⓐ 프롬프트 원문을 클립보드에 그대로 심고(파싱 없음, 오차 0 — 실측 확인) ⓑ 같은 Windows Terminal 창에 새 탭을 열어 그 프로젝트 경로에서 `claude`를 인자 없이 대기시킨다. 사용자는 새 탭에서 `Ctrl+V` → `Enter`만 하면 된다.

**왜 프롬프트를 인자로 안 넘기나**: `wt.exe`→`claude` 다단 인자 전달에서 따옴표·여러 단어 문자열이 깨지는 게 실측으로 재현됐다(테스트 중 `Write-Host "..." -ForegroundColor Green`의 `-ForegroundColor Green`이 문자열 안으로 밀려 들어감). 클립보드 경유만 이스케이핑 위험이 완전히 없는 경로라서 프롬프트는 항상 클립보드로, 명령줄엔 고정된 짧은 단어(`claude`)만 태운다.

**한계**: `wt.exe`가 없는 환경(비Windows, 다른 PC 원격)에선 스크립트가 클립보드까지만 하고 새 탭은 건너뛴다 — 이 경우 [[project-rules-audit-2026-07-11]]이 아니라 CLAUDE.md 규칙 10-b 자체의 폴백(코드블록 프롬프트)으로 돌아간다. `` `[다른 PC]` `` 항목은 애초에 이 자동화 대상이 아니다(이 PC에서 새 탭을 열어봐야 다른 PC엔 안 보임).
