#!/usr/bin/env python3
"""PreToolUse(Bash) hook: git push 앞에서 doc-sync 사전 검토를 강제한다.

CLAUDE.md 규칙 10의 '사전(메인)' 경로가 모델 기억에만 의존해 죽는 문제를
(실측: 2026-07-12 세션 push 4회 중 사전 doc-sync 0회, 전부 사후 훅이 잡음)
기계 강제로 바꾼다. 규칙 형태론: 내 판단을 통과하지 않는 훅만이 확실히 발화한다.

동작:
- Bash 명령에 git push가 없으면 침묵 통과.
- 필터(2026-08-10 추가): push 예정 범위 + 미커밋 변경을 훑어 아래 중 하나면
  doc-sync 의식 없이 자동 통과 — doc-sync 스킬을 불러도 결론이 100% "변경
  없음"일 게 뻔한 경우이므로 사전에 걸러도 보호 수준이 줄지 않는다.
    a) 문서 아닌 파일 변경이 0개 (코드가 안 바뀌었으니 동기화할 게 없음)
    b) 저장소에 동기화 후보 문서 자체가 없음(CLAUDE.md/docs/**/*.md/루트 *.md/
       .doc-sync.json 전부 없음) — 있어도 갱신할 대상이 없음
  범위를 못 구하면(신규 repo·이상한 cwd 등) 안전 쪽으로 폴백해 기존 로직대로
  진행한다(자동 통과하지 않음). post-push 훅(doc-sync-hook.py)의 "비-문서
  변경 0개면 침묵"과 같은 필터를 사전 쪽에도 대칭으로 이식한 것.
- 필터를 통과하지 못했으면(=진짜 검토가 필요하면) 센티널(~/.claude/.doc-sync-ready)이
  30분 이내인지 확인 — 있으면 소비(삭제)하고 통과.
- 없거나 오래됐으면 push를 deny하고 이유에 절차를 적는다:
  doc-sync 실행 → 센티널 touch → push 재시도.

실패는 열림(fail-open): 스크립트 오류·파싱 실패 시 push를 막지 않는다
(디스패처의 `|| true`와 이 파일의 광역 except가 함께 보장).
"""
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

SENTINEL = Path.home() / ".claude" / ".doc-sync-ready"
MAX_AGE_SECONDS = 30 * 60

# 따옴표 안(커밋 메시지 등)의 문자열을 제거한 뒤, &&·;·|·개행으로 세그먼트를
# 나누고 공백 토큰 단위로 git·push를 찾는다. \b 기반 정규식은 "pre-push-doc-
# sync-hook.py"처럼 하이픈으로 이어진 파일명 안의 "push"까지 단어경계로 오인해
# 매칭했다(실측: git add 커맨드가 이 훅 자신 때문에 deny됨) — 토큰 단위 비교로 교체.
_QUOTED = re.compile(r'"[^"]*"|\'[^\']*\'')


def command_has_git_push(command: str) -> bool:
    stripped = _QUOTED.sub("", command)
    for segment in re.split(r"&&|\|\||;|\||\n", stripped):
        tokens = segment.split()
        try:
            git_at = tokens.index("git")
        except ValueError:
            continue
        if "push" in tokens[git_at + 1:]:
            return True
    return False


def _git(cwd: str, *args: str):
    """returncode==0이면 stdout, 아니면 None (실패를 '변경 없음'과 구분)."""
    try:
        r = subprocess.run(
            ["git", "-C", cwd, *args],
            capture_output=True, text=True, encoding="utf-8", timeout=10,
        )
        if r.returncode == 0:
            return r.stdout
    except Exception:
        pass
    return None


def _is_doc(path: str) -> bool:
    return bool(
        re.search(r"\.(md|markdown|txt|rst)$", path, re.IGNORECASE)
        or re.search(r"(^|/)LICENSE$", path)
        or re.search(r"(^|/)CHANGELOG(\.md)?$", path, re.IGNORECASE)
    )


def _pushed_and_uncommitted_files(cwd: str):
    """push 예정 범위(unpushed) + 미커밋 변경 파일 목록. 못 구하면 None."""
    diff_out = _git(cwd, "diff", "--name-only", "@{u}...HEAD")
    if diff_out is None:
        diff_out = _git(cwd, "diff", "--name-only", "origin/main...HEAD")
    if diff_out is None:
        diff_out = _git(cwd, "diff", "--name-only", "origin/master...HEAD")
    if diff_out is None:
        return None  # 범위를 전혀 못 구함 → 안전 쪽 폴백

    files = [f for f in diff_out.splitlines() if f.strip()]

    status_out = _git(cwd, "status", "--porcelain") or ""
    for line in status_out.splitlines():
        if len(line) <= 3:
            continue
        f = line[3:].strip()
        if " -> " in f:  # 이름변경: "old -> new"
            f = f.split(" -> ", 1)[1].strip()
        if f:
            files.append(f)

    return files


def _has_doc_candidates(cwd: str) -> bool:
    p = Path(cwd)
    if (p / "CLAUDE.md").exists() or (p / ".doc-sync.json").exists():
        return True
    try:
        if any(p.glob("*.md")):
            return True
    except OSError:
        pass
    docs_dir = p / "docs"
    if docs_dir.is_dir():
        try:
            if any(docs_dir.rglob("*.md")):
                return True
        except OSError:
            pass
    return False


def should_skip_enforcement(cwd: str) -> bool:
    """True면 doc-sync 의식 없이 자동 통과해도 안전(동기화할 게 구조적으로 없음)."""
    if not cwd or not os.path.isdir(cwd):
        return False  # cwd 불명 → 안전 쪽 폴백(기존 로직대로 진행)

    files = _pushed_and_uncommitted_files(cwd)
    if files is None:
        return False  # 범위 판단 불가 → 안전 쪽 폴백

    non_doc = [f for f in files if not _is_doc(f)]
    if not non_doc:
        return True  # 코드 변경 자체가 없음

    return not _has_doc_candidates(cwd)  # 문서 후보가 아예 없으면 스킵


def main() -> None:
    try:
        data = json.load(sys.stdin)
    except Exception:
        return
    if data.get("tool_name") != "Bash":
        return
    command = (data.get("tool_input") or {}).get("command", "")
    if not command_has_git_push(command):
        return

    cwd = str(data.get("cwd") or os.getcwd())
    if should_skip_enforcement(cwd):
        return

    try:
        age = time.time() - SENTINEL.stat().st_mtime
        if age < MAX_AGE_SECONDS:
            SENTINEL.unlink()  # 1회용 — push 한 번당 doc-sync 확인 한 번
            return
    except OSError:
        pass  # 센티널 없음/접근 불가 → deny로 진행

    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": (
                "[pre-push doc-sync] push 전 doc-sync 사전 검토(규칙 10)가 아직 확인되지 않았다. "
                "절차: 1) doc-sync 스킬을 호출해 문서 동기화를 검토하고(변경이 있으면 같은 커밋에 포함) "
                "2) `touch ~/.claude/.doc-sync-ready`를 별도 Bash 호출로 실행한 뒤 "
                "3) 그 다음 Bash 호출로 push를 재시도한다. "
                "⚠ touch와 push를 한 명령에 && 로 묶지 말 것 — 이 훅은 PreToolUse라 명령이 "
                "실행되기 전에 센티널을 검사하므로, 묶으면 touch가 실행되기도 전에 거부된다. "
                "이번 대화에서 doc-sync 사전 검토를 이미 마쳤다면 2)~3)만 하면 된다."
            ),
        }
    }))  # ensure_ascii 기본값(True) 유지 — Windows 파이프의 cp949 인코딩에도 JSON이 깨지지 않게 ASCII 이스케이프로 내보낸다


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass  # fail-open
