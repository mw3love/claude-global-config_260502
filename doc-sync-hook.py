#!/usr/bin/env python3
# PostToolUse hook: Bash 도구로 `git push`가 성공하면 doc-sync 스킬 호출을 지시한다.
# doc-sync-hook.ps1 의 크로스플랫폼(Windows/macOS/Linux) 포팅. 로직은 .ps1 과 동일하게 유지.
# - PostToolUse 는 성공한 tool 호출에만 발화하므로 success 체크 불필요
# - tool result 키 이름이 공식 문서에 미명시이므로 raw stdin 텍스트에서 push 결과 패턴을 추출
# - 푸쉬된 범위에 비-문서 코드 변경이 있을 때만 스킬 호출 지시
import sys, json, re, subprocess


def exit_silent():
    sys.exit(0)


def git(cwd, *args):
    try:
        r = subprocess.run(["git", "-C", cwd, *args], capture_output=True, text=True, encoding="utf-8")
        if r.returncode == 0 and r.stdout:
            return r.stdout
    except Exception:
        pass
    return ""


def main():
    raw = sys.stdin.read()
    if not raw or not raw.strip():
        exit_silent()

    try:
        payload = json.loads(raw)
    except Exception:
        exit_silent()

    if payload.get("tool_name") != "Bash":
        exit_silent()

    cmd = str((payload.get("tool_input") or {}).get("command") or "")
    if not cmd.strip():
        exit_silent()

    # git push 토큰 매칭 (.ps1 과 동일 정규식)
    if not re.search(r"\bgit(\s+--?[^\s=]+(=\S+)?)*\s+push(?=\s|$|[;|&\)])", cmd):
        exit_silent()
    if re.search(r"\bgit\s+push\b.*(--help|\s-h(\s|$))", cmd):
        exit_silent()
    # 자기-트리거 방지: hook 스크립트 자신을 호출하는 명령은 스킵 (.py/.ps1 둘 다)
    if re.search(r"doc-sync-hook\.(ps1|py)", cmd):
        exit_silent()

    # 푸쉬 결과 패턴 추출. raw 는 JSON 이스케이프된 \n 또는 실제 개행을 포함할 수 있음.
    new_branch = False
    forced = False
    ranges = []

    for ln in re.split(r"\\r\\n|\\n|\r\n|\r|\n", raw):
        m = re.search(r"\s([0-9a-f]{7,40}\.\.[0-9a-f]{7,40})\s+\S+\s+->\s+(\S+)", ln)
        if m:
            ranges.append(m.group(1))
            continue
        m = re.search(r"\*\s+\[new branch\]\s+\S+\s+->\s+(\S+)", ln)
        if m:
            new_branch = True
            ranges.append("__NEWBRANCH__:" + m.group(1))
            continue
        m = re.search(r"\+\s+([0-9a-f]{7,40}\.\.\.[0-9a-f]{7,40})\s+\S+\s+->\s+(\S+)", ln)
        if m:
            forced = True
            ranges.append("__FORCED__:" + m.group(1))

    if not ranges:
        exit_silent()  # up-to-date 등 변경 없음

    import os
    cwd = str(payload.get("cwd") or "")
    if not cwd.strip() or not os.path.isdir(cwd):
        cwd = os.getcwd()

    # 푸쉬된 범위의 변경 파일 수집
    changed = []
    for r in ranges:
        if r.startswith("__NEWBRANCH__:"):
            out = git(cwd, "log", "-50", "--name-only", "--pretty=format:", "HEAD")
            changed += [x for x in out.splitlines() if x]
            continue
        elif r.startswith("__FORCED__:"):
            diff_range = r[len("__FORCED__:"):].replace("...", "..")
        else:
            diff_range = r
        out = git(cwd, "diff", "--name-only", diff_range)
        changed += [x for x in out.splitlines() if x]

    unique = []
    seen = set()
    for f in changed:
        f = f.strip()
        if f and f not in seen:
            seen.add(f)
            unique.append(f)
    if not unique:
        exit_silent()

    # 비-문서 코드 변경이 1개라도 있어야 발화
    def is_doc(f):
        return (re.search(r"\.(md|markdown|txt|rst)$", f) or
                re.search(r"(^|/)LICENSE$", f) or
                re.search(r"(^|/)CHANGELOG(\.md)?$", f))

    non_doc = [f for f in unique if not is_doc(f)]
    if not non_doc:
        exit_silent()

    def label(r):
        if r.startswith("__NEWBRANCH__:"):
            return "[new branch] " + r[len("__NEWBRANCH__:"):]
        if r.startswith("__FORCED__:"):
            return "[forced] " + r[len("__FORCED__:"):]
        return r

    range_summary = ", ".join(label(r) for r in ranges)
    file_sample = "\n  - ".join(unique[:30])

    context = (
        "[doc-sync hook] `git push`가 방금 성공했습니다. doc-sync 스킬을 즉시 호출해 "
        "푸쉬된 변경사항이 핵심 문서(CLAUDE.md, 계획/설계/스펙 문서 등)에 반영되었는지 검토하세요.\n\n"
        "푸쉬 정보\n"
        "- 작업 폴더: %s\n"
        "- 푸쉬 범위: %s\n"
        "- 새 브랜치: %s / force: %s\n"
        "- 변경 파일(%d개):\n"
        "  - %s\n\n"
        "호출 방법: Skill 도구로 'doc-sync' 스킬을 인수 없이 호출하세요."
        % (cwd, range_summary, new_branch, forced, len(unique), file_sample)
    )

    output = json.dumps({
        "suppressOutput": True,
        "hookSpecificOutput": {
            "hookEventName": "PostToolUse",
            "additionalContext": context,
        },
    }, ensure_ascii=True)

    sys.stdout.write(output + "\n")
    sys.exit(0)


try:
    main()
except Exception as e:
    sys.stderr.write("[doc-sync-hook] error: %s\n" % e)
    sys.exit(0)
