---
name: reference-sync-repos-autostart
description: "로그온 시 sync-repos 자동실행 세팅 — HKCU Run 키 + 숨김 VBS (이 PC 한정, git 밖)"
metadata: 
  node_type: memory
  type: reference
  originSessionId: c0c086e5-8abf-4b73-88e3-7c42862d98f3
---

이 PC(HOME-DESKTOP)는 **Windows 로그온 시 sync-repos.py를 자동 실행**한다 — 전 repo(`.claude` 포함, repos.json 첫 항목)를 `git pull --ff-only --no-build`. 2026-07-17 세팅.

- **메커니즘:** HKCU 레지스트리 Run 키 `sync-repos-on-logon` = `wscript.exe "C:\Users\7make\AppData\Local\sync-repos\startup.vbs"`
- **VBS:** `%LOCALAPPDATA%\sync-repos\startup.vbs` — 60초 Sleep(네트워크 대기) 후 cmd로 python 숨김 실행(`Run(...,0)`). `now` 인자면 Sleep 스킵(테스트용).
- **로그:** `%LOCALAPPDATA%\sync-repos\startup.log` (타임스탬프 ASCII, python 출력 utf-8)

**왜 Task Scheduler가 아니라 Run 키인가:** 이 PC에서 Task Scheduler 작업 *생성*이 관리자 권한을 요구해 `Register-ScheduledTask`(CIM/pwsh·5.1 둘 다)와 `schtasks` 모두 0x80070005로 거부됨. HKCU Run 키는 사용자 영역이라 관리자 불요 — PasteFlow 자동시작과 동일 패턴. Task Scheduler를 쓰려면 elevated 터미널 필요.

**끄기/되돌리기:** Run 키 값 삭제 하나 (`reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v sync-repos-on-logon /f`).

**PC마다 별도 세팅 필요** — 레지스트리·VBS는 git 동기화 대상이 아님(repos.json 명단만 동기화됨). 새 프로젝트 추가는 repos.json만 고치면 수동/자동 양쪽이 자동 반영 → 이 자동화는 재설정 불필요. 관련: [[project-reference-wiki-migration]]
