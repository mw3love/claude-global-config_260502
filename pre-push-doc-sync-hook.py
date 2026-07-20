#!/usr/bin/env python3
"""PreToolUse(Bash) hook: git push 앞에서 doc-sync 사전 검토를 강제한다.

CLAUDE.md 규칙 10의 '사전(메인)' 경로가 모델 기억에만 의존해 죽는 문제를
(실측: 2026-07-12 세션 push 4회 중 사전 doc-sync 0회, 전부 사후 훅이 잡음)
기계 강제로 바꾼다. 규칙 형태론: 내 판단을 통과하지 않는 훅만이 확실히 발화한다.

동작:
- Bash 명령에 git push가 없으면 침묵 통과.
- 센티널(~/.claude/.doc-sync-ready)이 30분 이내면 소비(삭제)하고 통과.
- 없거나 오래됐으면 push를 deny하고 이유에 절차를 적는다:
  doc-sync 실행 → 센티널 touch → push 재시도.

실패는 열림(fail-open): 스크립트 오류·파싱 실패 시 push를 막지 않는다
(디스패처의 `|| true`와 이 파일의 광역 except가 함께 보장).
"""
import json
import re
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
