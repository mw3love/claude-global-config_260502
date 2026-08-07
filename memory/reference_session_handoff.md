---
name: reference-session-handoff
description: "새 세션 핸드오프 — session-handoff.ps1이 프롬프트를 클립보드에 복사(새 탭 자동오픈은 시도했다가 되돌림), CLAUDE.md 규칙 10-b가 호출"
metadata:
  node_type: memory
  type: reference
  originSessionId: 594e359b-5227-447d-8788-7c85e469df14
  modified: 2026-08-07T04:15:03.549Z
---

`~/.claude/session-handoff.ps1`(2026-08-07 추가)이 규칙 10-b의 `` `[🆕 새 세션]` `` 핸드오프에서 프롬프트 전달을 자동화한다.

**동작**: `-PromptFile <임시파일>`로 호출하면 프롬프트 원문을 클립보드에 그대로 심는다(파싱 없음, 오차 0 — 실측 확인). 새 탭·새 창을 여는 건 하지 않는다 — 사용자가 원하는 터미널에서 직접 새 세션을 열고 `Ctrl+V` → `Enter`.

**시도했다가 되돌린 것 — 새 탭 자동 오픈**: 처음엔 `wt.exe`로 같은 창에 새 탭을 열어 `claude`까지 대기시키는 것도 만들었으나, 실사용자가 터미널 창을 여러 개 띄워놓고 쓰는 워크플로우에서 `wt.exe -w 0`이 "지금 이 세션이 떠 있는 창"이 아니라 다른 창으로 탭을 여는 게 실측 확인됐다(2026-08-07). 어느 창에 새 세션을 열지는 사용자가 결정하는 게 맞다고 판단해 자동 오픈은 제거하고 클립보드 복사만 남겼다.

**왜 프롬프트를 인자로 안 넘기나**: 새 탭 자동화를 테스트하던 중 `wt.exe`→`powershell` 다단 인자 전달에서 따옴표·여러 단어 문자열이 깨지는 게 재현됐다(`Write-Host "..." -ForegroundColor Green`의 `-ForegroundColor Green`이 문자열 안으로 밀려 들어감). 클립보드 경유만 이스케이핑 위험이 완전히 없는 경로라, 자동화가 남긴 유일한 부분도 클립보드다.

**클립보드 자체도 100% 안전하진 않다**: `Set-Clipboard`가 Windows 쪽 사정(다른 프로세스가 클립보드를 순간 점유 등)으로 종종 실패한다 — 실측 재현됨(`Requested Clipboard operation did not succeed`). 최초 버전은 이 실패를 무시하고 `HANDOFF_OK`를 찍는 거짓 성공 버그가 있었다. 지금은 `Set-Clipboard` 후 `Get-Clipboard`로 즉시 되읽어 원본과 비교하고, 실패하면 최대 5회(200ms 간격) 재시도하며, 그래도 안 되면 `HANDOFF_FAILED`로 정직하게 실패를 보고한다(exit 1).
