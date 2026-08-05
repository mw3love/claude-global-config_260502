#!/usr/bin/env python3
# 여러 PC에서 쓰는 git 프로젝트들을 한 번에 git pull(+빌드)한다.
# sync-repos.ps1 의 크로스플랫폼(Windows/macOS/Linux) 포팅. 동작은 .ps1 과 동일.
#   ~/.claude/repos.json 명단을 읽어 각 repo 를 fast-forward(--ff-only) pull.
#   경로는 홈(~) 기준 상대경로 -> PC마다 사용자명이 달라도 동작.
#   pull 로 실제 변경이 생긴 repo 만 build 명령을 실행.
# 사용:  python3 ~/.claude/sync-repos.py [--build-all] [--no-build]
#
# [자기업데이트] 본 로직 전에 .claude 자체(이 스크립트 + repos.json)를 먼저 pull하고,
# 바뀌었으면 같은 인자로 재실행한다 — 파이썬은 파일을 이미 메모리에 읽은 뒤라 pull만으론
# 반영이 안 되기 때문. 로그온 자동실행처럼 사람이 지켜보지 않는 경로에서 특히 중요.
#
# [알림] 실행이 끝나면 항상 알림을 하나 띄운다(성공/변경없음/문제 구분). "매번 뜬다"는 걸
# 사용자가 기대하게 만들어, 알림이 아예 안 뜨는 것 자체가 "자동화가 실행조차 안 됐다"는
# 신호가 되게 한다. main() 전체를 try/except로 감싸 코드 안의 어떤 예외가 나든 최소 "실패"
# 알림 한 줄은 뜨게 한다. 알림은 새로 만들지 않고 기존 ~/.claude/toast.sh 디스패처를 재사용
# (Windows 토스트+화면중앙 팝업+Telegram, macOS/Linux 자동 분기 — 처음엔 이걸 놓치고 별도
# NotifyIcon 구현을 만들었다가 2026-07-22 뒤늦게 발견해 교체).
import sys, os, json, subprocess, shutil, datetime, traceback, time, socket
import concurrent.futures as cf

# 로그온 직후 네트워크가 아직 안 붙었을 때의 최대 대기 시간(상한선). 고정 sleep이 아니라
# _wait_for_network()가 github.com 연결을 폴링해 붙는 즉시 반환한다 — 유선처럼 네트워크가
# 이미 떠 있으면 거의 즉시 진행되고, 느린 Wi-Fi 부팅에서만 이 상한까지 기다린다.
# VBS(git 비동기화, PC별 파일)가 아니라 여기서 관리 — 값을 바꿔 push하면 각 PC는 다음
# pull(자기업데이트 포함)로 자동 반영. VBS는 --boot-wait 플래그만 넘긴다.
BOOT_WAIT_SECONDS = 90

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

LOG_DIR = os.path.join(os.path.expanduser("~"), "AppData", "Local", "sync-repos") if os.name == "nt" else None
LOG_PATH = os.path.join(LOG_DIR, "startup.log") if LOG_DIR else None


def git(cwd, *args):
    return subprocess.run(["git", "-C", cwd, *args], capture_output=True, text=True, encoding="utf-8")


def _wait_for_network(max_seconds):
    """github.com:443 접속을 2초 간격으로 폴링, 붙는 즉시 반환(고정 sleep 아님).
    max_seconds까지도 안 붙으면 포기하고 진행 — 이후 git pull이 실패하며 정상적으로
    '확인 필요' 알림으로 이어진다(기존 실패 경로 재사용, 별도 처리 불필요)."""
    start = time.time()
    while time.time() - start < max_seconds:
        try:
            socket.create_connection(("github.com", 443), timeout=3).close()
            _log("boot-wait: 네트워크 확인됨 (%.1fs 소요)" % (time.time() - start))
            return
        except OSError:
            time.sleep(2)
    _log("boot-wait: %ds 대기해도 네트워크 미확인 — 진행" % max_seconds)


def _log(line):
    if not LOG_PATH:
        return
    try:
        os.makedirs(LOG_DIR, exist_ok=True)
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write("%s  %s\n" % (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), line))
    except Exception:
        pass


def _notify(title, body):
    """[알림] 기존 ~/.claude/toast.sh 디스패처 재사용(직접 알림 구현 안 함) — Windows는
    toast.ps1(화면중앙 center-toast.ps1+알림음+Telegram), macOS/Linux는 osascript/notify-send로
    이미 분기돼 있다(실측 확인 ✓ 2026-07-22). toast.sh가 없는 환경(리포 없이 스크립트만
    배포된 경우 등)이면 조용히 스킵. title/body 사이에 줄바꿈을 넣는 이유: 한 줄로 이어붙이면
    중앙 팝업의 자동 줄바꿈이 문구 중간에서 꺾여 가독성이 떨어짐(2026-07-22 실측 발견) —
    일반 알림(Response complete 등)은 짧은 단문이라 이 문제가 없고 sync-repos만 해당."""
    _log("[notify] %s — %s" % (title, body))
    dispatcher = os.path.join(os.path.dirname(os.path.abspath(__file__)), "toast.sh")
    if not os.path.isfile(dispatcher):
        return
    msg = "%s\n%s" % (title, body[:200])
    # persist: 로그온 자동실행처럼 사람이 안 지켜보는 저빈도 호출이라, 중앙 팝업을 놓치면
    # 대안이 없다 — 우하단 토스트도 같이 띄워 알림센터에 남긴다(-Persist, Windows만
    # 의미 있음). 일반 응답완료 알림(고빈도)은 이 플래그를 안 쓴다.
    # [Windows] bash를 경유하지 않고 toast.ps1을 powershell로 직접 부른다 — 부팅 PATH엔
    # Git bash가 없어 `bash`가 WSL 런처(system32\bash.exe)로 잡히고, WSL은 Windows 경로를
    # 이해 못 해 toast.sh를 못 찾고(exit 127) uname도 Linux라 Windows 분기를 못 탄다.
    # Popen은 fire-and-forget이라 이 실패가 로그에도 안 남아 알림이 조용히 사라졌다
    # (2026-07-23 MW-Lenovo 부팅에서 발견). toast.sh의 Windows 분기가 하던 일과 동일.
    try:
        if sys.platform == "win32":
            ps1 = os.path.join(os.path.dirname(os.path.abspath(__file__)), "toast.ps1")
            subprocess.Popen(["powershell.exe", "-NoProfile", "-Sta",
                              "-ExecutionPolicy", "Bypass", "-File", ps1,
                              "-Message", msg, "-Persist"],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            bash = shutil.which("bash") or "bash"
            subprocess.Popen([bash, dispatcher, msg, "persist"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception as e:
        _log("notify 실패(무시하고 계속): %s" % e)


def _self_update_and_relaunch():
    """[자기업데이트] .claude(스크립트+repos.json)를 본 로직 전에 먼저 pull. 변경 있으면
    같은 인자로 재실행해 이번 실행부터 새 코드/명단이 반영되게 한다. 실패(로컬 미커밋과
    충돌 등)해도 치명적이지 않으니 조용히 건너뛰고 계속 진행 — 재실행 무한루프 방지는
    env 플래그로."""
    if os.environ.get("SYNC_REPOS_RELAUNCHED") == "1":
        return
    claude_dir = os.path.dirname(os.path.abspath(__file__))
    if not os.path.isdir(os.path.join(claude_dir, ".git")):
        return
    before = git(claude_dir, "rev-parse", "HEAD").stdout.strip()
    pull = git(claude_dir, "pull", "--ff-only")
    if pull.returncode != 0:
        last = (pull.stderr or pull.stdout).strip().splitlines()
        _log("self-update 건너뜀(pull 실패) — %s" % (last[-1] if last else ""))
        return
    after = git(claude_dir, "rev-parse", "HEAD").stdout.strip()
    if before != after:
        _log("self-update: %s -> %s, 재실행" % (before[:8], after[:8]))
        os.environ["SYNC_REPOS_RELAUNCHED"] = "1"
        os.execv(sys.executable, [sys.executable, os.path.abspath(__file__)] + sys.argv[1:])


_VBS_TEMPLATE = '''Dim fso, logDir, logPath, objShell
Set fso = CreateObject("Scripting.FileSystemObject")
logDir = CreateObject("WScript.Shell").ExpandEnvironmentStrings("%LOCALAPPDATA%") & "\\sync-repos"
If Not fso.FolderExists(logDir) Then fso.CreateFolder(logDir)
logPath = logDir & "\\startup.log"

Function Timestamp()
    Timestamp = Year(Now) & "-" & Right("0" & Month(Now), 2) & "-" & Right("0" & Day(Now), 2) & _
        " " & Right("0" & Hour(Now), 2) & ":" & Right("0" & Minute(Now), 2) & ":" & Right("0" & Second(Now), 2)
End Function

Sub LogMsg(msg)
    Dim f
    Set f = fso.OpenTextFile(logPath, 8, True)
    f.WriteLine Timestamp() & "  " & msg
    f.Close
End Sub

LogMsg "VBS triggered, dispatching (boot-wait handled by python)"
On Error Resume Next
Set objShell = CreateObject("WScript.Shell")
objShell.Run """{python_path}"" ""{script_path}"" --boot-wait", 0, False
If Err.Number <> 0 Then
    LogMsg "Run FAILED: " & Err.Number & " " & Err.Description
Else
    LogMsg "Run dispatched OK"
End If
'''


def _migrate_boot_vbs():
    """[VBS 1회 자동 마이그레이션] 로그온 자동실행 PC(HOME-DESKTOP·moak-minwoo 등)의
    구버전 startup.vbs(자체 WScript.Sleep)를 --boot-wait 방식으로 자동 교체한다.
    이미 새 방식(--boot-wait 포함)이면 조용히 스킵 — 매 실행(로그온마다)마다 불려도
    실질적으로 딱 한 번만 파일을 고친다. 자동실행 자체가 없는 PC(VBS 없음)는 건드리지
    않는다. python_path/script_path는 이 PC에서 실제로 이 프로세스를 띄운 값(sys.executable,
    __file__)을 그대로 써서 PC마다 다른 설치 경로에도 안전하다."""
    if os.name != "nt" or not LOG_DIR:
        return
    vbs_path = os.path.join(LOG_DIR, "startup.vbs")
    if not os.path.isfile(vbs_path):
        return
    try:
        with open(vbs_path, encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        _log("VBS 마이그레이션 건너뜀(읽기 실패): %s" % e)
        return
    if "--boot-wait" in content:
        return
    new_content = _VBS_TEMPLATE.format(python_path=sys.executable, script_path=os.path.abspath(__file__))
    try:
        with open(vbs_path, "w", encoding="utf-8") as f:
            f.write(new_content)
        _log("VBS 마이그레이션 완료 — --boot-wait 방식으로 교체")
    except Exception as e:
        _log("VBS 마이그레이션 실패(쓰기): %s" % e)


def _pull_one(home, r):
    """레포 하나의 pull 단계(네트워크 바운드)만 수행 — ThreadPoolExecutor로 병렬 실행된다.
    빌드는 리소스 경합을 피하려 이 함수엔 포함하지 않고 main()에서 순차로 처리한다."""
    rel = r.get("path", "")
    full = os.path.join(home, rel.replace("/", os.sep))
    name = r.get("desc") or rel
    entry = {"name": name, "full": full, "r": r, "status": "", "detail": ""}

    if not os.path.isdir(os.path.join(full, ".git")):
        entry.update(status="skip", detail="이 PC에 없음(미클론)")
        return entry

    dirty = git(full, "status", "--porcelain").stdout.strip()
    before = git(full, "rev-parse", "HEAD").stdout.strip()

    pull = git(full, "pull", "--ff-only")
    if pull.returncode != 0:
        last = (pull.stderr or pull.stdout).strip().splitlines()
        detail = "pull 실패 — " + (" ".join(last[-1].split()) if last else "")
        entry.update(status="error", detail=detail)
        return entry

    after = git(full, "rev-parse", "HEAD").stdout.strip()
    entry.update(changed=(before != after), dirty=dirty)
    return entry


def _short_name(r):
    """[토스트 표시명] repos.json의 short 필드(사람이 지정한 10자 이내 약어)를 우선 쓰고,
    없으면 desc를 10자로 하드컷한다 — 신규 레포가 short 없이 추가돼도 토스트가 깨지지
    않도록 하는 폴백(품질보다 항상 뭔가는 뜨는 게 우선)."""
    s = r.get("short")
    if s:
        return s[:10]
    return (r.get("desc") or r.get("path") or "").strip()[:10]


_STATUS_LABELS = {
    "skip": "미클론",
    "error": "pull 실패",
    "nochange": "변경없음",
    "updated": "업데이트",
    "built": "업데이트+빌드",
    "builderror": "빌드 실패",
}


def _write_desktop_report(results, ok, noch, skip, bad):
    """[바탕화면 리포트] 토스트는 title+body 200자로 잘려 정보 손실이 크다는 사용자 피드백
    (2026-08-05)에 따라, 매 실행마다 바탕화면에 전체 결과를 표로 남긴다. 사용자가 읽고
    직접 지우는 용도라 파일명을 고정해 실행마다 덮어쓴다. Desktop 폴더가 없는 환경
    (헤드리스 서버 등)은 조용히 스킵."""
    desktop = os.path.join(os.path.expanduser("~"), "Desktop")
    if not os.path.isdir(desktop):
        return
    # 파일명 접두사(YYMMDDHHmm)로 실행마다 별도 파일을 남긴다 — 고정 파일명 덮어쓰기였을 때
    # 전날 리포트를 못 읽고 새 로그온이 그걸 덮어써버리는 문제가 있었다(사용자 피드백
    # 2026-08-05). 접두사가 앞에 있어야 바탕화면 이름순 정렬이 곧 시간순이 된다.
    prefix = datetime.datetime.now().strftime("%y%m%d%H%M")
    path = os.path.join(desktop, "%s_sync-repos-결과.md" % prefix)
    lines = [
        "# sync-repos 결과 — %s" % datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "",
        "| 레포 | 상태 | 상세 |",
        "|---|---|---|",
    ]
    for e in results:
        lines.append("| %s | %s | %s |" % (e["name"], _STATUS_LABELS.get(e["status"], e["status"]), e["detail"]))
    lines += ["", "요약: 업데이트 %d / 변경없음 %d / 미클론 %d / 문제 %d" % (ok, noch, skip, len(bad))]
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
    except Exception as e:
        _log("바탕화면 리포트 쓰기 실패: %s" % e)


def main():
    build_all = "--build-all" in sys.argv or "-BuildAll" in sys.argv
    no_build = "--no-build" in sys.argv or "-NoBuild" in sys.argv

    home = os.path.expanduser("~")
    manifest = os.path.join(home, ".claude", "repos.json")

    if not os.path.isfile(manifest):
        print("[X] 명단 파일 없음: %s" % manifest)
        _notify("sync-repos 실패", "명단 파일 없음: %s" % manifest)
        sys.exit(1)

    try:
        with open(manifest, encoding="utf-8") as f:
            repos = json.load(f)
    except Exception as e:
        print("[X] repos.json 파싱 실패: %s" % e)
        _notify("sync-repos 실패", "repos.json 파싱 실패: %s" % e)
        sys.exit(1)

    # fnm(Fast Node Manager)로 node 를 깔면 node/npm 이 대화형 셸 활성화(eval "$(fnm env)")에만 PATH 로 들어온다.
    # sync-repos 의 빌드 서브프로세스는 비대화형이라 그 활성화가 없어 npm 을 못 찾는다(macOS 실측).
    # fnm 이 있으면 빌드 명령 앞에 활성화를 붙여 이 구멍을 메운다. Windows 는 .ps1 엔진 담당이라 손대지 않는다.
    def find_fnm():
        if os.name == "nt":
            return None
        p = shutil.which("fnm")
        if p:
            return p
        for cand in ("~/.local/bin/fnm", "~/.fnm/fnm"):
            cp = os.path.expanduser(cand)
            if os.path.isfile(cp):
                return cp
        return None

    fnm_path = find_fnm()

    # path 없는 항목 = 참고 전용(reference-repos 스킬용) — 동기화 대상에서 제외.
    sync_targets = [r for r in repos if r.get("path")]

    print("\n=== sync-repos === (%d개 대상)\n" % len(sync_targets))

    # pull 단계는 레포마다 독립된 네트워크 왕복이라 순차로 돌면 레포 수만큼 지연이 쌓인다
    # (실측: 7개 순차 ~28초). 서로 다른 레포라 충돌 여지가 없어 스레드풀로 동시에 돌린다.
    # 빌드는 CPU/리소스 경합 우려가 있어 병렬 대상에서 제외하고 아래에서 순차 처리한다.
    t0 = time.time()
    if sync_targets:
        with cf.ThreadPoolExecutor(max_workers=min(8, len(sync_targets))) as ex:
            pulled = list(ex.map(lambda r: _pull_one(home, r), sync_targets))
    else:
        pulled = []
    _log("병렬 pull 완료: %d개 레포, %.1fs 소요" % (len(sync_targets), time.time() - t0))

    results = []
    for entry in pulled:
        name = entry["name"]

        if entry["status"] == "skip":
            results.append(entry)
            print("  [-] %-22s %s" % (name, entry["detail"]))
            continue

        if entry["status"] == "error":
            results.append(entry)
            print("  [!] %-22s %s" % (name, entry["detail"]))
            continue

        r, full, changed, dirty = entry["r"], entry["full"], entry["changed"], entry["dirty"]
        should_build = bool(r.get("build")) and not no_build and (changed or build_all)

        if not changed and not should_build:
            entry.update(status="nochange", detail=("변경없음 (로컬 미커밋 있음)" if dirty else "변경없음"))
            results.append(entry)
            print("  [=] %-22s %s" % (name, entry["detail"]))
            continue

        if should_build:
            print("  [~] %-22s 빌드 중: %s" % (name, r["build"]))
            try:
                build_cmd = r["build"]
                run_kwargs = {"shell": True, "cwd": full}
                if fnm_path:  # fnm node 를 PATH 로 끌어와 비대화형 빌드에서도 npm 이 잡히게 한다.
                    build_cmd = 'eval "$(%s env --shell bash)"; %s' % (fnm_path, build_cmd)
                    run_kwargs["executable"] = "/bin/bash"
                b = subprocess.run(build_cmd, **run_kwargs)
                if b.returncode != 0:
                    entry.update(status="builderror", detail="업데이트됨, 빌드 실패")
                else:
                    entry.update(status="built", detail=("업데이트 + 빌드 완료" if changed else "빌드 완료(강제)"))
            except Exception as e:
                entry.update(status="builderror", detail="업데이트됨, 빌드 예외: %s" % e)
        else:
            entry.update(status="updated", detail="업데이트됨(빌드 없음)")

        results.append(entry)
        print("  [v] %-22s %s" % (name, entry["detail"]))

    # ---- 요약 ----
    ok = sum(1 for e in results if e["status"] in ("built", "updated"))
    noch = sum(1 for e in results if e["status"] == "nochange")
    skip = sum(1 for e in results if e["status"] == "skip")
    bad = [e for e in results if e["status"] in ("error", "builderror")]

    print("\n요약: 업데이트 %d / 변경없음 %d / 미클론 %d / 문제 %d" % (ok, noch, skip, len(bad)))
    _write_desktop_report(results, ok, noch, skip, bad)

    if bad:
        print("\n확인 필요:")
        for b in bad:
            print("  - %s: %s" % (b["name"], b["detail"]))
        _notify(
            "sync-repos: 확인 필요 (%d건)" % len(bad),
            "; ".join("%s: %s" % (b["name"], b["detail"]) for b in bad),
        )
        sys.exit(2)

    # [토스트 본문] 변경없음은 건수만(내용이 없으니 이름을 나열해봐야 정보가 안 됨),
    # 업데이트·미클론은 약어 이름을 나열한다(사용자 피드백 2026-08-05 — desc 원문은
    # 길어서 200자 제한에 잘렸고, 미클론은 아예 이름이 안 보여 뭐가 안 잡히는지 몰랐음).
    parts = []
    if ok:
        updated_short = ", ".join(_short_name(e["r"]) for e in results if e["status"] in ("built", "updated"))
        parts.append("업데이트: %s" % updated_short)
    if skip:
        skip_short = ", ".join(_short_name(e["r"]) for e in results if e["status"] == "skip")
        parts.append("미클론: %s" % skip_short)
    if noch:
        parts.append("변경없음 %d" % noch)
    _notify("sync-repos", " / ".join(parts) if parts else "변경사항 없음")
    sys.exit(0)


if __name__ == "__main__":
    # SYNC_REPOS_BOOT_WAITED 가드: 자기업데이트가 os.execv로 재실행해도 --boot-wait 플래그는
    # 그대로 남아있어, 가드가 없으면 재실행마다 또 대기해 실질 지연이 배로 늘어난다
    # (2026-08-03·04 실측: 30s+30s=76~85초 — 사용자가 "1분 넘게 안 된다"고 느낀 원인).
    # execv는 현재 프로세스의 os.environ을 그대로 물려주므로 여기서 세팅한 값이 재실행 후에도 유지된다.
    if "--boot-wait" in sys.argv and os.environ.get("SYNC_REPOS_BOOT_WAITED") != "1":
        _log("boot-wait: 네트워크 대기 시작 (최대 %ds)" % BOOT_WAIT_SECONDS)
        _wait_for_network(BOOT_WAIT_SECONDS)
        os.environ["SYNC_REPOS_BOOT_WAITED"] = "1"
    _migrate_boot_vbs()
    _self_update_and_relaunch()
    try:
        main()
    except SystemExit:
        raise
    except Exception as e:
        _log("예외:\n%s" % traceback.format_exc())
        _notify("sync-repos 실패(예외)", "%s: %s" % (type(e).__name__, e))
        sys.exit(1)
