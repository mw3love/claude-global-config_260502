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

def model_setting():
    # settings.json 의 "model" 필드(opusplan 등 별칭) — stdin JSON엔 해석된 모델만 오므로 별도 확인
    import os
    try:
        with open(os.path.join(os.path.expanduser("~"), ".claude", "settings.json"), encoding="utf-8") as f:
            return json.load(f).get("model")
    except Exception:
        return None

def git_status_part(cwd):
    # fetch 없이 @{upstream} 캐시로만 비교 + FETCH_HEAD mtime 으로 그 캐시가 언제 기준인지 라벨링
    # (참고: github.com/ykdojo/claude-code-tips Tip 0 context-bar.sh)
    if not cwd:
        return None
    import subprocess, os
    try:
        def run(args):
            try:
                r = subprocess.run(["git", "-C", cwd] + args, capture_output=True, text=True, timeout=2)
            except Exception:
                return None
            return r.stdout.strip() if r.returncode == 0 else None

        branch = run(["branch", "--show-current"])
        if not branch:
            return None

        try:
            status_out = subprocess.run(
                ["git", "-C", cwd, "--no-optional-locks", "status", "--porcelain", "-uall"],
                capture_output=True, text=True, timeout=2
            ).stdout
        except Exception:
            status_out = ""
        lines = [l for l in status_out.splitlines() if l.strip()]
        file_count = len(lines)

        upstream = run(["rev-parse", "--abbrev-ref", "@{upstream}"])
        ahead = behind = 0
        fetch_ago = ""
        if upstream:
            counts = run(["rev-list", "--left-right", "--count", "HEAD...@{upstream}"])
            if counts:
                pieces = counts.split()
                if len(pieces) == 2:
                    ahead, behind = int(pieces[0]), int(pieces[1])
            fetch_head = os.path.join(cwd, ".git", "FETCH_HEAD")
            if os.path.isfile(fetch_head):
                mtime = os.path.getmtime(fetch_head)
                lt = time.localtime(mtime)
                now_lt = time.localtime()
                if (lt.tm_year, lt.tm_yday) == (now_lt.tm_year, now_lt.tm_yday):
                    fetch_ago = time.strftime("%H:%M", lt)
                else:
                    fetch_ago = time.strftime("%m/%d %H:%M", lt)
            if ahead == 0 and behind == 0:
                sync = "synced"
            elif ahead > 0 and behind == 0:
                sync = "{} ahead".format(ahead)
            elif behind > 0 and ahead == 0:
                sync = "{} behind".format(behind)
            else:
                sync = "{} ahead, {} behind".format(ahead, behind)
            if fetch_ago:
                sync += " ({})".format(fetch_ago)
        else:
            sync = "no upstream"

        if file_count == 0:
            detail = "clean, {}".format(sync)
        elif file_count == 1:
            fname = lines[0][3:].strip() if len(lines[0]) > 3 else lines[0]
            detail = "{} uncommitted, {}".format(fname, sync)
        else:
            detail = "{} files uncommitted, {}".format(file_count, sync)

        if behind > 0:
            gcolor = Red
        elif file_count > 0 or ahead > 0:
            gcolor = Orange
        else:
            gcolor = Green

        return "{}{}{} ({})".format(gcolor, branch, Reset, detail)
    except Exception:
        return None

Sep = " | "
line1 = []
line2 = []

# 1행: 현재 폴더(leaf) + git 브랜치/미커밋/동기화 상태
cwd = g(data, "workspace", "current_dir") or data.get("cwd")
if cwd:
    leaf = re.split(r"[\\/]+", str(cwd).rstrip("\\/"))[-1]
    if leaf:
        line1.append(Cyan + leaf + Reset)

git_part = git_status_part(cwd)
if git_part:
    line1.append(git_part)

# 2행: 모델 + 컨텍스트 창 크기
model = g(data, "model", "display_name") or g(data, "model", "id") or "Claude"
short = re.sub(r"\s", "", re.sub(r"^Claude\s*", "", model)) or "Claude"
tag = " [opusplan]" if str(model_setting() or "").startswith("opusplan") else ""
line2.append(short + tag + fmt_ctxsize(g(data, "context_window", "context_window_size")))

# 컨텍스트 사용률
used = g(data, "context_window", "used_percentage")
if used is not None:
    pct = round(used)
    line2.append("C: {}{}%{}".format(color(pct), pct, Reset))

# 5시간 / 7일 레이트리밋
for key, label in (("five_hour", "5h"), ("seven_day", "7d")):
    p = g(data, "rate_limits", key, "used_percentage")
    if p is not None:
        v = round(p)
        rem = fmt_remaining(g(data, "rate_limits", key, "resets_at"))
        line2.append("{}: {}{}%{} {}".format(label, color(v), v, Reset, rem).rstrip())

out(Sep.join(line1) + "\n" + Sep.join(line2))
