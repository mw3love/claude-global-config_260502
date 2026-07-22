#!/usr/bin/env bash
# Cross-platform Claude Code 알림 디스패처 (toast.ps1 의 OS 분기 래퍼).
#   Windows  -> toast.ps1 (중앙 팝업+알림음 기본, 2번째 인자가 "persist"면 우하단 토스트도 추가)
#   macOS    -> osascript display notification + (옵션) Telegram
#   Linux    -> notify-send + (옵션) Telegram
# settings.json 의 훅에서 `bash -c '~/.claude/toast.sh "<메시지>"'` 로 호출된다.
# sync-repos처럼 사람이 안 지켜보는 저빈도 자동화는 `toast.sh "<메시지>" persist`로 호출해
# 알림센터에 남는 우하단 토스트를 추가로 띄운다(2026-07-22) — macOS/Linux는 원래부터 알림센터
# 저장이 기본이라 이 옵션이 필요 없음(무시됨).
msg="${1:-Response complete}"
msg="${msg//\"/}"                 # osascript/JSON 안전: 큰따옴표 제거 (메시지는 고정 문자열)
persist="${2:-}"
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
    # Windows: toast.ps1 이 중앙 팝업+알림음+Telegram 처리, persist면 우하단 토스트도 추가
    if [ "$persist" = "persist" ]; then
      powershell.exe -NoProfile -Sta -ExecutionPolicy Bypass -File "$claude_dir/toast.ps1" -Message "$msg" -Persist >/dev/null 2>&1 &
    else
      powershell.exe -NoProfile -Sta -ExecutionPolicy Bypass -File "$claude_dir/toast.ps1" -Message "$msg" >/dev/null 2>&1 &
    fi
    ;;
  Darwin)
    /usr/bin/osascript -e "display notification \"$msg\" with title \"Claude Code\"" >/dev/null 2>&1
    # 배너가 권한/집중모드로 막혀도 최소한 소리로 알림 (의존성 없음, Windows 무관)
    afplay /System/Library/Sounds/Glass.aiff >/dev/null 2>&1 &
    send_telegram "$msg" &
    ;;
  *)
    command -v notify-send >/dev/null 2>&1 && notify-send "Claude Code" "$msg" >/dev/null 2>&1
    send_telegram "$msg" &
    ;;
esac
exit 0
