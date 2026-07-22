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
import sys, os, json, subprocess, shutil, datetime, traceback

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

LOG_DIR = os.path.join(os.path.expanduser("~"), "AppData", "Local", "sync-repos") if os.name == "nt" else None
LOG_PATH = os.path.join(LOG_DIR, "startup.log") if LOG_DIR else None


def git(cwd, *args):
    return subprocess.run(["git", "-C", cwd, *args], capture_output=True, text=True, encoding="utf-8")


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
    bash = shutil.which("bash") or "bash"
    msg = "%s\n%s" % (title, body[:200])
    # persist: 로그온 자동실행처럼 사람이 안 지켜보는 저빈도 호출이라, 중앙 팝업을 놓치면
    # 대안이 없다 — 우하단 토스트도 같이 띄워 알림센터에 남긴다(toast.sh -Persist, Windows만
    # 의미 있음). 일반 응답완료 알림(고빈도)은 이 플래그를 안 쓴다.
    try:
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

    results = []
    for r in sync_targets:
        rel = r.get("path", "")
        full = os.path.join(home, rel.replace("/", os.sep))
        name = r.get("desc") or rel
        entry = {"name": name, "status": "", "detail": ""}

        if not os.path.isdir(os.path.join(full, ".git")):
            entry.update(status="skip", detail="이 PC에 없음(미클론)")
            results.append(entry)
            print("  [-] %-22s %s" % (name, entry["detail"]))
            continue

        dirty = git(full, "status", "--porcelain").stdout.strip()
        before = git(full, "rev-parse", "HEAD").stdout.strip()

        pull = git(full, "pull", "--ff-only")
        if pull.returncode != 0:
            last = (pull.stderr or pull.stdout).strip().splitlines()
            detail = "pull 실패 — " + (" ".join(last[-1].split()) if last else "")
            entry.update(status="error", detail=detail)
            results.append(entry)
            print("  [!] %-22s %s" % (name, entry["detail"]))
            continue

        after = git(full, "rev-parse", "HEAD").stdout.strip()
        changed = before != after

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

    if bad:
        print("\n확인 필요:")
        for b in bad:
            print("  - %s: %s" % (b["name"], b["detail"]))
        _notify(
            "sync-repos: 확인 필요 (%d건)" % len(bad),
            "; ".join("%s: %s" % (b["name"], b["detail"]) for b in bad),
        )
        sys.exit(2)

    if ok:
        _notify("sync-repos 완료", "%d개 업데이트, %d개 변경없음, %d개 미클론" % (ok, noch, skip))
    else:
        _notify("sync-repos: 변경없음", "%d개 전부 최신 상태(미클론 %d)" % (noch, skip))
    sys.exit(0)


if __name__ == "__main__":
    _self_update_and_relaunch()
    try:
        main()
    except SystemExit:
        raise
    except Exception as e:
        _log("예외:\n%s" % traceback.format_exc())
        _notify("sync-repos 실패(예외)", "%s: %s" % (type(e).__name__, e))
        sys.exit(1)
