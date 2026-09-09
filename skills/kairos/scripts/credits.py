"""크레딧 잔액 조회 — GET /credits/

사용: python credits.py [--account kairos|jbnu]
"""
import json
import sys
import _gw

account = None
if "--account" in sys.argv:
    i = sys.argv.index("--account")
    account = sys.argv[i + 1] if i + 1 < len(sys.argv) else None
_gw.use(account)

_, resp, _ = _gw.get("/credits/")
print(json.dumps(resp, ensure_ascii=False, indent=2))
