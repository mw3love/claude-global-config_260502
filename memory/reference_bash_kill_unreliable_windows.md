---
name: bash-kill-unreliable-on-windows
description: "Bash tool's `kill <pid>` does not reliably terminate native Windows python.exe processes on this PC — use `taskkill //F //PID <pid> //T` instead."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: af2a684e-0ab5-4767-9ad5-a63437f03d9e
  modified: 2026-08-07T16:00:33.508Z
---

On this dev PC, `kill <pid>` issued via the Bash tool (Git Bash/MSYS) does not reliably terminate a `python.exe` process started with `nohup ... &` for local testing (e.g. `dashboard_server.py`). The command appears to succeed (no error), but the process keeps running and keeps holding its port.

**Why:** Git Bash's `kill` sends a POSIX-style signal through the MSYS layer; native Windows processes (not Cygwin/MSYS-aware) often don't react to it the way a real Linux process would. Confirmed 2026-08-08: after ending a session's dashboard test server with `kill $PID` (no error shown), the next session's `netstat -ano | grep 8765` still showed the old PID `LISTENING`, and by the following session there were 3 stray `dashboard_server.py` processes all bound to port 8765 simultaneously (accumulated across sessions), all silently writing to and reading from the same shared `tools/dashboard_workspace.json` — a real (if low-stakes, mock-data-only) race condition.

**How to apply:** When starting a local test server (e.g. `tools/dashboard_server.py`) via Bash/nohup for Playwright-based verification in this repo, always tear it down with `taskkill //F //PID <pid> //T` (double-slash needed so Git Bash doesn't reinterpret `/F`/`/PID` as path fragments), not `kill`. Verify with `wmic process where "name='python.exe'" get ProcessId,CommandLine` and `netstat -ano | grep ':8765.*LISTEN'` that nothing is left before ending a session — don't just trust a clean `kill` exit code as proof the process is gone. See [[cimon-dashboard-dev-workflow]] for the broader mock-DB test loop this fits into.
