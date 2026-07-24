---
name: reference-sync-repos-autostart
description: "로그온 시 sync-repos 자동실행 세팅 — HKCU Run 키 + 숨김 VBS (이 PC 한정, git 밖)"
metadata: 
  node_type: memory
  type: reference
  originSessionId: c0c086e5-8abf-4b73-88e3-7c42862d98f3
  modified: 2026-07-22T23:17:50.893Z
---

**Windows 로그온 시 sync-repos.py를 자동 실행**하는 PC가 2대 있다 — 전 repo(`.claude` 포함, repos.json 첫 항목)를 `git pull --ff-only`.

| PC | 사용자 | 세팅일 |
|---|---|---|
| HOME-DESKTOP | 7make | 2026-07-17 |
| MW-Lenovo | minwoo | 2026-07-22 |

- **메커니즘:** HKCU 레지스트리 Run 키 `sync-repos-on-logon` = `wscript.exe "%LOCALAPPDATA%\sync-repos\startup.vbs"`(경로는 PC별 사용자명 반영)
- **VBS:** `%LOCALAPPDATA%\sync-repos\startup.vbs` — 60초 Sleep(네트워크 대기) 후 python 숨김 실행(`Run(...,0)`, 비대기). 로그 타임스탬프는 로캘 무관 수동 조립(`Now`의 오전/오후 로캘 포맷이 시스템 코드페이지라 UTF-8 로그와 섞이면 깨짐 — 2026-07-22 MW-Lenovo에서 발견).
- **로그:** `%LOCALAPPDATA%\sync-repos\startup.log` (VBS·python 공용, 둘 다 UTF-8/로캘무관 포맷으로 통일)
- **[2026-07-22 추가] 자기업데이트 + 완료알림** — `sync-repos.py` 자체가 이제 ⓐ 본 로직 전에 `.claude`를 먼저 pull해 스크립트/명단이 바뀌었으면 같은 인자로 자동 재실행(파이썬이 파일을 이미 메모리에 읽은 뒤라 pull만으론 반영 안 됨), ⓑ 실행이 끝나면 항상 알림 — "알림 없음 = 자동실행 자체가 안 됨"이 되도록 전체를 넓은 try/except로 감쌈. 알림은 새로 만들지 않고 **기존 `~/.claude/toast.sh` 디스패처를 그대로 호출**(macOS/Linux 자동 분기 — 처음엔 이 존재를 놓치고 `NotifyIcon`을 따로 만들었다가 뒤늦게 발견해 교체, [[feedback-notification-design]] 참조). 상세: 스킬 `~/.claude/skills/sync-repos/SKILL.md`의 안전가드 절.
- **[2026-07-22 추가 2] `-Persist` 플래그** — `toast.ps1`은 기본으로 화면중앙 팝업(`center-toast.ps1`)+알림음만 낸다(응답완료 등 고빈도 알림의 중복 피로 방지, 우하단 WinRT 토스트는 기본 제거). `sync-repos.py`는 `toast.sh "<msg>" persist`로 호출해 우하단 토스트를 **추가로** 띄운다 — 로그온 자동실행처럼 저빈도·무인 상황은 중앙 팝업을 놓치면 대안이 없어, 알림센터(종 아이콘)에 남는 토스트의 지속성이 필요하기 때문(사용자 판단, 실측 확인 ✓ 중앙+우하단 둘 다 노출). title/body는 `\n`으로 줄바꿈해 전달(한 줄로 이어붙이면 중앙 팝업 자동 줄바꿈이 문구 중간에서 꺾임). 텔레그램 발송은 중앙 팝업 호출 *뒤*에 둬야 함(동기 네트워크 호출이 앞에 있으면 팝업이 2~3초 지연 — 순서만으로 해결, 별도 백그라운드 불필요).
- **[정정] WinRT 토스트가 이 PC에서 안 되는 게 아니었다** — 직접 만든 스크립트로 `[Windows.UI.Notifications.ToastNotificationManager]`를 호출했을 때 타입로드/컬렉션열거 예외가 났던 건, `powershell.exe` 호출에 **`-Sta`(단일 스레드 아파트먼트) 플래그가 빠져서**였다(WinRT COM은 STA 필요). 기존 `toast.ps1`은 `-NoProfile -Sta -ExecutionPolicy Bypass`로 호출해 정상 동작 — 즉 "이 PC는 WinRT가 안 됨"이 아니라 "내 호출 방식이 틀렸음"이었다. `NotifyIcon`으로 대체한 결정 자체는 유효(기존 디스패처 재사용이 어차피 더 나음)하지만, 원인 진단은 오판이었다.

**왜 Task Scheduler가 아니라 Run 키인가:** 이 PC들에서 Task Scheduler 작업 *생성*이 관리자 권한을 요구해 `Register-ScheduledTask`(CIM/pwsh·5.1 둘 다)와 `schtasks` 모두 0x80070005로 거부됨. HKCU Run 키는 사용자 영역이라 관리자 불요 — PasteFlow 자동시작과 동일 패턴. Task Scheduler를 쓰려면 elevated 터미널 필요.

**끄기/되돌리기:** Run 키 값 삭제 하나 (`reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v sync-repos-on-logon /f`).

- **[2026-07-23 정정] 부팅 알림이 처음부터 조용히 깨져 있었다** — `_notify()`가 `bash toast.sh`를 부르는데, 무인 부팅 프로세스 PATH엔 Git bash가 없어 `shutil.which("bash")`가 WSL 런처(`system32\bash.exe`)로 잡힌다. WSL은 Windows 경로를 이해 못 해 `toast.sh`를 못 찾고(exit 127), `uname`도 `Linux`라 Windows 분기(`toast.ps1`)를 못 탄다. `Popen`이 fire-and-forget이라 로그엔 `[notify]`만 남고 실패는 안 찍혀 **실행은 정상인데 알림만 사라졌다**(그래서 "안 돌았다"고 오인). 위 "실측 확인 ✓"는 Git bash가 PATH에 있던 Claude 터미널/다른 PC 조건이었던 것으로 추정. **수정(커밋 793bbc4):** `sync-repos.py`가 `sys.platform=="win32"`이면 `toast.ps1`을 `powershell`로 직접 호출(bash 우회). 자기업데이트 relaunch가 있어 다른 PC(HOME-DESKTOP)도 다음 부팅 때 pull→재실행으로 자동 반영될 것(단 그 PC 실부팅 검증은 미완).

**PC마다 별도 세팅 필요** — 레지스트리·VBS는 git 동기화 대상이 아님(repos.json 명단만 동기화됨). 새 프로젝트 추가는 repos.json만 고치면 수동/자동 양쪽이 자동 반영 → 이 자동화는 재설정 불필요. 관련: [[project-reference-wiki-migration]]
