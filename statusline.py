import sys, json, re, math, time

# Claude Code statusLine — statusline.ps1 의 bash/python 포팅(PowerShell 콜드스타트 제거용).
# stdin 의 세션 JSON 을 받아 "폴더 | 모델 | C:% | 5h:% | 7d:%" 를 ANSI 색으로 출력.

def out(s):
    # 콘솔 코드페이지와 무관하게 UTF-8 로(한글 폴더명 안전). 개행 없음([Console]::Write 와 동일)
    sys.stdout.buffer.write(s.encode("utf-8"))

raw = sys.stdin.read()
try:
    data = json.loads(raw)
except Exception:
    out("Claude")
    sys.exit(0)

ESC = "\x1b"
Reset = ESC + "[0m"
Green = ESC + "[32m"
Orange = ESC + "[38;5;208m"
Red = ESC + "[31m"
Cyan = ESC + "[36m"

def color(pct):
    if pct < 50:
        return Green
    elif pct <= 80:
        return Orange
    return Red

def fmt_remaining(resets_at):
    if not resets_at:
        return ""
    sec = int(resets_at) - int(time.time())
    if sec <= 0:
        return ""
    h = sec // 3600
    m = (sec % 3600) // 60
    if h >= 24:
        return "({}d {}h)".format(h // 24, h % 24)
    elif h > 0:
        return "({}h {}m)".format(h, m)
    return "({}m)".format(m)

def fmt_ctxsize(tokens):
    if not tokens:
        return ""
    if tokens >= 1000000:
        v = round(tokens / 1000000, 1)
        s = "{}M".format(int(v)) if v == math.floor(v) else "{}M".format(v)
        return " ({})".format(s)
    elif tokens >= 1000:
        return " ({}K)".format(round(tokens / 1000))
    return ""

def g(d, *keys):
    for k in keys:
        if not isinstance(d, dict):
            return None
        d = d.get(k)
    return d

Sep = " | "
parts = []

# 현재 폴더(leaf)
cwd = g(data, "workspace", "current_dir") or data.get("cwd")
if cwd:
    leaf = re.split(r"[\\/]+", str(cwd).rstrip("\\/"))[-1]
    if leaf:
        parts.append(Cyan + leaf + Reset)

# 모델 + 컨텍스트 창 크기
model = g(data, "model", "display_name") or g(data, "model", "id") or "Claude"
short = re.sub(r"\s", "", re.sub(r"^Claude\s*", "", model)) or "Claude"
parts.append(short + fmt_ctxsize(g(data, "context_window", "context_window_size")))

# 컨텍스트 사용률
used = g(data, "context_window", "used_percentage")
if used is not None:
    pct = round(used)
    parts.append("C: {}{}%{}".format(color(pct), pct, Reset))

# 5시간 / 7일 레이트리밋
for key, label in (("five_hour", "5h"), ("seven_day", "7d")):
    p = g(data, "rate_limits", key, "used_percentage")
    if p is not None:
        v = round(p)
        rem = fmt_remaining(g(data, "rate_limits", key, "resets_at"))
        parts.append("{}: {}{}%{} {}".format(label, color(v), v, Reset, rem).rstrip())

out(Sep.join(parts))
