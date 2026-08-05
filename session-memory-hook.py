#!/usr/bin/env python3
# SessionStart hook — 지금 여는 프로젝트가 repos.json에 등록된 레포면, 그 프로젝트의
# auto-memory 저장 위치를 ~/.claude/memory/projects/<이름>으로 돌려놓는다(autoMemoryDirectory
# 설정, 공식 지원 — OS junction/symlink 불필요). 그 폴더는 ~/.claude 레포 안이라 이미 있는
# git commit/push 흐름을 그대로 타고 여러 PC로 넘어간다(사용자 피드백 2026-08-05:
# sync-repos의 레포별 pull에 얹으면 미클론·git 에러 때문에 불안정해짐 — 그래서 이 훅은
# 그 루프와 완전히 무관하게, cwd 하나만 보고 독립적으로 동작한다).
#
# 매 세션 시작마다 불리지만 멱등(idempotent) — 이미 올바른 값이면 파일을 건드리지 않는다.
# 실패해도 세션 시작을 막지 않게 전체를 try/except로 감싼다(SessionStart는 원래 논블로킹).
import sys, os, json, subprocess, datetime

LOG_PATH = os.path.join(os.path.expanduser("~"), "AppData", "Local", "sync-repos", "session-memory-hook.log") \
    if os.name == "nt" else os.path.join(os.path.expanduser("~"), ".claude", "session-memory-hook.log")


def _log(line):
    try:
        os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write("%s  %s\n" % (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), line))
    except Exception:
        pass


def _git_root(cwd):
    try:
        r = subprocess.run(["git", "-C", cwd, "rev-parse", "--show-toplevel"],
                            capture_output=True, text=True, encoding="utf-8", timeout=5)
        if r.returncode != 0:
            return None
        return r.stdout.strip()
    except Exception:
        return None


def main():
    raw = sys.stdin.read()
    data = json.loads(raw) if raw.strip() else {}
    cwd = data.get("cwd") or os.getcwd()

    home = os.path.expanduser("~")
    root = _git_root(cwd)
    if not root:
        return  # git 레포가 아니면 이 훅은 할 일이 없다

    # 경로 비교는 os.path.realpath로 대소문자/슬래시 차이를 흡수(Windows 실측 필요 없이 안전)
    root_norm = os.path.realpath(root)
    home_norm = os.path.realpath(home)

    manifest = os.path.join(home, ".claude", "repos.json")
    if not os.path.isfile(manifest):
        return
    with open(manifest, encoding="utf-8") as f:
        repos = json.load(f)

    matched = None
    for r in repos:
        rel = r.get("path")
        if not rel:
            continue
        candidate = os.path.realpath(os.path.join(home_norm, rel.replace("/", os.sep)))
        if candidate == root_norm:
            matched = r
            break

    if not matched:
        return  # repos.json에 없는 프로젝트 — 손대지 않는다

    # .claude 자신은 memory/projects/<이름> 서브폴더가 아니라 memory/ 루트를 그대로 쓴다
    # (이미 memory/MEMORY.md 등 기존 파일이 거기 있음 — 과거엔 post-merge hook의 junction이
    # 이 역할을 했는데, 그 방식은 비공식 해시 알고리즘에 의존해 버전업 시 깨질 위험이 있어
    # 이 hook과 같은 공식 autoMemoryDirectory 방식으로 통일한다. junction 자체는 안전하게
    # 남겨둠 — 두 메커니즘이 같은 목적지를 가리켜도 충돌 없음, 2026-08-05).
    if matched["path"] == ".claude":
        target_dir = os.path.join(home, ".claude", "memory")
        target_value = "~/.claude/memory"
    else:
        name = os.path.basename(matched["path"].rstrip("/"))
        target_dir = os.path.join(home, ".claude", "memory", "projects", name)
        target_value = "~/.claude/memory/projects/%s" % name
    os.makedirs(target_dir, exist_ok=True)

    settings_dir = os.path.join(root, ".claude")
    settings_path = os.path.join(settings_dir, "settings.local.json")
    os.makedirs(settings_dir, exist_ok=True)

    existing = {}
    if os.path.isfile(settings_path):
        try:
            with open(settings_path, encoding="utf-8") as f:
                existing = json.load(f)
        except Exception:
            existing = {}

    if existing.get("autoMemoryDirectory") == target_value:
        return  # 이미 올바르게 설정됨 — 건드리지 않음(멱등)

    existing["autoMemoryDirectory"] = target_value
    with open(settings_path, "w", encoding="utf-8") as f:
        json.dump(existing, f, ensure_ascii=False, indent=2)
        f.write("\n")
    _log("설정: %s -> autoMemoryDirectory=%s" % (matched.get("desc") or name, target_value))


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        _log("예외(무시): %s: %s" % (type(e).__name__, e))
