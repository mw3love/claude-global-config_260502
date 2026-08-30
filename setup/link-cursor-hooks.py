#!/usr/bin/env python3
"""~/.cursor/hooks.json 과 ~/.cursor/hooks 를 repo cursor-hooks/ 에 연결.

Cursor는 ~/.claude 훅을 자동으로 읽지 않는 줄 알았으나, 실제로는
~/.claude/settings.json 훅도 돌린다. 그래도 Cursor 규격 훅(beforeShellExecution)은
~/.cursor/hooks.json 이 필요하다. git pull 후 post-merge가 이 스크립트를 호출한다.

hooks.json 은 심볼릭 링크로 두지 않는다. 작업공간이 ~/.cursor 이면 Cursor가
'workspace root 아래 심볼릭 링크'를 거부한다(실측 로그). 내용은 원본을 복사한다.
hooks/ 스크립트 폴더는 링크(또는 Windows 정션)로 둔다.

이미 올바른 연결이면 원본만 다시 복사. 사용자가 만든 다른 실파일이 있으면 덮어쓰지 않는다.

출력: STATUS|메시지  (STATUS = OK|NEW|SKIP|TODO|FAIL)
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

_OURS_MARKER = "pre-push-doc-sync"


def _same(link: Path, target: Path) -> bool:
    try:
        if not link.exists() and not link.is_symlink():
            return False
        return link.resolve() == target.resolve()
    except OSError:
        return False


def _is_ours_json(path: Path) -> bool:
    try:
        return _OURS_MARKER in path.read_text(encoding="utf-8")
    except OSError:
        return False


def _copy_json(dst: Path, src: Path) -> str:
    """hooks.json 은 복사본. 심볼릭 링크면 끊고 실파일로 바꾼다."""
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.is_symlink():
        dst.unlink()
        shutil.copy2(src, dst)
        return "NEW"
    if not dst.exists():
        shutil.copy2(src, dst)
        return "NEW"
    if not dst.is_file():
        return "TODO"
    if not _is_ours_json(dst) and dst.read_bytes() != src.read_bytes():
        return "TODO"
    if dst.read_bytes() == src.read_bytes():
        return "OK"
    shutil.copy2(src, dst)
    return "NEW"


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

    st_json = _copy_json(dst_json, src_json)
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
        print("NEW|Cursor 훅 연결: ~/.cursor/hooks.json 복사 + hooks/ 링크")
        return 0
    print("OK|Cursor 훅 이미 연결됨")
    return 0


if __name__ == "__main__":
    sys.exit(main())
