#!/usr/bin/env python3
"""~/.cursor/hooks.json 과 ~/.cursor/hooks 를 repo cursor-hooks/ 에 연결.

Cursor는 ~/.claude 훅을 자동으로 읽지 않는다. git pull 후 post-merge가 이 스크립트를
호출해 문짝(~/.cursor)에서 노트(이 레포)로 전선을 잇는다.
이미 올바른 링크면 무동작. 사용자가 만든 실파일이 있으면 덮어쓰지 않는다.

출력: STATUS|메시지  (STATUS = OK|NEW|SKIP|TODO|FAIL)
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def _same(link: Path, target: Path) -> bool:
    try:
        if not link.exists() and not link.is_symlink():
            return False
        return link.resolve() == target.resolve()
    except OSError:
        return False


def _link(link: Path, target: Path, *, is_dir: bool) -> str:
    if _same(link, target):
        return "OK"

    if link.exists() or link.is_symlink():
        if link.is_symlink():
            link.unlink()
        elif is_dir and link.is_dir() and not any(link.iterdir()):
            link.rmdir()
        else:
            return "TODO"

    link.parent.mkdir(parents=True, exist_ok=True)
    try:
        os.symlink(str(target), str(link), target_is_directory=is_dir)
        return "NEW"
    except OSError:
        if os.name == "nt" and is_dir:
            r = subprocess.run(
                ["cmd", "/c", "mklink", "/J", str(link), str(target)],
                capture_output=True,
                text=True,
            )
            return "NEW" if r.returncode == 0 else "FAIL"
        return "FAIL"


def main() -> int:
    home = Path.home()
    src_json = home / ".claude" / "cursor-hooks" / "hooks.json"
    src_dir = home / ".claude" / "cursor-hooks" / "hooks"
    dst_json = home / ".cursor" / "hooks.json"
    dst_dir = home / ".cursor" / "hooks"

    if not src_json.is_file():
        print("SKIP|cursor-hooks/hooks.json 없음")
        return 0

    src_dir.mkdir(parents=True, exist_ok=True)

    st_json = _link(dst_json, src_json, is_dir=False)
    st_dir = _link(dst_dir, src_dir, is_dir=True)

    if "FAIL" in (st_json, st_dir):
        print("FAIL|~/.cursor 훅 링크 실패 (Windows면 개발자 모드 또는 관리자 권한 필요할 수 있음)")
        return 1
    if "TODO" in (st_json, st_dir):
        print(
            "TODO|~/.cursor/hooks.json 또는 hooks 가 이미 있어 덮어쓰지 않음. "
            "직접 확인: " + str(dst_json)
        )
        return 0
    if st_json == "NEW" or st_dir == "NEW":
        print("NEW|Cursor 훅 링크 생성: ~/.cursor/hooks.json -> ~/.claude/cursor-hooks/")
        return 0
    print("OK|Cursor 훅 링크 이미 연결됨")
    return 0


if __name__ == "__main__":
    sys.exit(main())
