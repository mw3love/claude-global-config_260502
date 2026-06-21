#!/usr/bin/env bash
# Cross-platform Claude Code 알림 디스패처 (toast.ps1 의 OS 분기 래퍼).
#   Windows  -> toast.ps1 (Windows 토스트 + Telegram, 기존 동작 그대로)
#   macOS    -> osascript display notification + (옵션) Telegram
#   Linux    -> notify-send + (옵션) Telegram
# settings.json 의 훅에서 `bash -c '~/.claude/toast.sh "<메시지>"'` 로 호출된다.
msg="${1:-Response complete}"
msg="${msg//\"/}"                 # osascript/JSON 안전: 큰따옴표 제거 (메시지는 고정 문자열)
claude_dir="$HOME/.claude"

send_telegram() {
  local cfg="$claude_dir/telegram.json"
  [ -f "$cfg" ] || return 0
  local py; for c in python3 python; do command -v "$c" >/dev/null 2>&1 && { py="$c"; break; }; done
  [ -n "$py" ] || return 0
  "$py" - "$cfg" "$1" <<'PYEOF' >/dev/null 2>&1
import json, sys, urllib.request, urllib.parse, platform
cfg, msg = sys.argv[1], sys.argv[2]
try:
    d = json.load(open(cfg, encoding="utf-8"))
    body = urllib.parse.urlencode({"chat_id": d["chat_id"], "text": "[%s] Claude Code: %s" % (platform.node(), msg)}).encode()
    urllib.request.urlopen("https://api.telegram.org/bot%s/sendMessage" % d["bot_token"], data=body, timeout=5).read()
except Exception:
    pass
PYEOF
}

case "$(uname -s)" in
  MINGW*|MSYS*|CYGWIN*)
    # Windows: 기존 toast.ps1 이 토스트 + Telegram 을 모두 처리 (변경 없음)
    powershell.exe -NoProfile -Sta -ExecutionPolicy Bypass -File "$claude_dir/toast.ps1" -Message "$msg" >/dev/null 2>&1 &
    ;;
  Darwin)
    /usr/bin/osascript -e "display notification \"$msg\" with title \"Claude Code\"" >/dev/null 2>&1
    send_telegram "$msg" &
    ;;
  *)
    command -v notify-send >/dev/null 2>&1 && notify-send "Claude Code" "$msg" >/dev/null 2>&1
    send_telegram "$msg" &
    ;;
esac
exit 0
