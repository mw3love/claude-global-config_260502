#!/usr/bin/env python3
# 여러 PC에서 쓰는 git 프로젝트들을 한 번에 git pull(+빌드)한다.
# sync-repos.ps1 의 크로스플랫폼(Windows/macOS/Linux) 포팅. 동작은 .ps1 과 동일.
#   ~/.claude/repos.json 명단을 읽어 각 repo 를 fast-forward(--ff-only) pull.
#   경로는 홈(~) 기준 상대경로 -> PC마다 사용자명이 달라도 동작.
#   pull 로 실제 변경이 생긴 repo 만 build 명령을 실행.
# 사용:  python3 ~/.claude/sync-repos.py [--build-all] [--no-build]
import sys, os, json, subprocess

# 콘솔 코드페이지와 무관하게 한글 출력 안전(Windows cp949 깨짐 방지). macOS/Linux 는 원래 UTF-8.
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

build_all = "--build-all" in sys.argv or "-BuildAll" in sys.argv
no_build = "--no-build" in sys.argv or "-NoBuild" in sys.argv

home = os.path.expanduser("~")
manifest = os.path.join(home, ".claude", "repos.json")

if not os.path.isfile(manifest):
    print("[X] 명단 파일 없음: %s" % manifest)
    sys.exit(1)

try:
    with open(manifest, encoding="utf-8") as f:
        repos = json.load(f)
except Exception as e:
    print("[X] repos.json 파싱 실패: %s" % e)
    sys.exit(1)


def git(cwd, *args):
    return subprocess.run(["git", "-C", cwd, *args], capture_output=True, text=True, encoding="utf-8")


print("\n=== sync-repos === (%d개 대상)\n" % len(repos))

results = []
for r in repos:
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
            b = subprocess.run(r["build"], shell=True, cwd=full)
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
    sys.exit(2)

sys.exit(0)
