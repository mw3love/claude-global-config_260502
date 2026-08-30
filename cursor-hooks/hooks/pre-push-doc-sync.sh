#!/usr/bin/env bash
# Cursor 훅 환경은 PATH가 짧을 수 있다. python을 못 찾으면 fail-open으로 push가 그냥 나간다.
export PATH="/usr/bin:/bin:/usr/local/bin:/opt/homebrew/bin:$PATH"
LOG="${HOME}/.claude/cursor-hooks/pre-push-invoke.log"
{
  date "+%Y-%m-%d %H:%M:%S"
  echo "cwd=$(pwd)"
  echo "path=$PATH"
  command -v python3 || true
  command -v python || true
} >>"$LOG" 2>&1
if command -v python3 >/dev/null 2>&1; then
  exec python3 "$(dirname "$0")/pre-push-doc-sync.py"
fi
if command -v python >/dev/null 2>&1; then
  exec python "$(dirname "$0")/pre-push-doc-sync.py"
fi
echo "NO PYTHON" >>"$LOG"
exit 0
