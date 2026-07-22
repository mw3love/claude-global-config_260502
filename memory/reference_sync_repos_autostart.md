---
name: reference-sync-repos-autostart
description: "로그온 시 sync-repos 자동실행 세팅 — HKCU Run 키 + 숨김 VBS (이 PC 한정, git 밖)"
metadata: 
  node_type: memory
  type: reference
  originSessionId: c0c086e5-8abf-4b73-88e3-7c42862d98f3
  modified: 2026-07-22T00:13:30.232Z
---

**Windows 로그온 시 sync-repos.py를 자동 실행**하는 PC가 2대 있다 — 전 repo(`.claude` 포함, repos.json 첫 항목)를 `git pull --ff-only`.

| PC | 사용자 | 세팅일 |
|---|---|---|
| HOME-DESKTOP | 7make | 2026-07-17 |
| MW-Lenovo | minwoo | 2026-07-22 |

- **메커니즘:** HKCU 레지스트리 Run 키 `sync-repos-on-logon` = `wscript.exe "%LOCALAPPDATA%\sync-repos\startup.vbs"`(경로는 PC별 사용자명 반영)
- **VBS:** `%LOCALAPPDATA%\sync-repos\startup.vbs` — 60초 Sleep(네트워크 대기) 후 python 숨김 실행(`Run(...,0)`, 비대기). 로그 타임스탬프는 로캘 무관 수동 조립(`Now`의 오전/오후 로캘 포맷이 시스템 코드페이지라 UTF-8 로그와 섞이면 깨짐 — 2026-07-22 MW-Lenovo에서 발견).
- **로그:** `%LOCALAPPDATA%\sync-repos\startup.log` (VBS·python 공용, 둘 다 UTF-8/로캘무관 포맷으로 통일)
- **[2026-07-22 추가] 자기업데이트 + 완료알림** — `sync-repos.py` 자체가 이제 ⓐ 본 로직 전에 `.claude`를 먼저 pull해 스크립트/명단이 바뀌었으면 같은 인자로 자동 재실행(파이썬이 파일을 이미 메모리에 읽은 뒤라 pull만으론 반영 안 됨), ⓑ 실행이 끝나면 항상 Windows 풍선알림(`System.Windows.Forms.NotifyIcon` — WinRT 토스트는 이 PC에서 실측 실패해 대체) — "알림 없음 = 자동실행 자체가 안 됨"이 되도록 전체를 넓은 try/except로 감쌈. 상세: 스킬 `~/.claude/skills/sync-repos/SKILL.md`의 안전가드 절.

**왜 Task Scheduler가 아니라 Run 키인가:** 이 PC들에서 Task Scheduler 작업 *생성*이 관리자 권한을 요구해 `Register-ScheduledTask`(CIM/pwsh·5.1 둘 다)와 `schtasks` 모두 0x80070005로 거부됨. HKCU Run 키는 사용자 영역이라 관리자 불요 — PasteFlow 자동시작과 동일 패턴. Task Scheduler를 쓰려면 elevated 터미널 필요.

**끄기/되돌리기:** Run 키 값 삭제 하나 (`reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v sync-repos-on-logon /f`).

**PC마다 별도 세팅 필요** — 레지스트리·VBS는 git 동기화 대상이 아님(repos.json 명단만 동기화됨). 새 프로젝트 추가는 repos.json만 고치면 수동/자동 양쪽이 자동 반영 → 이 자동화는 재설정 불필요. 관련: [[project-reference-wiki-migration]]
