---
name: reference-sync-repos-autostart
description: "로그온 시 sync-repos 자동실행 세팅 — HKCU Run 키 + 숨김 VBS (이 PC 한정, git 밖)"
metadata: 
  node_type: memory
  type: reference
  originSessionId: c0c086e5-8abf-4b73-88e3-7c42862d98f3
  modified: 2026-08-03T23:05:22.955Z
---

**Windows 로그온 시 sync-repos.py를 자동 실행**하는 PC가 2대 있다 — 전 repo(`.claude` 포함, repos.json 첫 항목)를 `git pull --ff-only`.

| PC | 사용자 | 세팅일 |
|---|---|---|
| HOME-DESKTOP | 7make | 2026-07-17 |
| MW-Lenovo | minwoo | 2026-07-22 |
| moak-minwoo | aros | 2026-07-23 |

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

- **[2026-07-27 확인] 알림센터 UI에서 "안 보이는 것처럼" 보이는 건 버그가 아니라 그룹핑+이름 문제였다** — `moak-minwoo`(aros) PC에서 사용자가 "로그온 자동실행 알림이 알림센터에 안 남아있다"고 의심. `%LOCALAPPDATA%\Microsoft\Windows\Notifications\wpndatabase.db`를 직접 복사해 SQLite로 쿼리한 결과 로그온 토스트(10:25:54)와 이후 수동 실행 토스트(10:29:57) **둘 다 정상 등록**(만료 3일 뒤, `s:toast`/`s:banner`/`c:storage:toast` 모두 활성)였고, 스크린샷으로 실제 알림센터 확인해보니 **"Windows PowerShell" 헤더 아래 그룹핑되어 최신 것만 펼쳐 보이고 이전 것은 "+1 알림"으로 접혀 있었다** — 사용자가 이 접힘 표시를 못 보고 "없다"고 판단한 것. 즉 ⓐ 알림은 항상 `toast.ps1`의 borrowed AppId 때문에 "Claude Code"가 아니라 **"Windows PowerShell"이라는 이름으로 뜬다**(제목 텍스트 안에 "Claude Code"가 있어도 앱 이름 자체는 안 바뀜), ⓑ 같은 앱에서 알림이 연달아 오면 Windows가 자동으로 **그룹핑해 접는다** — 둘 다 실패가 아니라 정상 동작. 앞으로 이 자동화가 "안 뜬 것 같다"는 의심이 들면 먼저 알림센터에서 "Windows PowerShell" 그룹의 "+N 알림" 펼치기부터 확인할 것(재구현·재설계 불필요).
- 화면중앙 팝업(`center-toast.ps1`)은 원래 **일시적**이라 로그온 순간 화면을 보고 있지 않았으면 놓치는 게 정상 — 그래서 `-Persist` 토스트가 백업으로 있는 것이지, 팝업을 못 본 것 자체는 이상 신호가 아니다.
- **[2026-07-31] 대기시간을 VBS→python 상수로 이전 + VBS 자체를 1회 자동 마이그레이션** — 사용자가 "체감상 너무 길다"고 판단했고, 매번 PC별 VBS를 손으로 고치는 대신 값 변경이 push 한 번으로 퍼지길 원함(추가로 "PC마다 손으로 한 번씩 고쳐야 한다"는 것 자체도 자동화해 달라고 요청). 구조:
  - VBS는 이제 자체 `Sleep` 없이 곧바로 `python sync-repos.py --boot-wait`만 실행. 실제 대기 초는 `sync-repos.py` 상단 `BOOT_WAIT_SECONDS`(현재 30, git 추적)가 결정 — `--boot-wait` 플래그가 있을 때만 sleep한다. **대기시간을 바꾸려면 이제 `BOOT_WAIT_SECONDS`만 고쳐 push**하면 각 PC가 다음 pull(자기업데이트 포함)에서 자동 반영.
  - **VBS 자체의 1회 마이그레이션도 수동이 아니라 코드가 스스로 함** — `sync-repos.py`의 `_migrate_boot_vbs()`가 자기업데이트 직후 매 실행(=매 로그온)마다 불리지만, VBS 내용에 `--boot-wait`가 이미 있으면 조용히 스킵하는 멱등 구조라 실질적으로 딱 한 번만 파일을 고쳐 쓴다. 구버전 VBS가 있는 PC(HOME-DESKTOP·moak-minwoo)는 다음 로그온에서 old VBS→old 코드 실행→자기업데이트가 새 `sync-repos.py`(마이그레이션 함수 포함)를 pull&재실행→그 안에서 VBS를 자동 교체, 그 다음 로그온부터 새 방식 적용. `python_path`/`script_path`는 해당 PC의 실제 `sys.executable`/`__file__`로 채워 설치 경로 차이에도 안전 — 스크래치패드에서 가짜 old VBS로 마이그레이션+idempotent 스킵 둘 다 실측 확인.
  - MW-Lenovo는 수동으로 이미 새 VBS 적용 완료(위 마이그레이션 로직 배포 전에 먼저 손으로 바꿔둔 상태). HOME-DESKTOP·moak-minwoo는 아직 구버전 VBS(60초 자체 Sleep) — **push만 하면** 그 PC들이 다음 로그온에서 자동으로 갈아탄다(수동 개입 불필요).
- **[2026-08-04] "1분 넘게 안 되다가 한참 뒤에 됨" 원인 — 자기업데이트 재실행 시 부팅대기가 중복 실행됨** — `sync-repos.py`의 자기업데이트가 `os.execv`로 재실행할 때 `--boot-wait` 플래그가 그대로 남아있어, 가드 없이는 매 재실행마다 또 대기했다. `startup.log` 실측: 2026-08-03 30+30=76초, 2026-08-04 85초(자기업데이트가 거의 매 로그온마다 걸림 — 레포가 자주 push되므로). 고정 `time.sleep`도 네트워크가 이미 붙어 있어도 무조건 다 기다리는 낭비였음. 수정: `_wait_for_network()`(github.com:443 폴링, 붙는 즉시 반환, 상한 90s)로 교체 + `SYNC_REPOS_BOOT_WAITED` env 가드로 중복 대기 차단(`SYNC_REPOS_RELAUNCHED`와 동일 패턴 — `execv`는 현재 프로세스 environ을 그대로 물려받음). 코드는 이 PC(현재 세션)에만 반영, 아직 push 전 — push되면 각 PC가 다음 로그온에서 자기업데이트로 자동 반영.
