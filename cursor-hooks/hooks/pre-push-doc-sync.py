#!/usr/bin/env python3
"""Cursor 문지기 — git push 앞에서 Claude와 같은 doc-sync 센티널을 강제한다.

논리(push인지, 문서 후보, .doc-sync-ready)는 ~/.claude/pre-push-doc-sync-hook.py 를 재사용한다.
입구만 Cursor JSON이다: beforeShellExecution({command,cwd}) 또는 preToolUse(Shell).

fail-open: 파싱·임포트·예외 시 아무것도 안 찍고 종료 → Cursor가 명령을 통과시킨다.
"""
from __future__ import annotations

import importlib.util
import json
import os
import sys
from pathlib import Path

DENY_AGENT = (
    "[pre-push doc-sync] push 전 doc-sync 사전 검토가 아직 확인되지 않았다. "
    "절차: 1) doc-sync 스킬을 호출해 문서 동기화를 검토하고(변경이 있으면 같은 커밋에 포함) "
    "2) `touch ~/.claude/.doc-sync-ready`를 별도 셸 호출로 실행한 뒤 "
    "3) 그 다음 셸 호출로 push를 재시도한다. "
    "touch와 push를 한 명령에 && 로 묶지 말 것 — 이 훅은 명령 실행 전에 센티널을 검사하므로, "
    "묶으면 touch가 실행되기도 전에 거부된다. "
    "이번 대화에서 doc-sync 사전 검토를 이미 마쳤다면 2)~3)만 하면 된다."
)
DENY_USER = "git push가 막힘 — 먼저 doc-sync 검토 후 touch ~/.claude/.doc-sync-ready"


def _load_claude_prepush():
    path = Path.home() / ".claude" / "pre-push-doc-sync-hook.py"
    spec = importlib.util.spec_from_file_location("claude_prepush", path)
    if spec is None or spec.loader is None:
        raise ImportError("pre-push-doc-sync-hook.py 없음")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _extract_command_cwd(data: dict) -> tuple[str, str]:
    tool = data.get("tool_name")
    if tool:
        if tool != "Shell":
            return "", str(data.get("cwd") or os.getcwd())
        inp = data.get("tool_input") or {}
        cmd = inp.get("command") or ""
        cwd = data.get("cwd") or inp.get("working_directory") or os.getcwd()
        return str(cmd), str(cwd)
    return str(data.get("command") or ""), str(data.get("cwd") or os.getcwd())


def _deny() -> None:
    print(
        json.dumps(
            {
                "permission": "deny",
                "user_message": DENY_USER,
                "agent_message": DENY_AGENT,
            },
            ensure_ascii=True,
        )
    )


def _allow() -> None:
    print(json.dumps({"permission": "allow"}))


def main() -> None:
    raw = sys.stdin.read()
    if not raw or not raw.strip():
        return
    try:
        data = json.loads(raw)
    except Exception:
        return

    command, cwd = _extract_command_cwd(data)
    if not command:
        _allow()
        return

    mod = _load_claude_prepush()
    if not mod.command_has_git_push(command):
        _allow()
        return
    if mod.should_skip_enforcement(cwd):
        _allow()
        return

    if mod.sentinel_allows():
        _allow()
        return

    _deny()


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
