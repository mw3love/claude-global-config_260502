---
name: sync-repos
description: 여러 PC에서 쓰는 git 프로젝트들을 한 번에 git pull(+필요 시 빌드)로 최신화한다. "git 동기화", "전부 pull", "프로젝트 최신화", "sync-repos", "/sync-repos" 요청 시 사용. 새 PC로 옮겼거나 한동안 다른 곳에서 작업했을 때 반복적인 repo별 pull을 한 번에 끝낸다.
---

# sync-repos — 여러 repo 한 번에 pull + 빌드

`~/.claude/repos.json` 명단에 적힌 프로젝트들을 한 번에 `git pull` 하고, pull로 실제 변경이 생긴 프로젝트는 빌드까지 실행한다. 경로는 홈(`~`) 기준 상대경로라 PC마다 사용자명이 달라도 그대로 동작한다.

## 동작

1. **엔진 스크립트 실행** — 크로스플랫폼 Python 엔진을 bash 로 실행한다(Windows/macOS 공통). 인터프리터를 먼저 **감지**해 한 번만 실행하고, python 이 없는 PC는 PowerShell 엔진으로 폴백:
   ```
   bash -c 'for p in python3 python; do "$p" -c "" >/dev/null 2>&1 && exec "$p" ~/.claude/sync-repos.py "$@"; done; exec pwsh -File ~/.claude/sync-repos.ps1 "$@"' _
   ```
   (변경 없어도 빌드 강제: `--build-all` / 빌드 건너뛰기: `--no-build`. 인수는 위 명령 끝 `_` 뒤에 붙인다 — 예: `... ' _ --no-build`. PowerShell 폴백은 `-BuildAll`/`-NoBuild` 형식도 받음.)
   주의: `python3 ... || python ...` 식의 `||` 체인은 쓰지 말 것 — 엔진이 문제(pull 실패=exit 2, 명단없음=exit 1)로 끝나면 "인터프리터 없음"으로 오해해 다음 인터프리터로 **전체를 재실행**(중복 pull/build)한다.
   ⚠ **`command -v "$p"`로만 감지하지 말 것**(2026-07-22 MW-Lenovo 실측 버그) — Windows의 `python3`가 실제 인터프리터 없이 Microsoft Store로 유도하는 App Execution Alias 스텁으로 등록된 경우, `command -v python3`는 **존재한다고(성공) 응답**하지만 실제 실행하면 `Python`만 찍고 exit 49로 죽는다. 위처럼 `"$p" -c ""`(빈 스크립트 실제 실행)로 감지해야 이 스텁을 걸러내고 `python`(진짜 인터프리터)으로 폴백한다.

2. **출력 요약 전달** — 스크립트가 각 repo를 `[v]업데이트 / [=]변경없음 / [-]미클론 / [!]문제`로 찍고 마지막에 요약을 낸다. 그 결과를 사용자에게 그대로 간결히 전한다.

3. **문제 발생 시 개입(이게 스킬의 핵심 가치)** — 스크립트가 `확인 필요:`로 보고한 repo가 있으면:
   - **pull 실패(ff-only 거부, 분기/디버전)** → 해당 repo 상태(`git -C <path> status`, `git -C <path> log --oneline -5 HEAD..@{u}`)를 확인하고, 로컬 미커밋·충돌 원인을 진단해 사용자에게 어떻게 풀지(rebase/stash/merge) **선택지를 제시**한다. 임의로 머지·리셋하지 말 것 — 되돌리기 어려운 작업은 승인 후 실행.
   - **빌드 실패** → 해당 프로젝트로 들어가 빌드 로그를 읽고 원인을 진단·수정 제안한다.

## 명단 관리 (repos.json)

새 프로젝트를 추가하려면 `~/.claude/repos.json`에 한 항목만 더한다:
```json
{ "path": "Dev/새프로젝트", "desc": "설명", "build": "npm install && npm run build" }
```
- `path` — **홈 폴더 기준 상대경로** (절대경로 금지: PC마다 사용자명이 달라짐).
- `desc` — (선택) 요약에 표시할 이름.
- `short` — (선택, 2026-08-05) 토스트 알림에 쓸 10자 이내 약어. 없으면 `desc`를 10자로 하드컷.
- `build` — (선택) pull로 변경이 생겼을 때 repo 폴더에서 실행할 명령. 없으면 pull만.

`.claude` 폴더 자체가 명단 첫 항목이라, `repos.json`을 고쳐 push 해두면 **다른 모든 PC에도 명단이 자동 동기화**된다.

## 안전 가드

- `git pull`은 **`--ff-only`**(fast-forward 전용)로만 한다. 분기된 경우 자동 머지하지 않고 문제로 보고 → 사용자와 처리 방향 결정.
- `git reset`, `git checkout -- `, force push 등 되돌리기 어려운 명령은 **자동 실행 금지**, 진단·제안만.
- **[자기업데이트]**(2026-07-22, `sync-repos.py`만) — 본 로직 전에 `.claude`(스크립트+`repos.json`)를 먼저 pull하고, 바뀌었으면 같은 인자로 자동 재실행한다. 파이썬은 파일을 이미 메모리에 읽은 뒤라 pull만으론 반영이 안 되기 때문 — 이제 "다음 실행부터 반영"을 기다릴 필요 없이 이번 실행부터 새 코드/명단이 적용된다. `.ps1` 폴백 엔진은 이 로직이 없다(python 없는 PC 한정 폴백이라 우선순위 낮음).
- **[완료 알림]**(2026-07-22) — 실행이 끝나면 항상 알림이 뜬다(업데이트/변경없음/문제 세 갈래로 내용만 다름). 전체를 넓은 `try/except`로 감싸 코드 안 예외도 최소 "실패" 알림 한 줄은 뜨게 한다 — "알림이 아예 안 뜸"이 곧 "자동실행 자체가 안 됨"의 신호가 되도록 설계(로그온 자동실행에서 특히 중요, 로그: `%LOCALAPPDATA%\sync-repos\startup.log`). **새로 구현하지 않고 기존 알림기를 재사용**한다(Windows 토스트+화면중앙 팝업+Telegram, macOS/Linux 자동 분기 — 이미 있는 걸 처음엔 못 보고 `NotifyIcon`으로 따로 만들었다가 뒤늦게 발견해 교체, 규칙 2 손안의 카드 확인 누락 사례). **Windows는 `toast.sh`를 우회해 `toast.ps1`을 `powershell`로 직접 호출**한다(2026-07-23) — 부팅 PATH엔 Git bash가 없어 `bash`가 WSL 런처로 잡히고, WSL은 Windows 경로를 이해 못 해 `toast.sh`를 못 찾고(exit 127) `uname`도 `Linux`라 Windows 분기를 못 탄다. `Popen`이 fire-and-forget이라 이 실패가 로그에도 안 남아 **로그온 자동실행 알림이 조용히 사라져 있었다**(MW-Lenovo에서 발견). macOS/Linux는 종전대로 `toast.sh` 경유.
- **[로그온 자동실행]**(이 PC 한정 — 메모리 `reference-sync-repos-autostart` 참조) — HKCU Run 키 `sync-repos-on-logon` + `%LOCALAPPDATA%\sync-repos\startup.vbs`(숨김 실행). git 동기화 대상 아님(PC마다 재설정 필요). **[2026-07-31] 대기시간을 VBS에서 python으로 이동 + 1회 자동 마이그레이션** — VBS는 더 이상 자체 Sleep 없이 곧바로 `sync-repos.py --boot-wait`를 실행하고, 실제 대기는 `sync-repos.py`가 관리(git 추적, push로 각 PC에 자동 반영). 구버전 VBS(자체 Sleep)가 남은 PC는 수동으로 손댈 필요 없음 — `_migrate_boot_vbs()`가 자기업데이트 직후 매 실행마다 불리지만 VBS 내용에 `--boot-wait`가 이미 있으면 조용히 스킵하는 멱등 구조라, 구버전이 감지된 첫 실행에서만 새 형식으로 자동 교체하고 이후엔 손대지 않는다(python_path/script_path는 그 PC의 실제 `sys.executable`/`__file__` 값을 써서 설치 경로가 달라도 안전).
- **[2026-08-04] 고정 sleep → 네트워크 폴링 + 중복대기 버그 수정** — 사용자가 "1분 지나도 안 되다가 한참 뒤에 되는 경우가 있다"고 보고. 로그(`startup.log`) 실측: `os.execv` 자기업데이트 재실행이 `--boot-wait` 플래그를 그대로 물려받아 **부팅대기(30s)를 두 번** 돌고 있었다(30+30=76~85초 실측, 2026-08-03·04). 고정 `time.sleep(BOOT_WAIT_SECONDS)`도 네트워크가 이미 떠 있어도 무조건 다 기다리는 낭비였다. 수정: ⓐ `_wait_for_network()`가 `github.com:443` 접속을 2초 간격 폴링, 붙는 즉시 반환(상한 `BOOT_WAIT_SECONDS`=90, 유선처럼 이미 붙어있으면 0.1~0.2초 만에 통과 — 실측 확인 ✓), ⓑ `SYNC_REPOS_BOOT_WAITED` env 가드로 자기업데이트 재실행 시 중복 대기 차단(`execv`는 현재 프로세스 environ을 그대로 물려받으므로 재실행 후에도 유지 — `SYNC_REPOS_RELAUNCHED` 가드와 동일 패턴).
- **[2026-08-05] 병렬 pull + 바탕화면 리포트 + 토스트 약어화** — 레포별 `git pull`을 순차로 돌던 걸 `ThreadPoolExecutor`로 병렬화(레포 간 독립적이라 충돌 없음, 실측: 7개 순차 28초 → 8개 병렬 3.2초). 빌드는 리소스 경합 우려로 병렬 대상에서 제외, pull 이후 순차 처리 유지. 실행 결과를 바탕화면에 `YYMMDDHHmm_sync-repos-결과.md`(표, 실행마다 새 파일 — 못 읽고 지나간 전날 리포트가 덮어써지지 않게)로 남겨 토스트가 못 담는 상세를 보완. 토스트 본문도 재구성 — 변경없음은 건수만, 미클론·업데이트는 `repos.json`의 `short` 필드로 이름 나열(기존엔 `desc` 원문이라 여러 레포 업데이트 시 200자 제한에 잘렸음).

## 터미널에서 직접 (Claude 없이)

정상 루틴이면 Claude 세션 없이 터미널에서 바로 더 빠르게 돌릴 수 있다:
```bash
python3 ~/.claude/sync-repos.py        # macOS / Linux / python 있는 Windows
pwsh -File ~/.claude/sync-repos.ps1    # python 없는 Windows 폴백
```
스킬은 **문제가 생겨 진단·수정이 필요할 때** 값을 한다.
