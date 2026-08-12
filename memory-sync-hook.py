#!/usr/bin/env python3
# SessionEnd hook — ~/.claude/memory/ 하위에 쌓인 자동 메모리 기록(autoMemoryDirectory,
# session-memory-hook.py 참조)을 세션 종료 시 자동으로 commit+push한다.
#
# 문제: 메모리 쓰기는 어느 프로젝트에서 세션을 열든 ~/.claude repo에 떨어지는데, 그 repo의
# git 커밋/푸쉬는 사용자가 ~/.claude를 직접 열 때만 일어났다 — 여러 PC로 옮겨다니며 작업하는
# 워크플로에서 전역 메모리가 미커밋 상태로 방치되고, 이게 다음 sync-repos pull(--ff-only)의
# 실패 원인이 되기도 했다(로컬 dirty tree가 원격의 새 커밋과 충돌). 2026-08-12 사용자 지적.
#
# sync-repos의 pull 루프와는 완전히 무관하게 동작한다(session-memory-hook.py의 2026-08-05
# 결정 참조 — 그 둘을 묶었다가 불안정해진 전례가 있어 재결합하지 않는다).
#
# 스코프는 memory/ 하위뿐이다 — CLAUDE.md·skills·훅·settings.json 같은 행동/설정 파일은
# 여전히 사용자 승인 후 수동 커밋(전역 규칙 12, 자기수정 방지).
#
# SessionEnd는 동기 실행(세션 종료를 블록)이므로 빠르게 끝나야 한다 — 변경 없으면 git status
# 한 번으로 끝나고(가장 흔한 경로), 실패해도 세션 종료 자체를 막지 않게 전부 try/except.
import sys, os, json, subprocess, datetime

CLAUDE_DIR = os.path.join(os.path.expanduser("~"), ".claude")
LOG_PATH = os.path.join(CLAUDE_DIR, "memory-sync-hook.log")


def _log(line):
    try:
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write("%s  %s\n" % (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), line))
    except Exception:
        pass


def _run(args, timeout=10):
    try:
        r = subprocess.run(["git", "-C", CLAUDE_DIR] + args, capture_output=True,
                            text=True, encoding="utf-8", timeout=timeout)
        return r.returncode, (r.stdout or "").strip(), (r.stderr or "").strip()
    except Exception as e:
        return 1, "", str(e)


def _notify_failure(body):
    # 실패했을 때만 알림 — 성공은 조용히(사용자가 방금 세션을 끝낸 시점이라 매번 띄우면
    # 오히려 소음, feedback_notification_design.md의 "항상 알림"은 사람이 안 지켜보는
    # 저빈도 무인 자동화용 원칙이라 여기 그대로 적용하지 않음). 기존 toast 디스패처 재사용.
    try:
        msg = "전역 메모리 push 실패\n%s" % body[:200]
        if sys.platform == "win32":
            ps1 = os.path.join(CLAUDE_DIR, "toast.ps1")
            if os.path.isfile(ps1):
                subprocess.Popen(["powershell.exe", "-NoProfile", "-Sta",
                                  "-ExecutionPolicy", "Bypass", "-File", ps1,
                                  "-Message", msg, "-Persist"],
                                  stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            dispatcher = os.path.join(CLAUDE_DIR, "toast.sh")
            if os.path.isfile(dispatcher):
                subprocess.Popen(["bash", dispatcher, msg],
                                  stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass


def main():
    raw = sys.stdin.read()
    try:
        data = json.loads(raw) if raw.strip() else {}
    except Exception:
        data = {}
    src_cwd = data.get("cwd") or ""
    leaf = os.path.basename(str(src_cwd).rstrip("\\/")) or "unknown"

    if not os.path.isdir(os.path.join(CLAUDE_DIR, ".git")):
        return

    code, out, err = _run(["status", "--porcelain", "--", "memory/"])
    if code != 0:
        _log("status 실패(무시): %s" % err)
        return
    if not out:
        return  # 변경 없음 — 가장 흔한 경로, 조용히 종료

    code, _, err = _run(["add", "--", "memory/"])
    if code != 0:
        _log("add 실패: %s" % err)
        return

    msg = "auto(memory): %s 세션 종료 시 동기화" % leaf
    code, _, err = _run(["commit", "-m", msg])
    if code != 0:
        _log("commit 실패: %s" % err)
        return
    _log("commit 완료: %s" % msg)

    code, _, err = _run(["push"], timeout=20)
    if code != 0:
        _log("push 실패(로컬 커밋은 남아있음, 다음 sync-repos에서 재시도됨): %s" % err)
        _notify_failure(err or "원인 미상")
        return
    _log("push 완료")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        _log("예외(무시): %s: %s" % (type(e).__name__, e))
